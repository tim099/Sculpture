# 威尼斯 1666 的低密度住宅（gura-venice-housing-1666）—— 三型、三種地塊同 summit 的 fr、carib、kaguya 的 roman：
#   8 × 12（原本那一份）、8 × 10 淺版（-s，轉角）、8 × 8 小版（-xs，轉角只剩 2 格深）；屋子一樣、院子照地塊收（D ＝ 地塊進深，格）。
#   A 威尼斯紅：排屋（casa a schiera）—— 立面正中一根煙囪身從二樓爬上屋頂、兩側各一列窗（NTA 附錄的 A 型 g3 立面）：一樓石框門＋方窗、二樓兩扇哥德單窗；緩坡四坡筒瓦頂；後院井欄。
#   B 土黃：店屋 —— 一樓店面＋門、二樓方窗＋石陽台門、兩坡頂（屋脊順街）、屋頂木平台（altana）、屋面一根喇叭煙囪；後院晾衣桿、井欄。
#   C 粉：一樓 regalzier（紅灰泥畫白磚縫）、二樓抹灰伸出巷子 0.6 m 架在木托架（barbacani）上、兩扇哥德單窗、四坡頂、屋面喇叭煙囪；後院井欄。
#   人數同現有的低密度住宅：一棟 6 人（Blocksail GROW.live〔佔位〕）；兩層（低密度）。
# 層高同 venice_dense：一樓 3.3 m（石基 0.3 m）、樓板 0.2 m、二樓 3.0 m。
from common import *
from venice_dense import put, roof, front_chimney, roof_chimney, roof_altana, back_corte, PL, T, ROOF_P

UP = (38, 68)


def yard(M, D, X0, X1, Y1, gate):
    """D ≥ 100 ⇒ 後院院牆（後牆在地塊後緣）＋後門；8 × 8 ⇒ 沒有院子（後門直接開到後巷）。"""
    if D >= 100:
        back_corte(M, X0, X1, Y1, D, gate=(gate, 12))


def laundry(M, x0, x1, y, h=26):
    """晾衣繩：兩根木桿、一道繩、幾件晾著的布（灰泥色以外的布色）。"""
    for x in (x0, x1 - 1):
        M.box('body', x, y, 0, x + 1, y + 1, h, LEGNO)
    for x in range(x0, x1):
        M.put('body', x, y, h - 1, WOOD_D)
    for i, (a, b, c) in enumerate(((x0 + 3, x0 + 9, 255), (x0 + 12, x0 + 17, 42), (x0 + 20, x0 + 27, 218))):
        if b < x1 - 1:
            M.box('body', a, y, h - 9, b, y + 1, h - 1, c)


def house_a(D=120):
    M = Model((80, D, 112))
    M.plaster = ROSSO
    X0, Y0, X1, Y1 = 2, 12, 78, 72
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    plastered(M, R, PL, UP[1], T, M.plaster, salt=51)
    slab(M, R, 36, 38)
    stone_band(M, R, 36)
    dentils(M, R, UP[1] - 1)
    put(M, 'door', '前-門', 'front', R, 18, PL)
    put(M, 'windowq', '前-窗', 'front', R, 62, PL + 9)
    for i, cx in enumerate((17, 63)):
        put(M, 'window', '二樓-哥德窗%d' % (i + 1), 'front', R, cx, UP[0] + 6)
    steps(M, 18, Y0)
    M.anchor('door', 18, Y0 - 1, PL)
    front_chimney(M, 40, Y0, 98)
    put(M, 'door', '後-門', 'back', R, 40, PL)
    for i, cx in enumerate((20, 60)):
        put(M, 'windowq', '後-二樓窗%d' % (i + 1), 'back', R, cx, UP[0] + 8)
    roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': UP[1], 'p': ROOF_P, 'over': (2, 2, 4, 4)}], salt=51)
    yard(M, D, X0, X1, Y1, 56)
    if D >= 120:
        vera(M, 30, 96)
    elif D >= 100:
        laundry(M, 8, 40, 88)
    M.models += [model(LANTERN, '燈籠-門', (6.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return _ret(M, 'a', D, '住宅 A（排屋：立面正中一根煙囪、兩側一樓石框門與方窗、二樓兩扇哥德單窗、緩坡四坡筒瓦頂%s；威尼斯紅灰泥、綠窗板）',
                ('、後院井欄', '、院子只剩院牆與晾衣繩', '；沒有院子'), {'body': '牆身', 'roof': '屋頂'})


def house_b(D=120):
    UPB = (38, 72)                                                      # 二樓 3.4 m：陽台門＋通氣窗 3.0 m，3.0 m 的二樓會頂到屋簷
    M = Model((80, D, 116))
    M.plaster = OCRA
    X0, Y0, X1, Y1 = 2, 12, 78, 72
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    plastered(M, R, PL, UPB[1], T, M.plaster, salt=61)
    slab(M, R, 36, 38)
    stone_band(M, R, 36)
    dentils(M, R, UPB[1] - 1)
    put(M, 'shop', '前-店面', 'front', R, 20, PL)
    put(M, 'door', '前-門', 'front', R, 56, PL)
    steps(M, 56, Y0)
    M.anchor('door', 56, Y0 - 1, PL)
    put(M, 'windowq', '二樓-窗', 'front', R, 18, UPB[0] + 7)
    put(M, 'door', '二樓-陽台門', 'front', R, 54, UPB[0])
    poggiolo(M, 42, 67, Y0, 5, UPB[0])
    put(M, 'door', '後-門', 'back', R, 40, PL)
    for i, cx in enumerate((20, 60)):
        put(M, 'windowq', '後-二樓窗%d' % (i + 1), 'back', R, cx, UPB[0] + 8)
    top = roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': UPB[1], 'p': 0.36, 'over': (2, 2, 4, 4), 'gable': 'x'}], salt=61)
    for xg in (X0, X1 - T):                                             # 兩頭的山牆（照屋面高補灰泥）
        for y in range(Y0, Y1):
            for z in range(UPB[1], top.get((xg + 1, y), UPB[1])):
                for x in range(xg, xg + T):
                    M.put('body', x, y, z, M.plaster)
    roof_altana(M, top, 8, 44, 48, 70)
    roof_chimney(M, top, 66, 30)
    yard(M, D, X0, X1, Y1, 22)
    if D >= 120:
        vera(M, 56, 98)
        laundry(M, 8, 36, 104)
    elif D >= 100:
        laundry(M, 40, 74, 88)
    M.models += [model(LANTERN, '燈籠-門', (44.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return _ret(M, 'b', D, '住宅 B（店屋：一樓店面＋門、二樓方窗＋石陽台門、屋脊順街的兩坡頂、屋頂木平台、喇叭煙囪%s；土黃灰泥、綠窗板）',
                ('、後院井欄與晾衣繩', '、院子只剩院牆與晾衣繩', '；沒有院子'), {'body': '牆身', 'gallery': '陽台與屋頂平台', 'roof': '屋頂'})


def house_c(D=120):
    M = Model((80, D, 112))
    M.plaster = ROSA
    X0, Y0, X1, Y1 = 2, 12, 78, 72
    R, RJ = (X0, Y0, X1, Y1), (X0, Y0 - 6, X1, Y1)
    plinth(M, R)
    regal_wall(M, R, PL, 36, T)
    stone_band(M, R, 34, 36)
    jetty_floor(M, X0, X1, Y0 - 6, Y1, 36, 38)
    plastered(M, RJ, 38, UP[1], T, M.plaster, salt=71)
    barbacani(M, (X0 + 1, 20, 38, 56, X1 - 3), Y0, Y0 - 6, 36)
    dentils(M, RJ, UP[1] - 1)
    put(M, 'door', '前-門', 'front', R, 40, PL)
    put(M, 'windowq', '前-窗', 'front', R, 16, PL + 9)
    put(M, 'windowq', '前-窗2', 'front', R, 64, PL + 9)
    for i, cx in enumerate((18, 62)):
        put(M, 'window', '二樓-哥德窗%d' % (i + 1), 'front', RJ, cx, UP[0] + 6)
    steps(M, 40, Y0)
    M.anchor('door', 40, Y0 - 1, PL)
    put(M, 'door', '後-門', 'back', R, 40, PL)
    for i, cx in enumerate((20, 60)):
        put(M, 'windowq', '後-二樓窗%d' % (i + 1), 'back', R, cx, UP[0] + 8)
    top = roof(M, [{'x0': X0, 'y0': Y0 - 6, 'x1': X1, 'y1': Y1, 'ze': UP[1], 'p': ROOF_P, 'over': (2, 2, 2, 4)}], salt=71)
    roof_chimney(M, top, 60, 58)
    yard(M, D, X0, X1, Y1, 56)
    if D >= 120:
        vera(M, 24, 96)
    elif D >= 100:
        vera(M, 24, 86)
    M.models += [model(LANTERN, '燈籠-門', (28.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return _ret(M, 'c', D, '住宅 C（一樓紅灰泥畫白磚縫（regalzier）、二樓抹灰伸出巷子 0.6 m 架在木托架上、兩扇哥德單窗、四坡頂、喇叭煙囪%s；粉灰泥、綠窗板）',
                ('、後院井欄', '、院子只剩院牆與井欄', '；沒有院子'), {'body': '牆身', 'roof': '屋頂'})


def _ret(M, t, D, title, yard_txt, layers):
    sfx, i, nm = ('', 0, '') if D >= 120 else ('-s', 1, ' 淺版') if D >= 100 else ('-xs', 2, ' 小版')
    head = title.split('（')[0]
    return {'key': 'house-%s%s' % (t, sfx), 'variant': t + sfx, 'level': 1, 'live': 6,
            'title': head + nm + '（地塊 8 × %d：' % (D // 10) + title.split('（', 1)[1] % yard_txt[i],
            'use': 'house', 'lot': (8, D // 10), 'M': M, 'layers': layers}


ALL = [lambda: house_a(120), lambda: house_b(120), lambda: house_c(120),
       lambda: house_a(100), lambda: house_b(100), lambda: house_c(100),
       lambda: house_a(80), lambda: house_b(80), lambda: house_c(80)]
# 配色變化（設計決定）：每一型換灰泥與窗板，淺版、小版照同一套
RC = {'a': ({ROSSO: ROSA, SCURI: PORTA}, '粉灰泥、深褐窗板'), 'b': ({OCRA: CREMA, SCURI: SH_GREY}, '米白灰泥、灰藍窗板'),
      'c': ({ROSA: OCRA, SCURI: PORTA}, '土黃灰泥、深褐窗板')}
VARIANTS = [('house-%s2%s' % (t, s), 'house-%s%s' % (t, s), RC[t][0], '住宅 %s2%s（%s 的配色變化：%s；替換色，不另存格子）' % (t.upper(), nm, t.upper() + nm, RC[t][1]))
            for s, nm in (('', ''), ('-s', ' 淺版'), ('-xs', ' 小版')) for t in 'abc']
