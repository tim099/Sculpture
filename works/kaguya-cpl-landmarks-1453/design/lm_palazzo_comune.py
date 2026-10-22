# 熱那亞總督府（Palazzo del Comune，Podestà 宮，加拉塔；1314 Montano de Marinis 建、1315 火災、1316 重建）1453：照熱那亞 Palazzo San Giorgio 1260 翼 ——
#   四層：底層灰白方整石、五個尖拱的柱廊（朝南、朝金角灣）；上面三層清水紅磚、每層三聯尖拱窗（白石框）；頂上一圈燕尾雉堞（Ghibelline）；
#   立面掛熱那亞十字與歷任 Podestà 的紋章石（背面 Luchino de Facio 約 1446–47 的那一塊 1453 年已經在牆上）。
#   ⛔ 不做：1880 年代拆掉南面三分之二後的 Bereket Han 立面、Bankalar Cd 的近代銀行建築。沒做：塔樓（沒有來源提到）。
#   研究整理：scratchpad/cpl/research_batch2.md §8；占地：OSM way 165521785（Podestat Sarayı，18.4 × 11.8 m、約 120°，與 Bankalar Cd 平行）
#   —— 那只是今天剩下的北側約三分之一 ⇒ 進深做 26 m（往南伸進今天的街）。
import numpy as np
import byz
from byz import BRICK, STONE, TILE, MARBLE

KEY = 'palazzo-comune'
TITLE = '熱那亞總督府 1453（Palazzo del Comune，加拉塔的 Podestà 宮，1316）'
TITLE_SHORT = '熱那亞總督府 1453'
MPV = 0.2
W, D, H = 18.0, 26.0, 22.0
META = {'kind': 'building', 'use': 'palazzo-comune', 'style': 'genoa', 'lot': '18,26', 'base': 0, 'variant': 'a', 'lamps': 6}
PARTS = (('body', 1, '主體（石砌柱廊、磚砌三層、雉堞、紋章石）'), ('roof', 2, '屋頂（紅瓦）'))
PROV = {
    '1314 年建、1315 火災、1316 重建；範本 Palazzo San Giorgio 1260 翼；四層': '參考資料：Wikipedia（Genoese Palace）；TBL',
    '底層五個尖拱柱廊、灰色石；上層清水磚；三聯與四聯窗；燕尾雉堞': '參考資料：Wikipedia（Palazzo San Giorgio）',
    'Luchino de Facio（約 1446–47）的紋章石（2021 年被盜）⇒ 1453 年已經在牆上': '參考資料：Wikipedia',
    '臨街寬 18.4 m（今存北側約三分之一）': '參考資料：OSM way 165521785；Wikipedia（1880 年代拆了南面三分之二）',
    '進深 26 m、總高 19.6 m＋雉堞、窗與柱廊的大小': '設計決定（原進深與立面細節查不到）',
    '沒有塔樓': '設計決定（沒有來源提到）',
}


def pointed(M, cx, cy, z0, z1, w, normal='y', depth=2.0):
    """尖拱開口：兩段圓弧（半徑 ＝ 寬、圓心在對面的起拱點）交在頂上。"""
    if normal == 'y':
        u, v = M.X - cx, M.Y - cy
    else:
        u, v = M.Y - cy, M.X - cx
    zs = z1 - np.sqrt(max(w * w - (w / 2) ** 2, 0))
    top = zs + np.sqrt(np.clip(w * w - (np.abs(u) + w / 2) ** 2, 0, None))
    return (np.abs(u) < w / 2) & (np.abs(v) < depth / 2) & (M.Z >= z0) & (M.Z < np.minimum(top, z1))


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 0.0)
    x0, x1, y0, y1 = 0.4, 17.6, 0.4, 25.6
    zg, zt = 5.6, 19.6                                           # 底層頂、簷口（雉堞底）
    M.add(M.box(x0, x1, y0, y1, 0, zg), STONE, 1)
    M.add(M.box(x0, x1, y0, y1, zg, zt), BRICK, 1)
    M.add(M.box(x0, x1, y0, y1, zg - 0.3, zg), STONE, 1)                          # 石帶
    # 底層柱廊：正面五個尖拱、往裡 4 m 是開的（柱廊）
    bw = (x1 - x0) / 5
    for k in range(5):
        xc = x0 + bw * (k + 0.5)
        M.air(pointed(M, xc, y0, 0.0, 4.8, bw - 0.9, normal='y', depth=0.8) | (pointed(M, xc, y0 + 2.4, 0.0, 4.8, bw - 0.9, normal='y', depth=4.0)))
    M.air(M.box(x0 + 0.6, x1 - 0.6, y0 + 0.8, y0 + 4.2, 0.0, 4.2))
    M.door(M.arch_open((x0 + x1) / 2, y0 + 4.4, 0.0, 3.4, 1.8, normal='y', depth=1.0))
    # 上面三層：正面每層五組三聯尖拱窗（白石框）；兩側與背面每層一排雙聯窗
    for zf in (6.6, 11.2, 15.8):
        for k in range(5):
            xc = x0 + bw * (k + 0.5)
            M.add(M.box(xc - 1.25, xc + 1.25, y0 - 0.2, y0 + 0.2, zf - 0.3, zf - 0.1), MARBLE, 1)   # 窗台
            for j in (-1, 0, 1):
                M.win(pointed(M, xc + j * 0.75, y0, zf, zf + 2.6, 0.55, normal='y', depth=1.6))
        for yy in np.arange(3.0, y1 - 1.0, 3.2):
            for xx in (x0, x1):
                for j in (-1, 1):
                    M.win(pointed(M, xx, yy + j * 0.45, zf, zf + 2.4, 0.55, normal='x', depth=1.6))
        for k in range(5):
            xc = x0 + bw * (k + 0.5)
            for j in (-1, 1):
                M.win(pointed(M, xc + j * 0.45, y1, zf, zf + 2.4, 0.55, normal='y', depth=1.6))
    # 紋章石（正面柱廊上方一排、白石、凸一格）
    for k in range(1, 5):                                        # 拱與拱之間的墩上
        xc = x0 + bw * k
        M.add(M.box(xc - 0.35, xc + 0.35, y0 - 0.2, y0 + 0.2, zg - 1.5, zg - 0.4), MARBLE, 1)
    # 燕尾雉堞：每 1.4 m 一個、寬 0.8、高 1.4、頂上剪一個 V
    def merlons(along, a0, a1, fixed, axis):
        for a in np.arange(a0 + 0.4, a1 - 0.4, 1.4):
            if axis == 'x':
                blk = M.box(a - 0.4, a + 0.4, fixed - 0.3, fixed + 0.3, zt, zt + 1.4)
                notch = (np.abs(M.X - a) < 0.2 + (M.Z - (zt + 1.0)) * 0.5) & (M.Z >= zt + 1.0)
            else:
                blk = M.box(fixed - 0.3, fixed + 0.3, a - 0.4, a + 0.4, zt, zt + 1.4)
                notch = (np.abs(M.Y - a) < 0.2 + (M.Z - (zt + 1.0)) * 0.5) & (M.Z >= zt + 1.0)
            M.add(blk & ~notch, BRICK, 1)
    merlons('x', x0, x1, y0 + 0.3, 'x'); merlons('x', x0, x1, y1 - 0.3, 'x')
    merlons('y', y0, y1, x0 + 0.3, 'y'); merlons('y', y0, y1, x1 - 0.3, 'y')
    M.add(M.hip(x0 + 0.8, x1 - 0.8, y0 + 0.8, y1 - 0.8, zt - 0.2, 1.2, 0.5), TILE, 2)   # 雉堞後面的低四坡瓦頂
    G, L = M.finish(shell_m=0.8, seed=1316)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell((x0 + x1) / 2, y0 + 0.2, 0)}
    return G, L, anchors, {'簷口（m）': zt, '雉堞頂（m）': zt + 1.4}
