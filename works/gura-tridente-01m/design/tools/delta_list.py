# 新清單 − 作品現在已有的格 ⇒ 只補新增的那幾格（全清單重貼會被已佔用的格擋）
#   用法：python -I -X utf8 tools/delta_list.py <work> <新清單> <輸出>
import os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wio import export_list, key  # noqa: E402

work, src, dst = sys.argv[1:4]
W = export_list(work, None)
N = np.loadtxt(src, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
have = set(key(W).tolist())
kn = key(N)
add = N[[k not in have for k in kn.tolist()]]
gone = len(have - set(kn.tolist()))
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# %s：新清單 − 作品現況（delta_list.py）\n' % os.path.basename(src))
    for x, y, z, c in add.tolist():
        f.write('%d,%d,%d,%d\n' % (x, y, z, c))
print('%s：補 %d 格；作品有、新清單沒有 %d 格' % (work, len(add), gone))
if gone:
    sys.exit(1)
