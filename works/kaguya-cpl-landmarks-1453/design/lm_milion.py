# 米利翁（Milion，帝國道路的零點；君士坦丁 4 世紀初）1453：四面拱門（tetrapylon）上覆穹頂 ——
#   1268–71 年歸聖索菲亞；到 15 世紀末仍完好、16 世紀初為了 Su terazisi 水塔工程消失（Müller-Wiener）；Madden：1203 年的大火裡倖存。
#   ⛔ 不做：今天立著的那一截墩（1967–68 發掘後立起）、Su terazisi、Ayasofya Meydanı 的現代鋪面。
#   研究整理：scratchpad/cpl/research_batch3.md §3；位置 OSM node 1908677124（Milyon Taşı，41.008067, 28.978018）；寬約 14.6 m 只有一張沒出處的復原圖說（弱）。
import byz
from byz import BANDED, MARBLE, LEAD, STONE, BRICK

KEY = 'milion'
TITLE = '米利翁里程碑 1453（Milion：四面拱門、穹頂）'
TITLE_SHORT = '米利翁 1453'
MPV = 0.2
W, D, H = 15.0, 15.0, 19.0
META = {'kind': 'building', 'use': 'milion', 'style': 'roman', 'lot': '15,15', 'base': 0, 'variant': 'a', 'lamps': 4}
PARTS = (('body', 1, '四面拱門（墩、拱、簷）'), ('roof', 2, '穹頂'))
PROV = {
    '四面拱門上覆穹頂（tetrapylon）': '參考資料：Müller-Wiener 1977 p.216（經 Wikipedia）',
    '到 15 世紀末仍完好；1203 年大火倖存': '參考資料：Wikipedia（引 Müller-Wiener p.218）；Madden 1991–92（引 Dirimtekin）',
    '寬約 14.6 m': '參考資料：Wikipedia 的復原圖說（沒出處，弱）',
    '高、拱的寬高、穹頂的大小、材料': '設計決定（查不到）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.6, 1.0)
    c = W / 2
    zs, za = 6.2, 12.6                                         # 起拱、簷口
    M.add(M.box(0.3, W - 0.3, 0.3, D - 0.3, 0, za), BANDED, 1)
    for normal in ('x', 'y'):                                  # 兩條軸各一道穿過去的拱（寬 6.4 m）
        M.air(M.arch_open(c, c, 0, zs + 3.2, 6.4, normal=normal, depth=W + 2))
    M.air(M.box(4.0, W - 4.0, 4.0, D - 4.0, 0, zs + 3.2))      # 中間交叉處
    M.add(M.box(0.0, W, 0.0, D, 0, 0.8) & ~M.box(4.0, W - 4.0, 4.0, D - 4.0, 0, 99) & ~M.box(c - 3.2, c + 3.2, -1, 99, 0, 99) & ~M.box(-1, 99, c - 3.2, c + 3.2, 0, 99), MARBLE, 1)   # 墩基
    for normal in ('x', 'y'):                                  # 大理石拱圈
        ring = M.arch_open(c, c, 0, zs + 3.8, 7.6, normal=normal, depth=W + 0.4) & ~M.arch_open(c, c, 0, zs + 3.2, 6.4, normal=normal, depth=W + 2) & (M.Z >= zs)
        outer = (M.X < 0.9) | (M.X > W - 0.9) | (M.Y < 0.9) | (M.Y > D - 0.9)
        M.add(ring & outer, MARBLE, 1)
    M.add(M.box(0.0, W, 0.0, D, za - 0.6, za), MARBLE, 1)     # 簷口
    M.add(M.box(0.0, W, 0.0, D, zs - 0.4, zs), MARBLE, 1)     # 起拱線
    M.add(M.box(1.5, W - 1.5, 1.5, D - 1.5, za, za + 1.2), BANDED, 1)       # 穹頂座（方 → 圓）
    M.add(M.dome(c, c, za + 1.2, 5.6, 4.6, ribs=16), LEAD, 2)
    G, L = M.finish(shell_m=0.8, seed=330, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'top': M.cell(c, c, za + 5.6)}
    return G, L, anchors, {'簷口（m）': za, '穹頂頂（m）': za + 1.2 + 4.6}
