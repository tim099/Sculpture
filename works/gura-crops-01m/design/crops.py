# 新作物的農莊與種植園（TASK-0929；Blocksail TASK-0917 生產鏈新加的配方）：麻莊（農莊 recipe hemp）、龍舌蘭園（種植園 recipe sisal）。
# 照 meadow-farm-01m（BUILDING_SPEC §6.20）的拆法：牆身 body、屋頂 roof（種植園多木廊 gallery）**直接關聯 meadow 的基礎款那幾件**（不另存格子、自動 credit），
#   這裡只畫後半的作業區 work（y ≥ WORK_Y）；成品 meta recipes ⇒ townmodels 寫進索引 ⇒ 遊戲照地塊的配方挑這一款。
# 工具、色票、小件全部借 meadow 的 farm.py（⇐ apex-one-industry-01m ⇐ trailhead-harbour-01m ⇐ summit-carib-01m）。
# 史料：這一批沒有上網查 —— 配置是設計（浸麻、立著曬的麻束、打麻的木砧是歐洲鄉間處理纖維麻的通法；
#   龍舌蘭（cabuya、pita）的葉子刮成纖維、晾在繩上、紮成捆是加勒比與墨西哥的通法），寫在作品 notes。
from farm import *                                                     # noqa: F401,F403
from farm import _Shift                                                # noqa: E402
from industry import heap, stone_block                                 # noqa: E402

FIBER = 218                      # 麻、龍舌蘭的纖維（米白；同麻袋）
STALK, STALK_D = 177, 140        # 麻稈（淺黃褐）與泡過的深一點
AGAVE, AGAVE_D = 52, 32          # 龍舌蘭葉（綠、深綠；同菜的兩階）


def farm_hemp():
    """麻莊（纖維麻）：後院一口毛石圍的浸麻池（水裡泡著一捆捆麻、上面壓石頭）、一排立著曬的麻束堆、
    一座打麻的木砧（brake：架上一道木槽、上面一根可以掀起來的木顎）、砧下一堆打碎的麻屑、幾捆梳好的麻纖維。"""
    M = farm_base(farm_model())
    farm_work_ground(M, 9170)
    # 浸麻池（毛石 4.6 × 2.6 m、高 0.6 m；池底一層泥、水面低一格）
    x0, y0, x1, y1, h = 8, 72, 54, 98, 6
    stone_block(_Shift(M, 1), x0, y0, 0, x1, y1, h, salt=9171, layer='work')
    M.clear(x0 + 3, y0 + 3, 2, x1 - 3, y1 - 3, h + 2, 'work')
    M.box('work', x0 + 3, y0 + 3, 2, x1 - 3, y1 - 3, h - 1, DARK)
    M.box('work', x0 + 3, y0 + 3, h - 1, x1 - 3, y1 - 3, h, WATER)
    for i, y in enumerate(range(y0 + 5, y1 - 6, 6)):                              # 泡著的麻捆（沿 x、浮在水面一格）＋壓在上面的石頭
        M.box('work', x0 + 6, y, h, x1 - 6, y + 3, h + 1, STALK_D, True)
        M.box('work', x0 + 6 + (i % 2) * 8, y, h + 1, x0 + 10 + (i % 2) * 8, y + 3, h + 3, RUBBLE)
        M.box('work', x1 - 14 + (i % 2) * 4, y, h + 1, x1 - 10 + (i % 2) * 4, y + 3, h + 3, RUBBLE)
    # 立著曬的麻束堆（比麥束高瘦）
    for (x, y) in ((70, 76), (82, 78), (94, 76), (106, 78)):
        stook(M, x, y, 18)
    # 打麻的木砧：四條腿、上面一道木槽、一根木顎（一頭鉸在槽上、另一頭抬起來）
    for (x, y) in ((66, 100), (88, 100), (66, 106), (88, 106)):
        M.box('work', x, y, 1, x + 2, y + 2, 9, FRAME)
    M.box('work', 66, 100, 9, 90, 108, 10, BOARD)
    M.box('work', 67, 103, 10, 89, 105, 11, BOARD_D)                              # 槽
    rope_line(M, (68, 104, 11), (90, 104, 17), color=LOG, layer='work')           # 掀起來的木顎（六連通）
    heap(_Shift(M, 1), 78, 114, 12, 3, 3, lambda x, y, z: STALK_D if (x + y) % 3 else STALK, layer='work')   # 打碎的麻屑
    # 梳好的麻纖維（一束一束紮著、擱在木板上）
    M.box('work', 98, 96, 1, 116, 112, 3, BOARD)
    for i in range(4):
        y = 98 + i * 3
        M.box('work', 100, y, 3, 114, y + 2, 5, FIBER)
        M.box('work', 106, y, 3, 107, y + 2, 5, ROPE, True)
    basket(M, 60, 112, STALK)
    return {'key': 'farm-hemp', 'title': '麻莊（農莊：浸麻池、立著曬的麻束、打麻的木砧、梳好的麻纖維）', 'use': 'farm', 'lot': (12, 12), 'M': M, 'style': 'common',
            'layers': FARM_LAYERS, 'share': {'body': 'meadow-farm-01m-farm', 'roof': 'meadow-farm-01m-farm'}, 'variant': 'f', 'meta': {'recipes': 'hemp'}}


def plant_sisal():
    """龍舌蘭園（cabuya、pita）：後院茅草棚下刮纖維的長台（台上一片攤開的葉、一把木刮刀）、棚邊一堆砍下的龍舌蘭葉；
    兩道晾纖維的繩架（柱子、橫桿、掛滿一束一束米白的纖維）、一排紮好的纖維捆、一台裝著葉子的牛車。"""
    M = plant_base(plant_model())
    plant_work_ground(M, 9270)
    open_shed(M, 10, 72, 62, 98, 20, 9271)
    M.box('work', 14, 80, 1, 54, 86, 8, BOARD)                                    # 刮纖維的長台
    for x in range(16, 52, 6):                                                   # 台上攤開的葉（一片一片，刮過的那半截淡）
        M.box('work', x, 81, 8, x + 4, 85, 9, AGAVE if x < 34 else FIBER)
    M.box('work', 34, 85, 8, 36, 90, 9, FRAME)                                    # 木刮刀（一頭擱在台緣、伸出台邊）
    heap(_Shift(M, 1), 30, 108, 16, 7, 6, lambda x, y, z: AGAVE_D if (x + y + z) % 3 == 0 else AGAVE, layer='work')
    for y in (76, 94):                                                           # 晾纖維的繩架：柱子、橫桿、掛著的纖維
        for x in range(72, 147, 18):
            M.box('work', x, y, 1, x + 2, y + 2, 20, FRAME)
        M.box('work', 72, y, 20, 146, y + 1, 21, FRAME)
        for x in range(75, 143, 3):
            if (x - 72) % 18 < 2:
                continue
            M.box('work', x, y, 12 + (x % 2) * 2, x + 2, y + 1, 20, FIBER if x % 4 else STALK)
    for i in range(5):                                                           # 紮好的纖維捆
        x = 74 + i * 10
        M.box('work', x, 104, 1, x + 8, 112, 7, FIBER)
        for xx in (x + 2, x + 5):
            M.box('work', xx, 104, 1, xx + 1, 112, 7, ROPE, True)
    cart(M, 132, 100, load=lambda M2, x, y, z: M2.box('work', x + 1, y + 1, z, x + 10, y + 16, z + 3, AGAVE))
    return {'key': 'plantation-sisal', 'title': '龍舌蘭園（種植園：刮纖維的棚與長台、晾纖維的繩架、紮好的纖維捆、裝葉子的牛車）', 'use': 'plantation', 'lot': (16, 12), 'M': M,
            'style': 'common', 'layers': PLANT_LAYERS, 'share': {k: 'meadow-farm-01m-plantation' for k in ('body', 'roof', 'gallery')}, 'variant': 'g', 'meta': {'recipes': 'sisal'}}


ALL = [farm_hemp, plant_sisal]
