# Step 9 ledger (TASK-0019): the gun models as the ENGINE has them, against guns_placement.json.
#   1. models.json of both deck works: every gun / fork twin present, source work, at, pivot, rotate, scale, mirror, meta
#      (incl. the station arc) equal to the placement; no extra models.
#   2. the CLI's own reading (work sub=models): every model ok / drawn, and its printed box equal to the box computed from
#      that model's own source cells with the draft_guns transform (a wrong transform shows up here).
#   3. the cloth: sails as the engine settles them (export obj, default wind) against every gun -- swivels over their whole
#      arc -- measured on the triangle surfaces (same densifying as check_sails_sim.py).
#   4. gun fittings: anchors (anchors.json) vs gunfittings_points.json, the link 砲具 and its meta, the gun tackle in the
#      assembly's ropes.json vs gun_ropes.json, and the tackle as the engine draws it (obj rope tubes, sag included):
#      vertices inside a solid (design solids + fittings + other guns' cells; the rope's own gun and ring excepted).
#      The cell ledger of the fittings work and the whole-ship export: tools/check_rigging.py --extra=gunfittings:…
#   Usage: python -X utf8 tools/check_guns.py <design> [--obj=<path>] [--probe=dx=<gun>:<cells>] [--write]
#     probe dx: pretend one model sits n cells off in x (the box comparison must name it)
import sys, os, json, re, subprocess, tempfile, math
import numpy as np
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
opt = dict(a[2:].split('=', 1) for a in sys.argv[2:] if a.startswith('--') and '=' in a)
probe = dict([opt['probe'].split('=', 1)]) if 'probe' in opt else {}
write = '--write' in sys.argv and not probe
SENATE = os.environ.get('SENATE', 'senate')
WORKS = os.path.dirname(os.path.dirname(design))
ASM = 'claude-baghlah-01m-assembly'
sys.path.insert(0, design)
import draft_guns as DG

plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
GB = plan['guns_build']
PL = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']
guns = {k: DG.Gun(k, t, design, GB['search']['inset']) for k, t in GB['types'].items()}
R = {'models': {}, 'problems': []}


def cli(args):
    p = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        raise SystemExit('✗ exit %d %s\n%s' % (p.returncode, args, (p.stdout + p.stderr)[-1500:]))
    return p.stdout + p.stderr


# expected models: name -> (deck work, source work, cells for the box, placement row, meta)
want = {}
for r in PL:
    t = GB['types'][r['type']]
    meta = dict(t['meta'])
    meta.update({'deck': r['deck'], 'side': r['side'], 'port': r['port'] if isinstance(r['port'], int) else 'swivel'})
    if r['swivel']:
        meta['arc'] = r['arc']
    g = guns[r['type']]
    want[r['name']] = (GB['deck_works'][r['deck']], t['work'], g.barrel, r, meta)
    if t.get('mount_work'):
        want[r['name'] + '座'] = (GB['deck_works'][r['deck']], t['mount_work'], g.mount, r, {'kind': 'gunmount'})

seen = set()
for dk, w in GB['deck_works'].items():
    have = {m['name']: m for m in json.load(open(os.path.join(WORKS, w, 'models.json'), encoding='utf-8'))['models']}
    out = cli(['op=work', 'sub=models', 'work=' + w])
    printed = {}
    for line in out.splitlines():
        m = re.match(r'- (\S) `([^`]+)`［(\w+)］.*外框 \(([-\d.,]+)\)–\(([-\d.,]+)\)', line)
        if m:
            printed[m.group(2)] = (m.group(1), m.group(3), [float(v) for v in m.group(4).split(',')], [float(v) for v in m.group(5).split(',')])
    for nm, m in have.items():
        seen.add(nm)
        if nm not in want:
            R['problems'].append(['extra model', w, nm])
            continue
        hw, src, cells, r, meta = want[nm]
        t = GB['types'][r['type']]
        s = float(t['scale'])
        diff = []
        if hw != w:
            diff.append('host')
        if m['work'] != src:
            diff.append('work')
        if any(abs(a - b) > 1e-6 for a, b in zip(m['at'], r['at'])):
            diff.append('at')
        if any(abs(a - b) > 1e-6 for a, b in zip(m['pivot'], t['pivot'])):
            diff.append('pivot')
        if any(abs(a - b) > 1e-6 for a, b in zip(m['rotate'], [0, 0, r['phi']])):
            diff.append('rotate')
        if any(abs(a - s) > 1e-6 for a in m['scale']):
            diff.append('scale')
        if (m['mirror'] or '') != ('y' if r['side'] == 'P' else ''):
            diff.append('mirror')
        if not m.get('enabled', True):
            diff.append('disabled')
        md = {k: v for k, v in (m.get('meta') or {}).items() if k != 'id'}
        if md != meta:
            diff.append('meta %s != %s' % (md, meta))
        # box from this model's own cells
        g = guns[r['type']]
        lo_c, hi_c = cells.min(0), cells.max(0) + 1
        corners = np.array([[(lo_c[0], hi_c[0])[k & 1], (lo_c[1], hi_c[1])[(k >> 1) & 1], (lo_c[2], hi_c[2])[(k >> 2) & 1]] for k in range(8)], float)
        at = np.array(r['at'], float)
        if probe.get('dx') and probe['dx'].rsplit(':', 1)[0] == nm:
            at[0] += float(probe['dx'].rsplit(':', 1)[1])
        Wc = g.world(corners, at, r['phi'], r['side'] == 'P')
        blo, bhi = Wc.min(0), Wc.max(0)
        pr = printed.get(nm)
        if not pr:
            diff.append('not printed by sub=models')
            box_err = None
        else:
            if pr[0] != '✓' or pr[1] != 'ok':
                diff.append('cli %s %s' % (pr[0], pr[1]))
            box_err = round(float(max(np.abs(np.array(pr[2]) - blo).max(), np.abs(np.array(pr[3]) - bhi).max())), 3)
            if box_err > 0.051:                                                 # the CLI prints one decimal
                diff.append('box off by %s' % box_err)
        R['models'][nm] = {'host': w, 'diff': diff, 'box_err': box_err}
        if diff:
            R['problems'].append([nm] + diff)
missing = sorted(set(want) - seen)
R['missing'] = missing
R['problems'] += [['missing', nm] for nm in missing]
R['count'] = {'want': len(want), 'have': len(seen), 'guns': sum(1 for n in want if not n.endswith('座')), 'fork_twins': sum(1 for n in want if n.endswith('座'))}
R['box_err_max'] = max((v['box_err'] for v in R['models'].values() if v['box_err'] is not None), default=None)

# ── the settled cloth against the guns (swivels over the arc) ──
obj = opt.get('obj')
if not obj and not probe:
    tmp = tempfile.mkdtemp()
    obj = os.path.join(tmp, 'a.obj')
    cli(['op=export', 'format=obj', 'work=' + ASM, 'out=' + obj])                # ropes on: the gun tackle tubes are read too
if obj:
    V, cur, faces = [], None, {}
    for line in open(obj, encoding='utf-8'):
        if line.startswith('o '):
            cur = line.split('#', 1)[1].strip() if line.startswith('o sail_') else None
            if cur:
                faces[cur] = []
        elif line.startswith('v '):
            x, y, z = map(float, line.split()[1:4])
            V.append((x, z, y))
        elif line.startswith('f ') and cur:
            faces[cur].append([int(t.split('/')[0]) - 1 for t in line.split()[1:]])
    V = np.array(V)

    def dense(T, step):
        out = []
        edge = np.linalg.norm(T[:, [1, 2, 0]] - T, axis=2).max(1)
        nn = np.maximum(2, np.ceil(edge / step)).astype(int)
        for n in sorted(set(nn)):
            sel = T[nn == n]
            Wb = np.array([(i / n, j / n, 1 - (i + j) / n) for i in range(n + 1) for j in range(n + 1 - i)])
            out.append(np.einsum('kw,twd->tkd', Wb, sel).reshape(-1, 3))
        return np.concatenate(out)

    cloth = {}
    for nm, F in faces.items():
        tk = sorted({tuple(sorted((f[0], f[i], f[i + 1]))) for f in F if len(f) >= 3 for i in range(1, len(f) - 1)})
        T3 = np.array([[V[a], V[b], V[c]] for a, b, c in tk])
        cloth[nm] = T3
    # gun cubes: distance from a surface point to the nearest gun cell cube (scaled cubes ⇒ test against the samples'
    # cell centres with half-size = scale / 2)
    res = {}
    for r in PL:
        g = guns[r['type']]
        mir = r['side'] == 'P'
        if r['swivel']:
            a0, a1 = [float(a) for a in r['arc'].split(',')]
            angs = np.arange(a0, a1 + 1e-9, GB['sweep_step_deg'])
        else:
            angs = [r['phi']]
        best = None
        for a in angs:
            C = g.world(g.centers, r['at'], float(a), mir)
            lo, hi = C.min(0) - 40, C.max(0) + 40                             # only triangles within 4 m are sampled
            kd = cKDTree(C)
            for nm, T3 in cloth.items():
                cen = T3.mean(1)
                near = np.all((cen > lo) & (cen < hi), 1)
                if not near.any():
                    continue
                P = dense(T3[near], 0.25)
                d, _ = kd.query(P)
                dmin = float(d.min()) - g.scale * math.sqrt(3) / 2              # centre distance minus the cube's half-diagonal
                if best is None or dmin < best[0]:
                    best = [round(dmin, 2), nm, int(a)]
        res[r['name']] = best
    R['cloth_clearance'] = {k: v for k, v in res.items() if v}
    R['cloth_clearance_min'] = min(R['cloth_clearance'].values(), key=lambda v: v[0]) if R['cloth_clearance'] else None
    R['cloth_sails'] = sorted(cloth)
    if R['cloth_clearance_min'] and R['cloth_clearance_min'][0] < 0:
        R['problems'].append(['cloth through a gun', R['cloth_clearance_min']])
# ── gun fittings read back ──
FB = plan['gunfittings_build']
PTS = json.load(open(os.path.join(design, 'gunfittings_points.json'), encoding='utf-8'))['anchors']
GR = json.load(open(os.path.join(design, 'gun_ropes.json'), encoding='utf-8'))['ropes']
an = {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, FB['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
R['fittings_anchors'] = {'want': len(PTS), 'have': len(an), 'diff': sorted(n for n in PTS if list(an.get(n, [])) != list(PTS[n])),
                         'extra': sorted(n for n in an if n not in PTS)}
lk = {l['name']: l for l in json.load(open(os.path.join(WORKS, ASM, 'links.json'), encoding='utf-8'))['links']}
L = lk.get(FB['link'])
R['fittings_link'] = None if L is None else {'work': L.get('work'), 'at': L['at'], 'meta': {k: v for k, v in (L.get('meta') or {}).items() if k != 'id'}}
if L is None or L.get('work') != FB['work'] or list(L['at']) != [0, 0, 0] or R['fittings_link']['meta'] != FB['link_meta']:
    R['problems'].append(['fittings link', R['fittings_link']])
ropes = {r['name']: r for r in json.load(open(os.path.join(WORKS, ASM, 'ropes.json'), encoding='utf-8'))['ropes']}
rd = []
for r in GR:
    g_ = ropes.get(r['name'])
    if g_ is None:
        rd.append([r['name'], 'missing'])
        continue
    for f in ('from', 'to', 'color', 'group'):
        if g_.get(f) != r[f]:
            rd.append([r['name'], f])
    for f in ('slack', 'thickness'):
        if abs(float(g_.get(f, -1)) - float(r[f])) > 1e-9:
            rd.append([r['name'], f])
R['gun_ropes'] = {'plan': len(GR), 'diff': rd}
R['problems'] += [['fittings anchor', n] for n in R['fittings_anchors']['diff'] + R['fittings_anchors']['extra']] + [['gun rope'] + d for d in rd]
if obj:
    from draft_masts import ship_cells, load
    M = os.path.join(design, 'masks')
    solid = set(ship_cells(design, plan))
    for f in ('main', 'mizzen', 'jibboom', 'cable_beam'):
        solid |= set(load(os.path.join(M, 'masts', f + '.vox.txt')))
    for f in ('rings', 'stern_spars', 'halyard_bitt'):
        solid |= set(load(os.path.join(M, 'rigging', f + '.vox.txt')))
    solid |= set(load(os.path.join(M, 'gunfittings', 'gunfittings.vox.txt')))
    gun_cells = {}
    for r in PL:
        g = guns[r['type']]
        gun_cells[r['name']] = set(map(tuple, np.floor(g.world(g.samples, r['at'], r['phi'], r['side'] == 'P')).astype(int).tolist()))
    allgun = {}
    for n_, cs in gun_cells.items():
        for c in cs:
            allgun[c] = n_
    tubes, cur = {}, None
    vi = 0
    for line in open(obj, encoding='utf-8'):
        if line.startswith('o '):
            nm = line.split('#', 1)[1].strip() if '#' in line else ''
            cur = nm if line.startswith('o rope_') and nm in {r['name'] for r in GR} else None
            if cur:
                tubes[cur] = []
        elif line.startswith('v '):
            if cur:
                x, y, z = map(float, line.split()[1:4])
                tubes[cur].append((x, z, y))
    inside, lowest = {}, None
    for nm, P in tubes.items():
        gun = nm.split('.')[0]
        ring = tuple(PTS[next(r['to'] for r in GR if r['name'] == nm).split('/', 1)[1]])
        near_ring = {(ring[0] + a, ring[1] + b, ring[2] + c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)}
        n_in = 0
        for q in P:
            c = (int(math.floor(q[0])), int(math.floor(q[1])), int(math.floor(q[2])))
            if c in near_ring or c in gun_cells[gun]:
                continue
            if c in solid or (c in allgun and allgun[c] != gun):
                n_in += 1
        if n_in:
            inside[nm] = n_in
        zmin = min(q[2] for q in P)
        if lowest is None or zmin < lowest[0]:
            lowest = [round(zmin, 2), nm]
    R['gun_tackle_tubes'] = {'ropes': len(tubes), 'vertices_inside_solid': inside, 'lowest_vertex_z': lowest}
    if len(tubes) != len(GR):
        R['problems'].append(['gun tackle tubes in obj', len(tubes), len(GR)])
    R['problems'] += [['tackle inside solid', k, v] for k, v in inside.items()]
R['problems_total'] = len(R['problems'])
print(json.dumps({k: v for k, v in R.items() if k != 'models'}, ensure_ascii=False))
if write:
    with open(os.path.join(design, 'verify_step9.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
