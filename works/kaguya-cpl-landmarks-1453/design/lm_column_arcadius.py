# 阿卡狄烏斯紀念柱（Xerolophos，402–421）1453：雕像 740 年地震倒下、之後沒有重立 ⇒ 柱身（螺旋浮雕帶、內梯的小窗）＋空的雕像座＋錐頂；1715／1719 年才拆。
#   研究整理：kaguya 暫存區 scratchpad/cpl/research_columns_churches.md §A2。
import math
import byz, columns
from byz import MARBLE, STONE

KEY = 'column-arcadius'
TITLE = '阿卡狄烏斯紀念柱 1453（Column of Arcadius，Xerolophos；雕像 740 年已倒）'
TITLE_SHORT = '阿卡狄烏斯紀念柱 1453'
MPV = 0.2
W, D, H = 10.0, 10.0, 50.0
META = {'kind': 'building', 'use': 'column-arcadius', 'style': 'roman', 'lot': '10,10', 'base': 0, 'variant': 'a', 'lamps': 4}
PARTS = (('body', 1, '柱（台階、浮雕基座、螺旋浮雕柱身、柱頭）'), ('top', 2, '空的雕像座與錐頂'))
PROV = {
    '台階 3 級共 2 m、基座 8 m 高、柱身連柱礎 31.92 m、雕像座 4 m': '參考資料：Wikipedia 引 Konrad 2001 p.370、Bauer 1996 p.208（照殘存部分重建）',
    '柱身外徑 4.1 → 3.8 m': '參考資料：Gyllius（內周 28 ft、壁厚底 2 ft 3 digit、頂 1 ft 9 in）⇒ 推算',
    '柱頭 1.7 m': '參考資料：Kollwitz 1.66 m（經 tezara 21752）',
    '螺旋浮雕帶 13 圈': '參考資料：TBL 引用的敘事圈編號到 13',
    '56 個小窗、門在基座北面 1.9 × 1.14 m': '參考資料：Gyllius（56 個小窗、門 6 ft 2 digit × 3 ft 9 in）；TBL（北面）',
    '基座寬 6.5 m、台階寬、柱礎 1.2 m、柱頭寬 4.6 m、錐頂 1.5 m': '設計決定（查無；今天殘存的基座核心長 6 m）',
    '總高 49.1 m': '量回來；Gyllius 記 147 ft（約 44.8 m）、Kollwitz 推算近 50 m',
}


def build():
    M = byz.Model(W, D, H, MPV)
    cx = cy = 5.0
    C = {'steps': [[9.6, 0.67], [8.6, 0.67], [7.6, 0.66]], 'pedestal': {'w': 6.5, 'h': 8.0, 'mat': MARBLE, 'cornice': 0.25}, 'base': {'d': 4.6, 'h': 1.2},
         'shaft': {'d0': 4.1, 'd1': 3.8, 'h': 30.72, 'mat': MARBLE, 'spiral': {'turns': 13, 'band': 0.4, 'depth': 0.2}},
         'capital': {'w': 4.6, 'h': 1.7, 'mat': MARBLE}}
    z_shaft0 = 2.0 + 8.0 + 1.2
    ztop = columns.column(M, cx, cy, C, lay=1)
    # 基座四面的浮雕（四層）：每層一道往外凸的帶；北面的門（模型 y 0 ＝ 北：地塊 rot 270）
    for k in range(4):
        z0 = 2.0 + 0.8 + k * 1.75
        M.add(M.box(cx - 3.35, cx + 3.35, cy - 3.35, cy + 3.35, z0, z0 + 0.4) & ~M.box(cx - 3.2, cx + 3.2, cy - 3.2, cy + 3.2, 0, 99), MARBLE, 1)
    M.door(M.arch_open(cx, cy - 3.25, 2.0, 2.0 + 1.9, 1.14, normal='y', depth=1.0))
    # 內梯的小窗：沿螺旋往上 56 個（一圈約 4 個）
    for k in range(56):
        zw = z_shaft0 + 1.0 + k * (30.72 - 2.0) / 56
        r = 2.05 - 0.15 * (zw - z_shaft0) / 30.72
        M.win(M.ring_windows(cx, cy, r - 0.8, r + 0.5, zw, zw + 0.6, [k * 97.0], 0.12))
    # 空的雕像座（3.2 m 見方、4 m）＋ 錐頂
    M.add(M.box(cx - 1.6, cx + 1.6, cy - 1.6, cy + 1.6, ztop, ztop + 4.0), MARBLE, 2)
    k = (M.Z - (ztop + 4.0)) / 1.5
    M.add((M.Z >= ztop + 4.0) & (M.Z < ztop + 5.5) & ((M.X - cx) ** 2 + (M.Y - cy) ** 2 < (1.6 * (1 - k)) ** 2), STONE, 2)
    G, L = M.finish(shell_m=0.8, seed=402)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(cx, 0.2, 2.0), 'top': M.cell(cx, cy, ztop + 5.3)}
    return G, L, anchors, {'柱頭頂（m）': round(ztop, 2), '錐頂（m）': round(ztop + 5.5, 2)}
