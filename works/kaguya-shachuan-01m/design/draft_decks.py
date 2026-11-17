# 沙船 步驟 5（TASK-1313）：三層甲板（底艙／主甲板／尾樓）、水密隔艙、尾樓 break、2 座梯子、貨艙與舵艙
#   出處：kaguya-guineaman-01m/design/draft_decks.py（改寫為沙船平底＋水密隔艙＋三層甲板＋兩梯＋空艙房）
#   用法：python -I -X utf8 draft_decks.py <design 資料夾> [--probe=drop_ladder=lower]
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
    """從步驟 4 完稿（hull_01 - carve + paint）建立實際船殼布林陣列與顏色陣列。"""
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
    zdeck = {k: L.deck_z(k, X + 0.5).astype(int) for k in keys}

    LD = B['ladders']
    ladders = [dict(l) for l in LD['list']]
    if probe and probe.startswith('drop_ladder='):
        drop = probe.split('=', 1)[1]
        ladders = [l for l in ladders if l['name'] != drop]
    th = LD['tread_half']

    # ── 1. 開口（艙口、梯井、桅孔）──
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
        low_end = (X[:, None] == xs + s * 1) & (np.abs(Yy - yc)[None, :] <= th + 2)
        coam[ld['up']] |= side | low_end
    for k in keys:
        for mk, r in B['mast_r'].items():
            m = plan['masts'][mk]
            if not (span[k][0] <= m['x'] <= span[k][1]):
                continue
            if zdeck[k][m['x'] - x0] <= m['heel_z'] + 0.5:
                continue
            xa = mast_x_at(m, zdeck[k] + 0.5)
            hit = (X[:, None] + 0.5 - (xa[:, None] + 0.5)) ** 2 + (Yy[None, :] - YC) ** 2 <= r * r
            hole[k] |= hit
    for k in keys:
        coam[k] &= ~hole[k]

    # ── 2. 甲板板＋橫樑＋圍欄 ──
    decks = {}
    BM = B['beam']
    for k in keys:
        cell = np.zeros(S.shape, np.uint8)
        plank = B['plank']['weather'] if k in B['plank']['weather_decks'] else B['plank']['interior']
        bd = BM['depth'][k]
        a, b = span[k]
        for xi in range(nx):
            if not (a <= X[xi] <= b):
                continue
            z = int(zdeck[k][xi])
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

    # ── 3. 底艙水密隔艙壁（放進 hold 子作品，x=72..216，中央留通路＋前後封壁留過水眼防封閉空腔）──
    BH = B['bulkhead']
    for bx in BH['x']:
        xi = bx - x0
        zh = int(zdeck['hold'][xi])
        zm = int(zdeck['main'][xi])
        is_end = bx in BH['end_sealed']
        for z in range(zh + 1, zm - BM['depth']['main']):
            for yi in range(ny):
                if not inside[xi, yi, z]:
                    continue
                if is_end:
                    # 前後水密封壁在中央留 1 格「過水眼／通氣眼」（z = zh + 5, dy = 0），高於船底起翹段、防止封閉 3D 空腔
                    if z == zh + 5 and DY[yi] == 0:
                        continue
                else:
                    # 中間隔艙壁中央留 5 格寬 × 1.6 m 高通道（|dy| <= 2, z <= zh + door_h）
                    if abs(DY[yi]) <= BH['door_half'] and z <= zh + BH['door_h']:
                        continue
                if decks['hold'][xi, yi, z] == 0:
                    decks['hold'][xi, yi, z] = BH['color']

    # ── 4. 尾樓 break（前壁＋舵艙門＋尾樓胸牆留梯口）──
    gaps = {}
    for ld in ladders:
        if 'head_x' in ld and not ld.get('well'):
            gaps.setdefault(ld['up'], []).append(YC + ld['dy'])
    for br in B['breaks']:
        xi = br['x'] - x0
        zl, zu = int(zdeck[br['lo']][xi]), int(zdeck[br['up']][xi])
        door = np.zeros(ny, bool)
        for d_dy in br['doors_dy']:
            door |= np.abs(np.abs(DY) - d_dy) <= br['door_half']
        for z in range(zl + 1, zu):
            rowm = inside[xi, :, z] & ~(door & (z <= zl + 15))
            decks[br['up']][xi, rowm & (decks[br['up']][xi, :, z] == 0), z] = br['color']
        gap = np.zeros(ny, bool)
        for yc in gaps.get(br['up'], []):
            gap |= np.abs(Yy - yc) <= th + 1
        for z in range(zu + 1, zu + 1 + br['rail_h']):
            rowm = inside[xi, :, z] & ~gap
            decks[br['up']][xi, rowm, z] = br['color']

    # ── 5. 梯子 ──
    LC = LD['color']
    lad, pts = {}, {}
    for ld in ladders:
        up, lo = ld['up'], ld['lo']
        cell = lad.setdefault(up, np.zeros(S.shape, np.uint8))
        s, xs = ld['dir'], ld['xs']
        yc = YC + ld['dy']
        zl = int(zdeck[lo][xs - x0])
        hx = ld['head_x']
        zu = int(zdeck[up][hx - x0])
        n = (zu - zl - 1) // LD['rise']
        yc_i = yc - ylo
        for kk in range(0, n + 2):
            xa = xs + s * LD['run'] * kk
            xr = sorted((xa, xa + s * (LD['run'] - 1)))
            zt = zl + LD['rise'] * kk
            for xx in range(xr[0], xr[1] + 1):
                if 1 <= kk <= n:
                    cell[xx - x0, yc_i - th:yc_i + th + 1, zt] = LC
                if kk == 0:
                    zlo, zhi = zl + 1, zl + 3
                elif kk <= n:
                    zlo, zhi = zt - 3, zt
                else:
                    zlo, zhi = zl + LD['rise'] * n - 3, zu
                for z in range(zlo, zhi + 1):
                    for yy in (yc_i - th - 1, yc_i + th + 1):
                        cell[xx - x0, yy, z] = LC
        zf = int(zdeck[lo][xs - s - x0])
        P = {
            'foot': [xs - s, yc, zf + 1],
            'lo': [xs + s * LD['run'], yc, zl + LD['rise'] + 1],
            'hi': [xs + s * LD['run'] * n, yc, zl + LD['rise'] * n + 1],
            'head': [hx, yc, zu + 1],
        }
        pts[ld['name']] = {'up': up, 'lo': lo, 'points': P, 'steps': n}

    anyd = np.zeros(S.shape, bool)
    for c in decks.values():
        anyd |= c > 0
    for k in lad:
        lad[k][anyd | wall] = 0

    # ── 6. 封閉空腔檢查與補實 ──
    uni = wall.copy()
    for c in list(decks.values()) + list(lad.values()):
        uni |= c > 0
    cav = ndimage.binary_fill_holes(uni) & ~uni
    labc, ncav = ndimage.label(cav)
    filled = []
    for i in range(1, ncav + 1):
        idx = np.argwhere(labc == i)
        xm, zm = int(np.median(idx[:, 0])), float(np.median(idx[:, 2]))
        k = min(keys, key=lambda kk: abs(zdeck[kk][xm] - zm) + (0 if span[kk][0] <= xm + x0 <= span[kk][1] else 1000))
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

    # 檢查空艙房（貨艙與舵艙）內全空氣、腳下全實心
    rooms_check = {}
    for rk, rv in B['rooms'].items():
        rx0, rx1 = rv['x0'] - x0, rv['x1'] - x0
        ry0, ry1 = rv['y0'] - ylo, rv['y1'] - ylo
        rz0, rz1 = rv['z0'], rv['z1']
        box_solid = int(every[rx0:rx1 + 1, ry0:ry1 + 1, rz0:rz1 + 1].sum())
        floor_solid = int(every[rx0:rx1 + 1, ry0:ry1 + 1, rz0 - 1].all())
        rooms_check[rk] = {'solid_inside': box_solid, 'floor_all_solid': bool(floor_solid), 'headroom': rz1 - rz0 + 1}
    R['rooms_check'] = rooms_check
    R['cavities_filled'] = filled

    # 甲板 meta（對齊 Ship_Decks §9.3）
    decks_meta = {}
    for k in keys:
        if k == 'hold':
            fl = f"{span['hold'][0]}:{int(zdeck['hold'][span['hold'][0]-x0])+1},{span['hold'][1]}:{int(zdeck['hold'][span['hold'][1]-x0])+1}"
        elif k == 'poop':
            fl = f"{span['poop'][0]}:{int(zdeck['poop'][span['poop'][0]-x0])+1},{span['poop'][1]}:{int(zdeck['poop'][span['poop'][1]-x0])+1}"
        else:
            rx0 = plan['decks']['main']['rise_x0']
            fl = f"{span['main'][0]}:{int(zdeck['main'][span['main'][0]-x0])+1},{rx0}:{int(zdeck['main'][rx0-x0])+1},{span['main'][1]}:{int(zdeck['main'][span['main'][1]-x0])+1}"
        decks_meta[k] = {
            'kind': 'deck',
            'deck': k,
            'level': B['levels'][k],
            'name': B['names'][k],
            'floor': fl,
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
        R['lists']['deck-' + k] = dump(os.path.join(od, k + '.vox.txt'), c, f'# 沙船 甲板 {k}（draft_decks.py）\n')
    for k, c in lad.items():
        R['lists']['ladders-' + k] = dump(os.path.join(ol, k + '.vox.txt'), c, f'# 沙船 梯子（上到 {k}；draft_decks.py）\n')
    with open(os.path.join(design, 'ladder_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pts, f, ensure_ascii=False, indent=2)
    with open(os.path.join(design, 'decks_meta.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(decks_meta, f, ensure_ascii=False, indent=2)

    # 圖紙 04：每層俯視＋中線縱剖面
    sc = 3
    Hp = 80 + len(keys) * (ny * sc // 2 + 40) + nz * sc + 80
    Wp = max(nx * sc + 160, 960)
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((30, 14), '沙船 新圖紙 04：三層甲板、8 道水密隔艙、2 座梯子、貨艙與舵艙 v1（藍＝梯子）', fill=(0, 0, 0), font=font(16))
    for i, k in enumerate(keys):
        oy = 55 + i * (ny * sc // 2 + 40)
        d.text((15, oy + 20), B['names'][k], fill=(0, 0, 0), font=font(13))
        top = decks[k].max(axis=2)
        lt = lad[k].max(axis=2) if k in lad else np.zeros_like(top)
        for xi_ in range(nx):
            for yi_ in range(ny):
                if lt[xi_, yi_]:
                    d.rectangle([90 + xi_ * sc, oy + yi_ * sc // 2, 90 + (xi_ + 1) * sc - 1, oy + (yi_ + 1) * sc // 2], fill=(0, 90, 200))
                elif top[xi_, yi_]:
                    d.rectangle([90 + xi_ * sc, oy + yi_ * sc // 2, 90 + (xi_ + 1) * sc - 1, oy + (yi_ + 1) * sc // 2], fill=palette_rgb(int(top[xi_, yi_])))
    oy_sec = 55 + len(keys) * (ny * sc // 2 + 40)
    yc_i = YC - ylo
    for xi_ in range(nx):
        for z in range(nz):
            c = H_col[xi_, yc_i, z] if wall[xi_, yc_i, z] else 0
            for dd in list(decks.values()) + list(lad.values()):
                if dd[xi_, yc_i, z]:
                    c = dd[xi_, yc_i, z]
            if c:
                d.rectangle([90 + xi_ * sc, oy_sec + (nz - z) * sc, 90 + (xi_ + 1) * sc - 1, oy_sec + (nz - z + 1) * sc - 1], fill=palette_rgb(int(c)))
    im.save(os.path.join(design, 'sheet04_decks_v1.png'))
    with open(os.path.join(design, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in R.items() if k not in ('ladder_points', 'lists', 'decks_meta')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
