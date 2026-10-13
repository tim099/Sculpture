# 階段二十驗收：只讀引擎的匯出（組裝件 list／parts／obj），跟設計那一側（verify_binnacle.json、nf_state stage19、verify_ladder_points.json）比。
# 用法：python -I -X utf8 -B check_binnacle.py <design> <組裝件 list> <parts.json> <obj> [偏移 dx,dy,dz]
#   偏移 ＝ 反向對照：羅經櫃的網格整批平移（＋我這邊的預期外框）
#   ① 結果帳：組裝件 ＝ nf_state stage19（模型不是格，格數不該變）
#   ② parts：模型 甲板-後/羅經櫃 的 meta ＝ {kind: binnacle}、外框 vs 我算的
#   ③ 碰撞：羅經櫃網格三角形重心往裡 0.02 格，落在實心格的有幾個
#   ④ 著地：底面三角形重心往下 0.5 格是實心的比例
#   ⑤ 四周：網格面上取樣，到別的模型（舵輪、舵輪座…）網格面、到每條繩的最近距離；companion 梯子 head 那一段（站的格 x head..head+2、頭頂 3 格）有沒有被外框蓋到
import sys, os, json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, NX, NY, NZ

off = np.array([float(v) for v in sys.argv[5].split(',')]) if len(sys.argv) > 5 else np.zeros(3)
V = json.load(open(os.path.join(D, 'verify_binnacle.json'), encoding='utf-8'))
LP = json.load(open(os.path.join(D, 'verify_ladder_points.json'), encoding='utf-8'))
a = np.loadtxt(sys.argv[2], delimiter=',', dtype=int, comments='#', ndmin=2)
E = np.zeros((NX, NY, NZ), np.int16); E[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
X = np.zeros((NX, NY, NZ), np.int16)
for k, v in state_after(D, 'stage19').items():
    if not k.endswith('_model'):
        m = v > 0; X[m] = v[m]
print('① 組裝件 vs stage19：', len(a), '／', int((X > 0).sum()), '缺', int(((X > 0) & (E == 0)).sum()), '多', int(((E > 0) & (X == 0)).sum()),
      '色差', int(((E > 0) & (X > 0) & (E != X)).sum()))
occ = E > 0

P = json.load(open(sys.argv[3], encoding='utf-8'))
mods = {m['path']: m for m in P['models']}
mb = mods.get('甲板-後/' + V['model']['name'])
if mb is None:
    print('② parts 裡沒有 甲板-後/' + V['model']['name'])
else:
    lo, hi = np.array(V['box_world'][0]), np.array(V['box_world'][1])
    print('② meta', mb['meta'], '＝ 我的' if mb['meta'] == V['model']['meta'] else '≠ 我的 %s' % V['model']['meta'],
          '｜外框 引擎', mb['box'], '｜我算的格心取樣外框', lo.round(2).tolist(), hi.round(2).tolist())

vs, vn, cur, tris, rope = [], [], None, {}, {}
for line in open(sys.argv[4], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('vn '):
        vn.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        head = line.split('#')[0].split()[1]
        cur = (head.split('_')[0], line.split('#', 1)[1].strip() if '#' in line else head)
    elif line.startswith('f ') and cur and cur[0] in ('model', 'rope'):
        ids = [t.split('/') for t in line.split()[1:]]
        (tris if cur[0] == 'model' else rope).setdefault(cur[1], []).append(([int(t[0]) - 1 for t in ids], int(ids[0][-1]) - 1 if len(ids[0]) > 2 and ids[0][-1] else -1))
vs = np.array(vs)[:, [0, 2, 1]]; vn = np.array(vn)[:, [0, 2, 1]] if vn else np.zeros((0, 3))          # obj 是 y 朝上（階段十三）
key = '甲板-後/' + V['model']['name']
T = tris[key]
idx = np.array([t[0] for t in T])
A = vs[idx] + off
nrm = vn[[t[1] for t in T]]
cen = A.mean(axis=1) - 0.02 * nrm
i = np.floor(cen).astype(int)
print('③ 碰撞三角形', int(occ[i[:, 0], i[:, 1], i[:, 2]].sum()), '／', len(T))
c2 = A.mean(axis=1)
zmin = c2[:, 2].min(); lowT = A[np.abs(c2[:, 2] - zmin) < 1e-6]
# 🩸 v1 只拿底面三角形的重心：底面被合併成 2 個大三角形 ⇒ 2 個點代表整個底面（網格的頂點／重心不代表網格，今天第四次）。改在底面上取樣。
g = [(p_ / 16, q_ / 16) for p_ in range(1, 16) for q_ in range(1, 16 - p_)]
low = np.concatenate([lowT[:, 0] + (lowT[:, 1] - lowT[:, 0]) * u + (lowT[:, 2] - lowT[:, 0]) * w for u, w in g])
j = np.floor(low + [0, 0, -0.5]).astype(int)
print('④ 著地（底面三角形 %d 個、取樣 %d 點，底 z %.3f）：正下方實心的比例 %.3f' % (len(lowT), len(low), zmin, float(occ[j[:, 0], j[:, 1], j[:, 2]].mean())))


def samples(Tri, n=8):
    g = [(p / n, q / n) for p in range(n + 1) for q in range(n + 1 - p)]
    return np.concatenate([Tri[:, 0] + (Tri[:, 1] - Tri[:, 0]) * u + (Tri[:, 2] - Tri[:, 0]) * w for u, w in g])


bs = samples(A)
blo, bhi = bs.min(0), bs.max(0)
near_m, near_r = [], []
for nm, TT in list(tris.items()) + list(rope.items()):
    if nm == key:
        continue
    Q = vs[np.array([t[0] for t in TT])]
    m = np.all((Q.max(1) > blo - 6) & (Q.min(1) < bhi + 6), axis=1)
    if not m.any():
        continue
    s = samples(Q[m], 6)
    s = s[np.all((s > blo - 6) & (s < bhi + 6), axis=1)]
    if not len(s):
        continue
    d = float(np.sqrt(((s[:, None, :] - bs[None, ::7]) ** 2).sum(-1)).min())
    (near_m if nm in tris else near_r).append((round(d, 2), nm))
print('⑤ 最近的模型', sorted(near_m)[:3], '｜最近的繩', sorted(near_r)[:3])
cp = [r for r in LP['ladders'] if r['ladder'] == 'companion'][0]
hx, hy, hz = cp['head']
lane = [(hx + k * cp['up_dir_x'], hy, hz + dz) for k in range(3) for dz in range(3)]      # head 往上梯方向 3 欄（ladder_points 的「平地」）× 頭頂 3 格
inb = [p for p in lane if np.all(np.array(p) + 0.5 >= blo) and np.all(np.array(p) + 0.5 <= bhi)]
print('   companion head 那一段 %d 格（%s..）：在羅經櫃外框裡 %d、是實心 %d｜羅經櫃外框 x %.2f–%.2f' % (
    len(lane), lane[0], len(inb), sum(int(occ[p]) for p in lane), blo[0], bhi[0]))
