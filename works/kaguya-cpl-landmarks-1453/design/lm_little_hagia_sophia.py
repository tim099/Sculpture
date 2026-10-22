# 小聖索菲亞（聖塞爾吉烏斯與巴克斯教堂，Sts Sergius & Bacchus，527–536）1453：方中八角、16 瓣的鉛皮穹頂（8 平瓣開窗、8 凹瓣不開）；西邊是前廊與中庭。
#   ⛔ 不做（1506–13 改寺）：西側 5 小圓頂、6 柱的門廊（取代了中庭）、宣禮塔、medrese、改成方形的窗。
#   研究整理：scratchpad/cpl/research_columns_churches.md §B4；占地：OSM way 303179753（45.5 × 28.3 m 含鄂圖曼門廊、軸方位 105.5°）。
import math
import numpy as np
import byz, church
from byz import BANDED, STONE, LEAD, TILE, MARBLE

KEY = 'little-hagia-sophia'
TITLE = '小聖索菲亞 1453（聖塞爾吉烏斯與巴克斯教堂，527–536）'
TITLE_SHORT = '小聖索菲亞 1453'
MPV = 0.2
W, D, H = 24.0, 52.0, 24.0
META = {'kind': 'building', 'use': 'little-hagia-sophia', 'style': 'roman', 'lot': '24,52', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（方殿、前廊、後殿）'), ('roof', 2, '屋頂（16 瓣穹頂、鉛皮）'), ('atrium', 3, '中庭（圍牆與柱廊）'))
PROV = {
    '外框東西 30.8 × 南北 23.6 m（含前廊、不計牆龕）；內八角 16.3 × 15.4 m；墩高 10.2 m；樓座 6.1 m': '參考資料：van Millingen 1912（英尺實測）',
    '穹頂 16 瓣：8 平瓣各開 1 窗、8 凹瓣不開；鋪鉛；直徑約 16 m': '參考資料：van Millingen 1912；TBL',
    '頂冠離地約 21 m': '設計決定：TBL 寫「超過 30 m」，照墩高推算 20–22 m',
    '後殿內半圓、外 3 面、三扇大磚拱窗；沒有側後殿': '參考資料：van Millingen 1912；TBL',
    '牆：磚加碎石、灰縫厚、偶夾石帶': '參考資料：van Millingen 1912；TBL',
    '中庭與外框同寬、深 18 m、單圈柱廊': '設計決定（查無；1506–13 年被門廊取代）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (2.0, 0.35)
    y0 = 18.0                                    # 前廊西牆
    yb = y0 + 30.8                               # 東牆
    # 方殿＋前廊（南牆比北牆短 2.5 m：東南角斜切）
    M.add(M.box(0.2, 23.8, y0, yb, 0, 13.5), BANDED, 1)
    M.add(M.hip(0.2, 23.8, y0 + 5.5, yb, 13.5, 1.4, 0.3), LEAD, 2)
    M.add(M.shed(0.2, 23.8, y0, y0 + 5.5, 9.5, 11.0, '+y'), TILE, 2)
    M.add(M.box(0.2, 23.8, y0, y0 + 5.5, 0, 9.5), BANDED, 1)
    M.S[M.full(M.box(0.2, 23.8, y0, y0 + 5.5, 11.2, 13.6))] = False
    # 南牆比北牆短 2.5 m（TBL）：東南角斜切（連屋頂）
    cut = (M.X > 23.8 - 2.5 * np.clip((M.Y - (yb - 6.0)) / 6.0, 0, 1))
    M.S[M.full(cut & M.box(0, 24, yb - 6.0, yb, 0, 99))] = False
    # 八角鼓座＋16 瓣穹頂（中心照內八角的中心）
    cx, cy = 11.8, y0 + 5.5 + (30.8 - 5.5) / 2
    M.add(M.ngon(cx, cy, 9.2, 8, 13.5, 15.6, rot=22.5), BANDED, 1)
    ang = np.arctan2(M.Y - cy, M.X - cx)
    rr = np.hypot(M.X - cx, M.Y - cy)
    lobe = 0.92 + 0.08 * np.abs(np.cos(8 * ang))          # 16 瓣起伏（外觀起伏）
    R = 8.2
    M.add((rr / (R * lobe)) ** 2 + ((M.Z - 15.6) / 5.4) ** 2 <= 1, LEAD, 2)
    M.add((M.Z >= 15.6) & (M.Z < 16.6) & (rr <= R + 0.4), LEAD, 2)
    M.domes.append((cx, cy, 15.6, R, 16))
    M.win(M.ring_windows(cx, cy, R - 1.6, R + 0.8, 16.0, 17.6, [22.5 + 45 * k for k in range(8)], 0.6))
    # 後殿（內半圓、外 3 面）、三扇大窗
    M.add(M.apse(cx, yb - 0.2, 4.6, 3, 0, 12.0), BANDED, 1)
    M.add(M.semidome(cx, yb - 0.2, 12.0, 4.0, '+y'), LEAD, 2)
    M.win(M.ring_windows(cx, yb, 3.0, 5.2, 6.0, 10.5, [60, 90, 120], 0.9))
    # 側牆的窗（樓座那一層、底層）、前廊的門
    for xx in (0.2, 23.8):
        for yy in np.arange(y0 + 8.0, yb - 3.0, 4.0):
            M.win(M.arch_open(xx, yy, 7.5, 10.5, 1.4, normal='x', depth=2.4))
            M.win(M.arch_open(xx, yy, 2.5, 5.0, 1.2, normal='x', depth=2.4))
    for xc in (5.0, 11.8, 18.6):
        M.door(M.arch_open(xc, y0, 0, 3.8 if xc == 11.8 else 3.2, 2.0 if xc == 11.8 else 1.6, normal='y', depth=2.0))
    # 中庭：外牆 6 m、三面單圈柱廊（往裡斜的屋頂）、西門
    A = 3
    for (x0, x1, yy0, yy1) in ((0.2, 23.8, 0.0, 0.8), (0.2, 1.0, 0.0, y0), (23.0, 23.8, 0.0, y0)):
        M.add(M.box(x0, x1, yy0, yy1, 0, 6.0), BANDED, A)
    for (x0, x1, yy0, yy1, hi) in ((1.0, 23.0, 0.8, 4.2, '-y'), (1.0, 4.4, 0.8, y0, '-x'), (19.6, 23.0, 0.8, y0, '+x')):
        M.add(M.shed(x0, x1, yy0, yy1, 4.6, 5.8, hi), TILE, A)
    for xx in np.arange(4.4, 20.0, 3.0):
        M.add(M.box(xx - 0.3, xx + 0.3, 4.0, 4.6, 0, 4.6), MARBLE, A)
    for yy in np.arange(5.0, y0, 3.0):
        M.add(M.box(4.0, 4.6, yy - 0.3, yy + 0.3, 0, 4.6), MARBLE, A)
        M.add(M.box(19.4, 20.0, yy - 0.3, yy + 0.3, 0, 4.6), MARBLE, A)
    M.door(M.arch_open(11.8, 0.0, 0, 3.6, 2.4, normal='y', depth=2.0))
    M.air(M.arch_open(11.8, 0.4, 0, 3.6, 2.4, normal='y', depth=1.0))
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=527)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(11.8, 0.2, 0), 'dome-top': M.cell(cx, cy, 20.8)}
    return G, L, anchors, {'穹頂頂（m）': 21.0}
