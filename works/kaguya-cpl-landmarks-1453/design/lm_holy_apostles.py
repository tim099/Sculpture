# 聖使徒教堂（Holy Apostles，查士丁尼 536–550；1461/62 拆、原址蓋法提赫清真寺）1453：希臘十字、五穹頂（四臂各一＋中央）、西臂較長、每臂三廊；
#   944–985 年五穹頂都加開窗鼓座、中央的抬高（Beckwith；Epstein 反對抬高說）；1296 地震中央穹頂塌、後修復。
#   1453：有屋頂但殘破（Gennadios 1456 因此遷往至福聖母修道院）。東端連君士坦丁的圓形陵、北臂末端查士丁尼家族的十字形陵。
#   ⚠ 沒有任何實測：開間（中央 15 m、四周 12.5 m）是一份沒能確認作者的重建提案；全長、全寬、穹頂徑、高、兩座陵的尺寸都是設計決定（威尼斯聖馬可只當比例代理）。
#   研究整理：scratchpad/cpl/research_palaces_cisterns.md §5；位置：法提赫清真寺（OSM relation 1661399）中心、軸線正東西。
import numpy as np
import byz, church
from byz import BANDED, STONE, LEAD, TILE, MARBLE, GOLD

KEY = 'holy-apostles'
TITLE = '聖使徒教堂 1453（Holy Apostles，查士丁尼 536–550；五穹頂、君士坦丁陵）'
TITLE_SHORT = '聖使徒教堂 1453'
MPV = 0.4
W, D, H = 56.0, 112.0, 34.0
META = {'kind': 'building', 'use': 'holy-apostles', 'style': 'roman', 'lot': '56,112', 'base': 0, 'variant': 'a'}
PARTS = (('body', 1, '主體（四臂三廊、前廊、後殿、兩座陵）'), ('roof', 2, '屋頂（五個穹頂、陵的穹頂、坡頂）'), ('atrium', 3, '中庭（柱廊）'))
PROV = {
    '希臘十字、五穹頂、西臂較長、每臂三廊；正廳五門': '參考資料：Procopius、Mesarites、Constantine of Rhodes（經 Wikipedia、de.Wikipedia）',
    '五穹頂都有開窗鼓座、中央較高；中央穹頂有瓣': '參考資料：Beckwith（經 Wikipedia）；Mesarites',
    '開間：中央 15 m、四周 12.5 m': '參考資料：academia.edu 的重建提案摘要（作者未能確認）—— 照它取',
    '臂寬 21.5 m（中跨 12.5＋兩側廊各 4.5）、西臂 17.5 m、牆高、穹頂徑（中央鼓座 15 m、四臂 12 m）、頂高 31 m': '設計決定（威尼斯聖馬可 76.5 × 62.6 m、內高 28.15 m 只當比例）',
    '君士坦丁圓陵（東端，直徑 26 m）、查士丁尼十字陵（北臂末端，臂 10 m）': '參考資料：Wikipedia（位置是通說）；尺寸是設計決定',
    '1453 年殘破：鉛皮斑駁': '參考資料：Gennadios 遷座（van Millingen 1912；Wikipedia）；斑駁的畫法是設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.8, 0.6)
    cx = 33.0                                   # 教堂十字的中線（x：北 → 南）；北邊 0–12 m 留給查士丁尼陵
    yN, yW0, yC0, yC1, yE1 = 30.0, 36.0, 53.5, 68.5, 81.0     # 前廊西牆、西臂起、中央開間、東臂止
    cyc = (yC0 + yC1) / 2
    hw = 21.5 / 2                                # 臂半寬（含側廊）
    bay = 12.5 / 2                               # 臂中跨半寬
    # 四臂（三廊）：側廊 12 m、中跨 17 m 加坡頂；中央開間 20 m
    arms = [(cx - hw, cx + hw, yW0, yC0), (cx - hw, cx + hw, yC1, yE1), (cx - 7.5 - 12.5, cx - 7.5, yC0, yC1), (cx + 7.5, cx + 7.5 + 12.5, yC0, yC1)]
    for (x0, x1, y0, y1) in arms[:2]:
        M.add(M.box(x0, x1, y0, y1, 0, 12.0), BANDED, 1)
        M.add(M.box(cx - bay, cx + bay, y0, y1, 0, 17.0), BANDED, 1)
        M.add(M.shed(x0, cx - bay, y0, y1, 12.0, 13.6, '+x'), TILE, 2)
        M.add(M.shed(cx + bay, x1, y0, y1, 12.0, 13.6, '-x'), TILE, 2)
    for (x0, x1, y0, y1) in arms[2:]:
        M.add(M.box(x0, x1, cyc - hw, cyc + hw, 0, 12.0), BANDED, 1)
        M.add(M.box(x0, x1, cyc - bay, cyc + bay, 0, 17.0), BANDED, 1)
        M.add(M.shed(x0, x1, cyc - hw, cyc - bay, 12.0, 13.6, '+y'), TILE, 2)
        M.add(M.shed(x0, x1, cyc + bay, cyc + hw, 12.0, 13.6, '-y'), TILE, 2)
    M.add(M.box(cx - 7.5, cx + 7.5, yC0, yC1, 0, 19.0), BANDED, 1)
    # 五個穹頂（鼓座＋鉛皮）：四臂各一（中跨中心）、中央一（較高、24 窗、有瓣）
    domes = [(cx, yW0 + 17.5 - bay, 17.0), (cx, yC1 + bay, 17.0), (cx - 7.5 - bay, cyc, 17.0), (cx + 7.5 + bay, cyc, 17.0)]
    for (dx, dy, z0) in domes:
        M.add(M.box(dx - bay, dx + bay, dy - bay, dy + bay, z0 - 0.4, z0), LEAD, 2)
        church._dome(M, {'cx': dx, 'cy': dy, 'r': 6.0, 'n': 16, 'z0': z0, 'h': 2.8, 'win': 16, 'rise': 4.6, 'ribs': 16, 'cross': True}, 2, 1, BANDED)
    M.add(M.box(cx - 7.5, cx + 7.5, yC0, yC1, 18.6, 19.0), LEAD, 2)
    church._dome(M, {'cx': cx, 'cy': cyc, 'r': 7.4, 'n': 24, 'z0': 19.0, 'h': 4.2, 'win': 24, 'rise': 6.2, 'ribs': 24, 'cross': True}, 2, 1, BANDED)
    # 西臂多出來的一跨（沒有穹頂）：屋脊坡頂
    M.add(M.gable(cx - bay, cx + bay, yW0, yW0 + 5.0, 17.0, 2.4, 'y'), TILE, 2)
    # 前廊（五門）、後殿（外 3 面、三窗）
    M.add(M.box(cx - hw, cx + hw, yN, yW0, 0, 11.0), BANDED, 1)
    M.add(M.shed(cx - hw, cx + hw, yN, yW0, 11.0, 12.6, '+y'), TILE, 2)
    for k in range(5):
        xc = cx - hw + (k + 0.5) * 2 * hw / 5
        M.door(M.arch_open(xc, yN, 0, 4.6 if k == 2 else 3.8, 2.4 if k == 2 else 1.8, normal='y', depth=2.0))
        M.win(M.arch_open(xc, yN, 6.4, 9.6, 1.6, normal='y', depth=2.0))
    M.add(M.apse(cx, yE1 - 0.4, 6.6, 3, 0, 13.0), BANDED, 1)
    M.add(M.semidome(cx, yE1 - 0.4, 13.0, 5.8, '+y'), LEAD, 2)
    M.win(M.ring_windows(cx, yE1, 4.6, 7.2, 6.0, 11.0, [60, 90, 120], 1.0))
    # 側廊兩層窗、中跨的高窗（每臂的盡頭三連窗）
    for (x0, x1, y0, y1) in arms[:2]:
        for xx in (x0, x1):
            for yy in np.arange(y0 + 2.5, y1 - 1.0, 3.6):
                M.win(M.arch_open(xx, yy, 2.6, 5.4, 1.2, normal='x', depth=2.4)); M.win(M.arch_open(xx, yy, 7.4, 10.4, 1.2, normal='x', depth=2.4))
    for (x0, x1, y0, y1) in arms[2:]:
        for yy in (cyc - hw, cyc + hw):
            for xx in np.arange(x0 + 2.0, x1 - 1.0, 3.6):
                M.win(M.arch_open(xx, yy, 2.6, 5.4, 1.2, normal='y', depth=2.4)); M.win(M.arch_open(xx, yy, 7.4, 10.4, 1.2, normal='y', depth=2.4))
        xe = x0 if x0 < cx else x1
        for k in (-1, 0, 1):
            M.win(M.arch_open(xe, cyc + k * 2.6, 12.6, 16.0, 1.4, normal='x', depth=2.4))
    # 君士坦丁圓陵（東端，直徑 26 m、牆高 15 m、扁穹頂）
    ry = yE1 + 5.0 + 13.0
    M.add(M.cyl(cx, ry, 13.0, 0, 15.0), BANDED, 1)
    M.add(M.dome(cx, ry, 15.0, 12.6, 5.6, ribs=16), LEAD, 2)
    M.add(M.box(cx - 3.0, cx + 3.0, yE1 + 3.0, ry - 11.0, 0, 9.0), BANDED, 1)          # 連到後殿的過道
    M.add(M.gable(cx - 3.0, cx + 3.0, yE1 + 3.0, ry - 11.0, 9.0, 1.4, 'y'), TILE, 2)
    for a in range(0, 360, 30):
        M.win(M.ring_windows(cx, ry, 11.6, 13.6, 9.0, 12.6, [a + 15], 0.8))
    # 查士丁尼家族的十字形陵（北臂末端，臂 10 m、牆 12 m、中央小穹頂）
    jx, jy = cx - 7.5 - 12.5 - 5.0, cyc
    M.add(M.box(jx - 5.0, jx + 5.0, jy - 2.6, jy + 2.6, 0, 11.0) | M.box(jx - 2.6, jx + 2.6, jy - 5.0, jy + 5.0, 0, 11.0), BANDED, 1)
    M.add(M.gable(jx - 5.0, jx + 5.0, jy - 2.6, jy + 2.6, 11.0, 1.4, 'x') | M.gable(jx - 2.6, jx + 2.6, jy - 5.0, jy + 5.0, 11.0, 1.4, 'y'), TILE, 2)
    church._dome(M, {'cx': jx, 'cy': jy, 'r': 2.8, 'n': 8, 'z0': 12.0, 'h': 2.0, 'win': 8, 'rise': 2.4, 'ribs': 8}, 2, 1, BANDED)
    # 中庭（西）：外牆 7 m、三面柱廊
    A = 3
    for (x0, x1, y0, y1) in ((cx - hw, cx + hw, 0.0, 1.2), (cx - hw, cx - hw + 1.2, 0.0, yN), (cx + hw - 1.2, cx + hw, 0.0, yN)):
        M.add(M.box(x0, x1, y0, y1, 0, 7.0), BANDED, A)
    for (x0, x1, y0, y1, hi) in ((cx - hw + 1.2, cx + hw - 1.2, 1.2, 6.0, '-y'), (cx - hw + 1.2, cx - hw + 6.0, 1.2, yN, '-x'), (cx + hw - 6.0, cx + hw - 1.2, 1.2, yN, '+x')):
        M.add(M.shed(x0, x1, y0, y1, 5.6, 6.8, hi), TILE, A)
    for xx in np.arange(cx - hw + 8.6, cx + hw - 6.0, 3.6):
        M.add(M.box(xx - 0.4, xx + 0.4, 5.6, 6.4, 0, 5.6), MARBLE, A)
    for yy in np.arange(8.6, yN - 1.0, 3.6):
        M.add(M.box(cx - hw + 5.6, cx - hw + 6.4, yy - 0.4, yy + 0.4, 0, 5.6), MARBLE, A)
        M.add(M.box(cx + hw - 6.4, cx + hw - 5.6, yy - 0.4, yy + 0.4, 0, 5.6), MARBLE, A)
    M.door(M.arch_open(cx, 0.0, 0, 4.4, 3.2, normal='y', depth=3.0))
    M.air(M.arch_open(cx, 0.6, 0, 4.4, 3.2, normal='y', depth=1.4))
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=1.2, seed=550)
    # 1453 年殘破：鉛皮斑駁（照位置雜湊把一成的鉛換成接縫的深色）
    zz, yy, xx = np.nonzero(G == byz.COL['lead'])
    h = ((xx.astype(np.int64) // 3 * 2654435761) ^ (yy.astype(np.int64) // 3 * 40503) ^ (zz.astype(np.int64) // 3 * 9973)) % 100
    G[zz[h < 10], yy[h < 10], xx[h < 10]] = byz.COL['lead_seam']
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(cx, 0.4, 0), 'dome-top': M.cell(cx, cyc, 29.4), 'crossing': M.cell(cx, cyc, 0)}
    return G, L, anchors, {'中央穹頂頂（m）': round(19.0 + 4.2 + 6.2, 2), '十字中心離框中心（y，m）': round(cyc - D / 2, 2)}
