# Step 5 ledger (TASK-0019): each deck / ladder sub-work replayed from its events vs its design list; overlaps with the hull
#   and between parts; the assembled ship (hull + all parts, as the links place them at 0,0,0): structure, ladder points;
#   anchors and link meta read back from the work files vs ladder_points.json / decks_meta.tsv.
#   Usage: python -X utf8 tools/check_decks.py <design> [--probe=dz=<n>]   (probe: compare against lists shifted up n; must report)
#   * Reads only events/, anchors.json, links.json -- never the engine's views. Replay is design/verify_step4.replay.
import sys, os, json
import numpy as np
from scipy import ndimage

design = os.path.abspath(sys.argv[1])
sys.path.insert(0, design)
from verify_step4 import replay

sys.stdout.reconfigure(encoding='utf-8')
probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
dz = int(probe.get('dz', 0))
HULL = 'claude-baghlah-01m'
WORKS = os.path.dirname(os.path.dirname(design))
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
pts = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
parts = {'deck-' + g['key']: os.path.join(design, 'masks', 'decks', g['key'] + '.vox.txt') for g in plan['decks_build']['groups']}
for up in sorted({v['group_up'] for v in pts.values()}):
    parts['ladders-' + up] = os.path.join(design, 'masks', 'ladders', up + '.vox.txt')


def load(path):
    out = {}
    for l in open(path, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            out[(x, y, z + dz)] = c
    return out


R = {'parts': {}}
hull, _ = replay(os.path.join(WORKS, HULL))
seen = {}
bad = 0
for nm, path in parts.items():
    w, log = replay(os.path.join(WORKS, '%s-%s' % (HULL, nm)))
    d = load(path)
    miss, extra = len(set(d) - set(w)), len(set(w) - set(d))
    cdiff = sum(1 for k in set(d) & set(w) if d[k] != w[k])
    ov_h = len(set(w) & set(hull))
    ov_p = sum(len(set(w) & s) for s in seen.values())
    seen[nm] = set(w)
    bad += miss + extra + cdiff + ov_h + ov_p
    R['parts'][nm] = {'work': len(w), 'design': len(d), 'missing': miss, 'extra': extra, 'colour_diff': cdiff,
                      'hull_overlap': ov_h, 'overlap_with_earlier_parts': ov_p, 'events': len(log)}
R['problems_total'] = bad

# assembled: hull + parts (all links at 0,0,0, turn 0, no mirror -- read back below)
allc = set(hull)
for s in seen.values():
    allc |= s
A = np.array(sorted(allc))
lo = A.min(axis=0)
G = np.zeros(tuple(A.max(axis=0) - lo + 1), bool)
G[tuple((A - lo).T)] = True
R['assembled'] = {'cells': len(allc), 'components_6': int(ndimage.label(G)[1]),
                  'cavities': int((ndimage.binary_fill_holes(G) & ~G).sum())}
yc = plan['space']['yc']
mir = {(x, 2 * yc - y, z) for x, y, z in allc}
R['assembled']['mirror_diff'] = len(allc ^ mir)
probs = []
for nm, v in sorted(pts.items()):
    for pk, (x, y, z) in v['points'].items():
        air = (x, y, z) not in allc
        floor = (x, y, z - 1) in allc
        head = sum(1 for k in range(14) if (x, y, z + k) in allc)
        if not (air and floor) or head:
            probs.append([nm, pk, [x, y, z], air, floor, head])
R['ladder_point_problems'] = probs

# anchors on the ladder sub-works vs ladder_points.json
an = {}
for up in sorted({v['group_up'] for v in pts.values()}):
    f = os.path.join(WORKS, '%s-ladders-%s' % (HULL, up), 'anchors.json')
    for a in json.load(open(f, encoding='utf-8'))['anchors']:
        an[a['name']] = a['at']
want = {'%s.%s' % (nm, pk): p for nm, v in pts.items() for pk, p in v['points'].items()}
R['anchors'] = {'want': len(want), 'found': sum(1 for k in want if k in an),
                'diff': [k for k in want if k in an and list(an[k]) != list(want[k])], 'unexpected': sorted(set(an) - set(want))}

# links + meta
lk = json.load(open(os.path.join(WORKS, HULL + '-assembly', 'links.json'), encoding='utf-8'))['links']
tsv = {}
for l in open(os.path.join(design, 'decks_meta.tsv'), encoding='utf-8'):
    p, n, m = l.rstrip('\n').split('\t')
    tsv[n] = json.loads(m)
meta_diff, placement = [], []
for l in lk:
    if l['name'].startswith('甲板-'):
        if l.get('meta') != tsv.get(l['name']):
            meta_diff.append(l['name'])
    if list(l['at']) != [0, 0, 0] or l['turn'] or l['mirror'] or not l['enabled']:
        placement.append(l['name'])
sub = {}
for g in plan['decks_build']['groups']:
    f = os.path.join(WORKS, '%s-deck-%s' % (HULL, g['key']), 'links.json')
    if os.path.exists(f):
        for l in json.load(open(f, encoding='utf-8'))['links']:
            sub[g['key'] + '/' + l['name']] = [l['work'], l.get('meta')]
R['links'] = {'assembly': [l['name'] for l in lk], 'deck_meta_diff_vs_tsv': meta_diff, 'not_at_origin_or_disabled': placement, 'ladder_links': sub}
print(json.dumps(R, ensure_ascii=False, indent=1))
