# 聖狄奧多若教堂（St. Theodore，Vefa Kilise Camii／Molla Gürani Camii）1453：四柱十字形（中殿約 9 m 見方）、內前廊、
#   巴列奧略時期（約 1300～1320）的五開間外前廊：南北各多伸出一開間，中間與兩端三座八角形高鼓座穹頂（中間 16 瓣、兩端 8 肋）、
#   立面下層兩組三聯拱夾大門、上層五個拱窗、石帶夾磚帶；北側兩層附屬樓（比外前廊早）；南側四柱迴廊式小禮拜堂（東端半圓後殿）；西南角鐘樓。
#   ⛔ 不做：宣禮塔、外前廊頂上的土耳其式簷口、鄂圖曼時期砌死的南北三聯窗（還原成三聯窗）。
#   研究整理：scratchpad/cpl/research_batch2.md §4；占地：OSM way 111002436（25.0 × 25.3 m、教堂軸 110°）。
import byz, church
from byz import BANDED, BRICK, LEAD, TILE, STONE, MARBLE

KEY = 'vefa'
TITLE = '聖狄奧多若教堂 1453（St. Theodore，Vefa Kilise Camii；巴列奧略外前廊三穹頂）'
TITLE_SHORT = '聖狄奧多若教堂 1453'
MPV = 0.2
W, D, H = 27.0, 22.0, 20.0
META = {'kind': 'building', 'use': 'vefa', 'style': 'roman', 'lot': '27,22', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（中殿、聖所、內外前廊、南側小禮拜堂、北附屬樓、後殿）'), ('roof', 2, '屋頂（穹頂鋪鉛、拱頂鋪瓦）'), ('tower', 3, '西南角鐘樓'))
PROV = {
    '中殿約 9 m 見方；主穹頂鼓座外十二邊、12 窗': '參考資料：Wikipedia；van Millingen 1912',
    '外前廊五開間（西緣 19.9 m）、南北各多伸一開間；三座八角形高鼓座穹頂（中 16 瓣、兩端 8 肋）': '參考資料：van Millingen 1912；Wikipedia；TBL；OSM way 111002436',
    '外前廊立面：下層兩組三聯拱夾大門、上層五個拱窗；1 皮石：2～3 皮磚': '參考資料：van Millingen 1912；Wikipedia',
    '中間穹頂開窗、兩端不開': '設計決定（van Millingen 說三座都不開；Sussex 馬賽克資料庫說中間的先知像在窗之間）',
    '主後殿外五邊、三聯窗；側後殿不凸出': '參考資料：van Millingen 1912',
    '北側兩層附屬樓（比外前廊早）': '參考資料：Varsallona 2018；TBL',
    '南側四柱迴廊、東端半圓後殿（1848 年前已拆）': '參考資料：van Millingen 1912 引 Le Noir、Salzenberg；Müller-Wiener 1977 —— 寬 3.4 m、高是設計決定',
    '西南角鐘樓（基座今存）': '參考資料：TBL；高 17 m、方錐頂、頂層拱窗是設計決定',
    '穹頂鋪鉛': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.7, 0.25)
    M.band_z0 = 0.5
    ax = 13.0                                                    # 教堂軸（x）；x 0 ＝ 北
    bw = 19.9 / 5                                                # 外前廊一開間
    bx = [ax - 2 * bw, ax - bw, ax, ax + bw, ax + 2 * bw]        # 五開間的中心
    P = {
        'naos': {'x': [7.4, 18.6], 'y': [7.5, 18.6], 'z': 8.8, 'arm_w': 4.2, 'arm_z': 11.2, 'roof': 'barrel', 'rise': 1.2},
        'domes': [{'cx': ax, 'cy': 13.05, 'r': 2.6, 'n': 12, 'z0': 11.6, 'h': 3.0, 'win': 12, 'rise': 2.0, 'ribs': 12, 'cross': True}],
        'apses': [{'cx': ax, 'y': 18.6, 'r': 2.7, 'facets': 5, 'z': 8.2, 'win': 3, 'win_w': 0.7}],
        'bays': [{'x': [7.4, 18.6], 'y': [4.5, 7.5], 'z': 8.0, 'roof': 'shed', 'high': '+y', 'rise': 0.8},                          # 內前廊
                 {'x': [ax - 2.5 * bw, ax + 2.5 * bw], 'y': [0.0, 4.5], 'z': 8.4, 'roof': 'shed', 'high': '+y', 'rise': 0.6, 'domes': [
                     {'cx': bx[0], 'cy': 2.25, 'r': 1.85, 'n': 8, 'z0': 9.0, 'h': 2.0, 'win': 0, 'rise': 1.5, 'ribs': 8},
                     {'cx': bx[2], 'cy': 2.25, 'r': 1.95, 'n': 8, 'z0': 9.0, 'h': 2.3, 'win': 8, 'rise': 1.6, 'ribs': 16},
                     {'cx': bx[4], 'cy': 2.25, 'r': 1.85, 'n': 8, 'z0': 9.0, 'h': 2.0, 'win': 0, 'rise': 1.5, 'ribs': 8}],
                  'arcade_x': [bx[1] - 1.1, bx[1], bx[1] + 1.1, bx[3] - 1.1, bx[3], bx[3] + 1.1], 'arc_z0': 1.3, 'arc_z1': 4.2, 'arc_w': 0.85},   # 外前廊：下層兩組三聯拱
                 {'x': [18.6, 22.0], 'y': [7.5, 18.6], 'z': 6.4, 'roof': 'shed', 'high': '-x', 'rise': 0.8},                          # 南側小禮拜堂（迴廊）
                 {'x': [0.4, 7.4], 'y': [5.0, 17.0], 'z': 8.0, 'roof': 'shed', 'high': '+x', 'rise': 1.0, 'mat': BRICK}],             # 北附屬樓（兩層）
        'door': [{'x': ax, 'w': 1.8, 'h': 3.2}],
    }
    church.cross_in_square(M, P)
    M.add(M.apse(20.3, 18.6 - 0.2, 1.4, 3, 0, 5.6), BANDED, 1)                         # 南側小禮拜堂的半圓後殿
    M.add(M.semidome(20.3, 18.4, 5.6, 1.35, '+y'), TILE, 2)
    for yy in (9.3, 11.9, 14.5, 17.1):                                                  # 南側迴廊的拱
        M.win(M.arch_open(22.0, yy, 1.0, 4.8, 1.6, normal='x', depth=1.6))
    for i in range(5):                                                                  # 外前廊上層：五個拱窗
        M.win(M.arch_open(bx[i], 0.0, 5.3, 7.5, 1.1, normal='y', depth=1.6))
    for yy in (7.5, 10.5, 13.5):                                                        # 北附屬樓兩層的窗
        for z0, z1 in ((1.4, 3.2), (5.2, 7.0)):
            M.win(M.arch_open(0.4, yy + 1.2, z0, z1, 0.8, normal='x', depth=1.6))
    # 西南角鐘樓（方塔、頂層四面拱窗開口、方錐頂）
    tx0, tx1, ty0, ty1 = 22.9, 26.6, 0.3, 4.0
    M.add(M.box(tx0, tx1, ty0, ty1, 0, 16.8), BANDED, 3)
    M.add(M.box(tx0 - 0.2, tx1 + 0.2, ty0 - 0.2, ty1 + 0.2, 16.4, 16.8), STONE, 3)
    M.add(M.hip(tx0 - 0.2, tx1 + 0.2, ty0 - 0.2, ty1 + 0.2, 16.8, 3.0, 1.6), TILE, 3)
    tcx, tcy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    M.air(M.arch_open(tcx, tcy, 13.0, 15.8, 1.6, normal='y', depth=5.0) & M.box(tx0 - 1, tx1 + 1, ty0 - 1, ty1 + 1, 0, 99))
    M.air(M.arch_open(tcx, tcy, 13.0, 15.8, 1.6, normal='x', depth=5.0) & M.box(tx0 - 1, tx1 + 1, ty0 - 1, ty1 + 1, 0, 99))
    M.door(M.arch_open(tcx, ty0, 0, 2.4, 1.0, normal='y', depth=1.2))
    G, L = M.finish(shell_m=0.8, seed=1310)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(ax, 0.2, 0), 'dome-top': M.cell(ax, 13.05, 16.6)}
    return G, L, anchors, {'穹頂頂（m）': 16.6, '鐘樓頂（m）': 19.8}
