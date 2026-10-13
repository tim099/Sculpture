# 新圖紙 01 線形圖（TASK-0529 階段一）：plan.json 的 lines 段 ⇒ 船殼曲面、線形圖、定稿圖對照、殼的預覽格、verify_lines.json。
# 用法：python -I -X utf8 draft_lines.py <design 資料夾> [--v1]
#   · 有 lines.upper（階段二：舷牆、後甲板）⇒ 出 *_v2；--v1 ＝ 拿掉 upper、照階段一重產 *_v1（逐位元組相同）。
#   · 沒有史實圖紙：曲面全是參數 —— 半寬 hb(x, z) ＝ 船中剖面 hb_mid(z) × 沿船長的豐滿度 f(ξ)；
#     ξ ＝ 離最大寬那一站的距離 ÷ 到那一層端點（艏柱 rabbet／艉柱 rabbet／艉板外的虛擬端點）的距離，f ＝ (1 − ξ^a)^b，a、b 從底到頂漸變。
#   · 龍骨、艏柱、艉柱：半寬 keel.half（3 格寬）—— 在 hb 小於它的地方取它。
#   · 方艉：z ≥ transom.z 那幾層在艉板面 x_tr(z) 截斷；艉板寬由 virtual_extension 控制（虛擬端點在艉板外多遠）。
#   · 格 k 的格心 k+0.5；在不在船殼內 ＝ |y − 80| ≤ hb(x+0.5, z+0.5) 且 z+0.5 ≤ 船殼頂（v1 ＝ 舷弧；v2 ＝ 舷牆頂）。
#   · v2：舷弧 ＝ 主甲板在船邊的高度；後甲板（x ≤ x_break）高 rise；舷牆頂 ＝ 甲板邊 ＋ 舷牆，在斷口往前 drift 格內降回船腰高度。
#   · 重跑逐位元組相同（PIL 寫 PNG 不帶時間；json 排序鍵）。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

YC = 80
FONT = r"C:\Windows\Fonts\msjh.ttc"


class Hull:
    def __init__(s, plan):
        L = plan['lines']
        s.L = L
        k, sp, st, sh, ms, tr = L['keel'], L['sternpost'], L['stem'], L['sheer'], L['midship'], L['transom']
        s.half = k['half']; s.rab = k['rabbet_z']; s.kx0 = k['x_aft']; s.kx1 = k['x_fwd']
        s.sp_x0, s.sp_rake, s.sp_h, s.sp_sid = sp['x_at_keel'], sp['rake'], sp['rake_height'], sp['siding']
        s.st_x0, s.st_rx, s.st_rz, s.st_sid = st['x_at_keel'], st['rx'], st['rz'], st['siding']
        s.sh = sh
        s.dwl = L['dwl']
        s.xm = ms['x']; s.B = ms['half_beam']; s.zmb = ms['z_max_beam']
        s.t = math.tan(math.radians(ms['deadrise_deg'])); s.R = ms['bilge_radius']
        s.th, s.thh = ms['tumblehome'], ms['tumblehome_height']
        s.yc = s.B - s.R
        s.zc = s.rab + (s.yc - s.half) * s.t + s.R * math.sqrt(1 + s.t * s.t)
        s.z_floor_tan = s.zc - s.R / math.sqrt(1 + s.t * s.t)
        s.trz, s.trk, s.trV = tr['z'], tr['rake'], tr['virtual_extension']
        s.fu = L['fullness']
        s.legacy_transom = False
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
        out = np.where(m, s.B - s.th * ((z - s.zmb) / s.thh) ** 2, out)
        return out

    def sheer(s, x):
        x = np.asarray(x, float); h = s.sh
        aft = h['z_low'] + (h['z_aft'] - h['z_low']) * ((h['x_low'] - x) / (h['x_low'] - h['x_aft'])) ** 2
        fwd = h['z_low'] + (h['z_fwd'] - h['z_low']) * ((x - h['x_low']) / (h['x_fwd'] - h['x_low'])) ** 2
        return np.where(x <= h['x_low'], aft, fwd)

    def deck_side(s, x):
        """甲板在船邊的高度：主甲板 ＝ 舷弧；後甲板那一段加 rise（斷口是直的一階）。"""
        x = np.asarray(x, float); z = s.sheer(x)
        if not s.up: return z
        q = s.up['quarterdeck']
        return np.where(x <= q['x_break'], z + q['rise'], z)

    def top(s, x):
        """船殼側面到哪：v1 ＝ 舷弧；v2 ＝ 舷牆頂（後甲板舷牆在斷口往前 drift 格內 smoothstep 降回船腰）。"""
        x = np.asarray(x, float)
        if not s.up: return s.sheer(x)
        q = s.up['quarterdeck']
        hi = q['rise'] + q['bulwark'] - s.up['bulwark']
        tt = np.clip((x - q['x_break']) / q['drift'], 0, 1)
        return s.sheer(x) + s.up['bulwark'] + hi * (1 - tt * tt * (3 - 2 * tt))

    def stern_top(s):
        """船尾最高點（艉板面與船殼頂的交點）：(x, z)。"""
        x = float(s.transom_face(s.sh['z_aft']))
        if not s.up: return x, float(s.sh['z_aft'])
        for _ in range(60): x = float(s.transom_face(float(s.top(x))))
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
        """這一層船殼往後到哪（含艉柱本身）：艉板以下 ＝ 艉柱後緣；艉板以上 ＝ 艉板面。"""
        z = np.asarray(z, float)
        return np.where(z >= s.trz, s.transom_face(z), s.post_face(z))

    def ends(s, z):
        """豐滿度用的兩個端點（rabbet；方艉那幾層的後端是艉板外的虛擬點）。"""
        z = np.asarray(z, float)
        xf = s.stem_face(z) - s.st_sid
        xa_post = s.post_face(z) + s.sp_sid
        # 方艉那幾層：後端點從艉柱 rabbet 漸變（smoothstep，值與斜率都連續）到艉板外的虛擬點
        # 🩸 v1 直接切換 ⇒ z 18 那一層豐滿度跳一級，船尾 0、1 站的剖面在翼艉板高度折出台階
        tt = np.clip((z - s.trz) / max(1e-9, s.sh['z_aft'] - s.trz), 0, 1)
        sm = tt * tt * (3 - 2 * tt)
        xa_tr = s.transom_face(s.sh['z_aft']) - s.trV
        xa = np.where(z >= s.trz, xa_post + (xa_tr - xa_post) * sm, xa_post)
        if s.legacy_transom:   # v1（錯的那版）：z 18 直接切換 —— 只給「重產 v1 對照圖」用
            xa_v1 = s.transom_face(z) - s.trV * tt
            xa = np.where(z >= s.trz, np.minimum(xa_post, xa_v1), xa_post)
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
        # 龍骨（z < rabbet）只在龍骨長度內；艏柱／艉柱撐到前緣／後緣
        inside_x = (x <= s.stem_face(z)) & (x >= s.aft_limit(z))
        keel_zone = (z < s.rab) & ((x < s.kx0) | (x > s.kx1)) & (body <= s.half)
        if s.up:   # v2：龍骨兩端外（船頭 forefoot、船尾艉柱根部）是柱子的根，不是船外 —— 前後已經由 stem_face／aft_limit 框住
            # 🩸 v1 把它們排除了：船頭 75 格（階段二疊圖才看到）、船尾 6 格（補了沿柱子的探針才量到）
            keel_zone = np.zeros_like(keel_zone)
        ok = inside_x & (z >= 0) & (z <= s.top(x)) & ~keel_zone
        # 艏柱前、艉柱後那一截在 rabbet 以下只有柱子本身：stem_face／post_face 已經擋住，這裡處理龍骨端點外的底部
        bottom_fore = (x > s.kx1) & (z < s.kx1 * 0 + s.rab) & (z < s.st_rz - s.st_rz * np.sqrt(np.clip(1 - ((x - s.st_x0) / s.st_rx) ** 2, 0, 1)))
        ok &= ~bottom_fore
        return np.where(ok, out, np.nan)


# ───────────────────────── 讀數 ─────────────────────────
def readings(H):
    d = 0.25
    xs = np.arange(0, 384, d) + d / 2
    zs = np.arange(0, H.dwl, d) + d / 2
    X, Z = np.meshgrid(xs, zs, indexing='ij')
    hb = H.hb(X, Z)
    w = np.where(np.isnan(hb), 0, 2 * hb)
    V = float(w.sum() * d * d)                         # 格³
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
    # 平順度：每條水線沿 x（步 1）的二階差分、單峰（一階差分換號次數）
    fair = {}
    for zw in H.L['waterlines'] + [int(H.sh['z_low'])]:
        xx = np.arange(0, 384, 1.0)
        h = H.hb(xx, np.full(xx.shape, float(zw)))
        v = h[~np.isnan(h)]
        body = v[v > H.half + 1e-6]
        d1 = np.diff(body)
        sign = np.sign(d1[np.abs(d1) > 1e-9])
        flips = int((np.diff(sign) != 0).sum()) if sign.size > 1 else 0
        d2 = np.abs(np.diff(body, 2)).max() if body.size > 2 else 0.0
        fair[str(zw)] = {'max_hb': round(float(body.max()), 3) if body.size else 0, 'd2_max': round(float(d2), 4), 'monotone_flips': flips}
    return {
        'LWL_vox': round(LWL, 2), 'LWL_m': round(LWL * 0.1, 2), 'BWL_m': round(BWL * 0.1, 2), 'T_m': round(T * 0.1, 2),
        'x_lwl': [round(x_lo, 2), round(x_hi, 2)],
        'volume_m3': round(m3, 2), 'displacement_t_seawater': round(m3 * 1.025, 1),
        'LCB_x': round(lcb, 2), 'LCB_pct_from_aft_lwl': round((lcb - x_lo) / LWL * 100, 1),
        'Cb': round(Cb, 3), 'Cm': round(Cm, 3), 'Cp': round(Cp, 3), 'Cwp': round(Cwp, 3),
        'L_over_B': round(LWL / BWL, 2), 'B_over_T': round(BWL / T, 2),
        'fairness': fair,
    }


# ───────────────────────── 殼的預覽格 ─────────────────────────
def shell_voxels(H, thick):
    NX, NY, NZ = 384, 161, (56 if not H.up else 72)
    x = np.arange(NX) + 0.5; z = np.arange(NZ) + 0.5
    X, Z = np.meshgrid(x, z, indexing='ij')
    hb = H.hb(X, Z)                                       # (NX, NZ)
    dy = np.abs(np.arange(NY) - YC).astype(float)        # 格心離中線
    solid = (~np.isnan(hb))[:, None, :] & (dy[None, :, None] <= np.nan_to_num(hb, nan=-1)[:, None, :])
    # 頂面開口：往上複製最上面那層再侵蝕 ⇒ 殼不會長出蓋子
    ext = np.concatenate([solid, np.zeros((NX, NY, thick + 2), bool)], axis=2)
    for x_i in range(NX):
        col = solid[x_i]
        if not col.any(): continue
        ztop = np.where(col.any(axis=0))[0].max()
        for k in range(1, thick + 3): ext[x_i, :, ztop + k] = col[:, ztop]
    ball = np.zeros((2 * thick + 1,) * 3, bool)
    c = thick
    for i in range(2 * thick + 1):
        for j in range(2 * thick + 1):
            for k in range(2 * thick + 1):
                if (i - c) ** 2 + (j - c) ** 2 + (k - c) ** 2 <= thick * thick: ball[i, j, k] = True
    inner = ndimage.binary_erosion(ext, structure=ball, border_value=0)[:, :, :NZ]
    shell = solid & ~inner
    lab, ncomp = ndimage.label(shell)
    holes = int((ndimage.binary_fill_holes(shell) & ~shell).sum())
    mirror_diff = int((shell != shell[:, ::-1, :][:, :, :]).sum()) if NY == 2 * YC + 1 else -1
    return solid, shell, {'solid_voxels': int(solid.sum()), 'shell_voxels': int(shell.sum()), 'components': int(ncomp),
                          'enclosed_cavity_voxels': holes, 'mirror_diff_y_vs_160_minus_y': mirror_diff,
                          'bbox': [int(v) for v in np.argwhere(shell).min(0)] + [int(v) for v in np.argwhere(shell).max(0)]}


# ───────────────────────── 畫圖 ─────────────────────────
def font(sz):
    return ImageFont.truetype(FONT, sz)


def draw_sheet(H, R, path):
    S = 4
    W, Hh = 1700, 1010
    im = Image.new('RGB', (W, Hh), (250, 248, 242))
    g = ImageDraw.Draw(im)
    ink, blue, grey, red = (30, 30, 30), (30, 90, 200), (170, 170, 170), (190, 40, 40)
    f14, f18, f24 = font(14), font(18), font(24)
    g.text((20, 12), "夜隼號 Night Falcon　新圖紙 01" + ("" if not H.up else " v2（＋舷牆、後甲板）") + "　線形（側面／半寬／橫剖面）　0.1 m／格　summit 2026-10-13　（設計，沒有史實圖紙）", fill=ink, font=f24)
    ox = 40
    # 站位
    st = np.linspace(H.kx0, H.kx1, H.L['stations'])
    # ── 側面 ──
    top = 60; base = top + 64 * S
    def P(x, z): return (ox + x * S, base - z * S)
    g.text((ox, top - 4), "側面（profile）", fill=ink, font=f18)
    for zz in H.L['waterlines']:
        g.line([P(0, zz), P(384, zz)], fill=blue if zz == H.dwl else grey, width=2 if zz == H.dwl else 1)
        g.text(P(2, zz + 2.5), ("DWL " if zz == H.dwl else "WL ") + str(zz), fill=blue if zz == H.dwl else grey, font=f14)
    for k, x in enumerate(st):
        g.line([P(x, -2), P(x, 62)], fill=grey, width=1)
        g.text(P(x - 1, -2.5), str(k), fill=grey, font=f14)
    # 輪廓：龍骨底 → 艏柱前緣 → 舷弧 → 艉板 → 艉柱
    pts = profile_points(H, P)
    g.line(pts + [pts[0]], fill=ink, width=3)
    g.line([P(H.xm, 0), P(H.xm, 50)], fill=red, width=1)
    g.text(P(H.xm + 1, 52), "最大寬 x " + str(H.xm), fill=red, font=f14)
    g.line([P(H.kx0, H.rab), P(H.kx1, H.rab)], fill=ink, width=1)
    if H.up:
        xd = np.arange(float(H.stern_top()[0]), float(H.stem_face(H.st_rz)), 1.0)
        zd = H.deck_side(xd)
        keep = xd >= H.transom_face(zd); xd, zd = xd[keep], zd[keep]   # 艉板外不畫
        for k in range(0, len(xd) - 1, 4):
            if abs(zd[k + 1] - zd[k]) < 2: g.line([P(xd[k], zd[k]), P(xd[k + 1], zd[k + 1])], fill=(120, 120, 120), width=2)
        qb = H.up['quarterdeck']['x_break']
        g.line([P(qb, float(H.sheer(qb))), P(qb, float(H.deck_side(qb)))], fill=(120, 120, 120), width=2)
        g.text(P(qb - 40, float(H.deck_side(qb)) - 2), "後甲板（+" + str(H.up['quarterdeck']['rise']) + "）", fill=(120, 120, 120), font=f14)
        g.text(P(qb + 6, float(H.sheer(qb)) - 1), "虛線 ＝ 甲板邊　實線頂 ＝ 舷牆頂", fill=(120, 120, 120), font=f14)
    # ── 半寬 ──
    top2 = base + 50; cl = top2 + 10
    def Q(x, y): return (ox + x * S, cl + y * S)
    g.text((ox, top2 - 18), "半寬（half-breadth；中線在上）", fill=ink, font=f18)
    g.line([Q(0, 0), Q(384, 0)], fill=ink, width=1)
    for k, x in enumerate(st): g.line([Q(x, 0), Q(x, 36)], fill=grey, width=1)
    xx = np.arange(0, 384, 0.5)
    for zw in H.L['waterlines'] + ['sheer'] + (['top'] if H.up else []):
        if zw == 'top': h = H.hb(xx, H.top(xx) - 1e-6); col = (190, 40, 40)
        elif zw == 'sheer': h = H.hb(xx, H.sheer(xx) - 1e-6); col = ink
        else: h = H.hb(xx, np.full(xx.shape, float(zw))); col = blue if zw == H.dwl else (120, 120, 120)
        seg = []
        for x, y in zip(xx, h):
            if np.isnan(y):
                if len(seg) > 1: g.line(seg, fill=col, width=2 if zw in ('sheer', 'top', H.dwl) else 1)
                seg = []
            else: seg.append(Q(x, y))
        if len(seg) > 1: g.line(seg, fill=col, width=2 if zw in ('sheer', 'top', H.dwl) else 1)
    g.text(Q(300, 34), "粗黑 ＝ 舷弧（甲板邊）　藍 ＝ DWL" + ("　紅 ＝ 舷牆頂" if H.up else ""), fill=ink, font=f14)
    # ── 橫剖面 ──
    S2 = 6; cx = 1180; base3 = 960
    def B(y, z): return (cx + y * S2, base3 - z * S2)
    g.text((cx - 260, base3 - 60 * S2 - 30), "橫剖面（body plan；左 ＝ 船尾 0–5 站、右 ＝ 船頭 5–10 站）", fill=ink, font=f18)
    for zz2 in H.L['waterlines']:
        g.line([B(-40, zz2), B(40, zz2)], fill=blue if zz2 == H.dwl else grey, width=1)
    g.line([B(0, -1), B(0, 58)], fill=ink, width=1)
    zz = np.arange(0, 56 if not H.up else 72, 0.25)
    for k, x in enumerate(st):
        sg = -1 if k < 5 else 1
        for side in ([-1, 1] if k == 5 else [sg]):
            h = H.hb(np.full(zz.shape, x), zz)
            seg = [B(side * y, z) for y, z in zip(h, zz) if not np.isnan(y)]
            if len(seg) > 1: g.line(seg, fill=red if k == 5 else ink, width=2 if k == 5 else 1)
    g.text(B(-40, -4), "站距 " + str(round(st[1] - st[0], 2)) + " 格；紅 ＝ 5 站（船中附近）", fill=ink, font=f14)
    # ── 讀數框 ──
    tx, ty = 40, 620
    lines = [
        "讀數（verify_lines.json）",
        "水線長 LWL " + str(R['LWL_m']) + " m　水線寬 BWL " + str(R['BWL_m']) + " m　吃水 T " + str(R['T_m']) + " m",
        "排水體積 " + str(R['volume_m3']) + " m3　排水量（海水）" + str(R['displacement_t_seawater']) + " t",
        "Cb " + str(R['Cb']) + "　Cm " + str(R['Cm']) + "　Cp " + str(R['Cp']) + "　Cwp " + str(R['Cwp']),
        "L/B " + str(R['L_over_B']) + "　B/T " + str(R['B_over_T']) + "　浮心 LCB 在水線長 " + str(R['LCB_pct_from_aft_lwl']) + "%（從船尾量）",
        "殼預覽：" + str(R['shell']['shell_voxels']) + " 格、元件 " + str(R['shell']['components']) + "、封閉空腔 " + str(R['shell']['enclosed_cavity_voxels']) + " 格、左右差 " + str(R['shell']['mirror_diff_y_vs_160_minus_y']),
    ]
    if H.up:
        u = R['upper']
        lines.append("舷牆頂 ÷ 船長：船腰 " + str(u['waist_rail_over_length']) + "　後甲板 " + str(u['qd_rail_over_length']) + "（定稿圖目測 " + str(u['concept']['waist_rail_over_length']) + "／" + str(u['concept']['qd_rail_over_length']) + "）")
    for i, s_ in enumerate(lines): g.text((tx, ty + i * 26), s_, fill=ink, font=f18 if i else f24)
    im.save(path, optimize=False)


def profile_points(H, P):
    """側面輪廓（龍骨底 → 艏柱前緣 → 舷弧 → 艉板 → 艉柱）—— 圖紙與對照圖共用。"""
    pts = [P(H.kx0, 0), P(H.kx1, 0)]
    zmax = 60 if not H.up else 72
    for z in np.linspace(0, zmax, 240 if not H.up else 288):
        xs = float(H.stem_face(z))
        if z > H.top(xs): break
        pts.append(P(xs, z))
    if H.up: pts.append(P(float(H.stem_face(H.st_rz)), float(H.top(H.stem_face(H.st_rz)))))
    xs_bow = float(H.stem_face(min(H.st_rz, float(H.top(H.stem_face(H.st_rz))))))
    x_tr_top = H.stern_top()[0]
    for x in np.linspace(xs_bow, x_tr_top, 200 if not H.up else 400): pts.append(P(x, float(H.top(x))))
    for z in np.linspace(float(H.top(x_tr_top)), H.trz, 20): pts.append(P(float(H.transom_face(z)), z))
    for z in np.linspace(H.trz, 0, 20): pts.append(P(float(H.post_face(z)), z))
    return pts


def draw_compare(H, concept, path):
    """定稿圖（看的）左下那艘（船頭朝右）與新圖紙側面並排 —— 船長目測對齊、龍骨底同一條線；只並排、不疊（AI 生的概念圖不是量的）。"""
    src = Image.open(concept).convert('RGB')
    crop = src.crop((20, 640, 600, 1170))   # 右緣 600：再往右會裁到定稿圖右下那艘的船尾
    KEEL_Y, HULL_PX = 497, 491          # 像素量（2026-10-13）：龍骨底 y 497（x 94..414 逐欄最低深色像素都是 497）；船長 ＝ 艉廊外緣 x≈54 → 艏柱頂 x≈545（兩端目測 ±10）。🩸 第一版目測 545／440 ⇒ 龍骨差 48 px
    x_st = H.stern_top()[0]
    S = HULL_PX / (float(H.stem_face(H.st_rz)) - x_st)
    im = Image.new('RGB', (crop.width * 2 + 60, crop.height + 110), (250, 248, 242))
    g = ImageDraw.Draw(im)
    g.text((10, 8), "左：定稿圖 night_falcon_v1.png 左下（看的，不是量的）　右：新圖紙 01 側面（船長照像素量對齊，兩端 ±10 px；龍骨底同高）", fill=(30, 30, 30), font=font(18))
    im.paste(crop, (10, 50))
    ox, base = crop.width + 40 - x_st * S + 60, 50 + KEEL_Y
    def P(x, z): return (ox + x * S, base - z * S)
    g.line(profile_points(H, P), fill=(30, 30, 30), width=2)
    xx = np.linspace(x_st, float(H.stem_face(H.st_rz)), 120)
    if not H.up:
        for k in range(0, len(xx) - 1, 2): g.line([P(xx[k], float(H.sheer(xx[k])) + 10), P(xx[k + 1], float(H.sheer(xx[k + 1])) + 10)], fill=(150, 150, 150), width=2)
    else:
        zd = H.deck_side(xx)
        xx = xx[xx >= H.transom_face(zd)]; zd = H.deck_side(xx)
        for k in range(0, len(xx) - 1, 2):
            if abs(zd[k + 1] - zd[k]) < 2: g.line([P(xx[k], zd[k]), P(xx[k + 1], zd[k + 1])], fill=(150, 150, 150), width=2)
        # 定稿圖目測的高度（2 倍放大圖讀的，±4 px）畫成短橫線
        for name, ypx, x0, x1 in CONCEPT_MARKS:
            g.line([(10 + x0, 50 + ypx), (10 + x1, 50 + ypx)], fill=(200, 60, 60), width=2)
    g.line([P(xx[0] - 10, H.dwl), P(xx[-1] + 10, H.dwl)], fill=(30, 90, 200), width=1)
    g.text(P(xx[0], float(H.sheer(xx[0])) + 14) if not H.up else P(xx[0], float(H.top(xx[0])) + 12),
           "虛線 ＝ 舷牆示意（+1 m，未設計）" if not H.up else "虛線 ＝ 甲板邊；左圖紅短線 ＝ 定稿圖目測的舷牆頂", fill=(120, 120, 120), font=font(14))
    g.text(P(xx[0], H.dwl - 6), "DWL", fill=(30, 90, 200), font=font(14))
    g.line([(10, base), (im.width - 10, base)], fill=(200, 120, 120), width=1)
    g.text((12, base + 6), "龍骨底（兩邊同一條線）", fill=(200, 120, 120), font=font(14))
    im.save(path, optimize=False)


# 定稿圖（裁切座標）目測的高度：2 倍放大圖讀的，±4 px（2026-10-13 階段二）。(名字, y, x0, x1)
CONCEPT_MARKS = [('qd_rail', 356, 54, 260), ('waist_rail', 398, 260, 385), ('waist_bulwark', 407, 260, 385)]


def upper_readings(H):
    """v2：舷牆頂高 ÷ 船長（船長 ＝ 船尾最高點 → 艏柱頂，跟定稿圖的量法同）。"""
    x_st, z_st = H.stern_top()
    Lh = float(H.stem_face(H.st_rz)) - x_st
    q = H.up['quarterdeck']
    x_w = float(H.xm); x_q = (x_st + q['x_break']) / 2
    KEEL_Y, HULL_PX = 497, 491
    c = {k: round((KEEL_Y - y) / HULL_PX, 3) for k, y, _, _ in CONCEPT_MARKS}
    return {'hull_length_vox': round(Lh, 2), 'stern_top': [round(x_st, 2), round(z_st, 2)],
            'waist_rail_z_at_x': [x_w, round(float(H.top(x_w)), 2)], 'qd_rail_z_at_x': [round(x_q, 2), round(float(H.top(x_q)), 2)],
            'waist_rail_over_length': round(float(H.top(x_w)) / Lh, 3), 'qd_rail_over_length': round(float(H.top(x_q)) / Lh, 3),
            'concept': {'waist_rail_over_length': c['waist_rail'], 'qd_rail_over_length': c['qd_rail'], 'waist_bulwark_over_length': c['waist_bulwark'],
                        'note': '定稿圖 2 倍放大目測 ±4 px；龍骨 y 497、船長 491 px（階段一像素量）'}}


def draw_aft_body(H, path, title):
    """船尾半邊橫剖面（0–5 站）—— 給「v1 台階 vs 修正」對照用。"""
    S2 = 8; W, Hh = 520, 560; cx, base = 420, 520
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im)
    g.text((16, 10), title, fill=(30, 30, 30), font=font(20))
    def B(y, z): return (cx - y * S2, base - z * S2)
    for zw in H.L['waterlines'] + [H.trz]:
        col = (30, 90, 200) if zw == H.dwl else ((190, 40, 40) if zw == H.trz else (180, 180, 180))
        g.line([B(-6, zw), B(46, zw)], fill=col, width=1)
    g.text(B(45, H.trz + 1.2), "z " + str(H.trz) + "（翼艉板）", fill=(190, 40, 40), font=font(14))
    g.line([B(0, -1), B(0, 56)], fill=(30, 30, 30), width=1)
    st = np.linspace(H.kx0, H.kx1, H.L['stations'])
    zz = np.arange(0, 56, 0.125)
    for k in range(0, 6):
        h = H.hb(np.full(zz.shape, st[k]), zz)
        seg = [B(y, z) for y, z in zip(h, zz) if not np.isnan(y)]
        if len(seg) > 1: g.line(seg, fill=(190, 40, 40) if k == 0 else (30, 30, 30), width=3 if k == 0 else 1)
    g.text((16, Hh - 30), "紅 ＝ 0 站；左 ＝ 舷外", fill=(120, 120, 120), font=font(14))
    im.save(path, optimize=False)


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    if '--v1' in sys.argv or '--legacy-transom-overlays' in sys.argv: plan['lines'].pop('upper', None)
    H = Hull(plan)
    tag = 'v2' if H.up else 'v1'
    if '--legacy-transom-overlays' in sys.argv:
        od = os.path.join(d, '..', 'overlays')
        H.legacy_transom = True
        draw_aft_body(H, os.path.join(od, 'stage1_v1_transom_step.png'), "v1（重產）：方艉在 z 18 直接切換")
        H.legacy_transom = False
        draw_aft_body(H, os.path.join(od, 'stage1_v2_transom_smooth.png'), "v2：漸變（smoothstep）")
        print('overlays ok'); return
    R = readings(H)
    solid, shell, rs = shell_voxels(H, plan['lines']['shell_preview_thickness'])
    R['shell'] = rs
    if H.up: R['upper'] = upper_readings(H)
    R['midship_section'] = {'floor_tangent_z': round(H.z_floor_tan, 3), 'bilge_center': [round(H.yc, 3), round(H.zc, 3)],
                            'hb_at_dwl': round(float(H.hb_mid(H.dwl)), 3)}
    if not H.up:   # 殼的預覽只屬於階段一；階段二的正式遮罩由 draft_hull.py 產
        os.makedirs(os.path.join(d, 'masks', 'hull'), exist_ok=True)
        with open(os.path.join(d, 'masks', 'hull', 'shell_preview.vox.txt'), 'w', encoding='utf-8', newline='\n') as fo:
            fo.write("# 夜隼號 新圖紙 01 殼的預覽（厚 " + str(plan['lines']['shell_preview_thickness']) + " 格；只給草稿看形狀，⛔ 不是正式落子）\n")
            for x, y, z in np.argwhere(shell): fo.write(f"{x},{y},{z},136\n")
    draw_sheet(H, R, os.path.join(d, 'sheet01_lines_' + tag + '.png'))
    draw_compare(H, os.path.join(d, '..', 'references', 'night_falcon_v1.png'), os.path.join(d, 'compare01_concept_' + tag + '.png'))
    with open(os.path.join(d, 'verify_lines.json' if not H.up else 'verify_lines_v2.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
