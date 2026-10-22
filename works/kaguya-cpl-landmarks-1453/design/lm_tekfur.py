# 波菲羅根尼圖斯宮（Palace of the Porphyrogenitus，Tekfur Sarayı；多數學者定在 1261–1291）1453：三層的宮殿主樓橫跨在布雷契耐那一段內外兩道城牆之間（東西短邊在二樓高度擱在牆頂）、
#   北邊是兩道牆之間的庭院（北端橫牆封閉、東北角門通城內、西牆門通 parateichion）、庭院西北端另一座宅邸。圍城時是地標（Kritoboulos），有屋頂、還在用（Buondelmonti 標 Palatium Imperatoris）。
#   ⛔ 不做：1719 年後的陶窯、19 世紀玻璃坊、1864 火災後的空殼、2010s 重建的屋頂與玻璃與電梯。城牆本身是規劃的牆（另外畫）⇒ 這裡只到主樓兩端。
#   研究整理：scratchpad/cpl/research_palaces_cisterns.md §1；占地：OSM relation 21597522（71.4 × 32.1 m）、主樓 way 530509576（24.5 × 11.8 m）。
import numpy as np
import byz
from byz import BANDED, STONE, MARBLE, TILE, LEAD, BRICK, GREEN

KEY = 'tekfur'
TITLE = '波菲羅根尼圖斯宮 1453（Palace of the Porphyrogenitus，Tekfur Sarayı，1261–91）'
TITLE_SHORT = '波菲羅根尼圖斯宮 1453'
MPV = 0.2
W, D, H = 32.0, 71.0, 28.0
META = {'kind': 'building', 'use': 'tekfur-saray', 'style': 'roman', 'lot': '32,71', 'base': 0, 'variant': 'a'}
PARTS = (('body', 1, '主樓（三層、陽台、托架小禮拜堂）'), ('roof', 2, '屋頂'), ('court', 3, '庭院（圍牆、門、西北的宅邸）'))
PROV = {
    '主樓 24.5 × 11.8 m、三層、總高 > 25 m': '參考資料：OSM way 530509576（描線）；van Millingen 1899 ch.VII；Tafferner 1688；TBL',
    '北立面：一樓 4 個大拱、二樓 5 扇大窗、三樓四面開窗；窗有大理石框': '參考資料：Wikipedia；van Millingen 1899',
    '下段大塊琢石；上段磚與石灰岩交替、紅白幾何拼磚、紅白分段拱石': '參考資料：TBL',
    '三樓東南角托架陽台；南面托架小禮拜堂': '參考資料：van Millingen 1899；TBL；Tafferner 1688（可容 6 人）',
    '庭院約 25 × 50–55 m、北端橫牆、東北門、西門；西北端另一座宅邸（L 形約 25 × 13 m）': '參考資料：van Millingen 1899；OSM relation 21597522 的其他 member（用途是推估）',
    '各層高 9／7／8 m、緩坡屋頂': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.6, 0.5)
    M.band_z0 = 6.0
    # 主樓：模型 y 0 ＝ 北（庭院北端）；主樓在南端
    x0, x1, y0, y1 = 3.8, 28.3, 58.6, 70.4
    zt = 24.0
    M.add(M.box(x0, x1, y0, y1, 0, zt), BANDED, 1)
    M.add(M.hip(x0, x1, y0, y1, zt, 1.6, 0.3), TILE, 2)
    M.add(M.box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, zt - 0.6, zt), MARBLE, 1)          # 簷口
    for zz in (9.0, 16.0):                                                              # 樓層線
        M.add(M.box(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, zz - 0.3, zz), MARBLE, 1)
    # 北立面：一樓 4 拱（拱廊、深 2 m）、二樓 5 窗、三樓 6 窗；南、東、西三樓也開窗
    for k in range(4):
        xc = x0 + (k + 0.5) * (x1 - x0) / 4
        M.air(M.arch_open(xc, y0 + 1.0, 0.0, 7.6, 4.0, normal='y', depth=2.0))
        M.win(M.arch_open(xc, y0 + 2.0, 0.0, 7.4, 3.6, normal='y', depth=2.4))
    for k in range(5):
        xc = x0 + (k + 0.5) * (x1 - x0) / 5
        M.win(M.arch_open(xc, y0, 10.6, 14.6, 1.8, normal='y', depth=2.0))
        M.add(M.arch_open(xc, y0 - 0.2, 10.4, 14.8, 2.4, normal='y', depth=0.4) & ~M.arch_open(xc, y0 - 0.2, 10.6, 14.6, 1.8, normal='y', depth=0.6), MARBLE, 1)
    for k in range(6):
        xc = x0 + (k + 0.5) * (x1 - x0) / 6
        for yy in (y0, y1):
            M.win(M.arch_open(xc + (0.8 if yy == y1 else 0.0), yy, 17.6, 21.6, 1.6, normal='y', depth=2.0))
    for xx in (x0, x1):
        for yy in (61.5, 64.5, 67.5):
            M.win(M.arch_open(xx, yy, 17.6, 21.6, 1.4, normal='x', depth=2.0))
    for k in range(4):                                                                  # 南面二樓（窗不跟上下對齊）
        M.win(M.arch_open(x0 + 3.5 + k * 5.8, y1, 11.0, 14.2, 1.4, normal='y', depth=2.0))
    # 紅白幾何拼磚帶：上段每一層窗下一條棋盤帶
    for zb in (15.0, 22.4):
        cb = ((np.floor(M.X / 0.4) + np.floor(M.Z / 0.4)) % 2 == 0)
        band = M.full(M.box(x0, x1, y0, y1, zb - 0.8, zb)) & M.S
        M.MAT[band & M.full(cb)] = MARBLE
        M.MAT[band & ~M.full(cb)] = BRICK
    # 下段大塊琢石
    M.MAT[M.S & M.full(M.Z < 6.0) & (M.MAT == BANDED)] = STONE
    # 三樓東南角托架陽台、南面托架小禮拜堂
    M.add(M.box(x1 - 4.0, x1 + 1.4, y1 - 0.2, y1 + 0.0, 0, 0), STONE, 1)
    M.add(M.box(x1 - 3.0, x1, y1 - 3.0, y1, 16.0, 16.4) | M.box(x1, x1 + 1.4, y1 - 5.0, y1, 16.0, 16.4), MARBLE, 1)
    M.add(M.box(x1, x1 + 1.4, y1 - 5.0, y1, 16.4, 17.4) & ~M.box(x1, x1 + 1.2, y1 - 4.8, y1, 16.4, 17.4), MARBLE, 1)
    for yy in (y1 - 4.4, y1 - 0.8):
        M.add(M.box(x1, x1 + 1.0, yy - 0.3, yy + 0.3, 14.6, 16.0) & (M.Z - 14.6 > (x1 + 1.0 - M.X) * 0.0), STONE, 1)
    cx = 12.0
    M.add(M.apse(cx, y1 - 0.1, 1.8, 3, 9.6, 15.6), BANDED, 1)
    for k in range(4):
        M.add(M.box(cx - 1.6 + k * 0.2, cx + 1.6 - k * 0.2, y1, y1 + 1.6 - k * 0.4, 8.8 + k * 0.2, 9.0 + k * 0.2), STONE, 1)
    M.add(M.semidome(cx, y1 - 0.1, 15.6, 1.6, '+y'), LEAD, 2)
    M.win(M.ring_windows(cx, y1, 0.6, 2.4, 11.6, 14.4, [90], 0.35))
    # 庭院：東牆（主樓東北角往北）、北端橫牆（東北角門）、西牆（門通 parateichion）；西北的宅邸（L 形，二層）
    C = 3
    M.add(M.box(28.3, 30.3, 0.0, y0, 0, 8.0), BANDED, C)
    M.add(M.box(1.0, 30.3, 0.0, 1.8, 0, 8.0), BANDED, C)
    M.add(M.box(1.0, 3.0, 1.8, y0, 0, 8.0), BANDED, C)
    M.door(M.arch_open(26.0, 0.0, 0, 4.2, 3.2, normal='y', depth=3.0))
    M.air(M.arch_open(26.0, 0.9, 0, 4.2, 3.2, normal='y', depth=1.6))
    M.door(M.arch_open(1.0, 40.0, 0, 3.0, 1.6, normal='x', depth=2.0))
    M.add(M.box(3.0, 16.0, 1.8, 26.0, 0, 10.0) & ~M.box(10.0, 16.0, 8.0, 26.0, 0, 99), BANDED, C)
    M.add(M.hip(3.0, 10.0, 1.8, 26.0, 10.0, 1.2, 0.35), TILE, C)
    M.add(M.hip(3.0, 16.0, 1.8, 8.0, 10.0, 1.2, 0.35) & ~M.box(3.0, 10.0, 1.8, 26.0, 0, 99), TILE, C)
    for yy in (6.0, 12.0, 18.0, 23.0):
        M.win(M.arch_open(10.0, yy, 5.0, 8.4, 1.4, normal='x', depth=2.0))
        M.win(M.arch_open(3.0, yy, 5.0, 8.4, 1.6, normal='x', depth=2.0))
    M.MAT[M.S & M.full(M.Z < 1.0) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=1261)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(26.0, 0.2, 0), 'top': M.cell(16.0, 64.5, 25.4)}
    return G, L, anchors, {'主樓簷口（m）': zt}
