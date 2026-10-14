# 圖紙 F2 v1（TASK-0538 船首像）：每一高度的橫剖面 ⇒ 身體粗形（0.01 m／格）＋ 雙手 ＋ 提燈（示意）＋ 預覽圖
# 用法：python -I draft_body.py <design 資料夾>
#   · 正面遮罩那一列 ⇒ 寬（y 區間）；右側遮罩那一列 ⇒ 深（x 區間）；同一個 z（身高 H 為 1）。
#     一列有好幾段時取最長那段（斷臂、手肘縫那幾段不算身體 —— 手另外做）。沿 z 中位數平滑（雜訊、透視）。
#   · 剖面 ＝ 框在 [x 區間] × [y 區間] 裡的超橢圓 |dx/a|^n + |dy/b|^n ≤ 1（plan body.section_n）。
#   · 手：draft_sheet_f1 同一套 IK；圓錐管（肩 → 肘 → 腕 → 握點）。提燈只是示意（之後另做外部模型）。
#   ⇒ body.npz（佔格）、verify_body.json、sheetF2_v1.png
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draft_sheet_f1 import Figure, F   # noqa: E402


def row_interval(m, yimg, to_body, centre_hint=None):
    """遮罩第 yimg 列：取最長那段 ⇒ (lo, hi)（身體座標）"""
    r = m[int(round(yimg))]
    xs = np.where(r)[0]
    if len(xs) == 0:
        return None
    br = np.where(np.diff(xs) > 1)[0]
    segs = np.split(xs, br + 1)
    s = max(segs, key=len)
    a, b = to_body(s[0] - 0.5), to_body(s[-1] + 0.5)
    return min(a, b), max(a, b)


def sections(fig, dz, smooth, sigma):
    fr, ri = fig.P['photos']['front'], fig.P['photos']['right']
    zs = np.arange(0.0, 1.0 + 1e-9, dz)
    Y, Xr = [], []
    for z in zs:
        yf = fr['sole_y'] - z * fig.Hf
        yr = ri['sole_y'] - z * fig.Hr
        Y.append(row_interval(fig.mf, min(yf, fig.mf.shape[0] - 1), fig.fy))
        Xr.append(row_interval(fig.mr, min(yr, fig.mr.shape[0] - 1), fig.rx))
    ok = np.array([a is not None and b is not None for a, b in zip(Y, Xr)])
    Y = np.array([a if a is not None else (np.nan, np.nan) for a in Y], float)
    Xr = np.array([a if a is not None else (np.nan, np.nan) for a in Xr], float)
    if smooth > 1:
        for A in (Y, Xr):
            for c in (0, 1):
                v = A[:, c]
                good = ~np.isnan(v)
                v[good] = ndimage.median_filter(v[good], size=smooth, mode='nearest')
                v[good] = ndimage.gaussian_filter1d(v[good], sigma, mode='nearest')
    return zs, Y, Xr, ok


def build(fig, N, B):
    """N ＝ 每 H 幾格；回傳佔格陣列與座標原點（身體座標 → 格：(v − lo) × N）"""
    zs, Y, Xr, ok = sections(fig, 1.0 / N, B['smooth_rows'], B['smooth_sigma_rows'])
    lo = np.array(B['box_lo'])
    hi = np.array(B['box_hi'])
    shape = np.ceil((hi - lo) * N).astype(int)
    V = np.zeros(shape, bool)
    gx = lo[0] + (np.arange(shape[0]) + 0.5) / N
    gy = lo[1] + (np.arange(shape[1]) + 0.5) / N
    GX, GY = np.meshgrid(gx, gy, indexing='ij')
    n = B['section_n']
    for k_, z in enumerate(zs):
        if not ok[k_] or np.isnan(Y[k_]).any() or np.isnan(Xr[k_]).any():
            continue
        iz = int(round((z - lo[2]) * N))
        if not (0 <= iz < shape[2]):
            continue
        cx, a = (Xr[k_, 0] + Xr[k_, 1]) / 2, (Xr[k_, 1] - Xr[k_, 0]) / 2
        cy, b = (Y[k_, 0] + Y[k_, 1]) / 2, (Y[k_, 1] - Y[k_, 0]) / 2
        V[:, :, iz] |= (np.abs((GX - cx) / a) ** n + np.abs((GY - cy) / b) ** n) <= 1.0
    # 3D 平滑：照片邊緣每列 ±1–2 px 的雜訊放大到 500 層會變成一圈圈的台階 ⇒ 模糊後取一半
    V = ndimage.gaussian_filter(V.astype(np.float32), B['smooth_3d_sigma']) > 0.5
    # 手：圓錐管
    R = fig.P['arms']['radius_H']
    gz = lo[2] + (np.arange(shape[2]) + 0.5) / N
    arms = np.zeros_like(V)
    for side in ('left', 'right'):
        A = fig.arms[side]
        for P0, P1, r0, r1 in ((A['S'], A['E'], R['shoulder'], R['elbow']), (A['E'], A['W'], R['elbow'], R['wrist']),
                               (A['W'], A['tip'], R['wrist'], R['wrist'] * 0.85)):
            seg_capsule(arms, lo, N, P0, P1, r0, r1)
    L = fig.lantern
    lant = np.zeros_like(V)
    w = L['w'] / 2
    ix = slice(*[int(round((v - lo[0]) * N)) for v in (L['cx'] - w, L['cx'] + w)])
    iy = slice(*[int(round((v - lo[1]) * N)) for v in (L['cy'] - w, L['cy'] + w)])
    iz = slice(*[int(round((v - lo[2]) * N)) for v in (L['bottom'], L['body_top'])])
    lant[ix, iy, iz] = True
    return V, arms, lant, (zs, Y, Xr, ok), lo


def seg_capsule(M, lo, N, P0, P1, r0, r1):
    P0, P1 = np.asarray(P0, float), np.asarray(P1, float)
    rmax = max(r0, r1)
    a = np.minimum(P0, P1) - rmax
    b = np.maximum(P0, P1) + rmax
    i0 = np.maximum(np.floor((a - lo) * N).astype(int), 0)
    i1 = np.minimum(np.ceil((b - lo) * N).astype(int), np.array(M.shape))
    if (i1 <= i0).any():
        return
    g = [lo[d] + (np.arange(i0[d], i1[d]) + 0.5) / N for d in range(3)]
    X, Y, Z = np.meshgrid(*g, indexing='ij')
    Pt = np.stack([X, Y, Z], -1)
    d = P1 - P0
    t = np.clip(((Pt - P0) @ d) / (d @ d), 0, 1)
    C = P0 + t[..., None] * d
    r = r0 + (r1 - r0) * t
    M[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]] |= np.linalg.norm(Pt - C, axis=-1) <= r


def render(occ_list, yaw_deg, size, N, pitch_deg=8):
    """簡單正交渲染：表面格點旋轉後做深度緩衝，用深度梯度打光。occ_list ＝ [(佔格, 顏色)]"""
    yaw, pit = math.radians(yaw_deg), math.radians(pitch_deg)
    pts, cols = [], []
    for occ, col in occ_list:
        surf = occ & ~ndimage.binary_erosion(occ)
        p = np.argwhere(surf).astype(np.float32)
        pts.append(p)
        cols.append(np.tile(np.array(col, np.float32), (len(p), 1)))
    P = np.vstack(pts)
    Cc = np.vstack(cols)
    c = P.mean(0)
    P = P - c
    # yaw ＝ 觀者站的方位角（0 ＝ 她正前方 +x、90 ＝ 她的左手邊 +y、−90 ＝ 右手邊）；畫面右 ＝ (−sin yaw, cos yaw)
    # （v1 標籤把 ±90 弄反：標「右側」的那張其實是從她左邊看的）
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    u = -np.sin(yaw) * x + np.cos(yaw) * y               # 畫面橫軸
    dpt = -(np.cos(yaw) * x + np.sin(yaw) * y)           # 深度（越小越近）
    v = z * math.cos(pit) - dpt * math.sin(pit)
    dpt = dpt * math.cos(pit) + z * math.sin(pit)
    W, H = size
    s = min(W / (np.ptp(u) + 20), H / (np.ptp(v) + 20))
    iu = ((u - u.min()) * s + 10).astype(int)
    iv = (H - 10 - (v - v.min()) * s).astype(int)
    keep = (iu >= 0) & (iu < W) & (iv >= 0) & (iv < H)
    iu, iv, dpt, Cc = iu[keep], iv[keep], dpt[keep], Cc[keep]
    zb = np.full((H, W), np.inf, np.float32)
    order = np.argsort(-dpt)                              # 遠的先畫、近的蓋上去
    img = np.full((H, W, 3), 245, np.float32)
    k = max(1, int(math.ceil(s)))
    for dy in range(k):
        for dx in range(k):
            yy, xx = np.clip(iv[order] + dy, 0, H - 1), np.clip(iu[order] + dx, 0, W - 1)
            zb[yy, xx] = dpt[order]
            img[yy, xx] = Cc[order]
    D = np.where(np.isinf(zb), np.nan, zb)
    Df = ndimage.gaussian_filter(np.nan_to_num(D, nan=np.nanmax(D)), 1.2)     # 抹平 1 格的台階，不然打光變成一圈圈橫紋
    gy, gx = np.gradient(Df)
    nrm = 1 / np.sqrt(1 + (gx / s) ** 2 + (gy / s) ** 2)
    light = np.clip(0.35 + 0.65 * nrm - 0.25 * np.clip(gx / s, -1, 1), 0.2, 1.0)
    out = img * np.where(np.isinf(zb), 1.0, light)[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def main():
    design = sys.argv[1]
    fig = Figure(design)
    B = fig.P['body']
    H_m = fig.P['placement']['H_m']
    N = int(round(H_m / fig.P['work']['meters_per_voxel']))       # 每 H 幾格（5.0 m ÷ 0.01 ＝ 500）
    V, arms, lant, (zs, Y, Xr, ok), lo = build(fig, N, B)
    np.savez_compressed(os.path.join(design, 'body.npz'), body=V, arms=arms, lantern=lant, lo=lo, N=N)
    allv = V | arms
    lab, ncomp = ndimage.label(allv)
    ver = {'N_per_H': N, 'H_m': H_m, 'shape': list(V.shape), 'body_cells': int(V.sum()), 'arm_cells': int((arms & ~V).sum()),
           'lantern_cells_placeholder': int(lant.sum()), 'components_body_arms': int(ncomp),
           'rows_without_section': int((~ok).sum()), 'section_n': B['section_n']}
    # 剖面讀數（關鍵高度）
    levels = B['levels']
    ver['levels'] = {}
    for name, z in levels.items():
        k_ = int(round(z * N))
        ver['levels'][name] = {'z': z, 'width_H': round(float(Y[k_, 1] - Y[k_, 0]), 4), 'depth_H': round(float(Xr[k_, 1] - Xr[k_, 0]), 4),
                               'width_m': round(float(Y[k_, 1] - Y[k_, 0]) * H_m, 3), 'depth_m': round(float(Xr[k_, 1] - Xr[k_, 0]) * H_m, 3)}
    # ── 圖紙 F2
    Wd, Hd = 2400, 1560
    im = Image.new('RGB', (Wd, Hd), (252, 252, 250))
    d = ImageDraw.Draw(im)
    d.text((20, 12), '夜燈號 船首像 —— 圖紙 F2 v1：橫剖面與粗形（臉、髮、衣褶的細部在 F3）', fill=(30, 30, 30), font=F(26))
    # (a) 正面／側面外輪廓＋剖面高度
    S, ox, oz = 700, 60, 800
    for which, ox_ in (('front', 260), ('right', 600)):
        for a, b in fig.outline_pts(which):
            d.point((ox_ + a * S, oz - b * S), fill=(70, 70, 70))
    for name, z in levels.items():
        d.line([(120, oz - z * S), (820, oz - z * S)], fill=(200, 80, 80))
        d.text((826, oz - z * S - 8), name, fill=(200, 80, 80), font=F(13))
    d.text((60, 52), '(a) 外輪廓（左：正面、右：右側）與剖面高度', fill=(30, 30, 30), font=F(18))
    # (b) 剖面（每格 0.4 H 見方）
    cell, sc = 230, 520
    x0, y0 = 960, 60
    d.text((x0, y0 - 8), '(b) 橫剖面（從上往下看；上 ＝ 往前、右 ＝ 她的左手）；虛框 ＝ 正面寬 × 側面深，填色 ＝ 超橢圓 n＝%.1f＋手' % B['section_n'], fill=(30, 30, 30), font=F(16))
    for i, (name, z) in enumerate(levels.items()):
        cx0 = x0 + (i % 6) * cell
        cy0 = y0 + 20 + (i // 6) * (cell + 24)
        iz = int(round((z - lo[2]) * N))
        sl = V[:, :, iz] | arms[:, :, iz]
        pts = np.argwhere(sl)
        d.rectangle([cx0, cy0, cx0 + cell - 8, cy0 + cell - 8], outline=(220, 220, 220))
        cxm, cym = cx0 + (cell - 8) / 2, cy0 + (cell - 8) / 2
        # 身體座標中心（0, 0）放在格子中央
        for (ix, iy) in pts:
            xb = lo[0] + (ix + 0.5) / N
            yb = lo[1] + (iy + 0.5) / N
            d.point((cxm + yb * sc * 0.4, cym - xb * sc * 0.4), fill=(150, 120, 90) if V[ix, iy, iz] else (200, 120, 0))
        k_ = int(round(z * N))
        if not np.isnan(Y[k_]).any() and not np.isnan(Xr[k_]).any():
            d.rectangle([cxm + Y[k_, 0] * sc * 0.4, cym - Xr[k_, 1] * sc * 0.4, cxm + Y[k_, 1] * sc * 0.4, cym - Xr[k_, 0] * sc * 0.4], outline=(200, 80, 80))
        L = ver['levels'][name]
        d.text((cx0 + 4, cy0 + 4), f'{name}  z {z:.2f}', fill=(30, 30, 30), font=F(13))
        d.text((cx0 + 4, cy0 + cell - 28), f'寬 {L["width_m"]:.2f} × 深 {L["depth_m"]:.2f} m', fill=(90, 90, 90), font=F(12))
    # (c) 預覽
    ivory, gold, lamp = (235, 228, 210), (200, 150, 60), (255, 200, 80)
    occ = [(V, ivory), (arms & ~V, (225, 215, 195)), (lant, lamp)]
    xs_ = 60
    for yaw, title in ((0, '正面'), (35, '左前（燈那一側）'), (-90, '右側'), (-145, '右後')):
        r = render(occ, yaw, (330, 600), N)
        im.paste(r, (xs_, 900))
        d.text((xs_ + 6, 904), f'(c) {title}', fill=(30, 30, 30), font=F(15))
        xs_ += 345
    d.text((60, 1515), f'粗形：身體 {ver["body_cells"]:,} 格、手 {ver["arm_cells"]:,} 格（0.01 m／格、H ＝ {H_m} m）；提燈是示意方塊，之後另做外部模型。'
                       f'剖面只用兩張照片的外輪廓 ⇒ 胸、背、衣褶的起伏還沒有（F3）。', fill=(90, 90, 90), font=F(14))
    im.save(os.path.join(design, 'sheetF2_v1.png'))
    ver['outputs'] = ['sheetF2_v1.png', 'body.npz']
    json.dump(ver, open(os.path.join(design, 'verify_body.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k_: ver[k_] for k_ in ('shape', 'body_cells', 'arm_cells', 'components_body_arms', 'rows_without_section')}))


if __name__ == '__main__':
    main()
