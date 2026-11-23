# 海鷗號 新圖紙 01（TASK-0024）：線形 ⇒ 圖紙 sheet01_lines_v1.png、讀數 verify_lines.json、船殼清單 masks/hull/hull_01.vox.txt
#   用法：python -I -X utf8 draft_lines.py [--probe=half_beam=3]
#   出處：kotoko-fusta-01m/design/draft_lines.py（越嶺號；它照皇家號 apex-one-reale-01m/design/draft_lines.py 改）。
#   改的地方：範圍、讀數的站位、色帶（舷頂綠＋白色護舷帶）、圖紙文字改英文＋Pillow 內建字型（換一台機器也逐位元組相同）、
#            多讀 Schellinks 1664 的比例對照（schellinks_check）。
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
X0, X1, ZMAX = 5, 160, 30
MID = 82


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
    # 顏色：外面那一層（距離 ≤ 1 或兩柱）照水線分瀝青黑／原木；裡面的牆 141；舷頂往下幾格的紅綠帶（外面那層）
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
            if t <= wl:
                continue
            band = (shell[i, :, t] & ~post[i, :, t]) if off == 0 else (outer[i, :, t] & ~post[i, :, t])
            col[i, band, t] = C[cname]
    return col


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
    disp = float(below.sum()) * 0.001 * 1.025
    sheer_mid = float(L.sheer(np.array([MID + 0.5]))[0])
    table = {}
    for x in range(20, 151, 10):
        row = {}
        for z in (2, 4, wl, 10, 13):
            dys = np.where(solid[x - X0, :, z])[0]
            row[str(z)] = int(dys.max() - L.YC) if len(dys) else None
        table[str(x)] = row
    lbp = int(xf.max() - xa.min() + 1) if len(xf) and len(xa) else None
    return {
        'length_bp_cells': lbp, 'length_bp_m': round(lbp * 0.1, 2) if lbp else None,
        'stem_head_x_max': int(xf.max()) if len(xf) else None,
        'sternpost_head_x_min': int(xa.min()) if len(xa) else None,
        'keel_cells_z0': [int(keel_z0.min()), int(keel_z0.max())] if len(keel_z0) else None,
        'keel_length_m': round((keel_z0.max() - keel_z0.min() + 1) * 0.1, 2) if len(keel_z0) else None,
        'hull_x_range': [int(xs_any.min()), int(xs_any.max())],
        'beam_cells': beam, 'beam_m': round(beam * 0.1, 2),
        'waterline_z': wl, 'waterline_length_m': round((wl_x.max() - wl_x.min() + 1) * 0.1, 2),
        'displacement_t': round(disp, 1),
        'sheer_mid_z': round(sheer_mid, 2), 'depth_keel_to_deck_edge_m': round((np.floor(sheer_mid) + 1) * 0.1, 2),
        'depth_keel_top_to_deck_edge_m': round((np.floor(sheer_mid) + 1 - L.z_keel_top) * 0.1, 2),
        'freeboard_mid_m': round((np.floor(sheer_mid) - wl) * 0.1, 2),
        'cells': int(solid.sum()),
        'colors': {str(c): int((col == c).sum()) for c in np.unique(col[col > 0])},
        'half_breadth_table': table,
    }


def schellinks_check(L, plan, col):
    """SCH 讀數（references/sch_readings.json，以全長為 1 的比例）換成格，對照清單的格子：每一項報「圖紙 → 作品」。"""
    with open(os.path.join(os.path.dirname(HERE), 'references', 'sch_readings.json'), encoding='utf-8') as f:
        S = json.load(f)
    p = S['points_px']
    wl = plan['waterline']['z']
    wy = p['waterline_y']
    x_bow_px, x_stern_px = p['stem_head_scroll_top'][0], p['stern_top'][0]
    k = (L.x_st - L.x_sh) / float(x_stern_px - x_bow_px)        # 格／px（全長對全長）

    def gx(px):
        return L.x_st - (px - x_bow_px) * k                       # 圖是船頭朝左 ⇒ 反向

    def gz(py):
        return wl + 1 + (wy - py) * k                             # 水線那一格的頂 ＝ 圖上的水線

    solid = col > 0
    YC = L.YC

    def top_at(x):
        zs = np.where(solid[int(round(x)) - X0, YC + int(L.keel_hw) + 1:, :].any(axis=0))[0]   # 舷側（中線外）最高的格
        return int(zs.max()) + 1 if len(zs) else None              # 格頂

    def stem_x_at(z):
        xs = np.where(solid[:, YC, int(z)])[0]
        return int(xs.max()) + X0 + 1 if len(xs) else None         # 最前一格的前緣

    out = {}
    for name, (px, py) in (('waist_gunwale@mainmast', (p['mainmast_x'], p['waist_gunwale_y_at_mainmast'])),
                           ('bow_bulwark_top_fwd', tuple(p['bow_panelled_bulwark_top_fwd'])),
                           ('bow_bulwark_aft_end', tuple(p['bow_panelled_bulwark_aft_end'])),
                           ('stern_top', tuple(p['stern_top']))):
        x = gx(px)
        out[name] = {'x': round(x, 1), 'drawing_top_z': round(gz(py), 1), 'work_top_z': top_at(x)}
    for i, (px, py) in enumerate(p['stern_rail_profile']):
        x = gx(px)
        out['stern_rail_%d' % i] = {'x': round(x, 1), 'drawing_top_z': round(gz(py), 1), 'work_top_z': top_at(x)}
    zst = gz(p['stem_at_waterline'][1])
    out['stem_at_waterline'] = {'z': wl, 'drawing_x': round(gx(p['stem_at_waterline'][0]), 1), 'work_x': stem_x_at(wl)}
    out['stem_head'] = {'drawing_z': round(gz(p['stem_head_scroll_top'][1]), 1), 'post_top_z': int(np.where(solid[:, YC, :].any(axis=0))[0].max()) + 1,
                        'note': '圖上的柱頭含渦卷裝飾（步驟 6）；船殼只到柱頂'}
    out['cells_per_px'] = round(k, 5)
    return out


def sheet(L, plan, col, R, path):
    s = 6
    Wd = (X1 - X0 + 1) * s + 120
    H = 1100
    img = Image.new('RGB', (Wd, H), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = font(12)
    d.text((40, 16), 'al-Nawras (Sale felucca, 1666) - new sheet 01: lines   0.1 m/cell   Claude-Ojousama 2026-11-21', fill=(20, 20, 40), font=f)
    wl = plan['waterline']['z']
    ox = 60

    def px(x):
        return ox + (x - X0) * s

    oy = 60 + ZMAX * s
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
    sc = R['schellinks_check']
    for name, v in sc.items():
        if isinstance(v, dict) and 'drawing_top_z' in v:
            x, z = v['x'], v['drawing_top_z']
            d.ellipse([px(x) - 4, oy - z * s - 4, px(x) + 4, oy - z * s + 4], outline=(200, 30, 30), width=2)
    v = sc['stem_at_waterline']
    d.ellipse([px(v['drawing_x']) - 4, oy - (wl + 1) * s - 4, px(v['drawing_x']) + 4, oy - (wl + 1) * s + 4], outline=(200, 30, 30), width=2)
    d.text((40, oy + 26), 'red circles = Schellinks 1664 readings scaled to LOA 14.0 m', fill=(200, 30, 30), font=f)
    for x in range(10, 161, 10):
        d.line([px(x), oy + 4, px(x), oy + 10], fill=(80, 80, 80))
        d.text((px(x) - 8, oy + 12), str(x), fill=(80, 80, 80), font=f)
    oy2 = oy + 90 + 18 * s
    d.text((40, oy + 50), '2. half-breadths (plan view, centreline at bottom; rail z 13 / DWL z %d / z 3)' % wl, fill=(20, 20, 40), font=f)
    d.line([px(X0), oy2, px(X1), oy2], fill=(120, 120, 120))
    for z, c in ((13, (30, 30, 90)), (wl, (40, 110, 200)), (3, (150, 120, 60))):
        pts = []
        for xi in range(col.shape[0]):
            ys = np.where(solid[xi, :, z])[0]
            if len(ys):
                pts.append((px(xi + X0), oy2 - (ys.max() - L.YC + 1) * s))
        if len(pts) > 1:
            d.line(pts, fill=c, width=2)
    k = 10
    oy3 = oy2 + 60 + 26 * k
    cx = 60 + 22 * k
    d.text((40, oy2 + 20), '3. sections x10 (left half: aft stations, right half: fwd stations; red = midship x %d)' % MID, fill=(20, 20, 40), font=f)
    d.line([cx, oy3 - 26 * k, cx, oy3 + 10], fill=(120, 120, 120))
    d.line([cx - 200, oy3 - (wl + 1) * k, cx + 200, oy3 - (wl + 1) * k], fill=(40, 110, 200))
    for x in range(20, 151, 10):
        side = -1 if x < MID else 1
        pts = []
        for z in range(0, 26):
            ys = np.where(solid[x - X0, :, z])[0]
            if len(ys):
                pts.append((cx + side * (ys.max() - L.YC + 1) * k, oy3 - (z + 1) * k))
        if len(pts) > 1:
            d.line(pts, fill=(30, 30, 90) if x != MID else (200, 40, 40), width=2 if x == MID else 1)
    tx, ty = cx + 280, oy2 + 50
    d.text((tx, ty), '4. main dimensions (read from the cell list)', fill=(20, 20, 40), font=f)
    rows = [
        ('stem head - sternpost head', '%.1f m' % R['length_bp_m'], 'design: 14 m (FAR-87 plan)'),
        ('keel (z 0 layer)', '%.1f m' % R['keel_length_m'], 'stem 29 deg / sternpost 17 deg from Schellinks'),
        ('beam (outside)', '%.1f m' % R['beam_m'], 'design: about 3.2 m'),
        ('keel bottom - rail (midship)', '%.1f m' % R['depth_keel_to_deck_edge_m'], 'freeboard 0.7 m from Schellinks + draught'),
        ('DWL / draught', 'z %d / %.1f m' % (wl, (wl + 1) * 0.1), 'design (shallow bar at Sale)'),
        ('freeboard (midship rail)', '%.1f m' % R['freeboard_mid_m'], 'Schellinks 7.1 cells'),
        ('waterline length', '%.1f m' % R['waterline_length_m'], 'Schellinks LWL/LOA 0.89'),
        ('displacement (solid below DWL)', '%.1f t' % R['displacement_t'], 'design target about 15 t'),
    ]
    for i, (a, b, c) in enumerate(rows):
        y = ty + 24 + i * 20
        d.text((tx, y), a, fill=(30, 30, 30), font=f)
        d.text((tx + 200, y), b, fill=(160, 30, 30), font=f)
        d.text((tx + 290, y), c, fill=(90, 90, 90), font=f)
    d.text((40, H - 30), 'colours: below DWL tallow 218 / topside 173 / rail green 16 / wale white 255 / inside 141. sources: plan.json src of every number; references/sch_readings.json',
           fill=(60, 60, 60), font=f)
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
    R['schellinks_check'] = schellinks_check(L, plan, col)
    if probe:
        print(json.dumps({'probe': probe, 'beam_m': R['beam_m'], 'length_bp_m': R['length_bp_m'], 'half_breadth_table': R['half_breadth_table'], 'schellinks_check': R['schellinks_check']}, ensure_ascii=False))
        return
    out = os.path.join(HERE, 'masks', 'hull')
    os.makedirs(out, exist_ok=True)
    idx = np.argwhere(col > 0)
    rows = ['%d,%d,%d,%d' % (x + X0, y, z, col[x, y, z]) for x, y, z in idx]
    fn = os.path.join(out, 'hull_01.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 海鷗號 船殼（draft_lines.py）x,y,z,color —— at 0,0,0\n')
        f.write('\n'.join(rows) + '\n')
    R['lists'] = [{'file': os.path.relpath(fn, HERE).replace('\\', '/'), 'cells': len(rows), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()}]
    with open(os.path.join(HERE, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(L, plan, col, R, os.path.join(HERE, 'sheet01_lines_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('half_breadth_table',)}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
