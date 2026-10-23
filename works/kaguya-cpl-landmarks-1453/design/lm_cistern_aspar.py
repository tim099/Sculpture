# 阿斯帕露天蓄水池 1453（Cistern of Aspar，459 起）：152 m 見方、深 10–11 m；磚帶約 0.5 m、石帶約 1.2 m；西南牆的放射狀磚拱痕（扶壁壁龕）；北角的圓柱形壓力塔＋半穹頂（中期拜占庭，1453 在）；晚期可能已是花園（Xerokepion「乾園」）
#   研究整理：scratchpad/cpl/research_palaces_cisterns.md §4；占地：OSM way 309052085（Çukur Bostan Parkı，150 × 130 m、方位 145.8°）。
#   z 0 ＝ 池底（菜園面）：Blocksail SPECIAL 的 sink 8.0 ⇒ 地塊整平到地面下 8.0 m（遊戲只挖地塊裡面、牆擋著）。⛔ 不做：池內的村落（1565/66 的清真寺、木屋、1950s 公寓）、停車場、運動場。
import byz, cistern
from byz import BANDED, STONE, LEAD

KEY = 'cistern-aspar'
TITLE = '阿斯帕露天蓄水池 1453（Cistern of Aspar，459 起；池底是菜園與果園）'
TITLE_SHORT = '阿斯帕露天蓄水池 1453'
MPV = 0.4
W, D, H = 152.0, 152.0, 13.0
META = {'kind': 'building', 'use': 'cistern-aspar', 'style': 'roman', 'lot': '152,152', 'base': 0, 'variant': 'a', 'sink': 8.0, 'ground': 'hide', 'lamps': 12}
PARTS = (('body', 1, '池牆（磚帶＋石帶、牆頂步道與女兒牆、坡道）'), ('garden', 2, '池底（畦田、果園的地、看守小屋）'),
         ('trees-fruit', 3, '果樹（遊戲換成生成式的果樹）', {'kind': 'tree', 'tree': 'fruit'}), ('trees-olive', 4, '橄欖（遊戲換成生成式的橄欖樹）', {'kind': 'tree', 'tree': 'olive'}),
         ('field', 5, '菜畦（遊戲換成生成式的作物）', {'kind': 'field'}))
PROV = {
    '外框 152 × 152 m、牆厚 5.2 m': '參考資料：Wikipedia；TBL',
    '深 10–11 m（1453 年照淤積取 8.0 m）': '參考資料：Wikipedia；TBL；取深度的七、八成是設計決定',
    '牆：opus listatum，磚帶約 0.5 m、石帶約 1.2 m（WP 記 5 皮磚 / 5 皮石）': '參考資料：TBL 圖說；Wikipedia',
    '1453 年池內是菜園、果園': '參考資料：Clavijo 1403（全城概述）；Wikipedia、TBL（推估）；畦田、果樹、看守小屋、坡道是設計決定',
    '女兒牆 1 m': '設計決定（牆頂高出地面多少查無）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.5, 1.2)
    P = {'depth': 8.0, 'wall_t': 5.2, 'parapet': 1.0, 'niche': 8.0, 'seed': 459, 'mat': BANDED}
    zt = cistern.cistern(M, P, 1, 2, 5)
    # 北角（模型 x、y 都大的那一角）的圓柱形壓力塔＋半穹頂
    cx, cy = W - 5.2, D - 5.2
    M.add(M.cyl(cx, cy, 3.4, 0, 8.0 + 4.0), BANDED, 1)
    M.add(M.semidome(cx, cy, 8.0 + 4.0, 3.2, '-y') | M.semidome(cx, cy, 8.0 + 4.0, 3.2, '+y'), LEAD, 1)
    G, L = M.finish(shell_m=1.2, seed=459)
    anchors = {'lot-0': [0, 0, 0], 'rim': M.cell(W / 2, 0.5, 8.0)}
    return G, L, anchors, {'池深（m）': 8.0, '牆頂（m）': zt}
