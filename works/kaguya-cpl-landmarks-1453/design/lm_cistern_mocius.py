# 莫齊烏斯露天蓄水池 1453（Cistern of Mocius，491–518）：170 × 147 m、深約 12 m；面層是大石塊（不同於另兩座的小石＋磚）、內角倒斜角；晚期 St Mocius 教堂被拆作建材（Doukas）
#   研究整理：scratchpad/cpl/research_palaces_cisterns.md §4；占地：OSM way 315745066（Çukurbostan Parkı，171 × 148 m、長軸方位 90.8°）。
#   z 0 ＝ 池底（菜園面）：Blocksail SPECIAL 的 sink 9.0 ⇒ 地塊整平到地面下 9.0 m（遊戲只挖地塊裡面、牆擋著）。⛔ 不做：咖啡屋、19 世紀的兩口井、20 世紀的棚屋、公園。
import byz, cistern
from byz import BANDED, STONE, LEAD

KEY = 'cistern-mocius'
TITLE = '莫齊烏斯露天蓄水池 1453（Cistern of Mocius，491–518；池底是菜園與果園）'
TITLE_SHORT = '莫齊烏斯露天蓄水池 1453'
MPV = 0.4
W, D, H = 147.0, 170.0, 11.0
META = {'kind': 'building', 'use': 'cistern-mocius', 'style': 'roman', 'lot': '147,170', 'base': 0, 'variant': 'a', 'sink': 9.0, 'lamps': 12}
PARTS = (('body', 1, '池牆（磚帶＋石帶、牆頂步道與女兒牆、坡道）'), ('garden', 2, '池底（畦田、果園的地、看守小屋）'),
         ('trees-fruit', 3, '果樹（遊戲換成生成式的果樹）', {'kind': 'tree', 'tree': 'fruit'}), ('trees-olive', 4, '橄欖（遊戲換成生成式的橄欖樹）', {'kind': 'tree', 'tree': 'olive'}))
PROV = {
    '外框 147 × 170 m、牆厚 6.0 m': '參考資料：Wikipedia；TBL',
    '深 10.5–15 m（TBL 取 12 m）（1453 年照淤積取 9.0 m）': '參考資料：Wikipedia；TBL；取深度的七、八成是設計決定',
    '牆：大型石塊面層（類似 Anastasius 長城）': '參考資料：TBL 圖說；Wikipedia',
    '1453 年池內是菜園、果園': '參考資料：Clavijo 1403（全城概述）；Wikipedia、TBL（推估）；畦田、果樹、看守小屋、坡道是設計決定',
    '女兒牆 1 m': '設計決定（牆頂高出地面多少查無）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 0.0)
    P = {'depth': 9.0, 'wall_t': 6.0, 'parapet': 1.0, 'niche': 0, 'seed': 491, 'mat': STONE}
    zt = cistern.cistern(M, P, 1, 2)
    G, L = M.finish(shell_m=1.2, seed=491)
    anchors = {'lot-0': [0, 0, 0], 'rim': M.cell(W / 2, 0.5, 9.0)}
    return G, L, anchors, {'池深（m）': 9.0, '牆頂（m）': zt}
