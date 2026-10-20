# 階段三落格（TASK-0754）：桅子作品、上下帆桁子作品＋固定點、帆桁模型（放在桅子作品裡）、組裝件關聯、繩端固定點、帆、繩、meta
#   用法：python -I -X utf8 tools/build_rig.py [--skip=<步驟,…>]   步驟：create stamp yanchors models links anchors sails ropes meta（繩的端點會指到帆桁模型 ⇒ 模型先掛）
#   · 照抄皇家號 tools/build_rig.py 的流程；帆兩條邊（頂、腳）都綁在帆桁模型上。
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'apex-one-punt-01m'
ASM = HULL + '-assembly'
P = 'persona=apex-one'
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
RP = json.load(open(os.path.join(HERE, 'rig_plan.json'), encoding='utf-8'))
NAMES = {'upper': '上帆桁', 'lower': '下帆桁'}


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


def stamp(w, f):
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', f], text=True, encoding='utf-8')
    if r.returncode:
        sys.exit(1)


if 'create' not in skip:
    cli('op=work', 'sub=create', P, 'id=%s-mast' % HULL, 'title=蓬特號 桅（單桅，桅頂兩排導索孔）', 'parent_work=' + HULL, 'size=280,201,140', 'tags=sub')
    cli('op=work', 'sub=update', P, 'work=%s-mast' % HULL, 'meters_per_voxel=0.1')
    for k in ('upper', 'lower'):
        y = RP['yards'][k]
        cli('op=work', 'sub=create', P, 'id=%s-yard-%s' % (HULL, k), 'title=蓬特號 %s（%.1f m）' % (NAMES[k], y['meta']['length_m']),
            'parent_work=' + HULL, 'size=%d,%d,%d' % tuple(y['size']), 'tags=sub')
        cli('op=work', 'sub=update', P, 'work=%s-yard-%s' % (HULL, k), 'meters_per_voxel=0.1')

if 'stamp' not in skip:
    stamp('%s-mast' % HULL, os.path.join(HERE, 'masks', 'rig', 'mast.vox.txt'))
    for k in ('upper', 'lower'):
        stamp('%s-yard-%s' % (HULL, k), os.path.join(HERE, 'masks', 'rig', 'yard_%s.vox.txt' % k))

if 'yanchors' not in skip:
    for k in ('upper', 'lower'):
        for nm, at in RP['yards'][k]['anchors'].items():
            cli('op=work', 'sub=anchor', P, 'work=%s-yard-%s' % (HULL, k), 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'note=階段三 帆桁')

if 'models' not in skip:
    for k in ('upper', 'lower'):
        y = RP['yards'][k]
        cli('op=work', 'sub=model', P, 'work=%s-mast' % HULL, 'name=yard-' + k, 'source_work=%s-yard-%s' % (HULL, k),
            'at=%g,%g,%g' % tuple(y['at']), 'pivot=%g,%g,%g' % tuple(y['pivot']), 'scale=1', 'rotate=0,0,0', 'meta=' + json.dumps(y['meta'], ensure_ascii=False),
            'note=階段三 %s（掛在桅的前面）' % NAMES[k])

if 'links' not in skip:
    cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=桅', 'source_work=%s-mast' % HULL, 'at=0,0,0', 'note=階段三')

if 'anchors' not in skip:
    for a in RP['anchors']:
        w = HULL if a['work'] == 'hull' else '%s-%s' % (HULL, a['work'])
        cli('op=work', 'sub=anchor', P, 'work=' + w, 'name=' + a['name'], 'at=%d,%d,%d' % tuple(a['at']), 'note=階段三 索具')

if 'sails' not in skip:
    for s in RP['sails']:
        args = ['op=work', 'sub=sail', P, 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(s['corners']), 'corner_names=' + '|'.join(s['corner_names']),
                'bind=' + ','.join(map(str, s['bind'])), 'note=階段三：頂綁上帆桁、腳綁下帆桁']
        if s.get('free'):
            args.append('free=' + ','.join(map(str, s['free'])))
        if s.get('color'):
            args.append('color=' + s['color'])
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
