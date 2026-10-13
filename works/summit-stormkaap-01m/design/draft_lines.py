# 風暴角號 新圖紙 01 線形圖（TASK-0547 階段一）：plan.json 的 frame＋lines ⇒ 船殼曲面、線形圖、殼的預覽格、verify_lines.json。
# 用法：python -I -X utf8 -B draft_lines.py <design 資料夾>
#   · 從夜隼號 draft_lines.py（TASK-0529）改來：框的大小與中線改讀 plan.frame；上層從「一段後甲板」改成好幾層（tiers）；
#     tumblehome 加冪次 p 與下限（高船尾那幾層不會收到變負）；殼的預覽改用 EDT（框大了，球形侵蝕太慢）。
#   · 沒有描任何一張圖：曲面全是參數 —— 半寬 hb(x, z) ＝ 船中剖面 hb_mid(z) × 沿船長的豐滿度 f(ξ)；
#     ξ ＝ 離最大寬那一站的距離 ÷ 到那一層端點（艏柱 rabbet／艉柱 rabbet／艉板外的虛擬端點）的距離，f ＝ (1 − ξ^a)^b，a、b 從底到頂漸變。
#   · 龍骨、艏柱、艉柱：半寬 keel.half —— 在 hb 小於它的地方取它。
#   · 方艉（spiegel）：z ≥ transom.z 那幾層在艉板面 x_tr(z) 截斷；艉板寬由 virtual_extension 控制。
#   · 格 k 的格心 k+0.5；在不在船殼內 ＝ |y − YC| ≤ hb(x+0.5, z+0.5) 且 z+0.5 ≤ 舷牆頂 top(x)。
#   · 上層（upper）：舷弧 ＝ 主甲板（上甲板）在船邊的高度；每一層 tier 在 x_break 那一側整段抬 rise（疊在它下面那一層上）；
#     舷牆頂 ＝ 甲板邊 ＋ 那一層的舷牆，在斷口往船中 drift 格內 smoothstep 降回下一層。
#   · 重跑逐位元組相同（PIL 寫 PNG 不帶時間；json 排序鍵）。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

FONT = r"C:\Windows\Fonts\msjh.ttc"


def frame(plan):
    f = plan['frame']
    return f['NX'], f['NY'], f['NZ_hull'], f['YC']


class Hull:
    def __init__(s, plan):
        L = plan['lines']
        s.L = L
        s.NX, s.NY, s.NZ, s.YC = frame(plan)
        k, sp, st, sh, ms, tr = L['keel'], L['sternpost'], L['stem'], L['sheer'], L['midship'], L['transom']
        s.half = k['half']; s.rab = k['rabbet_z']; s.kx0 = k['x_aft']; s.kx1 = k['x_fwd']
        s.sp_x0, s.sp_rake, s.sp_h, s.sp_sid = sp['x_at_keel'], sp['rake'], sp['rake_height'], sp['siding']
        s.st_x0, s.st_rx, s.st_rz, s.st_sid = st['x_at_keel'], st['rx'], st['rz'], st['siding']
        s.sh = sh
        s.dwl = L['dwl']
        s.xm = ms['x']; s.B = ms['half_beam']; s.zmb = ms['z_max_beam']
        s.t = math.tan(math.radians(ms['deadrise_deg'])); s.R = ms['bilge_radius']
        s.th, s.thh, s.thp, s.thmin = ms['tumblehome'], ms['tumblehome_height'], ms.get('tumblehome_power', 2.0), ms.get('min_half_frac', 0.4)
        s.yc = s.B - s.R
        s.zc = s.rab + (s.yc - s.half) * s.t + s.R * math.sqrt(1 + s.t * s.t)
        s.z_floor_tan = s.zc - s.R / math.sqrt(1 + s.t * s.t)
        s.trz, s.trk, s.trV = tr['z'], tr['rake'], tr['virtual_extension']
        s.trBlend = tr.get('blend_height', s.sh['z_aft'] - tr['z'])   # 方艉那幾層的後端點從艉柱漸變到虛擬點要多高（夜隼號＝舷弧船尾高 − 翼艉板）
        s.fu = L['fullness']
        s.up = L.get('upper')

    # ── 剖面與輪廓 ──
    def hb_mid(s, z):
        z = np.asarray(z, float)
        out = np.full(z.shape, np.nan)
        out = np.where(z < s.rab, s.half, out)
        m = (z >= s.rab) & (z <= s.z_floor_tan)
        out = np.where(m, s.half + (z - s.rab) / s.t, out)
        m = (z > s.z_floor_tan) & (z <= s.zc)
        out = np.where(m, s.yc + np.sqrt(np.clip(s.R * s.R - (s.zc - z) ** 2, 0, None)), out)
        m = (z > s.zc) & (z <= s.zmb)
        out = np.where(m, s.B, out)
        m = z > s.zmb
        th = s.B - s.th * (np.clip(z - s.zmb, 0, None) / s.thh) ** s.thp
        out = np.where(m, np.maximum(th, s.B * s.thmin), out)
        return out

    def sheer(s, x):
        x = np.asarray(x, float); h = s.sh
        aft = h['z_low'] + (h['z_aft'] - h['z_low']) * ((h['x_low'] - x) / (h['x_low'] - h['x_aft'])) ** 2
        fwd = h['z_low'] + (h['z_fwd'] - h['z_low']) * ((x - h['x_low']) / (h['x_fwd'] - h['x_low'])) ** 2
        return np.where(x <= h['x_low'], aft, fwd)

    def tiers(s):
        return (s.up or {}).get('tiers', [])

    def covers(s, t, x):
        x = np.asarray(x, float)
        return x <= t['x_break'] if t['end'] == 'aft' else x >= t['x_break']

    def deck_side(s, x):
        """甲板在船邊的高度：上甲板 ＝ 舷弧；每一層 tier 在它那一段再抬 rise（斷口是直的一階）。"""
        x = np.asarray(x, float); z = s.sheer(x)
        for t in s.tiers(): z = z + np.where(s.covers(t, x), t['rise'], 0)
        return z

    def top(s, x):
        """船殼側面到哪 ＝ 舷牆頂：上甲板舷牆 ＋ 每一層在斷口往船中 drift 格內 smoothstep 降回下一層。"""
        x = np.asarray(x, float)
        if not s.up: return s.sheer(x)
        z = s.sheer(x) + s.up['bulwark']
        base = {'aft': s.up['bulwark'], 'fore': s.up['bulwark']}   # 下一層（含它的抬高）的舷牆頂，離舷弧多高
        cum = {'aft': 0.0, 'fore': 0.0}
        for t in s.tiers():
            e = t['end']; cum[e] += t['rise']
            hi = cum[e] + t['bulwark'] - base[e]
            tt = np.clip(((x - t['x_break']) if e == 'aft' else (t['x_break'] - x)) / t['drift'], 0, 1)
            z = z + hi * (1 - tt * tt * (3 - 2 * tt))
            base[e] = cum[e] + t['bulwark']
        return z

    def stern_top(s):
        """船尾最高點（艉板面與船殼頂的交點）：(x, z)。"""
        x = float(s.transom_face(s.sh['z_aft']))
        for _ in range(80): x = float(s.transom_face(float(s.top(x))))
        return x, float(s.top(x))

    def stem_face(s, z):
        z = np.asarray(z, float)
        q = np.clip((s.st_rz - z) / s.st_rz, 0, 1)
        return s.st_x0 + s.st_rx * np.sqrt(1 - q * q)

    def post_face(s, z):
        return s.sp_x0 - s.sp_rake * np.asarray(z, float) / s.sp_h

    def transom_face(s, z):
        return s.post_face(s.trz) - (np.asarray(z, float) - s.trz) * s.trk

    def aft_limit(s, z):
        z = np.asarray(z, float)
        return np.where(z >= s.trz, s.transom_face(z), s.post_face(z))

    def ends(s, z):
        """豐滿度用的兩個端點（rabbet；方艉那幾層的後端從艉柱 rabbet smoothstep 漸變到艉板外的虛擬點 —— 夜隼號 v1 的台階教訓）。"""
        z = np.asarray(z, float)
        xf = s.stem_face(z) - s.st_sid
        xa_post = s.post_face(z) + s.sp_sid
        tt = np.clip((z - s.trz) / max(1e-9, s.trBlend), 0, 1)
        sm = tt * tt * (3 - 2 * tt)
        xa_tr = s.transom_face(s.sh['z_aft']) - s.trV
        xa = np.where(z >= s.trz, xa_post + (xa_tr - xa_post) * sm, xa_post)
        return xf, xa

    def ab(s, z, side):
        top = s.sh['z_low']
        tt = np.clip((np.asarray(z, float) - s.rab) / (top - s.rab), 0, 1)
        f = s.fu[side]
        return f['a_bottom'] + (f['a_top'] - f['a_bottom']) * tt, f['b_bottom'] + (f['b_top'] - f['b_bottom']) * tt

    def hb(s, x, z):
        """半寬；船殼外 ⇒ nan。x、z 可以是同形陣列。"""
        x = np.asarray(x, float); z = np.asarray(z, float)
        x, z = np.broadcast_arrays(x, z)
        xf, xa = s.ends(z)
        af, bf = s.ab(z, 'fore'); aa, ba = s.ab(z, 'aft')
        xi_f = np.clip((x - s.xm) / np.maximum(xf - s.xm, 1e-9), 0, None)
        xi_a = np.clip((s.xm - x) / np.maximum(s.xm - xa, 1e-9), 0, None)
        ff = np.where(xi_f < 1, (1 - np.clip(xi_f, 0, 1) ** af) ** bf, 0.0)
        fa = np.where(xi_a < 1, (1 - np.clip(xi_a, 0, 1) ** aa) ** ba, 0.0)
        f = np.where(x >= s.xm, ff, fa)
        body = s.hb_mid(np.maximum(z, s.rab)) * f
        out = np.maximum(body, s.half)
        inside_x = (x <= s.stem_face(z)) & (x >= s.aft_limit(z))
        ok = inside_x & (z >= 0) & (z <= s.top(x))
        bottom_fore = (x > s.kx1) & (z < s.rab) & (z < s.st_rz - s.st_rz * np.sqrt(np.clip(1 - ((x - s.st_x0) / s.st_rx) ** 2, 0, 1)))
        ok &= ~bottom_fore
        return np.where(ok, out, np.nan)


# ───────────────────────── 讀數 ─────────────────────────
def readings(H):
    d = 0.25
    xs = np.arange(0, H.NX, d) + d / 2
    zs = np.arange(0, H.dwl, d) + d / 2
    X, Z = np.meshgrid(xs, zs, indexing='ij')
    hb = H.hb(X, Z)
    w = np.where(np.isnan(hb), 0, 2 * hb)
    V = float(w.sum() * d * d)
    lcb = float((w.sum(axis=1) * xs).sum() / max(1e-9, w.sum(axis=1).sum()))
    wl = H.hb(xs, np.full(xs.shape, H.dwl))
    wl_ok = ~np.isnan(wl) & (wl > H.half + 1e-6)
    x_lo, x_hi = float(xs[wl_ok].min() - d / 2), float(xs[wl_ok].max() + d / 2)
    LWL = x_hi - x_lo
    BWL = float(2 * np.nanmax(wl))
    T = float(H.dwl)
    Awp = float(np.where(np.isnan(wl), 0, 2 * wl).sum() * d)
    mid = H.hb(np.full(zs.shape, H.xm), zs)
    Am = float(np.where(np.isnan(mid), 0, 2 * mid).sum() * d)
    Cb = V / (LWL * BWL * T); Cm = Am / (BWL * T); Cp = Cb / Cm; Cwp = Awp / (LWL * BWL)
    m3 = V * 0.001
    fair = {}
    for zw in H.L['waterlines'] + [int(H.sh['z_low'])]:
        xx = np.arange(0, H.NX, 1.0)
        h = H.hb(xx, np.full(xx.shape, float(zw)))
        v = h[~np.isnan(h)]
        body = v[v > H.half + 1e-6]
        d1 = np.diff(body)
        sign = np.sign(d1[np.abs(d1) > 1e-9])
        flips = int((np.diff(sign) != 0).sum()) if sign.size > 1 else 0
        d2 = np.abs(np.diff(body, 2)).max() if body.size > 2 else 0.0
        fair[str(zw)] = {'max_hb': round(float(body.max()), 3) if body.size else 0, 'd2_max': round(float(d2), 4), 'monotone_flips': flips}
    # 船中剖面：最大寬、上甲板邊、各層舷牆頂的半寬（tumblehome 的讀數）
    zq = [H.dwl, H.zmb, float(H.sheer(H.xm)), float(H.top(H.xm))]
    x_st, z_st = H.stern_top()
    return {
        'LWL_vox': round(LWL, 2), 'LWL_m': round(LWL * 0.1, 2), 'BWL_m': round(BWL * 0.1, 2), 'T_m': round(T * 0.1, 2),
        'x_lwl': [round(x_lo, 2), round(x_hi, 2)],
        'volume_m3': round(m3, 2), 'displacement_t_seawater': round(m3 * 1.025, 1),
        'LCB_x': round(lcb, 2), 'LCB_pct_from_aft_lwl': round((lcb - x_lo) / LWL * 100, 1),
        'Cb': round(Cb, 3), 'Cm': round(Cm, 3), 'Cp': round(Cp, 3), 'Cwp': round(Cwp, 3),
        'L_over_B': round(LWL / BWL, 2), 'B_over_T': round(BWL / T, 2),
        'fairness': fair,
        'midship_half_breadth_at_z': {str(round(z, 2)): round(float(H.hb_mid(z)), 3) for z in zq},
        'hull_length_m': round((float(H.stem_face(H.st_rz)) - x_st) * 0.1, 2),
        'stern_top_xz': [round(x_st, 2), round(z_st, 2)],
        'stern_top_above_dwl_m': round((z_st - H.dwl) * 0.1, 2),
        'transom_half_width_near_top': round(float(np.nan_to_num(H.hb(x_st + 1.0, z_st - 1.0), nan=-1)), 3),   # 艉板頂往裡、往下各 1 格那一點
    }


# ───────────────────────── 殼的預覽格 ─────────────────────────
def shell_voxels(H, thick):
    NX, NY, NZ = H.NX, H.NY, H.NZ
    x = np.arange(NX) + 0.5; z = np.arange(NZ) + 0.5
    X, Z = np.meshgrid(x, z, indexing='ij')
    hb = H.hb(X, Z)                                       # (NX, NZ)
    dy = np.abs(np.arange(NY) - H.YC).astype(float)
    solid = (~np.isnan(hb))[:, None, :] & (dy[None, :, None] <= np.nan_to_num(hb, nan=-1)[:, None, :])
    # 頂面開口：每一欄最上面那層往上複製 thick+2 層 ⇒ EDT 不把頂面當船外，殼不會長出蓋子
    ext = np.concatenate([solid, np.zeros((NX, NY, thick + 2), bool)], axis=2)
    colany = solid.any(axis=1)                            # (NX, NZ)
    for x_i in range(NX):
        if not colany[x_i].any(): continue
        ztop = np.where(colany[x_i])[0].max()
        for k in range(1, thick + 3): ext[x_i, :, ztop + k] = solid[x_i, :, ztop]
    dist = ndimage.distance_transform_edt(ext)[:, :, :NZ]
    # 甲板分段的斷口：高的那一欄在矮的那一欄頂上複製的 thick+2 層裡，3D 距離把隔壁當成船內 ⇒ 斷口那面牆少一道 6 格高的縫（第一版的預覽看得穿）。
    # 🩸 第二版加「每一層的水平距離」⇒ 舷弧每升一格，那一層就多一道橫跨全寬的牆（預覽變成一條一條的）。
    # ⇒ 第三版：一欄比左右 thick 格內最矮那一欄的頂高出 2 格以上的那一段，整個截面算斷口的牆（舷弧一格只升不到 0.5，碰不到）。
    tv = np.where(colany.any(axis=1), NZ - 1 - np.argmax(colany[:, ::-1], axis=1), -1)          # 每一欄最高的實心格
    low = ndimage.minimum_filter1d(np.where(tv < 0, NZ, tv), size=2 * thick + 1, mode='nearest')
    zz = np.arange(NZ)[None, None, :]
    step = solid & (zz >= low[:, None, None] + 2)
    shell = solid & ((dist <= thick) | step)
    lab, ncomp = ndimage.label(shell)
    holes = int((ndimage.binary_fill_holes(shell) & ~shell).sum())
    mirror_diff = int((shell != shell[:, ::-1, :]).sum()) if NY == 2 * H.YC + 1 else -1
    return solid, shell, {'solid_voxels': int(solid.sum()), 'shell_voxels': int(shell.sum()), 'components': int(ncomp),
                          'enclosed_cavity_voxels': holes, 'mirror_diff': mirror_diff,
                          'bbox': [int(v) for v in np.argwhere(shell).min(0)] + [int(v) for v in np.argwhere(shell).max(0)]}


# ───────────────────────── 畫圖 ─────────────────────────
def font(sz):
    return ImageFont.truetype(FONT, sz)


def profile_points(H, P):
    """側面輪廓（龍骨底 → 艏柱前緣 → 舷牆頂 → 艉板 → 艉柱）。"""
    pts = [P(H.kx0, 0), P(H.kx1, 0)]
    for z in np.linspace(0, H.st_rz, 300):
        pts.append(P(float(H.stem_face(z)), z))
    xs_bow = float(H.stem_face(H.st_rz))
    pts.append(P(xs_bow, float(H.top(xs_bow))))
    x_tr_top = H.stern_top()[0]
    for x in np.linspace(xs_bow, x_tr_top, 600): pts.append(P(x, float(H.top(x))))
    for z in np.linspace(float(H.top(x_tr_top)), H.trz, 30): pts.append(P(float(H.transom_face(z)), z))
    for z in np.linspace(H.trz, 0, 30): pts.append(P(float(H.post_face(z)), z))
    return pts


def draw_sheet(H, R, plan, path):
    S = 2.5
    W, Hh = 1900, 1240
    im = Image.new('RGB', (W, Hh), (250, 248, 242))
    g = ImageDraw.Draw(im)
    ink, blue, grey, red = (30, 30, 30), (30, 90, 200), (170, 170, 170), (190, 40, 40)
    f14, f18, f24 = font(14), font(18), font(24)
    g.text((20, 12), "風暴角號 Stormkaap　新圖紙 01　線形（側面／半寬／橫剖面）　0.1 m／格　summit 2026-10-13　（設計；底本 VOC retourschip，沒有描圖）", fill=ink, font=f24)
    ox = 40
    st = np.linspace(H.kx0, H.kx1, H.L['stations'])
    zmax = float(H.stern_top()[1]) + 6
    # ── 側面 ──
    top = 60; base = top + zmax * S
    def P(x, z): return (ox + x * S, base - z * S)
    g.text((ox, top - 4), "側面（profile）", fill=ink, font=f18)
    for zz in H.L['waterlines']:
        g.line([P(0, zz), P(H.NX, zz)], fill=blue if zz == H.dwl else grey, width=2 if zz == H.dwl else 1)
        g.text(P(2, zz + 4), ("DWL " if zz == H.dwl else "WL ") + str(zz), fill=blue if zz == H.dwl else grey, font=f14)
    for k, x in enumerate(st):
        g.line([P(x, -2), P(x, zmax - 4)], fill=grey, width=1)
        g.text(P(x - 1, -3), str(k), fill=grey, font=f14)
    pts = profile_points(H, P)
    g.line(pts + [pts[0]], fill=ink, width=3)
    g.line([P(H.xm, 0), P(H.xm, H.zmb + 20)], fill=red, width=1)
    g.text(P(H.xm + 1, H.zmb + 24), "最大寬 x " + str(H.xm), fill=red, font=f14)
    g.line([P(H.kx0, H.rab), P(H.kx1, H.rab)], fill=ink, width=1)
    if H.up:
        x0 = float(H.stern_top()[0]); x1 = float(H.stem_face(H.st_rz))
        xd = np.arange(x0, x1, 1.0); zd = H.deck_side(xd)
        keep = xd >= H.transom_face(zd); xd, zd = xd[keep], zd[keep]
        for k in range(0, len(xd) - 1, 4):
            if abs(zd[k + 1] - zd[k]) < 2: g.line([P(xd[k], zd[k]), P(xd[k + 1], zd[k + 1])], fill=(120, 120, 120), width=2)
        for t in H.tiers():
            xb = t['x_break']
            lo = float(H.deck_side(xb + (1 if t['end'] == 'aft' else -1)))
            hi = float(H.deck_side(xb))
            g.line([P(xb, lo), P(xb, hi)], fill=(120, 120, 120), width=2)
            g.text(P(xb + (-60 if t['end'] == 'aft' else 4), hi + 3), t['name'] + "（+" + str(t['rise']) + "）", fill=(120, 120, 120), font=f14)
        g.text(P(H.xm - 40, float(H.sheer(H.xm)) - 6), "虛線 ＝ 甲板邊　實線頂 ＝ 舷牆頂", fill=(120, 120, 120), font=f14)
    # ── 半寬 ──
    top2 = base + 40; cl = top2 + 10
    def Q(x, y): return (ox + x * S, cl + y * S)
    g.text((ox, top2 - 18), "半寬（half-breadth；中線在上）", fill=ink, font=f18)
    g.line([Q(0, 0), Q(H.NX, 0)], fill=ink, width=1)
    for k, x in enumerate(st): g.line([Q(x, 0), Q(x, H.B + 4)], fill=grey, width=1)
    xx = np.arange(0, H.NX, 0.5)
    for zw in H.L['waterlines'] + ['sheer', 'top']:
        if zw == 'top': h = H.hb(xx, H.top(xx) - 1e-6); col = red
        elif zw == 'sheer': h = H.hb(xx, H.sheer(xx) - 1e-6); col = ink
        else: h = H.hb(xx, np.full(xx.shape, float(zw))); col = blue if zw == H.dwl else (120, 120, 120)
        seg = []
        for x, y in zip(xx, h):
            if np.isnan(y):
                if len(seg) > 1: g.line(seg, fill=col, width=2 if zw in ('sheer', 'top', H.dwl) else 1)
                seg = []
            else: seg.append(Q(x, y))
        if len(seg) > 1: g.line(seg, fill=col, width=2 if zw in ('sheer', 'top', H.dwl) else 1)
    g.text(Q(H.NX - 230, H.B + 2), "粗黑 ＝ 舷弧（上甲板邊）　藍 ＝ DWL　紅 ＝ 舷牆頂", fill=ink, font=f14)
    # ── 橫剖面 ──
    S2 = 3.2; cx = 1580; base3 = Hh - 40
    def B(y, z): return (cx + y * S2, base3 - z * S2)
    g.text((cx - 300, base3 - zmax * S2 - 26), "橫剖面（左 ＝ 船尾 0–5 站、右 ＝ 船頭 5–10 站）", fill=ink, font=f18)
    for zz2 in H.L['waterlines']:
        g.line([B(-H.B - 8, zz2), B(H.B + 8, zz2)], fill=blue if zz2 == H.dwl else grey, width=1)
    g.line([B(0, -1), B(0, zmax)], fill=ink, width=1)
    zz = np.arange(0, zmax, 0.25)
    for k, x in enumerate(st):
        sg = -1 if k < 5 else 1
        for side in ([-1, 1] if k == 5 else [sg]):
            h = H.hb(np.full(zz.shape, x), zz)
            seg = []
            for y, z in list(zip(h, zz)) + [(np.nan, 0)]:   # 遇到 nan 就斷線（⛔ 不要把兩段接起來）
                if np.isnan(y):
                    if len(seg) > 1: g.line(seg, fill=red if k == 5 else ink, width=2 if k == 5 else 1)
                    seg = []
                else: seg.append(B(side * y, z))
    g.text(B(-H.B - 8, -6), "站距 " + str(round(st[1] - st[0], 2)) + " 格；紅 ＝ 5 站", fill=ink, font=f14)
    # ── 讀數框 ──
    tx, ty = 40, cl + (H.B + 14) * S
    lines = [
        "讀數（verify_lines.json）",
        "船長（艉板頂 → 艏柱頂）" + str(R['hull_length_m']) + " m　水線長 LWL " + str(R['LWL_m']) + " m　水線寬 BWL " + str(R['BWL_m']) + " m　吃水 T " + str(R['T_m']) + " m",
        "排水體積 " + str(R['volume_m3']) + " m3　排水量（海水）" + str(R['displacement_t_seawater']) + " t",
        "Cb " + str(R['Cb']) + "　Cm " + str(R['Cm']) + "　Cp " + str(R['Cp']) + "　Cwp " + str(R['Cwp']) + "　L/B " + str(R['L_over_B']) + "　B/T " + str(R['B_over_T']),
        "浮心 LCB 在水線長 " + str(R['LCB_pct_from_aft_lwl']) + "%（從船尾量）　船尾頂離水線 " + str(R['stern_top_above_dwl_m']) + " m",
        "船中半寬（z：格）" + "　".join(k + "：" + str(v) for k, v in R['midship_half_breadth_at_z'].items()),
        "殼預覽：" + str(R['shell']['shell_voxels']) + " 格、元件 " + str(R['shell']['components']) + "、封閉空腔 " + str(R['shell']['enclosed_cavity_voxels']) + " 格、左右差 " + str(R['shell']['mirror_diff']),
    ]
    for i, s_ in enumerate(lines): g.text((tx, ty + i * 26), s_, fill=ink, font=f18 if i else f24)
    # 史料對照（plan.reference_dims；只列數字，量的是誰寫在 provenance）
    rd = plan.get('reference_dims', {})
    ty2 = ty + len(lines) * 26 + 14
    if rd:
        g.text((tx, ty2), "底本讀數（史料；出處見 plan.json provenance）", fill=ink, font=f18)
        for i, (k, v) in enumerate(sorted(rd.items())):
            g.text((tx + 10, ty2 + 26 + i * 22), k + "：" + str(v), fill=(90, 90, 90), font=f14)
    im.save(path, optimize=False)


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H = Hull(plan)
    R = readings(H)
    solid, shell, rs = shell_voxels(H, plan['lines']['shell_preview_thickness'])
    R['shell'] = rs
    R['midship_section'] = {'floor_tangent_z': round(H.z_floor_tan, 3), 'bilge_center': [round(H.yc, 3), round(H.zc, 3)],
                            'hb_at_dwl': round(float(H.hb_mid(H.dwl)), 3)}
    os.makedirs(os.path.join(d, 'masks', 'hull'), exist_ok=True)
    with open(os.path.join(d, 'masks', 'hull', 'shell_preview.vox.txt'), 'w', encoding='utf-8', newline='\n') as fo:
        fo.write("# 風暴角號 新圖紙 01 殼的預覽（厚 " + str(plan['lines']['shell_preview_thickness']) + " 格；只給草稿看形狀，⛔ 不是正式落子）\n")
        for x, y, z in np.argwhere(shell): fo.write(f"{x},{y},{z},136\n")
    draw_sheet(H, R, plan, os.path.join(d, 'sheet01_lines_v1.png'))
    with open(os.path.join(d, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
