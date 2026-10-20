# 城牆模組（TASK-0741；TOWN_BUILD §4、建築規格 §5）：每一級 section（斷面，沿曲線一節一節拉）、tower、gate、joint、end。
# 座標：x ＝ 沿牆（曲線的切線方向）、y ＝ 橫過牆（−y ＝ 牆外、+y ＝ 城裡）、z ＝ 往上（z 0 ＝ 牆中線那一點的地面）。
#   中線 y ＝ Y/2（Y 取偶數）；z 0 那一層 ＝ base（遊戲往下延到地面）。
#   接口：wall-a 那一格的 −x 面、wall-b 那一格的 +x 面（都在中線、地面那一層）—— 牆身從那裡接進來。
#   城門另有 road-out／road-in：路從牆外、城裡接進門洞的兩點。
from kit import *

TIER_NAME = {1: '木柵', 2: '土堤＋木柵', 3: '石牆'}


def W(tier, part, title, size):
    M = Model(size)
    return M, {'key': 'wall%d-%s' % (tier, part), 'tier': tier, 'part': part, 'title': '城牆 %d 級（%s）｜%s' % (tier, TIER_NAME[tier], title), 'M': M}


def log(M, x0, y0, d, h, z0=0, salt=0, tip=3, color=None):
    """一根原木：截面 d×d 去掉四角（d ≥ 4）、頂端削尖 tip 層；樹皮色每根略有不同。"""
    c = color or (LOG_D if h01('log', x0, y0, salt) < 0.3 else LOG)
    for x in range(x0, x0 + d):
        for y in range(y0, y0 + d):
            corner = d >= 4 and x in (x0, x0 + d - 1) and y in (y0, y0 + d - 1)
            for z in range(z0, z0 + h):
                k = z0 + h - z                                     # 離頂幾層（1 ＝ 最頂）
                if k <= tip:
                    m = (d - 1) * (k - 1) / max(1, tip)            # 越往上越細
                    if abs(x + 0.5 - (x0 + d / 2)) > m / 2 + 0.5 or abs(y + 0.5 - (y0 + d / 2)) > m / 2 + 0.5:
                        continue
                    M.put('body', x, y, z, LOG_TIP)
                elif not corner:
                    M.put('body', x, y, z, c)


def palisade(M, x0, x1, yc, d, hbase, z0=0, salt=0, pitch=None):
    pitch = pitch or d
    for x in range(x0, x1 - d + 1, pitch):
        h = hbase + int(h01('ph', x, salt) * 4) - 1
        log(M, x, yc - d // 2, d, h, z0, salt)


def hip_cap(M, x0, y0, x1, y1, ze, p, over, color_fn=None, salt=0):
    F = roof_field([{'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'ze': ze, 'p': p, 'over': (over,) * 4}])
    return build_roof(M, F, 2, 'body', color_fn=color_fn, salt=salt)


def shingle(x, y, f, r, e):
    if r or e:
        return WOOD_D
    return WOOD_G if (x + y) % 5 else WOOD


def loophole_ring(M, x0, y0, x1, y1, z0, z1, step=8, off=4):
    for z in range(z0, z1):
        for x in range(x0 + off, x1 - 2, step):
            M.cells.pop((x, y0, z), None)
            M.cells.pop((x, y1 - 1, z), None)
        for y in range(y0 + off, y1 - 2, step):
            M.cells.pop((x0, y, z), None)
            M.cells.pop((x1 - 1, y, z), None)


def leaf(M, x, y0, y1, z1, color=WOOD):
    """一扇開著的木門（貼著門洞側邊、往城裡開 90°）：一格厚、三道橫檔、一道斜撐。"""
    for y in range(y0, y1):
        for z in range(0, z1):
            c = color
            if z in (2, z1 // 2, z1 - 3) or (y - y0) == int((z / max(1, z1 - 1)) * (y1 - y0 - 1)):
                c = WOOD_D
            M.put('body', x, y, z, c)


# ═════════════ 一級：木柵（pieux）═════════════
def w1_section():
    M, B = W(1, 'section', '斷面（2 m 一節：原木立柵、兩道內橫檔、內側的射擊踏台）', (20, 40, 40))
    palisade(M, 0, 20, 20, 4, 33, salt=1)
    for z0 in (8, 24):
        M.box('body', 0, 22, z0, 20, 23, z0 + 2, WOOD_D)
    M.box('body', 0, 22, 16, 20, 31, 17, WOOD)
    for px in (2, 12):
        M.box('body', px, 29, 0, px + 2, 31, 16, WOOD_D)
    M.anchor('wall-a', 0, 20, 0)
    M.anchor('wall-b', 19, 20, 0)
    B['len'] = 2
    return B


def w1_tower():
    M, B = W(1, 'tower', '塔（木構碉樓：一樓橫木牆、二樓挑出帶射口、木瓦四坡頂）', (50, 50, 84))
    for z in range(0, 32):                                       # 一樓：橫木一層一層疊（每 4 格一根），轉角咬合凸出
        c = LOG if (z // 4) % 2 == 0 else LOG_D
        for x in range(5, 45):
            for y in range(5, 45):
                if x in range(5, 8) or x in range(42, 45) or y in range(5, 8) or y in range(42, 45):
                    M.put('body', x, y, z, c)
        if (z // 4) % 2 == 0:
            for (a, b) in ((3, 5), (45, 47)):
                M.box('body', a, 5, z, b, 8, z + 1, c)
                M.box('body', a, 42, z, b, 45, z + 1, c)
    M.box('body', 2, 2, 32, 48, 48, 34, WOOD)                    # 樓板一路伸到挑出的二樓牆（托梁）
    for z in range(34, 58):                                      # 二樓挑出 3 格
        c = LOG if (z // 4) % 2 == 0 else LOG_D
        for x in range(2, 48):
            for y in range(2, 48):
                if x in (2, 3, 46, 47) or y in (2, 3, 46, 47):
                    M.put('body', x, y, z, c)
    loophole_ring(M, 2, 2, 48, 48, 42, 48, step=8, off=6)
    loophole_ring(M, 3, 3, 47, 47, 42, 48, step=8, off=6)
    hip_cap(M, 2, 2, 48, 48, 58, 0.9, 2, color_fn=shingle)
    for z in range(0, 20):                                       # 城裡那一面的門
        for x in range(20, 30):
            for y in range(42, 45):
                M.cells.pop((x, y, z), None)
            M.put('body', x, 43, z, WOOD_D if x in (20, 29) or z == 19 else WOOD)
    M.anchor('wall-a', 5, 25, 0)
    M.anchor('wall-b', 44, 25, 0)
    return B


def w1_gate():
    M, B = W(1, 'gate', '城門（兩座木碉樓夾 5 m 門洞、上面一道走道、兩扇開著的木門）', (120, 60, 72))
    palisade(M, 0, 12, 30, 4, 33, salt=2)                        # 兩側的短柵伸進碉樓 2 格（接成一塊）
    palisade(M, 108, 120, 30, 4, 33, salt=3)
    for (x0, x1) in ((10, 35), (85, 110)):
        for z in range(0, 50):
            c = LOG if (z // 4) % 2 == 0 else LOG_D
            for x in range(x0, x1):
                for y in range(18, 42):
                    if x in (x0, x0 + 1, x0 + 2, x1 - 3, x1 - 2, x1 - 1) or y in (18, 19, 20, 39, 40, 41):
                        M.put('body', x, y, z, c)
        loophole_ring(M, x0, 18, x1, 42, 36, 42, step=7, off=5)
        hip_cap(M, x0, 18, x1, 42, 50, 0.9, 2, color_fn=shingle, salt=x0)
    M.box('body', 35, 24, 32, 85, 36, 34, WOOD)                  # 走道
    for x in range(35, 85):
        for z in range(34, 42):
            if z == 41 or x % 4 == 0:
                M.put('body', x, 24, z, WOOD_D)
                M.put('body', x, 35, z, WOOD_D)
    M.box('body', 35, 24, 28, 85, 26, 32, WOOD_D)                # 門楣橫梁
    leaf(M, 34, 41, 58, 30)
    leaf(M, 85, 41, 58, 30)
    M.anchor('wall-a', 0, 30, 0)
    M.anchor('wall-b', 119, 30, 0)
    M.anchor('road-out', 60, 0, 0)
    M.anchor('road-in', 60, 59, 0)
    return B


def w1_joint():
    M, B = W(1, 'joint', '接頭（三根原木綁成的粗柱，蓋住轉角的縫）', (8, 40, 40))
    for (x, y) in ((0, 16), (4, 16), (2, 20)):
        log(M, x, y, 4, 36 - (y - 16), salt=x + y)
    M.box('body', 0, 16, 20, 8, 24, 22, WOOD_D)
    M.anchor('wall-a', 0, 20, 0)
    M.anchor('wall-b', 7, 20, 0)
    return B


def w1_end():
    M, B = W(1, 'end', '收尾（最後一根粗原木＋城裡那一側的斜撐）', (12, 40, 40))
    log(M, 0, 17, 6, 36, salt=9)
    for i in range(16):                                          # 斜撐：從柱子 2.4 m 處斜到地面
        y = 23 + i
        z = 24 - int(i * 24 / 15)
        M.box('body', 2, y, max(0, z - 2), 4, y + 1, z + 1, WOOD_D)
    M.anchor('wall-a', 0, 20, 0)
    return B


# ═════════════ 二級：土堤＋木柵、石砌門樓 ═════════════
def bank(M, x0, x1, yc, z0=0, top=20, salt=0, taper=None):
    """土堤：底寬 40（yc ± 20）、頂寬 18（yc −8 … +10）、高 top；頂上鋪泥路、坡面長草。taper ＝ (x 從, x 到) 那一段沿 x 收到 0。"""
    for x in range(x0, x1):
        h = top
        if taper:
            a, b = taper
            if x >= a:
                h = int(round(top * max(0.0, (b - x - 0.5) / (b - a))))
        for y in range(yc - 20, yc + 20):
            dy = y - yc
            if dy < -8:
                hy = int(h * (dy + 20) / 12.0)
            elif dy >= 10:
                hy = int(h * (20 - dy) / 10.0)
            else:
                hy = h
            for z in range(z0, z0 + hy):
                if z == z0 + hy - 1:
                    c = EARTH if (-4 <= dy < 9 and hy == h) else (GRASS_D if h01('g', x, y, salt) < 0.35 else GRASS)
                else:
                    c = EARTH
                M.put('body', x, y, z, c)


def w2_section():
    M, B = W(2, 'section', '斷面（2 m 一節：土堤 2 m 高、堤頂木柵、柵後泥路）', (20, 40, 42))
    bank(M, 0, 20, 20, salt=1)
    palisade(M, 0, 20, 14, 4, 21, z0=19, salt=4)
    M.anchor('wall-a', 0, 20, 0)
    M.anchor('wall-b', 19, 20, 0)
    B['len'] = 2
    return B


def w2_tower():
    M, B = W(2, 'tower', '塔（毛石塔基＋木構二樓、射口、紅瓦四坡頂）', (50, 50, 80))
    rubble(M, (3, 3, 47, 47), 0, 30, 5, base=STONE_W, dark=STONE, salt=21)
    M.box('body', 3, 3, 0, 47, 47, 1, STONE)
    M.box('body', 5, 5, 28, 45, 45, 30, WOOD)
    for z in range(30, 54):
        for x in range(4, 46):
            for y in range(4, 46):
                if x in (4, 5, 44, 45) or y in (4, 5, 44, 45):
                    post = (x - 4) % 10 < 2 or (y - 4) % 10 < 2
                    M.put('body', x, y, z, WOOD_D if (post or z in (30, 31, 52, 53)) else WOOD_G)
    loophole_ring(M, 4, 4, 46, 46, 38, 46, step=10, off=7)
    loophole_ring(M, 5, 5, 45, 45, 38, 46, step=10, off=7)
    hip_cap(M, 4, 4, 46, 46, 54, 0.8, 3, salt=22)
    for z in range(1, 22):
        for x in range(20, 30):
            for y in range(42, 47):
                M.cells.pop((x, y, z), None)
            M.put('body', x, 44, z, WOOD_D if x in (20, 29) or z == 21 else WOOD)
    M.anchor('wall-a', 3, 25, 0)
    M.anchor('wall-b', 46, 25, 0)
    return B


def w2_gate():
    M, B = W(2, 'gate', '城門（石砌門樓：4 m 拱門洞、上面一間守衛室、紅瓦四坡頂、門上王室紋章；兩側接土堤）', (120, 80, 96))
    bank(M, 0, 30, 40, salt=2)
    bank(M, 90, 120, 40, salt=3)
    palisade(M, 0, 30, 34, 4, 21, z0=19, salt=5)
    palisade(M, 90, 120, 34, 4, 21, z0=19, salt=6)
    R = (30, 16, 90, 64)
    rubble(M, R, 0, 70, 6, base=STONE_W, dark=STONE, salt=23)
    quoins(M, R, 0, 70, long=7, short=4, step=6)
    M.box('body', 36, 22, 40, 84, 58, 42, WOOD)                   # 守衛室地板
    for x in range(40, 80):                                      # 拱門洞：半圓，起拱 20、頂 40
        dx = x + 0.5 - 60
        ztop = 20 + int(math.sqrt(max(0.0, 400 - dx * dx)))
        for z in range(0, ztop):
            for y in range(16, 64):
                M.cells.pop((x, y, z), None)
        for z in range(ztop, ztop + 3):                          # 拱券石
            for y in (16, 63):
                M.put('body', x, y, z, STONE_L)
    for (cx, face) in ((48, 16), (72, 16), (48, 63), (72, 63)):  # 守衛室的窗
        for x in range(cx - 3, cx + 3):
            for z in range(48, 58):
                M.cells.pop((x, face, z), None)
                M.cells.pop((x, face + (1 if face == 16 else -1), z), None)
    for x in range(53, 68):                                      # 門上紋章：石框、藍底、三朵金色百合
        for z in range(44, 58):
            edge = x in (53, 67) or z in (44, 57)
            M.put('body', x, 15, z, STONE_L if edge else SH_BLUE)
    for (fx, fz) in ((56, 52), (63, 52), (59, 47)):
        for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (-1, 1), (2, 1)):
            M.put('body', fx + dx, 15, fz + dz, GOLD)
    hip_cap(M, 30, 16, 90, 64, 70, 0.7, 4, salt=24)
    leaf(M, 39, 64, 79, 34)
    leaf(M, 80, 64, 79, 34)
    M.anchor('wall-a', 0, 40, 0)
    M.anchor('wall-b', 119, 40, 0)
    M.anchor('road-out', 60, 0, 0)
    M.anchor('road-in', 60, 79, 0)
    return B


def w2_joint():
    M, B = W(2, 'joint', '接頭（圓的土墩、頂上一圈木柵；蓋住轉角）', (40, 40, 42))
    for x in range(0, 40):
        for y in range(0, 40):
            r = math.hypot(x + 0.5 - 20, y + 0.5 - 20)
            if r < 20:
                h = 20 if r < 9 else int(20 * (20 - r) / 11)
                for z in range(0, h):
                    top = z == h - 1
                    M.put('body', x, y, z, (EARTH if r < 8 else (GRASS_D if h01('j', x, y) < 0.35 else GRASS)) if top else EARTH)
    for i in range(14):                                          # 外半圈木柵
        a = math.pi * (0.1 + 0.8 * i / 13) + math.pi
        x = int(round(20 + 7 * math.cos(a))) - 2
        y = int(round(20 + 7 * math.sin(a))) - 2
        log(M, x, y, 4, 21 + int(h01('jl', i) * 3), z0=19, salt=i)
    M.anchor('wall-a', 0, 20, 0)
    M.anchor('wall-b', 39, 20, 0)
    return B


def w2_end():
    M, B = W(2, 'end', '收尾（土堤往前收成斜坡、木柵停在一根粗原木）', (24, 40, 42))
    bank(M, 0, 24, 20, salt=7, taper=(4, 24))
    palisade(M, 0, 4, 14, 4, 21, z0=19, salt=8)
    log(M, 4, 11, 6, 24, z0=17, salt=11)
    M.anchor('wall-a', 0, 20, 0)
    return B


# ═════════════ 三級：石牆、石塔、城門樓 ═════════════
def curtain(M, x0, x1, yc, salt=0):
    """石牆斷面：外面底下 2 m 有斜的牆腳（talus）、6 m 高到走道；外側垛牆 1.8 m（雉堞：1.2 m 垛＋0.8 m 垛口）、內側矮牆；牆身毛石。
    y 相對中線：外牆面 −10（牆腳 −14）、內牆面 +13。"""
    yo, yi = yc - 10, yc + 13
    for x in range(x0, x1):
        merlon = ((x - x0) % 20) < 12
        for z in range(0, 78):
            ya = yo - (max(0, 20 - z) * 4 // 20)                # 牆腳往外斜 4 格
            if z < 60:
                ys = range(ya, yi)
            elif z < 78:
                ys = list(range(yo, yo + 4))                     # 外側垛牆
                if z >= 70 and not merlon:
                    ys = []
                if z < 64:
                    ys = list(ys) + list(range(yi - 2, yi))      # 內側矮牆
            for y in ys:
                rowi = z // 5
                u = x + (4 if rowi % 2 else 0)
                c = STONE_L if (z % 5 == 4 or u % 8 == 0) else (STONE if h01('cs', u // 8, rowi, salt) < 0.15 else STONE_W)
                if z == 59 and yo + 4 <= y < yi - 2:
                    c = STONE_L                                  # 走道鋪石
                if (z == 77 and merlon) or (z == 69 and not merlon):
                    c = STONE_L                                  # 垛頂、垛口的壓頂石
                if z in (50, 51) and y == ya:
                    c = STONE_L
                M.put('body', x, y, z, c)
        for z in (50, 51):                                       # 腰線（往外凸一格）
            M.put('body', x, yo - 1, z, STONE_L)


def w3_section():
    M, B = W(3, 'section', '斷面（2 m 一節：毛石牆 6 m、斜牆腳、腰線、走道、雉堞＋內側矮牆）', (20, 40, 80))
    curtain(M, 0, 20, 20, salt=1)
    M.anchor('wall-a', 0, 20, 0)
    M.anchor('wall-b', 19, 20, 0)
    B['len'] = 2
    return B


def round_tower(M, cx, cy, r, h, salt=0, slits=True):
    """圓塔：牆厚 6、底下斜牆腳、腰線、外挑的托石一圈、雉堞（每 20° 一垛）；裡面兩層樓板。"""
    for x in range(int(cx - r - 4), int(cx + r + 5)):
        for y in range(int(cy - r - 4), int(cy + r + 5)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            ang = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx)) % 360
            for z in range(0, h + 16):
                ro = r + (max(0, 16 - z) * 3 / 16.0)             # 牆腳
                if z >= h - 4:
                    ro = r + 2                                   # 托石一圈外挑
                if z >= h:
                    ro = r + 2
                    merlon = (ang % 20) < 12
                    if z >= h + 8 and not merlon:
                        continue
                    if d < r - 2:
                        continue
                if d >= ro or (d < r - 6 and z not in (0, 58, 59, h - 2, h - 1)):
                    continue
                rowi = z // 5
                u = int(ang * r / 57.3) + (4 if rowi % 2 else 0)
                c = STONE_L if (z % 5 == 4 or u % 8 == 0) else (STONE if h01('rt', u // 8, rowi, salt) < 0.15 else STONE_W)
                if z in (h - 4, h - 3) or z in (50, 51) or z == h + 15 or (z == h + 7):
                    c = STONE_L
                M.put('body', x, y, z, c)
    if slits:
        for a in range(200, 341, 35):                            # 射口（外半圈）
            for z0 in (24, 64):
                rad = math.radians(a)
                for k in range(int(r - 7), int(r + 4)):
                    x = int(cx + k * math.cos(rad))
                    y = int(cy + k * math.sin(rad))
                    for z in range(z0, z0 + 8):
                        M.cells.pop((x, y, z), None)


def w3_tower():
    M, B = W(3, 'tower', '塔（圓塔 5.6 m：斜牆腳、腰線、托石、雉堞、射口；兩側接走道的門）', (72, 72, 108))
    round_tower(M, 36, 36, 28, 90, salt=31)
    for x in list(range(4, 13)) + list(range(59, 68)):           # 走道進塔的門（拱）
        for y in range(28, 44):
            for z in range(60, 80):
                if z < 76 or abs(y + 0.5 - 36) < 8 - (z - 76) * 2:
                    if abs(y + 0.5 - 36) < 6:
                        M.cells.pop((x, y, z), None)
    M.anchor('wall-a', 12, 36, 0)
    M.anchor('wall-b', 59, 36, 0)
    return B


def w3_gate():
    M, B = W(3, 'gate', '城門（門樓：兩座圓角樓夾 3.6 m 拱門洞、吊閘、托石與雉堞、門上王室紋章；兩側接石牆）', (120, 80, 124))
    curtain(M, 0, 26, 40, salt=2)
    curtain(M, 94, 120, 40, salt=3)
    R = (26, 14, 94, 66)
    for x in range(R[0], R[2]):
        for y in range(R[1], R[3]):
            for z in range(0, 112):
                edge = x - R[0] < 6 or R[2] - 1 - x < 6 or y - R[1] < 6 or R[3] - 1 - y < 6
                if z < 96 and not edge and z not in (0, 58, 59, 94, 95):
                    continue
                if z >= 96:
                    if not (x - R[0] < 4 or R[2] - 1 - x < 4 or y - R[1] < 4 or R[3] - 1 - y < 4):
                        continue
                    per = (x + y) % 20 < 12
                    if z >= 104 and not per:
                        continue
                rowi = z // 5
                u = x + y + (4 if rowi % 2 else 0)
                c = STONE_L if (z % 5 == 4 or u % 8 == 0 or z in (94, 95, 103, 111)) else (STONE if h01('gs', u // 8, rowi) < 0.15 else STONE_W)
                M.put('body', x, y, z, c)
    for (tx, ty) in ((30, 18), (90, 18)):                       # 前面兩座圓角樓
        round_tower(M, tx, ty, 13, 100, salt=tx, slits=False)
    for x in range(42, 78):                                      # 拱門洞：起拱 30、頂 48
        dx = x + 0.5 - 60
        ztop = 30 + int(math.sqrt(max(0.0, 324 - dx * dx)))
        for z in range(0, ztop):
            for y in range(0, 80):
                k = M.cells.get((x, y, z))
                if k and R[1] - 6 <= y < R[3]:
                    del M.cells[(x, y, z)]
        for z in range(ztop, ztop + 3):
            M.put('body', x, R[1], z, STONE_L)
            M.put('body', x, R[3] - 1, z, STONE_L)
        if x % 4 == 1:                                           # 吊閘（拉起來，只露出下緣的齒）
            for z in range(ztop - 6, ztop):
                M.put('body', x, R[1] + 4, z, IRON)
    for x in range(50, 71):                                      # 紋章
        for z in range(56, 76):
            edge = x in (50, 70) or z in (56, 75)
            M.put('body', x, R[1] - 1, z, STONE_L if edge else SH_BLUE)
    for (fx, fz) in ((54, 67), (65, 67), (59, 60)):
        for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (-1, 1), (2, 1), (0, 3), (1, 3)):
            M.put('body', fx + dx, R[1] - 1, fz + dz, GOLD)
    for x in range(30, 90):                                      # 門上托石（假的堞眼）
        if x % 4 < 2:
            for z in range(88, 94):
                M.put('body', x, R[1] - 1, z, STONE_L)
                M.put('body', x, R[1] - 2, z, STONE_L)
    leaf(M, 41, 66, 79, 40)                                      # 門扇貼著門洞兩側的牆（鉸鏈那一格碰到牆）
    leaf(M, 78, 66, 79, 40)
    M.anchor('wall-a', 0, 40, 0)
    M.anchor('wall-b', 119, 40, 0)
    M.anchor('road-out', 60, 0, 0)
    M.anchor('road-in', 60, 79, 0)
    return B


def w3_joint():
    M, B = W(3, 'joint', '接頭（圓的小角樓，半徑 1.5 m；蓋住轉角）', (40, 44, 96))
    round_tower(M, 20, 22, 15, 76, salt=33, slits=False)
    M.anchor('wall-a', 14, 22, 0)
    M.anchor('wall-b', 25, 22, 0)
    return B


def w3_end():
    M, B = W(3, 'end', '收尾（方的端樓：斜牆腳、雉堞；牆停在海邊或山壁）', (40, 44, 104))
    for x in range(0, 38):
        for y in range(0, 44):
            for z in range(0, 96):
                xa = 38 - (max(0, 20 - z) * 4 // 20)
                ya, yb = 4 - (max(0, 20 - z) * 4 // 20), 40 + (max(0, 20 - z) * 4 // 20)
                if not (x < xa - 4 + 4 and ya <= y < yb and x < xa):
                    continue
                if z >= 84:
                    edge = x < 4 or xa - 1 - x < 4 or y - ya < 4 or yb - 1 - y < 4
                    if not edge:
                        continue
                    per = (x + y) % 20 < 12
                    if z >= 90 and not per:
                        continue
                elif not (x < 6 or xa - 1 - x < 6 or y - ya < 6 or yb - 1 - y < 6) and z not in (0, 58, 59, 82, 83):
                    continue
                rowi = z // 5
                u = x + y + (4 if rowi % 2 else 0)
                c = STONE_L if (z % 5 == 4 or u % 8 == 0 or z in (82, 83, 89, 95)) else (STONE if h01('es', u // 8, rowi) < 0.15 else STONE_W)
                M.put('body', x, y, z, c)
    M.anchor('wall-a', 0, 22, 0)
    return B


TIERS = {1: [w1_section, w1_tower, w1_gate, w1_joint, w1_end],
         2: [w2_section, w2_tower, w2_gate, w2_joint, w2_end],
         3: [w3_section, w3_tower, w3_gate, w3_joint, w3_end]}
