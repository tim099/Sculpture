# 米雷萊昂教堂（Myrelaion，Bodrum Camii，約 920 年 Romanos I Lekapenos）1453：十字四柱、方邊約 9 m；蓋在同平面的下層教堂（兼小蓄水池）上 ⇒ 從街面看是兩層高；
#   全磚造、外牆半圓柱扶壁（南 6、西門兩側 2、東 2 個半）；8 瓣南瓜頂隔瓣開窗（4 窗）；3 個外 3 面的後殿；前廊 3 開間（中間穹頂）＋外前廊。
#   ⛔ 不做：約 1500 年 Mesih Paşa 改寺時的石造宣禮塔、鄂圖曼木門廊（還原成外前廊）、以墩代柱、1784 年火災後重建的屋頂與北牆。
#   研究整理：scratchpad/cpl/research_columns_churches.md §B7；占地：OSM way 198768798（17.1 × 11.3 m、軸方位 95.2°）。
import byz, church
from byz import BRICK, STONE, LEAD, TILE

KEY = 'myrelaion'
TITLE = '米雷萊昂教堂 1453（Myrelaion，Romanos I Lekapenos 的修道院教堂，約 920）'
TITLE_SHORT = '米雷萊昂教堂 1453'
MPV = 0.2
W, D, H = 12.0, 18.0, 20.0
META = {'kind': 'building', 'use': 'myrelaion', 'style': 'roman', 'lot': '12,18', 'base': 0, 'variant': 'a'}
PARTS = (('body', 1, '主體（下層、上層教堂、前廊、扶壁、後殿）'), ('roof', 2, '屋頂（南瓜頂、瓦）'))
PROV = {
    '方邊約 9 m、連前廊約 10 × 17 m': '參考資料：Wikipedia 引 Krautheimer 1986 p.403；TBL',
    '8 凹瓣南瓜頂、隔瓣開窗（4 窗）': '參考資料：van Millingen 1912；TBL；直徑 4.5 m 是設計決定',
    '3 個後殿、各外 3 面': '參考資料：van Millingen 1912；Wikipedia',
    '半圓柱扶壁：南 6、西門兩側各 1、東 2（半個）': '參考資料：van Millingen 1912（實測）；北面照南面（1784 年後重建的北牆不算）',
    '全磚造': '參考資料：Wikipedia；TBL（1964–65 年修復換了約 90% 的磚）',
    '下層教堂高 5 m、外前廊深 3 m': '設計決定（下層同平面、外前廊後來被木門廊取代）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 0.0)
    up = 5.0                                     # 下層教堂（台基）高
    P = {
        'naos': {'x': [1.3, 10.7], 'y': [6.5, 15.9], 'z': up + 7.0, 'arm_w': 3.4, 'arm_z': up + 8.8, 'roof': 'barrel', 'rise': 1.0},
        'domes': [{'cx': 6.0, 'cy': 11.2, 'r': 2.6, 'n': 8, 'z0': up + 9.3, 'h': 2.2, 'win': 4, 'rise': 1.9, 'ribs': 8, 'cross': True}],
        'apses': [{'cx': 6.0, 'r': 1.8, 'facets': 3, 'z': up + 6.0, 'win': 1, 'win_w': 0.6}, {'cx': 2.9, 'r': 0.95, 'facets': 3, 'z': up + 4.8},
                  {'cx': 9.1, 'r': 0.95, 'facets': 3, 'z': up + 4.8}],
        'bays': [{'x': [1.3, 10.7], 'y': [3.0, 6.5], 'z': up + 6.0, 'roof': 'shed', 'high': '+y', 'rise': 0.8, 'domes': [
                     {'cx': 6.0, 'cy': 4.75, 'r': 1.3, 'n': 8, 'z0': up + 6.6, 'h': 1.0, 'win': 0, 'rise': 1.0}]},
                 {'x': [1.3, 10.7], 'y': [0.0, 3.0], 'z': up + 4.5, 'roof': 'shed', 'high': '+y', 'rise': 0.7,
                  'arcade_x': [2.8, 9.2], 'arc_z0': up + 0.8, 'arc_z1': up + 3.6, 'arc_w': 1.6}],
    }
    church.cross_in_square(M, P)
    # 下層：同平面的台基（下層教堂），小窗；外前廊的門在上層（階梯沒做）
    M.add(M.box(1.3, 10.7, 0.0, 15.9, 0, up), BRICK, 1)
    for xx in (1.3, 10.7):
        for yy in (8.5, 13.5):
            M.win(M.arch_open(xx, yy, 1.8, 3.4, 0.7, normal='x', depth=1.6))
    M.door(M.arch_open(6.0, 0.0, up, up + 2.6, 1.4, normal='y', depth=1.2))
    M.door(M.arch_open(6.0, 0.0, 0.0, 2.4, 1.2, normal='y', depth=1.2))
    # 半圓柱扶壁（從地面到上層簷口）
    zt = up + 6.6
    for yy in (4.0, 6.4, 8.6, 10.8, 13.0, 15.2):
        M.add(M.cyl(10.7, yy, 0.55, 0, zt), BRICK, 1)
        M.add(M.cyl(1.3, yy, 0.55, 0, zt), BRICK, 1)
    for xx in (4.4, 7.6):
        M.add(M.cyl(xx, 0.55, 0.55, 0, up + 4.2), BRICK, 1)
    for xx in (1.3, 10.7):
        M.add(M.cyl(xx, 15.9, 0.55, 0, zt), BRICK, 1)
    G, L = M.finish(shell_m=0.8, seed=920)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(6.0, 0.2, up), 'dome-top': M.cell(6.0, 11.2, up + 13.3)}
    return G, L, anchors, {'上層地板（m）': up}
