# 直接出處：gura-pinas-01m/design/tools/check_stage8.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成康塞普西翁號（TASK-0969）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/tools/check_stage8.py（收穫號，照抄後改成康塞普西翁號 —— TASK-0969）
# 階段八（TASK-0597）讀數：砲 —— 一律從作品讀（models.json ＝ CLI 寫進去的那一份、CLI `work sub=models` 的狀態與外框、組裝件匯出）
#   ① 每門砲的 at／pivot／rotate／scale／mirror ＝ 設計（guns_placement.json）
#   ② 外框：照 models.json 用 gunsim 的變換算 vs CLI 印的外框（公式寫錯會在這裡現形；容差 0.06 ＝ CLI 印到 0.1）
#   ③ 碰撞：模型每一格的格心＋八個角（inset 0.2）落在組裝件實心格裡的樣本數，逐門
#   ④ 砲口：砲口那一點是空的，而且沿砲身方向再往外 20 格內沒有船殼（＝ 砲口已經在船殼外；不經過設計那一側的 outer）
#   ⑤ meta：kind=gun、gun 在遊戲的砲種表（Blockside/src/config/game.json guns 的 code）、來源有 muzzle／breech
#   用法：python -I -X utf8 tools/check_stage8.py <design> [--push=<砲名>:<格>]（反向對照：那一門照作品讀完之後往外推幾格再量）
import json, os, re, subprocess, sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
push = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--push=')), None)
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list
from gunsim import Grid, Gun, inset_offsets
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
VALHALLA = os.path.dirname(os.path.dirname(WORKS))
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
GB = plan['guns_build']
PL = {r['name']: r for r in json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']}
CODES = {g['code'] for g in json.load(open(os.path.join(VALHALLA, 'Blockside', 'src', 'config', 'game.json'), encoding='utf-8'))['guns'].values()}

models = {}
cli_box, cli_ok = {}, {}
for dk, w in GB['deck_works'].items():
    for m in json.load(open(os.path.join(WORKS, w, 'models.json'), encoding='utf-8'))['models']:
        if (m.get('meta') or {}).get('kind') == 'gun':
            models[m['name']] = dict(m, host=w)
    out = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=models', '--arg', 'work=' + w], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
    for l in out.splitlines():
        mm = re.match(r'- (\S) `([^`]+)`［(\w+)］.*外框 \(([-\d.,]+)\)–\(([-\d.,]+)\)', l)
        if mm:
            cli_ok[mm.group(2)] = mm.group(3)
            cli_box[mm.group(2)] = (np.array(mm.group(4).split(','), float), np.array(mm.group(5).split(','), float))
print('砲模型（從作品讀）%d、設計 %d；CLI 狀態 ok %d／其他 %d' % (len(models), len(PL), sum(1 for n in models if cli_ok.get(n) == 'ok'), sum(1 for n in models if cli_ok.get(n) != 'ok')))
print('  設計有、作品沒有：%s；作品有、設計沒有：%s' % (sorted(set(PL) - set(models)), sorted(set(models) - set(PL))))

# ① 參數 ＝ 設計
diff = []
for n, m in models.items():
    r = PL.get(n)
    if not r:
        continue
    t = GB['types'][r['type']]
    want = {'at': r['at'], 'pivot': t['pivot'], 'rotate': [0, 0, r['phi']], 'scale': [t['scale']] * 3, 'mirror': 'y' if r['side'] == 'P' else '', 'work': t['work']}
    for k, v in want.items():
        got = m[k]
        if (isinstance(v, list) and not np.allclose(np.array(got, float), np.array(v, float), atol=1e-6)) or (not isinstance(v, list) and got != v):
            diff.append((n, k, got, v))
print('① 參數 ≠ 設計：%d %s' % (len(diff), diff[:4]))

# 來源砲（格子＋固定點）
src = {}
for n, m in models.items():
    w = m['work']
    if w not in src:
        A = json.load(open(os.path.join(WORKS, w, 'anchors.json'), encoding='utf-8'))['anchors']
        src[w] = (export_list(w, None), {a['name']: a['at'] for a in A})


def gun_of(m):
    cells, anchors = src[m['work']]
    return Gun('-', {'work': m['work'], 'scale': m['scale'][0], 'pivot': m['pivot'], 'meta': m['meta']}, cells, anchors, GB['search']['inset'])


# ② 外框
dev = []
for n, m in models.items():
    g = gun_of(m)
    lo, hi = g.bbox(m['at'], m['rotate'][2], m['mirror'] == 'y')
    if n in cli_box:
        d = max(np.abs(lo - cli_box[n][0]).max(), np.abs(hi - cli_box[n][1]).max())
        dev.append((round(float(d), 3), n))
dev.sort(reverse=True)
print('② 外框（gunsim vs CLI）最大差 %s（%d 門比過）' % (dev[0] if dev else None, len(dev)))
print('   前五：', dev[:5], '｜不轉的（φ 是 0 或 ±90 的倍數）最大：', max((d for d in dev if abs(models[d[1]]['rotate'][2]) % 90 == 0), default=None))

# ③④ 碰撞與砲口
A = export_list(GB['assembly'], None, links=None)
G = Grid(A)
H = Grid(export_list(GB['hull'], None), outside=False)
coll, mz, mz_beyond = {}, [], {}
pushed = None
if push:
    pushed, dpush = push.rsplit(':', 1)
    dpush = float(dpush)
for n, m in sorted(models.items()):
    g = gun_of(m)
    at = np.array(m['at'], float)
    mir = m['mirror'] == 'y'
    d = g.direction(m['rotate'][2], mir)
    if n == pushed:
        at[:2] += d * dpush
    k = int(G.hit(g.world(g.samples, at, m['rotate'][2], mir)).sum())
    if k:
        coll[n] = k
    tip = g.world(g.anchors['muzzle'][None], at, m['rotate'][2], mir)[0]
    # 砲門是洞 ⇒ 砲口那條線上量不到牆（v1 只量砲口往外那條線：往裡拉 8 格照樣報 0）；改量砲門兩側：砲口左右各偏 6 格的線上，沿砲身方向最外面那格船殼在哪
    perp = np.array([-d[1], d[0]])
    face = -1e9
    for s in (-8.0, -7.0, -6.0, 6.0, 7.0, 8.0):        # 康塞普西翁號：鏡板上砲門與窗挨得近，只量 ±6 會兩條都落在開口裡（左舷鏡過來差半格）⇒ 多掃幾條
        ts = np.arange(-20.0, 20.5, 0.5)
        P = np.array([[tip[0] + perp[0] * s + d[0] * t, tip[1] + perp[1] * s + d[1] * t, tip[2]] for t in ts])
        hit = H.hit(P)
        if hit.any():
            face = max(face, float(ts[hit].max()) + 0.5)
    if face == -1e9:                                   # 一條線都沒碰到船殼 ＝ 量不到（v1 當成伸出 10 億、算過關 ⇒ 瞎的尺）
        mz.append((n, bool(G.hit(tip[None])[0]), '量不到'))
        continue
    beyond = -face
    mz_beyond[n] = round(beyond, 2)
    if G.hit(tip[None])[0] or beyond <= 0:
        mz.append((n, bool(G.hit(tip[None])[0]), round(beyond, 2)))
print('③ 碰撞（樣本落在組裝件實心裡）：%d 門 %s' % (len(coll), coll))
print('④ 砲口不在船殼外（砲口實心、或沒超過砲門兩側的船殼面）：%d 門 %s；伸出 min %s／max %s' % (
    len(mz), mz[:6], min(mz_beyond.items(), key=lambda kv: kv[1]), max(mz_beyond.items(), key=lambda kv: kv[1])))

# ⑤ meta
bad = []
for n, m in models.items():
    me = m.get('meta') or {}
    a = src[m['work']][1]
    if me.get('kind') != 'gun' or me.get('gun') not in CODES or 'muzzle' not in a or 'breech' not in a:
        bad.append((n, me.get('gun')))
by = {}
for m in models.values():
    by[m['meta']['gun']] = by.get(m['meta']['gun'], 0) + 1
print('⑤ meta 不合：%d %s；砲種 %s' % (len(bad), bad[:4], dict(sorted(by.items()))))
