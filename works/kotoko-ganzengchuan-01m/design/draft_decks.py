# 福建趕繒船 步驟 5（TASK-1314）：4 層甲板（底艙／主甲板／艏平台／尾樓）、水密隔艙、3 座梯子與空艙房
#   出處：kaguya-shachuan-01m/design/draft_decks.py（改寫為尖底福船四層甲板、底艙壓艙防空腔、三梯與兩處空艙房）
#   用法：python -I -X utf8 draft_decks.py <design 資料夾> [--probe=drop_ladder=hold]
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import build as hull_build, font, rgb as palette_rgb

sys.stdout.reconfigure(encoding='utf-8')


def load_carved_hull(design, x0, ylo, shape):
    """從步驟 4 完稿（hull_01 - carve + paint）建立實際船殼陣列。"""
    H = np.zeros(shape, np.uint8)
    hull_pts = np.loadtxt(os.path.join(design, 'masks', 'hull', 'hull_01.vox.txt'), delimiter=',', comments='#', dtype=int)
    for x, y, z, c in hull_pts:
        H[x - x0, y - ylo, z] = c
    c_path = os.path.join(design, 'masks', 'ports', 'carve.vox.txt')
    if os.path.exists(c_path):
        for x, y, z, _ in np.loadtxt(c_path, delimiter=',', comments='#', dtype=int, ndmin=2):
            H[x - x0, y - ylo, z] = 0
    p_path = os.path.join(design, 'masks', 'ports', 'paint.vox.txt')
    if os.path.exists(p_path):
        for x, y, z, c in np.loadtxt(p_path, delimiter=',', comments='#', dtype=int, ndmin=2):
            H[x - x0, y - ylo, z] = c
    return H


def mast_x_at(m, z):
    ang = math.radians(m['rake_deg'])
    return m['x'] + (np.asarray(z, float) - m['heel_z']) * math.tan(ang)


def main():
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = a

    plan = HL.load_plan(design)
    L, _, S, x0, ylo = hull_build(plan, None)
    YC = L.YC
    H_col = load_carved_hull(design, x0, ylo, S.shape)
    wall = H_col > 0
    inside = S & ~wall

    nx, ny, nz = S.shape
    X = np.arange(nx) + x0
    Yy = np.arange(ny) + ylo
    DY = Yy - YC
    B = plan['decks_build']
    keys = list(B['spans'])
    span = {k: B['spans'][k] for k in keys}
    # floor 是甲板上第一層空氣，因此地板頂格 = floor - 1
    zplank = {k: int(plan['decks'][k]['floor']) - 1 for k in keys}

    LD = B['ladders']
    ladders = [dict(l) for l in LD['list']]
    if probe and probe.startswith('drop_ladder='):
        drop = probe.split('=', 1)[1]
        ladders = [l for l in ladders if l['name'] != drop]
    th = int(LD['tread_half'])

    # ── 1. 甲板開口（主艙口、梯井、桅孔）──
    hole = {k: np.zeros((nx, ny), bool) for k in keys}
    coam = {k: np.zeros((nx, ny), bool) for k in keys}
    for h in B['hatches']:
        m = (X[:, None] >= h['x0']) & (X[:, None] <= h['x1']) & (np.abs(DY)[None, :] <= h['half'])
        ring = (X[:, None] >= h['x0'] - 1) & (X[:, None] <= h['x1'] + 1) & (np.abs(DY)[None, :] <= h['half'] + 1) & ~m
        for k in h['decks']:
            hole[k] |= m
            coam[k] |= ring
    for ld in ladders:
        if not ld.get('well'):
            continue
        s, xs, yc = ld['dir'], ld['xs'], YC + ld['dy']
        xa, xb = sorted((xs + s * ld['well_a'], xs + s * ld['well_b']))
        m = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Yy - yc)[None, :] <= th + 1)
        hole[ld['up']] |= m
        side = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Yy - yc)[None, :] == th + 2)
        low_end = (X[:, None] == xs + s * (ld['well_a'] - 1)) & (np.abs(Yy - yc)[None, :] <= th + 2)
        coam[ld['up']] |= side | low_end
    for k in keys:
        for mk, r in B['mast_r'].items():
            m = plan['masts'][mk]
            if not (span[k][0] <= m['x'] <= span[k][1]):
                continue
            if zplank[k] <= m['heel_z']:
                continue
            xa = float(mast_x_at(m, zplank[k] + 0.5))
            hit = (X[:, None] + 0.5 - (xa + 0.5)) ** 2 + (Yy[None, :] - YC) ** 2 <= r * r
            hole[k] |= hit
    for k in keys:
        coam[k] &= ~hole[k]

    # ── 2. 甲板鋪板＋橫樑＋圍欄 ──
    decks = {}
    BM = B['beam']
    for k in keys:
        cell = np.zeros(S.shape, np.uint8)
        plank = B['plank']['weather'] if k in B['plank']['weather_decks'] else B['plank']['interior']
        bd = int(BM['depth'][k])
        a, b = span[k]
        z = zplank[k]
        for xi in range(nx):
            if not (a <= X[xi] <= b):
                continue
            row = inside[xi, :, z] & ~hole[k][xi]
            cell[xi, row, z] = plank
            if ((X[xi] - BM['phase']) % BM['every']) < BM['w']:
                for dz in range(1, bd + 1):
                    rb = inside[xi, :, z - dz] & ~hole[k][xi]
                    cell[xi, rb & (cell[xi, :, z - dz] == 0), z - dz] = BM['color']
            for dz in range(1, B['coaming_h'] + 1):
                rc = inside[xi, :, z + dz] & coam[k][xi]
                cell[xi, rc, z + dz] = B['trim']
        decks[k] = cell

    # ── 3. 水密橫隔艙壁（put in deck-hold, x=112..282, 留中央 5 格通行門）──
    BH = B['bulkhead']
    zh_air = int(plan['decks']['hold']['floor'])
    zm_beam = zplank['main'] - int(BM['depth']['main'])
    for bx in BH['x']:
        xi = bx - x0
        for z in range(zh_air, zm_beam):
            for yi in range(ny):
                if not inside[xi, yi, z]:
                    continue
                if abs(DY[yi]) <= BH['door_half'] and z <= zh_air + BH['door_h'] - 1:
                    continue
                if decks['hold'][xi, yi, z] == 0:
                    decks['hold'][xi, yi, z] = BH['color']

    # ── 4. 尾樓／艏平台 break（隔牆＋門＋梯口胸牆）──
    gaps = {}
    for ld in ladders:
        if not ld.get('well'):
            gaps.setdefault(ld['up'], []).append(YC + ld['dy'])
    for br in B['breaks']:
        xi = br['x'] - x0
        zl_air = int(plan['decks'][br['lo']]['floor'])
        zu_top = zplank[br['up']]
        door = np.zeros(ny, bool)
        for d_dy in br['doors_dy']:
            door |= np.abs(np.abs(DY) - d_dy) <= br['door_half']
        for z in range(zl_air, zu_top):
            rowm = inside[xi, :, z] & ~(door & (z < zl_air + br['door_h']))
            decks[br['up']][xi, rowm & (decks[br['up']][xi, :, z] == 0), z] = br['color']
        gap = np.zeros(ny, bool)
        for yc_g in gaps.get(br['up'], []):
            gap |= np.abs(Yy - yc_g) <= th + 1
        for z in range(zu_top + 1, zu_top + 1 + br['rail_h']):
            rowm = inside[xi, :, z] & ~gap
            decks[br['up']][xi, rowm & (decks[br['up']][xi, :, z] == 0), z] = br['rail_color']

    # ── 5. 梯子 ──
    LC = int(LD['color'])
    lad, pts = {}, {}
    for ld in ladders:
        up, lo = ld['up'], ld['lo']
        cell = lad.setdefault(up, np.zeros(S.shape, np.uint8))
        s, xs = int(ld['dir']), int(ld['xs'])
        yc = YC + int(ld['dy'])
        zl_air = int(plan['decks'][lo]['floor'])
        zl_top = zl_air - 1
        zu_air = int(plan['decks'][up]['floor'])
        zu_top = zu_air - 1
        hx = int(ld['head_x'])
        n = (zu_air - zl_air) // int(LD['rise'])
        yc_i = yc - ylo
        for kk in range(0, n + 2):
            xa = xs + s * int(LD['run']) * kk
            xr = sorted((xa, xa + s * (int(LD['run']) - 1)))
            zt = min(zu_top, zl_top + int(LD['rise']) * kk)
            if kk == n + 1:
                zt = zu_top
            for xx in range(xr[0], xr[1] + 1):
                if 1 <= kk <= n:
                    cell[xx - x0, yc_i - th:yc_i + th + 1, zt] = LC
                if kk == 0:
                    zlo, zhi = zl_top + 1, zl_top + 3
                elif kk <= n:
                    zlo, zhi = zt - 3, zt
                else:
                    zlo, zhi = min(zu_top, zl_top + int(LD['rise']) * n) - 3, zu_top
                for z in range(zlo, zhi + 1):
                    for yy in (yc_i - th - 1, yc_i + th + 1):
                        cell[xx - x0, yy, z] = LC
        lo_z = min(zu_air, zl_air + int(LD['rise']))
        hi_z = min(zu_air, zl_air + int(LD['rise']) * n)
        P = {
            'foot': [xs - s, yc, zl_air],
            'lo': [xs + s * int(LD['run']), yc, lo_z],
            'hi': [xs + s * int(LD['run']) * n, yc, hi_z],
            'head': [hx, yc, zu_air],
        }
        pts[ld['name']] = {'up': up, 'lo': lo, 'points': P, 'steps': n}

    anyd = np.zeros(S.shape, bool)
    for c in decks.values():
        anyd |= c > 0
    for k in lad:
        lad[k][anyd | wall] = 0

    # ── 6. 封閉空腔檢查與底艙壓艙底肋填實 ──
    uni = wall.copy()
    for c in list(decks.values()) + list(lad.values()):
        uni |= c > 0
    cav = ndimage.binary_fill_holes(uni) & ~uni
    labc, ncav = ndimage.label(cav)
    filled = []
    for i in range(1, ncav + 1):
        idx = np.argwhere(labc == i)
        xm, zm = int(np.median(idx[:, 0])), float(np.median(idx[:, 2]))
        k = min(keys, key=lambda kk: abs(zplank[kk] - zm) + (0 if span[kk][0] <= xm + x0 <= span[kk][1] else 1000))
        decks[k][labc == i] = BM['color']
        filled.append({'deck': k, 'cells': int(len(idx)), 'x': [int(idx[:, 0].min() + x0), int(idx[:, 0].max() + x0)], 'z': [int(idx[:, 2].min()), int(idx[:, 2].max())]})

    # ── 7. 讀數與驗收檢查 ──
    R = {'decks': {}, 'ladders': {}}
    allc = np.zeros(S.shape, np.int16)
    for k, c in decks.items():
        m = c > 0
        R['decks'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & wall).sum()), 'outside_hull': int((m & ~S).sum()), 'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    for k, c in lad.items():
        m = c > 0
        R['ladders'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & wall).sum()), 'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    R['overlap_between_parts'] = int((allc > 1).sum())

    every = wall.copy()
    for c in list(decks.values()) + list(lad.values()):
        every |= c > 0
    bad = []
    for nm, v in pts.items():
        for pk, (px, py, pz) in v['points'].items():
            xi_, yi_ = px - x0, py - ylo
            ok_air = not every[xi_, yi_, pz]
            ok_floor = bool(every[xi_, yi_, pz - 1])
            head = int(every[xi_, yi_, pz:pz + 14].sum())
            if not (ok_air and ok_floor) or head:
                bad.append((nm, pk, [px, py, pz], ok_air, ok_floor, head))
    R['ladder_point_problems'] = bad
    R['ladder_count'] = len(pts)

    rooms_check = {}
    for rk, rv in B['rooms'].items():
        rx0, rx1 = rv['x0'] - x0, rv['x1'] - x0
        ry0, ry1 = rv['y0'] - ylo, rv['y1'] - ylo
        rz0, rz1 = rv['z0'], rv['z1']
        box_solid = int(every[rx0:rx1 + 1, ry0:ry1 + 1, rz0:rz1 + 1].sum())
        floor_solid = bool(every[rx0:rx1 + 1, ry0:ry1 + 1, rz0 - 1].all())
        rooms_check[rk] = {'solid_inside': box_solid, 'floor_all_solid': floor_solid, 'headroom': rz1 - rz0 + 1}
    R['rooms_check'] = rooms_check
    R['cavities_filled'] = filled

    # 最終合併後的 6 連通元件與封閉空腔再檢
    uni_final = wall.copy()
    for c in list(decks.values()) + list(lad.values()):
        uni_final |= c > 0
    _, comp_final = ndimage.label(uni_final)
    cav_final = int((ndimage.binary_fill_holes(uni_final) & ~uni_final).sum())
    R['combined_components'] = int(comp_final)
    R['combined_cavities'] = cav_final

    decks_meta = {}
    for k in keys:
        a, b = span[k]
        fl_z = int(plan['decks'][k]['floor'])
        decks_meta[k] = {
            'kind': 'deck',
            'deck': k,
            'level': B['levels'][k],
            'name': B['names'][k],
            'floor': f'{a}:{fl_z},{b}:{fl_z}',
            'thick': B['thick'][k],
        }
    R['decks_meta'] = decks_meta

    if probe:
        print(json.dumps({'probe': probe, 'ladder_count': len(pts), 'reach': {k: sorted(nm for nm, v in pts.items() if k in (v['up'], v['lo'])) for k in keys}}, ensure_ascii=False))
        return

    def dump(path, c, head):
        idx = np.argwhere(c > 0)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for xi_, yi_, z in idx:
                f.write(f'{xi_ + x0},{yi_ + ylo},{z},{c[xi_, yi_, z]}\n')
        return [int(len(idx)), hashlib.sha256(open(path, 'rb').read()).hexdigest()]

    od, ol = os.path.join(design, 'masks', 'decks'), os.path.join(design, 'masks', 'ladders')
    for dd in (od, ol):
        os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd):
            if f.endswith('.vox.txt'):
                os.remove(os.path.join(dd, f))

    R['lists'] = {}
    for k, c in decks.items():
        R['lists']['deck-' + k] = dump(os.path.join(od, k + '.vox.txt'), c, f'# 福建趕繒船 甲板 {k}（draft_decks.py）\n')
    for k, c in lad.items():
        R['lists']['ladders-' + k] = dump(os.path.join(ol, k + '.vox.txt'), c, f'# 福建趕繒船 梯子（上到 {k}；draft_decks.py）\n')
    with open(os.path.join(design, 'ladder_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pts, f, ensure_ascii=False, indent=2)
    with open(os.path.join(design, 'decks_meta.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(decks_meta, f, ensure_ascii=False, indent=2)

    # 圖紙 04：每層俯視＋中線縱剖面
    sc = 3
    Hp = 80 + len(keys) * (ny * sc // 2 + 36) + 85 * sc + 80
    Wp = max(nx * sc + 160, 960)
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((30, 14), '福建趕繒船 新圖紙 04：4 層甲板、9 道隔艙壁、3 座梯子與空艙房 v1（藍＝梯子）', fill=(0, 0, 0), font=font(16))
    for i, k in enumerate(keys):
        oy = 55 + i * (ny * sc // 2 + 36)
        d.text((15, oy + 20), B['names'][k], fill=(0, 0, 0), font=font(13))
        top = decks[k].max(axis=2)
        lt = lad[k].max(axis=2) if k in lad else np.zeros_like(top)
        for xi_ in range(nx):
            for yi_ in range(ny):
                if lt[xi_, yi_]:
                    d.rectangle([90 + xi_ * sc, oy + yi_ * sc // 2, 90 + (xi_ + 1) * sc - 1, oy + (yi_ + 1) * sc // 2], fill=(0, 90, 200))
                elif top[xi_, yi_]:
                    d.rectangle([90 + xi_ * sc, oy + yi_ * sc // 2, 90 + (xi_ + 1) * sc - 1, oy + (yi_ + 1) * sc // 2], fill=palette_rgb(int(top[xi_, yi_])))
    oy_sec = 55 + len(keys) * (ny * sc // 2 + 36)
    yc_i = YC - ylo
    for xi_ in range(nx):
        for z in range(min(nz, 82)):
            c = H_col[xi_, yc_i, z] if wall[xi_, yc_i, z] else 0
            for dd in list(decks.values()) + list(lad.values()):
                if dd[xi_, yc_i, z]:
                    c = dd[xi_, yc_i, z]
            if c:
                d.rectangle([90 + xi_ * sc, oy_sec + (82 - z) * sc, 90 + (xi_ + 1) * sc - 1, oy_sec + (82 - z + 1) * sc - 1], fill=palette_rgb(int(c)))
    im.save(os.path.join(design, 'sheet04_decks_v1.png'))
    with open(os.path.join(design, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in R.items() if k not in ('ladder_points', 'lists', 'decks_meta')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
