# 法式（fr）的中、高密度住宅（TASK-0893）—— 照 summit-bourg-fr-01m 住宅 A 的做法（灰泥牆、隅石、腰線、鐵陽台、四坡紅陶瓦、老虎窗），層數加高、地塊加寬。
#   中密度 house-m-a：地塊 12 × 12 m（3 × 3 格）；三層的城中屋（maison de ville）—— 一樓切石牆、兩間店面（貨門）夾正門，二樓落地窗＋通長鐵陽台，
#     三樓四扇窗、屋面三扇老虎窗（閣樓）；後院院牆＋廚房小屋＋水井。住 12 人（低密度的兩倍）〔設計〕。
#   高密度 house-h-a：地塊 16 × 16 m（4 × 4 格）；四層的出租公寓（maison à loyer）—— 臨街一棟四層，加右側一道三層的側翼，L 形圍出內院；
#     一樓左邊一道車馬門穿到內院（porte cochère）、一間店面；二樓落地窗＋通長鐵陽台；內院院牆、後門、水井。住 24 人（四倍）〔設計〕。
# 層高照住宅 A：一樓 3.3 m（石基 0.3 m）、樓板 0.2 m、樓上每層 3.0 m。
# 鄰居的地塊只隔 2 cm ⇒ 左右兩面是共用牆（不開窗；側翼的右牆同理），屋簷、陽台、台階一律在框裡。
from common import *

PL, T = 3, 3                                    # 石基高、牆厚（格）
STONE_DW = 173                                  # 切石牆裡深一點的石塊（暖褐；kit 的 STONE_D 110 畫出來偏藍紫 —— BUILDING_SPEC §10 第 6 條同一個坑）
FLOORS = [(PL, 36), (38, 68), (70, 100), (102, 132)]   # 每一層牆的 [底, 頂)；樓板在兩層之間（36..38、68..70、100..102）


def storeys(M, R, n, color, salt=0):
    """n 層的屋身：石基、一樓切石牆、樓上灰泥、樓板、隅石、腰線、簷口線腳。回傳牆頂 z。"""
    X0, Y0, X1, Y1 = R
    M.box('body', X0, Y0, 0, X1, Y1, PL, STONE)
    rubble(M, R, PL, FLOORS[0][1], T, base=STONE_W, mortar=STONE_L, course=5, block=8, salt=salt, dark=STONE_DW)
    for i in range(1, n):
        z0, z1 = FLOORS[i]
        floor_slab(M, R, FLOORS[i - 1][1], z0)
        stucco_walls(M, R, z0, z1, T, color)
    top = FLOORS[n - 1][1]
    quoins(M, R, FLOORS[1][0], top)
    band(M, R, FLOORS[0][1], FLOORS[1][0], STONE_L, out=1)          # 一樓頂的石腰線（店面的簷）
    for i in range(2, n):
        band(M, R, FLOORS[i - 1][1], FLOORS[i][0], TRIM, out=0)      # 樓層線
    band(M, R, top - 3, top, TRIM, out=1)                            # 簷口線腳
    return top


def front_steps(M, cx, Y0, w=19):
    for k in range(3):
        M.box('body', cx - w // 2, Y0 - 1 - k, 0, cx + w - w // 2, Y0 - k, PL - k, STONE_L)


def house_m_a():
    M = Model((120, 120, 140))
    X0, Y0, X1, Y1 = 3, 12, 117, 76
    R = (X0, Y0, X1, Y1)
    zt = storeys(M, R, 3, SALMON, salt=31)
    P = FR_PARTS
    # 一樓：兩間店面（貨門）夾正門
    put_part(M, P, 'cartdoor', '前-店面1', 'front', R, 22, PL, T)
    put_part(M, P, 'door', '前-門', 'front', R, 60, PL, T)
    put_part(M, P, 'cartdoor', '前-店面2', 'front', R, 98, PL, T)
    front_steps(M, 60, Y0)
    M.anchor('door', 60, Y0 - 1, PL)
    # 二樓：四扇落地窗＋通長鐵陽台（托架挑出 0.9 m）；三樓：四扇窗
    for i, cx in enumerate((18, 46, 74, 102)):
        put_part(M, P, 'frenchdoor', '二樓-落地窗%d' % (i + 1), 'front', R, cx, FLOORS[1][0], T)
        put_part(M, P, 'window', '三樓-窗%d' % (i + 1), 'front', R, cx, FLOORS[2][0] + 8, T)
    iron_balcony(M, 5, 115, 3, Y0, FLOORS[1][0], brackets=(5, 42, 75, 113))          # 托架在一樓的店面、門之間
    # 背面：後門、一樓兩扇窗、樓上每層三扇窗
    put_part(M, P, 'door', '後-門', 'back', R, 60, PL, T)
    for i, cx in enumerate((25, 95)):
        put_part(M, P, 'window', '後-一樓窗%d' % (i + 1), 'back', R, cx, PL + 9, T)
    for f in (1, 2):
        for i, cx in enumerate((25, 60, 95)):
            put_part(M, P, 'window', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 8, T)
    # 屋頂：四坡（0.85），前簷蓋到陽台外緣；三扇老虎窗、兩支煙囪
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': zt, 'p': 0.85, 'over': (3, 3, 8, 6)}])
    top = build_roof(M, F, salt=31)
    for i, cx in enumerate((32, 60, 88)):
        y0 = Y0 + 3
        free_part(M, P, 'dormer', '老虎窗%d' % (i + 1), (cx - 7, y0, top[(cx, y0 + 1)] - 1))
    free_part(M, P, 'chimney', '煙囪1', (8, Y1 - 22, zt - 7))
    free_part(M, P, 'chimney', '煙囪2', (104, Y1 - 22, zt - 7))
    # 後院：院牆＋後門、廚房小屋（左後角，同住宅 A）、水井
    FRH.yard(M, X0, Y1, X1, 120, 3, 22, SALMON, gate=(96, 13, 19))
    FRH.kitchen(M, (X0 + 3, 92, 40, 117), SALMON, 'right', 104, vent_face='front', vent_c=22, low='right', chim=(6, 108, 2), salt=32)
    well(M, 72, 100)
    M.models += [model(LANTERN, '燈籠-門', (48.5, Y0, 24.5)),
                 model(BARREL, '酒桶-院1', (104, 96, 0)), model(BARREL, '酒桶-院2', (104, 103, 0))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-a', 'variant': 'm-a', 'level': 2, 'live': 12,
            'title': '中密度住宅 M-A（三層的城中屋：一樓切石兩間店面夾正門、二樓落地窗＋通長鐵陽台、三樓、閣樓老虎窗；後院院牆＋廚房＋水井；鮭粉牆綠百葉）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂'}}


def house_h_a():
    M = Model((160, 160, 172))
    M.shutter = SH_BLUE
    X0, Y0, X1, Y1 = 3, 12, 157, 80                                   # 臨街的一棟
    R = (X0, Y0, X1, Y1)
    WR = (105, Y1 - T, 157, 157)                                       # 右側的側翼（三層；前端疊在臨街那一棟的後牆上 ⇒ 那一道牆兩邊共用）
    zt = storeys(M, R, 4, CREAM, salt=41)
    zw = storeys(M, WR, 3, CREAM, salt=42)
    P = FR_PARTS
    # 一樓：車馬門（穿到內院）、窗、正門（樓梯間）、窗、店面
    put_part(M, P, 'cartdoor', '前-車馬門', 'front', R, 32, PL, T)
    put_part(M, P, 'window', '前-一樓窗1', 'front', R, 60, PL + 9, T)
    put_part(M, P, 'door', '前-門', 'front', R, 85, PL, T)
    put_part(M, P, 'window', '前-一樓窗2', 'front', R, 108, PL + 9, T)
    put_part(M, P, 'cartdoor', '前-店面', 'front', R, 136, PL, T)
    front_steps(M, 85, Y0)
    M.anchor('door', 85, Y0 - 1, PL)
    # 樓上：每層五個開間；二樓落地窗＋通長鐵陽台，三、四樓窗
    for i, cx in enumerate((20, 50, 80, 110, 140)):
        put_part(M, P, 'frenchdoor', '二樓-落地窗%d' % (i + 1), 'front', R, cx, FLOORS[1][0], T)
        for f in (2, 3):
            put_part(M, P, 'window', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, FLOORS[f][0] + 8, T)
    iron_balcony(M, 5, 155, 3, Y0, FLOORS[1][0], brackets=(5, 47, 73, 96, 120, 153))
    # 臨街那一棟的背面（朝內院那一段 x < 105）：車馬門、後門、樓上每層三扇窗
    put_part(M, P, 'cartdoor', '後-車馬門', 'back', R, 32, PL, T)
    put_part(M, P, 'door', '後-門', 'back', R, 80, PL, T)
    for f in (1, 2, 3):
        for i, cx in enumerate((20, 55, 85)):
            put_part(M, P, 'window', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 8, T)
    # 側翼朝內院那一面（left）：一樓門、窗；樓上每層三扇窗
    put_part(M, P, 'door', '側翼-門', 'left', WR, 100, PL, T)
    for i, cy in enumerate((122, 142)):                                # 窗要在內院後牆（y 154..157）之前
        put_part(M, P, 'window', '側翼-一樓窗%d' % (i + 1), 'left', WR, cy, PL + 9, T)
    for f in (1, 2):
        for i, cy in enumerate((98, 122, 145)):
            put_part(M, P, 'window', '側翼-%d樓窗%d' % (f + 1, i + 1), 'left', WR, cy, FLOORS[f][0] + 8, T)
    # 屋頂：臨街那一棟四坡（0.85）、側翼四坡（0.85，低一層；前端撞進臨街那一棟的後坡）；四扇老虎窗、三支煙囪
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': zt, 'p': 0.85, 'over': (3, 3, 8, 5)},
                    {'x0': WR[0], 'y0': Y1, 'x1': WR[2], 'y1': WR[3], 'ze': zw, 'p': 0.85, 'over': (4, 3, 0, 3)}])
    top = build_roof(M, F, salt=41)
    for i, cx in enumerate((30, 62, 98, 130)):
        y0 = Y0 + 3
        free_part(M, P, 'dormer', '老虎窗%d' % (i + 1), (cx - 7, y0, top[(cx, y0 + 1)] - 1))
    free_part(M, P, 'chimney', '煙囪1', (8, Y1 - 22, zt - 7))
    free_part(M, P, 'chimney', '煙囪2', (144, Y1 - 22, zt - 7))
    free_part(M, P, 'chimney', '煙囪3', (144, 138, zw - 7))
    # 內院：左、後兩道院牆（右邊是側翼）、後牆一扇門、水井
    for (a, b, c, d) in ((X0, Y1, X0 + 3, 157), (X0, 154, WR[0], 157)):
        M.box('body', a, b, 0, c, d, 22, CREAM)
        M.box('body', a, b, 22, c, d, 24, TILE_R)
    FRH.simple_door(M, 'back', (X0, Y1, WR[0], 157), 52, 13, 19, 3)
    well(M, 55, 118)
    M.models += [model(LANTERN, '燈籠-門', (73.5, Y0, 24.5)), model(LANTERN, '燈籠-車馬門', (16, Y0, 31)),
                 model(BARREL, '酒桶-內院1', (90, 140, 0)), model(BARREL, '酒桶-內院2', (90, 147, 0)), model(CRATE, '貨箱-內院', (20, 140, 0))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-a', 'variant': 'h-a', 'level': 3, 'live': 24,
            'title': '高密度住宅 H-A（四層的出租公寓：臨街一棟四層＋右側三層側翼圍出內院；一樓車馬門穿到內院、店面；二樓落地窗＋通長鐵陽台；老虎窗；米白牆藍百葉）',
            'use': 'house', 'lot': (16, 16), 'M': M, 'layers': {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂'}}


def house_m_b():
    """中密度 M-B（原地升級用，TASK-0895）：低密度同一塊 8 × 12 地塊上蓋三層 —— 窄的城中屋（一間店面＋正門、二樓兩扇落地窗＋鐵陽台、三樓兩扇窗、一扇老虎窗）；後院同住宅 A。"""
    M = Model((80, 120, 140))
    X0, Y0, X1, Y1 = 3, 12, 77, 72
    R = (X0, Y0, X1, Y1)
    zt = storeys(M, R, 3, OCHRE, salt=71)
    P = FR_PARTS
    put_part(M, P, 'cartdoor', '前-店面', 'front', R, 22, PL, T)
    put_part(M, P, 'door', '前-門', 'front', R, 58, PL, T)
    front_steps(M, 58, Y0)
    M.anchor('door', 58, Y0 - 1, PL)
    for i, cx in enumerate((22, 58)):
        put_part(M, P, 'frenchdoor', '二樓-落地窗%d' % (i + 1), 'front', R, cx, FLOORS[1][0], T)
        put_part(M, P, 'window', '三樓-窗%d' % (i + 1), 'front', R, cx, FLOORS[2][0] + 8, T)
    iron_balcony(M, 5, 75, 3, Y0, FLOORS[1][0], brackets=(5, 41, 73))
    put_part(M, P, 'door', '後-門', 'back', R, 40, PL, T)
    for i, cx in enumerate((18, 62)):
        put_part(M, P, 'window', '後-一樓窗%d' % (i + 1), 'back', R, cx, PL + 9, T)
    for f in (1, 2):
        for i, cx in enumerate((22, 58)):
            put_part(M, P, 'window', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 8, T)
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': zt, 'p': 0.85, 'over': (3, 3, 8, 6)}])
    top = build_roof(M, F, salt=71)
    free_part(M, P, 'dormer', '老虎窗', (33, Y0 + 3, top[(40, Y0 + 4)] - 1))
    free_part(M, P, 'chimney', '煙囪', (62, Y1 - 18, zt - 7))
    FRH.yard(M, X0, Y1, X1, 120, 3, 22, OCHRE, gate=(56, 13, 19))
    FRH.kitchen(M, (X0 + 3, 92, 34, 117), OCHRE, 'right', 104, vent_face='front', vent_c=18, low='right', chim=(6, 108, 2), salt=72)
    M.models += [model(LANTERN, '燈籠-門', (46.5, Y0, 24.5)), model(BARREL, '酒桶-院', (66, 103, 0))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-m-b', 'variant': 'm-b', 'level': 2, 'live': 8,
            'title': '中密度住宅 M-B（原地升級：低密度同一塊 8 × 12 蓋三層 —— 窄的城中屋，一樓店面＋正門、二樓落地窗＋鐵陽台、三樓、老虎窗；後院院牆＋廚房；土黃牆綠百葉）',
            'use': 'house', 'lot': (8, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂'}}


def house_h_b():
    """高密度 H-B（原地升級用，TASK-0895）：中密度同一塊 12 × 12 地塊上蓋四層 —— M-A 的臨街屋加一層、屋身深 0.6 m；後院縮成 4 m。"""
    M = Model((120, 120, 172))
    M.shutter = SH_GREY
    X0, Y0, X1, Y1 = 3, 12, 117, 78
    R = (X0, Y0, X1, Y1)
    zt = storeys(M, R, 4, CREAM, salt=81)
    P = FR_PARTS
    put_part(M, P, 'cartdoor', '前-車馬門', 'front', R, 22, PL, T)
    put_part(M, P, 'door', '前-門', 'front', R, 60, PL, T)
    put_part(M, P, 'cartdoor', '前-店面', 'front', R, 98, PL, T)
    front_steps(M, 60, Y0)
    M.anchor('door', 60, Y0 - 1, PL)
    for i, cx in enumerate((18, 46, 74, 102)):
        put_part(M, P, 'frenchdoor', '二樓-落地窗%d' % (i + 1), 'front', R, cx, FLOORS[1][0], T)
        for f in (2, 3):
            put_part(M, P, 'window', '%d樓-窗%d' % (f + 1, i + 1), 'front', R, cx, FLOORS[f][0] + 8, T)
    iron_balcony(M, 5, 115, 3, Y0, FLOORS[1][0], brackets=(5, 42, 75, 113))
    put_part(M, P, 'cartdoor', '後-車馬門', 'back', R, 22, PL, T)
    put_part(M, P, 'door', '後-門', 'back', R, 60, PL, T)
    put_part(M, P, 'window', '後-一樓窗', 'back', R, 95, PL + 9, T)
    for f in (1, 2, 3):
        for i, cx in enumerate((25, 60, 95)):
            put_part(M, P, 'window', '後-%d樓窗%d' % (f + 1, i + 1), 'back', R, cx, FLOORS[f][0] + 8, T)
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': zt, 'p': 0.85, 'over': (3, 3, 8, 5)}])
    top = build_roof(M, F, salt=81)
    for i, cx in enumerate((32, 60, 88)):
        free_part(M, P, 'dormer', '老虎窗%d' % (i + 1), (cx - 7, Y0 + 3, top[(cx, Y0 + 4)] - 1))
    free_part(M, P, 'chimney', '煙囪1', (8, Y1 - 22, zt - 7))
    free_part(M, P, 'chimney', '煙囪2', (104, Y1 - 22, zt - 7))
    FRH.yard(M, X0, Y1, X1, 120, 3, 22, CREAM, gate=(96, 13, 19))   # 後院 4 m：院牆＋後門、水井（廚房放不下）
    well(M, 60, 104)
    M.models += [model(LANTERN, '燈籠-門', (48.5, Y0, 24.5)), model(BARREL, '酒桶-院1', (84, 100, 0)), model(BARREL, '酒桶-院2', (84, 107, 0))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'house-h-b', 'variant': 'h-b', 'level': 3, 'live': 13,
            'title': '高密度住宅 H-B（原地升級：中密度同一塊 12 × 12 蓋四層 —— 一樓車馬門、正門、店面；二樓落地窗＋通長鐵陽台；三四樓；老虎窗；後院院牆＋水井；米白牆灰百葉）',
            'use': 'house', 'lot': (12, 12), 'M': M, 'layers': {'body': '牆身', 'gallery': '陽台', 'roof': '屋頂'}}


ALL = [house_m_a, house_h_a, house_m_b, house_h_b]
# 配色變化（設計決定）：M-A 換土黃牆藍百葉、H-A 換藍牆綠百葉（H-A 的藍百葉是部件關聯換的 49:42 ⇒ 外層看到的是 42）
VARIANTS = [('house-m-a2', 'house-m-a', {SALMON: OCHRE, SH_GREEN: SH_BLUE}, '中密度住宅 M-A2（M-A 的配色變化：土黃牆、藍百葉；替換色，不另存格子）'),
            ('house-h-a2', 'house-h-a', {CREAM: BLUE, SH_BLUE: SH_GREEN}, '高密度住宅 H-A2（H-A 的配色變化：藍牆、綠百葉；替換色，不另存格子）'),
            ('house-m-b2', 'house-m-b', {OCHRE: SALMON, SH_GREEN: SH_RED}, '中密度住宅 M-B2（M-B 的配色變化：鮭粉牆、紅百葉；替換色，不另存格子）'),
            ('house-h-b2', 'house-h-b', {CREAM: OCHRE, SH_GREY: SH_GREEN}, '高密度住宅 H-B2（H-B 的配色變化：土黃牆、綠百葉；替換色，不另存格子）')]
