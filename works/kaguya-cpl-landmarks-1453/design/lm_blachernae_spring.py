# Blachernae 的聖泉浴堂（Hagion Louma；聖母教堂的聖泉）1453：1434 年大火裡只剩泉水 ——
#   做成：一間小小的穹頂浴堂（方室、東邊小後殿、西邊前廊與門、裡面往下的台階到泉池），旁邊一口井欄；還有人來取水 ⇒ 門口一盞燈。
#   ⚠ 1453 年的建築查不到：今日的 Ayvansaray 教堂是 1867 年蓋的（排除）⇒ 平面、大小全是設計決定。
#   研究整理：scratchpad/cpl/research_batch7.md §1。
import byz, church
from byz import BANDED, BRICK, STONE, LEAD, TILE, MARBLE

KEY = 'blachernae-spring'
TITLE = 'Blachernae 的聖泉浴堂 1453（Hagion Louma；小穹頂堂＋泉池）'
TITLE_SHORT = 'Blachernae 聖泉 1453'
MPV = 0.2
W, D, H = 12.0, 14.0, 11.0
META = {'kind': 'building', 'use': 'blachernae-spring', 'style': 'roman', 'lot': '12,14', 'base': 0, 'variant': 'a', 'lamps': 4}
PARTS = (('body', 1, '主體（方室、前廊、後殿、井欄）'), ('roof', 2, '屋頂（穹頂、瓦）'))
PROV = {
    '聖母教堂的聖泉、聖浴場 Hagion Louma；1434 年大火只剩泉水': '參考資料：Wikipedia（Church of St. Mary of Blachernae）',
    '平面、大小、穹頂、井欄': '設計決定（1867 年的教堂不算）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.2)
    P = {
        'naos': {'x': [1.5, 10.5], 'y': [3.5, 11.0], 'z': 5.0, 'arm_w': 3.2, 'arm_z': 6.0, 'roof': 'barrel', 'rise': 0.8},
        'domes': [{'cx': 6.0, 'cy': 7.25, 'r': 2.2, 'n': 8, 'z0': 6.2, 'h': 1.2, 'win': 4, 'rise': 1.8, 'ribs': 8, 'cross': True}],
        'apses': [{'cx': 6.0, 'r': 1.5, 'facets': 5, 'z': 4.2, 'win': 1, 'win_w': 0.5}],
        'bays': [{'x': [1.5, 10.5], 'y': [0.6, 3.5], 'z': 4.0, 'roof': 'shed', 'high': '+y', 'rise': 0.6, 'arcade_x': [3.5, 8.5], 'arc_z0': 0.6, 'arc_z1': 3.0, 'arc_w': 1.4}],
        'door': [{'x': 6.0, 'w': 1.2, 'h': 2.4}],
    }
    church.cross_in_square(M, P)
    M.add(M.cyl(10.8, 1.6, 0.8, 0, 0.9) & ~M.cyl(10.8, 1.6, 0.45, -1, 99), MARBLE, 1)   # 井欄
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=473)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(6.0, 0.8, 0.0), 'dome-top': M.cell(6.0, 7.25, 9.2)}
    return G, L, anchors, {'穹頂頂（m）': 9.2}
