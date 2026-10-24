# 小地塊的建築（Tim 2026-10-24「接著修和平港、皇家港疊在一起的房子」；Blocksail tools/town_foot.cjs 量到的房子互疊）
#   和平港 1686（carib）：照 Cornuau 的圖量的房子只有 4～15 × 4～6 m（地塊 ＝ 圖上的屋子），最小的住宅模型是 8 × 8 ⇒ 遊戲照舊擺 8 × 12 的房子、溢到隔壁。
#     ⇒ 一套小木屋（case）：寬 4、5、6、7、8、10、12 m × 深 4、5 m，兩型 —— a 木板牆＋木瓦四坡頂、b 編條糊泥刷白＋棕櫚茅草四坡頂（17 世紀法屬安地列斯的兩種作法，summit-carib-01m 的史料）；
#     另外小倉庫 12 × 4、小砲台 6 × 4、小酒館 12 × 6、小教堂 12 × 5（和平港那幾塊的地塊）。
#   皇家港 1692（en）：21 間酒館的地塊是 8 × 12，酒館模型（fr）10 × 14 ⇒ 疊到兩邊的住宅 ⇒ 英國磚造的兩層酒館 8 × 12。
# 工具照 ame-carib-civic-01m/design（civic ⇒ summit-carib-01m 的調色盤、Model、牆、屋頂、部件；english 的磚牆、紅陶瓦）⇒ 不另抄一份；部件全部借（關聯指回原作品）。
# 座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框（鄰居只隔 2 cm）。
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
WORKS = os.path.dirname(os.path.dirname(HERE))
AME = os.path.join(WORKS, 'ame-carib-civic-01m', 'design')
if AME not in sys.path:
    sys.path.insert(0, AME)
from civic import *                                   # noqa: E402,F401,F403  carib 的調色盤、Model、board_walls、daub_walls、rubble_walls、shingle_roof、thatch_roof、put_part、free_part
import civic as _CV                                   # noqa: E402
import english as EN                                  # noqa: E402
from public import GUN, GUN_PIVOT                     # noqa: E402
from townpub import end_gable                         # noqa: E402

_CV._borrow_fr('window', 'chimney')                    # 英國酒館的玻璃窗、煙囪（同 ame 的英國那一套）
BARREL = 'summit-rocher-01m-barrel'
SIGN = 100                                             # 招牌板（牛血紅漆）


def barrel(M, name, x, y):
    M.models.append({'name': name, 'source': BARREL, 'at': [x, y, 0], 'pivot': [6, 6, 0], 'meta': {}})


# ─────────────────────────────── 小木屋 case（W × D m） ───────────────────────────────
CABIN_W = (4, 5, 6, 7, 8, 10, 12)
CABIN_D = (4, 5)


def cabin(W, D, kind):
    """小木屋：一間、平房；a 木板牆（四角叉柱）＋木瓦四坡頂、b 編條糊泥刷白（露柱）＋棕櫚茅草四坡頂（陡一點）。
    門窗照寬擺：4 m 只有門（窗開在右牆）、5～7 m 一門一窗、8 m 起一門兩窗；背面一扇窗。地塊就是屋子（圖上量的），屋簷收在框裡。"""
    X, Y = W * 10, D * 10
    M = Model((X, Y, 72))
    X0, Y0, X1, Y1 = 3, 5, X - 3, Y - 3
    R = (X0, Y0, X1, Y1)
    h = 27                                                              # 門 2.3 m ⇒ 簷口在門楣上（townpub.small_house 同）
    if kind == 'a':
        t = 2
        board_walls(M, R, 0, h, t)
        roof = shingle_roof
        p = 0.8
    else:
        t = 3
        daub_walls(M, R, 0, h, t)
        roof = thatch_roof
        p = 1.0
    span = X1 - X0
    if W <= 4:
        dc, wins = X0 + span // 2, []
        put_part(M, 'window-board', '右-窗', 'right', R, (Y0 + Y1) // 2, 10, t)
    elif W <= 7:
        dc, wins = X0 + 10, [X1 - 14]
    else:
        dc, wins = X0 + span // 2, [X0 + span // 4 - 1, X1 - span // 4 + 1]
    put_part(M, 'door-plank', '前-門', 'front', R, dc, 0, t)
    for i, cx in enumerate(wins):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, 10, t)
    put_part(M, 'window-board', '後-窗', 'back', R, X0 + span // 2, 10, t)
    roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': h, 'p': p, 'over': (3, 3, 4, 3)}], salt=W * 10 + D + (0 if kind == 'a' else 500))
    M.anchor('door', dc, Y0 - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    look = '木板牆、木瓦頂' if kind == 'a' else '編條糊泥刷白、棕櫚茅草頂'
    return {'key': 'cabin-%dx%d-%s' % (W, D, kind), 'variant': '%dx%d-%s' % (W, D, kind), 'style': 'carib', 'use': 'house', 'lot': (W, D), 'M': M,
            'title': '小木屋 %d × %d m（case；%s；平房一間、%s）' % (W, D, kind, look), 'layers': {'body': '牆身', 'roof': '屋頂'}}


# ─────────────────────────────── 和平港的其他小建築 ───────────────────────────────
def warehouse_s():
    """小倉庫 12 × 4：一長間木板牆的貨棚、兩坡木瓦頂（屋脊沿街）、兩端山牆；正面雙扇門＋兩扇氣窗。和平港岸邊那幾間（15 × 4～16 × 6）。"""
    M = Model((120, 40, 70))
    X0, Y0, X1, Y1 = 3, 5, 117, 37
    R = (X0, Y0, X1, Y1)
    h = 30
    board_walls(M, R, 0, h, 2, bay=26)
    p = 0.6
    for (a, b) in ((X0, X0 + 2), (X1 - 2, X1)):
        end_gable(M, a, b, Y0, Y1, h, p)
    put_part(M, 'door-double', '前-門', 'front', R, 60, 0, 2)
    for i, cx in enumerate((25, 95)):
        put_part(M, 'vent', '前-氣窗%d' % (i + 1), 'front', R, cx, 14, 2)
    shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': h, 'p': p, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=901)
    M.anchor('door', 60, Y0 - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'warehouse-s', 'variant': 's', 'style': 'carib', 'use': 'warehouse', 'lot': (12, 4), 'M': M,
            'title': '小倉庫 12 × 4 m（木板牆的貨棚、兩坡木瓦頂；雙扇門、兩扇氣窗）', 'layers': {'body': '牆身', 'roof': '屋頂'}}


def battery_s():
    """小砲台 6 × 4：一門砲（風暴角號 6 磅長砲）擺在木板平台上、前面一道毛石胸牆開一個砲眼；兩側矮木柵。和平港岸邊那幾座（6～8 × 4）。"""
    M = Model((60, 40, 30))
    M.box('body', 2, 12, 0, 58, 38, 2, FLOOR)                           # 平台
    M.box('body', 2, 2, 0, 58, 12, 12, RUBBLE)                          # 胸牆
    for x in range(2, 58):
        for z in range(0, 12):
            if (x + z) % 7 == 0 or z % 4 == 3:
                M.put('body', x, 2, z, MORTAR, force=True)
    M.clear(23, 2, 6, 37, 12, 12)                                       # 砲眼
    palisade(M, [(2, 12), (2, 37)], h=10)
    palisade(M, [(57, 12), (57, 37)], h=10)
    M.models.append({'name': '砲', 'source': GUN, 'at': [30, 24, 2], 'pivot': GUN_PIVOT, 'rotate': [0, 0, 180], 'meta': {'kind': 'deco'}})
    M.anchor('door', 30, 36, 2)                                         # 從後面上平台
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'battery-s', 'variant': 's', 'style': 'carib', 'use': 'battery', 'lot': (6, 4), 'M': M,
            'title': '小砲台 6 × 4 m（毛石胸牆一個砲眼、木板平台、一門 6 磅砲、兩側矮木柵）', 'layers': {'body': '胸牆與平台'}}


def tavern_s():
    """小酒館 12 × 6：木板牆一間、前面通長的外廊（柱立到屋簷）、四坡木瓦頂蓋過外廊；雙扇門、兩扇窗；廊柱上掛一塊招牌。和平港 pdp-ma4（19 × 7）。"""
    M = Model((120, 60, 80))
    X0, Y0, X1, Y1 = 3, 16, 117, 57
    R = (X0, Y0, X1, Y1)
    h = 31                                                              # 門在外廊地板上（z 2）、雙扇門高 2.7 m ⇒ 前簷要在 2.9 m 以上
    board_walls(M, R, 0, h, 2, bay=26)
    M.box('gallery', X0, 5, 0, X1, Y0 - 1, 2, FLOOR)                    # 外廊地板（停在牆前一格：門窗部件的外框在那一格）
    put_part(M, 'door-double', '前-門', 'front', R, 60, 2, 2)              # 門窗照外廊地板的高（0.2 m）
    for i, cx in enumerate((24, 96)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, 12, 2)
    put_part(M, 'door-plank', '後-門', 'back', R, 30, 0, 2)
    top = shingle_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': h, 'p': 0.7, 'over': (3, 3, 13, 3)}], salt=902)
    gallery_posts(M, (X0, 40, 78, X1 - 2), 5, 2, top)                  # 廊柱立到屋面底下
    M.box('gallery', 42, 4, 16, 43, 5, 24, IRON)                        # 招牌：廊柱上伸出一根鐵桿、掛一塊板
    M.box('gallery', 43, 4, 23, 52, 5, 24, IRON)
    M.box('gallery', 44, 4, 15, 52, 5, 22, SIGN)
    M.anchor('door', 60, Y0 - 2, 2)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'tavern-s', 'variant': 's', 'style': 'carib', 'use': 'tavern', 'lot': (12, 6), 'M': M,
            'title': '小酒館 12 × 6 m（木板牆、前面通長外廊、四坡木瓦頂；雙扇門、兩扇窗、廊下一塊招牌）', 'layers': {'body': '牆身', 'gallery': '外廊', 'roof': '屋頂'}}


def chapel_s():
    """小教堂 12 × 5：編條糊泥刷白的一間、兩坡茅草頂（屋脊沿街）、兩端山牆；正面雙扇門、兩扇欄杆窗；屋脊正中一座木鐘架（銅鐘）、頂上一支十字架。和平港的 chapelle（13 × 5）。"""
    M = Model((120, 50, 100))
    X0, Y0, X1, Y1 = 3, 6, 117, 47
    R = (X0, Y0, X1, Y1)
    h = 34
    daub_walls(M, R, 0, h, 3)
    p = 0.9
    for (a, b) in ((X0, X0 + 3), (X1 - 3, X1)):
        end_gable(M, a, b, Y0, Y1, h, p, color=LIME)
    put_part(M, 'door-double', '前-門', 'front', R, 60, 0, 3)
    for i, cx in enumerate((26, 94)):
        put_part(M, 'window-baluster', '前-窗%d' % (i + 1), 'front', R, cx, 12, 3)
    top = thatch_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': h, 'p': p, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=903)
    yc = (Y0 + Y1) // 2
    zr = top[(60, yc)]
    for (x, y) in ((54, yc - 4), (64, yc - 4), (54, yc + 2), (64, yc + 2)):   # 鐘架四根柱
        M.box('body', x, y, zr - 2, x + 2, y + 2, zr + 14, FRAME, force=True)
    M.box('body', 54, yc - 4, zr + 14, 66, yc + 4, zr + 16, FRAME, force=True)
    for x in range(56, 64):                                             # 銅鐘
        for y in range(yc - 2, yc + 2):
            for z in range(zr + 5, zr + 13):
                r = (z - zr - 5) / 8.0
                if abs(x + 0.5 - 60) <= 1.5 + 2.5 * r and abs(y + 0.5 - yc) <= 1.5 + 0.5 * r:
                    M.put('body', x, y, z, BRONZE, force=True)
    M.box('body', 59, yc - 1, zr + 13, 61, yc + 1, zr + 14, IRON, force=True)    # 鐘吊在橫梁上
    M.box('body', 59, yc - 1, zr + 16, 61, yc + 1, zr + 28, FRAME, force=True)   # 十字架
    M.box('body', 55, yc - 1, zr + 22, 65, yc + 1, zr + 24, FRAME, force=True)
    M.anchor('door', 60, Y0 - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'chapel-s', 'variant': 's', 'style': 'carib', 'use': 'church', 'lot': (12, 5), 'M': M,
            'title': '小教堂 12 × 5 m（編條糊泥刷白、兩坡茅草頂；雙扇門、兩扇欄杆窗；屋脊上一座木鐘架與十字架）', 'layers': {'body': '牆身與鐘架', 'roof': '屋頂'}}


# ─────────────────────────────── 皇家港的英國酒館 8 × 12 ───────────────────────────────
def en_tavern():
    """英國磚造的酒館 8 × 12：兩層磚牆、紅陶瓦四坡頂、煙囪；一樓雙扇門＋兩扇玻璃窗、二樓三扇；門邊鐵臂吊一塊招牌；後院磚院牆、後門、酒桶。
    皇家港 1692 年前「每十個人一間酒館」那一排（High St、Thames St）〔史料見 ame-carib-civic-01m references/research_civic.md §10〕；樣子照 ame 的英國那一套（磚、瓦、兩層）。"""
    M = Model((80, 120, 105))                                           # 煙囪（fr 部件 4 m 高）從簷下 z 58 起 ⇒ 頂到 98
    X0, Y0, X1, Y1 = 3, 10, 77, 72
    R = (X0, Y0, X1, Y1)
    EN.brick_walls(M, R, 0, 31, 4, salt=71)
    M.box('body', X0 + 4, Y0 + 4, 29, X1 - 4, Y1 - 4, 31, FLOOR)
    EN.brick_walls(M, R, 31, 60, 4, salt=72)
    put_part(M, 'door-double', '前-門', 'front', R, 40, 0, 4)
    for i, cx in enumerate((16, 64)):
        put_part(M, 'window', '前-窗%d' % (i + 1), 'front', R, cx, 9, 4)
    for i, cx in enumerate((16, 40, 64)):
        put_part(M, 'window', '二樓-窗%d' % (i + 1), 'front', R, cx, 38, 4)
    put_part(M, 'door-plank', '後-門', 'back', R, 26, 0, 4)
    for i, cx in enumerate((20, 60)):
        put_part(M, 'window', '後-二樓窗%d' % (i + 1), 'back', R, cx, 38, 4)
    top = EN.tile_roof(M, [{'x0': X0, 'y0': Y0, 'x1': X1, 'y1': Y1, 'ze': 60, 'p': 0.6, 'over': (3, 3, 4, 4)}], salt=73)
    free_part(M, 'chimney', '煙囪', (60, 52, 58))
    M.box('body', 8, 9, 34, 9, 10, 36, IRON)                            # 招牌：牆上伸出鐵臂、吊一塊板（在門左上）
    M.box('body', 8, 3, 34, 9, 9, 35, IRON)
    M.box('body', 8, 3, 25, 9, 9, 34, SIGN)                             # 板頂接到鐵臂（z 34）
    for (a, b, c, d) in ((X0, Y1, X0 + 3, 117), (X1 - 3, Y1, X1, 117), (X0, 114, X1, 117)):   # 後院磚牆
        EN.brick_walls(M, (a, b, c, d), 0, 20, 3, salt=74)
    M.clear(50, 114, 0, 64, 117, 18)
    M.box('body', 50, 115, 0, 64, 116, 17, SHUT)
    for i, (x, y) in enumerate(((10, 84), (10, 92), (20, 84), (60, 96))):
        barrel(M, '酒桶-院%d' % (i + 1), x, y)
    M.anchor('door', 40, Y0 - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'en-tavern', 'variant': 'a', 'style': 'en', 'use': 'tavern', 'lot': (8, 12), 'M': M,
            'title': '英國磚造的酒館 8 × 12 m（兩層磚牆、紅陶瓦四坡頂、煙囪；雙扇門、玻璃窗、門邊鐵臂招牌；後院磚院牆、酒桶）', 'layers': {'body': '牆身', 'roof': '屋頂'}}


ALL = [lambda w=w, d=d, k=k: cabin(w, d, k) for d in CABIN_D for w in CABIN_W for k in 'ab'] + [warehouse_s, battery_s, tavern_s, chapel_s, en_tavern]
