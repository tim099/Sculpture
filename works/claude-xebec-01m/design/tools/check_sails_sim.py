# 利劍號 步驟 8（TASK-0022）：掛好的帆布（引擎 export obj，作品預設風／秒數）對船的格子 —— 平面三角形的讀數看不到鼓起來的那一塊，這一把看得到。
#   出處：蠍子號 claude-galiot-01m/design/tools/check_sails_sim.py（海鷗號 → 星辰號的做法：export obj ropes=0、讀 o sail_ 的頂點、
#         OBJ 軸 (x, z, y) ⇒ 雕刻 (vx, vz, vy)）。改：實心格換成利劍號的清單（船殼＋換色、三層甲板、梯子、長喙、船尾平台、窗玻璃、三根桅、
#         三根帆桁的世界格）；桅孔步驟 5 就刻在甲板清單裡（不用再扣）；篷架是 deco 模型，另外算（帆碰到篷不算穿船，但要報）。
#   用法：python -I -X utf8 tools/check_sails_sim.py [--wind=x,y,z] [--json=<輸出檔>]
#     --wind：用這個風 export（反向對照：鼓的方向要跟著變、讀數要動）
import sys, os, json, subprocess, tempfile
import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
SENATE = wio.SENATE
ASM = 'claude-xebec-01m-assembly'
opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {tuple(map(int, r[:3])) for r in a}


solid = {}
for fn, lab in (('masks/hull/hull_01.vox.txt', 'hull'), ('masks/step6/hull_paint.vox.txt', 'hull'), ('masks/decks/hold.vox.txt', 'deck-hold'),
                ('masks/decks/main.vox.txt', 'deck-main'), ('masks/decks/quarter.vox.txt', 'deck-quarter'), ('masks/ladders/main.vox.txt', 'ladders'),
                ('masks/ladders/quarter.vox.txt', 'ladders'), ('masks/deco/beak.vox.txt', 'beak'), ('masks/deco/platform.vox.txt', 'platform'),
                ('masks/deco/glass.vox.txt', 'glass'), ('masks/deco/awning.vox.txt', 'awning(deco)'),
                ('masks/masts/mizzen.vox.txt', 'mast-mizzen'), ('masks/masts/main.vox.txt', 'mast-main'), ('masks/masts/fore.vox.txt', 'mast-fore')):
    for k in load(fn):
        solid[k] = lab
for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
    for (x, y, z) in load('masks/yards/lateen-%s.vox.txt' % p['mast']):
        solid[(int(round(x + 0.5 - p['pivot'][0] + p['at'][0] - 0.5)), int(round(y + 0.5 - p['pivot'][1] + p['at'][1] - 0.5)),
               int(round(z + 0.5 - p['pivot'][2] + p['at'][2] - 0.5)))] = 'yard-' + p['mast']

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
    inside, where = {}, {}
    for p in P:
        k = tuple(int(np.floor(v)) for v in p)
        if k in solid:
            inside[solid[k]] = inside.get(solid[k], 0) + 1
            if not solid[k].startswith('yard-'):
                # 穿多深：頂點到最近一個不是實心的格（方塊）的距離（格心距離會把 0.7 格深報成 0.4，verifier8）
                dep = min(np.linalg.norm(np.maximum(np.abs(p - (np.array(e) + 0.5)) - 0.5, 0))
                          for e in [(k[0] + a, k[1] + b, k[2] + c) for a in range(-3, 4) for b in range(-3, 4) for c in range(-3, 4)] if e not in solid)
                where.setdefault(solid[k], []).append([round(float(v), 1) for v in p] + [round(float(dep), 2)])
    d, i = tree.query(P)
    byp = {}
    for lab in sorted(set(labs)):
        kk = np.array([k for k in sorted(solid) if solid[k] == lab], float) + 0.5
        byp[lab] = round(float(cKDTree(kk).query(P)[0].min()), 2)
    R.setdefault('min_dist_by_part', {})[nm] = byp
    R['sails'][nm] = {'vertices': int(len(P)), 'vertices_inside_solid': inside, 'inside_not_yard_at': where, 'min_dist_cells': round(float(d.min()), 2),
                      'nearest_part': labs[int(i[int(np.argmin(d))])], 'x_range': [round(float(P[:, 0].min()), 1), round(float(P[:, 0].max()), 1)],
                      'y_range': [round(float(P[:, 1].min()), 1), round(float(P[:, 1].max()), 1)], 'z_range': [round(float(P[:, 2].min()), 1), round(float(P[:, 2].max()), 1)]}
print(json.dumps(R, ensure_ascii=False))
if 'json' in opt:
    with open(os.path.join(HERE, opt['json']), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
