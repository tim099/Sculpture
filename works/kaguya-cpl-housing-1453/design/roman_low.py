# 羅馬（君士坦丁堡 1453）的低密度住宅（TASK-0893；Tim 2026-10-24「做吧，君堡的低密度住宅也換成 roman 版」）
#   以前 roman 底下沒有住宅 ⇒ 君堡的住宅地全退回 fr 的法式小屋。三型、三種地塊同 summit 的 fr、carib：
#     8 × 12（原本那一份）、8 × 10 淺版（-s，轉角）、8 × 8 小版（-xs，轉角只剩 2 格深）；屋子一樣、院子照地塊收（D ＝ 地塊進深，格）。
#   A 白灰泥：一樓方石夾磚、二樓木構夾灰泥挑出街面 0.5 m（四根木托架）、緩坡四坡頂；後院井欄、陶甕。
#   B 土黃：店屋 —— 一樓拱券店面＋門、二樓木構夾灰泥、山牆朝街的兩坡頂；後院葡萄架、陶甕。
#   C 鮭粉：一樓方石夾磚、二樓抹灰的磚石牆（磚帶、鋸齒簷）、二樓通長木陽台、四坡頂；後院灶間、井欄。二樓高 3.2 m（陽台門的卸力拱放得進簷下）。
#   人數同現有的低密度住宅：一棟 6 人（Blocksail GROW.live〔佔位〕）；大多數人住的房子住人的不超過兩層（common.py 的史料）⇒ 都是兩層。
# 層高：一樓 3.3 m（石基 0.3 m）、樓板 0.2 m、二樓 2.8 m。
from common import *
import roman_dense as RD
from roman_dense import put, slab, jetty_floor, steps, plinth, cornice, back_yard, kitchen, PL, T

UP = (38, 66)                     # 二樓的 [地板頂, 天花)
LOW_P = 0.35


def yard_or_alley(M, D, X0, X1, Y1, gate):
    """D ≥ 100 ⇒ 後院院牆（後牆在地塊後緣）＋後門；8 × 8 ⇒ 沒有院子（後門直接開到後巷）。"""
    if D >= 100:
        back_yard(M, X0, X1, Y1, D, gate=(gate, 12))


def pergola(M, x0, y0, x1, y1, h=24):
    """葡萄架：四根木柱、頂上一格一格的木條，葡萄葉一叢一叢（決定論的雜湊）。"""
    for (x, y) in ((x0, y0), (x0, y1 - 2), (x1 - 2, y0), (x1 - 2, y1 - 2)):
        M.box('body', x, y, 0, x + 2, y + 2, h, TIMBER)
    for x in range(x0, x1):
        for y in range(y0, y1):
            if (x - x0) % 5 == 0 or (y - y0) % 5 == 0 or x in (x0, x1 - 1) or y in (y0, y1 - 1):
                M.put('body', x, y, h, TIMBER)
            elif h01('vine', (x - x0) // 5, (y - y0) // 5, 0) < 0.6:          # 整格填滿（接著四邊的木條 ⇒ 不浮空）
                M.put('body', x, y, h, LEAF if h01('v2', x, y, 0) < 0.7 else GRASS_D)
    for (x, y) in ((x0, y0), (x1 - 2, y1 - 2)):                         # 兩根柱子爬著藤
        for z in range(4, h, 3):
            M.put('body', x - 1, y, z, LEAF)


def gable_ends(M, X0, X1, ys, ze, p, color):
    """兩坡頂（屋脊沿 y）前後兩面的山牆：三角形，木構框邊、灰泥填，中間一根中柱。ys ＝ 牆的 y 範圍們。"""
    for (ya, yb) in ys:
        for x in range(X0, X1):
            top = ze + p * min(x + 0.5 - X0, X1 - x - 0.5)
            for z in range(ze, int(math.floor(top))):
                c = TIMBER if (z == ze or z >= top - 1.5 or abs(x + 0.5 - (X0 + X1) / 2) < 1.1) else color
                for y in range(ya, yb):
                    M.put('body', x, y, z, c)


def house_a(D=120):
    M = Model((80, D, 90))
    M.plaster, M.shut = PLASTER, SHUT
    X0, Y0, X1, Y1 = 3, 12, 77, 72
    R, RJ = (X0, Y0, X1, Y1), (X0, Y0 - 5, X1, Y1)
    plinth(M, R)
    masonry(M, R, PL, 36, T, salt=51)
    jetty_floor(M, X0, X1, Y0 - 5, Y1, 36, 38)
    timber(M, RJ, UP[0], UP[1], T, panel=18, plaster=M.plaster)
    brackets(M, (X0, 26, 52, X1 - 2), Y0, Y0 - 5, 36)
    cornice(M, R, 34)
    put(M, 'door', '前-門', 'front', R, 40, PL)
    for i, cx in enumerate((15, 65)):
        put(M, 'window', '前-窗%d' % (i + 1), 'front', R, cx, PL + 9)
    for i, cx in enumerate((20, 60)):
        put(M, 'window', '二樓-窗%d' % (i + 1), 'front', RJ, cx, UP[0] + 8)
    steps(M, 40, Y0)
    M.anchor('door', 40, Y0 - 1, PL)
    put(M, 'door', '後-門', 'back', R, 40, PL)
    for i, cx in enumerate((20, 60)):
        put(M, 'window', '後-二樓窗%d' % (i + 1), 'back', RJ, cx, UP[0] + 8)
    F = roof_field([{'x0': X0, 'y0': Y0 - 5, 'x1': X1, 'y1': Y1, 'ze': UP[1], 'p': LOW_P, 'over': (3, 3, 4, 4)}])
    build_roof(M, F, salt=51)
    yard_or_alley(M, D, X0, X1, Y1, 56)
    if D >= 120:
        wellhead(M, 26, 96)
        for (cx, cy) in ((64, 98), (64, 106)):
            jar(M, cx, cy)
    elif D >= 100:
        jar(M, 64, 86)
    M.models += [model(LANTERN, '燈籠-門', (28.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return _ret(M, 'a', D, '住宅 A（一樓方石夾磚、二樓木構夾灰泥挑出街面、緩坡四坡頂%s；白灰泥、牛血紅門板）',
                ('、後院井欄、陶甕', '、院子只剩院牆與一只陶甕', '；沒有院子'), {'body': '牆身', 'roof': '屋頂'})


def house_b(D=120):
    M = Model((80, D, 90))
    M.plaster, M.shut = OCHRE, SH_GREEN
    X0, Y0, X1, Y1 = 3, 12, 77, 72
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    masonry(M, R, PL, 36, T, salt=61)
    slab(M, R, 36, 38)
    timber(M, R, 36, UP[1], T, panel=18, plaster=M.plaster)
    cornice(M, R, 34)
    gp = 0.4
    gable_ends(M, X0, X1, ((Y0, Y0 + T), (Y1 - T, Y1)), UP[1], gp, M.plaster)
    put(M, 'shop', '前-店面', 'front', R, 22, PL)
    put(M, 'door', '前-門', 'front', R, 58, PL)
    put(M, 'window2', '二樓-雙拱窗', 'front', R, 40, UP[0] + 6)
    steps(M, 58, Y0)
    M.anchor('door', 58, Y0 - 1, PL)
    put(M, 'door', '後-門', 'back', R, 40, PL)
    for i, cx in enumerate((18, 62)):
        put(M, 'window', '後-二樓窗%d' % (i + 1), 'back', R, cx, UP[0] + 8)
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': UP[1], 'p': gp, 'over': (3, 3, 4, 4), 'gable': 'y'}])
    build_roof(M, F, salt=61)
    yard_or_alley(M, D, X0, X1, Y1, 22)
    if D >= 120:
        pergola(M, 40, 80, 72, 110)
        for (cx, cy) in ((12, 86), (12, 94), (20, 86)):
            jar(M, cx, cy)
    elif D >= 100:
        for (cx, cy) in ((60, 86), (68, 86)):
            jar(M, cx, cy)
    M.models += [model(LANTERN, '燈籠-門', (46.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return _ret(M, 'b', D, '住宅 B（店屋：一樓拱券店面＋門、二樓木構夾灰泥、山牆朝街的兩坡頂%s；土黃灰泥、綠門板）',
                ('、後院葡萄架、陶甕', '、院子只剩院牆與陶甕', '；沒有院子'), {'body': '牆身', 'roof': '屋頂'})


def house_c(D=120):
    UP = (38, 70)                                                        # 二樓 3.2 m：陽台門＋卸力拱高 2.9 m，2.8 m 的二樓會頂到屋簷
    M = Model((80, D, 90))
    M.plaster, M.shut = SALMON, SH_BLUE
    X0, Y0, X1, Y1 = 3, 12, 77, 72
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    masonry(M, R, PL, 36, T, salt=71)
    slab(M, R, 36, 38)
    shell(M, R, 36, 38, T, lambda x, y, z: BRICK_R)                   # 樓層的一道磚帶
    shell(M, R, 38, UP[1], T, lambda x, y, z: M.plaster)              # 二樓抹灰
    cornice(M, R, UP[1] - 2)
    put(M, 'door', '前-門', 'front', R, 40, PL)
    for i, cx in enumerate((15, 65)):
        put(M, 'window', '前-窗%d' % (i + 1), 'front', R, cx, PL + 9)
    put(M, 'window2', '二樓-雙拱窗1', 'front', R, 16, UP[0] + 6)
    put(M, 'door', '二樓-陽台門', 'front', R, 40, UP[0])
    put(M, 'window2', '二樓-雙拱窗2', 'front', R, 64, UP[0] + 6)
    wood_balcony(M, 5, 75, 4, Y0, UP[0], posts=14)
    brackets(M, (5, 26, 52, 73), Y0, 4, UP[0] - 2, layer='gallery')
    steps(M, 40, Y0)
    M.anchor('door', 40, Y0 - 1, PL)
    put(M, 'door', '後-門', 'back', R, 40, PL)
    for i, cx in enumerate((18, 62)):
        put(M, 'window', '後-二樓窗%d' % (i + 1), 'back', R, cx, UP[0] + 8)
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': UP[1], 'p': LOW_P, 'over': (3, 3, 8, 4)}])
    build_roof(M, F, salt=71)
    yard_or_alley(M, D, X0, X1, Y1, 56)
    if D >= 120:
        kitchen(M, (6, 92, 34, 117), salt=72)
        wellhead(M, 56, 96)
    elif D >= 100:
        wellhead(M, 26, 86)
    M.models += [model(LANTERN, '燈籠-門', (28.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return _ret(M, 'c', D, '住宅 C（一樓方石夾磚、二樓抹灰的磚石牆、通長木陽台＋雙拱窗、四坡頂%s；鮭粉灰泥、藍門板）',
                ('、後院灶間、井欄', '、院子只剩院牆與井欄', '；沒有院子'), {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂'})


def _ret(M, t, D, title, yard_txt, layers):
    sfx, i, nm = ('', 0, '') if D >= 120 else ('-s', 1, ' 淺版') if D >= 100 else ('-xs', 2, ' 小版')
    head = title.split('（')[0]
    return {'key': 'house-%s%s' % (t, sfx), 'variant': t + sfx, 'level': 1, 'live': 6,
            'title': head + nm + '（地塊 8 × %d：' % (D // 10) + title.split('（', 1)[1] % yard_txt[i],
            'use': 'house', 'lot': (8, D // 10), 'M': M, 'layers': layers}


ALL = [lambda: house_a(120), lambda: house_b(120), lambda: house_c(120),
       lambda: house_a(100), lambda: house_b(100), lambda: house_c(100),
       lambda: house_a(80), lambda: house_b(80), lambda: house_c(80)]
# 配色變化（設計決定）：每一型換灰泥與門板，淺版、小版照同一套
RC = {'a': ({PLASTER: OCHRE, SHUT: SH_BLUE}, '土黃灰泥、藍門板'), 'b': ({OCHRE: PLASTER, SH_GREEN: SHUT}, '白灰泥、牛血紅門板'),
      'c': ({SALMON: PLASTER, SH_BLUE: SH_GREEN}, '白灰泥、綠門板')}
VARIANTS = [('house-%s2%s' % (t, s), 'house-%s%s' % (t, s), RC[t][0], '住宅 %s2%s（%s 的配色變化：%s；替換色，不另存格子）' % (t.upper(), nm, t.upper() + nm, RC[t][1]))
            for s, nm in (('', ''), ('-s', ' 淺版'), ('-xs', ' 小版')) for t in 'abc']
