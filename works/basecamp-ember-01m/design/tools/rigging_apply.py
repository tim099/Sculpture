# 餘燼號 階段七：照 masks/rigging 與 rigging_placement.json 下 CLI
# 用法：python -I rigging_apply.py <design 資料夾> <步驟>
#   步驟：fittings（建子作品、落格、固定點、關聯；船殼固定點）｜sails（風＋帆）｜ropes（繩，母繩先、子繩後）
#   重跑：子作品已在 ⇒ 不重建不重落；固定點、關聯、帆、繩 overwrite=1
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
P = 'basecamp-ember-01m'
ASM = P + '-assembly'
PL = json.load(open(os.path.join(D, 'rigging_placement.json'), encoding='utf-8'))
TITLE = {'channels': '餘燼號 channels（一舷）', 'belaying': '餘燼號 舷牆 pin rails 與 cleats（一舷）', 'fiferails': '餘燼號 fife rails 與 bitts'}
ok = bad = 0


def cli(args, show=False, quiet_fail=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        if not quiet_fail:
            bad += 1
            print('✗', ' '.join(args[:6])[:160], (r.stdout + r.stderr)[-300:])
    else:
        ok += 1
        if show:
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%g' % c for c in v)


if step == 'fittings':
    for nm, F in PL['fittings'].items():
        rc, _ = cli(['op=work', 'sub=show', 'work=' + F['work']], quiet_fail=True)
        if rc:
            cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + F['work'], 'title=' + TITLE[nm], 'size=' + xyz(F['size']), 'parent_work=' + P, 'tags=sub'], show=True)
            cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + F['work'], 'meters_per_voxel=0.1'])
            path = os.path.join(D, 'masks', 'rigging', nm + '.vox.txt').replace('\\', '/')
            n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
            cli(['op=stampvox', 'persona=basecamp', 'work=' + F['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n], show=True)
        for a in PL['anchors'][nm]:
            cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + F['work'], 'name=' + a['name'], 'at=' + xyz(a['local']), 'overwrite=1',
                 'note=憲法號 %s 換算（階段七；世界 %s）' % (xyz(a['con_world']), xyz(a['world']))])
        host = F['parent_link_work'] or ASM
        cli(['op=work', 'sub=link', 'persona=basecamp', 'work=' + host, 'name=' + F['link'], 'source_work=' + F['work'], 'at=' + xyz(F['at'])], show=True)
        if F.get('mirror_link'):
            cli(['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=' + F['mirror_link'], 'source_work=' + F['work'], 'at=' + xyz(F['mirror_at']), 'mirror=y'], show=True)
    for a in PL['hull_anchors']:
        cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + P, 'name=' + a['name'], 'at=' + xyz([int(t) for t in a['at']]), 'overwrite=1',
             'note=主桅 stay 的 knighthead（憲法號 %s 換算）' % xyz(a['con_at'])])

elif step == 'sails':
    cli(['op=work', 'sub=wind', 'persona=basecamp', 'work=' + ASM, 'wind=' + xyz(PL['wind']), 'sail_seconds=%g' % PL['seconds']])
    for s in PL['sails']:
        args = ['op=work', 'sub=sail', 'persona=basecamp', 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(c['at'] for c in s['corners']),
                'corner_names=' + '|'.join(c['name'] for c in s['corners']), 'bind=' + ','.join(str(b) for b in s['bind']),
                'fullness=%g' % s['fullness'], 'color=' + s['color'], 'overwrite=1', 'note=' + s['note']]
        fr = [c['name'] for c in s['corners'] if not c['pin']]
        if fr:
            args.append('free=' + ','.join(fr))
        if s.get('res'):
            args.append('res=%d' % s['res'])
        cli(args)

elif step == 'ropes':
    t0 = time.time()
    for i, r in enumerate(PL['ropes']):
        args = ['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
                'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'note=' + r.get('note', '')]
        if r.get('group'):
            args.append('group=' + r['group'])
        cli(args)
        if (i + 1) % 100 == 0:
            print('ropes', i + 1, 'ok', ok, 'bad', bad, '%.0fs' % (time.time() - t0), flush=True)
else:
    raise SystemExit('步驟？ fittings｜sails｜ropes')
print(step, 'ok', ok, 'bad', bad)
