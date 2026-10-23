# 大皇宮上層台地（Daphne 一帶，大競技場東側）1453：帕列奧略時代棄用、只當監獄；Mehmed II 入宮見其荒廢（Necipoğlu 1991）；Clavijo 1403 說城中心多圍起來的麥田與果園 ——
#   台地上：Daphne 宮的廳（沒有屋頂、斷牆、地坪還在）、聖司提反小堂的殘牆與後殿、八角亭的殘牆、一排斷柱（柱廊）、果園與橄欖、菜畦、碎石、穿過台地的一條石板小徑；
#   台地的邊：下坡那一邊的女兒牆（擋土牆本身 ＝ 地塊的石基，遊戲在坡下補）、靠大競技場那一邊的矮圍牆。
#   ⚠ 各棟的位置、大小、高度全是設計決定 —— 大皇宮在 1453 年的樣子只有「幾乎什麼都沒留下」（BL）；Daphne 各廳的平面查不到。
#   ⛔ 不做：藍色清真寺（1609–16）與它的附屬、Arasta、1871 年以後的監獄、旅館、鐵路。
#   研究整理：scratchpad/cpl/research_batch3.md §4；框 160 × 100 m 沿大競技場的軸（方位 38° 是正面 ＝ 下坡），後緣離大競技場東緣 10 m。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK

KEY = 'palace-daphne'
TITLE = '大皇宮上層台地 1453（Daphne 一帶的廢墟、果園）'
TITLE_SHORT = '大皇宮上層台地 1453'
MPV = 0.4
W, D, H = 160.0, 100.0, 14.0
META = {'kind': 'building', 'use': 'palace-daphne', 'style': 'roman', 'lot': '160,100', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('ground', 1, '台地（草、菜畦、小徑、女兒牆、圍牆）'), ('ruins', 2, '廢墟（Daphne 的廳、小堂、八角亭、斷柱、碎石）'),
         ('trees-fruit', 3, '果樹（遊戲換成生成式的果樹）', {'kind': 'tree', 'tree': 'fruit'}),
         ('trees-olive', 4, '橄欖（遊戲換成生成式的橄欖）', {'kind': 'tree', 'tree': 'olive'}),
         ('trees-cypress', 5, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}))
PROV = {
    '大皇宮約 16 ha、六層台地、從大競技場到海岸落差約 33 m': '參考資料：Wikipedia（Great Palace of Constantinople）',
    '帕列奧略時代棄用、只當監獄；1453 年 Mehmed II 入宮見其荒廢': '參考資料：Necipoğlu 1991 p.3（經 Wikipedia）',
    '到征服時，除 Nea 外幾乎什麼都沒留下': '參考資料：The Byzantine Legacy（Great Palace）',
    '城中心多圍起來的麥田與果園': '參考資料：Clavijo 1403（Markham 1859 英譯）',
    'Daphne 宮在大競技場東側、Kathisma 旁；有聖司提反小堂、八角亭': '參考資料：Wikipedia（Palace of Daphne；推估）',
    '台地的框、各棟的位置大小高度、殘存程度、果園與菜畦': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.2)
    M.band_z0 = 1.0
    rnd = random.Random(1453)
    G1, R = 1, 2
    # ── 地面：草；穿過台地的石板小徑（缺了好幾段）；菜畦 ──
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    path = M.box(66.0, 69.6, 0, D, 0, 2 * MPV) & ((M.Y // 4.0) % 5 != 2)
    M.add(path, STONE, G1)
    ruins.plots(M, rnd, 112.0, 156.0, 36.0, 84.0, G1)
    # ── 台地的邊：下坡那一邊（y 0）的女兒牆、靠大競技場那一邊（y D）的矮圍牆 ──
    ruins.wall(M, 0, W, 0, 1.2, 1.4, rnd, G1, bite=0.9, step=3.0)
    ruins.wall(M, 0, W, D - 1.2, D, 2.6, rnd, G1, bite=0.8, step=3.0)
    # ── Daphne 的廳：沒有屋頂，一面長牆還有一排窗洞 ──
    ruins.shell(M, 18.0, 62.0, 52.0, 78.0, 10.0, 1.6, rnd, R, bite=0.55)
    for k in range(6):
        M.air(M.arch_open(22.0 + k * 7.0, 52.0, 5.0, 8.4, 2.0, normal='y', depth=2.4))
    M.air(M.arch_open(40.0, 78.0, 0, 4.4, 3.2, normal='y', depth=2.4))
    # 聖司提反小堂：殘牆＋後殿（朝 +x）
    ruins.shell(M, 75.0, 93.0, 58.0, 72.0, 7.5, 1.2, rnd, R, bite=0.5)          # 西牆離小徑邊的柏樹 ≥ 2 m（樹冠伸進牆裡會被斷牆咬掉、剩一截浮空）
    M.add(M.apse_x(93.0, 65.0, 3.6, 5, 0, 6.0, '+x') & ~M.apse_x(92.0, 65.0, 2.6, 5, -1, 99, '+x'), BANDED, R)
    # 八角亭：殘牆
    oct_ = M.ngon(108.0, 66.0, 7.0, 8, 0, 6.5, rot=22.5) & ~M.ngon(108.0, 66.0, 5.8, 8, -1, 99, rot=22.5)
    M.add(oct_, BANDED, R)
    for k in range(8):
        M.air(M.box(100.0 + k * 2.2, 101.4 + k * 2.2, 58.0, 74.0, 6.5 - rnd.random() * 4.0, 99))
    M.add(M.ngon(108.0, 66.0, 5.8, 8, 0, MPV, rot=22.5), MARBLE, R)
    # 一排斷柱（柱廊，沿靠大競技場那一邊）
    for k in range(26):
        x = 22.0 + k * 4.4
        h = rnd.random()
        ruins.stub(M, x, 88.0, 0.35, 0.0 if h < 0.25 else 1.2 + h * (5.5 if h > 0.75 else 2.0), R)
    for (cx, cy, L_) in ((40.0, 84.0, 4.6), (78.0, 84.5, 3.8), (118.0, 84.0, 5.2)):
        ruins.fallen(M, cx, cy, 0.35, L_, R)
    ruins.rubble(M, rnd, 10.0, 150.0, 44.0, 96.0, 46, R)
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    # ── 樹：果園（西南）、橄欖（東北）、小徑兩邊的柏樹 ──
    for x in range(14, 60, 6):
        for y in range(10, 42, 6):
            M.tree(x + rnd.uniform(-0.8, 0.8), y + rnd.uniform(-0.8, 0.8), rnd.uniform(3.5, 5.0), rnd.uniform(3.4, 4.4), 3)
    for x in range(76, 152, 7):
        for y in range(9, 30, 7):
            M.tree(x + rnd.uniform(-1, 1), y + rnd.uniform(-1, 1), rnd.uniform(4.0, 6.0), rnd.uniform(4.0, 5.2), 4)
    for y in range(8, 96, 12):
        for x in (64.0, 71.6):
            M.tree(x, y, 10.0, 2.2, 5)
    G, L = M.finish(shell_m=0.8, seed=1453, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'廳的牆頂（m）': 10.0}
