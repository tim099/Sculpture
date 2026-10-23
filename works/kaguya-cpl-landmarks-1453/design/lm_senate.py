# 元老院（奧古斯都廣場東邊；Justinian 重建，門廊 6 根大柱）1453：大皇宮與奧古斯都廣場一帶 15 世紀初已成廢墟（Buondelmonti）——
#   做成：朝廣場的門廊（六根柱：四根還立著、兩根斷了、一段倒在地上；柱頂盤掉光）、後面的大廳只剩斷牆與窗洞（屋頂塌了、裡面碎石與草）、後殿的殘牆。
#   ⚠ 平面、大小、高度、殘存程度都是設計決定 —— 只知道「東邊、Justinian 重建、門廊 6 根大柱」。
#   ⛔ 不做：君士坦丁廣場北側的那一座元老院（另一座，在圓外）、1453 年後的建築。
#   研究整理：scratchpad/cpl/research_batch3.md §3（WP Augustaeum 引 Procopius Aed. I.10）、§1.4（另一座的形制當參考）。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK

KEY = 'senate'
TITLE = '元老院 1453（奧古斯都廣場東邊；六柱門廊、廢墟）'
TITLE_SHORT = '元老院 1453'
MPV = 0.2
W, D, H = 35.0, 34.0, 16.0
META = {'kind': 'building', 'use': 'senate', 'style': 'roman', 'lot': '35,34', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('body', 1, '大廳與後殿的殘牆'), ('portico', 2, '門廊（柱、柱礎、倒下的柱段、台階）'), ('ground', 3, '地面（草、碎石）'))
PROV = {
    '奧古斯都廣場東邊是元老院；Justinian 重建，門廊 6 根大柱': '參考資料：Wikipedia（Augustaeum，引 Procopius Aed. I.10）',
    '15 世紀初廣場一帶已成廢墟': '參考資料：Buondelmonti（經 Wikipedia 引 Katsaveli）',
    '平面、大小、高度、哪幾根柱還立著、後殿': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.4)
    M.band_z0 = 0.0
    rnd = random.Random(532)
    B, P, G1 = 1, 2, 3
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    # 門廊：三級台階（大理石）、六根柱（x 5…30、直徑 1.4 m、高 11 m）
    for k in range(3):
        M.add(M.box(1.0 + k * 0.5, W - 1.0 - k * 0.5, 0.6 + k * 0.5, 8.0, 0, 0.4 * (k + 1)), MARBLE, P)
    zc = 1.2
    hs = (11.0, 11.0, 3.4, 11.0, 1.6, 11.0)
    for k, h in enumerate(hs):
        x = 5.0 + k * 5.0
        M.add(M.box(x - 1.0, x + 1.0, 3.0, 5.0, zc, zc + 0.6), MARBLE, P)                    # 柱礎
        M.add(M.cyl(x, 4.0, 0.7, zc + 0.6, zc + h), MARBLE, P)
        if h >= 11.0:
            M.add(M.box(x - 0.95, x + 0.95, 3.05, 4.95, zc + h, zc + h + 1.2), MARBLE, P)    # 柱頭
    ruins.fallen(M, 13.0, 11.4, 0.7, 6.2, P)                                                # 斷了的那根倒進大廳裡
    # 大廳（y 8～30）：斷牆、正面三道門、兩側的窗洞；屋頂塌了
    ruins.shell(M, 1.5, W - 1.5, 8.0, 30.0, 13.0, 1.8, rnd, B, bite=0.45)
    for x in (10.0, 17.5, 25.0):
        M.air(M.arch_open(x, 8.0, zc, zc + 5.0 if x == 17.5 else zc + 4.0, 3.2 if x == 17.5 else 2.4, normal='y', depth=2.6))
    for y in (12.0, 17.0, 22.0, 27.0):
        for x in (1.5, W - 1.5):
            M.air(M.arch_open(x, y, 6.0, 9.6, 1.8, normal='x', depth=2.6))
    # 後殿（朝 +y）
    M.add(M.apse(W / 2, 30.0, 6.0, 7, 0, 10.0, '+y') & ~M.apse(W / 2, 29.0, 4.6, 7, -1, 99, '+y'), BANDED, B)
    M.air(M.box(W / 2 - 2.0, W / 2 + 4.0, 30.0, D, 6.0 + rnd.random() * 2.0, 99))
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    ruins.rubble(M, rnd, 4.0, W - 4.0, 10.5, 28.0, 16, G1, 0.6, 1.6)
    ruins.fallen(M, 6.0, 20.0, 0.45, 4.0, G1)
    G, L = M.finish(shell_m=0.8, seed=532, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'柱頭頂（m）': round(zc + 11.0 + 1.2, 2), '大廳牆頂（m）': 13.0}
