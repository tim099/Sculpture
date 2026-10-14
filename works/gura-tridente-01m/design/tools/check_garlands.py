# TASK-0577 讀數：① 四件子作品 匯出 vs 清單；組裝件 ＝ 藏本階段關聯 ＋ 清單 ② 不碰砲（砲的變換從引擎固定點反推）③ 貼牆：每一欄木條靠牆那一格的外側一格是船殼
#   ④ 反向對照：清單整批往船裡推 1 格 ⇒ 結果帳要報、貼牆要報；z −3 ⇒ 跟原本的格重疊（插進甲板）要報
#   砲索的 obj 檢查（garland 變實心之後）另跑 tools/check_gunfittings.py。用法：python -I -X utf8 tools/check_garlands.py <design>
import json, os, re, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import deco_base as DB  # noqa: E402

WORKS = os.path.dirname(os.path.dirname(D))
V = json.load(open(os.path.join(D, 'verify_garlands.json'), encoding='utf-8'))
VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
YC = 200


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

with tempfile.TemporaryDirectory() as d:
    pj = os.path.join(d, 'p.json').replace(os.sep, '/')
    subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + pj], capture_output=True)
    PJ = json.load(open(pj, encoding='utf-8'))
by = {m['path']: m for m in PJ['models']}
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
mine = set(map(tuple, ALL[:, :3].tolist()))
src, hit = {}, 0
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
    hit += sum(1 for p in map(tuple, np.floor(samp @ sol[:3] + sol[3]).astype(int).tolist()) if p in mine)
print('② garland 的格裡落了砲（引擎固定點反推的變換）：%d 個取樣點' % hit)

H = DB.export_list(DB.ASM, '船殼')
hull = set(map(tuple, H[:, :3].tolist()))


def detached(cells):
    """每個 (x, z) 一條木條：靠牆那一格（|y − 中線| 最大的那格）的外側一格要是船殼。"""
    outer = {}
    for x, y, z in cells:
        k = (x, z, 1 if y > YC else -1)
        if k not in outer or abs(y - YC) > abs(outer[k] - YC):
            outer[k] = y
    return sum(1 for (x, z, s), y in outer.items() if (x, y + s, z) not in hull), len(outer)


wood = ALL[ALL[:, 3] == 136][:, :3]
print('③ 貼牆：靠牆那一格外側不是船殼的 %d 欄（共 %d 欄）' % detached(map(tuple, wood.tolist())))
inw = ALL.copy()
inw[:, 1] -= np.where(inw[:, 1] > YC, 1, -1)
dn = ALL.copy()
dn[:, 2] -= 3                                                           # 甲板面上第一層空氣 ＋2 ⇒ 往下 3 才到甲板板（第一版 −2 只報 22 格：那還是空氣）
base = set(map(tuple, B[:, :3].tolist()))
w2 = inw[inw[:, 3] == 136][:, :3]
print('④ 反向對照：往船裡推 1 ⇒ 結果帳 缺 %d、多 %d、色差 %d；貼牆失敗 %d 欄｜z −3 ⇒ 跟原本的格重疊 %d' % (
    ledger(NOW, np.concatenate([B, inw])) + (detached(map(tuple, w2.tolist()))[0], sum(1 for p in map(tuple, dn[:, :3].tolist()) if p in base))))
st = {k: v for k, v in re.findall(r'🔢 (\w+) = (\S+)', subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=stats', '--arg', 'work=' + DB.ASM, '--arg', 'structure=1'],
                                                                     capture_output=True, text=True, encoding='utf-8', errors='replace').stdout)}
print('⑤ 引擎：格 %s、元件 %s、空腔 %s、link_overlap %s' % (st.get('total_voxels'), st.get('components'), st.get('cavities'), st.get('link_overlap')))
