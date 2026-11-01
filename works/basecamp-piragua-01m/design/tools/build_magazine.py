# 杉心號 步驟 10 落格（TASK-1152）：彈藥庫子作品、墊板、火藥桶模型、固定點 blast／door、組裝件關聯「彈藥庫」＋meta
#   用法：python -I -X utf8 tools/build_magazine.py   （讀 magazine_placement.json；draft_magazine.py 產）
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
M = json.load(open(os.path.join(HERE, 'magazine_placement.json'), encoding='utf-8'))
HULL, P = 'basecamp-piragua-01m', 'persona=basecamp'


def cli(*args):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    print('  exit=%d %s' % (r.returncode, next((l for l in out.splitlines() if l[:1] in '✓✗'), '')[:150]), flush=True)
    if r.returncode:
        print(out[-1200:])
        sys.exit(1)


cli('op=work', 'sub=create', P, 'id=' + M['host'], 'title=杉心號 彈藥庫（舵手腳前的墊板＋火藥桶）', 'parent_work=' + HULL, 'size=140,101,40')
cli('op=work', 'sub=update', P, 'work=' + M['host'], 'tags=sub', 'meters_per_voxel=0.1')
r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), M['host'], '0', os.path.join(HERE, 'masks', 'magazine', 'board.vox.txt')])
if r.returncode:
    sys.exit(1)
for nm, at in M['anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + M['host'], 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=步驟 10 彈藥庫')
for m in M['models']:
    cli('op=work', 'sub=model', P, 'work=' + M['host'], 'name=' + m['name'], 'source_work=' + m['work'], 'at=%g,%g,%g' % tuple(m['at']),
        'pivot=%g,%g,%g' % tuple(m['pivot']), 'scale=%g' % m['scale'], 'rotate=%g,%g,%g' % tuple(m['rotate']), 'overwrite=1',
        'meta=' + json.dumps(m['meta'], ensure_ascii=False), 'note=步驟 10 火藥桶（引用憲法號的桶）')
cli('op=work', 'sub=link', P, 'work=' + HULL + '-assembly', 'name=' + M['link'], 'source_work=' + M['host'], 'at=0,0,0', 'overwrite=1', 'note=步驟 10')
f = os.path.join(HERE, 'magazine_meta.tsv')
with open(f, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('link\t%s\t%s\n' % (M['link'], json.dumps(M['link_meta'], ensure_ascii=False)))
cli('op=work', 'sub=meta', P, 'work=' + HULL + '-assembly', 'file=' + f.replace('\\', '/'))
