# 港口建築的水上版（Blocksail TASK-0899 第二階段；docs/TOWN_BUILD.md §5.18、BUILDING_SPEC §5 第一列的 water／slip）—— 船棚、小船廠、大船廠、修船碼頭。
# 陸上版照舊（ame-carib-civic-01m 的修船碼頭、兩座船廠；trailhead-harbour-01m 的船棚），這裡另做一份「站在木樁平台上、船台斜進水裡」的，兩版並存（Tim 2026-10-24「另做水上版並存」）。
# 工具照 ame-carib-civic-01m/design 的 shipyard.py（船骨架、鋸木架、木板倉庫）、harbour.py（絞盤、繩盤、原木堆、瀝青鍋、工具棚）
#   與 trailhead-harbour-01m/design/quay.py（圓材、繩、滑車、繫纜木樁）、crest-berth-01m/design/berth.py（護舷、鐵梯、燈柱）⇒ 不另抄一份。
#
# 座標（同 BUILDING_SPEC §5 水上版那一列）：x 臨碼頭寬（從碼頭上面向水看，左 → 右）；y 進深，y 0 ＝ 正面（貼碼頭線、棧橋邊）、y 大 ＝ 背面（朝水）；z 往上，0.1 m／格。
#   z ZD（＝ meta deckz × 10）＝ 平台面：遊戲把模型往下放 deckz（Blockside 63_towns.js townLotInst），平台的木板（厚 0.4 m）與樁由遊戲畫（每 4 m 一根到海床）⇒ 模型只雕平台上面的東西；
#   船台那一條（背面往回 slip.len、寬 slip.w、x 置中）遊戲不鋪板也不立樁 ⇒ 船台的滑道從平台斜下去、尾端到 z 0（比平台面低 deckz）、底下立樁 —— 這一段在模型裡。
#   meta water ＝ d0（world/town.js WATER）、slip ＝ "len,w,drop"（drop ＝ deckz）。大小照 WATER（框 ＝ 地塊、⛔ 什麼都不伸出框）。
# 史料：陸上版那幾份（作品 references；English Harbour 1725、Port Royal 本地造 sloop、Aubin 1702 BIGUES）；17 世紀港口的船台從船廠斜進水、底下打樁〔通常的做法〕。
#   Tim 的參考圖（TASK-0899 任務描述）：木造船棚踩在水上的木樁、後半在石碼頭上，裡面一條木板船台斜進水裡、船台上一艘小船。尺寸、配置是設計。
import os, sys, math

WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in (('ame-carib-civic-01m', 'design'), ('trailhead-harbour-01m', 'design'), ('crest-berth-01m', 'design')):
    p = os.path.join(WORKS, *sub)
    if p not in sys.path:
        sys.path.insert(0, p)
from shipyard import hull_frame, saw_trestle, board_store               # noqa: E402  它 import civic、harbour
from berth import *                                                    # noqa: E402,F401  quay（rope_line、spar、tackle_block、bollard）、harbour、civic／kit ＋ fenders、ladder、lamp_post、cargo、cannon_bollard
from harbour import EMBER                                              # noqa: E402

LANTERN_PIVOT = [4.5, 13, 15.5]


class Water:
    """平台上的東西畫在 T（z 0 ＝ 地板面）、完了整份往上搬 ZD ＋ 1 進 M（格、部件關聯、外部模型、固定點）；船台、樁、護舷、梯畫在 M 的真 z。
    M 的 z ZD 先鋪一層 0.1 m 的木地板（同漁場水上版 BUILDING_SPEC §6.24：遊戲的板頂在 z ZD 的底面 ⇒ 地板高 0.1 m、不跟板頂同一個面閃；
    工人的工作點要腳下有格 —— tools/workspots.py、townkit_check）；slip ＝ (x0, x1, y0) 船台口（遊戲不鋪板）⇒ 那一塊不鋪；
    rooms ＝ 四面有牆的屋子（倉庫、鐵匠鋪）的框 ⇒ 牆裡面不鋪（底下是遊戲的板；鋪了整間封死、算成封閉空腔）。"""

    def __init__(s, X, Y, Z, ZD, slip=None, rooms=()):
        s.ZD = ZD
        s.M = Model((X, Y, Z))
        s.T = Model((X, Y, Z - ZD - 1))
        s.T.shutter = s.M.shutter
        for x in range(X):
            k = (x // 3) % 7
            c = WOOD_G if k == 3 else WOOD_D if k == 5 else WOOD
            for y in range(Y):
                if slip and slip[0] <= x < slip[1] and y >= slip[2]:
                    continue
                if any(r[0] + 4 <= x < r[2] - 4 and r[1] + 4 <= y < r[3] - 4 for r in rooms):
                    continue
                s.M.put('body', x, y, ZD, c)

    def done(s):
        dz = s.ZD + 1
        for (x, y, z), (ln, c) in s.T.cells.items():
            s.M.put(ln, x, y, z + dz, c, force=True)
        s.M.oob += s.T.oob
        for L in s.T.links:
            L = dict(L)
            L['at'] = [L['at'][0], L['at'][1], L['at'][2] + dz]
            L['cells'] = {(x, y, z + dz): c for (x, y, z), c in L['cells'].items()}
            s.M.links.append(L)
        for m in s.T.models:
            m = dict(m); m['at'] = [m['at'][0], m['at'][1], m['at'][2] + dz]; s.M.models.append(m)
        for k, (x, y, z) in s.T.anchors.items():
            s.M.anchors[k] = (x, y, z + dz)
        for R in getattr(s.T, 'ropes', []):                             # 繩（berth.py rope）跟著往上搬
            rope(s.M, R['name'], [R['a'][0], R['a'][1], R['a'][2] + dz], [R['b'][0], R['b'][1], R['b'][2] + dz], R['color'], R['thick'], R['slack'])
        return s.M


def ways(M, cx, gap, ya, za, yb, zb, ys, ZD, salt=0):
    """船台（slipway）：兩條平行的滑道木（ways，截面 3 × 3、中線兩邊各 gap 格），從 (ya, za) 等坡斜到 (yb, zb)；每 2 m 一根橫枕木。
    滑道底下：平台上那一段（y < ys）每 2 m 一疊墊木（從平台面 ZD 起）；水上那一段（y ≥ ys，遊戲沒鋪板）每 2 m 一對樁（0.4 m 見方、到 z 0）＋ 一道橫樑。"""
    def zw(y):
        return int(round(za + (zb - za) * (y - ya) / (yb - ya)))
    xs = (cx - gap - 3, cx + gap)
    for y in range(ya, yb):
        z = zw(y)
        for x in xs:
            M.box('body', x, y, z, x + 3, y + 1, z + 3, LOG if (y // 7 + salt) % 5 else LOG_D, force=True)
        if (y - ya) % 20 == 0:
            M.box('body', cx - gap - 6, y, z - 2, cx + gap + 6, y + 3, z, FRAME, force=True)   # 橫枕木（滑道底下）
            base = ZD if y < ys else 0
            for x in xs:
                M.box('body', x - (1 if y >= ys else 0), y, base, x + 3 + (1 if y >= ys else 0), y + 3, z - 2, WOOD_G if y >= ys else LOG_D, force=True)
    return zw


def slip_ladder(M, x0, y0, z1):
    """船台尾端旁的上下梯（木）：兩根側木從 z 0 到 z1、每 0.3 m 一級。"""
    for x in (x0, x0 + 6):
        M.box('body', x, y0, 0, x + 1, y0 + 1, z1, FRAME, force=True)
    for z in range(2, z1, 3):
        M.box('body', x0, y0, z, x0 + 7, y0 + 1, z + 1, FRAME, force=True)


def back_edge(M, X, Y, ZD, step=40, skip=()):
    """背面（朝水）那一條邊：護舷木樁每 step 格、從 z 0 到平台面上 0.2 m（貼著板外緣），一道橫護木；skip ＝ 不擺的 x 範圍（船台的口）。"""
    for x in range(step // 2, X - 2, step):
        if any(a - 3 <= x <= b for a, b in skip):
            continue
        M.box('body', x, Y - 2, 0, x + 3, Y, ZD + 2, WOOD_D, force=True)
    for a, b in [(0, X)] if not skip else [(0, skip[0][0])] + [(skip[i][1], skip[i + 1][0]) for i in range(len(skip) - 1)] + [(skip[-1][1], X)]:
        if b > a:
            M.box('body', a, Y - 1, ZD - 5, b, Y, ZD - 2, WOOD_D, force=True)


def lantern(T, name, at):
    T.models.append({'name': name, 'source': LANTERN, 'at': list(at), 'pivot': LANTERN_PIVOT, 'meta': {'kind': 'light'}})


def barrel(T, name, x, y, z=0):
    T.models.append({'name': name, 'source': BARREL, 'at': [x, y, z], 'pivot': [6, 6, 0], 'meta': {}})


def crate(T, name, x, y, z=0):
    T.models.append({'name': name, 'source': CRATE, 'at': [x, y, z], 'pivot': [6, 6, 0], 'meta': {}})


def plank_stack(T, x0, x1, y0, rows=4):
    """一落木板（沿 x、每層 0.4 m 寬、0.1 m 厚，層間墊兩根短方木）。"""
    for k in range(rows):
        z = k * 2
        T.box('body', x0 + 4, y0, z, x0 + 7, y0 + 12, z + 1, FRAME, force=True)
        T.box('body', x1 - 7, y0, z, x1 - 4, y0 + 12, z + 1, FRAME, force=True)
        T.box('body', x0, y0, z + 1, x1, y0 + 12, z + 2, BOARD if k % 2 else BOARD_D, force=True)


def work(M, pts):
    """工作點（BUILDING_SPEC §5「工作點」；TASK-0904）：work-<組><號> 站的那一格（腳下是地板）＋ -to 面向（工作檯、絞盤、船骨架的腰高）。
    同一組的點彼此直線走得到；tools/workspots.py 挑的照收（2026-10-31 看過俯視圖），工具挑不到的（工棚工作檯、鋸木架、火槽、船骨架兩側、絞盤推桿）手補。"""
    for nm, x, y, z, tx, ty, tz in pts:
        M.anchor('work-' + nm, x, y, z)
        M.anchor('work-' + nm + '-to', tx, ty, tz)


def finish(B, W, d0, slip=None):
    """收尾：meta（water、deckz、slip、base 0）、地面 z 0 與平台面、門口在平台面上。"""
    B['meta'] = dict(water=d0, deckz=W.ZD / 10, base=0)
    if slip:
        B['meta']['slip'] = '%g,%g,%g' % (slip[0], slip[1], W.ZD / 10)
    B['ground'] = (0, W.ZD)
    B['door_deck'] = True
    B['style'] = 'common'
    return B


# ─────────────────────────────── 船棚（水上版）8 × 16 m ───────────────────────────────
def boat_shed_water():
    """船棚水上版（WATER['boat-shed']：8 × 16、d0 4、船台 8 × 4 m、尾端水深 1.2 m）：陸上版（trailhead quay.py boat_shed）反過來 ——
    正面（碼頭、棧橋那一邊）一道木板牆開一扇門（人從碼頭進）、**背面敞開朝水**；兩條圓木滑道從門裡一路斜下去、穿過背面那 8 m 的船台口進水裡；
    一艘 9 m 小艇擱在滑道上面那一段的墊木上（不碰水）；門裡一座絞盤把船拉上來；側邊槳架、繩盤。棚踩在遊戲畫的平台上，船台口底下自己立樁。"""
    X, Y, ZD = 80, 160, 20
    W = Water(X, Y, ZD + 72, ZD, slip=(20, 60, 80))
    T, M = W.T, W.M
    R = (4, 4, 76, 158)                                                # 柱圍的範圍
    board_walls(T, (R[0], R[1], R[2], R[1] + 2), 0, 36, 2, posts=False)   # 正面木板牆（門開在中間）
    put_part(T, 'door-plank', '船棚-門', 'front', (R[0], R[1], R[2], R[1] + 2), 18, 0, 2)
    posts = [(x, y) for y in range(R[1], R[3] - 2, 26) for x in (R[0], R[2] - 2)] + [(R[0], R[3] - 2), (R[2] - 2, R[3] - 2)]
    for (px, py) in posts:
        T.box('body', px, py, 0, px + 2, py + 2, 36, FRAME)
    for y0 in sorted({py for _, py in posts}):
        T.box('body', R[0], y0, 36, R[2], y0 + 2, 38, FRAME)
    for x0 in (R[0], R[2] - 2):
        T.box('body', x0, R[1], 36, x0 + 2, R[3], 38, FRAME)
    shingle_roof(T, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 38, 'p': 0.62, 'over': (4, 4, 4, 2), 'gable': 'y'}], salt=899)
    gable_wall(T, R[0], R[2], R[1], R[1] + 2, 38, 0.62)                # 正面的山牆
    capstan(T, 40, 16, bars=False)                                     # 拉船的絞盤（門裡，推桿收起來 ⇒ 不擋門）
    for py in (40, 70):                                                # 槳架（右邊，平台上那一段）
        T.box('body', 66, py, 0, 68, py + 2, 26, FRAME)
    for z in (8, 16, 24):
        T.box('body', 66, 40, z, 68, 72, z + 1, FRAME)
    for py in range(44, 70, 6):
        rope_line(T, (63.5, py + 0.5, 0.5), (66.5, py + 0.5, 25.5), FLOOR)
    rope_coil(T, 14, 30)
    barrel(T, '酒桶-1', 12, 52)
    lantern(T, '燈籠-門', [26.5, R[1] + 2, 26.5])                      # 門裡掛一盞（作品有燈籠 ⇒ 不自動補門口燈）
    T.anchor('door', 18, 0, 0)
    T.anchor('lot-0', 0, 0, 0)
    M = W.done()
    ys = Y - 80                                                        # 船台口（遊戲不鋪板）：y 80～160、x 20～60
    zw = ways(M, 40, 8, 28, ZD + 6, Y, 0, ys, ZD, salt=1)
    for y in (40, 66, 92):                                             # 小艇的墊木：架在兩條滑道上，頂面水平（z ZD ＋ 12）
        M.box('body', 30, y, zw(y) + 3, 50, y + 3, ZD + 12, FRAME, force=True)
    M.models.append({'name': '小艇', 'source': 'basecamp-ember-01m-boat', 'at': [40, 67, ZD + 12], 'pivot': [90, 26, 0], 'rotate': [0, 0, 90], 'meta': {}})   # 9 m：y 22～112，尾端過了船台口 3 m、在水面上 1 m 多
    rope(M, '絞盤繩', (40.5, 18.5, ZD + 6.5), (40.5, 40.5, ZD + 12.5), thick=0.5)   # 絞盤的繩 ⇒ 第一根墊木（拴船首的環在那裡；真的繩，TASK-0899）
    slip_ladder(M, 8, Y - 2, ZD + 1)
    work(M, [('a1', 40, 74, 21, 40, 67, 30), ('a2', 26, 74, 21, 32, 67, 30), ('b1', 40, 60, 21, 40, 67, 30), ('c1', 56, 37, 21, 49, 35, 30)])   # 小艇底下、槳架前
    return finish({'key': 'boat-shed-water', 'title': '船棚水上版（共用：兩坡木瓦頂的長棚、正面木板牆與門、背面敞開；兩條滑道從棚裡斜進水、一艘 9 m 小艇、拉船的絞盤、槳架）',
                   'use': 'boat-shed', 'lot': (8, 16), 'M': M, 'layers': {'body': '棚架、船台與擺設', 'roof': '屋頂'}, 'px': 3}, W, 4, (8, 4))


# ─────────────────────────────── 小船廠（水上版）40 × 32 m ───────────────────────────────
def shipyard_small_water():
    """小船廠水上版（WATER['shipyard-small']：40 × 32、d0 12、船台 20 × 8 m、尾端水深 2.5 m）：陸上版（ame shipyard.py）照碼頭排 ——
    中間一條船台從正面後 2 m 起、一路斜過背面 20 m 的船台口進水裡，上面一艘 16 m 的 sloop 骨架（下半已釘板；整艘在水面上）；
    左前工棚、鋸木架、瀝青鍋；右前木板倉庫、蒸彎木板的火槽；背面平台兩邊是木料場（原木、木板落）、兩座絞盤、繩盤，背面邊上護舷、船台口旁一道梯。"""
    X, Y, ZD = 400, 320, 20
    W = Water(X, Y, ZD + 90, ZD, slip=(160, 240, 120), rooms=[(250, 10, 384, 96)])
    T, M = W.T, W.M
    tool_shed(T, 16, 14, 136, 64, 30, salt=161)
    saw_trestle(T, 30, 82)
    tar_kettle(T, 120, 96)
    board_store(T, (250, 10, 384, 96), 34, salt=162)
    T.box('body', 250, 104, 0, 310, 112, 2, RUBBLE)                    # 蒸彎木板的火槽（倉庫前）
    T.box('body', 252, 106, 1, 308, 110, 2, EMBER, force=True)
    for x in (248, 310):
        T.box('body', x, 106, 0, x + 2, 110, 6, RUBBLE)
    T.box('body', 248, 106, 6, 312, 110, 7, FLOOR)
    log_pile(T, 20, 140, 150, 3, 5)                                    # 背面左：原木堆、木板落
    plank_stack(T, 30, 130, 200)
    capstan(T, 100, 262)
    rope_coil(T, 40, 270)
    log_pile(T, 270, 380, 150, 2, 5)                                   # 背面右
    plank_stack(T, 270, 370, 200, 3)
    capstan(T, 300, 262)
    rope_coil(T, 360, 280)
    for x in range(30, X - 20, 60):                                    # 背面邊上的繫纜木樁（船台口讓開）
        if not 150 <= x <= 250:
            bollard(T, x, Y - 8, 9)
    barrel(T, '瀝青桶-1', 136, 88)
    crate(T, '貨箱-棚', 26, 22)
    lantern(T, '燈籠-倉庫', [298.5, 10, 22.5])
    T.anchor('door', 200, 0, 0)
    T.anchor('lot-0', 0, 0, 0)
    M = W.done()
    ys = Y - 200                                                       # 船台口：y 120～320、x 160～240
    zw = ways(M, 200, 14, 20, ZD + 30, Y, 0, ys, ZD, salt=2)
    hull_frame(M, 200, 40, 200, 52, 26, zw(40) + 3, zw(200) + 3)      # 船骨架：龍骨坐在橫枕木上（滑道頂 ＋ 0）
    M.clear(150, 0, 0, 250, ys, ZD)                                    # 平台上那一段：龍骨墩只從平台面起（hull_frame 從 z 0 起畫）
    back_edge(M, X, Y, ZD, skip=[(160, 240)])
    slip_ladder(M, 150, Y - 2, ZD + 1)
    work(M, [('a1', 145, 160, 21, 138, 159, 30), ('b1', 14, 160, 21, 22, 159, 30), ('c1', 264, 161, 21, 272, 156, 30),          # 木料場（工具挑的）
             ('d1', 370, 144, 21, 370, 152, 30), ('d2', 342, 144, 21, 342, 152, 30), ('d3', 314, 144, 21, 314, 152, 30), ('d4', 286, 144, 21, 286, 152, 30),
             ('e1', 120, 217, 21, 120, 210, 30), ('e2', 43, 217, 21, 43, 210, 30), ('f1', 120, 194, 21, 120, 202, 30), ('f2', 43, 194, 21, 43, 202, 30),
             ('g1', 165, 90, 21, 178, 90, 30), ('h1', 235, 90, 21, 222, 90, 30),                                                  # 船骨架兩側（手補）
             ('i1', 36, 46, 21, 36, 56, 30), ('j1', 50, 100, 21, 50, 88, 30), ('k1', 280, 120, 21, 280, 108, 24)])                   # 工棚工作檯、鋸木架、蒸板火槽（手補）
    return finish({'key': 'shipyard-small-water', 'title': '小船廠水上版（共用：船台從平台斜進水、上面一艘 16 m 的 sloop 骨架；工棚、鋸木架、瀝青鍋、木板倉庫、蒸板火槽、木料場、兩座絞盤、護舷）',
                   'use': 'shipyard-small', 'lot': (40, 32), 'M': M, 'layers': {'body': '船台、骨架與設施', 'roof': '屋頂'}, 'px': 2}, W, 12, (20, 8))


# ─────────────────────────────── 大船廠（水上版）80 × 52 m ───────────────────────────────
def shipyard_large_water():
    """大船廠水上版（WATER['shipyard-large']：80 × 52、d0 20、船台 32 × 14 m、尾端水深 4 m）：陸上版（ame shipyard.py）的設施照搬到前面 20 m ——
    左前長倉庫、鐵匠鋪（毛石、火爐、煙囪）、木料堆、鋸木架；右前桅杆棚；中間一條寬船台從正面後 4 m 起、斜過背面 32 m 的船台口進水，上面一艘 26 m 的船骨架（整艘在水面上）；
    背面平台：左邊起桅的起重架（sheers，兩根粗圓材叉成 A 字、前後穩索）站在背面邊上、右邊剛鋪的龍骨與艏艉柱（第二艘，擱在平台上的墩上）、絞盤三座、瀝青鍋、繩盤；背面邊上舊砲倒插的繫纜樁、護舷。"""
    X, Y, ZD = 800, 520, 25
    W = Water(X, Y, ZD + 150, ZD, slip=(330, 470, 200), rooms=[(20, 20, 300, 100), (20, 120, 90, 180)])
    T, M = W.T, W.M
    board_store(T, (20, 20, 300, 100), 40, salt=171)
    mx0, mx1 = 500, 780                                                # 桅杆棚
    posts = [(x, 22) for x in range(mx0 + 2, mx1 - 2, 60)] + [(x, 76) for x in range(mx0 + 2, mx1 - 2, 60)] + [(mx1 - 4, 22), (mx1 - 4, 76)]
    lean_roof_posts(T, mx0, 20, mx1, 80, 34, 0.2, 'front', shingle_color, posts, salt=172)
    for i, y in enumerate((34, 46, 58)):
        T.box('body', mx0 + 20, y, 0, mx1 - 30 - i * 40, y + 6, 6, LOG)
    sm = (20, 120, 90, 180)                                            # 鐵匠鋪
    rubble_walls(T, sm, 0, 28, 4, salt=173)
    put_part(T, 'door-plank', '鐵匠鋪-門', 'front', sm, 55, 0, 4)
    top = shingle_roof(T, [{'x0': sm[0], 'y0': sm[1], 'x1': sm[2], 'y1': sm[3], 'ze': 28, 'p': 0.7, 'over': (3, 3, 3, 3)}], salt=174)
    hearth(T, 30, 160, 50, 176, hanger=False)
    free_part(T, 'chimney', '鐵匠鋪-煙囪', (32, 164, top[(36, 167)] - 10))
    log_pile(T, 110, 290, 130, 3, 5)
    saw_trestle(T, 130, 168)
    log_pile(T, 510, 770, 110, 2, 5)
    tar_kettle(T, 520, 160)
    barrel(T, '瀝青桶-1', 536, 152)
    barrel(T, '瀝青桶-2', 548, 152)
    # 背面平台
    ax, ay = 140, Y - 30                                               # 起桅的起重架（站在背面邊上，頭往水那一邊傾）
    feet = [(ax - 34, ay - 40), (ax + 34, ay - 40)]
    hx, hy, hz = ax, ay - 2, 128
    for (fx, fy) in feet:
        rubble_walls(T, (fx - 7, fy - 7, fx + 7, fy + 7), 0, 4, 6, salt=fx)
        T.box('body', fx - 1, fy - 1, 0, fx + 1, fy + 1, 4, RUBBLE)       # 墩心（rubble_walls 只砌一圈、中間 2 × 2 空著 ⇒ 底下有地板就封成空腔）
        spar(T, (fx + 0.5, fy + 0.5, 4), (hx + 0.5 + (fx - hx) * 0.05, hy + 0.5, hz + 6), 3.0)
    for z in range(hz - 2, hz + 8):
        for x in range(hx - 6, hx + 7):
            for y in range(hy - 4, hy + 5):
                if (abs(x - hx) >= 4 or abs(y - hy) >= 4) and math.hypot(x - hx, (y - hy) * 1.5) <= 6.5:
                    T.put('body', x, y, z, ROPE, force=True)
    T.box('body', ax - 2, 260, 0, ax + 2, 264, 16, FRAME)              # 後穩索的地樁
    rope(T, '起桅架-後穩索', (hx + 0.5, hy - 3.5, hz + 4), (ax + 0.5, 262.5, 15.5), thick=0.8)   # 起桅架的繩都是真的繩（TASK-0899）
    rope(T, '起桅架-吊滑車索', (hx + 0.5, hy + 0.5, hz - 2), (hx + 0.5, hy + 0.5, hz - 10), thick=0.8)
    tackle_block(T, hx, hy, hz - 18, 8)
    rope(T, '起桅架-吊索', (hx + 0.5, hy + 0.5, hz - 18), (hx + 0.5, hy + 0.5, 40), thick=0.7)
    tackle_block(T, hx, hy, 34, 6)
    rope(T, '起桅架-拉索', (hx + 2.5, hy + 0.5, hz - 12), (ax + 0.5, 300.5, 3.5), thick=0.7)   # 拉的那一頭 ⇒ 導向滑車 ⇒ 絞盤
    T.box('body', ax - 2, 298, 0, ax + 3, 304, 3, FRAME)
    capstan(T, ax, 280)
    for y in range(240, 450):                                          # 第二艘：剛鋪的龍骨（擱在平台的墩上）、艏艉柱
        T.box('body', 649, y, 8, 651, y + 1, 11, FRAME)
        if (y - 240) % 20 == 0:
            T.box('body', 646, y, 0, 654, y + 3, 8, LOG_D)
    for y in (240, 448):
        T.box('body', 649, y, 8, 651, y + 2, 60, FRAME)
    capstan(T, 560, 300)
    capstan(T, 740, 300)
    rope_coil(T, 260, 300)
    rope_coil(T, 560, 470)
    log_pile(T, 220, 300, 380, 2, 5)
    plank_stack(T, 700, 780, 380)
    for x in range(40, X - 20, 160):                                   # 背面邊上舊砲倒插的繫纜樁（船台口、起重架讓開）
        if not (300 <= x <= 500 or 100 <= x <= 180):
            cannon_bollard(T, x, Y - 8)
    lantern(T, '燈籠-倉庫', [140.5, 20, 26.5])
    lantern(T, '燈籠-起重架', [ax + 0.5, 260, 13])
    T.anchor('door', 400, 0, 0)
    T.anchor('lot-0', 0, 0, 0)
    M = W.done()
    ys = Y - 320                                                       # 船台口：y 200～520、x 330～470
    zw = ways(M, 400, 26, 40, ZD + 24, Y, 0, ys, ZD, salt=3)
    hull_frame(M, 400, 90, 350, 84, 46, zw(90) + 3, zw(350) + 3, plank=0.5)
    M.clear(320, 0, 0, 480, ys, ZD)
    back_edge(M, X, Y, ZD, step=50, skip=[(330, 470)])
    for x in (320, 474):
        slip_ladder(M, x, Y - 2, ZD + 1)
    work(M, [('a1', 295, 140, 26, 288, 139, 35), ('a2', 365, 189, 26, 372, 188, 35), ('a3', 365, 174, 26, 372, 175, 35), ('b1', 104, 140, 26, 112, 139, 35),   # tools/workspots.py 挑的
             ('c1', 434, 189, 26, 427, 188, 35), ('c2', 434, 174, 26, 427, 175, 35), ('c3', 504, 121, 26, 512, 116, 35), ('d1', 305, 391, 26, 298, 386, 35),
             ('e1', 214, 391, 26, 222, 386, 35), ('f1', 775, 121, 26, 768, 116, 35), ('g1', 420, 134, 26, 422, 140, 35), ('h1', 380, 134, 26, 378, 140, 35),
             ('i1', 290, 374, 26, 290, 382, 35), ('i2', 276, 374, 26, 276, 382, 35), ('i3', 262, 374, 26, 262, 382, 35), ('i4', 248, 374, 26, 248, 382, 35),
             ('i5', 234, 374, 26, 234, 382, 35), ('j1', 760, 104, 26, 760, 112, 35), ('j2', 746, 104, 26, 746, 112, 35), ('j3', 732, 104, 26, 732, 112, 35)])
    return finish({'key': 'shipyard-large-water', 'title': '大船廠水上版（共用：寬船台從平台斜進水、上面一艘 26 m 的船骨架；起桅的起重架、剛鋪的龍骨、長倉庫、桅杆棚、鐵匠鋪、木料、三座絞盤、護舷）',
                   'use': 'shipyard-large', 'lot': (80, 52), 'M': M, 'layers': {'body': '船台、骨架與設施', 'roof': '屋頂'}, 'px': 1}, W, 20, (32, 14))


# ─────────────────────────────── 修船碼頭（水上版）32 × 20 m ───────────────────────────────
def careening_wharf_water():
    """修船碼頭水上版（WATER['careening-wharf']：32 × 20、d0 8、平台底下 ≥ 2 m）：陸上版（ame harbour.py）是「背面一道木碼頭面」，水上版整塊就是伸進水裡的木平台 ——
    船靠在背面那一條邊（English Harbour 那種 careening wharf：把船拉倒、修水線下的船殼）。
    前面左邊木板倉庫、右邊三座工具棚與木料；中間絞盤屋（四根木柱、四坡頂）與另一座露天絞盤，兩條拉船的繩從絞盤經背面邊上的導向滑車伸出去（船那一頭不在地塊裡 ⇒ 繩收在滑車）；
    背面邊上一排粗繫纜樁（每 5 m）、厚護舷、兩道下水的梯；煮瀝青的鍋、瀝青桶。"""
    X, Y, ZD = 320, 200, 15
    W = Water(X, Y, ZD + 70, ZD, rooms=[(10, 10, 120, 80)])
    T, M = W.T, W.M
    board_store(T, (10, 10, 120, 80), 34, salt=181)
    for i, x0 in enumerate((206, 250)):
        tool_shed(T, x0, 12, x0 + 36, 48, 28, salt=186 + i)
    tool_shed(T, 206, 58, 242, 94, 28, salt=188)
    log_pile(T, 250, 306, 72, 3, 4)
    hx0, hy0, hx1, hy1 = 130, 100, 186, 150                            # 絞盤屋
    for (px, py) in ((hx0, hy0), (hx1 - 4, hy0), (hx0, hy1 - 4), (hx1 - 4, hy1 - 4)):
        T.box('body', px, py, 0, px + 4, py + 4, 30, FRAME)
    for (a, b) in ((hy0, hy0 + 4), (hy1 - 4, hy1)):
        T.box('body', hx0, a, 28, hx1, b, 30, FRAME)
    shingle_roof(T, [{'x0': hx0, 'y0': hy0, 'x1': hx1, 'y1': hy1, 'ze': 30, 'p': 0.7, 'over': (4, 4, 4, 4)}], salt=183)
    capstan(T, 158, 125)
    capstan(T, 250, 130)
    tar_kettle(T, 90, 120)
    barrel(T, '瀝青桶', 104, 104)
    rope_coil(T, 60, 150)
    rope_coil(T, 290, 160)
    for k, (cx, cy, bx) in enumerate(((158, 125, 120), (250, 130, 220))):   # 拉船的繩：絞盤 ⇒ 背面邊上的導向滑車（掛在粗樁上）
        T.box('body', bx - 3, Y - 12, 0, bx + 3, Y - 6, 14, FRAME)
        tackle_block(T, bx, Y - 10, 8, 5)
        rope(T, '拉船索-%d' % (k + 1), (cx + 0.5, cy + 4.5, 5.5), (bx + 0.5, Y - 10.5, 10.5), thick=0.6)   # 真的繩（TASK-0899）
        rope(T, '拉船索-%d-出' % (k + 1), (bx + 0.5, Y - 8.5, 9.5), (bx + 0.5, Y - 1.5, 4.5), thick=0.6, slack=1.02)
    for x in range(30, X - 10, 50):
        if abs(x - 120) > 12 and abs(x - 220) > 12:
            bollard(T, x, Y - 8, 11)
    crate(T, '貨箱-門口', 30, 92)
    barrel(T, '酒桶-門口', 50, 92)
    lantern(T, '燈籠-絞盤屋', [156.5, hy0 + 4, 18.5])
    T.anchor('door', 65, 0, 0)
    T.anchor('lot-0', 0, 0, 0)
    M = W.done()
    back_edge(M, X, Y, ZD, step=30)
    for x in (60, 290):
        slip_ladder(M, x, Y - 2, ZD + 1)
    work(M, [('a1', 243, 83, 16, 244, 82, 25), ('b1', 311, 83, 16, 304, 80, 25), ('c1', 215, 182, 16, 220, 188, 25), ('d1', 115, 182, 16, 120, 188, 25),   # tools/workspots.py 挑的
             ('e1', 129, 194, 16, 121, 191, 25), ('e2', 268, 93, 16, 268, 84, 25), ('f1', 229, 194, 16, 221, 191, 25), ('f2', 296, 93, 16, 296, 84, 25),
             ('h1', 296, 66, 16, 296, 74, 25), ('h2', 268, 66, 16, 268, 74, 25),
             ('i1', 142, 125, 16, 158, 125, 25), ('j1', 174, 125, 16, 158, 125, 25), ('k1', 250, 113, 16, 250, 130, 25), ('l1', 250, 147, 16, 250, 130, 25)])   # 推絞盤（手補）
    return finish({'key': 'careening-wharf-water', 'title': '修船碼頭水上版（共用：伸進水裡的木平台、船靠背面邊上；絞盤屋與兩座絞盤、導向滑車、粗繫纜樁與厚護舷、木板倉庫、三座工具棚、瀝青鍋、下水的梯）',
                   'use': 'careening-wharf', 'lot': (32, 20), 'M': M, 'layers': {'body': '平台上的設施', 'roof': '屋頂'}, 'px': 3}, W, 8)


ALL = [boat_shed_water, shipyard_small_water, shipyard_large_water, careening_wharf_water]
