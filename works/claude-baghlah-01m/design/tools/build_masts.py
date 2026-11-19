# Source: calli-cosecha-01m/design/tools/build_masts.py (Harvest) -- adapted for the Star (TASK-0019 step 7)
# Step 7 placement: mast / jib-boom / cable-beam sub-works, lateen yard sub-works (+ anchors), yard models in their mast
#   sub-works, assembly links (masts meta kind=mast + mast=; jib boom mast=bowsprit; cable beam plain).
#   Usage: python -X utf8 tools/build_masts.py <design> <stage>   stage = parts | yards | links   (SENATE = wrapper path)
#   * Stops at the first non-zero exit (only 0 counts: step 6 learned exit 2 hides a blocked link).
#   * A sub-work that already exists is neither recreated nor restamped.
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
stage = sys.argv[2]
HULL = 'claude-baghlah-01m'
ASM = HULL + '-assembly'
PERSONA = 'Claude-Ojousama'
SENATE = os.environ.get('SENATE', 'senate')
WORKS = os.path.dirname(os.path.dirname(design))
NOTE = '步驟 7（TASK-0019；design/draft_masts.py）'
PARTS = [('mast-main', 'main', '480,160,400', '星辰號 主桅（柚木一整根，28 m）', '主桅', {'kind': 'mast', 'mast': 'main'}),
         ('mast-mizzen', 'mizzen', '480,160,400', '星辰號 後桅（17 m）', '後桅', {'kind': 'mast', 'mast': 'mizzen'}),
         ('jibboom', 'jibboom', '480,160,400', '星辰號 foc 的桿子（bâton-volant，11.5 m）', 'foc桿', {'kind': None, 'mast': None}),   # step 14: no yard binds a bowsprit mast => shipcheck warns, so the link carries no mast meta
         ('cable-beam', 'cable_beam', '420,160,120', '星辰號 錨纜橫樑', '錨纜橫樑', None)]


def cli(*args, ok=(0,)):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args)))
    return out


def exists(w):
    return os.path.exists(os.path.join(WORKS, w, 'work.json'))


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=' + PERSONA, 'work=' + work, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s != %d (%s %s)' % (got, n, work, os.path.basename(path)))
    print('  stampvox %s %s: %d' % (work, os.path.basename(path), n))


def create(w, title, size):
    cli('op=work', 'sub=create', 'persona=' + PERSONA, 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=' + size, 'tags=sub')
    cli('op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + w, 'meters_per_voxel=0.1')
    print('✓ created', w)


if stage == 'parts':
    for key, fn, size, title, _, _ in PARTS:
        w = '%s-%s' % (HULL, key)
        if exists(w):
            print('· exists', w)
            continue
        create(w, title, size)
        stamp(w, os.path.join(design, 'masks', 'masts', fn + '.vox.txt'))
elif stage == 'yards':
    LAT = json.load(open(os.path.join(design, 'yards_lateen.json'), encoding='utf-8'))
    for key, v in LAT.items():
        w = '%s-yard-%s-lateen' % (HULL, key)
        if exists(w):
            print('· exists', w)
            continue
        create(w, '星辰號 %s 三角帆桁（%.1f m）' % ({'main': '主桅', 'mizzen': '後桅'}[key], v['len_m']), '%d,%d,%d' % tuple(v['size']))
        stamp(w, os.path.join(design, 'masks', 'yards', 'lateen-%s.vox.txt' % key))
        for an, at in sorted(v['anchors'].items()):
            cli('op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'note=' + NOTE + '：帆桁固定點')
        print('  anchors %s: %d' % (w, len(v['anchors'])))
elif stage == 'links':
    for key, fn, size, title, link, meta in PARTS:
        args = ['op=work', 'sub=link', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + link, 'source_work=%s-%s' % (HULL, key), 'at=0,0,0',
                'note=%s：%s' % (NOTE, title)]
        if meta:
            args.append('meta=' + json.dumps(meta, separators=(',', ':')))
        cli(*args)
        print('✓ link', link)
    for p in json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8')):
        cli('op=work', 'sub=model', 'persona=' + PERSONA, 'work=%s-%s' % (HULL, p['host']), 'name=' + p['name'], 'source_work=' + p['work'],
            'at=%g,%g,%g' % tuple(p['at']), 'pivot=%g,%g,%g' % tuple(p['pivot']), 'rotate=%g,%g,%g' % tuple(p['rotate']),
            'scale=%g,%g,%g' % tuple(p['scale']), 'meta=' + json.dumps(p['meta'], ensure_ascii=False, separators=(',', ':')),
            'note=%s：三角帆桁（rig=lateen；yard=gaff）' % NOTE)
        print('✓ model', p['host'], p['name'])
    print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-30:]))
else:
    raise SystemExit('stage = parts | yards | links')
