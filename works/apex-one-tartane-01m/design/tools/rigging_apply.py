# 塔爾塔納 步驟 8（TASK-1299）：channels＋旗桿子作品、固定點、靜索、橫繩組（climb=1）、帆與旗、帆索、預設風、meta
#   用法：python -I -X utf8 tools/rigging_apply.py <design> [channels] [anchors] [ropes] [ratlines] [sails] [sailropes] [wind] [meta]
import json, os, re, subprocess, sys, tempfile

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
steps = [a for a in sys.argv[2:] if not a.startswith('--')] or ['channels', 'anchors', 'ropes', 'ratlines', 'sails', 'sailropes', 'wind', 'meta']
HULL = 'apex-one-tartane-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
P = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
retries = 0


def cli(*args, ok=(0,)):
    global retries
    for k in range(5):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = r.stdout + r.stderr
        if r.returncode in ok or 'IOException' not in out:
            break
        retries += 1
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return r.returncode, out


if 'channels' in steps:
    for sub, link_name, title, fn in (
        ('channels', '支索板', '塔爾塔納 兩舷支索板＋deadeyes', 'channels.vox.txt'),
        ('flagstaff', '旗桿', '塔爾塔納 船尾國旗桿', 'flagstaff.vox.txt'),
    ):
        w = '%s-%s' % (HULL, sub)
        if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
            cli('op=work', 'sub=create', 'persona=apex-one', 'id=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=360,192,320')
            cli('op=work', 'sub=update', 'persona=apex-one', 'work=' + w, 'meters_per_voxel=0.1', 'tags=sub')
            path = os.path.join(design, 'masks', 'rigging', fn)
            n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
            _, out = cli('op=stampvox', 'persona=apex-one', 'work=' + w,
                         'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
            if int(re.search(r'placed\D{0,12}(\d+)', out).group(1)) != n:
                raise SystemExit('✗ %s placed' % sub)
            print('✓ %s %d 格' % (sub, n))
        cli('op=work', 'sub=link', 'persona=apex-one', 'work=' + ASM, 'name=' + link_name, 'source_work=' + w, 'at=0,0,0', 'note=步驟 8', ok=(0, 2))

if 'anchors' in steps:
    k = 0
    for part, items in P['anchors'].items():
        work = P['anchor_works'][part]
        for nm, xyz in sorted(items.items()):
            cli('op=work', 'sub=anchor', 'persona=apex-one', 'work=' + work, 'name=' + nm,
                'at=%d,%d,%d' % tuple(xyz), 'overwrite=1', 'note=步驟 8（draft_rigging.py）')
            k += 1
    print('✓ 固定點 %d' % k)


def rope(r):
    cli('op=work', 'sub=rope', 'persona=apex-one', 'work=' + ASM, 'name=' + r['name'],
        'from=' + r['from'], 'to=' + r['to'], 'slack=%g' % r['slack'],
        'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'overwrite=1', 'note=步驟 8')


if 'ropes' in steps:
    rs = [r for r in P['ropes'] if not r['from'].startswith('sail:') and not r['to'].startswith('sail:')]
    for r in rs:
        rope(r)
    print('✓ 繩（不綁帆）%d' % len(rs))

if 'ratlines' in steps:
    for r in P['ratline_sets']:
        args = ['op=work', 'sub=ratlines', 'persona=apex-one', 'work=' + ASM, 'name=' + r['name'],
                'rope_a=' + r['rope_a'], 'rope_b=' + r['rope_b'],
                'step=%g' % r['step'], 'start=%g' % r['start'], 'stop=%g' % r['stop'], 'min_span=%g' % r['min_span'],
                'thickness=%g' % r['thickness'], 'color=#2b2620', 'group=' + r['group'], 'overwrite=1']
        if r.get('climb'):
            args += ['climb=1', 'foot=' + r['foot'], 'head=' + r['head']]
        cli(*args)
    print('✓ 橫繩組 %d' % len(P['ratline_sets']))

if 'sails' in steps:
    for s in P['sails']:
        args = ['op=work', 'sub=sail', 'persona=apex-one', 'work=' + ASM, 'name=' + s['name'],
                'corners=' + '|'.join(s['corners']), 'bind=' + ','.join(map(str, s['bind'])),
                'color=' + s['color'], 'fullness=%g' % s['fullness'], 'overwrite=1', 'note=步驟 8']
        if s['corner_names']:
            args.append('corner_names=' + '|'.join(s['corner_names']))
        if s['free']:
            args.append('free=' + ','.join(map(str, s['free'])))
        if s.get('texture'):
            args.append('texture=' + os.path.abspath(os.path.join(design, s['texture'])).replace('\\', '/'))
        cli(*args)
    print('✓ 帆／旗 %d' % len(P['sails']))

if 'sailropes' in steps:
    rs = [r for r in P['ropes'] if r['from'].startswith('sail:') or r['to'].startswith('sail:')]
    for r in rs:
        rope(r)
    print('✓ 綁帆角之繩 %d' % len(rs))

if 'wind' in steps:
    cli('op=work', 'sub=wind', 'persona=apex-one', 'work=' + ASM, 'wind=%g,%g,%g' % tuple(P['wind']), 'sail_seconds=%g' % P['sail_seconds'])
    print('✓ 預設風 %s、%g 秒' % (P['wind'], P['sail_seconds']))

if 'meta' in steps:
    d = tempfile.mkdtemp()
    f = os.path.join(d, 'meta.tsv')
    with open(f, 'w', encoding='utf-8', newline='\n') as fh:
        for part, name, meta in P['meta']:
            fh.write('%s\t%s\t%s\n' % (part, name, json.dumps(meta, ensure_ascii=False, separators=(',', ':'))))
    cli('op=work', 'sub=meta', 'persona=apex-one', 'work=' + ASM, 'file=' + f.replace('\\', '/'))
    print('✓ meta %d 筆' % len(P['meta']))

print('IOException 重試 %d 次' % retries)
