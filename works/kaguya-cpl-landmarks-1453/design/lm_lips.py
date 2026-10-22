# 利普斯修道院（Lips／Fenari İsa）1453：北堂（907，Theotokos，四柱十字、屋頂四座小禮拜堂）＋南堂（約 1286–1304，Theodora，St John Prodromos，三面迴廊）＋ 14 世紀初的外迴廊（沿南堂南側與西側）。
#   ⛔ 不做：宣禮塔、北堂改柱為尖拱、1847/48 年南堂改柱為墩。北主頂、南主頂、南堂前廊頂今天都是鄂圖曼重建 ⇒ 照拜占庭式做（8 窗圓拱、窗間有肋）。
#   研究整理：scratchpad/cpl/research_columns_churches.md §B6；占地：OSM way 329095050（29.5 × 25.3 m、東西軸方位 113.8°）。
#   ⚠ 史料表原本的地塊 rot 114（正面朝南）⇒ 改成正面朝西（rot 203.75、寬 30 × 深 26）。
import byz, church
from byz import BANDED, STONE, LEAD, TILE, MARBLE

KEY = 'lips'
TITLE = '利普斯修道院 1453（Lips，北堂 907 與南堂 1286–1304）'
TITLE_SHORT = '利普斯修道院 1453'
MPV = 0.2
W, D, H = 30.0, 26.0, 20.0
META = {'kind': 'building', 'use': 'lips', 'style': 'roman', 'lot': '30,26', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（兩座教堂、前廊、外迴廊、後殿）'), ('roof', 2, '屋頂（七個穹頂、瓦）'))
PROV = {
    '北堂中殿 13 × 9.5 m、四柱十字、前廊 3 開間、屋頂 4 座小禮拜堂（西兩角、東 prothesis／diakonikon 上）': '參考資料：Wikipedia；TBL；van Millingen 1912',
    '南堂：方形核心 1 穹頂、三面迴廊、前廊也有穹頂；主後殿外 7 面、兩層壁龕；其他後殿外 3 面；東端大理石簷帶刻銘文': '參考資料：TBL；van Millingen 1912',
    '外迴廊沿南堂南側與西側（14 世紀初）': '參考資料：van Millingen 1912；TBL',
    '牆：北堂磚與小粗石交替；南堂約 5 皮磚對 3–4 皮琢石': '參考資料：TBL；Wikipedia',
    '1453 年 7 個穹頂': '參考資料：研究整理（北主頂、4 小頂、南主頂、南前廊頂）',
    '各量體的牆高、穹頂徑': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.9, 0.6)
    P = {
        'naos': {'x': [1.0, 11.5], 'y': [7.0, 20.0], 'z': 9.0, 'arm_w': 4.2, 'arm_z': 11.5, 'roof': 'barrel', 'rise': 1.2},   # 北堂
        'domes': [{'cx': 6.25, 'cy': 13.5, 'r': 2.7, 'n': 8, 'z0': 12.2, 'h': 2.8, 'win': 8, 'rise': 2.1, 'ribs': 8, 'cross': True},
                  {'cx': 2.6, 'cy': 8.6, 'r': 1.05, 'n': 8, 'z0': 9.3, 'h': 1.6, 'win': 4, 'rise': 0.9, 'ribs': 8},          # 屋頂四座小禮拜堂
                  {'cx': 9.9, 'cy': 8.6, 'r': 1.05, 'n': 8, 'z0': 9.3, 'h': 1.6, 'win': 4, 'rise': 0.9, 'ribs': 8},
                  {'cx': 2.6, 'cy': 18.4, 'r': 1.05, 'n': 8, 'z0': 9.3, 'h': 1.6, 'win': 4, 'rise': 0.9, 'ribs': 8},
                  {'cx': 9.9, 'cy': 18.4, 'r': 1.05, 'n': 8, 'z0': 9.3, 'h': 1.6, 'win': 4, 'rise': 0.9, 'ribs': 8},
                  {'cx': 17.0, 'cy': 13.0, 'r': 3.0, 'n': 8, 'z0': 12.6, 'h': 2.8, 'win': 8, 'rise': 2.4, 'ribs': 8, 'cross': True},   # 南堂
                  {'cx': 17.0, 'cy': 5.5, 'r': 1.6, 'n': 8, 'z0': 9.9, 'h': 1.8, 'win': 4, 'rise': 1.3, 'ribs': 8}],                  # 南堂前廊
        'apses': [{'cx': 6.25, 'r': 2.3, 'facets': 3, 'z': 8.0, 'win': 3, 'win_w': 0.7}, {'cx': 2.6, 'r': 1.0, 'facets': 3, 'z': 6.0},
                  {'cx': 9.9, 'r': 1.0, 'facets': 3, 'z': 6.0},
                  {'cx': 17.0, 'y': 20.0, 'r': 2.8, 'facets': 7, 'z': 9.5, 'win': 3, 'win_w': 0.6}, {'cx': 13.2, 'y': 20.0, 'r': 1.1, 'facets': 3, 'z': 6.5},
                  {'cx': 20.8, 'y': 20.0, 'r': 1.1, 'facets': 3, 'z': 6.5}],
        'bays': [{'x': [1.0, 11.5], 'y': [3.0, 7.0], 'z': 8.0, 'roof': 'shed', 'high': '+y', 'rise': 0.9},                     # 北堂前廊
                 {'x': [11.5, 22.5], 'y': [4.0, 20.0], 'z': 9.5, 'roof': 'flat'},                                               # 南堂（含三面迴廊）
                 {'x': [22.5, 28.5], 'y': [0.6, 21.0], 'z': 7.0, 'roof': 'shed', 'high': '-x', 'rise': 0.9,                     # 外迴廊（南）
                  },
                 {'x': [11.5, 22.5], 'y': [0.6, 4.0], 'z': 7.0, 'roof': 'shed', 'high': '+y', 'rise': 0.9,                      # 外迴廊（西）
                  'arcade_x': [13.5, 20.5], 'arc_z0': 1.0, 'arc_z1': 4.6, 'arc_w': 1.8}],
        'door': [{'x': 17.0, 'y': 0.6, 'w': 1.8, 'h': 3.2}, {'x': 6.25, 'y': 3.0, 'w': 1.6, 'h': 3.0}],
    }
    church.cross_in_square(M, P)
    # 屋頂小禮拜堂的方座（北堂角落屋頂上）
    for cx, cy in ((2.6, 8.6), (9.9, 8.6), (2.6, 18.4), (9.9, 18.4)):
        M.add(M.box(cx - 1.3, cx + 1.3, cy - 1.3, cy + 1.3, 0, 9.3), BANDED, 1)
    # 南堂十字（核心）
    M.add(M.box(11.5, 22.5, 11.0, 15.0, 0, 12.0), BANDED, 1); M.add(M.barrel(11.5, 22.5, 11.0, 15.0, 12.0, 'x', 1.0), TILE, 2)
    M.add(M.box(15.0, 19.0, 4.0, 20.0, 0, 12.0), BANDED, 1); M.add(M.barrel(15.0, 19.0, 4.0, 20.0, 12.0, 'y', 1.0), TILE, 2)
    # 外迴廊南牆的拱龕（2–3 層退縮線腳）：暗一格的淺龕
    for yy in range(3, 20, 3):
        M.win(M.arch_open(28.5, yy + 0.5, 1.2, 5.0, 1.8, normal='x', depth=0.8))
    # 南堂東端的大理石簷帶（銘文）
    M.add(M.box(11.5, 22.5, 19.8, 20.3, 8.6, 9.1), MARBLE, 1)
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=907)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(17.0, 0.2, 0), 'dome-top': M.cell(17.0, 13.0, 17.6)}
    return G, L, anchors, {}
