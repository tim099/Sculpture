# Source: calli-cosecha-01m/design/draft_deco.py (Harvest, stern deco), basecamp-frigate-constitution-01m/design/draft_stern_glass.py
#   (glass), apex-two-galeon-01m Ship_Ends §3 (6-connected window distance) -- rewritten for the Star (TASK-0019 step 6)
# Star (al-Najm) new sheet 04: decorations.
#   Inputs: plan.json (deco / stern / paint), the hull design (draft_ports.build -- NOT the live work, so a rerun after
#           stamping gives the same lists), the step-5 deck / ladder lists (masks/decks, masks/ladders).
#   Outputs (all at=0,0,0):
#     masks/step6/hull_recolor.vox.txt   hull cells that change colour (stampvox overwrite=1): window reveals white, rail-cap fix
#     masks/step6/hull_add.vox.txt       new hull cells: window sashes (white) in the glass layer
#     masks/deco/stern_glass.vox.txt     link, meta material=glass
#     masks/deco/quarter_gallery.vox.txt port side only; starboard = mirror=y link (at 0,1,0)
#     masks/deco/gallery_glass.vox.txt   link inside the gallery work, meta material=glass
#     masks/deco/quarter_rail.vox.txt    helm-deck rail + bulwark cloth + breast balustrade (both sides, one link)
#     masks/deco/stern_carving.vox.txt   external model, meta deco=1
#     masks/deco/stem_head.vox.txt       external model, meta deco=1
#     verify_deco.json, sheet04_deco_v1.png
#   Usage: python -X utf8 draft_deco.py <design> [--probe=drop_glass] [--no-write]
#     --probe=drop_glass: reverse control -- one glass cell removed from every stern window; the seal check must report each.
import sys, os, json, math, hashlib
from collections import deque
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_ports import build, FACE_X_MAX
from draft_lines import font, palette_rgb

SX, SY, SZ = 420, 160, 120
N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def load_list(path):
    out = {}
    for l in open(path, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            out[(x, y, z)] = c
    return out


def base(plan, design):
    B = build(plan)
    x0, ylo = B['x0'], B['ylo']
    hull = {(int(i + x0), int(j + ylo), int(k)): int(B['final'][i, j, k]) for i, j, k in np.argwhere(B['keep'])}
    parts = {}
    for g in plan['decks_build']['groups']:
        parts['deck-' + g['key']] = load_list(os.path.join(design, 'masks', 'decks', g['key'] + '.vox.txt'))
    for f in sorted(os.listdir(os.path.join(design, 'masks', 'ladders'))):
        parts['ladders-' + f.split('.')[0]] = load_list(os.path.join(design, 'masks', 'ladders', f))
    return B, hull, parts


def stern_windows(plan, B, hull, C):
    """Window holes, 6-connected distance from the outside, recess / glass / sash, reveal recolour."""
    YC = plan['space']['yc']
    x0, ylo = B['x0'], B['ylo']
    holes = {(int(i + x0), int(j + ylo), int(k)) for i, j, k in np.argwhere(B['holes'])}
    SW = plan['deco']['stern_windows']
    out = {'glass': {}, 'sash': {}, 'reveal': {}, 'per_window': [], 'holes': set()}
    for w in LY.stern_windows(plan, YC):
        hs = {p for p in holes if w['y0'] <= p[1] <= w['y1'] and w['z0'] <= p[2] <= w['z1'] and p[0] < FACE_X_MAX}
        out['holes'] |= hs
        dist = {}
        q = deque()
        for p in sorted(hs):
            o = (p[0] - 1, p[1], p[2])
            if o not in hs and o not in hull:
                dist[p] = 1
                q.append(p)
        while q:
            p = q.popleft()
            for d in N6:
                n = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
                if n in hs and n not in dist:
                    dist[n] = dist[p] + 1
                    q.append(n)
        yc = (w['y0'] + w['y1']) // 2
        g = s = 0
        for p, d in dist.items():
            if d != SW['recess'] + 1:
                continue
            if p[1] == yc or p[2] == SW['sash_z']:
                out['sash'][p] = C['white']
                s += 1
            else:
                out['glass'][p] = C['glass']
                g += 1
        rv = 0
        for p in hs:
            for d in N6:
                n = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
                if n in hull and n not in out['reveal'] and hull[n] != C['white']:
                    out['reveal'][n] = C['white']
                    rv += 1
        out['per_window'].append({'j': w['j'], 'y': [w['y0'], w['y1']], 'z': [w['z0'], w['z1']], 'hole_cells': len(hs),
                                  'unreached': len(hs) - len(dist), 'depth_max': max(dist.values()), 'glass': g, 'sash': s, 'reveal_recoloured': rv})
    return out


def rail_cap_fix(plan, hull, occ_base):
    """Inner-plank (177) cells near the rail top whose top face is open -> rail-cap black."""
    HB = plan['hull_build']
    top = {}
    for (x, y, z) in hull:
        top[(x, y < plan['space']['yc'])] = max(top.get((x, y < plan['space']['yc']), -1), z)
    fix = {}
    for (x, y, z), c in hull.items():
        if c == HB['inner_color'] and (x, y, z + 1) not in occ_base and z >= top[(x, y < plan['space']['yc'])] - 2:
            fix[(x, y, z)] = plan['paint']['rail_cap']
    return fix


def stern_face(plan, B):
    """xf[(y, z)]: first wall cell from aft (windows counted as wall) on the stern face."""
    x0, ylo = B['x0'], B['ylo']
    W = B['wall']
    xf = {}
    for j in range(W.shape[1]):
        for k in range(W.shape[2]):
            c = np.nonzero(W[:, j, k])[0]
            if len(c) and c[0] + x0 < FACE_X_MAX:
                xf[(int(j + ylo), int(k))] = int(c[0] + x0)
    return xf


def carving(plan, B, xf, C, avoid=(), face_ok=None):
    """2-D design on the stern face (y, z) -> relief 1 cell aft of the face; steps between rows filled (6-connected).
    Cells in `avoid` (the quarter galleries wrap the stern corners) are left out."""
    YC = plan['space']['yc']
    D = plan['deco']['stern_carving']
    wins = LY.stern_windows(plan, YC)
    d2 = {}

    if face_ok is not None:      # v2 (verifier step 6 B): only on the black stern face, not on the teak side planking
        xf = {k: v for k, v in xf.items() if k in face_ok}

    def put(y, z, c=None):
        if (y, z) in xf:
            d2[(y, z)] = C['white'] if c is None else c

    zb0, zb1 = D['z_band']
    zm = D['z_moulding']
    pw = D['pilaster_w']
    # v1 had 2-wide pilasters filling the gaps between the (white) window frames => the whole window band read as one
    # white block. v2: the frames are the dividers; the 2-cell gaps stay black; dividers only in the panel band and
    # a short finial above the frames; outer pilasters 1 wide with one black cell between them and the outer frames.
    gaps = [(a['y1'] + 2, b['y0'] - 2) for a, b in zip(wins, wins[1:])]
    outer = [(wins[0]['y0'] - 1 - pw - 1, wins[0]['y0'] - 2 - pw), (wins[-1]['y1'] + 2 + pw, wins[-1]['y1'] + 1 + 2 * pw)]
    for y0, y1 in outer:
        for y in range(y0, y1 + 1):
            for z in range(zb0 + 1, zm):
                put(y, z)
    for y0, y1 in gaps:
        for y in range(y0, y1 + 1):
            for z in list(range(zb0 + 1, zb1)) + list(range(wins[0]['z1'] + 2, wins[0]['z1'] + 2 + D['arch_rise'])):
                put(y, z)
    ylo, yhi = outer[0][0], outer[1][1]
    # mouldings
    for y in range(ylo, yhi + 1):
        put(y, zb0)
        put(y, zb1)
        put(y, zm)
    for w in wins:
        c = (w['y0'] + w['y1']) // 2
        # pointed pediment: from the frame's top corners up to an apex arch_rise above the frame (inside stays black), finial
        zf = w['z1'] + 1
        for k in range(D['arch_rise'] + 1):
            put(c - 3 + k, zf + k)
            put(c + 3 - k, zf + k)
        put(c, zf + D['arch_rise'] + 1)
        # panel under the window: cross + four dots
        zc = (zb0 + zb1) // 2
        for dz in (-1, 0, 1):
            put(c, zc + dz)
        put(c - 1, zc)
        put(c + 1, zc)
        for dy in (-2, 2):
            put(c + dy, zc - 1)
            put(c + dy, zc + 1)
    # border following the face outline, inset cells in from the edge (upper field, z > moulding)
    M = np.zeros((SY, SZ), bool)
    for (y, z) in xf:
        M[y, z] = True
    dist = ndimage.distance_transform_cdt(np.pad(M, 1), metric='chessboard')[1:-1, 1:-1]
    for (y, z) in xf:
        if z > zm and dist[y, z] == D['border_inset'] + 1:
            put(y, z)
    # star (al-Najm) and two rosettes
    S = D['star']
    r = S['r']
    for a in range(-r, r + 1):
        for b in range(-r, r + 1):
            if (max(abs(a), abs(b)) <= r - 1 or abs(a) + abs(b) <= r) and (a, b) != (0, 0):
                put(S['y'] + a, S['z'] + b)
    for yc in (S['y'] - D['rosettes_dy'], S['y'] + D['rosettes_dy']):
        for dz in (-1, 0, 1):
            put(yc, S['z'] + dz)
        put(yc - 1, S['z'])
        put(yc + 1, S['z'])
    # 2-D -> 3-D: one cell aft of the face; fill the step towards each 2-D neighbour whose face is further aft
    cells = {}
    for (y, z), c in d2.items():
        cells[(xf[(y, z)] - 1, y, z)] = c
    for (y, z), c in d2.items():
        for dy, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (y + dy, z + dz)
            if nb in d2 and xf[nb] < xf[(y, z)]:
                for x in range(xf[nb] - 1, xf[(y, z)] - 1):
                    cells.setdefault((x, y, z), c)
    dropped = sorted(p for p in cells if p in avoid)
    for p in dropped:
        del cells[p]
    return cells, dropped


def gallery(plan, hull, C):
    """Port quarter gallery: body, windows (recess / glass / sash), mouldings, roof, pendant."""
    G = plan['deco']['quarter_gallery']
    YC = plan['space']['yc']
    zb, zt = G['z_base'], G['z_top']

    def xfront(z):
        return int(math.floor(G['x_front_top'] - (zt - z) * G['front_slope'] + 0.5))

    ys = {}
    for (x, y, z) in hull:
        if y < YC and zb - 1 <= z <= G['roof_z']:
            ys[(x, z)] = min(ys.get((x, z), 999), y)
    yout = {}
    for (x, z), v in ys.items():
        if zb <= z <= zt and x <= xfront(z):
            yout[x] = min(yout.get(x, 999), v - G['dep'])
    body = {}
    for (x, z), v in ys.items():
        if zb <= z <= zt and x <= xfront(z) and x in yout:
            for y in range(yout[x], v):
                body[(x, y, z)] = C['black']
    # windows: shared frames, mullions, transom
    w, n = G['win_w'], G['win_n']
    fx = [G['win_x0'] + j * (w + 1) for j in range(n + 1)]
    wz0, wz1 = G['win_z']
    inner = set()
    for j in range(n):
        for x in range(fx[j] + 1, fx[j + 1]):
            for z in range(wz0, wz1 + 1):
                inner.add((x, z))
    hole = {p for p in body if (p[0], p[2]) in inner}
    dist = {}
    q = deque()
    for p in sorted(hole):
        if (p[0], p[1] - 1, p[2]) not in body:
            dist[p] = 1
            q.append(p)
    while q:
        p = q.popleft()
        for d in N6:
            nb = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
            if nb in hole and nb not in dist:
                dist[nb] = dist[p] + 1
                q.append(nb)
    glass = {}
    for p, d in dist.items():
        if d == 1:
            del body[p]
        elif d == 2:
            x, y, z = p
            k = (x - fx[[i for i in range(n) if fx[i] < x < fx[i + 1]][0]] - 1)
            if z == G['transom_z'] or k % G['mullion_every'] == G['mullion_every'] - 1:
                body[p] = C['white']
            else:
                del body[p]
                glass[p] = C['glass']
        else:
            body[p] = C['dark']
    # outer surface paint: frames, base / top mouldings
    for (x, y, z) in list(body):
        if (x, y - 1, z) in body or (x, y, z) in dist:
            continue
        frame = (zb + 4 <= z <= zt - 3) and ((x in fx and wz0 - 1 <= z <= wz1 + 1) or
                                             (z in (wz0 - 1, wz1 + 1) and fx[0] <= x <= fx[-1]))
        if frame or z in (zb, zt):
            body[(x, y, z)] = C['white']
    # roof (black, 1 overhang outboard and forward) and base moulding (white, 1 overhang outboard)
    xs_g = sorted({p[0] for p in body})
    for x in range(xs_g[0], xfront(zt) + 2):
        if (x, G['roof_z']) in ys and (min(x, xfront(zt)) in yout):
            for y in range(yout[min(x, xfront(zt))] - 1, ys[(x, G['roof_z'])]):
                body.setdefault((x, y, G['roof_z']), C['black'])
    for x in range(xs_g[0], xfront(zb) + 1):
        if (x, zb - 1) in ys and x in yout:
            for y in range(yout[x] - 1, ys[(x, zb - 1)]):
                body.setdefault((x, y, zb - 1), C['white'])
    # pendant: lower half-ellipsoid under the base moulding, fluted (white with black grooves)
    P = G['pendant']
    foot = [(x, y) for (x, y, z) in body if z == zb - 1]
    yc = (min(y for x, y in foot if abs(x - P['xc']) <= 1) + max(y for x, y in foot if abs(x - P['xc']) <= 1)) / 2.0
    for z in range(P['z_top'] - P['az'], P['z_top']):
        for x in range(P['xc'] - P['ax'], P['xc'] + P['ax'] + 1):
            for y in range(int(yc) - P['dep'] - 1, int(yc) + P['dep'] + 2):
                u = (x - P['xc']) / float(P['ax'])
                v = (y - yc) / float(P['dep'])
                t = (P['z_top'] - z - 0.5) / float(P['az'])
                if u * u + v * v + t * t <= 1.0 and (x, y, z) not in hull:
                    grooved = (x - P['xc']) % 3 == 0 and z < P['z_top'] - 1
                    body[(x, y, z)] = C['black'] if grooved else C['white']
    return body, glass, {'frames_x': fx, 'window_cells': len(hole), 'glass': len(glass), 'pendant_yc': yc,
                         'x_span': [min(p[0] for p in body), max(p[0] for p in body)],
                         'y_span': [min(p[1] for p in body), max(p[1] for p in body)],
                         'z_span': [min(p[2] for p in body), max(p[2] for p in body)]}


def quarter_rail(plan, hull, parts, C):
    R = plan['deco']['quarter_rail']
    YC = plan['space']['yc']
    out = {}
    tops = {}
    for (x, y, z) in hull:
        if y < YC and R['x_from'] <= x <= R['x_to']:
            tops[x] = max(tops.get(x, -1), z)
    xs = [x for x in sorted(tops) if tops[x] < R['top_z']]
    for x in xs:
        wall = sorted(y for (hx, y, hz) in hull if hx == x and hz == tops[x] and y < YC)
        ym = wall[len(wall) // 2]
        post = (x - xs[0]) % R['post_every'] == 0 or x == xs[-1]
        for z in range(tops[x] + 1, R['top_z'] + 1):
            c = C['black'] if (z == R['top_z'] or post) else C['red']
            out[(x, ym, z)] = c
            out[(x, 2 * YC - ym, z)] = c
    # breast balustrade on the breast rail
    poop = parts['deck-poop']
    bx = R['breast_x']
    zbr = max(z for (x, y, z) in poop if x == bx)
    yb = sorted(y for (x, y, z) in poop if x == bx and z == zbr)
    ends = {y for y in yb if (y - 1) not in yb or (y + 1) not in yb}
    for y in yb:
        bal = (y - YC) % R['baluster_every'] == 0 or y in ends
        for z in range(zbr + 1, R['top_z'] + 1):
            if z == R['top_z']:
                out[(bx, y, z)] = C['black']
            elif bal:
                out[(bx, y, z)] = C['white']
    # front corners: the side rail (y = ym at x = bx) and the breast balustrade (from yb[0]) leave a 1-wide gap -> black post
    #   (verifier step 6 D: empty column at (150, 36 / 124, 75-80), handrail broken)
    wall = sorted(y for (hx, y, hz) in hull if hx == bx and hz == tops[bx] and y < YC)
    ym = wall[len(wall) // 2]
    corner = 0
    for y in range(ym + 1, yb[0]):
        for z in range(tops[bx] + 1, R['top_z'] + 1):
            if (bx, y, z) not in hull and (bx, y, z) not in poop:
                out[(bx, y, z)] = C['black']
                out[(bx, 2 * YC - y, z)] = C['black']
                corner += 2
    return out, {'side_x': [xs[0], xs[-1]], 'breast_top_z': zbr, 'breast_y_cells': len(yb), 'breast_segment_ends': sorted(ends),
                 'corner_cells': corner}


def stem_head(plan, hull, C):
    S = plan['deco']['stem_head']
    YC = plan['space']['yc']
    zt = max(z for (x, y, z) in hull if y == YC and x > 300)
    xt = max(x for (x, y, z) in hull if y == YC and z == zt)
    out = {}
    half = S['post_w'] // 2
    k = S['rake_x_per_z']
    for i in range(S['post_len']):
        z = zt + 1 + i
        xc = int(math.floor(xt - 1 + k * (i + 1) + 0.5))
        for x in range(xc - half, xc + half + 1):
            for y in range(YC - half, YC + half + 1):
                out[(x, y, z)] = C['white'] if i == S['post_len'] - 1 else 136
    zt_post = zt + S['post_len']
    xe = xt - 1 + k * S['post_len'] + 0.5
    a = np.array([k, 0.0, 1.0])
    a /= np.linalg.norm(a)
    n = np.array([-a[2], 0.0, a[0]])
    r = S['knob_r']
    cen = np.array([xe, YC + 0.5, zt_post + 0.5]) + a * r
    for x in range(int(cen[0]) - r - 1, int(cen[0]) + r + 2):
        for y in range(YC - r - 1, YC + r + 2):
            for z in range(int(cen[2]) - r - 1, int(cen[2]) + r + 2):
                p = np.array([x + 0.5, y + 0.5, z + 0.5]) - cen
                if p @ p > (r + 0.5) ** 2:
                    continue
                t = p @ a
                qv = p - t * a
                ang = abs(math.atan2(qv[1], qv @ n))          # |angle| => ribs mirror across the centre line
                rib = int(math.floor(ang / (math.pi / 4))) % 2
                c = C['black'] if -0.5 * r <= t <= -0.5 * r + 1.0 else C['white']   # v2: white knob, black collar (v1 lobes read as a skull)
                out.setdefault((x, y, z), c)
    return out, {'stem_top': [xt, YC, zt], 'knob_centre': [round(float(v), 2) for v in cen]}


def comps(cells):
    A = np.array(sorted(cells))
    lo = A.min(axis=0)
    G = np.zeros(tuple(A.max(axis=0) - lo + 1), bool)
    G[tuple((A - lo).T)] = True
    lab, n = ndimage.label(G)
    cav = int((ndimage.binary_fill_holes(G) & ~G).sum())
    return n, cav


def mirror_diff(cells, yc):
    return sum(1 for (x, y, z), c in cells.items() if cells.get((x, 2 * yc - y, z)) != c)


def glass_seal(win_holes, glass, occ, drop=False):
    """Per window: flood the outside air in a box around it (glass, sash, hull, decks solid); reaching the air behind the
    wall = leak. drop=True removes the middle glass cell of each window first (reverse control)."""
    res = []
    by_win = {}
    for p in win_holes:
        by_win.setdefault((p[1] // 9, ), []).append(p)
    groups = []
    hs = sorted(win_holes)
    seen = set()
    for p in hs:
        if p in seen:
            continue
        comp = []
        q = deque([p])
        seen.add(p)
        while q:
            c = q.popleft()
            comp.append(c)
            for d in N6:
                nb = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
                if nb in win_holes and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        groups.append(comp)
    for comp in groups:
        g = [p for p in comp if p in glass]
        solid = set(occ)
        removed = None
        if drop and g:
            g.sort()
            removed = g[len(g) // 2]
            solid.discard(removed)
        xs = [p[0] for p in comp]; ys = [p[1] for p in comp]; zs = [p[2] for p in comp]
        x0, x1 = min(xs) - 3, max(xs) + 1
        y0, y1, z0, z1 = min(ys) - 2, max(ys) + 2, min(zs) - 2, max(zs) + 2
        behind = {p for p in comp if (p[0] + 1, p[1], p[2]) not in comp and p not in solid}
        q = deque()
        seen = set()
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                s = (x0, y, z)
                if s not in solid:
                    seen.add(s)
                    q.append(s)
        while q:
            c = q.popleft()
            for d in N6:
                nb = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
                if x0 <= nb[0] <= x1 and y0 <= nb[1] <= y1 and z0 <= nb[2] <= z1 and nb not in solid and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        leak = sorted(seen & behind)
        res.append({'window_y': [min(ys), max(ys)], 'glass': len(g), 'behind_open': len(behind), 'leak_cells': len(leak),
                    'removed': list(removed) if removed else None})
    return res


def walk_cells(occ, floor_cells, head=12):
    """Cells a crew member can stand in: air, a floor-part cell below, `head` cells of air above."""
    out = set()
    for (x, y, z) in floor_cells:
        p = (x, y, z + 1)
        if p in occ:
            continue
        if all((x, y, z + 1 + k) not in occ for k in range(head)):
            out.add(p)
    return out


def project(cells, view, box, scale):
    """Orthographic first-hit picture. view: 'aft' (look +x), 'port' (look +y), 'top' (look -z)."""
    (a0, a1), (b0, b1) = box
    W, H = a1 - a0 + 1, b1 - b0 + 1
    depth = np.full((W, H), 10 ** 6, np.int64)
    col = np.zeros((W, H), np.int64)
    for (x, y, z), c in cells.items():
        if view == 'aft':
            u, v, d = y - a0, z - b0, x
        elif view == 'port':
            u, v, d = x - a0, z - b0, y
        else:
            u, v, d = x - a0, y - b0, -z
        if 0 <= u < W and 0 <= v < H and d < depth[u, v]:
            depth[u, v] = d
            col[u, v] = c
    img = Image.new('RGB', (W * scale, H * scale), (236, 240, 244))
    px = img.load()
    shade = {}
    for u in range(W):
        for v in range(H):
            c = int(col[u, v])
            if not c:
                continue
            rgb = shade.setdefault(c, palette_rgb(c))
            yy = (H - 1 - v) if view != 'top' else v
            for i in range(scale):
                for j in range(scale):
                    px[u * scale + i, yy * scale + j] = rgb
    return img


def draw(path, title, panels, rows):
    pad = 30
    wmax = max(p[1].size[0] for p in panels)
    H = 90 + sum(p[1].size[1] + 40 for p in panels) + len(rows) * 22 + 60
    img = Image.new('RGB', (max(wmax + 2 * pad, 1100), H), (250, 250, 248))
    d = ImageDraw.Draw(img)
    d.text((pad, 20), title, fill=(20, 20, 20), font=font(22))
    d.text((pad, 52), '0.1 m/cell; first-hit orthographic views of hull + decks + all step-6 parts (glass drawn opaque light blue)', fill=(60, 60, 60), font=font(14))
    y = 90
    for cap, im in panels:
        d.text((pad, y), cap, fill=(0, 0, 0), font=font(15))
        img.paste(im, (pad, y + 22))
        y += im.size[1] + 40
    for k, v in rows:
        d.text((pad, y), k, fill=(0, 0, 0), font=font(14))
        d.text((pad + 330, y), v, fill=(30, 30, 30), font=font(14))
        y += 22
    d.text((pad, y + 10), 'Provenance: plan.json deco.*.src (P2 fig. 7, P3, PT; design decisions marked there).', fill=(90, 90, 90), font=font(12))
    img.save(path)


def shift_y(cells, dy):
    return {(x, y + dy, z): c for (x, y, z), c in cells.items()}


def dump(path, cells, head):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s (%d cells, at=0,0,0; TASK-0019 step 6)\n' % (head, len(cells)))
        for (x, y, z), c in sorted(cells.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    probe = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe=')), None)
    write = '--no-write' not in sys.argv and probe is None
    plan = HL.load_plan(design)
    YC = plan['space']['yc']
    C = plan['deco']['colors']
    B, hull, parts = base(plan, design)
    occ_base = set(hull)
    for p in parts.values():
        occ_base |= set(p)

    SWr = stern_windows(plan, B, hull, C)
    capfix = rail_cap_fix(plan, hull, occ_base)
    recolor = dict(capfix)
    recolor.update(SWr['reveal'])
    hull_add = dict(SWr['sash'])
    hull_new = dict(hull)
    hull_new.update(recolor)
    hull_new.update(hull_add)

    gal, gglass, ginfo = gallery(plan, hull, C)
    galS = {(x, 2 * YC - y, z): c for (x, y, z), c in gal.items()}
    gglassS = {(x, 2 * YC - y, z): c for (x, y, z), c in gglass.items()}
    xf = stern_face(plan, B)
    face_ok = {(y, z) for (y, z), x in xf.items() if hull_new.get((x, y, z)) in (C['black'], C['white']) or (x, y, z) in SWr['holes']}
    carve, carve_dropped = carving(plan, B, xf, C, avoid=set(gal) | set(galS), face_ok=face_ok)
    rail, rinfo = quarter_rail(plan, hull, parts, C)
    stem, sinfo = stem_head(plan, hull, C)

    links = {'hull': hull_new}
    links.update(parts)
    links.update({'stern-glass': SWr['glass'], 'gallery-P': gal, 'gallery-S': galS, 'gallery-glass-P': gglass,
                  'gallery-glass-S': gglassS, 'quarter-rail': rail})
    models = {'stern-carving': carve, 'stem-head': stem}
    R = {'probe': probe}

    # overlaps: every link / model against everything placed before it
    seen = {}
    ov = {}
    for nm, cs in list(links.items()) + list(models.items()):
        k = set(cs)
        ov[nm] = {o: len(k & s) for o, s in seen.items() if k & s}
        seen[nm] = k
    R['overlaps'] = {k: v for k, v in ov.items() if v}
    allL = {}
    for cs in links.values():
        allL.update(cs)
    n, cav = comps(allL)
    R['assembled_links'] = {'cells': len(allL), 'components_6': n, 'cavities': cav, 'mirror_diff': mirror_diff(allL, YC)}
    allM = {}
    for cs in models.values():
        allM.update(cs)
    R['models'] = {}
    for nm, cs in models.items():
        lab_n, _ = comps(cs)
        A = np.array(sorted(cs))
        lo = A.min(axis=0)
        Gm = np.zeros(tuple(A.max(axis=0) - lo + 1), bool)
        Gm[tuple((A - lo).T)] = True
        lab, k = ndimage.label(Gm)
        touching = set()
        for (x, y, z) in cs:
            if any((x + d[0], y + d[1], z + d[2]) in allL for d in N6):
                touching.add(int(lab[x - lo[0], y - lo[1], z - lo[2]]))
        R['models'][nm] = {'cells': len(cs), 'components_6': int(k), 'components_not_touching_ship': int(k - len(touching)),
                           'mirror_diff': mirror_diff(cs, YC), 'over_window_openings': sum(1 for (x, y, z) in cs if (y, z) in
                           {(p[1], p[2]) for p in SWr['holes']} and x < FACE_X_MAX)}
    # windows
    R['stern_windows'] = SWr['per_window']
    occ_after = set(allL)
    sealed = glass_seal(SWr['holes'], SWr['glass'], occ_after, drop=(probe == 'drop_glass'))
    R['glass_seal'] = sealed
    R['reveal_wood_left'] = sum(1 for p in SWr['holes'] for d in N6
                                if (q := (p[0] + d[0], p[1] + d[1], p[2] + d[2])) in hull_new and hull_new[q] in
                                (plan['hull_build']['frame_color'], plan['hull_build']['inner_color']))
    R['rail_cap_fix'] = {'cells': len(capfix), 'x_span': [min(p[0] for p in capfix), max(p[0] for p in capfix)] if capfix else None}
    capleft = rail_cap_fix(plan, hull_new, occ_base)
    R['rail_cap_fix']['left_after'] = len(capleft)
    R['gallery'] = ginfo
    R['quarter_rail'] = rinfo
    R['stem_head'] = sinfo
    # ladder points with every new link and model in place
    pts = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
    occ_all = set(allL) | set(allM)
    lp = []
    for nm, v in sorted(pts.items()):
        for pk, (x, y, z) in v['points'].items():
            if (x, y, z) in occ_all or (x, y, z - 1) not in occ_all or any((x, y, z + k) in occ_all for k in range(14)):
                lp.append([nm, pk])
    R['ladder_point_problems'] = lp
    # deck walk cells lost to the new parts
    floors = set()
    for nm, cs in parts.items():
        if nm.startswith('deck-'):
            floors |= set(cs)
    w0 = walk_cells(occ_base, floors)
    w1 = walk_cells(occ_all, floors)
    lost = sorted(w0 - w1)
    breast = {(x, y, z) for (x, y, z) in parts['deck-poop'] if x == plan['deco']['quarter_rail']['breast_x']}
    R['walk_cells_lost'] = {'cells': len(lost), 'on_top_of_breast_rail': sum(1 for (x, y, z) in lost if (x, y, z - 1) in breast),
                            'other': [list(p) for p in lost if (p[0], p[1], p[2] - 1) not in breast][:10]}
    # swivel stations and gun-port fields: new cells near them
    new = set()
    for nm in ('stern-glass', 'gallery-P', 'gallery-S', 'quarter-rail'):
        new |= set(links[nm])
    new |= set(allM)
    sw = plan['ports']['swivels']
    # v2 (verifier step 6 A): the y window follows the hull side at that x (v1 used a fixed y <= 45 / >= 115, which
    #   never looked at the narrow stern where the x 40 swivel sits on a rail at y 55)
    def side_y(x0, x1, z0):
        ys = [y for (x, y, z) in hull if x0 <= x <= x1 and z >= z0 and y < YC]
        return min(ys)
    near_sw = {}
    for sx in sw['x']:
        ztop = max(z for (x, y, z) in hull if x == sx and y < YC)
        ys = side_y(sx, sx, ztop - 2)
        near_sw[str(sx)] = sum(1 for (x, y, z) in new if abs(x - sx) <= 4 and z >= ztop - 3 and (y <= ys + 6 or y >= 2 * YC - ys - 6))
    R['new_cells_near_swivel_stations'] = near_sw
    near_port = 0
    for p in LY.ports(plan):
        ys = side_y(p['x0'], p['x1'], p['z0'])
        for (x, y, z) in new:
            if p['x0'] - 2 <= x <= p['x1'] + 2 and p['z0'] - 2 <= z <= p['z1'] + 2 and (y <= ys + 8 or y >= 2 * YC - ys - 8):
                near_port += 1
    R['new_cells_in_front_of_gun_ports'] = near_port
    R['carving_dropped_under_gallery'] = [list(p) for p in carve_dropped]
    R['counts'] = {'hull_recolor': len(recolor), 'hull_add': len(hull_add), 'stern_glass': len(SWr['glass']),
                   'gallery_P': len(gal), 'gallery_glass_P': len(gglass), 'quarter_rail': len(rail),
                   'stern_carving': len(carve), 'stem_head': len(stem)}
    print(json.dumps({k: v for k, v in R.items() if k not in ('stern_windows',)}, ensure_ascii=False))
    if not write:
        return
    FR = plan['deco']['quarter_gallery']['frame']
    assert all(0 <= y - FR['at_y'] < FR['size'][1] for (x, y, z) in gal), 'gallery outside its frame'
    out = os.path.join(design, 'masks')
    os.makedirs(os.path.join(out, 'step6'), exist_ok=True)
    os.makedirs(os.path.join(out, 'deco'), exist_ok=True)
    files = {
        'step6/hull_recolor.vox.txt': (recolor, 'hull recolour: window reveals white 182, rail-cap fix 36 (stampvox overwrite=1)'),
        'step6/hull_add.vox.txt': (hull_add, 'hull add: stern window sashes white 182'),
        'deco/stern_glass.vox.txt': (SWr['glass'], 'stern window glass (link meta material=glass)'),
        'deco/quarter_gallery.vox.txt': (shift_y(gal, -FR['at_y']), 'port quarter gallery, frame-local (work 420x40x120; link at 0,%d,0, starboard mirror=y at 0,%d,0)' % (FR['at_y'], 161 - FR['at_y'] - FR['size'][1])),
        'deco/gallery_glass.vox.txt': (shift_y(gglass, -FR['at_y']), 'quarter gallery glass, frame-local (link inside the gallery at 0,0,0, meta material=glass)'),
        'deco/quarter_rail.vox.txt': (rail, 'helm-deck rail, bulwark cloth, breast balustrade'),
        'deco/stern_carving.vox.txt': (carve, 'stern carving (external model, meta deco=1)'),
        'deco/stem_head.vox.txt': (stem, 'stem head finial (external model, meta deco=1)'),
    }
    sha = {}
    for rel, (cs, head) in files.items():
        p = os.path.join(out, rel)
        dump(p, cs, head)
        sha[rel] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    R['sha256'] = sha
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
        f.write('\n')
    pic = dict(allL)
    pic.update(allM)
    panels = [
        ('1 Stern elevation from aft (y 30..130, z 40..92), x6', project(pic, 'aft', ((30, 130), (40, 92)), 6)),
        ('2 Port quarter from the side (x 18..170, z 40..92), x5', project(pic, 'port', ((18, 170), (40, 92)), 5)),
        ('3 Bow head from the side (x 340..400, z 55..90), x6', project(pic, 'port', ((340, 400), (55, 90)), 6)),
    ]
    rows = [
        ('Links assembled', '%d cells, %d component, %d cavity, mirror diff %d' % (len(allL), n, cav, R['assembled_links']['mirror_diff'])),
        ('Overlaps', str(R['overlaps'] or 0)),
        ('Stern glass', '%d cells; seal leaks %s' % (len(SWr['glass']), [s['leak_cells'] for s in sealed])),
        ('Window reveals still wood', str(R['reveal_wood_left'])),
        ('Models (deco=1)', ', '.join('%s %d cells / %d comp' % (k, v['cells'], v['components_6']) for k, v in R['models'].items())),
        ('Ladder points / walk cells lost', '%d / %d (on top of the breast rail %d)' % (len(lp), R['walk_cells_lost']['cells'], R['walk_cells_lost']['on_top_of_breast_rail'])),
        ('Rail-cap fix', '%d cells, left after %d' % (len(capfix), len(capleft))),
    ]
    draw(os.path.join(design, 'sheet04_deco_v1.png'), plan['title'].split(',')[0] + ', new sheet 04:  stern carving, glass, quarter galleries, helm rail, stem head  v1', panels, rows)
    print('wrote', ', '.join('%s %s' % (k, v[:8]) for k, v in sha.items()))


if __name__ == '__main__':
    main()
