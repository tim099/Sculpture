# 利劍號 新圖紙 01（TASK-0022 步驟 3）：線形 ⇒ 船殼清單 masks/hull/hull_01.vox.txt、讀數 verify_lines.json、
#   圖紙 sheet01_lines_v1.png、跟 Chapman 原圖的對照 overlay_bodyplan_v1.png、overlay_profile_v1.png
#   用法：python -I -X utf8 draft_lines.py [--probe=scale_y=1.05]
#   出處：claude-galiot-01m/design/draft_lines.py（蠍子號）改：半寬改用 lines.py 的剖面表；多了艏柱頭、wale 兩條、砲門與槳門；
#        對照圖直接畫回 Chapman 的掃描（像素 ＝ 公尺 ÷ K ÷ m_per_px）。
#   · 只讀 plan.json、sections.json、原圖，不碰作品。圖紙文字英文＋Pillow 內建字型（換一台機器也逐位元組相同）。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
PLAN = HL.load_plan(HERE)
X1 = PLAN['space']['hull'][0] - 1
ZMAX = PLAN['space']['hull'][2] - 1
V = HL.V
SCAN = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', '..', '..', '..', 'FAR-92', 'sayf', 'research', 'plans_agent', 'sources',
                                     'Chapman_1768_PlLVIII_SMM_ArchitecturanLVIII_4000px.jpg'))
# 原圖座標（lines_agent calib）：側視 AP x 526.07、基線 y = a·x + b；body plan 中線 x 2125.5、基線 y 773.14
MPX, AP_PX, BA, BB, BP_CX, BP_BY = 0.014457, 526.07, -0.002472920132139914, 1149.0815406648483, 2125.5, 773.1387559808612


def palette_rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def main_rail(L, Xm):
    """主舷牆頂（不含後甲板舷牆、船首凹弧）：腰部那段往兩頭線性外延。"""
    pts = [p for p in L.top_pts if 5.9 * L.K <= p[0] <= 32.6 * L.K]
    a = np.array([p[0] for p in pts]); b = np.array([p[1] for p in pts])
    Xm = np.asarray(Xm, float)
    lo = b[0] + (b[1] - b[0]) / (a[1] - a[0]) * (Xm - a[0])
    hi = b[-1] + (b[-1] - b[-2]) / (a[-1] - a[-2]) * (Xm - a[-1])
    return np.where(Xm < a[0], lo, np.where(Xm > a[-1], hi, np.interp(Xm, a, b)))


def hull_cells(L, plan):
    hb = plan['hull_build']
    wall = V(hb['wall'])
    C = {k: V(v) for k, v in hb['colors'].items()}
    wl = plan['waterline']['z']
    S = L.solid(0, X1, ZMAX, 0.0)
    Sx = np.pad(L.solid(0, X1, ZMAX, 3.0), 1)
    dist = ndimage.distance_transform_edt(Sx)[1:-1, 1:-1, 1:-1]
    shell = S & (dist <= wall)
    W = 2 * L.YC + 1
    # 艏柱頭：艏柱外緣往後 3 格、龍骨寬，從船殼頂一路到 stem_outer 的最高點
    head = np.zeros_like(S)
    zs_top = L.stem[-1][0]
    dyok = np.abs(np.arange(W) - L.YC) <= L.keel_hw
    for z in range(ZMAX + 1):
        zm = (z + 0.5) * 0.1
        if zm > zs_top:
            break
        xf = L.XAP + float(L.x_fwd(zm)) * 10
        for x in range(int(np.floor(xf)) - 2, int(np.floor(xf)) + 1):
            if 0 <= x <= X1 and x + 0.5 <= xf + 0.5:
                head[x, dyok, z] = True
    solid = shell | head
    outer = solid & ((dist <= 1.0) | head)
    col = np.zeros(S.shape, np.uint8)
    Z = np.arange(ZMAX + 1)[None, None, :]
    col[solid] = C['inner']
    col[outer & (Z <= wl)] = C['bottom']
    col[outer & (Z > wl)] = C['topside']
    xs = np.arange(0, X1 + 1) + 0.5
    Xm = L.x_m(xs)
    mr = main_rail(L, Xm)
    top = L.top(Xm)
    for i in range(len(xs)):
        # wale 兩條（AG lower_wale 船中 Z 3.29、wale_top 4.17 ⇒ 主舷牆頂往下 1.97、1.09 m，各 2 格）
        for off in V(hb['wales']):
            zc = int(np.floor((mr[i] - off) * 10))
            for z in (zc - 1, zc):
                if wl < z <= ZMAX:
                    col[i, outer[i, :, z], z] = C['wale']
        # 舷牆頂紅：每個 (x, y) 那一欄船殼最上面一格，只算 top(X) 往下 2 格以內（不然船中間那幾欄最上面是船底）
        #   （v1 只塗 floor(top) 那一層 ⇒ 舷弧台階的地方斷斷續續；步驟 4 落格後看側視圖才看到）
        zt = int(np.floor(top[i] * 10 - 1e-6))
        sh = shell[i] & ~head[i]
        for y in np.where(sh.any(axis=1))[0]:
            zz = np.where(sh[y])[0].max()
            if zz >= zt - 2:
                col[i, y, zz] = C['rail']
    # 砲門、槳門：挖穿那一段船殼（所有 y）
    ports = []
    for kind in ('gun', 'oar'):
        P = plan['ports'][kind]
        for j, X in enumerate(V(P['X'])):
            Xk = X * L.K
            w = V(P['size'])
            if kind == 'gun':
                ztop = float(np.interp(Xk, [p[0] * L.K for p in V(plan['ports']['rail_lower_XZ'])],
                                       [p[1] * L.K for p in V(plan['ports']['rail_lower_XZ'])])) - V(P['below_rail_lower'])
                zsil = ztop - w
            else:
                zsil = V(P['sill'])[j] * L.K
                ztop = zsil + w
            xa = int(round(L.XAP + (Xk - w / 2) * 10)); xb = int(round(L.XAP + (Xk + w / 2) * 10))
            za = int(round(zsil * 10)); zb = int(round(ztop * 10))
            col[xa:xb, :, za:zb] = 0
            ports.append({'kind': kind, 'X_m': round(Xk, 3), 'x': [xa, xb - 1], 'z': [za, zb - 1]})
    # 後甲板那一段的方窗、圓孔（plan.ports.window／round）
    for Xa, Xb, Zc in V(plan['ports']['window']):
        h = plan['ports']['window']['height']
        xa = int(round(L.XAP + Xa * L.K * 10)); xb = int(round(L.XAP + Xb * L.K * 10))
        za = int(round((Zc - h / 2) * L.K * 10)); zb = int(round((Zc + h / 2) * L.K * 10))
        col[xa:xb, :, za:zb] = 0
        ports.append({'kind': 'window', 'X_m': round((Xa + Xb) / 2 * L.K, 3), 'x': [xa, xb - 1], 'z': [za, zb - 1]})
    for Xc, Zc in V(plan['ports']['round']):
        r = plan['ports']['round']['diameter'] / 2 * L.K * 10
        cxx, czz = L.XAP + Xc * L.K * 10, Zc * L.K * 10
        xs_ = [x for x in range(int(cxx - r) - 1, int(cxx + r) + 2) for z in range(int(czz - r) - 1, int(czz + r) + 2) if (x + 0.5 - cxx) ** 2 + (z + 0.5 - czz) ** 2 <= r * r]
        cells_ = [(x, z) for x in range(int(cxx - r) - 1, int(cxx + r) + 2) for z in range(int(czz - r) - 1, int(czz + r) + 2) if (x + 0.5 - cxx) ** 2 + (z + 0.5 - czz) ** 2 <= r * r]
        for x, z in cells_:
            col[x, :, z] = 0
        ports.append({'kind': 'round', 'X_m': round(Xc * L.K, 3), 'cells_xz': len(cells_), 'x': [min(c[0] for c in cells_), max(c[0] for c in cells_)], 'z': [min(c[1] for c in cells_), max(c[1] for c in cells_)]})
    return col, ports, mr, top


def readings(L, plan, col, ports, mr, top):
    wl = plan['waterline']['z']
    solid = col > 0
    S = L.solid(0, X1, ZMAX, 0.0)
    xs_any = np.where(solid.any(axis=(1, 2)))[0]
    wl_x = np.where(S[:, :, wl].any(axis=1))[0]
    wl_y = np.where(S[:, :, wl].any(axis=0))[0]
    below = S[:, :, :wl + 1]
    lwl = int(wl_x.max() - wl_x.min() + 1); bwl = int(wl_y.max() - wl_y.min() + 1)
    ys = np.where(solid.any(axis=(0, 2)))[0]
    stations = {}
    for s in json.load(open(os.path.join(HERE, 'sections.json'), encoding='utf-8'))['sections']:
        x = int(np.floor(L.XAP + s['X'] * 10))
        row = {}
        for z in (5, 10, 15, 20, 25, 28, 35, 40, 45, 50):
            d = np.where(S[x, :, z])[0]
            row[str(z)] = int(d.max() - L.YC) if len(d) else None
        stations[s['station']] = {'x': x, 'half_breadth_cells': row}
    mid = int(PLAN['space']['mid_x'])
    return {
        'hull_x_range': [int(xs_any.min()), int(xs_any.max())],
        'length_pp_m': round(float(L.x_fwd(5.0 * L.K)) - float(L.x_aft(6.6 * L.K)), 2),
        'length_pp_def': 'Chapman 的兩條垂線畫在柱頂那個高度（AP x 526 px 在艉柱頂、FP x 3220 px 在艏柱 Z 5 m 處）⇒ 艏柱外緣（Z 5.0 m）到艉柱外緣（Z 6.6 m），公尺、已 × K',
        'waterline_z': wl, 'draught_m': round((wl + 1) * 0.1, 2),
        'waterline_length_m': round(lwl * 0.1, 2), 'waterline_beam_m': round(bwl * 0.1, 2),
        'beam_cells': int(ys.max() - ys.min() + 1), 'beam_m': round((ys.max() - ys.min() + 1) * 0.1, 2),
        'displacement_t': round(float(below.sum()) * 0.001 * 1.025, 1),
        'block_coefficient': round(float(below.sum()) / (lwl * bwl * (wl + 1)), 3),
        'main_rail_mid_z_m': round(float(mr[mid]), 2), 'top_at_stern_m': round(float(top[int(L.XAP)]), 2),
        'cells': int(solid.sum()),
        'colors': {str(c): int((col == c).sum()) for c in np.unique(col[col > 0])},
        'ports': ports,
        'station_half_breadths': stations,
    }


def source_checks(R, plan):
    return {c['name']: {'source': c['value'], 'work': R.get(c['key']), 'unit': c.get('unit', ''), 'src': c['src']} for c in plan['checks']}


def overlay_bodyplan(L, col, path):
    """Chapman body plan 上畫作品的剖面（站的那一欄的外緣），左半艉段、右半艏段。紅 ＝ 作品，藍點 ＝ sections.json 的讀數。"""
    im = Image.open(SCAN).convert('RGB')
    d = ImageDraw.Draw(im)
    solid = col > 0
    for s in json.load(open(os.path.join(HERE, 'sections.json'), encoding='utf-8'))['sections']:
        sg = -1 if s['X'] < 21 else 1
        x = int(np.floor(L.XAP + s['X'] * 10))
        pts = []
        for z in range(ZMAX + 1):
            ys = np.where(solid[x, :, z])[0]
            if len(ys):
                Ym = (ys.max() - L.YC + 0.5) * 0.1
                pts.append((BP_CX + sg * Ym / L.K / MPX, BP_BY - (z + 0.5) * 0.1 / L.K / MPX))
        if len(pts) > 1:
            d.line(pts, fill=(220, 0, 0), width=1)
        for z, y in s['ZY']:
            px, py = BP_CX + sg * y / L.K / MPX, BP_BY - z / L.K / MPX
            d.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5], outline=(0, 60, 220))
    im.crop((1700, 340, 2560, 790)).resize((860 * 2, 450 * 2)).save(path)


def overlay_profile(L, col, ports, path):
    """Chapman 側視上畫作品的外形輪廓（中線剖面的最上、最下、最前、最後）、砲門與槳門框。"""
    im = Image.open(SCAN).convert('RGB')
    d = ImageDraw.Draw(im)
    solid = col.any(axis=1)                              # [x, z]：任何 y 有格
    def P(xc, zc):
        X = (xc - L.XAP) * 0.1 / L.K
        x = AP_PX + X / MPX
        return x, (BA * x + BB) - zc * 0.1 / L.K / MPX
    up, lo = [], []
    for x in range(solid.shape[0]):
        zz = np.where(solid[x])[0]
        if len(zz):
            up.append(P(x + 0.5, zz.max() + 1)); lo.append(P(x + 0.5, zz.min()))
    d.line(up, fill=(220, 0, 0), width=2); d.line(lo, fill=(220, 0, 0), width=2)
    for p in ports:
        a = P(p['x'][0], p['z'][1] + 1); b = P(p['x'][1] + 1, p['z'][0])
        d.rectangle([a[0], a[1], b[0], b[1]], outline=(0, 160, 0) if p['kind'] == 'gun' else (0, 60, 220), width=2)
    im.crop((0, 380, 3800, 1170)).save(path)


def sheet(L, plan, col, R, path):
    s = 2
    Wd = (X1 + 1) * s + 120
    H = 1000
    img = Image.new('RGB', (Wd, H), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((40, 14), '%s - new sheet 01: lines   0.1 m/cell   %s %s   (Chapman 1768 Pl. LVIII No.17, scale x %.5f)' % (plan['title_en'], plan['author'], plan['date'], L.K), fill=(20, 20, 40), font=f)
    wl = plan['waterline']['z']
    ox = 60
    px = lambda x: ox + x * s
    oy = 60 + (ZMAX + 1) * s
    d.text((40, 36), '1. profile (starboard outside; bow to the right)', fill=(20, 20, 40), font=f)
    solid = col > 0
    for xi in range(col.shape[0]):
        for z in range(col.shape[2]):
            ys = np.where(solid[xi, :, z])[0]
            if len(ys):
                d.rectangle([px(xi), oy - (z + 1) * s, px(xi) + s - 1, oy - z * s - 1], fill=palette_rgb(int(col[xi, ys.max(), z])))
    d.line([px(0), oy - (wl + 1) * s, px(X1), oy - (wl + 1) * s], fill=(40, 110, 200))
    for x in range(0, X1 + 1, 20):
        d.line([px(x), oy + 4, px(x), oy + 10], fill=(80, 80, 80))
        d.text((px(x) - 8, oy + 12), str(x), fill=(80, 80, 80), font=f)
    oy2 = oy + 60 + 60 * s
    d.text((40, oy + 34), '2. half-breadths (plan view; rail top / z 40 / DWL z %d / z 10)' % wl, fill=(20, 20, 40), font=f)
    d.line([px(0), oy2, px(X1), oy2], fill=(120, 120, 120))
    for z, c in ((None, (200, 30, 30)), (40, (30, 30, 90)), (wl, (40, 110, 200)), (10, (150, 120, 60))):
        pts = []
        for xi in range(col.shape[0]):
            zz = np.where(solid[xi].any(axis=0))[0] if z is None else [z]
            if not len(zz):
                continue
            zq = zz.max() if z is None else z
            ys = np.where(solid[xi, :, zq])[0]
            if len(ys):
                pts.append((px(xi), oy2 - (ys.max() - L.YC + 1) * s))
        if len(pts) > 1:
            d.line(pts, fill=c, width=1)
    ty = oy2 + 40
    d.text((40, ty), '3. main dimensions (work -> source)', fill=(20, 20, 40), font=f)
    keys = ['length_pp_m', 'draught_m', 'waterline_length_m', 'waterline_beam_m', 'beam_m', 'displacement_t', 'block_coefficient', 'main_rail_mid_z_m', 'cells']
    for i, k in enumerate(keys):
        d.text((40 + (i % 3) * 330, ty + 20 + (i // 3) * 18), '%s = %s' % (k, R[k]), fill=(30, 30, 30), font=f)
    for i, (n, v) in enumerate(R['source_checks'].items()):
        d.text((1100, ty + 20 + i * 18), '%s: source %s -> work %s %s' % (n, v['source'], v['work'], v['unit']), fill=(160, 30, 30), font=f)
    img.save(path)


def main():
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=')
            probe[k] = float(v)
    L = HL.Lines(PLAN, probe or None)
    col, ports, mr, top = hull_cells(L, PLAN)
    R = readings(L, PLAN, col, ports, mr, top)
    R['source_checks'] = source_checks(R, PLAN)
    if probe:
        print(json.dumps({'probe': probe, 'beam_m': R['beam_m'], 'waterline_beam_m': R['waterline_beam_m'], 'displacement_t': R['displacement_t'],
                          'station_half_breadths': R['station_half_breadths']}, ensure_ascii=False))
        return
    out = os.path.join(HERE, 'masks', 'hull')
    os.makedirs(out, exist_ok=True)
    idx = np.argwhere(col > 0)
    rows = ['%d,%d,%d,%d' % (x, y, z, col[x, y, z]) for x, y, z in idx]
    fn = os.path.join(out, 'hull_01.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as fo:
        fo.write('# 利劍號 船殼（draft_lines.py）x,y,z,color —— at 0,0,0\n')
        fo.write('\n'.join(rows) + '\n')
    R['lists'] = [{'file': 'masks/hull/hull_01.vox.txt', 'cells': len(rows), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()}]
    with open(os.path.join(HERE, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=1)
    sheet(L, PLAN, col, R, os.path.join(HERE, 'sheet01_lines_v1.png'))
    overlay_bodyplan(L, col, os.path.join(HERE, 'overlay_bodyplan_v1.png'))
    overlay_profile(L, col, ports, os.path.join(HERE, 'overlay_profile_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('station_half_breadths', 'ports')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
