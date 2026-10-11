# 階段六的檢查工具（2026-10-11 從 scratchpad 搬來；雕之前修改成讀「刻掉柱頭之後」的作品）
# 設計層面的結構檢查：作品現況（扣掉 post_trim）＋新木料 ⇒ 清單內重複格、跟作品重疊、face-connected 元件數、3D 封閉空腔、
#   新木料各自的元件數（每一舷）、計畫 vs 清單的旗標
import sys, os, glob, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')
import draft_frames_ends as DFE
W = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m'
cx = DFE.Ctx(W + '/design')
world = set(cx.world.keys())
print('world（刻掉柱頭之後）', len(world), '｜post_trim', len(cx.trim))
lists = {}
dups = 0
for f in sorted(glob.glob(W + '/design/masks/ends/*.vox.txt')):
    a = [tuple(map(int, l.split(',')[:3])) for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#')]
    dups += len(a) - len(set(a))
    lists[os.path.basename(f).replace('.vox.txt', '')] = np.array(a, int)
new = np.vstack(list(lists.values()))
newset = set(map(tuple, new))
print('lists', len(lists), 'voxels', len(new), '| 清單內重複', dups, '| 清單之間重複', len(new) - len(newset) - dups,
      '| 跟作品重疊', len(newset & world), '| 跟要刻的柱頭重疊', len(newset & cx.trim))
old = np.array(list(world), int)
allv = np.vstack([old, new])
mn = allv.min(0) - 1
mx = allv.max(0) + 2
G = np.zeros(mx - mn, bool)
G[tuple((allv - mn).T)] = True
lab, n = ndimage.label(G)
sizes = np.bincount(lab.ravel())[1:]
print('components', n, 'largest', sizes.max(), 'others', sorted(sizes)[:-1][:10], '| total', int(G.sum()))
filled = ndimage.binary_fill_holes(G)
cav = filled & ~G
cl, cn = ndimage.label(cav)
print('sealed cavities', cn, 'cells', int(cav.sum()))
for i in range(1, min(cn, 20) + 1):
    idx = np.argwhere(cl == i) + mn
    print('  cavity', i, len(idx), 'x', idx[:, 0].min(), idx[:, 0].max(), 'y', idx[:, 1].min(), idx[:, 1].max(), 'z', idx[:, 2].min(), idx[:, 2].max())
for nm, a in lists.items():
    half = a[a[:, 1] >= 160]
    m2 = half.min(0) - 1
    g = np.zeros(half.max(0) - m2 + 2, bool)
    g[tuple((half - m2).T)] = True
    l2, n2 = ndimage.label(g)
    if n2 != 1:
        s2 = np.bincount(l2.ravel())[1:]
        print('timber', nm, 'components per side', n2, 'sizes', sorted(s2)[:8])
v = json.load(open(W + '/design/verify_frames_ends.json', encoding='utf-8'))
for r in v['timbers']:
    if r.get('plan_vs_list'):
        print('flag', r['name'], r['plan_vs_list'])

# ── 2026-10-11 第二輪 verifier 量到的那幾格，做成常駐檢查 ──
occ = set(map(tuple, allv))
own = {}
for nm, a in lists.items():
    for c in map(tuple, a):
        own[c] = nm
# ① 同一對 cant 兩片之間 1–3 格的空段（沿 x、y、z 任一軸，一端是 -fwd、另一端是 -aft）
gaps = {}
for c, nm in own.items():
    if '-cant' not in nm or not nm.endswith('-aft'):
        continue
    base = nm[:-4]
    for ax in range(3):
        for sg in (1, -1):
            run = []
            p = list(c)
            for _ in range(4):
                p[ax] += sg
                q = tuple(p)
                if q in occ:
                    if own.get(q) == base + '-fwd' and 1 <= len(run) <= 3:
                        for r in run:
                            gaps.setdefault(base, set()).add(r)
                    break
                run.append(q)
print('同一對 cant 之間 1–3 格的空段', {k: len(v) for k, v in sorted(gaps.items())} or 0)
# ② 舷頂：每個 X 的最高格（|dy| ≥ 9）—— 看兩頭接縫有沒有台階
tops = {}
for x, y, z in occ:
    if abs(y - 160) >= 9 and z > tops.get(x, -1):
        tops[x] = z
for lo, hi in ((170, 196), (606, 632)):
    print('舷頂 X %d..%d' % (lo, hi), ' '.join('%d:%d' % (x, tops.get(x, -1)) for x in range(lo, hi + 1)))
# ③ 接縫處舷側的縫：z 60..120、|dy| ≥ 30 的格投影到 x，列出空著的 x
for lo, hi in ((175, 192), (612, 630)):
    xs = sorted({x for x, y, z in occ if lo <= x <= hi and abs(y - 160) >= 30 and 60 <= z <= 120})
    print('舷側有格的 x（%d..%d）' % (lo, hi), xs, '空', [x for x in range(lo, hi + 1) if x not in xs])
# ④ 從船尾看的單格洞（Z 40..80）：視線 x 92..200 一格都沒碰到、但在外形裡（外形 ＝ 同一列 y 兩側都有格）
for z in range(40, 81):
    row = {y for x, y, zz in occ if zz == z and 92 <= x <= 200}
    if row:
        holes = [y for y in range(min(row), max(row) + 1) if y not in row]
        if holes:
            print('  從船尾看 z %d 的洞 y %s' % (z, holes))
