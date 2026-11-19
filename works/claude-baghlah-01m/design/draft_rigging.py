# Source: calli-cosecha-01m/design/draft_rigging.py (Harvest: anchors per sub-work, ropes with groups, lateen sails bound
#   to the yard models, sail ropes with meta, flags with a texture) -- rewritten for the Star (TASK-0019 step 8).
#   Different from the Harvest: no channels / deadeyes / ratlines (PT: shrouds are single pendants with a tackle hooked to
#   rings outside the hull, moved as needed); trapezoid lateens (4 corners: fore, peak, clew, tack; tack and clew free);
#   jib on a stay from the jib-boom tip to the main hounds; halyards over the masthead sheaves to a bitt; bumkin + flagstaff.
# Star (al-Najm) new sheet 06: rigging, sails, flags.
#   Inputs: plan.json (rigging, rig_build, masts), yards_lateen.json / yards_placement.json, and the design lists of every
#           earlier part (draft_masts.ship_cells + masks/masts + masks/yards) -- NOT the live works.
#   Outputs:
#     masks/rigging/{rings,stern_spars,halyard_bitt}.vox.txt   sub-works at 0,0,0
#     rigging_plan.json        anchors per work, ropes, sails, meta, wind
#     textures/ensign.png      plain red (24 x 16)
#     verify_rigging.json, sheet06_rigging_v1.png
#   Usage: python -X utf8 draft_rigging.py <design> [--probe=<kind>=<arg>]   (nothing written with a probe)
#     --probe=nometa=<rope>      drop one rope's meta: the sail-rope meta check must name it
#     --probe=ring_dx=<n>        shift the main rings n cells in x: the mizzen-yard sweep clearance must move
#     --probe=side=<main|mizzen> put that mast's shrouds on the sail's side: the rope-through-sail count must report it
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_masts import ship_cells, load
from draft_lines import font, palette_rgb

HULL = 'claude-baghlah-01m'
LINK = {'hull': '船殼', 'mast-main': '主桅', 'mast-mizzen': '後桅', 'jibboom': 'foc桿', 'deck-poop': '甲板-poop',
        'rings': '支索環', 'stern-spars': '船尾桿', 'halyard-bitt': '升降索柱', 'cable-beam': '錨纜橫樑'}
YARD_LINK = {'main': '主桅', 'mizzen': '後桅'}


def seg_dist(p, q, a, b):
    """Shortest distance between segments pq and ab (3D)."""
    p, q, a, b = (np.asarray(v, float) for v in (p, q, a, b))
    d1, d2, r = q - p, b - a, p - a
    A, E, F = d1 @ d1, d2 @ d2, d2 @ r
    if A < 1e-12 and E < 1e-12:
        return float(np.linalg.norm(r))
    if A < 1e-12:
        s, t = 0.0, min(1.0, max(0.0, F / E))
    else:
        C = d1 @ r
        if E < 1e-12:
            t, s = 0.0, min(1.0, max(0.0, -C / A))
        else:
            B = d1 @ d2
            den = A * E - B * B
            s = min(1.0, max(0.0, (B * F - C * E) / den)) if den > 1e-12 else 0.0
            t = (B * s + F) / E
            if t < 0:
                t, s = 0.0, min(1.0, max(0.0, -C / A))
            elif t > 1:
                t, s = 1.0, min(1.0, max(0.0, (B - C) / A))
    return float(np.linalg.norm((p + d1 * s) - (a + d2 * t)))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    YC = plan['space']['yc']
    RG = plan['rigging']
    C = RG['colors']
    T = RG['thick']
    SK = RG['slack']
    M = os.path.join(design, 'masks')

    # ── everything placed before step 8 (design lists), split by work ──
    occ = ship_cells(design, plan)
    hull = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
    hull.update(load(os.path.join(M, 'step6', 'hull_recolor.vox.txt')))
    hull.update(load(os.path.join(M, 'step6', 'hull_add.vox.txt')))
    masts = {k: load(os.path.join(M, 'masts', f + '.vox.txt')) for k, f in
             (('mast-main', 'main'), ('mast-mizzen', 'mizzen'), ('jibboom', 'jibboom'), ('cable-beam', 'cable_beam'))}
    poop = load(os.path.join(M, 'decks', 'poop.vox.txt'))
    LAT = json.load(open(os.path.join(design, 'yards_lateen.json'), encoding='utf-8'))
    YP = {y['mast']: y for y in json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))}
    yards = {}
    for key in ('main', 'mizzen'):
        off = [int(round(YP[key]['at'][i] - YP[key]['pivot'][i])) for i in range(3)]
        yards[key] = {(x + off[0], y + off[1], z + off[2]): c for (x, y, z), c in load(os.path.join(M, 'yards', 'lateen-%s.vox.txt' % key)).items()}
    occ_all = dict(occ)
    for d_ in list(masts.values()) + list(yards.values()):
        occ_all.update(d_)

    def ypt(key, anchor):
        """A yard-model anchor in world coordinates (rotate 0, scale 1): at + (local + 0.5 - pivot)."""
        p = YP[key]
        loc = LAT[key]['anchors'][anchor]
        return [p['at'][i] + loc[i] + 0.5 - p['pivot'][i] for i in range(3)]

    # starboard outer y of the hull per (x, z), rail top per x
    yout, rail = {}, {}
    for (x, y, z) in hull:
        if y >= YC and y > yout.get((x, z), -1):
            yout[(x, z)] = y
        if z > rail.get(x, -1):
            rail[x] = z

    parts = {'rings': {}, 'stern-spars': {}, 'halyard-bitt': {}}
    skipped = {k: 0 for k in parts}

    def put(part, k, c):
        if k in occ_all:
            skipped[part] += 1
            return
        parts[part][k] = c

    anchors = {k: {} for k in LINK}

    # ── rings outside the hull (both sides; 1 x 1 x 3) ──
    SH = RG['shrouds']
    dxp = int(probe.get('ring_dx', 0))
    ring_xs = sorted(set([x + dxp for x in SH['main']['rings_x']] + SH['mizzen']['rings_x']))
    for x in ring_xs:
        zr = rail[x] - SH['ring_below_rail'] - 1
        yo = max(yout[(x, z)] for z in (zr - 1, zr, zr + 1))
        yflare = max(yout[(x, z)] for z in range(zr, rail[x] + 1))   # v5: the bow flares out above the ring
        for sd, sg in (('S', 1), ('P', -1)):
            ys = lambda k: (yo + k) if sg == 1 else (2 * YC - yo - k)
            for z in (zr - 1, zr, zr + 1):                      # strap on the side
                put('rings', (x, ys(1), z), C['ring'])
            kout = SH['ring_out'] + (yflare - yo)
            for k in range(2, kout + 1):                        # eye standing out, past the flare
                put('rings', (x, ys(k), zr), C['ring'])
            anchors['rings']['ring-%s-%d' % (sd, x)] = [x, ys(kout), zr]

    # ── stern spars: flagstaff on the taffrail, bumkin on the starboard quarter ──
    SS = RG['stern_spars']
    fs = SS['flagstaff']
    for z in range(fs['z0'], fs['z1'] + 1):
        c = C['cap'] if z > fs['z1'] - fs['cap'] else C['spar']
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            put('stern-spars', (fs['x'] + dx, fs['y'] + dy, z), c)
    bk = SS['bumkin']                                            # round spar between heel and tip cell centres
    h0, h1 = np.array(bk['heel'], float) + 0.5, np.array(bk['tip'], float) + 0.5
    ax_ = h1 - h0
    La = float(np.linalg.norm(ax_))
    lo_, hi_ = np.minimum(h0, h1) - 2, np.maximum(h0, h1) + 2
    for x in range(int(lo_[0]), int(hi_[0]) + 1):
        for y in range(int(lo_[1]), int(hi_[1]) + 1):
            for z in range(int(lo_[2]), int(hi_[2]) + 1):
                q = np.array([x + 0.5, y + 0.5, z + 0.5]) - h0
                t_ = float(q @ ax_) / La
                if -0.5 <= t_ <= La + 0.5 and float(np.linalg.norm(q - ax_ * (t_ / La))) <= bk['r'] + 1e-9:
                    put('stern-spars', (x, y, z), C['lash'] if x in bk['lash_x'] else C['spar'])
    tipc = max((k for k in parts['stern-spars'] if abs(k[0] - bk['tip'][0]) <= 0 and abs(k[1] - bk['tip'][1]) <= 1), key=lambda k: (k[2], k[1]))
    anchors['stern-spars']['bumkin-tip'] = list(tipc)
    anchors['stern-spars']['flag-top'] = [fs['x'] + 1, fs['y'], fs['z1'] - fs['cap']]

    # ── halyard bitt e on the quarterdeck ──
    BT = RG['bitt']
    for x in range(BT['x0'], BT['x1'] + 1):
        for y in range(BT['y0'], BT['y1'] + 1):
            for z in range(BT['z0'], BT['z1'] + 1):
                if z >= BT['top_from'] and (x in (BT['x0'], BT['x1']) or y in (BT['y0'], BT['y1'])):
                    continue                                     # upper part reduced to 3 x 3
                c = C['bitt']
                if BT['sheave_z'][0] <= z <= BT['sheave_z'][1] and y == (BT['y0'] + BT['y1']) // 2:
                    c = C['sheave']
                put('halyard-bitt', (x, y, z), c)
    ym = (BT['y0'] + BT['y1']) // 2
    for y in range(BT['y0'] - 2, BT['y1'] + 3):                  # cabillot through the reduced top
        if not (BT['y0'] < y < BT['y1']):
            put('halyard-bitt', ((BT['x0'] + BT['x1']) // 2, y, BT['pin_z']), C['spar'])
    anchors['halyard-bitt']['halyard'] = BT['anchor']                 # v5: inside the sheave slot (v4: the air cell in front)
    KV = BT['kevel']
    for x in range(KV['x0'], KV['x1'] + 1):
        for y in range(KV['y0'], KV['y1'] + 1):
            for z in range(KV['z0'], KV['z1'] + 1):
                put('halyard-bitt', (x, y, z), C['cap'] if z == KV['z1'] else C['bitt'])
    anchors['halyard-bitt']['halyard-mizzen'] = KV.get('anchor') or [KV['x1'] + 1, (KV['y0'] + KV['y1']) // 2, KV['z1'] - 1]   # step 11: plan may give it (fall from aft)

    # ── anchors on earlier works ──
    MS = masts['mast-main']
    anchors['mast-main']['hound-' + SH['main']['side']] = SH['main']['hound']
    anchors['mast-mizzen']['hound-' + SH['mizzen']['side']] = SH['mizzen']['hound']
    HY = RG['halyards']
    for i, (fx, fy, fz, ax_, ay, az) in enumerate(HY['main']['itagues'], 1):
        anchors['mast-main']['sheave-%d-fore' % i] = [fx, fy, fz]
        anchors['mast-main']['sheave-%d-aft' % i] = [ax_, ay, az]
    fx, fy, fz, ax_, ay, az = HY['mizzen']['itagues'][0]
    anchors['mast-mizzen']['sheave-fore'] = [fx, fy, fz]
    anchors['mast-mizzen']['sheave-aft'] = [ax_, ay, az]
    SL = RG['sails']
    anchors['mast-main']['foc-stay'] = SL['foc']['stay_to']
    anchors['mast-main']['parrel'] = [191, 77, 257]                  # v5: the yard hangs one cell off the mast (verifier: no drosse)
    anchors['mast-mizzen']['parrel'] = [108, 78, 187]
    if isinstance(SL['foc']['sheet_to'][0], str):
        anchors[SL['foc']['sheet_to'][0]]['foc-sheet'] = SL['foc']['sheet_to'][1]
    J = masts['jibboom']
    xt = max(x for (x, y, z) in J)
    tip = max(((x, y, z) for (x, y, z) in J if x == xt), key=lambda k: (k[2], -abs(k[1] - 87)))
    anchors['jibboom']['tip'] = list(tip)

    def rail_cell(x, side):
        z = rail[x]
        y = max(y for (xx, y, zz) in hull if xx == x and zz == z and y >= YC)
        return [x, y if side == 'S' else 2 * YC - y, z]
    anchors['hull']['tack-main'] = [SL['main']['tack_to'][0], SL['main']['tack_to'][1], max(z for (x, y, z) in hull if x == SL['main']['tack_to'][0] and y == SL['main']['tack_to'][1])]
    anchors['hull']['sheet-main-' + SL['main']['sheet_to'][1]] = rail_cell(*SL['main']['sheet_to'])
    anchors['hull']['tack-mizzen-' + SL['mizzen']['tack_to'][1]] = rail_cell(*SL['mizzen']['tack_to'])

    # anchor cells: on which work, solid or the air cell next to it
    work_cells = {'cable-beam': masts['cable-beam'], 'hull': hull, 'mast-main': MS, 'mast-mizzen': masts['mast-mizzen'], 'jibboom': J, 'deck-poop': poop,
                  'rings': parts['rings'], 'stern-spars': parts['stern-spars'], 'halyard-bitt': parts['halyard-bitt']}
    anchor_state = {}
    for w, items in anchors.items():
        for nm, p in items.items():
            k = tuple(p)
            if k in work_cells[w]:
                anchor_state['%s/%s' % (w, nm)] = 'solid'
            else:
                nb = any((k[0] + a, k[1] + b, k[2] + c) in work_cells[w] for a, b, c in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
                anchor_state['%s/%s' % (w, nm)] = 'air-next-to-work' if nb else 'AIR-FAR'

    cen = lambda p: [p[0] + 0.5, p[1] + 0.5, p[2] + 0.5]
    WP = {}                                            # endpoint spec -> world point (for the readings and the sheet)

    def A_(w, nm):
        spec = '%s/%s' % (LINK[w], nm)
        WP[spec] = cen(anchors[w][nm])
        return spec

    def X_(p):
        spec = '%.2f,%.2f,%.2f' % tuple(p)
        WP[spec] = list(p)
        return spec

    def Y_(key, anchor):
        """A yard-model point: an anchor name, or a local cell [x, y, z] (integers = cell centre)."""
        if isinstance(anchor, list):
            spec = 'model:%s/yard-%s-lateen/%d,%d,%d' % (YARD_LINK[key], key, anchor[0], anchor[1], anchor[2])
            p = YP[key]
            WP[spec] = [p['at'][i] + anchor[i] + 0.5 - p['pivot'][i] for i in range(3)]
            return spec
        spec = 'model:%s/yard-%s-lateen/%s' % (YARD_LINK[key], key, anchor)
        WP[spec] = ypt(key, anchor)
        return spec

    ropes = []

    def rope(name, a, b, group, th, slack, color, meta=None):
        ropes.append({'name': name, 'from': a, 'to': b, 'group': group, 'thickness': th, 'slack': slack, 'color': color, 'meta': meta})

    # ── shrouds: pendant (hounds -> block), block (short thick rope), falls (block -> ring) ──
    for key, w in (('main', 'mast-main'), ('mizzen', 'mast-mizzen')):
        S_ = SH[key]
        side = S_['side']
        if probe.get('side') == key:
            side = 'P' if side == 'S' else 'S'
        hk = 'hound-' + S_['side']
        if side != S_['side']:
            hp = list(S_['hound'])
            hp[1] = 2 * YC - hp[1]
            anchors[w]['hound-' + side] = hp
            hk = 'hound-' + side
        h = np.array(cen(anchors[w][hk]))
        xs = [x + (dxp if key == 'main' else 0) for x in S_['rings_x']]
        for i, x in enumerate(sorted(xs, reverse=True), 1):
            rn = 'ring-%s-%d' % (side, x)
            r = np.array(cen(anchors['rings'][rn]))
            long_ = (x - dxp) in S_['long_pendant']
            f = S_['long_block_frac'] if long_ else S_['block_frac']
            u = (r - h) / np.linalg.norm(r - h)
            b0 = h + f * (r - h)
            b1 = b0 + SH['block_len'] * u
            nm = '%s-shroud-%s-%d' % (key, side, i)
            rope(nm + '-pendant', A_(w, hk), X_(b0), 'standing/shrouds', T['pendant'], SK['standing'], C['linen'] if long_ else C['standing'], {'kind': 'shroud'})
            rope(nm + '-block', X_(b0), X_(b1), 'standing/blocks', T['block'], 1.0, C['block'])
            perp = np.cross(u, [0, 0, 1.0])
            perp = perp / np.linalg.norm(perp) if np.linalg.norm(perp) > 1e-6 else np.array([1.0, 0, 0])
            for k in range(SH['falls']):
                o = (k - (SH['falls'] - 1) / 2) * 2 * SH['fall_spread'] / max(1, SH['falls'] - 1)
                rope('%s-fall-%d' % (nm, k + 1), X_(b1 + o * perp), A_('rings', rn), 'standing/shroud-tackles', T['fall'], SK['standing'], C['running'], {'kind': 'shroud'})

    # ── halyards ──
    def halyard(key, w, itagues, lead, block_frac, nfalls, spread, to_spec, to_pt):
        sling = Y_(key, 'sling')
        names = sorted(n for n in anchors[w] if n.startswith('sheave'))
        fores = [n for n in names if n.endswith('fore')]
        afts = [n for n in names if n.endswith('aft')]
        aft_pts = [np.array(cen(anchors[w][n])) for n in afts]
        mid_aft = sum(aft_pts) / len(aft_pts)
        blk = mid_aft + block_frac * (np.array(to_pt) - mid_aft)
        u = (np.array(to_pt) - blk) / np.linalg.norm(np.array(to_pt) - blk)
        blk1 = blk + 4 * u
        for i, (fn, an) in enumerate(zip(fores, afts), 1):
            nm = '%s-itague-%d' % (key, i)
            ld = list(lead)
            ld[2] += 8 * (i - 1) if key == 'main' else 0
            rope(nm + '-up', sling, X_(ld), 'running/halyards', T['itague'], SK['halyard'], C['running'], {'kind': 'halyard'})
            rope(nm + '-lead', X_(ld), A_(w, fn), 'running/halyards', T['itague'], SK['halyard'], C['running'], {'kind': 'halyard'})
            al = np.array(cen(anchors[w][an])) + np.array(HY['aft_lead'], float)
            rope(nm + '-out', A_(w, an), X_(al), 'running/halyards', T['itague'], SK['halyard'], C['running'], {'kind': 'halyard'})
            rope(nm + '-down', X_(al), X_(blk), 'running/halyards', T['itague'], SK['halyard'], C['running'], {'kind': 'halyard'})
        rope('%s-halyard-block' % key, X_(blk), X_(blk1), 'running/blocks', T['block'] * 1.3, 1.0, C['block'])
        perp = np.cross(u, [0, 0, 1.0])
        perp = perp / np.linalg.norm(perp)
        for k in range(nfalls):
            o = (k - (nfalls - 1) / 2) * 2 * spread / max(1, nfalls - 1)
            rope('%s-halyard-fall-%d' % (key, k + 1), X_(blk1 + o * perp), to_spec, 'running/halyards', T['halyard_fall'], SK['halyard'], C['running'], {'kind': 'halyard'})
        return blk.tolist()
    hb_main = halyard('main', 'mast-main', HY['main']['itagues'], HY['main']['lead'], HY['main']['block_frac'], HY['main']['falls'], HY['main']['fall_spread'],
                      A_('halyard-bitt', 'halyard'), cen(anchors['halyard-bitt']['halyard']))
    hb_miz = halyard('mizzen', 'mast-mizzen', HY['mizzen']['itagues'], HY['mizzen']['lead'], HY['mizzen']['block_frac'], HY['mizzen']['falls'], HY['mizzen']['fall_spread'],
                     A_('halyard-bitt', 'halyard-mizzen'), cen(anchors['halyard-bitt']['halyard-mizzen']))
    for key, w in (('main', 'mast-main'), ('mizzen', 'mast-mizzen')):         # v5: parrel (PT drosse) closing the gap yard -> mast
        rope('%s-parrel' % key, Y_(key, 'pivot'), A_(w, 'parrel'), 'running/parrels', 2.0, 1.0, C['block'])

    # ── jib stay ──
    rope('foc-stay', A_('jibboom', 'tip'), A_('mast-main', 'foc-stay'), 'standing/stays', T['stay'], 1.0, C['standing'], {'kind': 'stay'})

    # ── sails ──
    sails = []

    def sail(name, corners, names, bind, free, meta, color=None, fullness=None, texture=None):
        sails.append({'name': name, 'corners': corners, 'corner_names': names, 'bind': bind, 'free': free, 'meta': meta,
                      'fullness': fullness or SL['fullness'], 'color': color or C['sail'], 'texture': texture})
    for key, w in (('main', 'mast-main'), ('mizzen', 'mast-mizzen')):
        S_ = SL[key]
        nm = S_['name']
        sail(nm, [Y_(key, 'fore'), Y_(key, S_.get('head_aft', 'peak')), X_(S_['clew']), X_(S_['tack'])], ['fore', 'peak', 'clew', 'tack'], [0], ['clew', 'tack'], S_['meta'],
             fullness=S_.get('fullness'))
        if S_['sheet_to'] == 'bumkin':
            sto = A_('stern-spars', 'bumkin-tip')
        else:
            sto = A_('hull', 'sheet-%s-%s' % (key, S_['sheet_to'][1]))
        rope(nm + '.sheet', 'sail:%s/clew' % nm, sto, 'running/sheets', T['sheet'], SK['sheet'], C['running'], {'kind': 'sheet', 'sail': nm})
        tto = A_('hull', 'tack-main') if key == 'main' else A_('hull', 'tack-mizzen-%s' % S_['tack_to'][1])
        rope(nm + '.tack', 'sail:%s/tack' % nm, tto, 'running/tacks', T['tack'], SK['tack'], C['running'], {'kind': 'tack', 'sail': nm})
        WP['sail:%s/clew' % nm] = list(S_['clew'])
        WP['sail:%s/tack' % nm] = list(S_['tack'])
    F = SL['foc']
    tp, sp = np.array(cen(anchors['jibboom']['tip'])), np.array(cen(anchors['mast-main']['foc-stay']))
    head = tp + F['head_frac'] * (sp - tp)
    sail('foc', [A_('jibboom', 'tip'), X_(head), X_(F['clew'])], ['tack', 'head', 'clew'], [0], ['clew'], F['meta'])
    rope('foc.sheet', 'sail:foc/clew', A_(F['sheet_to'][0], 'foc-sheet'), 'running/sheets', T['sheet'], F.get('sheet_slack', SK['sheet']), C['running'], {'kind': 'sheet', 'sail': 'foc'})
    WP['sail:foc/clew'] = list(F['clew'])
    # flags
    FL = RG['flags']
    E = FL['ensign']
    hx = fs['x'] + 2.15                                      # hoist 0.15 off the fore face of the staff (v4 +2.5 flew 0.5 off it; on the face the cloth dips into the staff)
    ztop = fs['z1'] - fs['cap'] + 0.5
    ens = [[hx, fs['y'] + 0.5, ztop], [hx + E['fly'], fs['y'] + 0.5, ztop], [hx + E['fly'], fs['y'] + 0.5, ztop - E['hoist']], [hx, fs['y'] + 0.5, ztop - E['hoist']]]
    sail('ensign', [X_(p) for p in ens], None, [3], [1, 2], E['meta'], color=C['flag'], fullness=1.04, texture='textures/ensign.png')
    PN = FL['pennant']
    tz = max(z for (x, y, z) in MS)
    fx_ = max(x for (x, y, z) in MS if z == tz) + 1.15         # 0.15 off the fore face of the truck (v4 flew 0.5 off it)
    pen = [[fx_, YC + 0.5, tz + 0.5], [fx_ + PN['len'], YC + 0.5, tz + 0.5 - PN['hoist'] / 2], [fx_, YC + 0.5, tz + 0.5 - PN['hoist']]]
    sail('pennant', [X_(p) for p in pen], None, [2], [1], PN['meta'], color=C['flag'], fullness=1.04)

    metas = [['sail', s['name'], s['meta']] for s in sails] + [['rope', r['name'], r['meta']] for r in ropes if r['meta']]
    if 'nometa' in probe:
        metas = [m for m in metas if not (m[0] == 'rope' and m[1] == probe['nometa'])]

    # ── readings ──
    R = {'probe': probe or None}
    new_all = {}
    for p_ in parts.values():
        new_all.update(p_)
    R['parts'] = {}
    for nm, cl in parts.items():
        G = np.zeros((480, 160, 400), bool)
        for k in cl:
            G[k] = True
        lab, n = ndimage.label(G)
        N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
        touch = sum(1 for (x, y, z) in cl if any((x + a, y + b, z + c) in occ_all for a, b, c in N6))
        comp_touch = {int(lab[k]) for k in cl if any((k[0] + a, k[1] + b, k[2] + c) in occ_all for a, b, c in N6)}
        cols = {}
        for c in cl.values():
            cols[str(c)] = cols.get(str(c), 0) + 1
        R['parts'][nm] = {'cells': len(cl), 'skipped_on_ship': skipped[nm], 'components_6': int(n), 'cells_touching_ship': touch,
                          'components_not_touching_ship': int(n) - len(comp_touch), 'colours': cols,
                          'mirror_diff': sum(1 for (x, y, z), c in cl.items() if cl.get((x, 2 * YC - y, z)) != c)}
    G = np.zeros((480, 160, 400), bool)
    for k in list(occ_all) + list(new_all):
        G[k] = True
    lab, n = ndimage.label(G)
    G0 = np.zeros((480, 160, 400), bool)
    for k in occ_all:
        G0[k] = True
    R['ship_with_new_parts'] = {'cells': int(G.sum()), 'components_6': int(n), 'components_6_before': int(ndimage.label(G0)[1]),
                                'note': 'the two yards are models one cell off their masts ⇒ 3 components before step 8'}
    # the new parts must not touch the gun-port fields or the swivel stations (same measure as step 6 v2: follows the side)
    sw = plan['ports']['swivels']
    near_sw = {}
    for sx in sw['x'] + [sw['bow']['x']]:
        ztop_ = max(z for (x, y, z) in hull if x == sx)
        ys = min(y for (x, y, z) in hull if x == sx and z >= ztop_ - 2 and y < YC)
        near_sw[str(sx)] = sum(1 for (x, y, z) in new_all if abs(x - sx) <= 4 and z >= ztop_ - 3 and (y <= ys + 6 or y >= 2 * YC - ys - 6))
    R['new_cells_near_swivel_stations'] = near_sw
    sys.path.insert(0, design)
    import layout as LY
    near_port = 0
    for p in LY.ports(plan):                              # in front of the port and the gun's recoil space (2 m in from the side)
        ys = min(y for (x, y, z) in hull if p['x0'] <= x <= p['x1'] and z >= p['z0'] and y < YC)
        for (x, y, z) in new_all:
            if p['x0'] - 2 <= x <= p['x1'] + 2 and p['z0'] - 2 <= z <= p['z1'] + 2 and (y <= ys + 20 or y >= 2 * YC - ys - 20):
                near_port += 1
    R['new_cells_in_gun_port_fields'] = near_port
    R['anchors'] = {k: len(v) for k, v in anchors.items()}
    R['anchor_cells'] = anchor_state
    R['anchors_far_from_their_work'] = sorted(k for k, v in anchor_state.items() if v == 'AIR-FAR')

    # ropes through solid cells: straight segment (slack <= 1.03), samples 0.25 cells apart, 2 cells left out at each end;
    # clearance = distance from the sample to the nearest solid cell centre - 0.5 (cube) - tube radius
    solid = np.zeros((480, 160, 400), bool)
    for k in list(occ_all) + list(new_all):
        solid[k] = True
    edt = ndimage.distance_transform_edt(~solid)

    def pt(spec):
        return np.array(WP[spec], float)
    rope_clear = {}
    from scipy.spatial import cKDTree
    SC = np.argwhere(solid)
    KT = cKDTree(SC + 0.5)

    def cube_dist(q):
        """Exact distance from point q to the nearest solid unit cube (v2: the verifier showed edt-0.5 misses tube contacts)."""
        idx = KT.query_ball_point(q, 3.5)
        if not idx:
            return 9.0
        c = SC[idx].astype(float)
        d = np.maximum(np.maximum(c - q, q - (c + 1.0)), 0.0)
        return float(np.sqrt((d * d).sum(1)).min())
    for r in ropes:
        a, b = pt(r['from']), pt(r['to'])
        L = np.linalg.norm(b - a)
        worst, hits, where = 1e9, 0, None
        # v5: a rope that ends INSIDE its anchor (ring eye, sheave slot) enters solid there by design ⇒ skip the solid run
        #   connected to each end, then 2 cells more (v4: a fixed 2 cells only)
        ss_ = np.arange(0.0, L + 1e-9, 0.25)
        insol = np.array([solid[tuple(int(math.floor(v)) for v in a + (b - a) * (s / L))] for s in ss_])
        lo_s, hi_s = 0.0, L
        i0 = 0
        while i0 < len(ss_) and insol[i0]:
            i0 += 1
        i1 = len(ss_) - 1
        while i1 >= 0 and insol[i1]:
            i1 -= 1
        lo_s = (ss_[i0] if i0 < len(ss_) else L) + 2.0
        hi_s = (ss_[i1] if i1 >= 0 else 0.0) - 2.0
        for s in np.arange(lo_s, hi_s + 1e-9, 0.25):
            q = a + (b - a) * (s / L)
            i, j, k = (int(math.floor(v)) for v in q)
            if solid[i, j, k]:
                hits += 1
                worst, where = -1.0, q
                continue
            if edt[i, j, k] > 4.5:
                continue
            cl = cube_dist(q) - r['thickness'] / 2
            if cl < worst:
                worst, where = cl, q
        rope_clear[r['name']] = {'len_cells': round(float(L), 1), 'samples_in_solid': hits, 'min_clearance': None if worst == 1e9 else round(float(worst), 2),
                                 'at': None if where is None else [round(float(v), 1) for v in where]}
    R['ropes_through_solid'] = sorted(n for n, v in rope_clear.items() if v['samples_in_solid'])
    R['rope_min_clearance'] = sorted(((v['min_clearance'], n) for n, v in rope_clear.items() if v['min_clearance'] is not None))[:8]
    R['ropes_tube_touching_solid'] = sorted(n for n, v in rope_clear.items() if v['min_clearance'] is not None and v['min_clearance'] < 0)
    # rope vs rope (surface to surface), pairs that share no endpoint and do not belong to the same shroud / halyard
    fam = lambda n: n.split('-pendant')[0].split('-block')[0].split('-fall')[0] if 'shroud' in n else (n.split('-')[0] + '-halyard' if ('itague' in n or 'halyard' in n) else n)
    rr = []
    for i in range(len(ropes)):
        for j in range(i + 1, len(ropes)):
            a, b = ropes[i], ropes[j]
            if {a['from'], a['to']} & {b['from'], b['to']} or fam(a['name']) == fam(b['name']):
                continue
            dd = seg_dist(pt(a['from']), pt(a['to']), pt(b['from']), pt(b['to'])) - (a['thickness'] + b['thickness']) / 2
            rr.append((round(dd, 2), a['name'], b['name']))
    R['rope_rope_closest'] = sorted(rr)[:6]

    # flat sails (corner polygons before the cloth settles): ropes that pass through a sail polygon
    def tris(s):
        P_ = [np.array(WP[c] if c in WP else 0, float) for c in s['corners']]
        return [(P_[0], P_[1], P_[2])] + ([(P_[0], P_[2], P_[3])] if len(P_) == 4 else [])

    def seg_tri(a, b, t):
        e1, e2 = t[1] - t[0], t[2] - t[0]
        d = b - a
        h = np.cross(d, e2)
        det = e1 @ h
        if abs(det) < 1e-9:
            return False
        f = 1.0 / det
        s = a - t[0]
        u = f * (s @ h)
        q = np.cross(s, e1)
        v = f * (d @ q)
        w = f * (e2 @ q)
        return 0.02 < u and 0.02 < v and u + v < 0.98 and 0.02 < w < 0.98
    through = []
    for s in sails:
        own = {s['name']}
        for r in ropes:
            if r['from'].startswith('sail:' + s['name']) or r['to'].startswith('sail:' + s['name']):
                continue
            if s['name'] == 'foc' and r['name'] == 'foc-stay':
                continue
            a, b = pt(r['from']), pt(r['to'])
            if any(seg_tri(a, b, t) for t in tris(s)):
                through.append('%s × %s' % (r['name'], s['name']))
    R['ropes_through_flat_sails'] = through

    # yard sweeps (Ship_Masts §5 lateen limit asin(2.5 m / pivot->fore horizontal), from verify_masts.json) vs ropes
    VM = json.load(open(os.path.join(design, 'verify_masts.json'), encoding='utf-8'))
    lim = {k: VM['yards'][k]['lateen_swing_limit_deg'] for k in ('main', 'mizzen')} if 'lateen_swing_limit_deg' in VM['yards']['main'] else {'main': 9.5, 'mizzen': 23.4}
    sweep = {}
    for key in ('main', 'mizzen'):
        pv = np.array(YP[key]['at'], float)
        ends = [np.array(ypt(key, 'fore')), np.array(ypt(key, 'peak'))]
        best = (1e9, None, None)
        other = (1e9, None, None)                            # closest rope of the OTHER mast's shrouds (the ring_dx control moves it)
        for ang in np.linspace(-lim[key], lim[key], 25):
            th = math.radians(ang)
            Rz = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
            segs = [(pv, pv + Rz @ (e - pv)) for e in ends]
            for r in ropes:
                if r['from'].startswith('model:%s/yard-%s' % (YARD_LINK[key], key)) or 'sail:' in r['from'] or r['name'].startswith(key + '-itague') \
                        or r['name'].startswith(key + '-halyard'):
                    continue
                for a_, b_ in segs:
                    dd = seg_dist(pt(r['from']), pt(r['to']), a_, b_) - r['thickness'] / 2
                    if dd < best[0]:
                        best = (dd, r['name'], round(float(ang), 1))
                    if 'shroud' in r['name'] and not r['name'].startswith(key) and dd < other[0]:
                        other = (dd, r['name'], round(float(ang), 1))
        sweep[key] = {'limit_deg': lim[key], 'min_axis_to_rope': round(best[0], 2), 'rope': best[1], 'at_deg': best[2],
                      'min_to_other_mast_shrouds': round(other[0], 2), 'other_rope': other[1]}
    R['yard_sweep_vs_ropes'] = sweep

    # sail set (Ship_Rigging §9.1)
    DEF = {'topsail': 1, 'jib': 1, 'topgallant': 2, 'gaff': 2}
    stage = {s['name']: int(s['meta'].get('set', DEF.get(s['meta']['sail'], 3))) for s in sails if s['meta']['kind'] == 'sail'}
    R['sail_set'] = {str(k): sorted(n for n, st in stage.items() if st <= k) for k in (1, 2, 3)}
    R['sail_set_ok'] = bool(R['sail_set']['1'] and R['sail_set']['2'] and R['sail_set']['1'] != R['sail_set']['2'] != R['sail_set']['3'])
    names = [r['name'] for r in ropes]
    have = {m[1] for m in metas if m[0] == 'rope'}
    need = [r['name'] for r in ropes if '.' in r['name'] and r['name'].split('.')[0] in {s['name'] for s in sails}]
    R['sail_ropes_without_meta'] = sorted(set(need) - have)
    R['sail_rope_meta_wrong'] = sorted(m[1] for m in metas if m[0] == 'rope' and m[1] in need and m[2].get('sail') != m[1].split('.')[0])
    R['dup_rope_names'] = len(names) - len(set(names))
    R['counts'] = {'ropes': len(ropes), 'sails': sum(1 for s in sails if s['meta']['kind'] == 'sail'), 'flags': sum(1 for s in sails if s['meta']['kind'] == 'flag'),
                   'groups': {g: sum(1 for r in ropes if r['group'] == g) for g in sorted({r['group'] for r in ropes})}, 'meta_sails': sum(1 for m in metas if m[0] == 'sail'),
                   'meta_ropes': len(have)}
    # PT luff : leech for the two lateens (flat, before the cloth settles)
    ratio = {}
    for s in sails[:2]:
        P_ = [np.array(WP[c]) for c in s['corners']]
        luff, leech = np.linalg.norm(P_[0] - P_[3]) * 0.1, np.linalg.norm(P_[1] - P_[2]) * 0.1
        ratio[s['name']] = {'luff_m': round(float(luff), 1), 'leech_m': round(float(leech), 1), 'leech_over_luff': round(float(leech / luff), 2),
                            'foot_m': round(float(np.linalg.norm(P_[2] - P_[3]) * 0.1), 1)}
    R['lateen_shape'] = ratio
    R['halyard_blocks'] = {'main': [round(v, 1) for v in hb_main], 'mizzen': [round(v, 1) for v in hb_miz]}
    if probe:
        keys = {'nometa': ['sail_ropes_without_meta'], 'ring_dx': ['yard_sweep_vs_ropes', 'ropes_through_flat_sails'], 'side': ['ropes_through_flat_sails']}
        print(json.dumps({k: R[k] for kk in probe for k in keys.get(kk, [])} | {'probe': probe}, ensure_ascii=False))
        return

    # ── write ──
    os.makedirs(os.path.join(M, 'rigging'), exist_ok=True)
    sha = {}
    for nm, fn in (('rings', 'rings'), ('stern-spars', 'stern_spars'), ('halyard-bitt', 'halyard_bitt')):
        p = os.path.join(M, 'rigging', fn + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('# Star step 8: %s (world coordinates, at 0,0,0)\n' % nm)
            for k in sorted(parts[nm]):
                fh.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], parts[nm][k]))
        sha[fn] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    os.makedirs(os.path.join(design, 'textures'), exist_ok=True)
    tw, th_ = E['texture']
    Image.new('RGBA', (tw, th_), (180, 18, 30, 255)).save(os.path.join(design, 'textures', 'ensign.png'))
    works = {k: (HULL if k == 'hull' else '%s-%s' % (HULL, k)) for k in LINK}
    out = {'anchors': anchors, 'anchor_works': works, 'links': LINK, 'ropes': ropes, 'sails': sails, 'meta': metas,
           'wind': SL['wind'], 'sail_seconds': SL['sail_seconds'], 'points': WP}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    R['sha256'] = sha
    R['rope_clearance'] = rope_clear
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)

    # ── sheet 06: side elevation, plan view, stern view ──
    sc = 2
    W, H = 480 * sc + 80, 400 * sc + 160 * sc + 220
    img = Image.new('RGB', (W, H), (250, 248, 240))
    d = ImageDraw.Draw(img)
    d.text((40, 16), 'Star (al-Najm) sheet 06: rigging, sails, flags (step 8, TASK-0019)', fill=(20, 20, 20), font=font(22))
    d.text((40, 46), 'side = projection along y; sails drawn flat (corner polygons, before the cloth settles); blue = sails, dark = standing, tan = running, red = flags', fill=(60, 60, 60), font=font(14))
    oz = 80 + 400 * sc
    Xs = lambda x: 40 + x * sc
    Zs = lambda z: oz - z * sc
    side = {}
    for src, colfn in ((occ, lambda c: (215, 200, 175)), (masts['mast-main'], palette_rgb), (masts['mast-mizzen'], palette_rgb), (masts['jibboom'], palette_rgb),
                       (yards['main'], palette_rgb), (yards['mizzen'], palette_rgb), (new_all, palette_rgb)):
        for (x, y, z), c in src.items():
            side[(x, z)] = colfn(c)
    for (x, z), rgb in side.items():
        d.rectangle([Xs(x), Zs(z + 1), Xs(x + 1) - 1, Zs(z) - 1], fill=rgb)

    def hexrgb(h):
        return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    for s in sails:
        P_ = [WP[c] for c in s['corners']]
        col = (200, 40, 50) if s['meta']['kind'] == 'flag' else (70, 110, 190)
        d.polygon([(Xs(p[0]), Zs(p[2])) for p in P_], outline=col, width=2)
    for r in ropes:
        a, b = WP[r['from']], WP[r['to']]
        d.line([Xs(a[0]), Zs(a[2]), Xs(b[0]), Zs(b[2])], fill=hexrgb(r['color']) if r['color'] != C['linen'] else (150, 140, 110), width=max(1, int(round(r['thickness']))))
    # plan view (z max projection), below
    oy = oz + 30
    d.text((40, oy - 22), 'from above (y down = starboard)', fill=(20, 20, 20), font=font(15))
    top = {}
    for src in (occ, masts['mast-main'], masts['mast-mizzen'], masts['jibboom'], masts['cable-beam'], yards['main'], yards['mizzen'], new_all):
        for (x, y, z), c in src.items():
            if z >= top.get((x, y), (-1,))[0]:
                top[(x, y)] = (z, c)
    for (x, y), (z, c) in top.items():
        d.rectangle([Xs(x), oy + y * sc, Xs(x + 1) - 1, oy + (y + 1) * sc - 1], fill=palette_rgb(c))
    for s in sails:
        P_ = [WP[c] for c in s['corners']]
        col = (200, 40, 50) if s['meta']['kind'] == 'flag' else (70, 110, 190)
        d.polygon([(Xs(p[0]), oy + p[1] * sc) for p in P_], outline=col, width=2)
    for r in ropes:
        a, b = WP[r['from']], WP[r['to']]
        d.line([Xs(a[0]), oy + a[1] * sc, Xs(b[0]), oy + b[1] * sc], fill=hexrgb(r['color']) if r['color'] != C['linen'] else (150, 140, 110), width=1)
    img.save(os.path.join(design, 'sheet06_rigging_v1.png'), optimize=False)
    print(json.dumps({k: R[k] for k in R if k not in ('rope_clearance', 'anchor_cells')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
