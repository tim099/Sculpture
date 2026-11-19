# Step 6 ledger (TASK-0019): every step-6 work replayed from its events vs its design list; the hull replayed vs
#   step-4 design + step-6 recolour + sashes; the assembly as the ENGINE assembles it (export format=list, every link
#   placed / mirrored by the engine) vs the design assembled by hand; link + model meta read back from the work files.
#   Usage: python -X utf8 tools/check_deco.py <design> [--probe=gallery_at_y=<n>]
#     probe: assemble the design with the port gallery at a different y (and its mirror); the export comparison must report it.
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
FR = plan['deco']['quarter_gallery']['frame']


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


def load(path):
    out = {}
    for l in open(path, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            out[(x, y, z)] = c
    return out


def cmp(have, want):
    return {'have': len(have), 'want': len(want), 'missing': len(set(want) - set(have)), 'extra': len(set(have) - set(want)),
            'colour_diff': sum(1 for k in set(want) & set(have) if want[k] != have[k])}


R = {'probe': probe or None, 'works': {}}
M = os.path.join(design, 'masks')
lists = {'stern-glass': 'deco/stern_glass', 'quarter-gallery': 'deco/quarter_gallery', 'quarter-gallery-glass': 'deco/gallery_glass',
         'quarter-rail': 'deco/quarter_rail', 'stern-carving': 'deco/stern_carving', 'stem-head': 'deco/stem_head'}
design_parts = {}
for k, rel in lists.items():
    have, n = replay(os.path.join(WORKS, '%s-%s' % (HULL, k)))
    want = load(os.path.join(M, rel + '.vox.txt'))
    design_parts[k] = want
    R['works'][k] = dict(cmp(have, want), events=n)
hull_want = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
hull_want.update(load(os.path.join(M, 'step6', 'hull_recolor.vox.txt')))
hull_want.update(load(os.path.join(M, 'step6', 'hull_add.vox.txt')))
hull_have, n = replay(os.path.join(WORKS, HULL))
R['works']['hull'] = dict(cmp(hull_have, hull_want), events=n)

# design assembled by hand (absolute coordinates)
A = dict(hull_want)
for g in plan['decks_build']['groups']:
    A.update(load(os.path.join(M, 'decks', g['key'] + '.vox.txt')))
for f in sorted(os.listdir(os.path.join(M, 'ladders'))):
    A.update(load(os.path.join(M, 'ladders', f)))
A.update(design_parts['stern-glass'])
A.update(design_parts['quarter-rail'])
gy = int(probe.get('gallery_at_y', FR['at_y']))
for k in ('quarter-gallery', 'quarter-gallery-glass'):
    for (x, y, z), c in design_parts[k].items():
        A[(x, y + gy, z)] = c
        A[(x, (161 - gy - FR['size'][1]) + (FR['size'][1] - 1 - y), z)] = c
# engine-assembled
out = os.path.join(tempfile.gettempdir(), 'baghlah_asm_step6.txt')
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
                                  'mirror_diff': sum(1 for (x, y, z), c in E.items() if E.get((x, 2 * YC - y, z)) != c)}
# links + models read back
lk = {l['name']: l for l in json.load(open(os.path.join(WORKS, ASM, 'links.json'), encoding='utf-8'))['links']}
gl = {l['name']: l for l in json.load(open(os.path.join(WORKS, HULL + '-quarter-gallery', 'links.json'), encoding='utf-8'))['links']}
R['links'] = {n: {'work': lk[n]['work'], 'at': lk[n]['at'], 'mirror': lk[n].get('mirror'), 'meta': lk[n].get('meta'), 'enabled': lk[n]['enabled']}
              for n in ('船尾窗玻璃', '側廊-P', '側廊-S', '舵手台欄杆') if n in lk}
R['links']['側廊/窗玻璃'] = {'work': gl['窗玻璃']['work'], 'at': gl['窗玻璃']['at'], 'meta': gl['窗玻璃'].get('meta')} if '窗玻璃' in gl else None
md = {m['name']: m for m in json.load(open(os.path.join(WORKS, ASM, 'models.json'), encoding='utf-8'))['models']}
R['models'] = {n: {k: md[n].get(k) for k in ('work', 'at', 'pivot', 'scale', 'rotate', 'mirror', 'meta', 'enabled')} for n in ('船尾雕花', '艏柱頭') if n in md}
sizes = {}
for k in lists:
    wj = json.load(open(os.path.join(WORKS, '%s-%s' % (HULL, k), 'work.json'), encoding='utf-8'))
    sizes[k] = [wj.get('size_x'), wj.get('size_y'), wj.get('size_z'), wj.get('meters_per_voxel')]
R['work_sizes'] = sizes
bad = sum(v['missing'] + v['extra'] + v['colour_diff'] for v in R['works'].values())
bad += R['assembly_export_vs_design']['missing'] + R['assembly_export_vs_design']['extra'] + R['assembly_export_vs_design']['colour_diff']
R['problems_total'] = bad
print(json.dumps(R, ensure_ascii=False, indent=1))
