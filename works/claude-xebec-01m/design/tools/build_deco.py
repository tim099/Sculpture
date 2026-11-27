# 利劍號 步驟 6 落格（TASK-0022）：長喙、船尾平台、窗玻璃、篷架四件子作品（船殼的框、0.1 m、parent 船殼、tags sub）⇒ stamp_lists ⇒
#   長喙、船尾平台掛組裝件（關聯）、窗玻璃掛組裝件（關聯 meta material=glass）、篷架是組裝件的外部模型 meta deco=1；船殼換色（彎刀船名）stampvox overwrite=1
#   出處：claude-galiot-01m/design/tools/build_deco.py（蠍子號）。改：件與名稱、窗玻璃的關聯 meta、框改讀組裝件那一格（篷架、平台超出船殼的框）。
#   用法：python -I -X utf8 tools/build_deco.py
#   已經建過、已經有格的件不重落（讀回格數 ＝ 清單才算數，不等就停）；換色只在船殼那幾格還不是新色的時候落。
import os, re, subprocess, sys, json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
SENATE = wio.SENATE
P = 'persona=Claude-Ojousama'
T = 'claude-xebec-01m'
ASM = T + '-assembly'
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
SIZE_HULL = ','.join(str(v) for v in PLAN['space']['hull'])
SIZE_ASM = ','.join(str(v) for v in PLAN['space']['assembly'])
PARTS = [  # 清單, 子作品 id 尾巴, 名稱, 框, 關聯名或模型名, 'link'／'model', meta
    ('beak', 'beak', '利劍號 長喙（éperon；不是撞角）', SIZE_HULL, '長喙', 'link', None),
    ('platform', 'stern-platform', '利劍號 船尾平台與欄杆', SIZE_HULL, '船尾平台', 'link', None),
    ('glass', 'window-glass', '利劍號 船尾艙窗玻璃', SIZE_HULL, '窗玻璃', 'link', {'material': 'glass'}),
    ('awning', 'awning', '利劍號 船尾篷架', SIZE_ASM, '船尾篷架', 'model', {'deco': 1}),
]


def cli(*args):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


WORKS = os.path.dirname(os.path.dirname(HERE))
for key, tail, title, size, name, how, meta in PARTS:
    w = T + '-' + tail
    f = os.path.join(HERE, 'masks', 'deco', key + '.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
        rc, out = cli('op=work', 'sub=create', P, 'work=' + w, 'title=' + title, 'size=' + size, 'parent_work=' + T, 'tags=sub')
        assert rc == 0, out[-800:]
        rc, out = cli('op=work', 'sub=update', P, 'work=' + w, 'meters_per_voxel=0.1')
        assert rc == 0, out[-800:]
        print('· 建了', w)
    rc, out = cli('op=stats', P, 'work=' + w)
    have = int(re.search(r'total_voxels = (\d+)', out).group(1))
    if have == 0:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', f], capture_output=True, text=True, encoding='utf-8')
        print(r.stdout.strip())
        if r.returncode:
            sys.exit(1)
    elif have != n:
        sys.exit('✗ %s 已有 %d 格 ≠ 清單 %d' % (w, have, n))
    m = ['meta=' + json.dumps(meta, separators=(',', ':'))] if meta else []
    if how == 'link':
        rc, out = cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=' + name, 'source_work=' + w, 'at=0,0,0', 'overwrite=1', 'note=步驟 6（TASK-0022）', *m)
    else:
        rc, out = cli('op=work', 'sub=model', P, 'work=' + ASM, 'name=' + name, 'source_work=' + w, 'at=0,0,0', 'pivot=0,0,0', 'scale=1', 'rotate=0,0,0',
                      'mirror=none', 'overwrite=1', *m, 'note=步驟 6（TASK-0022）：裝飾，可隱藏（Ship_Fittings §9.9）')
    assert rc == 0, out[-800:]
    print('✓', ASM, '/', name, '←', w, n, how, meta)

f = os.path.join(HERE, 'masks', 'step6', 'hull_paint.vox.txt')
want = np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2)
work = wio.export_list(T, None)
cw = dict(zip(wio.key(work).tolist(), work[:, 3].tolist()))
todo = [r for r, k in zip(want.tolist(), wio.key(want).tolist()) if cw.get(k) != r[3]]
if todo:
    # 只落顏色真的要換的那幾格（清單裡有的格原本就是黑 36）
    ft = os.path.join(HERE, 'masks', 'step6', 'hull_paint_todo.vox.txt')
    with open(ft, 'w', encoding='utf-8', newline='\n') as fo:
        fo.write('# 利劍號 船殼換色：hull_paint 裡顏色要換的那幾格（build_deco.py 產生）\n')
        fo.write('\n'.join('%d,%d,%d,%d' % tuple(r) for r in todo) + '\n')
    rc, out = cli('op=stampvox', P, 'work=' + T, 'voxels=' + ft, 'at=0,0,0', 'expect_pixels=%d' % len(todo), 'overwrite=1', 'draft=0', 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    print('換色 stampvox exit=%d placed=%s／%d（清單 %d 格，其中 %d 格原本就是新色）' % (rc, m.group(1) if m else None, len(todo), len(want), len(want) - len(todo)))
    assert rc == 0 and m and int(m.group(1).replace(',', '')) == len(todo), out[-1500:]
else:
    print('· 換色已經落過（%d 格都是新色）' % len(want))
