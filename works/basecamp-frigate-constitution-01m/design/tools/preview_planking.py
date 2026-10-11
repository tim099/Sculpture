# 階段七的設計預覽（不經過引擎）：作品現況（events 重播）＋外板清單（dub 那份蓋過肋骨），照清單的顏色上色、深度陰影＋面向光照
# 用法：python -I preview_planking.py <輸出資料夾> [黑色色號，覆寫清單裡的黑]
import sys, os, glob, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay import replay
W = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m'
OUT = sys.argv[1]
BLACK = int(sys.argv[2]) if len(sys.argv) > 2 else None


def rgb332(i):
    return (((i >> 5) & 7) * 255 / 7, ((i >> 2) & 7) * 255 / 7, (i & 3) * 255 / 3)


vox = {k: v[0] for k, v in replay(W).items()}
for f in sorted(glob.glob(W + '/design/masks/planking/*.vox.txt')):
    for line in open(f, encoding='utf-8'):
        if line.strip() and not line.startswith('#'):
            x, y, z, c = (int(v) for v in line.split(','))
            if BLACK is not None and c == 36:
                c = BLACK
            vox[(x, y, z)] = c
P = np.array(list(vox.keys()), float) + 0.5
C = np.array([rgb332(c) if c not in (141, 177, 173, 209, 104) else (200, 175, 140) for c in vox.values()], float)
occ = set(vox.keys())


def render(region, yaw, pitch, scale, path, size=(1600, 900)):
    m = (P[:, 0] >= region[0]) & (P[:, 0] <= region[1])
    Q, K = P[m], C[m]
    yaw, pitch = math.radians(yaw), math.radians(pitch)
    fwd = np.array([-math.cos(pitch) * math.cos(yaw), -math.cos(pitch) * math.sin(yaw), -math.sin(pitch)])
    right = np.array([-math.sin(yaw), math.cos(yaw), 0.0])
    up = np.cross(right, fwd)
    ctr = Q.mean(0)
    sx = ((Q - ctr) @ right) * scale + size[0] / 2
    sy = -((Q - ctr) @ up) * scale + size[1] / 2
    dep = (Q - ctr) @ fwd
    img = np.full((size[1], size[0], 3), 235.0)
    zb = np.full((size[1], size[0]), np.inf)
    r = max(1, int(math.ceil(scale * 0.75)))
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            xi = np.round(sx + dx).astype(int)
            yi = np.round(sy + dy).astype(int)
            ok = (xi >= 0) & (xi < size[0]) & (yi >= 0) & (yi < size[1])
            idx = np.where(ok)[0]
            d = dep[idx]
            lin = yi[idx] * size[0] + xi[idx]
            o = np.lexsort((d, lin))
            lin_s, d_s, id_s = lin[o], d[o], idx[o]
            first = np.r_[True, lin_s[1:] != lin_s[:-1]]
            lin_s, d_s, id_s = lin_s[first], d_s[first], id_s[first]
            cur = zb.ravel()[lin_s]
            better = d_s < cur
            zb.ravel()[lin_s[better]] = d_s[better]
            img.reshape(-1, 3)[lin_s[better]] = K[id_s[better]]
    valid = np.isfinite(zb)
    zn = np.where(valid, zb, np.nan)
    gy, gx = np.gradient(np.nan_to_num(zn, nan=np.nanmax(zn) + 50))
    # 面向光照：用深度梯度近似法線
    nrm = np.dstack([-gx, -gy, np.ones_like(gx) * 1.5])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    L = np.array([-0.5, -0.6, 0.62])
    L /= np.linalg.norm(L)
    lam = np.clip(nrm @ L, 0, 1)
    shade = np.where(valid, 0.55 + 0.6 * lam, 1.0)
    edge = ((np.abs(gx) > 2.5) | (np.abs(gy) > 2.5)) & valid
    out = img * shade[:, :, None]
    out[edge] *= 0.6
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)


tag = '' if BLACK is None else '_k%d' % BLACK
render((80, 700), 300, 18, 2.5, os.path.join(OUT, 'pv7_full%s.png' % tag))
render((80, 260), 230, 20, 5.0, os.path.join(OUT, 'pv7_stern_q%s.png' % tag))
render((540, 700), 40, 18, 5.0, os.path.join(OUT, 'pv7_bow_q%s.png' % tag))
print('done', len(vox))
