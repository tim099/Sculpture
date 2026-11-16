# 塔爾塔納 步驟 4（TASK-1299）讀數：作品匯出 vs 設計終帳（hull - carve + paint）、線形對照與反向對照
#   用法：python -I -X utf8 tools/check_hull.py <design> [mark=] [probe_x=<站>]
import os, sys, math
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
mark = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('mark=')), None)
probe_x = int(next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('probe_x=')), '-1'))
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
import lines as HL
from wio import export_list, load_lists, key

WORK = 'apex-one-tartane-01m'

W = export_list(WORK, mark)
D0 = load_lists(os.path.join(design, 'masks', 'hull'))
cd = dict(zip(key(D0).tolist(), D0[:, 3].tolist()))

carve_f = os.path.join(design, 'masks', 'paint', 'carve.vox.txt')
paint_f = os.path.join(design, 'masks', 'paint', 'paint.vox.txt')
if os.path.exists(carve_f):
    C = np.loadtxt(carve_f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    for k in key(C).tolist():
        cd.pop(k, None)
if os.path.exists(paint_f):
    P = np.loadtxt(paint_f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    for k, c in zip(key(P).tolist(), P[:, 3].tolist()):
        cd[k] = c

cw = dict(zip(key(W).tolist(), W[:, 3].tolist()))
miss = len(set(cd) - set(cw))
extra = len(set(cw) - set(cd))
cdiff = sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])
print('結果帳：作品 %d、設計 %d、缺 %d、多 %d、色差 %d' % (len(W), len(cd), miss, extra, cdiff))

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
for x in range(96, 260, 8):
    for z in range(2, 42, 3):
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
print('線形對照：%d 點、|差| 最大 %d（%s）、差 ≠ 0 的 %d 點%s' % (
    len(diffs), max(diffs), worst[1], sum(1 for v in diffs if v),
    '（probe_x=%d：設計那一站 +3 ⇒ 報 %d 點）' % (probe_x, probe_hits) if probe_x >= 0 else ''))
