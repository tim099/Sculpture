# 新圖紙 03 線形圖（TASK-0484）：plan.json 的 lines 段 ＋ source_lines.json（原圖讀數）⇒ 船殼曲面、線形圖、對照圖、底肋與 keelson 遮罩、verify_lines.json。
# 用法：python -I draft_lines.py <design 資料夾>
#   · 船殼曲面（molded，肋骨外面）＝ 11 號各站沿船長的形狀 × 每個高度一個修正係數，讓船中（Ø 肋位）剛好等於 15 號的船中剖面；
#     龍骨側面（半寬 2.5 格）固定不動：hb(X, z) = 2.5 + (H11(X, z) − 2.5) · s(z)。
#   · 不用 scipy.interpolate（這台的 scipy.interpolate 被一個舊的 interpnd.pyd 擋住載不起來）：PCHIP 與自然三次樣條自己寫。
#   · 底肋遮罩給 `stampimg facing=x+`：引擎 x± 是 u→Z、v→Y 且 v 翻轉（write_mask_x 處理）。
import sys, os, json, math
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft as D   # noqa: E402  共用曲線、遮罩、畫圖工具（draft.py 的 main 只在直接執行時跑）

HALF = 2.5          # 龍骨／deadwood 的半寬（y 158..162 ⇒ 中線 160 兩側各 2.5）
YC = 160            # 中線格（dy = y − 160）


# ───────────────────────── 插值（不靠 scipy.interpolate） ─────────────────────────
def pchip(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    h = np.diff(x)
    d = np.diff(y) / h
    n = len(x)
    m = np.zeros(n)
    if n == 2:
        m[:] = d[0]
    else:
        for i in range(1, n - 1):
            if d[i - 1] * d[i] > 0:
                w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        m[0], m[-1] = d[0], d[-1]

    def f(q):
        q = np.asarray(q, float)
        i = np.clip(np.searchsorted(x, q) - 1, 0, n - 2)
        t = (q - x[i]) / h[i]
        return ((2 * t ** 3 - 3 * t ** 2 + 1) * y[i] + (t ** 3 - 2 * t ** 2 + t) * h[i] * m[i]
                + (-2 * t ** 3 + 3 * t ** 2) * y[i + 1] + (t ** 3 - t ** 2) * h[i] * m[i + 1])
    return f


def natural_spline(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = len(x)
    if n == 1:
        return lambda q: np.full(np.shape(q), y[0])
    if n == 2:
        return lambda q: y[0] + (y[1] - y[0]) * (np.asarray(q, float) - x[0]) / (x[1] - x[0])
    h = np.diff(x)
    A = np.zeros((n, n))
    b = np.zeros(n)
    A[0, 0] = A[-1, -1] = 1.0
    for i in range(1, n - 1):
        A[i, i - 1], A[i, i], A[i, i + 1] = h[i - 1], 2 * (h[i - 1] + h[i]), h[i]
        b[i] = 6 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
    M = np.linalg.solve(A, b)

    def f(q):
        q = np.asarray(q, float)
        i = np.clip(np.searchsorted(x, q) - 1, 0, n - 2)
        t1, t2 = x[i + 1] - q, q - x[i]
        return ((M[i] * t1 ** 3 + M[i + 1] * t2 ** 3) / (6 * h[i]) + (y[i] / h[i] - M[i] * h[i] / 6) * t1
                + (y[i + 1] / h[i] - M[i + 1] * h[i] / 6) * t2)
    return f


# ───────────────────────── 船殼曲面 ─────────────────────────
class Hull:
    def __init__(s, plan, src):
        L = plan['lines']
        s.L = L
        s.zg = np.arange(0.0, L['z_max'] + 1e-9, 0.25)
        st = {k: v for k, v in src['d11']['stations'].items() if k not in L['exclude_stations']}
        s.st = sorted(st.items(), key=lambda kv: kv[1]['x'])
        s.sx = np.array([v['x'] for _, v in s.st])
        # 每一站：z → hb（rabbet 以下 ＝ 龍骨半寬；頂以上 ＝ nan）
        s.table = np.full((len(s.st), len(s.zg)), np.nan)
        for j, (_, v) in enumerate(s.st):
            p = np.array(v['pts'], float)
            p[0, 0] = HALF
            f = pchip(p[:, 1], p[:, 0])
            row = f(s.zg)
            row[s.zg < p[0, 1]] = HALF
            row[s.zg > p[-1, 1]] = np.nan
            s.table[j] = row
        # 15 號船中剖面（高度對齊作品龍骨頂 8）
        m = np.array(src['d15']['points_ft'], float)
        hb15 = m[:, 0] * 3.048
        z15 = 8.0 + (m[:, 1] - L['d15_keel_top_ft']) * 3.048
        hb15[0] = HALF
        s.m15 = (hb15, z15)
        fm = pchip(z15, hb15)
        s.xmid = L['midship_x']
        h11 = s.H11(s.xmid, s.zg)
        M = fm(s.zg)
        M[s.zg < z15[0]] = HALF
        ratio = np.where((h11 - HALF) > 1.0, (M - HALF) / np.maximum(h11 - HALF, 1e-6), np.nan)
        ratio[s.zg > z15[-1]] = np.nan
        # 龍骨附近（h11−2.5 ≤ 1）比值不穩 ⇒ 用最近的有效值；頂上 15 號沒畫到的高度 ⇒ 用最後的有效值
        good = np.where(~np.isnan(ratio))[0]
        ratio[:good[0]] = ratio[good[0]]
        ratio[good[-1] + 1:] = ratio[good[-1]]
        k = L['ratio_smooth_cells']
        if k > 0:
            w = int(k / 0.25)
            ker = np.ones(2 * w + 1) / (2 * w + 1)
            pad = np.pad(ratio, w, mode='edge')
            ratio = np.convolve(pad, ker, mode='valid')
        s.ratio = ratio

    def H11(s, X, z):
        """11 號各站在高度 z（陣列）沿船長的自然樣條 → 在 X 的半寬。"""
        z = np.atleast_1d(np.asarray(z, float))
        out = np.full(z.shape, np.nan)
        for i, zz in enumerate(z):
            j = int(round(zz / 0.25))
            if j < 0 or j >= len(s.zg):
                continue
            col = s.table[:, j]
            ok = ~np.isnan(col)
            if ok.sum() >= 2 and s.sx[ok][0] <= X <= s.sx[ok][-1]:
                out[i] = natural_spline(s.sx[ok], col[ok])(X)
        return out

    def hb(s, X, z):
        z = np.atleast_1d(np.asarray(z, float))
        j = np.clip(np.round(z / 0.25).astype(int), 0, len(s.zg) - 1)
        h = s.H11(X, z)
        return np.where(np.isnan(h), np.nan, HALF + np.maximum(h - HALF, 0.0) * s.ratio[j])

    def section(s, X, z0=0.0, z1=None):
        """(hb, z) 折線，z 由下往上；只取有定義的高度。"""
        z1 = s.L['z_max'] if z1 is None else z1
        zz = s.zg[(s.zg >= z0) & (s.zg <= z1)]
        h = s.hb(X, zz)
        ok = ~np.isnan(h)
        return np.c_[h[ok], zz[ok]]


# ───────────────────────── 底肋 ─────────────────────────
def frames(plan):
    F = plan['lines']['frames']
    out = []
    for f in range(F['f_from'], F['f_to'] + 1):
        x = F['x0'] + F['spacing'] * f
        out.append((f, x))
    return out


def a_line(C, x):
    return max(C['Aa'].z(x), C['Af'].z(x))


def b_line(C, x):
    ba = C['Ba']
    if x < ba.a:
        return ba.base + ba.R1 - math.sqrt(max(0.0, ba.R1 ** 2 - (ba.a - x) ** 2))
    return ba.base


def floor_cells(hull, plan, C, X):
    """一片底肋在 Y-Z 平面的格子（dy, z 都是格索引；dy = y − 160）。"""
    fl = plan['lines']['floor']
    A = a_line(C, X)
    sec = hull.section(X, 7.0, 60.0)                 # molded 外緣（hb, z）
    seg = np.diff(sec, axis=0)
    arc = np.r_[0.0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
    # 底肋頭：沿 molded 線從龍骨側面量 arc ≤ head_arc（下半段才算）
    head = fl['head_arc']
    cells = set()
    for z in range(8, 45):
        zc = z + 0.5
        hbz = hull.hb(X, [zc])[0]
        if np.isnan(hbz):
            continue
        for dy in range(0, int(hbz) + 1):
            yc = dy                                  # 格中心離中線（dy=0 ⇒ 中線那一格）
            if yc >= hbz:
                continue
            P = np.array([yc, zc])
            d = np.hypot(sec[:, 0] - P[0], sec[:, 1] - P[1])
            i = int(np.argmin(d))
            near_arc = arc[i]
            ok = (zc <= A) or (d[i] <= fl['moulded'])
            if ok and near_arc <= head:
                cells.add((dy, z))
                cells.add((-dy, z))
    return cells, A


def main():
    design = sys.argv[1]
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    src = json.load(open(os.path.join(design, 'source_lines.json'), encoding='utf-8'))
    C, polys = D.build(plan)
    hull = Hull(plan, src)
    L = plan['lines']
    out = {'ratio': {}, 'midship_vs_d15': {}, 'stations_vs_d11': {}, 'floors': [], 'keelson': {}}
    for z in (9, 10, 12, 15, 20, 30, 40, 50, 63, 80, 100):
        out['ratio']['z%g' % z] = round(float(hull.ratio[int(z / 0.25)]), 3)
    # 讀數：船中剖面 vs 15 號、各站 vs 11 號（設計曲面離原圖讀數多遠，水平方向）
    hb15, z15 = hull.m15
    d = [abs(hull.hb(hull.xmid, [z])[0] - h) for h, z in zip(hb15, z15) if not np.isnan(hull.hb(hull.xmid, [z])[0])]
    out['midship_vs_d15'] = {'n': len(d), 'rms': round(float(np.sqrt(np.mean(np.square(d)))), 3), 'max': round(float(np.max(d)), 3)}
    for lab, v in src['d11']['stations'].items():
        dd = []
        for h, z in v['pts'][1:]:
            g = hull.hb(v['x'], [z])[0]
            if not np.isnan(g):
                dd.append(g - h)
        if dd:
            out['stations_vs_d11'][lab] = {'x': round(v['x'], 1), 'mean': round(float(np.mean(dd)), 2), 'rms': round(float(np.sqrt(np.mean(np.square(dd)))), 2), 'max_abs': round(float(np.max(np.abs(dd))), 2)}

    # 底肋遮罩
    mdir = os.path.join(design, 'masks', 'floors')
    os.makedirs(mdir, exist_ok=True)
    fl = L['floor']
    for f, X in frames(plan):
        cells, A = floor_cells(hull, plan, C, X)
        ys = [YC + dy for dy, z in cells]
        zs = [z for dy, z in cells]
        y0, z0 = min(ys), min(zs)
        w, h = D.write_mask_x(os.path.join(mdir, 'f%+03d.png' % f), [(YC + dy, z) for dy, z in cells], fl['color'], y0, z0)
        x0 = int(round(X)) - fl['sided'] // 2
        out['floors'].append({'f': f, 'x': round(X, 2), 'x_cells': [x0, x0 + fl['sided'] - 1], 'A': round(A, 2), 'cells_yz': len(cells),
                              'hb_max': max(abs(dy) for dy, z in cells), 'z_max': max(zs),
                              'stamp': {'png': 'design/masks/floors/f%+03d.png' % f, 'at': '%d,%d,%d' % (x0, y0, z0), 'facing': 'x+',
                                        'thickness': fl['sided'], 'expect_pixels': len(cells)}})

    # keelson（X-Z 平面，sided 與龍骨同 y 158..162）
    ks = L['keelson']
    poly = ([(ks['x_from'], a_line(C, ks['x_from']))] + [(x, a_line(C, x)) for x in np.arange(ks['x_from'], ks['x_to'] + 0.01, 0.25)]
            + [(x, b_line(C, x)) for x in np.arange(ks['x_to'], ks['x_from'] - 0.01, -0.25)])
    kc = D.cells_of(poly)
    x0, z0, w, h = D.write_mask(os.path.join(design, 'masks', 'keelson.png'), kc, ks['color'])
    out['keelson'] = {'cells_xz': len(kc), 'bbox_x': [x0, x0 + w - 1], 'bbox_z': [z0, z0 + h - 1],
                      'stamp': {'png': 'design/masks/keelson.png', 'at': '%d,158,%d' % (x0, z0), 'facing': 'y+', 'thickness': 5, 'expect_pixels': len(kc)}}

    render(design, plan, src, hull, C, polys, out)
    json.dump(out, open(os.path.join(design, 'verify_lines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ('ratio', 'midship_vs_d15', 'stations_vs_d11', 'keelson')}, ensure_ascii=False))
    print('floors', len(out['floors']), 'cells', sum(f['cells_yz'] for f in out['floors']))


# ───────────────────────── 圖紙 03 ─────────────────────────
def render(design, plan, src, hull, C, polys, out):
    L = plan['lines']
    T4, task = L['title'], L['task']
    st = hull.st
    # 線形圖：左上橫剖面（船尾一半在左、船頭一半在右）、右上水線半寬、下面側面
    sh = D.Sheet(2440, 1560)
    bp = D.Panel(sh, 80, 100, -72, 72, -6, 130, 5.0)
    bp.grid(minor=10, major=50, label_x=20, label_z=20)
    for z in (63,):
        bp.line([(-72, z), (72, z)], D.CONSTR, 1.6, dash=(10, 5))
    bp.text(5, (130 - 63) * 5 - 18, 'LWL（Z 63）', 13, color=D.CONSTR)
    for lab, v in st:
        sec = hull.section(v['x'], 0, 128)
        sign = -1 if v['x'] < hull.xmid else 1
        bp.line([(sign * h, z) for h, z in sec], D.INK, 1.8)
        top = sec[-1]
        bp.label(sign * top[0], top[1], lab, dx=sign * 6, dy=-6, size=13, anchor='la' if sign > 0 else 'ra', leader=False)
    mid = hull.section(hull.xmid, 0, 128)
    for sg in (-1, 1):
        bp.line([(sg * h, z) for h, z in mid], D.RED, 2.4)
    bp.label(mid[-1][0], mid[-1][1], 'Ø 船中', dx=8, dy=-24, size=13, color=D.RED, leader=False)
    # 三片底肋示意（船尾、船中、船頭）
    for f in (L['show_floors'] if 'show_floors' in L else []):
        rec = [r for r in out['floors'] if r['f'] == f][0]
        X = rec['x']
        cells, _ = floor_cells(hull, plan, C, X)
        for dy, z in cells:
            if (dy < 0) == (X < hull.xmid) or dy == 0:
                bp.poly([(dy - 0.5, z), (dy + 0.5, z), (dy + 0.5, z + 1), (dy - 0.5, z + 1)], fill=D.INNER)
    bp.poly([(-HALF, 0), (HALF, 0), (HALF, 8), (-HALF, 8)], fill=D.OAK)
    bp.line([(-HALF, 0), (HALF, 0), (HALF, 8), (-HALF, 8), (-HALF, 0)], D.INK, 1.4)
    bp.poly([(-HALF, 12), (HALF, 12), (HALF, 17), (-HALF, 17)], fill=D.INNER)
    bp.line([(-HALF, 12), (HALF, 12), (HALF, 17), (-HALF, 17), (-HALF, 12)], D.INK, 1.2)
    bp.commit()
    sh.text(80, 24, '新圖紙 03　線形圖 v1（Lines）', 26, bold=True)
    sh.text(80, 62, '左上：橫剖面（左半＝船尾各站、右半＝船頭各站，紅＝Ø 船中＝15 號剖面）｜右上：水線半寬｜下：側面肋位、底肋與 keelson', 15, color=D.CONSTR)
    sh.text(80 + 72 * 5, 100 + 136 * 5 + 30, '橫剖面 Body plan　每格 5 px｜紅褐＝底肋（船尾 f%+d、船頭 f%+d）、中間方塊＝龍骨與 keelson' % (L['show_floors'][0], L['show_floors'][-1]), 13, anchor='ma', color=D.CONSTR)

    hp = D.Panel(sh, 880, 100, 170, 640, -2, 72, 3.2)
    hp.grid(minor=10, major=50, label_x=50, label_z=20)
    xs = np.arange(hull.sx[0], hull.sx[-1] + 0.01, 1.0)
    for z in (12, 20, 30, 40, 50, 63, 80, 100):
        pts = [(x, hull.hb(x, [z])[0]) for x in xs]
        pts = [p for p in pts if not np.isnan(p[1])]
        hp.line(pts, D.RED if z == 63 else D.INK, 2.0 if z == 63 else 1.4)
        mx = max(pts, key=lambda p: p[1])
        hp.label(mx[0], mx[1], 'Z%g' % z, dx=0, dy=-4, size=12, anchor='md', leader=False, color=D.RED if z == 63 else D.INK)
    for lab, v in st:
        hp.line([(v['x'], -2), (v['x'], 72)], D.CONSTR, 1.0, dash=(6, 5))
        hp.text((v['x'] - 170) * 3.2, 4, lab, 12, anchor='ma', color=D.CONSTR)
    hp.line([(hull.xmid, -2), (hull.xmid, 72)], D.RED, 1.2, dash=(6, 5))
    hp.commit()
    sh.text(880 + 470 * 3.2 / 2, 100 + 74 * 3.2 + 30, '水線半寬 Half-breadth　X 170..640、半寬 0..72 格（中線在下）', 13, anchor='ma', color=D.CONSTR)

    pp = D.Panel(sh, 80, 1000, 110, 710, -10, 136, 3.4)
    pp.grid(label_x=50, label_z=20)
    D.draw_parts_v2(pp, plan, C, polys, dashed=False)
    for r in out['floors']:
        x0, x1 = r['x_cells']
        pp.poly([(x0, 8), (x1 + 1, 8), (x1 + 1, r['z_max'] + 1), (x0, r['z_max'] + 1)], fill=D.INNER)
    kpoly = [(L['keelson']['x_from'], a_line(C, L['keelson']['x_from']))] + [(x, a_line(C, x)) for x in np.arange(L['keelson']['x_from'], L['keelson']['x_to'] + 0.01, 1)] + [(x, b_line(C, x)) for x in np.arange(L['keelson']['x_to'], L['keelson']['x_from'] - 0.01, -1)]
    pp.poly(kpoly, fill=D.OAK)
    pp.line(kpoly + [kpoly[0]], D.INK, 1.4)
    for lab, v in st:
        pp.line([(v['x'], -10), (v['x'], 136)], D.CONSTR, 1.0, dash=(6, 5))
        pp.text((v['x'] - 110) * 3.4, 4, lab, 12, anchor='ma', color=D.CONSTR)
    pp.line([(hull.xmid, -10), (hull.xmid, 136)], D.RED, 1.2, dash=(6, 5))
    pp.commit()
    sh.text(80 + 300 * 3.4, 1000 + 146 * 3.4 + 26, '側面 Profile　肋距 %.3f 格（26"）｜底肋 f%+d…f%+d 共 %d 片（每片 sided %d 格）｜keelson X %g..%g' % (
        L['frames']['spacing'], L['frames']['f_from'], L['frames']['f_to'], len(out['floors']), L['floor']['sided'], L['keelson']['x_from'], L['keelson']['x_to']), 13, anchor='ma', color=D.CONSTR)
    D.title_block(sh, 1300, 860, 990, plan, '線形圖　Ø 船中 X %.1f、型寬 %.1f 格' % (hull.xmid, 2 * float(np.nanmax(hull.hb(hull.xmid, hull.zg)))), title=T4, task=task)
    sh.save(os.path.join(design, 'sheet03_lines_v1.png'))

    # 對照：橫剖面疊 11 號描點（點）與 15 號船中（紅點）
    sh = D.Sheet(1600, 1000)
    bp = D.Panel(sh, 80, 100, -72, 72, -6, 130, 5.0)
    bp.grid(minor=10, major=50, label_x=20, label_z=20)
    for lab, v in src['d11']['stations'].items():
        sign = -1 if v['x'] < hull.xmid else 1
        sec = hull.section(v['x'], 0, 128)
        if lab not in L['exclude_stations']:
            bp.line([(sign * h, z) for h, z in sec], D.INK, 1.4)
        for h, z in v['pts']:
            bp.cross(sign * h, z, color=(40, 110, 200) if lab not in L['exclude_stations'] else (150, 150, 150), r=3)
    hb15, z15 = hull.m15
    for h, z in zip(hb15, z15):
        bp.cross(h, z, color=D.RED, r=4)
        bp.cross(-h, z, color=D.RED, r=4)
    for sg in (-1, 1):
        bp.line([(sg * h, z) for h, z in mid], D.RED, 1.6)
    bp.commit()
    sh.text(80, 24, '對照　新圖紙 03 橫剖面（線）＋ 11 號描點（藍十字；灰＝3 號站，未採用）＋ 15 號船中（紅十字）', 22, bold=True)
    sh.text(80, 62, '船中（紅線）以 15 號為準；其他各站照 11 號的形狀，再乘同一組高度修正（見 verify_lines.json 的 ratio）', 15, color=D.CONSTR)
    D.title_block(sh, 860, 880, 700, plan, '對照圖　每格 5 px', title=T4, task=task)
    sh.save(os.path.join(design, 'compare03_bodyplan_v1.png'))


if __name__ == '__main__':
    main()
