# 階段十三驗收：只讀引擎的匯出（組裝件 list／parts／obj、-gun-4l 的 list），跟設計那一側（verify_guns.json、nf_state）比。
# 用法：python -I -X utf8 -B check_guns.py <design> <組裝件 list> <組裝件 parts.json> <組裝件 obj> <-gun-4l list> [偏移 dx,dy,dz]
#   偏移 ＝ 反向對照：把引擎給的砲（parts 的點、obj 的網格）整批平移，該報的要報出來。
# 量的東西：
#   ① 結果帳：組裝件格子 ＝ nf_state stage12（本階段一格都不該動）；-gun-4l ＝ masks/guns/gun4.vox.txt
#   ② 固定點：parts 的 muzzle／breech…（引擎換算）vs 我用 at／pivot／scale／mirror 算的 —— 最大差
#   ③ 碰撞：obj 每個三角形的重心沿法線往裡 0.02 格，落在引擎 list 的實心格裡的有幾個（每門）
#   ④ 砲口：parts 的 muzzle 離舷牆外面（引擎 list 在砲門下緣那一列最外那一格）幾格；砲軸在開口的哪裡
#   ⑤ 著地：obj 網格最低那一層頂點（輪底），正下方那一格是實心的比例
import sys, os, json, re
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, NX, NY, NZ

off = np.array([float(v) for v in sys.argv[6].split(',')]) if len(sys.argv) > 6 else np.zeros(3)
V = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
rows = {r['model']: r for r in V['rows']}


def read_list(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


# ① 結果帳
a = read_list(sys.argv[2])
E = np.zeros((NX, NY, NZ), np.int16)
E[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
W = state_after(D, 'stage12')
X = np.zeros((NX, NY, NZ), np.int16)
for v in W.values():
    m = v > 0
    X[m] = v[m]
miss = int(((X > 0) & (E == 0)).sum()); extra = int(((E > 0) & (X == 0)).sum()); cdiff = int(((E > 0) & (X > 0) & (E != X)).sum())
print('① 組裝件 vs stage12：', len(a), '／', int((X > 0).sum()), '缺', miss, '多', extra, '色差', cdiff)
g = read_list(sys.argv[5])
mine = read_list(os.path.join(D, V['gun']['file']))
sg = {tuple(r[:3]): r[3] for r in g}; sm = {tuple(r[:3]): r[3] for r in mine}
print('① -gun-4l vs gun4.vox.txt：', len(sg), '／', len(sm), '缺', len(set(sm) - set(sg)), '多', len(set(sg) - set(sm)),
      '色差', sum(1 for k in sm if k in sg and sg[k] != sm[k]))
occ = E > 0

# ② 固定點
P = json.load(open(sys.argv[3], encoding='utf-8'))
piv = np.array(V['gun']['pivot']); S = V['scale']
worst = 0.0; got = 0
for m in P['models']:
    if m['name'] not in rows:
        continue
    r = rows[m['name']]; side = -1 if r['mirror'] == 'y' else 1
    for k, c in V['gun']['anchors'].items():
        q = (np.array(c, float) + 0.5 - piv) * S
        q[1] *= side
        w = q + np.array(r['at'])
        e = np.array(m['points'][k]) + off
        worst = max(worst, float(np.abs(w - e).max())); got += 1
print('② 固定點', got, '個（12 門 × 7）引擎 vs 我算的 最大差', round(worst, 4))

# ③⑤ obj
vs, vn = [], []
cur = None; tris = {}
for line in open(sys.argv[4], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('vn '):
        vn.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        mm = re.search(r'#\s*(\S+)', line); cur = mm.group(1).split('/')[-1] if mm else None
    elif line.startswith('f ') and cur in rows:
        ids = [t.split('/') for t in line.split()[1:]]
        tris.setdefault(cur, []).append(([int(t[0]) - 1 for t in ids], int(ids[0][-1]) - 1))
vs = np.array(vs)[:, [0, 2, 1]]; vn = np.array(vn)[:, [0, 2, 1]]       # 引擎的 obj 是 y 朝上：(x, 作品 z, 作品 y) ⇒ 換回作品座標
hull = W['hull']
print('③④⑤ 每門：碰撞三角形／三角形數｜砲口伸出舷牆外（格）｜砲軸 z 在開口裡的位置（0 下緣、1 上緣）｜輪底著地')
tot_hit = 0; min_out = 9e9; sup_all = []
for name in sorted(rows, key=lambda s: (int(s[3:]), s[2])):
    r = rows[name]; side = 1 if r['side'] == 'S' else -1
    T = tris.get(name, [])
    idx = np.array([t[0] for t in T]); nrm = vn[[t[1] for t in T]]
    cen = vs[idx].mean(axis=1) - 0.02 * nrm + off
    i = np.floor(cen).astype(int)
    hits = int(occ[i[:, 0], i[:, 1], i[:, 2]].sum()); tot_hit += hits
    mz = [m for m in P['models'] if m['name'] == name][0]['points']['muzzle']
    mz = np.array(mz) + off
    x0, x1 = r['opening_x']; z0, z1 = r['opening_z']
    ys = [y for y in range(NY) if hull[int(round((x0 + x1 + 1) / 2 - 0.5)), y, z0 - 1] and (y - 80) * side > 0]
    outer = (max(ys) + 1) if side > 0 else min(ys)
    out = (mz[1] - outer) * side; min_out = min(min_out, out)
    pos = (mz[2] - z0) / (z1 + 1 - z0)
    vv = np.unique(vs[idx].reshape(-1, 3), axis=0) + off
    low = vv[vv[:, 2] <= vv[:, 2].min() + 1e-6]
    j = np.floor(low + [0, 0, -0.5]).astype(int)
    sup = float(occ[j[:, 0], j[:, 1], j[:, 2]].mean()); sup_all.append((name, sup))
    print(f'   {name}: {hits}／{len(T)}｜{out:.2f}｜{pos:.2f}｜{sup:.2f}（輪底 z {low[0, 2]:.2f}）')
print('③ 碰撞合計', tot_hit, '｜④ 砲口伸出最小', round(min_out, 2), '｜⑤ 沒全著地的：', [n for n, s in sup_all if s < 1.0])
