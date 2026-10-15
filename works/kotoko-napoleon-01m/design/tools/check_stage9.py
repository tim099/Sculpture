# 拿破崙號 階段九讀數（TASK-0614）—— 抄自三叉戟號 gura-tridente-01m/design/tools/check_stage9.py（gura）；改：mio、框 1200、加 ⑦ 舵、⑧ 拿掉一個 kind 的反向對照。
# 原檔說明：階段九讀數（TASK-0562）：① 彈藥庫子作品結果帳（匯出 vs 清單）② 組裝件結果帳：現在（links=all）vs 藏掉 彈藥庫-前／後 ＋ 兩間清單搬到 at
#   ③ 遊戲讀的那一份（export format=parts）：彈藥庫關聯 meta（kind、pos、powder_lb ＝ 桶數 × 100）與 blast／door 點、火藥桶 kind=powder 數、
#      甲板零件 meta 與外框 vs draft 算的 ④ 零件外框裡的實心格（格心落在外框內；外框比模型大 ⇒ 這是比較嚴的尺）⑤ 引擎：models／ropes broken、結構
#   ⑥ 反向對照：真的拿掉 彈藥庫-前 的 pos ⇒ parts 少那一欄；再加回
#   用法：python -I -X utf8 tools/check_stage9.py <design>
import json, math, os, re, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
sys.path.insert(0, design)
import mio as DB  # noqa: E402

PL = json.load(open(os.path.join(design, 'magazines_placement.json'), encoding='utf-8'))
VF = json.load(open(os.path.join(design, 'verify_fittings.json'), encoding='utf-8'))


def key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


def ledger(now, want):
    dn = dict(zip(key(now).tolist(), now[:, 3].tolist()))
    dw = dict(zip(key(want).tolist(), want[:, 3].tolist()))
    return len(set(dw) - set(dn)), len(set(dn) - set(dw)), sum(1 for k in set(dn) & set(dw) if dn[k] != dw[k])


def read(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def cli(*a):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = cli('op=export', 'format=parts', 'work=' + DB.ASM, 'out=' + out)
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))


# ① ②
moved = []
for k, R in sorted(PL['rooms'].items()):
    L = read(os.path.join(design, 'masks', 'magazines', k + '.vox.txt'))
    N = DB.export_list(R['work'], None)
    print('① %s 結果帳：清單 %d ↔ 子作品 %d，缺 %d、多 %d、色差 %d' % ((R['work'], len(L), len(N)) + ledger(N, L)))
    W = L.copy()
    W[:, :3] += np.array(R['at'], np.int32)
    moved.append(W)
links = ','.join(R['link'] for R in PL['rooms'].values())
B = DB.export_list(DB.ASM, 'all', ('hide_links=' + links,))   # ⚠ 舵是模型、不是關聯 ⇒ 不在格子裡
NOW = DB.export_list(DB.ASM, 'all')
E = np.concatenate([B] + moved)
print('② 組裝件結果帳：藏彈藥庫 %d ＋ 兩間 %s ↔ 現在 %d，缺 %d、多 %d、色差 %d；設計那一份自己重疊 %d' % (
    (len(B), [len(m) for m in moved], len(NOW)) + ledger(NOW, E) + (len(E) - len(np.unique(key(E))),)))

# ③
P = parts()
lk = {l['path']: l for l in P['links']}
for k, R in sorted(PL['rooms'].items()):
    l = lk.get(R['link'], {})
    pts = l.get('points', {})
    want_b = [R['at'][i] + R['anchors']['blast'][i] + 0.5 for i in range(3)]
    print('③ %s：meta %s（桶 %d ⇒ 要 %d）、blast %s（要 %s）、door %s' % (R['link'], l.get('meta'), len(R['barrels']), len(R['barrels']) * 100,
                                                                pts.get('blast'), want_b, pts.get('door')))
by = {m['path']: m for m in P['models']}
kegs = [m for m in P['models'] if (m.get('meta') or {}).get('kind') == 'powder']
print('   火藥桶 kind=powder：%d（plan %d），state 不是 ok %d' % (len(kegs), sum(len(R['barrels']) for R in PL['rooms'].values()), sum(m.get('state') != 'ok' for m in kegs)))
worst, metad, miss = 0.0, 0, 0
for r in VF['rows']:
    m = by.get('甲板-spar/' + r['model'])
    if m is None:
        miss += 1
        continue
    metad += m.get('meta') != r['meta']
    worst = max(worst, max(abs(m['box'][i] - r['box'][i]) for i in range(6)))
print('   甲板零件 %d：找不到 %d、meta 不同 %d、外框跟 draft 算的最大差 %.3f' % (len(VF['rows']), miss, metad, worst))

# ④
occ = np.zeros((1200, 400, 260), bool)
A = NOW[NOW[:, 2] < 260]
occ[A[:, 0], A[:, 1], A[:, 2]] = True
for r in VF['rows']:
    m = by.get('甲板-spar/' + r['model'])
    b = m['box']
    xs = [x for x in range(int(math.floor(b[0])), int(math.ceil(b[3]))) if b[0] <= x + 0.5 <= b[3]]
    ys = [y for y in range(int(math.floor(b[1])), int(math.ceil(b[4]))) if b[1] <= y + 0.5 <= b[4]]
    zs = [z for z in range(int(math.floor(b[2])), int(math.ceil(b[5]))) if b[2] <= z + 0.5 <= b[5]]
    sub = occ[xs[0]:xs[-1] + 1, ys[0]:ys[-1] + 1, zs[0]:zs[-1] + 1]
    n = int(sub.sum())
    where = ''
    if n:
        ii = np.argwhere(sub)
        where = '（z %d..%d、色 %s）' % (zs[0] + ii[:, 2].min(), zs[0] + ii[:, 2].max(),
                                     sorted(set(int(c) for c in A[(A[:, 0] >= xs[0]) & (A[:, 0] <= xs[-1]) & (A[:, 1] >= ys[0]) & (A[:, 1] <= ys[-1]) &
                                                                    (A[:, 2] >= zs[0]) & (A[:, 2] <= zs[-1])][:, 3].tolist())))
    print('④ %s 外框裡的實心格 %d%s；腳下（draft）%s' % (r['model'], n, where, r['support']))

# ⑤
st = {k: v for k, v in re.findall(r'🔢 (\w+) = (\S+)', cli('op=stats', 'work=' + DB.ASM, 'structure=1').stdout)}
mo = {k: v for k, v in re.findall(r'🔢 (\w+) = (\S+)', cli('op=work', 'sub=models', 'work=' + DB.ASM).stdout)}
ro = {k: v for k, v in re.findall(r'🔢 (\w+) = (\S+)', cli('op=work', 'sub=ropes', 'work=' + DB.ASM).stdout)}
print('⑤ 引擎：格 %s、元件 %s、空腔 %s、link_overlap %s；模型 %s broken %s；繩 %s broken %s' % (
    st.get('total_voxels'), st.get('components'), st.get('cavities'), st.get('link_overlap'), mo.get('model_count'), mo.get('models_broken'),
    ro.get('rope_count'), ro.get('ropes_broken')))

# ⑥ 反向對照（真的改，再改回）
R = PL['rooms']['fore']
before = lk[R['link']]['meta']
cli('op=work', 'sub=meta', 'persona=kotoko', 'work=' + DB.ASM, 'part=link', 'name=' + R['link'], 'meta={"pos":null}')
m1 = {l['path']: l for l in parts()['links']}[R['link']].get('meta')
cli('op=work', 'sub=meta', 'persona=kotoko', 'work=' + DB.ASM, 'part=link', 'name=' + R['link'], 'meta=' + json.dumps({'pos': before['pos']}))
m2 = {l['path']: l for l in parts()['links']}[R['link']].get('meta')
print('⑥ 反向對照：拿掉 %s 的 pos ⇒ parts meta %s（少 %d 欄）；加回 ⇒ %s（跟原本相同 %s）' % (R['link'], m1, len(before) - len(m1 or {}), m2, m2 == before))

# ④b 格子級碰撞：位置從引擎的外框反推（box 最小角 ＝ at ＋ s·(格子最小角 − pivot)；mirror=y 那一軸取最大角翻過來），把來源每一格（格心＋八角）搬過去量
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
occ2 = occ.copy()
for m in P['models']:
    if m['path'].startswith('甲板-spar/') and m['path'].split('/', 1)[1] in [r['model'] for r in VF['rows']]:
        continue
    b = m['box']
    occ2[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
         max(0, int(math.floor(b[2]))):min(260, int(math.ceil(b[5])))] = True
for r in VF['rows']:
    m = by['甲板-spar/' + r['model']]
    C = DB.export_list(r['work'], None)
    s, piv = r['scale'], np.array(r['pivot'], float)
    lo, hi = C[:, :3].min(0).astype(float), C[:, :3].max(0).astype(float) + 1
    at = np.array(m['box'][:3], float) - s * (lo - piv)
    if r['mirror'] == 'y':
        at[1] = m['box'][1] + s * (hi[1] - piv[1])
    q = ((C[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3) - piv) * s
    if r['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    i = np.floor(q + at).astype(int)
    hit = int(occ2[i[:, 0], i[:, 1], i[:, 2]].sum())
    print('④b %s 位置（從引擎外框反推）%s vs draft %s；碰到實心／其他模型外框的取樣點 %d' % (r['model'], [round(v, 3) for v in at.tolist()], r['at'], hit))

# ⑦ 舵（本船加的）：子作品結果帳、parts 的模型 meta、stock-top 與鉸鏈、轉 ±max_deg 時舵的每一格（格心）落在船的實心裡幾格
PR = json.load(open(os.path.join(design, 'rudder_placement.json'), encoding='utf-8'))
RL = read(os.path.join(design, 'masks', 'rudder', 'rudder.vox.txt'))
RN = DB.export_list(PR['work'], None)
print('⑦ 舵 結果帳：清單 %d ↔ 子作品 %d，缺 %d、多 %d、色差 %d' % ((len(RL), len(RN)) + ledger(RN, RL)))
mr = by.get(PR['model'])
st_w = [PR['anchors']['stock-top'][i] + 0.5 for i in range(3)]
print('   parts：%s state %s、meta 跟 draft 相同 %s、stock-top %s（要 %s）' % (PR['model'], mr and mr.get('state'), mr and mr.get('meta') == PR['meta'],
                                                                 mr and mr.get('points', {}).get('stock-top'), st_w))
h = np.array([PR['meta']['hinge_x'], PR['meta']['hinge_y'], PR['meta']['hinge_z']])
ax = np.array([PR['meta']['axis_x'], PR['meta']['axis_y'], PR['meta']['axis_z']])
ax = ax / np.linalg.norm(ax)
Q = RL[:, :3].astype(float) + 0.5 - h


def rot(v, k, deg):
    t = math.radians(deg)
    return v * math.cos(t) + np.cross(k, v) * math.sin(t) + np.outer(v @ k, k) * (1 - math.cos(t))


for deg in (-PR['meta']['max_deg'], -15, 0, 15, PR['meta']['max_deg']):
    W = rot(Q, ax, deg) + h
    i = np.floor(W).astype(int)
    print('   轉 %+d°：舵的格心落在船（組裝件 links=all）實心裡 %d 格' % (deg, int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())))

# ⑧ 反向對照（單子要的）：真的拿掉羅經櫃的 kind ⇒ 讀數要報那一件；再加回
def fit_meta_diff():
    pm = {m['path']: m for m in parts()['models']}
    return [r['model'] for r in VF['rows'] if pm.get('甲板-spar/' + r['model'], {}).get('meta') != r['meta']]


cli('op=work', 'sub=meta', 'persona=kotoko', 'work=kotoko-napoleon-01m-deck-spar', 'part=model', 'name=羅經櫃', 'meta={"kind":null}')
d1 = fit_meta_diff()
cli('op=work', 'sub=meta', 'persona=kotoko', 'work=kotoko-napoleon-01m-deck-spar', 'part=model', 'name=羅經櫃', 'meta={"kind":"binnacle"}')
d2 = fit_meta_diff()
print('⑧ 反向對照：拿掉 羅經櫃 的 kind ⇒ meta 不同 %s；加回 ⇒ %s' % (d1, d2))

# ⑨ 錨（本船加的）：parts 裡的兩隻錨（state、meta、ring 等固定點 vs draft_anchors 算的）、船殼的 hawse-S／P、錨每一格（格心＋八角）碰到實心／其他模型外框
VA = json.load(open(os.path.join(design, 'verify_anchors.json'), encoding='utf-8'))
P9 = parts()
pm = {m['path']: m for m in P9['models']}
hull_pts = next((l.get('points') or {} for l in P9['links'] if l['path'] == '船殼'), {})
for r in VA['rows']:
    m = pm.get(r['model'])
    dd = max(abs(m['points'][k][i] - VA['points'][r['model']][k][i]) for k in VA['points'][r['model']] for i in range(3)) if m else None
    print('⑨ %s：state %s、meta 相同 %s、固定點跟 draft 最大差 %s' % (r['model'], m and m.get('state'), m and m.get('meta') == VA['meta'], dd))
for k, v in sorted(VA['hawse'].items()):
    print('   船殼 %s：parts %s（要 %s）' % (k, hull_pts.get(k), [c + 0.5 for c in v]))
CA = DB.export_list(VA['work'], None)
sampA = (CA[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
occ3 = occ.copy()
for m in P9['models']:
    if m['path'].startswith('錨-'):
        continue
    b = m['box']
    occ3[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
         max(0, int(math.floor(b[2]))):min(260, int(math.ceil(b[5])))] = True
for r in VA['rows']:
    q = (sampA - np.array(VA['pivot'], float)) * VA['scale']
    if r['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    t = math.radians(r['rotate'][2])
    W = np.stack([q[:, 0] * math.cos(t) - q[:, 1] * math.sin(t), q[:, 0] * math.sin(t) + q[:, 1] * math.cos(t), q[:, 2]], 1) + np.array(r['at'])
    i = np.floor(W).astype(int)
    print('   %s 碰到實心／其他模型外框的取樣點 %d；往船裡推 3 格 ⇒ %d' % (r['model'], int(occ3[i[:, 0], i[:, 1], i[:, 2]].sum()),
          int(occ3[i[:, 0], i[:, 1] + (-3 if r['mirror'] == 'none' else 3), i[:, 2]].sum())))
