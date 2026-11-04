# 鹽田的沼澤鹽款、礦坑的鹽岩款（TASK-1199；Tim 2026-11-04「另外變體可以參考金礦 銀礦坑 外型稍微改變(子模組替換)」）——
#   Blocksail 多了兩種資源分布區（沼澤鹽 marsh-salt、鹽岩 rock-salt）與兩條配方：鹽田的 salt-marsh、礦坑的 rock-salt。
#   成品 meta recipes ⇒ townmodels 寫進索引 ⇒ 遊戲照地塊的配方挑這一款（同 ridge-two-mine-ores-01m 的金礦款、銀礦款）；一般曬鹽 salt、別的礦照舊用基礎款。
# 做法同金銀礦款（BUILDING_SPEC §6.31）：基礎款整座照生、再微調 —— 鹽池、鹽堆、礦石都在 body 那一層 ⇒ 不能只關聯基礎款的牆身 ⇒ 整座另存。
#   ① 沼澤鹽田：kotoko-grainsea-01m 的鹽田（grainsea.py saltpan()）整座照生 ——
#      鹽換成灰的海灣鹽（sel gris：鹽沼的泥讓鹽帶灰；結晶池、耙成的小堆、鹽倉與池邊的鹽堆、手推車上的鹽）；
#      池埂長鹽沼的草（海蓬子一類，綠、深綠一叢一叢）—— 一看就是泥灘上的鹽沼，不是乾燥海岸的鹽池
#   ② 鹽岩礦：apex-one-industry-01m 的礦坑（industry.py mine()）整座照生 ——
#      礦石換成淡粉、帶白的岩鹽；前院右半邊（原本空著）兩垛鑿成方塊的鹽磚＋一排鹽袋
# 史料〔通論，沒翻原典〕：大西洋岸（聖通日、布魯阿日、蓋朗德）的鹽沼一級一級引潮水、結晶池耙出來的鹽帶灰（sel gris）；
#   岩鹽在礦裡鑿成塊運出（加泰隆尼亞的卡多納鹽山、波蘭的維利奇卡）—— 塊的大小、垛法是設計。
import os, sys
_W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _d in (os.path.join(_W, 'apex-one-industry-01m', 'design'), os.path.join(_W, 'kotoko-grainsea-01m', 'design')):
    if _d not in sys.path:
        sys.path.insert(1, _d)
from industry import *                                                 # noqa: F401,F403,E402
from industry import mine as _mine                                     # noqa: E402
from grainsea import saltpan as _saltpan, SALT, SALT_D                 # noqa: E402

GREY, GREY_D = 182, 146          # 灰的海灣鹽（sel gris；淺灰米、深一點帶藍）—— 同毛石那兩色
WEED, WEED_D = GRASS, GRASS_D    # 鹽沼的草（76、44）
ROCK, ROCK_P = 250, 246          # 岩鹽（淡橘白、偏粉）；亮面 SALT 255


# 工作點（BUILDING_SPEC §5 work-*）：基礎款作品上登記的點（tools/workspots.py 挑的、手補的）照抄 —— 外型只換色、加的東西不壓到它們
#   ⇒ 鹽田照 kotoko-grainsea-01m-saltpan、礦坑照 apex-one-industry-01m-mine（2026-11-04 讀的），礦坑另外在鹽磚垛前補兩點
SALTPAN_WORK = {'a1': ((52, 25, 1), (59, 22, 10)), 'b1': ((66, 32, 0), (64, 25, 9)), 'c1': ((90, 35, 0), (90, 27, 9)), 'd1': ((78, 6, 0), (72, 13, 9)),
                'd2': ((94, 13, 0), (91, 21, 9)), 'e1': ((112, 36, 0), (104, 28, 9)), 'd3': ((112, 15, 0), (104, 23, 9)),
                'f1': ((35, 85, 2), (35, 95, 11)), 'f2': ((60, 95, 2), (60, 105, 11)), 'f3': ((85, 85, 2), (85, 95, 11))}
MINE_WORK = {'f1': ((83, 74, 1), (84, 82, 10)), 'b1': ((47, 49, 1), (55, 46, 10)), 'a2': ((72, 50, 1), (64, 47, 10)), 'a3': ((71, 36, 1), (64, 42, 10)),
             'b2': ((39, 63, 1), (32, 59, 10)), 'c1': ((20, 84, 1), (24, 92, 10)), 'b3': ((48, 35, 1), (56, 42, 10)), 'd1': ((24, 46, 1), (24, 54, 10)),
             'e1': ((85, 51, 1), (85, 44, 10)), 'e2': ((104, 51, 1), (104, 44, 10))}   # e：鹽磚垛前（本作品加的）；基礎款的 a1 改成 f1 —— 跟 a2、a3 中間隔著鹽袋與鹽磚垛（直線走不過去）


def _work(M, W):
    for k, (at, to) in W.items():
        assert at not in M.cells, '工作點 %s 在實心裡：%s' % (k, at)
        M.anchor('work-' + k, *at)
        M.anchor('work-' + k + '-to', *to)


def _free(M, x0, y0, x1, y1):
    """這塊地（z ≥ 1）原本是空的 ⇒ 新加的東西不會跟基礎款撞。"""
    hit = [k for k in M.cells if x0 <= k[0] < x1 and y0 <= k[1] < y1 and k[2] >= 1]
    assert not hit, '撞到基礎款：%d 格，例 %s' % (len(hit), hit[:3])


def saltpan_marsh():
    """鹽田（沼澤鹽款）：鹽換成灰的海灣鹽；池埂長鹽沼的草。"""
    B = _saltpan()
    M = B['M']
    n = 0
    for k, (ly, c) in list(M.cells.items()):                          # 鹽（白 255、陰影面 218）⇒ 灰；只動 body 那一層（屋頂的 218 不是鹽）
        if ly == 'body' and c in (SALT, SALT_D):
            M.cells[k] = (ly, GREY_D if (c == SALT_D or h01('sg', *k) < 0.25) else GREY); n += 1
    assert n > 1000, '鹽的格太少（%d）⇒ 基礎款變了？' % n
    xs, ys = [4, 32, 60, 88, 116], [46, 68, 90, 112]
    for x in range(4, 116):                                             # 池埂（土埂 z 0、1）頂上一叢一叢的草：埂頂那一格換色、少數再長高一格
        for y in range(46, 114):
            if not (any(v - 1 <= x <= v for v in xs) or any(v - 1 <= y <= v for v in ys)):
                continue
            k = (x, y, 1)
            if k not in M.cells or M.cells[k][0] != 'body':
                continue
            r = h01('weed', x, y)
            if r < 0.45:
                M.cells[k] = ('body', WEED if r < 0.3 else WEED_D)
                if r < 0.12 and (x, y, 2) not in M.cells and not any(a[:2] == (x, y) for a, _ in SALTPAN_WORK.values()):
                    M.put('body', x, y, 2, WEED_D)
    B.update({'key': 'saltpan-marsh', 'variant': 'b', 'meta': {'recipes': 'salt-marsh'},
              'title': '鹽田（沼澤鹽款：灰的海灣鹽、池埂上鹽沼的草）'})
    _work(M, SALTPAN_WORK)
    M.notes.append('基礎款 kotoko-grainsea-01m（鹽田 saltpan()）整座照生、鹽換成灰的海灣鹽；池埂的草是本作品加的')
    return B


def mine_rocksalt():
    """礦坑（鹽岩款）：礦石換成淡粉帶白的岩鹽；前院右邊兩垛鹽磚、一排鹽袋。"""
    B = _mine()
    M = B['M']
    n = 0
    for k, (ly, c) in list(M.cells.items()):
        if c == ORE:
            r = h01('rs', *k)
            M.cells[k] = (ly, SALT if r < 0.15 else (ROCK_P if r < 0.45 else ROCK)); n += 1
    assert n > 100, '礦石的格太少（%d）' % n
    _free(M, 72, 34, 116, 68)
    # 鹽磚（0.6 × 0.4 m、高 0.3 m）兩垛：每垛 3 × 2 塊、三層，上一層橫著擺（交錯）
    for (x0, y0) in ((76, 38), (96, 38)):
        for z in range(3):
            for i in range(3):
                for j in range(2):
                    if z % 2 == 0:
                        bx, by, w, d = x0 + i * 6, y0 + j * 4, 6, 4
                    else:
                        bx, by, w, d = x0 + j * 9, y0 + i * 3, 9, 3
                    M.box('body', bx, by, 1 + z * 3, bx + w - 1, by + d - 1, 4 + z * 3, ROCK if (i + j + z) % 3 else ROCK_P)   # 塊與塊之間留一格縫
    for i, x in enumerate(range(76, 112, 7)):                           # 鹽袋（0.5 × 0.4 m、高 0.5 m）×5
        h = 6 + i % 2
        M.box('body', x, 56, 1, x + 5, 60, h, SACK)
        M.box('body', x + 1, 57, h, x + 4, 59, h + 1, ROPE)             # 紮口的繩
    B.update({'key': 'mine-rocksalt', 'variant': 'd', 'meta': {'recipes': 'rock-salt'},
              'title': '礦坑（鹽岩款：淡粉的岩鹽、鑿成塊的鹽磚、鹽袋）'})
    _work(M, MINE_WORK)
    M.notes.append('基礎款 apex-one-industry-01m（礦坑 mine()）整座照生、礦石換成岩鹽；鹽磚、鹽袋是本作品加的')
    return B


ALL = [saltpan_marsh, mine_rocksalt]
