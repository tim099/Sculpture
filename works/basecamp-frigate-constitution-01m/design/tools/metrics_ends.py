# 階段六的檢查工具（2026-10-11 從 scratchpad 搬來；路徑以本作品為準）
import sys, os, json, numpy as np
D = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m/design'
sys.path.insert(0, D)
import draft_ends as DE
plan, src, tr, H = DE.load(D)
W = DE.WLZ
def curve(z, x0, x1):
    xs = np.arange(x0, x1, 0.05)
    v = np.array([H.hb(x, [z])[0] for x in xs]); ok = ~np.isnan(v)
    return np.c_[xs[ok], v[ok]]
def seg_dist(P, C):
    # P: points (n,2); C: polyline (m,2) → min distance from each P to polyline
    A = C[:-1]; B = C[1:]; AB = B - A; L2 = (AB ** 2).sum(1) + 1e-12
    out = []
    for p in P:
        t = np.clip(((p - A) * AB).sum(1) / L2, 0, 1)
        Q = A + AB * t[:, None]
        out.append(np.sqrt(((Q - p) ** 2).sum(1)).min())
    return np.array(out)
res = {}
for key, pts in tr.items():
    w = key[1]
    if w not in W: continue
    z = W[w]
    if key[0] == 's':
        if w == 'B': lo = 169.5
        else: lo = plan['ends']['stern']['wl_end_x'][w]
        hi = H.XS; C = curve(z, 95, H.XS + 0.01)
        # junction ratio (design / lines at station 9) for the corrected metric
        xj = H.XS
    else:
        lo = max(H.XB, plan['ends']['bow']['trace_from_x'].get(w, 0)); hi = plan['ends']['bow']['wl_end_x_lines'][w]
        C = curve(z, H.XB, 680); xj = H.XB
    P = np.array([p for p in pts if lo <= p[0] <= hi])
    if len(P) < 3 or len(C) < 3: continue
    dn = seg_dist(P, C)
    # 扣掉接縫站的刻意修正：描線按 r = (h_design − 2.5)/(g − g_end) 縮放（以接縫站為準）
    g = np.interp(xj, P[:, 0], P[:, 1]) if P[0, 0] <= xj <= P[-1, 0] else None
    hd = H.hb(xj, [z])[0]
    if g is None:
        f = np.polyfit(P[:8, 0], P[:8, 1], 1) if key[0] == 'b' else np.polyfit(P[-8:, 0], P[-8:, 1], 1)
        g = np.polyval(f, xj)
    ge = 1.65
    r = (hd - 2.5) / (g - ge)
    Pc = np.c_[P[:, 0], 2.5 + (P[:, 1] - ge) * r]
    # 收尾點也移到設計的收尾（船頭：rabbet）—— t 線性重排
    xe_l = plan['ends']['bow']['wl_end_x_lines'][w] if key[0] == 'b' else plan['ends']['stern']['wl_end_x'][w]
    xe_d = C[-1, 0] if key[0] == 'b' else C[0, 0]
    Pc2 = Pc.copy(); Pc2[:, 0] = xj + (Pc[:, 0] - xj) * (xe_d - xj) / (xe_l - xj)
    dc = seg_dist(Pc2, C)
    res[key] = {'n': len(P), 'normal_raw_max': round(float(dn.max()), 2), 'normal_raw_rms': round(float(np.sqrt((dn**2).mean())), 2),
                'junction_ratio': round(float(r), 3), 'shape_after_corrections_max': round(float(dc.max()), 2), 'shape_rms': round(float(np.sqrt((dc**2).mean())), 2)}
for k, v in res.items(): print(k, v)

