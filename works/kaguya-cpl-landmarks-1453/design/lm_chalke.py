# Chalke 門（大皇宮的正門，奧古斯都廣場東南角）與基督 Chalkites 小堂 1453 ——
#   Chalke 本體：Justinian 重建（矩形、四個附牆墩、中央穹頂）；1200 年以後沒有紀錄（Isaac II 拆了它的銅門）⇒ 1453 年只剩四個墩基、斷牆、門檻的大理石板；
#   Chalkites 小堂：John Tzimiskes 建、存到 1804 ⇒ 1453 年還在：一座十字形的小穹頂堂（10 × 8 m）、後殿朝東（模型 +x）、門朝西。
#   ⚠ 墩基的位置與大小、小堂的形制與大小都是設計決定（研究推的小堂位置 41.0074, 28.9795 ＝ 模型 37, 10.5）。
#   ⛔ 不做：Chalke 的銅門、穹頂、馬賽克（早就沒了）；1453 年後的建築。
#   研究整理：scratchpad/cpl/research_batch3.md §4（c）。
import random
import byz, ruins
from byz import BANDED, STONE, MARBLE, TILE, LEAD, GOLD

KEY = 'chalke'
TITLE = 'Chalke 門的墩基與基督 Chalkites 小堂 1453'
TITLE_SHORT = 'Chalke 與 Chalkites 小堂 1453'
MPV = 0.2
W, D, H = 48.0, 28.0, 16.0
META = {'kind': 'building', 'use': 'chalke', 'style': 'roman', 'lot': '48,28', 'base': 0, 'variant': 'a'}
PARTS = (('chapel', 1, '基督 Chalkites 小堂'), ('roof', 2, '小堂的屋頂與穹頂'), ('ruins', 3, 'Chalke 門的墩基、斷牆、門檻'), ('ground', 4, '地面（草、石板）'),
         ('trees-cypress', 5, '柏樹（遊戲換成生成式的柏樹）', {'kind': 'tree', 'tree': 'cypress'}))
PROV = {
    'Chalke 在奧古斯都廣場東南角；Justinian 重建：矩形、四個附牆墩、中央穹頂': '參考資料：Wikipedia（Chalke Gate）；The Byzantine Legacy（Great Palace）',
    'Chalke 本體 1200 年後沒有紀錄（Isaac II 拆其銅門）；Chalkites 小堂存到 1804': '參考資料：The Byzantine Legacy（推估）',
    '小堂在聖索菲亞東南角之南': '參考資料：The Byzantine Legacy（推估）',
    '墩基的位置大小、小堂的形制與大小、柏樹': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.4)
    M.band_z0 = 1.0
    rnd = random.Random(976)
    C, R, RU, G1 = 1, 2, 3, 4
    M.add(M.box(0, W, 0, D, 0, MPV), byz.GREEN, G1)
    # ── Chalke：四個墩基（3 × 3 m，斷在不同高度）、連著的斷牆、門檻的大理石板、碎石 ──
    for (px, py, h) in ((5.5, 9.5, 2.6), (18.5, 9.5, 1.2), (5.5, 18.5, 3.4), (18.5, 18.5, 0.8)):
        M.add(M.box(px - 1.5, px + 1.5, py - 1.5, py + 1.5, 0, h), STONE, RU)
        M.add(M.box(px - 1.7, px + 1.7, py - 1.7, py + 1.7, 0, 0.4), MARBLE, RU)
    ruins.wall(M, 7.0, 17.0, 18.0, 19.2, 1.8, rnd, RU, bite=0.8)
    ruins.wall(M, 4.8, 6.0, 11.0, 17.0, 1.4, rnd, RU, bite=0.8)
    M.add(M.box(9.0, 15.0, 8.6, 10.4, 0, 0.3), MARBLE, RU)                                        # 門檻
    ruins.rubble(M, rnd, 7.0, 17.0, 11.0, 17.0, 8, RU, 0.5, 1.2)
    # ── Chalkites 小堂（中心 37, 10.5；本體 x 32～42、y 6.5～14.5；十字的兩臂筒形拱；八角鼓座＋鉛皮穹頂；後殿朝 +x）──
    cx, cy, x0, x1, y0, y1 = 37.0, 10.5, 32.0, 42.0, 6.5, 14.5
    M.add(M.box(x0 - 2.0, x1 + 3.0, y0 - 2.0, y1 + 2.0, 0, 2 * MPV), STONE, G1)                  # 小堂四周的石板
    M.add(M.box(x0, x1, y0, y1, 0, 6.0), BANDED, C)
    M.add(M.box(x0, x1, cy - 1.8, cy + 1.8, 0, 7.4) | M.box(cx - 1.8, cx + 1.8, y0, y1, 0, 7.4), BANDED, C)
    M.add(M.box(x0, x1, y0, y1, 6.0, 6.3), TILE, R)
    M.add(M.barrel(x0, x1, cy - 1.8, cy + 1.8, 7.4, 'x', 1.0) | M.barrel(cx - 1.8, cx + 1.8, y0, y1, 7.4, 'y', 1.0), TILE, R)
    M.add(M.ngon(cx, cy, 2.4, 8, 7.4, 9.6, rot=22.5), BANDED, C)
    M.add(M.dome(cx, cy, 9.6, 2.2, 1.8, ribs=8), LEAD, R)
    M.win(M.ring_windows(cx, cy, 1.4, 3.0, 7.9, 9.3, [22.5 + 45 * k for k in range(8)], 0.3))
    M.add(M.apse_x(x1 - 0.2, cy, 2.2, 3, 0, 5.4, '+x'), BANDED, C)
    M.add(M.semidome(x1 - 0.2, cy, 5.4, 2.0, '+x'), TILE, R)
    M.win(M.ring_windows(x1, cy, 1.2, 2.8, 2.6, 4.6, [0], 0.35))
    M.door(M.arch_open(x0, cy, 0, 2.8, 1.6, normal='x', depth=1.6))
    for yy in (y0, y1):
        M.win(M.arch_open(cx, yy, 3.0, 5.2, 0.9, normal='y', depth=1.6))
    t_ = 0.15
    M.add(M.box(cx - t_, cx + t_, cy - t_, cy + t_, 11.3, 12.9) | M.box(cx - t_, cx + t_, cy - 0.5, cy + 0.5, 12.2, 12.5), GOLD, R)
    M.MAT[M.S & M.full(M.Z < 1.0) & (M.MAT == BANDED)] = STONE
    # ── 柏樹 ──
    for (tx, ty) in ((28.0, 4.0), (28.0, 17.0), (45.5, 4.0), (45.5, 17.0), (24.0, 24.0)):
        M.tree(tx, ty, 9.0, 2.0, 5)
    G, L = M.finish(shell_m=0.8, seed=976, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'chapel': M.cell(cx, cy, 0.4)}
    return G, L, anchors, {'穹頂頂（m）': 11.4, '十字架頂（m）': 12.9}
