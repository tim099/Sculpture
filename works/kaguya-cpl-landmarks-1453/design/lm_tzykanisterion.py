# Tzykanisterion 馬球場（巴西爾一世拆了舊的蓋 Nea、往東重建一座更大的，用兩道廊接 Nea）1453：大皇宮一帶帕列奧略時代棄用（Necipoğlu 1991）——
#   做成：一片長方形的土場（草從邊上長回來、場上幾棵野樹）、一圈矮圍牆（斷了好幾段）、靠海那一邊四級看台（塌了兩段）、看台中間皇帝的看台（台基＋四根斷柱）、
#   朝 Nea 那一邊的門（兩座門墩）與兩道廊的殘柱、場的兩頭各一根石柱（標記，設計）。
#   ⚠ 大小、看台、門、殘存程度都是設計決定 —— 只知道「在 Nea 與海牆之間、比舊的大、用兩道廊接 Nea；首都的馬球場也拿來行刑示眾」。
#   ⛔ 不做：1453 年後的建築。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK

KEY = 'tzykanisterion'
TITLE = 'Tzykanisterion 馬球場 1453（圍牆、看台殘段、皇帝看台）'
TITLE_SHORT = 'Tzykanisterion 1453'
MPV = 0.4
W, D, H = 150.0, 56.0, 9.0
META = {'kind': 'building', 'use': 'tzykanisterion', 'style': 'roman', 'lot': '150,56', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('field', 1, '場地（土、草）'), ('walls', 2, '圍牆、看台、門墩、廊的殘柱、碎石'),
         ('trees', 3, '野樹（遊戲換成生成式的樹）', {'kind': 'tree', 'tree': 'broadleaf'}))
PROV = {
    '巴西爾一世拆舊的馬球場蓋 Nea、往東重建一座更大的，用兩道廊接 Nea；在 Nea 與海牆之間': '參考資料：Wikipedia（Tzykanisterion、Nea Ekklesia）',
    '首都的馬球場也拿來行刑示眾': '參考資料：Wikipedia（Tzykanisterion）',
    '帕列奧略時代大皇宮一帶棄用': '參考資料：Necipoğlu 1991 p.3（經 Wikipedia）',
    '大小、看台、皇帝看台、門、標記石柱、殘存程度': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.2)
    M.band_z0 = 0.6
    rnd = random.Random(886)
    F, Wl, T = 1, 2, 3
    # ── 場地：土（中間踩實）、外圈與兩頭草長回來 ──
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, F)
    M.add(M.box(6.0, W - 6.0, 6.0, 42.0, 0, MPV), byz.SOIL, F)
    for k in range(22):
        x, y = 6.0 + rnd.random() * (W - 12.0), 6.0 + rnd.random() * 36.0
        r = 1.5 + rnd.random() * 3.5
        M.add(M.cyl(x, y, r, 0, MPV), byz.GREEN, F)
    # ── 圍牆：一圈矮牆（厚 1 m、高 3 m、斷了好幾段）；朝 Nea 那一邊（y 0）中間留門 ──
    ruins.wall(M, 0, 68.0, 0, 1.0, 3.0, rnd, Wl, bite=0.8, step=3.0)
    ruins.wall(M, 82.0, W, 0, 1.0, 3.0, rnd, Wl, bite=0.8, step=3.0)
    ruins.wall(M, 0, 1.0, 0, D, 3.0, rnd, Wl, bite=0.8, step=3.0)
    ruins.wall(M, W - 1.0, W, 0, D, 3.0, rnd, Wl, bite=0.8, step=3.0)
    for (a, b) in ((18.0, 26.0), (104.0, 109.0)):
        M.air(M.box(a, b, -1, 2.0, MPV, 99))
    M.air(M.box(-1, 2.0, 20.0, 27.0, MPV, 99))
    # ── 靠海那一邊的看台：四級（y 44～54，每級高 0.6、深 2.4）、後面的高牆；塌了兩段 ──
    for k in range(4):
        M.add(M.box(2.0, W - 2.0, 44.0 + k * 2.4, D - 1.0, 0, 0.6 * (k + 1)), MARBLE if k % 2 else STONE, Wl)
    ruins.wall(M, 1.0, W - 1.0, D - 1.6, D, 4.6, rnd, Wl, bite=0.5, step=3.0)
    for (a, b) in ((22.0, 37.0), (112.0, 121.0)):
        M.air(M.box(a, b, 43.0, D - 1.6, 0.2 + rnd.random() * 0.4, 99))
        ruins.rubble(M, rnd, a, b, 44.0, D - 2.0, 7, Wl, 0.6, 1.4)
    # 皇帝的看台：看台中間突出的台基（高 3.4）、四根斷柱
    M.add(M.box(68.0, 82.0, 40.0, D - 1.6, 0, 3.4), MARBLE, Wl)
    for (x, y, h) in ((69.5, 41.5, 4.2), (80.5, 41.5, 1.6), (69.5, 52.0, 0.0), (80.5, 52.0, 3.0)):
        ruins.stub(M, x, y, 0.35, h, Wl)
    # ── 門：兩座門墩（4 × 4、高 6，頂咬掉一角）；往 Nea 的兩道廊只剩柱礎與斷柱（y 1～7） ──
    for x in (66.0, 84.0):
        M.add(M.box(x - 2.0, x + 2.0, 0, 4.0, 0, 6.0), BANDED, Wl)
        M.air(M.box(x - 2.1, x + 2.1, -0.1, 2.0 + rnd.random() * 2.0, 4.4 + rnd.random() * 1.2, 99))
    for x in (70.0, 80.0):
        for y in (1.5, 5.0):
            h = rnd.random()
            ruins.stub(M, x, y, 0.3, 0.0 if h < 0.35 else 0.8 + h * 2.6, Wl)
    M.MAT[M.S & M.full(M.Z < 1.2) & (M.MAT == BANDED)] = STONE
    # 場的兩頭各一根標記石柱（設計）
    for x in (12.0, W - 12.0):
        ruins.stub(M, x, 24.0, 0.45, 2.6, Wl, mat=STONE)
    ruins.rubble(M, rnd, 4.0, W - 4.0, 2.0, 8.0, 12, Wl, 0.5, 1.2)
    # ── 野樹：場上與牆邊幾棵（離牆、看台 ≥ 2 m） ──
    for (x, y, h, w) in ((30.0, 14.0, 6.0, 4.4), (96.0, 34.0, 5.0, 3.8), (132.0, 12.0, 6.5, 4.6), (48.0, 36.0, 4.5, 3.4)):
        M.tree(x, y, h, w, T)
    G, L = M.finish(shell_m=0.8, seed=886, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'看台後牆頂（m）': 4.6, '門墩頂（m）': 6.0}
