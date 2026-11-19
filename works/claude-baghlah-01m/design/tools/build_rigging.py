# Source: calli-cosecha-01m/design/tools/rigging_apply.py (Harvest) -- adapted for the Star (TASK-0019 step 8)
# Step 8 placement from rigging_plan.json: new sub-works (rings, stern spars, halyard bitt) + links, anchors, ropes that do
#   not touch a sail, sails, the sails' own ropes, default wind, meta (one batch file).
#   Usage: python -X utf8 tools/build_rigging.py <design> [parts] [anchors] [ropes] [sails] [sailropes] [wind] [meta] [prune]
#          (none given = all, in this order; SENATE = wrapper path)
#          prune: remove the step-8 ropes / sails / anchors (note starts with 步驟 8) that rigging_plan.json no longer has
#   * Only exit 0 counts (step 6 learned exit 2 hides a blocked link); anchors / ropes / sails use overwrite=1 (plan wins).
#   * A sub-work that already exists is neither recreated nor restamped; a link that already exists is not re-added.
import json, os, re, subprocess, sys, tempfile

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
steps = [a for a in sys.argv[2:] if not a.startswith('--')] or ['parts', 'anchors', 'ropes', 'sails', 'sailropes', 'wind', 'meta', 'prune']
HULL = 'claude-baghlah-01m'
ASM = HULL + '-assembly'
PERSONA = 'Claude-Ojousama'
SENATE = os.environ.get('SENATE', 'senate')
WORKS = os.path.dirname(os.path.dirname(design))
NOTE = '步驟 8（TASK-0019；design/draft_rigging.py）'
P = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
PARTS = [('rings', 'rings', '星辰號 支索的環（船外兩舷）'), ('stern-spars', 'stern_spars', '星辰號 船尾的桿（國旗桿＋bumkin）'),
         ('halyard-bitt', 'halyard_bitt', '星辰號 升降索柱 e')]
retries = 0


def cli(*args):
    global retries
    for _ in range(5):
        r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = r.stdout + r.stderr
        if r.returncode == 0 or 'IOException' not in out:
            break
        retries += 1
    if r.returncode != 0:
        print(out[-2000:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args)[:300]))
    return out


if 'parts' in steps:
    links = json.load(open(os.path.join(WORKS, ASM, 'links.json'), encoding='utf-8'))
    have_links = {l['name'] for l in (links if isinstance(links, list) else links.get('links', []))}
    for key, fn, title in PARTS:
        w = '%s-%s' % (HULL, key)
        if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
            cli('op=work', 'sub=create', 'persona=' + PERSONA, 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=420,160,120', 'tags=sub')
            cli('op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + w, 'meters_per_voxel=0.1')
            path = os.path.join(design, 'masks', 'rigging', fn + '.vox.txt')
            n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
            out = cli('op=stampvox', 'persona=' + PERSONA, 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
            m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
            got = int(m.group(1).replace(',', '')) if m else None
            if got != n:
                print(out[-1500:])
                raise SystemExit('✗ placed %s != %d (%s)' % (got, n, w))
            print('✓ created %s, stampvox %d' % (w, n))
        else:
            print('· exists', w)
        ln = P['links'][key]
        if ln not in have_links:
            cli('op=work', 'sub=link', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + ln, 'source_work=' + w, 'at=0,0,0', 'note=%s：%s' % (NOTE, title))
            print('  link', ln)
if 'anchors' in steps:
    k = 0
    for part, items in P['anchors'].items():
        work = P['anchor_works'][part]
        for nm, xyz in sorted(items.items()):
            cli('op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + work, 'name=' + nm, 'at=%d,%d,%d' % tuple(xyz), 'overwrite=1', 'note=' + NOTE)
            k += 1
    print('✓ anchors %d' % k)


def rope(r):
    cli('op=work', 'sub=rope', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'slack=%g' % r['slack'],
        'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'overwrite=1', 'note=' + NOTE)


is_sail_rope = lambda r: r['from'].startswith('sail:') or r['to'].startswith('sail:')
if 'ropes' in steps:
    rs = [r for r in P['ropes'] if not is_sail_rope(r)]
    for r in rs:
        rope(r)
    print('✓ ropes (no sail end) %d' % len(rs))
if 'sails' in steps:
    for s in P['sails']:
        args = ['op=work', 'sub=sail', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(s['corners']), 'bind=' + ','.join(map(str, s['bind'])),
                'color=' + s['color'], 'fullness=%g' % s['fullness'], 'overwrite=1', 'note=' + NOTE]
        if s['corner_names']:
            args.append('corner_names=' + '|'.join(s['corner_names']))
        if s['free']:
            args.append('free=' + ','.join(map(str, s['free'])))
        if s.get('texture'):
            args.append('texture=' + os.path.join(design, s['texture']))
        cli(*args)
    print('✓ sails %d' % len(P['sails']))
if 'sailropes' in steps:
    rs = [r for r in P['ropes'] if is_sail_rope(r)]
    for r in rs:
        rope(r)
    print('✓ sail ropes %d' % len(rs))
if 'wind' in steps:
    cli('op=work', 'sub=wind', 'persona=' + PERSONA, 'work=' + ASM, 'wind=%g,%g,%g' % tuple(P['wind']), 'sail_seconds=%g' % P['sail_seconds'])
    print('✓ wind %s, %g s' % (P['wind'], P['sail_seconds']))
if 'meta' in steps:
    d = tempfile.mkdtemp()
    f = os.path.join(d, 'meta.tsv')
    with open(f, 'w', encoding='utf-8', newline='\n') as fh:
        for part, name, meta in P['meta']:
            fh.write('%s\t%s\t%s\n' % (part, name, json.dumps(meta, ensure_ascii=False, separators=(',', ':'))))
    cli('op=work', 'sub=meta', 'persona=' + PERSONA, 'work=' + ASM, 'file=' + f)
    print('✓ meta %d' % len(P['meta']))
if 'prune' in steps:                         # step-8 ropes / sails / anchors that the plan no longer has (only ones this tool wrote)
    def items(path, key):
        if not os.path.exists(path):
            return []
        d = json.load(open(path, encoding='utf-8'))
        return d if isinstance(d, list) else d.get(key, [])
    keep_r = {r['name'] for r in P['ropes']}
    keep_s = {s['name'] for s in P['sails']}
    n = 0
    for r in items(os.path.join(WORKS, ASM, 'ropes.json'), 'ropes'):
        if r.get('note', '').startswith('步驟 8') and r['name'] not in keep_r:
            cli('op=work', 'sub=unrope', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + r['name'])
            n += 1
    for s in items(os.path.join(WORKS, ASM, 'sails.json'), 'sails'):
        if s.get('note', '').startswith('步驟 8') and s['name'] not in keep_s:
            cli('op=work', 'sub=unsail', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + s['name'])
            n += 1
    for part, work in P['anchor_works'].items():
        keep_a = set(P['anchors'].get(part, {}))
        for a in items(os.path.join(WORKS, work, 'anchors.json'), 'anchors'):
            if a.get('note', '').startswith('步驟 8') and a['name'] not in keep_a:
                cli('op=work', 'sub=unanchor', 'persona=' + PERSONA, 'work=' + work, 'name=' + a['name'])
                n += 1
    print('✓ pruned %d' % n)
print('IOException retries %d' % retries)
