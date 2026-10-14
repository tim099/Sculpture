# 圖紙 F3 v1（TASK-0538 船首像）：F2 粗形 ＋ 解剖與細部 ⇒ 身體（0.01 m／格）
# 用法：python -I draft_f3.py <design 資料夾>
#   · 剖面：正面寬 × 側面深的框裡的超橢圓，前後半邊各自的指數（plan f3.zones；臉那幾層前面收尖）。
#     量剖面前先把斷臂從正面遮罩切掉（trace_params cut_poly）。
#   · 脖子：深度不超過寬 × neck_depth_ratio（側面那幾層含後面垂下的髮綹與斜方肌）。
#   · 胸：乳房那幾層的前緣先壓到胸廓線（上下兩層內插），再加兩顆橢球（照片讀數）。
#   · 臉：前緣壓到臉面（plan f3.face_plane），中線加一道窄脊照側面輪廓（鼻、唇、下巴）；挖兩個眼窩。
#   · 髮髻：後腦一顆橢球。
#   · 浮雕（雙向）：照片高通濾波 ⇒ 暗的谷往裡刻、亮的稜往外長（正面照 +x 那面、右側照 −y 那面）；只在衣褶與頭髮的區域。
#   ⇒ f3.npz、verify_f3.json、sheetF3_v1.png（剖面＋細部示意；真樣子看引擎圖）
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draft_sheet_f1 import Figure, F   # noqa: E402
from draft_body import sections, seg_capsule   # noqa: E402
from trace_photos import load   # noqa: E402


def interp_pts(pts, z):
    p = np.array(pts, float)
    return float(np.interp(z, p[:, 0], p[:, 1]))


def ellipsoid(M, lo, N, c, r):
    c, r = np.asarray(c, float), np.asarray(r, float)
    i0 = np.maximum(np.floor((c - r - lo) * N).astype(int), 0)
    i1 = np.minimum(np.ceil((c + r - lo) * N).astype(int), np.array(M.shape))
    g = [lo[d] + (np.arange(i0[d], i1[d]) + 0.5) / N for d in range(3)]
    X, Y, Z = np.meshgrid(*g, indexing='ij')
    inside = ((X - c[0]) / r[0]) ** 2 + ((Y - c[1]) / r[1]) ** 2 + ((Z - c[2]) / r[2]) ** 2 <= 1
    return (slice(i0[0], i1[0]), slice(i0[1], i1[1]), slice(i0[2], i1[2])), inside


def highpass(view, sigma):
    img, _ = load(view)
    lum = img.mean(2)
    return lum - ndimage.gaussian_filter(lum, sigma)


def main():
    design = sys.argv[1]
    fig = Figure(design)
    B, G = fig.P['body'], fig.P['f3']
    H_m = fig.P['placement']['H_m']
    N = int(round(H_m / fig.P['work']['meters_per_voxel']))
    zs, Y, Xr, ok = sections(fig, 1.0 / N, B['smooth_rows'], B['smooth_sigma_rows'])
    lo, hi = np.array(B['box_lo']), np.array(B['box_hi'])
    shape = np.ceil((hi - lo) * N).astype(int)
    V = np.zeros(shape, bool)
    gx = lo[0] + (np.arange(shape[0]) + 0.5) / N
    gy = lo[1] + (np.arange(shape[1]) + 0.5) / N
    GX, GY = np.meshgrid(gx, gy, indexing='ij')
    ver = {'N_per_H': N, 'H_m': H_m}
    # 每一列的框，套上各區的修正
    rows = []
    for k_, z in enumerate(zs):
        if not ok[k_] or np.isnan(Y[k_]).any() or np.isnan(Xr[k_]).any():
            rows.append(None)
            continue
        yL, yR = Y[k_]
        xB, xF = Xr[k_]
        zone = next(zn for zn in G['zones'] if zn['z'][0] <= z < zn['z'][1])
        if G['neck']['z'][0] <= z < G['neck']['z'][1]:
            xB = max(xB, xF - (yR - yL) * G['neck']['depth_ratio'])
        if G['breast']['z'][0] <= z < G['breast']['z'][1]:
            xF = min(xF, interp_pts(G['breast']['chest_line_z_x'], z))
        if z >= G['face_plane']['z_from']:
            xF = min(xF, interp_pts(G['face_plane']['z_x'], z))
        rows.append((z, yL, yR, xB, xF, zone['n_front'], zone['n_back']))
    for k_, r in enumerate(rows):
        if r is None:
            continue
        z, yL, yR, xB, xF, nf, nb = r
        iz = int(round((z - lo[2]) * N))
        if not (0 <= iz < shape[2]):
            continue
        cy, b = (yL + yR) / 2, (yR - yL) / 2
        cx = (xB + xF) / 2
        a = (xF - xB) / 2
        dx = (GX - cx) / a
        n = np.where(dx >= 0, nf, nb)
        V[:, :, iz] |= (np.abs(dx) ** n + np.abs((GY - cy) / b) ** n) <= 1.0
    V = ndimage.gaussian_filter(V.astype(np.float32), B['smooth_3d_sigma']) > 0.5
    # 胸
    for c, r in G['breast']['ellipsoids']:
        sl, ins = ellipsoid(V, lo, N, c, r)
        V[sl] |= ins
    # 臉：中線窄脊（鼻、唇、下巴）—— 前緣 ＝ 側面輪廓的前緣（未壓到臉面的那個）
    Fc = G['face_ridge']
    for k_, z in enumerate(zs):
        if not (Fc['z'][0] <= z <= Fc['z'][1]) or rows[k_] is None:
            continue
        iz = int(round((z - lo[2]) * N))
        xF_true = Xr[k_, 1]
        xP = rows[k_][4]
        if xF_true <= xP:
            continue
        w = interp_pts(Fc['half_width_z'], z)
        cy = interp_pts(Fc['centre_y_z'], z)
        dy = np.abs(GY - cy) / w
        reach = xP + (xF_true - xP) * np.sqrt(np.clip(1 - dy ** 2, 0, 1))
        V[:, :, iz] |= (GX <= reach) & (GX >= xP - 0.02) & (dy <= 1)
    # 眼窩
    for c, r in G['eye_sockets']:
        sl, ins = ellipsoid(V, lo, N, c, r)
        V[sl] &= ~ins
    # 髮髻
    sl, ins = ellipsoid(V, lo, N, *G['bun'])
    V[sl] |= ins
    # 浮雕：照片暗線往裡刻
    fr, ri = fig.P['photos']['front'], fig.P['photos']['right']
    R = G['relief']
    carved = 0
    grown = 0
    for view in ('front', 'right'):
        mask = fig.mf if view == 'front' else fig.mr
        for (za, zb_), gain, dmax, dout, sig in R['bands']:
            hp = highpass(view, sig)
            for iz in range(int((za - lo[2]) * N), int((zb_ - lo[2]) * N)):
                z = lo[2] + (iz + 0.5) / N
                if view == 'front':
                    yimg = fr['sole_y'] - z * fig.Hf
                    for iy in range(shape[1]):
                        y = gy[iy]
                        ximg = fr['mid_x'] + y * fig.Hf
                        if not (0 <= ximg < hp.shape[1]) or not mask[int(yimg), int(ximg)]:
                            continue
                        hv = hp[int(yimg), int(ximg)] * gain
                        d = int(np.clip(round(hv), -dmax, dout))       # < 0 ＝ 暗的谷往裡刻、> 0 ＝ 亮的稜往外長
                        if d == 0:
                            continue
                        col = np.where(V[:, iy, iz])[0]
                        if len(col):
                            t = col.max()
                            if d < 0:
                                V[t + d + 1:t + 1, iy, iz] = False
                                carved += -d
                            else:
                                V[t + 1:min(t + 1 + d, shape[0]), iy, iz] = True
                                grown += d
                else:
                    yimg = ri['sole_y'] - z * fig.Hr
                    for ix in range(shape[0]):
                        x = gx[ix]
                        ximg = ri['ref_x'] + x * fig.Hr
                        if not (0 <= ximg < hp.shape[1]) or not mask[int(yimg), int(ximg)]:
                            continue
                        hv = hp[int(yimg), int(ximg)] * gain
                        d = int(np.clip(round(hv), -dmax, dout))
                        if d == 0:
                            continue
                        col = np.where(V[ix, :, iz])[0]                 # 她的右側 ＝ y 最小那面
                        if len(col):
                            t = col.min()
                            if d < 0:
                                V[ix, t:t - d, iz] = False
                                carved += -d
                            else:
                                V[ix, max(t - d, 0):t, iz] = True
                                grown += d
    ver['relief_carved_cells'] = int(carved)
    ver['relief_grown_cells'] = int(grown)
    # 手、提燈（同 F2）
    Rr = fig.P['arms']['radius_H']
    arms = np.zeros_like(V)
    for side in ('left', 'right'):
        A = fig.arms[side]
        for P0, P1, r0, r1 in ((A['S'], A['E'], Rr['shoulder'], Rr['elbow']), (A['E'], A['W'], Rr['elbow'], Rr['wrist']),
                               (A['W'], A['tip'], Rr['wrist'], Rr['wrist'] * 0.85)):
            seg_capsule(arms, lo, N, P0, P1, r0, r1)
    L = fig.lantern
    lant = np.zeros_like(V)
    w = L['w'] / 2
    ix = slice(*[int(round((v - lo[0]) * N)) for v in (L['cx'] - w, L['cx'] + w)])
    iy = slice(*[int(round((v - lo[1]) * N)) for v in (L['cy'] - w, L['cy'] + w)])
    izs = slice(*[int(round((v - lo[2]) * N)) for v in (L['bottom'], L['body_top'])])
    lant[ix, iy, izs] = True
    lab, ncomp = ndimage.label(V | arms)
    sizes = np.bincount(lab.ravel())[1:]
    ver.update({'body_cells': int(V.sum()), 'arm_cells': int((arms & ~V).sum()), 'components': int(ncomp),
                'component_sizes_top5': sorted(sizes.tolist(), reverse=True)[:5]})
    # 剖面讀數
    ver['levels'] = {}
    for name, z in B['levels'].items():
        k_ = int(round(z * N))
        r = rows[k_]
        if r:
            ver['levels'][name] = {'z': z, 'width_m': round((r[2] - r[1]) * H_m, 3), 'depth_m': round((r[4] - r[3]) * H_m, 3)}
    np.savez_compressed(os.path.join(design, 'f3.npz'), body=V, arms=arms, lantern=lant, lo=lo, N=N)
    json.dump(ver, open(os.path.join(design, 'verify_f3.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: ver[k] for k in ('body_cells', 'arm_cells', 'components', 'component_sizes_top5', 'relief_carved_cells', 'relief_grown_cells')}))
    print({k: v for k, v in ver['levels'].items()})


if __name__ == '__main__':
    main()
