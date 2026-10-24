# 農莊與種植園的主建築（Tim 2026-10-24：「試著幫目前的農莊建造專用建築模型吧(可以做一款基礎款 並基於基礎款作微調(替換子模型) 做出幾款農莊 目前都是用住宅模型」）。
# 地塊照 Blocksail world/buildings.js：農莊 farm 12 × 12 m、種植園 plantation 16 × 12 m；田（annex）長在地塊後面（y 大的那一邊），這裡只做主建築與院子。
# 拆法：每一種一個基礎款（牆身 body、屋頂 roof：農舍／主屋、倉棚、院子、水井、圍籬），各款共用這兩件；
#   後半的「作業區」（work，y ≥ WORK_Y）是各款自己的子作品 —— 換作業區 ＝ 換一款（build.py 的 share）。
#   配方對到哪一款寫在成品的 meta recipes（逗號分隔；遊戲照地塊的 recipe 挑，沒對到的用基礎款）。
# 工具同 apex-one-industry-01m（⇐ trailhead-harbour-01m ⇐ ame-carib-civic-01m ⇐ summit-carib-01m 的調色盤、Model、牆、屋頂、部件）。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 風格 common（毛石、木板、茅草、木瓦）⇒ 法屬、英屬、西屬的城都擺得下（TOWN_BUILD §2.1 的退路）。
# 史料：這一批沒有上網查 —— 配置是設計（17 世紀加勒比海與歐洲鄉間農莊的常見樣子：打穀場、玉米倉、烤菸棚、靛藍三池、曬可可的台），寫在作品 notes。
import math
from workshops2 import *                                               # noqa: F401,F403
from industry import heap, cord, wheelbarrow, shovel, yard_ground, stone_block   # noqa: E402
from townpub import end_gable, trestle_table                           # noqa: E402
import kit                                                             # noqa: E402

kit.PRIO['work'] = 2             # 作業區比牆身低一級 ⇒ 各款的作業區碰到共用的牆身一格都改不動（共用的那兩件才能逐格跟基礎款一樣）

WORK_Y = 64                      # 作業區從這一排起（往後到地塊後緣，接著是田）
HAY, HAY_D = 177, 140            # 乾草、麥稈（淺黃褐）與陰影
CORN = 252                       # 玉米穗（黃）
CORN_H = 177                     # 玉米苞葉（乾）
CABBAGE, CABBAGE_D = 52, 32      # 菜（綠、深綠）
PUMPKIN = 240                    # 南瓜（橙）
ROOT = 173                       # 木薯根（紅褐）
MEAL = 255                       # 木薯粉（白）
LEAF_G, LEAF_B = 52, 100         # 菸葉：剛掛上去的綠、烤乾的褐
INDIGO_W, INDIGO_C = 6, 10       # 靛藍的水（深藍）、曬乾的靛藍塊
CANE, CANE_T = 148, 177          # 甘蔗稈（暗的黃綠；188 在遊戲裡是螢光綠，整捆跳出來）、切口與枯葉
COTTON = 255                     # 棉花（白）
POD = 228                        # 可可果莢（紅橙）
BEAN = 100                       # 曬乾的可可豆（褐）
SACKC = 218                      # 麻袋（米白）


# ─────────────────────────────── 共用的小件 ───────────────────────────────
def ground(M, x0, y0, x1, y1, salt, layer):
    """院子的地（一層，z 0）：同 industry.yard_ground（灰褐的土 141 ＋ 零星深一點的 108），可以指定層。"""
    for x in range(x0, x1):
        for y in range(y0, y1):
            M.put(layer, x, y, 0, 108 if h01('gd', salt, x // 3, y // 3) < 0.12 else 141)


def well(M, cx, cy, layer='body'):
    """水井：毛石井欄（外半徑 6、高 0.8 m、裡面黑）、兩根木柱、橫的轆轤（搖把）、一只吊桶。"""
    for x in range(cx - 7, cx + 8):
        for y in range(cy - 7, cy + 8):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 6.2:
                M.box(layer, x, y, 0, x + 1, y + 1, 8 if d > 4.2 else 1, (MORTAR if (x + y) % 5 == 0 else RUBBLE) if d > 4.2 else DARK)
    for x in (cx - 6, cx + 5):
        M.box(layer, x, cy, 8, x + 1, cy + 1, 22, FRAME)
    M.box(layer, cx - 6, cy, 20, cx + 6, cy + 1, 21, LOG)                         # 轆轤
    M.box(layer, cx + 6, cy, 18, cx + 7, cy + 1, 21, FRAME)                       # 搖把
    M.box(layer, cx - 1, cy, 12, cx + 1, cy + 1, 20, ROPE)
    M.box(layer, cx - 2, cy - 1, 9, cx + 2, cy + 2, 12, BOARD)                    # 吊桶


def trough(M, x0, y0, n=16, layer='body'):
    """木水槽（沿 x、長 n、寬 4、高 4，裡面一層水）。"""
    M.box(layer, x0, y0, 0, x0 + n, y0 + 4, 4, BOARD)
    M.box(layer, x0 + 1, y0 + 1, 2, x0 + n - 1, y0 + 3, 4, WATER, force=True)


def stook(M, cx, cy, h=10, layer='work'):
    """麥束堆（stook）：幾捆立著靠成一個小尖堆，頂上一捆橫壓（半徑 3）。"""
    for x in range(cx - 3, cx + 4):
        for y in range(cy - 3, cy + 4):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            t = int(h * (1 - d / 3.6))
            for z in range(1, max(1, t) + 1):
                M.put(layer, x, y, z, HAY_D if z == 1 or (x + y + z) % 4 == 0 else HAY)


def rick(M, x0, y0, x1, y1, h, layer='work'):
    """草垛（長方的乾草堆，頂上收成一道脊）。"""
    w = (y1 - y0) / 2.0
    for x in range(x0, x1):
        for y in range(y0, y1):
            d = abs(y + 0.5 - (y0 + w)) / w
            t = int(h * (1 - 0.55 * d * d))
            for z in range(1, t + 1):
                M.put(layer, x, y, z, HAY_D if (x * 3 + z) % 7 == 0 else HAY)


def sack_row(M, x0, y0, n, layer='work', color=SACKC):
    """一排立著的麻袋（每個 4 × 4 × 6、頂上收口）。"""
    for i in range(n):
        x = x0 + i * 5
        M.box(layer, x, y0, 1, x + 4, y0 + 4, 6, color)
        M.box(layer, x + 1, y0 + 1, 6, x + 3, y0 + 3, 7, ROPE)


def basket(M, cx, cy, fill, layer='work'):
    """編的籃（半徑 3、高 4、裝滿 fill）。"""
    for x in range(cx - 3, cx + 4):
        for y in range(cy - 3, cy + 4):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 3.2:
                M.box(layer, x, y, 1, x + 1, y + 1, 4, HAY_D if d > 2.2 else fill)
                if d <= 2.2:
                    M.put(layer, x, y, 4, fill)


def open_shed(M, x0, y0, x1, y1, ze, salt, posts_step=20, layer='work', roof='thatch'):
    """開敞的棚：四周柱子、兩坡頂（屋脊沿 x）。回傳屋面高度場。⛔ 屋頂畫在同一層（作業區的棚屬於那一款）。"""
    pts = sorted({(x, y) for x in list(range(x0, x1 - 2, posts_step)) + [x1 - 2] for y in (y0, y1 - 2)})
    for (x, y) in pts:
        M.box(layer, x, y, 1, x + 2, y + 2, ze, FRAME)
    for y in (y0, y1 - 2):
        M.box(layer, x0, y, ze, x1, y + 2, ze + 2, FRAME)
    F = roof_field([{'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'ze': ze + 2, 'p': 0.55, 'over': (2, 2, 3, 3), 'gable': 'x'}])
    fn = (lambda x, y, f, r, e: thatch_color(x, y, f, r, e, salt)) if roof == 'thatch' else (lambda x, y, f, r, e: shingle_color(x, y, f, r, e, salt))
    return build_roof(M, F, 3 if roof == 'thatch' else 2, layer, color_fn=fn, force=False)


def cart(M, x0, y0, load=None, layer='work'):
    """兩輪的牛車（沿 +y：車轅往前 −y）：木板車斗 12 × 18、兩個大輪（側看一圈）、車轅；load(M, x, y, z) 自己往斗裡裝。"""
    M.box(layer, x0, y0, 6, x0 + 12, y0 + 18, 7, BOARD)
    for (xa, ya, xb, yb) in ((x0, y0, x0 + 1, y0 + 18), (x0 + 11, y0, x0 + 12, y0 + 18), (x0, y0, x0 + 12, y0 + 1), (x0, y0 + 17, x0 + 12, y0 + 18)):
        M.box(layer, xa, ya, 7, xb, yb, 10, BOARD_D)
    for x in (x0 - 1, x0 + 12):                                                  # 輪：半徑 5 的圈（在 y–z 平面）＋輪轂
        for y in range(y0 + 3, y0 + 15):
            for z in range(1, 13):
                d = math.hypot(y + 0.5 - (y0 + 9), z + 0.5 - 6.5)
                if 4.4 <= d <= 5.6:
                    M.put(layer, x, y, z, FRAME)
    for x in (x0 + 4, x0 + 7):                                                   # 車轅（往前伸、斜落到地；六連通）
        rope_line(M, (x, y0, 6), (x, y0 - 14, 1), color=FRAME, layer=layer)
    if load:
        load(M, x0 + 1, y0 + 1, 7)


# ─────────────────────────────── 農莊 12 × 12 m 的基礎款 ───────────────────────────────
def farm_base(M):
    """農莊的共用部分（牆身＋屋頂）：左前毛石的農舍（4.8 × 3.6 m、茅草兩坡頂、山牆邊一根毛石煙囪、木板門、兩扇窗），
    右前木板的穀倉（4.4 × 4.8 m、木瓦兩坡頂、大貨門），中間的院子、農舍後面的水井、穀倉邊的水槽；正面與兩側木柵，後面敞開接田。"""
    ground(M, 2, 2, 118, WORK_Y, 9101, 'body')
    picket_fence(M, [(1, 1), (22, 1)])
    picket_fence(M, [(40, 1), (78, 1)])
    picket_fence(M, [(106, 1), (118, 1)])
    picket_fence(M, [(1, 1), (1, 118)])
    picket_fence(M, [(118, 1), (118, 118)])
    # 農舍
    R = (6, 10, 58, 46)
    rubble_walls(M, R, 0, 24, 4, salt=9102)
    for x0, x1 in ((R[0], R[0] + 4), (R[2] - 4, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 24, 0.8, z0=24, color=RUBBLE, edge=RUBBLE_D)
    top = thatch_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 24, 'p': 0.8, 'over': (3, 3, 4, 4), 'gable': 'x'}], salt=9103)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 1, FLOOR)
    zc = max(top[(x, y)] for x in range(8, 16) for y in range(24, 32)) + 6         # 煙囪：左山牆裡側、穿出茅草頂
    M.box('body', 8, 24, 1, 16, 32, zc, RUBBLE, force=True)
    M.box('body', 7, 23, zc - 2, 17, 33, zc, MORTAR, force=True)
    M.box('body', 10, 26, zc - 2, 14, 30, zc, DARK, force=True)
    M.anchor('smoke', 12, 28, zc - 1)
    put_part(M, 'door-plank', '農舍-門', 'front', R, 26, 0, 4)                  # 毛石牆 4 格厚 ⇒ 開口挖穿 4 格
    put_part(M, 'window-board', '農舍-前窗', 'front', R, 46, 9, 4)
    put_part(M, 'window-board', '農舍-後窗', 'back', R, 28, 9, 4)
    trestle_table(M, 34, 48, 30, 38, 8)                                          # 屋裡一張桌
    # 穀倉
    B = (70, 8, 114, 56)
    board_walls(M, B, 0, 30, 2)
    for x0, x1 in ((B[0], B[0] + 2), (B[2] - 2, B[2])):
        end_gable(M, x0, x1, B[1], B[3], 30, 0.6, z0=30)
    shingle_roof(M, [{'x0': B[0], 'y0': B[1], 'x1': B[2], 'y1': B[3], 'ze': 30, 'p': 0.6, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=9104)
    M.box('body', B[0] + 2, B[1] + 2, 0, B[2] - 2, B[3] - 2, 1, FLOOR)
    put_part(M, 'cartdoor', '穀倉-貨門', 'front', B, 92, 0, 2)
    put_part(M, 'vent', '穀倉-氣窗', 'right', B, 32, 16, 2)
    for L in M.links:                                                            # 門框底那一層壓到院子的地 ⇒ 地讓給門
        for k in L['cells']:
            M.cells.pop(k, None)
    rick(M, 74, 40, 110, 52, 12, layer='body')                                   # 穀倉裡靠後牆的乾草
    # 院子：水井（農舍後面）、水槽（穀倉左邊）
    well(M, 30, 56)
    trough(M, 60, 52, 8)
    lantern(M, '燈籠-農舍', (12, R[1] - 1, 18))
    M.anchor('door', 26, 8, 1)
    M.anchor('lot-0', 0, 0, 0)
    return M


def farm_model():
    return Model((120, 120, 70))


FARM_LAYERS = {'body': '農舍、穀倉與院子', 'roof': '屋頂', 'work': '作業區'}


def farm_work_ground(M, salt):
    ground(M, 2, WORK_Y, 118, 118, salt, 'work')


def farm():
    """農莊（基礎款）：農舍、穀倉、院子；後院堆柴、一座草垛、一台手推車。"""
    M = farm_base(farm_model())
    farm_work_ground(M, 9110)
    rick(M, 10, 80, 50, 96, 14)
    for x in range(64, 100):                                                     # 柴堆（沿 x，靠右柵）
        for y in range(104, 112):
            for z in range(1, 9):
                end = x in (64, 99)
                M.put('work', x, y, z, LOG_TIP if end and (y + z) % 3 else LOG)
    wheelbarrow_w(M, 70, 76)
    return {'key': 'farm', 'title': '農莊（共用：毛石農舍與茅草頂、木板穀倉、院子與水井；後院草垛、柴堆）', 'use': 'farm', 'lot': (12, 12), 'M': M, 'style': 'common',
            'layers': FARM_LAYERS}


def wheelbarrow_w(M, x0, y0, load=None):
    """industry.wheelbarrow 畫在作業區那一層（輪子著地 z 1：z 0 是地）。"""
    M2 = _Shift(M, 1)
    wheelbarrow(M2, x0, y0, load, layer='work')


class _Shift:
    """把別人的小件整個抬 dz 格（作業區的地在 z 0 ⇒ 擺設從 z 1 起）。"""
    def __init__(s, M, dz):
        s.M, s.dz = M, dz

    def put(s, layer, x, y, z, c, force=False):
        s.M.put(layer, x, y, z + s.dz, c, force)

    def box(s, layer, x0, y0, z0, x1, y1, z1, c, force=False):
        s.M.box(layer, x0, y0, z0 + s.dz, x1, y1, z1 + s.dz, c, force)


def farm_grain():
    """麥與大麥的農莊：後院一塊圓的打穀場（踩實的淺土、邊上一圈石）、場上攤開的麥稈與兩把連枷；三個麥束堆；麥稈草垛；兩袋穀。"""
    M = farm_base(farm_model())
    farm_work_ground(M, 9120)
    cx, cy = 40, 92
    for x in range(cx - 20, cx + 21):                                            # 打穀場：半徑 19 的淺土、邊上一圈石
        for y in range(cy - 20, cy + 21):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 18:
                M.put('work', x, y, 0, 182 if h01('tf', x // 2, y // 2) < 0.2 else 218, True)
            elif d <= 19.5:
                M.box('work', x, y, 0, x + 1, y + 1, 2, RUBBLE)
    for x in range(cx - 12, cx + 10):                                            # 攤開的麥稈
        for y in range(cy - 6, cy + 8):
            if h01('st', x, y) < 0.55:
                M.put('work', x, y, 1, HAY if (x + y) % 3 else HAY_D)
    for (x, y) in ((cx - 2, cy - 12), (cx + 12, cy + 6)):                        # 連枷（長柄＋短的打棒）
        M.box('work', x, y, 1, x + 14, y + 1, 2, FRAME)
        M.box('work', x + 14, y, 1, x + 20, y + 1, 2, LOG)
    for (x, y) in ((76, 78), (88, 80), (100, 78)):
        stook(M, x, y, 11)
    rick(M, 70, 98, 112, 112, 16)
    sack_row(M, 64, 86, 2)
    return {'key': 'farm-grain', 'title': '麥莊（農莊：打穀場、麥束堆、麥稈草垛）', 'use': 'farm', 'lot': (12, 12), 'M': M, 'style': 'common',
            'layers': FARM_LAYERS, 'share': {'body': 'farm', 'roof': 'farm'}, 'variant': 'b', 'meta': {'recipes': 'wheat,barley'}}


def corn_crib(M, x0, y0, x1, y1, h=22):
    """玉米倉（corn crib）：架高 0.6 m 的窄長木條箱（板條之間留縫、看得到裡面的黃玉米）、茅草兩坡頂。"""
    for (x, y) in ((x0, y0), (x1 - 2, y0), (x0, y1 - 2), (x1 - 2, y1 - 2)):
        M.box('work', x, y, 1, x + 2, y + 2, 7, RUBBLE)                           # 石墩
    M.box('work', x0, y0, 7, x1, y1, 8, FLOOR)
    M.box('work', x0 + 1, y0 + 1, 8, x1 - 1, y1 - 1, 7 + h, CORN)               # 裡面滿滿的玉米（滿到板條頂 ⇒ 屋頂底下沒有封住的空腔）
    for z in range(8, 7 + h):
        for x in range(x0, x1):
            for y in range(y0, y1):
                if x in (x0, x1 - 1) or y in (y0, y1 - 1):
                    if (z % 3 != 2) or z >= 7 + h - 4 or x in (x0, x1 - 1) and y in (y0, y1 - 1):   # 最上面那幾道不留縫（屋簷壓下來會把縫封成空腔）
                        M.put('work', x, y, z, BOARD if (x + y) % 2 else BOARD_D, True)
    F = roof_field([{'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'ze': 7 + h, 'p': 0.7, 'over': (2, 2, 3, 3), 'gable': 'x'}])
    build_roof(M, F, 3, 'work', color_fn=lambda x, y, f, r, e: thatch_color(x, y, f, r, e, 9131), force=False)


def farm_maize():
    """玉米的農莊：後院兩座架高的玉米倉（木條箱、茅草頂）、一堆剝好的玉米穗、一堆苞葉、搓玉米的板凳與籃。"""
    M = farm_base(farm_model())
    farm_work_ground(M, 9130)
    corn_crib(M, 10, 74, 54, 88)
    corn_crib(M, 10, 96, 54, 110)
    heap(_Shift(M, 1), 80, 86, 12, 8, 7, lambda x, y, z: CORN if (x + y + z) % 4 else CORN_H, layer='work')
    heap(_Shift(M, 1), 98, 106, 9, 6, 6, lambda x, y, z: CORN_H if (x + z) % 3 else HAY_D, layer='work')
    M.box('work', 66, 100, 1, 84, 104, 5, BOARD)                                  # 板凳
    basket(M, 72, 110, CORN)
    basket(M, 62, 94, CORN)
    return {'key': 'farm-maize', 'title': '玉米莊（農莊：架高的玉米倉、玉米穗堆）', 'use': 'farm', 'lot': (12, 12), 'M': M, 'style': 'common',
            'layers': FARM_LAYERS, 'share': {'body': 'farm', 'roof': 'farm'}, 'variant': 'c', 'meta': {'recipes': 'maize'}}


def farm_vegetables():
    """菜園的農莊：後院木框的菜畦（甘藍一排一排、南瓜爬一畦）、堆肥、裝菜的籃、一架晾洋蔥的木架、澆菜的水桶。"""
    M = farm_base(farm_model())
    farm_work_ground(M, 9140)
    for i, y0 in enumerate(range(72, 112, 10)):                                  # 四畦：木框、土、菜
        M.box('work', 8, y0, 1, 60, y0 + 7, 2, FRAME)
        M.box('work', 9, y0 + 1, 1, 59, y0 + 6, 2, 108, True)
        for x in range(11, 58, 4):
            if i == 3:                                                           # 最後一畦是南瓜
                if (x // 4) % 2 == 0:
                    M.box('work', x, y0 + 2, 2, x + 3, y0 + 5, 4, PUMPKIN)
                M.box('work', x, y0 + 3, 2, x + 4, y0 + 4, 3, CABBAGE_D)
            else:
                M.box('work', x + 1, y0 + 2, 2, x + 3, y0 + 5, 4, CABBAGE)
                M.put('work', x + 1, y0 + 2, 4, CABBAGE_D)
    heap(_Shift(M, 1), 96, 104, 10, 8, 7, lambda x, y, z: 108 if (x + y + z) % 3 else CABBAGE_D, layer='work')   # 堆肥
    for (x, y, f) in ((70, 76, CABBAGE), (78, 76, PUMPKIN), (86, 78, ROOT)):
        basket(M, x, y, f)
    for x in (70, 98):                                                           # 晾洋蔥的架
        M.box('work', x, 88, 1, x + 2, 90, 20, FRAME)
    M.box('work', 70, 88, 20, 100, 90, 21, FRAME)
    for x in range(73, 97, 3):
        M.box('work', x, 88, 13, x + 1, 90, 20, HAY)
    trough(M, 70, 112, 10, layer='work')
    return {'key': 'farm-vegetables', 'title': '菜園莊（農莊：菜畦、堆肥、裝菜的籃、晾洋蔥的架）', 'use': 'farm', 'lot': (12, 12), 'M': M, 'style': 'common',
            'layers': FARM_LAYERS, 'share': {'body': 'farm', 'roof': 'farm'}, 'variant': 'd', 'meta': {'recipes': 'vegetables'}}


def farm_cassava():
    """木薯的農莊（加勒比海的 manioc）：後院茅草棚下刨木薯的長凳與刨板、壓汁的編管（couleuvre）吊在架上、
    石灶上烤木薯餅的大鐵盤（platine）；棚外攤在草蓆上曬的木薯粉、一堆剛挖的木薯根。"""
    M = farm_base(farm_model())
    farm_work_ground(M, 9150)
    open_shed(M, 10, 72, 70, 104, 22, 9151)
    M.box('work', 14, 78, 1, 44, 82, 7, BOARD)                                    # 刨木薯的長凳
    M.box('work', 18, 79, 7, 30, 81, 8, IRON)                                     # 刨板
    M.box('work', 54, 80, 1, 56, 82, 22, FRAME)                                    # 壓汁的架與吊著的編管
    M.box('work', 54, 80, 21, 66, 82, 22, FRAME, True)
    M.box('work', 62, 80, 8, 64, 82, 21, HAY_D)
    M.box('work', 61, 79, 4, 65, 83, 8, BOARD)                                     # 接汁的盆
    stone_block(_Shift(M, 1), 22, 90, 0, 44, 100, 6, salt=9152, layer='work')     # 石灶
    M.box('work', 24, 92, 7, 42, 98, 8, IRON)                                     # 烤餅的鐵盤
    M.box('work', 28, 93, 8, 38, 97, 9, MEAL)                                      # 盤上一張餅
    M.box('work', 23, 89, 2, 27, 90, 5, EMBER, True)
    for x0 in (78, 96):                                                          # 曬粉的草蓆
        M.box('work', x0, 74, 1, x0 + 16, 90, 2, HAY_D)
        M.box('work', x0 + 1, 75, 2, x0 + 15, 89, 3, MEAL)
    heap(_Shift(M, 1), 92, 106, 12, 7, 6, lambda x, y, z: ROOT if (x + y) % 4 else 108, layer='work')
    basket(M, 74, 100, ROOT)
    return {'key': 'farm-cassava', 'title': '木薯莊（農莊：刨木薯的棚、壓汁的編管、烤木薯餅的石灶、曬木薯粉的草蓆）', 'use': 'farm', 'lot': (12, 12), 'M': M, 'style': 'common',
            'layers': FARM_LAYERS, 'share': {'body': 'farm', 'roof': 'farm'}, 'variant': 'e', 'meta': {'recipes': 'cassava'}}


# ─────────────────────────────── 種植園 16 × 12 m 的基礎款 ───────────────────────────────
def plant_base(M):
    """種植園的共用部分（牆身＋屋頂）：左前種植園主的木板屋（7.2 × 4.0 m、架在毛石墩上 0.4 m、正面一道木廊與台階、木瓦兩坡頂），
    右前工具與存貨的木板棚（5.2 × 4.0 m、貨門），中間院子、水井；正面與兩側木柵，後面敞開接田。"""
    ground(M, 2, 2, 158, WORK_Y, 9201, 'body')
    picket_fence(M, [(1, 1), (30, 1)])
    picket_fence(M, [(52, 1), (106, 1)])
    picket_fence(M, [(130, 1), (158, 1)])
    picket_fence(M, [(1, 1), (1, 118)])
    picket_fence(M, [(158, 1), (158, 118)])
    R = (6, 18, 78, 58)
    for x in list(range(R[0], R[2] - 3, 12)) + [R[2] - 3]:                        # 毛石墩
        for y in (R[1], R[1] + 18, R[3] - 3):
            M.box('body', x, y, 0, x + 3, y + 3, 4, RUBBLE)
    M.box('body', R[0], R[1], 4, R[2], R[3], 5, FLOOR)
    board_walls(M, R, 5, 30, 2)
    for x0, x1 in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 30, 0.55, z0=30)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.55, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=9202)
    shed_roof(M, R[0] - 3, 4, R[2] + 3, R[1], 30, 0.25, low='front', color_fn=lambda x, y, f, r, e: shingle_color(x, y, f, r, e, 9205))   # 木廊的單坡頂（接在主屋簷下）
    # 正面木廊：地板（同屋）、柱、欄杆、中間的台階
    M.box('gallery', R[0], 6, 4, R[2], R[1], 5, FLOOR)
    for x in list(range(R[0], R[2] - 2, 18)) + [R[2] - 2]:
        M.box('gallery', x, 6, 0, x + 2, 8, 27, FRAME)
    rail(M, R[0], 34, 6, 5, gap=None)
    rail(M, 50, R[2], 6, 5, gap=None)
    steps(M, 34, 50, 6, 2, 2, run=3, back=False)
    put_part(M, 'door-double', '主屋-門', 'front', R, 42, 5, 2)
    for xc in (18, 66):
        put_part(M, 'window-board', '主屋-前窗-%d' % xc, 'front', R, xc, 13, 2)
    put_part(M, 'window-board', '主屋-後窗', 'back', R, 42, 13, 2)
    trestle_table(M, 20, 40, 36, 46, 13)
    # 工具與存貨的棚
    B = (98, 14, 152, 54)
    board_walls(M, B, 0, 26, 2)
    for x0, x1 in ((B[0], B[0] + 2), (B[2] - 2, B[2])):
        end_gable(M, x0, x1, B[1], B[3], 26, 0.6, z0=26)
    shingle_roof(M, [{'x0': B[0], 'y0': B[1], 'x1': B[2], 'y1': B[3], 'ze': 26, 'p': 0.6, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=9203)
    M.box('body', B[0] + 2, B[1] + 2, 0, B[2] - 2, B[3] - 2, 1, FLOOR)
    put_part(M, 'cartdoor', '存貨棚-貨門', 'front', B, 118, 0, 2)
    put_part(M, 'window-board', '存貨棚-側窗', 'right', B, 34, 10, 2)
    for L in M.links:
        for k in L['cells']:
            M.cells.pop(k, None)
    sack_row(_Ly(M, 'body'), 104, 46, 6)
    well(M, 88, 30)
    lantern(M, '燈籠-主屋', (R[0] + 20, 6, 22))
    M.anchor('door', 42, 2, 2)                                                  # 最下一級台階上面那一格
    M.anchor('lot-0', 0, 0, 0)
    return M


class _Ly:
    """把作業區的小件畫進別的層（基礎款裡的麻袋）。"""
    def __init__(s, M, layer):
        s.M, s.layer = M, layer

    def put(s, layer, x, y, z, c, force=False):
        s.M.put(s.layer, x, y, z, c, force)

    def box(s, layer, x0, y0, z0, x1, y1, z1, c, force=False):
        s.M.box(s.layer, x0, y0, z0, x1, y1, z1, c, force)


def plant_model():
    return Model((160, 120, 70))


PLANT_LAYERS = {'body': '主屋、存貨棚與院子', 'roof': '屋頂', 'gallery': '木廊', 'work': '作業區'}
PLANT_SHARE = {'body': 'plantation', 'roof': 'plantation', 'gallery': 'plantation'}


def plant_work_ground(M, salt):
    ground(M, 2, WORK_Y, 158, 118, salt, 'work')


def plantation():
    """種植園（基礎款）：主屋、存貨棚、院子；後院一座開敞的工具棚、柴堆、一台牛車。"""
    M = plant_base(plant_model())
    plant_work_ground(M, 9210)
    open_shed(M, 10, 74, 70, 100, 20, 9211, roof='shingle')
    trestle_table(_Shift(M, 1), 20, 50, 84, 90, 8, layer='work')
    for x in range(90, 130):
        for y in range(104, 112):
            for z in range(1, 9):
                M.put('work', x, y, z, LOG_TIP if x in (90, 129) and (y + z) % 3 else LOG)
    cart(M, 130, 74)
    return {'key': 'plantation', 'title': '種植園（共用：架高的木板主屋與木廊、存貨棚、院子與水井；後院工具棚、柴堆、牛車）', 'use': 'plantation', 'lot': (16, 12), 'M': M,
            'style': 'common', 'layers': PLANT_LAYERS}


def plant_tobacco():
    """菸草園：後院一座高的烤菸棚（tobacco barn：木板牆留縫、裡面一層一層的橫桿掛滿菸葉，下層綠、上層烤成褐）、
    院子裡一排曬菸的架、捲好的菸捲堆在桶旁。"""
    M = plant_base(plant_model())
    plant_work_ground(M, 9220)
    X0, Y0, X1, Y1 = 10, 72, 80, 112
    for (x, y) in [(x, y) for x in range(X0, X1 - 1, 10) for y in (Y0, Y1 - 2)] + [(X1 - 2, Y0), (X1 - 2, Y1 - 2)]:
        M.box('work', x, y, 1, x + 2, y + 2, 40, FRAME)
    for z in range(1, 40):                                                        # 板牆留縫（每兩塊空一道）
        for x in range(X0, X1):
            for y in (Y0, Y1 - 1):
                if (x // 3) % 3 != 2 or (x - X0) % 4 == 0:                       # 橫桿插進去的那一欄不留縫
                    M.put('work', x, y, z, BOARD if z % 3 else BOARD_D)
        for y in range(Y0, Y1):
            for x in (X0, X1 - 1):
                if (y // 3) % 3 != 2:
                    M.put('work', x, y, z, BOARD if z % 3 else BOARD_D)
    for k, z in enumerate(range(10, 38, 7)):                                     # 一層一層的橫桿（兩端插進板牆）、掛的菸葉
        for x in range(X0 + 4, X1 - 4, 4):
            M.box('work', x, Y0, z, x + 1, Y1, z + 1, FRAME, True)
            for y in range(Y0 + 2, Y1 - 2, 2):
                M.box('work', x, y, z - 4, x + 1, y + 1, z, LEAF_G if k == 0 else LEAF_B)
    for xa in (X0, X1 - 1):                                                     # 兩端的山牆板
        end_gable(M, xa, xa + 1, Y0, Y1, 40, 0.6, z0=40, layer='work')
    F = roof_field([{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 40, 'p': 0.6, 'over': (2, 2, 3, 3), 'gable': 'x'}])
    build_roof(M, F, 2, 'work', color_fn=lambda x, y, f, r, e: shingle_color(x, y, f, r, e, 9221), force=False)
    for x in (96, 140):                                                          # 曬菸的架
        M.box('work', x, 80, 1, x + 2, 82, 20, FRAME)
    M.box('work', 96, 80, 20, 142, 82, 21, FRAME)
    for x in range(99, 139, 3):
        M.box('work', x, 80, 12, x + 1, 82, 20, LEAF_G if x % 2 else LEAF_B)
    for (x, y) in ((100, 98), (110, 98), (105, 104)):                            # 捲好的菸捲（rolls）
        for xx in range(x - 3, x + 4):
            for zz in range(1, 8):
                if math.hypot(xx + 0.5 - x, zz - 4) <= 3.2:
                    M.box('work', xx, y, zz, xx + 1, y + 6, zz + 1, LEAF_B if (xx + zz) % 3 else 68)
    return {'key': 'plantation-tobacco', 'title': '菸草園（種植園：留縫的高烤菸棚與掛滿的菸葉、曬菸的架、菸捲）', 'use': 'plantation', 'lot': (16, 12), 'M': M,
            'style': 'common', 'layers': PLANT_LAYERS, 'share': PLANT_SHARE, 'variant': 'b', 'meta': {'recipes': 'tobacco'}}


def plant_indigo():
    """靛藍工坊（indigoterie）：後院三個一級比一級低的毛石池 —— 浸泡池（trempoire，泡著葉子的綠水）、打池（batterie，深藍、一根打水的木槳）、
    沉澱池（reposoir，最低、底下一層藍泥）；旁邊茅草棚下的木箱裡晾著切好的靛藍塊、一堆泡過的葉渣。"""
    M = plant_base(plant_model())
    plant_work_ground(M, 9230)
    for (x0, h, fill) in ((10, 16, CABBAGE_D), (42, 12, INDIGO_W), (70, 8, INDIGO_W)):
        stone_block(_Shift(M, 1), x0, 76, 0, x0 + 26, 106, h, salt=9231 + x0, layer='work')
        M.clear(x0 + 3, 79, h - 4, x0 + 23, 103, h + 2, 'work')                   # 池裡（石塊的頂 z h；水面低一格）
        M.box('work', x0 + 3, 79, h - 4, x0 + 23, 103, h - 1, INDIGO_C if h == 8 else DARK)   # 池底：沉澱池是一層藍泥
        M.box('work', x0 + 3, 79, h - 1, x0 + 23, 103, h, fill)
    rope_line(M, (55, 90, 11), (55, 96, 25), color=FRAME, layer='work')       # 打池的木槳（斜靠、六連通）
    open_shed(M, 104, 74, 152, 100, 18, 9235)
    for x in range(108, 148, 10):                                                # 晾靛藍塊的木箱
        M.box('work', x, 80, 1, x + 8, 92, 4, BOARD)
        for xx in range(x + 1, x + 7, 2):
            for yy in range(81, 91, 2):
                M.put('work', xx, yy, 4, INDIGO_C)
    heap(_Shift(M, 1), 124, 108, 14, 6, 6, lambda x, y, z: CABBAGE_D if (x + z) % 3 else 108, layer='work')
    return {'key': 'plantation-indigo', 'title': '靛藍工坊（種植園：浸泡、打、沉澱三個毛石池、晾靛藍塊的棚）', 'use': 'plantation', 'lot': (16, 12), 'M': M,
            'style': 'common', 'layers': PLANT_LAYERS, 'share': PLANT_SHARE, 'variant': 'c', 'meta': {'recipes': 'indigo'}}


def cane_bundle(M, x0, y0, n=24, layer='work'):
    """一捆甘蔗（沿 x、長 n、截面 4 × 4、中間一道綁繩、切口淺）。"""
    for x in range(x0, x0 + n):
        for y in range(y0, y0 + 4):
            for z in range(1, 5):
                M.put(layer, x, y, z, ROPE if x == x0 + n // 2 else (CANE_T if x in (x0, x0 + n - 1) else CANE))


def plant_cane():
    """甘蔗的種植園：後院一排排砍好綁好的甘蔗捆（等著送糖廠）、一台裝滿甘蔗的牛車、砍蔗刀架、一堆蔗葉。"""
    M = plant_base(plant_model())
    plant_work_ground(M, 9240)
    for r, y in enumerate(range(76, 108, 6)):
        for k in range(3):
            cane_bundle(M, 10 + k * 28 + (r % 2) * 6, y)
            if r < 4:
                cane_bundle(_Shift(M, 4), 12 + k * 28 + (r % 2) * 6, y + 1, 20)
    cart(M, 120, 76, load=lambda M2, x, y, z: [cane_bundle(_Shift(M2, z + 3 * j - 1), x, y + 4 * i, 10) for j in range(2) for i in range(4)])
    heap(_Shift(M, 1), 136, 108, 14, 6, 5, lambda x, y, z: CANE_T if (x + y) % 3 else CABBAGE_D, layer='work')
    M.box('work', 104, 106, 1, 106, 108, 14, FRAME)                               # 刀架
    M.box('work', 104, 106, 14, 116, 108, 15, FRAME)
    for x in range(107, 115, 3):
        M.box('work', x, 106, 8, x + 1, 107, 14, IRON)
    return {'key': 'plantation-cane', 'title': '甘蔗園（種植園：一排排綁好的甘蔗捆、裝滿甘蔗的牛車、蔗葉堆）', 'use': 'plantation', 'lot': (16, 12), 'M': M,
            'style': 'common', 'layers': PLANT_LAYERS, 'share': PLANT_SHARE, 'variant': 'd', 'meta': {'recipes': 'cane'}}


def plant_cotton():
    """棉花的種植園：後院架高的曬棉台（木架上攤開的白棉）、一座茅草棚下挑籽的長桌與一台手搖軋棉機、一排紮好的棉包、裝棉的籃。"""
    M = plant_base(plant_model())
    plant_work_ground(M, 9250)
    for x0 in (10, 48):                                                          # 兩座曬棉台
        for (x, y) in ((x0, 76), (x0 + 32, 76), (x0, 104), (x0 + 32, 104)):
            M.box('work', x, y, 1, x + 2, y + 2, 8, FRAME)
        M.box('work', x0, 76, 8, x0 + 34, 106, 9, BOARD)
        for x in range(x0 + 1, x0 + 33):
            for y in range(77, 105):
                if h01('ct', x // 2, y // 2) < 0.75:
                    M.box('work', x, y, 9, x + 1, y + 1, 10 + (1 if (x + y) % 5 == 0 else 0), COTTON)
    open_shed(M, 96, 72, 152, 96, 18, 9251)
    trestle_table(_Shift(M, 1), 100, 130, 80, 86, 8, layer='work')
    for x in range(102, 128, 4):
        M.box('work', x, 81, 10, x + 2, 85, 11, COTTON)
    M.box('work', 136, 78, 1, 146, 88, 10, FRAME)                                 # 軋棉機（木框、兩根輥、搖把）
    M.box('work', 137, 80, 10, 145, 81, 12, LOG)
    M.box('work', 137, 83, 10, 145, 84, 12, LOG)
    M.box('work', 146, 81, 9, 148, 82, 14, FRAME)
    for i in range(5):                                                           # 紮好的棉包
        x = 98 + i * 10
        M.box('work', x, 104, 1, x + 8, 112, 9, SACKC)
        for xx in (x + 2, x + 5):
            M.box('work', xx, 104, 1, xx + 1, 112, 9, ROPE, True)
    basket(M, 90, 100, COTTON)
    basket(M, 90, 110, COTTON)
    return {'key': 'plantation-cotton', 'title': '棉花園（種植園：架高的曬棉台、挑籽桌與軋棉機、紮好的棉包）', 'use': 'plantation', 'lot': (16, 12), 'M': M,
            'style': 'common', 'layers': PLANT_LAYERS, 'share': PLANT_SHARE, 'variant': 'e', 'meta': {'recipes': 'cotton'}}


def plant_cocoa():
    """可可的種植園：後院架高的曬豆台（boucan：木台上攤一層褐的可可豆，台邊的軌道上一片可以推過來蓋的木瓦活動頂）、
    發酵的木箱（蓋著蕉葉）、一堆剖開前的紅橙果莢、剖莢的砧板與刀。"""
    M = plant_base(plant_model())
    plant_work_ground(M, 9260)
    X0, X1, Y0, Y1 = 10, 90, 78, 106
    for x in range(X0, X1 - 1, 16):
        for y in (Y0, Y1 - 2):
            M.box('work', x, y, 1, x + 2, y + 2, 10, FRAME)
    M.box('work', X0, Y0, 10, X1, Y1, 11, BOARD)
    for x in range(X0 + 1, X1 - 1):                                              # 豆子（一層，用木耙耙出一道一道）
        for y in range(Y0 + 1, Y1 - 1):
            M.put('work', x, y, 11, BEAN if (y // 2) % 3 else 68)
    for x in range(X1, 150):                                                     # 活動頂的軌道（往右延伸，頂推開停在右邊）
        for y in (Y0, Y1 - 2):
            if (x - X1) % 16 == 0:
                M.box('work', x, y, 1, x + 2, y + 2, 10, FRAME)
            M.box('work', x, y, 10, x + 1, y + 2, 11, FRAME)
    for x in range(96, 148):                                                     # 推開的活動頂（木瓦、平的微坡）
        for y in range(Y0 - 1, Y1 + 1):
            M.put('work', x, y, 14, shingle_color(x, y, 'front', False, y in (Y0 - 1, Y1), 9261))
            if y % 8 == 0:
                M.put('work', x, y, 15, SHINGLE_R)                                  # 每 0.8 m 一道壓條
        if (x - 96) % 12 == 0:
            for y in (Y0, Y1 - 2):
                M.box('work', x, y, 11, x + 1, y + 2, 14, FRAME)
    for i in range(3):                                                           # 發酵箱（蓋著綠的蕉葉）
        x = 14 + i * 16
        M.box('work', x, 110, 1, x + 12, 117, 8, BOARD)
        M.box('work', x, 110, 8, x + 12, 117, 9, CABBAGE)
    heap(_Shift(M, 1), 116, 110, 10, 6, 6, lambda x, y, z: POD if (x + y + z) % 4 else CABBAGE_D, layer='work')
    M.box('work', 134, 108, 1, 142, 114, 6, LOG)                                   # 剖莢的砧
    M.box('work', 136, 110, 6, 141, 111, 7, IRON)
    return {'key': 'plantation-cocoa', 'title': '可可園（種植園：架高的曬豆台與推開的活動頂、發酵箱、可可果莢）', 'use': 'plantation', 'lot': (16, 12), 'M': M,
            'style': 'common', 'layers': PLANT_LAYERS, 'share': PLANT_SHARE, 'variant': 'f', 'meta': {'recipes': 'cocoa'}}


ALL = [farm, farm_grain, farm_maize, farm_vegetables, farm_cassava, plantation, plant_tobacco, plant_indigo, plant_cane, plant_cotton, plant_cocoa]
