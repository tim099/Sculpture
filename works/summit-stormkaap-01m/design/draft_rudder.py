# 新圖紙 06a 舵（TASK-0547 階段六）：plan.json 的 rudder ⇒ 舵子作品的清單（世界座標）＋ 船殼的 gudgeon ＋ 給遊戲的模型參數（kind=rudder、轉軸、stock-top）、verify_rudder.json。
# 用法：python -I -X utf8 -B draft_rudder.py <design 資料夾>
#   · 做法照夜隼號階段十五（舵是外部模型：遊戲 10_ship.js:37–38 用固定點 stock-top 找「腳」、31_sailing.js:89 被打掉轉向剩 12%）。
#   · 前緣貼著艉柱後緣：每一層 z，中線那幾欄（y 128–132）現況最小 x 的前一格 ＝ 舵的前緣（量現況的格，⛔ 不用公式猜）。
#   · 弦長 chord(z)（往船尾）：底部 → z_taper0 不變、到 z_taper1 線性收、z_stock 以上是舵柱（stock）。厚度：前段 3 格（|dy| ≤ 1）、後段 1 格；舵柱 stock_half 。
#   · 顏色照外板那一套：船底／藻帶／船身（藻帶上下緣照 x 起伏，draft_planking.band_edges）；pintle 帶子 73（舵上），gudgeon 73（船殼、艉柱兩側凸 1 格，不跟著轉）。
#   · 轉軸 ＝ 艉柱後緣那條線：從 (post_face(0), YC＋0.5, 0) 沿 (−rake/rake_height, 0, 1) 方向（單位化）。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull
from draft_planking import band_edges
from sk_state import state_after

NZ6 = 200


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    Rd = plan['rudder']; Pl = plan['planking']; PC = Pl['colors']
    H = Hull(plan); YC = H.YC
    W = state_after(d, 'stage5c', nz=NZ6)
    occ = np.zeros(W['hull'].shape, bool)
    for v in W.values(): occ |= v > 0
    rud = np.zeros(W['hull'].shape, np.int16)
    gud = np.zeros(W['hull'].shape, bool)
    le = {}
    for z in range(0, Rd['z_top'] + 1):
        cols = [np.nonzero(occ[:200, y, z])[0] for y in range(YC - 2, YC + 3)]
        xm = min(int(c.min()) for c in cols if len(c))
        x_le = xm - 1
        le[z] = x_le
        if z < Rd['z_taper0']: ch = Rd['chord_bottom']
        elif z < Rd['z_taper1']: ch = Rd['chord_bottom'] + (Rd['chord_mid'] - Rd['chord_bottom']) * (z - Rd['z_taper0']) / (Rd['z_taper1'] - Rd['z_taper0'])
        elif z < Rd['z_stock']: ch = Rd['chord_mid'] + (Rd['stock_chord'] - Rd['chord_mid']) * (z - Rd['z_taper1']) / (Rd['z_stock'] - Rd['z_taper1'])
        else: ch = Rd['stock_chord']
        ch = int(round(ch))
        lo, hi = band_edges(Pl, np.array([x_le + 0.5]))
        col = PC['bottom'] if z + 0.5 < lo[0] else (PC['algae'] if z + 0.5 < hi[0] else PC['topsides'])
        for k in range(ch):                                    # k ＝ 離前緣幾格（往船尾）
            x = x_le - k
            if z >= Rd['z_stock']: half = Rd['stock_half']
            else: half = 1 if k < math.ceil(ch * Rd['thick_frac']) else 0
            for y in range(YC - half, YC + half + 1):
                rud[x, y, z] = col
    # pintle 帶子（舵上，前 3 格、|dy| 加 1）＋ gudgeon（船殼，艉柱兩側凸 1 格、往前 3 格）
    for zp in Rd['pintles_z']:
        for z in (zp, zp + 1):
            x_le = le[z]
            for x in range(x_le - 2, x_le + 1):
                for y in (YC - 2, YC + 2):
                    if rud[x, y, z] == 0: rud[x, y, z] = Rd['iron']
                for y in range(YC - 1, YC + 2): rud[x, y, z] = Rd['iron']
            for y in (YC - 3, YC + 3):
                for x in range(x_le + 1, x_le + 4):
                    if not occ[x, y, z]: gud[x, y, z] = True
    # 讀數
    rud_m = rud > 0
    ov = int((rud_m & occ).sum()) + int((gud & occ).sum()) + int((rud_m & gud).sum())
    n_r = int(ndimage.label(rud_m)[1])
    x_hinge0 = float(H.post_face(0.0)); rk = plan['lines']['sternpost']
    ax = np.array([-rk['rake'] / rk['rake_height'], 0.0, 1.0]); ax = ax / np.linalg.norm(ax)
    zt = Rd['z_top']
    stock_top = [int(le[zt] - (Rd['stock_chord'] - 1) // 2), YC, zt]
    order = {'rudder': [], 'hull': []}
    od = os.path.join(d, 'masks', 'rudder'); os.makedirs(od, exist_ok=True)
    for f in os.listdir(od): os.remove(os.path.join(od, f))
    for key, name, m, col in (('rudder', 'rudder', rud_m, rud), ('hull', 'gudgeons', gud, Rd['iron'])):
        pts = np.argwhere(m)
        text = lst(pts, col[tuple(pts.T)] if not np.isscalar(col) else col)
        fn = name + '.vox.txt'
        open(os.path.join(od, fn), 'w', encoding='utf-8', newline='\n').write(text)
        order[key].append({'name': name, 'op': 'stampvox', 'file': 'masks/rudder/' + fn, 'at': [0, 0, 0], 'expect_pixels': int(len(pts)),
                           'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})
    R = {'stamp_order': order,
         'model': {'name': '舵', 'at': [round(x_hinge0, 3), YC + 0.5, 0], 'pivot': [round(x_hinge0, 3), YC + 0.5, 0], 'scale': 1,
                   'meta': {'kind': 'rudder', 'turn_axis': 'hinge', 'hinge_x': round(x_hinge0, 3), 'hinge_y': YC + 0.5, 'hinge_z': 0.0,
                            'axis_x': round(float(ax[0]), 4), 'axis_y': 0, 'axis_z': round(float(ax[2]), 4), 'max_deg': Rd['max_deg']}},
         'anchors': {'stock-top': stock_top},
         'leading_edge_x': {str(z): int(le[z]) for z in (0, 20, 40, 60, 80, zt)},
         'counts': {'rudder': int(rud_m.sum()), 'gudgeons': int(gud.sum()),
                    'by_color': {str(k): int((rud == k).sum()) for k in sorted(set(rud[rud_m].tolist()))}},
         'checks': {'overlap_with_ship': ov, 'components_rudder': n_r, 'mirror_rudder': int((rud != rud[:, ::-1, :]).sum()),
                    'mirror_gudgeons': int((gud != gud[:, ::-1, :]).sum()),
                    'leading_edge_touches_post': all(occ[le[z] + 1, YC, z] for z in range(0, zt + 1))}}
    with open(os.path.join(d, 'verify_rudder.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: R[k] for k in ('model', 'anchors', 'leading_edge_x', 'counts', 'checks')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
