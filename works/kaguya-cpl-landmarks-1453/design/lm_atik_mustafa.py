# Blachernae 的十字穹頂教堂（Atik Mustafa Paşa Camii／Hz. Cabir Camii；St Thekla？SS Peter & Mark？；9 或 11 世紀）1453：完整的教堂 ——
#   最簡單的十字穹頂型（domed Greek cross）、L 形墩、十字臂與四角小室筒拱；南北牆三層（地面三連拱、中層三窗、上層一扇三聯窗）；
#   三個多角形後殿（外 3 面、突出明顯）；西邊拜占庭的前廊（形式查不到 ⇒ 設計：3 開間、單坡）、穹頂有鼓座開窗（推測）。
#   ⛔ 不做：1509 年地震後的無鼓座穹頂、鄂圖曼的屋頂與簷口、西側木前廊、宣禮塔、mihrab、1692 年的噴泉。
#   研究整理：scratchpad/cpl/research_batch6.md §3；占地 OSM way 329233909（18.8 × 15.5 m、軸 132.7°）、後殿朝東南。
import byz, church
from byz import BANDED, BRICK, STONE, LEAD, TILE

KEY = 'atik-mustafa'
TITLE = 'Blachernae 的十字穹頂教堂 1453（Atik Mustafa Paşa；三個後殿）'
TITLE_SHORT = 'Atik Mustafa Paşa 教堂 1453'
MPV = 0.2
W, D, H = 16.0, 19.0, 16.0
META = {'kind': 'building', 'use': 'atik-mustafa', 'style': 'roman', 'lot': '16,19', 'base': 0, 'variant': 'a', 'lamps': 6}
PARTS = (('body', 1, '主體（十字臂、角落小室、前廊、後殿）'), ('roof', 2, '屋頂（穹頂、瓦）'))
PROV = {
    '十字穹頂型、L 形墩、南北牆三層立面、三個多角形後殿（外 3 面）': '參考資料：Van Millingen 1912 Ch. X、Fig. 64/65；Wikipedia（Atik Mustafa Pasha Mosque）',
    '寬 15 × 長 17.5 m、中央穹頂間約 4.1 m 見方': '參考資料：Wikipedia；量自 Van Millingen 1912 Fig. 64（±3–5%）',
    '1453 年的前廊與穹頂（現存的是 1509 年後鄂圖曼重建）': '設計決定（形式查不到）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.0)
    P = {
        'naos': {'x': [0.6, 15.4], 'y': [3.8, 16.0], 'z': 7.0, 'arm_w': 4.4, 'arm_z': 8.6, 'roof': 'barrel', 'rise': 1.1},
        'domes': [{'cx': 8.0, 'cy': 9.9, 'r': 2.5, 'n': 8, 'z0': 8.8, 'h': 1.6, 'win': 8, 'rise': 1.8, 'ribs': 8, 'cross': True}],
        'apses': [{'cx': 8.0, 'r': 2.2, 'facets': 3, 'z': 6.6, 'win': 1, 'win_w': 0.7}, {'cx': 3.6, 'r': 1.15, 'facets': 3, 'z': 5.2},
                  {'cx': 12.4, 'r': 1.15, 'facets': 3, 'z': 5.2}],
        'bays': [{'x': [0.6, 15.4], 'y': [0.4, 3.8], 'z': 5.6, 'roof': 'shed', 'high': '+y', 'rise': 0.8}],
        'door': [{'x': 8.0, 'w': 1.6, 'h': 3.0}, {'x': 3.6, 'w': 1.0, 'h': 2.4}, {'x': 12.4, 'w': 1.0, 'h': 2.4}],
    }
    church.cross_in_square(M, P)
    # 南北牆：地面三連拱（封了開窗）、中層三窗
    for xx in (0.6, 15.4):
        for yy in (8.4, 9.9, 11.4):
            M.win(M.arch_open(xx, yy, 1.2, 3.4, 0.9, normal='x', depth=2.4))
    M.MAT[M.S & M.full(M.Z < 0.8) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=1059)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(8.0, 0.6, 0.0), 'dome-top': M.cell(8.0, 9.9, 12.2)}
    return G, L, anchors, {'穹頂頂（m）': round(8.8 + 1.6 + 1.8, 2)}
