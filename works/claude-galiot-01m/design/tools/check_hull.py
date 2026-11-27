# 出處：claude-felucca-01m/design/tools/check_hull.py（海鷗號；它出自 kotoko-fusta-01m/design/tools/check_hull.py）。
#   改的地方：作品 id、格子大小、量線形的站位改讀 plan.json（海鷗號寫死 claude-felucca-01m、170×161×50、x 20..150）。
# 蠍子號 步驟 4 讀數（TASK-0023）：
#   ① 結果帳：作品（export format=list links=none）vs 設計清單 masks/hull —— 缺／多／色差
#   ② 結構（在作品匯出的格子上算）：6 連通元件數、封閉空腔（跟外面不通的空格）、鏡像差（y ↔ 2·YC − y，含顏色）
#   ③ 線形對照：作品右舷外緣（每個 (x, z) 最大的 dy）vs lines.hb 取 floor；兩柱之間每 20 格、z 1..舷頂每 3
#   用法：python -I -X utf8 tools/check_hull.py [--probe=half_beam=3] [--shift=3]
#     --probe ⇒ 線形那一側加減（作品不動 ⇒ ③ 要報出差）；--shift=N ⇒ 設計清單整片往上搬 N 格（① 要報出缺／多）
import sys, os, json
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.stdout.reconfigure(encoding='utf-8')
import lines as HL
import wio

WORK = 'claude-galiot-01m'
probe = {}
shift = 0
for a in sys.argv[1:]:
    if a.startswith('--probe='):
        k, v = a[len('--probe='):].split('=')
        probe[k] = float(v)
    if a.startswith('--shift='):
        shift = int(a.split('=')[1])

plan = HL.load_plan(HERE)
SX, SY, SZ = [int(v) for v in plan['space']['hull']]
work = wio.export_list(WORK, None)
design = wio.load_lists(os.path.join(HERE, 'masks', 'hull')).copy()
design[:, 2] += shift
kw, kd = wio.key(work), wio.key(design)
cw = dict(zip(kw.tolist(), work[:, 3].tolist()))
cd = dict(zip(kd.tolist(), design[:, 3].tolist()))
missing = len(set(cd) - set(cw))
extra = len(set(cw) - set(cd))
cdiff = sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])
R = {'ledger': {'work': len(cw), 'design': len(cd), 'missing': missing, 'extra': extra, 'color_diff': cdiff}}
print('① 結果帳：作品 %d ／ 設計 %d ⇒ 缺 %d、多 %d、色差 %d' % (len(cw), len(cd), missing, extra, cdiff))
f0 = tuple(design[0].tolist())
R['ledger']['positive_control'] = {'cell': f0[:3], 'design_color': f0[3], 'work_color': cw.get(int(wio.key(design[:1])[0]))}

L = HL.Lines(plan, probe or None)
YC = L.YC
G = np.zeros((SX, 2 * YC + 1, SZ), np.uint8)
G[work[:, 0], work[:, 1], work[:, 2]] = work[:, 3]
S = G > 0
lab, ncomp = ndimage.label(S)
filled = ndimage.binary_fill_holes(S)
cav = int((filled & ~S).sum())
mir = G[:, ::-1, :]
mdiff = int((G != mir).sum())
R['structure'] = {'components': int(ncomp), 'cavity_cells': cav, 'mirror_diff_cells': mdiff,
                  'colors': {str(c): int((G == c).sum()) for c in np.unique(G[S])}}
print('② 結構：%d 元件、空腔 %d 格、鏡像差 %d 格；色 %s' % (ncomp, cav, mdiff, R['structure']['colors']))

occ = {}
for x, y, z, c in work.tolist():
    if y >= YC:
        k = (x, z)
        occ[k] = max(occ.get(k, -1), y - YC)
x_a = int(np.ceil(float(L.x_sh) / 20.0) * 20)
x_b = int(np.floor(float(L.x_st) / 20.0) * 20)
z_top = int(np.floor(L.z_side))
diffs = []
for x in range(x_a, x_b + 1, 20):
    for z in range(1, z_top + 1, 3):
        hb = float(L.hb(np.array([x + 0.5]), np.array([min(z + 0.5, float(L.sheer(np.array([x + 0.5]))[0]) + 0.5)]))[0])
        want = int(np.floor(hb)) if hb >= 0 else None
        got = occ.get((x, z))
        if want is None or got is None:
            continue
        diffs.append(abs(got - want))
R['lines'] = {'points': len(diffs), 'max_diff': max(diffs) if diffs else None, 'n_diff': sum(1 for d in diffs if d),
              'stations': [x_a, x_b, 20], 'z': [1, z_top, 3]}
print('③ 線形對照：%d 點、差 ≠ 0 的 %d 點、最大差 %s' % (len(diffs), R['lines']['n_diff'], R['lines']['max_diff']))
if not probe and not shift:
    with open(os.path.join(HERE, 'verify_step4.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
