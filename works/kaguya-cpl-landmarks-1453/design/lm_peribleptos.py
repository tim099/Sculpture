# Peribleptos 聖母修道院（Theotokos Peribleptos，Sulu Manastır；約 1030–34 年 Romanos III Argyros 創建、葬在這裡）1453：完整、還在用的大修道院 ——
#   Clavijo 1402/03 親見：上層教堂「方形、帶高聳的半圓後殿」、5 座祭壇、碧玉柱與牆面、外面畫著金色藍色的人物與圖案。
#   做成：院牆一圈（西面門樓）、主堂（四柱十字型＋大穹頂、高的半圓主後殿、兩側小後殿、前廊；坐在下部結構上 ⇒ 地面那一層拱窗）、
#   北邊一排修士房舍（瓦頂）、前院東邊的柏樹、主堂後面的果樹、前院的蓄水池口。
#   ⚠ 原教堂 1782 年燒掉：位置、朝向、全長全寬、穹頂都查不到 ⇒ 全部是設計決定；只有 naos 下部約 10.2 × 10.3 m（四墩）是調查的數字。
#   ⛔ 不做：1887 年的亞美尼亞 Surp Kevork 教堂與它的院子。
#   研究整理：scratchpad/cpl/research_batch6.md §2。
import random
import byz, church, ruins
from byz import BANDED, BRICK, STONE, LEAD, TILE, MARBLE

KEY = 'peribleptos'
TITLE = 'Peribleptos 聖母修道院 1453（主堂、院牆、房舍；位置與大小是設計）'
TITLE_SHORT = 'Peribleptos 修道院 1453'
MPV = 0.2
W, D, H = 34.0, 46.0, 22.0
META = {'kind': 'building', 'use': 'peribleptos', 'style': 'roman', 'lot': '34,46', 'base': 0, 'variant': 'a', 'lamps': 10}
PARTS = (('body', 1, '主體（主堂、房舍、院牆、門樓）'), ('roof', 2, '屋頂（穹頂、瓦）'), ('ground', 3, '院子（石板、草）'),
         ('trees-cypress', 4, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}),
         ('trees-fruit', 5, '果樹（遊戲換成生成式的果樹）', {'kind': 'tree', 'tree': 'fruit'}))
PROV = {
    'Romanos III Argyros 約 1030–34 年創建、葬在這裡；1453 年還在用': '參考資料：The Byzantine Legacy（Theotokos Peribleptos）',
    '上層教堂方形、高的半圓後殿、5 座祭壇、碧玉柱、外牆畫金藍色人物': '參考資料：Clavijo 1403（Markham 1859 英譯）經 The Byzantine Legacy',
    'naos 下部 10.2 × 10.3 m、四墩；西端三分的前廊下部': '參考資料：Özgümüş 1997–98 調查（經 The Byzantine Legacy）',
    '位置、朝向、主堂與院子的大小、房舍、樹': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.2)
    rnd = random.Random(1032)
    B, R, G1 = 1, 2, 3
    # 院子：石板（主堂前）＋草
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    M.add(M.box(9.0, 25.0, 3.0, 14.0, 0, MPV), STONE, G1)
    M.add(M.box(15.4, 18.6, 0.0, 3.0, 0, MPV), STONE, G1)
    # 主堂：下部結構高 2.4（地面一層拱窗）上蓋十字型；naos 14 × 14、穹頂 r 4.2；高的半圓主後殿
    up = 2.4
    x0, x1 = 10.0, 24.0
    P = {
        'naos': {'x': [x0, x1], 'y': [18.0, 32.0], 'z': up + 9.0, 'arm_w': 5.6, 'arm_z': up + 11.4, 'roof': 'gable', 'rise': 1.4},
        'domes': [{'cx': 17.0, 'cy': 25.0, 'r': 3.8, 'n': 12, 'z0': up + 11.6, 'h': 2.6, 'win': 12, 'rise': 3.2, 'ribs': 12, 'cross': True}],
        'apses': [{'cx': 17.0, 'r': 3.2, 'facets': 12, 'z': up + 9.6, 'win': 3, 'win_w': 0.8}, {'cx': 12.2, 'r': 1.4, 'facets': 8, 'z': up + 6.4},
                  {'cx': 21.8, 'r': 1.4, 'facets': 8, 'z': up + 6.4}],
        'bays': [{'x': [x0, x1], 'y': [14.0, 18.0], 'z': up + 7.0, 'roof': 'shed', 'high': '+y', 'rise': 1.0,
                  'arcade_x': [12.4, 21.6], 'arc_z0': up + 0.8, 'arc_z1': up + 4.6, 'arc_w': 1.8}],
    }
    church.cross_in_square(M, P, body=B, roof=R)
    M.add(M.box(x0, x1, 14.0, 32.0, 0, up), BRICK, B)
    for xx in (x0, x1):
        for yy in (20.0, 25.0, 30.0):
            M.win(M.arch_open(xx, yy, 0.4, 1.9, 1.2, normal='x', depth=1.6))
    # 前面的台階（上到前廊）＋門
    for k in range(6):
        M.add(M.box(15.0, 19.0, 14.0 - 2.4 + k * 0.4, 14.0, 0, 0.4 * (k + 1)), MARBLE, B)
    M.door(M.arch_open(17.0, 14.0, up, up + 3.2, 1.8, normal='y', depth=1.2))
    # 北邊一排房舍（兩層、瓦頂）
    M.add(M.box(0.6, 6.6, 4.0, 44.0, 0, 6.4), BANDED, B)
    M.add(M.gable(0.6, 6.6, 4.0, 44.0, 6.4, 1.6, 'y'), TILE, R)
    for yy in range(7, 44, 4):
        M.win(M.arch_open(6.6, yy + 0.0, 1.0, 2.4, 0.8, normal='x', depth=1.2))
        M.win(M.arch_open(6.6, yy + 0.0, 3.8, 5.2, 0.8, normal='x', depth=1.2))
    for yy in (10.0, 22.0, 34.0):
        M.door(M.arch_open(6.6, yy + 2.0, 0, 2.2, 1.0, normal='x', depth=1.2))
    # 院牆（厚 0.8、高 4）＋西面門樓
    for a in ((0, W, 0, 0.8), (0, W, D - 0.8, D), (0, 0.8, 0, D), (W - 0.8, W, 0, D)):
        M.add(M.box(a[0], a[1], a[2], a[3], 0, 4.0), BANDED, B)
    M.add(M.box(14.0, 20.0, 0, 3.0, 0, 7.0), BANDED, B)
    M.add(M.gable(14.0, 20.0, 0, 3.0, 7.0, 1.2, 'x'), TILE, R)
    M.door(M.arch_open(17.0, 0.0, 0, 3.4, 2.4, normal='y', depth=3.2))
    # 前院的蓄水池口（井欄）
    M.add(M.cyl(22.5, 8.0, 1.1, 0, 1.0) & ~M.cyl(22.5, 8.0, 0.7, -1, 99), MARBLE, B)
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    # 樹：前院東邊的柏樹、主堂後面的果樹（離牆、房舍 ≥ 2 m）
    for (x, y) in ((27.0, 5.0), (27.0, 11.0), (30.5, 8.0)):
        M.tree(x, y, 11.0, 2.4, 4)
    for x in (11.0, 24.0, 28.0):
        M.tree(x + rnd.uniform(-0.4, 0.4), 41.0 + rnd.uniform(-0.4, 0.4), rnd.uniform(4.0, 5.0), 3.0, 5)
    M.DOORS = [d & M.full(M.Z >= MPV) for d in M.DOORS]                 # 門洞外那一格 finish 會整個挖掉 ⇒ 地面那一層（草）不算進門
    G, L = M.finish(shell_m=0.8, seed=1032, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(17.0, 0.4, 0.0), 'dome-top': M.cell(17.0, 25.0, up + 11.6 + 2.6 + 3.2)}
    return G, L, anchors, {'穹頂頂（m）': round(up + 11.6 + 2.6 + 3.2, 2)}
