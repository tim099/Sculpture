# Step 10 ledger (TASK-0019): the magazine, skids, hearth and the step-10 models as the ENGINE has them, against
#   gear_placement.json / masks/gear (structure from tools/check_guns.py).
#   1. the three new works replayed from their events vs their design lists (missing / extra / colour);
#   2. anchors (anchors.json): magazine blast / door, hearth smoke; the source works' hinge-a / hinge-b still there;
#   3. assembly links 彈藥庫 (meta kind=magazine, pos, powder_lb, hoist) and 小艇架 (at 0,0,0, on);
#   4. models.json of deck-main, deck-poop and the magazine: every step-10 model present with work, at, pivot, rotate,
#      scale, meta equal to the placement; nothing else new on those works (step-9 guns and fork twins are known);
#   5. the CLI's own reading (work sub=models): every model ✓ ok, its printed box equal to the box from that model's own
#      source cells with the draft_gear transform;
#   6. the sails as the engine settles them (export obj) against the deck models, measured on the triangle surfaces.
#   The whole-ship export: tools/check_rigging.py --extra=gunfittings:gunfittings/gunfittings,magazine:gear/magazine,boat-skids:gear/skids
#   Usage: python -X utf8 tools/check_gear.py <design> [--obj=<path>] [--probe=dx=<model>:<cells>] [--write]
#     probe dx: pretend one model sits n cells off in x (the box comparison must name it)
import sys, os, json, re, subprocess, tempfile, math, glob
import numpy as np
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
opt = dict(a[2:].split('=', 1) for a in sys.argv[2:] if a.startswith('--') and '=' in a)
probe = dict([opt['probe'].split('=', 1)]) if 'probe' in opt else {}
write = '--write' in sys.argv and not probe
SENATE = os.environ.get('SENATE', 'senate')
WORKS = os.path.dirname(os.path.dirname(design))
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
import draft_gear as DGR
from draft_masts import load


def replay(work_dir):
    """Same replay as tools/check_rigging.py (that file runs on import): stampvox placed_colored, box, carves, workedit."""
    cells, n = {}, 0
    for p in sorted(glob.glob(os.path.join(work_dir, 'events', '*', '*.json'))):
        e = json.load(open(p, encoding='utf-8'))
        n += 1
        if 'placed_colored' in e:
            for x, y, z, c in e['placed_colored']:
                cells[(x, y, z)] = c
        elif e.get('op') == 'box':
            for x, y, z in e.get('placed_voxels', []):
                cells[(x, y, z)] = e['color']
        if 'carved_voxels' in e:
            for v in e['carved_voxels']:
                cells.pop(tuple(v[:3]), None)
        if e.get('op') == 'workedit':
            for a in e['edit'].get('after', []):
                k = (a['x'], a['y'], a['z'])
                if a['color']:
                    cells[k] = a['color']
                else:
                    cells.pop(k, None)
    return cells, n


plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
GB = plan['gear_build']
PL = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))
ASM = GB['assembly']
HOST = dict(GB['deck_works'], magazine=GB['magazine']['work'])
R = {'works': {}, 'problems': []}


def cli(args):
    p = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        raise SystemExit('✗ exit %d %s\n%s' % (p.returncode, args, (p.stdout + p.stderr)[-1500:]))
    return p.stdout + p.stderr


def items(path, key):
    d = json.load(open(path, encoding='utf-8'))
    return d if isinstance(d, list) else d.get(key, [])


# 1. replay
for w, fn in ((GB['magazine']['work'], 'magazine'), (GB['skids']['work'], 'skids'), (GB['hearth']['work'], 'hearth')):
    have, n = replay(os.path.join(WORKS, w))
    want = load(os.path.join(design, 'masks', 'gear', fn + '.vox.txt'))
    c = {'have': len(have), 'want': len(want), 'missing': len(set(want) - set(have)), 'extra': len(set(have) - set(want)),
         'colour_diff': sum(1 for k in set(want) & set(have) if want[k] != have[k]), 'events': n}
    R['works'][fn] = c
    if c['missing'] or c['extra'] or c['colour_diff']:
        R['problems'].append(['ledger', fn, c])

# 2. anchors
R['anchors'] = {}
for w, want in ((GB['magazine']['work'], PL['magazine']['anchors']), (GB['hearth']['work'], PL['hearth']['anchors']),
                ('meadow-monitor-01m-hatch', None), ('gura-pinas-01m-door', None)):
    have = {a['name']: a['at'] for a in items(os.path.join(WORKS, w, 'anchors.json'), 'anchors')}
    if want is None:
        ok = 'hinge-a' in have and 'hinge-b' in have
        R['anchors'][w] = {'hinges': [have.get('hinge-a'), have.get('hinge-b')]}
        if not ok:
            R['problems'].append(['hinges missing', w])
        continue
    diff = [k for k in want if list(have.get(k) or []) != list(want[k])]
    R['anchors'][w] = {'have': have, 'diff': diff}
    if diff:
        R['problems'].append(['anchors', w, diff])

# 3. links
lk = {l['name']: l for l in items(os.path.join(WORKS, ASM, 'links.json'), 'links')}
R['links'] = {}
for name, w, meta in ((PL['magazine']['link'], PL['magazine']['work'], PL['magazine']['meta']), (PL['skids']['link'], PL['skids']['work'], None)):
    l = lk.get(name)
    if l is None:
        R['links'][name] = None
        R['problems'].append(['link missing', name])
        continue
    md = {k: v for k, v in (l.get('meta') or {}).items() if k != 'id'}
    d = {'work': l.get('work') or l.get('source_work'), 'at': l['at'], 'enabled': l.get('enabled', True), 'meta': md}
    R['links'][name] = d
    if d['work'] != w or list(d['at']) != [0, 0, 0] or not d['enabled'] or (meta and md != meta) or (not meta and md):
        R['problems'].append(['link', name, d])

# 4 + 5. models
known = set()
for r in json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']:
    known |= {r['name'], r['name'] + '座'}
if os.path.exists(os.path.join(design, 'helm_placement.json')):          # step 11 anchors on deck-main (read back by tools/check_helm.py)
    known |= {a['name'] for a in json.load(open(os.path.join(design, 'helm_placement.json'), encoding='utf-8'))['anchors']}
want = {r['name']: r for r in PL['models']}
src_cache = {}


def src(w):
    if w not in src_cache:
        p = os.path.join(design, 'masks', 'gear', 'hearth.vox.txt') if w == GB['hearth']['work'] else os.path.join(design, 'masks', 'gear_src', w + '.vox.txt')
        src_cache[w] = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :3].astype(float)
    return src_cache[w]


R['models'] = {}
seen = set()
for hk, w in HOST.items():
    path = os.path.join(WORKS, w, 'models.json')
    have = {m['name']: m for m in items(path, 'models')} if os.path.exists(path) else {}
    out = cli(['op=work', 'sub=models', 'work=' + w])
    printed = {}
    for line in out.splitlines():
        m = re.match(r'- (\S) `([^`]+)`［(\w+)］.*外框 \(([-\d.,]+)\)–\(([-\d.,]+)\)', line)
        if m:
            printed[m.group(2)] = (m.group(1), m.group(3), [float(v) for v in m.group(4).split(',')], [float(v) for v in m.group(5).split(',')])
    for nm, m in have.items():
        if nm in known:
            continue
        seen.add(nm)
        if nm not in want:
            R['problems'].append(['extra model', w, nm])
            continue
        r = want[nm]
        diff = []
        if HOST[r['host']] != w:
            diff.append('host')
        if m['work'] != r['work']:
            diff.append('work')
        for k, v in (('at', r['at']), ('pivot', r['pivot']), ('rotate', [0, 0, r['rotate']]), ('scale', r['scale'])):
            if any(abs(a - b) > 1e-4 for a, b in zip(m[k], v)):
                diff.append('%s %s != %s' % (k, m[k], v))
        if (m.get('mirror') or '') != '':
            diff.append('mirror')
        if not m.get('enabled', True):
            diff.append('disabled')
        md = {k: v for k, v in (m.get('meta') or {}).items() if k != 'id'}
        if md != r['meta']:
            diff.append('meta %s != %s' % (md, r['meta']))
        g = DGR.Model(src(r['work']), r['pivot'], r['scale'], r['rotate'])
        at = np.array(r['at'], float)
        if probe.get('dx') and probe['dx'].rsplit(':', 1)[0] == nm:
            at[0] += float(probe['dx'].rsplit(':', 1)[1])
        blo, bhi = g.bbox(at)
        pr = printed.get(nm)
        box_err = None
        if not pr:
            diff.append('not printed by sub=models')
        else:
            if pr[0] != '✓' or pr[1] != 'ok':
                diff.append('cli %s %s' % (pr[0], pr[1]))
            box_err = round(float(max(np.abs(np.array(pr[2]) - blo).max(), np.abs(np.array(pr[3]) - bhi).max())), 3)
            if box_err > 0.051:                                                 # the CLI prints one decimal
                diff.append('box off by %s' % box_err)
        R['models'][nm] = {'host': w, 'diff': diff, 'box_err': box_err}
        if diff:
            R['problems'].append([nm] + diff)
R['missing'] = sorted(set(want) - seen)
R['problems'] += [['missing', nm] for nm in R['missing']]
R['count'] = {'want': len(want), 'have': len(seen), 'barrels': sum(1 for n in seen if n.startswith('桶-'))}
R['box_err_max'] = max((v['box_err'] for v in R['models'].values() if v['box_err'] is not None), default=None)

# 6. settled cloth vs the deck models (cube centres; half-diagonal subtracted)
obj = opt.get('obj')
if not obj and not probe:
    obj = os.path.join(tempfile.mkdtemp(), 'a.obj')
    cli(['op=export', 'format=obj', 'work=' + ASM, 'out=' + obj])
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
        cloth[nm] = np.array([[V[a], V[b], V[c]] for a, b, c in tk])
    res = {}
    for nm, r in want.items():
        if r['host'] == 'magazine':
            continue
        g = DGR.Model(src(r['work']), r['pivot'], r['scale'], r['rotate'])
        C = g.world(g.centers, r['at'])
        kd = cKDTree(C)
        best = None
        for sn, T3 in cloth.items():
            P = dense(T3, 0.25)
            d, _ = kd.query(P)
            dmin = float(d.min()) - float(np.linalg.norm(g.scale)) / 2
            if best is None or dmin < best[0]:
                best = [round(dmin, 2), sn]
        res[nm] = best
    R['cloth_clearance'] = res
    R['cloth_clearance_min'] = min(res.values(), key=lambda v: v[0]) if res else None
    R['cloth_sails'] = sorted(cloth)
    if R['cloth_clearance_min'] and R['cloth_clearance_min'][0] <= 0:
        R['problems'].append(['cloth', R['cloth_clearance_min']])
R['problems_total'] = len(R['problems'])
print(json.dumps(R, ensure_ascii=False, indent=1))
if write:
    with open(os.path.join(design, 'verify_step10.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
