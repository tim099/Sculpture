# 新圖紙產生器（TASK-0482）：plan.json（設計參數）⇒ 圖紙 PNG、與原圖的對照圖、雕刻遮罩、驗證讀數。
# 用法：python -I draft.py <design 資料夾> [--ref <02 號圖 JPG 的絕對路徑>]
#   · 曲線一律由 plan.json 的參數算出來（圓弧、切線、直線），⛔ 不讀原圖的線 —— 原圖只拿來畫對照圖。
#   · 遮罩給 `sculpture op=stampimg facing=y+` 用：⚠ y± 貼片的 v 軸不翻轉 ⇒ 遮罩第 0 列 ＝ 最低的 z（圖看起來上下顛倒）。
#   · 讀數寫進 verify.json：設計曲線離原圖描點多遠、每個部件幾格、跟既有龍骨的衝突格。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
SS = 3                      # 超取樣倍數（畫大再縮，線才平滑）
INK = (38, 42, 56)
PAPER = (247, 243, 231)
GRID1 = (214, 222, 230)
GRID5 = (170, 186, 204)
OAK = (226, 199, 152)
DARK = (176, 128, 92)
RED = (200, 40, 40)
CONSTR = (90, 120, 170)


# ───────────────────────── 曲線 ─────────────────────────
def cut_at(pts, z_top):
    """沿曲線（z 單調遞增）裁到 z_top，交點內插。"""
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        if q[1] <= z_top:
            out.append(q)
            continue
        if p[1] < z_top:
            t = (z_top - p[1]) / (q[1] - p[1])
            out.append((p[0] + t * (q[0] - p[0]), z_top))
        break
    return out


class Biarc:
    """下弧在 x=a 與水平線 z=base 相切起彎，上弧（圓心 C2、半徑 R2）與下弧內切；下弧半徑由相切條件解出。"""
    def __init__(s, c):
        s.base, s.a, s.R2 = c['base_z'], c['tangent_x'], c['r2']
        s.C2 = np.array(c['center2'], float)
        dx, dz = s.C2[0] - s.a, s.C2[1] - s.base
        s.R1 = (s.R2 ** 2 - dx * dx - dz * dz) / (2 * (s.R2 - dz))
        s.C1 = np.array([s.a, s.base + s.R1])
        u = s.C1 - s.C2
        u /= np.linalg.norm(u)
        s.J = s.C1 + s.R1 * u
        s.thJ = math.atan2(u[1], u[0])
        assert -math.pi / 2 < s.thJ < 0, 'junction 不在下弧右下象限'

    def points(s, x_back, z_top, step=0.1):
        pts = [(x_back, s.base), (s.a, s.base)]
        n = max(8, int(s.R1 * (s.thJ + math.pi / 2) / step))
        for i in range(1, n + 1):
            t = -math.pi / 2 + (s.thJ + math.pi / 2) * i / n
            pts.append((s.C1[0] + s.R1 * math.cos(t), s.C1[1] + s.R1 * math.sin(t)))
        t_end = math.asin(min(1.0, (min(z_top + 1, s.C2[1]) - s.C2[1]) / s.R2))
        n = max(8, int(s.R2 * (t_end - s.thJ) / step))
        for i in range(1, n + 1):
            t = s.thJ + (t_end - s.thJ) * i / n
            pts.append((s.C2[0] + s.R2 * math.cos(t), s.C2[1] + s.R2 * math.sin(t)))
        return cut_at(pts, z_top)


class ArcLine:
    """圓弧在 x=a 與水平線相切起彎，到角度 phi 後接切線直線。"""
    def __init__(s, c):
        s.base, s.a, s.R = c['base_z'], c['tangent_x'], c['r']
        s.phi = math.radians(c['phi_deg'])
        s.C = np.array([s.a, s.base + s.R])
        s.J = s.C + s.R * np.array([math.cos(s.phi), math.sin(s.phi)])
        s.d = np.array([-math.sin(s.phi), math.cos(s.phi)])
        s.angle_deg = math.degrees(math.atan2(s.d[1], s.d[0]))

    def points(s, x_back, z_top, step=0.1):
        pts = [(x_back, s.base), (s.a, s.base)]
        n = max(8, int(s.R * (s.phi + math.pi / 2) / step))
        for i in range(1, n + 1):
            t = -math.pi / 2 + (s.phi + math.pi / 2) * i / n
            pts.append((s.C[0] + s.R * math.cos(t), s.C[1] + s.R * math.sin(t)))
        L = (z_top + 1 - s.J[1]) / s.d[1]
        pts.append(tuple(s.J + L * s.d))
        return cut_at(pts, z_top)


class Line:
    def __init__(s, c):
        s.x0, s.z0 = c['through']
        s.k = math.tan(math.radians(c['rake_deg']))   # 往上每格往船尾（-X）退 k 格

    def x(s, z):
        return s.x0 - s.k * (z - s.z0)


class Arc:
    def __init__(s, c):
        s.C = np.array(c['center'], float)
        s.R = c['r']
        s.z = c['z']

    def points(s, step=0.2):
        out = []
        z = s.z[0]
        while z <= s.z[1] + 1e-9:
            out.append((s.C[0] + math.sqrt(s.R ** 2 - (z - s.C[1]) ** 2), z))
            z += step
        return out


class ArcT:
    """單一圓弧：在 x=a 與水平線 z=base 相切，往 dir（+1 ＝ 船頭、-1 ＝ 船尾）升起。"""
    def __init__(s, c):
        s.base, s.a, s.R, s.dir = c['base_z'], c['tangent_x'], c['r'], c.get('dir', 1)

    def z(s, x):
        d = (x - s.a) * s.dir
        return s.base if d <= 0 else s.base + s.R - math.sqrt(max(0.0, s.R ** 2 - d * d))

    def points(s, x0, x1, step=0.1):
        n = max(2, int(abs(x1 - x0) / step))
        return [(x0 + (x1 - x0) * i / n, s.z(x0 + (x1 - x0) * i / n)) for i in range(n + 1)]


class BiarcFree:
    """雙圓弧（四個參數）：下弧在 x=a 與 z=base 相切、往 dir 升起，到角度 phi 接上半徑 r2 的上弧。"""
    def __init__(s, c):
        s.base, s.a, s.R1, s.R2, s.dir = c['base_z'], c['tangent_x'], c['r1'], c['r2'], c.get('dir', 1)
        s.phi = math.radians(c['phi_deg'])
        s.C1 = np.array([s.a, s.base + s.R1])
        u = np.array([s.dir * math.cos(s.phi), math.sin(s.phi)])
        s.J = s.C1 + s.R1 * u
        s.C2 = s.J - s.R2 * u

    def points(s, x_back, z_top, step=0.1):
        pts = [(x_back, s.base), (s.a, s.base)]
        n = max(8, int(s.R1 * (s.phi + math.pi / 2) / step))
        for i in range(1, n + 1):
            t = -math.pi / 2 + (s.phi + math.pi / 2) * i / n
            pts.append((s.C1[0] + s.dir * s.R1 * math.cos(t), s.C1[1] + s.R1 * math.sin(t)))
        t_end = math.asin(max(-1.0, min(1.0, (z_top + 1 - s.C2[1]) / s.R2)))
        n = max(8, int(s.R2 * max(0.0, t_end - s.phi) / step))
        for i in range(1, n + 1):
            t = s.phi + (t_end - s.phi) * i / n
            pts.append((s.C2[0] + s.dir * s.R2 * math.cos(t), s.C2[1] + s.R2 * math.sin(t)))
        return cut_at(pts, z_top)


def from_x(pts, x0, d):
    """沿曲線（x 朝 d 單調）從 x=x0 開始取（交點內插）。"""
    out = []
    for p, q in zip(pts, pts[1:]):
        if (q[0] - x0) * d < 0:
            continue
        if not out:
            t = 0.0 if q[0] == p[0] else (x0 - p[0]) / (q[0] - p[0])
            t = min(1.0, max(0.0, t))
            out.append((x0, p[1] + t * (q[1] - p[1])))
        out.append(q)
    return out


def z_on(pts, x):
    """曲線（x 單調遞增）在 x 的 z。"""
    for p, q in zip(pts, pts[1:]):
        if p[0] <= x <= q[0] and q[0] != p[0]:
            return p[1] + (q[1] - p[1]) * (x - p[0]) / (q[0] - p[0])
    raise ValueError('x=%g 不在曲線範圍內' % x)


def meet(f, g, lo, hi):
    """二分法：f(x) − g(x) 在 [lo, hi] 變號的那一點。"""
    a, b = lo, hi
    fa = f(a) - g(a)
    for _ in range(80):
        m = (a + b) / 2
        fm = f(m) - g(m)
        if (fm > 0) == (fa > 0):
            a, fa = m, fm
        else:
            b = m
    return (a + b) / 2


def build(plan):
    cv = plan['curves']
    C = {'T': Biarc(cv['T']), 'F': Biarc(cv['F']), 'O': ArcLine(cv['O']), 'A': Arc(cv['A']),
         'SPa': Line(cv['SPa']), 'SPf': Line(cv['SPf'])}
    P = plan['parts']
    st, gr, sp = P['stem'], P['gripe'], P['sternpost']
    polys = {
        'stem': C['F'].points(st['back_x'], st['head_z']) + C['T'].points(st['back_x'], st['head_z'])[::-1],
        'gripe': C['O'].points(gr['back_x'], gr['top_z']) + C['F'].points(gr['back_x'], gr['top_z'])[::-1],
        'sternpost': [(C['SPa'].x(sp['heel_z']), sp['heel_z']), (C['SPf'].x(sp['heel_z']), sp['heel_z']),
                      (C['SPf'].x(sp['head_z']), sp['head_z']), (C['SPa'].x(sp['head_z']), sp['head_z'])],
    }
    if 'inner_post' in P:           # 階段三（新圖紙 v2）
        C['Bf'], C['Af'] = Biarc(cv['Bf']), ArcT(cv['Af'])
        C['Ba'], C['Aa'] = BiarcFree(cv['Ba']), ArcT(cv['Aa'])
        C['IP'] = Line(cv['IP'])
        ip, ad, fd, ap = P['inner_post'], P['aft_deadwood'], P['fore_deadwood'], P['apron']
        polys['inner_post'] = [(C['SPf'].x(ip['heel_z']), ip['heel_z']), (C['IP'].x(ip['heel_z']), ip['heel_z']),
                               (C['IP'].x(ip['head_z']), ip['head_z']), (C['SPf'].x(ip['head_z']), ip['head_z'])]
        b_aft = from_x(C['Ba'].points(C['Ba'].a + 200, ad['cap_z']), ad['fwd_x'], -1)   # 平直段在切點的船頭側
        polys['aft_deadwood'] = ([(C['IP'].x(8.0), 8.0), (ad['fwd_x'], 8.0)] + b_aft
                                 + [(C['IP'].x(ad['cap_z']), ad['cap_z'])])
        Tp = C['T'].points(fd['aft_x'], 130)
        x_meet = meet(lambda x: z_on(Tp, x), C['Af'].z, C['T'].a + 1, C['T'].a + 80)
        z_meet = C['Af'].z(x_meet)
        C['meet_AT'] = (x_meet, z_meet)
        t_low = C['T'].points(C['T'].a, z_meet)
        a_pts = C['Af'].points(fd['aft_x'], x_meet)
        polys['fore_deadwood'] = [(fd['aft_x'], 8.0)] + t_low + a_pts[::-1]
        polys['apron'] = (a_pts + C['T'].points(C['T'].a, ap['top_z'])[len(t_low) - 1:]
                          + C['Bf'].points(ap['aft_x'], ap['top_z'])[::-1])
    return C, polys


def keel_outline(plan):
    k = plan['existing']['keel']
    fr = {int(z): x for z, x in k['front_by_layer'].items()}
    z0, z1 = k['z']
    pts = [(k['x_from'], z0)]
    for z in range(z0, z1 + 1):            # 前緣逐層（格的右緣 = front+1）
        pts.append((fr[z] + 1, z))
        pts.append((fr[z] + 1, z + 1))
    pts.append((k['x_from'], z1 + 1))
    return pts


def keel_cells(plan):
    k = plan['existing']['keel']
    cells = set()
    for z in range(k['z'][0], k['z'][1] + 1):
        for x in range(k['x_from'], k['front_by_layer'][str(z)] + 1):
            cells.add((x, z))
    h = k['hook']
    for x in range(h['x'][0], h['x'][1] + 1):
        cells.add((x, h['z']))
    return cells


# ───────────────────────── 格子 ─────────────────────────
def inside(poly, X, Z):
    """偶奇規則：點 (X, Z) 是否在多邊形內（向量化）。"""
    res = np.zeros(X.shape, bool)
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if zi != zj:
            c = ((zi > Z) != (zj > Z)) & (X < (xj - xi) * (Z - zi) / (zj - zi) + xi)
            res ^= c
        j = i
    return res


def cells_of(poly):
    xs = [p[0] for p in poly]
    zs = [p[1] for p in poly]
    x0, x1 = int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 1
    z0, z1 = int(math.floor(min(zs))) - 1, int(math.ceil(max(zs))) + 1
    X, Z = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(z0, z1 + 1) + 0.5)
    m = inside(poly, X, Z)
    return {(int(x - 0.5), int(z - 0.5)) for x, z in zip(X[m], Z[m])}


def palette_rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def write_mask(path, cells, color):
    xs = [c[0] for c in cells]
    zs = [c[1] for c in cells]
    x0, z0 = min(xs), min(zs)
    w, h = max(xs) - x0 + 1, max(zs) - z0 + 1
    a = np.zeros((h, w, 4), np.uint8)
    r, g, b = palette_rgb(color)
    for x, z in cells:
        a[z - z0, x - x0] = (r, g, b, 255)    # 第 0 列 ＝ 最低的 z（y± 貼片不翻轉）
    Image.fromarray(a, 'RGBA').save(path)
    return x0, z0, w, h


# ───────────────────────── 畫圖 ─────────────────────────
def font(size, bold=False):
    f = 'C:/Windows/Fonts/msjhbd.ttc' if bold else 'C:/Windows/Fonts/msjh.ttc'
    return ImageFont.truetype(f, int(size * SS))


class Panel:
    """一塊以作品座標畫圖的區域：X 往右、Z 往上，每格 s px。先畫在自己的圖層（自動裁切），commit 時才貼上圖紙。"""
    def __init__(s, sheet, left, top, X0, X1, Z0, Z1, scale):
        s.sh, s.left, s.top, s.X0, s.X1, s.Z0, s.Z1, s.s = sheet, left, top, X0, X1, Z0, Z1, scale
        s.w, s.h = (X1 - X0) * scale, (Z1 - Z0) * scale
        s.img = Image.new('RGB', (int(s.w * SS), int(s.h * SS)), PAPER)
        s.d = ImageDraw.Draw(s.img)

    def px(s, x, z):
        return ((x - s.X0) * s.s * SS, (s.Z1 - z) * s.s * SS)

    def sheet_xy(s, x, z):
        return (s.left + (x - s.X0) * s.s, s.top + (s.Z1 - z) * s.s)

    def poly(s, pts, fill=None):
        s.d.polygon([s.px(*p) for p in pts], fill=fill)

    def line(s, pts, color, width=2, dash=None):
        q = [s.px(*p) for p in pts]
        if not dash:
            s.d.line(q, fill=color, width=int(width * SS), joint='curve')
            return
        on, off = dash[0] * SS, dash[1] * SS
        acc, draw = 0.0, True
        for a, b in zip(q, q[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            t = 0.0
            while t < L:
                left = (on if draw else off) - acc
                step = min(left, L - t)
                if draw:
                    p0 = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
                    p1 = (a[0] + (b[0] - a[0]) * (t + step) / L, a[1] + (b[1] - a[1]) * (t + step) / L)
                    s.d.line([p0, p1], fill=color, width=int(width * SS))
                t += step
                acc += step
                if acc >= (on if draw else off) - 1e-9:
                    acc, draw = 0.0, not draw

    def grid(s, minor=10, major=50, label_x=50, label_z=20, mpc=0.1):
        for x in range(int(math.ceil(s.X0 / minor)) * minor, int(s.X1) + 1, minor):
            s.d.line([s.px(x, s.Z0), s.px(x, s.Z1)], fill=GRID5 if x % major == 0 else GRID1, width=SS)
            if x % label_x == 0:
                s.sh.text(s.sheet_xy(x, s.Z0)[0], s.top + s.h + 6, '%g m' % (x * mpc), 13, anchor='ma', color=CONSTR)
        for z in range(int(math.ceil(s.Z0 / minor)) * minor, int(s.Z1) + 1, minor):
            s.d.line([s.px(s.X0, z), s.px(s.X1, z)], fill=GRID5 if z % major == 0 else GRID1, width=SS)
            if z % label_z == 0:
                s.sh.text(s.left - 6, s.sheet_xy(s.X0, z)[1], '%g m' % (z * mpc), 13, anchor='rm', color=CONSTR)

    def text(s, x, y, t, size=15, anchor='la', color=INK, bold=False):
        s.d.text((x * SS, y * SS), t, fill=color, font=font(size, bold), anchor=anchor)

    def label(s, x, z, text, dx=0, dy=0, size=15, color=INK, anchor='la', leader=True):
        p = s.px(x, z)
        tx, ty = p[0] / SS + dx, p[1] / SS + dy
        if leader and (dx or dy):
            s.d.line([p, (tx * SS, ty * SS)], fill=color, width=SS)
            s.d.ellipse([p[0] - 2.5 * SS, p[1] - 2.5 * SS, p[0] + 2.5 * SS, p[1] + 2.5 * SS], fill=color)
        s.text(tx, ty, text, size, anchor=anchor, color=color)

    def cross(s, x, z, color=CONSTR, r=6):
        p = s.px(x, z)
        s.d.line([(p[0] - r * SS, p[1]), (p[0] + r * SS, p[1])], fill=color, width=SS)
        s.d.line([(p[0], p[1] - r * SS), (p[0], p[1] + r * SS)], fill=color, width=SS)

    def paste(s, rgb):
        """把一張已經對齊這個 panel 的 RGB 陣列貼成底圖（原圖對照用）。"""
        s.img.paste(Image.fromarray(rgb).resize(s.img.size, Image.BILINEAR), (0, 0))

    def commit(s):
        s.sh.img.paste(s.img, (int(s.left * SS), int(s.top * SS)))
        s.sh.d.rectangle([s.left * SS, s.top * SS, (s.left + s.w) * SS, (s.top + s.h) * SS], outline=INK, width=SS)


class Sheet:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.img = Image.new('RGB', (w * SS, h * SS), PAPER)
        s.d = ImageDraw.Draw(s.img)

    def text(s, x, y, t, size=15, anchor='la', color=INK, bold=False):
        s.d.text((x * SS, y * SS), t, fill=color, font=font(size, bold), anchor=anchor)

    def save(s, path):
        s.img.resize((s.w, s.h), Image.LANCZOS).save(path, optimize=True)


def draw_parts(pn, plan, C, polys, tint=True, ink=INK, width=2.2):
    E = plan['existing']
    sh = E['shoe']
    shoe = [(sh['x'][0], sh['z'][0]), (sh['x'][1] + 1, sh['z'][0]), (sh['x'][1] + 1, sh['z'][1] + 1), (sh['x'][0], sh['z'][1] + 1)]
    keel = keel_outline(plan)
    for pts, fill in ((shoe, DARK), (keel, OAK), (polys['gripe'], DARK), (polys['stem'], OAK), (polys['sternpost'], OAK)):
        pn.poly(pts, fill=fill if tint else None)
    for pts in (shoe, keel, polys['gripe'], polys['stem'], polys['sternpost']):
        pn.line(pts + [pts[0]], ink, width)
    pn.line(C['A'].points(), ink, 1.4, dash=(9, 6))


def draw_construction(pn, C):
    for k in ('T', 'F'):
        b = C[k]
        pn.cross(*b.C1)
        pn.cross(*b.J, color=RED, r=4)
    pn.cross(*C['O'].C)
    pn.cross(*C['O'].J, color=RED, r=4)


DEADWOOD = (240, 224, 192)
INNER = (206, 162, 128)


def next_stage_lines(plan, C):
    """下一階段（肋骨）的示意虛線：cutting-down line（底肋頂）與 keelson 頂，船中段接起兩頭的區塊。"""
    P = plan['parts']
    ad, fd = P['aft_deadwood'], P['fore_deadwood']
    ba = C['Ba'].points(C['Ba'].a + 200, ad['cap_z'])
    head = from_x(ba, ad['fwd_x'], -1)[0]
    b_line = [(fd['aft_x'], C['Bf'].base)] + [p for p in ba if ad['fwd_x'] <= p[0] <= fd['aft_x']] + [head]
    a_line = C['Af'].points(fd['aft_x'], C['Af'].a) + C['Aa'].points(C['Aa'].a, ad['fwd_x'])
    return a_line, b_line


def draw_parts_v2(pn, plan, C, polys, tint=True, ink=INK, width=2.2, dashed=True):
    E = plan['existing']
    sh = E['shoe']
    shoe = [(sh['x'][0], sh['z'][0]), (sh['x'][1] + 1, sh['z'][0]), (sh['x'][1] + 1, sh['z'][1] + 1), (sh['x'][0], sh['z'][1] + 1)]
    keel = keel_outline(plan)
    order = ((shoe, DARK), (keel, OAK), (polys['aft_deadwood'], DEADWOOD), (polys['fore_deadwood'], DEADWOOD),
             (polys['gripe'], DARK), (polys['stem'], OAK), (polys['sternpost'], OAK), (polys['inner_post'], INNER), (polys['apron'], INNER))
    for pts, fill in order:
        pn.poly(pts, fill=fill if tint else None)
    for pts, _ in order:
        pn.line(pts + [pts[0]], ink, width)
    if dashed:
        a_line, b_line = next_stage_lines(plan, C)
        pn.line(a_line, ink, 1.4, dash=(9, 6))
        pn.line(b_line, ink, 1.4, dash=(9, 6))


def title_block(sh, x, y, w, plan, sub, title=None, task=None):
    sh.d.rectangle([x * SS, y * SS, (x + w) * SS, (y + 88) * SS], outline=INK, width=2 * SS)
    sh.text(x + 12, y + 10, title or plan['title'], 19, bold=True)
    sh.text(x + 12, y + 38, sub, 14)
    sh.text(x + 12, y + 60, '設計：%s　%s　%s　｜參考 NARA RG 19 02 號側面圖（1849）重新設計，非描圖' % (plan['author'], plan.get('date_v2', plan['date']) if task else plan['date'], task or plan['task']), 13, color=CONSTR)


def scale_bar(sh, x, y, s_px_per_cell, meters=10, mpc=0.1):
    cells = meters / mpc
    for i in range(meters):
        x0 = x + i * s_px_per_cell / mpc
        sh.d.rectangle([x0 * SS, y * SS, (x0 + s_px_per_cell / mpc) * SS, (y + 8) * SS], fill=INK if i % 2 == 0 else PAPER, outline=INK, width=SS)
    for m in (0, 5, 10):
        sh.text(x + m * s_px_per_cell / mpc, y + 12, '%d m' % m, 13, anchor='ma')
    sh.text(x + cells * s_px_per_cell + 12, y - 2, '1 格 = 0.1 m', 13)


# ───────────────────────── 原圖對照 ─────────────────────────
class Original:
    def __init__(s, plan, path):
        r = plan['reference']
        (s1, s2, meters) = r['ref_scale']
        px = math.hypot(s2[0] - s1[0], s2[1] - s1[1])
        k = 1.0 / (px / meters * plan['meters_per_cell'])
        ang = math.atan2(s2[1] - s1[1], s2[0] - s1[0])
        th = -ang
        s.ar, s.ai = k * math.cos(th), k * math.sin(th)
        s.ref_anchor, s.work_anchor = r['ref_anchor'], r['work_anchor']
        s.shift = r['bow_sheet_shift_px']
        im = Image.open(path).convert('RGB')
        s.red = 2
        s.a = np.asarray(im.reduce(s.red)).astype(np.float32)

    def raster(s, pn, ppc):
        """原圖重取樣到作品座標（每格 ppc px）；船頭那張先補回接縫錯位。"""
        W, H = int((pn.X1 - pn.X0) * ppc), int((pn.Z1 - pn.Z0) * ppc)
        gx, gz = np.meshgrid(pn.X0 + (np.arange(W) + 0.5) / ppc, pn.Z1 - (np.arange(H) + 0.5) / ppc)
        u, w = gx - s.work_anchor[0], s.work_anchor[1] - gz
        n = s.ar ** 2 + s.ai ** 2
        dx, dy = (s.ar * u + s.ai * w) / n, (-s.ai * u + s.ar * w) / n
        x, y = s.ref_anchor[0] + dx, s.ref_anchor[1] + dy
        bow = x > 11800 + 0.2866 * (y - 1184)
        x = np.where(bow, x + s.shift[0], x) / s.red
        y = np.where(bow, y + s.shift[1], y) / s.red
        off = (x < 0) | (y < 0) | (x > s.a.shape[1] - 2) | (y > s.a.shape[0] - 2)
        x0, y0 = np.clip(np.floor(x).astype(int), 0, s.a.shape[1] - 2), np.clip(np.floor(y).astype(int), 0, s.a.shape[0] - 2)
        fx, fy = (x - x0)[..., None], (y - y0)[..., None]
        a = s.a
        out = (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)
        out = 255 - (255 - out) * 0.75     # 淡一點，讓新線看得清楚
        out[off] = PAPER
        return out.clip(0, 255).astype(np.uint8)


def x_at(pts, z):
    for p, q in zip(pts, pts[1:]):
        if (p[1] - z) * (q[1] - z) <= 0 and p[1] != q[1]:
            return p[0] + (q[0] - p[0]) * (z - p[1]) / (q[1] - p[1])
    raise ValueError('z=%g 不在曲線範圍內' % z)


# ───────────────────────── 讀數 ─────────────────────────
def dist_to_polyline(pts, poly):
    P = np.asarray(pts, float)
    A = np.asarray(poly[:-1], float)
    B = np.asarray(poly[1:], float)
    best = np.full(len(P), np.inf)
    for a, b in zip(A, B):
        ab = b - a
        L2 = ab @ ab
        t = np.clip(((P - a) @ ab) / L2, 0, 1) if L2 > 0 else np.zeros(len(P))
        q = a + t[:, None] * ab
        best = np.minimum(best, np.hypot(*(P - q).T))
    return best


def stage3(design, ref, plan, C, polys, cells, out):
    """新圖紙 v2（TASK-0483）：apron・內艉柱・船頭／船尾 deadwood 的讀數與圖紙。v1 的產出不經過這裡。"""
    P = plan['parts']
    T3 = plan['title_v2']
    ad, fd, ap, ip = P['aft_deadwood'], P['fore_deadwood'], P['apron'], P['inner_post']
    s3 = {'curves': {}, 'parts': {}}
    s3['curves']['Bf'] = {'r1': round(C['Bf'].R1, 3), 'junction': [round(v, 2) for v in C['Bf'].J]}
    s3['curves']['Ba'] = {'junction': [round(v, 2) for v in C['Ba'].J], 'center2': [round(v, 2) for v in C['Ba'].C2]}
    s3['curves']['A_meets_T'] = [round(v, 2) for v in C['meet_AT']]
    sp = os.path.join(design, 'source_points.json')
    S = json.load(open(sp, encoding='utf-8'))['points'] if os.path.exists(sp) else {}
    pairs = {'B_fore_src': C['Bf'].points(480, 115), 'A_fore_src': C['Af'].points(480, 640),
             'B_aft_src': C['Ba'].points(C['Ba'].a + 200, 60), 'A_aft_src': C['Aa'].points(420, 150)}
    for k, poly in pairs.items():
        if k in S:
            d = dist_to_polyline(S[k], poly)
            s3['curves'][k] = {'n': len(d), 'rms': round(float(np.sqrt((d ** 2).mean())), 3), 'p95': round(float(np.percentile(d, 95)), 3), 'max': round(float(d.max()), 3)}
    if 'IP_src' in S:
        d = np.array([abs(p[0] - C['IP'].x(p[1])) for p in S['IP_src']])
        s3['curves']['IP_src'] = {'n': len(d), 'rms': round(float(np.sqrt((d ** 2).mean())), 3), 'max': round(float(d.max()), 3)}
    # 跟階段一、二已經雕好的格子重疊幾格（貼合處共用同一條線 ⇒ 應該是 0）
    E = plan['existing']
    carved = {tuple(c) for c in E['keel'].get('carved_xz', [])}
    existing = {c for c in keel_cells(plan) if c not in carved}
    existing |= {(x, z) for x in range(E['shoe']['x'][0], E['shoe']['x'][1] + 1) for z in range(E['shoe']['z'][0], E['shoe']['z'][1] + 1)}
    for k in ('stem', 'gripe', 'sternpost'):
        existing |= cells[k]
    new = ('inner_post', 'aft_deadwood', 'fore_deadwood', 'apron')
    for k in new:
        others = set().union(*[cells[o] for o in new if o != k])
        s3['parts'][k] = {'cells_xz': len(cells[k]), 'overlap_existing_xz': len(cells[k] & existing), 'overlap_other_new_xz': len(cells[k] & others)}
    out['stage3'] = s3

    a_line, b_line = next_stage_lines(plan, C)
    Tp, Bp = C['T'].points(570, 124), C['Bf'].points(570, 124)

    # 圖紙 02：側面全圖 v2
    sh = Sheet(2520, 860)
    pn = Panel(sh, 70, 92, 110, 710, -14, 136, 4)
    pn.grid(label_x=50, label_z=20)
    draw_parts_v2(pn, plan, C, polys)
    sh.text(70, 22, '新圖紙 02　側面 v2（Profile）', 26, bold=True)
    sh.text(70, 58, '加上 apron・內艉柱・船頭與船尾的 deadwood（淺色＝deadwood、紅褐＝apron／內艉柱）｜虛線：cutting-down line 與 keelson 頂，肋骨階段再做', 15, color=CONSTR)
    pn.label(360, 5, '龍骨 Keel', dx=0, dy=-40, anchor='ma')
    pn.label(170, 22, 'Deadwood（船尾，含 sternson）', dx=40, dy=-90)
    pn.label((C['SPf'].x(60) + C['IP'].x(60)) / 2, 60, '內艉柱 Inner post', dx=30, dy=-50)
    pn.label((x_at(Tp, 95) + x_at(Bp, 95)) / 2, 95, 'Apron', dx=-70, dy=-20, anchor='ra')
    pn.label(605, 14, 'Deadwood（船頭）', dx=-80, dy=-70, anchor='ra')
    pn.label(430, C['Af'].base, 'cutting-down line（底肋頂）', dx=0, dy=26, anchor='ma', color=CONSTR, leader=False)
    pn.label(430, 17, 'keelson 頂', dx=0, dy=-22, anchor='ma', color=CONSTR, leader=False)
    pn.commit()
    scale_bar(sh, 70, 790, 4)
    title_block(sh, 1560, 752, 930, plan, '側面全圖　每格 4 px（1 m ＝ 40 px）', title=T3, task=plan['task_v2'])
    sh.save(os.path.join(design, 'sheet02_profile_v2.png'))

    def detail(tint, ink, width, orig=None):
        sh = Sheet(1960, 1200)
        ps = Panel(sh, 80, 100, 112, 206, -6, 96, 8)
        pb = Panel(sh, 900, 100, 566, 706, -6, 132, 7)
        for pn in (ps, pb):
            if orig is not None:
                pn.paste(orig.raster(pn, pn.s * 1.0))
            pn.grid(minor=10, major=50, label_x=10, label_z=10)
            draw_parts_v2(pn, plan, C, polys, tint=tint, ink=ink, width=width)
        return sh, ps, pb

    sh, ps, pb = detail(True, INK, 2.2)
    sh.text(80, 24, '新圖紙 02b　船尾・船頭內側構件細部 v2', 26, bold=True)
    sh.text(80, 62, '數字單位：格（0.1 m）｜內艉柱與 apron 照原圖讀數；deadwood 的頂（keelson 頂那條線）與 cutting-down line 照原圖形狀、高度對齊作品龍骨', 15, color=CONSTR)
    ipx = lambda z: C['IP'].x(z)
    ps.label((C['SPf'].x(30) + ipx(30)) / 2, 30, '內艉柱 傾 %.1f°，厚 %.1f→%.1f' % (plan['curves']['IP']['rake_deg'], ipx(8) - C['SPf'].x(8), ipx(ip['head_z']) - C['SPf'].x(ip['head_z'])), dx=40, dy=-120)
    ps.label((C['SPf'].x(ip['head_z']) + ipx(ip['head_z'])) / 2, ip['head_z'], '頂 Z %g' % ip['head_z'], dx=40, dy=-20)
    bj = C['Ba'].J
    ps.label(bj[0], bj[1], 'keelson 頂線 R%g → R%g' % (plan['curves']['Ba']['r1'], plan['curves']['Ba']['r2']), dx=-20, dy=-70, anchor='ra')
    ps.label(ad['fwd_x'], 14, '前端 X %g（40 號站位，keelson 從這裡接）' % ad['fwd_x'], dx=-10, dy=60, anchor='ra')
    ps.label((ipx(ad['cap_z']) + C['Ba'].C2[0] - C['Ba'].R2) / 2, ad['cap_z'], '頂 Z %g' % ad['cap_z'], dx=60, dy=-30)
    ps.label(165, 20, 'Deadwood', dx=0, dy=0, leader=False)
    mx, mz = C['meet_AT']
    pb.label(mx, mz, 'cutting-down line R%g 與 rabbet 交於 (%.1f, %.1f)' % (plan['curves']['Af']['r'], mx, mz), dx=40, dy=60)
    pb.label(*C['Bf'].J, 'apron 內緣 R%.1f → R%g（與艏柱同心，厚 6）' % (C['Bf'].R1, plan['curves']['Bf']['r2']), dx=-40, dy=-30, anchor='ra')
    pb.label(fd['aft_x'], 15, '後端 X %g（keelson 從這裡接）' % fd['aft_x'], dx=10, dy=-110)
    pb.label((x_at(Tp, ap['top_z']) + x_at(Bp, ap['top_z'])) / 2, ap['top_z'], 'apron 頂 Z %g' % ap['top_z'], dx=-30, dy=-24, anchor='ra')
    pb.label(605, 14, 'Deadwood', dx=-60, dy=40, anchor='ra')
    ps.commit()
    pb.commit()
    title_block(sh, 900, 1095, 990, plan, '細部　船尾每格 8 px／船頭每格 7 px', title=T3, task=plan['task_v2'])
    sh.save(os.path.join(design, 'sheet02b_details_v2.png'))

    if ref:
        orig = Original(plan, ref)
        sh, ps, pb = detail(False, RED, 1.6, orig)
        ps.commit()
        pb.commit()
        sh.text(80, 24, '對照　原圖（02 號，已補接縫錯位）＋ 新圖紙 v2（紅線）', 26, bold=True)
        sh.text(80, 62, '內側構件只求大致符合：形狀照原圖，高度對齊作品的龍骨（原圖龍骨線本身往船頭微升）', 15, color=CONSTR)
        title_block(sh, 900, 1095, 990, plan, '對照圖　船尾每格 8 px／船頭每格 7 px', title=T3, task=plan['task_v2'])
        sh.save(os.path.join(design, 'compare02_details_v2.png'))


def main():
    design = sys.argv[1]
    ref = sys.argv[sys.argv.index('--ref') + 1] if '--ref' in sys.argv else None
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    C, polys = build(plan)
    P = plan['parts']
    out = {'curves': {}, 'parts': {}, 'keel_conflicts': [], 'stamp': {}}
    out['curves']['T'] = {'r1': round(C['T'].R1, 3), 'junction': [round(v, 2) for v in C['T'].J]}
    out['curves']['F'] = {'r1': round(C['F'].R1, 3), 'junction': [round(v, 2) for v in C['F'].J]}
    out['curves']['O'] = {'junction': [round(v, 2) for v in C['O'].J], 'line_angle_deg': round(C['O'].angle_deg, 2)}

    # 設計曲線離原圖描點多遠（source_points.json：原圖描點，已換到作品座標）
    sp = os.path.join(design, 'source_points.json')
    if os.path.exists(sp):
        S = json.load(open(sp, encoding='utf-8'))['points']
        pairs = {'T_rabbet': C['T'].points(570, 124), 'F_foreface': C['F'].points(570, 124),
                 'O_gripe': C['O'].points(590, 69)}
        for k, poly in pairs.items():
            d = dist_to_polyline(S[k], poly)
            out['curves'][k] = {'n': len(d), 'rms': round(float(np.sqrt((d ** 2).mean())), 3), 'p95': round(float(np.percentile(d, 95)), 3), 'max': round(float(d.max()), 3)}
        for k, ln, zr in (('SP_aft', C['SPa'], (8, 88)), ('SP_fwd', C['SPf'], (8, 88))):
            pts = [p for p in S[k] if zr[0] <= p[1] <= zr[1]]
            d = np.array([abs(p[0] - ln.x(p[1])) for p in pts])
            out['curves'][k] = {'n': len(d), 'rms': round(float(np.sqrt((d ** 2).mean())), 3), 'max': round(float(d.max()), 3)}

    # 部件格子與遮罩
    kc = keel_cells(plan)
    mdir = os.path.join(design, 'masks')
    os.makedirs(mdir, exist_ok=True)
    cells = {k: cells_of(v) for k, v in polys.items()}
    stem_all = cells['stem']
    for (x, z) in sorted(kc):
        if x >= P['stem']['back_x'] and (x, z) not in stem_all:
            out['keel_conflicts'].append([x, z, 'gripe' if (x, z) in cells['gripe'] else 'outside'])
    for k, cs in cells.items():
        part = P[k]
        x0, z0, w, h = write_mask(os.path.join(mdir, k + '.png'), cs, part['color'])
        y0, y1 = part['sided_y']
        out['parts'][k] = {'cells_xz': len(cs), 'overlap_keel_xz': len(cs & kc), 'bbox_x': [x0, x0 + w - 1], 'bbox_z': [z0, z0 + h - 1],
                           'voxels_if_empty': len(cs) * (y1 - y0 + 1)}
        out['stamp'][k] = {'png': 'design/masks/%s.png' % k, 'at': '%d,%d,%d' % (x0, y0, z0), 'facing': 'y+',
                           'thickness': y1 - y0 + 1, 'expect_pixels': len(cs)}

    # 圖紙 01：側面全圖
    sh = Sheet(2520, 860)
    pn = Panel(sh, 70, 92, 110, 710, -14, 136, 4)
    pn.grid(label_x=50, label_z=20)
    draw_parts(pn, plan, C, polys)
    draw_construction(pn, C)
    sh.text(70, 22, '新圖紙 01　側面 v1（Profile）', 26, bold=True)
    sh.text(70, 58, '龍骨・艏柱（含前腳）・gripe・艉柱　｜　灰色虛線 apron 是下一階段的示意', 15, color=CONSTR)
    pn.label(360, 5, '龍骨 Keel 18"×24"（階段一）', dx=0, dy=-40, anchor='ma')
    pn.label(360, 1, '護龍骨 Shoe 6"', dx=0, dy=30, anchor='ma')
    Fp, Tp, Op = C['F'].points(570, 124), C['T'].points(570, 124), C['O'].points(590, 68)
    pn.label((C['SPa'].x(60) + C['SPf'].x(60)) / 2, 60, '艉柱 Sternpost', dx=50, dy=-40)
    pn.label((x_at(Fp, 95) + x_at(Tp, 95)) / 2, 95, '艏柱 Stem', dx=-70, dy=-30, anchor='ra')
    pn.label((x_at(Fp, 14) + x_at(Tp, 14)) / 2, 14, '前腳 Forefoot', dx=-90, dy=-60, anchor='ra')
    pn.label((x_at(Op, 40) + x_at(Fp, 40)) / 2, 40, 'Gripe', dx=50, dy=20)
    pn.label(590, 6, '斜接口 Hook scarf', dx=-60, dy=-110, anchor='ra')
    pn.commit()
    scale_bar(sh, 70, 790, 4)
    title_block(sh, 1560, 752, 930, plan, '側面全圖　每格 4 px（1 m ＝ 40 px）')
    sh.save(os.path.join(design, 'sheet01_profile_v1.png'))

    # 圖紙 01b：船尾、船頭細部（標尺寸）
    sh = Sheet(1640, 1240)
    ps = Panel(sh, 80, 100, 112, 156, -6, 96, 9)
    pb = Panel(sh, 620, 100, 566, 706, -6, 132, 7)
    for pn in (ps, pb):
        pn.grid(minor=10, major=50, label_x=10, label_z=10)
        draw_parts(pn, plan, C, polys)
    draw_construction(pb, C)
    sh.text(80, 24, '新圖紙 01b　艉柱・艏柱細部 v1', 26, bold=True)
    sh.text(80, 62, '十字：圓弧圓心（藍）與兩段圓弧的相切點（紅）｜數字單位：格（0.1 m）', 15, color=CONSTR)
    a, f = C['SPa'], C['SPf']
    sp_ = P['sternpost']
    ps.label(a.x(40), 40, '後緣 傾 %.1f°' % plan['curves']['SPa']['rake_deg'], dx=-14, dy=0, anchor='rm', leader=False)
    ps.label(f.x(40), 40, '前緣 傾 %.1f°' % plan['curves']['SPf']['rake_deg'], dx=14, dy=0, anchor='lm', leader=False)
    ps.label((a.x(sp_['heel_z']) + f.x(sp_['heel_z'])) / 2, sp_['heel_z'], '根部厚 %.1f' % (f.x(sp_['heel_z']) - a.x(sp_['heel_z'])), dx=60, dy=-70)
    ps.label((a.x(sp_['head_z']) + f.x(sp_['head_z'])) / 2, sp_['head_z'], '頂 Z %g，厚 %.1f' % (sp_['head_z'], f.x(sp_['head_z']) - a.x(sp_['head_z'])), dx=30, dy=-30)
    T, F, O = C['T'], C['F'], C['O']
    st = P['stem']
    pb.label(585, 8, 'T.P. x=585（rabbet 與前緣同一點起彎）', dx=30, dy=-90)
    pb.label(*F.J, '前緣 R%.1f → R%g' % (F.R1, plan['curves']['F']['r2']), dx=70, dy=40)
    pb.label(*T.J, 'rabbet R%.1f → R%g' % (T.R1, plan['curves']['T']['r2']), dx=-30, dy=-40, anchor='ra')
    pb.label(O.J[0], O.J[1], 'gripe 外緣 R%g 接 %.1f° 直線' % (plan['curves']['O']['r'], O.angle_deg), dx=60, dy=70)
    tx = T.points(570, st['head_z'])[-1][0]
    fx = F.points(570, st['head_z'])[-1][0]
    pb.label((tx + fx) / 2, st['head_z'], '頂 Z %g（%.1f m），上段同心厚 %g' % (st['head_z'], st['head_z'] / 10, plan['curves']['F']['r2'] - plan['curves']['T']['r2']), dx=-20, dy=-24, anchor='ra')
    pb.label(O.points(590, P['gripe']['top_z'])[-1][0], P['gripe']['top_z'], 'gripe 頂 Z %g\n之上接 knee of the head' % P['gripe']['top_z'], dx=12, dy=60)
    ps.commit()
    pb.commit()
    title_block(sh, 620, 1130, 990, plan, '細部　艉柱每格 9 px／艏柱每格 7 px')
    sh.save(os.path.join(design, 'sheet01b_details_v1.png'))

    # 對照：原圖（已補接縫）＋新圖紙的線
    if ref:
        orig = Original(plan, ref)
        sh = Sheet(1640, 1240)
        ps = Panel(sh, 80, 100, 112, 156, -6, 96, 9)
        pb = Panel(sh, 620, 100, 566, 706, -6, 132, 7)
        for pn in (ps, pb):
            pn.paste(orig.raster(pn, pn.s * 1.0))
            pn.grid(minor=10, major=50, label_x=10, label_z=10)
            draw_parts(pn, plan, C, polys, tint=False, ink=RED, width=1.6)
            pn.commit()
        sh.text(80, 24, '對照　原圖（02 號，已補接縫錯位）＋ 新圖紙（紅線）', 26, bold=True)
        sh.text(80, 62, '原圖只求大致符合：船殼曲線的走向與半徑照原圖，抖動、膠帶痕、拼貼錯位都不跟', 15, color=CONSTR)
        title_block(sh, 620, 1130, 990, plan, '對照圖　艉柱每格 9 px／艏柱每格 7 px')
        sh.save(os.path.join(design, 'compare01_details_v1.png'))
        sh = Sheet(2520, 860)
        pn = Panel(sh, 70, 92, 110, 710, -14, 136, 4)
        pn.paste(orig.raster(pn, 4))
        pn.grid(label_x=50, label_z=20)
        draw_parts(pn, plan, C, polys, tint=False, ink=RED, width=1.4)
        pn.commit()
        sh.text(70, 22, '對照　原圖 ＋ 新圖紙（紅線）　側面全圖', 26, bold=True)
        title_block(sh, 1560, 752, 930, plan, '對照圖　每格 4 px')
        sh.save(os.path.join(design, 'compare01_profile_v1.png'))

    if 'inner_post' in P:
        stage3(design, ref, plan, C, polys, cells, out)
    json.dump(out, open(os.path.join(design, 'verify.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
