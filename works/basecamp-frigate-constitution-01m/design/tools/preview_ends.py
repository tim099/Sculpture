# 階段六的檢查工具（2026-10-11 從 scratchpad 搬來；路徑以本作品為準）
# 設計審查用的等角預覽（不經過引擎）：既有作品（events 重播）＋新木料清單，深度緩衝逐格投影
import sys, os, glob, json, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import draft_frames_ends as DFE
W = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m'
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get('TEMP', '.'), '')
cx = DFE.Ctx(W + '/design')          # 作品現況扣掉雕兩頭之前要刻的柱頭（post_trim）
old = np.array([k for k in cx.world.keys()], int)
new = []
for f in sorted(glob.glob(W + '/design/masks/ends/*.vox.txt')):
    for line in open(f, encoding='utf-8'):
        if line.strip() and not line.startswith('#'):
            new.append([int(v) for v in line.split(',')[:3]])
new = np.array(new, int)
print('old', len(old), 'new', len(new))
olds = set(map(tuple, old))
ov = sum(1 for c in map(tuple, new) if c in olds)
print('overlap new∩old', ov)


def render(pts_list, cols, region, yaw, pitch, scale, path, size=(1400, 1000)):
    yaw, pitch = math.radians(yaw), math.radians(pitch)
    # 視線方向：從 (cos yaw, sin yaw) 方位、俯角 pitch 看過來
    fwd = np.array([-math.cos(pitch) * math.cos(yaw), -math.cos(pitch) * math.sin(yaw), -math.sin(pitch)])
    right = np.array([-math.sin(yaw), math.cos(yaw), 0.0])
    up = np.cross(right, fwd)
    allp, allc = [], []
    for P, c in zip(pts_list, cols):
        m = (P[:, 0] >= region[0]) & (P[:, 0] <= region[1])
        allp.append(P[m] + 0.5)
        allc.append(np.tile(np.array(c, float), (m.sum(), 1)))
    P = np.vstack(allp)
    C = np.vstack(allc)
    ctr = P.mean(0)
    sx = ((P - ctr) @ right) * scale + size[0] / 2
    sy = -((P - ctr) @ up) * scale + size[1] / 2
    dep = (P - ctr) @ fwd
    img = np.full((size[1], size[0], 3), 245.0)
    zb = np.full((size[1], size[0]), np.inf)
    r = max(1, int(math.ceil(scale * 0.75)))
    order = np.argsort(-dep)
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            xi = np.round(sx + dx).astype(int)
            yi = np.round(sy + dy).astype(int)
            ok = (xi >= 0) & (xi < size[0]) & (yi >= 0) & (yi < size[1])
            idx = np.where(ok)[0]
            # 深度測試（近的贏）
            d = dep[idx]
            lin = yi[idx] * size[0] + xi[idx]
            o = np.lexsort((d, lin))
            lin_s, d_s, id_s = lin[o], d[o], idx[o]
            first = np.r_[True, lin_s[1:] != lin_s[:-1]]
            lin_s, d_s, id_s = lin_s[first], d_s[first], id_s[first]
            cur = zb.ravel()[lin_s]
            better = d_s < cur
            zb.ravel()[lin_s[better]] = d_s[better]
            img.reshape(-1, 3)[lin_s[better]] = C[id_s[better]]
    # 深度陰影＋邊緣
    valid = np.isfinite(zb)
    zn = np.where(valid, zb, np.nan)
    lo, hi = np.nanpercentile(zn, 2), np.nanpercentile(zn, 98)
    shade = np.where(valid, 1.0 - 0.45 * np.clip((zn - lo) / (hi - lo + 1e-9), 0, 1), 1.0)
    gx = np.abs(np.diff(np.nan_to_num(zn, nan=hi + 50), axis=1, prepend=hi + 50))
    gy = np.abs(np.diff(np.nan_to_num(zn, nan=hi + 50), axis=0, prepend=hi + 50))
    edge = ((gx > 2.0) | (gy > 2.0)) & valid
    out = img * shade[:, :, None]
    out[edge] *= 0.55
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)


OLD = (200, 190, 175)
NEW = (205, 120, 60)
render([old, new], [OLD, NEW], (85, 215), 225, 25, 5.0, OUT + 'pv_stern_q.png')
render([old, new], [OLD, NEW], (85, 215), 180, 8, 5.0, OUT + 'pv_stern_aft.png')
render([old, new], [OLD, NEW], (585, 700), 35, 25, 6.0, OUT + 'pv_bow_q.png')
render([old, new], [OLD, NEW], (585, 700), 90, 60, 6.0, OUT + 'pv_bow_top.png')
print('done')
