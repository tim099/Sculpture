# 出處：erina-oxford-01m/design/tools/hull_state.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 船殼現在應該的樣子（設計那一側）＝ draft_lines 的船殼清單 − 炮門開口 ＋ 塗裝 ⇒ masks/hull_state.vox.txt（給 delta_apply 對作品）
#   用法：python -I -X utf8 tools/hull_state.py <design>（先跑 draft_lines.py、draft_ports.py）
import os, sys
import numpy as np
design = sys.argv[1]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import load_lists, key
hull = load_lists(os.path.join(design, 'masks', 'hull'))
carve = np.loadtxt(os.path.join(design, 'masks', 'ports', 'carve.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
paint = np.loadtxt(os.path.join(design, 'masks', 'ports', 'paint.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
st = {tuple(r[:3]): r[3] for r in hull.tolist()}
for r in carve.tolist():
    st.pop(tuple(r[:3]), None)
for r in paint.tolist():
    st[tuple(r[:3])] = r[3]
# 艏斜桅穿過船殼的孔（階段六刻掉、由艏斜桅填滿）⇒ 船殼應有的樣子不含那幾格
bp = os.path.join(design, 'masks', 'masts', 'bowsprit.vox.txt')
if os.path.exists(bp):
    for r in np.loadtxt(bp, delimiter=',', comments='#', dtype=np.int32, ndmin=2).tolist():
        st.pop(tuple(r[:3]), None)
# 舵柄穿過船尾舷牆的 helm port（步驟 11 刻掉、由舵柄填滿）
hp = os.path.join(design, 'masks', 'rudder', 'helm_port_hull.vox.txt')
if os.path.exists(hp):
    for r in np.loadtxt(hp, delimiter=',', comments='#', dtype=np.int32, ndmin=2).tolist():
        st.pop(tuple(r[:3]), None)
with open(os.path.join(design, 'masks', 'hull_state.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 信風號 船殼現在應該的樣子（hull − 炮門開口 ＋ 塗裝）\n')
    for k in sorted(st):
        f.write('%d,%d,%d,%d\n' % (k + (st[k],)))
print('hull_state', len(st))
