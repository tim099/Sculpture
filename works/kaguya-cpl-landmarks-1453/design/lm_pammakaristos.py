# 至福聖母修道院（Pammakaristos／Fethiye）1453：12 世紀的迴廊式主堂（北翼 13 世紀末、西南翼 14 世紀）＋南側 Glabas 遺孀約 1310 年的側堂（瘦高、五個穹頂那一座）；1455/56–1587 是牧首區駐地。
#   ⛔ 不做（約 1590 年 Murad III 改寺）：東側斜向的大圓頂 mihrab 室 ⇒ 還原成 3 個後殿；改柱為拱；鄂圖曼開的西門、南門；宣禮塔；medrese。
#   研究整理：scratchpad/cpl/research_columns_churches.md §B5；占地：OSM way 136456159（33.5 × 25.9 m、軸方位 97.5°）。
import byz, church
from byz import BANDED, STONE, LEAD, TILE

KEY = 'pammakaristos'
TITLE = '至福聖母修道院 1453（Pammakaristos，主堂與 Glabas 側堂 1310）'
TITLE_SHORT = '至福聖母修道院 1453'
MPV = 0.2
W, D, H = 26.0, 34.0, 24.0
META = {'kind': 'building', 'use': 'pammakaristos', 'style': 'roman', 'lot': '26,34', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（主堂、迴廊、前廊、側堂、後殿）'), ('roof', 2, '屋頂（穹頂、瓦）'))
PROV = {
    '主堂穹頂高鼓座、24 瓣隔瓣開窗（12 窗）': '參考資料：van Millingen 1912；直徑約 6.4 m 是設計決定',
    '外前廊 5 開間、內前廊 4 開間': '參考資料：van Millingen 1912',
    '側堂：四柱十字式、主穹頂 12 開間 12 窗、比例瘦高；前廊樓座上 2 個小穹頂': '參考資料：van Millingen 1912；Wikipedia；TBL',
    '側堂後殿外 7 面、中間三連窗': '參考資料：van Millingen 1912',
    '牆：磚石條紋、退縮磚': '參考資料：van Millingen 1912；Wikipedia 引 Mathews 1976',
    '主堂東端 3 個後殿（今天是 mihrab 室）': '參考資料：TDV、van Millingen（還原）；尺寸是設計決定',
    '各量體的牆高、位置': '設計決定（對照 OSM 外框）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 0.4)
    P = {
        'naos': {'x': [5.0, 17.0], 'y': [9.0, 25.0], 'z': 10.0, 'arm_w': 6.0, 'arm_z': 12.0, 'roof': 'barrel', 'rise': 1.4},
        'domes': [{'cx': 11.0, 'cy': 17.0, 'r': 3.8, 'n': 12, 'z0': 12.8, 'h': 3.6, 'win': 12, 'rise': 3.2, 'ribs': 24, 'cross': True},
                  {'cx': 21.0, 'cy': 22.0, 'r': 1.9, 'n': 12, 'z0': 12.2, 'h': 4.2, 'win': 12, 'rise': 1.6, 'ribs': 12, 'cross': True},   # 側堂（瘦高）
                  {'cx': 19.4, 'cy': 15.0, 'r': 1.2, 'n': 8, 'z0': 9.8, 'h': 2.2, 'win': 4, 'rise': 1.0, 'ribs': 8},                     # 側堂前廊樓座上的兩個小頂
                  {'cx': 22.6, 'cy': 15.0, 'r': 1.2, 'n': 8, 'z0': 9.8, 'h': 2.2, 'win': 4, 'rise': 1.0, 'ribs': 8}],
        'apses': [{'cx': 11.0, 'r': 3.0, 'facets': 5, 'z': 9.0, 'win': 3, 'win_w': 0.8}, {'cx': 6.8, 'r': 1.4, 'facets': 3, 'z': 7.0},
                  {'cx': 15.2, 'r': 1.4, 'facets': 3, 'z': 7.0}, {'cx': 21.0, 'y': 27.0, 'r': 2.5, 'facets': 7, 'z': 9.5, 'win': 3, 'win_w': 0.6}],
        'bays': [{'x': [1.0, 5.0], 'y': [5.0, 25.0], 'z': 7.5, 'roof': 'shed', 'high': '+x', 'rise': 1.0},                       # 北翼迴廊
                 {'x': [17.0, 21.0], 'y': [5.0, 13.0], 'z': 7.5, 'roof': 'shed', 'high': '-x', 'rise': 1.0},                      # 南翼迴廊（西段）
                 {'x': [17.5, 24.5], 'y': [17.0, 27.0], 'z': 10.0, 'roof': 'flat'},                                               # 側堂中殿
                 {'x': [17.5, 24.5], 'y': [13.0, 17.0], 'z': 9.5, 'roof': 'flat'},                                                # 側堂前廊（二層、樓座）
                 {'x': [1.0, 21.0], 'y': [5.0, 9.0], 'z': 8.0, 'roof': 'shed', 'high': '+y', 'rise': 1.0},                       # 內前廊
                 {'x': [1.0, 25.0], 'y': [0.6, 5.0], 'z': 7.0, 'roof': 'shed', 'high': '+y', 'rise': 1.0,                       # 外前廊
                  'arcade_x': [3.4, 7.8, 16.2, 20.6], 'arc_z0': 1.0, 'arc_z1': 5.0, 'arc_w': 2.0}],
        'door': [{'x': 12.0, 'y': 0.6, 'w': 2.0, 'h': 3.4}],
    }
    church.cross_in_square(M, P)
    # 側堂十字臂（四柱十字式的上半）
    M.add(M.box(17.5, 24.5, 20.6, 23.4, 0, 11.5), BANDED, 1)
    M.add(M.barrel(17.5, 24.5, 20.6, 23.4, 11.5, 'x', 0.9), TILE, 2)
    M.add(M.box(19.6, 22.4, 17.0, 27.0, 0, 11.5), BANDED, 1)
    M.add(M.barrel(19.6, 22.4, 17.0, 27.0, 11.5, 'y', 0.9), TILE, 2)
    # 南立面的簷帶（Glabas 的墓誌銘）：側堂南牆頂下一條大理石帶
    M.add(M.box(24.3, 24.7, 13.0, 27.0, 8.6, 9.2), byz.MARBLE, 1)
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=1310)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(12.0, 0.2, 0), 'dome-top': M.cell(11.0, 17.0, 19.4)}
    return G, L, anchors, {}
