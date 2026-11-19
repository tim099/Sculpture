# Step 8 ledger (TASK-0019), structure from tools/check_masts.py: every work replayed from its events vs its design list
#   (the three new step-8 works and all 19 earlier ones: nothing of theirs may change); the assembly as the ENGINE
#   assembles it (export format=list) vs the design assembled by hand; the yard models (the mizzen yard moved to port in
#   step 8 v4) and the step-8 anchors read back from the work files; ropes.json / sails.json / meta / default wind read back
#   from the assembly vs rigging_plan.json; the CLI's own rope / sail readings (broken counts).
#   Usage: python -X utf8 tools/check_rigging.py <design> [--probe=drop_meta=<rope>] [--probe=part_dx=<n>] [--extra=<part>:<list>,…] [--write]
#     extra:     later steps' linked parts (step 9: gunfittings:gunfittings/gunfittings) -- replayed like the others and added
#                to the design, so the engine export still compares cell for cell (never written to verify_step8.json)
#     drop_meta: after reading the work, pretend that rope has no meta (the meta check must name it)
#     part_dx:   assemble the design with the three new parts shifted n cells in x (the export comparison must report it)
#   * Replay reads only events/ (stampvox placed_colored, box, carve/carvevox carved_voxels, workedit after[]).
import sys, os, json, glob, re, subprocess, tempfile
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
extra = [kv.split(':', 1) for a in sys.argv[2:] if a.startswith('--extra=') for kv in a.split('=', 1)[1].split(',')]
mworks = [kv.split(':', 1) for a in sys.argv[2:] if a.startswith('--works=') for kv in a.split('=', 1)[1].split(',')]     # step 11: model sub-works (replayed only, not in format=list)
carves = [kv.split(':', 1) for a in sys.argv[2:] if a.startswith('--carve=') for kv in a.split('=', 1)[1].split(',')]     # step 11: carve lists taken off a work's design list
write = '--write' in sys.argv and not probe and not extra and not mworks and not carves
HULL = 'claude-baghlah-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(design))
SENATE = os.environ.get('SENATE', 'senate')
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
RP = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
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


def cli(*args):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def items(path, key):
    d = json.load(open(path, encoding='utf-8'))
    return d if isinstance(d, list) else d.get(key, [])


M = os.path.join(design, 'masks')
R = {'probe': probe or None, 'works': {}}
want = {}
lists = {'rings': 'rigging/rings', 'stern-spars': 'rigging/stern_spars', 'halyard-bitt': 'rigging/halyard_bitt',
         'mast-main': 'masts/main', 'mast-mizzen': 'masts/mizzen', 'jibboom': 'masts/jibboom', 'cable-beam': 'masts/cable_beam',
         'yard-main-lateen': 'yards/lateen-main', 'yard-mizzen-lateen': 'yards/lateen-mizzen',
         'stern-glass': 'deco/stern_glass', 'quarter-rail': 'deco/quarter_rail', 'stern-carving': 'deco/stern_carving', 'stem-head': 'deco/stem_head',
         'quarter-gallery': 'deco/quarter_gallery', 'quarter-gallery-glass': 'deco/gallery_glass'}
for g in plan['decks_build']['groups']:
    lists['deck-' + g['key']] = 'decks/' + g['key']
    lists['ladders-' + g['key']] = 'ladders/' + g['key']
for k, rel in extra + mworks:
    lists[k] = rel
cut = {}
for k, rel in carves:
    cut.setdefault(k, set()).update(load(os.path.join(M, rel + '.vox.txt')))
for k, rel in lists.items():
    have, n = replay(os.path.join(WORKS, '%s-%s' % (HULL, k)))
    want[k] = {c: v for c, v in load(os.path.join(M, rel + '.vox.txt')).items() if c not in cut.get(k, ())}
    R['works'][k] = dict(cmp(have, want[k]), events=n)
hw = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
hw.update(load(os.path.join(M, 'step6', 'hull_recolor.vox.txt')))
hw.update(load(os.path.join(M, 'step6', 'hull_add.vox.txt')))
for c in cut.get('hull', ()):
    hw.pop(c, None)
R['carved_off_design'] = {k: len(v) for k, v in cut.items()}
have, n = replay(os.path.join(WORKS, HULL))
R['works']['hull'] = dict(cmp(have, hw), events=n)

# design assembled by hand: everything linked (no models) + step 7 + step 8 links at 0,0,0
A = ship_cells(design, plan)
for k in ('stern_carving', 'stem_head'):                         # models: not in format=list
    for key in load(os.path.join(M, 'deco', k + '.vox.txt')):
        A.pop(key, None)
dx = int(probe.get('part_dx', 0))
for k in ('mast-main', 'mast-mizzen', 'jibboom', 'cable-beam'):
    A.update(want[k])
for k in ('rings', 'stern-spars', 'halyard-bitt'):
    for (x, y, z), c in want[k].items():
        A[(x + dx, y, z)] = c
for k, rel in extra:
    A.update(want[k])
for k, v in cut.items():                                          # the trunk: carved cells are gone from the ship (stern-carving is a model, already off)
    for c in v:
        A.pop(c, None)
out = os.path.join(tempfile.gettempdir(), 'baghlah_asm_step8.txt')
rc, o = cli('op=export', 'work=' + ASM, 'format=list', 'out=' + out)
if rc != 0:
    print(o[-1500:])
    raise SystemExit('✗ export exit %d' % rc)
E = load(out)
R['assembly_export_vs_design'] = cmp(E, A)
G = np.zeros((480, 160, 400), bool)
for (x, y, z) in E:
    G[x, y, z] = True
lab, ncomp = ndimage.label(G)
asym = set(want['jibboom']) | set(want['stern-spars'])          # the jib boom (starboard) and the bumkin (port) are one-sided by design
R['assembly_export_structure'] = {'cells': len(E), 'components_6': int(ncomp), 'cavities': int((ndimage.binary_fill_holes(G) & ~G).sum()),
                                  'mirror_diff_excl_jibboom_bumkin': sum(1 for (x, y, z), c in E.items()
                                                                         if (x, y, z) not in asym and (x, 2 * YC - y, z) not in asym and E.get((x, 2 * YC - y, z)) != c)}
# links of the new parts
lk = {l['name']: l for l in items(os.path.join(WORKS, ASM, 'links.json'), 'links')}
R['links'] = {}
for part, ln in RP['links'].items():
    if part in ('rings', 'stern-spars', 'halyard-bitt'):
        l = lk.get(ln)
        R['links'][ln] = None if l is None else {'work': l.get('work') or l.get('source_work'), 'at': l['at'], 'mirror': l.get('mirror'), 'enabled': l['enabled']}
# yard models (mizzen moved to port in step 8 v4)
place = {p['name']: p for p in json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))}
R['models'] = {}
for key in ('main', 'mizzen'):
    host = '%s-mast-%s' % (HULL, key)
    md = {m['name']: m for m in items(os.path.join(WORKS, host, 'models.json'), 'models')}
    nm = 'yard-%s-lateen' % key
    m, p = md.get(nm), place[nm]
    R['models'][nm] = {'at': m and m['at'], 'diff_vs_placement': [f for f in ('at', 'pivot', 'rotate', 'scale') if m is None or [float(v) for v in m[f]] != [float(v) for v in p[f]]],
                       'meta_diff': [k for k in p['meta'] if m is None or m['meta'].get(k) != p['meta'][k]]}
# step-8 anchors read back
R['anchors'] = {}
for part, items_ in RP['anchors'].items():
    w = RP['anchor_works'][part]
    an = {a['name']: a for a in items(os.path.join(WORKS, w, 'anchors.json'), 'anchors')}
    stale = sorted(n for n, a in an.items() if a.get('note', '').startswith('步驟 8') and n not in items_)
    R['anchors'][part] = {'want': len(items_), 'diff': sorted(n for n in items_ if n not in an or list(an[n]['at']) != list(items_[n])), 'stale_step8': stale}
# ropes / sails / meta / wind read back
ropes = {r['name']: r for r in items(os.path.join(WORKS, ASM, 'ropes.json'), 'ropes')}
sails = {s['name']: s for s in items(os.path.join(WORKS, ASM, 'sails.json'), 'sails')}
if 'drop_meta' in probe and probe['drop_meta'] in ropes:
    ropes[probe['drop_meta']] = dict(ropes[probe['drop_meta']], meta=None)
rd = []
for r in RP['ropes']:
    g = ropes.get(r['name'])
    if g is None:
        rd.append((r['name'], 'missing'))
        continue
    for f in ('from', 'to', 'color', 'group'):
        if g.get(f) != r[f]:
            rd.append((r['name'], f))
    for f in ('slack', 'thickness'):
        if abs(float(g.get(f, -1)) - float(r[f])) > 1e-9:
            rd.append((r['name'], f))
    if (g.get('meta') or None) != (r['meta'] or None):
        rd.append((r['name'], 'meta'))
R['ropes'] = {'plan': len(RP['ropes']), 'work_total': len(ropes), 'diff': rd,
              'work_not_in_plan': sorted(n for n in ropes if n not in {r['name'] for r in RP['ropes']})}
sd = []
for s in RP['sails']:
    g = sails.get(s['name'])
    if g is None:
        sd.append((s['name'], 'missing'))
        continue
    free = set(s['free'])
    names = s['corner_names'] or [''] * len(s['corners'])
    for i, (c, cn) in enumerate(zip(s['corners'], names)):
        gc = g['corners'][i] if i < len(g['corners']) else {}
        if gc.get('at') != c or (gc.get('name') or '') != cn or bool(gc.get('pin')) == (i in free or cn in free):
            sd.append((s['name'], 'corner %d' % i))
    if len(g['corners']) != len(s['corners']):
        sd.append((s['name'], 'corner count'))
    if list(g.get('bind', [])) != list(s['bind']):
        sd.append((s['name'], 'bind'))
    if g.get('color', '').lower() != s['color'].lower() or abs(float(g.get('fullness', 0)) - s['fullness']) > 1e-9:
        sd.append((s['name'], 'color/fullness'))
    if (g.get('meta') or None) != s['meta']:
        sd.append((s['name'], 'meta'))
    if bool(g.get('texture')) != bool(s.get('texture')):
        sd.append((s['name'], 'texture'))
R['sails'] = {'plan': len(RP['sails']), 'work_total': len(sails), 'diff': sd}
sail_names = {s['name'] for s in RP['sails']}
need = [n for n in ropes if '.' in n and n.split('.')[0] in sail_names]
R['sail_rope_meta'] = {'need': len(need), 'missing': sorted(n for n in need if not ropes[n].get('meta')),
                       'wrong_sail': sorted(n for n in need if ropes[n].get('meta') and ropes[n]['meta'].get('sail') != n.split('.')[0]),
                       'wrong_kind': sorted(n for n in need if ropes[n].get('meta') and ropes[n]['meta'].get('kind') != n.split('.')[1])}
R['flags'] = {n: sails[n].get('meta') for n in sails if (sails[n].get('meta') or {}).get('kind') == 'flag'}
R['ensign_ok'] = all(m.get('nation') for m in R['flags'].values() if m.get('flag') == 'ensign') and \
    all(sails[n].get('texture') for n, m in R['flags'].items() if m.get('flag') == 'ensign')
YM = {p['meta']['sail'] for p in place.values()}
R['yard_meta_sail_is_a_sail'] = sorted(YM - sail_names) or 0
rc, o = cli('op=work', 'sub=sails', 'work=' + ASM)
m = re.search(r'風 \(([-\d.]+),([-\d.]+),([-\d.]+)\) m/s.*?模擬 ([\d.]+) 秒', o)
R['default_wind'] = [float(v) for v in m.groups()] if m else None
cnt = {k: int(v) for k, v in re.findall(r'🔢 (sails_drawn|sails_broken|ropes_broken|sail_count) = (\d+)', o)}
rc2, o2 = cli('op=work', 'sub=ropes', 'work=' + ASM)
cnt.update({'rope_' + k: int(v) for k, v in re.findall(r'🔢 (rope_count|ropes_broken|ropes_ungrouped) = (\d+)', o2)})
R['cli'] = cnt
bad = sum(v['missing'] + v['extra'] + v['colour_diff'] for v in R['works'].values())
bad += sum(R['assembly_export_vs_design'][k] for k in ('missing', 'extra', 'colour_diff'))
bad += (R['assembly_export_structure']['components_6'] != 1) + R['assembly_export_structure']['cavities'] + R['assembly_export_structure']['mirror_diff_excl_jibboom_bumkin']
bad += sum(v is None for v in R['links'].values())
bad += sum(len(v['diff_vs_placement']) + len(v['meta_diff']) for v in R['models'].values())
bad += sum(len(v['diff']) + len(v['stale_step8']) for v in R['anchors'].values())
bad += len(R['ropes']['diff']) + len(R['sails']['diff']) + len(R['sail_rope_meta']['missing']) + len(R['sail_rope_meta']['wrong_sail']) + len(R['sail_rope_meta']['wrong_kind'])
bad += (not R['ensign_ok']) + (R['yard_meta_sail_is_a_sail'] != 0) + (R['default_wind'] != [float(v) for v in RP['wind']] + [float(RP['sail_seconds'])])
bad += cnt.get('sails_broken', 1) + cnt.get('rope_ropes_broken', 1)
R['problems_total'] = bad
print(json.dumps(R, ensure_ascii=False, indent=1))
if write:
    with open(os.path.join(design, 'verify_step8.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
