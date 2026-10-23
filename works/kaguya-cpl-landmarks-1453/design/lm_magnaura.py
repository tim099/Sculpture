# 馬格瑙拉廢墟（OSM「Magnaura Sarayı」，大皇宮東側）1453：今天立在那裡的是一組兩層的拱頂下部結構＋一座坡道塔（WP 用「Büyük Saray Merdiven Kulesi」的照片當 Magnaura 的殘部）——
#   鑑定不確定；1453 年大皇宮已廢 ⇒ 做成：一樓三道並排的筒形拱（拱口朝正面、一道塌了一半）、二樓的牆只剩下半截與窗洞、東北角一座方的坡道塔（上半截斷了）、地上長草與碎石。
#   ⚠ 高度、拱數、塔的位置都是設計決定；框 23 × 28 m、軸 45° 照 OSM way 530509322。
#   ⛔ 不做：Magnaura 大廳本身（位置、尺寸、1453 年的狀態都查不到）、19 世紀以後的建築。
#   研究整理：scratchpad/cpl/research_batch3.md §4（b4、d）。
import random
import byz, ruins
from byz import BANDED, STONE, BRICK, MARBLE

KEY = 'magnaura'
TITLE = '馬格瑙拉廢墟 1453（大皇宮的拱頂下部結構、坡道塔）'
TITLE_SHORT = '馬格瑙拉廢墟 1453'
MPV = 0.2
W, D, H = 23.0, 28.0, 14.0
META = {'kind': 'building', 'use': 'magnaura', 'style': 'roman', 'lot': '23,28', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('body', 1, '下部結構（筒形拱、二樓殘牆、坡道塔）'), ('ground', 2, '地面（草、碎石）'))
PROV = {
    'OSM「Magnaura Sarayı」廢墟 23 × 28 m、軸 45°': '參考資料：OSM way 530509322、node 1652694014',
    '鑑定不確定（可能是大皇宮的坡道塔、拱頂下部結構）': '參考資料：Wikipedia（Magnaura；推估）',
    '拱數、高度、塔、殘存程度': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.4)
    M.band_z0 = 0.0
    rnd = random.Random(1453)
    B, G1 = 1, 2
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    # 一樓：三道並排的筒形拱（沿 y、跨 5 m、墩 1.4 m），拱頂 6.4 m；正面（y 0）的拱口開著
    x0, x1, y0, y1 = 1.0, 22.0, 1.0, 20.0
    M.add(M.box(x0, x1, y0, y1, 0, 7.6), BANDED, B)
    for k in range(3):
        bx = x0 + 1.4 + k * 6.4
        M.air(M.barrel(bx, bx + 5.0, y0 - 1, y1 - 1.4, 4.2, 'y', 2.5) | M.box(bx, bx + 5.0, y0 - 1, y1 - 1.4, 0, 4.2))
    M.air(M.box(x0 + 7.4, x0 + 13.8, y0 - 1, y0 + 7.0, 4.0 + rnd.random(), 99))      # 中間那道的前段塌了
    # 二樓：只剩下半截的牆、窗洞
    ruins.shell(M, x0, x1, y0, y1, 12.0, 1.4, rnd, B, bite=0.45, floor=None)
    M.air(M.box(x0 + 1.4, x1 - 1.4, y0 + 1.4, y1 - 1.4, 7.6, 99))
    for k in range(4):
        M.air(M.arch_open(x0 + 3.0 + k * 5.0, y0, 8.4, 10.6, 1.4, normal='y', depth=2.0))
    # 坡道塔（東北角，方 6 m，上半截斷了）
    tx0, ty0 = 15.0, 20.0
    M.add(M.box(tx0, tx0 + 6.0, ty0, ty0 + 6.0, 0, 13.4), BANDED, B)
    M.air(M.box(tx0 + 1.2, tx0 + 4.8, ty0 + 1.2, ty0 + 4.8, 0.4, 99))
    M.air(M.box(tx0 - 1, tx0 + 3.0, ty0 - 1, ty0 + 7, 10.2, 99))
    M.air(M.box(tx0 + 3.0, tx0 + 7, ty0 + 3.0, ty0 + 7, 11.8, 99))
    for z in (2.0, 6.0, 9.6):
        M.air(M.arch_open(tx0 + 3.0, ty0 + 6.0, z, z + 1.6, 0.8, normal='y', depth=1.6))
    M.air(M.arch_open(tx0 + 3.0, ty0, 0, 2.6, 1.4, normal='y', depth=2.0))
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    ruins.rubble(M, rnd, 0.5, 14.0, 20.5, 27.5, 9, G1, 0.4, 1.1)
    ruins.rubble(M, rnd, 7.0, 15.0, 0.2, 6.0, 5, G1, 0.4, 1.0)
    G, L = M.finish(shell_m=0.8, seed=1453, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'塔頂（m）': 13.4, '一樓拱頂（m）': 6.7}
