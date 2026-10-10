# 階段六的檢查工具（2026-10-11 從 scratchpad 搬來；路徑以本作品為準）
# 設計層面的結構檢查：既有＋新木料 ⇒ face-connected 元件數、3D 封閉空腔、新木料各自的元件數、懸空
import sys, os, glob, numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay import replay
W = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m'
vox = replay(W)
old = np.array(list(vox.keys()), int)
lists = {}
for f in sorted(glob.glob(W + '/design/masks/ends/*.vox.txt')):
    a = [list(map(int, l.split(',')[:3])) for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#')]
    lists[os.path.basename(f).replace('.vox.txt', '')] = np.array(a, int)
new = np.vstack(list(lists.values()))
allv = np.vstack([old, new])
mn = allv.min(0) - 1; mx = allv.max(0) + 2
G = np.zeros(mx - mn, bool)
G[tuple((allv - mn).T)] = True
lab, n = ndimage.label(G)
sizes = np.bincount(lab.ravel())[1:]
print('components', n, 'largest', sizes.max(), 'others', sorted(sizes)[:-1][:10])
filled = ndimage.binary_fill_holes(G)
cav = filled & ~G
cl, cn = ndimage.label(cav)
print('sealed cavities', cn, 'cells', int(cav.sum()))
if cn:
    for i in range(1, min(cn, 20) + 1):
        idx = np.argwhere(cl == i) + mn
        print('  cavity', i, len(idx), 'x', idx[:, 0].min(), idx[:, 0].max(), 'y', idx[:, 1].min(), idx[:, 1].max(), 'z', idx[:, 2].min(), idx[:, 2].max())
# 每根木料一舷的元件數
for nm, a in lists.items():
    half = a[a[:, 1] > 160]
    m2 = half.min(0) - 1
    g = np.zeros(half.max(0) - m2 + 2, bool); g[tuple((half - m2).T)] = True
    l2, n2 = ndimage.label(g)
    if n2 != 1:
        s2 = np.bincount(l2.ravel())[1:]
        print('timber', nm, 'components per side', n2, 'sizes', sorted(s2)[:8])
