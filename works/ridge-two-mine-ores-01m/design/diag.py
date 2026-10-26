# 浮空／撞格診斷：python -I -X utf8 -B diag.py <key>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'trailhead-harbour-01m', 'design')
sys.path.insert(1, TH)
import numpy as np
from scipy import ndimage
import ores
from quay import composite
key = sys.argv[1]
fn = [f for f in ores.ALL if f.__name__.replace('_', '-') == key][0]
B = fn(); M = B['M']
comp, clash = composite(M)
a = np.zeros((M.X, M.Y, M.Z), bool)
for k in comp: a[k] = True
lab, n = ndimage.label(a)
ground = set(np.unique(lab[:, :, 0])) - {0}
for i in range(1, n + 1):
    if i in ground: continue
    xs, ys, zs = np.nonzero(lab == i)
    print('floating', len(xs), 'x', xs.min(), xs.max(), 'y', ys.min(), ys.max(), 'z', zs.min(), zs.max(), 'colors', sorted({comp[(int(x), int(y), int(z))] for x, y, z in zip(xs, ys, zs)})[:5])
for L in M.links:
    hit = [k for k in L['cells'] if k in M.cells]
    if hit: print('clash', L['name'], len(hit), hit[:3], [M.cells[k] for k in hit[:3]])
print('door', M.anchors['door'], 'cell at door:', comp.get(tuple(M.anchors['door'])), 'below:', comp.get((M.anchors['door'][0], M.anchors['door'][1], M.anchors['door'][2] - 1)))
