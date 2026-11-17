# 來源：basecamp-piragua-01m/design/tools/check_hull.py（改寫對照突尼斯轉運划艇 Sandal）
# 步驟 4 船殼結果帳：作品匯出（CLI export format=list）逐格對清單 design/masks/hull/hull.vox.txt
#   讀數：缺／多／色差、6 鄰接元件數、封閉空腔、形狀鏡像差與塗裝鏡像差（y ↔ 100 − y）。
#   反向對照：--shift=dz 把清單整份往上搬 dz 格再比 ⇒ missing == extra == list（尺會叫）。
#   用法：python -I -X utf8 tools/check_hull.py [--shift=3]
import os, sys, json
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio

sys.stdout.reconfigure(encoding='utf-8')
shift = int(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--shift=')), '0'))
want = np.loadtxt(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
want[:, 2] += shift
got = wio.export_list('kiara-tunis-sandal-01m', None)
W = {tuple(r[:3]): int(r[3]) for r in want}
G = {tuple(r[:3]): int(r[3]) for r in got}
miss = [k for k in W if k not in G]
extra = [k for k in G if k not in W]
cdiff = [k for k in W if k in G and W[k] != G[k]]
A = np.zeros((136, 101, 30), bool)
for k in G:
    A[k] = True
lab, n = ndimage.label(A)
la, na = ndimage.label(~A)
border = set(np.unique(np.r_[
    la[0].ravel(), la[-1].ravel(),
    la[:, 0].ravel(), la[:, -1].ravel(),
    la[:, :, 0].ravel(), la[:, :, -1].ravel(),
]))
cav = len([i for i in range(1, na + 1) if i not in border])
mir_shape = int((A != A[:, ::-1, :]).sum())
mir_color = sum(1 for k, c in G.items() if G.get((k[0], 100 - k[1], k[2])) != c)
print(json.dumps({
    'shift': shift,
    'list': len(W),
    'work': len(G),
    'missing': len(miss),
    'extra': len(extra),
    'color_diff': len(cdiff),
    'components': int(n),
    'cavities': cav,
    'mirror_diff': mir_shape,
    'mirror_color_diff': mir_color,
}, ensure_ascii=False))
