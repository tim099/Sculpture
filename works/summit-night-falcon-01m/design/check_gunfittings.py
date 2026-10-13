# 階段十四驗收：只讀引擎的匯出（組裝件 list、sub=ropes 的輸出、obj），跟設計那一側（verify_gunfittings.json、verify_guns.json、nf_state）比。
# 用法：python -I -X utf8 -B check_gunfittings.py <design> <組裝件 list> <sub=ropes 輸出> <組裝件 obj> [偏移 dx,dy,dz]
#   偏移 ＝ 反向對照：我這邊的預期端點、和 obj 的繩網格整批平移，該報的要報出來。
# 量的東西：
#   ① 結果帳：組裝件格子 ＝ nf_state stage14
#   ② 繩：60 條都在、state ok；兩端（引擎解出來的）vs 我算的（砲的固定點照 at／pivot／scale／mirror、環的格心；P 舷鏡過去）—— 最大差
#   ③ 中段：obj 裡每條砲索的管子頂點，離兩端各 1.5 格以外的，落在實心格（引擎 list）或別門砲（不算自己這門）的有幾個
#   ④ 舊繩：281 條的兩端沒動（跟階段十三的 sub=ropes 比；給第五個參數之外的環境變數 OLD_ROPES 才比）
import sys, os, json, re
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, NX, NY, NZ

off = np.array([float(v) for v in sys.argv[5].split(',')]) if len(sys.argv) > 5 else np.zeros(3)
V = json.load(open(os.path.join(D, 'verify_gunfittings.json'), encoding='utf-8'))
VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))


def read_list(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


a = read_list(sys.argv[2])
E = np.zeros((NX, NY, NZ), np.int16); E[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
W = state_after(D, 'stage14')
X = np.zeros((NX, NY, NZ), np.int16)
for v in W.values():
    m = v > 0; X[m] = v[m]
print('① 組裝件 vs stage14：', len(a), '／', int((X > 0).sum()), '缺', int(((X > 0) & (E == 0)).sum()), '多', int(((E > 0) & (X == 0)).sum()),
      '色差', int(((E > 0) & (X > 0) & (E != X)).sum()))
occ = E > 0


def parse(path):
    R = {}
    pat = re.compile(r'^- ([✓✗]) `([^`]+)`［(\w+)］ (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\) → (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\)')
    for l in open(path, encoding='utf-8'):
        m = pat.match(l.strip())
        if m:
            g = m.groups()
            R[g[1]] = {'state': g[2], 'a': np.array([float(v) for v in g[4:7]]), 'b': np.array([float(v) for v in g[8:11]])}
    return R


R = parse(sys.argv[3])
piv = np.array(VG['gun']['pivot']); S = VG['scale']
rows = {r['model']: r for r in VG['rows']}


def gun_pt(model, k):
    r = rows[model]
    q = (np.array(VG['gun']['anchors'][k], float) + 0.5 - piv) * S
    if r['mirror'] == 'y':
        q[1] = -q[1]
    return q + np.array(r['at'])


anc = {x['name']: np.array(x['world'], float) + 0.5 for x in V['anchors']}


def endpoint(s):
    if s.startswith('model:'):
        _, model, k = s[len('model:'):].split('/')
        return gun_pt(model, k)
    fl, nm = s.split('/')
    p = anc[nm].copy()
    if fl.endswith('-鏡像'):
        p[1] = 161 - p[1]
    return p


worst = 0.0; missing = []; bad = []
for r in V['ropes']:
    e = R.get(r['name'])
    if e is None:
        missing.append(r['name']); continue
    if e['state'] != 'ok':
        bad.append(r['name'])
    for k, s in (('a', r['from']), ('b', r['to'])):
        worst = max(worst, float(np.abs(e[k] - (endpoint(s) + off)).max()))
print('② 砲索', len(V['ropes']), '條：缺', missing, '非 ok', bad, '｜兩端 引擎 vs 我算的 最大差', round(worst, 4))

# ③ obj
gcells = [tuple(map(int, l.split(',')[:3])) for l in open(os.path.join(D, VG['gun']['file']), encoding='utf-8') if not l.startswith('#')]
gc = np.array(gcells, float) + 0.5
gunc = {}
for m, r in rows.items():
    q = (gc - piv) * S
    if r['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    gunc[m] = set(map(tuple, np.floor(q + np.array(r['at'])).astype(int)))
vs = []; cur = None; ids = {}
names = {r['name'] for r in V['ropes']}
for line in open(sys.argv[4], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        cur = line.split('#', 1)[1].strip() if '#' in line else None
    elif line.startswith('f ') and cur in names:
        ids.setdefault(cur, set()).update(int(t.split('/')[0]) - 1 for t in line.split()[1:])
vs = np.array(vs)[:, [0, 2, 1]]                         # obj 是 y 朝上 ⇒ 換回作品座標（階段十三的坑）
tot = 0; per = {}
for r in V['ropes']:
    if r['name'] not in ids:
        per[r['name']] = 'obj 裡沒有'; continue
    P = vs[sorted(ids[r['name']])] + off
    A, B = endpoint(r['from']) + off, endpoint(r['to']) + off
    far = (np.linalg.norm(P - A, axis=1) > 1.5) & (np.linalg.norm(P - B, axis=1) > 1.5)
    own = 'model:甲板-主/' + r['name'].split('.')[0]
    own_cells = gunc[r['name'].split('.')[0]]
    h = 0
    for p in P[far]:
        k = tuple(np.floor(p).astype(int))
        if not (0 <= k[0] < NX and 0 <= k[1] < NY and 0 <= k[2] < NZ):
            continue
        if occ[k]:
            h += 1
        elif any(k in c for m, c in gunc.items() if c is not own_cells):
            h += 1
    if h:
        per[r['name']] = h
    tot += h
print('③ 中段頂點落在實心或別門砲：合計', tot, '｜有的繩：', per if per else '無')
