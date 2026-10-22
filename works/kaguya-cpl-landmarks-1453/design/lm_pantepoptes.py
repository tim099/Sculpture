# 全視者基督修道院教堂（Christ Pantepoptes，Eski İmaret Camii，約 1087 Anna Dalassene）1453：四柱十字形、三分式聖所、內前廊（上有樓廊）＋巴列奧略時期的外前廊（中間低穹頂、不開窗）；
#   主穹頂：鼓座內圓外十二邊、12 扇圓頭窗；凹磚法（灰漿帶比磚厚）。
#   ⛔ 不做：西南角的宣禮塔、鄂圖曼的平屋頂與頭盔頂（今天已修回）、son cemaat yeri；南北兩條外側廊巴列奧略時期就拆了 ⇒ 不做。
#   沒做：東北方的修士宿舍（史料只有「大型基座」、尺寸查不到）。
#   研究整理：scratchpad/cpl/research_batch2.md §3；占地：OSM way 525963959（20.8 × 13.3 m、教堂軸 99°）。
import byz, church
from byz import BANDED, LEAD, TILE

KEY = 'pantepoptes'
TITLE = '全視者基督修道院教堂 1453（Christ Pantepoptes，約 1087）'
TITLE_SHORT = '全視者基督教堂 1453'
MPV = 0.2
W, D, H = 14.0, 21.0, 18.0
META = {'kind': 'building', 'use': 'pantepoptes', 'style': 'roman', 'lot': '14,21', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（中殿、聖所、側室、內外前廊、後殿）'), ('roof', 2, '屋頂（穹頂鋪鉛、拱頂鋪瓦）'))
PROV = {
    '中殿 9.20 × 10.55 m、聖所往東 5.40 m': '參考資料：Ousterhout 1991–92（轉引）；TBL',
    '鼓座內圓外十二邊、12 扇圓頭窗、穹面 12 格': '參考資料：van Millingen 1912；Wikipedia；TDV',
    '外前廊三開間、中間低穹頂不開窗、對外只有中間一道門': '參考資料：van Millingen 1912；TBL；Wikipedia',
    '東端側室苜蓿葉形、側後殿低': '參考資料：Wikipedia；TBL',
    '凹磚法': '參考資料：Wikipedia；TDV',
    '主穹頂直徑 4.6 m、各部高度': '設計決定（查不到）',
    '穹頂鋪鉛、拱頂鋪瓦': '設計決定（今天的瓦頂是 1970 年修復；1453 年是瓦是鉛查不到）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.2, 0.3)
    M.band_z0 = 0.4
    P = {
        'naos': {'x': [1.725, 12.275], 'y': [6.2, 15.4], 'z': 8.4, 'arm_w': 4.6, 'arm_z': 10.6, 'roof': 'barrel', 'rise': 1.3},
        'domes': [{'cx': 7.0, 'cy': 10.8, 'r': 2.9, 'n': 12, 'z0': 11.0, 'h': 3.2, 'win': 12, 'rise': 2.3, 'ribs': 12, 'cross': True}],
        'apses': [{'cx': 7.0, 'y': 18.4, 'r': 2.4, 'facets': 3, 'z': 8.0, 'win': 3, 'win_w': 0.7},
                  {'cx': 2.65, 'y': 17.6, 'r': 0.95, 'facets': 3, 'z': 5.4}, {'cx': 11.35, 'y': 17.6, 'r': 0.95, 'facets': 3, 'z': 5.4}],
        'bays': [{'x': [3.6, 10.4], 'y': [15.4, 18.4], 'z': 9.0, 'roof': 'barrel', 'axis': 'y', 'rise': 1.0},                       # 聖所
                 {'x': [1.725, 3.6], 'y': [15.4, 17.6], 'z': 6.2, 'roof': 'shed', 'high': '+x', 'rise': 0.7},                        # 北側室（prothesis）
                 {'x': [10.4, 12.275], 'y': [15.4, 17.6], 'z': 6.2, 'roof': 'shed', 'high': '-x', 'rise': 0.7},                      # 南側室（diakonikon）
                 {'x': [1.725, 12.275], 'y': [3.2, 6.2], 'z': 9.2, 'roof': 'shed', 'high': '+y', 'rise': 0.8},                       # 內前廊（上有樓廊）
                 {'x': [1.3, 12.7], 'y': [0.0, 3.2], 'z': 6.0, 'roof': 'shed', 'high': '+y', 'rise': 0.8, 'domes': [
                     {'cx': 7.0, 'cy': 1.6, 'r': 1.55, 'n': 8, 'z0': 6.5, 'h': 0.7, 'win': 0, 'rise': 1.1}],
                  'arcade_x': [3.3, 10.7], 'arc_z0': 1.4, 'arc_z1': 4.6, 'arc_w': 1.5}],                                            # 外前廊
        'door': [{'x': 7.0, 'w': 1.6, 'h': 3.0}],
    }
    church.cross_in_square(M, P)
    # 樓廊的三聯窗（內前廊上層，從外前廊屋頂上看得到）、內前廊南北兩端的窗
    for k in (-1, 0, 1):
        M.win(M.arch_open(7.0 + k * 1.1, 3.2, 7.2, 8.7, 0.7, normal='y', depth=1.6))
    for xx in (1.725, 12.275):
        M.win(M.arch_open(xx, 4.7, 2.0, 4.4, 0.8, normal='x', depth=2.0))
        M.win(M.arch_open(xx, 4.7, 6.2, 8.2, 0.7, normal='x', depth=2.0))
    G, L = M.finish(shell_m=0.8, seed=1087)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(7.0, 0.2, 0), 'dome-top': M.cell(7.0, 10.8, 16.5)}
    return G, L, anchors, {'穹頂頂（m）': 16.5}
