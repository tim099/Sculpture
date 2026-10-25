# 泊位建築（Blocksail TASK-0906；docs/TOWN_BUILD.md §5.19、BUILDING_SPEC §6.21）—— 五級泊位在棧橋（碼頭線）上的擺設：繫纜樁、護舷、梯、燈、貨、起重設施。
# 工具照 trailhead-harbour-01m/design/quay.py（圓材、繩、滑車、繫纜木樁）⇒ 它再 import ame-carib-civic-01m 的 harbour.py（絞盤、繩盤）與 summit-carib-01m 的調色盤、Model、屋頂。
#
# 座標（跟一般建築不同，§6.21）：
#   x ＝ 沿棧橋（泊位長；從棧橋上面向水看，左 → 右）；y ＝ 往水：y 0 ＝ 棧橋邊往裡 EDGE 公尺、y = EDGE × 10 ＝ 棧橋邊、再往外是船停的預留區（泊位寬）；
#   z ＝ 往上，z SINK × 10 ＝ 棧橋面（遊戲把模型往下放 SINK 公尺 ⇒ 護舷、梯子伸得到水裡）。0.1 m／格。
#   遊戲（Blockside 63_towns.js townLotInst）照地塊的 berth.over 把 y 0 對到「棧橋邊往裡 EDGE 公尺」（棧橋寬 6、8、10 m 都一樣貼邊）、不墊石基。
# 棧橋面本身由遊戲畫（規劃的 piers、quays）⇒ 棧橋上（y < EDGE × 10）什麼都不擺（運輸通道；魚骨式只在棧橋邊立船尾纜樁）；泊位自己的平台、指形棧橋（連樁、樑）在這裡雕；
#   預留區除了護舷與起重機的吊臂之外是空的（船停在那裡）。
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
# 五級（同 world/town.js BERTH_CLS：泊位長 len（沿棧橋）、預留那一塊往外 out、平台 apron、指形棧橋寬 fw；fl ＝ 指形棧橋伸多長〔設計：船長的八成上下〕）
#   大船以上（Tim 2026-10-25「起重機可能要往外擴(自帶一小段棧橋) 不然會讓棧橋沒有運輸通道」）：棧橋邊外先一條 apron 公尺的平台（樁上鋪板），起重機、貨、繫纜樁、梯都在平台上，船靠平台外緣 ⇒ 棧橋面空出來走貨
#   小艇、小船（「泊位是否可以自帶一小段棧橋(現實中那樣的魚骨泊位?)」）：魚骨式 —— 一格停一艘、船身垂直棧橋（船尾靠棧橋），格的兩側各半根指形棧橋（相鄰兩格拼成一根 fw 寬的）⇒ 模型左右對稱
CLS = {'boat': dict(name='小艇泊位', len=8, out=16, fw=1.6, fl=10), 'small': dict(name='小船泊位', len=16, out=40, fw=2.0, fl=28),
       'large': dict(name='大船泊位', len=100, out=24, apron=8), 'huge': dict(name='巨艦泊位', len=160, out=32, apron=8), 'titan': dict(name='超巨艦泊位', len=300, out=52, apron=12)}
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


def deck_strip(M, x0, x1, y0, y1, piles_x=(), piles_y=(), salt=0):
    """泊位自己的一段棧橋（平台、指形棧橋）：面板 0.3 m（z ZD − 3 ～ ZD，面跟棧橋面齊；板沿 y 鋪、每 0.3 m 一條，舊板灰一點）、
    底下沿 x 的樑（0.3 m 高）、樁（0.4 m 見方、從水面下到樑底；piles_x × piles_y 每一點一根）。畫在真的 z。"""
    for x in range(x0, x1):
        k = (x // 3 + salt) % 7
        c = WOOD_G if k == 3 else WOOD_D if k == 5 else WOOD
        M.box('body', x, y0, ZD - 3, x + 1, y1, ZD, c, force=True)
    for y in sorted(set([y0, y1 - 3] + [p - 1 for p in piles_y])):
        M.box('body', x0, max(y0, y), ZD - 6, x1, min(y1, y + 3), ZD - 3, WOOD_D, force=True)
    for px in piles_x:
        for py in piles_y:
            M.box('body', px - 2, py - 2, 0, px + 2, py + 2, ZD - 6, WOOD_G, force=True)


def fenders(M, X, step, y=EY, x0=0, axis='x'):
    """護舷：每 step 格一根直立木樁（0.3 × 0.2 m、從水面下 0.6 m 到棧橋面上 0.2 m）＋ 一道橫的護木（棧橋面下 0.3 m）。
    axis 'x' ⇒ 貼在 y 這條邊上、沿 x 排（棧橋邊、平台外緣）；'y' ⇒ 貼在 x ＝ y 這條邊上、沿 y 從 x0 排到 X（指形棧橋朝船那一面）。畫在真的 z。"""
    if axis == 'x':
        for x in range(step // 2, X - 2, step):
            M.box('body', x, y, 0, x + 3, y + 2, ZD + 2, WOOD_D)
        M.box('body', 0, y, ZD - 5, X, y + 1, ZD - 2, WOOD_D, force=True)
    else:
        for t in range(x0 + step // 2, X - 2, step):
            M.box('body', y, t, 0, y + 2, t + 3, ZD + 2, WOOD_D)
        M.box('body', y, x0, ZD - 5, y + 1, X, ZD - 2, WOOD_D, force=True)


def ladder(M, x0, y=EY):
    """上下小艇的鐵梯：兩根鐵條掛在邊上（y），從水面下到棧橋面，每 0.3 m 一級踏棍。"""
    for x in (x0, x0 + 6):
        M.box('body', x, y + 2, 0, x + 1, y + 3, ZD + 4, IRON, force=True)
        M.box('body', x, y, ZD + 3, x + 1, y + 2, ZD + 4, IRON, force=True)   # 頂上彎回面上
    for z in range(2, ZD + 1, 3):
        M.box('body', x0, y + 2, z, x0 + 7, y + 3, z + 1, IRON, force=True)


def lamp_post(T, x0, name, y=22):
    """燈柱：方木 0.4 m、高 3.6 m，柱頂掛一盞燈籠（外部模型，kind light ⇒ 遊戲夜裡點亮）—— 擺法照起重架的穩索樁（quay.py sheers）。"""
    T.box('body', x0 - 2, y, 0, x0 + 2, y + 4, 36, FRAME)
    T.box('body', x0 - 3, y - 1, 33, x0 + 3, y + 5, 34, FRAME)
    T.models.append({'name': name, 'source': LANTERN, 'at': [x0 + 0.5, y, 33], 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}})


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


def treadwheel_crane(T, x0, reach, salt=0, y0=4):
    """踏輪起重機（treadwheel crane；Bruges、Gdańsk、Lüneburg 的港口吊車那一型）：
    - 棚：四根柱（0.3 m）圍 4.8 × 2.4 m、高 6 m，兩坡木瓦頂（屋脊沿 x）；柱腳一圈木地檻。y0 ＝ 棚靠棧橋那一邊。
    - 踏輪：直徑 4.4 m、寬 1.2 m，輪面在 x–z 平面（人在裡面沿 x 走）；兩圈輪緣、各 8 根輻條、一圈踏板（沿 y 的木條）；輪軸沿 y 穿過兩邊的柱。
    - 吊臂：從屋脊往水那一邊（+y）伸出到棚外 reach 格，斜撐從前柱撐到吊臂中段；臂頂一個滑車、吊索垂到吊鉤，鉤上掛一張貨網（兩個桶）。
    - 繩：從輪軸捲上來、沿吊臂到臂頂的滑車。
    大小是設計（史料上的港口踏輪吊車輪徑 4～7 m）。z 0 ＝ 棧橋面。"""
    X0, X1, Y0, Y1 = x0 - 24, x0 + 24, y0, y0 + 24
    for (x, y) in ((X0, Y0), (X1 - 3, Y0), (X0, Y1 - 3), (X1 - 3, Y1 - 3)):
        T.box('body', x, y, 0, x + 3, y + 3, 60, FRAME)
    T.box('body', X0, Y0, 0, X1, Y0 + 3, 2, FRAME); T.box('body', X0, Y1 - 3, 0, X1, Y1, 2, FRAME)     # 地檻
    T.box('body', X0, Y0, 0, X0 + 3, Y1, 2, FRAME); T.box('body', X1 - 3, Y0, 0, X1, Y1, 2, FRAME)
    T.box('body', X0, Y0, 58, X1, Y0 + 3, 61, FRAME); T.box('body', X0, Y1 - 3, 58, X1, Y1, 61, FRAME)  # 柱頭梁
    T.box('body', X0, Y0, 58, X0 + 3, Y1, 61, FRAME); T.box('body', X1 - 3, Y0, 58, X1, Y1, 61, FRAME)
    shingle_roof(T, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 61, 'p': 0.7, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=906 + salt)
    # 踏輪
    cz, R = 26, 22
    wy0, wy1 = Y0 + 3, Y0 + 16                                        # 兩圈輪緣（各 2 格寬）的 y
    for x in range(x0 - R - 1, x0 + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            d = math.hypot(x + 0.5 - x0, z + 0.5 - cz)
            if R - 3 <= d < R - 1 and (int(math.degrees(math.atan2(z + 0.5 - cz, x + 0.5 - x0))) // 9) % 2 == 0:
                T.box('body', x, wy0, z, x + 1, wy1 + 2, z + 1, WOOD, force=True)   # 踏板（沿 y 的木條；兩頭伸進輪緣 ⇒ 接在一起）
    for x in range(x0 - R - 1, x0 + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            d = math.hypot(x + 0.5 - x0, z + 0.5 - cz)
            for yr in (wy0, wy1):
                if R - 2 <= d <= R:
                    T.box('body', x, yr, z, x + 1, yr + 2, z + 1, WOOD_D, force=True)
    for k in range(8):                                                 # 輻條
        a = k * math.pi / 4
        for yr in (wy0, wy1):
            rope_line(T, (x0 + 0.5, yr + 0.5, cz + 0.5), (x0 + 0.5 + math.cos(a) * (R - 2), yr + 0.5, cz + 0.5 + math.sin(a) * (R - 2)), WOOD_D)
            rope_line(T, (x0 + 0.5, yr + 1.5, cz + 0.5), (x0 + 0.5 + math.cos(a) * (R - 2), yr + 1.5, cz + 0.5 + math.sin(a) * (R - 2)), WOOD_D)
    T.box('body', x0 - 1, Y0, cz - 1, x0 + 2, Y1, cz + 2, FRAME, force=True)   # 輪軸（穿過兩邊）
    T.box('body', x0 - 2, Y0, 0, x0 + 3, Y0 + 3, cz, FRAME, force=True)        # 軸架（前後各一根立柱撐輪軸）
    T.box('body', x0 - 2, Y1 - 3, 0, x0 + 3, Y1, cz, FRAME, force=True)
    # 吊臂：從屋脊往 +y 伸出（臂頂在 y Y1 ＋ reach、z 78），斜撐
    ty, tz, ry = Y1 + reach, 78, Y0 + 11                               # 吊臂從屋脊（棚的中線）伸出去 ⇒ 不穿屋面
    for dx in (-1, 0):
        rope_line(T, (x0 + dx + 0.5, ry + 0.5, 71), (x0 + dx + 0.5, ty, tz), FRAME, r=1)
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


def gangway_tower(T, x0, y0, edge):
    """登船梯塔（超巨艦泊位）：木架塔 2.4 × 2.4 m、高 7 m、裡面一道之字梯；頂上一座吊橋板往水那一邊伸到平台外緣外 2.5 m（搭到船舷）。z 0 ＝ 棧橋面。"""
    X0, Y0 = x0 - 12, y0
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
    T.box('body', X0 + 6, Y0 + 24, 70, X0 + 18, edge + 25, 72, WOOD)    # 吊橋板（伸到平台外緣外 2.5 m）
    T.box('body', X0 + 6, Y0 + 24, 72, X0 + 7, edge + 25, 80, FRAME); T.box('body', X0 + 17, Y0 + 24, 72, X0 + 18, edge + 25, 80, FRAME)   # 扶手


def apron_model(cls, layout):
    """大船以上：棧橋邊（y EY）外一條 apron 公尺的平台（y EY ～ AY），擺設全在平台上（棧橋面上什麼都不擺 ⇒ 運輸通道）、船靠平台外緣 AY。
    layout 的 y（dy）都從平台內緣（棧橋邊）量：{bollard, bstep, cranes: [(x, reach)]（reach ＝ 吊臂伸過平台外緣幾格）, ladders, lamps,
    cargo: [(x, dy, kind)], sacks: [(x, dy)], capstans: [(x, dy)], coils: [(x, dy)], gangways}。"""
    C = CLS[cls]
    A = int(C['apron'] * 10)
    X, Y, AY = C['len'] * 10, int((EDGE + C['apron'] + C['out']) * 10), EY + A
    Z = ZD + 96
    D = Deck(X, Y, Z)
    T = D.T
    used = []                                                          # 起重機、梯塔佔的 x 範圍（繫纜樁讓開）
    cy0 = EY + 8                                                       # 起重機的棚：平台內緣往外 0.8 m 起（2.4 m 深）⇒ 棚外到平台外緣留一條走道
    for (x, reach) in layout.get('cranes', []):
        treadwheel_crane(T, x, (AY - cy0 - 24) + reach, salt=x, y0=cy0); used.append((x - 28, x + 28))
    for x in layout.get('gangways', []):
        gangway_tower(T, x, EY + 10, AY); used.append((x - 16, x + 16))
    bs = layout['bstep']
    for x in range(bs // 2, X, bs):                                    # 繫纜樁：平台外緣往裡 0.5 m，間距 bstep
        if any(a <= x <= b for a, b in used):
            continue
        (cannon_bollard if layout['bollard'] == 'cannon' else wood_bollard)(T, x, AY - 5)
    for k, x in enumerate(layout.get('lamps', [])):
        lamp_post(T, x, '燈籠-%d' % (k + 1), y=EY + 2)                  # 燈柱站平台內緣（不擋纜繩、不佔棧橋）
    for k, (x, dy, kind) in enumerate(layout.get('cargo', [])):
        cargo(T, x, EY + dy, kind, ('酒桶' if kind == 'barrel' else '貨箱') + '-%d' % (k + 1))
    for (x, dy) in layout.get('sacks', []):
        sacks(T, x, EY + dy, 5)
    for (x, dy) in layout.get('capstans', []):
        capstan(T, x, EY + dy)
    for (x, dy) in layout.get('coils', []):
        rope_coil(T, x, EY + dy)
    M = D.done()
    py = [EY + 4, AY - 4] + ([EY + A // 2] if A >= 100 else [])       # 樁：平台兩緣（寬 12 m 的中間再一排）、沿 x 每 4 m
    deck_strip(M, 0, X, EY, AY, piles_x=list(range(20, X - 4, 40)), piles_y=py, salt=len(cls))
    fenders(M, X, layout.get('fstep', 40), y=AY)
    for x in layout.get('ladders', []):
        ladder(M, x, y=AY)
    M.anchor('lot-0', 0, 0, ZD)
    M.anchor('door', min(X - 1, layout.get('door', X // 2)), 10, ZD)  # 上下船的地方（棧橋面，邊往裡 2 m）
    return {'key': 'berth-' + cls, 'title': '%s（共用：%s）' % (C['name'], layout['desc']), 'use': 'berth-' + cls, 'lot': (C['len'], EDGE + C['apron'] + C['out']), 'M': M,
            'style': 'common', 'layers': {'body': '平台與上面的擺設', 'roof': '起重機的屋頂'}, 'ground': (0, ZD), 'door_deck': True,
            'meta': {'edge': EDGE, 'deckz': SINK, 'base': 0, 'apron': C['apron']}, 'px': 1 if X > 1200 else 2}


def finger_model(cls, layout):
    """小艇、小船：魚骨式一格（x 0 ～ X 沿棧橋），兩側各半根指形棧橋（x 0 ～ h、X − h ～ X；從棧橋邊 y EY 伸 fl 公尺）、船停中間、船尾靠棧橋。
    指形棧橋：面板、樑、外側一排樁（每 4 m）、朝船那一面護舷、每 cstep 一根繫纜木樁（兩側都有 ⇒ 船兩舷都綁得到）、尖端一根高一點的繫船樁；
    棧橋邊（y EY）這一格中間的船尾纜樁、護舷。棧橋面上不擺貨（運輸通道）。layout：{cstep, lamp（尖端掛燈：左半根）, ladder（棧橋邊中間一道鐵梯）}。"""
    C = CLS[cls]
    X, Y, h, FL = C['len'] * 10, int((EDGE + C['out']) * 10), int(round(C['fw'] * 10 / 2)), int(C['fl'] * 10)
    Z = ZD + 40
    D = Deck(X, Y, Z)
    T = D.T
    tip = EY + FL
    cs = layout['cstep']
    for xc in (h // 2, X - h + h // 2):                                # 兩側的半根：繫纜木樁、尖端的繫船樁
        for y in range(EY + cs, tip - 10, cs):
            wood_bollard(T, xc, y, h=6)
        T.box('body', xc - 2, tip - 6, 0, xc + 2, tip - 2, 14, WOOD_D)
    for xb in ([X // 2 - 30, X // 2 + 30] if X >= 120 else [X // 2]):  # 棧橋邊的船尾纜樁（棧橋邊往裡 0.5 m）
        wood_bollard(T, xb, EY - 5, h=7)
    if layout.get('lamp'):
        lamp_post(T, h // 2, '燈籠-1', y=tip - 12)
    M = D.done()
    for (a, b, px) in ((0, h, 2), (X - h, X, X - 3)):
        deck_strip(M, a, b, EY, tip, piles_x=[px], piles_y=list(range(EY + 20, tip, 40)) + [tip - 3], salt=a)
    fenders(M, tip, 30, y=h, x0=EY, axis='y')                         # 朝船那一面的護舷（左半根的內側 x h、右半根的內側 x X − h − 2）
    fenders(M, tip, 30, y=X - h - 2, x0=EY, axis='y')
    fenders(M, X, 30, y=EY)                                            # 棧橋邊（船尾）
    if layout.get('ladder'):
        ladder(M, X // 2 - 3, y=EY)
    M.anchor('lot-0', 0, 0, ZD)
    M.anchor('door', X // 2, 10, ZD)
    return {'key': 'berth-' + cls, 'title': '%s（共用：%s）' % (C['name'], layout['desc']), 'use': 'berth-' + cls, 'lot': (C['len'], EDGE + C['out']), 'M': M,
            'style': 'common', 'layers': {'body': '指形棧橋與上面的擺設', 'roof': '（無）'}, 'ground': (0, ZD), 'door_deck': True,
            'meta': {'edge': EDGE, 'deckz': SINK, 'base': 0, 'fw': C['fw']}, 'px': 2}


def berth_boat():
    return finger_model('boat', dict(cstep=40, desc='魚骨式一格：兩側各半根指形棧橋（10 m）、繫纜木樁、尖端繫船樁、護舷、棧橋邊的船尾纜樁'))


def berth_small():
    return finger_model('small', dict(cstep=80, lamp=True, ladder=True,
                                      desc='魚骨式一格：兩側各半根指形棧橋（28 m）、繫纜木樁每 8 m、尖端繫船樁與燈、護舷、船尾纜樁、鐵梯'))


def berth_large():
    return apron_model('large', dict(bollard='cannon', bstep=150, ladders=[290, 720], lamps=[200, 820], cranes=[(500, 40)], capstans=[(880, 50)], coils=[(110, 60), (640, 60)],
                                     cargo=[(380, 40, 'crate2'), (396, 40, 'crate2'), (412, 40, 'crate'), (388, 54, 'barrel'), (590, 40, 'barrel'), (604, 40, 'barrel'), (618, 40, 'crate')],
                                     sacks=[(420, 56), (570, 56)], door=300,
                                     desc='自帶 8 m 平台（樁上鋪板）：舊砲倒插的繫纜樁每 15 m、一座踏輪起重機、絞盤、兩道鐵梯、護舷、燈柱、貨箱、桶、貨袋'))


def berth_huge():
    return apron_model('huge', dict(bollard='cannon', bstep=160, ladders=[260, 800, 1340], lamps=[150, 800, 1450], cranes=[(500, 45), (1100, 45)],
                                    capstans=[(330, 50), (1270, 50)], coils=[(700, 60), (900, 60)],
                                    cargo=[(380, 40, 'crate2'), (396, 40, 'crate2'), (388, 54, 'barrel'), (610, 40, 'barrel'), (624, 40, 'barrel'), (980, 40, 'crate2'), (996, 40, 'crate'),
                                           (1210, 40, 'barrel'), (1224, 40, 'barrel'), (1238, 40, 'crate2')], sacks=[(420, 56), (1010, 56)], door=800,
                                    desc='自帶 8 m 平台：舊砲倒插的繫纜樁每 16 m、兩座踏輪起重機、兩座絞盤、三道鐵梯、護舷、燈柱、貨'))


def berth_titan():
    return apron_model('titan', dict(bollard='cannon', bstep=200, ladders=[300, 1500, 2700], lamps=[150, 900, 1500, 2100, 2850], cranes=[(700, 50), (1900, 50), (2400, 50)],
                                     gangways=[1200], capstans=[(500, 60), (1650, 60), (2600, 60)], coils=[(1000, 90), (2200, 90)],
                                     cargo=[(580, 50, 'crate2'), (596, 50, 'crate2'), (588, 64, 'barrel'), (810, 50, 'barrel'), (824, 50, 'barrel'), (1780, 50, 'crate2'), (1796, 50, 'crate'),
                                            (2010, 50, 'barrel'), (2024, 50, 'barrel'), (2280, 50, 'crate2'), (2296, 50, 'crate2'), (2510, 50, 'barrel')],
                                     sacks=[(620, 70), (1820, 70), (2320, 70)], door=1200,
                                     desc='自帶 12 m 平台：舊砲倒插的繫纜樁每 20 m、三座踏輪起重機、登船梯塔、三座絞盤、三道鐵梯、護舷、燈柱、貨'))


ALL = [berth_boat, berth_small, berth_large, berth_huge, berth_titan]
