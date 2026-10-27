# 階段五（TASK-0594）讀數：每件裝飾子作品匯出 vs 清單（結果帳）、跟組裝件其他部件的重疊（組裝件 links 全開 vs 拿掉這一件）
#   用法：python -I -X utf8 tools/check_stage5.py <design>
import os, sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key
HULL = 'abigail-fluyt-01m'
for nm in ('espolon', 'figurehead', 'stern-deco', 'name-board'):
    W = export_list('%s-%s' % (HULL, nm), None)
    D = np.loadtxt(os.path.join(design, 'masks', 'deco', nm + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
    print('%-11s 作品 %5d、設計 %5d、缺 %d、多 %d、色差 %d' % (nm, len(cw), len(cd), len(set(cd) - set(cw)), len(set(cw) - set(cd)), sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])))
