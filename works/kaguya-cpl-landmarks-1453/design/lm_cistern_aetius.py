# 艾提烏斯露天蓄水池 1453（Cistern of Aetius，約 421）：244 × 85 m、深 13–15 m；磚帶約 0.35 m、石帶約 1.8 m
#   研究整理：scratchpad/cpl/research_palaces_cisterns.md §4；占地：OSM way 1385387864（Vefa 球場，長軸方位 140.5°）。
#   z 0 ＝ 池底（菜園面）：Blocksail SPECIAL 的 sink 10.0 ⇒ 地塊整平到地面下 10.0 m（遊戲只挖地塊裡面、牆擋著）。⛔ 不做：球場、看台、1926 年後的一切。
import byz, cistern
from byz import BANDED, STONE, LEAD

KEY = 'cistern-aetius'
TITLE = '艾提烏斯露天蓄水池 1453（Cistern of Aetius，約 421；池底是菜園與果園）'
TITLE_SHORT = '艾提烏斯露天蓄水池 1453'
MPV = 0.4
W, D, H = 85.0, 244.0, 12.0
META = {'kind': 'building', 'use': 'cistern-aetius', 'style': 'roman', 'lot': '85,244', 'base': 0, 'variant': 'a', 'sink': 10.0}
PARTS = (('body', 1, '池牆（磚帶＋石帶、牆頂步道與女兒牆、坡道）'), ('garden', 2, '池底（畦田、果園的地、看守小屋）'),
         ('trees-fruit', 3, '果樹（遊戲換成生成式的果樹）', {'kind': 'tree', 'tree': 'fruit'}), ('trees-olive', 4, '橄欖（遊戲換成生成式的橄欖樹）', {'kind': 'tree', 'tree': 'olive'}))
PROV = {
    '外框 85 × 244 m、牆厚 5.2 m': '參考資料：Wikipedia；TBL',
    '深 13–15 m（1453 年照淤積取 10.0 m）': '參考資料：Wikipedia；TBL；取深度的七、八成是設計決定',
    '牆：opus listatum，磚帶約 0.35 m、石帶約 1.8 m（WP 記 4 皮磚 / 10 皮石）': '參考資料：TBL 圖說；Wikipedia',
    '1453 年池內是菜園、果園': '參考資料：Clavijo 1403（全城概述）；Wikipedia、TBL（推估）；畦田、果樹、看守小屋、坡道是設計決定',
    '女兒牆 1 m': '設計決定（牆頂高出地面多少查無）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.35, 1.8)
    P = {'depth': 10.0, 'wall_t': 5.2, 'parapet': 1.0, 'niche': 0, 'seed': 421, 'mat': BANDED}
    zt = cistern.cistern(M, P, 1, 2)
    G, L = M.finish(shell_m=1.2, seed=421)
    anchors = {'lot-0': [0, 0, 0], 'rim': M.cell(W / 2, 0.5, 10.0)}
    return G, L, anchors, {'池深（m）': 10.0, '牆頂（m）': zt}
