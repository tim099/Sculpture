# 船殼碗裡面的檢查（階段十八 v2 之後補的尺）：某件子作品的每一格，在同一個 (x, z) 那一列左右兩邊都有船殼、正下方也有船殼。
# 只讀引擎匯出：船殼子作品的 list、受測子作品的 list（＋它在組裝件裡的 at）。
# 用法：python -I -X utf8 -B check_inside_hull.py <船殼 list> <受測 list> <at x,y,z> [偏移 dx,dy,dz]
#   偏移 ＝ 反向對照：受測格整批平移
# 🩸 為什麼要這把尺：彈藥庫 v1 有 3,582 格長到船底外，「1 塊／空腔 0／左右對稱」三把尺都過 —— 沒有一把在問「它在不在船裡」。
import sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
h = np.loadtxt(sys.argv[1], delimiter=',', dtype=int, comments='#', ndmin=2)[:, :3]
p = np.loadtxt(sys.argv[2], delimiter=',', dtype=int, comments='#', ndmin=2)
at = np.array([int(v) for v in sys.argv[3].split(',')])
off = np.array([int(v) for v in sys.argv[4].split(',')]) if len(sys.argv) > 4 else np.zeros(3, int)
H = np.zeros((384, 161, 320), bool); H[h[:, 0], h[:, 1], h[:, 2]] = True
w = p[:, :3] + at + off
out = []
for x, y, z in w:
    ys = np.nonzero(H[x, :, z])[0]
    ok = len(ys) > 0 and ys.min() < y < ys.max() and H[x, y, :z].any()
    if not ok:
        out.append((x, y, z))
o = np.array(out)
print('受測 %d 格，在船殼碗外 %d 格' % (len(w), len(o)) + ('；外框 %s–%s' % (o.min(0).tolist(), o.max(0).tolist()) if len(o) else ''))
