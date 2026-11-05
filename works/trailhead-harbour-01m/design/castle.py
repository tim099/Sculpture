# 城鎮建築第五批（TASK-0861；Tim 2026-10-23「下一批做加拉塔 1453 年的城堡 Kastellion（熱那亞聖十字堡）跟兩塊修道院地塊，補完手擺城裡最後沒模型的地塊」）
#   —— 加拉塔堡（genoa；原 0.2 m／格，2026-11-05 改 0.1 m、加砲）、和平港的嘉布遣會修院（carib，0.1 m／格）。君士坦丁堡的生命之泉修道院 kaguya 正在做（kaguya-cpl-pege-1453），這裡不做。
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
PIERRIER = 'apex-one-reale-01m-gun-pierrier'                           # 迴旋後膛砲 pierrier（apex-one；0.05 m、11 × 38 × 13、砲口朝 +y；固定點 pivot 5,18,0 ＝ 叉架插銷的底）


def banded01(salt=0):
    """帶狀砌法的 0.1 m 版（2026-11-05 從 0.2 m 改）：每 2.2 m 一段 —— 1.0 m 磚帶（一皮磚一格、灰縫一格 ⇒ 五皮）＋ 1.2 m 方石（兩皮各 0.6 m、一塊 0.9 m、豎縫上下皮錯開）。"""
    def f(x, y, z):
        k = z % 22
        if k < 10:
            if k % 2 == 1:
                return MORTAR_B
            return BRICK_2 if h01('bk', (x + y + (2 if (k // 2) % 2 else 0)) // 5, z, salt) < 0.3 else BRICK_1
        c = (k - 10) // 6
        if (k - 10) % 6 == 5:
            return STONE_J
        u = x + y + (4 if (z // 22 + c) % 2 else 0)
        return STONE_J if u % 9 == 0 else STONE_B
    return f


def flagpole01(M, x, y, z0, z_top, layer='body'):
    """旗杆的 0.1 m 版（civic.flagpole_on 是 2 × 2 格：在 0.2 m 的作品裡才是 0.4 m 粗）：4 × 4 格、頂上一顆圓頭；回傳布旗的綁邊（旗杆 +x 那一格的空氣，上、下）。"""
    M.box(layer, x, y, z0, x + 4, y + 4, z_top, FRAME)
    M.box(layer, x, y, z_top, x + 4, y + 4, z_top + 4, GOLD)
    return (x + 4, y, z_top - 4), (x + 4, y, z_top - 40)


def kastellion():
    """加拉塔堡（Kastellion tou Galatou；1453 年熱那亞稱聖十字堡 Castrum Sancte Crucis）—— 金角灣巨鏈的北端：一圈高牆圍的院子＋一座高塔。
    - 照什麼：地下部分（今 Yeraltı Camii）約 50 × 40 m 的長方形、牆厚約 2.25 m〔摘：The Byzantine Legacy〈Kastellion〉〕；「一座高塔、一個高牆圍起來的院子」〔摘〕；
      巨鏈從這裡拉到對岸的 Kentenarion 塔〔摘〕；北端是加拉塔堡、不是 1348 年的加拉塔塔（TOWN_BUILD §5.2，kaguya 的研究）。
      牆高、塔高（26 m）與位置、城垛、院子裡的小堂、倉房、火藥間、砲都是設計（舊平面圖學者說細節不準〔摘〕⇒ 不照）。
    - 0.1 m／格（Tim 2026-11-05「改成0.1m一格(因為匯入時也會轉換) 然後強化一下武裝」；以前 0.2 m：座標全部 ×2、外形尺寸不變）。
      正面（y 0）＝ 城門、朝東（加拉塔的地塊 rot 0）；塔在右後角，巨鏈的鐵環在塔的右面（x 大的那一面 ＝ 朝南、朝金角灣）。
    - 武裝（設計：1453 前後熱那亞的堡 —— 鍛鐵箍的 bombardella 架在牆頂、垛口上架後膛迴旋砲）：正面牆頂 4 門、朝海的右牆頂 3 門、塔頂朝海 2 門 bombardella ＋ 2 門 pierrier（朝東、朝西沿岸）。
      正面與右牆加厚到 4.0 m（往院子裡加，外面不變）⇒ 砲後面留 1.2 m 走道，沿牆頂走得過去；塔：右牆牆頂開一扇門進塔、塔裡一層木樓板（＝ 牆頂那一層）、直梯穿塔頂的梯口上去。"""
    X, Y, Z = 500, 400, 360
    M = Model((X, Y, Z))
    WT, WF, HW, PAR = 22, 40, 100, 6                                   # 左、後牆厚 2.2 m；正面、右牆 4.0 m（牆頂放砲）；牆頂 10 m；城垛厚 0.6 m
    TX0, TY0, TX1, TY1, TH = 376, 276, 498, 398, 260                   # 塔：右後角 12.2 × 12.2 m、高 26 m、牆厚 2 m
    S = np.zeros((X, Y, Z), bool)
    S[2:X - 2, 2:2 + WF, :HW] = True                                   # 正面
    S[2:TX0 + 20, Y - 2 - WT:Y - 2, :HW] = True                        # 後面（接到塔的牆身為止，不伸進塔裡）
    S[2:2 + WT, 2:Y - 2, :HW] = True                                   # 左
    S[X - 2 - WF:X - 2, 2:TY0 + 20, :HW] = True                        # 右（朝海；同上）
    # 城垛：牆外緣 PAR 格厚、高 1.6 m；每 1.8 m 一個垛口（寬 0.8、高 0.8 m）
    ring = np.zeros((X, Y), bool)
    ring[2:X - 2, 2:2 + PAR] = ring[2:X - 2, Y - 2 - PAR:Y - 2] = True
    ring[2:2 + PAR, 2:Y - 2] = ring[X - 2 - PAR:X - 2, 2:Y - 2] = True
    S[:, :, HW:HW + 16] |= ring[:, :, None]
    xs, ys = np.meshgrid(np.arange(X), np.arange(Y), indexing='ij')
    crenel = ring & (((xs + ys) % 18) < 8)
    S[:, :, HW + 8:HW + 16] &= ~crenel[:, :, None]

    def gtop(x):
        return GZ + int(math.sqrt(max(0.0, 400 - (x + 0.5 - 250) ** 2)))
    # 城門：正面中間寬 4 m、拱頂高 5.6 m（直段 3.6 m ＋ 半圓）
    GX0, GX1, GZ = 230, 270, 36
    for x in range(GX0, GX1):
        S[x, 0:2 + WF, :gtop(x)] = False
    # 上牆頂的石階（左牆裡面，一階高 0.2 m、深 0.4 m，從 y 176 升到 y 376 的後牆牆頂）
    for k in range(HW // 2):
        y0 = 176 + 4 * k
        S[2 + WT:2 + WT + 16, y0:y0 + 4, :2 * (k + 1)] = True
    # 砲：正面 4 門（砲口朝外 −y）、右牆 3 門（朝海 +x）；砲位前的城垛挖低成砲眼
    gx = (80, 170, 330, 410)
    gy = (100, 170, 240)
    for x in gx:
        S[x - 8:x + 8, 2:2 + PAR, HW + 2:HW + 16] = False
    for y in gy:
        S[X - 2 - PAR:X - 2, y - 8:y + 8, HW + 2:HW + 16] = False
    S = hollow(S, keep=6)
    put_mask(M, S, banded01(8611), layer='rampart')
    # 城門的鐵柵（升起來、只露底下 0.8 m）與門上的大理石牌（熱那亞的紅十字：聖十字堡）
    for x in range(GX0, GX1):
        if (x - GX0) % 5 == 2:                                          # 一根一根的鐵條，頂端插在拱頂裡
            for z in range(gtop(x) - 8, gtop(x)):
                M.put('rampart', x, 12, z, IRON, force=True)
                M.put('rampart', x, 13, z, IRON, force=True)
    M.box('rampart', 236, 0, 64, 264, 2, 88, MARBLE_W, force=True)
    M.box('rampart', 248, 0, 66, 252, 2, 86, RED, force=True)
    M.box('rampart', 238, 0, 74, 262, 2, 78, RED, force=True)
    M.box('rampart', GX0, 2, 0, GX1, 2 + WF, 2, STONE_J, force=True)   # 門洞鋪地（從牆面那一線起：門口那一格要是空氣）
    lantern(M, '燈籠-門', (221, 2, 32))                                # 掛在牆面上（牆面 y 2；以前 at 在 y 0 ⇒ 跟牆隔兩格空氣，匯入檢查「開場就掉」）
    M.anchor('door', 250, 0, 0)
    # 塔（Megálos Pýrgos）：頂上城垛；院子那一面一扇門、右牆牆頂一扇門（進木樓板那一層）
    T = np.zeros((X, Y, Z), bool)
    T[TX0:TX1, TY0:TY1, :TH] = True
    T[TX0 + 20:TX1 - 20, TY0 + 20:TY1 - 20, :TH - 12] = False           # 塔裡空的；頂上 1.2 m 的石板頂
    tring = np.zeros((X, Y), bool)
    tring[TX0:TX1, TY0:TY0 + PAR] = tring[TX0:TX1, TY1 - PAR:TY1] = True
    tring[TX0:TX0 + PAR, TY0:TY1] = tring[TX1 - PAR:TX1, TY0:TY1] = True
    T[:, :, TH:TH + 16] |= tring[:, :, None]
    tcren = tring & (((xs + ys) % 18) < 8)
    T[:, :, TH + 8:TH + 16] &= ~tcren[:, :, None]
    T[TX0:TX0 + 20, 326:346, :32] = False                              # 塔門（院子那一面）
    T[462:472, TY0:TY0 + 20, HW:HW + 22] = False                       # 牆頂進塔的門（右牆牆頂 ⇒ 塔裡的木樓板）
    for z0 in (80, 140, 200):                                          # 射口（細長）
        for (x0, x1, y0, y1) in ((TX0 + 56, TX0 + 62, TY0, TY0 + 20), (TX0 + 56, TX0 + 62, TY1 - 20, TY1), (TX1 - 20, TX1, TY0 + 56, TY0 + 62)):
            T[x0:x1, y0:y1, z0:z0 + 20] = False
    T[470:478, 330:340, TH - 12:TH] = False                            # 塔頂的梯口（直梯從底下穿上來）
    tgy = (305, 365)                                                   # 塔頂朝海的兩門 bombardella：砲眼
    for y in tgy:
        T[TX1 - PAR:TX1, y - 8:y + 8, TH + 2:TH + 16] = False
    PX = 420                                                           # 塔頂兩門 pierrier（朝東 −y、朝西 +y）架在垛口的台上：那一段一定是垛口
    for (y0, y1) in ((TY0, TY0 + PAR), (TY1 - PAR, TY1)):
        T[PX - 4:PX + 4, y0:y1, TH + 8:TH + 16] = False
    T = hollow(T, keep=6)
    bt = banded01(8612)
    for (x, y, z) in zip(*np.nonzero(T)):
        M.put('tower', int(x), int(y), int(z), bt(int(x), int(y), int(z)), force=True)
    M.box('rampart', TX0 + 20, TY0 + 20, HW - 2, TX1 - 20, TY1 - 20, HW, FLOOR, force=True)   # 塔裡的木樓板（＝ 牆頂那一層甲板）
    # 直梯：立在梯口靠 −x 的那一邊（x 470..471，頂端貼著塔頂石板的邊）、從木樓板到塔頂；爬的人在 +x 那一側、面朝 −x，
    #   到頂往前跨過梯頂就踩上甲板（樓梯自檢 ④：以前梯子貼著右牆、爬的人在梯口裡 ⇒ 最上一階到甲板邊懸空 6 柱）
    for z in range(HW, TH):
        for y in (331, 338):
            M.put('ladder', 470, y, z, FRAME)
            M.put('ladder', 471, y, z, FRAME)
        if (z - HW) % 3 == 2:
            for y in range(332, 338):
                M.put('ladder', 471, y, z, FRAME)
    ft, fb = flagpole01(M, 434, 334, TH, TH + 90, layer='tower')
    M.anchor('flag', 434, 334, TH + 92)
    M.anchor('flag-top', *ft)
    M.anchor('flag-bottom', *fb)
    flag = flag_sail('flag', ft, fb, 36, toward=1)
    flag['meta'] = dict(flag['meta'], pattern='genoa')                 # 熱那亞旗（白底紅十字；同 kaguya 的加拉塔塔）
    # 巨鏈的繫點：塔右面離地 2.4 m 的大鐵環（徑 2 m、0.2 m 粗），底下垂一截鏈到地
    for y in range(320, 352):
        for z in range(8, 40):
            if 9.0 <= math.hypot(y + 0.5 - 336, z + 0.5 - 24) <= 11.0:
                M.put('tower', 498, y, z, IRON, force=True)
                M.put('tower', 499, y, z, IRON, force=True)
    for z in range(0, 14):
        M.put('tower', 498, 335, z, IRON, force=True)
        M.put('tower', 498, 336, z, IRON, force=True)
        if z % 4 < 2:
            for y in (333, 334, 337, 338):
                M.put('tower', 498, y, z, IRON, force=True)
    M.anchor('chain', 498, 336, 24)
    # 院子：聖十字小堂（帶狀磚石、紅瓦兩坡頂、後面半圓的聖壇）、靠後牆的倉房、左前角的火藥間
    wc = banded01(8613)
    C = (120, 220, 180, 320)
    for x in range(C[0], C[2]):
        for y in range(C[1], C[3]):
            if x < C[0] + 6 or x >= C[2] - 6 or y < C[1] + 6 or y >= C[3] - 6:
                for z in range(50):
                    M.put('body', x, y, z, wc(x, y, z))
    for x in range(126, 174):                                          # 聖壇（半圓，半徑 2.4 m、高 4 m、半穹頂紅瓦）
        for y in range(320, 346):
            r = math.hypot(x + 0.5 - 150, y + 0.5 - 320)
            if 18 <= r <= 24:
                for z in range(40):
                    M.put('body', x, y, z, wc(x, y, z))
            if r <= 24:
                for z in range(40, 66):
                    if 21 <= math.sqrt(r * r + (z + 0.5 - 40) ** 2) <= 25:
                        M.put('roof', x, y, z, TILE_A)
    M.clear(140, C[1], 0, 160, C[1] + 6, 28)                            # 小堂的門
    M.box('body', 140, C[1] + 2, 0, 160, C[1] + 4, 26, FRAME)
    ctop = tile_roof(M, [{'x0': C[0], 'y0': C[1], 'x1': C[2], 'y1': C[3], 'ze': 50, 'p': 0.8, 'over': (4, 4, 4, 0), 'gable': 'y'}], salt=8614)
    zc = int(max(ctop[(x, C[1] + 2)] for x in (149, 150)))             # 正面山牆頂的十字（立在屋脊上）
    M.box('roof', 148, C[1], zc, 152, C[1] + 4, zc + 16, FRAME, force=True)
    M.box('roof', 142, C[1], zc + 8, 158, C[1] + 4, zc + 12, FRAME, force=True)
    SH = (120, 344, 340, 376)                                          # 倉房：靠後牆的單坡
    for x in range(SH[0], SH[2]):
        for y in range(SH[1], SH[3]):
            if x < SH[0] + 6 or x >= SH[2] - 6 or y < SH[1] + 6:
                for z in range(40):
                    M.put('body', x, y, z, wc(x, y, z))
    M.clear(220, SH[1], 0, 240, SH[1] + 6, 28)
    shed_roof(M, SH[0], SH[1] - 4, SH[2], SH[3], 52, 0.3, low='front', color_fn=lambda x, y, f, r, e: TILE_R if r or e else TILE_A)
    MR = (40, 52, 88, 96)                                              # 火藥間（厚牆、窄門、紅瓦）
    for x in range(MR[0], MR[2]):
        for y in range(MR[1], MR[3]):
            if x < MR[0] + 6 or x >= MR[2] - 6 or y < MR[1] + 6 or y >= MR[3] - 6:
                for z in range(32):
                    M.put('magazine', x, y, z, wc(x, y, z))
    M.box('magazine', MR[0] + 6, MR[1] + 6, 0, MR[2] - 6, MR[3] - 6, 2, FLOOR)
    M.clear(MR[2] - 6, 66, 0, MR[2], 82, 22, 'magazine')
    tile_roof(M, [{'x0': MR[0], 'y0': MR[1], 'x1': MR[2], 'y1': MR[3], 'ze': 32, 'p': 0.8, 'over': (2, 2, 2, 2)}], salt=8615)
    M.box('body', 280, 180, 0, 300, 200, 8, STONE_J)                    # 蓄水池的井口
    M.box('body', 284, 184, 2, 296, 196, 8, DARK, force=True)
    guns_w = [gun_model('砲%d' % (i + 1), x, 30, HW, 0, -1, 'bombardella', src=BOMB, pivot=[6.5, 0, 0]) for i, x in enumerate(gx)]
    guns_w += [gun_model('砲%d' % (i + 5), X - 2 - 28, y, HW, 1, 0, 'bombardella', src=BOMB, pivot=[6.5, 0, 0]) for i, y in enumerate(gy)]
    guns_t = [gun_model('塔砲%d' % (i + 1), TX1 - 28, y, TH, 1, 0, 'bombardella', src=BOMB, pivot=[6.5, 0, 0]) for i, y in enumerate(tgy)]
    guns_t += [gun_model('迴旋砲-東', PX, TY0 + PAR // 2, TH + 8, 0, -1, 'pierrier', src=PIERRIER, pivot=[5.5, 18.5, 0]),
               gun_model('迴旋砲-西', PX, TY1 - PAR // 2, TH + 8, 0, 1, 'pierrier', src=PIERRIER, pivot=[5.5, 18.5, 0])]
    for i, g in enumerate(guns_w + guns_t):                            # 砲的 id（造船規格 §12：gun-<序號>，一件組裝件裡唯一）
        g['meta']['id'] = 'gun-%d' % (i + 1)
    for g in guns_t[2:4]:                                              # 迴旋砲：砲管與叉架拆兩件（同皇家號、拉貝爾號的掛法：叉架 kind=gunmount、mount_of 指砲）
        g['meta'].update(mount='turret', arc='-80,80')
        guns_t.append(dict(g, name=g['name'] + '座', source=PIERRIER + '-mount',
                           meta={'kind': 'gunmount', 'mount_of': g['meta']['id'], 'id': 'gunmount-%s' % g['meta']['id'].split('-')[1]}))
    kegs = [powder_keg('火藥桶-%d' % (i + 1), x, y, 2) for i, (x, y) in enumerate(((52, 72), (64, 72), (52, 84), (64, 84)))]
    M.anchor('lot-0', 0, 0, 0)
    # 駐軍的工作點（summit 2026-10-25 在 0.2 m 版標的 work-<名>／-to ⇒ 座標 ×2；塔頂 z 260、牆頂 z 100、e1 站在石階上）：寫進產生程式，apply anchors 才不會當成清單外的拿掉
    for nm, at, to in (('a1', (386, 286, 260), (382, 282, 268)), ('b1', (486, 386, 260), (490, 390, 268)), ('a2', (386, 386, 260), (382, 390, 268)),
                       ('b2', (486, 286, 260), (490, 282, 268)), ('a3', (386, 346, 260), (380, 346, 268)), ('a4', (446, 286, 260), (446, 280, 268)),
                       ('a5', (446, 386, 260), (446, 392, 268)), ('a6', (486, 346, 260), (492, 346, 268)), ('c1', (12, 386, 100), (8, 390, 108)),
                       ('d1', (486, 12, 100), (490, 8, 108)), ('c2', (12, 12, 100), (8, 8, 108)), ('e1', (28, 346, 86), (20, 346, 94))):
        M.anchor('work-' + nm, *at)
        M.anchor('work-%s-to' % nm, *to)
    LA ={'L1.foot': (472, 335, HW), 'L1.lo': (472, 335, HW + 2), 'L1.hi': (472, 335, TH - 2), 'L1.head': (468, 335, TH)}
    return {'key': 'kastellion', 'mpv': 0.1,
            'title': '加拉塔堡（Kastellion／聖十字堡 1453：帶狀磚石的高牆與城垛、26 m 的高塔、巨鏈的鐵環、城門與熱那亞紅十字牌、院子裡的小堂、倉房、火藥間；九門 bombardella、塔頂兩門迴旋砲）',
            'use': 'fort', 'lot': (50, 40), 'M': M, 'style': 'genoa', 'flags': [flag],
            'layers': {'body': '院子（小堂、倉房、井）', 'rampart': '城牆、城垛、城門與石階（牆頂 ＝ 甲板）', 'tower': '高塔（塔頂 ＝ 甲板）、巨鏈的鐵環', 'magazine': '火藥間', 'roof': '屋頂',
                       'ladder': '塔裡的直梯（牆頂那一層 ⇒ 塔頂）'},
            'layer_meta': {'rampart': {'kind': 'deck', 'deck': 'wall', 'level': 1, 'name': '牆頂', 'floor': '0:%d,%d:%d' % (HW, X, HW), 'thick': 12, 'material': 'stone'},
                           'tower': {'kind': 'deck', 'deck': 'tower', 'level': 2, 'name': '塔頂', 'floor': '%d:%d,%d:%d' % (TX0, TH, TX1, TH), 'thick': 12, 'material': 'stone'},
                           'magazine': {'kind': 'magazine', 'pos': 'mid', 'powder_lb': 100 * len(kegs), 'material': 'stone', 'hoist': '塔裡的直梯（牆頂那一層 ⇒ 塔頂）/L1'},   # 塔頂的砲：火藥從直梯吊上去（取用點在梯腳、梯頭）
                           'ladder': {'kind': 'ladders'}},
            'layer_anchors': {'magazine': {'blast': (64, 78, 12), 'door': (MR[2], 74, 0)}, 'ladder': LA},
            'layer_models': {'rampart': guns_w, 'tower': guns_t, 'magazine': kegs}}


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
