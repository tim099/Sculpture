# Step 11 read-back (TASK-0019), structure from tools/check_gear.py: the rudder, tiller, collar, rollers and the two anchors
#   as the ENGINE has them, against helm_placement.json / masks/helm / masks/step11.
#   1. the four new works and the three carved works replayed from their events vs their design lists (carve lists taken off);
#   2. anchors: rudder stock-top, hull hawse-S / hawse-P;
#   3. assembly links 舵頭圈, 艏柱滾輪 (at 0,0,0, enabled);
#   4. models.json: assembly 舵 / 舵柄, deck-main 錨-S / 錨-P -- work, at, pivot, rotate, scale, mirror, meta equal the placement;
#   5. the CLI's own reading (work sub=models): ✓ ok, its printed box equal to the box from the model's source cells;
#      the stern carving model (its source lost 4 cells) still ✓ ok;
#   6. export format=parts: every kind=rudder / kind=tiller model has spin (Ship_Helm 9.8.1); kind=anchor has hawse;
#   7. the sails as the engine settles them (export obj) against the new parts (cell samples, triangle surfaces densified).
#   Usage: python -X utf8 tools/check_helm.py <design> [--obj=<path>] [--probe=dx=<model>:<cells>] [--write]
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
from draft_masts import load
from draft_helm import Grapnel
from draft_gear import corners

HULL = 'claude-baghlah-01m'
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
HB = plan['helm_build']
DECK = plan['gear_build']['deck_works']
PL = json.load(open(os.path.join(design, 'helm_placement.json'), encoding='utf-8'))
ASM = HB['assembly']
R = {'works': {}, 'problems': []}


def replay(work_dir):
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


def cli(args):
    p = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        raise SystemExit('✗ exit %d %s\n%s' % (p.returncode, args, (p.stdout + p.stderr)[-1500:]))
    return p.stdout + p.stderr


def items(path, key):
    d = json.load(open(path, encoding='utf-8'))
    return d if isinstance(d, list) else d.get(key, [])


M = os.path.join(design, 'masks')
# 1. replay
hull_want = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
hull_want.update(load(os.path.join(M, 'step6', 'hull_recolor.vox.txt')))
hull_want.update(load(os.path.join(M, 'step6', 'hull_add.vox.txt')))
checks = [(HB[k]['work'], load(os.path.join(M, 'helm', f + '.vox.txt'))) for k, f in (('rudder', 'rudder'), ('tiller', 'tiller'), ('fittings', 'fittings'), ('rollers', 'rollers'))]
cut = {w: set(load(os.path.join(M, rel + '.vox.txt'))) for w, rel in PL['carve'].items()}
checks.append((HULL, {k: v for k, v in hull_want.items() if k not in cut['hull']}))
checks.append((HULL + '-deck-poop', {k: v for k, v in load(os.path.join(M, 'decks', 'poop.vox.txt')).items() if k not in cut['deck-poop']}))
checks.append((HULL + '-stern-carving', {k: v for k, v in load(os.path.join(M, 'deco', 'stern_carving.vox.txt')).items() if k not in cut['stern-carving']}))
for w, want in checks:
    have, n = replay(os.path.join(WORKS, w))
    c = {'have': len(have), 'want': len(want), 'missing': len(set(want) - set(have)), 'extra': len(set(have) - set(want)),
         'colour_diff': sum(1 for k in set(want) & set(have) if want[k] != have[k]), 'events': n}
    R['works'][w] = c
    if c['missing'] or c['extra'] or c['colour_diff']:
        R['problems'].append(['ledger', w, c])
R['carved_still_there'] = {w: len(cut[k] & set(replay(os.path.join(WORKS, w))[0])) for k, w in (('hull', HULL), ('deck-poop', HULL + '-deck-poop'), ('stern-carving', HULL + '-stern-carving'))}
if any(R['carved_still_there'].values()):
    R['problems'].append(['carved cells still there', R['carved_still_there']])

# 2. anchors
R['anchors'] = {}
for w, want in ((PL['rudder']['work'], PL['rudder']['anchors']), (HULL, PL['hawse'])):
    have = {a['name']: a['at'] for a in items(os.path.join(WORKS, w, 'anchors.json'), 'anchors')}
    diff = [k for k in want if list(have.get(k) or []) != list(want[k])]
    R['anchors'][w] = {k: have.get(k) for k in want}
    if diff:
        R['problems'].append(['anchors', w, diff])

# 3. links
lk = {l['name']: l for l in items(os.path.join(WORKS, ASM, 'links.json'), 'links')}
R['links'] = {}
for l in PL['links']:
    g = lk.get(l['link'])
    d = None if g is None else {'work': g.get('work') or g.get('source_work'), 'at': g['at'], 'enabled': g.get('enabled', True), 'mirror': g.get('mirror') or ''}
    R['links'][l['link']] = d
    if d is None or d['work'] != l['work'] or list(d['at']) != [0, 0, 0] or not d['enabled'] or d['mirror']:
        R['problems'].append(['link', l['link'], d])

# 4 + 5. models
gsrc = np.loadtxt(os.path.join(M, 'helm_src', HB['anchors']['work'] + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :3].astype(float)
want = {}
for key, f in (('rudder', 'rudder'), ('tiller', 'tiller')):
    m = PL[key]
    cells = np.array(sorted(load(os.path.join(M, 'helm', f + '.vox.txt'))), float)
    want[m['model']] = dict(host=m['host'], work=m['work'], at=m['at'], pivot=m['pivot'], rotate=0, scale=[1, 1, 1], mirror='', meta=m['meta'],
                            g=Grapnel(cells, m['pivot'], 1.0, 0, False))
for a in PL['anchors']:
    want[a['name']] = dict(host=DECK[a['host']], work=a['work'], at=a['at'], pivot=a['pivot'], rotate=a['rotate'], scale=[a['scale']] * 3, mirror=a['mirror'], meta=a['meta'],
                       g=Grapnel(gsrc, a['pivot'], a['scale'], a['rotate'], a['mirror'] == 'y'))
R['models'] = {}
printed_all = {}
for w in sorted({v['host'] for v in want.values()}):
    have = {m['name']: m for m in items(os.path.join(WORKS, w, 'models.json'), 'models')}
    out = cli(['op=work', 'sub=models', 'work=' + w])
    printed = {}
    for line in out.splitlines():
        m = re.match(r'- (\S) `([^`]+)`［(\w+)］.*外框 \(([-\d.,]+)\)–\(([-\d.,]+)\)', line)
        if m:
            printed[m.group(2)] = (m.group(1), m.group(3), [float(v) for v in m.group(4).split(',')], [float(v) for v in m.group(5).split(',')])
    printed_all[w] = printed
    for nm, r in want.items():
        if r['host'] != w:
            continue
        m = have.get(nm)
        if m is None:
            R['problems'].append(['missing model', w, nm])
            continue
        diff = []
        if m['work'] != r['work']:
            diff.append('work')
        for k, v in (('at', r['at']), ('pivot', r['pivot']), ('rotate', [0, 0, r['rotate']]), ('scale', r['scale'])):
            if any(abs(a - b) > 1e-4 for a, b in zip(m[k], v)):
                diff.append('%s %s != %s' % (k, m[k], v))
        if (m.get('mirror') or '') != r['mirror']:
            diff.append('mirror %r' % m.get('mirror'))
        if not m.get('enabled', True):
            diff.append('disabled')
        md = {k: v for k, v in (m.get('meta') or {}).items() if k != 'id'}
        if md != r['meta']:
            diff.append('meta %s != %s' % (md, r['meta']))
        at = np.array(r['at'], float)
        if probe.get('dx') and probe['dx'].rsplit(':', 1)[0] == nm:
            at[0] += float(probe['dx'].rsplit(':', 1)[1])
        blo, bhi = r['g'].bbox(at)
        pr = printed.get(nm)
        box_err = None
        if not pr:
            diff.append('not printed by sub=models')
        else:
            if pr[0] != '✓' or pr[1] != 'ok':
                diff.append('cli %s %s' % (pr[0], pr[1]))
            box_err = round(float(max(np.abs(np.array(pr[2]) - blo).max(), np.abs(np.array(pr[3]) - bhi).max())), 3)
            if box_err > 0.051:
                diff.append('box off by %s' % box_err)
        R['models'][nm] = {'host': w, 'diff': diff, 'box_err': box_err, 'cli': pr[:2] if pr else None}
        if diff:
            R['problems'].append([nm] + diff)
sc = printed_all.get(ASM, {})
carv = [k for k in sc if 'carving' in k or '雕花' in k]
R['stern_carving_model_cli'] = {k: sc[k][:2] for k in carv}
if not carv or any(sc[k][0] != '✓' or sc[k][1] != 'ok' for k in carv):
    R['problems'].append(['stern carving model', R['stern_carving_model_cli']])

# 6. export format=parts: spin / hawse in the meta the game reads
pth = os.path.join(tempfile.mkdtemp(), 'parts.json')
cli(['op=export', 'format=parts', 'work=' + ASM, 'out=' + pth])
txt = open(pth, encoding='utf-8').read()
try:
    P = json.loads(txt)
except ValueError:
    P = None
found = {}


def walk(o):
    if isinstance(o, dict):
        mt = o.get('meta') if isinstance(o.get('meta'), dict) else None
        if mt and mt.get('kind') in ('rudder', 'tiller', 'anchor', 'wheel'):
            found.setdefault(mt['kind'], []).append({'name': o.get('name') or o.get('path'), 'spin': mt.get('spin'), 'spin_k': mt.get('spin_k'),
                                                    'hawse': mt.get('hawse'), 'pivot': [mt.get('spin_pivot_x'), mt.get('spin_pivot_z')]})
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
walk(P)
R['parts_export'] = found
if [f['spin'] for f in found.get('rudder', [])] != ['rudder'] or [f['spin'] for f in found.get('tiller', [])] != ['rudder']:
    R['problems'].append(['parts spin', found.get('rudder'), found.get('tiller')])
if len(found.get('anchor', [])) != 2 or not all(f['hawse'] for f in found['anchor']):
    R['problems'].append(['parts anchors', found.get('anchor')])
if found.get('wheel'):
    R['problems'].append(['unexpected wheel', found['wheel']])

# 7. settled cloth vs the new parts
obj = opt.get('obj')
if not obj and not probe:
    obj = os.path.join(tempfile.mkdtemp(), 'a.obj')
    cli(['op=export', 'format=obj', 'work=' + ASM, 'out=' + obj, 'ropes=0'])
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
        cloth[nm] = dense(np.array([[V[a], V[b], V[c]] for a, b, c in tk]), 0.25)
    parts = {}
    for key, f in (('rudder', 'rudder'), ('tiller', 'tiller'), ('collar', 'fittings'), ('rollers', 'rollers')):
        parts[key] = corners(np.array(sorted(load(os.path.join(M, 'helm', f + '.vox.txt'))), float))
    for nm, r in want.items():
        if nm.startswith('錨'):
            parts[nm] = r['g'].world(r['g'].samples, r['at'])
    res = {}
    for pk, Pp in parts.items():
        kd = cKDTree(Pp)
        best = None
        for sn, C in cloth.items():
            d, _ = kd.query(C)
            if best is None or float(d.min()) < best[0]:
                best = [round(float(d.min()), 2), sn]
        res[pk] = best
    R['cloth_clearance'] = res
    R['cloth_clearance_min'] = min(res.values(), key=lambda v: v[0])
    R['cloth_sails'] = sorted(cloth)
    if R['cloth_clearance_min'][0] <= 0.5:
        R['problems'].append(['cloth', R['cloth_clearance_min']])
R['problems_total'] = len(R['problems'])
print(json.dumps(R, ensure_ascii=False, indent=1))
if write:
    with open(os.path.join(design, 'verify_step11.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
