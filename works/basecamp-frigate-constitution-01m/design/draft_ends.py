# 新圖紙 03 v2（TASK-0486）：船殼延伸到船頭與船尾 —— plan.json 的 ends 段 ＋ source_ends_traces.json（11 號水線描線）＋ 1–9 號站的船殼（draft_lines.Hull）
#   ⇒ HullV2（整艘的 hb(X, z)）、新圖紙 03 v2（sheet03_lines_v2.png）、verify_ends.json。
# 用法：python -I draft_ends.py <design 資料夾>
#   · 1–9 號站之間（X 181.5..617.1）完全照舊（直接呼叫 draft_lines.Hull）⇒ 已雕的底肋與肋骨一格都不受影響。
#   · 兩頭每個高度一條水線：原圖水線換成正規化形狀 φ(t)（t：接縫站 0 → 收尾 1）、沿高度 PCHIP；接縫站的半寬取 1–9 號站船殼本身，
#     斜率差用 β·L·u(1−u)² 補 ⇒ C1。船尾 tuck 以上被 wing transom、counter、船尾面切掉（平面上是平的）。
#   · 高度一律是「從水線量」的框（＝ body plan 的框、本作品船殼的框）；sheer plan 的讀數要先換框（見 plan.json ends.provenance）。
import sys, os, json, math
import numpy as np
from scipy.interpolate import UnivariateSpline, PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft as D            # noqa: E402
import draft_lines as DL     # noqa: E402

HALF = DL.HALF
WLZ = {'A': 62.86, 'B': 53.72, 'C': 44.58, 'D': 35.43, 'E': 26.29, 'F': 17.14}
ORDER = ['F', 'E', 'D', 'C', 'B', 'A']


def smooth(pts, lo, hi, s_per=0.06):
    """描線（有 0.1 格級的雜訊）→ 平滑樣條；只取 [lo, hi]。"""
    p = np.array(pts, float)
    p = p[(p[:, 0] >= lo) & (p[:, 0] <= hi)]
    p = p[np.argsort(p[:, 0])]
    _, idx = np.unique(np.round(p[:, 0], 2), return_index=True)
    p = p[idx]
    return UnivariateSpline(p[:, 0], p[:, 1], k=3, s=len(p) * s_per ** 2)


def psi(t, a, p, q):
    """收到切口的水線形狀：(1 − a·t)·(1 − t^p)^(1/q)；t=0 ⇒ 1、t=1 ⇒ 0；a 控制離開接縫站的斜率。"""
    t = np.clip(t, 0.0, 1.0)
    return (1 - a * t) * np.power(np.clip(1 - np.power(t, p), 0, 1), 1.0 / q)


class HullV2:
    def __init__(s, plan, src, traces):
        s.base = DL.Hull(plan, src)
        s.E = plan['ends']
        s.XS, s.XB = float(s.base.sx[0]), float(s.base.sx[-1])
        # 接縫站最高那一格：表格 0.25 一格、四捨五入 ⇒ 站頂那個 z 本身取不到值，退一格
        s.ztop9 = s.base.st[0][1]['pts'][-1][1] - 0.26
        s.ztop1 = s.base.st[-1][1]['pts'][-1][1] - 0.26
        s.z9 = s.base.st[0][1]['pts'][0][1]      # 9 號站最低點（11.8）：以下往船尾只有 deadwood
        s.z1 = s.base.st[-1][1]['pts'][0][1]     # 1 號站最低點（15.76）
        s.C, _ = D.build(plan)
        Tp = np.array(s.C['T'].points(580.0, 130))
        s.T = lambda z: float(np.interp(z, Tp[:, 1], Tp[:, 0]))
        s.zg = np.arange(0.0, s.E['z_top'] + 1e-9, 0.25)
        s.tg = np.linspace(0.0, 1.0, 801)
        s.junction = []
        s._stern_shapes(traces)
        s._bow_shapes(traces)
        s._tables()

    # ───────── 形狀 ─────────
    def _norm(s, f, Xj, Xe, ge):
        gj = float(f(Xj))
        return lambda t: np.clip((f(Xj + (Xe - Xj) * np.asarray(t, float)) - ge) / (gj - ge), 0.0, 1.5)

    def _stern_shapes(s, T):
        E = s.E['stern']
        phis = {}
        for w in E['use_wl']:
            phis[w] = s._norm(smooth(T['s' + w], E['wl_end_x'][w] - 0.5, s.XS + 15), s.XS, E['wl_end_x'][w], E['g_end'])
        zz = [s.z9] + [WLZ[w] for w in E['use_wl']] + [E['tuck_z']]
        xx = [s.XS] + [E['wl_end_x'][w] for w in E['use_wl']] + [E['tuck_post_x']]
        s.s_xe = PchipInterpolator(zz, xx)
        rows = [phis[w](s.tg) for w in E['use_wl']] + [s._tuck_phi()]
        s.s_phiz = PchipInterpolator([WLZ[w] for w in E['use_wl']] + [E['tuck_z']], np.array(rows), axis=0)
        s.s_zlo = WLZ[E['use_wl'][0]]

    def _cut(s, z):
        E = s.E['stern']
        return float(np.interp(z, *zip(*E['aft_profile_zx']))), float(np.interp(z, *zip(*E['aft_outline_zhb'])))

    def _taper(s, z, h9, he, xa):
        """psi 的 a：讓水線離開 9 號站的斜率 ＝ 1–9 號站船殼在 9 號站的斜率。"""
        zc = min(z, s.ztop9)
        d = (s.base.hb(s.XS + 0.5, [zc])[0] - s.base.hb(s.XS, [zc])[0]) / 0.5
        if abs(h9 - he) < 0.05:
            return 0.0
        return float(np.clip(d * (s.XS - xa) / (h9 - he), -0.3, 0.8))

    def _tuck_phi(s):
        """wing transom 下緣那條水線：跟正上方被橫面切掉的水線同形，只在最後 closure_cells 格用四分之一橢圓收到艉柱後緣。"""
        E = s.E['stern']
        zt, xe, dl = E['tuck_z'], E['tuck_post_x'], E['closure_cells']
        h9 = s.base.hb(s.XS, [zt])[0]
        xa, he = s._cut(zt + 0.01)
        sh = list(E['counter_shape'])
        sh[0] = s._taper(zt + 0.01, h9, he, xa)
        X = s.XS - s.tg * (s.XS - xe)
        hw = he + (h9 - he) * psi((s.XS - X) / (s.XS - xa), *sh)
        hw_c = he + (h9 - he) * psi((s.XS - (xe + dl)) / (s.XS - xa), *sh)
        u = np.clip((xe + dl - X) / dl, 0.0, 1.0)
        hb = np.where(X >= xe + dl, hw, HALF + (hw_c - HALF) * np.sqrt(np.clip(1 - u * u, 0, 1)))
        return (hb - HALF) / (h9 - HALF)

    def _bow_shapes(s, T):
        E = s.E['bow']
        st1 = E['station1_hb_lines']
        rows = []
        for w in ORDER:
            pts = [q for q in T['b' + w] if q[0] >= E['trace_from_x'].get(w, -1e9)]
            if w in st1:      # 描線沒描到 1 號站：補 1 號站的原圖讀數（11 號水線半寬圖）
                pts += [[s.XB - 1.0, st1[w] + 0.45], [s.XB, st1[w]]]
            phi = s._norm(smooth(pts, s.XB - 1.0, E['wl_end_x_lines'][w] + 0.5), s.XB, E['wl_end_x_lines'][w], E['g_end'])
            rows.append(phi(s.tg))
        zt = E['top_shape_z']
        zc = min(zt, s.ztop1)
        h1 = s.base.hb(s.XB, [zc])[0]
        d = (h1 - s.base.hb(s.XB - 0.5, [zc])[0]) / 0.5
        s.b_top_a = float(np.clip(-d * (s.T(zt) - s.XB) / (h1 - HALF), 0.0, 0.8))
        rows.append((1 - s.b_top_a * s.tg) * np.power(np.clip(1 - np.power(s.tg, E['top_shape_p']), 0, 1), 1.0 / E['top_shape_q']))
        s.b_phiz = PchipInterpolator([WLZ[w] for w in ORDER] + [zt], np.array(rows), axis=0)

    def _phi_tz(s, interp, zlo, zhi, z, t):
        return np.interp(np.clip(t, 0.0, 1.0), s.tg, interp(min(max(z, zlo), zhi)))

    # ───────── 每個高度一條水線 ─────────
    def _stern_row(s, z, X):
        E = s.E['stern']
        out = np.full(X.shape, np.nan)
        if z < s.z9:
            return out
        h9 = s.base.hb(s.XS, [min(z, s.ztop9)])[0]
        if z <= E['tuck_z']:
            xe = float(s.s_xe(z))
            if xe >= s.XS - 1e-6:
                return out
            ph = s._phi_tz(s.s_phiz, s.s_zlo, E['tuck_z'], z, (s.XS - X) / (s.XS - xe))
            ok = X >= xe
            out[ok] = HALF + (h9 - HALF) * ph[ok]
            return out
        xa, he = s._cut(z)
        sh = list(E['counter_shape'] if z <= E['knuckle_z'] else E['quarter_shape'])
        sh[0] = s._taper(z, h9, he, xa)
        ok = X >= xa
        out[ok] = he + (h9 - he) * psi((s.XS - X[ok]) / (s.XS - xa), *sh)
        return out

    def _bow_row(s, z, X):
        E = s.E['bow']
        out = np.full(X.shape, np.nan)
        if z < s.z1:
            return out
        h1 = s.base.hb(s.XB, [min(z, s.ztop1)])[0]
        xe = s.XB + (s.T(WLZ['F']) - s.XB) * (z - s.z1) / (WLZ['F'] - s.z1) if z < WLZ['F'] else s.T(z)
        t = (X - s.XB) / (xe - s.XB)
        ok = (X <= xe) & (t >= 0)
        out[ok] = HALF + (h1 - HALF) * s._phi_tz(s.b_phiz, WLZ['F'], E['top_shape_z'], z, t)[ok]
        return out

    def _match(s, row, z, xs, xj, sgn):
        """C1：值在接縫站本來就對上；斜率差用 β·L·u(1−u)² 補（u ＝ 從接縫站量到這條水線收尾處的比例，兩端都是 0）。"""
        zc = min(z, s.ztop9 if sgn < 0 else s.ztop1)
        h0 = s.base.hb(xj, [zc])[0]
        ok = np.where(~np.isnan(row))[0]
        j0 = int(np.argmin(np.abs(xs - xj)))
        j1 = j0 + (-4 if sgn < 0 else 4)
        if np.isnan(h0) or len(ok) < 5 or np.isnan(row[j0]) or np.isnan(row[j1]):
            return row
        d_ext = (row[j1] - row[j0]) / (xs[j1] - xs[j0])
        d_base = (s.base.hb(xj - sgn * 0.5, [zc])[0] - h0) / (-sgn * 0.5)
        L = abs(xj - (xs[ok[0]] if sgn < 0 else xs[ok[-1]]))
        u = np.clip(np.abs(xs - xj) / L, 0.0, 1.0)
        beta = (d_base - d_ext) * (1.0 if sgn > 0 else -1.0)
        s.junction.append({'end': 'stern' if sgn < 0 else 'bow', 'z': round(float(z), 2), 'slope_base': round(float(d_base), 4),
                           'slope_shape': round(float(d_ext), 4), 'max_correction': round(float(abs(beta) * L * 4 / 27), 3)})
        return np.where(np.isnan(row), row, row + beta * L * u * (1 - u) ** 2)

    def _tables(s):
        E = s.E
        s.xs_s = np.r_[np.arange(E['stern']['x_min'], s.XS - 1e-6, 0.25), s.XS]
        s.xs_b = np.arange(s.XB, E['bow']['x_max'] + 1e-9, 0.25)
        s.tab_s = np.full((len(s.zg), len(s.xs_s)), np.nan)
        s.tab_b = np.full((len(s.zg), len(s.xs_b)), np.nan)
        for i, z in enumerate(s.zg):
            s.tab_s[i] = s._match(s._stern_row(z, s.xs_s), z, s.xs_s, s.XS, -1)
            s.tab_b[i] = s._match(s._bow_row(z, s.xs_b), z, s.xs_b, s.XB, +1)

    def _tab(s, tab, xs, X, z):
        i = np.clip(np.round(np.asarray(z, float) / 0.25).astype(int), 0, len(s.zg) - 1)
        if X < xs[0] or X > xs[-1]:
            return np.full(np.shape(i), np.nan)
        j = int(np.clip(np.searchsorted(xs, X) - 1, 0, len(xs) - 2))
        a = (X - xs[j]) / (xs[j + 1] - xs[j])
        v0, v1 = tab[i, j], tab[i, j + 1]
        return np.where(np.isnan(v0) | np.isnan(v1), np.nan, (1 - a) * v0 + a * v1)

    # ───────── 對外：跟 draft_lines.Hull 同一組介面 ─────────
    def hb(s, X, z):
        z = np.atleast_1d(np.asarray(z, float))
        if s.XS <= X <= s.XB:
            return s.base.hb(X, z)
        return s._tab(s.tab_s, s.xs_s, X, z) if X < s.XS else s._tab(s.tab_b, s.xs_b, X, z)

    def section(s, X, z0=0.0, z1=None):
        z1 = s.E['z_top'] if z1 is None else z1
        zz = s.zg[(s.zg >= z0) & (s.zg <= z1)]
        h = s.hb(X, zz)
        ok = ~np.isnan(h)
        return np.c_[h[ok], zz[ok]]

    def aft_x(s, z):
        """船尾在高度 z 的最後端（tuck 以下 ＝ 水線收到 half-siding 的地方；以上 ＝ wing transom／counter／船尾面）。"""
        E = s.E['stern']
        return float(s.s_xe(z)) if z <= E['tuck_z'] else s._cut(z)[0]


def load(design):
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    src = json.load(open(os.path.join(design, 'source_lines.json'), encoding='utf-8'))
    tr = json.load(open(os.path.join(design, 'source_ends_traces.json'), encoding='utf-8'))['traces']
    return plan, src, tr, HullV2(plan, src, tr)


# ───────────────────────── 讀數 ─────────────────────────
def readings(design, plan, H, tr):
    raw = json.load(open(os.path.join(design, 'source_ends_raw.json'), encoding='utf-8'))
    out = {'junction': {}, 'vs_lines_traces': {}, 'vs_lines_stations': {}, 'ends': {}, 'stern_cut': {}}
    for end in ('stern', 'bow'):
        js = [j for j in H.junction if j['end'] == end]
        out['junction'][end] = {'rows': len(js), 'max_correction_cells': max(j['max_correction'] for j in js),
                                'max_correction_at_or_below_A': max(j['max_correction'] for j in js if j['z'] <= WLZ['A'])}
    # C1 讀數：接縫兩側 0.5 格的斜率差（設計後）、值的跳動
    for end, xj, sg in (('stern', H.XS, -1), ('bow', H.XB, 1)):
        jumps, kinks = [], []
        for z in np.arange(12.0, 126.0, 0.5):
            zc = z
            v_in = H.base.hb(xj - sg * 0.5, [zc])[0]
            v0 = H.hb(xj, [zc])[0]
            v_out = H.hb(xj + sg * 0.5, [zc])[0]
            v_out2 = H.hb(xj + sg * 0.25, [zc])[0]
            if np.isnan(v_in) or np.isnan(v0) or np.isnan(v_out):
                continue
            jumps.append(abs(v_out2 - v0) - abs(v0 - H.base.hb(xj - sg * 0.25, [zc])[0]))
            kinks.append(abs((v_out - v0) - (v0 - v_in)) / 0.5)
        out['junction'][end].update({'max_slope_change_per_cell': round(float(np.max(kinks)), 4), 'n': len(kinks)})
    # 原圖描線 vs 設計（同一個 X 的半寬差；描線換算見 source_ends_traces.json）
    for key, pts in tr.items():
        w = key[1]
        if w not in WLZ:
            continue
        if key[0] == 's' and w not in plan['ends']['stern']['use_wl'] + ['B']:
            continue
        lo, hi = (plan['ends']['stern']['wl_end_x'][w] + 1.0, H.XS) if key[0] == 's' else (H.XB, plan['ends']['bow']['wl_end_x_lines'][w] - 1.0)
        if key == 'bB':
            lo = max(lo, plan['ends']['bow']['trace_from_x']['B'])
        d = []
        for x, h in pts:
            if lo <= x <= hi:
                g = H.hb(x, [WLZ[w]])[0]
                if not np.isnan(g):
                    d.append(g - h)
        if d:
            d = np.array(d)
            out['vs_lines_traces'][key] = {'n': int(len(d)), 'mean': round(float(d.mean()), 2), 'rms': round(float(np.sqrt((d * d).mean())), 2),
                                           'max_abs': round(float(np.abs(d).max()), 2)}
    # 原圖站點（9.5／0.5 號站，hb_px × 0.15618）
    lines = raw['readings'][0]['data']
    st_x = {'9.5': 154.52, '0.5': 644.45}
    for st, xs in st_x.items():
        for w in ORDER:
            v = lines['3_half_breadths'][w].get(st)
            if isinstance(v, dict) and 'hb_px' in v and 'half-siding' not in v.get('note', ''):
                hb_l = v['hb_px'] * 0.15618
                g = H.hb(xs, [WLZ[w]])[0]
                out['vs_lines_stations']['%s_%s' % (st, w)] = {'X': xs, 'lines': round(hb_l, 2), 'design': None if np.isnan(g) else round(float(g), 2),
                                                               'diff': None if np.isnan(g) else round(float(g - hb_l), 2)}
    # 收尾點：每條水線收到 half-siding 的 X（船尾 vs 原圖讀數；船頭 vs 作品 rabbet）
    for w in ORDER:
        z = WLZ[w]
        xs = np.arange(95.0, H.XS, 0.05)
        v = np.array([H.hb(x, [z])[0] for x in xs])
        ok = np.where(~np.isnan(v))[0]
        xb = np.arange(H.XB, 680.0, 0.05)
        vb = np.array([H.hb(x, [z])[0] for x in xb])
        okb = np.where(~np.isnan(vb))[0]
        out['ends'][w] = {'stern_design': round(float(xs[ok[0]]), 2) if len(ok) else None, 'stern_lines': plan['ends']['stern']['wl_end_x'][w],
                          'bow_design': round(float(xb[okb[-1]]), 2) if len(okb) else None, 'bow_rabbet_T': round(H.T(z), 2),
                          'bow_lines': plan['ends']['bow']['wl_end_x_lines'][w]}
    # 船尾切口：切口處的半寬 vs body plan 船尾正視（設計就是照它切的 ⇒ 這是自我一致的檢查，不是證據）
    for z in (76, 80, 82, 84, 86, 88, 90, 95, 100, 110, 120, 127):
        xa = H.aft_x(z)
        out['stern_cut'][str(z)] = {'x': round(xa, 2), 'hb_at_cut': round(float(H.hb(xa + 0.01, [z])[0]), 2)}
    return out


# ───────────────────────── 圖紙 03 v2 ─────────────────────────
def render(design, plan, H, tr, out):
    E = plan['ends']
    sh = D.Sheet(2440, 1560)
    BLUE = (40, 110, 200)
    GREEN = (40, 150, 70)
    # 左上：橫剖面（左半＝船尾各站、右半＝船頭各站）
    bp = D.Panel(sh, 80, 100, -72, 72, -6, 132, 4.6)
    bp.grid(minor=10, major=50, label_x=20, label_z=20)
    fx0, fsp = plan['lines']['frames']['x0'], plan['lines']['frames']['spacing']
    stern_x = [fx0 + fsp * f for f in range(-41, -50, -1)] + [120.0, 112.0, 104.0]
    bow_x = [fx0 + fsp * f for f in range(26, 33)]
    for xs, sg in ((stern_x, -1), (bow_x, 1)):
        for x in xs:
            sec = H.section(x, 0, E['z_top'])
            if len(sec) < 2:
                continue
            # 中間有斷的（船尾懸出部只在 counter 以上）分段畫
            br = np.where(np.diff(sec[:, 1]) > 0.3)[0]
            for part in np.split(sec, br + 1):
                if len(part) > 1:
                    bp.line([(sg * h, z) for h, z in part], D.INK, 1.6)
    for x, sg in ((H.XS, -1), (H.XB, 1)):
        bp.line([(sg * h, z) for h, z in H.section(x, 0, E['z_top'])], D.RED, 2.4)
    raw = json.load(open(os.path.join(design, 'source_ends_raw.json'), encoding='utf-8'))
    body = raw['readings'][2]['data']['stern_outline_ordered_hb_z']
    for seg in ('counter_lower_edge', 'hull_side_at_name_band_end', 'transom_side_edge'):
        for h, z in body[seg]:
            bp.cross(-h, z, color=BLUE, r=3)
    for k, v in out['vs_lines_stations'].items():
        st, w = k.split('_')
        bp.cross((-1 if st == '9.5' else 1) * v['lines'], WLZ[w], color=GREEN, r=5)
    bp.commit()
    sh.text(80, 24, '新圖紙 03　線形圖 v2（Lines：船頭與船尾）', 26, bold=True)
    sh.text(80, 62, '左上：橫剖面（左半＝船尾 f-41…f-49 的肋位與懸出部、右半＝船頭 f+26…f+32；紅＝9／1 號站）｜右上：水線半寬｜下：側面 buttock 與船尾輪廓', 15, color=D.CONSTR)
    sh.text(80 + 72 * 4.6, 100 + 138 * 4.6 + 28, '每格 4.6 px｜綠十字＝11 號 9.5／0.5 號站水線半寬、藍十字＝11 號船尾正視（counter 下緣那條平線＝wing transom 上緣、name band 端、transom 側緣）', 12, anchor='ma', color=D.CONSTR)

    # 右上：水線半寬，兩頭各一塊
    for (x0, x1, left, key) in ((92, 200, 880, 's'), (600, 680, 1700, 'b')):
        hp = D.Panel(sh, left, 100, x0, x1, -2, 62, 7.0 if key == 's' else 9.0)
        hp.grid(minor=10, major=50, label_x=20, label_z=20)
        for z in [12, 17.14, 21.7, 26.29, 30.9, 35.43, 40, 44.58, 49.2, 53.72, 58.3, 62.86, 67, 71, 75.4, 78, 81.2, 84, 88, 95, 105, 115, 125]:
            pts = [(x, H.hb(x, [z])[0]) for x in np.arange(x0, x1, 0.25)]
            pts = [p for p in pts if not np.isnan(p[1])]
            if len(pts) > 1:
                col = D.RED if z in WLZ.values() else (BLUE if z > 75.4 else D.INK)
                hp.line(pts, col, 1.8 if z in WLZ.values() else 1.2)
        for k, pts in tr.items():
            if k[0] == key:
                for x, h in pts[::3]:
                    if x0 <= x <= x1:
                        hp.cross(x, h, color=GREEN, r=1)
        xj = H.XS if key == 's' else H.XB
        hp.line([(xj, -2), (xj, 62)], D.RED, 1.2, dash=(6, 5))
        hp.commit()
    sh.text(880 + 108 * 3.5, 100 + 64 * 7.0 + 30, '水線半寬　紅＝水線 A–F（11 號）、黑＝之間與以上、藍＝tuck 以上（被 counter／船尾面切掉）、綠點＝11 號描線', 13, anchor='ma', color=D.CONSTR)

    # 下：側面（buttock）兩頭
    for (x0, x1, left, sc) in ((92, 200, 80, 5.0), (600, 680, 760, 5.0)):
        pp = D.Panel(sh, left, 800, x0, x1, -4, 132, sc)
        pp.grid(minor=10, major=50, label_x=20, label_z=20)
        C = H.C
        polys = D.build(plan)[1]
        D.draw_parts_v2(pp, plan, C, polys, dashed=False)
        for b in [5, 10, 15, 20, 25, 30, 35, 40, 44, 47]:
            seg = []
            for x in np.arange(x0, x1, 0.25):
                h = H.hb(x, H.zg)
                ok = np.where(~np.isnan(h) & (h >= b))[0]
                if len(ok):
                    seg.append((x, H.zg[ok[0]]))
                elif len(seg) > 1:
                    pp.line(seg, BLUE, 1.3)
                    seg = []
                else:
                    seg = []
            if len(seg) > 1:
                pp.line(seg, BLUE, 1.3)
        if x0 < 300:
            pp.line([(x, z) for z, x in E['stern']['aft_profile_zx']], D.RED, 2.2)
            pp.line([(H.aft_x(z), z) for z in np.arange(12.0, E['stern']['tuck_z'] + 0.01, 0.5)], D.RED, 1.6, dash=(6, 4))
            for z, x in E['stern']['aft_profile_zx']:
                pp.cross(x, z, color=D.RED, r=3)
        pp.commit()
    sh.text(80 + 54 * 5, 800 + 136 * 5 + 22, '船尾側面　藍＝buttock（半寬 5…47 格）、紅實線＝wing transom／counter／船尾面、紅虛線＝水線收到艉柱（rabbet）', 12, anchor='ma', color=D.CONSTR)
    sh.text(760 + 40 * 5, 800 + 136 * 5 + 22, '船頭側面　buttock 收到艏柱 rabbet', 12, anchor='ma', color=D.CONSTR)
    x, y, w = 1260, 1340, 1120
    sh.d.rectangle([x * D.SS, y * D.SS, (x + w) * D.SS, (y + 110) * D.SS], outline=D.INK, width=2 * D.SS)
    sh.text(x + 12, y + 10, E['title'], 17, bold=True)
    sh.text(x + 12, y + 40, '兩頭延伸：X %.1f..%.1f（船尾）／%.1f..%.1f（船頭）' % (E['stern']['x_min'], H.XS, H.XB, E['bow']['x_max']), 14)
    sh.text(x + 12, y + 64, '設計：%s　%s　%s' % (plan['author'], E['date'], E['task']), 13, color=D.CONSTR)
    sh.text(x + 12, y + 86, '高度＝從水線量（body plan 的框）；出處見 plan.json ends.provenance', 13, color=D.CONSTR)
    sh.save(os.path.join(design, 'sheet03_lines_v2.png'))


def main():
    design = sys.argv[1]
    plan, src, tr, H = load(design)
    out = readings(design, plan, H, tr)
    render(design, plan, H, tr, out)
    json.dump(out, open(os.path.join(design, 'verify_ends.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ('junction', 'vs_lines_stations', 'ends')}, ensure_ascii=False))
    print(json.dumps(out['vs_lines_traces'], ensure_ascii=False))


if __name__ == '__main__':
    main()
