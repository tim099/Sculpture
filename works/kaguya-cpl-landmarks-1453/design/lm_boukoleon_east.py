# 布科勒昂宮的東翼（Boukoleon 往東、沿馬爾馬拉海牆的那一段）1453：仍立、但已成廢墟 ——
#   OSM「Bukoleon Sarayı Kalıntıları」（way 1184851395）的輪廓 166 × 51 m、臨海兩段 48 m＋113 m；遊戲裡的布科勒昂（lm_boukoleon.py）只有正對皇家階梯門那 60 m
#   ⇒ 這一座補輪廓東邊剩下的 78 m（從布科勒昂的東緣隔 1 m 到輪廓的東端）。東段立面 1871／1873 年修鐵路時拆掉，今天什麼都不剩。
#   做成：臨海一長條兩層的翼樓（屋頂塌了、牆頂高低不齊、中段塌成一個缺口）、上層一排拱窗、底層朝裡的拱頂下部結構入口；東端一座方樓；
#         後面的庭院：兩排列柱的殘柱與倒柱、八角的噴泉池、斷掉的後牆、碎石、草與野樹。
#   ⚠ 遊戲裡海牆是規劃的牆（另外畫，高 12 m）⇒ 這一座同布科勒昂擺在海牆內側（正面離牆的中線約 4 m）、上層露出牆頂。
#   ⚠ 只有「宮殿延伸到這裡、1453 年是廢墟」有出處；翼樓、方樓、庭院、噴泉池的樣子與大小全是設計決定。
#   ⛔ 不做：鐵路、1959 Kennedy Caddesi 填海、今天的護欄與步道。研究整理：scratchpad/cpl/research_batch3.md §5。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK

KEY = 'boukoleon-east'
TITLE = '布科勒昂宮的東翼 1453（臨海翼樓與庭院的廢墟）'
TITLE_SHORT = '布科勒昂宮東翼 1453'
MPV = 0.2
W, D, H = 78.0, 40.0, 20.0
META = {'kind': 'building', 'use': 'boukoleon-east', 'style': 'roman', 'lot': '78,40', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('body', 1, '臨海的翼樓與東端的方樓（廢墟）'), ('ruins', 2, '庭院的廢墟（殘柱、倒柱、噴泉池、斷牆、碎石）'), ('ground', 3, '地面（草）'),
         ('trees-fig', 4, '野樹（遊戲換成生成式的闊葉樹）', {'kind': 'tree', 'tree': 'broadleaf'}),
         ('trees-cypress', 5, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}))
PROV = {
    '布科勒昂的廢墟輪廓 166 × 51 m、臨海兩段 48 m＋113 m': '參考資料：OSM way 1184851395（Bukoleon Sarayı Kalıntıları）',
    '東段立面 1871／1873 年修鐵路時拆掉': '參考資料：van Millingen 1899；Wikipedia（Bucoleon Palace）',
    '宮殿的立面砌在海牆本身上': '參考資料：van Millingen 1899（Leunclavius 的記載）',
    '1453 年仍立、但已成廢墟': '參考資料：Wikipedia（推估）；Necipoğlu 1991',
    '翼樓、方樓、庭院、噴泉池的樣子與大小、殘存程度、樹；擺在海牆內側': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.4)
    M.band_z0 = 0.0
    rnd = random.Random(1873)
    B, R, G1, T1, T2 = 1, 2, 3, 4, 5
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    # ── 臨海的翼樓：y 2..14、高 15 m；屋頂塌了、牆頂一段段往下咬；中段（x 30..46）塌成缺口 ──
    x0, x1, y0, y1, zt = 1.0, 66.0, 2.0, 14.0, 15.0
    M.add(M.box(x0, x1, y0, y1, 0, zt), BANDED, B)
    M.add(M.box(x0, x1, y0, y0 + 0.6, 8.8, 9.4), MARBLE, B)                                                # 上層的腰線
    M.air(M.box(x0 + 1.2, x1 - 1.2, y0 + 1.2, y1 - 1.2, 9.4, 99))                                           # 上層裡面空了（屋頂、樓板塌了）
    M.add(M.box(x0 + 1.2, 30.0, y0 + 1.2, y1 - 1.2, 9.0, 9.4), STONE, B)                                    # 西半的樓板還在
    for xc in range(4, 64, 5):                                                                             # 上層一排拱窗（1.6 m 寬）
        if 28.0 <= xc <= 48.0:
            continue
        M.air(M.arch_open(xc + 0.5, y0, 10.4, 13.0, 1.6, normal='y', depth=2.6))
    for xc in range(5, 64, 6):                                                                             # 底層朝庭院的拱（下部結構的入口，幾個塌了）
        if 30.0 <= xc <= 46.0:
            continue
        M.air(M.arch_open(xc, y1, 0, 5.6, 3.2, normal='y', depth=2.6))
    for k in range(22):                                                                                    # 牆頂高低不齊（最低咬到 13.2 m：再低窗頂上那一截就跟兩邊斷開、浮空）
        cx = x0 + k * 3.0
        M.air(M.box(cx, cx + 1.6 + rnd.random() * 1.2, y0 - 1, y1 + 1, zt - 0.4 - rnd.random() * 1.4, 99))
    M.air(M.box(30.0, 46.0, y0 - 1, y1 + 1, 4.0, 99))                                                       # 中段的缺口：只剩 4 m 高的牆根
    for k in range(5):                                                                                     # 缺口兩邊的牆咬成階梯
        M.air(M.box(30.0 - (k + 1) * 0.8, 30.0, y0 - 1, y1 + 1, 4.0 + (k + 1) * 2.0, 99))
        M.air(M.box(46.0, 46.0 + (k + 1) * 0.8, y0 - 1, y1 + 1, 4.0 + (k + 1) * 2.0, 99))
    # ── 東端的方樓：x 66..77、y 1..17、高 18 m；四面開窗、頂咬掉一角 ──
    M.add(M.box(66.0, 77.0, 1.0, 17.0, 0, 18.0), BANDED, B)
    M.add(M.box(66.0, 77.0, 1.0, 1.6, 8.8, 9.4), MARBLE, B)
    M.air(M.box(67.4, 75.6, 2.4, 15.6, 9.4, 99))                                                            # 上層空了（樓板、屋頂塌了）
    for xc in (69.5, 73.5):
        M.air(M.arch_open(xc, 1.0, 10.4, 15.0, 1.8, normal='y', depth=3.0))
    for yc in (5.5, 12.5):
        M.air(M.arch_open(yc, 77.0, 10.4, 15.0, 1.8, normal='x', depth=3.0))
    M.air(M.arch_open(71.5, 17.0, 0, 4.4, 2.4, normal='y', depth=3.0))                                      # 門（朝庭院）
    M.air(M.box(71.0, 78.0, 9.0, 18.0, 15.0, 99))                                                           # 頂咬掉東北角
    M.air(M.box(66.0, 70.0, 0.0, 6.0, 16.6, 99))
    M.MAT[M.S & M.full(M.Z < 2.0) & (M.MAT == BANDED)] = STONE
    # ── 後面的庭院：兩排列柱（殘柱、倒柱）、噴泉池、斷掉的後牆與東西兩道隔牆、碎石 ──
    for row_y in (19.0, 33.0):
        for i, cx in enumerate(range(8, 64, 4)):
            h = rnd.choice((0.0, 0.0, 1.6, 2.8, 4.4, 5.6))
            ruins.stub(M, cx, row_y, 0.35, h, R)
    for (cx, cy, L_, ax) in ((14.0, 21.0, 4.6, 'x'), (27.0, 31.0, 5.0, 'x'), (45.0, 21.5, 3.8, 'x'), (57.0, 23.0, 4.4, 'y'), (39.0, 30.5, 4.2, 'x')):
        ruins.fallen(M, cx, cy, 0.35, L_, R, axis=ax)
    M.add(M.ngon(36.0, 26.0, 3.4, 8, 0, 0.9) & ~M.ngon(36.0, 26.0, 2.8, 8, 0.3, 99), MARBLE, R)             # 八角的噴泉池（乾了）
    M.add(M.cyl(36.0, 26.0, 0.5, 0, 1.6), MARBLE, R)                                                        # 池中的柱座
    ruins.wall(M, 1.0, 66.0, 38.0, 39.2, 4.2, rnd, R, bite=0.8, step=2.0)                                    # 後牆
    ruins.wall(M, 1.0, 2.2, 16.0, 38.0, 3.2, rnd, R, bite=0.7)                                              # 西邊的隔牆（跟布科勒昂之間）
    ruins.rubble(M, rnd, 30.0, 46.0, 14.5, 20.0, 12, R)                                                     # 翼樓塌下來的那一堆
    ruins.rubble(M, rnd, 4.0, 64.0, 21.0, 36.0, 18, R)
    for (tx, ty, th, tw) in ((10.0, 26.0, 7.0, 5.0), (24.0, 35.0, 6.0, 4.4), (50.0, 27.0, 8.0, 6.0), (62.0, 35.0, 5.4, 4.0)):
        M.tree(tx, ty, th, tw, T1)
    for (tx, ty) in ((70.0, 24.0), (74.0, 30.0)):
        M.tree(tx, ty, 9.0, 2.4, T2)
    G, L = M.finish(shell_m=0.8, seed=1873, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'翼樓牆頂（m）': zt, '方樓（m）': 18.0}
