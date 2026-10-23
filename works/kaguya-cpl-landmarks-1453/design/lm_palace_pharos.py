# 大皇宮下層台地（金色大殿 Chrysotriklinos、Pharos 聖母小堂、燈塔一帶）1453：帕列奧略時代棄用（Necipoğlu 1991）；Pharos 小堂沒撐過拉丁占領（1204–61）——
#   台地上：金色大殿的八角殘殼（八個半圓壁龕只剩下半截、穹頂塌了、地坪還在）、Pharos 聖母小堂的殘牆（三個後殿朝 +x、前庭一圈斷柱）、
#   燈塔的方塔基（靠海那一邊、塔身斷在半截）、一排斷柱、石板小徑、橄欖與無花果、菜畦、碎石；下坡那一邊的女兒牆（擋土牆本身 ＝ 地塊的石基，遊戲在坡下補）。
#   ⚠ 各棟的位置、大小、高度全是設計決定 —— 只知道「金色大殿是八角形、八個壁龕；Pharos 小堂在它的南、東南，小、三個後殿、有前庭；燈塔在小堂旁邊」。
#   ⛔ 不做：1453 年後的建築（蘇丹艾哈邁德一帶的房子、鐵路）。
#   框 160 × 110 m 沿大競技場的軸（方位 38° 是正面 ＝ 下坡、朝海），後緣接中層台地（lm_palace_mosaic.py）的下坡邊、間隔 1 m。
import math, random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK

KEY = 'palace-pharos'
TITLE = '大皇宮下層台地 1453（金色大殿殘殼、Pharos 小堂、燈塔塔基）'
TITLE_SHORT = '大皇宮下層台地 1453'
MPV = 0.4
W, D, H = 160.0, 110.0, 18.0
META = {'kind': 'building', 'use': 'palace-pharos', 'style': 'roman', 'lot': '160,110', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('ground', 1, '台地（草、菜畦、小徑、女兒牆）'), ('ruins', 2, '廢墟（金色大殿、Pharos 小堂、燈塔塔基、斷柱、碎石）'),
         ('trees-olive', 3, '橄欖（遊戲換成生成式的橄欖）', {'kind': 'tree', 'tree': 'olive'}),
         ('trees-fruit', 4, '無花果（遊戲換成生成式的果樹）', {'kind': 'tree', 'tree': 'fruit'}),
         ('trees-cypress', 5, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}))
PROV = {
    '金色大殿是八角形的覲見廳、八個壁龕': '參考資料：Wikipedia（Chrysotriklinos）',
    'Pharos 聖母小堂在金色大殿的南、東南，名字來自旁邊的燈塔；小、三個後殿、前廊、前庭；沒撐過拉丁占領': '參考資料：Wikipedia（Church of the Virgin of the Pharos、Chrysotriklinos）',
    'Pharos 一帶在布科勒昂海濱那一面': '參考資料：Cambridge Elements（The Great Palace）、pallasweb（Passion Relics and the Pharos Church）',
    '帕列奧略時代棄用；1453 年 Mehmed II 入宮見其荒廢': '參考資料：Necipoğlu 1991 p.3（經 Wikipedia）',
    '台地的框、各棟的位置大小高度、殘存程度、樹與菜畦': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.2)
    M.band_z0 = 1.0
    rnd = random.Random(864)
    G1, R = 1, 2
    # ── 地面：草；從中層台地下來的石板小徑（缺了好幾段）、往小堂的支路；菜畦 ──
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    M.add(M.box(84.0, 87.6, 40.0, D, 0, 2 * MPV) & ((M.Y // 4.0) % 5 != 3), STONE, G1)
    M.add(M.box(84.0, 120.0, 40.0, 43.6, 0, 2 * MPV) & ((M.X // 4.0) % 6 != 2), STONE, G1)
    ruins.plots(M, rnd, 118.0, 156.0, 52.0, 100.0, G1)
    # ── 下坡那一邊（y 0）的女兒牆 ──
    ruins.wall(M, 0, W, 0, 1.2, 1.4, rnd, G1, bite=0.9, step=3.0)
    # ── 金色大殿：八角殘殼（外 r 15、牆厚 2）＋八個半圓壁龕（只剩下半截）；穹頂塌了、地坪還在 ──
    cx, cy = 52.0, 68.0
    hall = M.ngon(cx, cy, 15.0, 8, 0, 11.0, rot=22.5) & ~M.ngon(cx, cy, 13.0, 8, -1, 99, rot=22.5)
    M.add(hall, BANDED, R)
    for k in range(8):
        a = math.radians(k * 45.0)
        nx, ny = cx + math.cos(a) * 14.6, cy + math.sin(a) * 14.6
        niche = M.cyl(nx, ny, 4.4, 0, 3.0 + rnd.random() * 4.0) & ~M.cyl(nx, ny, 3.2, -1, 99) & ~M.ngon(cx, cy, 13.0, 8, -1, 99, rot=22.5)
        M.add(niche, BANDED, R)
        M.air(M.cyl(nx, ny, 2.4, 0.4, 99) & M.ngon(cx, cy, 15.2, 8, -1, 99, rot=22.5))      # 壁龕通進廳裡的開口
    for k in range(10):
        a0 = rnd.random() * 2 * math.pi
        M.air(M.cyl(cx + math.cos(a0) * 15.0, cy + math.sin(a0) * 15.0, 2.0 + rnd.random() * 2.5, 4.0 + rnd.random() * 6.0, 99))
    M.add(M.ngon(cx, cy, 13.0, 8, 0, MPV, rot=22.5), MARBLE, R)
    ruins.rubble(M, rnd, cx - 9.0, cx + 9.0, cy - 9.0, cy + 9.0, 14, R, 0.8, 2.0)
    # ── Pharos 聖母小堂：16 × 14 m 的殘牆、三個後殿朝 +x、穹頂塌了；前庭（西）一圈斷柱 ──
    ruins.shell(M, 92.0, 108.0, 20.0, 34.0, 8.0, 1.2, rnd, R, bite=0.5)
    M.add(M.apse_x(108.0, 27.0, 3.0, 5, 0, 7.0, '+x') & ~M.apse_x(107.0, 27.0, 2.0, 5, -1, 99, '+x'), BANDED, R)
    for yy in (22.6, 31.4):
        M.add(M.apse_x(108.0, yy, 1.4, 5, 0, 5.0, '+x') & ~M.apse_x(107.4, yy, 0.8, 5, -1, 99, '+x'), BANDED, R)
    M.air(M.arch_open(92.0, 27.0, 0, 3.6, 2.4, normal='x', depth=2.0))
    for k in range(5):
        for (x, y) in ((76.0 + k * 3.6, 20.5), (76.0 + k * 3.6, 33.5)):
            h = rnd.random()
            ruins.stub(M, x, y, 0.3, 0.0 if h < 0.3 else 1.0 + h * 3.0, R)
    M.add(M.box(76.0, 92.0, 20.0, 34.0, 0, MPV), MARBLE, R)
    ruins.fallen(M, 80.0, 26.0, 0.3, 3.4, R)
    # ── 燈塔：方塔基 9 × 9 m（中空、塔身斷在 9～13 m），靠海那一邊、小堂的東南 ──
    tx, ty = 128.0, 9.0
    M.add(M.box(tx - 4.5, tx + 4.5, ty - 4.5, ty + 4.5, 0, 13.0) & ~M.box(tx - 2.7, tx + 2.7, ty - 2.7, ty + 2.7, 1.0, 99), STONE, R)
    for k in range(6):
        M.air(M.box(tx - 4.6 + k * 1.6, tx - 3.0 + k * 1.6, ty - 5.0, ty + 5.0, 9.0 + rnd.random() * 4.0, 99))
    M.air(M.arch_open(tx, ty + 4.5, 0.6, 3.4, 1.6, normal='y', depth=2.4))
    ruins.rubble(M, rnd, tx - 9.0, tx + 9.0, ty + 5.0, ty + 14.0, 9, R, 0.6, 1.4)
    # ── 一排斷柱：從金色大殿往小堂的柱廊（y 48） ──
    for k in range(14):
        x = 70.0 + k * 3.8
        h = rnd.random()
        ruins.stub(M, x, 48.0, 0.35, 0.0 if h < 0.3 else 1.2 + h * (5.0 if h > 0.75 else 2.0), R)
    ruins.fallen(M, 96.0, 50.0, 0.35, 4.4, R)
    ruins.rubble(M, rnd, 8.0, 150.0, 10.0, 100.0, 40, R)
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    # ── 樹：橄欖（西南）、無花果（燈塔與小堂之間、廳的東北）、小徑兩邊的柏樹 ──
    for x in range(8, 34, 6):
        for y in range(8, 44, 6):
            M.tree(x + rnd.uniform(-0.8, 0.8), y + rnd.uniform(-0.8, 0.8), rnd.uniform(4.0, 5.5), rnd.uniform(3.8, 4.8), 3)
    for (x, y) in ((116.0, 26.0), (142.0, 22.0), (148.0, 36.0), (74.0, 92.0), (40.0, 98.0), (24.0, 80.0)):
        M.tree(x, y, rnd.uniform(4.0, 5.0), rnd.uniform(4.0, 5.0), 4)
    for y in range(52, 106, 12):
        for x in (81.4, 90.2):
            M.tree(x, y, 10.0, 2.2, 5)
    G, L = M.finish(shell_m=0.8, seed=864, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'金色大殿的牆頂（m）': 11.0, '燈塔塔基頂（m）': 13.0}
