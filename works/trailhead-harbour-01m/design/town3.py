# 城鎮共用建築第三批（TASK-0847；Tim 2026-10-23「繼續增加城鎮的共用建築吧 GO」）—— 魚市、瞭望塔（共用 common）、監獄、小教堂（加勒比海 carib）。
# 工具同 quay.py（ame-carib-civic-01m/design 的 harbour.py ⇒ civic.py ⇒ summit-carib-01m 的調色盤、Model、屋頂、部件）；
#   townpub.py 借長桌、山牆（end_gable）。座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 史料：作品 references/README.md 第三批那一節；查不到的都寫「設計」。
import os, sys, math
from quay import *                                                     # noqa: F401  rope_line、spar、bollard、tackle_block ＋ harbour／civic／carib 的全部
from townpub import end_gable, trestle_table, bench                    # noqa: E402

FISH, FISH_B = 151, 146          # 攤上的魚（銀藍）、灰一點的魚
SHELL, SHELL_D = 44, 36          # 龜殼（深綠）、殼上的紋


def barred(M, face, R, c, z0, w=8, h=8, t=4):
    """鐵條窗：在牆 R＝(X0, Y0, X1, Y1) 的 face 面、開口中心 c（front／back 量 x、left／right 量 y）、底 z0 開 w × h 的洞，
    牆厚中間立一排鐵條（每隔一格一根）＋一道橫條。鐵條上下都頂著牆 ⇒ 不會浮空。"""
    X0, Y0, X1, Y1 = R
    us = range(c - w // 2, c - w // 2 + w)
    if face in ('front', 'back'):
        ys = range(Y0, Y0 + t) if face == 'front' else range(Y1 - t, Y1)
        M.clear(us.start, ys.start, z0, us.stop, ys.stop, z0 + h, 'body')
        yb = ys.start + t // 2
        for x in us:
            if (x - us.start) % 2 == 1:
                M.box('body', x, yb, z0, x + 1, yb + 1, z0 + h, IRON)
        M.box('body', us.start, yb, z0 + h // 2, us.stop, yb + 1, z0 + h // 2 + 1, IRON)
    else:
        xs = range(X0, X0 + t) if face == 'left' else range(X1 - t, X1)
        M.clear(xs.start, us.start, z0, xs.stop, us.stop, z0 + h, 'body')
        xb = xs.start + t // 2
        for y in us:
            if (y - us.start) % 2 == 1:
                M.box('body', xb, y, z0, xb + 1, y + 1, z0 + h, IRON)
        M.box('body', xb, us.start, z0 + h // 2, xb + 1, us.stop, z0 + h // 2 + 1, IRON)


def lantern(M, name, at):
    """夜裡的燈（外部模型 summit-rocher-01m-lantern）：at ＝ 掛的那一面（柱或牆的正面）。作品有燈籠 ⇒ townmodels 不再自動補門口燈。"""
    M.models.append({'name': name, 'source': 'summit-rocher-01m-lantern', 'at': list(at), 'pivot': [4.5, 13, 15.5], 'meta': {'kind': 'light'}})


# ─────────────────────────────── 魚市 12 × 10 m ───────────────────────────────
def fish_market():
    """魚市（fish-market）：碼頭邊一座開敞的棚 —— 石板地好沖洗、三張攤桌擺魚、一張擺翻過來的海龜、市場官的公秤；棚後兩座曬魚架。
    - 照什麼：TOWN_BUILD §1.1.7「魚市：下游」；ame 的研究（research_civic.md §10.4）：Port Royal 最晚 1671 年有市場官、用他自己的公秤（beam scales）、
      禁用提秤（LAWS84）；海龜從 Caymanes 運來、養在港內的方形木柵欄、約 2000 人每天吃龜肉（SL、CSP）〔讀過〕。
      魚市、肉市有沒有獨立建築〔沒查到〕⇒ 開敞的茅草棚、攤桌、曬魚架都是設計。
    - 生成器擺在碼頭臨陸那一側（world/town.js ⑦b，同修船：離廣場遠的先）⇒ 正面（y 0）朝碼頭。"""
    X, Y, Z = 120, 100, 70
    M = Model((X, Y, Z))
    R = (4, 6, 116, 66)                                                # 柱子圍的範圍（11.2 × 6 m）
    M.box('body', R[0], R[1], 0, R[2], R[3], 1, RUBBLE)               # 石板地
    xs = [4, 31, 58, 85, 114]
    for px in xs:
        for py in (R[1], R[3] - 2):
            M.box('body', px, py, 1, px + 2, py + 2, 30, FRAME)
    for py in (R[1], R[3] - 2):                                        # 柱頭的縱梁（沿 x）
        M.box('body', R[0], py, 30, R[2], py + 2, 32, FRAME)
    for px in (R[0], R[2] - 2):
        M.box('body', px, R[1], 30, px + 2, R[3], 32, FRAME)
    thatch_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 32, 'p': 0.7, 'over': (4, 4, 5, 5), 'gable': 'x'}], salt=847)
    # 攤桌（前排三張）：桌面擺一排一排的魚
    for (x0, x1) in ((10, 34), (44, 54), (66, 110)):
        trestle_table(M, x0, x1, 12, 22, 8)
        for x in range(x0 + 2, x1 - 2, 4):
            M.box('body', x, 13, 9, x + 2, 21, 10, FISH if (x // 4) % 3 else FISH_B)
    # 後排：海龜那一張（翻過來的龜：殼朝下、四肢朝上）
    trestle_table(M, 78, 110, 44, 58, 8)
    for x in range(82, 106):
        for y in range(45, 57):
            if ((x + 0.5 - 94) / 12) ** 2 + ((y + 0.5 - 51) / 6) ** 2 <= 1:
                M.put('body', x, y, 9, SHELL)
                if ((x + 0.5 - 94) / 9) ** 2 + ((y + 0.5 - 51) / 4) ** 2 <= 1:
                    M.put('body', x, y, 10, SHELL_D if (x + y) % 5 == 0 else FISH_B)
    for (fx, fy) in ((85, 46), (101, 46), (85, 54), (101, 54)):       # 四肢
        M.box('body', fx, fy, 10, fx + 2, fy + 2, 12, SHELL)
    # 市場官的公秤（等臂秤）：一根柱、橫桿、兩個盤（鐵）
    M.box('body', 38, 44, 1, 40, 46, 24, FRAME)
    M.box('body', 29, 44, 24, 49, 46, 25, IRON)
    for cx in (30, 47):
        M.box('body', cx, 44, 16, cx + 1, 46, 24, IRON)
        M.box('body', cx - 3, 42, 15, cx + 4, 48, 16, IRON)
    # 棚後的曬魚架：兩根柱＋兩道橫桿，桿上一排剖開的魚往下掛
    for (x0, x1) in ((8, 52), (64, 108)):
        for px in (x0, x1 - 2):
            M.box('body', px, 82, 0, px + 2, 84, 24, FRAME)
        for zr in (14, 22):
            M.box('body', x0, 82, zr, x1, 84, zr + 1, FRAME)
            for x in range(x0 + 3, x1 - 3, 3):
                M.box('body', x, 82, zr - 5, x + 2, 83, zr, FISH if (x // 3 + zr) % 4 else FISH_B)
    M.models += [{'name': '酒桶-1', 'source': 'summit-rocher-01m-barrel', 'at': [14, 36, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '酒桶-2', 'source': 'summit-rocher-01m-barrel', 'at': [14, 50, 1], 'pivot': [6, 6, 0], 'meta': {}},
                 {'name': '貨箱-1', 'source': 'summit-rocher-01m-crate', 'at': [60, 50, 1], 'pivot': [6, 6, 0], 'meta': {}}]
    lantern(M, '燈籠-中柱', (59.5, R[1], 27))
    M.anchor('door', 60, 2, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'fish-market', 'title': '魚市（共用：開敞的茅草棚、石板地、三張攤桌、翻過來的海龜、市場官的公秤；棚後兩座曬魚架）',
            'use': 'fish-market', 'lot': (12, 10), 'M': M, 'style': 'common', 'layers': {'body': '棚架、攤桌與曬魚架', 'roof': '屋頂'}}


# ─────────────────────────────── 瞭望塔 6 × 6 m ───────────────────────────────
def watchtower():
    """瞭望塔（watchtower）：毛石台基上四根木柱、兩層斜撐、頂上一層平台（欄杆、半邊茅草遮陽頂）、平台角上一座堆好柴的烽火籃；裡面一架木梯。
    - 照什麼：TOWN_BUILD §1.1.7「燈塔年代對不上 ⇒ 1720 年以前的加勒比海用瞭望塔（watchtower）＋烽火」「瞭望塔：港口外最高的岬角」。
      17 世紀加勒比海瞭望塔的形制〔沒查到〕⇒ 木構、高度（平台 11.8 m）、烽火籃都是設計。
    - 生成器照碉堡那一套找高處、看得到港口（world/town.js ⑦b）⇒ 正面（y 0）朝港口、梯子的上下口在正面。"""
    X, Y, Z = 60, 60, 160
    M = Model((X, Y, Z))
    rubble_walls(M, (8, 8, 52, 52), 0, 8, 22, salt=8471)               # 實心的台基（0.8 m 高）
    M.box('body', 24, 3, 0, 36, 8, 4, RUBBLE)                         # 台基正面的兩級石階
    M.box('body', 24, 5, 4, 36, 8, 8, RUBBLE)
    P = [(10, 10), (47, 10), (10, 47), (47, 47)]                       # 四根角柱 3 × 3
    for (px, py) in P:
        M.box('body', px, py, 8, px + 3, py + 3, 118, FRAME)
    for zb in (60, 100):                                               # 兩道圈梁
        M.box('body', 10, 10, zb, 50, 13, zb + 2, FRAME)
        M.box('body', 10, 47, zb, 50, 50, zb + 2, FRAME)
        M.box('body', 10, 10, zb, 13, 50, zb + 2, FRAME)
        M.box('body', 47, 10, zb, 50, 50, zb + 2, FRAME)
    for (za, zb) in ((10, 60), (62, 100)):                             # 每一面兩層 X 形斜撐（粗 2 格；六連通）
        for (a, b) in (((11.5, 11.5), (48.5, 11.5)), ((11.5, 48.5), (48.5, 48.5))):
            rope_line(M, (a[0], a[1], za), (b[0], b[1], zb), FRAME)
            rope_line(M, (b[0], b[1], za), (a[0], a[1], zb), FRAME)
            rope_line(M, (a[0] + 1, a[1], za), (b[0] + 1, b[1], zb), FRAME)
        for (a, b) in (((11.5, 11.5), (11.5, 48.5)), ((48.5, 11.5), (48.5, 48.5))):
            rope_line(M, (a[0], a[1], za), (b[0], b[1], zb), FRAME)
            rope_line(M, (b[0], b[1], za), (a[0], a[1], zb), FRAME)
    M.box('body', 4, 4, 118, 56, 56, 120, FLOOR)                       # 平台（往外挑 0.6 m）
    M.box('body', 4, 4, 117, 56, 6, 118, FRAME)                        # 平台邊的托梁
    M.box('body', 4, 54, 117, 56, 56, 118, FRAME)
    M.clear(14, 13, 117, 24, 18, 120)                                 # 上下口（先挖、再立梯子 ⇒ 梯腳一路接到平台上面當扶手）
    # 梯子：台基頂上靠正面那一側、爬到平台的上下口
    for rx in (15, 22):
        M.box('body', rx, 14, 8, rx + 1, 15, 128, FRAME)
    for z in range(11, 118, 3):
        M.box('body', 16, 14, z, 22, 15, z + 1, FRAME)
    for (x0, x1, y, ax) in ((4, 56, 4, 'x'), (4, 56, 55, 'x')):        # 欄杆
        rail(M, x0, x1, y, 120, 10, 'body', FRAME, axis=ax)
    for x in (4, 55):
        rail(M, 4, 56, x, 120, 10, 'body', FRAME, axis='y')
    # 遮陽頂：只蓋後半（前半要看得到天、烽火籃在前）；四根柱立在平台上
    top = thatch_roof(M, [{'x0': 4, 'y0': 28, 'x1': 56, 'y1': 56, 'ze': 140, 'p': 0.6, 'over': (2, 2, 2, 2), 'gable': 'x'}], salt=8472)
    for (px, py) in ((5, 29), (53, 29), (5, 53), (53, 53)):
        zt = min(top[(x, y)] for x in range(px, px + 2) for y in range(py, py + 2)) - 1
        M.box('body', px, py, 120, px + 2, py + 2, zt, FRAME)
    # 烽火籃（前右角）：四支鐵腳、一圈鐵籠，裡面堆好的柴（不點 ⇒ 不用火色）
    for (lx, ly) in ((38, 8), (47, 8), (38, 17), (47, 17)):
        M.box('body', lx, ly, 120, lx + 1, ly + 1, 132, IRON)
    for z in range(126, 134):
        for x in range(38, 48):
            for y in range(8, 18):
                edge = x in (38, 47) or y in (8, 17)
                if z == 126 or (edge and (x + y + z) % 2 == 0) or (edge and z == 133):
                    M.put('body', x, y, z, IRON)
                elif not edge and z < 133:
                    M.put('body', x, y, z, LOG_TIP if (x + z) % 4 == 0 else LOG)
    lantern(M, '燈籠-平台', (12, 10, 114))
    M.anchor('door', 30, 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    M.anchor('lookout', 30, 40, 121)                                   # 平台上站人的那一格（之後遊戲拿來放哨兵）
    return {'key': 'watchtower', 'title': '瞭望塔（共用：毛石台基、四柱兩層斜撐的木塔、11.8 m 的平台與欄杆、半邊茅草遮陽頂、烽火籃、木梯）',
            'use': 'watchtower', 'lot': (6, 6), 'M': M, 'style': 'common', 'layers': {'body': '台基、塔身與平台', 'roof': '遮陽頂'}}


# ─────────────────────────────── 監獄 12 × 14 m ───────────────────────────────
def jail():
    """監獄（jail）：臨路一棟刷白的毛石看守屋（看守的桌凳、掛鐐銬的架）、後面一圈毛石高牆圍的放風院、院底一排三間平頂的牢房（cachots）；門口一副枷。
    - 照什麼：ame 的研究（research_civic.md）：早年沒有監獄、犯人在衛兵所上鐐，後來「好幾個島有監獄與地牢（cachots）」（DT2 pp.446–447）；
      1694 年 Saint-Pierre 有 Palais de la Justice 與監獄（LB1 p.78）；Port-de-Paix 1685 年起有監獄、衛兵所（MSM1 pp.698–699）；
      牙買加 1681 年「no prison」、1682 年撥款蓋 gaol、1688 年 gaol 很滿（CSP）〔讀過†〕⇒ 鎮以上有一座。
      監獄、cachot 的形制〔沒查到〕⇒ 平面、牆高、鐵條窗、枷都是設計（毛石刷白照同一套的醫院）。
    - 生成器擺在廣場空著的邊（《印地亞斯法》：cabildo 與監獄圍著廣場〔摘〕）⇒ 港口街、主要道路。"""
    X, Y, Z = 120, 140, 75
    M = Model((X, Y, Z))
    # 放風院的高牆（先砌；前面那一段就是看守屋的後牆 ⇒ 挖掉，等一下照看守屋砌）
    rubble_walls(M, (6, 60, 114, 136), 0, 36, 4, salt=8473)
    M.clear(10, 60, 0, 110, 64, 36)
    M.box('body', 10, 64, 0, 110, 132, 1, EARTH_W)                    # 院子的夯土地
    # 看守屋 10.8 × 5 m：毛石牆腳、上面抹灰刷白、兩坡木瓦頂、兩端刷白的山牆
    R = (6, 14, 114, 64)
    rubble_walls(M, R, 0, 6, 4, salt=8474)
    stucco_walls(M, R, 6, 34, 4, LIME)
    M.box('body', R[0] + 4, R[1] + 4, 0, R[2] - 4, R[3] - 4, 1, RUBBLE)
    for x0, x1 in ((R[0], R[0] + 4), (R[2] - 4, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 34, 0.75, z0=34, color=LIME, edge=LIME)
    M.box('body', 58, 18, 1, 62, 60, 34, LIME)                         # 中間一道隔牆（左看守、右鐐銬）
    put_part(M, 'door-plank', '隔牆-門', 'left', (58, 18, 62, 60), 39, 0, 4)
    put_part(M, 'door-plank', '前-門', 'front', R, 40, 0, 4)
    put_part(M, 'door-plank', '後-門（往院子）', 'back', R, 80, 0, 4)
    for c in (20, 90):
        barred(M, 'front', R, c, 14, 8, 8, 4)
    barred(M, 'left', R, 39, 14, 8, 8, 4)
    barred(M, 'right', R, 39, 14, 8, 8, 4)
    M.anchor('door', 40, R[1] - 1, 0)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 34, 'p': 0.75, 'over': (3, 3, 4, 4), 'gable': 'x'}], salt=8475)
    # 看守屋裡：看守的桌凳（左）、鐐銬架（右：一根橫木掛幾副鐵鐐）
    trestle_table(M, 14, 34, 30, 40, 8)
    bench(M, 14, 34, 44, 47)
    M.box('body', 70, 56, 1, 72, 58, 20, FRAME)
    M.box('body', 104, 56, 1, 106, 58, 20, FRAME)
    M.box('body', 70, 56, 20, 106, 58, 22, FRAME)
    for x in range(74, 104, 6):
        M.box('body', x, 57, 12, x + 1, 58, 20, IRON)
        M.box('body', x - 1, 57, 11, x + 2, 58, 12, IRON)
    # 院底三間牢房（平頂、毛石）：前牆各一扇厚木門，後牆（＝院牆）高處一個鐵條小窗
    C = (10, 104, 110, 132)
    rubble_walls(M, C, 0, 30, 3, salt=8476)
    for x0 in (42, 75):
        M.box('body', x0, C[1], 0, x0 + 3, C[3], 30, RUBBLE)
    M.box('body', C[0], C[1], 30, C[2], C[3], 32, RUBBLE)             # 平頂（石板＋灰漿）
    M.box('body', C[0], C[1], 32, C[2], C[1] + 1, 33, MORTAR)          # 前緣的一道收頭
    for i, cx in enumerate((26, 59, 93)):
        put_part(M, 'door-plank', '牢房-門%d' % (i + 1), 'front', C, cx, 0, 3)
        barred(M, 'back', (6, 60, 114, 136), cx, 24, 6, 6, 4)
    # 院子：一個石水槽
    M.box('body', 90, 76, 0, 106, 84, 6, RUBBLE)
    M.box('body', 92, 78, 1, 104, 82, 6, DARK, force=True)
    # 門口的枷（stocks）：兩根柱、上下兩塊板，板上三個洞
    for px in (14, 30):
        M.box('body', px, 6, 0, px + 2, 8, 12, FRAME)
    M.box('body', 14, 6, 6, 32, 8, 8, FRAME)
    M.box('body', 14, 6, 9, 32, 8, 11, FRAME)
    for hx in (18, 22, 26):
        M.box('body', hx, 6, 8, hx + 2, 8, 9, FRAME)
    M.clear(18, 6, 8, 20, 8, 9); M.clear(22, 6, 8, 24, 8, 9); M.clear(26, 6, 8, 28, 8, 9)
    lantern(M, '燈籠-門', (55.5, R[1], 26.5))
    for L in M.links:                                                  # 門框的腳落在地板那一層 ⇒ 讓給門框（不然部件與地板疊格）
        for k in L['cells']:
            if k[2] == 0 and k in M.cells:
                del M.cells[k]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'jail', 'title': '監獄（毛石刷白的看守屋、兩坡木瓦頂、鐵條窗；毛石高牆圍的放風院、院底三間平頂牢房；門口一副枷）',
            'use': 'jail', 'lot': (12, 14), 'M': M, 'style': 'carib', 'layers': {'body': '看守屋、院牆與牢房', 'roof': '屋頂'}}


# ─────────────────────────────── 小教堂 8 × 12 m ───────────────────────────────
def reed_walls(M, rect, z0, z1, t=2, bay=28):
    """蘆葦牆（叉柱入土 fourches en terre、柱間編蘆葦）：一根一根直的蘆葦（色照欄位雜湊）、中間與頂上兩道綁的橫木；四角與每 bay 格一根柱。"""
    X0, Y0, X1, Y1 = rect
    for z in range(z0, z1):
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                if X0 + t <= x < X1 - t and Y0 + t <= y < Y1 - t:
                    continue
                u = x if y in range(Y0, Y0 + t) or y in range(Y1 - t, Y1) else y
                c = THATCH_B if h01('reed', u, x == X0 or x == X1 - 1, y) < 0.35 else THATCH_A
                M.put('body', x, y, z, FRAME if z in (z0 + 12, z1 - 2, z1 - 1) else c)
    pts = [(X0, Y0), (X1 - 2, Y0), (X0, Y1 - 2), (X1 - 2, Y1 - 2)]
    pts += [(x, y) for y in range(Y0 + bay, Y1 - bay // 2, bay) for x in (X0, X1 - 2)]
    for (cx, cy) in pts:
        M.box('body', cx, cy, z0, cx + 2, cy + 2, z1, FRAME, force=True)


def chapel():
    """小教堂（chapel）：最小型的那一種 —— 叉柱入土、柱間編蘆葦、棕櫚葉（茅草）兩坡頂，4.6 × 8.4 m；祭壇、祭壇旁一個小櫃、幾條長凳；
    門前一支木十字、旁邊一座木架掛一口鐘。
    - 照什麼：summit 的研究（research_1640-1700.md §5）：新堂區的臨時小禮拜堂「叉柱入土、蘆葦圍牆、稻草屋頂，26 × 14 法尺」（LB2 約 p.104）；
      Ance Ferri 的小禮拜堂「叉柱入土、蘆葦圍牆、棕櫚葉屋頂，祭壇旁有個小櫃」（LB2 約 pp.310–311）；Tortuga 有過小禮拜堂（DT1 p.173）〔讀過〕。
      26 × 14 法尺 ＝ 8.44 × 4.55 m ⇒ 84 × 46 格。鐘架、門前的十字、長凳是設計。
    - 城以上多一座（TOWN_BUILD §1.1.3「小教堂可以好幾座」）；生成器擺在主要道路旁。"""
    X, Y, Z = 80, 120, 70
    M = Model((X, Y, Z))
    R = (17, 22, 63, 106)                                              # 4.6 × 8.4 m
    M.box('body', R[0] + 2, R[1] + 2, 0, R[2] - 2, R[3] - 2, 1, EARTH_W)   # 夯土地
    reed_walls(M, R, 0, 26, 2)
    M.clear(34, R[1], 0, 46, R[1] + 2, 22)                             # 門洞（沒有門扇）＋門框
    for px in (32, 46):
        M.box('body', px, R[1], 0, px + 2, R[1] + 2, 24, FRAME, force=True)
    M.box('body', 32, R[1], 22, 48, R[1] + 2, 24, FRAME, force=True)
    for cy in (46, 78):                                                # 兩側的窗洞
        for (x0, x1) in ((R[0], R[0] + 2), (R[2] - 2, R[2])):
            M.clear(x0, cy - 4, 10, x1, cy + 4, 20)
    for y0, y1 in ((R[1], R[1] + 2), (R[3] - 2, R[3])):
        gable_wall(M, R[0], R[2], y0, y1, 26, 0.9, color=THATCH_A, edge=FRAME)
    top = thatch_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 26, 'p': 0.9, 'over': (5, 5, 6, 6), 'gable': 'y'}], salt=8477)
    zt = max(top[(x, R[1])] for x in range(38, 42))                    # 正面屋脊上的木十字
    M.box('roof', 39, R[1], zt, 41, R[1] + 2, zt + 11, FRAME, force=True)
    M.box('roof', 36, R[1], zt + 6, 44, R[1] + 2, zt + 8, FRAME, force=True)
    # 室內：祭壇（木台、白布）、旁邊的小櫃、木十字；四條長凳（中間走道）
    M.box('body', 31, 94, 1, 49, 102, 9, FLOOR)
    M.box('body', 30, 93, 9, 50, 103, 10, LIME)
    M.box('body', 39, 100, 10, 41, 102, 20, FRAME)
    M.box('body', 36, 100, 15, 44, 102, 17, FRAME)
    M.box('body', 52, 96, 1, 58, 102, 12, FRAME)
    M.box('body', 53, 95, 3, 57, 96, 10, SHUT)
    for y in (40, 52, 64, 76):
        for (a, b) in ((22, 36), (44, 58)):
            bench(M, a, b, y, y + 3)
    # 門前：一支木十字（石堆的座）；右前方的鐘架（兩柱一梁，鐘用鐵環掛在梁下）
    M.box('body', 37, 6, 0, 43, 12, 3, RUBBLE)
    M.box('body', 39, 8, 3, 41, 10, 30, FRAME)
    M.box('body', 34, 8, 22, 46, 10, 24, FRAME)
    for px in (64, 74):
        M.box('body', px, 30, 0, px + 2, 32, 32, FRAME)
    M.box('body', 64, 30, 32, 76, 32, 34, FRAME)
    M.box('body', 69, 30, 30, 71, 32, 32, IRON)
    for z in range(22, 30):
        r = 1 + (29 - z) // 2
        for x in range(70 - r - 1, 70 + r + 1):
            for y in range(31 - r - 1, 31 + r + 1):
                M.put('body', x, y, z, BRONZE)
    M.anchor('bell', 70, 31, 26)
    lantern(M, '燈籠-門左', (28.5, R[1], 21))                           # 自己掛：門前有十字 ⇒ townmodels 自動補的門口燈會挑到門裡面那一邊
    M.anchor('door', 40, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'chapel', 'title': '小教堂（叉柱入土、蘆葦牆、棕櫚葉兩坡頂的最小型小禮拜堂；祭壇與小櫃、長凳；門前木十字、木架掛鐘）',
            'use': 'chapel', 'lot': (8, 12), 'M': M, 'style': 'carib', 'layers': {'body': '牆與擺設', 'roof': '屋頂'}}


ALL = [fish_market, watchtower, jail, chapel]
