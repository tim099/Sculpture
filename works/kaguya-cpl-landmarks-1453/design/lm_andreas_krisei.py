# 聖安德烈教堂（Hagios Andreas en Krisei，Koca Mustafa Paşa Camii；約 1284 年 Theodora Raoulaina 重建）1453：還是教堂／修道院 ——
#   迴廊式（ambulatory）：中央穹頂（肋拱、鼓座開窗）四面中，北、南、西三面一圈單層迴廊；東邊筒拱的 bema＋半圓主後殿、兩側小後殿；
#   西邊內前廊（3 開間）＋外前廊（5 開間：中間、兩端三個小穹頂）。
#   ⛔ 不做：南北兩個半穹頂（鄂圖曼）、1768 年的穹頂與鼓座、北側五穹頂門廊、宣禮塔、mihrab、外牆的鄂圖曼石材外覆、陵墓與噴泉。
#   研究整理：scratchpad/cpl/research_batch6.md §1；占地：OSM way 329087345 扣掉北門廊（本體 24.8 × 16.5 m）、軸 57°。
import byz, church
from byz import BANDED, BRICK, STONE, LEAD, TILE

KEY = 'andreas-krisei'
TITLE = '聖安德烈教堂 1453（Hagios Andreas en Krisei；迴廊式、肋拱穹頂）'
TITLE_SHORT = '聖安德烈教堂 1453'
MPV = 0.2
W, D, H = 17.0, 25.0, 20.0
META = {'kind': 'building', 'use': 'andreas-krisei', 'style': 'roman', 'lot': '17,25', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（迴廊、內外前廊、後殿）'), ('roof', 2, '屋頂（肋拱穹頂、瓦）'))
PROV = {
    '迴廊式平面、中央穹頂三面迴廊、三連拱兩柱': '參考資料：Van Millingen 1912 Ch. V、Fig. 36（復原）',
    '全長 24.8、寬 16.5、穹頂內徑 5.7、bema＋後殿深 4.7、內前廊 4.4、外前廊 6.2 m': '參考資料：量自 Van Millingen 1912 Fig. 37（±3–5%）',
    '1453 年是肋拱穹頂（現存的是 1768 年鄂圖曼穹頂）': '參考資料：Wikipedia（Koca Mustafa Pasha Mosque）；The Byzantine Legacy',
    '穹頂與各部的高度、磚石帶、外前廊的小穹頂大小': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.2)
    x0, x1 = 0.3, 16.7
    P = {
        # 迴廊＋中央穹頂間（6.0 × 6.3 m）：十字臂寬 6.3 ⇒ 臂比四角高
        'naos': {'x': [x0, x1], 'y': [10.6, 21.4], 'z': 7.6, 'arm_w': 6.3, 'arm_z': 10.4, 'roof': 'gable', 'rise': 1.6},
        'domes': [{'cx': 8.5, 'cy': 16.0, 'r': 3.6, 'n': 16, 'z0': 10.6, 'h': 2.6, 'win': 16, 'rise': 2.9, 'ribs': 16, 'cross': True}],
        'apses': [{'cx': 8.5, 'r': 2.6, 'facets': 5, 'z': 7.4, 'win': 3, 'win_w': 0.7}, {'cx': 3.4, 'r': 1.3, 'facets': 3, 'z': 5.6},
                  {'cx': 13.6, 'r': 1.3, 'facets': 3, 'z': 5.6}],
        'bays': [{'x': [x0, x1], 'y': [6.2, 10.6], 'z': 7.2, 'roof': 'shed', 'high': '+y', 'rise': 0.9},
                 {'x': [x0, x1], 'y': [0.0, 6.2], 'z': 6.2, 'roof': 'shed', 'high': '+y', 'rise': 0.8,
                  'domes': [{'cx': cx, 'cy': 3.1, 'r': 1.5 if cx == 8.5 else 1.2, 'n': 8, 'z0': 6.6, 'h': 0.8, 'win': 0, 'rise': 1.1 if cx == 8.5 else 0.9}
                            for cx in (2.2, 8.5, 14.8)],
                  'arcade_x': [2.2, 5.3, 11.7, 14.8], 'arc_z0': 0.8, 'arc_z1': 4.4, 'arc_w': 1.9}],
        'door': [{'x': 8.5, 'w': 1.8, 'h': 3.4}],
    }
    church.cross_in_square(M, P)
    # 迴廊的南北面：三連拱（兩柱）的位置開一排矮窗
    for xx in (x0, x1):
        for yy in (13.0, 16.0, 19.0):
            M.win(M.arch_open(xx, yy, 3.4, 5.8, 1.1, normal='x', depth=2.4))
    # 外牆的石帶：地面一圈石砌勒腳
    M.MAT[M.S & M.full(M.Z < 1.0) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=1284)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(8.5, 0.2, 0.0), 'dome-top': M.cell(8.5, 16.0, 16.0)}
    return G, L, anchors, {'穹頂頂（m）': round(10.6 + 2.6 + 2.9, 2)}
