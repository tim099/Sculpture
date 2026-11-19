# Source: pinnacle-patache-01m/design/draft_guns.py + gunsim.py (San Roman, TASK-0970: the same two components, the 4l
#   carriage gun and the pierrier) -- rewritten for the Star (TASK-0019 step 9).
# Star (al-Najm) new sheet 07: guns. Every gun is an external model hung on the deck sub-work it stands on (Ship_Guns 4.2).
#   Broadside 4l: from outside the hull, back along the gun axis in 0.5-cell steps until every cell centre and its 8 corners
#     (inset 0.2) are clear of every solid; then the muzzle must be outside the hull, the muzzle cell empty, the carriage
#     standing on the deck. P side = mirror=y, searched on its own.
#   Swivels (pierrier, mount=turret): on top of the rail (the highest solid of that station, middle of its width).
#     The barrel and its fork (the split -mount, Ship_Guns 4.2.1) are measured together; turret ⇒ the whole arc is measured
#     every sweep_step_deg (Ship_Turrets 4.5).
#   Differences from San Roman: solids are the design lists of every earlier step (draft_masts.ship_cells + masts + yards +
#     rigging parts), not a CLI export ⇒ the run needs no server and a rerun after stamping is byte-identical; component
#     cells are cached in masks/guns_src (exported once, sha in verify); added readings: default recoil, the arc sweep,
#     the muzzle ray, straight-rope clearance, ladder points, bounding boxes.
#   Outputs: guns_placement.json, verify_guns.json, sheet07_guns_v1.png
#   Usage: python -X utf8 draft_guns.py <design> [--probe=push=<gun name>:<cells>] [--probe=scale=<type>:<scale>]
#     reverse controls, nothing written: push one gun outward (its collision samples must show up); place a type at
#     another scale (prints the full readings at that scale).
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout as LY
from draft_lines import font, palette_rgb
from draft_masts import ship_cells, load


def r3(v):
    return [round(float(c), 3) for c in v]


def inset_offsets(inset):
    a, b = inset, 1.0 - inset
    return np.array([[0.5, 0.5, 0.5]] + [[(a, b)[k & 1], (a, b)[(k >> 1) & 1], (a, b)[(k >> 2) & 1]] for k in range(8)])


def load_src(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :3]


class Gun:
    """Model transform (CLI work model; same as San Roman gunsim): p = at + Rz(phi) . M (v - pivot) . scale, M = mirror y."""

    def __init__(s, key, t, design, inset):
        s.key, s.t = key, t
        s.scale = float(t['scale'])
        s.pivot = np.array(t['pivot'], float)
        G = os.path.join(design, 'masks', 'guns_src')
        s.barrel = load_src(os.path.join(G, t['work'] + '.vox.txt')).astype(float)
        s.mount = load_src(os.path.join(G, t['mount_work'] + '.vox.txt')).astype(float) if t.get('mount_work') else np.zeros((0, 3))
        s.cells = np.concatenate([s.barrel, s.mount])
        works = os.path.dirname(os.path.dirname(design))
        A = json.load(open(os.path.join(works, t['work'], 'anchors.json'), encoding='utf-8'))['anchors']
        s.anchors = {a['name']: np.array(a['at'], float) + 0.5 for a in A}
        off = inset_offsets(inset)
        s.samples = (s.cells[:, None, :] + off[None]).reshape(-1, 3)
        s.barrel_samples = (s.barrel[:, None, :] + off[None]).reshape(-1, 3)
        s.centers = s.cells + 0.5
        s.bottom = s.cells[s.cells[:, 2] == s.cells[:, 2].min()] + 0.5
        s.lo, s.hi = s.cells.min(0), s.cells.max(0) + 1
        s.barrel_len = float(np.linalg.norm(s.anchors['muzzle'] - s.anchors['breech']) * s.scale)

    def world(s, P, at, phi, mirror):
        q = (np.asarray(P, float) - s.pivot) * s.scale
        if mirror:
            q = q * np.array([1.0, -1.0, 1.0])
        c, sn = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        x = q[..., 0] * c - q[..., 1] * sn
        y = q[..., 0] * sn + q[..., 1] * c
        return np.stack([x + at[0], y + at[1], q[..., 2] + at[2]], -1)

    def axis(s, phi, mirror):
        """Unit vector breech -> muzzle in world (3D)."""
        a = s.world(s.anchors['breech'][None], (0, 0, 0), phi, mirror)[0]
        b = s.world(s.anchors['muzzle'][None], (0, 0, 0), phi, mirror)[0]
        return (b - a) / np.linalg.norm(b - a)

    def direction(s, phi, mirror):
        a = s.world(s.pivot[None], (0, 0, 0), phi, mirror)[0]
        b = s.world((s.pivot + [0, 1.0, 0])[None], (0, 0, 0), phi, mirror)[0]
        d = (b - a)[:2]
        return d / np.linalg.norm(d)

    def bbox(s, at, phi, mirror):
        corners = np.array([[(s.lo[0], s.hi[0])[k & 1], (s.lo[1], s.hi[1])[(k >> 1) & 1], (s.lo[2], s.hi[2])[(k >> 2) & 1]] for k in range(8)], float)
        W = s.world(corners, at, phi, mirror)
        return W.min(0), W.max(0)


class Grid:
    def __init__(s, cells):
        s.G = np.zeros((480, 160, 400), bool)
        c = np.array(list(cells), int)
        s.G[c[:, 0], c[:, 1], c[:, 2]] = True

    def hit(s, P):
        i = np.floor(np.asarray(P, float)).astype(int)
        ok = np.all((i >= 0) & (i < np.array(s.G.shape)), -1)
        out = np.ones(i.shape[:-1], bool)                    # outside the frame counts as solid (must not leave it)
        j = i[ok]
        out[ok] = s.G[j[:, 0], j[:, 1], j[:, 2]]
        return out


def seg_points_dist(a, b, P):
    d = b - a
    t = np.clip(((P - a) @ d) / max(d @ d, 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * d), axis=1)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    YC = plan['space']['yc']
    GB = plan['guns_build']
    S = GB['search']
    M = os.path.join(design, 'masks')
    if 'scale' in probe:
        k, v = probe['scale'].split(':')
        GB['types'][k]['scale'] = float(v)

    # ── every solid placed before step 9 (design lists) ──
    occ = ship_cells(design, plan)
    hull = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
    hull.update(load(os.path.join(M, 'step6', 'hull_recolor.vox.txt')))
    hull.update(load(os.path.join(M, 'step6', 'hull_add.vox.txt')))
    for f in ('main', 'mizzen', 'jibboom', 'cable_beam'):
        occ.update(load(os.path.join(M, 'masts', f + '.vox.txt')))
    for f in ('rings', 'stern_spars', 'halyard_bitt'):
        occ.update(load(os.path.join(M, 'rigging', f + '.vox.txt')))
    YP = {y['mast']: y for y in json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))}
    for key in ('main', 'mizzen'):
        off = [int(round(YP[key]['at'][i] - YP[key]['pivot'][i])) for i in range(3)]
        for (x, y, z), c in load(os.path.join(M, 'yards', 'lateen-%s.vox.txt' % key)).items():
            occ[(x + off[0], y + off[1], z + off[2])] = c
    G = Grid(occ)
    decks = {}
    for k in GB['deck_works']:
        top = {}
        for (x, y, z) in load(os.path.join(M, 'decks', k + '.vox.txt')):
            if z + 1 > top.get((x, y), -1):
                top[(x, y)] = z + 1
        decks[k] = top
    guns = {k: Gun(k, t, design, S['inset']) for k, t in GB['types'].items()}
    RP = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
    ropes = [(r['name'], np.array(RP['points'][r['from']], float), np.array(RP['points'][r['to']], float), r['thickness'] / 2.0)
             for r in RP['ropes'] if r['from'] in RP['points'] and r['to'] in RP['points']]
    LP = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))

    hull_by_xz = {}
    for (x, y, z) in hull:
        lo, hi = hull_by_xz.get((x, z), (999, -1))
        hull_by_xz[(x, z)] = (min(lo, y), max(hi, y))

    def hull_outer(x, z, side):
        lo, hi = hull_by_xz[(x, z)]
        return (hi + 1) if side > 0 else lo

    def deck_top(dk, pts):
        zs = [decks[dk][p] for p in pts if p in decks[dk]]
        return max(zs) if zs else None

    def check(g, at, phi, mirror):
        tip = g.world(g.anchors['muzzle'][None], at, phi, mirror)[0]
        bot = g.world(g.bottom, at, phi, mirror)
        below = bot.copy()
        below[:, 2] -= 1.0
        return tip, (not G.hit(tip[None])[0]), float(G.hit(below).mean())

    def place(g, base_xy, d_out, phi, mirror, zd, outer, side):
        best = None
        d_side = np.array([d_out[1], -d_out[0]])
        for dz in S['dz']:
            for off in S['dx']:
                for k in range(int(S['back_max'] / S['step']) + 1):
                    back = k * S['step']
                    b = np.array(base_xy, float) + d_side * off - d_out * back
                    at = (float(b[0]), float(b[1]), float(zd + dz))
                    if G.hit(g.world(g.samples, at, phi, mirror)).any():
                        continue
                    tip, free, sup = check(g, at, phi, mirror)
                    beyond = (tip[1] - outer) * side
                    ok = bool(beyond > 0 and free and sup >= GB['support_min'])
                    cand = {'at': r3(at), 'phi': phi, 'back': back, 'off': off, 'dz': dz, 'muzzle_beyond': round(float(beyond), 2),
                            'muzzle_free': free, 'support': round(sup, 3), 'axis_z': round(float(tip[2]), 2), 'ok': ok}
                    key = (not ok, dz, back, abs(off))
                    if best is None or key < best[0]:
                        best = (key, cand)
                    break
        return best

    rows = []
    # ── broadside 4l (main deck ports) ──
    for p in LY.ports(plan):
        g = guns[p['gun']]
        xc = (p['x0'] + p['x1'] + 1) / 2.0
        zm = (p['z0'] + p['z1']) // 2
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            outs = [hull_outer(x, zm, side) for x in (p['x0'] - 2, p['x1'] + 2)]
            outer = max(outs) if side > 0 else min(outs)
            yin = [outer - side * d for d in (8, 14, 20, 26)]
            zd = deck_top(p['deck'], [(x, y) for x in (p['x0'], int(xc), p['x1']) for y in yin])
            b_ = place(g, (xc, outer), g.direction(0.0, mirror), 0.0, mirror, zd, outer, side)
            r = {'deck': p['deck'], 'port': p['i'], 'side': nm, 'type': p['gun'], 'swivel': False, 'outer': outer, 'deck_z': zd,
                 'opening': {'x': [p['x0'], p['x1']], 'z': [p['z0'], p['z1']]}}
            r.update(b_[1] if b_ else {'ok': False, 'at': None})
            rows.append(r)
    # ── swivels on the rail top ──
    SW = GB['swivels']
    g = guns[SW['type']]
    rail_cells = dict(hull)
    rail_cells.update(load(os.path.join(M, 'deco', 'quarter_rail.vox.txt')))     # the helm-deck rail (x 140 station)
    for row in SW['rows']:
        x = row['x']
        # station = top of the bulwark / rail on the starboard side (outer half only: masts and yards stand on the centre line)
        zt = max(z for (xx, y, z) in rail_cells if xx == x and y > YC + 20)
        ys = sorted(y for (xx, y, z) in rail_cells if xx == x and z == zt and y > YC + 20)
        ym = (ys[0] + ys[-1]) / 2.0
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            y_at = (ym + 0.5) if side > 0 else (2 * YC + 1 - (ym + 0.5))
            at = (x + 0.5, y_at, float(zt + 1))
            hit = int(G.hit(g.world(g.samples, at, 0.0, mirror)).sum())
            tip, free, sup = check(g, at, 0.0, mirror)
            outer = (ys[-1] + 1) if side > 0 else (2 * YC - ys[-1])
            beyond = (tip[1] - outer) * side
            rows.append({'deck': row['deck'], 'port': 'sw%d' % x, 'side': nm, 'type': SW['type'], 'swivel': True, 'deck_z': deck_top(row['deck'], [(x, int(y_at) - side * d) for d in (3, 5, 8, 12)]),
                         'rail_z': zt, 'arc': row.get('arc', g.t['meta']['arc']), 'at': r3(at), 'phi': 0.0, 'back': 0.0, 'off': 0.0, 'dz': 0, 'muzzle_beyond': round(float(beyond), 2),
                         'muzzle_free': free, 'support': round(sup, 3), 'axis_z': round(float(tip[2]), 2), 'hit_samples': hit,
                         'ok': bool(hit == 0 and beyond > 0 and free)})
    # ── names ──
    cnt = {}
    for r in rows:
        if r['swivel']:
            cnt[('sw', r['side'])] = cnt.get(('sw', r['side']), 0) + 1
            r['name'] = '迴旋砲-%s%02d' % (r['side'], cnt[('sw', r['side'])])
        else:
            pre = GB['prefix'][r['deck']]
            cnt[(pre, r['side'])] = cnt.get((pre, r['side']), 0) + 1
            r['name'] = '砲%s-%s%02d' % (pre, r['side'], cnt[(pre, r['side'])])
    rows.sort(key=lambda r: (r['swivel'], r['side'], r['name']))
    fail = [[r['name'], r.get('opening'), r.get('deck_z')] for r in rows if r.get('at') is None]
    if fail:
        print(json.dumps({'placed_none': fail}, ensure_ascii=False))
        raise SystemExit('✗ %d guns found no clear position' % len(fail))

    def world_of(r, which='samples', phi=None, push=0.0, recoil=0.0):
        g = guns[r['type']]
        mir = r['side'] == 'P'
        ph = r['phi'] if phi is None else phi
        at = np.array(r['at'], float)
        if push:
            at[:2] += g.direction(ph, mir) * push
        if recoil:
            at -= g.axis(ph, mir) * recoil
        return g.world(getattr(g, which), at, ph, mir)

    if probe.get('push'):
        nm, d = probe['push'].rsplit(':', 1)
        rep = {}
        for r in rows:
            n = int(G.hit(world_of(r, push=float(d) if r['name'] == nm else 0.0)).sum())
            if n:
                rep[r['name']] = n
        print(json.dumps({'probe': probe, 'hit_samples_by_gun': rep}, ensure_ascii=False))
        return

    R = {'read': {'solid_cells': len(occ), 'hull_cells': len(hull),
                  'component_sha256': {f: hashlib.sha256(open(os.path.join(M, 'guns_src', f), 'rb').read()).hexdigest()[:16] for f in sorted(os.listdir(os.path.join(M, 'guns_src')))}},
         'guns': len(rows), 'by_type': {}, 'not_ok': [[r['name'], r['muzzle_beyond'], r['muzzle_free'], r['support']] for r in rows if not r['ok']]}
    for r in rows:
        R['by_type'][r['type']] = R['by_type'].get(r['type'], 0) + 1
    bs = [r for r in rows if not r['swivel']]
    for f in ('back', 'off', 'dz', 'muzzle_beyond', 'support', 'axis_z'):
        R['broadside_' + f] = [min(r[f] for r in bs), max(r[f] for r in bs)]
    # the barrel in the port: clearance to the sill and the lintel at the hull wall
    gap = []
    for r in bs:
        g = guns['4l']
        P = world_of(r, 'barrel_samples')
        o = r['opening']
        side = 1 if r['side'] == 'S' else -1
        u = (P[:, 1] - r['outer']) * side                                       # 0 = outer face, -3 = inner face of the wall
        inwall = P[(P[:, 0] >= o['x'][0]) & (P[:, 0] <= o['x'][1] + 1) & (u >= -3) & (u <= 0)]
        gap.append([round(float(inwall[:, 2].min() - o['z'][0]), 2), round(float(o['z'][1] + 1 - inwall[:, 2].max()), 2)] if len(inwall) else None)
    R['barrel_in_port_sill_lintel_gap'] = [min(g_[0] for g_ in gap if g_), min(g_[1] for g_ in gap if g_)] if any(gap) else None
    R['barrel_not_in_port'] = [r['name'] for r, g_ in zip(bs, gap) if not g_]
    # gun vs gun (cell centres in one cell)
    occg, clash = {}, []
    for r in rows:
        for c in set(map(tuple, np.floor(world_of(r, 'centers')).astype(int).tolist())):
            if c in occg and occg[c] != r['name']:
                clash.append([r['name'], occg[c]])
                break
            occg[c] = r['name']
    R['gun_gun_clash'] = clash
    # symmetry: P at.y = 2·YC + 1 − S at.y, same x / z, phi opposite
    by = {(str(r['port']), r['side']): r for r in rows}
    asym = []
    for (pt, sd), r in by.items():
        q = by.get((pt, 'P'))
        if sd == 'S' and (q is None or abs(r['at'][0] - q['at'][0]) > 1e-6 or abs(2 * YC + 1 - r['at'][1] - q['at'][1]) > 1e-6 or r['at'][2] != q['at'][2] or r['phi'] != -q['phi']):
            asym.append([r['name'], q and q['name']])
    R['asymmetric_pairs'] = asym
    # default recoil (Ship_Guns 4.2): barrel length x k, at least min; swivels recoil the barrel only
    RC = GB['recoil']
    rec = {}
    for r in rows:
        g = guns[r['type']]
        dist = max(RC['min'], g.barrel_len * RC['k'])
        P = world_of(r, 'barrel_samples' if r['swivel'] else 'samples', recoil=dist)
        rec[r['name']] = [round(dist, 2), int(G.hit(P).sum())]
        r['recoil_cells'] = round(dist, 2)
    R['recoil_hit_samples'] = {k: v for k, v in rec.items() if v[1]}
    R['recoil_cells'] = sorted({v[0] for v in rec.values()})
    # the arc sweep of the swivels (turret: continuous)
    def arc_angles(r):
        a0, a1 = [float(a) for a in r['arc'].split(',')]
        return np.arange(a0, a1 + 1e-9, GB['sweep_step_deg'])
    angs = arc_angles({'arc': GB['types']['pierrier']['meta']['arc']})
    sweep = {}
    for r in rows:
        if not r['swivel']:
            continue
        hits = {}
        for a in arc_angles(r):
            n = int(G.hit(world_of(r, phi=float(a))).sum())
            if n:
                hits[str(int(a))] = n
        sweep[r['name']] = hits
    R['swivel_sweep_angles'] = [int(angs[0]), int(angs[-1]), len(angs)]
    R['swivel_sweep_hits'] = {k: v for k, v in sweep.items() if v}
    # muzzle ray (the shot must not run into the own ship): broadside at phi 0, swivels over the arc
    ray = {}
    for r in rows:
        g = guns[r['type']]
        mir = r['side'] == 'P'
        worst = None
        for a in (arc_angles(r) if r['swivel'] else [r['phi']]):
            mz = g.world(g.anchors['muzzle'][None], r['at'], float(a), mir)[0]
            d = g.axis(float(a), mir)
            t = np.arange(0.5, GB['ray_len'] + 1e-9, 0.25)
            Q = mz[None] + t[:, None] * d[None]
            inside = np.all((Q >= 0) & (Q < np.array(G.G.shape)), -1)          # past the frame = open sea, not the ship
            hit = G.hit(Q) & inside
            if hit.any():
                first = float(t[hit.argmax()])
                if worst is None or first < worst[1]:
                    worst = [int(a), round(first, 2)]
        if worst:
            ray[r['name']] = worst
    R['muzzle_ray_hits'] = ray
    # straight-rope clearance (ropes are not solid in the game, this is about looking right): over the arc for swivels
    rc = {}
    for r in rows:
        best = None
        for a in (arc_angles(r) if r['swivel'] else [r['phi']]):
            P = world_of(r, 'centers', phi=float(a))
            lo, hi = P.min(0) - 3, P.max(0) + 3
            for nm, a_, b_, rad in ropes:
                if np.any(np.maximum(a_, b_) < lo) or np.any(np.minimum(a_, b_) > hi):
                    continue
                dmin = float(seg_points_dist(a_, b_, P).min()) - 0.5 - rad
                if best is None or dmin < best[0]:
                    best = [round(dmin, 2), nm, int(a)]
        rc[r['name']] = best
    R['rope_clearance_min'] = min((v for v in rc.values() if v), key=lambda v: v[0]) if any(rc.values()) else None
    R['rope_clearance_below_0'] = {k: v for k, v in rc.items() if v and v[0] < 0}
    # ladder points and the gun boxes (crew stand around the box; Ship_Turrets 4.6 step 5)
    lad = []
    for r in rows:
        g = guns[r['type']]
        lo, hi = g.bbox(r['at'], r['phi'], r['side'] == 'P')
        for nm, L in LP.items():
            for pn, p in L['points'].items():
                q = np.array(p, float) + 0.5
                if np.all(q > lo - 1) and np.all(q < hi + 1):
                    lad.append([r['name'], nm, pn])
    R['ladder_points_in_gun_box'] = lad
    # height of the swivel axis above the deck the crew stands on
    R['swivel_arcs'] = {r['name']: r['arc'] for r in rows if r['swivel']}
    R['swivel_axis_above_deck_m'] = {r['name']: round((r['axis_z'] - r['deck_z']) * 0.1, 2) for r in rows if r['swivel'] and r['side'] == 'S'}
    for r in rows:
        lo, hi = guns[r['type']].bbox(r['at'], r['phi'], r['side'] == 'P')
        r['bbox'] = [r3(lo), r3(hi)]
    if probe:                                                                   # --probe=scale: full readings, nothing written
        print(json.dumps({'probe': probe, 'readings': R}, ensure_ascii=False))
        return
    json.dump({'note': 'draft_guns.py: at = model at (pivot lands there), phi = rotate z, P = mirror y', 'rows': rows},
              open(os.path.join(design, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(R, open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)

    # ── sheet 07: plan view of the main deck guns + swivel arcs; side view ──
    sc = 3
    W_, H_ = 40 + 480 * sc + 40, 60 + 160 * sc + 40 + 130 * sc + 40
    img = Image.new('RGB', (W_, H_), (250, 248, 242))
    d = ImageDraw.Draw(img)
    d.text((40, 15), 'Star (al-Najm) sheet 07: guns -- 22 x 4l (scale 0.443) on the main deck, 8 pierrier swivels on the poop / helm rail', fill=(20, 20, 20), font=font(16))
    oy = 50
    Xs = lambda x: 40 + x * sc
    top = {}
    for (x, y, z), c in occ.items():
        if z >= top.get((x, y), (-1,))[0]:
            top[(x, y)] = (z, c)
    for (x, y), (z, c) in top.items():
        rgb = palette_rgb(c)
        d.rectangle([Xs(x), oy + y * sc, Xs(x + 1) - 1, oy + (y + 1) * sc - 1], fill=tuple(int(v * 0.45 + 140) for v in rgb))
    for r in rows:
        col = (30, 30, 30) if not r['swivel'] else (170, 30, 40)
        for p in world_of(r, 'centers'):
            d.point((Xs(p[0]), oy + p[1] * sc), fill=col)
        if r['swivel']:
            g = guns[r['type']]
            for a in arc_angles(r):
                mz = g.world(g.anchors['muzzle'][None], r['at'], float(a), r['side'] == 'P')[0]
                d.point((Xs(mz[0]), oy + mz[1] * sc), fill=(220, 120, 0))
    oz = oy + 160 * sc + 40 + 130 * sc
    Zs = lambda z: oz - (z - 0) * sc
    side_ = {}
    for (x, y, z), c in occ.items():
        if y <= YC:
            side_[(x, z)] = c
    for (x, z), c in side_.items():
        rgb = palette_rgb(c)
        d.rectangle([Xs(x), Zs(z + 1), Xs(x + 1) - 1, Zs(z) - 1], fill=tuple(int(v * 0.45 + 140) for v in rgb))
    for r in rows:
        if r['side'] != 'P':
            continue
        for p in world_of(r, 'centers'):
            d.point((Xs(p[0]), Zs(p[2])), fill=(30, 30, 30) if not r['swivel'] else (170, 30, 40))
    d.text((40, oz - 130 * sc - 25), 'port side (z 0 .. 130)', fill=(20, 20, 20), font=font(14))
    img.save(os.path.join(design, 'sheet07_guns_v1.png'), optimize=False)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
