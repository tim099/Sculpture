# 新圖紙 01 線形圖（TASK-0538）：plan.json ＋ readings_LI*.json（原圖讀數）⇒ 船殼曲面 hb(x, z)、線形圖、Pl. LI 對照圖、verify_lines.json。
# 用法：python -I draft_lines.py <design 資料夾>
#   · 長度先用「底圖公尺」（Chapman Pl. LI 上的尺寸）算，最後才 × k 換成格；k 由寬度上限算（plan.json scale）。
#   · 船殼（molded，肋骨外面）：每個高度 z，把各站半寬沿船長用 PCHIP 接起來，兩頭收到船尾柱／船頭柱的 rabbet；
#     z 在 tuck 以上，船尾那頭改收到 counter／船尾板（plan silhouette.stern_outline）。
#   · 不用 scipy.interpolate（這台載不起來）：PCHIP 自己寫。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None


# ───────────────────────── 插值 ─────────────────────────
def pchip(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = len(x)
    if n == 1:
        return lambda q: np.full(np.shape(q), y[0])
    h = np.diff(x)
    d = np.diff(y) / h
    m = np.zeros(n)
    if n == 2:
        m[:] = d[0]
    else:
        for i in range(1, n - 1):
            if d[i - 1] * d[i] > 0:
                w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        # 端點：三點公式，限制不過衝
        for e, (i0, i1) in ((0, (0, 1)), (n - 1, (n - 2, n - 3))):
            hh0, hh1 = (h[0], h[1]) if e == 0 else (h[-1], h[-2])
            d0, d1 = (d[0], d[1]) if e == 0 else (d[-1], d[-2])
            v = ((2 * hh0 + hh1) * d0 - hh0 * d1) / (hh0 + hh1)
            if np.sign(v) != np.sign(d0):
                v = 0.0
            elif np.sign(d0) != np.sign(d1) and abs(v) > abs(3 * d0):
                v = 3 * d0
            m[e] = v

    def f(q):
        q = np.asarray(q, float)
        i = np.clip(np.searchsorted(x, q) - 1, 0, n - 2)
        t = (q - x[i]) / h[i]
        return ((2 * t ** 3 - 3 * t ** 2 + 1) * y[i] + (t ** 3 - 2 * t ** 2 + t) * h[i] * m[i]
                + (-2 * t ** 3 + 3 * t ** 2) * y[i + 1] + (t ** 3 - t ** 2) * h[i] * m[i + 1])
    return f


def lin(xp, fp):
    xp = np.asarray(xp, float)
    fp = np.asarray(fp, float)
    o = np.argsort(xp)
    return lambda q: np.interp(q, xp[o], fp[o])


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ───────────────────────── 船 ─────────────────────────
class Ship:
    def __init__(s, plan, R, B):
        s.P = plan
        H, Sh, Si = plan['hull'], plan['sheer'], plan['silhouette']
        s.keel_half, s.stem_half, s.plank = H['keel_half'], H['stem_half'], H['plank']
        s.tumble, s.topside_z = H['tumble_per_m'], H['topside_z']
        sp = H['sternpost']
        s.sp_x0, s.sp_tan = sp['x_at_keel_top'], math.tan(math.radians(sp['rake_deg']))
        s.tuck_z = H['tuck_z']
        s.keel_depth = (R['datum']['keel_bottom_py'] - R['datum']['keel_top_py']) / R['px_per_m']

        # 各站：z → hb（z 範圍內有值）
        s.st = []
        secs = dict(B['body_plan']['sections_z_hb'])
        secs['mid'] = secs.get('mid_L', R['midship_section_z_hb'])   # 重追的最外圈（舊讀數 z 1.3–1.7 有跳線）
        for k, x in H['stations_x'].items():
            p = np.array(secs[k], float)
            p = p[np.argsort(p[:, 0])]
            ztop = H['station_top_z'].get(k, p[-1, 0])
            p = p[p[:, 0] <= ztop + 1e-9]
            s.st.append(dict(name=k, x=x, z0=p[0, 0], z1=p[-1, 0], f=lin(p[:, 0], p[:, 1]), hb_top=p[-1, 1]))
        s.st.sort(key=lambda d: d['x'])

        # 船頭柱：外緣（原圖讀數）＋ rabbet（各站下端）
        so = np.array(R['stem_outer'], float)
        so = so[np.argsort(so[:, 1])]
        s.stem_outer_pts = so
        top = so[so[:, 1] >= so[-1, 1] - 1.0]
        s.stem_top_slope = np.polyfit(top[:, 1], top[:, 0], 1)[0]          # dx/dz
        rp = np.array(B['stem_rabbet_profile']['x_z'], float)                # (x, z)，z ≤ 5.2
        s.rab_pts = rp[np.argsort(rp[:, 1])]
        s.rab_rake = H['rabbet_rake_above']
        s.stem_siding = H['stem_siding']

        # 舷弧：主 wale 擬合
        w = np.array(B['main_wale']['x_z'], float)
        a, b = Sh['wale_fit_x']
        w = w[(w[:, 0] >= a) & (w[:, 0] <= b)]
        s.wale_c = np.polyfit(w[:, 0], w[:, 1], Sh['wale_poly_deg'])
        s.wale_rms = float(np.sqrt(np.mean((np.polyval(s.wale_c, w[:, 0]) - w[:, 1]) ** 2)))
        s.wale_pts = w
        s.rail_above_wale = Sh['rail_above_wale']

        # 船尾輪廓（tuck 以上）
        so2 = np.array(Si['stern_outline_x_z'], float)
        s.stern_outline = so2
        s.stern_x_of_z = lin(so2[:, 1], so2[:, 0])
        s.Si = Si
        s.lwl_s, s.lwl_b = Si['lwl']['stern_z'], Si['lwl']['bow_z']
        s.stern_top = s.lwl_s + Si['stern_top_above_lwl']

    # 船頭柱外緣 x(z)（頂上照最後 1 m 的斜度往上延）
    def stem_outer_x(s, z):
        so = s.stem_outer_pts
        z = np.asarray(z, float)
        x = np.interp(z, so[:, 1], so[:, 0])
        hi = z > so[-1, 1]
        return np.where(hi, so[-1, 0] + (z - so[-1, 1]) * s.stem_top_slope, x)

    def rabbet_x(s, z):                          # 船頭柱 rabbet：追線（z ≤ 5.2）＋往上幾乎垂直
        z = np.asarray(z, float)
        rp = s.rab_pts
        low = np.interp(z, rp[:, 1], rp[:, 0])
        return np.where(z > rp[-1, 1], rp[-1, 0] + (z - rp[-1, 1]) * s.rab_rake, low)

    def sternpost_x(s, z):                       # 船尾柱後面
        return s.sp_x0 - np.asarray(z, float) * s.sp_tan

    def wale(s, x):
        return np.polyval(s.wale_c, x)

    def lwl(s, x):
        return s.lwl_s + (s.lwl_b - s.lwl_s) * (np.asarray(x, float) - (-0.319)) / (38.901 + 0.319)

    # 舷牆頂（輪廓的上緣）
    def top(s, x):
        Si = s.Si
        x = np.asarray(x, float)
        base = s.wale(np.clip(x, -1.0, 41.0)) + s.rail_above_wale
        qd = Si['qd_rise'] * smoothstep((Si['qd_break_x'] + Si['qd_scroll'] / 2 - x) / Si['qd_scroll'])
        z = base + qd
        xt, xp = Si['taffrail_x'], Si['poop_from_x']
        base_t = s.wale(-1.0) + s.rail_above_wale + Si['qd_rise']
        t = np.clip((xp - x) / (xp - xt), 0, 1)
        z = z + (s.stern_top - base_t) * t ** Si['poop_power']
        xb = Si['bow_rise_from_x']
        xe = s.fwd_end_top_x()
        z = z + Si['bow_rise'] * np.clip((x - xb) / (xe - xb), 0, 1) ** 2
        return z

    def fwd_end_top_x(s):                        # 船頭舷牆頂：rabbet ＋ 船頭柱寬
        return float(s.rabbet_x(11.0)) + s.stem_siding

    # 船殼半寬 molded：hb(x, z)；船殼外（＝ 兩頭之間）以外 nan
    def ends(s, z):
        """這個高度的船尾端 (x, hb) 與船頭端 (x, hb)"""
        if z <= s.tuck_z:
            xa = float(s.sternpost_x(z)) + 0.40          # rabbet 在船尾柱後面往前 0.40（設計）
            ha = s.keel_half
        else:
            xa = float(s.stern_x_of_z(min(z, s.stern_outline[-1, 1])))
            ha = None                                    # counter／船尾板：半寬由最後一站往後延
        xf = float(s.rabbet_x(z))
        return (xa, ha), (xf, s.stem_half)

    def station_hb(s, st, z):
        if z < st['z0'] - 1e-9:
            return None
        if z <= st['z1'] + 1e-9:
            return float(st['f'](z))
        if st['z1'] >= 9.0:                              # 舷頂以上：照內傾往上
            return st['hb_top'] - s.tumble * (z - st['z1'])
        return None

    def row(s, z):
        (xa, ha), (xf, hf) = s.ends(z)
        pts = []
        for st in s.st:
            if xa + 0.05 < st['x'] < xf - 0.05:
                h = s.station_hb(st, z)
                if h is not None:
                    pts.append((st['x'], max(h, s.keel_half)))
        if not pts:
            return None
        if ha is None:                                   # 船尾板：照最後兩站的斜率往後延，但不比最近一站寬
            if len(pts) >= 2:
                (x1, h1), (x2, h2) = pts[0], pts[1]
                ha = min(h1, h1 + (h1 - h2) / (x2 - x1) * (xa - x1) * 0.5)
            else:
                ha = pts[0][1]
        P = [(xa, ha)] + pts + [(xf, hf)]
        X = np.array([p[0] for p in P])
        Hh = np.array([p[1] for p in P])
        return X, Hh, pchip(X, Hh)

    def hb(s, x, z):
        r = s.row(z)
        x = np.asarray(x, float)
        if r is None:
            return np.full(x.shape, np.nan)
        X, Hh, f = r
        out = f(x)
        out[(x < X[0]) | (x > X[-1])] = np.nan
        out[z > s.top(x) + 1e-9] = np.nan
        return np.maximum(out, 0.0)


# ───────────────────────── 畫圖工具 ─────────────────────────
def font(size, bold=False):
    f = 'C:/Windows/Fonts/msjhbd.ttc' if bold else 'C:/Windows/Fonts/msjh.ttc'
    return ImageFont.truetype(f, int(size))


C_HULL = (20, 20, 20)
C_GRID = (215, 220, 230)
C_WL = (40, 110, 200)
C_SHEER = (200, 60, 40)
C_DES = (210, 120, 0)
C_LAMP = (235, 175, 0)
C_TXT = (40, 40, 40)


class Panel:
    """世界座標（格）→ 圖上像素：u = ox + (X − X0)·sc，v = oy − (Z − Z0)·sc"""
    def __init__(s, dr, ox, oy, X0, Z0, sc):
        s.dr, s.ox, s.oy, s.X0, s.Z0, s.sc = dr, ox, oy, X0, Z0, sc

    def p(s, X, Z):
        return (s.ox + (X - s.X0) * s.sc, s.oy - (Z - s.Z0) * s.sc)

    def line(s, pts, fill, width=1):
        pts = [s.p(a, b) for a, b in pts if np.isfinite(a) and np.isfinite(b)]
        if len(pts) >= 2:
            s.dr.line(pts, fill=fill, width=width)

    def text(s, X, Z, t, fill=C_TXT, f=None, anchor='la'):
        s.dr.text(s.p(X, Z), t, fill=fill, font=f, anchor=anchor)


def main():
    design = sys.argv[1]
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    R = json.load(open(os.path.join(design, 'readings_LI.json'), encoding='utf-8'))
    B = json.load(open(os.path.join(design, 'readings_LI_bodyplan.json'), encoding='utf-8'))
    ship = Ship(plan, R, B)
    Sc = plan['scale']
    Si = plan['silhouette']

    # ── 船殼表：x 每 0.05、z 每 0.05（底圖公尺）
    xs = np.round(np.arange(-3.0, 42.5 + 1e-9, 0.05), 3)
    zmax = ship.stern_top + 0.05
    zs = np.round(np.arange(0.0, zmax, 0.05), 3)
    T = np.full((len(zs), len(xs)), np.nan)
    for j, z in enumerate(zs):
        T[j] = ship.hb(xs, z)
    hb_max = float(np.nanmax(T[zs <= 9.5]))
    jm, im = np.unravel_index(np.nanargmax(np.where(zs[:, None] <= 9.5, T, -1)), T.shape)

    # ── 倍數：寬度先碰上限
    k = Sc['breadth_limit_m'] / (2 * (hb_max + ship.plank))
    cpm = Sc['cells_per_m'] * k                           # 底圖 1 m ＝ 幾格
    X = lambda x: Sc['X_of_x0'] + np.asarray(x, float) * cpm
    Z = lambda z: Sc['Z_of_keel_top'] + np.asarray(z, float) * cpm
    Yh = lambda h: np.asarray(h, float) * cpm             # 半寬（格）
    kd = ship.keel_depth

    # ── 輪廓上的幾個點
    x_taff = Si['taffrail_x']
    x_head = Si['head']['figurehead_box_x'][1]
    x_stem_top = ship.fwd_end_top_x()
    xr = np.linspace(x_taff, x_stem_top, 600)
    top = ship.top(xr)
    M = plan['masts']
    bs = M['bowsprit']
    bs_z0 = float(ship.top(x_stem_top)) - 0.6
    bs_ang = math.radians(bs['angle_deg'])
    bs_tip = (x_stem_top + (bs['outboard'] + bs['jibboom_outboard']) * math.cos(bs_ang),
              bs_z0 + (bs['outboard'] + bs['jibboom_outboard']) * math.sin(bs_ang))

    # ── verify
    beam_cells = 2 * (hb_max + ship.plank) * cpm
    ver = {
        'k': round(k, 5),
        'k_note': 'k ＝ 13.335 ÷（2 ×（最大半寬 molded ＋ 外板））',
        'hb_max_molded_m': round(hb_max, 3), 'hb_max_at_x_z': [float(xs[im]), float(zs[jm])],
        'plank_m': ship.plank,
        'beam_with_plank_cells': round(beam_cells, 2), 'beam_with_plank_m': round(beam_cells / 10, 3),
        'between_perpendiculars_m': round((38.901 + 0.319) * k, 2),
        'sternpost_to_stem_head_m': round((x_stem_top - float(ship.sternpost_x(0))) * k, 2),
        'hull_X_cells': [round(float(X(min(x_taff, -1.13))), 1), round(float(X(x_head)), 1)],
        'bowsprit_tip_X_cells': round(float(X(bs_tip[0])), 1),
        'stern_top_Z_cells': round(float(Z(ship.stern_top)), 1),
        'mast_top_Z_cells': {n: round(float(Z(M['lengths_above_keel'][n])), 1) for n in M['x']},
        'lwl_Z_cells': {'stern': round(float(Z(ship.lwl_s)), 1), 'bow': round(float(Z(ship.lwl_b)), 1)},
        'draft_m': {'stern': round((ship.lwl_s + kd) * k, 2), 'bow': round((ship.lwl_b + kd) * k, 2)},
        'wale_fit_rms_m': round(ship.wale_rms, 3),
        'Y_half_max_cells': round(beam_cells / 2, 1),
        'fits_work': None,
    }
    ver['fits_work'] = bool(ver['bowsprit_tip_X_cells'] < plan['verify']['max_x_cells'] and ver['hull_X_cells'][0] > 0
                            and ver['Y_half_max_cells'] < 160 and max(ver['mast_top_Z_cells'].values()) < plan['verify']['max_z_cells'])

    # ════════════════ sheet01：線形圖 ════════════════
    SC1 = 2.2
    W, Hh = 2050, 1330
    im1 = Image.new('RGB', (W, Hh), 'white')
    dr = ImageDraw.Draw(im1)
    fT, fM, fS = font(30, True), font(17), font(14)
    dr.text((30, 18), plan['title'], fill=C_TXT, font=fT)
    dr.text((30, 58), f'TASK-0538 · basecamp · {plan["date"]} · 底圖 Chapman 1768 Pl. LI（英國東印度商船）放大 ×{k:.4f}（寬度先碰 43 ft 9 in）· 1 格 = 0.1 m · 格線每 10 m',
            fill=C_TXT, font=fM)

    # ── 側面（船殼放大）
    PX0, PZ0 = 30.0, -12.0
    pr = Panel(dr, 40, 650, PX0, PZ0, SC1)
    for gx in range(0, 1100, 100):
        if PX0 <= gx <= PX0 + 680:
            pr.line([(gx, PZ0), (gx, PZ0 + 255)], C_GRID)
            pr.text(gx + 2, PZ0 + 253, f'{gx}', fill=(150, 150, 170), f=fS)
    for gz in range(0, 260, 50):
        pr.line([(PX0, gz), (PX0 + 680, gz)], C_GRID)
        pr.text(PX0 + 1, gz + 6, f'Z {gz}', fill=(150, 150, 170), f=fS)
    # 站位
    for st in ship.st:
        pr.line([(X(st['x']), Z(0)), (X(st['x']), Z(ship.top(st['x'])))], (225, 225, 225))
        pr.text(X(st['x']), Z(-0.2) , st['name'], fill=(160, 160, 160), f=fS, anchor='ma')
    # 吃水線
    pr.line([(X(x), Z(ship.lwl(x))) for x in np.linspace(-0.8, 41.3, 50)], C_WL, 2)
    pr.text(X(41.6), Z(ship.lwl(41)), '吃水線（船尾深 0.5 底圖 m）', fill=C_WL, f=fS)
    # 龍骨、船頭柱、船尾柱、船尾
    zz = np.linspace(ship.stem_outer_pts[0, 1], ship.stem_outer_pts[-1, 1], 80)
    stem = [(X(ship.stem_outer_x(z)), Z(z)) for z in zz]           # 船頭柱＋gripe＋knee 外緣（照圖）
    zb = np.linspace(4.0, float(ship.top(x_stem_top)), 30)
    bowf = [(X(ship.rabbet_x(z) + ship.stem_siding), Z(z)) for z in zb]   # 船頭柱前面（吃水線以上、knee 後面）
    keel = [(X(ship.sternpost_x(0)), Z(-kd)), (X(ship.stem_outer_pts[0, 0]), Z(-kd))]
    pr.line(keel, C_HULL, 3)
    pr.line(stem, C_HULL, 3)
    pr.line([(X(ship.stem_outer_pts[0, 0]), Z(-kd)), stem[0]], C_HULL, 3)
    pr.line(bowf, C_HULL, 2)
    pr.line([(X(x), Z(z)) for x, z in zip(*ship.rab_pts.T)], (150, 150, 150), 1)
    spz = np.linspace(-kd, ship.tuck_z, 20)
    pr.line([(X(ship.sternpost_x(z)), Z(z)) for z in spz], C_HULL, 3)
    so = ship.stern_outline
    pr.line([(X(a), Z(b)) for a, b in so], C_HULL, 3)
    # 舷牆頂（輪廓上緣）、wale
    pr.line([(X(a), Z(b)) for a, b in zip(xr, top)], C_HULL, 3)
    pr.line([(X(x_taff), Z(ship.stern_top)), (X(so[-1, 0]), Z(so[-1, 1]))], C_HULL, 3)
    xw = np.linspace(-1.2, 41.0, 200)
    for off in (0.0, -Sh_wd(plan)):
        pr.line([(X(x), Z(ship.wale(x) + off)) for x in xw], C_SHEER, 2)
    pr.text(X(24), Z(ship.wale(24)) + 8, '主 wale（照圖）', fill=C_SHEER, f=fS)
    pr.line([(X(x), Z(ship.wale(x) + ship.rail_above_wale)) for x in np.linspace(Si['qd_break_x'], 37, 50)], (200, 200, 200), 1)
    # 舵
    rz = Si['rudder_top_z']
    rud = [(X(ship.sternpost_x(-kd)), Z(-kd)), (X(Si['rudder_back_at_keel_x']), Z(-kd)),
           (X(ship.sternpost_x(rz) - 0.45), Z(rz)), (X(ship.sternpost_x(rz)), Z(rz))]
    pr.line(rud, C_HULL, 2)
    # 船頭 knee、船頭像框
    hd = Si['head']
    fx, fz = hd['figurehead_box_x'], hd['figurehead_box_z']
    pr.line([(X(fx[0]), Z(fz[0])), (X(fx[1]), Z(fz[0])), (X(fx[1]), Z(fz[1])), (X(fx[0]), Z(fz[1])), (X(fx[0]), Z(fz[0]))], C_DES, 2)
    # head rails（設計）：船頭舷牆往前接到船頭像背後，上下兩條
    xb0 = x_stem_top
    ztop_b = float(ship.top(x_stem_top))
    for z0, z1 in ((ztop_b - 1.2, fz[1] - 0.9), (ztop_b - 2.6, fz[0] + 1.0)):
        t = np.linspace(0, 1, 20)
        pr.line([(X(xb0 + (fx[0] - xb0) * u), Z(z0 + (z1 - z0) * u - 0.35 * math.sin(math.pi * u))) for u in t], C_DES, 2)
    lamp_hand = (X(fx[1] - 0.5), Z(fz[1] + 0.4))
    pr.dr.ellipse([pr.p(lamp_hand[0] - 5, lamp_hand[1] + 5), pr.p(lamp_hand[0] + 5, lamp_hand[1] - 5)], fill=C_LAMP, outline=C_DES)
    pr.text(X(fx[0]), Z(fz[0]) - 4, f'船頭像：舉燈的女像（框 {(fx[1] - fx[0]) * k:.1f} × {(fz[1] - fz[0]) * k:.1f} m）', fill=C_DES, f=fS, anchor='la')
    # 船尾大提燈
    lt = (X(x_taff + 0.3), Z(ship.stern_top + 0.6))
    pr.dr.ellipse([pr.p(lt[0] - 6, lt[1] + 7), pr.p(lt[0] + 6, lt[1] - 7)], fill=C_LAMP, outline=C_DES)
    pr.text(lt[0] + 10, lt[1] + 4, '船尾大提燈', fill=C_DES, f=fS, anchor='la')
    # 桅（只畫到圖框）、bowsprit
    for n, x in M['x'].items():
        r = math.radians(M['rake_deg'][n])
        L = M['lengths_above_keel'][n]
        pr.line([(X(x), Z(0)), (X(x) - 240 * math.tan(r), 240)], (120, 90, 60), 3)
        pr.text(X(x) + 6, 30, {'mizzen': '後桅', 'main': '主桅', 'fore': '前桅'}[n], fill=(120, 90, 60), f=fS)
    bl = (PX0 + 680 - X(x_stem_top)) / math.cos(bs_ang)                 # 只畫到圖框右緣
    pr.line([(X(x_stem_top), Z(bs_z0)), (X(x_stem_top) + bl * math.cos(bs_ang), Z(bs_z0) + bl * math.sin(bs_ang))], (120, 90, 60), 3)
    # 標註
    pr.text(X(Si['qd_break_x']), Z(ship.top(Si['qd_break_x'])) + 14, '後甲板盡頭（劇照比例）', fill=C_DES, f=fS, anchor='ma')
    pr.text(X(x_taff) + 10, Z(ship.stern_top) - 14, f'船尾頂：吃水線上 {Si["stern_top_above_lwl"] * k:.1f} m（劇照比例 2.09 × 船腰）', fill=C_DES, f=fS)
    pr.text(PX0 + 678, PZ0 + 3, '側面（船殼；桅只畫到 240 格）', fill=C_TXT, f=fM, anchor='rd')

    # ── 半寬圖
    hp = Panel(dr, 40, 650 + 210, PX0, 0, SC1)          # Z 軸當 Y（往上 ＝ 船寬）
    dr.text((40, 650 + 18), '半寬（左舷一半；molded，肋骨外面）', fill=C_TXT, font=fM)
    hp.line([(PX0, 0), (PX0 + 680, 0)], C_GRID)
    for gx in range(100, 800, 100):
        hp.line([(gx, 0), (gx, 75)], C_GRID)
    wls = [(1.0, '1'), (2.0, '2'), (3.0, '3'), (4.0, '4'), (5.36, '吃水'), (7.0, '7')]
    for z, lab in wls:
        h = ship.hb(xs, z)
        hp.line([(X(x), Yh(v)) for x, v in zip(xs, h)], C_WL, 1)
        i8 = int(np.argmin(np.abs(xs - 8.0)))
        if np.isfinite(h[i8]):
            hp.text(X(8.0) - 3, Yh(h[i8]) + 2, f'z{lab}', fill=C_WL, f=fS, anchor='rd')
    mb = np.nanmax(np.where(zs[:, None] <= 9.5, T, np.nan), axis=0)
    hp.line([(X(x), Yh(v)) for x, v in zip(xs, mb)], C_HULL, 2)
    ht = np.array([ship.hb(np.array([x]), float(ship.top(x)) - 0.01)[0] for x in xs])
    hp.line([(X(x), Yh(v)) for x, v in zip(xs, ht)], C_SHEER, 2)
    hp.text(X(20), Yh(mb[np.searchsorted(xs, 20)]) + 16, f'最大寬（molded 半寬 {hb_max * cpm:.1f} 格）', fill=C_HULL, f=fS)
    hp.text(X(28), Yh(ht[np.searchsorted(xs, 28)]) - 2, '舷牆頂', fill=C_SHEER, f=fS)

    # ── 橫切面（左：船尾半；右：船頭半）
    BX, BZ, SB = 1700, 650, 2.2
    dr.text((BX - 200, 98), '橫切面（左：船尾那半段；右：船頭那半段）', fill=C_TXT, font=fM)
    for gz in range(0, 230, 50):
        dr.line([(BX - 180, BZ - gz * SB), (BX + 180, BZ - gz * SB)], fill=C_GRID)
    dr.line([(BX, BZ + 10), (BX, BZ - 230 * SB)], fill=(180, 180, 180))
    for st in ship.st:
        sgn = -1 if st['x'] < 18.0 else (1 if st['x'] > 19.0 else 0)
        sides = [sgn] if sgn else [-1, 1]
        zz2 = np.arange(0, float(ship.top(st['x'])), 0.05)
        pts = [(z, ship.hb(np.array([st['x']]), z)[0]) for z in zz2]
        for sd in sides:
            q = [(BX + sd * Yh(h) * SB, BZ - Z(z) * SB) for z, h in pts if np.isfinite(h)]
            if len(q) > 1:
                dr.line(q, fill=C_HULL if st['name'] == 'mid' else (90, 90, 90), width=2 if st['name'] == 'mid' else 1)
                h2 = ship.hb(np.array([st['x']]), 2.0)[0]
                if np.isfinite(h2) and st['name'] != 'mid':
                    dr.text((BX + sd * Yh(h2) * SB, BZ - Z(2.0) * SB), st['name'], fill=(200, 60, 40), font=font(12), anchor='mm')
    dr.line([(BX - 180, BZ - Z(5.36) * SB), (BX + 180, BZ - Z(5.36) * SB)], fill=C_WL, width=1)

    # ── 全帆輪廓縮圖
    TX, TZ, ST = 1260, 1300, 0.55
    dr.text((TX, TZ - 420), '全長示意（桅、bowsprit 是草案，帆裝階段再算）', fill=C_TXT, font=fS)
    tp = Panel(dr, TX, TZ - 20, 0, 0, ST)
    tp.line([(0, 0), (1024, 0), (1024, 700), (0, 700), (0, 0)], (200, 200, 200))
    tp.line([(X(a), Z(b)) for a, b in zip(xr, top)], C_HULL, 2)
    tp.line(keel, C_HULL, 2)
    tp.line(stem, C_HULL, 2)
    tp.line([(X(a), Z(b)) for a, b in so], C_HULL, 2)
    for n, x in M['x'].items():
        r = math.radians(M['rake_deg'][n])
        L = M['lengths_above_keel'][n]
        tp.line([(X(x), Z(0)), (X(x - L * math.sin(r)), Z(L * math.cos(r)))], (120, 90, 60), 2)
    tp.line([(X(x_stem_top), Z(bs_z0)), (X(bs_tip[0]), Z(bs_tip[1]))], (120, 90, 60), 2)
    tp.line([(X(x), Z(ship.lwl(x))) for x in (-0.8, 41.3)], C_WL, 1)
    tp.text(2, 690, '作品框 1024 × 800（X × Z）', fill=(150, 150, 150), f=fS)

    # ── 數字欄
    ty = 900
    lines = [
        f'放大倍數 k = {k:.4f}（最大半寬 molded {hb_max:.3f} ＋ 外板 {ship.plank} 底圖 m）',
        f'船寬（含外板）{ver["beam_with_plank_m"]:.2f} m ＝ {ver["beam_with_plank_cells"]:.1f} 格',
        f'兩垂標間 {ver["between_perpendiculars_m"]:.1f} m；船尾柱到船頭柱頂 {ver["sternpost_to_stem_head_m"]:.1f} m',
        f'吃水（龍骨底起）船尾 {ver["draft_m"]["stern"]:.2f} m、船頭 {ver["draft_m"]["bow"]:.2f} m',
        f'船殼 X {ver["hull_X_cells"][0]:.0f}–{ver["hull_X_cells"][1]:.0f}；bowsprit 尖 X {ver["bowsprit_tip_X_cells"]:.0f}；船尾頂 Z {ver["stern_top_Z_cells"]:.0f}',
        f'主 wale 擬合 rms {ship.wale_rms * 100:.1f} cm（底圖）',
        '黑：照圖（Chapman Pl. LI 讀數）　紅：照圖的舷弧　橘：設計（船頭像、knee、燈）',
    ]
    for i, t in enumerate(lines):
        dr.text((40, ty + 22 * i + 20), t, fill=C_TXT, font=fM)
    out1 = os.path.join(design, 'sheet01_lines_v1.png')
    im1.save(out1)

    # ════════════════ compare01：疊回 Pl. LI ════════════════
    ref = R
    pxm = ref['px_per_m']
    x0p, kt, hc = ref['datum']['x0_px'], ref['datum']['keel_top_py'], ref['datum']['half_breadth_centre_py']
    bpc, bpk = B['body_plan']['centre_px'], B['body_plan']['keel_top_py']
    plate = os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768', 'PlLI_Engelsk_Ostindiefarare.tif')
    base = Image.open(plate).convert('L')
    cx0, cy0, cx1, cy1 = 900, 3500, 11300, 8100
    s2 = 0.17
    A = base.crop((cx0, cy0, cx1, cy1)).resize((int((cx1 - cx0) * s2), int((cy1 - cy0) * s2)), Image.LANCZOS).convert('RGB')
    A = Image.blend(A, Image.new('RGB', A.size, 'white'), 0.35)
    da = ImageDraw.Draw(A)
    P = lambda x, z: ((x0p + x * pxm - cx0) * s2, (kt - z * pxm - cy0) * s2)
    PH = lambda x, h: ((x0p + x * pxm - cx0) * s2, (hc + h * pxm - cy0) * s2)
    red, org = (230, 0, 0), (255, 120, 0)
    da.line([P(a, b) for a, b in zip(xr, top)], fill=org, width=2)
    da.line([P(a, b) for a, b in so], fill=org, width=2)
    da.line([P(float(ship.stem_outer_x(z)), z) for z in zz], fill=red, width=2)
    da.line([P(float(ship.rabbet_x(z)), z) for z in np.linspace(0.05, 9.0, 60)], fill=red, width=2)
    da.line([P(float(ship.rabbet_x(z) + ship.stem_siding), z) for z in zb], fill=org, width=2)
    fx, fz = Si['head']['figurehead_box_x'], Si['head']['figurehead_box_z']
    da.rectangle([P(fx[0], fz[1]), P(fx[1], fz[0])], outline=org, width=2)
    da.line([P(float(ship.sternpost_x(z)), z) for z in spz], fill=red, width=2)
    da.line([P(x, ship.wale(x)) for x in xw], fill=red, width=2)
    da.line([P(x, ship.lwl(x)) for x in (-0.8, 41.3)], fill=(0, 90, 220), width=1)
    for n, x in M['x'].items():
        da.line([P(x, 9.0), P(x, 12.5)], fill=red, width=2)
    # 半寬圖：最大寬（z ≤ tuck）molded 與 ＋外板（原圖：細線 5.15、粗線 5.32）
    mbt = np.nanmax(np.where(zs[:, None] <= ship.tuck_z, T, np.nan), axis=0)
    da.line([PH(x, v) for x, v in zip(xs, mbt) if np.isfinite(v)], fill=red, width=1)
    da.line([PH(x, v + ship.plank) for x, v in zip(xs, mbt) if np.isfinite(v)], fill=org, width=1)
    fa = font(22, True)
    da.text((10, 8), 'compare01 v1：紅／橘 ＝ 新圖紙（底圖公尺，未放大）疊回 Chapman Pl. LI', fill=(0, 0, 0), font=fa)
    da.text((10, 38), '側面：紅 ＝ 照圖讀數做的（船頭柱、船尾柱、wale、桅位）；橘 ＝ 設計（舷牆頂、船尾樓、船尾輪廓）', fill=(0, 0, 0), font=font(17))
    da.text((10, 62), '半寬圖（下）：紅 ＝ 用橫切面圖做的船殼最大寬（molded）、橘 ＝ ＋外板 0.13 —— 半寬圖是另一張圖，這是獨立對照（船尾 x < 3 的最大寬線高度不同，不能直接比）', fill=(0, 0, 0), font=font(17))
    # 橫切面圖
    bx0, by0, bx1, by1 = 7450, 1750, 9900, 4180
    s3 = 0.42
    Bm = base.crop((bx0, by0, bx1, by1)).resize((int((bx1 - bx0) * s3), int((by1 - by0) * s3)), Image.LANCZOS).convert('RGB')
    Bm = Image.blend(Bm, Image.new('RGB', Bm.size, 'white'), 0.35)
    db = ImageDraw.Draw(Bm)
    PB = lambda sd, h, z: ((bpc + sd * h * pxm - bx0) * s3, (bpk - z * pxm - by0) * s3)
    for st in ship.st:
        sd = -1 if st['x'] < 18.0 else (1 if st['x'] > 19.0 else 0)
        zz2 = np.arange(0, float(ship.top(st['x'])), 0.05)
        pts = [(z, ship.hb(np.array([st['x']]), z)[0]) for z in zz2]
        for s_ in ([sd] if sd else [-1, 1]):
            q = [PB(s_, h, z) for z, h in pts if np.isfinite(h)]
            if len(q) > 1:
                db.line(q, fill=red, width=2)
    db.text((8, 6), '橫切面圖：紅 ＝ 新圖紙在各站（自己對自己：檢查平滑與內插沒有走樣）', fill=(0, 0, 0), font=font(17))
    Wc = A.width + Bm.width + 20
    C = Image.new('RGB', (Wc, max(A.height, Bm.height)), 'white')
    C.paste(A, (0, 0))
    C.paste(Bm, (A.width + 20, 0))
    out2 = os.path.join(design, 'compare01_chapman_v1.png')
    C.save(out2)

    # 數字：z 1.38 水線與最大寬，在幾個 x 跟半寬圖原圖比
    chk = []
    mbr = np.array(R['max_breadth_plan_x_hb'], float)          # 半寬圖外圈粗線（readings_LI.json）
    for xm in (3.0, 8.0, 13.0, 18.9, 25.0, 30.0, 35.0, 37.5):
        i = int(np.argmin(np.abs(xs - xm)))
        j = int(np.argmin(np.abs(mbr[:, 0] - xm)))
        chk.append({'x': xm, 'maxb_molded': round(float(mbt[i]), 3), 'maxb_plus_plank': round(float(mbt[i] + ship.plank), 3),
                    'half_breadth_plan_outer_thick': round(float(mbr[j, 1]), 3) if abs(mbr[j, 0] - xm) < 0.3 else None})
    ver['half_breadth_check_points'] = chk
    ver['outputs'] = [os.path.basename(out1), os.path.basename(out2)]
    json.dump(ver, open(os.path.join(design, 'verify_lines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(ver, ensure_ascii=False, indent=1))


def Sh_wd(plan):
    return plan['sheer']['wale_depth']


if __name__ == '__main__':
    main()
