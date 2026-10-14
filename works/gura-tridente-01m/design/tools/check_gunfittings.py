# TASK-0575 讀數（落格之後；只讀引擎的匯出，跟 verify_gunfittings.json 比）—— 四把尺照風暴角號 check_gunfittings.py（summit）：
#   ① 結果帳：每件砲具子作品 匯出 vs 清單；組裝件（links=all）＝ 藏 砲具 的組裝件 ＋ 環（清單搬到 frame_at）
#   ② 環的固定點：parts.json 裡 <甲板>/砲具 的 points（引擎換算過的世界座標）vs 我算的格心
#   ③ 繩：每條都在、state ok；兩端（引擎 sub=ropes 解出來的）vs 我算的；全部繩 broken 0
#   ④ 中段：引擎 obj 裡每條砲索的管子頂點（離兩端各 1.5 格以外），落在實心格或別門砲（不算自己這門）的有幾個
#   偏移 ＝ 反向對照：我這邊的預期整批平移，該報的要報（⚠ 要往下推：往上是往空氣推，④ 量不出來 —— summit 的教訓）
#   用法：python -I -X utf8 tools/check_gunfittings.py <design> [偏移 dx,dy,dz]
import json, math, os, re, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
off = np.array([float(v) for v in sys.argv[2].split(',')]) if len(sys.argv) > 2 else np.zeros(3)
sys.path.insert(0, D)
import deco_base as DB  # noqa: E402

WORKS = os.path.dirname(os.path.dirname(D))
V = json.load(open(os.path.join(D, 'verify_gunfittings.json'), encoding='utf-8'))
VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
NX, NY, Z0, Z1 = 1100, 400, 60, 200


def key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


def ledger(now, want):
    dn = dict(zip(key(now).tolist(), now[:, 3].tolist()))
    dw = dict(zip(key(want).tolist(), want[:, 3].tolist()))
    return len(set(dw) - set(dn)), len(set(dn) - set(dw)), sum(1 for k in set(dn) & set(dw) if dn[k] != dw[k])


def run(*a):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


tmp = tempfile.mkdtemp()
# ①
moved = []
for w in V['works']:
    L = np.loadtxt(os.path.join(D, w['file']), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    N = DB.export_list(w['work'], None)
    if not off.any():
        print('① %s：清單 %d ↔ 子作品 %d，缺 %d、多 %d、色差 %d' % ((w['work'], len(L), len(N)) + ledger(N, L)))
    W = L.copy()
    W[:, :3] += np.array(w['frame_at'], np.int32)
    moved.append(W)
hide = ','.join('%s/%s' % (w['deck'], w['link']) for w in V['works'])
B = DB.export_list(DB.ASM, 'all', ('hide_links=' + hide,))
NOW = DB.export_list(DB.ASM, 'all')
E = np.concatenate([B] + moved)
if not off.any():
    print('① 組裝件：藏砲具 %d ＋ 環 %d ↔ 現在 %d，缺 %d、多 %d、色差 %d；環跟原本重疊 %d' % (
        (len(B), sum(len(m) for m in moved), len(NOW)) + ledger(NOW, E) + (len(E) - len(np.unique(key(E))),)))

# ②
pj = os.path.join(tmp, 'p.json').replace('\\', '/')
run('op=export', 'format=parts', 'work=' + DB.ASM, 'out=' + pj)
PJ = json.load(open(pj, encoding='utf-8'))
eng = {}
for l in PJ['links']:
    if l['path'].endswith('/砲具'):
        for k, v in (l.get('points') or {}).items():
            eng[l['path'].split('/')[0] + '/' + k] = np.array(v, float)
worst, miss = 0.0, 0
for an in V['anchors']:
    e = eng.get(an['deck'] + '/' + an['name'])
    if e is None:
        miss += 1
        continue
    worst = max(worst, float(np.abs(e - (np.array(an['world'], float) + 0.5 + off)).max()))
print('② 環的固定點 %d：引擎缺 %d｜引擎 vs 我算的格心 最大差 %.4f' % (len(V['anchors']), miss, worst))

# ③（端點我這邊：砲的固定點照 verify_guns 的擺法、環照格心）
by = {m['path']: m for m in PJ['models']}


rows_g = {rr['host_link'] + '/' + rr['model']: rr for rr in VG['rows']}
tan = {t: {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, tp['work'], 'anchors.json'), encoding='utf-8'))['anchors']} for t, tp in VG['types'].items()}


def endpoint(s):
    if s.startswith('model:'):                                         # 砲的點：照 verify_guns 的擺法自己算（⛔ 不拿引擎的，不然是引擎對引擎）
        d, m, k = s[len('model:'):].split('/')
        rr = rows_g[d + '/' + m]
        q = (np.array(tan[rr['type']][k], float) + 0.5 - np.array(rr['pivot'], float)) * rr['scale']
        if rr['mirror'] == 'y':
            q[1] = -q[1]
        g = math.radians(rr['rotate'][2])
        c, sn = round(math.cos(g), 12), round(math.sin(g), 12)
        return np.array([q[0] * c - q[1] * sn, q[0] * sn + q[1] * c, q[2]]) + np.array(rr['at'], float)
    d, _, nm = s.split('/')
    an = next(a for a in V['anchors'] if a['deck'] == d and a['name'] == nm)
    return np.array(an['world'], float) + 0.5


out = run('op=work', 'sub=ropes', 'work=' + DB.ASM)
txt = out.stdout
m = re.search(r'📄 回傳檔：(\S+)', txt)
if m and os.path.exists(m.group(1)):
    txt = open(m.group(1), encoding='utf-8').read()
pat = re.compile(r'^- ([✓✗]) `([^`]+)`［(\w+)］ (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\) → (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\)')
R = {}
for line in txt.splitlines():
    mm = pat.match(line.strip())
    if mm:
        g = mm.groups()
        R[g[1]] = {'state': g[2], 'a': np.array([float(v) for v in g[4:7]]), 'b': np.array([float(v) for v in g[8:11]])}
worst, missing, bad = 0.0, 0, 0
for r in V['ropes']:
    e = R.get(r['name'])
    if e is None:
        missing += 1
        continue
    bad += e['state'] != 'ok'
    for k, s in (('a', r['from']), ('b', r['to'])):
        worst = max(worst, float(np.abs(e[k] - (endpoint(s) + off)).max()))
nb = re.search(r'🔢 ropes_broken = (\d+)', out.stdout)
print('③ 砲索 %d 條：缺 %d、非 ok %d｜兩端 引擎 vs 我算的 最大差 %.3f｜sub=ropes 解析到 %d 條、ropes_broken %s' % (
    len(V['ropes']), missing, bad, worst, len(R), nb.group(1) if nb else '?'))

# ④ obj：只匯砲索那一組繩（region 切到幾乎沒有格子、不畫模型與帆）
oj = os.path.join(tmp, 'g.obj').replace('\\', '/')
r = run('op=export', 'format=obj', 'work=' + DB.ASM, 'out=' + oj, 'region=0..1,0..1,0..1', 'models=0', 'sails=0', 'rope_groups=guns')
if r.returncode != 0:
    raise SystemExit('obj 匯出失敗：' + (r.stdout + r.stderr)[-600:])
occ = np.zeros((NX, NY, Z1 - Z0), bool)
A = NOW[(NOW[:, 2] >= Z0) & (NOW[:, 2] < Z1)]
occ[A[:, 0], A[:, 1], A[:, 2] - Z0] = True
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
gid = np.zeros((NX, NY, Z1 - Z0), np.int16)
idx = {}
tc = {}
for i, rr in enumerate(VG['rows']):
    if rr['type'] not in tc:
        c = DB.export_list(VG['types'][rr['type']]['work'], None)[:, :3].astype(float)
        tc[rr['type']] = (c[:, None, :] + OFFS[None]).reshape(-1, 3)
    q = (tc[rr['type']] - np.array(rr['pivot'], float)) * rr['scale']
    if rr['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    g = rr['rotate'][2]
    cc, ss = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    q = np.stack([q[:, 0] * cc - q[:, 1] * ss, q[:, 0] * ss + q[:, 1] * cc, q[:, 2]], 1) + np.array(rr['at'], float)
    w = np.floor(q).astype(int)
    gid[w[:, 0], w[:, 1], w[:, 2] - Z0] = i + 1
    idx[rr['host_link'] + '/' + rr['model']] = i + 1
names = {r['name'] for r in V['ropes']}
vs, cur, ids = [], None, {}
for line in open(oj, encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        cur = line.split('#', 1)[1].strip() if '#' in line else line[2:].strip()
    elif line.startswith('f ') and cur in names:
        ids.setdefault(cur, set()).update(int(t.split('/')[0]) - 1 for t in line.split()[1:])
vs = np.array(vs)[:, [0, 2, 1]]                                       # obj 是 y 朝上 ⇒ 換回作品座標
tot, per, noobj = 0, {}, 0
for r in V['ropes']:
    if r['name'] not in ids:
        noobj += 1
        continue
    P = vs[sorted(ids[r['name']])] + off
    A_, B_ = endpoint(r['from']) + off, endpoint(r['to']) + off
    far = (np.linalg.norm(P - A_, axis=1) > 1.5) & (np.linalg.norm(P - B_, axis=1) > 1.5)
    own = idx[r['name'].split('.')[0] + '/' + r['name'].split('.')[1]]
    k = np.floor(P[far]).astype(int)
    ok = (k[:, 2] >= Z0) & (k[:, 2] < Z1)
    k = k[ok]
    g = gid[k[:, 0], k[:, 1], k[:, 2] - Z0]
    h = int((occ[k[:, 0], k[:, 1], k[:, 2] - Z0] | ((g != 0) & (g != own))).sum())
    if h:
        per[r['name']] = h
    tot += h
print('④ obj 中段頂點落在實心或別門砲：合計 %d（obj 裡沒有的繩 %d、obj 頂點 %d）｜有的繩 %d 條：%s' % (
    tot, noobj, len(vs), len(per), dict(list(per.items())[:8]) if per else '無'))
