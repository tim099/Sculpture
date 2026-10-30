# 補缺的城鎮建築（calli 2026-10-31；Tim「布里奇敦（英屬）的小教堂、監獄，巴拉科阿（西屬）的砲台，也缺模型 那補上模型吧 GO」）：
#   en 小教堂、en 監獄（布里奇敦挑模型的退路 en ⇒ common ⇒ fr 都沒有）、es 砲台（巴拉科阿 es ⇒ common ⇒ fr 都沒有）。
# 工具全部借別人的產生程式 ⇒ 跟同一套的建築站在一起不突兀：
#   en ＝ ame-carib-civic-01m 的 english.py（磚牆、紅瓦、陽台）＋ trailhead-harbour-01m 的 forts.py（battery_en 的擺法）；
#   es ＝ basecamp-es-01m 的 es.py（刷白砌石、切石、鐘牆、哨亭）。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料與設計的分界：
#   〔摘〕英屬加勒比的城是磚造、紅瓦（皇家港：HEATH「goodly Brick Houses」，ame 的研究 research_civic.md §10）；英國國教的堂裡是講台（pulpit）、聖餐桌與欄杆、
#        牆上十誡與主禱文的板（1560 年代起規定要掛）；英國城鎮的監獄門前常有枷（stocks）—— 這幾樣是英國本土的通法，布里奇敦當年的樣子〔沒查到〕。
#   〔設計〕三棟的平面、尺寸、木鐘樓、枷的位置、砲台的哨亭全部。西班牙砲台照 trailhead 的英國砲台（battery_en）同一套擺法，換成 es 的刷白砌石與切石（es.py 的牆與 garita）。
import math
from es import *                                                       # noqa: F401,F403  es 的全部（masonry、portal、garita、tile_floor…）＋ forts／town3／civic／carib
from english import brick_walls, BRICK_A, BRICK_B, BRICK_M, PAVE       # noqa: E402
from townpub import bench                                              # noqa: E402

STONE_G = 182                    # 灰的石（墓碑、十誡板的底）
LETTER = DARK                    # 板上的字（一道一道深色）


def brick_color(x, y, z, z0=0, salt=0):
    """同 english.brick_walls 的配色（一皮 1 格、每 3 皮一道灰縫、豎縫錯開）—— 山牆、煙囪這些不是一圈牆的地方用。"""
    row = (z - z0) // 3
    u = x + y + (2 if row % 2 else 0)
    if (z - z0) % 3 == 2 or u % 5 == 0:
        return BRICK_M
    return BRICK_B if h01('bk', u // 5, row, salt) < 0.3 else BRICK_A


def brick_gable(M, x0, x1, y0, y1, ze, p, over=3, salt=0, layer='body'):
    """磚的山牆（屋脊沿 y）：x ∈ [x0, x1)、牆厚 y ∈ [y0, y1)；頂 ＝ ze ＋ p × 離最近一邊 ＋ over（高出屋面、蓋住瓦的斷面）；頂上一格灰的壓頂。"""
    for x in range(x0, x1):
        d = min(x + 0.5 - x0, x1 - x - 0.5)
        zt = int(math.floor(ze + p * d)) + over
        for z in range(ze, zt + 1):
            for y in range(y0, y1):
                M.put(layer, x, y, z, BRICK_M if z == zt else brick_color(x, y, z, 0, salt), force=True)


def bell_at(M, xa, yc, ztop, half_y=2, layer='body'):
    """一口鐘（同 es.espadana 的鐘）：鐵桿吊在 ztop（實心的那一層）底下。回傳鐘的中心。"""
    M.box(layer, xa - 1, yc, ztop - 3, xa + 1, yc + 1, ztop, IRON, force=True)
    for z in range(ztop - 10, ztop - 3):
        rr = 1 + (ztop - 3 - z) // 2
        for x in range(xa - rr - 1, xa + rr + 1):
            for y in range(yc - min(rr, half_y), yc + min(rr, half_y) + 1):
                M.put(layer, x, y, z, BRONZE, force=True)
    return (xa, yc, ztop - 7)


def tablet(M, x0, x1, y, z0, z1):
    """十誡／主禱文的板（木框、灰底、一道一道深色的字）：貼在牆上（y 那一排）。"""
    for x in range(x0, x1):
        for z in range(z0, z1):
            edge = x in (x0, x1 - 1) or z in (z0, z1 - 1)
            line = not edge and (z - z0) % 3 == 1 and x0 + 2 <= x < x1 - 2
            M.put('body', x, y, z, FRAME if edge else (LETTER if line else STONE_G), force=True)


def stocks(M, x0, y0):
    """枷（stocks）：兩根柱、上下兩片厚板夾著（三個腳洞）、前面一條長凳。佔 x0..x0+20、y0..y0+8。"""
    for x in (x0, x0 + 18):
        M.box('body', x, y0 + 4, 0, x + 2, y0 + 6, 12, FRAME)
    M.box('body', x0 + 2, y0 + 4, 3, x0 + 18, y0 + 6, 6, FRAME)
    M.box('body', x0 + 2, y0 + 4, 7, x0 + 18, y0 + 6, 10, FRAME)
    for x in (x0 + 5, x0 + 9, x0 + 13):
        M.box('body', x, y0 + 4, 6, x + 2, y0 + 6, 7, DARK)
    M.box('body', x0 + 1, y0, 4, x0 + 19, y0 + 2, 5, FLOOR)
    for x in (x0 + 2, x0 + 16):
        M.box('body', x, y0, 0, x + 2, y0 + 2, 4, FRAME)


def brick_well(M, cx, cy, r=6, h=8):
    """井（磚砌的圓井欄、深色的井口、兩根柱＋橫梁的轆轤）—— 設計。"""
    for x in range(cx - r - 1, cx + r + 1):
        for y in range(cy - r - 1, cy + r + 1):
            d2 = (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2
            if d2 <= r * r:
                for z in range(0, h):
                    M.put('body', x, y, z, DARK if d2 <= (r - 2) ** 2 and z > 0 else brick_color(x, y, z, 0, 77), force=True)
    for x in (cx - r, cx + r - 2):
        M.box('body', x, cy - 1, h, x + 2, cy + 1, h + 14, FRAME)
    M.box('body', cx - r, cy - 1, h + 14, cx + r, cy + 1, h + 16, FRAME)
    M.box('body', cx, cy, h + 2, cx + 1, cy + 1, h + 14, IRON)


# ─────────────────────────────── 英國小教堂（chapel of ease）8 × 12 m ───────────────────────────────
def en_chapel():
    """英國的小教堂（chapel of ease：教區教堂太遠的地方另蓋的一間）：磚造一間 5.6 × 9.2 m、牆高 4 m、紅瓦兩坡頂（屋脊沿進深）、前後兩面磚山牆；
    正面山牆的屋脊上一座刷白的木鐘樓（下段封板、上段四根柱開敞掛一口鐘、四坡尖頂、頂上風向標）；正面雙扇門、門上一扇窗，兩側各兩扇、後牆一扇平開窗；
    裡面磚鋪地、後面高一階的聖壇：聖餐桌三面圍欄杆、兩側牆上十誡與主禱文的板；右前的木講台（上面一片傘蓋）、兩列四排長凳；
    門前磚鋪的小路、兩側墓園的四塊墓碑。"""
    X, Y, Z = 80, 120, 100
    M = Model((X, Y, Z))
    R = (12, 16, 68, 108)                                              # 5.6 × 9.2 m
    t, H, p = 4, 40, 0.6
    M.box('body', 34, 0, 0, 46, R[1], 1, PAVE)                         # 門前的磚鋪小路
    brick_walls(M, R, 0, H, t, salt=3101)
    M.box('body', R[0] + t, R[1] + t, 0, R[2] - t, R[3] - t, 1, PAVE)
    top = tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': p, 'over': (3, 3, 0, 0), 'gable': 'y'}], salt=3102)
    brick_gable(M, R[0], R[2], R[1], R[1] + t, H, p, over=2, salt=3103)
    brick_gable(M, R[0], R[2], R[3] - t, R[3], H, p, over=2, salt=3104)
    put_part(M, 'door-double', '前-門', 'front', R, 40, 0, t)
    put_part(M, 'window', '前-門上窗', 'front', R, 40, 46, t)
    for i, cy in enumerate((46, 80)):
        put_part(M, 'window', '左-窗%d' % (i + 1), 'left', R, cy, 14, t)
        put_part(M, 'window', '右-窗%d' % (i + 1), 'right', R, cy, 14, t)
    put_part(M, 'window', '後-窗', 'back', R, 40, 16, t)
    # ── 聖壇：高一階、聖餐桌、三面欄杆、十誡與主禱文的板 ──
    M.box('body', R[0] + t, 84, 1, R[2] - t, R[3] - t, 3, PAVE)
    M.box('body', 32, 94, 3, 48, 100, 11, FRAME)                         # 聖餐桌
    M.box('body', 31, 93, 11, 49, 101, 12, LIME)                         # 桌布
    for (x0, y0, x1, y1) in ((24, 88, 56, 89), (24, 88, 25, 102), (55, 88, 56, 102)):   # 欄杆（正面中間留口）
        for x in range(x0, x1):
            for y in range(y0, y1):
                if y0 == 88 and y1 == 89 and 37 <= x < 43:
                    continue
                M.box('body', x, y, 3, x + 1, y + 1, 9 if (x + y) % 3 == 0 else 3, FRAME)
                M.put('body', x, y, 9, FRAME)
    tablet(M, 20, 32, R[3] - t - 1, 14, 34)                             # 十誡（左）、主禱文（右）：窗兩側
    tablet(M, 48, 60, R[3] - t - 1, 14, 34)
    # ── 講台（pulpit）：右前、木箱高 1.4 m、後面一根柱撐傘蓋（sounding board） ──
    M.box('body', 54, 60, 1, 62, 68, 14, FRAME)
    M.box('body', 53, 59, 14, 63, 69, 15, FLOOR)
    M.box('body', 62, 63, 1, 64, 65, 30, FRAME)
    M.box('body', 52, 58, 30, 64, 70, 32, FRAME)
    # ── 長凳：兩列四排（中間走道） ──
    for y in (32, 44, 56, 68):
        bench(M, 20, 36, y, y + 3)
        if y < 56:
            bench(M, 44, 60, y, y + 3)
    # ── 墓園：路兩側各兩塊墓碑 ──
    for x in (16, 24, 52, 60):
        M.box('body', x, 6, 0, x + 5, 7, 6, STONE_G)
        M.box('body', x + 1, 6, 6, x + 4, 7, 7, STONE_G)
    # ── 木鐘樓：正面那一端的屋脊上 ──
    yb0, yb1 = R[1] + 3, R[1] + 13
    xb0, xb1 = 34, 46
    zb = max(top[(x, y)] for x in range(xb0, xb1) for y in range(yb0, yb1))
    M.box('body', xb0, yb0, zb, xb1, yb1, zb + 10, LIME)                 # 下段：刷白的封板
    for x in range(xb0, xb1):                                           # 封板的橫縫
        for y in (yb0, yb1 - 1):
            for z in (zb + 3, zb + 6):
                M.put('body', x, y, z, FRAME, force=True)
    M.box('body', xb0, yb0, zb + 10, xb1, yb1, zb + 11, FRAME)
    for (x, y) in ((xb0, yb0), (xb1 - 2, yb0), (xb0, yb1 - 2), (xb1 - 2, yb1 - 2)):   # 上段：四根柱
        M.box('body', x, y, zb + 11, x + 2, y + 2, zb + 22, LIME)
    M.box('body', xb0, yb0, zb + 22, xb1, yb1, zb + 24, FRAME)          # 柱頂的圈梁
    for i in range(0, 6):                                               # 四坡尖頂（深灰的鉛皮；進深 10 格 ⇒ 第 6 層收成一條脊）
        M.box('body', xb0 - 1 + i, yb0 - 1 + i, zb + 24 + i, xb1 + 1 - i, yb1 + 1 - i, zb + 25 + i, DARK)
    xm, ym = (xb0 + xb1) // 2, (yb0 + yb1) // 2
    M.box('body', xm - 1, ym - 1, zb + 30, xm + 1, ym + 1, zb + 38, IRON)   # 風向標的桿（立在尖頂的脊上）
    M.box('body', xm - 5, ym - 1, zb + 36, xm + 4, ym, zb + 37, IRON)
    M.box('body', xm + 2, ym - 1, zb + 37, xm + 4, ym, zb + 39, IRON)
    bc = bell_at(M, xm, ym, zb + 22)
    lantern(M, '燈籠-門左', (27.5, R[1], 26))
    yield_to_parts(M)
    M.anchor('door', 40, R[1] - 2, 1)
    M.anchor('bell', *bc)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'en-chapel', 'style': 'en',
            'title': '英國小教堂（chapel of ease：磚造一間、紅瓦兩坡頂、磚山牆、屋脊上刷白的木鐘樓掛一口鐘；聖餐桌與欄杆、十誡與主禱文的板、木講台、長凳；門前小路與墓碑）',
            'use': 'chapel', 'lot': (8, 12), 'M': M, 'layers': {'body': '磚牆、鐘樓與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 英國監獄（gaol）12 × 14 m ───────────────────────────────
def en_jail():
    """英國的監獄（gaol）：臨路一棟兩層的磚屋（樓下看守與牢門、樓上獄卒 keeper 住；10.8 × 5.2 m、兩層 6 m）、紅瓦四坡頂、一根煙囪；
    樓下鐵條窗、樓上平開窗；門旁一副枷（stocks）；後面磚砌高牆圍的放風院、院底三間單坡瓦頂的牢房（各一扇厚木門、後牆鐵條小窗）、院子裡一口井。
    - 照什麼：英國城鎮的監獄與枷〔摘：本土的通法〕；布里奇敦的監獄（cage、gaol）的樣子〔沒查到〕。
    - 設計：平面同 es 那一座（前屋、院、院底牢房）⇒ 磚、瓦、平開窗、枷換成英國的。"""
    X, Y, Z = 120, 140, 100
    M = Model((X, Y, Z))
    # 放風院的高牆
    brick_walls(M, (6, 60, 114, 136), 0, 40, 4, salt=3201)
    M.clear(10, 60, 0, 110, 64, 40)
    M.box('body', 10, 64, 0, 110, 132, 1, EARTH_W)
    for x in range(6, 114):                                             # 牆頂一皮灰的壓頂
        for y in range(132, 136):
            M.put('body', x, y, 40, BRICK_M)
    for y in range(64, 136):
        for x in list(range(6, 10)) + list(range(110, 114)):
            M.put('body', x, y, 40, BRICK_M)
    # 前屋：兩層
    R = (6, 12, 114, 64)
    t, H1, H = 4, 30, 60
    brick_walls(M, R, 0, H, t, salt=3202)
    M.box('body', R[0] + t, R[1] + t, 0, R[2] - t, R[3] - t, 1, PAVE)
    M.box('body', R[0] + t, R[1] + t, H1, R[2] - t, R[3] - t, H1 + 2, FLOOR)   # 樓板
    M.box('body', 58, R[1] + t, 1, 62, R[3] - t, H1, BRICK_A)           # 樓下的隔牆（左看守、右牢門）
    put_part(M, 'door-plank', '隔牆-門', 'left', (58, R[1] + t, 62, R[3] - t), 38, 0, 4)
    put_part(M, 'door-plank', '前-門', 'front', R, 60, 0, t)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 84, 0, t)
    for i, c in enumerate((24, 96)):
        barred(M, 'front', R, c, 12, 8, 10, t)
        put_part(M, 'window', '前-樓上窗%d' % (i + 1), 'front', R, c, 40, t)
    put_part(M, 'window', '前-樓上窗中', 'front', R, 60, 40, t)
    for f in ('left', 'right'):
        barred(M, f, R, 38, 12, 8, 8, t)
        put_part(M, 'window', '%s-樓上窗' % {'left': '左', 'right': '右'}[f], f, R, 38, 40, t)
    top = tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.6, 'over': (3, 3, 4, 3)}], salt=3203)
    free_part(M, 'chimney', '煙囪', (20, 46, top[(24, 49)] - 10))
    # 樓下：看守的桌凳、掛鐐銬的架
    trestle_table(M, 14, 34, 30, 40, 8)
    bench(M, 14, 34, 44, 47)
    M.box('body', 70, 52, 1, 72, 54, 20, FRAME)
    M.box('body', 104, 52, 1, 106, 54, 20, FRAME)
    M.box('body', 70, 52, 20, 106, 54, 22, FRAME)
    for x in range(74, 104, 6):
        M.box('body', x, 53, 12, x + 1, 54, 20, IRON)
        M.box('body', x - 1, 53, 11, x + 2, 54, 12, IRON)
    # 院底三間牢房：磚牆、單坡瓦頂（高的那一邊靠後牆）、各一扇厚木門、後牆高處鐵條小窗
    C = (10, 104, 110, 132)
    brick_walls(M, C, 0, 28, 4, salt=3204)
    for x0 in (42, 75):
        M.box('body', x0, C[1], 0, x0 + 4, C[3], 28, BRICK_A)
    shed_roof(M, C[0], C[1] - 3, C[2], C[3], 36, 0.25, low='front')
    for i, cx in enumerate((26, 59, 93)):
        put_part(M, 'door-plank', '牢房-門%d' % (i + 1), 'front', C, cx, 0, 4)
        barred(M, 'back', (6, 60, 114, 136), cx, 26, 6, 6, 4)
    brick_well(M, 90, 82, 6, 8)
    stocks(M, 76, 2)                                                    # 門右邊的枷（臨路）
    lantern(M, '燈籠-門', (46.5, R[1], 26.5))
    yield_to_parts(M)
    M.anchor('door', 60, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    # 工作點（BUILDING_SPEC §5；公職照 3 級城的 staff 4 ＋ 1）：a 看守那一間（桌前、窗前）、b 牢門那一間（鐐銬架前、兩扇窗前）
    for nm, at, to in (('a1', (24, 42, 1), (24, 35, 9)), ('a2', (30, 22, 1), (30, 15, 12)), ('b1', (88, 47, 1), (88, 53, 14)),
                       ('b2', (78, 30, 1), (78, 24, 10)), ('b3', (100, 30, 1), (106, 30, 10))):
        M.anchor('work-' + nm, *at)
        M.anchor('work-%s-to' % nm, *to)
    return {'key': 'en-jail', 'style': 'en',
            'title': '英國監獄（gaol：兩層磚屋、紅瓦四坡頂、煙囪、樓下鐵條窗、樓上平開窗、門旁一副枷；磚牆圍的放風院、院底三間單坡瓦頂的牢房、井）',
            'use': 'jail', 'lot': (12, 14), 'M': M, 'layers': {'body': '磚屋、院牆與牢房', 'roof': '屋頂'}}


# ─────────────────────────────── 西班牙砲台（batería）12 × 12 m ───────────────────────────────
def es_battery():
    """西班牙的小砲台（batería）：照 trailhead 的英國砲台（battery_en）同一套擺法 —— 正面一道切石胸牆（厚 1.6 m、高 2.4 m、壓頂）、三個外張砲眼、木砲床、三門 6 磅砲、
    左前角 1.2 m 的進出口、兩側刷白砌石的翼牆、背面開敞；換成 es 的：切石胸牆、右前角胸牆上一座圓形哨亭（garita）、後面一間刷白砌石的小火藥庫（紅陶瓦、切石門框）、旗杆。
    - 照什麼：西屬加勒比的砲台與哨亭（哈瓦那 Real Fuerza、garita 的說明，basecamp 的 es 研究）〔摘〕；這一座的形制〔設計〕。
    - 海戰用的 meta 同 battery_en：胸牆與砲床一層 kind=deck、火藥庫一層 kind=magazine、砲 gun=6l、桶 kind=powder；material=stone。"""
    M = Model((120, 120, 90))
    PY0, PY1, H, SILL, PLAT = 4, 20, 24, 12, 4
    guns = (30, 60, 88)
    for x in range(16, 116):                                            # 胸牆：整道切石
        for y in range(PY0, PY1):
            for z in range(0, H):
                M.put('rampart', x, y, z, coral_color(x, y, z, 0, 3301))
    masonry(M, (4, PY1 + 14, 14, 70), 0, H - 4, 10, layer='rampart', plinth=4, salt=3302)
    masonry(M, (106, PY1, 116, 70), 0, H - 4, 10, layer='rampart', plinth=4, salt=3303)
    M.box('rampart', 16, PY0, H - 1, 116, PY1, H, CORAL_J, force=True)          # 壓頂
    for cx in guns:                                                     # 外張的砲眼：裡面 0.8 m、外面 1.6 m
        for y in range(PY0, PY1):
            half = 4 + (PY1 - 1 - y) * 4 // (PY1 - PY0)
            for x in range(cx - half, cx + half):
                for z in range(SILL, H + 1):
                    M.cells.pop((x, y, z), None)
    garita(M, 107, 12, H, r=7, h=20, layer='rampart')                  # 右前角的哨亭（站在胸牆頂上）
    M.clear(105, 15, H + 1, 109, 20, H + 13, 'rampart')                 # 哨亭朝裡（砲台那一邊）的門洞
    for cx in guns:                                                     # 木砲床
        M.box('rampart', cx - 12, PY1, 0, cx + 12, PY1 + 34, PLAT - 1, FRAME)
        for x in range(cx - 12, cx + 12):
            if (x - cx) % 6:
                M.box('rampart', x, PY1, PLAT - 1, x + 1, PY1 + 34, PLAT, FLOOR)
        bx, by = cx + 13, PY1 + 22                                      # 砲彈堆
        for z, n in ((0, 3), (1, 2), (2, 1)):
            for i in range(n):
                for j in range(n):
                    M.box('body', bx + i * 2 + z, by + j * 2 + z, z, bx + i * 2 + z + 2, by + j * 2 + z + 2, z + 1, IRON)
    mr = (70, 84, 104, 112)
    masonry(M, mr, 0, 26, 4, layer='magazine', plinth=4, salt=3304)
    M.box('magazine', mr[0] + 4, mr[1] + 4, 0, mr[2] - 4, mr[3] - 4, 1, FLOOR_T)
    M.clear(81, mr[1], 0, 93, mr[1] + 4, 22, 'magazine')                 # 門洞（put_part 只挖 body 那幾層）
    put_part(M, 'door-plank', '火藥庫-門', 'front', mr, 87, 0, 4)
    tile_roof(M, [{'x0': mr[0], 'y0': mr[1], 'x1': mr[2], 'y1': mr[3], 'ze': 26, 'p': 0.7, 'over': (3, 3, 3, 3)}], salt=3305)
    ft, fb = flagpole_on(M, 22, 96, 0, 80)
    M.anchor('flag', 22, 96, 81)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 28, toward=1)]
    guns_m = [gun_model('砲%d' % (i + 1), cx, PY1 + 15, PLAT, 0, -1, '6l') for i, cx in enumerate(guns)]
    kegs = [powder_keg('火藥桶-%d' % (i + 1), x, 100, 1) for i, x in enumerate((80, 94))]
    lantern(M, '燈籠-火藥庫', (78.5, 84, 20))
    for L in M.links:
        for k in L['cells']:
            M.cells.pop(k, None)
    M.anchor('door', 9, 1, 0)                                           # 左前角的進出口（同 battery_en：正面朝港口、路從正面接進來）
    M.anchor('lot-0', 0, 0, 0)
    for nm, at, to in (('a1', (60, 25, 3), (60, 18, 12)), ('b1', (82, 25, 3), (88, 18, 12)), ('c1', (30, 25, 3), (30, 18, 12))):   # 工作點：每門砲後面砲床板縫那一格（同 battery_en）
        M.anchor('work-' + nm, *at)
        M.anchor('work-%s-to' % nm, *to)
    return {'key': 'es-battery', 'title': '西班牙砲台（batería：切石胸牆與刷白翼牆、三個外張砲眼、右前角的圓形哨亭、木砲床、三門 6 磅砲、刷白砌石的小火藥庫、旗杆）',
            'use': 'battery', 'lot': (12, 12), 'M': M, 'style': 'es', 'flags': flags,
            'layers': {'body': '砲彈堆與旗杆', 'rampart': '胸牆、哨亭與砲床（甲板）', 'magazine': '火藥庫', 'roof': '屋頂'},
            'layer_meta': {'rampart': {'kind': 'deck', 'deck': 'battery', 'level': 0, 'name': '砲床', 'floor': '0:%d,120:%d' % (PLAT, PLAT), 'thick': PLAT, 'material': 'stone'},
                           'magazine': {'kind': 'magazine', 'pos': 'mid', 'powder_lb': 100 * len(kegs), 'material': 'stone'}},
            'layer_anchors': {'magazine': {'blast': (87, 98, 10), 'door': (87, mr[1] - 1, 0)}},
            'layer_models': {'rampart': guns_m, 'magazine': kegs}}


ALL = [en_chapel, en_jail, es_battery]
