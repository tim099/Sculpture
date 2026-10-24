# 城鎮建材與營造（TASK-0894 第 ⑤ 步；Tim 2026-10-24「接著做第 ⑤ 步：新建築的模型與建築模式選單」）—— 六種，全部共用 common：
#   伐木場（lumber-camp）、黏土坑（clay-pit）、磚窯（brickworks）、礦坑（mine）、煉鐵場（ironworks）、營造廠（builder）。
# 工具同 trailhead-harbour-01m/design 的 workshops2.py（＋ workshops／town3／quay／harbour／civic／carib／kit 的全部）。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 地塊照 Blocksail world/buildings.js 的 lot（4 m 一格的整數倍）：伐木場 8 × 12、黏土坑 12 × 12、磚窯 12 × 12、礦坑 12 × 16、煉鐵場 12 × 16、營造廠 12 × 16。
# 配方（Blocksail docs/PRODUCTION.md §14）：伐木場 原木／木柴／木炭；黏土坑 黏土；磚窯 黏土＋木柴 ⇒ 磚；礦坑 礦石；煉鐵場 煉生鐵、鍛熟鐵；營造廠 建設量（吃建材）。
# 史料：作品 references/README.md；這一批沒有上網查 ⇒ 配置全是設計（照 17 世紀前後歐洲與北美殖民地的通法），寫在那一份。
from workshops2 import *                                               # noqa: F401,F403
from civic import crag_solid, put_mask, rock_color                     # noqa: E402

CLAY = 141                       # 黏土（濕的灰褐）
CLAY_D = 108                     # 坑底泡水的黏土（深）
CLAY_L = 177                     # 曬乾的黏土、生磚坯（淺褐）
BRICK_R = 168                    # 燒好的磚（紅）
BRICK_D = 136                    # 燒好的磚（深紅）
ORE = 132                        # 鐵礦石（紅褐）
SLAG = 73                        # 爐渣（暗灰藍）
SPOIL = 146                      # 廢石堆（灰）
LIMEW = 255                      # 石灰（白）
SAND = 213                       # 鑄床的砂（土黃）


def stone_block(M, x0, y0, z0, x1, y1, z1, salt=0, layer='body', force=False):
    """實心毛石塊（爐台、爐身）：0.5 × 0.4 m 的石塊錯縫，灰縫淺、石塊深淺不一。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(z0, z1):
                c = (z // 4 + (x if (z // 4) % 2 else x + 3) // 5 + y // 5) % 7
                col = MORTAR if z % 4 == 3 else (RUBBLE_D if h01('sb', salt, (x + (z // 4 % 2) * 3) // 5, y // 5, z // 4) < 0.35 else RUBBLE)
                if c == 0 and z % 4 != 3:
                    col = RUBBLE_D
                M.put(layer, x, y, z, col, force)


def heap(M, cx, cy, rx, ry, h, color_fn, z0=0, layer='body'):
    """一堆（圓錐、橢圓底）：每一柱高 h ×（1 − 離中心的比例）。"""
    for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            t = int(round(h * (1 - d)))
            if t > 0:
                for z in range(z0, z0 + t):
                    M.put(layer, x, y, z, color_fn(x, y, z))


def cord(M, x0, x1, y0, y1, h, layer='body'):
    """劈好的木柴堆（沿 x 一層一層，端面淺、每三層一道暗縫）。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(h):
                end = x in (x0, x1 - 1)
                col = LOG_TIP if end and (y + z) % 3 else (DARK if (y + z) % 5 == 0 and end else LOG)
                M.put(layer, x, y, z, col)


def wheelbarrow(M, x0, y0, load=None, layer='body'):
    """手推車（沿 +y：輪在前 y0、把手在後）：木斗 6 × 8 × 3、前面一個輪、兩根把手、兩隻腳；load ＝ 斗裡裝的色。"""
    M.box(layer, x0 + 3, y0, 0, x0 + 4, y0 + 1, 4, FRAME)                        # 輪（側看一條；著地）
    M.box(layer, x0, y0 + 2, 3, x0 + 7, y0 + 10, 4, BOARD)                       # 斗底
    for (xa, xb, ya, yb) in ((x0, x0 + 1, y0 + 2, y0 + 10), (x0 + 6, x0 + 7, y0 + 2, y0 + 10), (x0, x0 + 7, y0 + 2, y0 + 3), (x0, x0 + 7, y0 + 9, y0 + 10)):
        M.box(layer, xa, ya, 4, xb, yb, 6, BOARD)
    if load is not None:
        M.box(layer, x0 + 1, y0 + 3, 4, x0 + 6, y0 + 9, 6, load)
    for x in (x0, x0 + 6):
        M.box(layer, x, y0 + 10, 4, x + 1, y0 + 16, 5, FRAME)                    # 把手
        M.box(layer, x, y0 + 9, 0, x + 1, y0 + 10, 3, FRAME)                     # 腳


def shovel(M, x, y, z0, layer='body'):
    """斜靠的鏟子：木柄 ＋ 鐵頭（柄每往後一格先補一格 ⇒ 六連通，⛔ 斜著走只有邊碰邊 ⇒ 算成浮空）。"""
    for k in range(10):
        M.put(layer, x, y + k // 3, z0 + k, FRAME, True)
        if k and k % 3 == 0:
            M.put(layer, x, y + k // 3, z0 + k - 1, FRAME, True)
    M.box(layer, x - 1, y, z0 - 2, x + 2, y + 1, z0, IRON, True)


def yard_ground(M, x0, y0, x1, y1, salt=0, layer='body'):
    """踩實的院子地（一層）：灰褐的土、零星深一點的塊（⛔ EARTH_W 140 在遊戲裡是亮的芥末黃，整片院子會跳出來 —— 第一版在金斯敦看到的）。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            M.put(layer, x, y, 0, CLAY_D if h01('yg', salt, x // 3, y // 3) < 0.22 else EARTH)


# ─────────────────────────────── 伐木場 8 × 12 m ───────────────────────────────
def lumber_camp():
    """伐木場（lumber-camp）：臨路一塊劈柴的空地（樹墩上插著斧頭、X 字鋸木架上一段原木、劈好的柴一排）；中間一座開敞的木瓦單坡棚，
    棚下碼滿劈好的木柴；後院原木堆、一座悶燒的炭窯（土蓋的圓丘、頂上冒煙的口）、幾個樹墩。
    - 配方：伐原木、砍柴、燒炭（PRODUCTION §1.2）—— 燒炭在伐木場 ⇒ 後院一座炭窯（meule：木柴堆成圓丘、外面糊土悶燒）。
    - 17 世紀加勒比海的伐木營地〔沒查到〕⇒ 劈柴台、鋸木架、柴堆、炭窯照歐洲的通法（設計）。"""
    X, Y, Z = 80, 120, 60
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 78, 118, salt=8801)                                 # 踩實的地
    for x in range(4, 76):                                                       # 地上的木屑（前院一片）
        for y in range(4, 40):
            if h01('chip', x, y) < 0.18:
                M.put('body', x, y, 1, SAWDUST)
    # 前院：劈柴的樹墩（斧頭）、X 字鋸木架與原木、劈好的柴一排
    for x in range(14, 24):
        for y in range(14, 24):
            if math.hypot(x + 0.5 - 19, y + 0.5 - 19) <= 4.2:
                M.box('body', x, y, 1, x + 1, y + 1, 6, LOG)
    M.box('body', 17, 18, 6, 22, 20, 7, LOG_TIP, force=True)                     # 樹墩頂的年輪
    rod(M, (20.5, 19.5, 6.5), (26.5, 19.5, 13.5), 0.8, FRAME, FRAME)           # 斧柄
    M.box('body', 19, 18, 6, 22, 21, 8, IRON, force=True)                        # 斧頭（砍進樹墩）
    for (x, ya, yb) in ((40, 10, 22), (46, 10, 22), (40, 26, 38), (46, 26, 38)):
        rod(M, (x + 0.5, ya + 0.5, 1), (x + 6.5 - (x - 40), yb + 0.5 - 12 + 12, 11), 0.8, FRAME, FRAME) if False else None
    for y0 in (12, 32):                                                          # 兩座 X 字的鋸木架
        rod(M, (40.5, y0 + 0.5, 1), (52.5, y0 + 0.5, 12), 0.9, FRAME, FRAME)
        rod(M, (52.5, y0 + 0.5, 1), (40.5, y0 + 0.5, 12), 0.9, FRAME, FRAME)
    rod(M, (46.5, 6, 11.5), (46.5, 40, 11.5), 2.6)                             # 架上的一段原木
    cord(M, 60, 74, 8, 38, 9)                                                    # 劈好的柴一排（沿 y）
    # 中間：開敞的單坡棚（高的那邊朝後）、棚下滿滿的柴
    S = (6, 44, 74, 76)
    top = shed_roof(M, S[0] - 2, S[1] - 2, S[2] + 2, S[3] + 2, 34, 0.35, low='front', color_fn=lambda x, y, f, r, e: shingle_color(x, y, f, r, e, 8811))
    roof_posts(M, top, [(x, y) for x in (S[0], 38, S[2] - 2) for y in (S[1], S[3] - 2)])
    for xa, xb in ((9, 36), (41, 71)):
        cord(M, xa, xb, 54, 72, 16)
    # 後院：原木堆、炭窯、樹墩
    log_pile(M, 6, 46, 84, 3, 5)
    cx, cy, r = 60, 98, 14                                                       # 炭窯：土蓋的圓丘（半徑 1.4 m、高 1.2 m）
    for x in range(cx - r - 1, cx + r + 2):
        for y in range(cy - r - 1, cy + r + 2):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r
            t = int(round(12 * math.sqrt(max(0.0, 1 - d * d))))
            for z in range(t):
                M.put('body', x, y, z, CHAR if h01('sod', x // 3, y // 3, z // 3) < 0.15 else (EARTH if h01('sod2', x // 2, y // 2, z // 2) < 0.6 else CLAY_D))   # 糊的土（灰褐）、燒黑的幾塊
    M.box('body', cx - 1, cy - 1, 11, cx + 1, cy + 1, 13, CHAR, force=True)      # 頂上的煙口
    M.box('body', cx - 1, cy - 1, 12, cx + 1, cy + 1, 13, EMBER, force=True)
    M.anchor('smoke', cx, cy, 13)
    for k in range(4):                                                           # 炭窯下緣一圈通氣孔（暗）
        a = k * math.pi / 2 + 0.4
        M.put('body', int(cx + (r - 1) * math.cos(a)), int(cy + (r - 1) * math.sin(a)), 1, CHAR, True)
    for (x, y) in ((24, 100), (34, 108), (14, 110)):
        for xx in range(x - 3, x + 4):
            for yy in range(y - 3, y + 4):
                if math.hypot(xx + 0.5 - x, yy + 0.5 - y) <= 3:
                    M.box('body', xx, yy, 1, xx + 1, yy + 1, 4, LOG)
    shovel(M, 74, 90, 3)
    lantern(M, '燈籠-柱', (S[0], S[1] - 1, 22))
    M.anchor('door', 40, 4, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'lumber-camp', 'title': '伐木場（共用：劈柴的空地、樹墩與斧、X 字鋸木架、開敞的單坡柴棚；後院原木堆、悶燒的炭窯）',
            'use': 'lumber-camp', 'lot': (8, 12), 'M': M, 'style': 'common', 'layers': {'body': '空地、柴棚、炭窯與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 黏土坑 12 × 12 m ───────────────────────────────
def clay_pit():
    """黏土坑（clay-pit）：地挖不下去 ⇒ 四周堆起挖出來的土圍成一圈（0.9～1.2 m 高、內壁露出一層一層的黏土），圈裡是坑底泡水的黏土與一灘水；
    正面留一道缺口、兩塊踏板斜下到坑底；坑邊一座和泥的圓槽（中間立軸、一根橫桿：人推著轉、把黏土和勻）；兩台手推車、黏土堆；左後角茅草小棚放鏟子。
    - 史料：殖民地燒磚就地挖黏土、和泥、做坯（設計：通法）；坑挖不進地面 ⇒ 改成土圍（同鋸木坊的「坑改成架高」）。"""
    X, Y, Z = 120, 120, 50
    M = Model((X, Y, Z))
    P = (20, 30, 100, 100)                                                       # 坑（土圍裡面）
    M.box('body', P[0], P[1], 0, P[2], P[3], 1, CLAY_D)
    for x in range(P[0] - 14, P[2] + 14):                                        # 土圍：坡 1:1、頂寬 0.4 m，正面中間留缺口
        for y in range(P[1] - 14, P[3] + 14):
            if P[0] <= x < P[2] and P[1] <= y < P[3]:
                continue
            dx = max(P[0] - x - 1, x - P[2], 0)
            dy = max(P[1] - y - 1, y - P[3], 0)
            d = max(dx, dy)
            h = 12 - abs(d - 4) if d < 16 else 0
            h = min(h, 11 + int(3 * h01('rim', x // 6, y // 6)))
            if 52 <= x < 66 and y < P[1] + 2:
                h = 0                                                            # 缺口
            if not (0 <= x < X and 0 <= y < Y):
                continue
            for z in range(max(0, h)):
                inner = d <= 2
                col = (CLAY if z % 4 < 2 else CLAY_L) if inner else (SOD if z == h - 1 and h01('gr', x // 3, y // 3) < 0.25 else (EARTH if (z + x // 7) % 5 else CLAY_D))   # 挖出來的土（零星長了草）
                M.put('body', x, y, z, col)
    for x in range(P[0], P[2]):                                                  # 坑底：一灘水、腳印深淺
        for y in range(P[1], P[3]):
            if math.hypot((x + 0.5 - 76) / 14, (y + 0.5 - 78) / 9) < 1:
                M.put('body', x, y, 0, WATER, True)
            elif h01('ft', x // 2, y // 2) < 0.12:
                M.put('body', x, y, 0, CLAY, True)
    for k in range(2):                                                           # 缺口的兩塊踏板（斜下到坑底）
        for t in range(18):
            M.box('body', 54 + k * 6, 14 + t, 0, 58 + k * 6, 15 + t, 1 + (17 - t) // 3, BOARD, force=True)
    # 坑底：挖到一半的黏土塊、插著的鏟子、手推車
    heap(M, 40, 60, 10, 8, 6, lambda x, y, z: CLAY if (x + z) % 5 else CLAY_D)
    shovel(M, 46, 58, 2)
    wheelbarrow(M, 64, 44, CLAY)
    # 坑外右前：和泥的圓槽（直徑 2.6 m）、立軸、橫桿
    cx, cy = 104, 14
    for x in range(cx - 14, cx + 14):
        for y in range(cy - 13, cy + 14):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if 0 <= y < Y and 0 <= x < X:
                if 10 <= d < 13:
                    M.box('body', x, y, 0, x + 1, y + 1, 5, BOARD)
                elif d < 10:
                    M.box('body', x, y, 0, x + 1, y + 1, 4, CLAY)
    M.box('body', cx - 1, cy - 1, 0, cx + 1, cy + 1, 14, FRAME)
    rod(M, (cx + 0.5, cy + 0.5, 12.5), (cx - 12.5, cy + 0.5, 9.5), 0.8, FRAME, FRAME)
    # 正面：黏土堆、第二台手推車
    heap(M, 22, 12, 10, 7, 8, lambda x, y, z: CLAY_L if z > 4 else CLAY)
    wheelbarrow(M, 36, 2, CLAY_L)
    # 左後角：茅草小棚（鏟子、水桶）
    top = thatch_roof(M, [{'x0': 2, 'y0': 104, 'x1': 30, 'y1': 118, 'ze': 22, 'p': 0.6, 'over': (1, 1, 2, 1), 'gable': 'x'}], salt=8821)
    roof_posts(M, top, [(3, 105), (27, 105), (3, 115), (27, 115)])
    for k in range(3):
        shovel(M, 8 + k * 5, 112, 3)
    M.models += [{'name': '水桶', 'source': 'summit-rocher-01m-barrel', 'at': [24, 110, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-棚', (3, 104, 16))
    M.anchor('door', 59, 6, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'clay-pit', 'title': '黏土坑（共用：挖出來的土圍成一圈、內壁一層一層的黏土、坑底泡水的黏土與一灘水；缺口的踏板、和泥的圓槽、手推車、黏土堆、茅草小棚）',
            'use': 'clay-pit', 'lot': (12, 12), 'M': M, 'style': 'common', 'layers': {'body': '土圍、坑與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 磚窯 12 × 12 m ───────────────────────────────
def brick_hack(M, x0, x1, y0, rows, color=CLAY_L, layer='body'):
    """晾坯的磚堆（hack）：生磚坯側立、一皮一皮交錯（中間留縫通風），沿 x；rows 皮。"""
    for z in range(rows * 2):
        for x in range(x0, x1):
            if z < 2 or x in (x0, x1 - 1) or (x + (z // 2)) % 3 != 2:      # 最底兩層、兩端整條（不然兩端那一截跟下面錯開、算成浮空）
                M.box(layer, x, y0, z, x + 1, y0 + 4, z + 1, color)


def brickworks():
    """磚窯（brickworks）：後半一座方的磚砌升焰窯（4.4 × 4.4 m、高 3 m、上面開口、看得到裡面碼好的磚）—— 正面兩個拱的火口（紅的火）、柴堆；
    前半一座長的茅草晾坯棚（八根柱）、棚下三排晾著的生磚坯；左前做坯的木桌（磚模、一團黏土）、黏土堆；右前燒好的紅磚一垛一垛。
    - 照什麼：殖民地的磚多是就地燒（clamp 或小窯）〔通論〕；升焰窯：火在下面拱道裡燒、熱往上穿過碼好的坯（設計）。
    - 遊戲：1 級（土窯、磚的起點；PRODUCTION §14.2）⇒ 窯身雖然是磚，蓋它只吃木材。"""
    X, Y, Z = 120, 120, 70
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 118, 118, salt=8802)
    # 窯：4.4 × 4.4 m、高 3 m、牆厚 0.6 m；正面兩個拱的火口；頂上開口、裡面碼好的磚
    K = (38, 66, 82, 110)
    for x in range(K[0], K[2]):
        for y in range(K[1], K[3]):
            for z in range(30):
                wall = x < K[0] + 6 or x >= K[2] - 6 or y < K[1] + 6 or y >= K[3] - 6
                if wall:
                    M.put('body', x, y, z, MORTAR if z % 3 == 2 and z < 27 else (BRICK_D if (x + y + z // 3) % 4 == 0 or z >= 27 else BRICK_R))   # 頂上三層壓頂（深紅）
                elif z < 27:
                    M.put('body', x, y, z, CLAY_L if (x + y + z) % 4 else BRICK_R)  # 碼好的坯（燒到一半：淺的、紅的交錯）
    for xa in (44, 62):                                                          # 火口：寬 1 m、高 0.9 m 的拱，往裡 1 m 紅的火
        for x in range(xa, xa + 10):
            for z in range(10):
                if z < 7 or math.hypot(x + 0.5 - xa - 5, z - 7) < 5:
                    for y in range(K[1], K[1] + 10):
                        M.put('body', x, y, z, EMBER if y >= K[1] + 7 else DARK, True)
    M.anchor('smoke', 60, 88, 30)
    cord(M, 86, 116, 70, 100, 10)                                                # 窯邊柴堆
    # 晾坯棚：前半，屋脊沿 x、茅草，八根柱
    S = (6, 20, 114, 56)
    top = thatch_roof(M, [{'x0': S[0], 'y0': S[1], 'x1': S[2], 'y1': S[3], 'ze': 24, 'p': 0.55, 'over': (2, 2, 2, 2), 'gable': 'x'}], salt=8831)
    roof_posts(M, top, [(x, y) for x in (S[0], 40, 76, S[2] - 2) for y in (S[1], S[3] - 2)])
    for y0 in (26, 36, 46):
        brick_hack(M, 12, 108, y0, 5)
    # 左前：做坯桌（磚模、一團黏土）、黏土堆；右前：燒好的紅磚垛
    trestle_table(M, 8, 30, 4, 14, 8)
    M.box('body', 14, 7, 9, 22, 11, 10, FRAME)                                   # 磚模
    M.box('body', 15, 8, 9, 21, 10, 10, CLAY, force=True)
    M.box('body', 24, 6, 9, 29, 12, 12, CLAY)                                    # 一團黏土
    heap(M, 12, 72, 10, 9, 10, lambda x, y, z: CLAY if z < 6 else CLAY_L)
    for (x0, y0) in ((88, 4), (100, 4), (88, 12)):
        for z in range(9):
            for x in range(x0, x0 + 10):
                for y in range(y0, y0 + 6):
                    M.put('body', x, y, z, MORTAR if (x + y + z) % 7 == 0 else (BRICK_R if (x // 2 + z) % 2 else BRICK_D))
    wheelbarrow(M, 64, 4, BRICK_R)
    lantern(M, '燈籠-棚', (S[0], S[1] - 1, 16))
    M.anchor('door', 52, 4, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'brickworks', 'title': '磚窯（共用：後半一座方的磚砌升焰窯、正面兩個拱的火口、柴堆；前半茅草晾坯棚與三排生磚坯；做坯桌、黏土堆、燒好的紅磚垛）',
            'use': 'brickworks', 'lot': (12, 12), 'M': M, 'style': 'common', 'layers': {'body': '窯、晾坯棚與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 礦坑 12 × 16 m ───────────────────────────────
def mine():
    """礦坑（mine）：後半一座岩丘、正面木框的坑道口（兩根立柱、一根橫楣、裡面黑的），坑道口鋪出兩條木軌、一台礦車；
    岩丘頂上一座絞車（兩座木架、橫軸、搖把、垂下坑井的繩與吊桶）；前院礦石堆（紅褐）、廢石堆（灰）、揀礦的木桌；右前一座工具棚。
    - 照什麼：平硐（adit）＋豎井的絞車（windlass）是歐洲 16、17 世紀小礦的通法（設計；Agricola《De re metallica》1556 有這一類的圖〔記得、沒有翻〕）。"""
    X, Y, Z = 120, 160, 100
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 118, 158, salt=8803)
    S = crag_solid(60, 118, 54, 40, 30, 20, 56, X, Y, salt=8841)
    put_mask(M, S, rock_color)
    # 坑道口：岩丘正面（y 約 78）挖 2 m 寬、2.2 m 高、往裡 4 m；木框（立柱、橫楣），裡面黑
    yf = min(y for x in range(52, 70) for y in range(Y) if S[x, y, 4]) if True else 78
    M.clear(50, yf - 2, 1, 70, yf + 40, 22)
    for x in range(50, 70):
        for z in range(1, 22):
            M.put('body', x, yf + 40, z, DARK, True)                             # 坑道盡頭（暗）
    for y in range(yf - 2, yf + 40):
        for x in range(50, 70):
            M.put('body', x, y, 0, DARK if y > yf + 6 else EARTH, True)
    for xa in (50, 68):                                                          # 立柱、每 1 m 一副框
        for y in (yf - 2, yf + 8, yf + 18):
            M.box('body', xa, y, 1, xa + 2, y + 2, 22, FRAME, force=True)
    for y in (yf - 2, yf + 8, yf + 18):
        M.box('body', 50, y, 22, 70, y + 2, 25, FRAME, force=True)               # 橫楣
    # 木軌：枕木每 0.6 m、兩條鐵皮包的木軌，從坑道裡鋪到前院
    for y in range(20, yf + 30, 6):
        M.box('body', 54, y, 1, 66, y + 2, 2, FRAME, force=True)
    for x in (55, 64):
        M.box('body', x, 20, 2, x + 1, yf + 30, 3, IRON, force=True)
    # 礦車：木斗 1 × 1.4 m、四個輪、裝滿礦石
    M.box('body', 54, 40, 3, 66, 54, 4, FRAME)
    for (xa, xb, ya, yb) in ((54, 55, 40, 54), (65, 66, 40, 54), (54, 66, 40, 41), (54, 66, 53, 54)):
        M.box('body', xa, ya, 4, xb, yb, 10, BOARD)
    M.box('body', 55, 41, 4, 65, 53, 11, ORE)
    for (x, y) in ((53, 43), (66, 43), (53, 50), (66, 50)):
        M.box('body', x, y, 2, x + 1, y + 2, 5, IRON, force=True)
    # 岩丘頂：絞車（兩座 A 字木架、橫軸、搖把、繩與吊桶）
    zt = max(z for z in range(S.shape[2]) if S[60, 118, z]) + 1
    for xa in (50, 70):
        rod(M, (xa + 0.5, 112.5, zt), (xa + 0.5, 118.5, zt + 12), 1, FRAME, FRAME)
        rod(M, (xa + 0.5, 124.5, zt), (xa + 0.5, 118.5, zt + 12), 1, FRAME, FRAME)
    rod(M, (48.5, 118.5, zt + 12.5), (73.5, 118.5, zt + 12.5), 1.6, FRAME, FRAME)
    M.box('body', 73, 118, zt + 6, 75, 120, zt + 13, FRAME, force=True)         # 搖把
    M.clear(56, 114, zt - 8, 64, 122, zt + 1)                                    # 豎井口
    for x in range(56, 64):
        for y in range(114, 122):
            M.put('body', x, y, zt - 9, DARK, True)
    rope_line(M, (60, 118, zt + 11), (60, 118, zt - 2))
    M.box('body', 58, 116, zt - 5, 62, 120, zt - 2, BOARD, force=True)          # 吊桶
    # 前院：礦石堆、廢石堆、揀礦桌、工具棚
    heap(M, 22, 30, 14, 12, 12, lambda x, y, z: ORE if h01('ore', x, y, z) < 0.8 else RUBBLE_D)
    heap(M, 100, 92, 16, 22, 16, lambda x, y, z: SPOIL if h01('sp', x // 2, y // 2, z) < 0.7 else ROCK_D)
    trestle_table(M, 8, 34, 52, 64, 8)
    for k in range(6):
        M.box('body', 10 + k * 4, 56, 9, 12 + k * 4, 59, 10 + k % 2, ORE)
    tool_shed(M, 86, 4, 116, 30, 30, salt=8842)
    shovel(M, 40, 70, 3)
    M.models += [{'name': '水桶', 'source': 'summit-rocher-01m-barrel', 'at': [36, 60, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-坑口', (49, yf - 2, 18))
    M.anchor('door', 60, 4, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'mine', 'title': '礦坑（共用：岩丘正面木框的坑道口、木軌與礦車、丘頂的絞車與豎井；礦石堆、廢石堆、揀礦桌、工具棚）',
            'use': 'mine', 'lot': (12, 16), 'M': M, 'style': 'common', 'layers': {'body': '岩丘、坑道與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 煉鐵場 12 × 16 m ───────────────────────────────
def ironworks():
    """煉鐵場（ironworks）：兩段在同一座（Tim：「冶煉可以分兩階段 … 可以在同一個建築」）——
    ① 後半一座方的石砌高爐（底 4.4 m、往上收到 2.8 m、高 7.2 m，頂上紅的爐口）；後面靠土坡搭一座木的上料橋通到爐口（筐裡的礦石、木炭）；
       爐的左邊一間風箱房（兩具大皮風箱、上面一根搖桿）；爐前開敞的出鐵棚，地上的砂床一道主溝分出一排一排的生鐵（pig）；
    ② 右前一座精煉爐（毛石爐台、紅的火、石罩、大煙囪）與一具落錘（粗木架、長柄的錘、鐵砧）—— 生鐵在這裡鍛成熟鐵；
    院子：礦石堆、木炭堆、爐渣堆。
    - 照什麼：17 世紀的高爐＋精煉爐（finery forge）＋落錘是同一套煉鐵場（北美 1646 年的 Saugus 鐵工場就是這一套〔通論、沒上網查〕）；
      史實的風箱、落錘是水車帶的 ⇒ 城裡沒有水路，改成人力搖桿（設計）。"""
    X, Y, Z = 120, 160, 110
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 118, 158, salt=8804)
    # ① 高爐：中心 (60, 104)；底半寬 22、頂半寬 14、高 72
    cx, cy, H = 60, 104, 72
    for z in range(H):
        hw = int(round(22 - 8 * z / H))
        stone_block(M, cx - hw, cy - hw, z, cx + hw, cy + hw, z + 1, salt=8851)
    for x in range(cx - 6, cx + 6):                                              # 爐口（頂上紅的、四周一圈黑）
        for y in range(cy - 6, cy + 6):
            M.put('body', x, y, H - 1, EMBER if abs(x + 0.5 - cx) < 4 and abs(y + 0.5 - cy) < 4 else CHAR, True)
    M.anchor('smoke', cx, cy, H)
    for x in range(cx - 6, cx + 6):                                              # 出鐵拱（正面）：寬 1.2 m、高 1.6 m，裡面暗、底下紅的出鐵口
        for z in range(1, 16):
            if z < 11 or math.hypot(x + 0.5 - cx, z - 11) < 6:
                for y in range(cy - 24, cy - 16):
                    M.put('body', x, y, z, DARK, True)
    M.box('body', cx - 2, cy - 17, 1, cx + 2, cy - 15, 3, EMBER, force=True)
    # 上料橋：後面一道土坡（到爐口高）、橋面木板、欄杆、兩個筐
    for y in range(128, 158):
        h = int(H * (y - 128) / 30) if y < 158 else H
        h = min(H - 2, int(H * 0.55 + (y - 128) * 1.1))
        for x in range(48, 72):
            for z in range(h):
                M.put('body', x, y, z, SOD if z == h - 1 else (RUBBLE if x in (48, 71) or y == 157 else EARTH))   # 兩側砌石擋土、頂上一層草
    for y in range(118, 128):
        M.box('body', 52, y, H - 3, 68, y + 1, H - 2, BOARD, force=True)
    for y in (118, 122, 126):
        M.box('body', 52, y, 0, 54, y + 2, H - 3, FRAME)
        M.box('body', 66, y, 0, 68, y + 2, H - 3, FRAME)
    for (x, c) in ((55, ORE), (62, CHAR)):
        M.box('body', x, 123, H - 2, x + 4, 127, H + 2, BOARD)
        M.box('body', x + 1, 124, H + 1, x + 3, 126, H + 2, c, force=True)
    # 風箱房（左）：單坡棚、兩具大皮風箱、搖桿
    top = shed_roof(M, 4, 82, 36, 124, 46, 0.35, low='left' if False else 'front', color_fn=lambda x, y, f, r, e: shingle_color(x, y, f, r, e, 8852))
    roof_posts(M, top, [(4, 82), (34, 82), (4, 122), (34, 122)])
    for y0 in (90, 108):
        for x in range(8, 34):
            h = 3 + (34 - x) // 4
            M.box('body', x, y0, 10, x + 1, y0 + 12, 11, FRAME)
            M.box('body', x, y0, 11, x + 1, y0 + 12, 11 + h, LEATHER)
            M.box('body', x, y0, 11 + h, x + 1, y0 + 12, 12 + h, FRAME)
        M.box('body', 8, y0, 0, 10, y0 + 2, 10, FRAME)
        M.box('body', 34, y0 + 4, 12, cx - 21, y0 + 8, 15, IRON, force=True)     # 風管接到爐側
    rod(M, (20.5, 92.5, 34), (20.5, 116.5, 34), 1.2, FRAME, FRAME)             # 搖桿的橫軸
    M.box('body', 19, 103, 0, 22, 106, 35, FRAME)                                # 撐橫軸的柱（兩具風箱中間）
    # 出鐵棚：爐前開敞、木瓦兩坡頂（屋脊沿 y）；砂床：一道主溝、兩邊一排一排的生鐵
    T = (34, 30, 86, 80)
    top = shingle_roof(M, [{'x0': T[0], 'y0': T[1], 'x1': T[2], 'y1': T[3], 'ze': 34, 'p': 0.55, 'over': (2, 2, 2, 2), 'gable': 'y'}], salt=8853)
    roof_posts(M, top, [(x, y) for x in (T[0], T[2] - 2) for y in (T[1], 54, T[3] - 2)])
    for x in range(T[0] + 4, T[2] - 4):
        for y in range(T[1] + 4, T[3]):
            M.put('body', x, y, 1, SAND)
    M.box('body', cx - 1, T[1] + 6, 1, cx + 1, cy - 16, 2, IRON, force=True)     # 主溝（冷了的鐵）
    for y in range(T[1] + 8, T[3] - 2, 6):
        for xs in ((40, 58), (62, 80)):
            M.box('body', xs[0], y, 1, xs[1], y + 2, 2, IRON, force=True)        # 一根一根的生鐵
    # ② 精煉爐與落錘（右前）
    stone_block(M, 90, 30, 0, 114, 50, 9, salt=8854)
    M.box('body', 94, 34, 9, 108, 44, 10, CHAR, force=True)
    M.box('body', 98, 36, 9, 104, 42, 10, EMBER, force=True)
    stone_block(M, 90, 46, 9, 114, 50, 22, salt=8855)                           # 爐後的擋火牆
    stone_block(M, 88, 30, 22, 116, 50, 25, salt=8856)                          # 石罩
    stone_block(M, 96, 40, 25, 108, 50, 58, salt=8857)                          # 煙囪
    M.box('body', 98, 42, 57, 106, 48, 58, CHAR, force=True)
    M.anchor('smoke', 102, 45, 58) if False else None
    for (x, y) in ((88, 30), (114, 30)):
        M.box('body', x, y, 9, x + 2, y + 2, 22, IRON)
    for (x, y) in ((90, 4), (110, 4), (90, 20), (110, 20)):                    # 落錘：四柱的粗木架、橫軸、長柄的錘、鐵砧
        M.box('body', x, y, 0, x + 3, y + 3, 26, FRAME)
    for y in (4, 20):
        M.box('body', 90, y, 24, 113, y + 3, 27, FRAME)
    rod(M, (91.5, 12.5, 22.5), (112.5, 12.5, 22.5), 1.4, FRAME, FRAME)        # 橫軸
    rod(M, (100.5, 12.5, 22.5), (100.5, 30.5, 10.5), 1.2, FRAME, FRAME)       # 錘柄
    M.box('body', 98, 28, 6, 104, 34, 12, IRON, force=True)                      # 錘頭
    for x in range(97, 106):
        for y in range(27, 36):
            if math.hypot(x + 0.5 - 101, y + 0.5 - 31) <= 4:
                M.box('body', x, y, 0, x + 1, y + 1, 4, LOG)                     # 樹墩
    M.box('body', 98, 29, 4, 104, 33, 6, IRON, force=True)                       # 鐵砧
    # 院子：礦石堆、木炭堆（棚邊）、爐渣堆
    heap(M, 16, 30, 13, 12, 12, lambda x, y, z: ORE if h01('ore2', x, y, z) < 0.85 else RUBBLE_D)
    heap(M, 16, 62, 13, 12, 14, lambda x, y, z: CHAR if h01('ch2', x, y, z) < 0.9 else DARK)
    heap(M, 100, 140, 16, 14, 10, lambda x, y, z: SLAG if h01('sl', x // 2, y // 2, z) < 0.7 else DARK)
    wheelbarrow(M, 78, 10, ORE)
    lantern(M, '燈籠-棚', (T[0], T[1] - 1, 24))
    M.anchor('door', 60, 4, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'ironworks', 'title': '煉鐵場（共用：石砌高爐、上料橋、風箱房、出鐵棚與砂床上的生鐵；精煉爐與落錘；礦石、木炭、爐渣堆）',
            'use': 'ironworks', 'lot': (12, 16), 'M': M, 'style': 'common', 'layers': {'body': '高爐、精煉爐與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 營造廠 12 × 16 m ───────────────────────────────
def builder():
    """營造廠（builder）：建築工的場子 —— 左前一間木板的工頭屋（門、窗、木瓦兩坡頂），右前木料與磚垛、灰漿槽與石灰池；
    後半一座蓋到一半的木構架（兩層的柱、梁、一半的椽、一面釘了一半的板牆）、靠著的鷹架與梯子；中間一座鋸木架、一台起重的人字架（滑車、吊著一捆木料）。
    - 照什麼：17 世紀的木匠、泥水匠就在工地旁邊搭棚、堆料（設計；城裡的「營造廠」是遊戲的抽象：PRODUCTION §14.2 雇建築工、照菜單吃建材）。"""
    X, Y, Z = 120, 160, 100
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 118, 158, salt=8805)
    # 工頭屋：5.6 × 4.4 m 的木板屋
    R = (6, 8, 62, 52)
    board_walls(M, R, 0, 26)
    end_gable(M, R[0], R[0] + 2, R[1], R[3], 26, 0.6, z0=26)
    end_gable(M, R[2] - 2, R[2], R[1], R[3], 26, 0.6, z0=26)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 26, 'p': 0.6, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=8861)
    M.box('body', R[0] + 2, R[1] + 2, 0, R[2] - 2, R[3] - 2, 1, FLOOR)
    put_part(M, 'door-plank', '前-門', 'front', R, 20, 0, 2)
    put_part(M, 'window-board', '前-窗', 'front', R, 44, 9, 2)
    put_part(M, 'window-board', '右-窗', 'right', R, 30, 9, 2)
    for L in M.links:                                                            # 門框底那一層壓到院子的地 ⇒ 地讓給門
        for k in L['cells']:
            M.cells.pop(k, None)
    trestle_table(M, 30, 54, 36, 46, 8)                                          # 屋裡畫圖的桌
    M.box('body', 34, 38, 9, 46, 44, 10, CREAM, force=True)                      # 攤開的圖
    # 右前：木板堆（墊隔條）、磚垛、灰漿槽、石灰池
    for k in range(8):
        if k % 2 == 0:
            M.box('body', 72, 8, k, 114, 22, k + 1, FLOOR)
        else:
            for x in (73, 92, 111):
                M.box('body', x, 8, k, x + 2, 22, k + 1, FRAME)
    for (x0, y0) in ((72, 30), (86, 30), (100, 30)):
        for z in range(8):
            for x in range(x0, x0 + 10):
                for y in range(y0, y0 + 8):
                    M.put('body', x, y, z, MORTAR if (x + y + z) % 7 == 0 else (BRICK_R if (x // 2 + z) % 2 else BRICK_D))
    M.box('body', 72, 44, 0, 94, 54, 4, BOARD)                                   # 灰漿槽
    M.box('body', 73, 45, 1, 93, 53, 4, MORTAR, force=True)
    shovel(M, 96, 48, 4)
    for x in range(98, 116):                                                     # 石灰池（矮木框、白的石灰膏）
        for y in range(42, 56):
            edge = x in (98, 115) or y in (42, 55)
            M.box('body', x, y, 0, x + 1, y + 1, 3, BOARD if edge else LIMEW)
    # 中間：鋸木架、人字起重架
    saw_trestle(M, 10, 64)
    rod(M, (78.5, 66.5, 1), (88.5, 76.5, 46), 1.4, FRAME, FRAME)
    rod(M, (98.5, 66.5, 1), (88.5, 76.5, 46), 1.4, FRAME, FRAME)
    rope_line(M, (88, 77, 45), (88, 120, 1))                                      # 後拉索
    tackle_block(M, 88, 77, 38, 5)
    rope_line(M, (88, 77, 38), (88, 77, 20))
    rod(M, (80.5, 77.5, 18.5), (96.5, 77.5, 18.5), 2.2)                        # 吊著的一捆木料
    rope_line(M, (88, 77, 21), (88, 77, 20))
    # 後半：蓋到一半的木構架（6 × 3 m、兩層：柱、梁、一半的椽、一面板牆釘了一半）
    F = (24, 96, 96, 148)
    posts = [(x, y) for x in (F[0], 48, 72, F[2] - 2) for y in (F[1], F[3] - 2)]
    for (x, y) in posts:
        M.box('body', x, y, 0, x + 2, y + 2, 52, FRAME)
    for z in (24, 50):
        for y in (F[1], F[3] - 2):
            M.box('body', F[0], y, z, F[2], y + 2, z + 2, FRAME)
        for x in (F[0], 48, 72, F[2] - 2):
            M.box('body', x, F[1], z, x + 2, F[3], z + 2, FRAME)
    for k, x in enumerate(range(F[0], 60, 8)):                                   # 一半的椽（左半）
        for t in range(26):
            zz = 52 + t
            M.box('body', x, F[1] + t, zz, x + 2, F[1] + t + 1, zz + 2, FRAME, force=True)
            M.box('body', x, F[3] - 1 - t, zz, x + 2, F[3] - t, zz + 2, FRAME, force=True)
    for x in range(F[0] + 2, 72):                                                # 背面的板牆釘了一半（下層、左邊）
        for z in range(1, 24):
            if x < 60 or z < 12:
                M.put('body', x, F[3] - 2, z, BOARD if (z // 3) % 2 else BOARD_D)
    M.box('body', F[0] + 2, F[1] + 2, 24, F[2] - 2, F[3] - 2, 25, FLOOR)        # 二樓的樓板（鋪好了）
    # 鷹架（右邊外側）與梯子
    for (x, y) in ((100, 98), (100, 146), (110, 98), (110, 146)):
        M.box('body', x, y, 0, x + 2, y + 2, 60, LOG)
    for z in (20, 40):
        M.box('body', 100, 98, z, 112, 148, z + 1, BOARD)
    for x in (104, 108):                                                         # 梯子：兩根梯柱（六連通的斜線）、每 0.3 m 一級
        rope_line(M, (x, 92, 1), (x, 86, 40), color=FRAME)
    for k in range(1, 13):
        z = 1 + k * 3
        y = 92 - round(6 * (z - 1) / 39)
        M.box('body', 104, y, z, 109, y + 1, z + 1, FRAME, force=True)
    wheelbarrow(M, 60, 60, BRICK_R)
    lantern(M, '燈籠-屋', (R[0] + 10, R[1] - 1, 18))
    M.anchor('door', 20, 4, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'builder', 'title': '營造廠（共用：木板的工頭屋；木板堆、磚垛、灰漿槽、石灰池；鋸木架、人字起重架；後半蓋到一半的兩層木構架、鷹架與梯子）',
            'use': 'builder', 'lot': (12, 16), 'M': M, 'style': 'common', 'layers': {'body': '屋、料場、構架與擺設', 'roof': '屋頂'}}


ALL = [lumber_camp, clay_pit, brickworks, mine, ironworks, builder]
