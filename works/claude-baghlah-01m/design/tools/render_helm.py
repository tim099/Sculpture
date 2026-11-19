# Step 11 process pictures (no GPU here, so orthographic projections of the design lists, like tools/render_gear.py):
#   overlays/stage11_stern_starboard.png  stern from starboard (rudder, stock through the counter, tiller over the poop)
#   overlays/stage11_poop_top.png         poop deck from above (tiller, collar, binnacle, kevel, mizzen)
#   overlays/stage11_bow_starboard.png    bow from starboard (stem rollers, anchors on the well deck seen through the side cut at y 88)
#   Usage: python -X utf8 tools/render_helm.py <design>
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

design = os.path.abspath(sys.argv[1])
sys.path.insert(0, design)
from draft_masts import ship_cells, load
from draft_lines import palette_rgb
from draft_helm import Grapnel
from draft_gear import Model

plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
M = os.path.join(design, 'masks')
PL = json.load(open(os.path.join(design, 'helm_placement.json'), encoding='utf-8'))
A = ship_cells(design, plan)
for sub in ('masts', 'rigging', 'gunfittings'):
    for f in sorted(os.listdir(os.path.join(M, sub))):
        A.update(load(os.path.join(M, sub, f)))
for f in ('magazine', 'skids'):
    A.update(load(os.path.join(M, 'gear', f + '.vox.txt')))
for rel in PL['carve'].values():
    for k in load(os.path.join(M, rel + '.vox.txt')):
        A.pop(k, None)
NEW = {}
for f in ('rudder', 'tiller', 'fittings', 'rollers'):
    NEW.update(load(os.path.join(M, 'helm', f + '.vox.txt')))
gsrc = np.loadtxt(os.path.join(M, 'helm_src', PL['anchors'][0]['work'] + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
for a in PL['anchors']:
    g = Grapnel(gsrc[:, :3].astype(float), a['pivot'], a['scale'], a['rotate'], a['mirror'] == 'y')
    for p, c in zip(np.floor(g.world(g.centers, a['at'])).astype(int).tolist(), gsrc[:, 3].tolist()):
        NEW[tuple(p)] = c
GP = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))
for r in GP['models']:
    if r['name'] != '羅經櫃':
        continue
    s = np.loadtxt(os.path.join(M, 'gear_src', r['work'] + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    g = Model(s[:, :3].astype(float), r['pivot'], r['scale'], r['rotate'])
    for p, c in zip(np.floor(g.world(g.centers, r['at'])).astype(int).tolist(), s[:, 3].tolist()):
        A.setdefault(tuple(p), c)


def shade(c, k):
    return tuple(int(v * k) for v in c)


def project(xr, vr, depth, key, k, path, title, new_bright=True, cut=None):
    """xr: horizontal range, vr: vertical range, depth: iterable of the third axis (nearest first); key(x, v, d) -> cell."""
    W, H = (xr[1] - xr[0]) * k, (vr[1] - vr[0]) * k + 30
    im = Image.new('RGB', (W, H), (235, 240, 245))
    d = ImageDraw.Draw(im)
    d.text((6, 6), title, fill=(0, 0, 0))
    for x in range(*xr):
        for v in range(*vr):
            for i, dd in enumerate(depth):
                c = key(x, v, dd)
                if c in NEW:
                    col = palette_rgb(NEW[c])
                elif c in A:
                    col = shade(palette_rgb(A[c]), 0.85 - min(i, 40) * 0.006)
                else:
                    continue
                px, py = (x - xr[0]) * k, 30 + (vr[1] - 1 - v) * k
                d.rectangle([px, py, px + k - 1, py + k - 1], fill=col)
                break
    im.save(path)


O = os.path.join(os.path.dirname(design), 'overlays')
project((10, 130), (-2, 100), range(130, 30, -1), lambda x, v, y: (x, y, v), 6, os.path.join(O, 'stage11_stern_starboard.png'),
        'stage 11: stern from starboard (rudder + stock, tiller over the poop)')
project((20, 125), (30, 131), range(110, 60, -1), lambda x, v, z: (x, v, z), 7, os.path.join(O, 'stage11_poop_top.png'),
        'stage 11: poop deck from above (tiller, collar, binnacle, kevel, mizzen)')
project((290, 400), (40, 100), range(88, 30, -1), lambda x, v, y: (x, y, v), 7, os.path.join(O, 'stage11_bow_starboard.png'),
        'stage 11: bow from starboard, cut at y 88 (stem rollers, anchor S on the well deck)')
print('ok')
