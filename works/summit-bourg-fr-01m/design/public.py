# 公共建築（TASK-0741）：酒館、倉庫、市場、市政廳、總督府、教堂 —— 地塊照生成器 world/town.js 的 PUB 表。
# 座標同 houses.py（x 臨路寬、y 進深、y 0 臨路；0.1 m／格）。
from kit import *
from houses import put_part, free_part, simple_door, yard

ORANGE, YELLOW = 236, 252


def walls_union(M, rects, z0, z1, t, color):
    """幾塊長方形拼成的屋身：先全部填滿、再各自挖掉內部 ⇒ 交界的那段牆自然被挖通（中央凸出的門廳）。"""
    for (a, b, c, d) in rects:
        M.box('body', a, b, z0, c, d, z1, color)
    for (a, b, c, d) in rects:
        M.clear(a + t, b + t, z0, c - t, d - t, z1, 'body')


def gable_wall(M, x0, x1, y0, y1, ze, p, color, edge=TRIM, layer='body'):
    """山牆（三角）：x ∈ [x0, x1)、牆厚 y ∈ [y0, y1)；頂 ＝ ze ＋ p × 離最近一邊的距離；外緣一圈 edge 色。"""
    for x in range(x0, x1):
        d = min(x + 0.5 - x0, x1 - x - 0.5)
        zt = int(math.floor(ze + p * d))
        for z in range(ze, zt + 1):
            for y in range(y0, y1):
                c = edge if (z >= zt - 1 or x in (x0, x1 - 1)) else color
                M.put(layer, x, y, z, c, force=True)


def dormer_on(M, top, cx, face, rect, inset, name):
    X0, Y0, X1, Y1 = rect
    H = 24
    if face == 'front':
        yf = Y0 + inset
        at = (cx - 7, yf - 1, top[(cx, yf)] - 1)
        return free_part(M, 'dormer', name, at, 0)
    yf = Y1 - inset - 1
    at = (cx - 7, yf - (H - 2), top[(cx, yf)] - 1)
    return free_part(M, 'dormer', name, at, 180)


def iron_rail(M, x0, x1, y0, y1, z0, h, layer='gallery', front_only=False):
    """鍛鐵欄杆：沿長方形的前緣（＋兩側）每 2 格一根、頂一條。"""
    for x in range(x0, x1):
        M.put(layer, x, y0, z0 + h, IRON)
        if x % 2 == 0:
            for z in range(z0, z0 + h):
                M.put(layer, x, y0, z, IRON)
    if not front_only:
        for xs in (x0, x1 - 1):
            for y in range(y0, y1):
                M.put(layer, xs, y, z0 + h, IRON)
                if y % 2 == 0:
                    for z in range(z0, z0 + h):
                        M.put(layer, xs, y, z, IRON)


# ─────────────────────────────── 酒館 10 × 14 m ───────────────────────────────
def tavern():
    M = Model((100, 140, 106))
    X0, Y0, X1, Y1 = 4, 28, 96, 104
    R, t, pl = (X0, Y0, X1, Y1), 3, 4
    M.box('body', X0, Y0, 0, X1, Y1, pl, STONE)
    stucco_walls(M, R, pl, 38, t, SALMON)
    floor_slab(M, R, 38, 40)
    stucco_walls(M, R, 40, 70, t, SALMON)
    quoins(M, R, pl, 70)
    band(M, R, 38, 40, TRIM, out=0)
    put_part(M, 'door', '前-門', 'front', R, 50, pl, t)
    for i, cx in enumerate((22, 78)):
        put_part(M, 'frenchdoor', '前-大窗%d' % (i + 1), 'front', R, cx, pl, t)
    for i, cx in enumerate((22, 50, 78)):
        put_part(M, 'frenchdoor', '前-落地窗%d' % (i + 1), 'front', R, cx, 40, t)
    put_part(M, 'door', '後-門', 'back', R, 30, pl, t)
    put_part(M, 'window', '後-窗', 'back', R, 70, pl + 9, t)
    for i, cx in enumerate((25, 50, 75)):
        put_part(M, 'window', '後-二樓窗%d' % (i + 1), 'back', R, cx, 40 + 8, t)
    for face in ('left', 'right'):
        put_part(M, 'window', '%s-窗' % ('左' if face == 'left' else '右'), face, R, 66, pl + 9, t)
        put_part(M, 'window', '%s-二樓窗' % ('左' if face == 'left' else '右'), face, R, 66, 40 + 8, t)
    M.anchor('door', 50, Y0 - 1, pl)
    # 兩層外廊（木柱）
    M.box('gallery', 2, 10, 0, 98, Y0, pl, STONE_L)
    M.box('gallery', 2, 10, 38, 98, Y0, 40, WOOD)
    M.box('gallery', 2, 10, 38, 98, 11, 40, WOOD_D)
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 70, 'p': 0.8, 'over': (4, 4, 18, 6), 'kick': {'front': 0.35}}])
    top = build_roof(M, F, salt=7)
    for px in (2, 33, 64, 95):
        M.box('gallery', px, 10, pl, px + 3, 13, 38, WOOD_D)
        zt = min(top[(x, y)] - 1 for x in range(px, px + 3) for y in range(10, 13))
        M.box('gallery', px, 10, 40, px + 3, 13, zt, WOOD_D)
    zb = min(top[(x, 11)] - 1 for x in range(2, 98))
    M.box('gallery', 2, 10, zb - 2, 98, 12, zb, WOOD_D)
    for x in range(2, 98):
        M.put('gallery', x, 10, 50, WOOD_D)
        M.put('gallery', x, 10, 41, WOOD_D)
        if x % 3 == 0:
            for z in range(42, 50):
                M.put('gallery', x, 10, z, WOOD_D)
    for xs in (2, 97):
        for y in range(10, Y0):
            M.put('gallery', xs, y, 50, WOOD_D)
            if y % 3 == 0:
                for z in range(40, 50):
                    M.put('gallery', xs, y, z, WOOD_D)
    # 吊招牌：從左前柱伸出去的鐵臂、垂下的木牌（一串葡萄）
    for y in range(1, 10):
        M.put('gallery', 3, y, 58, IRON)
    for z in range(54, 58):
        M.put('gallery', 3, 2, z, IRON)
        M.put('gallery', 3, 9, z, IRON)
    for y in range(1, 11):
        for z in range(40, 54):
            M.put('gallery', 3, y, z, WOOD_D if (y in (1, 10) or z in (40, 53)) else WOOD)
    G = ['..ll....',
         '.lpp....',
         '.pppp...',
         'pppppp..',
         '.ppppp..',
         '..pppp..',
         '...pp...',
         '....p...']
    for r, row in enumerate(G):
        for cidx, ch in enumerate(row):
            if ch != '.':
                M.put('gallery', 3, 2 + cidx, 51 - r, PURPLE if ch == 'p' else LEAF, force=True)
    M.anchor('sign', 3, 5, 47)
    free_part(M, 'chimney', '煙囪', (84, 90, 50))
    # 後院：院牆、側門、靠後牆的棚子
    yard(M, X0, Y1, X1, 140, 3, 22, SALMON, gate=(80, 16, 19))
    F2 = {}                                                           # 靠後牆的棚子：單坡（貼著院牆那邊高）、前面三根柱
    for x in range(X0 + 3, 61):
        for y in range(118, 137):
            F2[(x, y)] = (26 - 0.25 * (136.5 - (y + 0.5)), 'front', False, 0)
    t2 = build_roof(M, F2, 2, 'roof', salt=8)
    for px in (X0 + 3, 31, 57):
        zt = min(t2[(x, y)] - 1 for x in range(px, px + 3) for y in range(122, 125))
        M.box('body', px, 122, 0, px + 3, 125, zt, WOOD_D)
    M.models += [{'name': '燈籠-柱%d' % (i + 1), 'source': 'summit-rocher-01m-lantern', 'at': [px + 1.5, 10, 30.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}
                 for i, px in enumerate((33, 64))]
    M.models += [{'name': '酒桶-廊%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [p[0], p[1], pl], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, p in enumerate(((9, 16), (9, 23), (91, 16)))]
    M.models += [{'name': '酒桶-棚%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, 131, 0], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, x in enumerate((14, 21, 28, 35))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'tavern', 'title': '酒館（二層樓、上下兩層木外廊、吊招牌、後院棚子；鮭粉牆）', 'use': 'tavern', 'lot': (10, 14), 'M': M,
            'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}}


# ─────────────────────────────── 倉庫 12 × 16 m ───────────────────────────────
def warehouse():
    M = Model((120, 160, 96))
    X0, Y0, X1, Y1 = 4, 10, 116, 154
    R, t = (X0, Y0, X1, Y1), 5
    rubble(M, R, 0, 56, t, base=STONE_W, dark=STONE, salt=9)
    M.box('body', X0 + t, Y0 + t, 0, X1 - t, Y1 - t, 1, EARTH)        # 地面（夯土）
    M.box('body', X0 + t, Y0 + t, 34, X1 - t, Y0 + 40, 36, WOOD)     # 閣樓（前段）
    quoins(M, R, 0, 56, long=8, short=4, step=6)
    for i, cx in enumerate((32, 88)):
        put_part(M, 'cartdoor', '前-貨門%d' % (i + 1), 'front', R, cx, 0, t)
        M.box('body', cx - 15, Y0, 29, cx + 15, Y0 + t, 33, STONE_L)   # 石過梁
    put_part(M, 'cartdoor', '後-貨門', 'back', R, 60, 0, t)
    M.box('body', 45, Y1 - t, 29, 75, Y1, 33, STONE_L)
    simple_door(M, 'front', R, 60, 14, 16, t, z0=36)                  # 閣樓門
    M.box('body', 52, Y0, 52, 68, Y0 + t, 55, STONE_L)
    for y in range(0, Y0 + 6):                                        # 吊貨梁
        M.box('body', 59, y, 53, 61, y + 1, 55, WOOD_D, force=True)
    M.anchor('hoist', 60, 1, 52)
    for face in ('left', 'right'):
        for i, cy in enumerate((34, 70, 106, 136)):
            put_part(M, 'vent', '%s-氣窗%d' % ('左' if face == 'left' else '右', i + 1), face, R, cy, 22, t)
    for i, cx in enumerate((20, 100)):
        put_part(M, 'vent', '前-氣窗%d' % (i + 1), 'front', R, cx, 40, t)
    M.anchor('door', 32, Y0 - 1, 0)
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 56, 'p': 0.6, 'over': (4, 4, 6, 6)}])
    build_roof(M, F, thick=3, salt=9)
    M.models += [{'name': '貨箱%d' % (i + 1), 'source': 'summit-rocher-01m-crate', 'at': list(p), 'pivot': [6, 6, 0], 'meta': {}}
                 for i, p in enumerate(((10, 4, 0), (10, 4, 6), (17, 4, 0), (104, 4, 0)))]
    M.models += [{'name': '酒桶%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': list(p), 'pivot': [6, 6, 0], 'meta': {}}
                 for i, p in enumerate(((52, 4, 0), (110, 4, 0), (110, 4, 9)))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'warehouse', 'title': '倉庫（毛石牆、兩扇貨門、閣樓門與吊貨梁、低緩的四坡頂）', 'use': 'warehouse', 'lot': (12, 16), 'M': M,
            'layers': {'body': '牆身', 'roof': '屋頂'}}


# ─────────────────────────────── 市場 20 × 16 m ───────────────────────────────
def market():
    M = Model((200, 160, 96))
    X0, Y0, X1, Y1 = 10, 10, 190, 150
    pl = 3
    for x in range(4, 196):                                           # 石板地台（棋盤）
        for y in range(4, 156):
            c = STONE_L if ((x // 6) + (y // 6)) % 2 == 0 else STONE
            for z in range(0, pl):
                M.put('body', x, y, z, c if z == pl - 1 else STONE)
    xs = (10, 40, 70, 97, 124, 154, 184)
    ys = (10, 38, 66, 94, 122, 144)
    pil = [(x, Y0) for x in xs] + [(x, 144) for x in xs] + [(X0, y) for y in ys[1:-1]] + [(184, y) for y in ys[1:-1]]
    for (px, py) in pil:                                              # 石柱：柱礎、柱身、柱頭
        M.box('body', px - 1, py - 1, pl, px + 7, py + 7, pl + 3, STONE)
        M.box('body', px, py, pl + 3, px + 6, py + 6, 33, STONE_L)
        M.box('body', px - 1, py - 1, 33, px + 7, py + 7, 36, STONE)
    for (a, b, c, d) in ((X0, Y0, X1, Y0 + 6), (X0, 144, X1, Y1), (X0, Y0, X0 + 6, Y1), (184, Y0, X1, Y1)):
        M.box('body', a, b, 36, c, d, 40, WOOD_D)                     # 簷檁一圈
    for x in xs[1:-1]:                                                # 每一跨一根橫梁（沿 y；兩端停在屋面底下）
        M.box('body', x + 1, Y0 + 6, 40, x + 5, Y1 - 6, 44, WOOD_D)
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 40, 'p': 0.7, 'over': (8, 8, 8, 8)}])
    top = build_roof(M, F, thick=3, salt=10)
    for x in xs[1:-1]:                                                # 中線的高木柱撐到屋脊
        zt = min(top[(xx, yy)] - 2 for xx in range(x + 1, x + 5) for yy in range(78, 82))
        M.box('body', x + 1, 78, pl, x + 5, 82, zt, WOOD_D)
    # 攤位：木桌、上面的貨
    goods = (ORANGE, YELLOW, LEAF, PURPLE, ORANGE, LEAF)
    for i, (sx, sy) in enumerate(((24, 30), (110, 30), (24, 112), (110, 112), (56, 56), (138, 104))):
        M.box('body', sx, sy, 9, sx + 18, sy + 9, 10, WOOD)
        for (lx, ly) in ((sx, sy), (sx + 17, sy), (sx, sy + 8), (sx + 17, sy + 8)):
            M.box('body', lx, ly, pl, lx + 1, ly + 1, 9, WOOD_D)
        for gx in range(sx + 1, sx + 17, 3):
            for gy in range(sy + 1, sy + 8, 3):
                M.box('body', gx, gy, 10, gx + 2, gy + 2, 12, goods[i])
    M.anchor('door', 100, 3, 0)
    M.models += [{'name': '貨箱%d' % (i + 1), 'source': 'summit-rocher-01m-crate', 'at': list(p), 'pivot': [6, 6, 0], 'meta': {}}
                 for i, p in enumerate(((48, 34, pl), (48, 34, pl + 6), (150, 50, pl), (88, 118, pl)))]
    M.models += [{'name': '酒桶%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': list(p), 'pivot': [6, 6, 0], 'meta': {}}
                 for i, p in enumerate(((160, 120, pl), (167, 120, pl), (80, 60, pl)))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'market', 'title': '市場（halle：石柱一圈、中線木柱、大的四坡頂、石板地台、攤位）', 'use': 'market', 'lot': (20, 16), 'M': M,
            'layers': {'body': '柱與地台', 'roof': '屋頂'}}


# ─────────────────────────────── 市政廳 20 × 16 m ───────────────────────────────
def townhall():
    M = Model((200, 160, 172))
    X0, Y0, X1, Y1 = 12, 34, 188, 150
    R, t = (X0, Y0, X1, Y1), 3
    PV = (76, 28, 124, 40)                                            # 中央凸出的門廳
    M.box('body', X0, Y0, 0, X1, Y1, 6, STONE)
    M.box('body', 76, 28, 0, 124, Y0, 6, STONE)
    walls_union(M, [R, PV], 6, 84, t, OCHRE)
    floor_slab(M, (X0, Y0, X1, Y1), 42, 44)
    floor_slab(M, (76, 28, 124, Y0), 42, 44)
    quoins(M, R, 6, 84)
    quoins(M, (76, 28, 124, Y0 + 3), 6, 84)
    for rr in (R, (76, 28, 124, Y0 + 3)):
        band(M, rr, 42, 44, STONE_L, out=1)
        band(M, rr, 80, 84, TRIM, out=1)
    # 門廳：門、二樓落地窗＋鐵欄杆陽台、正面石階
    put_part(M, 'door', '前-大門', 'front', PV, 100, 6, t)
    put_part(M, 'frenchdoor', '前-陽台門', 'front', PV, 100, 44, t)
    M.box('gallery', 88, 21, 41, 112, 28, 44, STONE_L)
    iron_rail(M, 88, 112, 21, 28, 44, 10)
    for k, (yy, zh) in enumerate(((25, 6), (22, 4), (19, 2))):
        M.box('body', 86, yy, 0, 114, yy + 3, zh, STONE_L)
    M.anchor('door', 100, 27, 6)
    for i, cx in enumerate((30, 54, 146, 170)):
        put_part(M, 'window-arch', '前-窗%d' % (i + 1), 'front', R, cx, 6 + 8, t)
        put_part(M, 'window-arch', '前-二樓窗%d' % (i + 1), 'front', R, cx, 44 + 6, t)
    put_part(M, 'door', '後-門', 'back', R, 100, 6, t)
    for i, cx in enumerate((30, 60, 140, 170)):
        put_part(M, 'window-arch', '後-窗%d' % (i + 1), 'back', R, cx, 6 + 8, t)
    for i, cx in enumerate((30, 60, 100, 140, 170)):
        put_part(M, 'window-arch', '後-二樓窗%d' % (i + 1), 'back', R, cx, 44 + 6, t)
    for face in ('left', 'right'):
        for i, cy in enumerate((70, 114)):
            nm = '左' if face == 'left' else '右'
            put_part(M, 'window-arch', '%s-窗%d' % (nm, i + 1), face, R, cy, 6 + 8, t)
            put_part(M, 'window-arch', '%s-二樓窗%d' % (nm, i + 1), face, R, cy, 44 + 6, t)
    # 屋頂：主屋四坡（0.85）＋門廳兩坡、正面山牆（鐘面）
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 84, 'p': 0.85, 'over': (5, 5, 5, 5)},
                    {'x0': 76, 'y0': 28, 'x1': 124, 'y1': 60, 'ze': 84, 'p': 0.55, 'over': (3, 3, 0, 0), 'gable': 'y'}])
    top = build_roof(M, F, salt=11)
    gable_wall(M, 76, 124, 28, 31, 84, 0.55, OCHRE, edge=TRIM)
    for x in range(94, 106):                                          # 鐘面（山牆三角裡）
        for z in range(85, 97):
            r = math.hypot(x + 0.5 - 100, z + 0.5 - 90.5)
            if r < 5.2:
                c = TRIM if r < 4.4 else STONE_L
                if (abs(x + 0.5 - 100) < 0.6 and 90 <= z < 94) or (abs(z + 0.5 - 90.5) < 0.6 and 100 <= x < 103):
                    c = IRON
                M.put('body', x, 27, z, c)
    for i, cx in enumerate((50, 64, 136, 150)):
        dormer_on(M, top, cx, 'front', R, 4, '老虎窗-前%d' % (i + 1))
    for i, cx in enumerate((50, 80, 120, 150)):
        dormer_on(M, top, cx, 'back', R, 4, '老虎窗-後%d' % (i + 1))
    for i, cx in enumerate((70, 130)):
        free_part(M, 'chimney', '煙囪%d' % (i + 1), (cx - 4, 88, top[(cx, 92)] - 33))
    # 鐘樓（campanile）：屋脊正中一座方的木構小樓，四面拱口、鐘、穹頂
    cx0, cy0, cw = 88, 80, 24
    zr = min(top[(x, y)] for x in range(cx0, cx0 + cw) for y in range(cy0, cy0 + cw))
    for z in range(zr - 1, 150):
        for x in range(cx0, cx0 + cw):
            for y in range(cy0, cy0 + cw):
                if x in (cx0, cx0 + cw - 1, cx0 + 1, cx0 + cw - 2) or y in (cy0, cy0 + cw - 1, cy0 + 1, cy0 + cw - 2):
                    corner = (x - cx0 < 4 or cx0 + cw - 1 - x < 4) and (y - cy0 < 4 or cy0 + cw - 1 - y < 4)
                    M.put('roof', x, y, z, STONE_L if corner else TRIM, force=True)
    for z in range(130, 146):                                         # 拱口
        for k in range(6, cw - 6):
            if z >= 143 and (k < 8 or k > cw - 9):
                continue
            for d in (0, 1):
                for (x, y) in ((cx0 + k, cy0 + d), (cx0 + k, cy0 + cw - 1 - d), (cx0 + d, cy0 + k), (cx0 + cw - 1 - d, cy0 + k)):
                    M.cells.pop((x, y, z), None)
    M.box('roof', cx0 - 1, cy0 - 1, 128, cx0 + cw + 1, cy0 + cw + 1, 130, STONE_L, force=True)
    M.box('roof', cx0 - 2, cy0 - 2, 150, cx0 + cw + 2, cy0 + cw + 2, 152, TRIM, force=True)
    for z in range(152, 166):                                         # 穹頂（鉛皮）＋尖頂
        r = (cw / 2 + 1) * math.sqrt(max(0.0, 1 - ((z - 152) / 14.0) ** 2))
        for x in range(cx0 - 2, cx0 + cw + 2):
            for y in range(cy0 - 2, cy0 + cw + 2):
                if max(abs(x + 0.5 - (cx0 + cw / 2)), abs(y + 0.5 - (cy0 + cw / 2))) < r:
                    M.put('roof', x, y, z, SLATE)
    M.box('roof', 99, 91, 166, 102, 94, 171, GOLD)
    for z in range(134, 144):                                         # 鐘（口大頂小）
        rr = 5 - (z - 134) * 0.35
        for x in range(92, 109):
            for y in range(84, 101):
                if math.hypot(x + 0.5 - 100, y + 0.5 - 92) < rr:
                    M.put('roof', x, y, z, BRONZE)
    M.box('roof', 99, 91, 144, 101, 93, 150, WOOD_D)
    M.anchor('bell', 100, 92, 138)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'townhall', 'title': '市政廳（hôtel de ville：二層＋閣樓、中央門廳與鐘面山牆、弧拱窗、四坡頂老虎窗、屋脊鐘樓；土黃牆）', 'use': 'townhall', 'lot': (20, 16), 'M': M,
            'layers': {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂與鐘樓'}}


# ─────────────────────────────── 總督府 28 × 22 m ───────────────────────────────
def governor():
    M = Model((280, 220, 150))
    MAIN, WL, WR = (20, 120, 260, 208), (20, 56, 76, 123), (204, 56, 260, 123)
    PV = (110, 114, 170, 126)
    t = 3
    for r in (MAIN, WL, WR, PV):
        M.box('body', r[0], r[1], 0, r[2], r[3], 6, STONE)
    walls_union(M, [MAIN, WL, WR, PV], 6, 88, t, CREAM)
    for r in (MAIN, WL, WR, PV):
        floor_slab(M, r, 44, 46)
    for r in (MAIN, WL, WR):
        quoins(M, r, 6, 88)
    for r in (MAIN, WL, WR, PV):
        band(M, r, 44, 46, STONE_L, out=1)
        band(M, r, 84, 88, TRIM, out=1)
    # 開口：主屋面向中庭（門廳的門＋長陽台）、兩翼朝街與朝中庭、背面
    put_part(M, 'door', '中庭-大門', 'front', PV, 140, 6, t)
    for i, cx in enumerate((121, 159)):
        put_part(M, 'window-arch', '中庭-門廳窗%d' % (i + 1), 'front', PV, cx, 6 + 8, t)
    for i, cx in enumerate((128, 152)):
        put_part(M, 'frenchdoor', '中庭-陽台門%d' % (i + 1), 'front', PV, cx, 46, t)
    M.box('gallery', 110, 107, 43, 170, 114, 46, STONE_L)
    iron_rail(M, 110, 170, 107, 114, 46, 10)
    for i, cx in enumerate((94, 186)):
        put_part(M, 'window-arch', '中庭-窗%d' % (i + 1), 'front', MAIN, cx, 6 + 8, t)
        put_part(M, 'window-arch', '中庭-二樓窗%d' % (i + 1), 'front', MAIN, cx, 46 + 6, t)
    for i, cx in enumerate((40, 70, 100, 140, 180, 210, 240)):
        put_part(M, 'window-arch', '後-窗%d' % (i + 1), 'back', MAIN, cx, 6 + 8, t)
        put_part(M, 'window-arch', '後-二樓窗%d' % (i + 1), 'back', MAIN, cx, 46 + 6, t)
    for r, nm, inner in ((WL, '左翼', 'right'), (WR, '右翼', 'left')):
        for i, cx in enumerate((r[0] + 16, r[0] + 40)):
            put_part(M, 'window-arch', nm + '-街窗%d' % (i + 1), 'front', r, cx, 6 + 8, t)
            put_part(M, 'window-arch', nm + '-街二樓窗%d' % (i + 1), 'front', r, cx, 46 + 6, t)
        put_part(M, 'door', nm + '-門', inner, r, 76, 6, t)
        put_part(M, 'window-arch', nm + '-中庭窗', inner, r, 100, 6 + 8, t)
        for i, cy in enumerate((76, 100)):
            put_part(M, 'window-arch', nm + '-中庭二樓窗%d' % (i + 1), inner, r, cy, 46 + 6, t)
    for face, r, nm in (('left', MAIN, '主屋左'), ('right', MAIN, '主屋右'), ('left', WL, '左翼左'), ('right', WR, '右翼右')):
        for i, cy in enumerate((r[1] + 22, r[3] - 22) if r is MAIN else (r[1] + 30,)):
            put_part(M, 'window-arch', '%s-窗%d' % (nm, i + 1), face, r, cy, 6 + 8, t)
            put_part(M, 'window-arch', '%s-二樓窗%d' % (nm, i + 1), face, r, cy, 46 + 6, t)
    # 屋頂：三塊四坡（主屋、兩翼）＋門廳兩坡、正面山牆（王室紋章）
    F = roof_field([{'x0': MAIN[0], 'y0': MAIN[1], 'x1': MAIN[2], 'y1': MAIN[3], 'ze': 88, 'p': 0.85, 'over': (6, 6, 6, 6)},
                    {'x0': WL[0], 'y0': WL[1], 'x1': WL[2], 'y1': MAIN[3], 'ze': 88, 'p': 0.85, 'over': (6, 6, 6, 0)},    # 兩翼的屋脊一路伸進主屋 ⇒ 接成天溝
                    {'x0': WR[0], 'y0': WR[1], 'x1': WR[2], 'y1': MAIN[3], 'ze': 88, 'p': 0.85, 'over': (6, 6, 6, 0)},
                    {'x0': PV[0], 'y0': PV[1], 'x1': PV[2], 'y1': 150, 'ze': 88, 'p': 0.55, 'over': (3, 3, 0, 0), 'gable': 'y'}])
    top = build_roof(M, F, salt=12)
    gable_wall(M, PV[0], PV[2], PV[1], PV[1] + 3, 88, 0.55, CREAM, edge=TRIM)
    for x in range(133, 148):                                         # 紋章：藍盾、三朵金色百合（山牆三角裡）
        for z in range(89, 100):
            dx = abs(x + 0.5 - 140.5)
            if dx < (6 if z > 92 else (z - 88) * 1.7):
                M.put('body', x, PV[1] - 1, z, SH_BLUE)
    for (fx, fz) in ((137, 95), (143, 95), (140, 91)):
        for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (-1, 1), (2, 1)):
            M.put('body', fx + dx, PV[1] - 1, fz + dz, GOLD, force=True)
    for i, cx in enumerate((60, 90, 190, 220)):
        dormer_on(M, top, cx, 'back', MAIN, 4, '老虎窗-後%d' % (i + 1))
    for i, cx in enumerate((80, 200)):
        dormer_on(M, top, cx, 'front', MAIN, 4, '老虎窗-前%d' % (i + 1))
    for i, cx in enumerate((70, 210)):
        free_part(M, 'chimney', '煙囪%d' % (i + 1), (cx - 4, 160, 100))
    # 中庭前的圍牆：矮牆＋鐵柵、石柱、大門的兩根門柱（球頂）與開著的鐵門
    for x in range(20, 260):
        if 124 <= x < 156:
            continue
        for y in range(10, 14):
            for z in range(0, 10):
                M.put('body', x, y, z, CREAM if z < 9 else STONE_L)
        if x % 2 == 0:
            for z in range(10, 24):
                M.put('body', x, 12, z, IRON)
        M.put('body', x, 12, 24, IRON)
    for px in list(range(20, 116, 32)) + list(range(164, 260, 32)) + [256]:
        M.box('body', px, 9, 0, px + 4, 15, 28, STONE_L, force=True)
    for px in (116, 156):
        M.box('body', px, 8, 0, px + 8, 16, 36, STONE_L, force=True)
        M.box('body', px + 1, 9, 36, px + 7, 15, 38, STONE)
        for x in range(px + 1, px + 7):
            for y in range(9, 15):
                for z in range(38, 44):
                    if math.hypot(x + 0.5 - (px + 4), y + 0.5 - 12, z + 0.5 - 41) < 3.2:
                        M.put('body', x, y, z, STONE_L)
    for (hx, sgn) in ((124, 1), (156, -1)):                           # 兩扇鐵門開向中庭（貼著門柱內側）
        for y in range(15, 31):
            M.put('body', hx if sgn > 0 else hx - 1, y, 30, IRON)
            M.put('body', hx if sgn > 0 else hx - 1, y, 1, IRON)
            if y % 2 == 0:
                for z in range(1, 30):
                    M.put('body', hx if sgn > 0 else hx - 1, y, z, IRON)
    # 旗杆（中庭正中）＋白旗（法國王旗）
    M.box('body', 139, 70, 0, 142, 73, 3, STONE_L)
    M.box('body', 140, 71, 3, 141, 72, 128, WOOD_D)
    M.box('body', 140, 71, 128, 141, 72, 130, GOLD)
    for x in range(141, 165):
        for z in range(108, 126):
            M.put('body', x, 71, z, TRIM)
    M.anchor('flag', 140, 71, 127)
    M.anchor('door', 140, 9, 0)
    M.models += [{'name': '燈籠-門柱%d' % (i + 1), 'source': 'summit-rocher-01m-lantern', 'at': [px + 4, 8, 30.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}
                 for i, px in enumerate((116, 156))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'governor', 'title': '總督府（gouvernement：主屋＋兩翼圍出中庭、門廳山牆的王室紋章、長陽台、鐵柵與門柱、旗杆；米白牆）', 'use': 'governor', 'lot': (28, 22), 'M': M,
            'layers': {'body': '牆身與圍牆', 'gallery': '陽台', 'roof': '屋頂'}}


# ─────────────────────────────── 教堂 16 × 28 m ───────────────────────────────
def church():
    M = Model((160, 280, 230))
    X0, Y0, X1, Y1 = 24, 44, 136, 244
    R, t = (X0, Y0, X1, Y1), 4
    M.box('body', X0, Y0, 0, X1, Y1, 6, STONE_L)
    for x in range(X0 + t, X1 - t):                                   # 地坪：黑白方磚
        for y in range(Y0 + t, Y1 - t):
            M.put('body', x, y, 5, STONE_L if ((x // 5) + (y // 5)) % 2 else STONE, force=True)
    stucco_walls(M, R, 6, 96, t, CREAM)
    quoins(M, R, 6, 96)
    band(M, R, 90, 96, TRIM, out=1)
    for by in (64, 104, 144, 184, 224):                               # 扶壁（壁柱）
        M.box('body', X0 - 3, by - 2, 6, X0, by + 2, 90, STONE_L)
        M.box('body', X1, by - 2, 6, X1 + 3, by + 2, 90, STONE_L)
    for face in ('left', 'right'):
        for i, cy in enumerate((84, 124, 164, 204)):
            put_part(M, 'window-round', '%s-窗%d' % ('左' if face == 'left' else '右', i + 1), face, R, cy, 30, t)
    # 半圓後殿
    cxa, cya, ra = 80, Y1, 36
    for x in range(cxa - ra - 1, cxa + ra + 1):
        for y in range(Y1 - 4, 280):
            r = math.hypot(x + 0.5 - cxa, y + 0.5 - cya)
            if y >= Y1 and ra - t <= r < ra:
                for z in range(0, 90):
                    M.put('body', x, y, z, STONE_L if z < 6 else CREAM)
            elif y >= Y1 and r < ra - t:
                for z in range(0, 6):
                    M.put('body', x, y, z, STONE_L)
    M.clear(cxa - ra + t, Y1 - t, 6, cxa + ra - t, Y1, 90, 'body')   # 打通後殿與正殿
    # 屋頂：正殿兩坡（屋脊沿 y）＋後殿半圓錐
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 96, 'p': 0.6, 'over': (6, 6, 0, 0), 'gable': 'y'}])
    for x in range(cxa - ra - 6, cxa + ra + 6):
        for y in range(Y1, 280):
            r = math.hypot(x + 0.5 - cxa, y + 0.5 - cya)
            if r < ra + 5:
                z = 90 + 0.6 * (ra - r)
                cur = F.get((x, y))
                if cur is None or z > cur[0]:
                    F[(x, y)] = (z, 'front', False, 1)
    top = build_roof(M, F, salt=13)
    gable_wall(M, X0, X1, Y1 - t, Y1, 96, 0.6, CREAM, edge=TRIM)    # 後山牆（後殿屋頂上面露出來的那一塊）
    # 正立面：兩層古典立面＋渦卷＋山牆頂＋十字架
    FY0, FY1 = 36, Y0
    M.box('body', 16, FY0, 0, 144, FY1, 6, STONE_L)
    M.box('body', 16, FY0, 6, 144, FY1, 76, CREAM)
    for px in (16, 44, 110, 138):                                     # 下層壁柱
        M.box('body', px, FY0 - 2, 6, px + 6, FY1, 76, STONE_L, force=True)
    M.box('body', 14, FY0 - 3, 76, 146, FY1, 84, TRIM, force=True)    # 簷部
    M.box('body', 44, FY0, 84, 116, FY1, 130, CREAM)
    for px in (44, 110):
        M.box('body', px, FY0 - 2, 84, px + 6, FY1, 130, STONE_L, force=True)
    for side in (-1, 1):                                              # 渦卷（四分之一圓）
        for k in range(0, 24):
            x = (44 - 1 - k) if side < 0 else (116 + k)
            h = int(30 * math.sqrt(max(0.0, 1 - ((k + 0.5) / 24.0) ** 2)))
            for z in range(84, 84 + h):
                for y in range(FY0 + 2, FY1):
                    M.put('body', x, y, z, TRIM if z >= 84 + h - 2 else CREAM, force=True)
    M.box('body', 42, FY0 - 3, 126, 118, FY1, 130, TRIM, force=True)
    gable_wall(M, 42, 118, FY0, FY1, 130, 0.5, CREAM, edge=TRIM)      # 三角山牆頂
    M.box('body', 79, 39, 149, 81, 42, 168, IRON, force=True)         # 十字架
    M.box('body', 74, 39, 160, 86, 42, 162, IRON, force=True)
    # 大門：半圓拱、石框、兩扇木門
    for x in range(64, 96):
        for z in range(6, 60):
            dx = x + 0.5 - 80
            inside = (z < 46 and abs(dx) < 12) or (z >= 46 and math.hypot(dx, z + 0.5 - 46) < 12)
            frame = (z < 46 and abs(dx) < 15) or (z >= 46 and math.hypot(dx, z + 0.5 - 46) < 15)
            if inside:
                for y in range(FY0, FY1 + t):
                    M.cells.pop((x, y, z), None)
                M.put('body', x, FY1 - 2, z, WOOD_D if (abs(dx) < 1 or (z - 6) % 8 == 7) else WOOD, force=True)
            elif frame:
                M.put('body', x, FY0 - 1, z, STONE_L, force=True)
    for k, (yy, zh) in enumerate(((33, 6), (30, 4), (27, 2))):        # 三級石階
        M.box('body', 50, yy, 0, 110, yy + 3, zh, STONE_L, force=True)
    M.anchor('door', 80, 35, 6)
    FR = (16, FY0, 144, FY1)
    for i, cx in enumerate((30, 130)):
        put_part(M, 'window-round', '正面-窗%d' % (i + 1), 'front', FR, cx, 24, 8)
    place_free(M, PT_OCULUS, '正面-圓窗', (72, FY0 - 1, 96))
    carve_cells(M, M.links[-1]['cells'], ('body',))
    for x in range(74, 87):                                           # 圓窗後面挖穿立面
        for z in range(98, 110):
            if math.hypot(x + 0.5 - 80, z + 0.5 - 104) < 5.2:
                for y in range(FY0 + 2, FY1):
                    M.cells.pop((x, y, z), None)
    # 鐘樓：正立面後面那一跨升起來
    TX0, TY0, TW = 60, 46, 40
    for z in range(84, 178):
        for x in range(TX0, TX0 + TW):
            for y in range(TY0, TY0 + TW):
                if x - TX0 < 4 or TX0 + TW - 1 - x < 4 or y - TY0 < 4 or TY0 + TW - 1 - y < 4:
                    corner = (x - TX0 < 6 or TX0 + TW - 1 - x < 6) and (y - TY0 < 6 or TY0 + TW - 1 - y < 6)
                    M.put('body', x, y, z, STONE_L if corner else CREAM, force=True)
    for zz in (136, 172):
        M.box('body', TX0 - 1, TY0 - 1, zz, TX0 + TW + 1, TY0 + TW + 1, zz + 3, TRIM, force=True)
    for k in range(TW):                                               # 四面的鐘口（半圓拱）
        for z in range(142, 170):
            dx = k + 0.5 - TW / 2
            if (z < 162 and abs(dx) < 7) or (z >= 162 and math.hypot(dx, z + 0.5 - 162) < 7):
                for d in range(4):
                    for (x, y) in ((TX0 + k, TY0 + d), (TX0 + k, TY0 + TW - 1 - d), (TX0 + d, TY0 + k), (TX0 + TW - 1 - d, TY0 + k)):
                        M.cells.pop((x, y, z), None)
    M.box('body', TX0 + 4, TY0 + 4, 140, TX0 + TW - 4, TY0 + TW - 4, 142, WOOD)   # 鐘樓的樓板
    bcx, bcy = TX0 + TW / 2, TY0 + TW / 2
    for z in range(148, 162):                                         # 鐘（口大頂小）
        rr = 7.5 - (z - 148) * 0.35
        for x in range(TX0 + 8, TX0 + TW - 8):
            for y in range(TY0 + 8, TY0 + TW - 8):
                if math.hypot(x + 0.5 - bcx, y + 0.5 - bcy) < rr:
                    M.put('body', x, y, z, BRONZE)
    M.box('body', int(bcx) - 1, int(bcy) - 1, 162, int(bcx) + 1, int(bcy) + 1, 172, WOOD_D)
    M.anchor('bell', int(bcx), int(bcy), 154)
    for z in range(175, 206):                                         # 八角穹頂（鉛皮）＋燈籠亭＋十字架
        r = (TW / 2 + 1) * math.sqrt(max(0.0, 1 - ((z - 175) / 31.0) ** 2))
        for x in range(TX0 - 1, TX0 + TW + 1):
            for y in range(TY0 - 1, TY0 + TW + 1):
                dx, dy = abs(x + 0.5 - bcx), abs(y + 0.5 - bcy)
                if max(dx, dy, (dx + dy) / 1.414) < r:
                    M.put('roof', x, y, z, SLATE)
    bx, by = int(bcx), int(bcy)
    for z in range(200, 212):                                         # 燈籠亭：8 格見方的空心小亭、四面開口、鉛皮頂
        for x in range(bx - 4, bx + 4):
            for y in range(by - 4, by + 4):
                edge = x in (bx - 4, bx + 3) or y in (by - 4, by + 3)
                corner = x in (bx - 4, bx + 3) and y in (by - 4, by + 3)
                if z >= 210:
                    M.put('roof', x, y, z, SLATE)
                elif edge and (corner or not (203 <= z < 208)):
                    M.put('roof', x, y, z, TRIM)
    M.box('roof', int(bcx) - 1, int(bcy) - 1, 212, int(bcx) + 1, int(bcy) + 1, 228, IRON)
    M.box('roof', int(bcx) - 5, int(bcy) - 1, 222, int(bcx) + 5, int(bcy) + 1, 224, IRON)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'church', 'title': '教堂（正殿兩坡頂、半圓後殿、兩層古典立面＋渦卷＋山牆、立面後的方鐘樓與八角穹頂；米白牆）', 'use': 'church', 'lot': (16, 28), 'M': M,
            'layers': {'body': '牆身與立面', 'roof': '屋頂與穹頂'}}


import parts as _PT
PT_OCULUS = _PT.all_parts()['oculus']

ALL = [tavern, warehouse, market, townhall, governor, church]
