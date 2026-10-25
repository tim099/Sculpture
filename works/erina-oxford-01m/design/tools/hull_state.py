# 牛津號 船殼現在應該的樣子（設計那一側）＝ draft_lines 的船殼清單 − 炮門開口 ＋ 塗裝 ⇒ masks/hull_state.vox.txt（給 delta_apply 對作品）
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
with open(os.path.join(design, 'masks', 'hull_state.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 牛津號 船殼現在應該的樣子（hull − 炮門開口 ＋ 塗裝）\n')
    for k in sorted(st):
        f.write('%d,%d,%d,%d\n' % (k + (st[k],)))
print('hull_state', len(st))
