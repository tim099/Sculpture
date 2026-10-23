# 城鎮共用建築第七批（TASK-0872；Tim 2026-10-24「接著繼續完成手上的task吧 GO」）—— 剩下的四種工坊：蒸餾坊、製革坊、織布坊、鋸木坊（全部共用 common）。
# 工具同 workshops.py（第六批：roof_posts、ring_x、barrel_shell ＋ town3／quay／harbour／civic／carib 的全部）。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 地塊 ＝ 住宅那一格 8 × 12 m（TOWN_BUILD §1.1.5）；開場不擺（§1.1.10 第 4 題）⇒ 建築模式「🔨 工坊」蓋。
# 配方（TOWN_SIM §4）：蒸餾坊 糖蜜 ⇒ 蘭姆酒；製革（牧場的牛皮 ⇒ 皮革）；織坊 棉花 ⇒ 帆布；鋸木坊 原木 ⇒ 木板。
# 史料：作品 references/README.md 第七批那一節；查不到的都寫「設計」。
from workshops import *                                                # noqa: F401,F403
from townpub import BARK                                               # noqa: E402

COPPER = 173                     # 蒸餾器的銅（偏紅的褐）
WASH = 140                       # 槽裡發酵的糖渣沫（金褐）
LIQUOR = 68                      # 鞣液（深褐）
HIDE = 141                       # 生皮（灰褐）
CLOTH = SACK                     # 帆布（米白）
COTTON = LIME                    # 棉花（白）
SAWDUST = 213                    # 木屑（土黃）
TUB_WATER = 46                   # 冷卻桶的水（同 civic 的泉水）


def tub(M, cx, cy, z0, h, r, fill, layer='body'):
    """敞口的木桶、木槽（圓）：桶板一圈（同 barrel_shell）、上下兩道鐵箍；裡面從底到頂下一格裝滿 fill（⛔ 不留空 ⇒ 沒有封閉空腔）。"""
    barrel_shell(M, cx, cy, z0, h, r, r, hoops=(1, h - 2), layer=layer)
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) < r - 1:
                M.box(layer, x, y, z0, x + 1, y + 1, z0 + h - 1, fill)


def rod(M, a, b, rad, color=LOG, end=LOG_TIP, layer='body'):
    """一根任意方向的圓木：離線段 a → b 不到 rad 的格都填（⛔ quay 的 spar 截面畫在水平面 ⇒ 只適合直立的桅杆，躺著的會變成一片板）；
    兩端那一層換淺色的截面（同原木堆的端面）。"""
    ax, ay, az = a
    dx, dy, dz = b[0] - ax, b[1] - ay, b[2] - az
    L2 = dx * dx + dy * dy + dz * dz
    R = int(math.ceil(rad)) + 1
    for x in range(int(min(ax, b[0])) - R, int(max(ax, b[0])) + R + 1):
        for y in range(int(min(ay, b[1])) - R, int(max(ay, b[1])) + R + 1):
            for z in range(int(min(az, b[2])) - R, int(max(az, b[2])) + R + 1):
                px, py, pz = x + 0.5 - ax, y + 0.5 - ay, z + 0.5 - az
                t = (px * dx + py * dy + pz * dz) / L2
                if not 0 <= t <= 1:
                    continue
                if (px - t * dx) ** 2 + (py - t * dy) ** 2 + (pz - t * dz) ** 2 <= rad * rad:
                    tip = t * math.sqrt(L2) < 1 or (1 - t) * math.sqrt(L2) < 1
                    M.put(layer, x, y, z, end if tip else color, force=True)


def pot_still(M, cx, cy, z0, layer='body'):
    """銅的壺式蒸餾器（alembic）：鼓起的鍋身、收窄的頸、頂上一個小圓頭（helm）；實心（看不到裡面）。回傳頭頂那一格的 z。"""
    prof = [5.5, 6.5, 7.0, 7.0, 6.8, 6.3, 5.5, 4.4, 3.0, 2.2, 2.2, 3.2, 3.6, 3.2, 2.0]
    for dz, r in enumerate(prof):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for y in range(int(cy - r - 1), int(cy + r + 2)):
                if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                    M.put(layer, x, y, z0 + dz, COPPER, force=True)
    return z0 + len(prof) - 1


def hides_hung(M, x0, x1, y, z1, n, layer='body'):
    """橫桿上掛的皮：每張一格厚、寬 w、從桿下往下垂（長短不一），顏色在生皮與鞣好的皮之間換。"""
    w = (x1 - x0) // n
    for i in range(n):
        h = 10 + int(h01('hide', x0, y, i) * 5)
        M.box(layer, x0 + i * w + 1, y, z1 - h, x0 + (i + 1) * w - 1, y + 1, z1, HIDE if i % 2 else LEATHER)


# ─────────────────────────────── 蒸餾坊 8 × 12 m ───────────────────────────────
def distillery():
    """蒸餾坊（distillery／still-house）：毛石牆、木瓦兩坡頂的蒸餾房 —— 後牆邊一座毛石爐台，台上兩座銅的壺式蒸餾器（爐門朝前、紅的火），
    爐台後面一根毛石煙囪穿出屋頂；左前一口毛石砌的渣沫槽（放到發酸才蒸）、右前兩個發酵的木槽；銅管從蒸餾器頭穿過後牆，
    接到後院茅草棚下兩個冷卻的木桶（桶裡盤著銅管、出口接酒桶）；院裡的酒桶、柴堆。
    - 照什麼：Ligon 1657（巴貝多）：糖莊裡有一間 Still-house，「兩座 Still」、接酒的 receivers；渣沫存在 Cistern 裡「放到開始發酸」才蒸（不酸，酒氣上不來）；
      蒸第二次出最烈的酒，叫 kill-devil〔讀過：pp.84 圖例 R、S、X、Y，pp.92–93，p.112〕。
      爐台、蒸餾器的形狀、冷卻桶（worm tub）〔沒查到 17 世紀的圖〕⇒ 照壺式蒸餾的通法（設計）；鎮民表、配方的蒸餾坊是城裡的一間，不是糖莊那一套。"""
    X, Y, Z = 80, 120, 80
    M = Model((X, Y, Z))
    R = (6, 10, 74, 70)                                                # 蒸餾房 6.8 × 6 m
    rubble_walls(M, R, 0, 28, 4, salt=8721)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 1, EARTH_W)
    for x0, x1 in ((R[0], R[0] + 4), (R[2] - 4, R[2])):               # 兩端的山牆（先砌 ⇒ 屋面蓋過牆頂）
        end_gable(M, x0, x1, R[1], R[3], 28, 0.6, z0=28, color=RUBBLE, edge=RUBBLE_D)
    put_part(M, 'door-plank', '前-門', 'front', R, 40, 0, 4)
    put_part(M, 'window-board', '前-窗-左', 'front', R, 18, 10, 4)
    put_part(M, 'window-board', '前-窗-右', 'front', R, 62, 10, 4)
    put_part(M, 'window-board', '右-窗', 'right', R, 30, 10, 4)
    top = shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 28, 'p': 0.6, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=8722)
    # 爐台（後牆邊，高 1 m）：每座蒸餾器底下一個爐門（朝前、裡面紅的火）
    M.box('body', 10, 44, 0, 70, 66, 10, RUBBLE)
    stills = (24, 54)
    for cx in stills:
        M.clear(cx - 3, 44, 2, cx + 3, 48, 7)
        M.box('body', cx - 3, 48, 2, cx + 3, 49, 7, EMBER, force=True)
        M.box('body', cx - 4, 43, 7, cx + 4, 44, 8, IRON, force=True)  # 爐門上的鐵楣
    # 煙囪：爐台後面、兩座蒸餾器中間，從爐台頂穿過屋頂
    zc = max(top[(x, y)] for x in range(35, 45) for y in range(60, 70)) + 7
    M.box('body', 35, 60, 10, 45, 70, zc, RUBBLE, force=True)
    M.box('body', 34, 59, zc - 2, 46, 71, zc, MORTAR, force=True)
    M.box('body', 38, 63, zc - 2, 42, 67, zc, CHAR, force=True)
    M.anchor('smoke', 40, 65, zc - 1)
    # 兩座蒸餾器、頭上的銅管（往後穿過後牆、往下斜到冷卻桶）
    for cx in stills:
        zt = pot_still(M, cx + 0.5, 54.5, 10)
        rope_line(M, (cx + 0.5, 54.5, zt), (cx + 0.5, 63.5, zt - 1), COPPER)
        rope_line(M, (cx + 0.5, 63.5, zt - 1), (cx + 0.5, 80.5, 17.5), COPPER)
    # 左前：毛石渣沫槽（Ligon 的 Cistern；裝到離槽口一格）
    M.box('body', 10, 16, 0, 30, 38, 8, RUBBLE)
    M.box('body', 12, 18, 1, 28, 36, 7, WASH, force=True)
    M.box('body', 12, 18, 7, 28, 36, 8, WASH, force=True)
    M.box('body', 12, 18, 7, 28, 19, 8, RUBBLE, force=True)
    # 右前：兩個發酵的木槽
    for cy in (22, 34):
        tub(M, 62, cy, 1, 9, 5.5, WASH)
    # 後院：茅草棚下兩個冷卻桶（裡面盤著銅管：水面上露一圈）、出口的短管
    lean_roof_posts(M, 6, 72, 74, 100, 40, 0.25, 'back', thatch_color, [(8, 74), (70, 74), (8, 96), (70, 96)], salt=8723)
    for cx in stills:
        tub(M, cx + 0.5, 84.5, 0, 17, 7, TUB_WATER)
        ring = [(x, y) for x in range(cx - 6, cx + 7) for y in range(78, 91) if 3.2 <= math.hypot(x + 0.5 - cx - 0.5, y + 0.5 - 84.5) <= 4.3]
        for (x, y) in ring:
            M.put('body', x, y, 16, COPPER, force=True)
        M.box('body', cx, 91, 3, cx + 1, 95, 4, COPPER, force=True)    # 出口（接院裡的酒桶）
    log_pile(M, 6, 26, 102, 3, 4)
    palisade(M, [(R[0], R[3]), (1, R[3]), (1, 118), (78, 118), (78, R[3]), (R[2] - 1, R[3])], gap={(x, 118) for x in range(34, 46)})
    M.models += [{'name': '接酒桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [cx - 5, 95, 0], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, cx in enumerate(stills)] + \
                [{'name': '酒桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, y, z], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, (x, y, z) in enumerate(((44, 104, 0), (56, 104, 0), (68, 104, 0), (50, 16, 1)))]
    lantern(M, '燈籠-門', (52, R[1], 20))
    M.anchor('door', 40, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'distillery', 'title': '蒸餾坊（共用：毛石的蒸餾房、木瓦兩坡頂；爐台上兩座銅蒸餾器、毛石煙囪、渣沫槽、發酵木槽；後院茅草棚下的冷卻桶與接酒桶、柴堆）',
            'use': 'distillery', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '蒸餾房與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 製革坊 8 × 12 m ───────────────────────────────
def tannery():
    """製革坊（tannery）：臨路一間木板的刮皮房（beam house：斜放的刮皮木、木凳、窗），旁邊兩口白的石灰池（脫毛）；
    中間一座開敞的木瓦頂棚，棚下兩排六口木框的鞣池（深褐的鞣液、浮著幾張皮）、池間的踏板；後院兩道晾皮的橫桿、樹皮堆（鞣料）。
    - 照什麼：英國的製革坊：刮皮房（beam house，去肉去毛）、泡皮與石灰的長方池、鞣皮的方池、磨樹皮的地方（Rhayader、Newcastle、Birely 的遺址紀錄）；
      1623 年 Northamptonshire 的紀錄「tanne howses and tanne fatts」與石灰池〔摘：各地的史蹟紀錄〕。
      池子本來挖在地裡 ⇒ 地面挖不下去，改成矮的石框、木框池（同 ame 的船廠把鋸木坑改成鋸木架）；17 世紀加勒比海的製革坊〔沒查到〕⇒ 配置是設計。
      有污水 ⇒ 生成器要放下游、下風（TOWN_BUILD §1.1.3、§1.1.5）—— 開場不擺，建築模式蓋的時候由玩家挑地方。"""
    X, Y, Z = 80, 120, 60
    M = Model((X, Y, Z))
    # 刮皮房（左前，3.4 × 3.4 m）
    B = (6, 8, 40, 42)
    board_walls(M, B, 0, 26, 2)
    M.box('body', B[0] + 2, B[1] + 2, 0, B[2] - 2, B[3] - 2, 1, FLOOR)
    put_part(M, 'door-plank', '刮皮房-門', 'front', B, 22, 0, 2)
    put_part(M, 'window-board', '刮皮房-窗', 'right', B, 26, 9, 2)
    shingle_roof(M, [{'x0': B[0], 'y0': B[1], 'x1': B[2], 'y1': B[3], 'ze': 26, 'p': 0.6, 'over': (2, 2, 3, 2), 'gable': 'x'}], salt=8731)
    for x0, x1 in ((B[0], B[0] + 2), (B[2] - 2, B[2])):
        end_gable(M, x0, x1, B[1], B[3], 26, 0.6, z0=26)
    # 刮皮木：半圓的木頭斜架在兩隻腳上（低的一頭著地）、上面搭一張皮
    rod(M, (11, 30.5, 2.5), (30, 30.5, 10.5), 2.2)
    M.box('body', 27, 29, 0, 29, 31, 8, FRAME)                        # 高的一頭的腳
    for x in range(18, 29):                                            # 皮只搭在木頭上（⛔ 伸出木頭的那一截會浮空）
        zt = int(1.5 + (x + 0.5 - 11) * 8 / 19) + 3
        M.box('body', x, 27, zt - 1, x + 1, 34, zt, HIDE, force=True)
        if x == 18:
            M.box('body', x, 27, 1, x + 1, 34, zt, HIDE, force=True)  # 垂到地上的那一頭
    bench(M, 10, 22, 14, 18)
    # 石灰池兩口（右前）：毛石框、裡面白的石灰水
    for x0 in (46, 61):
        M.box('body', x0, 12, 0, x0 + 13, 38, 6, RUBBLE)
        M.box('body', x0 + 2, 14, 1, x0 + 11, 36, 6, LIME, force=True)
    # 鞣池棚：六根柱、木瓦兩坡頂；兩排三口木框的鞣池
    S = (6, 48, 74, 94)
    top = shingle_roof(M, [{'x0': S[0], 'y0': S[1], 'x1': S[2], 'y1': S[3], 'ze': 26, 'p': 0.5, 'over': (2, 2, 3, 3), 'gable': 'x'}], salt=8732)
    roof_posts(M, top, [(S[0], S[1]), (39, S[1]), (S[2] - 2, S[1]), (S[0], S[3] - 2), (39, S[3] - 2), (S[2] - 2, S[3] - 2)])
    M.box('body', S[0], S[1], 0, S[2], S[3], 1, BOARD)                # 池間的踏板
    for i, x0 in enumerate((9, 30, 51)):
        for j, y0 in enumerate((53, 73)):
            M.box('body', x0, y0, 1, x0 + 19, y0 + 17, 6, FRAME)
            M.box('body', x0 + 2, y0 + 2, 1, x0 + 17, y0 + 15, 6, LIQUOR, force=True)
            if (i + j) % 2 == 0:                                       # 浮著的皮
                M.box('body', x0 + 4, y0 + 4, 5, x0 + 12, y0 + 11, 6, HIDE, force=True)
    # 後院：晾皮的兩道橫桿（四根柱）、樹皮堆（一層一層交錯）
    for (px, py) in ((8, 100), (44, 100), (8, 112), (44, 112)):
        M.box('body', px, py, 0, px + 2, py + 2, 24, FRAME)
    for py in (100, 112):
        M.box('body', 8, py, 22, 46, py + 1, 24, FRAME)
        hides_hung(M, 10, 44, py + 1, 23, 4)
    for k in range(7):
        if k % 2 == 0:
            for y in range(98, 116, 3):
                M.box('body', 52, y, k, 74, y + 2, k + 1, BARK)
        else:
            for x in range(52, 74, 3):
                M.box('body', x, 98, k, x + 2, 116, k + 1, LOG_D)
    palisade(M, [(S[0], S[3]), (1, S[3]), (1, 118), (78, 118), (78, S[3]), (S[2] - 1, S[3])], gap={(x, 118) for x in range(30, 40)})
    M.models += [{'name': '水桶', 'source': 'summit-rocher-01m-barrel', 'at': [44, 42, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-柱', (40, S[1], 18))
    M.anchor('door', 22, B[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'tannery', 'title': '製革坊（共用：木板的刮皮房與刮皮木、兩口石灰池；開敞的棚下六口鞣池；後院晾皮的橫桿、樹皮堆）',
            'use': 'tannery', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '刮皮房、池與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 織布坊 8 × 12 m ───────────────────────────────
def loom(M, x0, y0, layer='body'):
    """一台腳踏織機（框 20 × 18 格）：四根柱、兩側頂梁與一道橫梁、前面的胸梁與卷布軸、後面的經軸；經線一根隔一根拉在兩梁之間，
    綜框吊在橫梁下、腳底兩塊踏板；前面一張織工坐的凳。"""
    for (x, y) in ((x0, y0), (x0 + 18, y0), (x0, y0 + 16), (x0 + 18, y0 + 16)):
        M.box(layer, x, y, 0, x + 2, y + 2, 18, FRAME)
    for x in (x0, x0 + 18):
        M.box(layer, x, y0, 16, x + 2, y0 + 18, 18, FRAME)            # 兩側頂梁
    M.box(layer, x0, y0 + 8, 16, x0 + 20, y0 + 10, 18, FRAME)          # 橫梁（吊綜框）
    M.box(layer, x0, y0, 8, x0 + 20, y0 + 2, 10, FRAME)                # 胸梁
    M.box(layer, x0 + 2, y0 + 2, 5, x0 + 18, y0 + 4, 7, CLOTH)         # 卷布軸上已經織好的布
    M.box(layer, x0, y0 + 2, 5, x0 + 2, y0 + 4, 8, FRAME)
    M.box(layer, x0 + 18, y0 + 2, 5, x0 + 20, y0 + 4, 8, FRAME)
    M.box(layer, x0, y0 + 14, 7, x0 + 20, y0 + 16, 10, LOG)            # 經軸
    for x in range(x0 + 3, x0 + 17):
        if x % 2:
            M.box(layer, x, y0 + 2, 9, x + 1, y0 + 14, 10, CLOTH)      # 經線
    M.box(layer, x0 + 2, y0 + 8, 10, x0 + 18, y0 + 9, 16, FRAME)       # 綜框（吊在橫梁下）
    for x in (x0 + 6, x0 + 12):
        M.box(layer, x, y0 + 5, 1, x + 2, y0 + 12, 2, BOARD)           # 踏板
        M.box(layer, x, y0 + 11, 0, x + 2, y0 + 12, 1, FRAME)
    bench(M, x0 + 4, x0 + 16, y0 - 5, y0 - 2)


def weaver():
    """織布坊（weaver）：一間木板屋、木瓦兩坡頂，四面開窗（織布要亮）—— 屋裡兩台腳踏織機、紡車、右牆的整經架、後面桌上一捲一捲的帆布、門邊的棉花包；
    後門出去是曬布的草地：三幅帆布攤在草上、四角釘著木樁。
    - 照什麼：TOWN_SIM 的配方「織坊」（棉花 ⇒ 帆布，修船要用）、鎮民表；腳踏織機、紡車、整經、草地曬白是歐洲的通法。
      17 世紀加勒比海城裡的織坊〔沒查到〕⇒ 配置是設計。"""
    X, Y, Z = 80, 120, 70
    M = Model((X, Y, Z))
    R = (6, 12, 74, 76)                                                # 6.8 × 6.4 m
    board_walls(M, R, 0, 30, 2, bay=26)
    M.box('body', R[0] + 2, R[1] + 2, 0, R[2] - 2, R[3] - 2, 1, FLOOR)
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 30, 0.7, z0=30)
    put_part(M, 'door-plank', '前-門', 'front', R, 20, 0, 2)
    for i, c in enumerate((40, 62)):                                   # 窗框連百葉寬 2 m ⇒ 中心隔 22 格
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, c, 9, 2)
    for i, c in enumerate((32, 56)):
        put_part(M, 'window-board', '右-窗%d' % (i + 1), 'right', R, c, 9, 2)
        put_part(M, 'window-board', '左-窗%d' % (i + 1), 'left', R, c, 9, 2)
    put_part(M, 'door-plank', '後-門（往曬布場）', 'back', R, 58, 0, 2)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.7, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=8741)
    loom(M, 10, 32)
    loom(M, 42, 32)
    # 紡車（左後）：木台、兩根立柱夾著輪軸、立著的輪（x–z 平面）
    M.box('body', 10, 60, 4, 26, 66, 6, FRAME)
    for (x, y) in ((10, 60), (24, 60), (10, 64), (24, 64)):
        M.box('body', x, y, 0, x + 2, y + 2, 4, FRAME)
    for y in (61, 64):
        M.box('body', 17, y, 6, 19, y + 1, 13, FRAME)
    M.box('body', 17, 61, 11, 19, 65, 13, IRON, force=True)            # 輪軸
    ring_x(M, 18, 62, 12, 5.5, FRAME)
    ring_x(M, 18, 63, 12, 5.5, FRAME)
    for a in range(4):
        t = a * math.pi / 4
        rope_line(M, (18 + 0.5 - 5 * math.cos(t), 62.5, 12.5 - 5 * math.sin(t)), (18 + 0.5 + 5 * math.cos(t), 62.5, 12.5 + 5 * math.sin(t)), FRAME)
    # 右牆的整經架：兩根立柱、三道橫木（靠牆）
    for y in (40, 68):
        M.box('body', 70, y, 1, 72, y + 2, 26, FRAME)
    for z in (8, 14, 20):
        M.box('body', 71, 40, z, 72, 70, z + 1, FRAME)
        M.box('body', 70, 42, z - 2, 71, 68, z - 1, CLOTH)                # 繞在架上的紗
    # 後牆邊：一張桌、桌上三捲帆布；門邊的棉花包（繩捆）
    trestle_table(M, 32, 52, 64, 72, 8)
    for i, (x, z) in enumerate(((34, 9), (42, 9), (38, 13))):
        M.box('body', x, 65, z, x + 8, 71, z + 4, CLOTH)
        M.box('body', x, 65, z, x + 1, 71, z + 4, BOARD_D)             # 捲的端面
    for (x, y, z) in ((50, 16, 1), (60, 16, 1), (55, 16, 9)):
        M.box('body', x, y, z, x + 9, y + 8, z + 8, COTTON)
        M.box('body', x + 4, y, z, x + 5, y + 8, z + 8, ROPE, force=True)
    # 後院：曬布的草地、三幅攤開的帆布、四角的木樁；木柵
    M.box('body', 2, 78, 0, 78, 117, 1, GRASS)
    for y0 in (82, 92, 102):
        M.box('body', 10, y0, 1, 70, y0 + 7, 2, CLOTH)
        for (x, y) in ((9, y0), (70, y0), (9, y0 + 6), (70, y0 + 6)):
            M.box('body', x, y, 1, x + 1, y + 1, 3, FRAME)
    palisade(M, [(R[0], R[3]), (1, R[3]), (1, 118), (78, 118), (78, R[3]), (R[2] - 1, R[3])], gap={(x, 118) for x in range(34, 46)})
    lantern(M, '燈籠-門', (30, R[1], 21))
    M.anchor('door', 20, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'weaver', 'title': '織布坊（共用：四面開窗的木板屋、木瓦兩坡頂；兩台腳踏織機、紡車、整經架、帆布捲與棉花包；後院曬布的草地）',
            'use': 'weaver', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '屋與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 鋸木坊 8 × 12 m ───────────────────────────────
def sawmill():
    """鋸木坊（sawmill）：一座開敞的長棚、屋脊順著進深（木瓦兩坡頂、八根柱）—— 棚正中架高的鋸台（兩座粗木架，代鋸木坑）、台上一根原木，
    前半已經鋸成板（看得到鋸縫）、中間一把立著的長鋸（上下兩個握把：上面的人站在木頭上、下面的人站在台下）、台下一堆木屑、靠台的梯子；
    左邊墊隔條晾的板材堆、右邊墊木上等著鋸的第二根原木與廢邊料；後院原木堆。
    - 照什麼：鋸木坑（saw pit）：兩個人上下拉長鋸、上面的人（top sawyer）站在木頭上沿墨線帶鋸、下面的人在坑裡；鋸好的木料最大的用家是造船〔摘：Wikipedia Saw pit、Whipsaw〕。
      地面挖不下去 ⇒ 坑改成架高的鋸台（同 ame 船廠的鋸木架）；比木工坊前院那一座大、自己一座棚 ⇒ 鋸木坊整間就做這件事。
      17 世紀加勒比海城裡的鋸木坊〔沒查到〕（水力、風力鋸木廠在北美、歐洲才有）⇒ 配置是設計。"""
    X, Y, Z = 80, 120, 80
    M = Model((X, Y, Z))
    S = (6, 14, 74, 94)                                                # 棚 6.8 × 8 m
    M.box('body', S[0], S[1], 0, S[2], S[3], 1, EARTH_W)
    top = shingle_roof(M, [{'x0': S[0], 'y0': S[1], 'x1': S[2], 'y1': S[3], 'ze': 32, 'p': 0.6, 'over': (3, 3, 3, 3), 'gable': 'y'}], salt=8751)
    roof_posts(M, top, [(x, y) for x in (S[0], S[2] - 2) for y in (S[1], 40, 66, S[3] - 2)])
    for x in (S[0], S[2] - 2):                                         # 柱頭的縱梁
        M.box('body', x, S[1], 30, x + 2, S[3], 32, FRAME)
    # 鋸台：兩座粗木架（頂 1.6 m）、台上的原木（沿 y）
    for y0 in (26, 76):
        for (x, y) in ((30, y0), (48, y0), (30, y0 + 6), (48, y0 + 6)):
            M.box('body', x, y, 0, x + 2, y + 2, 15, FRAME)
        M.box('body', 30, y0, 15, 50, y0 + 8, 16, FRAME)
        M.box('body', 30, y0, 4, 50, y0 + 1, 6, FRAME)                 # 下面的橫撐
    rod(M, (40.5, 58, 20.5), (40.5, 88, 20.5), 4.5)                   # 還沒鋸的那一半（躺在兩座木架上：底 16）
    M.box('body', 36, 20, 16, 45, 58, 25, LOG)                         # 鋸成板的那一半（方料）
    for x in (38, 41):
        M.box('body', x, 20, 17, x + 1, 57, 25, DARK, force=True)      # 鋸縫
    M.box('body', 36, 20, 16, 45, 21, 25, LOG_TIP, force=True)         # 端面
    # 長鋸：立在鋸好與沒鋸的交界（y 57）、上下握把
    M.box('body', 40, 57, 4, 41, 59, 40, IRON, force=True)
    M.box('body', 37, 57, 38, 44, 59, 40, FRAME, force=True)           # 上握把（tiller）
    M.box('body', 38, 57, 4, 43, 59, 6, FRAME, force=True)             # 下握把（box）
    # 台下的木屑堆、靠台的梯子
    for x in range(30, 52):
        for y in range(48, 68):
            h = int(3 - 0.35 * math.hypot(x + 0.5 - 40.5, y + 0.5 - 58))
            if h > 0:
                M.box('body', x, y, 1, x + 1, y + 1, 1 + h, SAWDUST)
    for k in range(9):                                                 # 梯子：從地面斜靠到鋸台（兩根梯柱、每 0.2 m 一級）
        y = 34 + k
        z = k * 2
        for x in (51, 55):
            M.box('body', x, y, z, x + 1, y + 1, z + 3, FRAME, force=True)
        if k % 2 == 0:
            M.box('body', 51, y, z + 1, 56, y + 1, z + 2, FRAME, force=True)
    M.box('body', 50, 34, 15, 51, 43, 17, FRAME, force=True)           # 梯頂搭在鋸台上
    # 左邊：墊隔條晾的板材堆（沿 y）
    for k in range(8):
        if k % 2 == 0:
            M.box('body', 10, 20, k, 26, 88, k + 1, FLOOR)
        else:
            for y in (21, 44, 66, 86):
                M.box('body', 10, y, k, 26, y + 2, k + 1, FRAME)
    # 右邊：墊木上等著鋸的原木、廢邊料（slab）斜靠在柱上
    for y in (30, 76):
        M.box('body', 58, y, 0, 70, y + 3, 3, FRAME)
    rod(M, (64.5, 24, 6.5), (64.5, 84, 6.5), 3.6)                     # 墊木頂 3
    for i in range(4):
        M.box('body', 70 - i * 2, 41 + i, 0, 72 - i * 2, 43 + i, 18 - i * 3, BOARD)
    # 後院：原木堆
    log_pile(M, 6, 74, 97, 3, 5)
    M.models += [{'name': '水桶', 'source': 'summit-rocher-01m-barrel', 'at': [58, 6, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-柱', (8, S[1] + 1, 22))
    M.anchor('door', 40, 8, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'sawmill', 'title': '鋸木坊（共用：開敞的長棚、木瓦兩坡頂；架高的鋸台與長鋸（代鋸木坑）、鋸了一半的原木、木屑堆、梯子；晾板材堆、等著鋸的原木；後院原木堆）',
            'use': 'sawmill', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '棚、鋸台與擺設', 'roof': '屋頂'}}


ALL = [distillery, tannery, weaver, sawmill]
