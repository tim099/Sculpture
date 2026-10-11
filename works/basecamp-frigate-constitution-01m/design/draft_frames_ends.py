# 新圖紙 04 v2（TASK-0486）：船頭與船尾的骨架 —— plan.json 的 framing_ends 段 ＋ 新圖紙 03 v2 的船殼（draft_ends.HullV2）
#   ⇒ 每根木料一份 3D 格子清單（給 `sculpture op=stampvox`，TASK-0487）、新圖紙 04 v2、verify_frames_ends.json。
# 用法：python -I draft_frames_ends.py <design 資料夾>
#   · 斜的木料（cant、fashion piece）是「只在平面上轉角度」的垂直平板（Steel 1805：perpendicular to the half-breadth plan）；
#     一格屬於它 ⇔ 格中心在平板厚度內、在船殼內、|dy| ≥ 3（留給龍骨／deadwood／艉柱）、在它自己那個平面裡離船殼 ≤ moulded、不高過舷頂。
#     「在平面裡離船殼多遠」用平面內 0.25 格的取樣做距離轉換（EDT）—— 跟中段肋骨「在肋骨平面裡量」同一個定義。
#   · hawse pieces、knighthead、counter timbers 是跟中線平行的平板（y 為常數）；transoms 與船尾橫材是水平的。
#   · 同一格只給一根木料：照 priority 由前往後分，後面的讓（記在讀數裡）。左右舷照中線鏡像（y ↔ 320 − y），同一根木料兩舷放同一份清單。
#   · 全部同色 141（Tim 2026-10-11：木紋不做、同色匯出可合併）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import draft as D            # noqa: E402
import draft_lines as DL     # noqa: E402
import draft_frames as DF    # noqa: E402
import draft_ends as DE      # noqa: E402
from replay import replay    # noqa: E402

YC = DL.YC
HALF = DL.HALF


# ───────────────────────── 整艘的半寬表（查表比逐點算樣條快幾百倍） ─────────────────────────
class HullTable:
    """hb(X, z) 在 X 每 0.25、z 每 0.25 的表：1–9 號站之間用 draft_lines.Hull 同一組樣條（逐個 z 一次算整排 X ⇒ 值相同），兩頭用 HullV2 的表。"""
    def __init__(s, H, x0, x1):
        s.H = H
        s.zg = H.zg
        s.xg = np.arange(x0, x1 + 1e-9, 0.25)
        tab = np.full((len(s.zg), len(s.xg)), np.nan)
        base = H.base
        mid = (s.xg >= H.XS) & (s.xg <= H.XB)
        xm = s.xg[mid]
        for j, z in enumerate(s.zg):
            jj = min(int(round(z / 0.25)), len(base.zg) - 1)
            col = base.table[:, jj]
            ok = ~np.isnan(col)
            if ok.sum() >= 2:
                sx = base.sx[ok]
                inr = (xm >= sx[0]) & (xm <= sx[-1])
                h = np.full(xm.shape, np.nan)
                h[inr] = DL.natural_spline(sx, col[ok])(xm[inr])
                tab[j, mid] = np.where(np.isnan(h), np.nan, HALF + np.maximum(h - HALF, 0.0) * base.ratio[jj])
        for i, x in enumerate(s.xg):
            if not mid[i]:
                tab[:, i] = H.hb(float(x), s.zg)
        s.tab = tab
        valid = ~np.isnan(tab)
        s.top = np.where(valid.any(0), s.zg[np.clip(valid.shape[0] - 1 - np.argmax(valid[::-1], 0), 0, None)], np.nan)

    def hb(s, X, Z):
        """X、Z 同形的陣列 → 半寬（X 線性內插、Z 取最近的 0.25 格；表外 nan）。"""
        X = np.asarray(X, float)
        Z = np.asarray(Z, float)
        zi = np.clip(np.round(Z / 0.25).astype(int), 0, len(s.zg) - 1)
        fx = (X - s.xg[0]) / 0.25
        xi = np.clip(np.floor(fx).astype(int), 0, len(s.xg) - 2)
        a = fx - xi
        v = (1 - a) * s.tab[zi, xi] + a * s.tab[zi, xi + 1]
        out_of = (fx < 0) | (fx > len(s.xg) - 1)
        return np.where(out_of, np.nan, v)

    def top_at(s, X):
        return np.interp(np.asarray(X, float), s.xg, np.nan_to_num(s.top, nan=-1.0))


# ───────────────────────── 木料 ─────────────────────────
class Ctx:
    def __init__(s, design):
        s.design = design
        s.plan, s.src, s.tr, s.H = DE.load(design)
        s.F = s.plan['framing']
        s.FE = s.plan['framing_ends']
        s.T = HullTable(s.H, 94.0, 681.0)
        s.m_of = DF.moulded_fn(s.F)
        s.sc, _ = DF.sheer_fit(s.F)
        s.cap = s.FE['stern']['sheer_cap']
        s.claim = {}          # (x, dy, z) → 木料名（只記 dy ≥ 0 那一舷；另一舷是鏡像）
        s.timbers = []
        # 作品現況（events 重播）扣掉雕兩頭之前要刻掉的艉柱頭／內艉柱頭（plan framing_ends.stern.post_trim）
        #   ⇒ 清單排除已有的格：從中線起的橫材（dy 0..2）在柱頭以下讓給柱子，stampvox 落地數才會 ＝ 清單格數
        W = os.path.dirname(os.path.abspath(design))
        vox = replay(W)
        pt = s.FE['stern']['post_trim']
        s.trim = {k for k, v in vox.items() if k[0] < pt['x_max'] and abs(k[1] - YC) <= 2 and
                  ((v[0] == 177 and k[2] >= pt['sternpost_from_z']) or (v[0] == 173 and k[2] >= pt['inner_post_from_z']))}
        s.world = {k: v[0] for k, v in vox.items() if k not in s.trim}

    def sheer(s, X):
        return np.minimum(np.polyval(s.sc, X), s.cap)

    def top(s, X):
        """木料頂：sheer（封頂 sheer_cap）與船殼表上緣取小；兩頭再各加一道（2026-10-11 雕之前修，兩個 verifier 都量到 9 號站一道 2 格的台階）：
        · 船尾：從 9 號站已雕方肋的頂（top_ramp.z_station9 ＝ 126.0）起、斜率 0，二次曲線升到船尾面的 sheer_cap
          —— 原本船尾直接用 sheer_cap 128.4，而 9 號站往前的方肋停在 126（1–9 號站的船殼只到 8 號站頂）⇒ cant 頂 z 127、方肋頂 z 125。
        · 船頭：不高過 bow_top_cap（已雕方肋頂 123 那一層）。"""
        X = np.asarray(X, float)
        t = np.minimum(s.sheer(X), s.T.top_at(X))
        R = s.FE['stern']['top_ramp']
        u = np.clip((s.H.XS - X) / (s.H.XS - R['x_end']), 0.0, 1.0)
        ramp = R['z_station9'] + (s.cap - R['z_station9']) * u * u
        t = np.where(X < s.H.XS, np.minimum(t, ramp), t)
        return np.where(X > s.H.XB, np.minimum(t, s.FE['bow']['top_cap']), t)

    def inside(s, x, dy, z):
        """格中心 (x+0.5, dy, z+0.5) 在船殼內（|dy| < hb），而且不高過船殼表的上緣（z_top）——
        表的 z 索引會被夾住，船頭在 z_top 以上照樣回值（不會變 nan），所以要另外擋（verifier 2026-10-11）。"""
        h = s.T.hb(x + 0.5, z + 0.5)
        return ~np.isnan(h) & (np.abs(dy) < h) & (np.asarray(z) + 0.5 <= s.T.zg[-1])

    def occupied(s, c):
        """這一格（兩舷任一）在作品裡已經有東西。"""
        return (c[0], YC + c[1], c[2]) in s.world or (c[0], YC - c[1], c[2]) in s.world

    def add(s, name, kind, cells, meta):
        """cells：(x, dy, z) 陣列（dy ≥ 0）。已被別的木料佔的格讓掉、作品裡已有的格讓給作品；記下讓了幾格。"""
        keep, lost = [], {}
        for c in cells:
            c = (int(c[0]), int(c[1]), int(c[2]))
            o = s.claim.get(c)
            if o is None and s.occupied(c):
                o = '(作品現有)'
            if o is None:
                s.claim[c] = name
                keep.append(c)
            else:
                lost[o] = lost.get(o, 0) + 1
        s.timbers.append({'name': name, 'kind': kind, 'cells_half': keep, 'yielded_to': lost, **meta})
        return keep


def plane_band(cx, s0, s1, P0, u, n, d0, d1, mfix=None, zlo=7.0, zhi=None, extra=None):
    """垂直平板：平面線 P(s) = P0 + s·u（plan 上的單位向量 u；n ＝ u 轉 90°），厚度 d ∈ [d0, d1)。回傳 (x, dy, z) 格。"""
    zhi = cx.H.E['z_top'] if zhi is None else zhi
    ss = np.arange(s0, s1 + 1e-9, 0.25)
    zz = np.arange(zlo, cx.T.zg[-1] + 12.0 + 1e-9, 0.25)
    dm = 0.5 * (d0 + d1)
    PX = P0[0] + ss * u[0] + dm * n[0]
    PY = P0[1] + ss * u[1] + dm * n[1]
    S, Z = np.meshgrid(ss, zz)
    HB = cx.T.hb(np.broadcast_to(PX, S.shape), np.minimum(Z, cx.T.zg[-1]))
    # 舷頂（與表的上緣）以上把船殼往上延伸：距離只量側面與底面的 molded 線，⛔ 不量「切掉的頂」——
    # 否則每根木料頂上都會多一條沿著舷頂的水平帶子（第一版 knighthead 的頭因此長成 35 格長的方塊）
    for j in range(HB.shape[1]):
        col = HB[:, j]
        ok = np.where(~np.isnan(col))[0]
        if len(ok):
            col[ok[-1] + 1:] = col[ok[-1]]
    ins = ~np.isnan(HB) & (np.abs(np.broadcast_to(PY, S.shape)) < HB)
    dist = ndimage.distance_transform_edt(ins, sampling=(0.25, 0.25))
    # 候選格：平板的 bbox
    corners = [P0 + a * u + b * n for a in (s0, s1) for b in (d0, d1)]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    X, Y, Zc = np.meshgrid(np.arange(int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 2),
                           np.arange(max(3, int(math.floor(min(ys))) - 1), int(math.ceil(max(ys))) + 2),
                           np.arange(int(math.floor(zlo)), int(math.ceil(zhi)) + 1), indexing='ij')
    X, Y, Zc = X.ravel(), Y.ravel(), Zc.ravel()
    xc, yc, zc = X + 0.5, Y.astype(float), Zc + 0.5          # dy 的格中心就是 dy（中線格 160 的中心＝中線）
    sv = (xc - P0[0]) * u[0] + (yc - P0[1]) * u[1]
    dv = (xc - P0[0]) * n[0] + (yc - P0[1]) * n[1]
    ok = (dv >= d0) & (dv < d1) & (sv >= s0) & (sv <= s1) & (Y >= 3)
    ok &= cx.inside(X, Y, Zc) & (zc <= cx.top(xc))
    si = np.clip(np.round((sv - s0) / 0.25).astype(int), 0, len(ss) - 1)
    zi = np.clip(np.round((zc - zz[0]) / 0.25).astype(int), 0, len(zz) - 1)
    mlim = np.array([cx.m_of(z) for z in zc]) if mfix is None else np.full(zc.shape, mfix)
    ok &= dist[zi, si] <= mlim
    if extra is not None:
        ok &= extra(X, Y, Zc)
    return np.c_[X[ok], Y[ok], Zc[ok]]


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def steel_fan(n, sq_x, head_last, heel_last, z_mb, cx, sign, first_head=None, arc=False):
    """Steel 的兩線法：舷寬線（z_mb）與 bearding line（dy 2.5）在最後一片方肋與最後一根 cant 之間各分 n 等分，對應點連線。
    sign：+1 船頭（往 +X）、−1 船尾。回傳每根 cant 的 (heel_xy, head_xy)。
    first_head（2026-10-11 雕之前修）：第一根的舷寬點直接給（貼著已雕的方肋、空 1 格）；heel 跟著平移同樣的量，其餘照舊等分到最後一根。
      —— 原本第一根離方肋的距離是「一個 cant 間距」，接縫處的縫是 3–4 格（其他地方 1 格）。
    arc：舷寬點沿舷寬線的弧長等分（船頭船殼轉得快，照 X 等分會往艏柱越開越大，verifier 量到最大 3.3–3.9 格）。"""
    if first_head is None:
        h1, l1 = sq_x + (head_last - sq_x) / n, sq_x + (heel_last - sq_x) / n
    else:
        h1 = first_head
        l1 = sq_x + (heel_last - sq_x) / n + (first_head - (sq_x + (head_last - sq_x) / n))
    if arc:
        xs = np.linspace(h1, head_last, 2001)
        hs = np.array([float(cx.T.hb(x, z_mb)) for x in xs])
        sl = np.r_[0.0, np.cumsum(np.hypot(np.diff(xs), np.diff(hs)))]
        heads = [float(np.interp(sl[-1] * (k - 1) / (n - 1), sl, xs)) for k in range(1, n + 1)]
    else:
        heads = [h1 + (head_last - h1) * (k - 1) / (n - 1) for k in range(1, n + 1)]
    out = []
    for k in range(1, n + 1):
        hx = heads[k - 1]
        lx = l1 + (heel_last - l1) * (k - 1) / (n - 1)
        hb = float(cx.T.hb(hx, z_mb))
        out.append((np.array([lx, HALF]), np.array([hx, hb])))
    return out


def junction_head(cx, end, z_mb, gap):
    """第一根 cant（一對 6 格）的舷寬點：讓它的那一片跟已雕方肋在舷側（|dy| ≥ 30、z_mb ± 10）之間剛好空 gap 格。"""
    pts = [k for k, c in cx.world.items() if c == 141 and abs(k[1] - YC) >= 30 and abs(k[2] - z_mb) <= 10]
    if end == 'stern':
        sq_min = min(k[0] for k in pts if k[0] < 300)
        return float(sq_min - gap - 3)          # 船頭側那片 d ∈ [0,3) ⇒ 格 line..line+2
    sq_max = max(k[0] for k in pts if k[0] > 500)
    return float(sq_max + gap + 4)              # 船尾側那片 d ∈ [−3,0) ⇒ 格 line−3..line−1


def cant_pair(cx, base, kind, heel, head, sided):
    """一對 cant（雙片）：當成一塊 d ∈ [−sided, sided) 產（moulded 在兩片的中縫量 ⇒ 兩片內側面對齊），再照 d 的正負切成兩片；
    船頭側（-fwd）先、船尾側（-aft）讓。原本兩片各自在自己的中面量 ⇒ 內側面差 2–3 格（verifier 2026-10-11：船尾 156 格缺口）。"""
    u = unit(head - heel)
    nrm = np.array([u[1], -u[0]])
    cells = plane_band(cx, -2.0, 80.0, heel, u, nrm, -float(sided), float(sided))
    d = (cells[:, 0] + 0.5 - heel[0]) * nrm[0] + (cells[:, 1] - heel[1]) * nrm[1]
    ang = math.degrees(math.atan2(abs(head[0] - heel[0]), head[1] - heel[1]))
    meta = {'heel': [round(float(v), 2) for v in heel], 'head': [round(float(v), 2) for v in head], 'cant_deg': round(ang, 1)}
    cx.add(base + '-fwd', kind, cells[d >= 0], meta | {'d': [0, sided]})
    cx.add(base + '-aft', kind, cells[d < 0], meta | {'d': [-sided, 0]})


def cant(cx, name, kind, heel, head, d0, d1, mfix=None, zlo=7.0, zhi=None, extra=None):
    u = unit(head - heel)
    nrm = np.array([u[1], -u[0]])           # u 轉 −90°：兩頭的 cant 都是 u ≈ (小, +1) ⇒ n ≈ +X（船頭方向）；d > 0 ＝ 船頭側
    s1 = 80.0
    cells = plane_band(cx, -2.0, s1, heel, u, nrm, d0, d1, mfix, zlo, zhi, extra)
    ang = math.degrees(math.atan2(abs(head[0] - heel[0]), head[1] - heel[1]))
    return cx.add(name, kind, cells, {'heel': [round(float(v), 2) for v in heel], 'head': [round(float(v), 2) for v in head],
                                      'cant_deg': round(ang, 1), 'd': [d0, d1]})


# ───────────────────────── 設計 ─────────────────────────
def build(cx):
    FE = cx.FE
    fx0, fsp = cx.plan['lines']['frames']['x0'], cx.plan['lines']['frames']['spacing']
    out = {'stern': {}, 'bow': {}}

    # ── 船尾 ──
    S = FE['stern']
    sq = fx0 + fsp * S['last_square']                    # 最後一片方肋（plane A 的中心 X）
    fp_heel = np.array([S['fashion_piece']['heel_x'], HALF])
    fp_head = np.array(S['fashion_piece']['head_xy'])
    fh = junction_head(cx, 'stern', S['breadth_z'], FE['junction_gap_cells'])
    fan = steel_fan(S['cants'] + 1, sq, fp_head[0], fp_heel[0], S['breadth_z'], cx, -1, first_head=fh)
    out['stern']['first_head_x'] = fh
    # 最後一條（k = n+1）就是 fashion piece 的線；前 n 條是 cant 對
    cant(cx, 'S-fashion-piece', 'fashion_piece', fp_heel, fp_head, -S['fashion_piece']['sided'] / 2, S['fashion_piece']['sided'] / 2,
         mfix=S['fashion_piece']['moulded'], zhi=S['wing_transom']['z'][1] + 0.99)
    for k, (heel, head) in enumerate(fan[:-1], 1):
        cant_pair(cx, 'S-cant%d' % k, 'stern_cant', heel, head, 3)
    out['stern']['fan'] = [{'k': k + 1, 'heel': [round(float(a), 2) for a in h], 'head': [round(float(a), 2) for a in q]} for k, (h, q) in enumerate(fan)]

    # 船尾橫面以上：counter timbers（y 為常數的平板，沿 counter／船尾面往內 moulded 格）
    E = cx.H.E['stern']
    def aft_cut(Zc):
        return np.array([cx.H.aft_x(z + 0.5) for z in Zc])
    ct = S['counter_timbers']
    zlo, zhi = S['wing_transom']['z'][1] + 1, int(math.floor(cx.cap)) - 0
    # 厚度垂直於 counter／船尾面量（側面看的輪廓線，x-z 平面）—— counter 下緣那段幾乎是水平的（每升 1 層往前 2.6 格），
    # 水平量 3 格的帶子上下層接不起來（2026-10-11 雕之前修：counter timbers 在 Z 81–82 斷成碎塊）
    zz = np.arange(E['tuck_z'], cx.H.E['z_top'] + 1e-9, 0.1)
    prof = np.c_[[cx.H.aft_x(z) for z in zz], zz]
    A_, B_ = prof[:-1], prof[1:]
    AB = B_ - A_
    L2 = (AB ** 2).sum(1) + 1e-12
    def d_face(px, pz):
        p = np.array([px, pz])
        t = np.clip(((p - A_) * AB).sum(1) / L2, 0, 1)
        return float(np.sqrt((((A_ + AB * t[:, None]) - p) ** 2).sum(1)).min())
    # dy 照 11 號船尾正視的窗位框（2026-10-11 雕之前修）：每根一段 [dy0, dy1]，名字取 dy0；舷邊那根 side_sided 格
    for rng in ct['dy'] + ['side']:
        dy0 = rng if rng == 'side' else rng[0]
        cells = []
        prev_to = None
        for z in range(zlo, zhi + 1):
            xa = cx.H.aft_x(z + 0.5)
            he = float(np.interp(z + 0.5, *zip(*E['aft_outline_zhb'])))
            if rng == 'side':
                d_from, d_to = int(math.floor(he)) - ct['side_sided'], int(math.floor(he)) - 1
                if prev_to is not None:           # 船尾外形在 Z 82–85 每層往外跳約 3 格 ⇒ 跟下一層至少重疊一格
                    d_from = min(d_from, prev_to)
                # 往內接到 side_inner_dy（最外那扇窄窗 34.53 之外是實心的角）—— 原本跟 dy 35–37 那根之間留一道 1 格的長縫（verifier）
                d_from = min(d_from, ct['side_inner_dy'])
                prev_to = d_to
            else:
                d_from, d_to = rng
            for dy in range(max(3, d_from), d_to + 1):
                for x in range(int(math.floor(xa)), int(math.floor(xa)) + 4 * ct['moulded'] + 1):
                    if x + 0.5 < xa or d_face(x + 0.5, z + 0.5) >= ct['moulded']:
                        continue
                    if cx.inside(np.array([x]), np.array([dy]), np.array([z]))[0] and z + 0.5 <= cx.top(x + 0.5):
                        cells.append((x, dy, z))
        cx.add('S-counter-timber-%s' % dy0, 'counter_timber', np.array(cells, int).reshape(-1, 3), {'dy': rng})

    # 船尾面上的橫材：窗台（seat transom）、窗楣、taffrail —— 從中線（rails_from_dy）起；原本 dy 3 起 ⇒ 船尾中線一道 0.5 m 的縫
    for nm, (za, zb) in S['stern_rails'].items():
        cells = []
        for z in range(za, zb + 1):
            xa = cx.H.aft_x(z + 0.5)
            hbz = float(np.interp(z + 0.5, *zip(*E['aft_outline_zhb'])))
            for dy in range(S['rails_from_dy'], int(math.ceil(hbz)) + 1):
                for x in range(int(math.floor(xa)), int(math.floor(xa)) + ct['moulded'] + 1):
                    if x + 0.5 < xa or x + 0.5 >= xa + ct['moulded']:
                        continue
                    if cx.inside(np.array([x]), np.array([dy]), np.array([z]))[0]:
                        cells.append((x, dy, z))
        cx.add('S-rail-%s' % nm, 'stern_rail', np.array(cells, int).reshape(-1, 3), {'z': [za, zb]})

    # wing transom：橫面後面 moulded 格深、Z 範圍內、船殼內（兩端頂到 fashion piece）
    wt = S['wing_transom']
    cells = []
    for z in range(wt['z'][0], wt['z'][1] + 1):
        xa = cx.H.aft_x(z + 0.5)
        for x in range(int(math.floor(xa)), int(math.floor(xa)) + wt['depth_x'] + 1):
            if x + 0.5 < xa or x + 0.5 >= xa + wt['depth_x']:
                continue
            for dy in range(wt['from_dy'], 60):        # 中線起；柱頭以下的格 add() 讓給作品現有的柱子
                if cx.inside(np.array([x]), np.array([dy]), np.array([z]))[0]:
                    cells.append((x, dy, z))
    cx.add('S-wing-transom', 'transom', np.array(cells, int).reshape(-1, 3), {'z': wt['z']})

    # 下面的 transoms：水平的帶子，只在 fashion piece 的船尾側；一格屬於它 ⇔ 貼著艉柱前緣往前 depth_x 格，
    #   或在那一層的水平面裡離船殼表面 ≤ transom_moulded（像一根躺平的肋骨，從艉柱接到 fashion piece）。
    #   原本只有貼著艉柱的那一塊 ⇒ 艉柱與 fashion piece 之間的船殼表面留了一串斜的小洞（2026-10-11 雕之前修，剪影量到）
    C = cx.H.C
    u_fp = unit(fp_head - fp_heel)
    tm = S['transom_moulded']
    gx = np.arange(C['SPf'].x(S['transoms_z'][0][1] + 1.0) - 3.0, fp_heel[0] + 6.0, 0.25)
    gy = np.arange(-6.0, 62.0, 0.25)
    GX, GY = np.meshgrid(gx, gy, indexing='ij')
    for i, (za, zb) in enumerate(S['transoms_z'], 1):
        cells = []
        for z in range(za, zb + 1):
            HB = cx.T.hb(GX, np.full(GX.shape, z + 0.5))
            ins = ~np.isnan(HB) & (np.abs(GY) < HB)
            dist = ndimage.distance_transform_edt(ins, sampling=(0.25, 0.25))
            x0 = C['SPf'].x(z + 0.5)
            for x in range(int(math.floor(x0)), int(math.ceil(fp_heel[0])) + 3):
                if x + 0.5 < x0:
                    continue
                for dy in range(3, 60):
                    # fashion piece 的船尾側（d < 0 ＝ 往艉柱那邊；它自己的厚度之外）
                    d = ((x + 0.5 - fp_heel[0]) * u_fp[1] - (dy - fp_heel[1]) * u_fp[0])
                    if d >= -S['fashion_piece']['sided'] / 2 or not cx.inside(np.array([x]), np.array([dy]), np.array([z]))[0]:
                        continue
                    near_post = x + 0.5 < x0 + S['transom_depth_x']
                    gi = int(round((x + 0.5 - gx[0]) / 0.25))
                    gj = int(round((dy - gy[0]) / 0.25))
                    if near_post or (0 <= gi < len(gx) and dist[gi, gj] <= tm):
                        cells.append((x, dy, z))
        cx.add('S-transom%d' % i, 'transom', np.array(cells, int).reshape(-1, 3), {'z': [za, zb]})

    # 懸出部的側面：雙片的方 quarter timbers（每對 x0..x1、之間空 1 格，跟方肋同一個節奏；只取側面那一條帶子，counter 底面那段留給 counter timbers）
    #   原本 3 片單的（X 119／112／105）在 X 121–128 留了 8–10 格的洞（verifier 2026-10-11）
    for i, (x0, x1) in enumerate(S['quarter_timbers'], 1):
        def extra(X, Y, Zc):
            hbz = cx.T.hb(X + 0.5, Zc + 0.5)
            return (Zc >= S['wing_transom']['z'][1] + 1) & (Y >= hbz - np.array([cx.m_of(z + 0.5) for z in Zc]) - 0.5) & (Y >= S['quarter_min_dy'])
        cells = plane_band(cx, 0.0, 70.0, np.array([float(x0), 0.0]), np.array([0.0, 1.0]), np.array([1.0, 0.0]), 0.0, float(x1 - x0 + 1), extra=extra)
        cx.add('S-quarter%d' % i, 'quarter_timber', cells, {'x': [x0, x1]})

    # ── 船頭 ──
    B = FE['bow']
    sqb = fx0 + fsp * B['last_square'] + cx.F['plane_b_offset']     # 最後一片方肋（plane B 的中心 X）
    fhb = junction_head(cx, 'bow', B['breadth_z'], FE['junction_gap_cells'])
    fan = steel_fan(B['cants'], sqb, B['foremost_head_x'], B['foremost_heel_x'], B['breadth_z'], cx, +1,
                    first_head=fhb, arc=B.get('arc_spacing', False))
    out['bow']['first_head_x'] = fhb
    # 雙片（2026-10-11 雕之前修）：每對兩片各 sided 格，船頭側（d ≥ 0）先、船尾側讓；原本單片看起來像稀疏的板條
    dbl = B.get('double', False)
    for k, (heel, head) in enumerate(fan, 1):
        if dbl:
            cant_pair(cx, 'B-cant%d' % k, 'bow_cant', heel, head, B['sided'])
        else:
            cant(cx, 'B-cant%d' % k, 'bow_cant', heel, head, -B['sided'] / 2, B['sided'] / 2)
    out['bow']['fan'] = [{'k': k + 1, 'heel': [round(float(a), 2) for a in h], 'head': [round(float(a), 2) for a in q]} for k, (h, q) in enumerate(fan)]
    heel6, head6 = fan[-1]
    u6 = unit(head6 - heel6)
    fore_d = float(B['sided']) if dbl else B['sided'] / 2
    def fore_of_last(X, Y, Zc):          # 最前一根（一對）cant 的船頭側（d > 0）、它自己的厚度之外
        return ((X + 0.5 - heel6[0]) * u6[1] - (Y - heel6[1]) * u6[0]) >= fore_d
    # knighthead 與 hawse pieces：y 為常數的平板、在最前一根 cant 的船頭側、平面裡離船殼 ≤ moulded
    #   knighthead 兩根之間要讓 bowsprit 過 ⇒ dy 5–8；dy 3–4 在艏柱頭以下補 chock（貼著艏柱，給 bowsprit 墊底）
    KH = B['knighthead']
    for nm, (d0, d1), mfix, ztop in [('B-knighthead', KH['dy'], KH['moulded'], None),
                                     ('B-knighthead-chock', KH['chock_dy'], KH['moulded'], KH['chock_top_z'])] + \
            [('B-hawse%d' % (i + 1), r, B['hawse']['moulded'], None) for i, r in enumerate(B['hawse']['dy'])]:
        cells = []
        for dy in range(d0, d1 + 1):
            c = plane_band(cx, 560.0, 690.0, np.array([0.0, dy]), np.array([1.0, 0.0]), np.array([0.0, -1.0]), -0.5, 0.5,
                           mfix=mfix, zlo=7.0, extra=fore_of_last)
            cells.append(c)
        cells = np.vstack(cells) if cells else np.zeros((0, 3), int)
        if ztop is not None:
            cells = cells[cells[:, 2] <= ztop]
        if nm == 'B-knighthead':
            # 頭伸出欄杆：在船殼頂那一層的腳印上往上長到 top_z
            top_layer = {}
            for x, dy, z in cells:
                if z >= top_layer.get((x, dy), -1):
                    top_layer[(x, dy)] = z
            zt = max(top_layer.values())
            foot = [(x, dy) for (x, dy), z in top_layer.items() if z >= zt - 1]
            up = [(x, dy, z) for (x, dy) in foot for z in range(zt + 1, B['knighthead']['top_z'] + 1)]
            cells = np.vstack([cells, np.array(up, int).reshape(-1, 3)])
        kind = 'knighthead' if nm == 'B-knighthead' else ('chock' if nm.endswith('chock') else 'hawse_piece')
        cx.add(nm, kind, cells, {'dy': [d0, d1]} | ({'z_top': ztop} if ztop is not None else {}))
    return out


# ───────────────────────── 雕之前修：針孔、夾縫、同一對 cant 之間的缺口、碎塊 ─────────────────────────
def pair_of(name):
    """'S-cant3-fwd' → 'S-cant3'；不是成對的 cant ⇒ None。"""
    for suf in ('-fwd', '-aft'):
        if name.endswith(suf) and '-cant' in name:
            return name[:-len(suf)]
    return None


def fill_and_clean(cx):
    """只跑一輪（不讓填補一路長出去）。回傳讀數。作品現況 ＋ 新木料（兩舷）一起看，只在 dy ≥ 0 那一舷找、另一舷鏡像。"""
    F = cx.FE['fill']
    solid = set(cx.world.keys())
    for (x, dy, z) in cx.claim:
        solid.add((x, YC + dy, z))
        solid.add((x, YC - dy, z))
    owner = lambda x, dy, z: cx.claim.get((x, abs(dy), z))
    kind_of = {t['name']: t['kind'] for t in cx.timbers}
    nb6 = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    cand = set()
    for (x, dy, z) in cx.claim:
        for ddx, ddy, ddz in nb6:
            c = (x + ddx, dy + ddy, z + ddz)
            if c[1] < 0 or c in cx.claim or (c[0], YC + c[1], c[2]) in solid:
                continue
            cand.add(c)
    filled, why = {}, {'faces': 0, 'axes': 0, 'pair': 0}
    for (x, dy, z) in sorted(cand):
        if not cx.inside(np.array([x]), np.array([dy]), np.array([z]))[0]:
            continue
        if (x, YC + dy, z) in cx.trim or (x, YC - dy, z) in cx.trim:     # 刻掉的柱頭就是要空著
            continue
        s = [(x + a, YC + dy + b, z + c) in solid for a, b, c in nb6]
        faces = sum(s)
        axes = sum(1 for i in range(0, 6, 2) if s[i] and s[i + 1])
        pair = False
        for i in range(0, 6, 2):
            a, b, c = nb6[i]
            o1, o2 = owner(x + a, dy + b, z + c), owner(x - a, dy - b, z - c)
            if not (o1 and o2 and o1 != o2):
                continue
            if F.get('same_pair_sandwich') and pair_of(o1) and pair_of(o1) == pair_of(o2):
                pair = True
            # 指定的兩類木料之間的 1 格夾縫（最前一對船頭 cant 跟 hawse／knighthead／chock 之間的階梯縫）
            k1, k2 = kind_of[o1], kind_of[o2]
            if [k1, k2] in F.get('slot_kind_pairs', []) or [k2, k1] in F.get('slot_kind_pairs', []):
                pair = True
        if faces >= F['min_solid_faces'] or axes >= F['sandwich_axes'] or pair:
            # 歸給接觸面最多的那根新木料
            cnt = {}
            for a, b, c in nb6:
                o = owner(x + a, dy + b, z + c)
                if o:
                    cnt[o] = cnt.get(o, 0) + 1
            if not cnt:
                continue
            filled[(x, dy, z)] = max(sorted(cnt), key=lambda k: cnt[k])
            why['faces' if faces >= F['min_solid_faces'] else ('axes' if axes >= F['sandwich_axes'] else 'pair')] += 1
    for c, nm in filled.items():
        cx.claim[c] = nm
    # 碎塊：一根木料（這一舷）裡 ≤ fragment_max_cells 的元件 ⇒ 歸給接觸面最多的鄰居木料
    moved = []
    by = {}
    for c, nm in cx.claim.items():
        by.setdefault(nm, []).append(c)
    for nm, cells in by.items():
        if kind_of.get(nm) in F.get('fragment_keep_kinds', []):      # 被 counter timbers 刻意斷開的橫材，段落照設計留著
            continue
        a = np.array(cells, int)
        mn = a.min(0) - 1
        g = np.zeros(a.max(0) - mn + 2, bool)
        g[tuple((a - mn).T)] = True
        lab, n = ndimage.label(g)
        if n <= 1:
            continue
        sizes = np.bincount(lab.ravel())[1:]
        big = int(np.argmax(sizes)) + 1
        lim = max(F['fragment_max_cells'], F.get('fragment_max_frac', 0.0) * sizes.max())   # 絕對格數或主體的幾成，取大
        for li in range(1, n + 1):
            if li == big or sizes[li - 1] > lim:
                continue
            frag = [tuple(int(v) for v in p + mn) for p in np.argwhere(lab == li)]
            cnt = {}
            for (x, dy, z) in frag:
                for ddx, ddy, ddz in nb6:
                    o = owner(x + ddx, dy + ddy, z + ddz)
                    if o and o != nm:
                        cnt[o] = cnt.get(o, 0) + 1
            if cnt:
                to = max(sorted(cnt), key=lambda k: cnt[k])
                for c in frag:
                    cx.claim[c] = to
                moved.append({'from': nm, 'to': to, 'cells_half': len(frag)})
    # 每根木料的格子照 claim 重建（填補、碎塊歸屬都在 claim 上）
    for t in cx.timbers:
        t['cells_half'] = sorted(c for c, nm in cx.claim.items() if nm == t['name'])
    by_t = {}
    for c, nm in filled.items():
        by_t[nm] = by_t.get(nm, 0) + 1
    return {'filled_half': len(filled), 'filled_by_rule': why, 'filled_to': by_t, 'fragments_moved': moved}


def write_lists(cx):
    """每根木料一份清單（兩舷），絕對座標（stampvox 的 at = 0,0,0）。"""
    odir = os.path.join(cx.design, 'masks', 'ends')
    os.makedirs(odir, exist_ok=True)
    # 先清掉舊清單：木料改名、改根數之後，舊檔留著會被 glob 讀進檢查與雕刻（例：單片 B-cant1..6、B-hawse5）
    for f in os.listdir(odir):
        if f.endswith('.vox.txt'):
            os.remove(os.path.join(odir, f))
    rows = []
    col = cx.FE['color']
    for t in cx.timbers:
        cells = t['cells_half']
        lines = ['# %s（%s）—— TASK-0486 新圖紙 04 v2；兩舷 y ↔ 320 − y；x,y,z,color 絕對座標（at=0,0,0）' % (t['name'], t['kind'])]
        n = 0
        for x, dy, z in sorted(cells):
            lines.append('%d,%d,%d,%d' % (x, YC + dy, z, col))
            n += 1
            if dy != 0:              # 中線那一格只寫一次（stampvox 遇到重複格會整刀拒絕）
                lines.append('%d,%d,%d,%d' % (x, YC - dy, z, col))
                n += 1
        body = '\n'.join(lines) + '\n'
        path = os.path.join(odir, t['name'] + '.vox.txt')
        open(path, 'w', encoding='utf-8', newline='\n').write(body)
        xs = [c[0] for c in cells] or [0]
        zs = [c[2] for c in cells] or [0]
        dys = [c[1] for c in cells] or [0]
        row = {k: v for k, v in t.items() if k != 'cells_half'} | {
            'voxels': n, 'list': 'design/masks/ends/%s.vox.txt' % t['name'], 'sha256': hashlib.sha256(body.encode('utf-8')).hexdigest(),
            'bbox': [[min(xs), max(xs)], [min(dys), max(dys)], [min(zs), max(zs)]],
            'stamp': {'voxels': 'design/masks/ends/%s.vox.txt' % t['name'], 'at': '0,0,0', 'expect_pixels': n}}
        # 計畫 vs 產物：z／dy 的計畫範圍跟清單實際的 bbox 對不上就標出來（2026-10-11 verifier：taffrail 計畫 4 層、清單 1 層，沒有一行在叫）
        flags = []
        if 'z' in t and isinstance(t['z'], list) and (t['z'][0] != min(zs) or t['z'][1] != max(zs)):
            flags.append('z 計畫 %s ≠ 清單 %s' % (t['z'], [min(zs), max(zs)]))
        if isinstance(t.get('x'), list) and (t['x'][0] != min(xs) or t['x'][1] != max(xs)):
            flags.append('x 計畫 %s ≠ 清單 %s' % (t['x'], [min(xs), max(xs)]))
        if 'z_top' in t and t['z_top'] != max(zs):
            flags.append('z 上限 計畫 %s ≠ 清單 %s' % (t['z_top'], max(zs)))
        if isinstance(t.get('dy'), list) and len(t['dy']) == 2 and isinstance(t['dy'][0], int) and (t['dy'][0] != min(dys) or t['dy'][1] != max(dys)):
            flags.append('dy 計畫 %s ≠ 清單 %s' % (t['dy'], [min(dys), max(dys)]))
        if n == 0:
            flags.append('清單是空的')
        row['plan_vs_list'] = flags
        rows.append(row)
    return rows


# ───────────────────────── 圖紙 04 v2 ─────────────────────────
def render(cx, rows):
    sh = D.Sheet(2440, 1560)
    kinds = {'stern_cant': (196, 140, 96), 'fashion_piece': (168, 98, 60), 'transom': (150, 110, 70), 'counter_timber': (176, 120, 80),
             'stern_rail': (120, 90, 60), 'quarter_timber': (190, 150, 110), 'bow_cant': (196, 140, 96), 'knighthead': (150, 100, 60),
             'hawse_piece': (176, 128, 88), 'chock': (130, 92, 62)}
    by = {}
    for t in cx.timbers:
        for c in t['cells_half']:
            by[c] = t['kind']
    # 上：平面（從上往下看，每格只畫最上面那一格的木料種類），船尾與船頭各一塊
    for (x0, x1, left, scale) in ((92, 195, 80, 7.0), (600, 680, 1340, 9.0)):
        pn = D.Panel(sh, left, 100, x0, x1, -2, 60, scale)
        pn.grid(minor=10, major=50, label_x=20, label_z=20)
        top = {}
        for (x, dy, z), k in by.items():
            if x0 <= x <= x1 and z >= top.get((x, dy), (-1, ''))[0]:
                top[(x, dy)] = (z, k)
        for (x, dy), (z, k) in top.items():
            pn.poly([(x, dy - 0.5), (x + 1, dy - 0.5), (x + 1, dy + 0.5), (x, dy + 0.5)], fill=kinds[k])
        # 既有的方肋（plane A/B）位置與船殼 z 80 的水線
        xs = np.arange(x0, x1, 0.25)
        pn.line([(x, float(cx.T.hb(x, 80.0))) for x in xs if not np.isnan(cx.T.hb(x, 80.0))], D.RED, 1.4)
        pn.commit()
    sh.text(80, 24, '新圖紙 04　肋骨圖 v2（Framing：船頭與船尾）', 26, bold=True)
    sh.text(80, 62, '上：平面（俯視，每格畫最上面那根木料；紅＝船殼 Z 80 的水線）｜左下：船尾正視（counter timbers、窗台／窗楣／taffrail、wing transom、transoms）｜右下：側面', 15, color=D.CONSTR)
    # 左下：船尾正視（從船尾往前看，X 最小那一格）
    pn = D.Panel(sh, 80, 600, -60, 60, 40, 140, 6.0)
    pn.grid(minor=10, major=50, label_x=20, label_z=20)
    front = {}
    for (x, dy, z), k in by.items():
        if x <= 160 and (x < front.get((dy, z), (999, ''))[0]):
            front[(dy, z)] = (x, k)
    for (dy, z), (x, k) in front.items():
        for sg in (1, -1):
            pn.poly([(sg * dy - 0.5, z), (sg * dy + 0.5, z), (sg * dy + 0.5, z + 1), (sg * dy - 0.5, z + 1)], fill=kinds[k])
    pn.commit()
    # 右下：側面（從右舷看，每格畫 dy 最大的那根）
    for (x0, x1, left) in ((92, 200, 860), (600, 680, 1600)):
        pp = D.Panel(sh, left, 600, x0, x1, 0, 140, 5.4)
        pp.grid(minor=10, major=50, label_x=20, label_z=20)
        side = {}
        for (x, dy, z), k in by.items():
            if x0 <= x <= x1 and dy >= side.get((x, z), (-1, ''))[0]:
                side[(x, z)] = (dy, k)
        for (x, z), (dy, k) in side.items():
            pp.poly([(x, z), (x + 1, z), (x + 1, z + 1), (x, z + 1)], fill=kinds[k])
        pp.commit()
    # 圖例＋圖框
    lx, ly = 860, 1380
    for i, (k, rgb) in enumerate(kinds.items()):
        sh.d.rectangle([(lx + (i % 5) * 220) * D.SS, (ly + (i // 5) * 26) * D.SS, (lx + (i % 5) * 220 + 16) * D.SS, (ly + (i // 5) * 26 + 16) * D.SS], fill=rgb, outline=D.INK, width=D.SS)
        sh.text(lx + (i % 5) * 220 + 24, ly + (i // 5) * 26 - 2, k, 13)
    x, y, w = 80, 1300, 720
    sh.d.rectangle([x * D.SS, y * D.SS, (x + w) * D.SS, (y + 110) * D.SS], outline=D.INK, width=2 * D.SS)
    sh.text(x + 12, y + 10, cx.FE['title'], 17, bold=True)
    sh.text(x + 12, y + 40, '%d 根木料（兩舷各一份清單）、%d voxel；全部同色 %d' % (len(rows), sum(r['voxels'] for r in rows), cx.FE['color']), 14)
    sh.text(x + 12, y + 64, '設計：%s　%s　%s' % (cx.plan['author'], cx.FE['date'], cx.FE['task']), 13, color=D.CONSTR)
    sh.text(x + 12, y + 86, '排法參考 Steel 1805、Humphreys 1794 規格（出處見 plan.json framing_ends.provenance）', 13, color=D.CONSTR)
    sh.save(os.path.join(cx.design, 'sheet04_frames_v2.png'))


def main():
    design = sys.argv[1]
    cx = Ctx(design)
    out = build(cx)
    out['fill'] = fill_and_clean(cx)
    out['post_trim_cells'] = len(cx.trim)
    rows = write_lists(cx)
    out['timbers'] = rows
    out['total_voxels'] = sum(r['voxels'] for r in rows)
    render(cx, rows)
    json.dump(out, open(os.path.join(design, 'verify_frames_ends.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for r in rows:
        print('%-26s %-15s %6d  yielded %s  %s  %s' % (r['name'], r['kind'], r['voxels'], r['yielded_to'], r.get('cant_deg', ''),
                                                       ('⚠ ' + '；'.join(r['plan_vs_list'])) if r['plan_vs_list'] else ''))
    print('fill', json.dumps(out['fill'], ensure_ascii=False))
    print('post_trim_cells', out['post_trim_cells'], 'total', out['total_voxels'])


if __name__ == '__main__':
    main()
