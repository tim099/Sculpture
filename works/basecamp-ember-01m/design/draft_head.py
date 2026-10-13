# 餘燼號 階段九 船頭（plan.json head_build；新圖紙 10）—— 憲法號 draft_head.py（新圖紙 13）照換算改寫
#   曲線現讀憲法號 plan.json 的 head 段，照 head_build.map 換到餘燼號座標：x ＋66；z ≤ 63 不動、63..131 拉到 63..154、≥ 131 ＋23
#   （船殼在 z 109 插了 23 層 ⇒ knee 跟著船頭變高）。配色：憲法號的白 → 金；盾牌 → 火焰紋章；billethead 不做（換成船首像，另一支 draft_figurehead.py）。
#   現況 ＝ 組裝件藏起這一階段的關聯（套用之後重跑逐位元組一樣）。
#   ⇒ masks/head/knee.vox.txt（子作品，at=0,0,0）、masks/head/side.vox.txt（一舷，自己的座標；另一舷 mirror=y）、
#      masks/head/knee_anchors.json（bobstay）、verify_head.json、sheet10_head_v1.png
# 用法：python -I draft_head.py <design 資料夾>
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from scipy.interpolate import PchipInterpolator
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP                               # noqa: E402
from draft_ladders import existing_links, export_hidden  # noqa: E402

YC = 160
XA, XB, ZB = 626, 866, 230         # 只看船頭這一塊
PAPER, INK = (250, 248, 240), (30, 30, 30)


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


class Mapper:
    """憲法號 (x, z) → 餘燼號 (x, z)"""
    def __init__(s, m):
        s.dx = m['dx']
        s.z0 = m['z_keep_below']
        s.za, s.zb = m['z_stretch_to']
        s.sh = m['z_shift_above']
        assert abs(s.za + s.sh - s.zb) < 1e-9, '拉伸段的上端要接上整段平移'

    def z(s, z):
        if z <= s.z0:
            return float(z)
        if z < s.za:
            return s.z0 + (z - s.z0) * (s.zb - s.z0) / (s.za - s.z0)
        return float(z + s.sh)

    def x(s, x):
        return float(x + s.dx)

    def pts(s, P):
        return [[round(s.x(x), 3), round(s.z(z), 3)] for x, z in P]


class Head:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.H = s.plan['head_build']
        s.C0 = json.load(open(os.path.join(DP.CON_DESIGN, 'plan.json'), encoding='utf-8'))['head']
        s.M = Mapper(s.H['map'])
        s.P = s.mapped()
        have = set(existing_links(s.H['assembly']))
        s.hidden = [h for h in s.H['hide_links'] if h in have]
        a = export_hidden(s.H['assembly'], s.hidden)
        assert len(a) == s.H['assembly_voxels'], ('組裝件現況對不上', len(a), s.H['assembly_voxels'])
        s.read = {'hidden': s.hidden, 'voxels': int(len(a))}
        m = a[(a[:, 0] >= XA) & (a[:, 0] < XB) & (a[:, 2] < ZB)]
        s.G = np.zeros((XB - XA, 320, ZB), np.uint8)
        s.G[m[:, 0] - XA, m[:, 1], m[:, 2]] = m[:, 3]
        s.col = s.H['colors']
        s.knee = {}            # (x,y,z) → color
        s.side = {}            # 一舷（y > 160）
        s.kind = {}

    def mapped(s):
        """憲法號 head 段 → 餘燼號座標（只換用到的數值）"""
        C, M = s.C0, s.M
        K = dict(C['knee'])
        K['front'], K['top'] = M.pts(K['front']), M.pts(K['top'])
        ch = {'upper': {'a': M.pts(C['cheeks']['upper']['a']), 'thick': C['cheeks']['upper']['thick']},
              'lower': {'b': M.pts(C['cheeks']['lower']['b']), 'thick': C['cheeks']['lower']['thick']},
              'aft_x': M.x(C['cheeks']['aft_x']), 'proud': C['cheeks']['proud']}
        tb = dict(C['trailboard'])
        tb['u_from_x'] = M.x(tb['u_from_x'])
        tb['u_to_x'] = M.x(722.0)
        hw = dict(C['hawse'])
        hw['front_view'] = [[dy, round(M.z(z), 3)] for dy, z in hw['front_view']]
        R = dict(C['rails'])
        R['plan'] = [[M.x(x), dy] for x, dy in R['plan']]
        R['top'] = {'upper': M.pts(R['top']['upper']), 'lower': M.pts(R['top']['lower'])}
        R['main'] = {'upper': M.pts(R['main']['upper']), 'lower': M.pts(R['main']['lower'])}
        R['timbers_x'] = [M.x(x) for x in R['timbers_x']]
        R['panel_from_x'] = M.x(643.0)
        R['timber_from_x'] = M.x(645.0)
        ct = dict(C['cathead'])
        ct['root'] = [M.x(ct['root'][0]), round(M.z(ct['root'][1]), 3)]
        em = dict(s.H['emblem'])
        em['center_x'] = M.x(C['shield']['center_x'])
        return {'knee': K, 'cheeks': ch, 'trailboard': tb, 'hawse': hw, 'rails': R, 'cathead': ct, 'emblem': em,
                'knee_min_y_x': M.x(667), 'hawse_search_x': [M.x(640), M.x(680)],
                'bobstays': [[M.x(707), M.z(96)], [M.x(713), M.z(104)]]}

    def S(s):
        """現況 ＋ knee（rails 之前的實心）。"""
        A = s.G > 0
        for (x, y, z) in s.knee:
            A[x - XA, y, z] = True
        return A

    # ── knee ──
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
                xs = xs_all.max() + XA                 # 那一欄最前面的實心（艏柱／gripe）
                for x in range(xs + 1, int(math.floor(xfront + 0.5)) + 1):
                    if z > zt(x):
                        continue
                    if abs(dy) > K['edge_half_width'] and x > xfront - K['edge_depth']:
                        continue
                    if Gs[x - XA, y, z]:
                        continue
                    s.knee[(x, y, z)] = s.col['black'] if z >= 63 else s.col['copper']
                    s.kind[(x, y, z)] = 'knee'
        # bobstay 固定點：換算後那一層 knee 中線最前面那格
        s.anchors = []
        for i, (bx, bz) in enumerate(s.P['bobstays']):
            z = int(round(bz))
            xs = [x for (x, y, zz) in s.knee if y == YC and zz == z]
            s.anchors.append({'name': 'bobstay-%d' % (i + 1), 'at': [max(xs), YC, z], 'from_constitution': [round(bx, 2), round(bz, 2)]})

    # ── 外殼（y > 160 那一舷）──
    def shells(s, zr, xr, kmax=2):
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
        sh = s.shells((75, 176), (666, 856))
        kn = P['knee']
        min_y = lambda x: YC + kn['half_width'] + 1 if x >= P['knee_min_y_x'] else YC + 1
        gold = s.col['gold']
        # cheeks（金）
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
        s.decal(sh, cheek_up, C['proud'], lambda x, z: gold, 'cheek', min_y)
        s.decal(sh, cheek_lo, C['proud'], lambda x, z: gold, 'cheek', min_y)
        # hawse 圈（照正視的 (dy, z) 找到船殼表面上的點）
        H = P['hawse']
        s.hawse_at = []
        xa_, xb_ = (int(v) for v in P['hawse_search_x'])
        for dyc, zc in H['front_view']:
            z0 = int(round(zc))
            xs = [x for x in range(xa_, xb_) if s.outer_dy(A, x, z0) >= 0]
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
            s.decal(sh, ring, H['proud'], lambda x, z: s.col[s.H['hawse']['ring']], 'hawse', min_y)

            def hole(x, z, dyc=dyc, zc=zc, fac=fac):
                ody = s.outer_dy(A, x, z)
                return ody >= 0 and math.hypot((ody - dyc) * fac, z - zc) < H['r_in']
            # 孔：圈裡面貼一層黑（餘燼號的 hawse 在暗紅帶上 —— 灰圈貼紅底像字母；金圈＋黑孔）
            s.decal(sh, hole, 1, lambda x, z: s.col[s.H['hawse']['hole']], 'hawse-hole', min_y)
        # 火焰紋章（盾牌的位置；knee 那一面，直立）
        EM = P['emblem']
        rows = EM['rows']
        hgt, wid = len(rows), len(rows[0])
        cxs = EM['center_x']
        zt_a = poly_interp(Ta, 0, 1)
        zb_b = poly_interp(Bb, 0, 1)
        zmid = (zt_a(cxs) - tu + zb_b(cxs)) / 2
        s.emblem_at = {'x': cxs, 'z_mid': round(float(zmid), 2), 'inner': [round(float(zb_b(cxs)), 2), round(float(zt_a(cxs) - tu), 2)]}
        top = int(round(zmid + (hgt - 1) / 2))
        left = int(round(cxs - (wid - 1) / 2))
        lg = EM['legend']
        emblem = {}
        for i, row in enumerate(rows):
            for j, ch in enumerate(row):
                if ch != '.':
                    emblem[(left + j, top - i)] = s.col[lg[ch]]
        s.decal(sh, lambda x, z: (x, z) in emblem, EM['proud'], lambda x, z: emblem[(x, z)], 'emblem', min_y)
        # trailboard 卷草（金；兩道 cheek 之間，從前面那個 hawse 圈的前緣往前）
        TB = P['trailboard']
        sc = TB['scroll']
        xs_c = np.arange(TB['u_from_x'], TB['u_to_x'], 0.25)
        up_in = zt_a(xs_c) - tu
        lo_in = zb_b(xs_c)
        ok = up_in - lo_in > 2 * TB['min_half_height']
        xs_c, mid, hh = xs_c[ok], ((up_in + lo_in) / 2)[ok], ((up_in - lo_in) / 2)[ok]
        u = np.concatenate([[0], np.cumsum(np.hypot(np.diff(xs_c), np.diff(mid)))])
        s.scroll_len = float(u[-1])
        lam = sc['wavelength']
        tx = np.gradient(xs_c)
        tz = np.gradient(mid)
        tn = np.hypot(tx, tz)
        tx, tz = tx / tn, tz / tn
        hp = hh * np.abs(tx)                      # 垂直於帶子的半高
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
            vt = sk * sc['stem_amp'] * h
            uc, vc = up + R * 0.6, vt - sk * R
            th0 = math.atan2(vt - vc, up - uc)
            tt = np.linspace(0, 1, 80)
            ang = th0 - sk * 2 * np.pi * sc['curl_turns'] * tt
            rr = R * (1 - 0.5 * tt)
            cpts.append(np.stack([uc + rr * np.cos(ang), vc + rr * np.sin(ang)], 1))
        cpts = np.concatenate(cpts)
        em_box = (left - 1, left + wid, top - hgt, top + 1)

        def scroll_mask(x, z):
            if not (xs_c[0] <= x <= xs_c[-1]):
                return False
            if em_box[0] <= x <= em_box[1] and em_box[2] <= z <= em_box[3]:
                return False
            du = signed_dist(np.array(x + 0.0), np.array(z + 0.0), Ta)
            dl = signed_dist(np.array(x + 0.0), np.array(z + 0.0), Bb)
            if not (du > tu + 0.15 and dl < -0.35):
                return False
            dd = np.hypot(xs_c - x, mid - z)
            i = int(np.argmin(dd))
            uu = u[i] + (x - xs_c[i]) * tx[i] + (z - mid[i]) * tz[i]
            vv = -(x - xs_c[i]) * tz[i] + (z - mid[i]) * tx[i]
            near = np.abs(cpts[:, 0] - uu) <= 1.5
            return bool(near.any() and np.min(np.hypot(cpts[near, 0] - uu, cpts[near, 1] - vv)) <= sc['line_half'])
        s.decal(sh, scroll_mask, TB['proud'], lambda x, z: gold, 'scroll', min_y)
        s.build_cathead(A)
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
        s.cathead_cells = []
        for x in range(int(rx) - 6, int(rx + L) + 6):
            for y in range(YC, 320):
                for z in range(int(rz) - 6, int(rz + L * math.sin(b)) + 7):
                    p = np.array([x, y, z], float) - o
                    uu, vv, ww = p @ d, p @ v, p @ w
                    if 0 <= uu <= L and abs(vv) <= hf and abs(ww) <= hf:
                        c = s.col['gold'] if uu > L - 1 else s.col['black']
                        if s.put_side(x, y, z, c, 'cathead'):
                            s.cathead_cells.append((x, y, z, uu))

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
        panel_poly = R['top']['lower'] + [p for p in R['main']['upper'] if p[0] >= R['panel_from_x']][::-1]
        allp = np.array(top_poly + main_poly, float)
        xs = np.arange(int(allp[:, 0].min()) - 2, int(allp[:, 0].max()) + 3)
        zs = np.arange(int(allp[:, 1].min()) - 2, int(allp[:, 1].max()) + 3)
        XX, ZZ = np.meshgrid(xs, zs, indexing='ij')
        m_top = in_polygon(XX + 0.0, ZZ + 0.0, top_poly)
        m_main = in_polygon(XX + 0.0, ZZ + 0.0, main_poly)
        m_panel = in_polygon(XX + 0.0, ZZ + 0.0, panel_poly) & ~m_top & ~m_main

        def ybase(x, z):
            yb = YC + int(round(dy_plan(x)))
            ody = s.outer_dy(A, x, z)
            if ody >= 0:
                yb = max(yb, YC + ody + 1)
            return yb
        for name, Mk in (('rail-top', m_top), ('rail-main', m_main)):
            edge = Mk & ~ndimage.binary_erosion(Mk, ndimage.generate_binary_structure(2, 1), border_value=0)
            for i, k in np.argwhere(Mk):
                x, z = int(xs[i]), int(zs[k])
                yb = ybase(x, z)
                # 最上一道黑芯金邊；main rail 全金
                c = s.col['gold'] if (edge[i, k] or name == 'rail-main') else s.col['black']
                for t in range(R['rail_thick']):
                    s.put_side(x, yb + t, z, c, name)
        for i, k in np.argwhere(m_panel):
            x, z = int(xs[i]), int(zs[k])
            yb = ybase(x, z)
            for t in range(R['panel_thick']):
                s.put_side(x, yb + t, z, s.col['black'], 'panel')
        # head timbers：上 cheek（knee 那一面）→ main rail 下緣
        zt_a = poly_interp(s.P['cheeks']['upper']['a'], 0, 1)
        ml = np.array([p for p in R['main']['lower'] if p[0] >= R['timber_from_x']], float)
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
                    for ax in range(3):
                        if q[ax] != prev[ax]:
                            mid = list(prev)
                            mid[ax] = q[ax]
                            s.put_side(*mid, s.col['gold'], 'timber')
                            prev = tuple(mid)
                s.put_side(*q, s.col['gold'], 'timber')
                prev = q

    # ── 驗 ──
    def verify(s):
        v = {'read': s.read, 'map': s.H['map']}
        v['knee'] = {'cells': len(s.knee), 'colors': {str(c): sum(1 for q in s.knee.values() if q == c) for c in sorted(set(s.knee.values()))},
                     'x': [min(k[0] for k in s.knee), max(k[0] for k in s.knee)], 'z': [min(k[2] for k in s.knee), max(k[2] for k in s.knee)]}
        v['side'] = {'cells': len(s.side), 'by_kind': {}, 'colors': {str(c): sum(1 for q in s.side.values() if q == c) for c in sorted(set(s.side.values()))}}
        for q in s.side:
            v['side']['by_kind'][s.kind[q]] = v['side']['by_kind'].get(s.kind[q], 0) + 1
        mir = {(x, 2 * YC - y, z): c for (x, y, z), c in s.side.items()}
        G = s.G > 0
        v['overlap_with_world'] = sum(1 for k in list(s.knee) + list(s.side) + list(mir) if G[k[0] - XA, k[1], k[2]])
        v['side_mirror_overlap'] = sum(1 for k in mir if k in s.side or k in s.knee)
        v['side_min_y'] = min(k[1] for k in s.side)
        v['knee_mirror_mismatch'] = sum(1 for (x, y, z), c in s.knee.items() if s.knee.get((x, 2 * YC - y, z)) != c)
        A = G.copy()
        for k in list(s.knee) + list(s.side) + list(mir):
            A[k[0] - XA, k[1], k[2]] = True
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
        bx = s.H['subworks']['side']['box']
        s.box = tuple(bx['at']) + tuple(bx['size'])
        out_box = [k for k in s.side if not all(s.box[a] <= k[a] < s.box[a] + s.box[a + 3] for a in range(3))]
        assert not out_box, ('一舷那件有格在固定的框外', out_box[:5])
        v['side_box'] = {'at': list(s.box[:3]), 'size': list(s.box[3:]), 'mirror_at_y': 321 - s.box[1] - s.box[4],
                         'used': [[min(k[a] for k in s.side), max(k[a] for k in s.side)] for a in range(3)]}
        v['hawse'] = s.hawse_at
        v['emblem'] = s.emblem_at
        v['cathead'] = s.cathead_at
        v['timbers'] = s.timbers
        v['knee_anchors'] = s.anchors
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
                ('knee', sorted((k[0], k[1], k[2], c) for k, c in s.knee.items()), 'knee of the head（作品座標，at=0,0,0）'),
                ('side', sorted((k[0] - x0, k[1] - y0, k[2] - z0, c) for k, c in s.side.items()),
                 '船頭裝飾一舷（y > 160；自己的座標，at=%d,%d,%d；另一舷 mirror=y、at.y ＝ %d）' % (x0, y0, z0, 321 - y0 - s.box[4]))):
            p = os.path.join(out, fname + '.vox.txt')
            body = '\n'.join('%d,%d,%d,%d' % r for r in rows)
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（%d 格）\n' % (fname, note, len(rows)) + body + '\n')
            s.files[fname] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        p = os.path.join(out, 'knee_anchors.json')
        open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(s.anchors, ensure_ascii=False, indent=1) + '\n')


# ── 圖紙 ──
def view(T, D, axis, rng_a, rng_b, depth_rng, flip_a=False):
    """正交投影：axis ＝ 'side'（從 +y 往 −y 看，橫軸 x）、'front'（從 +x 往 −x 看，橫軸 y）、'top'（從上往下，橫軸 x、縱軸 y）。"""
    na, nb = rng_a[1] - rng_a[0], rng_b[1] - rng_b[0]
    img = np.zeros((nb, na, 3), np.uint8)
    img[:] = PAPER
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
                    img[ib, ia] = DP.rgb(c)
                    break
    return img


def render_sheet(T, path, extra=None):
    f12, f14, f18 = DP.font(13), DP.font(15), DP.font(20)
    D1 = {}
    D1.update(T.knee)
    D1.update(T.side)
    D1.update({(x, 2 * YC - y, z): c for (x, y, z), c in T.side.items()})
    if extra:
        D1.update(extra)
    sc = 5
    xa, xb, za, zb = 690, 830, 58, 190
    side0 = Image.fromarray(view(T, {}, 'side', (xa, xb), (za, zb), range(319, -1, -1))).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)
    side1 = Image.fromarray(view(T, D1, 'side', (xa, xb), (za, zb), range(319, -1, -1))).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)
    ya, yb = YC - 60, YC + 61
    front = Image.fromarray(view(T, D1, 'front', (ya, yb), (za, zb), range(XB - 1, 660, -1), flip_a=True)).resize(((yb - ya) * sc, (zb - za) * sc), Image.NEAREST)
    top = Image.fromarray(view(T, D1, 'top', (xa, xb), (YC - 60, YC + 61), range(ZB - 1, 60, -1))).resize(((xb - xa) * sc, 121 * sc), Image.NEAREST)
    PADL = 50
    W = PADL + 2 * (xb - xa) * sc + 50 + 40
    H = 3600
    can = Image.new('RGB', (W, H), PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), T.H['title'], font=f18, fill=INK)
    dr.text((PADL, 40), '正交投影；每格 %d px；側面從 y > 160 那一舷看（x %d–%d、z %d–%d）' % (sc, xa, xb - 1, za, zb - 1), font=f12, fill=INK)
    y = 66
    for i, (title, im) in enumerate((('現在（只有艏柱與 gripe 平台）', side0), ('新圖紙 10 v1（側面）', side1))):
        x0 = PADL + i * ((xb - xa) * sc + 50)
        dr.text((x0, y), title, font=f14, fill=INK)
        can.paste(im, (x0, y + 22))
        for z in range(60, zb, 10):
            yy = y + 22 + (zb - 1 - z) * sc + sc // 2
            dr.line([(x0 - 6, yy), (x0 - 1, yy)], fill=(130, 130, 130))
            if i == 0:
                dr.text((x0 - 30, yy - 7), str(z), font=f12, fill=(130, 130, 130))
        for x in range(700, xb, 20):
            dr.text((x0 + (x - xa) * sc - 8, y + 22 + (zb - za) * sc + 2), str(x), font=f12, fill=(130, 130, 130))
    y += 22 + (zb - za) * sc + 30
    dr.text((PADL, y), '正前方（往船尾看）', font=f14, fill=INK)
    can.paste(front, (PADL, y + 22))
    x0 = PADL + (yb - ya) * sc + 50
    dr.text((x0, y), '俯視（上 ＝ y > 160）', font=f14, fill=INK)
    can.paste(top, (x0, y + 22))
    y += 22 + max((zb - za) * sc, 121 * sc) + 24
    v = T.v
    lines = [
        'knee %d 格；一舷 %d 格（%s）—— 兩舷 %d' % (
            v['knee']['cells'], v['side']['cells'], '、'.join('%s %d' % kv for kv in sorted(v['side']['by_kind'].items())), 2 * v['side']['cells']),
        '換算：x ＋66；z ≤ 63 不動、63..131 → 63..154、≥ 131 ＋23；hawse 圈 %s；火焰紋章 x %.0f、z %.1f' % (
            ['x %d dy %.0f z %.1f' % (h['x'], h['dy'], h['z']) for h in v['hawse']], v['emblem']['x'], v['emblem']['z_mid']),
        'cathead 根 %s → 端 %s；head timbers %s；bobstay 固定點 %s' % (v['cathead']['root'], v['cathead']['end'], T.P['rails']['timbers_x'], [a['at'] for a in v['knee_anchors']]),
        '重疊 %d、浮空 %d、knee 鏡像差 %d、空腔 %s；組裝件預期 %d 格（不含船首像與錨）' % (
            v['overlap_with_world'], v['floating']['n'], v['knee_mirror_mismatch'], v['cavities_box'], v['expect_assembly_after']),
        '出處：憲法號新圖紙 13（11 號 1927 sheer／body plan 讀圖）照換算；配色白 → 金、盾牌 → 火焰；設計決定見 plan.json head_build',
    ]
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=INK)
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
    render_sheet(T, os.path.join(design, 'sheet10_head_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('timbers',)}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
