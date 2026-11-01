# 杉心號 步驟 13 落格（TASK-1152）：槳元件子作品（0.05 m）＋固定點 pivot／blade／seat、船殼上 14 支槳模型
#   用法：python -I -X utf8 tools/build_oars.py [--skip=create]   （讀 oars_placement.json；draft_oars.py 產）
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
M = json.load(open(os.path.join(HERE, 'oars_placement.json'), encoding='utf-8'))
HULL, P = 'basecamp-piragua-01m', 'persona=basecamp'
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))


def cli(*args):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    print('  exit=%d %s' % (r.returncode, next((l for l in out.splitlines() if l[:1] in '✓✗'), '')[:150]), flush=True)
    if r.returncode:
        print(out[-1200:])
        sys.exit(1)


W = M['component']
if 'create' not in skip:
    cli('op=work', 'sub=create', P, 'id=' + W, 'title=杉心號 槳（3.4 m、1 人划；通用部件，0.05 m）', 'parent_work=' + HULL, 'size=%d,%d,%d' % tuple(M['size']))
    cli('op=work', 'sub=update', P, 'work=' + W, 'tags=sub', 'meters_per_voxel=0.05')
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), W, '0', os.path.join(HERE, 'masks', 'oar', 'oar.vox.txt')])
    if r.returncode:
        sys.exit(1)
    for nm, at in M['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + W, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=步驟 13 槳')
for m in M['models']:
    args = ['op=work', 'sub=model', P, 'work=' + M['host'], 'name=' + m['name'], 'source_work=' + W, 'at=%g,%g,%g' % tuple(m['at']),
            'pivot=%g,%g,%g' % tuple(m['pivot']), 'scale=%g' % m['scale'], 'rotate=%g,%g,%g' % tuple(m['rotate']), 'overwrite=1',
            'meta=' + json.dumps(m['meta'], ensure_ascii=False), 'note=步驟 13 槳（靠在舷頂，繩環）']
    if m['mirror']:
        args.append('mirror=' + m['mirror'])
    cli(*args)
