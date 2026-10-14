# TASK-0575 落格：照 verify_gunfittings.json —— 每層一件砲具子作品（0.1 m、parent 船殼、tags sub）→ stampvox 環（讀回 placed）→ 固定點 →
#   那一層甲板子作品裡的關聯 `砲具` at frame_at → 組裝件掛砲索（端點 model:<甲板>/<砲>/<點> → <甲板>/砲具/<環>）
#   用法：python -I -X utf8 tools/apply_gunfittings.py <design> works|anchors|links|ropes
#   參考風暴角號 apply_gunfittings.py（summit）；IOException 中英文都重試
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
HULL, ASM = 'gura-tridente-01m', 'gura-tridente-01m-assembly'
V = json.load(open(os.path.join(D, 'verify_gunfittings.json'), encoding='utf-8'))
ok = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, retried
    for k in range(5):
        r = run(args)
        out = r.stdout + r.stderr
        if r.returncode and any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 4:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        print('✗ rc=%d' % r.returncode, ' '.join(args[:6]))
        print(out[-1200:])
        raise SystemExit(1)
    ok += 1
    return r.stdout


xyz = lambda v: ','.join('%g' % c for c in v)
if step == 'works':
    for w in V['works']:
        if run(['op=work', 'sub=show', 'work=' + w['work']]).returncode != 0:
            cli(['op=work', 'sub=create', 'persona=gura', 'id=' + w['work'], 'title=' + w['title'], 'size=' + xyz(w['frame_size']), 'parent_work=' + HULL, 'tags=sub'])
            cli(['op=work', 'sub=update', 'persona=gura', 'work=' + w['work'], 'meters_per_voxel=0.1'])
        have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + w['work']])).group(1))
        if have == 0:
            out = cli(['op=stampvox', 'persona=gura', 'work=' + w['work'], 'voxels=' + os.path.join(D, w['file']).replace('\\', '/'), 'at=0,0,0',
                       'expect_pixels=%d' % w['voxels'], 'share=0'])
            n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
            if n != w['voxels']:
                raise SystemExit('✗ %s placed %d ≠ %d' % (w['work'], n, w['voxels']))
        elif have != w['voxels']:
            raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (w['work'], have, w['voxels']))
        print('✓', w['work'], w['voxels'])
elif step == 'anchors':
    for i, a in enumerate(V['anchors'], 1):
        cli(['op=work', 'sub=anchor', 'persona=gura', 'work=' + a['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
             'note=%s（%s；draft_gunfittings.py）' % ('船牆環' if a['kind'] == 'ring' else '甲板環', a['gun'])])
        if i % 100 == 0:
            print('  固定點 %d／%d' % (i, len(V['anchors'])), flush=True)
    print('✓ 固定點', len(V['anchors']))
elif step == 'links':
    for w in V['works']:
        cli(['op=work', 'sub=link', 'persona=gura', 'work=' + w['host_work'], 'name=' + w['link'], 'source_work=' + w['work'], 'at=' + xyz(w['frame_at']),
             'overwrite=1', 'note=砲具（TASK-0575）'])
        print('✓ 關聯', w['host_work'], w['link'], w['frame_at'])
elif step == 'ropes':
    for i, rp in enumerate(V['ropes'], 1):
        cli(['op=work', 'sub=rope', 'persona=gura', 'work=' + ASM, 'name=' + rp['name'], 'from=' + rp['from'], 'to=' + rp['to'], 'color=' + rp['color'],
             'thickness=%g' % rp['thickness'], 'slack=%g' % rp['slack'], 'group=' + rp['group'], 'overwrite=1', 'note=砲索（TASK-0575）'])
        if i % 100 == 0:
            print('  繩 %d／%d' % (i, len(V['ropes'])), flush=True)
    print('✓ 繩', len(V['ropes']))
else:
    raise SystemExit('步驟？ works|anchors|links|ropes')
print(step, 'ok', ok, 'IOException 重試', retried)
