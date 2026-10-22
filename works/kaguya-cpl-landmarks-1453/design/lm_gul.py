# 聖狄奧多西婭教堂（Hagia Theodosia／Christ Euergetes，Gül Camii，11 世紀末～12 世紀前半）1453：坐在高大拱頂地下層上的十字形圓頂教堂，三面樓廊、
#   四角各一座無鼓座半球小穹頂；主穹頂坐在開窗的高鼓座上（像 Kalenderhane）；三個大幅外凸的後殿（主後殿七邊、側後殿三邊）；西面拜占庭前廊。
#   1453 年 5 月 28 日（聖人節前夕）教堂掛滿玫瑰花環，君士坦丁十一世在此祈禱 —— 玫瑰清真寺的名字。
#   ⛔ 不做：宣禮塔（Selim II／Murad IV）、Murad IV 重建的低八角主穹頂與尖拱、幾乎整面西牆與十字臂山牆的土耳其重建、外前廊與木門廊、蘇丹包廂、樓廊與前廊切寬的尖拱。
#   研究整理：scratchpad/cpl/research_batch2.md §6；占地：OSM way 330645373（26.1 × 22.4 m、長軸 137°，西北－東南向）。
import byz, church
from byz import BANDED, BRICK, LEAD, TILE

KEY = 'gul'
TITLE = '聖狄奧多西婭教堂 1453（Hagia Theodosia／Christ Euergetes，Gül Camii；高鼓座主穹頂、四角小穹頂）'
TITLE_SHORT = '聖狄奧多西婭教堂 1453'
MPV = 0.2
W, D, H = 22.0, 30.0, 28.0
META = {'kind': 'building', 'use': 'gul', 'style': 'roman', 'lot': '22,30', 'base': 0, 'variant': 'a', 'lamps': 10}
PARTS = (('body', 1, '主體（拱頂地下層、教堂、樓廊、前廊、後殿）'), ('roof', 2, '屋頂（主穹頂、四角小穹頂鋪鉛、拱頂鋪瓦）'))
PROV = {
    '26 × 20 m、坐在高大的拱頂地下層上、三面樓廊、四角圓頂': '參考資料：Wikipedia；van Millingen 1912；Schäfer 1973',
    '四角穹頂半球形、直接坐在帆拱上、沒有肋也沒有鼓座（原設計）': '參考資料：van Millingen 1912',
    '三個後殿大幅外凸：主後殿七邊、側後殿三邊（四層壁龕）': '參考資料：van Millingen 1912；Wikipedia',
    '主穹頂原本是開窗的高鼓座': '參考資料：Wikipedia（類似 Kalenderhane）；十二邊、12 窗、直徑約 7 m 是設計決定',
    '西面前廊寬同教堂、深 4 m、三開間': '設計決定（van Millingen：舊牆基與舊鋪面意味著原本有拜占庭前廊；尺寸查不到）',
    '地下層高 4.5 m、各部高度': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 0.3)
    M.band_z0 = 0.5
    up = 4.5                                                     # 地下層（拱頂）高 ⇒ 教堂地板
    ax = 11.0
    # 地下層：整座教堂（含前廊）底下；四周一圈拱門
    M.add(M.box(1.5, 20.5, 0.0, 23.5, 0, up), BANDED, 1)
    for yy in (3.0, 7.0, 11.0, 15.0, 19.0):
        for xx in (1.5, 20.5):
            M.win(M.arch_open(xx, yy, 0.8, 3.6, 1.6, normal='x', depth=1.6))
    P = {
        'naos': {'x': [1.5, 20.5], 'y': [4.0, 23.5], 'z': up + 10.0, 'arm_w': 8.0, 'arm_z': up + 13.0, 'roof': 'barrel', 'rise': 2.0},
        'domes': [{'cx': ax, 'cy': 13.0, 'r': 4.3, 'n': 12, 'z0': up + 13.4, 'h': 4.0, 'win': 12, 'rise': 3.4, 'ribs': 12, 'cross': True}],
        'apses': [{'cx': ax, 'y': 23.5, 'r': 3.6, 'facets': 4, 'z': up + 9.0, 'win': 3, 'win_w': 0.8, 'win_z0': up + 3.0},
                  {'cx': 4.6, 'y': 23.5, 'r': 1.9, 'facets': 3, 'z': up + 7.8, 'win': 1, 'win_w': 0.5},
                  {'cx': 17.4, 'y': 23.5, 'r': 1.9, 'facets': 3, 'z': up + 7.8, 'win': 1, 'win_w': 0.5}],
        'bays': [{'x': [1.5, 20.5], 'y': [0.0, 4.0], 'z': up + 7.0, 'roof': 'shed', 'high': '+y', 'rise': 1.0,
                  'arcade_x': [5.0, 17.0], 'arc_z0': up + 0.8, 'arc_z1': up + 4.6, 'arc_w': 2.2}],                    # 前廊（三開間）
    }
    church.cross_in_square(M, P)
    # 四角的半球小穹頂（無鼓座、坐在角落格的平頂上）
    for (dx, dy) in ((5.2, 7.6), (16.8, 7.6), (5.2, 19.9), (16.8, 19.9)):
        M.add(M.dome(dx, dy, up + 10.3, 2.1, 2.1, ribs=0), LEAD, 2)
    # 兩側牆：下層（教堂）與樓廊兩排窗
    for yy in (6.5, 10.0, 16.0, 21.0):
        for xx in (1.5, 20.5):
            M.win(M.arch_open(xx, yy, up + 1.2, up + 4.0, 1.0, normal='x', depth=1.8))
            M.win(M.arch_open(xx, yy, up + 6.0, up + 8.6, 0.9, normal='x', depth=1.8))
    M.door(M.arch_open(ax, 0.0, up, up + 3.4, 2.0, normal='y', depth=1.6))
    M.door(M.arch_open(ax, 0.0, 0.0, 2.8, 1.6, normal='y', depth=1.6))                  # 地下層的門
    G, L = M.finish(shell_m=0.8, seed=1120)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(ax, 0.2, up), 'dome-top': M.cell(ax, 13.0, up + 20.8)}
    return G, L, anchors, {'教堂地板（m）': up, '穹頂頂（m）': up + 20.8}
