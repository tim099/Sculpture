# 維吉尼亞號（CSS Virginia，1862；ex-USS Merrimack）產生程式 —— 一次算出整艘的格子，照部件分開寫成 stampvox 清單＋固定點／meta 的 JSON。
# 用法：python -I -X utf8 -B gen_virginia.py <輸出資料夾>
# 比例 0.1 m／格；X 船長（船頭 +X）、Y 船寬（中線 y=90，鏡像 y ↔ 180−y）、Z 高度（z=0 ＝ 龍骨底）。框 900×181×170；每個部件都用同一個框、關聯 at 0,0,0。
# 史料（Wikipedia CSS Virginia；USNI Naval History 2012-04；Mariners' Museum）：
#   全長約 263 ft（主甲板）＝ 80 m、寬 51 ft ＝ 15.6 m、吃水 21–22 ft；砲廓約 172 ft、側板斜 36°、24 吋橡松木＋兩層 2 吋鐵板；頂上 14 ft 寬的颶風甲板（格柵）、
#   前端錐形鐵駕駛塔；14 個砲門（船頭、船尾各 3：中線＋兩邊 45°，每舷 4）；兩舷各 1 門 6.4 吋 Brooke＋3 門 9 吋 Dahlgren、船頭船尾各 1 門 7 吋 Brooke（樞軸）；
#   鑄鐵撞角；一根煙囪、一具螺旋槳。
# 遊戲上的取捨（照實記）：
#   · 兩頭的甲板史料是「設計成淹在水下」⇒ 這裡放在水線上 0.4 m（z 69）—— 淹著的甲板，遊戲裡站在上面的人會被當成落水。
#   · 砲廓的下緣（knuckle）史料在水線下 2 ft ⇒ 這裡從甲板緣（z 66，水線上 0.1 m）開始斜上去：船殼側邊跟砲廓接在同一條線上。
#   · 鐵甲：水平 2 格（0.2 m ⇒ 垂直於斜面約 0.12 m ≈ 4.6 吋）；木背板水平 10 格（垂直約 0.59 m ≈ 23 吋）。
import sys, os, json, math
import numpy as np
from scipy import ndimage

NX, NY, NZ = 900, 181, 170
YC = 90
ZW = 65                      # 設計水線（格的 z；meta waterline_z）
ZDK = 66                     # 主甲板板的底（66–68 三格），走路格 69
ZFL = 69
K36 = 1 / math.tan(math.radians(36))   # 斜 36°：每升一格往裡 1.376 格
XS, XB = 48, 850             # 船尾（翼艉板）、船頭（艏柱）在甲板的 x
XM0, XM1 = 270, 620          # 船中段（全寬）
HB = 78                      # 半寬（15.6 m）
XC0, XC1, RC = 224, 748, 78  # 砲廓：x 範圍、兩頭的半徑（平面是兩頭圓的長方形）
ZTOP = 100                   # 砲廓頂（颶風甲板 97–100，走路格 101）
T_IRON, T_WOOD = 2, 12       # 鐵甲到 e < 2、木背板到 e < 12（e ＝ 平面往裡的距離 − 斜面該退的量）

# ── 顏色（rgb332）──
C_IRON, C_IRON_D, C_BLACK, C_COPPER = 73, 37, 36, 172
C_OAK, C_OAK_D, C_PINE, C_LIGHT = 136, 104, 177, 214

x = np.arange(NX); y = np.arange(NY); z = np.arange(NZ)
DY = np.abs(y - YC).astype(np.float64)


def hb_deck(xx):
    """主甲板的半寬（平面）。"""
    xx = np.asarray(xx, dtype=np.float64)
    out = np.full(xx.shape, float(HB))
    f = xx > XM1
    t = np.clip((xx[f] - XM1) / (XB - XM1), 0, 1); out[f] = HB * (1 - t ** 2.0) ** 0.7
    a = xx < XM0
    t = np.clip((XM0 - xx[a]) / (XM0 - XS), 0, 1); out[a] = 26 + (HB - 26) * (1 - t ** 2.2) ** 0.6   # 船尾：翼艉板寬 5.2 m
    out[(xx < XS) | (xx > XB)] = -1
    return out


def z_keel(xx):
    """船底（中線那一格的底；龍骨另外放在它下面）。船頭 forefoot 往上翹、船尾 counter 底在 z 48。"""
    xx = np.asarray(xx, dtype=np.float64)
    out = np.full(xx.shape, 6.0)
    b = xx > 760; out[b] = 6 + ((xx[b] - 760) / (XB - 760)) ** 2 * 24
    s = xx < 230; out[s] = 6 + ((230 - xx[s]) / (230 - 60)).clip(0, 1) ** 2.2 * 42   # 船尾的 run 從 x 230 慢慢翹上去（⛔ 太急 ⇒ 水線下的船尾收成一顆球）
    out[xx < 60] = 48
    return out


def section(u, xx):
    """橫剖面：u ＝ (z − 船底) ／ (60 − 船底)，0 ＝ 船底、1 ＝ 舷側直的那一段；兩頭比較尖（V）。"""
    end = np.clip(np.maximum((xx - XM1) / (XB - XM1), (XM0 - xx) / (XM0 - XS)), 0, 1)
    p = 2.8 - 1.4 * end
    u = np.clip(u, 0, 1)
    return (1 - (1 - u) ** p) ** (1 / 1.5)


def build():
    own = np.zeros((NX, NY, NZ), np.uint8)
    col = np.zeros((NX, NY, NZ), np.uint8)
    names = [None]
    stat = {}

    hole = {'m': None}                                           # 煙道裡面（空的）：誰都不能佔 ⇒ 甲板、颶風甲板在那裡開洞

    def claim(name, mask, color):
        m = mask & (own == 0)
        if hole['m'] is not None: m = m & ~hole['m']
        if name not in names: names.append(name)
        i = names.index(name)
        own[m] = i
        col[m] = color if np.isscalar(color) else color[m]
        stat[name] = stat.get(name, 0) + int(m.sum())
        return m

    X3 = x[:, None, None].astype(np.float64); Y3 = y[None, :, None]; Z3 = z[None, None, :].astype(np.float64)
    DY3 = np.abs(Y3 - YC)
    hbd = hb_deck(x)                                             # (NX,)
    zk = z_keel(x)
    # ── 船殼外形 ──
    u = (z[None, :] - zk[:, None]) / (60 - zk[:, None])          # (NX, NZ)
    sec = section(u, x[:, None].astype(np.float64))
    hbxz = np.where(z[None, :] >= zk[:, None], hbd[:, None] * sec, -1)   # (NX, NZ) 半寬
    hbxz[:, ZDK:] = -1                                            # 船殼側邊到 z 65；66 起是甲板
    hbxz[hbd < 0, :] = -1
    hull = DY3 <= hbxz[:, None, :]
    # 龍骨、艏柱、艉柱、deadwood（中線 ±3、船底以下到 z 0）
    keel = (DY3 <= 4) & (Z3 < zk[:, None, None] + 1) & (X3 >= 60) & (X3 <= XB) & (Z3 >= 0)
    stem = (DY3 <= 3) & (X3 >= XB - 5) & (X3 <= XB) & (Z3 >= 26) & (Z3 < ZDK)
    post = (DY3 <= 3) & (X3 >= 60) & (X3 <= 66) & (Z3 >= 0) & (Z3 < 50)
    dead = (DY3 <= 3) & (X3 >= 60) & (X3 < 230) & (Z3 < zk[:, None, None] + 1)
    # 螺旋槳的開口（deadwood 裡：x 67–79、z 10–46）
    aperture = (X3 >= 67) & (X3 <= 79) & (Z3 >= 10) & (Z3 <= 46) & (DY3 <= 4)
    solid = (hull | keel | stem | post | dead) & ~aperture
    # 殼厚：船外往裡的距離（頂面往上複製 ⇒ 甲板那一面不算船外）
    ext = np.concatenate([solid, np.repeat(solid[:, :, ZDK - 1:ZDK], 6, axis=2)], axis=2)
    d = ndimage.distance_transform_edt(ext)[:, :, :NZ]
    shell = solid & (d <= 5.0)
    inner = solid & ~shell                                         # 船艙（空的）
    backbone = (keel | stem | post | dead) & ~aperture
    # 包銅皮：水線下 2 格以上最外那一層（z ≤ 62）
    outer = solid & (d <= 1.0)
    claim('sheathing', outer & (Z3 <= ZW - 3) & ~backbone, C_COPPER)
    hullcol = np.where(Z3 >= ZW - 2, C_BLACK, C_OAK)
    claim('hull', backbone, C_OAK_D)
    claim('hull', shell, np.broadcast_to(hullcol, shell.shape))
    # 舵（艉柱後面：x 50–59、z 4–56，中線 ±1）、龍骨往後伸的 skeg 撐著舵底
    rudder = (DY3 <= 1) & (X3 >= 50) & (X3 <= 59) & (Z3 >= 4) & (Z3 <= 56)
    skeg = (DY3 <= 3) & (X3 >= 48) & (X3 < 60) & (Z3 <= 3)
    claim('hull', skeg, C_OAK_D)
    claim('hull', rudder, C_OAK_D)
    # 螺旋槳（兩葉，轂在 x 70–76、z 28；軸往前穿進 deadwood）
    hub = (X3 >= 70) & (X3 <= 76) & (DY3 <= 2) & (np.abs(Z3 - 28) <= 2)
    blade = (np.abs(X3 - 73) <= 1) & (np.abs(Z3 - 28) <= 17) & (np.abs(Z3 - 28) >= 2) & (DY3 <= 5 - np.abs(Z3 - 28) / 6)
    shaft = (X3 >= 77) & (X3 <= 250) & (DY3 <= 1) & (np.abs(Z3 - 28) <= 1)
    claim('engine', hub | blade, C_COPPER)
    # ── 煙道（Tim 2026-10-16：「煙囪跟發動機中間沒有連接(中間是炮甲板)」）：鍋爐頂 → 煙箱 → 直煙道穿住艙甲板以上、主甲板、砲甲板、颶風甲板 → 煙囪（z 101 起）──
    #   兩排鍋爐（y ＝ YC ∓ 17）頂上各一條橫煙道（x 336–437，避開中線 x 414–426 的梯子與艙口）匯到前排鍋爐前端頂上的煙箱（x 436–462），
    #   直煙道 ＝ 煙囪的延長（中心 x 450、外半徑 10、內半徑 8）。牆 2 格、裡面空的（hole：甲板在那裡開洞）；牆先佔 ⇒ 穿過甲板的那幾層是煙道牆。
    FNX = 450
    rt = np.hypot(X3 - FNX, Y3 - YC)
    sbox = (X3 >= 436) & (X3 <= 462) & (DY3 <= 26) & (Z3 >= 44) & (Z3 <= 52)
    sbox_in = (X3 >= 438) & (X3 <= 460) & (DY3 <= 24) & (Z3 >= 44) & (Z3 <= 50)          # 底是開的（接鍋爐頂）
    flue = np.zeros((NX, NY, NZ), bool); flue_in = np.zeros((NX, NY, NZ), bool)
    for ry in (YC - 17, YC + 17):
        dr = np.abs(Y3 - ry)
        flue |= (X3 >= 336) & (X3 <= 437) & (dr <= 7) & (Z3 >= 44) & (Z3 <= 50)
        flue_in |= (X3 >= 338) & (X3 <= 438) & (dr <= 5) & (Z3 >= 44) & (Z3 <= 48)   # 底是開的、前端通煙箱
    trunk = (rt <= 10) & (Z3 >= 51) & (Z3 <= ZTOP)
    trunk_in = (rt <= 8) & (Z3 >= 50) & (Z3 <= ZTOP)
    hole['m'] = sbox_in | flue_in | trunk_in
    claim('boiler', (sbox | flue | trunk) & ~hole['m'], C_IRON_D)
    # ── 撞角（鑄鐵：船頭水線下，x 851–868、z 34–54）──
    tr = (X3 - XB) / 18.0
    ram = (X3 > XB) & (X3 <= XB + 18) & (Z3 >= 34 + tr * 6) & (Z3 <= 54 - tr * 8) & (DY3 <= 7 * (1 - tr) + 1)
    claim('ram', ram, C_IRON)
    # ── 砲廓 ──
    xs0, xs1 = XC0 + RC, XC1 - RC                                  # 兩邊直的那一段
    dseg = np.where(X3 < xs0, np.hypot(X3 - xs0, DY3), np.where(X3 > xs1, np.hypot(X3 - xs1, DY3), DY3))
    dpl = np.minimum(RC - dseg, hbd[:, None, None] - DY3)            # 平面往裡的距離（不超出船殼）
    e = dpl - (Z3 - ZDK) * K36
    inz = (Z3 >= ZDK) & (Z3 <= ZTOP)
    iron = inz & (e >= 0) & ((e < T_IRON) | ((Z3 >= ZTOP - 1) & (e < T_WOOD)))   # 頂緣兩層也包鐵（⛔ 木背板露在頂上一圈）
    wood = inz & (e >= T_IRON) & (e < T_WOOD) & ~iron
    # 砲門
    S_PORTS = [330, 420, 510, 600]; P_PORTS = [375, 465, 555, 645]   # 兩舷錯開（史料：砲廓只有 30 ft 寬，後座要錯開）
    PZ0, PZ1, PW = 76, 86, 5
    ports = np.zeros((NX, NY, NZ), bool)
    for px in S_PORTS: ports |= (np.abs(X3 - px) <= PW) & (Y3 > YC) & (Z3 >= PZ0) & (Z3 <= PZ1)
    for px in P_PORTS: ports |= (np.abs(X3 - px) <= PW) & (Y3 < YC) & (Z3 >= PZ0) & (Z3 <= PZ1)
    for cx, sgn in ((xs1, 1), (xs0, -1)):                           # 船頭、船尾：中線＋左右 45°
        for ang in (0, 45, -45):
            a = math.radians(ang); ux, uy = sgn * math.cos(a), math.sin(a)
            along = (X3 - cx) * ux + (Y3 - YC) * uy; perp = np.abs(-(X3 - cx) * uy + (Y3 - YC) * ux)
            ports |= (along > 20) & (perp <= PW) & (Z3 >= PZ0) & (Z3 <= PZ1)
    claim('casemate-iron', iron & ~ports, C_IRON)
    claim('casemate-wood', wood & ~ports, C_OAK_D)
    # 颶風甲板（頂：z 97–100，格柵：每 3 格一條鐵條、中間是木框；三個艙口兩個放梯子）
    roof = (Z3 >= ZTOP - 3) & (Z3 <= ZTOP) & (e >= T_WOOD)
    grate = roof & ((((X3.astype(int) % 3) == 0) | ((Y3 % 3) == 0)) | (Z3 < ZTOP))
    HATCH_ROOF = [(360, YC), (600, YC)]
    for hx, hy in HATCH_ROOF: grate &= ~((np.abs(X3 - hx) <= 6) & (np.abs(Y3 - hy) <= 5))
    claim('hurricane', grate & (Z3 == ZTOP), C_IRON)              # 格柵的鐵條 ＝ 跟砲廓同一種鐵灰（⛔ 37 號在遊戲的光下偏藍）
    claim('hurricane', grate & (Z3 < ZTOP), C_OAK_D)
    # 颶風甲板的邊（砲廓頂的木頭邊上那一圈欄杆座）
    # ── 主甲板（66–68，整個船殼；梯子的艙口挖掉）＋橫樑（63–65 每 24 格一根，只在船艙裡）──
    deck_area = (DY3 <= hbd[:, None, None]) & (hbd[:, None, None] > 0)
    HATCH_MAIN = [(420, YC), (560, YC)]
    hatch_main = np.zeros((NX, NY, NZ), bool)
    for hx, hy in HATCH_MAIN: hatch_main |= (np.abs(X3 - hx) <= 7) & (np.abs(Y3 - hy) <= 5)
    plank = deck_area & (Z3 >= ZDK) & (Z3 <= ZDK + 2) & ~hatch_main
    pcol = np.where((Y3 % 4) == 0, C_OAK, C_PINE)
    claim('deck-main', plank, np.broadcast_to(pcol, plank.shape))
    # 吊錨木（cathead）：船頭兩舷各一根，從甲板伸出舷外 1.5 m（z 69–70）；錨的 ring 掛在它外端底下（遊戲照 ring 找撐住它的那一格）
    cat = (np.abs(X3 - 790) <= 2) & (Z3 >= ZFL) & (Z3 <= ZFL + 1) & (DY3 >= 36) & (DY3 <= 60)
    claim('deck-main', cat, C_OAK_D)
    beams = inner & (Z3 >= ZDK - 3) & (Z3 < ZDK) & ((X3.astype(int) % 24) < 3) & ~hatch_main
    claim('deck-main', beams, C_OAK)
    # ── 住艙甲板（44–46，走路格 47）、艙底甲板（20–22，走路格 23）：船艙裡 ──
    ZB, ZH = 44, 20
    HATCH_BERTH = [(475, YC), (620, YC)]
    hatch_b = np.zeros((NX, NY, NZ), bool)
    for hx, hy in HATCH_BERTH: hatch_b |= (np.abs(X3 - hx) <= 7) & (np.abs(Y3 - hy) <= 5)
    berth = inner & (Z3 >= ZB) & (Z3 <= ZB + 2) & (X3 >= 110) & (X3 <= 800) & ~hatch_main & ~hatch_b
    claim('deck-berth', berth, np.broadcast_to(pcol, berth.shape))
    hold = inner & (Z3 >= ZH) & (Z3 <= ZH + 2) & (X3 >= 190) & (X3 <= 720)
    claim('deck-hold', hold, np.broadcast_to(np.where((Y3 % 4) == 0, C_OAK_D, C_OAK), hold.shape))
    # ── 機艙：四座鍋爐（橫躺的圓筒，空心；部件「鍋爐」，跟煙道一起，造船規格 §9.6）＋主機（箱，空心）＋軸 ──
    boil = np.zeros((NX, NY, NZ), bool); boilers = []
    for bx0, bx1 in ((330, 392), (400, 462)):
        for by in (YC - 17, YC + 17):
            r = np.hypot(Y3 - by, Z3 - 35)
            boil |= (X3 >= bx0) & (X3 <= bx1) & (r <= 12) & ((r >= 10.5) | (X3 <= bx0 + 1) | (X3 >= bx1 - 1))
            boilers.append([(bx0 + bx1) // 2, by, 35])
    claim('boiler', boil & inner, C_IRON_D)
    eng = np.zeros((NX, NY, NZ), bool)
    box = (X3 >= 255) & (X3 <= 318) & (DY3 <= 20) & (Z3 >= ZH + 3) & (Z3 <= 42)
    boxin = (X3 >= 257) & (X3 <= 316) & (DY3 <= 18) & (Z3 >= ZH + 3) & (Z3 <= 40)
    eng |= box & ~boxin
    claim('engine', eng & inner, C_IRON_D)
    # 軸（部件「軸」，kind=shaft；TASK-0653：傳動件 ⇒ 照「通不通、還有幾條路」把主機的動力傳到螺旋槳）：x 77（轂後）–250（主機前）、中線 ±1、z 27–29
    claim('shaft', shaft & ~solid, C_IRON_D)
    claim('shaft', shaft & solid & (own == 0), C_IRON_D)
    # ── 彈藥庫（艙底甲板上：前 x 640–690、後 x 200–245）：銅皮內襯的房間、門洞 5 格寬 ──
    mags = {}
    for nm, x0_, x1_ in (('magazine-fore', 640, 690), ('magazine-aft', 200, 245)):
        zt = ZH + 3 + 19
        hw = 22
        room = (X3 >= x0_) & (X3 <= x1_) & (DY3 <= hw) & (Z3 >= ZH + 3) & (Z3 <= zt)
        air = (X3 > x0_) & (X3 < x1_) & (DY3 < hw) & (Z3 >= ZH + 3) & (Z3 < zt)
        dx = x0_ if nm == 'magazine-fore' else x1_                  # 門：朝船中段那一面
        door = (np.abs(X3 - dx) <= 0) & (DY3 <= 2) & (Z3 >= ZH + 3) & (Z3 <= ZH + 3 + 15)
        wall = room & ~air & ~door & inner
        claim(nm, wall, C_COPPER)
        cx_, cy_, cz_ = (x0_ + x1_) // 2, YC, ZH + 3 + 8
        mags[nm] = {'blast': [cx_, cy_, cz_], 'door': [dx + (-1 if nm == 'magazine-fore' else 1), YC, ZH + 3], 'kegs': 60 if nm == 'magazine-fore' else 40}
    # ── 駕駛塔（錐形鐵塔：砲廓頂前端）、煙囪、旗桿 ──
    PH = (660, YC, ZTOP + 1)
    r = np.hypot(X3 - PH[0], Y3 - PH[1]); rz = 14 - (Z3 - PH[2]) * 0.5
    ph = (Z3 >= PH[2]) & (Z3 <= PH[2] + 12) & (r <= rz) & ((r >= rz - 2) | (Z3 >= PH[2] + 11))
    slit = (Z3 >= PH[2] + 8) & (Z3 <= PH[2] + 9) & (((np.abs(Y3 - YC) <= 1)) | (np.abs(X3 - PH[0]) <= 1))
    doorph = (X3 < PH[0]) & (np.abs(Y3 - YC) <= 3) & (Z3 <= PH[2] + 6)
    claim('pilothouse', ph & ~slit & ~doorph, C_IRON)
    FN = (450, YC)
    r = np.hypot(X3 - FN[0], Y3 - FN[1])
    fun = (Z3 >= ZTOP + 1) & (Z3 <= ZTOP + 45) & (r <= 10) & (r >= 8)
    collar = (Z3 >= ZTOP + 1) & (Z3 <= ZTOP + 3) & (r <= 12) & (r >= 8)
    claim('funnel', fun | collar, C_BLACK)
    FS = (300, YC)
    pole = (np.abs(X3 - FS[0]) <= 0) & (np.abs(Y3 - FS[1]) <= 0) & (Z3 >= ZTOP + 1) & (Z3 <= ZTOP + 40)
    claim('hurricane', pole, C_OAK_D)
    # ── 梯子（每座：兩根側板＋每 3 格一階；往 +x 爬）──
    ladders = []
    LAD = [('main-roof-a', 360, ZFL, ZTOP + 1), ('main-roof-f', 600, ZFL, ZTOP + 1),
           ('berth-main-a', 420, ZB + 3, ZFL), ('berth-main-f', 560, ZB + 3, ZFL),
           ('hold-berth-a', 475, ZH + 3, ZB + 3), ('hold-berth-f', 620, ZH + 3, ZB + 3)]
    lad = np.zeros((NX, NY, NZ), bool); ltread = np.zeros((NX, NY, NZ), bool)
    for nm, hx, z0_, z1_ in LAD:
        H = z1_ - z0_; run = int(round(H * 0.55)); xa = hx + 6 - run   # 往 +x 爬，頂端在艙口前緣（hx＋7）往後一格 ⇒ 上去就踩到上層甲板
        steps = []
        for k in range(1, H // 3 + 1):
            zz = z0_ + 3 * k - 1; xx = int(round(xa + run * (zz - z0_) / H))
            if zz >= z1_ - 1: break
            steps.append((xx, zz))
            ltread |= (np.abs(X3 - xx) <= 1) & (np.abs(Y3 - YC) <= 2) & (Z3 == zz)
        for zz in range(z0_, z1_ - 1):
            xx = xa + run * (zz - z0_) / H
            lad |= (np.abs(X3 - xx) <= 1) & (np.abs(Y3 - YC) == 3) & (Z3 == zz)
        lo, hi = steps[0], steps[-1]
        ladders.append({'name': nm, 'foot': [int(xa - 3), YC, z0_], 'lo': [lo[0], YC, lo[1] + 1], 'hi': [hi[0], YC, hi[1] + 1], 'head': [hx + 9, YC, z1_]})
    claim('ladders', lad | ltread, C_OAK)
    meta = {'names': names, 'stat': stat, 'ladders': ladders, 'mags': mags, 'ports': {'S': S_PORTS, 'P': P_PORTS}, 'pilothouse': PH, 'funnel': FN, 'flagstaff': [FS[0], FS[1], ZTOP + 40],
            'boilers': boilers, 'uptake': [449, YC, 44]}   # 鍋爐：每座中心（boiler-1…4）、煙道底（煙箱底那一片的中心）
    return own, col, names, meta


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    own, col, names, meta = build()
    counts = {}
    for i, nm in enumerate(names):
        if not nm: continue
        idx = np.argwhere(own == i)
        cs = col[own == i]
        order = np.lexsort((idx[:, 2], idx[:, 1], idx[:, 0]))
        idx, cs = idx[order], cs[order]
        with open(os.path.join(out, 'part_%s.txt' % nm), 'w', newline='\n') as f:
            f.write('# 維吉尼亞號 %s —— x,y,z,color（框 %d×%d×%d、關聯 at 0,0,0）\n' % (nm, NX, NY, NZ))
            f.write('\n'.join('%d,%d,%d,%d' % (a, b, c, k) for (a, b, c), k in zip(idx.tolist(), cs.tolist())))
            f.write('\n')
        counts[nm] = len(idx)
    # 對稱：每個部件 y ↔ 180−y 逐格（含顏色）
    sym = {}
    for i, nm in enumerate(names):
        if not nm: continue
        m = own == i
        sym[nm] = int((m != m[:, ::-1, :]).sum())
    # 連通：全部的格 6 連通幾塊
    lab, n = ndimage.label(own > 0)
    sizes = np.bincount(lab.ravel())[1:]
    meta.update(counts=counts, mirror_diff=sym, components=int(n), small=sorted(sizes.tolist())[:-1][-10:] if n > 1 else [])
    # 排水（設計水線以下，跟遊戲 hydrostatics 同一個算法：每個 x、每一層最外兩格之間的寬）
    tot = own > 0
    vol = 0
    for zz in range(ZW):
        lay = tot[:, :, zz]
        anyy = lay.any(axis=1)
        lo = np.argmax(lay, axis=1); hi = NY - 1 - np.argmax(lay[:, ::-1], axis=1)
        vol += int(((hi - lo + 1) * anyy).sum())
    meta['disp_t'] = round(vol * 0.001 * 1.025, 1)
    json.dump(meta, open(os.path.join(out, 'virginia_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: meta[k] for k in ('counts', 'mirror_diff', 'components', 'small', 'disp_t')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
