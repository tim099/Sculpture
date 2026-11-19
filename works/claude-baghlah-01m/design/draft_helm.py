# Source: calli-cosecha-01m/design/draft_rudder_anchor.py (Harvest, TASK-0619: rudder along the sternpost with a bevelled
#   fore edge, hinge on the post's aft line, stock-top; anchors placed by a search) -- rewritten for the Star (TASK-0019 step 11).
# Star (al-Najm) new sheet 09: rudder, stock, tiller, stem rollers, anchors (Ship_Helm 9.8 / 9.8.1, Ship_Game 9 rudder / anchor).
#   PT (Paris 1843 v.1, Baggala): "la plupart n'emploient qu'une tres-longue barre; la fusee du gouvernail, toujours droite,
#     penetre dans le navire en percant la voute, qui est basse et oblique"; no cathead, "a la mer il faut mettre les ancres
#     sur le pont"; "un rouleau place dans la partie saillante de l'etrave ... et souvent un second, g, est cloue du cote
#     oppose" (P2 fig. 10); anchors and cable "tres-petit".
#   Rudder (model kind=rudder, its own sub-work at world coordinates, at = pivot = hinge):
#     blade z 0..z_top aft of the sternpost's aft line (lines.x_post), width from P2 fig. 7 (after edge 7 deg), sides bevelled
#     at the fore edge (turns without sweeping the post), never forward of the hull at that (y, z); three iron straps (P2);
#     stock: cells within r of the hinge axis from z0 up through the counter (PT), the stern cabin and the poop deck to the head;
#     hinge on the post's aft line at z 0, axis along the post rake.
#   Trunk: every earlier cell within trunk_r of the axis between the stock's foot and the poop plank is carved (rudder port in
#     the counter, hole in the poop deck) -- carve lists per work, applied with carvevox (masks/step11/*_carve.vox.txt).
#   Collar (helm-fittings sub-work, linked): a ring on the poop deck round the hole; stock-top must find ship cells within 8.
#   Tiller (model kind=tiller, own sub-work, spin about the rudder's hinge / axis): from the stock head forward on the poop
#     deck's centre line to x_tip (the mizzen at x 107-111 stops it; the kevel and the binnacle moved for it, plan.rigging /
#     plan.gear_build), tapering, a grip at the end.
#   Stem rollers (stem-rollers sub-work, linked): a cheek on each side of the stem on the bow rail with a roller in the slot
#     next to the stem; hull anchors hawse-S / hawse-P on the roller tops. Position found by a search (supported, free,
#     clear of ropes) -- the main sail's tack is tied at the stem head.
#   Anchors: the shared grapnel (kotoko-fusta-01m-anchor-grapnel, 0.05 m) x scale, standing on the fore well deck (at sea,
#     PT), S + P mirrored (P mirror=y), position found by a search; cable lines hawse -> cable beam measured.
#   Inputs: plan.json (helm_build), the design lists of every earlier step (no server), guns_placement.json, gear_placement.json,
#     rigging_plan.json, masks/gear_src, masks/helm_src (grapnel cells, exported once, sha in verify).
#   Outputs: masks/helm/{rudder,tiller,fittings,rollers}.vox.txt (world, at 0,0,0), masks/step11/{hull,poop,carving}_carve.vox.txt,
#     helm_placement.json, verify_helm.json, sheet09_helm_v1.png
#   Usage: python -X utf8 draft_helm.py <design> [--probe=<kind>=<arg>]   (nothing written with a probe)
#     --probe=nofit=1        skip the blade fit (fore edge at the post line like v1): the rudder sweep must hit the post
#     --probe=tip=<x>        another tiller tip: the tiller sweep must hit the binnacle / kevel when it is too long
#     --probe=noswept=1      cut only the round trunk (not what the stock sweeps): the rudder sweep must hit the trunk edges
#     --probe=anchor_dx=<n>  push both anchors n cells in x after the search: collisions must show up
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
from draft_lines import font, palette_rgb
from draft_masts import ship_cells, load
from draft_guns import Gun
from draft_gear import Model, corners

SHAPE = (480, 160, 400)


def r3(v):
    return [round(float(c), 3) for c in v]


def rodrigues(P, origin, axis, deg):
    """Rotate points P about the line (origin, axis) by deg (right hand)."""
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    t = math.radians(deg)
    v = np.asarray(P, float) - origin
    c, s = math.cos(t), math.sin(t)
    return origin + v * c + np.cross(k, v) * s + np.outer(v @ k, k) * (1 - c)


def seg_dist(a, b, P):
    d = b - a
    t = np.clip(((P - a) @ d) / max(d @ d, 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * d), axis=1)


class Grapnel(Model):
    """Model with an optional y mirror (CLI: mirror=y flips the source about the pivot before the rotation)."""

    def __init__(s, cells, pivot, scale, rot, mirror):
        s.mirror = mirror
        Model.__init__(s, cells, pivot, scale, rot)

    def world(s, P, at):
        q = (np.asarray(P, float) - s.pivot) * s.scale
        if s.mirror:
            q = q * np.array([1.0, -1.0, 1.0])
        c, sn = math.cos(math.radians(s.rot)), math.sin(math.radians(s.rot))
        return np.stack([q[..., 0] * c - q[..., 1] * sn + at[0], q[..., 0] * sn + q[..., 1] * c + at[1], q[..., 2] + at[2]], -1)


def grid_of(cells):
    G = np.zeros(SHAPE, bool)
    c = np.array(list(cells), int)
    if len(c):
        G[c[:, 0], c[:, 1], c[:, 2]] = True
    return G


def hit(P, G):
    i = np.floor(np.asarray(P, float)).astype(int)
    ok = np.all((i >= 0) & (i < np.array(G.shape)), -1)
    out = np.ones(i.shape[:-1], bool)
    j = i[ok]
    out[ok] = G[j[:, 0], j[:, 1], j[:, 2]]
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    YC = plan['space']['yc']
    L = HL.Lines(plan)
    HB = plan['helm_build']
    RU, ST, TI, FI, RO, AN = HB['rudder'], HB['stock'], HB['tiller'], HB['fittings'], HB['rollers'], HB['anchors']
    if 'tip' in probe:
        TI['x_tip'] = int(probe['tip'])
    M = os.path.join(design, 'masks')

    # ── every solid placed before step 11, labelled by the work it lives in (design lists; same set as draft_gear.py + gear) ──
    src = {}

    def add(tag, path, off=(0, 0, 0)):
        for (x, y, z), c in load(path).items():
            src[(x + off[0], y + off[1], z + off[2])] = (tag, c)
    hull = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
    hull.update(load(os.path.join(M, 'step6', 'hull_recolor.vox.txt')))
    hull.update(load(os.path.join(M, 'step6', 'hull_add.vox.txt')))
    occ = ship_cells(design, plan)
    for k, c in occ.items():
        src[k] = ('other', c)
    for k, c in hull.items():
        src[k] = ('hull', c)
    for g in plan['decks_build']['groups']:
        add('deck-' + g['key'], os.path.join(M, 'decks', g['key'] + '.vox.txt'))
        add('ladders-' + g['key'], os.path.join(M, 'ladders', g['key'] + '.vox.txt'))
    for f, t in (('stern_glass', 'stern-glass'), ('quarter_rail', 'quarter-rail'), ('stern_carving', 'stern-carving'), ('stem_head', 'stem-head')):
        add(t, os.path.join(M, 'deco', f + '.vox.txt'))
    for f in ('main', 'mizzen', 'jibboom', 'cable_beam'):
        add({'main': 'mast-main', 'mizzen': 'mast-mizzen', 'jibboom': 'jibboom', 'cable_beam': 'cable-beam'}[f], os.path.join(M, 'masts', f + '.vox.txt'))
    for f, t in (('rings', 'rings'), ('stern_spars', 'stern-spars'), ('halyard_bitt', 'halyard-bitt')):
        add(t, os.path.join(M, 'rigging', f + '.vox.txt'))
    add('gunfittings', os.path.join(M, 'gunfittings', 'gunfittings.vox.txt'))
    YP = {y['mast']: y for y in json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))}
    for key in ('main', 'mizzen'):
        off = [int(round(YP[key]['at'][i] - YP[key]['pivot'][i])) for i in range(3)]
        add('yard-' + key, os.path.join(M, 'yards', 'lateen-%s.vox.txt' % key), off)
    for f in ('magazine', 'skids'):
        add({'magazine': 'magazine', 'skids': 'boat-skids'}[f], os.path.join(M, 'gear', f + '.vox.txt'))
    G0 = grid_of(src)

    # models before step 11 (guns + their forks, step-10 gear) as exact cell obstacles
    GBG = plan['guns_build']
    gun_t = {k: Gun(k, t, design, 0.2) for k, t in GBG['types'].items()}
    MO = np.zeros(SHAPE, bool)
    model_boxes = []
    for r in json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']:
        g = gun_t[r['type']]
        i = np.floor(g.world(g.centers, r['at'], r['phi'], r['side'] == 'P')).astype(int)
        MO[i[:, 0], i[:, 1], i[:, 2]] = True
        model_boxes.append((r['name'], r['bbox']))
    GP = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))
    hearth_src = np.array(sorted(load(os.path.join(M, 'gear', 'hearth.vox.txt'))), float)
    gear_models = {}
    for r in GP['models']:
        cells = hearth_src if r['work'].endswith('-hearth') else \
            np.loadtxt(os.path.join(M, 'gear_src', r['work'] + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :3].astype(float)
        g = Model(cells, r['pivot'], r['scale'], r['rotate'])
        i = np.floor(g.world(g.centers, r['at'])).astype(int)
        MO[i[:, 0], i[:, 1], i[:, 2]] = True
        gear_models[r['name']] = (g, r)
        model_boxes.append((r['name'], r['bbox']))
    RP = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
    ropes = [(rp['name'], np.array(RP['points'][rp['from']], float), np.array(RP['points'][rp['to']], float), rp['thickness'] / 2.0)
             for rp in RP['ropes'] if rp['from'] in RP['points'] and rp['to'] in RP['points']]

    def rope_clear(P):
        best = (1e9, None)
        for nm, a, b, rad in ropes:
            if min(a[0], b[0]) - 30 > P[:, 0].max() or max(a[0], b[0]) + 30 < P[:, 0].min():
                continue
            d = float(seg_dist(a, b, P).min()) - rad
            if d < best[0]:
                best = (d, nm)
        return round(best[0], 2), best[1]

    V = {'read': {'solid_cells': len(src), 'model_cells': int(MO.sum())}}

    # ── rudder: hinge on the post's aft line, axis along the rake ──
    rake = L.sp_rake
    axis = np.array([-math.sin(rake), 0.0, math.cos(rake)])
    hinge = np.array([float(L.x_post(0.0)), YC + 0.5, 0.0])

    def axis_x(z):
        return float(L.x_post(z))
    minx = {}
    for (x, y, z) in hull:
        if x < minx.get((y, z), 10 ** 9):
            minx[(y, z)] = x
    C = RU['colors']
    zs_w, ws = zip(*RU['width'])
    ARC = np.arange(-RU['max_deg'], RU['max_deg'] + 0.01, RU['arc_step'])

    def clears(cell, G):
        """True if the cell's samples (centre + corners inset 0.2) stay out of G over the whole arc."""
        P = corners(np.array([cell], float))
        return not any(hit(rodrigues(P, hinge, axis, a), G).any() for a in ARC)

    # stock first (the trunk is cut round it), then the blade fitted against the ship after the cut
    stock = {}
    for z in range(ST['z0'], ST['z1'] + 1):
        xc = axis_x(z + 0.5)
        for x in range(int(math.floor(xc - ST['r'])) - 1, int(math.ceil(xc + ST['r'])) + 1):
            for y in range(YC - 2, YC + 3):
                if (x + 0.5 - xc) ** 2 + (y - YC) ** 2 <= ST['r'] ** 2 + 1e-9:
                    stock[(x, y, z)] = ST['cap'] if z == ST['z1'] else (C['iron'] if z in ST['hoops'] else ST['color'])

    # ── trunk: earlier cells within trunk_r of the axis, plus every cell the stock sweeps over the arc (stock foot .. poop plank) ──
    carve = {}
    for z in range(ST['z0'], ST['trunk_z1'] + 1):
        xc = axis_x(z + 0.5)
        for x in range(int(xc - ST['trunk_r']) - 2, int(xc + ST['trunk_r']) + 3):
            for y in range(YC - 4, YC + 5):
                if (x + 0.5 - xc) ** 2 + (y - YC) ** 2 <= ST['trunk_r'] ** 2 + 1e-9 and (x, y, z) in src:
                    carve[(x, y, z)] = src[(x, y, z)]
    Ps = corners(np.array(sorted(stock), float))
    swept_extra = 0
    for a in ([] if probe.get('noswept') else ARC):
        for q in set(map(tuple, np.floor(rodrigues(Ps, hinge, axis, a)).astype(int).tolist())):
            if q in src and q not in carve:
                carve[q] = src[q]
                swept_extra += 1
    by_work = {}
    for k, (w, c) in carve.items():
        by_work.setdefault(w, {})[k] = c
    G1 = G0.copy()
    for k in carve:
        G1[k] = False

    # ── blade: per (y, z) from the after edge forward to the most forward cell that clears the post over the whole arc ──
    blade, fore_gap = {}, []
    for z in range(0, RU['z_top'] + 1):
        xh = axis_x(z + 0.5)
        W = float(np.interp(z + 0.5, zs_w, ws))
        base = C['below'] if z < plan['hull_build']['bottom_top_z'] else C['above']      # the hull's paint line (white below z 42)
        c = C['iron'] if z in RU['straps'] else base
        for y in range(YC - RU['half_t'], YC + RU['half_t'] + 1):
            x_hi = min(int(math.floor(xh)) - 1, minx.get((y, z), 10 ** 9) - 1) - (RU['bevel'] if y != YC else 0)
            while not probe.get('nofit') and x_hi >= int(math.floor(xh - W)) and not clears((x_hi, y, z), G1):
                x_hi -= 1
            fore_gap.append(round(xh - (x_hi + 1), 2))
            for x in range(int(math.floor(xh - W)), x_hi + 1):
                blade[(x, y, z)] = c
    rudder = dict(blade)
    rudder.update(stock)
    top = sorted(k for k in stock if k[2] == ST['z1'] and k[1] == YC)
    stock_top = list(top[len(top) // 2])

    # ── collar on the poop deck round the hole ──
    fit = {}
    for z in FI['z']:
        xc = axis_x(z + 0.5)
        for x in range(int(xc) - 6, int(xc) + 7):
            for y in range(YC - 5, YC + 6):
                d2 = (x + 0.5 - xc) ** 2 + (y - YC) ** 2
                if ST['trunk_r'] ** 2 < d2 <= FI['r_out'] ** 2 and not G1[x, y, z]:
                    fit[(x, y, z)] = FI['color']

    # ── tiller: from the stock head forward on the centre line ──
    tiller = {}
    tip = TI['x_tip']
    x0t = int(math.floor(axis_x(TI['z'][0] + 0.5)))
    for x in range(x0t, tip + 1):
        if x > tip - TI['grip']:
            ys, zz, c = [YC], TI['z'][1:], TI['grip_color']
        elif x > tip - TI['taper']:
            ys, zz, c = range(YC - 1, YC + 2), TI['z'][1:], TI['color']
        else:
            ys, zz, c = range(YC - 1, YC + 2), TI['z'], TI['color']
        for y in ys:
            for z in zz:
                if (x, y, z) not in stock:
                    tiller[(x, y, z)] = C['iron'] if x in TI['bands'] else c

    # ── stem rollers: search the most forward spot on the bow rail that is supported, free and clear of ropes ──
    ys_S = list(range(RO['y_in'], RO['y_in'] + RO['cheek_w']))
    rtried, rbest = [], None

    def roller_cells(xs, zb, foot):
        """Cheeks: every column from its own rail top + 1 (foot) up to zb + 1 (flat top); roller in the inner slot."""
        cells = {}
        cx = xs + RO['len'] // 2
        for side in (1, -1):
            for x in range(xs, xs + RO['len']):
                for y in ys_S:
                    yy = YC + side * (y - YC)
                    for z in range(foot[(x, y)], zb + 2):
                        cells[(x, yy, z)] = RO['cheek_color']
            yin = YC + side * (RO['y_in'] - YC)
            yout = YC + side * (RO['y_in'] + RO['cheek_w'] - 1 - YC)
            for x in range(cx - 1, cx + 2):
                cells[(x, yin, zb + 1)] = RO['roller_color']
                cells[(x, yin, zb + 2)] = RO['roller_color']
                cells[(x, yout, zb + 2)] = RO['cheek_color']
            cells[(cx, yin, zb + 3)] = RO['roller_color']
            cells[(cx, yout, zb + 3)] = RO['cheek_color']
        return cells, cx
    for xs in range(RO['x_try'][1], RO['x_try'][0] - 1, -1):
        foot = {}
        for x in range(xs, xs + RO['len']):
            for y in ys_S:
                col = [z for z in range(55, 90) if G1[x, y, z]]          # rail top: hull, or the bow deck stepped up to it
                foot[(x, y)] = max(col) + 1 if col else None
        tops = set(foot.values())
        if None in tops or max(tops) - min(tops) > RO['rail_step_max']:
            rtried.append([xs, 'support', sorted(t for t in tops if t is not None)])
            continue
        zb = max(tops)
        cells, cx = roller_cells(xs, zb, foot)
        P = corners(np.array(sorted(cells), float))
        hits = int(hit(P, G1 | MO).sum())
        rc = rope_clear(P)
        rtried.append([xs, zb, hits, rc[0], rc[1]])
        if hits == 0 and rc[0] >= RO['rope_clear_min']:
            rbest = {'x': xs, 'zb': zb, 'cx': cx, 'rope_clear': rc, 'rail_tops': [min(tops), max(tops)]}
            rfoot = foot
            break
    if rbest is None:
        raise SystemExit('✗ no spot for the stem rollers: %s' % json.dumps(rtried, ensure_ascii=False))
    rollers, cx = roller_cells(rbest['x'], rbest['zb'], rfoot)
    hawse = {'hawse-S': [cx, RO['y_in'], rbest['zb'] + 3], 'hawse-P': [cx, 2 * YC - RO['y_in'], rbest['zb'] + 3]}

    # ── new fixed solids (stock / blade / tiller are models; collar + rollers are linked works) ──
    G2 = G1 | grid_of(fit) | grid_of(rollers)

    # ── anchors: grapnel pair on the fore well deck (S, P = mirror y) ──
    gsrc = np.loadtxt(os.path.join(M, 'helm_src', AN['work'] + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :3].astype(float)
    gS = Grapnel(gsrc, AN['pivot'], AN['scale'], AN['rotate'], False)
    gP = Grapnel(gsrc, AN['pivot'], AN['scale'], -AN['rotate'], True)
    main_top = {}
    for (x, y, z) in load(os.path.join(M, 'decks', 'main.vox.txt')):
        main_top[(x, y)] = max(main_top.get((x, y), -1), z + 1)
    obst = G2 | MO
    for k in list(rudder) + list(tiller):
        obst[k] = True

    def seat(g, x, y):
        bot = g.world(g.bottom, (x, y, 0.0))
        under = [main_top[c] for c in set(map(tuple, np.floor(bot[:, :2]).astype(int).tolist())) if c in main_top]
        if not under:
            return None
        z0 = min(under)
        for z in range(z0, z0 + 12):
            if hit(g.world(g.samples, (x, y, float(z))), obst).any():
                continue
            below = g.world(g.bottom, (x, y, float(z)))
            below[:, 2] -= 0.5
            if hit(below, obst).any():
                return float(z)
        return None
    atried, abest = [], None
    for ya in np.arange(AN['y_try'][1], AN['y_try'][0] - 0.01, -0.5):              # S: from the side inwards (stowed against the side) ...
        for xa in np.arange(AN['x_try'][0], AN['x_try'][1] + 0.01, 0.5):          # ... then from the hearth forward
            yp = 2 * YC + 1 - ya
            zs_ = seat(gS, xa, ya)
            zp_ = seat(gP, xa, yp) if zs_ is not None else None
            if zs_ is None or zp_ is None:
                continue
            PS = gS.world(gS.samples, (xa, ya, zs_))
            PP = gP.world(gP.samples, (xa, yp, zp_))
            rc = rope_clear(np.concatenate([PS, PP]))
            # keep clear of the hull wall by margin: the box grown by 1 must not touch the hull
            lo, hi = gS.bbox((xa, ya, zs_))
            near = False
            for (xa_, ya_, za_), gg in (((xa, ya, zs_), gS), ((xa, yp, zp_), gP)):        # box grown by 1 (above the floor) clear of hull and models (the hearth)
                lo, hi = gg.bbox((xa_, ya_, za_))
                sl = (slice(int(lo[0]) - 1, int(math.ceil(hi[0])) + 1), slice(int(lo[1]) - 1, int(math.ceil(hi[1])) + 1), slice(int(lo[2]) + 1, int(math.ceil(hi[2]))))
                near = near or bool(G2[sl].any() or MO[sl].any())
            atried.append([float(xa), float(ya), zs_, zp_, rc[0], bool(near)])
            if rc[0] >= AN['rope_clear_min'] and not near:
                abest = {'x': float(xa), 'yS': float(ya), 'yP': float(yp), 'zS': zs_, 'zP': zp_, 'rope_clear': rc}
                break
        if abest:
            break
    dxp = float(probe.get('anchor_dx', 0))
    arows = [{'name': '錨-S', 'host': AN['host'], 'work': AN['work'], 'at': [abest['x'] + dxp, abest['yS'], abest['zS']], 'pivot': AN['pivot'], 'scale': AN['scale'],
              'rotate': AN['rotate'], 'mirror': '', 'meta': dict(AN['meta']), '_g': gS},
             {'name': '錨-P', 'host': AN['host'], 'work': AN['work'], 'at': [abest['x'] + dxp, abest['yP'], abest['zP']], 'pivot': AN['pivot'], 'scale': AN['scale'],
              'rotate': -AN['rotate'], 'mirror': 'y', 'meta': dict(AN['meta']), '_g': gP}]
    for r in arows:
        r['meta']['hawse'] = '%d,%d,%d' % tuple(hawse['hawse-' + r['name'][-1]])
        lo, hi = r['_g'].bbox(r['at'])
        r['bbox'] = [r3(lo), r3(hi)]

    # ════ readings ════
    def samples(cells):
        return corners(np.array(sorted(cells), float))
    R = {}
    # rudder at rest and over the whole arc (blade + stock), against the ship after the trunk is cut (+ collar, rollers)
    Pr = samples(rudder)
    sweep = []
    for deg in range(-RU['max_deg'], RU['max_deg'] + 1, 1):                    # readings at 1 deg (the fit used arc_step)
        Q = rodrigues(Pr, hinge, axis, deg)
        h = hit(Q, G2)
        hw = {}
        for q in np.floor(Q[h]).astype(int):
            w = src.get(tuple(q), ('new', 0))[0]
            hw[w] = hw.get(w, 0) + 1
        sweep.append({'deg': deg, 'hits': int(h.sum()), 'by_work': hw})
    R['rudder'] = {'cells': len(rudder), 'blade': len(blade), 'stock': len(stock), 'z': [0, ST['z1']], 'hinge': r3(hinge), 'axis': [round(float(v), 4) for v in axis],
                   'stock_top': stock_top, 'at_rest_hits_solid': int(hit(Pr, G2).sum()), 'at_rest_hits_models': int(hit(Pr, MO).sum()),
                   'sweep': sweep, 'sweep_hits_max': max(s['hits'] for s in sweep),
                   'blade_fore_gap_to_axis': [min(fore_gap), max(fore_gap)],
                   'width_top_bottom': [len({x for (x, y, z) in blade if z == 0 and y == YC}), len({x for (x, y, z) in blade if z == RU['z_top'] and y == YC})],
                   'mirror_diff': sum(1 for (x, y, z), c in rudder.items() if rudder.get((x, 2 * YC - y, z)) != c)}
    # stock-top: ship cells within 8 (Ship_Game 9 rudder)
    shipG = G2
    st = np.array(stock_top, float) + 0.5
    nz = np.argwhere(shipG[int(st[0]) - 9:int(st[0]) + 10, int(st[1]) - 9:int(st[1]) + 10, int(st[2]) - 9:int(st[2]) + 10])
    dd = np.linalg.norm(nz + np.array([int(st[0]) - 9, int(st[1]) - 9, int(st[2]) - 9]) + 0.5 - st, axis=1) if len(nz) else np.array([99.0])
    R['stock_top_nearest_ship_cell'] = round(float(dd.min()), 2)
    # stock vs the stern glass (the stock rises inside the cabin right behind the centre window)
    glass = np.array([k for k, (w, c) in src.items() if w == 'stern-glass'], float) + 0.5
    sc = np.array(sorted(stock), float) + 0.5
    R['stock_to_glass_min'] = round(float(min(np.linalg.norm(glass - p, axis=1).min() for p in sc)), 2)
    # trunk
    R['trunk'] = {'r': ST['trunk_r'], 'z': [ST['z0'], ST['trunk_z1']], 'carved_by_work': {w: len(v) for w, v in sorted(by_work.items())}, 'swept_extra': swept_extra,
                  'gap_min_stock_to_leftover': None}
    rem = np.argwhere(G1[20:70, YC - 6:YC + 7, ST['z0']:ST['trunk_z1'] + 1]) + np.array([20, YC - 6, ST['z0']])
    R['trunk']['gap_min_stock_to_leftover'] = round(float(min(np.abs(rem - np.array(k)).max(axis=1).min() for k in stock if k[2] <= ST['trunk_z1'])), 2)
    # tiller at rest and over the arc: solids, models, ropes, lowest point over the deck
    Pt = samples(tiller)
    Pt0 = corners(np.array(sorted(tiller), float), 0.0)                          # exact cell corners for the lowest point (verifier 11: 76.92, not 77.15)
    tsw = []
    for deg in range(-RU['max_deg'], RU['max_deg'] + 1, 1):                    # readings at 1 deg (the fit used arc_step)
        Q = rodrigues(Pt, hinge, axis, deg)
        tsw.append({'deg': deg, 'hits_solid': int(hit(Q, G2).sum()), 'hits_models': int(hit(Q, MO).sum()), 'z_min': round(float(rodrigues(Pt0, hinge, axis, deg)[:, 2].min()), 2),
                    'rope_clear': rope_clear(Q)})
    R['tiller'] = {'cells': len(tiller), 'x': [min(k[0] for k in tiller), max(k[0] for k in tiller)], 'z': [min(k[2] for k in tiller), max(k[2] for k in tiller)],
                   'length_m_from_axis': round((tip + 1 - axis_x(TI['z'][1] + 0.5)) / 10.0, 2),
                   'sweep': tsw, 'sweep_hits_max': max(s['hits_solid'] + s['hits_models'] for s in tsw),
                   'deck_surface_z': FI['z'][0], 'z_min_over_arc': min(s['z_min'] for s in tsw),
                   'rope_clear_min': min(s['rope_clear'][0] for s in tsw),
                   'tip_to_binnacle': None, 'mirror_diff': sum(1 for (x, y, z), c in tiller.items() if tiller.get((x, 2 * YC - y, z)) != c)}
    if '羅經櫃' in gear_models:
        R['tiller']['tip_to_binnacle'] = round(gear_models['羅經櫃'][1]['bbox'][0][0] - (tip + 1), 2)
    # connected: blade + stock one piece; tiller touches the stock; collar touches the poop plank; rollers touch the hull
    def ncomp(cells):
        return int(ndimage.label(grid_of(cells))[1])
    R['pieces'] = {'rudder_components': ncomp(rudder), 'rudder_plus_tiller': ncomp({**rudder, **tiller}), 'tiller_components': ncomp(tiller),
                   'collar_components': ncomp(fit), 'collar_touch_ship': sum(1 for (x, y, z) in fit if G1[x, y, z - 1]),
                   'rollers_components': ncomp(rollers), 'rollers_touch_ship': sum(1 for (x, y, z) in rollers if G1[x, y, z - 1])}
    R['fittings'] = {'cells': len(fit), 'on_solid': int(sum(G1[k] for k in fit)), 'mirror_diff': sum(1 for (x, y, z), c in fit.items() if fit.get((x, 2 * YC - y, z)) != c),
                     'rope_clear': rope_clear(samples(fit)), 'hits_models': int(hit(samples(fit), MO).sum())}
    R['rollers'] = {'cells': len(rollers), 'chosen': rbest, 'tried': rtried, 'hawse': hawse, 'on_solid': int(sum(G1[k] for k in rollers)),
                    'hits_models': int(hit(samples(rollers), MO).sum()),
                    'mirror_diff': sum(1 for (x, y, z), c in rollers.items() if rollers.get((x, 2 * YC - y, z)) != c)}
    # anchors
    rows_rep = []
    obst2 = G2 | MO
    for k in list(rudder) + list(tiller):
        obst2[k] = True
    for r in arows:
        g = r['_g']
        Pa = g.world(g.samples, r['at'])
        lo, hi = r['bbox']
        cx_, cy_, fz = int(math.floor((lo[0] + hi[0]) / 2)), int(math.floor((lo[1] + hi[1]) / 2)), int(math.floor(lo[2])) - 1
        rows_rep.append({'name': r['name'], 'at': r3(r['at']), 'hits': int(hit(Pa, obst2).sum()), 'bbox': r['bbox'],
                         'foot_gap': next((d for d in range(0, 13) if obst2[cx_, cy_, fz - d]), None), 'rope_clear': rope_clear(Pa)})
    sS = set(map(tuple, np.floor(arows[0]['_g'].world(arows[0]['_g'].centers, arows[0]['at'])).astype(int).tolist()))
    sP = set(map(tuple, np.floor(arows[1]['_g'].world(arows[1]['_g'].centers, arows[1]['at'])).astype(int).tolist()))
    R['anchors'] = {'chosen': abest, 'tried_n': len(atried), 'rows': rows_rep,
                    'mirror_diff_cells': len({(x, 2 * YC - y, z) for (x, y, z) in sS} ^ sP),
                    'to_hearth_min': None}
    if '爐灶' in gear_models:
        gh, rh = gear_models['爐灶']
        Ph = gh.world(gh.centers, rh['at'])
        R['anchors']['to_hearth_min'] = round(float(min(np.linalg.norm(Ph - p, axis=1).min() for p in np.concatenate([
            arows[0]['_g'].world(arows[0]['_g'].centers, arows[0]['at']), arows[1]['_g'].world(arows[1]['_g'].centers, arows[1]['at'])]))), 2)
    # cable lines hawse -> cable beam (top face at the same y): through solid?  distance to the hearth?
    beam = load(os.path.join(M, 'masts', 'cable_beam.vox.txt'))
    bx = (min(k[0] for k in beam) + max(k[0] for k in beam) + 1) / 2.0
    bz = max(k[2] for k in beam) + 1.0
    cab = {}
    for nm, hw in hawse.items():
        a = np.array(hw, float) + np.array([0.5, 0.5, 1.0])
        b = np.array([bx, hw[1] + 0.5, bz])
        t = np.linspace(0, 1, 400)[:, None]
        Ps = a + (b - a) * t
        own = np.linalg.norm(Ps - a, axis=1) > 2.0
        own &= np.linalg.norm(Ps - b, axis=1) > 2.0
        h = hit(Ps[own], G2 | MO)
        ent = {'from': r3(a), 'to': r3(b), 'samples_in_solid': int(h.sum()), 'len_m': round(float(np.linalg.norm(b - a)) / 10, 2)}
        if '爐灶' in gear_models:
            ent['to_hearth_min'] = round(float(min(seg_dist(a, b, Ph[i:i + 1])[0] for i in range(len(Ph)))), 2)
        if h.any():
            ent['first_solid'] = r3(Ps[own][h][0])
        cab[nm] = ent
    R['cable_lines'] = cab
    # ladder points: nothing new on them
    LP = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
    newG = grid_of(fit) | grid_of(rollers) | grid_of(rudder) | grid_of(tiller)
    for r in arows:
        i = np.floor(r['_g'].world(r['_g'].centers, r['at'])).astype(int)
        newG[i[:, 0], i[:, 1], i[:, 2]] = True
    lp_bad = []
    pts = LP['points'] if isinstance(LP, dict) and 'points' in LP else LP
    for nm, v in (pts.items() if isinstance(pts, dict) else []):
        for k in ('foot', 'head', 'lo', 'hi'):
            p = v.get('points', v).get(k) if isinstance(v, dict) else None
            if p and newG[int(p[0]), int(p[1]), int(p[2]):int(p[2]) + 14].any():
                lp_bad.append([nm, k])
    R['ladder_points_blocked'] = lp_bad
    R['carved_cells_total'] = len(carve)
    if probe:
        print(json.dumps({'probe': probe, 'rudder_sweep_hits_max': R['rudder']['sweep_hits_max'], 'rudder_sweep': [(s['deg'], s['hits'], s['by_work']) for s in sweep],
                          'tiller_sweep_hits_max': R['tiller']['sweep_hits_max'], 'tiller': [(s['deg'], s['hits_solid'], s['hits_models']) for s in tsw],
                          'trunk_gap': R['trunk']['gap_min_stock_to_leftover'], 'anchors': rows_rep}, ensure_ascii=False))
        return

    # ════ outputs ════
    out = os.path.join(M, 'helm')
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(M, 'step11'), exist_ok=True)
    lists = {}

    def write(path, part, title):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 星辰號 %s（世界座標、at 0,0,0；draft_helm.py）\n' % title)
            for (x, y, z), c in sorted(part.items()):
                f.write('%d,%d,%d,%d\n' % (x, y, z, c))
        lists[os.path.relpath(path, M).replace('\\', '/')] = [len(part), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    write(os.path.join(out, 'rudder.vox.txt'), rudder, '舵（舵葉＋舵桿；外部模型 kind=rudder）')
    write(os.path.join(out, 'tiller.vox.txt'), tiller, '舵柄（外部模型 kind=tiller）')
    write(os.path.join(out, 'fittings.vox.txt'), fit, '舵頭圈（船尾樓甲板上，關聯）')
    write(os.path.join(out, 'rollers.vox.txt'), rollers, '艏柱滾輪（兩舷夾板＋滾輪，關聯）')
    carve_files = {'hull': 'hull_carve', 'deck-poop': 'poop_carve', 'stern-carving': 'carving_carve'}
    for w, part in sorted(by_work.items()):
        if w not in carve_files:
            raise SystemExit('✗ the trunk would cut %d cells of %s (not planned)' % (len(part), w))
        write(os.path.join(M, 'step11', carve_files[w] + '.vox.txt'), part, '舵孔要刻掉的格（%s；carvevox）' % w)
    V.update(R)
    V['lists'] = lists
    V['grapnel_src_sha256'] = hashlib.sha256(open(os.path.join(M, 'helm_src', AN['work'] + '.vox.txt'), 'rb').read()).hexdigest()
    spin = {'spin': 'rudder', 'spin_k': RU['max_deg'], 'spin_min': -RU['max_deg'], 'spin_max': RU['max_deg'], 'spin_lag': 0.3}
    hm = {'hinge_x': round(float(hinge[0]), 4), 'hinge_y': hinge[1], 'hinge_z': 0.0, 'axis_x': round(float(axis[0]), 4), 'axis_y': 0.0, 'axis_z': round(float(axis[2]), 4)}
    place = {'note': 'draft_helm.py 的結果（世界座標）',
             'rudder': {'work': RU['work'], 'title': RU['title'], 'model': RU['model'], 'host': HB['assembly'], 'at': r3(hinge), 'pivot': r3(hinge),
                        'anchors': {'stock-top': stock_top},
                        'meta': dict({'kind': 'rudder'}, **hm, max_deg=RU['max_deg'], turn_axis='hinge', **spin)},
             'tiller': {'work': TI['work'], 'title': TI['title'], 'model': TI['model'], 'host': HB['assembly'], 'at': r3(hinge), 'pivot': r3(hinge),
                        'meta': dict({'kind': 'tiller'}, **spin, spin_pivot_x=hm['hinge_x'], spin_pivot_y=hm['hinge_y'], spin_pivot_z=0.0,
                                     spin_axis_x=hm['axis_x'], spin_axis_y=0.0, spin_axis_z=hm['axis_z'])},
             'links': [{'work': FI['work'], 'title': FI['title'], 'link': FI['link'], 'list': 'helm/fittings'},
                       {'work': RO['work'], 'title': RO['title'], 'link': RO['link'], 'list': 'helm/rollers'}],
             'anchors': [{k: v for k, v in r.items() if not k.startswith('_')} for r in arows],
             'hawse': hawse,
             'carve': {w: 'step11/' + carve_files[w] for w in sorted(by_work)}}
    json.dump(place, open(os.path.join(design, 'helm_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(V, open(os.path.join(design, 'verify_helm.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    shown = {}                                                                   # models drawn on the sheet (verifier 11: the binnacle was missing in (b))
    for nm in ('羅經櫃',):
        if nm in gear_models:
            g, r = gear_models[nm]
            for p in np.floor(g.world(g.centers, r['at'])).astype(int).tolist():
                shown[tuple(p)] = 104
    sheet(design, plan, src, carve, rudder, tiller, fit, rollers, arows, hawse, hinge, axis, R, YC, shown)
    short = {k: R[k] for k in ('stock_top_nearest_ship_cell', 'stock_to_glass_min', 'trunk', 'pieces', 'carved_cells_total', 'ladder_points_blocked')}
    short['rudder'] = {k: R['rudder'][k] for k in ('cells', 'blade', 'stock', 'stock_top', 'at_rest_hits_solid', 'at_rest_hits_models', 'sweep_hits_max', 'width_top_bottom', 'mirror_diff')}
    short['tiller'] = {k: R['tiller'][k] for k in ('cells', 'x', 'z', 'length_m_from_axis', 'sweep_hits_max', 'z_min_over_arc', 'rope_clear_min', 'tip_to_binnacle', 'mirror_diff')}
    short['fittings'] = R['fittings']
    short['rollers'] = {k: R['rollers'][k] for k in ('cells', 'chosen', 'hawse', 'on_solid', 'hits_models', 'mirror_diff')}
    short['anchors'] = {k: R['anchors'][k] for k in ('chosen', 'rows', 'mirror_diff_cells', 'to_hearth_min')}
    short['cable_lines'] = R['cable_lines']
    print(json.dumps(short, ensure_ascii=False))
    print(json.dumps(lists, ensure_ascii=False))


def sheet(design, plan, src, carve, rudder, tiller, fit, rollers, arows, hawse, hinge, axis, R, YC, shown):
    """Sheet 09: stern centre-line section (rudder, stock, trunk, tiller), poop deck from above (tiller arc), bow (rollers, anchors)."""
    W, Hh = 1800, 1250
    im = Image.new('RGB', (W, Hh), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 12), 'Star (al-Najm) sheet 09: rudder, tiller, stem rollers, anchors (TASK-0019 step 11; draft_helm.py)', fill=(0, 0, 0), font=font(22))
    new = {}
    for part in (rudder, tiller, fit, rollers, shown):
        new.update(part)

    def colour(k):
        if k in new:
            return palette_rgb(new[k])
        if k in src and k not in carve:
            return tuple(int(v * 0.55 + 110) for v in palette_rgb(src[k][1]))
        return None

    def panel(ox, oy, xr, vr, k, get, title):
        d.text((ox, oy - 24), title, fill=(0, 0, 0), font=font(15))
        for x in range(*xr):
            for v in range(*vr):
                c = get(x, v)
                if c is not None:
                    px, py = ox + (x - xr[0]) * k, oy + (vr[1] - 1 - v) * k
                    d.rectangle([px, py, px + k - 1, py + k - 1], fill=c)
        return lambda x, v: (ox + (x - xr[0]) * k, oy + (vr[1] - v) * k)
    # (a) centre-line section y = YC, x 15..125, z 0..95 (carved cells drawn red)
    def side(x, z):
        k = (x, YC, z)
        if k in carve:
            return (220, 60, 60)
        return colour(k)
    ta = panel(30, 70, (15, 126), (0, 96), 7, side, '(a) centre line y %d: rudder blade + stock (model), trunk carved (red), collar, tiller; hinge axis dashed' % YC)
    p0, p1 = hinge, hinge + axis * 92
    a_, b_ = ta(p0[0], p0[2]), ta(p1[0], p1[2])
    for t in np.linspace(0, 1, 40)[::2]:
        q0 = (a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t)
        q1 = (a_[0] + (b_[0] - a_[0]) * (t + 0.025), a_[1] + (b_[1] - a_[1]) * (t + 0.025))
        d.line([q0, q1], fill=(0, 0, 200), width=2)
    # (b) poop deck from above with the tiller arc
    def top(x, y):
        for z in range(95, 70, -1):
            c = colour((x, y, z))
            if c is not None:
                return c
        return None
    tb = panel(840, 70, (20, 130), (30, 131), 8, top, '(b) poop deck from above: tiller (arc +-%d deg), collar, binnacle, kevel, mizzen' % plan['helm_build']['rudder']['max_deg'])
    tipx = plan['helm_build']['tiller']['x_tip'] + 1
    for deg in (-35, 0, 35):
        q = rodrigues(np.array([[tipx, YC + 0.5, 80.5]]), hinge, axis, deg)[0]
        h = (float(hinge[0] + axis[0] * 80.5 / axis[2]), YC + 0.5)
        d.line([tb(*h), tb(q[0], q[1])], fill=(200, 30, 30), width=2)
    # (c) bow from above + side: rollers, anchors (boxes), cable lines
    def top_c(x, y):
        for z in range(95, 45, -1):
            c = colour((x, y, z))
            if c is not None:
                return c
        return None
    tc = panel(30, 800, (286, 400), (45, 116), 6, top_c, '(c) bow from above: stem rollers, anchors (boxes), cable lines to the cable beam')
    for r in arows:
        lo, hi = r['bbox']
        d.rectangle([tc(lo[0], hi[1]), tc(hi[0], lo[1])], outline=(200, 30, 30), width=3)
        d.text(tc(lo[0], hi[1] + 3), 'anchor-' + r['name'][-1], fill=(200, 30, 30), font=font(14))
    for nm, c in R['cable_lines'].items():
        d.line([tc(c['from'][0], c['from'][1]), tc(c['to'][0], c['to'][1])], fill=(30, 90, 200), width=2)

    def side_c(x, z):
        for y in range(YC, YC + 40):
            c = colour((x, y, z))
            if c is not None:
                return c
        return None
    td = panel(760, 800, (340, 400), (55, 90), 10, side_c, '(c\') stem head from starboard: cheek + roller, hawse-S x')
    hx = hawse['hawse-S']
    p = td(hx[0] + 0.5, hx[2] + 0.5)
    d.line([p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8], fill=(200, 0, 0), width=3)
    d.line([p[0] - 8, p[1] + 8, p[0] + 8, p[1] - 8], fill=(200, 0, 0), width=3)
    tl = R['tiller']
    d.text((1400, 800), '\n'.join([
        'rudder: blade z 0-%d, stock to z %d, hinge (%.2f, %.1f, 0)' % (plan['helm_build']['rudder']['z_top'], plan['helm_build']['stock']['z1'], hinge[0], hinge[1]),
        '  axis (%.4f, 0, %.4f), max 35 deg, stock-top %s' % (axis[0], axis[2], R['rudder']['stock_top']),
        '  sweep hits max %d' % R['rudder']['sweep_hits_max'],
        'tiller: x %d-%d, z %d-%d, %.2f m from the axis' % (tl['x'][0], tl['x'][1], tl['z'][0], tl['z'][1], tl['length_m_from_axis']),
        '  sweep hits max %d, lowest z %.2f (deck %d)' % (tl['sweep_hits_max'], tl['z_min_over_arc'], tl['deck_surface_z']),
        'trunk r %.1f: carved %s' % (R['trunk']['r'], R['trunk']['carved_by_work']),
        'rollers x %d, hawse-S %s / hawse-P %s' % (R['rollers']['chosen']['x'], hawse['hawse-S'], hawse['hawse-P']),
        'anchors: grapnel x %.2g at %s / %s' % (arows[0]['scale'], r3(arows[0]['at']), r3(arows[1]['at']))]), fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet09_helm_v1.png'))


if __name__ == '__main__':
    main()
