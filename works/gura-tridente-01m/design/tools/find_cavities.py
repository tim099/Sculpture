# 找封閉空腔在哪：組裝件（照關聯開關）匯出 ⇒ 3D 補洞 − 原本 ⇒ 每一個空腔的格數與外框
#   用法：python -I -X utf8 tools/find_cavities.py [work=gura-tridente-01m-assembly]
import os, subprocess, sys, tempfile
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
work = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('work=')), 'gura-tridente-01m-assembly')
with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, 'a.txt').replace(os.sep, '/')
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    A = np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
o = A[:, :3].min(0) - 1
sh = A[:, :3].max(0) - o + 2
G = np.zeros(sh, bool)
G[A[:, 0] - o[0], A[:, 1] - o[1], A[:, 2] - o[2]] = True
F = ndimage.binary_fill_holes(G) & ~G
lab, n = ndimage.label(F)
print('格數 %d、空腔 %d 個、%d 格' % (len(A), n, int(F.sum())))
for i in range(1, n + 1):
    idx = np.argwhere(lab == i)
    lo, hi = idx.min(0) + o, idx.max(0) + o
    print('  空腔 %d：%d 格　x %d..%d　y %d..%d　z %d..%d' % (i, len(idx), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
