# 資源建築 B 糧與海（TASK-0927；Tim 2026-10-25「根據資源也把建築分成幾組(每組3~4種) 我先分配一下建造任務吧」「927 GO」）——
#   磨坊（mill：common 畜力磨、roman 塔式風車兩款）、漁場（fishery）、鹽田（saltpan）。
# 工具同 apex-one-industry-01m/design/industry.py（院子地、一堆、手推車、鏟子、實心毛石）⇐ trailhead-harbour-01m 的 workshops2／workshops／town3／quay
#   ⇐ ame-carib-civic-01m 的 harbour／civic ⇐ summit-carib-01m 的調色盤、Model、牆、屋頂、部件。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 地塊照 Blocksail world/buildings.js 的 lot：磨坊 8 × 12、漁場 8 × 12、鹽田 12 × 12。
# 配方（Blocksail world/recipes.js）：磨坊 麥 ⇒ 麵粉；漁場 捕魚；鹽田 曬鹽。配方、數字不動（TASK-0917 那一側）。
# 史料：這一批沒有上網查 ⇒ 配置全是設計，照通法（作品 references/README.md 寫了哪一格照什麼）。
import os, sys, math

AP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'apex-one-industry-01m', 'design')
if AP not in sys.path:
    sys.path.insert(1, AP)
from industry import *                                                 # noqa: F401,F403  stone_block、heap、wheelbarrow、shovel、yard_ground ＋ workshops2 以下的全部
from town3 import FISH, FISH_B                                         # noqa: E402  魚市那兩色（銀藍、灰一點）

MILLSTONE, MILLSTONE_D = 146, 110   # 磨石（灰、深一點的磨面）
OX, OX_D, HORN = 100, 68, 177       # 牛（褐）、深一點的蹄與鼻、角
LIMEST, LIMEST_D, MORT_R = 218, 182, 205   # 君士坦丁堡的石灰岩方石、深一點的石、粉紅厚灰漿（同 kaguya-roman-1453）
BRICK_RM = 168                      # 羅馬牆裡夾的磚帶
SAIL = 218                          # 風車的帆布（米白）
NET, NET_D = 68, 36                 # 漁網（浸過樹皮汁的深褐）、濕的更深
BRINE = 246                         # 濃縮中的鹵水（偏粉紅：鹽池裡的藻）
SEA_W = WATER                       # 剛引進來的海水（同 civic 的泉水 46）
SALT, SALT_D = 255, 218             # 鹽（白）、陰影面
TRAP = THATCH_A                     # 編的魚簍（稻草色）


def cone_roof(M, cx, cy, R, ze, p, color_fn, thick=2, layer='roof'):
    """圓錐頂：半徑 R（格）、簷口高 ze、坡度 p；坡面照方位分四面（色的條紋順著坡）。回傳 {(x, y): 頂 z}。"""
    F = {}
    for x in range(int(cx - R) - 1, int(cx + R) + 2):
        for y in range(int(cy - R) - 1, int(cy + R) + 2):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > R or not M.inb(x, y, 0):
                continue
            facet = ('front' if dy < 0 else 'back') if abs(dy) >= abs(dx) else ('left' if dx < 0 else 'right')
            F[(x, y)] = (ze + p * (R - d), facet, d < 1.2, 0)
    return build_roof(M, F, thick, layer, color_fn)


def ring_posts(M, top, cx, cy, r, n, a0=0.0):
    """圓錐頂底下一圈 n 根柱（2 × 2，立到屋面底下）。"""
    pts = []
    for k in range(n):
        a = a0 + 2 * math.pi * k / n
        pts.append((int(round(cx + r * math.cos(a))) - 1, int(round(cy + r * math.sin(a))) - 1))
    roof_posts(M, top, pts)


def sacks(M, x0, y0, nx, ny, layers=2, layer='body', color=SACK):
    """一疊麻袋（一個 5 × 4 × 3 格，往上一層少一個）。"""
    for k in range(layers):
        for i in range(nx - k):
            for j in range(ny):
                x, y, z = x0 + i * 5 + k * 2, y0 + j * 4, k * 3
                M.box(layer, x, y, z, x + 5, y + 4, z + 3, color if (i + j + k) % 3 else MORTAR)


def ox(M, x0, y0, layer='body'):
    """一頭牛（頭朝 −y）：身 6 × 14、腿四根、頭、兩支角、尾；x0, y0 ＝ 身子左前角。"""
    for (lx, ly) in ((0, 1), (4, 1), (0, 11), (4, 11)):
        M.box(layer, x0 + lx, y0 + ly, 0, x0 + lx + 2, y0 + ly + 2, 7, OX_D)
    M.box(layer, x0, y0, 7, x0 + 6, y0 + 14, 13, OX)
    M.box(layer, x0 + 1, y0 + 2, 13, x0 + 5, y0 + 7, 14, OX)            # 肩峰
    M.box(layer, x0 + 1, y0 - 5, 9, x0 + 5, y0, 14, OX)                # 頭
    M.box(layer, x0 + 2, y0 - 6, 9, x0 + 4, y0 - 5, 11, OX_D)          # 鼻
    for hx in (x0 + 1, x0 + 4):
        M.box(layer, hx, y0 - 3, 14, hx + 1, y0 - 2, 16, HORN)          # 角（長在頭頂兩側）
    M.box(layer, x0 + 2, y0 + 14, 5, x0 + 4, y0 + 15, 12, OX_D)        # 尾


# ─────────────────────────────── 磨坊（畜力磨）8 × 12 m ───────────────────────────────
def mill():
    """磨坊（mill，共用）：臨路一間木板的麵粉間（木板門、兩扇窗、麻袋、秤）；後面一座圓錐茅草頂的畜力磨（manège）——
    毛石磨台上下兩片磨石、磨石上的木斗、穿到屋頂的立軸、伸出去的拉桿、套著軛的一頭牛、走出一圈深色的環道；後門出去就是磨台。
    - 照什麼：加勒比海的城（法屬、英屬）沒有河可以架水車、也不常有風車 ⇒ 牲口拉的磨（manège、horse mill）；
      17 世紀加勒比海的穀物磨坊〔沒查到〕（當地麵粉多半船運，玉米、木薯在家裡手磨）⇒ 磨台、立軸直接帶磨石、圓錐頂照歐洲鄉間畜力磨的通法（設計）。"""
    X, Y, Z = 80, 120, 60
    M = Model((X, Y, Z))
    # 麵粉間（前半）：木板牆、木瓦兩坡頂
    R = (6, 6, 74, 38)                                                 # 6.8 × 3.2 m
    board_walls(M, R, 0, 28, 2, bay=26)
    M.box('body', R[0] + 2, R[1] + 2, 0, R[2] - 2, R[3] - 2, 1, FLOOR)
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 28, 0.7, z0=28)
    put_part(M, 'door-plank', '前-門', 'front', R, 40, 0, 2)
    put_part(M, 'window-board', '前-窗-左', 'front', R, 18, 9, 2)
    put_part(M, 'window-board', '前-窗-右', 'front', R, 62, 9, 2)
    put_part(M, 'door-plank', '後-門（往磨台）', 'back', R, 40, 0, 2)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 28, 'p': 0.7, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=9271)
    sacks(M, 9, 26, 4, 2, 3)                                           # 左牆邊一疊麵粉袋
    sacks(M, 52, 27, 3, 2, 2)
    M.box('body', 30, 26, 1, 32, 28, 22, FRAME)                        # 秤：一根柱、橫桿、兩個盤
    M.box('body', 23, 26, 22, 39, 28, 23, IRON)
    for cx in (24, 37):
        M.box('body', cx, 26, 15, cx + 1, 28, 22, IRON)
        M.box('body', cx - 2, 25, 14, cx + 3, 29, 15, IRON)
    # 畜力磨（後半）：圓錐茅草頂、八根柱
    cx, cy, Rr = 40, 78, 34
    yard_ground(M, 4, 42, 76, 116, salt=9272)
    for x in range(cx - 30, cx + 31):                                  # 牛走出來的環道（深一點的土）
        for y in range(cy - 30, cy + 31):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if 22 <= d <= 29 and M.inb(x, y, 0):
                M.put('body', x, y, 0, CLAY_D if h01('trk', x // 2, y // 2) < 0.75 else EARTH, True)
    top = cone_roof(M, cx, cy, Rr, 26, 0.75, lambda x, y, f, r, e: thatch_color(x, y, f, r, e, 9273))
    ring_posts(M, top, cx, cy, 31, 8, math.pi / 8)
    stone_block(M, cx - 9, cy - 9, 0, cx + 9, cy + 9, 6, salt=9274)    # 毛石磨台（1.8 m 見方、0.6 m 高）
    for x in range(cx - 8, cx + 8):                                    # 下磨石（不動）、上磨石（轉）
        for y in range(cy - 8, cy + 8):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 7.5:
                M.put('body', x, y, 6, MILLSTONE_D, True)
            if d <= 7.0:
                M.box('body', x, y, 7, x + 1, y + 1, 10, MILLSTONE if (x + y) % 5 else MILLSTONE_D, True)
    for (px, py) in ((cx - 7, cy + 4), (cx + 5, cy + 4)):              # 木斗的兩根腳（立在磨台上）
        M.box('body', px, py, 6, px + 2, py + 2, 18, FRAME)
    M.box('body', cx - 7, cy + 2, 18, cx + 7, cy + 8, 22, BOARD)       # 木斗（裝穀子）
    M.box('body', cx - 5, cy + 3, 21, cx + 5, cy + 7, 22, BREAD, True)
    z = 10                                                             # 立軸：從上磨石一路到屋面底下
    while z < Z - 1 and (cx, cy, z) not in M.cells:
        M.box('body', cx - 1, cy - 1, z, cx + 1, cy + 1, z + 1, FRAME)
        z += 1
    M.box('body', cx + 1, cy - 1, 14, cx + 27, cy + 1, 16, FRAME)      # 拉桿（往 +x 伸到牛背上）
    M.box('body', cx + 25, cy - 4, 12, cx + 27, cy - 2, 16, FRAME)     # 軛的立桿
    M.box('body', cx + 23, cy - 4, 12, cx + 30, cy - 3, 13, FRAME)     # 軛
    ox(M, cx + 23, cy - 2)
    M.box('body', cx - 12, cy - 11, 0, cx - 9, cy - 4, 4, FRAME)       # 出粉口下的木槽
    M.box('body', cx - 11, cy - 10, 3, cx - 10, cy - 5, 4, SACK, True)
    sacks(M, 8, 96, 3, 2, 2)                                           # 後院：等著磨的麥袋、手推車
    wheelbarrow(M, 60, 98, load=SACK)
    lantern(M, '燈籠-門', (48.5, R[1], 21))
    M.anchor('door', 40, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'mill', 'title': '磨坊（共用：臨路的木板麵粉間、麻袋與秤；後面圓錐茅草頂的畜力磨 —— 毛石磨台、兩片磨石、木斗、立軸與拉桿、一頭牛與環道）',
            'use': 'mill', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '麵粉間、磨台與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 磨坊（君士坦丁堡：塔式風車）8 × 12 m ───────────────────────────────
def roman_stone(x, y, z, salt=0):
    """君士坦丁堡的牆：石灰岩方石，每 12 層夾三皮紅磚（同 kaguya-roman-1453 的牆那一套色），灰縫粉紅。"""
    zz = z % 15
    if zz >= 12:
        return BRICK_RM if zz != 13 else MORT_R
    if zz % 4 == 3:
        return MORT_R
    return LIMEST_D if h01('rs', (x + (z // 4 % 2) * 3) // 6, y // 6, z // 4, salt) < 0.3 else LIMEST


def mill_wind():
    """磨坊（mill，君士坦丁堡 1453：roman）：一座石砌的圓塔風車（直徑 4.4 m、牆高 6.2 m；方石夾磚帶，同城牆那一套）、紅陶瓦圓錐頂；
    正面伸出風軸、八根輻、每根綁一張三角帆布；塔腳一扇木門、兩層小窗；門口麻袋、靠著塔的一片備用磨石；後院一道矮石牆圍的院子、石砌小倉、手推車。
    - 照什麼：愛琴海一帶的塔式風車（八根輻、三角帆）照通法；1453 年君士坦丁堡城裡磨坊的樣子〔沒查到〕（城裡也有牲口磨、水車在引水渠沿線）⇒ 塔形、帆數是設計。
      這一款給 roman 那一套的城（Blockside townPick 照城的風格先找 roman:mill，找不到才退到 common 的畜力磨）。"""
    X, Y, Z = 80, 120, 105
    M = Model((X, Y, Z))
    cx, cy, R, T, ZT = 40, 58, 22, 5, 62
    for x in range(cx - R - 3, cx + R + 3):                            # 塔：方石夾磚帶；塔腳一圈 0.3 m 高的石基
        for y in range(cy - R - 3, cy + R + 3):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= R + 2 and d > R - T - 2:
                M.box('body', x, y, 0, x + 1, y + 1, 3, LIMEST_D)
            if R - T < d <= R:
                for z in range(3, ZT):
                    M.put('body', x, y, z, roman_stone(x, y, z, 9275))
            if d <= R - T:
                M.put('body', x, y, 0, FLOOR)
                M.put('body', x, y, 30, FLOOR)                          # 二樓樓板（磨石在上面）
    M.clear(cx - 3, cy - 3, 30, cx + 4, cy + 4, 31)                     # 樓板留一個口（爬梯上去）
    for z in range(1, 30, 3):                                          # 爬梯
        M.box('body', cx - 3, cy + 2, z, cx + 4, cy + 3, z + 1, FRAME)
    for x in (cx - 3, cx + 3):
        M.box('body', x, cy + 2, 1, x + 1, cy + 4, 31, FRAME)
    for x in range(cx - 8, cx + 8):                                    # 樓上的磨石
        for y in range(cy - 2, cy + 14):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - (cy + 6))
            if d <= 6.5:
                M.box('body', x, y, 31, x + 1, y + 1, 35, MILLSTONE if d > 1.5 else MILLSTONE_D)
    # 門（正面，往裡縮一格的木板門）、兩層小窗
    M.clear(cx - 5, cy - R - 1, 0, cx + 6, cy - R + T + 2, 22)
    M.box('body', cx - 5, cy - R + T - 1, 1, cx + 6, cy - R + T, 22, SHUT)
    M.box('body', cx - 6, cy - R + T - 1, 22, cx + 7, cy - R + T + 1, 24, LIMEST_D)   # 門楣
    for (a, z0) in ((0.0, 40), (math.pi, 40), (math.pi / 2, 46), (-math.pi / 2 + 0.6, 40)):
        wx, wy = int(round(cx + (R - 2) * math.cos(a))), int(round(cy + (R - 2) * math.sin(a)))
        M.clear(wx - 2, wy - 2, z0, wx + 3, wy + 3, z0 + 6)
    # 紅陶瓦圓錐頂
    cone_roof(M, cx, cy, R + 3, ZT - 3, 1.0, lambda x, y, f, r, e: tile_color(x, y, f, r, e, 9276))
    # 風軸、輪轂、八根輻、三角帆 —— 自己一件（vanes）、施工最後才裝（build0 0.85 ⇒ 0.97；不然它自己一團由下往上掃，塔還沒起來帆就浮在半空）
    hz, hy = 66.5, 24
    rod(M, (cx + 0.5, hy - 1, hz), (cx + 0.5, cy - 4, hz), 1.7, FRAME, FRAME, layer='vanes')
    for x in range(cx - 3, cx + 4):
        for z in range(int(hz) - 4, int(hz) + 4):
            if math.hypot(x + 0.5 - cx - 0.5, z + 0.5 - hz) <= 3.2:
                M.box('vanes', x, hy - 1, z, x + 1, hy + 2, z + 1, FRAME, True)
    RS = 33
    ang = [math.radians(22.5 + 45 * k) for k in range(8)]
    for a in ang:
        rod(M, (cx + 0.5, hy + 0.5, hz), (cx + 0.5 + RS * math.cos(a), hy + 0.5, hz + RS * math.sin(a)), 0.75, FRAME, FRAME, layer='vanes')
    for x in range(cx - RS - 1, cx + RS + 2):                          # 帆：從輻的三成處開始，越往外越寬（一張帆搭在輻的逆時針那一側）
        for z in range(int(hz) - RS - 1, int(hz) + RS + 2):
            dx, dz = x + 0.5 - cx - 0.5, z + 0.5 - hz
            r = math.hypot(dx, dz)
            if not 10 <= r <= RS - 1:
                continue
            th = math.atan2(dz, dx)
            for a in ang:
                da = (th - a) % (2 * math.pi)
                if 0 < da < math.radians(26) * (r - 10) / (RS - 11) + math.radians(3):
                    M.put('vanes', x, hy, z, SAIL)
                    break
    # 門口：麻袋、靠著塔的備用磨石；後院：矮石牆、石砌小倉、手推車
    sacks(M, 10, 22, 3, 2, 2)
    for x in range(54, 68):
        for z in range(0, 14):
            if math.hypot(x + 0.5 - 61, z + 0.5 - 7) <= 6.8:
                M.box('body', x, 34, z, x + 1, 37, z + 1, MILLSTONE if (x + z) % 4 else MILLSTONE_D)
    for (xa, ya, xb, yb) in ((4, 86, 76, 88), (4, 86, 6, 118), (74, 86, 76, 118), (4, 116, 76, 118)):
        for x in range(xa, xb):
            for y in range(ya, yb):
                for z in range(12):
                    M.put('body', x, y, z, roman_stone(x, y, z + 3, 9277))
    M.clear(34, 86, 0, 46, 88, 12)                                     # 院門
    S = (48, 92, 74, 116)
    for x in range(S[0], S[2]):
        for y in range(S[1], S[3]):
            if x in (S[0], S[0] + 1, S[2] - 2, S[2] - 1) or y in (S[1], S[1] + 1, S[3] - 2, S[3] - 1):
                for z in range(24):
                    M.put('body', x, y, z, roman_stone(x, y, z, 9278))
    M.clear(56, S[1], 0, 64, S[1] + 2, 18)                              # 小倉的門洞（朝前）
    shed_roof(M, S[0] - 1, S[1] - 2, S[2] + 1, S[3] + 1, 30, 0.25, low='front', color_fn=lambda x, y, f, r, e: tile_color(x, y, f, r, e, 9279))
    yard_ground(M, 6, 88, 48, 116, salt=9280)
    wheelbarrow(M, 14, 96, load=SACK)
    sacks(M, 28, 104, 3, 2, 2)
    lantern(M, '燈籠-門', (32.5, cy - R + 2, 22))
    M.anchor('door', cx, cy - R - 3, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'mill-wind', 'title': '風車磨坊（君士坦丁堡：方石夾磚帶的圓塔、紅陶瓦圓錐頂、八根輻與三角帆布、樓上的磨石；後院矮石牆、石砌小倉）',
            'use': 'mill', 'lot': (8, 12), 'M': M, 'style': 'roman', 'variant': 'b', 'layers': {'body': '塔與擺設', 'vanes': '風軸、輻與帆', 'roof': '屋頂'},
            'layer_meta': {'vanes': {'part': 'vanes', 'build0': 0.85, 'build1': 0.97, 'sweep': 'z',
                                     # 照風轉（TASK-0939；標法同船的 spin，造船規格 §9.8）：每秒轉 spin_k × 風速（m/s）度；轉軸過輪轂中心、沿 y（正轉 ＝ 從正面看順時針，輻在前、帆拖在後）
                                     'spin': 'wind', 'spin_mode': 'rate', 'spin_k': 9, 'spin_pivot_x': 40.5, 'spin_pivot_y': 24.5, 'spin_pivot_z': 66.5,
                                     'spin_axis_x': 0, 'spin_axis_y': 1, 'spin_axis_z': 0}}}


# ─────────────────────────────── 漁場 8 × 12 m ───────────────────────────────
def rowboat(M, x0, x1, yc, zb, layer='body'):
    """一艘小划船（沿 x 長；墊在兩塊墊木上）：船殼一格厚、船底平、兩端收尖、舷緣往兩頭翹；兩道坐板。zb ＝ 船底那一層。"""
    L, xc, HB, D = x1 - x0, (x0 + x1) / 2, 8.0, 7
    for x in range(x0, x1):
        t = (x + 0.5 - xc) / (L / 2)
        hb = HB * max(0.0, 1 - t * t) ** 0.55
        if hb < 0.6:
            continue
        ztop = zb + D + int(round(2.5 * t * t))
        for z in range(zb, ztop):
            w = hb * ((z - zb + 1) / D) ** 0.45 if z - zb < D else hb
            for y in range(int(yc - w) - 1, int(yc + w) + 2):
                dy = abs(y + 0.5 - yc)
                if dy > w:
                    continue
                shell = z == zb or dy > w - 1.2 or abs(t) > 0.93
                if shell:
                    M.put(layer, x, y, z, FRAME if z >= ztop - 1 else BOARD)
    for xs in (int(xc) - 9, int(xc) + 7):                              # 坐板
        M.box(layer, xs, int(yc - HB) + 1, zb + D - 2, xs + 3, int(yc + HB), zb + D - 1, FLOOR)
    for xs in (x0 + 10, x1 - 13):                                       # 墊木
        M.box(layer, xs, int(yc) - 6, 0, xs + 3, int(yc) + 6, zb, FRAME)


def net_rack(M, x0, x1, y, h=24, layer='body'):
    """晾網架：兩端與中間的柱、頂上一根橫桿，網從橫桿垂下來（格子網：每 3 格一條線，四邊收一道）。"""
    for px in (x0, (x0 + x1) // 2 - 1, x1 - 2):
        M.box(layer, px, y, 0, px + 2, y + 2, h, FRAME)
    M.box(layer, x0, y, h, x1, y + 2, h + 1, FRAME)
    for x in range(x0 + 2, x1 - 2):
        if (x0 + x1) // 2 - 1 <= x <= (x0 + x1) // 2:
            continue
        sag = int(round(3 * math.sin(math.pi * ((x - x0) % ((x1 - x0) // 2)) / ((x1 - x0) // 2))))
        for z in range(6 + sag, h):
            if x % 3 == 0 or (z - sag) % 3 == 0 or z == 6 + sag:
                M.put(layer, x, y + 1, z, NET if h01('nt', x, z) < 0.85 else NET_D)


def fishery():
    """漁場（fishery，共用）：臨路一座開敞的茅草魚棚 —— 剖魚的長桌、一簍一簍的魚、醃魚的桶、鹽箱；中間兩道晾網架；後院墊木上一艘翻修中的小划船、
    靠著柱的兩支槳、一疊編的魚簍、四爪小錨、曬魚架。
    - 照什麼：漁場地塊在岸邊（適地 SUITS 照臨水），模型只管地塊裡的樣子；17 世紀加勒比海漁家的棚〔沒查到〕⇒ 魚棚、晾網、拖上岸的小船照各地漁村的通法（設計）。"""
    X, Y, Z = 80, 120, 60
    M = Model((X, Y, Z))
    R = (4, 4, 76, 44)                                                 # 魚棚 7.2 × 4 m（正面全開）
    M.box('body', R[0], R[1], 0, R[2], R[3], 1, RUBBLE)               # 石板地（好沖洗）
    for px in (R[0], 39, R[2] - 2):
        for py in (R[1], R[3] - 2):
            M.box('body', px, py, 1, px + 2, py + 2, 28, FRAME)
    board_walls(M, (R[0], R[3] - 2, R[2], R[3]), 1, 28, 2, posts=False)   # 後牆（擋風）
    for py in (R[1], R[3] - 2):
        M.box('body', R[0], py, 28, R[2], py + 2, 30, FRAME)
    thatch_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.7, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=9281)
    trestle_table(M, 8, 36, 22, 32, 8)                                 # 剖魚的長桌、桌上的魚
    for x in range(10, 34, 4):
        M.box('body', x, 24, 9, x + 2, 31, 10, FISH if (x // 4) % 3 else FISH_B)
    M.box('body', 26, 23, 9, 28, 25, 10, IRON, True)                   # 刀
    for (tx, ty) in ((46, 14), (54, 14), (46, 24)):                     # 一簍一簍的魚
        tub(M, tx, ty, 1, 6, 3.5, FISH)
    for (bx, by) in ((62, 30), (68, 30)):                              # 醃魚的桶（敞口、裝鹽水）
        tub(M, bx, by, 1, 9, 3.5, SALT_D)
    M.box('body', 58, 8, 1, 72, 16, 7, BOARD)                          # 鹽箱
    M.box('body', 59, 9, 6, 71, 15, 7, SALT, True)
    net_rack(M, 6, 74, 54)
    net_rack(M, 6, 74, 66, h=22)
    rowboat(M, 14, 66, 92, 4)
    for (ox0, ang) in ((70, 0.0), (74, 0.0)):                          # 兩支槳靠在後面的柱上
        rod(M, (ox0 + 0.5, 104.5, 0.5), (ox0 + 0.5, 110.5, 26.5), 0.7, FRAME, FRAME)
        M.box('body', ox0, 104, 0, ox0 + 1, 107, 6, BOARD, True)       # 槳葉
    M.box('body', 70, 111, 0, 76, 113, 30, FRAME)                      # 柱（槳靠著）
    for i, (tx, ty) in enumerate(((10, 106), (17, 106), (13, 106))):    # 魚簍（編的、橫放、口朝 +x ⇒ 兩個並排、上面再疊一個）
        z0 = 0 if i < 2 else 6
        for x in range(tx, tx + 6):
            for y in range(ty, ty + 6):
                for z in range(z0, z0 + 6):
                    if math.hypot(y + 0.5 - ty - 3, z + 0.5 - z0 - 3) <= 3 and (x == tx or math.hypot(y + 0.5 - ty - 3, z + 0.5 - z0 - 3) > 2):
                        M.put('body', x, y, z, TRAP if (x + y + z) % 3 else THATCH_R)
    M.box('body', 40, 110, 0, 41, 114, 1, IRON)                        # 四爪小錨（平放）＋錨繩一盤
    M.box('body', 38, 112, 0, 43, 113, 1, IRON)
    M.box('body', 40, 106, 0, 41, 110, 1, IRON)
    rope_coil(M, 50, 110, r=4, h=2)
    for px in (26, 56):                                                # 曬魚架（後緣）
        M.box('body', px, 116, 0, px + 2, 118, 20, FRAME)
    M.box('body', 26, 116, 18, 58, 118, 19, FRAME)
    for x in range(29, 55, 3):
        M.box('body', x, 116, 13, x + 2, 117, 18, FISH if (x // 3) % 4 else FISH_B)
    lantern(M, '燈籠-中柱', (40.5, R[1], 24))
    M.anchor('door', 40, 2, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'fishery', 'title': '漁場（共用：開敞的茅草魚棚、剖魚的長桌、魚簍與醃魚桶；兩道晾網架；後院墊木上的小划船、槳、魚簍、小錨、曬魚架）',
            'use': 'fishery', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '魚棚、晾網架、小船與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 漁場水上版 8 × 20 m（TASK-0963）───────────────────────────────
DECK_Z = 15                         # 平台面（遊戲畫的木板頂）在模型 z 1.5 m ⇒ 成品 meta deckz 1.5；模型自己的地板在 z 15（比遊戲的板高一格，不跟它的頂面打架）、上面的東西從 16 起


def shift(M, Mp, dz):
    """暫存的框 Mp（z 0 ＝ 地板上）⇒ M 的 z 往上 dz：格、外部模型（燈籠）都搬。"""
    for (x, y, z), (ly, c) in sorted(Mp.cells.items()):
        M.put(ly, x, y, z + dz, c)
    for m in Mp.models:
        m = dict(m)
        m['at'] = [m['at'][0], m['at'][1], m['at'][2] + dz]
        M.models.append(m)
    M.oob += Mp.oob


def boat_y(M, y0, y1, xc, zb=0, layer='body'):
    """沿 y 的小划船（浮在水上：船底在 zb、沒有墊木）—— 照 rowboat 在暫存的框裡長（船底 z 0 ⇒ 墊木那一段是空的），再轉 90°、抬到 zb（船寬 x xc ± 9、長 y0～y1）。"""
    T = Model((y1 - y0, 20, 14))
    rowboat(T, 0, y1 - y0, 10, 0, layer)
    for (x, y, z), (ly, c) in sorted(T.cells.items()):
        M.put(ly, int(xc) - 10 + y, y0 + x, z + zb, c)


def traps(M, tx, ty, layer='body'):
    """三個編的魚簍（橫放、口朝 +x）：兩個並排、上面再疊一個（同陸上版）。"""
    for i, (x0, y0) in enumerate(((tx, ty), (tx + 7, ty), (tx + 3, ty))):
        z0 = 0 if i < 2 else 6
        for x in range(x0, x0 + 6):
            for y in range(y0, y0 + 6):
                for z in range(z0, z0 + 6):
                    r = math.hypot(y + 0.5 - y0 - 3, z + 0.5 - z0 - 3)
                    if r <= 3 and (x == x0 or r > 2):
                        M.put(layer, x, y, z, TRAP if (x + y + z) % 3 else THATCH_R)


def fishery_water():
    """漁場水上版（fishery，共用；TASK-0963）：海堤、棧橋臨水那一側的木樁平台 —— 前面 8 × 8 m 的平台上一座開敞的茅草魚棚（剖魚的長桌、魚簍、醃魚桶、鹽箱）、
    兩道晾網架、一疊魚簍與一盤繩；後面一條 2 m 寬、12 m 長的窄棧橋伸到海上：尾端兩根繫船樁、一道下水的梯子，兩旁各繫一條小划船。
    - 照什麼：Tim 2026-10-26 的參考圖（水上的方平台、上面一間棚、後面伸出一條窄棧橋）「魚場是否可以參考這個 要有棧橋到海上(本體可以蓋在棧橋上)」「可以蓋在海堤 棧橋上」。
      17 世紀加勒比海漁家的棧橋〔沒查到〕⇒ 配置是設計。
    - 平台與樁由遊戲畫（Blocksail world/town.js WATER.fishery：8 × 20 m、jetty 12 × 2 m）：模型的 z 15 ＝ 平台面（meta deckz 1.5）、y 0 ＝ 正面（朝碼頭）；
      模型多鋪一層地板（比遊戲的板高 0.1 m、範圍一樣）、尾端的繫船樁與梯子往下伸到 z 0、小船的底在 z 3（水面在 z 1～5：碼頭面 1.0～1.4 m）。"""
    X, Y, Z = 80, 200, 62
    M = Model((X, Y, Z))
    JX0, JX1, JY = 30, 50, 80                                          # 窄棧橋：x 30～50（2 m）、y 80 起（12 m）
    for x in range(X):                                                 # 地板：平台的板沿 y、棧橋的板橫鋪
        for y in range(JY):
            M.put('body', x, y, DECK_Z, FLOOR if (x // 3) % 2 else BOARD)
    for x in range(JX0, JX1):
        for y in range(JY, Y):
            M.put('body', x, y, DECK_Z, FLOOR if (y // 3) % 2 else BOARD)
    for px in (JX0, JX1 - 2):                                          # 繫船樁（尾端，伸出板面 1.2 m）、半路兩根（伸出 0.2 m）
        M.box('body', px, 195, 0, px + 2, 197, DECK_Z + 13, FRAME)
        M.box('body', px, 138, 0, px + 2, 140, DECK_Z + 3, FRAME)
    for x in (37, 42):                                                 # 下水梯：掛在尾端那一緣
        M.box('body', x, Y - 1, 2, x + 1, Y, DECK_Z, FRAME)
    for z in range(3, DECK_Z, 3):
        M.box('body', 38, Y - 1, z, 42, Y, z + 1, BOARD)
    boat_y(M, 136, 188, 18, 3)                                         # 兩旁各一條小划船（船底 z 0.3 m：碼頭面 1.0 m 吃水 0.2 m、木棧橋 1.4 m 浮高 0.2 m —— 水面 0 m 加浪），繩繫在尾端的樁上
    boat_y(M, 126, 178, 62, 3)
    rod(M, (18.5, 186.5, 12.5), (30.5, 195.5, DECK_Z + 10.5), 0.9, ROPE, ROPE)
    rod(M, (62.5, 176.5, 12.5), (48.5, 195.5, DECK_Z + 10.5), 0.9, ROPE, ROPE)

    P = Model((X, JY, 46))                                             # 平台上（z 0 ＝ 地板上）
    R = (6, 4, 74, 38)                                                 # 魚棚 6.8 × 3.4 m（正面全開）
    for px in (R[0], 39, R[2] - 2):
        for py in (R[1], R[3] - 2):
            P.box('body', px, py, 0, px + 2, py + 2, 26, FRAME)
    board_walls(P, (R[0], R[3] - 2, R[2], R[3]), 0, 26, 2, posts=False)   # 後牆（擋風）
    for py in (R[1], R[3] - 2):
        P.box('body', R[0], py, 26, R[2], py + 2, 28, FRAME)
    thatch_roof(P, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 28, 'p': 0.7, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=9282)
    trestle_table(P, 10, 36, 20, 30, 8)                                # 剖魚的長桌、桌上的魚、刀
    for x in range(12, 34, 4):
        P.box('body', x, 22, 9, x + 2, 29, 10, FISH if (x // 4) % 3 else FISH_B)
    P.box('body', 28, 21, 9, 30, 23, 10, IRON, True)
    for (tx, ty) in ((46, 12), (54, 12), (46, 21)):                     # 一簍一簍的魚
        tub(P, tx, ty, 0, 6, 3.5, FISH)
    for (bx, by) in ((62, 27), (68, 27)):                              # 醃魚的桶
        tub(P, bx, by, 0, 9, 3.5, SALT_D)
    P.box('body', 58, 8, 0, 72, 16, 6, BOARD)                          # 鹽箱
    P.box('body', 59, 9, 5, 71, 15, 6, SALT, True)
    net_rack(P, 2, 28, 50)                                             # 兩道晾網架（中間留路往棧橋）
    net_rack(P, 52, 78, 50, h=22)
    traps(P, 58, 66)
    rope_coil(P, 20, 70, r=4, h=2)
    lantern(P, '燈籠-中柱', (40.5, R[1], 22))
    shift(M, P, DECK_Z + 1)
    J = Model((X, Y, 12))                                              # 棧橋上：一簍魚、一盤繩
    tub(J, 35, 170, 0, 5, 3, FISH)
    rope_coil(J, 44, 184, r=3, h=2)
    shift(M, J, DECK_Z + 1)
    M.anchor('door', 40, 1, DECK_Z + 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'fishery-water', 'title': '漁場水上版（共用：木樁平台上開敞的茅草魚棚、剖魚的長桌、魚簍與醃魚桶、晾網架；一條窄棧橋伸到海上，尾端的繫船樁、下水梯、兩旁繫著的小划船）',
            'use': 'fishery', 'lot': (8, 20), 'M': M, 'style': 'common', 'variant': 'b', 'meta': {'water': '2', 'deckz': '1.5'},
            'layers': {'body': '平台、魚棚、棧橋、小船與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 鹽田 12 × 12 m ───────────────────────────────
def salt_heap(M, cx, cy, r, h):
    heap(M, cx, cy, r, r, h, lambda x, y, z: SALT_D if (x + 0.5 - cx) > (y + 0.5 - cy) + 2 and h01('sh', x, y, z) < 0.6 else SALT)


def saltpan():
    """鹽田（saltpan，共用）：後面三排一格一格的淺池（土埂 0.2 m 高）—— 最後一排剛引進來的海水、中間一排濃縮中的鹵水（偏粉紅）、
    最前一排結晶的鹽（白、耙成小堆）；後緣一道引水溝與木閘門。臨路一間木板鹽倉（棕櫚茅草頂），旁邊兩座鹽堆、兩支長柄耙、裝鹽的手推車。
    - 照什麼：海鹽的曬鹽池一級一級濃縮（蓄水池 ⇒ 蒸發池 ⇒ 結晶池）、結晶池耙鹽成堆是各地鹽田的通法；
      加勒比海（Tortuga、Salt Tortuga、Turks 一帶）17 世紀耙鹽的天然鹽池〔讀過的只有「有」，樣子沒查到〕⇒ 池的格數、大小是設計。"""
    X, Y, Z = 120, 120, 50
    M = Model((X, Y, Z))
    # 鹽池：x 4..116、y 46..112，4 欄 × 3 排；土埂 2 格寬、2 格高；池底一層土、池面一層（水、鹵水、鹽）
    xs = [4, 32, 60, 88, 116]
    ys = [46, 68, 90, 112]
    stage = {0: SALT, 1: BRINE, 2: SEA_W}
    for x in range(4, 116):
        for y in range(46, 114):
            bank = any(v - 1 <= x <= v for v in xs) or any(v - 1 <= y <= v for v in ys)
            if bank:
                M.box('body', x, y, 0, x + 1, y + 1, 2, EARTH if h01('bk', x // 2, y // 2) < 0.8 else CLAY_D)
            else:
                row = 0 if y < 68 else (1 if y < 90 else 2)
                M.put('body', x, y, 0, CLAY_D)
                M.put('body', x, y, 1, stage[row] if not (row == 0 and h01('cr', x // 2, y // 2) < 0.08) else SALT_D)
    for (cx, cy) in ((14, 56), (24, 60), (44, 54), (52, 60), (74, 57), (100, 55)):   # 結晶池裡耙成的小堆
        salt_heap(M, cx, cy, 3.2, 3)
    # 後緣的引水溝與木閘門
    for x in range(4, 116):
        for y in range(114, 118):
            M.put('body', x, y, 0, CLAY_D)
            M.put('body', x, y, 1, SEA_W if 114 < y < 117 else EARTH)
    M.box('body', 58, 112, 0, 62, 118, 6, FRAME)                       # 閘門的兩根柱與板
    M.box('body', 58, 113, 2, 62, 114, 6, BOARD, True)
    # 臨路的鹽倉（木板、棕櫚茅草兩坡頂）
    R = (8, 6, 60, 38)                                                 # 5.2 × 3.2 m
    board_walls(M, R, 0, 30, 2)
    M.box('body', R[0] + 2, R[1] + 2, 0, R[2] - 2, R[3] - 2, 1, FLOOR)
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 30, 0.8, z0=30)
    put_part(M, 'door-double', '前-門', 'front', R, 34, 0, 2)
    put_part(M, 'window-board', '右-窗', 'right', R, 22, 9, 2)
    thatch_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.8, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=9282)
    salt_heap(M, 22, 26, 9, 9)                                         # 倉裡的鹽堆
    # 鹽倉旁：兩座鹽堆、長柄耙、手推車
    salt_heap(M, 80, 22, 11, 14)
    salt_heap(M, 102, 26, 9, 11)
    for (rx, ry) in ((66, 40), (92, 41)):                               # 長柄耙（平放在池埂上：柄 2.4 m、耙頭 0.6 m）
        M.box('body', rx, ry, 0, rx + 24, ry + 1, 1, FRAME)
        M.box('body', rx + 24, ry - 3, 0, rx + 25, ry + 4, 1, BOARD)
    wheelbarrow(M, 66, 8, load=SALT)
    M.models += [{'name': '鹽桶', 'source': 'summit-rocher-01m-barrel', 'at': [112, 10, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-門', (48.5, R[1], 22))
    M.anchor('door', 34, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'saltpan', 'title': '鹽田（共用：三排淺池 —— 海水、粉紅的鹵水、結晶的鹽耙成小堆；後緣引水溝與木閘門；臨路的木板鹽倉、兩座鹽堆、長柄耙、手推車）',
            'use': 'saltpan', 'lot': (12, 12), 'M': M, 'style': 'common', 'layers': {'body': '鹽池、鹽倉與擺設', 'roof': '屋頂'}}


ALL = [mill, mill_wind, fishery, fishery_water, saltpan]
