import numpy as np
import itertools,math
def distance(a, b, p):
    d = b - a
    lo = np.array(p, float)
    hi = lo + 1
    ts = [0.0, 1.0]
    for j in range(3):
        if abs(d[j]) > 1e-12:
            ts.extend((t for t in ((lo[j] - a[j]) / d[j], (hi[j] - a[j]) / d[j]) if 0 < t < 1))
    ts = sorted(ts)
    best = (1e+99, 0)
    for left, right in zip(ts[:-1], ts[1:]):
        mid = (left + right) / 2
        v = a + d * mid
        mask = (v < lo) | (v > hi)
        bound = np.where(v < lo, lo, hi)
        dd = d[mask]
        aa = (a - bound)[mask]
        t = min(right, max(left, -float(aa @ dd) / float(dd @ dd))) if dd @ dd > 1e-12 else mid
        pt = a + d * t
        delta = np.maximum(0, np.maximum(lo - pt, pt - hi))
        dist = float(delta @ delta)
        if dist < best[0]:
            best = (dist, t)
    return (math.sqrt(best[0]), best[1])
def triangle_hits(tri):
    lo = np.floor(tri.min(axis=0)).astype(int)
    hi = np.floor(tri.max(axis=0)).astype(int)
    cand = np.array([p for p in itertools.product(*(range(lo[j], hi[j] + 1) for j in range(3))) if p in occupied], float).reshape(-1, 3)
    if not len(cand):
        return []
    edges = np.roll(tri, -1, axis=0) - tri
    axes = [*np.eye(3), np.cross(edges[0], edges[1])]
    axes += [np.cross(e, b) for e in edges for b in np.eye(3)]
    ok = np.ones(len(cand), bool)
    centers = cand + 0.5
    for axis in axes:
        if np.linalg.norm(axis) < 1e-10:
            continue
        pp = tri @ axis
        c = centers @ axis
        rad = np.abs(axis).sum() * 0.5
        ok &= (c + rad >= pp.min() + 1e-07) & (c - rad <= pp.max() - 1e-07)
    return [tuple(map(int, p)) for p in cand[ok]]
