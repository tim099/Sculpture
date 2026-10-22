# 君士坦丁紀念柱（Çemberlitaş）1453：1106 年大風吹倒雕像與最上面三節，Manuel I Komnenos（1143–80）在原處砌大理石頂、立十字架 ⇒ 斑岩柱身 → 大理石砌頂 → 十字架。
#   ⛔ 不做 1779 年以後包住基座與最底一節的鄂圖曼石殼、今天的鐵箍。研究整理：kaguya 暫存區 scratchpad/cpl/research_columns_churches.md §A1。
import byz, columns
from byz import MARBLE, PORPHYRY, BRONZE, GOLD

KEY = 'column-constantine'
TITLE = '君士坦丁紀念柱 1453（Column of Constantine，330；Manuel I 的砌頂與十字架）'
TITLE_SHORT = '君士坦丁紀念柱 1453'
MPV = 0.2
W, D, H = 12.0, 12.0, 41.0
META = {'kind': 'building', 'use': 'column-constantine', 'style': 'roman', 'lot': '12,12', 'base': 0, 'variant': 'a'}
PARTS = (('body', 1, '柱（台階、白大理石基座、斑岩柱身、砌頂）'), ('top', 2, '十字架'))
PROV = {
    '台階 5 級共 2 m、底級 11.25 m 見方、頂平台 8.35 m': '參考資料：TBL（5 級約 2 m、底級 11.25 m）；Vett 1929–30 量平台 8.35 m（Columbia MCID）',
    '基座 3.7 m 見方 × 5.5 m 高、白大理石': '參考資料：Gyllius III.3（11 ft 9 in × 18 ft）；Vett 3.80 m',
    '柱身 8 節 × 3.28 m、直徑 2.9 m、接縫一道金屬箍': '參考資料：Gyllius 8 節各 10 ft 9 in（1540 年代，離 1453 最近；今天 7 節）；TBL 底節直徑 2.90 m；箍的年代不明（可能早到 5 世紀）',
    '柱礎 0.6 m、砌頂 2.7 m、十字架 3 m': '設計決定：砌頂照「原始地面到頂約 37 m」（今天 34.8 m ＋ 原地面低 2.2–2.5 m）倒推；十字架高查無',
}


def build():
    M = byz.Model(W, D, H, MPV)
    cx = cy = 6.0
    steps = [[11.25, 0.4], [10.5, 0.4], [9.8, 0.4], [9.05, 0.4], [8.35, 0.4]]
    C = {'steps': steps, 'pedestal': {'w': 3.7, 'h': 5.5, 'mat': MARBLE, 'cornice': 0.25}, 'base': {'d': 3.3, 'h': 0.6},
         'shaft': {'d0': 2.9, 'd1': 2.9, 'h': 8 * 3.28, 'drums': 8, 'ring_h': 0.3, 'mat': PORPHYRY, 'ring_mat': BRONZE},
         'capital': {'w': 3.0, 'h': 2.7, 'mat': MARBLE},
         'top': {'kind': 'cross', 'h': 3.0, 'arm': 1.6, 't': 0.4}}
    ztop = columns.column(M, cx, cy, dict(C, top=None), lay=1)
    zc = ztop                                    # 十字架另一件（top）：照砌頂頂立
    T = C['top']
    M.add(M.box(cx - 0.2, cx + 0.2, cy - 0.2, cy + 0.2, zc, zc + T['h']), GOLD, 2)
    M.add(M.box(cx - T['arm'] / 2, cx + T['arm'] / 2, cy - 0.2, cy + 0.2, zc + T['h'] * 0.62, zc + T['h'] * 0.62 + 0.4), GOLD, 2)
    G, L = M.finish(shell_m=0.8, seed=330)
    anchors = {'lot-0': [0, 0, 0], 'top': M.cell(cx, cy, zc + T['h'] - 0.2)}
    return G, L, anchors, {'砌頂頂（m）': round(ztop, 2), '十字架頂（m）': round(zc + T['h'], 2)}
