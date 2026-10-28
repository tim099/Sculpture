# 直接出處：apex-two-galeon-01m/design/tools/check_stage5.py（康塞普西翁號，TASK-0969）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是康塞普西翁號那時寫的出處
# 直接出處：gura-pinas-01m/design/tools/check_stage5.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/tools/check_stage5.py（收穫號，照抄後改成聖羅曼號 —— TASK-0970）
# 階段五（TASK-0594）讀數：每件裝飾子作品匯出 vs 清單（結果帳）、跟組裝件其他部件的重疊（組裝件 links 全開 vs 拿掉這一件）
#   用法：python -I -X utf8 tools/check_stage5.py <design>
import os, sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key
HULL = 'pinnacle-patache-01m'
for nm in ('espolon', 'figurehead', 'hackebort'):      # 聖羅曼號：沒有 stern-deco
    W = export_list('%s-%s' % (HULL, nm), None)
    D = np.loadtxt(os.path.join(design, 'masks', 'deco', nm + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
    print('%-11s 作品 %5d、設計 %5d、缺 %d、多 %d、色差 %d' % (nm, len(cw), len(cd), len(set(cd) - set(cw)), len(set(cw) - set(cd)), sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])))
