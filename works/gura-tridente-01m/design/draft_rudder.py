# 三叉戟號 階段五（TASK-0558）舵：貼著艉柱後緣、頂端順著 counter 收進去（實船從 helm port 穿進船裡；不刻船殼）
#   輸入：plan.json（rudder、lines、waterline）＋「階段五之前」的組裝件（deco_base.base_grid）
#   輸出：masks/rudder/rudder.vox.txt（子作品座標）、rudder_placement.json、verify_rudder.json
#   用法：python -I -X utf8 draft_rudder.py <design> [--base=<快取.npy>]
import sys, os, json, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import deco_base as DB

YC = 200


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    cache = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--base=')), None)
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    RU = plan['rudder']
    G = np.load(cache) if cache and os.path.exists(cache) else DB.base_grid()
    S = G > 0
    zw = plan['waterline']['z']
    sub = S[:170]
    FX = np.where(sub.any(0), sub.argmax(0), -1)                    # [y, z] 從船尾往前第一格實心

    def chord(z):
        lo, mid, top = RU['chord_bottom'], RU['chord_wl'], RU['chord_head']
        if z <= zw:
            return lo + (mid - lo) * (z - RU['z_bottom']) / float(zw - RU['z_bottom'])
        return mid + (top - mid) * min(1.0, (z - zw) / float(RU['head_z'] - zw))

    cells = {}
    for z in range(RU['z_bottom'], RU['z_top'] + 1):
        xp = float(L.x_post(z + 0.5))                                 # 艉柱後緣（線形）
        xa = int(math.floor(xp - chord(z) + 0.5))
        col = RU['copper'] if z <= zw else RU['black']
        for dy in range(-RU['half_front'], RU['half_front'] + 1):
            y = YC + dy
            f = FX[y, z]
            if f < 0:
                continue
            xb = f - 1                                                # 前緣貼著現況最後面那格實心
            if xb < xa:
                continue
            for x in range(xa, xb + 1):
                frac = (xb - x) / max(1.0, float(xb - xa))            # 0 ＝ 前緣、1 ＝ 後緣
                if abs(dy) > RU['half_aft'] and frac > 0.5:
                    continue                                          # 後半薄一點
                cells[(x, y, z)] = col
    # pintle／gudgeon 帶：舵板兩側凸 1 格（離前緣 band_back 格內）＋ 艉柱兩側往前 band_fwd 格（只貼 |dy| ≤ band_dy 的空格）
    bands = 0
    for zb in RU['bands_z']:
        for z in (zb, zb + 1):
            xs = [k[0] for k in cells if k[2] == z and k[1] == YC]
            if not xs:
                continue
            xf = max(xs)
            for sgn in (-1, 1):
                for x in range(xf - RU['band_back'] + 1, xf + 1):
                    y = YC + sgn * (RU['half_front'] + 1)
                    if not S[x, y, z] and (x, y, z) not in cells:
                        cells[(x, y, z)] = RU['band']
                        bands += 1
                for x in range(xf + 1, xf + 1 + RU['band_fwd']):
                    ys = np.nonzero(S[x, :, z])[0]
                    if not len(ys):
                        continue
                    y = (ys.max() + 1) if sgn > 0 else (ys.min() - 1)
                    if abs(y - YC) <= RU['band_dy'] and not S[x, y, z]:
                        cells[(x, y, z)] = RU['band']
                        bands += 1
    # 讀數
    over = sum(1 for k in cells if S[k])
    lo = np.array([40, 150, 0]); hi = np.array([170, 251, 140])
    U = S[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]].copy()
    Ub = U.copy()
    for (x, y, z) in cells:
        U[x - lo[0], y - lo[1], z - lo[2]] = True
    lab, _ = ndimage.label(U)
    base_labels = set(np.unique(lab[Ub]).tolist()) - {0}
    floating = sum(1 for (x, y, z) in cells if lab[x - lo[0], y - lo[1], z - lo[2]] not in base_labels)
    holes = int((ndimage.binary_fill_holes(U) & ~U).sum())
    asym = sum(1 for (x, y, z) in cells if (x, 2 * YC - y, z) not in cells or cells[(x, 2 * YC - y, z)] != cells[(x, y, z)])
    zs = [k[2] for k in cells]
    org, size = DB.bbox(cells)
    n, h = DB.write_local(os.path.join(design, 'masks', 'rudder', 'rudder.vox.txt'), cells, org, '# 三叉戟號 舵（子作品座標）\n')
    place = {'rudder': {'at': org, 'size': size}}
    with open(os.path.join(design, 'rudder_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1)
    by = {int(c): int(m) for c, m in zip(*np.unique(np.array(list(cells.values())), return_counts=True))}
    R = {'cells': n, 'sha256': h, 'by_color': by, 'band_cells': bands, 'z': [min(zs), max(zs)], 'overlap_base': over, 'floating': floating,
         'cavities': holes, 'asym': asym, 'placement': place}
    with open(os.path.join(design, 'verify_rudder.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
