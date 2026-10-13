# 階段十五驗收：只讀引擎的匯出（組裝件 list／parts／obj），跟設計那一側（verify_helm.json、nf_state stage15）比。
# 用法：python -I -X utf8 -B check_helm.py <design> <組裝件 list> <parts.json> <obj> [偏移 dx,dy,dz]
#   ① 結果帳：組裝件 ＝ nf_state stage15（舵不再是格、gudgeon 在船殼）
#   ② 固定點：parts 的 舵/stock-top、舵輪/axle…（引擎換算）vs 我算的
#   ③ 碰撞：舵、舵輪、舵輪座的網格三角形重心往裡 0.02 格，落在實心格的有幾個
#   ④ 舵的網格（靜止）＝ 原本舵的格扣 gudgeon：網格頂點的外框 vs 格子外框
#   ⑤ 舵輪四周：舵輪與座的網格頂點到 boom 網格、到每條繩管頂點的最近距離；底座最低那層頂點正下方是實心的比例
import sys, os, json, re
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, NX, NY, NZ

off = np.array([float(v) for v in sys.argv[5].split(',')]) if len(sys.argv) > 5 else np.zeros(3)
V = json.load(open(os.path.join(D, 'verify_helm.json'), encoding='utf-8'))
a = np.loadtxt(sys.argv[2], delimiter=',', dtype=int, comments='#', ndmin=2)
E = np.zeros((NX, NY, NZ), np.int16); E[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
W = state_after(D, 'stage15')
X = np.zeros((NX, NY, NZ), np.int16)
for k, v in W.items():
    if not k.endswith('_model'):
        m = v > 0; X[m] = v[m]
print('① 組裝件 vs stage15：', len(a), '／', int((X > 0).sum()), '缺', int(((X > 0) & (E == 0)).sum()), '多', int(((E > 0) & (X == 0)).sum()),
      '色差', int(((E > 0) & (X > 0) & (E != X)).sum()))
occ = E > 0

P = json.load(open(sys.argv[3], encoding='utf-8'))
mods = {m['name']: m for m in P['models']}
S = V['scale']; piv = np.array(V['pivot']); at = np.array(V['at'])
exp = {('舵輪', k): (np.array(c) + 0.5 - piv) * S + at for k, c in V['wheel']['anchors'].items()}
exp.update({('舵輪座', k): (np.array(c) + 0.5 - piv) * S + at for k, c in V['stand']['anchors'].items()})
exp.update({('舵', k): np.array(c) + 0.5 for k, c in V['rudder']['anchors'].items()})       # 舵：scale 1、at ＝ pivot ⇒ 子作品座標 ＝ 世界
worst = 0.0
for (mn, k), e in exp.items():
    worst = max(worst, float(np.abs(np.array(mods[mn]['points'][k]) - (e + off)).max()))
print('② 固定點', len(exp), '個 引擎 vs 我算的 最大差', round(worst, 4), '｜meta 舵', mods['舵']['meta'], '｜舵輪', mods['舵輪']['meta'])

vs, vn = [], []; cur = None; tris = {}; verts = {}
want = {'舵', '舵輪', '舵輪座', 'yard-main-boom'}
for line in open(sys.argv[4], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('vn '):
        vn.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        nm = line.split('#', 1)[1].strip().split('/')[-1] if '#' in line else None
        cur = ('rope', nm) if 'rope_' in line.split('#')[0] else ('model', nm)
    elif line.startswith('f ') and cur:
        ids = [t.split('/') for t in line.split()[1:]]
        if cur[0] == 'model' and cur[1] in want:
            tris.setdefault(cur[1], []).append(([int(t[0]) - 1 for t in ids], int(ids[0][-1]) - 1))
        if cur[0] == 'rope':
            verts.setdefault(cur[1], set()).update(int(t[0]) - 1 for t in ids)
vs = np.array(vs)[:, [0, 2, 1]]; vn = np.array(vn)[:, [0, 2, 1]]          # obj 是 y 朝上（階段十三）
for mn in ('舵', '舵輪', '舵輪座'):
    T = tris[mn]; idx = np.array([t[0] for t in T]); nrm = vn[[t[1] for t in T]]
    cen = vs[idx].mean(axis=1) - 0.02 * nrm + off
    i = np.floor(cen).astype(int)
    print('③', mn, '碰撞三角形', int(occ[i[:, 0], i[:, 1], i[:, 2]].sum()), '／', len(T))
rv = np.unique(vs[np.array([t[0] for t in tris['舵']])].reshape(-1, 3), axis=0) + off
rc = np.argwhere(W['rudder_model'] > 0)
print('④ 舵網格外框', rv.min(0).round(3).tolist(), rv.max(0).round(3).tolist(), '｜格子外框', rc.min(0).tolist(), (rc.max(0) + 1).tolist())
hv = np.unique(np.concatenate([vs[np.array([t[0] for t in tris[m]])].reshape(-1, 3) for m in ('舵輪', '舵輪座')]), axis=0) + off
# 🩸 v1 拿頂點對頂點：boom 整根只有 120 個頂點（擠在兩端與台階），中段是長三角形 ⇒ 量到的是舵輪到 boom 尾端（45.6 格）。改在三角形面上密集取樣。
def tri_samples(T, n=24):
    A = vs[np.array([t[0] for t in T])]
    g = [(i / n, j / n) for i in range(n + 1) for j in range(n + 1 - i)]
    return np.concatenate([A[:, 0] + (A[:, 1] - A[:, 0]) * a_ + (A[:, 2] - A[:, 0]) * b_ for a_, b_ in g])
bv = tri_samples(tris['yard-main-boom'])
d_boom = float(np.sqrt(((hv[:, None, :] - bv[None]) ** 2).sum(-1)).min())
near = []
for nm, ids in verts.items():
    rvv = vs[sorted(ids)]
    lo, hi = hv.min(0) - 8, hv.max(0) + 8
    rvv = rvv[np.all((rvv > lo) & (rvv < hi), axis=1)]
    if len(rvv):
        near.append((round(float(np.sqrt(((rvv[:, None, :] - hv[None]) ** 2).sum(-1)).min()), 2), nm))
# 🩸 v1 拿底面頂點：外圈頂點剛好在格子邊界上，floor 落到隔壁那一格 ⇒ 報 0.5。改用底面三角形的重心。
T = tris['舵輪座']; idx = np.array([t[0] for t in T]); cen = vs[idx].mean(axis=1) + off
zmin = cen[:, 2].min(); low = cen[np.abs(cen[:, 2] - zmin) < 1e-6]
j = np.floor(low + [0, 0, -0.5]).astype(int)
print('⑤ 舵輪到 boom 網格最近', round(d_boom, 2), '格｜最近的繩', sorted(near)[:4], '｜底座著地', round(float(occ[j[:, 0], j[:, 1], j[:, 2]].mean()), 2), '（底 z', low[0, 2], '）')
