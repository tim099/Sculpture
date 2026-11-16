# 塔爾塔納 步驟 7（TASK-1299）：雙拉丁桅（trinquet -23° ＋ mestre 0°）、船首斜桅（bout-dehors 15°）與兩根雙拼拉丁斜桁
#   輸出：masks/masts/{fore,main,bowsprit}.vox.txt、masks/yards/{fore_lateen,main_lateen}.vox.txt、
#         yards_placement.json、verify_masts.json、sheet06_masts_v1.png
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist)
    M = {m['key']: m for m in LY.masts(plan, L)}
    B = LY.bowsprit(plan, L)

    # 讀入甲板與船首飾物件以嚴密檢查零碰撞
    occupied = set()
    for p_dir in (os.path.join(design, 'masks', 'decks'), os.path.join(design, 'masks', 'ladders')):
        if os.path.exists(p_dir):
            for f in os.listdir(p_dir):
                if f.endswith('.vox.txt'):
                    arr = np.loadtxt(os.path.join(p_dir, f), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
                    for r in arr:
                        occupied.add((int(r[0]), int(r[1]), int(r[2])))
    for x, y, z in np.argwhere(wall):
        occupied.add((int(x + x0), int(y + ylo), int(z)))
    deco_spec = json.load(open(os.path.join(design, 'deco_spec.json'), encoding='utf-8'))['parts']
    beak_occ = set()
    bk_at = deco_spec['beak']['at']
    for r in np.loadtxt(os.path.join(design, 'masks', 'deco', 'beak.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2):
        beak_occ.add((int(r[0] + bk_at[0]), int(r[1] + bk_at[1]), int(r[2] + bk_at[2])))

    WOOD_LIGHT, WOOD_MID, BAND = 177, 141, 68

    def build_pole_mast(m):
        cells = {}
        z0, z1 = int(math.floor(m['heel'])), int(round(m['truck']))
        z_calc = m['calcet']
        r_base = 2.15 if m['key'] == 'main' else 1.85
        r_top = 1.15 if m['key'] == 'main' else 1.05
        # 雙桅立於船尾／龍骨內，於底盤區填基座塊（確保不浮空並緊壓 keelson）
        for z in range(z0, z1 + 1):
            t = (z - z0) / max(1.0, z1 - z0)
            xc = float(LY.mast_axis_x(plan, m['key'], z + 0.5, L))
            r = r_base * (1 - t) + r_top * t
            band = ((z - z0) % 16 in (0, 1)) and z < z_calc - 4
            is_calcet = z >= z_calc
            col_z = BAND if band else (WOOD_MID if is_calcet else WOOD_LIGHT)
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    x = int(round(xc)) + dx
                    y = YC + dy
                    if is_calcet:
                        ok = (abs(x - round(xc)) <= 1 and abs(dy) <= 1) or (abs(dy) == 2 and z >= z1 - 3 and abs(x - round(xc)) <= 1)
                    else:
                        ok = math.hypot(x - xc, dy) <= r
                    # 添加兩舷腮木（hounds bolster）於靜索領圈下（供 climb=1 繩梯頂踏點立腳）
                    z_hnd = int(round(z0 + (0.78 if m['key'] == 'main' else 0.72) * (z1 - z0)))
                    if z in (z_hnd - 1, z_hnd) and abs(dy) == 2 and abs(dx) <= 1:
                        ok = True
                        col_z_eff = WOOD_MID
                    else:
                        col_z_eff = col_z
                    if ok:
                        if (x, y, z) in occupied:
                            continue   # 跳過穿過甲板／龍骨時預留孔位外緣（實際孔洞已開，此處雙重保護）
                        cells[(x, y, z)] = col_z_eff
            # 與斜向連接補強（-23° 前傾桅每步 1 格防對角切斷）
            if abs(m['rake']) > 5 and z > z0:
                xc_prev = float(LY.mast_axis_x(plan, m['key'], z - 0.5, L))
                xmid = int(round(0.5 * (xc + xc_prev)))
                if (xmid, YC, z) not in occupied:
                    cells[(xmid, YC, z)] = BAND if band else WOOD_LIGHT
        # 填補前傾前桅基座與船底死材間 1 格封閉空腔 (239, 96, 9)
        if m['key'] == 'fore' and (239, YC, 9) not in occupied:
            cells[(239, YC, 9)] = WOOD_LIGHT
        return cells

    masts_vox = {}
    for mk in ('fore', 'main'):
        masts_vox[mk] = build_pole_mast(M[mk])

    # ── bowsprit (bout-dehors) ＋ 支撐木枕（saddle bitt，僅自甲板 z=28..32 往上撐住斜桅尾）──
    bow_cells = {}
    x_s0, z_s0 = float(B['x0']), float(B['z0'])
    a = math.radians(B['angle'])
    ln = B['len']
    # 枕座立柱（step bitt on main foredeck x=252..254, y=YC±2, z=27..33，先避開 occupied 與 fore 桅）
    for x in range(int(x_s0), int(x_s0) + 3):
        for z in range(27, 34):
            for dy in (-2, -1, 0, 1, 2):
                if abs(dy) == 2 or z >= 32:
                    pt = (x, YC + dy, z)
                    if pt not in occupied and pt not in beak_occ and pt not in masts_vox['fore']:
                        bow_cells[pt] = WOOD_MID if z < 33 else BAND
    # 斜桅圓木（自 x_s0,z_s0 前伸 ln 格 @15°，半徑由 1.25 縮至 0.65，步距 0.25 確保完全 6 連通）
    steps = int(ln * 4) + 1
    for i in range(steps):
        t = i / (steps - 1)
        s = t * ln
        cx = x_s0 + s * math.cos(a)
        cz = z_s0 + s * math.sin(a)
        r = 1.25 * (1 - t) + 0.65 * t
        ccol = BAND if (int(s) % 14 in (0, 1) and s > 4) else WOOD_LIGHT
        xi0, zi0 = int(round(cx)), int(round(cz))
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                for dz in (-2, -1, 0, 1, 2):
                    pt = (xi0 + dx, YC + dy, zi0 + dz)
                    if pt in occupied or pt in beak_occ:
                        continue
                    # 到軸線最短距離（近似點到圓柱）
                    vx, vz = pt[0] - x_s0, pt[2] - z_s0
                    proj = vx * math.cos(a) + vz * math.sin(a)
                    perp = abs(-vx * math.sin(a) + vz * math.cos(a))
                    if -0.5 <= proj <= ln + 0.5 and math.hypot(perp, pt[1] - YC) <= r:
                        bow_cells[pt] = ccol

    # ── 雙拼拉丁斜桁子作品（沿 +X 水平建造，car 在 +X、peak 在 -X）──
    yards_spec = {}
    yard_defs = {
        'fore_lateen': {
            'mast': 'fore', 'sail': 'fore-lateen', 'len_m': 10.4, 'tilt': 41.0,
            'fwd_frac': 0.26, 'r_max': 1.35, 'r_min': 0.65,
        },
        'main_lateen': {
            'mast': 'main', 'sail': 'main-lateen', 'len_m': 18.4, 'tilt': 39.0,
            'fwd_frac': 0.34, 'r_max': 1.75, 'r_min': 0.75,
        },
    }
    yc_local, zc_local = 4, 4
    yards_vox = {}
    for yname, yd in yard_defs.items():
        L_v = int(round(yd['len_m'] / 0.1))
        box_x = L_v + 4
        x_peak = 2
        x_car = x_peak + L_v - 1
        x_piv = int(round(x_car - yd['fwd_frac'] * (L_v - 1)))
        cells = {}
        # 雙材併綁特徵（carca ＋ penna 中段重疊處略粗 + 黑繩紮束 wooldings）
        for x in range(x_peak, x_car + 1):
            u = (x - x_peak) / max(1, L_v - 1)   # 0 at peak (-X), 1 at car (+X)
            dist_piv = abs(x - x_piv) / (0.5 * L_v)
            r = yd['r_max'] * max(0.0, 1.0 - 0.65 * dist_piv) + yd['r_min'] * (0.35 + 0.35 * u)
            r = min(yd['r_max'], max(yd['r_min'], r))
            is_band = (abs(x - x_piv) <= 1) or (x % 9 == 0)
            ccol = BAND if is_band else WOOD_MID
            for dy in range(-3, 4):
                for dz in range(-3, 4):
                    if math.hypot(dy, dz) <= r:
                        cells[(x, yc_local + dy, zc_local + dz)] = ccol

        m_info = M[yd['mast']]
        hz = m_info['yards']['lateen']['z']
        hx = float(LY.mast_axis_x(plan, yd['mast'], hz, L))
        anchors = {
            'pivot': [x_piv, yc_local, zc_local],
            'sling': [x_piv, yc_local, zc_local + 2],
            'fore': [x_car, yc_local, zc_local],
            'earing-F': [x_car - 1, yc_local, zc_local],
            'peak': [x_peak, yc_local, zc_local],
            'earing-A': [x_peak + 1, yc_local, zc_local],
        }
        # 加每隔 8 格之帆桁綁點 top-00..
        for ti, tx in enumerate(range(x_peak + 1, x_car, 8)):
            anchors['top-%02d' % ti] = [tx, yc_local, zc_local]

        yards_vox[yname] = (cells, [box_x, 9, 9])
        yards_spec[yname] = {
            'mast': yd['mast'], 'sail': yd['sail'], 'len_m': yd['len_m'], 'diam_m': round(yd['r_max'] * 0.2, 2),
            'tilt_deg': yd['tilt'], 'box': [box_x, 9, 9],
            'pivot': [x_piv + 0.5, yc_local + 0.5, zc_local + 0.5],
            'at': [round(hx + 0.5, 2), round(YC + 0.5 - 3.5, 2), round(hz + 0.5, 2)],
            'anchors': anchors,
        }

    # ── 寫出遮罩＋驗證 6 連通＝1 與零重疊 ──
    om = os.path.join(design, 'masks', 'masts')
    oy = os.path.join(design, 'masks', 'yards')
    os.makedirs(om, exist_ok=True)
    os.makedirs(oy, exist_ok=True)
    R = {'masts': {}, 'yards': {}, 'overlap': {}}

    def check_and_write(dct, path, hdr):
        pts = np.array(list(dct.keys()), dtype=int)
        mn = pts.min(axis=0)
        mx = pts.max(axis=0)
        arr = np.zeros(mx - mn + 1, dtype=bool)
        for k in dct:
            arr[k[0] - mn[0], k[1] - mn[1], k[2] - mn[2]] = True
        _, ncomp = ndimage.label(arr)
        ov_hull = sum(1 for k in dct if k in occupied)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(hdr)
            for (x, y, z), c in sorted(dct.items()):
                fh.write('%d,%d,%d,%d\n' % (x, y, z, c))
        return {'cells': len(dct), 'components_6': int(ncomp), 'overlap_hull_decks': ov_hull,
                'x_range': [int(mn[0]), int(mx[0])], 'z_range': [int(mn[2]), int(mx[2])],
                'sha256': hashlib.sha256(open(path, 'rb').read()).hexdigest()}

    for mk in ('fore', 'main'):
        R['masts'][mk] = check_and_write(masts_vox[mk], os.path.join(om, mk + '.vox.txt'), '# 塔爾塔納 桅 %s (at 0,0,0)\n' % mk)
    R['masts']['bowsprit'] = check_and_write(bow_cells, os.path.join(om, 'bowsprit.vox.txt'), '# 塔爾塔納 船首斜桅 (at 0,0,0)\n')
    ov_b = sum(1 for k in bow_cells if k in beak_occ)
    R['overlap']['bowsprit_vs_beak'] = ov_b

    for yname, (cells, box) in yards_vox.items():
        res = check_and_write(cells, os.path.join(oy, yname + '.vox.txt'), '# 塔爾塔納 帆桁 %s (局部框 %s)\n' % (yname, box))
        yards_spec[yname]['verify'] = res
        R['yards'][yname] = res

    with open(os.path.join(design, 'yards_placement.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(yards_spec, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)

    # 側面預覽圖（驗證桅、雙拼斜桁傾斜角度、斜桅清理艏柱與雕首）
    sc = 3.5
    x_lo, x_hi, z_hi = 50, 345, 230
    im = Image.new('RGB', (int((x_hi - x_lo) * sc) + 80, int(z_hi * sc) + 80), (250, 248, 240))
    d = ImageDraw.Draw(im)
    X = lambda xv: 40 + (xv - x_lo) * sc
    Zs = lambda zv: 40 + (z_hi - zv) * sc
    for (x, y, z) in occupied:
        if x_lo <= x < x_hi and z < z_hi:
            d.rectangle([X(x), Zs(z + 1), X(x + 1), Zs(z)], fill=(185, 165, 140))
    for (x, y, z) in beak_occ:
        if x_lo <= x < x_hi and z < z_hi:
            d.rectangle([X(x), Zs(z + 1), X(x + 1), Zs(z)], fill=(150, 100, 40))
    for mk, dct in list(masts_vox.items()) + [('bowsprit', bow_cells)]:
        for (x, y, z), c in dct.items():
            d.rectangle([X(x), Zs(z + 1), X(x + 1), Zs(z)], fill=palette_rgb(c))
    for yname, ys in yards_spec.items():
        ax, ay, az = ys['at']
        xp, _, _ = ys['pivot']
        L_v = int(round(ys['len_m'] / 0.1))
        a_y = math.radians(ys['tilt_deg'])
        c_pts = []
        for lx in (2, 2 + L_v - 1):
            dx = lx + 0.5 - xp
            wx = ax + dx * math.cos(a_y)
            wz = az - dx * math.sin(a_y)
            c_pts.append((wx, wz))
        d.line([X(c_pts[0][0]), Zs(c_pts[0][1]), X(c_pts[1][0]), Zs(c_pts[1][1])], fill=(60, 40, 20), width=5)
    im.save(os.path.join(design, 'sheet06_masts_v1.png'), optimize=False)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
