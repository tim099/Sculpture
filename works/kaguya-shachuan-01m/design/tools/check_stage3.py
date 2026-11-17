# 出處：kaguya-guineaman-01m/design/tools/check_stage3.py（改寫供沙船步驟 4 後半驗證）
# 讀數：作品匯出 vs 預期（結果帳）、砲門與船尾窗開口實心檢查（正／反向對照）
# 用法：python -I -X utf8 tools/check_stage3.py <design> [mark=炮門塗裝:end]
import os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
mark = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('mark=')), '炮門塗裝:end')
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
import lines as HL
from wio import export_list, load_lists, key

WORK = 'kaguya-shachuan-01m'

W = export_list(WORK, mark)
H_hull = load_lists(os.path.join(design, 'masks', 'hull'))
C_carve = np.loadtxt(os.path.join(design, 'masks', 'ports', 'carve.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
P_paint = np.loadtxt(os.path.join(design, 'masks', 'ports', 'paint.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')

exp = dict(zip(key(H_hull).tolist(), H_hull[:, 3].tolist()))
for k in key(C_carve).tolist():
    exp.pop(k, None)
for k, c in zip(key(P_paint).tolist(), P_paint[:, 3].tolist()):
    exp[k] = c

got = dict(zip(key(W).tolist(), W[:, 3].tolist()))
miss = len(set(exp) - set(got))
extra = len(set(got) - set(exp))
cdiff = sum(1 for k in set(exp) & set(got) if exp[k] != got[k])
print('結果帳（%s）：作品 %d、預期 %d、缺 %d、多 %d、色差 %d' % (mark, len(W), len(exp), miss, extra, cdiff))

carve_hits = sum(1 for k in key(C_carve).tolist() if k in got)
print('開口實心檢查（%s）：刻除清單 %d 格裡仍存在於作品的有 %d 格' % (mark, len(C_carve), carve_hits))
