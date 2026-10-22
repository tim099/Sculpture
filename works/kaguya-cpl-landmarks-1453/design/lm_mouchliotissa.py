# 蒙古人聖母院（Panagia Mouchliotissa，St. Mary of the Mongols，Kanlı Kilise）1453：城裡唯一的圓頂四葉形（tetraconch）——
#   中央方塊四面各一個半圓殿（外五邊、半穹頂），中央塔狀高鼓座（外圓、八格開窗）；西面三開間前廊（中間筒拱、兩側無鼓座低穹頂）。
#   Maria Palaiologina 1281 年後整修成女修院；1453 年 5 月 29 日最後的抵抗在這裡（血之教堂）。從沒改成清真寺。
#   ⛔ 不做：南側三走道交叉拱大廳（18 世紀，取代了南半圓殿）、西側擴建、鄂圖曼外前廊、尖拱、1892 年的小鐘樓、旁邊 1881 年的希臘學校、高圍牆。
#   補回：南半圓殿（跟北半圓殿對稱）、前廊南端一開間與它的低穹頂。沒做：女修院房舍（配置查不到）。
#   研究整理：scratchpad/cpl/research_batch2.md §5；占地：OSM way 261825033（17.3 × 19.1 m 含南側擴建、教堂軸約 106°）。
import math
import byz, church
from byz import BANDED, LEAD, TILE

KEY = 'mouchliotissa'
TITLE = '蒙古人聖母院 1453（Panagia Mouchliotissa，St. Mary of the Mongols；四葉形）'
TITLE_SHORT = '蒙古人聖母院 1453'
MPV = 0.2
W, D, H = 16.0, 17.0, 17.0
META = {'kind': 'building', 'use': 'mouchliotissa', 'style': 'roman', 'lot': '16,17', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（中央方塊、四個半圓殿、前廊、塔狀鼓座）'), ('roof', 2, '屋頂（穹頂、半穹頂鋪鉛）'))
PROV = {
    '圓頂四葉形、原始 12 × 12 m': '參考資料：van Millingen 1912；Wikipedia；TBL（引 Bouras）',
    '鼓座八格、每格開窗、外圓、平簷；半穹頂與後殿外五邊': '參考資料：van Millingen 1912',
    '中央圓頂被塔狀結構包住（高起的鼓座）': '參考資料：Wikipedia',
    '前廊三開間：中間筒拱、兩側無鼓座低穹頂（原本兩座、今存一座）': '參考資料：van Millingen 1912；TBL',
    '南半圓殿、前廊南端一開間': '設計決定（照北半圓殿、北端對稱補回；被 18 世紀南側大廳取代）',
    '中央方塊 5.4 m、各部高度': '設計決定（圓頂直徑與高度查不到）',
    '磚石帶狀砌、穹頂鋪鉛': '設計決定（TBL：窗、簷口、屋頂的原貌一無所知）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.9, 0.25)
    M.band_z0 = 0.5
    cx, cy, s = 8.0, 10.6, 2.7                                   # 中央方塊中心、半邊
    za, r = 7.2, 3.1                                             # 半圓殿簷口、外接圓半徑
    M.add(M.box(cx - s, cx + s, cy - s, cy + s, 0, 10.6), BANDED, 1)          # 中央方塊（四角墩＋上面的塔狀鼓座座）
    rr = r * math.cos(math.pi / 10)
    for tow in ('+x', '-x'):
        x0 = cx + s if tow == '+x' else cx - s
        M.add(M.apse_x(x0, cy, r, 5, 0, za, tow), BANDED, 1)
        M.add(M.semidome(x0, cy, za, rr * 0.97, tow), LEAD, 2)
        a0 = 0 if tow == '+x' else 180
        M.win(M.ring_windows(x0, cy, rr - 1.4, r + 0.6, za - 4.0, za - 1.0, [a0 - 36, a0, a0 + 36], 0.35))
    M.add(M.apse(cx, cy + s, r, 5, 0, za, '+y'), BANDED, 1)
    M.add(M.semidome(cx, cy + s, za, rr * 0.97, '+y'), LEAD, 2)
    M.win(M.ring_windows(cx, cy + s, rr - 1.4, r + 0.6, za - 4.0, za - 1.0, [54, 90, 126], 0.35))
    M.add(M.apse(cx, cy - s, r, 5, 0, za, '-y'), BANDED, 1)                    # 西半圓殿（前廊後面）
    M.add(M.semidome(cx, cy - s, za, rr * 0.97, '-y'), LEAD, 2)
    # 塔狀鼓座（外圓、八格開窗、平簷）＋穹頂
    M.add(M.cyl(cx, cy, 2.75, 10.6, 13.6), BANDED, 1)
    M.add(M.cyl(cx, cy, 2.95, 13.4, 13.7), BANDED, 1)
    M.add(M.dome(cx, cy, 13.7, 2.75, 2.1, ribs=8), LEAD, 2)
    M.win(M.ring_windows(cx, cy, 1.6, 3.4, 11.3, 13.1, [22.5 + 45 * k for k in range(8)], 0.4))
    t = max(0.15, M.mpv * 0.51)
    M.add(M.box(cx - t, cx + t, cy - t, cy + t, 15.6, 16.8), byz.GOLD, 2)
    M.add(M.box(cx - t, cx + t, cy - 0.5, cy + 0.5, 16.2, 16.2 + max(0.3, M.mpv)), byz.GOLD, 2)
    # 中央方塊四角上面的平頂（瓦）
    M.add(M.box(cx - s, cx + s, cy - s, cy + s, 10.6, 10.9), TILE, 2)
    # 前廊（三開間）：y 0.6～4.6、寬 12 m；中間筒拱、兩側無鼓座低穹頂
    x0, x1, y0, y1, zn = 2.0, 14.0, 0.6, 5.2, 6.0
    M.add(M.box(x0, x1, y0, y1, 0, zn), BANDED, 1)
    M.add(M.barrel(6.0, 10.0, y0, y1, zn, 'y', 1.1), TILE, 2)
    for dx in (4.0, 12.0):
        M.add(M.box(dx - 2.0, dx + 2.0, y0, y1, zn, zn + 0.3), TILE, 2)
        M.add(M.dome(dx, (y0 + y1) / 2, zn + 0.3, 1.7, 1.3, ribs=0), LEAD, 2)
    M.door(M.arch_open(8.0, y0, 0, 2.7, 1.4, normal='y', depth=1.6))
    for dx in (4.0, 12.0):
        M.win(M.arch_open(dx, y0, 1.6, 4.0, 1.0, normal='y', depth=1.6))
    G, L = M.finish(shell_m=0.8, seed=1281)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(8.0, y0 + 0.2, 0), 'dome-top': M.cell(cx, cy, 15.8)}
    return G, L, anchors, {'穹頂頂（m）': 15.8}
