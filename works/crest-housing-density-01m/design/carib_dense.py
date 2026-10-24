# 加勒比海（carib）的中、高密度住宅（TASK-0893）—— 照 summit-carib-01m 住宅 C「兩層的商家」的做法往上加：一樓毛石、樓上木構架釘橫板、
#   前面通長的外廊（柱從地面立到屋面）、木瓦四坡頂接緩坡廊頂；窗是木板百葉（17 世紀的加勒比海聚落窗上沒有玻璃，summit-carib-01m references/README.md）。
#   中密度 house-m-a：地塊 12 × 12 m（3 × 3 格）；三層 —— 一樓毛石店面（貨門＋兩扇氣窗）、二三樓木板牆，前面上下兩層通長外廊、左側外樓梯上二樓；
#     後院毛石院牆＋木板廚房披屋。住 12 人（低密度的兩倍）〔設計〕。
#   高密度 house-h-a：地塊 16 × 16 m（4 × 4 格）；臨街一棟四層（一樓毛石：車馬門穿到內院、雙扇門、店面）、前面三層通長外廊；
#     右側一道三層的側翼，朝內院那一面上下兩層外廊（加勒比海的院落屋：廊朝院子）；內院毛石院牆、後門、蓄水井、木板廚房披屋。住 24 人（四倍）〔設計〕。
#   史料的位置：皇家港 1692 年地震前有三、四層的磚屋（之後英國那一套再做磚的）；這一套照 carib 的木構，層數是〔設計〕。
# 層高照住宅 C：一樓 3.0 m、樓板 0.2 m、樓上每層 2.6 m。
from common import *
from carib import *                            # noqa: F401,F403  BOARD、LIME、SHUT、FRAME、FLOOR、RUBBLE…、board_walls、rubble_walls、shingle_roof、rail、gallery_posts

FLOORS = [(0, 30), (32, 58), (60, 86), (88, 114)]   # 每一層牆的 [底, 頂)；樓板 30..32、58..60、86..88


def storeys(M, R, n, salt=0, bay=26):
    """n 層：一樓毛石（厚 4）、樓上木板牆（厚 2、四角＋每 bay 格一根柱）、樓板。回傳牆頂 z。"""
    X0, Y0, X1, Y1 = R
    rubble_walls(M, R, 0, FLOORS[0][1], 4, salt=salt)
    for i in range(1, n):
        z0, z1 = FLOORS[i]
        M.box('body', X0, Y0, FLOORS[i - 1][1], X1, Y1, z0, FLOOR)
        board_walls(M, R, z0, z1, 2, bay=bay)
    return FLOORS[n - 1][1]


def front_gallery(M, x0, x1, gy0, gy1, levels, posts, top, stair=None):
    """前面的通長外廊：每一層一片木地板（y gy0..gy1、頂 ＝ 那一層的地板）＋欄杆；柱從地面立到屋面底下。"""
    for z in levels:
        M.box('gallery', x0, gy0, z - 2, x1, gy1, z, FLOOR)
    gallery_posts(M, posts, gy0, 0, top)
    for z in levels:
        rail(M, x0 + 2, x1 - 2, gy0, z)
        rail(M, gy0 + 2, gy1, x0, z, axis='y', gap=stair if z == levels[0] else None)   # stair ＝ 左邊外樓梯上來那一段（y 範圍）不做欄杆
        rail(M, gy0 + 2, gy1, x1 - 1, z, axis='y')


def side_stair(M, sx0, y_back, z_top, step_h=2, run=3):
    """外樓梯（同住宅 C）：從後往前爬到 z_top（前廊的地板），每級高 2、深 3、厚 4；斜梁落地那一頭撐住。"""
    n = z_top // step_h
    for k in range(n):
        zt = step_h * (k + 1)
        ya = y_back - run * (k + 1)
        M.box('gallery', sx0, ya, max(0, zt - 4), sx0 + 5, ya + run, zt, FLOOR)
    M.box('gallery', sx0, y_back - run * n - 2, 0, sx0 + 1, y_back + 1, 2, FRAME)
    for k in range(0, n, 3):
        ya = y_back - run * (k + 1)
        M.box('gallery', sx0, ya, 0, sx0 + 1, ya + 1, step_h * (k + 1) - 2, FRAME)


def yard_rubble(M, segs, h=18, salt=0):
    for (a, b, c, d) in segs:
        rubble(M, (a, b, c, d), 0, h, 4, 'body', base=RUBBLE, mortar=MORTAR, course=5, block=7, salt=salt, dark=RUBBLE_D)


def plank_gate(M, x0, x1, y, h=16):
    """院牆上的木板門：先挖、再一片直板（每 3 格一道深色縫）。"""
    M.clear(x0, y - 1, 0, x1, y + 2, 18, 'body')
    for z in range(0, h):
        for x in range(x0, x1):
            M.put('body', x, y, z, SHUT if (x - x0) % 3 else FRAME)


def cput(M, pid, name, face, rect, center, z, t):
    """carib 的擺部件：借來的法式部件（貨門、氣窗）百葉是綠 49 ⇒ 換成這一套的 SHUT（同 summit-carib-01m houses.put_part）。"""
    P = CB_PARTS[pid]
    return put_part(M, CB_PARTS, pid, name, face, rect, center, z, t, shutter=SHUT if P.get('src') else SH_GREEN)


def lean_roof_posts(M, x0, y0, x1, y1, z_hi, p, low, roof_fn, salt=0):
    """單坡的棚（抄 summit-carib-01m houses.lean_roof_posts，不帶柱）：屋面 roof_fn 鋪色；回傳 {(x,y): 頂 z}。"""
    F = {}
    for x in range(x0, x1):
        for y in range(y0, y1):
            if not M.inb(x, y, 0):
                continue
            px, py = x + 0.5, y + 0.5
            d = {'front': y1 - py, 'back': py - y0, 'left': x1 - px, 'right': px - x0}[low]
            F[(x, y)] = (z_hi - p * d, low if low in ('front', 'back') else 'left', False, 0)
    return build_roof(M, F, 2, 'roof', color_fn=lambda x, y, f, r, e: roof_fn(x, y, f, r, e, salt))


def lean_kitchen(M, kr, door_face, door_c, z_hi, low, salt=0):
    """木板廚房披屋（同住宅 C）：木板牆、木板門、單坡木瓦頂；牆頂照屋面切。"""
    board_walls(M, kr, 0, z_hi + 2, 2)
    cput(M, 'door-plank', '廚房-門', door_face, kr, door_c, 0, 2)
    ktop = lean_roof_posts(M, kr[0] - 2, kr[1] - 2, kr[2] + 2, kr[3] + 2, z_hi, 0.25, low, shingle_color, salt=salt)
    for k in [k for k, v in M.cells.items() if v[0] == 'body' and kr[0] <= k[0] < kr[2] and kr[1] <= k[1] < kr[3] and k[2] >= ktop[(k[0], k[1])] - 1]:
        del M.cells[k]


def house_m_a():
    M = Model((120, 120, 120))
    P = CB_PARTS
    X0, Y0, X1, Y1 = 8, 28, 112, 82
    R = (X0, Y0, X1, Y1)
    GY0 = 13
    zt = storeys(M, R, 3, salt=51)
    # 一樓：貨門（店面）＋兩扇氣窗；樓上：正中一扇木板門出到外廊、兩旁木板百葉窗
    cput(M, 'cartdoor', '前-貨門', 'front', R, 60, 0, 4)
    for i, cx in enumerate((25, 95)):
        cput(M, 'vent', '前-氣窗%d' % (i + 1), 'front', R, cx, 12, 4)
    for f in (1, 2):
        z0 = FLOORS[f][0]
        cput(M, 'door-plank', '%d樓-門' % (f + 1), 'front', R, 60, z0, 2)
        for i, cx in enumerate((25, 95)):
            cput(M, 'window-board', '%d樓-前窗%d' % (f + 1, i + 1), 'front', R, cx, z0 + 9, 2)
        for i, cx in enumerate((30, 90)):
            cput(M, 'window-board', '%d樓-後窗%d' % (f + 1, i + 1), 'back', R, cx, z0 + 9, 2)
        cput(M, 'window-board', '%d樓-右窗' % (f + 1), 'right', R, 55, z0 + 9, 2)
        cput(M, 'window-board', '%d樓-左窗' % (f + 1), 'left', R, 62, z0 + 9, 2)
    cput(M, 'door-plank', '後-門', 'back', R, 60, 0, 4)
    cput(M, 'vent', '右-氣窗', 'right', R, 55, 12, 4)
    M.anchor('door', 60, Y0 - 1, 0)
    # 屋頂：木瓦四坡（0.85）、前面緩坡（0.4）蓋過外廊；外廊兩層、五根柱；左側外樓梯上二樓的廊
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': zt, 'p': 0.85, 'over': (6, 6, 17, 4), 'kick': {'front': 0.4}}], salt=51)
    front_gallery(M, 2, 118, GY0, Y0, (FLOORS[1][0], FLOORS[2][0]), (2, 40, 78, 116), top, stair=(20, Y0))         # 柱在開口之間（⛔ 立在貨門正前方）
    side_stair(M, 2, 73, FLOORS[1][0])
    # 後院：毛石院牆（後面一扇木板門）、木板廚房披屋（右後角）
    ye = 119
    yard_rubble(M, ((X0, Y1, X0 + 3, ye), (X1 - 3, Y1, X1, ye), (X0, ye - 3, X1, ye)), salt=52)
    plank_gate(M, 30, 42, ye - 2)
    lean_kitchen(M, (70, 92, X1 - 3, 113), 'left', 102, 38, 'left', salt=53)
    M.models += [model(LANTERN, '燈籠-貨門', (43.5, Y0, 22.5)),
                 model(CRATE, '貨箱-門口1', (78, 20, 0)), model(CRATE, '貨箱-門口2', (90, 20, 0)), model(BARREL, '酒桶-門口', (98, 20, 0))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-a', 'variant': 'm-a', 'level': 2, 'live': 12,
            'title': '中密度住宅 M-A（三層的商家：一樓毛石店面、二三樓木板牆、前面上下兩層通長外廊、左側外樓梯、木瓦四坡頂；後院石牆＋木板廚房）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}}


def house_h_a():
    M = Model((160, 160, 150))
    P = CB_PARTS
    X0, Y0, X1, Y1 = 6, 28, 154, 86                                   # 臨街的一棟（四層）
    R = (X0, Y0, X1, Y1)
    WR = (104, Y1 - 4, 154, 154)                                       # 右側的側翼（三層；前端疊在臨街那一棟的後牆上）
    GY0 = 13
    zt = storeys(M, R, 4, salt=61)
    zw = storeys(M, WR, 3, salt=62)
    # 臨街那一面：一樓車馬門（穿到內院）、雙扇門、店面貨門、兩扇氣窗；樓上每層正中一扇門出到外廊、四扇木板百葉窗
    cput(M, 'cartdoor', '前-車馬門', 'front', R, 35, 0, 4)
    cput(M, 'vent', '前-氣窗1', 'front', R, 60, 12, 4)
    cput(M, 'door-double', '前-門', 'front', R, 80, 0, 4)
    cput(M, 'cartdoor', '前-店面', 'front', R, 115, 0, 4)
    cput(M, 'vent', '前-氣窗2', 'front', R, 141, 12, 4)
    M.anchor('door', 80, Y0 - 1, 0)
    for f in (1, 2, 3):
        z0 = FLOORS[f][0]
        cput(M, 'door-plank', '%d樓-門' % (f + 1), 'front', R, 80, z0, 2)
        for i, cx in enumerate((22, 50, 110, 138)):
            cput(M, 'window-board', '%d樓-前窗%d' % (f + 1, i + 1), 'front', R, cx, z0 + 9, 2)
    # 臨街那一棟的背面（朝內院那一段 x < 104）：車馬門、木板門、樓上每層三扇窗
    cput(M, 'cartdoor', '後-車馬門', 'back', R, 35, 0, 4)
    cput(M, 'door-plank', '後-門', 'back', R, 80, 0, 4)
    for f in (1, 2, 3):
        for i, cx in enumerate((22, 55, 85)):
            cput(M, 'window-board', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 9, 2)
    # 側翼朝內院那一面（left）：一樓木板門＋氣窗；樓上每層一扇門出到廊、兩扇窗
    cput(M, 'door-plank', '側翼-門', 'left', WR, 100, 0, 4)
    cput(M, 'vent', '側翼-氣窗', 'left', WR, 130, 12, 4)
    for f in (1, 2):
        z0 = FLOORS[f][0]
        cput(M, 'door-plank', '側翼-%d樓門' % (f + 1), 'left', WR, 118, z0, 2)
        for i, cy in enumerate((98, 140)):
            cput(M, 'window-board', '側翼-%d樓窗%d' % (f + 1, i + 1), 'left', WR, cy, z0 + 9, 2)
    # 屋頂：臨街那一棟木瓦四坡、前面緩坡蓋過外廊；側翼四坡、朝內院那一邊緩坡蓋過院子裡的廊
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': zt, 'p': 0.85, 'over': (4, 4, 17, 4), 'kick': {'front': 0.4}},
                           {'x0': WR[0], 'y0': Y1, 'x1': WR[2], 'y1': WR[3], 'ze': zw, 'p': 0.85, 'over': (14, 4, 0, 4), 'kick': {'left': 0.4}}], salt=61)
    front_gallery(M, 2, 158, GY0, Y0, (FLOORS[1][0], FLOORS[2][0], FLOORS[3][0]), (2, 60, 96, 130, 156), top)         # 柱在開口之間（⛔ 立在大門正前方）
    # 院子裡的廊（側翼左邊 x 92..104、y 92..150）：兩層地板、四根柱、欄杆
    gx0 = WR[0] - 12
    for z in (FLOORS[1][0], FLOORS[2][0]):
        M.box('gallery', gx0, Y1 + 6, z - 2, WR[0], 150, z, FLOOR)
        rail(M, Y1 + 8, 148, gx0, z, axis='y')
        rail(M, gx0 + 2, WR[0] - 1, Y1 + 6, z)                            # 欄杆停在側翼牆外那一格之前（那一格是窗的百葉）
        rail(M, gx0 + 2, WR[0] - 1, 149, z)
    for py in (Y1 + 6, 106, 127, 148):
        zt2 = min(top[(x, y)] - 1 for x in range(gx0, gx0 + 2) for y in range(py, py + 2))
        M.box('gallery', gx0, py, 0, gx0 + 2, py + 2, zt2, FRAME)
    # 內院：左、後兩道毛石院牆（後面一扇木板門）、蓄水井、木板廚房披屋（左後角）
    yard_rubble(M, ((X0, Y1, X0 + 3, 157), (X0, 154, WR[0], 157)), salt=63)
    plank_gate(M, 46, 58, 155)
    well(M, 60, 112, ring=RUBBLE, cap=MORTAR, post=FRAME)
    lean_kitchen(M, (11, 128, 40, 151), 'right', 140, 36, 'left', salt=64)
    M.models += [model(LANTERN, '燈籠-門', (68.5, Y0, 24)), model(LANTERN, '燈籠-車馬門', (18, Y0, 31)),
                 model(CRATE, '貨箱-店面1', (126, 20, 0)), model(BARREL, '酒桶-店面', (134, 20, 0)),
                 model(BARREL, '酒桶-內院1', (80, 140, 0)), model(BARREL, '酒桶-內院2', (80, 147, 0))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-a', 'variant': 'h-a', 'level': 3, 'live': 24,
            'title': '高密度住宅 H-A（院落屋：臨街一棟四層、一樓毛石車馬門與店面、前面三層通長外廊；右側三層側翼、朝內院上下兩層廊；內院蓄水井＋木板廚房）',
            'use': 'house', 'lot': (16, 16), 'M': M, 'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}}


def house_m_b():
    """中密度 M-B（原地升級用，TASK-0895）：低密度同一塊 8 × 12 地塊上蓋三層 —— 住宅 C「兩層的商家」加一層：一樓毛石貨門、二三樓木板牆、前面上下兩層外廊、左側外樓梯；後院石牆＋木板廚房。"""
    M = Model((80, 120, 120))
    X0, Y0, X1, Y1 = 8, 28, 74, 74
    R = (X0, Y0, X1, Y1)
    GY0 = 13
    zt = storeys(M, R, 3, salt=91)
    cput(M, 'cartdoor', '前-貨門', 'front', R, 41, 0, 4)
    for i, cx in enumerate((18, 64)):
        cput(M, 'vent', '前-氣窗%d' % (i + 1), 'front', R, cx, 12, 4)
    for f in (1, 2):
        z0 = FLOORS[f][0]
        cput(M, 'door-plank', '%d樓-門' % (f + 1), 'front', R, 41, z0, 2)
        for i, cx in enumerate((20, 62)):
            cput(M, 'window-board', '%d樓-前窗%d' % (f + 1, i + 1), 'front', R, cx, z0 + 9, 2)
        for i, cx in enumerate((24, 58)):
            cput(M, 'window-board', '%d樓-後窗%d' % (f + 1, i + 1), 'back', R, cx, z0 + 9, 2)
        cput(M, 'window-board', '%d樓-右窗' % (f + 1), 'right', R, 52, z0 + 9, 2)
    cput(M, 'door-plank', '後-門', 'back', R, 40, 0, 4)
    cput(M, 'vent', '右-氣窗', 'right', R, 52, 12, 4)
    M.anchor('door', 41, Y0 - 1, 0)
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': zt, 'p': 0.85, 'over': (6, 6, 17, 4), 'kick': {'front': 0.4}}], salt=91)
    front_gallery(M, 2, 78, GY0, Y0, (FLOORS[1][0], FLOORS[2][0]), (2, 27, 52, 76), top, stair=(20, Y0))
    side_stair(M, 2, 73, FLOORS[1][0])
    ye = 119
    yard_rubble(M, ((X0, Y1, X0 + 3, ye), (X1 - 3, Y1, X1, ye), (X0, ye - 3, X1, ye)), salt=92)
    plank_gate(M, 30, 42, ye - 2)
    lean_kitchen(M, (48, 88, X1 - 3, 113), 'left', 100, 38, 'left', salt=93)
    M.models += [model(LANTERN, '燈籠-貨門', (24.5, Y0, 22.5)), model(CRATE, '貨箱-門口', (58, 20, 0)), model(BARREL, '酒桶-門口', (66, 20, 0))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-b', 'variant': 'm-b', 'level': 2, 'live': 8,
            'title': '中密度住宅 M-B（原地升級：低密度同一塊 8 × 12 蓋三層 —— 住宅 C 的商家加一層：一樓毛石貨門、二三樓木板牆、上下兩層外廊、外樓梯；後院石牆＋木板廚房）',
            'use': 'house', 'lot': (8, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}}


def house_h_b():
    """高密度 H-B（原地升級用，TASK-0895）：中密度同一塊 12 × 12 地塊上蓋四層 —— M-A 加一層：前面三層通長外廊、外樓梯上二樓；後院石牆＋木板廚房。"""
    M = Model((120, 120, 150))
    X0, Y0, X1, Y1 = 8, 28, 112, 82
    R = (X0, Y0, X1, Y1)
    GY0 = 13
    zt = storeys(M, R, 4, salt=101)
    cput(M, 'cartdoor', '前-貨門', 'front', R, 60, 0, 4)
    for i, cx in enumerate((25, 95)):
        cput(M, 'vent', '前-氣窗%d' % (i + 1), 'front', R, cx, 12, 4)
    for f in (1, 2, 3):
        z0 = FLOORS[f][0]
        cput(M, 'door-plank', '%d樓-門' % (f + 1), 'front', R, 60, z0, 2)
        for i, cx in enumerate((25, 95)):
            cput(M, 'window-board', '%d樓-前窗%d' % (f + 1, i + 1), 'front', R, cx, z0 + 9, 2)
        for i, cx in enumerate((30, 90)):
            cput(M, 'window-board', '%d樓-後窗%d' % (f + 1, i + 1), 'back', R, cx, z0 + 9, 2)
        cput(M, 'window-board', '%d樓-右窗' % (f + 1), 'right', R, 55, z0 + 9, 2)
        cput(M, 'window-board', '%d樓-左窗' % (f + 1), 'left', R, 62, z0 + 9, 2)
    cput(M, 'door-plank', '後-門', 'back', R, 60, 0, 4)
    M.anchor('door', 60, Y0 - 1, 0)
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': zt, 'p': 0.85, 'over': (6, 6, 17, 4), 'kick': {'front': 0.4}}], salt=101)
    front_gallery(M, 2, 118, GY0, Y0, (FLOORS[1][0], FLOORS[2][0], FLOORS[3][0]), (2, 40, 78, 116), top, stair=(20, Y0))
    side_stair(M, 2, 73, FLOORS[1][0])
    ye = 119
    yard_rubble(M, ((X0, Y1, X0 + 3, ye), (X1 - 3, Y1, X1, ye), (X0, ye - 3, X1, ye)), salt=102)
    plank_gate(M, 30, 42, ye - 2)
    lean_kitchen(M, (70, 92, X1 - 3, 113), 'left', 102, 38, 'left', salt=103)
    M.models += [model(LANTERN, '燈籠-貨門', (43.5, Y0, 22.5)), model(CRATE, '貨箱-門口', (78, 20, 0)), model(BARREL, '酒桶-門口', (90, 20, 0))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-b', 'variant': 'h-b', 'level': 3, 'live': 13,
            'title': '高密度住宅 H-B（原地升級：中密度同一塊 12 × 12 蓋四層 —— 一樓毛石店面、二三四樓木板牆、前面三層通長外廊、外樓梯；後院石牆＋木板廚房）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}}


ALL = [house_m_a, house_h_a, house_m_b, house_h_b]
# 配色變化（設計決定，照 summit-carib-01m 那一套的史料）：M-A2 板牆刷石灰白（Saba「刷得很白」）、H-A2 一樓石牆刷白（St Thomas「照荷蘭方式刷白」）
VARIANTS = [('house-m-a2', 'house-m-a', {BOARD: LIME}, '中密度住宅 M-A2（M-A 的配色變化：板牆刷石灰白；替換色，不另存格子）'),
            ('house-h-a2', 'house-h-a', {RUBBLE: LIME, RUBBLE_D: LIME, MORTAR: LIME}, '高密度住宅 H-A2（H-A 的配色變化：一樓石牆刷白；替換色，不另存格子）'),
            ('house-m-b2', 'house-m-b', {RUBBLE: LIME, RUBBLE_D: LIME, MORTAR: LIME}, '中密度住宅 M-B2（M-B 的配色變化：一樓石牆刷白；替換色，不另存格子）'),
            ('house-h-b2', 'house-h-b', {BOARD: LIME}, '高密度住宅 H-B2（H-B 的配色變化：板牆刷石灰白；替換色，不另存格子）')]
