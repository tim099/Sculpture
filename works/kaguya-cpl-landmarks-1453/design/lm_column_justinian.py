# 查士丁尼騎像柱（Augustaion，543）1453：柱子與騎像都在；手上的球十字 1422–27 年掉了、柱前三座「蠻族國王」像 1433 年以前已移走（Majeska 1984）⇒ 騎像沒有球、柱前沒有三王。
#   柱是磚石芯外包銅板（1204 年後被剝了一部分 ⇒ 下半段露磚）。騎像面朝東、右手往東伸、頭盔有大羽飾（Procopius、Gyllius）。
#   研究整理：kaguya 暫存區 scratchpad/cpl/research_columns_churches.md §A3。
import byz, columns
from byz import MARBLE, BRONZE, BRICK

KEY = 'column-justinian'
TITLE = '查士丁尼騎像柱 1453（Column of Justinian，Augustaion，543；球十字已失）'
TITLE_SHORT = '查士丁尼騎像柱 1453'
MPV = 0.2
W, D, H = 13.0, 13.0, 50.0
META = {'kind': 'building', 'use': 'column-justinian', 'style': 'roman', 'lot': '13,13', 'base': 0, 'variant': 'a', 'lamps': 4}
PARTS = (('body', 1, '柱（七級台階、大理石基座、包銅柱身、柱頭）'), ('top', 2, '騎像（青銅）'))
PROV = {
    '七級台階、大理石基座': '參考資料：Wikipedia（7 級台階、大理石基座）；寬、高是設計決定（底級 12 m、共 3 m；基座 5 × 4 m）',
    '柱身 32 m、磚石芯外包銅板': '參考資料：學界估柱身 30–40 m（Boeck 2021 書評，ByzRev）；Buondelmonti「70」照 70 肘 ≈ 32 m 取；Gyllius「many Stones covered with Brass」；直徑 3.2 m 是設計決定',
    '騎像全高約 7.5 m、面朝東、羽飾頭盔、沒有球十字': '參考資料：Gyllius II.17 碎片（鼻 > 9 in、馬蹄高 9 in）⇒ 約真人 3–4.5 倍（推算）；Procopius；Majeska 1984 p.240（球 1422–27 掉落）',
    '下半段露磚（銅板剝掉）': '設計決定：1204 年後銅板被剝走的程度有爭議 ⇒ 下面 12 m 照種子露磚',
}


def build():
    import random
    M = byz.Model(W, D, H, MPV)
    cx = cy = 6.5
    steps = [[12.0 - k * 0.7, 3.0 / 7] for k in range(7)]
    C = {'steps': steps, 'pedestal': {'w': 5.0, 'h': 4.0, 'mat': MARBLE, 'cornice': 0.25}, 'base': {'d': 3.6, 'h': 0.6},
         'shaft': {'d0': 3.2, 'd1': 3.0, 'h': 32.0, 'drums': 16, 'ring_h': 0.2, 'mat': BRONZE, 'ring_mat': BRONZE},
         'capital': {'w': 3.8, 'h': 1.8, 'mat': BRONZE}}
    ztop = columns.column(M, cx, cy, C, lay=1)
    # 銅板剝掉的地方露磚：柱身下 12 m，每 1.6 m × 45° 一片照種子
    z0 = 3.0 + 4.0 + 0.6
    rnd = random.Random(1204)
    import numpy as np
    ang = np.degrees(np.arctan2(M.Y - cy, M.X - cx)) % 360
    for zi in range(int(12 / 1.6)):
        for ai in range(8):
            if rnd.random() < 0.45:
                sel = (M.Z >= z0 + zi * 1.6) & (M.Z < z0 + zi * 1.6 + 1.6) & (ang >= ai * 45) & (ang < ai * 45 + 45) & ((M.X - cx) ** 2 + (M.Y - cy) ** 2 < 1.7 ** 2)
                M.MAT[M.full(sel) & M.S] = BRICK
    # 騎像：模型 +y ＝ 東（地塊 rot 180：正面 y 0 朝西）⇒ dir 90
    T = {'kind': 'rider', 'scale': 4.6, 'dir': 90, 'orb': False, 'plinth': [5.4, 0.8]}
    zt = columns.rider(M, cx, cy, ztop, T, 2)
    G, L = M.finish(shell_m=0.8, seed=543)
    anchors = {'lot-0': [0, 0, 0], 'top': M.cell(cx, cy, zt - 0.2)}
    return G, L, anchors, {'柱頭頂（m）': round(ztop, 2), '騎像頂（m）': round(zt, 2)}

