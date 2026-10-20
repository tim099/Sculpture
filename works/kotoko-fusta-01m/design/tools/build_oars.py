# 越嶺號 階段六落格（TASK-0763）：兩件槳元件（新通用部件 0.05 m；建作品、落格、固定點 pivot／blade／seat）⇒ 72 個槳模型掛在舷外槳架
#   用法：python -I -X utf8 tools/build_oars.py
import os, sys, json, re, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
P = 'persona=kotoko'
PL = json.load(open(os.path.join(HERE, 'oars_placement.json'), encoding='utf-8'))
TITLE = {'inner': '槳（fusta alla sensile 靠走道那位，7.2 m、舷內 2.4 m、1 人划；通用部件，0.05 m）',
         'outer': '槳（fusta alla sensile 靠舷那位，6.6 m、舷內 1.8 m、1 人划；通用部件，0.05 m）'}
NOTE = {'pivot': '槳柄靠在縱樑上的那一點（轉的中心、推力作用點、掛點）', 'blade': '槳葉末端', 'seat': '槳手站的那一格（座板頂上一格；右舷那幾支的中位數）'}


def cli(*args, ok=(0,), quiet=False):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if not quiet or r.returncode not in ok:
        line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
        print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


for kind, c in PL['components'].items():
    W = c['work']
    if subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=show', '--arg', 'work=' + W], capture_output=True).returncode:
        cli('op=work', 'sub=create', P, 'id=' + W, 'title=' + TITLE[kind], 'parent_work=kotoko-fusta-01m', 'size=%d,%d,%d' % tuple(c['size']), 'tags=sub')
        cli('op=work', 'sub=update', P, 'work=' + W, 'meters_per_voxel=0.05')
    have = int(re.search(r'total_voxels = (\d+)', cli('op=stats', 'work=' + W, quiet=True)).group(1))
    if have == 0:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), W, '0', os.path.join(HERE, 'masks', 'oars', kind + '.vox.txt')], text=True, encoding='utf-8')
        if r.returncode:
            sys.exit(1)
    elif have != c['cells']:
        sys.exit('✗ %s 已有 %d 格 ≠ %d' % (W, have, c['cells']))
    for nm, at in c['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + W, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE[nm])

n = 0
for r in PL['rows']:
    cli('op=work', 'sub=model', P, 'work=' + PL['host_work'], 'name=' + r['name'], 'source_work=' + PL['components'][r['kind']]['work'],
        'at=%g,%g,%g' % tuple(r['at']), 'pivot=%g,%g,%g' % tuple(r['pivot']), 'rotate=0,0,0', 'scale=0.5', 'mirror=' + r['mirror'], 'overwrite=1',
        'meta=' + json.dumps(r['meta'], ensure_ascii=False), 'note=階段六 槳（draft_oars.py）', quiet=True)
    n += 1
print('✓ 槳模型', n)
