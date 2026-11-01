# 巧克力館（TASK-1143；Tim 2026-10-31「另外開單(都要有自己的模型)」）—— 加勒比海（carib）第一款。
# 工具同 ridge-two-inn-01m 的 inn.py（restaurant ⇒ workshops ⇒ quay ⇒ ame-carib-civic-01m 的 harbour／civic ⇒ summit-carib-01m 的調色盤、Model、牆、屋頂、部件）。
#   座標同 kit.py：x 臨路寬（從街上看左 → 右）、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料與設計的分界：
#   〔摘：通論〕17 世紀西屬美洲與西班牙喝巧克力：可可豆烘過、在加熱的石磨台（metate）上用石棍（mano）磨成膏、加糖與香料，
#              在銅壺（chocolatera）裡加熱水、用木攪棒（molinillo）攪出泡沫，倒進小杯（jícara）喝；倫敦 1657 年起有專門賣巧克力的店（chocolate house）。
#   〔設計〕平面、桌數、櫃台、招牌（一杯冒熱氣的巧克力）、後院曬可可豆的架子 —— 都沒有查到單一城的樣子；版型照 trailhead 的餐廳。
#   遊戲：社交那一本（Blocksail world/food.js SATISFY.social）；菜單加糖的、不加糖的熱巧克力（world/recipes.js cocoa-sweet、cocoa-plain）。
import os, sys
from restaurant import *                                               # noqa: F401,F403  workshops ⇒ quay ＋ harbour／civic／carib 的全部、table_set、trestle_table、bench、lantern、hearth
from workshops2 import COPPER                                          # noqa: E402  蒸餾器的銅（偏紅的褐）

CHOC = FRAME                     # 杯裡、壺口的巧克力（深褐）
CUP = SACK                       # 陶杯（米白）
BEAN = LEATHER                   # 可可豆（褐）
MAT = THATCH_A                   # 曬豆的草蓆（稻草色）
SUGAR = TRIM                     # 糖塊（白）


def cup(M, x, y, z, layer='body'):
    """一只小杯（jícara）：2 × 2 × 2 的陶杯、杯口一層巧克力。"""
    M.box(layer, x, y, z, x + 2, y + 2, z + 1, CUP, force=True)
    M.box(layer, x, y, z + 1, x + 2, y + 2, z + 2, CHOC, force=True)


def small_table(M, x0, y0, z=8, layer='body', cups=((1, 1), (5, 5))):
    """一張小方桌（8 × 8 格、中間一根腳）＋桌上的杯。"""
    M.box(layer, x0, y0, z, x0 + 8, y0 + 8, z + 1, FLOOR)
    M.box(layer, x0 + 3, y0 + 3, 0, x0 + 5, y0 + 5, z, FRAME)
    for dx, dy in cups:
        cup(M, x0 + dx, y0 + dy, z + 1, layer)


def stool(M, x0, y0, layer='body', z=4):
    """一張小凳（4 × 4 的座面、中間一根腳）。"""
    M.box(layer, x0, y0, z, x0 + 4, y0 + 4, z + 1, FLOOR)
    M.box(layer, x0 + 1, y0 + 1, 0, x0 + 3, y0 + 3, z, FRAME)


def chocolatera(M, x, y, z, layer='body'):
    """銅的巧克力壺：4 × 4 × 5 的壺身、壺口一圈巧克力、木攪棒（molinillo）從壺口伸出來。"""
    M.box(layer, x, y, z, x + 4, y + 4, z + 5, COPPER)
    M.box(layer, x + 1, y + 1, z + 4, x + 3, y + 3, z + 5, CHOC, force=True)
    M.box(layer, x + 1, y + 1, z + 5, x + 2, y + 2, z + 9, FRAME)
    M.box(layer, x + 4, y + 1, z + 1, x + 5, y + 3, z + 4, FRAME)          # 木柄


def sugar_loaf(M, x, y, z, layer='body'):
    """一顆糖錐（3 × 3 底、往上收）。"""
    M.box(layer, x, y, z, x + 3, y + 3, z + 3, SUGAR)
    M.box(layer, x + 1, y + 1, z + 3, x + 2, y + 2, z + 5, SUGAR)


def sack(M, x0, y0, z=0, w=5, d=5, h=6, layer='body'):
    """一袋可可豆：米白的麻袋、敞口露出褐的豆。"""
    M.box(layer, x0, y0, z, x0 + w, y0 + d, z + h, CUP)
    M.box(layer, x0 + 1, y0 + 1, z + h - 1, x0 + w - 1, y0 + d - 1, z + h, BEAN, force=True)


def chocolate_house():
    """巧克力館（chocolate-house；西屬的 chocolatería、英屬的 chocolate house）：臨路一棟橫板牆的屋子（8.8 × 5 m、毛石地檻、木瓦四坡頂往前放緩蓋住前廊），
    前廊兩張小方桌與小凳、桌上的杯；屋裡三張小桌、後牆的長櫃台（兩只銅的巧克力壺插著攪棒、一排杯、糖錐）、櫃台後的架子；
    左後角磨可可的石磨台（metate＋石棍、底下一盆炭火）、幾袋可可豆；吊一塊畫著一杯冒熱氣巧克力的招牌。
    後院用木柵圍起來：曬可可豆的架子（草蓆上鋪一層豆）、茅草單坡的灶棚（石灶、吊一口鍋、紅的火）、水桶。"""
    X, Y, Z = 100, 120, 72
    M = Model((X, Y, Z))
    X0, Y0, X1, Y1 = 6, 30, 94, 80                                     # 屋 8.8 × 5 m
    R, t, fl = (X0, Y0, X1, Y1), 2, 4
    GY0 = 10                                                           # 前廊的前緣（廊深 2 m）
    rubble_walls(M, R, 0, fl, 4, salt=11431)
    M.box('body', X0, Y0, fl - 1, X1, Y1, fl, FLOOR)
    board_walls(M, R, fl, 34, t)
    piers(M, (X0, GY0, X1, Y0), fl - 1, step=22)
    M.box('gallery', X0, GY0, fl - 1, X1, Y0, fl, FLOOR)
    # ── 門窗 ──
    put_part(M, 'door-double', '前-門', 'front', R, 50, fl, t)
    for i, cx in enumerate((22, 78)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, fl + 9, t)
    for face, nm in (('left', '左'), ('right', '右')):
        put_part(M, 'window-board', '%s-窗' % nm, face, R, 48, fl + 9, t)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 40, fl, t)
    steps(M, 40, 60, GY0, 1, 2, 4, back=False)
    M.anchor('door', 50, Y0 - 1, fl)
    # ── 屋頂、前廊 ──
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 34, 'p': 0.9, 'over': (4, 4, Y0 - GY0 + 4, 4), 'kick': {'front': 0.42}}], salt=11432)
    gallery_posts(M, (X0, 28, 70, X1 - 2), GY0, fl, top)
    for tx in (14, 72):                                                # 前廊：兩張小方桌、各兩張小凳
        small_table(M, tx, 16, fl + 8, layer='gallery')
        stool(M, tx - 6, 18, layer='gallery', z=fl + 4)
        stool(M, tx + 10, 18, layer='gallery', z=fl + 4)
    # ── 屋裡：三張小桌與小凳 ──
    for (tx, ty) in ((14, 38), (32, 50), (66, 38)):
        small_table(M, tx, ty, fl + 8)
        stool(M, tx - 6, ty + 2, z=fl + 4)
        stool(M, tx + 10, ty + 2, z=fl + 4)
    # ── 後牆的長櫃台（x 54..90、y 60..66）：兩只巧克力壺、一排杯、糖錐；櫃台後的架子 ──
    M.box('body', 54, 60, fl, 90, 66, fl + 10, FRAME)
    M.box('body', 54, 60, fl + 10, 90, 66, fl + 11, FLOOR)
    chocolatera(M, 58, 61, fl + 11)
    chocolatera(M, 66, 61, fl + 11)
    for x in range(74, 84, 3):
        cup(M, x, 62, fl + 11)
    sugar_loaf(M, 85, 61, fl + 11)
    for z in (fl + 16, fl + 22):                                       # 後牆上兩層架：一排杯、糖錐、一只壺
        M.box('body', 56, Y1 - t - 3, z, 88, Y1 - t, z + 1, FLOOR)
        for x in range(58, 72, 3):
            cup(M, x, Y1 - t - 2, z + 1)
    sugar_loaf(M, 76, Y1 - t - 3, fl + 17)
    sugar_loaf(M, 81, Y1 - t - 3, fl + 17)
    chocolatera(M, 78, Y1 - t - 4, fl + 23)
    # ── 左後角：磨可可的石磨台（metate：三級往後升的石板＋一根石棍）、底下一盆炭火；可可豆袋 ──
    for k in range(3):
        M.box('body', 10, 66 + 3 * k, fl, 24, 69 + 3 * k, fl + 3 + k, STONE_D)
    M.box('body', 11, 70, fl + 4, 23, 71, fl + 5, STONE_L, force=True)    # 石棍（mano；擱在第二級上）
    M.box('body', 12, 72, fl + 5, 22, 75, fl + 6, CHOC, force=True)       # 磨出來的可可膏
    M.box('body', 26, 70, fl, 30, 74, fl + 2, IRON)                       # 炭盆
    M.box('body', 27, 71, fl + 2, 29, 73, fl + 3, EMBER, force=True)
    sack(M, 10, 54, fl)
    sack(M, 16, 54, fl, h=5)
    # ── 招牌：右前角一根柱、橫臂、吊著的一塊板（畫一杯冒熱氣的巧克力）──
    M.box('body', 95, 4, 0, 97, 6, 42, FRAME)
    M.box('body', 82, 4, 40, 97, 6, 42, FRAME)
    for x in (84, 93):
        M.box('body', x, 4, 36, x + 1, 5, 40, IRON)
    for x in range(83, 95):
        for z in range(26, 36):
            M.put('body', x, 4, z, FRAME if x in (83, 94) or z in (26, 35) else SHUT)
    M.box('body', 86, 4, 28, 92, 5, 32, CUP)                            # 杯身
    M.box('body', 86, 4, 31, 92, 5, 32, CHOC)                           # 杯口的巧克力
    M.box('body', 92, 4, 29, 93, 5, 31, CUP)                            # 杯把
    for (x, z) in ((87, 33), (88, 34), (90, 33), (89, 34)):            # 冒的熱氣
        M.put('body', x, 4, z, TRIM)
    M.anchor('sign', 89, 4, 30)
    # ── 後院：木柵；曬可可豆的架子；茅草單坡的灶棚、石灶；水桶 ──
    yb = Y - 2
    palisade(M, [(X0, Y1), (2, Y1), (2, yb), (X - 2, yb), (X - 2, Y1), (X1 - 1, Y1)], gap={(x, yb) for x in range(30, 42)})
    for x in (8, 34):                                                  # 曬豆的架子（barbacoa：四根腳、草蓆面、鋪一層豆）
        for y in (92, 106):
            M.box('body', x, y, 0, x + 2, y + 2, 7, FRAME)
    M.box('body', 8, 92, 7, 36, 108, 8, MAT)
    for x in range(10, 34, 2):
        for y in range(94, 106, 2):
            if (x + y) % 4:
                M.put('body', x, y, 8, BEAN)
    K = (56, 88, 94, 114)                                              # 灶棚 3.8 × 2.6 m
    M.box('body', K[0], K[1], 0, K[2], K[3], 1, EARTH_W)
    lean_roof_posts(M, K[0] - 2, K[1] - 2, K[2] + 2, K[3] + 2, 30, 0.3, 'back', thatch_color,
                    [(K[0], K[1]), (K[2] - 2, K[1]), (K[0], K[3] - 2), (K[2] - 2, K[3] - 2)], salt=11433)
    hearth(M, 72, 98, 86, 110, 8)                                     # 石灶（叉柱吊一口鍋：烘豆、燒水）
    M.box('body', 76, 100, 2, 82, 106, 3, EMBER, force=True)
    M.anchor('smoke', 79, 104, 20)
    sack(M, 60, 106, 1)
    M.models += [{'name': '水桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [48, 108, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-門', (36.5, Y0, 24.5))
    M.anchor('lot-0', 0, 0, 0)
    # 工作點（BUILDING_SPEC §5；服務 ＝ 菜單最多人的那道 加糖的熱巧克力 jobs 3 × 二級 mult 2 ＝ 6 ＋ 1 ＝ 7）：
    #   a 櫃台後、b 石磨台前、c／d 屋裡兩桌之間送杯、f 前廊、g 後院灶前、e 曬豆架旁
    for nm, at, to in (('a1', (72, 72, fl), (72, 63, fl + 11)), ('b1', (17, 62, fl), (17, 70, fl + 4)), ('c1', (27, 47, fl), (18, 42, fl + 9)),
                       ('d1', (56, 44, fl), (70, 42, fl + 9)), ('f1', (50, 22, fl), (18, 20, fl + 9)), ('g1', (79, 94, 1), (79, 104, 8)),
                       ('e1', (22, 88, 0), (22, 100, 8))):
        M.anchor('work-' + nm, *at)
        M.anchor('work-%s-to' % nm, *to)
    return {'key': 'carib-chocolate-house', 'style': 'carib',
            'title': '加勒比海的巧克力館（chocolatería／chocolate house：橫板牆的屋子、木瓦四坡頂蓋住前廊；屋裡小桌、長櫃台上的銅巧克力壺與攪棒、磨可可的石磨台；招牌畫一杯熱巧克力；後院曬可可豆的架子與灶棚）',
            'use': 'chocolate-house', 'lot': (10, 12), 'M': M, 'layers': {'body': '屋、擺設與後院', 'gallery': '前廊', 'roof': '屋頂'}}


ALL = [chocolate_house]
