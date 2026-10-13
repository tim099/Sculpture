# 階段十九驗收：只讀引擎的匯出（組裝件 list、parts、obj、sub=ropes 的輸出），跟設計那一側（nf_state stage18 ＋ verify_ladders.json）比。
# 用法：python -I -X utf8 -B check_ladders.py <design> <組裝件 list> <parts json> <組裝件 obj> <sub=ropes 輸出> [偏移 dx,dy,dz]
#   偏移 ＝ 反向對照：我這邊的梯子格、固定點、繩端點整批平移，該報的要報出來。
#   ① 結果帳：nf_state stage18 ＋ 梯子清單 vs 組裝件 list —— 缺／多／色差
#   ② 左右對稱：組裝件 list 自己 y ↔ 160 − y（含顏色）
#   ③ parts：kind=ladders 的關聯、固定點 24 個；遊戲那 12 個 vs verify_ladder_points（＋0.5）；
#      而且用另一條路量「腳踩的那一格」：那一格是空的、正下方是實心（lo／hi 正下方是踏板色）
#   ④ obj：梯子的格有沒有被別的繩／帆／模型穿過（三角形面上取樣，⛔ 不只看頂點；扶手繩自己不算）；扶手繩中段離兩端 1.5 格外落在實心幾次
#      （v1 報 companion 兩條各 6：查了是繩從柱頂往下垂、貼著自己那根柱 (111,76|84,46) ⇒ 自己的柱分開報）
#   ⑤ 扶手繩：6 條 ok、兩端 引擎 vs 我算的
import sys, os, json, re
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, NX, NY, NZ

off = np.array([int(v) for v in sys.argv[6].split(',')]) if len(sys.argv) > 6 else np.zeros(3, int)
V = json.load(open(os.path.join(D, 'verify_ladders.json'), encoding='utf-8'))
LP = json.load(open(os.path.join(D, 'verify_ladder_points.json'), encoding='utf-8'))
TREAD = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['ladders']['colors']['tread']

# ① 結果帳
exp = np.zeros((NX, NY, NZ), np.int16)
for k, w in state_after(D, 'stage18').items():
    if not k.endswith('_model'):
        exp = np.where(w > 0, w, exp)
lad = np.loadtxt(os.path.join(D, V['file']['path']), delimiter=',', dtype=int, comments='#', ndmin=2)
q = lad[:, :3] + off
exp[q[:, 0], q[:, 1], q[:, 2]] = lad[:, 3]
a = np.loadtxt(sys.argv[2], delimiter=',', dtype=int, comments='#', ndmin=2)
got = np.zeros((NX, NY, NZ), np.int16)
got[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
miss = int(((exp > 0) & (got == 0)).sum()); extra = int(((got > 0) & (exp == 0)).sum()); cdiff = int(((exp > 0) & (got > 0) & (exp != got)).sum())
print('① 結果帳 引擎 %d 格／設計 %d 格：缺 %d、多 %d、色差 %d' % (len(a), int((exp > 0).sum()), miss, extra, cdiff))

# ② 左右對稱
print('② 左右對稱（y ↔ 160 − y，含顏色）不同的格：%d' % int((got != got[:, ::-1, :]).sum()))

# ③ parts
P = json.load(open(sys.argv[3], encoding='utf-8'))
L = [l for l in P['links'] if (l.get('meta') or {}).get('kind') == 'ladders']
pts = L[0]['points'] if L else {}
worst, n, bad_stand = 0.0, 0, []
for r in LP['ladders']:
    for k in ('foot', 'lo', 'hi', 'head'):
        nm = '%s.%s' % (r['ladder'], k)
        if nm not in pts:
            bad_stand.append(nm + ' 沒有'); continue
        e = np.array(pts[nm])
        worst = max(worst, float(np.abs(e - (np.array(r[k]) + off + 0.5)).max())); n += 1
        c = np.floor(e).astype(int)
        below = got[c[0], c[1], c[2] - 1]
        if got[tuple(c)] != 0 or below == 0 or (k in ('lo', 'hi') and below != TREAD):
            bad_stand.append('%s 那格 %d、下面 %d' % (nm, got[tuple(c)], below))
print('③ kind=ladders 關聯 %d 個（%s）、固定點 %d 個；遊戲點 %d 個 引擎 vs 算的（＋0.5）最大差 %g｜腳踩那格不是「空、下面實心（lo／hi 下面是踏板）」：%s'
      % (len(L), L[0]['path'] if L else '-', len(pts), n, worst, bad_stand or '無'))

# ④ obj
vs, fa, cur, kind = [], {}, None, None
for line in open(sys.argv[4], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        cur = line.split('#', 1)[1].strip() if '#' in line else line.split()[1]
        kind = line.split()[1].split('_')[0]
    elif line.startswith('f ') and kind in ('rope', 'sail', 'model'):
        fa.setdefault((kind, cur), []).append([int(t.split('/')[0]) - 1 for t in line.split()[1:4]])
vs = np.array(vs)[:, [0, 2, 1]]                         # obj 是 y 朝上 ⇒ 換回作品座標


def samples(tris, step=0.25):
    out = []
    for t in tris:
        a_, b_, c_ = t
        m = int(np.ceil(max(np.linalg.norm(b_ - a_), np.linalg.norm(c_ - a_), np.linalg.norm(c_ - b_)) / step)) + 1
        i, j = np.meshgrid(np.arange(m + 1), np.arange(m + 1), indexing='ij'); k = (i + j) <= m
        out.append(a_ + np.outer(i[k] / m, b_ - a_) + np.outer(j[k] / m, c_ - a_))
    return np.concatenate(out) if out else np.zeros((0, 3))


ladset = set(map(tuple, q))
box = (q.min(0) - 2, q.max(0) + 3)
hit = {}
manrope_names = {r['name'] for r in V['ropes']}
for (kind, nm), F in fa.items():
    if nm in manrope_names:
        continue
    T = vs[np.array(F)]
    sel = ((T.max(1) >= box[0]) & (T.min(1) <= box[1])).all(1)
    if not sel.any():
        continue
    s = np.floor(samples(T[sel])).astype(int)
    h = len({tuple(p) for p in s} & ladset)
    if h:
        hit[nm] = h
print('④a 梯子的格被別的繩／帆／模型穿過：%s' % (hit or '無'))
mr = {}
end = {}
for line in open(sys.argv[5], encoding='utf-8'):
    m = re.match(r'- . `([^`]+)`［(\w+)］ \S+ \(([-\d.]+),([-\d.]+),([-\d.]+)\) → \S+ \(([-\d.]+),([-\d.]+),([-\d.]+)\)', line)
    if m and m.group(1) in manrope_names:
        end[m.group(1)] = (m.group(2), np.array([float(m.group(i)) for i in (3, 4, 5)]), np.array([float(m.group(i)) for i in (6, 7, 8)]))
for nm in manrope_names:
    F = fa.get(('rope', nm))
    if not F or nm not in end:
        mr[nm] = 'obj 或 sub=ropes 裡沒有'; continue
    S = samples(vs[np.array(F)])
    A, B = end[nm][1], end[nm][2]
    far = (np.linalg.norm(S - A, axis=1) > 1.5) & (np.linalg.norm(S - B, axis=1) > 1.5)
    k = np.floor(S[far]).astype(int)
    solid = got[k[:, 0], k[:, 1], k[:, 2]] > 0
    ownpost = np.zeros(len(k), bool)                    # 自己那兩根扶手柱（柱頂往下那一欄）：繩從柱頂的眼出去，貼著自己的柱子不算撞
    for E_ in (A, B):
        ownpost |= (k[:, 0] == int(np.floor(E_[0]))) & (k[:, 1] == int(np.floor(E_[1]))) & (k[:, 2] <= int(np.floor(E_[2])))
    h, hp = int((solid & ~ownpost).sum()), int((solid & ownpost).sum())
    if h or hp:
        mr[nm] = '撞 %d／貼自己的柱 %d' % (h, hp)
print('④b 扶手繩中段（離兩端 1.5 格外）取樣點落在實心：%s' % (mr or '無'))

# ⑤ 扶手繩
an = {x['name']: np.array(x['at']) + off + 0.5 for x in V['anchors']}
worst, st = 0.0, []
for r in V['ropes']:
    if r['name'] not in end:
        st.append(r['name'] + ' 沒有'); continue
    s_, A, B = end[r['name']]
    if s_ != 'ok':
        st.append('%s %s' % (r['name'], s_))
    worst = max(worst, float(np.abs(A - an[r['from'].split('/')[-1]]).max()), float(np.abs(B - an[r['to'].split('/')[-1]]).max()))
print('⑤ 扶手繩 %d 條：非 ok／缺 %s｜兩端 引擎 vs 我算的 最大差 %g' % (len(V['ropes']), st or '無', worst))
