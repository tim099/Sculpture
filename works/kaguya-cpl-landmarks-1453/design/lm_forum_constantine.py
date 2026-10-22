# 君士坦丁廣場（Forum of Constantine，Plakotos「石板地」）1453：圓形的大理石鋪面、正中是君士坦丁紀念柱 ——
#   1203 年 8 月的大火把有頂的柱廊和「大部分廣場本身」夷平（Madden），之後沒有重建的紀錄 ⇒ 1453 年 ＝ 石板空地＋柱、四周的斷垣：
#   東西兩座紀念拱門只剩殘墩（Mese 從中間穿過）、柱廊剩幾段（後牆、斷柱、幾塊過梁）、碎石堆。
#   柱子照 kaguya-cpl-column-constantine-1453（lm_column_constantine.py）的數字，在這裡用 0.4 m 的格重蓋一次：
#     以前柱子是一塊 12 × 12 m 的特殊建築、廣場是 140 × 140 m 的手擺廣場，兩塊各自整平 ⇒ 廣場的鋪面比柱子的地塊高 2.4 m、五級台階整個埋在鋪面下（2026-10-23 遊戲裡拍到）⇒ 併成一塊。
#   ⛔ 不做：Atik Ali Paşa 清真寺（1496，在圓裡西側）、Çemberlitaş 浴場（1584）、1779 年包住柱基的鄂圖曼石殼、元老院（在圓外北側、1453 年的樣子查不到）、柱腳的聖君士坦丁小堂（尺寸與 1453 年在不在都查不到）。
#   研究整理：scratchpad/cpl/research_batch3.md §1；柱心 OSM way 1153684927（41.008563, 28.971299）；門軸 95°／275°（Milion → 柱心 → 狄奧多西廣場）。
import math
import random
import byz, columns
from byz import MARBLE, PORPHYRY, BRONZE, GOLD, STONE, BANDED, BRICK

KEY = 'forum-constantine'
TITLE = '君士坦丁廣場 1453（Forum of Constantine：石板圓場、紀念柱、拱門殘墩、柱廊殘段）'
TITLE_SHORT = '君士坦丁廣場 1453'
MPV = 0.4
W, D, H = 140.0, 140.0, 42.0
META = {'kind': 'building', 'use': 'forum-constantine', 'style': 'roman', 'lot': '140,140', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('paving', 1, '石板圓場（Prokonnesos 大理石）'), ('column', 2, '君士坦丁紀念柱（台階、基座、斑岩柱身、砌頂）'), ('cross', 3, '十字架'),
         ('ruins', 4, '拱門殘墩、柱廊殘段、碎石'))
PROV = {
    '圓形、直徑約 140 m（柱東約 70 m 的基礎若屬拱門）；東西兩座大理石拱門；兩層柱廊': '參考資料：Zosimos 2.30.4；Kaldellis 2016（GRBS）；Bauer 1996',
    '鋪面 Prokonnesos 大理石板（1929–30 發掘；別名 Plakotos）': '參考資料：Kaldellis 2016（引 Mamboury、Vett）；Gyllius III.3',
    '1203 年大火：有頂柱廊燒光、廣場周邊與大部分廣場本身被夷平；1204 後沒有重建紀錄': '參考資料：Madden 1991–92（引 Choniates）',
    '柱：五級台階、白大理石基座、八節斑岩柱身、Manuel I 的砌頂與十字架': '同 kaguya-cpl-column-constantine-1453 的 PROV',
    '殘墩、柱廊殘段的位置、長度、高度；碎石': '設計決定（1453 年殘存多少查不到）',
}


def portico(M, rnd, a0, a1, r_col, r_wall, lay, two=False):
    """一段柱廊殘段：a0 → a1（度，模型中心看出去、從 +x 往 +y）；後牆在 r_wall、柱在 r_col；柱一根一根斷在不同高度。"""
    cx, cy = W / 2, D / 2
    ang = (byz.np.degrees(byz.np.arctan2(M.Y - cy, M.X - cx)) + 360) % 360
    r = byz.np.hypot(M.X - cx, M.Y - cy)
    inside = (ang >= a0) & (ang < a1) if a0 < a1 else (ang >= a0) | (ang < a1)
    # 後牆：斷斷續續，高 2–6 m
    n = max(1, int((a1 - a0) % 360 / 3.0))
    for k in range(n):
        b0 = a0 + k * 3.0; b1 = b0 + 3.0
        hw = 1.0 + rnd.random() * 5.0
        seg = ((ang >= b0 % 360) & (ang < b1 % 360)) if (b0 % 360) < (b1 % 360) else ((ang >= b0 % 360) | (ang < b1 % 360))
        M.add(seg & (r >= r_wall - 1.4) & (r < r_wall) & (M.Z < hw), BANDED, lay)
    # 柱：沿弧每 3.8 m 一根
    L = math.radians((a1 - a0) % 360) * r_col
    nc = int(L / 3.8)
    tops = []
    for k in range(nc + 1):
        a = math.radians(a0 + ((a1 - a0) % 360) * k / max(1, nc))
        x, y = cx + r_col * math.cos(a), cy + r_col * math.sin(a)
        roll = rnd.random()
        h = 7.0 if roll > 0.55 else (0.6 + rnd.random() * 3.5 if roll > 0.15 else 0.0)
        M.add(M.box(x - 0.7, x + 0.7, y - 0.7, y + 0.7, 0, 0.6), MARBLE, lay)                       # 柱礎
        if h > 0:
            M.add(M.cyl(x, y, 0.45, 0.6, 0.6 + h), MARBLE, lay)
        if h >= 7.0:
            M.add(M.box(x - 0.7, x + 0.7, y - 0.7, y + 0.7, 7.6, 8.4), MARBLE, lay)                   # 柱頭
            if two:
                M.add(M.cyl(x, y, 0.35, 8.4, 14.0), MARBLE, lay)
                M.add(M.box(x - 0.55, x + 0.55, y - 0.55, y + 0.55, 14.0, 14.6), MARBLE, lay)
        tops.append((x, y, h))
    for (x0, y0, h0), (x1, y1, h1) in zip(tops, tops[1:]):                                           # 相鄰兩根都立著 ⇒ 過梁還在
        if h0 >= 7.0 and h1 >= 7.0:
            t = byz.np.clip(((M.X - x0) * (x1 - x0) + (M.Y - y0) * (y1 - y0)) / ((x1 - x0) ** 2 + (y1 - y0) ** 2), 0, 1)
            d = byz.np.hypot(M.X - (x0 + t * (x1 - x0)), M.Y - (y0 + t * (y1 - y0)))
            M.add((d < 0.6) & (M.Z >= 8.4) & (M.Z < 9.4), MARBLE, lay)
    # 倒下的柱段、碎石
    for k in range(int(nc * 0.6)):
        a = math.radians(a0 + ((a1 - a0) % 360) * rnd.random())
        rr = r_col - 2.0 - rnd.random() * 5.0
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        s = 0.5 + rnd.random() * 1.2
        M.add(M.dome(x, y, 0.4, s, s * 0.5), MARBLE if k % 2 else STONE, lay)


def gate(M, x0, x1, hl, hr, lay):
    """紀念拱門的殘墩（Mese 從中間穿過 ⇒ 開口 12 m）：南北兩墩、墩頂留一截起拱。"""
    cy = D / 2
    for (y0, y1, h, s) in ((cy + 6.0, cy + 12.0, hl, -1), (cy - 12.0, cy - 6.0, hr, 1)):
        M.add(M.box(x0, x1, y0, y1, 0, h), MARBLE, lay)
        M.add(M.box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 0, 1.0), MARBLE, lay)                     # 墩基
        yy = y0 if s < 0 else y1                                                                      # 起拱：朝開口那一邊斜出去一截
        M.add(M.box(x0, x1, min(yy, yy + s * 2.0), max(yy, yy + s * 2.0), h - 1.6, h) & ((M.Z - (h - 1.6)) >= byz.np.abs(M.Y - yy) * 0.6), MARBLE, lay)


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.2)
    rnd = random.Random(330)
    cx, cy = W / 2, D / 2
    r = byz.np.hypot(M.X - cx, M.Y - cy)
    # 石板圓場：每 3.2 m 一道板縫（灰的）
    seam = ((M.X % 3.2) < MPV) | ((M.Y % 3.2) < MPV)
    M.add((r < 69.6) & (M.Z < 0.4) & ~seam, MARBLE, 1)
    M.add((r < 69.6) & (M.Z < 0.4) & seam, STONE, 1)
    # 紀念柱（同 lm_column_constantine.py）
    steps = [[11.25, 0.4], [10.5, 0.4], [9.8, 0.4], [9.05, 0.4], [8.35, 0.4]]
    C = {'steps': steps, 'pedestal': {'w': 3.7, 'h': 5.5, 'mat': MARBLE, 'cornice': 0.25}, 'base': {'d': 3.3, 'h': 0.6},
         'shaft': {'d0': 2.9, 'd1': 2.9, 'h': 8 * 3.28, 'drums': 8, 'ring_h': 0.4, 'mat': PORPHYRY, 'ring_mat': BRONZE},
         'capital': {'w': 3.0, 'h': 2.7, 'mat': MARBLE}}
    ztop = columns.column(M, cx, cy, C, lay=2)
    M.add(M.box(cx - 0.2, cx + 0.2, cy - 0.2, cy + 0.2, ztop, ztop + 3.0), GOLD, 3)
    M.add(M.box(cx - 0.8, cx + 0.8, cy - 0.2, cy + 0.2, ztop + 1.86, ztop + 2.26), GOLD, 3)
    # 東、西拱門殘墩（模型 +x ＝ 往東，Mese 方位 95°）
    gate(M, W - 7.0, W - 1.0, 9.0, 7.2, 4)
    gate(M, 1.0, 7.0, 5.4, 6.6, 4)
    # 柱廊殘段：四段（避開兩座門）；東南那段（−y ＝ 南；rot 95 ⇒ +x 往東、+y 往北）兩層還看得出來
    for a0, a1, two in ((28, 62, False), (112, 146, False), (204, 234, False), (292, 326, True)):
        portico(M, rnd, a0, a1, 63.0, 69.6, 4, two)
    G, L = M.finish(shell_m=1.2, seed=330, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'top': M.cell(cx, cy, ztop + 2.8)}
    return G, L, anchors, {'砌頂頂（m）': round(ztop, 2), '十字架頂（m）': round(ztop + 3.0, 2)}
