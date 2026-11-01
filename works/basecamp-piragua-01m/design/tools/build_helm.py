# 杉心號 步驟 11 落格（TASK-1152）：舵槳子作品（整船的框）＋固定點、組裝件裡的舵槳模型、甲板-main 裡的四爪錨模型、船殼的 hawse-S
#   用法：python -I -X utf8 tools/build_helm.py   （讀 helm_placement.json；draft_helm.py 產）
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
M = json.load(open(os.path.join(HERE, 'helm_placement.json'), encoding='utf-8'))
HULL, P = 'basecamp-piragua-01m', 'persona=basecamp'


def cli(*args):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    print('  exit=%d %s' % (r.returncode, next((l for l in out.splitlines() if l[:1] in '✓✗'), '')[:150]), flush=True)
    if r.returncode:
        print(out[-1200:])
        sys.exit(1)


W = M['steer_work']
cli('op=work', 'sub=create', P, 'id=' + W, 'title=杉心號 舵槳（右舷船尾側）', 'parent_work=' + HULL, 'size=140,101,100')
cli('op=work', 'sub=update', P, 'work=' + W, 'tags=sub', 'meters_per_voxel=0.1')
r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), W, '0', os.path.join(HERE, 'masks', 'steer', 'rudder.vox.txt')])
if r.returncode:
    sys.exit(1)
for nm, at in M['steer_anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + W, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=步驟 11 舵槳')
for nm, at in M['hull_anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + HULL, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=步驟 11 錨鏈孔')
for m in M['models']:
    cli('op=work', 'sub=model', P, 'work=' + m['host'], 'name=' + m['name'], 'source_work=' + m['work'], 'at=%g,%g,%g' % tuple(m['at']),
        'pivot=%g,%g,%g' % tuple(m['pivot']), 'scale=%g' % m['scale'], 'rotate=%g,%g,%g' % tuple(m['rotate']), 'overwrite=1',
        'meta=' + json.dumps(m['meta'], ensure_ascii=False), 'note=步驟 11')
