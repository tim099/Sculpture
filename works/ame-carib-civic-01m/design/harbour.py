# 共用的港口配套（風格 common；TASK-0772，TOWN_BUILD §1.1.7 Tim：「起重機 造船廠 其他港口裝飾物等 可以共用」）——
# 不分地區：任何風格的城缺了都照退路拿到（TOWN_BUILD §2.1）。座標同 civic.py（x 臨路寬、y 進深 y 0 臨路、z 往上；0.1 m／格）。
# 生成器把它們放在「碼頭臨陸那一側、離廣場遠的先 ⇒ 港口街靠岸那一段」（world/town.js ⑦b）：正面（y 0）朝路、背面多半朝水。
from civic import *

ROPE = THATCH_A                  # 麻繩（偏暖的稻草色；同茅草那一色）
EMBER = 236                      # 柴火的火口（偏紅橙；⛔ 不用 245 ⇒ 那是燈籠玻璃、遊戲夜裡會當燈點亮）
TAR = DARK                       # 瀝青、焦油


def capstan(M, cx, cy, bars=True, layer='body'):
    """絞盤（cabestan）：方木座 1.2 × 1.2 m、鼓 直徑 0.6 m 高 1.0 m、頂上的帽、四根推桿（往外 1.4 m，0.9 m 高）、一圈繩。"""
    M.box(layer, cx - 6, cy - 6, 0, cx + 6, cy + 6, 2, FRAME)
    for x in range(cx - 4, cx + 4):
        for y in range(cy - 4, cy + 4):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 3.2:
                M.box(layer, x, y, 2, x + 1, y + 1, 10, FLOOR if d > 2.2 else FRAME)
            if d <= 4.0:
                M.box(layer, x, y, 10, x + 1, y + 1, 12, FRAME)
    if bars:
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for k in range(1, 14):                                       # 從鼓裡面插出來（從 4 起 ⇒ 跟鼓沒相連、算成浮空）
                M.put(layer, cx + dx * k - (1 if dx < 0 else 0), cy + dy * k - (1 if dy < 0 else 0), 9, FRAME)
    for x in range(cx - 4, cx + 4):                                    # 鼓上纏的繩（一圈，z 4..6）
        for y in range(cy - 4, cy + 4):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if 2.8 < d <= 3.8:
                M.box(layer, x, y, 4, x + 1, y + 1, 7, ROPE, force=True)


def rope_coil(M, cx, cy, r=5, h=2, layer='body'):
    """地上一盤繩（圓的一圈一圈）。"""
    for x in range(cx - r, cx + r + 1):
        for y in range(cy - r, cy + r + 1):
            d = math.hypot(x - cx, y - cy)
            if 1.5 <= d <= r:
                M.box(layer, x, y, 0, x + 1, y + 1, h, ROPE)


def log_pile(M, x0, x1, y0, rows=3, d=4, layer='body'):
    """原木堆：沿 x 的原木（截面 d × d 格、端面淺色），一層比一層少一根、往裡縮半根。"""
    for r in range(rows):
        n = rows - r + 1
        for i in range(n):
            y = y0 + i * d + r * d // 2
            z = r * d
            for x in range(x0, x1):
                end = x in (x0, x1 - 1)
                M.box(layer, x, y, z, x + 1, y + d, z + d, LOG_TIP if end else (LOG_D if (i + r) % 2 else LOG))


def tar_kettle(M, cx, cy, layer='body'):
    """煮瀝青的鐵鍋：毛石圍的灶（前面開火口、裡面紅的炭）＋鍋（直徑 0.8 m）＋鍋裡的黑瀝青。"""
    M.box(layer, cx - 6, cy - 6, 0, cx + 6, cy + 6, 5, RUBBLE)
    M.box(layer, cx - 3, cy - 6, 0, cx + 3, cy, 4, EMBER, force=True)
    for x in range(cx - 5, cx + 5):
        for y in range(cy - 5, cy + 5):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 4.2:
                M.box(layer, x, y, 5, x + 1, y + 1, 10, IRON if d > 3.2 else TAR, force=True)
    for (dx, dy) in ((-6, -1), (5, -1)):                               # 兩根小叉柱＋橫木（翻鍋用）
        M.box(layer, cx + dx, cy + dy, 5, cx + dx + 1, cy + dy + 2, 16, FRAME)
    M.box(layer, cx - 6, cy - 1, 16, cx + 6, cy + 1, 17, FRAME)


def tool_shed(M, x0, y0, x1, y1, z_hi=30, salt=0):
    """工具棚：單坡木瓦頂、四根柱、背面一道木板牆；棚下一張工作檯。回傳屋面高度場。"""
    board_walls(M, (x0, y1 - 2, x1, y1), 0, z_hi - 6, 2, posts=False)
    top = lean_roof_posts(M, x0 - 2, y0 - 3, x1 + 2, y1 + 1, z_hi, 0.3, 'front', shingle_color,
                          [(x0, y0), (x1 - 2, y0), (x0, y1 - 4), (x1 - 2, y1 - 4)], salt=salt)
    bx0, bx1 = x0 + 8, x0 + 8 + 24                                     # 工作檯：2.4 × 0.8 m、高 0.85 m
    M.box('body', bx0, y1 - 12, 8, bx1, y1 - 4, 9, FLOOR)
    for x in (bx0, bx1 - 2):
        for y in (y1 - 12, y1 - 6):
            M.box('body', x, y, 0, x + 2, y + 2, 8, FRAME)
    return top


# ─────────────────────────────── 修船灘 24 × 12 m ───────────────────────────────
def careening_beach():
    """修船灘（carénage sur la plage）：把船拖上灘、用滑車把船往一邊拉倒（abattre en carène），刮掉船底的藤壺與船蛆、重新塗瀝青。
    岸上要的：拉船的絞盤兩座、打進地裡的粗木樁（繫滑車）、煮瀝青的鍋、木料堆、放工具與帆的棚子。
    —— 這一件是空地上的設施（船本身不在模型裡）；每一樣東西的大小、數量是設計（史料見 references/research_civic.md 修船灘一節）。"""
    X, Y, Z = 240, 120, 60
    M = Model((X, Y, Z))
    tool_shed(M, 10, 14, 74, 54, 30, salt=71)
    M.models += [{'name': '酒桶-棚1', 'source': 'summit-rocher-01m-barrel', 'at': [14, 20, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-棚1', 'source': 'summit-rocher-01m-crate', 'at': [44, 20, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-棚2', 'source': 'summit-rocher-01m-crate', 'at': [56, 20, 0], 'pivot': [6, 6, 0], 'meta': {}}]
    tar_kettle(M, 100, 32)
    M.models.append({'name': '瀝青桶', 'source': 'summit-rocher-01m-barrel', 'at': [116, 24, 0], 'pivot': [6, 6, 0], 'meta': {}})
    log_pile(M, 132, 204, 12, 3, 4)                                    # 7.2 m 的原木（補船殼用的木料）
    for (y, z) in ((44, 0), (48, 0)):                                  # 地上兩根備用的圓材（桅、桁），沿 x 6 m
        M.box('body', 140, y, z, 200, y + 3, z + 3, LOG_D)
    capstan(M, 60, 84)
    capstan(M, 176, 84)
    rope_coil(M, 96, 84)
    rope_coil(M, 140, 86)
    for x in (24, 118, 214):                                           # 拉倒船用的粗木樁（0.4 m 見方、1.5 m 高、頂上一道鐵箍）
        M.box('body', x, 106, 0, x + 4, 110, 15, FRAME)
        M.box('body', x, 106, 12, x + 4, 110, 13, IRON, force=True)
    M.anchor('door', 120, 0, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'careening-beach', 'title': '修船灘（共用：拉船的絞盤兩座、繫滑車的粗木樁三根、煮瀝青的鍋、木料與圓材堆、工具棚與工作檯）',
            'use': 'careening-beach', 'lot': (24, 12), 'M': M, 'style': 'common',
            'layers': {'body': '設施', 'roof': '棚頂'}}


# ─────────────────────────────── 修船碼頭 30 × 20 m ───────────────────────────────
def careening_wharf():
    """修船碼頭（careening wharf）：English Harbour 第一座船廠（1725 年起）只有一座絞盤屋、一座石造倉庫、三座工具棚（TOWN_BUILD §1.1.7〔開〕）⇒ 照這一套：
    背面（多半朝水）一道木碼頭面＋繫纜樁、碼頭上兩座拉倒船的絞盤，靠中間的那一座有絞盤屋（四根石墩撐的四坡頂、四面開敞）；
    左邊一座毛石倉庫（貨門、兩坡木瓦頂）、右邊一排三座工具棚。每一棟的大小、絞盤數是設計。"""
    X, Y, Z = 300, 200, 90
    M = Model((X, Y, Z))
    # 碼頭面：背面 2.8 m 寬的木板面（底下毛石擋土）＋每 5 m 一根繫纜樁
    WY0 = 172
    rubble_walls(M, (0, WY0, X, 200), 0, 4, 28, salt=81)
    for x in range(0, X):
        for y in range(WY0, 200):
            M.put('body', x, y, 4, FLOOR if x % 6 else FRAME, force=True)
    for x in range(20, X - 10, 50):
        M.box('body', x, 192, 5, x + 4, 196, 13, FRAME)
        M.box('body', x - 1, 191, 11, x + 5, 197, 12, FRAME)
    # 絞盤屋（中）：石墩 4 根、四坡木瓦頂、裡面一座絞盤
    hx0, hy0, hx1, hy1 = 120, 112, 180, 164
    for (px, py) in ((hx0, hy0), (hx1 - 6, hy0), (hx0, hy1 - 6), (hx1 - 6, hy1 - 6)):
        rubble_walls(M, (px, py, px + 6, py + 6), 0, 30, 3, salt=82 + px)
    shingle_roof(M, [{'x0': hx0, 'y0': hy0, 'x1': hx1, 'y1': hy1, 'ze': 30, 'p': 0.7, 'over': (4, 4, 4, 4)}], salt=83)
    capstan(M, 150, 138)
    capstan(M, 240, 150)                                               # 碼頭上另一座（露天）
    rope_coil(M, 200, 150)
    # 石造倉庫（左）：10 × 6.8 m、毛石牆 0.4 m、兩坡木瓦頂、正面貨門＋兩扇窗
    R = (10, 30, 110, 98)
    rubble_walls(M, R, 0, 36, 4, salt=84)
    put_part(M, 'cartdoor', '倉庫-貨門', 'front', R, 60, 0, 4)
    for i, cx in enumerate((24, 96)):
        put_part(M, 'window-board', '倉庫-窗%d' % (i + 1), 'front', R, cx, 14, 4)
    put_part(M, 'door-plank', '倉庫-後門', 'back', R, 60, 0, 4)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 36, 'p': 0.7, 'over': (4, 4, 4, 4), 'gable': 'x'}], salt=85)
    for (x0, x1) in ((R[0], R[0] + 4), (R[2] - 4, R[2])):              # 兩端的山牆（毛石，沿 y 收成三角）
        for y in range(R[1], R[3]):
            d = min(y + 0.5 - R[1], R[3] - y - 0.5)
            for z in range(36, 36 + int(0.7 * d)):
                for x in range(x0, x1):
                    M.put('body', x, y, z, RUBBLE if z % 5 != 4 else MORTAR, force=True)
    # 工具棚三座（右）：4 × 3.6 m 單坡
    for i, x0 in enumerate((196, 236)):
        tool_shed(M, x0, 20, x0 + 36, 56, 28, salt=86 + i)
    tool_shed(M, 196, 66, 232, 102, 28, salt=89)
    log_pile(M, 240, 290, 72, 3, 4)
    M.models += [{'name': '貨箱-門口1', 'source': 'summit-rocher-01m-crate', 'at': [30, 18, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-門口1', 'source': 'summit-rocher-01m-barrel', 'at': [90, 18, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '瀝青桶', 'source': 'summit-rocher-01m-barrel', 'at': [108, 150, 0], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '燈籠-絞盤屋', 'source': 'summit-rocher-01m-lantern', 'at': [146.5, hy0 + 2, 18.5], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}}]
    tar_kettle(M, 110, 128)
    M.anchor('door', 150, 0, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'careening-wharf', 'title': '修船碼頭（共用：木碼頭面與繫纜樁、絞盤屋與兩座絞盤、毛石倉庫、三座工具棚、煮瀝青的鍋、木料堆）',
            'use': 'careening-wharf', 'lot': (30, 20), 'M': M, 'style': 'common',
            'layers': {'body': '碼頭、倉庫與棚', 'roof': '屋頂'}}


ALL = [careening_beach, careening_wharf]
