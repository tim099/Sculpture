# 抄自三叉戟號 gura-tridente-01m/design/tools/rigging_apply.py（gura）；改：作品、persona、TASK。
# 階段七落格：照 rigging_plan.json —— channels 子作品＋兩條關聯、固定點（船殼、channels、三根桅、艏斜桅）、繩（不綁帆的先）、帆、綁帆角的繩、預設風、meta（批次）
#   用法：python -I -X utf8 tools/rigging_apply.py <design> [channels] [anchors] [ropes] [sails] [sailropes] [wind] [meta]（不給 ⇒ 全部，照順序）
#   · 同名的固定點、繩、帆一律 overwrite=1（以 plan 為準）；每一筆讀回 exit 0 才往下；IOException 自動重試
import json, os, re, subprocess, sys, tempfile

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
steps = [a for a in sys.argv[2:] if not a.startswith('--')] or ['channels', 'anchors', 'ropes', 'sails', 'sailropes', 'wind', 'meta']
HULL = 'kaguya-gloire-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
P = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))
retries = 0


def cli(*args, ok=(0,)):
    global retries
    for k in range(5):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = r.stdout + r.stderr
        if r.returncode in ok or 'IOException' not in out:
            break
        retries += 1
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return r.returncode, out


if 'channels' in steps:
    C = P['channels']
    if not os.path.exists(os.path.join(WORKS, C['work'], 'work.json')):
        cli('op=work', 'sub=create', 'persona=kaguya', 'id=' + C['work'], 'title=' + C['title'], 'parent_work=' + HULL, 'size=' + ','.join(map(str, C['size'])), 'tags=sub')
        cli('op=work', 'sub=update', 'persona=kaguya', 'work=' + C['work'], 'meters_per_voxel=0.1')
    path = os.path.join(design, 'masks', 'rigging', 'channels.vox.txt')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli('op=stats', 'work=' + C['work'], 'links=none')[1]).group(1))
    if have == 0:
        _, out = cli('op=stampvox', 'persona=kaguya', 'work=' + C['work'], 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
        if int(re.search(r'🔢 placed = (\d+)', out).group(1)) != n:
            raise SystemExit('✗ channels placed')
    elif have != n:
        raise SystemExit('✗ channels 已有 %d 格 ≠ %d' % (have, n))
    for name, at, mir in (('channels', C['at'], False), ('channels-鏡像', C['at_mirror'], True)):
        args = ['op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=' + name, 'source_work=' + C['work'], 'at=%d,%d,%d' % tuple(at), 'note=階段七（TASK-0612）']
        if mir:
            args.append('mirror=y')
        cli(*args, ok=(0, 2))
    print('✓ channels %d 格、關聯 channels／channels-鏡像' % n)
if 'anchors' in steps:
    k = 0
    for part, items in P['anchors'].items():
        work = P['anchor_works'][part]
        for nm, xyz in sorted(items.items()):
            cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + work, 'name=' + nm, 'at=%d,%d,%d' % tuple(xyz), 'overwrite=1', 'note=階段七（draft_rigging.py）')
            k += 1
    print('✓ 固定點 %d' % k)


def rope(r):
    args = ['op=work', 'sub=rope', 'persona=kaguya', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'slack=%g' % r['slack'],
            'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'overwrite=1', 'note=階段七（TASK-0612）']
    cli(*args)


if 'ropes' in steps:
    rs = [r for r in P['ropes'] if not r['from'].startswith('sail:') and not r['to'].startswith('sail:')]
    for i, r in enumerate(rs, 1):
        rope(r)
        if i % 50 == 0:
            print('  繩 %d/%d' % (i, len(rs)), flush=True)
    print('✓ 繩（不綁帆）%d' % len(rs))
if 'sails' in steps:
    for s in P['sails']:
        args = ['op=work', 'sub=sail', 'persona=kaguya', 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(s['corners']), 'bind=' + ','.join(map(str, s['bind'])),
                'color=' + s['color'], 'fullness=%g' % s['fullness'], 'overwrite=1', 'note=階段七（TASK-0612）']
        if s['corner_names']:
            args.append('corner_names=' + '|'.join(s['corner_names']))
        if s['free']:
            args.append('free=' + ','.join(map(str, s['free'])))
        if s.get('texture'):
            args.append('texture=' + os.path.abspath(os.path.join(design, s['texture'])).replace('\\', '/'))
        cli(*args)
    print('✓ 帆 %d' % len(P['sails']))
if 'sailropes' in steps:
    rs = [r for r in P['ropes'] if r['from'].startswith('sail:') or r['to'].startswith('sail:')]
    for r in rs:
        rope(r)
    print('✓ 綁帆角的繩 %d' % len(rs))
if 'wind' in steps:
    cli('op=work', 'sub=wind', 'persona=kaguya', 'work=' + ASM, 'wind=%g,%g,%g' % tuple(P['wind']), 'sail_seconds=%g' % P['sail_seconds'])
    print('✓ 預設風 %s、%g 秒' % (P['wind'], P['sail_seconds']))
if 'meta' in steps:
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, 'meta.tsv')
        with open(f, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('# 光榮號 帆、旗、帆自己的繩（造船規格 §9.1）\n')
            for part, name, meta in P['meta']:
                fh.write('%s\t%s\t%s\n' % (part, name, json.dumps(meta, ensure_ascii=False, separators=(',', ':'))))
        _, out = cli('op=work', 'sub=meta', 'persona=kaguya', 'work=' + ASM, 'file=' + f.replace('\\', '/'))
    print('✓ meta %d 筆' % len(P['meta']))
print('IOException 重試 %d 次' % retries)
