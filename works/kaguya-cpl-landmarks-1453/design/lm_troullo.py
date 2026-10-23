# 特魯洛的施洗約翰堂（St John the Baptist in Troullo，Hirami Ahmet Paşa Mescidi；12 世紀）1453：完整的小教堂 ——
#   四柱十字型、前廊 3 開間；八角鼓座穹頂（8 肋 8 窗）；三個後殿裡外都是半圓（君士坦丁堡唯一外觀也是半圓的）、主後殿外突 3 m、一扇低而大的三聯窗；
#   南北十字臂筒拱、牆上三聯窗；灰縫比磚厚（磚 3 cm、灰縫 7–9 cm）⇒ 牆面以灰漿為主。
#   ⛔ 不做：diaconicon 改的 mihrab、鄂圖曼拿掉柱改橫樑、1961 年的修復。
#   研究整理：scratchpad/cpl/research_batch6.md §4；占地 OSM way 329234516（輪廓粗）的中心、朝向照 Van Millingen 1912 Fig. 70 的 76°。
import byz, church
from byz import BANDED, BRICK, STONE, LEAD, TILE

KEY = 'troullo'
TITLE = '特魯洛的施洗約翰堂 1453（St John in Troullo；四柱、八角鼓座、半圓後殿）'
TITLE_SHORT = '特魯洛施洗約翰堂 1453'
MPV = 0.2
W, D, H = 10.0, 16.0, 14.0
META = {'kind': 'building', 'use': 'troullo', 'style': 'roman', 'lot': '10,16', 'base': 0, 'variant': 'a', 'lamps': 6}
PARTS = (('body', 1, '主體（前廊、十字臂、後殿）'), ('roof', 2, '屋頂（穹頂、瓦）'))
PROV = {
    '四柱十字型、前廊 3 開間交叉拱；三個後殿裡外半圓、主後殿外突 3 m；八角鼓座 8 肋 8 窗': '參考資料：Van Millingen 1912 Ch. XII、Fig. 70；Wikipedia（Hirami Ahmet Pasha Mosque）',
    '含前廊長 15 m；穹頂內徑約 4 m、頂約 10.6 m、屋簷約 6.4 m': '參考資料：Wikipedia；量自 Van Millingen 1912（±3–5%）',
    '磚 3 cm、灰縫 7–9 cm': '參考資料：Van Millingen 1912 第 1 章的磚縫表',
    '寬、窗的大小、屋面': '設計決定',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.4, 0.4)                          # 灰縫多、磚線細
    P = {
        'naos': {'x': [0.4, 9.6], 'y': [3.8, 12.8], 'z': 5.4, 'arm_w': 3.4, 'arm_z': 6.8, 'roof': 'barrel', 'rise': 0.9},
        'domes': [{'cx': 5.0, 'cy': 8.3, 'r': 2.3, 'n': 8, 'z0': 7.0, 'h': 1.8, 'win': 8, 'rise': 1.8, 'ribs': 8, 'cross': True}],
        'apses': [{'cx': 5.0, 'r': 1.9, 'facets': 14, 'z': 5.0, 'win': 3, 'win_w': 0.5, 'win_z0': 1.6},
                  {'cx': 2.0, 'r': 0.95, 'facets': 10, 'z': 4.2}, {'cx': 8.0, 'r': 0.95, 'facets': 10, 'z': 4.2}],
        'bays': [{'x': [0.4, 9.6], 'y': [0.4, 3.8], 'z': 5.0, 'roof': 'shed', 'high': '+y', 'rise': 0.6}],
        'door': [{'x': 5.0, 'w': 1.4, 'h': 2.6}],
    }
    church.cross_in_square(M, P)
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=1150)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(5.0, 0.6, 0.0), 'dome-top': M.cell(5.0, 8.3, 10.6)}
    return G, L, anchors, {'穹頂頂（m）': round(7.0 + 1.8 + 1.8, 2)}
