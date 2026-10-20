# 東羅馬城牆 1453 的三套模組（TASK-0748）：狄奧多西內牆（land-inner）、外牆（land-outer）、海牆（sea）。
# 每一套：section（斷面，沿曲線一節一節拉）、tower（塔；外牆有方塔與新月塔兩型，遊戲照順序輪流）、gate（城門）、end（收尾）。
# 尺寸照史料（Blocksail 研究檔 walls.md §1.2、§2；van Millingen 1899、Meyer-Plath & Schneider 1943、en.wikipedia 引 Turnbull 2004）：
#   內牆：厚 4.7 m、城裡高約 12 m、雉堞 1.4 m；塔 96 座，方形為主、寬 10～12 m、外凸 5.5～10 m、高 15～20 m。
#   外牆：底厚 2 m、走道 8.5～9 m；牆後有拱廊室；塔方形與新月形交替、外凸約 4.9 m、高 9～14 m。
#   海牆：幾乎貼著岸、高 12～15 m（金角灣約 10 m）；牆基橫嵌大理石柱加固；方塔。
#   牆面：石灰岩方石夾紅磚帶（內牆 7～11 道）；海牆修補多、磚帶不齊。
# 座標與接口見 rkit.py 檔頭。
import math
from rkit import *

SETS = {'land-inner': '狄奧多西內牆', 'land-outer': '狄奧多西外牆', 'sea': '海牆'}


def W(set_, part, title, size, variant=''):
    M = Model(size)
    key = 'wall-%s-%s%s' % (set_, part, ('-' + variant) if variant else '')
    return M, {'key': key, 'set': set_, 'part': part, 'variant': variant or 'a', 'title': '%s｜%s' % (SETS[set_], title), 'M': M}


def block(M, x0, y0, x1, y1, z0, z1, mason, shape=None):
    """實心的砌體（看不見的裡面也填 —— 壓縮後幾乎不佔、表面才算面數）；shape(x, y) ⇒ 那一柱要不要（圓的、弧的）。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            if shape and not shape(x, y):
                continue
            for z in range(z0, z1):
                M.put(x, y, z, mason.color(x + y, z))


def ring_parapet(M, inside, x0, y0, x1, y1, z0, h, crenel_h, mason, t=3):
    """塔頂一圈雉堞：inside(x, y) ＝ 塔的平面；離平面邊 < t 格的那一圈立垛牆，沿周長每 10 格一垛（垛寬 6）。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            if not inside(x, y):
                continue
            edge = any(not inside(x + dx, y + dy) for dx in range(-t, t + 1) for dy in range(-t, t + 1) if abs(dx) + abs(dy) <= t)
            if not edge:
                continue
            merlon = ((x + y) % 10) < 6
            for z in range(z0, z0 + h):
                if not merlon and z >= z0 + h - crenel_h:
                    continue
                top = z == z0 + h - 1 or (not merlon and z == z0 + h - crenel_h - 1)
                M.put(x, y, z, LIME_G if top else mason.color(x + y, z))


def tunnel(M, x0, x1, yc, half, z0, spring):
    """走道穿過塔：沿 x 挖 x0..x1、寬 2·half、底 z0、起拱 spring 的拱頂通道；地面鋪石。"""
    for x in range(x0, x1):
        for y in range(yc - half - 1, yc + half + 1):
            for z in range(z0, spring + half + 2):
                dy = y + 0.5 - yc
                d = math.hypot(dy, z + 0.5 - spring) if z >= spring else abs(dy)
                if d < half:
                    M.cells.pop((x, y, z), None)
        for y in range(yc - half, yc + half):
            if (x, y, z0 - 1) in M.cells:
                M.cells[(x, y, z0 - 1)] = PAVE


def leaf(M, x, y0, y1, z1):
    """一扇開著的木門（貼著門洞側邊，一格厚、三道鐵條）。"""
    for y in range(y0, y1):
        for z in range(0, z1):
            M.put(x, y, z, IRON if z in (3, z1 // 2, z1 - 4) else WOOD_D)


# ═════════════ 內牆（狄奧多西，5 世紀；北段接布雷契耐牆）═════════════
MI = Masonry(period=12, salt='in')
IN_T, IN_TOP = 12, 56                                      # 牆厚一半（2.4 m ⇒ 厚 4.8 m）、走道高（11.2 m）


def inner_profile(M, x0, x1, yc, plinth=True):
    """內牆斷面：厚 4.8 m、走道 11.2 m、外側垛牆 0.6 m 厚 2 m 高（垛口 1 m）、內側矮牆；牆腳外側凸 1 格。"""
    yo, yi = yc - IN_T, yc + IN_T
    block(M, x0, yo, x1, yi, 0, IN_TOP, MI)
    for x in range(x0, x1):
        for y in range(yo + 3, yi - 2):
            M.cells[(x, y, IN_TOP - 1)] = PAVE
    merlons(M, x0, x1, yo, yo + 3, IN_TOP, 10, 5, cap=LIME_G, mason=MI)
    block(M, x0, yi - 2, x1, yi, IN_TOP, IN_TOP + 3, MI)
    if plinth:
        block(M, x0, yo - 1, x1, yo, 0, 4, MI)


def li_section():
    M, B = W('land-inner', 'section', '斷面（4 m 一節：厚 4.8 m、走道 11.2 m、雉堞、牆腳；石灰岩夾紅磚帶）', (20, 28, 66))
    inner_profile(M, 0, 20, 14)
    M.anchor('wall-a', 0, 14, 0)
    M.anchor('wall-b', 19, 14, 0)
    B['len'] = 4
    return B


def inner_tower(M, x0, x1, yc, h=92, salt=''):
    """內牆方塔：x0..x1（10.4 m）、往外凸到牆外 6 m、城裡那側凸 0.4 m；上層兩扇圓拱窗、下層射口、塔頂雉堞、走道穿過。"""
    yo, yi = yc - IN_T - 30, yc + IN_T + 2
    block(M, x0, yo, x1, yi, 0, h, MI)
    block(M, x0 - 1, yo - 1, x1 + 1, yi, 0, 5, MI)         # 牆腳
    for x in range(x0 + 3, x1 - 3):
        for y in range(yo + 3, yi - 3):
            M.cells[(x, y, h - 1)] = PAVE
    ring_parapet(M, lambda x, y: x0 <= x < x1 and yo <= y < yi, x0, yo, x1, yi, h, 10, 5, MI)
    w = x1 - x0
    for u in (w // 4 - 4, 3 * w // 4 - 4):                 # 外面（−y）上層兩扇窗、下層兩道射口
        opening(M, 'y', yo, +1, x0 + u, x0 + u + 8, h - 28, h - 10, 3)
        opening(M, 'y', yo, +1, x0 + u + 3, x0 + u + 5, 28, 38, 3, arch=False, brick=False)
    for (xp, d) in ((x0, +1), (x1 - 1, -1)):               # 兩側（露在牆外那一段）各一扇窗
        opening(M, 'x', xp, d, yo + 8, yo + 16, h - 28, h - 10, 3)
    tunnel(M, x0, x1, yc, 5, IN_TOP, IN_TOP + 6)
    for (xp, d) in ((x0, +1), (x1 - 1, -1)):               # 通道口的磚拱
        for y in range(yc - 7, yc + 7):
            for z in range(IN_TOP + 4, IN_TOP + 14):
                if (xp, y, z) in M.cells and math.hypot(y + 0.5 - yc, z + 0.5 - (IN_TOP + 6)) < 6.6:
                    M.cells[(xp, y, z)] = BRICK


def li_tower():
    M, B = W('land-inner', 'tower', '塔（方塔 10.4 m、外凸 6 m、高 18.4 m＋雉堞；上層圓拱窗、下層射口、走道穿過）', (60, 88, 102))
    yc = 44
    inner_profile(M, 0, 4, yc)
    inner_profile(M, 56, 60, yc)
    inner_tower(M, 4, 56, yc)
    M.anchor('wall-a', 0, yc, 0)
    M.anchor('wall-b', 59, yc, 0)
    return B


def li_gate():
    M, B = W('land-inner', 'gate', '城門（兩座方塔夾 4.4 m 拱門洞；大理石與紅磚交替的拱石、門上大理石帶；兩扇開著的門）', (140, 88, 102))
    yc = 44
    inner_profile(M, 0, 4, yc)
    inner_profile(M, 136, 140, yc)
    inner_tower(M, 4, 56, yc, salt='g1')
    inner_tower(M, 84, 140 - 4, yc, salt='g2')
    block(M, 56, yc - IN_T, 84, yc + IN_T, 0, IN_TOP + 8, MI)   # 門上的牆比牆身高一點（門樓）
    for x in range(56, 84):
        for y in range(yc - IN_T + 3, yc + IN_T - 2):
            M.cells[(x, y, IN_TOP + 7)] = PAVE
    merlons(M, 56, 84, yc - IN_T, yc - IN_T + 3, IN_TOP + 8, 10, 5, cap=LIME_G, mason=MI)
    for x in range(56, 84):                                  # 門上的大理石帶
        for z in (40, 41):
            M.put(x, yc - IN_T - 1, z, MARBLE)
    arch_cut(M, 70, 11, 22, yc - IN_T - 1, yc + IN_T, ring=3, alt=(MARBLE, BRICK))
    leaf(M, 59, yc + 2, yc + IN_T, 22)
    leaf(M, 80, yc + 2, yc + IN_T, 22)
    M.anchor('wall-a', 0, yc, 0)
    M.anchor('wall-b', 139, yc, 0)
    M.anchor('road-out', 70, 0, 0)
    M.anchor('road-in', 70, 87, 0)
    return B


def li_end():
    M, B = W('land-inner', 'end', '收尾（方塔：牆停在海牆、或接別的牆的地方）', (57, 88, 102))
    yc = 44
    inner_profile(M, 0, 4, yc)
    inner_tower(M, 4, 56, yc, salt='e')
    M.anchor('wall-a', 0, yc, 0)
    return B


# ═════════════ 外牆（狄奧多西；台地 peribolos 那一側有拱廊室）═════════════
MO = Masonry(period=12, salt='out')
OUT_T, OUT_TOP = 5, 38                                     # 牆厚一半（1 m ⇒ 厚 2 m）、走道高（7.6 m）


def outer_profile(M, x0, x1, yc, arcade=True):
    """外牆斷面：厚 2 m、走道 7.6 m、垛牆 2 m；城裡那一側每 2 m 一道扶壁、扶壁之間圓拱（牆後的拱廊室）。"""
    yo, yi = yc - OUT_T, yc + OUT_T
    block(M, x0, yo, x1, yi, 0, OUT_TOP, MO)
    for x in range(x0, x1):
        for y in range(yo + 3, yi):
            M.cells[(x, y, OUT_TOP - 1)] = PAVE
    merlons(M, x0, x1, yo, yo + 3, OUT_TOP, 10, 5, cap=LIME_G, mason=MO)
    block(M, x0, yo - 1, x1, yo, 0, 3, MO)
    if arcade:
        block(M, x0, yi, x1, yi + 6, 0, OUT_TOP - 2, MO)
        for x in range(x0, x1):
            for y in range(yi, yi + 6):
                M.cells[(x, y, OUT_TOP - 3)] = PAVE
        for k in range(x0 // 10 - 1, x1 // 10 + 1):
            xc = k * 10 + 5 + 0.5
            for x in range(max(x0, int(xc) - 4), min(x1, int(xc) + 5)):
                dx = x + 0.5 - xc
                for z in range(0, 31):
                    d = math.hypot(dx, z + 0.5 - 27) if z >= 27 else abs(dx)
                    if d < 3.5:
                        for y in range(yi, yi + 6):
                            M.cells.pop((x, y, z), None)
                    elif d < 4.6 and z >= 26 and (x, yi + 5, z) in M.cells:
                        M.cells[(x, yi + 5, z)] = BRICK


def lo_section():
    M, B = W('land-outer', 'section', '斷面（4 m 一節：厚 2 m、走道 7.6 m、雉堞；城裡那一側的拱廊室）', (20, 32, 48))
    outer_profile(M, 0, 20, 16)
    M.anchor('wall-a', 0, 16, 0)
    M.anchor('wall-b', 19, 16, 0)
    B['len'] = 4
    return B


def outer_tower(M, x0, x1, yc, h=54, crescent=False):
    """外牆的塔：方塔，或新月塔（外面是半圓）；寬 x1 − x0（7 m）、外凸到牆外 5 m、高 10.8 m＋雉堞。"""
    yo, yi = yc - OUT_T - 25, yc + OUT_T + 1
    r = (x1 - x0) / 2.0
    xc, yr = x0 + r, yo + r

    def inside(x, y):
        if not (x0 <= x < x1 and yo <= y < yi):
            return False
        if crescent and y + 0.5 < yr:
            return math.hypot(x + 0.5 - xc, y + 0.5 - yr) < r
        return True

    block(M, x0, yo, x1, yi, 0, h, MO, shape=inside)
    for x in range(x0, x1):
        for y in range(yo, yi):
            if inside(x, y) and inside(x - 3, y) and inside(x + 3, y) and inside(x, y - 3) and inside(x, y + 3):
                M.cells[(x, y, h - 1)] = PAVE
    ring_parapet(M, inside, x0, yo, x1, yi, h, 10, 5, MO)
    xm = (x0 + x1) // 2
    opening(M, 'y', yo + (0 if not crescent else 0), +1, xm - 3, xm + 3, h - 20, h - 8, 3 if not crescent else 4)
    for xs in (x0 + 7, x1 - 8):
        opening(M, 'y', yo if not crescent else int(yr - math.sqrt(max(0.0, r * r - (xs + 0.5 - xc) ** 2))), +1, xs, xs + 1, 16, 24, 3, arch=False, brick=False)
    tunnel(M, x0, x1, yc, 3, OUT_TOP, OUT_TOP + 4)


def lo_tower(crescent):
    v = 'b' if crescent else ''
    M, B = W('land-outer', 'tower', ('新月塔' if crescent else '方塔') + '（寬 7 m、外凸 5 m、高 10.8 m＋雉堞；走道穿過）', (45, 64, 64), variant=v)
    yc = 32
    outer_profile(M, 0, 5, yc)
    outer_profile(M, 40, 45, yc)
    outer_tower(M, 5, 40, yc, crescent=crescent)
    M.anchor('wall-a', 0, yc, 0)
    M.anchor('wall-b', 44, yc, 0)
    return B


def lo_gate():
    M, B = W('land-outer', 'gate', '城門（方的門樓 10 m：3.2 m 拱門洞、紅磚白石交替的拱石、雉堞）', (60, 64, 64))
    yc = 32
    outer_profile(M, 0, 5, yc)
    outer_profile(M, 55, 60, yc)
    yo, yi = yc - OUT_T - 12, yc + OUT_T + 8
    block(M, 5, yo, 55, yi, 0, 50, MO)
    for x in range(8, 52):
        for y in range(yo + 3, yi - 3):
            M.cells[(x, y, 49)] = PAVE
    ring_parapet(M, lambda x, y: 5 <= x < 55 and yo <= y < yi, 5, yo, 55, yi, 50, 10, 5, MO)
    arch_cut(M, 30, 8, 16, yo, yi, ring=2, alt=(MARBLE, BRICK))
    opening(M, 'y', yo, +1, 26, 34, 32, 44, 3)
    tunnel(M, 5, 55, yc, 3, OUT_TOP, OUT_TOP + 4)
    M.anchor('wall-a', 0, yc, 0)
    M.anchor('wall-b', 59, yc, 0)
    M.anchor('road-out', 30, 0, 0)
    M.anchor('road-in', 30, 63, 0)
    return B


def lo_end():
    M, B = W('land-outer', 'end', '收尾（方塔）', (40, 64, 64))
    yc = 32
    outer_profile(M, 0, 5, yc)
    outer_tower(M, 5, 40, yc)
    M.anchor('wall-a', 0, yc, 0)
    return B


# ═════════════ 海牆（馬爾馬拉海、金角灣；貼著岸）═════════════
MS = Masonry(period=13, salt='sea', irregular=True)
SEA_T, SEA_TOP = 8, 56                                     # 牆厚一半（1.6 m ⇒ 厚 3.2 m）、走道高（11.2 m）


def sea_profile(M, x0, x1, yc):
    """海牆斷面：厚 3.2 m、走道 11.2 m、雉堞；海那一側的牆腳斜出 0.4 m、牆腳橫嵌大理石柱（柱頭朝外，每 3 m 一根）。"""
    yo, yi = yc - SEA_T, yc + SEA_T
    block(M, x0, yo, x1, yi, 0, SEA_TOP, MS)
    for x in range(x0, x1):
        for y in range(yo + 3, yi - 2):
            M.cells[(x, y, SEA_TOP - 1)] = PAVE
    merlons(M, x0, x1, yo, yo + 3, SEA_TOP, 10, 5, cap=LIME_G, mason=MS)
    block(M, x0, yi - 2, x1, yi, SEA_TOP, SEA_TOP + 3, MS)
    block(M, x0, yo - 1, x1, yo, 0, 10, MS)
    block(M, x0, yo - 2, x1, yo - 1, 0, 5, MS)
    for x in range(x0, x1):                                  # 柱頭（直徑 0.8 m）：每 15 格一根，兩排錯開
        for z in range(0, 10):
            for (cx, cz) in ((7.5, 3.5), (0.0, 7.5), (15.0, 7.5)):
                u = (x % 15) + 0.5
                if math.hypot(u - cx, z + 0.5 - cz) < 2.1:
                    y = yo - 2 if z < 5 else yo - 1
                    if (x, y, z) in M.cells:
                        M.cells[(x, y, z)] = MARBLE


def s_section():
    M, B = W('sea', 'section', '斷面（4 m 一節：厚 3.2 m、走道 11.2 m、雉堞；牆腳斜出、橫嵌大理石柱；磚帶修補過、不齊）', (20, 40, 66))
    sea_profile(M, 0, 20, 20)
    M.anchor('wall-a', 0, 20, 0)
    M.anchor('wall-b', 19, 20, 0)
    B['len'] = 4
    return B


def sea_tower(M, x0, x1, yc, h=80):
    """海牆方塔：寬 x1 − x0、外凸到牆外 4 m、高 16 m＋雉堞；上層兩扇窗、下層射口、走道穿過。"""
    yo, yi = yc - SEA_T - 20, yc + SEA_T + 1
    block(M, x0, yo, x1, yi, 0, h, MS)
    block(M, x0 - 1, yo - 1, x1 + 1, yi, 0, 8, MS)
    for x in range(x0 + 3, x1 - 3):
        for y in range(yo + 3, yi - 3):
            M.cells[(x, y, h - 1)] = PAVE
    ring_parapet(M, lambda x, y: x0 <= x < x1 and yo <= y < yi, x0, yo, x1, yi, h, 10, 5, MS)
    w = x1 - x0
    if w >= 40:
        for u in (w // 4 - 3, 3 * w // 4 - 4):
            opening(M, 'y', yo, +1, x0 + u, x0 + u + 7, h - 24, h - 9, 3)
    else:
        opening(M, 'y', yo, +1, x0 + w // 2 - 3, x0 + w // 2 + 4, h - 24, h - 9, 3)
    for xs in (x0 + 8, x1 - 9):
        opening(M, 'y', yo, +1, xs, xs + 2, 26, 34, 3, arch=False, brick=False)
    tunnel(M, x0, x1, yc, 4, SEA_TOP, SEA_TOP + 5)


def s_tower():
    M, B = W('sea', 'tower', '塔（方塔 9 m、外凸 4 m、高 16 m＋雉堞；上層窗、下層射口、走道穿過）', (55, 60, 90))
    yc = 30
    sea_profile(M, 0, 5, yc)
    sea_profile(M, 50, 55, yc)
    sea_tower(M, 5, 50, yc)
    M.anchor('wall-a', 0, yc, 0)
    M.anchor('wall-b', 54, yc, 0)
    return B


def s_gate():
    M, B = W('sea', 'gate', '海門（兩座小方塔夾 3.6 m 拱門洞；紅磚白石交替的拱石、門上大理石帶）', (110, 60, 90))
    yc = 30
    sea_profile(M, 0, 5, yc)
    sea_profile(M, 105, 110, yc)
    sea_tower(M, 5, 40, yc, h=72)
    sea_tower(M, 70, 105, yc, h=72)
    sea_profile(M, 40, 70, yc)
    for x in range(40, 70):
        for z in (34, 35):
            M.put(x, yc - SEA_T - 3, z, MARBLE)
    arch_cut(M, 55, 9, 18, yc - SEA_T - 2, yc + SEA_T, ring=3, alt=(MARBLE, BRICK))
    leaf(M, 46, yc + 1, yc + SEA_T, 18)
    leaf(M, 63, yc + 1, yc + SEA_T, 18)
    M.anchor('wall-a', 0, yc, 0)
    M.anchor('wall-b', 109, yc, 0)
    M.anchor('road-out', 55, 0, 0)
    M.anchor('road-in', 55, 59, 0)
    return B


def s_end():
    M, B = W('sea', 'end', '收尾（方塔）', (51, 60, 90))
    yc = 30
    sea_profile(M, 0, 5, yc)
    sea_tower(M, 5, 50, yc)
    M.anchor('wall-a', 0, yc, 0)
    return B


ALL = [li_section, li_tower, li_gate, li_end,
       lo_section, lambda: lo_tower(False), lambda: lo_tower(True), lo_gate, lo_end,
       s_section, s_tower, s_gate, s_end]
