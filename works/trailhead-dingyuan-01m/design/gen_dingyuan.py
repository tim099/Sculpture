# 定遠號（Ting-Yuen，1884；北洋艦隊旗艦）產生程式 —— 一次算出整艘的格子（0.1 m／格），照部件分開寫成 stampvox 清單＋固定點／meta 的 JSON。
# 用法：python -I -X utf8 -B gen_dingyuan.py <輸出資料夾>
# 座標：X 船長（船頭 +X）、Y 船寬（中線 y=110，+Y ＝ 右舷 S；鏡像 y ↔ 220−y）、Z 高度（z=0 ＝ 龍骨底）。每個部件都用整船的框、關聯 at 0,0,0。
# 數字讀 plan.json 的 params；每個數字的出處在 plan.json 的 provenance（原圖讀數／參考資料／設計決定）。
# 結構：船殼（外板 2 格、衝角、圓船尾、船尾 deadwood）＋城堡裝甲帶＋兩座露砲台（梯次配置、凸台）＋三層甲板（下甲板／舯部主甲板／艉樓艏樓）＋飛橋甲板
#       ＋兩根煙囪、八座鍋爐、兩具臥式主機、兩支軸、兩個螺旋槳、一片舵＋兩根戰鬥桅＋司令塔、海圖室、通風筒、艇架＋彈藥庫三間、梯子。
# 會轉的（砲塔層、砲）與外部模型（螺旋槳、舵、小艇、錨…）在 gen_parts.py 與 apply_*.py。
import sys, os, json, math
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P = PLAN['params']
NX, NY, NZ = P['frame']
YC = (NY - 1) // 2
ZW = P['z_waterline']
ZLD, ZMD, ZUD, ZHD = P['z_lower_deck'], P['z_main_deck'], P['z_upper_deck'], P['z_hurricane']   # 各層甲板最上一層（走路格 ＋1）
MIRR = ('boilers-aft', 'boilers-fwd', 'engine', 'shaft')                # 右舷做、左舷 mirror=y 關聯的部件
ZTOP = ZUD + 1                                   # 船殼（舷牆）頂 ＝ 艉樓、艏樓走路格那一層
XS, XSW, XST = P['x_stern_deck'], P['x_stern_wl'], P['x_stem']
XR, ZR = P['ram_tip']
B = P['half_beam']
C = P['colors']
XPE, XFC = P['x_poop_end'], P['x_fc_start']
CIT = P['citadel']


def g(x0, x1, y0, y1, z0, z1):
    """局部的開放格點（半開區間），broadcast 用，不配整個框。"""
    return (np.arange(x0, x1, dtype=np.float32)[:, None, None], np.arange(y0, y1, dtype=np.float32)[None, :, None],
            np.arange(z0, z1, dtype=np.float32)[None, None, :])


def seg(p0, p1, r):
    """線段 p0→p1、半徑 r 的圓管：回傳（局部原點, 遮罩）—— 只配線段的外框。格心離線段 ≤ r 就算。"""
    p0 = np.asarray(p0, np.float32); p1 = np.asarray(p1, np.float32)
    lo = np.floor(np.minimum(p0, p1) - r - 1).astype(int); hi = np.ceil(np.maximum(p0, p1) + r + 1).astype(int)
    lo = np.maximum(lo, 0)
    X, Y, Z = g(lo[0], hi[0] + 1, lo[1], hi[1] + 1, lo[2], hi[2] + 1)
    d = p1 - p0; L2 = max(float(d @ d), 1e-6)
    t = np.clip(((X + 0.5 - p0[0]) * d[0] + (Y + 0.5 - p0[1]) * d[1] + (Z + 0.5 - p0[2]) * d[2]) / L2, 0, 1)
    dist = np.sqrt((X + 0.5 - p0[0] - t * d[0]) ** 2 + (Y + 0.5 - p0[1] - t * d[1]) ** 2 + (Z + 0.5 - p0[2] - t * d[2]) ** 2)
    return (int(lo[0]), int(lo[1]), int(lo[2])), dist <= r


# ───────────────────────── 線形 ─────────────────────────
def x_end(z):
    """船頭外形（側視）：z 這一層船殼最前面到哪。艏柱垂直 → 水線下 2.2 m 往前彎到衝角尖 → 衝角下緣是往後下降的直線。"""
    z = np.asarray(z, np.float32)
    zk = P['z_stem_knuckle']
    s = np.clip((zk - z) / (zk - ZR), 0, 1)
    ram = XST + (XR - XST) * np.sqrt(1 - (1 - s) ** 2)
    ff = P['forefoot_x0'] + (XR - P['forefoot_x0']) * np.clip(z / ZR, 0, 1)
    return np.where(z >= zk, XST, np.where(z >= ZR, ram, ff)).astype(np.float32)


def x_start(z):
    """船尾外形（側視）：甲板 x 6、水線 x 11（幾乎沒有懸出），水線下慢慢往前。"""
    z = np.asarray(z, np.float32)
    up = XS + (XSW - XS) * ((ZTOP - z) / (ZTOP - ZW)) ** 2
    dn = XSW + (ZW - z) * 0.6
    return np.where(z >= ZW, up, dn).astype(np.float32)


def z_bottom(x):
    """船底：中段平在 z 0；船尾往上收（雙螺旋槳在船尾突出部下面）。"""
    rx, rz = P['run']
    x = np.asarray(x, np.float32)
    return np.where(x < rx, rz * (rx - x) / (rx - XS), 0).astype(np.float32)


def half_width(X, Z):
    """船殼在 (x, z) 的半寬（< 0 ＝ 不在船殼裡）。平面：中段全寬、船尾橢圓、船頭收尖（終點照那一層的側視外形）；剖面：舭部照 p 次方收。"""
    xa, xf = P['x_aft_full'], P['x_fwd_full']
    a1, b1 = P['stern_pow']; a2, b2 = P['bow_pow']
    xs, xe = x_start(Z), x_end(Z)
    xp = np.minimum(xe, XST)                                              # 船身照艏柱收尖（衝角另外是一塊尖楔，下面）
    hp = np.full(np.broadcast(X, Z).shape, B, np.float32)
    ta = np.clip((xa - X) / np.maximum(xa - xs, 1), 0, 1)
    tf = np.clip((X - xf) / np.maximum(xp - xf, 1), 0, 1)
    hp = np.where(X < xa, B * (1 - ta ** a1) ** b1, hp)
    hp = np.where(X > xf, np.where(X <= xp, B * (1 - tf ** a2) ** b2, 0), hp)
    full = np.where(X < xa, 1 - ta, np.where(X > xf, 1 - tf, 1.0))
    p0, p1 = P['bilge_p']
    p = p0 + (p1 - p0) * full
    zb = z_bottom(X)
    zt = zb + P['bilge_h']
    s = np.clip((zt - Z) / P['bilge_h'], 0, 1)
    f = np.where(Z < zt, (1 - np.minimum(s, 0.9999) ** p) ** (1 / p), 1.0)
    hw = hp * f
    rk, rl = P['ram_wedge']                                               # 衝角：從艏柱往前的尖楔，半寬 ＝ rk ×（到尖端的距離），最寬 rl
    hw = np.maximum(hw, np.where((X <= xe) & (xe > XST) & (X > XST - 30), np.minimum(rk * (xe - X), rl), -1))
    out = (X < xs) | (X > xe) | (Z < zb) | (Z > ZTOP)
    return np.where(out, -1, hw).astype(np.float32)


def build():
    own = np.zeros((NX, NY, NZ), np.uint8)
    col = np.zeros((NX, NY, NZ), np.uint8)
    names = [None]
    stat = {}
    res = np.zeros((NX, NY, NZ), bool)                                    # 右舷做、左舷鏡像的部件：對面那一份先佔（別的部件不准落）

    def claim(name, o, mask, color):
        """mask：局部陣列，原點 o=(x0,y0,z0)；只落沒人佔的格（先到先贏）。鏡像部件同時把 y 鏡過去的那一份保留起來。"""
        x0, y0, z0 = o
        sx, sy, sz = mask.shape
        R = own[x0:x0 + sx, y0:y0 + sy, z0:z0 + sz]
        Cc = col[x0:x0 + sx, y0:y0 + sy, z0:z0 + sz]
        m = mask & (R == 0) & ~res[x0:x0 + sx, y0:y0 + sy, z0:z0 + sz]
        if name not in names: names.append(name)
        i = names.index(name)
        R[m] = i
        Cc[m] = color if np.isscalar(color) else np.broadcast_to(color, m.shape)[m]
        stat[name] = stat.get(name, 0) + int(m.sum())
        if name in MIRR:
            ym = 2 * YC - (y0 + sy - 1)
            res[x0:x0 + sx, ym:ym + sy, z0:z0 + sz] |= m[:, ::-1, :]
        return m

    def claimw(name, mask, color):                                       # 整個框的遮罩
        return claim(name, (0, 0, 0), mask, color)

    anc, info = {}, {}
    ZH = ZTOP + 6                                                         # 船殼的計算高度（頂上多幾層 ⇒ 頂面不算外板）
    # ── 船殼外形 ──
    xx = np.arange(NX, dtype=np.float32)[:, None]; zz = np.arange(ZH, dtype=np.float32)[None, :]
    hw = half_width(xx, np.minimum(zz, ZTOP))
    hw[:, ZTOP + 1:] = hw[:, ZTOP:ZTOP + 1]
    Y = np.arange(NY, dtype=np.float32)[None, :, None]
    DY = np.abs(Y - YC)
    env = DY <= hw[:, None, :]                                            # (NX, NY, ZH)
    # 露砲台凸台（半徑 47 的圓，往下收到 z 72）
    rs, zs = P['sponson']
    X3, _, Z3 = g(0, NX, 0, 1, 0, ZH)
    Z3b = np.broadcast_to(Z3, (1, 1, ZH))
    for bb in P['barbettes']:
        bx, by = bb['x'], YC + bb['dy']
        r = np.hypot(np.arange(NX, dtype=np.float32)[:, None, None] - bx, Y - by)
        rz = np.where(Z3b >= ZMD + 1, rs, rs - (ZMD + 1 - Z3b) * (rs - (B - abs(bb['dy']) - 1)) / (ZMD + 1 - zs))
        env |= (r <= rz) & (Z3b >= zs)
    env_full = env.copy()
    env = env[:, :, :ZTOP + 1].copy()
    waist = (np.arange(NX) > XPE) & (np.arange(NX) < XFC)
    env[waist, :, P['z_waist_top'] + 1:] = False                           # 舯部舷牆頂比艉樓、艏樓低（主砲管從上面過）；侵蝕照沒切的算 ⇒ 頂面不會長出一層蓋子
    cm = P['casemates37']; pw_, pz0, pz1 = cm['port']                       # 舷牆上 37 mm 砲的砲眼（舷外那一半挖穿）
    for cxx in cm['x']:
        env[cxx - pw_:cxx + pw_ + 1, :, pz0:pz1 + 1] &= (np.abs(np.arange(NY) - YC) < cm['dy'])[:, None]
    inner2 = ndimage.binary_erosion(env_full, iterations=P['t_shell'])[:, :, :ZTOP + 1]
    inner4 = ndimage.binary_erosion(env_full, iterations=P['belt'][2])[:, :, :ZTOP + 1]
    inner1 = ndimage.binary_erosion(env_full, iterations=1)[:, :, :ZTOP + 1]
    del env_full
    shell = env & ~inner2
    info['env'] = env; info['inner'] = inner2; info['hw'] = hw
    Zs = np.arange(ZTOP + 1)[None, None, :]
    Xs = np.arange(NX)[:, None, None]
    band = np.where(Zs < ZW, C['red'], np.where(Zs <= P['band_black_top'], C['black'], C['white'])).astype(np.uint8)
    # 舷窗（黃銅圈）：下排全船、上排艉樓與艏樓；只換最外那一層的色
    sc = P['scuttles']
    port = np.zeros((NX, 1, ZTOP + 1), bool)
    for x0 in range(30, 900, sc['pitch']):
        port[x0:x0 + 2, 0, sc['low_z']:sc['low_z'] + 2] = True
        if x0 < XPE - 10 or x0 > XFC + 10:
            port[x0:x0 + 2, 0, sc['up_z']:sc['up_z'] + 2] = True
    outer = env & ~inner1
    shell_col = np.where(outer, np.where(port & (Zs > 62), C['brass'], band), np.where(Zs > ZLD, C['wall'], C['iron'])).astype(np.uint8)
    # ── 舵（獨立子作品，先佔 ⇒ 船殼在舵柱那裡留孔）──
    R_ = P['rudder']
    rx0, rx1 = R_['x']; rz0, rz1 = R_['z']; px0, px1 = R_['post']
    Xg, Yg, Zg = g(0, 60, YC - 3, YC + 4, 0, 80)
    rud = (Xg >= rx0) & (Xg <= rx1) & (np.abs(Yg - YC) <= 1) & (Zg >= rz0) & (Zg <= rz1) & ~((Xg < rx0 + 4) & (Zg < rz0 + 4))   # 舵葉（後下角削掉）
    stock_top = 70
    rud |= (np.hypot(Xg - (rx1 - 0.5), Yg - YC) <= 1.6) & (Zg >= rz1) & (Zg <= stock_top)                                        # 舵桿，往上穿進船尾
    rud |= (Xg >= rx0 + 6) & (Xg <= rx1 - 2) & (np.abs(Yg - YC) <= 2) & ((Zg.astype(int) - rz0) % 12 == 6) & (Zg <= rz1 - 4)    # 舵葉的橫筋（看得出兩面）
    claim('rudder', (0, YC - 3, 0), rud, C['iron'])
    anc['rudder'] = {'stock-top': [rx1, YC, stock_top]}
    info['rudder_hinge'] = [rx1 + 0.5, YC + 0.5, rz0]
    # ── 螺旋槳（兩個；右舷 S 右旋、左舷 P 照 y 鏡像 ⇒ 左旋）──
    S_ = P['screw']
    sxh, sdy, szh, sr = S_['x'], S_['dy'], S_['z'], S_['r']
    Xg, Yg, Zg = g(sxh - 6, sxh + 7, YC + sdy - sr - 2, YC + sdy + sr + 3, max(0, szh - sr - 2), szh + sr + 3)
    yy_, zz_ = Yg - (YC + sdy), Zg - szh
    ang = np.arctan2(zz_, yy_); rr = np.hypot(yy_, zz_)
    nb = S_['blades']
    da = (ang - math.pi / nb) % (2 * math.pi / nb); da = np.minimum(da, 2 * math.pi / nb - da)
    arcl = da * rr
    halfw = 1.0 + 4.5 * np.clip(np.sin(math.pi * np.clip(rr / sr, 0, 1)), 0, 1) ** 0.7
    sgn = np.sign(((ang - math.pi / nb) % (2 * math.pi / nb)) - math.pi / nb)
    blade = (rr <= sr) & (rr > 2.5) & (arcl <= halfw) & (np.abs(Xg - sxh - sgn * arcl * 0.45) <= 1)
    hub = ((np.abs(Xg - sxh) <= 2.5) & (rr <= 3.2)) | ((Xg > sxh + 2) & (Xg <= sxh + 5) & (rr <= 2.4)) | ((Xg < sxh - 2) & (Xg >= sxh - 4) & (rr <= 3.2 - (sxh - 2 - Xg)))
    scr = hub | blade
    claim('screw-s', (sxh - 6, YC + sdy - sr - 2, max(0, szh - sr - 2)), scr, C['bronze'])
    claim('screw-p', (sxh - 6, YC - sdy - sr - 2, max(0, szh - sr - 2)), scr[:, ::-1, :], C['bronze'])
    anc['screw-s'] = {'hub': [sxh, YC + sdy, szh], 'shaft-fwd': [sxh + 5, YC + sdy, szh]}
    anc['screw-p'] = {'hub': [sxh, YC - sdy, szh], 'shaft-fwd': [sxh + 5, YC - sdy, szh]}
    # ── 裝甲帶（城堡兩舷，外 4 格；水線下紅、上黑；裡面兩層鐵灰）──
    z0b, z1b, _ = P['belt']
    beltm = env & ~inner4 & (Xs >= CIT[0]) & (Xs <= CIT[1]) & (Zs >= z0b) & (Zs <= z1b)
    claimw('belt', np.pad(beltm, ((0, 0), (0, 0), (0, NZ - ZTOP - 1))), np.pad(np.where(outer, band, C['iron']).astype(np.uint8), ((0, 0), (0, 0), (0, NZ - ZTOP - 1))))
    # ── 船殼外板 ──
    # 外板 2 格（材質照關聯「船殼」的 meta：iron_hull ＝ 鐵外板＋肋骨內襯的混合層，比重、硬度取鐵與橡木的中間 —— 全鐵 ⇒ 遊戲照材質算 9,215 t，Tim 2026-10-21）
    claimw('hull', np.pad(shell, ((0, 0), (0, 0), (0, NZ - ZTOP - 1))), np.pad(shell_col, ((0, 0), (0, 0), (0, NZ - ZTOP - 1))))
    # deadwood（船尾中線的鰭，撐舵柱）＋舵柱＋舵底的龍骨靴＋軸架（A 字）
    sk0, sk1 = P['skeg']
    Xg, Yg, Zg = g(0, sk1 + 1, YC - 3, YC + 4, 0, 72)
    zb_ = z_bottom(Xg)
    skeg = (Xg >= sk0) & (np.abs(Yg - YC) <= 2) & (Zg <= zb_ + 3)
    skeg |= (Xg >= px0) & (Xg <= px1) & (np.abs(Yg - YC) <= 2) & (Zg <= zb_ + 3)
    skeg |= (Xg >= rx0 - 2) & (Xg <= px1) & (np.abs(Yg - YC) <= 1) & (Zg <= rz0 - 2)
    claim('hull', (0, YC - 3, 0), skeg, np.where(Zg < ZW, C['red'], C['black']))
    info['skeg'] = (Xg, Yg, Zg, skeg)
    # ── 甲板 ──
    hat = np.zeros((NX, NY, NZ), bool)                                    # 艙口（梯子穿過的洞；甲板不落）
    holes = np.zeros((NX, NY, NZ), bool)                                  # 煙囪、桅、露砲台中間…（不落甲板）
    # 梯子（先算位置 ⇒ 艙口）
    ladders = []
    lad_mask = np.zeros((NX, NY, NZ), bool)

    def ladder(nm, x_top, y, z_lo, z_hi, dirx, run_k=0.55, hatch_decks=(), width=2):
        """梯子：最高一階在 x_top、往 dirx 爬（爬的人往 dirx 走）；z_lo ＝ 下層走路格、z_hi ＝ 上層走路格。回傳四點。"""
        H = z_hi - z_lo; run = int(round(H * run_k))
        xb = x_top - dirx * run                                            # 最低一階的 x
        steps = []
        for k in range(1, H // 3 + 1):
            zz_ = z_lo + 3 * k - 1
            if zz_ >= z_hi - 1: break
            x_ = int(round(xb + dirx * run * (zz_ - z_lo) / H))
            steps.append((x_, zz_))
            lad_mask[min(x_, x_ + dirx):max(x_, x_ + dirx) + 1, y - width:y + width + 1, zz_] = True
        xprev = None
        for zz_ in range(z_lo, z_hi - 1):                                  # 兩根側板（x 換格的那一層兩格都放 ⇒ 六連通不斷）
            x_ = int(round(xb + dirx * run * (zz_ - z_lo) / H))
            for xq in {x_, xprev if xprev is not None else x_}:
                lad_mask[xq, y - width - 1, zz_] = True; lad_mask[xq, y + width + 1, zz_] = True
            xprev = x_
        for zd in hatch_decks:                                             # 甲板上的艙口：梯子穿過那一層的位置 ± 幾格
            xm = xb + dirx * run * (zd - z_lo) / H
            hat[int(math.floor(xm - 5)):int(math.ceil(xm + 5)) + 1, y - width - 1:y + width + 2, zd - 5:zd + 1] = True
        lo, hi = steps[0], steps[-1]
        d = {'name': nm, 'foot': [lo[0] - dirx * 3, y, z_lo], 'lo': [lo[0], y, lo[1] + 1], 'hi': [hi[0], y, hi[1] + 1], 'head': [hi[0] + dirx * 4, y, z_hi]}
        ladders.append(d)
        return d

    WL1, WM1, WU1, WH1 = ZLD + 1, ZMD + 1, ZUD + 1, ZHD + 1               # 各層走路格
    tm = P['turret_main']
    for bb in P['barbettes']:
        cx, cy = bb['x'], YC + bb['dy']
        # 露砲台裡的梯子：下甲板 → 固定平台（轉盤中間的洞），往 +x 爬
        ladder('barbette-' + bb['name'], cx - 4, cy, WL1, tm['z_table'], 1, run_k=0.3, hatch_decks=(ZMD,))   # 梯頭 ＝ 轉軸那一格：兩門砲中間的走道（遊戲的取用點要在砲的外框外）
    for t in P['turrets_15']:
        cx = t['x']; back = -t['front']                                    # 梯子在砲尾那一側
        ladder('turret15-' + t['name'], cx + back * 6, YC + 10, WM1, WU1, back, run_k=0.45, hatch_decks=(ZUD,))   # 梯頭在砲尾旁（偏中線 1 m、離轉軸 1.4 m）：砲的外框外、掃過那一圈的牆裡
    LAD = [  # 名字, 最高一階 x, y, 下層, 上層, 往哪爬, 穿過哪幾層的艙口
        ('waist-a', 312, YC, WL1, WM1, 1, (ZMD,)),
        ('waist-b', 630, YC - 2, WL1, WM1, 1, (ZMD,)),
        ('poop-lower', 160, YC, WL1, WM1, -1, (ZMD,)),
        ('fc-lower', 790, YC, WL1, WM1, 1, (ZMD,)),
        ('poop-break-P', 244, YC - 60, WM1, WU1, -1, ()),
        ('poop-break-S', 244, YC + 60, WM1, WU1, -1, ()),
        ('fc-break-a', 686, YC - 40, WM1, WU1, 1, ()),
        ('fc-break-b', 686, YC - 15, WM1, WU1, 1, ()),
        ('hurricane', 506, YC + 38, WM1, WH1, 1, (ZHD,)),
        ('engine', 352, YC, 5, WL1, 1, (ZLD,)),
        ('stokehold', 398, YC, 5, WL1, 1, (ZLD,)),
    ]
    for nm, xt, y, zl, zh, dx, hd in LAD:
        ladder(nm, xt, y, zl, zh, dx, hatch_decks=hd)
    # 煙囪（中線、橢圓；甲板以下的直煙道也在煙囪部件裡，下到煙箱頂）
    fa, fb = P['funnel_half']
    ftop = P['funnel_top']
    z_smoke_top = 58
    for f in P['funnels']:
        fx = f['x']
        Xg, Yg, Zg = g(fx - fa - 1, fx + fa + 2, YC - fb - 1, YC + fb + 2, z_smoke_top - 6, ftop + 1)
        e_o = ((Xg - fx) / fa) ** 2 + ((Yg - YC) / fb) ** 2
        e_i = ((Xg - fx) / (fa - 2)) ** 2 + ((Yg - YC) / (fb - 2)) ** 2
        tube = (e_o <= 1) & (e_i > 1) & (Zg >= z_smoke_top - 6) & (Zg <= ftop)
        rim = (e_o <= 1.12) & (e_i > 1) & (Zg >= ftop - 1)
        cl = (np.abs(Yg - YC) < 0.5) & (Zg >= 52) & (Zg <= z_smoke_top) & (e_o <= 1)   # 煙箱中線那一欄（鍋爐部件兩舷鏡像，中線歸煙囪）
        fc = np.where(Zg > ftop - P['funnel_band'], C['black'], C['buff'])
        claim('funnel-' + f['name'], (fx - fa - 1, YC - fb - 1, z_smoke_top - 6), tube | rim, fc)
        holes[fx - fa - 1:fx + fa + 2, YC - fb - 1:YC + fb + 2, z_smoke_top - 6:ftop + 1] |= (e_o <= 1.05) & (Zg >= z_smoke_top - 6)
        anc['funnel-' + f['name']] = {'smoke': [fx, YC, ftop - 1]}
    # 鍋爐（每間兩座，兩舷各一，爐門朝中線；右舷做、左舷鏡像）＋煙箱（爐前頂上，接煙囪）
    BR = P['boiler_rooms']; BO = P['boiler']
    for gi, f in enumerate(P['funnels']):
        nm = 'boilers-' + f['name']
        a_ = {}
        for k, ri in enumerate(f['boilers']):
            bx = (BR[ri] + BR[ri + 1]) // 2
            y0, y1 = YC + BO['y_front'], YC + BO['y_front'] + BO['len']
            Xg, Yg, Zg = g(bx - 25, bx + 26, y0, y1 + 1, 2, 60)
            rr = np.hypot(Xg - bx, Zg - BO['zc'])
            cyl = (rr <= BO['r']) & (Yg >= y0) & (Yg <= y1)
            front = cyl & (Yg <= y0 + 1)
            furn = np.zeros(cyl.shape, bool)
            for fdx, fz in ((-12, BO['zc'] - 9), (0, BO['zc'] - 13), (12, BO['zc'] - 9)):
                furn |= front & (np.hypot(Xg - (bx + fdx), Zg - fz) <= 4)
            saddle = (np.abs(Xg - bx) <= 16) & (Zg <= 7) & (Yg >= y0 + 3) & (Yg <= y1 - 3) & ((Yg.astype(int) - y0) % 9 < 2)
            claim(nm, (bx - 25, y0, 2), furn, C['black'])
            claim(nm, (bx - 25, y0, 2), cyl | saddle, C['iron'])
            a_['boiler-%d' % (k + 1)] = [bx, (y0 + y1) // 2, BO['zc']]
            a_['stoke-%d' % (k + 1)] = [bx, YC + 4, 5]
            # 煙箱：爐前頂上（y 中線＋1 … y0+8）、從鍋爐那一欄往煙囪那一欄
            xa_, xb_ = min(bx, f['x']) - 14, max(bx, f['x']) + 14
            hm = (holes | lad_mask)[xa_:xb_ + 1, YC + 1:y0 + 9, 52:z_smoke_top + 1]
            claim(nm, (xa_, YC + 1, 52), ~hm, C['iron'])
            cm = ~(holes | lad_mask)[xa_:xb_ + 1, YC:YC + 1, 52:z_smoke_top + 1]          # 中線那一欄（兩舷鏡像都不含 ⇒ 歸煙囪）
            claim('funnel-' + f['name'], (xa_, YC, 52), cm, C['iron'])
        a_['uptake'] = [f['x'], YC, 52]
        anc[nm] = a_
    # 主機（兩具臥式三缸；右舷做、左舷鏡像）：曲軸沿 x（軸心 dy_crank、z）、汽缸沿 +y 躺著、連桿、底座、凝汽器
    E = P['engine']
    ey, ez = YC + E['dy_crank'], E['z']
    ex0, ex1 = min(E['x']) - 14, max(E['x']) + 14
    Xg, Yg, Zg = g(ex0 - 2, ex1 + 3, YC + 14, YC + 90, 2, 46)
    eng = (np.hypot(Yg - ey, Zg - ez) <= 3) & (Xg >= ex0 - 2) & (Xg <= ex1 + 2)                                  # 曲軸
    bed = (Xg >= ex0) & (Xg <= ex1) & (Yg >= ey - 10) & (Yg <= ey + E['cyl_len'] + 18) & (Zg <= 7) & (Zg >= 3)     # 底座
    cylm = np.zeros(eng.shape, bool); cover = np.zeros(eng.shape, bool); rod = np.zeros(eng.shape, bool); band_ = np.zeros(eng.shape, bool)
    c0 = ey + 14
    for cxx in E['x']:
        rr = np.hypot(Xg - cxx, Zg - ez)
        cylm |= (rr <= E['r_cyl']) & (Yg >= c0) & (Yg <= c0 + E['cyl_len'])
        cover |= (rr <= E['r_cyl'] + 1.2) & ((np.abs(Yg - c0) <= 0.5) | (np.abs(Yg - (c0 + E['cyl_len'])) <= 0.5))
        band_ |= (rr <= E['r_cyl'] + 0.6) & (np.abs(Yg - (c0 + E['cyl_len'] // 2)) <= 0.5)
        rod |= (np.hypot(Xg - cxx, Zg - ez) <= 1.5) & (Yg >= ey) & (Yg < c0)                                        # 活塞桿／連桿（trunk）
        rod |= (np.abs(Xg - cxx) <= 2) & (np.abs(Yg - ey) <= 4) & (np.abs(Zg - ez) <= 6)                            # 曲柄臂
        cylm |= (np.abs(Xg - cxx) <= 3) & (Zg >= 7) & (Zg <= ez - E['r_cyl']) & (Yg >= c0 + 4) & (Yg <= c0 + E['cyl_len'] - 4)   # 汽缸座
    cond = (Xg >= ex0 + 4) & (Xg <= ex1 - 4) & (np.hypot(Yg - (ey + E['cyl_len'] + 26), Zg - 18) <= 7)            # 凝汽器（沿 x 的圓筒）
    off = (ex0 - 2, YC + 14, 2)
    inside = info['inner'][ex0 - 2:ex1 + 3, YC + 14:YC + 90, 2:46]
    claim('engine', off, (cover | band_) & inside, C['brass'])
    claim('engine', off, (eng | bed | cylm | rod | cond) & inside, C['iron'])
    anc['engine'] = {'core': [E['x'][1], ey + 24, ez], 'cyl-1': [E['x'][0], c0 + 10, ez], 'cyl-2': [E['x'][1], c0 + 10, ez], 'cyl-3': [E['x'][2], c0 + 10, ez],
                     'tend-1': [E['x'][1], ey - 6, 8], 'tend-2': [E['x'][1], ey + 56, 8]}
    # 軸（右舷；左舷鏡像）：主機曲軸後端 → 螺旋槳轂前（略往外斜）；兩端固定點在軸心那一格
    fa_ = (ex0 - 2 + 0.5, ey + 0.5, ez + 0.5); fb_ = (sxh + 5 + 0.5, YC + sdy + 0.5, szh + 0.5)
    o, m_ = seg(fb_, fa_, P['shaft_r'])
    claim('shaft', o, m_, C['iron'])
    anc['shaft'] = {'aft': [sxh + 5, YC + sdy, szh], 'fwd': [ex0 - 2, ey, ez]}
    # 軸架（A 字：螺旋槳前，兩根撐到船殼；在船殼裡面那一段不落）
    ax_ = sxh + 9
    for (ty, tz) in ((YC + 12, szh + 24), (YC + sdy - 14, szh + 28)):
        o, m_ = seg((ax_ + 0.5, YC + sdy + 0.5, szh + 0.5), (ax_ + 0.5, ty + 0.5, tz + 0.5), 1.4)
        sx_, sy_, sz_ = m_.shape
        m_ = m_ & ~info['inner'][o[0]:o[0] + sx_, o[1]:o[1] + sy_, o[2]:o[2] + sz_]
        claim('hull', o, m_, C['red'])
        claim('hull', (o[0], 2 * YC - (o[1] + sy_ - 1), o[2]), m_[:, ::-1, :], C['red'])
    # ── 露砲台（固定的裝甲圈＋中間的固定平台＋撐柱）──
    r0, r1 = P['barbette_r']; bz0, bz1 = P['barbette_z']
    for bb in P['barbettes']:
        cx, cy = bb['x'], YC + bb['dy']
        Xg, Yg, Zg = g(cx - r1 - 1, cx + r1 + 2, cy - r1 - 1, cy + r1 + 2, bz0, tm['z_table'])
        rr = np.hypot(Xg - cx, Yg - cy)
        ring = (rr > r0 - 0.5) & (rr <= r1 + 0.5) & (Zg <= bz1)
        plat = (rr <= tm['r_hole'] + 0.5) & (Zg == bz1) & (Xg >= cx - 4)
        post = (np.hypot(Xg - (cx + 4), Yg - cy) <= 2) & (Zg < bz1)
        o = (cx - r1 - 1, cy - r1 - 1, bz0)
        claim('barbettes', o, ring, C['black'])
        claim('barbette-platforms', o, plat | post, C['iron'])
        anc.setdefault('barbettes', {})['pivot-' + bb['name']] = [cx, cy, tm['z_table']]
    # 司令塔（8 in，圓、黑；頂下一圈觀察縫、後面一扇門）
    cn = P['conning']; ccx = cn['x']; cri, cro = cn['r']; ch = cn['h']
    Xg, Yg, Zg = g(ccx - cro - 1, ccx + cro + 2, YC - cro - 1, YC + cro + 2, WU1, WU1 + ch + 3)
    rr = np.hypot(Xg - ccx, Yg - YC)
    wall = (rr > cri - 0.5) & (rr <= cro + 0.5) & (Zg < WU1 + ch)
    slit = (Zg >= WU1 + ch - 5) & (Zg <= WU1 + ch - 4) & (np.abs(np.arctan2(Yg - YC, Xg - ccx)) < 2.2)
    door = (Xg < ccx) & (np.abs(Yg - YC) <= 3) & (Zg < WU1 + 19)
    roof = (rr <= cro + 0.5) & (Zg >= WU1 + ch) & (Zg <= WU1 + ch + 1)
    cap = (rr <= 3.5) & (Zg == WU1 + ch + 2)
    claim('conning', (ccx - cro - 1, YC - cro - 1, WU1), (wall & ~slit & ~door) | roof | cap, C['black'])
    # 桅（戰鬥桅：空心鋼管、桅樓（圓台＋護牆）、頂桿、信號桁；主桅加兩根吊艇桿與斜桁）
    MST = {}
    for m in P['masts']:
        mx, mr = m['x'], m['r']
        nm = 'mast-' + m['name']
        top = m['top_z']
        Xg, Yg, Zg = g(mx - 120, mx + 121, YC - 60, YC + 61, m['z0'], m['pole_top'] + 2)
        rr = np.hypot(Xg - mx, Yg - YC)
        tube = (rr <= mr + 0.5) & (Zg < top)                                                             # 下桅（實心：空心管會封成空腔）
        pl =(rr <= m['top_r'] + 0.5) & (Zg == top)
        wallm = (rr > m['top_r'] - 1.0) & (rr <= m['top_r'] + 0.5) & (Zg > top) & (Zg <= top + 10)
        wallm &= ~((np.abs(Yg - YC) <= 3) & (Xg < mx) & (Zg > top) & (Zg <= top + 9))                    # 後面一個開口（登頂的口）
        wallm &= ~((np.abs(Xg - mx) <= 3) & (Zg > top) & (Zg <= top + 9))                                 # 兩舷各一個開口（繩梯上來的口；2026-10-21）
        pole = (rr <= m['pole_r'] + 0.5) & (Zg > top) & (Zg <= m['pole_top'])
        truck = (rr <= m['pole_r'] + 1.5) & (Zg >= m['pole_top'] - 1) & (Zg <= m['pole_top'])
        parts_ = tube | pl | pole                                                                          # 信號桁是帆桁模型（gen_parts signal_yard；遊戲照帆桁 meta 認桅）

        if m.get('platform2'):
            z2 = m['platform2']
            parts_ |= (rr <= 12.5) & (Zg == z2)
            wallm |= (rr > 11.5) & (rr <= 12.5) & (Zg > z2) & (Zg <= z2 + 8) & ~((np.abs(Yg - YC) <= 3) & (Xg < mx))
        own_c = np.where(wallm, C['white'], C['buff'])
        sub = parts_ | wallm
        claim(nm, (mx - 120, YC - 60, m['z0']), truck, C['white'])
        claim(nm, (mx - 120, YC - 60, m['z0']), sub, own_c)
        if m.get('gaff_z'):                                                # 主桅斜桁（往船尾、往上 25°；掛國旗）
            gz = m['gaff_z']; ca, sa = math.cos(math.radians(25)), math.sin(math.radians(25))
            g0 = mx - m['pole_r'] + 0.5                                        # 斜桁腳貼著頂桿
            peak = (g0 - 60 * ca, YC + 0.5, gz + 60 * sa + 0.5)
            o, m_ = seg((g0, YC + 0.5, gz + 0.5), peak, 1.1)
            claim(nm, o, m_, C['buff'])
            MST['gaff_peak'] = [peak[0] - 0.5, YC, peak[2] - 0.5]
            for sy in (1, -1):                                             # 吊艇桿：從桅腳往前、往外上（照片：主桅兩根長桿；吊魚雷艇）
                o, m_ = seg((mx + mr + 0.5, YC + 0.5, 160.5), (mx + 95.5, YC + sy * 40 + 0.5, 205.5), 1.4)
                claim(nm, o, m_, C['buff'])
        MST[m['name']] = {'top': top, 'pole_top': m['pole_top'], 'r': m['top_r'], 'x': mx, 'yard_z': m['yard_z'], 'yard_half': m['yard_half']}
    info['masts'] = MST
    # 通風筒（大的 cowl：管子從主甲板起、頂上一個朝前的喇叭口；外 buff、口裡紅）
    for vx, vdy in P['vents']:
        vy = YC + vdy
        Xg, Yg, Zg = g(vx - 10, vx + 11, vy - 8, vy + 9, WM1, WM1 + 64)
        rr = np.hypot(Xg - vx, Yg - vy)
        pipe = (rr <= 4.5) & (rr > 2.5) & (Zg < WM1 + 50)
        hz = WM1 + 54
        rh = np.sqrt((Xg - vx - 2) ** 2 + (Yg - vy) ** 2 + ((Zg - hz) * 1.2) ** 2)
        head = (rh <= 7.5) & (rh > 5.5) & ~((Xg > vx + 3) & (np.hypot(Yg - vy, Zg - hz) <= 5.5)) & (Zg >= WM1 + 47)
        mouth = (rh <= 5.5) & (Xg > vx + 3) & (np.hypot(Yg - vy, Zg - hz) <= 5.5) & (Xg <= vx + 5)
        claim('vents', (vx - 10, vy - 8, WM1), mouth, C['red'])
        claim('vents', (vx - 10, vy - 8, WM1), pipe | head, C['buff'])
        holes[vx - 5:vx + 6, vy - 5:vy + 6, ZMD - 5:ZMD + 1] |= (np.hypot(np.arange(vx - 5, vx + 6)[:, None] - vx, np.arange(vy - 5, vy + 6)[None, :] - vy) <= 2.5)[:, :, None]
    # 鋼索要的固定點（桅頂、舷牆頂）稍後在 meta 裡
    # ── 甲板 ──
    inner = info['inner']
    lad_hat = hat
    def deck_layers(nm, ztop, x0, x1, top_c, under_c, beam_depth=3, pitch=12, extra_holes=None, plate_layers=2, pl_name=None, pl_x=None):
        Xg = np.arange(NX)[:, None, None]; Zg = np.arange(NZ)[None, None, :]
        xr = (Xg >= x0) & (Xg <= x1)
        inn = np.zeros((NX, NY, NZ), bool); inn[:, :, :ZTOP + 1] = inner
        bad = lad_hat | holes | lad_mask
        if extra_holes is not None: bad = bad | extra_holes
        top = inn & xr & (Zg == ztop) & ~bad
        if pl_name:
            pxr = (Xg >= pl_x[0]) & (Xg <= pl_x[1])
            claimw(pl_name, top & pxr, C['iron'])
        claimw(nm, top, top_c)
        if plate_layers > 1: claimw(nm, inn & xr & (Zg < ztop) & (Zg >= ztop - plate_layers + 1) & ~bad, under_c)
        beams = inn & xr & (Zg < ztop - plate_layers + 1) & (Zg >= ztop - plate_layers + 1 - beam_depth) & ((Xg % pitch) < 2) & ~bad
        claimw(nm, beams, C['beam'])
        return top
    deck_layers('deck-lower', ZLD, 0, NX - 1, C['teak'], C['beam'], plate_layers=1, pl_name='armour-deck', pl_x=CIT)
    deck_layers('deck-main', ZMD, 0, NX - 1, C['teak'], C['beam'])
    deck_layers('deck-poop', ZUD, 0, XPE, C['teak'], C['beam'])
    deck_layers('deck-fc', ZUD, XFC, NX - 1, C['teak'], C['beam'])
    # 艉樓、艏樓的前／後壁（白、各兩扇門）
    for xw, doors in ((XPE, (YC - 40, YC + 40)), (XFC, (YC + 25, YC - 62))):
        Xg, Yg, Zg = g(xw, xw + 1, 0, NY, WM1, ZUD - 1)
        wl = np.broadcast_to(inner[xw:xw + 1, :, WM1:ZUD - 1], (1, NY, ZUD - 1 - WM1)).copy()
        for dy_ in doors: wl &= ~((np.abs(Yg - dy_) <= 4) & (Zg < WM1 + 20))
        wl &= ~lad_mask[xw:xw + 1, :, WM1:ZUD - 1]
        claim('superstructure', (xw, 0, WM1), wl, C['white'])
    # 欄杆（艉樓、艏樓甲板邊；舷牆頂那一圈外板裡面一格）：柱每 12 格、頂上一條
    railz0, railz1 = P['rails']['z']
    rail = np.zeros((NX, NY, NZ), bool)
    edge = inner[:, :, ZTOP] & ~ndimage.binary_erosion(inner[:, :, ZTOP], structure=np.ones((3, 3), bool))
    xm = np.arange(NX)[:, None]
    edge &= (xm <= XPE)
    post = edge & ((xm % 12) == 0)
    for zz_ in range(railz0, railz1): rail[:, :, zz_] = post
    rail[:, :, railz1] = edge
    for t in P['turrets_15']:                                                # 砲塔掃過的地方不放欄杆
        rr = np.hypot(np.arange(NX)[:, None] - t['x'], np.arange(NY)[None, :] - YC)
        rail &= ~(rr <= 45)[:, :, None]
    claimw('rails', rail, C['white'])
    # 飛橋甲板（舯部、蓋在兩座露砲台上）：柚木＋樑、四周欄杆；中線撐柱與海圖室底下的柱
    hd = P['hurricane']; hx0, hx1 = hd['x']; hh = hd['half']
    Xg, Yg, Zg = g(hx0, hx1 + 1, YC - hh, YC + hh + 1, ZHD - 1, ZHD + 10)
    plate = np.zeros(np.broadcast(Xg, Yg, Zg).shape, bool)
    plate |= (Zg == ZHD) | ((Zg == ZHD - 1) & ((Xg.astype(int) % 15) < 2))
    rim_ = (Xg <= hx0) | (Xg >= hx1) | (np.abs(Yg - YC) >= hh)
    railh = (Zg > ZHD) & (Zg <= ZHD + 9) & rim_ & (((Xg.astype(int) + Yg.astype(int)) % 12 == 0) | (Zg == ZHD + 9))
    bad = (holes | lad_hat | lad_mask)[hx0:hx1 + 1, YC - hh:YC + hh + 1, ZHD - 1:ZHD + 10]
    railh &= ~((np.abs(Yg - (YC + 38)) <= 4) & (Xg < hx0 + 30))           # 梯頭那一段不放欄杆
    claim('deck-hurricane', (hx0, YC - hh, ZHD - 1), plate & ~bad, np.where(Zg == ZHD, C['teak'], C['beam']))
    claim('deck-hurricane', (hx0, YC - hh, ZHD - 1), railh & ~bad, C['white'])
    cols = [(hx0 + 5, YC), (600, YC), (hx1 - 8, YC), (hx0 + 5, YC - 16), (hx0 + 5, YC + 16), (hx0 + 25, YC - 16), (hx0 + 25, YC + 16)]
    for cxx, cyy in cols:
        Xg, Yg, Zg = g(cxx - 1, cxx + 2, cyy - 1, cyy + 2, WM1, ZHD - 1)
        claim('deck-hurricane', (cxx - 1, cyy - 1, WM1), np.ones((3, 3, ZHD - 1 - WM1), bool), C['white'])
    info['hurricane_cols'] = cols
    # 海圖室（飛橋甲板後端：白牆、窗、後門、灰頂）
    chh = P['chart_house']; cx0, cx1 = chh['x']; ch_ = chh['half']; chz = chh['h']
    Xg, Yg, Zg = g(cx0, cx1 + 1, YC - ch_, YC + ch_ + 1, WH1, WH1 + chz + 2)
    shellc = ((Xg <= cx0 + 1) | (Xg >= cx1 - 1) | (np.abs(Yg - YC) >= ch_ - 1)) & (Zg < WH1 + chz)          # 牆 2 格厚（鐵、平滑面至少 2 格；Tim 2026-10-21「海圖室改成鐵的吧」）
    win = (Zg >= WH1 + 11) & (Zg <= WH1 + 16) & (((Xg.astype(int) - cx0) % 6 >= 2) & ((Xg.astype(int) - cx0) % 6 <= 4) | ((np.abs(Yg - YC).astype(int) % 6 >= 2) & (np.abs(Yg - YC).astype(int) % 6 <= 4) & (Xg >= cx1 - 1)))
    door = (Xg <= cx0 + 1) & (np.abs(Yg - YC) <= 3) & (Zg < WH1 + 19)
    roofc = (Zg >= WH1 + chz) & (Zg <= WH1 + chz + 1) & (np.abs(Yg - YC) <= ch_ + (Zg - WH1 - chz)) & (Xg >= cx0 - (Zg - WH1 - chz)) & (Xg <= cx1 + (Zg - WH1 - chz))
    claim('chart-house', (cx0, YC - ch_, WH1), roofc, C['grey'])
    claim('chart-house', (cx0, YC - ch_, WH1), shellc & ~win & ~door, C['white'])
    hx = cx0 + 13                                                         # 舵輪的鐵立柱（裡面是齒輪、接蒸汽操舵機）：3×3 柱高 1.3 m、頂上 5×5 齒輪箱；舵輪模型（gen_parts helm_wheel）的軸從後面插進來
    Xg, Yg, Zg = g(hx - 1, hx + 4, YC - 2, YC + 3, WH1, WH1 + 14)
    ped = ((Xg >= hx) & (Xg <= hx + 2) & (np.abs(Yg - YC) <= 1)) | ((Zg >= WH1 + 10) & (np.abs(Yg - YC) <= 2) & (Xg >= hx - 1) & (Xg <= hx + 3))
    claim('chart-house', (hx - 1, YC - 2, WH1), ped, C['iron'])
    info['chart'] = dict(x0=cx0, x1=cx1, half=ch_, z=WH1, helm_x=hx)
    # 艇架（魚雷艇：主甲板上的柱＋橫樑；艉樓小艇：艉樓甲板上的柱＋橫樑）
    tb = P['torpedo_boats']; sb = P['stern_boats']
    for nm_, xs_, zt_, zfl, half_ in (('skids', (tb['x'] + 30, tb['x'] + 95, tb['x'] + 160), tb['z'] - 1, WM1, 42), ('skids', (sb['x'] + 30, sb['x'] + 80), sb['z'] - 1, WU1, 40)):
        for sx_ in xs_:
            Xg, Yg, Zg = g(sx_ - 1, sx_ + 2, YC - half_ - 1, YC + half_ + 2, zfl, zt_ + 1)
            beam_ = (Zg >= zt_ - 2) & (np.abs(Yg - YC) <= half_)
            postm = (np.abs(np.abs(Yg - YC) - half_) <= 1) & (Zg >= 0)
            postm |= (np.abs(Yg - YC) <= 1) & (Zg < zt_ - 2)
            claim(nm_, (sx_ - 1, YC - half_ - 1, zfl), beam_ | postm, C['white'])
    # 彈藥庫（艙底：銅皮地板＋鉛灰牆、一扇門；前彈藥庫分左右兩間，各吊一座露砲台）
    mags = {}
    spots = {}
    zf = 8
    for mg in P['magazines']:
        x0_, x1_ = mg['x']; dy_ = mg['dy']
        rooms = [('mag-' + mg['name'], YC - dy_, YC + dy_)] if mg['name'] == 'aft' else [('mag-fore-P', YC - dy_, YC - 2), ('mag-fore-S', YC + 2, YC + dy_)]
        for rn, y0_, y1_ in rooms:
            Xg, Yg, Zg = g(x0_, x1_ + 1, y0_, y1_ + 1, zf - 2, ZLD - 3)
            inn_ = inner[x0_:x1_ + 1, y0_:y1_ + 1, zf - 2:ZLD - 3]
            floor_ = (Zg <= zf) & inn_
            wall_ = ((Xg == x0_) | (Xg == x1_) | (Yg == y0_) | (Yg == y1_)) & (Zg > zf) & inn_
            ydoor = (y0_ + y1_) // 2
            door_ = (Xg == x1_) & (np.abs(Yg - ydoor) <= 3) & (Zg > zf) & (Zg <= zf + 20)
            claim(rn, (x0_, y0_, zf - 2), floor_, C['bronze'])
            claim(rn, (x0_, y0_, zf - 2), wall_ & ~door_, C['grey'])
            mags[rn] = {'blast': [(x0_ + x1_) // 2, (y0_ + y1_) // 2, zf + 8], 'door': [x1_ + 1, ydoor, zf + 1]}
            spots[rn] = [[xx_ + 0.5, yy_ + 0.5, zf + 1] for xx_ in range(x0_ + 3, x1_ - 7, 6) for yy_ in range(y0_ + 3, y1_ - 3, 6)
                         if inner[xx_ - 3:xx_ + 4, yy_ - 3:yy_ + 4, zf + 1:zf + 7].all()]
    # 鍋爐艙、機艙的地板（鐵格柵 z 3–4；燒火通道、主機旁站得住）＋水密艙壁（每道中間一扇門 ⇒ 艙底連成一片、不封死）
    br0, br1 = P['engine_room'][0], BR[-1]
    Xg = np.arange(NX)[:, None, None]; Zg = np.arange(NZ)[None, None, :]
    inn = np.zeros((NX, NY, NZ), bool); inn[:, :, :ZTOP + 1] = inner
    fl = inn & (Xg >= br0) & (Xg <= br1) & (Zg <= 4) & ~lad_mask
    claimw('floor', fl, C['iron'])
    bulk = np.zeros((NX, NY, NZ), bool)
    zz1 = np.arange(NZ)[None, :]; yy1 = np.arange(NY)[:, None]
    for xb_ in (60, 160, br0, BR[1], BR[2], BR[3], BR[4], 666, 860):
        w_ = inn[xb_] & (zz1 < ZLD - 3)
        zb0 = int(np.nonzero(inn[xb_, YC])[0].min())                     # 那一道的艙底（中線最低的空格）
        zb0 = max(zb0, 5 if br0 <= xb_ <= br1 else zb0)
        w_ &= ~((np.abs(yy1 - YC) <= 3) & (zz1 >= zb0) & (zz1 <= zb0 + 19))
        w_ &= ~((np.abs(np.abs(yy1 - YC) - 60) <= 3) & (zz1 >= zb0 + 5) & (zz1 <= zb0 + 24))
        bulk[xb_] = w_
    claimw('bulkheads', bulk & ~lad_mask, C['iron'])
    # 梯子（最後落：踏板與側板；穿過的艙口已經空出來）
    claimw('ladders', lad_mask, C['iron'])
    info['lad_total'] = int(lad_mask.sum())
    anc['ladders'] = ladders
    anc['mags'] = mags
    info['spots'] = spots
    return own, col, names, anc, info, stat


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    own, col, names, anc, info, stat = build()
    counts = {}
    for i, nm in enumerate(names):
        if not nm: continue
        idx = np.argwhere(own == i)
        cs = col[own == i]
        order = np.lexsort((idx[:, 2], idx[:, 1], idx[:, 0]))
        idx, cs = idx[order], cs[order]
        with open(os.path.join(out, 'part_%s.txt' % nm), 'w', newline='\n') as f:
            f.write('# 定遠號 %s —— x,y,z,color（框 %d×%d×%d、關聯 at 0,0,0）\n' % (nm, NX, NY, NZ))
            f.write('\n'.join('%d,%d,%d,%d' % (a, b, c, k) for (a, b, c), k in zip(idx.tolist(), cs.tolist())))
            f.write('\n')
        counts[nm] = len(idx)
    np.save(os.path.join(out, 'own.npy'), own)
    json.dump({'names': names[1:]}, open(os.path.join(out, 'own_names.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    # 組起來的樣子：右舷做、左舷鏡像的部件補上鏡像
    full = own > 0
    for nm in MIRR:
        if nm in names: full |= (own == names.index(nm))[:, ::-1, :]
    for nm in ('rudder', 'screw-s', 'screw-p'):                                # 模型（不是關聯）也算進外形
        pass
    lab, n = ndimage.label(full)
    sizes = np.bincount(lab.ravel())[1:]
    big = int(np.argmax(sizes)) + 1 if n else 0
    small = []
    if n > 1:
        for i in np.argsort(sizes)[:-1][:12]:
            w = np.argwhere(lab == i + 1)[0].tolist()
            small.append([int(sizes[i]), w, names[own[tuple(w)]]])
    cav = ndimage.binary_fill_holes(full) & ~full
    clab, cn = ndimage.label(cav)
    csz = np.bincount(clab.ravel())[1:]
    cav_list = []
    for i in np.argsort(csz)[::-1][:8]:
        w = np.argwhere(clab == i + 1)[0].tolist(); cav_list.append([int(csz[i]), w])
    mirror_hit = {}                                                       # 鏡像部件鏡過去之後，落在別的部件的格上幾格（要 0）
    for nm in MIRR:
        if nm in names:
            i = names.index(nm)
            mm = (own == i)[:, ::-1, :]
            mirror_hit[nm] = int((mm & (own > 0) & (own != i)).sum())
    mirror_diff = {}
    for i, nm in enumerate(names):
        if not nm or nm in MIRR or nm in ('screw-s', 'screw-p', 'barbettes', 'ladders'): continue
        m = own == i
        mirror_diff[nm] = int((m != m[:, ::-1, :]).sum())
    # 排水量（設計水線以下的外形：每一層每一欄最外兩格之間；衝角、舵、deadwood 都算）
    env = info['env']
    vol = int(env[:, :, :ZW + 1].sum())
    meta = dict(names=names[1:], counts=counts, mirror_hit=mirror_hit, ladder_cells=[int(info['lad_total']), counts.get('ladders', 0)], total=int(full.sum()), components=int(n), small=small, cavities=int(cn), cavity_top=cav_list,
                mirror_diff=mirror_diff, disp_t=round(vol * 0.001 * 1.025, 1), anchors=anc, spots=info['spots'], masts=info['masts'],
                chart=info['chart'], hurricane_cols=info['hurricane_cols'], rudder_hinge=info['rudder_hinge'],
                plan={'z_waterline': ZW, 'walk': {'lower': ZLD + 1, 'main': ZMD + 1, 'upper': ZUD + 1, 'hurricane': ZHD + 1}, 'YC': YC})
    json.dump(meta, open(os.path.join(out, 'dingyuan_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: meta[k] for k in ('counts', 'mirror_hit', 'ladder_cells', 'total', 'components', 'small', 'cavities', 'cavity_top', 'mirror_diff', 'disp_t')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
