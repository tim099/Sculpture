# 收穫號 新圖紙 01（TASK-0590）：線形 ⇒ 圖紙 sheet01_lines_v1.png、讀數 verify_lines.json、船殼清單 masks/hull/hull_NN.vox.txt
#   用法：python -I -X utf8 draft_lines.py <design 資料夾> [--probe=half_beam=+3]
#   · 只讀 plan.json、不碰作品。船殼 ＝ 線形圍出來的實心，往裡留 wall 格（外板 1、肋骨、內板 1）；舷頂以上多算 EXTRA 層再切 ⇒ 舷頂不會變成一層蓋子。
#   · --probe：反向對照用（拿某個線形參數加減幾格重算讀數，⛔ 不寫清單與圖）。
#   · 結構照 gura-tridente-01m/design/draft_lines.py（同一套讀數與清單格式），圖紙與配色是本船的。
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def palette_rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


EXTRA = 60   # 舷頂以上多算的層數：要大於舷頂最大的落差（船樓 133 − 船腰 100 ＝ 33）⇒ 船樓前後緣不會長出一條橫跨船寬的「牆」


def hull_volume(L, plan):
    """回傳 (x0, ylo, S, dist)：S ＝ 外形實心（舷頂切齊）、dist ＝ 到船外的距離（EDT，1 ＝ 貼著外面那一層）。"""
    Z = plan['lines']
    zmax = int(math.ceil(L.top_max)) + 2          # 步驟 17：舷頂是曲線（lines.top_curve）⇒ 照 lines 算出來的最高處
    zs = np.arange(0, zmax + 1) + 0.5
    xa = float(np.min(L.x_aft(zs)))
    xs_ = float(np.max(L.x_stem(zs)))
    x0, x1 = int(math.floor(xa)) - 3, int(math.ceil(xs_)) + 3
    half = int(math.ceil(L.B2)) + 3
    ylo = L.YC - half
    Sx = L.solid(x0, x1, zmax + EXTRA, extra_top=EXTRA)[:, ylo:L.YC + half + 1, :]
    S = Sx[:, :, :zmax + 1].copy()
    top = L.top_z(np.arange(x0, x1 + 1) + 0.5)
    zz = np.arange(zmax + 1)[None, None, :] + 0.5
    S &= zz <= top[:, None, None] + 0.5
    dist = ndimage.distance_transform_edt(np.pad(Sx, 1))[1:-1, 1:-1, 1:-1][:, :, :zmax + 1].astype(np.float32)
    return x0, ylo, S, dist


def shell_colors(plan, S, dist):
    """牆：dist ≤ wall ⇒ 顏色照層（外板 1 層、肋骨、內板）；外板再照高度分水線下／上。"""
    W = plan['hull_build']
    T = float(W['wall'])
    wall = S & (dist <= T + 1e-6)
    col = np.zeros(S.shape, np.uint8)
    col[wall & (dist > 1.0)] = W['frame_color']
    col[wall & (dist > T - 1.0)] = W['inner_color']
    outer = wall & (dist <= 1.0)
    zz = np.broadcast_to(np.arange(S.shape[2])[None, None, :], S.shape)
    col[outer] = W['side_color']
    col[outer & (zz < W['bottom_top_z'])] = W['bottom_color']
    return wall, col


def readings(L, plan, S, wall, x0, ylo):
    m = plan['meters_per_cell']
    wl = float(plan['waterline']['z'])
    zl = float(plan['readings_at']['deck_z'])
    lgd = float(L.x_stem(zl) - L.x_aft(zl))
    keel = float(L.x_ff - L.x_post(0))
    beam_cells = int(S.any(axis=(0, 2)).sum())
    disp = float(S[:, :, :int(round(wl))].sum()) * m ** 3 * 1.025
    wl_beam = int(S[:, :, int(wl)].any(axis=0).sum())
    stations = []
    for x in range(int(math.ceil((x0 + 10) / 40.0)) * 40, x0 + S.shape[0] - 5, 40):
        row = {'x': x}
        for name, z in (('wl', wl), ('mb', L.z_mb), ('d1', plan['readings_at']['deck_z']), ('rail', plan['readings_at']['rail_z'])):
            col = S[x - x0, :, int(z)]
            ys = np.nonzero(col)[0]
            row[name] = int(np.max(np.abs(ys + ylo - L.YC))) if len(ys) else None
            row[name + '_design'] = round(float(L.hb(np.array([x + 0.5]), np.array([z + 0.5]))[0]), 2)
        stations.append(row)
    # Ordenanza 的三格對照（FG art.21、22）：mura、cuadra 的寬；hold beams 與 puente 那一層的半寬
    ra = plan['readings_at']
    codo = 5.7468
    xs_d, xp_d = float(L.x_stem(zl)), float(L.x_aft(zl))
    Lq = (xs_d - xp_d) / 4.0
    x_mura, x_cuadra = int(xs_d - Lq - codo), int(xp_d + Lq + 2 * codo)

    def full_beam(x, z):
        ys = np.nonzero(S[x - x0, :, int(z)])[0]
        return int(len(ys))
    xm = int((xs_d + xp_d) / 2)
    ord_check = {
        'x_mura': x_mura, 'beam_mura': full_beam(x_mura, L.z_mb), 'want_mura': round(beam_cells - codo, 1),
        'x_cuadra': x_cuadra, 'beam_cuadra': full_beam(x_cuadra, L.z_mb), 'want_cuadra': round(beam_cells - 2 * codo, 1),
        'x_mid': xm, 'beam_hold_beams': full_beam(xm, ra['hold_beams_z']), 'beam_puente': full_beam(xm, ra['puente_z']),
    }
    lab, ncomp = ndimage.label(wall)
    filled = ndimage.binary_fill_holes(wall)
    cav = int((filled & ~wall).sum())
    mir = wall[:, ::-1, :]
    sym = int((wall != mir).sum())
    xs = np.nonzero(S.any(axis=(1, 2)))[0]
    return {
        'length_deck_m': round(lgd * m, 3), 'length_deck_cells': round(lgd, 2), 'at_z': zl,
        'keel_length_m': round(keel * m, 3), 'extreme_beam_m': round(beam_cells * m, 3), 'extreme_beam_cells': beam_cells,
        'waterline_beam_m': round(wl_beam * m, 3),
        'length_beam_ratio': round(lgd / max(1, beam_cells), 3), 'keel_beam_ratio': round(keel / max(1, beam_cells), 3),
        'hull_top_max_z': int(math.ceil(L.top_max)), 'waterline_z': wl,
        'displacement_t_at_wl': round(disp, 1), 'solid_cells': int(S.sum()), 'wall_cells': int(wall.sum()),
        'components_6': int(ncomp), 'cavity_cells': cav, 'mirror_diff_cells': sym,
        'x_range': [int(x0 + xs[0]), int(x0 + xs[-1])],
        'ordenanza_check': ord_check,
        'stations': stations,
    }


def draw(plan, L, S, wall, col, x0, ylo, R, path):
    sc = 2.0
    nx, ny, nz = S.shape
    zmax = nz - 1
    padL, padT = 60, 90
    Wp = int(nx * sc) + padL * 2 + 140
    side_h = int(nz * sc)
    plan_h = int(ny * sc / 2) + 20
    body_h = int(nz * sc)
    Hp = padT + side_h + 60 + plan_h + 60 + body_h + 330
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    f12, f14, f20 = font(12), font(14), font(22)
    d.text((padL, 20), plan['title'] + '　v1', fill=(20, 20, 20), font=f20)
    d.text((padL, 52), '0.1 m／格　X 船長（船頭在右）　Z 高度（z 0 ＝ 龍骨底面）　中線 y %d' % L.YC, fill=(60, 60, 60), font=f14)
    # ① 側面：外板顏色的剪影（從 −y 看：每個 (x, z) 最外那一格的色）
    oy = padT
    for xi in range(nx):
        for z in np.nonzero(wall[xi].any(axis=0))[0]:
            ys = np.nonzero(wall[xi, :, z])[0]
            c = palette_rgb(int(col[xi, ys[0], z]))
            X0, Y0 = padL + xi * sc, oy + (zmax - z) * sc
            d.rectangle([X0, Y0, X0 + sc, Y0 + sc], fill=c)

    def hline(z, color, label):
        y = oy + (zmax - z) * sc
        d.line([padL, y, padL + nx * sc, y], fill=color)
        d.text((padL + nx * sc + 4, y - 8), label, fill=color, font=f12)
    hline(plan['waterline']['z'], (0, 90, 200), 'WL %g' % plan['waterline']['z'])
    for k, v in plan.get('decks_preview', {}).items():
        hline(v, (190, 0, 0), '%s %d' % (k, v))
    for x in range((x0 // 50 + 1) * 50, x0 + nx, 50):
        X = padL + (x - x0) * sc
        d.line([X, oy + side_h, X, oy + side_h + 6], fill=(0, 0, 0))
        d.text((X - 10, oy + side_h + 8), str(x), fill=(80, 80, 80), font=f12)
    d.text((padL, oy - 20), '① 側面（外板色；紅線 ＝ 甲板預覽、藍線 ＝ 設計水線）', fill=(0, 0, 0), font=f14)
    # ② 半寬圖
    oy2 = oy + side_h + 60
    d.text((padL, oy2 - 20), '② 半寬圖（右舷；每條線 ＝ 那個高度的外緣）', fill=(0, 0, 0), font=f14)
    cy = oy2 + plan_h - 10
    d.line([padL, cy, padL + nx * sc, cy], fill=(0, 0, 0))
    wlz = int(plan['waterline']['z'])
    levels = [(8, (130, 130, 130)), (25, (0, 130, 0)), (wlz, (0, 90, 200)), (int(L.z_mb), (0, 0, 0)),
              (int(plan['readings_at']['deck_z']) + 25, (190, 0, 0)), (int(plan['readings_at']['rail_z']), (140, 0, 140))]
    for j, (z, c) in enumerate(levels):
        pts = []
        for xi in range(nx):
            ys = np.nonzero(S[xi, :, min(z, nz - 1)])[0]
            if len(ys):
                pts.append((padL + xi * sc, cy - (ys[-1] + ylo - L.YC) * sc))
        if len(pts) > 1:
            d.line(pts, fill=c, width=1)
        d.text((padL + nx * sc + 4, cy - 14 * j - 80), 'z %d' % z, fill=c, font=f12)
    # ③ 橫剖面（body plan）
    oy3 = oy2 + plan_h + 60
    d.text((padL, oy3 - 20), '③ 橫剖面（左半 ＝ 船尾那一半的站、右半 ＝ 船頭那一半；外緣）', fill=(0, 0, 0), font=f14)
    cx = Wp // 2
    zmid = plan['readings_at']['deck_z']
    mid = (L.x_aft(zmid) + L.x_stem(zmid)) / 2.0
    st = plan.get('body_stations') or [s['x'] for s in R['stations']]
    pal = [(170, 0, 0), (200, 90, 0), (180, 140, 0), (0, 120, 0), (0, 120, 140), (0, 0, 0), (0, 0, 190), (90, 0, 190), (170, 0, 150), (120, 60, 0), (0, 90, 60)]
    for i, x in enumerate(st):
        xi = x - x0
        if xi < 0 or xi >= nx:
            continue
        sgn = -1 if x < mid else 1
        c = pal[i % len(pal)]
        pts = []
        for z in range(nz):
            ys = np.nonzero(S[xi, :, z])[0]
            if len(ys):
                pts.append((cx + sgn * (ys[-1] + ylo - L.YC) * sc * 1.6, oy3 + (zmax - z) * sc))
        if len(pts) > 1:
            d.line(pts, fill=c, width=2)
        d.text((cx + sgn * 300 - (60 if sgn < 0 else 0), oy3 + 16 * i), 'x %d' % x, fill=c, font=f12)
    d.line([cx, oy3, cx, oy3 + body_h], fill=(0, 0, 0))
    # ④ 主尺寸與讀數
    oy4 = oy3 + body_h + 20
    rows = [
        ('甲板長（z %g，艏柱到艉柱）' % R['at_z'], '%.2f m（%.1f 格）' % (R['length_deck_m'], R['length_deck_cells'])),
        ('龍骨長', '%.2f m' % R['keel_length_m']),
        ('最大寬（含外板）', '%.2f m（%d 格）；水線寬 %.2f m' % (R['extreme_beam_m'], R['extreme_beam_cells'], R['waterline_beam_m'])),
        ('比例', '甲板長 ÷ 寬 %.2f、龍骨 ÷ 寬 %.2f' % (R['length_beam_ratio'], R['keel_beam_ratio'])),
        ('設計水線', 'z %g（%.1f m）' % (R['waterline_z'], R['waterline_z'] * 0.1)),
        ('排水量（水線下實心 × 1.025）', '%.0f t' % R['displacement_t_at_wl']),
        ('船殼牆', '%s 格（外板＋肋骨＋內板，%g 格厚）' % (format(R['wall_cells'], ','), plan['hull_build']['wall'])),
        ('結構', '6 連通元件 %d、封閉空腔 %d、兩舷鏡像差 %d' % (R['components_6'], R['cavity_cells'], R['mirror_diff_cells'])),
    ]
    for i, (k, v) in enumerate(rows):
        d.text((padL, oy4 + i * 24), k, fill=(40, 40, 40), font=f14)
        d.text((padL + 320, oy4 + i * 24), v, fill=(0, 0, 0), font=f14)
    d.text((padL, oy4 + len(rows) * 24 + 10), '出處見 plan.json 的 src 欄（參考資料附出處／設計決定）。', fill=(90, 90, 90), font=f12)
    im.save(path, optimize=False)


def write_lists(out_dir, wall, col, x0, ylo, chunk=250000):
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith('.vox.txt'):
            os.remove(os.path.join(out_dir, f))
    idx = np.argwhere(wall)
    order = np.lexsort((idx[:, 2], idx[:, 1], idx[:, 0]))
    idx = idx[order]
    files = []
    for k in range(0, len(idx), chunk):
        part = idx[k:k + chunk]
        name = 'hull_%02d.vox.txt' % (k // chunk + 1)
        p = os.path.join(out_dir, name)
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 收穫號 船殼（draft_lines.py）—— x,y,z,color；at 0,0,0\n')
            for (xi, yi, z) in part:
                f.write('%d,%d,%d,%d\n' % (xi + x0, yi + ylo, z, col[xi, yi, z]))
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        files.append({'file': name, 'cells': int(len(part)), 'x_from': int(part[0][0] + x0), 'x_to': int(part[-1][0] + x0), 'sha256': h})
    return files


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    if probe:
        k, dv = probe[0].split('=')
        plan['lines'][k]['v'] = float(plan['lines'][k]['v']) + float(dv)
    L = HL.Lines(plan)
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist)
    R = readings(L, plan, S, wall, x0, ylo)
    R['colors'] = {int(c): int(n) for c, n in zip(*np.unique(col[wall], return_counts=True))}
    if probe:
        print(json.dumps({'probe': probe[0], 'extreme_beam_cells': R['extreme_beam_cells'], 'stations': R['stations']}, ensure_ascii=False))
        return
    if '--no-write' in sys.argv:
        print(json.dumps({k: v for k, v in R.items() if k != 'stations'}, ensure_ascii=False))
        draw(plan, L, S, wall, col, x0, ylo, R, os.path.join(design, 'sheet01_lines_v1.png'))
        return
    files = write_lists(os.path.join(design, 'masks', 'hull'), wall, col, x0, ylo)
    R['lists'] = files
    R['list_total'] = sum(f['cells'] for f in files)
    draw(plan, L, S, wall, col, x0, ylo, R, os.path.join(design, 'sheet01_lines_v1.png'))
    with open(os.path.join(design, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('stations', 'lists')}, ensure_ascii=False))
    print('lists', len(files), R['list_total'])


if __name__ == '__main__':
    main()
