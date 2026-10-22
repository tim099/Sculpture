# 全能者修道院（Pantokrator／Zeyrek）1453：三座教堂南北並排 —— 南堂（Pantokrator，1118–24）、中間的皇家禮拜堂（St Michael，heroon：Komnenos 與 Palaiologos 的皇陵）、北堂（Eleousa，1134 後）；1136 年前加的外前廊。
#   ⛔ 不做：西立面的磚造宣禮塔（可能是 Fatih 時代）、18 世紀的墩、鄂圖曼的 konak。北堂穹頂今天是 1766 年後重建的 ⇒ 照南堂縮小。
#   研究整理：scratchpad/cpl/research_columns_churches.md §B3；占地：OSM way 137519649（58.7 × 31.1 m、東西軸方位 113.5°）。
#   ⚠ 史料表原本的地塊 rot 114（正面朝南）是照長軸取的 ⇒ 改成正面朝西（rot 203.5、寬 59 × 深 31）。
import byz, church
from byz import BANDED, STONE, LEAD, TILE

KEY = 'pantokrator'
TITLE = '全能者修道院 1453（Pantokrator，三座教堂與皇陵禮拜堂，1118–36）'
TITLE_SHORT = '全能者修道院 1453'
MPV = 0.2
W, D, H = 59.0, 31.0, 28.0
META = {'kind': 'building', 'use': 'pantokrator', 'style': 'roman', 'lot': '59,31', 'base': 0, 'variant': 'a'}
PARTS = (('body', 1, '主體（三座教堂、前廊、後殿）'), ('roof', 2, '屋頂（五個穹頂、瓦）'))
PROV = {
    '南堂主穹頂 16 瓣 16 窗、約 7 m；前廊中央鼓座穹頂外 12 邊 12 窗；內外前廊各 5 開間': '參考資料：van Millingen 1912；直徑 serhatengul.com（弱）',
    '皇陵禮拜堂兩個穹頂：西頂 16 瓣 16 窗、東頂橢圓 8 × 7 m 12 窗': '參考資料：van Millingen 1912；尺寸（弱，搜尋摘要）',
    '北堂穹頂 8 窗（今天是鄂圖曼重建）': '參考資料：van Millingen；TDV（1766 後重建）⇒ 設計決定：照南堂縮小、12 瓣',
    '南堂與中堂主後殿外 7 面、三連窗；北堂 5 面；側後殿 3 面': '參考資料：van Millingen 1912（北堂取 vM 的 5 面；Wikipedia 說 7 面）',
    '牆：退縮磚（灰縫約磚的 3 倍）': '參考資料：Wikipedia；外表原本抹粉紅灰泥（TBL）—— 沒做，照磚',
    '各量體的牆高、寬': '設計決定（對照 OSM 外框；南堂是首都現存最大的四柱十字堂）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 0.0)
    P = {
        # 北堂（x 小 ＝ 北）
        'naos': {'x': [2.0, 19.0], 'y': [9.0, 26.0], 'z': 10.0, 'arm_w': 6.4, 'arm_z': 13.0, 'roof': 'barrel', 'rise': 1.5},
        'domes': [{'cx': 10.5, 'cy': 17.5, 'r': 3.8, 'n': 12, 'z0': 13.8, 'h': 3.6, 'win': 12, 'rise': 3.2, 'ribs': 12, 'cross': True},
                  {'cx': 26.5, 'cy': 13.5, 'r': 3.4, 'n': 16, 'z0': 13.8, 'h': 3.2, 'win': 16, 'rise': 3.0, 'ribs': 16},               # 皇陵西頂
                  {'cx': 26.5, 'cy': 21.0, 'r': 4.3, 'n': 12, 'z0': 13.8, 'h': 3.4, 'win': 12, 'rise': 3.4, 'ribs': 24, 'cross': True},  # 皇陵東頂
                  {'cx': 46.0, 'cy': 18.0, 'r': 4.6, 'n': 16, 'z0': 15.5, 'h': 4.2, 'win': 16, 'rise': 3.9, 'ribs': 16, 'cross': True},  # 南堂主頂
                  {'cx': 46.0, 'cy': 6.5, 'r': 2.6, 'n': 12, 'z0': 11.0, 'h': 2.6, 'win': 12, 'rise': 2.2, 'ribs': 24}],                # 南堂內前廊中央
        'apses': [{'cx': 10.5, 'r': 3.2, 'facets': 5, 'z': 9.5, 'win': 3}, {'cx': 5.0, 'r': 1.4, 'facets': 3, 'z': 7.0}, {'cx': 16.0, 'r': 1.4, 'facets': 3, 'z': 7.0},
                  {'cx': 26.5, 'y': 26.0, 'r': 3.4, 'facets': 7, 'z': 10.5, 'win': 3},
                  {'cx': 46.0, 'y': 27.0, 'r': 3.9, 'facets': 7, 'z': 11.0, 'win': 3, 'win_w': 0.9}, {'cx': 39.5, 'y': 27.0, 'r': 1.6, 'facets': 3, 'z': 8.0},
                  {'cx': 52.5, 'y': 27.0, 'r': 1.6, 'facets': 3, 'z': 8.0}],
        'bays': [{'x': [19.0, 34.0], 'y': [8.0, 26.0], 'z': 12.0, 'roof': 'barrel', 'axis': 'y', 'rise': 1.6},                    # 皇陵禮拜堂（東西向長廳）
                 {'x': [36.0, 56.0], 'y': [9.0, 27.0], 'z': 11.0, 'roof': 'flat'},                                                # 南堂中殿（角落）
                 {'x': [36.0, 56.0], 'y': [4.0, 9.0], 'z': 10.0, 'roof': 'shed', 'high': '+y', 'rise': 1.0},                      # 南堂內前廊
                 {'x': [2.0, 19.0], 'y': [4.0, 9.0], 'z': 9.0, 'roof': 'shed', 'high': '+y', 'rise': 1.0},                       # 北堂前廊
                 {'x': [19.0, 34.0], 'y': [4.0, 8.0], 'z': 9.0, 'roof': 'shed', 'high': '+y', 'rise': 1.0},                      # 皇陵禮拜堂前廊
                 {'x': [34.0, 36.0], 'y': [4.0, 27.0], 'z': 9.0, 'roof': 'flat'},                                                 # 南堂與皇陵之間
                 {'x': [56.0, 58.5], 'y': [4.0, 27.0], 'z': 8.0, 'roof': 'shed', 'high': '-x', 'rise': 0.8},                     # 南堂南側
                 {'x': [19.0, 58.5], 'y': [0.4, 4.0], 'z': 8.0, 'roof': 'shed', 'high': '+y', 'rise': 1.0,                       # 外前廊（1136 年前）
                  'arcade_x': [22.5, 26.5, 30.5, 38.0, 42.0, 50.0, 54.0], 'arc_z0': 1.0, 'arc_z1': 5.6, 'arc_w': 2.2}],
        'door': [{'x': 46.0, 'y': 0.4, 'w': 2.4, 'h': 3.8}, {'x': 10.5, 'y': 4.0, 'w': 1.8, 'h': 3.2}],
    }
    church.cross_in_square(M, P)
    # 南堂的十字臂（四柱十字）
    for (x0, x1, y0, y1, ax) in ((36.0, 56.0, 14.4, 21.6, 'x'), (42.4, 49.6, 9.0, 27.0, 'y')):
        M.add(M.box(x0, x1, y0, y1, 0, 14.5), BANDED, 1)
        M.add(M.barrel(x0, x1, y0, y1, 14.5, ax, 1.6), TILE, 2)
    for xx in (36.0, 56.0):
        for k in (-1, 0, 1):
            M.win(M.arch_open(xx, 18.0 + k * 2.0, 10.5, 13.6, 1.0, normal='x', depth=2.4))
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=1118)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(46.0, 0.2, 0), 'dome-top': M.cell(46.0, 18.0, 23.5)}
    return G, L, anchors, {}
