# 查讀數哪裡不對（只讀、不寫檔）：python -I -X utf8 -B diag.py <key>
#   撞格 ⇒ 哪個部件撞到哪一層的格；框外 ⇒ 哪一層、大概在哪；浮空 ⇒ 每一塊的格數與外框；門口 ⇒ 那一格與上下是什麼。
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
import civic, harbour, townpub, english, shipyard
from civic import composite

key = sys.argv[1]
fn = {f.__name__.replace('_', '-'): f for m in (civic, harbour, townpub, english, shipyard) for f in m.ALL}[key]
oob = []
_put = civic.Model.put


def put(s, layer, x, y, z, c, force=False):
    if not s.inb(x, y, z):
        oob.append((layer, x, y, z))
    return _put(s, layer, x, y, z, c, force)


civic.Model.put = put
B = fn()
M = B['M']
for L in M.links:
    bad = [k for k in L['cells'] if k in M.cells]
    if bad:
        print('撞格', L['name'], len(bad), sorted({M.cells[k] for k in bad})[:4], bad[:3])
if oob:
    a = np.array([o[1:] for o in oob])
    print('框外', len(oob), sorted({o[0] for o in oob}), 'min', a.min(0), 'max', a.max(0))
comp, _ = composite(M)
arr = np.zeros((M.X, M.Y, M.Z), bool)
for k in comp:
    arr[k] = True
lab, n = ndimage.label(arr)
ground = set(np.unique(lab[:, :, 0])) - {0}
for i in range(1, n + 1):
    if i in ground:
        continue
    idx = np.argwhere(lab == i)
    print('浮空', len(idx), idx.min(0), idx.max(0))
dx, dy, dz = M.anchors['door']
print('門口', (dx, dy, dz), '那一格', comp.get((dx, dy, dz)), '腳下', comp.get((dx, dy, dz - 1)), '頭上', comp.get((dx, dy, dz + 1)))
