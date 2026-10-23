# 聖波利尤克托斯教堂（St Polyeuktos，Saraçhane；Anicia Juliana 約 518–527）1453：沒有上部結構的廢墟台地 ——
#   教堂地坪架在巨大的下部結構上、比中庭高約 5 m（Harrison 1969）；10 世紀末到 11 世紀初已廢棄、12 世紀上半大規模拆石、
#   12 世紀下半中庭成了墓地（百多座石棺墓）、中庭北側的下部結構封門抹灰改成蓄水池；1204 年後十字軍又搬走雕刻。
#   做成：西邊低的中庭（草、殘存的鋪面、一片停用的石棺墓、矮牆殘段、北側有後殿的小建築殘牆）、
#   東邊 52 × 52 m 的磚砌台地（四邊被咬得參差、台頂被挖出一個一個取石坑、兩道 8 m 厚的基礎牆露出來、側邊的半圓 exedra 殘牆、散落的大理石塊、野樹）、
#   台地西面一排拱室的口（北邊幾個是蓄水池）、中央大階梯只剩一半。
#   ⚠ 1453 年地面上還露出多少沒有直接記載 ⇒ 殘存的程度、坑、樹都是設計決定。
#   研究整理：scratchpad/cpl/research_batch6.md §5；位置照衛星影像判讀（±5 m）、東西向。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK, DARK

KEY = 'polyeuktos'
TITLE = '聖波利尤克托斯教堂的廢墟台地 1453（取石坑、基礎牆、中庭的石棺墓）'
TITLE_SHORT = '聖波利尤克托斯廢墟 1453'
MPV = 0.4
W, D, H = 52.0, 78.0, 13.0
META = {'kind': 'building', 'use': 'polyeuktos', 'style': 'roman', 'lot': '52,78', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('ground', 1, '中庭（草、鋪面殘段、石棺墓）'), ('ruins', 2, '台地、基礎牆、exedra、拱室、階梯、碎石'),
         ('trees', 3, '野樹（遊戲換成生成式的樹）', {'kind': 'tree', 'tree': 'broadleaf'}))
PROV = {
    '教堂約 52 × 52 m＋西側中庭 26 m；地坪比中庭高約 5 m、中央大階梯': '參考資料：Harrison & Fıratlı 1969（TAED）；Wikipedia（Church of St. Polyeuctus）',
    '兩道基礎牆各 8 m 厚': '參考資料：The Byzantine Legacy（Polyeuktos）',
    '中殿兩側各 3 個半圓 exedra': '參考資料：Wikipedia；The Byzantine Legacy',
    '11 世紀前廢棄、12 世紀拆石、中庭成墓地、北側下部結構改蓄水池': '參考資料：Harrison & Fıratlı 1969',
    '1453 年露出多少、坑、殘牆的高度、樹': '設計決定',
}
TOP = 5.0                                      # 台地頂（比中庭高）


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.0)
    M.band_z0 = 0.0
    rnd = random.Random(524)
    G1, R, T = 1, 2, 3
    y0 = 26.0                                  # 台地西緣（中庭 y 0～26）
    # ── 中庭：草、殘存的鋪面、矮牆殘段 ──
    M.add(M.box(0, W, 0, y0, 0, MPV), byz.GREEN, G1)
    for k in range(14):
        x, y = rnd.uniform(4, W - 8), rnd.uniform(3, y0 - 6)
        M.add(M.box(x, x + rnd.uniform(2, 5), y, y + rnd.uniform(2, 4), 0, MPV), MARBLE if k % 2 else STONE, G1)
    ruins.wall(M, 0, W, 0, 0.8, 1.6, rnd, R, mat=STONE, bite=0.9, step=3.0)
    ruins.wall(M, 0, 0.8, 0, y0, 1.6, rnd, R, mat=STONE, bite=0.9, step=3.0)
    ruins.wall(M, W - 0.8, W, 0, y0, 1.6, rnd, R, mat=STONE, bite=0.9, step=3.0)
    # 中庭北側有後殿的小建築（洗禮堂？）：殘牆
    ruins.shell(M, 1.5, 11.5, 6.0, 16.0, 3.6, 0.8, rnd, R, bite=0.7, floor=None)
    M.add(M.apse_x(11.5, 11.0, 2.4, 7, 0, 3.0, '+x') & ~M.apse_x(10.9, 11.0, 1.7, 7, -1, 99, '+x'), BANDED, R)
    # 停用的石棺墓（中庭東半，沿列排）
    for i in range(7):
        for j in range(5):
            if rnd.random() < 0.25:
                continue
            x, y = 16.0 + i * 4.4 + rnd.uniform(-0.3, 0.3), 3.0 + j * 2.6
            if 21.0 < x < 31.0 and y > 15.0:
                continue                       # 階梯前面留空
            M.add(M.box(x, x + 2.2, y, y + 0.9, 0, 0.8), MARBLE if rnd.random() < 0.6 else STONE, G1)
            if rnd.random() < 0.5:
                M.add(M.gable(x - 0.1, x + 2.3, y - 0.1, y + 1.0, 0.8, 0.35, 'x'), MARBLE, G1)
    # ── 台地：磚砌下部結構 52 × 52、頂 5 m；四邊咬得參差 ──
    M.add(M.box(0, W, y0, D, 0, TOP), BRICK, R)
    for k in range(40):
        side = k % 4
        a = rnd.uniform(0, 52.0)
        w, d, z = rnd.uniform(2, 6), rnd.uniform(0.8, 2.6), rnd.uniform(1.5, TOP - 0.4)
        if side == 0:
            M.air(M.box(a, a + w, y0 - 1, y0 + d, z, 99))
        elif side == 1:
            M.air(M.box(a, a + w, D - d, D + 1, z, 99))
        elif side == 2:
            M.air(M.box(-1, d, y0 + a, y0 + a + w, z, 99))
        else:
            M.air(M.box(W - d, W + 1, y0 + a, y0 + a + w, z, 99))
    # 台頂：取石坑（挖進去 1～3 m）＋草蓋在沒挖的地方
    pits = M.full(M.Z < -99)
    for k in range(16):
        cx, cy = rnd.uniform(6, W - 6), rnd.uniform(y0 + 6, D - 6)
        r = rnd.uniform(2.0, 4.5)
        pits = pits | M.cyl(cx, cy, r, TOP - rnd.uniform(1.0, 3.0), 99)
    M.air(pits & M.full(M.Z < TOP + 1))
    M.add(M.box(0, W, y0, D, TOP - MPV, TOP) & ~pits & M.full(M.MAT == BRICK), byz.GREEN, G1)
    # 兩道 8 m 厚的基礎牆露出台頂（東西向、斷斷續續）
    for (xa, xb) in ((8.0, 16.0), (36.0, 44.0)):
        y = y0 + 4.0
        while y < D - 4.0:
            L = rnd.uniform(3.0, 8.0)
            M.add(M.box(xa, xb, y, min(D - 4.0, y + L), TOP - MPV, TOP + rnd.uniform(0.6, 2.4)), BRICK, R)
            y += L + rnd.uniform(2.0, 5.0)
    # 中殿兩側各 3 個半圓 exedra 的殘牆（台頂上）
    for k in range(3):
        cy = y0 + 14.0 + k * 13.0
        for (cx, s) in ((17.5, 1), (34.5, -1)):
            ring = M.cyl(cx, cy, 4.2, TOP - MPV, TOP + rnd.uniform(1.0, 3.2)) & ~M.cyl(cx, cy, 3.4, -1, 99)
            half = M.full(M.X * s < cx * s)   # 朝外那一半
            M.add(ring & half, BANDED, R)
    # 台地西面一排拱室的口（北邊三個是蓄水池：封了一半、裡面暗）
    for k in range(8):
        x = 4.0 + k * 6.2
        M.air(M.arch_open(x, y0, 0.4, 3.4, 2.4, normal='y', depth=4.0))
        M.add(M.box(x - 1.3, x + 1.3, y0 + 3.6, y0 + 4.2, 0, 3.6), DARK, R)
        if k < 3:
            M.add(M.box(x - 1.3, x + 1.3, y0 - 0.2, y0 + 0.4, 0, 1.8), STONE, R)
    # 中央大階梯（中庭 → 台頂；只剩一半）
    for k in range(12):
        z = (k + 1) * TOP / 12.0
        ya = y0 - 6.0 + k * 0.5
        M.add(M.box(21.0, 31.0, ya, y0, 0, z) & M.full((M.X < 26.0) | (M.Z < z - 1.6)), MARBLE, R)
    ruins.rubble(M, rnd, 26.0, 32.0, y0 - 6.0, y0 - 1.0, 8, R, 0.5, 1.2)
    # 台頂散落的大理石塊與碎石
    for k in range(30):
        x, y = rnd.uniform(3, W - 3), rnd.uniform(y0 + 3, D - 3)
        a, b = rnd.uniform(0.8, 2.4), rnd.uniform(0.6, 1.4)
        M.add(M.box(x, x + a, y, y + b, TOP - MPV, TOP + rnd.uniform(0.4, 1.0)) & ~pits, MARBLE, R)
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    # 野樹：台頂與中庭西邊（離牆、坑 ≥ 2 m 照種子挑）
    for (x, y, h, w) in ((24.0, 40.0, 6.5, 4.8), (46.0, 62.0, 5.5, 4.0), (5.0, 70.0, 6.0, 4.4), (28.0, 72.0, 5.0, 3.6), (40.0, 9.0, 5.5, 4.0)):
        M.tree(x, y, h, w, T, z0=TOP if y > y0 else 0.0)
    G, L = M.finish(shell_m=0.8, seed=524, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'台地頂（m）': TOP}
