# 階段十六驗收：只讀引擎的匯出（組裝件 list／parts／obj），跟設計那一側（verify_steering.json、nf_state stage16）比。
# 用法：python -I -X utf8 -B check_steering.py <design> <組裝件 list> <parts.json> <obj> [偏移 dx,dy,dz]
#   ① 結果帳：組裝件 ＝ nf_state stage16
#   ② 固定點：parts 的 舵/tiller-end、舵輪/tiller-rope-a／b（引擎換算）vs 我算的
#   ③ 舵（含舵柄）網格三角形重心往裡 0.02 落在實心格的有幾個（靜止）
#   ④ 舵索 6 段：管子表面取樣點（離兩端 1.0 格以外）落在實心格、或落在舵輪座／舵輪的格子裡的有幾個（繩孔要讓它過得去）
import sys, os, json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, NX, NY, NZ

off = np.array([float(v) for v in sys.argv[5].split(',')]) if len(sys.argv) > 5 else np.zeros(3)
V = json.load(open(os.path.join(D, 'verify_steering.json'), encoding='utf-8'))
VH = json.load(open(os.path.join(D, 'verify_helm.json'), encoding='utf-8'))
a = np.loadtxt(sys.argv[2], delimiter=',', dtype=int, comments='#', ndmin=2)
E = np.zeros((NX, NY, NZ), np.int16); E[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
W = state_after(D, 'stage16')
X = np.zeros((NX, NY, NZ), np.int16)
for k, v in W.items():
    if not k.endswith('_model'):
        m = v > 0; X[m] = v[m]
print('① 組裝件 vs stage16：', len(a), '／', int((X > 0).sum()), '缺', int(((X > 0) & (E == 0)).sum()), '多', int(((E > 0) & (X == 0)).sum()),
      '色差', int(((E > 0) & (X > 0) & (E != X)).sum()))
occ = E > 0
P = json.load(open(sys.argv[3], encoding='utf-8'))
mods = {m['name']: m for m in P['models']}
S = VH['scale']; piv = np.array(VH['pivot']); at = np.array(VH['at'])
exp = {('舵', 'tiller-end'): np.array(V['anchors']['rudder'][0]['at']) + 0.5}
for x in V['anchors']['wheel']:
    exp[('舵輪', x['name'])] = (np.array(x['at']) + 0.5 - piv) * S + at
worst = max(float(np.abs(np.array(mods[m]['points'][k]) - (e + off)).max()) for (m, k), e in exp.items())
print('② 固定點', len(exp), '個 引擎 vs 我算的 最大差', round(worst, 4))

vs, vn = [], []; cur = None; tris = {}; rv = {}
names = {r['name'] for r in V['ropes']}
for line in open(sys.argv[4], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('vn '):
        vn.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        nm = line.split('#', 1)[1].strip() if '#' in line else ''
        cur = ('rope', nm) if 'rope_' in line.split('#')[0] else ('model', nm.split('/')[-1])
    elif line.startswith('f ') and cur:
        ids = [t.split('/') for t in line.split()[1:]]
        if cur == ('model', '舵'):
            tris.setdefault('舵', []).append(([int(t[0]) - 1 for t in ids], int(ids[0][-1]) - 1))
        elif cur[0] == 'rope' and cur[1] in names:
            rv.setdefault(cur[1], []).append([int(t[0]) - 1 for t in ids])
vs = np.array(vs)[:, [0, 2, 1]]; vn = np.array(vn)[:, [0, 2, 1]]          # obj 是 y 朝上（階段十三）
T = tris['舵']; idx = np.array([t[0] for t in T]); nrm = vn[[t[1] for t in T]]
cen = vs[idx].mean(axis=1) - 0.02 * nrm + off
i = np.floor(cen).astype(int)
print('③ 舵＋舵柄 網格碰撞三角形', int(occ[i[:, 0], i[:, 1], i[:, 2]].sum()), '／', len(T))
# 舵輪與座的格子（世界，0.02 m 子作品換過來；取格心）
def world_cells(path):
    c = np.loadtxt(os.path.join(D, path), delimiter=',', dtype=int, comments='#', ndmin=2)[:, :3].astype(float) + 0.5
    return c * 0 + ((c - piv) * S + at)
stand = np.loadtxt(os.path.join(D, VH['stand']['file']), delimiter=',', dtype=int, comments='#', ndmin=2)[:, :3]
holes = {tuple(map(int, l.split(',')[:3])) for l in open(os.path.join(D, V['stand_holes']['file']), encoding='utf-8') if not l.startswith('#')}
stand_set = {tuple(c) for c in stand} - holes
wheel_set = {tuple(map(int, l.split(',')[:3])) for l in open(os.path.join(D, VH['wheel']['file']), encoding='utf-8') if not l.startswith('#')}
tot = 0; per = {}
for r in V['ropes']:
    # 🩸 v1 只拿管子的頂點：直的繩（下垂 0）整段只有兩端兩圈頂點，中段一個都沒有 ⇒ 往船頭挪 1 格穿過甲板也報 0。改在三角形面上取樣。
    A = vs[np.array(rv[r['name']])[:, :3]]
    g = [(i_ / 12, j_ / 12) for i_ in range(13) for j_ in range(13 - i_)]
    Pv = np.concatenate([A[:, 0] + (A[:, 1] - A[:, 0]) * a_ + (A[:, 2] - A[:, 0]) * b_ for a_, b_ in g]) + off
    ends = []
    for s in (r['from'], r['to']):
        if s.startswith('model:舵/'):
            ends.append(exp[('舵', 'tiller-end')] + off)
        elif s.startswith('model:甲板-後/舵輪/'):
            ends.append(exp[('舵輪', s.split('/')[-1])] + off)
        else:
            nm = s.split('/')[-1]
            ends.append(np.array([x['at'] for x in V['anchors']['quarter'] if x['name'] == nm][0]) + 0.5 + off)
    far = np.all([np.linalg.norm(Pv - e, axis=1) > 1.0 for e in ends], axis=0)
    h = 0
    for p in Pv[far]:
        k = tuple(np.floor(p).astype(int))
        sk = tuple(np.floor((p - at) / S + piv).astype(int))
        if occ[k] or sk in stand_set or sk in wheel_set:
            h += 1
    per[r['name']] = h; tot += h
print('④ 舵索管子頂點（中段）落在實心／舵輪座／舵輪：合計', tot, per)
