# 階段十四讀數（落格之後）：只讀引擎的匯出，跟設計那一側（verify_gunfittings.json、verify_guns.json、階段十三的組裝件 list）比。
# 從夜隼號 check_gunfittings.py 改（兩件子作品、不鏡像、砲的 rotate）。
# 用法：python -I -X utf8 -B check_gunfittings.py <design> <stage13 匯出資料夾> <stage14 匯出資料夾> [偏移 dx,dy,dz]
#   stage14 匯出資料夾裡：assembly.list.txt（export list）、ropes.txt（sub=ropes 的輸出）、parts.json（export parts）、assembly.obj（export obj）
#   偏移 ＝ 反向對照：我這邊的預期（環的格心、砲的固定點）整批平移，該報的要報出來。
# 量的東西：
#   ① 結果帳：stage14 組裝件格子 ＝ stage13 ∪ 環（兩份清單），缺／多／色差
#   ② 環的固定點：parts.json 裡 甲板-下/砲具、甲板-上/砲具 的 points（引擎換算過的世界座標）vs 我算的格心
#   ③ 繩：206 條都在、state ok；兩端（引擎解出來的）vs 我算的 —— 最大差；舊繩條數不變
#   ④ 中段：obj 裡每條砲索的管子頂點，離兩端各 1.5 格以外的，落在實心格或別門砲（不算自己這門）的有幾個
import sys, os, json, re, math
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); E13 = os.path.abspath(sys.argv[2]); E14 = os.path.abspath(sys.argv[3])
off = np.array([float(v) for v in sys.argv[4].split(',')]) if len(sys.argv) > 4 else np.zeros(3)
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
NX, NY, NZ = plan['frame']['NX'], plan['frame']['NY'], plan['frame']['NZ_work']
V = json.load(open(os.path.join(D, 'verify_gunfittings.json'), encoding='utf-8'))
VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
S = VG['scale']


def read_list(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


# ① 結果帳
a13 = read_list(os.path.join(E13, 'ship_list.txt')); a14 = read_list(os.path.join(E14, 'assembly.list.txt'))
X = np.zeros((NX, NY, NZ), np.int16); X[a13[:, 0], a13[:, 1], a13[:, 2]] = a13[:, 3]
for st in V['stamp_order']:
    w = [x for x in V['works'] if x['work'] == st['work']][0]
    m = read_list(os.path.join(D, st['file']))
    p = m[:, :3] + np.array(w['frame_at'])
    assert not X[tuple(p.T)].any(), '環落在原本有格的地方'
    X[tuple(p.T)] = m[:, 3]
E = np.zeros((NX, NY, NZ), np.int16); E[a14[:, 0], a14[:, 1], a14[:, 2]] = a14[:, 3]
print('① 組裝件 stage14 %d 格 vs stage13 ∪ 環 %d 格：缺 %d、多 %d、色差 %d' % (len(a14), int((X > 0).sum()), int(((X > 0) & (E == 0)).sum()),
      int(((E > 0) & (X == 0)).sum()), int(((E > 0) & (X > 0) & (E != X)).sum())))
occ = E > 0

# ② 環的固定點
PJ = json.load(open(os.path.join(E14, 'parts.json'), encoding='utf-8'))
eng = {}
for l in PJ['links']:
    if l['path'].endswith('/砲具'):
        for k, v in (l.get('points') or {}).items():
            eng[l['path'].split('/')[0] + '/' + k] = np.array(v, float)
worst = 0.0; miss = []
for an in V['anchors']:
    e = eng.get(an['deck'] + '/' + an['name'])
    if e is None:
        miss.append(an['name']); continue
    worst = max(worst, float(np.abs(e - (np.array(an['world'], float) + 0.5 + off)).max()))
print('② 環的固定點 %d 個：引擎缺 %d｜引擎 vs 我算的格心 最大差 %.4f' % (len(V['anchors']), len(miss), worst))


# ③ 繩
def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2]])


rows = {r['host_link'] + '/' + r['model']: r for r in VG['rows']}


def gun_pt(key, k):
    r = rows[key]; tp = VG['types'][r['type']]
    q = (np.array(tp['anchors'][k], float) + 0.5 - np.array(r['pivot'], float)) * S
    if r['mirror'] == 'y':
        q[1] = -q[1]
    return rotz(q, r['rotate'][2]) + np.array(r['at'], float)


anc = {an['deck'] + '/砲具/' + an['name']: np.array(an['world'], float) + 0.5 for an in V['anchors']}


def endpoint(s):
    if s.startswith('model:'):
        d, m, k = s[len('model:'):].split('/')
        return gun_pt(d + '/' + m, k)
    return anc[s].copy()


pat = re.compile(r'^- ([✓✗]) `([^`]+)`［(\w+)］ (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\) → (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\)')
R = {}
for line in open(os.path.join(E14, 'ropes.txt'), encoding='utf-8'):
    m = pat.match(line.strip())
    if m:
        g = m.groups()
        R[g[1]] = {'state': g[2], 'a': np.array([float(v) for v in g[4:7]]), 'b': np.array([float(v) for v in g[8:11]])}
worst = 0.0; missing = []; bad = []
for r in V['ropes']:
    e = R.get(r['name'])
    if e is None:
        missing.append(r['name']); continue
    if e['state'] != 'ok':
        bad.append(r['name'])
    for k, s in (('a', r['from']), ('b', r['to'])):
        worst = max(worst, float(np.abs(e[k] - (endpoint(s) + off)).max()))
print('③ 砲索 %d 條：缺 %d、非 ok %d｜兩端 引擎 vs 我算的 最大差 %.3f（引擎印到 0.1）｜ropes.txt 全部 %d 條' % (len(V['ropes']), len(missing), len(bad), worst, len(R)))

# ④ obj 中段
offs = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
gunc = {}
for key, r in rows.items():
    tp = VG['types'][r['type']]
    c = read_list(os.path.join(D, tp['file']))[:, :3].astype(float)
    smp = (c[:, None, :] + offs[None]).reshape(-1, 3)
    q = (smp - np.array(r['pivot'], float)) * S
    if r['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    g = r['rotate'][2]; cc, ss = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    q = np.stack([q[:, 0] * cc - q[:, 1] * ss, q[:, 0] * ss + q[:, 1] * cc, q[:, 2]], 1) + np.array(r['at'], float)
    gunc[key] = set(map(tuple, np.floor(q).astype(int)))
cellgun = {}
for key, cs in gunc.items():
    for c in cs:
        cellgun.setdefault(c, set()).add(key)
names = {r['name'] for r in V['ropes']}
vs, cur, ids = [], None, {}
for line in open(os.path.join(E14, 'assembly.obj'), encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        cur = line.split('#', 1)[1].strip() if '#' in line else line[2:].strip()
    elif line.startswith('f ') and cur in names:
        ids.setdefault(cur, set()).update(int(t.split('/')[0]) - 1 for t in line.split()[1:])
vs = np.array(vs)[:, [0, 2, 1]]                         # obj 是 y 朝上（x, 作品 z, 作品 y）⇒ 換回作品座標
tot = 0; per = {}; noobj = 0
for r in V['ropes']:
    if r['name'] not in ids:
        noobj += 1; continue
    P = vs[sorted(ids[r['name']])] + off
    A, B = endpoint(r['from']) + off, endpoint(r['to']) + off
    far = (np.linalg.norm(P - A, axis=1) > 1.5) & (np.linalg.norm(P - B, axis=1) > 1.5)
    own = r['name'].split('.')[0] + '/' + r['name'].split('.')[1]
    h = 0
    for p in P[far]:
        k = tuple(np.floor(p).astype(int))
        if not (0 <= k[0] < NX and 0 <= k[1] < NY and 0 <= k[2] < NZ):
            continue
        if occ[k] or (cellgun.get(k, set()) - {own}):
            h += 1
    if h:
        per[r['name']] = h
    tot += h
print('④ 中段頂點落在實心或別門砲：合計 %d（obj 裡沒有的繩 %d）｜有的繩 %d 條：%s' % (tot, noobj, len(per), dict(list(per.items())[:12]) if per else '無'))
