# 城鎮建築第四批（TASK-0853；Tim 2026-10-23「那繼續加建築吧 GO」）—— 碉堡（四角稜堡：加勒比海毛石 carib、英國磚 en）、英國砲台（en）。
# 起因：盤點六座城每一塊地塊照風格退路找模型，還沒有的是皇家港的 Fort Charles 與三座砲台（en）、和平港的 Cussy 堡（carib）。
# 工具同 town3.py（quay.py ⇒ ame 那一套）；英國的磚照 ame english.py 的砌法與色。座標同 kit.py：x 臨路寬、y 進深（y 0 臨路、正面）、z 往上；0.1 m／格。
# 史料：作品 references/README.md 第四批那一節；形制查不到的都寫「設計」。
import math
import numpy as np
from scipy import ndimage
from town3 import *                                                    # noqa: F401  barred、lantern ＋ quay／harbour／civic／carib 的全部
from civic import hollow, put_mask, gun, flagpole_on                   # noqa: E402
from public import flag_sail                                           # noqa: E402
from english import brick_walls, tile_roof, BRICK_A, BRICK_B, BRICK_M  # noqa: E402


def pip_grid(poly, X, Y):
    """多邊形（格的角座標）⇒ [X, Y] 的布林陣列（格心在裡面）。"""
    xs, ys = np.meshgrid(np.arange(X) + 0.5, np.arange(Y) + 0.5, indexing='ij')
    inside = np.zeros((X, Y), bool)
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        cond = (y1 > ys) != (y2 > ys)
        xint = (x2 - x1) * (ys - y1) / ((y2 - y1) if y2 != y1 else 1e-9) + x1
        inside ^= cond & (xs < xint)
    return inside


def wall_color(style, salt=0):
    """外牆的色：carib ＝ 毛石（灰縫淺、一皮 5 格、石塊 7 格錯開）；en ＝ 磚（一皮 3 格、每 5 格一道豎縫，深淺兩色混砌）。"""
    if style == 'en':
        def f(x, y, z):
            row = z // 3
            u = x + y + (2 if row % 2 else 0)
            if z % 3 == 2 or u % 5 == 0:
                return BRICK_M
            return BRICK_B if h01('bk', u // 5, row, salt) < 0.3 else BRICK_A
        return f

    def g(x, y, z):
        row = z // 5
        u = x + y + (3 if row % 2 else 0)
        if z % 5 == 4 or u % 7 == 0:
            return MORTAR
        return RUBBLE_D if h01('rb', u // 7, row, salt) < 0.2 else RUBBLE
    return g


def cut_embrasure(S, inside, gx, gy, dx, dy, z0, z1, half=5):
    """砲眼：從砲的位置沿 (dx, dy) 往外走到多邊形外面，沿途左右 half 格內、z0..z1 的格挖空（胸牆上開一道口）。"""
    L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
    X, Y = inside.shape
    t = 0.0
    while True:
        cx, cy = gx + dx * t, gy + dy * t
        if not (0 <= cx < X and 0 <= cy < Y) or (t > 10 and not inside[int(cx), int(cy)]):
            break
        for s in np.arange(-half, half + 0.01, 0.5):
            x, y = int(math.floor(cx - dy * s)), int(math.floor(cy + dx * s))
            if 0 <= x < X and 0 <= y < Y:
                S[x, y, z0:z1] = False
        t += 0.5


def gun_model(name, x, y, z, dx, dy, code, src=None, pivot=None):
    """海戰用的砲（跟船互通）：船上同一件砲元件、meta kind=gun gun=<砲種代碼>（造船規格 §4.2、§9；遊戲的砲種表 Blockside config/game.json guns 的 code）。
    砲口朝 (dx, dy)（元件的砲口朝 +y；轉角 ＝ atan2(−dx, dy)）。"""
    rz = round(math.degrees(math.atan2(-dx, dy))) % 360
    return {'name': name, 'source': src or GUN, 'at': [x, y, z], 'pivot': pivot or GUN_PIVOT, 'rotate': [0, 0, rz], 'meta': {'kind': 'gun', 'gun': code}}


POWDER = 'basecamp-frigate-constitution-01m-powder-barrel'             # 憲法號的火藥桶（0.02 m；作品預設 meta 已有 render=lathe）


def powder_keg(name, x, y, z):
    """火藥桶（造船規格 §8：scale 0.2、pivot 11,11,0、meta kind=powder powder_lb=100；掛在彈藥庫那一層，遊戲照它擺取用點）。"""
    return {'name': name, 'source': POWDER, 'at': [x, y, z], 'pivot': [11, 11, 0], 'scale': [0.2, 0.2, 0.2], 'meta': {'kind': 'powder', 'powder_lb': 100}}


# ─────────────────────────────── 碉堡（四角稜堡）30 × 30 m ───────────────────────────────
def bastion_fort(style):
    """四角稜堡：正方形的幕牆、四角各一座稜堡（兩面＋兩翼），外牆砌到 3.6 m，牆後是土台（terreplein，寬 3 m），外緣一道 1.2 m 的胸牆開砲眼；
    正面幕牆中間一個門洞（雙扇木門）；左邊一條坡道從操場上土台；操場裡一棟營房、一間火藥庫、一口井、旗杆；九門 6 磅砲（正面 2、兩側與背面各 1、四座稜堡尖各 1）。
    - 照什麼：和平港 Cussy 1685 年「起造自己的房子，加一座 20 門砲的砲台與海邊壕溝，另有監獄、衛兵所」（ame 的研究 MSM1 pp.698–699〔讀過†〕）、
      和平港那一筆的名字「四角稜堡的總督府」；Fort Charles（皇家港，1656 年 Fort Cromwell、1662 年改名）是磚造〔摘〕—— 它的平面是不規則的「船形」，這裡不照。
      稜堡的比例、牆高、胸牆、砲數都是設計（一座小型的方堡；17 世紀加勒比海的小堡多是土與木，這裡給磚石的那一種）。
    - style：carib ＝ 毛石牆、木瓦頂；en ＝ 磚牆、紅陶瓦頂（皇家港）。生成器把碉堡正面朝港口 ⇒ 門與兩門正面砲在 −y。"""
    W, Z = 300, 120
    M = Model((W, W, Z))
    T, a, s, f = 4, 60, 45, 24                                         # 稜堡尖離框 0.4 m、幕牆線離框 6 m、肩離角 4.5 m、翼長 2.4 m
    B = W - a
    poly = [(a, a + s), (a - f, a + s), (T, T), (a + s, a - f), (a + s, a),
            (B - s, a), (B - s, a - f), (W - T, T), (B + f, a + s), (B, a + s),
            (B, B - s), (B + f, B - s), (W - T, W - T), (B - s, B + f), (B - s, B),
            (a + s, B), (a + s, B + f), (T, W - T), (a - f, B - s), (a, B - s)]
    inside = pip_grid(poly, W, W)
    d = ndimage.distance_transform_edt(inside)
    BAND, PAR, HT, HP = 30, 7, 36, 48                                  # 土台寬 3 m、胸牆厚 0.7 m、土台頂 3.6 m、胸牆頂 4.8 m
    ram = inside & (d <= BAND)
    par = inside & (d <= PAR)
    S = np.zeros((W, W, Z), bool)
    S[:, :, :HT] |= ram[:, :, None]
    S[:, :, HT:HP] |= par[:, :, None]
    # 門洞（正面幕牆中間，寬 2 m、高 2.8 m）
    GX0, GX1, GH = 140, 160, 28
    S[GX0:GX1, :a + BAND + 2, :GH] = False
    # 坡道（左邊幕牆裡面，x 90..104、y 120..200：往 y 120 那一頭升到土台頂）
    ramp = np.zeros((W, W), bool)
    for y in range(120, 200):
        h = int(round(HT * (200 - y) / 80))
        S[90:104, y, :h] = True
        ramp[90:104, y] = True
    # 砲：位置、砲口方向（土台上、胸牆後 1.4 m）
    gp = HT
    guns = [(125, a + PAR + 14, 0, -1), (175, a + PAR + 14, 0, -1),           # 正面
            (a + PAR + 14, 150, -1, 0), (B - PAR - 14, 150, 1, 0), (150, B - PAR - 14, 0, 1),   # 左、右、背面
            (46, 46, -1, -1), (W - 46, 46, 1, -1), (W - 46, W - 46, 1, 1), (46, W - 46, -1, 1)]  # 四座稜堡尖
    for (gx, gy, dx, dy) in guns:
        cut_embrasure(S, inside, gx, gy, dx, dy, HT + 4, HP, half=4)
    S = hollow(S, keep=6)
    wc = wall_color(style, salt=8531)

    def color(x, y, z):
        if ramp[x, y]:
            return EARTH_W
        if z == HT - 1 and not par[x, y]:                               # 土台頂：夯土長草
            return SOD if h01('sd', x // 4, y // 4) < 0.35 else EARTH_W
        if z == HP - 1 and par[x, y]:                                   # 胸牆壓頂
            return MORTAR if style != 'en' else BRICK_M
        if HT - 4 <= z < HT - 2 and d[x, y] <= 1.5:                     # 牆頂下一道腰線（cordon）
            return MORTAR if style != 'en' else BRICK_B
        return wc(x, y, z)
    put_mask(M, S, color, layer='rampart')
    M.box('rampart', GX0, a, 0, GX1, a + BAND + 2, 1, RUBBLE if style != 'en' else BRICK_A, force=True)    # 門洞的鋪地（從牆外面那一線起：門口那一格要是空氣）
    M.box('rampart', GX0 - 2, a, GH, GX1 + 2, a + 2, GH + 2, FRAME, force=True)                           # 門楣（木）
    put_part(M, 'door-double', '門', 'front', (a + s, a, B - s, a + BAND), 150, 0, 2)
    lantern(M, '燈籠-門', (134.5, a, 26))
    M.anchor('door', 150, a - 1, 0)
    # 操場：營房（背面）、火藥庫（右前）、井、旗杆
    R = (112, 172, 206, 206)
    if style == 'en':
        brick_walls(M, R, 0, 30, 3, salt=8532)
    else:
        rubble_walls(M, R, 0, 6, 3, salt=8532)
        board_walls(M, R, 6, 30, 2, bay=26)
    put_part(M, 'door-plank', '營房-門', 'front', R, 159, 0, 3)
    for cx in (128, 190):
        put_part(M, 'window-board', '營房-窗%d' % (1 if cx < 150 else 2), 'front', R, cx, 10, 3)
    roof_fn = tile_roof if style == 'en' else shingle_roof
    roof_fn(M, [{'x0': R[0], 'y0': R[1], 'x1': R[2], 'y1': R[3], 'ze': 30, 'p': 0.7, 'over': (3, 3, 3, 0), 'gable': 'x'}], salt=8533)
    MR = (170, 98, 204, 132)                                            # 火藥庫：厚牆、窄門、沒有窗（自己一層 ⇒ 遊戲照 kind=magazine 認）
    if style == 'en':
        brick_walls(M, MR, 0, 26, 4, layer='magazine', salt=8534)
    else:
        rubble_walls(M, MR, 0, 26, 4, layer='magazine', salt=8534)
    M.box('magazine', MR[0] + 4, MR[1] + 4, 0, MR[2] - 4, MR[3] - 4, 1, FLOOR)   # 木地板
    M.clear(MR[0], 109, 0, MR[0] + 4, 121, 22, 'magazine')              # 門洞（put_part 只挖 body 那幾層）
    put_part(M, 'door-plank', '火藥庫-門', 'left', MR, 115, 0, 4)
    roof_fn(M, [{'x0': MR[0], 'y0': MR[1], 'x1': MR[2], 'y1': MR[3], 'ze': 26, 'p': 0.8, 'over': (2, 2, 2, 2)}], salt=8535)
    M.box('body', 120, 104, 0, 132, 116, 8, RUBBLE)                     # 井
    M.box('body', 122, 106, 1, 130, 114, 8, DARK, force=True)
    ft, fb = flagpole_on(M, 140, 140, 0, 110)
    M.anchor('flag', 140, 140, 111)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 30, toward=1)]
    # 海戰用的 meta（Tim 2026-10-23「堡壘之後打算做入海戰 … 跟船套用同架構」「堡壘用的炮可以跟船互通(且meta標記要對應船的規格)」）：
    #   砲 ＝ 船上同一件 6 磅砲元件、meta kind=gun gun=6l，掛在它站的那一層（土台 ＝ 甲板）；火藥桶 ＝ 憲法號的火藥桶元件、kind=powder，掛在火藥庫那一層（造船規格 §4.2、§8、§9）
    guns_m = [gun_model('砲%d' % (i + 1), gx, gy, gp, dx, dy, '6l') for i, (gx, gy, dx, dy) in enumerate(guns)]
    kegs = [powder_keg('火藥桶-%d' % (i + 1), x, y, 1) for i, (x, y) in enumerate(((180, 106), (180, 120), (192, 106), (192, 120)))]
    for L in M.links:                                                   # 部件（門、窗）的格蓋過牆與鋪地 ⇒ 讓給部件
        for k in L['cells']:
            M.cells.pop(k, None)
    M.anchor('lot-0', 0, 0, 0)
    nm = {'carib': '毛石', 'en': '磚'}[style]
    mat = 'stone' if style != 'en' else 'brick'
    return {'key': 'fort' if style == 'carib' else 'fort-en', 'variant': 'a',
            'title': '碉堡（四角稜堡，%s牆：土台與胸牆、九個砲眼與 6 磅砲、門洞、坡道、營房、火藥庫、井、旗杆）' % nm,
            'use': 'fort', 'lot': (30, 30), 'M': M, 'style': style, 'flags': flags,
            'layers': {'body': '操場（營房、井、旗杆）', 'rampart': '堡牆與土台（甲板）', 'magazine': '火藥庫', 'roof': '屋頂'},
            'layer_meta': {'rampart': {'kind': 'deck', 'deck': 'rampart', 'level': 1, 'name': '土台', 'floor': '0:%d,%d:%d' % (HT, W, HT), 'thick': 6, 'material': mat},
                           'magazine': {'kind': 'magazine', 'pos': 'mid', 'powder_lb': 100 * len(kegs), 'material': mat}},
            'layer_anchors': {'magazine': {'blast': (187, 115, 10), 'door': (MR[0] - 1, 115, 0)}},
            'layer_models': {'rampart': guns_m, 'magazine': kegs}}


def fort():
    return bastion_fort('carib')


def fort_en():
    return bastion_fort('en')


# ─────────────────────────────── 英國砲台 12 × 12 m ───────────────────────────────
def battery_en():
    """英國的小砲台（皇家港 Fort James、Fort Carlisle、Fort Rupert 那一類）：正面一道磚砌胸牆（厚 1.6 m、高 2.4 m）、三個外張的砲眼、木砲床、三門 6 磅砲；
    左前角留進出口、兩側短翼牆、背面開敞；後面一間磚砌小火藥庫；旗杆。
    - 照什麼：皇家港是磚城（ame 的研究：HEATH「goodly Brick Houses」〔讀過†〕）、Fort Charles 磚造〔摘〕；三座小堡的形制〔沒查到〕⇒ 設計（同 summit 的砲台那一套擺法）。
    - 海戰用的 meta 同碉堡：胸牆與砲床一層 kind=deck、火藥庫一層 kind=magazine、砲 kind=gun gun=6l、桶 kind=powder。"""
    M = Model((120, 120, 90))
    PY0, PY1, H, SILL, PLAT = 4, 20, 24, 12, 4
    guns = (30, 60, 90)
    brick_walls(M, (16, PY0, 116, PY1), 0, H, 16, layer='rampart', salt=8536)    # 左前角留 1.2 m 的進出口（同 summit 的砲台）
    brick_walls(M, (4, PY1 + 14, 14, 70), 0, H - 4, 10, layer='rampart', salt=8537)
    brick_walls(M, (106, PY1, 116, 70), 0, H - 4, 10, layer='rampart', salt=8538)
    M.box('rampart', 16, PY0, H - 1, 116, PY1, H, BRICK_M, force=True)          # 壓頂
    for cx in guns:                                                     # 外張的砲眼：裡面 0.8 m、外面 1.6 m
        for y in range(PY0, PY1):
            half = 4 + (PY1 - 1 - y) * 4 // (PY1 - PY0)
            for x in range(cx - half, cx + half):
                for z in range(SILL, H + 1):
                    M.cells.pop((x, y, z), None)
    for cx in guns:                                                     # 木砲床
        M.box('rampart', cx - 12, PY1, 0, cx + 12, PY1 + 34, PLAT - 1, FRAME)
        for x in range(cx - 12, cx + 12):
            if (x - cx) % 6:
                M.box('rampart', x, PY1, PLAT - 1, x + 1, PY1 + 34, PLAT, FLOOR)
        bx, by = cx + 14, PY1 + 22                                      # 砲彈堆
        for z, n in ((0, 3), (1, 2), (2, 1)):
            for i in range(n):
                for j in range(n):
                    M.box('body', bx + i * 2 + z, by + j * 2 + z, z, bx + i * 2 + z + 2, by + j * 2 + z + 2, z + 1, IRON)
    mr = (70, 84, 104, 112)
    brick_walls(M, mr, 0, 26, 4, layer='magazine', salt=8539)
    M.box('magazine', mr[0] + 4, mr[1] + 4, 0, mr[2] - 4, mr[3] - 4, 1, FLOOR)
    M.clear(81, mr[1], 0, 93, mr[1] + 4, 22, 'magazine')                 # 門洞（put_part 只挖 body 那幾層）
    put_part(M, 'door-plank', '火藥庫-門', 'front', mr, 87, 0, 4)
    tile_roof(M, [{'x0': mr[0], 'y0': mr[1], 'x1': mr[2], 'y1': mr[3], 'ze': 26, 'p': 0.7, 'over': (3, 3, 3, 3)}], salt=8540)
    ft, fb = flagpole_on(M, 22, 96, 0, 80)
    M.anchor('flag', 22, 96, 81)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flags = [flag_sail('flag', ft, fb, 28, toward=1)]
    guns_m = [gun_model('砲%d' % (i + 1), cx, PY1 + 15, PLAT, 0, -1, '6l') for i, cx in enumerate(guns)]
    kegs = [powder_keg('火藥桶-%d' % (i + 1), x, 100, 1) for i, x in enumerate((80, 94))]
    lantern(M, '燈籠-火藥庫', (78.5, 84, 20))
    for L in M.links:
        for k in L['cells']:
            M.cells.pop(k, None)
    M.anchor('door', 9, 1, 0)                                           # 左前角的進出口（同 summit 的砲台：正面朝港口、路從正面接進來）
    M.anchor('lot-0', 0, 0, 0)
    return {'key': 'battery-en', 'title': '砲台（英國：磚砌胸牆與翼牆、三個外張砲眼、木砲床、三門 6 磅砲、磚砌小火藥庫、旗杆）',
            'use': 'battery', 'lot': (12, 12), 'M': M, 'style': 'en', 'flags': flags,
            'layers': {'body': '砲彈堆與旗杆', 'rampart': '胸牆與砲床（甲板）', 'magazine': '火藥庫', 'roof': '屋頂'},
            'layer_meta': {'rampart': {'kind': 'deck', 'deck': 'battery', 'level': 0, 'name': '砲床', 'floor': '0:%d,120:%d' % (PLAT, PLAT), 'thick': PLAT, 'material': 'brick'},
                           'magazine': {'kind': 'magazine', 'pos': 'mid', 'powder_lb': 100 * len(kegs), 'material': 'brick'}},
            'layer_anchors': {'magazine': {'blast': (87, 98, 10), 'door': (87, mr[1] - 1, 0)}},
            'layer_models': {'rampart': guns_m, 'magazine': kegs}}


ALL = [fort, fort_en, battery_en]
