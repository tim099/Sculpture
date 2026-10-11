# 階段六的檢查工具（2026-10-11 雕之前修）：從船尾往前看（沿 +X）／從船頭往後看的剪影
# 作品現況（events 重播，扣掉 post_trim 要刻的柱頭）＋ 新木料清單；對每一條視線 (y, z)：
#   · 視線在船殼外形裡（X 範圍內有任一個 X 的剖面包住它）卻在這一段 X 裡一格都沒碰到 ⇒「看得進船殼」
# 用法：python -I silhouette_ends.py [stern|bow]
import sys, os, glob, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')
from replay import replay
import draft_frames_ends as DFE
W = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m'
which = sys.argv[1] if len(sys.argv) > 1 else 'stern'
cx = DFE.Ctx(W + '/design')
occ = set(cx.world.keys())
for f in sorted(glob.glob(W + '/design/masks/ends/*.vox.txt')):
    for line in open(f, encoding='utf-8'):
        if line.strip() and not line.startswith('#'):
            x, y, z = (int(v) for v in line.split(',')[:3])
            occ.add((x, y, z))
xr = (92, 200) if which == 'stern' else (590, 700)
pts = np.array([p for p in occ if xr[0] <= p[0] <= xr[1]], int)
hit = {}
for x, y, z in pts:
    k = (y - 160, z)
    if k not in hit or (x < hit[k] if which == 'stern' else x > hit[k]):
        hit[k] = x
holes = []
for z in range(0, 137):
    for dy in range(0, 70):
        if (dy, z) in hit:
            continue
        # 這條視線在船殼外形裡嗎（X 範圍內任一剖面）
        ins = False
        for X in np.arange(xr[0] + 0.5, xr[1], 1.0):
            if cx.inside(np.array([int(X)]), np.array([dy]), np.array([z]))[0] and z + 0.5 <= cx.top(X):
                ins = True
                break
        if ins:
            holes.append((dy, z))
print(which, 'rays hitting', len(hit), 'see-into-hull rays (dy>=0 side)', len(holes))
if holes:
    a = np.array(holes)
    for z in sorted(set(a[:, 1])):
        d = sorted(a[a[:, 1] == z][:, 0])
        print('  z %3d  dy %s' % (z, d if len(d) < 14 else '%d..%d (%d)' % (d[0], d[-1], len(d))))
