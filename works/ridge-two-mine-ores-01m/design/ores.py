# 礦坑的金礦款、銀礦款（TASK-1018；Tim 2026-10-27「4 加微調子模型」）—— Blocksail 礦坑多了金礦 gold-ore、銀礦 silver-ore 兩條配方，
#   成品 meta recipes ⇒ townmodels 寫進索引 ⇒ 遊戲照地塊的配方挑這一款（同 meadow-farm 的作物款、gura-crops 的麻莊）；銅、鐵、硫磺、硝石照舊用基礎款。
# 照 apex-one-industry-01m 的礦坑（mine()：岩丘、坑道口、木軌與礦車、絞車、礦石堆、廢石堆、揀礦桌、工具棚）整座生出來，再微調：
#   ① 礦石換色（礦石堆、礦車、揀礦桌上的那幾塊）：金 ＝ 含金石英（白、帶金點）；銀 ＝ 暗灰的銀礦（輝銀礦、方鉛礦一類，帶銀光）
#   ② 前院右半邊（原本空著）各加一件看得出是哪一種礦的作業：
#      金：一道淘金槽（斜放的木槽、槽底一道道橫擋、上頭一隻水桶放水）＋三個淘金木盤（batea）
#      銀：一片石板院（patio）、上面攤一塊礦泥餅（torta）＋一排皮礦袋（zurrón）
# 礦石的礦礫堆在 body 那一層 ⇒ 不能像麻莊那樣只關聯基礎款的牆身、另畫作業區 ⇒ 整座另存（工具、色票全部借 apex-one 的 industry.py，自動 credit 寫在 notes）。
# 史料：
#   - 銀的 patio（汞齊法）：1550 年代 Bartolomé de Medina 在新西班牙推開，17 世紀美洲的銀大多這樣煉：礦石磨成泥、攤在石板院上加鹽與汞踩勻〔通論，沒翻原典〕。
#   - 金：加勒比海與中美洲的金多半是沖積金，用木槽沖洗、batea 木盤淘〔通論〕；含金石英脈要先搗碎再洗。
#   - 礦袋：西屬美洲的礦工用生皮袋（zurrón）背礦出坑〔通論〕。
import os, sys
_IND = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'apex-one-industry-01m', 'design')
if _IND not in sys.path:
    sys.path.insert(1, _IND)
from industry import *                                                 # noqa: F401,F403,E402
from industry import mine as _mine                                     # noqa: E402

QUARTZ = 255                     # 含金石英（白；同石灰）
GOLD = 248                       # 金點、淘出來的金砂（RGB332 7,6,0）
AG_ORE = SLAG                    # 銀礦（暗灰藍 73；同爐渣）
AG = 219                         # 銀光（淺灰帶藍；⛔ 182 ＝ 毛石 RUBBLE）
MUD = RUBBLE_D                   # 礦泥餅（灰 146）


def _reore(M, fn):
    """把基礎款所有礦石色（ORE）的格換成 fn(x, y, z) 給的色（同一層、同一格）。"""
    n = 0
    for k, (ly, c) in list(M.cells.items()):
        if c == ORE:
            M.cells[k] = (ly, fn(*k)); n += 1
    return n


def _free(M, x0, y0, x1, y1):
    """這塊地（z ≥ 1）原本是空的 ⇒ 新加的東西不會跟基礎款撞。"""
    hit = [k for k in M.cells if x0 <= k[0] < x1 and y0 <= k[1] < y1 and k[2] >= 1]
    assert not hit, '撞到基礎款：%d 格，例 %s' % (len(hit), hit[:3])


def _base(title):
    B = _mine()
    B.update({'title': title, 'variant': None})
    return B, B['M']


def mine_gold():
    """礦坑（金礦款）：礦石換成含金石英；前院右邊一道淘金槽（槽頭一隻水桶、斜下去的木槽、槽底的橫擋留住金砂）、三個淘金木盤。"""
    B, M = _base('礦坑（金礦款：含金石英的礦石堆與礦車、淘金槽、淘金木盤）')
    _reore(M, lambda x, y, z: GOLD if h01('au', x, y, z) < 0.12 else QUARTZ)
    _free(M, 72, 34, 116, 68)
    # 淘金槽：沿 x 從槽頭（x 80，高 1.4 m）斜到槽尾（x 110，高 0.6 m）；槽寬 0.7 m（y 44～51）、側板高 0.3 m
    for x in range(80, 112):
        z = 14 - (x - 80) * 8 // 31
        M.box('body', x, 44, z, x + 1, 51, z + 1, BOARD)                       # 槽底
        for y in (44, 50):
            M.box('body', x, y, z + 1, x + 1, y + 1, z + 4, BOARD_D)           # 側板
        M.put('body', x, 46 + (x % 3 == 0), z + 1, WATER) if x % 4 else M.box('body', x, 45, z + 1, x + 1, 50, z + 2, BOARD_D)   # 水、每 0.4 m 一道橫擋
        if x % 4 == 2:
            M.put('body', x, 47, z + 1, GOLD)                                  # 擋下來的金砂
    for (x, h) in ((82, 13), (95, 10), (108, 7)):                              # 槽腳（每一處兩根）
        for y in (44, 50):
            M.box('body', x, y, 1, x + 1, y + 1, h, FRAME)
    M.box('body', 72, 42, 1, 80, 53, 18, BOARD_D)                              # 槽頭的水桶（木桶，0.8 × 1.1 m、高 1.7 m）
    for z in (4, 10, 16):
        M.box('body', 72, 42, z, 80, 53, z + 1, IRON)                          # 鐵箍
    M.box('body', 73, 43, 17, 79, 52, 18, WATER)
    # 淘金木盤（batea：圓的淺木盤，底下一圈金砂）×3，擱在槽尾邊的地上
    for i, (cx, cy) in enumerate(((92, 60), (102, 61), (111, 58))):
        for x in range(cx - 4, cx + 5):
            for y in range(cy - 4, cy + 5):
                r2 = (x - cx) ** 2 + (y - cy) ** 2
                if r2 <= 16:
                    M.put('body', x, y, 1, BOARD_D)
                    if r2 >= 10:
                        M.put('body', x, y, 2, BOARD_D)                        # 盤緣
                    elif r2 <= 4:
                        M.put('body', x, y, 2, GOLD if h01('pan', i, x, y) < 0.5 else SAND)
    M.notes.append('基礎款 apex-one-industry-01m（礦坑 mine()）整座照生、礦石換成含金石英；淘金槽、淘金木盤是本作品加的')
    B.update({'key': 'mine-gold', 'variant': 'b', 'meta': {'recipes': 'gold-ore'}})
    return B


def mine_silver():
    """礦坑（銀礦款）：礦石換成暗灰帶銀光的銀礦；前院右邊一片石板院（patio）上攤一塊礦泥餅（torta），院邊一排皮礦袋。"""
    B, M = _base('礦坑（銀礦款：暗灰的銀礦、石板院上攤的礦泥餅、皮礦袋）')
    _reore(M, lambda x, y, z: AG if h01('ag', x, y, z) < 0.10 else AG_ORE)
    _free(M, 72, 34, 116, 68)
    stone_block(M, 76, 36, 0, 114, 60, 1, salt=9301)                           # 石板院（3.8 × 2.4 m、一層）
    for x in range(80, 110):                                                   # 礦泥餅（扁的、0.3 m 高，邊緣薄）
        for y in range(39, 57):
            e = min(x - 80, 109 - x, y - 39, 56 - y)
            for z in range(1, 1 + min(3, 1 + e // 2)):
                M.put('body', x, y, z, AG if h01('torta', x, y, z) < 0.06 else MUD, True)
    for i, x in enumerate(range(78, 112, 7)):                                  # 皮礦袋（0.5 × 0.4 m、高 0.5～0.6 m）×5
        h = 5 + i % 2
        M.box('body', x, 61, 1, x + 5, 65, h, HIDE)
        M.box('body', x + 1, 62, h, x + 4, 64, h + 1, ROPE)                    # 紮口的繩
    M.notes.append('基礎款 apex-one-industry-01m（礦坑 mine()）整座照生、礦石換成銀礦；石板院、礦泥餅、皮礦袋是本作品加的')
    B.update({'key': 'mine-silver', 'variant': 'c', 'meta': {'recipes': 'silver-ore'}})
    return B


ALL = [mine_gold, mine_silver]
