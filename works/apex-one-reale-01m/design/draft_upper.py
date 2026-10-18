# 皇家號 新圖紙 02（TASK-0698）：甲板以上的構造 ⇒ 子作品清單、梯子固定點、船尾塗裝、圖紙 sheet02、讀數 verify_upper.json
#   用法：python -I -X utf8 draft_upper.py [--probe=drop_bench=N]
#   · 只讀 plan.json 與船殼清單（masks/hull，階段一證過 ＝ 作品）、不碰作品。
#   · 每件子作品用整船的框（720×321×140、at 0,0,0）；兩舷照 |dy| 產 ⇒ 逐格對稱。
#   · 重疊的處理：船殼 ＞ 甲板 ＞ 槳架 ＞ 砲台 ＞ 撞角 ＞ 船尾 ＞ 梯子（後面的扣掉前面已經有的格）⇒ 部件之間重疊 0。
#   · --probe：反向對照用（只印讀數、⛔ 不寫檔）。drop_bench=N ⇒ 少產第 N 張划手座（0 起）。
import sys, os, json, hashlib, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 720, 321, 140
PIECES = ['deck', 'apostis', 'rambade', 'eperon', 'stern', 'ladders']


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def palette_rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def load_list(path):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    return a


class Ctx:
    def __init__(self, plan, probe):
        self.plan = plan
        self.L = HL.Lines(plan)
        self.YC = self.L.YC
        self.P = {k: V(v) for k, v in plan['layout'].items()}
        self.C = {k: V(v) for k, v in plan['layout']['colors'].items()}
        self.wl = plan['waterline']['z']
        self.probe = probe
        h = load_list(os.path.join(HERE, 'masks', 'hull', 'hull_01.vox.txt'))
        self.hull = np.zeros((SX, SY, SZ), np.uint8)
        self.hull[h[:, 0], h[:, 1], h[:, 2]] = h[:, 3]
        xs = np.arange(SX) + 0.5
        self.sh = np.floor(self.L.sheer(xs)).astype(int)                       # 舷頂那一格的 z
        self.hbs = np.array([float(self.L.hb(x + 0.5, self.sh[x] - 0.5)) for x in range(SX)])   # 舷頂下一格的外緣半寬
        self.wall = int(V(plan['hull_build']['wall']))
        self.benches = [int(round(self.P['bench_first_x'] + self.P['bench_pitch'] * i)) for i in range(int(self.P['bench_count']))]

    def hw_deck(self, x):
        return int(np.floor(self.hbs[x])) - self.wall if self.hbs[x] > 0 else -1

    def deck_top(self, x, dy):
        hw = self.hw_deck(x)
        if hw < 0:
            return None
        dy = min(abs(dy), hw)
        cam = self.P['deck_camber'] * (hw / self.L.B2) * (1 - (dy / max(hw, 1)) ** 2)
        return int(self.sh[x] - self.P['deck_side_below_sheer'] + round(cam))

    def seat_top(self, x):
        return int(self.sh[x] + self.P['seat_above_sheer'])

    def rail_top(self, x):
        return int(self.sh[x] + self.P['rail_above_sheer'])


def put(a, x, dy, z, c):
    """兩舷一起放（dy ≥ 0；dy 0 只放一次）。"""
    if 0 <= x < SX and 0 <= z < SZ:
        a[x, 160 + dy, z] = c
        a[x, 160 - dy, z] = c


# ───────── 甲板、中央走道、划手座 ─────────
def build_deck(K):
    a = np.zeros((SX, SY, SZ), np.uint8)
    C, P = K.C, K.P
    for x in range(SX):
        hw = K.hw_deck(x)
        if hw < 2:
            continue
        for dy in range(hw + 1):
            t = K.deck_top(x, dy)
            put(a, x, dy, t, C['deck'])
            put(a, x, dy, t - 1, C['deck'])
            if x % int(P['beam_every']) in (0, 1):
                put(a, x, dy, t - 2, C['beam'])
                put(a, x, dy, t - 3, C['beam'])
    # 中央走道（兩頭各兩級台階）
    cx0, cx1 = P['coursier_x']
    ch = int(P['coursier_height'])
    for x in range(cx0 - 6, cx1 + 7):
        if x < cx0 - 3:
            top = 3
        elif x < cx0:
            top = 6
        elif x > cx1 + 3:
            top = 3
        elif x > cx1:
            top = 6
        else:
            top = ch
        zt = K.deck_top(x, 0) + top
        for dy in range(int(P['coursier_half']) + 1):
            for z in range(K.deck_top(x, dy) + 1, zt + 1):
                put(a, x, dy, z, C['deck'] if z == zt else C['wood'])
    # 划手座、柱、腳踏
    b0, b1 = P['bench_dy']
    drop = K.probe.get('drop_bench')
    for i, xc in enumerate(K.benches):
        if drop is not None and i == int(drop):
            continue
        st = K.seat_top(xc)
        for x in (xc - 1, xc, xc + 1):
            for dy in range(b0, b1 + 1):
                put(a, x, dy, st, C['cloth'])
                put(a, x, dy, st - 1, C['dark'])
        for dy in (18, 32):
            if dy <= K.hw_deck(xc):
                for z in range(K.deck_top(xc, dy) + 1, st - 1):
                    put(a, xc, dy, z, C['dark'])
        xf = xc - int(P['footrest_back'])
        zf = K.deck_top(xf, 0) + 3                          # 腳踏是一根水平的桿（v1 照甲板拱走 ⇒ 每一階只靠邊相接、斷成 4 格一段）
        for dy in range(b0, min(36, K.hw_deck(xf)) + 1):
            put(a, xf, dy, zf, C['dark'])
        for z in range(K.deck_top(xf, 22) + 1, zf):
            put(a, xf, 22, z, C['dark'])
    # 艙口（espale 中線）：往艙底的開口＋1 格高的圍欄
    hx0, hx1 = P['hatch_x']
    hh = int(P['hatch_half'])
    for x in range(hx0, hx1 + 1):
        for dy in range(hh + 1):
            for z in range(K.deck_top(x, dy) - 3, K.deck_top(x, dy) + 1):
                put(a, x, dy, z, 0)
    for x in range(hx0 - 1, hx1 + 2):
        for dy in range(hh + 2):
            if x in (hx0 - 1, hx1 + 1) or dy == hh + 1:
                put(a, x, dy, K.deck_top(x, dy) + 1, C['wood'])
    return a


# ───────── 舷外槳架（apostis） ─────────
def build_apostis(K):
    a = np.zeros((SX, SY, SZ), np.uint8)
    C, P = K.C, K.P
    ax0, ax1 = P['apostis_x']
    ah = int(P['apostis_half'])
    w0, w1 = P['walkway_dy']
    for x in range(ax0 + 3, ax1 - 2):                      # 縱樑：3 寬、4 高、頂金
        rt = K.rail_top(x)
        for dy in range(ah - 2, ah + 1):
            for z in range(rt - 3, rt + 1):
                put(a, x, dy, z, C['gold'] if z == rt else C['navy'])
    for x in range(ax0 + 2, ax1 - 1):                      # 舷外走道
        wt = K.seat_top(x)
        for dy in range(w0, w1 + 1):
            put(a, x, dy, wt, C['deck'])
            put(a, x, dy, wt - 1, C['deck'])
    for xj in (list(range(ax0, ax0 + 3)) + list(range(ax1 - 2, ax1 + 1))):   # 兩頭的橫樑（joug）：躺在甲板上、外端立到縱樑高
        for dy in range(ah + 1):
            for z in (K.sh[xj] + 1, K.sh[xj] + 2):
                put(a, xj, dy, z, C['dark'])
        for dy in range(ah - 2, ah + 1):
            for z in range(K.sh[xj] + 1, K.rail_top(xj) + 1):
                put(a, xj, dy, z, C['gold'] if z == K.rail_top(xj) else C['navy'])
    for xc in K.benches:                                   # bacalats：每兩張座之間一個彎托架（2 寬）
        xb = xc + 6
        d0 = int(np.floor(K.hbs[xb])) + 1
        z0 = K.sh[xb] - 2
        zt = K.rail_top(xb) - 4
        for t in np.linspace(0, math.pi / 2, 80):
            dy = d0 + (ah - 1 - d0) * math.sin(t)
            z = z0 + (zt - z0) * (1 - math.cos(t))
            for ddy in (0, 1):
                for dz in (0, 1):
                    for x in (xb, xb + 1):
                        put(a, x, int(round(dy)) + ddy - 1, int(round(z)) + dz, C['dark'])
    for xc in K.benches:                                   # 槳座（tolet）：每張座一根，立在縱樑上
        for z in (K.rail_top(xc) + 1, K.rail_top(xc) + 2):
            put(a, xc, ah - 1, z, C['beam'])
    return a


# ───────── 船頭砲台（rambade）、角落平台（conilles） ─────────
def rambade_geo(K):
    P = K.P
    rx0, rx1 = P['rambade_x']
    zt = max(K.deck_top(x, 0) for x in range(rx0, rx1 + 1)) + int(P['rambade_clear'])
    d_in, w_aft, w_fwd = P['rambade_dy']
    wf = lambda x: int(np.floor(w_aft + (w_fwd - w_aft) * (x - rx0) / (rx1 - rx0)))
    return rx0, rx1, zt, d_in, wf


def build_rambade(K):
    a = np.zeros((SX, SY, SZ), np.uint8)
    C, P = K.C, K.P
    rx0, rx1, zt, d_in, wf = rambade_geo(K)
    ph = int(P['parapet_h'])
    for x in range(rx0, rx1 + 1):
        w = wf(x)
        wn = wf(x + 1) if x < rx1 else w
        for dy in range(d_in, w + 1):
            edge = dy >= w - 1 or x >= rx1 - 1
            put(a, x, dy, zt, C['navy'] if edge else C['deck'])
            put(a, x, dy, zt - 1, C['navy'] if edge else C['deck'])
        for dy in range(min(w, wn), w + 1):                # 外緣欄杆（斜邊照相鄰兩欄補滿 ⇒ 面相連）
            for z in (zt + ph - 1, zt + ph):
                put(a, x, dy, z, C['gold'] if z == zt + ph else C['navy'])
        if (x - rx0) % 6 == 0 or x == rx1:
            for z in range(zt + 1, zt + ph - 1):
                put(a, x, w, z, C['navy'])
    for dy in range(d_in, wf(rx1) + 1):                    # 船頭那一邊的欄杆
        for z in (zt + ph - 1, zt + ph):
            put(a, rx1, dy, z, C['gold'] if z == zt + ph else C['navy'])
        if (dy - d_in) % 6 == 0:
            for z in range(zt + 1, zt + ph - 1):
                put(a, rx1, dy, z, C['navy'])
    # 角落平台（conilles）：船殼外、砲台底下，頂齊舷頂
    for x in range(rx0, rx1 - 5):
        d0 = int(np.floor(K.hbs[x])) + 1
        for dy in range(d0, wf(x) + 1):
            for z in (K.sh[x] - 1, K.sh[x]):
                put(a, x, dy, z, C['navy'] if dy >= wf(x) - 1 else C['deck'])
    # 柱：內緣（站在甲板上）、外緣（站在角落平台上），每 10 格
    for x in list(range(rx0, rx1 + 1, 10)) + [rx1 - 6]:
        if K.hw_deck(x) >= d_in:
            for z in range(K.deck_top(x, d_in) + 1, zt - 1):
                put(a, x, d_in, z, C['dark'])
        if x <= rx1 - 6:
            for z in range(K.sh[x] + 1, zt - 1):
                put(a, x, wf(x) - 1, z, C['dark'])
    return a


def build_ladders(K):
    """砲台的兩座梯子（甲板 → 砲台），回傳 (格, 固定點)。"""
    a = np.zeros((SX, SY, SZ), np.uint8)
    C = K.C
    rx0, rx1, zt, d_in, wf = rambade_geo(K)
    pts = {}
    d0, d1, dm = 16, 22, 19
    xtop = rx0 - 1
    zb = K.deck_top(xtop - 6, dm)
    n = (zt - zb) // 3
    rungs = []
    for k in range(1, n + 1):
        x = xtop - (n - k)
        z = zb + 3 * k
        if z >= zt - 1:
            break
        rungs.append((x, z))
    for (x, z) in rungs:
        for dy in range(d0, d1 + 1):
            put(a, x, dy, z, C['dark'])
    xlo, xhi = rungs[0][0], rungs[-1][0]
    for side in (d0 - 1, d1 + 1):                         # 兩條側板：從甲板到砲台底
        for k, (x, z) in enumerate(rungs):
            z_from = K.deck_top(x, side) + 1 if k == 0 else rungs[k - 1][1]
            for zz in range(z_from, z + 3):
                if zz < zt - 1:
                    put(a, x, side, zz, C['dark'])
    for s, sgn in (('S', 1), ('P', -1)):
        y = 160 + sgn * dm
        pts['ram-%s' % s] = {
            'foot': [xlo - 2, y, K.deck_top(xlo - 2, dm) + 1],
            'lo': [rungs[0][0], y, rungs[0][1] + 1],
            'hi': [rungs[-1][0], y, rungs[-1][1] + 1],
            'head': [rx0 + 2, y, zt + 1],
        }
    return a, pts


# ───────── 撞角（éperon） ─────────
def build_eperon(K):
    a = np.zeros((SX, SY, SZ), np.uint8)
    C, E = K.C, K.P['eperon']
    x0, x1 = E['x0'], E['x1']
    zc_of = lambda x: E['z0'] + (E['z1'] - E['z0']) * (x - x0) / (x1 - x0)
    for x in range(x0, x1 + 1):
        f = (x - x0) / (x1 - x0)
        zc = zc_of(x)
        h = E['h0'] + (E['h1'] - E['h0']) * f
        w = int(round(E['w0'] + (E['w1'] - E['w0']) * f))
        zlo, zhi = int(round(zc - h / 2)), int(round(zc + h / 2))
        for dy in range(w + 1):
            for z in range(zlo, zhi + 1):
                put(a, x, dy, z, C['gold'] if (z == zhi or x > x1 - 6) else C['navy'])
    cx, cz = x1 + 2, zc_of(x1)                              # 尖端的金球
    for x in range(cx - 3, cx + 4):
        for dy in range(4):
            for z in range(int(cz) - 3, int(cz) + 4):
                if (x - cx) ** 2 + dy ** 2 + (z - cz) ** 2 <= 6.5:
                    put(a, x, dy, z, C['gold'])
    xa, za = int(K.L.x_fwd(26)) + 1, 26                     # 斜撐：艏柱 → 撞角下緣
    xb = x0 + 26
    zb = int(round(zc_of(xb) - (E['h0'] + (E['h1'] - E['h0']) * (xb - x0) / (x1 - x0)) / 2)) - 1
    for t in np.linspace(0, 1, 120):
        x = int(round(xa + (xb - xa) * t))
        z = int(round(za + (zb - za) * t))
        for dy in (0, 1):
            for dz in (0, 1):
                put(a, x, dy, z + dz, C['navy'])
    return a


# ───────── 船尾：篷、翹尾、欄杆、燈桿 ─────────
def catmull(pts, n=400):
    P = np.array(pts, float)
    P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n // (len(P) - 3), endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return np.array(out)


def lantern_x(K):
    return next(x for x in range(SX) if K.hbs[x] >= 12)


def build_stern(K):
    a = np.zeros((SX, SY, SZ), np.uint8)
    C, P = K.C, K.P
    c0, c1 = P['canopy_x']
    for x in range(c0, c1 + 1):                            # 篷
        hc = min(int(np.floor(K.hbs[x])), 30)
        if hc < 6:
            continue
        zb = K.sh[x] + int(P['canopy_eave'])
        zr = K.deck_top(x, 0) + int(P['canopy_ridge'])
        roof = lambda d: zb + (zr - zb) * math.sqrt(max(0.0, 1 - (d / hc) ** 2))
        for dy in range(hc + 1):
            zhi = int(math.floor(roof(dy)))
            zlo = int(math.floor(roof(dy + 1))) if dy < hc else zb - 3
            for z in range(min(zlo, zhi), zhi + 1):
                if dy == hc and z == zb - 3:
                    c = C['gold']                           # 流蘇
                elif (x - c0) % 12 == 6:
                    c = C['gold']                           # 拱肋
                elif x % 8 == 2 and dy % 8 == 4 and dy < hc:
                    c = C['gold']                           # 金百合（點）
                else:
                    c = C['cloth']
                put(a, x, dy, z, c)
    for x in (80, 92, 104, 116, 128, 137):                 # 篷柱（立在舷頂上）
        hc = min(int(np.floor(K.hbs[x])), 30)
        zb = K.sh[x] + int(P['canopy_eave'])
        for z in range(K.sh[x] + 1, zb - 3):
            put(a, x, hc, z, C['dark'])
    xl = lantern_x(K)                                      # 船尾欄杆（金）＋三根燈桿
    hwl = int(np.floor(K.hbs[xl]))
    for x in (xl, xl + 1):
        for dy in range(hwl + 1):
            for z in range(K.sh[x] + 1, K.sh[x] + 7):
                put(a, x, dy, z, C['gold'])
    LA = P['lanterns']
    for dy in sorted(set(abs(d) for d in LA['dy'])):
        for z in range(K.sh[xl] + 7, LA['top_z']):
            put(a, xl, dy, z, C['iron'])
    pts = [(72, 49), (69, 56), (64, 63), (61, 70), (62, 76), (66, 80), (70, 79), (71, 75)]   # 翹尾（中線上的 x, z）
    curve = catmull(pts)
    for i, (cx, cz) in enumerate(curve):
        r = 2.6 - 1.2 * i / (len(curve) - 1)
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for dy in range(int(r) + 2):
                for z in range(int(cz - r) - 1, int(cz + r) + 2):
                    if (x + 0.5 - cx) ** 2 + dy ** 2 + (z + 0.5 - cz) ** 2 <= r * r:
                        put(a, x, dy, z, C['gold'])
    return a


def lanterns(K):
    LA = K.P['lanterns']
    xl = lantern_x(K)
    return [{'name': 'lantern-%s' % ('P' if d < 0 else 'S' if d > 0 else 'C'), 'at': [xl + 0.5, 160 + d + 0.5, LA['top_z']],
             'source': LA['source'], 'scale': LA['scale']} for d in LA['dy']]


# ───────── 船尾外板塗裝（換色，船殼作品） ─────────
def stern_paint(K):
    C = K.C
    out = {}
    xmax = int(K.P['stern_paint_x'])
    hull = K.hull
    for x in range(SX):
        if x > xmax:
            break
        for z in range(K.wl + 2, K.sh[x]):
            col = hull[x, :, z]
            ys = np.where(col > 0)[0]
            if not len(ys):
                continue
            for y in (ys.min(), ys.max()):
                if col[y] not in (C['navy'], C['gold']):
                    continue
                if z == K.wl + 2 or z == K.sh[x] - 1 or x >= xmax - 1:
                    c = C['gold']
                elif (x + z) % 8 == 0 or (x - z) % 8 == 0:
                    c = C['gold']
                elif (x + z) % 8 == 4 and (x - z) % 8 == 4:
                    c = C['gold']
                else:
                    c = C['blue']
                if c != col[y]:
                    out[(x, int(y), z)] = c
    return out


def mirror_diff(a):
    return int((a != a[:, ::-1, :]).sum())


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan(HERE)
    K = Ctx(plan, probe)
    taken = K.hull > 0
    pieces = {}
    builders = {'deck': build_deck, 'apostis': build_apostis, 'rambade': build_rambade, 'eperon': build_eperon, 'stern': build_stern}
    for name in PIECES:
        if name == 'ladders':
            a, lpts = build_ladders(K)
        else:
            a = builders[name](K)
        clipped = int(((a > 0) & taken).sum())
        a[taken] = 0
        pieces[name] = (a, clipped)
        taken |= a > 0
    R = {'pieces': {}}
    for name, (a, clipped) in pieces.items():
        R['pieces'][name] = {'cells': int((a > 0).sum()), 'clipped_by_earlier': clipped, 'mirror_diff': mirror_diff(a),
                             'colors': {str(c): int((a == c).sum()) for c in np.unique(a[a > 0])}}
    deck = pieces['deck'][0]
    seat_x = sorted(set(int(x) for x in np.where((deck == K.C['cloth']).any(axis=(1, 2)))[0]))
    centers = [x for x in seat_x if x - 1 in seat_x and x + 1 in seat_x]
    R['benches'] = {'per_side': len(centers), 'x': centers,
                    'pitch_mean_cells': round(float(np.diff(centers).mean()), 3) if len(centers) > 1 else None,
                    'first_from_sternpost_m': round((centers[0] - 70) * 0.1, 2) if centers else None}
    ap = pieces['apostis'][0]
    ys = np.where(ap.any(axis=(0, 2)))[0]
    R['apostis_width_m'] = round((ys.max() - ys.min() + 1) * 0.1, 2)
    rx0, rx1, zt, d_in, wf = rambade_geo(K)
    R['rambade'] = {'x': [rx0, rx1], 'floor_top_z': zt, 'deck_clear_cells': zt - 1 - max(K.deck_top(x, 0) for x in range(rx0, rx1 + 1)) - 1}
    # 梯子四點：那一格空、腳下實心、頭頂（foot／head 14 格；lo／hi 7 格）
    allc = taken
    chk = {}
    for nm, p4 in lpts.items():
        r = {}
        for k, (x, y, z) in p4.items():
            head = 14 if k in ('foot', 'head') else 7
            r[k] = {'at': [x, y, z], 'empty': not allc[x, y, z], 'solid_below': bool(allc[x, y, z - 1]),
                    'blocked_above_within': int(next((h for h in range(1, head + 1) if allc[x, y, z + h]), 0))}
        chk[nm] = r
    R['ladders'] = chk
    R['lanterns'] = []
    for L_ in lanterns(K):
        x, y, z = int(L_['at'][0]), int(L_['at'][1]), int(L_['at'][2])
        R['lanterns'].append({'name': L_['name'], 'at': L_['at'], 'pole_below': bool(allc[x, y, z - 1]), 'air_at': not allc[x, y, z]})
    paint = stern_paint(K)
    R['stern_paint'] = {'cells': len(paint), 'colors': {str(c): sum(1 for v in paint.values() if v == c) for c in set(paint.values())}}
    if probe:
        print(json.dumps({'probe': probe, 'benches_per_side': R['benches']['per_side'], 'deck_cells': R['pieces']['deck']['cells']}, ensure_ascii=False))
        return
    out = os.path.join(HERE, 'masks', 'upper')
    os.makedirs(out, exist_ok=True)
    R['lists'] = []
    for name, (a, _) in pieces.items():
        idx = np.argwhere(a > 0)
        fn = os.path.join(out, name + '.vox.txt')
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 皇家號 %s（draft_upper.py）x,y,z,color —— at 0,0,0\n' % name)
            f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, a[x, y, z]) for x, y, z in idx) + '\n')
        R['lists'].append({'piece': name, 'file': os.path.relpath(fn, HERE).replace('\\', '/'), 'cells': len(idx),
                           'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()})
    fn = os.path.join(HERE, 'masks', 'paint', 'stern.vox.txt')
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 皇家號 船尾外板塗裝（draft_upper.py）x,y,z,color —— 換色，stampvox overwrite=1，at 0,0,0\n')
        f.write('\n'.join('%d,%d,%d,%d' % (k[0], k[1], k[2], v) for k, v in sorted(paint.items())) + '\n')
    with open(os.path.join(HERE, 'ladder_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(lpts, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'lanterns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(lanterns(K), f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_upper.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(K, pieces, paint, R, os.path.join(HERE, 'sheet02_layout_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('ladders',)}, ensure_ascii=False)[:3000])
    print(json.dumps(R['ladders'], ensure_ascii=False))


def sheet(K, pieces, paint, R, path):
    comp = K.hull.copy()
    for (x, y, z), c in paint.items():
        comp[x, y, z] = c
    for name, (a, _) in pieces.items():
        comp[a > 0] = a[a > 0]
    s = 2
    x0, x1, y0, y1 = 30, 700, 90, 231
    W = (x1 - x0) * s + 80
    H = 120 + (y1 - y0) * s + 60 + 100 * s + 120
    img = Image.new('RGB', (W, H), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f1, f2, f3 = font(28), font(18), font(14)
    d.text((40, 14), '皇家號 La Réale 新圖紙 02：甲板以上的配置　0.1 m／格　apex-one 2026-10-18', fill=(20, 20, 40), font=f1)
    d.text((40, 60), '① 俯視（每個 (x, y) 最高那一格的顏色；船頭朝右）—— 32 對划手座、中央走道、舷外槳架、船頭砲台、撞角、船尾篷', fill=(20, 20, 40), font=f2)
    oy = 100
    solid = comp > 0
    zt = np.where(solid.any(axis=2), SZ - 1 - np.argmax(solid[:, :, ::-1], axis=2), -1)
    for x in range(x0, x1):
        for y in range(y0, y1):
            z = zt[x, y]
            if z >= 0:
                c = palette_rgb(int(comp[x, y, z]))
                d.rectangle([40 + (x - x0) * s, oy + (y - y0) * s, 40 + (x - x0) * s + s - 1, oy + (y - y0) * s + s - 1], fill=c)
    oy2 = oy + (y1 - y0) * s + 40
    d.text((40, oy2 - 28), '② 側面（右舷外觀）', fill=(20, 20, 40), font=f2)
    base = oy2 + 100 * s
    for x in range(x0, x1):
        for z in range(0, 100):
            ys = np.where(solid[x, :, z])[0]
            if len(ys):
                c = palette_rgb(int(comp[x, ys.max(), z]))
                d.rectangle([40 + (x - x0) * s, base - (z + 1) * s, 40 + (x - x0) * s + s - 1, base - z * s - 1], fill=c)
    d.line([40, base - (K.wl + 1) * s, 40 + (x1 - x0) * s, base - (K.wl + 1) * s], fill=(40, 110, 200))
    for x in range(50, x1, 50):
        d.text((40 + (x - x0) * s - 10, base + 6), str(x), fill=(80, 80, 80), font=f3)
    b = R['benches']
    d.text((40, base + 34), '划手座每舷 %d 張、平均間距 %.2f 格（史料 1.252 m）、第一張離艉柱頂 %.1f m；舷外槳架寬 %.1f m；砲台底 z %d（甲板上淨空 %d 格）。槳本身不畫（TASK-0691）。'
           % (b['per_side'], b['pitch_mean_cells'], b['first_from_sternpost_m'], R['apostis_width_m'], R['rambade']['floor_top_z'] - 1, R['rambade']['deck_clear_cells']),
           fill=(60, 60, 60), font=f3)
    d.text((40, base + 56), '色：甲板 177、座墊紅絨 160、深色木 104、中央走道側板 141、槳架深藍 37＋金頂 244、船尾格子藍 42／金 244、燈桿 73；燈是三叉戟號的船尾燈（模型，不在圖上）。',
           fill=(60, 60, 60), font=f3)
    img.save(path)


if __name__ == '__main__':
    main()
