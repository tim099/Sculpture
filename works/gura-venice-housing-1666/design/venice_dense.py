# 威尼斯 1666 的中、高密度住宅（gura-venice-housing-1666）—— 四種佔地照 kaguya、crest 的那幾套：
#   中 M-B 8 × 12（原地升級，三層、住 8）、中 M-A 12 × 12（三層、住 12）、高 H-B 12 × 12（原地升級，四層、住 13）、高 H-A 16 × 16（四層＋三層側翼、住 24）；人數〔設計〕同 crest。
#   樣子（史料見 ../notes.md）：
#     M-B 窄的店屋：一樓店面＋門、樓上哥德單窗與方窗、屋頂木平台（altana）、牆外一根喇叭煙囪；
#     M-A 三開間的小宅邸（palazzetto）：中間哥德門、主樓層中間三連窗＋石陽台照亮 portego、兩側單窗；樓層石線腳、臨街兩角隅石；
#     H-B 出租的公寓排屋（case in affitto）：一樓 regalzier（紅灰泥畫白磚縫）、兩間店面夾門、二樓以上伸出巷子 0.6 m（barbacani 木托架）、三排方窗；
#     H-A 院子宅邸：臨街四層（哥德門、主樓層三連窗＋石陽台、兩側哥德單窗），右邊三層側翼 L 形圍出院子（corte），
#         院子裡一道露天石梯（scala scoperta）貼著臨街那一棟的後牆爬到二樓、井欄（vera da pozzo）。
# 層高：一樓 3.3 m（石基 0.3 m）、樓板 0.2 m、樓上每層 3.0 m（同 kaguya、crest）。左右兩面是跟鄰居共用的牆 ⇒ 不開窗；屋簷陽台台階一律在框裡。
from common import *
import vparts

PL, T = 3, 3
FLOORS = [(PL, 36), (38, 68), (70, 100), (102, 132)]       # 每一層的 [地板頂, 天花)；樓板在兩層之間
ROOF_P = 0.33
ROOT = 'gura-venice-housing-1666'
PARTS = {pid: dict(P, work=ROOT + '-part-' + pid) for pid, P in vparts.all_parts().items()}


def put(M, pid, name, face, rect, center, z):
    """部件的開口中心對準 center（front／back 量 x、left／right 量 y），底在 z。窗板色照 M.shutter（kit.place 換 49）。"""
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


def roof(M, rects, salt=0):
    F = roof_field(rects)
    return build_roof(M, F, salt=salt)


def front_chimney(M, cx, y_wall, z_top, name='smoke'):
    """臨街牆外的煙道（canna fumaria）：貼牆、從一樓頂上兩塊石托架起，爬過屋簷、頂上喇叭口。"""
    cy = max(11, y_wall - 5)                                               # 錐帽張到半徑 9.5 格 ⇒ 不出框（煙道吃進牆裡一點）
    for k in range(4):                                                     # 石托（一層一層往外挑）
        M.box('body', cx - 5, y_wall - 1 - k * 2 - 1, 30 + k, cx + 5, y_wall, 31 + k, ISTRIA_G)
    mouth = chimney(M, cx, cy, 34, z_top)
    if name and name not in M.anchors:
        M.anchor(name, *mouth)
    return mouth


def roof_chimney(M, top, cx, cy, h=26):
    """從屋面冒出來的煙囪：底照那一點的屋面高。"""
    z0 = top[(cx, cy)] - 2
    mouth = chimney(M, cx, cy, z0, z0 + h)
    if 'smoke' not in M.anchors:
        M.anchor('smoke', *mouth)
    return mouth


def roof_altana(M, top, x0, y0, x1, y1, lift=8):
    """屋面上的木平台：四角磚墩從屋面穿上來，平台面比那一塊最高的屋面高 lift 格。"""
    zmax = max(top.get((x, y), 0) for x in range(x0, x1) for y in range(y0, y1))
    piers = [(px, py, top[(px + 1, py + 1)] - 1) for (px, py) in ((x0, y0), (x1 - 3, y0), (x0, y1 - 3), (x1 - 3, y1 - 3))]
    altana(M, x0, y0, x1, y1, zmax + lift, piers)


def back_corte(M, X0, X1, y0, y1, gate=None, salt=0):
    """後面的小院（corte）：左、右、後三道磚院牆、後牆一道木門；地面石板。"""
    corte_wall(M, (X0, y0, X0 + T, y1), salt=salt)
    corte_wall(M, (X1 - T, y0, X1, y1), salt=salt)
    corte_wall(M, (X0, y1 - T, X1, y1), salt=salt)
    if gate:
        cx, w = gate
        M.clear(cx - w // 2, y1 - T, 0, cx + w - w // 2, y1, 27)
        M.box('body', cx - w // 2, y1 - 2, 0, cx + w - w // 2, y1 - 1, 21, PORTA)
        for x in (cx - w // 2, cx + w - w // 2 - 1):
            M.box('body', x, y1 - 2, 0, x + 1, y1 - 1, 21, WOOD_D)


# ─────────────────────────────── 中 M-B 8 × 12 ───────────────────────────────
def house_m_b():
    M = Model((80, 120, 140))
    M.plaster = ROSSO
    X0, Y0, X1, Y1 = 2, 12, 78, 74
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    plastered(M, R, PL, 100, T, M.plaster, salt=11)
    slab(M, R, 36, 38); slab(M, R, 68, 70)
    stone_band(M, R, 36); stone_band(M, R, 68)
    dentils(M, R, 99)
    put(M, 'shop', '前-店面', 'front', R, 20, PL)
    put(M, 'door', '前-門', 'front', R, 48, PL)
    steps(M, 48, Y0)
    M.anchor('door', 48, Y0 - 1, PL)
    for f in (1, 2):
        for i, cx in enumerate((18, 46)):                                      # 二樓哥德單窗、三樓方窗（哥德窗的尖會頂到屋簷）
            put(M, 'window' if f == 1 else 'windowq', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, FLOORS[f][0] + (8 if f == 1 else 6))
    front_chimney(M, 70, Y0, 124)
    put(M, 'door', '後-門', 'back', R, 40, PL)
    for f in (1, 2):
        for i, cx in enumerate((22, 58)):
            put(M, 'windowq', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 8)
    top = roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 100, 'p': ROOF_P, 'over': (2, 2, 4, 4)}], salt=11)
    roof_altana(M, top, 10, 44, 56, 72)
    back_corte(M, X0, X1, Y1, 120, gate=(30, 12), salt=12)
    vera(M, 56, 98)
    M.models += [model(LANTERN, '燈籠-門', (36.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-b', 'variant': 'm-b', 'level': 2, 'live': 8,
            'title': '中密度住宅 M-B（原地升級：8 × 12 蓋三層的窄店屋 —— 一樓店面＋門、樓上哥德單窗與方窗、牆外喇叭煙囪、屋頂木平台；後院井欄；威尼斯紅灰泥、綠窗板）',
            'use': 'house', 'lot': (8, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '屋頂平台', 'roof': '屋頂'}}


# ─────────────────────────────── 中 M-A 12 × 12 ───────────────────────────────
def house_m_a():
    M = Model((120, 120, 150))
    M.plaster = ROSA
    X0, Y0, X1, Y1 = 2, 12, 118, 76
    R = (X0, Y0, X1, Y1)
    plinth(M, R)
    plastered(M, R, PL, 100, T, M.plaster, salt=21)
    slab(M, R, 36, 38); slab(M, R, 68, 70)
    stone_band(M, R, 36); stone_band(M, R, 68, 70)
    dentils(M, R, 99)
    put(M, 'doorg', '前-門', 'front', R, 60, PL)
    steps(M, 60, Y0)
    M.anchor('door', 60, Y0 - 1, PL)
    for i, cx in enumerate((20, 100)):
        put(M, 'windowq', '前-一樓窗%d' % (i + 1), 'front', R, cx, PL + 9)
    put(M, 'trifora', '二樓-三連窗', 'front', R, 60, FLOORS[1][0] + 2)
    poggiolo(M, 42, 79, Y0, 6, FLOORS[1][0] + 2)
    for i, cx in enumerate((20, 100)):
        put(M, 'window', '二樓-哥德窗%d' % (i + 1), 'front', R, cx, FLOORS[1][0] + 6)
    for i, cx in enumerate((20, 46, 74, 100)):
        put(M, 'windowq', '三樓-窗%d' % (i + 1), 'front', R, cx, FLOORS[2][0] + 7)
    put(M, 'door', '後-門', 'back', R, 60, PL)
    for f in (1, 2):
        for i, cx in enumerate((25, 60, 95)):
            put(M, 'windowq', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 8)
    top = roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 100, 'p': ROOF_P, 'over': (2, 2, 4, 4)}], salt=21)
    roof_chimney(M, top, 16, 60)
    roof_chimney(M, top, 104, 26)
    back_corte(M, X0, X1, Y1, 120, gate=(96, 12), salt=22)
    vera(M, 40, 98)
    M.models += [model(LANTERN, '燈籠-門', (46.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-a', 'variant': 'm-a', 'level': 2, 'live': 12,
            'title': '中密度住宅 M-A（三開間的小宅邸：哥德門、主樓層三連窗＋石陽台、兩側哥德單窗、三樓方窗、樓層石線腳、兩根喇叭煙囪；後院井欄；粉灰泥、綠窗板）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '石陽台', 'roof': '屋頂'}}


# ─────────────────────────────── 高 H-B 12 × 12 ───────────────────────────────
def house_h_b():
    M = Model((120, 120, 170))
    M.plaster = OCRA
    X0, Y0, X1, Y1 = 2, 12, 118, 78
    R = (X0, Y0, X1, Y1)
    RJ = (X0, Y0 - 6, X1, Y1)
    plinth(M, R)
    regal_wall(M, R, PL, 36, T)
    stone_band(M, R, 34, 36)
    jetty_floor(M, X0, X1, Y0 - 6, Y1, 36, 38)
    plastered(M, RJ, 38, 132, T, M.plaster, salt=31)
    slab(M, RJ, 68, 70); slab(M, RJ, 100, 102)
    barbacani(M, (X0 + 1, 22, 42, 62, 82, 102, X1 - 3), Y0, Y0 - 6, 36)
    dentils(M, RJ, 131)
    put(M, 'shop', '前-店面1', 'front', R, 20, PL)
    put(M, 'door', '前-門', 'front', R, 60, PL)
    put(M, 'shop', '前-店面2', 'front', R, 100, PL)
    steps(M, 60, Y0)
    M.anchor('door', 60, Y0 - 1, PL)
    for f in (1, 2, 3):
        for i, cx in enumerate((16, 44, 76, 104)):
            put(M, 'window' if f == 1 else 'windowq', '%d樓-窗%d' % (f + 1, i + 1), 'front', RJ, cx, FLOORS[f][0] + 7)
    put(M, 'door', '後-門', 'back', R, 60, PL)
    for f in (1, 2, 3):
        for i, cx in enumerate((25, 60, 95)):
            put(M, 'windowq', '後-%d樓窗%d' % (f + 1, i + 1), 'back', RJ, cx, FLOORS[f][0] + 8)
    top = roof(M, [{'x0': X0, 'y0': Y0 - 6, 'x1': X1, 'y1': Y1, 'ze': 132, 'p': ROOF_P, 'over': (2, 2, 2, 4)}], salt=31)
    roof_chimney(M, top, 14, 40)
    roof_chimney(M, top, 106, 58)
    roof_altana(M, top, 50, 46, 90, 74)
    back_corte(M, X0, X1, Y1, 120, gate=(30, 12), salt=32)
    vera(M, 84, 100)
    M.models += [model(LANTERN, '燈籠-門', (48.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-b', 'variant': 'h-b', 'level': 3, 'live': 13,
            'title': '高密度住宅 H-B（原地升級：12 × 12 蓋四層的出租排屋 —— 一樓紅灰泥畫白磚縫（regalzier）、兩間店面夾門，二樓以上抹灰伸出巷子 0.6 m 架在木托架上、三排方窗、屋頂木平台、兩根喇叭煙囪；後院井欄；土黃灰泥、綠窗板）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '屋頂平台', 'roof': '屋頂'}}


# ─────────────────────────────── 高 H-A 16 × 16 ───────────────────────────────
def scala(M, x_foot, y0, y1, z_top, run=3, rise=2, land=14):
    """院子裡的露天石梯（scala scoperta）：貼著 y0 那一道牆、從 x_foot 往 +x 爬到 z_top 的平台（平台長 land）；
    梯底下砌實（磚）、踏面伊斯特拉石、外側（y1 − 1）一道石欄杆。回傳平台的 x 範圍。"""
    n = z_top // rise
    xt = x_foot + n * run
    for k in range(n):
        zt = (k + 1) * rise
        xx = x_foot + k * run
        M.box('body', xx, y0, 0, xx + run, y1, zt - 1, MATTONE)
        M.box('body', xx, y0, zt - 1, xx + run, y1, zt, ISTRIA_G)
    M.box('body', xt, y0, 0, xt + land, y1, z_top - 1, MATTONE)              # 頂上的平台
    M.box('body', xt, y0, z_top - 1, xt + land, y1, z_top, ISTRIA_G)
    for xx in range(x_foot, xt + land):                                       # 外側的石欄杆：照梯的坡
        zb = min(z_top, ((xx - x_foot) // run + 1) * rise)
        M.put('body', xx, y1 - 1, zb + 9, ISTRIA)
        if (xx - x_foot) % 3 == 0 or xx == xt + land - 1:
            M.box('body', xx, y1 - 1, zb, xx + 1, y1, zb + 9, ISTRIA)
    return (xt, xt + land)


def house_h_a():
    M = Model((160, 160, 170))
    M.plaster = ROSSO
    X0, Y0, X1, Y1 = 2, 12, 158, 76                                   # 臨街那一棟
    R = (X0, Y0, X1, Y1)
    WR = (110, Y1 - T, 158, 158)                                       # 右側翼（前端疊在臨街那一棟的後牆上）
    plinth(M, R)
    plastered(M, R, PL, 132, T, M.plaster, salt=41)
    for (a, b) in ((36, 38), (68, 70), (100, 102)):
        slab(M, R, a, b)
    stone_band(M, R, 36); stone_band(M, R, 68, 70); stone_band(M, R, 100)
    dentils(M, R, 131)
    put(M, 'doorg', '前-門', 'front', R, 80, PL)
    steps(M, 80, Y0)
    M.anchor('door', 80, Y0 - 1, PL)
    for i, cx in enumerate((22, 50, 110, 138)):
        put(M, 'windowq', '前-一樓窗%d' % (i + 1), 'front', R, cx, PL + 9)
    put(M, 'trifora', '二樓-三連窗', 'front', R, 80, FLOORS[1][0] + 2)
    poggiolo(M, 62, 99, Y0, 6, FLOORS[1][0] + 2)
    for f in (1, 2, 3):
        for i, cx in enumerate((22, 48, 112, 138)):
            put(M, 'window' if f < 3 else 'windowq', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, FLOORS[f][0] + 6)
    for f in (2, 3):
        put(M, 'window' if f == 2 else 'windowq', '%d樓-中窗' % (f + 1), 'front', R, 80, FLOORS[f][0] + 6)
    # 臨街那一棟的背面（朝院子 x < 110）：後門、樓上窗
    put(M, 'door', '後-門', 'back', R, 100, PL)
    put(M, 'door', '後-二樓門', 'back', R, 84, FLOORS[1][0])                  # 露天石梯頂上的平台接這一道門
    for f in (1, 2, 3):
        for i, cx in enumerate((20, 50) if f == 1 else (20, 50, 84)):
            put(M, 'windowq', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 8)
    # 側翼：三層、一樓 regalzier、樓上抹灰；朝院子（left）一樓門與窗、二樓一道門接露天石梯
    M.box('body', WR[0], WR[1], 0, WR[2], WR[3], PL, ISTRIA_G)
    regal_wall(M, WR, PL, 36, T)
    plastered(M, WR, 36, 100, T, M.plaster, salt=42)
    slab(M, WR, 36, 38); slab(M, WR, 68, 70)
    stone_band(M, WR, 36)
    dentils(M, WR, 99)
    put(M, 'door', '側翼-門', 'left', WR, 96, PL)
    put(M, 'windowq', '側翼-一樓窗', 'left', WR, 146, PL + 9)
    for i, cy in enumerate((96, 120, 144)):
        put(M, 'window', '側翼-二樓窗%d' % (i + 1), 'left', WR, cy, FLOORS[1][0] + 6)
    for i, cy in enumerate((96, 120, 144)):
        put(M, 'windowq', '側翼-三樓窗%d' % (i + 1), 'left', WR, cy, FLOORS[2][0] + 8)
    scala(M, 20, Y1, Y1 + 12, FLOORS[1][0])                              # 貼著臨街那一棟的後牆、往右爬到二樓的後門
    top = roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 132, 'p': ROOF_P, 'over': (2, 2, 4, 4)},
                   {'x0': WR[0], 'y0': Y1, 'x1': WR[2], 'y1': WR[3], 'ze': 100, 'p': ROOF_P, 'over': (2, 2, 0, 2)}], salt=41)
    roof_chimney(M, top, 30, 60)
    roof_chimney(M, top, 130, 28)
    roof_chimney(M, top, 146, 120)
    # 院子：左、後兩道院牆（右邊是側翼）、井欄、石板
    corte_wall(M, (X0, Y1, X0 + T, 158), salt=43)
    corte_wall(M, (X0, 155, WR[0], 158), salt=43)
    M.box('body', X0 + T, Y1, 0, WR[0], 155, 1, PAVE)
    vera(M, 50, 116)
    M.models += [model(LANTERN, '燈籠-門', (66.5, Y0, 24.5))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-a', 'variant': 'h-a', 'level': 3, 'live': 24,
            'title': '高密度住宅 H-A（院子宅邸：臨街四層 —— 哥德門、主樓層三連窗＋石陽台、哥德單窗、樓層石線腳；右邊三層側翼圍出院子，院子裡露天石梯爬到二樓、井欄；三根喇叭煙囪；威尼斯紅灰泥、綠窗板）',
            'use': 'house', 'lot': (16, 16), 'M': M, 'layers': {'body': '牆身', 'gallery': '石陽台', 'roof': '屋頂'}}


ALL = [house_m_b, house_m_a, house_h_b, house_h_a]
# 配色變化（設計決定）：灰泥換另一種威尼斯常見的色、窗板換深褐（kit 的 49 ⇒ 100）或灰藍；伊斯特拉石與磚不換
VARIANTS = [('house-m-b2', 'house-m-b', {ROSSO: OCRA, SCURI: SH_GREY}, '中密度住宅 M-B2（M-B 的配色變化：土黃灰泥、灰藍窗板；替換色，不另存格子）'),
            ('house-m-a2', 'house-m-a', {ROSA: CREMA}, '中密度住宅 M-A2（M-A 的配色變化：米白灰泥、綠窗板；替換色，不另存格子）'),
            ('house-h-b2', 'house-h-b', {OCRA: ROSSO, SCURI: PORTA}, '高密度住宅 H-B2（H-B 的配色變化：威尼斯紅灰泥、深褐窗板；替換色，不另存格子）'),
            ('house-h-a2', 'house-h-a', {ROSSO: ROSA, SCURI: SH_GREY}, '高密度住宅 H-A2（H-A 的配色變化：粉灰泥、灰藍窗板；替換色，不另存格子）')]
