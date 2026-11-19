# Step 8 (TASK-0019): the sails AFTER the cloth settles (engine export obj at the work's default wind / seconds), measured
#   against the voxels (design lists of every part + the two yard models), the ropes (straight, from rigging_plan.json) and
#   each other. The flat-polygon readings in draft_rigging.py cannot see the belly; this one can.
#   Usage: python -X utf8 tools/check_sails_sim.py <design> [--obj=<path>] [--wind=x,y,z] [--write]
#     --obj    reuse an export (default: export the assembly now, ropes=0)
#     --wind   export with this wind instead of the work default (a reverse control: the belly must move)
#   OBJ axes: the engine writes (x, z, y) ⇒ sculpt = (vx, vz, vy).
import sys, os, json, math, subprocess, tempfile
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
opt = dict(a[2:].split('=', 1) for a in sys.argv[2:] if a.startswith('--') and '=' in a)
write = '--write' in sys.argv
SENATE = os.environ.get('SENATE', 'senate')
ASM = 'claude-baghlah-01m-assembly'
sys.path.insert(0, design)
from draft_masts import ship_cells, load
from draft_rigging import seg_dist

plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
RP = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
M = os.path.join(design, 'masks')

obj = opt.get('obj')
tmp = None
if not obj:
    tmp = tempfile.mkdtemp()
    obj = os.path.join(tmp, 'a.obj')
    args = ['op=export', 'format=obj', 'work=' + ASM, 'out=' + obj, 'ropes=0']
    if 'wind' in opt:
        args.append('wind=' + opt['wind'])
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise SystemExit('export failed: ' + (r.stdout + r.stderr)[-800:])

V, cur, sails = [], None, {}
for line in open(obj, encoding='utf-8'):
    if line.startswith('o '):
        cur = line.split('#', 1)[1].strip() if line.startswith('o sail_') else None
        if cur:
            sails[cur] = {'faces': []}
    elif line.startswith('v '):
        x, y, z = map(float, line.split()[1:4])
        V.append((x, z, y))
    elif line.startswith('f ') and cur:
        sails[cur]['faces'].append([int(t.split('/')[0]) - 1 for t in line.split()[1:]])
V = np.array(V)

# solids, labelled by part
own = {}
def add(cells, label):
    for k in cells:
        own[k] = label
add(ship_cells(design, plan), 'ship')
for k, f in (('mast-main', 'main'), ('mast-mizzen', 'mizzen'), ('jibboom', 'jibboom'), ('cable-beam', 'cable_beam')):
    add(load(os.path.join(M, 'masts', f + '.vox.txt')), k)
YP = {y['mast']: y for y in json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))}
for key in ('main', 'mizzen'):
    off = [int(round(YP[key]['at'][i] - YP[key]['pivot'][i])) for i in range(3)]
    add({(x + off[0], y + off[1], z + off[2]) for (x, y, z) in load(os.path.join(M, 'yards', 'lateen-%s.vox.txt' % key))}, 'yard-' + key)
for f in ('rings', 'stern_spars', 'halyard_bitt'):
    add(load(os.path.join(M, 'rigging', f + '.vox.txt')), f)
solid = np.zeros((480, 160, 400), bool)
for k in own:
    solid[k] = True
edt = ndimage.distance_transform_edt(~solid)

ropes = [(r['name'], np.array(RP['points'][r['from']]), np.array(RP['points'][r['to']]), r['thickness'] / 2, r['from'], r['to']) for r in RP['ropes']
         if r['from'] in RP['points'] and r['to'] in RP['points']]


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
    return 0 <= u and 0 <= v and u + v <= 1 and 0 < w < 1



R = {'obj': os.path.basename(obj), 'wind': opt.get('wind', 'work default'), 'sails': {}}
# v2 (verifier step 8, 4c): distances are taken on the triangle SURFACES, not only on the vertices (vertex-only main↔foc was
#   5.74, the surface 4.95). Densifying whole sails is too slow, so every reading first picks the triangles that can matter
#   (coarse distance + triangle size) and samples only those on a barycentric grid.
TRI, COARSE, KD, H = {}, {}, {}, {}


def dense(T, step):
    if len(T) == 0:
        return np.zeros((0, 3))
    out = []
    edge = np.linalg.norm(T[:, [1, 2, 0]] - T, axis=2).max(1)
    for n in sorted(set(np.maximum(2, np.ceil(edge / step)).astype(int))):
        sel = T[np.maximum(2, np.ceil(edge / step)).astype(int) == n]
        W = np.array([(i / n, j / n, 1 - (i + j) / n) for i in range(n + 1) for j in range(n + 1 - i)])
        out.append(np.einsum('kw,twd->tkd', W, sel).reshape(-1, 3))
    return np.concatenate(out)


def cubes_gap(P, C):
    if len(P) == 0:
        return None
    t_ = cKDTree(C + 0.5)
    _, i = t_.query(P, k=min(8, len(C)))
    best = 9e9
    for kk in range(i.shape[1]):
        c = C[i[:, kk]]
        g = np.maximum(np.maximum(c - P, P - (c + 1.0)), 0.0)
        best = min(best, float(np.sqrt((g * g).sum(1)).min()))
    return round(best, 2)


import time
T0 = time.time()
for nm, s in sails.items():
    print('· %s %.1fs' % (nm, time.time() - T0), file=sys.stderr)
    F = [f for f in s['faces'] if len(f) >= 3]
    tk = sorted({tuple(sorted((f[0], f[i], f[i + 1]))) for f in F for i in range(1, len(f) - 1)})   # both faces are written: once each
    T3 = np.array([[V[a], V[b], V[c]] for a, b, c in tk])
    TRI[nm] = T3
    H[nm] = np.linalg.norm(T3[:, [1, 2, 0]] - T3, axis=2).max(1)
    COARSE[nm] = np.concatenate([T3.reshape(-1, 3), T3.mean(1)])
    KD[nm] = cKDTree(COARSE[nm])
    # cells entered: dense samples (0.3) of the triangles that come within reach of a solid
    cent = T3.mean(1)
    ci = np.clip(np.floor(cent).astype(int), 0, [479, 159, 399])
    near = edt[tuple(ci.T)] <= H[nm] + 2
    P_ = np.concatenate([COARSE[nm], dense(T3[near], 0.3)])
    inside = {}
    for k in map(tuple, np.unique(np.clip(np.floor(P_).astype(int), 0, [479, 159, 399]), axis=0)):
        if solid[k]:
            inside[own[k]] = inside.get(own[k], 0) + 1          # distinct cells entered
    through, close = [], []
    lo, hi = T3.reshape(-1, 3).min(0) - 2, T3.reshape(-1, 3).max(0) + 2
    for rn, a, b, rad, fa, fb in ropes:
        if fa.startswith('sail:%s/' % nm) or fb.startswith('sail:%s/' % nm) or (nm == 'foc' and rn == 'foc-stay'):
            continue
        if (np.maximum(a, b) < lo).any() or (np.minimum(a, b) > hi).any():
            continue
        if any(seg_tri(a, b, t) for t in T3):
            through.append(rn)
            continue
        L_ = float(np.linalg.norm(b - a))
        S_ = a + np.outer(np.linspace(0, 1, max(2, int(L_ / 0.25) + 1)), b - a)
        d0 = float(KD[nm].query(S_)[0].min())
        if d0 < 2.0 + H[nm].max():
            sel = T3[np.min(np.linalg.norm(cent[:, None, :] - S_[None, ::8, :], axis=2), 1) <= d0 + H[nm] + 1]
            dd = float(cKDTree(dense(sel, 0.15)).query(S_)[0].min()) - rad
            if dd < 2.0:
                close.append((round(dd, 2), rn))
    R['sails'][nm] = {'triangles': len(T3), 'cells_entered': inside, 'ropes_through_cloth': sorted(through), 'ropes_within_2_cells': sorted(close)[:6],
                      'bbox': [[round(float(v), 1) for v in lo + 2], [round(float(v), 1) for v in hi - 2]]}
# sail vs sail on the surfaces
print('· pairs %.1fs' % (time.time() - T0), file=sys.stderr)
names = sorted(TRI)
ss = []
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        A_, B_ = names[i], names[j]
        d0 = float(KD[B_].query(COARSE[A_])[0].min())
        if d0 > 15:                                  # far apart: the vertex distance is good to within a triangle size
            ss.append((round(d0, 2), A_, B_, 'vertices (> 15, not densified)'))
            continue
        ca, cb = TRI[A_].mean(1), TRI[B_].mean(1)
        sa = TRI[A_][KD[B_].query(ca)[0] - H[A_] <= d0 + H[B_].max() + 1]       # each triangle's own size, the other side's largest
        sb = TRI[B_][KD[A_].query(cb)[0] - H[B_] <= d0 + H[A_].max() + 1]
        print('· pair %s %s: %d × %d triangles' % (A_, B_, len(sa), len(sb)), file=sys.stderr)
        pa, pb = dense(sa, 0.2), dense(sb, 0.2)          # 0.2 apart ⇒ distance error < 0.15
        d, k = cKDTree(pb).query(pa)
        m = int(np.argmin(d))
        ss.append((round(float(d[m]), 2), A_, B_, [round(float(v), 1) for v in pa[m]], [round(float(v), 1) for v in pb[k[m]]]))
R['sail_sail_nearest_surface'] = sorted(ss, key=lambda t: t[0])[:6]
FIN = np.array(sorted(load(os.path.join(M, 'deco', 'stem_head.vox.txt'))), float)
fl, fh = FIN.min(0) - 12, FIN.max(0) + 13
R['cloth_to_stem_head_finial'] = {}
for n in ('foc', 'main-lateen'):
    c = TRI[n].mean(1)
    sel = TRI[n][np.all((c >= fl - H[n][:, None]) & (c <= fh + H[n][:, None]), axis=1)]
    R['cloth_to_stem_head_finial'][n] = cubes_gap(dense(sel, 0.1), FIN)
sw_ = plan['ports']['swivels']
hullc = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
R['cloth_above_swivel_stations_m'] = {}
for sx in sw_['x'] + [sw_['bow']['x']]:
    zt = max(z for (x, y, z) in hullc if x == sx)
    for n in ('main-lateen', 'mizzen-lateen', 'foc'):
        c = TRI[n].mean(1)
        P = dense(TRI[n][np.abs(c[:, 0] - (sx + 0.5)) <= 6 + H[n]], 0.3)
        m_ = (np.abs(P[:, 0] - (sx + 0.5)) <= 6) & ((P[:, 1] < 60) | (P[:, 1] > 100)) if len(P) else np.zeros(0, bool)
        if m_.any():
            R['cloth_above_swivel_stations_m']['%s@%d' % (n, sx)] = round(float((P[m_, 2].min() - (zt + 1)) * 0.1), 2)
R['problems'] = {nm: v for nm, v in R['sails'].items() if v['ropes_through_cloth']}
print(json.dumps(R, ensure_ascii=False))
if write:
    with open(os.path.join(design, 'verify_step8_sails.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
