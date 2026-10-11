# 新圖紙 13（船頭子作品）：plan.json 的 head 段 ＋ 組裝件的現況（船頭三條關聯加進來之前）
#   ⇒ masks/head/knee.vox.txt（子作品，at=0,0,0）、masks/head/side.vox.txt（一舷，自己的座標；另一舷 mirror=y）、
#      verify_head.json、sheet13_head_v1.png
# 用法：python -I draft_head.py <design 資料夾>
#   · knee：前緣（11 號 cutwater）與上緣（上 cheek 線 T_a）圍出的月牙，從艏柱前緣往前填；billethead 坐在頂上
#   · 貼在表面上的（cheeks、卷草、盾牌、hawse 圈）：每一層 z 跟船外相通、貼著實心的空格（外殼）裡，照側面 (x,z) 的圖樣挑
#   · rails：側面照 11 號、平面照 plan 曲線（離船殼不到 1 格就往外推）
import sys, os, json, hashlib, math, subprocess
import numpy as np
from scipy import ndimage
from scipy.interpolate import PchipInterpolator
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402

YC = 160
XA, XB, ZB = 560, 800, 200         # 只看船頭這一塊


def existing_links(work):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=links', '--arg', 'work=' + work],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    for line in r.stdout.splitlines():
        if 'link_paths =' in line:
            return [p for p in line.split('=', 1)[1].strip().split(';') if p]
    return []


def poly_interp(pts, key, val):
    a = np.array(pts, float)
    o = np.argsort(a[:, key])
    return lambda q: np.interp(q, a[o, key], a[o, val])


def signed_dist(px, pz, poly):
    """點到折線的距離，右手邊（沿折線前進方向的右側）為正。px, pz 同形狀陣列。"""
    P = np.array(poly, float)
    best = np.full(np.shape(px), np.inf)
    sgn = np.ones(np.shape(px))
    for (ax, az), (bx, bz) in zip(P[:-1], P[1:]):
        dx, dz = bx - ax, bz - az
        L2 = dx * dx + dz * dz
        t = np.clip(((px - ax) * dx + (pz - az) * dz) / L2, 0, 1)
        qx, qz = ax + t * dx, az + t * dz
        d = np.hypot(px - qx, pz - qz)
        cr = dx * (pz - az) - dz * (px - ax)          # > 0 ⇒ 左手邊
        m = d < best
        best = np.where(m, d, best)
        sgn = np.where(m, np.where(cr > 0, -1.0, 1.0), sgn)
    return best * sgn


def in_polygon(px, pz, poly):
    P = np.array(poly, float)
    inside = np.zeros(np.shape(px), bool)
    n = len(P)
    for i in range(n):
        ax, az = P[i]
        bx, bz = P[(i + 1) % n]
        cond = ((az > pz) != (bz > pz))
        xint = ax + (pz - az) * (bx - ax) / np.where(bz == az, 1e-9, bz - az)
        inside ^= cond & (px < xint)
    return inside


class Head:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['head']
        B = s.P['base']
        have = existing_links(ASSEMBLY)
        hide = [l for l in B['hide_links'] if l in have]
        a = export_list(ASSEMBLY, draft=False, hide_links=','.join(hide) if hide else None)
        assert len(a) == B['assembly_voxels'], ('讀到的現況格數對不上', len(a), B['assembly_voxels'])
        s.read = {'hidden': hide, 'voxels': int(len(a))}
        m = a[(a[:, 0] >= XA) & (a[:, 0] < XB) & (a[:, 2] < ZB)]
        s.G = np.zeros((XB - XA, 320, ZB), np.uint8)
        s.G[m[:, 0] - XA, m[:, 1], m[:, 2]] = m[:, 3]
        s.col = s.P['colors']
        s.knee = {}            # (x,y,z) → color
        s.side = {}            # 一舷（y > 160）
        s.kind = {}

    def S(s):
        """現況 ＋ knee（rails 之前的實心）。"""
        A = s.G > 0
        for (x, y, z) in s.knee:
            A[x - XA, y, z] = True
        return A

    # ── knee ＋ billethead ──
    def build_knee(s):
        K = s.P['knee']
        F = np.array(K['front'], float)
        xf = lambda z: np.interp(z, F[:, 1], F[:, 0])
        T = np.array(K['top'], float)
        zt = lambda x: np.interp(x, T[:, 0], T[:, 1], right=1e9)
        z0, z1 = K['z_from'], int(math.floor(F[:, 1].max()))
        Gs = s.G > 0
        for z in range(z0, z1 + 1):
            xfront = xf(z)
            for dy in range(-K['half_width'], K['half_width'] + 1):
                y = YC + dy
                col = Gs[:, y, z]
                xs_all = np.where(col[: int(xfront) - XA + 1])[0]
                if not len(xs_all):
                    continue
                xs = xs_all.max() + XA                 # 那一欄最前面的實心（艏柱／gripe／薄牆）
                for x in range(xs + 1, int(math.floor(xfront + 0.5)) + 1):
                    if z > zt(x):
                        continue
                    if abs(dy) > K['edge_half_width'] and x > xfront - K['edge_depth']:
                        continue
                    if Gs[x - XA, y, z]:
                        continue
                    s.knee[(x, y, z)] = s.col['black'] if z >= 63 else s.col['copper']
                    s.kind[(x, y, z)] = 'knee'
        # billethead
        Bh = s.P['billethead']
        cx, cz = Bh['center']
        r = Bh['radius']
        sp = Bh['spiral']
        ts = np.linspace(0, 1, 800)
        th = np.radians(sp['start_deg']) - 2 * np.pi * sp['turns'] * ts
        rr = sp['r_out'] - (sp['r_out'] - sp['r_in']) * ts
        spx, spz = cx + rr * np.cos(th), cz + rr * np.sin(th)
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for z in range(int(cz - r) - 1, int(cz + r) + 2):
                d = math.hypot(x - cx, z - cz)
                if d > r:
                    continue
                for dy in range(-Bh['half_width'], Bh['half_width'] + 1):
                    y = YC + dy
                    if Gs[x - XA, y, z]:
                        continue
                    c = s.col['white']
                    if abs(dy) == Bh['half_width']:
                        # 側面：白色雕刻、黑色凹處 —— 外圈白、渦卷線白、其餘黑；渦眼黑底一格白星
                        if d <= Bh['eye_radius']:
                            c = s.col['white'] if (x == round(cx) and z == round(cz)) else s.col['black']
                        elif d >= r - 0.9 or np.min(np.hypot(spx - x, spz - z)) <= 0.55:
                            c = s.col['white']
                        else:
                            c = s.col['black']
                    s.knee[(x, y, z)] = c
                    s.kind[(x, y, z)] = 'billethead'
        # 頸：knee 頂到球底之間的空格補上（同一欄上下都有）
        for x in range(int(cx - r), int(cx + r) + 1):
            for dy in range(-K['half_width'], K['half_width'] + 1):
                y = YC + dy
                zs = sorted(z for (xx, yy, z) in s.knee if xx == x and yy == y)
                for za, zb in zip(zs[:-1], zs[1:]):
                    for z in range(za + 1, zb):
                        if zb - za <= 3 and not Gs[x - XA, y, z]:
                            s.knee[(x, y, z)] = s.col['black']
                            s.kind[(x, y, z)] = 'knee'

    # ── 外殼（y > 160 那一舷）──
    def shells(s, zr, xr=(600, 790), kmax=2):
        A = s.S()
        st = ndimage.generate_binary_structure(2, 1)
        sh = {}
        for z in range(*zr):
            sol = A[xr[0] - XA:xr[1] - XA, YC:, z]
            lab, n = ndimage.label(~sol, structure=st)
            seeds = set(np.unique(np.concatenate([lab[-1], lab[:, -1]]))) - {0}
            ext = np.isin(lab, list(seeds))
            prev = sol.copy()
            layers = []
            for k in range(kmax):
                d = ndimage.binary_dilation(prev, st) & ext & ~prev
                layers.append(d)
                prev = prev | d
            sh[z] = layers
        s.shell_x0 = xr[0]
        return sh

    def outer_dy(s, A, x, z):
        col = A[x - XA, YC:, z]
        w = np.where(col)[0]
        return int(w.max()) if len(w) else -1

    def put_side(s, x, y, z, c, kind):
        k = (int(x), int(y), int(z))
        if k in s.side or k in s.knee or s.G[k[0] - XA, k[1], k[2]]:
            return False
        s.side[k] = int(c)
        s.kind[k] = kind
        return True

    def decal(s, sh, mask_fn, proud, color_fn, kind, min_y=None):
        for z, layers in sh.items():
            for k in range(proud):
                for i, j in np.argwhere(layers[k]):
                    x, y = i + s.shell_x0, j + YC
                    if y <= YC or (min_y is not None and y < min_y(x)):
                        continue
                    if mask_fn(x, z):
                        s.put_side(x, y, z, color_fn(x, z), kind)

    def build_side(s):
        P = s.P
        A = s.S()
        sh = s.shells((75, 142))
        kn = P['knee']
        min_y = lambda x: YC + kn['half_width'] + 1 if x >= 667 else YC + 1
        # cheeks
        C = P['cheeks']
        Ta, Bb = C['upper']['a'], C['lower']['b']
        tu, tl = C['upper']['thick'], C['lower']['thick']
        aft = C['aft_x']

        def cheek_up(x, z):
            if x < aft:
                return False
            d = signed_dist(np.array(x + 0.0), np.array(z + 0.0), Ta)
            return -0.35 <= d <= tu + 0.15

        def cheek_lo(x, z):
            if x < aft:
                return False
            d = signed_dist(np.array(x + 0.0), np.array(z + 0.0), Bb)
            return -0.35 <= d <= tl + 0.15
        s.decal(sh, cheek_up, C['proud'], lambda x, z: s.col['white'], 'cheek', min_y)
        s.decal(sh, cheek_lo, C['proud'], lambda x, z: s.col['white'], 'cheek', min_y)
        # hawse 圈（照正視的 (dy, z) 找到船殼表面上的點；表面距離 ≈ |Δdy|·√(1 + 1/k²)，k ＝ 那裡表面每前進 1 格 dy 少多少）
        H = P['hawse']
        s.hawse_at = []
        for dyc, zc in H['front_view']:
            z0 = int(round(zc))
            xs = [x for x in range(640, 680) if s.outer_dy(A, x, z0) >= 0]
            dys = np.array([s.outer_dy(A, x, z0) for x in xs], float)
            i = int(np.argmin(np.abs(dys - dyc)))
            xc = xs[i]
            k = abs(np.polyfit(xs[max(0, i - 3):i + 4], dys[max(0, i - 3):i + 4], 1)[0])
            fac = math.sqrt(1 + 1 / max(k, 0.2) ** 2)
            s.hawse_at.append({'x': xc, 'dy': float(dys[i]), 'z': zc, 'slope': round(k, 2)})

            def ring(x, z, dyc=dyc, zc=zc, fac=fac):
                ody = s.outer_dy(A, x, z)
                if ody < 0:
                    return False
                d = math.hypot((ody - dyc) * fac, z - zc)
                return H['r_in'] <= d <= H['r_out']
            s.decal(sh, ring, H['proud'], lambda x, z: s.col[H['color']], 'hawse', min_y)
        # 盾牌（knee 那一面，直立）
        SH = P['shield']
        rows = SH['rows']
        hgt, wid = len(rows), len(rows[0])
        cxs = SH['center_x']
        zT = signed_dist  # noqa
        zt_a = poly_interp(Ta, 0, 1)
        zb_b = poly_interp(Bb, 0, 1)
        zmid = (zt_a(cxs) - tu + zb_b(cxs)) / 2
        s.shield_at = {'x': cxs, 'z_mid': round(float(zmid), 2), 'inner': [round(float(zb_b(cxs)), 2), round(float(zt_a(cxs) - tu), 2)]}
        top = int(round(zmid + (hgt - 1) / 2))
        left = int(round(cxs - (wid - 1) / 2))
        lg = SH['legend']
        shield = {}
        for i, row in enumerate(rows):
            for j, ch in enumerate(row):
                if ch != '.':
                    shield[(left + j, top - i)] = s.col[{'white': 'white', 'blue': 'blue', 'red': 'red'}[lg[ch]]]
        s.decal(sh, lambda x, z: (x, z) in shield, SH['proud'], lambda x, z: shield[(x, z)], 'shield', min_y)
        # trailboard 卷草（兩道 cheek 之間；從前面那個 hawse 圈的前緣往前）
        TB = P['trailboard']
        sc = TB['scroll']
        # 帶子中線：上下兩道 cheek 內緣的中點；以前進方向的弧長 u 當參數
        xs_c = np.arange(TB['u_from_x'], 722.0, 0.25)
        up_in = zt_a(xs_c) - tu
        lo_in = zb_b(xs_c)
        ok = up_in - lo_in > 2 * TB['min_half_height']
        xs_c, mid, hh = xs_c[ok], ((up_in + lo_in) / 2)[ok], ((up_in - lo_in) / 2)[ok]
        u = np.concatenate([[0], np.cumsum(np.hypot(np.diff(xs_c), np.diff(mid)))])
        s.scroll_len = float(u[-1])
        lam = sc['wavelength']
        # 中線的切線與法線；v 量垂直於帶子的距離（v1 第一次量的是鉛直的 z 差，帶子在船頭陡起來時圖樣被壓扁）
        tx = np.gradient(xs_c)
        tz = np.gradient(mid)
        tn = np.hypot(tx, tz)
        tx, tz = tx / tn, tz / tn
        hp = hh * np.abs(tx)                      # 垂直於帶子的半高
        # 圖樣：莖 v ＝ A·h(u)·sin(2πu/λ)（取樣成點，量到曲線的真正距離 —— 第二次量的是 v 方向的差，波浪陡的地方線就斷）；
        # 每個波峰往內（中線那側）勾一個小鉤（0.75 圈）
        uu_s = np.arange(0, u[-1], 0.1)
        h_s = np.interp(uu_s, u, hp)
        stem_pts = np.stack([uu_s, sc['stem_amp'] * h_s * np.sin(2 * np.pi * uu_s / lam)], 1)
        cpts = [stem_pts]
        nlobe = int(u[-1] / (lam / 2))
        for k in range(nlobe):
            up = (k + 0.5) * lam / 2
            sk = 1 if k % 2 == 0 else -1
            h = float(np.interp(up, u, hp))
            R = sc['curl_r'] * h * 2
            vt = sk * sc['stem_amp'] * h                 # 波峰
            uc, vc = up + R * 0.6, vt - sk * R          # 鉤的中心：波峰往前、往中線各一點
            th0 = math.atan2(vt - vc, up - uc)
            tt = np.linspace(0, 1, 80)
            ang = th0 - sk * 2 * np.pi * sc['curl_turns'] * tt
            rr = R * (1 - 0.5 * tt)
            cpts.append(np.stack([uc + rr * np.cos(ang), vc + rr * np.sin(ang)], 1))
        cpts = np.concatenate(cpts)
        shield_box = (left - 1, left + wid, top - hgt, top + 1)

        def scroll_mask(x, z):
            if not (xs_c[0] <= x <= xs_c[-1]):
                return False
            if shield_box[0] <= x <= shield_box[1] and shield_box[2] <= z <= shield_box[3]:
                return False
            du = signed_dist(np.array(x + 0.0), np.array(z + 0.0), Ta)
            dl = signed_dist(np.array(x + 0.0), np.array(z + 0.0), Bb)
            if not (du > tu + 0.15 and dl < -0.35):
                return False
            # 投到中線：u ＝ 弧長、v ＝ 垂直於帶子的距離（往上／往後為正）
            dd = np.hypot(xs_c - x, mid - z)
            i = int(np.argmin(dd))
            uu = u[i] + (x - xs_c[i]) * tx[i] + (z - mid[i]) * tz[i]
            vv = -(x - xs_c[i]) * tz[i] + (z - mid[i]) * tx[i]
            near = np.abs(cpts[:, 0] - uu) <= 1.5
            return bool(near.any() and np.min(np.hypot(cpts[near, 0] - uu, cpts[near, 1] - vv)) <= sc['line_half'])
        s.decal(sh, scroll_mask, TB['proud'], lambda x, z: s.col['white'], 'scroll', min_y)
        # cathead（先放，rails 讓它）
        s.build_cathead(A)
        # rails
        s.build_rails(A)

    def build_cathead(s, A):
        Cc = s.P['cathead']
        rx, rz = Cc['root']
        rdy = s.outer_dy(A, int(rx), int(rz)) - 1
        a, b = math.radians(Cc['angle_deg']), math.radians(Cc['rise_deg'])
        d = np.array([math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b)])
        v = np.array([-math.sin(a), math.cos(a), 0.0])
        w = np.cross(d, v)
        o = np.array([rx, YC + rdy, rz], float)
        L, hf = Cc['length'], Cc['half'] + 0.1
        s.cathead_at = {'root': [rx, rdy, rz], 'end': [round(float(c), 1) for c in (o + d * L)]}
        for x in range(int(rx) - 6, int(rx + L) + 6):
            for y in range(YC, 320):
                for z in range(int(rz) - 6, int(rz + L * math.sin(b)) + 7):
                    p = np.array([x, y, z], float) - o
                    uu, vv, ww = p @ d, p @ v, p @ w
                    if 0 <= uu <= L and abs(vv) <= hf and abs(ww) <= hf:
                        c = s.col['gold'] if uu > L - 1 else s.col['black']
                        s.put_side(x, y, z, c, 'cathead')

    def build_rails(s, A):
        R = s.P['rails']
        pl = np.array(R['plan'], float)
        dyf = PchipInterpolator(pl[:, 0], pl[:, 1], extrapolate=False)

        def dy_plan(x):
            if x <= pl[0, 0]:
                return pl[0, 1]
            if x >= pl[-1, 0]:
                return pl[-1, 1]
            return float(dyf(x))
        top_poly = R['top']['upper'] + R['top']['lower'][::-1]
        main_poly = R['main']['upper'] + R['main']['lower'][::-1]
        panel_poly = R['top']['lower'] + [p for p in R['main']['upper'] if p[0] >= 643.0][::-1]
        xs = np.arange(630, 722)
        zs = np.arange(105, 142)
        XX, ZZ = np.meshgrid(xs, zs, indexing='ij')
        m_top = in_polygon(XX + 0.0, ZZ + 0.0, top_poly)
        m_main = in_polygon(XX + 0.0, ZZ + 0.0, main_poly)
        m_panel = in_polygon(XX + 0.0, ZZ + 0.0, panel_poly) & ~m_top & ~m_main
        s.rail_y = {}

        def ybase(x, z):
            yb = YC + int(round(dy_plan(x)))
            ody = s.outer_dy(A, x, z)
            if ody >= 0:
                yb = max(yb, YC + ody + 1)
            return yb
        for name, M in (('rail-top', m_top), ('rail-main', m_main)):
            edge = M & ~ndimage.binary_erosion(M, ndimage.generate_binary_structure(2, 1), border_value=0)
            for i, k in np.argwhere(M):
                x, z = int(xs[i]), int(zs[k])
                yb = ybase(x, z)
                # 最上一道黑芯白邊；main rail 全白（3 格粗的鉤做黑芯會變成描邊的空心字）
                c = s.col['white'] if (edge[i, k] or name == 'rail-main') else s.col['black']
                for t in range(R['rail_thick']):
                    s.put_side(x, yb + t, z, c, name)
        for i, k in np.argwhere(m_panel):
            x, z = int(xs[i]), int(zs[k])
            yb = ybase(x, z)
            for t in range(R['panel_thick']):
                s.put_side(x, yb + t, z, s.col['black'], 'panel')
        # head timbers：上 cheek（knee 那一面）→ main rail 下緣
        zt_a = poly_interp(s.P['cheeks']['upper']['a'], 0, 1)
        ml = np.array([p for p in R['main']['lower'] if p[0] >= 645.0], float)
        zml = lambda x: np.interp(x, ml[:, 0], ml[:, 1])
        s.timbers = []
        for xt in R['timbers_x']:
            x2 = xt + R['timber_lean']
            p0 = np.array([xt, YC + s.P['knee']['half_width'] + 1, zt_a(xt) - 0.5])
            p1 = np.array([x2, ybase(int(round(x2)), int(round(zml(x2)))), zml(x2) - 0.5])
            s.timbers.append([[round(float(c), 1) for c in p0], [round(float(c), 1) for c in p1]])
            n = int(np.linalg.norm(p1 - p0) * 4) + 2
            prev = None
            for t in np.linspace(0, 1, n):
                q = tuple(int(round(c)) for c in p0 + (p1 - p0) * t)
                if prev is not None and sum(abs(a - b) for a, b in zip(q, prev)) > 1:
                    # 保持面相連：斜著走補中間的格
                    for ax in range(3):
                        if q[ax] != prev[ax]:
                            mid = list(prev)
                            mid[ax] = q[ax]
                            s.put_side(*mid, s.col['white'], 'timber')
                            prev = tuple(mid)
                s.put_side(*q, s.col['white'], 'timber')
                prev = q

    # ── 驗 ──
    def verify(s):
        v = {'read': s.read}
        v['knee'] = {'cells': len(s.knee), 'by_kind': {k: sum(1 for q in s.knee if s.kind[q] == k) for k in ('knee', 'billethead')},
                     'colors': {str(c): sum(1 for q in s.knee.values() if q == c) for c in sorted(set(s.knee.values()))}}
        v['side'] = {'cells': len(s.side), 'by_kind': {}, 'colors': {str(c): sum(1 for q in s.side.values() if q == c) for c in sorted(set(s.side.values()))}}
        for q in s.side:
            v['side']['by_kind'][s.kind[q]] = v['side']['by_kind'].get(s.kind[q], 0) + 1
        mir = {(x, 2 * YC - y, z): c for (x, y, z), c in s.side.items()}
        G = s.G > 0
        ov = 0
        for k in list(s.knee) + list(s.side) + list(mir):
            if G[k[0] - XA, k[1], k[2]]:
                ov += 1
        v['overlap_with_world'] = ov
        v['side_mirror_overlap'] = sum(1 for k in mir if k in s.side or k in s.knee)
        v['side_min_y'] = min(k[1] for k in s.side)
        v['knee_mirror_mismatch'] = sum(1 for (x, y, z), c in s.knee.items() if s.knee.get((x, 2 * YC - y, z)) != c)
        A = G.copy()
        N = np.zeros_like(G)
        for k in list(s.knee) + list(s.side) + list(mir):
            A[k[0] - XA, k[1], k[2]] = True
            N[k[0] - XA, k[1], k[2]] = True
        lab, n = ndimage.label(A)
        base = set(np.unique(lab[G])) - {0}
        fl = [k for k in list(s.knee) + list(s.side) if lab[k[0] - XA, k[1], k[2]] not in base]
        v['floating'] = {'n': len(fl), 'by_kind': {}}
        for k in fl:
            kd = s.kind.get(k, '?')
            v['floating']['by_kind'][kd] = v['floating']['by_kind'].get(kd, 0) + 1
        v['floating']['first'] = [list(k) + [s.kind.get(k)] for k in fl[:8]]

        def cav(sol):
            l, nn = ndimage.label(~sol)
            e = set(np.unique(np.concatenate([l[0].ravel(), l[-1].ravel(), l[:, 0].ravel(), l[:, -1].ravel(), l[:, :, 0].ravel(), l[:, :, -1].ravel()]))) - {0}
            return int(nn - len(e))
        v['cavities_box'] = {'before': cav(G), 'after': cav(A)}
        bx = s.P['subworks']['side']['box']
        s.box = tuple(bx['at']) + tuple(bx['size'])
        out_box = [k for k in s.side if not all(s.box[a] <= k[a] < s.box[a] + s.box[a + 3] for a in range(3))]
        assert not out_box, ('一舷那件有格在固定的框外', out_box[:5])
        v['side_box'] = {'at': list(s.box[:3]), 'size': list(s.box[3:]), 'mirror_at_y': 321 - s.box[1] - s.box[4],
                         'used': [[min(k[a] for k in s.side), max(k[a] for k in s.side)] for a in range(3)]}
        v['hawse'] = s.hawse_at
        v['shield'] = s.shield_at
        v['cathead'] = s.cathead_at
        v['timbers'] = s.timbers
        v['scroll_length'] = round(s.scroll_len, 1)
        v['expect_assembly_after'] = s.read['voxels'] + len(s.knee) + 2 * len(s.side)
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'head')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        x0, y0, z0 = s.box[:3]
        for fname, rows, note in (
                ('knee', sorted((k[0], k[1], k[2], c) for k, c in s.knee.items()), 'knee of the head ＋ billethead（作品座標，at=0,0,0）'),
                ('side', sorted((k[0] - x0, k[1] - y0, k[2] - z0, c) for k, c in s.side.items()),
                 '船頭裝飾一舷（y > 160；自己的座標，at=%d,%d,%d；另一舷 mirror=y、at.y ＝ %d）' % (x0, y0, z0, 321 - y0 - s.box[4]))):
            p = os.path.join(out, fname + '.vox.txt')
            body = '\n'.join('%d,%d,%d,%d' % r for r in rows)
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（%d 格）\n' % (fname, note, len(rows)) + body + '\n')
            s.files[fname] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}


# ── 圖紙 ──
def all_cells(T, with_new=True):
    D = {}
    if with_new:
        D.update(T.knee)
        D.update(T.side)
        D.update({(x, 2 * YC - y, z): c for (x, y, z), c in T.side.items()})
    return D


def view(T, D, axis, rng_a, rng_b, depth_rng, flip_a=False):
    """正交投影：axis ＝ 'side'（從 +y 往 −y 看，橫軸 x）、'front'（從 +x 往 −x 看，橫軸 y，觀者左手邊 ＝ +y）、'top'（從上往下，橫軸 x、縱軸 y）。"""
    na, nb = rng_a[1] - rng_a[0], rng_b[1] - rng_b[0]
    img = np.zeros((nb, na, 3), np.uint8)
    img[:] = DD.PAPER
    G = T.G
    for ia in range(na):
        a = rng_a[0] + ia
        for ib in range(nb):
            b = rng_b[1] - 1 - ib
            for dd in depth_rng:
                if axis == 'side':
                    k = (a, dd, b)
                elif axis == 'front':
                    k = (dd, (rng_a[1] - 1 - ia) if flip_a else a, b)
                else:
                    k = (a, b, dd)
                if not (XA <= k[0] < XB and 0 <= k[1] < 320 and 0 <= k[2] < ZB):
                    continue
                c = D.get(k)
                if c is None and G[k[0] - XA, k[1], k[2]]:
                    c = int(G[k[0] - XA, k[1], k[2]])
                if c is not None:
                    img[ib, ia] = DP.rgb332(c)
                    break
    return img


def render_sheet(T, path):
    f12, f14, f18 = DD._font(13), DD._font(15), DD._font(20)
    D0, D1 = {}, all_cells(T)
    sc = 5
    xa, xb, za, zb = 618, 745, 58, 152
    # 視線一路走到另一舷（穿過空的 head 看得到對面的 rails；第一版停在中線，中間一塊是紙）
    side0 = Image.fromarray(view(T, D0, 'side', (xa, xb), (za, zb), range(319, -1, -1))).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)
    side1 = Image.fromarray(view(T, D1, 'side', (xa, xb), (za, zb), range(319, -1, -1))).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)
    ya, yb = YC - 55, YC + 56
    front = Image.fromarray(view(T, D1, 'front', (ya, yb), (za, zb), range(XB - 1, 600, -1), flip_a=True)).resize(((yb - ya) * sc, (zb - za) * sc), Image.NEAREST)
    top = Image.fromarray(view(T, D1, 'top', (xa, xb), (YC - 55, YC + 56), range(ZB - 1, 60, -1))).resize(((xb - xa) * sc, 111 * sc), Image.NEAREST)
    PADL = 50
    W = PADL + 2 * (xb - xa) * sc + 50 + 40
    H = 3000
    can = Image.new('RGB', (W, H), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), T.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '正交投影；每格 %d px；側面從 y > 160 那一舷看（x %d–%d、z %d–%d）' % (sc, xa, xb - 1, za, zb - 1), font=f12, fill=DD.INK)
    y = 66
    for i, (title, im) in enumerate((('現在（只有艏柱、gripe 平台）', side0), ('新圖紙 13 v1（側面）', side1))):
        x0 = PADL + i * ((xb - xa) * sc + 50)
        dr.text((x0, y), title, font=f14, fill=DD.INK)
        can.paste(im, (x0, y + 22))
        for z in range(60, zb, 10):
            yy = y + 22 + (zb - 1 - z) * sc + sc // 2
            dr.line([(x0 - 6, yy), (x0 - 1, yy)], fill=(130, 130, 130))
            if i == 0:
                dr.text((x0 - 30, yy - 7), str(z), font=f12, fill=(130, 130, 130))
        for x in range(620, xb, 20):
            dr.text((x0 + (x - xa) * sc - 8, y + 22 + (zb - za) * sc + 2), str(x), font=f12, fill=(130, 130, 130))
    y += 22 + (zb - za) * sc + 30
    dr.text((PADL, y), '正前方（往船尾看；觀者左手邊 ＝ y > 160）', font=f14, fill=DD.INK)
    can.paste(front, (PADL, y + 22))
    x0 = PADL + (yb - ya) * sc + 50
    dr.text((x0, y), '俯視（上 ＝ y > 160）', font=f14, fill=DD.INK)
    can.paste(top, (x0, y + 22))
    y += 22 + max((zb - za) * sc, 111 * sc) + 24
    v = T.v
    P = T.P
    lines = [
        'knee＋billethead %d 格（knee %d、billethead %d）；一舷 %d 格（%s）—— 兩舷 %d' % (
            v['knee']['cells'], v['knee']['by_kind']['knee'], v['knee']['by_kind']['billethead'], v['side']['cells'],
            '、'.join('%s %d' % kv for kv in sorted(v['side']['by_kind'].items())), 2 * v['side']['cells']),
        'knee：前緣照 11 號 cutwater、上緣照上 cheek（T_a），厚 5（最前 2 格收成 3）；billethead 中心 %s、半徑 %.1f、寬 7；hawse 圈 %s' % (
            P['billethead']['center'], P['billethead']['radius'], ['x %d dy %.0f z %.1f' % (h['x'], h['dy'], h['z']) for h in v['hawse']]),
        'rails 平面：%s；cathead 根 %s → 端 %s；head timbers %s' % (P['rails']['plan'], v['cathead']['root'], v['cathead']['end'], P['rails']['timbers_x']),
        '重疊 %d、浮空 %d、knee 鏡像差 %d、空腔 %s；組裝件預期 %d 格' % (
            v['overlap_with_world'], v['floating']['n'], v['knee_mirror_mismatch'], v['cavities_box'], v['expect_assembly_after']),
        '出處：11 號（1927）sheer／body plan 讀圖；USS Constitution Museum 與 Plan 24779／30155／24825／25175；照片 2011／2013／2023；設計決定見 plan.json head.decisions',
    ]
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, W, y + 20))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    T = Head(design)
    T.build_knee()
    T.build_side()
    v = T.verify()
    T.write()
    v['files'] = T.files
    json.dump(v, open(os.path.join(design, 'verify_head.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(T, os.path.join(design, 'sheet13_head_v1.png'))
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
