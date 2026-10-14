# TASK-0576 讀數：① 三件子作品 匯出 vs 清單；組裝件（links=all）＝ 藏本階段關聯 ＋ 清單 ② 不碰砲：每門砲的變換從引擎匯出的固定點反推（最小平方仿射），
#   把來源砲每一格（格心＋八角）搬上船，跟桿的格比 ③ 不浮空：每支桿（頭以外那一排）正上方一格是組裝件的實心 ④ 反向對照：清單整批 y ＋1 ⇒ ① 要報、③ 要報
#   用法：python -I -X utf8 tools/check_implements.py <design>
import json, os, re, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import deco_base as DB  # noqa: E402

WORKS = os.path.dirname(os.path.dirname(D))
V = json.load(open(os.path.join(D, 'verify_implements.json'), encoding='utf-8'))
VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))


def key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


def ledger(now, want):
    dn = dict(zip(key(now).tolist(), now[:, 3].tolist()))
    dw = dict(zip(key(want).tolist(), want[:, 3].tolist()))
    return len(set(dw) - set(dn)), len(set(dn) - set(dw)), sum(1 for k in set(dn) & set(dw) if dn[k] != dw[k])


L = {}
for w in V['works']:
    L[w['work']] = np.loadtxt(os.path.join(D, w['file']), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    N = DB.export_list(w['work'], None)
    print('① %s：清單 %d ↔ 子作品 %d，缺 %d、多 %d、色差 %d' % ((w['work'], len(L[w['work']]), len(N)) + ledger(N, L[w['work']])))
hide = ','.join('%s/%s' % (w['deck'], w['link']) for w in V['works'])
B = DB.export_list(DB.ASM, 'all', ('hide_links=' + hide,))
NOW = DB.export_list(DB.ASM, 'all')
ALL = np.concatenate(list(L.values()))
E = np.concatenate([B, ALL])
print('① 組裝件：藏本階段 %d ＋ 清單 %d ↔ 現在 %d，缺 %d、多 %d、色差 %d；清單跟原本重疊 %d' % (
    (len(B), len(ALL), len(NOW)) + ledger(NOW, E) + (len(E) - len(np.unique(key(E))),)))

# ②
with tempfile.TemporaryDirectory() as d:
    pj = os.path.join(d, 'p.json').replace(os.sep, '/')
    subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + pj], capture_output=True)
    PJ = json.load(open(pj, encoding='utf-8'))
by = {m['path']: m for m in PJ['models']}
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
imp = set(map(tuple, ALL[:, :3].tolist()))
src = {}
hit = 0
for r in VG['rows']:
    if r['type'] not in src:
        C = DB.export_list(r['work'], None)
        an = {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, r['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
        src[r['type']] = ((C[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3), an)
    samp, an = src[r['type']]
    m = by[r['host_link'] + '/' + r['model']]
    names = sorted(n for n in an if n in m['points'])
    X = np.hstack([np.array([np.array(an[n], float) + 0.5 for n in names]), np.ones((len(names), 1))])
    sol, *_ = np.linalg.lstsq(X, np.array([m['points'][n] for n in names], float), rcond=None)
    w = np.floor(samp @ sol[:3] + sol[3]).astype(int)
    hit += sum(1 for p in map(tuple, w.tolist()) if p in imp)
print('② 桿的格裡落了砲（引擎固定點反推的變換）：%d 個取樣點' % hit)

# ③
occ = set(map(tuple, NOW[:, :3].tolist()))


def hanging(cells):
    """每支桿：同一個 (x, z) 那一排（不算頭底下那一層）正上方一格要是實心。"""
    top = {}
    for x, y, z in cells:
        top.setdefault((x, y), z)
        top[(x, y)] = max(top[(x, y)], z)
    return sum(1 for (x, y), z in top.items() if (x, y, z + 1) not in occ)


print('③ 浮空（桿正上方那一格不是實心）：%d 欄（共 %d 欄）' % (hanging(imp), len({(x, y) for x, y, _ in imp})))

# ④
sh = ALL.copy()
sh[:, 1] += 1
occ_wo = set(map(tuple, B[:, :3].tolist()))
print('④ 反向對照：清單 y ＋1 ⇒ 結果帳 缺 %d、多 %d、色差 %d；浮空 %d 欄' % (ledger(NOW, np.concatenate([B, sh])) + (
    sum(1 for (x, y), z in {(p[0], p[1]): p[2] for p in map(tuple, sh[:, :3].tolist())}.items() if (x, y, z + 1) not in occ_wo),)))
dn = ALL[:, :3].copy()
dn[:, 2] -= 1                                                           # 🩸 第一版浮空的反向拿 y ＋1：桿本來就沿 y、平移後還在同一片天花板底下 ⇒ 0 —— 方向選錯；要往下
print('   浮空的反向：清單 z −1 ⇒ 浮空 %d 欄' % sum(1 for (x, y), z in {(p[0], p[1]): max(q[2] for q in [p]) for p in map(tuple, dn.tolist())}.items()
                                         if (x, y, z + 1) not in occ_wo))
st = {k: v for k, v in re.findall(r'🔢 (\w+) = (\S+)', subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=stats', '--arg', 'work=' + DB.ASM, '--arg', 'structure=1'],
                                                                     capture_output=True, text=True, encoding='utf-8', errors='replace').stdout)}
print('⑤ 引擎：格 %s、元件 %s、空腔 %s、link_overlap %s' % (st.get('total_voxels'), st.get('components'), st.get('cavities'), st.get('link_overlap')))
