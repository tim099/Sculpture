# 明鄭一號大鳥船 新圖紙 04（TASK-1316 步驟 5）：四層甲板（底艙／主砲甲板／上戰棚／高尾樓）、20 道水密隔艙壁、貨艙口與桅孔、break、5 座梯子、2 間機能艙房
#   輸入：plan.json + draft_lines + masks/ports/carve.vox.txt（實際雕刻後船殼）
#   輸出：masks/decks/<層>.vox.txt、masks/ladders/<上層>.vox.txt、masks/rooms/<層>.vox.txt、
#         ladder_points.json、room_points.json、decks_meta.json、verify_decks.json、sheet04_decks_v1.png
#   用法：python -I -X utf8 draft_decks.py <design 資料夾> [--probe=drop_ladder=<梯名>]
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL

sys.stdout.reconfigure(encoding='utf-8')


def mast_axis_x(plan, key, z):
    m = plan['masts'][key]
    return float(m['x']) + (np.asarray(z, float) - float(m['heel_z'])) * math.tan(math.radians(float(m['rake_deg'])))


def load_carved_shell(design, plan, L, x0, ylo, shape):
    nx, ny, nz = shape
    hull_dir = os.path.join(design, 'masks', 'hull')
    carve_p = os.path.join(design, 'masks', 'ports', 'carve.vox.txt')
    pts = []
    for fn in sorted(os.listdir(hull_dir)):
        if fn.endswith('.vox.txt'):
            a = np.loadtxt(os.path.join(hull_dir, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
            if a.size:
                pts.append(a)
    A = np.concatenate(pts) if pts else np.zeros((0, 4), np.int32)
    wall = np.zeros(shape, np.uint8)
    xi = A[:, 0] - x0
    yi = A[:, 1] - ylo
    zi = A[:, 2]
    m = (xi >= 0) & (xi < nx) & (yi >= 0) & (yi < ny) & (zi >= 0) & (zi < nz)
    wall[xi[m], yi[m], zi[m]] = A[m, 3]
    full_wall = wall > 0

    if os.path.exists(carve_p):
        C = np.loadtxt(carve_p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
        if C.size:
            cx, cy, cz = C[:, 0] - x0, C[:, 1] - ylo, C[:, 2]
            cm = (cx >= 0) & (cx < nx) & (cy >= 0) & (cy < ny) & (cz >= 0) & (cz < nz)
            wall[cx[cm], cy[cm], cz[cm]] = 0
    return wall, full_wall


def port_boxes(plan, L):
    """與 draft_ports.py 同步的砲門開口位置清單（供檢查艙內淨空）。"""
    YC = L.YC
    P = plan['ports']
    boxes = []
    xs_top = np.array([p[0] for p in plan['lines']['top']], float)
    zs_top = np.array([p[1] for p in plan['lines']['top']], float)

    def top_z_at(x):
        return float(np.interp(float(x), xs_top, zs_top))

    # 下層主砲甲板 12 門
    enc = P['enclosed']
    f_main = int(plan['decks']['main']['floor'])
    z0, z1 = f_main + int(enc['sill']), f_main + int(enc['sill']) + int(enc['h']) - 1
    hw = int(enc['w']) // 2
    for i, x in enumerate(enc['x'], 1):
        boxes.append(('main', f'enc-{i}', x - hw, x + hw - 1, z0, z1))

    # 上戰棚 bow hongyi + fagong
    f_up = int(plan['decks']['upper']['floor'])
    for nm, cfg in (('uhy', P['upper_hongyi']), ('fag', P['upper_fagong'])):
        hw_ = int(cfg['w']) // 2
        zs = f_up + int(cfg['sill'])
        for i, x in enumerate(cfg['x'], 1):
            zt = int(math.ceil(top_z_at(x))) + 1
            boxes.append(('upper', f'{nm}-{i}', x - hw_, x + hw_ - 1, zs, zt))
    return boxes


def main():
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = a

    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    zmax = int(math.ceil(L.top_max)) + 2
    x0 = int(math.floor(L.xa_min)) - 3
    x1 = int(math.ceil(L.xf_max)) + 3
    half = int(math.ceil(L.B)) + 6
    ylo = L.YC - half
    yhi = L.YC + half

    S = L.solid(x0, x1, zmax, 0)[:, ylo:yhi + 1, :]
    wall_col, full_wall = load_carved_shell(design, plan, L, x0, ylo, S.shape)
    wall = wall_col > 0
    # 艙裡 ＝ 外形實心扣掉未開孔前整片船殼牆（砲門與艉窗空間不計為艙內甲板）
    inside = S & ~full_wall

    nx, ny, nz = S.shape
    X = np.arange(nx) + x0
    Y = np.arange(ny) + ylo
    DY = Y - YC

    B = plan['decks_build']
    deck_keys = list(plan['decks'].keys())
    DK = plan['decks']
    span = {k: tuple(B['spans'][k]) for k in deck_keys}
    # floor 值為甲板上第一層空氣；鋪板最高在 z = floor - 1
    zdeck = {k: np.full(nx, int(DK[k]['floor']), dtype=int) for k in deck_keys}

    LD = B['ladders']
    ladders = [dict(l) for l in LD['list']]
    if probe and probe.startswith('drop_ladder='):
        drop = probe.split('=', 1)[1]
        ladders = [l for l in ladders if l['name'] != drop]
    th = int(LD['tread_half'])

    # ── 開口：貨艙口、梯井、桅孔 ──
    hole = {k: np.zeros((nx, ny), bool) for k in deck_keys}
    coam = {k: np.zeros((nx, ny), bool) for k in deck_keys}
    for h in B['hatches']:
        m = (X[:, None] >= h['x0']) & (X[:, None] <= h['x1']) & (np.abs(DY)[None, :] <= h['half'])
        ring = (X[:, None] >= h['x0'] - 1) & (X[:, None] <= h['x1'] + 1) & (np.abs(DY)[None, :] <= h['half'] + 1) & ~m
        for k in h['decks']:
            hole[k] |= m
            coam[k] |= ring

    for ld in ladders:
        if not ld.get('well'):
            continue
        s, xs, yc = int(ld['dir']), int(ld['xs']), YC + int(ld['dy'])
        wa, wb = int(ld.get('well_a', 4)), int(ld.get('well_b', 16))
        xa, xb = sorted((xs + s * wa, xs + s * wb))
        m = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - yc)[None, :] <= th + 2)
        hole[ld['up']] |= m
        side = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - yc)[None, :] == th + 3)
        low_end = (X[:, None] == xs + s * (wa - 1)) & (np.abs(Y - yc)[None, :] <= th + 3)
        coam[ld['up']] |= side | low_end

    mast_keys = [mk for mk in ('fore', 'main', 'mizzen') if mk in plan['masts']]
    for k in deck_keys:
        z_air = int(DK[k]['floor'])
        for mk in mast_keys:
            heel_z = float(plan['masts'][mk]['heel_z'])
            if z_air <= heel_z + 0.5:
                continue  # 桅腳立於該層或更上層，不開孔
            mx_at = mast_axis_x(plan, mk, z_air - 0.5)
            mr = float(B['mast_r'][mk])
            hit = ((X[:, None] + 0.5 - (mx_at + 0.5)) ** 2 + (Y[None, :] + 0.5 - (YC + 0.5)) ** 2) <= mr * mr
            hole[k] |= hit
    for k in deck_keys:
        coam[k] &= ~hole[k]

    # ── 甲板：鋪板 (floor - 1) ＋ 橫樑 (floor - 2) ＋ 艙口/梯井圍欄 (floor) ──
    decks = {}
    phase = int(B['beam'].get('phase', 0))
    every = int(B['beam']['every'])
    bw = int(B['beam']['w'])
    for k in deck_keys:
        cell = np.zeros(S.shape, np.uint8)
        plank = int(B['plank']['weather']) if k in B['plank']['weather_decks'] else int(B['plank']['interior'])
        bd = int(B['beam']['depth'][k])
        a, b = span[k]
        z_air = int(DK[k]['floor'])
        zp = z_air - 1  # 鋪板層
        for xi in range(nx):
            xw = int(X[xi])
            if not (a <= xw <= b):
                continue
            row = inside[xi, :, zp] & ~hole[k][xi]
            cell[xi, row, zp] = plank
            if ((xw - phase) % every) < bw:
                for dz in range(1, bd + 1):
                    zb_idx = zp - dz
                    if zb_idx >= 0:
                        rb = inside[xi, :, zb_idx] & ~hole[k][xi]
                        cell[xi, rb & (cell[xi, :, zb_idx] == 0), zb_idx] = int(B['beam']['color'])
            for dz in range(0, int(B['coaming_h'])):
                zc_idx = z_air + dz
                if zc_idx < nz:
                    rc = inside[xi, :, zc_idx] & coam[k][xi]
                    cell[xi, rc, zc_idx] = int(B['trim'])
        decks[k] = cell

    # ── 20 道橫向水密隔艙壁（位於底艙 deck-hold：z=12..46，留中央門洞通行）──
    bh = B['bulkhead']
    z_hold_air = int(DK['hold']['floor'])
    z_main_plank = int(DK['main']['floor']) - 1
    bh_door_half = int(bh['door_half'])
    bh_door_top = z_hold_air + int(bh['door_h']) - 1
    bh_col = int(bh['color'])
    for xw in bh['x']:
        xi = int(xw) - x0
        if not (0 <= xi < nx):
            continue
        door_m = np.abs(DY) <= bh_door_half
        sealed = int(xw) in bh.get('end_sealed', [])
        for z in range(z_hold_air, z_main_plank):
            rowm = inside[xi, :, z].copy()
            if (not sealed) and (z <= bh_door_top):
                rowm &= ~door_m
            # 隔艙頂樑若撞到 deck-main 橫樑則讓 deck-main
            sel = rowm & (decks['main'][xi, :, z] == 0) & (decks['hold'][xi, :, z] == 0)
            decks['hold'][xi, sel, z] = bh_col

    # ── Break（x=132 高尾樓前斷牆＋門洞＋樓頂護欄，歸於 deck-poop）──
    gaps = {}
    for ld in ladders:
        if 'head_x' in ld:
            gaps.setdefault(ld['up'], []).append(YC + int(ld['dy']))
    for br in B['breaks']:
        xi = int(br['x']) - x0
        zl = int(DK[br['lo']]['floor'])
        zu = int(DK[br['up']]['floor'])  # poop air = 92, plank = 91
        door = np.zeros(ny, bool)
        dh = int(br.get('door_half', 2))
        d_height = int(br.get('door_h', 17))
        for d in br['doors_dy']:
            door |= np.abs(np.abs(DY) - int(d)) <= dh
        for z in range(zl, zu):
            rowm = inside[xi, :, z] & ~(door & (z < zl + d_height))
            sel = rowm & (decks[br['up']][xi, :, z] == 0) & (decks[br['lo']][xi, :, z] == 0)
            decks[br['up']][xi, sel, z] = int(br['color'])
        gap = np.zeros(ny, bool)
        for yk in gaps.get(br['up'], []):
            gap |= np.abs(Y - yk) <= th + 1
        for z in range(zu, zu + int(br['rail_h'])):
            rowm = inside[xi, :, z] & ~gap
            decks[br['up']][xi, rowm, z] = int(br.get('rail_color', B['trim']))

    # ── 梯子（依 rise=3, run=2；從 lo.floor 上到 up.floor）──
    LC = int(LD['color'])
    lad, pts = {}, {}
    for ld in ladders:
        up, lo = ld['up'], ld['lo']
        cell = lad.setdefault(up, np.zeros(S.shape, np.uint8))
        s, xs = int(ld['dir']), int(ld['xs'])
        yc = YC + int(ld['dy'])
        yc_i = yc - ylo
        zl = int(DK[lo]['floor'])
        zu = int(DK[up]['floor'])
        n = (zu - zl - 1) // int(LD['rise'])
        hx = int(ld['head_x'])
        for kk in range(0, n + 2):
            xa = xs + s * int(LD['run']) * kk
            xr = sorted((xa, xa + s * (int(LD['run']) - 1)))
            if kk == n + 1 and not ld.get('well'):
                xr = [xa, xa]
            zt = zl + int(LD['rise']) * kk
            for xx in range(xr[0], xr[1] + 1):
                if 1 <= kk <= n:
                    cell[xx - x0, yc_i - th:yc_i + th + 1, zt] = LC
                if kk == 0:
                    zlo, zhi = zl, zl + 2
                elif kk <= n:
                    zlo, zhi = zt - 3, zt
                else:
                    zlo, zhi = zl + int(LD['rise']) * n - 3, zu - 1
                for z in range(max(0, zlo), min(nz, zhi + 1)):
                    for yy in (yc_i - th - 1, yc_i + th + 1):
                        cell[xx - x0, yy, z] = LC
        P = {
            'foot': [xs - s, yc, zl],
            'lo': [xs + s * int(LD['run']), yc, zl + int(LD['rise']) + 1],
            'hi': [xs + s * int(LD['run']) * n, yc, zl + int(LD['rise']) * n + 1],
            'head': [hx, yc, zu],
        }
        pts[ld['name']] = {'up': up, 'lo': lo, 'points': P, 'steps': n}

    # ── 機能艙房實木隔牆（rooms-upper 後舵艙前/側隔屏 x=101, y=107/149 + rooms-hold 貨艙側欄）──
    rooms_vox = {}
    room_pts = {}

    # 1) upper 後艙房（x=102..131, y=108..148, z=70..89）→ 實木側隔板 y=107, 149 與後艙壁 x=101（x=101 在 y=134..138 留門洞避開尾桅 x=96）
    ru = np.zeros(S.shape, np.uint8)
    z_u_air, z_p_beam = int(DK['upper']['floor']), int(DK['poop']['floor']) - 2
    for z in range(z_u_air, z_p_beam + 1):
        for yw in (107, 149):
            yi = yw - ylo
            for xw in range(101, 132):
                xi = xw - x0
                if inside[xi, yi, z]:
                    ru[xi, yi, z] = int(B['bulkhead']['color'])
        xi_aft = 101 - x0
        for yw in range(108, 149):
            yi = yw - ylo
            if not (133 <= yw <= 141 and z < z_u_air + 17) and inside[xi_aft, yi, z]:
                ru[xi_aft, yi, z] = int(B['bulkhead']['color'])
    # 清掉與 deck/wall 重疊
    for dk_c in decks.values():
        ru[dk_c > 0] = 0
    ru[wall] = 0
    rooms_vox['upper'] = ru
    room_pts['upper'] = {
        '1': {
            'min': [102, 108, 70],
            'max': [131, 148, 89],
            'door': [132, 128, 70],
        }
    }

    # 2) hold 中央貨艙間（x=259..275, y=110..146, z=12..45）→ 兩側低護欄 y=109, 147 (z=12..17) 形成獨立貨艙界
    rh = np.zeros(S.shape, np.uint8)
    for z in range(12, 18):
        for yw in (109, 147):
            yi = yw - ylo
            for xw in range(259, 276):
                xi = xw - x0
                if inside[xi, yi, z] and decks['hold'][xi, yi, z] == 0:
                    rh[xi, yi, z] = int(B['trim'])
    rooms_vox['hold'] = rh
    room_pts['hold'] = {
        '1': {
            'min': [259, 110, 12],
            'max': [275, 146, 45],
            'door': [258, 128, 12],
        }
    }

    # 甲板與船殼優先，梯子讓路
    any_fixed = wall.copy()
    for c in list(decks.values()) + list(rooms_vox.values()):
        any_fixed |= c > 0
    for k in lad:
        lad[k][any_fixed] = 0

    # ── 封閉空腔：底艙 (hold z<10) 尖底壓艙底肋自動填實進 hold（橫樑色），保零空腔 ──
    uni = wall.copy()
    for c in list(decks.values()) + list(lad.values()) + list(rooms_vox.values()):
        uni |= c > 0
    cav = ndimage.binary_fill_holes(uni) & ~uni
    labc, ncav = ndimage.label(cav)
    filled = []
    for i in range(1, ncav + 1):
        idx = np.argwhere(labc == i)
        xm, zm = int(np.median(idx[:, 0])), float(np.median(idx[:, 2]))
        k = min(deck_keys, key=lambda kk: abs(zdeck[kk][xm] - zm) + (0 if span[kk][0] <= xm + x0 <= span[kk][1] else 1000))
        decks[k][labc == i] = int(B['beam']['color'])
        filled.append({
            'deck': k, 'cells': int(len(idx)),
            'x': [int(idx[:, 0].min() + x0), int(idx[:, 0].max() + x0)],
            'z': [int(idx[:, 2].min()), int(idx[:, 2].max())],
        })

    # ── 檢查讀數 ──
    R = {'decks': {}, 'ladders': {}, 'rooms': {}}
    allc = np.zeros(S.shape, np.int16)
    for k, c in decks.items():
        m = c > 0
        R['decks'][k] = {
            'cells': int(m.sum()),
            'hull_overlap': int((m & wall).sum()),
            'outside_hull': int((m & ~S).sum()),
            'mirror_diff': int((m != m[:, ::-1, :]).sum()),
        }
        allc += m
    for k, c in lad.items():
        m = c > 0
        R['ladders'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & wall).sum())}
        allc += m
    for k, c in rooms_vox.items():
        m = c > 0
        R['rooms'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & wall).sum())}
        allc += m
    R['overlap_between_parts'] = int((allc > 1).sum())

    every = wall.copy()
    for c in list(decks.values()) + list(lad.values()) + list(rooms_vox.values()):
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

    room_problems = []
    for dk, rmap in room_pts.items():
        for rname, rv in rmap.items():
            rx0, ry0, rz0 = rv['min']
            rx1, ry1, rz1 = rv['max']
            sub = every[rx0 - x0:rx1 - x0 + 1, ry0 - ylo:ry1 - ylo + 1, rz0:rz1 + 1]
            sub_floor = every[rx0 - x0:rx1 - x0 + 1, ry0 - ylo:ry1 - ylo + 1, rz0 - 1]
            non_air = int(sub.sum())
            unfloored = int((~sub_floor).sum())
            dx, dy, dz = rv['door']
            door_ok = (not every[dx - x0, dy - ylo, dz]) and bool(every[dx - x0, dy - ylo, dz - 1])
            if non_air or unfloored or not door_ok:
                room_problems.append((dk, rname, non_air, unfloored, door_ok))

    blocked = []
    for dk, pnm, px0, px1, pz0, pz1 in port_boxes(plan, L):
        for side in (1, -1):
            n = 0
            for x in range(px0, px1 + 1):
                for z in range(pz0, pz1 + 1):
                    for dy in range(18, 56):
                        yi_ = YC + side * dy - ylo
                        if 0 <= yi_ < ny and inside[x - x0, yi_, z] and allc[x - x0, yi_, z]:
                            n += 1
            if n:
                blocked.append((dk, pnm, 'S' if side > 0 else 'P', n))

    # 驗證組起後的總封閉空腔數 ＝ 0
    post_cav = ndimage.binary_fill_holes(every) & ~every
    R['post_cavities'] = int(post_cav.sum())
    R['ports_blocked_inside'] = blocked
    R['ladder_points'] = pts
    R['ladder_point_problems'] = bad
    R['ladder_count'] = len(pts)
    R['room_problems'] = room_problems
    R['reach'] = {k: sorted(nm for nm, v in pts.items() if k in (v['up'], v['lo'])) for k in deck_keys}
    R['holes'] = {k: int(hole[k].sum()) for k in deck_keys}
    R['cavities_filled'] = filled

    if probe:
        print(json.dumps({'probe': probe, 'ladder_count': len(pts), 'reach': R['reach']}, ensure_ascii=False))
        return

    def dump(path, c, head):
        idx = np.argwhere(c > 0)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for xi_, yi_, z in idx:
                f.write('%d,%d,%d,%d\n' % (xi_ + x0, yi_ + ylo, z, c[xi_, yi_, z]))
        return [int(len(idx)), hashlib.sha256(open(path, 'rb').read()).hexdigest()]

    od = os.path.join(design, 'masks', 'decks')
    ol = os.path.join(design, 'masks', 'ladders')
    orr = os.path.join(design, 'masks', 'rooms')
    for dd in (od, ol, orr):
        os.makedirs(dd, exist_ok=True)
        for fn in os.listdir(dd):
            if fn.endswith('.vox.txt'):
                os.remove(os.path.join(dd, fn))

    R['lists'] = {}
    for k, c in decks.items():
        R['lists']['deck-' + k] = dump(os.path.join(od, k + '.vox.txt'), c, '# 明鄭一號大鳥船 甲板 %s（draft_decks.py）\n' % k)
    for k, c in lad.items():
        R['lists']['ladders-' + k] = dump(os.path.join(ol, k + '.vox.txt'), c, '# 明鄭一號大鳥船 梯子（上到 %s）\n' % k)
    for k, c in rooms_vox.items():
        R['lists']['rooms-' + k] = dump(os.path.join(orr, k + '.vox.txt'), c, '# 明鄭一號大鳥船 機能艙房 %s\n' % k)

    with open(os.path.join(design, 'ladder_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pts, f, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'room_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(room_pts, f, ensure_ascii=False, indent=1)

    # 輸出給 Step 5 的甲板 meta（含 floor 弦弧點與 thick）
    decks_meta = {}
    for k in deck_keys:
        a, b = span[k]
        z_air = int(DK[k]['floor'])
        # 嚴格對齊該層有實體地板的 [x_min, x_max] 範圍
        occ_x = X[(decks[k] > 0).any(axis=(1, 2))]
        fx0, fx1 = (int(occ_x.min()), int(occ_x.max())) if len(occ_x) else (a, b)
        decks_meta[k] = {
            'kind': 'deck',
            'deck': k,
            'level': int(DK[k]['level']),
            'name': B['names'][k],
            'floor': f'{fx0}:{z_air},{fx1}:{z_air}',
            'thick': int(DK[k]['thick']),
        }
    with open(os.path.join(design, 'decks_meta.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(decks_meta, f, ensure_ascii=False, indent=1)

    # 圖紙 sheet04_decks_v1.png
    keys = deck_keys
    Hp = 80 + len(keys) * (ny + 30) + nz + 60
    im = Image.new('RGB', (nx + 140, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((40, 16), '明鄭一號大鳥船 新圖紙 04：4 層甲板、20 水密隔艙、梯子與機能艙房（藍=梯子）', fill=(0, 0, 0), font=DL.font(16))
    for i, k in enumerate(keys):
        oy = 60 + i * (ny + 30)
        d.text((10, oy + ny // 2 - 6), k, fill=(0, 0, 0), font=DL.font(12))
        top = decks[k].max(axis=2)
        if k in rooms_vox:
            top = np.maximum(top, rooms_vox[k].max(axis=2))
        lt = lad[k].max(axis=2) if k in lad else np.zeros_like(top)
        for xi_ in range(nx):
            for yi_ in range(ny):
                if lt[xi_, yi_]:
                    d.point((100 + xi_, oy + yi_), fill=(0, 90, 200))
                elif top[xi_, yi_]:
                    d.point((100 + xi_, oy + yi_), fill=DL.rgb(int(top[xi_, yi_])))
    oy = 60 + len(keys) * (ny + 30)
    yc_i = YC - ylo
    for xi_ in range(nx):
        for z in range(nz):
            c = wall_col[xi_, yc_i, z] if wall[xi_, yc_i, z] else 0
            for dd in list(decks.values()) + list(rooms_vox.values()) + list(lad.values()):
                if dd[xi_, yc_i, z]:
                    c = dd[xi_, yc_i, z]
            if c:
                d.point((100 + xi_, oy + nz - z), fill=DL.rgb(int(c)))
    im.save(os.path.join(design, 'sheet04_decks_v1.png'))

    with open(os.path.join(design, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('ladder_points', 'lists')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
