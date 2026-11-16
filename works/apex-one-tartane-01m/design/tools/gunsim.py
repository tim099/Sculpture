# 體素格網與外部模型碰撞／腳下檢查工具（對齊 Sculpture work sub=model 世界變換：p = at + Rz(phi)*M((v - pivot)*scale)）
import math
import numpy as np


def inset_offsets(inset):
    a, b = inset, 1.0 - inset
    return np.array([[0.5, 0.5, 0.5]] + [[(a, b)[k & 1], (a, b)[(k >> 1) & 1], (a, b)[(k >> 2) & 1]] for k in range(8)])


class Grid:
    def __init__(s, cells, pad=4, outside=True):
        s.outside = outside
        c = np.asarray(cells)[:, :3].astype(int)
        s.lo = c.min(0) - pad
        s.shape = tuple(int(v) for v in c.max(0) - s.lo + 1 + pad)
        s.G = np.zeros(s.shape, bool)
        i = c - s.lo
        s.G[i[:, 0], i[:, 1], i[:, 2]] = True

    def hit(s, P):
        i = np.floor(np.asarray(P, float)).astype(int) - s.lo
        ok = np.all((i >= 0) & (i < np.array(s.shape)), -1)
        out = np.full(i.shape[:-1], s.outside, bool)
        j = i[ok]
        out[ok] = s.G[j[:, 0], j[:, 1], j[:, 2]]
        return out

    def solid(s, x, y, z):
        return bool(s.hit(np.array([[x + 0.5, y + 0.5, z + 0.5]]))[0])


class Gun:
    def __init__(s, key, t, cells, anchors, inset):
        s.key, s.work, s.scale, s.meta = key, t['work'], float(t['scale']), t['meta']
        s.pivot = np.array(t['pivot'], float)
        s.anchors = {k: np.array(v, float) + 0.5 for k, v in anchors.items()}
        c = np.asarray(cells)[:, :3].astype(float)
        s.cells = c
        s.n = len(c)
        s.samples = (c[:, None, :] + inset_offsets(inset)[None]).reshape(-1, 3)
        s.centers = c + 0.5
        s.bottom = c[c[:, 2] == c[:, 2].min()] + 0.5
        s.lo, s.hi = c.min(0), c.max(0) + 1

    def world(s, P, at, phi, mirror):
        q = (np.asarray(P, float) - s.pivot) * s.scale
        if mirror:
            q = q * np.array([1.0, -1.0, 1.0])
        c, sn = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        x = q[..., 0] * c - q[..., 1] * sn
        y = q[..., 0] * sn + q[..., 1] * c
        return np.stack([x + at[0], y + at[1], q[..., 2] + at[2]], -1)

    def bbox(s, at, phi, mirror):
        corners = np.array([[(s.lo[0], s.hi[0])[k & 1], (s.lo[1], s.hi[1])[(k >> 1) & 1], (s.lo[2], s.hi[2])[(k >> 2) & 1]] for k in range(8)], float)
        W = s.world(corners, at, phi, mirror)
        return W.min(0), W.max(0)
