# 港口配套第八批（TASK-0888；Tim 2026-10-24「把6座城的港口都擺上港口設施 可以參考海商王 Anno系列 以及現實港口（17世紀左右）…也可以加上更多港口建築」）
#   船具行（chandlery）、港務所（harbour-office）—— 共用 common，生成器照規模補（鎮、城起）；
#   海軍倉庫（naval-store，英國 en）、海龜圍欄（turtle-crawl，common）、商人廊廳（loggia，熱那亞 genoa）、港邊倉庫列（emporion，羅馬 roman）—— 只照史料擺在那幾座城。
# 工具照 trailhead-harbour-01m/design（quay.py ⇒ ame-carib-civic-01m 的 harbour／civic／english ⇒ summit-carib-01m 的調色盤、Model、屋頂、部件）⇒ 不另抄一份。
# 座標同 kit.py：x 臨路寬（從碼頭看左 → 右）、y 進深（y 0 朝碼頭）、z 往上（z 0 整平面）；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料（研究 2026-10-24，kaguya 的暫存；重點抄在 Blocksail TOWN_BUILD §1.1.7）：
#   Port Royal：皇家海軍 1675 年起派駐官員、在前灘租一間倉庫；海龜在 High St 的市場賣、養在港內的方形木柵（Wikipedia Port Royal、ame research_civic.md §10.4）
#   Galata：1316 年碑文，podestà 重建公署、市場、loggia、醫院、過磅所（thebyzantinelegacy.com Galata slabs）；熱那亞的石牆黑白相間（Genoa 的 San Lorenzo、Palazzo San Giorgio）
#   Constantinople：巴列奧略王朝的港區四周「許多倉庫」、Sirkeci 挖到過倉庫遺址（Wikipedia Neorion Harbour、Prosphorion Harbour）
#   船具行、港務所：海商王、Anno 1800（Harbourmaster's Office）都有；17 世紀的具體樣子〔沒查到〕⇒ 設計
import os, sys, math
from quay import *                                                     # noqa: F401,F403  繩、圓材、滑車、繫纜樁 ＋ harbour／civic／carib 的全部
import english                                                         # noqa: E402  磚牆、紅陶瓦、大橫桿秤（英國那一套）
from townpub import trestle_table, bench                               # noqa: E402
from town3 import lantern, SHELL, SHELL_D                              # noqa: E402
from workshops import roof_posts, SACK                                 # noqa: E402

CLOTH = 218                      # 帆布（米白）
FLAG_R, FLAG_W = 160, 255        # 旗：紅、白
WATER7 = 46                      # 圍欄裡的水面（同 civic 的泉水）
BELLY = 177                      # 翻過來的海龜肚子（淡黃）
SAND = 213                       # 沙
GEN_D, GEN_W = 73, 255           # 熱那亞黑白相間的石帶：深灰石板、白大理石
LIME_R, LIME_G, BRICK_R, BRICK_RM = 218, 182, 168, 205   # 羅馬那一套：石灰岩方石（米白、灰米）、紅磚、磚帶的粉紅厚灰漿（同 kaguya-roman-1453 rkit）
AMPH = 136                       # 陶罐（赤陶）


def barrel(M, name, x, y, z=0):
    M.models.append({'name': name, 'source': 'summit-rocher-01m-barrel', 'at': [x, y, z], 'pivot': [6, 6, 0], 'meta': {}})


def crate(M, name, x, y, z=0):
    M.models.append({'name': name, 'source': 'summit-rocher-01m-crate', 'at': [x, y, z], 'pivot': [6, 6, 0], 'meta': {}})


def goods(M, tag, items):
    """碼頭擺設（Tim 2026-10-25「碼頭擺設目前想法是做到碼頭相關建築內 而不是直接擺上去」）：[(種類, x, y, z)]，種類 'c' 貨箱、'b' 木桶。"""
    for i, (k, x, y, z) in enumerate(items):
        (crate if k == 'c' else barrel)(M, '%s-%s-%d' % (tag, '貨箱' if k == 'c' else '桶', i + 1), x, y, z)


def sacks(M, x0, y0, n=3, layer='body'):
    """一堆貨袋（每袋 0.7 × 0.6 × 0.6 m；第三袋疊在前兩袋上）。"""
    for i in range(n):
        x, y, z = (x0 + 8 * (i % 2), y0, 0) if i < 2 else (x0 + 4, y0, 6)
        M.box(layer, x, y, z, x + 7, y + 6, z + 6, SACK)


def anchor_prop(M, x0, y0, layer='body'):
    """靠牆躺的鐵錨（長 2.4 m）：錨桿沿 y 躺在地上、錨冠兩爪往上翹、頂上一根木橫桿（stock）。"""
    M.box(layer, x0, y0, 0, x0 + 2, y0 + 24, 2, IRON)                  # 錨桿
    for k in range(6):                                                  # 兩爪（沿 x 往兩邊、往上）
        M.box(layer, x0 - 1 - k, y0 + k, k // 2, x0, y0 + k + 1, k // 2 + 2, IRON)
        M.box(layer, x0 + 2, y0 + k, k // 2, x0 + 3 + k, y0 + k + 1, k // 2 + 2, IRON)
    M.box(layer, x0 - 7, y0 + 21, 0, x0 + 9, y0 + 23, 3, FRAME)        # 木橫桿
    M.box(layer, x0, y0 + 24, 0, x0 + 2, y0 + 27, 2, IRON)             # 錨環那一頭


def shot_pile(M, x0, y0, n=4, layer='body'):
    """砲彈堆成金字塔（每顆 2 × 2 × 2 格）。"""
    for k in range(n):
        for i in range(n - k):
            for j in range(n - k):
                M.box(layer, x0 + 2 * i + k, y0 + 2 * j + k, 2 * k, x0 + 2 * i + k + 2, y0 + 2 * j + k + 2, 2 * k + 2, IRON)


def arch_open(M, axis, plane0, plane1, c, hw, spring, z0=0, layer=None):
    """在牆上挖一個半圓拱的開口：axis 'x' ⇒ 牆沿 x（開口跨 x ∈ [c − hw, c + hw)、牆厚 y ∈ [plane0, plane1)）；'y' ⇒ 牆沿 y。"""
    for u in range(c - hw, c + hw):
        du = u + 0.5 - c
        zt = spring + int(math.floor(math.sqrt(max(0.0, hw * hw - du * du))))
        if axis == 'x':
            M.clear(u, plane0, z0, u + 1, plane1, zt, layer)
        else:
            M.clear(plane0, u, z0, plane1, u + 1, zt, layer)


def banded_walls(M, rect, z0, z1, t, fn, layer='body'):
    """照 fn(x, y, z) 給色的牆（外框 rect、厚 t）。"""
    X0, Y0, X1, Y1 = rect
    for z in range(z0, z1):
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                if X0 + t <= x < X1 - t and Y0 + t <= y < Y1 - t:
                    continue
                M.put(layer, x, y, z, fn(x, y, z))


# ─────────────────────────────── 船具行 10 × 14 m ───────────────────────────────
def chandlery():
    """船具行兼帆布閣樓（chandlery）：一樓毛石的店面（雙扇門、兩扇窗），二樓木板牆、兩側一排窗 —— 縫帆的閣樓要光；
    山牆朝碼頭、山尖下伸出一根吊貨梁（滑車、繩垂到門口的貨箱）；右邊一條窄院子堆桶、靠牆躺一支錨、立著一捆槳；後院一堆圓材、兩盤繩。
    - 前院（2026-10-25 碼頭擺設做進建築裡）：店面往後退到 y 2.2 m ⇒ 臨碼頭空出一條院子：左邊疊貨箱、門旁一盤繩、右邊兩個桶。
    - 照什麼：海商王的港口都有賣船具的、Anno 的倉儲；17 世紀加勒比海的船具行樣子〔沒查到〕⇒ 設計。吊貨梁照阿姆斯特丹倉庫山尖的 hijsbalk（作法通用）。"""
    X, Y, Z = 100, 140, 96
    M = Model((X, Y, Z))
    R = (4, 22, 80, 124)
    rubble(M, R, 0, 34, 4, base=RUBBLE, mortar=MORTAR, dark=RUBBLE_D, salt=8881)
    M.box('body', R[0], R[1], 34, R[2], R[3], 36, FLOOR)                # 二樓地板
    board_walls(M, R, 36, 62, 2)
    top = shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 62, 'p': 0.6, 'over': (3, 3, 3, 3), 'gable': 'y'}], salt=8882)
    for yy, face in ((R[1], 'front'), (R[3], 'back')):                  # 兩端山牆（三角）
        for x in range(R[0], R[2]):
            d = min(x + 0.5 - R[0], R[2] - x - 0.5)
            zt = int(math.floor(62 + 0.6 * d))
            ys = range(yy, yy + 2) if face == 'front' else range(yy - 2, yy)
            for z in range(62, zt):
                for y in ys:
                    M.put('body', x, y, z, BOARD_D if (z % 3 == 2) else BOARD)
    put_part(M, 'door-double', '店門', 'front', R, 42, 0, 4)
    for cx in (16, 68):
        put_part(M, 'window-board', '店窗-%d' % cx, 'front', R, cx, 10, 4)
    put_part(M, 'door-plank', '閣樓貨門', 'front', R, 42, 38, 2)       # 二樓正面的貨門（吊進帆布捲）
    for cy in range(26, 120, 22):                                       # 閣樓兩側一排窗
        put_part(M, 'window-board', '閣樓窗-左-%d' % cy, 'left', R, cy, 42, 2)
        put_part(M, 'window-board', '閣樓窗-右-%d' % cy, 'right', R, cy, 42, 2)
    for cy in (40, 96):
        put_part(M, 'window-board', '店窗-右-%d' % cy, 'right', R, cy, 10, 4)
    # 吊貨梁：從山尖下往外伸 0.8 m、梁頭吊一個滑車、繩垂到門口的貨箱
    M.box('body', 41, 0, 74, 44, R[1] + 4, 77, FRAME)
    rope_line(M, (42.5, 1.5, 72), (42.5, 1.5, 74))                       # 滑車吊在梁頭
    tackle_block(M, 42, 1, 66)
    rope_line(M, (42.5, 1.5, 66), (42.5, 1.5, 44))                       # 繩垂到樓上貨門那一層
    goods(M, '前院', [('c', 12, 7, 0), ('c', 19, 7, 0), ('c', 12, 14, 0), ('c', 15, 10, 6), ('b', 68, 12, 0), ('b', 78, 12, 0)])
    rope_coil(M, 27, 13, r=4)
    # 右邊的窄院子：桶、錨、一捆槳
    for i, (x, y, z) in enumerate(((90, 14, 0), (90, 28, 0), (90, 42, 0), (90, 14, 12))):
        barrel(M, '桶-%d' % (i + 1), x, y, z)
    anchor_prop(M, 90, 60)
    for k in range(4):                                                  # 一捆槳（靠牆立著）
        M.box('body', 82 + k * 2, 100, 0, 83 + k * 2, 101, 44, LOG)
        M.box('body', 81 + k * 2, 100, 0, 84 + k * 2, 103, 8, LOG)
    M.box('body', 81, 99, 30, 90, 101, 32, ROPE)                        # 綁槳的繩
    # 後院：圓材堆、繩盤、一捲攤開的帆布
    log_pile(M, 8, 60, 126, rows=2, d=4)
    rope_coil(M, 70, 132, r=5)
    rope_coil(M, 88, 130, r=4)
    lantern(M, '燈籠-門', (29, R[1], 24))
    M.anchor('door', 42, 3, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'chandlery', 'title': '船具行（共用：一樓毛石店面、二樓木板牆的帆布閣樓、兩側一排窗；山尖的吊貨梁與滑車；臨碼頭的前院堆貨箱、桶、繩盤；錨、一捆槳、圓材堆）',
            'use': 'chandlery', 'lot': (10, 14), 'M': M, 'style': 'common', 'layers': {'body': '牆、梁與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 港務所 8 × 8 m ───────────────────────────────
def harbour_office():
    """港務所（harbour-office）：毛石小屋（一門兩窗、木瓦四坡頂），右邊一根 11 m 的旗桿（有橫桁，掛港旗、打信號）；門口告示板、長凳、燈籠；
    屋後一個水桶。
    - 前院（2026-10-25 碼頭擺設做進建築裡）：小屋往後退 1 m ⇒ 門口右邊兩個貨箱、旗桿前一個桶；水桶挪到旗桿後面。
    - 照什麼：Anno 1800 的 Harbourmaster's Office（港口的管理處）；17 世紀加勒比海港口有沒有港務官的屋子〔沒查到〕⇒ 設計；旗桿＝港口打信號（設計）。"""
    X, Y, Z = 80, 80, 116
    M = Model((X, Y, Z))
    R = (6, 22, 58, 70)
    rubble(M, R, 0, 30, 4, base=RUBBLE, mortar=MORTAR, dark=RUBBLE_D, salt=8883)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.55, 'over': (3, 3, 3, 3)}], salt=8884)
    put_part(M, 'door-plank', '門', 'front', R, 24, 0, 4)
    put_part(M, 'window-board', '窗-右', 'right', R, 38, 10, 4)          # 正面那一段留給告示板
    put_part(M, 'window-board', '窗-左', 'left', R, 38, 10, 4)
    # 旗桿：毛石座、桿、橫桁、紅白旗
    M.box('body', 66, 26, 0, 74, 34, 4, RUBBLE)
    M.box('body', 69, 29, 4, 71, 31, 112, FRAME)
    M.box('body', 60, 29, 96, 80, 31, 98, FRAME)                        # 橫桁
    for x in range(52, 69):                                             # 旗（掛在桿上、往左飄；上紅下白）
        for z in range(100, 112):
            M.put('body', x, 30, z, FLAG_R if z >= 106 else FLAG_W)
    rope_line(M, (60.5, 30.5, 96), (67.5, 30.5, 4))                     # 橫桁的拉索（到旗桿座）
    # 告示板（門右邊）、長凳
    for x in (33, 41):
        M.box('body', x, 4, 0, x + 1, 5, 22, FRAME)
    M.box('body', 32, 4, 12, 43, 5, 21, BOARD)
    for x in range(34, 41, 2):                                          # 板上釘的告示
        M.box('body', x, 3, 14 + (x % 3), x + 1, 4, 18 + (x % 3), CLOTH)
    bench(M, 8, 20, 4, 8)
    barrel(M, '水桶', 74, 56, 0)
    goods(M, '前院', [('c', 49, 10, 0), ('c', 56, 10, 0), ('b', 66, 13, 0)])
    lantern(M, '燈籠-門', (16, R[1], 22))
    M.anchor('door', 24, 4, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'harbour-office', 'title': '港務所（共用：毛石小屋、木瓦四坡頂；11 m 的旗桿與橫桁、紅白港旗；門口告示板、長凳）',
            'use': 'harbour-office', 'lot': (8, 8), 'M': M, 'style': 'common', 'layers': {'body': '牆、旗桿與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 海軍倉庫 14 × 22 m ───────────────────────────────
def naval_store():
    """海軍倉庫（naval-store，英國那一套）：兩層磚造的長倉庫、紅陶瓦四坡頂；正面一扇大貨門、樓上的吊貨門與伸出的吊貨梁；兩側一排鐵條氣窗；
    門前兩堆砲彈、一支錨；後院一堆桅杆圓材。
    - 前院（2026-10-25 碼頭擺設做進建築裡）：倉庫往後退 1.4 m ⇒ 門前的院子：砲彈、絞盤之外，貨箱、桶、一盤纜繩、貨袋。
    - 照什麼：皇家海軍 1675 年起派駐 Port Royal、在前灘租了一間倉庫（Wikipedia Port Royal）〔讀過〕；皇家港的房子磚造、兩到四層（ame english.py 的史料）；
      倉庫本身的樣子〔沒查到〕⇒ 照英國本土的海軍倉庫（磚、規整的窗）設計。"""
    X, Y, Z = 140, 220, 104
    M = Model((X, Y, Z))
    R = (6, 26, 134, 198)
    english.brick_walls(M, R, 0, 64, 4, salt=8885)
    M.box('body', R[0] + 4, R[1] + 4, 32, R[2] - 4, R[3] - 4, 34, FLOOR)   # 二樓樓板
    english.tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 64, 'p': 0.5, 'over': (3, 3, 3, 3)}], salt=8886)
    M.box('body', R[0], R[1], 62, R[2], R[3], 64, MORTAR)               # 簷口的白石帶（磚頂一道）
    put_part(M, 'cartdoor', '大貨門', 'front', R, 70, 0, 4)
    put_part(M, 'door-plank', '樓上貨門', 'front', R, 70, 34, 4)
    M.box('body', 68, 2, 58, 72, R[1] + 4, 61, FRAME)                   # 吊貨梁（簷下伸出）
    rope_line(M, (69.5, 3.5, 56), (69.5, 3.5, 58))
    tackle_block(M, 69, 3, 50)
    rope_line(M, (69.5, 3.5, 50), (69.5, 3.5, 30))
    for cx in (28, 112):
        put_part(M, 'vent', '氣窗-前-%d' % cx, 'front', R, cx, 12, 4)
        put_part(M, 'window-board', '窗-前-%d' % cx, 'front', R, cx, 42, 4)
    for cy in range(40, 190, 30):
        for face in ('left', 'right'):
            put_part(M, 'vent', '氣窗-%s-%d' % (face, cy), face, R, cy, 12, 4)
            put_part(M, 'vent', '氣窗-%s-上-%d' % (face, cy), face, R, cy, 44, 4)
    shot_pile(M, 20, 2, 4)
    shot_pile(M, 104, 2, 4)
    capstan(M, 40, 6, bars=False)
    goods(M, '前院', [('c', 92, 8, 0), ('c', 99, 8, 0), ('c', 95, 15, 0), ('c', 95, 9, 6), ('b', 118, 12, 0), ('b', 128, 12, 0), ('b', 123, 21, 0)])
    rope_coil(M, 50, 19, r=5)
    sacks(M, 8, 15)
    log_pile(M, 10, 130, 200, rows=3, d=4)                              # 後院的桅杆圓材
    lantern(M, '燈籠-門', (90, R[1], 26))
    M.anchor('door', 70, 4, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'naval-store', 'title': '海軍倉庫（英國：兩層磚造、紅陶瓦四坡頂；大貨門、樓上吊貨門與吊貨梁、兩側鐵條氣窗；門前院子的砲彈堆、絞盤、貨箱、桶、纜繩、貨袋；桅杆圓材）',
            'use': 'naval-store', 'lot': (14, 22), 'M': M, 'style': 'en', 'layers': {'body': '牆、門窗與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 海龜圍欄 12 × 10 m ───────────────────────────────
def turtle_crawl():
    """海龜圍欄（turtle-crawl）：岸邊一個挖淺的水池、四周一圈打下去的木樁（樁與樁之間留縫、潮水進出）、正面一道木柵門和踏板；池裡五隻海龜；
    後面一座茅草的遮陽棚，棚下一張桌、一隻翻過來的海龜（等著殺）、一把秤。
    - 照什麼：皇家港的海龜從開曼運來、養在港內的方形木柵、約 2000 人每天吃龜肉（ame research_civic.md §10.4，SL、CSP）〔讀過〕；
      柵欄的構造〔17 世紀沒查到〕⇒ 照 19 世紀 Florida 的 crawl（木樁圍成、樁間留縫讓潮水進出）設計 —— 年代差一百多年，照實寫。"""
    X, Y, Z = 120, 100, 44
    M = Model((X, Y, Z))
    P = (8, 6, 112, 70)                                                 # 樁圍的範圍
    M.box('body', P[0], P[1], 0, P[2], P[3], 1, SAND)                   # 池邊的沙
    M.box('body', P[0] + 2, P[1] + 2, 0, P[2] - 2, P[3] - 2, 1, WATER7, force=True)   # 水面（池底在整平面下，看到的是水）
    for x in range(P[0], P[2], 3):                                      # 木樁（每 0.3 m 一根、1 格粗、高 1.4 m）
        for y in (P[1], P[3] - 1):
            M.box('body', x, y, 0, x + 1, y + 1, 14 + (x % 2), LOG)
    for y in range(P[1], P[3], 3):
        for x in (P[0], P[2] - 1):
            M.box('body', x, y, 0, x + 1, y + 1, 14 + (y % 2), LOG)
    for y in (P[1], P[3] - 1):                                          # 樁頂一道橫木（綁住）
        M.box('body', P[0], y, 12, P[2], y + 1, 13, FRAME)
    for x in (P[0], P[2] - 1):
        M.box('body', x, P[1], 12, x + 1, P[3], 13, FRAME)
    M.clear(52, P[1], 0, 68, P[1] + 1, 16)                              # 正面的門：拿掉樁、放一道柵門（開著，靠在旁邊的樁上）
    M.box('body', 52, P[1], 12, 68, P[1] + 1, 13, FRAME)
    for x in range(68, 76, 2):
        M.box('body', x, P[1] - 1, 1, x + 1, P[1], 12, FRAME)
    for z in (3, 10):                                                   # 柵門的兩道橫檔
        M.box('body', 68, P[1] - 1, z, 76, P[1], z + 1, FRAME)
    M.box('body', 54, 0, 0, 66, P[1] + 10, 1, FLOOR)                    # 踏板（從碼頭走進池邊）
    for i, (cx, cy) in enumerate(((30, 24), (48, 40), (72, 22), (88, 46), (34, 52))):   # 池裡的海龜（橢圓的殼、殼上的紋）
        for x in range(cx - 5, cx + 5):
            for y in range(cy - 4, cy + 4):
                if ((x + 0.5 - cx) / 5) ** 2 + ((y + 0.5 - cy) / 4) ** 2 <= 1:
                    M.box('body', x, y, 1, x + 1, y + 1, 2 + (1 if abs(x + 0.5 - cx) < 3 and abs(y + 0.5 - cy) < 2 else 0), SHELL_D if (x + y) % 4 == 0 else SHELL)
    # 後面的遮陽棚（茅草單坡）、桌、翻過來的海龜、秤
    S = (10, 76, 110, 98)
    top = thatch_roof(M, [{'x0': S[0], 'y0': S[1], 'x1': S[2], 'y1': S[3], 'ze': 28, 'p': 0.5, 'over': (2, 2, 2, 2), 'gable': 'x'}], salt=8887)
    roof_posts(M, top, [(S[0], S[1]), (58, S[1]), (S[2] - 2, S[1]), (S[0], S[3] - 2), (58, S[3] - 2), (S[2] - 2, S[3] - 2)])
    trestle_table(M, 20, 50, 80, 92, 8)
    for x in range(26, 42):                                             # 桌上一隻翻過來的海龜（肚子朝上）
        for y in range(82, 90):
            if ((x + 0.5 - 34) / 8) ** 2 + ((y + 0.5 - 86) / 4) ** 2 <= 1:
                M.box('body', x, y, 9, x + 1, y + 1, 11, BELLY)
    english.beam_scale(M, 80, 86)
    lantern(M, '燈籠-棚', (58, S[1], 20))
    M.anchor('door', 60, 2, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'turtle-crawl', 'title': '海龜圍欄（共用：岸邊的淺水池、一圈留縫的木樁與柵門；池裡五隻海龜；茅草遮陽棚下的桌、翻過來的海龜、大橫桿秤）',
            'use': 'turtle-crawl', 'lot': (12, 10), 'M': M, 'style': 'common', 'layers': {'body': '樁、水池與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 商人廊廳 16 × 10 m ───────────────────────────────
def loggia():
    """熱那亞商人廊廳（loggia）：石台上一座三面開敞的拱廊（正面五個拱、兩側各兩個），後牆實的；柱與牆照熱那亞的作法黑白石帶相間；
    紅陶瓦四坡頂；廊裡一張長桌（帳本）、兩條長凳、一座大橫桿秤、幾袋貨；後牆正中一面聖喬治紅十字的盾（熱那亞的紋章）。
    - 碼頭擺設（2026-10-25 做進建築裡）：開敞的廊就是貨物過秤、登帳的地方 ⇒ 拱廊裡靠正面一排貨箱、桶（從拱門看得到）。
    - 照什麼：Galata 1316 年碑文寫 podestà 重建了 loggia（商人廊廳）、過磅所（thebyzantinelegacy.com Galata slabs）〔讀過摘要〕；
      黑白石帶照 Genoa 的 San Lorenzo、Palazzo San Giorgio；loggia 在加拉塔港邊的位置、樣子〔沒查到〕⇒ 開敞拱廊是義大利商人 loggia 的通常樣子（設計）。"""
    X, Y, Z = 160, 100, 70
    M = Model((X, Y, Z))
    R = (4, 6, 156, 94)
    M.box('body', R[0] - 2, R[1] - 2, 0, R[2] + 2, R[3] + 2, 3, GEN_W)  # 石台（三級台階的高）
    M.box('body', 60, 0, 0, 100, R[1] - 2, 2, GEN_W)                    # 正面的台階
    band = lambda x, y, z: GEN_D if ((z - 3) // 4) % 2 else GEN_W        # 黑白相間（每 0.4 m 一帶）
    banded_walls(M, R, 3, 46, 5, band)
    for i in range(5):                                                  # 正面五個拱（淨寬 2.2 m、拱腳 2.6 m）
        arch_open(M, 'x', R[1], R[1] + 5, R[0] + 16 + i * 30, 11, 26, z0=3)
    for cy in (32, 62):                                                 # 兩側各兩個
        arch_open(M, 'y', R[0], R[0] + 5, cy, 10, 26, z0=3)
        arch_open(M, 'y', R[2] - 5, R[2], cy, 10, 26, z0=3)
    english.tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 46, 'p': 0.4, 'over': (3, 3, 3, 3)}], salt=8888)
    # 後牆正中的盾：白底紅十字（聖喬治）
    for x in range(72, 88):
        for z in range(24, 40):
            M.put('body', x, R[3] - 6, z, FLAG_R if (78 <= x < 82 or 30 <= z < 34) else FLAG_W, force=True)
    trestle_table(M, 40, 120, 56, 68, 11)
    M.box('body', 70, 60, 12, 78, 66, 13, CLOTH)                        # 攤開的帳本
    bench(M, 40, 120, 72, 76, z=7)
    bench(M, 40, 120, 48, 52, z=7)
    english.beam_scale(M, 30, 30, z0=3)
    for i, (x, y) in enumerate(((120, 24), (128, 24), (124, 32))):
        for z in range(3, 9):
            M.box('body', x, y, z, x + 7, y + 6, z + 1, SACK)
    goods(M, '廊裡', [('c', 100, 17, 3), ('c', 107, 17, 3), ('c', 103, 17, 9), ('b', 138, 17, 3), ('b', 147, 17, 3)])
    lantern(M, '燈籠-中拱', (76, R[1], 30))
    M.anchor('door', 80, 2, 2)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'loggia', 'title': '商人廊廳（熱那亞：石台上三面開敞的拱廊、黑白相間的石帶、紅陶瓦四坡頂；長桌與帳本、長凳、大橫桿秤、貨袋；後牆聖喬治紅十字盾）',
            'use': 'loggia', 'lot': (16, 10), 'M': M, 'style': 'genoa', 'layers': {'body': '拱廊與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 港邊倉庫列 30 × 12 m ───────────────────────────────
def emporion():
    """港邊倉庫列（emporion，羅馬／拜占庭）：一長排兩層的倉庫 —— 牆是石灰岩方石夾紅磚帶（opus mixtum，同城牆那一套的作法）；
    一樓七個拱門的貨間（深色的木門關著、中間那間開著看得到貨）、二樓每間一扇小拱窗；紅陶瓦緩坡的兩坡頂；門前一排陶罐、貨袋與桶。
    - 前院（2026-10-25 碼頭擺設做進建築裡）：整排往後退 1.2 m ⇒ 陶罐那一排後面幾間門口堆貨箱、桶、貨袋、一盤繩（開著那一間的門口留空）。
    - 照什麼：巴列奧略王朝的港區四周「許多倉庫」、Prosphorion 在 Sirkeci 挖到倉庫遺址（Wikipedia Neorion／Prosphorion Harbour）〔讀過摘要〕；
      一排貨間的形制照羅馬港口的 horrea（設計）；石磚相間照 kaguya-roman-1453 的牆。"""
    X, Y, Z = 300, 120, 84
    M = Model((X, Y, Z))
    R = (4, 20, 296, 112)

    def mixtum(x, y, z):
        k = z % 14
        if k >= 10:
            return BRICK_RM if k == 12 else BRICK_R                     # 三皮紅磚＋一道粉紅厚灰漿
        return LIME_G if h01('em', (x + y) // 6, z // 2, 0) < 0.25 else LIME_R
    banded_walls(M, R, 0, 60, 5, mixtum)
    M.box('body', R[0] + 5, R[1] + 5, 30, R[2] - 5, R[3] - 5, 32, FLOOR)
    for i in range(7):                                                  # 一樓七個貨間的拱門、二樓小拱窗
        cx = R[0] + 21 + i * 41
        arch_open(M, 'x', R[1], R[1] + 5, cx, 9, 16)
        if i != 3:
            M.box('body', cx - 9, R[1] + 3, 0, cx + 9, R[1] + 4, 25, FRAME, force=True)   # 關著的木門（在牆厚中間）
        arch_open(M, 'x', R[1], R[1] + 5, cx, 3, 42, z0=36)
        M.box('body', cx - 3, R[1] + 4, 36, cx + 3, R[1] + 5, 45, DARK, force=True)
    for cy in (36, 84):                                                 # 兩端山牆的小窗
        for x0 in (R[0], R[2] - 5):
            arch_open(M, 'y', x0, x0 + 5, cy, 3, 42, z0=36)
    english.tile_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 60, 'p': 0.3, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=8889)
    for (x0, x1) in ((R[0], R[0] + 5), (R[2] - 5, R[2])):               # 兩端山牆（三角，同牆的作法）
        for y in range(R[1], R[3]):
            d = min(y + 0.5 - R[1], R[3] - y - 0.5)
            for z in range(60, int(math.floor(60 + 0.3 * d))):
                for x in range(x0, x1):
                    M.put('body', x, y, z, mixtum(x, y, z))
    cx3 = R[0] + 21 + 3 * 41                                            # 開著的那一間：裡面看得到的貨
    for i in range(3):
        for z in range(0, 6):
            M.box('body', cx3 - 7 + i * 5, R[1] + 8, z, cx3 - 3 + i * 5, R[1] + 13, z + 1, SACK)
    for i in range(18):                                                 # 門前一排陶罐（直徑 0.6 m、高 0.9 m、細頸）
        cx, cy = 12 + i * 16, 5
        if R[0] + 21 + 3 * 41 - 12 < cx < R[0] + 21 + 3 * 41 + 12:
            continue
        for x in range(cx - 3, cx + 3):
            for y in range(cy - 3, cy + 3):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= 9:
                    M.box('body', x, y, 0, x + 1, y + 1, 7, AMPH)
        M.box('body', cx - 1, cy - 1, 7, cx + 1, cy + 1, 9, AMPH)
    goods(M, '前院', [('b', 20, 15, 0), ('b', 30, 15, 0), ('c', 62, 15, 0), ('c', 69, 15, 0), ('c', 65, 15, 6),
                      ('c', 185, 15, 0), ('c', 192, 15, 0), ('b', 226, 15, 0), ('b', 236, 15, 0), ('c', 266, 15, 0)])
    sacks(M, 124, 12)
    sacks(M, 162, 12)
    rope_coil(M, 280, 15, r=4)
    lantern(M, '燈籠-中', (cx3 + 12, R[1], 22))
    M.anchor('door', cx3, 4, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'emporion', 'title': '港邊倉庫列（羅馬：一長排兩層、石灰岩方石夾紅磚帶；一樓七個拱門的貨間、二樓小拱窗、紅陶瓦緩坡頂；門前一排陶罐，幾間門口堆貨箱、桶、貨袋、繩盤）',
            'use': 'emporion', 'lot': (30, 12), 'M': M, 'style': 'roman', 'layers': {'body': '牆、門與擺設', 'roof': '屋頂'}}


ALL = [chandlery, harbour_office, naval_store, turtle_crawl, loggia, emporion]
