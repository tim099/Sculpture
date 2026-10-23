# 松島號（Matsushima，1892；1894 年黃海海戰聯合艦隊旗艦）產生程式 —— 一次算出整艘的格子（0.1 m／格），照部件分開寫成 stampvox 清單＋固定點／meta 的 JSON。
# 用法：python -I -X utf8 -B gen_matsushima.py <輸出資料夾>
# 座標：X 船長（船頭 +X）、Y 船寬（中線 y=90，+Y ＝ 右舷 S；鏡像 y ↔ 180−y）、Z 高度（z=0 ＝ 龍骨底）。每個部件都用整船的框、關聯 at 0,0,0。
# 數字讀 plan.json 的 params；每個數字的出處在 plan.json 的 provenance（原圖讀數／參考資料／設計決定）。
# 結構：內傾船殼（外板 2 格、水線衝角、懸出的圓 counter、船尾 deadwood）＋長船首樓（艦首到 x 385）＋低一層的後甲板（主砲露砲台）
#       ＋四層甲板（防護甲板／中甲板（12 cm 砲列）／上甲板／船首樓甲板）＋艦橋＋煙囪、六座鍋爐、兩具臥式主機、兩支軸、兩個螺旋槳、一片舵
#       ＋軍用桅（兩層桅樓）＋司令塔、海圖室、通風筒、艇架＋彈藥庫兩間、梯子。
# 會轉的（砲塔層、砲）與外部模型（螺旋槳、舵、小艇、錨…）在 gen_parts.py 與 apply_links.py。
# 寫法照定遠號的 gen_dingyuan.py（trailhead）改：船形、甲板層、上層建築、機艙排法都換成松島號的。
import sys, os, json, math
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P = PLAN['params']
NX, NY, NZ = P['frame']
YC = (NY - 1) // 2
ZW = P['z_waterline']
ZLD, ZMD, ZUD, ZFC, ZBR = P['z_lower_deck'], P['z_middle_deck'], P['z_upper_deck'], P['z_fc_deck'], P['z_bridge']   # 各層甲板最上一層（走路格 ＋1）
MIRR = ('boilers', 'engine', 'shaft')                                    # 右舷做、左舷 mirror=y 關聯的部件
ZTA, ZTF = ZUD + 1, ZFC + 1                                               # 船殼頂：後甲板段、船首樓段（＝那一層的走路格）
XB = P['x_break']
XS, XSW, XPOST, XST, XSTW = P['x_stern_deck'], P['x_stern_wl'], P['x_post'], P['x_stem'], P['x_stem_wl']
XR, ZR = P['ram_tip']
B = P['half_beam']
C = P['colors']


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
    """船頭外形（側視）：z 這一層船殼最前面到哪。甲板 x 985 → 水線 989（艏柱微往前斜）→ 水線下鼓到衝角尖（x 997、z 51）→ 衝角下緣圓弧往後下到龍骨。"""
    z = np.asarray(z, np.float32)
    up = XST + (XSTW - XST) * np.clip((ZTF - z) / (ZTF - ZW), 0, 1)
    s = np.clip((ZW - z) / (ZW - ZR), 0, 1)
    ram = XSTW + (XR - XSTW) * np.sqrt(1 - (1 - s) ** 2)
    ff0 = P['forefoot_x0']
    ff = ff0 + (XR - ff0) * np.sqrt(np.clip(1 - ((ZR - z) / ZR) ** 2, 0, 1))
    return np.where(z >= ZW, up, np.where(z >= ZR, ram, ff)).astype(np.float32)


def x_start(z):
    """船尾外形（側視）：後甲板 x 6、水線 x 66（懸出的 counter，往下照二次曲線收）；水線下到 z 52 斜到舵柱 x 84，再下去就是舵柱。"""
    z = np.asarray(z, np.float32)
    up = XS + (XSW - XS) * (np.clip(ZTA - z, 0, None) / (ZTA - ZW)) ** 2
    knee = XSW + (XPOST - XSW) * np.clip((ZW - z) / (ZW - 52), 0, 1)
    return np.where(z >= ZW, up, knee).astype(np.float32)


def z_bottom(x):
    """船底：中段平在 z 0；船尾從 x 300 往後收到舵柱（z 58）—— 雙螺旋槳在 counter 下面。"""
    rx, rz = P['run']
    x = np.asarray(x, np.float32)
    return np.where(x < rx, rz * np.clip((rx - x) / (rx - XPOST), 0, 1), 0).astype(np.float32)


def half_width(X, Z):
    """船殼在 (x, z) 的半寬（< 0 ＝ 不在船殼裡）。平面：中段全寬、船尾尖圓、船頭收尖；剖面：舭部照 p 次方收、水線上 1.4 m 起內傾。"""
    k = np.clip((np.asarray(Z, np.float32) - (ZW - 8)) / (ZTF - (ZW - 8)), 0, 1) ** 0.6   # 水線下照細的線形、往上漸漸換成甲板的平面（船頭外飄、counter 圓胖）
    lerp = lambda a, b: a + (b - a) * k
    xa, xf = lerp(P['x_aft_full'], P['x_aft_full_deck']), lerp(P['x_fwd_full'], P['x_fwd_full_deck'])
    a1, b1 = lerp(P['stern_pow'][0], P['stern_pow_deck'][0]), lerp(P['stern_pow'][1], P['stern_pow_deck'][1])
    a2, b2 = lerp(P['bow_pow'][0], P['bow_pow_deck'][0]), lerp(P['bow_pow'][1], P['bow_pow_deck'][1])
    xs, xe = x_start(Z), x_end(Z)
    xp = np.minimum(xe, XST)
    hp = np.full(np.broadcast(X, Z).shape, B, np.float32)
    ta = np.clip((xa - X) / np.maximum(xa - xs, 1), 0, 1)
    tf = np.clip((X - xf) / np.maximum(xp - xf, 1), 0, 1)
    hp = np.where(X < xa, B * (1 - ta ** a1) ** b1, hp)
    hp = np.where(X > xf, np.where(X <= xp, B * (1 - tf ** a2) ** b2, 0), hp)
    zt0 = P['z_tumble0']
    tb = P['tumble'] * np.clip((Z - zt0) / (ZTF - zt0), 0, 1) ** 1.3
    hp = hp - tb * hp / B
    ta0 = np.clip((P['x_aft_full'] - X) / np.maximum(P['x_aft_full'] - xs, 1), 0, 1); tf0 = np.clip((X - P['x_fwd_full']) / np.maximum(xp - P['x_fwd_full'], 1), 0, 1)
    full = np.where(X < P['x_aft_full'], 1 - ta0, np.where(X > P['x_fwd_full'], 1 - tf0, 1.0))
    p0, p1 = P['bilge_p']
    p = p0 + (p1 - p0) * full
    zb = z_bottom(X)
    zt = zb + P['bilge_h']
    s = np.clip((zt - Z) / P['bilge_h'], 0, 1)
    f = np.where(Z < zt, (1 - np.minimum(s, 0.9999) ** p) ** (1 / p), 1.0)
    hw = hp * f
    rk, rl = P['ram_wedge']                                               # 衝角：從艏柱往前的尖楔
    hw = np.maximum(hw, np.where((X <= xe) & (xe > XST) & (X > XST - 30), np.minimum(rk * (xe - X), rl), -1))
    out = (X < xs) | (X > xe) | (Z < zb) | (Z > ZTF)
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
        x1, y1, z1 = min(x0 + sx, NX), min(y0 + sy, NY), min(z0 + sz, NZ)
        if not np.isscalar(color): color = np.broadcast_to(color, mask.shape)[:x1 - x0, :y1 - y0, :z1 - z0]
        mask = mask[:x1 - x0, :y1 - y0, :z1 - z0]
        R = own[x0:x1, y0:y1, z0:z1]
        Cc = col[x0:x1, y0:y1, z0:z1]
        m = mask & (R == 0) & ~res[x0:x1, y0:y1, z0:z1]
        if name not in names: names.append(name)
        i = names.index(name)
        R[m] = i
        Cc[m] = color if np.isscalar(color) else color[m]
        stat[name] = stat.get(name, 0) + int(m.sum())
        if name in MIRR:
            ym = 2 * YC - (y1 - 1)
            res[x0:x1, ym:ym + (y1 - y0), z0:z1] |= m[:, ::-1, :]
        return m

    def claimw(name, mask, color):                                       # 整個框的遮罩
        return claim(name, (0, 0, 0), mask, color)

    anc, info = {}, {}
    ZH = ZTF + 6                                                          # 船殼的計算高度（頂上多幾層 ⇒ 頂面不算外板）
    xx = np.arange(NX, dtype=np.float32)[:, None]; zz = np.arange(ZH, dtype=np.float32)[None, :]
    hw = half_width(xx, np.minimum(zz, ZTF))
    hw[:, ZTF + 1:] = hw[:, ZTF:ZTF + 1]
    Y = np.arange(NY, dtype=np.float32)[None, :, None]
    DY = np.abs(Y - YC)
    env = DY <= hw[:, None, :]                                            # (NX, NY, ZH)
    # 57 mm 突出砲台（船首樓側面的半圓凸台，往下收成托座）
    sp = P['sponsons_57']; spr = sp['r']; spz0, spz1 = sp['z']
    X3 = np.arange(NX, dtype=np.float32)[:, None, None]; Z3 = np.arange(ZH, dtype=np.float32)[None, None, :]
    sp_cent = []
    for sx_ in sp['x']:
        hws = float(half_width(np.float32(sx_), np.float32(120)))
        for sg in (1, -1):
            cy = YC + sg * (hws - 2)
            rz = np.where(Z3 >= spz0, spr, spr * np.clip((Z3 - (spz0 - 10)) / 10, 0, 1))
            env |= (np.hypot(X3 - sx_, Y - cy) <= rz) & (Z3 >= spz0 - 10) & (Z3 <= ZTF)
            sp_cent.append((sx_, cy, sg))
    info['sponsons'] = sp_cent
    env_full = env.copy()
    env = env[:, :, :ZTF + 1].copy()
    env[:XB, :, ZTA + 1:] = False                                         # 後甲板段比船首樓低一層；侵蝕照沒切的算 ⇒ 頂面不會長出一層蓋子
    inner2 = ndimage.binary_erosion(env_full, iterations=P['t_shell'])[:, :, :ZTF + 1]
    inner1 = ndimage.binary_erosion(env_full, iterations=1)[:, :, :ZTF + 1]
    del env_full
    shell = env & ~inner2
    info['env'] = env; info['inner'] = inner2; info['hw'] = hw
    Zs = np.arange(ZTF + 1)[None, None, :]
    Xs = np.arange(NX)[:, None, None]
    Ys = np.arange(NY)[None, :, None]
    b0, b1 = P['boot']
    band = np.where(Zs < b0, C['red'], np.where(Zs <= b1, C['black'], C['white'])).astype(np.uint8)
    outer = env & ~inner1
    # 開口（刻穿外板）：12 cm 砲列的砲門、艏追擊砲的砲門、突出砲台的砲門、船尾與艏的魚雷管口
    side = DY >= (hw[:, None, :ZTF + 1] - 6)                              # 靠舷側那幾格（不切到中線的甲板）
    ports = np.zeros((NX, 1, ZTF + 1), bool)
    bt = P['battery']; pz0, pz1 = bt['port_z']
    for x_ in bt['x']:
        ports[x_ - bt['port_half_x']:x_ + bt['port_half_x'] + 1, 0, pz0:pz1 + 1] = True
    bc = P['bow_chasers']; bh, bz0, bz1 = bc['port']
    ports[bc['x'] - bh:bc['x'] + bh + 1, 0, bz0:bz1 + 1] = True
    open_m = ports & side
    for (sx_, cy, sg) in sp_cent:                                        # 突出砲台：朝舷外那一面開口
        pz_0, pz_1 = sp['port_z']
        Xg, Yg, Zg = g(sx_ - spr - 1, sx_ + spr + 2, int(cy) - spr - 1, int(cy) + spr + 2, pz_0, pz_1 + 1)
        o_ = (np.abs(Xg - sx_) <= 4) & ((Yg - cy) * sg >= 2)
        open_m[sx_ - spr - 1:sx_ + spr + 2, int(cy) - spr - 1:int(cy) + spr + 2, pz_0:pz_1 + 1] |= np.broadcast_to(o_, (2 * spr + 3, 2 * spr + 3, pz_1 + 1 - pz_0))
    tt = np.zeros((NX, NY, ZTF + 1), bool)                               # 魚雷管口：艏（艏柱上、水線上 1.5 m）、艉（counter 上）、兩舷（x 245）—— 只換色
    tt |= (np.abs(Xs - XST) <= 6) & (np.hypot(Ys - YC, Zs - (ZW + 15)) <= 2.2)
    tt |= (Xs <= XS + 8) & (np.hypot(Ys - YC, Zs - (ZTA - 14)) <= 2.2)
    tt |= (np.abs(Xs - 245) <= 2) & (np.abs(Zs - (ZW + 18)) <= 2) & side
    shell &= ~open_m
    sc = P['scuttles']
    scut = np.zeros((NX, 1, ZTF + 1), bool)
    for x0 in range(30, 980, sc['pitch']):
        if any(abs(x0 - xb_) < 10 for xb_ in bt['x']): continue
        scut[x0:x0 + 2, 0, sc['z'] + 3:sc['z'] + 5] = True                # 下排：水線上約 4 m
        if x0 > XB + 10 and abs(x0 - bc['x']) > 14 and all(abs(x0 - s_) > 14 for s_ in sp['x']):
            scut[x0:x0 + 2, 0, sc['z_up']:sc['z_up'] + 2] = True           # 上排：船首樓
    shell_col = np.where(outer, np.where(tt | (scut & (Zs > b1 + 4)), C['black'], band), np.where(Zs > ZLD, C['wall'], C['iron'])).astype(np.uint8)
    # ── 舵（獨立子作品，先佔 ⇒ 船殼在舵柱那裡留孔）──
    R_ = P['rudder']
    rx0, rx1 = R_['x']; rz0, rz1 = R_['z']; px0, px1 = R_['post']; stock_top = R_['stock_top']
    Xg, Yg, Zg = g(0, 100, YC - 3, YC + 4, 0, 90)
    rud = (Xg >= rx0) & (Xg <= rx1) & (np.abs(Yg - YC) <= 1) & (Zg >= rz0) & (Zg <= rz1) & ~((Xg < rx0 + 5) & (Zg > rz1 - 5))   # 舵葉（後上角削掉）
    rud |= (np.hypot(Xg - (rx1 - 0.5), Yg - YC) <= 1.6) & (Zg >= rz1) & (Zg <= stock_top)                                        # 舵桿，往上穿進 counter
    rud |= (Xg >= rx0 + 6) & (Xg <= rx1 - 2) & (np.abs(Yg - YC) <= 2) & ((Zg.astype(int) - rz0) % 12 == 6) & (Zg <= rz1 - 4)    # 舵葉的橫筋
    claim('rudder', (0, YC - 3, 0), rud, C['iron'])
    anc['rudder'] = {'stock-top': [rx1, YC, stock_top]}
    info['rudder_hinge'] = [rx1 + 0.5, YC + 0.5, rz0]
    # ── 螺旋槳（兩個；右舷 S 照內旋 ⇒ 左旋、左舷 P 照 y 鏡像）──
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
    blade = (rr <= sr) & (rr > 2.5) & (arcl <= halfw) & (np.abs(Xg - sxh + sgn * arcl * 0.45) <= 1)
    hub = ((np.abs(Xg - sxh) <= 2.5) & (rr <= 3.2)) | ((Xg > sxh + 2) & (Xg <= sxh + 5) & (rr <= 2.4)) | ((Xg < sxh - 2) & (Xg >= sxh - 4) & (rr <= 3.2 - (sxh - 2 - Xg)))
    scr = hub | blade
    claim('screw-s', (sxh - 6, YC + sdy - sr - 2, max(0, szh - sr - 2)), scr, C['bronze'])
    claim('screw-p', (sxh - 6, YC - sdy - sr - 2, max(0, szh - sr - 2)), scr[:, ::-1, :], C['bronze'])
    anc['screw-s'] = {'hub': [sxh, YC + sdy, szh], 'shaft-fwd': [sxh + 5, YC + sdy, szh]}
    anc['screw-p'] = {'hub': [sxh, YC - sdy, szh], 'shaft-fwd': [sxh + 5, YC - sdy, szh]}
    # ── 船殼外板 ──
    claimw('hull', np.pad(shell, ((0, 0), (0, 0), (0, NZ - ZTF - 1))), np.pad(shell_col, ((0, 0), (0, 0), (0, NZ - ZTF - 1))))
    # deadwood（船尾中線的鰭）＋舵柱＋舵底的龍骨靴＋軸架（A 字）
    sk0, sk1 = P['skeg']
    Xg, Yg, Zg = g(0, sk1 + 1, YC - 3, YC + 4, 0, 72)
    zb_ = z_bottom(Xg)
    skeg = (Xg >= sk0) & (np.abs(Yg - YC) <= 2) & (Zg <= zb_ + 3)
    skeg |= (Xg >= px0) & (Xg <= px1) & (np.abs(Yg - YC) <= 2) & (Zg <= zb_ + 3)
    skeg |= (Xg >= rx0 - 2) & (Xg <= px1) & (np.abs(Yg - YC) <= 1) & (Zg <= rz0 - 2)
    claim('hull', (0, YC - 3, 0), skeg, np.where(Zg < b0, C['red'], C['black']))
    ax_ = sxh + 9
    for (ty, tz) in ((YC + 3, szh + 14), (YC + sdy - 6, szh + 30)):
        o, m_ = seg((ax_ + 0.5, YC + sdy + 0.5, szh + 0.5), (ax_ + 0.5, ty + 0.5, tz + 0.5), 1.4)
        sx_, sy_, sz_ = m_.shape
        m_ = m_ & ~info['inner'][o[0]:o[0] + sx_, o[1]:o[1] + sy_, o[2]:o[2] + sz_]
        claim('hull', o, m_, C['red'])
        claim('hull', (o[0], 2 * YC - (o[1] + sy_ - 1), o[2]), m_[:, ::-1, :], C['red'])
    # ── 梯子（先算位置 ⇒ 艙口、別的部件讓開）──
    hat = np.zeros((NX, NY, NZ), bool)                                    # 艙口（甲板不落）
    holes = np.zeros((NX, NY, NZ), bool)                                  # 煙囪、桅、露砲台中間…（甲板不落）
    ladders = []
    lad_mask = np.zeros((NX, NY, NZ), bool)

    def ladder(nm, x_top, y, z_lo, z_hi, dirx, run_k=0.55, hatch_decks=(), width=2):
        """梯子：最高一階在 x_top、往 dirx 爬（爬的人往 dirx 走）；z_lo ＝ 下層走路格、z_hi ＝ 上層走路格。回傳四點。"""
        H = z_hi - z_lo; run = int(round(H * run_k))
        xb = x_top - dirx * run
        steps = []
        for k in range(1, H // 3 + 1):
            zz_ = z_lo + 3 * k - 1
            if zz_ >= z_hi - 1: break
            x_ = int(round(xb + dirx * run * (zz_ - z_lo) / H))
            steps.append((x_, zz_))
            lad_mask[min(x_, x_ + dirx):max(x_, x_ + dirx) + 1, y - width:y + width + 1, zz_] = True
        xprev = None
        rails = []
        for zz_ in range(z_lo, z_hi - 1):                                  # 兩根側板（x 換格的那一層兩格都放 ⇒ 六連通不斷）
            x_ = int(round(xb + dirx * run * (zz_ - z_lo) / H))
            for xq in {x_, xprev if xprev is not None else x_}:
                lad_mask[xq, y - width - 1, zz_] = True; lad_mask[xq, y + width + 1, zz_] = True
                rails.append((xq, zz_))
            xprev = x_
        for zd in hatch_decks:                                             # 甲板上的艙口（造船規格 §9.3 開梯口的做法；TASK-0838）
            # 梯頂那一頭：開到側板在這層甲板裡蓋到的最後一欄為止（不多開 ⇒ head 不踩在洞上）；
            # 梯腳那一頭：開到人站在那一階、頭上 1.4 m 碰不到甲板底為止。
            # 舊寫法是「梯子穿過那一層的位置 ± 5」⇒ 梯頂那一頭多開 6 排、head 踩在洞上（ladcheck 2026-10-23：13 座 ✗）。
            xe = max((xq * dirx for xq, zq in rails if zd - 5 <= zq <= zd), default=None)
            if xe is None: continue
            xe *= dirx
            xs = int(math.floor(xb + dirx * run * (zd - 5 - 14 - z_lo) / H)) if dirx > 0 else int(math.ceil(xb + dirx * run * (zd - 5 - 14 - z_lo) / H))
            hat[min(xs, xe):max(xs, xe) + 1, y - width - 1:y + width + 2, zd - 5:zd + 1] = True
        lo, hi = steps[0], steps[-1]
        d = {'name': nm, 'foot': [lo[0] - dirx * 3, y, z_lo], 'lo': [lo[0], y, lo[1] + 1], 'hi': [hi[0], y, hi[1] + 1], 'head': [hi[0] + dirx * 4, y, z_hi]}
        ladders.append(d)
        return d

    WH, WL1, WM1, WU1, WF1, WB1 = 5, ZLD + 1, ZMD + 1, ZUD + 1, ZFC + 1, ZBR + 1   # 各層走路格（WH ＝ 機艙地板）
    tm = P['turret_main']; bb = P['barbette']; bx_ = bb['x']
    ladder('barbette', bx_ - 6, YC, WL1, tm['z_table'] + 1, 1, run_k=0.3)    # 露砲台裡：防護甲板 → 轉盤中間的艙口（彈藥從這裡吊上來）
    LAD = [  # 名字, 最高一階 x, y, 下層, 上層, 往哪爬, 穿過哪幾層的艙口
        ('engine', 520, YC, WH, WL1, 1, (ZLD,)),
        ('stokehold', 664, YC, WH, WL1, -1, (ZLD,)),
        ('lm-aft', 210, YC, WL1, WM1, -1, (ZMD,)),
        ('lm-mid', 470, YC + 30, WL1, WM1, 1, (ZMD,)),
        ('lm-fwd', 760, YC, WL1, WM1, 1, (ZMD,)),
        ('mu-aft', 190, YC, WM1, WU1, -1, (ZUD,)),
        ('mu-mid', 560, YC + 30, WM1, WU1, 1, (ZUD,)),
        ('mu-fwd', 840, YC, WM1, WU1, 1, (ZUD,)),
        ('uf-fwd', 880, YC, WU1, WF1, 1, (ZFC,)),
        ('uf-mid', 620, YC - 34, WU1, WF1, 1, (ZFC,)),
        ('break-P', XB - 1, YC - 46, WU1, WF1, 1, ()),
        ('break-S', XB - 1, YC + 46, WU1, WF1, 1, ()),
        ('bridge-P', P['bridge']['x'][0], YC - 30, WF1, WB1, 1, ()),
        ('bridge-S', P['bridge']['x'][0], YC + 30, WF1, WB1, 1, ()),
    ]
    for nm, xt, y, zl, zh, dx, hd in LAD:
        ladder(nm, xt, y, zl, zh, dx, hatch_decks=hd)
    # ── 煙囪（中線、圓；甲板以下的直煙道也在煙囪部件裡，下到煙箱頂）──
    F = P['funnel']; fx, fr, ftop = F['x'], F['r'], F['top']
    z_smoke = 48
    Xg, Yg, Zg = g(fx - fr - 3, fx + fr + 4, YC - fr - 3, YC + fr + 4, z_smoke - 6, ftop + 1)
    rr = np.hypot(Xg - fx, Yg - YC)
    tube = (rr <= fr + 0.5) & (rr > fr - 2 + 0.5) & (Zg >= z_smoke - 6) & (Zg <= ftop)
    rim = (rr <= fr + 2.0) & (rr > fr - 2 + 0.5) & (Zg >= ftop - 3)
    band_ = (rr <= fr + 1.2) & (rr > fr - 2 + 0.5) & (np.abs(Zg - (ftop - F['band'])) <= 1)
    cl = (np.abs(Yg - YC) < 0.5) & (Zg >= z_smoke - 6) & (Zg <= z_smoke + 2) & (rr <= fr + 0.5)
    claim('funnel', (fx - fr - 3, YC - fr - 3, z_smoke - 6), tube | rim | band_ | cl, C['black'])
    holes[fx - fr - 3:fx + fr + 4, YC - fr - 3:YC + fr + 4, z_smoke - 6:ftop + 1] |= (rr <= fr + 0.9)
    anc['funnel'] = {'smoke': [fx, YC, ftop - 1]}
    # ── 鍋爐（六座：兩舷各三、爐門朝中線；右舷做、左舷鏡像）＋煙箱（爐前頂上，接煙囪）──
    BO = P['boiler']
    a_ = {}
    y0, y1 = YC + BO['y_front'], YC + BO['y_front'] + BO['len']
    for k, bx in enumerate(P['boiler_x']):
        Xg, Yg, Zg = g(bx - 25, bx + 26, y0, y1 + 1, 2, 60)
        rr = np.hypot(Xg - bx, Zg - BO['zc'])
        cyl = (rr <= BO['r']) & (Yg >= y0) & (Yg <= y1)
        front = cyl & (Yg <= y0 + 1)
        furn = np.zeros(cyl.shape, bool)
        for fdx, fz in ((-11, BO['zc'] - 8), (0, BO['zc'] - 12), (11, BO['zc'] - 8)):
            furn |= front & (np.hypot(Xg - (bx + fdx), Zg - fz) <= 3.6)
        saddle = (np.abs(Xg - bx) <= 15) & (Zg <= 8) & (Yg >= y0 + 3) & (Yg <= y1 - 3) & ((Yg.astype(int) - y0) % 9 < 2)
        okb = ~lad_mask[bx - 25:bx + 26, y0:y1 + 1, 2:60] & info['inner'][bx - 25:bx + 26, y0:y1 + 1, 2:60]
        claim('boilers', (bx - 25, y0, 2), furn & okb, C['black'])
        claim('boilers', (bx - 25, y0, 2), (cyl | saddle) & okb, C['iron'])
        a_['boiler-%d' % (k + 1)] = [bx, (y0 + y1) // 2, BO['zc']]
        a_['stoke-%d' % (k + 1)] = [bx, YC + 4, 5]
    xa_, xb2 = min(P['boiler_x']) - 16, max(P['boiler_x']) + 16                # 煙箱：爐前頂上（中線 +1 … 爐前 +8）、一整排
    hm = (holes | lad_mask)[xa_:xb2 + 1, YC + 1:y0 + 9, z_smoke - 6:z_smoke + 3]
    claim('boilers', (xa_, YC + 1, z_smoke - 6), ~hm, C['iron'])
    cm = ~(holes | lad_mask)[xa_:xb2 + 1, YC:YC + 1, z_smoke - 6:z_smoke + 3]          # 中線那一欄（兩舷鏡像都不含 ⇒ 歸煙囪）
    claim('funnel', (xa_, YC, z_smoke - 6), cm, C['iron'])
    a_['uptake'] = [fx, YC, z_smoke - 6]
    anc['boilers'] = a_
    # ── 主機（兩具臥式三缸三段膨脹；右舷做、左舷鏡像）：曲軸沿 x、汽缸沿 +y 躺著、連桿、底座、凝汽器（在曲軸內側）──
    E = P['engine']
    ey, ez = YC + E['dy_crank'], E['z']
    ex0, ex1 = min(E['x']) - 14, max(E['x']) + 14
    Xg, Yg, Zg = g(ex0 - 2, ex1 + 3, YC + 1, YC + 80, 2, 46)
    eng = (np.hypot(Yg - ey, Zg - ez) <= 3) & (Xg >= ex0 - 2) & (Xg <= ex1 + 2)
    bed = (Xg >= ex0) & (Xg <= ex1) & (Yg >= ey - 20) & (Yg <= ey + 10 + E['cyl_len'] + 4) & (Zg <= 7) & (Zg >= 3)
    cylm = np.zeros(eng.shape, bool); cover = np.zeros(eng.shape, bool); rod = np.zeros(eng.shape, bool); bnd = np.zeros(eng.shape, bool)
    c0 = ey + 10
    for cxx in E['x']:
        rr = np.hypot(Xg - cxx, Zg - ez)
        cylm |= (rr <= E['r_cyl']) & (Yg >= c0) & (Yg <= c0 + E['cyl_len'])
        cover |= (rr <= E['r_cyl'] + 1.2) & ((np.abs(Yg - c0) <= 0.5) | (np.abs(Yg - (c0 + E['cyl_len'])) <= 0.5))
        bnd |= (rr <= E['r_cyl'] + 0.6) & (np.abs(Yg - (c0 + E['cyl_len'] // 2)) <= 0.5)
        rod |= (np.hypot(Xg - cxx, Zg - ez) <= 1.5) & (Yg >= ey) & (Yg < c0)
        rod |= (np.abs(Xg - cxx) <= 2) & (np.abs(Yg - ey) <= 4) & (np.abs(Zg - ez) <= 6)
        cylm |= (np.abs(Xg - cxx) <= 3) & (Zg >= 7) & (Zg <= ez - E['r_cyl']) & (Yg >= c0 + 4) & (Yg <= c0 + E['cyl_len'] - 4)
    cond = (Xg >= ex0 + 4) & (Xg <= ex1 - 4) & (np.hypot(Yg - (ey - 13), Zg - 14) <= 6)              # 凝汽器（沿 x 的圓筒，曲軸內側，坐在底座上）
    off = (ex0 - 2, YC + 1, 2)
    inside = info['inner'][ex0 - 2:ex1 + 3, YC + 1:YC + 80, 2:46] & ~lad_mask[ex0 - 2:ex1 + 3, YC + 1:YC + 80, 2:46]
    claim('engine', off, (cover | bnd) & inside, C['brass'])
    claim('engine', off, (eng | bed | cylm | rod | cond) & inside, C['iron'])
    anc['engine'] = {'core': [E['x'][1], ey + 20, ez], 'cyl-1': [E['x'][0], c0 + 10, ez], 'cyl-2': [E['x'][1], c0 + 10, ez], 'cyl-3': [E['x'][2], c0 + 10, ez],
                     'tend-1': [E['x'][1], ey - 6, 8], 'tend-2': [E['x'][1], c0 + E['cyl_len'] + 6, 8]}
    # 軸（右舷；左舷鏡像）：主機曲軸後端 → 螺旋槳轂前；兩端固定點在軸心那一格
    fa_ = (ex0 - 2 + 0.5, ey + 0.5, ez + 0.5); fb_ = (sxh + 5 + 0.5, YC + sdy + 0.5, szh + 0.5)
    o, m_ = seg(fb_, fa_, P['shaft_r'])
    claim('shaft', o, m_, C['iron'])
    anc['shaft'] = {'aft': [sxh + 5, YC + sdy, szh], 'fwd': [ex0 - 2, ey, ez]}
    # ── 露砲台（固定的裝甲圈＋四根撐柱）──
    r0, r1 = bb['r']; bz0, bz1 = bb['z']
    Xg, Yg, Zg = g(bx_ - r1 - 1, bx_ + r1 + 2, YC - r1 - 1, YC + r1 + 2, bz0, bz1 + 1)
    rr = np.hypot(Xg - bx_, Yg - YC)
    ring = (rr > r0 - 0.5) & (rr <= r1 + 0.5)
    post = np.zeros(ring.shape, bool)
    for a in (45, 135, 225, 315):
        post |= np.hypot(Xg - (bx_ + 28 * math.cos(math.radians(a))), Yg - (YC + 28 * math.sin(math.radians(a)))) <= 2
    # 防護甲板那一層、船尾那一側開一扇門（0.7 × 2.0 m）：圈裡的接收處接上防護甲板（揚弾手倒了，預備水手從 lm-aft 走得進來；TASK-0841）
    door = (Xg < bx_) & (np.abs(Yg - YC) <= 3) & (Zg <= bz0 + 19)
    o = (bx_ - r1 - 1, YC - r1 - 1, bz0)
    claim('barbette', o, ring & ~door & ~lad_mask[o[0]:o[0] + ring.shape[0], o[1]:o[1] + ring.shape[1], bz0:bz1 + 1], C['white'])
    claim('barbette-posts', o, post & ~lad_mask[o[0]:o[0] + ring.shape[0], o[1]:o[1] + ring.shape[1], bz0:bz1 + 1], C['iron'])
    # 揚弾筒（主砲；Tim 2026-10-23「彈藥從艙底經過轉盤中間吊上砲」，TASK-0841 kind=hoist）：轉軸上、防護甲板 → 轉盤中間的洞底下，
    #   外徑 1.1 m、內徑 0.5 m（壁 0.3 m ＝ 史料揚弾筒裝甲 250–300 mm，ja Wikipedia 松島型）；筒底朝右舷開口（0.5 × 2.0 m）＝ 艙底接收處。
    tube = (rr > 2.5) & (rr <= 5.5) & ~((Yg > YC) & (np.abs(Xg - bx_) <= 2) & (Zg <= bz0 + 19))
    claim('hoist', o, tube & ~lad_mask[o[0]:o[0] + ring.shape[0], o[1]:o[1] + ring.shape[1], bz0:bz1 + 1], C['iron'])
    anc['hoist'] = {'bottom': [bx_, YC + 7, bz0], 'top': [bx_, YC, tm['z_table'] + 16]}
    holes[bx_ - r0:bx_ + r0 + 1, YC - r0:YC + r0 + 1, ZLD + 1:bz1 + 1] |= (np.hypot(np.arange(bx_ - r0, bx_ + r0 + 1)[:, None] - bx_, np.arange(YC - r0, YC + r0 + 1)[None, :] - YC) <= r1 + 0.5)[:, :, None]
    anc['barbette'] = {'pivot': [bx_, YC, tm['z_table']]}
    # ── 桅（軍用桅：實心鋼管、兩層圓的裝甲桅樓、頂桿、兩根信號桁、斜桁、桅腳往前的吊艇桿）──
    M = P['mast']; mx = M['x']
    Xg, Yg, Zg = g(mx - 100, mx + 110, YC - 45, YC + 46, M['z0'], M['pole_top'] + 2)
    rr = np.hypot(Xg - mx, Yg - YC)
    t1, t2 = M['top1'], M['top2']; wh = M['wall_h']
    tube = (rr <= M['r'] + 0.5) & (Zg <= t1)
    tube |= (rr <= M['r_mid'] + 0.5) & (Zg > t1) & (Zg <= t2)
    pl = ((rr <= M['r1'] + 0.5) & (Zg == t1)) | ((rr <= M['r2'] + 0.5) & (Zg == t2))
    door1 = (np.abs(Yg - YC) <= 3) & (Xg < mx) & (Zg > t1) & (Zg <= t1 + 12)
    door2 = (np.abs(Yg - YC) <= 3) & (Xg < mx) & (Zg > t2) & (Zg <= t2 + 12)
    wallm = (rr > M['r1'] - 1.5) & (rr <= M['r1'] + 0.5) & (Zg > t1) & (Zg <= t1 + wh) & ~door1
    wallm |= (rr > M['r2'] - 1.5) & (rr <= M['r2'] + 0.5) & (Zg > t2) & (Zg <= t2 + wh) & ~door2
    bd0, bd1 = M['band']                                                  # 桅樓上半圈的裝甲帶（中間留一圈射擊縫：47 mm 從縫裡開）＋四根撐柱
    for rT, tT in ((M['r1'], t1), (M['r2'], t2)):
        wallm |= (rr > rT - 1.5) & (rr <= rT + 0.5) & (Zg >= tT + bd0) & (Zg <= tT + bd1)
        for a in (0, 90, 180, 270):
            wallm |= (np.hypot(Xg - (mx + (rT - 0.5) * math.cos(math.radians(a + 45))), Yg - (YC + (rT - 0.5) * math.sin(math.radians(a + 45)))) <= 1.2) & (Zg > tT) & (Zg < tT + bd0)
    rim1 = (rr > M['r1'] - 0.5) & (rr <= M['r1'] + 1.5) & ((Zg == t1 + bd1) | (Zg == t1 - 1))
    rim2 = (rr > M['r2'] - 0.5) & (rr <= M['r2'] + 1.5) & ((Zg == t2 + bd1) | (Zg == t2 - 1))
    pole = (rr <= M['pole_r'] + 0.5) & (Zg > t2) & (Zg <= M['pole_top'])
    truck = (rr <= M['pole_r'] + 1.5) & (Zg >= M['pole_top'] - 1) & (Zg <= M['pole_top'])
    sub = tube | pl | pole                                               # 信號桁不落格子：改成帆桁模型（apply_links.py，meta kind=yard、mast=main ⇒ 遊戲才認得這根桅）
    o_m = (mx - 100, YC - 45, M['z0'])
    claim('mast', o_m, (truck | rim1 | rim2) & ~lad_mask[o_m[0]:o_m[0] + 210, o_m[1]:o_m[1] + 91, o_m[2]:M['pole_top'] + 2], C['white'])
    claim('mast', o_m, (sub | wallm) & ~lad_mask[o_m[0]:o_m[0] + 210, o_m[1]:o_m[1] + 91, o_m[2]:M['pole_top'] + 2], C['white'])
    gz, gdeg, glen = M['gaff']
    ca, sa = math.cos(math.radians(gdeg)), math.sin(math.radians(gdeg))
    g0 = mx - M['r_mid'] + 0.5
    peak = (g0 - glen * ca, YC + 0.5, gz + glen * sa + 0.5)
    o, m_ = seg((g0, YC + 0.5, gz + 0.5), peak, 1.1)
    claim('mast', o, m_, C['white'])
    (dx0, dz0), (dx1, dz1) = M['derrick']
    o, m_ = seg((dx0 + 0.5, YC + 0.5, dz0 + 0.5), (dx1 + 0.5, YC + 0.5, dz1 + 0.5), 1.6)
    claim('mast', o, m_, C['white'])
    holes[mx - 8:mx + 9, YC - 8:YC + 9, ZLD + 1:ZFC + 1] |= (np.hypot(np.arange(mx - 8, mx + 9)[:, None] - mx, np.arange(YC - 8, YC + 9)[None, :] - YC) <= M['r'] + 0.9)[:, :, None]
    info['mast'] = {'x': mx, 'top1': t1, 'top2': t2, 'r1': M['r1'], 'r2': M['r2'], 'pole_top': M['pole_top'], 'gaff_peak': [peak[0] - 0.5, YC, peak[2] - 0.5], 'wall_h': wh}
    # ── 司令塔（125 mm、圓；頂下一圈觀察縫、後面一扇門）──
    cn = P['conning']; ccx = cn['x']; cri, cro = cn['r']; ch = cn['h']
    Xg, Yg, Zg = g(ccx - cro - 1, ccx + cro + 2, YC - cro - 1, YC + cro + 2, WF1, WF1 + ch + 2)
    rr = np.hypot(Xg - ccx, Yg - YC)
    wall = (rr > cri - 0.5) & (rr <= cro + 0.5) & (Zg < WF1 + ch)
    slit = (Zg >= WF1 + ch - 5) & (Zg <= WF1 + ch - 4) & (np.abs(np.arctan2(Yg - YC, Xg - ccx)) < 2.2)
    door = (Xg < ccx) & (np.abs(Yg - YC) <= 3) & (Zg < WF1 + 19)
    roof = (rr <= cro + 0.5) & (Zg >= WF1 + ch) & (Zg <= WF1 + ch + 1)
    claim('conning', (ccx - cro - 1, YC - cro - 1, WF1), (wall & ~slit & ~door) | roof, C['grey'])
    # ── 海圖室（司令塔後；白牆、窗、後門、灰頂）──
    chh = P['chart_house']; cx0, cx1 = chh['x']; ch_ = chh['half']; chz = chh['h']
    Xg, Yg, Zg = g(cx0, cx1 + 1, YC - ch_, YC + ch_ + 1, WF1, WF1 + chz + 2)
    shellc = ((Xg == cx0) | (Xg == cx1) | (np.abs(Yg - YC) == ch_)) & (Zg < WF1 + chz)
    win = (Zg >= WF1 + 11) & (Zg <= WF1 + 15) & (np.abs(Yg - YC) == ch_) & (((Xg.astype(int) - cx0) % 6 >= 2) & ((Xg.astype(int) - cx0) % 6 <= 4))
    doorc = (Xg == cx0) & (np.abs(Yg - YC) <= 3) & (Zg < WF1 + 19)
    roofc = (Zg >= WF1 + chz) & (Zg <= WF1 + chz + 1)
    claim('chart-house', (cx0, YC - ch_, WF1), roofc, C['grey'])
    claim('chart-house', (cx0, YC - ch_, WF1), shellc & ~win & ~doorc, C['white'])
    # ── 艦橋（司令塔上的一片甲板，兩翼伸到兩舷；柚木＋樑、四周欄杆、撐柱）──
    br = P['bridge']; bx0, bx1 = br['x']; bh_ = br['half']
    Xg, Yg, Zg = g(bx0, bx1 + 1, YC - bh_, YC + bh_ + 1, ZBR - 1, ZBR + 10)
    plate = (Zg == ZBR) | ((Zg == ZBR - 1) & ((Xg.astype(int) % 8) < 2))
    rimb = (Xg <= bx0) | (Xg >= bx1) | (np.abs(Yg - YC) >= bh_)
    railb = (Zg > ZBR) & (Zg <= ZBR + 9) & rimb & (((Xg.astype(int) + Yg.astype(int)) % 8 == 0) | (Zg == ZBR + 9))
    railb &= ~((np.abs(np.abs(Yg - YC) - 30) <= 4) & (Xg <= bx0 + 1))                # 梯頭那一段不放欄杆
    hb = (lad_mask | hat)[bx0:bx1 + 1, YC - bh_:YC + bh_ + 1, ZBR - 1:ZBR + 10]
    claim('bridge', (bx0, YC - bh_, ZBR - 1), plate & ~hb, np.where(Zg == ZBR, C['teak'], C['beam']))
    claim('bridge', (bx0, YC - bh_, ZBR - 1), railb & ~hb, C['white'])
    cols = [(bx0 + 2, YC - bh_ + 2), (bx0 + 2, YC + bh_ - 2), (bx1 - 2, YC - bh_ + 2), (bx1 - 2, YC + bh_ - 2), (bx0 + 2, YC - 45), (bx0 + 2, YC + 45), (bx1 - 2, YC)]
    for cxx, cyy in cols:
        claim('bridge', (cxx - 1, cyy - 1, WF1), np.ones((3, 3, ZBR - 1 - WF1), bool) & ~lad_mask[cxx - 1:cxx + 2, cyy - 1:cyy + 2, WF1:ZBR - 1], C['white'])
    info['bridge'] = dict(x0=bx0, x1=bx1, half=bh_, z=WB1)
    # ── 煙囪罩（船首樓甲板上；兩舷各一扇門、頂上讓煙囪穿過）──
    cs = P['casing']; csx0, csx1 = cs['x']; csh = cs['half']; csz = cs['h']
    Xg, Yg, Zg = g(csx0, csx1 + 1, YC - csh, YC + csh + 1, WF1, WF1 + csz + 1)
    wallc = ((Xg <= csx0 + 1) | (Xg >= csx1 - 1) | (np.abs(Yg - YC) >= csh - 1)) & (Zg < WF1 + csz)
    doorcs = (np.abs(Yg - YC) >= csh - 1) & (np.abs(Xg - (csx0 + 10)) <= 3) & (Zg < WF1 + 19)
    roofcs = (Zg == WF1 + csz)
    hc = holes[csx0:csx1 + 1, YC - csh:YC + csh + 1, WF1:WF1 + csz + 1]
    claim('superstructure', (csx0, YC - csh, WF1), (wallc & ~doorcs | roofcs) & ~hc, C['white'])
    # ── 船首樓的後壁（白、兩扇門）──
    xw = XB
    Xg, Yg, Zg = g(xw, xw + 2, 0, NY, WU1, ZFC)
    wl = np.broadcast_to(inner2[xw:xw + 2, :, WU1:ZFC], (2, NY, ZFC - WU1)).copy()
    for dy_ in (-12, 12): wl &= ~((np.abs(Yg - (YC + dy_)) <= 4) & (Zg < WU1 + 20))
    wl &= ~lad_mask[xw:xw + 2, :, WU1:ZFC]
    claim('superstructure', (xw, 0, WU1), wl, C['white'])
    # ── 通風筒（喇叭口：管子從船首樓甲板起、頂上一個朝前的喇叭口；外白、口裡紅）──
    for vx, vdy in P['vents']:
        vy = YC + vdy
        Xg, Yg, Zg = g(vx - 10, vx + 11, vy - 8, vy + 9, WF1, WF1 + 44)
        rr = np.hypot(Xg - vx, Yg - vy)
        pipe = (rr <= 3.5) & (Zg < WF1 + 32)                                  # 實心（空心管會封成空腔）
        hz = WF1 + 35
        rh = np.sqrt((Xg - vx - 2) ** 2 + (Yg - vy) ** 2 + ((Zg - hz) * 1.2) ** 2)
        recess = (Xg > vx + 1) & (np.hypot(Yg - vy, Zg - hz) <= 4.2)          # 喇叭口：往前開的凹
        head = (rh <= 5.8) & ~recess & (Zg >= WF1 + 29)
        mouth = (rh <= 5.8) & (Xg > vx) & (Xg <= vx + 1) & (np.hypot(Yg - vy, Zg - hz) <= 4.2)
        claim('vents', (vx - 10, vy - 8, WF1), mouth, C['red'])
        claim('vents', (vx - 10, vy - 8, WF1), pipe | head, C['white'])
    # ── 甲板 ──
    inner = info['inner']

    def deck_layers(nm, ztop, x0, x1, top_c, under_c, beam_depth=3, pitch=12, plate_layers=2):
        Xg = np.arange(NX)[:, None, None]; Zg = np.arange(NZ)[None, None, :]
        xr = (Xg >= x0) & (Xg <= x1)
        inn = np.zeros((NX, NY, NZ), bool); inn[:, :, :ZTF + 1] = inner
        bad = hat | holes | lad_mask
        top = inn & xr & (Zg == ztop) & ~bad
        claimw(nm, top, top_c)
        if plate_layers > 1: claimw(nm, inn & xr & (Zg < ztop) & (Zg >= ztop - plate_layers + 1) & ~bad, under_c)
        beams = inn & xr & (Zg < ztop - plate_layers + 1) & (Zg >= ztop - plate_layers + 1 - beam_depth) & ((Xg % pitch) < 2) & ~bad
        claimw(nm, beams, C['beam'])
        return top
    deck_layers('deck-lower', ZLD, 0, NX - 1, C['iron'], C['iron'], plate_layers=2)
    deck_layers('deck-middle', ZMD, 0, NX - 1, C['teak'], C['beam'])
    deck_layers('deck-upper', ZUD, 0, NX - 1, C['teak'], C['beam'])
    deck_layers('deck-fc', ZFC, XB, NX - 1, C['teak'], C['beam'])
    # ── 欄杆（船首樓甲板邊、後甲板邊；舷頂那一圈外板裡面一格）：柱每 12 格、頂上一條 ──
    rail = np.zeros((NX, NY, NZ), bool)
    rh_ = P['rails']['h']; rp = P['rails']['pitch']
    xm = np.arange(NX)[:, None]; ym = np.arange(NY)[None, :]
    gap = np.zeros((NX, NY), bool)                                         # 梯頭、突出砲台不放
    for L in ladders:
        hx, hy, hz = L['head']; fx_, fy_, fz_ = L['foot']
        gap |= (np.abs(xm - hx) <= 8) & (np.abs(ym - hy) <= 6)
        gap |= (np.abs(xm - fx_) <= 8) & (np.abs(ym - fy_) <= 6)
    for (sx_, cy, sg) in sp_cent: gap |= np.hypot(xm - sx_, ym - cy) <= spr + 3
    for zt_, x0_, x1_ in ((ZTF, XB, NX - 1), (ZTA, 0, XB - 1)):
        e2 = inner[:, :, zt_] & ~ndimage.binary_erosion(inner[:, :, zt_], structure=np.ones((3, 3), bool))
        e2 &= (xm >= x0_) & (xm <= x1_) & ~gap
        if zt_ == ZTF: e2 |= (xm >= XB) & (xm <= XB + 1) & inner[:, :, zt_] & ~gap   # 船首樓後緣（往後甲板那一邊）
        postm = e2 & ((xm % rp) == 0)
        for zz_ in range(zt_, zt_ + rh_ - 1): rail[:, :, zz_] |= postm      # 柱從走路格起（立在甲板上）
        rail[:, :, zt_ + rh_ - 1] |= e2
    rail &= ~lad_mask
    rl, rn = ndimage.label(rail)
    has_post = np.zeros(rn + 1, bool)
    for zt_ in (ZTF, ZTA): has_post[np.unique(rl[:, :, zt_][rail[:, :, zt_]])] = True   # 走路格那一層有格 ⇒ 有柱
    has_post[0] = False
    claimw('rails', has_post[rl], C['white'])
    # ── 艇架（船首樓甲板上：cutter 兩艘、whaleboat 兩艘的墊木）──
    for key in ('boats', 'whaleboats'):
        bt_ = P[key]
        for sx_ in (bt_['x'] + 15, bt_['x'] + 60):
            for sg in (1, -1):
                Xg, Yg, Zg = g(sx_ - 1, sx_ + 2, YC + sg * bt_['dy'] - 10, YC + sg * bt_['dy'] + 11, WF1, bt_['z'])
                chock = (np.abs(Yg - (YC + sg * bt_['dy'])) >= 4 + (Zg - WF1) * 0.5) & (np.abs(Yg - (YC + sg * bt_['dy'])) <= 9)
                claim('skids', (sx_ - 1, YC + sg * bt_['dy'] - 10, WF1), chock & ~lad_mask[sx_ - 1:sx_ + 2, YC + sg * bt_['dy'] - 10:YC + sg * bt_['dy'] + 11, WF1:bt_['z']], C['beam'])
    # ── 彈藥庫（艙底：銅皮地板＋鉛灰牆、一扇門）──
    mags, spots = {}, {}
    zf = 8
    for mg in P['magazines']:
        x0_, x1_ = mg['x']; dy_ = mg['dy']
        rn = 'mag-' + mg['name']; y0_, y1_ = YC - dy_, YC + dy_
        Xg, Yg, Zg = g(x0_, x1_ + 1, y0_, y1_ + 1, zf - 2, ZLD - 3)
        inn_ = inner[x0_:x1_ + 1, y0_:y1_ + 1, zf - 2:ZLD - 3]
        floor_ = (Zg <= zf) & inn_
        wall_ = ((Xg == x0_) | (Xg == x1_) | (Yg == y0_) | (Yg == y1_)) & (Zg > zf) & inn_
        door_ = (Xg == x1_) & (np.abs(Yg - YC) <= 3) & (Zg > zf) & (Zg <= zf + 20)
        lm = lad_mask[x0_:x1_ + 1, y0_:y1_ + 1, zf - 2:ZLD - 3]
        claim(rn, (x0_, y0_, zf - 2), floor_ & ~lm, C['bronze'])
        claim(rn, (x0_, y0_, zf - 2), wall_ & ~door_ & ~lm, C['grey'])
        mags[rn] = {'blast': [(x0_ + x1_) // 2, YC, zf + 8], 'door': [x1_ + 1, YC, zf + 1]}
        spots[rn] = [[xx_ + 0.5, yy_ + 0.5, zf + 1] for xx_ in range(x0_ + 3, x1_ - 7, 6) for yy_ in range(y0_ + 3, y1_ - 3, 6)
                     if inner[xx_ - 3:xx_ + 4, yy_ - 3:yy_ + 4, zf + 1:zf + 7].all()]
    # ── 機艙與鍋爐艙的地板（鐵板 z 3–4）＋水密艙壁（每道中間一扇門 ⇒ 艙底連成一片、不封死）──
    br0, br1 = P['engine_room'][0], P['boiler_room'][1]
    Xg = np.arange(NX)[:, None, None]; Zg = np.arange(NZ)[None, None, :]
    inn = np.zeros((NX, NY, NZ), bool); inn[:, :, :ZTF + 1] = inner
    fl = inn & (Xg >= br0) & (Xg <= br1) & (Zg <= 4) & ~lad_mask
    claimw('floor', fl, C['iron'])
    bulk = np.zeros((NX, NY, NZ), bool)
    zz1 = np.arange(NZ)[None, :]; yy1 = np.arange(NY)[:, None]
    for xb_ in (180, 270, br0, P['engine_room'][1], br1, 760, 890):
        w_ = inn[xb_] & (zz1 < ZLD - 3)
        zb0 = int(np.nonzero(inn[xb_, YC])[0].min())
        zb0 = max(zb0, 5 if br0 <= xb_ <= br1 else zb0)
        w_ &= ~((np.abs(yy1 - YC) <= 3) & (zz1 >= zb0) & (zz1 <= zb0 + 19))
        w_ &= ~((np.abs(np.abs(yy1 - YC) - 45) <= 3) & (zz1 >= zb0 + 5) & (zz1 <= zb0 + 24))
        bulk[xb_] = w_
    claimw('bulkheads', bulk & ~lad_mask, C['iron'])
    # ── 梯子（最後落：踏板與側板；穿過的艙口已經空出來）──
    claimw('ladders', lad_mask, C['iron'])
    info['lad_total'] = int(lad_mask.sum())
    # 封閉空腔（≤ 600 格）填實：歸給旁邊佔最多格的部件（造船規格 §8 最後一條；鏡像部件的鏡過去那一份先算進來）
    full = own > 0
    for nm in MIRR:
        if nm in names: full |= (own == names.index(nm))[:, ::-1, :]
    cav = ndimage.binary_fill_holes(full) & ~full
    clab, cn = ndimage.label(cav)
    filled = []
    for i in range(1, cn + 1):
        w = np.argwhere(clab == i)
        if len(w) > 600: continue
        lo = np.maximum(w.min(0) - 1, 0); hi = w.max(0) + 2
        sub_ = clab[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] == i
        ring_ = ndimage.binary_dilation(sub_) & ~sub_
        nb = own[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]][ring_]
        nb = nb[(nb > 0)]
        nb = nb[~np.isin(nb, [names.index(m) for m in MIRR if m in names])]
        if not len(nb): continue
        k_ = int(np.bincount(nb).argmax())
        cc = np.bincount(col[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]][ring_ & (own[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] == k_)]).argmax()
        claim(names[k_], tuple(int(v) for v in lo), sub_, int(cc))
        filled.append([names[k_], int(len(w)), w[0].tolist()])
    info['filled'] = filled
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
            f.write('# 松島號 %s —— x,y,z,color（框 %d×%d×%d、關聯 at 0,0,0）\n' % (nm, NX, NY, NZ))
            f.write('\n'.join('%d,%d,%d,%d' % (a, b, c, k) for (a, b, c), k in zip(idx.tolist(), cs.tolist())))
            f.write('\n')
        counts[nm] = len(idx)
    np.save(os.path.join(out, 'own.npy'), own)
    json.dump({'names': names[1:]}, open(os.path.join(out, 'own_names.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    full = own > 0
    for nm in MIRR:
        if nm in names: full |= (own == names.index(nm))[:, ::-1, :]
    lab, n = ndimage.label(full)
    sizes = np.bincount(lab.ravel())[1:]
    small = []
    if n > 1:
        for i in np.argsort(sizes)[:-1][:12]:
            w = np.argwhere(lab == i + 1)[0].tolist()
            small.append([int(sizes[i]), w, names[own[tuple(w)]] if own[tuple(w)] else 'mirror'])
    cav = ndimage.binary_fill_holes(full) & ~full
    clab, cn = ndimage.label(cav)
    csz = np.bincount(clab.ravel())[1:]
    cav_list = []
    for i in np.argsort(csz)[::-1][:8]:
        w = np.argwhere(clab == i + 1)[0].tolist(); cav_list.append([int(csz[i]), w])
    mirror_hit = {}
    for nm in MIRR:
        if nm in names:
            i = names.index(nm)
            mm = (own == i)[:, ::-1, :]
            mirror_hit[nm] = int((mm & (own > 0) & (own != i)).sum())
    mirror_diff = {}
    for i, nm in enumerate(names):
        if not nm or nm in MIRR or nm in ('screw-s', 'screw-p', 'ladders'): continue
        m = own == i
        mirror_diff[nm] = int((m != m[:, ::-1, :]).sum())
    env = info['env']
    vol = int(env[:, :, :ZW + 1].sum())
    meta = dict(names=names[1:], counts=counts, mirror_hit=mirror_hit, ladder_cells=[int(info['lad_total']), counts.get('ladders', 0)], total=int(full.sum()), components=int(n), small=small, cavities=int(cn), cavity_top=cav_list,
                mirror_diff=mirror_diff, disp_t=round(vol * 0.001 * 1.025, 1), anchors=anc, spots=info['spots'], mast=info['mast'],
                bridge=info['bridge'], rudder_hinge=info['rudder_hinge'], sponsons=info['sponsons'], filled=info['filled'],
                plan={'z_waterline': ZW, 'walk': {'hold': 5, 'lower': ZLD + 1, 'middle': ZMD + 1, 'upper': ZUD + 1, 'fc': ZFC + 1, 'bridge': ZBR + 1}, 'YC': YC})
    json.dump(meta, open(os.path.join(out, 'matsushima_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: meta[k] for k in ('filled', 'counts', 'mirror_hit', 'ladder_cells', 'total', 'components', 'small', 'cavities', 'cavity_top', 'mirror_diff', 'disp_t')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
