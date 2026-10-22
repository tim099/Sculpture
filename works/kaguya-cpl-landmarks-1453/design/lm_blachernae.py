# 布雷契耐宮（Blachernae，帕列奧略皇居；Alexios I、Manuel I 擴建，1261 後 Michael VIII 重修）1453：宮殿台地（部分人工堆成）上的皇居 ——
#   背面貼著陸牆（Manuel 牆、阿內馬斯那一段：城內地面與牆頂步道同高）、正面朝城內；台上一圈圍牆＋門樓，靠牆的主樓（三層＋東北的樓閣）、
#   西南的大廳（屋頂塌了的廢墟）、西南側翼、東北的宮內禮拜堂、庭院與噴泉、沿正面圍牆的馬廄與雜屋。
#   1453：皇帝君士坦丁十一世住在這一區，但宮殿已經衰敗（Tafur 1437）；到征服時皇室似乎只還在用波菲羅根尼圖斯宮與阿內馬斯那一組（TBL）。
#   ⛔ 不做：阿內馬斯雙塔與牆內的拱廳（城牆本身是規劃的牆，另外畫）、聖母布雷契耐教堂（1434 燒毀，在台地東邊外面）、1453 年後的清真寺與道堂。
#   研究整理：scratchpad/cpl/research_palaces_cisterns.md §2（＋ research_batch3.md）；位置：阿內馬斯 OSM node 6373152085、台地擋土牆約 12 × 180 m（TBL）。
#   ⚠ 台地上每一棟的位置、大小、高度都是設計決定 —— 宮殿本體在 1453 年的樣子查不到（廳名 Anastasius、Ocean、Danube、Irene 樓…位置全都不知道）。
import math
import byz
from byz import BANDED, STONE, MARBLE, TILE, LEAD, BRICK, SOIL, WOOD, DOOR

KEY = 'blachernae'
TITLE = '布雷契耐宮 1453（Blachernae，帕列奧略皇居；台地、圍牆、主樓、大廳廢墟、禮拜堂）'
TITLE_SHORT = '布雷契耐宮 1453'
MPV = 0.4
W, D, H = 130.0, 96.0, 32.0
META = {'kind': 'building', 'use': 'blachernae', 'style': 'roman', 'lot': '130,96', 'base': 0, 'variant': 'a', 'lamps': 10}
PARTS = (('body', 1, '宮殿（主樓、樓閣、大廳廢墟、側翼、禮拜堂、馬廄）'), ('roof', 2, '屋頂'), ('enclosure', 3, '圍牆與門樓'),
         ('court', 4, '庭院（鋪面、花園、噴泉）'),
         ('trees-cypress', 5, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}),
         ('trees-plane', 6, '懸鈴木（遊戲換成生成式的懸鈴木）', {'kind': 'tree', 'tree': 'plane'}))
PROV = {
    '宮殿在人工堆成的台地上、背面是陸牆（城內地面與牆頂步道同高）；台地擋土牆約 12 m 高、180 m 長': '參考資料：van Millingen 1899 ch.X；TBL（Blachernai Palace）',
    'Clavijo 1403：皇帝的宮殿在不面海的那個角、山丘上；Tafur 1437：曾經極壯麗、如今衰敗': '參考資料：Clavijo（Markham 1859 英譯）；Tafur（Vasiliev 轉引）',
    '1453 年皇室主要用波菲羅根尼圖斯宮與阿內馬斯那一組': '參考資料：TBL（推估）',
    '台地 130 × 96 m、各棟的位置、大小、層數、大廳屋頂已塌、禮拜堂的形制': '設計決定（宮殿本體的平面與 1453 年的狀態查不到）',
    '牆面：下段琢石、上段磚石交替、大理石腰線（照同期的波菲羅根尼圖斯宮）': '設計決定（參考資料：TBL 的波菲羅根尼圖斯宮）',
}


def arcade(M, x0, x1, n, y, z0, z1, w, normal='y', depth=2.0, glass=False):
    """沿 x（normal y）或沿 y（normal x）一排 n 個拱：挖空或裝窗。"""
    for k in range(n):
        c = x0 + (k + 0.5) * (x1 - x0) / n
        a = M.arch_open(c, y, z0, z1, w, normal='y', depth=depth) if normal == 'y' else M.arch_open(y, c, z0, z1, w, normal='x', depth=depth)
        (M.win if glass else M.air)(a)


def crenel(M, x0, x1, y0, y1, z, mat, lay, step=2.0, h=1.2):
    """雉堞：牆頂每 step 公尺一個垛（一半實一半空）。"""
    along_x = (x1 - x0) >= (y1 - y0)
    u = M.X if along_x else M.Y
    on = ((u - (x0 if along_x else y0)) % step) < step / 2
    M.add(M.box(x0, x1, y0, y1, z, z + h) & on, mat, lay)


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.2)
    M.band_z0 = 5.0
    B, R, E, C = 1, 2, 3, 4
    # ── 圍牆（正面、兩側；背面是陸牆）＋門樓、角塔 ──
    t, zw = 2.4, 8.0
    for x0, x1, y0, y1 in ((0, W, 0, t), (0, t, 0, D), (W - t, W, 0, D)):
        M.add(M.box(x0, x1, y0, y1, 0, zw), BANDED, E)
        crenel(M, x0, x1, y0, y1, zw, BANDED, E)
    gx = 52.0                                                   # 門樓：兩座方塔夾一道拱門
    for x0 in (gx - 11.0, gx + 4.0):
        M.add(M.box(x0, x0 + 7.0, 0, 7.0, 0, 13.0), BANDED, E)
        crenel(M, x0, x0 + 7.0, 0, 0.8, 13.0, BANDED, E); crenel(M, x0, x0 + 7.0, 6.2, 7.0, 13.0, BANDED, E)
        M.win(M.arch_open(x0 + 3.5, 0.0, 8.6, 11.0, 0.8, normal='y', depth=1.6))
    M.add(M.box(gx - 4.0, gx + 4.0, 0, 7.0, 6.4, 10.0), BANDED, E)
    M.door(M.arch_open(gx, 1.2, 0, 6.0, 4.4, normal='y', depth=2.4))
    M.air(M.arch_open(gx, 4.6, 0, 6.0, 4.4, normal='y', depth=4.8))
    for x0 in (0.0, W - 8.0):                                   # 正面兩個角塔
        M.add(M.box(x0, x0 + 8.0, 0, 8.0, 0, 12.0), BANDED, E)
        crenel(M, x0, x0 + 8.0, 0, 0.8, 12.0, BANDED, E)
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    # ── 主樓（靠陸牆）：三層 8／7／7 m、一樓朝庭院的拱廊、二三樓的窗；東北端一座五層的樓閣 ──
    x0, x1, y0, y1, zt = 52.0, 104.0, 74.0, 93.0, 22.0
    M.add(M.box(x0, x1, y0, y1, 0, zt), BANDED, B)
    M.add(M.box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, zt - 0.6, zt), MARBLE, B)
    M.add(M.hip(x0, x1, y0, y1, zt, 2.4, 0.35), TILE, R)
    for zz in (8.0, 15.0):
        M.add(M.box(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, zz - 0.4, zz), MARBLE, B)
    M.air(M.box(x0 + 1.0, x1 - 1.0, y0, y0 + 3.2, 0, 6.4))               # 拱廊（深 3.2 m）
    arcade(M, x0 + 1.0, x1 - 1.0, 10, y0 + 0.2, 0, 6.6, 3.6, depth=0.8)
    for k in range(10):
        c = x0 + 1.0 + (k + 0.5) * (x1 - x0 - 2.0) / 10
        M.door(M.arch_open(c, y0 + 3.2, 0, 3.0, 1.6, normal='y', depth=1.2)) if k % 3 == 1 else M.win(M.arch_open(c, y0 + 3.2, 1.0, 4.4, 1.6, normal='y', depth=1.2))
    arcade(M, x0 + 1.0, x1 - 1.0, 12, y0, 9.4, 13.4, 1.8, glass=True)
    arcade(M, x0 + 1.0, x1 - 1.0, 12, y1, 9.4, 13.4, 1.6, glass=True)
    arcade(M, x0 + 1.0, x1 - 1.0, 15, y0, 16.4, 20.2, 1.6, glass=True)
    arcade(M, x0 + 1.0, x1 - 1.0, 15, y1, 16.4, 20.2, 1.6, glass=True)
    # 紅白幾何拼磚帶（照波菲羅根尼圖斯宮）：每層窗下一條
    for zb in (9.0, 16.0):
        cb = ((M.X // 0.8) + (M.Z // 0.8)) % 2 == 0
        band = M.full(M.box(x0, x1, y0, y1, zb - 0.8, zb)) & M.S
        M.MAT[band & M.full(cb)] = MARBLE
        M.MAT[band & ~M.full(cb)] = BRICK
    # 東北的樓閣（五層，比主樓高；朝金角灣的那一面三樓托架陽台）
    px0, px1, py0, py1, pz = 104.0, 120.0, 64.0, 93.0, 28.0
    M.add(M.box(px0, px1, py0, py1, 0, pz), BANDED, B)
    M.add(M.box(px0 - 0.3, px1 + 0.3, py0 - 0.3, py1 + 0.3, pz - 0.6, pz), MARBLE, B)
    M.add(M.hip(px0, px1, py0, py1, pz, 2.6, 0.45), TILE, R)
    for zz in (8.0, 13.5, 18.5, 23.0):
        M.add(M.box(px0 - 0.2, px1 + 0.2, py0 - 0.2, py1 + 0.2, zz - 0.4, zz), MARBLE, B)
    for zz0, zz1 in ((2.0, 5.6), (9.6, 12.4), (15.0, 17.6), (20.0, 22.2), (24.4, 26.8)):
        arcade(M, px0 + 1.0, px1 - 1.0, 4, py0, zz0, zz1, 1.4, glass=True)
        arcade(M, py0 + 1.0, py1 - 1.0, 7, px1, zz0, zz1, 1.4, normal='x', glass=True)
    M.add(M.box(px1, px1 + 1.6, py0 + 6.0, py0 + 16.0, 13.5, 13.9), MARBLE, B)        # 陽台
    M.add(M.box(px1 + 1.4, px1 + 1.6, py0 + 6.0, py0 + 16.0, 13.9, 15.0), MARBLE, B)
    for yy in (py0 + 7.0, py0 + 11.0, py0 + 15.0):
        M.add(M.box(px1, px1 + 1.2, yy - 0.3, yy + 0.3, 12.4, 13.5), STONE, B)
    M.MAT[M.S & M.full(M.Z < 5.0) & (M.MAT == BANDED)] = STONE
    # ── 西南的大廳（屋頂塌了、只剩牆與窗洞）──
    hx0, hx1, hy0, hy1, hz = 10.0, 48.0, 66.0, 93.0, 15.0
    M.add(M.box(hx0, hx1, hy0, hy1, 0, hz) & ~M.box(hx0 + 1.6, hx1 - 1.6, hy0 + 1.6, hy1 - 1.6, 0.4, 99), BANDED, B)
    M.add(M.box(hx0 + 1.6, hx1 - 1.6, hy0 + 1.6, hy1 - 1.6, 0, 0.4), MARBLE, B)
    for k in range(7):                                                   # 斷掉的牆頂：一段一段高低不齊
        cx = hx0 + 2.0 + k * 5.6
        M.air(M.box(cx, cx + 2.8, hy0 - 1, hy0 + 1.7, hz - (1.2 + (k * 37 % 5) * 0.6), 99))
        M.air(M.box(cx + 1.4, cx + 3.6, hy1 - 1.7, hy1 + 1, hz - (0.8 + (k * 53 % 4) * 0.8), 99))
    arcade(M, hx0 + 1.0, hx1 - 1.0, 7, hy0, 6.0, 11.0, 2.2)
    arcade(M, hx0 + 1.0, hx1 - 1.0, 7, hy1, 6.0, 11.0, 2.2)
    arcade(M, hy0 + 1.0, hy1 - 1.0, 4, hx0, 6.0, 11.0, 2.2, normal='x')
    M.air(M.arch_open(29.0, hy0, 0, 6.0, 4.0, normal='y', depth=2.4))
    for xx in range(14, 46, 4):                                          # 倒在地上的碎石堆
        M.add(M.box(xx, xx + 1.6, hy0 + 4.0 + (xx * 7 % 9), hy0 + 5.2 + (xx * 7 % 9), 0.4, 0.4 + (xx % 3) * 0.4 + 0.4), STONE, B)
    # ── 西南側翼（兩層、朝庭院一樓拱廊）──
    wx0, wx1, wy0, wy1, wz = 3.0, 15.0, 14.0, 66.0, 12.0
    M.add(M.box(wx0, wx1, wy0, wy1, 0, wz), BANDED, B)
    M.add(M.gable(wx0, wx1, wy0, wy1, wz, 2.6, 'y'), TILE, R)
    M.add(M.box(wx0 - 0.2, wx1 + 0.2, wy0, wy1, 6.0, 6.4), MARBLE, B)
    arcade(M, wy0 + 1.0, wy1 - 1.0, 9, wx1, 0, 4.6, 3.2, normal='x', depth=1.4)
    arcade(M, wy0 + 1.0, wy1 - 1.0, 13, wx1, 7.6, 10.6, 1.4, normal='x', glass=True)
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    # ── 宮內禮拜堂（十字形平面、一座穹頂、後殿朝東北 +x）──
    cx0, cx1, cy0, cy1 = 92.0, 110.0, 24.0, 38.0
    ccx, ccy = 102.0, (cy0 + cy1) / 2
    M.add(M.box(cx0, cx0 + 4.0, cy0, cy1, 0, 7.5), BANDED, B)                         # 前廊
    M.add(M.shed(cx0, cx0 + 4.0, cy0, cy1, 7.5, 8.6, '+x'), TILE, R)
    M.add(M.box(cx0 + 4.0, cx1, cy0, cy1, 0, 9.0), BANDED, B)
    M.add(M.box(cx0 + 4.0, cx1, ccy - 2.4, ccy + 2.4, 0, 11.0) | M.box(ccx - 2.4, ccx + 2.4, cy0, cy1, 0, 11.0), BANDED, B)
    M.add(M.box(cx0 + 4.0, cx1, cy0, cy1, 9.0, 9.4), TILE, R)
    M.add(M.barrel(cx0 + 4.0, cx1, ccy - 2.4, ccy + 2.4, 11.0, 'x', 1.4) | M.barrel(ccx - 2.4, ccx + 2.4, cy0, cy1, 11.0, 'y', 1.4), TILE, R)
    M.add(M.ngon(ccx, ccy, 3.4, 8, 11.0, 14.0, rot=90 + 22.5), BANDED, B)
    M.add(M.dome(ccx, ccy, 14.0, 3.1, 2.6, ribs=8), LEAD, R)
    M.win(M.ring_windows(ccx, ccy, 2.0, 4.0, 11.6, 13.6, [22.5 + 45 * k for k in range(8)], 0.4))
    M.add(M.apse_x(cx1 - 0.2, ccy, 3.2, 3, 0, 8.0, '+x'), BANDED, B)
    M.add(M.semidome(cx1 - 0.2, ccy, 8.0, 3.0, '+x'), TILE, R)
    M.win(M.ring_windows(cx1, ccy, 1.8, 3.8, 3.6, 6.8, [0], 0.45))
    M.door(M.arch_open(cx0, ccy, 0, 3.0, 1.8, normal='x', depth=1.6))
    for yy in (cy0, cy1):
        arcade(M, cx0 + 5.0, cx1 - 1.0, 3, yy, 5.0, 8.0, 1.0, glass=True)
    t_ = 0.21
    M.add(M.box(ccx - t_, ccx + t_, ccy - t_, ccy + t_, 16.4, 18.4) | M.box(ccx - t_, ccx + t_, ccy - 0.6, ccy + 0.6, 17.6, 18.0), byz.GOLD, R)
    # ── 馬廄、雜屋（沿正面圍牆的東北段，單坡貼著牆）──
    M.add(M.box(66.0, W - t, t, 12.0, 0, 5.0), BANDED, B)
    M.add(M.shed(66.0, W - t, t, 12.0, 5.0, 6.8, '-y'), TILE, R)
    for k in range(14):
        c = 68.0 + k * 4.0
        (M.door if k % 2 == 0 else M.win)(M.arch_open(c, 12.0, 0, 3.0 if k % 2 == 0 else 2.6, 1.6 if k % 2 == 0 else 1.0, normal='y', depth=1.2))
    # ── 庭院：門樓到主樓的大理石步道、方形花園（十字小徑）、八角噴泉 ──
    M.add(M.box(gx - 3.0, gx + 3.0, 7.0, y0, 0, 0.4), MARBLE, C)
    M.add(M.box(20.0, 48.0, 22.0, 58.0, 0, 0.4) & ~(M.box(32.8, 35.2, 22, 58, 0, 1) | M.box(20, 48, 38.8, 41.2, 0, 1)), SOIL, C)
    M.add(M.box(20.0, 48.0, 22.0, 58.0, 0, 0.4) & (M.box(32.8, 35.2, 22, 58, 0, 1) | M.box(20, 48, 38.8, 41.2, 0, 1)), MARBLE, C)
    M.add(M.ngon(gx, 44.0, 4.2, 8, 0, 0.8, rot=22.5) & ~M.ngon(gx, 44.0, 3.6, 8, 0.4, 9, rot=22.5), MARBLE, C)
    M.add(M.cyl(gx, 44.0, 0.6, 0, 2.2) | M.cyl(gx, 44.0, 1.2, 1.8, 2.2), MARBLE, C)
    for k in range(6):                                                   # 柏樹：步道兩旁
        for xx in (gx - 6.0, gx + 6.0):
            M.tree(xx, 14.0 + k * 9.0 + (4.5 if xx > gx else 0), 10.0, 2.6, 5)
    for xx, yy in ((24.0, 26.0), (44.0, 26.0), (24.0, 54.0), (44.0, 54.0), (80.0, 48.0), (96.0, 52.0)):
        M.tree(xx, yy, 13.0, 8.0, 6)
    G, L = M.finish(shell_m=1.2, seed=1081, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'gate': M.cell(gx, 0.4, 0), 'top': M.cell((px0 + px1) / 2, (py0 + py1) / 2, pz + 2.0)}
    return G, L, anchors, {'主樓簷口（m）': zt, '樓閣簷口（m）': pz, '大廳牆頂（m）': hz}
