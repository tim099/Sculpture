# 讀數小工具：幾份清單合起來的 6 連通元件（每塊的格數、框、第一格是哪份清單的）
#   用法：python -I -X utf8 tools/components.py <清單…>
import sys, os
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 280, 201, 180
G = np.zeros((SX, SY, SZ), bool)
src = {}
for f in sys.argv[1:]:
    a = np.loadtxt(f, delimiter=',', comments='#', dtype=int, ndmin=2, encoding='utf-8')
    G[a[:, 0], a[:, 1], a[:, 2]] = True
    for r in a:
        src[tuple(r[:3])] = os.path.basename(f)
lab, n = ndimage.label(G)
sz = ndimage.sum(G, lab, range(1, n + 1))
print('元件', n)
for i in np.argsort(-sz)[:15]:
    p = np.argwhere(lab == i + 1)
    print(int(sz[i]), p.min(0).tolist(), p.max(0).tolist(), src.get(tuple(p[0])))
