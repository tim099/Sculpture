# 生命之泉修道院（Zoodochos Pege，Balıklı；Leo I／Justinian 起建、Basil I 重建）1453：陸牆外、Pege 門（Silivri 門）前 ——
#   1422 年 Murad II 圍城時在此紮營、教堂受重創；1453 年前修沒修好不知道 ⇒ 做成半毀：十字型主堂的穹頂塌了一半、北臂的屋頂沒了、
#   西邊前廊還在；南邊院子裡往下通到聖泉的小穹頂亭（還有人來取水）、一圈斷了幾段的院牆、柏樹與梧桐。
#   ⚠ 平面照今日 1833–35 年的教堂（蓋在古地基上；OSM way 559461214 32.1 × 21.0 m）推、其餘是設計決定。
#   ⛔ 不做：1833–35 年的教堂、鐘樓、墓園。
#   研究整理：scratchpad/cpl/research_batch7.md §2。
import random
import byz, church, ruins
from byz import BANDED, BRICK, STONE, LEAD, TILE, MARBLE

KEY = 'pege'
TITLE = '生命之泉修道院 1453（Zoodochos Pege；半毀的主堂、聖泉亭、院牆）'
TITLE_SHORT = '生命之泉修道院 1453'
MPV = 0.2
W, D, H = 34.0, 44.0, 22.0
META = {'kind': 'building', 'use': 'pege', 'style': 'roman', 'lot': '34,44', 'base': 0, 'variant': 'a', 'lamps': 4}
PARTS = (('body', 1, '主體（主堂殘體、前廊、聖泉亭、院牆）'), ('roof', 2, '屋頂（殘存的穹頂、瓦）'), ('ground', 3, '院子（草、碎石）'),
         ('trees-cypress', 4, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}),
         ('trees-plane', 5, '梧桐（遊戲換成生成式的梧桐）', {'kind': 'tree', 'tree': 'plane'}))
PROV = {
    '陸牆外的聖泉修道院；1422 年 Murad II 在此紮營、教堂受重創': '參考資料：Wikipedia（Church of St. Mary of the Spring）',
    '1453 年前有沒有修復不知道；之後拆除，Gyllius 時已不存': '參考資料：Wikipedia',
    '主堂 32 × 21 m（今日教堂在古地基上）': '參考資料：OSM way 559461214（量）',
    '半毀的程度、聖泉亭、院牆、樹': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.2)
    rnd = random.Random(1422)
    B, R, G1 = 1, 2, 3
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    x0, x1 = 6.5, 27.5
    P = {
        'naos': {'x': [x0, x1], 'y': [12.0, 34.0], 'z': 10.0, 'arm_w': 7.0, 'arm_z': 13.0, 'roof': 'gable', 'rise': 1.8},
        'domes': [{'cx': 17.0, 'cy': 23.0, 'r': 4.4, 'n': 12, 'z0': 13.2, 'h': 2.4, 'win': 12, 'rise': 3.4, 'ribs': 12}],
        'apses': [{'cx': 17.0, 'r': 3.2, 'facets': 5, 'z': 9.0, 'win': 3, 'win_w': 0.8}, {'cx': 10.5, 'r': 1.5, 'facets': 3, 'z': 7.0},
                  {'cx': 23.5, 'r': 1.5, 'facets': 3, 'z': 7.0}],
        'bays': [{'x': [x0, x1], 'y': [8.0, 12.0], 'z': 8.0, 'roof': 'shed', 'high': '+y', 'rise': 1.0,
                  'arcade_x': [10.0, 24.0], 'arc_z0': 1.0, 'arc_z1': 5.4, 'arc_w': 2.0}],
        'door': [{'x': 17.0, 'w': 2.0, 'h': 3.6, 'y': 8.0}],
    }
    church.cross_in_square(M, P, body=B, roof=R)
    # 半毀：穹頂北半塌了、北臂（x 小的那一邊）屋頂沒了、牆頂咬掉
    M.air(M.box(0, 17.0, 17.0, 29.0, 13.0, 99))
    M.air(M.box(x0 - 0.5, 13.5, 19.5, 26.5, 9.0, 99))
    for k in range(6):
        a = rnd.uniform(x0, x1 - 3.0)
        M.air(M.box(a, a + rnd.uniform(2, 4), 11.5, 34.5, rnd.uniform(7.0, 10.5), 99) & M.full(M.Z < 13.0))
    ruins.rubble(M, rnd, 8.5, 16.5, 18.0, 28.0, 10, G1, 0.6, 1.6)
    # 聖泉亭（南邊院子：方 4 × 4、小穹頂、往下的門洞）
    M.add(M.box(26.0, 31.0, 5.0, 10.0, 0, 3.6), BANDED, B)
    M.add(M.dome(28.5, 7.5, 3.6, 2.2, 1.6), LEAD, R)
    M.door(M.arch_open(26.0, 7.5, 0, 2.4, 1.2, normal='x', depth=1.4))
    # 院牆（厚 0.8、高 3.2；斷了幾段）＋西面的門
    for a in ((0, W, 0, 0.8), (0, W, D - 0.8, D), (0, 0.8, 0, D), (W - 0.8, W, 0, D)):
        ruins.wall(M, a[0], a[1], a[2], a[3], 3.2, rnd, B, bite=0.5, step=4.0)
    M.air(M.box(15.0, 19.0, -0.1, 1.0, MPV, 99))
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    # 樹：前院的柏樹、後面的梧桐
    for (x, y) in ((4.0, 6.0), (4.0, 14.0), (4.0, 26.0), (30.0, 18.0), (30.0, 28.0)):
        M.tree(x, y, 11.0, 2.4, 4)
    for (x, y) in ((8.0, 40.0), (27.0, 40.0)):
        M.tree(x, y, 9.0, 5.0, 5)
    M.DOORS = [d & M.full(M.Z >= MPV) for d in M.DOORS]                 # 門洞外那一格 finish 會整個挖掉 ⇒ 地面那一層（草）不算進門
    G, L = M.finish(shell_m=0.8, seed=1422, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(17.0, 0.4, 0.0)}
    return G, L, anchors, {'殘存穹頂頂（m）': round(13.2 + 2.4 + 3.4, 2)}
