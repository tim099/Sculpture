# 資源建築 C 酒與糖（TASK-0928；Tim 2026-10-25「/scp-task 928 GO」，gura 開單）—— 三種，全部共用 common：
#   葡萄園主建築（vineyard）、釀酒坊（winery）、糖廠（sugar-works）。
# 工具同 apex-one-industry-01m/design 的 industry.py（＋ trailhead-harbour-01m 的 workshops2／workshops／town3／quay ＋ ame-carib-civic-01m ＋ summit-carib-01m 的全部）。
#   座標同 kit.py：x 臨路寬、y 進深（y 0 臨路）、z 往上；0.1 m／格；作品框 ＝ 地塊、⛔ 什麼都不伸出框。
# 地塊照 Blocksail world/buildings.js 的 lot：葡萄園 10 × 10（後緣接葡萄田 annex）、釀酒坊 10 × 12、糖廠 16 × 12。
# 配方：葡萄園 grapes、釀酒坊 wine（TASK-0917，gura 那一側還沒合進 main）；糖廠 sugar（PRODUCTION）。
# 史料：作品 references/README.md；這一批沒有上網查 ⇒ 配置是設計（照 17 世紀前後地中海與加勒比海的通法），寫在那一份。
import os, sys, math

WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AP1 = os.path.join(WORKS, 'apex-one-industry-01m', 'design')
if AP1 not in sys.path:
    sys.path.insert(1, AP1)
from industry import *                                                 # noqa: F401,F403,E402  heap、cord、wheelbarrow、shovel、yard_ground、stone_block ＋ workshops2 的全部

GRAPE = 98                       # 葡萄（紫）
MUST = 97                        # 葡萄汁、新酒（暗紅紫）
POMACE = 64                      # 壓過的葡萄渣（暗紅褐）
WICKER = 176                     # 柳條筐（同茅草 B 那一色）
CANE = 148                       # 甘蔗（⛔ 188 在遊戲裡是螢光綠，meadow 改過）
CANE_TIP = 177                   # 甘蔗的切口（淺）
BAGASSE = 176                    # 榨過的蔗渣（乾的稻草色）
SYRUP = (177, 172, 136, 100, 64)  # 煮糖鍋一列：從生汁（淺）到快成糖的糖漿（深）
MOLASSES = 64                    # 糖蜜（暗）
POT = BRICK_D                    # 陶的糖模（倒放的圓錐）
SUGAR = SACK                     # 糖模口露出來的糖（米白）
JUICE = 177                      # 剛榨的蔗汁


def basket(M, cx, cy, z0, r=3.2, h=4, fill=GRAPE, layer='body'):
    """柳條筐：一圈筐壁、裡面裝滿 fill，頂上再堆一層（中間鼓起）。"""
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                M.box(layer, x, y, z0, x + 1, y + 1, z0 + h, WICKER if d > r - 1 else fill)
                if d < r - 1.6:
                    M.put(layer, x, y, z0 + h, fill)


def cask(M, cx, y0, y1, cz, r, layer='body'):
    """躺著的大酒桶（沿 y）：中段鼓起、桶板深淺一根一根換、四道鐵箍、兩端淺色的桶底；下面兩座木托架（從地面 z 1 頂到桶底）。"""
    n = y1 - y0
    hoops = {y0 + 1, y0 + 4, y1 - 5, y1 - 2}
    for y in (y0 + 3, y1 - 4):                                           # 托架先畫（桶蓋過它 ⇒ 兩者相接）
        M.box(layer, int(cx - r * 0.8), y, 1, int(cx + r * 0.8) + 1, y + 2, int(cz - r * 0.6) + 1, FRAME)
    for y in range(y0, y1):
        t = (y - y0 + 0.5) / n
        rr = r * (0.86 + 0.14 * math.sin(math.pi * t))
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.hypot(x + 0.5 - cx, z + 0.5 - cz)
                if d <= rr:
                    if y in (y0, y1 - 1):
                        col = LOG_TIP if d < rr - 1 else FRAME
                    elif y in hoops:
                        col = IRON
                    else:
                        a = int((math.atan2(z + 0.5 - cz, x + 0.5 - cx) + math.pi) / (2 * math.pi) * 18)
                        col = FRAME if a % 2 else BOARD_D
                    M.put(layer, x, y, z, col, force=True)


# ─────────────────────────────── 葡萄園 10 × 10 m ───────────────────────────────
def vineyard():
    """葡萄園（vineyard）主建築：田（annex）長在地塊後面，這一件只做院子 —— 左前一間毛石的小屋（看園的人、放工具；木瓦兩坡頂）；
    右邊一座開敞的木瓦壓榨棚：棚下一口架高的毛石踩葡萄槽（滿滿的葡萄、一角已經踩出汁）、槽口的出汁嘴接一個木桶，棚後一具籃式壓榨機（縫隙透出葡萄的板條籃、螺桿、橫梁）；
    院子裡一筐一筐的葡萄、一台載筐的手推車、空筐疊、壓過的葡萄渣堆；後緣敞開、一條踩出來的路通到田裡。
    - 照什麼：踩葡萄的槽（lagar／treading floor）、籃式螺桿壓榨機是地中海一帶 17 世紀前後的通法〔通論、沒上網查〕；尺寸、擺法是設計。"""
    X, Y, Z = 100, 100, 60
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 98, 98, salt=9281)
    for y in range(56, 98):                                                      # 通到田裡的路（踩實、深一點）
        for x in range(44, 56):
            M.put('body', x, y, 0, CLAY_D if h01('vp', x // 2, y // 2) < 0.6 else EARTH, True)
    # 左前：毛石小屋 3.4 × 3.6 m
    R = (6, 8, 40, 44)
    rubble_walls(M, R, 0, 28, 4, salt=9282)
    for x0, x1 in ((R[0], R[0] + 4), (R[2] - 4, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 28, 0.6, z0=28, color=RUBBLE, edge=RUBBLE_D)
    put_part(M, 'door-plank', '前-門', 'front', R, 23, 1, 4)
    put_part(M, 'window-board', '右-窗', 'right', R, 26, 11, 4)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 28, 'p': 0.6, 'over': (3, 3, 3, 3), 'gable': 'x'}], salt=9283)
    trestle_table(M, 12, 30, 34, 40, 8)                                          # 屋裡靠後牆的桌（剪刀、筐）
    # 右邊：開敞的壓榨棚（屋脊沿 x），六根柱
    S = (48, 10, 94, 58)
    top = shingle_roof(M, [{'x0': S[0], 'y0': S[1], 'x1': S[2], 'y1': S[3], 'ze': 30, 'p': 0.55, 'over': (2, 2, 3, 2), 'gable': 'x'}], salt=9284)
    roof_posts(M, top, [(x, y) for x in (S[0], S[2] - 2) for y in (S[1], 32, S[3] - 2)])
    # 踩葡萄的槽：毛石砌、高 0.8 m；槽裡滿滿的葡萄，右前角踩出一灘汁
    T = (54, 18, 88, 40)
    stone_block(M, T[0], T[1], 0, T[2], T[3], 8, salt=9285)
    for x in range(T[0] + 3, T[2] - 3):
        for y in range(T[1] + 3, T[3] - 3):
            M.box('body', x, y, 6, x + 1, y + 1, 8, MUST if (x > 76 and y < 26) else (GRAPE if h01('gr', x, y) < 0.85 else POMACE), force=True)
            if not (x > 76 and y < 26) and h01('gr2', x // 2, y // 2) < 0.5:
                M.put('body', x, y, 8, GRAPE)
    M.box('body', 70, 14, 4, 72, 18, 5, FRAME, force=True)                       # 出汁嘴
    M.box('body', 70, 14, 5, 72, 15, 6, FRAME, force=True)
    tub(M, 71, 9.5, 1, 5, 3.6, MUST)                                             # 接汁的木桶（坐在院子地上）
    # 籃式壓榨機（棚後）：板條籃（留縫、裝滿葡萄）、蓋板、螺桿、兩根柱撐的橫梁
    bx, by = 70, 50
    barrel_shell(M, bx, by, 1, 9, 5.5, 5.5, gap=True, hoops=(2, 7))
    for x in range(bx - 6, bx + 7):
        for y in range(by - 6, by + 7):
            if math.hypot(x + 0.5 - bx, y + 0.5 - by) < 4.6:
                M.box('body', x, y, 1, x + 1, y + 1, 9, GRAPE)
                M.put('body', x, y, 9, FRAME)
    M.box('body', bx - 9, by - 7, 0, bx + 9, by + 7, 1, FRAME, force=True)      # 底下的木台（接汁的淺盤）
    for xa in (bx - 9, bx + 7):
        M.box('body', xa, by - 1, 1, xa + 2, by + 1, 24, FRAME)
    M.box('body', bx - 9, by - 1, 22, bx + 9, by + 1, 25, FRAME)
    rod(M, (bx, by, 10), (bx, by, 22), 1.2, IRON, IRON)                         # 螺桿
    rod(M, (bx - 6, by, 18.5), (bx + 6, by, 18.5), 0.7, FRAME, FRAME)          # 轉螺桿的橫棍
    # 院子：一筐一筐的葡萄、載筐的手推車、空筐疊、葡萄渣堆
    for (x, y) in ((50, 46), (58, 48), (52, 54), (90, 50), (88, 64)):
        basket(M, x, y, 1)
    wheelbarrow(M, 24, 60, GRAPE)
    for x in range(10, 18):                                                      # 空筐疊（倒扣、三個疊一個）：實心 ⇒ 不封出空腔（第一版只有筐壁＋頂，裡面關了 192 格）
        for y in range(78, 86):
            d = math.hypot(x + 0.5 - 14, y + 0.5 - 82)
            if d <= 3.6:
                for k in range(3):
                    M.box('body', x, y, 1 + k * 4, x + 1, y + 1, 5 + k * 4, WICKER)
                    if d > 2.6:
                        M.put('body', x, y, 4 + k * 4, FRAME)                    # 每個筐口一圈深色的邊
    heap(M, 76, 84, 12, 9, 7, lambda x, y, z: POMACE if h01('pm', x, y, z) < 0.75 else MUST, z0=1)
    M.models += [{'name': '酒桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, y, 1], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, (x, y) in enumerate(((10, 50), (22, 50)))]
    lantern(M, '燈籠-棚', (S[0], S[1], 20))
    M.anchor('door', 23, R[1] - 1, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'vineyard', 'title': '葡萄園（共用：毛石的看園小屋；開敞的壓榨棚、毛石踩葡萄槽、籃式壓榨機；一筐筐葡萄、手推車、葡萄渣堆；後緣通到葡萄田）',
            'use': 'vineyard', 'lot': (10, 10), 'M': M, 'style': 'common', 'layers': {'body': '小屋、壓榨棚與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 釀酒坊 10 × 12 m ───────────────────────────────
def winery():
    """釀酒坊（winery）：臨路一座毛石的酒坊（8.8 × 5.2 m、木瓦兩坡頂、雙扇大貨門），裡面三個躺在木托架上的大酒桶（從貨門看得到中間那一個）；
    後院一座開敞的單坡棚，棚下一具橫梁壓榨機（一端插在兩根柱之間、另一端吊著螺桿與石墜，梁下的石台上一餅壓扁的葡萄渣、汁從石台的嘴流進木桶）；
    右後角斜蓋著兩扇木板門的酒窖口（毛石框）、兩個直立的大發酵桶、一排酒桶。
    - 照什麼：橫梁壓榨機（beam press：一端固定、一端用螺桿與石墜往下拉）是地中海葡萄酒的老式壓榨〔通論、沒上網查〕；地挖不下去 ⇒ 酒窖只做斜蓋的入口（設計）。"""
    X, Y, Z = 100, 120, 70
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 98, 118, salt=9291)
    # 臨路：毛石酒坊
    R = (6, 6, 94, 58)
    rubble_walls(M, R, 0, 34, 4, salt=9292)
    for x0, x1 in ((R[0], R[0] + 4), (R[2] - 4, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 34, 0.6, z0=34, color=RUBBLE, edge=RUBBLE_D)
    put_part(M, 'cartdoor', '前-貨門', 'front', R, 50, 1, 4)
    put_part(M, 'window-board', '前-窗-左', 'front', R, 20, 13, 4)
    put_part(M, 'window-board', '前-窗-右', 'front', R, 80, 13, 4)
    put_part(M, 'window-board', '左-窗', 'left', R, 32, 13, 4)
    put_part(M, 'window-board', '右-窗', 'right', R, 32, 13, 4)
    top = shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 34, 'p': 0.6, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=9293)
    for cx in (22, 50, 78):                                                      # 三個大酒桶（沿 y 躺著，直徑 1.6 m、長 3 m）
        cask(M, cx, 20, 50, 10, 8)
    # 後院：單坡棚（高的一邊靠酒坊）＋ 橫梁壓榨機
    S = (8, 64, 66, 112)
    top2 = shed_roof(M, S[0], S[1], S[2], S[3], 32, 0.2, low='back', color_fn=lambda x, y, f, r, e: shingle_color(x, y, f, r, e, 9294))
    roof_posts(M, top2, [(x, y) for x in (S[0], 34, S[2] - 2) for y in (S[1], S[3] - 2)])
    stone_block(M, 24, 80, 0, 48, 98, 6, salt=9295)                              # 壓榨的石台
    M.box('body', 27, 83, 6, 45, 95, 10, POMACE)                                 # 一餅壓扁的葡萄渣
    M.box('body', 26, 82, 10, 46, 96, 11, FRAME)                                 # 蓋板
    M.box('body', 33, 86, 11, 39, 93, 14, FRAME)                                 # 墊木（頂著梁）
    for ya in (82, 93):                                                          # 固定端：兩根柱夾住梁、上面一道橫木
        M.box('body', 10, ya, 0, 14, ya + 3, 24, FRAME)
    M.box('body', 10, 82, 20, 14, 96, 23, FRAME)
    M.box('body', 57, 84, 0, 68, 95, 8, RUBBLE)                                  # 石墜（螺桿穿過）
    rod(M, (12.5, 89.5, 16.5), (64.5, 89.5, 16.5), 2.4, LOG, LOG_TIP)          # 橫梁
    rod(M, (62.5, 89.5, 1), (62.5, 89.5, 24), 1.4, FRAME, FRAME)               # 螺桿（頂在棚頂底下：那裡棚頂只有 2.6 m；第一版拉到 3 m 穿出棚頂）
    rod(M, (56.5, 89.5, 22.5), (68.5, 89.5, 22.5), 0.7, FRAME, FRAME)          # 轉螺桿的橫棍
    M.box('body', 35, 98, 3, 37, 102, 4, FRAME, force=True)                      # 石台的出汁嘴
    tub(M, 36, 105.5, 1, 6, 4.5, MUST)                                           # 接汁的木桶
    # 右邊：兩個直立的大發酵桶
    for cy in (72, 88):
        tub(M, 82, cy, 1, 18, 7, MUST)
    # 右後角：斜蓋的酒窖口（毛石框、兩扇木板門、鐵環）
    C = (72, 98, 94, 116)
    for y in range(C[1], C[3]):
        zt = 4 + (y - C[1]) * 8 // (C[3] - C[1] - 1)
        for x in range(C[0], C[2]):
            side = x < C[0] + 3 or x >= C[2] - 3 or y >= C[3] - 3
            if side:
                M.box('body', x, y, 0, x + 1, y + 1, zt + 2, RUBBLE if (x + y + zt) % 5 else MORTAR)
            else:
                M.box('body', x, y, 0, x + 1, y + 1, zt, DARK)                   # 門底下（實心、看不到）
                M.put('body', x, y, zt, FRAME if x in (82, 83) else (BOARD_D if (x - C[0]) % 4 == 0 else BOARD))
    for x in (78, 87):                                                           # 拉門的鐵環：貼在那一排門板上面一格
        M.put('body', x, 104, 4 + (104 - C[1]) * 8 // (C[3] - C[1] - 1) + 1, IRON, True)
    M.models += [{'name': '酒桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, y, 1], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, (x, y) in enumerate(((10, 116), (22, 116), (64, 64), (64, 76)))]
    lantern(M, '燈籠-門', (68, R[1], 22))
    M.anchor('door', 50, R[1] - 1, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'winery', 'title': '釀酒坊（共用：毛石的酒坊、雙扇貨門、裡面三個躺著的大酒桶；後院棚下的橫梁壓榨機與石墜、兩個大發酵桶、斜蓋的酒窖口、一排酒桶）',
            'use': 'winery', 'lot': (10, 12), 'M': M, 'style': 'common', 'layers': {'body': '酒坊、壓榨機與擺設', 'roof': '屋頂'}}


# ─────────────────────────────── 糖廠 16 × 12 m ───────────────────────────────
def sugar_works():
    """糖廠（sugar-works）：17 世紀加勒比海糖莊的三件事在同一塊地 ——
    ① 左前牛拉的磨坊：四坡茅草頂（八根柱）下一座三根直立滾筒的榨蔗機（木架、包鐵的滾筒），中間那根往上接兩根長的推桿（牛繞圈拉）、地上一圈踩出來的牛道；
       榨出的汁沿一道木槽流進煮糖房；
    ② 右邊毛石的煮糖房（7 × 5.8 m、木瓦兩坡頂）：靠後牆一條毛石爐台，台上五口一口比一口小的銅鍋（從淺的生汁到深的糖漿）、
       後牆外每口鍋底下一個紅的火口、右後角一根穿出屋頂的毛石煙囪；左前接汁的石槽；
    ③ 左後開敞的茅草養糖棚：兩排木架上一排排倒放的陶糖模（口上露出白糖）、架下滴糖蜜的槽；棚前幾桶糖蜜；
       煮糖房後面一大堆曬乾的蔗渣（燒火用）、磨坊旁一堆綁好的甘蔗。
    - 照什麼：三滾筒直立榨蔗機（牛力）、一列由大到小的銅鍋（the train）、陶糖模養糖滴糖蜜是 17 世紀巴貝多、牙買加糖莊的通法（Ligon 1657 寫過這一套〔記得、這一輪沒有翻〕）；
      史實的煮糖房、養糖房、磨坊是三座分開的大房子 ⇒ 縮在一塊 16 × 12 m 的地上（設計）；水車、風車磨坊不做（城裡沒有水路）。"""
    X, Y, Z = 160, 120, 80
    M = Model((X, Y, Z))
    yard_ground(M, 2, 2, 158, 118, salt=9301)
    # ① 磨坊：中心 (40, 40)、牛道半徑 2.2～2.8 m
    cx, cy = 40, 40
    for x in range(cx - 30, cx + 31):
        for y in range(cy - 30, cy + 31):
            if 22 <= math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= 28 and h01('ox', x // 2, y // 2) < 0.8:
                M.put('body', x, y, 0, CLAY_D, True)
    top = thatch_roof(M, [{'x0': 10, 'y0': 10, 'x1': 70, 'y1': 70, 'ze': 30, 'p': 0.55, 'over': (2, 2, 2, 2), 'gable': None}], salt=9302)
    roof_posts(M, top, [(10, 10), (68, 10), (10, 68), (68, 68), (38, 10), (38, 68), (10, 38), (68, 24), (68, 54)])
    M.box('body', 26, 34, 1, 54, 46, 4, FRAME)                                   # 榨蔗機的木座
    for xa in (26, 51):
        M.box('body', xa, 37, 4, xa + 3, 44, 20, FRAME)                          # 兩側立柱
    M.box('body', 26, 37, 20, 54, 44, 23, FRAME)                                 # 頂梁
    for rx in (31.5, 40.5, 49.5):                                                # 三根包鐵的滾筒
        rod(M, (rx, 40.5, 4), (rx, 40.5, 20), 3.2, IRON, IRON)
    rod(M, (40.5, 40.5, 23), (40.5, 40.5, 30), 2.4, FRAME, FRAME)              # 中間那根往上的軸
    rod(M, (40.5, 40.5, 27.5), (14.5, 40.5, 24.5), 1.2, FRAME, FRAME)          # 兩根推桿（牛拉）
    rod(M, (40.5, 40.5, 27.5), (66.5, 40.5, 24.5), 1.2, FRAME, FRAME)
    M.box('body', 54, 38, 2, 90, 44, 4, FRAME)                                   # 汁槽（木）：從榨蔗機流到煮糖房
    M.box('body', 55, 39, 3, 90, 43, 4, JUICE, force=True)
    for k in range(3):                                                           # 榨過、塞在機前的一把蔗
        rod(M, (24.5, 36.5 + k * 3, 6), (8.5, 34.5 + k * 3, 1.5), 0.8, BAGASSE, BAGASSE)
    # 磨坊旁：綁好的甘蔗一堆（沿 x、兩層）
    for k in range(5):
        for j in range(2):
            rod(M, (4.5, 76.5 + k * 1.6, 1.5 + j * 1.6), (34.5, 76.5 + k * 1.6, 1.5 + j * 1.6), 0.9, CANE, CANE_TIP)
    # ② 煮糖房
    R = (84, 24, 154, 82)
    rubble_walls(M, R, 0, 34, 4, salt=9303)
    for x0, x1 in ((R[0], R[0] + 4), (R[2] - 4, R[2])):
        end_gable(M, x0, x1, R[1], R[3], 34, 0.6, z0=34, color=RUBBLE, edge=RUBBLE_D)
    put_part(M, 'door-double', '前-門', 'front', R, 118, 1, 4)
    put_part(M, 'window-board', '前-窗-左', 'front', R, 98, 13, 4)
    put_part(M, 'window-board', '前-窗-右', 'front', R, 140, 13, 4)
    put_part(M, 'window-board', '右-窗', 'right', R, 46, 13, 4)
    top2 = shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 34, 'p': 0.6, 'over': (3, 3, 4, 3), 'gable': 'x'}], salt=9304)
    stone_block(M, 88, 30, 0, 100, 48, 8, salt=9305)                             # 接汁的石槽（汁槽穿過左牆流進來）
    M.box('body', 90, 32, 6, 98, 46, 8, JUICE, force=True)
    M.box('body', 84, 39, 3, 90, 43, 4, JUICE, force=True)
    stone_block(M, 100, 58, 0, 150, 78, 10, salt=9306)                           # 爐台（靠後牆）
    kettles = [(106, 5.5), (117, 5.0), (127, 4.5), (136, 4.0), (144, 3.5)]
    for i, (kx, r) in enumerate(kettles):
        for x in range(int(kx - r - 1), int(kx + r + 2)):
            for y in range(int(68 - r - 1), int(68 + r + 2)):
                d = math.hypot(x + 0.5 - kx, y + 0.5 - 68)
                if d <= r:
                    M.put('body', x, y, 9, COPPER if d > r - 1 else SYRUP[i], True)
                    if d > r - 1:
                        M.put('body', x, y, 10, COPPER, True)                    # 鍋緣
        M.clear(kx - 2, 79, 1, kx + 3, 82, 7)                                    # 後牆外的火口（往裡到牆的最裡一層是紅的火）
        M.box('body', kx - 2, 78, 1, kx + 3, 79, 7, EMBER, force=True)
    zc = max(top2.get((x, y), 34) for x in range(140, 150) for y in range(72, 86)) + 10
    M.box('body', 140, 76, 0, 150, 86, zc, RUBBLE, force=True)                   # 煙囪（騎在後牆上）
    M.box('body', 139, 75, zc - 2, 151, 87, zc, MORTAR, force=True)
    M.box('body', 143, 79, zc - 2, 147, 83, zc, CHAR, force=True)
    M.anchor('smoke', 145, 81, zc - 1)
    # ③ 養糖棚（左後）：兩排木架、倒放的陶糖模、架下的糖蜜槽
    lean_roof_posts(M, 4, 86, 80, 116, 28, 0.25, 'back', thatch_color, [(4, 86), (40, 86), (78, 86), (4, 114), (40, 114), (78, 114)], salt=9307)
    for ry in (92, 104):
        for xa in (10, 40, 72):
            M.box('body', xa, ry, 0, xa + 2, ry + 7, 6, FRAME)                   # 架腳
        M.box('body', 10, ry, 6, 74, ry + 7, 7, FRAME)                           # 架面
        M.box('body', 12, ry + 2, 1, 72, ry + 5, 2, FRAME)                       # 糖蜜槽
        M.box('body', 13, ry + 3, 1, 71, ry + 4, 2, MOLASSES, force=True)
        for px in range(16, 70, 7):                                              # 倒放的糖模（尖朝下、口朝上露出白糖）
            for dz in range(6):
                rr = 1.2 + dz * 0.5
                for x in range(int(px - rr - 1), int(px + rr + 2)):
                    for y in range(int(ry + 3.5 - rr - 1), int(ry + 3.5 + rr + 2)):
                        d = math.hypot(x + 0.5 - px, y + 0.5 - ry - 3.5)
                        if d <= rr:
                            M.put('body', x, y, 7 + dz, SUGAR if (dz == 5 and d < rr - 1) else POT)
    # 煮糖房後面：曬乾的蔗渣一大堆（燒火用）
    heap(M, 128, 104, 22, 10, 12, lambda x, y, z: BAGASSE if h01('bg', x, y, z) < 0.8 else THATCH_A, z0=1)
    M.models += [{'name': '糖蜜桶-%d' % (i + 1), 'source': 'summit-rocher-01m-barrel', 'at': [x, y, 1], 'pivot': [6, 6, 0], 'meta': {}}
                 for i, (x, y) in enumerate(((86, 96), (86, 108), (98, 102)))]
    lantern(M, '燈籠-門', (132, R[1], 22))
    M.anchor('door', 118, R[1] - 1, 1)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'sugar-works', 'title': '糖廠（共用：牛拉的三滾筒榨蔗磨坊與茅草頂、汁槽；毛石的煮糖房、爐台上五口銅鍋、後牆外的火口與煙囪；茅草養糖棚裡倒放的陶糖模與糖蜜槽；蔗渣堆、甘蔗堆）',
            'use': 'sugar-works', 'lot': (16, 12), 'M': M, 'style': 'common', 'layers': {'body': '磨坊、煮糖房、養糖棚與擺設', 'roof': '屋頂'}}


ALL = [vineyard, winery, sugar_works]
