# 共用的船廠類（風格 common；TASK-0772 第二段）：小船廠、大船廠、製繩場 —— 史料 references/research_civic.md §10.1（Port Royal 本地造 sloop）、
# TOWN_BUILD §1.1.7（Havana Real Arsenal、English Harbour、製繩場的長度）。造船場的位置、規模、設施都沒查到 ⇒ 配置與尺寸全是設計。
# 座標同 civic.py（x 臨路寬、y 進深 y 0 臨路、z 往上；0.1 m／格）；背面（y 大）多半朝水 ⇒ 船台往背面斜下去。
from civic import *
from harbour import capstan, rope_coil, log_pile, tar_kettle, tool_shed, ROPE, EMBER


def hull_frame(M, cx, ys0, ys1, beam, depth, z_front, z_back, plank=0.4, layer='body'):
    """船台上的船骨架：龍骨（沿 y，從 z_front 斜到 z_back）、每 1 m 一道肋骨（酒杯形：半寬 ＝ 船寬一半 × √(高 ÷ 深)，兩端收窄）、
    艏柱與艉柱、下面 plank 那一段已經釘上船殼板；龍骨底下每 2 m 一個龍骨墩。"""
    L = ys1 - ys0

    def zk(y):
        return int(round(z_front + (z_back - z_front) * (y - ys0) / L))

    def half(y):
        u = (y - ys0) / L
        return beam / 2 * max(0.15, math.sin(math.pi * u) ** 0.6)
    for y in range(ys0, ys1):                                          # 龍骨
        M.box(layer, cx - 1, y, zk(y), cx + 1, y + 1, zk(y) + 3, FRAME)
        if (y - ys0) % 20 == 0:                                        # 龍骨墩
            M.box(layer, cx - 3, y, 0, cx + 3, y + 3, zk(y), LOG_D)
    for y in range(ys0 + 6, ys1 - 4, 10):
        w, z0 = half(y), zk(y) + 3
        prev = 0
        for dz in range(0, depth):
            dx = int(round(w * math.sqrt((dz + 1) / depth)))
            for xx in range(prev, dx + 1):                             # 同一層從上一層的寬補到這一層（面相連，不然一節一節只有邊碰邊）
                M.box(layer, cx + xx, y, z0 + dz, cx + xx + 1, y + 2, z0 + dz + 1, FRAME)
                M.box(layer, cx - xx - 1, y, z0 + dz, cx - xx, y + 2, z0 + dz + 1, FRAME)
            prev = dx
        if w > beam * 0.3:                                             # 肋骨頂一道橫梁（甲板梁）
            M.box(layer, cx - int(w) - 1, y, z0 + depth - 1, cx + int(w) + 1, y + 2, z0 + depth, FRAME)
    for y in range(ys0 + 6, ys1 - 4):                                  # 船殼板：下面 plank 那一段（貼著肋骨外面）
        w, z0 = half(y), zk(y) + 3                                     # 板厚 2 格（x、z 各多一格）：龍骨斜著往下、船寬沿 y 變 ⇒ 一格厚的板每換一格高或寬就只剩邊碰邊、算成浮空
        for dz in range(0, int(depth * plank)):
            dx = int(round(w * math.sqrt((dz + 1) / depth))) + 1
            c = BOARD if dz % 4 else BOARD_D
            M.box(layer, cx + dx, y, z0 + dz, cx + dx + 2, y + 1, z0 + dz + 2, c)
            M.box(layer, cx - dx - 2, y, z0 + dz, cx - dx, y + 1, z0 + dz + 2, c)
    for y in (ys0, ys1 - 2):                                           # 艏柱、艉柱
        M.box(layer, cx - 1, y, zk(y), cx + 1, y + 2, zk(y) + depth + 8, FRAME)


def slipway(M, cx, ys0, ys1, z_front, z_back, gap=14, layer='body'):
    """船台：兩條平行的滑道木（ways），從 z_front 斜到 z_back，底下每 2 m 一根橫枕木。"""
    L = ys1 - ys0
    for y in range(ys0, ys1):
        z = int(round(z_front + (z_back - z_front) * (y - ys0) / L))
        for x in (cx - gap - 3, cx + gap):
            M.box(layer, x, y, 0, x + 3, y + 1, max(1, z), LOG if z > 2 else LOG_D)
        if (y - ys0) % 20 == 0:
            M.box(layer, cx - gap - 6, y, 0, cx + gap + 6, y + 3, 2, FRAME)


def saw_trestle(M, x0, y0, layer='body'):
    """鋸木架（代鋸木坑：坑挖不進地面 ⇒ 架高；上面一根方木、一把立著的長鋸）。"""
    for x in (x0, x0 + 40):
        for y in (y0, y0 + 10):
            M.box(layer, x, y, 0, x + 2, y + 2, 14, FRAME)
    M.box(layer, x0, y0, 14, x0 + 42, y0 + 12, 15, FRAME)
    M.box(layer, x0 - 8, y0 + 3, 15, x0 + 50, y0 + 9, 21, LOG)
    M.box(layer, x0 + 18, y0 + 5, 4, x0 + 19, y0 + 7, 30, IRON)


def board_store(M, R, ze=36, door_c=None, salt=0):
    """木板倉庫（共用：不分地區的木構釘板、兩坡木瓦頂、兩端山牆、正面一扇貨門）。"""
    rubble_walls(M, R, 0, 4, 4, salt=salt)
    board_walls(M, R, 4, ze, 2, bay=26)
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        for y in range(R[1], R[3]):
            d = min(y + 0.5 - R[1], R[3] - y - 0.5)
            for z in range(ze, ze + int(0.6 * d) + 1):
                for x in range(x0, x1):
                    M.put('body', x, y, z, FRAME if y in (R[1], R[3] - 1) else BOARD, force=True)
    put_part(M, 'cartdoor', '倉庫-貨門-%d' % salt, 'front', R, door_c if door_c is not None else (R[0] + R[2]) // 2, 0, 4)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': ze, 'p': 0.6, 'over': (4, 4, 4, 4), 'gable': 'x'}], salt=salt)


# ─────────────────────────────── 小船廠 40 × 30 m ───────────────────────────────
def shipyard_small():
    """小船廠（§10.1）：皇家港約一百艘 12–40 噸的 sloop「most of them built in the Country」（LAWS83）；造船場的位置、規模、設施都沒查到 ⇒
    照研究的建模建議：背面（朝水）一座船台、上面一艘 16 m 的 sloop 骨架（下半已釘板）；前面工棚與工作檯、木料與圓材堆、鋸木架（代鋸木坑）、
    煮瀝青的鍋、蒸彎木板的火槽、繩捲；左後一座木板倉庫。全部是推測。"""
    X, Y, Z = 400, 300, 90
    M = Model((X, Y, Z))
    slipway(M, 280, 110, 300, 14, 2)
    hull_frame(M, 280, 124, 284, 52, 26, 18, 6)
    tool_shed(M, 20, 18, 140, 70, 30, salt=161)
    log_pile(M, 160, 250, 20, 3, 5)
    for y in (44, 49, 54):
        M.box('body', 160, y, 0, 250, y + 4, 4, LOG_D)
    saw_trestle(M, 40, 100)
    tar_kettle(M, 130, 110)
    M.box('body', 160, 100, 0, 220, 108, 2, RUBBLE)                    # 蒸彎木板的火槽：一道淺溝（石砌邊、裡面紅的炭）、上面架一塊木板
    M.box('body', 162, 102, 1, 218, 106, 2, EMBER, force=True)
    for x in (158, 220):
        M.box('body', x, 102, 0, x + 2, 106, 6, RUBBLE)
    M.box('body', 158, 102, 6, 222, 106, 7, FLOOR)
    rope_coil(M, 100, 150)
    rope_coil(M, 120, 160)
    board_store(M, (20, 200, 150, 290), 34, salt=162)
    capstan(M, 340, 200)
    M.models += [{'name': '瀝青桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [146, 104, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-棚', 'source': 'summit-rocher-01m-crate', 'at': [30, 26, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-倉庫', 'source': 'summit-rocher-01m-lantern', 'at': [66.5, 200, 22.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('door', 200, 0, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'shipyard-small', 'title': '小船廠（共用：船台上一艘 16 m 的 sloop 骨架、工棚、木料與圓材堆、鋸木架、瀝青鍋、蒸板火槽、木板倉庫、絞盤）',
            'use': 'shipyard-small', 'lot': (40, 30), 'M': M, 'style': 'common', 'layers': {'body': '船台、骨架與設施', 'roof': '屋頂'}}


# ─────────────────────────────── 大船廠 80 × 50 m ───────────────────────────────
def shipyard_large():
    """大船廠（首府才有）：Havana Real Arsenal 約 1717 年開工、占地約 9 ha（TOWN_BUILD §1.1.7〔開〕）—— 地塊只有 0.4 ha ⇒ 只放核心：
    兩座船台（一艘 30 m 的船骨架、一座剛鋪龍骨）、背面一座起桅用的起重架（sheers：加勒比海、地中海不用踏輪吊車，TOWN_BUILD §1.1.10）、
    前面一長棟木板倉庫、桅杆棚、鐵匠鋪（毛石、火爐、煙囪）、木料堆、鋸木架、瀝青鍋、絞盤。配置與尺寸是設計。"""
    X, Y, Z = 800, 500, 150
    M = Model((X, Y, Z))
    slipway(M, 300, 170, 500, 18, 2, gap=26)
    hull_frame(M, 300, 190, 490, 84, 46, 24, 6, plank=0.5)
    slipway(M, 560, 170, 500, 18, 2, gap=26)
    for y in range(200, 470):                                          # 第二座：剛鋪龍骨、立了艏艉柱
        z = int(round(24 + (6 - 24) * (y - 200) / 270))
        M.box('body', 559, y, z, 561, y + 1, z + 3, FRAME)
        if (y - 200) % 20 == 0:
            M.box('body', 557, y, 0, 563, y + 3, z, LOG_D)
    for y in (200, 468):
        z = int(round(24 + (6 - 24) * (y - 200) / 270))
        M.box('body', 559, y, z, 561, y + 2, z + 50, FRAME)
    ax, ay = 700, 470                                                   # 起重架（sheers）：兩根粗圓材叉成 A 字、頂上綁在一起
    for sx in (-1, 1):
        for z in range(0, 130):
            x = ax + sx * int(round(30 * (1 - z / 130)))
            M.box('body', x - 2, ay - 2, z, x + 3, ay + 2, z + 1, LOG)
    M.box('body', ax - 3, ay - 3, 128, ax + 3, ay + 3, 132, ROPE, force=True)
    M.box('body', ax - 34, ay - 4, 0, ax + 34, ay + 4, 3, FRAME, force=True)
    capstan(M, ax, 400)
    board_store(M, (20, 20, 330, 100), 40, salt=171)
    mx0, mx1 = 380, 780                                                 # 桅杆棚：一長排柱、單坡頂、底下躺著幾根桅杆
    posts = [(x, 22) for x in range(mx0 + 2, mx1 - 2, 60)] + [(x, 76) for x in range(mx0 + 2, mx1 - 2, 60)] + [(mx1 - 4, 22), (mx1 - 4, 76)]
    lean_roof_posts(M, mx0, 20, mx1, 80, 34, 0.2, 'front', shingle_color, posts, salt=172)
    for i, y in enumerate((34, 46, 58)):
        M.box('body', mx0 + 20, y, 0, mx1 - 30 - i * 40, y + 6, 6, LOG)
    sm = (20, 140, 90, 200)                                             # 鐵匠鋪：毛石小屋＋火爐＋煙囪
    rubble_walls(M, sm, 0, 28, 4, salt=173)
    put_part(M, 'door-plank', '鐵匠鋪-門', 'front', sm, 55, 0, 4)
    top = shingle_roof(M, [{'x0': sm[0], 'y0': sm[1], 'x1': sm[2], 'y1': sm[3], 'ze': 28, 'p': 0.7, 'over': (3, 3, 3, 3)}], salt=174)
    hearth(M, 30, 180, 50, 196, hanger=False)
    free_part(M, 'chimney', '鐵匠鋪-煙囪', (32, 184, top[(36, 187)] - 10))
    log_pile(M, 120, 230, 140, 3, 5)
    log_pile(M, 120, 230, 172, 2, 5)
    saw_trestle(M, 140, 220)
    tar_kettle(M, 420, 160)
    capstan(M, 420, 260)
    rope_coil(M, 460, 200)
    M.models += [{'name': '瀝青桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [436, 152, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '瀝青桶-2', 'source': 'summit-rocher-01m-barrel', 'at': [448, 152, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-倉庫', 'source': 'summit-rocher-01m-lantern', 'at': [140.5, 20, 26.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('door', 400, 0, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'shipyard-large', 'title': '大船廠（共用：兩座船台（一艘 30 m 的船骨架、一座剛鋪龍骨）、起桅的起重架、長倉庫、桅杆棚、鐵匠鋪、木料堆、鋸木架、瀝青鍋、絞盤）',
            'use': 'shipyard-large', 'lot': (80, 50), 'M': M, 'style': 'common', 'layers': {'body': '船台、骨架與設施', 'roof': '屋頂'}}


# ─────────────────────────────── 製繩場 200 × 10 m ───────────────────────────────
def ropewalk():
    """製繩場（首府才有）：300 m 上下的細長建築（Copenhagen 980 呎、Chatham 1,120 呎，TOWN_BUILD §1.1.7〔摘〕）—— 地塊 200 m：
    一長排柱撐的兩坡木瓦頂（兩側開敞）、左端紡車（大木輪）、每 20 m 一根撐繩的木樁（stakehead）、三股繩一路拉到右端的牽繩車。配置是設計。"""
    X, Y, Z = 2000, 100, 50
    M = Model((X, Y, Z))
    top = shingle_roof(M, [{'x0': 4, 'y0': 10, 'x1': 1996, 'y1': 90, 'ze': 24, 'p': 0.5, 'over': (4, 4, 6, 6), 'gable': 'x'}], salt=181)
    xs = list(range(4, 1990, 40)) + [1992]
    gallery_posts(M, xs, 10, 0, top, layer='body')
    gallery_posts(M, xs, 88, 0, top, layer='body')
    for x in range(200, 1900, 200):                                     # 撐繩的木樁：一根柱＋橫木（繩股架在上面）
        M.box('body', x, 46, 0, x + 2, 54, 8, FRAME)
        M.box('body', x, 34, 8, x + 2, 66, 9, FRAME)
    for y in (40, 50, 60):                                              # 三股繩
        M.box('body', 60, y, 9, 1940, y + 1, 10, ROPE)
    cx, cy = 40, 50                                                     # 紡車：木架上一個立著的大輪（半徑 1.4 m）
    for x in (34, 44):
        M.box('body', x, cy - 3, 0, x + 2, cy + 3, 19, FRAME)
    for y in range(cy - 14, cy + 15):
        for z in range(4, 33):
            d = math.hypot(y + 0.5 - cy, z + 0.5 - 18)
            if 12.5 <= d <= 14 or (d < 14 and (abs(y + 0.5 - cy) < 1 or abs(z + 0.5 - 18) < 1)):
                M.put('body', 39, y, z, FRAME)
    M.box('body', 36, cy - 1, 17, 44, cy + 1, 19, IRON)                 # 輪軸（接到兩邊的架子）
    M.box('body', 46, 38, 0, 48, 40, 9, FRAME)                          # 掛繩的鉤架（兩根柱＋橫木，接住三股繩的頭）
    M.box('body', 46, 60, 0, 48, 62, 9, FRAME)
    M.box('body', 46, 38, 9, 60, 62, 10, FRAME)
    M.box('body', 1940, 36, 0, 1970, 64, 6, FLOOR)                      # 牽繩車（sledge）：右端一台木車、上面的架子接住三股繩
    M.box('body', 1940, 38, 6, 1944, 62, 10, FRAME)
    M.models += [{'name': '麻包-1', 'source': 'summit-rocher-01m-crate', 'at': [80, 20, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '焦油桶', 'source': 'summit-rocher-01m-barrel', 'at': [100, 20, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-左端', 'source': 'summit-rocher-01m-lantern', 'at': [24.5, 10, 14.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('door', 1000, 0, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'ropewalk', 'title': '製繩場（共用：200 m 長棚、兩側開敞、兩坡木瓦頂；左端紡車、每 20 m 一根撐繩樁、三股繩、右端牽繩車）',
            'use': 'ropewalk', 'lot': (200, 10), 'M': M, 'style': 'common', 'layers': {'body': '柱、紡車與繩', 'roof': '屋頂'}}


ALL = [shipyard_small, shipyard_large, ropewalk]
