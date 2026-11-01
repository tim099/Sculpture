# 杉心號 步驟 7–8 落格（TASK-1152）：坐板桅孔、桅子作品、拉丁帆桁子作品＋固定點、帆桁模型（放在桅子作品裡）、組裝件關聯、固定點、帆、繩、meta
#   出處：kotoko-fusta-01m/design/tools/build_rig.py（越嶺號）—— 固定點的作品改成船殼／桅，persona 改 basecamp。
#   用法：python -I -X utf8 tools/build_rig.py [--skip=<步驟,…>]   步驟：holes create stamp yanchors models links anchors sails ropes meta（繩的端點會指到帆角 ⇒ 帆先掛）
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'basecamp-piragua-01m'
ASM = HULL + '-assembly'
P = 'persona=basecamp'
WORK = {'hull': HULL, 'mast': HULL + '-mast'}
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
YJ = json.load(open(os.path.join(HERE, 'yards.json'), encoding='utf-8'))['main']
RP = json.load(open(os.path.join(HERE, 'rig_plan.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:160]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


def stamp(w, f):
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', f], text=True, encoding='utf-8')
    if r.returncode:
        sys.exit(1)


if 'holes' not in skip:
    f = os.path.join(HERE, 'masks', 'masts', 'thwart_hole.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    cli('op=carvevox', P, 'work=%s-deck-main' % HULL, 'voxels=' + f.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'draft=0', 'share=0')

if 'create' not in skip:
    cli('op=work', 'sub=create', P, 'id=%s-mast' % HULL, 'title=杉心號 桅（艙底起 5 m，可拆）', 'parent_work=' + HULL, 'size=140,101,100')
    cli('op=work', 'sub=update', P, 'work=%s-mast' % HULL, 'tags=sub', 'meters_per_voxel=0.1')
    cli('op=work', 'sub=create', P, 'id=%s-yard' % HULL, 'title=杉心號 拉丁帆桁（%.1f m）' % YJ['meta']['length_m'],
        'parent_work=' + HULL, 'size=%d,%d,%d' % tuple(YJ['size']))
    cli('op=work', 'sub=update', P, 'work=%s-yard' % HULL, 'tags=sub', 'meters_per_voxel=0.1')

if 'stamp' not in skip:
    stamp('%s-mast' % HULL, os.path.join(HERE, 'masks', 'masts', 'mast.vox.txt'))
    stamp('%s-yard' % HULL, os.path.join(HERE, 'masks', 'yards', 'yard.vox.txt'))

if 'yanchors' not in skip:
    for nm, at in YJ['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=%s-yard' % HULL, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=步驟 7 拉丁帆桁')

if 'models' not in skip:
    cli('op=work', 'sub=model', P, 'work=%s-mast' % HULL, 'name=yard', 'source_work=%s-yard' % HULL,
        'at=%g,%g,%g' % tuple(YJ['at']), 'pivot=%g,%g,%g' % tuple(YJ['pivot']), 'scale=1', 'rotate=0,0,0', 'overwrite=1',
        'meta=' + json.dumps(YJ['meta'], ensure_ascii=False), 'note=步驟 7 拉丁帆桁（掛在桅的左舷側）')

if 'links' not in skip:
    cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=桅', 'source_work=%s-mast' % HULL, 'at=0,0,0', 'overwrite=1', 'note=步驟 7')

if 'anchors' not in skip:
    for a in RP['anchors']:
        cli('op=work', 'sub=anchor', P, 'work=' + WORK[a['work']], 'name=' + a['name'], 'at=%d,%d,%d' % tuple(a['at']), 'overwrite=1', 'note=步驟 8 索具')

if 'sails' not in skip:
    for s in RP['sails']:
        args = ['op=work', 'sub=sail', P, 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(s['corners']), 'corner_names=' + '|'.join(s['corner_names']),
                'bind=' + ','.join(map(str, s['bind'])), 'free=' + ','.join(map(str, s['free'])), 'overwrite=1', 'note=步驟 8']
        if s.get('color'):
            args.append('color=' + s['color'])
        if s.get('fullness'):
            args.append('fullness=%g' % s['fullness'])
        cli(*args)

if 'ropes' not in skip:
    for r in RP['ropes']:
        cli('op=work', 'sub=rope', P, 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'slack=%g' % r['slack'],
            'thickness=%g' % r['thickness'], 'color=' + r['color'], 'group=' + r['group'], 'overwrite=1', 'note=步驟 8')

if 'meta' not in skip:
    f = os.path.join(HERE, 'rig_meta.tsv')
    rows = [('sail', s['name'], s['meta']) for s in RP['sails']] + [('rope', r['name'], r['meta']) for r in RP['ropes'] if r.get('meta')]
    with open(f, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(''.join('%s\t%s\t%s\n' % (a, b, json.dumps(c, ensure_ascii=False)) for a, b, c in rows))
    cli('op=work', 'sub=meta', P, 'work=' + ASM, 'file=' + f.replace('\\', '/'))
    cli('op=work', 'sub=wind', P, 'work=' + ASM, 'wind=4.5,-1.5,0', 'sail_seconds=3', ok=(0, 1, 2))
