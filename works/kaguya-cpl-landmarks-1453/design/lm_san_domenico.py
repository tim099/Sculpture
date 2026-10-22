# 聖保羅與聖道明教堂（San Paolo e San Domenico，加拉塔的道明會修院教堂，1323–1337；今 Arap Camii）1453：義大利托缽修會式三走道長堂 ——
#   主堂高牆與木構人字屋頂（比側廊高、側高窗）、平直東端的方形聖所（交叉肋拱、比側廊高）、尖拱長窗、西北立面玫瑰窗與哥德式大門；
#   東北側廊外一排熱那亞家族禮拜堂；東南端西南側的方形鐘樓（底下哥德式尖拱通道、頂層三聯拱窗、磚砌四角錐尖頂）。小磚皮與方整石交替。
#   1453 年熱那亞人在用；1475–78 年才改成清真寺。
#   ⛔ 不做：鐘樓的鄂圖曼圓錐頂、1734 年的鄂圖曼門窗與 mihrab、1868 年的淨水亭與庭院、1913–19 年的平頂木屋架與降低的牆、阿拉伯風格的 son cemaat yeri。
#   沒做：修院的迴廊（配置查不到）。
#   研究整理：scratchpad/cpl/research_batch2.md §7；占地：OSM way 175518809（51.6 × 24.8 m、長軸 136°／316°、聖所在東南）、鐘樓 way 1204026749。
import numpy as np
import byz
from byz import BANDED, TILE, STONE, MARBLE, LEAD

KEY = 'san-domenico'
TITLE = '聖保羅與聖道明教堂 1453（San Paolo e San Domenico，加拉塔的道明會教堂，1323–1337）'
TITLE_SHORT = '聖道明教堂 1453'
MPV = 0.2
W, D, H = 26.0, 48.0, 30.0
META = {'kind': 'building', 'use': 'san-domenico', 'style': 'genoa', 'lot': '26,48', 'base': 0, 'variant': 'a', 'lamps': 10}
PARTS = (('body', 1, '主體（主堂、側廊、聖所、家族禮拜堂）'), ('roof', 2, '屋頂（紅瓦）'), ('tower', 3, '鐘樓'))
PROV = {
    '三走道長堂、平直東端的方形聖所（交叉肋拱 6.7 × 7.0 m）、兩列大理石柱、不設 narthex': '參考資料：Wikipedia；TBL；德文 Wikipedia；Kültür Envanteri',
    '主堂木構屋頂比側廊高（側高窗）、聖所高出側廊': '參考資料：TBL',
    '尖拱長窗、玫瑰窗（今已封）、哥德式大門': '參考資料：TBL；Wikipedia',
    '東北側廊外的家族禮拜堂': '參考資料：Wikipedia；TBL（推估）',
    '方形鐘樓、底下哥德式尖拱通道、原本的三聯窗': '參考資料：TDV（Eyice）；Wikipedia',
    '小磚皮與方整石交替': '參考資料：Wikipedia',
    '主堂寬 6.7 m、側廊 3.5 m、長 40 m': '設計決定（只有未證實的數字；聖所寬照 6.7 m）',
    '主堂簷口 13 m、側廊 7.5 m': '設計決定（1913–19 年降低了高度，原高查不到）',
    '鐘樓高 22 m＋四角錐尖頂 6 m、四角小尖塔': '設計決定（102 級階梯 ⇒ 約 20 m；原本的尖頂形式查不到，照 14 世紀利古里亞鐘樓）',
    '紅瓦屋頂': '設計決定',
}


def pointed(M, cx, cy, z0, z1, w, normal='y', depth=2.0):
    """尖拱開口（哥德式）：兩段圓弧交在頂上（半徑 ＝ 寬）。"""
    if normal == 'y':
        u, v = M.X - cx, M.Y - cy
    else:
        u, v = M.Y - cy, M.X - cx
    r = w
    zs = z1 - np.sqrt(max(r * r - (w / 2) ** 2, 0))              # 起拱線（兩段弧在 z1 交會；圓心在對面的起拱點）
    top = zs + np.sqrt(np.clip(r * r - (np.abs(u) + r - w / 2) ** 2, 0, None))
    return (np.abs(u) < w / 2) & (np.abs(v) < depth / 2) & (M.Z >= z0) & (M.Z < np.minimum(top, z1))


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.5, 0.6)
    M.band_z0 = 0.3
    nx0, nx1 = 8.5, 15.2                                          # 主堂
    ax0, ax1 = 5.0, 18.7                                          # 側廊外牆
    y0, y1, ys1 = 0.6, 40.0, 47.0                                 # 立面、主堂東端、聖所東端
    zn, za, zs = 13.0, 7.5, 14.0
    cx = (nx0 + nx1) / 2
    M.add(M.box(ax0, ax1, y0, y1, 0, za), BANDED, 1)                              # 側廊
    M.add(M.box(nx0, nx1, y0, y1, 0, zn), BANDED, 1)                              # 主堂高牆
    M.add(M.box(nx0, nx1, y1 - 0.4, ys1, 0, zs), BANDED, 1)                       # 聖所
    M.add(M.shed(ax0, nx0, y0, y1, za, za + 2.6, '+x'), TILE, 2)                  # 側廊屋頂
    M.add(M.shed(nx1, ax1, y0, y1, za, za + 2.6, '-x'), TILE, 2)
    M.add(M.gable(nx0 - 0.3, nx1 + 0.3, y0, y1, zn, 3.0, 'y'), TILE, 2)          # 主堂人字頂
    M.add(M.gable(nx0 - 0.3, nx1 + 0.3, y1, ys1 + 0.3, zs, 3.0, 'y'), TILE, 2)   # 聖所人字頂（高一點）
    M.add(M.box(nx0, nx1, y0 - 0.0, y0 + 0.6, zn, zn + 3.2) & M.gable(nx0, nx1, y0, y0 + 0.6, zn, 3.0, 'y'), BANDED, 1)   # 立面山牆
    # 東北側廊外的家族禮拜堂（一排四間）
    for k in range(4):
        c0 = 14.0 + k * 5.6
        M.add(M.box(1.0, ax0, c0, c0 + 5.0, 0, 6.2), BANDED, 1)
        M.add(M.shed(1.0, ax0, c0, c0 + 5.0, 6.2, 7.4, '+x'), TILE, 2)
        M.win(pointed(M, 1.0, c0 + 2.5, 2.2, 5.0, 0.8, normal='x', depth=1.6))
    # 窗：側高窗、側廊尖拱長窗、聖所高窗
    for yy in np.arange(4.0, y1 - 1.0, 4.2):
        for xx in (nx0, nx1):
            M.win(pointed(M, xx, yy, za + 3.0, za + 5.0, 0.7, normal='x', depth=1.6))
        if yy < 13.0 or yy > 37.0:
            M.win(pointed(M, ax0, yy, 2.2, 5.6, 0.8, normal='x', depth=1.6))
        M.win(pointed(M, ax1, yy, 2.2, 5.6, 0.8, normal='x', depth=1.6))
    for yy in (42.0, 45.0):
        for xx in (nx0, nx1):
            M.win(pointed(M, xx, yy, 3.0, 11.0, 0.9, normal='x', depth=1.6))
    for k in (-1, 0, 1):
        M.win(pointed(M, cx + k * 1.6, ys1, 3.0, 11.5 if k == 0 else 10.0, 0.8, normal='y', depth=1.6))
    # 立面：哥德式大門（尖拱）、玫瑰窗、側廊門
    M.door(pointed(M, cx, y0, 0, 4.6, 2.2, normal='y', depth=1.6))
    M.win(((M.X - cx) ** 2 + (M.Z - 10.0) ** 2 < 1.5 ** 2) & (np.abs(M.Y - y0) < 0.8))
    for xx in ((ax0 + nx0) / 2, (nx1 + ax1) / 2):
        M.win(pointed(M, xx, y0, 2.4, 5.4, 0.8, normal='y', depth=1.6))
    # 鐘樓（東南端的西南側）：方塔、底下尖拱通道、頂層四面三聯拱開口、磚砌四角錐尖頂＋四角小尖塔
    tx0, tx1, ty0, ty1 = 18.7, 24.9, 38.6, 44.8
    tcx, tcy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    M.add(M.box(tx0, tx1, ty0, ty1, 0, 22.0), BANDED, 3)
    M.add(M.box(tx0 - 0.3, tx1 + 0.3, ty0 - 0.3, ty1 + 0.3, 21.6, 22.0), STONE, 3)
    k = (M.Z - 22.0) / 6.5
    hw = 2.6 * (1 - k)
    M.add((M.Z >= 22.0) & (M.Z < 28.5) & (np.abs(M.X - tcx) < hw) & (np.abs(M.Y - tcy) < hw), BANDED, 3)
    for ex in (tx0 + 0.5, tx1 - 0.5):
        for ey in (ty0 + 0.5, ty1 - 0.5):
            kk = (M.Z - 22.0) / 2.4
            M.add((M.Z >= 22.0) & (M.Z < 24.4) & (np.abs(M.X - ex) < 0.45 * (1 - kk)) & (np.abs(M.Y - ey) < 0.45 * (1 - kk)), STONE, 3)
    M.add(M.box(tcx - 0.15, tcx + 0.15, tcy - 0.15, tcy + 0.15, 28.3, 29.8), byz.GOLD, 3)
    M.add(M.box(tcx - 0.5, tcx + 0.5, tcy - 0.15, tcy + 0.15, 29.0, 29.3), byz.GOLD, 3)
    for k3 in (-1, 0, 1):
        M.air(pointed(M, tcx + k3 * 1.5, tcy, 17.2, 20.6, 1.0, normal='y', depth=8.0) & M.box(tx0, tx1, ty0, ty1, 0, 99))
        M.air(pointed(M, tcx, tcy + k3 * 1.5, 17.2, 20.6, 1.0, normal='x', depth=8.0) & M.box(tx0, tx1, ty0, ty1, 0, 99))
    M.air(pointed(M, tcx, tcy, 0.0, 4.6, 3.0, normal='x', depth=8.0) & M.box(tx0, tx1, ty0, ty1, 0, 99))   # 底下的尖拱通道
    G, L = M.finish(shell_m=0.8, seed=1325)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(cx, y0 + 0.2, 0), 'bell': M.cell(tcx, tcy, 19.0)}
    return G, L, anchors, {'主堂簷口（m）': zn, '鐘樓尖頂（m）': 29.8}
