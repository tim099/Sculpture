# 住宅三型（TASK-0741；地塊 8 × 12 m ＝ 80 × 120 格）：
#   A 二層樓、二樓托架木陽台、四坡頂、後院＋廚房小屋（土黃牆、綠百葉）
#   B 平房「有廊的屋子」（case à galerie）：前廊細柱、陡的四坡頂接緩坡廊頂、兩扇老虎窗、後院木柵＋小棚（藍牆）
#   C 二層樓、上下兩層外廊（一樓石柱、二樓木柱）、四坡頂接緩坡、後院＋廚房小屋＋水井（米白牆、紅百葉）
# 屋身都在地塊前半、後半圍成院子；屋簷不出地塊（兩側鄰居的地塊只隔 2 cm）。
# 淺版 8 × 10 m（house-a-s／b-s／c-s；TASK-0742，Tim 2026-10-22「轉角放淺一點的房子」）：屋子一模一樣、院牆／木柵收到後緣 —— 廚房小屋、小棚放不下就不擺，
#   C 的水井往前挪（Manor Lords 的 burgage plot：地塊夠深才有後院擴建）。D ＝ 地塊進深（格；120 ＝ 原本那一份，逐位元組不變）。
# 小版 8 × 8 m（house-a-xs／b-xs／c-xs；TASK-0840，Tim 2026-10-23「加8x8模型吧」）：城鎮的綁路格 4 m 一格之後，轉角只剩 2 格深（8 m）⇒ 這一版。
#   沒有院子（後門直接開到後巷）；A 的屋子原樣放得下（陽台 y 3～屋簷 y 78）；B、C 的屋身淺 0.4 m（5.4 ⇒ 5.0 m）、B 的前廊淺 0.6 m（2.0 ⇒ 1.4 m）——
#   屋身的進深、簷口、煙囪、老虎窗、側窗都照 Y0／Y1 算（D 100、120 的位置算出來跟原本一樣 ⇒ 逐位元組不變）。
from kit import *
import parts as PT

PARTS = PT.all_parts()


def put_part(M, pid, name, face, rect, center, z, t):
    """部件的開口中心對準 center（front／back 量 x、left／right 量 y），底在 z。"""
    P = PARTS[pid]
    W = P['dims'][0]
    X0, Y0, X1, Y1 = rect
    if face == 'front':
        u = center - X0 - W // 2
    elif face == 'back':
        u = X1 - W - center + W // 2
    elif face == 'right':
        u = center - W // 2 - Y0
    else:
        u = Y1 - W - center + W // 2
    return place(M, P, name, face, rect, u, z, t)


def free_part(M, pid, name, at, turn=0, mirror='', carve=('roof',)):
    P = PARTS[pid]
    place_free(M, P, name, at, turn, mirror)
    return carve_cells(M, M.links[-1]['cells'], carve)


def simple_door(M, face, rect, center, w, h, t, z0=0, color=None):
    """沒有框的木板門（廚房、棚子）：挖穿牆厚、在牆中間那一層放一片門板。"""
    X0, Y0, X1, Y1 = rect
    color = M.shutter if color is None else color
    a = center - w // 2
    for u in range(a, a + w):
        for z in range(z0, z0 + h):
            for k in range(t):
                if face == 'front':
                    p = (u, Y0 + k, z)
                elif face == 'back':
                    p = (u, Y1 - 1 - k, z)
                elif face == 'right':
                    p = (X1 - 1 - k, u, z)
                else:
                    p = (X0 + k, u, z)
                M.cells.pop(p, None)
                if k == t // 2:
                    c = WOOD_D if (u - a) % 3 == 2 or z == z0 + h // 2 else color
                    M.put('body', p[0], p[1], p[2], c)


def yard(M, x0, y0, x1, y1, t, h, color, gate=None, coping=TILE_R):
    """院牆：左、右、後三面（前面是屋子的後牆）；gate ＝ (中心 x, 寬, 高) 開在後牆、放一扇關著的門。"""
    for (a, b, c, d) in ((x0, y0, x0 + t, y1), (x1 - t, y0, x1, y1), (x0, y1 - t, x1, y1)):
        M.box('body', a, b, 0, c, d, h, color)
        M.box('body', a, b, h, c, d, h + 2, coping)
    if gate:
        gx, gw, gh = gate
        simple_door(M, 'back', (x0, y0, x1, y1), gx, gw, gh, t)


def kitchen(M, rect, color, door_face, door_c, vent_face=None, vent_c=None, low='front', chim=None, salt=0):
    """廚房小屋：一層、牆厚 3、單坡頂（low 那一邊低）、木板門、一扇氣窗、煙囪。"""
    X0, Y0, X1, Y1 = rect
    t, h = 3, 26
    stucco_walls(M, rect, 0, h + 4, t, color)
    simple_door(M, door_face, rect, door_c, 9, 19, t)
    if vent_face:
        put_part(M, 'vent', '廚房-氣窗', vent_face, rect, vent_c, 10, t)
    # 單坡：高的那邊牆頂 h+4、低的那邊 h；坡面多出簷 3 格
    ov = 3
    span = (Y1 - Y0) if low in ('front', 'back') else (X1 - X0)
    p = 4.0 / span
    zhi = h + 4 + int(round(p * ov)) + 1
    xs0, ys0, xs1, ys1 = X0 - ov, Y0 - ov, X1 + ov, Y1 + ov
    # 牆頂照坡面切（高的那邊高、低的那邊低）
    for (x, y, z) in [k for k in M.cells if X0 <= k[0] < X1 and Y0 <= k[1] < Y1 and h <= k[2] < h + 4]:
        d = {'front': y + 0.5 - Y0, 'back': Y1 - (y + 0.5), 'left': x + 0.5 - X0, 'right': X1 - (x + 0.5)}[low]
        if z >= h + int(p * d):
            M.cells.pop((x, y, z), None)
    F = {}
    for x in range(xs0, xs1):
        for y in range(ys0, ys1):
            if not M.inb(x, y, 0):
                continue
            d = {'front': y + 0.5 - Y0, 'back': Y1 - (y + 0.5), 'left': x + 0.5 - X0, 'right': X1 - (x + 0.5)}[low]
            F[(x, y)] = (h + p * d + 1, 'front' if low in ('front', 'back') else 'left', False, 0)
    build_roof(M, F, 2, 'roof', salt=salt)
    if chim:
        free_part(M, 'chimney', '廚房-煙囪', chim, carve=('roof', 'body'))


def house_a(D=120):
    M = Model((80, D, 100))
    X0, Y0, X1, Y1 = 3, 12, 77, 72
    R, t, pl = (X0, Y0, X1, Y1), 3, 3
    M.box('body', X0, Y0, 0, X1, Y1, pl, STONE)                       # 石基（實心，也是一樓地面）
    stucco_walls(M, R, pl, 35, t, OCHRE)
    floor_slab(M, R, 35, 37)
    stucco_walls(M, R, 37, 67, t, OCHRE)
    quoins(M, R, pl, 67)
    band(M, R, 35, 37, TRIM, out=0)                                   # 樓層線
    band(M, R, 65, 67, TRIM, out=1)                                   # 簷口線腳
    # 開口
    put_part(M, 'door', '前-門', 'front', R, 40, pl, t)
    for i, cx in enumerate((17, 63)):
        put_part(M, 'window', '前-窗%d' % (i + 1), 'front', R, cx, pl + 9, t)
    for i, cx in enumerate((17, 40, 63)):
        put_part(M, 'frenchdoor', '前-落地窗%d' % (i + 1), 'front', R, cx, 37, t)
    put_part(M, 'door', '後-門', 'back', R, 40, pl, t)
    for i, cx in enumerate((20, 60)):
        put_part(M, 'window', '後-窗%d' % (i + 1), 'back', R, cx, 37 + 8, t)
    # 門前三級石階
    for k in range(3):
        M.box('body', 33, Y0 - 1 - k, 0, 48, Y0 - k, pl - k, STONE_L)
    M.anchor('door', 40, Y0 - 1, pl)
    # 二樓陽台（托架挑出 0.9 m）
    M.box('gallery', 5, 3, 35, 75, Y0, 37, WOOD)
    M.box('gallery', 5, 3, 35, 75, 4, 37, WOOD_D)
    for bx in (5, 27, 51, 73):                                        # 托架（實心三角）
        for y in range(4, Y0):
            for z in range(34 - (y - 4) - 1, 35):
                M.box('gallery', bx, y, z, bx + 2, y + 1, z + 1, WOOD_D)
    for x in range(5, 75):                                            # 鍛鐵欄杆＋木扶手
        M.put('gallery', x, 3, 37, IRON)
        M.put('gallery', x, 3, 46, WOOD_D)
        if x % 2 == 0:
            for z in range(38, 46):
                M.put('gallery', x, 3, z, IRON)
    for xs in (5, 74):
        for y in range(3, Y0):
            M.put('gallery', xs, y, 37, IRON)
            M.put('gallery', xs, y, 46, WOOD_D)
            if y % 2 == 1:
                for z in range(38, 46):
                    M.put('gallery', xs, y, z, IRON)
    # 屋頂：四坡，前簷深（蓋過陽台）
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 67, 'p': 0.85, 'over': (3, 3, 10, 6)}])
    build_roof(M, F, salt=1)
    free_part(M, 'chimney', '煙囪', (62, 58, 60))
    if D <= 80:                                                        # 小版 8 × 8：屋身到 y 72、屋簷到 y 78 ⇒ 沒有院子，後門開到後巷
        M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [28.5, Y0, 24.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
        M.anchor('lot-0', 0, 0, 0)
        return {'key': 'house-a-xs', 'title': '住宅 A 小版（地塊 8 × 8：同 A 的屋子；沒有院子）', 'use': 'house', 'lot': (8, 8), 'M': M,
                'layers': {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂'}}
    # 後院：院牆、後門、廚房（左後角）
    yard(M, X0, Y1, X1, D, 3, 22, OCHRE, gate=(56, 13, 19))
    if D < 120:                                                        # 淺版：院子 2.5 m（屋身到 y 72、院牆 y 97..100）⇒ 廚房、酒桶放不下
        M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [28.5, Y0, 24.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
        M.anchor('lot-0', 0, 0, 0)
        return {'key': 'house-a-s', 'title': '住宅 A 淺版（地塊 8 × %d：同 A 的屋子；院子只剩院牆，沒有廚房）' % (D // 10), 'use': 'house', 'lot': (8, D // 10), 'M': M,
                'layers': {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂'}}
    kitchen(M, (X0 + 3, 92, 34, 117), OCHRE, 'right', 104, vent_face='front', vent_c=18, low='right', chim=(6, 108, 2), salt=2)
    M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [28.5, Y0, 24.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '酒桶-院1', 'source': 'summit-rocher-01m-barrel', 'at': [66, 100, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-院2', 'source': 'summit-rocher-01m-barrel', 'at': [66, 107, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-a', 'title': '住宅 A（二層樓、二樓托架木陽台、四坡頂、後院＋廚房；土黃牆綠百葉）', 'use': 'house', 'lot': (8, 12), 'M': M,
            'layers': {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂'}}


def house_b(D=120):
    M = Model((80, D, 82))
    X0, Y0, X1, Y1 = (6, 24, 74, 74) if D <= 80 else (6, 30, 74, 84)  # 小版：前廊 y 10..24（1.4 m）、屋身 5.0 m、後簷到 y 80
    R, t, pl = (X0, Y0, X1, Y1), 3, 6
    M.box('body', X0, Y0, 0, X1, Y1, pl, STONE)
    stucco_walls(M, R, pl, 40, t, BLUE)
    quoins(M, R, pl, 40, color=TRIM, long=2, short=2, step=200)       # 轉角護板（白）
    band(M, R, 38, 40, TRIM, out=0)
    put_part(M, 'door', '前-門', 'front', R, 40, pl, t)
    for i, cx in enumerate((16, 64)):
        put_part(M, 'frenchdoor', '前-落地窗%d' % (i + 1), 'front', R, cx, pl, t)
    for i, cx in enumerate((22, 58)):
        put_part(M, 'window', '後-窗%d' % (i + 1), 'back', R, cx, pl + 9, t)
    put_part(M, 'window', '左-窗', 'left', R, (Y0 + Y1) // 2, pl + 9, t)   # 側窗在屋身中間（原本 57）
    put_part(M, 'window', '右-窗', 'right', R, (Y0 + Y1) // 2, pl + 9, t)
    simple_door(M, 'back', R, 40, 10, 22, t, z0=pl)
    # 前廊：石基＋木地板、細柱、欄杆、中間三級石階
    M.box('gallery', 4, 10, 0, 76, Y0, pl - 1, STONE)
    M.box('gallery', 4, 10, pl - 1, 76, Y0, pl, WOOD)
    for k, zh in enumerate((4, 2)):                                   # 兩級石階（每級 0.2 m），上到廊的地板 0.6 m
        M.box('gallery', 34, 10 - 3 * (k + 1), 0, 46, 10 - 3 * k, zh, STONE_L)
    # 屋頂：陡的四坡（1.0）＋前廊緩坡（0.45）
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 40, 'p': 1.0, 'over': (6, 6, Y0 - 6, 6), 'kick': {'front': 0.45}}])   # 前簷蓋到 y 6（原本 24）
    top = build_roof(M, F, salt=3)
    posts = (4, 22, 39, 56, 74)
    for px in posts:
        zt = min(top[(x, y)] - 1 for x in range(px, px + 2) for y in range(10, 12))
        M.box('gallery', px, 10, pl, px + 2, 12, zt, TRIM)
    zb = min(top[(x, 11)] - 1 for x in range(4, 76))
    M.box('gallery', 4, 10, zb - 2, 76, 12, zb, TRIM)                 # 柱頂的橫梁
    for x in range(4, 76):                                            # 欄杆（中間留給石階）
        if 34 <= x < 46:
            continue
        M.put('gallery', x, 10, pl + 9, TRIM)
        M.put('gallery', x, 10, pl + 1, TRIM)
        if x % 3 == 0:
            for z in range(pl + 2, pl + 9):
                M.put('gallery', x, 10, z, TRIM)
    for xs in (4, 75):
        for y in range(10, Y0):
            M.put('gallery', xs, y, pl + 9, TRIM)
            if y % 3 == 0:
                for z in range(pl, pl + 9):
                    M.put('gallery', xs, y, z, TRIM)
    M.anchor('door', 40, Y0 - 1, pl)
    for i, cx in enumerate((24, 56)):                                 # 兩扇老虎窗：前牆底埋進屋面一格
        y0 = Y0 + 3                                                    # 原本 33
        zf = top[(cx, y0 + 1)] - 1
        free_part(M, 'dormer', '老虎窗%d' % (i + 1), (cx - 7, y0, zf))
    free_part(M, 'chimney', '煙囪', (62, Y1 - 30, 38))                 # 原本 y 54
    if D <= 80:                                                        # 小版 8 × 8：後簷到 y 80 ⇒ 沒有院子、木柵
        M.models += [{'name': '燈籠-廊', 'source': 'summit-rocher-01m-lantern', 'at': [29, Y0, 26.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
        M.anchor('lot-0', 0, 0, 0)
        return {'key': 'house-b-xs', 'title': '住宅 B 小版（地塊 8 × 8：B 的有廊屋子，屋身淺 0.4 m、前廊 1.4 m；沒有院子）', 'use': 'house', 'lot': (8, 8), 'M': M,
                'layers': {'body': '牆身', 'gallery': '前廊', 'roof': '屋頂'}}
    # 後院：木柵圍籬＋小棚
    yb = D - 2
    picket_fence(M, [(X0, Y1), (1, Y1), (1, yb), (36, yb)])
    picket_fence(M, [(46, yb), (78, yb), (78, Y1), (X1 - 1, Y1)])
    if D < 120:                                                        # 淺版：院子 1.4 m（屋身到 y 84、木柵 y 98）⇒ 小棚、貨箱放不下
        M.models += [{'name': '燈籠-廊', 'source': 'summit-rocher-01m-lantern', 'at': [29, Y0, 26.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
        M.anchor('lot-0', 0, 0, 0)
        return {'key': 'house-b-s', 'title': '住宅 B 淺版（地塊 8 × %d：同 B 的有廊屋子；院子只剩木柵，沒有小棚）' % (D // 10), 'use': 'house', 'lot': (8, D // 10), 'M': M,
                'layers': {'body': '牆身', 'gallery': '前廊', 'roof': '屋頂'}}
    sx0, sy0, sx1, sy1 = 50, 98, 74, 116
    for x in range(sx0, sx1):                                         # 木板牆：牆頂跟著單坡走
        for y in range(sy0, sy1):
            if x in (sx0, sx1 - 1) or y in (sy0, sy1 - 1):
                for z in range(0, int(22 + 0.25 * (y + 0.5 - sy0))):
                    M.put('body', x, y, z, WOOD_D if z % 4 == 3 else WOOD_G)
    simple_door(M, 'front', (sx0, sy0, sx1, sy1), 60, 8, 17, 1, color=WOOD_G)
    F2 = {}
    for x in range(sx0 - 2, sx1 + 2):
        for y in range(sy0 - 3, sy1 + 2):
            if M.inb(x, y, 0):
                F2[(x, y)] = (22 + 0.25 * (y + 0.5 - sy0), 'front', False, 0)
    build_roof(M, F2, 2, 'roof', color_fn=lambda x, y, f, r, e: WOOD_D if e else WOOD_G)
    M.models += [{'name': '燈籠-廊', 'source': 'summit-rocher-01m-lantern', 'at': [29, Y0, 26.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '貨箱-棚', 'source': 'summit-rocher-01m-crate', 'at': [44, 108, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-b', 'title': '住宅 B（平房 case à galerie：前廊細柱、陡四坡頂接緩坡、老虎窗、後院木柵＋小棚；藍牆）', 'use': 'house', 'lot': (8, 12), 'M': M,
            'layers': {'body': '牆身', 'gallery': '前廊', 'roof': '屋頂'}}


def house_c(D=120):
    M = Model((80, D, 98))
    M.shutter = SH_RED
    X0, Y0, X1, Y1 = (4, 22, 76, 72) if D <= 80 else (4, 24, 76, 78)  # 小版：外廊 y 6..22、屋身 5.0 m、後簷到 y 78
    R, t, pl = (X0, Y0, X1, Y1), 3, 4
    M.box('body', X0, Y0, 0, X1, Y1, pl, STONE)
    stucco_walls(M, R, pl, 36, t, CREAM)
    floor_slab(M, R, 36, 38)
    stucco_walls(M, R, 38, 68, t, CREAM)
    quoins(M, R, pl, 68)
    band(M, R, 36, 38, TRIM, out=0)
    put_part(M, 'door', '前-門', 'front', R, 40, pl, t)
    for i, cx in enumerate((15, 65)):
        put_part(M, 'window', '前-窗%d' % (i + 1), 'front', R, cx, pl + 9, t)
    for i, cx in enumerate((15, 40, 65)):
        put_part(M, 'frenchdoor', '前-落地窗%d' % (i + 1), 'front', R, cx, 38, t)
    put_part(M, 'door', '後-門', 'back', R, 40, pl, t)
    for i, cx in enumerate((20, 60)):
        put_part(M, 'window', '後-窗%d' % (i + 1), 'back', R, cx, 38 + 8, t)
    M.anchor('door', 40, Y0 - 1, pl)
    # 兩層外廊
    M.box('gallery', 2, 6, 0, 78, Y0, pl, STONE_L)                   # 一樓廊的石板地
    M.box('gallery', 2, 6, 36, 78, Y0, 38, WOOD)
    M.box('gallery', 2, 6, 36, 78, 7, 38, WOOD_D)
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 68, 'p': 0.8, 'over': (4, 4, Y0 - 4, 6), 'kick': {'front': 0.35}}])   # 前簷蓋到 y 4（原本 20）
    top = build_roof(M, F, salt=5)
    for px in (2, 26, 51, 75):
        M.box('gallery', px, 6, pl, px + 3, 9, 36, TRIM)                # 一樓石柱（抹白）
        zt = min(top[(x, y)] - 1 for x in range(px, px + 2) for y in range(6, 8))
        M.box('gallery', px, 6, 38, px + 2, 8, zt, TRIM)                # 二樓木柱
    zb = min(top[(x, 7)] - 1 for x in range(2, 78))
    M.box('gallery', 2, 6, zb - 2, 78, 8, zb, TRIM)
    for x in range(2, 78):                                            # 二樓欄杆
        M.put('gallery', x, 6, 48, TRIM)
        M.put('gallery', x, 6, 39, TRIM)
        if x % 3 == 0:
            for z in range(40, 48):
                M.put('gallery', x, 6, z, TRIM)
    for xs in (2, 77):
        for y in range(6, Y0):
            M.put('gallery', xs, y, 48, TRIM)
            if y % 3 == 0:
                for z in range(38, 48):
                    M.put('gallery', xs, y, z, TRIM)
    free_part(M, 'chimney', '煙囪', (7, Y1 - 18, 46))                 # 原本 y 60
    if D <= 80:                                                        # 小版 8 × 8：後簷到 y 78 ⇒ 沒有院子、廚房、水井
        M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [28.5, Y0, 25.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
        M.anchor('lot-0', 0, 0, 0)
        return {'key': 'house-c-xs', 'title': '住宅 C 小版（地塊 8 × 8：C 的兩層外廊屋子，屋身淺 0.4 m；沒有院子）', 'use': 'house', 'lot': (8, 8), 'M': M,
                'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}, 'shutter': SH_RED}
    # 後院：院牆、廚房（右後角）、水井
    yard(M, X0, Y1, X1, D, 3, 22, CREAM, gate=(22, 13, 19))
    if D >= 120:
        kitchen(M, (46, 92, X1 - 3, 117), CREAM, 'left', 104, vent_face='front', vent_c=60, low='left', chim=(64, 108, 2), salt=6)
    wx, wy = (26, 100) if D >= 120 else (56, 89)                      # 淺版：院子 1.9 m（屋身到 y 78、院牆 y 97..100）⇒ 廚房放不下，水井挪到右邊廚房原本那一角、往前
    for x in range(wx - 6, wx + 6):                                   # 水井：石圈＋木架
        for y in range(wy - 6, wy + 6):
            r = math.hypot(x + 0.5 - wx, y + 0.5 - wy)
            if 3.2 < r < 6.0:
                for z in range(0, 9):
                    M.put('body', x, y, z, STONE_L if z == 8 else STONE)
    M.box('body', wx - 6, wy - 1, 9, wx - 4, wy + 1, 30, WOOD_D)
    M.box('body', wx + 4, wy - 1, 9, wx + 6, wy + 1, 30, WOOD_D)
    M.box('body', wx - 6, wy - 1, 30, wx + 6, wy + 1, 32, WOOD_D)
    if D < 120:
        M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [28.5, Y0, 25.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
        M.anchor('lot-0', 0, 0, 0)
        return {'key': 'house-c-s', 'title': '住宅 C 淺版（地塊 8 × %d：同 C 的屋子；院子只剩院牆與水井，沒有廚房）' % (D // 10), 'use': 'house', 'lot': (8, D // 10), 'M': M,
                'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}, 'shutter': SH_RED}
    M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [28.5, Y0, 25.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '酒桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [12, 104, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-c', 'title': '住宅 C（二層樓、上下兩層外廊、四坡頂接緩坡、後院＋廚房＋水井；米白牆紅百葉）', 'use': 'house', 'lot': (8, 12), 'M': M,
            'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}, 'shutter': SH_RED}


def house_a_s():
    return house_a(100)


def house_b_s():
    return house_b(100)


def house_c_s():
    return house_c(100)


def house_a_xs():
    return house_a(80)


def house_b_xs():
    return house_b(80)


def house_c_xs():
    return house_c(80)


ALL = [house_a, house_b, house_c, house_a_s, house_b_s, house_c_s, house_a_xs, house_b_xs, house_c_xs]
