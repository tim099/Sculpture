# 西班牙風格（es）的城鎮建築（TASK-0975；Tim 2026-10-26「看一下是否需要增加新的建築吧」⇒「開建築單吧 go」⇒「/scp-task 975 開工」）。
# 第一批：聖地牙哥（TASK-0958）、聖多明哥（TASK-0960）三套都沒有模型、在遊戲裡是空地的五種 —— 碉堡、醫院、海關、小教堂、監獄。
# 工具同 basecamp-livestock-01m（⇐ trailhead-harbour-01m 的 forts.py、town3.py ⇐ ame-carib-civic-01m ⇐ summit-carib-01m 的調色盤、Model、牆、屋頂、部件）。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 跟 carib（法屬木構）、en（英國磚）不同的地方（史料與設計的分界寫在 references/README.md；查不到的一律「設計」）：
#   - 牆：砌石（mampostería）刷石灰白，牆腳一道珊瑚石（piedra coralina）的勒腳、轉角隅石、門的石框（portada）都用暖色的切石（sillería）。
#   - 屋頂：紅陶瓦（teja；同 kit 的三色混鋪）。
#   - 窗：車製木欄杆的窗（rejas de madera；借 summit 的欄杆窗）；監獄、火藥庫用鐵條窗。
#   - 教堂類：正面一面鐘牆（espadaña）高出屋頂、拱洞掛鐘。
#   - 碉堡：切石的方形四角稜堡、牆腳往外斜（escarpa）、稜堡尖上的圓形哨亭（garita，圓頂、托在石托上）。
import math
import numpy as np
from scipy import ndimage
from forts import *                                                    # noqa: F401,F403  pip_grid、cut_embrasure、gun_model、powder_keg ＋ town3／quay／civic／carib 的全部
from forts import POWDER                                               # noqa: E402,F401
from townpub import trestle_table, bench                               # noqa: E402
from english import tile_roof, beam_scale, balcony                     # noqa: E402
from civic import hollow, put_mask, flagpole_on                        # noqa: E402
from public import flag_sail                                           # noqa: E402

CORAL, CORAL_D, CORAL_J = 177, 146, 218      # 珊瑚石（暖的砂岩色）、深一點的石、灰縫 —— 勒腳、隅石、門框、拱券、碉堡的牆
CAL = LIME                                   # 石灰白（同 carib 的 LIME 255）—— 刷白的砌石牆
FLOOR_T = 168                                # 陶磚地（losas de barro）
PLAQUE, PLAQUE_G, PLAQUE_R = 182, 248, 160   # 石牌、金、紅（王室紋章的石牌；形制是設計）


# ─────────────────────────────── 牆、石作 ───────────────────────────────
def coral_color(x, y, z, z0=0, salt=0):
    """切石（sillería）：一皮 4 格、每塊 9 格長、上下皮錯開半塊；灰縫淺。"""
    row = (z - z0) // 4
    u = x + y + (4 if row % 2 else 0)
    if (z - z0) % 4 == 3 or u % 9 == 0:
        return CORAL_J
    return CORAL_D if h01('cs', u // 9, row, salt) < 0.15 else CORAL


def masonry(M, rect, z0, z1, t=5, layer='body', plinth=6, salt=0):
    """刷白的砌石牆（mampostería encalada）＋牆腳一道 plinth 格高的切石勒腳＋四角的切石隅石。"""
    X0, Y0, X1, Y1 = rect
    stucco_walls(M, rect, z0, z1, t, CAL, layer)
    for x in range(X0, X1):
        for y in range(Y0, Y1):
            if X0 + t <= x < X1 - t and Y0 + t <= y < Y1 - t:
                continue
            for z in range(z0, min(z1, z0 + plinth)):
                M.put(layer, x, y, z, coral_color(x, y, z, z0, salt), force=True)
    quoins(M, rect, z0 + plinth, z1, color=CORAL, long=7, short=4, step=5, layer=layer)


def portal(M, rect, cx, w=20, h=27, face='front', salt=0):
    """門的石框（portada）：門部件兩側各一根 3 格寬的切石壁柱、凸出牆外 1 格；上面一道 3 格高的楣、再上一層 2 格的簷線。
    只做 front、back 兩面（壁柱落在部件框的外面 ⇒ 不撞部件）。"""
    X0, Y0, X1, Y1 = rect
    yo = Y0 - 1 if face == 'front' else Y1
    ys = range(yo, yo + 1)
    a, b = cx - w // 2, cx + w // 2
    for y in ys:
        for x in list(range(a - 3, a)) + list(range(b, b + 3)):
            for z in range(0, h + 1):
                M.put('body', x, y, z, coral_color(x, 0, z, 0, salt), force=True)
        for x in range(a - 4, b + 4):
            for z in range(h + 1, h + 4):
                M.put('body', x, y, z, CORAL_J if z == h + 3 else CORAL, force=True)
            for z in range(h + 4, h + 6):
                if a - 2 <= x < b + 2:
                    M.put('body', x, y, z, CORAL, force=True)


def plaque(M, rect, cx, z0, face='front'):
    """王室紋章的石牌（設計）：10 × 12 格、凸出牆外 1 格；中間一塊紅、上面一道金（冠）。"""
    X0, Y0, X1, Y1 = rect
    y = Y0 - 1 if face == 'front' else Y1
    for x in range(cx - 5, cx + 5):
        for z in range(z0, z0 + 12):
            c = PLAQUE
            if cx - 3 <= x < cx + 3 and z0 + 2 <= z < z0 + 8:
                c = PLAQUE_R
            elif cx - 3 <= x < cx + 3 and z0 + 9 <= z < z0 + 11:
                c = PLAQUE_G
            M.put('body', x, y, z, c, force=True)


def espadana(M, xc, y0, y1, z0, w=22, steps=((0, 22), (22, 6), (28, 4)), arch=(10, 14, 6), layer='body', bell=True):
    """鐘牆（espadaña）：牆厚 y0..y1，從 z0 往上一段一段收窄 —— steps ＝ [(從 z0 起幾格, 這一段的寬)…]，最後一段頂上一支石十字；
    第一段開一個圓拱洞 arch ＝ (洞寬, 洞底離 z0 幾格, 洞高到拱頂起點)，拱洞裡掛一口鐘（鐵桿吊在拱頂）。回傳 (鐘的中心, 頂 z)。"""
    segs = []
    for i, (dz, ww) in enumerate(steps):
        top = z0 + (steps[i + 1][0] if i + 1 < len(steps) else dz + 6)
        segs.append((z0 + dz, top, ww))
    for (za, zb, ww) in segs:
        for x in range(xc - ww // 2, xc + ww // 2):
            for y in range(y0, y1):
                for z in range(za, zb):
                    c = CAL
                    if x in (xc - ww // 2, xc + ww // 2 - 1) or z == zb - 1:
                        c = CORAL
                    M.put(layer, x, y, z, c, force=True)
    zt = segs[-1][1]
    for y in range(y0 + 1, y1 - 1):                                    # 石十字
        M.box(layer, xc - 1, y, zt, xc + 1, y + 1, zt + 9, CORAL, force=True)
        M.box(layer, xc - 4, y, zt + 5, xc + 4, y + 1, zt + 7, CORAL, force=True)
    aw, ab, ah = arch
    zs = z0 + ab + ah                                                  # 拱頂起點（半圓的圓心高）
    r = aw / 2.0
    for x in range(xc - aw // 2, xc + aw // 2):
        for z in range(z0 + ab, int(zs + r) + 1):
            dx = x + 0.5 - xc
            if z < zs or dx * dx + (z + 0.5 - zs) ** 2 <= r * r:
                M.clear(x, y0, z, x + 1, y1, z + 1, layer)
    bc = None
    if bell:
        ztop = int(zs + r)                                             # 拱頂那一層（實心）
        while M.get(xc, (y0 + y1) // 2, ztop) is None and ztop < zt:
            ztop += 1
        yc = (y0 + y1) // 2
        M.box(layer, xc - 1, yc, ztop - 3, xc + 1, yc + 1, ztop, IRON, force=True)
        for z in range(ztop - 10, ztop - 3):                           # 鐘：上窄下寬
            rr = 1 + (z - (ztop - 10)) * 0 + (ztop - 3 - z) // 2
            for x in range(xc - rr - 1, xc + rr + 1):
                for y in range(yc - min(rr, (y1 - y0) // 2 - 1), yc + min(rr, (y1 - y0) // 2 - 1) + 1):
                    M.put(layer, x, y, z, BRONZE, force=True)
        bc = (xc, yc, ztop - 7)
    return bc, zt


def arcade(M, x0, x1, y0, y1, piers, z_spring, z_top, layer='body', fill=CAL):
    """拱廊（soportal、claustro）：x0..x1 × y0..y1 從地面砌到 z_top 的實心牆，照 piers ＝ [(a, b)…]（墩的 x 範圍）留墩、墩之間挖成半圓拱的洞（拱頂 ＝ z_spring ＋ 半跨）。
    墩、拱券（洞緣 2 格）是切石，拱上的三角（spandrel）刷白。"""
    M.box(layer, x0, y0, 0, x1, y1, z_top, fill)
    ps = sorted(piers)
    for (a, b) in ps:
        for x in range(a, b):
            for y in range(y0, y1):
                for z in range(0, z_spring):
                    M.put(layer, x, y, z, coral_color(x, y, z), force=True)
    for (pa, pb), (qa, qb) in zip(ps, ps[1:]):
        a, b = pb, qa
        xc, r = (a + b) / 2.0, (b - a) / 2.0
        for x in range(a, b):
            for z in range(0, z_top):
                dx = x + 0.5 - xc
                inside = z < z_spring or dx * dx + (z + 0.5 - z_spring) ** 2 <= r * r
                ring = not inside and (z < z_spring + 1 or dx * dx + (z + 0.5 - z_spring) ** 2 <= (r + 2) ** 2)
                for y in range(y0, y1):
                    if inside:
                        M.clear(x, y, z, x + 1, y + 1, z + 1, layer)
                    elif ring and z >= z_spring - 1:
                        M.put(layer, x, y, z, CORAL, force=True)


def tile_floor(M, x0, y0, x1, y1, z=0, layer='body'):
    """陶磚地（一格一塊、每 4 格一道灰縫的方格）。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            M.put(layer, x, y, z, CORAL_J if (x % 6 == 0 or y % 6 == 0) else FLOOR_T)


def cobbles(M, x0, y0, x1, y1, z=0, layer='body', salt=0):
    """石鋪的前庭（atrio）：大小兩色的石塊。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            M.put(layer, x, y, z, CORAL_D if h01('cb', x // 3, y // 3, salt) < 0.4 else CORAL)


def aljibe(M, cx, cy, r=7, h=8, layer='body'):
    """蓄水池的井口（aljibe：屋頂與院子的雨水流進地下的池子）—— 方的切石井欄、中間暗的井口、上面一道木轆轤架（設計）。"""
    M.box(layer, cx - r, cy - r, 0, cx + r, cy + r, h, CORAL)
    M.box(layer, cx - r + 2, cy - r + 2, 1, cx + r - 2, cy + r - 2, h, DARK, force=True)
    for x in (cx - r, cx + r - 2):
        M.box(layer, x, cy - 1, h, x + 2, cy + 1, h + 14, FRAME)
    M.box(layer, cx - r, cy - 1, h + 14, cx + r, cy + 1, h + 16, FRAME)


def gable_end(M, x0, x1, y0, y1, ze, p, over=3, color=CAL, edge=CORAL, layer='body'):
    """正面的山牆（frontispicio）：x ∈ [x0, x1)、牆厚 y ∈ [y0, y1)，屋脊沿 y；頂 ＝ ze ＋ p × 離最近一邊 ＋ over（高出屋面、蓋住瓦的斷面）；頂上兩格石壓頂。"""
    for x in range(x0, x1):
        d = min(x + 0.5 - x0, x1 - x - 0.5)
        zt = int(math.floor(ze + p * d)) + over
        for z in range(ze, zt + 1):
            for y in range(y0, y1):
                M.put(layer, x, y, z, edge if z >= zt - 1 else color, force=True)


def yield_to_parts(M, ground_only=False):
    """部件（門、窗）的格蓋過牆與鋪地 ⇒ 讓給部件（不然 link_overlap）。"""
    for L in M.links:
        for k in L['cells']:
            if (not ground_only or k[2] == 0) and k in M.cells:
                del M.cells[k]


# ─────────────────────────────── 小教堂（ermita）8 × 12 m ───────────────────────────────
def chapel():
    """小教堂（ermita）：一間的砌石刷白小堂（5.6 × 9.4 m、牆厚 0.6 m、牆高 4.2 m）、紅陶瓦兩坡頂（屋脊沿進深）；
    正面的山牆高出屋面、山牆頂上一面鐘牆（espadaña）、一個拱洞掛一口鐘、頂上石十字；切石門框的雙扇木門；兩側高處各一扇木欄杆窗；
    裡面陶磚地、後牆的祭壇與木作的祭壇屏（retablo）、四排長凳；門前石鋪的前庭與一支石十字（cruz de atrio）。
    - 照什麼：哈瓦那 Guanabacoa 的 Potosí 小堂 1644 年先是「木板與棕櫚葉（tabla y guano）」、1675 年改成切石與砌石、木作的穆德哈爾式頂（alfarje）〔摘：Diario de Cuba〕
      ⇒ 1660 年代兩種都有；這裡做砌石的那一種（跟 carib 的蘆葦小堂分開）。鐘牆是西班牙鄉間小堂的通法〔摘：只查到西班牙本土的例子〕。
    - 設計：尺寸、牆高、鐘牆的收分、祭壇屏、前庭的十字。"""
    X, Y, Z = 80, 120, 100
    M = Model((X, Y, Z))
    R = (12, 14, 68, 108)                                              # 5.6 × 9.4 m
    t, H = 6, 42
    cobbles(M, 4, 0, 76, R[1], salt=9751)                              # 前庭（到正面牆）
    masonry(M, R, 0, H, t, salt=9752)
    tile_floor(M, R[0] + t, R[1] + t, R[2] - t, R[3] - t)                # 地板在牆之後（masonry 會清掉牆裡面）
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.55, 'over': (4, 4, 0, 4), 'gable': 'y'}], salt=9753)
    gable_end(M, R[0], R[2], R[1], R[1] + t, H, 0.55, over=3)          # 正面山牆高出屋面
    zg = int(math.floor(H + 0.55 * 28)) + 3                            # 山牆頂（中線）
    bc, zt = espadana(M, 40, R[1], R[1] + t, zg - 1, w=22, steps=((0, 22), (20, 12), (26, 6)), arch=(10, 3, 9))
    put_part(M, 'door-double', '前-門', 'front', R, 40, 0, t)
    portal(M, R, 40, 20, 27, salt=9754)
    for cy in (52, 84):
        put_part(M, 'window-baluster', '左-窗%d' % (1 if cy < 70 else 2), 'left', R, cy, 20, t)
        put_part(M, 'window-baluster', '右-窗%d' % (1 if cy < 70 else 2), 'right', R, cy, 20, t)
    # 祭壇、祭壇屏（木作描金）、十字；長凳兩列四排（中間走道）
    M.box('body', 28, 92, 1, 52, 100, 10, CAL)                         # 祭壇（砌石刷白）
    M.box('body', 27, 91, 10, 53, 101, 11, CORAL)
    for x in range(24, 56):                                            # 祭壇屏：靠後牆一片木作、三格一道金線
        for z in range(11, 38):
            M.put('body', x, 101, z, PLAQUE_G if (x - 24) % 8 == 0 or z in (11, 24, 37) else FRAME)
    M.box('body', 39, 100, 26, 41, 101, 36, PLAQUE_G)
    M.box('body', 36, 100, 31, 44, 101, 33, PLAQUE_G)
    for y in (40, 52, 64, 76):
        for (a, b) in ((22, 36), (44, 58)):
            bench(M, a, b, y, y + 3)
    # 前庭的石十字（座三級）
    M.box('body', 6, 4, 1, 16, 12, 3, CORAL)
    M.box('body', 8, 6, 3, 14, 10, 5, CORAL)
    M.box('body', 10, 7, 5, 12, 9, 28, CORAL)
    M.box('body', 7, 7, 20, 15, 9, 22, CORAL)
    lantern(M, '燈籠-門左', (25.5, R[1], 24))
    yield_to_parts(M)
    M.anchor('door', 40, R[1] - 2, 1)
    M.anchor('bell', *bc)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'chapel', 'style': 'es',
            'title': '小教堂（ermita：砌石刷白的一間小堂、紅陶瓦兩坡頂、正面鐘牆 espadaña 掛一口鐘、切石門框、木欄杆窗；祭壇屏、長凳；石鋪前庭與石十字）',
            'use': 'chapel', 'lot': (8, 12), 'M': M, 'layers': {'body': '牆與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 監獄（cárcel）12 × 14 m ───────────────────────────────
def jail():
    """監獄（cárcel real）：臨路一棟兩層的砌石刷白屋（樓下衛兵與看守、樓上典獄長 alcaide 住；10.8 × 5 m、兩層 6.2 m）、紅陶瓦四坡頂；
    樓下鐵條窗、樓上木欄杆窗；切石門框、門上王室紋章的石牌；後面刷白的高牆圍放風院、院底三間平頂（azotea、石壓頂）的牢房（calabozos）、院子的蓄水池井口。
    - 照什麼：《印地亞斯法》cabildo 與監獄圍著廣場〔摘〕；聖多明哥、哈瓦那的監獄跟 cabildo 同一棟或相鄰〔沒查到形制〕。
    - 設計：兩層、平面、鐵條窗、平頂牢房、紋章的樣子（跟 carib 那一座同一個擺法：前屋、院、院底牢房）。"""
    X, Y, Z = 120, 140, 100
    M = Model((X, Y, Z))
    # 放風院的高牆
    masonry(M, (6, 60, 114, 136), 0, 40, 4, salt=9761)
    M.clear(10, 60, 0, 110, 64, 40)
    M.box('body', 10, 64, 0, 110, 132, 1, EARTH_W)
    # 前屋：兩層
    R = (6, 12, 114, 64)
    t, H1, H = 5, 30, 62
    masonry(M, R, 0, H, t, salt=9762)
    tile_floor(M, R[0] + t, R[1] + t, R[2] - t, R[3] - t)
    M.box('body', R[0] + t, R[1] + t, H1, R[2] - t, R[3] - t, H1 + 2, FLOOR)   # 樓板
    M.box('body', 58, R[1] + t, 1, 62, R[3] - t, H1, CAL)              # 樓下的隔牆（左衛兵、右看守）
    put_part(M, 'door-plank', '隔牆-門', 'left', (58, R[1] + t, 62, R[3] - t), 38, 0, 4)
    put_part(M, 'door-double', '前-門', 'front', R, 60, 0, t)
    portal(M, R, 60, 20, 27, salt=9763)
    plaque(M, R, 60, 36)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 84, 0, t)
    for c in (24, 96):
        barred(M, 'front', R, c, 12, 8, 10, t)
        put_part(M, 'window-baluster', '前-樓上窗%d' % (1 if c < 60 else 2), 'front', R, c, 40, t)
    for f in ('left', 'right'):
        barred(M, f, R, 38, 12, 8, 8, t)
        put_part(M, 'window-baluster', '%s-樓上窗' % {'left': '左', 'right': '右'}[f], f, R, 38, 40, t)
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.55, 'over': (3, 3, 4, 3)}], salt=9764)
    # 樓下：看守的桌凳、掛鐐銬的架
    trestle_table(M, 14, 34, 30, 40, 8)
    bench(M, 14, 34, 44, 47)
    M.box('body', 70, 52, 1, 72, 54, 20, FRAME)
    M.box('body', 104, 52, 1, 106, 54, 20, FRAME)
    M.box('body', 70, 52, 20, 106, 54, 22, FRAME)
    for x in range(74, 104, 6):
        M.box('body', x, 53, 12, x + 1, 54, 20, IRON)
        M.box('body', x - 1, 53, 11, x + 2, 54, 12, IRON)
    # 院底三間牢房：平頂（azotea）＋石壓頂、各一扇厚木門、後牆高處鐵條小窗
    C = (10, 104, 110, 132)
    masonry(M, C, 0, 30, 4, salt=9765)
    for x0 in (42, 75):
        M.box('body', x0, C[1], 0, x0 + 4, C[3], 30, CAL)
    M.box('body', C[0], C[1], 30, C[2], C[3], 32, CAL)
    for x in range(C[0], C[2]):
        M.put('body', x, C[1], 32, CORAL)
        M.put('body', x, C[1], 33, CORAL)
    for i, cx in enumerate((26, 59, 93)):
        put_part(M, 'door-plank', '牢房-門%d' % (i + 1), 'front', C, cx, 0, 4)
        barred(M, 'back', (6, 60, 114, 136), cx, 26, 6, 6, 4)
    aljibe(M, 90, 82, 6, 7)
    lantern(M, '燈籠-門', (40.5, R[1], 26.5))
    yield_to_parts(M)
    M.anchor('door', 60, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'jail', 'style': 'es',
            'title': '監獄（cárcel real：兩層砌石刷白屋、紅陶瓦四坡頂、樓下鐵條窗、樓上木欄杆窗、切石門框與紋章石牌；高牆圍的放風院、院底三間平頂牢房、蓄水池井口）',
            'use': 'jail', 'lot': (12, 14), 'M': M, 'layers': {'body': '屋、院牆與牢房', 'roof': '屋頂'}}


# ─────────────────────────────── 海關（aduana）16 × 14 m ───────────────────────────────
def customs():
    """海關（aduana、contaduría）：兩層砌石刷白、臨路一道四跨的拱廊（soportal：樓上壓在拱上、拱廊深 2.4 m），紅陶瓦四坡頂；
    拱廊下一座大橫桿秤與待驗的貨（糖桶、貨箱）；樓下臨拱廊的雙扇門與木欄杆窗、樓上一道木陽台（balcón volado）與木欄杆窗、門上王室紋章的石牌；後面圍牆的貨院。
    - 照什麼：聖多明哥的 Atarazanas Reales（1509～1541 起造）同一棟裡是船廠、倉庫、海關與收稅的地方〔摘：Wikipedia〕；
      聖多明哥街屋的陽台 16 世紀還很少、後來越來越多（陽台有石、磚、木、鐵）〔摘：El Día〈Los balcones de la Ciudad Colonial〉〕。
    - 設計：平面、拱廊（Atarazanas 的列柱門廳據說是 18 世紀加的〔摘〕⇒ 1660 年代有沒有拱廊沒查到）、秤、陽台的位置、紋章。"""
    X, Y, Z = 160, 140, 110
    M = Model((X, Y, Z))
    t, H1, H = 5, 32, 64
    R = (4, 4, 156, 104)                                               # 15.2 × 10 m（樓上整塊；樓下前面 2.4 m 是拱廊）
    RG = (4, 28, 156, 104)                                             # 樓下的牆（拱廊後面那一道是正面）
    masonry(M, RG, 0, H1, t, salt=9771)
    masonry(M, (R[0], R[1], R[2], R[3]), H1, H, t, plinth=0, salt=9772)
    quoins(M, R, H1, H, color=CORAL, long=7, short=4, step=5)
    # 拱廊：四跨、墩 0.6 m
    piers = [(4, 10), (40, 46), (77, 83), (114, 120), (150, 156)]
    arcade(M, 4, 156, 4, 10, piers, 18, H1)
    for (a, b) in piers:                                               # 墩往裡一道到正面牆（拱廊兩側的牆＝邊上那兩個墩）
        if a in (4, 150):
            M.box('body', a, 10, 0, b, RG[1], H1, CAL)
    tile_floor(M, 10, 10, 150, RG[1])
    M.box('body', 4, 4, H1, 156, 28, H1 + 2, CAL, force=True)          # 拱廊頂（＝樓上的地板）
    tile_floor(M, RG[0] + t, RG[1] + t, RG[2] - t, RG[3] - t)
    M.box('body', R[0] + t, R[1] + t, H1, R[2] - t, R[3] - t, H1 + 2, FLOOR)
    put_part(M, 'door-double', '樓下-大門', 'front', RG, 80, 0, t)
    portal(M, RG, 80, 20, 27, salt=9773)
    for i, cx in enumerate((24, 136)):
        put_part(M, 'window-baluster', '樓下-窗%d' % (i + 1), 'front', RG, cx, 8, t)
    put_part(M, 'cartdoor', '後-貨門', 'back', R, 80, 0, t)
    # 樓上：正面四扇窗＋中間一道陽台（陽台在拱廊頂上方、從牆往外 3 格）
    for i, cx in enumerate((24, 58, 102, 136)):
        put_part(M, 'window-baluster', '樓上-窗%d' % (i + 1), 'front', R, cx, H1 + 10, t)
    balcony(M, 46, 114, 1, 4, H1 + 6, layer='body')                     # 陽台跟牆身同一層（這一棟沒有 gallery 那一層）
    plaque(M, R, 80, H1 + 12)
    for f in ('left', 'right'):
        put_part(M, 'window-baluster', '%s-樓上窗' % {'left': '左', 'right': '右'}[f], f, R, 60, H1 + 10, t)
        put_part(M, 'window-baluster', '%s-樓下窗' % {'left': '左', 'right': '右'}[f], f, RG, 66, 8, t)
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': H, 'p': 0.5, 'over': (3, 3, 3, 3)}], salt=9774)
    # 拱廊下：大橫桿秤、待驗的貨
    beam_scale(M, 120, 16, 1)
    M.models += [{'name': '糖桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [20, 14, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '糖桶-2', 'source': 'summit-rocher-01m-barrel', 'at': [32, 14, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-1', 'source': 'summit-rocher-01m-crate', 'at': [56, 16, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-2', 'source': 'summit-rocher-01m-crate', 'at': [96, 16, 1], 'pivot': [6, 6, 0], 'meta': {}}]
    # 後面的貨院：刷白的圍牆、木柵門
    masonry(M, (4, 104, 156, 138), 0, 26, 4, plinth=4, salt=9775)
    M.clear(8, 104, 0, 152, 108, 26)
    M.box('body', 8, 108, 0, 152, 134, 1, EARTH_W)
    M.clear(66, 134, 0, 94, 138, 26)                                   # 後門洞
    for x in range(66, 94, 3):
        M.box('body', x, 135, 1, x + 2, 137, 22, FRAME)
    M.box('body', 66, 135, 10, 94, 137, 12, FRAME)
    M.box('body', 66, 134, 0, 94, 138, 1, EARTH_W)
    lantern(M, '燈籠-拱廊', (66.5, RG[1], 22))
    yield_to_parts(M)
    M.anchor('door', 80, 2, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'customs', 'style': 'es',
            'title': '海關（aduana：兩層砌石刷白、臨路四跨拱廊、紅陶瓦四坡頂、樓上木陽台與木欄杆窗、紋章石牌；拱廊下大橫桿秤與待驗的貨；後面圍牆的貨院）',
            'use': 'customs', 'lot': (16, 14), 'M': M, 'layers': {'body': '牆、拱廊、陽台與貨院', 'roof': '屋頂'}}


# ─────────────────────────────── 醫院（hospital）20 × 16 m ───────────────────────────────
def hospital():
    """醫院：臨路一長棟（19.2 × 7 m）左端是小堂（鐘牆、雙扇門）、右邊是病房（兩排床）；後面一個院子，院底一排廚房與藥房、前面一道三跨的拱廊（平頂）（claustro 的一邊）；院子中間的蓄水池井口、兩畦藥草。
    - 照什麼：聖多明哥的 San Nicolás de Bari（1503～1552）是教堂兼醫院（中間一道當禮拜、兩側住病人；拉丁十字、四個院子）〔摘：Afar、SAH、El Día〕
      ⇒ 小一號的城照「小堂＋病房＋院子」三樣組；Hospital 跟教堂同一棟、院子圍著拱廊是這一型的通法（形制照它、比例照地塊縮）。
    - 設計：一長棟的配置（十字形放不進 20 × 16 m）、牆高、拱廊跨數、藥草畦、床數。"""
    X, Y, Z = 200, 160, 110
    M = Model((X, Y, Z))
    t, H = 6, 44
    R1 = (4, 6, 196, 76)
    masonry(M, R1, 0, H, t, salt=9781)
    tile_floor(M, R1[0] + t, R1[1] + t, R1[2] - t, R1[3] - t)
    M.box('body', 60, R1[1] + t, 1, 66, R1[3] - t, H, CAL)               # 小堂與病房之間的牆
    put_part(M, 'door-plank', '隔牆-門', 'left', (60, R1[1] + t, 66, R1[3] - t), 58, 0, t)
    tile_roof(M, [{'x0': R1[0], 'y0': R1[1], 'x1': R1[2], 'y1': R1[3], 'ze': H, 'p': 0.55, 'over': (3, 3, 4, 4), 'gable': 'x'}], salt=9782)
    for x0, x1 in ((R1[0], R1[0] + t), (R1[2] - t, R1[2])):
        end_gable(M, x0, x1, R1[1], R1[3], H, 0.55, z0=H, color=CAL, edge=CORAL)
    bc, zt = espadana(M, 32, R1[1], R1[1] + t, H - 1, w=20, steps=((0, 20), (22, 10), (28, 4)), arch=(10, 6, 8))   # 小堂的鐘牆：正面牆往上
    put_part(M, 'door-double', '小堂-門', 'front', R1, 32, 0, t)
    portal(M, R1, 32, 20, 27, salt=9783)
    put_part(M, 'door-double', '病房-門', 'front', R1, 128, 0, t)
    portal(M, R1, 128, 20, 27, salt=9784)
    plaque(M, R1, 128, 34)
    for i, cx in enumerate((86, 104, 152, 174)):
        put_part(M, 'window-baluster', '前-窗%d' % (i + 1), 'front', R1, cx, 16, t)
    for i, cx in enumerate((86, 152, 174)):
        put_part(M, 'window-baluster', '後-窗%d' % (i + 1), 'back', R1, cx, 16, t)
    put_part(M, 'door-plank', '病房-後門', 'back', R1, 116, 0, t)
    put_part(M, 'window-baluster', '小堂-側窗', 'left', R1, 41, 18, t)
    # 小堂：祭壇
    M.box('body', 14, 52, 1, 50, 62, 10, CAL)
    M.box('body', 13, 51, 10, 51, 63, 11, CORAL)
    M.box('body', 31, 62, 11, 33, 63, 30, PLAQUE_G)
    M.box('body', 27, 62, 22, 37, 63, 24, PLAQUE_G)
    # 病房：兩排床（靠前牆、後牆）
    for x0 in range(70, 190, 12):
        if 116 <= x0 <= 138:
            continue
        for (y0, y1) in ((14, 30), (52, 68)):
            M.box('body', x0, y0, 1, x0 + 8, y1, 4, FRAME)
            M.box('body', x0, y0, 4, x0 + 8, y1, 5, CAL)
    # 院子：兩側院牆、院底一排廚房與藥房（兩坡瓦頂）、前面三跨拱廊
    masonry(M, (4, 76, 196, 156), 0, 30, 4, plinth=4, salt=9785)
    M.clear(8, 76, 0, 192, 80, 30)
    R2 = (4, 120, 196, 156)
    masonry(M, R2, 0, 34, 5, salt=9786)
    M.box('body', 100, 125, 1, 104, 151, 34, CAL)
    tile_roof(M, [{'x0': R2[0], 'y0': R2[1], 'x1': R2[2], 'y1': R2[3], 'ze': 34, 'p': 0.55, 'over': (3, 3, 0, 3), 'gable': 'x'}], salt=9787)
    put_part(M, 'door-plank', '廚房-門', 'front', R2, 52, 0, 5)
    put_part(M, 'door-plank', '藥房-門', 'front', R2, 148, 0, 5)
    put_part(M, 'window-baluster', '藥房-窗', 'front', R2, 176, 10, 5)
    arcade(M, 60, 146, 106, 112, [(60, 66), (86, 92), (114, 120), (140, 146)], 14, 28)
    M.box('body', 60, 106, 28, 146, 120, 30, CORAL, force=True)          # 拱廊頂（平頂，石壓頂）
    tile_floor(M, 66, 112, 140, 120)
    hearth(M, 20, 140, 36, 150, hanger=False)
    for x in range(150, 186, 6):                                       # 藥房的藥櫃
        M.box('body', x, 148, 1, x + 4, 151, 22, FRAME)
    aljibe(M, 100, 92, 7, 8)
    for (x0, x1) in ((16, 50), (150, 184)):                            # 兩畦藥草
        for y in range(84, 100):
            for x in range(x0, x1):
                M.put('body', x, y, 0, GRASS if (y - 84) % 4 < 2 else EARTH_W)
    lantern(M, '燈籠-病房門', (112.5, R1[1], 24))
    yield_to_parts(M)
    M.anchor('door', 128, R1[1] - 1, 0)
    M.anchor('bell', *bc)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'hospital', 'style': 'es',
            'title': '醫院（hospital：臨路一長棟砌石刷白、左端小堂與鐘牆、右邊兩排床的病房、紅陶瓦兩坡頂、切石門框與紋章石牌；後院三跨拱廊、廚房與藥房、蓄水池井口、藥草畦）',
            'use': 'hospital', 'lot': (20, 16), 'M': M, 'layers': {'body': '病房、小堂與院子', 'roof': '屋頂'}}


# ─────────────────────────────── 碉堡（fuerte）30 × 30 m ───────────────────────────────
def garita(M, cx, cy, z0, r=7, h=22, layer='rampart'):
    """圓形哨亭（garita）：z0 往下 12 格是倒錐的石托（從半徑 2 長到 r）、z0 起圓筒 h 格（三面各一道窺孔）、上面半球頂＋頂上一顆石珠。"""
    for z in range(z0 - 12, z0):
        rr = 2 + (r - 2) * (z - (z0 - 12)) / 12.0
        for x in range(int(cx - rr) - 1, int(cx + rr) + 2):
            for y in range(int(cy - rr) - 1, int(cy + rr) + 2):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= rr * rr:
                    M.put(layer, x, y, z, CORAL, force=True)
    for z in range(z0, z0 + h + r + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for y in range(int(cy - r) - 1, int(cy + r) + 2):
                d2 = (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2
                if z < z0 + h:
                    if (r - 2) ** 2 < d2 <= r * r:
                        M.put(layer, x, y, z, CAL if z > z0 + 1 else CORAL, force=True)
                    elif d2 <= (r - 2) ** 2 and z == z0:
                        M.put(layer, x, y, z, CORAL, force=True)
                else:
                    dz = z + 0.5 - (z0 + h)
                    if d2 + dz * dz <= r * r:
                        M.put(layer, x, y, z, CORAL if dz < 1.5 else CAL, force=True)
    M.box(layer, int(cx) - 1, int(cy) - 1, z0 + h + r, int(cx) + 1, int(cy) + 1, z0 + h + r + 3, CORAL, force=True)


def fort():
    """碉堡（fuerte）：切石的方形四角稜堡（同 trailhead 的 bastion_fort 那一套：幕牆線離框 6 m、土台寬 3 m、胸牆 0.7 m、九個砲眼與 6 磅砲、正面門洞、左邊坡道、火藥庫、旗杆）；
    換成西班牙的作法：
    - 牆是珊瑚石的切石、牆腳往外斜（escarpa：從牆腳到土台頂往裡收 0.4 m）、土台頂下一道半圓的腰線（cordón）；
    - 四座稜堡尖上各一座圓形哨亭（garita：石托、圓筒、半球頂）；
    - 操場裡的營房刷白、紅陶瓦，火藥庫切石＋紅陶瓦；井換成蓄水池井口（aljibe）；門上王室紋章的石牌。
    - 照什麼：哈瓦那 Real Fuerza（1558～1577）近正方形、每邊 30 多公尺、四角各一座稜堡、海岸的石灰岩砌、斜牆、壕溝與吊橋〔摘：Wikipedia、ancient-history-sites〕；
      garita 是西班牙加勒比海堡壘的特徵（圓筒、圓頂）〔摘：USF ClipPix〈Fort Matanzas〉〕；聖地牙哥的莫羅堡（San Pedro de la Roca）是另一座特殊建築（不在這張）。
    - 設計：沒有壕溝（地塊只有 30 × 30 m）、牆高、砲數、哨亭的大小、營房與火藥庫。"""
    W, Z = 300, 130
    M = Model((W, W, Z))
    T, a, s, f = 4, 60, 45, 24
    B = W - a
    poly = [(a, a + s), (a - f, a + s), (T, T), (a + s, a - f), (a + s, a),
            (B - s, a), (B - s, a - f), (W - T, T), (B + f, a + s), (B, a + s),
            (B, B - s), (B + f, B - s), (W - T, W - T), (B - s, B + f), (B - s, B),
            (a + s, B), (a + s, B + f), (T, W - T), (a - f, B - s), (a, B - s)]
    inside = pip_grid(poly, W, W)
    d = ndimage.distance_transform_edt(inside)
    BAND, PAR, HT, HP, BAT = 30, 7, 36, 48, 4                          # 土台寬、胸牆厚、土台頂、胸牆頂、斜牆收進幾格
    S = np.zeros((W, W, Z), bool)
    for z in range(HT):                                                # escarpa：越高往裡收越多
        cut = BAT * z / float(HT)
        S[:, :, z] = inside & (d <= BAND) & (d > cut)
    S[:, :, HT:HP] |= (inside & (d <= PAR) & (d > BAT))[:, :, None]
    GX0, GX1, GH = 140, 160, 28
    S[GX0:GX1, :a + BAND + 2, :GH] = False
    ramp = np.zeros((W, W), bool)
    for y in range(120, 200):
        h = int(round(HT * (200 - y) / 80))
        S[90:104, y, :h] = True
        ramp[90:104, y] = True
    gp = HT
    guns = [(125, a + PAR + 14, 0, -1), (175, a + PAR + 14, 0, -1),
            (a + PAR + 14, 150, -1, 0), (B - PAR - 14, 150, 1, 0), (150, B - PAR - 14, 0, 1),
            (46, 46, 0.30, -0.95), (W - 46, 46, -0.30, -0.95), (W - 46, W - 46, -0.30, 0.95), (46, W - 46, 0.30, 0.95)]   # 稜堡的砲從朝前、朝後那一面打出去（尖上站哨亭）
    for (gx, gy, dx, dy) in guns:
        cut_embrasure(S, inside, gx, gy, dx, dy, HT + 4, HP, half=4)
    S = hollow(S, keep=6)
    par = inside & (d <= PAR)

    def color(x, y, z):
        if ramp[x, y]:
            return EARTH_W
        if z == HT - 1 and not par[x, y]:
            return SOD if h01('sd', x // 4, y // 4) < 0.35 else EARTH_W
        if z == HP - 1 and par[x, y]:
            return CORAL_J
        if HT - 3 <= z < HT - 1 and d[x, y] <= BAT + 2:                # 腰線
            return CORAL_J
        return coral_color(x, y, z, 0, 9791)
    put_mask(M, S, color, layer='rampart')
    M.box('rampart', GX0, a, 0, GX1, a + BAND + 2, 1, CORAL, force=True)
    M.box('rampart', GX0 - 2, a, GH, GX1 + 2, a + 6, GH + 2, CORAL_J, force=True)        # 門楣（斜牆在這一高收進 3 格 ⇒ 楣深 6 格才砌進牆裡）
    put_part(M, 'door-double', '門', 'front', (a + s, a, B - s, a + BAND), 150, 0, 2)
    lantern(M, '燈籠-門', (134.5, a, 26))
    M.anchor('door', 150, a - 1, 0)
    # 稜堡尖的哨亭：中心在尖往裡（沿對角線）1.3 m 的胸牆上
    for (cx, cy) in ((17, 17), (W - 17, 17), (W - 17, W - 17), (17, W - 17)):
        garita(M, cx, cy, HP, r=7, h=22)
    # 門上的紋章石牌：貼在那一高的牆面外 1 格（斜牆 ⇒ 每一層的牆面不同）
    for z in range(31, 43):
        yf = next(y for y in range(a, a + BAND) if S[150, y, z])
        for x in range(145, 155):
            c = PLAQUE_R if 147 <= x < 153 and 33 <= z < 39 else (PLAQUE_G if 147 <= x < 153 and 40 <= z < 42 else PLAQUE)
            M.put('rampart', x, yf - 1, z, c, force=True)
    # 操場：營房（刷白、紅陶瓦）、火藥庫（切石、紅陶瓦）、蓄水池井口、旗杆
    R = (112, 172, 206, 206)
    masonry(M, R, 0, 30, 4, plinth=5, salt=9792)
    put_part(M, 'door-plank', '營房-門', 'front', R, 159, 0, 4)
    for cx in (128, 190):
        put_part(M, 'window-baluster', '營房-窗%d' % (1 if cx < 150 else 2), 'front', R, cx, 10, 4)
    tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.6, 'over': (3, 3, 3, 0), 'gable': 'x'}], salt=9793)
    MR = (170, 98, 204, 132)
    for x in range(MR[0], MR[2]):
        for y in range(MR[1], MR[3]):
            if MR[0] + 4 <= x < MR[2] - 4 and MR[1] + 4 <= y < MR[3] - 4:
                continue
            for z in range(0, 26):
                M.put('magazine', x, y, z, coral_color(x, y, z, 0, 9794))
    M.box('magazine', MR[0] + 4, MR[1] + 4, 0, MR[2] - 4, MR[3] - 4, 1, FLOOR)
    M.clear(MR[0], 109, 0, MR[0] + 4, 121, 22, 'magazine')
    put_part(M, 'door-plank', '火藥庫-門', 'left', MR, 115, 0, 4)
    tile_roof(M, [{'x0': MR[0], 'y0': MR[1], 'x1': MR[2], 'y1': MR[3], 'ze': 26, 'p': 0.7, 'over': (2, 2, 2, 2)}], salt=9795)
    aljibe(M, 126, 110, 7, 8)
    ft, fb = flagpole_on(M, 140, 140, 0, 110)
    M.anchor('flag', 140, 140, 111)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 30, toward=1)]
    guns_m = [gun_model('砲%d' % (i + 1), gx, gy, gp, dx, dy, '6l') for i, (gx, gy, dx, dy) in enumerate(guns)]
    kegs = [powder_keg('火藥桶-%d' % (i + 1), x, y, 1) for i, (x, y) in enumerate(((180, 106), (180, 120), (192, 106), (192, 120)))]
    yield_to_parts(M)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'fort', 'variant': 'a', 'style': 'es',
            'title': '碉堡（fuerte：切石四角稜堡、斜牆腳與腰線、稜堡尖四座圓頂哨亭 garita、九個砲眼與 6 磅砲、門上紋章石牌；操場的營房、火藥庫、蓄水池井口、旗杆）',
            'use': 'fort', 'lot': (30, 30), 'M': M, 'flags': flags,
            'layers': {'body': '操場（營房、井、旗杆）', 'rampart': '堡牆、土台與哨亭（甲板）', 'magazine': '火藥庫', 'roof': '屋頂'},
            'layer_meta': {'rampart': {'kind': 'deck', 'deck': 'rampart', 'level': 1, 'name': '土台', 'floor': '0:%d,%d:%d' % (HT, W, HT), 'thick': 6, 'material': 'stone'},
                           'magazine': {'kind': 'magazine', 'pos': 'mid', 'powder_lb': 100 * len(kegs), 'material': 'stone'}},
            'layer_anchors': {'magazine': {'blast': (187, 115, 10), 'door': (MR[0] - 1, 115, 0)}},
            'layer_models': {'rampart': guns_m, 'magazine': kegs}}


ALL = [chapel, jail, customs, hospital, fort]
