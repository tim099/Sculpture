# 越嶺號 階段一讀數（TASK-0758；照皇家號 check_hull.py 改範圍）：
#   ① 結果帳：作品（export format=list links=none mark=船殼:end）vs 設計清單 masks/hull —— 缺／多／色差
#   ② 線形對照：作品右舷外緣（每個 (x, z) 最大的 dy）vs lines.hb 取 floor；x 60..300 每 20、z 2..14 每 3
#   用法：python -I -X utf8 tools/check_hull.py [--probe=half_beam=+3]  （probe ⇒ 線形那一側加減，作品不動 ⇒ 要報出差）
import sys, os, json
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.stdout.reconfigure(encoding='utf-8')
import lines as HL
import wio

probe = {}
for a in sys.argv[1:]:
    if a.startswith('--probe='):
        k, v = a[len('--probe='):].split('=')
        probe[k] = float(v)

work = wio.export_list('kotoko-fusta-01m', '船殼:end')
design = wio.load_lists(os.path.join(HERE, 'masks', 'hull'))
kw, kd = wio.key(work), wio.key(design)
cw = dict(zip(kw.tolist(), work[:, 3].tolist()))
cd = dict(zip(kd.tolist(), design[:, 3].tolist()))
missing = len(set(cd) - set(cw))
extra = len(set(cw) - set(cd))
cdiff = sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])
print('① 結果帳：作品 %d ／ 設計 %d ⇒ 缺 %d、多 %d、色差 %d' % (len(cw), len(cd), missing, extra, cdiff))

plan = HL.load_plan(HERE)
L = HL.Lines(plan, probe or None)
occ = {}
for x, y, z, c in work.tolist():
    if y >= L.YC:
        k = (x, z)
        occ[k] = max(occ.get(k, -1), y - L.YC)
n = 0
diffs = []
for x in range(60, 301, 20):
    for z in range(2, 16, 3):
        h = float(L.hb(x + 0.5, z + 0.5))
        if h < 0 or (x, z) not in occ:
            continue
        n += 1
        diffs.append(occ[(x, z)] - int(np.floor(h)))
diffs = np.array(diffs)
print('② 線形對照%s：%d 點、差不為 0 的 %d 點、最大 |差| %d' % (' probe=' + json.dumps(probe) if probe else '', n, int((diffs != 0).sum()), int(np.abs(diffs).max()) if n else -1))
