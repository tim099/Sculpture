# 狄奧多西廣場（Forum of Theodosius／Forum Tauri，393）1453：狄奧多西紀念柱還立著（頂上的像 480 年震落、之後沒有）、
#   西凱旋門 558 年後已不跨街，殘骸散在 Mese 兩旁（Madden：「當時如此、今日亦然」）；Gilles 引老居民：廣場與柱都在、長滿野樹、是賊窩。
#   柱照「形制與阿卡狄烏斯柱相同」（Cedrenus，經 Gilles）⇒ 數字照 lm_column_arcadius.py；1203 年的大火沒燒到這裡。
#   ⛔ 不做：Eski Saray（1455–58）、Bayezid 清真寺與浴場（1500–07；柱子約 1504 年為蓋浴場拆掉）、Beyazıt 廣場、大學門樓、Basilica Theodosiana（約 462 已燒毀）。
#   研究整理：scratchpad/cpl/research_batch3.md §2；拱門殘件 OSM node 12766787301（41.009447, 28.962221）、柱的位置是推測（浴場東南角附近 41.00975, 28.96175）。
import math
import random
import byz, columns
from byz import MARBLE, STONE, BANDED, SOIL

KEY = 'forum-tauri'
TITLE = '狄奧多西廣場 1453（Forum Tauri：狄奧多西紀念柱、凱旋門殘骸、野樹）'
TITLE_SHORT = '狄奧多西廣場 1453'
MPV = 0.2
W, D, H = 64.0, 50.0, 47.0
META = {'kind': 'building', 'use': 'forum-tauri', 'style': 'roman', 'lot': '64,50', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('column', 1, '狄奧多西紀念柱（台階、基座、螺旋浮雕柱身、空的柱頂）'), ('ruins', 2, '凱旋門殘墩、倒下的柱段、碎石、荒地'),
         ('trees-wild', 3, '野樹（遊戲換成生成式的闊葉樹）', {'kind': 'tree', 'tree': 'broadleaf'}))
PROV = {
    '狄奧多西柱：386 年起建、滿刻浮雕、內有螺旋梯；高 40–50 m；形制同阿卡狄烏斯柱': '參考資料：Columbia IDP（引 Konstantinos of Rhodes）；TAN；Gyllius III.6（引 Cedrenus）',
    '柱頂的像 480 年震落、512 年後沒有像；1204 年 Mourtzouphlos 從柱頂被推下（頂上可站人）': '參考資料：TAN；Madden 1991–92',
    '約 1504 年 Bayezid 為蓋浴場拆柱 ⇒ 1453 年還立著': '參考資料：Gyllius III.6；Madden',
    '凱旋門三開間：中跨 7.2 m、側跨各 3.6 m、四墩各 4 根柱（淚滴紋）；558 年後不跨街、殘骸散落': '參考資料：Naumann 1976（經 Columbia IDP）；Madden',
    '廣場長滿野樹、是賊窩（Mehmed 把地送給來蓋房的人）': '參考資料：Gyllius III.6（引老居民）',
    '柱的位置、殘墩的高、碎石與樹的位置；廣場的範圍（三說差很大）取 64 × 50 m': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.6, 1.0)
    rnd = random.Random(393)
    # 模型：rot 94 ⇒ +x 往東（沿 Mese）、+y 往北；拱門殘件在 (54, 11.5)、柱在西 39.6 m、北 32.5 m（研究推的是北 33.5 m；框只到 50 m）
    ax, ay = 54.0, 11.5
    cx, cy = ax - 39.6, ay + 32.5
    # ── 狄奧多西柱（同阿卡狄烏斯柱的數字；頂上空的）──
    C = {'steps': [[9.6, 0.67], [8.6, 0.67], [7.6, 0.66]], 'pedestal': {'w': 6.5, 'h': 8.0, 'mat': MARBLE, 'cornice': 0.25}, 'base': {'d': 4.6, 'h': 1.2},
         'shaft': {'d0': 4.1, 'd1': 3.8, 'h': 30.72, 'mat': MARBLE, 'spiral': {'turns': 13, 'band': 0.4, 'depth': 0.2}},
         'capital': {'w': 4.6, 'h': 1.7, 'mat': MARBLE}}
    z_shaft0 = 2.0 + 8.0 + 1.2
    ztop = columns.column(M, cx, cy, C, lay=1)
    for k in range(4):
        z0 = 2.0 + 0.8 + k * 1.75
        M.add(M.box(cx - 3.35, cx + 3.35, cy - 3.35, cy + 3.35, z0, z0 + 0.4) & ~M.box(cx - 3.2, cx + 3.2, cy - 3.2, cy + 3.2, 0, 99), MARBLE, 1)
    M.door(M.arch_open(cx, cy - 3.25, 2.0, 2.0 + 1.9, 1.14, normal='y', depth=1.0))
    for k in range(56):
        zw = z_shaft0 + 1.0 + k * (30.72 - 2.0) / 56
        r = 2.05 - 0.15 * (zw - z_shaft0) / 30.72
        M.win(M.ring_windows(cx, cy, r - 0.8, r + 0.5, zw, zw + 0.6, [k * 97.0 + 40.0], 0.12))
    M.add(M.box(cx - 2.0, cx + 2.0, cy - 2.0, cy + 2.0, ztop, ztop + 0.8), MARBLE, 1)                 # 空的柱頂平台＋欄杆（頂上可站人）
    M.add(M.box(cx - 2.0, cx + 2.0, cy - 2.0, cy + 2.0, ztop + 0.8, ztop + 1.8) & ~M.box(cx - 1.6, cx + 1.6, cy - 1.6, cy + 1.6, 0, 99), MARBLE, 1)
    # ── 凱旋門殘墩：四墩沿 y（拱跨 Mese），中跨 7.2、側跨 3.6、墩 1.8；中間那一跨就是今天的路 ⇒ 不擺碎石 ──
    R = 2
    ys, y = [], ay - (4 * 1.8 + 7.2 + 2 * 3.6) / 2
    for span in (3.6, 7.2, 3.6, None):
        ys.append(y); y += 1.8 + (span or 0)
    for k, y0 in enumerate(ys):
        h = (3.8, 1.6, 2.4, 4.6)[k]
        M.add(M.box(ax - 2.6, ax + 2.6, y0, y0 + 1.8, 0, 0.8), MARBLE, R)                              # 墩基
        M.add(M.box(ax - 2.2, ax + 2.2, y0 + 0.1, y0 + 1.7, 0.8, h), BANDED, R)
        for dx in (-1.6, 1.6):                                                                       # 墩前後各兩根柱（斷在不同高）
            hh = h + (1.4 if (k + (dx > 0)) % 2 else -0.6)
            M.add(M.cyl(ax + dx, y0 + 0.9, 0.55, 0.8, max(1.4, hh)), MARBLE, R)
    for k in range(9):                                                                               # 倒下的柱段：躺在拱門北邊（遠離路）
        x0 = ax - 10.0 + rnd.random() * 16.0
        y0 = ay + 13.0 + rnd.random() * 8.0
        L_ = 1.6 + rnd.random() * 2.6
        if k % 2:
            M.add(((M.Y - y0) ** 2 + (M.Z - 0.55) ** 2 < 0.55 ** 2) & (M.X >= x0) & (M.X < x0 + L_), MARBLE, R)
        else:
            M.add(((M.X - x0) ** 2 + (M.Z - 0.55) ** 2 < 0.55 ** 2) & (M.Y >= y0) & (M.Y < y0 + L_), MARBLE, R)
    for k in range(26):                                                                              # 碎石、拱石塊
        x0 = 4.0 + rnd.random() * 56.0
        y0 = 22.0 + rnd.random() * 26.0
        if math.hypot(x0 - cx, y0 - cy) < 7.0: continue
        s = 0.5 + rnd.random() * 1.3
        M.add(M.dome(x0, y0, 0.0, s, s * 0.5), STONE if k % 3 else MARBLE, R)
    # 荒地：零碎的土塊（廣場的大理石板只剩一角）
    M.add(M.box(cx - 9.0, cx + 9.0, cy - 9.0, cy + 9.0, 0, 0.2) & ~M.box(cx - 4.8, cx + 4.8, cy - 4.8, cy + 4.8, 0, 9), MARBLE, R)
    M.add(M.box(0, W, 0, D, 0, 0.2), byz.GREEN, R, over=False)                                            # 其他地方是荒地的草（不然遊戲的石基頂是一片灰）
    # ── 野樹 ──
    for (tx, ty, th, tw) in ((28.0, 30.0, 9.0, 7.0), (34.0, 44.0, 11.0, 8.0), (46.0, 36.0, 8.0, 6.0), (58.0, 44.0, 10.0, 7.0),
                             (4.0, 30.0, 7.0, 5.0), (24.0, 46.0, 6.0, 4.6), (62.0, 28.0, 7.0, 5.0), (40.0, 26.0, 6.0, 4.0)):
        M.tree(tx, ty, th, tw, 3)
    G, L = M.finish(shell_m=0.8, seed=393, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'top': M.cell(cx, cy, ztop + 1.6)}
    return G, L, anchors, {'柱頭頂（m）': round(ztop, 2), '柱頂欄杆（m）': round(ztop + 1.8, 2)}
