# 泊位建築（Blocksail TASK-0906；docs/TOWN_BUILD.md §5.19、BUILDING_SPEC §6.21）—— 五級泊位在棧橋（碼頭線）上的擺設：繫纜樁、護舷、梯、燈、貨、起重設施。
# 工具照 trailhead-harbour-01m/design/quay.py（圓材、繩、滑車、繫纜木樁）⇒ 它再 import ame-carib-civic-01m 的 harbour.py（絞盤、繩盤）與 summit-carib-01m 的調色盤、Model、屋頂。
#
# 座標（跟一般建築不同，§6.21）：
#   x ＝ 沿棧橋（泊位長；從棧橋上面向水看，左 → 右）；y ＝ 往水：y 0 ＝ 棧橋邊往裡 EDGE 公尺、y = EDGE × 10 ＝ 棧橋邊、再往外是船停的預留區（泊位寬）；
#   z ＝ 往上，z SINK × 10 ＝ 棧橋面（遊戲把模型往下放 SINK 公尺 ⇒ 護舷、梯子伸得到水裡）。0.1 m／格。
#   遊戲（Blockside 63_towns.js townLotInst）照地塊的 berth.over 把 y 0 對到「棧橋邊往裡 EDGE 公尺」（棧橋寬 6、8、10 m 都一樣貼邊）、不墊石基。
# 棧橋面本身由遊戲畫（規劃的 piers、quays）⇒ 這裡只雕上面的東西；預留區（y > EDGE × 10）除了護舷與起重機的吊臂之外是空的（船停在那裡）。
# 史料（作品 references/README.md）：碼頭上的繫纜樁 —— 17 世紀起用退役的舊砲倒插當繫纜樁（cannon bollard；Portsmouth、English Harbour 都還留著）〔摘〕；
#   踏輪起重機（treadwheel crane）—— 中世紀到 18 世紀港口卸貨的主力（Bruges 的 Kraan、Gdańsk Żuraw、Lüneburg、Trier 的港口吊車）：人在大木輪裡走、
#   輪軸捲繩、經吊臂頂的滑車吊貨〔摘〕；碼頭邊的護舷木樁、上下船的鐵梯〔通常的做法〕。大小、間距是設計。
import os, sys, math

WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRAIL = os.path.join(WORKS, 'trailhead-harbour-01m', 'design')
if TRAIL not in sys.path:
    sys.path.insert(0, TRAIL)
from quay import *                                                     # noqa: E402,F401  rope_line、spar、tackle_block、bollard ＋ harbour（capstan、rope_coil、log_pile）＋ civic／kit

EDGE, SINK = 3.0, 2.0                    # 棧橋邊在 y = EDGE × 10；棧橋面在 z = SINK × 10〔設計：最窄的棧橋 6 m ⇒ 一半 3 m 剛好到中線〕
EY, ZD = int(EDGE * 10), int(SINK * 10)
# 五級（同 world/town.js BERTH_CLS：泊位長 len、預留寬 w）
CLS = {'boat': dict(name='小艇泊位', len=20, w=8), 'small': dict(name='小船泊位', len=48, w=16), 'large': dict(name='大船泊位', len=100, w=24),
       'huge': dict(name='巨艦泊位', len=160, w=32), 'titan': dict(name='超巨艦泊位', len=300, w=52)}
CRATE, BARREL, LANTERN = 'summit-rocher-01m-crate', 'summit-rocher-01m-barrel', 'summit-rocher-01m-lantern'


class Deck:
    """在 Model 上包一層：z 照棧橋面量（z 0 ＝ 棧橋面 ⇒ 實際 z ＋ ZD）；借來的工具（絞盤、繩盤、繫纜樁）都從 z 0 起 ⇒ 先畫在一個暫存的 Model、再整份往上搬。"""

    def __init__(s, X, Y, Z):
        s.M = Model((X, Y, Z))
        s.T = Model((X, Y, Z - ZD))                                     # 棧橋面以上（z 0 ＝ 棧橋面）

    def done(s):
        for (x, y, z), (ln, c) in s.T.cells.items():
            s.M.put(ln, x, y, z + ZD, c, force=True)
        s.M.oob += s.T.oob
        for m in s.T.models:
            m = dict(m); m['at'] = [m['at'][0], m['at'][1], m['at'][2] + ZD]; s.M.models.append(m)
        return s.M


def cannon_bollard(T, cx, cy):
    """舊砲倒插的繫纜樁：鐵、直徑 0.5 m、高 0.9 m（砲口朝上、砲口塞一顆砲彈）、腳下一圈石墊。"""
    for x in range(cx - 4, cx + 4):
        for y in range(cy - 4, cy + 4):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 3.6:
                T.put('body', x, y, 0, STONE_L)
            for z in range(1, 10):
                r = 2.6 if z < 7 else 3.0 if z == 7 else 2.3
                if d <= r:
                    T.put('body', x, y, z, IRON)
            if d <= 1.8:
                T.put('body', x, y, 10, DARK)                          # 砲口塞的砲彈


def wood_bollard(T, cx, cy, h=9):
    """繫纜木樁（借 quay.py：方木 0.4 m、頂上一圈帽）。"""
    bollard(T, cx, cy, h)


def fenders(M, X, step, salt=0):
    """棧橋邊外面的護舷：每 step 格一根直立木樁（0.3 × 0.2 m、從水面下 0.6 m 到棧橋面上 0.2 m）＋ 一道橫的護木（棧橋面下 0.3 m）。
    畫在真的 z（不是棧橋面起算）：棧橋面 z ＝ ZD。"""
    for x in range(step // 2, X - 2, step):
        M.box('body', x, EY, 0, x + 3, EY + 2, ZD + 2, WOOD_D)
    M.box('body', 0, EY, ZD - 5, X, EY + 1, ZD - 2, WOOD_D, force=True)


def ladder(M, x0):
    """上下小艇的鐵梯：兩根鐵條掛在棧橋邊（y EY），從水面下到棧橋面，每 0.3 m 一級踏棍。"""
    for x in (x0, x0 + 6):
        M.box('body', x, EY + 2, 0, x + 1, EY + 3, ZD + 4, IRON, force=True)
        M.box('body', x, EY, ZD + 3, x + 1, EY + 2, ZD + 4, IRON, force=True)   # 頂上彎回棧橋面
    for z in range(2, ZD + 1, 3):
        M.box('body', x0, EY + 2, z, x0 + 7, EY + 3, z + 1, IRON, force=True)


def lamp_post(T, x0, name):
    """燈柱：方木 0.4 m、高 3.6 m，柱頂掛一盞燈籠（外部模型，kind light ⇒ 遊戲夜裡點亮）—— 擺法照起重架的穩索樁（quay.py sheers）。"""
    T.box('body', x0 - 2, 22, 0, x0 + 2, 26, 36, FRAME)
    T.box('body', x0 - 3, 21, 33, x0 + 3, 27, 34, FRAME)
    T.models.append({'name': name, 'source': LANTERN, 'at': [x0 + 0.5, 22, 33], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}})


def cargo(T, x0, y0, kind, name):
    """貨（外部模型：貨箱、酒桶；0.6 m 見方）；疊兩層的貨箱寫 kind='crate2'。"""
    src = BARREL if kind == 'barrel' else CRATE
    T.models.append({'name': name, 'source': src, 'at': [x0, y0, 0], 'pivot': [6, 6, 0], 'meta': {}})
    if kind == 'crate2':
        T.models.append({'name': name + '-上', 'source': CRATE, 'at': [x0, y0, 12], 'pivot': [6, 6, 0], 'meta': {}})


def sacks(T, x0, y0, n=3):
    """一堆貨袋（麻布色的圓角塊，0.6 × 0.4 × 0.3 m，交錯疊兩層）。"""
    for k in range(n):
        x = x0 + (k % 3) * 7 + (3 if k >= 3 else 0)
        z = 0 if k < 3 else 3
        for dx in range(6):
            for dy in range(4):
                for dz in range(3):
                    if (dx in (0, 5) and dz == 2) or (dy in (0, 3) and dz == 2 and dx in (0, 5)):
                        continue
                    T.put('body', x + dx, y0 + dy, z + dz, ROPE)


def treadwheel_crane(T, x0, reach, salt=0):
    """踏輪起重機（treadwheel crane；Bruges、Gdańsk、Lüneburg 的港口吊車那一型）：
    - 棚：四根柱（0.3 m）圍 4.8 × 2.6 m、高 6 m，兩坡木瓦頂（屋脊沿 x）；柱腳一圈木地檻。
    - 踏輪：直徑 4.4 m、寬 1.2 m，輪面在 x–z 平面（人在裡面沿 x 走）；兩圈輪緣、各 8 根輻條、一圈踏板（沿 y 的木條）；輪軸沿 y 穿過兩邊的柱。
    - 吊臂：從棚頂往水那一邊（+y）伸出 reach 格，斜撐從前柱撐到吊臂中段；臂頂一個滑車、吊索垂到吊鉤，鉤上掛一張貨網（兩個桶）。
    - 繩：從輪軸捲上來、沿吊臂到臂頂的滑車。
    大小是設計（史料上的港口踏輪吊車輪徑 4～7 m）。z 0 ＝ 棧橋面。"""
    X0, X1, Y0, Y1 = x0 - 24, x0 + 24, 4, 28
    for (x, y) in ((X0, Y0), (X1 - 3, Y0), (X0, Y1 - 3), (X1 - 3, Y1 - 3)):
        T.box('body', x, y, 0, x + 3, y + 3, 60, FRAME)
    T.box('body', X0, Y0, 0, X1, Y0 + 3, 2, FRAME); T.box('body', X0, Y1 - 3, 0, X1, Y1, 2, FRAME)     # 地檻
    T.box('body', X0, Y0, 0, X0 + 3, Y1, 2, FRAME); T.box('body', X1 - 3, Y0, 0, X1, Y1, 2, FRAME)
    T.box('body', X0, Y0, 58, X1, Y0 + 3, 61, FRAME); T.box('body', X0, Y1 - 3, 58, X1, Y1, 61, FRAME)  # 柱頭梁
    T.box('body', X0, Y0, 58, X0 + 3, Y1, 61, FRAME); T.box('body', X1 - 3, Y0, 58, X1, Y1, 61, FRAME)
    shingle_roof(T, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 61, 'p': 0.7, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=906 + salt)
    # 踏輪
    cz, R = 26, 22
    for x in range(x0 - R - 1, x0 + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            d = math.hypot(x + 0.5 - x0, z + 0.5 - cz)
            if R - 3 <= d < R - 1 and (int(math.degrees(math.atan2(z + 0.5 - cz, x + 0.5 - x0))) // 9) % 2 == 0:
                T.box('body', x, 7, z, x + 1, 22, z + 1, WOOD, force=True)   # 踏板（沿 y 的木條；兩頭伸進輪緣 ⇒ 接在一起）
    for x in range(x0 - R - 1, x0 + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            d = math.hypot(x + 0.5 - x0, z + 0.5 - cz)
            for yr in (7, 20):                                         # 兩圈輪緣（各 2 格寬）
                if R - 2 <= d <= R:
                    T.box('body', x, yr, z, x + 1, yr + 2, z + 1, WOOD_D, force=True)
    for k in range(8):                                                 # 輻條
        a = k * math.pi / 4
        for yr in (7, 20):
            rope_line(T, (x0 + 0.5, yr + 0.5, cz + 0.5), (x0 + 0.5 + math.cos(a) * (R - 2), yr + 0.5, cz + 0.5 + math.sin(a) * (R - 2)), WOOD_D)
            rope_line(T, (x0 + 0.5, yr + 1.5, cz + 0.5), (x0 + 0.5 + math.cos(a) * (R - 2), yr + 1.5, cz + 0.5 + math.sin(a) * (R - 2)), WOOD_D)
    T.box('body', x0 - 1, Y0, cz - 1, x0 + 2, Y1, cz + 2, FRAME, force=True)   # 輪軸（穿過兩邊）
    T.box('body', x0 - 2, Y0, 0, x0 + 3, Y0 + 3, cz, FRAME, force=True)        # 軸架（前後各一根立柱撐輪軸）
    T.box('body', x0 - 2, Y1 - 3, 0, x0 + 3, Y1, cz, FRAME, force=True)
    # 吊臂：從棚頂後梁往 +y 伸出（臂頂在 y Y1 ＋ reach、z 72），斜撐
    ty, tz = Y1 + reach, 78                                            # 吊臂從屋脊（y 15）伸出去 ⇒ 不穿屋面
    for dx in (-1, 0):
        rope_line(T, (x0 + dx + 0.5, 15.5, 71), (x0 + dx + 0.5, ty, tz), FRAME, r=1)
    rope_line(T, (x0 + 0.5, Y1 - 1.5, 30), (x0 + 0.5, Y1 + reach * 0.5, 68), FRAME, r=1)
    tackle_block(T, x0, ty - 2, tz - 8, 6)                              # 臂頂的滑車
    rope_line(T, (x0 + 1.5, Y1 - 4.5, cz + 2), (x0 + 1.5, ty - 1, tz - 2), ROPE)   # 從輪軸捲上來的繩 ⇒ 臂頂
    hz = 30                                                            # 吊鉤離棧橋面 3 m
    rope_line(T, (x0 + 0.5, ty - 1.5, tz - 8), (x0 + 0.5, ty - 1.5, hz + 4), ROPE)
    T.box('body', x0, ty - 2, hz, x0 + 1, ty - 1, hz + 4, IRON, force=True)
    for (dx, dy) in ((-5, -4), (5, -4), (-5, 5), (5, 5)):              # 貨網（同起重架的那一張）
        rope_line(T, (x0 + 0.5, ty - 1.5, hz), (x0 + 0.5 + dx, ty - 1.5 + dy, hz - 9), ROPE)
    for x in range(x0 - 6, x0 + 7):
        for y in range(ty - 7, ty + 5):
            T.put('body', x, y, hz - 10, ROPE, force=True)
            if x in (x0 - 6, x0 + 6) or y in (ty - 7, ty + 4):
                T.box('body', x, y, hz - 10, x + 1, y + 1, hz - 2, ROPE, force=True)
    for bx in (x0 - 3, x0 + 4):
        for y in range(ty - 5, ty + 3):
            for x in range(bx - 3, bx + 3):
                for z in range(hz - 9, hz - 2):
                    if math.hypot(x + 0.5 - bx, z + 0.5 - (hz - 5.5)) <= 3.2:
                        T.put('body', x, y, z, IRON if y in (ty - 5, ty + 2) else FRAME if (y - ty) % 3 == 0 else FLOOR, force=True)


def post_crane(T, x0, reach):
    """柱式小吊車（小船泊位）：一根方柱（0.3 m、高 5 m）、斜撐、往水那一邊伸出的吊臂、臂頂滑車、吊鉤；柱腳一個捲繩的小絞輪。z 0 ＝ 棧橋面。"""
    py = 14
    T.box('body', x0 - 2, py - 2, 0, x0 + 2, py + 2, 2, FRAME)
    T.box('body', x0 - 1, py - 1, 0, x0 + 2, py + 2, 52, FRAME)
    ty, tz = EY + reach, 52
    rope_line(T, (x0 + 0.5, py + 0.5, 50), (x0 + 0.5, ty, tz), FRAME, r=1)
    rope_line(T, (x0 + 0.5, py + 0.5, 28), (x0 + 0.5, py + (ty - py) * 0.55, 51), FRAME)
    tackle_block(T, x0, ty - 2, tz - 7, 5)
    rope_line(T, (x0 + 0.5, ty - 1.5, tz - 7), (x0 + 0.5, ty - 1.5, 24), ROPE)
    T.box('body', x0, ty - 2, 20, x0 + 1, ty - 1, 24, IRON, force=True)
    T.box('body', x0 + 2, py - 3, 6, x0 + 8, py + 4, 12, WOOD_D)        # 絞輪（橫著的木鼓）
    rope_line(T, (x0 + 5.5, py + 0.5, 12), (x0 + 1.5, py + 0.5, 50), ROPE)


def gangway_tower(T, x0):
    """登船梯塔（超巨艦泊位）：木架塔 2.4 × 2.4 m、高 7 m、裡面一道之字梯；頂上一座吊橋板往水那一邊伸 2.5 m（搭到船舷）。z 0 ＝ 棧橋面。"""
    X0, Y0 = x0 - 12, 4
    for (x, y) in ((X0, Y0), (X0 + 21, Y0), (X0, Y0 + 21), (X0 + 21, Y0 + 21)):
        T.box('body', x, y, 0, x + 3, y + 3, 72, FRAME)
    for z in (0, 24, 48, 70):
        T.box('body', X0, Y0, z, X0 + 24, Y0 + 3, z + 2, FRAME); T.box('body', X0, Y0 + 21, z, X0 + 24, Y0 + 24, z + 2, FRAME)
        T.box('body', X0, Y0, z, X0 + 3, Y0 + 24, z + 2, FRAME); T.box('body', X0 + 21, Y0, z, X0 + 24, Y0 + 24, z + 2, FRAME)
    for k, (za, zb) in enumerate(((2, 24), (26, 48), (50, 70))):        # 之字梯（每段 2.2 m 高）
        xa, xb = (X0 + 4, X0 + 20) if k % 2 == 0 else (X0 + 20, X0 + 4)
        rope_line(T, (xa + 0.5, Y0 + 8, za), (xb + 0.5, Y0 + 8, zb), WOOD, r=1)
        rope_line(T, (xa + 0.5, Y0 + 14, za), (xb + 0.5, Y0 + 14, zb), WOOD, r=1)
    T.box('body', X0, Y0, 70, X0 + 24, Y0 + 24, 72, WOOD)              # 頂上的平台
    T.box('body', X0 + 6, Y0 + 24, 70, X0 + 18, EY + 25, 72, WOOD)      # 吊橋板（伸到預留區 2.5 m）
    T.box('body', X0 + 6, Y0 + 24, 72, X0 + 7, EY + 25, 80, FRAME); T.box('body', X0 + 17, Y0 + 24, 72, X0 + 18, EY + 25, 80, FRAME)   # 扶手


def berth_model(cls, layout):
    """一個泊位（cls）：layout ＝ {bollard: 'wood'|'cannon', bstep, cranes: [(x, 'tread'|'post', reach)], ladders, lamps, cargo: [(x, y, kind)], sacks, capstans, coils, gangways}。"""
    C = CLS[cls]
    X, Y = C['len'] * 10, int((EDGE + C['w']) * 10)
    Z = ZD + max([96] + [80 if c[1] == 'tread' else 60 for c in layout.get('cranes', [])])
    D = Deck(X, Y, Z)
    T = D.T
    used = []                                                          # 起重機、梯塔佔的 x 範圍（繫纜樁讓開）
    for (x, kind, reach) in layout.get('cranes', []):
        if kind == 'tread':
            treadwheel_crane(T, x, reach, salt=x); used.append((x - 28, x + 28))
        else:
            post_crane(T, x, reach); used.append((x - 6, x + 6))
    for x in layout.get('gangways', []):
        gangway_tower(T, x); used.append((x - 16, x + 16))
    bs = layout['bstep']
    for x in range(bs // 2, X, bs):                                    # 繫纜樁：棧橋邊往裡 0.5 m（y 25），間距 bstep
        if any(a <= x <= b for a, b in used):
            continue
        (cannon_bollard if layout['bollard'] == 'cannon' else wood_bollard)(T, x, 25)
    for k, x in enumerate(layout.get('lamps', [])):
        lamp_post(T, x, '燈籠-%d' % (k + 1))
    for k, (x, y, kind) in enumerate(layout.get('cargo', [])):
        cargo(T, x, y, kind, ('酒桶' if kind == 'barrel' else '貨箱') + '-%d' % (k + 1))
    for (x, y) in layout.get('sacks', []):
        sacks(T, x, y, 5)
    for (x, y) in layout.get('capstans', []):
        capstan(T, x, y)
    for (x, y) in layout.get('coils', []):
        rope_coil(T, x, y)
    M = D.done()
    fenders(M, X, layout.get('fstep', 40))
    for x in layout.get('ladders', []):
        ladder(M, x)
    M.anchor('lot-0', 0, 0, ZD)
    M.anchor('door', min(X - 1, layout.get('door', X // 2)), 10, ZD)  # 上下船的地方（棧橋面，邊往裡 2 m）
    return {'key': 'berth-' + cls, 'title': '%s（共用：%s）' % (C['name'], layout['desc']), 'use': 'berth-' + cls, 'lot': (C['len'], EDGE + C['w']), 'M': M,
            'style': 'common', 'layers': {'body': '棧橋上的擺設', 'roof': '起重機的屋頂'}, 'ground': (0, ZD), 'door_deck': True, 'meta': {'edge': EDGE, 'deckz': SINK, 'base': 0}, 'px': 1 if X > 1200 else 2}


def berth_boat():
    return berth_model('boat', dict(bollard='wood', bstep=70, ladders=[96], lamps=[150], coils=[(40, 12)], cargo=[(120, 6, 'barrel')], door=100,
                              desc='小艇靠的短段：兩根繫纜木樁、上下船的鐵梯、護舷木、燈柱、繩盤與一個桶'))


def berth_small():
    return berth_model('small', dict(bollard='wood', bstep=120, ladders=[236], lamps=[300], cranes=[(150, 'post', 40)], coils=[(380, 12)],
                               cargo=[(60, 6, 'crate2'), (76, 6, 'crate'), (66, 16, 'barrel'), (410, 6, 'barrel'), (424, 6, 'barrel')], sacks=[(90, 4)], door=240,
                               desc='繫纜木樁每 12 m、柱式小吊車、鐵梯、護舷、燈柱、貨箱、桶、貨袋'))


def berth_large():
    return berth_model('large', dict(bollard='cannon', bstep=150, ladders=[290, 720], lamps=[200, 820], cranes=[(500, 'tread', 60)], capstans=[(880, 14)], coils=[(110, 12), (640, 12)],
                               cargo=[(400, 6, 'crate2'), (416, 6, 'crate2'), (432, 6, 'crate'), (408, 16, 'barrel'), (580, 6, 'barrel'), (594, 6, 'barrel'), (608, 6, 'crate')],
                               sacks=[(430, 14), (560, 14)], door=300,
                               desc='舊砲倒插的繫纜樁每 15 m、一座踏輪起重機、絞盤、兩道鐵梯、護舷、燈柱、貨箱、桶、貨袋'))


def berth_huge():
    return berth_model('huge', dict(bollard='cannon', bstep=160, ladders=[260, 800, 1340], lamps=[150, 800, 1450], cranes=[(500, 'tread', 70), (1100, 'tread', 70)],
                              capstans=[(330, 14), (1270, 14)], coils=[(700, 12), (900, 12)],
                              cargo=[(400, 6, 'crate2'), (416, 6, 'crate2'), (408, 16, 'barrel'), (600, 6, 'barrel'), (614, 6, 'barrel'), (1000, 6, 'crate2'), (1016, 6, 'crate'),
                                     (1200, 6, 'barrel'), (1214, 6, 'barrel'), (1228, 6, 'crate2')], sacks=[(430, 14), (1030, 14)], door=800,
                              desc='舊砲倒插的繫纜樁每 16 m、兩座踏輪起重機、兩座絞盤、三道鐵梯、護舷、燈柱、貨'))


def berth_titan():
    return berth_model('titan', dict(bollard='cannon', bstep=200, ladders=[300, 1500, 2700], lamps=[150, 900, 1500, 2100, 2850], cranes=[(700, 'tread', 80), (1900, 'tread', 80), (2400, 'tread', 80)],
                               gangways=[1200], capstans=[(500, 14), (1650, 14), (2600, 14)], coils=[(1000, 12), (2200, 12)],
                               cargo=[(600, 6, 'crate2'), (616, 6, 'crate2'), (608, 16, 'barrel'), (800, 6, 'barrel'), (814, 6, 'barrel'), (1800, 6, 'crate2'), (1816, 6, 'crate'),
                                      (2000, 6, 'barrel'), (2014, 6, 'barrel'), (2300, 6, 'crate2'), (2316, 6, 'crate2'), (2500, 6, 'barrel')],
                               sacks=[(630, 14), (1830, 14), (2330, 14)], door=1200,
                               desc='舊砲倒插的繫纜樁每 20 m、三座踏輪起重機、登船梯塔、三座絞盤、三道鐵梯、護舷、燈柱、貨'))


ALL = [berth_boat, berth_small, berth_large, berth_huge, berth_titan]
