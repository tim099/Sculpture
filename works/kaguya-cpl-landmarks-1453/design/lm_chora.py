# 柯拉修道院（救主堂，Chora／Kariye）1453：11–12 世紀的主堂＋ Metochites 1315–21 的內外前廊、南側堂（parekklesion）、北側二層附屬 —— 外觀完整（城破後最早遭劫的之一）。
#   ⛔ 不做：西南角的宣禮塔（Bayezid II，1511 年前；1453 年那裡是鐘樓）、mihrab、1668 年的噴泉、19 世紀壓平的屋頂輪廓。主穹頂冠今天是鄂圖曼換的 ⇒ 照 vM 做 16 瓣 8 窗。
#   研究整理：kaguya 暫存區 scratchpad/cpl/research_columns_churches.md §B2；方向、占地：OSM relation 7614527（36.5 × 32.3 m、軸方位 104.5°）。
import byz, church
from byz import BANDED, STONE, LEAD, TILE, GOLD, BRICK

KEY = 'chora'
TITLE = '柯拉修道院 1453（救主堂 Chora，Metochites 1315–21 的前廊與側堂）'
TITLE_SHORT = '柯拉修道院 1453'
MPV = 0.2
W, D, H = 32.0, 37.0, 27.0
META = {'kind': 'building', 'use': 'chora', 'style': 'roman', 'lot': '32,37', 'base': 0, 'variant': 'a', 'lamps': 8}
PARTS = (('body', 1, '主體（牆、前廊、側堂、鐘樓、後殿）'), ('roof', 2, '屋頂（六個穹頂、瓦、鐘樓頂）'))
PROV = {
    '外前廊 23 × 4 m、內前廊 18 × 4 m': '參考資料：Wikipedia',
    '主穹頂淨徑 7.7 m（16 瓣 8 窗）；側堂穹頂 4.5 m（12 邊 12 窗）；共 6 個穹頂': '參考資料：Wikipedia；van Millingen 1912',
    '主後殿外 5 面、兩側 3 面': '參考資料：van Millingen 1912',
    '牆：磚石條紋': '參考資料：van Millingen 1912（側堂後殿北牆）；石帶、磚帶的高是設計決定',
    '鐘樓（西南角）': '參考資料：TBL（宣禮塔取代原本的鐘樓）；尺寸是設計決定',
    '各量體的牆高、側堂長 20 m、北側附屬寬': '設計決定（查無實測；對照 OSM 外框）',
}


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (0.9, 0.45)
    P = {
        'naos': {'x': [6.0, 22.0], 'y': [8.0, 25.0], 'z': 11.0, 'arm_w': 8.0, 'arm_z': 13.5, 'roof': 'barrel', 'rise': 1.6},
        'domes': [{'cx': 14.0, 'cy': 16.5, 'r': 4.7, 'n': 16, 'z0': 14.2, 'h': 3.6, 'win': 8, 'rise': 3.8, 'ribs': 16, 'cross': True},
                  {'cx': 8.0, 'cy': 6.0, 'r': 2.4, 'n': 16, 'z0': 10.0, 'h': 2.4, 'win': 8, 'rise': 2.0, 'ribs': 16},      # 內前廊北端
                  {'cx': 17.5, 'cy': 6.0, 'r': 2.7, 'n': 16, 'z0': 10.0, 'h': 2.4, 'win': 8, 'rise': 2.3, 'ribs': 16},     # 內前廊門南側（大一點）
                  {'cx': 4.8, 'cy': 22.0, 'r': 1.6, 'n': 8, 'z0': 10.0, 'h': 1.8, 'win': 8, 'rise': 1.4, 'ribs': 8},       # 北側 prothesis（8 瓣）
                  {'cx': 23.3, 'cy': 22.0, 'r': 1.6, 'n': 8, 'z0': 10.0, 'h': 1.8, 'win': 0, 'rise': 1.4},                 # 南側 diakonikon（素面）
                  {'cx': 27.0, 'cy': 9.5, 'r': 2.8, 'n': 12, 'z0': 11.2, 'h': 3.8, 'win': 12, 'rise': 2.4, 'ribs': 12}],   # 側堂（12 邊 12 窗）
        'apses': [{'cx': 14.0, 'r': 4.2, 'facets': 5, 'z': 10.5, 'win': 3, 'win_w': 0.9}, {'cx': 4.8, 'y': 25.0, 'r': 1.4, 'facets': 3, 'z': 7.5},
                  {'cx': 23.3, 'y': 25.0, 'r': 1.4, 'facets': 3, 'z': 7.5}, {'cx': 27.0, 'y': 24.0, 'r': 2.6, 'facets': 5, 'z': 8.5, 'win': 3}],
        'bays': [{'x': [3.0, 6.0], 'y': [8.0, 25.0], 'z': 9.0, 'roof': 'shed', 'high': '+x', 'rise': 1.0},                     # 北側（prothesis 與二層附屬）
                 {'x': [22.0, 24.5], 'y': [18.0, 25.0], 'z': 9.0, 'roof': 'shed', 'high': '-x', 'rise': 0.8},                   # 南側 diakonikon
                 {'x': [24.0, 30.0], 'y': [4.0, 24.0], 'z': 10.0, 'roof': 'gable', 'axis': 'y', 'rise': 1.4},                   # 側堂
                 {'x': [3.0, 24.0], 'y': [4.0, 8.0], 'z': 9.5, 'roof': 'shed', 'high': '+y', 'rise': 1.0},                      # 內前廊
                 {'x': [3.0, 30.0], 'y': [0.0, 4.0], 'z': 7.5, 'roof': 'shed', 'high': '+y', 'rise': 1.0,                       # 外前廊：西面一排拱
                  'arcade_x': [5.0, 8.5, 12.0, 20.0, 23.5, 27.0], 'arc_z0': 1.0, 'arc_z1': 5.4, 'arc_w': 2.0}],
        'door': [{'x': 16.0, 'y': 0.0, 'w': 2.2, 'h': 3.6}],
    }
    church.cross_in_square(M, P)
    # 鐘樓（西南角，外前廊南端外側；設計）：4 × 4 m、18 m、頂層四面開拱、四坡頂
    bx0, bx1, by0, by1 = 28.0, 32.0, 0.0, 4.0
    M.add(M.box(bx0, bx1, by0, by1, 0, 17.0), BANDED, 1)
    M.add(M.hip(bx0, bx1, by0, by1, 17.0, 2.2, 1.2), TILE, 2)
    for xc in (30.0,):
        M.win(M.arch_open(xc, by0, 13.5, 16.3, 1.6, normal='y', depth=1.6))
        M.win(M.arch_open(xc, by1, 13.5, 16.3, 1.6, normal='y', depth=1.6))
    M.win(M.arch_open(bx0, 2.0, 13.5, 16.3, 1.6, normal='x', depth=1.6))
    M.win(M.arch_open(bx1, 2.0, 13.5, 16.3, 1.6, normal='x', depth=1.6))
    # Metochites 的東扶壁（主後殿兩側）
    for xc in (9.4, 18.6):
        M.add(M.box(xc - 0.6, xc + 0.6, 25.0, 27.6, 0, 7.5), BANDED, 1)
    # 牆腳一圈石
    M.MAT[M.S & M.full(M.Z < 1.0) & (M.MAT == BANDED)] = STONE
    G, L = M.finish(shell_m=0.8, seed=1315)
    anchors = {'lot-0': [0, 0, 0], 'door': M.cell(16.0, 0.2, 0), 'bell': M.cell(30.0, 2.0, 14.0), 'dome-top': M.cell(14.0, 16.5, 23.0)}
    return G, L, anchors, {}
