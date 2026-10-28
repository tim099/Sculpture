# 出處：erina-oxford-01m/design/tools/check_stage3.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 階段三讀數（TASK-0972）：結果帳（作品 ＝ 船殼 − 刻 ＋ 換色）、從作品格子量炮門開沒開（正向對照：同一把尺量刻之前的 船殼:end）
#   用法：python -I -X utf8 tools/check_stage3.py <design>
#   作品那一側一律從 CLI 匯出讀（export format=list links=none）
import os, sys, json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, load_lists, key

WORK = 'erina-tradewind-01m'
hull = load_lists(os.path.join(design, 'masks', 'hull'))
carve = np.loadtxt(os.path.join(design, 'masks', 'ports', 'carve.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
paint = np.loadtxt(os.path.join(design, 'masks', 'ports', 'paint.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
want = dict(zip(key(hull).tolist(), hull[:, 3].tolist()))
for k in key(carve).tolist():
    want.pop(k, None)
for k, c in zip(key(paint).tolist(), paint[:, 3].tolist()):
    want[k] = c
W = export_list(WORK, '炮門塗裝:end')
got = dict(zip(key(W).tolist(), W[:, 3].tolist()))
miss = len(set(want) - set(got))
extra = len(set(got) - set(want))
cd = sum(1 for k in set(want) & set(got) if want[k] != got[k])
print('結果帳：作品 %d、設計 %d、缺 %d、多 %d、色差 %d' % (len(got), len(want), miss, extra, cd))

V = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))


def open_check(cells):
    S = set(key(cells[:, :3]).tolist())
    bad = []
    for p in V['ports']:
        for side in (1, -1):
            n = 0
            for x in range(p['x0'], p['x1'] + 1):
                for z in range(p['z0'], p['z1'] + 1):
                    for dy in range(10, 40):
                        y = 96 + side * dy
                        if (x * 1000 + y) * 1000 + z in S:
                            n += 1
            if n:
                bad.append((p['deck'], p['i'], 'S' if side > 0 else 'P', n))
    return bad


b = open_check(W)
print('炮門開口裡還有實心（作品 炮門:end）：%d 個' % len(b), b[:4])
b0 = open_check(export_list(WORK, '船殼:end'))
print('正向對照（同一把尺量刻之前的 船殼:end）：%d 個報（應該 %d）' % (len(b0), len(V['ports']) * 2), b0[:2])
