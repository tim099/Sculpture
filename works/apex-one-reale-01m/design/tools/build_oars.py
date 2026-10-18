# 階段六落格（TASK-0705）：槳元件（通用部件，子作品＋固定點）、64 支槳的外部模型（掛在舷外槳架子作品裡；左舷 mirror=y）
#   用法：python -I -X utf8 tools/build_oars.py [--skip=comp,models]
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'apex-one-reale-01m'
P = 'persona=apex-one'
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
V = json.load(open(os.path.join(HERE, 'verify_oars.json'), encoding='utf-8'))
PL = json.load(open(os.path.join(HERE, 'oars_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,), quiet=False):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    if not quiet or r.returncode not in ok:
        print('  exit=%d %s' % (r.returncode, line[:150]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


if 'comp' not in skip:
    w = PL['work']
    cli('op=work', 'sub=create', P, 'id=' + w, 'title=槳（galère，13 m、7 人划；通用部件，0.05 m）', 'parent_work=' + HULL,
        'size=%d,%d,%d' % tuple(V['component']['size']), 'tags=sub')
    cli('op=work', 'sub=update', P, 'work=' + w, 'meters_per_voxel=0.05')
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', os.path.join(HERE, 'masks', 'oars', 'oar.vox.txt')],
                       text=True, encoding='utf-8')
    if r.returncode:
        sys.exit(1)
    notes = {'pivot': '槳座：槳靠在舷緣（槳架）的那一點 ＝ 划槳轉的中心、推力作用點、掛點', 'blade': '槳葉末端',
             'seat': '第一個槳手坐的那一格（划手座頂上一格；其他人沿槳柄每 0.6 m 往船裡）'}
    for nm, at in V['component']['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + w, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'note=' + notes[nm])

if 'models' not in skip:
    for o in PL['oars']:
        args = ['op=work', 'sub=model', P, 'work=%s-apostis' % HULL, 'name=' + o['name'], 'source_work=' + PL['work'], 'at=%g,%g,%g' % tuple(o['at']),
                'pivot=%g,%g,%g' % tuple(PL['pivot']), 'scale=%g' % PL['scale'], 'meta=' + json.dumps(o['meta'], ensure_ascii=False), 'note=階段六 槳（draft_oars.py）']
        if o['mirror']:
            args.append('mirror=' + o['mirror'])
        cli(*args, quiet=True)
    print('  models: %d' % len(PL['oars']))
