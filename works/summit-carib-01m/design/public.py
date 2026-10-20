# 公共建築（TASK-0757）：酒館、倉庫、小教堂、長官的屋子、砲台 —— 地塊照生成器 world/town.js 的 PUB 表。
# 座標同 houses.py（x 臨路寬、y 進深、y 0 臨路；0.1 m／格）。史料見作品 references/README.md。
from carib import *
from houses import put_part, free_part, lean_roof_posts, hearth

GUN = 'summit-stormkaap-01m-gun-6l'          # 風暴角號 6 磅長砲（0.05 m；砲口朝 +y、框 17 × 55 × 19）
GUN_PIVOT = [8.5, 27.5, 0]


def flagpole(M, x, y, z_top, layer='body'):
    """旗杆（2 × 2、頂上一顆圓頭）。回傳布旗的綁邊（旗杆 +x 那一格的空氣，上、下）。"""
    M.box(layer, x, y, 0, x + 2, y + 2, z_top, FRAME)
    M.box(layer, x - 1, y - 1, 0, x + 3, y + 3, 3, RUBBLE)              # 杆腳的石座
    M.box(layer, x, y, z_top, x + 2, y + 2, z_top + 2, GOLD)
    return (x + 2, y, z_top - 2), (x + 2, y, z_top - 20)


def flag_sail(name, top, bottom, fly, toward=1):
    """白旗（布，遊戲照風飄；BUILDING_SPEC §6.2）：綁邊 top→bottom、尾端往 x 方向 toward 伸 fly 格。"""
    tx = top[0] + toward * fly
    return {'name': name, 'corners': 'flag-top|flag-bottom|%d,%d,%d|%d,%d,%d' % (tx, bottom[1], bottom[2], tx, top[1], top[2]),
            'bind': '0', 'free': '2,3', 'color': 255, 'meta': {'kind': 'flag', 'flag': 'ensign', 'pattern': 'white'}}


# ─────────────────────────────── 酒館 10 × 14 m ───────────────────────────────
def tavern():
    M = Model((100, 140, 72))
    X0, Y0, X1, Y1 = 6, 36, 94, 100
    R, t, fl = (X0, Y0, X1, Y1), 2, 4
    GY0 = 14
    rubble_walls(M, R, 0, fl, 4, salt=11)
    M.box('body', X0, Y0, fl - 1, X1, Y1, fl, FLOOR)
    board_walls(M, R, fl, 34, t)
    piers(M, (X0, GY0, X1, Y0), fl - 1, step=20)
    M.box('gallery', X0, GY0, fl - 1, X1, Y0, fl, FLOOR)
    put_part(M, 'door-double', '前-門', 'front', R, 50, fl, t)
    for i, cx in enumerate((22, 78)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, fl + 9, t)
    for face, nm in (('left', '左'), ('right', '右')):
        for i, cy in enumerate((56, 82)):
            put_part(M, 'window-board', '%s-窗%d' % (nm, i + 1), face, R, cy, fl + 9, t)
    put_part(M, 'door-plank', '後-門', 'back', R, 30, fl, t)
    put_part(M, 'window-board', '後-窗', 'back', R, 70, fl + 9, t)
    steps(M, 40, 60, GY0, 1, 2, 4, back=False)
    M.anchor('door', 50, Y0 - 1, fl)
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 34, 'p': 0.9, 'over': (4, 4, 24, 4), 'kick': {'front': 0.42}}], salt=12)
    gallery_posts(M, (X0, 30, 68, X1 - 2), GY0, fl, top)
    for (a, b) in ((10, 42), (58, 90)):                                # 廊下沿牆的長凳（板＋兩端的腳）
        M.box('gallery', a, Y0 - 4, fl + 4, b, Y0 - 1, fl + 5, FLOOR)
        for x in (a, b - 2):
            M.box('gallery', x, Y0 - 4, fl, x + 2, Y0 - 1, fl + 4, FRAME)
    # 招牌：右前角一根柱、橫臂、吊著的一塊板
    M.box('body', 95, 10, 0, 97, 12, 42, FRAME)
    M.box('body', 82, 10, 40, 97, 12, 42, FRAME)
    for x in (84, 93):
        M.box('body', x, 10, 36, x + 1, 11, 40, IRON)
    for x in range(83, 95):
        for z in range(26, 36):
            M.put('body', x, 10, z, FRAME if x in (83, 94) or z in (26, 35) else SHUT)
    for x in range(86, 92):                                            # 板上畫一只酒杯（深色）
        M.put('body', x, 10, 33, DARK)
    for z in range(29, 33):
        M.put('body', 88, 10, z, DARK)
        M.put('body', 89, 10, z, DARK)
    M.box('body', 86, 10, 28, 92, 11, 29, DARK)
    M.anchor('sign', 88, 10, 30)
    # 後院：木柵、茅草涼棚（桶當桌）
    palisade(M, [(X0, Y1), (2, Y1), (2, 138), (98, 138), (98, Y1), (X1 - 1, Y1)], gap={(x, 138) for x in range(12, 24)})
    lean_roof_posts(M, 40, 104, 96, 134, 32, 0.25, 'back', thatch_color, [(42, 106), (68, 106), (93, 106), (42, 130), (68, 130), (93, 130)], salt=13)
    M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [36.5, Y0, 24.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '酒桶-廊1', 'source': 'summit-rocher-01m-barrel', 'at': [14, 22, fl], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-廊2', 'source': 'summit-rocher-01m-barrel', 'at': [82, 22, fl], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-棚1', 'source': 'summit-rocher-01m-barrel', 'at': [55, 118, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-棚2', 'source': 'summit-rocher-01m-barrel', 'at': [80, 118, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-棚', 'source': 'summit-rocher-01m-crate', 'at': [66, 124, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'tavern', 'title': '酒館（cabaret／punch house：橫板牆、寬前廊與長凳、雙扇門、吊招牌、木瓦四坡頂；後院茅草涼棚）', 'use': 'tavern', 'lot': (10, 14), 'M': M,
            'layers': {'body': '牆身', 'gallery': '前廊', 'roof': '屋頂'}}


# ─────────────────────────────── 倉庫 12 × 16 m ───────────────────────────────
def warehouse():
    """邊疆的倉庫：木板圍牆＋essente 屋頂（Labat 1701 Caye Saint-Louis）；毛石地檻、叉柱每 2.6 m 一根、兩坡頂、貨門、閣樓門與吊貨梁。"""
    M = Model((120, 160, 80))
    X0, Y0, X1, Y1 = 8, 14, 112, 144
    R, ze, p, sl = (X0, Y0, X1, Y1), 36, 0.6, 4
    rubble_walls(M, R, 0, sl, 4, salt=21)
    board_walls(M, R, sl, ze, 2, bay=26)
    gable_wall(M, X0, X1, Y0, Y0 + 2, ze, p)
    gable_wall(M, X0, X1, Y1 - 2, Y1, ze, p)
    put_part(M, 'cartdoor', '前-貨門', 'front', R, 60, 0, 4)
    for i, cx in enumerate((20, 99)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, 14, 2)
    put_part(M, 'door-plank', '前-閣樓門', 'front', R, 60, ze + 1, 2)
    for face, nm in (('left', '左'), ('right', '右')):
        for i, cy in enumerate((27, 79, 131)):
            put_part(M, 'window-board', '%s-窗%d' % (nm, i + 1), face, R, cy, 16, 2)
    put_part(M, 'door-plank', '後-門', 'back', R, 60, 0, 4)
    M.anchor('door', 60, Y0 - 1, 0)
    shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ze, 'p': p, 'over': (5, 5, 4, 4), 'gable': 'y'}], salt=22)
    zr = int(math.floor(ze + p * (60 - X0)))                           # 吊貨梁：從山牆頂下面伸出去
    M.box('body', 59, Y0 - 9, zr - 6, 61, Y0 + 2, zr - 4, FRAME, force=True)
    M.box('body', 59, Y0 - 9, zr - 9, 60, Y0 - 8, zr - 6, IRON)
    M.anchor('hoist', 59, Y0 - 9, zr - 10)
    M.models += [{'name': '貨箱-門口1', 'source': 'summit-rocher-01m-crate', 'at': [30, 6, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-門口2', 'source': 'summit-rocher-01m-crate', 'at': [38, 6, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-門口3', 'source': 'summit-rocher-01m-crate', 'at': [34, 6, 6], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-門口1', 'source': 'summit-rocher-01m-barrel', 'at': [82, 6, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-門口2', 'source': 'summit-rocher-01m-barrel', 'at': [90, 6, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'warehouse', 'title': '倉庫（magasin：木板牆、毛石地檻、兩坡木瓦頂、貨門、閣樓門與吊貨梁）', 'use': 'warehouse', 'lot': (12, 16), 'M': M,
            'layers': {'body': '牆身', 'roof': '屋頂'}}


# ─────────────────────────────── 小教堂 16 × 28 m ───────────────────────────────
def church():
    """1660 年代法屬島上的教堂（Du Tertre 2:450）：離地 3–4 法尺以下是毛石牆、上面木構架、四周開敞透氣；
    聖所那一端（後面約 10 法尺）與正面釘板（Labat 1701 Cap 的堂區教堂）；沒有玻璃，正面與聖所兩側開欄杆窗（Rochefort）；
    單一中殿、長凳（男前女後）、祭壇與祭壇欄杆、後面披屋式的聖器室；墓地沒圍牆（Petite-Rivière）。屋脊上的木鐘架是設計（史料沒寫鐘怎麼掛）。"""
    M = Model((160, 280, 130))
    X0, Y0, X1, Y1 = 35, 50, 125, 238
    R, ze, p, sw, fl = (X0, Y0, X1, Y1), 40, 1.0, 11, 4                  # 簷 4.0 m、石牆頂 1.1 m、地板頂 0.4 m
    SY = Y1 - 32                                                       # 聖所：最後 3.2 m 釘板
    rubble_walls(M, R, 0, sw, 4, salt=31)
    M.box('body', X0 + 4, Y0 + 4, 0, X1 - 4, Y1 - 4, fl - 1, EARTH_W)
    M.box('body', X0 + 4, Y0 + 4, fl - 1, X1 - 4, Y1 - 4, fl, FLOOR)
    board_walls(M, (X0, Y0, X1, Y0 + 2), sw, ze, 2, posts=False)        # 正面釘板（整面）
    board_walls(M, (X0, SY, X1, Y1), sw, ze, 2, posts=False)            # 聖所三面釘板
    for y in list(range(Y0, SY, 26)) + [SY, Y1 - 2]:                    # 長牆上的柱（每 2.6 m）立到簷
        for x in (X0, X1 - 2):
            M.box('body', x, y, sw, x + 2, y + 2, ze, FRAME, force=True)
    for x in (X0, X1 - 2):                                             # 牆梁
        M.box('body', x, Y0, ze - 2, x + 2, Y1, ze, FRAME, force=True)
    gable_wall(M, X0, X1, Y0, Y0 + 2, ze, p)
    gable_wall(M, X0, X1, Y1 - 2, Y1, ze, p)
    put_part(M, 'door-double', '前-大門', 'front', R, 80, fl, 4)
    put_part(M, 'window-baluster', '前-窗1', 'front', R, 54, fl + 12, 4)
    put_part(M, 'window-baluster', '前-窗2', 'front', R, 106, fl + 12, 4)
    put_part(M, 'window-baluster', '前-山牆窗', 'front', R, 80, ze + 8, 2)
    for face in ('left', 'right'):
        put_part(M, 'window-baluster', '%s-聖所窗' % ('左' if face == 'left' else '右'), face, R, SY + 16, sw + 6, 2)
    steps(M, 66, 94, Y0, 2, 2, 3, back=False, layer='body', color=RUBBLE)
    M.anchor('door', 80, Y0 - 1, fl)
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ze, 'p': p, 'over': (6, 6, 5, 5), 'gable': 'y'}], salt=32)
    # 室內：長凳（中間留走道）、祭壇欄杆、祭壇
    for y in range(Y0 + 30, SY - 30, 14):
        for (a, b) in ((X0 + 8, 74), (86, X1 - 8)):
            M.box('body', a, y, fl + 4, b, y + 4, fl + 5, FLOOR)
            for x in (a + 1, b - 3):
                M.box('body', x, y + 1, fl, x + 2, y + 3, fl + 4, FRAME)
    for x in range(X0 + 6, X1 - 6):                                    # 祭壇欄杆（車製欄杆）
        if 76 <= x < 84:
            continue
        M.put('body', x, SY - 8, fl + 9, FRAME)
        if x % 2 == 0:
            for z in range(fl, fl + 9):
                M.put('body', x, SY - 8, z, FRAME)
    M.box('body', 68, SY + 8, fl, 92, SY + 18, fl + 10, LIME)          # 祭壇（刷白）＋台面
    M.box('body', 66, SY + 7, fl + 10, 94, SY + 19, fl + 11, FRAME)
    M.box('body', 79, SY + 12, fl + 11, 81, SY + 14, fl + 19, GOLD)    # 祭壇上的十字
    M.box('body', 76, SY + 12, fl + 15, 84, SY + 14, fl + 17, GOLD)
    # 屋脊上靠前的木鐘架（設計）：四根柱、小四坡頂、一口鐘（Tortuga 有過從 Maracaibo 搶來的鐘，Labat）、十字架
    bx0, bx1, by0, by1 = 73, 87, 62, 76
    zc = 98
    for (px, py) in ((bx0, by0), (bx1 - 2, by0), (bx0, by1 - 2), (bx1 - 2, by1 - 2)):
        zb = min(top[(x, y)] for x in range(px, px + 2) for y in range(py, py + 2))
        M.box('roof', px, py, zb - 1, px + 2, py + 2, zc, FRAME, force=True)
    M.box('roof', bx0, by0, zc - 2, bx1, by1, zc, FRAME, force=True)
    M.clear(bx0 + 2, by0 + 2, zc - 2, bx1 - 2, by1 - 2, zc, 'roof')
    F = roof_field([{'x0': bx0, 'y0': by0, 'x1': bx1, 'y1': by1, 'ze': zc, 'p': 0.9, 'over': (2, 2, 2, 2)}])
    btop = build_roof(M, F, 2, 'roof', color_fn=lambda x, y, f, r, e: shingle_color(x, y, f, r, e, 33))
    for z in range(zc - 9, zc - 2):
        r = 1 + (zc - 3 - z) // 2
        for x in range(80 - r - 1, 80 + r + 1):
            for y in range(69 - r - 1, 69 + r + 1):
                M.put('roof', x, y, z, BRONZE)
    M.box('roof', bx0, 68, zc - 3, bx1, 70, zc - 2, FRAME, force=True)
    M.anchor('bell', 80, 69, zc - 6)
    zt = max(btop.values())
    M.box('roof', 79, 68, zt + 1, 81, 70, zt + 14, FRAME)
    M.box('roof', 76, 68, zt + 9, 84, 70, zt + 11, FRAME)
    # 聖器室：祭壇後面的披屋（木板牆、單坡木瓦）
    sr = (62, Y1, 98, Y1 + 18)
    board_walls(M, sr, 0, 40, 2)
    put_part(M, 'door-plank', '聖器室-門', 'right', sr, Y1 + 9, 0, 2)
    stop = lean_roof_posts(M, 60, Y1 - 2, 100, Y1 + 20, 34, 0.35, 'back', shingle_color, [], salt=34)
    for k in [k for k, v in M.cells.items() if v[0] == 'body' and sr[0] <= k[0] < sr[2] and sr[1] <= k[1] < sr[3] and k[2] >= stop[(k[0], k[1])] - 1]:
        del M.cells[k]
    # 墓地（沒圍牆）：幾支木十字、土堆
    for (cx, cy) in ((44, 262), (60, 268), (110, 260), (124, 270), (142, 262), (30, 272), (96, 274)):
        M.box('body', cx - 2, cy - 3, 0, cx + 4, cy + 5, 1, EARTH_W)
        M.box('body', cx, cy, 1, cx + 2, cy + 1, 12, FRAME)
        M.box('body', cx - 2, cy, 8, cx + 4, cy + 1, 10, FRAME)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'church', 'title': '小教堂（毛石牆到 1.1 m、上面木構架開敞、正面與聖所釘板、欄杆窗、兩坡木瓦頂、屋脊木鐘架；長凳、祭壇；聖器室披屋；沒圍牆的墓地）', 'use': 'church', 'lot': (16, 28), 'M': M,
            'layers': {'body': '牆身', 'roof': '屋頂與鐘架'}}


# ─────────────────────────────── 長官的屋子 10 × 12 m ───────────────────────────────
def commandant():
    """小指揮官屋（Labat 1696 Fort Louis 的上尉住屋：叉柱入土、四周釘板、essente、一層四小間）＋外面一圈打入土的粗木樁柵欄
    （Du Tertre 1656 Grenada：木構架的大亭外 9–10 法尺圍柵）；毛石台基與台階、前門雙扇；旗杆與白旗是設計（史料沒寫旗杆）。"""
    M = Model((100, 120, 90))
    X0, Y0, X1, Y1 = 14, 40, 86, 96
    R, t, fl = (X0, Y0, X1, Y1), 2, 5
    rubble_walls(M, R, 0, fl - 1, 4, salt=41)
    M.box('body', X0 + 4, Y0 + 4, 0, X1 - 4, Y1 - 4, fl - 1, EARTH_W)
    M.box('body', X0, Y0, fl - 1, X1, Y1, fl, FLOOR)
    board_walls(M, R, fl, 35, t)
    for x in range(X0 + 2, X1 - 2):                                    # 內部隔成四間：十字兩道板牆
        M.box('body', x, 67, fl, x + 1, 69, 35, BOARD)
    for y in range(Y0 + 2, Y1 - 2):
        M.box('body', 49, y, fl, 51, y + 1, 35, BOARD)
    M.clear(46, 66, fl, 54, 70, fl + 21, 'body')                          # 中間留一個門洞
    put_part(M, 'door-double', '前-門', 'front', R, 50, fl, t)
    for i, cx in enumerate((28, 72)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, fl + 8, t)
        put_part(M, 'window-board', '後-窗%d' % (i + 1), 'back', R, cx, fl + 8, t)
    for face, nm in (('left', '左'), ('right', '右')):
        put_part(M, 'window-board', '%s-窗1' % nm, face, R, 54, fl + 8, t)
        put_part(M, 'window-board', '%s-窗2' % nm, face, R, 82, fl + 8, t)
    M.box('body', 42, Y0 - 3, 0, 58, Y0, fl, RUBBLE)                   # 兩級石階（頂齊門檻）
    M.box('body', 42, Y0 - 6, 0, 58, Y0 - 3, fl - 2, RUBBLE)
    M.anchor('door', 50, Y0 - 1, fl)
    shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 35, 'p': 0.9, 'over': (5, 5, 5, 5)}], salt=42)
    # 柵欄（離屋約 3 m；正面中間一道門）
    palisade(M, [(48, 4), (2, 4), (2, 117), (97, 117), (97, 4), (52, 4)], h=22)
    for x in (44, 55):                                                 # 門柱＋橫楣
        M.box('body', x, 3, 0, x + 2, 6, 26, FRAME)
    M.box('body', 44, 3, 26, 57, 6, 28, FRAME)
    # 旗杆（前院右邊）＋白旗（布）
    ft, fb = flagpole(M, 80, 16, 86)
    M.anchor('flag', 80, 16, 87)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 28, toward=-1)]
    # 後院：廚房披屋（灶＋吊鍋）
    hearth(M, 66, 104, 78, 112)
    lean_roof_posts(M, 58, 100, 92, 116, 30, 0.35, 'back', thatch_color, [(60, 102), (88, 102), (60, 112), (88, 112)], salt=43)
    M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [37.5, Y0, 20.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '酒桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [14, 108, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'commandant', 'title': '長官的屋子（毛石台基、釘板木屋一層四間、木瓦四坡頂；外圍一圈木樁柵欄與門；旗杆與白旗；後院廚房披屋）', 'use': 'commandant', 'lot': (10, 12), 'M': M,
            'layers': {'body': '牆身', 'roof': '屋頂'}, 'flags': flags}


# ─────────────────────────────── 砲台 12 × 12 m ───────────────────────────────
def battery():
    """海岸砲台（Labat 1696 Fort Louis 的胸牆：兩排柵欄相隔 6 法尺、中間填土與柴捆、高 7–8 法尺；Du Tertre：平台＋圍牆＋砲眼）：
    正面（y 0，生成器讓它朝港口）胸牆厚 2.0 m、高 2.3 m，三個砲眼（舊法：兩頰用 gabion 圍），木砲床、三門 6 磅砲；
    左前角留一條進出的通道（生成器的路從正面接進來）；後面一間毛石小火藥庫；旗杆與白旗是設計。砲眼尺寸史料沒寫（設計）。"""
    M = Model((120, 120, 90))
    PY0, PY1, H = 4, 24, 23                                             # 胸牆 y 4..24（2.0 m）、高 2.3 m
    GX = 16                                                             # 左邊通道 x 2..16
    SILL = 12                                                           # 砲眼底（離砲床 0.8 m）
    PLAT = 4                                                            # 木砲床頂 0.4 m
    guns = (38, 66, 94)

    def rampart(x0, x1, y0, y1, h):
        """兩排柵欄夾土：外、裡兩面是一根挨一根的木樁（頂端參差），中間填土，頂上鋪一層土與草。"""
        for x in range(x0, x1):
            for y in range(y0, y1):
                face = y in (y0, y1 - 1) or x in (x0, x1 - 1)
                top = h + (1 if face and (x + y) % 2 == 0 else 0)
                for z in range(0, top):
                    if face:
                        c = FRAME if z in (6, h - 6) else BOARD
                    else:
                        c = (SOD if h01('sod', x, y) < 0.4 else EARTH_W) if z == h - 1 else EARTH_W
                    M.put('body', x, y, z, c)
    rampart(GX, 118, PY0, PY1, H)
    rampart(108, 118, PY1, 74, H - 4)
    rampart(2, 12, PY1 + 10, 74, H - 4)
    for cx in guns:                                                     # 砲眼：裡面寬 0.8 m、外面張開到 1.8 m；兩頰是 gabion（編條＋土）
        for y in range(PY0, PY1):
            half = 4 + (PY1 - 1 - y) * 5 // (PY1 - PY0)
            for x in range(cx - half, cx + half):
                for z in range(SILL, H + 2):
                    M.cells.pop((x, y, z), None)
            for x in (cx - half - 1, cx + half):
                for z in range(SILL, H):
                    if (x, y, z) in M.cells:
                        M.cells[(x, y, z)] = ('body', BOARD_D if z % 2 else FRAME)
    for cx in guns:                                                     # 砲床：木板平台
        for y in range(PY1, PY1 + 36):
            for x in range(cx - 12, cx + 12):
                for z in range(0, PLAT):
                    M.put('body', x, y, z, FLOOR if z == PLAT - 1 and (x - cx) % 6 else FRAME)
    for cx in guns:                                                     # 砲彈堆（鐵，3 層）
        bx, by = cx + 14, PY1 + 22
        for z, n in ((0, 3), (1, 2), (2, 1)):
            for i in range(n):
                for j in range(n):
                    M.box('body', bx + i * 2 + z, by + j * 2 + z, z, bx + i * 2 + z + 2, by + j * 2 + z + 2, z + 1, IRON)
    mr = (70, 84, 106, 112)                                            # 小火藥庫（砌石，Labat）
    rubble_walls(M, mr, 0, 28, 4, salt=51)
    put_part(M, 'door-plank', '火藥庫-門', 'front', mr, 88, 0, 4)
    shingle_roof(M, [{'x0': mr[0], 'y0': mr[1], 'x1': mr[2], 'y1': mr[3], 'ze': 28, 'p': 0.7, 'over': (3, 3, 3, 3)}], salt=52)
    ft, fb = flagpole(M, 20, 96, 80)
    M.anchor('flag', 20, 96, 81)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 28, toward=1)]
    M.anchor('door', 9, 1, 0)
    for i, cx in enumerate(guns):
        M.models.append({'name': '砲%d' % (i + 1), 'source': GUN, 'at': [cx, PY1 + 15, PLAT], 'pivot': GUN_PIVOT, 'rotate': [0, 0, 180], 'meta': {'kind': 'deco'}})
    M.models += [{'name': '火藥桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [60, 104, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '火藥桶-2', 'source': 'summit-rocher-01m-barrel', 'at': [62, 96, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'battery', 'title': '砲台（兩排木樁夾土的胸牆、三個砲眼與 gabion 頰、木砲床、三門 6 磅砲、毛石小火藥庫、旗杆與白旗）', 'use': 'battery', 'lot': (12, 12), 'M': M,
            'layers': {'body': '胸牆與砲床', 'roof': '屋頂'}, 'flags': flags}


ALL = [tavern, warehouse, church, commandant, battery]
