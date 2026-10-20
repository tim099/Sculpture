# 加勒比海的公共建築（風格 carib；TASK-0772）：市場、市政廳（法庭兼議事廳）、海關（秤房）、醫院、總督府 —— 地塊照生成器 world/town.js 的 PUB。
# 座標同 civic.py（x 臨路寬、y 進深 y 0 臨路、z 往上；0.1 m／格）。史料：references/research_civic.md §4–§8（每一棟「照什麼／推測」寫在函式說明）。
# 17 世紀法屬島上沒有市政機構、沒有市場棚、秤房只寫「漂亮的 case」⇒ 這幾棟大半是推測，照研究的建模建議做、⛔ 不編特殊形制。
from civic import *

PRODUCE = (76, 224, 252, 141)    # 攤上的瓜菜（綠、紅、黃、土）
MEAT = 160                       # 肉鋪掛的肉（深紅）
LEAF_A, LEAF_B = 80, 44          # 樹葉（同 kit 的 LEAF、GRASS_D）
BARK = 100


def end_gable(M, x0, x1, y0, y1, ze, p, z0=0, color=BOARD, edge=FRAME, layer='body'):
    """屋脊沿 x 的兩坡頂，x 那一端的山牆（三角在 y–z 平面）：x ∈ [x0, x1) 是牆厚、y ∈ [y0, y1) 是寬；牆從 z0 立到 ze ＋ p × 離最近一邊的距離。"""
    for y in range(y0, y1):
        d = min(y + 0.5 - y0, y1 - y - 0.5)
        zt = int(math.floor(ze + p * d))
        for z in range(z0, zt + 1):
            for x in range(x0, x1):
                c = edge if (z >= zt - 1 or y in (y0, y1 - 1)) else (BOARD_D if (z - z0) % 3 == 2 and color == BOARD else color)
                M.put(layer, x, y, z, c, force=True)


def trestle_table(M, x0, x1, y0, y1, z=8, top=FLOOR, layer='body'):
    """木板桌（板＋兩端的腳）。"""
    M.box(layer, x0, y0, z, x1, y1, z + 1, top)
    for x in (x0 + 1, x1 - 3):
        M.box(layer, x, y0 + 1, 0, x + 2, y1 - 1, z, FRAME)


def bench(M, x0, x1, y0, y1, z=4, layer='body'):
    M.box(layer, x0, y0, z, x1, y1, z + 1, FLOOR)
    for x in (x0, x1 - 2):
        M.box(layer, x, y0, 0, x + 2, y1, z, FRAME)


def big_tree(M, cx, cy, h_trunk, r, zc, salt=0, layer='body'):
    """一棵大樹（無花果或葫蘆樹，樹下開庭 —— DT2 p.446）：粗樹幹＋三根大枝＋幾團樹冠（只留殼）。"""
    X, Y, Z = M.X, M.Y, M.Z
    for z in range(0, h_trunk):
        rr = 4.2 if z < 6 else 3.2
        for x in range(int(cx - 6), int(cx + 6)):
            for y in range(int(cy - 6), int(cy + 6)):
                if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= rr:
                    M.put(layer, x, y, z, BARK if h01('bk', x, y, z // 3) < 0.7 else FRAME)
    blobs = [(cx, cy, zc, r, r, r * 0.6)]
    for i, (dx, dy) in enumerate(((-1, -0.4), (0.8, -0.7), (0.3, 1))):
        bx, by = cx + dx * r * 0.55, cy + dy * r * 0.55
        blobs.append((bx, by, zc - 4 + i * 3, r * 0.65, r * 0.65, r * 0.45))
        n = int(r * 0.55)
        for k in range(n):                                             # 大枝：從樹幹頂斜出去到那一團
            u = k / max(1, n - 1)
            x, y, z = cx + (bx - cx) * u, cy + (by - cy) * u, h_trunk - 6 + (zc - 4 - h_trunk + 6) * u
            M.box(layer, int(x) - 1, int(y) - 1, int(z), int(x) + 1, int(y) + 1, int(z) + 2, BARK)
    S = np.zeros((X, Y, Z), bool)
    xs = np.arange(X)[:, None, None] + 0.5
    ys = np.arange(Y)[None, :, None] + 0.5
    zs = np.arange(Z)[None, None, :] + 0.5
    for (bx, by, bz, rx, ry, rz) in blobs:
        S |= ((xs - bx) / rx) ** 2 + ((ys - by) / ry) ** 2 + ((zs - bz) / rz) ** 2 <= 1.0
    S &= zs >= h_trunk - 8
    sh = hollow(S, 4)
    put_mask(M, sh, lambda x, y, z: LEAF_B if h01('lf', x // 3, y // 3, z // 3, salt) < 0.35 else LEAF_A, layer)
    for z in range(h_trunk - 8, zc + 2):                               # 樹幹一路伸進樹冠（跟殼相連）
        for x in range(int(cx - 2), int(cx + 2)):
            for y in range(int(cy - 2), int(cy + 2)):
                M.put(layer, x, y, z, BARK)


def small_house(M, R, z1, door_face, door_c, roof='shingle', salt=0, rubble=False):
    """一間小屋（衛兵所、肉鋪、牢房）：木板牆或毛石牆、四坡頂、一扇木板門。牆至少 2.7 m（門 2.3 m 高 ⇒ 屋簷要在門楣上面，不然簷口壓到門框）。"""
    z1 = max(z1, 27)
    if rubble:
        rubble_walls(M, R, 0, z1, 3, salt=salt)
    else:
        board_walls(M, R, 0, z1, 2)
    put_part(M, 'door-plank', '小屋-門-%d' % salt, door_face, R, door_c, 0, 3 if rubble else 2)
    f = shingle_roof if roof == 'shingle' else thatch_roof
    f(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': z1, 'p': 0.8, 'over': (3, 3, 3, 3)}], salt=salt)


# ─────────────────────────────── 市場 20 × 16 m ───────────────────────────────
def market():
    """市場（§4）：1700 年前法屬的交易在港邊倉庫列前、廣場上（DT2 pp.18、449、521）；1685 年 Code Noir 已假設每處有 Marché。
    有頂的市場棚沒有任何描述 ⇒ 借當時人心裡「像 halle」的樣子（LB2 pp.84–85 的 carbet：一排短柱出地 9 法尺、屋面垂得很低、一端封一端開，推測）；
    棚下兩排木板桌擺瓜菜、菸草捲、桶；後面空地擺賣；右後一間小肉鋪（St-Christophe 每天賣鮮肉的 boutique，DT2 p.19）。"""
    X, Y, Z = 200, 160, 60
    M = Model((X, Y, Z))
    SX0, SX1, SY0, SY1 = 6, 194, 14, 80                               # 棚 18.8 × 6.6 m
    top = thatch_roof(M, [{'x0': SX0, 'y0': SY0, 'x1': SX1, 'y1': SY1, 'ze': 22, 'p': 0.75, 'over': (4, 4, 8, 8), 'gable': 'x'}], salt=91)
    xs = list(range(SX0, SX1 - 2, 30)) + [SX1 - 2]
    gallery_posts(M, xs, SY0, 0, top, layer='body')
    gallery_posts(M, xs, SY1 - 2, 0, top, layer='body')
    end_gable(M, SX0, SX0 + 2, SY0, SY1, 22, 0.75)                     # 左端封起來（右端開敞）
    for y0 in (26, 58):                                                # 兩排攤桌
        for x0 in range(18, 150, 40):
            trestle_table(M, x0, x0 + 32, y0, y0 + 8)
            for i in range(5):                                         # 桌上的貨：瓜菜堆、菸草捲
                c = PRODUCE[(i + x0 // 40) % len(PRODUCE)]
                M.box('body', x0 + 2 + i * 6, y0 + 2, 9, x0 + 6 + i * 6, y0 + 6, 11 + (i % 2), c)
    trestle_table(M, 24, 64, 112, 120)                                 # 後面空地的兩張
    trestle_table(M, 76, 116, 126, 134)
    for x0 in (28, 40, 52):
        M.box('body', x0, 114, 9, x0 + 8, 118, 12, 100)                 # 菸草捲（捲成條的菸葉）
    mr = (140, 104, 190, 144)                                           # 肉鋪 5 × 4 m
    small_house(M, mr, 24, 'front', 158, salt=92)
    put_part(M, 'window-board', '肉鋪-窗', 'front', mr, 178, 8, 2)
    M.box('body', 140, 94, 0, 142, 96, 22, FRAME)                       # 門前的掛肉架（兩根柱＋橫桿、掛幾塊肉）
    M.box('body', 188, 94, 0, 190, 96, 22, FRAME)
    M.box('body', 140, 94, 22, 190, 96, 23, FRAME)
    for x in (150, 162, 174):
        M.box('body', x, 94, 14, x + 4, 96, 22, MEAT)
    M.models += [{'name': '糖桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [180, 30, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '糖桶-2', 'source': 'summit-rocher-01m-barrel', 'at': [180, 44, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-攤1', 'source': 'summit-rocher-01m-crate', 'at': [100, 112, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-棚', 'source': 'summit-rocher-01m-lantern', 'at': [100.5, SY0, 9.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('door', 100, 0, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'market', 'title': '市場（開敞長棚：一排短柱、棕櫚葉兩坡頂垂得很低、左端封右端開；棚下兩排攤桌；後面擺賣的空地；小肉鋪與掛肉架）',
            'use': 'market', 'lot': (20, 16), 'M': M, 'style': 'carib', 'layers': {'body': '棚、攤與肉鋪', 'roof': '屋頂'}}


# ─────────────────────────────── 市政廳（法庭兼議事廳 Auditoire）20 × 16 m ───────────────────────────────
def townhall():
    """市政廳（§5）：法屬 1700 年前沒有市政機構與市政建築；議事（Conseil）在總督家、堡裡、港邊大倉庫或廣場上的 Auditoire（DT2 p.26），
    開庭在「一間專用的廳，每週兩次」（DT2 p.444）；首任總督們在**大樹下**開庭（Poincy 在無花果樹下、Du Parquet 在葫蘆樹下，DT2 p.446）。
    ⇒ 做成 Auditoire：兩層木構釘板（樓下大廳、樓上書記與檔案；推測）、兩坡木瓦頂；前院一棵大樹、樹下長桌與長凳；
    側邊一間衛兵所（早年犯人在衛兵所上鐐，DT2 pp.446–447）、一間毛石小牢房（cachot，形制推測）；旗杆是推測。"""
    X, Y, Z = 200, 160, 100
    M = Model((X, Y, Z))
    R = (70, 70, 190, 150)                                              # 12 × 8 m
    rubble_walls(M, R, 0, 4, 4, salt=101)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 3, EARTH_W)
    M.box('body', R[0], R[1], 3, R[2], R[3], 4, FLOOR)
    board_walls(M, R, 4, 34, 2, bay=26)
    M.box('body', R[0] + 2, R[1] + 2, 33, R[2] - 2, R[3] - 2, 35, FLOOR)   # 樓板
    board_walls(M, R, 34, 58, 2, bay=26)                                # 從 34 起（35 起 ⇒ 樓上整層跟樓下隔一格、算成浮空）
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 58, 0.7, z0=58)
    put_part(M, 'door-double', '前-大門', 'front', R, 130, 4, 2)
    for i, cx in enumerate((92, 168)):
        put_part(M, 'window-baluster', '前-窗%d' % (i + 1), 'front', R, cx, 12, 2)
    for i, cx in enumerate((92, 130, 168)):
        put_part(M, 'window-board', '前-樓上窗%d' % (i + 1), 'front', R, cx, 40, 2)
        put_part(M, 'window-board', '後-樓上窗%d' % (i + 1), 'back', R, cx, 40, 2)
    for face in ('left', 'right'):
        put_part(M, 'window-baluster', '%s-窗' % face, face, R, 110, 12, 2)
    put_part(M, 'door-plank', '後-門', 'back', R, 130, 4, 2)
    M.box('body', 120, 64, 0, 140, 70, 4, RUBBLE)                       # 門前一級石階
    M.anchor('door', 130, 63, 0)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 58, 'p': 0.7, 'over': (4, 4, 5, 5), 'gable': 'x'}], salt=102)
    trestle_table(M, 92, 168, 100, 112, z=11)                           # 廳裡議事的長桌與兩條長凳
    bench(M, 92, 168, 94, 98, z=8)
    bench(M, 92, 168, 114, 118, z=8)
    # 前院的大樹＋樹下開庭的長桌與長凳
    big_tree(M, 36, 48, 40, 30, 62, salt=103)
    trestle_table(M, 22, 52, 66, 74)
    bench(M, 22, 52, 60, 63)
    bench(M, 22, 52, 77, 80)
    # 衛兵所（右前）、牢房（左後）
    small_house(M, (150, 8, 190, 40), 22, 'left', 24, salt=104)
    small_house(M, (8, 112, 36, 140), 20, 'right', 126, salt=105, rubble=True)
    ft, fb = flagpole(M, 110, 20, 80)
    M.anchor('flag', 110, 20, 81)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 28, toward=1)]
    M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [114.5, R[1], 26.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'townhall', 'title': '市政廳（法庭兼議事廳 Auditoire：兩層木構釘板、兩坡木瓦頂；前院大樹與樹下開庭的長桌長凳；衛兵所、毛石小牢房；旗杆與白旗）',
            'use': 'townhall', 'lot': (20, 16), 'M': M, 'style': 'carib', 'layers': {'body': '牆身與院子', 'roof': '屋頂'}, 'flags': flags}


# ─────────────────────────────── 海關（秤房 poids Royal）16 × 14 m ───────────────────────────────
def customs():
    """海關（§6）：法屬島上「倉庫之間總有一間漂亮的 case 當皇家秤房」（DT2 p.452），所有貨物都要在這裡過秤、收 1% 秤費（DT3），
    菸草捲用切的鉗子剖開驗貨（DT2 pp.461–462）；旁邊是衛兵所（DT2 pp.25–27）。秤房的尺寸、秤具的形式都沒查到 ⇒
    木構釘板、比住屋高（3 m，讓秤架有空間）、兩坡木瓦頂、正面一道披屋卸貨廊、廊下一座吊架大橫桿秤（推測形制）、菸草捲與糖桶；右後衛兵所。"""
    X, Y, Z = 160, 140, 70
    M = Model((X, Y, Z))
    R = (20, 50, 120, 120)                                              # 10 × 7 m
    board_walls(M, R, 0, 30, 2, bay=26)
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 30, 0.7, z0=30)
    put_part(M, 'door-double', '前-大門', 'front', R, 70, 0, 2)
    for i, cx in enumerate((36, 104)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, 9, 2)
    put_part(M, 'door-plank', '右-書記門', 'right', R, 96, 0, 2)
    put_part(M, 'window-board', '左-窗', 'left', R, 85, 9, 2)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.7, 'over': (4, 4, 3, 4), 'gable': 'x'}], salt=111)
    lean_roof_posts(M, 18, 22, 122, 48, 27, 0.2, 'front', shingle_color, [(20, 24), (68, 24), (118, 24)], salt=112)
    M.box('body', R[0], 22, 0, R[2], R[1] - 1, 1, FLOOR)                # 廊下的木板地（停在門框前一格）
    # 吊架大橫桿秤（推測）：兩根柱＋橫梁、中間吊鏈、橫桿、兩端吊盤
    for x in (34, 62):
        M.box('body', x, 34, 1, x + 2, 36, 26, FRAME)
    M.box('body', 34, 34, 24, 64, 36, 26, FRAME)
    M.box('body', 48, 34, 16, 49, 35, 24, IRON)
    M.box('body', 36, 34, 15, 62, 35, 16, IRON)
    for x in (37, 60):
        M.box('body', x, 34, 7, x + 1, 35, 15, IRON)
        M.box('body', x - 3, 32, 6, x + 4, 38, 7, FRAME)
    M.box('body', 58, 33, 7, 62, 37, 9, IRON)                           # 秤錘
    for k in range(2):                                                  # 菸草捲（直徑 0.6 m、長 1.2 m，堆兩層：上一層架在下一層兩捲之間）
        x0 = 80
        for j in range(3 - k):
            yc = 30 + j * 6 + k * 3
            for x in range(x0, x0 + 12):
                for y in range(yc - 3, yc + 3):
                    for z in range(k * 5, k * 5 + 6):
                        if math.hypot(y + 0.5 - yc, z + 0.5 - k * 5 - 3) <= 3:
                            M.put('body', x, y, z, FRAME if x in (x0, x0 + 11) else 100)
    small_house(M, (124, 96, 156, 132), 22, 'left', 114, salt=113)
    M.models += [{'name': '糖桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [108, 28, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '糖桶-2', 'source': 'summit-rocher-01m-barrel', 'at': [108, 40, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱', 'source': 'summit-rocher-01m-crate', 'at': [26, 28, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-廊', 'source': 'summit-rocher-01m-lantern', 'at': [84.5, 24, 10.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('door', 70, 49, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'customs', 'title': '海關（皇家秤房 poids Royal：木構釘板、兩坡木瓦頂、正面卸貨廊；廊下吊架大橫桿秤、菸草捲與糖桶；衛兵所）',
            'use': 'customs', 'lot': (16, 14), 'M': M, 'style': 'carib', 'layers': {'body': '牆身與廊', 'roof': '屋頂'}}


# ─────────────────────────────── 醫院 20 × 16 m ───────────────────────────────
def hospital():
    """醫院（§7）：照 Guadeloupe Basse-Terre 1696 年的 Charité 醫院（LB2 pp.170–171）——一長棟砌石病房（80 × 30 法尺）兼禮拜堂、面海；
    後面一個方院，四周是牆，牆內側靠一圈披屋當廚房、倉庫與修士的房間。病房 26 m 塞不進 20 m ⇒ 照比例縮到 19.2 × 7.8 m（研究的建議①）。
    刷白、窗用欄杆、床兩排靠牆、祭壇在左端、井與菜園是推測。"""
    X, Y, Z = 200, 160, 80
    M = Model((X, Y, Z))
    R = (4, 6, 196, 84)
    rubble_walls(M, R, 0, 6, 4, salt=121)
    stucco_walls(M, R, 6, 38, 4, LIME)
    for x0, x1 in ((R[0], R[0] + 4), (R[2] - 4, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 38, 0.75, z0=38, color=LIME, edge=LIME)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 1, RUBBLE)   # 石板地
    put_part(M, 'door-double', '前-大門', 'front', R, 100, 0, 4)
    put_part(M, 'door-plank', '後-門（往方院）', 'back', R, 100, 0, 4)
    for i, cx in enumerate((30, 62, 138, 170)):
        put_part(M, 'window-baluster', '前-窗%d' % (i + 1), 'front', R, cx, 12, 4)
        put_part(M, 'window-baluster', '後-窗%d' % (i + 1), 'back', R, cx, 12, 4)
    M.anchor('door', 100, 5, 0)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 38, 'p': 0.75, 'over': (3, 3, 4, 4), 'gable': 'x'}], salt=122)
    zr = int(38 + 0.75 * 39)                                            # 屋脊上靠左端的木十字（病房兼禮拜堂）
    M.box('roof', 10, 44, zr, 12, 46, zr + 12, FRAME, force=True)
    M.box('roof', 7, 44, zr + 7, 15, 46, zr + 9, FRAME, force=True)
    # 室內：左端祭壇＋欄杆；兩排床（靠前牆、後牆）
    M.box('body', 10, 34, 1, 20, 56, 11, LIME)
    M.box('body', 9, 33, 11, 21, 57, 12, FRAME)
    for y in range(14, 76):
        if 40 <= y < 48:
            continue
        M.put('body', 28, y, 9, FRAME)
        if y % 2 == 0:
            M.box('body', 28, y, 1, 29, y + 1, 9, FRAME)
    for x0 in range(36, 186, 12):
        if 88 <= x0 <= 108:
            continue
        for (y0, y1) in ((10, 28), (62, 80)):
            M.box('body', x0, y0, 1, x0 + 8, y1, 4, FRAME)
            M.box('body', x0, y0, 4, x0 + 8, y1, 5, LIME)
    # 方院：毛石院牆、牆內側靠著一排披屋（廚房、倉庫、修士房）、井、菜園
    rubble_walls(M, (4, 84, 196, 158), 0, 24, 4, salt=123)
    M.clear(8, 84, 0, 192, 88, 24)                                      # 前面那一道就是病房的後牆 ⇒ 不再砌一道（不然後門、後窗撞上）
    lean_roof_posts(M, 6, 120, 194, 154, 27, 0.25, 'front', shingle_color, [(10, 122), (64, 122), (128, 122), (188, 122)], salt=124)
    for x in (64, 128):
        M.box('body', x, 124, 0, x + 2, 154, 22, BOARD)
    hearth(M, 24, 138, 40, 148)
    M.box('body', 96, 98, 0, 112, 112, 8, RUBBLE)                       # 井
    M.box('body', 99, 101, 1, 109, 109, 8, DARK, force=True)
    for x in (96, 110):
        M.box('body', x, 104, 8, x + 2, 106, 22, FRAME)
    M.box('body', 96, 104, 22, 112, 106, 23, FRAME)
    for (x0, x1) in ((14, 80), (124, 186)):                             # 菜園：一畦一畦
        for y in range(92, 116):
            for x in range(x0, x1):
                M.put('body', x, y, 0, GRASS if (y - 92) % 6 < 3 else EARTH_W)
    M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [84.5, R[1], 26.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '水桶-井', 'source': 'summit-rocher-01m-barrel', 'at': [116, 100, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'hospital', 'title': '醫院（Charité 型：砌石刷白的長病房兼禮拜堂、兩排床、左端祭壇、欄杆窗、兩坡木瓦頂；後面毛石院牆圍的方院、院牆內側的披屋（廚房、倉庫、修士房）、井、菜園）',
            'use': 'hospital', 'lot': (20, 16), 'M': M, 'style': 'carib', 'layers': {'body': '病房與方院', 'roof': '屋頂'}}


# ─────────────────────────────── 總督府 28 × 22 m ───────────────────────────────
def governor():
    """總督府（§8）：1660–90 年代法屬的總督住處多在堡裡或 maison-forte；Fort-Royal 1694 的 corps de logis「下倉、中住、上武器廳」（LB1 pp.198–199）、
    Guadeloupe 修院的「石底層＋木上層」、Tortuga 灘邊 maison-forte 的「下層槍眼、樓上操砲」合起來（合成是推測）：
    主屋 22.8 × 9.2 m（借 1717 年 70 × 28 法尺，MSM2 p.463）、下層毛石、上層木構釘板、紅瓦四坡頂；**窗裝玻璃、有煙囪**（只有總督家有，DT2 pp.451–452）；
    前院：低石牆與門、衛兵所、兩座站崗小亭各一門小砲（Du Parquet 宅院，DT2 p.27）、旗杆（推測）；後院分開的廚房（DT2 p.451）。
    2026-10-21 看了 LB1 p.198 的夾頁〈Plan de l'Arcenal et Logement du Général au Fort Royal de la Martinique〉與〈Plan des Souterrains〉（Tim 同意下載；
    references/plates/）：一長棟、只有一間深（約 10 m）、房間一字排開（廳、臥房、小書房、更衣間、另一套房，中間樓梯往下到地下層的火藥庫、廚房與烤爐）、
    正面一排規律的扶壁、窗開在扶壁之間 ⇒ 下層正面與背面照這個節奏加扶壁（每 4.2～4.8 m 一道、凸出 0.5 m），窗只開在扶壁之間。
    圖上那一棟約 53 m 長、地塊只有 28 m ⇒ 照節奏截一段（不是照比例縮）。"""
    X, Y, Z = 280, 220, 120
    M = Model((X, Y, Z))
    R = (26, 64, 254, 156)
    FL = 6                                                              # 一樓地板 0.6 m（三級石階）
    rubble_walls(M, R, 0, 32, 4, salt=131)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, FL - 1, EARTH_W)
    M.box('body', R[0] + 4, R[1] + 4, FL - 1, R[2] - 4, R[3] - 4, FL, FLOOR)
    M.box('body', R[0] + 2, R[1] + 2, 31, R[2] - 2, R[3] - 2, 33, FLOOR)
    board_walls(M, R, 32, 60, 2, bay=26)
    for x in (R[0] + 4, R[2] - 6):                                     # 側牆下層的槍眼（maison-forte）
        for y in (88, 132):
            M.clear(x - 4, y, 14, x + 6, y + 2, 22)
    for x0 in (26, 68, 112, 164, 206, 250):                             # 下層的扶壁（LB1 p.198 夾頁：正面一排規律的扶壁）：毛石、凸出 0.5 m、頂上一皮壓頂
        for (y0, y1) in ((R[1] - 5, R[1]), (R[3], R[3] + 5)):
            rubble_walls(M, (x0, y0, x0 + 4, y1), 0, 30, 4, salt=139 + x0)
            M.box('body', x0, y0, 30, x0 + 4, y1, 32, MORTAR)
    put_part(M, 'door-double', '前-大門', 'front', R, 140, FL, 4)
    steps(M, 126, 154, R[1], 3, 2, 3, back=False, layer='body', color=RUBBLE)
    for i, cx in enumerate((49, 92, 187, 230)):                        # 窗只開在扶壁之間
        put_part(M, 'window', '前-窗%d' % (i + 1), 'front', R, cx, FL + 8, 4)
        put_part(M, 'window', '後-窗%d' % (i + 1), 'back', R, cx, FL + 8, 4)
    for i, cx in enumerate((49, 92, 140, 187, 230)):
        put_part(M, 'window', '前-樓上窗%d' % (i + 1), 'front', R, cx, 38, 2)
        put_part(M, 'window', '後-樓上窗%d' % (i + 1), 'back', R, cx, 38, 2)
    for face in ('left', 'right'):
        put_part(M, 'window', '%s-樓上窗' % face, face, R, 110, 38, 2)
    put_part(M, 'door-plank', '後-門', 'back', R, 140, FL, 4)
    steps(M, 132, 148, R[3], 3, 2, 3, back=True, layer='body', color=RUBBLE)
    M.anchor('door', 140, R[1] - 1, FL)
    F = roof_field([{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 60, 'p': 0.6, 'over': (5, 5, 5, 5)}])
    top = build_roof(M, F, 2, 'roof', salt=132)                         # 紅瓦（荷蘭瓦；只有總督、富戶用得起 —— RF、summit §8）
    for i, (cx, cy) in enumerate(((70, 104), (210, 104))):             # 兩根煙囪（磚，固定點 smoke）
        zb = top[(cx + 4, cy + 3)] - 10
        free_part(M, 'chimney', '煙囪%d' % (i + 1), (cx, cy, zb))
    # 前院：低石牆＋門、衛兵所、兩座站崗小亭（各一門小砲）、旗杆
    for (x0, x1) in ((4, 116), (164, 276)):
        rubble_walls(M, (x0, 4, x1, 8), 0, 10, 4, salt=133 + x0)
    for gx in (113, 164):
        M.box('body', gx, 3, 0, gx + 3, 9, 18, RUBBLE)
    for i, (x0, face) in enumerate(((8, 'left'), (248, 'right'))):
        kr = (x0, 12, x0 + 24, 36)
        for (px, py) in ((kr[0], kr[1]), (kr[2] - 2, kr[1]), (kr[0], kr[3] - 2), (kr[2] - 2, kr[3] - 2)):
            M.box('body', px, py, 0, px + 2, py + 2, 22, FRAME)
        board_walls(M, (kr[0], kr[3] - 2, kr[2], kr[3]), 0, 22, 2, posts=False)
        M.box('body', kr[0], kr[1], 0, kr[2], kr[3], 1, FLOOR)
        shingle_roof(M, [{'x0': kr[0], 'y0': kr[1], 'x1': kr[2], 'y1': kr[3], 'ze': 22, 'p': 0.9, 'over': (2, 2, 2, 2)}], salt=135 + i)
        gun(M, '小亭-砲%d' % (i + 1), x0 + 12, 22, 1, 'front')
    small_house(M, (40, 16, 90, 50), 24, 'right', 33, salt=137)
    ft, fb = flagpole(M, 196, 30, 100)
    M.anchor('flag', 196, 30, 101)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 30, toward=1)]
    # 後院：分開的廚房（木板、灶）＋柴堆
    kr = (180, 176, 236, 212)
    board_walls(M, kr, 0, 28, 2)
    put_part(M, 'door-plank', '廚房-門', 'front', kr, 208, 0, 2)
    hearth(M, 196, 196, 212, 206, hanger=False)
    shingle_roof(M, [{'x0': kr[0], 'y0': kr[1], 'x1': kr[2], 'y1': kr[3], 'ze': 28, 'p': 0.8, 'over': (3, 3, 3, 3)}], salt=138)
    M.models += [{'name': '燈籠-門左', 'source': 'summit-rocher-01m-lantern', 'at': [122.5, R[1], 30.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '燈籠-門右', 'source': 'summit-rocher-01m-lantern', 'at': [158.5, R[1], 30.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '酒桶-後院', 'source': 'summit-rocher-01m-barrel', 'at': [160, 190, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'governor', 'title': '總督府（maison-forte 型：下層毛石開槍眼、上層木構釘板、紅瓦四坡頂、玻璃窗、兩根煙囪；前院低石牆、衛兵所、兩座站崗小亭各一門小砲、旗杆與白旗；後院分開的廚房）',
            'use': 'governor', 'lot': (28, 22), 'M': M, 'style': 'carib', 'layers': {'body': '牆身與院子', 'roof': '屋頂'}, 'flags': flags}


ALL = [market, townhall, customs, hospital, governor]
