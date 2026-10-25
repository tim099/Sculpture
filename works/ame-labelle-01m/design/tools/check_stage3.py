# 階段三（TASK-0592）讀數：作品匯出 vs（船殼清單 − 刻 ＋ 換色）的結果帳；砲門與船尾追擊砲門從「作品」量開了沒
#   用法：python -I -X utf8 tools/check_stage3.py <design> [mark=砲門:end]
#   · 作品那一側一律從 CLI 匯出讀；砲門開了沒也拿作品的格子量（⛔ 不拿 draft_ports 自己的陣列當作品）
import os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
mark = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('mark=')), '砲門:end')
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
import lines as HL
import layout as LY
import draft_ports as DP
from wio import export_list, load_lists, key

W = export_list('ame-labelle-01m', mark)
H = load_lists(os.path.join(design, 'masks', 'hull'))
carve = np.loadtxt(os.path.join(design, 'masks', 'ports', 'carve.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
paint = np.loadtxt(os.path.join(design, 'masks', 'ports', 'paint.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
want = dict(zip(key(H).tolist(), H[:, 3].tolist()))
for k in key(carve).tolist():
    want.pop(k, None)
for k, c in zip(key(paint).tolist(), paint[:, 3].tolist()):
    want[k] = c
got = dict(zip(key(W).tolist(), W[:, 3].tolist()))
miss = len(set(want) - set(got))
extra = len(set(got) - set(want))
cdiff = sum(1 for k in set(want) & set(got) if want[k] != got[k])
print('結果帳：作品 %d、設計（船殼 − 刻 ＋ 換色）%d、缺 %d、多 %d、色差 %d' % (len(got), len(want), miss, extra, cdiff))

plan = HL.load_plan(design)
L = HL.Lines(plan)
YC = L.YC
occ = set(key(W).tolist())
shut = []
for p in LY.ports(plan):
    for side in (1, -1):
        n = 0
        for x in range(p['x0'], p['x1'] + 1):
            for z in range(p['z0'], p['z1'] + 1):
                for dy in range(6, 70):
                    y = YC + side * dy
                    if ((x * 1000 + y) * 1000 + z) in occ:
                        n += 1
        if n:
            shut.append((p['deck'], p['i'], 'S' if side > 0 else 'P', n))
print('砲門（作品量）：%d 個開口裡還有實心的 %d 個 %s' % (len(LY.ports(plan)) * 2, len(shut), shut[:6]))
# 船尾追擊砲門：窗框裡、從船尾往前到 x 170 為止的格 ＝ 0（整段刻穿 ⇒ 看得進艙裡）
st = []
for w in DP.stern_windows(plan, YC):
    if w['kind'] != 'port':
        continue
    n = 0
    for y in range(w['y0'], w['y1'] + 1):
        for z in range(w['z0'], w['z1'] + 1):
            xs = [x for x in range(80, 170) if ((x * 1000 + y) * 1000 + z) in occ]
            # 從最後面那一格往前：船尾面那一段牆要整段沒有（第一個實心若在 x ≥ 150 ＝ 已經是艙裡別的東西，不算）
            if xs and xs[0] < 150:
                n += 1
    st.append((w['y0'], n))
print('船尾追擊砲門（作品量）：', st)
