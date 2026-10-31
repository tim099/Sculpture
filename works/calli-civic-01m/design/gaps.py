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

# ─────────────────────────────── 加勒比海的學校（école）12 × 10 m ───────────────────────────────
def desk(M, x0, x1, y0, y1, zb, h, top=FLOOR, layer='body'):
    """一張桌（或長凳）：四角的腳從 zb 立到 zb ＋ h、頂一片板。"""
    for x, y in ((x0, y0), (x1 - 2, y0), (x0, y1 - 2), (x1 - 2, y1 - 2)):
        M.box(layer, x, y, zb, x + 2, y + 2, zb + h, FRAME)
    M.box(layer, x0, y0, zb + h, x1, y1, zb + h + 1, top)


BOOKS = (160, 100, SH_GREEN, SH_BLUE, DARK, 136)   # 書背：紅、褐、綠、藍、黑、牛皮


def book_row(M, x0, x1, y0, y1, z, salt=0, axis='x'):
    """一排立著的書（一本 1 格寬、高 3～4 格；色照雜湊）。"""
    n = (x1 - x0) if axis == 'x' else (y1 - y0)
    for i in range(n):
        if h01('bk', i, z, salt) < 0.12:
            continue
        c = BOOKS[int(h01('bc', i, z, salt) * len(BOOKS)) % len(BOOKS)]
        hh = 3 + (h01('bh', i, z, salt) < 0.5)
        if axis == 'x':
            M.box('body', x0 + i, y0, z, x0 + i + 1, y1, z + hh, c)
        else:
            M.box('body', x0, y0 + i, z, x1, y0 + i + 1, z + hh, c)


def carib_school():
    """加勒比海的學校（petite école）：毛石台基上一間釘板的教室（10 × 5 m）、木瓦四坡頂、前廊與三級台階、雙扇門、開著木板百葉的窗（街上看得到裡面）；
    裡面左端一座講台（老師的桌椅）、牆上木十字、書架；學生的長桌與長凳四排面向講台、桌上攤著書；後院木柵、一副吊鐘的木架、長凳、水桶。
    - 照什麼：牆、屋頂、門廊、門窗全照 summit-carib-01m 的住宅 A（同一套木構）；17 世紀法屬島上的孩子多半由教士或修會教讀寫與教理〔摘：通說〕。
    - 設計：當年島上的學校長什麼樣子〔沒查到〕⇒ 平面、講台、四排桌凳、吊鐘架全部是設計（17 世紀還沒有黑板 ⇒ 不放）。"""
    X, Y, Z = 120, 100, 80
    M = Model((X, Y, Z))
    X0, Y0, X1, Y1, GY0 = 10, 26, 110, 76, 12
    R, t, fl = (X0, Y0, X1, Y1), 2, 6
    rubble_walls(M, (X0, GY0, X1, Y1), 0, fl - 1, 4, salt=3301)      # 毛石台基（含前廊底下）
    M.box('body', X0 + 4, GY0 + 4, 0, X1 - 4, Y1 - 4, fl - 1, EARTH_W)
    M.box('body', X0, Y0, fl - 1, X1, Y1, fl, FLOOR)
    board_walls(M, R, fl, 37, t)
    M.box('gallery', X0, GY0, fl - 1, X1, Y0, fl, FLOOR)
    put_part(M, 'door-double', '前-大門', 'front', R, 60, fl, t)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 60, fl, t)
    for i, cx in enumerate((26, 94)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, fl + 7, t)
    for i, cx in enumerate((24, 90)):
        put_part(M, 'window-board', '後-窗%d' % (i + 1), 'back', R, cx, fl + 7, t)
    put_part(M, 'window-board', '右-窗', 'right', R, (Y0 + Y1) // 2, fl + 7, t)
    steps(M, 52, 68, GY0, 3, 2, 3, back=False, layer='body', color=RUBBLE)
    steps(M, 54, 66, Y1, 3, 2, 3, back=True, layer='body', color=RUBBLE)
    M.anchor('door', 60, Y0 - 1, fl)
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 37, 'p': 0.8, 'over': (4, 4, Y0 - GY0 + 3, 4), 'kick': {'front': 0.45}}], salt=3302)
    gallery_posts(M, (X0, 34, 84, X1 - 2), GY0, fl, top)
    desk(M, 16, 40, 14, 17, fl, 3, layer='gallery')                    # 前廊靠左一條長凳（等上課的孩子）
    # 講台（左端）：老師的桌椅；左牆上木十字；後牆角的書架
    zp = fl + 3
    M.box('body', X0 + t, 30, fl, 34, 68, zp, FLOOR)
    desk(M, 18, 28, 42, 60, zp, 7)
    book_row(M, 20, 26, 44, 47, zp + 8, salt=1)
    M.box('body', 14, 48, zp, 17, 54, zp + 4, FRAME)                    # 椅子：座、靠背（老師面向 +x 的學生）
    M.box('body', 13, 48, zp + 4, 17, 54, zp + 5, FLOOR)
    M.box('body', 13, 48, zp + 5, 14, 54, zp + 12, FRAME)
    M.box('body', X0 + t, 50, fl + 16, X0 + t + 1, 52, fl + 27, FRAME)  # 木十字
    M.box('body', X0 + t, 47, fl + 22, X0 + t + 1, 55, fl + 24, FRAME)
    S = (14, 70, 32, 74)                                                # 書架（靠後牆）
    for x in (S[0], S[2] - 2):
        M.box('body', x, S[1], fl, x + 2, S[3], fl + 24, FRAME)
    for i, z in enumerate((fl, fl + 6, fl + 12, fl + 18, fl + 24)):
        M.box('body', S[0], S[1], z, S[2], S[3], z + 1, FLOOR)
        if z < fl + 24:
            book_row(M, S[0] + 2, S[2] - 2, S[1] + 1, S[3], z + 1, salt=10 + i)
    # 學生：四排長桌＋長凳（面向講台 ⇒ 桌在 x 小的那一邊、凳在後面），桌上攤著書
    for r, x in enumerate((42, 58, 74, 90)):
        desk(M, x, x + 4, 36, 66, fl, 6)
        desk(M, x + 7, x + 10, 36, 66, fl, 3)
        for j, y in enumerate((39, 47, 55, 61)):
            if h01('ob', r, j) < 0.7:
                M.box('body', x + 1, y, fl + 7, x + 3, y + 3, fl + 8, BOOKS[(r + j) % len(BOOKS)])
                M.box('body', x + 1, y + 1, fl + 7, x + 3, y + 2, fl + 8, LIME)   # 攤開的書頁
    # 後院：木柵、吊鐘的木架、長凳、水桶
    yb = Y - 2
    palisade(M, [(X0, Y1), (1, Y1), (1, yb), (X - 2, yb), (X - 2, Y1), (X1 - 1, Y1)], gap={(x, yb) for x in range(54, 66)})
    for x in (92, 104):
        M.box('body', x, 86, 0, x + 2, 88, 30, FRAME)
    M.box('body', 90, 86, 30, 108, 88, 32, FRAME)
    bell_at(M, 99, 87, 30)
    bench(M, 14, 40, 86, 89)
    M.models += [{'name': '燈籠-廊', 'source': 'summit-rocher-01m-lantern', 'at': [46.5, Y0, 22.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '水桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [74, 86, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    M.anchor('lot-0', 0, 0, 0)
    # 工作點（BUILDING_SPEC §5；服務 ＝ 菜單最多人的那道 jobs 2 × 二級 mult 2 ＝ 4 ＋ 1）：a 講台（台前、桌旁），b 兩條走道（前、後），c 書架前
    for nm, at, to in (('a1', (30, 38, zp), (44, 38, fl + 14)), ('a2', (36, 52, fl), (50, 52, fl + 12)), ('b1', (66, 31, fl), (66, 50, fl + 8)),
                       ('b2', (82, 69, fl), (82, 50, fl + 8)), ('c1', (23, 66, zp), (23, 72, fl + 14))):
        M.anchor('work-' + nm, *at)
        M.anchor('work-%s-to' % nm, *to)
    return {'key': 'carib-school', 'style': 'carib',
            'title': '加勒比海的學校（petite école：毛石台基、釘板教室、木瓦四坡頂、前廊與台階、開著百葉的窗；講台、老師的桌椅、木十字、書架、四排長桌長凳；後院木柵、吊鐘木架）',
            'use': 'school', 'lot': (12, 10), 'M': M, 'layers': {'body': '教室與後院', 'gallery': '前廊', 'roof': '屋頂'}}


# ─────────────────────────────── 英國、西班牙的學校 12 × 10 m（TASK-1135）───────────────────────────────
#   平面同 carib-school（左端講台、四排長桌長凳面向講台、書架、後院吊鐘）⇒ 換成各自那一套的牆、屋頂、門窗與擺設；工作點同 5 點。
def school_room(M, X0, Y0, X1, Y1, t, zf):
    """教室裡面：左端講台（老師的桌椅）、前牆左角的書架、四排長桌＋長凳（面向講台）、桌上攤著書。回傳講台面 zp。"""
    zp = zf + 3
    M.box('body', X0 + t, Y0 + t + 4, zf, 34, Y1 - t - 4, zp, FLOOR)
    desk(M, 18, 28, 38, 54, zp, 7)
    book_row(M, 20, 26, 40, 43, zp + 8, salt=21)
    M.box('body', X0 + t + 1, 43, zp, X0 + t + 4, 49, zp + 4, FRAME)          # 椅子：座、靠背（老師面向 +x 的學生）
    M.box('body', X0 + t, 43, zp + 4, X0 + t + 4, 49, zp + 5, FLOOR)
    M.box('body', X0 + t, 43, zp + 5, X0 + t + 1, 49, zp + 12, FRAME)
    S = (X0 + t, Y0 + t, X0 + t + 18, Y0 + t + 4)                         # 書架（前牆左角）
    for x in (S[0], S[2] - 2):
        M.box('body', x, S[1], zf, x + 2, S[3], zf + 24, FRAME)
    for i, z in enumerate((zf, zf + 6, zf + 12, zf + 18, zf + 24)):
        M.box('body', S[0], S[1], z, S[2], S[3], z + 1, FLOOR)
        if z < zf + 24:
            book_row(M, S[0] + 2, S[2] - 2, S[1], S[3] - 1, z + 1, salt=30 + i)
    for r, x in enumerate((42, 58, 74, 90)):
        desk(M, x, x + 4, Y0 + t + 7, Y1 - t - 8, zf, 6)
        desk(M, x + 7, x + 10, Y0 + t + 7, Y1 - t - 8, zf, 3)
        for j, y in enumerate((Y0 + t + 9, Y0 + t + 16, Y0 + t + 23, Y0 + t + 29)):
            if h01('ob', r, j, 7) < 0.7:
                M.box('body', x + 1, y, zf + 7, x + 3, y + 3, zf + 8, BOOKS[(r + j + 2) % len(BOOKS)])
                M.box('body', x + 1, y + 1, zf + 7, x + 3, y + 2, zf + 8, LIME)
    return zp


def school_work(M, Y0, Y1, t, zf, zp):
    """工作點（BUILDING_SPEC §5；同 carib-school：服務 jobs 2 × 二級 mult 2 ＝ 4 ＋ 1）：a 講台（台前、台邊），b 兩條走道（前、後），c 書架前。"""
    ya, yb = Y0 + t + 2, Y1 - t - 3
    for nm, at, to in (('a1', (30, 36, zp), (44, 36, zf + 12)), ('a2', (37, 46, zf), (50, 46, zf + 10)), ('b1', (66, ya, zf), (66, 46, zf + 8)),
                       ('b2', (82, yb, zf), (82, 46, zf + 8)), ('c1', (22, Y0 + t + 6, zp), (22, Y0 + t + 1, zf + 14))):
        M.anchor('work-' + nm, *at)
        M.anchor('work-%s-to' % nm, *to)


def en_school():
    """英國的學校（petty school）：磚造一間教室（10 × 5.2 m、牆高 3.6 m）、紅瓦四坡頂；正面雙扇門、門前磚鋪小路、前後各兩扇窗、兩側各一扇；
    裡面磚鋪地、左端講台（老師的桌椅）、講台後面的後牆上十誡與主禱文的板、前牆左角書架、四排長桌長凳面向講台、桌上攤著書；後院磚牆、木架吊一口鐘、長凳、水桶。
    - 照什麼：磚牆紅瓦同 ame 的 english.py（皇家港「goodly Brick Houses」）；英國國教的學校在牆上掛十誡與主禱文的板、不掛十字架〔摘：同 en-chapel 的通法〕。
    - 設計：英屬加勒比 1660 年代的學校長什麼樣子〔沒查到〕⇒ 平面、講台、桌凳、吊鐘架全部是設計（還沒有黑板 ⇒ 不放）。"""
    X, Y, Z = 120, 100, 80
    M = Model((X, Y, Z))
    R = (10, 20, 110, 72)
    t, H = 4, 36
    M.box('body', 50, 0, 0, 70, R[1], 1, PAVE)                          # 門前磚鋪小路
    brick_walls(M, R, 0, H, t, salt=3501)
    M.box('body', R[0] + t, R[1] + t, 0, R[2] - t, R[3] - t, 1, PAVE)
    put_part(M, 'door-double', '前-門', 'front', R, 60, 0, t)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 60, 0, t)
    for i, cx in enumerate((40, 86)):
        put_part(M, 'window', '前-窗%d' % (i + 1), 'front', R, cx, 10, t)
    for i, cx in enumerate((28, 90)):
        put_part(M, 'window', '後-窗%d' % (i + 1), 'back', R, cx, 10, t)
    for f in ('left', 'right'):
        put_part(M, 'window', '%s-窗' % {'left': '左', 'right': '右'}[f], f, R, 46, 10, t)
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.6, 'over': (3, 3, 4, 3)}], salt=3502)
    zp = school_room(M, *R, t, 1)
    tablet(M, 15, 23, R[3] - t - 1, 14, 30)                             # 十誡（左）、主禱文（右）：講台後面的後牆
    tablet(M, 34, 42, R[3] - t - 1, 14, 30)
    # 後院：三面磚牆（後牆中間開口）、吊鐘的木架、長凳、水桶
    for (x0, y0, x1, y1) in ((10, R[3], 14, 98), (106, R[3], 110, 98)):
        brick_walls(M, (x0, y0, x1, y1), 0, 18, 4, salt=3503 + x0)
    for (x0, x1) in ((10, 54), (66, 110)):
        brick_walls(M, (x0, 94, x1, 98), 0, 18, 4, salt=3510 + x0)
    for x in (88, 100):
        M.box('body', x, 84, 0, x + 2, 86, 30, FRAME)
    M.box('body', 86, 84, 30, 104, 86, 32, FRAME)
    bc = bell_at(M, 95, 85, 30)
    bench(M, 18, 44, 84, 87)
    M.models += [{'name': '燈籠-門', 'source': 'summit-rocher-01m-lantern', 'at': [46.5, R[1], 24.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}},
                 {'name': '水桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [72, 82, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    yield_to_parts(M)
    M.anchor('door', 60, R[1] - 1, 1)                                     # 門前的鋪面上一格
    M.anchor('bell', *bc)
    M.anchor('lot-0', 0, 0, 0)
    school_work(M, R[1], R[3], t, 1, zp)
    return {'key': 'en-school', 'style': 'en',
            'title': '英國的學校（petty school：磚造一間教室、紅瓦四坡頂、雙扇門與平開窗、門前磚鋪小路；講台、老師的桌椅、十誡與主禱文的板、書架、四排長桌長凳；後院磚牆、吊鐘木架）',
            'use': 'school', 'lot': (12, 10), 'M': M, 'layers': {'body': '教室與後院', 'roof': '屋頂'}}


def es_school():
    """西班牙的學校（escuela de primeras letras）：刷白砌石一間教室（10 × 5.2 m、牆高 4 m）、紅陶瓦兩坡頂、兩端刷白山牆；正面牆上一座小鐘牆（espadaña）掛一口鐘；
    切石門框的雙扇門、木欄杆窗；裡面陶磚地、左端講台（老師的桌椅）、左牆上木十字、前牆左角書架、四排長桌長凳面向講台；後院砌石牆、蓄水池井口、長凳、水桶；門前卵石。
    - 照什麼：牆、屋頂、鐘牆、門框、窗全照 basecamp 的 es.py（同一套的小堂、醫院）；西屬城鎮的讀寫課（primeras letras）多半由修會或教區開〔摘：通說〕。
    - 設計：哈瓦那、聖多明哥 1660 年代的學校長什麼樣子〔沒查到〕⇒ 平面、鐘牆的位置、講台、桌凳全部是設計（還沒有黑板 ⇒ 不放）。"""
    X, Y, Z = 120, 100, 100
    M = Model((X, Y, Z))
    R = (10, 20, 110, 72)
    t, H = 4, 40
    cobbles(M, 0, 0, X, R[1], salt=3601)
    masonry(M, R, 0, H, t, plinth=5, salt=3602)
    tile_floor(M, R[0] + t, R[1] + t, R[2] - t, R[3] - t)
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.55, 'over': (3, 3, 4, 4), 'gable': 'x'}], salt=3603)
    for x0, x1 in ((R[0], R[0] + t), (R[2] - t, R[2])):
        end_gable(M, x0, x1, R[1], R[3], H, 0.55, z0=H, color=CAL, edge=CORAL)
    bc, zt = espadana(M, 86, R[1], R[1] + t, H - 1, w=16, steps=((0, 16), (16, 8), (22, 4)), arch=(8, 4, 7))
    put_part(M, 'door-double', '前-門', 'front', R, 60, 0, t)
    portal(M, R, 60, 20, 27, salt=3604)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 60, 0, t)
    for i, cx in enumerate((34, 86)):
        put_part(M, 'window-baluster', '前-窗%d' % (i + 1), 'front', R, cx, 14, t)
    for i, cx in enumerate((28, 90)):
        put_part(M, 'window-baluster', '後-窗%d' % (i + 1), 'back', R, cx, 14, t)
    put_part(M, 'window-baluster', '右-窗', 'right', R, 46, 14, t)
    zp = school_room(M, *R, t, 1)
    M.box('body', R[0] + t, 45, 16, R[0] + t + 1, 47, 30, FRAME)        # 左牆上的木十字
    M.box('body', R[0] + t, 42, 24, R[0] + t + 1, 50, 26, FRAME)
    # 後院：砌石牆（後牆中間開口）、蓄水池井口、長凳、水桶
    for (x0, y0, x1, y1) in ((10, R[3], 14, 98), (106, R[3], 110, 98)):
        masonry(M, (x0, y0, x1, y1), 0, 20, 4, plinth=3, salt=3605 + x0)
    for (x0, x1) in ((10, 54), (66, 110)):
        masonry(M, (x0, 94, x1, 98), 0, 20, 4, plinth=3, salt=3610 + x0)
    aljibe(M, 92, 84, 6, 8)
    bench(M, 18, 44, 84, 87)
    M.models += [{'name': '水桶-院', 'source': 'summit-rocher-01m-barrel', 'at': [72, 82, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-門', (46.5, R[1], 26))
    yield_to_parts(M)
    M.anchor('door', 60, R[1] - 1, 1)                                     # 門前的鋪面上一格
    M.anchor('bell', *bc)
    M.anchor('lot-0', 0, 0, 0)
    school_work(M, R[1], R[3], t, 1, zp)
    return {'key': 'es-school', 'style': 'es',
            'title': '西班牙的學校（escuela de primeras letras：刷白砌石一間教室、紅陶瓦兩坡頂、正面小鐘牆掛一口鐘、切石門框的雙扇門、木欄杆窗；講台、老師的桌椅、木十字、書架、四排長桌長凳；後院砌石牆、蓄水池井口）',
            'use': 'school', 'lot': (12, 10), 'M': M, 'layers': {'body': '教室與後院', 'roof': '屋頂'}}


ALL = [en_chapel, en_jail, es_battery, carib_school, en_school, es_school]
