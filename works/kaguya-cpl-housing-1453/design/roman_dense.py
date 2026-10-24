# 羅馬（君士坦丁堡 1453）的中、高密度住宅（TASK-0893；Tim 2026-10-24「接著參考目前的task 893 給君堡也加上中高密度的住宅建築吧」）
#   四種佔地照 crest-001 的 fr、carib 兩套（同一張單）：
#     中 M-B 8 × 12（原地升級，三層、住 8）、中 M-A 12 × 12（三層、住 12）、高 H-B 12 × 12（原地升級，四層、住 13）、高 H-A 16 × 16（四層＋三層側翼、住 24）；人數〔設計〕同 crest。
#   樣子〔設計〕（史料見 common.py）：一、二樓石灰岩方石夾紅磚帶；三樓以上木構夾灰泥，有的挑出街面（木托架）；
#     大街那一面一樓是磚拱券的店面；二樓雙拱窗、木陽台；紅陶筒瓦緩坡（0.35）四坡頂；後面院子有井欄、陶甕、院牆。
#     H-A 是大街上的柱廊房子（embolos）：一樓臨街退進一道五個拱的柱廊、店面開在廊下；後面 L 形圍出院子，側翼朝院子兩層木迴廊。
# 層高同 crest 的 fr：一樓 3.3 m（石基 0.3 m）、樓板 0.2 m、樓上每層 3.0 m。鄰居的地塊只隔 2 cm ⇒ 左右兩面是共用牆（不開窗）、屋簷陽台台階一律在框裡。
from common import *
import bzparts

PL, T = 3, 3
FLOORS = [(PL, 36), (38, 68), (70, 100), (102, 132)]       # 每一層的 [地板頂, 天花)；樓板在兩層之間
ROOF_P = 0.35
ROOT = 'kaguya-cpl-housing-1453'
PARTS = {pid: dict(P, work=ROOT + '-part-' + pid) for pid, P in bzparts.all_parts().items()}


def put(M, pid, name, face, rect, center, z):
    """部件的開口中心對準 center（front／back 量 x、left／right 量 y），底在 z（同 crest common.put_part）。"""
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
    L = M.links[-1]
    L['part'] = P['work']
    sh = getattr(M, 'shut', SHUT)                                       # 這一棟的門板色（低密度三型各一色；中高密度沒設 ⇒ 照部件原色）
    if sh != SHUT:
        L['recolor'] = dict(L.get('recolor') or {})
        L['recolor'][SHUT] = sh
        L['cells'] = {k: (sh if c == SHUT else c) for k, c in L['cells'].items()}


def slab(M, R, z0, z1, t=T):
    """樓板：只鋪牆裡（牆照常往上砌，外面看不到一道木帶）。"""
    X0, Y0, X1, Y1 = R
    M.box('body', X0 + t, Y0 + t, z0, X1 - t, Y1 - t, z1, WOOD)


def jetty_floor(M, x0, x1, y0, y1, z0, z1):
    """挑出那一截的樓板：外面看得到一根一根的擱柵頭。"""
    for x in range(x0, x1):
        M.box('body', x, y0, z0, x + 1, y1, z1, TIMBER if x % 4 < 2 else WOOD)


def steps(M, cx, y_wall, w=16, n=PL):
    for k in range(n):
        M.box('body', cx - w // 2, y_wall - 1 - k, 0, cx + w - w // 2, y_wall - k, n - k, LIME_G)


def plinth(M, R):
    X0, Y0, X1, Y1 = R
    M.box('body', X0, Y0, 0, X1, Y1, PL, LIME_G)


def cornice(M, R, z, color=BRICK_R):
    """簷下一道磚的鋸齒線腳（dogtooth，拜占庭牆頂常見）：外面一層，每隔一格凸出一格。"""
    X0, Y0, X1, Y1 = R
    for x in range(X0, X1):
        for y in range(Y0, Y1):
            if X0 < x < X1 - 1 and Y0 < y < Y1 - 1:
                continue
            if (x + y) % 2 == 0:
                k = (x, y, z)
                if k in M.cells:
                    M.cells[k] = ('body', color)


def back_yard(M, X0, X1, y0, y1, gate=None, salt=0):
    """後院的院牆：左、右、後三段（後牆在 y1 − 3..y1）；gate ＝ (中心 x, 寬) ⇒ 後牆開一道門、一扇木門關著。"""
    yard_wall(M, (X0, y0, X0 + T, y1), salt=salt)
    yard_wall(M, (X1 - T, y0, X1, y1), salt=salt)
    yard_wall(M, (X0, y1 - T, X1, y1), salt=salt)
    if gate:
        cx, w = gate
        M.clear(cx - w // 2, y1 - T, 0, cx + w - w // 2, y1, 23)
        M.box('body', cx - w // 2, y1 - 2, 0, cx + w - w // 2, y1 - 1, 19, getattr(M, 'shut', SHUT))
        for x in (cx - w // 2, cx + w - w // 2 - 1):
            M.box('body', x, y1 - 2, 0, x + 1, y1 - 1, 19, TIMBER)


def kitchen(M, R, salt=0):
    """院子角落的灶間：方石夾磚的矮屋、單坡筒瓦頂（低的那邊朝院子）、朝院子一道門洞。"""
    X0, Y0, X1, Y1 = R
    masonry(M, R, 0, 24, T, salt=salt)
    cx = (X0 + X1) // 2
    M.clear(cx - 5, Y0, 0, cx + 5, Y0 + T, 20)
    M.box('body', cx - 5, Y0 + T - 1, 0, cx + 5, Y0 + T, 20, DARK)
    shed_roof(M, X0 - 2, Y0 - 3, X1 + 2, Y1, 32, 0.3, low='front')


# ─────────────────────────────── 中 M-B 8 × 12 ───────────────────────────────
def house_m_b():
    """中密度 M-B（原地升級：低密度同一塊 8 × 12 蓋三層）—— 窄的店屋：一樓拱券店面＋門，二樓雙拱窗＋小窗（方石夾磚），
    三樓木構夾灰泥挑出街面 0.6 m（四根木托架）；後院院牆、井欄、陶甕。"""
    M = Model((80, 120, 122))
    X0, Y0, X1, Y1 = 3, 12, 77, 74
    R = (X0, Y0, X1, Y1)
    RJ = (X0, Y0 - 6, X1, Y1)
    plinth(M, R)
    masonry(M, R, PL, 68, T, salt=11)
    slab(M, R, 36, 38)
    jetty_floor(M, X0, X1, Y0 - 6, Y1, 68, 70)
    timber(M, RJ, 70, 100, T)
    brackets(M, (X0, 40, X1 - 2), Y0, Y0 - 6, 68)
    cornice(M, R, 66)
    put(M, 'shop', '前-店面', 'front', R, 22, PL)
    put(M, 'door', '前-門', 'front', R, 58, PL)
    steps(M, 58, Y0)
    M.anchor('door', 58, Y0 - 1, PL)
    put(M, 'window2', '二樓-雙拱窗', 'front', R, 22, FLOORS[1][0] + 8)
    put(M, 'window', '二樓-窗', 'front', R, 58, FLOORS[1][0] + 10)
    for i, cx in enumerate((22, 58)):
        put(M, 'window', '三樓-窗%d' % (i + 1), 'front', RJ, cx, FLOORS[2][0] + 8)
    put(M, 'door', '後-門', 'back', R, 40, PL)
    for i, cx in enumerate((16, 64)):
        put(M, 'window', '後-一樓窗%d' % (i + 1), 'back', R, cx, PL + 9)
    for f in (1, 2):
        for i, cx in enumerate((20, 60)):
            put(M, 'window', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R if f == 1 else RJ, cx, FLOORS[f][0] + 8)
    F = roof_field([{'x0': X0, 'y0': Y0 - 6, 'x1': X1, 'y1': Y1, 'ze': 100, 'p': ROOF_P, 'over': (3, 3, 4, 4)}])
    build_roof(M, F, salt=11)
    back_yard(M, X0, X1, Y1, 120, gate=(30, 12), salt=12)
    wellhead(M, 56, 98)
    for (cx, cy) in ((14, 84), (14, 92), (22, 84)):
        jar(M, cx, cy)
    M.models += [model(LANTERN, '燈籠-門', (46.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-b', 'variant': 'm-b', 'level': 2, 'live': 8,
            'title': '中密度住宅 M-B（原地升級：8 × 12 蓋三層的窄店屋 —— 一樓拱券店面＋門、二樓雙拱窗、三樓木構挑出街面；後院井欄、陶甕；白灰泥、牛血紅門板）',
            'use': 'house', 'lot': (8, 12), 'M': M, 'layers': {'body': '牆身', 'roof': '屋頂'}}


# ─────────────────────────────── 中 M-A 12 × 12 ───────────────────────────────
def house_m_a():
    """中密度 M-A（12 × 12、三層）—— 一樓兩間拱券店面夾正門；二樓方石夾磚、通長木陽台（芝諾法管的那種），中間一道門通陽台、兩邊雙拱窗；
    三樓木構夾灰泥四扇窗；後院灶間、井欄、陶甕、院牆後門。"""
    M = Model((120, 120, 122))
    X0, Y0, X1, Y1 = 3, 12, 117, 76
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    masonry(M, R, PL, 68, T, salt=21)
    slab(M, R, 36, 38)
    slab(M, R, 68, 70)
    timber(M, R, 68, 100, T)
    cornice(M, R, 66)
    put(M, 'shop', '前-店面1', 'front', R, 22, PL)
    put(M, 'door', '前-門', 'front', R, 60, PL)
    put(M, 'shop', '前-店面2', 'front', R, 98, PL)
    steps(M, 60, Y0)
    M.anchor('door', 60, Y0 - 1, PL)
    put(M, 'window2', '二樓-雙拱窗1', 'front', R, 22, FLOORS[1][0] + 8)
    put(M, 'door', '二樓-陽台門', 'front', R, 60, FLOORS[1][0])
    put(M, 'window2', '二樓-雙拱窗2', 'front', R, 98, FLOORS[1][0] + 8)
    wood_balcony(M, 5, 115, 4, Y0, FLOORS[1][0])
    brackets(M, (5, 40, 78, 113), Y0, 4, FLOORS[1][0] - 2, layer='gallery')
    for i, cx in enumerate((18, 46, 74, 102)):
        put(M, 'window', '三樓-窗%d' % (i + 1), 'front', R, cx, FLOORS[2][0] + 8)
    put(M, 'door', '後-門', 'back', R, 60, PL)
    for i, cx in enumerate((25, 95)):
        put(M, 'window', '後-一樓窗%d' % (i + 1), 'back', R, cx, PL + 9)
    for f in (1, 2):
        for i, cx in enumerate((25, 60, 95)):
            put(M, 'window', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 8)
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 100, 'p': ROOF_P, 'over': (3, 3, 8, 4)}])
    build_roof(M, F, salt=21)
    back_yard(M, X0, X1, Y1, 120, gate=(96, 12), salt=22)
    kitchen(M, (6, 92, 40, 117), salt=23)
    wellhead(M, 70, 98)
    for (cx, cy) in ((100, 86), (108, 86), (108, 94)):
        jar(M, cx, cy)
    M.models += [model(LANTERN, '燈籠-門', (48.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-a', 'variant': 'm-a', 'level': 2, 'live': 12,
            'title': '中密度住宅 M-A（三層的店屋：一樓兩間拱券店面夾正門、二樓通長木陽台＋雙拱窗、三樓木構夾灰泥；後院灶間、井欄、陶甕；白灰泥、牛血紅門板）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂'}}


# ─────────────────────────────── 高 H-B 12 × 12 ───────────────────────────────
def house_h_b():
    """高密度 H-B（原地升級：中密度同一塊 12 × 12 蓋四層）—— 一、二樓方石夾磚（店面、門、雙拱窗），三、四樓木構挑出街面 0.6 m；
    後院縮成 4 m：井欄、陶甕、院牆後門。"""
    M = Model((120, 120, 150))
    X0, Y0, X1, Y1 = 3, 12, 117, 78
    R = (X0, Y0, X1, Y1)
    RJ = (X0, Y0 - 6, X1, Y1)
    plinth(M, R)
    masonry(M, R, PL, 68, T, salt=31)
    slab(M, R, 36, 38)
    jetty_floor(M, X0, X1, Y0 - 6, Y1, 68, 70)
    timber(M, RJ, 70, 100, T)
    slab(M, RJ, 100, 102)
    timber(M, RJ, 100, 132, T)
    brackets(M, (X0, 40, 78, X1 - 2), Y0, Y0 - 6, 68)
    cornice(M, R, 66)
    put(M, 'shop', '前-店面1', 'front', R, 22, PL)
    put(M, 'door', '前-門', 'front', R, 60, PL)
    put(M, 'shop', '前-店面2', 'front', R, 98, PL)
    steps(M, 60, Y0)
    M.anchor('door', 60, Y0 - 1, PL)
    put(M, 'window2', '二樓-雙拱窗1', 'front', R, 22, FLOORS[1][0] + 8)
    put(M, 'window', '二樓-窗', 'front', R, 60, FLOORS[1][0] + 10)
    put(M, 'window2', '二樓-雙拱窗2', 'front', R, 98, FLOORS[1][0] + 8)
    for f in (2, 3):
        for i, cx in enumerate((18, 46, 74, 102)):
            put(M, 'window', '%d樓-窗%d' % (f + 1, i + 1), 'front', RJ, cx, FLOORS[f][0] + 8)
    put(M, 'door', '後-門', 'back', R, 60, PL)
    put(M, 'window', '後-一樓窗', 'back', R, 95, PL + 9)
    for f in (1, 2, 3):
        for i, cx in enumerate((25, 60, 95)):
            put(M, 'window', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R if f == 1 else RJ, cx, FLOORS[f][0] + 8)
    F = roof_field([{'x0': X0, 'y0': Y0 - 6, 'x1': X1, 'y1': Y1, 'ze': 132, 'p': ROOF_P, 'over': (3, 3, 4, 4)}])
    build_roof(M, F, salt=31)
    back_yard(M, X0, X1, Y1, 120, gate=(30, 12), salt=32)
    wellhead(M, 80, 100)
    for (cx, cy) in ((100, 90), (108, 90), (108, 98)):
        jar(M, cx, cy)
    M.models += [model(LANTERN, '燈籠-門', (48.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-b', 'variant': 'h-b', 'level': 3, 'live': 13,
            'title': '高密度住宅 H-B（原地升級：12 × 12 蓋四層 —— 一樓兩間店面夾正門、二樓雙拱窗、三四樓木構挑出街面；後院井欄、陶甕；白灰泥、牛血紅門板）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身', 'roof': '屋頂'}}


# ─────────────────────────────── 高 H-A 16 × 16 ───────────────────────────────
def arcade(M, y0, y1, centers, hw, spring, z0, salt=0):
    """在沿 x 的牆（厚 y0..y1）上開一排半圓拱；牆外那一面拱上一圈磚石相間的拱券。"""
    S = set()
    for cx in centers:
        cells = arch_cells(cx - hw, cx + hw, z0, spring)
        S |= set(cells)
        for (x, z) in cells:
            M.clear(x, y0, z, x + 1, y1, z + 1)
    for (x, z) in list(S):
        for dx in (-2, -1, 0, 1, 2):
            for dz in (-2, -1, 0, 1, 2):
                k = (x + dx, y0, z + dz)
                if (x + dx, z + dz) in S or k not in M.cells or z + dz < spring:
                    continue
                cx = min(centers, key=lambda c: abs(x + dx + 0.5 - c))
                outer = max(abs(dx), abs(dz)) == 2 and not any((x + dx + a, z + dz + b) in S for a in (-1, 0, 1) for b in (-1, 0, 1))
                M.cells[k] = ('body', BRICK_R if outer else ring_color(x + dx, z + dz, cx, spring, 13))


def gallery(M, x0, x1, y0, y1, floors, posts):
    """側翼朝院子的木迴廊：每層一片木地板＋外緣欄杆，立柱從地面一路到最上面那層的欄杆頂。"""
    for z in floors:
        M.box('gallery', x0, y0, z - 2, x1, y1, z, WOOD)
        for y in range(y0, y1):
            for zz in (z + 4, z + 9):
                M.put('gallery', x0, y, zz, TIMBER)
            if (y - y0) % 3 == 0:
                M.box('gallery', x0, y, z, x0 + 1, y + 1, z + 9, TIMBER)
    for y in posts:
        M.box('gallery', x0, y, 0, x0 + 2, y + 2, max(floors) + 10, TIMBER)


def house_h_a():
    """高密度 H-A（16 × 16、四層＋三層側翼）—— 大街上的柱廊房子（embolos）：一樓臨街退進 2.4 m，五個磚拱的柱廊，廊下兩間店面夾正門；
    二樓方石夾磚、中間三個開間一道木陽台、五扇雙拱窗；三、四樓木構夾灰泥。後面右邊一道三層側翼 L 形圍出院子，側翼朝院子兩層木迴廊；院子井欄、陶甕。"""
    M = Model((160, 160, 150))
    X0, Y0, X1, Y1 = 3, 4, 157, 80                                    # 臨街那一棟（含柱廊）
    R = (X0, Y0, X1, Y1)
    RS = (X0, 28, X1, Y1)                                              # 廊後面的店面那一道牆
    WR = (104, Y1 - T, 157, 157)                                       # 右側翼（前端疊在臨街那一棟的後牆上）
    plinth(M, R)
    M.box('body', X0 + T, Y0, 0, X1 - T, 28, PL, PAVE)                 # 廊下的石板
    masonry(M, R, PL, 68, T, salt=41)
    masonry(M, (X0, 28, X1, 28 + T), PL, 36, T, salt=41)              # 店面那一道牆（只有臨街那一段）
    slab(M, R, 36, 38)
    slab(M, R, 68, 70)
    timber(M, R, 68, 100, T)
    slab(M, R, 100, 102)
    timber(M, R, 100, 132, T)
    centers = (22, 51, 80, 109, 138)
    arcade(M, Y0, Y0 + T, centers, 11, 24, PL, salt=41)
    cornice(M, R, 66)
    for k in range(PL):                                                # 中間那個拱前面的台階
        M.box('body', 69, Y0 - 1 - k, 0, 91, Y0 - k, PL - k, LIME_G)
    put(M, 'shop', '廊下-店面1', 'front', RS, 30, PL)
    put(M, 'window', '廊下-窗1', 'front', RS, 55, PL + 9)
    put(M, 'door', '廊下-門', 'front', RS, 80, PL)
    put(M, 'window', '廊下-窗2', 'front', RS, 105, PL + 9)
    put(M, 'shop', '廊下-店面2', 'front', RS, 130, PL)
    M.anchor('door', 80, 27, PL)
    for i, cx in enumerate(centers):
        if cx == 80:
            put(M, 'door', '二樓-陽台門', 'front', R, cx, FLOORS[1][0])
        else:
            put(M, 'window2', '二樓-雙拱窗%d' % (i + 1), 'front', R, cx, FLOORS[1][0] + 8)
        for f in (2, 3):
            put(M, 'window', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, FLOORS[f][0] + 8)
    wood_balcony(M, 36, 125, 0, Y0, FLOORS[1][0], posts=11)
    brackets(M, (36, 64, 93, 123), Y0, 0, FLOORS[1][0] - 2, layer='gallery')
    # 臨街那一棟的背面（朝院子 x < 104）：後門、樓上窗
    put(M, 'door', '後-門', 'back', R, 50, PL)
    put(M, 'window', '後-一樓窗', 'back', R, 80, PL + 9)
    for f in (1, 2, 3):
        for i, cx in enumerate((20, 50, 80)):
            put(M, 'window', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 8)
    # 側翼：一、二樓方石夾磚、三樓木構；朝院子（left）一樓門與窗、二三樓每層兩道門通迴廊
    masonry(M, WR, 0, 68, T, salt=42)
    M.box('body', WR[0], WR[1], 0, WR[2], WR[3], PL, LIME_G)
    slab(M, WR, 36, 38)
    slab(M, WR, 68, 70)
    timber(M, WR, 68, 100, T)
    cornice(M, WR, 66)
    put(M, 'door', '側翼-門', 'left', WR, 115, PL)
    for i, cy in enumerate((95, 140)):
        put(M, 'window', '側翼-一樓窗%d' % (i + 1), 'left', WR, cy, PL + 9)
    for f in (1, 2):
        for i, cy in enumerate((100, 135)):
            put(M, 'door', '側翼-%d樓門%d' % (f + 1, i + 1), 'left', WR, cy, FLOORS[f][0])
    gallery(M, 88, 104, 84, 154, (FLOORS[1][0], FLOORS[2][0]), (84, 106, 130, 152))
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 132, 'p': ROOF_P, 'over': (3, 3, 4, 4)},
                    {'x0': WR[0], 'y0': Y1, 'x1': WR[2], 'y1': WR[3], 'ze': 100, 'p': ROOF_P, 'over': (18, 3, 0, 3)}])
    build_roof(M, F, salt=41)
    # 院子：左、後兩道院牆（右邊是側翼）、井欄、陶甕
    yard_wall(M, (X0, Y1, X0 + T, 157), salt=43)
    yard_wall(M, (X0, 154, WR[0], 157), salt=43)
    wellhead(M, 50, 118)
    for (cx, cy) in ((14, 138), (22, 138), (14, 146), (70, 146)):
        jar(M, cx, cy)
    M.models += [model(LANTERN, '燈籠-廊下門', (68.5, 28, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-a', 'variant': 'h-a', 'level': 3, 'live': 24,
            'title': '高密度住宅 H-A（大街上的柱廊房子：一樓五個磚拱的柱廊、廊下店面夾正門；二樓木陽台＋雙拱窗；三四樓木構；右側三層側翼圍出院子、朝院子兩層木迴廊；白灰泥、牛血紅門板）',
            'use': 'house', 'lot': (16, 16), 'M': M, 'layers': {'body': '牆身', 'gallery': '陽台與迴廊', 'roof': '屋頂'}}


ALL = [house_m_b, house_m_a, house_h_b, house_h_a]
# 配色變化（設計決定）：灰泥換土黃或鮭粉、門板換綠或藍；方石與磚不換（同一座城的石頭是同一種）
VARIANTS = [('house-m-b2', 'house-m-b', {PLASTER: OCHRE, SHUT: SH_BLUE}, '中密度住宅 M-B2（M-B 的配色變化：土黃灰泥、藍門板；替換色，不另存格子）'),
            ('house-m-a2', 'house-m-a', {PLASTER: OCHRE, SHUT: SH_GREEN}, '中密度住宅 M-A2（M-A 的配色變化：土黃灰泥、綠門板；替換色，不另存格子）'),
            ('house-h-b2', 'house-h-b', {PLASTER: SALMON, SHUT: SH_GREEN}, '高密度住宅 H-B2（H-B 的配色變化：鮭粉灰泥、綠門板；替換色，不另存格子）'),
            ('house-h-a2', 'house-h-a', {PLASTER: SALMON, SHUT: SH_BLUE}, '高密度住宅 H-A2（H-A 的配色變化：鮭粉灰泥、藍門板；替換色，不另存格子）')]
