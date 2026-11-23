# 海鷗號 步驟 8（TASK-0024）：掛好的帆布（引擎 export obj，作品預設風／秒數）對船的格子 —— 平面三角形的讀數看不到鼓起來的那一塊，這一把看得到。
#   出處：星辰號 claude-baghlah-01m/design/tools/check_sails_sim.py 的做法（export obj ropes=0、讀 o sail_ 的頂點、OBJ 軸 (x, z, y) ⇒ 雕刻 (vx, vz, vy)），自己寫、只量頂點。
#   用法：python -I -X utf8 tools/check_sails_sim.py [--wind=x,y,z] [--json=<輸出檔>]
#     --wind：用這個風 export（反向對照：鼓的方向要跟著變、讀數要動）
#   量：每面帆的頂點有幾個落在船的實心格裡（船殼、甲板、兩桅、桿、艏柱頭、兩根帆桁的世界格）、離最近實心格幾格、往哪一舷鼓多少。
import sys, os, json, subprocess, tempfile
import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
SENATE = os.environ.get('SENATE', '/paperclip/instances/default/projects/482d2c24-3be9-40fc-8ec9-1a7a02dd4f3f/1ea1d409-d2dd-45dc-b44e-35e83e49b833/_default/.work/senate/bin/senate')
ASM = 'claude-felucca-01m-assembly'
opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {tuple(map(int, r[:3])) for r in a}


solid = {}
for fn, lab in (('masks/hull/hull_01.vox.txt', 'hull'), ('masks/decks/deck_main.vox.txt', 'deck'), ('masks/masts/main.vox.txt', 'mast-main'),
                ('masks/masts/fore.vox.txt', 'mast-fore'), ('masks/masts/tack_spar.vox.txt', 'tack-spar'), ('masks/deco/stem_head.vox.txt', 'stem-head')):
    for k in load(fn):
        solid[k] = lab
for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
    key = p['mast']
    for (x, y, z) in load('masks/yards/lateen-%s.vox.txt' % key):
        solid[(int(round(x + 0.5 - p['pivot'][0] + p['at'][0] - 0.5)), int(round(y + 0.5 - p['pivot'][1] + p['at'][1] - 0.5)),
               int(round(z + 0.5 - p['pivot'][2] + p['at'][2] - 0.5)))] = 'yard-' + key

tmp = tempfile.mkdtemp()
obj = os.path.join(tmp, 'a.obj')
args = ['op=export', 'format=obj', 'work=' + ASM, 'out=' + obj, 'ropes=0']
if 'wind' in opt:
    args.append('wind=' + opt['wind'])
r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
if r.returncode != 0:
    raise SystemExit('export failed: ' + (r.stdout + r.stderr)[-800:])
V, cur, owner = [], None, []
for line in open(obj, encoding='utf-8'):
    if line.startswith('o '):
        cur = line.split('#', 1)[1].strip() if line.startswith('o sail_') and '#' in line else (line[2:].strip()[5:] if line.startswith('o sail_') else None)
    elif line.startswith('v '):
        x, y, z = map(float, line.split()[1:4])
        V.append((x, z, y))
        owner.append(cur)
V = np.array(V)
owner = np.array(owner, dtype=object)
keys = np.array(sorted(solid), float) + 0.5
tree = cKDTree(keys)
labs = [solid[k] for k in sorted(solid)]
R = {'wind': opt.get('wind', 'default'), 'sails': {}}
for nm in sorted({o for o in owner if o}):
    P = V[owner == nm]
    inside = {}
    for p in P:
        k = tuple(int(np.floor(v)) for v in p)
        if k in solid:
            inside[solid[k]] = inside.get(solid[k], 0) + 1
    d, i = tree.query(P)
    R['sails'][nm] = {'vertices': int(len(P)), 'vertices_inside_solid': inside, 'min_dist_cells': round(float(d.min()), 2),
                      'nearest_part': labs[int(i[int(np.argmin(d))])], 'y_range': [round(float(P[:, 1].min()), 1), round(float(P[:, 1].max()), 1)]}
print(json.dumps(R, ensure_ascii=False))
if 'json' in opt:
    with open(os.path.join(HERE, opt['json']), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
