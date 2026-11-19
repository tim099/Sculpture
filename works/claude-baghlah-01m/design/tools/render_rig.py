# Step 8 process images (TASK-0019) without a GPU: orthographic projections of the ENGINE's assembly export (format=list)
#   + the two yard models (design lists) + the settled sails from an engine OBJ export (work default wind) + the ropes
#   (straight, rigging_plan.json). Nearest cell wins; cells are shaded by depth; sails drawn semi-transparent on top.
#   Usage: python -X utf8 tools/render_rig.py <design> <obj> <out dir>
import sys, os, json, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw

design, objp, outd = (os.path.abspath(a) for a in sys.argv[1:4])
sys.path.insert(0, design)
from draft_masts import load
from draft_lines import font, palette_rgb
SENATE = os.environ.get('SENATE', 'senate')
RP = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
tmp = os.path.join(tempfile.gettempdir(), 'baghlah_render8.txt')
r = subprocess.run([SENATE, 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'work=claude-baghlah-01m-assembly', '--arg', 'format=list', '--arg', 'out=' + tmp],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
if r.returncode != 0:
    raise SystemExit(r.stdout[-800:] + r.stderr[-800:])
cells = load(tmp)
for y in json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8')):
    key = y['mast']
    off = [int(round(y['at'][i] - y['pivot'][i])) for i in range(3)]
    for (a, b, c), col in load(os.path.join(design, 'masks', 'yards', 'lateen-%s.vox.txt' % key)).items():
        cells[(a + off[0], b + off[1], c + off[2])] = col
for f in ('stern_carving', 'stem_head'):
    cells.update(load(os.path.join(design, 'masks', 'deco', f + '.vox.txt')))
V, tri, cur = [], {}, None
for line in open(objp, encoding='utf-8'):
    if line.startswith('o '):
        cur = line.split('#', 1)[1].strip() if line.startswith('o sail_') else None
        if cur:
            tri[cur] = []
    elif line.startswith('v '):
        x, y, z = map(float, line.split()[1:4])
        V.append((x, z, y))
    elif line.startswith('f ') and cur:
        f = [int(t.split('/')[0]) - 1 for t in line.split()[1:]]
        for i in range(1, len(f) - 1):
            tri[cur].append((f[0], f[i], f[i + 1]))
V = np.array(V)
sail_col = {n: ((178, 18, 30) if n in ('ensign', 'pennant') else (242, 234, 216)) for n in tri}


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def view(name, ax_u, ax_v, ax_d, flip_u, rng_u, rng_v, depth_near_high, title):
    sc = 2
    W, H = (rng_u[1] - rng_u[0]) * sc + 40, (rng_v[1] - rng_v[0]) * sc + 70
    img = Image.new('RGB', (W, H), (236, 240, 244))
    best = {}
    for k, c in cells.items():
        u, v, d = k[ax_u], k[ax_v], k[ax_d]
        dd = d if depth_near_high else -d
        if (u, v) not in best or dd > best[(u, v)][0]:
            best[(u, v)] = (dd, c)
    dmin = min(b[0] for b in best.values())
    dmax = max(b[0] for b in best.values())
    px = img.load()
    U = lambda u: 20 + ((rng_u[1] - u) if flip_u else (u - rng_u[0])) * sc
    Vv = lambda v: 50 + (rng_v[1] - v) * sc
    for (u, v), (dd, c) in best.items():
        if not (rng_u[0] <= u < rng_u[1] and rng_v[0] <= v < rng_v[1]):
            continue
        s = 0.65 + 0.35 * (dd - dmin) / max(1, dmax - dmin)
        rgb = tuple(int(ch * s) for ch in palette_rgb(c))
        x0, y0 = U(u) if not flip_u else U(u + 1), Vv(v + 1)
        for i in range(sc):
            for j in range(sc):
                px[x0 + i, y0 + j] = rgb
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for n, ts in tri.items():
        for a, b, c in ts:
            pts = [(U(V[i][ax_u]), Vv(V[i][ax_v])) for i in (a, b, c)]
            d.polygon(pts, fill=sail_col[n] + (110,))
    img = Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')
    d = ImageDraw.Draw(img)
    for rp in RP['ropes']:
        a, b = RP['points'].get(rp['from']), RP['points'].get(rp['to'])
        if a and b:
            d.line([U(a[ax_u]), Vv(a[ax_v]), U(b[ax_u]), Vv(b[ax_v])], fill=hexrgb(rp['color']), width=1)
    d.text((20, 14), title, fill=(20, 20, 20), font=font(16))
    img.save(os.path.join(outd, name), optimize=False)
    print('✓', name, img.size)


os.makedirs(outd, exist_ok=True)
view('stage8_side_port.png', 0, 2, 1, False, (0, 420), (30, 330), False,
     'Star step 8: from port (sails settled at the default wind 4.5,-1.5,0 m/s; ropes straight)')
view('stage8_top.png', 0, 1, 2, False, (0, 420), (0, 160), True, 'Star step 8: from above (y up = starboard)')
view('stage8_stern.png', 1, 2, 0, False, (0, 160), (30, 330), False, 'Star step 8: from astern (port on the left)')
