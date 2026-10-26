# 餐廳（TASK-0998；Tim 2026-10-26「另外試著加入餐廳建築吧 GO（包含建築模型 可以先做加勒比海風格）」）—— 加勒比海（carib）第一款。
# 工具同 town3.py／workshops.py（quay ⇒ ame-carib-civic-01m 的 harbour／civic ⇒ summit-carib-01m 的調色盤、Model、牆、屋頂、部件）；
#   版型照 summit 的酒館（summit-carib-01m/design/public.py tavern：橫板牆、寬前廊、木瓦頂往前廊放緩）。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料：作品 references/README.md 餐廳那一節；查不到的都寫「設計」。
import os, sys, math
from workshops import *                                                # noqa: F401,F403  quay ＋ harbour／civic／carib 的全部、roof_posts
from townpub import MEAT                                               # noqa: E402  肉鋪掛的肉（深紅）
from houses import lean_roof_posts, hearth                             # noqa: E402

POT = DARK                       # 鐵鍋
PLATE = 255                      # 桌上的盤（白：同 TRIM）
FIRE = EMBER


def table_set(M, x0, x1, y0, y1, layer='body', z=8, plates=True):
    """一張長桌（架腳）、兩邊長凳；桌上每隔 6 格一個盤（白）＋盤中一塊肉（深紅）。"""
    trestle_table(M, x0, x1, y0, y1, z, layer=layer)
    bench(M, x0, x1, y0 - 4, y0 - 1, layer=layer)
    bench(M, x0, x1, y1 + 1, y1 + 4, layer=layer)
    if plates:
        for x in range(x0 + 2, x1 - 2, 6):
            for y in (y0 + 1, y1 - 3):
                M.box(layer, x, y, z + 1, x + 3, y + 2, z + 2, PLATE, force=True)
                M.put(layer, x + 1, y, z + 2, MEAT)


def meat_rail(M, x0, x1, y, z, n, layer='body'):
    """廚房裡吊肉的橫桿：x0..x1 一根木桿（z），下面掛 n 塊肉（鐵鉤＋深紅的一塊）。"""
    M.box(layer, x0, y, z, x1, y + 1, z + 1, FRAME, force=True)
    step = (x1 - x0) // (n + 1)
    for i in range(n):
        x = x0 + step * (i + 1)
        M.put(layer, x, y, z - 1, IRON)
        M.box(layer, x - 1, y, z - 6, x + 2, y + 1, z - 1, MEAT, force=True)


# ─────────────────────────────── 餐廳 10 × 14 m ───────────────────────────────
def restaurant():
    """餐廳（restaurant；加勒比海的 ordinary／cook-shop）：臨路一棟橫板牆的食堂（8.8 × 5.4 m、毛石地檻、木瓦四坡頂往前放緩蓋住前廊），
    前廊擺兩張長桌（盤裡有肉）、廊下的柱；食堂裡兩張長桌與長凳、後牆的出菜檯與碗盤架；吊一塊畫著鍋的招牌。
    後院用木柵圍起來，獨立的廚房棚（茅草單坡頂）：石砌的灶（叉柱吊一口鍋、紅的火、煙口）、吊肉的橫桿、切肉的砧板桌；
    棚外一座燻肉架（boucan）與營火、水桶、柴堆。
    - 照什麼：17 世紀的港口城裡有專門賣飯的 ordinary 與 cook-shop（皇家港、和平港這類港口；酒館以喝為主、ordinary 以一頓飯為主）〔摘：通論，沒查到單一城的平面〕；
      熱帶的房子把廚房蓋在主屋外、獨立一間（怕熱、怕火）〔摘：通論〕；燻肉架 boucan 是加勒比海燻肉的木格柵（buccaneer 這個字就是從這裡來）〔摘〕。
      平面、桌數、灶的樣子、招牌都是設計；版型照 summit 的酒館。
    - 遊戲：服務建築、只賣吃的（外食那一本）；菜單有指名牧場肉的烤肉大餐、胡椒燉鍋（Blocksail world/recipes.js SERVE_RECIPES）。"""
    X, Y, Z = 100, 140, 72
    M = Model((X, Y, Z))
    X0, Y0, X1, Y1 = 6, 34, 94, 88                                     # 食堂 8.8 × 5.4 m
    R, t, fl = (X0, Y0, X1, Y1), 2, 4
    GY0 = 10                                                           # 前廊的前緣
    rubble_walls(M, R, 0, fl, 4, salt=9981)
    M.box('body', X0, Y0, fl - 1, X1, Y1, fl, FLOOR)
    board_walls(M, R, fl, 34, t)
    piers(M, (X0, GY0, X1, Y0), fl - 1, step=22)
    M.box('gallery', X0, GY0, fl - 1, X1, Y0, fl, FLOOR)
    put_part(M, 'door-double', '前-門', 'front', R, 50, fl, t)
    for i, cx in enumerate((22, 78)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, fl + 9, t)
    for face, nm in (('left', '左'), ('right', '右')):
        put_part(M, 'window-board', '%s-窗' % nm, face, R, 61, fl + 9, t)
    put_part(M, 'door-plank', '後-門（往廚房）', 'back', R, 72, fl, t)
    steps(M, 40, 60, GY0, 1, 2, 4, back=False)
    M.anchor('door', 50, Y0 - 1, fl)
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 34, 'p': 0.9, 'over': (4, 4, 24, 4), 'kick': {'front': 0.42}}], salt=9982)
    gallery_posts(M, (X0, 28, 70, X1 - 2), GY0, fl, top)
    # 前廊：兩張長桌（沿 x），盤裡有肉
    table_set(M, 10, 34, 20, 26, layer='gallery', z=fl + 8)
    table_set(M, 66, 90, 20, 26, layer='gallery', z=fl + 8)
    # 食堂裡：兩張長桌（沿 y）、後牆的出菜檯（及腰的木檯）與碗盤架
    for (a, b) in ((16, 22), (38, 44)):
        trestle_table(M, a, b, 44, 70, fl + 8)
        bench(M, a - 4, a - 1, 44, 70, fl + 4)
        bench(M, b + 1, b + 4, 44, 70, fl + 4)
        for y in range(46, 68, 6):
            M.box('body', a + 1, y, fl + 9, a + 3, y + 3, fl + 10, PLATE, force=True)
            M.box('body', b - 3, y, fl + 9, b - 1, y + 3, fl + 10, PLATE, force=True)
    M.box('body', 56, 76, fl, 90, Y1 - t, fl + 10, FRAME)              # 出菜檯（後門左邊）
    M.box('body', 56, 76, fl + 10, 90, Y1 - t, fl + 11, FLOOR)
    for z in (fl + 18, fl + 24):                                       # 碗盤架（後牆上兩層板、架上一排白盤）
        M.box('body', 58, Y1 - t - 3, z, 66, Y1 - t, z + 1, FLOOR)
        for x in range(58, 66, 2):
            M.put('body', x, Y1 - t - 2, z + 1, PLATE)
            M.put('body', x, Y1 - t - 2, z + 2, PLATE)
    M.box('body', 70, 78, fl + 11, 74, 82, fl + 14, POT)               # 檯上一口鍋
    # 招牌：右前角一根柱、橫臂、吊著的一塊板（畫一口鍋）
    M.box('body', 95, 4, 0, 97, 6, 42, FRAME)
    M.box('body', 82, 4, 40, 97, 6, 42, FRAME)
    for x in (84, 93):
        M.box('body', x, 4, 36, x + 1, 5, 40, IRON)
    for x in range(83, 95):
        for z in range(26, 36):
            M.put('body', x, 4, z, FRAME if x in (83, 94) or z in (26, 35) else SHUT)
    for x in range(86, 92):                                            # 鍋身
        for z in range(28, 32):
            if (x, z) not in ((86, 28), (91, 28)):
                M.put('body', x, 4, z, DARK)
    M.box('body', 85, 4, 32, 93, 5, 33, DARK)                          # 鍋沿
    for (x, z) in ((87, 33), (88, 34), (90, 33), (89, 34)):            # 冒的熱氣
        M.put('body', x, 4, z, TRIM)
    M.anchor('sign', 88, 4, 30)
    # 後院：木柵；獨立的廚房棚（茅草單坡、低的那邊朝後）、石灶、吊肉的橫桿、砧板桌
    palisade(M, [(X0, Y1), (2, Y1), (2, 138), (98, 138), (98, Y1), (X1 - 1, Y1)], gap={(x, 138) for x in range(12, 24)})
    K = (50, 98, 94, 130)                                              # 廚房棚 4.4 × 3.2 m
    M.box('body', K[0], K[1], 0, K[2], K[3], 1, EARTH_W)
    lean_roof_posts(M, K[0] - 2, K[1] - 2, K[2] + 2, K[3] + 2, 32, 0.3, 'back', thatch_color,
                    [(K[0], K[1]), (K[2] - 2, K[1]), (K[0], K[3] - 2), (K[2] - 2, K[3] - 2)], salt=9983)
    hearth(M, 76, 116, 90, 128, 8)                                     # 石灶（叉柱吊一口鍋）
    M.box('body', 80, 118, 2, 86, 124, 3, FIRE, force=True)            # 灶裡的火
    M.anchor('smoke', 83, 122, 20)
    meat_rail(M, K[0] + 4, K[0] + 22, 112, 24, 4)                     # 吊肉的橫桿（兩端架在柱頂的橫木上）
    for x in (K[0] + 2, K[0] + 22):
        M.box('body', x, 112, 0, x + 2, 113, 25, FRAME)
    trestle_table(M, 54, 72, 100, 106, 8)                              # 砧板桌
    M.box('body', 60, 101, 9, 66, 105, 11, LOG)                        # 砧板
    M.box('body', 67, 102, 9, 70, 104, 10, MEAT, force=True)
    M.box('body', 61, 102, 11, 62, 103, 13, IRON, force=True)          # 剁肉刀立在砧板上
    # 棚外：燻肉架（boucan）壓在營火上、柴堆、水桶
    log_pile(M, 6, 30, 120, 3, 4)                                     # 柴堆（四根一排 ⇒ 進深 16 格）
    M.models += [{'name': '燻肉架', 'source': 'summit-rocher-01m-boucan', 'at': [26, 104, 0], 'pivot': [16, 10, 0], 'meta': {}},
                 {'name': '營火-燻肉架', 'source': 'summit-rocher-01m-campfire', 'at': [26, 104, 0], 'pivot': [6.5, 6.5, 0], 'meta': {'kind': 'light', 'light': 'fire'}},
                 {'name': '水桶-廚房', 'source': 'summit-rocher-01m-barrel', 'at': [44, 120, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-廊', 'source': 'summit-rocher-01m-barrel', 'at': [50, 15, fl], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-門', (36.5, Y0, 24.5))
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'restaurant', 'title': '餐廳（加勒比海的 ordinary：橫板牆的食堂、寬前廊擺長桌、吊招牌畫一口鍋、木瓦四坡頂；後院獨立的茅草廚房棚、石灶、吊肉、燻肉架 boucan）',
            'use': 'restaurant', 'lot': (10, 14), 'M': M, 'style': 'carib', 'layers': {'body': '食堂、廚房與擺設', 'gallery': '前廊', 'roof': '屋頂'}}


ALL = [restaurant]
