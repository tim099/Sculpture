# 光榮號 階段八讀數（TASK-0613）—— 抄自三叉戟號 gura-tridente-01m/design/tools/check_stage8.py（gura）；改：mio、框 1200、反向對照往外推 3 格（單子要的）、量轉了角度的砲。
# 原檔說明：階段八讀數（TASK-0561）：① 墊木結果帳：甲板子作品現在 vs 標記 階段八墊木:begin ＋ 墊木清單 ② 遊戲讀的那一份（組裝件 export format=parts）：每門在不在、state、meta vs verify、
#   固定點 vs draft 算的 ③ 碰撞（獨立的尺）：每門的變換從引擎匯出的固定點反推（最小平方仿射，⛔ 不用 draft 的公式），把來源砲每一格（格心＋八角）搬上船，
#   對現讀的組裝件（links=all）＋ 其他模型外框（不含砲自己）＋ 已量過的砲 ④ 砲口在船殼外（引擎的 muzzle 點、那一排船殼最外面的外側）⑤ 輪子著地
#   ⑥ 反向對照：一門砲往外推 2 格 ⇒ 碰撞要報；把一門的 meta 改掉 ⇒ meta 不同 1
#   用法：python -I -X utf8 tools/check_stage8.py <design>
import json, math, os, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
sys.path.insert(0, design)
import mio as DB  # noqa: E402

WORKS = os.path.dirname(os.path.dirname(design))
V = json.load(open(os.path.join(design, 'verify_guns.json'), encoding='utf-8'))
NX, NY, NZ, YC = 1200, 400, 260, 200


def key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


def ledger(now, want):
    dn = dict(zip(key(now).tolist(), now[:, 3].tolist()))
    dw = dict(zip(key(want).tolist(), want[:, 3].tolist()))
    return len(set(dw) - set(dn)), len(set(dn) - set(dw)), sum(1 for k in set(dn) & set(dw) if dn[k] != dw[k])


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))


# ① 墊木
for hw, P in sorted(V['pads'].items()):
    pad = np.loadtxt(os.path.join(design, P['file']), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    B = DB.export_list(hw, 'none', ('mark=階段八墊木:begin',))
    N = DB.export_list(hw, 'none')
    E = np.concatenate([B, pad])
    print('① 墊木 %s：begin %d ＋ 墊木 %d ↔ 現在 %d，缺 %d、多 %d、色差 %d；墊木跟 begin 重疊 %d' % (
        (hw, len(B), len(pad), len(N)) + ledger(N, E) + (len(E) - len(np.unique(key(E))),)))

# ② 遊戲讀的那一份
PJ = parts()
by = {m['path']: m for m in PJ['models']}
rows = V['rows']
miss = notok = metad = 0
worst = 0.0
for r in rows:
    m = by.get('%s/%s' % (r['host_link'], r['model']))
    if m is None:
        miss += 1
        continue
    notok += m.get('state') != 'ok'
    metad += m.get('meta') != r['meta']
    for nm in ('muzzle', 'breech'):
        worst = max(worst, max(abs(m['points'][nm][i] - r[nm][i]) for i in range(3)))
print('② parts：砲 %d 門（verify %d），找不到 %d、state 不是 ok %d、meta 不同 %d；muzzle／breech 跟 draft 算的最大差 %.4f 格；全部模型 %d' % (
    sum(1 for p in by if (by[p].get('meta') or {}).get('kind') == 'gun'), len(rows), miss, notok, metad, worst, len(PJ['models'])))

# ③ 碰撞（獨立的尺）
A = DB.export_list(DB.ASM, 'all')
A = A[A[:, 2] < NZ]
occ = np.zeros((NX, NY, NZ), bool)
occ[A[:, 0], A[:, 1], A[:, 2]] = True
H = DB.export_list(DB.ASM, '船殼')
hull = np.zeros((NX, NY, NZ), bool)
H = H[H[:, 2] < NZ]
hull[H[:, 0], H[:, 1], H[:, 2]] = True
others = np.zeros_like(occ)
for m in PJ['models']:
    if (m.get('meta') or {}).get('kind') == 'gun':
        continue
    b = m['box']
    others[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
           max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
src = {}
offs = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
for k, T in V['types'].items():
    C = DB.export_list(T['work'], None)
    an = json.load(open(os.path.join(WORKS, T['work'], 'anchors.json'), encoding='utf-8'))['anchors']
    src[k] = {'samp': (C[:, :3].astype(float)[:, None, :] + offs[None]).reshape(-1, 3),
              'bot': np.array([[x + ox, y + oy, 0.5] for x, y, _ in C[C[:, 2] == 0][:, :3] for ox in (0.3, 0.7) for oy in (0.3, 0.7)]),   # z 取格心：最小平方解出的仿射把 z 0.0 算成 92.99999 ⇒ floor 會多掉一格（第一版報 124 門懸空，錯在尺）
              'an': {a['name']: a['at'] for a in an}}


def fit(r, m):
    """引擎的固定點（世界）↔ 來源作品的固定點（格心）⇒ 仿射 W ＝ L·M ＋ t；回 (M, t, 殘差最大)。"""
    an = src[r['type']]['an']
    names = sorted(n for n in an if n in m['points'])
    L = np.array([np.array(an[n], float) + 0.5 for n in names])
    W = np.array([m['points'][n] for n in names], float)
    X = np.hstack([L, np.ones((len(L), 1))])
    sol, *_ = np.linalg.lstsq(X, W, rcond=None)
    return sol[:3], sol[3], float(np.abs(X @ sol - W).max()), len(names)


def collide(Wp, grid_guns):
    i = np.floor(Wp).astype(int)
    ok = (i[:, 0] >= 0) & (i[:, 0] < NX) & (i[:, 1] >= 0) & (i[:, 1] < NY) & (i[:, 2] >= 0) & (i[:, 2] < NZ)
    h = np.ones(len(Wp), bool)
    h[ok] = occ[i[ok, 0], i[ok, 1], i[ok, 2]] | others[i[ok, 0], i[ok, 1], i[ok, 2]] | grid_guns[i[ok, 0], i[ok, 1], i[ok, 2]]
    return int(h.sum())


def outer_face(x, z, side):
    col = np.nonzero(hull[int(x), :, int(z)])[0]
    col = col[col > YC] if side > 0 else col[col < YC]
    return None if len(col) == 0 else (col.max() + 1 if side > 0 else col.min())


guns = np.zeros_like(occ)
tot_hit = bad_out = hang = fitres = 0.0
hit_list, out_list, hang_list = [], [], []
T_by = {}
for r in rows:
    m = by.get('%s/%s' % (r['host_link'], r['model']))
    if m is None:
        continue
    M, t, res, npts = fit(r, m)
    fitres = max(fitres, res)
    T_by[r['model'] + '@' + r['host_link']] = (M, t)
    s = src[r['type']]
    Wp = s['samp'] @ M + t
    h = collide(Wp, guns)
    if h:
        hit_list.append((r['model'] + '@' + r['host_link'], h))
    tot_hit += h
    i = np.floor(Wp).astype(int)
    guns[i[:, 0], i[:, 1], i[:, 2]] = True
    mu = np.array(m['points']['muzzle'])
    if 'Q' in r:                                                         # 船頭砲門（TASK-0578）：引擎的砲口點沿砲軸超過開門點 Q 多少
        sg = 1 if r['meta']['side'] == 'S' else -1
        th = math.radians(r['angle_deg'])
        out = float((mu - np.array(r['Q'])) @ np.array([math.cos(th), sg * math.sin(th), 0.0]))
    elif r['meta'].get('arc') == 'stern':
        row = np.nonzero(hull[:, int(mu[1]), r['port_z'][0] - 1])[0]
        out = float(row.min() - mu[0])
    elif r['meta'].get('deck') == 'battery':                           # 船頭砲台（TASK-0588）：砲管從船頭舷牆上面伸出去 ⇒ 砲口超過那一排（砲口的 y、砲台面那一層）船殼最前面那格多少
        row = np.nonzero(hull[:, int(mu[1]), int(r['at'][2]) - 1])[0]
        out = float(mu[0] - (row.max() + 1))
    else:
        side = 1 if r['meta']['side'] == 'S' else -1
        ob = outer_face(math.floor(mu[0]), r['port_z'][0] - 1, side)
        out = -99.0 if ob is None else float((mu[1] - ob) * side)
    if out < 0.5:
        out_list.append((r['model'] + '@' + r['host_link'], round(out, 2)))
    wb = np.floor(s['bot'] @ M + t).astype(int)
    hz = int((~occ[wb[:, 0], wb[:, 1], wb[:, 2] - 1]).sum())
    if hz:
        hang_list.append((r['model'] + '@' + r['host_link'], hz))
print('③ 碰撞（變換從引擎的固定點反推；仿射殘差最大 %.4f）：碰到實心／其他模型外框／別門砲的取樣點 合計 %d，有碰的 %d 門 %s' % (fitres, tot_hit, len(hit_list), hit_list[:6]))
print('④ 砲口在船殼外（≥ 0.5 格）：沒伸出去的 %d 門 %s' % (len(out_list), out_list[:6]))
print('⑤ 輪子著地（模型 z 0 那一層的取樣點正下方是實心）：懸空的 %d 門 %s' % (len(hang_list), hang_list[:6]))

# ⑥ 反向對照
r0 = next(r for r in rows if r['host_link'] == '甲板-lower' and r['model'] == '砲-S08')
M, t = T_by['砲-S08@甲板-lower']
g2 = guns.copy()
Wp = src[r0['type']]['samp'] @ M + t
i = np.floor(Wp).astype(int)
g2[i[:, 0], i[:, 1], i[:, 2]] = False                                      # 拿掉它自己再量
print('⑥ 反向對照：砲-S08@甲板-lower 原位 %d、往外（+y）推 3 格 ⇒ %d、往船頭推 2 格 ⇒ %d；meta 改 gun=xx ⇒ meta 不同 %d' % (
    collide(Wp, g2), collide(Wp + np.array([0, 3.0, 0]), g2), collide(Wp + np.array([2.0, 0, 0]), g2),
    sum(1 for r in rows if dict(r['meta'], **({'gun': 'xx'} if r is r0 else {})) != by['%s/%s' % (r['host_link'], r['model'])].get('meta'))))
wb0 = np.floor(src[r0['type']]['bot'] @ M + t).astype(int)
wb1 = np.floor(src[r0['type']]['bot'] @ M + t + np.array([0, 0, 1.0])).astype(int)
print('   輪子：砲-S08@甲板-lower 原位懸空取樣 %d／%d、抬高 1 格 ⇒ %d' % (
    int((~occ[wb0[:, 0], wb0[:, 1], wb0[:, 2] - 1]).sum()), len(wb0), int((~occ[wb1[:, 0], wb1[:, 1], wb1[:, 2] - 1]).sum())))
