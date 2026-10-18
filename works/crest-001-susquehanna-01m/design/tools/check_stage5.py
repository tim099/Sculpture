# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/check_stage5.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 階段五讀數（TASK-0610）：每件裝飾子作品的結果帳（匯出 vs 清單）
#   用法：python -I -X utf8 tools/check_stage5.py <design>
import os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key  # noqa: E402

HULL = 'crest-001-susquehanna-01m'
SUBID = {'head': 'head', 'figurehead': 'figurehead', 'stern': 'stern-deco', 'name': 'name-board', 'funnels': 'funnels', 'screw': 'screw'}
tot = [0, 0, 0, 0]
for k, sub in SUBID.items():
    W = export_list('%s-%s' % (HULL, sub), None)
    D = np.loadtxt(os.path.join(design, 'masks', 'deco', k + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
    m, e = len(set(cd) - set(cw)), len(set(cw) - set(cd))
    c = sum(1 for q in set(cd) & set(cw) if cd[q] != cw[q])
    print('  %-10s 作品 %6d、設計 %6d、缺 %d、多 %d、色差 %d' % (k, len(W), len(D), m, e, c))
    tot = [tot[0] + len(W), tot[1] + m, tot[2] + e, tot[3] + c]
print('階段五結果帳：%d 件、作品 %d 格、缺 %d、多 %d、色差 %d' % ((len(SUBID),) + tuple(tot)))
