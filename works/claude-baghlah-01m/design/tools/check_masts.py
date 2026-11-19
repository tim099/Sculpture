# Step 7 ledger (TASK-0019): every step-7 work replayed from its events vs its design list (earlier works too: nothing of
#   theirs may change); the assembly as the ENGINE assembles it (export format=list) vs the design assembled by hand with the
#   step-7 parts; link meta, yard models (models.json) and yard anchors (anchors.json) read back from the work files; the
#   shipcheck "mast" rule (Ship_Masts §5) evaluated on the read-back files, not on the generator's numbers.
#   Usage: python -X utf8 tools/check_masts.py <design> [--probe=mast_dx=<n>]
#     probe: assemble the design with both masts shifted n cells in x; the export comparison must report it.
#   * Replay reads only events/ (stampvox placed_colored, box, carve/carvevox carved_voxels, workedit after[]).
import sys, os, json, glob, subprocess, tempfile
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
HULL = 'claude-baghlah-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(design))
SENATE = os.environ.get('SENATE', 'senate')
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
YC = plan['space']['yc']
sys.path.insert(0, design)
from draft_masts import ship_cells, load


def replay(work_dir):
    cells, n = {}, 0
    for p in sorted(glob.glob(os.path.join(work_dir, 'events', '*', '*.json'))):
        e = json.load(open(p, encoding='utf-8'))
        n += 1
        if 'placed_colored' in e:
            for x, y, z, c in e['placed_colored']:
                cells[(x, y, z)] = c
        elif e.get('op') == 'box':
            for x, y, z in e.get('placed_voxels', []):
                cells[(x, y, z)] = e['color']
        if 'carved_voxels' in e:
            for v in e['carved_voxels']:
                cells.pop(tuple(v[:3]), None)
        if e.get('op') == 'workedit':
            for a in e['edit'].get('after', []):
                k = (a['x'], a['y'], a['z'])
                if a['color']:
                    cells[k] = a['color']
                else:
                    cells.pop(k, None)
    return cells, n


def cmp(have, want):
    return {'have': len(have), 'want': len(want), 'missing': len(set(want) - set(have)), 'extra': len(set(have) - set(want)),
            'colour_diff': sum(1 for k in set(want) & set(have) if want[k] != have[k])}


M = os.path.join(design, 'masks')
R = {'probe': probe or None, 'works': {}}
new = {'mast-main': 'masts/main', 'mast-mizzen': 'masts/mizzen', 'jibboom': 'masts/jibboom', 'cable-beam': 'masts/cable_beam',
       'yard-main-lateen': 'yards/lateen-main', 'yard-mizzen-lateen': 'yards/lateen-mizzen'}
want = {}
for k, rel in new.items():
    have, n = replay(os.path.join(WORKS, '%s-%s' % (HULL, k)))
    want[k] = load(os.path.join(M, rel + '.vox.txt'))
    R['works'][k] = dict(cmp(have, want[k]), events=n)
# earlier works: hull = step 4 + step 6; decks, ladders, deco as designed (unchanged by step 7)
old = {HULL: None}
hw = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
hw.update(load(os.path.join(M, 'step6', 'hull_recolor.vox.txt')))
hw.update(load(os.path.join(M, 'step6', 'hull_add.vox.txt')))
have, n = replay(os.path.join(WORKS, HULL))
R['works']['hull'] = dict(cmp(have, hw), events=n)
for g in plan['decks_build']['groups']:
    have, n = replay(os.path.join(WORKS, '%s-deck-%s' % (HULL, g['key'])))
    R['works']['deck-' + g['key']] = dict(cmp(have, load(os.path.join(M, 'decks', g['key'] + '.vox.txt'))), events=n)
    have, n = replay(os.path.join(WORKS, '%s-ladders-%s' % (HULL, g['key'])))
    R['works']['ladders-' + g['key']] = dict(cmp(have, load(os.path.join(M, 'ladders', g['key'] + '.vox.txt'))), events=n)
for k, f in (('stern-glass', 'stern_glass'), ('quarter-rail', 'quarter_rail'), ('stern-carving', 'stern_carving'), ('stem-head', 'stem_head'),
             ('quarter-gallery', 'quarter_gallery'), ('quarter-gallery-glass', 'gallery_glass')):
    have, n = replay(os.path.join(WORKS, '%s-%s' % (HULL, k)))
    R['works'][k] = dict(cmp(have, load(os.path.join(M, 'deco', f + '.vox.txt'))), events=n)

# design assembled by hand: everything linked (no models) + step-7 links at 0,0,0
A = ship_cells(design, plan)
for k in ('stern_carving', 'stem_head'):                         # models: not in format=list
    for key in load(os.path.join(M, 'deco', k + '.vox.txt')):
        A.pop(key, None)
dx = int(probe.get('mast_dx', 0))
for k in ('mast-main', 'mast-mizzen', 'jibboom', 'cable-beam'):
    for (x, y, z), c in want[k].items():
        A[(x + (dx if k.startswith('mast') else 0), y, z)] = c
out = os.path.join(tempfile.gettempdir(), 'baghlah_asm_step7.txt')
r = subprocess.run([SENATE, 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'work=' + ASM, '--arg', 'format=list', '--arg', 'out=' + out],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
if r.returncode != 0:
    print((r.stdout + r.stderr)[-1500:])
    raise SystemExit('✗ export exit %d' % r.returncode)
E = load(out)
R['assembly_export_vs_design'] = cmp(E, A)
G = np.zeros((480, 160, 400), bool)
for (x, y, z) in E:
    G[x, y, z] = True
lab, ncomp = ndimage.label(G)
R['assembly_export_structure'] = {'cells': len(E), 'components_6': int(ncomp), 'cavities': int((ndimage.binary_fill_holes(G) & ~G).sum()),
                                  'mirror_diff_excl_jibboom': sum(1 for (x, y, z), c in E.items()
                                                                  if (x, y, z) not in want['jibboom'] and (x, 2 * YC - y, z) not in want['jibboom']
                                                                  and E.get((x, 2 * YC - y, z)) != c)}
# links / models / anchors read back
lk = {l['name']: l for l in json.load(open(os.path.join(WORKS, ASM, 'links.json'), encoding='utf-8'))['links']}
R['links'] = {n: {'work': lk[n].get('work'), 'at': lk[n]['at'], 'turn': lk[n].get('turn'), 'mirror': lk[n].get('mirror'), 'meta': lk[n].get('meta'), 'enabled': lk[n]['enabled']}
              for n in ('主桅', '後桅', 'foc桿', '錨纜橫樑') if n in lk}
masts_meta = [l.get('meta', {}) for l in lk.values() if l.get('meta', {}).get('kind') == 'mast']
place = {p['name']: p for p in json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))}
LAT = json.load(open(os.path.join(design, 'yards_lateen.json'), encoding='utf-8'))
R['models'], R['anchors'], R['shipcheck_mast'] = {}, {}, {}
for key in ('main', 'mizzen'):
    host = '%s-mast-%s' % (HULL, key)
    md = {m['name']: m for m in json.load(open(os.path.join(WORKS, host, 'models.json'), encoding='utf-8'))['models']}
    nm = 'yard-%s-lateen' % key
    m, p = md.get(nm), place[nm]
    diff = [f for f in ('at', 'pivot', 'rotate', 'scale') if m is None or [float(v) for v in m[f]] != [float(v) for v in p[f]]]
    meta_diff = [k for k in p['meta'] if m is None or m['meta'].get(k) != p['meta'][k]]
    R['models'][nm] = {'host': host, 'work': m and m['work'], 'diff_vs_placement': diff, 'meta_diff': meta_diff, 'enabled': m and m['enabled']}
    yw = '%s-yard-%s-lateen' % (HULL, key)
    an = {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, yw, 'anchors.json'), encoding='utf-8'))['anchors']}
    R['anchors'][yw] = {'count': len(an), 'want': len(LAT[key]['anchors']),
                        'diff': sorted(k for k in set(an) | set(LAT[key]['anchors']) if an.get(k) != LAT[key]['anchors'].get(k)),
                        'on_yard_cell': sum(1 for a in an.values() if tuple(a) in want['yard-%s-lateen' % key])}
    # Ship_Masts shipcheck: yard meta.mast == exactly one kind=mast link; that mast's own cells within pivot z −40..−10, centre ±4
    pv = [float(m['at'][i]) for i in range(3)]
    mast_cells = replay(os.path.join(WORKS, host))[0]
    band = [c for c in mast_cells if pv[2] - 40 <= c[2] + 0.5 <= pv[2] - 10 and abs(c[1] + 0.5 - (YC + 0.5)) <= 4]
    R['shipcheck_mast'][nm] = {'yard_mast': m['meta'].get('mast'), 'kind_mast_links_named': sum(1 for mm in masts_meta if mm.get('mast') == m['meta'].get('mast')),
                               'pivot_at': pv, 'mast_cells_in_band': len(band)}
bad = sum(v['missing'] + v['extra'] + v['colour_diff'] for v in R['works'].values())
bad += R['assembly_export_vs_design']['missing'] + R['assembly_export_vs_design']['extra'] + R['assembly_export_vs_design']['colour_diff']
bad += (R['assembly_export_structure']['components_6'] != 1) + R['assembly_export_structure']['cavities'] + R['assembly_export_structure']['mirror_diff_excl_jibboom']
bad += sum(len(v['diff_vs_placement']) + len(v['meta_diff']) for v in R['models'].values())
bad += sum(len(v['diff']) + (v['count'] - v['on_yard_cell']) for v in R['anchors'].values())
bad += sum((v['kind_mast_links_named'] != 1) + (v['mast_cells_in_band'] == 0) for v in R['shipcheck_mast'].values())
R['problems_total'] = bad
print(json.dumps(R, ensure_ascii=False, indent=1))
