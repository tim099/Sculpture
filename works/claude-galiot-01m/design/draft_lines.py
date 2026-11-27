# 蠍子號 新圖紙 01（TASK-0023 步驟 3）：線形 ⇒ 圖紙 sheet01_lines_v1.png、讀數 verify_lines.json、船殼清單 masks/hull/hull_01.vox.txt
#   用法：python -I -X utf8 draft_lines.py [--probe=half_beam=3]
#   出處：claude-felucca-01m/design/draft_lines.py（海鷗號）；它出自 kotoko-fusta-01m/design/draft_lines.py（越嶺號），越嶺號照皇家號 apex-one-reale-01m/design/draft_lines.py 改。
#   改的地方：範圍（X0、X1、ZMAX、MID）改讀 plan.json 的 space／lines；讀數的站位照船長取；史料對照改成讀 plan.json 的 checks
#            （每一點：史料寫的數值 → 作品量到的）；圖紙文字英文＋Pillow 內建字型（換一台機器也逐位元組相同）。
#   · 只讀 plan.json、不碰作品。船殼 ＝ 線形圍出來的實心，往裡留 wall 格；舷頂以上多算 EXTRA 層再量距離 ⇒ 舷頂不會變成一層蓋子。
#   · 艏柱、艉柱在舷頂以上那一段另外加（post_mould 格厚、龍骨寬）。
#   · --probe：反向對照用（拿某個線形參數加減幾格重算讀數，⛔ 不寫清單與圖）。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
EXTRA = 30
_PLAN = HL.load_plan(HERE)
X0 = 0
X1 = int(_PLAN['space']['hull'][0]) - 1
ZMAX = int(_PLAN['space']['hull'][2]) - 1
MID = int(_PLAN['space']['mid_x'])


def font(sz):
    return ImageFont.load_default()


def palette_rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def hull_cells(L, plan):
    """回傳 col：[x, y, z] 的色號陣列（0 ＝ 空），x 從 X0 起。"""
    hb = plan['hull_build']
    wall = V(hb['wall'])
    C = {k: V(v) for k, v in hb['colors'].items()}
    wl = plan['waterline']['z']
    S = L.solid(X0, X1, ZMAX, 0)
    Sx = np.pad(L.solid(X0, X1, ZMAX, EXTRA), 1)
    dist = ndimage.distance_transform_edt(Sx)[1:-1, 1:-1, 1:-1]
    shell = S & (dist <= wall)
    W = 2 * L.YC + 1
    post = np.zeros_like(S)
    m = int(V(hb['post_mould']))
    dyok = np.abs(np.arange(W) - L.YC) <= L.keel_hw
    for z in range(ZMAX + 1):
        zc = z + 0.5
        if zc <= L.z_st:
            xf = float(L.x_fwd(zc))
            for x in range(int(np.floor(xf - m + 0.5)), int(np.floor(xf)) + 1):
                if x + 0.5 <= xf and X0 <= x <= X1:
                    post[x - X0, dyok, z] = True
        if zc <= L.z_sh:
            xa = float(L.x_aft(zc))
            for x in range(int(np.ceil(xa - 0.5)), int(np.ceil(xa - 0.5)) + m):
                if x + 0.5 >= xa and X0 <= x <= X1:
                    post[x - X0, dyok, z] = True
    solid = shell | post
    # 顏色：外面那一層（距離 ≤ 1 或兩柱）照水線分水線下／上層；裡面的牆 inner；舷頂往下幾格的色帶（外面那層）
    outer = solid & ((dist <= 1.0) | post)
    col = np.zeros(S.shape, np.uint8)
    Z = np.arange(ZMAX + 1)[None, None, :]
    col[solid] = C['inner']
    col[outer & (Z <= wl)] = C['bottom']
    col[outer & (Z > wl)] = C['topside']
    xs = np.arange(X0, X1 + 1) + 0.5
    top = np.floor(L.sheer(xs)).astype(int)
    for i in range(len(xs)):
        for off, cname in V(hb['bands']):
            t = top[i] + off
            if t <= wl or t > ZMAX:
                continue
            band = (shell[i, :, t] & ~post[i, :, t]) if off == 0 else (outer[i, :, t] & ~post[i, :, t])
            col[i, band, t] = C[cname]
    return col


def stations(plan):
    """半寬表的站位：船殼兩柱之間每 20 格（量線形用）。"""
    a = int(np.ceil(V(plan['lines']['sternpost_head_x']) / 20.0) * 20)
    b = int(np.floor(V(plan['lines']['stem_head_x']) / 20.0) * 20)
    return list(range(a, b + 1, 20))


def readings(L, plan, col):
    wl = plan['waterline']['z']
    solid = col > 0
    xs_any = np.where(solid.any(axis=(1, 2)))[0] + X0
    keel_z0 = np.where(solid[:, L.YC, 0])[0] + X0
    zst = int(L.z_st) - 1
    zsh = int(L.z_sh) - 1
    xf = np.where(solid[:, L.YC, zst])[0] + X0
    xa = np.where(solid[:, L.YC, zsh])[0] + X0
    ys = np.where(solid.any(axis=(0, 2)))[0]
    beam = int(ys.max() - ys.min() + 1)
    Sol = L.solid(X0, X1, ZMAX, 0)
    below = Sol[:, :, :wl + 1]
    wl_x = np.where(Sol[:, :, wl].any(axis=1))[0] + X0
    wl_y = np.where(Sol[:, :, wl].any(axis=0))[0]
    disp = float(below.sum()) * 0.001 * 1.025
    sheer_mid = float(L.sheer(np.array([MID + 0.5]))[0])
    zs_tab = sorted(set([3, 6, wl, int(np.floor(sheer_mid))]))
    table = {}
    for x in stations(plan):
        row = {}
        for z in zs_tab:
            dys = np.where(solid[x - X0, :, z])[0]
            row[str(z)] = int(dys.max() - L.YC) if len(dys) else None
        table[str(x)] = row
    lbp = int(xf.max() - xa.min() + 1) if len(xf) and len(xa) else None
    lwl = int(wl_x.max() - wl_x.min() + 1)
    bwl = int(wl_y.max() - wl_y.min() + 1)
    T = (wl + 1) * 0.1
    return {
        'length_bp_cells': lbp, 'length_bp_m': round(lbp * 0.1, 2) if lbp else None,
        'stem_head_x_max': int(xf.max()) if len(xf) else None,
        'sternpost_head_x_min': int(xa.min()) if len(xa) else None,
        'keel_cells_z0': [int(keel_z0.min()), int(keel_z0.max())] if len(keel_z0) else None,
        'keel_length_m': round((keel_z0.max() - keel_z0.min() + 1) * 0.1, 2) if len(keel_z0) else None,
        'hull_x_range': [int(xs_any.min()), int(xs_any.max())],
        'beam_cells': beam, 'beam_m': round(beam * 0.1, 2),
        'waterline_z': wl, 'draught_m': round(T, 2),
        'waterline_length_m': round(lwl * 0.1, 2), 'waterline_beam_m': round(bwl * 0.1, 2),
        'displacement_t': round(disp, 1),
        'block_coefficient': round(float(below.sum()) / (lwl * bwl * (wl + 1)), 3),
        'sheer_mid_z': round(sheer_mid, 2), 'depth_keel_to_deck_edge_m': round((np.floor(sheer_mid) + 1) * 0.1, 2),
        'depth_keel_top_to_deck_edge_m': round((np.floor(sheer_mid) + 1 - L.z_keel_top) * 0.1, 2),
        'freeboard_mid_m': round((np.floor(sheer_mid) - wl) * 0.1, 2),
        'length_beam_ratio': round(lbp / beam, 2) if lbp else None,
        'cells': int(solid.sum()),
        'colors': {str(c): int((col == c).sum()) for c in np.unique(col[col > 0])},
        'half_breadth_table': table,
    }


def source_checks(L, plan, col, R):
    """plan.json 的 checks：每一點「史料寫的 → 作品量到的」。kind：
       rail_z@x（那一欄舷側最高格的頂）、stem_x@z（中線那一層最前一格的前緣）、reading（R 的某個讀數，比史料數值）、
       hb_ratio@x（那一欄舷頂下一層的外緣全寬 ÷ 船中同一層的全寬；比史料平面圖的站寬 ÷ 最大寬）。"""
    out = {}
    solid = col > 0
    YC = L.YC

    def width_below_rail(x):
        z = int(np.floor(L.sheer(np.array([x + 0.5]))[0])) - 1
        ys = np.where(solid[x - X0, :, z])[0]
        return (int(ys.max() - ys.min() + 1) if len(ys) else 0), z

    for c in plan.get('checks', []):
        k = c['kind']
        if k == 'hb_ratio@x':
            x = int(round(c['x']))
            w, z = width_below_rail(x)
            wm, _ = width_below_rail(MID)
            out[c['name']] = {'x': x, 'z': z, 'source_ratio': c['ratio'], 'work_ratio': round(w / float(wm), 3),
                              'work_width_m': round(w * 0.1, 2), 'mid_width_m': round(wm * 0.1, 2), 'src': c['src']}
            continue
        if k == 'rail_z@x':
            x = int(round(c['x']))
            zs = np.where(solid[x - X0, YC + int(L.keel_hw) + 1:, :].any(axis=0))[0]
            out[c['name']] = {'x': x, 'source_z': c['z'], 'work_z': int(zs.max()) + 1 if len(zs) else None, 'src': c['src']}
        elif k == 'stem_x@z':
            z = int(c['z'])
            xs = np.where(solid[:, YC, z])[0]
            out[c['name']] = {'z': z, 'source_x': c['x'], 'work_x': int(xs.max()) + X0 + 1 if len(xs) else None, 'src': c['src']}
        elif k == 'reading':
            out[c['name']] = {'source': c['value'], 'work': R.get(c['key']), 'unit': c.get('unit', ''), 'src': c['src']}
    return out


def sheet(L, plan, col, R, path):
    s = 3
    Wd = (X1 - X0 + 1) * s + 120
    H = 1100
    img = Image.new('RGB', (Wd, H), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = font(12)
    d.text((40, 16), '%s - new sheet 01: lines   0.1 m/cell   %s %s' % (plan['title_en'], plan['author'], plan['date']), fill=(20, 20, 40), font=f)
    wl = plan['waterline']['z']
    ox = 60

    def px(x):
        return ox + (x - X0) * s

    oy = 70 + 60 * s
    d.text((40, 40), '1. profile (starboard outside; bow to the right)', fill=(20, 20, 40), font=f)
    solid = col > 0
    for xi in range(col.shape[0]):
        for z in range(col.shape[2]):
            ys = np.where(solid[xi, :, z])[0]
            if len(ys):
                c = palette_rgb(int(col[xi, ys.max(), z]))
                d.rectangle([px(xi + X0), oy - (z + 1) * s, px(xi + X0) + s - 1, oy - z * s - 1], fill=c)
    d.line([px(X0), oy - (wl + 1) * s, px(X1), oy - (wl + 1) * s], fill=(40, 110, 200), width=1)
    d.text((px(X1) - 130, oy - (wl + 1) * s + 4), 'DWL z %d' % wl, fill=(40, 110, 200), font=f)
    for name, v in R.get('source_checks', {}).items():
        if 'source_z' in v:
            d.ellipse([px(v['x']) - 4, oy - v['source_z'] * s - 4, px(v['x']) + 4, oy - v['source_z'] * s + 4], outline=(200, 30, 30), width=2)
        elif 'source_x' in v:
            d.ellipse([px(v['source_x']) - 4, oy - (v['z'] + 1) * s - 4, px(v['source_x']) + 4, oy - (v['z'] + 1) * s + 4], outline=(200, 30, 30), width=2)
    for x in range(0, X1 + 1, 20):
        d.line([px(x), oy + 4, px(x), oy + 10], fill=(80, 80, 80))
        d.text((px(x) - 8, oy + 12), str(x), fill=(80, 80, 80), font=f)
    hb_max = int(V(plan['lines']['half_beam'])) + 4
    oy2 = oy + 60 + hb_max * s
    rail = int(np.floor(R['sheer_mid_z']))
    d.text((40, oy + 34), '2. half-breadths (plan view, centreline at bottom; rail z %d / DWL z %d / z 3)' % (rail, wl), fill=(20, 20, 40), font=f)
    d.line([px(X0), oy2, px(X1), oy2], fill=(120, 120, 120))
    for z, c in ((rail, (30, 30, 90)), (wl, (40, 110, 200)), (3, (150, 120, 60))):
        pts = []
        for xi in range(col.shape[0]):
            ys = np.where(solid[xi, :, z])[0]
            if len(ys):
                pts.append((px(xi + X0), oy2 - (ys.max() - L.YC + 1) * s))
        if len(pts) > 1:
            d.line(pts, fill=c, width=2)
    k = 8
    zsec = min(ZMAX + 1, rail + 12)
    oy3 = oy2 + 60 + zsec * k
    cx = 60 + (hb_max + 4) * k
    d.text((40, oy2 + 20), '3. sections x%d (left half: aft stations, right half: fwd stations; red = midship x %d)' % (k, MID), fill=(20, 20, 40), font=f)
    d.line([cx, oy3 - zsec * k, cx, oy3 + 10], fill=(120, 120, 120))
    d.line([cx - (hb_max + 2) * k, oy3 - (wl + 1) * k, cx + (hb_max + 2) * k, oy3 - (wl + 1) * k], fill=(40, 110, 200))
    for x in stations(plan) + [MID]:
        side = -1 if x < MID else 1
        pts = []
        for z in range(0, zsec):
            ys = np.where(solid[x - X0, :, z])[0]
            if len(ys):
                pts.append((cx + side * (ys.max() - L.YC + 1) * k, oy3 - (z + 1) * k))
        if len(pts) > 1:
            d.line(pts, fill=(30, 30, 90) if x != MID else (200, 40, 40), width=2 if x == MID else 1)
    tx, ty = cx + (hb_max + 10) * k, oy2 + 50
    d.text((tx, ty), '4. main dimensions (read from the cell list; right column = source or design decision)', fill=(20, 20, 40), font=f)
    rows = [(a, (b % R[key]) if key else b, c) for a, b, key, c in plan['sheet01_rows']]
    for i, (a, b, c) in enumerate(rows):
        y = ty + 24 + i * 20
        d.text((tx, y), a, fill=(30, 30, 30), font=f)
        d.text((tx + 230, y), b, fill=(160, 30, 30), font=f)
        d.text((tx + 330, y), c, fill=(90, 90, 90), font=f)
    sc = R.get('source_checks', {})
    if sc:
        y = ty + 24 + len(rows) * 20 + 20
        d.text((tx, y), '5. source checks (source -> work)', fill=(20, 20, 40), font=f)
        for i, (name, v) in enumerate(sc.items()):
            if 'source_ratio' in v:
                t = '%s: x %d  %.2f -> %.2f' % (name, v['x'], v['source_ratio'], v['work_ratio'])
            elif 'source_z' in v:
                t = '%s: x %d  z %s -> %s' % (name, v['x'], v['source_z'], v['work_z'])
            elif 'source_x' in v:
                t = '%s: z %d  x %s -> %s' % (name, v['z'], v['source_x'], v['work_x'])
            else:
                t = '%s: %s -> %s %s' % (name, v['source'], v['work'], v.get('unit', ''))
            d.text((tx, y + 20 + i * 18), t, fill=(30, 30, 30), font=f)
    d.text((40, H - 30), plan['sheet01_footer'], fill=(60, 60, 60), font=f)
    img.save(path)


def main():
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan(HERE)
    L = HL.Lines(plan, probe or None)
    col = hull_cells(L, plan)
    R = readings(L, plan, col)
    R['source_checks'] = source_checks(L, plan, col, R)
    if probe:
        print(json.dumps({'probe': probe, 'beam_m': R['beam_m'], 'length_bp_m': R['length_bp_m'], 'displacement_t': R['displacement_t'],
                          'half_breadth_table': R['half_breadth_table'], 'source_checks': R['source_checks']}, ensure_ascii=False))
        return
    out = os.path.join(HERE, 'masks', 'hull')
    os.makedirs(out, exist_ok=True)
    idx = np.argwhere(col > 0)
    rows = ['%d,%d,%d,%d' % (x + X0, y, z, col[x, y, z]) for x, y, z in idx]
    fn = os.path.join(out, 'hull_01.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蠍子號 船殼（draft_lines.py）x,y,z,color —— at 0,0,0\n')
        f.write('\n'.join(rows) + '\n')
    R['lists'] = [{'file': os.path.relpath(fn, HERE).replace('\\', '/'), 'cells': len(rows), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()}]
    with open(os.path.join(HERE, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(L, plan, col, R, os.path.join(HERE, 'sheet01_lines_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('half_breadth_table',)}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
