# Source: calli-cosecha-01m/design/draft_gear.py (Harvest, TASK-0598: magazine sub-work + powder-barrel models, boat skids,
#   reused components as models with the z measured) + apex-two-barbados-01m/design/draft_gear.py (Barbados, TASK-1147:
#   hatch covers from the Monitor hatch scaled per axis, galley) -- rewritten for the Star (TASK-0019 step 10).
# Star (al-Najm) new sheet 08: magazine and deck gear.
#   Magazine (Ship_Magazine 8): between two bulkheads on the orlop platform; for every x the air of the (y, z) section nearest
#     the centre line (4-connected) between floor and ztop ⇒ copper bulkheads (oak frame, door 5 wide), copper on the hull side,
#     pine floor with oak battens; barrels upright every pitch, aisle on the centre line, a pair at a time (both sides
#     mirror), cap barrels; sealed cavities <= 50 filled, every new cell must reach the old solid.
#   Boat skids: three cross beams with 2x2 posts down to the first solid.
#   Hearth (galley): its own 0.05 m sub-work drawn here (sand box, three stones, pot, dallah); smoke anchor over the pot.
#   Models (boat, binnacle, hearth, hatch covers, cabin door): at.z None ⇒ measured (lowest z from the host deck top up where
#     every sample is clear and the bottom touches a solid); doors are placed first and count as obstacles for the rest.
#   Differences from Harvest: solids are the design lists of every earlier step (like draft_guns.py) ⇒ no server, a rerun after
#     stamping is byte-identical; component cells come from masks/gear_src (exported once, sha in verify); added readings:
#     hoist ladders (9x9 flat spot by the foot, a stand by the head), door openings (Ship_Fittings 9.7), galley faces (9.13),
#     rope clearance, ladder points, gun boxes.
#   Outputs: masks/gear/{magazine,skids,hearth}.vox.txt, gear_placement.json, verify_gear.json, sheet08_gear_v1.png
#   Usage: python -X utf8 draft_gear.py <design> [--probe=shift=<model>:<dx>] [--probe=nokind=<model>] [--probe=cap=<n>]
#     reverse controls, nothing written: push one model along x (its collisions must show up); drop one model's kind;
#     another barrel cap (the barrel readings at that cap).
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import font, palette_rgb
from draft_masts import ship_cells, load
from draft_guns import Gun, Grid

HEAD = 12           # walk: 1.2 m of air over the standing cell (Ship_Decks)
BARREL_HEAD = 8     # powder spot: 9 x 9 flat, 0.8 m clear (todo step 9 / San Roman)


def r3(v):
    return [round(float(c), 3) for c in v]


def corners(cells, inset=0.2):
    a, b = inset, 1.0 - inset
    o = np.array([[0.5, 0.5, 0.5]] + [[(a, b)[k & 1], (a, b)[(k >> 1) & 1], (a, b)[(k >> 2) & 1]] for k in range(8)])
    return (cells[:, None, :] + o[None]).reshape(-1, 3)


class Model:
    """CLI work model: p = at + Rz(rot) . ((v - pivot) * scale)  (scale per axis, no mirror in this step)."""

    def __init__(s, cells, pivot, scale, rot):
        s.cells = np.asarray(cells, float)
        s.pivot = np.array(pivot, float)
        s.scale = np.array(scale if isinstance(scale, (list, tuple)) else [scale] * 3, float)
        s.rot = float(rot)
        s.samples = corners(s.cells)
        s.centers = s.cells + 0.5
        zmin = s.cells[:, 2].min()
        s.bottom = corners(s.cells[s.cells[:, 2] == zmin])
        s.bottom = s.bottom[s.bottom[:, 2] < zmin + 0.5]
        s.lo, s.hi = s.cells.min(0), s.cells.max(0) + 1

    def world(s, P, at):
        q = (np.asarray(P, float) - s.pivot) * s.scale
        c, sn = math.cos(math.radians(s.rot)), math.sin(math.radians(s.rot))
        return np.stack([q[..., 0] * c - q[..., 1] * sn + at[0], q[..., 0] * sn + q[..., 1] * c + at[1], q[..., 2] + at[2]], -1)

    def bbox(s, at):
        C = np.array([[(s.lo[0], s.hi[0])[k & 1], (s.lo[1], s.hi[1])[(k >> 1) & 1], (s.lo[2], s.hi[2])[(k >> 2) & 1]] for k in range(8)], float)
        W = s.world(C, at)
        return W.min(0), W.max(0)

    def local(s, P, at):
        q = np.asarray(P, float) - np.array(at, float)
        c, sn = math.cos(math.radians(-s.rot)), math.sin(math.radians(-s.rot))
        return np.stack([q[..., 0] * c - q[..., 1] * sn, q[..., 0] * sn + q[..., 1] * c, q[..., 2]], -1) / s.scale + s.pivot


def hearth_cells(H):
    """The sand-box hearth in its own frame (0.05 m): x 0..23, y 0..19."""
    C = H['colors']
    nx, ny = H['size'][0], H['size'][1]
    cells = {}
    for x in range(nx):
        for y in range(ny):
            cells[(x, y, 0)] = C['box']                                          # bottom planks
            edge = x in (0, nx - 1) or y in (0, ny - 1)
            for z in range(1, 9):
                if edge:
                    corner = x in (0, nx - 1) and y in (0, ny - 1)
                    cells[(x, y, z)] = C['rim'] if (z == 8 or corner) else C['box']
                elif z <= 6:
                    cells[(x, y, z)] = C['sand']
    cx, cy = 12.0, 10.5
    for x in range(1, nx - 1):                                                   # sand top: ash ring round the fire, char spots
        for y in range(1, ny - 1):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            cells[(x, y, 7)] = C['char'] if d < 2.6 else (C['ash'] if d < 4.6 and (x + y) % 3 else C['sand'])
    for (x, y) in ((11, 11), (12, 10), (13, 11), (12, 11)):                       # embers under the pot
        cells[(x, y, 7)] = C['ember'] if (x + y) % 2 else C['ember2']
    for sx, sy in ((12, 6), (9, 13), (15, 13)):                                  # three stones (athafi), 3 x 3, rounded top; v1 (12,5)/(8,14)/(16,14) left the pot floating 0.03 off them
        for x in range(sx - 1, sx + 2):
            for y in range(sy - 1, sy + 2):
                for z in (7, 8):
                    cells[(x, y, z)] = C['stone']
                if (x - sx) * (y - sy) == 0:
                    cells[(x, y, 9)] = C['stone']
    for x in range(7, 18):                                                       # copper pot on the stones
        for y in range(5, 17):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 4.0:
                cells[(x, y, 10)] = C['pot']
                if d > 3.0:
                    for z in range(11, 15):
                        cells[(x, y, z)] = C['pot']
                else:
                    cells[(x, y, 11)] = C['food']
    for x in range(18, 21):                                                      # dallah (brass coffee pot) on the sand, corner
        for y in range(2, 5):
            cells[(x, y, 7)] = C['brass']
            for z in (8, 9, 10):
                if (x - 19) * (y - 3) == 0:
                    cells[(x, y, z)] = C['brass']
    cells[(19, 3, 11)] = C['brass']
    cells[(19, 3, 12)] = C['brass']                                              # lid knob
    cells[(17, 3, 10)] = C['brass']                                              # spout
    for x in range(2, 10):                                                       # two sticks of firewood
        cells[(x, 17, 7)] = C['wood']
        if x >= 4:
            cells[(x, 16, 7)] = C['wood']
    return cells


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    YC = plan['space']['yc']
    GB = plan['gear_build']
    MG, SK, HB = GB['magazine'], GB['skids'], GB['hearth']
    if 'cap' in probe:
        MG['cap'] = int(probe['cap'])
    M = os.path.join(design, 'masks')
    SRC = os.path.join(M, 'gear_src')

    # ── every solid placed before step 10 (design lists; same set as draft_guns.py + the step-9 gun fittings) ──
    occ = ship_cells(design, plan)
    for f in ('main', 'mizzen', 'jibboom', 'cable_beam'):
        occ.update(load(os.path.join(M, 'masts', f + '.vox.txt')))
    for f in ('rings', 'stern_spars', 'halyard_bitt'):
        occ.update(load(os.path.join(M, 'rigging', f + '.vox.txt')))
    occ.update(load(os.path.join(M, 'gunfittings', 'gunfittings.vox.txt')))
    YP = {y['mast']: y for y in json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))}
    for key in ('main', 'mizzen'):
        off = [int(round(YP[key]['at'][i] - YP[key]['pivot'][i])) for i in range(3)]
        for (x, y, z), c in load(os.path.join(M, 'yards', 'lateen-%s.vox.txt' % key)).items():
            occ[(x + off[0], y + off[1], z + off[2])] = c
    G0 = Grid(occ)
    S0 = G0.G
    decks = {}
    for k in GB['deck_works']:
        top = {}
        for (x, y, z) in load(os.path.join(M, 'decks', k + '.vox.txt')):
            top[(x, y)] = max(top.get((x, y), -1), z + 1)
        decks[k] = top
    # guns: every cell centre in world (exact obstacle for the new models) + their boxes
    GBG = plan['guns_build']
    gun_t = {k: Gun(k, t, design, 0.2) for k, t in GBG['types'].items()}
    gun_rows = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']
    gun_cells = np.zeros(S0.shape, bool)
    gun_box = []
    for r in gun_rows:
        g = gun_t[r['type']]
        W = g.world(g.centers, r['at'], r['phi'], r['side'] == 'P')
        i = np.floor(W).astype(int)
        gun_cells[i[:, 0], i[:, 1], i[:, 2]] = True
        gun_box.append((r['name'], np.array(r['bbox'][0], float), np.array(r['bbox'][1], float)))

    # ── magazine: per x, the air of the (y, z) section nearest the centre line, z F..ZTOP ──
    C = MG['colors']
    COPPER, OAK, DARK, PINE = C['copper'], C['oak'], C['dark'], C['pine']
    X0, X1, F, ZTOP = MG['x0'], MG['x1'], MG['floor'], MG['ztop']
    interior, mlog = {}, []
    for x in range(X0, X1 + 1):
        band = np.zeros(S0.shape[1:], bool)
        band[:, F:ZTOP + 1] = ~S0[x, :, F:ZTOP + 1]
        lab, _ = ndimage.label(band)
        I = np.zeros_like(band)
        seeds = []
        for sgn in (-1, 1):
            ys = [y for y in range(YC, YC + sgn * 80, sgn) if 0 <= y < band.shape[0] and band[y, F + 1]]
            if ys:
                I |= lab == lab[ys[0], F + 1]
                seeds.append(ys[0])
        interior[x] = I
        ys, zs = np.nonzero(I)
        mlog.append({'x': x, 'cells': int(I.sum()), 'y': [int(ys.min()), int(ys.max())] if len(ys) else None, 'seeds': seeds,
                     'pillar': bool(S0[x, YC, F + 1])})
    mag = {}
    dw, dh = MG['door_w'], MG['door_head']
    door_x = X1 if MG['door'] == 'fore' else X0
    for x, I in interior.items():
        wall = x in (X0, X1)
        for y, z in zip(*np.nonzero(I)):
            y, z = int(y), int(z)
            if z == F:
                mag[(x, y, z)] = OAK if (y - YC) % 6 == 0 else PINE                  # floor: pine, an oak batten every 6
            elif wall:
                if x == door_x and abs(y - YC) <= dw // 2 and z <= ZTOP - dh:
                    continue                                                        # doorway
                frame = (y - YC) % 8 == 0 or z == F + 1 or z == ZTOP
                if x == door_x and (abs(y - YC) == dw // 2 + 1 and z <= ZTOP - dh + 1 or abs(y - YC) <= dw // 2 and z == ZTOP - dh + 1):
                    frame = True
                mag[(x, y, z)] = OAK if frame else COPPER
            else:
                side = any(not (0 <= y + d < I.shape[0]) or (not I[y + d, z] and S0[x, y + d, z]) for d in (-1, 1))
                if side and abs(y - YC) > 6:
                    mag[(x, y, z)] = COPPER                                         # copper on the hull side (not on the mizzen heel)
    free = set()
    for x, I in interior.items():
        for y, z in zip(*np.nonzero(I)):
            k = (x, int(y), int(z))
            if F + 1 <= k[2] <= ZTOP and k not in mag:
                free.add(k)
    B = MG['barrel']
    R = B['d'] * B['mpv'] / 0.1 / 2
    H = B['h'] * B['mpv'] / 0.1
    barrels, rack, capacity = [], {}, []

    def foot(cx, cy):
        return [(x, y) for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R))) for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)))]

    def body_free(cx, cy, z0):
        # every cell whose centre is within R + 0.75 of the axis must be free (Harvest v3: R + 0.3 let barrels graze the copper)
        return all((x, y, z) in free and (x, y, z) not in rack for x in range(int(math.floor(cx - R - 1)), int(math.ceil(cx + R + 1)))
                   for y in range(int(math.floor(cy - R - 1)), int(math.ceil(cy + R + 1))) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= (R + 0.75) ** 2
                   for z in range(int(math.floor(z0)), int(math.ceil(z0 + H))))

    def under_barrel(x, y, z, t_now):
        return any(b['tier'] < t_now and b['at'][2] <= z < b['at'][2] + H and (x + 0.5 - b['at'][0]) ** 2 + (y + 0.5 - b['at'][1]) ** 2 <= R ** 2 for b in barrels)

    def in_barrel(x, y, z):
        return any(z < b['at'][2] + H and z + 1 > b['at'][2] and (x + 0.5 - b['at'][0]) ** 2 + (y + 0.5 - b['at'][1]) ** 2 <= (R + 0.75) ** 2 for b in barrels)

    for t in range(0, 4):
        n_t = 0
        cx = X0 + 2 + R
        while cx + R <= X1 - 1:
            z0 = F + 1 + t * B['tier']
            cy = YC + 0.5 + (B['aisle'] + 0.5 + R)
            while abs(cy - YC) < 80:                                                # one mirrored pair at a time
                pair = [(cy, 1), (2 * YC + 1 - cy, -1)]
                shelf = {s: [(x, y, int(z0) - 1) for x, y in foot(cx, c)] if t else [] for c, s in pair}
                ok = all(body_free(cx, c, z0) and all(p in free and p not in rack and not under_barrel(*p, t) for p in shelf[s]) for c, s in pair)
                posts = {}
                if ok and t:
                    def post_ok(x, y):
                        return all((x, y, z) in free and (x, y, z) not in rack and not in_barrel(x, y, z) for z in range(F + 1, int(z0) - 1))
                    col = sorted((x, y) for x, y, _ in shelf[1] if post_ok(x, y))
                    best = max(((a, b) for a in col for b in col), key=lambda ab: ((ab[0][0] - ab[1][0]) ** 2 + (ab[0][1] - ab[1][1]) ** 2, ab), default=None)
                    if not best or best[0] == best[1]:
                        ok = False
                    else:
                        posts[1] = sorted(set(best))
                        posts[-1] = [(x, 2 * YC - y) for x, y in posts[1]]
                        ok = all(post_ok(x, y) for x, y in posts[-1])
                if ok:
                    n_t += 2
                    if len(barrels) + 2 <= MG['cap']:
                        for c, s in pair:
                            barrels.append({'at': [round(cx, 3), round(c, 3), round(z0, 3)], 'tier': t})
                            for p in shelf[s]:
                                rack[p] = OAK
                            for px, py in posts.get(s, []):
                                for z in range(F + 1, int(z0) - 1):
                                    rack[(px, py, z)] = DARK
                elif not t:
                    break
                cy += B['pitch']
            cx += B['pitch']
        capacity.append(n_t)
        if len(barrels) >= MG['cap'] or (not n_t and t):
            break
    assert not set(rack) & set(mag)
    mag.update(rack)
    free -= set(rack)

    # ── boat skids: cross beams 2 wide x 2 high, 2x2 posts down to the first solid ──
    skids = {}
    for xs in SK['xs']:
        for x in (xs, xs + 1):
            for y in range(YC - SK['y_half'], YC + SK['y_half'] + 1):
                for z in (SK['beam_z'], SK['beam_z'] + 1):
                    skids[(x, y, z)] = SK['color']
            for py in (YC - SK['post_dy'] - 1, YC - SK['post_dy'], YC + SK['post_dy'], YC + SK['post_dy'] + 1):
                z = SK['beam_z'] - 1
                while z > 0 and not S0[x, py, z]:
                    skids[(x, py, z)] = SK['color']
                    z -= 1

    new = dict(mag)
    clash = [k for k in skids if k in new]
    new.update(skids)
    on_solid = [k for k in new if S0[k]]
    sealed, floating = [], []
    for nm, part, (xa, xb, za, zb) in (('magazine', mag, (X0 - 2, X1 + 2, F - 2, ZTOP + 3)),
                                        ('skids', skids, (min(SK['xs']) - 2, max(SK['xs']) + 3, 50, SK['beam_z'] + 4))):
        sub = S0[xa:xb + 1, :, za:zb + 1].copy()
        nw = np.zeros_like(sub)
        for (x, y, z) in part:
            if xa <= x <= xb and za <= z <= zb:
                nw[x - xa, y, z - za] = True
        solid = sub | nw
        lab, n = ndimage.label(~solid)
        edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
        for L in range(1, n + 1):
            if L in edge:
                continue
            xs_, ys_, zs_ = np.nonzero(lab == L)
            if len(xs_) > 50:
                sealed.append([nm, 'big', int(len(xs_)), int(xs_.min()) + xa, int(ys_.min()), int(zs_.min()) + za])
                continue
            for x, y, z in zip(xs_, ys_, zs_):
                part[(int(x) + xa, int(y), int(z) + za)] = OAK
                nw[x, y, z] = True
            sealed.append([nm, 'filled', int(len(xs_)), int(xs_.min()) + xa, int(ys_.min()), int(zs_.min()) + za])
        solid = sub | nw
        lab, n = ndimage.label(solid)
        anchored = set(np.unique(lab[sub])) - {0}
        fl = [int(L) for L in np.unique(lab[nw]) if L not in anchored]
        floating += [[nm, (np.argwhere(lab == L).min(axis=0) + [xa, 0, za]).tolist()] for L in fl]

    # grid with the new cells
    S = S0.copy()
    for k in list(mag) + list(skids):
        S[k] = True

    def hit(P, grid):
        i = np.floor(np.asarray(P, float)).astype(int)
        ok = np.all((i >= 0) & (i < np.array(grid.shape)), -1)
        out = np.ones(i.shape[:-1], bool)
        j = i[ok]
        out[ok] = grid[j[:, 0], j[:, 1], j[:, 2]]
        return out

    # ── hearth cells (own frame) ──
    hearth = hearth_cells(HB)
    hlab, hn = ndimage.label(_dense(hearth))

    # ── models ──
    src_cache = {}

    def src(w):
        if w not in src_cache:
            if w == HB['work']:
                src_cache[w] = np.array(sorted(hearth), float)
            else:
                src_cache[w] = np.loadtxt(os.path.join(SRC, w + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :3].astype(float)
        return src_cache[w]

    obst = S | gun_cells                    # doors placed first are added here as they go
    rows = []
    order = sorted(GB['models'], key=lambda m: 0 if m.get('door') else 1)
    for m in order:
        sc = list(m['scale']) if isinstance(m['scale'], list) else [m['scale']] * 3
        at = list(m['at'])
        if m.get('door') == 'wall':
            # height: from the floor up to the first solid over the panel, at most opening + 1 (Ship_Fittings 9.7: top row on the lintel)
            y0, y1 = m['opening'][0] - 1, m['opening'][1] + 1
            xw = int(math.floor(at[0]))
            h = 0
            while h < m['opening'][3] - m['opening'][2] + 2 and not S[xw, y0:y1 + 1, int(at[2]) + h].any():
                h += 1
            sc[2] = round(h / 32.0, 4)
            m['_h'] = h
        g = Model(src(m['work']), m['pivot'], sc, m['rotate'])
        if at[2] is None:
            bot = g.world(g.bottom, (at[0], at[1], 0.0))
            tp = decks[m['host']]
            under = [tp[c] for c in set(map(tuple, np.floor(bot[:, :2]).astype(int).tolist())) if c in tp]
            z0 = min(under) if under else 0
            zf = None
            for z in range(z0, z0 + 40):
                if hit(g.world(g.samples, (at[0], at[1], float(z))), obst).any():
                    continue
                below = g.world(g.bottom, (at[0], at[1], float(z)))
                below[:, 2] -= 0.5
                if hit(below, obst).any():
                    zf = z
                    break
            at[2] = float(zf if zf is not None else z0)
        if probe.get('shift', '').split(':')[0] == m['name']:
            at[0] += float(probe['shift'].split(':')[1])          # after z is measured (v1 shifted first ⇒ the z search lifted it clear)
        lo, hi = g.bbox(at)
        r = {'name': m['name'], 'host': m['host'], 'work': m['work'], 'at': r3(at), 'pivot': m['pivot'], 'scale': [round(v, 7) for v in sc],
             'rotate': m['rotate'], 'meta': dict(m['meta']), 'bbox': [r3(lo), r3(hi)]}
        for k in ('door', 'opening', 'wall_x', '_h'):
            if k in m:
                r[k.strip('_')] = m[k]
        r['_g'] = g
        rows.append(r)
        if m.get('door'):
            P = g.world(g.centers, at)
            i = np.floor(P).astype(int)
            obst[i[:, 0], i[:, 1], i[:, 2]] = True
    # barrels (in the magazine)
    BW = B['work']
    for i, b in enumerate(barrels):
        g = Model(src(BW), B['pivot'], B['scale'], 0)
        lo, hi = g.bbox(b['at'])
        rows.append({'name': '桶-%03d' % (i + 1), 'host': 'magazine', 'work': BW, 'at': r3(b['at']), 'pivot': B['pivot'], 'scale': [B['scale']] * 3, 'rotate': 0,
                     'meta': {'kind': 'powder', 'powder_lb': 100}, 'tier': b['tier'], 'bbox': [r3(lo), r3(hi)], '_g': g})
    if probe.get('nokind'):
        for r in rows:
            if r['name'] == probe['nokind']:
                r['meta'] = {k: v for k, v in r['meta'].items() if k != 'kind'}

    # ── readings per model: collisions (samples vs every solid incl. guns and the doors), foot, support ──
    RP = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
    ropes = [(rp['name'], np.array(RP['points'][rp['from']], float), np.array(RP['points'][rp['to']], float), rp['thickness'] / 2.0)
             for rp in RP['ropes'] if rp['from'] in RP['points'] and rp['to'] in RP['points']]
    LP = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
    door_cells = np.zeros(S.shape, bool)
    for r in rows:
        if r.get('door'):
            P = r['_g'].world(r['_g'].centers, r['at'])
            i = np.floor(P).astype(int)
            door_cells[i[:, 0], i[:, 1], i[:, 2]] = True
    coll, nofoot, nokind = {}, [], []
    for r in rows:
        g = r['_g']
        P = g.world(g.samples, r['at'])
        own = np.zeros(len(P), bool)
        if r.get('door'):
            # a door does not collide with itself in the obstacle grid: test against S | guns only
            k = int(hit(P, S | gun_cells).sum())
        else:
            k = int(hit(P, S | gun_cells | door_cells).sum())
        if k:
            coll[r['name']] = k
        lo, hi = np.array(r['bbox'][0]), np.array(r['bbox'][1])
        cx, cy, fz = int(math.floor((lo[0] + hi[0]) / 2)), int(math.floor((lo[1] + hi[1]) / 2)), int(math.floor(lo[2])) - 1
        d = next((dd for dd in range(0, GB['foot_reach'] + 1) if S[cx, cy, fz - dd]), None)
        r['foot_gap'] = d
        if d is None and not r.get('door'):
            nofoot.append(r['name'])
        bot = g.world(g.bottom, r['at'])
        bot[:, 2] -= 0.5
        r['support'] = round(float(hit(bot, S).mean()), 3)
        if 'kind' not in r['meta']:
            nokind.append(r['name'])
        # rope clearance (straight ropes; tube radius subtracted)
        best = (1e9, None)
        for nm, a, b, rad in ropes:
            dvec = b - a
            t = np.clip(((P - a) @ dvec) / max(dvec @ dvec, 1e-12), 0, 1)
            dist = np.linalg.norm(P - (a + t[:, None] * dvec), axis=1).min() - rad
            if dist < best[0]:
                best = (float(dist), nm)
        r['rope_clear'] = [round(best[0], 2), best[1]]
        r['gun_box_overlap'] = [n for n, a, b in gun_box if not (np.any(hi <= a) or np.any(b <= lo))]
        r['ladder_pts_in_box'] = [[ln, pk] for ln, v in LP.items() for pk, p in v['points'].items()
                                  if all(lo[i] <= p[i] + 0.5 <= hi[i] for i in range(3)) or (lo[0] <= p[0] + 0.5 <= hi[0] and lo[1] <= p[1] + 0.5 <= hi[1] and p[2] < hi[2] and p[2] + HEAD > lo[2])]
    # model vs model: centres of a in b's own cells
    overlap = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            (alo, ahi), (blo, bhi) = (np.array(a['bbox'][0]), np.array(a['bbox'][1])), (np.array(b['bbox'][0]), np.array(b['bbox'][1]))
            if np.any(ahi <= blo) or np.any(bhi <= alo):
                continue
            loc = b['_g'].local(a['_g'].world(a['_g'].centers, a['at']), b['at'])
            cells_b = set(map(tuple, b['_g'].cells.astype(int).tolist()))
            k = sum(1 for t_ in np.floor(loc).astype(int).tolist() if tuple(t_) in cells_b)
            if k:
                overlap.append([a['name'], b['name'], k])

    # ── walk cells (for galley faces and hoist heads): solid under, HEAD air, not inside a non-door model box ──
    box_solid = np.zeros(S.shape, bool)
    for r in rows:
        if r.get('door'):
            continue
        lo, hi = r['bbox']
        box_solid[int(math.floor(lo[0])):int(math.ceil(hi[0])), int(math.floor(lo[1])):int(math.ceil(hi[1])), int(math.floor(lo[2])):int(math.ceil(hi[2]))] = True
    for n, a, b in gun_box:
        box_solid[int(math.floor(a[0])):int(math.ceil(b[0])), int(math.floor(a[1])):int(math.ceil(b[1])), int(math.floor(a[2])):int(math.ceil(b[2]))] = True
    WS = S | box_solid

    def standable(x, y, z, head=HEAD):
        return 0 <= x < WS.shape[0] and 0 <= y < WS.shape[1] and 1 <= z < WS.shape[2] - head and WS[x, y, z - 1] and not WS[x, y, z:z + head].any()

    def near_stand(px, py, pz, rad, head=HEAD):
        best = None
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if dx * dx + dy * dy > rad * rad:
                    continue
                for dz in range(-3, 4):
                    if standable(px + dx, py + dy, pz + dz, head):
                        d = math.sqrt(dx * dx + dy * dy)
                        if best is None or d < best[0]:
                            best = (round(d, 2), [px + dx, py + dy, pz + dz])
        return best

    galley = {}
    for r in rows:
        if r['meta'].get('kind') != 'galley':
            continue
        lo, hi = np.array(r['bbox'][0]), np.array(r['bbox'][1])
        cxm, cym, zb = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, int(math.floor(lo[2]))
        faces = {'-x': (lo[0] - 2, cym), '+x': (hi[0] + 2, cym), '-y': (cxm, lo[1] - 2), '+y': (cxm, hi[1] + 2)}
        galley[r['name']] = {f: near_stand(int(math.floor(px)), int(math.floor(py)), zb, 6) for f, (px, py) in faces.items()}

    # ── hoist ladders: a 9x9 flat spot (0.8 m clear, no model or gun box) by the foot, a stand by the head ──
    def flat9(x0, y0, z):
        blk = WS[x0:x0 + 9, y0:y0 + 9, z - 1]
        return blk.shape == (9, 9) and blk.all() and not WS[x0:x0 + 9, y0:y0 + 9, z:z + BARREL_HEAD].any()

    hoist = {}
    for path in MG['hoist'].split(','):
        ln = path.rsplit('/', 1)[1]
        v = LP[ln]
        fx, fy, fz = v['points']['foot']
        best = None
        for x0 in range(fx - 20, fx + 12):
            for y0 in range(fy - 20, fy + 12):
                for z in (fz - 1, fz, fz + 1):
                    if flat9(x0, y0, z):
                        d = math.hypot(x0 + 4.5 - (fx + 0.5), y0 + 4.5 - (fy + 0.5))
                        if best is None or d < best[0]:
                            best = (round(d, 2), [x0, y0, z])
        hx, hy, hz = v['points']['head']
        hoist[path] = {'foot': v['points']['foot'], 'head': v['points']['head'], 'decks': v.get('decks'), 'up': v['group_up'],
                       'flat9_nearest': best, 'head_stand': near_stand(hx, hy, hz, 3)}

    # ── doors (Ship_Fittings 9.7) ──
    doors = {}
    deck_layer = {'main': 55}
    for r in rows:
        if not r.get('door'):
            continue
        lo, hi = np.array(r['bbox'][0]), np.array(r['bbox'][1])
        if r['door'] == 'hatch':
            ox0, ox1, oy0, oy1 = r['opening']
            fx0, fx1, fy0, fy1 = int(round(lo[0])), int(round(hi[0])) - 1, int(round(lo[1])), int(round(hi[1])) - 1
            zl = deck_layer[r['host']]
            under_air = [(x, y) for x in range(fx0, fx1 + 1) for y in range(fy0, fy1 + 1) if not S0[x, y, zl]]
            open_cells = [(x, y) for x in range(ox0, ox1 + 1) for y in range(oy0, oy1 + 1)]
            doors[r['name']] = {'box_cells': [fx0, fx1, fy0, fy1, int(round(lo[2])), int(round(hi[2])) - 1], 'margin': [ox0 - fx0, fx1 - ox1, oy0 - fy0, fy1 - oy1],
                                'air_under_in_deck_layer': len(under_air), 'opening_cells': len(open_cells),
                                'opening_all_air': all(not S0[x, y, zl] for x, y in open_cells), 'air_under_outside_opening': len(set(under_air) - set(open_cells)),
                                'rests_on': r['support']}
        else:
            y0, y1 = int(round(lo[1])), int(round(hi[1])) - 1
            z0, z1 = int(round(lo[2])), int(round(hi[2])) - 1
            wx = r['wall_x']
            frame = all(S0[wx, y, z] for y in (y0, y1) for z in range(z0, z1 + 1))
            hole = [(y, z) for y in range(y0, y1 + 1) for z in range(z0, z1 + 1) if not S0[wx, y, z]]
            doors[r['name']] = {'panel_cells': [int(round(lo[0])), y0, y1, z0, z1], 'height': r.get('h'), 'frame_cols_wall': frame,
                                'hole_cells': len(hole), 'hole_rows': len({z for _, z in hole}), 'hole_y': [min(y for y, _ in hole), max(y for y, _ in hole)] if hole else None,
                                'floor_under': all(S0[int(round(lo[0])), y, z0 - 1] for y in range(y0, y1 + 1)), 'gap_to_wall': int(round(lo[0])) - wx - 1}

    for r in rows:
        r.pop('_g')
    cen = np.array(sorted(free)).mean(axis=0)
    blast = min(free, key=lambda p: sum((p[i] - cen[i]) ** 2 for i in range(3)))
    door = (door_x, YC, F + 1)
    kinds = {}
    for r in rows:
        kinds[r['meta'].get('kind')] = kinds.get(r['meta'].get('kind'), 0) + 1
    hz = np.array(sorted(hearth))
    V = {'read': {'solid_cells': len(occ), 'gun_cells': int(gun_cells.sum()),
                  'component_sha256': {f: hashlib.sha256(open(os.path.join(SRC, f), 'rb').read()).hexdigest()[:16] for f in sorted(os.listdir(SRC))}},
         'magazine': {'cells': len(mag), 'colors': {str(c): sum(1 for q in mag.values() if q == c) for c in sorted(set(mag.values()))}, 'air_inside': len(free),
                      'x': [X0, X1], 'barrels': len(barrels), 'cap': MG['cap'], 'capacity_per_tier': capacity, 'tiers': [sum(1 for b in barrels if b['tier'] == t) for t in range(4)],
                      'rack': len(rack), 'powder_lb': len(barrels) * 100, 'blast': list(blast), 'door': list(door), 'pillar_x': [r['x'] for r in mlog if r['pillar']],
                      'x_skipped': [r['x'] for r in mlog if not r['cells']], 'vs_waterline': {'floor': F, 'ztop': ZTOP, 'waterline_z': plan['waterline']['z'], 'air_rows_below_wl': plan['waterline']['z'] - (F + 1), 'air_rows_above_wl': ZTOP - plan['waterline']['z'] + 1}},
         'skids': {'cells': len(skids)},
         'hearth': {'cells': len(hearth), 'size': (hz.max(0) - hz.min(0) + 1).tolist(), 'components': int(hn), 'smoke': HB['smoke'],
                    'smoke_air': tuple(HB['smoke']) not in hearth, 'smoke_over_pot_bottom': tuple(HB['smoke'][:2]) + (10,) in hearth,
                    'colors': {str(c): sum(1 for q in hearth.values() if q == c) for c in sorted(set(hearth.values()))}},
         'new_on_solid': len(on_solid), 'mag_skids_clash': len(clash), 'sealed': sealed, 'floating': floating,
         'models': len(rows), 'kinds': kinds, 'model_collisions': coll, 'no_foot_within_12': nofoot, 'no_kind': nokind,
         'model_overlap_pairs': len(overlap), 'model_overlap': overlap[:10],
         'gear': {r['name']: {k: r[k] for k in ('at', 'scale', 'bbox', 'foot_gap', 'support', 'rope_clear', 'gun_box_overlap', 'ladder_pts_in_box') if k in r}
                  for r in rows if r['host'] != 'magazine'},
         'barrels_min_rope_clear': min(r['rope_clear'][0] for r in rows if r['host'] == 'magazine') if barrels else None,
         'galley_faces': galley, 'hoist': hoist, 'doors': doors,
         'mirror_diff': {'magazine': sum(1 for (x, y, z), c in mag.items() if mag.get((x, 2 * YC - y, z)) != c),
                         'skids': sum(1 for (x, y, z), c in skids.items() if skids.get((x, 2 * YC - y, z)) != c),
                         'barrels': sum(1 for b in barrels if not any(abs(c['at'][0] - b['at'][0]) < 1e-6 and abs(2 * YC + 1 - c['at'][1] - b['at'][1]) < 1e-6 for c in barrels))}}
    if probe:
        out = {'probe': probe, 'model_collisions': coll, 'no_kind': nokind, 'overlap': overlap[:5],
               'doors': {k: {q: v[q] for q in ('margin', 'air_under_outside_opening', 'frame_cols_wall', 'hole_cells', 'gap_to_wall') if q in v} for k, v in doors.items()}}
        if 'cap' in probe:
            out['magazine'] = {k: V['magazine'][k] for k in ('barrels', 'tiers', 'capacity_per_tier', 'rack')}
        print(json.dumps(out, ensure_ascii=False))
        return
    od = os.path.join(M, 'gear')
    os.makedirs(od, exist_ok=True)
    lists = {}
    for nm, part, head in (('magazine', mag, '# 星辰號 彈藥庫（世界座標、at 0,0,0；draft_gear.py）\n'),
                           ('skids', skids, '# 星辰號 小艇架（世界座標、at 0,0,0；draft_gear.py）\n'),
                           ('hearth', hearth, '# 星辰號 沙箱灶（自己的 0.05 m 框、原點 ＝ 子作品原點；draft_gear.py）\n')):
        p = os.path.join(od, nm + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for (x, y, z), c in sorted(part.items()):
                f.write('%d,%d,%d,%d\n' % (x, y, z, c))
        lists[nm] = [len(part), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    V['lists'] = lists
    place = {'note': 'draft_gear.py 的結果；模型 at ＝ pivot 落點（世界座標；host 子作品都在 0,0,0）；桶掛在彈藥庫子作品',
             'magazine': {'work': MG['work'], 'link': MG['link'], 'anchors': {'blast': list(blast), 'door': list(door)},
                          'meta': {'kind': 'magazine', 'pos': MG['pos'], 'powder_lb': len(barrels) * 100, 'hoist': MG.get('hoist_ids', MG['hoist'])}},
             'skids': {'work': SK['work'], 'link': SK['link']},
             'hearth': {'work': HB['work'], 'anchors': {'smoke': HB['smoke']}},
             'models': [{k: v for k, v in r.items() if k not in ('foot_gap', 'support', 'rope_clear', 'gun_box_overlap', 'ladder_pts_in_box')} for r in rows]}
    json.dump(place, open(os.path.join(design, 'gear_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(V, open(os.path.join(design, 'verify_gear.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    sheet(design, S0, mag, skids, hearth, rows, barrels, B, HB, MG, SK, YC)
    print(json.dumps({k: V[k] for k in V if k not in ('gear', 'read', 'lists')}, ensure_ascii=False))
    print(json.dumps(V['gear'], ensure_ascii=False))


def _dense(cells):
    a = np.array(list(cells))
    D = np.zeros(a.max(0) + 1, bool)
    D[a[:, 0], a[:, 1], a[:, 2]] = True
    return D


def sheet(design, S0, mag, skids, hearth, rows, barrels, B, HB, MG, SK, YC):
    """Sheet 08: orlop plan at the magazine, main-deck waist and well from above, the hearth (top + side)."""
    W, Hh = 1700, 1180
    im = Image.new('RGB', (W, Hh), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 12), '星辰號 新圖紙 08：彈藥庫與甲板物件（TASK-0019 步驟 10；draft_gear.py）', fill=(0, 0, 0), font=font(22))

    def panel(ox, oy, xr, yr, k, top_of, title):
        d.text((ox, oy - 26), title, fill=(0, 0, 0), font=font(16))
        for x in range(*xr):
            for y in range(*yr):
                c = top_of(x, y)
                if c is not None:
                    px, py = ox + (x - xr[0]) * k, oy + (yr[1] - 1 - y) * k
                    d.rectangle([px, py, px + k - 1, py + k - 1], fill=c)
        return lambda x, y: (ox + (x - xr[0]) * k, oy + (yr[1] - y) * k)

    # (a) orlop at the magazine: slice z = floor + 3
    zs = MG['floor'] + 3

    def top_a(x, y):
        if (x, y, zs) in mag:
            return palette_rgb(mag[(x, y, zs)])
        if (x, y, MG['floor']) in mag:
            return palette_rgb(mag[(x, y, MG['floor'])])
        if S0[x, y, zs]:
            return (120, 120, 120)
        return None
    to = panel(40, 90, (86, 160), (30, 131), 6, top_a, '(a) 底艙平台 z %d 切面：彈藥庫 x %d–%d、火藥桶 %d（圓）、後桅腳在房間裡' % (zs, MG['x0'], MG['x1'], len(barrels)))
    Rb = B['d'] * B['mpv'] / 0.1 / 2
    for b in barrels:
        px, py = to(b['at'][0], b['at'][1])
        d.ellipse([px - Rb * 6, py - Rb * 6, px + Rb * 6, py + Rb * 6], outline=(150, 20, 20), width=2)
    # (b) main deck waist + well from above
    by_name = {r['name']: r for r in rows}

    def top_b(x, y):
        for z in range(90, 40, -1):
            if (x, y, z) in skids:
                return palette_rgb(skids[(x, y, z)])
            if S0[x, y, z]:
                return palette_rgb(209) if z <= 58 else (140, 140, 140)
        return None
    tb = panel(560, 90, (196, 336), (30, 131), 6, top_b, '(b) 主甲板 x 196–335 俯視：艙蓋、小艇（外框）、小艇架、沙箱灶')
    for r in rows:
        if r['host'] == 'magazine' or r['host'] == 'poop' or r['name'].startswith('門'):
            continue
        lo, hi = r['bbox']
        if lo[0] < 196:
            continue
        a, b_ = tb(lo[0], hi[1]), tb(hi[0], lo[1])
        col = {'door': (30, 90, 200), 'boat': (200, 40, 40), 'galley': (230, 120, 0)}.get(r['meta']['kind'], (0, 0, 0))
        d.rectangle([a[0], a[1], b_[0], b_[1]], outline=col, width=3)
        d.text((a[0] + 4, a[1] + 4), r['name'], fill=col, font=font(14))
    # (c) the hearth, top and side (k = 14 px per 0.05 m cell)
    hz = max(z for (_, _, z) in hearth)

    def top_h(x, y):
        for z in range(hz, -1, -1):
            if (x, y, z) in hearth:
                return palette_rgb(hearth[(x, y, z)])
        return None
    panel(40, 820, (0, HB['size'][0]), (0, HB['size'][1]), 14, top_h, '(c) 沙箱灶 俯視（0.05 m／格；船上縮 0.5 ⇒ 1.2 × 1.0 m）')

    def side_h(x, z):
        for y in range(0, HB['size'][1]):
            if (x, y, z) in hearth:
                return palette_rgb(hearth[(x, y, z)])
        return None
    ts = panel(440, 900, (0, HB['size'][0]), (0, hz + 2), 14, side_h, '(c\') 沙箱灶 側視（−y 往 +y 看）；× ＝ smoke 固定點')
    sx, sz = HB['smoke'][0], HB['smoke'][2]
    px, py = ts(sx + 0.5, sz + 0.5)
    d.line([px - 8, py - 8, px + 8, py + 8], fill=(200, 0, 0), width=3)
    d.line([px - 8, py + 8, px + 8, py - 8], fill=(200, 0, 0), width=3)
    d.text((900, 820), '\n'.join([
        '模型（at ＝ pivot 落點，z 由程式量）：',
        *['  %s：%s × %s、z %s' % (r['name'], r['work'].split('-01m-')[-1], r['scale'][0] if len(set(r['scale'])) == 1 else r['scale'], r['at'][2])
          for r in rows if r['host'] != 'magazine'],
        '  火藥桶 %d（%d 磅）：憲法號 -powder-barrel × 0.2' % (len(barrels), len(barrels) * 100),
        'hoist：' + MG['hoist'],
        '不放絞盤（PT：用大滑車組起錨）']), fill=(0, 0, 0), font=font(15))
    im.save(os.path.join(design, 'sheet08_gear_v1.png'))


if __name__ == '__main__':
    main()
