# 奧古斯都廣場（Augustaion，聖索菲亞南方）1453：Buondelmonti（15 世紀初）說廣場已成廢墟；Clavijo 1403 在教堂前院看到 9 根非常大的白大理石柱 ——
#   四面的柱廊（459 重建、Justinian 修復）只剩柱礎與斷柱、鋪面殘破、其餘是碎石與菜園；正中偏西是查士丁尼騎像柱（柱與騎像都在、球十字 1422–27 掉了）。
#   查士丁尼柱照 kaguya-cpl-column-justinian-1453（lm_column_justinian.py）的數字在這裡重蓋一次：
#     跟君士坦丁廣場同一個理由 —— 柱與廣場各自一塊地塊會各自整平 ⇒ 一高一低（柱腳埋進廣場的鋪面、或柱浮在石基上）⇒ 併成一塊。
#   ⛔ 不做：Su terazisi、Hürrem Sultan 浴場（1556）、Hacı Beşir Ağa 噴泉、今天的 Ayasofya Meydanı 鋪面與鄂圖曼墓群、廣場東邊的元老院與東南的 Chalke（1453 年的樣子查不到）。
#   研究整理：scratchpad/cpl/research_batch3.md §3；大小 85 × 62 m 照 Guilland（Wikipedia 引 Katsaveli 2007）；北緣貼聖索菲亞地塊的南緣（模型 +x ＝ 沿南緣往東南、方位 123° 的那一邊是正面）。
import math
import random
import numpy as np
import byz, columns
from byz import MARBLE, BRONZE, BRICK, STONE, SOIL

KEY = 'augustaion'
TITLE = '奧古斯都廣場 1453（Augustaion：查士丁尼騎像柱、九根白柱、殘破的柱廊與鋪面）'
TITLE_SHORT = '奧古斯都廣場 1453'
MPV = 0.2
W, D, H = 85.0, 62.0, 51.0
META = {'kind': 'building', 'use': 'augustaion', 'style': 'roman', 'lot': '85,62', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('ground', 1, '地面（殘破的大理石鋪面、碎石、菜園、草）'), ('column', 2, '查士丁尼騎像柱（台階、基座、包銅柱身、柱頭）'), ('rider', 3, '騎像（青銅）'),
         ('ruins', 4, '九根白柱、柱廊的柱礎與斷柱'))
PROV = {
    '廣場約 85 × 60–65 m、四面柱廊、入口在西與南': '參考資料：Wikipedia（Augustaeum，引 Katsaveli 2007、Procopius Aed. I.10.5）',
    '15 世紀初已成廢墟': '參考資料：Buondelmonti（經 Wikipedia 引 Katsaveli）',
    '教堂前院 9 根非常大的白大理石柱（屬廣場柱廊或牧首府不確定）': '參考資料：Clavijo 1403（Markham 1859 英譯 p.36）',
    '查士丁尼柱：同 kaguya-cpl-column-justinian-1453 的 PROV（七級台階、包銅柱身 32 m、騎像面朝東、沒有球十字）': '同 lm_column_justinian.py',
    '九根白柱的位置與高、柱廊殘段、鋪面殘存多少、菜園': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    rnd = random.Random(543)
    # ── 地面：草為底；中間一大片殘破的大理石鋪面（每 2.4 m 一塊板，約三成缺了）；東南角菜園 ──
    M.add(M.box(0, W, 0, D, 0, 0.2), byz.GREEN, 1)
    keep = np.random.RandomState(543).rand(int(D / 2.4) + 1, int(W / 2.4) + 1) < 0.68             # 每塊板照種子抽：約三成缺了
    slab = keep[(M.Y // 2.4).astype(int), (M.X // 2.4).astype(int)]
    M.add(M.box(4, W - 4, 6, D - 2, 0, 0.2) & slab, MARBLE, 1)
    M.add(M.box(60, W - 1, 1, 18, 0, 0.3) & ((M.Y % 1.6) < 0.8), SOIL, 1)                        # 畦田
    # ── 查士丁尼騎像柱（同 lm_column_justinian.py；模型 +x 沿聖索菲亞南緣往東南 ⇒ 東 ＝ 從 +x 往 +y 33°）──
    cx, cy = 25.0, 41.0
    steps = [[12.0 - k * 0.7, 3.0 / 7] for k in range(7)]
    C = {'steps': steps, 'pedestal': {'w': 5.0, 'h': 4.0, 'mat': MARBLE, 'cornice': 0.25}, 'base': {'d': 3.6, 'h': 0.6},
         'shaft': {'d0': 3.2, 'd1': 3.0, 'h': 32.0, 'drums': 16, 'ring_h': 0.2, 'mat': BRONZE, 'ring_mat': BRONZE},
         'capital': {'w': 3.8, 'h': 1.8, 'mat': BRONZE}}
    ztop = columns.column(M, cx, cy, C, lay=2)
    z0 = 3.0 + 4.0 + 0.6
    r1204 = random.Random(1204)
    ang = np.degrees(np.arctan2(M.Y - cy, M.X - cx)) % 360
    for zi in range(int(12 / 1.6)):
        for ai in range(8):
            if r1204.random() < 0.45:
                sel = (M.Z >= z0 + zi * 1.6) & (M.Z < z0 + zi * 1.6 + 1.6) & (ang >= ai * 45) & (ang < ai * 45 + 45) & ((M.X - cx) ** 2 + (M.Y - cy) ** 2 < 1.7 ** 2)
                M.MAT[M.full(sel) & M.S] = BRICK
    T = {'kind': 'rider', 'scale': 4.6, 'dir': 33, 'orb': False, 'plinth': [5.4, 0.8]}
    zr = columns.rider(M, cx, cy, ztop, T, 3)
    # ── 九根白柱（Clavijo）：沿北緣（貼聖索菲亞那一邊）一排，柱高 11 m、柱頭、柱礎 ──
    R = 4
    for k in range(9):
        x = 14.0 + k * 7.0
        y = D - 7.0
        M.add(M.box(x - 1.0, x + 1.0, y - 1.0, y + 1.0, 0, 1.0), MARBLE, R)
        M.add(M.cyl(x, y, 0.65, 1.0, 12.0), MARBLE, R)
        M.add(M.box(x - 0.95, x + 0.95, y - 0.95, y + 0.95, 12.0, 13.2), MARBLE, R)
    # ── 柱廊殘段：東、南兩面的柱礎（斷柱高低不齊），西面南段兩根 ──
    def stub(x, y):
        h = 0.0 if rnd.random() < 0.35 else 0.8 + rnd.random() * (6.5 if rnd.random() < 0.3 else 2.4)
        M.add(M.box(x - 0.6, x + 0.6, y - 0.6, y + 0.6, 0, 0.6), MARBLE, R)
        if h > 0: M.add(M.cyl(x, y, 0.4, 0.6, 0.6 + h), MARBLE, R)
    for k in range(13):
        stub(6.0 + k * 6.0, 3.0)                       # 南（正面）
    for k in range(9):
        stub(W - 3.0, 8.0 + k * 6.0)                   # 東
    for y in (8.0, 14.0):
        stub(3.0, y)
    for k in range(18):                                # 倒下的柱段、碎石
        x, y = 6.0 + rnd.random() * (W - 12.0), 5.0 + rnd.random() * (D - 16.0)
        if math.hypot(x - cx, y - cy) < 8.0: continue
        if k % 3 == 0:
            L_ = 2.0 + rnd.random() * 3.0
            M.add(((M.Y - y) ** 2 + (M.Z - 0.4) ** 2 < 0.4 ** 2) & (M.X >= x) & (M.X < x + L_), MARBLE, R)
        else:
            s = 0.5 + rnd.random() * 1.0
            M.add(M.dome(x, y, 0.0, s, s * 0.5), STONE, R)
    G, L = M.finish(shell_m=0.8, seed=543, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'top': M.cell(cx, cy, zr - 0.2)}
    return G, L, anchors, {'柱頭頂（m）': round(ztop, 2), '騎像頂（m）': round(zr, 2)}
