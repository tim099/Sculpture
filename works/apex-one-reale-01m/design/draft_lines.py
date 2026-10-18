# 皇家號 新圖紙 01（TASK-0695）：線形 ⇒ 圖紙 sheet01_lines_v1.png、讀數 verify_lines.json、船殼清單 masks/hull/hull_NN.vox.txt
#   用法：python -I -X utf8 draft_lines.py [--probe=half_beam=+3]
#   · 只讀 plan.json、不碰作品。船殼 ＝ 線形圍出來的實心，往裡留 wall 格；舷頂以上多算 EXTRA 層再量距離 ⇒ 舷頂不會變成一層蓋子。
#   · 艏柱、艉柱在舷頂以上那一段另外加（post_mould 格厚、龍骨寬）。
#   · --probe：反向對照用（拿某個線形參數加減幾格重算讀數，⛔ 不寫清單與圖）。
#   · 結構照收穫號的 draft_lines.py（同一套讀數與清單格式），圖紙與配色是本船的。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
EXTRA = 40
X0, X1, ZMAX = 40, 680, 70


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
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
    # 兩柱在舷頂以上那一段
    W = 2 * L.YC + 1
    post = np.zeros_like(S)
    m = int(V(hb['post_mould']))
    dyok = np.abs(np.arange(W) - L.YC) <= L.keel_hw
    for z in range(ZMAX + 1):
        zc = z + 0.5
        if zc <= min(L.z_st, V(hb.get('stem_post_top_z', L.z_st))):
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
    # 顏色：外面那一層（距離 ≤ 1 或兩柱）照水線分白／深藍；裡面的牆 141；舷頂最上一格金、舷頂下 4 格一條金線（外面那層）
    outer = solid & ((dist <= 1.0) | post)
    col = np.zeros(S.shape, np.uint8)
    Z = np.arange(ZMAX + 1)[None, None, :]
    col[solid] = C['inner']
    col[outer & (Z <= wl)] = C['bottom']
    col[outer & (Z > wl)] = C['topside']
    xs = np.arange(X0, X1 + 1) + 0.5
    top = np.floor(L.sheer(xs)).astype(int)
    for i in range(len(xs)):
        t = top[i]
        sl = shell[i, :, t]
        col[i, sl & ~post[i, :, t], t] = C['gold']
        g = t - 4
        if g > wl:
            o = outer[i, :, g] & ~post[i, :, g]
            col[i, o, g] = C['gold']
    return col


def readings(L, plan, col):
    wl = plan['waterline']['z']
    solid = col > 0
    xs_any = np.where(solid.any(axis=(1, 2)))[0] + X0
    keel_z0 = np.where(solid[:, L.YC, 0])[0] + X0
    # 兩柱頂：艏柱最高那一格的最前、艉柱最高那一格的最後
    zst = int(min(L.z_st, V(plan['hull_build'].get('stem_post_top_z', L.z_st)))) - 1
    zsh = int(L.z_sh) - 1
    xf = np.where(solid[:, L.YC, zst])[0] + X0
    xa = np.where(solid[:, L.YC, zsh])[0] + X0
    # 最寬（含外板）：每個 x 的 max |dy|
    ys = np.where(solid.any(axis=(0, 2)))[0]
    beam = int(ys.max() - ys.min() + 1)
    # 水線長、排水量（外形實心在水線下的格數 × 0.001 m³ × 1.025）
    Sol = L.solid(X0, X1, ZMAX, 0)
    below = Sol[:, :, :wl + 1]
    wl_x = np.where(Sol[:, :, wl].any(axis=1))[0] + X0
    disp = float(below.sum()) * 0.001 * 1.025
    # 船中（x 360）舷頂、艙深
    mid = 360
    xs = np.array([mid + 0.5])
    sheer_mid = float(L.sheer(xs)[0])
    # 半寬表：每 20 格一站，z 5、10、19（水線）、25（甲板邊）
    table = {}
    for x in range(100, 641, 20):
        row = {}
        for z in (5, 10, wl, 25):
            dys = np.where(solid[x - X0, :, z])[0]
            row[str(z)] = int(dys.max() - L.YC) if len(dys) else None
        table[str(x)] = row
    return {
        'length_bp_cells': int(xf.max() - xa.min() + 1) if len(xf) and len(xa) else None,
        'length_bp_m': round((int(xf.max() - xa.min() + 1)) * 0.1, 2) if len(xf) and len(xa) else None,
        'stem_head_x_max': int(xf.max()) if len(xf) else None,
        'sternpost_head_x_min': int(xa.min()) if len(xa) else None,
        'keel_cells_z0': [int(keel_z0.min()), int(keel_z0.max())] if len(keel_z0) else None,
        'keel_length_m': round((keel_z0.max() - keel_z0.min() + 1) * 0.1, 2) if len(keel_z0) else None,
        'hull_x_range': [int(xs_any.min()), int(xs_any.max())],
        'beam_cells': beam, 'beam_m': round(beam * 0.1, 2),
        'waterline_z': wl, 'waterline_length_m': round((wl_x.max() - wl_x.min() + 1) * 0.1, 2),
        'displacement_t': round(disp, 1),
        'sheer_mid_z': round(sheer_mid, 2), 'depth_keel_to_deck_edge_m': round((np.floor(sheer_mid) + 1) * 0.1, 2),
        'freeboard_mid_m': round((np.floor(sheer_mid) - wl) * 0.1, 2),
        'cells': int(solid.sum()),
        'colors': {str(c): int((col == c).sum()) for c in np.unique(col[col > 0])},
        'half_breadth_table': table,
    }


def sheet(L, plan, col, R, path):
    s = 2
    Wd = (X1 - X0 + 1) * s + 120
    H = 860
    img = Image.new('RGB', (Wd, H), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f1, f2, f3 = font(30), font(18), font(14)
    d.text((40, 16), '皇家號 La Réale（1694）新圖紙 01：線形　0.1 m／格　apex-one 2026-10-18', fill=(20, 20, 40), font=f1)
    wl = plan['waterline']['z']
    ox = 60

    def px(x):
        return ox + (x - X0) * s

    # ① 側面（從右舷看：每個 (x, z) 取 y 最大那一格的顏色）
    oy = 120 + ZMAX * s
    d.text((40, 70), '① 側面（右舷外觀；船頭朝右）', fill=(20, 20, 40), font=f2)
    solid = col > 0
    for xi in range(col.shape[0]):
        for z in range(col.shape[2]):
            ys = np.where(solid[xi, :, z])[0]
            if len(ys):
                c = palette_rgb(int(col[xi, ys.max(), z]))
                d.rectangle([px(xi + X0), oy - (z + 1) * s, px(xi + X0) + s - 1, oy - z * s - 1], fill=c)
    d.line([px(X0), oy - (wl + 1) * s, px(X1), oy - (wl + 1) * s], fill=(40, 110, 200), width=1)
    d.text((px(X1) - 120, oy - (wl + 1) * s - 18), '設計水線 z %d' % wl, fill=(40, 110, 200), font=f3)
    for x in range(100, 681, 50):
        d.line([px(x), oy + 4, px(x), oy + 10], fill=(80, 80, 80))
        d.text((px(x) - 10, oy + 12), str(x), fill=(80, 80, 80), font=f3)
    # ② 半寬（俯視：甲板邊、水線、z 8 三條半寬線）
    oy2 = oy + 80 + 45 * s
    d.text((40, oy + 40), '② 半寬（俯視，中線在下；甲板邊 z 25 ／ 水線 z %d ／ z 8）' % wl, fill=(20, 20, 40), font=f2)
    d.line([px(X0), oy2, px(X1), oy2], fill=(120, 120, 120))
    for z, c in ((25, (30, 30, 90)), (wl, (40, 110, 200)), (8, (150, 120, 60))):
        pts = []
        for xi in range(col.shape[0]):
            ys = np.where(solid[xi, :, z])[0]
            if len(ys):
                pts.append((px(xi + X0), oy2 - (ys.max() - L.YC + 1) * s))
        if len(pts) > 1:
            d.line(pts, fill=c, width=2)
    # ③ 橫剖面（每 40 格一站，左半船尾、右半船頭）
    oy3 = oy2 + 80 + 60 * 4
    cx = 60 + 70 * 4
    d.text((40, oy2 + 30), '③ 橫剖面（×4；左半 船尾那一半的站、右半 船頭那一半；外緣）', fill=(20, 20, 40), font=f2)
    k = 4
    d.line([cx, oy3 - 60 * k, cx, oy3 + 10], fill=(120, 120, 120))
    d.line([cx - 200, oy3 - (wl + 1) * k, cx + 200, oy3 - (wl + 1) * k], fill=(40, 110, 200))
    for x in range(120, 621, 40):
        side = -1 if x < 360 else 1
        pts = []
        for z in range(0, 40):
            ys = np.where(solid[x - X0, :, z])[0]
            if len(ys):
                pts.append((cx + side * (ys.max() - L.YC + 1) * k, oy3 - (z + 1) * k))
        if len(pts) > 1:
            d.line(pts, fill=(30, 30, 90) if x != 360 else (200, 40, 40), width=2 if x == 360 else 1)
    # ④ 主尺寸表
    tx, ty = cx + 300, oy2 + 40
    d.text((tx, ty), '④ 主尺寸（讀數：從清單的格子量）', fill=(20, 20, 40), font=f2)
    rows = [
        ('兩柱間（艏柱頂—艉柱頂）', '%.1f m' % R['length_bp_m'], "175'7\" ＝ 57.03 m（TD）"),
        ('龍骨（z 0 那一層）', '%.1f m' % R['keel_length_m'], "148' ＝ 48.07 m（TD）"),
        ('最寬（含外板）', '%.1f m' % R['beam_m'], "23'10\" ＝ 7.74 m（TD）"),
        ('龍骨底到甲板邊（船中）', '%.1f m' % R['depth_keel_to_deck_edge_m'], "艙深 7'2\" ＝ 2.33 m ＋ 龍骨（TD）"),
        ('設計水線／吃水', 'z %d ／ %.1f m' % (wl, (wl + 1) * 0.1), '普通船約 1.8 m（Briais）'),
        ('乾舷（船中甲板邊）', '%.1f m' % R['freeboard_mid_m'], '普通船約 0.7 m（Briais）'),
        ('水線長', '%.1f m' % R['waterline_length_m'], '—'),
        ('排水量（水線下實心）', '%.0f t' % R['displacement_t'], '沒找到'),
    ]
    for i, (a, b, c) in enumerate(rows):
        y = ty + 32 + i * 26
        d.text((tx, y), a, fill=(30, 30, 30), font=f3)
        d.text((tx + 230, y), b, fill=(160, 30, 30), font=f3)
        d.text((tx + 360, y), c, fill=(90, 90, 90), font=f3)
    d.text((40, H - 40), '色：水線下白 218 ／ 船殼深藍 37 ／ 金 244（舷頂與一條金線）／ 牆裡 141。出處見 plan.json 每個數字的 src；細部照普通槳帆船（1691 手冊）× 長 1.22、寬 1.32。',
           fill=(60, 60, 60), font=f3)
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
    if probe:
        print(json.dumps({'probe': probe, 'beam_m': R['beam_m'], 'half_breadth_table': R['half_breadth_table']}, ensure_ascii=False))
        return
    # 清單（at 0,0,0）
    out = os.path.join(HERE, 'masks', 'hull')
    os.makedirs(out, exist_ok=True)
    idx = np.argwhere(col > 0)
    lines = ['%d,%d,%d,%d' % (x + X0, y, z, col[x, y, z]) for x, y, z in idx]
    files = []
    for i in range(0, len(lines), 250000):
        fn = os.path.join(out, 'hull_%02d.vox.txt' % (i // 250000 + 1))
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 皇家號 船殼（draft_lines.py）x,y,z,color —— at 0,0,0\n')
            f.write('\n'.join(lines[i:i + 250000]) + '\n')
        files.append(fn)
    R['lists'] = [{'file': os.path.relpath(f, HERE).replace('\\', '/'), 'cells': min(250000, len(lines) - k * 250000),
                   'sha256': hashlib.sha256(open(f, 'rb').read()).hexdigest()} for k, f in enumerate(files)]
    with open(os.path.join(HERE, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(L, plan, col, R, os.path.join(HERE, 'sheet01_lines_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('half_breadth_table',)}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
