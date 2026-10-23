# 城鎮共用建築第六批（TASK-0869；Tim 2026-10-23「843 847 繼續做共用建築吧 GO」）—— 過磅所（港口配套）、四種工坊：鐵匠鋪、麵包坊、桶匠、木工坊（全部共用 common）。
# 工具同 town3.py（quay ⇒ ame-carib-civic-01m 的 harbour／civic ⇒ summit-carib-01m 的調色盤、Model、牆、屋頂、部件）；shipyard.py 借鋸木架。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 工坊的地塊 ＝ 住宅那一格 8 × 12 m（TOWN_BUILD §1.1.5「蓋在城裡的建地上」、§3 ⑦）；開場不擺（§1.1.10 第 4 題），之後建築模式蓋、鎮民表的鐵匠、麵包師、木匠在這裡工作。
# 共用 ⇒ 開敞的棚、毛石與木板、木瓦頂：法屬、英屬、西屬的城擺起來都不突兀（TOWN_BUILD §2.1 的退路）。
# 史料：作品 references/README.md 第六批那一節；查不到的都寫「設計」。
import os, sys, math
from quay import *                                                     # noqa: F401  rope_line、spar ＋ harbour／civic／carib 的全部
from townpub import end_gable, trestle_table, bench                    # noqa: E402
from shipyard import saw_trestle                                       # noqa: E402
from town3 import lantern                                              # noqa: E402

LEATHER = 100                    # 風箱的皮（同菸草捲那一色的褐）
BREAD, BREAD_D = 213, 141        # 麵包（土黃）、烤深一點的皮
SACK = 218                       # 麵粉袋（米白）
CHAR = DARK                      # 木炭堆


def roof_posts(M, top, pts, z0=0, w=2, layer='body'):
    """柱子立到屋面底下：pts ＝ [(x, y)…]，每根 w × w，頂 ＝ 那幾欄屋面最低的那一格的下面。"""
    for (px, py) in pts:
        zt = min(top[(x, y)] for x in range(px, px + w) for y in range(py, py + w)) - 1
        M.box(layer, px, py, z0, px + w, py + w, zt, FRAME)


def ring_x(M, cx, y, cz, r, color=IRON, layer='body'):
    """立在 x–z 平面的一個圈（掛在牆上的鐵箍、磨刀石）：半徑 r、粗一格。"""
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for z in range(int(cz - r - 1), int(cz + r + 2)):
            d = math.hypot(x + 0.5 - cx, z + 0.5 - cz)
            if r - 0.75 <= d <= r + 0.5:
                M.put(layer, x, y, z, color)


def barrel_shell(M, cx, cy, z0, h, r0, r1, top_open=True, gap=False, hoops=(), color=FRAME, layer='body'):
    """做到一半的桶：桶板圍成一圈（截面圓，半徑從 r0（底）到 r1（頂）線性變）、厚一格；gap ⇒ 底下一半每隔一根桶板留縫（剛立起來、還沒收攏）；
    hoops ＝ 箍的高（那一圈換鐵色）。"""
    for z in range(z0, z0 + h):
        t = (z - z0) / max(1, h - 1)
        r = r0 + (r1 - r0) * t
        for x in range(int(cx - r - 2), int(cx + r + 2)):
            for y in range(int(cy - r - 2), int(cy + r + 2)):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if r - 1 <= d <= r:
                    a = int((math.atan2(y + 0.5 - cy, x + 0.5 - cx) + math.pi) / (2 * math.pi) * 24)
                    if gap and z < z0 + h // 2 and a % 2:
                        continue
                    M.put(layer, x, y, z, IRON if (z - z0) in hoops else (color if a % 2 else BOARD))


# ─────────────────────────────── 鐵匠鋪 8 × 12 m ───────────────────────────────
def smithy():
    """鐵匠鋪（smithy）：毛石三面牆、正面全開（一道石楣）的鍛造間 —— 後牆邊架高的石砌火爐、火爐上的石罩接一根毛石大煙囪穿出屋頂；
    火爐左邊一具雙板風箱（皮、木板、拉桿）、火爐前樹墩上的鐵砧、淬火桶、右牆的工具架與台鉗工作檯；後院木炭堆、廢鐵堆、釘馬掌的架（travail）。
    - 照什麼：鎮民表（Blocksail world/townkit/_people.js）的鐵匠在這裡工作；大船廠裡也有一間鐵匠鋪（ame，毛石小屋＋火爐＋煙囪）⇒ 同一套材料。
      17 世紀加勒比海城裡鐵匠鋪的形制〔沒查到〕⇒ 架高火爐、石罩、雙板風箱、樹墩鐵砧、釘馬掌架照歐洲鄉間鐵匠鋪的常見樣子（設計）。"""
    X, Y, Z = 80, 120, 80
    M = Model((X, Y, Z))
    R = (6, 20, 74, 84)                                                # 6.8 × 6.4 m
    rubble_walls(M, R, 0, 28, 4, salt=8691)
    M.clear(10, R[1], 0, 70, R[1] + 4, 24)                             # 正面全開，留兩端石墩與上面一道石楣
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 1, EARTH_W)   # 夯土地
    for x0, x1 in ((R[0], R[0] + 4), (R[2] - 4, R[2])):               # 兩端的山牆（毛石色；先砌 ⇒ 屋面蓋過牆頂，從上面看不到牆）
        end_gable(M, x0, x1, R[1], R[3], 28, 0.6, z0=28, color=RUBBLE, edge=RUBBLE_D)
    top = shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 28, 'p': 0.6, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=8692)
    # 火爐：後牆邊架高的石台（0.8 m）、台面的火床（黑炭、中間紅的火）、上面石罩、石罩接大煙囪
    M.box('body', 24, 60, 0, 50, 80, 8, RUBBLE)
    M.box('body', 26, 62, 8, 48, 78, 9, CHAR)
    M.box('body', 32, 66, 8, 42, 74, 9, EMBER, force=True)
    M.box('body', 24, 76, 9, 50, 80, 16, RUBBLE)                       # 火床後面的擋火牆
    M.box('body', 22, 66, 18, 52, 80, 20, RUBBLE_D)                    # 石罩（兩級往裡收）
    M.box('body', 26, 70, 20, 48, 80, 24, RUBBLE)
    for (x, y) in ((24, 66), (48, 66)):                               # 石罩前緣兩根鐵撐
        M.box('body', x, y, 9, x + 2, y + 1, 18, IRON)
    zc = max(top[(x, y)] for x in range(30, 44) for y in range(72, 80)) + 8
    M.box('body', 30, 72, 24, 44, 80, zc, RUBBLE, force=True)          # 煙囪（穿過屋頂，蓋過那幾格屋面）
    M.box('body', 29, 71, zc - 2, 45, 81, zc, MORTAR, force=True)      # 煙囪帽
    M.box('body', 33, 75, zc - 2, 41, 79, zc, CHAR, force=True)        # 煙道口
    M.anchor('smoke', 37, 77, zc - 1)
    # 雙板風箱（火爐左邊）：兩塊楔形的板、中間皮、嘴伸進火爐側面；木架撐著，上面一根拉桿接到吊在梁下的橫木
    for (x, y) in ((11, 64), (19, 64), (11, 74), (19, 74)):
        M.box('body', x, y, 0, x + 2, y + 2, 10, FRAME)
    for x in range(10, 23):
        h = 2 + (22 - x) // 3                                          # 左寬右窄：嘴在右邊（往火爐）
        M.box('body', x, 63, 10, x + 1, 77, 11, FRAME)                 # 下板
        M.box('body', x, 63, 11, x + 1, 77, 11 + h, LEATHER)           # 皮
        M.box('body', x, 63, 11 + h, x + 1, 77, 12 + h, FRAME)         # 上板
    M.box('body', 23, 69, 11, 26, 71, 13, IRON, force=True)            # 嘴（鐵管）伸進火爐側面
    M.box('body', 14, 69, 13, 16, 71, 30, FRAME)                       # 拉桿（從上板往上到橫木）
    M.box('body', 10, 69, 30, 36, 71, 32, FRAME)                       # 橫木（左端插進左牆）
    M.box('body', 34, 69, 18, 35, 70, 30, ROPE)                        # 拉繩垂到火爐前（鐵匠伸手拉）
    # 鐵砧：火爐前一個樹墩（半徑 3.5）、上面鐵砧（含尖角）；旁邊的淬火桶
    for x in range(30, 40):
        for y in range(42, 52):
            if math.hypot(x + 0.5 - 35, y + 0.5 - 47) <= 3.6:
                M.box('body', x, y, 0, x + 1, y + 1, 6, LOG)
    M.box('body', 31, 45, 6, 39, 49, 8, IRON)
    M.box('body', 32, 45, 8, 40, 49, 10, IRON)
    M.box('body', 40, 46, 9, 43, 48, 10, IRON)
    # 右牆：工具架（一根橫木、上面掛火鉗與錘）、台鉗工作檯
    M.box('body', 69, 30, 20, 70, 78, 21, FRAME)
    for i, y in enumerate(range(33, 76, 5)):
        M.box('body', 69, y, 11 + i % 3, 70, y + 1, 20, IRON)
        if i % 2 == 0:
            M.box('body', 68, y, 11 + i % 3, 69, y + 2, 13 + i % 3, IRON)
    trestle_table(M, 54, 68, 26, 34, 8)
    M.box('body', 56, 27, 9, 59, 30, 13, IRON)                         # 台鉗
    # 後院：木柵、木炭堆、廢鐵堆、釘馬掌的架（四柱、兩道橫木、頭前一道軛）
    palisade(M, [(R[0], R[3]), (1, R[3]), (1, 118), (78, 118), (78, R[3]), (R[2] - 1, R[3])], gap={(x, 118) for x in range(34, 46)})
    for x in range(6, 30):
        for y in range(92, 114):
            h = int(8 - 0.5 * math.hypot(x + 0.5 - 18, (y + 0.5 - 103) * 1.1))
            if h > 0:
                M.box('body', x, y, 0, x + 1, y + 1, h, CHAR if h01('ch', x, y) < 0.8 else RUBBLE_D)
    for (x, y, z) in ((34, 108, 0), (36, 110, 0), (40, 107, 0), (35, 112, 0), (35, 108, 1), (37, 110, 1)):   # 上一層壓在下一層上
        M.box('body', x, y, z, x + 3, y + 1, z + 1, IRON)
    for (px, py) in ((50, 92), (70, 92), (50, 112), (70, 112)):
        M.box('body', px, py, 0, px + 2, py + 2, 22, FRAME)
    for py in (92, 112):
        M.box('body', 50, py, 20, 72, py + 2, 22, FRAME)
    for px in (50, 70):
        M.box('body', px, 92, 12, px + 2, 114, 14, FRAME)
    M.box('body', 50, 92, 6, 72, 94, 8, FRAME)                         # 軛木（牛馬的頭靠在這裡）
    M.models += [{'name': '淬火桶', 'source': 'summit-rocher-01m-barrel', 'at': [48, 52, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [10, 112, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-石墩', (8, R[1], 20))
    M.anchor('door', 40, 12, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'smithy', 'title': '鐵匠鋪（共用：毛石三面牆、正面全開的鍛造間、架高的火爐與石罩、毛石大煙囪、雙板風箱、樹墩上的鐵砧、工具架；後院木炭、廢鐵、釘馬掌的架）',
            'use': 'smithy', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '牆、火爐與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 麵包坊 8 × 12 m ───────────────────────────────
def bakery():
    """麵包坊（bakery）：臨路一間木板店面（木板門、往下開當櫃檯的賣窗、架上一排一排的麵包、揉麵槽、麵粉袋）；
    後院一座毛石台基上的圓頂麵包爐（爐口朝店、裡面紅的火、爐頂前緣一支小煙口）、爐上的茅草披棚、成捆的柴。
    - 照什麼：鎮民表的麵包師（梅琳）在這裡與市場工作；TOWN_SIM 的配方「麵包坊」（麵粉 ⇒ 麵包）。
      加勒比海 17 世紀的麵包坊〔沒查到〕（當地多吃木薯餅 cassave，麵粉靠船運）⇒ 店面、圓頂爐（four à pain）、揉麵槽照法國鄉間麵包坊的常見樣子（設計）。"""
    X, Y, Z = 80, 120, 70
    M = Model((X, Y, Z))
    R = (6, 12, 74, 62)                                                # 店面 6.8 × 5 m
    board_walls(M, R, 0, 30, 2, bay=26)
    M.box('body', R[0] + 2, R[1] + 2, 0, R[2] - 2, R[3] - 2, 1, FLOOR)
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 30, 0.7, z0=30)
    put_part(M, 'door-plank', '前-門', 'front', R, 22, 0, 2)
    put_part(M, 'window-board', '前-賣窗', 'front', R, 54, 9, 2)
    put_part(M, 'door-plank', '後-門（往爐）', 'back', R, 34, 0, 2)
    put_part(M, 'window-board', '右-窗', 'right', R, 37, 9, 2)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.7, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=8693)
    # 賣窗裡面的櫃檯（擺幾條麵包）
    trestle_table(M, 44, 66, 16, 22, 8)
    for x in range(46, 64, 4):
        M.box('body', x, 17, 9, x + 3, 21, 11, BREAD if (x // 4) % 3 else BREAD_D)
    # 後牆的麵包架：三層板、板上一排圓麵包（板頂著後牆 ⇒ 不浮空）
    for z in (10, 16, 22):
        M.box('body', 44, 54, z, 72, 60, z + 1, FLOOR)
        for x in range(45, 71, 4):
            M.box('body', x, 55, z + 1, x + 3, 59, z + 3, BREAD if (x + z) % 3 else BREAD_D)
    for x in (44, 70):
        M.box('body', x, 54, 1, x + 2, 56, 23, FRAME)
    # 揉麵槽（pétrin：木箱、四腳）、麵粉袋
    M.box('body', 10, 36, 6, 34, 44, 11, FRAME)
    M.box('body', 11, 37, 9, 33, 43, 11, SACK, force=True)            # 槽裡的麵團
    for (x, y) in ((10, 36), (32, 36), (10, 42), (32, 42)):
        M.box('body', x, y, 0, x + 2, y + 2, 6, FRAME)
    for (x, y) in ((10, 48), (17, 48), (13, 52)):
        for z in range(0, 7):
            M.box('body', x, y, z, x + 6, y + 5, z + 1, SACK if z < 6 else MORTAR)
    # 後院：毛石台基上的圓頂麵包爐（爐口朝店）
    ox, oy = 34, 94
    M.box('body', 12, 74, 0, 56, 114, 8, RUBBLE)
    for x in range(14, 55):
        for y in range(76, 113):
            for z in range(8, 26):
                d = ((x + 0.5 - ox) / 18) ** 2 + ((y + 0.5 - oy) / 16) ** 2 + ((z + 0.5 - 8) / 14) ** 2
                if 0.72 <= d <= 1.0:
                    M.put('body', x, y, z, RUBBLE if h01('ov', x // 2, y // 2, z // 2) < 0.7 else MORTAR)
    M.box('body', 26, 77, 8, 42, 80, 18, RUBBLE_D, force=True)         # 爐口的石框（立在台基上）
    M.clear(29, 76, 8, 39, 84, 15)                                     # 爐口（朝店）
    M.box('body', 30, 82, 8, 38, 106, 9, CHAR, force=True)             # 爐床（炭）、裡面紅的火
    M.box('body', 32, 96, 9, 36, 102, 10, EMBER, force=True)
    M.box('body', 32, 80, 17, 36, 84, 28, RUBBLE, force=True)          # 爐頂前緣的小煙口
    M.anchor('smoke', 34, 82, 27)
    # 爐上的茅草披棚（高的一邊靠店）、柴捆
    lean_roof_posts(M, 6, 66, 74, 118, 40, 0.2, 'back', thatch_color, [(8, 68), (70, 68), (8, 114), (70, 114)], salt=8694)
    log_pile(M, 60, 74, 76, 3, 4)
    M.models += [{'name': '水桶', 'source': 'summit-rocher-01m-barrel', 'at': [64, 104, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-門', (34.5, R[1], 21))
    M.anchor('door', 22, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'bakery', 'title': '麵包坊（共用：木板店面、木瓦兩坡頂、賣窗與櫃檯、麵包架、揉麵槽與麵粉袋；後院毛石台基上的圓頂麵包爐、茅草披棚、柴堆）',
            'use': 'bakery', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '店面、麵包爐與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 桶匠 8 × 12 m ───────────────────────────────
def cooper():
    """桶匠（cooper）：一座開敞的木瓦頂工棚（背面木板牆、牆上掛著一圈一圈的鐵箍）—— 棚下三個做到一半的桶：剛立起桶板、底下還張開的；
    裡面燒著小火讓桶板彎的；收好、上了箍的；還有刨桶板的削板凳（shaving horse）、桶板堆、做好的桶；後院一堆劈好的橡木料。
    - 照什麼：鎮民表沒有桶匠，可是糖、蘭姆、醃肉、火藥、水全都裝桶（TOWN_SIM 的配方：木 ⇒ 桶）。
      做桶的步驟（立桶板 raising、烤彎 firing、收箍）是歐洲桶匠的通法；17 世紀加勒比海桶匠鋪的樣子〔沒查到〕⇒ 棚與擺設是設計。"""
    X, Y, Z = 80, 120, 60
    M = Model((X, Y, Z))
    R = (6, 16, 74, 88)                                                # 棚 6.8 × 7.2 m
    M.box('body', R[0], R[1], 0, R[2], R[3], 1, EARTH_W)
    board_walls(M, (R[0], R[3] - 2, R[2], R[3]), 0, 24, 2, posts=False)   # 背面木板牆
    top = shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 26, 'p': 0.55, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=8695)
    roof_posts(M, top, [(R[0], R[1]), (38, R[1]), (R[2] - 2, R[1]), (R[0], 50), (R[2] - 2, 50), (R[0], R[3] - 4), (R[2] - 2, R[3] - 4)])
    for i, cx in enumerate((14, 26, 38, 50, 62)):                      # 背牆上的鐵箍（掛在釘上：圈頂貼著牆）
        ring_x(M, cx, R[3] - 3, 14, 4 + i % 2)
    # 三個做到一半的桶
    barrel_shell(M, 22, 40, 1, 9, 6.5, 4.8, gap=True, hoops=(7,))      # 剛立起來：底下張開
    barrel_shell(M, 44, 40, 1, 9, 5.0, 5.0, hoops=(1, 7))              # 烤彎：裡面燒小火
    M.box('body', 42, 38, 1, 47, 43, 2, EMBER, force=True)
    for (x, y) in ((41, 37), (46, 42)):
        M.box('body', x, y, 1, x + 1, y + 1, 3, IRON, force=True)      # 小火籃的腳
    for z in range(0, 9):                                              # 收好的桶（腰鼓起）
        r = 4.2 + 0.9 * math.sin(math.pi * (z + 0.5) / 9)
        for x in range(56, 72):
            for y in range(32, 48):
                d = math.hypot(x + 0.5 - 64, y + 0.5 - 40)
                if d <= r:
                    M.put('body', x, y, z, IRON if z in (1, 7) else (FRAME if d > r - 1 else BOARD))
    # 削板凳（一條斜的長凳＋夾木）、旁邊樹墩上的斧
    M.box('body', 12, 60, 4, 36, 64, 5, FRAME)
    for (x, y) in ((12, 60), (34, 60)):
        M.box('body', x, y, 0, x + 2, y + 4, 4, FRAME)
    M.box('body', 24, 60, 5, 32, 64, 7, BOARD)                         # 斜板
    M.box('body', 22, 61, 5, 24, 63, 12, FRAME)                        # 夾木（立在凳面上）
    for x in range(40, 47):
        for y in range(58, 65):
            if math.hypot(x + 0.5 - 43.5, y + 0.5 - 61.5) <= 3.2:
                M.box('body', x, y, 0, x + 1, y + 1, 5, LOG)
    # 桶板堆：一層沿 x、一層沿 y 交錯
    for k in range(5):
        if k % 2 == 0:
            for y in range(70, 82, 3):
                M.box('body', 48, y, k, 70, y + 2, k + 1, BOARD)
        else:
            for x in range(48, 70, 3):
                M.box('body', x, 70, k, x + 2, 82, k + 1, FRAME)
    # 後院：木柵、劈好的橡木料
    palisade(M, [(R[0], R[3]), (1, R[3]), (1, 118), (78, 118), (78, R[3]), (R[2] - 1, R[3])], gap={(x, 118) for x in range(34, 46)})
    log_pile(M, 6, 30, 94, 3, 4)
    log_pile(M, 50, 74, 94, 3, 4)
    M.models += [{'name': '桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, y, 1], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, (x, y) in enumerate(((12, 24), (24, 24), (60, 24), (12, 76)))]
    lantern(M, '燈籠-柱', (39, R[1], 18))
    M.anchor('door', 26, 8, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'cooper', 'title': '桶匠（共用：開敞的木瓦頂工棚、背牆掛鐵箍；三個做到一半的桶（立板、烤彎、上箍）、削板凳、桶板堆、做好的桶；後院橡木料）',
            'use': 'cooper', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '工棚與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 木工坊 8 × 12 m ───────────────────────────────
def carpenter():
    """木工坊（carpenter）：前院一座鋸木架（代鋸木坑，同船廠）、墊著隔條晾的板材堆；後面一間木板工坊，正面大開口，裡面長工作檯、
    台上的刨子與木料、後牆的工具架、磨刀石；後院原木堆。
    - 照什麼：鎮民表的木匠（船廠、修船、木工坊都去）；TOWN_SIM 的配方「木工坊」（木 ⇒ 家具、建材）。
      17 世紀加勒比海木工坊的樣子〔沒查到〕⇒ 配置是設計；鋸木架、原木堆借 ame 的船廠那一套。"""
    X, Y, Z = 80, 120, 70
    M = Model((X, Y, Z))
    saw_trestle(M, 14, 12)                                             # 前院：鋸木架（x 6..64、y 12..24）
    for k in range(6):                                                 # 晾板材：每層板之間一道隔條
        z = k
        if k % 2 == 0:
            M.box('body', 10, 28, z, 70, 38, z + 1, FLOOR)
        else:
            for x in (12, 38, 66):
                M.box('body', x, 28, z, x + 2, 38, z + 1, FRAME)
    R = (6, 44, 74, 98)                                                # 工坊 6.8 × 5.4 m
    board_walls(M, R, 0, 30, 2, bay=26)
    M.clear(14, R[1], 0, 66, R[1] + 2, 24)                             # 正面大開口（留上面一道楣）
    M.box('body', 14, R[1], 24, 66, R[1] + 2, 26, FRAME, force=True)
    M.box('body', R[0] + 2, R[1] + 2, 0, R[2] - 2, R[3] - 2, 1, FLOOR)
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 30, 0.7, z0=30)
    put_part(M, 'door-plank', '後-門', 'back', R, 60, 0, 2)
    put_part(M, 'window-board', '左-窗', 'left', R, 71, 9, 2)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.7, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=8696)
    # 長工作檯（靠後牆）、台上一塊板與刨子、台鉗木柱
    trestle_table(M, 10, 50, 82, 92, 8)
    M.box('body', 14, 84, 9, 40, 90, 10, BOARD)
    M.box('body', 26, 86, 10, 31, 88, 12, FRAME)                       # 刨子
    M.box('body', 46, 82, 9, 49, 85, 13, FRAME)                        # 木台鉗
    # 後牆的工具架：一根橫木、掛鋸與鑿
    M.box('body', 10, 95, 18, 52, 96, 19, FRAME)
    for i, x in enumerate(range(12, 50, 6)):
        M.box('body', x, 95, 11 if i % 2 else 13, x + (4 if i % 2 else 1), 96, 18, IRON if i % 2 else FRAME)
    # 磨刀石：木架上一個立著的圓石（x–z 平面）、搖把
    for x in (56, 66):
        M.box('body', x, 70, 0, x + 2, 72, 12, FRAME)
    for r in (1.5, 2.5, 3.5, 4.5):
        ring_x(M, 62, 71, 12, r, RUBBLE)
    M.box('body', 58, 71, 11, 66, 72, 13, IRON, force=True)            # 軸
    M.box('body', 66, 71, 12, 68, 72, 16, IRON, force=True)            # 搖把
    # 後院：木柵、原木堆
    palisade(M, [(R[0], R[3]), (1, R[3]), (1, 118), (78, 118), (78, R[3]), (R[2] - 1, R[3])], gap={(x, 118) for x in range(34, 46)})
    log_pile(M, 6, 72, 102, 3, 4)
    lantern(M, '燈籠-楣', (40, R[1], 20))
    M.anchor('door', 40, 40, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'carpenter', 'title': '木工坊（共用：前院鋸木架與晾板堆；木板工坊正面大開口、長工作檯與刨子、工具架、磨刀石；後院原木堆）',
            'use': 'carpenter', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '工坊與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 過磅所 10 × 8 m ───────────────────────────────
def weighhouse():
    """過磅所（weighhouse）：碼頭邊一座開敞的秤棚 —— 六根柱、木瓦兩坡頂、架高一級的木板地台；正中一根粗橫梁吊著大天平（鐵橫桿、兩只用鐵鍊吊的方木盤，
    一邊擺糖桶、一邊疊砝碼）、砝碼架；右後一間書記的小屋（木板門、窗、寫帳的桌）；地台邊等著過秤的糖桶與袋。
    - 照什麼：法屬島上「倉庫之間總有一間漂亮的 case 當皇家秤房」，所有貨物要先在那裡過秤（DT2 p.452）；Martinique 各區「都有一處專門過秤的地方」（DT2）；
      過秤日商人帶帳本到場、法官監督（DT2 p.461）〔讀過；ame research_civic.md §6〕。
      秤具的形式〔沒查到〕（法屬原典沒寫）⇒ 吊在梁下的大天平是設計；ame 的海關（carib-customs）已經是那間秤房 ⇒ 這一件是碼頭邊的公秤棚，給沒有海關的
      地方或大港多一處秤。"""
    X, Y, Z = 100, 80, 60
    M = Model((X, Y, Z))
    R = (6, 8, 94, 56)                                                 # 棚 8.8 × 4.8 m
    M.box('body', R[0], R[1], 0, R[2], R[3], 2, FLOOR)                 # 地台（0.2 m）
    M.box('body', R[0], R[1], 0, R[2], R[1] + 1, 2, FRAME)
    top = shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 34, 'p': 0.55, 'over': (3, 3, 4, 4), 'gable': 'x'}], salt=8697)
    roof_posts(M, top, [(R[0], R[1]), (49, R[1]), (R[2] - 2, R[1]), (R[0], R[3] - 2), (49, R[3] - 2), (R[2] - 2, R[3] - 2)], z0=2)
    for y in (R[1], R[3] - 2):                                         # 柱頭的縱梁
        M.box('body', R[0], y, 32, R[2], y + 2, 34, FRAME)
    M.box('body', 49, R[1], 30, 51, R[3], 32, FRAME)                   # 正中的粗橫梁（吊天平）
    # 大天平：吊帶、鐵橫桿（長 5 m）、兩只鐵鍊吊的方木盤
    M.box('body', 49, 31, 26, 51, 33, 30, IRON)
    M.box('body', 24, 31, 25, 76, 33, 26, IRON)
    M.box('body', 49, 31, 18, 51, 32, 25, IRON)                        # 指針（往下）
    for cx in (26, 74):
        for (dx, dy) in ((-6, -6), (5, -6), (-6, 5), (5, 5)):
            rope_line(M, (cx + 0.5, 32.5, 25), (cx + dx + 0.5, 32 + dy + 0.5, 7), IRON)
        M.box('body', cx - 7, 25, 5, cx + 7, 39, 7, FRAME)            # 方木盤（離地台 0.3 m）
    for (x, z, w) in ((70, 7, 8), (71, 9, 6), (72, 11, 4)):           # 右盤上疊砝碼
        M.box('body', x, 29, z, x + w, 35, z + 2, IRON)
    # 砝碼架（左前）：一張矮桌、上面一排由大到小的砝碼
    trestle_table(M, 10, 22, 14, 20, 6)
    for i, x in enumerate(range(11, 21, 3)):
        M.box('body', x, 15, 7, x + 2, 19, 7 + 4 - i, IRON)
    # 書記的小屋（右後，地塊後半）
    S = (64, 58, 96, 78)
    board_walls(M, S, 0, 26, 2)
    put_part(M, 'door-plank', '書記-門', 'left', S, 68, 0, 2)
    put_part(M, 'window-board', '書記-窗', 'back', S, 80, 9, 2)
    shingle_roof(M, [{'x0': S[0], 'y0': S[1], 'x1': S[2], 'y1': S[3], 'ze': 26, 'p': 0.6, 'over': (2, 2, 2, 2)}], salt=8698)
    trestle_table(M, 76, 92, 64, 70, 8)
    M.box('body', 80, 65, 9, 86, 69, 10, SACK)                         # 攤開的帳本
    # 地台邊等著過秤的袋（左後）
    for (x, y) in ((10, 60), (17, 60), (24, 60), (13, 66), (20, 66)):
        for z in range(0, 6):
            M.box('body', x, y, z, x + 6, y + 5, z + 1, SACK if z < 5 else MORTAR)
    M.models += [{'name': '糖桶-盤上', 'source': 'summit-rocher-01m-barrel', 'at': [26, 32, 7], 'pivot': [6, 6, 0], 'meta': {}}] + \
                [{'name': '糖桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, y, 2], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, (x, y) in enumerate(((60, 46), (84, 18), (84, 46)))] + \
                [{'name': '糖桶-台外-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, y, 0], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, (x, y) in enumerate(((40, 66), (52, 66)))]
    lantern(M, '燈籠-柱', (50, R[1], 26))
    M.anchor('door', 50, 4, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'weighhouse', 'title': '過磅所（共用：碼頭邊開敞的秤棚、木瓦兩坡頂、木板地台；梁下的大天平與兩只吊盤、砝碼架；書記的小屋；等著過秤的糖桶與袋）',
            'use': 'weighhouse', 'lot': (10, 8), 'M': M, 'style': 'common', 'layers': {'body': '棚、天平與擺設', 'roof': '屋頂'}}


ALL = [weighhouse, smithy, bakery, cooper, carpenter]
