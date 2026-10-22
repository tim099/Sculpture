# 住宅三型（TASK-0757；地塊 8 × 12 m ＝ 80 × 120 格；史料見作品 references/README.md —— 每一格「照什麼／設計」都寫在那裡）：
#   A 「釘板的木屋」：毛石台基＋三級切石台階（Labat 的住屋）、木構架外釘橫板、牆頂 2.3 m（sablière ≤ 7 法尺）、木瓦（essente）四坡頂、
#      前面一道披屋式門廊（證據弱：Sloane 的 porch／Du Tertre 的 appentis）；後院木柵＋下風處的廚房披屋（鍋吊在兩根叉柱的橫木上）
#   B 「編條糊泥的小屋」（Labat 的標準小屋）：叉柱入土、編籬抹泥刷石灰、泥地；兩坡棕櫚葉頂、簷口垂到離地 0.6 m；門與唯一一扇窗都在山牆
#      （山牆朝街）；後院木柵＋燻肉架（boucan）＋養豬養雞的披屋
#   C 「兩層的商家」：一樓毛石（店面、貨門）、二樓木構架釘板（富戶「廳上加一層」）、外樓梯上二樓（Guadeloupe 修院的石底層＋木上層）、
#      二樓前廊（設計）、木瓦四坡頂；後院石牆＋木板廚房
# 屋子都在地塊前半、後半是院子；屋簷不出地塊（兩側鄰居只隔 2 cm）。
# 淺版 8 × 10 m（house-a-s／b-s／c-s；TASK-0742，Tim 2026-10-22「轉角放淺一點的房子」）：屋子一模一樣、院子縮到後緣 —— 廚房、披屋、燻肉架放不下就不擺
#   （Manor Lords 的 burgage plot：地塊夠深才有後院擴建）。D ＝ 地塊進深（格；120 ＝ 原本那一份，逐位元組不變）。
from carib import *
import parts as PT

PARTS = PT.all_parts()


def put_part(M, pid, name, face, rect, center, z, t):
    """部件的開口中心對準 center（front／back 量 x、left／right 量 y），底在 z。借來的法式部件百葉是綠 49 ⇒ 換成這一套的 SHUT。"""
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
    keep = M.shutter
    M.shutter = SHUT if P.get('src') else SH_GREEN
    r = place(M, P, name, face, rect, u, z, t)
    M.shutter = keep
    if P.get('src'):
        M.links[-1]['part'] = P['src']
    return r


def free_part(M, pid, name, at, turn=0, mirror='', carve=('roof',)):
    P = PARTS[pid]
    place_free(M, P, name, at, turn, mirror)
    if P.get('src'):
        M.links[-1]['part'] = P['src']
    return carve_cells(M, M.links[-1]['cells'], carve)


def lean_roof_posts(M, x0, y0, x1, y1, z_hi, p, low, roof_fn, posts, salt=0):
    """單坡的棚：posts ＝ [(x, y)…] 每根 2 × 2 立到屋面底下；屋面 roof_fn 鋪色。"""
    F = {}
    for x in range(x0, x1):
        for y in range(y0, y1):
            if not M.inb(x, y, 0):
                continue
            px, py = x + 0.5, y + 0.5
            d = {'front': y1 - py, 'back': py - y0, 'left': x1 - px, 'right': px - x0}[low]
            F[(x, y)] = (z_hi - p * d, low if low in ('front', 'back') else 'left', False, 0)
    top = build_roof(M, F, 2, 'roof', color_fn=lambda x, y, f, r, e: roof_fn(x, y, f, r, e, salt))
    for (px, py) in posts:
        zt = min(top[(x, y)] - 1 for x in range(px, px + 2) for y in range(py, py + 2))
        M.box('body', px, py, 0, px + 2, py + 2, zt, FRAME)
    return top


def hearth(M, x0, y0, x1, y1, h=6, hanger=True):
    """灶（三面石頭圍、中間黑的火口）；hanger ⇒ 兩根小叉柱架一根橫木、吊一口鍋（Du Tertre 2:451）。"""
    M.box('body', x0, y0, 0, x1, y1, h, RUBBLE)
    M.box('body', x0 + 2, y0, 2, x1 - 2, y1 - 2, h, DARK, force=True)
    if hanger:
        ym = (y0 + y1) // 2
        for x in (x0 - 2, x1):
            M.box('body', x, ym - 1, 0, x + 2, ym + 1, 16, FRAME)
        M.box('body', x0 - 2, ym - 1, 16, x1 + 2, ym + 1, 17, FRAME)
        M.box('body', (x0 + x1) // 2 - 3, ym - 3, 8, (x0 + x1) // 2 + 3, ym + 3, 12, DARK, force=True)   # 鍋
        M.box('body', (x0 + x1) // 2, ym, 12, (x0 + x1) // 2 + 1, ym + 1, 16, IRON)                       # 鍋鍊


def house_a(D=120):
    M = Model((80, D, 76))
    X0, Y0, X1, Y1 = 6, 28, 74, 78
    R, t, fl = (X0, Y0, X1, Y1), 2, 6                                   # 牆厚 0.2 m、地板頂 0.6 m（三級台階）
    GY0 = 12                                                           # 門廊 y 12..28（1.6 m 深）
    rubble_walls(M, (X0, GY0, X1, Y1), 0, fl - 1, 4, salt=1)           # 毛石台基（含門廊底下）
    M.box('body', X0 + 4, GY0 + 4, 0, X1 - 4, Y1 - 4, fl - 1, EARTH_W)  # 台基裡填土
    M.box('body', X0, Y0, fl - 1, X1, Y1, fl, FLOOR)
    board_walls(M, R, fl, 31, t)
    M.box('gallery', X0, GY0, fl - 1, X1, Y0, fl, FLOOR)
    put_part(M, 'door-plank', '前-門', 'front', R, 40, fl, t)
    for i, cx in enumerate((18, 62)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, fl + 7, t)
    put_part(M, 'door-plank', '後-門', 'back', R, 40, fl, t)          # 兩扇相對的門（Labat：前院與花園中軸）
    put_part(M, 'window-board', '左-窗', 'left', R, 53, fl + 7, t)
    put_part(M, 'window-board', '右-窗', 'right', R, 53, fl + 7, t)
    steps(M, 33, 47, GY0, 3, 2, 3, back=False, layer='body', color=RUBBLE)   # 三級切石台階
    steps(M, 34, 46, Y1, 3, 2, 3, back=True, layer='body', color=RUBBLE)
    M.anchor('door', 40, Y0 - 1, fl)
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 31, 'p': 1.0, 'over': (4, 4, 19, 4), 'kick': {'front': 0.45}}], salt=1)
    gallery_posts(M, (X0, 24, 54, X1 - 2), GY0, fl, top)
    # 後院：木柵（後面留院門）、下風處的廚房披屋（開敞、灶＋吊鍋）
    yb = D - 2
    palisade(M, [(X0, Y1), (1, Y1), (1, yb), (78, yb), (78, Y1), (X1 - 1, Y1)], gap={(x, yb) for x in range(36, 46)})
    if D < 120:                                                        # 淺版：院子 1.4 m（後台階到 y 84、後柵 y 98）⇒ 廚房披屋、酒桶、貨箱放不下
        M.models += [{'name': '燈籠-廊', 'source': 'summit-rocher-01m-lantern', 'at': [28.5, Y0, 20.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
        M.anchor('lot-0', 0, 0, 0)
        return {'key': 'house-a-s', 'title': '住宅 A 淺版（地塊 8 × %d：同 A 的屋子；院子只剩木柵，沒有廚房披屋）' % (D // 10), 'use': 'house', 'lot': (8, D // 10), 'M': M,
                'layers': {'body': '牆身', 'gallery': '門廊', 'roof': '屋頂'}}
    hearth(M, 54, 98, 66, 108)
    lean_roof_posts(M, 44, 88, 76, 116, 30, 0.35, 'back', thatch_color, [(46, 92), (72, 92), (46, 112), (72, 112)], salt=2)
    M.models += [{'name': '燈籠-廊', 'source': 'summit-rocher-01m-lantern', 'at': [28.5, Y0, 20.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '酒桶-水', 'source': 'summit-rocher-01m-barrel', 'at': [12, 88, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-院', 'source': 'summit-rocher-01m-crate', 'at': [24, 106, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-a', 'title': '住宅 A（釘板的木屋：毛石台基、三級切石台階、橫板牆、木瓦四坡頂、披屋式門廊；後院木柵＋廚房披屋）', 'use': 'house', 'lot': (8, 12), 'M': M,
            'layers': {'body': '牆身', 'gallery': '門廊', 'roof': '屋頂'}}


def house_b(D=120):
    """Labat 的標準小屋（30 × 15 法尺 ⇒ 縮成 5.0 × 6.8 m 放進 8 × 12 的地塊）：山牆朝街、門與唯一一扇窗開在山牆。"""
    M = Model((80, D, 66))
    X0, Y0, X1, Y1 = 15, 20, 65, 88
    R, t, sl, ze, p = (X0, Y0, X1, Y1), 3, 2, 22, 1.25                   # 牆頂 2.2 m；坡 1.25（簷口垂到離地約 0.6 m）
    rubble_walls(M, R, 0, sl, t + 1)
    M.box('body', X0, Y0, 0, X1, Y1, 1, EARTH_W)                         # 泥地
    daub_walls(M, R, sl, ze, t)
    gable_wall(M, X0, X1, Y0, Y0 + t, ze, p, color=LIME, daub=True)
    gable_wall(M, X0, X1, Y1 - t, Y1, ze, p, color=LIME, daub=True)
    put_part(M, 'door-plank', '前-門', 'front', R, 30, sl, t)
    put_part(M, 'window-board', '前-窗', 'front', R, 52, 9, t)
    M.box('body', 23, Y0 - 3, 0, 37, Y0, sl, RUBBLE)                    # 門前一塊石階
    M.anchor('door', 30, Y0 - 1, sl)
    thatch_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ze, 'p': p, 'over': (13, 13, 5, 5), 'gable': 'y'}], salt=3)
    # 後院：木柵、燻肉架、養豬養雞的披屋（茅草）
    yb = D - 3
    palisade(M, [(X0, Y1), (3, Y1), (3, yb), (77, yb), (77, Y1), (X1 - 1, Y1)], h=14, gap={(x, yb) for x in range(8, 18)})
    if D < 120:                                                        # 淺版：院子 0.9 m（屋身到 y 88、後柵 y 97）⇒ 披屋、燻肉架、酒桶放不下
        M.anchor('lot-0', 0, 0, 0)
        return {'key': 'house-b-s', 'title': '住宅 B 淺版（地塊 8 × %d：同 B 的小屋；院子只剩木柵）' % (D // 10), 'use': 'house', 'lot': (8, D // 10), 'M': M,
                'layers': {'body': '牆身', 'roof': '屋頂'}}
    lean_roof_posts(M, 48, 98, 76, 116, 22, 0.3, 'front', thatch_color, [(50, 100), (72, 100), (50, 112), (72, 112)], salt=4)
    palisade(M, [(50, 100), (50, 112)], h=8)
    M.models += [{'name': '燻肉架', 'source': 'summit-rocher-01m-boucan', 'at': [24, 102, 0], 'pivot': [16, 10, 0], 'meta': {}},
                 {'name': '酒桶-棚', 'source': 'summit-rocher-01m-barrel', 'at': [64, 106, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-b', 'title': '住宅 B（編條糊泥的小屋：叉柱入土、石灰白牆、兩坡棕櫚葉頂垂到近地、門與窗在朝街的山牆；後院木柵＋燻肉架 boucan＋披屋）', 'use': 'house', 'lot': (8, 12), 'M': M,
            'layers': {'body': '牆身', 'roof': '屋頂'}}


def house_c(D=120):
    M = Model((80, D, 96))
    X0, Y0, X1, Y1 = 8, 28, 74, 74
    R, t = (X0, Y0, X1, Y1), 4
    z1, fl2, z2 = 30, 32, 58                                            # 一樓牆頂、二樓地板頂、二樓牆頂
    GY0 = 13
    rubble_walls(M, R, 0, z1, t, salt=7)
    M.box('body', X0, Y0, z1, X1, Y1, fl2, FLOOR)
    board_walls(M, (X0, Y0, X1, Y1), fl2, z2, 2)
    put_part(M, 'cartdoor', '前-貨門', 'front', R, 41, 0, t)
    put_part(M, 'vent', '前-氣窗1', 'front', R, 18, 12, t)
    put_part(M, 'vent', '前-氣窗2', 'front', R, 64, 12, t)
    put_part(M, 'door-plank', '二樓-門', 'front', R, 41, fl2, 2)
    for i, cx in enumerate((20, 62)):
        put_part(M, 'window-board', '二樓-前窗%d' % (i + 1), 'front', R, cx, fl2 + 9, 2)
    for i, cx in enumerate((24, 58)):
        put_part(M, 'window-board', '二樓-後窗%d' % (i + 1), 'back', R, cx, fl2 + 9, 2)
    put_part(M, 'door-plank', '後-門', 'back', R, 40, 0, t)
    put_part(M, 'vent', '右-氣窗', 'right', R, 52, 12, t)
    put_part(M, 'window-board', '右-二樓窗', 'right', R, 52, fl2 + 9, 2)
    M.anchor('door', 41, Y0 - 1, 0)
    # 二樓前廊（x 2..78，柱從地面立到屋頂）＋左側外樓梯（從後往前爬到廊的左端）
    M.box('gallery', 2, GY0, z1, 78, Y0, fl2, FLOOR)
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': z2, 'p': 0.85, 'over': (6, 6, 17, 4), 'kick': {'front': 0.4}}], salt=5)
    for px in (2, 27, 52, 76):
        zt = min(top[(x, y)] - 1 for x in range(px, px + 2) for y in range(GY0, GY0 + 2))
        M.box('gallery', px, GY0, 0, px + 2, GY0 + 2, zt, FRAME)
    rail(M, 4, 76, GY0, fl2)
    rail(M, GY0 + 2, Y0, 77, fl2, axis='y')
    sx0, sx1 = 2, 7                                                     # 樓梯：每級高 2、深 3，15 級 ⇒ 從 y 73 爬到 y 28
    for k in range(15):                                                 # 每級厚 4（跟下一級疊 2 層 ⇒ 一級接一級連成一塊）
        zt = 2 * (k + 1)
        ya = 73 - 3 * (k + 1)
        M.box('gallery', sx0, ya, max(0, zt - 4), sx1, ya + 3, zt, FLOOR)
    M.box('gallery', sx0, Y0 - 2, 0, sx0 + 1, 74, 2, FRAME)               # 樓梯底下的斜梁落地那一頭（撐住第一級）
    for k in range(0, 15, 3):
        ya = 73 - 3 * (k + 1)
        M.box('gallery', sx0, ya, 0, sx0 + 1, ya + 1, 2 * (k + 1) - 2, FRAME)
    # 後院：毛石院牆（後面一扇門）、木板廚房（單坡木瓦頂）
    ye = D - 1                                                          # 院牆後緣（原本 119）
    for (a, b, c, d) in ((X0, Y1, X0 + 3, ye), (X1 - 3, Y1, X1, ye), (X0, ye - 3, X1, ye)):
        rubble(M, (a, b, c, d), 0, 18, 4, 'body', base=RUBBLE, mortar=MORTAR, course=5, block=7, salt=8, dark=RUBBLE_D)
    M.clear(30, ye - 3, 0, 42, ye, 18, 'body')
    for z in range(0, 16):
        for x in range(30, 42):
            M.put('body', x, ye - 2, z, SHUT if (x - 30) % 3 else FRAME)
    if D < 120:                                                         # 淺版：院子 2.2 m（屋身到 y 74、院牆 y 96..99）⇒ 木板廚房放不下
        M.models += [{'name': '燈籠-貨門', 'source': 'summit-rocher-01m-lantern', 'at': [24.5, Y0, 22.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                     {'name': '貨箱-門口1', 'source': 'summit-rocher-01m-crate', 'at': [58, 20, 0], 'pivot': [6, 6, 0], 'meta': {}},
                     {'name': '酒桶-門口', 'source': 'summit-rocher-01m-barrel', 'at': [66, 20, 0], 'pivot': [6, 6, 0], 'meta': {}}]
        M.anchor('lot-0', 0, 0, 0)
        return {'key': 'house-c-s', 'title': '住宅 C 淺版（地塊 8 × %d：同 C 的商家；院子只剩石牆，沒有木板廚房）' % (D // 10), 'use': 'house', 'lot': (8, D // 10), 'M': M,
                'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}}
    kr = (48, 88, X1 - 3, 113)
    board_walls(M, kr, 0, 40, 2)
    put_part(M, 'door-plank', '廚房-門', 'left', kr, 100, 0, 2)
    ktop = lean_roof_posts(M, 46, 86, X1 - 1, 115, 38, 0.25, 'left', shingle_color, [], salt=6)
    for k in [k for k, v in M.cells.items() if v[0] == 'body' and kr[0] <= k[0] < kr[2] and kr[1] <= k[1] < kr[3] and k[2] >= ktop[(k[0], k[1])] - 1]:
        del M.cells[k]                                                  # 牆頂照屋面切（屋面底下那一層就是牆頂）
    M.models += [{'name': '燈籠-貨門', 'source': 'summit-rocher-01m-lantern', 'at': [24.5, Y0, 22.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '貨箱-門口1', 'source': 'summit-rocher-01m-crate', 'at': [58, 20, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-門口', 'source': 'summit-rocher-01m-barrel', 'at': [66, 20, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-c', 'title': '住宅 C（兩層的商家：一樓毛石店面＋貨門、二樓木板牆＋前廊、側面外樓梯、木瓦四坡頂；後院石牆＋木板廚房）', 'use': 'house', 'lot': (8, 12), 'M': M,
            'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}}


def house_a_s():
    return house_a(100)


def house_b_s():
    return house_b(100)


def house_c_s():
    return house_c(100)


ALL = [house_a, house_b, house_c, house_a_s, house_b_s, house_c_s]
