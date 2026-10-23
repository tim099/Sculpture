# 元老院（君士坦丁廣場北側的那一座；門廊是斑岩柱）1453：464／465 年燒過；帕列奧略時代城中心多成廢墟（Buondelmonti、Clavijo）——
#   做成：朝廣場的門廊（四根斑岩柱：兩根還立著、一根斷了、一根倒在台階上；柱頂盤掉光）、後面的大廳只剩斷牆（屋頂塌了、裡面碎石、長了兩棵野樹）、
#   後殿的半圈殘牆。跟奧古斯都廣場東邊那一座（lm_senate.py，六根白大理石柱）分開：這一座小一點、柱是斑岩。
#   ⚠ 平面、大小、高度、殘存程度都是設計決定 —— 只知道「廣場北側、正對南側的噴泉、門廊是斑岩柱、464／465 年燒過」。
#   ⛔ 不做：1453 年後的建築（Çemberlitaş 一帶的商館、浴場）。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, BRICK, PORPHYRY

KEY = 'senate-forum'
TITLE = '元老院 1453（君士坦丁廣場北側；斑岩柱門廊、廢墟）'
TITLE_SHORT = '廣場的元老院 1453'
MPV = 0.2
W, D, H = 40.0, 30.0, 16.0
META = {'kind': 'building', 'use': 'senate-forum', 'style': 'roman', 'lot': '40,30', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('body', 1, '大廳與後殿的殘牆'), ('portico', 2, '門廊（斑岩柱、柱礎、倒下的柱段、台階）'), ('ground', 3, '地面（草、碎石）'),
         ('trees', 4, '野樹（遊戲換成生成式的樹）', {'kind': 'tree', 'tree': 'broadleaf'}))
PROV = {
    '君士坦丁廣場北側是元老院、門廊是斑岩柱，正對南側的噴泉': '參考資料：Wikipedia（Forum of Constantine）、The Byzantine Legacy（Forum of Constantine）',
    '464／465 年 Leo I 時的大火燒壞': '參考資料：Wikipedia（Forum of Constantine）',
    '平面、大小、高度、幾根柱還立著、後殿、野樹': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.4)
    M.band_z0 = 0.0
    rnd = random.Random(465)
    B, P, G1, T = 1, 2, 3, 4
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    # 門廊：三級台階（大理石，缺角）、四根斑岩柱（x 11…29、直徑 1.2 m、高 10 m）
    for k in range(3):
        M.add(M.box(4.0 + k * 0.5, W - 4.0 - k * 0.5, 0.6 + k * 0.5, 8.0, 0, 0.4 * (k + 1)), MARBLE, P)
    M.air(M.box(4.0, 9.0, 0, 3.0, MPV, 99))
    M.air(M.box(W - 7.5, W - 4.0, 0, 2.2, 0.4, 99))
    zc = 1.2
    hs = (10.0, 2.6, 10.0, 0.0)
    for k, h in enumerate(hs):
        x = 11.0 + k * 6.0
        M.add(M.box(x - 0.9, x + 0.9, 3.1, 4.9, zc, zc + 0.5), MARBLE, P)                    # 柱礎
        if h > 0:
            M.add(M.cyl(x, 4.0, 0.6, zc + 0.5, zc + h), PORPHYRY, P)
        if h >= 10.0:
            M.add(M.box(x - 0.85, x + 0.85, 3.15, 4.85, zc + h, zc + h + 1.0), MARBLE, P)    # 柱頭
    ruins.fallen(M, 30.5, 1.0, 0.6, 7.0, P, mat=PORPHYRY)                                     # 最東那一根倒在台階前
    # 大廳（y 8～26）：斷牆、正面一道大門（門楣塌了）、兩側高窗只剩洞
    ruins.shell(M, 3.0, W - 3.0, 8.0, 26.0, 12.0, 1.6, rnd, B, bite=0.65, step=6.0)     # 段長 6 m：2.4 m 一段咬出來像雉堞
    M.air(M.arch_open(W / 2, 8.0, zc, zc + 6.0, 4.0, normal='y', depth=2.4))
    for y in (13.0, 19.0):
        for x in (3.0, W - 3.0):
            M.air(M.arch_open(x, y, 6.5, 9.8, 1.8, normal='x', depth=2.4))
    # 後殿（朝 +y）：半圈殘牆，頂往下咬
    M.add(M.apse(W / 2, 26.0, 5.6, 7, 0, 9.0, '+y') & ~M.apse(W / 2, 25.0, 4.2, 7, -1, 99, '+y'), BANDED, B)
    M.air(M.box(W / 2 - 3.0, W / 2 + 1.5, 26.0, D, 4.0 + rnd.random() * 2.0, 99))
    M.MAT[M.S & M.full(M.Z < 1.6) & (M.MAT == BANDED)] = STONE
    ruins.rubble(M, rnd, 6.0, W - 6.0, 10.5, 24.0, 18, G1, 0.6, 1.8)
    ruins.fallen(M, 8.0, 15.0, 0.45, 4.2, G1)
    # 大廳裡長了兩棵野樹（離牆 ≥ 2 m）
    M.tree(13.0, 20.0, 7.5, 4.2, T)
    M.tree(27.5, 14.5, 6.0, 3.6, T)
    G, L = M.finish(shell_m=0.8, seed=465, mix=True)
    anchors = {'lot-0': [0, 0, 0]}
    return G, L, anchors, {'柱頭頂（m）': round(zc + 10.0 + 1.0, 2), '大廳牆頂（m）': 12.0}
