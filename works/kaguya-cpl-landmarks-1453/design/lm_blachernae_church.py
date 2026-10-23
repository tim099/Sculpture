# Blachernae 聖母大教堂（Theotokos ton Blachernon；Pulcheria／Leo I 5 世紀、Justin II 擴建；聖母長袍的 Soros）1453：1434 年燒毀 ——
#   Tafur 1437：「燒得無法修復」；Gyllius（1540 年代）時連廢墟都看不到 ⇒ 1453 年做成沒有屋頂的焦黑殘殼：
#   三廊的巴西利卡（中廊兩排斷柱、側廊樓座的牆只剩下半截）、東邊半圓後殿的殘牆、西邊前廊；牆上半段燒黑、地上燒剩的樑與碎石、長回來的草與野樹。
#   ⚠ 只知道「96 × 36 m（Janin，經 Wikipedia）、東西向、1434 燒毀」；位置是推的（把今日 Ayvansaray 教堂當成聖浴場 Hagion Louma）；殘存的程度、高度是設計決定。
#   ⛔ 不做：Soros 禮拜堂（大教堂東邊約 70 m，另一座）、1867 年的 Ayvansaray 教堂、近代院牆。
#   研究整理：scratchpad/cpl/research_batch7.md §1。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK, DARK, WOOD

KEY = 'blachernae-church'
TITLE = 'Blachernae 聖母大教堂 1453（1434 年燒毀：沒有屋頂的殘殼）'
TITLE_SHORT = 'Blachernae 聖母大教堂 1453'
MPV = 0.4
W, D, H = 36.0, 96.0, 20.0
META = {'kind': 'building', 'use': 'blachernae-church', 'style': 'roman', 'lot': '36,96', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('body', 1, '殘牆、後殿、前廊'), ('ground', 2, '地面（草、燒剩的樑、碎石、斷柱）'),
         ('trees', 3, '野樹（遊戲換成生成式的樹）', {'kind': 'tree', 'tree': 'broadleaf'}))
PROV = {
    '96 × 36 m、東西向': '參考資料：Janin（經 Wikipedia：Church of St. Mary of Blachernae）',
    '1434 年燒毀、Tafur 1437 說無法修復；Gyllius 時連廢墟都看不到': '參考資料：Wikipedia；Vasiliev 轉引 Tafur',
    '三廊巴西利卡、樓座': '參考資料：Wikipedia（Procopius 的描述）',
    '位置（今日教堂北 53 m、東 24 m）、殘存程度、高度、樹': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.2)
    M.band_z0 = 0.6
    rnd = random.Random(1434)
    B, G1, T = 1, 2, 3
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    # 外牆（厚 1.6、高 16，頂咬得很深）：西前廊 y 0～8、中殿 y 8～84、後殿 y 84～
    ruins.wall(M, 0, W, 0, 1.6, 9.0, rnd, B, bite=0.7, step=5.0)                 # 前廊西牆
    ruins.wall(M, 0, 1.6, 0, 84.0, 16.0, rnd, B, bite=0.65, step=5.5)
    ruins.wall(M, W - 1.6, W, 0, 84.0, 16.0, rnd, B, bite=0.65, step=5.5)
    ruins.wall(M, 0, W, 8.0, 9.6, 14.0, rnd, B, bite=0.6, step=5.0)               # 前廊與中殿之間
    M.add(M.apse(W / 2, 84.0, 9.5, 9, 0, 13.0, '+y') & ~M.apse(W / 2, 83.0, 8.0, 9, -1, 99, '+y'), BANDED, B)
    M.add(M.box(1.6, 8.0, 82.4, 84.0, 0, 12.0) | M.box(W - 8.0, W - 1.6, 82.4, 84.0, 0, 12.0), BANDED, B)
    for k in range(4):                                                         # 後殿的頂咬掉
        a = rnd.uniform(4.0, W - 8.0)
        M.air(M.box(a, a + rnd.uniform(3, 6), 82.0, D, rnd.uniform(5.0, 10.0), 99))
    for y in range(14, 80, 8):                                                  # 側牆的窗洞（上下兩層）
        for x in (0.0, W - 1.6):
            M.air(M.box(x - 0.1, x + 1.7, y, y + 2.2, 4.0, 7.0))
            M.air(M.box(x - 0.1, x + 1.7, y, y + 2.2, 10.0, 13.0))
    M.air(M.box(W / 2 - 2.0, W / 2 + 2.0, -0.1, 9.7, MPV, 5.0))                # 正門
    # 燒黑：牆的上半段（z > 6）一半的格塗暗
    burn = M.S & M.full(M.Z > 6.0) & (M.MAT == BANDED) & M.full(((M.X * 7 + M.Y * 3 + M.Z * 11) // 2.0) % 3 != 0)
    M.MAT[burn] = DARK
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    # 中廊兩排柱（x 10、26）：多半斷了、有的倒在地上
    for y in range(14, 80, 5):
        for x in (10.0, 26.0):
            h = rnd.random()
            ruins.stub(M, x, y, 0.45, 0.0 if h < 0.3 else 1.0 + h * (7.0 if h > 0.8 else 3.0), B)
    for (x, y) in ((12.0, 30.0), (22.0, 55.0), (14.0, 70.0)):
        ruins.fallen(M, x, y, 0.45, 4.6, G1)
    # 燒剩的屋樑（暗木）、碎石
    for k in range(18):
        x, y = rnd.uniform(4, W - 8), rnd.uniform(12, 78)
        L = rnd.uniform(3.0, 8.0)
        if k % 2:
            M.add(M.box(x, x + L, y, y + 0.4, MPV, 2 * MPV + 0.4), WOOD, G1)
        else:
            M.add(M.box(x, x + 0.4, y, y + L, MPV, 2 * MPV + 0.4), WOOD, G1)
    M.MAT[M.S & (M.MAT == WOOD)] = DARK
    ruins.rubble(M, rnd, 3.0, W - 3.0, 10.0, 82.0, 40, G1, 0.6, 1.8)
    # 野樹（中殿裡長出來；離牆、柱 ≥ 2 m）
    for (x, y, h, w) in ((18.0, 22.0, 6.0, 4.2), (18.0, 48.0, 7.5, 5.0), (6.0, 64.0, 5.0, 3.2), (18.0, 74.0, 5.5, 3.6)):
        M.tree(x, y, h, w, T)
    G, L = M.finish(shell_m=0.8, seed=1434, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'殘牆最高（m）': 16.0}
