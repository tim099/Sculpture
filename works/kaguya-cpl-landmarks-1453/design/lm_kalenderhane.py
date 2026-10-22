# 主座聖母教堂（Kalenderhane；Theotokos Kyriotissa）1453：十字形平面、四臂深筒拱、16 邊 16 窗 16 肋的穹頂；北南側廊、上層樓座、東端後殿 1453 年都還在（後來拆）；
#   內前廊（筒拱中跨夾兩個交叉拱）＋外前廊（長條筒拱，很晚才加）。緊貼瓦倫斯引水渠最東段的南側。
#   ⛔ 不做：宣禮塔、1746 年的 medrese 與 mahfil。要補回的：側廊（19 世紀拆）、樓座（1854 拆）、後殿（鄂圖曼拆）。
#   研究整理：scratchpad/cpl/research_columns_churches.md §B8；占地：OSM way 110314231（31.3 × 19.6 m、軸方位 101.2°）。
import byz, church
from byz import BANDED, STONE, LEAD, TILE

KEY = 'kalenderhane'
TITLE = '主座聖母教堂 1453（Theotokos Kyriotissa，Kalenderhane；12 世紀末）'
TITLE_SHORT = '主座聖母教堂 1453'
MPV = 0.2
W, D, H = 20.0, 32.0, 25.0
META = {'kind': 'building', 'use': 'kalenderhane', 'style': 'roman', 'lot': '20,32', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（十字臂、側廊與樓座、前廊、後殿）'), ('roof', 2, '屋頂（16 邊穹頂、筒拱屋面）'))
PROV = {
    '十字形平面、四臂覆深筒形拱頂': '參考資料：Wikipedia',
    '穹頂 16 邊、16 窗、16 肋；直徑 > 7 m；鋪鉛': '參考資料：van Millingen 1912；Wikipedia 引 Ousterhout 2008a；TDV（修復時照中拜占庭樣式重建、鋪鉛）—— 原真性存疑，照現狀',
    '內前廊、外前廊（長條筒拱）': '參考資料：van Millingen 1912；Wikipedia',
    '側廊寬 3.5 m、後殿內半圓外 3 面': '設計決定（研究建議；1453 年有、後來拆）',
    '牆：中拜占庭期磚石交替': '參考資料：Wikipedia',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 0.5)
    P = {
        'naos': {'x': [3.5, 16.5], 'y': [9.0, 27.0], 'z': 10.5, 'arm_w': 7.0, 'arm_z': 14.0, 'roof': 'barrel', 'rise': 2.4, 'roof_mat': LEAD},
        'domes': [{'cx': 10.0, 'cy': 18.0, 'r': 4.6, 'n': 16, 'z0': 15.6, 'h': 3.6, 'win': 16, 'rise': 3.9, 'ribs': 16, 'cross': True}],
        'apses': [{'cx': 10.0, 'r': 3.6, 'facets': 3, 'z': 11.0, 'win': 3, 'win_w': 0.9}],
        'bays': [{'x': [0.0, 3.5], 'y': [9.0, 26.0], 'z': 9.0, 'roof': 'shed', 'high': '+x', 'rise': 1.0},                 # 北側廊（上層樓座）
                 {'x': [16.5, 20.0], 'y': [9.0, 26.0], 'z': 9.0, 'roof': 'shed', 'high': '-x', 'rise': 1.0},               # 南側廊
                 {'x': [0.0, 20.0], 'y': [4.0, 9.0], 'z': 11.0, 'roof': 'barrel', 'axis': 'x', 'rise': 1.6, 'roof_mat': LEAD},   # 內前廊
                 {'x': [0.0, 20.0], 'y': [0.0, 4.0], 'z': 8.0, 'roof': 'barrel', 'axis': 'x', 'rise': 1.4, 'roof_mat': LEAD,    # 外前廊
                  'arcade_x': [3.0, 6.5, 13.5, 17.0], 'arc_z0': 1.0, 'arc_z1': 5.2, 'arc_w': 2.0}],
        'door': [{'x': 10.0, 'y': 0.0, 'w': 2.2, 'h': 3.8}],
    }
    church.cross_in_square(M, P)
    for xx in (0.0, 20.0):                       # 側廊兩層窗
        for yy in (12.0, 16.0, 20.0, 24.0):
            M.win(M.arch_open(xx, yy, 2.0, 4.2, 1.0, normal='x', depth=2.4))
            M.win(M.arch_open(xx, yy, 5.8, 7.8, 1.0, normal='x', depth=2.4))
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=1197)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(10.0, 0.2, 0), 'dome-top': M.cell(10.0, 18.0, 22.8)}
    return G, L, anchors, {}
