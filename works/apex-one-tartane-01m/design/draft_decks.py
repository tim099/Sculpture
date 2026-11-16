# 塔爾塔納 步驟 5（TASK-1299）：各層甲板、貨艙口與梯井、梯子（4 座＋四點）、空艙房檢查
#   輸出：masks/decks/<層>.vox.txt、masks/ladders/<上層>.vox.txt、ladder_points.json、decks_meta.tsv、verify_decks.json、sheet04_decks_v1.png
#   用法：python -I -X utf8 draft_decks.py <design> [--probe=drop_ladder=hold]
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb


def mast_hit(plan, L, key, X, Y, Z, r):
    xa = LY.mast_axis_x(plan, key, Z, L)
    return (np.asarray(X, float) + 0.5 - (xa + 0.5)) ** 2 + (np.asarray(Y, float) - plan['space']['yc']) ** 2 <= r * r


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist)
    inside = S & ~wall
    nx, ny, nz = S.shape
    X = np.arange(nx) + x0
    Y = np.arange(ny) + ylo
    DY = Y - YC
    B = plan['decks_build']
    rows = {r['key']: r for r in plan['decks']['rows']}
    span = {k: LY.deck_span(plan, L, k) for k in rows}
    zdeck = {k: LY.deck_z(plan, k, X + 0.5).astype(int) for k in rows}

    LD = B['ladders']
    ladders = [dict(l) for l in LD['list']]
    if probe:
        drop = probe[0].split('=')[1]
        ladders = [l for l in ladders if l['name'] != drop]
    th = LD['tread_half']

    hole = {k: np.zeros((nx, ny), bool) for k in rows}
    coam = {k: np.zeros((nx, ny), bool) for k in rows}
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
        zl = int(zdeck[ld['lo']][xs - x0])
        hx = ld['head_x']
        zu = int(zdeck[ld['up']][hx - x0])
        n = (zu - zl - 1) // LD['rise']
        xa, xb = sorted((xs + s * LD['run'], xs + s * LD['run'] * n + s * (LD['run'] - 1)))
        m = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - yc)[None, :] <= th + 1)
        hole[ld['up']] |= m
        side = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - yc)[None, :] == th + 2)
        low_end = (X[:, None] == xa - s) & (np.abs(Y - yc)[None, :] <= th + 2)
        coam[ld['up']] |= side | low_end

    mast_keys = [m['key'] for m in plan['masts']['rows'] if m['key'] != 'bowsprit']
    MS = {m['key']: m for m in LY.masts(plan, L)}
    for k in rows:
        for mk in mast_keys:
            if zdeck[k][MS[mk]['x'] - x0] <= MS[mk]['heel'] + 0.5:
                continue
            hit = mast_hit(plan, L, mk, X[:, None], Y[None, :], zdeck[k][:, None] + 0.5, B['mast_r'][mk])
            hole[k] |= hit
    for k in rows:
        coam[k] &= ~hole[k]

    decks = {}
    for k in rows:
        cell = np.zeros(S.shape, np.uint8)
        plank = B['plank']['weather'] if k in B['plank']['weather_decks'] else B['plank']['interior']
        bd = B['beam']['depth'][k]
        a, b = span[k]
        for xi in range(nx):
            if not (a <= X[xi] <= b):
                continue
            z = zdeck[k][xi]
            row = inside[xi, :, z] & ~hole[k][xi]
            cell[xi, row, z] = plank
            if (X[xi] % B['beam']['every']) < B['beam']['w']:
                for dz in range(1, bd + 1):
                    rb = inside[xi, :, z - dz] & ~hole[k][xi]
                    cell[xi, rb & (cell[xi, :, z - dz] == 0), z - dz] = B['beam']['color']
            for dz in range(1, B['coaming_h'] + 1):
                rc = inside[xi, :, z + dz] & coam[k][xi]
                cell[xi, rc, z + dz] = B['trim']
        decks[k] = cell

    gaps = {}
    for ld in ladders:
        if not ld.get('well'):
            gaps.setdefault(ld['up'], []).append(YC + ld['dy'])
    for br in B['breaks']:
        xi = br['x'] - x0
        zl, zu = int(zdeck[br['lo']][xi]), int(zdeck[br['up']][xi])
        door = np.zeros(ny, bool)
        for d_dy in br.get('doors_dy', []):
            door |= np.abs(np.abs(DY) - d_dy) <= 2
        wmask = np.zeros(ny, bool)
        for w_dy in br.get('windows_dy', []):
            wmask |= np.abs(np.abs(DY) - w_dy) <= 1
        for z in (range(zl + 1, zu) if br.get('bulkhead', True) else ()):
            cut = (door & (z <= zl + 15)) | (wmask & (28 <= z <= 30))
            rowm = inside[xi, :, z] & ~cut
            decks[br['up']][xi, rowm & (decks[br['up']][xi, :, z] == 0), z] = B['trim']
        gap = np.zeros(ny, bool)
        for yc in gaps.get(br['up'], []):
            gap |= np.abs(Y - yc) <= th + 1
        for z in range(zu + 1, zu + 1 + br['rail_h']):
            rowm = inside[xi, :, z] & ~gap
            decks[br['up']][xi, rowm, z] = B['trim']

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
        P = {'foot': [xs - s, yc, zl + 1],
             'lo': [xs + s * LD['run'], yc, zl + LD['rise'] + 1],
             'hi': [xs + s * LD['run'] * n, yc, zl + LD['rise'] * n + 1],
             'head': [hx, yc, zu + 1]}
        pts[ld['name']] = {'up': up, 'lo': lo, 'points': P, 'steps': n}

    anyd = np.zeros(S.shape, bool)
    for c in decks.values():
        anyd |= c > 0
    for k in lad:
        lad[k][anyd | wall] = 0

    uni = wall.copy()
    for c in list(decks.values()) + list(lad.values()):
        uni |= c > 0
    cav = ndimage.binary_fill_holes(uni) & ~uni
    labc, ncav = ndimage.label(cav)
    filled = []
    for i in range(1, ncav + 1):
        idx = np.argwhere(labc == i)
        xm, zm = int(np.median(idx[:, 0])), float(np.median(idx[:, 2]))
        k = min(rows, key=lambda kk: abs(zdeck[kk][xm] - zm) + (0 if span[kk][0] <= xm + x0 <= span[kk][1] else 1000))
        decks[k][labc == i] = B['beam']['color']
        filled.append({'deck': k, 'cells': int(len(idx)), 'x': [int(idx[:, 0].min() + x0), int(idx[:, 0].max() + x0)], 'z': [int(idx[:, 2].min()), int(idx[:, 2].max())]})

    # 重算船尾小艙可框純空氣矩陣（空艙房）
    every = wall.copy()
    for c in list(decks.values()) + list(lad.values()):
        every |= c > 0
    # 找 cabin (x=104..118, z=20..33) 的純空氣對稱半寬（quarter 横樑在 x=100,110,120 下伸 1 格到 z=34 ⇒ z=20..33 全空）
    yc_i = YC - ylo
    c_ymin, c_ymax = 0, ny
    for dy_lim in range(1, 22):
        ok_box = not every[104 - x0:117 - x0 + 1, yc_i - dy_lim:yc_i + dy_lim + 1, 20:34].any()
        if ok_box:
            c_ymin, c_ymax = YC - dy_lim, YC + dy_lim
        else:
            break
    room_spec = {'stern_cabin': {'min': [104, c_ymin, 20], 'max': [117, c_ymax, 33], 'door': [118, YC, 20],
                                 'width_m': round((c_ymax - c_ymin + 1) * 0.1, 2), 'len_m': 1.4, 'h_m': 1.4}}

    R = {'decks': {}, 'ladders': {}, 'rooms': room_spec}
    allc = np.zeros(S.shape, np.int16)
    for k, c in decks.items():
        m = c > 0
        R['decks'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & wall).sum()), 'outside_hull': int((m & ~S).sum()),
                         'colors': {int(a): int(b) for a, b in zip(*np.unique(c[m], return_counts=True))}, 'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    for k, c in lad.items():
        m = c > 0
        R['ladders'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & wall).sum()), 'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    R['overlap_between_parts'] = int((allc > 1).sum())

    bad = []
    for nm, v in pts.items():
        for pk, (px, py, pz) in v['points'].items():
            xi_, yi_ = px - x0, py - ylo
            ok_air = not every[xi_, yi_, pz]
            ok_floor = bool(every[xi_, yi_, pz - 1])
            head = int(every[xi_, yi_, pz:pz + 12].sum())
            if not (ok_air and ok_floor) or head:
                bad.append((nm, pk, [px, py, pz], ok_air, ok_floor, head))

    R['ladder_points'] = pts
    R['ladder_point_problems'] = bad
    R['ladder_count'] = len(pts)
    R['reach'] = {k: sorted(nm for nm, v in pts.items() if k in (v['up'], v['lo'])) for k in rows}
    R['holes'] = {k: int(hole[k].sum()) for k in rows}
    R['cavities_filled'] = filled

    if probe:
        print(json.dumps({'probe': probe[0], 'ladder_count': len(pts), 'reach': R['reach']}, ensure_ascii=False))
        return

    # 產生 decks_meta.tsv（依 floor 陣列自動產生含舷弧點對）
    tsv_lines = []
    level_of = {'hold': 0, 'cabin': 1, 'main': 2, 'quarter': 3}
    for r in plan['decks']['rows']:
        k = r['key']
        a, b = span[k]
        if k != 'main':
            fl = '%d:%d,%d:%d' % (a, r['z'] + 1, b, r['z'] + 1)
        else:
            xs_pts = sorted({a, 145, 160, 175, 200, 220, 240, b})
            xs_pts = [xx for xx in xs_pts if a <= xx <= b]
            fl = ','.join('%d:%d' % (xx, int(zdeck['main'][xx - x0]) + 1) for xx in xs_pts)
        thk = B['beam']['depth'][k] + 1
        meta = json.dumps({'kind': 'deck', 'deck': k, 'level': level_of[k], 'name': r['name'], 'floor': fl, 'thick': thk}, ensure_ascii=False, separators=(',', ':'))
        tsv_lines.append('link\t甲板-%s\t%s\n' % (k, meta))
    with open(os.path.join(design, 'decks_meta.tsv'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.writelines(tsv_lines)

    def dump(path, c, head):
        idx = np.argwhere(c > 0)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for xi_, yi_, z in idx:
                f.write('%d,%d,%d,%d\n' % (xi_ + x0, yi_ + ylo, z, c[xi_, yi_, z]))
        return [int(len(idx)), hashlib.sha256(open(path, 'rb').read()).hexdigest()]

    od, ol = os.path.join(design, 'masks', 'decks'), os.path.join(design, 'masks', 'ladders')
    for dd in (od, ol):
        os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd):
            if f.endswith('.vox.txt'):
                os.remove(os.path.join(dd, f))
    R['lists'] = {}
    for k, c in decks.items():
        R['lists']['deck-' + k] = dump(os.path.join(od, k + '.vox.txt'), c, '# 塔爾塔納 甲板 %s（at 0,0,0）\n' % k)
    for k, c in lad.items():
        R['lists']['ladders-' + k] = dump(os.path.join(ol, k + '.vox.txt'), c, '# 塔爾塔納 梯子（上到 %s；at 0,0,0）\n' % k)
    with open(os.path.join(design, 'ladder_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pts, f, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'rooms_spec.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(room_spec, f, ensure_ascii=False, indent=1)

    keys = list(rows)
    Hp = 80 + len(keys) * (ny + 30) + nz + 60
    im = Image.new('RGB', (nx + 140, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((4, 4), 'Tartane sheet 04 decks/ladders v1', fill=(0, 0, 0), font=font(10))
    for i, k in enumerate(keys):
        oy = 60 + i * (ny + 30)
        d.text((10, oy + ny // 2 - 6), k, fill=(0, 0, 0), font=font(12))
        top = decks[k].max(axis=2)
        lt = lad[k].max(axis=2) if k in lad else np.zeros_like(top)
        for xi_ in range(nx):
            for yi_ in range(ny):
                if lt[xi_, yi_]:
                    d.point((100 + xi_, oy + yi_), fill=(0, 90, 200))
                elif top[xi_, yi_]:
                    d.point((100 + xi_, oy + yi_), fill=palette_rgb(int(top[xi_, yi_])))
    oy = 60 + len(keys) * (ny + 30)
    for xi_ in range(nx):
        for z in range(nz):
            c = col[xi_, yc_i, z] if wall[xi_, yc_i, z] else 0
            for dd in list(decks.values()) + list(lad.values()):
                if dd[xi_, yc_i, z]:
                    c = dd[xi_, yc_i, z]
            if c:
                d.point((100 + xi_, oy + nz - z), fill=palette_rgb(int(c)))
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(os.path.join(design, 'sheet04_decks_v1.png'))
    with open(os.path.join(design, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('ladder_points', 'lists')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
