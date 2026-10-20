# 船尾窗的玻璃（TASK-0753；Tim 2026-10-20「新增一種透明材質標記(玻璃) … 用來做憲法號跟餘燼號的窗戶」）
#   新圖紙 12 開窗時「玻璃不做」⇒ 這裡補：每一欄窗（不是窗格的那幾欄）在窗格那一層（船尾面縮進 setback 格）放 1 格玻璃，
#   船尾面是斜的 ⇒ 上下兩排差 1 格的地方照窗格的做法往下一排補 1 格（從斜的角度看不露縫）。
#   子作品 basecamp-frigate-constitution-01m-stern-glass（at=0,0,0），組裝件的關聯 meta material=glass（Blockside 材質表：半透明＋反光）。
# 讀：plan.json stern.windows、masks/stern/hull_windows_carve.vox.txt（開窗刻掉的格 ⇒ 每欄的船尾面 xf）、
#     組裝件現在的格（export format=list region=80..160,100..220,80..140 ⇒ 第一個參數）：玻璃只放在空格。
# 寫：masks/stern/glass.vox.txt（stampvox at=0,0,0）
import json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
GLASS = 155                       # rgb332 (4,6,3)：淡藍灰；遊戲裡照材質表 clear 透出後面
P = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))['stern']
W, YC = P['windows'], 160


def cells(path):
    out = {}
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('#') or not ln.strip():
            continue
        v = [int(t) for t in ln.split(',')]
        out[(v[0], v[1], v[2])] = v[3] if len(v) > 3 else 1
    return out


carve = cells(os.path.join(HERE, 'masks', 'stern', 'hull_windows_carve.vox.txt'))
now = cells(sys.argv[1])
xf = defaultdict(lambda: 10 ** 9)
for (x, y, z) in carve:
    xf[(y, z)] = min(xf[(y, z)], x)
sh, z0, z1 = W['sash'], W['z'][0], W['z'][1]
glass, skipped = {}, []


def put(x, y, z):
    if (x, y, z) in now:
        skipped.append((x, y, z, now[(x, y, z)]))
        return
    glass[(x, y, z)] = GLASS


for a, b in W['dy']:
    for lo, hi in ([(a, b)] if a < 0 else [(a, b), (-b, -a)]):
        for dy in range(lo, hi + 1):
            if abs(dy) in sh['dy']:
                continue
            y = YC + dy
            for z in range(z0, z1 + 1):
                if z in sh['z'] or (y, z) not in xf:
                    continue
                put(xf[(y, z)] + sh['setback'], y, z)
                if z > z0 and (y, z - 1) in xf and z - 1 not in sh['z']:
                    for x in range(xf[(y, z)] + sh['setback'] + 1, xf[(y, z - 1)] + sh['setback'] + 1):
                        put(x, y, z)
rows = sorted((k[0], k[1], k[2], c) for k, c in glass.items())
out = os.path.join(HERE, 'masks', 'stern', 'glass.vox.txt')
with open(out, 'w', encoding='utf-8', newline='') as f:
    f.write('# glass —— 船尾窗的玻璃（%d 格，at=0,0,0；色 %d；TASK-0753）\n' % (len(rows), GLASS))
    for r in rows:
        f.write('%d,%d,%d,%d\n' % r)
print('玻璃 %d 格；跳過（已經有格）%d：%s' % (len(rows), len(skipped), skipped[:8]))
