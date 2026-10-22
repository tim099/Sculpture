# 布科勒昂宮（Boukoleon，大皇宮的海濱宮；Theophilos、Nikephoros II 擴建，拉丁皇帝偏愛）1453：仍立、但已成廢墟 ——
#   面海的那一棟坐在海牆上：上層一排三個大理石框的大開口（後面的拱頂廳、托架承托的面海陽台）、兩端各一隻獅像；
#   後面的台地：塌了一半的拱頂下部結構、斷牆、倒下的柱、碎石，長了野樹。
#   ⚠ 遊戲裡海牆是規劃的牆（另外畫，高 12 m）⇒ 這一棟擺在海牆內側、上層露出牆頂（史實上立面就砌在海牆本身上、窗離海面約 13.5 m）。
#   ⛔ 不做：1871／1873 鐵路拆掉的東段立面以外的近代東西（鐵路、1959 Kennedy Caddesi 填海、今天的護欄）；獅像 1871 年後搬到考古博物館 ⇒ 1453 年還在原位。
#   研究整理：scratchpad/cpl/research_palaces_cisterns.md §3（＋ research_batch3.md）。
import math
import random
import byz
from byz import BANDED, BRICK, STONE, MARBLE, TILE, SOIL, WOOD

KEY = 'boukoleon'
TITLE = '布科勒昂宮 1453（Boukoleon，大皇宮的海濱宮；已成廢墟）'
TITLE_SHORT = '布科勒昂宮 1453'
MPV = 0.2
W, D, H = 60.0, 38.0, 22.0
META = {'kind': 'building', 'use': 'boukoleon', 'style': 'roman', 'lot': '60,38', 'base': 0, 'variant': 'a', 'lamps': 0}
PARTS = (('body', 1, '面海的宮殿（廢墟：三個大理石框開口、陽台、獅像）'), ('ruins', 2, '台地上的廢墟（拱頂下部結構、斷牆、倒柱、碎石）'),
         ('trees-fig', 3, '野樹（遊戲換成生成式的闊葉樹）', {'kind': 'tree', 'tree': 'broadleaf'}))
PROV = {
    '宮殿坐落在台地上（約 61 × 53 m）、面海的立面砌在海牆本身上': '參考資料：van Millingen 1899（Leunclavius 的記載、腳註）',
    '現存西段：三個大理石框的大開口＋一個門道，後面是拱頂空間，面海陽台由大理石托架承托': '參考資料：Wikipedia（Bucoleon Palace）；TBL',
    '東段立面一排三窗、兩端各一隻獅像（1871 年拆）': '參考資料：van Millingen 1899',
    '窗離海面約 13.5 m；牆是磚石交替與純磚段': '參考資料：Müller-Wiener 2002（經土文 Wikipedia）',
    '1453 年仍立、但已成廢墟；大皇宮在帕列奧略時代被棄用': '參考資料：Wikipedia（推估）；Necipoğlu 1991（Mehmed II 入宮見其荒廢）',
    '模型 60 × 36 m、各段的高度、廢墟的樣子、野樹；擺在海牆內側': '設計決定',
}


def lion(M, cx, cy, z0, face='-y', lay=1):
    """獅像（蹲踞、朝 face）：基座＋身＋頭＋鬃，約 2.4 × 1.0 × 1.8 m。"""
    s = -1 if face == '-y' else 1
    M.add(M.box(cx - 1.3, cx + 1.3, cy - 0.7, cy + 0.7, z0, z0 + 0.6), MARBLE, lay)                         # 基座
    M.add(M.box(cx - 1.0, cx + 0.9, cy - 0.45, cy + 0.45, z0 + 0.6, z0 + 1.4), MARBLE, lay)                 # 身
    M.add(M.box(cx + 0.5, cx + 1.2, cy - 0.55, cy + 0.55, z0 + 0.9, z0 + 2.0), MARBLE, lay)                 # 鬃與頭
    M.add(M.box(cx + 1.2, cx + 1.5, cy - 0.3, cy + 0.3, z0 + 1.2, z0 + 1.7), MARBLE, lay)                   # 口鼻
    M.add(M.box(cx - 1.2, cx - 0.9, cy - 0.15, cy + 0.15, z0 + 0.6, z0 + 1.6), MARBLE, lay)                 # 尾


def build():
    M = byz.Model(W, D, H, MPV)
    M.band = (1.0, 1.4)
    M.band_z0 = 0.0
    rnd = random.Random(1204)
    # ── 面海的宮殿：y 0 ＝ 貼著海牆內側；地面層是拱頂下部結構（擋在海牆後面）、上層是開口那一層 ──
    x0, x1, y0, y1, zt = 3.0, 57.0, 2.0, 15.0, 19.0
    M.add(M.box(x0, x1, y0, y1, 0, zt), BANDED, 1)
    M.add(M.box(x0, x1, y0 - 0.0, y0 + 0.8, 9.0, 9.6), MARBLE, 1)                                          # 開口那一層的腰線
    # 屋頂塌了：牆頂高低不齊（一段段往下咬）、樓板只剩東半
    for k in range(18):
        cx = x0 + 1.0 + k * 3.0
        bite = 0.6 + rnd.random() * 3.4 if k < 12 else rnd.random() * 1.2
        if 13.0 <= cx <= 38.0:
            bite = min(bite, 2.2)                                    # 開口上面的過梁要留著（不然那一截浮空）
        M.air(M.box(cx, cx + 1.8 + rnd.random(), y0 - 1, y1 + 1, zt - bite, 99))
    M.add(M.box(x0 + 36.0, x1, y0, y1, 9.0, 9.4), STONE, 1)
    # 三個大理石框的大開口（方框、上有過梁）＋托架陽台；西段一個門道
    for xc in (21.0, 27.5, 34.0):
        M.air(M.box(xc - 1.6, xc + 1.6, y0 - 1, y0 + 2.4, 10.0, 15.6))
        M.add(M.box(xc - 2.1, xc + 2.1, y0, y0 + 0.4, 9.6, 16.2) & ~M.box(xc - 1.6, xc + 1.6, y0 - 1, y0 + 1, 10.0, 15.6), MARBLE, 1)
    M.add(M.box(18.0, 37.5, y0 - 1.6, y0, 9.6, 10.0), MARBLE, 1)                                           # 陽台
    for xx in range(18, 38, 2):
        M.add(M.box(xx + 0.4, xx + 0.8, y0 - 1.4, y0, 8.6 + 0.0, 9.6) & (M.Z - 8.6 >= (M.Y - y0 + 1.4) * -0.7), STONE, 1)   # 托架
    M.air(M.box(9.0, 12.2, y0 - 1, y0 + 2.4, 10.0, 14.2))                                                  # 西段門道
    M.add(M.box(8.6, 12.6, y0, y0 + 0.4, 9.6, 14.6) & ~M.box(9.0, 12.2, y0 - 1, y0 + 1, 10.0, 14.2), MARBLE, 1)
    for xc in (43.0, 47.5, 52.0):                                                                          # 東段一排三窗（小）
        M.air(M.arch_open(xc, y0, 11.0, 14.6, 1.6, normal='y', depth=2.4))
    for lx in (15.0, 40.5):                                                                                # 兩端的獅像（面海，各自坐在一塊托架石板上）
        M.add(M.box(lx - 1.6, lx + 1.6, y0 - 1.8, y0, 9.6, 10.0), MARBLE, 1)
        M.add(M.box(lx - 0.3, lx + 0.3, y0 - 1.4, y0, 8.4, 9.6) & (M.Z - 8.4 >= (M.Y - y0 + 1.4) * -0.8), STONE, 1)
        lion(M, lx, y0 - 0.9, 10.0, lay=1)
    M.air(M.box(x0 + 1.4, x1 - 1.4, y0 + 1.4, y1 - 1.4, 9.6, 99) & ~M.box(x0 + 36.0, x1, y0, y1, 0, 9.6))   # 上層裡面空了（屋頂塌了）
    for xc in range(6, 56, 6):                                                                             # 背面朝台地的拱（下部結構的入口，有幾個塌了）
        M.air(M.arch_open(xc, y1, 0, 6.4, 3.6, normal='y', depth=2.4))
    M.MAT[M.S & M.full(M.Z < 2.0) & (M.MAT == BANDED)] = STONE
    # ── 台地上的廢墟：兩排拱頂下部結構（一排還有頂、一排塌了）、斷牆、倒下的柱、碎石 ──
    R = 2
    for k in range(5):                                                                                     # 拱頂下部結構：沿 y 的筒形拱，跨 5 m
        bx = 6.0 + k * 9.0
        M.add((M.box(bx, bx + 1.2, 16.0, 30.0, 0, 4.6) | M.box(bx + 6.2, bx + 7.4, 16.0, 30.0, 0, 4.6)), BANDED, R)
        if k in (1, 2, 4):
            M.add(M.barrel(bx, bx + 7.4, 16.0, 30.0 if k != 2 else 22.0, 4.6, 'y', 3.0) & ~M.barrel(bx + 1.2, bx + 6.2, 15.0, 31.0, 4.6, 'y', 2.4), BRICK, R)
    for (ax, ay, aw, ad, ah) in ((2.0, 33.0, 22.0, 1.4, 5.5), (30.0, 34.0, 26.0, 1.2, 3.2), (56.6, 14.0, 1.4, 20.0, 6.5), (2.0, 14.0, 1.2, 14.0, 4.0)):
        M.add(M.box(ax, ax + aw, ay, ay + ad, 0, ah), BANDED, R)
        for j in range(int(max(aw, ad) // 2.5)):                                                           # 斷牆頂
            cx = j * 2.5
            if ad < aw:
                M.air(M.box(ax + cx, ax + cx + 1.2, ay - 1, ay + ad + 1, ah - rnd.random() * ah * 0.6, 99))
            else:
                M.air(M.box(ax - 1, ax + aw + 1, ay + cx, ay + cx + 1.2, ah - rnd.random() * ah * 0.6, 99))
    for (cx, cy, h_) in ((48.0, 18.0, 6.0), (51.0, 18.0, 3.8), (48.0, 24.0, 6.0)):                         # 還立著的柱
        M.add(M.cyl(cx, cy, 0.35, 0, h_), MARBLE, R)
        M.add(M.box(cx - 0.5, cx + 0.5, cy - 0.5, cy + 0.5, h_, h_ + 0.4), MARBLE, R)
    for (cx, cy, L_) in ((44.0, 28.0, 5.2), (52.0, 30.0, 4.6)):                                            # 倒下的柱
        M.add(((M.Y - cy) ** 2 + (M.Z - 0.35) ** 2 < 0.35 ** 2) & (M.X >= cx) & (M.X < cx + L_), MARBLE, R)
    for k in range(40):                                                                                    # 碎石堆
        cx, cy = 3.0 + rnd.random() * 52.0, 15.0 + rnd.random() * 19.0
        r = 0.6 + rnd.random() * 1.4
        M.add(M.dome(cx, cy, 0.0, r, r * 0.45), STONE if k % 3 else BRICK, R)
    M.add(M.box(0, W, 15.0, D, 0, 0.2), byz.GREEN, R, over=False)                                         # 台地上長滿草（不然遊戲的石基頂是一片灰）
    for (tx, ty, th, tw) in ((14.0, 31.0, 7.0, 5.0), (27.0, 25.0, 6.0, 4.4), (40.0, 32.0, 8.0, 6.0), (55.0, 32.0, 5.0, 3.6)):
        M.tree(tx, ty, th, tw, 3)
    G, L = M.finish(shell_m=0.8, seed=1204, mix=True)
    anchors = {'lot-0': [0, 0, 0], 'loggia': M.cell(27.5, 0.2, 10.0)}
    return G, L, anchors, {'立面牆頂（m）': zt, '開口那一層（m）': 10.0}
