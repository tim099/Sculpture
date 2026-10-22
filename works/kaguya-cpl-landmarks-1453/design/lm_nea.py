# 新教堂（Nea Ekklesia，Basil I，880 年祝聖；大皇宮東南角）1453：大皇宮在帕列奧略時代被棄用，但 Nea 還立著
#   （撐過征服，鄂圖曼當火藥庫，1490 年雷擊爆炸）—— 五穹頂、多數學者認為是十字形平面；穹頂覆銅瓦；西邊中庭有兩座大理石噴泉。
#   ⚠ 位置與尺寸都查不到 ⇒ 30 × 30 m 的十字形平面、四角小穹頂、西邊 30 × 20 m 的中庭、中心 41.0050, 28.9800（今 Cankurtaran 一帶）全是設計。
#   ⛔ 不做：鄂圖曼的火藥庫改裝、1490 年後的廢墟、藍色清真寺、Arasta、鐵路。
#   研究整理：scratchpad/cpl/research_batch3.md §4。
import byz, church
from byz import BANDED, MARBLE, LEAD, STONE, SOIL

KEY = 'nea'
TITLE = '新教堂 1453（Nea Ekklesia，Basil I 880；大皇宮東南角、五穹頂）'
TITLE_SHORT = '新教堂（Nea）1453'
MPV = 0.2
W, D, H = 32.0, 56.0, 28.0
META = {'kind': 'building', 'use': 'nea', 'style': 'roman', 'lot': '32,56', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '教堂（十字形平面、前廊、三後殿）'), ('roof', 2, '屋頂與五座穹頂（銅瓦）'), ('atrium', 3, '中庭（柱廊、兩座噴泉）'))
PROV = {
    'Basil I 880 年祝聖；五穹頂；穹頂覆銅瓦；中庭兩座大理石噴泉': '參考資料：Wikipedia（Nea Ekklesia，引 Mango 1991 ODB p.1446）；TBL',
    '撐過 1453，鄂圖曼當火藥庫，1490 年雷擊爆炸': '參考資料：Wikipedia；TBL',
    '十字形平面（cross-in-square）': '參考資料：多數學者的看法（Wikipedia）',
    '位置、30 × 30 m、穹頂的大小與高、中庭 30 × 20 m': '設計決定（查不到）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.6, 1.0)
    x0, x1, y0, y1 = 1.0, 31.0, 22.0, 50.0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    P = {
        'naos': {'x': [x0, x1], 'y': [y0, y1], 'z': 13.0, 'arm_w': 9.6, 'arm_z': 16.0, 'roof': 'barrel', 'rise': 2.0, 'roof_mat': LEAD},
        'domes': [{'cx': cx, 'cy': cy, 'r': 5.4, 'n': 12, 'z0': 17.6, 'h': 3.6, 'win': 12, 'rise': 4.6, 'ribs': 24, 'cross': True}] +
                 [{'cx': ax, 'cy': ay, 'r': 2.9, 'n': 8, 'z0': 13.4, 'h': 2.6, 'win': 8, 'rise': 2.4, 'ribs': 8} for ax in (6.2, 25.8) for ay in (27.2, 44.8)],
        'apses': [{'cx': cx, 'r': 4.6, 'facets': 3, 'z': 12.0, 'roof_mat': LEAD, 'win': 3, 'win_w': 0.9}, {'cx': 6.0, 'r': 2.4, 'facets': 3, 'z': 9.0, 'roof_mat': LEAD, 'win': 1},
                  {'cx': 26.0, 'r': 2.4, 'facets': 3, 'z': 9.0, 'roof_mat': LEAD, 'win': 1}],
        'bays': [{'x': [x0, x1], 'y': [17.0, y0], 'z': 10.0, 'roof': 'shed', 'high': '+y', 'rise': 1.4, 'roof_mat': LEAD,
                  'arcade_x': [5.0, 11.0, 16.0, 21.0, 27.0], 'arc_z0': 3.0, 'arc_z1': 8.0, 'arc_w': 2.0}],
        'door': [{'x': 16.0, 'y': 17.0, 'w': 2.4, 'h': 4.4}, {'x': 9.0, 'y': 17.0, 'w': 1.6, 'h': 3.4}, {'x': 23.0, 'y': 17.0, 'w': 1.6, 'h': 3.4}],
    }
    church.cross_in_square(M, P)
    M.MAT[M.S & M.full(M.Z < 1.2) & (M.MAT == BANDED)] = STONE
    # 中庭：三面柱廊（單坡、柱子）、正中兩座八角噴泉、西面的門
    A = 3
    M.add(M.box(0.0, W, 0.0, 1.2, 0, 7.0) | M.box(0.0, 1.2, 0.0, 17.0, 0, 7.0) | M.box(W - 1.2, W, 0.0, 17.0, 0, 7.0), BANDED, A)
    for (bx0, bx1, by0, by1, high) in ((1.2, W - 1.2, 1.2, 5.0, '-y'), (1.2, 5.0, 5.0, 17.0, '-x'), (W - 5.0, W - 1.2, 5.0, 17.0, '+x')):
        M.add(M.shed(bx0, bx1, by0, by1, 6.0, 7.0, high), LEAD, A)
    for xx in range(3, 31, 3):
        M.add(M.cyl(xx + 0.5, 5.0, 0.3, 0, 6.0), MARBLE, A)
    for yy in range(7, 17, 3):
        M.add(M.cyl(5.0, yy + 0.0, 0.3, 0, 6.0) | M.cyl(W - 5.0, yy + 0.0, 0.3, 0, 6.0), MARBLE, A)
    M.add(M.box(5.0, W - 5.0, 5.0, 17.0, 0, 0.2), MARBLE, A)                                         # 中庭鋪面
    for fx in (11.0, 21.0):
        M.add(M.ngon(fx, 11.0, 2.2, 8, 0.2, 0.9, rot=22.5) & ~M.ngon(fx, 11.0, 1.7, 8, 0.4, 9, rot=22.5), MARBLE, A)
        M.add(M.cyl(fx, 11.0, 0.35, 0.2, 2.0) | M.cyl(fx, 11.0, 0.8, 1.7, 2.0), MARBLE, A)
    M.door(M.arch_open(16.0, 0.0, 0, 4.0, 2.8, normal='y', depth=2.4))
    G, L = M.finish(shell_m=0.8, seed=880, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(16.0, 0.2, 0), 'top': M.cell(cx, cy, 17.6 + 3.6 + 4.6)}
    return G, L, anchors, {'主穹頂頂（m）': round(17.6 + 3.6 + 4.6, 1)}
