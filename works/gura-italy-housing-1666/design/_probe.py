# 檢查：每一棟的出框、部件撞格、浮空（build.py 之前先跑）
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icommon, kit
orig = kit.Model.put
bad = {}
def put(s, layer, x, y, z, c, force=False):
    if not s.inb(x, y, z): bad.setdefault(id(s), []).append((x, y, z, layer))
    return orig(s, layer, x, y, z, c, force)
kit.Model.put = put
import italy
import numpy as np
from scipy import ndimage
for fn in italy.ALL:
    B = fn(); M = B['M']; comp, clash = kit.composite(M)
    a = np.zeros((M.X, M.Y, M.Z), bool)
    for k in comp: a[k] = True
    lab, n = ndimage.label(a); g = set(np.unique(lab[:, :, 0])) - {0}
    fl = [(int((lab == i).sum()), np.argwhere(lab == i)[0].tolist()) for i in range(1, n + 1) if i not in g]
    b = bad.get(id(M), [])
    print(B['key'], 'oob', M.oob, b[:3], 'clash', clash, 'float', fl[:4])
