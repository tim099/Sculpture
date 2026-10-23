# 城鎮建築第五批（TASK-0861；Tim 2026-10-23「下一批做加拉塔 1453 年的城堡 Kastellion（熱那亞聖十字堡）跟兩塊修道院地塊，補完手擺城裡最後沒模型的地塊」）
#   —— 加拉塔堡（genoa，0.2 m／格）、和平港的嘉布遣會修院（carib，0.1 m／格）。君士坦丁堡的生命之泉修道院 kaguya 正在做（kaguya-cpl-pege-1453），這裡不做。
# 海戰用的 meta（Tim 2026-10-23「堡壘之後打算做入海戰」「堡壘用的炮可以跟船互通(且meta標記要對應船的規格)」）：同 forts.py —— 站人的牆頂、塔頂各一層 kind=deck；
#   砲 ＝ 船上同一件元件、kind=gun gun=<代碼>；火藥 ＝ kind=magazine 那一層裡的 kind=powder 桶。
# 座標同 kit.py：x 臨路寬、y 進深（y 0 臨路、正面）、z 往上。史料：作品 references/README.md 第五批那一節。
import math
import numpy as np
from forts import *                                                    # noqa: F401  gun_model、powder_keg、hollow、put_mask ＋ town3／quay／harbour／civic／carib 的全部

BOMB = 'kotoko-fusta-01m-gun-bombardella'                              # 15 世紀的 bombardella（kotoko；0.05 m、13 × 46 × 14、砲口朝 +y；遊戲砲種 bombardella）
STONE_B, STONE_J, BRICK_1, BRICK_2, MORTAR_B = 182, 145, 168, 136, 205  # 同 kaguya byz.py 的 stone、stone_dark、brick、brick_dark、mortar
MARBLE_W, RED = 218, 160


def banded(salt=0):
    """拜占庭的帶狀砌法（同加拉塔、君士坦丁堡的地標）：每 2.2 m 一段 —— 1.0 m 磚帶（一皮一格、灰縫一格）＋ 1.2 m 方石（6 格一塊、豎縫錯開）。"""
    def f(x, y, z):
        k = z % 11
        if k < 5:
            if k % 2 == 1:
                return MORTAR_B
            return BRICK_2 if h01('bk', (x + y) // 3, z, salt) < 0.3 else BRICK_1
        if k == 10:
            return STONE_J
        u = x + y + (3 if (z // 11) % 2 else 0)
        return STONE_J if u % 6 == 0 else STONE_B
    return f


# ─────────────────────────────── 加拉塔堡（Kastellion）50 × 40 m ───────────────────────────────
def kastellion():
    """加拉塔堡（Kastellion tou Galatou；1453 年熱那亞稱聖十字堡 Castrum Sancte Crucis）—— 金角灣巨鏈的北端：一圈高牆圍的院子＋一座高塔。
    - 照什麼：地下部分（今 Yeraltı Camii）約 50 × 40 m 的長方形、牆厚約 2.25 m〔摘：The Byzantine Legacy〈Kastellion〉〕；「一座高塔、一個高牆圍起來的院子」〔摘〕；
      巨鏈從這裡拉到對岸的 Kentenarion 塔〔摘〕；北端是加拉塔堡、不是 1348 年的加拉塔塔（TOWN_BUILD §5.2，kaguya 的研究）。
      牆高、塔高（26 m）與位置、城垛、院子裡的小堂、倉房、火藥間、四門 bombardella 都是設計（舊平面圖學者說細節不準〔摘〕⇒ 不照）。
    - 0.2 m／格（同 kaguya 的地標）。正面（y 0）＝ 城門；塔在右後角，巨鏈的鐵環在塔的右面（x 大的那一面）。"""
    X, Y, Z = 250, 200, 180
    M = Model((X, Y, Z))
    WT, WF, HW, PAR = 11, 16, 50, 3                                    # 側、後牆厚 2.2 m；正面牆加厚到 3.2 m（牆頂放砲）；牆頂 10 m；城垛厚 0.6 m
    S = np.zeros((X, Y, Z), bool)
    S[1:X - 1, 1:1 + WF, :HW] = True                                   # 正面
    S[1:X - 1, Y - 1 - WT:Y - 1, :HW] = True                           # 後面
    S[1:1 + WT, 1:Y - 1, :HW] = True                                   # 左
    S[X - 1 - WT:X - 1, 1:Y - 1, :HW] = True                           # 右
    # 城垛：牆外緣 PAR 格厚、高 1.6 m；每 9 格一個垛口（寬 4、高 0.8 m）
    ring = np.zeros((X, Y), bool)
    ring[1:X - 1, 1:1 + PAR] = ring[1:X - 1, Y - 1 - PAR:Y - 1] = True
    ring[1:1 + PAR, 1:Y - 1] = ring[X - 1 - PAR:X - 1, 1:Y - 1] = True
    S[:, :, HW:HW + 8] |= ring[:, :, None]
    xs, ys = np.meshgrid(np.arange(X), np.arange(Y), indexing='ij')
    crenel = ring & (((xs + ys) % 9) < 4)
    S[:, :, HW + 4:HW + 8] &= ~crenel[:, :, None]
    # 城門：正面中間寬 4 m、拱頂高 5.6 m（直段 3.6 m ＋ 半圓）
    GX0, GX1, GZ = 115, 135, 18
    for x in range(GX0, GX1):
        top = GZ + int(math.sqrt(max(0.0, 100 - (x + 0.5 - 125) ** 2)))
        S[x, 0:1 + WF, :top] = False
    # 上牆頂的石階（左牆裡面，一階高 0.2 m、深 0.4 m，從 y 88 升到 y 188 的牆頂）
    for k in range(HW):
        y0 = 88 + 2 * k
        S[1 + WT:1 + WT + 8, y0:y0 + 2, :k + 1] = True
    # 砲：四門 bombardella 在正面牆頂、砲口朝外（−y）；砲位前的城垛挖低成砲眼
    gx = (40, 85, 165, 205)
    for x in gx:
        S[x - 4:x + 4, 1:1 + PAR, HW + 1:HW + 8] = False
    S = hollow(S, keep=3)
    put_mask(M, S, banded(8611), layer='rampart')
    # 城門的鐵柵（升起來、只露底下 0.8 m）與門上的大理石牌（熱那亞的紅十字：聖十字堡）
    for x in range(GX0, GX1):
        top = GZ + int(math.sqrt(max(0.0, 100 - (x + 0.5 - 125) ** 2)))
        for z in range(top - 4, top):
            if (x - GX0) % 3 == 0:                                      # 一根一根的鐵條，頂端插在拱頂裡
                M.put('rampart', x, 6, z, IRON, force=True)
    M.box('rampart', 118, 0, 32, 132, 1, 44, MARBLE_W, force=True)
    M.box('rampart', 124, 0, 33, 126, 1, 43, RED, force=True)
    M.box('rampart', 119, 0, 37, 131, 1, 39, RED, force=True)
    M.box('rampart', GX0, 1, 0, GX1, 1 + WF, 1, STONE_J, force=True)   # 門洞鋪地（從牆面那一線起：門口那一格要是空氣）
    lantern(M, '燈籠-門', (110.5, 0, 16))
    M.anchor('door', 125, 0, 0)
    # 塔（Megálos Pýrgos）：右後角 12 × 12 m、高 26 m、牆厚 2 m；頂上城垛；院子那一面一扇門
    TX0, TY0, TX1, TY1, TH = 188, 138, 249, 199, 130
    T = np.zeros((X, Y, Z), bool)
    T[TX0:TX1, TY0:TY1, :TH] = True
    T[TX0 + 10:TX1 - 10, TY0 + 10:TY1 - 10, :TH - 6] = False            # 塔裡空的；頂上 1.2 m 的石板頂
    tring = np.zeros((X, Y), bool)
    tring[TX0:TX1, TY0:TY0 + PAR] = tring[TX0:TX1, TY1 - PAR:TY1] = True
    tring[TX0:TX0 + PAR, TY0:TY1] = tring[TX1 - PAR:TX1, TY0:TY1] = True
    T[:, :, TH:TH + 8] |= tring[:, :, None]
    tcren = tring & (((xs + ys) % 9) < 4)
    T[:, :, TH + 4:TH + 8] &= ~tcren[:, :, None]
    T[TX0:TX0 + 10, 163:173, :16] = False                              # 塔門（院子那一面）
    for z0 in (40, 70, 100):                                           # 射口（細長）
        for (x0, x1, y0, y1) in ((TX0 + 28, TX0 + 31, TY0, TY0 + 10), (TX0 + 28, TX0 + 31, TY1 - 10, TY1), (TX1 - 10, TX1, TY0 + 28, TY0 + 31)):
            T[x0:x1, y0:y1, z0:z0 + 10] = False
    T = hollow(T, keep=3)
    for (x, y, z) in zip(*np.nonzero(T)):
        M.put('tower', int(x), int(y), int(z), banded(8612)(int(x), int(y), int(z)), force=True)
    ft, fb = flagpole_on(M, 217, 167, TH, TH + 45, layer='tower')
    M.anchor('flag', 217, 167, TH + 46)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flag = flag_sail('flag', ft, fb, 18, toward=1)
    flag['meta'] = dict(flag['meta'], pattern='genoa')                 # 熱那亞旗（白底紅十字；同 kaguya 的加拉塔塔）
    # 巨鏈的繫點：塔右面離地 2.4 m 的大鐵環，底下垂一截鏈到地
    for th in range(0, 360, 6):
        a = math.radians(th)
        y, z = 168 + 5 * math.cos(a), 12 + 5 * math.sin(a)
        M.put('tower', 249, int(round(y)), int(round(z)), IRON, force=True)
    for z in range(0, 7):
        M.put('tower', 249, 168, z, IRON, force=True)
        if z % 2 == 0:
            M.put('tower', 249, 167, z, IRON, force=True)
            M.put('tower', 249, 169, z, IRON, force=True)
    M.anchor('chain', 249, 168, 12)
    # 院子：聖十字小堂（帶狀磚石、紅瓦兩坡頂、後面半圓的聖壇）、靠後牆的倉房、左前角的火藥間
    wc = banded(8613)
    C = (60, 110, 90, 160)
    for (x, y, z) in [(x, y, z) for x in range(C[0], C[2]) for y in range(C[1], C[3]) for z in range(25)
                      if x < C[0] + 3 or x >= C[2] - 3 or y < C[1] + 3 or y >= C[3] - 3]:
        M.put('body', x, y, z, wc(x, y, z))
    for x in range(63, 87):                                            # 聖壇（半圓，半徑 2.4 m、高 4 m、半穹頂紅瓦）
        for y in range(160, 173):
            r = math.hypot(x + 0.5 - 75, y + 0.5 - 160)
            if 9 <= r <= 12:
                for z in range(20):
                    M.put('body', x, y, z, wc(x, y, z))
            if r <= 12:
                for z in range(20, 33):
                    if 10.5 <= math.sqrt(r * r + (z + 0.5 - 20) ** 2) <= 12.5:
                        M.put('roof', x, y, z, TILE_A)
    M.clear(70, C[1], 0, 80, C[1] + 3, 14)                              # 小堂的門
    M.box('body', 70, C[1] + 1, 0, 80, C[1] + 2, 13, FRAME)
    ctop = tile_roof(M, [{'x0': C[0], 'y0': C[1], 'x1': C[2], 'y1': C[3], 'ze': 25, 'p': 0.8, 'over': (2, 2, 2, 0), 'gable': 'y'}], salt=8614)
    zc = int(max(ctop[(x, C[1] + 1)] for x in (74, 75)))               # 正面山牆頂的十字（立在屋脊上）
    M.box('roof', 74, C[1], zc, 76, C[1] + 2, zc + 8, FRAME, force=True)
    M.box('roof', 71, C[1], zc + 4, 79, C[1] + 2, zc + 6, FRAME, force=True)
    SH = (60, 172, 170, 188)                                           # 倉房：靠後牆的單坡
    for (x, y, z) in [(x, y, z) for x in range(SH[0], SH[2]) for y in range(SH[1], SH[3]) for z in range(20)
                      if x < SH[0] + 3 or x >= SH[2] - 3 or y < SH[1] + 3]:
        M.put('body', x, y, z, wc(x, y, z))
    M.clear(110, SH[1], 0, 120, SH[1] + 3, 14)
    shed_roof(M, SH[0], SH[1] - 2, SH[2], SH[3], 26, 0.3, low='front', color_fn=lambda x, y, f, r, e: TILE_R if r or e else TILE_A)
    MR = (20, 26, 44, 48)                                              # 火藥間（厚牆、窄門、紅瓦）
    for (x, y, z) in [(x, y, z) for x in range(MR[0], MR[2]) for y in range(MR[1], MR[3]) for z in range(16)
                      if x < MR[0] + 3 or x >= MR[2] - 3 or y < MR[1] + 3 or y >= MR[3] - 3]:
        M.put('magazine', x, y, z, wc(x, y, z))
    M.box('magazine', MR[0] + 3, MR[1] + 3, 0, MR[2] - 3, MR[3] - 3, 1, FLOOR)
    M.clear(MR[2] - 3, 33, 0, MR[2], 41, 11, 'magazine')
    tile_roof(M, [{'x0': MR[0], 'y0': MR[1], 'x1': MR[2], 'y1': MR[3], 'ze': 16, 'p': 0.8, 'over': (1, 1, 1, 1)}], salt=8615)
    M.box('body', 140, 90, 0, 150, 100, 4, STONE_J)                     # 蓄水池的井口
    M.box('body', 142, 92, 1, 148, 98, 4, DARK, force=True)
    guns_m = [gun_model('砲%d' % (i + 1), x, 15, HW, 0, -1, 'bombardella', src=BOMB, pivot=[6.5, 0, 0]) for i, x in enumerate(gx)]
    for g in guns_m:
        g['scale'] = [0.25, 0.25, 0.25]
    kegs = [dict(powder_keg('火藥桶-%d' % (i + 1), x, 36, 1), scale=[0.1, 0.1, 0.1]) for i, x in enumerate((26, 32))]
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'kastellion', 'mpv': 0.2,
            'title': '加拉塔堡（Kastellion／聖十字堡 1453：帶狀磚石的高牆與城垛、26 m 的高塔、巨鏈的鐵環、城門與熱那亞紅十字牌、院子裡的小堂、倉房、火藥間、四門 bombardella）',
            'use': 'fort', 'lot': (50, 40), 'M': M, 'style': 'genoa', 'flags': [flag],
            'layers': {'body': '院子（小堂、倉房、井）', 'rampart': '城牆、城垛、城門與石階（牆頂 ＝ 甲板）', 'tower': '高塔（塔頂 ＝ 甲板）、巨鏈的鐵環', 'magazine': '火藥間', 'roof': '屋頂'},
            'layer_meta': {'rampart': {'kind': 'deck', 'deck': 'wall', 'level': 1, 'name': '牆頂', 'floor': '0:%d,%d:%d' % (HW, X, HW), 'thick': 6, 'material': 'stone'},
                           'tower': {'kind': 'deck', 'deck': 'tower', 'level': 2, 'name': '塔頂', 'floor': '%d:%d,%d:%d' % (TX0, TH, TX1, TH), 'thick': 6, 'material': 'stone'},
                           'magazine': {'kind': 'magazine', 'pos': 'mid', 'powder_lb': 100 * len(kegs), 'material': 'stone'}},
            'layer_anchors': {'magazine': {'blast': (32, 37, 6), 'door': (MR[2], 37, 0)}},
            'layer_models': {'rampart': guns_m, 'magazine': kegs}}


# ─────────────────────────────── 和平港 嘉布遣會修院（Le Convent）14 × 4 m ───────────────────────────────
def convent():
    """和平港的嘉布遣會修院（Le Convent；北部傳教區的總部 —— MSM p.699，crest-001 手擺那一筆）：14 × 4 m 的一長棟 ——
    編條糊泥刷白的牆、木瓦兩坡頂、正面一扇門兩扇窗；左端山牆往上砌一面掛鐘的牆（clocher-mur）、頂上木十字；屋裡左端一張小祭壇。
    - 照什麼：地塊大小與名字（crest-001 照 Moreau de Saint-Méry 畫的）；同一套的牆、屋頂、窗門照 summit 的加勒比海建築（§6.3）。
      修院的形制〔沒查到〕⇒ 鐘牆、祭壇都是設計（鐘牆的做法照 Labat 寫的小禮拜堂沒有鐘樓、TOWN_BUILD 第三批的小教堂另立鐘架；這裡地塊太窄 ⇒ 砌在山牆上）。"""
    X, Y, Z = 140, 40, 80
    M = Model((X, Y, Z))
    R = (2, 2, 138, 38)
    daub_walls(M, R, 0, 28, 3)
    M.box('body', R[0] + 3, R[1] + 3, 0, R[2] - 3, R[3] - 3, 1, FLOOR)
    put_part(M, 'door-plank', '前-門', 'front', R, 70, 0, 3)
    for i, cx in enumerate((32, 108)):
        put_part(M, 'window-board', '前-窗%d' % (i + 1), 'front', R, cx, 10, 3)
        put_part(M, 'window-board', '後-窗%d' % (i + 1), 'back', R, cx, 10, 3)
    shingle_roof(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 28, 'p': 0.75, 'over': (2, 2, 2, 2), 'gable': 'x'}], salt=8616)
    end_gable(M, R[0], R[0] + 3, R[1], R[3], 28, 0.75, z0=28, color=LIME, edge=LIME)
    end_gable(M, R[2] - 3, R[2], R[1], R[3], 28, 0.75, z0=28, color=LIME, edge=LIME)
    # 鐘牆：左端山牆往上砌到 6.0 m、中間一個拱洞掛鐘、頂上木十字
    M.box('body', 0, 12, 28, 5, 28, 60, LIME, force=True)
    M.clear(0, 16, 44, 5, 24, 56)
    M.box('body', 0, 15, 56, 5, 25, 57, FRAME, force=True)            # 掛鐘的橫木
    for z in range(46, 55):
        r = 1 + (54 - z) // 3
        for y in range(20 - r - 1, 20 + r + 1):
            M.put('body', 2, y, z, BRONZE, force=True)
            M.put('body', 3, y, z, BRONZE, force=True)
    M.box('body', 2, 19, 55, 4, 21, 56, IRON, force=True)
    M.box('body', 1, 19, 60, 4, 21, 72, FRAME, force=True)
    M.box('body', 1, 16, 66, 4, 24, 68, FRAME, force=True)
    M.anchor('bell', 2, 20, 50)
    # 屋裡：左端的小祭壇（木、白布）
    M.box('body', 8, 12, 1, 14, 28, 9, FLOOR)
    M.box('body', 7, 11, 9, 15, 29, 10, LIME)
    M.box('body', 9, 19, 10, 11, 21, 18, FRAME)
    lantern(M, '燈籠-門', (60.5, R[1], 21))
    for L in M.links:
        for k in L['cells']:
            if k[2] == 0:
                M.cells.pop(k, None)
    M.anchor('door', 70, R[1] - 1, 0)
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'convent', 'title': '修院（嘉布遣會：刷白的編條糊泥長屋、木瓦兩坡頂、山牆上掛鐘的鐘牆與十字、小祭壇）',
            'use': 'monastery', 'lot': (14, 4), 'M': M, 'style': 'carib', 'layers': {'body': '牆、鐘牆與擺設', 'roof': '屋頂'}}


ALL = [kastellion, convent]
