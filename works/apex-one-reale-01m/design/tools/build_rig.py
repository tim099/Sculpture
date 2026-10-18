# 階段三落格（TASK-0701）：甲板桅孔、桅子作品、三角帆桁子作品＋固定點、帆桁模型（放在桅子作品裡）、組裝件關聯、固定點、繩、帆、meta
#   用法：python -I -X utf8 tools/build_rig.py [--skip=<步驟,…>]   步驟：holes create stamp yanchors models links anchors sails ropes meta（繩的端點會指到帆角 ⇒ 帆先掛）
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'apex-one-reale-01m'
ASM = HULL + '-assembly'
P = 'persona=apex-one'
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
YJ = json.load(open(os.path.join(HERE, 'yards.json'), encoding='utf-8'))
RP = json.load(open(os.path.join(HERE, 'rig_plan.json'), encoding='utf-8'))
NAMES = {'main': '主桅', 'fore': '前桅'}


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
    f = os.path.join(HERE, 'masks', 'masts', 'deck_holes.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    cli('op=work', 'sub=mark', P, 'work=%s-deck-main' % HULL, 'name=桅孔', 'phase=begin')
    cli('op=carvevox', P, 'work=%s-deck-main' % HULL, 'voxels=' + f.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'draft=0', 'share=0')
    cli('op=work', 'sub=mark', P, 'work=%s-deck-main' % HULL, 'name=桅孔', 'phase=end')

if 'create' not in skip:
    for k in ('main', 'fore'):
        cli('op=work', 'sub=create', P, 'id=%s-mast-%s' % (HULL, k), 'title=皇家號 %s（arbre de %s）' % (NAMES[k], 'mestre' if k == 'main' else 'trinquet'),
            'parent_work=' + HULL, 'size=720,321,460', 'tags=sub')
        cli('op=work', 'sub=update', P, 'work=%s-mast-%s' % (HULL, k), 'meters_per_voxel=0.1')
        y = YJ[k]
        cli('op=work', 'sub=create', P, 'id=%s-yard-%s' % (HULL, k), 'title=皇家號 %s三角帆桁（antenne，%.1f m）' % (NAMES[k], y['meta']['length_m']),
            'parent_work=' + HULL, 'size=%d,%d,%d' % tuple(y['size']), 'tags=sub')
        cli('op=work', 'sub=update', P, 'work=%s-yard-%s' % (HULL, k), 'meters_per_voxel=0.1')

if 'stamp' not in skip:
    for k in ('main', 'fore'):
        stamp('%s-mast-%s' % (HULL, k), os.path.join(HERE, 'masks', 'masts', k + '.vox.txt'))
        stamp('%s-yard-%s' % (HULL, k), os.path.join(HERE, 'masks', 'yards', k + '.vox.txt'))

if 'yanchors' not in skip:
    for k in ('main', 'fore'):
        for nm, at in YJ[k]['anchors'].items():
            cli('op=work', 'sub=anchor', P, 'work=%s-yard-%s' % (HULL, k), 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'note=階段三 三角帆桁')

if 'models' not in skip:
    for k in ('main', 'fore'):
        y = YJ[k]
        cli('op=work', 'sub=model', P, 'work=%s-mast-%s' % (HULL, k), 'name=yard-' + k, 'source_work=%s-yard-%s' % (HULL, k),
            'at=%g,%g,%g' % tuple(y['at']), 'pivot=%g,%g,%g' % tuple(y['pivot']), 'scale=1', 'rotate=0,0,0', 'meta=' + json.dumps(y['meta'], ensure_ascii=False),
            'note=階段三 三角帆桁（掛在桅的左舷側）')

if 'links' not in skip:
    for k in ('main', 'fore'):
        cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=' + NAMES[k], 'source_work=%s-mast-%s' % (HULL, k), 'at=0,0,0', 'note=階段三')

if 'anchors' not in skip:
    for a in RP['anchors']:
        cli('op=work', 'sub=anchor', P, 'work=%s-%s' % (HULL, a['work']), 'name=' + a['name'], 'at=%d,%d,%d' % tuple(a['at']), 'note=階段三 索具')

if 'sails' not in skip:
    for s in RP['sails']:
        args = ['op=work', 'sub=sail', P, 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(s['corners']), 'corner_names=' + '|'.join(s['corner_names']),
                'bind=' + ','.join(map(str, s['bind'])), 'free=' + ','.join(map(str, s['free'])), 'note=階段三']
        if s.get('color'):
            args.append('color=' + s['color'])
        if s.get('fullness'):
            args.append('fullness=%g' % s['fullness'])
        if s.get('texture'):
            args.append('texture=' + os.path.join(HERE, s['texture']).replace('\\', '/'))
        cli(*args)

if 'ropes' not in skip:
    for r in RP['ropes']:
        cli('op=work', 'sub=rope', P, 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'slack=%g' % r['slack'],
            'thickness=%g' % r['thickness'], 'color=' + r['color'], 'group=' + r['group'], 'overwrite=1', 'note=階段三')

if 'meta' not in skip:
    f = os.path.join(HERE, 'rig_meta.tsv')
    rows = [('sail', s['name'], s['meta']) for s in RP['sails']] + [('rope', r['name'], r['meta']) for r in RP['ropes'] if r.get('meta')]
    with open(f, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(''.join('%s\t%s\t%s\n' % (a, b, json.dumps(c, ensure_ascii=False)) for a, b, c in rows))
    cli('op=work', 'sub=meta', P, 'work=' + ASM, 'file=' + f.replace('\\', '/'))
