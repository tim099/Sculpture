# Step 10 process images (no GPU here ⇒ orthographic sections from the design lists, like render_guns.py):
#   overlays/stage10_magazine_x105.png  cross-section through the magazine (barrels as their model cells)
#   overlays/stage10_well_y65.png       long section through the fore well, port side (the hearth model, the cable beam)
#   overlays/stage10_waist_top.png      main deck waist from above (hatch covers, skids, boat, hearth as model cells)
#   Usage: python -X utf8 tools/render_gear.py <design>
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
sys.path.insert(0, design)
from draft_lines import palette_rgb, font
from draft_masts import ship_cells, load
import draft_gear as DGR

plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
M = os.path.join(design, 'masks')
occ = ship_cells(design, plan)
for f in ('main', 'mizzen', 'jibboom', 'cable_beam'):
    occ.update(load(os.path.join(M, 'masts', f + '.vox.txt')))
for f in ('rings', 'stern_spars', 'halyard_bitt'):
    occ.update(load(os.path.join(M, 'rigging', f + '.vox.txt')))
occ.update(load(os.path.join(M, 'gunfittings', 'gunfittings.vox.txt')))
for f in ('magazine', 'skids'):
    occ.update(load(os.path.join(M, 'gear', f + '.vox.txt')))
PL = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))
GB = plan['gear_build']
models = {}                                                    # world cell -> colour (model cells, by their centres)
for r in PL['models']:
    if r['work'] == GB['hearth']['work']:
        src = np.array([[x, y, z, c] for (x, y, z), c in load(os.path.join(M, 'gear', 'hearth.vox.txt')).items()])
    else:
        src = np.loadtxt(os.path.join(M, 'gear_src', r['work'] + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    g = DGR.Model(src[:, :3], r['pivot'], r['scale'], r['rotate'])
    W = np.floor(g.world(g.centers, r['at'])).astype(int)
    for (x, y, z), c in zip(W.tolist(), src[:, 3].tolist()):
        models.setdefault((x, y, z), c)
out = os.path.join(os.path.dirname(design), 'overlays')


def draw(name, title, ax, rng_u, rng_v, slab, k):
    nu, nv = rng_u[1] - rng_u[0], rng_v[1] - rng_v[0]
    im = Image.new('RGB', (nu * k + 40, nv * k + 70), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), title, fill=(0, 0, 0), font=font(16))
    for u in range(*rng_u):
        for v in range(*rng_v):
            col = None
            for s in slab:
                p = ax(u, v, s)
                if p in models:
                    col = palette_rgb(models[p])
                    break
                if p in occ:
                    col = palette_rgb(occ[p])
                    break
            if col:
                px, py = 20 + (u - rng_u[0]) * k, 50 + (rng_v[1] - 1 - v) * k
                d.rectangle([px, py, px + k - 1, py + k - 1], fill=col)
    im.save(os.path.join(out, name))
    print('✓', name)


draw('stage10_magazine_x105.png', '星辰號 步驟 10：彈藥庫橫剖面 x 105（往船頭看；火藥桶是模型的格、中間是後桅腳）', lambda u, v, s: (s, u, v), (36, 125), (30, 70), [105], 8)
draw('stage10_well_y65.png', '星辰號 步驟 10：水槽縱剖面 y 65（左舷，往右舷看；沙箱灶、錨纜橫樑）', lambda u, v, s: (u, s, v), (280, 345), (44, 80), [65], 10)
draw('stage10_waist_top.png', '星辰號 步驟 10：船腰俯視（艙蓋、小艇架、小艇、水槽的沙箱灶）', lambda u, v, s: (u, v, s), (196, 336), (30, 131),
     list(range(90, 40, -1)), 5)
