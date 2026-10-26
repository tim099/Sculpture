# 直接出處：gura-pinas-01m/design/gunsim.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成康塞普西翁號（TASK-0969）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/gunsim.py（收穫號，照抄後改成康塞普西翁號 —— TASK-0969）
# 康塞普西翁號 階段八（TASK-0597）砲的共用幾何：來源砲的格子、模型變換、組裝件的實心格網、碰撞取樣
#   模型變換（CLI work model；餘燼號 place_guns.py 量過）：世界 p ＝ at ＋ Rz(φ)·M(v − pivot)·scale，M ＝ mirror y（P 舷）
#   ⛔ 這裡算出來的外框，check_stage8.py 會跟 CLI `work sub=models` 印的外框逐門對 —— 公式寫錯會在那裡現形
import os, json, math
import numpy as np


def inset_offsets(inset):
    a, b = inset, 1.0 - inset
    return np.array([[0.5, 0.5, 0.5]] + [[(a, b)[k & 1], (a, b)[(k >> 1) & 1], (a, b)[(k >> 2) & 1]] for k in range(8)])


class Grid:
    """組裝件（或任一組格子）的實心格：numpy 布林格網。框外預設當實心（碰撞用：不該跑出去）；
    outside=False ⇒ 框外當空（射線用：check_stage8 v1 拿船殼格網量「砲口往外有沒有船殼」，射線一出框就算撞到 ⇒ 40 門假警報）。"""

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
        s.anchors = {k: np.array(v, float) + 0.5 for k, v in anchors.items()}       # 固定點取格心
        c = np.asarray(cells)[:, :3].astype(float)
        s.cells = c
        s.n = len(c)
        s.samples = (c[:, None, :] + inset_offsets(inset)[None]).reshape(-1, 3)
        s.centers = c + 0.5
        s.bottom = c[c[:, 2] == c[:, 2].min()] + 0.5                                   # 最底下那層（站在甲板上的那幾格）
        s.lo, s.hi = c.min(0), c.max(0) + 1

    def world(s, P, at, phi, mirror):
        q = (np.asarray(P, float) - s.pivot) * s.scale
        if mirror:
            q = q * np.array([1.0, -1.0, 1.0])
        c, sn = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        x = q[..., 0] * c - q[..., 1] * sn
        y = q[..., 0] * sn + q[..., 1] * c
        return np.stack([x + at[0], y + at[1], q[..., 2] + at[2]], -1)

    def direction(s, phi, mirror):
        """來源 +y（砲口方向）在世界 xy 的單位向量。"""
        a = s.world(s.pivot[None], (0, 0, 0), phi, mirror)[0]
        b = s.world((s.pivot + [0, 1.0, 0])[None], (0, 0, 0), phi, mirror)[0]
        d = (b - a)[:2]
        return d / np.linalg.norm(d)

    def bbox(s, at, phi, mirror):
        """模型外框（來源格子的外框八個角變換過去）—— 跟 CLI `work sub=models` 的外框對。"""
        corners = np.array([[(s.lo[0], s.hi[0])[k & 1], (s.lo[1], s.hi[1])[(k >> 1) & 1], (s.lo[2], s.hi[2])[(k >> 2) & 1]] for k in range(8)], float)
        W = s.world(corners, at, phi, mirror)
        return W.min(0), W.max(0)


def load_guns(GB, works_dir, export_list):
    out = {}
    cache = {}
    for k, t in GB['types'].items():
        w = t['work']
        if w not in cache:
            A = json.load(open(os.path.join(works_dir, w, 'anchors.json'), encoding='utf-8'))['anchors']
            cache[w] = (export_list(w, None), {a['name']: a['at'] for a in A})
        cells, anchors = cache[w]
        out[k] = Gun(k, t, cells, anchors, GB['search']['inset'])
    return out
