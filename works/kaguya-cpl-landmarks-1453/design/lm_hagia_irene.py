# 聖伊琳娜教堂（Hagia Irene）1453：查士丁尼 532 後重建、740 年地震後 Constantine V 再修 —— 三廊式穹頂巴西利卡、主穹頂（20 窗鼓座）＋西跨低扁的橢圓穹窿、西邊前廊與中庭。
#   1453 年後劃進 Topkapı 外牆當軍械庫、從沒改成清真寺 ⇒ 沒有宣禮塔要拿。⛔ 不做：中庭內圈拱廊大多是土耳其時代重建（做成單圈）、前廊樓座中間 3 個拱頂、鄂圖曼新開的主入口。
#   研究整理：scratchpad/cpl/research_columns_churches.md §B1；占地：OSM relation 4742554（102.7 × 48.4 m 含中庭、長軸方位 130.75°）。
import byz, church
import numpy as np
from byz import BANDED, STONE, LEAD, TILE, MARBLE

KEY = 'hagia-irene'
TITLE = '聖伊琳娜教堂 1453（Hagia Irene，532 後重建、740 後再修）'
TITLE_SHORT = '聖伊琳娜教堂 1453'
MPV = 0.4
W, D, H = 48.0, 103.0, 37.0
META = {'kind': 'building', 'use': 'hagia-irene', 'style': 'roman', 'lot': '48,103', 'base': 0, 'variant': 'a'}
PARTS = (('body', 1, '主體（中殿、側廊、前廊、後殿）'), ('roof', 2, '屋頂（主穹頂、西跨穹窿、坡頂）'), ('atrium', 3, '中庭（單圈柱廊）'))
PROV = {
    '本體約 57 × 32 m（不含中庭）；連中庭約 103 m': '參考資料：TBL；OSM relation 4742554',
    '主穹頂直徑 15–16 m、頂高 35 m、鼓座 20 扇半圓頭窗；鼓座平面圓角方形、窗台起才正圓': '參考資料：Wikipedia；TBL；van Millingen 1912',
    '西跨：低矮的橢圓穹窿，外觀只是屋面上一圈低圓筒（740 後加）': '參考資料：van Millingen 1912；TBL',
    '後殿內半圓、外 3 面、三扇大圓拱窗；東牆扶壁（早於土耳其時代）': '參考資料：van Millingen 1912；de.Wikipedia',
    '牆：側廊拱頂起拱線以下大塊方整石；以上 5 皮磚對 5 皮石': '參考資料：van Millingen 1912（實測）',
    '北、西、南三面坡屋頂；穹頂鋪鉛、坡頂鋪瓦': '參考資料：Wikipedia（坡頂）；材料是設計決定',
    '中庭單圈拱廊': '設計決定（vM：只有南北兩廊的外牆、部分內牆、西廊北端 3 個拱跨是拜占庭原物）',
    '各量體的牆高': '設計決定（照頂高 35 m 倒推）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 1.0)
    M.band_z0 = 9.0
    xa, xb = 8.0, 40.0                           # 本體南北牆（寬 32 m）
    yn, yb0, yb1 = 40.0, 46.0, 97.0              # 前廊西牆、本體西牆、東牆
    # 中庭（單圈拱廊）
    A = 3
    for (x0, x1, y0, y1) in ((xa, xb, 0.0, 1.2), (xa, xa + 1.2, 0.0, yn), (xb - 1.2, xb, 0.0, yn)):
        M.add(M.box(x0, x1, y0, y1, 0, 8.0), BANDED, A)
    for (x0, x1, y0, y1, hi) in ((xa + 1.2, xb - 1.2, 1.2, 6.5, '-y'), (xa + 1.2, xa + 6.5, 1.2, yn, '-x'), (xb - 6.5, xb - 1.2, 1.2, yn, '+x')):
        M.add(M.shed(x0, x1, y0, y1, 6.4, 7.8, hi), TILE, A)
    for xx in np.arange(xa + 9.0, xb - 7.0, 3.6):
        M.add(M.box(xx - 0.4, xx + 0.4, 6.0, 6.8, 0, 6.4), MARBLE, A)
    for yy in np.arange(9.0, yn - 1.0, 3.6):
        M.add(M.box(xa + 6.0, xa + 6.8, yy - 0.4, yy + 0.4, 0, 6.4), MARBLE, A)
        M.add(M.box(xb - 6.8, xb - 6.0, yy - 0.4, yy + 0.4, 0, 6.4), MARBLE, A)
    M.door(M.arch_open(24.0, 0.0, 0, 4.0, 3.0, normal='y', depth=3.0))
    M.air(M.arch_open(24.0, 0.6, 0, 4.0, 3.0, normal='y', depth=1.4))
    # 前廊（兩層）、本體：側廊（樓座）、中殿、方形穹頂基座、後殿
    M.add(M.box(xa, xb, yn, yb0, 0, 13.0), BANDED, 1)
    M.add(M.shed(xa, xb, yn, yb0, 13.0, 14.8, '+y'), TILE, 2)
    M.add(M.box(xa, xb, yb0, yb1, 0, 15.0), BANDED, 1)                                  # 側廊＋樓座
    M.add(M.shed(xa, 14.0, yb0, yb1, 15.0, 18.0, '+x'), TILE, 2)
    M.add(M.shed(34.0, xb, yb0, yb1, 15.0, 18.0, '-x'), TILE, 2)
    M.add(M.box(14.0, 34.0, yb0, yb1, 0, 19.0), BANDED, 1)                              # 中殿
    M.add(M.gable(14.0, 34.0, yb0, yb1, 19.0, 3.0, 'y'), TILE, 2)
    yc = 70.0                                                                         # 主穹頂中心
    M.add(M.box(13.0, 35.0, yc - 11.0, yc + 11.0, 0, 22.5), BANDED, 1)                  # 方形基座（穹頂四角的墩）
    M.add(M.box(13.0, 35.0, yc - 11.0, yc + 11.0, 22.5, 23.3), LEAD, 2)
    M.add(M.cyl(24.0, yc, 9.0, 23.0, 28.0), BANDED, 1)                                  # 鼓座（窗台起正圓）
    M.add(M.dome(24.0, yc, 28.0, 8.6, 6.9, ribs=20), LEAD, 2)
    M.win(M.ring_windows(24.0, yc, 7.6, 9.6, 23.8, 27.4, [9.0 + 18.0 * k for k in range(20)], 0.7))
    M.add(M.box(23.8, 24.2, yc - 0.2, yc + 0.2, 34.6, 36.8), byz.GOLD, 2)
    M.add(M.box(23.8, 24.2, yc - 0.8, yc + 0.8, 35.8, 36.2), byz.GOLD, 2)
    ycw = 52.0                                                                        # 西跨的低扁穹窿（屋面上一圈低圓筒）
    M.add(M.cyl(24.0, ycw, 6.6, 19.0, 21.4), BANDED, 1)
    M.add(M.dome(24.0, ycw, 21.4, 6.6, 1.8, ribs=0), LEAD, 2)
    M.add(M.apse(24.0, yb1 - 0.4, 8.2, 3, 0, 16.0), BANDED, 1)
    M.add(M.semidome(24.0, yb1 - 0.4, 16.0, 7.0, '+y'), LEAD, 2)
    M.win(M.ring_windows(24.0, yb1, 5.6, 8.8, 9.0, 14.0, [60, 90, 120], 1.3))
    for xx in (16.6, 31.4):                                                           # 東牆扶壁
        M.add(M.box(xx - 0.9, xx + 0.9, yb1, yb1 + 3.6, 0, 11.0), BANDED, 1)
    # 窗：側廊兩層、中殿高窗、前廊
    for xx in (xa, xb):
        for yy in np.arange(50.0, 94.0, 4.4):
            M.win(M.arch_open(xx, yy, 3.0, 6.4, 1.4, normal='x', depth=2.4))
            M.win(M.arch_open(xx, yy, 9.6, 13.0, 1.4, normal='x', depth=2.4))
    for xx in (14.0, 34.0):
        for yy in np.arange(50.0, 58.0, 3.6):
            M.win(M.arch_open(xx, yy, 15.8, 18.4, 1.2, normal='x', depth=2.4))
    for xc in (14.0, 24.0, 34.0):
        M.door(M.arch_open(xc, yn, 0, 4.4 if xc == 24.0 else 3.6, 2.4 if xc == 24.0 else 1.8, normal='y', depth=2.0))
        M.win(M.arch_open(xc, yn, 7.0, 11.0, 2.0, normal='y', depth=2.0))
    # 牆：側廊拱頂起拱線（約 9 m）以下是方整石
    M.MAT[M.S & M.full(M.Z < 9.0) & (M.MAT == BANDED) & M.full(M.Y >= yn)] = STONE
    G, L = M.finish(shell_m=1.2, seed=532)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(24.0, 0.2, 0), 'dome-top': M.cell(24.0, yc, 34.6)}
    return G, L, anchors, {'穹頂頂（m）': 34.9}
