# Bring a sub-work in line with its design list by the difference only (TASK-0019 step 6 v2 fixes after the verifier):
#   work cells (events replay) vs list ⇒ carvevox (colour-guarded) the extra cells, stampvox the missing ones,
#   stampvox overwrite=1 the recoloured ones. Each cut carries expect_pixels; placed / carved must match the list length.
#   Usage: python -X utf8 tools/delta_apply.py <design> <work-suffix> <list rel. to masks/> [--dry]
#   * Replay is the same as tools/check_deco.py (stampvox placed_colored, box, carved_voxels, workedit after[]).
import glob, json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
suffix, rel = sys.argv[2], sys.argv[3]
dry = '--dry' in sys.argv
HULL = 'claude-baghlah-01m'
WORK = '%s-%s' % (HULL, suffix)
PERSONA = 'Claude-Ojousama'
SENATE = os.environ.get('SENATE', 'senate')
WORKS = os.path.dirname(os.path.dirname(design))
TMP = os.path.join(design, 'masks', 'step6', 'delta')


def replay(work_dir):
    cells = {}
    for p in sorted(glob.glob(os.path.join(work_dir, 'events', '*', '*.json'))):
        e = json.load(open(p, encoding='utf-8'))
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
    return cells


def load(path):
    out = {}
    for l in open(path, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            x, y, z, c = map(int, l.split(','))
            out[(x, y, z)] = c
    return out


def cli(*args):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode != 0:
        print(out[-2000:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args)))
    return out


have = replay(os.path.join(WORKS, WORK))
want = load(os.path.join(design, 'masks', rel))
extra = {k: have[k] for k in have if k not in want}
miss = {k: want[k] for k in want if k not in have}
recol = {k: want[k] for k in want if k in have and have[k] != want[k]}
print('%s: have %d, want %d ⇒ carve %d, add %d, recolour %d' % (WORK, len(have), len(want), len(extra), len(miss), len(recol)))
if dry:
    raise SystemExit(0)
os.makedirs(TMP, exist_ok=True)
for tag, cs, op in (('carve', extra, 'carvevox'), ('add', miss, 'stampvox'), ('recolour', recol, 'stampvox')):
    if not cs:
        continue
    path = os.path.join(TMP, '%s_%s.vox.txt' % (suffix, tag))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s %s (%d cells, at=0,0,0; step 6 v2)\n' % (WORK, tag, len(cs)))
        for (x, y, z), c in sorted(cs.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    args = ['op=' + op, 'persona=' + PERSONA, 'work=' + WORK, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % len(cs)]
    if op == 'stampvox':
        args.append('share=0')
    if tag == 'recolour':
        args.append('overwrite=1')
    out = cli(*args)
    m = re.search(r'(placed|carved|刻)\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(2).replace(',', '')) if m else None
    print('  %s %s: %d (engine says %s)' % (op, tag, len(cs), got))
    if got != len(cs):
        print(out[-1500:])
        raise SystemExit('✗ count mismatch')
after = replay(os.path.join(WORKS, WORK))
print('  after: %d cells; missing %d, extra %d, colour diff %d' % (len(after), len(set(want) - set(after)), len(set(after) - set(want)),
                                                                   sum(1 for k in set(want) & set(after) if want[k] != after[k])))
