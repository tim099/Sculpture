# 曼加納聖喬治修道院（St George of the Mangana，Constantine IX Monomachos，1047 年祝聖）1453：修道院運作到征服 ——
#   Clavijo 1403：過第一道門是大院子，有許多房屋與果園，教堂在花園正中；門外有大洗禮池，覆以 8 根大理石柱撐的華蓋；教堂「非常高」、滿是馬賽克。
#   主堂約 27 × 33 m、主穹頂直徑約 10 m、四墩（BL 依 Demangel & Mamboury 1939）。
#   ⚠ 位置是推測（今天沒有東西留在地面上；Kynegion 以南、İncili Köşk 以西不遠）：中心 41.0106, 28.9858；穹頂高、前院大小、房舍、果園是設計。
#   ⛔ 不做：Mangana 宮（Isaac II 已拆，1453 年是廢墟或沒了）、Topkapı 的外牆（1478）、İncili Köşk、Gülhane、鐵路。
#   研究整理：scratchpad/cpl/research_batch3.md §6；research_palaces_cisterns.md §8。
import byz, church
from byz import BANDED, MARBLE, LEAD, STONE, TILE, SOIL

KEY = 'mangana'
TITLE = '曼加納聖喬治修道院 1453（St George of the Mangana，1047；前院、房舍、果園、八柱洗禮池）'
TITLE_SHORT = '曼加納聖喬治修道院 1453'
MPV = 0.2
W, D, H = 46.0, 82.0, 28.0
META = {'kind': 'building', 'use': 'mangana', 'style': 'roman', 'lot': '46,82', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主堂（十字形平面、穹頂、前廊、三後殿）'), ('roof', 2, '屋頂'), ('court', 3, '院牆、門、房舍、洗禮池的華蓋'),
         ('trees-fruit', 4, '果樹（遊戲換成生成式的果樹）', {'kind': 'tree', 'tree': 'fruit'}),
         ('trees-cypress', 5, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}))
PROV = {
    '主堂約 27 × 33 m、主穹頂直徑約 10 m、四墩': '參考資料：TBL（georgios-mangana，依 Demangel & Mamboury 1939）',
    '大院子、許多房屋與果園、教堂在花園正中；門外大洗禮池，8 根大理石柱撐的華蓋；教堂非常高': '參考資料：Clavijo 1403（Markham 1859 英譯 p.38–39）',
    '修道院運作到 1453': '參考資料：Wikipedia（Mangana，引 ODB p.1283–84）',
    '位置、穹頂高、院子的大小、房舍與果樹的位置': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.6, 1.0)
    x0, x1, y0, y1 = 9.5, 36.5, 44.0, 72.0                 # 主堂（含前廊共 33 m）
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    P = {
        'naos': {'x': [x0, x1], 'y': [y0, y1], 'z': 13.0, 'arm_w': 10.4, 'arm_z': 16.0, 'roof': 'barrel', 'rise': 2.2, 'roof_mat': LEAD},
        'domes': [{'cx': cx, 'cy': cy, 'r': 5.6, 'n': 12, 'z0': 17.0, 'h': 3.2, 'win': 12, 'rise': 4.8, 'ribs': 24, 'cross': True}],
        'apses': [{'cx': cx, 'r': 4.4, 'facets': 3, 'z': 12.0, 'roof_mat': LEAD, 'win': 3, 'win_w': 0.9}, {'cx': 13.5, 'r': 2.4, 'facets': 3, 'z': 9.0, 'roof_mat': LEAD, 'win': 1},
                  {'cx': 32.5, 'r': 2.4, 'facets': 3, 'z': 9.0, 'roof_mat': LEAD, 'win': 1}],
        'bays': [{'x': [x0, x1], 'y': [39.0, y0], 'z': 10.0, 'roof': 'shed', 'high': '+y', 'rise': 1.4, 'roof_mat': LEAD,
                  'arcade_x': [13.0, 18.0, 23.0, 28.0, 33.0], 'arc_z0': 3.0, 'arc_z1': 8.0, 'arc_w': 1.8}],
        'door': [{'x': 23.0, 'y': 39.0, 'w': 2.4, 'h': 4.2}],
    }
    church.cross_in_square(M, P)
    M.MAT[M.S & M.full(M.Z < 1.2) & (M.MAT == BANDED)] = STONE
    # 院牆（一圈 5 m、正面的門樓）、兩側的房舍（單坡貼牆）
    C = 3
    t = 1.0
    for bx0, bx1, by0, by1 in ((0, W, 0, t), (0, t, 0, D), (W - t, W, 0, D), (0, W, D - t, D)):
        M.add(M.box(bx0, bx1, by0, by1, 0, 5.0), BANDED, C)
    M.add(M.box(18.0, 28.0, 0, 6.0, 0, 8.0), BANDED, C)
    M.add(M.gable(18.0, 28.0, 0, 6.0, 8.0, 1.6, 'y'), TILE, 2)
    M.door(M.arch_open(23.0, 0.0, 0, 4.0, 3.0, normal='y', depth=2.4))
    M.air(M.arch_open(23.0, 3.0, 0, 4.0, 3.0, normal='y', depth=6.4))
    for yy0 in (8.0, 20.0, 50.0, 62.0):                                                             # 修士的房舍：東西兩側各四棟
        for (bx0, bx1, high) in ((t, 7.0, '-x'), (W - 7.0, W - t, '+x')):
            M.add(M.box(bx0, bx1, yy0, yy0 + 9.0, 0, 5.6), BANDED, C)
            M.add(M.shed(bx0, bx1, yy0, yy0 + 9.0, 5.6, 7.0, high), TILE, 2)
            xd = bx1 if high == '-x' else bx0
            M.door(M.arch_open(xd, yy0 + 4.5, 0, 2.4, 1.2, normal='x', depth=1.6))
            for dy in (2.0, 7.0):
                M.win(M.arch_open(xd, yy0 + dy, 2.8, 4.4, 0.7, normal='x', depth=1.6))
    # 洗禮池：門內（院子前段）一座圓池，覆八根大理石柱撐的華蓋（穹頂）
    px, py = 23.0, 13.0
    M.add(M.cyl(px, py, 3.0, 0, 0.9) & ~M.cyl(px, py, 2.4, 0.3, 9), MARBLE, C)
    for k in range(8):
        a = byz.math.radians(22.5 + 45 * k)
        M.add(M.cyl(px + 3.6 * byz.math.cos(a), py + 3.6 * byz.math.sin(a), 0.3, 0, 5.0), MARBLE, C)
    M.add(M.ngon(px, py, 4.2, 8, 5.0, 5.8, rot=22.5), MARBLE, C)
    M.add(M.dome(px, py, 5.8, 3.8, 2.4, ribs=8), LEAD, 2)
    # 院子：花園的土、果樹、教堂前兩排柏樹
    M.add(M.box(t, W - t, t, 38.0, 0, 0.2) & ~M.box(20.0, 26.0, t, 38.0, 0, 9) & ~M.cyl(px, py, 4.6, 0, 9), SOIL, C)
    M.add(M.box(20.0, 26.0, 6.0, 39.0, 0, 0.2), MARBLE, C)
    for (tx, ty) in ((11.0, 9.0), (14.0, 24.0), (10.0, 32.0), (33.0, 9.0), (34.0, 24.0), (36.0, 32.0), (40.0, 76.0), (6.0, 76.0), (12.0, 78.0), (34.0, 78.0)):
        M.tree(tx, ty, 5.5, 4.4, 4)
    for ty in (20.0, 26.0, 32.0):
        for tx in (18.0, 28.0):
            M.tree(tx, ty, 9.0, 2.2, 5)
    G, L = M.finish(shell_m=0.8, seed=1047, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(23.0, 0.2, 0), 'top': M.cell(cx, cy, 17.0 + 3.2 + 4.8)}
    return G, L, anchors, {'主穹頂頂（m）': round(17.0 + 3.2 + 4.8, 1)}
