# 英國那一套（風格 en；TASK-0772 第二段，皇家港 1660–1692）：海關、市場、醫院（推測）—— 史料 references/research_civic.md §10（Port Royal）。
# 皇家港跟法屬邊疆鎮最大的差別：磚造、兩到四層、很多房子有陽台、街道規整（LAWS83 To the Reader；HEATH「goodly Brick Houses … as fine as those in Cheapside」）。
# 座標同 civic.py（x 臨路寬、y 進深 y 0 臨路、z 往上；0.1 m／格）。
from civic import *
from townpub import trestle_table, small_house, end_gable, PRODUCE, MEAT

BRICK_A, BRICK_B, BRICK_M = 136, 168, 182      # 磚（深、淺兩色混砌）、灰縫 —— 磚牆只用在英國那一套
PAVE = 146                                     # 磚鋪地（深灰）


def brick_walls(M, rect, z0, z1, t=4, layer='body', salt=0):
    """磚牆（英式砌法的樣子：一皮 1 格、每 3 皮一道灰縫；丁頭與順頭交錯 ⇒ 每皮的豎縫錯開半塊）。"""
    X0, Y0, X1, Y1 = rect
    for z in range(z0, z1):
        row = (z - z0) // 3
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                if X0 + t <= x < X1 - t and Y0 + t <= y < Y1 - t:
                    continue
                u = x + y + (2 if row % 2 else 0)
                if (z - z0) % 3 == 2 or u % 5 == 0:
                    c = BRICK_M
                else:
                    c = BRICK_B if h01('bk', u // 5, row, salt) < 0.3 else BRICK_A
                M.put(layer, x, y, z, c)


def tile_roof(M, rects, salt=0, thick=2, layer='roof'):
    """紅陶瓦（kit 的 tile_color：法式套件那三色混鋪）—— Taylor 1688 說皇家港的房子瓦頂（只有〔摘要〕）。"""
    return build_roof(M, roof_field(rects), thick, layer, salt=salt)


def balcony(M, x0, x1, y0, y1, z, layer='gallery'):
    """木陽台：板面、外緣欄杆、底下兩道斜撐（撐到牆上）。"""
    M.box(layer, x0, y0, z, x1, y1, z + 1, FLOOR)
    rail(M, x0, x1, y0, z + 1, 9, layer=layer)
    for y in range(y0, y1):
        M.put(layer, x0, y, z + 10, FRAME)
        M.put(layer, x1 - 1, y, z + 10, FRAME)
        for zz in range(z + 1, z + 10):
            if (y - y0) % 3 == 0:
                M.put(layer, x0, y, zz, FRAME)
                M.put(layer, x1 - 1, y, zz, FRAME)
    for x in range(x0 + 2, x1 - 2, 30):                               # 托梁：板底下一根橫木從牆伸出來（斜撐一格一格是邊碰邊、算浮空 ⇒ 改直的）
        M.box(layer, x, y0, z - 2, x + 2, y1, z, FRAME)


def beam_scale(M, cx, cy, z0=0, layer='body'):
    """大橫桿秤（Clerk of the Market 的 beam scale，LAWS84；形制推測）：兩根柱＋橫梁、中間吊鏈、橫桿、兩端吊盤、秤錘。"""
    for x in (cx - 15, cx + 13):
        M.box(layer, x, cy, z0, x + 2, cy + 2, z0 + 26, FRAME)
    M.box(layer, cx - 15, cy, z0 + 24, cx + 15, cy + 2, z0 + 26, FRAME)
    M.box(layer, cx, cy, z0 + 16, cx + 1, cy + 1, z0 + 24, IRON)
    M.box(layer, cx - 12, cy, z0 + 15, cx + 13, cy + 1, z0 + 16, IRON)
    for x in (cx - 11, cx + 11):
        M.box(layer, x, cy, z0 + 7, x + 1, cy + 1, z0 + 15, IRON)
        M.box(layer, x - 3, cy - 2, z0 + 6, x + 4, cy + 4, z0 + 7, FRAME)
    M.box(layer, cx + 9, cy - 1, z0 + 7, cx + 13, cy + 3, z0 + 9, IRON)


# ─────────────────────────────── 海關（Custom-house）16 × 14 m ───────────────────────────────
def en_customs():
    """海關（§10.3）：「hither resort most of the Ships, here is the Custom-house, here live the Merchants」（LAWS83）；在濱水那條叫「the Wharf」的街上，
    街上是講究的磚房。Custom-house 本身的尺寸、外觀沒查到 ⇒ 照考古的 Building 1（磚造 53 × 47 英尺、6 間、兩層，JPR；跟 16 × 14 m 的框幾乎一樣大）：
    磚牆兩層、樓下臨街三個開間各一扇雙扇門（收稅廳與倉）、樓上辦公（推測分配）、樓上前面一道木陽台（Hanson：很多房子有陽台）、紅瓦四坡頂、兩根煙囪。"""
    X, Y, Z = 160, 140, 140
    M = Model((X, Y, Z))
    R = (4, 12, 156, 136)                                               # 15.2 × 12.4 m
    brick_walls(M, R, 0, 33, 4, salt=141)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 1, PAVE)
    M.box('body', R[0] + 2, R[1] + 2, 32, R[2] - 2, R[3] - 2, 34, FLOOR)
    brick_walls(M, R, 33, 62, 4, salt=142)
    for x in (54, 106):                                                 # 樓下隔成六間：兩道橫牆（門洞）＋一道縱牆
        M.box('body', x, R[1] + 4, 1, x + 2, R[3] - 4, 32, BRICK_A)
        M.clear(x, 66, 1, x + 2, 82, 22)
    M.box('body', R[0] + 4, 74, 1, R[2] - 4, 76, 32, BRICK_A)
    for x0 in (20, 72, 124):
        M.clear(x0, 74, 1, x0 + 14, 76, 22)
    for i, cx in enumerate((30, 80, 130)):
        put_part(M, 'door-double', '前-門%d' % (i + 1), 'front', R, cx, 1, 4)
        put_part(M, 'window', '前-樓上窗%d' % (i + 1), 'front', R, cx, 40, 4)
        put_part(M, 'window', '後-窗%d' % (i + 1), 'back', R, cx, 10, 4)
        put_part(M, 'window', '後-樓上窗%d' % (i + 1), 'back', R, cx, 40, 4)
    for face in ('left', 'right'):
        for j, cy in enumerate((44, 104)):
            put_part(M, 'window', '%s-窗%d' % (face, j + 1), face, R, cy, 10, 4)
            put_part(M, 'window', '%s-樓上窗%d' % (face, j + 1), face, R, cy, 40, 4)
    M.anchor('door', 80, R[1] - 1, 1)
    M.box('body', 4, 4, 0, 156, 12, 1, PAVE)                            # 門前磚鋪的人行道（HM：很多建築前有磚鋪人行道）
    balcony(M, 10, 150, 4, 12, 34)                                     # 貼到牆（y 12）
    top = tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 62, 'p': 0.6, 'over': (3, 3, 4, 3)}], salt=143)
    for i, (cx, cy) in enumerate(((30, 96), (122, 96))):
        free_part(M, 'chimney', '煙囪%d' % (i + 1), (cx, cy, top[(cx + 4, cy + 3)] - 10))
    M.models += [{'name': '貨桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [8, 2, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-1', 'source': 'summit-rocher-01m-crate', 'at': [146, 2, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [56.5, R[1], 26.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'en-customs', 'title': '海關（Custom-house：照考古 Building 1 的磚造兩層、六間；樓下臨街三扇雙扇門、樓上木陽台、紅瓦四坡頂、兩根煙囪、門前磚鋪人行道）',
            'use': 'customs', 'lot': (16, 14), 'M': M, 'style': 'en', 'layers': {'body': '磚牆', 'gallery': '陽台', 'roof': '屋頂'}}


# ─────────────────────────────── 市場（Market place）20 × 16 m ───────────────────────────────
def en_market():
    """市場（§10.4）：1662 年起有市場、1671 年有 Clerk of the Market；用他自己的秤裁決重量、禁用提秤（LAWS84）；屠戶與捕龜人要在 open Market 零售；
    敲鐘開市（LES）；肉市天亮前宰、7 點前散（SL）。有沒有頂棚建築沒查到 ⇒ 一塊開敞的磚鋪市場空地為主；
    後面一座小的英式 Market-House（樓下開敞的磚墩、樓上一間放秤與書記、屋頂小鐘樓 —— 推測，只有 Ward 1698「built rather like a Market-House」當旁證）；
    前面左右兩座肉攤棚、中間 Clerk 的大橫桿秤、幾張菜攤。龜欄（港裡的方形木柵）沒放：地塊不一定臨水。"""
    X, Y, Z = 200, 160, 110
    M = Model((X, Y, Z))
    M.box('body', 0, 0, 0, X, Y, 1, PAVE)                               # 整片磚鋪地
    for x in range(0, X, 4):
        for y in range(0, Y):
            if (y // 2 + x // 4) % 2 == 0:
                M.put('body', x, y, 0, BRICK_A, force=True)
    # Market-House：8 × 6 m，樓下六根磚墩開敞、樓上磚牆一間、紅瓦四坡頂、屋脊上一座小鐘樓
    R = (60, 92, 140, 152)
    for (px, py) in ((60, 92), (96, 92), (132, 92), (60, 144), (96, 144), (132, 144)):
        brick_walls(M, (px, py, px + 8, py + 8), 1, 30, 4, salt=150 + px + py)
    M.box('body', R[0], R[1], 30, R[2], R[3], 32, FLOOR)
    brick_walls(M, R, 32, 56, 3, salt=151)
    for i, cx in enumerate((80, 120)):
        put_part(M, 'window', '前-樓上窗%d' % (i + 1), 'front', R, cx, 38, 3)
        put_part(M, 'window', '後-樓上窗%d' % (i + 1), 'back', R, cx, 38, 3)
    for face in ('left', 'right'):
        put_part(M, 'window', '%s-樓上窗' % face, face, R, 122, 38, 3)
    for k in range(10):                                                 # 上樓的木梯（樓下中間，從前往後爬）
        M.box('body', 96, 104 + k * 3, 0, 104, 107 + k * 3, 3 + k * 3, FRAME)
    top = tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 56, 'p': 0.7, 'over': (4, 4, 4, 4)}], salt=152)
    cx, cy = 100, 122                                                   # 鐘樓：四根柱、小四坡頂、一口鐘
    zb = top[(cx, cy)]
    for (px, py) in ((cx - 7, cy - 7), (cx + 5, cy - 7), (cx - 7, cy + 5), (cx + 5, cy + 5)):
        M.box('roof', px, py, zb - 2, px + 2, py + 2, zb + 18, FRAME, force=True)
    M.box('roof', cx - 7, cy - 7, zb + 18, cx + 7, cy + 7, zb + 20, FRAME, force=True)
    btop = build_roof(M, roof_field([{'x0': cx - 7, 'y0': cy - 7, 'x1': cx + 7, 'y1': cy + 7, 'ze': zb + 20, 'p': 0.9, 'over': (2, 2, 2, 2)}]), 2, 'roof', salt=153)
    for z in range(zb + 9, zb + 17):
        r = 1 + (zb + 16 - z) // 2
        M.box('roof', cx - r, cy - r, z, cx + r, cy + r, z + 1, BRONZE)
    M.box('roof', cx - 1, cy - 1, zb + 15, cx + 1, cy + 1, zb + 18, IRON, force=True)   # 吊鐘的鐵環：鐘頂吊到上面那一圈頂板
    M.anchor('bell', cx, cy, zb + 12)
    # 前面：兩座肉攤棚（木柱、木瓦單坡頂、案板、掛肉）、中間的大橫桿秤、菜攤
    for i, x0 in enumerate((10, 140)):
        lean_roof_posts(M, x0, 14, x0 + 50, 50, 28, 0.25, 'front', shingle_color, [(x0 + 2, 16), (x0 + 46, 16), (x0 + 2, 46), (x0 + 46, 46)], salt=154 + i)
        trestle_table(M, x0 + 6, x0 + 44, 22, 30, z=9)
        M.box('body', x0 + 2, 46, 18, x0 + 48, 48, 19, FRAME)               # 掛肉的橫桿架在後面兩根柱上
        for x in range(x0 + 10, x0 + 42, 9):
            M.box('body', x, 46, 10, x + 4, 48, 18, MEAT)
    beam_scale(M, 100, 40)
    for (x0, y0) in ((20, 64), (140, 64)):
        trestle_table(M, x0, x0 + 40, y0, y0 + 8)
        for i in range(6):
            M.box('body', x0 + 2 + i * 6, y0 + 2, 9, x0 + 6 + i * 6, y0 + 6, 11, PRODUCE[i % len(PRODUCE)])
    M.models += [{'name': '桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [70, 60, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '桶-2', 'source': 'summit-rocher-01m-barrel', 'at': [130, 60, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱', 'source': 'summit-rocher-01m-crate', 'at': [170, 80, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-市場屋', 'source': 'summit-rocher-01m-lantern', 'at': [100.5, R[1], 22.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('door', 100, 0, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'en-market', 'title': '市場（Market place：磚鋪的市場空地；後面小的英式市場屋 —— 樓下磚墩開敞、樓上一間、紅瓦四坡頂、敲鐘開市的小鐘樓；前面兩座肉攤棚、大橫桿秤、菜攤）',
            'use': 'market', 'lot': (20, 16), 'M': M, 'style': 'en', 'layers': {'body': '鋪地、磚墩與攤', 'roof': '屋頂與鐘樓'}}


# ─────────────────────────────── 醫院 20 × 16 m（推測）───────────────────────────────
def en_hospital():
    """醫院（§10.5）：⛔ 1692 年以前查不到 Port Royal 有醫院（CSP 1681–92 搜 hospital／surgeon／sick 都沒有；1692 年 8 月才有 Kingston「蓋一間醫院」的罰款用途）。
    Tim 2026-10-21 選「補一棟」⇒ 照研究的建模建議：一棟**徵用的磚造兩層商人屋**當病房（照考古 Building 1 的磚造兩層），整棟都是推測：
    樓下臨街一扇雙扇門、兩扇窗，樓上木陽台；裡面上下兩層各兩排床；後院磚牆圍起來，一間磚砌的廚房（煙囪）、一口井、一條晾床單的繩。"""
    X, Y, Z = 200, 160, 140
    M = Model((X, Y, Z))
    R = (10, 12, 190, 100)                                              # 18 × 8.8 m
    brick_walls(M, R, 0, 33, 4, salt=161)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 1, PAVE)
    M.box('body', R[0] + 2, R[1] + 2, 32, R[2] - 2, R[3] - 2, 34, FLOOR)
    brick_walls(M, R, 33, 62, 4, salt=162)
    put_part(M, 'door-double', '前-門', 'front', R, 100, 1, 4)
    for i, cx in enumerate((40, 160)):
        put_part(M, 'window', '前-窗%d' % (i + 1), 'front', R, cx, 10, 4)
    for i, cx in enumerate((40, 100, 160)):
        put_part(M, 'window', '前-樓上窗%d' % (i + 1), 'front', R, cx, 40, 4)
        put_part(M, 'window', '後-樓上窗%d' % (i + 1), 'back', R, cx, 40, 4)
    for i, cx in enumerate((40, 160)):
        put_part(M, 'window', '後-窗%d' % (i + 1), 'back', R, cx, 10, 4)
    put_part(M, 'door-plank', '後-門', 'back', R, 100, 1, 4)
    for face in ('left', 'right'):
        put_part(M, 'window', '%s-窗' % face, face, R, 56, 10, 4)
        put_part(M, 'window', '%s-樓上窗' % face, face, R, 56, 40, 4)
    for x0 in list(range(18, 84, 12)) + list(range(118, 182, 12)):   # 床：上下兩層、各兩排（靠前牆、後牆，中間留走道）
        for (y0, y1) in ((17, 35), (77, 95)):
            for zf in (1, 34):
                M.box('body', x0, y0, zf, x0 + 8, y1, zf + 3, FRAME)
                M.box('body', x0, y0, zf + 3, x0 + 8, y1, zf + 4, LIME)
    for k in range(11):                                                 # 上樓的木梯（門廳右邊，從後往前爬）
        M.box('body', 112, 90 - k * 3, 1, 118, 93 - k * 3, 4 + k * 3, FRAME)
    M.anchor('door', 100, R[1] - 1, 1)
    M.box('body', 10, 4, 0, 190, 12, 1, PAVE)                           # 門前磚鋪人行道
    balcony(M, 16, 184, 4, 12, 34)
    top = tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 62, 'p': 0.6, 'over': (3, 3, 4, 3)}], salt=163)
    free_part(M, 'chimney', '煙囪', (150, 56, top[(154, 59)] - 10))
    # 後院：磚牆、廚房（磚、單坡瓦頂、灶、煙囪）、井、晾床單的繩
    for (x0, y0, x1, y1) in ((10, 100, 14, 156), (186, 100, 190, 156), (10, 152, 190, 156)):
        brick_walls(M, (x0, y0, x1, y1), 0, 20, 4, salt=164 + x0)
    kr = (20, 120, 70, 152)
    brick_walls(M, kr, 0, 26, 3, salt=167)
    put_part(M, 'door-plank', '廚房-門', 'right', kr, 136, 0, 3)
    hearth(M, 26, 140, 42, 149, hanger=False)
    ktop = tile_roof(M, [{'x0': kr[0], 'y0': kr[1], 'x1': kr[2], 'y1': kr[3], 'ze': 26, 'p': 0.7, 'over': (2, 2, 2, 2)}], salt=168)
    free_part(M, 'chimney', '廚房-煙囪', (28, 140, ktop[(32, 143)] - 10))
    M.box('body', 120, 116, 0, 136, 132, 8, BRICK_A)                    # 井（磚圈、暗的井口、木架）
    M.box('body', 123, 119, 1, 133, 129, 8, DARK, force=True)
    for x in (120, 134):
        M.box('body', x, 123, 8, x + 2, 125, 22, FRAME)
    M.box('body', 120, 123, 22, 136, 125, 23, FRAME)
    for x in (150, 182):                                                # 晾床單：兩根柱、一條繩、三塊白布
        M.box('body', x, 136, 0, x + 2, 138, 20, FRAME)
    M.box('body', 150, 136, 19, 184, 138, 20, THATCH_A)
    for x in (154, 164, 174):
        M.box('body', x, 136, 10, x + 7, 137, 19, LIME)
    M.models += [{'name': '水桶-井', 'source': 'summit-rocher-01m-barrel', 'at': [140, 118, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [76.5, R[1], 26.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'en-hospital', 'title': '醫院（推測：徵用的磚造兩層商人屋當病房 —— 1692 年以前查不到 Port Royal 有醫院；上下兩層各兩排床、樓上木陽台、紅瓦四坡頂；後院磚牆、廚房、井、晾床單的繩）',
            'use': 'hospital', 'lot': (20, 16), 'M': M, 'style': 'en', 'layers': {'body': '磚牆與後院', 'gallery': '陽台', 'roof': '屋頂'}}


ALL = [en_customs, en_market, en_hospital]
