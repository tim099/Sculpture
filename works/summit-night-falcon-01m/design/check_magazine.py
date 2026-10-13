# 階段十八驗收：只讀引擎匯出（組裝件 list／parts／obj），跟設計那一側（verify_magazine.json、nf_state stage18）比。
# 用法：python -I -X utf8 -B check_magazine.py <design> <組裝件 list> <parts.json> <obj> [偏移 dx,dy,dz]
#   ① 結果帳：組裝件 ＝ nf_state stage18
#   ② parts：關聯「彈藥庫」的 meta（kind=magazine、powder_lb）與 blast／door 的組裝件座標 vs 我算的；8 個桶的 meta
#   ③ 桶：網格三角形重心往裡 0.02 落在實心格的數（應 0）；底面三角形重心正下方是實心的比例（應 1）；桶跟桶之間最近距離
import sys, os, json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, NX, NY, NZ

off = np.array([float(v) for v in sys.argv[5].split(',')]) if len(sys.argv) > 5 else np.zeros(3)
V = json.load(open(os.path.join(D, 'verify_magazine.json'), encoding='utf-8'))
a = np.loadtxt(sys.argv[2], delimiter=',', dtype=int, comments='#', ndmin=2)
E = np.zeros((NX, NY, NZ), np.int16); E[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
W = state_after(D, 'stage18')
X = np.zeros((NX, NY, NZ), np.int16)
for k, v in W.items():
    if not k.endswith('_model'):
        m = v > 0; X[m] = v[m]
print('① 組裝件 vs stage18：', len(a), '／', int((X > 0).sum()), '缺', int(((X > 0) & (E == 0)).sum()), '多', int(((E > 0) & (X == 0)).sum()),
      '色差', int(((E > 0) & (X > 0) & (E != X)).sum()))
occ = E > 0
P = json.load(open(sys.argv[3], encoding='utf-8'))
link = [p for p in P['links'] if p.get('name') == V['link']['name'] or p.get('path') == V['link']['name']]
lk = link[0] if link else None
print('② 關聯 meta', lk and lk.get('meta'), '｜我的', V['link']['meta'])
worst = 0.0
for an in V['anchors']:
    got = None
    if lk and an['name'] in (lk.get('points') or {}):
        got = np.array(lk['points'][an['name']])
    e = np.array(an['world'], float) + 0.5 + off
    worst = max(worst, float(np.abs(got - e).max()) if got is not None else 9e9)
print('② blast／door 引擎 vs 我算的 最大差', round(worst, 4))
kegs = [m for m in P['models'] if m.get('path', '').startswith(V['link']['name'] + '/')]
print('② 桶', len(kegs), '個；meta', sorted({json.dumps(k['meta'], sort_keys=True) for k in kegs}))

vs, vn = [], []; cur = None; tris = {}
for line in open(sys.argv[4], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('vn '):
        vn.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        nm = line.split('#', 1)[1].strip() if '#' in line else ''
        cur = nm if nm.startswith(V['link']['name'] + '/') else None
    elif line.startswith('f ') and cur:
        ids = [t.split('/') for t in line.split()[1:]]
        tris.setdefault(cur, []).append(([int(t[0]) - 1 for t in ids], int(ids[0][-1]) - 1))
vs = np.array(vs)[:, [0, 2, 1]]; vn = np.array(vn)[:, [0, 2, 1]]          # obj 是 y 朝上
hits = 0; sup = []; cents = []
for nm, T in sorted(tris.items()):
    idx = np.array([t[0] for t in T]); nrm = vn[[t[1] for t in T]]
    cen = vs[idx].mean(axis=1) + off
    i = np.floor(cen - 0.02 * nrm).astype(int)
    hits += int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())
    low = cen[np.abs(cen[:, 2] - cen[:, 2].min()) < 1e-6]
    j = np.floor(low + [0, 0, -0.5]).astype(int)
    sup.append(float(occ[j[:, 0], j[:, 1], j[:, 2]].mean()))
    cents.append(vs[idx].reshape(-1, 3).mean(0))
c = np.array(cents)
dmin = min(float(np.linalg.norm(c[i] - c[j])) for i in range(len(c)) for j in range(i + 1, len(c))) if len(c) > 1 else 0
print('③ 桶網格 %d 個：碰撞三角形 %d｜底面著地 %s｜桶心最近距離 %.2f 格' % (len(tris), hits, [round(s, 2) for s in sup], dmin))
