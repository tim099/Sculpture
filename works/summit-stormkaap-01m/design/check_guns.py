# 階段十二驗收：只讀引擎的匯出（組裝件 list／parts／obj），跟設計那一側（verify_guns.json、masks）比。
# 用法：python -I -X utf8 -B check_guns.py <design> <匯出資料夾（ship_list.txt、parts.json、ship.obj）> <階段十一的 ship_list.txt> [偏移 dx,dy,dz]
#   偏移 ＝ 反向對照：把引擎給的砲（parts 的點、obj 的網格）整批平移，該報的要報出來。
# 量的東西：
#   ① 結果帳：組裝件 ＝ 階段十一的格子 ＋ 墊木（多 0、缺 0、顏色不同 0）；砲本身是模型、不在組裝件的格子裡
#   ② 固定點：parts 的 muzzle／breech…（引擎換算）vs 我用 at／pivot／scale／mirror／rotate 算的 —— 最大差
#   ③ 碰撞：obj 每門砲每個三角形的重心沿法線往裡 0.02 格，落在引擎實心格裡的數（每門）
#   ④ 砲口：parts 的 muzzle 沿砲口方向，離牆外面（verify 的 outer）幾格
#   ⑤ 著地：obj 網格最低那一層頂點（輪底），正下方那一格是實心的比例
#   ⑥ 砲碰砲：每門的 obj 三角形重心落在別門的外框（parts box）裡的數
import sys, os, json, re, math
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D, EX, PREV = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
off = np.array([float(v) for v in sys.argv[4].split(',')]) if len(sys.argv) > 4 else np.zeros(3)
V = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
rows = {r['host_link'] + '/' + r['model']: r for r in V['rows']}
rd = lambda p: np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


out = {}
# ① 結果帳
a = rd(os.path.join(EX, 'ship_list.txt')); b = rd(os.path.join(PREV, 'ship_list.txt'))
want = {tuple(r[:3]): int(r[3]) for r in b}
for P in V['pads'].values():
    for r in rd(os.path.join(D, P['file'])): want[tuple(r[:3])] = int(r[3])
got = {tuple(r[:3]): int(r[3]) for r in a}
out['ledger'] = {'engine': len(got), 'want': len(want), 'missing': sum(1 for k in want if k not in got), 'extra': sum(1 for k in got if k not in want),
                 'color_diff': sum(1 for k, v in want.items() if k in got and got[k] != v)}
occ = np.zeros((736, 261, 576), bool); occ[tuple(a[:, :3].T)] = True
# ② 固定點
PJ = json.load(open(os.path.join(EX, 'parts.json'), encoding='utf-8'))
M = {m['path']: m for m in PJ['models'] if m['path'] in rows}
out['models_found'] = len(M)
dmax = 0.0
for path, r in rows.items():
    T = V['types'][r['type']]; piv = np.array(T['pivot'])
    for name, at in T['anchors'].items():
        q = (np.array([at], float) + 0.5 - piv) * V['scale']
        if r['mirror'] == 'y': q[:, 1] = -q[:, 1]
        mine = rotz(q, r['rotate'][2])[0] + r['at']
        eng = np.array(M[path]['points'][name]) + off
        dmax = max(dmax, float(np.abs(mine - eng).max()))
out['anchor_max_diff'] = round(dmax, 4)
# ③ ⑤ ⑥ obj
S = {}; cur = None; Vv = []; F = []; vbase = nv = 0
for l in open(os.path.join(EX, 'ship.obj'), encoding='utf-8'):
    if l.startswith('o '):
        if cur in rows: S.setdefault(cur, []).append((np.array(Vv), np.array(F) - 1))
        m = re.match(r'o model_\d+ # (.+)', l.strip()); cur = m.group(1) if m else None; Vv = []; F = []; vbase = nv
    elif l.startswith('v '):
        nv += 1
        if cur in rows:
            x, z, y = map(float, l.split()[1:4]); Vv.append((x, y, z))
    elif l.startswith('f ') and cur in rows:
        F.append([int(t.split('/')[0]) - vbase for t in l.split()[1:4]])
if cur in rows: S.setdefault(cur, []).append((np.array(Vv), np.array(F) - 1))
boxes = {p: np.array(M[p]['box'], float) + np.concatenate([off, off]) for p in M}
coll, sup, cross, muz = {}, {}, {}, {}
for path, parts in S.items():
    Vg = np.vstack([v for v, _ in parts]) + off
    cs = []
    for v, f in parts:
        v = v + off; A, B_, C = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        n = np.cross(B_ - A, C - A); ln = np.linalg.norm(n, axis=1, keepdims=True); n = n / np.where(ln > 0, ln, 1)
        cs.append((A + B_ + C) / 3 + 0.02 * n)              # 🩸 讀 OBJ 時 y、z 對調 ⇒ 左右手性反了，算出來的法線朝內（頂面法線 z 平均 −1，量過）⇒ 往裡 ＝ ＋0.02 n
    cs = np.vstack(cs); i = np.floor(cs).astype(int)
    coll[path] = int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())
    zmin = Vg[:, 2].min()
    bc = []                                                  # 底面（三個頂點都在最低那一層）三角形的重心 ⇒ 正下方那一格
    for v, f in parts:
        v = v + off; zz = v[f][:, :, 2]
        k = (np.abs(zz - zmin) < 0.01).all(1)
        bc.append(v[f[k]].mean(1))
    j = np.floor(np.vstack(bc)).astype(int)
    sup[path] = round(float(occ[j[:, 0], j[:, 1], int(round(zmin)) - 1].mean()), 3)
    cross[path] = cs
    r = rows[path]; mz = np.array(M[path]['points']['muzzle']) + off
    ax = 1 if r['row'] in ('lower', 'upper') else 0
    sgn = {'砲-S': 1, '砲-P': -1}.get(r['model'][:3], -1 if r['row'] == 'stern' else 1)
    muz[path] = round(float((mz[ax] - r['outer']) * sgn), 3)
out['collision_tris'] = {k: v for k, v in coll.items() if v}
out['collision_total'] = sum(coll.values())
out['support_min'] = min(sup.values()); out['support_below_1'] = {k: v for k, v in sup.items() if v < 1}
# ⑥ 砲碰砲：每門往裡 0.02 的重心，落在別門的外框裡的 ⇒ 再看它離那門的往裡重心多近（< 0.5 格才算撞到同一塊）
from scipy.spatial import cKDTree
trees = {p: cKDTree(c) for p, c in cross.items()}
gg = {}
for p, c in cross.items():
    for p2, bx in boxes.items():
        if p2 == p: continue
        inb = c[((c >= bx[:3]) & (c <= bx[3:])).all(1)]
        if len(inb):
            gg[p + ' × ' + p2] = round(float(trees[p2].query(inb)[0].min()), 3)
out['gun_pair_min_dist'] = gg
out['muzzle_beyond_min'] = min(muz.values()); out['muzzle_beyond_below_1'] = {k: v for k, v in muz.items() if v < 1}
out['meshes'] = len(S)
print(json.dumps(out, ensure_ascii=False, indent=1))
if not off.any():
    with open(os.path.join(D, 'verify_guns_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
