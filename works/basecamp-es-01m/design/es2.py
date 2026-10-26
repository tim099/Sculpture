# 西班牙風格（es）第二批（TASK-0975 第三格；Tim 2026-10-26「第二批開工吧」）：教堂、市政廳（cabildo）、總督府、市場、酒館、倉庫；
#   住宅照 fr 那一套的佔地都要有 —— 低密度 8 × 12、8 × 10、8 × 8（a、b、c 三型）；中密度（level 2）12 × 12、8 × 12；高密度（level 3）16 × 16、12 × 12。
# 牆、屋頂、窗、門框、鐘牆、拱廊照第一批（es.py）；這一批多兩樣：
#   - 木格柵的封閉陽台（balcón de celosía）：聖地牙哥的 Velázquez 之家（16 世紀）樓上的陽台用木格柵封起來、看得出去、看不進來〔摘：passportandbaggage、cubadecentel〕；
#     哈瓦那的車製木陽台、木窗是 18 世紀前半才多起來〔摘：OHC 的文章〕⇒ 1660 年代只放在有錢人家（住宅 c、中高密度、總督府）。
#   - 窮人家：編條糊泥（bahareque）刷白、棕櫚葉（guano）頂 —— 聖地牙哥教堂的穹頂也是「cuje／embarrado：泥糊在細竹上」〔摘：佛羅倫斯大學〕。
# 座標、規矩同 es.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
from es import *                                                       # noqa: F401,F403

FL = 32                          # 一層樓高（地板到地板 3.2 m）
LATTICE = FRAME                  # 木格柵（深色木）
TILE_S = 168                     # 陽台小屋頂的瓦


# ─────────────────────────────── 小件 ───────────────────────────────
def slab(M, R, z, t, c=FLOOR):
    """樓板：牆裡面那一塊、z..z+2。"""
    M.box('body', R[0] + t, R[1] + t, z, R[2] - t, R[3] - t, z + 2, c)


def celosia(M, x0, x1, yw, z, h=24, d=4):
    """木格柵的封閉陽台（balcón de celosía）：貼在正面牆（牆外表面 y ＝ yw）往外 d 格；地板 z、兩根托梁；
    正面與兩側是方格的木格柵（每 3 格一道直、一道橫 ⇒ 6 連通、不會一格一格浮空）、上下兩道框、頂上一片小瓦頂。"""
    ya = yw - d
    M.box('body', x0, ya, z, x1, yw, z + 1, FLOOR, force=True)          # 地板
    for x in (x0 + 2, x1 - 4):                                          # 托梁（從牆伸出來）
        M.box('body', x, ya, z - 3, x + 2, yw, z, FRAME, force=True)
    for zz in range(z + 1, z + h):
        for x in range(x0, x1):
            if x in (x0, x1 - 1) or zz in (z + 1, z + h - 1) or x % 3 == 0 or zz % 3 == 0:
                M.put('body', x, ya, zz, LATTICE, force=True)
        for y in range(ya + 1, yw):
            for x in (x0, x1 - 1):
                if y == yw - 1 or zz in (z + 1, z + h - 1) or y % 3 == 0 or zz % 3 == 0:
                    M.put('body', x, y, zz, LATTICE, force=True)
    M.box('body', x0 - 1, ya - 1 if ya > 0 else ya, z + h, x1 + 1, yw, z + h + 1, TILE_S, force=True)   # 小瓦頂（多出一圈）
    M.box('body', x0 - 1, ya - 1 if ya > 0 else ya, z + h + 1, x1 + 1, yw, z + h + 2, TILE_R, force=True)


def yard_wall(M, X, y0, y1, h=24, t=4, plinth=4, salt=0):
    """後院的圍牆（刷白砌石）：x 4..X−4、y0..y1，前面那一道（貼著屋子的後牆）不砌。"""
    masonry(M, (4, y0, X - 4, y1), 0, h, t, plinth=plinth, salt=salt)
    M.clear(4 + t, y0, 0, X - 4 - t, y0 + t, h)
    M.box('body', 4 + t, y0, 0, X - 4 - t, y1 - t, 1, EARTH_W)


def kitchen(M, R, salt=0):
    """後院的廚房小屋（刷白砌石、單坡瓦頂往院子那一邊低、裡面一座灶）。"""
    masonry(M, R, 0, 24, 3, plinth=3, salt=salt)
    shed_roof(M, R[0], R[1], R[2], R[3], 30, 0.25, low='front', color_fn=None)
    hearth(M, R[0] + 4, R[3] - 10, R[0] + 18, R[3] - 4, hanger=False)
    put_part(M, 'door-plank', '廚房-門', 'front', R, (R[0] + R[2]) // 2 + 4, 0, 3)


def arch_cut(M, axis, a0, a1, w0, w1, z0, zs):
    """在牆上挖一個圓拱洞：axis 'x' ⇒ 洞沿 x 開（a0..a1）、穿過 y 的 w0..w1；'y' 反過來。z0..zs 是直的、上面半圓。"""
    ac, r = (a0 + a1) / 2.0, (a1 - a0) / 2.0
    for a in range(a0, a1):
        for z in range(z0, int(zs + r) + 1):
            da = a + 0.5 - ac
            if z < zs or da * da + (z + 0.5 - zs) ** 2 <= r * r:
                for w in range(w0, w1):
                    x, y = (a, w) if axis == 'x' else (w, a)
                    M.clear(x, y, z, x + 1, y + 1, z + 1, 'body')


def hip_tile(M, R, ze, p=0.5, over=(3, 3, 3, 3), gable=None, salt=0):
    r = {'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': ze, 'p': p, 'over': over}
    if gable:
        r['gable'] = gable
    return tile_roof(M, [r], salt=salt)


# ─────────────────────────────── 住宅（低密度）8 × 12、8 × 10、8 × 8 ───────────────────────────────
def _house_a(D):
    """A：一層的砌石屋（casa de mampostería）—— 臨街一棟 7.2 × 6 m、牆高 3.6 m、兩坡瓦頂（屋脊順著街）；左邊雙扇門＋切石門框、右邊一扇木欄杆窗（ventana de reja）；
    後面刷白的院牆、院底廚房小屋與蓄水池井口（院子夠深才擺）。"""
    M = Model((80, D, 80))
    R = (4, 2, 76, 62)
    masonry(M, R, 0, 36, 5, salt=9811)
    tile_floor(M, R[0] + 5, R[1] + 5, R[2] - 5, R[3] - 5)
    hip_tile(M, R, 36, 0.5, (2, 2, 2, 3), gable='x', salt=9812)
    for x0, x1 in ((R[0], R[0] + 5), (R[2] - 5, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 36, 0.5, z0=36, color=CAL, edge=CORAL)
    put_part(M, 'door-double', '前-門', 'front', R, 24, 0, 5)
    portal(M, R, 24, 20, 27, salt=9813)
    put_part(M, 'window-baluster', '前-窗', 'front', R, 56, 8, 5)
    put_part(M, 'door-plank', '後-門', 'back', R, 40, 0, 5)
    if D > 62 + 8:
        yard_wall(M, 80, 62, D - 2, salt=9814)
        if D >= 100:
            kitchen(M, (8, D - 28, 34, D - 6), salt=9815)
        if D >= 120:
            aljibe(M, 60, D - 30, 6, 7)
    lantern(M, '燈籠-門', (38.5, R[1], 24))
    yield_to_parts(M)
    M.anchor('door', 24, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return M


def _house_b(D):
    """B：編條糊泥的小屋（bahareque、bohío）—— 6 × 5 m、叉柱與木地檻露在外面、刷白；四坡棕櫚葉（guano）頂垂到 2 m 上下；
    木板門、一扇木板窗；後院木柵、露天的灶（兩根叉柱掛鍋）。"""
    M = Model((80, D, 70))
    R = (10, 6, 70, 56)
    M.box('body', R[0] + 3, R[1] + 3, 0, R[2] - 3, R[3] - 3, 1, EARTH_W)
    daub_walls(M, R, 0, 26, 3, CAL, bay=14)
    M.box('body', R[0] + 3, R[1] + 3, 0, R[2] - 3, R[3] - 3, 1, EARTH_W)
    thatch_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 26, 'p': 0.9, 'over': (5, 5, 4, 4)}], salt=9821)
    put_part(M, 'door-plank', '前-門', 'front', R, 28, 0, 3)
    put_part(M, 'window-board', '前-窗', 'front', R, 54, 8, 3)
    put_part(M, 'door-plank', '後-門', 'back', R, 40, 0, 3)
    if D > 70:
        picket_fence(M, [(4, 62), (4, D - 3), (75, D - 3), (75, 62)], z1=12, color=FRAME)
        hearth(M, 30, D - 22 if D >= 100 else D - 16, 46, (D - 14) if D >= 100 else D - 8, hanger=True)
    M.anchor('door', 28, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    yield_to_parts(M)
    return M


def _house_c(D):
    """C：兩層的街屋（casa alta）—— 樓下做生意（雙扇大門＋切石門框、小門）、樓上住人：中間一座木格柵的封閉陽台（照 Velázquez 之家）＋木欄杆窗；
    四坡瓦頂；後面院牆、廚房、井。"""
    M = Model((80, D, 100))
    R = (4, 6, 76, 66)
    masonry(M, R, 0, 2 * FL, 5, salt=9831)
    tile_floor(M, R[0] + 5, R[1] + 5, R[2] - 5, R[3] - 5)
    slab(M, R, FL, 5)
    hip_tile(M, R, 2 * FL, 0.5, (2, 2, 3, 3), salt=9832)
    put_part(M, 'door-double', '前-店門', 'front', R, 22, 0, 5)
    portal(M, R, 22, 20, 27, salt=9833)
    put_part(M, 'door-plank', '前-小門', 'front', R, 58, 0, 5)
    put_part(M, 'window-baluster', '樓上-窗（陽台裡）', 'front', R, 48, FL + 4, 5)
    put_part(M, 'window-baluster', '樓上-窗', 'front', R, 16, FL + 6, 5)
    celosia(M, 32, 66, R[1], FL, h=24, d=4)
    put_part(M, 'door-plank', '後-門', 'back', R, 40, 0, 5)
    if D > 66 + 8:
        yard_wall(M, 80, 66, D - 2, salt=9834)
        if D >= 100:
            kitchen(M, (46, D - 28, 72, D - 6), salt=9835)
        if D >= 120:
            aljibe(M, 22, D - 30, 6, 7)
    lantern(M, '燈籠-門', (36.5, R[1], 24))
    yield_to_parts(M)
    M.anchor('door', 22, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return M


HOUSE_TITLE = {
    'a': '住宅 A（一層的砌石屋：刷白、兩坡瓦頂、切石門框、木欄杆窗；後院院牆、廚房、蓄水池井口）',
    'b': '住宅 B（編條糊泥的小屋 bahareque：刷白、四坡棕櫚葉頂、木板門窗；後院木柵、露天的灶）',
    'c': '住宅 C（兩層的街屋：樓下店門與切石門框、樓上木格柵的封閉陽台、四坡瓦頂；後院院牆、廚房、井）',
}
HOUSE_FN = {'a': _house_a, 'b': _house_b, 'c': _house_c}
SIZE_TAG = {120: '', 100: '-s', 80: '-xs'}
SIZE_NOTE = {120: '', 100: '淺版 8 × 10：院子縮到後緣，', 80: '小版 8 × 8：沒有院子，'}


def _house_factory(t, D):
    def f():
        M = HOUSE_FN[t](D)
        title = HOUSE_TITLE[t]
        if SIZE_NOTE[D]:
            title = title.replace('（', '（' + SIZE_NOTE[D], 1)
        return {'key': 'house-%s%s' % (t, SIZE_TAG[D]), 'variant': '%s%s' % (t, SIZE_TAG[D]), 'style': 'es', 'title': title,
                'use': 'house', 'lot': (8, D // 10), 'M': M, 'layers': {'body': '牆身與院子', 'roof': '屋頂'}}
    f.__name__ = 'house_%s%s' % (t, SIZE_TAG[D].replace('-', '_'))
    return f


HOUSES = [_house_factory(t, D) for D in (120, 100, 80) for t in 'abc']


# ─────────────────────────────── 住宅（中、高密度） ───────────────────────────────
def house_m_a():
    """中密度 M-A（12 × 12，level 2，住 12 人）：兩層的院落屋（casa de patio）—— 臨街一棟 11.2 × 6 m、中間的門廊（zaguán）切石門框、兩扇木欄杆窗；
    樓上中間一座木格柵陽台＋三扇窗；四坡瓦頂；後面右側一層的廚房與下人房（單坡瓦頂）、院子、蓄水池井口。"""
    M = Model((120, 120, 110))
    R = (4, 4, 116, 64)
    masonry(M, R, 0, 2 * FL, 5, salt=9841)
    tile_floor(M, R[0] + 5, R[1] + 5, R[2] - 5, R[3] - 5)
    slab(M, R, FL, 5)
    hip_tile(M, R, 2 * FL, 0.5, (3, 3, 3, 3), salt=9842)
    put_part(M, 'door-double', '前-門廊', 'front', R, 60, 0, 5)
    portal(M, R, 60, 20, 27, salt=9843)
    for cx in (26, 94):
        put_part(M, 'window-baluster', '前-窗%d' % (1 if cx < 60 else 2), 'front', R, cx, 8, 5)
        put_part(M, 'window-baluster', '樓上-窗%d' % (1 if cx < 60 else 2), 'front', R, cx, FL + 6, 5)
    put_part(M, 'window-baluster', '樓上-窗（陽台裡）', 'front', R, 60, FL + 4, 5)
    celosia(M, 42, 78, R[1], FL, h=24, d=4)
    put_part(M, 'door-plank', '後-門', 'back', R, 40, 0, 5)
    yard_wall(M, 120, 64, 118, h=26, salt=9844)
    W = (80, 64, 116, 114)                                             # 右側一層的廚房與下人房
    masonry(M, W, 0, 30, 4, plinth=4, salt=9845)
    shed_roof(M, W[0], W[1], W[2], W[3], 36, 0.25, low='left')
    put_part(M, 'door-plank', '側屋-門', 'left', W, 90, 0, 4)
    hearth(M, 96, 98, 110, 106, hanger=False)
    aljibe(M, 40, 90, 6, 7)
    lantern(M, '燈籠-門', (74.5, R[1], 24))
    yield_to_parts(M)
    M.anchor('door', 60, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-a', 'variant': 'm-a', 'style': 'es', 'meta': {'level': 2, 'live': 12},
            'title': '中密度住宅 M-A（兩層的院落屋 casa de patio：門廊切石門框、木欄杆窗、樓上木格柵陽台、四坡瓦頂；右側廚房與下人房、院子、蓄水池井口）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身與院子', 'roof': '屋頂'}}


def house_m_b():
    """中密度 M-B（8 × 12，level 2，住 8 人）：低密度同一塊蓋兩層的窄街屋 —— 臨街 7.2 × 7 m 兩層、樓下店門＋小門、樓上木格柵陽台；四坡瓦頂；後院、井。"""
    M = Model((80, 120, 100))
    R = (4, 6, 76, 76)
    masonry(M, R, 0, 2 * FL, 5, salt=9851)
    tile_floor(M, R[0] + 5, R[1] + 5, R[2] - 5, R[3] - 5)
    slab(M, R, FL, 5)
    hip_tile(M, R, 2 * FL, 0.5, (2, 2, 3, 3), salt=9852)
    put_part(M, 'door-double', '前-店門', 'front', R, 22, 0, 5)
    portal(M, R, 22, 20, 27, salt=9853)
    put_part(M, 'door-plank', '前-小門', 'front', R, 58, 0, 5)
    put_part(M, 'window-baluster', '樓上-窗（陽台裡）', 'front', R, 40, FL + 4, 5)
    celosia(M, 22, 58, R[1], FL, h=24, d=4)
    put_part(M, 'door-plank', '後-門', 'back', R, 40, 0, 5)
    yard_wall(M, 80, 76, 118, salt=9854)
    aljibe(M, 56, 98, 6, 7)
    lantern(M, '燈籠-門', (36.5, R[1], 24))
    yield_to_parts(M)
    M.anchor('door', 22, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-b', 'variant': 'm-b', 'style': 'es', 'meta': {'level': 2, 'live': 8},
            'title': '中密度住宅 M-B（兩層的窄街屋：樓下店門與切石門框、樓上木格柵陽台、四坡瓦頂；後院、井）',
            'use': 'house', 'lot': (8, 12), 'M': M, 'layers': {'body': '牆身與院子', 'roof': '屋頂'}}


def house_h_a():
    """高密度 H-A（16 × 16，level 3，住 24 人）：三層的大宅（casa de altos）—— 臨街一棟 15.2 × 6.6 m 三層＋右側三層的側翼，圍出內院；
    樓下中間門廊、兩側兩間店；二樓通長的木格柵陽台、三樓木欄杆窗＋一道開敞的木陽台；四坡瓦頂；院子的蓄水池井口與院牆。"""
    M = Model((160, 160, 140))
    R = (4, 4, 156, 70)
    H = 3 * FL
    masonry(M, R, 0, H, 6, salt=9861)
    tile_floor(M, R[0] + 6, R[1] + 6, R[2] - 6, R[3] - 6)
    for k in (1, 2):
        slab(M, R, k * FL, 6)
    hip_tile(M, R, H, 0.5, (3, 3, 3, 3), salt=9862)
    put_part(M, 'door-double', '前-門廊', 'front', R, 80, 0, 6)
    portal(M, R, 80, 20, 27, salt=9863)
    for cx in (30, 130):
        put_part(M, 'door-double', '前-店門%d' % (1 if cx < 80 else 2), 'front', R, cx, 0, 6)
    for cx in (52, 108):
        put_part(M, 'window-baluster', '前-窗%d' % (1 if cx < 80 else 2), 'front', R, cx, 8, 6)
    for i, cx in enumerate((26, 62, 98, 134)):
        put_part(M, 'window-baluster', '二樓-窗%d' % (i + 1), 'front', R, cx, FL + 4, 6)
        put_part(M, 'window-baluster', '三樓-窗%d' % (i + 1), 'front', R, cx, 2 * FL + 4, 6)
    celosia(M, 14, 146, R[1], FL, h=24, d=4)
    balcony(M, 48, 112, 0, 4, 2 * FL + 1, layer='body')
    put_part(M, 'door-plank', '後-門', 'back', R, 50, 0, 6)
    W = (110, 70, 156, 156)                                            # 右側的三層側翼
    masonry(M, W, 0, H, 5, salt=9864)
    for k in (1, 2):
        slab(M, W, k * FL, 5)
    hip_tile(M, W, H, 0.5, (3, 3, 0, 3), gable='y', salt=9865)
    for i, cy in enumerate((92, 130)):
        put_part(M, 'door-plank' if i == 0 else 'window-baluster', '側翼-%s' % ('門' if i == 0 else '窗'), 'left', W, cy, 0 if i == 0 else 8, 5)
        put_part(M, 'window-baluster', '側翼-二樓窗%d' % (i + 1), 'left', W, cy, FL + 4, 5)
        put_part(M, 'window-baluster', '側翼-三樓窗%d' % (i + 1), 'left', W, cy, 2 * FL + 4, 5)
    masonry(M, (4, 70, 110, 156), 0, 30, 4, plinth=4, salt=9866)        # 院牆
    M.clear(8, 70, 0, 106, 74, 30)
    M.clear(106, 74, 0, 110, 152, 30)
    M.box('body', 8, 74, 0, 106, 152, 1, EARTH_W)
    aljibe(M, 56, 112, 7, 8)
    lantern(M, '燈籠-門', (94.5, R[1], 24))
    yield_to_parts(M)
    M.anchor('door', 80, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-a', 'variant': 'h-a', 'style': 'es', 'meta': {'level': 3, 'live': 24},
            'title': '高密度住宅 H-A（三層的大宅 casa de altos：臨街一棟＋右側三層側翼圍出內院；門廊、兩間店、二樓通長木格柵陽台、三樓木陽台、四坡瓦頂；蓄水池井口）',
            'use': 'house', 'lot': (16, 16), 'M': M, 'layers': {'body': '牆身與院子', 'roof': '屋頂'}}


def house_h_b():
    """高密度 H-B（12 × 12，level 3，住 13 人）：中密度同一塊蓋三層 —— 臨街一棟 11.2 × 7 m、樓下門廊與店、二樓木格柵陽台、三樓窗；四坡瓦頂；後院、井。"""
    M = Model((120, 120, 140))
    R = (4, 4, 116, 74)
    H = 3 * FL
    masonry(M, R, 0, H, 6, salt=9871)
    tile_floor(M, R[0] + 6, R[1] + 6, R[2] - 6, R[3] - 6)
    for k in (1, 2):
        slab(M, R, k * FL, 6)
    hip_tile(M, R, H, 0.5, (3, 3, 3, 3), salt=9872)
    put_part(M, 'door-double', '前-門廊', 'front', R, 60, 0, 6)
    portal(M, R, 60, 20, 27, salt=9873)
    put_part(M, 'door-double', '前-店門', 'front', R, 24, 0, 6)
    put_part(M, 'window-baluster', '前-窗', 'front', R, 96, 8, 6)
    for i, cx in enumerate((24, 60, 96)):
        put_part(M, 'window-baluster', '二樓-窗%d' % (i + 1), 'front', R, cx, FL + 4, 6)
        put_part(M, 'window-baluster', '三樓-窗%d' % (i + 1), 'front', R, cx, 2 * FL + 4, 6)
    celosia(M, 12, 108, R[1], FL, h=24, d=4)
    put_part(M, 'door-plank', '後-門', 'back', R, 60, 0, 6)
    yard_wall(M, 120, 74, 118, h=26, salt=9874)
    aljibe(M, 30, 96, 6, 7)
    lantern(M, '燈籠-門', (74.5, R[1], 24))
    yield_to_parts(M)
    M.anchor('door', 60, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-b', 'variant': 'h-b', 'style': 'es', 'meta': {'level': 3, 'live': 13},
            'title': '高密度住宅 H-B（三層的街屋：門廊與店、二樓木格柵陽台、三樓木欄杆窗、四坡瓦頂；後院、井）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身與院子', 'roof': '屋頂'}}


# ─────────────────────────────── 教堂（iglesia parroquial）16 × 28 m ───────────────────────────────
def church():
    """教堂：一間的長堂（11.2 × 22 m、牆厚 0.8 m、牆高 8 m）、兩側每 4 m 一道扶壁、紅陶瓦兩坡頂；正面山牆高出屋面、頂上一面寬的鐘牆開兩個拱洞各掛一口鐘；
    切石門框、門上一扇唱詩台的木欄杆窗；兩側高處的木欄杆窗；右後一間聖器室（單坡瓦頂）；裡面陶磚地、高一階的聖壇、描金的祭壇屏、長凳；前面石鋪的前庭與石十字。
    - 照什麼：聖地牙哥的主堂 1522／1528 起造、1662 年被海盜洗劫後重建〔摘：Wikipedia〈Timeline of Santiago de Cuba〉、travel2unlimited〕；形制〔沒查到〕。
    - 設計：一間的長堂、扶壁、鐘牆（小鎮教堂的通法，見小教堂）、尺寸、聖器室的位置。"""
    X, Y, Z = 160, 280, 170
    M = Model((X, Y, Z))
    R = (24, 30, 136, 250)
    t, H = 8, 80
    cobbles(M, 4, 0, 156, R[1], salt=9881)
    masonry(M, R, 0, H, t, salt=9882)
    tile_floor(M, R[0] + t, R[1] + t, R[2] - t, R[3] - t)
    M.box('body', R[0] + t, 214, 1, R[2] - t, R[3] - t, 3, CORAL)       # 聖壇高一階
    for y in range(70, 240, 40):                                       # 扶壁
        for (x0, x1) in ((R[0] - 6, R[0]), (R[2], R[2] + 6)):
            for z in range(0, H - 12):
                for x in range(x0, x1):
                    for yy in range(y, y + 8):
                        M.put('body', x, yy, z, coral_color(x, yy, z, 0, 9883))
            M.box('body', x0, y, H - 12, x1, y + 8, H - 10, CORAL_J)
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.5, 'over': (4, 4, 0, 4), 'gable': 'y'}], salt=9884)
    gable_end(M, R[0], R[2], R[1], R[1] + t, H, 0.5, over=3)
    zg = int(math.floor(H + 0.5 * 56)) + 3
    bc, zt = espadana(M, 80, R[1], R[1] + t, zg - 1, w=44, steps=((0, 44), (24, 24), (32, 8)),
                      arches=[(-10, 12, 4, 10), (10, 12, 4, 10)])
    put_part(M, 'door-double', '前-正門', 'front', R, 80, 0, t)
    portal(M, R, 80, 20, 27, salt=9885)
    put_part(M, 'window-baluster', '前-唱詩台窗', 'front', R, 80, 46, t)
    for cy in (90, 130, 170):
        put_part(M, 'window-baluster', '左-窗%d' % cy, 'left', R, cy + 20, 50, t)
        put_part(M, 'window-baluster', '右-窗%d' % cy, 'right', R, cy + 20, 50, t)
    S = (142, 196, 156, 240)                                           # 聖器室
    masonry(M, S, 0, 40, 4, plinth=4, salt=9886)
    shed_roof(M, S[0], S[1], S[2], S[3], 50, 0.5, low='right')
    put_part(M, 'door-plank', '聖器室-門', 'front', S, 149, 0, 4)
    M.box('body', 50, 236, 3, 110, 242, 12, CAL)                       # 祭壇
    M.box('body', 49, 235, 12, 111, 243, 13, CORAL)
    for x in range(40, 120):                                           # 祭壇屏
        for z in range(13, 74):
            M.put('body', x, R[3] - t - 1, z, PLAQUE_G if (x - 40) % 10 == 0 or z in (13, 34, 54, 73) else FRAME)
    M.box('body', 78, R[3] - t - 2, 40, 82, R[3] - t - 1, 64, PLAQUE_G)
    M.box('body', 72, R[3] - t - 2, 52, 88, R[3] - t - 1, 56, PLAQUE_G)
    for y in range(60, 200, 12):
        for (a, b) in ((36, 72), (88, 124)):
            bench(M, a, b, y, y + 3)
    M.box('body', 10, 8, 1, 22, 20, 3, CORAL)                          # 前庭的石十字
    M.box('body', 13, 11, 3, 19, 17, 5, CORAL)
    M.box('body', 15, 13, 5, 17, 15, 34, CORAL)
    M.box('body', 11, 13, 25, 21, 15, 27, CORAL)
    lantern(M, '燈籠-門左', (62.5, R[1], 26))
    yield_to_parts(M)
    M.anchor('door', 80, R[1] - 2, 1)
    M.anchor('bell', *bc)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'church', 'style': 'es',
            'title': '教堂（iglesia parroquial：一間的長堂、兩側扶壁、紅陶瓦兩坡頂、正面雙拱鐘牆、切石門框；聖器室、祭壇屏、長凳；石鋪前庭與石十字）',
            'use': 'church', 'lot': (16, 28), 'M': M, 'layers': {'body': '牆、扶壁與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 市政廳（cabildo）20 × 16 m ───────────────────────────────
def townhall():
    """市政廳（casas capitulares、cabildo）：兩層刷白砌石、臨街五跨拱廊（樓上壓在拱上）、樓上通長的木陽台（balcón corrido）與木欄杆窗、門上紋章；
    正面牆頂中間一面小鐘牆（議事的鐘）；四坡瓦頂；後面院子、蓄水池井口。
    - 照什麼：《印地亞斯法》cabildo 圍著廣場〔摘〕；哈瓦那的 Casas Capitulares 是 1776～1793 年才蓋的〔摘：OHC〕⇒ 1660 年代的形制〔沒查到〕。
    - 設計：拱廊、通長陽台、小鐘牆（同海關的拱廊、Velázquez 之家的陽台）。"""
    X, Y, Z = 200, 160, 110
    M = Model((X, Y, Z))
    t, H1, H = 5, FL, 2 * FL
    R = (4, 4, 196, 104)
    RG = (4, 30, 196, 104)
    masonry(M, RG, 0, H1, t, salt=9891)
    masonry(M, R, H1, H, t, plinth=0, salt=9892)
    quoins(M, R, H1, H, color=CORAL, long=7, short=4, step=5)
    piers = [(4, 10), (40, 46), (78, 84), (116, 122), (154, 160), (190, 196)]
    arcade(M, 4, 196, 4, 10, piers, 18, H1)
    for (a, b) in (piers[0], piers[-1]):
        M.box('body', a, 10, 0, b, RG[1], H1, CAL)
    tile_floor(M, 10, 10, 190, RG[1])
    M.box('body', 4, 4, H1, 196, 30, H1 + 2, CAL, force=True)
    tile_floor(M, RG[0] + t, RG[1] + t, RG[2] - t, RG[3] - t)
    M.box('body', R[0] + t, R[1] + t, H1, R[2] - t, R[3] - t, H1 + 2, FLOOR)
    put_part(M, 'door-double', '樓下-大門', 'front', RG, 100, 0, t)
    portal(M, RG, 100, 20, 27, salt=9893)
    for i, cx in enumerate((30, 62, 138, 170)):
        put_part(M, 'window-baluster', '樓下-窗%d' % (i + 1), 'front', RG, cx, 8, t)
    for i, cx in enumerate((24, 62, 138, 176)):
        put_part(M, 'window-baluster', '樓上-窗%d' % (i + 1), 'front', R, cx, H1 + 8, t)
    balcony(M, 8, 192, 0, 4, H1 + 4, layer='body')
    for f in ('left', 'right'):
        put_part(M, 'window-baluster', '%s-樓上窗' % {'left': '左', 'right': '右'}[f], f, R, 60, H1 + 8, t)
    hip_tile(M, R, H, 0.5, (3, 3, 3, 3), salt=9894)
    bc, zt = espadana(M, 100, 4, 10, H - 1, w=16, steps=((0, 16), (16, 8)), arch=(8, 3, 7))
    plaque(M, R, 100, H1 + 12)                                          # 中間不開窗：紋章在陽台後面的牆上
    put_part(M, 'door-plank', '後-門', 'back', R, 100, 0, t)
    yard_wall(M, 200, 104, 158, h=26, salt=9895)
    aljibe(M, 60, 130, 7, 8)
    lantern(M, '燈籠-拱廊', (86.5, RG[1], 22))
    yield_to_parts(M)
    M.anchor('door', 100, 2, 0)
    M.anchor('bell', *bc)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'townhall', 'style': 'es',
            'title': '市政廳（cabildo：兩層刷白砌石、臨街五跨拱廊、樓上通長木陽台、門上紋章、牆頂小鐘牆、四坡瓦頂；後院、蓄水池井口）',
            'use': 'townhall', 'lot': (20, 16), 'M': M, 'layers': {'body': '牆、拱廊、陽台與院子', 'roof': '屋頂'}}


# ─────────────────────────────── 總督府（casa de gobierno）28 × 22 m ───────────────────────────────
def governor():
    """總督府：圍著方院的兩層宅（臨街一棟兩層、兩側與後面一層），臨街切石門框＋紋章、兩座木格柵陽台、左前角一座再高一層的觀景樓（mirador：四面拱洞、瓦頂、旗杆）；
    院子裡一道三跨拱廊與廊下、蓄水池井口；後面一排廚房與倉房。
    - 照什麼：聖地牙哥的 Velázquez 之家（樓下生意、樓上住人、木格柵陽台）〔摘〕；總督住的地方 1660 年代的形制〔沒查到〕。
    - 設計：院落的配置、觀景樓、拱廊跨數、尺寸。"""
    X, Y, Z = 280, 220, 160
    M = Model((X, Y, Z))
    t, H1, H = 6, FL, 2 * FL
    R = (4, 4, 276, 74)
    masonry(M, R, 0, H, t, salt=9901)
    tile_floor(M, R[0] + t, R[1] + t, R[2] - t, R[3] - t)
    slab(M, R, H1, t)
    hip_tile(M, R, H, 0.5, (3, 3, 3, 3), salt=9902)
    put_part(M, 'door-double', '前-正門', 'front', R, 140, 0, t)
    portal(M, R, 140, 20, 27, salt=9903)
    plaque(M, R, 140, 36)
    for i, cx in enumerate((84, 108, 172, 196, 240)):
        put_part(M, 'window-baluster', '前-窗%d' % (i + 1), 'front', R, cx, 8, t)
    for i, cx in enumerate((84, 196)):
        put_part(M, 'window-baluster', '二樓-窗（陽台裡）%d' % (i + 1), 'front', R, cx, H1 + 4, t)
        celosia(M, cx - 22, cx + 22, R[1], H1, h=24, d=4)
    for i, cx in enumerate((140, 240)):
        put_part(M, 'window-baluster', '二樓-窗%d' % (i + 1), 'front', R, cx, H1 + 8, t)
    # 觀景樓：左前角再高一層（四面各一個拱洞的開敞層）、四坡瓦頂、旗杆
    T = (4, 4, 60, 60)
    HT = H + 30
    masonry(M, T, H, HT, 5, plinth=0, salt=9904)
    M.box('body', T[0] + 5, T[1] + 5, H, T[2] - 5, T[3] - 5, H + 2, FLOOR)
    for (a0, a1) in ((14, 30), (34, 50)):
        arch_cut(M, 'x', a0, a1, T[1], T[1] + 5, H + 4, H + 18)
        arch_cut(M, 'y', a0, a1, T[0], T[0] + 5, H + 4, H + 18)
        arch_cut(M, 'x', a0, a1, T[3] - 5, T[3], H + 4, H + 18)
        arch_cut(M, 'y', a0, a1, T[2] - 5, T[2], H + 4, H + 18)
    top = tile_roof(M, [{'x0': T[0], 'y0': T[1], 'x1': T[2], 'y1': T[3], 'ze': HT, 'p': 0.6, 'over': (3, 3, 3, 3)}], salt=9905)
    ft, fb = flagpole_on(M, 31, 31, top[(31, 31)] + 1, top[(31, 31)] + 34)
    M.anchor('flag', 31, 31, top[(31, 31)] + 35)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 24, toward=1)]
    # 兩側、後面一層的房
    for W, nm, cy in (((4, 74, 60, 216), '左', 140), ((220, 74, 276, 216), '右', 140)):
        masonry(M, W, 0, 36, 5, salt=9906 + W[0])
        hip_tile(M, W, 36, 0.5, (3, 3, 0, 3), gable='y', salt=9907 + W[0])
        put_part(M, 'door-plank', '%s屋-門' % nm, 'right' if nm == '左' else 'left', W, cy, 0, 5)
    B = (60, 180, 220, 216)
    masonry(M, B, 0, 36, 5, salt=9908)
    hip_tile(M, B, 36, 0.5, (0, 0, 3, 3), gable='x', salt=9909)
    put_part(M, 'door-plank', '廚房-門', 'front', B, 100, 0, 5)
    put_part(M, 'door-plank', '倉房-門', 'front', B, 180, 0, 5)
    hearth(M, 70, 200, 86, 210, hanger=False)
    # 院子：三跨拱廊＋廊下的平頂、蓄水池井口
    arcade(M, 60, 220, 98, 104, [(60, 66), (110, 116), (164, 170), (214, 220)], 18, 32)
    M.box('body', 60, 74, 32, 220, 104, 34, CORAL, force=True)
    tile_floor(M, 60, 74, 220, 98)
    M.box('body', 60, 104, 0, 220, 180, 1, EARTH_W)
    put_part(M, 'door-plank', '院-後門', 'back', R, 140, 0, t)
    aljibe(M, 140, 142, 8, 8)
    lantern(M, '燈籠-門', (122.5, R[1], 24))
    yield_to_parts(M)
    M.anchor('door', 140, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'governor', 'style': 'es', 'flags': flags,
            'title': '總督府（casa de gobierno：圍著方院的兩層宅、切石門框與紋章、兩座木格柵陽台、左前角觀景樓與旗杆；院子三跨拱廊、蓄水池井口；廚房與倉房）',
            'use': 'governor', 'lot': (28, 22), 'M': M, 'layers': {'body': '牆、拱廊與院子', 'roof': '屋頂'}}


# ─────────────────────────────── 市場（mercado）20 × 16 m ───────────────────────────────
def market():
    """市場：切石方墩撐著的開敞大棚（四周每 3.6 m 一墩、木梁、四坡瓦頂）、棚下石鋪地與兩排攤桌、掛肉的木架、大橫桿秤；後面一間刷白的肉鋪（carnicería）。
    - 照什麼：〔沒查到〕1660 年代西屬加勒比海的市場建築 ⇒ 設計（公家的肉鋪 carnicería 是西屬城鎮的通法〔設計判斷〕）。"""
    X, Y, Z = 200, 160, 90
    M = Model((X, Y, Z))
    P = (10, 10, 190, 120)
    cobbles(M, P[0], P[1], P[2], P[3], salt=9911)
    xs = list(range(P[0], P[2] - 5, 34)) + [P[2] - 6]
    ys = list(range(P[1], P[3] - 5, 36)) + [P[3] - 6]
    pts = {(x, P[1]) for x in xs} | {(x, P[3] - 6) for x in xs} | {(P[0], y) for y in ys} | {(P[2] - 6, y) for y in ys}
    for (px, py) in sorted(pts):
        for x in range(px, px + 6):
            for y in range(py, py + 6):
                for z in range(0, 32):
                    M.put('body', x, y, z, coral_color(x, y, z, 0, 9912), force=True)
        M.box('body', px - 1, py - 1, 32, px + 7, py + 7, 34, CORAL_J, force=True)
    for (y0, y1) in ((P[1], P[1] + 6), (P[3] - 6, P[3])):                # 木梁
        M.box('body', P[0], y0, 34, P[2], y1, 38, FRAME, force=True)
    for (x0, x1) in ((P[0], P[0] + 6), (P[2] - 6, P[2])):
        M.box('body', x0, P[1], 34, x1, P[3], 38, FRAME, force=True)
    hip_tile(M, P, 38, 0.4, (4, 4, 4, 4), salt=9913)
    for y in (40, 80):                                                 # 兩排攤桌
        for x0 in (30, 80, 130):
            trestle_table(M, x0, x0 + 36, y, y + 10, 8)
    for x in (34, 160):                                                # 掛肉的木架
        M.box('body', x, 104, 1, x + 2, 106, 26, FRAME)
    M.box('body', 34, 104, 26, 162, 106, 28, FRAME)
    for x in range(40, 160, 8):
        M.box('body', x, 104, 18, x + 1, 105, 26, IRON)
        M.box('body', x - 1, 104, 14, x + 2, 106, 18, 160)
    beam_scale(M, 100, 24, 1)
    S = (10, 124, 190, 156)                                            # 肉鋪
    masonry(M, S, 0, 32, 5, plinth=4, salt=9914)
    tile_floor(M, S[0] + 5, S[1] + 5, S[2] - 5, S[3] - 5)
    hip_tile(M, S, 32, 0.5, (3, 3, 0, 3), gable='x', salt=9915)
    for cx in (60, 140):
        put_part(M, 'door-plank', '肉鋪-門%d' % (1 if cx < 100 else 2), 'front', S, cx, 0, 5)
    put_part(M, 'window-baluster', '肉鋪-窗', 'front', S, 100, 8, 5)
    yield_to_parts(M)
    M.anchor('door', 100, 9, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'market', 'style': 'es',
            'title': '市場（mercado：切石方墩撐著的開敞大棚、木梁、四坡瓦頂；石鋪地與攤桌、掛肉架、大橫桿秤；後面刷白的肉鋪）',
            'use': 'market', 'lot': (20, 16), 'M': M, 'layers': {'body': '棚、攤與肉鋪', 'roof': '屋頂'}}


# ─────────────────────────────── 酒館（pulpería）10 × 14 m ───────────────────────────────
def tavern():
    """酒館（pulpería、taberna）：一層刷白砌石、兩坡瓦頂（屋脊順著街）、切石門框的雙扇門、木欄杆窗、門邊掛的木招牌；
    裡面一道木櫃台、靠牆的酒桶；後院、廚房與堆著的空桶。
    - 照什麼：〔沒查到〕形制 ⇒ 設計（同一層的住宅 A 放大）。"""
    X, Y, Z = 100, 140, 80
    M = Model((X, Y, Z))
    R = (4, 6, 96, 76)
    masonry(M, R, 0, 38, 5, salt=9921)
    tile_floor(M, R[0] + 5, R[1] + 5, R[2] - 5, R[3] - 5)
    hip_tile(M, R, 38, 0.5, (2, 2, 3, 3), gable='x', salt=9922)
    for x0, x1 in ((R[0], R[0] + 5), (R[2] - 5, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 38, 0.5, z0=38, color=CAL, edge=CORAL)
    put_part(M, 'door-double', '前-門', 'front', R, 30, 0, 5)
    portal(M, R, 30, 20, 27, salt=9923)
    put_part(M, 'window-baluster', '前-窗', 'front', R, 72, 8, 5)
    M.box('body', 46, 2, 30, 48, R[1], 32, FRAME, force=True)          # 招牌：一根木架從牆伸出、吊一塊木板
    M.box('body', 50, 2, 30, 52, R[1], 32, FRAME, force=True)
    M.box('body', 46, 2, 32, 52, 3, 33, FRAME, force=True)
    M.box('body', 44, 2, 22, 54, 3, 30, SHUT, force=True)
    M.box('body', 46, 2, 24, 52, 3, 28, PLAQUE_G, force=True)
    M.anchor('sign', 49, 2, 26)
    M.box('body', 40, 46, 1, 90, 52, 11, FRAME)                        # 櫃台
    M.box('body', 39, 45, 11, 91, 53, 12, FLOOR)
    for i, x in enumerate((14, 28, 64, 78)):
        M.models.append({'name': '酒桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, 62, 1], 'pivot': [6, 6, 0], 'meta': {}})
    put_part(M, 'door-plank', '後-門', 'back', R, 50, 0, 5)
    yard_wall(M, 100, 76, 138, salt=9924)
    kitchen(M, (60, 108, 94, 134), salt=9925)
    for i, x in enumerate((14, 26)):
        M.models.append({'name': '空桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, 120, 1], 'pivot': [6, 6, 0], 'meta': {}})
    lantern(M, '燈籠-門', (16.5, R[1], 24))
    yield_to_parts(M)
    M.anchor('door', 30, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'tavern', 'style': 'es',
            'title': '酒館（pulpería：一層刷白砌石、兩坡瓦頂、切石門框、木欄杆窗、木招牌；櫃台與酒桶；後院、廚房）',
            'use': 'tavern', 'lot': (10, 14), 'M': M, 'layers': {'body': '牆、擺設與後院', 'roof': '屋頂'}}


# ─────────────────────────────── 倉庫（almacén）12 × 16 m ───────────────────────────────
def warehouse():
    """倉庫（almacén）：一層高的刷白砌石倉（11.2 × 12.6 m、牆高 5 m、牆厚 0.6 m）、山牆朝街的兩坡瓦頂；正面大貨門、門上吊貨梁、兩扇鐵條氣窗；
    裡面堆的糖桶、貨箱與麻袋；後面小院。
    - 照什麼：聖多明哥 Atarazanas Reales 是倉庫、海關同一棟〔摘〕；單獨的倉庫形制〔沒查到〕⇒ 設計。"""
    X, Y, Z = 120, 160, 110
    M = Model((X, Y, Z))
    R = (4, 4, 116, 130)
    t, H = 6, 50
    masonry(M, R, 0, H, t, salt=9931)
    tile_floor(M, R[0] + t, R[1] + t, R[2] - t, R[3] - t)
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.5, 'over': (3, 3, 0, 0), 'gable': 'y'}], salt=9932)
    gable_end(M, R[0], R[2], R[1], R[1] + t, H, 0.5, over=2)
    gable_end(M, R[0], R[2], R[3] - t, R[3], H, 0.5, over=2)
    put_part(M, 'cartdoor', '前-貨門', 'front', R, 60, 0, t)
    for cx in (24, 96):
        barred(M, 'front', R, cx, 30, 8, 8, t)
    barred(M, 'left', R, 66, 30, 8, 8, t)
    barred(M, 'right', R, 66, 30, 8, 8, t)
    M.box('body', 58, 0, 62, 62, R[1] + t, 65, FRAME, force=True)      # 吊貨梁（從山牆伸出來）
    M.box('body', 59, 0, 56, 61, 1, 62, IRON, force=True)
    M.anchor('hoist', 60, 1, 55)
    for x0 in (14, 30, 82, 98):                                        # 麻袋堆
        M.box('body', x0, 70, 1, x0 + 12, 90, 10, 141)
    for i, (x, y) in enumerate(((20, 104), (34, 104), (80, 104), (94, 104), (20, 50))):
        M.models.append({'name': '糖桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, y, 1], 'pivot': [6, 6, 0], 'meta': {}})
    for i, (x, y) in enumerate(((84, 40), (96, 40))):
        M.models.append({'name': '貨箱-%d' % (i + 1), 'source': 'summit-rocher-01m-crate', 'at': [x, y, 1], 'pivot': [6, 6, 0], 'meta': {}})
    put_part(M, 'door-plank', '後-門', 'back', R, 60, 0, t)
    yard_wall(M, 120, 130, 158, h=24, salt=9933)
    lantern(M, '燈籠-門', (40.5, R[1], 26))
    yield_to_parts(M)
    M.anchor('door', 60, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'warehouse', 'style': 'es',
            'title': '倉庫（almacén：刷白砌石、山牆朝街的兩坡瓦頂、大貨門與吊貨梁、鐵條氣窗；糖桶、貨箱與麻袋；後面小院）',
            'use': 'warehouse', 'lot': (12, 16), 'M': M, 'layers': {'body': '牆、貨與後院', 'roof': '屋頂'}}


ALL = [church, townhall, governor, market, tavern, warehouse] + HOUSES + [house_m_a, house_m_b, house_h_a, house_h_b]
