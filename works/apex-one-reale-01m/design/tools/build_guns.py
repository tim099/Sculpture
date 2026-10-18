# 階段四落格（TASK-0702）：迴旋砲元件（子作品＋固定點）、19 門砲的外部模型（掛在所在那一層的子作品裡）
#   用法：python -I -X utf8 tools/build_guns.py [--skip=<步驟,…>]   步驟：comp models
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'apex-one-reale-01m'
P = 'persona=apex-one'
HOST = {'甲板-main': 'deck-main', '舷外槳架': 'apostis', '甲板-rambade': 'rambade'}
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
V = json.load(open(os.path.join(HERE, 'verify_guns.json'), encoding='utf-8'))
GP = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))['guns']


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


if 'comp' not in skip:
    w = HULL + '-gun-pierrier'
    cli('op=work', 'sub=create', P, 'id=' + w, 'title=皇家號 迴旋砲 pierrier（叉架上的後膛砲，0.05 m；外部模型的來源）', 'parent_work=' + HULL,
        'size=%d,%d,%d' % tuple(V['pierrier']['size']), 'tags=sub')
    cli('op=work', 'sub=update', P, 'work=' + w, 'meters_per_voxel=0.05')
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', os.path.join(HERE, 'masks', 'guns', 'pierrier.vox.txt')],
                       text=True, encoding='utf-8')
    if r.returncode:
        sys.exit(1)
    notes = {'muzzle': '砲口內膛那一格（空格）', 'breech': '砲尾（藥室）', 'cascabel': '尾巴的把手', 'pivot': '叉架插銷的底：轉的中心、站在欄杆上的那一點'}
    for nm, at in V['pierrier']['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + w, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'note=' + notes[nm])

if 'models' not in skip:
    for g in GP:
        cli('op=work', 'sub=model', P, 'work=%s-%s' % (HULL, HOST[g['host']]), 'name=' + g['name'], 'source_work=' + g['source'],
            'at=%g,%g,%g' % tuple(g['at']), 'pivot=%g,%g,%g' % tuple(g['pivot']), 'scale=%g' % g['scale'], 'rotate=%g,%g,%g' % tuple(g['rotate']),
            'meta=' + json.dumps(g['meta'], ensure_ascii=False), 'note=階段四（draft_guns.py）')
