# 斯圖狄奧斯修道院（聖約翰教堂，St John of Stoudios，463）1453：三廊巴西利卡（每側 7 根綠斑岩柱、上層再 7 根；北南西三面木構廊台）、前廊三開間（中間外牆 4 柱 in antis）、前庭；
#   拉丁時期屋頂塌、約 1290–93 由 Constantine Palaiologos 重修（新屋頂、宿舍、院地圍牆）⇒ 1453 年有屋頂、使用中（征服時受損）。
#   ⛔ 不做：Bayezid II 改清真寺（İmrahor Camii）後的西山牆 5 窗、較矮的後殿上段、宣禮塔、1782 火災與 1894 地震後的廢墟、現代修復。
#   研究整理：scratchpad/cpl/research_palaces_cisterns.md §6；占地：OSM way 331050716（遺址 32.6 × 20.5 m、軸方位 106.8°）。
import numpy as np
import byz
from byz import BANDED, STONE, MARBLE, TILE, LEAD

KEY = 'stoudios'
TITLE = '斯圖狄奧斯修道院 1453（St John of Stoudios，463；1290 年代重修）'
TITLE_SHORT = '斯圖狄奧斯修道院 1453'
MPV = 0.2
W, D, H = 26.0, 60.0, 20.0
META = {'kind': 'building', 'use': 'stoudios', 'style': 'roman', 'lot': '26,60', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（巴西利卡、前廊、後殿）'), ('roof', 2, '屋頂'), ('atrium', 3, '前庭（柱廊）'),
         ('trees-cypress', 4, '前庭的柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}), ('trees-plane', 5, '前庭中間的懸鈴木（遊戲換成生成式的懸鈴木）', {'kind': 'tree', 'tree': 'plane'}))
PROV = {
    '三廊巴西利卡、每側 7 柱（上層 7）、三面木廊台；南北牆各兩排 8 扇圓頭大窗；中殿屋頂高於側廊': '參考資料：van Millingen 1912 ch.II',
    '前廊三開間、木屋頂、中間外牆 4 柱 in antis 與古典簷部、5 門': '參考資料：van Millingen 1912',
    '後殿內半圓、外 3 面': '參考資料：van Millingen 1912',
    '外廓 33 × 25 m（含前廊、後殿）': '參考資料：OSM way 331050716（遺址 32.6 × 20.5 m）；Encyclopaedia of the Hellenic World（經轉引，未核對）',
    '前庭約 26 × 26 m、三面柱廊': '設計決定（尺寸查無）',
    '牆高（側廊 9.5 m、中殿 15 m）': '設計決定',
    '前庭四角的柏樹、中間的懸鈴木': '設計決定（修道院的庭院常種；斯圖狄奧斯的前庭種什麼查無）'
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 0.5)
    yN, yB, yE = 26.0, 31.0, 56.0                 # 前廊西牆、本體西牆、東牆
    x0, x1 = 0.5, 25.5
    M.add(M.box(x0, x1, yB, yE, 0, 9.5), BANDED, 1)
    M.add(M.shed(x0, 8.5, yB, yE, 9.5, 11.2, '+x'), TILE, 2)
    M.add(M.shed(17.5, x1, yB, yE, 9.5, 11.2, '-x'), TILE, 2)
    M.add(M.box(8.5, 17.5, yB, yE, 0, 15.0), BANDED, 1)
    M.add(M.gable(8.5, 17.5, yB, yE, 15.0, 2.6, 'y'), TILE, 2)
    for xx in (x0, x1):
        for k in range(8):
            yy = yB + 1.8 + k * (yE - yB - 3.0) / 7
            M.win(M.arch_open(xx, yy, 2.2, 4.6, 1.2, normal='x', depth=2.0)); M.win(M.arch_open(xx, yy, 6.0, 8.6, 1.2, normal='x', depth=2.0))
    for xx in (8.5, 17.5):
        for k in range(7):
            M.win(M.arch_open(xx, yB + 2.4 + k * 3.4, 11.2, 13.8, 1.1, normal='x', depth=2.0))
    M.add(M.apse(13.0, yE - 0.2, 4.6, 3, 0, 11.0), BANDED, 1)
    M.add(M.semidome(13.0, yE - 0.2, 11.0, 4.0, '+y'), TILE, 2)
    M.win(M.ring_windows(13.0, yE, 3.0, 5.2, 4.0, 8.6, [60, 90, 120], 0.8))
    # 前廊：三開間、木屋頂；中間開間的外牆是 4 柱 in antis（柱廊）＋簷部
    M.add(M.box(x0, x1, yN, yB, 0, 9.0), BANDED, 1)
    M.add(M.shed(x0, x1, yN, yB, 9.0, 10.4, '+y'), TILE, 2)
    M.air(M.box(8.5, 17.5, yN - 0.5, yN + 1.0, 0, 7.0))
    for xx in (9.6, 12.0, 14.0, 16.4):
        M.add(M.cyl(xx, yN + 0.5, 0.45, 0, 7.0), MARBLE, 1)
    M.add(M.box(8.5, 17.5, yN, yN + 1.0, 7.0, 9.0), MARBLE, 1)
    for xc in (4.5, 21.5):
        M.door(M.arch_open(xc, yN, 0, 3.4, 1.6, normal='y', depth=2.0))
    M.door(M.box(10.5, 15.5, yN + 0.9, yN + 2.4, 0, 4.0))
    # 前庭：外牆 6 m、北南西三面柱廊
    A = 3
    for (a0, a1, b0, b1) in ((x0, x1, 0.0, 1.0), (x0, x0 + 1.0, 0.0, yN), (x1 - 1.0, x1, 0.0, yN)):
        M.add(M.box(a0, a1, b0, b1, 0, 6.0), BANDED, A)
    for (a0, a1, b0, b1, hi) in ((x0 + 1.0, x1 - 1.0, 1.0, 5.0, '-y'), (x0 + 1.0, x0 + 5.0, 1.0, yN, '-x'), (x1 - 5.0, x1 - 1.0, 1.0, yN, '+x')):
        M.add(M.shed(a0, a1, b0, b1, 4.6, 5.8, hi), TILE, A)
    for xx in np.arange(x0 + 7.6, x1 - 5.0, 3.0):
        M.add(M.cyl(xx, 4.6, 0.3, 0, 4.6), MARBLE, A)
    for yy in np.arange(7.6, yN - 1.0, 3.0):
        M.add(M.cyl(x0 + 4.6, yy, 0.3, 0, 4.6), MARBLE, A); M.add(M.cyl(x1 - 4.6, yy, 0.3, 0, 4.6), MARBLE, A)
    for (tx, ty) in ((x0 + 7.0, 7.0), (x1 - 7.0, 7.0), (x0 + 7.0, yN - 3.0), (x1 - 7.0, yN - 3.0)):
        M.tree(tx, ty, 14.0, 2.4, 4)
    M.tree(13.0, 15.0, 18.0, 12.0, 5)
    M.door(M.arch_open(13.0, 0.0, 0, 3.8, 2.6, normal='y', depth=2.4))
    M.air(M.arch_open(13.0, 0.5, 0, 3.8, 2.6, normal='y', depth=1.2))
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=463)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(13.0, 0.2, 0), 'top': M.cell(13.0, 43.0, 17.4)}
    return G, L, anchors, {}
