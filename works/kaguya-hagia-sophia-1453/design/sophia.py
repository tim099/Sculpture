# 聖索菲亞大教堂 1453 的格子（TASK-0748）：照 plan.json 產生；numpy、決定論（同一份 plan ⇒ 逐格相同）。build.py 呼叫 build()。
# 做法：量體先當實心（研究座標：+X 往後殿、+Y 往北、Z 往上，公尺）⇒ 只留離「外面的空氣」shell_m 內的格（裡面是空的）
#   ⇒ 窗、門 ＝ 最外一格挖掉、第二格塗暗色（或門的木色）。座標換算見 plan.json 的 frame_note。
import os, json, math
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
MPV = P['mpv']
FX, FY, FZ = P['frame']['x'], P['frame']['y'], P['frame']['z_top']
NX = int(round((FY[1] - FY[0]) / MPV))          # 模型 x ＝ 北 → 南
NY = int(round((FX[1] - FX[0]) / MPV + 0.49))   # 模型 y ＝ 西 → 東（145 / 0.4 ＝ 362.5 ⇒ 363）
NZ = int(round(FZ / MPV))
C = P['colors']
BRICK, MARBLE, LEAD, GOLD, DARK, DOOR, TYMP = 1, 2, 3, 4, 5, 6, 7
BODY, ROOF, ANNEX = 1, 2, 3

RX = (FX[0] + (np.arange(NY) + 0.5) * MPV)[None, :, None]
RY = (FY[1] - (np.arange(NX) + 0.5) * MPV)[None, None, :]
RZ = ((np.arange(NZ) + 0.5) * MPV)[:, None, None]
SHAPE = (NZ, NY, NX)


def full(m): return np.broadcast_to(m, SHAPE)


def box(x0, x1, y0, y1, z0, z1): return (RX >= x0) & (RX < x1) & (RY >= y0) & (RY < y1) & (RZ >= z0) & (RZ < z1)


def roofed(x0, x1, y0, y1, z, rise, slope=0.15):
    """牆（z 以下）＋四坡的屋頂（離邊 d 公尺 ⇒ 高 min(rise, slope·d)）⇒ (牆, 屋頂)。"""
    d = np.minimum(np.minimum(RX - x0, x1 - RX), np.minimum(RY - y0, y1 - RY))
    inside = (RX >= x0) & (RX < x1) & (RY >= y0) & (RY < y1)
    wall = inside & (RZ < z)
    roof = inside & (RZ >= z) & (RZ < z + np.minimum(rise, slope * np.maximum(d, 0)) + MPV)
    return wall, roof


def sloped(x0, x1, y0, y1, z_in, z_out, axis):
    """扶壁：頂從貼著主體那一邊 z_in 斜到外面 z_out（axis ＝ 'y'：外面是 |Y| 大的那一邊；'x'：外面是 X 大的那一邊）。"""
    if axis == 'y':
        t = (np.abs(RY) - min(abs(y0), abs(y1))) / abs(y1 - y0)
    else:
        t = (RX - x0) / (x1 - x0)
    zt = z_in + (z_out - z_in) * np.clip(t, 0, 1)
    return box(x0, x1, y0, y1, 0, 99) & (RZ < zt)


def windows_ring(cx, cy, r_lo, r_hi, z0, z1, angles, half_w):
    """圍著 (cx, cy) 一圈的窗：角度（度，從 +X 逆時針往 +Y）、寬 2·half_w（公尺，照半徑換算）。"""
    dx, dy = RX - cx, RY - cy
    r = np.hypot(dx, dy); a = np.arctan2(dy, dx)
    m = np.zeros((1, NY, NX), bool) & False
    for ang in angles:
        da = np.angle(np.exp(1j * (a - math.radians(ang))))
        m = m | (np.abs(da) * np.maximum(r, 1e-6) < half_w)
    return m & (r >= r_lo) & (r <= r_hi) & (RZ >= z0) & (RZ < z1)


def build():
    S = np.zeros(SHAPE, bool); MAT = np.zeros(SHAPE, np.uint8); LAY = np.zeros(SHAPE, np.uint8)
    WIN, DOORS, AIR = [], [], []

    def add(m, mat, lay):
        m = full(m); S[m] = True; MAT[m] = mat; LAY[m] = lay

    # ── 中庭（西、北、南三面迴廊；東面成了外前廊）、宗主教府、聖器室、洗禮堂 ──
    A = P['atrium']; (ax0, ax1), (ay0, ay1), t = A['x'], A['y'], A['wall_t']
    add(box(ax0, ax0 + t, ay0, ay1, 0, A['z']), BRICK, ANNEX)
    add(box(ax0, ax1, ay1 - t, ay1, 0, A['z']), BRICK, ANNEX)
    add(box(ax0, ax1, ay0, ay0 + t, 0, A['z']), BRICK, ANNEX)
    wd = A['walk_d']
    for dist, inside in (((RX - ax0), box(ax0, ax0 + wd, ay0, ay1, 0, 99)), ((ay1 - RY), box(ax0, ax1, ay1 - wd, ay1, 0, 99)), ((RY - ay0), box(ax0, ax1, ay0, ay0 + wd, 0, 99))):
        zt = A['z'] - (A['z'] - A['walk_z_in']) * np.clip(dist / wd, 0, 1)
        add(inside & (RZ < zt) & (RZ >= zt - 0.8), LEAD, ANNEX)
    pz = A['walk_z_in'] - 0.7
    for yy in np.arange(ay0 + wd, ay1 - wd + 0.01, A['pier_step']):
        add(box(ax0 + wd - A['pier'], ax0 + wd, yy - A['pier'] / 2, yy + A['pier'] / 2, 0, pz), MARBLE, ANNEX)
    for xx in np.arange(ax0 + wd, ax1 - 0.6, A['pier_step']):
        add(box(xx - A['pier'] / 2, xx + A['pier'] / 2, ay1 - wd, ay1 - wd + A['pier'], 0, pz), MARBLE, ANNEX)
        add(box(xx - A['pier'] / 2, xx + A['pier'] / 2, ay0 + wd - A['pier'], ay0 + wd, 0, pz), MARBLE, ANNEX)
    fc = ((ax0 + ax1) / 2, (ay0 + ay1) / 2); u, v = np.abs(RX - fc[0]), np.abs(RY - fc[1])
    add((np.maximum(np.maximum(u, v), (u + v) / math.sqrt(2)) <= A['fountain_r']) & (RZ < A['fountain_h']), MARBLE, ANNEX)
    AIR.append(box(ax0 - 1, ax0 + t + 1, A['gate_y'][0], A['gate_y'][1], 0, A['gate_h']))
    Q = P['patriarchate']; w_, r_ = roofed(*Q['x'], *Q['y'], Q['z'], Q['roof_rise']); add(w_, BRICK, ANNEX); add(r_, LEAD, ANNEX)
    K = P['skeuophylakion']; rr = np.hypot(RX - K['c'][0], RY - K['c'][1])
    add((rr <= K['r']) & (RZ < K['z']), BRICK, ANNEX)
    add((RZ >= K['z']) & (rr <= K['r']) & (RZ < K['z'] + K['dome_rise'] * np.sqrt(np.clip(1 - (rr / K['r']) ** 2, 0, 1)) + MPV), LEAD, ANNEX)
    WIN.append(windows_ring(K['c'][0], K['c'][1], K['r'] - 1.5, K['r'] + 0.5, 8.0, 10.0, range(0, 360, 45), 0.6))
    Bp = P['baptistery']; u, v = np.abs(RX - Bp['c'][0]), np.abs(RY - Bp['c'][1]); oc = np.maximum(np.maximum(u, v), (u + v) / math.sqrt(2))
    add((oc <= Bp['r']) & (RZ < Bp['z']), BRICK, ANNEX)
    rb = np.sqrt((RX - Bp['c'][0]) ** 2 + (RY - Bp['c'][1]) ** 2 + (RZ - Bp['z']) ** 2)
    add((RZ >= Bp['z']) & (rb <= Bp['dome_r']), LEAD, ANNEX)
    add((RZ >= Bp['z']) & (RZ < Bp['z'] + 0.8) & (oc <= Bp['r']), LEAD, ANNEX)
    WIN.append(windows_ring(Bp['c'][0], Bp['c'][1], Bp['r'] * 0.9 - 1.5, Bp['r'] + 0.5, 6.5, 9.0, [22.5 + 45 * k for k in range(8)], 0.6))

    # ── 主體、扶壁墩、其他扶壁 ──
    M = P['main']; w_, r_ = roofed(*M['x'], *M['y'], M['z'], M['roof_rise'], M['roof_slope']); add(w_, BRICK, BODY); add(r_, LEAD, ROOF)
    for b in P['buttresses']:
        add(sloped(*b['x'], *b['y'], b['z_in'], b['z_out'], b.get('dir', 'y')), BRICK, BODY)
    Pi = P['piers']
    for sx in (-1, 1):
        for sy in (-1, 1):
            xs, ys = sorted([sx * Pi['x'][0], sx * Pi['x'][1]]), sorted([sy * Pi['y'][0], sy * Pi['y'][1]])
            w_, r_ = roofed(*xs, *ys, Pi['z'], 1.5, 0.4); add(w_, BRICK, BODY); add(r_, LEAD, ROOF)
    # 前廊、鐘樓、飛扶壁
    N = P['inner_narthex']; (nx0, nx1) = N['x']
    add(box(nx0, nx1, *N['y'], 0, N['z']), BRICK, BODY)
    zt = N['z'] + N['roof_rise'] * np.clip((RX - nx0) / (nx1 - nx0), 0, 1)
    add(box(nx0, nx1, *N['y'], N['z'], 99) & (RZ < zt + MPV), LEAD, ROOF)
    O = P['outer_narthex']; (ox0, ox1) = O['x']
    add(box(ox0, ox1, *O['y'], 0, O['z']), BRICK, BODY)
    zt = O['z'] + O['roof_rise'] * np.clip((RX - ox0) / (ox1 - ox0), 0, 1)
    add(box(ox0, ox1, *O['y'], O['z'], 99) & (RZ < zt + MPV), LEAD, ROOF)
    add(box(ox0, ox0 + 0.8, *O['y'], 0, 9.0), MARBLE, BODY)                           # 西立面的大理石貼面
    for yc in O['doors_y']:
        DOORS.append(box(ox0 - 1, ox0 + 1.2, yc - O['door_w'] / 2, yc + O['door_w'] / 2, 0, O['door_h']))
    F = P['flyers']
    for yc in F['y']:
        y0, y1 = yc - F['w'] / 2, yc + F['w'] / 2
        add(box(F['pier_x'][0], F['pier_x'][1], y0, y1, 0, F['pier_z']), BRICK, BODY)
        ztop = F['pier_z'] + (F['end_z'] - F['pier_z']) * np.clip((RX - F['pier_x'][1]) / (F['end_x'] - F['pier_x'][1]), 0, 1)
        add(box(F['pier_x'][1], F['end_x'], y0, y1, 0, 99) & (RZ < ztop) & (RZ >= ztop - F['thick']), BRICK, BODY)
    Bf = P['belfry']; (bx0, bx1), (by0, by1) = Bf['x'], Bf['y']
    add(box(bx0, bx1, by0, by1, 0, Bf['z']), BRICK, BODY)
    add(box(bx0, bx0 + 0.8, by0, by1, 0, 9.0), MARBLE, BODY)
    hx, hy, cxb, cyb = (bx1 - bx0) / 2, (by1 - by0) / 2, (bx0 + bx1) / 2, (by0 + by1) / 2
    k = np.clip((Bf['z'] + Bf['roof_h'] - RZ) / Bf['roof_h'], 0, 1)
    add((RZ >= Bf['z']) & (np.abs(RX - cxb) <= hx * k) & (np.abs(RY - cyb) <= hy * k), LEAD, ROOF)
    for yc in (cyb - hy / 2, cyb + hy / 2):
        WIN.append(box(bx0 - 1, bx0 + 1.2, yc - 0.8, yc + 0.8, *Bf['open_z']))
    for xc in (cxb - hx / 2, cxb + hx / 2):
        WIN.append(box(xc - 0.8, xc + 0.8, by0 - 1, by0 + 1.2, *Bf['open_z']) | box(xc - 0.8, xc + 0.8, by1 - 1.2, by1 + 1, *Bf['open_z']))
    DOORS.append(box(bx0 - 1, bx0 + 1.2, cyb - Bf['door_w'] / 2, cyb + Bf['door_w'] / 2, 0, Bf['door_h']))

    # ── 穹頂基座（正方形一路砌到穹頂底）、南北山牆 ──
    Db = P['dome_base']; (dx0, dx1), (dy0, dy1) = Db['x'], Db['y']
    add(box(dx0, dx1, dy0, dy1, 0, Db['z']), BRICK, BODY)
    add(box(dx0, dx1, dy0, dy1, Db['z'] - 0.8, Db['z']), LEAD, ROOF)                  # 基座頂（穹頂四角）鋪鉛
    Ar = Db['arch']; ra = np.hypot(RX, RZ - Ar['zc'])
    arch_in = ((ra < Ar['r_in']) & (RZ >= Ar['zc'])) | ((np.abs(RX) < Ar['r_in']) & (RZ < Ar['zc']))
    tymp = arch_in & (RZ >= M['z'] + M['roof_rise'] + 0.4)
    AIR.append(tymp & (np.abs(RY) >= dy1 - 0.8))                                      # 山牆退進大拱裡 0.8 m
    MAT[full(tymp & (np.abs(RY) >= dy1 - 2.4) & (np.abs(RY) < dy1 - 0.8)) & S] = TYMP   # 退進去的那一面顏色深一點 ⇒ 看得出拱
    for row in Db['tymp_rows']:
        n, st = row['n'], row['step']
        for i in range(n):
            xc = (i - (n - 1) / 2) * st
            WIN.append(box(xc - Db['win_w'] / 2, xc + Db['win_w'] / 2, -99, 99, *row['z']) & (np.abs(RY) >= dy1 - 2.4) & (np.abs(RY) < dy1))

    # ── 半穹頂、半圓壁龕、祭壇筒拱、後殿、西拱頂 ──
    Sd = P['semidomes']
    for s in (-1, 1):
        cx = s * Sd['cx']; rr = np.sqrt((RX - cx) ** 2 + RY ** 2 + (RZ - Sd['zc']) ** 2)
        add((rr <= Sd['r_out']) & (s * (RX - cx) >= 0) & (RZ >= Sd['zc'] - 1.0), LEAD, ROOF)
        WIN.append(windows_ring(cx, 0.0, Sd['r_out'] - 2.0, Sd['r_out'] + 0.5, *Sd['win_z'], [90 - s * 90 + a for a in (-60, -30, 0, 30, 60)], 0.8))
    Ex = P['exedrae']
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * Ex['cx'], sy * Ex['cy']; ux, uy = sx / math.sqrt(2), sy / math.sqrt(2)
            rr = np.sqrt((RX - cx) ** 2 + (RY - cy) ** 2 + (RZ - Ex['zc']) ** 2)
            add((rr <= Ex['r_out']) & ((RX - cx) * ux + (RY - cy) * uy >= 0) & (RZ >= Ex['zc'] - 1.0), LEAD, ROOF)
            base = math.degrees(math.atan2(uy, ux))
            WIN.append(windows_ring(cx, cy, Ex['r_out'] - 2.0, Ex['r_out'] + 0.5, Ex['zc'] + 1.3, Ex['zc'] + 3.3, [base - 40, base, base + 40], 0.6))
    Bm = P['bema']
    add(box(*Bm['x'], -Bm['half_w'], Bm['half_w'], 0, Bm['zc']), BRICK, BODY)
    add(box(*Bm['x'], -99, 99, Bm['zc'], 99) & (np.hypot(RY, RZ - Bm['zc']) <= Bm['r_out']), LEAD, ROOF)
    Ap = P['apse']; ax0_, ax1_ = Ap['x0'], Ap['x1']
    lim = Ap['half_w0'] - (Ap['half_w0'] - Ap['half_w1']) * np.clip((RX - (ax0_ + 1)) / (ax1_ - ax0_ - 1), 0, 1)
    apse = (RX >= ax0_) & (RX < ax1_) & (np.abs(RY) <= lim)
    add(apse & (RZ < Ap['z']), BRICK, BODY)
    add(apse & (RZ >= Ap['z']) & (np.sqrt((RX - ax0_) ** 2 + RY ** 2 + (RZ - Ap['z']) ** 2) <= Ap['conch_r']), LEAD, ROOF)
    for z0, z1 in Ap['win_rows']:
        WIN.append(box(ax1_ - 1.6, ax1_ + 1, -1.0, 1.0, z0, z1))
        WIN.append(box(ax0_ + 2.6, ax0_ + 4.2, -99, 99, z0, z1) & (np.abs(RY) >= 3.5))
    Wv = P['west_vault']; (wx0, wx1) = Wv['x']
    add(box(wx0, wx1, -Wv['half_w'], Wv['half_w'], 0, Wv['zc']), BRICK, BODY)
    add(box(wx0, wx1, -99, 99, Wv['zc'], 99) & (np.hypot(RY, RZ - Wv['zc']) <= Wv['r_out']), LEAD, ROOF)
    lun = (RZ >= Wv['zc']) & (np.hypot(RY, RZ - Wv['zc']) < Wv['lunette_r']) & ~((np.abs(np.abs(RY) - 2.2) < 0.3))
    WIN.append(lun & (RX < wx0 + 1.2) & (RX >= wx0 - 1))
    add(box(wx0, wx0 + 0.8, -99, 99, Wv['zc'], 99) & (np.hypot(RY, RZ - Wv['zc']) <= Wv['r_out'] - 0.6), BRICK, BODY)   # 西窗那一面是磚牆

    # ── 中央穹頂：40 個窗間墩一圈、鉛皮、頂上十字 ──
    Dm = P['dome']; zc, Ro, xs = Dm['zc'], Dm['r_out'], Dm['x_scale']
    rd = np.sqrt((RX / xs) ** 2 + RY ** 2 + (RZ - zc) ** 2)
    add((rd <= Ro) & (RZ >= Dm['z0']), LEAD, ROOF)
    rxy = np.hypot(RX / xs, RY); ang = np.degrees(np.arctan2(RY, RX / xs))
    surf = np.sqrt(np.clip(Ro ** 2 - (RZ - zc) ** 2, 0, None))
    ring_z = (RZ >= Dm['z0']) & (RZ < Dm['ring_top'])
    west = np.abs(np.angle(np.exp(1j * np.radians(ang - 180)))) <= math.radians(9.0 * Dm['west_ribs'] / 2)
    depth = np.where(west, Dm['pier_d_west'], Dm['pier_d']) * np.clip((Dm['ring_top'] - RZ) / (Dm['ring_top'] - Dm['z0']), 0, 1)
    step = 360.0 / Dm['n_win']
    fin = np.abs(np.angle(np.exp(1j * np.radians(ang) * Dm['n_win']))) / (2 * math.pi) * step   # 離最近一根肋多少度
    add(ring_z & (fin * math.pi / 180 * rxy < Dm['pier_w'] / 2) & (rxy >= surf - 0.8) & (rxy <= surf + depth), BRICK, ROOF)
    winm = np.abs(np.angle(np.exp(1j * (np.radians(ang) * Dm['n_win'] - math.pi)))) / (2 * math.pi) * step
    WIN.append((RZ >= Dm['z0'] + 0.4) & (RZ < Dm['ring_top'] - 0.8) & (winm * math.pi / 180 * rxy < Dm['win_w'] / 2) & (rxy >= surf - 2.0) & (rxy <= surf + 0.5))
    Cr = Dm['cross']; top = zc + Ro
    add(box(-0.2, 0.2, -0.2, 0.2, top - 0.8, top + Cr['h']), GOLD, ROOF)
    add(box(-0.2, 0.2, -Cr['arm'] / 2, Cr['arm'] / 2, top + Cr['arm_z'], top + Cr['arm_z'] + 0.4), GOLD, ROOF)
    add(box(-0.6, 0.6, -0.6, 0.6, top - 0.8, top + 0.4), GOLD, ROOF)

    # ── 主體的窗、牆腳的大理石 ──
    xs_ = np.arange(M['x'][0] + 2.6, M['x'][1] - 2.0, M['win_step'])
    for z0, z1 in M['win_rows']:
        cols = np.zeros((1, NY, 1), bool)
        for xc in xs_: cols = cols | ((RX >= xc - M['win_w'] / 2) & (RX < xc + M['win_w'] / 2))
        WIN.append(cols & (np.abs(RY) >= M['y'][1] - 1.6) & (np.abs(RY) < M['y'][1] + 0.4) & (RZ >= z0) & (RZ < z1))
        rows = np.zeros((1, 1, NX), bool)
        for yc in np.arange(8.0, 21.0, M['win_step']): rows = rows | (np.abs(np.abs(RY) - yc) < M['win_w'] / 2)   # |Y| 22～34 是 1317 年的東扶壁 ⇒ 不開
        WIN.append(rows & (RX >= M['x'][1] - 1.6) & (RX < M['x'][1] + 0.4) & (RZ >= z0) & (RZ < z1))
    for yc in np.arange(N['y'][0] + 4.0, N['y'][1] - 3.0, N['win_step']):
        WIN.append(box(nx0 - 1.0, nx0 + 1.2, yc - 0.8, yc + 0.8, *N['win_z']))
    base_course = S & (RZ < 1.2) & (LAY == BODY)
    MAT[base_course] = MARBLE

    # ── 挖空：只留離外面的空氣 shell_m 內的格；地板那一層留著（不然從底下看是空的） ──
    for a in AIR: S[full(a)] = False
    lab, n = ndimage.label(~S)
    edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()]))) - {0}
    ext = np.isin(lab, list(edge)); del lab
    dist = ndimage.distance_transform_cdt(~ext, metric='taxicab')
    sh = int(round(P['shell_m'] / MPV))
    keep = S & ((dist <= sh) | (full(RZ) < MPV))
    # 窗與門：最外一格挖掉、第二格上色
    for lst, col in ((WIN, DARK), (DOORS, DOOR)):
        for wm in lst:
            wm = full(wm)
            keep[wm & (dist == 1)] = False
            MAT[wm & (dist == 2) & keep] = col
    keep &= MAT > 0
    G = np.zeros(SHAPE, np.uint8)
    # 上色：磚（灰縫一層一層、深淺雜一點）、大理石、鉛皮（穹頂照 40 根肋的經線接縫、其他照進深每 2.4 m 一道）
    zz, yy, xx = np.nonzero(keep)
    h = ((xx.astype(np.int64) * 73856093) ^ (yy.astype(np.int64) * 19349663) ^ (zz.astype(np.int64) * 83492791)) & 0xffff
    h = h / 65536.0
    m = MAT[zz, yy, xx]
    col = np.zeros(len(zz), np.uint8)
    b = m == BRICK
    mort = (zz % 3 == 0)
    col[b] = np.where(mort[b], np.where(h[b] < 0.6, C['mortar'], C['brick']), np.where(h[b] < 0.22, C['brick_dark'], C['brick']))
    tb = m == TYMP
    col[tb] = np.where(mort[tb], np.where(h[tb] < 0.5, C['mortar'], C['brick_dark']), C['brick_dark'])
    mb = m == MARBLE; col[mb] = np.where(h[mb] < 0.2, C['marble_2'], C['marble'])
    lb = m == LEAD
    Xr, Yr, Zr = RX[0, yy, 0], RY[0, 0, xx], RZ[zz, 0, 0]
    on_dome = (np.sqrt((Xr / xs) ** 2 + Yr ** 2 + (Zr - zc) ** 2) <= Ro + 0.5) & (Zr >= Dm['z0'])
    a2 = np.degrees(np.arctan2(Yr, Xr / xs)); seam_d = (np.abs(np.angle(np.exp(1j * np.radians(a2) * Dm['n_win']))) < 0.25)
    seam = np.where(on_dome, seam_d, yy % 6 == 0)
    col[lb] = np.where(seam[lb], C['lead_seam'], C['lead'])
    col[m == GOLD] = C['gold']; col[m == DARK] = C['dark']; col[m == DOOR] = C['door']
    G[zz, yy, xx] = col
    L = np.zeros(SHAPE, np.uint8); L[keep] = LAY[keep]
    anchors = {'lot-0': (0, 0, 0),
               'door': (int((FY[1] - sum(A['gate_y']) / 2) / MPV), 0, 0),
               'bell': (int((FY[1] - cyb) / MPV), int((cxb - FX[0]) / MPV), int(round(22.6 / MPV))),
               'dome-top': (int(FY[1] / MPV), int(-FX[0] / MPV), min(NZ - 1, int((top + Cr['h']) / MPV)))}
    return G, L, anchors
