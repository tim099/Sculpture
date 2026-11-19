# Source: calli-cosecha-01m/design/draft_masts.py (Harvest: masts, lateen yards built slanted in their own frame, model
#   rotate 0) and apex-one-tartane-01m/design/draft_masts.py (bowsprit with a heel bitt) -- rewritten for the Star
#   (TASK-0019 step 7)
# Star (al-Najm) new sheet 05: masts and yards.
#   Inputs: plan.json (masts, rig_build, decks_build, gear), the design lists of every earlier part (hull step 4 + step 6,
#           decks, ladders, deco incl. both galleries and the two deco models) -- NOT the live works, so a rerun after
#           stamping gives the same lists.
#   Outputs:
#     masks/masts/{main,mizzen,jibboom}.vox.txt   sub-works at 0,0,0 (link meta kind=mast, mast=main|mizzen|bowsprit)
#     masks/masts/cable_beam.vox.txt              sub-work at 0,0,0 (plain link; the jib-boom heel is lashed to it)
#     masks/yards/lateen-{main,mizzen}.vox.txt    yard sub-works, frame-local
#     yards_lateen.json                           yard frames + anchors (pivot, sling, fore, peak, jackstay-NN)
#     yards_placement.json                        the yard models (host = mast sub-work): at / pivot / rotate / scale / meta
#     verify_masts.json, sheet05_masts_v1.png
#   Usage: python -X utf8 draft_masts.py <design> [--probe=pivot=<main|mizzen>:<dz>] [--probe=hole=<main|mizzen>]
#     probes (reverse controls, nothing written): shift a yard pivot by dz (the 10-40 band / clearance readings must move);
#     drop the hole-filling disk of one mast (the hole check must report the empty hole cells).
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout as LY
from draft_lines import font, palette_rgb

CELL = 0.1


def load(path, dy=0):
    out = {}
    for l in open(path, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            out[(x, y + dy, z)] = c
    return out


def ship_cells(design, plan):
    """Every cell placed before step 7, assembled from the design lists (same as tools/check_deco.py, which matched the
    engine export cell for cell), plus the two deco models (stern carving, stem head)."""
    M = os.path.join(design, 'masks')
    A = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
    A.update(load(os.path.join(M, 'step6', 'hull_recolor.vox.txt')))
    A.update(load(os.path.join(M, 'step6', 'hull_add.vox.txt')))
    for g in plan['decks_build']['groups']:
        A.update(load(os.path.join(M, 'decks', g['key'] + '.vox.txt')))
    for f in sorted(os.listdir(os.path.join(M, 'ladders'))):
        A.update(load(os.path.join(M, 'ladders', f)))
    for f in ('stern_glass', 'quarter_rail', 'stern_carving', 'stem_head'):
        A.update(load(os.path.join(M, 'deco', f + '.vox.txt')))
    FR = plan['deco']['quarter_gallery']['frame']
    gy, sy = FR['at_y'], FR['size'][1]
    for f in ('quarter_gallery', 'gallery_glass'):
        for (x, y, z), c in load(os.path.join(M, 'deco', f + '.vox.txt')).items():
            A[(x, y + gy, z)] = c
            A[(x, (161 - gy - sy) + (sy - 1 - y), z)] = c
    return A


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    YC = plan['space']['yc']
    RB = plan['rig_build']
    C = RB['colors']
    rows = {r['key']: r for r in plan['masts']['rows']}
    occ = ship_cells(design, plan)
    parts = {}
    skipped = {}
    trimmed = {}

    hull = set(load(os.path.join(design, 'masks', 'step4', 'hull4_01.vox.txt'))) | set(load(os.path.join(design, 'masks', 'step6', 'hull_add.vox.txt')))

    def put(part, k, c):
        if k in occ:
            w = 'hull' if k in hull else 'other'
            skipped.setdefault(part, {}).setdefault(w, 0)
            skipped[part][w] += 1
            return
        parts.setdefault(part, {})[k] = c

    # ── masts: hole disk (integer centre, same test as draft_decks.py) up to hole_to_z, taper, hounds lashing, square head ──
    heel = {'main': rows['main']['heel_z'], 'mizzen': int(LY.deck_z(plan, rows['mizzen']['heel_deck'], rows['mizzen']['x_step']))}
    truck = {k: heel[k] + int(round(rows[k]['len_m'] / CELL)) for k in ('main', 'mizzen')}
    for key in ('main', 'mizzen'):
        m, xm = RB['masts'][key], rows[key]['x_step']
        part = 'mast-' + key
        for z in range(heel[key], truck[key] + 1):
            if z <= m['hole_to_z']:
                r2, sq = m['hole_r'] ** 2, None
                if probe.get('hole') == key:
                    r2 = -1
            elif z < m['head_z0']:
                t = (z - m['hole_to_z'] - 1) / max(1, m['hounds_z'] - m['hole_to_z'] - 1)
                r = m['r_lo'] + (m['r_hi'] - m['r_lo']) * min(1.0, t)
                if z in (m['hounds_z'], m['hounds_z'] - 1):
                    r = m['hounds_r']
                r2, sq = r * r, None
            else:
                r2, sq = None, m['head_half']
            R_ = 5
            for dx in range(-R_, R_ + 1):
                for dy in range(-R_, R_ + 1):
                    if sq is None:
                        if dx * dx + dy * dy > r2:
                            continue
                    elif abs(dx) > sq or abs(dy) > sq:
                        continue
                    c = C['mast']
                    if z in (m['hounds_z'], m['hounds_z'] - 1) and dx * dx + dy * dy > m['r_hi'] ** 2:
                        c = C['lashing']
                    if m.get('coat') and m['hole_to_z'] - 1 <= z <= m['hole_to_z'] and dx * dx + dy * dy > m['r_lo'] ** 2:
                        c = C['lashing']          # mast coat: the ring wider than the mast, just above the deck
                    if sq is not None and dy == 0 and any(a <= z <= b for a, b in m['sheaves']):
                        c = C['sheave']
                    if z > truck[key] - m['cap_h']:
                        c = C['cap']
                    put(part, (xm + dx, YC + dy, z), c)
        # heel: the disk minus the V-bottom / keel leaves slivers cut off from the mast ⇒ keep only the main body
        cl = parts[part]
        G = np.zeros((480, 160, 400), bool)
        for (x, y, z) in cl:
            G[x, y, z] = True
        lab, n = ndimage.label(G)
        if n > 1:
            big = int(np.argmax(np.bincount(lab.ravel())[1:])) + 1
            drop = [k for k in cl if lab[k] != big]
            for k in drop:
                del cl[k]
            trimmed[part] = len(drop)

    # ── cable beam: x0..x1 × z0..z1, from the centre line outwards until the hull (both sides touch the bulwark) ──
    cb = RB['cable_beam']
    for x in range(cb['x0'], cb['x1'] + 1):
        for z in range(cb['z0'], cb['z1'] + 1):
            for sgn in (1, -1):
                y = YC if sgn == 1 else YC - 1
                while 0 <= y < 160 and (x, y, z) not in occ:
                    put('cable-beam', (x, y, z), C['cable_beam'])
                    y += sgn

    # ── jib boom (bâton-volant): heel on the cable beam, offset y; pitch solved = the lowest angle that clears every cell ──
    jb, J = rows['jibboom'], RB['jibboom']
    Lj = jb['len_m'] / CELL
    yj = YC + J['y_off']
    X0 = cb['x0'] + 0.0                                         # heel face flush with the aft face of the beam
    Z0 = cb['z1'] + 1 + J['r0']                                 # axis: boom bottom resting on the beam top
    beam_cells = parts['cable-beam']

    def boom(alpha):
        a = math.radians(alpha)
        u = (math.cos(a), math.sin(a))
        cells = {}
        for x in range(int(X0) - 3, int(X0 + Lj) + 4):
            for z in range(int(Z0) - 4, int(Z0 + Lj * u[1]) + 5):
                px, pz = x + 0.5 - X0, z + 0.5 - Z0
                t = px * u[0] + pz * u[1]
                if t < 0 or t > Lj:
                    continue
                r = J['r0'] + (J['r1'] - J['r0']) * t / Lj
                d2 = (px - t * u[0]) ** 2 + (pz - t * u[1]) ** 2
                for dy in range(-2, 3):
                    if d2 + dy * dy <= r * r:
                        cells[(x, yj + dy, z)] = (C['jibboom'], t)
        return cells

    alpha = None
    for k in range(0, 301):                                     # 0.05° steps
        a_ = k * 0.05
        cells = boom(a_)
        if not any(c in occ or c in beam_cells for c in cells):
            alpha = round(a_, 2)
            break
    if alpha is None:
        raise SystemExit('✗ jib boom: no clear pitch up to 15°')
    cells = boom(alpha)
    # contact: boom cells 6-adjacent (below) to ship cells => lashing there; heel lashing on the beam
    rest = sorted({x for (x, y, z) in cells if (x, y, z - 1) in occ and x > cb['x1'] + 4})
    lash_x = set()
    if rest:
        xr = rest[len(rest) // 2]
        lash_x |= {xr - 1, xr, xr + 1}
    lash_x |= {cb['x0'] + 1, cb['x0'] + 3}
    for k, (c, t) in cells.items():
        put('jibboom', k, C['lashing'] if k[0] in lash_x else c)
    jib_meta = {'alpha_deg': alpha, 'heel_axis': [X0, yj + 0.5, round(Z0, 2)], 'rest_x': rest[:1] + rest[-1:], 'lash_x': sorted(lash_x),
                'tip_x': round(X0 + Lj * math.cos(math.radians(alpha)), 1), 'tip_z': round(Z0 + Lj * math.sin(math.radians(alpha)), 1)}

    # ── lateen yards (frame-local): slanted pole, fore end low (x large), after end high; main has an upturned third piece ──
    lat, place = {}, []
    for key in ('main', 'mizzen'):
        Y = RB['yards'][key]
        Lc = Y['len_m'] / CELL
        th = math.radians(Y['tilt_deg'])
        pk = Y.get('peak_piece')
        Lp = pk['len_m'] / CELL if pk else 0.0
        L1 = Lc - Lp
        th2 = math.radians(Y['tilt_deg'] + (pk['extra_deg'] if pk else 0))
        pad = 3
        W_ = int(math.ceil(L1 * math.cos(th) + Lp * math.cos(th2))) + 2 * pad
        H_ = int(math.ceil(L1 * math.sin(th) + Lp * math.sin(th2))) + 2 * pad
        yc = 3
        F = (W_ - pad, pad)                                     # fore end (local x, z)
        J1 = (F[0] - L1 * math.cos(th), F[1] + L1 * math.sin(th))
        Pk = (J1[0] - Lp * math.cos(th2), J1[1] + Lp * math.sin(th2))
        segs = [(F, J1, 0.0, L1)] + ([(J1, Pk, L1, Lc)] if pk else [])
        hs = Y['hoist_frac'] * Lc

        def axis(s):
            for (a, b, s0, s1) in segs:
                if s <= s1 or (a, b, s0, s1) == segs[-1]:
                    f = (s - s0) / (s1 - s0)
                    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)

        def radius(s):
            if pk and s > L1:
                return pk['r']
            return Y['r_end'] + (Y['r_max'] - Y['r_end']) * max(0.0, 1 - abs(s - hs) / max(hs, L1 - hs))

        cells = {}
        for x in range(0, W_):
            for z in range(0, H_):
                best = None
                for (a, b, s0, s1) in segs:
                    vx, vz = b[0] - a[0], b[1] - a[1]
                    ln = math.hypot(vx, vz)
                    px, pz = x + 0.5 - a[0], z + 0.5 - a[1]
                    t = (px * vx + pz * vz) / ln
                    if t < -0.5 or t > ln + 0.5:
                        continue
                    tc = min(max(t, 0.0), ln)
                    d2 = (px - tc * vx / ln) ** 2 + (pz - tc * vz / ln) ** 2
                    s = s0 + tc
                    if best is None or d2 < best[0]:
                        best = (d2, s)
                if best is None:
                    continue
                d2, s = best
                r = radius(s)
                lash = (abs(s - hs) <= Y['lash_half'] and abs(s - hs) > 1.5 and int(round(s - hs)) % Y['lash_every'] == 0) or \
                       (pk and abs(s - L1) <= 4 and int(round(s - L1)) % 4 == 0)
                for dy in range(-3, 4):
                    if d2 + dy * dy <= r * r:
                        cells[(x, yc + dy, z)] = C['lashing'] if lash else C['yard']

        def near(s, top=False):
            px, pz = axis(s)
            best = min((k for k in cells if k[1] == yc), key=lambda k: ((k[0] + 0.5 - px) ** 2 + (k[2] + 0.5 - pz) ** 2, k))
            if top:
                z = best[2]
                while (best[0], yc, z + 1) in cells:
                    z += 1
                best = (best[0], yc, z)
            return list(best)
        anchors = {'pivot': near(hs), 'sling': near(hs, True), 'fore': near(1.0), 'peak': near(Lc - 1.0)}
        for k_, s in enumerate(np.arange(8.0, Lc - 4, 8.0)):
            anchors['jackstay-%02d' % (k_ + 1)] = near(float(s), True)
        pv = anchors['pivot']
        zp = RB['masts'][key]['pivot_z'] + int(probe['pivot'].split(':')[1]) if probe.get('pivot', '').startswith(key + ':') else RB['masts'][key]['pivot_z']
        xm = rows[key]['x_step']
        yw = YC + Y['y_off']
        off = (xm - pv[0], yw - pv[1], zp - pv[2])                 # local cell + off = world cell
        lat[key] = {'cells': cells, 'size': [W_, 7, H_], 'anchors': anchors, 'len_m': Y['len_m'], 'tilt_deg': Y['tilt_deg'],
                    'hoist_frac': Y['hoist_frac'], 'sail': Y['sail'], 'off': off}
        place.append({'name': 'yard-%s-lateen' % key, 'mast': key, 'host': 'mast-' + key, 'work': 'claude-baghlah-01m-yard-%s-lateen' % key,
                      'at': [xm + 0.5, yw + 0.5, zp + 0.5], 'pivot': [pv[0] + 0.5, pv[1] + 0.5, pv[2] + 0.5], 'rotate': [0, 0, 0], 'scale': [1, 1, 1],
                      'meta': {'kind': 'yard', 'mast': key, 'yard': 'gaff', 'rig': 'lateen', 'sail': Y['sail'], 'length_m': Y['len_m'],
                               'length_ft': round(Y['len_m'] / 0.3048, 1), 'diameter_in': round((2 * int(Y['r_max']) + 1) * CELL / 0.0254, 1),
                               'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}})

    # ── readings ──
    R = {'probe': probe or None, 'heel_z': heel, 'truck_z': truck, 'skipped_on_ship': skipped, 'heel_slivers_trimmed': trimmed, 'jibboom': jib_meta, 'parts': {}, 'yards': {}}
    allp = {}
    for nm, cl in parts.items():
        G = np.zeros((480, 160, 400), bool)
        for (x, y, z) in cl:
            G[x, y, z] = True
        _, n6 = ndimage.label(G)
        xs = [k[0] for k in cl]; zs = [k[2] for k in cl]
        R['parts'][nm] = {'cells': len(cl), 'components_6': int(n6), 'x': [min(xs), max(xs)], 'z': [min(zs), max(zs)],
                          'mirror_diff': None if nm == 'jibboom' else sum(1 for (x, y, z), c in cl.items() if cl.get((x, 2 * YC - y, z)) != c),
                          'colours': {str(c): sum(1 for v in cl.values() if v == c) for c in sorted(set(cl.values()))}}
        for k in cl:
            allp[k] = allp.get(k, 0) + 1
    R['overlap_ship'] = sum(1 for k in allp if k in occ)
    R['overlap_between_parts'] = sum(1 for v in allp.values() if v > 1)
    # mast holes: every hole-disk cell on each deck's plank layer (deck surface − 1) must be mast
    holes = {}
    for key in ('main', 'mizzen'):
        xm = rows[key]['x_step']
        r2 = RB['masts'][key]['hole_r'] ** 2
        for dk in ('orlop', 'main', 'poop'):
            row = LY.deck_row(plan, dk)
            if not (row.get('x_from', -1) <= xm <= row.get('x_to', 999)):
                continue
            zpl = int(LY.deck_z(plan, dk, xm)) - 1
            if zpl <= heel[key]:
                continue
            disk = [(xm + dx, YC + dy, zpl) for dx in range(-5, 6) for dy in range(-5, 6) if dx * dx + dy * dy <= r2]
            holes['%s@%s' % (key, dk)] = {'plank_z': zpl, 'disk': len(disk), 'mast': sum(1 for k in disk if k in parts.get('mast-' + key, {})),
                                         'deck': sum(1 for k in disk if k in occ),
                                         'empty': sum(1 for k in disk if k not in occ and k not in parts.get('mast-' + key, {}))}
    R['mast_holes'] = holes
    # whole ship + this step: one component, no cavity, mirror (jib boom excluded: it is offset to starboard on purpose)
    G = np.zeros((480, 160, 400), bool)
    for (x, y, z) in occ:
        G[x, y, z] = True
    for nm, cl in parts.items():
        for (x, y, z) in cl:
            G[x, y, z] = True
    lab, ncomp = ndimage.label(G)
    sizes = np.bincount(lab.ravel())[1:]
    R['ship_with_rig'] = {'cells': int(G.sum()), 'components_6': int(ncomp), 'smallest_components': sorted(int(v) for v in sizes)[:3],
                          'cavities': int((ndimage.binary_fill_holes(G) & ~G).sum())}
    # yards: structure, world extent, clearances, shipcheck band, lateen swing, sail ratio (PT luff = half leech)
    world_ship = set(occ) | set(allp)
    for key, l_ in lat.items():
        cl = l_['cells']
        W_, _, H_ = l_['size']
        G = np.zeros((W_, 7, H_), bool)
        for (x, y, z) in cl:
            G[x, y, z] = True
        _, n6 = ndimage.label(G)
        ox, oy, oz = l_['off']
        wc = {(x + ox, y + oy, z + oz) for (x, y, z) in cl}
        an_w = {n: [a[0] + ox, a[1] + oy, a[2] + oz] for n, a in l_['anchors'].items()}
        mast = parts['mast-' + key]
        pz = an_w['pivot'][2]
        band = [k for k in mast if pz - 40 <= k[2] <= pz - 10 and abs(k[1] - YC) <= 4]
        # clearance: smallest distance (cells) from any yard cell to any ship / rig cell (all parts incl. both masts)
        pts = np.array(sorted(world_ship), float)
        yp = np.array(sorted(wc), float)
        from scipy.spatial import cKDTree
        dmin, _ = cKDTree(pts).query(yp)
        fore, peak, piv = an_w['fore'], an_w['peak'], an_w['pivot']
        xh = fore[0] - piv[0]
        R['yards'][key] = {'size': l_['size'], 'cells': len(cl), 'components_6': int(n6), 'anchors': len(l_['anchors']),
                           'overlap_world': sum(1 for k in wc if k in world_ship), 'min_gap_cells': round(float(dmin.min()) - 1, 2),
                           'world_x': [min(k[0] for k in wc), max(k[0] for k in wc)], 'world_z': [min(k[2] for k in wc), max(k[2] for k in wc)],
                           'world_y': [min(k[1] for k in wc), max(k[1] for k in wc)],
                           'pivot_world': piv, 'fore_world': fore, 'peak_world': peak,
                           'mast_cells_in_shipcheck_band': len(band), 'band_z': [pz - 40, pz - 10],
                           'lateen_swing_deg': round(math.degrees(math.asin(min(1.0, 25.0 / xh))), 1) if xh > 0 else None}
    # PT: the main sail's luff (yard fore end → stem head) is half its leech (peak → clew 4.5 m before the poop)
    sh = plan['paris']['stem_head']
    clew = (plan['masts']['sails']['main_foot_to_x'], plan['readings_at']['rail_z'] + 3)
    f, p = R['yards']['main']['fore_world'], R['yards']['main']['peak_world']
    luff = math.hypot(f[0] - sh[0], f[2] - sh[1])
    leech = math.hypot(p[0] - clew[0], p[2] - clew[1])
    R['main_sail_check'] = {'tack': sh, 'clew': list(clew), 'luff_m': round(luff * CELL, 2), 'leech_m': round(leech * CELL, 2),
                            'leech_over_luff': round(leech / luff, 2), 'PT': 2.0}
    R['problems'] = (R['overlap_ship'] + R['overlap_between_parts'] + sum(v['empty'] for v in holes.values())
                     + sum(1 for v in R['parts'].values() if v['components_6'] != 1)
                     + (R['ship_with_rig']['components_6'] != 1) + R['ship_with_rig']['cavities']
                     + sum((v['components_6'] != 1) + v['overlap_world'] + (v['mast_cells_in_shipcheck_band'] == 0) for v in R['yards'].values())
                     + sum(v.get('other', 0) for v in skipped.values())
                     + sum(v.get('hull', 0) for k, v in skipped.items() if k not in ('mast-main', 'mast-mizzen')))
    if probe:
        print(json.dumps({k: R[k] for k in ('probe', 'mast_holes', 'problems')} | {'yards': {k: {kk: v[kk] for kk in ('pivot_world', 'band_z', 'mast_cells_in_shipcheck_band', 'min_gap_cells')} for k, v in R['yards'].items()}}, ensure_ascii=False))
        return

    # ── write ──
    def dump(path, cl, head):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(head)
            for (x, y, z), c in sorted(cl.items()):
                fh.write('%d,%d,%d,%d\n' % (x, y, z, c))
        return hashlib.sha256(open(path, 'rb').read()).hexdigest()

    sha = {}
    for nm, fn in (('mast-main', 'main'), ('mast-mizzen', 'mizzen'), ('jibboom', 'jibboom'), ('cable-beam', 'cable_beam')):
        sha['masts/' + fn] = dump(os.path.join(design, 'masks', 'masts', fn + '.vox.txt'), parts[nm], '# Star (al-Najm) step 7: %s (at 0,0,0)\n' % nm)
    for key, l_ in lat.items():
        sha['yards/lateen-' + key] = dump(os.path.join(design, 'masks', 'yards', 'lateen-%s.vox.txt' % key), l_['cells'],
                                          '# Star (al-Najm) step 7: %s lateen yard (frame-local %s)\n' % (key, l_['size']))
    R['sha256'] = sha
    with open(os.path.join(design, 'yards_lateen.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({k: {kk: v[kk] for kk in ('size', 'anchors', 'len_m', 'tilt_deg', 'hoist_frac', 'sail')} for k, v in lat.items()}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'yards_placement.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(place, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)

    # ── sheet 05: side elevation (whole ship), bow plan view, masthead detail ──
    sc = 2
    W, H = 480 * sc + 80, 400 * sc + 520
    img = Image.new('RGB', (W, H), (250, 248, 240))
    d = ImageDraw.Draw(img)
    d.text((40, 16), 'Star (al-Najm) sheet 05: masts, lateen yards, jib boom, cable beam (step 7, TASK-0019)', fill=(20, 20, 20), font=font(22))
    d.text((40, 46), '0.1 m/cell; side elevation = projection along y (far side hidden behind near); yards drawn unbraced (rotate 0); dashed = sail outline for step 8', fill=(60, 60, 60), font=font(14))
    oz = 70 + 400 * sc
    Xs = lambda x: 40 + x * sc
    Zs = lambda z: oz - z * sc
    side = {}
    for (x, y, z), c in occ.items():
        side[(x, z)] = (220, 205, 180)
    for nm, cl in parts.items():
        for (x, y, z), c in cl.items():
            side[(x, z)] = palette_rgb(c)
    for key, l_ in lat.items():
        ox, oy, oz_ = l_['off']
        for (x, y, z), c in l_['cells'].items():
            side[(x + ox, z + oz_)] = palette_rgb(c)
    for (x, z), rgb in side.items():
        d.rectangle([Xs(x), Zs(z + 1), Xs(x + 1) - 1, Zs(z) - 1], fill=rgb)
    d.line([Xs(0), Zs(plan['waterline']['z']), Xs(480), Zs(plan['waterline']['z'])], fill=(80, 120, 200), width=1)

    def dashed(p, q, col=(150, 60, 60)):
        n = int(math.hypot(q[0] - p[0], q[1] - p[1]) / 6) + 1
        for i in range(0, n, 2):
            a = (p[0] + (q[0] - p[0]) * i / n, p[1] + (q[1] - p[1]) * i / n)
            b = (p[0] + (q[0] - p[0]) * min(n, i + 1) / n, p[1] + (q[1] - p[1]) * min(n, i + 1) / n)
            d.line([Xs(a[0]), Zs(a[1]), Xs(b[0]), Zs(b[1])], fill=col, width=2)
    yf, yp_ = R['yards']['main']['fore_world'], R['yards']['main']['peak_world']
    for p_, q_ in ((yf, sh), (sh, clew), (clew, yp_)):
        dashed((p_[0], p_[-1]), (q_[0], q_[-1]))
    d.text((Xs(250), Zs(330)), 'main lateen 34 m, tilt 18 deg, hoist 47%%; luff %.1f m : leech %.1f m (PT 1:2, here 1:%.2f)' % (R['main_sail_check']['luff_m'], R['main_sail_check']['leech_m'], R['main_sail_check']['leech_over_luff']), fill=(120, 40, 40), font=font(14))
    d.text((Xs(10), Zs(262)), 'mizzen lateen 18 m, tilt 28 deg (starboard of its mast)', fill=(120, 40, 40), font=font(14))
    d.text((Xs(300), Zs(110)), 'jib boom %.2f deg, heel on cable beam x %d-%d' % (alpha, cb['x0'], cb['x1']), fill=(60, 60, 60), font=font(14))
    # bow plan view (x 280..420, y 50..110), scale 4
    s4, bx0, by0 = 4, 40, oz + 40
    d.text((bx0, by0 - 22), 'bow from above (x 280-420): jib boom y %d, stem head (white) y 77-83' % yj, fill=(20, 20, 20), font=font(15))
    top = {}
    for src, colfn in ((occ, lambda c: (205, 190, 165)), (parts.get('cable-beam', {}), palette_rgb), (parts.get('jibboom', {}), palette_rgb)):
        for (x, y, z), c in src.items():
            if 280 <= x < 420 and 50 <= y < 110 and z >= top.get((x, y), (-1,))[0]:
                top[(x, y)] = (z, colfn(c))
    for (x, y), (z, rgb) in top.items():
        if (x, y, z) in load_stem_head_cache(design):
            rgb = (240, 240, 240)
        X_, Y_ = bx0 + (x - 280) * s4, by0 + (y - 50) * s4
        d.rectangle([X_, Y_, X_ + s4 - 1, Y_ + s4 - 1], fill=rgb)
    # masthead detail (main), front view (y) and side view (x), scale 6
    s6, mx0, my0 = 6, 40 + 140 * 4 + 60, oz + 40
    d.text((mx0, my0 - 22), 'main masthead z 240-283: side | front', fill=(20, 20, 20), font=font(15))
    mm = parts['mast-main']
    ym = lat['main']
    yw = {(x + ym['off'][0], y + ym['off'][1], z + ym['off'][2]): c for (x, y, z), c in ym['cells'].items()}
    for view, base in (('x', mx0), ('y', mx0 + 30 * s6 + 30)):
        for src in (mm, yw):
            for (x, y, z), c in src.items():
                if 240 <= z <= 284:
                    h = (x - 176) if view == 'x' else (y - 66)
                    if 0 <= h < 30:
                        d.rectangle([base + h * s6, my0 + (284 - z) * s6, base + h * s6 + s6 - 1, my0 + (284 - z) * s6 + s6 - 1], fill=palette_rgb(c))
    img.save(os.path.join(design, 'sheet05_masts_v1.png'), optimize=False)
    print(json.dumps({k: R[k] for k in ('heel_z', 'truck_z', 'jibboom', 'overlap_ship', 'overlap_between_parts', 'mast_holes', 'ship_with_rig', 'main_sail_check', 'problems')}, ensure_ascii=False))
    print(json.dumps(R['yards'], ensure_ascii=False))
    print(json.dumps(R['parts'], ensure_ascii=False))


_SH = {}


def load_stem_head_cache(design):
    if 'v' not in _SH:
        _SH['v'] = set(load(os.path.join(design, 'masks', 'deco', 'stem_head.vox.txt')))
    return _SH['v']


if __name__ == '__main__':
    main()
