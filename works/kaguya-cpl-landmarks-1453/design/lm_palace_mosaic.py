# 大皇宮中層台地（馬賽克柱廊院一帶）1453：上層台地（Daphne）的下坡那一邊 ——
#   上坡那一邊：上層台地擋土牆前的一排拱頂下部結構（拱口朝下坡；幾個塌了、前面一堆碎石）—— 高 ＝ 兩層台地的整平面差（規劃量的 39.97 − 34.25 m），頂跟上層台地的地面齊；
#   中間：柱廊院（今天的馬賽克博物館那一帶）—— 7～9 世紀地坪已被大理石板蓋住（TAN）⇒ 1453 年是埋在廢墟下的台地：四面柱廊只剩柱礎與斷柱、院子是長草的土堆；
#   院子上坡那一邊一座有後殿的大廳（殘牆）；其他地方是菜畦、橄欖、碎石；下坡那一邊的女兒牆。
#   ⚠ 院子的大小、大廳、下部結構的拱數全是設計決定；馬賽克地坪的原面積約 1,872～1,900 m²、地坪帶寬約 6 m（≈ 柱廊進深）是量過的。
#   ⛔ 不做：馬賽克本身（1453 年埋在下面）、Arasta 市場（1610 年代）、馬賽克博物館的建築。
#   研究整理：scratchpad/cpl/research_batch3.md §4（b1）；院中心 ＝ 模型 82, 29（OSM way 1153966162，41.004295, 28.977433）。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK, DARK

KEY = 'palace-mosaic'
TITLE = '大皇宮中層台地 1453（馬賽克柱廊院、拱頂下部結構）'
TITLE_SHORT = '大皇宮中層台地 1453'
MPV = 0.4
W, D, H = 160.0, 100.0, 12.0
ARC_H = 5.6                                   # 下部結構的牆頂：兩層台地的整平面差 5.72 m（Blocksail 規劃 2026-10-23）留 0.12 m 不跟上層的地面疊
META = {'kind': 'building', 'use': 'palace-mosaic', 'style': 'roman', 'lot': '160,100', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('ground', 1, '台地（草、菜畦、女兒牆）'), ('vaults', 2, '拱頂下部結構（上層台地擋土牆前的一排拱）'),
         ('ruins', 3, '柱廊院與大廳的殘跡、碎石'),
         ('trees-olive', 4, '橄欖（遊戲換成生成式的橄欖）', {'kind': 'tree', 'tree': 'olive'}),
         ('trees-cypress', 5, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}),
         ('field', 6, '菜畦（遊戲換成生成式的作物）', {'kind': 'field'}))
PROV = {
    '柱廊院（今馬賽克博物館）的位置': '參考資料：OSM way 1153966162',
    '馬賽克原面積約 1,872～1,900 m²、地坪帶寬約 6 m': '參考資料：Wikipedia／Turkish Archaeological News（Great Palace Mosaic Museum）',
    '地坪 7～9 世紀已被大理石板蓋住 ⇒ 1453 年埋在廢墟下': '參考資料：Turkish Archaeological News（推估）',
    '台地系統與拱頂下部結構多半還在（當監獄用）': '參考資料：The Byzantine Legacy（推估）',
    '院子的大小、大廳、下部結構的拱數與塌了哪幾個、菜畦與樹': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.2)
    M.band_z0 = 1.0
    rnd = random.Random(1204)
    G1, V, R = 1, 2, 3
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    ruins.wall(M, 0, W, 0, 1.2, 1.4, rnd, G1, bite=0.9, step=3.0)
    ruins.plots(M, rnd, 122.0, 156.0, 6.0, 46.0, G1, field=6)
    # ── 上坡那一邊（y D）：上層台地擋土牆前的一排拱頂下部結構 ──
    y0, y1 = D - 4.0, D
    M.add(M.box(0, W, y0, y1, 0, ARC_H), BANDED, V)
    fallen_k = {3, 4, 11, 19}
    for k in range(26):
        xc = 4.0 + k * 6.0
        if k in fallen_k:                                                   # 塌了：拱頂沒了、牆頂缺一口，前面一堆碎石
            M.air(M.box(xc - 2.4, xc + 2.4, y0 - 1, y1 + 1, 1.6 + rnd.random() * 1.6, 99))
            ruins.rubble(M, rnd, xc - 3.0, xc + 3.0, y0 - 5.0, y0, 5, V, 0.8, 1.8)
        else:
            M.air(M.arch_open(xc, y0 + 1.6, 0, 4.4, 3.6, normal='y', depth=3.4))
            M.add(M.arch_open(xc, y1 - 0.5, 0, 4.4, 3.6, normal='y', depth=1.0), DARK, V)   # 拱裡面暗（後面是土）
    M.add(M.box(0, W, y0 - 0.3, y0, ARC_H - 0.5, ARC_H), MARBLE, V)          # 拱上的腰線
    # ── 柱廊院：中心 (82, 29)、外框 66 × 44 m、柱廊進深 6 m；只剩柱礎與斷柱，院子是長草的土堆 ──
    cx, cy, hw, hd = 82.0, 29.0, 33.0, 22.0
    ruins.wall(M, cx - hw, cx + hw, cy - hd, cy - hd + 1.2, 2.4, rnd, R, bite=0.9)
    ruins.wall(M, cx - hw, cx + hw, cy + hd - 1.2, cy + hd, 3.2, rnd, R, bite=0.9)
    ruins.wall(M, cx - hw, cx - hw + 1.2, cy - hd, cy + hd, 2.8, rnd, R, bite=0.9)
    ruins.wall(M, cx + hw - 1.2, cx + hw, cy - hd, cy + hd, 2.0, rnd, R, bite=0.9)
    ix0, ix1, iy0, iy1 = cx - hw + 6.0, cx + hw - 6.0, cy - hd + 6.0, cy + hd - 6.0
    pts = [(x, iy0) for x in range(int(ix0), int(ix1) + 1, 4)] + [(x, iy1) for x in range(int(ix0), int(ix1) + 1, 4)] + \
          [(ix0, y) for y in range(int(iy0) + 4, int(iy1), 4)] + [(ix1, y) for y in range(int(iy0) + 4, int(iy1), 4)]
    for (x, y) in pts:
        h = rnd.random()
        ruins.stub(M, x, y, 0.32, 0.0 if h < 0.4 else 0.9 + h * (4.0 if h > 0.85 else 1.6), R)
    for k in range(14):                                                     # 院子裡露出來的幾片大理石板（蓋在馬賽克上面的那一層）
        sx, sy = ix0 + 2.0 + rnd.random() * (ix1 - ix0 - 8.0), iy0 + 2.0 + rnd.random() * (iy1 - iy0 - 6.0)
        M.add(M.box(sx, sx + 2.4 + rnd.random() * 3.6, sy, sy + 1.6 + rnd.random() * 2.4, 0, 2 * MPV), MARBLE, R)
    ruins.rubble(M, rnd, ix0 + 2.0, ix1 - 2.0, iy0 + 2.0, iy1 - 2.0, 12, R, 0.6, 1.8)
    for (px, py, L_, ax) in ((60.0, 12.0, 4.2, 'x'), (101.0, 20.0, 3.6, 'y'), (75.0, 44.0, 5.0, 'x')):
        ruins.fallen(M, px, py, 0.32, L_, R, axis=ax)
    # ── 院子上坡那一邊：有後殿的大廳（殘牆，後殿朝 +y）──
    ruins.shell(M, 66.0, 98.0, 54.0, 72.0, 8.5, 1.6, rnd, R, bite=0.55)
    M.add(M.apse(82.0, 72.0, 7.0, 7, 0, 7.0, '+y') & ~M.apse(82.0, 71.0, 5.6, 7, -1, 99, '+y'), BANDED, R)
    M.air(M.arch_open(82.0, 54.0, 0, 5.0, 3.6, normal='y', depth=2.4))
    ruins.rubble(M, rnd, 8.0, 150.0, 50.0, 90.0, 40, R)
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    # ── 樹 ──
    for x in range(10, 44, 7):
        for y in range(8, 46, 7):
            M.tree(x + rnd.uniform(-1, 1), y + rnd.uniform(-1, 1), rnd.uniform(4.0, 6.0), rnd.uniform(4.0, 5.0), 4)
    for (tx, ty) in ((46.0, 58.0), (50.0, 66.0), (114.0, 58.0), (118.0, 66.0), (140.0, 70.0), (146.0, 80.0)):
        M.tree(tx, ty, 10.0, 2.2, 5)
    G, L = M.finish(shell_m=0.8, seed=1204, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'下部結構牆頂（m）': ARC_H}
