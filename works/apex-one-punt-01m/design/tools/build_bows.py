# 階段五落格（TASK-0754）：弓元件（通用部件）＋固定點、四把弓（模型掛在艏艉平台作品裡）、弓弦、箭庫子作品＋固定點＋關聯（meta kind=magazine）、弩箭箱模型
#   用法：python -I -X utf8 tools/build_bows.py [--skip=<步驟,…>]   步驟：part bows ropes magazine
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'apex-one-punt-01m'
ASM = HULL + '-assembly'
BOW = HULL + '-gun-bow'
MAG = HULL + '-magazine'
P = 'persona=apex-one'
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
BP = json.load(open(os.path.join(HERE, 'bow_part.json'), encoding='utf-8'))
PL = json.load(open(os.path.join(HERE, 'bows_placement.json'), encoding='utf-8'))


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


if 'part' not in skip:
    cli('op=work', 'sub=create', P, 'id=' + BOW, 'title=弓（bow，新王國角形複合弓＋弓架、搭在弦上的箭；換皮大砲，通用部件，0.05 m）', 'parent_work=' + HULL,
        'size=%d,%d,%d' % tuple(BP['size']), 'tags=sub')
    cli('op=work', 'sub=update', P, 'work=' + BOW, 'meters_per_voxel=0.05')
    stamp(BOW, os.path.join(HERE, 'masks', 'bow', 'bow.vox.txt'))
    for nm, at in BP['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + BOW, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'note=弓元件')

if 'bows' not in skip:
    for b in PL['bows']:
        cli('op=work', 'sub=model', P, 'work=%s-%s' % (HULL, b['work']), 'name=' + b['name'], 'source_work=' + BOW,
            'at=%g,%g,%g' % tuple(b['at']), 'pivot=%g,%g,%g' % tuple(b['pivot']), 'scale=%g' % b['scale'], 'rotate=%g,%g,%g' % tuple(b['rotate']),
            'meta=' + json.dumps(b['meta'], ensure_ascii=False), 'note=階段五 弓手（迴旋 0／±45°）')

if 'ropes' not in skip:
    for r in PL['ropes']:
        cli('op=work', 'sub=rope', P, 'work=%s-%s' % (HULL, r['work']), 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'slack=%g' % r['slack'],
            'thickness=%g' % r['thickness'], 'color=' + r['color'], 'meta=' + json.dumps(r['meta'], ensure_ascii=False), 'overwrite=1', 'note=階段五 弓弦')

if 'magazine' not in skip:
    M = PL['magazine']
    cli('op=work', 'sub=create', P, 'id=' + MAG, 'title=蓬特號 箭庫（貨艙梯腳旁的板）', 'parent_work=' + HULL, 'size=280,201,140', 'tags=sub')
    cli('op=work', 'sub=update', P, 'work=' + MAG, 'meters_per_voxel=0.1')
    stamp(MAG, os.path.join(HERE, 'masks', 'bow', 'magazine.vox.txt'))
    for nm, at in M['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + MAG, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'note=階段五 箭庫')
    for b in M['boxes']:
        cli('op=work', 'sub=model', P, 'work=' + MAG, 'name=' + b['name'], 'source_work=erina-dromon-01m-store-boltbox',
            'at=%g,%g,%g' % tuple(b['at']), 'pivot=%g,%g,%g' % tuple(b['pivot']), 'scale=%g' % b['scale'], 'rotate=0,0,0',
            'meta=' + json.dumps(b['meta'], ensure_ascii=False), 'note=階段五 弩箭箱（當箭箱，store=bolt）')
    cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=箭庫', 'source_work=' + MAG, 'at=0,0,0', 'meta=' + json.dumps(M['meta'], ensure_ascii=False), 'note=階段五')
