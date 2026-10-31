# 客棧（TASK-1142；Tim 2026-10-31「TASK-1142 GO」「另外開單(都要有自己的模型)」）—— 加勒比海（carib）第一款。
# 工具同 trailhead-harbour-01m 的 restaurant.py（quay ⇒ ame-carib-civic-01m 的 harbour／civic ⇒ summit-carib-01m 的調色盤、Model、牆、屋頂、部件）。
#   座標同 kit.py：x 臨路寬（從街上看左 → 右）、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料與設計的分界：
#   〔摘：通論〕17 世紀港口城的客棧（西屬 posada、mesón，英屬 inn、ordinary）住的是水手、商人、等船的人；樓下接待與喝酒、樓上一間一間的客房，
#              窮的睡通鋪（一間幾張床、一張床還常常兩個人睡）。加勒比海的木造兩層樓前面是上下兩層的外廊（樓上當陽台）。
#   〔設計〕平面、房間數、樓梯的位置、床、招牌（一張床的圖）、後院曬床單 —— 都沒有查到單一城的樣子。
#   遊戲：住宿那一本（Blocksail world/food.js SATISFY.lodge：只算上岸的水手）；菜單客房（床單、肥皂）、通鋪（world/recipes.js inn-room、inn-bunk）。
import os, sys
from restaurant import *                                               # noqa: F401,F403  workshops ⇒ quay ＋ harbour／civic／carib 的全部、table_set、trestle_table、bench、lantern

SHEET = TRIM                     # 床單、枕頭（白）
BLANKET = (SH_RED, SH_BLUE, 136)  # 毯子（紅、藍、牛皮色）


def bed(M, x0, y0, w, d, z, blanket, layer='body'):
    """一張床（頭朝 +y 的牆）：四根床腳＋床框 3 格高、白床單、枕頭（床頭那一截高一格）、毯子蓋住床尾三分之二。"""
    for x, y in ((x0, y0), (x0 + w - 1, y0), (x0, y0 + d - 1), (x0 + w - 1, y0 + d - 1)):
        M.box(layer, x, y, z, x + 1, y + 1, z + 3, FRAME)
    M.box(layer, x0, y0, z + 3, x0 + w, y0 + d, z + 4, FRAME)
    M.box(layer, x0, y0, z + 4, x0 + w, y0 + d, z + 5, SHEET)
    M.box(layer, x0 + 1, y0 + d - 4, z + 5, x0 + w - 1, y0 + d - 1, z + 6, SHEET)       # 枕頭
    M.box(layer, x0, y0, z + 5, x0 + w, y0 + (d * 2) // 3, z + 6, blanket)              # 毯子
    M.box(layer, x0 - 1, y0 + d - 1, z, x0 + w + 1, y0 + d, z + 10, FRAME)              # 床頭板


def chest(M, x0, y0, z, w=8, d=5, h=5, layer='body'):
    """床尾的木箱（水手的箱子）：深色木、頂上一道鐵條。"""
    M.box(layer, x0, y0, z, x0 + w, y0 + d, z + h, SHUT)
    M.box(layer, x0, y0, z + h - 1, x0 + w, y0 + 1, z + h, IRON, force=True)


def rail(M, x0, y0, x1, y1, z, h=9, layer='body', step=3):
    """欄杆：一格寬的扶手（頂一條）＋每 step 格一根直欄。沿 x 或沿 y（另一個方向寬 1）。"""
    M.box(layer, x0, y0, z + h - 1, x1, y1, z + h, FRAME)
    if x1 - x0 >= y1 - y0:
        for x in list(range(x0, x1, step)) + [x1 - 1]:
            M.box(layer, x, y0, z, x + 1, y1, z + h - 1, FRAME)
    else:
        for y in list(range(y0, y1, step)) + [y1 - 1]:
            M.box(layer, x0, y, z, x1, y + 1, z + h - 1, FRAME)


def carib_inn():
    """客棧（inn；加勒比海的 posada／inn）：毛石台基上一棟兩層的橫板木樓（10 × 6.2 m）、木瓦四坡頂往前放緩，蓋住前面上下兩層的外廊（樓上當陽台、欄杆）；
    樓下大堂：雙扇大門、兩張長桌與長凳、右後角的櫃台（帳本、鑰匙板、一排酒桶）、左邊順著牆往前爬的木樓梯；
    樓上：前面一條走廊（往陽台的門）、後面三間客房 —— 左邊通鋪（三張窄床）、中間與右邊各一張雙人床、床尾木箱；
    招牌吊在右前角（板上畫一張床）；後院木柵、兩根柱子拉的晾衣繩上曬著床單、洗衣的木盆與水桶、長凳。"""
    X, Y, Z = 120, 160, 110
    M = Model((X, Y, Z))
    X0, Y0, X1, Y1 = 10, 30, 110, 92                                   # 樓 10 × 6.2 m
    R, t, fl = (X0, Y0, X1, Y1), 2, 6
    F2 = fl + 32                                                       # 樓板（樓下淨高 3.2 m）
    ZT = F2 + 31                                                       # 牆頂（樓上淨高 3 m）
    GY0 = 12                                                           # 外廊的前緣（廊深 1.8 m）
    rubble_walls(M, (X0, GY0, X1, Y1), 0, fl - 1, 4, salt=11421)       # 毛石台基（含外廊底下）
    M.box('body', X0 + 4, GY0 + 4, 0, X1 - 4, Y1 - 4, fl - 1, EARTH_W)
    M.box('body', X0, Y0, fl - 1, X1, Y1, fl, FLOOR)
    board_walls(M, R, fl, F2, t)
    # 樓板（留樓梯口：x 12..22、y 52..88）
    SW = (X0 + t, 52, 22, Y1 - t)
    M.box('body', X0, Y0, F2, X1, SW[1], F2 + 1, FLOOR)
    M.box('body', SW[2], SW[1], F2, X1, Y1, F2 + 1, FLOOR)
    M.box('body', X0, SW[1], F2, SW[0], Y1, F2 + 1, FLOOR)
    M.box('body', SW[0], SW[3], F2, SW[2], Y1, F2 + 1, FLOOR)
    board_walls(M, R, F2 + 1, ZT, t)
    # 樓梯：靠左牆、從後面往前爬（11 級，每級高 3、深 3）；底下實心（樓梯下的儲物）
    for k in range(11):
        y0 = 85 - 3 * k
        M.box('body', SW[0], y0, fl, SW[2] - 1, y0 + 3, fl + 3 * (k + 1), FLOOR if k % 2 == 0 else FRAME)
    rail(M, SW[2] - 1, SW[1], SW[2], SW[3], F2 + 1)                    # 樓上：樓梯口右邊的欄杆
    rail(M, SW[0], SW[3] - 1, SW[2] - 1, SW[3], F2 + 1)
    # ── 門窗 ──
    put_part(M, 'door-double', '前-大門', 'front', R, 60, fl, t)
    for i, cx in enumerate((32, 88)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, fl + 9, t)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 92, fl, t)
    put_part(M, 'window-board', '後-窗', 'back', R, 56, fl + 9, t)
    put_part(M, 'window-board', '右-窗', 'right', R, 61, fl + 9, t)
    put_part(M, 'door-plank', '樓上-前-門（往陽台）', 'front', R, 60, F2 + 1, t)
    for i, cx in enumerate((32, 88)):
        put_part(M, 'window-board', '樓上-前-窗%d' % (i + 1), 'front', R, cx, F2 + 9, t)
    for i, cx in enumerate((36, 66, 95)):
        put_part(M, 'window-board', '樓上-後-窗%d' % (i + 1), 'back', R, cx, F2 + 9, t)
    put_part(M, 'window-board', '樓上-右-窗', 'right', R, 70, F2 + 9, t)
    put_part(M, 'window-board', '樓上-左-窗', 'left', R, 70, F2 + 9, t)
    steps(M, 50, 70, GY0, 2, 3, 3, back=False, layer='body', color=RUBBLE)
    steps(M, 86, 98, Y1, 2, 3, 3, back=True, layer='body', color=RUBBLE)
    M.anchor('door', 60, Y0 - 1, fl)
    # ── 屋頂、外廊（上下兩層）──
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ZT, 'p': 0.8, 'over': (4, 4, Y0 - GY0 + 4, 4), 'kick': {'front': 0.3}}], salt=11422)
    gallery_posts(M, (X0, 34, 84, X1 - 2), GY0, fl, top)
    M.box('gallery', X0, GY0, fl - 1, X1, Y0, fl, FLOOR)
    M.box('gallery', X0, GY0, F2, X1, Y0, F2 + 1, FLOOR)                # 陽台的地板（跟樓板同高）
    rail(M, X0, GY0, X1, GY0 + 1, F2 + 1, layer='gallery')
    rail(M, X0, GY0 + 1, X0 + 1, Y0, F2 + 1, layer='gallery')
    rail(M, X1 - 1, GY0 + 1, X1, Y0, F2 + 1, layer='gallery')
    bench(M, 16, 40, 14, 17, fl + 4, layer='gallery')                   # 樓下廊上一條長凳（等船的人）
    # ── 樓下大堂 ──
    for (a, b) in ((30, 36), (52, 58)):
        trestle_table(M, a, b, 46, 70, fl + 8)
        bench(M, a - 4, a - 1, 46, 70, fl + 4)
        bench(M, b + 1, b + 4, 46, 70, fl + 4)
    M.box('body', 76, 70, fl, 106, 74, fl + 10, FRAME)                  # 櫃台（右後角，L 形）
    M.box('body', 76, 70, fl + 10, 106, 74, fl + 11, FLOOR)
    M.box('body', 76, 74, fl, 80, 84, fl + 10, FRAME)
    M.box('body', 76, 74, fl + 10, 80, 84, fl + 11, FLOOR)
    M.box('body', 84, 71, fl + 11, 90, 73, fl + 12, SACK)               # 攤開的帳本
    M.box('body', 86, 71, fl + 12, 87, 73, fl + 13, DARK)
    M.box('body', 96, Y1 - t - 1, fl + 14, 106, Y1 - t, fl + 22, FRAME)  # 後牆上的鑰匙板（一排鐵鑰匙）
    for x in range(97, 106, 2):
        M.put('body', x, Y1 - t - 2, fl + 18, IRON, force=True)
    # ── 樓上：走廊、三間客房 ──
    zf = F2 + 1
    for x0, x1 in ((22, 50), (52, 79), (81, X1 - t)):                  # 客房的前牆（隔走廊；門口 8 格、高 21）
        cx = (x0 + x1) // 2
        M.box('body', x0, 48, zf, cx - 4, 50, ZT, BOARD)
        M.box('body', cx + 4, 48, zf, x1, 50, ZT, BOARD)
        M.box('body', cx - 4, 48, zf + 21, cx + 4, 50, ZT, BOARD)
    for x in (50, 79):                                                 # 房間之間的板牆
        M.box('body', x, 50, zf, x + 2, Y1 - t, ZT, BOARD)
    M.box('body', 20, 48, zf, 22, 52, ZT, BOARD)                       # 走廊左端（樓梯口）到牆的那一截
    for i, x in enumerate((24, 33, 42)):                               # 左：通鋪（三張窄床）
        bed(M, x, 64, 6, 22, zf, BLANKET[i % 3])
    bed(M, 58, 66, 14, 21, zf, BLANKET[0])                             # 中、右：雙人床＋床尾木箱
    chest(M, 61, 58, zf)
    bed(M, 88, 66, 14, 21, zf, BLANKET[1])
    chest(M, 91, 58, zf)
    M.box('body', 72, 84, zf, 77, 88, zf + 8, FRAME)                   # 中間那間的小几、臉盆
    M.box('body', 73, 85, zf + 8, 76, 87, zf + 9, SHEET)
    # ── 招牌：右前角的柱上一根橫臂、吊著一塊板（畫一張床：深色床框、白床單、紅毯子）──
    M.box('body', 112, 2, 0, 114, 4, 44, FRAME)
    M.box('body', 98, 2, 42, 114, 4, 44, FRAME)
    for x in (100, 109):
        M.box('body', x, 2, 38, x + 1, 3, 42, IRON)
    for x in range(99, 111):
        for z in range(28, 38):
            M.put('body', x, 2, z, FRAME if x in (99, 110) or z in (28, 37) else SHUT)
    M.box('body', 101, 2, 30, 109, 3, 31, DARK)                        # 床框
    M.box('body', 101, 2, 31, 102, 3, 34, DARK)                        # 床頭
    M.box('body', 102, 2, 31, 109, 3, 32, SHEET)
    M.box('body', 104, 2, 32, 109, 3, 33, SH_RED)
    M.box('body', 102, 2, 32, 104, 3, 33, SHEET)                       # 枕頭
    M.anchor('sign', 105, 2, 33)
    # ── 後院：木柵、晾衣繩上的床單、木盆、水桶、長凳 ──
    yb = Y - 2
    palisade(M, [(X0, Y1), (2, Y1), (2, yb), (X - 2, yb), (X - 2, Y1), (X1 - 1, Y1)], gap={(x, yb) for x in range(14, 26)})
    for x in (20, 100):
        M.box('body', x, 124, 0, x + 2, 126, 26, FRAME)
    M.box('body', 22, 124, 25, 100, 125, 26, FRAME)                    # 晾衣繩（一根橫桿）
    for i, x in enumerate((26, 44, 62, 80)):                           # 四條床單垂下來（每條 14 格寬、中間空一格）
        M.box('body', x, 124, 13, x + 14, 125, 25, SHEET if i % 2 == 0 else LIME, force=True)
    trestle_table(M, 40, 64, 104, 110, 8)                              # 疊床單的桌
    M.box('body', 44, 105, 9, 52, 109, 12, SHEET)
    bench(M, 70, 94, 140, 143)
    M.models += [{'name': '洗衣桶', 'source': 'summit-rocher-01m-barrel', 'at': [30, 106, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '水桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [104, 106, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-櫃台1', 'source': 'summit-rocher-01m-barrel', 'at': [92, 80, fl], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-櫃台2', 'source': 'summit-rocher-01m-barrel', 'at': [100, 80, fl], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-門', (46.5, Y0, 24.5))
    lantern(M, '燈籠-陽台', (74.5, Y0, F2 + 22.5))
    M.anchor('lot-0', 0, 0, 0)
    # 工作點（BUILDING_SPEC §5；服務 ＝ 菜單最多人的那道 客房 jobs 3 × 二級 mult 2 ＝ 6 ＋ 1 ＝ 7）：
    #   a 櫃台後、b 大堂（桌間）、c 樓梯口、d／f／g 三間客房各一點（床邊整理；隔著板牆 ⇒ 不同組，townkit_check「同一組隔著東西」）、e 後院晾床單
    #   ⛔ f1 不放在床尾木箱那一格（第一版 64,62 在箱子裡：townkit_check「點在實心裡」）
    for nm, at, to in (('a1', (90, 78, fl), (90, 70, fl + 12)), ('b1', (44, 58, fl), (34, 58, fl + 8)), ('c1', (30, 50, zf), (17, 60, zf)),
                       ('d1', (30, 58, zf), (30, 70, zf + 5)), ('f1', (56, 64, zf), (64, 72, zf + 5)), ('g1', (86, 62, zf), (94, 72, zf + 5)),
                       ('e1', (52, 120, 0), (52, 124, 18))):
        M.anchor('work-' + nm, *at)
        M.anchor('work-%s-to' % nm, *to)
    return {'key': 'carib-inn', 'style': 'carib',
            'title': '加勒比海的客棧（posada／inn：毛石台基上兩層的橫板木樓、木瓦四坡頂、上下兩層的外廊與陽台欄杆；樓下大堂、櫃台、樓梯；樓上通鋪與兩間客房；招牌畫一張床；後院曬床單）',
            'use': 'inn', 'lot': (12, 16), 'M': M, 'layers': {'body': '樓、客房與後院', 'gallery': '外廊與陽台', 'roof': '屋頂'}}


ALL = [carib_inn]
