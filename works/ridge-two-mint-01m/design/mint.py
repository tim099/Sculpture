# 鑄幣廠與火藥坊（TASK-0984；Tim 2026-10-26「/scp-task 984 GO」）—— TASK-0976 加的兩種新建築，全部共用 common：
#   鑄幣廠（mint）：吃銅錠、鑄銅幣（Blocksail docs/STORES.md §6.4、PRODUCTION.md §19.2）；
#   火藥坊（powder-mill）：硝石＋硫磺＋木炭 ⇒ 火藥（1660 年代的城沒有硫磺，暫時產不出來；模型照樣做）。
# 工具同 apex-one-industry-01m/design 的 industry.py（stone_block、heap、cord、wheelbarrow、shovel、yard_ground）
#   ＋ trailhead-harbour-01m/design 的 workshops2／workshops／town3／quay／harbour／civic／carib／kit 的全部。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 地塊照 Blocksail world/buildings/<種>.json 的 lot：兩種都 12 × 16 m。
# 史料：這一批沒有上網查 ⇒ 寫「通論」的是西屬美洲鑄幣廠、17 世紀火藥坊的常見做法（記得、沒翻原典），其餘配置全是設計。
import os, sys, math
_IND = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'apex-one-industry-01m', 'design')
if _IND not in sys.path:
    sys.path.insert(1, _IND)
from industry import *                                                 # noqa: F401,F403,E402
from town3 import barred                                               # noqa: E402

COIN = COPPER                    # 銅錠、銅條、銅幣（同蒸餾器的銅 173）
MOLTEN = EMBER                   # 坩堝裡熔的銅（紅橙；⛔ 不用 245 ⇒ 那是燈籠玻璃）
SALTPETRE = LIMEW                # 硝石的結晶（白）
SULPHUR = 252                    # 硫磺塊（黃）
POWDER = DARK                    # 火藥（黑）


def bellows(M, x0, x1, y0, y1, z0, toward='left', layer='body'):
    """雙板風箱（同 workshops.smithy 那一具，可以朝左或朝右）：沿 x 從寬到窄，嘴朝 toward；底下四根木腳。"""
    for (x, y) in ((x0, y0), (x1 - 2, y0), (x0, y1 - 2), (x1 - 2, y1 - 2)):
        M.box(layer, x, y, 0, x + 2, y + 2, z0, FRAME)
    for x in range(x0, x1):
        h = 2 + ((x - x0) if toward == 'left' else (x1 - 1 - x)) // 3
        M.box(layer, x, y0, z0, x + 1, y1, z0 + 1, FRAME)
        M.box(layer, x, y0, z0 + 1, x + 1, y1, z0 + 1 + h, LEATHER)
        M.box(layer, x, y0, z0 + 1 + h, x + 1, y1, z0 + 2 + h, FRAME)


def stump(M, cx, cy, r, h, layer='body'):
    """樹墩（圓、實心、年輪的頂）。"""
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                M.box(layer, x, y, 0, x + 1, y + 1, h - 1, LOG)
                M.put(layer, x, y, h - 1, LOG_TIP)


def chest(M, x0, y0, x1, y1, h, layer='body'):
    """鐵皮包角的木箱（錢箱）：箱身深色木、上下兩道鐵箍、正中一個鐵鎖。"""
    M.box(layer, x0, y0, 0, x1, y1, h, FRAME)
    for z in (1, h - 2):
        for x in range(x0, x1):
            for y in range(y0, y1):
                if x in (x0, x1 - 1) or y in (y0, y1 - 1):
                    M.put(layer, x, y, z, IRON, True)
    M.box(layer, (x0 + x1) // 2 - 1, y0 - 1, h - 4, (x0 + x1) // 2 + 1, y0, h - 2, IRON)


def chimney_through(M, top, x0, y0, x1, y1, z0, above=7):
    """毛石煙囪：從 z0 砌到穿過屋面再高 above 格，帽一圈灰縫、煙道口黑；回傳煙道口那一格（smoke）。"""
    zc = max(top[(x, y)] for x in range(x0, x1) for y in range(y0, y1) if (x, y) in top) + above
    M.box('body', x0, y0, z0, x1, y1, zc, RUBBLE, force=True)
    M.box('body', x0 - 1, y0 - 1, zc - 2, x1 + 1, y1 + 1, zc, MORTAR, force=True)
    M.box('body', x0 + 3, y0 + 3, zc - 2, x1 - 3, y1 - 3, zc, CHAR, force=True)
    return ((x0 + x1) // 2, (y0 + y1) // 2, zc - 1)


def kettle(M, cx, cy, z0, r, fill, layer='body'):
    """敞口的銅鍋（熬硝）：鍋身一圈銅、往上張開，裡面滿到鍋口下一格。"""
    for dz in range(6):
        rr = r - 2 + dz * 0.4
        for x in range(int(cx - r - 2), int(cx + r + 3)):
            for y in range(int(cy - r - 2), int(cy + r + 3)):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= rr:
                    M.put(layer, x, y, z0 + dz, COPPER if (d > rr - 1 or dz == 0 or dz == 5) else fill, True)


# ─────────────────────────────── 鑄幣廠 12 × 16 m ───────────────────────────────
def mint():
    """鑄幣廠（mint／casa de moneda）：臨路一間毛石的帳房（鐵條窗、木板門）—— 試金的桌與天平、兩只包鐵的錢箱、一袋袋銅幣、帳架；
    後門出去毛石圍牆圍起來的院子（銅錠一垛、木炭堆、水桶）；後半一座三面毛石、正面朝院子開敞的鑄造間：
    左邊熔銅的爐台（坩堝裡紅的銅、石罩、穿出屋頂的煙囪）與風箱、爐前砂床上鑄好的銅條；中間樹墩上的鐵砧（把銅條打薄）；
    右前剪坯的桌（大剪、一盤圓坯）；右後打幣的大樹墩（下模嵌在墩上、上模與錘）、一桶打好的銅幣。
    - 照什麼〔通論〕：西屬美洲 16、17 世紀的鑄幣是錘打幣（macuquina）—— 熔金屬鑄成條、打薄、剪成坯、秤過、放在上下兩個鋼模之間用錘打；
      帳房與錢箱、圍牆是鑄幣廠一定有的（錢要看得住）。爐、模、剪的樣子〔沒查到〕⇒ 照鐵匠鋪那一套（設計）。
    - 遊戲：配方 mint-copper 吃銅錠、產出的是錢（Blocksail recipes.js；purseMint 進主人的金庫）。"""
    X, Y, Z = 120, 160, 80
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 118, 158, salt=9841)
    # 院子的毛石圍牆（2.4 m）先砌：前面那一段 ＝ 帳房的後牆，帳房的牆與後門要蓋在它上面
    R = (10, 8, 110, 60)
    rubble_walls(M, (2, R[3] - 4, 118, 158), 0, 24, 4, salt=9844)
    # 帳房：10 × 5.2 m 的毛石屋、木瓦兩坡頂；地板高一格（門、窗都從 z 1 起）
    rubble_walls(M, R, 0, 30, 4, salt=9842)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 1, FLOOR)
    for x0, x1 in ((R[0], R[0] + 4), (R[2] - 4, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 30, 0.6, z0=30, color=RUBBLE, edge=RUBBLE_D)
    put_part(M, 'door-plank', '前-門', 'front', R, 60, 1, 4)
    put_part(M, 'door-plank', '後-門', 'back', R, 60, 1, 4)
    for c in (30, 90):
        barred(M, 'front', R, c, 11, w=10, h=10)
    barred(M, 'right', R, 34, 11, w=10, h=10)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.6, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=9843)
    # 帳房裡：試金的桌與天平（左）、帳架（左牆）、兩只錢箱與錢袋（右）
    trestle_table(M, 18, 50, 30, 40, 9)
    M.box('body', 33, 34, 10, 35, 36, 18, IRON)                                   # 天平的柱
    M.box('body', 26, 34, 18, 43, 36, 19, IRON)                                   # 橫梁
    for xp in (27, 41):
        M.box('body', xp, 35, 13, xp + 1, 36, 18, IRON)                           # 吊秤盤的鍊
        M.box('body', xp - 2, 33, 12, xp + 3, 38, 13, COPPER)                     # 秤盤
    M.box('body', 22, 32, 10, 26, 36, 11, COIN)                                   # 桌上一疊銅幣
    M.box('body', 22, 32, 11, 25, 35, 12, COIN)
    M.box('body', 44, 31, 10, 49, 38, 11, CREAM)                                  # 攤開的帳簿
    M.box('body', 15, 16, 1, 17, 54, 26, FRAME)                                   # 左牆的帳架：立板、三層架、架上的帳簿
    for z in (8, 15, 22):
        M.box('body', 15, 16, z, 22, 54, z + 1, FRAME)
        for y in range(18, 52, 4):
            M.box('body', 17, y, z + 1, 21, y + 2, z + 5 + (y // 4) % 2, LEATHER if (y // 4) % 2 else CREAM)
    chest(M, 70, 44, 86, 54, 9)
    chest(M, 88, 44, 104, 54, 9)
    for (x, y) in ((76, 22), (82, 24), (79, 30), (96, 20)):                       # 錢袋（口紮起來）
        M.box('body', x, y, 1, x + 5, y + 5, 6, SACK)
        M.box('body', x + 1, y + 1, 6, x + 4, y + 4, 7, SACK)
        M.box('body', x + 2, y + 2, 7, x + 3, y + 3, 8, ROPE)
    # 鑄造間：三面毛石、正面朝院子開敞（兩根石墩分三開間、上面一道石楣），木瓦兩坡頂
    H = (8, 100, 112, 156)
    rubble_walls(M, H, 0, 30, 4, salt=9845)
    for xa, xb in ((H[0] + 4, 38), (42, 78), (82, H[2] - 4)):
        M.clear(xa, H[1], 1, xb, H[1] + 4, 24)
    for x0, x1 in ((H[0], H[0] + 4), (H[2] - 4, H[2])):
        end_gable(M, x0, x1, H[1], H[3], 30, 0.6, z0=30, color=RUBBLE, edge=RUBBLE_D)
    top = shingle_roof(M, [{'x0': H[0], 'y0': H[1], 'x1': H[2], 'y1': H[3], 'ze': 30, 'p': 0.6, 'over': (3, 3, 4, 2), 'gable': 'x'}], salt=9846)
    # 熔銅的爐台（左後）：毛石台 1 m 高、台上坩堝（陶的一圈、裡面紅的銅）、後面擋火牆、石罩、煙囪
    stone_block(M, 12, 126, 0, 40, 152, 10, salt=9847)
    M.box('body', 14, 128, 10, 38, 150, 11, CHAR, force=True)
    for x in range(18, 34):
        for y in range(132, 148):
            d = math.hypot(x + 0.5 - 26, y + 0.5 - 140)
            if d <= 6:
                M.box('body', x, y, 10, x + 1, y + 1, 16, CLAY_D if d > 4.5 else MOLTEN, force=True)
    stone_block(M, 12, 148, 10, 40, 152, 20, salt=9848)
    stone_block(M, 10, 124, 22, 42, 152, 24, salt=9849)
    for (x, y) in ((12, 124), (38, 124)):
        M.box('body', x, y, 10, x + 2, y + 2, 22, IRON)
    sx, sy, sz = chimney_through(M, top, 20, 140, 32, 152, 24)
    M.anchor('smoke', sx, sy, sz)
    bellows(M, 42, 56, 132, 146, 10, toward='left')
    M.box('body', 39, 138, 11, 42, 140, 13, IRON, force=True)                     # 風箱嘴伸進爐台側面
    M.box('body', 48, 138, 13, 50, 140, 30, FRAME)                                # 拉桿，頂到屋架下
    M.box('body', 44, 138, 30, 66, 140, 32, FRAME)
    M.box('body', 64, 138, 18, 65, 139, 30, ROPE)
    # 爐前：砂床上鑄好的銅條（一排）、鉗子
    M.box('body', 14, 106, 0, 40, 122, 2, SAND)
    for y in range(108, 121, 3):
        M.box('body', 17, y, 2, 37, y + 2, 3, COIN, force=True)
    M.box('body', 40, 112, 1, 46, 113, 2, IRON)                                   # 擱在地上的鉗子
    # 中間：樹墩上的鐵砧（打薄的銅條擱在砧上）
    stump(M, 62, 126, 4, 6)
    M.box('body', 58, 124, 6, 66, 128, 8, IRON)
    M.box('body', 59, 124, 8, 67, 128, 10, IRON)
    M.box('body', 66, 125, 9, 69, 127, 10, IRON)
    M.box('body', 56, 125, 10, 68, 127, 11, COIN, force=True)
    # 右前：剪坯的桌（大剪、一盤圓坯、剪剩的銅條）
    trestle_table(M, 84, 108, 106, 116, 9)
    M.box('body', 86, 109, 10, 96, 110, 11, IRON)                                 # 大剪的兩片
    M.box('body', 86, 111, 10, 96, 112, 11, IRON)
    M.box('body', 95, 109, 10, 98, 112, 12, IRON)                                 # 剪的軸
    M.box('body', 98, 107, 10, 106, 115, 11, FRAME)                               # 一盤圓坯
    for (x, y) in ((99, 108), (101, 110), (103, 108), (100, 112), (104, 112), (102, 113)):
        M.box('body', x, y, 11, x + 1, y + 1, 12, COIN)
    # 右後：打幣的大樹墩（下模嵌在墩上）、立著的上模、靠著的錘；一桶打好的銅幣
    stump(M, 94, 136, 6, 8)
    M.box('body', 93, 135, 8, 95, 137, 10, IRON, force=True)                      # 下模
    M.box('body', 93, 135, 11, 95, 137, 15, IRON)                                 # 上模（還沒打下去：壓著一枚坯）
    M.put('body', 93, 135, 10, COIN, True)
    M.put('body', 94, 135, 10, COIN, True)
    M.put('body', 93, 136, 10, COIN, True)
    M.put('body', 94, 136, 10, COIN, True)
    rod(M, (101.5, 128.5, 1), (101.5, 128.5, 14), 0.8, FRAME, FRAME)            # 靠在墩邊的錘柄
    M.box('body', 99, 127, 13, 104, 131, 16, IRON, force=True)                    # 錘頭
    tub(M, 106, 146, 1, 7, 4.5, COIN)
    # 院子：銅錠一垛（交錯疊）、木炭堆、水桶
    for z in range(6):
        for k in range(4):
            if z % 2 == 0:
                M.box('body', 70 + k * 6, 70, z + 1, 74 + k * 6, 86, z + 2, COIN)
            else:
                M.box('body', 70, 70 + k * 4, z + 1, 92, 72 + k * 4, z + 2, COIN)
    heap(M, 20, 78, 12, 9, 10, lambda x, y, z: CHAR if h01('mc', x, y, z) < 0.88 else DARK, z0=1)
    M.models += [{'name': '水桶', 'source': 'summit-rocher-01m-barrel', 'at': [104, 74, 1], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-門', (46, R[1], 20))
    M.anchor('door', 60, R[1] - 1, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'mint', 'title': '鑄幣廠（共用：毛石帳房、鐵條窗、試金天平與錢箱；圍牆院子裡的銅錠與木炭；鑄造間的熔銅爐與風箱、砂床上的銅條、鐵砧、剪坯桌、打幣的樹墩與上下模）',
            'use': 'mint', 'lot': (12, 16), 'M': M, 'style': 'common', 'layers': {'body': '帳房、圍牆、鑄造間與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 火藥坊 12 × 16 m ───────────────────────────────
def powder_mill():
    """火藥坊（powder-mill）：用火的與碰火藥的分在兩頭，中間一道土堤 ——
    ① 前半：熬硝棚（三面毛石、正面開敞、木瓦單坡頂；爐台上兩口銅鍋、爐口紅的火、煙囪；棚前三個結晶木槽裡白的硝）、右前木炭堆與一箱黃的硫磺塊、手推車；
    ② 中間一道 1.8 m 的土堤（頂上長草、正中留一條走道）；
    ③ 後半：開敞的木瓦棚下一座搗藥機（一根長木臼、六根木杵、後面一根帶撥子的凸輪軸、軸頭一個大手輪）；右邊篩粒、晾藥的桌（布上一層黑的藥粒）；
       右後角一間厚毛石牆的小火藥庫（木板門、裡面六桶火藥）。
    - 照什麼〔通論〕：17 世紀的火藥坊 —— 硝要先熬過、結晶提純；三樣料一起在臼裡搗（stamp mill）、搗好過篩成粒（corning）、攤開晾乾、裝桶；
      怕火 ⇒ 熬硝的火離搗藥的地方遠、中間隔土堤，火藥庫牆厚、離其他東西遠。史實的搗藥機多半是水車帶的 ⇒ 城裡沒有水路，改成人搖的大手輪（設計）。
    - 遊戲：配方 gunpowder（硝石＋硫磺＋木炭 ⇒ 火藥）；1660 年代的城 10 km 內都沒有硫磺（TASK-0957）⇒ 現在產不出來，模型照樣擺料。"""
    X, Y, Z = 120, 160, 70
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 118, 158, salt=9851)
    # ① 熬硝棚（左前）：6 × 3.8 m、後牆與兩側毛石 2.6 m、正面開敞；單坡頂高的那邊在後
    S = (6, 14, 66, 52)
    rubble_walls(M, S, 0, 26, 4, salt=9852)
    M.clear(S[0] + 4, S[1], 1, S[2] - 4, S[1] + 4, 26)
    top = shed_roof(M, S[0] - 2, S[1] - 3, S[2] + 2, S[3] + 2, 38, 0.3, low='front', color_fn=lambda x, y, f, r, e: shingle_color(x, y, f, r, e, 9853))
    roof_posts(M, top, [(S[0], S[1] - 2), (S[2] - 2, S[1] - 2)])
    for x in range(S[0], S[2]):                                                   # 兩側牆補到屋面下（單坡 ⇒ 牆頂斜的）
        for y in range(S[1], S[3]):
            if x < S[0] + 4 or x >= S[2] - 4 or y >= S[3] - 4:
                zt = top.get((x, y))
                if zt is not None and zt - 2 > 26:
                    M.box('body', x, y, 26, x + 1, y + 1, zt - 1, RUBBLE)
    stone_block(M, 10, 32, 0, 62, 48, 9, salt=9854)                               # 爐台（後牆邊，0.9 m）
    for cx in (24, 48):
        M.clear(cx - 3, 32, 2, cx + 3, 36, 7)
        M.box('body', cx - 3, 36, 2, cx + 3, 37, 7, EMBER, force=True)
        M.box('body', cx - 4, 31, 7, cx + 4, 32, 8, IRON, force=True)
        kettle(M, cx, 40, 9, 6, SALTPETRE)
    sx, sy, sz = chimney_through(M, top, 32, 42, 40, 52, 9, above=6)
    M.anchor('smoke', sx, sy, sz)
    for cx in (16, 34, 52):                                                       # 棚前三個結晶的木槽（裝著白的硝）
        tub(M, cx, 22, 1, 7, 5, SALTPETRE)
    # 右前：木炭堆、硫磺箱、手推車、硝袋
    heap(M, 92, 22, 14, 11, 12, lambda x, y, z: CHAR if h01('pc', x, y, z) < 0.88 else DARK, z0=1)
    M.box('body', 96, 38, 1, 114, 52, 7, BOARD)                                   # 硫磺箱（木板框）
    M.box('body', 97, 39, 1, 113, 51, 7, SULPHUR, force=True)
    for (x, y) in ((99, 41), (104, 45), (109, 42), (101, 48), (107, 49)):
        M.box('body', x, y, 7, x + 2, y + 2, 8, SULPHUR)
    for (x, y) in ((74, 40), (80, 44), (76, 48)):
        M.box('body', x, y, 1, x + 5, y + 5, 6, SACK)
        M.box('body', x + 1, y + 1, 6, x + 4, y + 4, 7, SACK)
    wheelbarrow(M, 68, 4, CHAR)
    # ② 土堤：1.8 m 高、坡 1:1、頂上長草，正中留 1.2 m 的走道
    for x in range(4, 116):
        for y in range(56, 76):
            if 54 <= x < 66:
                continue
            h = int(18 - 1.6 * max(0.0, abs(y + 0.5 - 66) - 2))      # 頂寬 0.4 m、兩邊斜下去
            for z in range(1, h + 1):
                M.put('body', x, y, z, SOD if z == h and h01('bk', x // 3, y // 3) < 0.7 else (SOD_D if z == h else EARTH))
    # ③ 搗藥棚（後半左）：開敞、木瓦兩坡頂（屋脊沿 x）、六根柱
    T = (6, 82, 76, 128)
    top2 = shingle_roof(M, [{'x0': T[0], 'y0': T[1], 'x1': T[2], 'y1': T[3], 'ze': 40, 'p': 0.5, 'over': (2, 2, 2, 2), 'gable': 'x'}], salt=9855)
    roof_posts(M, top2, [(x, y) for x in (T[0], 44, T[2] - 2) for y in (T[1], T[3] - 2)])
    # 木臼：一根長木頭（沿 x）、六個臼坑（黑的藥）
    M.box('body', 12, 98, 1, 70, 108, 9, LOG)
    pest = [17 + k * 9 for k in range(6)]
    for px in pest:
        M.box('body', px - 1, 101, 5, px + 3, 105, 9, POWDER, force=True)
    # 木杵：立在臼坑裡（2 × 2）、前後兩道導木夾著；每根後面一個撥子；凸輪軸在後、軸頭大手輪
    for px in pest:
        M.box('body', px, 102, 6, px + 2, 104, 34, FRAME, force=True)
        M.box('body', px, 104, 26, px + 2, 110, 28, FRAME, force=True)            # 杵上的托（凸輪的撥子撥它）
    for y in (100, 104):
        M.box('body', 10, y, 22, 74, y + 2, 24, FRAME, force=True)                # 導木
        M.box('body', 10, y, 30, 74, y + 2, 32, FRAME, force=True)
    for x in (10, 72):
        M.box('body', x, 100, 1, x + 2, 106, 34, FRAME, force=True)               # 兩端的架柱
        M.box('body', x, 110, 1, x + 2, 114, 31, FRAME, force=True)               # 撐凸輪軸的柱
    rod(M, (8, 112.5, 29), (80, 112.5, 29), 1.6, FRAME, LOG_TIP)                  # 凸輪軸
    for px in pest:
        M.box('body', px, 109, 29, px + 2, 112, 31, FRAME, force=True)            # 軸上的撥子
    for y in range(98, 128):                                                       # 大手輪（立在 y–z 平面、x 78）：輪圈、四根輻、搖把
        for z in range(14, 45):
            d = math.hypot(y + 0.5 - 112.5, z + 0.5 - 29.5)
            if 11.75 <= d <= 13.75:                                            # 輪圈 2 格寬（1 格寬的圓只有斜角相碰 ⇒ 斷成幾段）
                M.box('body', 78, y, z, 80, y + 1, z + 1, FRAME, force=True)
    for (dy, dz) in ((1, 0), (0, 1)):
        for t in range(-12, 13):
            M.box('body', 78, int(112.5 + dy * t), int(29.5 + dz * t), 80, int(112.5 + dy * t) + 1, int(29.5 + dz * t) + 1, FRAME, force=True)
    M.box('body', 80, 112, 39, 83, 114, 41, FRAME, force=True)                    # 搖把
    # 右邊：篩粒、晾藥的桌（布上一層黑的藥粒）
    for y0 in (84, 100):
        trestle_table(M, 88, 114, y0, y0 + 10, 9)
        M.box('body', 89, y0 + 1, 10, 113, y0 + 9, 11, SACK, force=True)
        for x in range(90, 112):
            for y in range(y0 + 2, y0 + 8):
                if h01('gr', x, y) < 0.6:
                    M.put('body', x, y, 11, POWDER)
    M.box('body', 92, 80, 10, 100, 82, 14, FRAME)                                 # 篩（木框、鐵絲網）立在桌邊
    M.box('body', 93, 80, 11, 99, 81, 13, IRON, force=True)
    M.box('body', 92, 80, 0, 93, 82, 10, FRAME)
    M.box('body', 99, 80, 0, 100, 82, 10, FRAME)
    # 右後角：火藥庫（厚 0.6 m 的毛石牆、木板門朝前、木瓦兩坡頂）
    Q = (82, 122, 116, 156)
    rubble_walls(M, Q, 0, 27, 6, salt=9856)
    M.box('body', Q[0] + 6, Q[1] + 6, 0, Q[2] - 6, Q[3] - 6, 1, FLOOR)
    for x0, x1 in ((Q[0], Q[0] + 6), (Q[2] - 6, Q[2])):
        end_gable(M, x0, x1, Q[1], Q[3], 27, 0.5, z0=27, color=RUBBLE, edge=RUBBLE_D)
    put_part(M, 'door-plank', '火藥庫-門', 'front', Q, 97, 1, 6)
    shingle_roof(M, [{'x0': Q[0], 'y0': Q[1], 'x1': Q[2], 'y1': Q[3], 'ze': 27, 'p': 0.5, 'over': (2, 2, 2, 2), 'gable': 'x'}], salt=9857)
    for i, (x, y) in enumerate(((92, 134), (98, 134), (104, 134), (92, 140), (98, 140), (104, 140))):
        M.models.append({'name': '火藥桶-%d' % (i + 1), 'source': 'basecamp-frigate-constitution-01m-powder-barrel', 'at': [x, y, 1], 'pivot': [11, 11, 0],
                         'meta': {'kind': 'powder', 'powder_lb': 100}})
    lantern(M, '燈籠-熬硝棚', (S[0] + 4, S[1] - 2, 18))
    M.anchor('door', 60, 4, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'powder-mill', 'title': '火藥坊（共用：前半熬硝棚的爐台與銅鍋、結晶槽、木炭與硫磺；中間一道土堤；後半搗藥棚的木臼、六根木杵、凸輪軸與大手輪、篩粒晾藥的桌、厚牆的小火藥庫）',
            'use': 'powder-mill', 'lot': (12, 16), 'M': M, 'style': 'common', 'layers': {'body': '熬硝棚、土堤、搗藥機、火藥庫與擺設', 'roof': '屋頂'}}


ALL = [mint, powder_mill]
