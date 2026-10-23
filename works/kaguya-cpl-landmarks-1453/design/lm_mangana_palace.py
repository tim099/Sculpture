# 曼加納宮的廢墟（Mangana；Constantine IX Monomachos 11 世紀擴建）1453：12 世紀末 Isaac II 拆走材料 ⇒ 只剩基座與斷牆 ——
#   1871 年修鐵路時在 İncili Köşk 後方挖出一棟 322 × 53 英尺（98.1 × 16.2 m）的建築、大量大理石柱與柱頭（Van Millingen 1899；認為是曼加納宮）。
#   做成：98 × 16 m 的長條基座（拱頂下部結構的牆，四邊咬得參差、一排拱口半埋）、上面斷斷續續的牆基、散落的大理石柱段與柱頭、碎石、草與野樹。
#   ⚠ 位置 ±50 m、長軸照鐵路 13°（未驗證）；殘存的程度、高度是設計決定。旁邊的聖喬治修道院（mangana）還在用、另一座。
#   研究整理：scratchpad/cpl/research_batch7.md §4。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK, DARK

KEY = 'mangana-palace'
TITLE = '曼加納宮的廢墟 1453（98 × 16 m 的基座與斷牆）'
TITLE_SHORT = '曼加納宮廢墟 1453'
MPV = 0.4
W, D, H = 98.0, 16.0, 11.0
META = {'kind': 'building', 'use': 'mangana-palace', 'style': 'roman', 'lot': '98,16', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('ruins', 1, '基座、拱口、斷牆、柱段'), ('ground', 2, '地面（草、碎石）'),
         ('trees', 3, '野樹（遊戲換成生成式的樹）', {'kind': 'tree', 'tree': 'broadleaf'}))
PROV = {
    '1871 年挖出 322 × 53 英尺的建築、大量大理石柱與柱頭；Mordtmann、Van Millingen 認為是曼加納宮': '參考資料：Van Millingen 1899',
    '12 世紀末 Isaac II 拆走材料': '參考資料：ODB（經 Wikipedia：Mangana）',
    '位置、長軸方向、殘存程度、高度、樹': '設計決定（位置 ±50 m）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.0)
    M.band_z0 = 0.0
    rnd = random.Random(1045)
    R, G1, T = 1, 2, 3
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    top = 3.0
    M.add(M.box(1.0, W - 1.0, 1.0, D - 1.0, 0, top), BRICK, R)                     # 下部結構（拱頂的頂已經被拆走）
    for k in range(30):                                                         # 四邊咬得參差
        side = k % 2
        a = rnd.uniform(0, W - 4)
        if side == 0:
            M.air(M.box(a, a + rnd.uniform(2, 6), -0.1, rnd.uniform(1.6, 3.0), rnd.uniform(0.8, top - 0.4), 99))
        else:
            M.air(M.box(a, a + rnd.uniform(2, 6), D - rnd.uniform(1.6, 3.0), D + 0.1, rnd.uniform(0.8, top - 0.4), 99))
    for k in range(14):                                                         # 正面一排拱口（半埋、裡面暗）
        x = 4.0 + k * 6.8
        M.air(M.arch_open(x, 1.0, MPV, 2.4, 2.4, normal='y', depth=2.4))
        M.add(M.box(x - 1.2, x + 1.2, 3.2, 3.6, MPV, 2.2), DARK, R)
    M.add(M.box(1.0, W - 1.0, 1.0, D - 1.0, top, top + MPV) & M.full(M.MAT == BRICK), byz.GREEN, G1)
    # 基座上斷斷續續的牆基（隔間）、散落的大理石柱段與柱頭
    for x in range(8, 92, 14):
        h = rnd.uniform(0.6, 4.0)
        M.add(M.box(x, x + 1.2, 2.0, D - 2.0, top, top + h), BANDED, R)
    for k in range(12):                                                         # 倒在基座頂上的柱段（ruins.fallen 只會擺在地面 ⇒ 這裡自己寫、躺在基座最上一格上：0.4 m 一格時 box(…, top) 只填到 top − MPV）
        x, y, r, L_ = rnd.uniform(3, W - 8), rnd.uniform(4.5, 10.5), 0.4, rnd.uniform(2.0, 4.5)   # 邊上 3 m 被咬過 ⇒ 只擺中間那一段
        if k % 3:
            M.add(((M.Y - y) ** 2 + (M.Z - (top - MPV) - r) ** 2 < r * r) & (M.X >= x) & (M.X < x + L_), MARBLE, G1)
        else:
            M.add(((M.X - x) ** 2 + (M.Z - (top - MPV) - r) ** 2 < r * r) & (M.Y >= y) & (M.Y < y + min(L_, 11.5 - y)), MARBLE, G1)
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    for k in range(24):                                                         # 碎石（基座頂上）
        cx, cy, r = rnd.uniform(2.0, W - 2.0), rnd.uniform(4.5, D - 4.5), rnd.uniform(0.5, 1.4)
        M.add(M.dome(cx, cy, top, r, r * 0.45), STONE if k % 3 else BRICK, R)
    for (x, y, h, w) in ((29.0, 8.0, 5.0, 3.6), (57.0, 8.0, 6.0, 4.2), (85.0, 8.0, 4.5, 3.2)):
        M.tree(x, y, h, w, T, z0=top)
    G, L = M.finish(shell_m=0.8, seed=1045, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'基座頂（m）': top}
