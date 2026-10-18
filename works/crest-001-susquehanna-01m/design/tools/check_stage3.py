# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/check_stage3.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 階段三（TASK-0608）讀數：作品匯出（mark=砲門:end）vs 設計（船殼清單 − 刻 ＋ 換色）、每個砲門從船外看不看得穿
#   抄自三叉戟號 gura-tridente-01m/design/tools/check_stage3.py（gura，TASK-0556）；改：作品 ID。
#   用法：python -I -X utf8 tools/check_stage3.py <design> [mark=砲門:end]（反向對照：mark=船殼:end ⇒ 砲門還沒開，每一個都要報看不穿）
import os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
import hull_lines as HL
import layout as LY
from wio import export_list, load_lists, key  # noqa: E402


def read(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


mark = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('mark=')), '砲門:end')
plan = HL.load_plan(design)
L = HL.Lines(plan)
YC = L.YC
W = export_list('crest-001-susquehanna-01m', mark)
hull = load_lists(os.path.join(design, 'masks', 'hull'))
carve = read(os.path.join(design, 'masks', 'ports', 'carve.vox.txt'))
paint = read(os.path.join(design, 'masks', 'ports', 'paint.vox.txt'))
exp = dict(zip(key(hull).tolist(), hull[:, 3].tolist()))
for k in key(carve).tolist():
    exp.pop(k)
for k, c in zip(key(paint).tolist(), paint[:, 3].tolist()):
    exp[k] = c
got = dict(zip(key(W).tolist(), W[:, 3].tolist()))
miss = len(set(exp) - set(got))
extra = len(set(got) - set(exp))
cdiff = sum(1 for k in set(exp) & set(got) if exp[k] != got[k])
print('[mark %s] 階段三結果帳：' % mark + '作品 %d、設計 %d、缺 %d、多 %d、色差 %d' % (len(got), len(exp), miss, extra, cdiff))
solid = set(got)
bad = []
for p in LY.ports(plan):
    for side in (1, -1):
        n = 0
        for x in range(p['x0'], p['x1'] + 1):
            for z in range(p['z0'], p['z1'] + 1):
                for dy in range(6, 100):
                    if (x * 1000 + (YC + side * dy)) * 1000 + z in solid:
                        n += 1
        if n:
            bad.append((p['deck'], p['i'], 'S' if side > 0 else 'P', n))
print('[mark %s] 砲門看不穿的：%d 個（共 %d 個開口）%s' % (mark, len(bad), 2 * len(LY.ports(plan)), bad[:4]))
