# 光榮號 階段九（TASK-0614）舵 —— 抄自三叉戟號 gura-tridente-01m/design/draft_rudder.py（gura，階段五）；改：
#   ① 做成外部模型（造船規格 §9 kind=rudder）：子作品用整船的框、清單是世界座標（同收穫號 -rudder，calli）⇒ 模型 at ＝ pivot ＝ 鉸鏈下端；
#   ② 船的現況讀本船的清單（mio.stage_base：船殼＋甲板＋梯子＋階段五的部件，含螺旋槳）；③ 算 meta（hinge／axis／max_deg）與 stock-top。
#   前緣貼著現況艉柱後面那一格實心（螺旋槳 aperture 在艉柱前面 ⇒ 舵柱是 aperture 後面那 5 格）；頂端順著 counter 收進去（前緣追不上就停）。
#   輸出：masks/rudder/rudder.vox.txt（世界座標）、rudder_placement.json、verify_rudder.json
#   用法：python -I -X utf8 draft_rudder.py <design> [--probe=chord:+3]
import sys, os, json, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import mio

YC = 200


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe=')), None)
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    RU = plan['rudder']
    G, _ = mio.stage_base(design, ('decks', 'ladders', 'deco'))
    S = G > 0
    zw = plan['waterline']['z']
    sub = S[:400]
    FX = np.where(sub.any(0), sub.argmax(0), -1)                    # [y, z] 從船尾往前第一格實心
    dchord = float(probe.split(':')[1]) if probe and probe.startswith('chord:') else 0.0

    def chord(z):
        lo, mid, top = RU['chord_bottom'], RU['chord_wl'], RU['chord_head']
        if z <= zw:
            c = lo + (mid - lo) * (z - RU['z_bottom']) / float(zw - RU['z_bottom'])
        else:
            c = mid + (top - mid) * min(1.0, (z - zw) / float(RU['head_z'] - zw))
        return c + dchord

    cells = {}
    front = {}                                                        # z ⇒ 前緣那一格的 x（中線）
    for z in range(RU['z_bottom'], RU['z_top'] + 1):
        xp = float(L.x_post(z + 0.5))                                 # 艉柱後緣（線形）
        xa = int(math.floor(xp - chord(z) + 0.5))
        col = RU['copper'] if z <= zw else RU['black']
        f0 = FX[YC, z]
        if f0 < 0 or f0 - 1 < xa or f0 < int(round(xp)) - 1:
            break                                                     # counter 往後挑（前緣離開艉柱線超過 1 格）⇒ 舵頂到這裡：再往上的舵板掛在 counter 後面、一轉就掃進 counter 兩側
        front[z] = int(f0 - 1)
        xb = int(f0 - 1)                                              # 前緣 ＝ 中線那一欄現況最後面那格實心的後一格（各欄一樣 ⇒ 前緣是一條直線，才能繞鉸鏈轉）
        for dy in range(-RU['half_front'], RU['half_front'] + 1):
            y = YC + dy
            for x in range(xa, xb + 1):
                frac = (xb - x) / max(1.0, float(xb - xa))            # 0 ＝ 前緣、1 ＝ 後緣
                if abs(dy) > RU['half_aft'] and frac > 0.5:
                    continue                                          # 後半薄一點
                if abs(dy) > (xb - x) + 0.5:
                    continue                                          # 前緣削斜角（離前緣第 k 欄只留 |dy| ≤ k）⇒ 轉 ±max_deg 時前角不吃進艉柱
                if S[x, y, z]:
                    continue
                cells[(x, y, z)] = col
    # pintle／gudgeon 帶：舵板兩側凸 1 格（離前緣 band_back 格內）＋ 艉柱兩側往前 band_fwd 格（只貼 |dy| ≤ band_dy 的空格）
    #   ⚠ 艉柱上那一半是船的一部分、模型轉的時候不跟著轉 ⇒ 本船只做舵板上那一半（艉柱那一半不做：模型以外的格要改船殼）
    bands = 0
    for zb in RU['bands_z']:
        for z in (zb, zb + 1):
            if z not in front:
                continue
            xf = front[z]
            for sgn in (-1, 1):
                for x in range(xf - RU['band_back'] + 1, xf - 2):            # 離前緣 3 格起（再前面一轉就吃進艉柱）
                    y = YC + sgn * (RU['half_front'] + 1)
                    if not S[x, y, z] and (x, y, z) not in cells:
                        cells[(x, y, z)] = RU['band']
                        bands += 1
    # 鉸鏈 ＝ 艉柱後緣那一面（前緣那格的 x ＋ 1）、中線兩格之間（y 200.5 ＝ 中線那一格的格心）；軸 ＝ 艉柱的傾角
    z0, z1 = min(front), max(front)
    hinge = [float(front[z0] + 1), YC + 0.5, float(z0)]
    ax = np.array([float(L.x_post(z1) - L.x_post(z0)), 0.0, float(z1 - z0)])
    ax = ax / np.linalg.norm(ax)
    stock_top = [front[z1], YC, z1]
    # 讀數
    over = sum(1 for k in cells if S[k])
    # 轉舵掃線：鉸鏈軸轉 ±max_deg、±15°，舵每一格的格心落在船（現況）實心裡幾格
    Q = np.array(sorted(cells), float) + 0.5 - np.array(hinge)
    sweep = {}
    for deg in (-RU['max_deg'], -15, 15, RU['max_deg']):
        t = math.radians(deg)
        W = Q * math.cos(t) + np.cross(ax, Q) * math.sin(t) + np.outer(Q @ ax, ax) * (1 - math.cos(t)) + np.array(hinge)
        i = np.floor(W).astype(int)
        sweep[str(deg)] = int(S[i[:, 0], i[:, 1], i[:, 2]].sum())
    lo = np.array([60, 150, 0]); hi = np.array([260, 251, 160])
    U = S[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]].copy()
    Ub = U.copy()
    for (x, y, z) in cells:
        U[x - lo[0], y - lo[1], z - lo[2]] = True
    lab, _ = ndimage.label(U)
    base_labels = set(np.unique(lab[Ub]).tolist()) - {0}
    floating = sum(1 for (x, y, z) in cells if lab[x - lo[0], y - lo[1], z - lo[2]] not in base_labels)
    R0 = np.zeros_like(U)
    for (x, y, z) in cells:
        R0[x - lo[0], y - lo[1], z - lo[2]] = True
    own_comp = int(ndimage.label(R0)[1])
    holes = int((ndimage.binary_fill_holes(U) & ~U).sum())
    asym = sum(1 for (x, y, z) in cells if (x, 2 * YC - y, z) not in cells or cells[(x, 2 * YC - y, z)] != cells[(x, y, z)])
    # 舵頭旁邊 8 格內的船尾格（遊戲在這裡找掛住的格）
    st = np.array(stock_top)
    near = 0
    for x in range(st[0] - 8, st[0] + 9):
        for y in range(st[1] - 8, st[1] + 9):
            for z in range(st[2] - 8, st[2] + 9):
                if S[x, y, z] and (x - st[0]) ** 2 + (y - st[1]) ** 2 + (z - st[2]) ** 2 <= 64:
                    near += 1
    # 螺旋槳離舵：aperture 裡的螺旋槳格 vs 舵（轉 max_deg 的時候舵的前緣在艉柱後面 ⇒ 碰不到 aperture；這裡只量距離）
    if probe:
        print('probe', probe, '格', len(cells), '跟船重疊', over)
        return
    n, h = mio.write_local(os.path.join(design, 'masks', 'rudder', 'rudder.vox.txt'), cells, (0, 0, 0), '# 光榮號 舵（世界座標 ＝ 子作品座標；模型 at ＝ pivot ＝ 鉸鏈下端）\n')
    org, size = mio.bbox(cells)
    meta = {'kind': 'rudder', 'hinge_x': hinge[0], 'hinge_y': hinge[1], 'hinge_z': hinge[2],
            'axis_x': round(float(ax[0]), 4), 'axis_y': 0.0, 'axis_z': round(float(ax[2]), 4), 'max_deg': RU['max_deg'], 'turn_axis': 'hinge'}
    place = {'work': RU['work'], 'model': RU['model'], 'at': hinge, 'pivot': hinge, 'scale': 1, 'meta': meta,
             'anchors': {'stock-top': stock_top}, 'bbox': {'origin': org, 'size': size}}
    with open(os.path.join(design, 'rudder_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    by = {int(c): int(m) for c, m in zip(*np.unique(np.array(list(cells.values())), return_counts=True))}
    R = {'cells': n, 'sha256': h, 'by_color': by, 'band_cells': bands, 'z': [z0, z1], 'overlap_base': over, 'floating': floating, 'own_components': own_comp,
         'cavities': holes, 'asym': asym, 'sweep_hits': sweep, 'stock_top_near_hull_cells': near, 'placement': place}
    with open(os.path.join(design, 'verify_rudder.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
