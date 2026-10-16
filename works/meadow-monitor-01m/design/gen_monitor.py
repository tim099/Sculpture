# 莫尼特號（USS Monitor，1862；漢普頓錨地海戰）產生程式 —— 一次算出整艘的格子，照部件分開寫成 stampvox 清單＋固定點／meta 的 JSON。
# 用法：python -I -X utf8 -B gen_monitor.py <輸出資料夾>
# 比例 0.1 m／格；X 船長（船頭 +X）、Y 船寬（中線 y=65，鏡像 y ↔ 130−y）、Z 高度（z=0 ＝ 龍骨底）。每個部件都用同一個框、關聯 at 0,0,0。
# 數字全部讀 plan.json 的 params；每個數字的出處（原圖讀數／參考資料／設計決定）在 plan.json 的 provenance。
# 結構：下船殼（鐵、斜邊平底、兩頭斜收）＋浮筏（armor raft：外 2 格鐵甲、7 格橡木背襯、兩頭懸出）＋甲板（鐵板＋木）
#       船頭：錨井、駕駛塔；中段：砲塔（外部模型）坐在中隔艙壁上；後段：鍋爐、煙囪、主機、軸、螺旋槳（外部模型）、平衡舵。
import sys, os, json, math
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P = PLAN['params']

NX, NY, NZ = P['frame']
YC = (NY - 1) // 2
ZW = P['z_waterline']            # 設計水線（meta waterline_z）
ZD = P['z_deck_top']             # 甲板最上一層（鐵板）；走路格 ZFL
ZFL = ZD + 1
DL = P['deck_layers']
ZDB = ZD - DL + 1                # 甲板最下一層
ZR0 = P['z_raft_bottom']         # 浮筏底
ZLT = ZR0 - 1                    # 下船殼頂那一層
XS, XB = P['x_raft']
HB = P['half_beam']
XM0, XM1 = P['x_full']
XT0, XT1 = P['x_lower_top']
XB0, XB1 = P['x_lower_bottom']
HL, HF = P['half_beam_lower'], P['half_flat']
T_IRON, T_WOOD = P['t_iron'], P['t_wood']
ZB = P['z_berth_top']            # 住艙甲板最上一層；走路格 ZB+1
ZBF = ZB + 1

C = P['colors']
x = np.arange(NX); y = np.arange(NY); z = np.arange(NZ)


def hb_raft(xx):
    """浮筏的半寬：中段平行（XM0..XM1），兩頭照 (1 − t^a)^b 收成弧形尖頭（兩頭同形）。"""
    xx = np.asarray(xx, dtype=np.float64)
    a, b = P['end_pow']
    out = np.full(xx.shape, float(HB))
    f = xx > XM1; t = np.clip((xx[f] - XM1) / (XB - XM1), 0, 1); out[f] = HB * (1 - t ** a) ** b
    s = xx < XM0; t = np.clip((XM0 - xx[s]) / (XM0 - XS), 0, 1); out[s] = HB * (1 - t ** a) ** b
    out[(xx < XS) | (xx > XB)] = -1
    return out


def lower_half(X2, Z2):
    """下船殼在 (x, z) 的半寬：截面 ＝ 平底 HF 斜到頂 HL；兩頭斜收（rake：平底 XB0..XB1、頂 XT0..XT1）、平面收成尖頭。"""
    u = np.clip(Z2 / ZLT, 0, 1)
    sec = HF + (HL - HF) * u
    e0 = XB0 + (XT0 - XB0) * u; e1 = XB1 + (XT1 - XB1) * u        # 這一層的兩端
    Lend = P['end_len']
    s0 = np.clip((e0 + Lend - X2) / Lend, 0, 1); s1 = np.clip((X2 - (e1 - Lend)) / Lend, 0, 1)
    tp = (1 - np.maximum(s0, s1) ** 2) ** 0.6
    out = sec * tp
    out[(X2 < e0) | (X2 > e1) | (Z2 > ZLT) | (Z2 < 0)] = -1
    return out


def build():
    own = np.zeros((NX, NY, NZ), np.uint8)
    col = np.zeros((NX, NY, NZ), np.uint8)
    names = [None]
    stat = {}

    def claim(name, mask, color):
        m = mask & (own == 0)
        if name not in names: names.append(name)
        i = names.index(name)
        own[m] = i
        col[m] = color if np.isscalar(color) else np.broadcast_to(color, m.shape)[m]
        stat[name] = stat.get(name, 0) + int(m.sum())
        return m

    X3 = x[:, None, None].astype(np.float64); Y3 = y[None, :, None].astype(np.float64); Z3 = z[None, None, :].astype(np.float64)
    DY3 = np.abs(Y3 - YC)
    anc = {}
    hull_col = np.where(Z3 >= ZW, C['black'], C['red'])                 # 水線（30.5）以上黑、以下紅

    # ── 下船殼 ──
    X2, Z2 = np.meshgrid(x.astype(float), z.astype(float), indexing='ij')
    hl = lower_half(X2, Z2)                                             # (NX, NZ)
    lower = DY3 <= hl[:, None, :]
    ext = lower.copy(); ext[:, :, ZR0:ZR0 + 8] |= lower[:, :, ZLT:ZLT + 1]   # 頂面往上複製 ⇒ 接浮筏那一面不算船外
    d = ndimage.distance_transform_edt(ext)
    shell_l = lower & (d <= 2.0)
    inner_l = lower & ~shell_l
    # ── 浮筏（z ZR0..ZD；平面 hb_raft）──
    hbr = hb_raft(x)
    plan2 = (np.abs(y[None, :] - YC) <= hbr[:, None]) & (hbr[:, None] > 0)
    e = ndimage.distance_transform_edt(np.pad(plan2, 1))[1:-1, 1:-1][:, :, None]   # 平面往裡的距離（邊緣那一格 ＝ 1）
    raft = plan2[:, :, None] & (Z3 >= ZR0) & (Z3 <= ZD)
    iron = raft & (e <= T_IRON)
    wood = raft & (e > T_IRON) & (e <= T_IRON + T_WOOD) & (Z3 < ZDB)
    over_l = (DY3 <= hl[:, None, ZLT:ZLT + 1])                          # 下船殼頂那一圈正上方（浮筏底在這裡開口通進下船殼）
    raft_floor = raft & (Z3 <= ZR0 + 1) & (e > T_IRON) & ~over_l
    raft_in = raft & (e > T_IRON + T_WOOD) & (Z3 >= ZR0 + 2) & (Z3 < ZDB)
    hold = inner_l | raft_in | (raft & over_l & (e > T_IRON + T_WOOD) & (Z3 < ZDB))   # 船裡的空間（艙）
    # 螺旋槳井（浮筏船尾懸出部分的底挖開；井壁一格鐵、頂在 z w_top）
    w0, w1, whw, wtop = P['prop_well']
    well = (X3 >= w0) & (X3 <= w1) & (DY3 <= whw) & (Z3 >= ZR0) & (Z3 <= wtop)
    well_wall = (X3 >= w0 - 1) & (X3 <= w1 + 1) & (DY3 <= whw + 1) & (Z3 >= ZR0) & (Z3 <= wtop + 1) & ~well & raft
    # 錨井（船頭懸出部分：圓筒、底通海、頂是甲板）
    ax_, ar_ = P['anchor_well']
    rw = np.hypot(X3 - ax_, Y3 - YC)
    awell = (rw < ar_) & (Z3 >= ZR0) & (Z3 < ZDB)
    awall = (rw >= ar_) & (rw < ar_ + 1) & (Z3 >= ZR0) & (Z3< ZDB) & raft
    cut = well | awell
    # ── 船殼部件（關聯「船殼」，material iron）──
    claim('hull', shell_l, hull_col)
    claim('hull', well_wall | awall, C['iron'])
    # skeg（龍骨往後伸、撐舵底）＋舵（平衡舵）＋舵軸（往上穿進浮筏到甲板底）
    sk0, sk1 = P['skeg']
    claim('hull', (DY3 <= 2) & (Z3 <= 1) & (X3 >= sk0) & (X3 <= sk1 + 2), C['iron'])
    r0, r1, rz0, rsx = P['rudder']
    claim('hull', (DY3 <= 1) & (X3 >= r0) & (X3 <= r1) & (Z3 >= rz0) & (Z3 < ZR0) & ~((X3 > r1 - 3) & (Z3 < rz0 + 3)), C['iron'])
    claim('hull', (DY3 <= 1) & (np.abs(X3 - rsx) <= 1) & (Z3 >= 2) & (Z3 < ZDB) & ~well, C['iron'])
    # 中隔艙壁（砲塔的中軸立在上面）：船艙裡一整片、中間一道門
    bx = P['bulkhead_x']
    bulk = hold & (X3 == bx) & (Z3 >= 2) & ~((DY3 <= 2) & (Z3 >= ZBF) & (Z3 <= ZBF + 19))
    claim('hull', bulk, C['iron'])
    # ── 浮筏：鐵甲（水線上黑、下紅）、木背襯、底板 ──
    claim('raft-iron', iron & ~cut, hull_col)
    claim('raft-wood', (wood | raft_floor) & ~cut, C['oak_d'])
    # ── 主甲板：ZDB..ZD（最上一層鐵板、下面木）；艙口；樑（每 beam_pitch 格一根，3 格深，只在艙裡）──
    hatches = np.zeros((NX, NY, NZ), bool)
    for hx, hy, hw, hh in P['hatches_main']:
        hatches |= (np.abs(X3 - hx) <= hw) & (np.abs(Y3 - hy) <= hh)
    FX, FDY, FH, FZ = P['funnel']
    fhole = np.zeros((NX, NY, NZ), bool)
    for sy in (1, -1):
        fhole |= (np.abs(X3 - FX) <= FH - 2) & (np.abs(Y3 - (YC + sy * FDY)) <= FH - 2)
    deck = raft & (Z3 >= ZDB) & (e > T_IRON) & ~hatches & ~fhole
    TX = P['turret_x']
    rt = np.hypot(X3 - TX, Y3 - YC)
    # 砲塔底下原本嵌一圈青銅環（C['brass']）；Tim 2026-10-16：遊戲裡砲塔外緣露出黃色鋸齒、像破圖 ⇒ 拿掉，那一圈照甲板的顏色
    claim('deck-main', deck & (Z3 == ZD), C['deck'])
    claim('deck-main', deck & (Z3 < ZD), C['oak'])
    beams = hold & (Z3 >= ZDB - 3) & (Z3 < ZDB) & ((X3.astype(int) % P['beam_pitch']) < 2) & ~hatches & ~cut & ~fhole
    claim('deck-main', beams, C['oak_d'])
    # ── 住艙甲板（下船殼裡；ZB−1..ZB）──
    xb0, xb1 = P['x_berth']
    berth = inner_l & (Z3 >= ZB - 1) & (Z3 <= ZB) & (X3 >= xb0) & (X3 <= xb1)
    claim('deck-berth', berth, np.where((Y3.astype(int) % 4) == 0, C['oak_d'], C['pine']))
    # ── 駕駛塔（鐵塊疊成的方塔；最上一層與第二層之間是觀察縫，四角留著；頂板是 2 in 的蓋）──
    phx, phl, phw, phh, pht = P['pilothouse']
    box = (np.abs(X3 - phx) <= phl) & (DY3 <= phw) & (Z3 >= ZFL) & (Z3 < ZFL + phh)
    inn = (np.abs(X3 - phx) <= phl - pht) & (DY3 <= phw - pht) & (Z3 < ZFL + phh - 1)
    corner = (np.abs(X3 - phx) > phl - pht - 1) & (DY3 > phw - pht - 1)
    slit = (Z3 == ZFL + phh - 5) & ~corner
    claim('pilothouse', box & ~inn & ~slit, C['iron'])
    # ── 煙囪（方形、空心；一舷 S，P 舷用鏡像關聯）＋煙道（鍋爐頂往上穿甲板）──
    fcy = YC + FDY
    fo = (np.abs(X3 - FX) <= FH) & (np.abs(Y3 - fcy) <= FH)
    fi = (np.abs(X3 - FX) <= FH - 2) & (np.abs(Y3 - fcy) <= FH - 2)
    claim('funnel', fo & ~fi & (Z3 >= ZFL) & (Z3 < ZFL + FZ), C['black'])
    anc['funnel'] = {'smoke': [FX, fcy, ZFL + FZ - 1]}
    # ── 鍋爐（兩座並排；一舷 S，P 舷鏡像關聯）：實心箱（鐵殼＋滿水）、前面爐門 ──
    bx0, bx1 = P['x_boilers']; bhw, bdy, bh = P['boiler']
    bcy = YC + bdy
    boiler = (X3 >= bx0) & (X3 <= bx1) & (np.abs(Y3 - bcy) <= bhw) & (Z3 >= ZBF) & (Z3 < ZBF + bh)
    doors = boiler & (X3 == bx0) & (np.abs(Y3 - bcy) <= bhw - 3) & (((Z3 - ZBF) % 7) >= 2) & (((Z3 - ZBF) % 7) <= 4) & (Z3 < ZBF + 14)
    claim('boilers', doors & hold, C['black'])
    claim('boilers', boiler & hold, C['iron'])
    upt = fo & ~fi & (Z3 >= ZBF + bh) & (Z3 <= ZD) & ~deck
    claim('boilers', upt, C['black'])
    anc['boilers'] = {'boiler-1': [(bx0 + bx1) // 2, bcy, ZBF + bh // 2], 'uptake': [FX, fcy, ZBF + bh]}
    # ── 主機（振動槓桿式：一個橫置的汽缸鑄件兩頭各一活塞、兩組槓桿、單一曲柄）＋平台＋凝汽器（右舷後）──
    ex0, ex1 = P['x_engine']; ecx, ecz, ecr, ehl = P['engine_cyl']
    eng = (X3 >= ex0) & (X3 <= ex1) & (DY3 <= ehl + 2) & (Z3 >= ZBF) & (Z3 <= ZBF + 1)                   # 平台
    eng |= (np.hypot(X3 - ecx, Z3 - ecz) <= ecr) & (DY3 <= ehl)                                        # 汽缸（沿 y）
    eng |= (np.hypot(X3 - ecx, Z3 - ecz) <= ecr + 1) & (np.abs(DY3 - ehl) <= 1)                        # 兩頭的缸蓋
    for sx in (-1, 1):                                                                              # 槓桿的架子（兩片、在汽缸前後）
        eng |= (np.abs(X3 - (ecx + sx * (ecr + 4))) <= 1) & (DY3 <= ehl - 4) & (Z3 >= ZBF + 2) & (Z3 <= ecz + ecr + 6) & ((DY3 >= ehl - 7) | (Z3 >= ecz + ecr + 4))
    eng |= (np.abs(X3 - ex0 - 2) <= 2) & (np.hypot(Y3 - YC, Z3 - P['screw'][1]) <= 4)                  # 曲柄盤
    eng |= (X3 >= ex0) & (X3 <= ex0 + 10) & (Y3 >= YC + 20) & (Y3 <= YC + 27) & (Z3 >= ZBF + 2) & (Z3 <= ZBF + 15)   # 凝汽器（右舷）
    claim('engine', eng & hold, C['iron'])
    anc['engine'] = {'core': [ecx, YC, ecz], 'cyl-1': [ecx, YC - ehl + 3, ecz], 'cyl-2': [ecx, YC + ehl - 3, ecz]}
    # ── 軸（主機曲柄 → 螺旋槳轂）──
    sx_, sz_, sr_ = P['screw']
    shaft = (X3 >= sx_ + 3) & (X3 <= ex0 + 1) & (np.hypot(Y3 - YC, Z3 - sz_) <= 1.3)
    claim('shaft', shaft & (own == 0), C['iron'])
    anc['shaft'] = {'aft': [sx_ + 3, YC, sz_], 'fwd': [ex0, YC, sz_]}
    # ── 螺旋槳（四葉、9 ft；外部模型的來源 ⇒ 部件 screw，用整船的框）──
    ang = np.arctan2(Z3 - sz_, Y3 - YC); rr_ = np.hypot(Y3 - YC, Z3 - sz_)
    da = (ang - np.pi / 4) % (np.pi / 2); da = np.minimum(da, np.pi / 2 - da)
    arc = da * rr_
    half = 1.2 + 4.0 * np.sin(np.pi * np.clip(rr_ / sr_, 0, 1)) ** 0.8
    sgn = np.sign(((ang - np.pi / 4) % (np.pi / 2)) - np.pi / 4)
    blade = (rr_ <= sr_) & (rr_ > 2) & (arc <= half) & (np.abs(X3 - sx_ - sgn * arc * 0.35) <= 1)
    hub = (np.abs(X3 - sx_) <= 2) & (rr_ <= 2.5)
    hub |= (X3 > sx_ + 2) & (X3 <= sx_ + 4) & (rr_ <= 1.8)                                           # 轂往前一小段接軸
    claim('screw', hub | blade, C['iron'])
    anc['screw'] = {'hub': [sx_, YC, sz_], 'shaft-fwd': [sx_ + 4, YC, sz_]}
    # ── 甲板設備：鼓風機進氣管（兩根方管、機艙上方）──
    BX, BDY, BH, BZ = P['blowers']
    bl = np.zeros((NX, NY, NZ), bool)
    for sy in (1, -1):
        cyy = YC + sy * BDY
        o = (np.abs(X3 - BX) <= BH) & (np.abs(Y3 - cyy) <= BH) & (Z3 >= ZFL) & (Z3 < ZFL + BZ)
        i = (np.abs(X3 - BX) <= BH - 1) & (np.abs(Y3 - cyy) <= BH - 1) & (Z3 >= ZFL) & (Z3 < ZFL + BZ - 1)
        lid = (np.abs(X3 - BX) <= BH + 1) & (np.abs(Y3 - cyy) <= BH + 1) & (Z3 == ZFL + BZ)             # 頂蓋（擋雨，四面通氣）
        bl |= (o & ~i & ~((Z3 >= ZFL + BZ - 4) & (Z3 < ZFL + BZ - 1) & ~((np.abs(X3 - BX) == BH) & (np.abs(Y3 - cyy) == BH)))) | lid
    claim('deck-fittings', bl, C['black'])
    # ── 艙房（住艙甲板上：軍官艙在前、住艙、彈藥庫（右舷）、砲彈艙（左舷）、廚房爐）──
    zr0, zr1 = ZBF, ZDB - 4                                              # 牆從住艙甲板到樑底
    def room_walls(x0_, x1_, y0_, y1_, door_face, door_w=2):
        box = (X3 >= x0_) & (X3 <= x1_) & (Y3 >= y0_) & (Y3 <= y1_) & (Z3 >= zr0) & (Z3 <= zr1)
        inner = (X3 > x0_) & (X3 < x1_) & (Y3 > y0_) & (Y3 < y1_) & (Z3 < zr1)
        cyy = (y0_ + y1_) // 2; cxx = (x0_ + x1_) // 2
        if door_face == 'x+': door = (X3 == x1_) & (np.abs(Y3 - cyy) <= door_w)
        elif door_face == 'x-': door = (X3 == x0_) & (np.abs(Y3 - cyy) <= door_w)
        elif door_face == 'y+': door = (Y3 == y1_) & (np.abs(X3 - cxx) <= door_w)
        else: door = (Y3 == y0_) & (np.abs(X3 - cxx) <= door_w)
        door = door & (Z3 < zr0 + 19)
        return box & ~inner & ~door & hold
    m0, m1, my0, my1, mzh = P['magazine']
    claim('magazine', room_walls(m0, m1, my0, my1, 'x+'), C['lead'])
    mags = {'magazine': {'link': '彈藥庫', 'pos': 'mid', 'blast': [(m0 + m1) // 2, (my0 + my1) // 2, ZBF + 8], 'door': [m1 + 1, (my0 + my1) // 2, ZBF]}}
    # 火藥桶的位置（憲法號元件 4.4×4.4 格、每 5 格一個；門那一頭留 5 格走道）
    spots = [[xx + 0.5, yy + 0.5, ZBF] for xx in range(m0 + 3, m1 - 6, 5) for yy in range(my0 + 3, my1 - 1, 5)]
    s0, s1, sy0, sy1, szh = P['shellroom']
    cab = room_walls(s0, s1, sy0, sy1, 'x+')
    # 軍官艙：前段兩舷各一排（每間 2.4 m）、中間是 wardroom；最前面船長艙
    ox0, ox1 = 400, 476
    for k, cx0 in enumerate(range(ox0, ox1, 24)):
        for sgn_ in (1, -1):
            ya, yb = (YC + 14, YC + 40) if sgn_ > 0 else (YC - 40, YC - 14)
            cab |= room_walls(cx0, min(cx0 + 24, ox1), ya, yb, 'y-' if sgn_ > 0 else 'y+')
    cab |= hold & (X3 == ox0) & (DY3 <= 13) & (Z3 >= zr0) & (Z3 <= zr1) & ~(DY3 <= 3)               # wardroom 的後艙壁（中間門）
    stove = (X3 >= bx - 12) & (X3 <= bx - 4) & (np.abs(Y3 - YC + 8) <= 4) & (Z3 >= ZBF) & (Z3 <= ZBF + 8)   # 中隔艙壁後的廚房爐（背靠鍋爐那一側）
    claim('cabins', stove & hold, C['black'])
    claim('cabins', cab, C['white'])
    # ── 梯子（每座：兩根側板＋每 3 格一階；dirx ＝ 往哪個 x 方向爬）──
    ladders = []
    for nm, hx, z0_, z1_, dirx in P['ladders']:
        Hh = z1_ - z0_; run = int(round(Hh * 0.55))
        xa = hx - dirx * (run - 6)
        steps = []; m = np.zeros((NX, NY, NZ), bool)
        for k in range(1, Hh // 3 + 1):
            zz = z0_ + 3 * k - 1; xx = int(round(xa + dirx * run * (zz - z0_) / Hh))
            if zz >= z1_ - 1: break
            steps.append((xx, zz))
            m |= (np.abs(X3 - xx) <= 1) & (np.abs(Y3 - YC) <= 2) & (Z3 == zz)
        for zz in range(z0_, z1_ - 1):
            xx = xa + dirx * run * (zz - z0_) / Hh
            m |= (np.abs(X3 - xx) <= 1) & (np.abs(Y3 - YC) == 3) & (Z3 == zz)
        claim('ladders', m, C['oak'])
        lo, hi = steps[0], steps[-1]
        ladders.append({'name': nm, 'foot': [int(round(xa - dirx * 3)), YC, z0_], 'lo': [lo[0], YC, lo[1] + 1], 'hi': [hi[0], YC, hi[1] + 1], 'head': [hx + dirx * 9, YC, z1_]})
    anc['ladders'] = ladders
    anc['mags'] = mags
    # ── 封閉空腔：≤ 50 格的填實（同色木頭；造船規格 §8）——煙囪、鍋爐的鏡像也算進去 ──
    full = own > 0
    for nm in ('funnel', 'boilers'):
        full |= (own == names.index(nm))[:, ::-1, :]
    cav = ndimage.binary_fill_holes(full) & ~full
    clab, cn = ndimage.label(cav)
    for i in range(1, cn + 1):
        if (clab == i).sum() <= 50: claim('raft-wood', clab == i, C['oak_d'])
    anc['hull'] = {'hawse-S': [ax_ - ar_ - 1, YC + 1, ZW]}           # 錨鏈孔在錨井後側、近水線（Ericsson）；只有一隻錨 ⇒ 只登記 S（錨偏右舷 1 格讓遊戲認成右錨）
    info = dict(hold=hold, deck=deck, rt=rt, spots=spots)
    return own, col, names, anc, info


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    own, col, names, anc, info = build()
    counts = {}
    for i, nm in enumerate(names):
        if not nm: continue
        idx = np.argwhere(own == i)
        cs = col[own == i]
        order = np.lexsort((idx[:, 2], idx[:, 1], idx[:, 0]))
        idx, cs = idx[order], cs[order]
        with open(os.path.join(out, 'part_%s.txt' % nm), 'w', newline='\n') as f:
            f.write('# 莫尼特號 %s —— x,y,z,color（框 %d×%d×%d、關聯 at 0,0,0）\n' % (nm, NX, NY, NZ))
            f.write('\n'.join('%d,%d,%d,%d' % (a, b, c, k) for (a, b, c), k in zip(idx.tolist(), cs.tolist())))
            f.write('\n')
        counts[nm] = len(idx)
    sym = {}
    for i, nm in enumerate(names):
        if not nm: continue
        m = own == i
        sym[nm] = int((m != m[:, ::-1, :]).sum())
    # 組起來的樣子（煙囪、鍋爐另一舷鏡像）
    full = own > 0
    for nm in ('funnel', 'boilers'):
        full |= (own == names.index(nm))[:, ::-1, :]
    lab, n = ndimage.label(full)
    sizes = np.bincount(lab.ravel())[1:]
    cav = ndimage.binary_fill_holes(full) & ~full
    clab, cn = ndimage.label(cav)
    csz = sorted(np.bincount(clab.ravel())[1:].tolist())
    # 砲塔掃過的圓：甲板以上不能有別的實心
    sweep = (info['rt'] <= P['turret_r_out'] + 1.5) & (np.arange(NZ)[None, None, :] >= ZFL)
    # 排水（設計水線以下，每個 x、每一層最外兩格之間）
    vol = 0
    for zz in range(ZW + 1):
        lay = full[:, :, zz]
        anyy = lay.any(axis=1)
        lo = np.argmax(lay, axis=1); hi = NY - 1 - np.argmax(lay[:, ::-1], axis=1)
        vol += int(((hi - lo + 1) * anyy).sum())
    meta = dict(names=names[1:], counts=counts, total=int(full.sum()), mirror_diff=sym, components=int(n),
                small=sorted(sizes.tolist())[:-1][-10:] if n > 1 else [], cavities=cn, cavity_sizes=csz[-10:],
                turret_sweep_solid=int((sweep & full).sum()), disp_t=round(vol * 0.001 * 1.025, 1),
                anchors=anc, powder={'magazine': {'spots': info['spots']}},
                mags={k: {'link': v['link'], 'pos': v['pos']} for k, v in anc['mags'].items()},
                plan={'z_waterline': ZW, 'z_deck_walk': ZFL, 'z_berth_walk': ZBF},
                decks={'berth': {'kind': 'deck', 'deck': 'berth', 'level': 0, 'name': '住艙甲板', 'floor': '%d:%d,%d:%d' % (P['x_berth'][0], ZBF, P['x_berth'][1], ZBF), 'thick': 2},
                       'main': {'kind': 'deck', 'deck': 'main', 'level': 1, 'name': '主甲板（砲塔甲板）', 'floor': '%d:%d,%d:%d' % (XS, ZFL, XB, ZFL), 'thick': DL + 3}},
                engine_meta={'kind': 'engine', 'engine': 'direct', 'cylinders': 2, 'kn': 6, 'kn_max': 8, 'material': 'iron'})
    TM = PLAN['turret']
    meta['models'] = {
        'turret': {'at': [P['turret_x'] + 0.5, YC + 0.5, ZFL], 'rotate_z': 90,
                   'meta': {'kind': 'gun', 'gun': '11d', 'mount': 'turret', 'arc': '-174,174', 'rate': 16}},
        'screw': {'hub': [P['screw'][0] + 0.5, YC + 0.5, P['screw'][1] + 0.5],
                  'meta': {'kind': 'propeller', 'axis_x': 1, 'axis_y': 0, 'axis_z': 0, 'blades': 4, 'diameter_m': 2.74}},
        'wheel': {'at': [P['pilothouse'][0] + 0.5, YC + 0.5, ZFL], 'scale': 0.07},
        'anchor': {'at': [P['anchor_well'][0] + 0.5, YC + 1.5, ZDB - 0.5], 'scale': 0.2, 'rotate_z': 45},
    }
    json.dump(meta, open(os.path.join(out, 'monitor_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: meta[k] for k in ('counts', 'total', 'mirror_diff', 'components', 'small', 'cavities', 'cavity_sizes', 'turret_sweep_solid', 'disp_t')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
