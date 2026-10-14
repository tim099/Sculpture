# TASK-0578 讀數：① 船殼：現在 ＝ 標記 船頭砲門:begin − 刻除清單；刻掉那幾格刻之前的顏色 ＝ 清單 ② 墊木：甲板子作品 現在 ＝ 船頭砲墊木:begin ＋ 清單
#   ③ 三叉戟砲（parts，遊戲讀的那一份）：6 門在、state ok、meta 對、muzzle／breech vs draft ④ 火線：引擎的三個砲口點沿砲軸（引擎 muzzle − breech）往前 fire_clear 格，
#      落在實心的取樣點 ⑤ 碰撞：變換從引擎固定點反推，三叉戟砲每格（格心＋八角）落在實心或別門砲 ⑥ 反向對照：一門往前推 2 格 ⇒ ⑤ 要報；清單少一格 ⇒ ① 要報
#   用法：python -I -X utf8 tools/check_bowchase.py <design>
import json, math, os, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import deco_base as DB  # noqa: E402

WORKS = os.path.dirname(os.path.dirname(D))
V = json.load(open(os.path.join(D, 'verify_bowchase.json'), encoding='utf-8'))
VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))


def key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


def ledger(now, want):
    dn = dict(zip(key(now).tolist(), now[:, 3].tolist()))
    dw = dict(zip(key(want).tolist(), want[:, 3].tolist()))
    return len(set(dw) - set(dn)), len(set(dn) - set(dw)), sum(1 for k in set(dn) & set(dw) if dn[k] != dw[k])


def read(f):
    return np.loadtxt(os.path.join(D, f), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


# ①
Cv = read(V['carve']['file'])
H0 = DB.export_list('gura-tridente-01m', 'none', ('mark=船頭砲門:begin',))
H1 = DB.export_list('gura-tridente-01m', 'none')
keep = ~np.isin(key(H0), key(Cv))
d0 = dict(zip(key(H0).tolist(), H0[:, 3].tolist()))
colok = sum(1 for k, c in zip(key(Cv).tolist(), Cv[:, 3].tolist()) if d0.get(k) == c)
print('① 船殼：begin %d − 刻 %d ↔ 現在 %d，缺 %d、多 %d、色差 %d；刻之前的顏色對得上 %d／%d' % ((len(H0), len(Cv), len(H1)) + ledger(H1, H0[keep]) + (colok, len(Cv))))
Cm = Cv[1:]
k2 = ~np.isin(key(H0), key(Cm))
print('   反向對照：清單少一格 ⇒ 缺 %d、多 %d' % ledger(H1, H0[k2])[:2])
# ②
for w, P in sorted(V['pads'].items()):
    pad = read(P['file'])
    B = DB.export_list(w, 'none', ('mark=船頭砲墊木:begin',))
    N = DB.export_list(w, 'none')
    print('② 墊木 %s：begin %d ＋ %d ↔ 現在 %d，缺 %d、多 %d、色差 %d' % ((w, len(B), len(pad), len(N)) + ledger(N, np.concatenate([B, pad]))))
# ③
with tempfile.TemporaryDirectory() as d:
    pj = os.path.join(d, 'p.json').replace(os.sep, '/')
    subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + pj], capture_output=True)
    PJ = json.load(open(pj, encoding='utf-8'))
by = {m['path']: m for m in PJ['models']}
worst, metad, miss, notok = 0.0, 0, 0, 0
for r in V['trident'] + V['redo_broadside']:
    m = by.get(r['host_link'] + '/' + r['model'])
    if m is None:
        miss += 1
        continue
    notok += m.get('state') != 'ok'
    metad += m.get('meta') != r['meta']
    for nm in ('muzzle', 'breech'):
        worst = max(worst, max(abs(m['points'][nm][i] - r[nm][i]) for i in range(3)))
print('③ 三叉戟砲 6 ＋ 換回的 2：找不到 %d、state 不是 ok %d、meta 不同 %d；muzzle／breech 跟 draft 最大差 %.4f' % (miss, notok, metad, worst))
# ④ ⑤
A = DB.export_list(DB.ASM, 'all')
A = A[A[:, 2] < 260]
occ = np.zeros((1100, 400, 260), bool)
occ[A[:, 0], A[:, 1], A[:, 2]] = True
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
src, fits, gcell = {}, {}, {}
for r in VG['rows']:
    t = r['type']
    if t not in src:
        C = DB.export_list(r['work'], None)
        an = {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, r['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
        src[t] = ((C[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3), an)
    samp, an = src[t]
    m = by[r['host_link'] + '/' + r['model']]
    names = sorted(n for n in an if n in m['points'])
    X = np.hstack([np.array([np.array(an[n], float) + 0.5 for n in names]), np.ones((len(names), 1))])
    sol, *_ = np.linalg.lstsq(X, np.array([m['points'][n] for n in names], float), rcond=None)
    fits[(r['host_link'], r['model'])] = sol
    gcell[(r['host_link'], r['model'])] = np.floor(samp @ sol[:3] + sol[3]).astype(int)
gun_any = np.zeros_like(occ, dtype=np.int16)
for i, (k, w) in enumerate(gcell.items()):
    gun_any[w[:, 0], w[:, 1], w[:, 2]] = i + 1
idx = {k: i + 1 for i, k in enumerate(gcell)}
fc = plan['bowchase']['fire_clear']
fire_tot, hit_tot = 0, 0
for r in V['trident']:
    k = (r['host_link'], r['model'])
    m = by[r['host_link'] + '/' + r['model']]
    ax = np.array(m['points']['muzzle']) - np.array(m['points']['breech'])
    ax /= np.linalg.norm(ax)
    f_ = 0
    for nm in ('muzzle-a', 'muzzle-b', 'muzzle-c'):
        for s in np.arange(1.0, fc, 0.5):
            p = np.floor(np.array(m['points'][nm]) + ax * s).astype(int)
            f_ += bool(occ[tuple(p)]) or (gun_any[tuple(p)] not in (0, idx[k]))
    fire_tot += f_
    w = gcell[k]
    g = gun_any[w[:, 0], w[:, 1], w[:, 2]]
    hit_tot += int((occ[w[:, 0], w[:, 1], w[:, 2]] | ((g != 0) & (g != idx[k]))).sum())
print('④ 火線：三個砲口沿砲軸往前 %d 格落在實心或別門砲的取樣點 合計 %d（6 門）' % (fc, fire_tot))
print('⑤ 碰撞：三叉戟砲的格落在實心或別門砲 合計 %d' % hit_tot)
r0 = V['trident'][2]
k0 = (r0['host_link'], r0['model'])
m0 = by[r0['host_link'] + '/' + r0['model']]
ax = np.array(m0['points']['muzzle']) - np.array(m0['points']['breech'])
ax /= np.linalg.norm(ax)
samp, _ = src['trident']
w2 = np.floor(samp @ fits[k0][:3] + fits[k0][3] + ax * 2).astype(int)
g2 = gun_any[w2[:, 0], w2[:, 1], w2[:, 2]]
print('⑥ 反向對照：%s 往前推 2 格 ⇒ 碰撞 %d' % (r0['host_link'] + '/' + r0['model'], int((occ[w2[:, 0], w2[:, 1], w2[:, 2]] | ((g2 != 0) & (g2 != idx[k0]))).sum())))
