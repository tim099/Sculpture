# 來源：calli-cosecha-01m/design/tools/check_hull.py（照抄，WORK 與量的範圍改本船）
# 階段二（TASK-0972）讀數：作品匯出 vs 清單（結果帳）、線形對照（每站每個高度的右舷外緣 vs lines 的半寬）、反向對照
#   用法：python -I -X utf8 tools/check_hull.py <design> [mark=船殼:end] [probe_x=<站>]
#   · 作品那一側一律從 CLI 匯出讀（export format=list links=none）—— ⛔ 不讀自己的清單當作品
#   · 結構照 gura-tridente-01m/design/tools/check_hull.py
import os, sys, math
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
mark = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('mark=')), '船殼:end')
probe_x = int(next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('probe_x=')), '-1'))
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
import lines as HL
from wio import export_list, load_lists, key

WORK = 'erina-oxford-01m'

W = export_list(WORK, mark)
D = load_lists(os.path.join(design, 'masks', 'hull'))
kw, kd = key(W), key(D)
cw = dict(zip(kw.tolist(), W[:, 3].tolist()))
cd = dict(zip(kd.tolist(), D[:, 3].tolist()))
miss = len(set(cd) - set(cw))
extra = len(set(cw) - set(cd))
cdiff = sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])
print('結果帳：作品 %d、設計 %d、缺 %d、多 %d、色差 %d' % (len(W), len(D), miss, extra, cdiff))

plan = HL.load_plan(design)
L = HL.Lines(plan)
YC = L.YC
S = W[W[:, 1] >= YC]
outer = {}
for x, y, z in S[:, :3].tolist():
    k = (x, z)
    if y - YC > outer.get(k, -1):
        outer[k] = y - YC
diffs, worst, probe_hits = [], (0, None), 0
for x in range(40, 312, 10):
    for z in range(4, 98, 3):
        if z > L.top_z(x + 0.5):
            continue
        h = float(L.hb(np.array([x + 0.5]), np.array([z + 0.5]))[0])
        if h < 0:
            continue
        want = math.floor(h) + (3 if x == probe_x else 0)
        got = outer.get((x, z))
        if got is None:
            continue
        dlt = got - want
        diffs.append(abs(dlt))
        if x == probe_x and dlt != 0:
            probe_hits += 1
        if abs(dlt) > abs(worst[0]):
            worst = (dlt, (x, z, got, want))
print('線形對照：%d 點、|差| 最大 %d（%s）、差 ≠ 0 的 %d 點%s' % (len(diffs), max(diffs), worst[1], sum(1 for v in diffs if v),
      '（probe_x=%d：設計那一站 +3 ⇒ 報 %d 點）' % (probe_x, probe_hits) if probe_x >= 0 else ''))
