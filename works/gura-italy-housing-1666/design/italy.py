# 義大利 1666 的通用城市住宅（gura-italy-housing-1666）—— 低、中、高、超高四級（佔地同 Blocksail ZONE.fp；人數〔設計〕同 venice、crest 那幾套）
#   低（8 × 12、淺版 8 × 10、小版 8 × 8）：
#     A 托斯卡納的連棟小屋（case a schiera）：一樓小門＋拱頂店鋪、二樓兩扇石框方窗、窗台那一道石線、四坡筒瓦頂＋深木屋簷；黃赭灰泥
#     B 利古里亞的窄樓：三層、一樓拱頂店鋪＋黑石板門框、樓上畫白框的窄窗、白色樓層線、深色基座帶、順街的兩坡石板頂；粉灰泥
#     C 里窩那／托斯卡納：二樓三扇石框方窗、一樓大門夾兩扇窗、後半截加一層開敞的木欄杆涼廊（altana）；紅赭灰泥
#   中：M-B 8 × 12 三層的店屋（拱頂店鋪＋小門、深木屋簷；橙赭）；M-A 12 × 12 三開間的小宅邸（palazzetto：大門、一樓兩扇跪窗、主樓層石線；石灰白）
#   高：H-B 12 × 12 熱那亞的五層樓（兩間拱頂店鋪夾黑石板大門、畫框窄窗、石板頂；淡綠）；
#       H-A 16 × 16 佛羅倫斯的院子宅邸（一樓 pietra forte 粗面石＋四扇跪窗、兩層石框窗、頂樓開敞涼廊、深木屋簷；右側翼圍出院子、井；黃赭）
#   超高（第 4 級，Blocksail TASK-1291）：熱那亞 caruggi 兩旁的高樓 —— 一個地塊拆成 1～4 個 4.5～6 m 寬的開間（照 tavola 那種窄而深的產權），
#       各自一色、5～7 層、屋頂高低差一層；一樓一排拱頂店鋪、窄的住家門；樓上畫白框的窄窗、白色樓層線；石板頂。⛔ 不超過 7 層（1666 年還沒有 18～19 世紀的加蓋）。
# 層高（史料建議值，見 ../notes.md）：低、中、高 一樓 3.7 m（石基 0.3 m）、樓上每層 3.2 m（含 0.2 m 樓板）；超高 一樓 3.9 m、樓上每層 3.0 m。
from icommon import *
import iparts

ROOT = 'gura-italy-housing-1666'
STYLE = 'italy'
PL, T = 3, 3
PARTS = {pid: dict(P, work=ROOT + '-part-' + pid) for pid, P in iparts.all_parts().items()}


def floors(n, g=40, story=32):
    """n 層 ⇒ [(地板頂, 天花)…]（第 0 層是一樓）、屋簷 ze（最上面那一層的天花再高 0.6 m：頂樓窗頂上留一段牆給屋簷、木椽）。"""
    F = [(PL, g)]
    for i in range(1, n):
        z0 = g + 2 + story * (i - 1)
        F.append((z0, z0 + story - 2))
    return F, F[-1][1] + 6


def put(M, pid, name, face, rect, center, z):
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
    place(M, P, name, face, rect, u, z, T)
    M.links[-1]['part'] = P['work']


def paint_frame(M, R, cx, z0, face='front', w=4, top=21):
    """利古里亞畫上去的白窗框（finestral 的開口 cx − 3 ～ cx + 4、z0 ＋ 2 ～ z0 ＋ 20）：開口外 2 格一圈、頂上加厚成一道畫的小簷。"""
    X0, Y0, X1, Y1 = R
    y = Y0 if face == 'front' else Y1 - 1
    sx = 1 if face == 'front' else -1
    for x in range(cx - 3 - 2, cx + 5 + 2):
        xx = x if face == 'front' else (X0 + X1 - 1 - x)
        for z in range(z0, z0 + top + 3):
            c = M.cells.get((xx, y, z))
            if c and c[1] == M.plaster:
                M.cells[(xx, y, z)] = (c[0], BIANCO)


def paint_bands(M, R, F, faces=('front', 'back')):
    """利古里亞畫上去的白色樓層線（每一層樓板那裡 0.2 m）＋深色基座帶（一樓下段 1.1 m）。"""
    for (z0, z1) in F[1:]:
        surface(M, R, z0 - 2, z0, BIANCO, (M.plaster,), faces)
    surface(M, R, PL, PL + 11, ZOCCOLO, (M.plaster,), faces)


def hip(M, R, ze, p=0.33, over=(2, 2, 8, 8), salt=0, deep=True):
    """托斯卡納的屋頂：四坡筒瓦（筒瓦＋平瓦）＋深木屋簷（gronda）。回傳屋面高。"""
    X0, Y0, X1, Y1 = R
    top = build_roof(M, roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ze, 'p': p, 'over': over}]), salt=salt)
    if deep:
        gronda(M, top, X0, X1, Y0, Y0 - over[2], side='front')
        gronda(M, top, X0, X1, Y1, Y1 + over[3], side='back')
    return top


def slate(M, rects, colors=None):
    """利古里亞的屋頂：順街的兩坡石板（rects 照 roof_field，自帶 gable 'x'）＋兩頭的山牆照屋面高補灰泥（colors：每一塊的牆色，沒給 ⇒ M.plaster）。"""
    top = build_roof(M, roof_field([dict(r, gable='x') for r in rects]), color_fn=slate_color)
    for i, r in enumerate(rects):
        col = colors[i] if colors else M.plaster
        for xg in (r['x0'], r['x1'] - T):
            for y in range(r['y0'], r['y1']):
                for z in range(r['ze'], top.get((xg + 1, y), r['ze']) - 1):
                    for x in range(xg, xg + T):
                        M.put('body', x, y, z, col)
    return top


def yard(M, D, X0, X1, Y1, gate, color=CALCE):
    if D >= 100:
        back_corte(M, X0, X1, Y1, D, gate=(gate, 12), color=color)


def done(M, key, variant, level, live, lot, title, layers=None):
    M.anchor('lot-0', 0, 0, 0)
    return {'key': key, 'variant': variant, 'level': level, 'live': live, 'title': title, 'use': 'house', 'lot': lot, 'M': M,
            'layers': layers or {'body': '牆身', 'roof': '屋頂'}}


def lantern(M, cx, Y0):
    M.models += [model(LANTERN, '燈籠-門', (cx - 11.5, Y0, 26.5))]


# ─────────────────────────────── 低密度 ───────────────────────────────
def low_tag(D):
    return ('', '') if D >= 120 else ('-s', ' 淺版') if D >= 100 else ('-xs', ' 小版')


def house_a(D=120):
    F, ze = floors(2)
    M = Model((80, D, 130))
    M.plaster = GIALLO
    X0, Y0, X1, Y1 = 2, 12, 78, 72
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    wall(M, R, PL, ze, T, M.plaster)
    slab(M, R, F[1][0] - 2, F[1][0])
    put(M, 'porta', '前-門', 'front', R, 16, PL)
    put(M, 'volta', '前-店鋪', 'front', R, 52, PL)
    steps(M, 16, Y0, w=14)
    M.anchor('door', 16, Y0 - 1, PL)
    band(M, R, F[1][0] + 7, F[1][0] + 8, SERENA, faces=('front',))
    for i, cx in enumerate((22, 58)):
        put(M, 'finestra', '二樓-窗%d' % (i + 1), 'front', R, cx, F[1][0] + 8)
    put(M, 'porta', '後-門', 'back', R, 40, PL)
    for i, cx in enumerate((20, 60)):
        put(M, 'finestra', '後-二樓窗%d' % (i + 1), 'back', R, cx, F[1][0] + 8)
    top = hip(M, R, ze, salt=201)
    chimney(M, top, 62, 56)
    yard(M, D, X0, X1, Y1, 56)
    if D >= 120:
        pozzo(M, 28, 98)
    elif D >= 100:
        laundry(M, 8, 40, 88)
    lantern(M, 16, Y0)
    s, nm = low_tag(D)
    return done(M, 'house-a' + s, 'a' + s, 1, 6, (8, D // 10),
                '住宅 A%s（地塊 8 × %d：托斯卡納的連棟小屋 —— 一樓小門＋拱頂店鋪、二樓兩扇 pietra serena 石框方窗、窗台石線、四坡筒瓦頂＋深木屋簷%s；黃赭灰泥、綠窗板）'
                % (nm, D // 10, '、後院井' if D >= 120 else '、院子只剩院牆與晾衣繩' if D >= 100 else '；沒有院子'))


def house_b(D=120):
    F, ze = floors(3)
    M = Model((80, D, 160))
    M.plaster = ROSA
    X0, Y0, X1, Y1 = 2, 12, 78, 72
    R = (X0, Y0, X1, Y1)
    plinth(M, R, color=ARDESIA)
    wall(M, R, PL, ze, T, M.plaster)
    for (z0, z1) in F[1:]:
        slab(M, R, z0 - 2, z0)
    put(M, 'volta', '前-店鋪', 'front', R, 24, PL)
    put(M, 'portale', '前-門', 'front', R, 60, PL)
    steps(M, 60, Y0, color=ARDESIA)
    M.anchor('door', 60, Y0 - 1, PL)
    for f in (1, 2):
        for i, cx in enumerate((22, 58)):
            put(M, 'finestral', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, F[f][0] + 6)
            paint_frame(M, R, cx, F[f][0] + 6)
    put(M, 'porta', '後-門', 'back', R, 40, PL)
    for f in (1, 2):
        for i, cx in enumerate((22, 58)):
            put(M, 'finestral', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, F[f][0] + 6)
    paint_bands(M, R, F)
    top = slate(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ze, 'p': 0.4, 'over': (2, 2, 3, 3)}])
    chimney(M, top, 60, 60, cap='slate')
    yard(M, D, X0, X1, Y1, 22, color=M.plaster)
    if D >= 120:
        pozzo(M, 54, 98)
        laundry(M, 8, 36, 104)
    elif D >= 100:
        laundry(M, 40, 74, 88)
    lantern(M, 60, Y0)
    s, nm = low_tag(D)
    return done(M, 'house-b' + s, 'b' + s, 1, 6, (8, D // 10),
                '住宅 B%s（地塊 8 × %d：利古里亞的三層窄樓 —— 一樓拱頂店鋪＋黑石板門框、樓上畫白框的窄窗、白色樓層線、深色基座帶、順街的兩坡石板頂%s；粉灰泥、綠窗板）'
                % (nm, D // 10, '、後院井與晾衣繩' if D >= 120 else '、院子只剩院牆與晾衣繩' if D >= 100 else '；沒有院子'))


def house_c(D=120):
    F, ze = floors(2)
    M = Model((80, D, 150))
    M.plaster = ROSSO_O
    X0, Y0, X1, Y1 = 2, 12, 78, 72
    R = (X0, Y0, X1, Y1)
    LR = (X0, 44, X1, Y1)                                               # 後半截加的那一層涼廊
    plinth(M, R)
    wall(M, R, PL, ze, T, M.plaster)
    slab(M, R, F[1][0] - 2, F[1][0])
    put(M, 'portone', '前-門', 'front', R, 40, PL)
    for i, cx in enumerate((14, 66)):
        put(M, 'finestra', '前-一樓窗%d' % (i + 1), 'front', R, cx, PL + 12)
    steps(M, 40, Y0)
    M.anchor('door', 40, Y0 - 1, PL)
    band(M, R, F[1][0] + 7, F[1][0] + 8, SERENA, faces=('front',))
    for i, cx in enumerate((14, 40, 66)):
        put(M, 'finestra', '二樓-窗%d' % (i + 1), 'front', R, cx, F[1][0] + 8)
    put(M, 'porta', '後-門', 'back', R, 40, PL)
    for i, cx in enumerate((20, 60)):
        put(M, 'finestra', '後-二樓窗%d' % (i + 1), 'back', R, cx, F[1][0] + 8)
    zl = ze + 28                                                        # 涼廊：後半截加一層（左、右、後三面牆，朝街那一面開敞：石柱＋木欄杆）
    wall(M, LR, ze, zl, T, M.plaster)
    M.box('body', X0 + T, 44 + T, ze, X1 - T, Y1 - T, ze + 2, WOOD)
    M.clear(X0 + T, 44, ze + 2, X1 - T, 44 + T, zl - 3)
    for px in (X0 + T, 38, X1 - T - 3):
        M.box('body', px, 44, ze + 2, px + 3, 47, zl - 3, SERENA)
    for x in range(X0 + T, X1 - T):
        M.put('body', x, 44, ze + 11, WOOD_D)
        if x % 3 == 0:
            M.box('body', x, 44, ze + 2, x + 1, 45, ze + 11, WOOD_D)
    top = build_roof(M, roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ze, 'p': 0.3, 'over': (2, 2, 8, 6)},
                                     {'x0': X0, 'y0': 44, 'x1': X1, 'y1': Y1, 'ze': zl, 'p': 0.3, 'over': (2, 2, 6, 6)}]), salt=221)
    gronda(M, top, X0, X1, Y0, Y0 - 8, side='front')
    chimney(M, top, 14, 60)
    yard(M, D, X0, X1, Y1, 56)
    if D >= 120:
        pozzo(M, 24, 96)
    elif D >= 100:
        pozzo(M, 24, 86)
    lantern(M, 40, Y0)
    s, nm = low_tag(D)
    return done(M, 'house-c' + s, 'c' + s, 1, 6, (8, D // 10),
                '住宅 C%s（地塊 8 × %d：里窩那、托斯卡納 —— 一樓大門夾兩扇窗、二樓三扇石框方窗、後半截加一層開敞的涼廊（altana：石柱、木欄杆）、深木屋簷%s；紅赭灰泥、綠窗板）'
                % (nm, D // 10, '、後院井' if D >= 120 else '、院子只剩院牆與井' if D >= 100 else '；沒有院子'))


# ─────────────────────────────── 中密度 ───────────────────────────────
def house_m_b():
    F, ze = floors(3)
    M = Model((80, 120, 160))
    M.plaster = ARANCIO
    X0, Y0, X1, Y1 = 2, 12, 78, 74
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    wall(M, R, PL, ze, T, M.plaster)
    for (z0, z1) in F[1:]:
        slab(M, R, z0 - 2, z0)
    put(M, 'volta', '前-店鋪', 'front', R, 24, PL)
    put(M, 'porta', '前-門', 'front', R, 62, PL)
    steps(M, 62, Y0, w=14)
    M.anchor('door', 62, Y0 - 1, PL)
    for f in (1, 2):
        band(M, R, F[f][0] + 7, F[f][0] + 8, SERENA, faces=('front',))
        for i, cx in enumerate((22, 58)):
            put(M, 'finestra', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, F[f][0] + 8)
    put(M, 'porta', '後-門', 'back', R, 40, PL)
    for f in (1, 2):
        for i, cx in enumerate((20, 60)):
            put(M, 'finestra', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, F[f][0] + 8)
    top = hip(M, R, ze, salt=231)
    chimney(M, top, 60, 60)
    back_corte(M, X0, X1, Y1, 120, gate=(30, 12))
    pozzo(M, 56, 98)
    lantern(M, 62, Y0)
    return done(M, 'house-m-b', 'm-b', 2, 8, (8, 12),
                '中密度住宅 M-B（原地升級：8 × 12 蓋三層的托斯卡納店屋 —— 一樓拱頂店鋪＋小門、樓上兩層石框方窗與窗台石線、四坡筒瓦頂＋深木屋簷；後院井；橙赭灰泥、綠窗板）')


def house_m_a():
    F, ze = floors(3)
    M = Model((120, 120, 160))
    M.plaster = CALCE
    X0, Y0, X1, Y1 = 2, 12, 118, 76
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    wall(M, R, PL, ze, T, M.plaster)
    for (z0, z1) in F[1:]:
        slab(M, R, z0 - 2, z0)
    put(M, 'portone', '前-門', 'front', R, 60, PL)
    steps(M, 60, Y0, w=20)
    M.anchor('door', 60, Y0 - 1, PL)
    for i, cx in enumerate((22, 98)):
        put(M, 'inginocchiata', '前-跪窗%d' % (i + 1), 'front', R, cx, PL + 6)
    band(M, R, F[1][0] - 2, F[1][0], SERENA, faces=('front',))           # 主樓層的石線（樓板那裡）
    for f in (1, 2):
        band(M, R, F[f][0] + 7, F[f][0] + 8, SERENA, faces=('front',))
        for i, cx in enumerate((22, 60, 98)):
            put(M, 'finestra', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, F[f][0] + 8)
    put(M, 'porta', '後-門', 'back', R, 60, PL)
    for f in (1, 2):
        for i, cx in enumerate((25, 60, 95)):
            put(M, 'finestra', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, F[f][0] + 8)
    top = hip(M, R, ze, over=(2, 2, 10, 8), salt=241)
    chimney(M, top, 16, 60)
    chimney(M, top, 104, 30)
    back_corte(M, X0, X1, Y1, 120, gate=(96, 12))
    pozzo(M, 40, 98)
    lantern(M, 60, Y0)
    return done(M, 'house-m-a', 'm-a', 2, 12, (12, 12),
                '中密度住宅 M-A（三開間的托斯卡納小宅邸 palazzetto —— pietra serena 大門、一樓兩扇跪窗（鐵柵）、主樓層石線、兩層三扇石框方窗、四坡筒瓦頂＋深木屋簷、兩根煙囪；後院井；石灰白灰泥、綠窗板）')


# ─────────────────────────────── 高密度 ───────────────────────────────
def house_h_b():
    F, ze = floors(5)
    M = Model((120, 120, 230))
    M.plaster = VERDINO
    X0, Y0, X1, Y1 = 2, 12, 118, 80
    R = (X0, Y0, X1, Y1)
    plinth(M, R, color=ARDESIA)
    wall(M, R, PL, ze, T, M.plaster)
    for (z0, z1) in F[1:]:
        slab(M, R, z0 - 2, z0)
    put(M, 'volta', '前-店鋪1', 'front', R, 22, PL)
    put(M, 'portale', '前-門', 'front', R, 60, PL)
    put(M, 'volta', '前-店鋪2', 'front', R, 98, PL)
    steps(M, 60, Y0, color=ARDESIA)
    M.anchor('door', 60, Y0 - 1, PL)
    for f in range(1, 5):
        for i, cx in enumerate((22, 48, 74, 100)):
            put(M, 'finestral', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, F[f][0] + 6)
            paint_frame(M, R, cx, F[f][0] + 6)
    put(M, 'porta', '後-門', 'back', R, 60, PL)
    for f in range(1, 5):
        for i, cx in enumerate((30, 90)):
            put(M, 'finestral', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, F[f][0] + 6)
    paint_bands(M, R, F)
    top = slate(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ze, 'p': 0.4, 'over': (2, 2, 3, 3)}])
    chimney(M, top, 20, 46, cap='slate')
    chimney(M, top, 100, 46, cap='slate')
    back_corte(M, X0, X1, Y1, 120, gate=(30, 12), color=M.plaster)
    lantern(M, 60, Y0)
    return done(M, 'house-h-b', 'h-b', 3, 13, (12, 12),
                '高密度住宅 H-B（原地升級：12 × 12 蓋五層的熱那亞樓 —— 一樓兩間拱頂店鋪夾黑石板大門、樓上四排畫白框的窄窗、白色樓層線、深色基座帶、順街的兩坡石板頂、兩根煙囪；淡綠灰泥、綠窗板）')


def house_h_a():
    F, ze = floors(4)
    M = Model((160, 160, 200))
    M.plaster = GIALLO
    X0, Y0, X1, Y1 = 2, 12, 158, 76
    R = (X0, Y0, X1, Y1)
    WR = (110, Y1 - T, 158, 158)
    plinth(M, R, color=FORTE_D)
    bugnato(M, R, PL, F[0][1] + 2, T)
    wall(M, R, F[0][1] + 2, ze, T, M.plaster)
    for (z0, z1) in F[1:]:
        slab(M, R, z0 - 2, z0)
    put(M, 'portone', '前-門', 'front', R, 80, PL)
    steps(M, 80, Y0, w=20)
    M.anchor('door', 80, Y0 - 1, PL)
    for i, cx in enumerate((22, 50, 110, 138)):
        put(M, 'inginocchiata', '前-跪窗%d' % (i + 1), 'front', R, cx, PL + 6)
    band(M, R, F[1][0] - 2, F[1][0], SERENA, faces=('front',))
    for f in (1, 2):
        band(M, R, F[f][0] + 7, F[f][0] + 8, SERENA, faces=('front',))
        for i, cx in enumerate((20, 50, 80, 110, 140)):
            put(M, 'finestra', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, F[f][0] + 8)
    z3 = F[3][0]                                                        # 頂樓：朝街一整排開敞涼廊（Palazzo Guadagni 那種）—— 石柱、木欄杆；涼廊後面一道牆（屋裡）
    M.clear(X0 + T, Y0, z3, X1 - T, Y0 + T, ze)
    M.box('body', X0 + T, Y0 + 28, z3, X1 - T, Y0 + 31, ze, M.plaster)
    for i, cx in enumerate((40, 80, 120)):
        put(M, 'porta', '涼廊-門%d' % (i + 1), 'front', (X0, Y0 + 28, X1, Y1), cx, z3)
    for px in list(range(X0 + T, X1 - 4, 25)) + [X1 - T - 3]:
        M.box('body', px, Y0, z3, px + 3, Y0 + T, ze, SERENA)
    M.box('body', X0 + T, Y0, ze - 3, X1 - T, Y0 + T, ze, SERENA)
    for x in range(X0 + T, X1 - T):
        M.put('body', x, Y0, z3 + 10, WOOD_D)
        if x % 3 == 0:
            M.box('body', x, Y0, z3, x + 1, Y0 + 1, z3 + 10, WOOD_D)
    put(M, 'porta', '後-門', 'back', R, 100, PL)
    for f in (1, 2, 3):
        for i, cx in enumerate((20, 50, 84)):
            put(M, 'finestra', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, F[f][0] + 8)
    Fw, zew = floors(3)
    M.box('body', WR[0], WR[1], 0, WR[2], WR[3], PL, SERENA)
    wall(M, WR, PL, zew, T, M.plaster)
    for (z0, z1) in Fw[1:]:
        slab(M, WR, z0 - 2, z0)
    put(M, 'porta', '側翼-門', 'left', WR, 96, PL)
    put(M, 'finestra', '側翼-一樓窗', 'left', WR, 136, PL + 12)
    for f in (1, 2):
        for i, cy in enumerate((96, 136)):
            put(M, 'finestra', '側翼-%d樓窗%d' % (f + 1, i + 1), 'left', WR, cy, Fw[f][0] + 8)
    top = build_roof(M, roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': ze, 'p': 0.33, 'over': (2, 2, 12, 6)},
                                     {'x0': WR[0], 'y0': Y1, 'x1': WR[2], 'y1': WR[3], 'ze': zew, 'p': 0.33, 'over': (2, 2, 0, 2)}]), salt=251)
    gronda(M, top, X0, X1, Y0, Y0 - 12, side='front')
    chimney(M, top, 30, 60)
    chimney(M, top, 130, 30)
    chimney(M, top, 146, 120)
    corte_wall(M, (X0, Y1, X0 + T, 158))
    corte_wall(M, (X0, 155, WR[0], 158))
    M.box('body', X0 + T, Y1, 0, WR[0], 155, 1, PAVE)
    pozzo(M, 50, 116)
    lantern(M, 80, Y0)
    return done(M, 'house-h-a', 'h-a', 3, 24, (16, 16),
                '高密度住宅 H-A（佛羅倫斯的院子宅邸 —— 一樓 pietra forte 粗面石、大門、四扇跪窗；兩層五扇石框方窗與石線；頂樓朝街一整排開敞涼廊（石柱、木欄杆）；'
                '很深的木屋簷；右邊三層側翼圍出石板院子、井；三根煙囪；黃赭灰泥、綠窗板）')


# ─────────────────────────────── 超高密度（第 4 級）───────────────────────────────
def row(x0, x1, w, gap):
    n = max(1, (x1 - x0 + gap) // (w + gap))
    span = n * w + (n - 1) * gap
    s = x0 + (x1 - x0 - span) // 2
    return [s + i * (w + gap) + w // 2 for i in range(n)]


def genova(key, lot, units, live, title):
    """熱那亞的高樓：units ＝ [(x0, x1, 層數, 灰泥色)…]（一個開間一棟、各自一圈牆、一塊屋頂）。"""
    W, D = lot[0] * 10, lot[1] * 10
    zmax = max(floors(n, 42, 30)[1] for (_, _, n, _) in units)
    M = Model((W, D, zmax + 70))
    Y0 = 12
    Y1 = 74 if D <= 80 else D - 24
    rects, first = [], None
    for ui, (x0, x1, n, col) in enumerate(units):
        F, ze = floors(n, 42, 30)
        R = (x0, Y0, x1, Y1)
        M.plaster = col
        plinth(M, R, color=ARDESIA)
        wall(M, R, PL, ze, T, col)
        for (z0, z1) in F[1:]:
            slab(M, R, z0 - 2, z0)
        w = x1 - x0
        door_x = x1 - 11 if w >= 50 else (x0 + x1) // 2
        if w >= 50:                                                     # 一樓：拱頂店鋪＋窄的住家門（開間不到 5 m ⇒ 只有門）
            put(M, 'volta', '前-%d店鋪' % (ui + 1), 'front', R, x0 + 17, PL)
        put(M, 'porta', '前-%d門' % (ui + 1), 'front', R, door_x, PL)
        steps(M, door_x, Y0, w=14, color=ARDESIA)
        if first is None:
            first = door_x
        xs = row(x0 + 5, x1 - 5, 17, 5)
        for f in range(1, n):
            for i, cx in enumerate(xs):
                put(M, 'finestral', '%d-%d樓窗%d' % (ui + 1, f + 1, i + 1), 'front', R, cx, F[f][0] + 5)
                paint_frame(M, R, cx, F[f][0] + 5)
            for i, cx in enumerate(xs[::2]):
                put(M, 'finestral', '後%d-%d樓窗%d' % (ui + 1, f + 1, i + 1), 'back', R, cx, F[f][0] + 5)
        paint_bands(M, R, F)
        rects.append({'x0': x0, 'y0': Y0, 'x1': x1, 'y1': Y1, 'ze': ze, 'p': 0.4,
                      'over': (2 if ui == 0 else 0, 2 if ui == len(units) - 1 else 0, 3, 3)})
    M.plaster = units[0][3]
    M.anchor('door', first, Y0 - 1, PL)
    top = slate(M, rects, [u[3] for u in units])
    for (x0, x1, n, col) in units:
        M.plaster = col
        chimney(M, top, x1 - 12, Y1 - 14, cap='slate', color=col)
    M.plaster = units[0][3]
    if D >= 120:
        back_corte(M, units[0][0], units[-1][1], Y1, D, gate=(units[-1][1] - 24, 12), color=CALCE)
    lantern(M, first, Y0)
    return done(M, key, key.split('-', 1)[1], 4, live, lot, title)


def house_t_a():
    return genova('house-t-a', (20, 16), [(2, 58, 7, ROSA), (58, 110, 6, GIALLO), (110, 152, 7, VERDINO), (152, 198, 6, ARANCIO)], 80,
                  '超高密度住宅 T-A（20 × 16：熱那亞 caruggi 兩旁的高樓 —— 四個窄開間（粉、黃赭、淡綠、橙赭）各自 6～7 層、屋頂高低差一層；一樓拱頂店鋪與窄的住家門；'
                  '樓上畫白框的窄窗、白色樓層線、深色基座帶；順街的兩坡石板頂；後面小院）')


def house_t_b():
    return genova('house-t-b', (16, 16), [(2, 56, 7, GIALLO), (56, 104, 6, ROSA), (104, 158, 7, CALCE)], 64,
                  '超高密度住宅 T-B（16 × 16：熱那亞的高樓 —— 三個窄開間（黃赭、粉、石灰白）6～7 層；一樓拱頂店鋪與住家門；畫框窄窗、白色樓層線；石板頂；後面小院）')


def house_t_c():
    return genova('house-t-c', (12, 12), [(2, 62, 6, ARANCIO), (62, 118, 7, VERDINO)], 36,
                  '超高密度住宅 T-C（12 × 12：熱那亞的高樓 —— 兩個窄開間（橙赭 6 層、淡綠 7 層）；一樓拱頂店鋪與住家門；畫框窄窗、白色樓層線；石板頂；後面小院）')


def house_t_d():
    return genova('house-t-d', (8, 12), [(2, 78, 6, ROSA)], 24,
                  '超高密度住宅 T-D（8 × 12：熱那亞的六層窄樓 —— 一樓拱頂店鋪＋住家門、樓上畫白框的窄窗、白色樓層線、深色基座帶；石板頂；後面小院；粉灰泥）')


def house_t_e():
    return genova('house-t-e', (8, 8), [(2, 78, 5, GIALLO)], 16,
                  '超高密度住宅 T-E（8 × 8：熱那亞的五層窄樓 —— 一樓拱頂店鋪＋住家門、樓上畫白框的窄窗、白色樓層線、深色基座帶；石板頂；沒有院子；黃赭灰泥）')


ALL = [lambda: house_a(120), lambda: house_b(120), lambda: house_c(120),
       lambda: house_a(100), lambda: house_b(100), lambda: house_c(100),
       lambda: house_a(80), lambda: house_b(80), lambda: house_c(80),
       house_m_b, house_m_a, house_h_b, house_h_a,
       house_t_a, house_t_b, house_t_c, house_t_d, house_t_e]

# 配色變化（設計決定）：灰泥換一種 1666 年用得到的色（黃赭、紅赭、石灰白、粉、淡綠、橙赭；18 世紀才流行的粉藍、粉綠不用）、窗板換深褐或深紅
RC = {'a': ({GIALLO: CALCE, SCURO: PORTA}, '石灰白灰泥、深褐窗板'), 'b': ({ROSA: GIALLO, SCURO: 96}, '黃赭灰泥、深紅窗板'),
      'c': ({ROSSO_O: ARANCIO, SCURO: PORTA}, '橙赭灰泥、深褐窗板')}
VARIANTS = [('house-%s2%s' % (t, s), 'house-%s%s' % (t, s), RC[t][0], '住宅 %s2%s（%s 的配色變化：%s；替換色，不另存格子）' % (t.upper(), nm, t.upper() + nm, RC[t][1]))
            for s, nm in (('', ''), ('-s', ' 淺版'), ('-xs', ' 小版')) for t in 'abc']
VARIANTS += [('house-m-b2', 'house-m-b', {ARANCIO: ROSSO_O, SCURO: PORTA}, '中密度住宅 M-B2（M-B 的配色變化：紅赭灰泥、深褐窗板；替換色，不另存格子）'),
             ('house-m-a2', 'house-m-a', {CALCE: GIALLO}, '中密度住宅 M-A2（M-A 的配色變化：黃赭灰泥、綠窗板；替換色，不另存格子）'),
             ('house-h-b2', 'house-h-b', {VERDINO: ROSA, SCURO: 96}, '高密度住宅 H-B2（H-B 的配色變化：粉灰泥、深紅窗板；替換色，不另存格子）'),
             ('house-h-a2', 'house-h-a', {GIALLO: ROSSO_O, SCURO: PORTA}, '高密度住宅 H-A2（H-A 的配色變化：紅赭灰泥、深褐窗板；替換色，不另存格子）'),
             ('house-t-a2', 'house-t-a', {ROSA: CALCE, GIALLO: ROSSO_O, VERDINO: ROSA, ARANCIO: GIALLO, SCURO: PORTA},
              '超高密度住宅 T-A2（T-A 的配色變化：四個開間換成石灰白、紅赭、粉、黃赭，深褐窗板；替換色，不另存格子）'),
             ('house-t-b2', 'house-t-b', {GIALLO: VERDINO, ROSA: ARANCIO, CALCE: ROSA, SCURO: 96},
              '超高密度住宅 T-B2（T-B 的配色變化：淡綠、橙赭、粉，深紅窗板；替換色，不另存格子）'),
             ('house-t-c2', 'house-t-c', {ARANCIO: ROSA, VERDINO: GIALLO, SCURO: PORTA}, '超高密度住宅 T-C2（T-C 的配色變化：粉、黃赭，深褐窗板；替換色，不另存格子）'),
             ('house-t-d2', 'house-t-d', {ROSA: VERDINO, SCURO: 96}, '超高密度住宅 T-D2（T-D 的配色變化：淡綠灰泥、深紅窗板；替換色，不另存格子）'),
             ('house-t-e2', 'house-t-e', {GIALLO: ROSSO_O, SCURO: PORTA}, '超高密度住宅 T-E2（T-E 的配色變化：紅赭灰泥、深褐窗板；替換色，不另存格子）')]
