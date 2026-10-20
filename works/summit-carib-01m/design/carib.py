# 加勒比海風格（carib，17 世紀的木構聚落）城鎮建築套件（TASK-0757）—— 這一套自己的調色盤與工具；共用的 Model、屋頂、擺部件照 kit.py（抄自 summit-bourg-fr-01m，同一份）。
# 座標同 kit.py：x 臨路寬（從街上看左 → 右）、y 進深（y 0 臨路）、z 往上（z 0 整平面）；0.1 m／格；作品框 ＝ 地塊。
# 換色的角色（每個角色只用一個色，替換色才換得乾淨；BUILDING_SPEC §4）：
#   BOARD 木板牆（沒上漆、曬灰的）｜LIME 石灰水刷白的牆（編條糊泥、毛石抹灰）｜SHUT 百葉與木板門（沒上漆的木作）
#   屋面：木瓦 SHINGLE_A／B＋屋脊 SHINGLE_R；棕櫚茅草 THATCH_A／B＋屋脊 THATCH_R（屋面這一版不拿來換色）
from kit import *

BOARD, BOARD_D = 109, 104          # 木板牆、板縫與搭接那一道暗線
LIME = 255                         # 石灰水（白）
SHUT = 136                         # 百葉、木板門（沒上漆）
FRAME = 68                         # 柱、梁、窗框、門框（深色木）
FLOOR = 104                        # 木地板、台階
SHINGLE_A, SHINGLE_B, SHINGLE_R = 104, 100, 68
THATCH_A, THATCH_B, THATCH_R = 177, 176, 140
RUBBLE, RUBBLE_D, MORTAR = 182, 146, 218   # 毛石（淺灰米）、深一點的石、灰縫
SOD, SOD_D, EARTH_W = 113, 81, 140          # 胸牆的草皮、深一點的草、夯土

NAMES.update({BOARD: 'board', SHUT: 'shut', SHINGLE_A: 'shingle_a', SHINGLE_B: 'shingle_b', SHINGLE_R: 'shingle_r',
              THATCH_A: 'thatch_a', THATCH_B: 'thatch_b', THATCH_R: 'thatch_r', RUBBLE: 'rubble', SOD: 'sod'})


def shingle_color(x, y, facet, ridge, edge, salt=0):
    """木瓦：沿坡一排一排（每排 4 格高、排的下緣一道暗線）、每片 2～4 格寬錯開，一成的片深一色；屋脊與簷口深色。"""
    if ridge or edge:
        return SHINGLE_R
    a = x if facet in ('front', 'back') else y          # 沿簷口方向
    b = y if facet in ('front', 'back') else x          # 順坡方向
    row = b // 4
    if b % 4 == 3:
        return SHINGLE_R
    k = (a + (row % 2) * 2) // 3
    return SHINGLE_B if h01('sh', k, row, salt) < 0.08 else SHINGLE_A


def thatch_color(x, y, facet, ridge, edge, salt=0):
    """棕櫚茅草：順坡一束一束（顏色沿簷口方向成條）、簷口與屋脊深。"""
    if ridge or edge:
        return THATCH_R
    a = x if facet in ('front', 'back') else y
    b = y if facet in ('front', 'back') else x
    r = h01('th', a // 2, b // 7, salt)
    return THATCH_B if r < 0.3 else (THATCH_R if r < 0.36 else THATCH_A)


def board_walls(M, rect, z0, z1, t=2, color=BOARD, layer='body', posts=True, bay=0):
    """木板牆（橫向搭接的板，每 3 層一道暗線）；四角立柱（深色木，叉柱入土 fourches en terre：柱從 z 0 起）；bay ＞ 0 ⇒ 長牆每 bay 格再一根（史料：樑距 8 法尺 ≈ 26 格）。"""
    X0, Y0, X1, Y1 = rect
    for z in range(z0, z1):
        c = BOARD_D if (z - z0) % 3 == 2 else color
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                if X0 + t <= x < X1 - t and Y0 + t <= y < Y1 - t:
                    continue
                outer = x in (X0, X1 - 1) or y in (Y0, Y1 - 1)
                M.put(layer, x, y, z, c if outer else color)
    if posts:
        pts = [(X0, Y0), (X1 - 2, Y0), (X0, Y1 - 2), (X1 - 2, Y1 - 2)]
        if bay:
            pts += [(x, y) for x in range(X0 + bay, X1 - bay // 2, bay) for y in (Y0, Y1 - 2)]
            pts += [(x, y) for y in range(Y0 + bay, Y1 - bay // 2, bay) for x in (X0, X1 - 2)]
        for (cx, cy) in pts:
            M.box(layer, cx, cy, z0, cx + 2, cy + 2, z1, FRAME, force=True)


def daub_walls(M, rect, z0, z1, t=3, color=LIME, layer='body', bay=12):
    """編條糊泥（torchis／wattle and daub）刷石灰水：牆面白、外面露出立柱（每 bay 格一根）、底下地檻與頂上的牆梁。"""
    X0, Y0, X1, Y1 = rect
    stucco_walls(M, rect, z0, z1, t, color, layer)
    for z in range(z0, z1):
        sill = z < z0 + 2 or z >= z1 - 2
        for x in range(X0, X1):
            for y in (Y0, Y1 - 1):
                if sill or (x - X0) % bay in (0, 1) or x >= X1 - 2:
                    M.recolor(x, y, z, x + 1, y + 1, z + 1, FRAME)
        for y in range(Y0, Y1):
            for x in (X0, X1 - 1):
                if sill or (y - Y0) % bay in (0, 1) or y >= Y1 - 2:
                    M.recolor(x, y, z, x + 1, y + 1, z + 1, FRAME)


def rubble_walls(M, rect, z0, z1, t=4, layer='body', salt=0):
    """毛石牆（灰縫淺）：kit.rubble 換這一套的色。"""
    rubble(M, rect, z0, z1, t, layer, base=RUBBLE, mortar=MORTAR, course=5, block=7, salt=salt, dark=RUBBLE_D)


def piers(M, rect, z1, step=16, size=3, layer='body', color=RUBBLE):
    """架高的地板底下的石墩（每 step 格一個、四角一定有）。"""
    X0, Y0, X1, Y1 = rect
    xs = sorted(set(list(range(X0, X1 - size, step)) + [X1 - size]))
    ys = sorted(set(list(range(Y0, Y1 - size, step)) + [Y1 - size]))
    for x in xs:
        for y in ys:
            M.box(layer, x, y, 0, x + size, y + size, z1, color)


def palisade(M, pts, h=16, layer='body', gap=()):
    """木柵（palissade）：一根挨一根的削尖木樁（每根 1 格、頂端每隔一根高一格）、中間一道橫檔；gap ＝ 不立樁的 (x, y) 集合（院門）。"""
    for (a, b) in zip(pts, pts[1:]):
        (xa, ya), (xb, yb) = a, b
        n = max(abs(xb - xa), abs(yb - ya))
        for i in range(n + 1):
            x = xa + (i if xb > xa else -i if xb < xa else 0)
            y = ya + (i if yb > ya else -i if yb < ya else 0)
            if (x, y) in gap:
                continue
            top = h + (1 if (x + y) % 2 == 0 else 0)
            for z in range(0, top):
                M.put(layer, x, y, z, FRAME if z == 8 else (BOARD_D if z == top - 1 else BOARD))


def thatch_roof(M, rects, salt=0, thick=3, layer='roof'):
    F = roof_field(rects)
    return build_roof(M, F, thick, layer, color_fn=lambda x, y, f, r, e: thatch_color(x, y, f, r, e, salt))


def shingle_roof(M, rects, salt=0, thick=2, layer='roof'):
    F = roof_field(rects)
    return build_roof(M, F, thick, layer, color_fn=lambda x, y, f, r, e: shingle_color(x, y, f, r, e, salt))


def steps(M, x0, x1, y_front, n, rise, run=3, layer='gallery', color=FLOOR, back=True):
    """木台階：從 y_front 往前（−y）n 級，每級高 rise、深 run；最上一級頂 ＝ n × rise。back ⇒ 往 +y 走（台階朝後）。"""
    for k in range(n):
        zt = (n - k) * rise
        if back:
            ya, yb = y_front + k * run, y_front + (k + 1) * run
        else:
            ya, yb = y_front - (k + 1) * run, y_front - k * run
        M.box(layer, x0, ya, 0, x1, yb, zt, color)


def gallery_posts(M, xs, y, z0, top, w=2, layer='gallery', color=FRAME):
    """廊柱：每根 w × w、從 z0 立到屋面底下（top ＝ build_roof 回傳的高度場）。回傳柱頂最低的 z。"""
    zl = 999
    for px in xs:
        zt = min(top[(x, yy)] - 1 for x in range(px, px + w) for yy in range(y, y + w) if (x, yy) in top)
        M.box(layer, px, y, z0, px + w, y + w, zt, color)
        zl = min(zl, zt)
    return zl


def rail(M, x0, x1, y, z0, h=9, layer='gallery', color=FRAME, gap=None, axis='x', step=3):
    """木欄杆：一條扶手、一條底檔、每 step 格一根直條；axis ＝ 沿哪一軸；gap ＝ (a, b) 不做（台階）。"""
    for u in range(x0, x1):
        if gap and gap[0] <= u < gap[1]:
            continue
        p = (u, y) if axis == 'x' else (y, u)
        M.put(layer, p[0], p[1], z0 + h, color)
        M.put(layer, p[0], p[1], z0 + 1, color)
        if (u - x0) % step == 0:
            for z in range(z0 + 2, z0 + h):
                M.put(layer, p[0], p[1], z, color)


def gable_wall(M, x0, x1, y0, y1, ze, p, color=BOARD, edge=FRAME, layer='body', daub=False):
    """山牆（三角）：x ∈ [x0, x1)、牆厚 y ∈ [y0, y1)；頂 ＝ ze ＋ p × 離最近一邊的距離；外緣一圈 edge。
    木板 ⇒ 每 3 層一道暗線；daub ⇒ 石灰白牆，中線一根立柱。"""
    xm = (x0 + x1) // 2
    for x in range(x0, x1):
        d = min(x + 0.5 - x0, x1 - x - 0.5)
        zt = int(math.floor(ze + p * d))
        for z in range(ze, zt + 1):
            for y in range(y0, y1):
                if z >= zt - 1 or x in (x0, x1 - 1) or (daub and x in (xm - 1, xm)):
                    c = edge
                elif daub:
                    c = color
                else:
                    c = BOARD_D if (z - ze) % 3 == 2 and y in (y0, y1 - 1) else color
                M.put(layer, x, y, z, c, force=True)
