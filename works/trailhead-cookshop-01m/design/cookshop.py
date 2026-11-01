# 小飯館（TASK-1144；Tim 2026-10-31 小飯館「都要有自己的模型」）—— 加勒比海（carib）第一款。
# 工具同 crest-chocolate-01m 的 chocolate.py（restaurant ⇒ workshops ⇒ quay ⇒ ame-carib-civic-01m 的 harbour／civic ⇒ summit-carib-01m 的調色盤、Model、牆、屋頂、部件）；
#   魚的兩色借 trailhead-harbour-01m 的 town3.py（魚市），磚色借 apex-one-industry-01m 的 industry.py（磚窯）。
#   座標同 kit.py：x 臨路寬（從街上看左 → 右）、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料與設計的分界：
#   〔摘：通論〕17 世紀港口城裡做工的人多半在外面買熟食：倫敦的 cook-shop、西屬的 bodegón、伊斯坦堡的 aşçı dükkânı ——
#              臨街一個窗口或櫃台賣現成的熱食，站著吃或帶走（跟坐下來吃一頓的 ordinary、餐廳不同）；
#              加勒比海的木薯餅（cassava bread）是在三塊石頭架著的陶盤（taíno 的 burén）上烤成一大張圓餅〔摘：通論〕。
#   〔設計〕平面、窗口與撐起來的木板遮陽、櫃台上的派與碗、屋裡的保溫炭盆、後院的圓頂烤爐、殺魚桌、曬魚架、招牌（一條魚躺在一個派上）
#          —— 都沒有查到單一城的樣子；牆、屋頂、門窗照 summit-carib-01m，比餐廳（trailhead-harbour-01m restaurant）小一號。
#   遊戲：便餐那一本（Blocksail world/food.js SATISFY.fare）；菜單魚派、煎魚配木薯、鮮魚玉米燉鍋、木薯燉菜（world/recipes.js SERVE_RECIPES）。
import os, sys
from restaurant import *                                               # noqa: F401,F403  workshops ⇒ quay ＋ harbour／civic／carib 的全部、trestle_table、bench、lantern、hearth、lean_roof_posts、log_pile
from town3 import FISH, FISH_B                                         # noqa: E402  魚市的魚（銀藍、灰一點）
from industry import BRICK_R, BRICK_D, CLAY_L                          # noqa: E402  磚窯的磚（紅、深紅）、曬乾的黏土（淺褐）

PIE = THATCH_A                   # 魚派烤好的派皮（金黃）
PIE_RIM = THATCH_R               # 派皮捏起來的一圈邊（深一點）
BOWL = PLATE                     # 陶碗（白）
STEW = SOD_D                     # 碗裡、鍋裡的燉菜（深綠褐）
CASSAVA = LEATHER                # 木薯根（褐）
CASSAVA_BREAD = SACK             # 木薯餅（米白）
DOUGH = SACK                     # 揉好的麵皮


def pie(M, x, y, z, layer='body'):
    """一個魚派：直徑 6 格、派皮一層、邊一圈深色、中間一格冒氣孔。"""
    for dx in range(6):
        for dy in range(6):
            r2 = (dx - 2.5) ** 2 + (dy - 2.5) ** 2
            if r2 <= 7.5:
                M.put(layer, x + dx, y + dy, z, PIE_RIM if r2 > 4.5 else PIE, force=True)
    M.put(layer, x + 2, y + 2, z + 1, PIE_RIM, force=True)


def bowl(M, x, y, z, layer='body', full=True):
    """一只陶碗：3 × 3 × 2，裝了燉菜 ⇒ 上面一層換成燉菜色。"""
    M.box(layer, x, y, z, x + 3, y + 3, z + 2, BOWL, force=True)
    if full:
        M.put(layer, x + 1, y + 1, z + 1, STEW, force=True)


def pot(M, x, y, z, layer='body', w=6, h=5):
    """一口鐵鍋：w × w × h，鍋口一層燉菜、一根木勺斜靠。"""
    M.box(layer, x, y, z, x + w, y + w, z + h, POT)
    M.box(layer, x + 1, y + 1, z + h - 1, x + w - 1, y + w - 1, z + h, STEW, force=True)
    M.box(layer, x + w // 2, y + w // 2, z + h, x + w // 2 + 1, y + w // 2 + 1, z + h + 5, FRAME)


def bake_oven(M, cx, cy, r, h, layer='body'):
    """圓頂的烤爐（烤魚派）：毛石台座 0.6 m、上面半顆磚砌的圓頂（磚色兩種錯開）、正面（−y）一個黑的爐口。"""
    M.box(layer, cx - r - 2, cy - r - 2, 0, cx + r + 2, cy + r + 2, 6, RUBBLE)
    for x in range(cx - r, cx + r):
        for y in range(cy - r, cy + r):
            for z in range(6, 6 + h):
                if ((x + 0.5 - cx) / r) ** 2 + ((y + 0.5 - cy) / r) ** 2 + ((z - 6 + 0.5) / h) ** 2 <= 1:
                    M.put(layer, x, y, z, BRICK_D if (x // 3 + z // 2) % 3 == 0 else BRICK_R)
    M.box(layer, cx - 3, cy - r - 1, 6, cx + 3, cy - r + 3, 11, DARK, force=True)   # 爐口
    M.box(layer, cx - 2, cy - r + 1, 6, cx + 2, cy - r + 3, 7, EMBER, force=True)   # 爐口裡的炭


def buren(M, cx, cy, layer='body'):
    """烤木薯餅的陶盤（burén）：三塊石頭架著一張圓陶盤（直徑 1.2 m）、盤上一大張木薯餅、底下紅的火。"""
    for (sx, sy) in ((cx - 5, cy - 4), (cx + 3, cy - 4), (cx - 1, cy + 4)):
        M.box(layer, sx, sy, 0, sx + 2, sy + 2, 4, RUBBLE)
    for x in range(cx - 6, cx + 6):
        for y in range(cy - 6, cy + 6):
            r2 = (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2
            if r2 <= 36:
                M.put(layer, x, y, 4, CLAY_L)
            if r2 <= 16:
                M.put(layer, x, y, 5, CASSAVA_BREAD)
    M.box(layer, cx - 2, cy - 2, 0, cx + 2, cy + 2, 1, EMBER)


def roots(M, x0, y0, z, n=4, layer='body'):
    """一堆木薯根（褐，2 格粗、長短不一，堆兩層）。"""
    for i in range(n):
        L = 6 + (i * 3) % 4
        M.box(layer, x0, y0 + 2 * i, z, x0 + L, y0 + 2 * i + 2, z + 2, CASSAVA)
    for i in range(n - 1):
        M.box(layer, x0 + 1, y0 + 2 * i + 1, z + 2, x0 + 6, y0 + 2 * i + 3, z + 3, CASSAVA)


def cookshop():
    """小飯館（cookshop；西屬的 bodegón、倫敦的 cook-shop）：臨路一棟小一號的橫板牆屋子（7.2 × 4.4 m、毛石地檻、木瓦四坡頂），
    正面一個大窗口（3.6 m 寬）、櫃台從屋裡伸出牆外，上面一片撐起來的木板遮陽、兩根柱 —— 櫃台上擺魚派、一排裝好燉菜的碗、一口鍋；窗口前一條長凳；
    左邊一扇門（兩級台階）；屋裡做派的長桌（麵皮、魚）、保溫的炭盆上兩口燉鍋、後牆的碗架、一籃魚；右前角吊招牌（一條魚躺在一個派上）。
    後院木柵圍起來：茅草單坡的爐棚（圓頂磚砌烤爐、烤木薯餅的陶盤 burén）、殺魚桌、曬魚架、一堆木薯根、柴堆、水桶。"""
    X, Y, Z = 100, 140, 72
    M = Model((X, Y, Z))
    X0, Y0, X1, Y1 = 14, 22, 86, 66                                    # 屋 7.2 × 4.4 m
    R, t, fl = (X0, Y0, X1, Y1), 2, 4
    rubble_walls(M, R, 0, fl, 4, salt=11441)
    M.box('body', X0, Y0, fl - 1, X1, Y1, fl, FLOOR)
    board_walls(M, R, fl, 32, t)
    # ── 正面的窗口（x 32..68、地板上 1.0～2.4 m）、伸出牆外的櫃台、撐起來的木板遮陽 ──
    HX0, HX1, HZ0, HZ1 = 32, 68, fl + 10, fl + 24
    M.clear(HX0, Y0, HZ0, HX1, Y0 + t, HZ1, 'body')
    M.box('body', HX0, Y0, HZ0 - 1, HX1, Y0 + 8, HZ0, FLOOR, force=True)   # 櫃台面（牆裡 6 格深）
    M.box('body', HX0, Y0 + t, fl, HX1, Y0 + 8, HZ0 - 1, FRAME)           # 櫃台的檯身（屋裡那一側）
    M.box('gallery', HX0, Y0 - 3, HZ0 - 1, HX1, Y0, HZ0, FLOOR)           # 伸出牆外 0.3 m 的檯沿
    for x in (HX0, HX1 - 2):                                           # 檯沿底下兩塊托木
        M.box('gallery', x, Y0 - 3, HZ0 - 4, x + 2, Y0, HZ0 - 1, FRAME)
    M.box('gallery', HX0 - 2, Y0 - 9, HZ1 + 1, HX1 + 2, Y0, HZ1 + 2, SHUT)   # 撐起來的遮陽板（窗口白天的木板窗）
    for x in (HX0 - 2, HX1):                                           # 前面兩根撐柱
        M.box('gallery', x, Y0 - 9, 0, x + 2, Y0 - 7, HZ1 + 1, FRAME)
    for i, x in enumerate((HX0 + 2, HX0 + 10, HX0 + 18)):              # 檯上：三個魚派
        pie(M, x, Y0 - 2, HZ0, layer='gallery' if i == 0 else 'body')
    for x in range(HX0 + 26, HX1 - 12, 4):                             # 一排裝好燉菜的碗
        bowl(M, x, Y0 + 1, HZ0)
    pot(M, HX1 - 9, Y0 + 1, HZ0)                                       # 一口鍋（燉菜）
    bench(M, HX0 + 2, HX1 - 2, 4, 8, layer='gallery')                  # 窗口前的長凳（客人等、坐著吃）
    # ── 門窗 ──
    put_part(M, 'door-plank', '前-門', 'front', R, 22, fl, t)
    steps(M, 16, 28, Y0, 2, 2, 3, back=False)
    M.anchor('door', 22, Y0 - 1, fl)
    for face, nm in (('left', '左'), ('right', '右')):
        put_part(M, 'window-board', '%s-窗' % nm, face, R, 44, fl + 9, t)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 30, fl, t)
    # ── 屋頂 ──
    shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 32, 'p': 0.9, 'over': (4, 4, 4, 4)}], salt=11442)
    # ── 屋裡：做派的長桌（麵皮、魚）；保溫的炭盆＋兩口燉鍋；後牆的碗架；一籃魚 ──
    trestle_table(M, 20, 44, 46, 54, fl + 8)
    M.box('body', 22, 47, fl + 9, 32, 53, fl + 10, DOUGH, force=True)  # 擀開的麵皮
    pie(M, 24, 47, fl + 10)                                            # 包到一半的派
    for x in (35, 39):                                                 # 兩條待包的魚
        M.box('body', x, 47, fl + 9, x + 2, 53, fl + 10, FISH, force=True)
    M.box('body', 62, 50, fl, 80, 60, fl + 6, IRON)                    # 炭盆（長方的鐵盆、腳）
    M.box('body', 63, 51, fl + 6, 79, 59, fl + 7, EMBER, force=True)
    pot(M, 64, 52, fl + 7)
    pot(M, 72, 52, fl + 7)
    M.anchor('smoke', 71, 55, 40)                                      # 炭盆的煙從屋頂冒出去
    for z in (fl + 16, fl + 22):                                       # 後牆的碗架（兩層板、一排疊起來的碗）
        M.box('body', 46, Y1 - t - 4, z, 60, Y1 - t, z + 1, FLOOR)
        for x in range(47, 58, 4):
            bowl(M, x, Y1 - t - 3, z + 1, full=False)
    M.box('body', 50, 56, fl, 58, 62, fl + 4, THATCH_B)                # 一籃魚（籃身、上面一層魚）
    for x in range(51, 57, 2):
        M.box('body', x, 57, fl + 4, x + 2, 61, fl + 5, FISH_B if x % 4 == 1 else FISH, force=True)
    # ── 招牌：右前角一根柱、橫臂、吊著的一塊板（一條魚躺在一個派上）──
    M.box('body', 95, 4, 0, 97, 6, 42, FRAME)
    M.box('body', 82, 4, 40, 97, 6, 42, FRAME)
    for x in (84, 93):
        M.box('body', x, 4, 36, x + 1, 5, 40, IRON)
    for x in range(83, 95):
        for z in range(26, 36):
            M.put('body', x, 4, z, FRAME if x in (83, 94) or z in (26, 35) else SHUT)
    for x in range(85, 93):                                            # 派（底下半圓：派皮）
        for z in range(27, 31):
            if (x - 88.5) ** 2 / 16 + (z - 27) ** 2 / 12 <= 1:
                M.put('body', x, 4, z, PIE if z < 30 else PIE_RIM)
    for x in range(85, 92):                                            # 派上躺著的一條魚（魚身＋尾巴）
        M.put('body', x, 4, 31, FISH)
    M.put('body', 92, 4, 32, FISH)
    M.put('body', 92, 4, 30, FISH)
    M.put('body', 86, 4, 32, FISH_B)
    M.anchor('sign', 88, 4, 30)
    # ── 後院：木柵；茅草單坡的爐棚（圓頂烤爐、burén）；殺魚桌；曬魚架；木薯根、柴堆、水桶 ──
    yb = Y - 2
    palisade(M, [(X0, Y1), (2, Y1), (2, yb), (X - 2, yb), (X - 2, Y1), (X1 - 1, Y1)], gap={(x, yb) for x in range(44, 56)})
    K = (54, 92, 96, 128)                                              # 爐棚 4.2 × 3.6 m
    M.box('body', K[0], K[1], 0, K[2], K[3], 1, EARTH_W)
    lean_roof_posts(M, K[0] - 2, K[1] - 2, K[2] + 2, K[3] + 2, 34, 0.3, 'back', thatch_color,
                    [(K[0], K[1]), (K[2] - 2, K[1]), (K[0], K[3] - 2), (K[2] - 2, K[3] - 2)], salt=11443)
    bake_oven(M, 82, 116, 9, 14)                                       # 圓頂的烤爐（爐口朝前）
    buren(M, 64, 112)                                                  # 烤木薯餅的陶盤
    trestle_table(M, 10, 34, 74, 82, 8)                                # 殺魚桌
    for x in range(12, 30, 4):
        M.box('body', x, 76, 9, x + 2, 81, 10, FISH if (x // 4) % 2 else FISH_B, force=True)
    M.box('body', 30, 76, 9, 31, 79, 11, IRON, force=True)            # 刀
    for (x0, x1) in ((8, 40),):                                        # 曬魚架（兩根柱＋兩道橫桿，剖開的魚往下掛）
        for px in (x0, x1 - 2):
            M.box('body', px, 100, 0, px + 2, 102, 24, FRAME)
        for zr in (14, 22):
            M.box('body', x0, 100, zr, x1, 102, zr + 1, FRAME)
            for x in range(x0 + 3, x1 - 3, 3):
                M.box('body', x, 100, zr - 5, x + 2, 101, zr, FISH if (x // 3 + zr) % 4 else FISH_B)
    roots(M, 10, 118, 0)                                               # 一堆木薯根
    log_pile(M, 20, 44, 124, 2, 4)                                     # 柴堆
    M.models += [{'name': '水桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [44, 84, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-門', (28.5, Y0, 24.5))
    M.anchor('lot-0', 0, 0, 0)
    # 工作點（BUILDING_SPEC §5；服務 ＝ 菜單最多人的那道 魚派 jobs 3 × 二級 mult 2 ＝ 6 ＋ 1 ＝ 7）：
    #   a 窗口櫃台後（兩點）、b 做派的長桌、c 炭盆前；後院 d 烤爐前、e burén 旁、f 殺魚桌
    for nm, at, to in (('a1', (40, Y0 + 11, fl), (40, Y0 + 2, HZ0)), ('a2', (58, Y0 + 11, fl), (58, Y0 + 2, HZ0)),
                       ('b1', (32, 57, fl), (32, 50, fl + 9)), ('c1', (70, 46, fl), (70, 54, fl + 7)),
                       ('d1', (82, 100, 1), (82, 108, 8)), ('e1', (64, 100, 1), (64, 112, 5)), ('f1', (22, 86, 0), (22, 78, 9))):
        M.anchor('work-' + nm, *at)
        M.anchor('work-%s-to' % nm, *to)
    return {'key': 'carib-cookshop', 'style': 'carib',
            'title': '加勒比海的小飯館（bodegón／cook-shop：小一號的橫板牆屋子、臨街大窗口與伸出牆外的櫃台、撐起來的木板遮陽；櫃台上的魚派與燉菜碗；招牌畫一條魚躺在派上；後院圓頂烤爐、烤木薯餅的陶盤、殺魚桌、曬魚架）',
            'use': 'cookshop', 'lot': (10, 14), 'M': M, 'layers': {'body': '屋、擺設與後院', 'gallery': '窗口、遮陽與長凳', 'roof': '屋頂'}}


ALL = [cookshop]
