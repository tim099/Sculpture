# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/check_parts.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 結果帳（kaguya 自己寫的通用版）：作品（引擎匯出 format=list links=none）↔ 設計清單，逐格比位置與顏色。
#   用法：python -I -X utf8 tools/check_parts.py <design> <作品>=<清單或資料夾>[+<清單…>] …
#   例：tools/check_parts.py . crest-001-susquehanna-01m=masks/build/hull_01.vox.txt+…  crest-001-susquehanna-01m-armor=masks/build/armor.vox.txt
#   · 清單寫資料夾 ⇒ 那個資料夾裡全部 *.vox.txt。反向對照：--probe=<作品>:<dx> ⇒ 設計那一側整份往 x 推 dx 再比（要報缺／多，不是 0）。
import os, sys, json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
sys.path.insert(0, design)
import mio

probe = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe=')), None)


def load(p):
    A = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    return {(x, y, z): c for x, y, z, c in A.tolist()}


out = {}
bad = 0
for spec in [a for a in sys.argv[2:] if not a.startswith('--')]:
    work, lists = spec.split('=', 1)
    want = {}
    for item in lists.split('+'):
        p = os.path.join(design, item)
        files = [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.endswith('.vox.txt')] if os.path.isdir(p) else [p]
        for f in files:
            want.update(load(f))
    if probe and probe.split(':')[0] == work:
        dx = int(probe.split(':')[1])
        want = {(x + dx, y, z): c for (x, y, z), c in want.items()}
    A = mio.export_list(work, 'none')
    have = {(x, y, z): c for x, y, z, c in A.tolist()}
    miss = sum(1 for k in want if k not in have)
    extra = sum(1 for k in have if k not in want)
    diff = sum(1 for k, c in want.items() if k in have and have[k] != c)
    out[work] = {'design': len(want), 'work': len(have), 'missing': miss, 'extra': extra, 'color_diff': diff}
    bad += miss + extra + diff
print(json.dumps(out, ensure_ascii=False))
print('結果帳：' + ('缺 0、多 0、色差 0' if not bad else '有差 %d' % bad))
