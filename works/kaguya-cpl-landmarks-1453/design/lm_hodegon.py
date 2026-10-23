# Hodegon 修道院（Theotokos Hodegetria；聖路加畫的聖像，每週二抬出來遊行）1453：還在用 —— 圍城時聖像移到 Chora、城破時被砍碎。
#   做成：院牆與門樓、主堂（四柱十字型＋穹頂、三個後殿、前廊）、主堂前的石板院子（遊行的出發地）、北邊一排修士房舍、
#   南邊的聖泉井欄（Hodegon 的名字來自帶盲人到聖泉的「嚮導」）、柏樹。
#   ⚠ 尺寸查不到（Demangel–Mamboury 1939 有比例尺的平面沒取得）、位置學界有爭議 ⇒ 平面、大小全是設計決定。
#   研究整理：scratchpad/cpl/research_batch7.md §3。
import random
import byz, church
from byz import BANDED, BRICK, STONE, LEAD, TILE, MARBLE

KEY = 'hodegon'
TITLE = 'Hodegon 修道院 1453（Hodegetria 聖像；主堂、院子、房舍；平面是設計）'
TITLE_SHORT = 'Hodegon 修道院 1453'
MPV = 0.2
W, D, H = 34.0, 40.0, 20.0
META = {'kind': 'building', 'use': 'hodegon', 'style': 'roman', 'lot': '34,40', 'base': 0, 'variant': 'a', 'lamps': 10}
PARTS = (('body', 1, '主體（主堂、房舍、院牆、門樓、井欄）'), ('roof', 2, '屋頂（穹頂、瓦）'), ('ground', 3, '院子（石板、草）'),
         ('trees-cypress', 4, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}))
PROV = {
    'Hodegetria 聖像在這裡；圍城時移到 Chora、城破時被砍碎；修道院到 1453 年還在用': '參考資料：Wikipedia（Monastery of the Hodegon）',
    '名字來自帶盲人到聖泉的「嚮導」': '參考資料：Wikipedia',
    '位置：Demangel–Mamboury 發掘點（有爭議）': '參考資料：Wikipedia（座標）；Grotowski 2017 另有說法',
    '平面、大小、房舍、樹': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.2)
    rnd = random.Random(1453)
    B, R, G1 = 1, 2, 3
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    M.add(M.box(8.0, 26.0, 2.5, 15.0, 0, MPV), STONE, G1)                     # 遊行出發的石板院子
    x0, x1 = 9.5, 24.5
    P = {
        'naos': {'x': [x0, x1], 'y': [19.0, 32.0], 'z': 8.0, 'arm_w': 5.0, 'arm_z': 10.2, 'roof': 'gable', 'rise': 1.4},
        'domes': [{'cx': 17.0, 'cy': 25.5, 'r': 3.2, 'n': 12, 'z0': 10.4, 'h': 2.2, 'win': 12, 'rise': 2.6, 'ribs': 12, 'cross': True}],
        'apses': [{'cx': 17.0, 'r': 2.4, 'facets': 5, 'z': 7.4, 'win': 3, 'win_w': 0.6}, {'cx': 12.0, 'r': 1.2, 'facets': 3, 'z': 5.8},
                  {'cx': 22.0, 'r': 1.2, 'facets': 3, 'z': 5.8}],
        'bays': [{'x': [x0, x1], 'y': [15.5, 19.0], 'z': 6.4, 'roof': 'shed', 'high': '+y', 'rise': 0.9,
                  'arcade_x': [12.0, 22.0], 'arc_z0': 0.8, 'arc_z1': 4.4, 'arc_w': 1.8}],
        'door': [{'x': 17.0, 'w': 1.8, 'h': 3.2, 'y': 15.5}],
    }
    church.cross_in_square(M, P, body=B, roof=R)
    # 北邊一排房舍（兩層、瓦頂）
    M.add(M.box(0.6, 6.0, 4.0, 38.0, 0, 6.2), BANDED, B)
    M.add(M.gable(0.6, 6.0, 4.0, 38.0, 6.2, 1.4, 'y'), TILE, R)
    for yy in range(6, 38, 4):
        M.win(M.arch_open(6.0, yy, 1.0, 2.4, 0.8, normal='x', depth=1.2))
        M.win(M.arch_open(6.0, yy, 3.8, 5.2, 0.8, normal='x', depth=1.2))
    # 院牆＋西面門樓
    for a in ((0, W, 0, 0.8), (0, W, D - 0.8, D), (0, 0.8, 0, D), (W - 0.8, W, 0, D)):
        M.add(M.box(a[0], a[1], a[2], a[3], 0, 3.6), BANDED, B)
    M.add(M.box(14.0, 20.0, 0, 3.0, 0, 6.6), BANDED, B)
    M.add(M.gable(14.0, 20.0, 0, 3.0, 6.6, 1.2, 'x'), TILE, R)
    M.door(M.arch_open(17.0, 0.0, 0, 3.4, 2.4, normal='y', depth=3.2))
    # 南邊院子的聖泉井欄
    M.add(M.cyl(29.0, 22.0, 1.1, 0, 1.0) & ~M.cyl(29.0, 22.0, 0.7, -1, 99), MARBLE, B)
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    for (x, y) in ((29.0, 6.0), (29.0, 12.0), (29.0, 33.0), (10.0, 36.5)):
        M.tree(x, y, 10.5, 2.4, 4)
    M.DOORS = [d & M.full(M.Z >= MPV) for d in M.DOORS]                 # 門洞外那一格 finish 會整個挖掉 ⇒ 地面那一層（草）不算進門
    G, L = M.finish(shell_m=0.8, seed=1261, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(17.0, 0.4, 0.0), 'dome-top': M.cell(17.0, 25.5, 15.2)}
    return G, L, anchors, {'穹頂頂（m）': round(10.4 + 2.2 + 2.6, 2)}
