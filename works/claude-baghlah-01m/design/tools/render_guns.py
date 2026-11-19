# Step 9 process pictures (TASK-0019; no GPU on this machine ⇒ orthographic projections of the design lists + gun cells):
#   overlays/stage9_main_deck_top.png   main deck from above (everything below z 70), guns, fittings, gun tackle (straight)
#   overlays/stage9_port_section.png    cross-section through one port (default port 5): hull, deck, both guns, rings, tackle
#   overlays/stage9_poop_swivels.png    poop / helm rail from above (z ≤ 95) with the swivels and their arcs
#   Usage: python -X utf8 tools/render_guns.py <design> [port]
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

design = os.path.abspath(sys.argv[1])
port = int(sys.argv[2]) if len(sys.argv) > 2 else 5
sys.path.insert(0, design)
import draft_guns as DG
from draft_masts import ship_cells, load
from draft_lines import font, palette_rgb

plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
GB = plan['guns_build']
M = os.path.join(design, 'masks')
occ = ship_cells(design, plan)
for f in ('main', 'mizzen', 'jibboom', 'cable_beam'):
    occ.update(load(os.path.join(M, 'masts', f + '.vox.txt')))
for f in ('rings', 'stern_spars', 'halyard_bitt'):
    occ.update(load(os.path.join(M, 'rigging', f + '.vox.txt')))
fit = load(os.path.join(M, 'gunfittings', 'gunfittings.vox.txt'))
occ.update(fit)
PL = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']
PTS = json.load(open(os.path.join(design, 'gunfittings_points.json'), encoding='utf-8'))['anchors']
GR = json.load(open(os.path.join(design, 'gun_ropes.json'), encoding='utf-8'))['ropes']
guns = {k: DG.Gun(k, t, design, GB['search']['inset']) for k, t in GB['types'].items()}
rows = {r['name']: r for r in PL}
gun_cells = {}
for r in PL:
    g = guns[r['type']]
    gun_cells[r['name']] = (np.floor(g.world(g.centers, r['at'], r['phi'], r['side'] == 'P')).astype(int), 36 if r['type'] == '4l' else 73)
OUT = os.path.join(os.path.dirname(design), 'overlays')


def rope_pts(r):
    nm, anc = r['from'].split('/')[1], r['from'].rsplit('/', 1)[1]
    rr = rows[nm]
    g = guns[rr['type']]
    a = g.world(g.anchors[anc][None], rr['at'], rr['phi'], rr['side'] == 'P')[0]
    b = np.array(PTS[r['to'].split('/', 1)[1]], float) + 0.5
    return a, b


def top_view(path, x0, x1, zmax, sc, title, swivels=False):
    W_, H_ = (x1 - x0) * sc + 60, 160 * sc + 70
    img = Image.new('RGB', (W_, H_), (250, 248, 242))
    d = ImageDraw.Draw(img)
    d.text((20, 10), title, fill=(20, 20, 20), font=font(15))
    top = {}
    for (x, y, z), c in occ.items():
        if x0 <= x < x1 and z <= zmax and z >= top.get((x, y), (-1,))[0]:
            top[(x, y)] = (z, c)
    for r in PL:
        cells, col = gun_cells[r['name']]
        for x, y, z in cells:
            if x0 <= x < x1 and z <= zmax + 10 and z >= top.get((x, y), (-1,))[0]:
                top[(x, y)] = (z, col)
    X = lambda x: 30 + (x - x0) * sc
    Y = lambda y: 40 + y * sc
    for (x, y), (z, c) in top.items():
        d.rectangle([X(x), Y(y), X(x + 1) - 1, Y(y + 1) - 1], fill=palette_rgb(c))
    for r in GR:
        a, b = rope_pts(r)
        if x0 <= a[0] < x1:
            d.line([X(a[0]), Y(a[1]), X(b[0]), Y(b[1])], fill=(181, 154, 106), width=1)
    if swivels:
        for r in PL:
            if not r['swivel']:
                continue
            g = guns[r['type']]
            a0, a1 = [float(v) for v in r['arc'].split(',')]
            pts = [g.world(g.anchors['muzzle'][None], r['at'], a, r['side'] == 'P')[0] for a in np.arange(a0, a1 + 1e-9, 5)]
            d.line([(X(p[0]), Y(p[1])) for p in pts], fill=(220, 120, 0), width=2)
    img.save(path, optimize=False)


def section(path, pi, sc=8):
    r = next(q for q in PL if q['port'] == pi and q['side'] == 'S')
    xs = range(r['opening']['x'][0] - 1, r['opening']['x'][1] + 2)
    W_, H_ = 160 * sc + 60, 50 * sc + 70
    img = Image.new('RGB', (W_, H_), (250, 248, 242))
    d = ImageDraw.Draw(img)
    d.text((20, 10), 'Star sheet: section through port %d (x %d-%d, looking forward), guns, rings, tackle' % (pi, xs[0], xs[-1]), fill=(20, 20, 20), font=font(15))
    z0 = 40
    X = lambda y: 30 + y * sc
    Z = lambda z: 40 + (50 - (z - z0)) * sc
    best = {}
    for (x, y, z), c in occ.items():
        if x in xs and z0 <= z < z0 + 50 and (x < best.get((y, z), (999,))[0]):
            best[(y, z)] = (x, c)
    for nm in (r['name'], r['name'].replace('-S', '-P')):
        cells, col = gun_cells[nm]
        for x, y, z in cells:
            if x in xs and z0 <= z < z0 + 50:
                best[(y, z)] = (-1, col)
    for (y, z), (x, c) in best.items():
        d.rectangle([X(y), Z(z + 1), X(y + 1) - 1, Z(z) - 1], fill=palette_rgb(c))
    for rp in GR:
        if rp['from'].split('/')[1] in (r['name'], r['name'].replace('-S', '-P')):
            a, b = rope_pts(rp)
            d.line([X(a[1]), Z(a[2]), X(b[1]), Z(b[2])], fill=(181, 154, 106), width=2)
    img.save(path, optimize=False)


top_view(os.path.join(OUT, 'stage9_main_deck_top.png'), 40, 300, 70, 5, 'Star step 9: main deck from above (z <= 70) -- 22 x 4l, wall + deck rings, gun tackle (straight lines)')
section(os.path.join(OUT, 'stage9_port_section.png'), port)
top_view(os.path.join(OUT, 'stage9_poop_swivels.png'), 20, 160, 95, 7, 'Star step 9: poop / helm rail from above (z <= 95) -- 8 pierrier swivels, muzzle arcs', swivels=True)
print('ok')
