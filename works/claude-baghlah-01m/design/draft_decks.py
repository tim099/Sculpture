# Source: calli-cosecha-01m/design/draft_decks.py (Harvest, TASK-0593) -- adapted for the Star (TASK-0019 step 5)
# Star (al-Najm) new sheet 03: decks (hold platform, main deck with sheer and fore well, poop + steering platform),
#   cargo hatch, mast holes, stern-cabin bulkhead, step, breast rail, ladders, ladder points, deck meta.
#   Input:  plan.json (decks, decks_build, masts, ports) + the step-4 hull (draft_ports.build: what is on the work)
#   Output: masks/decks/<group>.vox.txt, masks/ladders/<up group>.vox.txt (world coords, at 0,0,0),
#           ladder_points.json, decks_meta.tsv, verify_decks.json, sheet03_decks_v1.png
#   Usage:  python -X utf8 draft_decks.py <design> [--probe=drop_ladder=<name>[,<name>]] [--probe=quarter_z=<z>]  (probes never write)
#   Differences from Harvest:
#   * layout.deck_z is the standing cell (first air); the plank is one cell below it.
#   * Planks step with the sheer / fore well column by column; a riser fills any drop of 2+ so the deck stays closed.
#   * Wells open only where a climber's head would hit the upper deck, up to the last tread (Ship_Decks "opening a hatch").
#   * Walk check: our own nav grid (1.2 m headroom, step <= 0.3 m, never on a ladder) split into decks by floor,
#     joined by ladders (Ship_Decks 9.3 checks 4, 5, 6 approximated; Blockside is not on this host).
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from draft_ports import build

HEAD = 12      # nav headroom (1.2 m)
STEP_HOLD = 6  # hold: Ship_Decks 6 joins hold areas with steps <= 0.6 m
HEAD_PT = 14   # ladder points: Harvest checks 14 cells over each point
STEP = 3       # nav step (0.3 m)


def row_span(plan, L, inside, x0, key):
    row = LY.deck_row(plan, key)
    a = row.get('x_from', -10 ** 6)
    b = row.get('x_to', 10 ** 6)
    return a, b


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probes = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
    plan = HL.load_plan(design)
    if 'quarter_z' in probes:
        LY.deck_row(plan, 'quarter')['z'] = int(probes['quarter_z'])
    H = build(plan)
    L, x0, ylo, S, wall, keep = H['L'], H['x0'], H['ylo'], H['S'], H['wall'], H['keep']
    YC = L.YC
    inside = S & ~wall
    nx, ny, nz = S.shape
    X = np.arange(nx) + x0
    Y = np.arange(ny) + ylo
    DY = Y - YC
    B = plan['decks_build']
    G = B['groups']
    gof = {r: g['key'] for g in G for r in g['rows']}
    rows = [r for g in G for r in g['rows']]
    zstand = {k: LY.deck_z(plan, k, X + 0.5).astype(int) for k in rows}
    # Bow: forward of the fore well the raked stem's inner face rises above the well plank ⇒ the main-deck plank
    # follows the bottom of that wedge (lowest inside cell on the centreline), so the forepeak is deck, not hold.
    yc0 = YC - ylo
    low_c = np.array([np.nonzero(inside[xi, yc0, :])[0][0] if inside[xi, yc0, :].any() else -1 for xi in range(nx)])
    bow = (X > B['bow_from_x']) & (low_c + 1 > zstand['main'])
    zstand['main'] = np.where(bow, low_c + 1, zstand['main'])
    span = {k: row_span(plan, L, inside, x0, k) for k in rows}
    inspan = {k: (X >= span[k][0]) & (X <= span[k][1]) for k in rows}

    LD = B['ladders']
    ladders = [dict(l) for l in LD['list']]
    if 'drop_ladder' in probes:
        ladders = [l for l in ladders if l['name'] not in probes['drop_ladder'].split(',')]
    th, rise, run = LD['tread_half'], LD['rise'], LD['run']

    def lower_stand(ld):
        """First air of the lower end: a deck row, or 'hold' = top of the inner bottom at the foot column."""
        xf = ld['xs'] - ld['dir'] - x0
        if ld['lo'] == 'hold':
            # v1 took the lowest inside cell on the centreline: a 1-cell groove by the keel (verifier, step 5).
            # Now: the first z where the hold is wide enough for the ladder (|dy| <= th + 2) -- a sole is laid under it.
            yc_ = YC + ld['dy']
            band = np.abs(Y - yc_) <= th + 2
            return int(next(z for z in range(nz) if inside[xf, band, z].all()))
        return int(zstand[ld['lo']][xf])

    # Ladder geometry first (wells depend on it)
    geo = []
    for ld in ladders:
        s, xs = ld['dir'], ld['xs']
        zl = lower_stand(ld)
        top_end = None
        # upper stand at the column just past the top tread
        guess_n = None
        for _ in range(3):
            xe = xs + s * (run * (guess_n or 4) + run - 1) + s
            zu = int(zstand[ld['up']][xe - x0])
            n = (zu - zl - 1) // rise
            if n == guess_n:
                break
            guess_n = n
        top_end = xs + s * (run * n + run - 1)
        zu = int(zstand[ld['up']][top_end + s - x0])
        head_x = top_end + s * LD['head_back']
        beam_bot = zu - 1 - B['beam']['depth'][ld['up']]
        k0 = next(k for k in range(0, n + 1) if zl + rise * k + HEAD_PT - 1 >= beam_bot)
        start = xs + s * run * k0
        geo.append(dict(ld, zl=zl, zu=zu, n=n, top_end=top_end, head_x=head_x, k0=k0, well_from=start))

    # Openings per row: hatches, ladder wells, mast holes; coamings
    hole = {k: np.zeros((nx, ny), bool) for k in rows}
    coam = {k: np.zeros((nx, ny), bool) for k in rows}
    for h in B['hatches']:
        m = (X[:, None] >= h['x0']) & (X[:, None] <= h['x1']) & (np.abs(DY)[None, :] <= h['half'])
        ring = (X[:, None] >= h['x0'] - 1) & (X[:, None] <= h['x1'] + 1) & (np.abs(DY)[None, :] <= h['half'] + 1) & ~m
        for k in h['rows']:
            hole[k] |= m
            coam[k] |= ring
    for g in geo:
        if not g.get('well'):
            continue
        s, yc = g['dir'], YC + g['dy']
        xa, xb = sorted((g['well_from'], g['top_end']))
        m = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - yc)[None, :] <= th + 2)
        hole[g['up']] |= m
        side = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - yc)[None, :] == th + 3)
        low_end = (X[:, None] == g['well_from'] - s) & (np.abs(Y - yc)[None, :] <= th + 3)
        coam[g['up']] |= side | low_end
    MR = B['mast_r']
    heel_z = {}
    for m in plan['masts']['rows']:
        if m['key'] not in MR:
            continue
        xm = m['x_step']
        if 'heel_z' in m:
            hz = m['heel_z']
        else:
            hz = int(zstand[m['heel_deck']][xm - x0])
        heel_z[m['key']] = hz
        disk = (X[:, None] - xm) ** 2 + (Y[None, :] - YC) ** 2 <= MR[m['key']] ** 2
        for k in rows:
            if inspan[k][xm - x0] and zstand[k][xm - x0] > hz:
                hole[k] |= disk
    for k in rows:
        coam[k] &= ~hole[k]

    # Decks: plank (+ riser where the next column steps down 2+), beams, coamings
    cells = {g['key']: np.zeros(S.shape, np.uint8) for g in G}
    P = B['plank']
    for k in rows:
        c = cells[gof[k]]
        pc = P['weather'] if k in P['weather_rows'] else P['interior']
        bd = B['beam']['depth'][k]
        zp = zstand[k] - 1
        for xi in range(nx):
            if not inspan[k][xi]:
                continue
            z = zp[xi]
            zlo = z
            for nb in (xi - 1, xi + 1):
                if 0 <= nb < nx and inspan[k][nb]:
                    zlo = min(zlo, zp[nb] + 1)
            for zz in range(zlo, z + 1):
                r = inside[xi, :, zz] & ~hole[k][xi]
                c[xi, r, zz] = pc
            if bd and (X[xi] % B['beam']['every']) < B['beam']['w']:
                for dz in range(1, bd + 1):
                    r = inside[xi, :, zlo - dz] & ~hole[k][xi] & (c[xi, :, zlo - dz] == 0)
                    c[xi, r, zlo - dz] = B['beam']['color']
            for dz in range(1, B['coaming_h'] + 1):
                r = inside[xi, :, z + dz] & coam[k][xi]
                c[xi, r, z + dz] = B['trim']

    # Stern-cabin bulkhead with a door; step; breast rail with ladder gaps (all on the poop group)
    for br in B['breaks']:
        xi = br['x'] - x0
        zl = int(zstand[br['lo']][xi])
        zu = int(zstand[br['up']][xi])
        door = np.abs(DY) <= br['door_half']
        c = cells[gof[br['up']]]
        for z in range(zl, zu - 1):
            r = inside[xi, :, z] & ~(door & (z < zl + br['door_h'])) & (c[xi, :, z] == 0)
            c[xi, r, z] = B['trim']
    st = B['step']
    c = cells['poop']
    for x in range(st['x0'], st['x1'] + 1):
        for z in range(st['z0'], st['z1'] + 1):
            r = inside[x - x0, :, z] & (c[x - x0, :, z] == 0)
            c[x - x0, r, z] = B['trim']
    bw = B['breast_rail']
    gap = np.zeros(ny, bool)
    for g in geo:
        if gof[g['up']] == 'poop' and g['lo'] != 'hold':
            gap |= np.abs(Y - (YC + g['dy'])) <= th + 1
    for z in range(bw['z0'], bw['z0'] + bw['h']):
        r = inside[bw['x'] - x0, :, z] & ~gap
        c[bw['x'] - x0, r, z] = B['trim']

    # Ladders: treads every `rise`, `run` long; stringers on both sides
    LC = LD['color']
    lad, pts = {}, {}
    for g in geo:
        up = gof[g['up']]
        cl = lad.setdefault(up, np.zeros(S.shape, np.uint8))
        s, xs, n, zl, zu = g['dir'], g['xs'], g['n'], g['zl'], g['zu']
        yc = YC + g['dy']
        yi = yc - ylo
        for kk in range(0, n + 2):
            xa = xs + s * run * kk
            xr = sorted((xa, xa + s * (run - 1)))
            zt = zl - 1 + rise * kk
            for xx in range(xr[0], xr[1] + 1):
                if 1 <= kk <= n:
                    cl[xx - x0, yi - th:yi + th + 1, zt] = LC
                if kk == 0:
                    zlo_, zhi_ = zl, zl + 2
                elif kk <= n:
                    zlo_, zhi_ = zt - 3, zt
                else:
                    zlo_, zhi_ = zl - 1 + rise * n - 3, zu - 1
                for z in range(max(zlo_, 0), zhi_ + 1):
                    for yy in (yi - th - 1, yi + th + 1):
                        cl[xx - x0, yy, z] = LC
        pts[g['name']] = {'up': g['up'], 'lo': g['lo'], 'group_up': up, 'steps': n, 'decks': g.get('decks'),
                          'points': {'foot': [xs - s, yc, zl], 'lo': [xs + s * run, yc, zl + rise],
                                     'hi': [xs + s * run * n, yc, zl + rise * n], 'head': [g['head_x'], yc, zu]}}
        if g['lo'] == 'hold':
            # hold sole: fill the V bottom under the foot and the first treads up to the foot level (ceiling boards)
            xa_, xb_ = sorted((xs - s * LD['sole_back'], xs + s * (run * LD['sole_treads'] + run - 1)))
            for xx in range(xa_, xb_ + 1):
                for z in range(0, zl):
                    r = inside[xx - x0, :, z] & (np.abs(Y - yc) <= th + 2)
                    cl[xx - x0, r, z] = B['trim']
    anyd = np.zeros(S.shape, bool)
    for c in cells.values():
        anyd |= c > 0
    for k in lad:
        lad[k][anyd | keep | ~inside] = 0      # decks and hull win; nothing outside the hold (v1: 4 stringer cells poked through the bottom)

    # Sealed cavities (hull + decks + ladders): fill with beam colour into the nearest deck group
    uni = keep.copy()
    for c in list(cells.values()) + list(lad.values()):
        uni |= c > 0
    cav = ndimage.binary_fill_holes(uni) & ~uni
    labc, ncav = ndimage.label(cav)
    filled = []
    for i in range(1, ncav + 1):
        idx = np.argwhere(labc == i)
        xm, zm = int(np.median(idx[:, 0])), float(np.median(idx[:, 2]))
        k = min(rows, key=lambda kk: abs(zstand[kk][xm] - zm) + (0 if inspan[kk][xm] else 1000))
        cells[gof[k]][labc == i] = B['beam']['color']
        filled.append({'group': gof[k], 'cells': int(len(idx)), 'x': [int(idx[:, 0].min() + x0), int(idx[:, 0].max() + x0)],
                       'z': [int(idx[:, 2].min()), int(idx[:, 2].max())]})

    # ---------------- readings ----------------
    R = {'groups': {}, 'ladders': {}}
    allc = np.zeros(S.shape, np.int16)
    for k, c in cells.items():
        m = c > 0
        R['groups'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & keep).sum()), 'outside_hull': int((m & ~S).sum()),
                          'colors': {int(a): int(b) for a, b in zip(*np.unique(c[m], return_counts=True))},
                          'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    for k, c in lad.items():
        m = c > 0
        R['ladders'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & keep).sum()), 'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    R['overlap_between_parts'] = int((allc > 1).sum())
    R['parts_outside_inside'] = int(((allc > 0) & ~inside).sum())
    occ = keep | (allc > 0)
    ladm = np.zeros(S.shape, bool)
    for c in lad.values():
        ladm |= c > 0
    R['structure_all'] = {'components_6': int(ndimage.label(occ)[1]),
                          'cavities': int((ndimage.binary_fill_holes(occ) & ~occ).sum()),
                          'mirror_diff': int((occ != occ[:, ::-1, :]).sum())}
    if probes.get('with_later') in ('1', '2', '3', '4'):     # (4 = + step 11 masks/helm, anchor boxes, trunk carved) step 7 (+ step 8 masks/rigging, step 9 masks/gunfittings, step 10 masks/gear): re-run walk / ladder points with every later part in the ship (never writes)
        from draft_masts import ship_cells
        later = set(ship_cells(design, plan))
        listed = lambda sub: sorted(os.listdir(os.path.join(design, 'masks', sub))) if os.path.isdir(os.path.join(design, 'masks', sub)) else []
        for sub, f in [('masts', f) for f in listed('masts')] + [('rigging', f) for f in listed('rigging')] + [('gunfittings', f) for f in listed('gunfittings')]:
            for l in open(os.path.join(design, 'masks', sub, f), encoding='utf-8'):
                if l.strip() and not l.startswith('#'):
                    later.add(tuple(map(int, l.split(',')[:3])))
        if probes['with_later'] in ('3', '4'):
            # step 10: magazine walls + boat skids (world lists; hearth.vox.txt is a model source in its own frame, not here) and
            # every non-door model box (barrels, boat, binnacle, hearth); doors are passages (Ship_Fittings 9.7) ⇒ not solid
            for f in ('magazine', 'skids'):
                for l in open(os.path.join(design, 'masks', 'gear', f + '.vox.txt'), encoding='utf-8'):
                    if l.strip() and not l.startswith('#'):
                        later.add(tuple(map(int, l.split(',')[:3])))
            for r in json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))['models']:
                if r['meta'].get('kind') == 'door':
                    continue
                lo, hi = r['bbox']
                for x in range(int(math.floor(lo[0])), int(math.ceil(hi[0]))):
                    for y in range(int(math.floor(lo[1])), int(math.ceil(hi[1]))):
                        for z in range(int(math.floor(lo[2])), int(math.ceil(hi[2]))):
                            later.add((x, y, z))
        if probes['with_later'] in ('2', '3', '4') and os.path.exists(os.path.join(design, 'guns_placement.json')):
            # step 9: the crew walk around every model box (Ship_Turrets 4.6 step 5) ⇒ fill each gun's box as solid
            for r in json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']:
                lo, hi = r['bbox']
                for x in range(int(math.floor(lo[0])), int(math.ceil(hi[0]))):
                    for y in range(int(math.floor(lo[1])), int(math.ceil(hi[1]))):
                        for z in range(int(math.floor(lo[2])), int(math.ceil(hi[2]))):
                            later.add((x, y, z))
        cut = set()
        if probes['with_later'] == '4':
            # step 11: rudder + tiller (models, world cells), collar, stem rollers; anchor boxes; the trunk carved off the hull / poop deck
            for f in ('rudder', 'tiller', 'fittings', 'rollers'):
                for l in open(os.path.join(design, 'masks', 'helm', f + '.vox.txt'), encoding='utf-8'):
                    if l.strip() and not l.startswith('#'):
                        later.add(tuple(map(int, l.split(',')[:3])))
            HP = json.load(open(os.path.join(design, 'helm_placement.json'), encoding='utf-8'))
            for r in HP['anchors']:
                lo, hi = r['bbox']
                for x in range(int(math.floor(lo[0])), int(math.ceil(hi[0]))):
                    for y in range(int(math.floor(lo[1])), int(math.ceil(hi[1]))):
                        for z in range(int(math.floor(lo[2])), int(math.ceil(hi[2]))):
                            later.add((x, y, z))
            for rel in HP['carve'].values():
                for l in open(os.path.join(design, 'masks', rel + '.vox.txt'), encoding='utf-8'):
                    if l.strip() and not l.startswith('#'):
                        cut.add(tuple(map(int, l.split(',')[:3])))
        added = 0
        for (x, y, z) in later:
            if 0 <= x - x0 < nx and 0 <= y - ylo < ny and 0 <= z < nz and not occ[x - x0, y - ylo, z]:
                occ[x - x0, y - ylo, z] = True
                added += 1
        removed = 0
        for (x, y, z) in cut - later:
            if 0 <= x - x0 < nx and 0 <= y - ylo < ny and 0 <= z < nz and occ[x - x0, y - ylo, z]:
                occ[x - x0, y - ylo, z] = False
                removed += 1
        R['with_later_added'] = added
        R['with_later_removed'] = removed

    # deck meta floor ("x:z" first air), from the plank cells actually written
    meta = {}
    for g in G:
        pts_xz = []
        for k in g['rows']:
            c = cells[g['key']]
            for xi in range(nx):
                if inspan[k][xi] and (c[xi, :, zstand[k][xi] - 1] > 0).any():
                    pts_xz.append((int(X[xi]), int(zstand[k][xi])))
        # step: first air on top of the step block
        pts_xz.sort()
        if g['key'] == 'poop':
            pts_xz = [(x, st['z1'] + 1) if st['x0'] <= x <= st['x1'] else (x, z) for x, z in pts_xz]
        comp = []
        for i, (x, z) in enumerate(pts_xz):
            prev = pts_xz[i - 1][1] if i else None
            nxt = pts_xz[i + 1][1] if i + 1 < len(pts_xz) else None
            if prev != z or nxt != z:
                comp.append('%d:%d' % (x, z))
        meta[g['key']] = {'kind': 'deck', 'deck': g['key'], 'level': g['level'], 'name': g['name'], 'floor': ','.join(comp), 'thick': g['thick']}
    R['deck_meta'] = meta

    def floor_at(gk, x):
        f = [tuple(map(int, p.split(':'))) for p in meta[gk]['floor'].split(',')]
        if x < f[0][0] or x > f[-1][0]:
            return None
        for (xa, za), (xb, zb) in zip(f, f[1:]):
            if xa <= x <= xb:
                return za if xb == xa else za + (zb - za) * (x - xa) / (xb - xa)
        return f[0][1]

    # ladder points: air, solid below, headroom; check 4 (top to head walkable within the tread width)
    probs = []
    for nm, v in pts.items():
        for pk, (px, py, pz) in v['points'].items():
            xi_, yi_ = px - x0, py - ylo
            air = not occ[xi_, yi_, pz]
            flo = bool(occ[xi_, yi_, pz - 1])
            hd = int(occ[xi_, yi_, pz:pz + HEAD_PT].sum())
            if not (air and flo) or hd:
                probs.append([nm, pk, [px, py, pz], air, flo, hd])
        hx, hz = v['points']['hi'][0], v['points']['hi'][2]
        ex, ez = v['points']['head'][0], v['points']['head'][2]
        s = 1 if ex > hx else -1
        run_empty, worst = 0, 0
        for x in range(hx + s, ex + s, s):
            ok = False
            for dy in range(-1, 2):
                yi_ = v['points']['head'][1] + dy - ylo
                for z in range(ez - 3, ez + 4):
                    if occ[x - x0, yi_, z - 1] and not occ[x - x0, yi_, z:z + HEAD].any():   # treads count here (Ship_Decks 4)
                        ok = True
            run_empty = 0 if ok else run_empty + 1
            worst = max(worst, run_empty)
        v['top_gap_cols'] = worst
    R['ladder_point_problems'] = probs

    # nav grid: stand where solid below, HEAD air above, standing cell inside the hull, not on a ladder
    st_ok = np.zeros(S.shape, bool)
    airrun = np.zeros(S.shape, np.int16)
    for z in range(nz - 1, -1, -1):
        airrun[:, :, z] = np.where(occ[:, :, z], 0, (airrun[:, :, z + 1] + 1) if z + 1 < nz else 1)
    st_ok[:, :, 1:] = occ[:, :, :-1] & ~ladm[:, :, :-1] & (airrun[:, :, 1:] >= HEAD) & inside[:, :, 1:]
    idx = np.argwhere(st_ok)
    nid = -np.ones(S.shape, np.int64)
    nid[tuple(idx.T)] = np.arange(len(idx))
    ea, eb, edz = [], [], []
    for dx, dyy in ((1, 0), (0, 1)):
        for dz in range(-STEP_HOLD, STEP_HOLD + 1):
            a = idx
            b = a + [dx, dyy, dz]
            ok = (b[:, 0] < nx) & (b[:, 1] < ny) & (b[:, 2] >= 0) & (b[:, 2] < nz)
            a, b = a[ok], b[ok]
            j = nid[tuple(b.T)]
            ok = j >= 0
            ea.append(nid[tuple(a[ok].T)])
            eb.append(j[ok])
            edz.append(np.full(int(ok.sum()), abs(dz)))
    ea, eb, edz = np.concatenate(ea), np.concatenate(eb), np.concatenate(edz)

    def comps(extra):
        same = (deck_of[ea] == deck_of[eb]) & ((edz <= STEP) | (deck_of[ea] == 'hold'))   # split by deck first; only ladders join decks
        e1 = np.concatenate([ea[same]] + [np.array([p for p, q in extra], np.int64)])
        e2 = np.concatenate([eb[same]] + [np.array([q for p, q in extra], np.int64)])
        M = coo_matrix((np.ones(len(e1)), (e1, e2)), shape=(len(idx), len(idx)))
        return connected_components(M, directed=False)[1]
    # which deck each standable cell belongs to (floor -3..+20, nearest floor wins); below the lowest floor = hold
    gx = idx[:, 0] + x0
    deck_of = np.full(len(idx), '', object)
    best = np.full(len(idx), 1e9)
    for g in G:
        fl = np.array([floor_at(g['key'], x) if floor_at(g['key'], x) is not None else np.nan for x in range(x0, x0 + nx)])
        f = fl[idx[:, 0]]
        d = idx[:, 2] - f
        ok = ~np.isnan(f) & (d >= -3) & (d <= 20) & (np.abs(d) < best)
        deck_of[ok] = g['key']
        best[ok] = np.abs(d[ok])
    lowest = np.array([min([floor_at(g['key'], x) for g in G if floor_at(g['key'], x) is not None] or [1e9]) for x in range(x0, x0 + nx)])
    hold = (deck_of == '') & (idx[:, 2] < lowest[idx[:, 0]] - 3)
    deck_of[hold] = 'hold'

    def nearest(p, want):
        x, y, z = p
        best_, bd_ = None, 1e9
        for dx in range(-10, 11):
            for dyy in range(-10, 11):
                for dz in range(-3, 4):
                    xi_, yi_, zi_ = x - x0 + dx, y - ylo + dyy, z + dz
                    if 0 <= xi_ < nx and 0 <= yi_ < ny and 0 <= zi_ < nz and nid[xi_, yi_, zi_] >= 0:
                        j = nid[xi_, yi_, zi_]
                        if deck_of[j] != want:
                            continue
                        dd = dx * dx + dyy * dyy + dz * dz
                        if dd < bd_:
                            best_, bd_ = j, dd
        return best_, bd_ ** 0.5 if best_ is not None else None
    links, link_rd = [], {}
    for nm, v in pts.items():
        lo_g = 'hold' if v['lo'] == 'hold' else gof[v['lo']]
        a, da = nearest(v['points']['foot'], lo_g)
        b, db = nearest(v['points']['head'], v['group_up'])
        link_rd[nm] = {'foot_to_walk': da, 'head_to_walk': db}
        if a is not None and b is not None:
            links.append((a, b))
    lab = comps(links)
    sizes = np.bincount(lab)
    trunk = int(np.argmax(sizes))
    walk = {}
    for gk in [g['key'] for g in G] + ['hold']:
        sel = deck_of == gk
        if probes.get('surface') and gk != 'hold':      # probe surface=1: only cells within 4 of the deck floor (drops the tops of model boxes)
            sel &= best <= 4
        cols = lambda m: len({(int(a), int(b)) for a, b in idx[m][:, :2]})
        tot, got = cols(sel), cols(sel & (lab == trunk))
        chunks = []
        for c_ in np.unique(lab[sel & (lab != trunk)]):
            mm = sel & (lab == c_)
            area = cols(mm)
            if area >= int(probes.get('chunk_cols', 200)):              # probe chunk_cols: list smaller pieces too
                chunks.append({'m2': area / 100.0, 'x': [int(idx[mm][:, 0].min() + x0), int(idx[mm][:, 0].max() + x0)],
                               'z': [int(idx[mm][:, 2].min()), int(idx[mm][:, 2].max())]})
        walk[gk] = {'m2': tot / 100.0, 'reached_m2': got / 100.0, 'unreached_chunks_ge_2m2': chunks}
    R['walk'] = walk
    R['ladder_links'] = link_rd

    # ports: nothing of ours in front of a port (inboard 8 cells from the inner face)
    blocked = []
    parts = allc > 0
    for p in LY.ports(plan):
        zc = (p['z0'] + p['z1']) // 2
        for sg in (1, -1):
            n = 0
            for x in range(p['x0'], p['x1'] + 1):
                ys = [y for y in range(ny) if (Y[y] - YC) * sg > 0 and wall[x - x0, y, zc]]
                yin = min(ys, key=lambda y: abs(Y[y] - YC))
                rng = range(yin - sg * 8, yin) if sg > 0 else range(yin + 1, yin + 9)
                for yy in rng:
                    n += int(parts[x - x0, yy, p['z0']:p['z1'] + 1].sum())
            if n:
                blocked.append([p['i'], 'S' if sg > 0 else 'P', n])
    R['ports_blocked_inside'] = blocked
    sc = []
    for s_ in LY.scuppers(plan):
        xm = (s_['x0'] + s_['x1']) // 2
        sc.append({'i': s_['i'], 'scupper_z0': s_['z0'], 'deck_first_air': int(zstand['main'][xm - x0])})
    R['scuppers_flush'] = sc
    R['holes'] = {k: int(hole[k].sum()) for k in rows}
    R['cavities_filled'] = filled
    R['ladders_geo'] = {g['name']: {'n': g['n'], 'zl': g['zl'], 'zu': g['zu'], 'top_end': g['top_end'], 'head_x': g['head_x'],
                                    'well': [g['well_from'], g['top_end']] if g.get('well') else None} for g in geo}
    R['ladder_points'] = pts
    R['mast_heel_z'] = heel_z
    if probes:
        print(json.dumps({'probe': probes, 'walk': {k: [v['m2'], v['reached_m2']] + ([v['unreached_chunks_ge_2m2']] if v['unreached_chunks_ge_2m2'] else []) for k, v in walk.items()},
                          'ladder_point_problems': probs, 'top_gap': {k: v['top_gap_cols'] for k, v in pts.items()},
                          'ports_blocked_inside': blocked}, ensure_ascii=False))
        return

    def dump(path, c, head):
        ii = np.argwhere(c > 0)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for a, b, z in ii:
                f.write('%d,%d,%d,%d\n' % (a + x0, b + ylo, z, c[a, b, z]))
        return [int(len(ii)), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    od, ol = os.path.join(design, 'masks', 'decks'), os.path.join(design, 'masks', 'ladders')
    for dd in (od, ol):
        os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd):
            if f.endswith('.vox.txt'):
                os.remove(os.path.join(dd, f))
    R['lists'] = {}
    for k, c in cells.items():
        R['lists']['deck-' + k] = dump(os.path.join(od, k + '.vox.txt'), c, '# Star deck %s (draft_decks.py; world coords, at 0,0,0)\n' % k)
    for k, c in lad.items():
        R['lists']['ladders-' + k] = dump(os.path.join(ol, k + '.vox.txt'), c, '# Star ladders up to %s (draft_decks.py; world coords, at 0,0,0)\n' % k)
    with open(os.path.join(design, 'ladder_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pts, f, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'decks_meta.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        for g in G:
            f.write('link\t甲板-%s\t%s\n' % (g['key'], json.dumps(meta[g['key']], ensure_ascii=False, separators=(',', ':'))))

    # sheet: each group from above + centreline section
    keys = [g['key'] for g in G]
    Hp = 80 + len(keys) * (ny + 30) + nz + 60
    im = Image.new('RGB', (nx + 140, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((10, 10), 'Star sheet 03: decks, hatch, break, ladders v1', fill=(0, 0, 0), font=font(14))
    d.text((10, 30), 'each deck from above; blue = ladders; bottom = centreline section', fill=(0, 0, 0), font=font(11))
    for i, k in enumerate(keys):
        oy = 60 + i * (ny + 30)
        d.text((10, oy + ny // 2 - 6), k, fill=(0, 0, 0), font=font(12))
        top = cells[k].max(axis=2)
        lt = lad[k].max(axis=2) if k in lad else np.zeros_like(top)
        for a in range(nx):
            for b in range(ny):
                if lt[a, b]:
                    d.point((100 + a, oy + b), fill=(0, 90, 200))
                elif top[a, b]:
                    d.point((100 + a, oy + b), fill=palette_rgb(int(top[a, b])))
    oy = 60 + len(keys) * (ny + 30)
    yc_i = YC - ylo
    final = H['final']
    for a in range(nx):
        for z in range(nz):
            cc = final[a, yc_i, z] if keep[a, yc_i, z] else 0
            for dd in list(cells.values()) + list(lad.values()):
                if dd[a, yc_i, z]:
                    cc = dd[a, yc_i, z]
            if cc:
                d.point((100 + a, oy + nz - z), fill=palette_rgb(int(cc)))
    im.save(os.path.join(design, 'sheet03_decks_v1.png'))
    with open(os.path.join(design, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('ladder_points', 'lists', 'deck_meta')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
