# 畜牧建築（TASK-0926；Tim 2026-10-25：「然後可以先開一下資源建築的task 根據資源也把建築分成幾組(每組3~4種) 我先分配一下建造任務吧」）。
# 地塊照 Blocksail world/buildings.js：養雞場 henhouse 8 × 8 m、豬圈 pigsty 8 × 10 m、牧場 ranch 16 × 12 m；
#   配方是穀飼（egg-barley、pork-barley、cattle-barley 吃大麥，基本的吃玉米；PRODUCTION §12.9 ⑥）⇒ 院子看得出飼料：穀袋、裝穀的槽、料箱。
#   牧場的牧草地（annex pasture）之後才做 ⇒ 這一版只做主建築與圍欄院子，後緣的圍欄留一道門接牧草地。
# 拆法：牆身 body（地、牆、圍欄、槽、牲畜、擺設）＋屋頂 roof；每一種一件成品、沒有配方變體（一款配兩條配方）。
# 工具同 meadow-farm-01m（⇐ apex-one-industry-01m ⇐ trailhead-harbour-01m ⇐ ame-carib-civic-01m ⇐ summit-carib-01m 的調色盤、Model、牆、屋頂、部件）。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 風格 common（毛石、木板、木瓦、茅草、木柵）。史料：這一批沒有上網查 —— 雞舍架高的棲木與產卵箱、半露天的豬圈（矮石牆圍的泥地＋後面的石砌豬舍）、
#   牛欄的乾草架與料槽是歐洲鄉間的通法（設計），寫在作品 notes。
# 牲畜是擺設（雕在牆身）：遊戲沒有動物 —— 先讓人看得出這塊地在養什麼。
import math
from workshops2 import *                                               # noqa: F401,F403
from industry import heap                                              # noqa: E402
from townpub import end_gable                                          # noqa: E402
from farm import ground, trough, rick, sack_row, well, cart, _Shift, HAY, HAY_D, CORN, SACKC   # noqa: E402

BARLEY = 177                     # 大麥（淺黃褐；同乾草那一色）
MUD = 108                        # 豬圈的泥（深褐）
MANURE = 100                     # 糞堆（褐）
HEN_W, HEN_B, COMB = 255, 140, 224   # 白雞、褐雞、雞冠（紅橙；⛔ 不用 160：那是百葉與門的換色角色）
PIG, SNOUT = 242, 206            # 豬（粉）、鼻與耳（深一點的粉）
COW, COW_W, HOOF, HORN = 140, 255, 100, 218   # 牛（黃褐）、白斑、蹄與尾、角


# ─────────────────────────────── 共用的小件 ───────────────────────────────
def walls_to_roof(M, R, t, z0, top, thick, color=BOARD):
    """單坡頂底下的牆補到屋面下（不然高的那一邊牆頂跟屋面之間空一截）：只補還空著的格（屋面那幾格不動）。"""
    X0, Y0, X1, Y1 = R
    for x in range(X0, X1):
        for y in range(Y0, Y1):
            if X0 + t <= x < X1 - t and Y0 + t <= y < Y1 - t:
                continue
            zt = top.get((x, y))
            if zt is None:
                continue
            for z in range(z0, zt - thick + 1):
                if M.get(x, y, z) is None:
                    M.put('body', x, y, z, color)


def rail_fence(M, pts, h=13, step=12, gap=None):
    """柱與橫桿的圍欄（牛欄）：沿 pts 的折線（軸向段），每 step 格一根 2 × 2 的柱（z 1..h），兩道橫桿（z 6、z h−1）；gap ＝ [(x0, y0, x1, y1)] 那幾段不做（門）。"""
    def skip(x, y):
        return gap and any(a <= x < c and b <= y < d for (a, b, c, d) in gap)
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        n = max(abs(xb - xa), abs(yb - ya))
        sx = (xb > xa) - (xb < xa)
        sy = (yb > ya) - (yb < ya)
        for i in range(n + 1):
            x, y = xa + sx * i, ya + sy * i
            if skip(x, y):
                continue
            post = i % step == 0 or i == n or skip(x + sx, y + sy) or skip(x - sx, y - sy)
            if post:
                M.box('body', x, y, 1, x + 2, y + 2, h + 1, FRAME)
            for z in (6, h - 1):
                M.put('body', x, y, z, LOG)


def hen(M, x, y, face, color):
    """一隻雞（2 × 3、高 0.4 m）：face ＝ 頭朝哪（'x+'、'x-'、'y+'、'y-'）；雞冠一格紅橙、尾巴翹一格。"""
    ax = face[0]
    s = 1 if face[1] == '+' else -1
    def p(u, v, z, c):                 # u ＝ 沿頭的方向（0 尾 … 2 頭）、v ＝ 橫（0、1）
        if ax == 'x':
            M.put('body', x + (u if s > 0 else 2 - u), y + v, z, c)
        else:
            M.put('body', x + v, y + (u if s > 0 else 2 - u), z, c)
    for u in range(3):
        for v in range(2):
            p(u, v, 1, color)
            p(u, v, 2, color)
    p(2, 0, 3, color)                  # 頭
    p(2, 0, 4, COMB)
    p(0, 1, 3, color)                  # 尾巴


def pig(M, x0, y0, face, color=PIG):
    """一頭豬（寬 5、長 13、高 0.8 m）：face ＝ 'y+'／'y-'／'x+'／'x-'（鼻子朝哪）。"""
    ax = face[0]
    s = 1 if face[1] == '+' else -1
    L = 13
    def p(u, v, z, c):                 # u ＝ 沿身體（0 屁股 … 12 鼻）、v ＝ 橫（0..4）
        uu = u if s > 0 else L - 1 - u
        if ax == 'y':
            M.put('body', x0 + v, y0 + uu, z, c)
        else:
            M.put('body', x0 + uu, y0 + v, z, c)
    for (u, v) in ((1, 1), (1, 3), (8, 1), (8, 3)):          # 腿（⛔ v 0、4：身體那一側在 z 3 修圓了 ⇒ 腿接不上）
        for z in (1, 2):
            p(u, v, z, SNOUT)
    for u in range(0, 10):                                   # 身體
        for v in range(5):
            for z in range(3, 8):
                if (v in (0, 4) and z in (3, 7)) or (u == 0 and z == 7):
                    continue                                 # 圓一點
                p(u, v, z, color)
    for u in range(10, 12):                                  # 頭
        for v in range(1, 4):
            for z in range(3, 7):
                p(u, v, z, color)
    for v in (1, 3):
        p(11, v, 7, SNOUT)                                   # 耳
    for v in range(1, 4):
        for z in (4, 5):
            p(12, v, z, SNOUT)                               # 鼻
    p(0, 2, 7, SNOUT)                                        # 捲尾巴（屁股頂那一格修圓空著）


def cow(M, x0, y0, face, patch=True):
    """一頭牛（寬 7、長 23、高 1.6 m）：face ＝ 'y+'／'y-'／'x+'／'x-'（頭朝哪）；黃褐、背上一塊白斑、兩支角。"""
    ax = face[0]
    s = 1 if face[1] == '+' else -1
    L = 23
    def p(u, v, z, c):
        uu = u if s > 0 else L - 1 - u
        if ax == 'y':
            M.put('body', x0 + v, y0 + uu, z, c)
        else:
            M.put('body', x0 + uu, y0 + v, z, c)
    for (u, v) in ((2, 0), (2, 5), (15, 0), (15, 5)):       # 腿（2 × 2 的方柱、蹄深色）
        for du in (0, 1):
            for dv in (0, 1):
                for z in range(1, 8):
                    p(u + du, v + dv, z, HOOF if z == 1 else COW)
    for u in range(1, 18):                                   # 身體
        for v in range(7):
            for z in range(8, 15):
                if (v in (0, 6) and z in (8, 14)) or (u in (1, 17) and z in (8, 14)):
                    continue
                c = COW_W if patch and 6 <= u <= 11 and z >= 12 and 1 <= v <= 5 else COW
                p(u, v, z, c)
    for u in range(18, 22):                                  # 脖子與頭（低一點，在吃草的樣子）
        for v in range(2, 5):
            for z in range(9 - (u - 18), 15 - (u - 18)):
                p(u, v, z, COW if u < 21 else COW_W)
    p(22, 3, 7, HOOF)                                        # 鼻
    p(22, 3, 8, HOOF)
    for v in (1, 5):                                         # 角
        p(19, v, 13, HORN)
        p(19, v, 12, COW)
    for z in range(9, 14):                                   # 尾巴
        p(0, 3, z, HOOF)


def grain_trough(M, x0, y0, n, w=4, z1=4, legs=False):
    """裝穀的木槽（沿 x、長 n、寬 w）：玉米與大麥混著（黃、淺黃褐）；legs ⇒ 架高 0.3 m 的料槽（牛）。"""
    zb = 4 if legs else 1
    if legs:
        for x in (x0, x0 + n - 2):
            M.box('body', x, y0, 1, x + 2, y0 + w, zb, FRAME)
    M.box('body', x0, y0, zb, x0 + n, y0 + w, zb + z1 - 1, BOARD)
    for x in range(x0 + 1, x0 + n - 1):
        for y in range(y0 + 1, y0 + w - 1):
            M.put('body', x, y, zb + z1 - 2, CORN if h01('gt', x, y) < 0.55 else BARLEY, True)


def hay_rack(M, x0, y0, n, h=16):
    """乾草架（牛）：兩頭木柱、上下兩道橫木、中間斜放的木條（每 3 格一根）、裡面塞滿乾草。"""
    for x in (x0, x0 + n - 2):
        M.box('body', x, y0, 1, x + 2, y0 + 6, h + 1, FRAME)
    M.box('body', x0, y0, 4, x0 + n, y0 + 6, 5, BOARD)                       # 底板（接草屑）
    for x in range(x0 + 2, x0 + n - 2):
        M.put('body', x, y0, h, FRAME)
        M.put('body', x, y0 + 5, h, FRAME)
        if (x - x0) % 3 == 0:
            for z in range(5, h):
                M.put('body', x, y0 + (z - 5) * 2 // (h - 5), z, FRAME)     # 前面的斜條
                M.put('body', x, y0 + 5 - (z - 5) * 2 // (h - 5), z, FRAME)
        for y in range(y0 + 1, y0 + 5):
            for z in range(5, h - 1):
                if M.get(x, y, z) is None:
                    M.put('body', x, y, z, HAY if (x + y + z) % 4 else HAY_D)


def water_pan(M, x0, y0, n=6):
    """淺水盤（雞）：一圈木框、裡面水。"""
    M.box('body', x0, y0, 1, x0 + n, y0 + n, 2, BOARD)
    M.box('body', x0 + 1, y0 + 1, 1, x0 + n - 1, y0 + n - 1, 2, WATER, True)


def feed_bin(M, x0, y0, w=10, d=6, h=8):
    """料箱：木板箱、蓋子掀開靠在後面，裡面滿到口的穀（黃與淺黃褐）。"""
    M.box('body', x0, y0, 1, x0 + w, y0 + d, h, BOARD)
    for x in range(x0 + 1, x0 + w - 1):
        for y in range(y0 + 1, y0 + d - 1):
            M.put('body', x, y, h - 1, CORN if h01('fb', x, y) < 0.5 else BARLEY, True)
    M.box('body', x0, y0 + d, h - 1, x0 + w, y0 + d + 1, h + 5, BOARD_D)    # 掀開的蓋


def post_lantern(M, name, x, y, h=20):
    """木柱上的燈籠（院子裡沒有牆可以掛）：2 × 2 的柱、燈籠掛在柱的正面（−y）。"""
    M.box('body', x, y, 1, x + 2, y + 2, h, FRAME)
    lantern(M, name, (x + 1, y - 1, h - 4))


# ─────────────────────────────── 養雞場 8 × 8 m ───────────────────────────────
def henhouse():
    """養雞場：左後木板雞舍（3.4 × 3.2 m、木瓦單坡頂、木板門、側窗；右牆開雞洞接一道有橫條的斜板、後牆外一排產卵箱），
    右邊木柵圍的雞場（料槽、水盤、棲木、十隻雞）；前院料箱、三袋穀、四處啄食的雞；正面木柵、中間是門。"""
    M = Model((80, 80, 45))
    ground(M, 1, 1, 79, 79, 9261, 'body')
    picket_fence(M, [(1, 1), (34, 1)])
    picket_fence(M, [(46, 1), (78, 1)])
    picket_fence(M, [(1, 1), (1, 78), (78, 78), (78, 1)])
    # 雞舍
    R = (6, 40, 40, 72)
    board_walls(M, R, 0, 24, 2)
    M.box('body', R[0] + 2, R[1] + 2, 0, R[2] - 2, R[3] - 2, 1, FLOOR)
    top = shed_roof(M, R[0] - 2, R[1] - 3, R[2] + 2, R[3] + 3, 34, 0.3, low='front', color_fn=lambda x, y, f, r, e: shingle_color(x, y, f, r, e, 9262))
    walls_to_roof(M, R, 2, 24, top, 2)
    for y in range(R[1] + 6, R[3] - 4, 6):                                     # 屋裡的棲木（從雞洞、窗看得到）
        M.box('body', R[0] + 2, y, 12, R[2] - 2, y + 1, 13, FRAME)
    put_part(M, 'door-plank', '雞舍-門', 'front', R, 16, 0, 2)
    put_part(M, 'window-board', '雞舍-窗', 'left', R, 56, 8, 2)
    for L in M.links:                                                          # 門框底那一層壓到地 ⇒ 地讓給門
        for k in L['cells']:
            M.cells.pop(k, None)
    M.clear(R[2] - 2, 52, 5, R[2], 57, 11)                                    # 雞洞（右牆，0.5 m 高的洞口）
    for x in range(R[2], R[2] + 10):                                           # 斜板：從洞口斜到地，每兩格一道橫條
        z = 4 - (x - R[2]) * 4 // 10
        zp = 4 - max(0, x - 1 - R[2]) * 4 // 10
        for zz in range(min(z, zp), max(z, zp) + 1):
            M.box('body', x, 52, zz, x + 1, 57, zz + 1, BOARD)
        if (x - R[2]) % 2 == 1:
            M.box('body', x, 52, z + 1, x + 1, 57, z + 2, FRAME)
    for i, x in enumerate(range(R[0] + 4, R[0] + 28, 8)):                       # 產卵箱（後牆外，三格；斜蓋）
        M.box('body', x, R[3], 6, x + 7, R[3] + 4, 12, BOARD)
        M.box('body', x + 1, R[3], 7, x + 6, R[3] + 3, 11, HAY, True)
        M.put('body', x + 3, R[3] + 1, 8, HEN_W if i % 2 == 0 else HEN_B, True)   # 蹲在窩裡的雞
        M.box('body', x, R[3] + 3, 12, x + 7, R[3] + 4, 13, BOARD_D)
    for x in (R[0] + 4, R[0] + 26):                                            # 產卵箱的腳
        M.box('body', x, R[3] + 2, 1, x + 1, R[3] + 3, 6, FRAME)
    lantern(M, '燈籠-雞舍', (28, R[1] - 1, 18))
    # 雞場（右邊）：前面一道木柵、左邊接雞舍
    picket_fence(M, [(40, 14), (46, 14)])
    picket_fence(M, [(52, 14), (78, 14)])
    picket_fence(M, [(40, 14), (40, R[1])])
    picket_fence(M, [(40, R[3]), (40, 78)])
    grain_trough(M, 50, 28, 22)
    water_pan(M, 64, 44)
    for x in (58, 72):                                                         # 棲木
        M.box('body', x, 62, 1, x + 2, 64, 11, FRAME)
    M.box('body', 58, 62, 10, 74, 64, 11, LOG)
    for (x, y, f, c) in ((52, 24, 'y+', HEN_W), (57, 25, 'y+', HEN_B), (63, 24, 'y+', HEN_W), (68, 25, 'y+', HEN_W),
                         (55, 34, 'y-', HEN_B), (61, 34, 'y-', HEN_W), (70, 50, 'x-', HEN_B), (48, 46, 'x+', HEN_W),
                         (54, 70, 'y-', HEN_W), (66, 56, 'x+', HEN_B)):
        hen(M, x, y, f, c)
    for (x, y) in ((53, 23), (60, 23), (66, 23), (58, 35)):                    # 撒在槽邊的穀
        M.put('body', x, y, 1, CORN)
    # 前院：料箱、穀袋、兩隻在外面晃的雞
    feed_bin(M, 26, 28)
    sack_row(M, 8, 26, 3, layer='body')
    hen(M, 12, 14, 'x+', HEN_B)
    hen(M, 30, 18, 'y-', HEN_W)
    M.anchor('door', 16, 38, 1)
    M.anchor('lot-0', 0, 0, 0)
    M.anchor('work-a1', 60, 26, 1)                                             # 雞場：撒穀、加水、撿蛋
    M.anchor('work-a1-to', 60, 30, 3)
    M.anchor('work-a2', 66, 40, 1)
    M.anchor('work-a2-to', 67, 47, 2)
    M.anchor('work-b1', 31, 36, 1)                                             # 前院：從料箱舀穀
    M.anchor('work-b1-to', 31, 31, 6)
    return {'key': 'henhouse', 'title': '養雞場（共用：木板雞舍與產卵箱、木柵雞場、料槽與料箱）', 'use': 'henhouse', 'lot': (8, 8), 'M': M, 'style': 'common',
            'layers': {'body': '雞舍、雞場與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 豬圈 8 × 10 m ───────────────────────────────
def pigsty():
    """豬圈：後面毛石的豬舍（7.2 × 3.0 m、茅草單坡頂、中間隔開，兩個低矮的入口通到前面的圈）；
    前面兩個矮毛石牆圍的泥地圈（各兩頭豬、靠前牆的石槽裝著拌穀的豬食）、木板圈門；臨路的走道上穀袋、餿水桶、木柵與門。"""
    M = Model((80, 100, 40))
    ground(M, 1, 1, 79, 99, 9271, 'body')
    picket_fence(M, [(1, 1), (34, 1)])
    picket_fence(M, [(46, 1), (78, 1)])
    picket_fence(M, [(1, 1), (1, 26)])
    picket_fence(M, [(78, 1), (78, 26)])
    # 豬舍
    R = (4, 66, 76, 96)
    rubble_walls(M, R, 0, 16, 4, salt=9272)
    top = shed_roof(M, R[0] - 2, R[1] - 3, R[2] + 2, R[3] + 3, 28, 0.36, low='front', thick=3,
                    color_fn=lambda x, y, f, r, e: thatch_color(x, y, f, r, e, 9273))
    walls_to_roof(M, R, 4, 16, top, 3, RUBBLE)
    M.box('body', 38, R[1], 0, 42, R[3], 16, RUBBLE)                           # 中間隔牆
    walls_to_roof(M, (38, R[1], 42, R[3]), 2, 16, top, 3, RUBBLE)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 1, HAY)           # 舍裡鋪的稻草
    for x0 in (16, 54):                                                        # 兩個入口（0.9 × 1.2 m）
        M.clear(x0, R[1], 1, x0 + 9, R[1] + 4, 13)
        M.box('body', x0 - 1, R[1], 13, x0 + 10, R[1] + 4, 15, FRAME, True)   # 木過梁
    # 圈：矮石牆（0.9 m）、中間隔開、各一道木板門
    rubble_walls(M, (4, 26, 76, R[1] + 2), 0, 9, 3, salt=9274)
    M.box('body', 38, 26, 0, 41, R[1], 9, RUBBLE)
    for x0 in (26, 46):                                                        # 圈門
        M.clear(x0, 26, 1, x0 + 8, 29, 9)
        M.box('body', x0, 27, 1, x0 + 8, 28, 9, BOARD)
        M.box('body', x0, 27, 4, x0 + 8, 28, 5, BOARD_D, True)
    for x in range(7, 73):                                                     # 圈裡是泥地（一灘一灘的水）
        for y in range(29, R[1]):
            if M.get(x, y, 0) and M.get(x, y, 0)[1] in (108, 141):
                M.put('body', x, y, 0, WATER if h01('mp', x // 4, y // 4) < 0.07 else MUD, True)
    for x0 in (8, 56):                                                         # 石槽（靠前牆，裡面是拌了穀的豬食）
        M.box('body', x0, 29, 1, x0 + 14, 34, 5, RUBBLE)
        for x in range(x0 + 1, x0 + 13):
            for y in range(30, 33):
                M.put('body', x, y, 4, CORN if h01('sl', x, y) < 0.35 else BARLEY, True)
    pig(M, 12, 40, 'y-')
    pig(M, 24, 46, 'x-')
    pig(M, 58, 38, 'y-')
    pig(M, 48, 50, 'x+', SNOUT)
    # 走道：穀袋、餿水桶、木柱燈籠
    sack_row(M, 52, 8, 3, layer='body')
    tub(M, 14, 14, 1, 8, 4, BARLEY)
    M.box('body', 22, 12, 1, 26, 16, 5, BOARD)                                 # 小桶
    M.box('body', 23, 13, 4, 25, 15, 5, CORN, True)
    post_lantern(M, '燈籠-圈門', 36, 20)
    M.anchor('door', 30, 25, 1)
    M.anchor('lot-0', 0, 0, 0)
    M.anchor('work-a1', 15, 24, 1)                                             # 走道：隔著矮牆倒豬食
    M.anchor('work-a1-to', 15, 31, 5)
    M.anchor('work-a2', 63, 24, 1)
    M.anchor('work-a2-to', 63, 31, 5)
    M.anchor('work-a3', 56, 18, 1)                                             # 穀袋那邊
    M.anchor('work-a3-to', 59, 10, 4)
    return {'key': 'pigsty', 'title': '豬圈（共用：毛石豬舍與茅草頂、矮石牆的泥地圈、石槽）', 'use': 'pigsty', 'lot': (8, 10), 'M': M, 'style': 'common',
            'layers': {'body': '豬舍、圈與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 牧場 16 × 12 m ───────────────────────────────
def ranch():
    """牧場：左後木板牛棚（7.0 × 5.2 m、木瓦兩坡頂、大貨門、窗；裡面靠後牆的乾草）；右邊柱與橫桿的牛欄（乾草架、架高的料槽、水槽、四頭牛），
    牛欄後面一道門接牧草地；前院穀袋、裝穀袋的牛車、水井、糞堆；正面木柵、中間是門。"""
    M = Model((160, 120, 65))
    ground(M, 1, 1, 159, 119, 9281, 'body')
    picket_fence(M, [(1, 1), (34, 1)])
    picket_fence(M, [(46, 1), (84, 1)])
    picket_fence(M, [(1, 1), (1, 118)])
    # 牛棚
    R = (6, 60, 76, 112)
    board_walls(M, R, 0, 30, 2, bay=26)
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 30, 0.6, z0=30)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.6, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=9282)
    put_part(M, 'cartdoor', '牛棚-貨門', 'front', R, 30, 0, 2)
    put_part(M, 'window-board', '牛棚-窗', 'front', R, 60, 9, 2)
    put_part(M, 'vent', '牛棚-氣窗', 'right', R, 86, 16, 2)
    for L in M.links:
        for k in L['cells']:
            M.cells.pop(k, None)
    rick(M, 10, 96, 72, 108, 16, layer='body')                                 # 靠後牆的乾草
    M.box('body', 50, 70, 1, 70, 76, 5, BOARD)                                 # 棚裡的料槽
    for x in range(51, 69):
        for y in range(71, 75):
            M.put('body', x, y, 4, CORN if h01('rk', x, y) < 0.5 else BARLEY, True)
    cow(M, 54, 77, 'y-', patch=False)                                          # 棚裡一頭
    lantern(M, '燈籠-牛棚', (50, R[1] - 1, 22))
    # 牛欄
    pts = [(84, 1), (84, 118), (158, 118), (158, 16), (84, 16)]
    rail_fence(M, pts, gap=[(110, 117, 128, 119), (112, 15, 124, 17)])
    hay_rack(M, 92, 22, 22)
    grain_trough(M, 122, 36, 28, w=5, legs=True)
    trough(M, 132, 92, 18)
    cow(M, 96, 30, 'y-')                                                       # 吃乾草
    cow(M, 126, 42, 'y-')                                                      # 吃穀
    cow(M, 136, 60, 'x-', patch=False)
    cow(M, 100, 80, 'x+')
    # 前院
    sack_row(M, 50, 20, 4, layer='body')
    cart(M, 60, 30, load=lambda m, x, y, z: [m.box('body', x + 1 + 5 * (i % 2), y + 1 + 5 * (i // 2), z, x + 5 + 5 * (i % 2), y + 5 + 5 * (i // 2), z + 5, SACKC) for i in range(6)], layer='body')
    well(M, 20, 40)
    heap(_Shift(M, 1), 70, 48, 7, 5, 6, lambda x, y, z: MANURE if (x + y + z) % 3 else MUD, layer='body')
    M.anchor('door', 30, 58, 1)
    M.anchor('lot-0', 0, 0, 0)
    M.anchor('work-a1', 103, 20, 1)                                            # 牛欄：添乾草、倒穀、看水
    M.anchor('work-a1-to', 103, 25, 10)
    M.anchor('work-a2', 136, 33, 1)
    M.anchor('work-a2-to', 136, 38, 7)
    M.anchor('work-a3', 141, 89, 1)
    M.anchor('work-a3-to', 141, 94, 3)
    M.anchor('work-b1', 40, 66, 1)                                             # 牛棚裡
    M.anchor('work-b1-to', 40, 100, 8)
    return {'key': 'ranch', 'title': '牧場（共用：木板牛棚、柱與橫桿的牛欄、乾草架與料槽；後面一道門接牧草地）', 'use': 'ranch', 'lot': (16, 12), 'M': M, 'style': 'common',
            'layers': {'body': '牛棚、牛欄與擺設', 'roof': '屋頂'}}


ALL = [henhouse, pigsty, ranch]
