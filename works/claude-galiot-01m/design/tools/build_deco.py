# 蠍子號 步驟 6 落格（TASK-0023）：spur、艉台與燈桿、船尾篷三件子作品（船殼的框、0.1 m、parent 船殼、tags sub）⇒ stamp_lists ⇒
#   spur 掛組裝件、艉台掛甲板-main（同一層甲板）、篷是組裝件的外部模型 meta deco=1；船殼換色（天蠍座紋章）stampvox overwrite=1；甲板 meta 重標（floor 多了艉台）
#   出處：tools/build_decks.py（本船步驟 5，照越嶺號 build_upper.py）。
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
T = 'claude-galiot-01m'
ASM = T + '-assembly'
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
SIZE = ','.join(str(v) for v in PLAN['space']['hull'])
PARTS = [  # 清單, 子作品 id 尾巴, 名稱, 掛在哪件作品, 關聯名或模型名, 'link'／'model'
    ('spur', 'spur', '蠍子號 spur（sperone）', ASM, 'spur', 'link'),
    ('poop', 'poop', '蠍子號 艉台與燈桿', T + '-deck-main', '艉台', 'link'),
    ('awning', 'awning', '蠍子號 船尾篷（骨架與紅布）', ASM, '船尾篷', 'model'),
]


def cli(*args):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


for key, tail, title, host, name, how in PARTS:
    w = T + '-' + tail
    f = os.path.join(HERE, 'masks', 'deco', key + '.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    rc, out = cli('op=work', 'sub=show', 'work=' + w)
    if rc != 0:
        rc, out = cli('op=work', 'sub=create', P, 'id=' + w, 'title=' + title, 'size=' + SIZE, 'parent_work=' + T, 'tags=sub')
        assert rc == 0, out[-800:]
        rc, out = cli('op=work', 'sub=update', P, 'id=' + w, 'meters_per_voxel=0.1')
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
    if how == 'link':
        rc, out = cli('op=work', 'sub=link', P, 'work=' + host, 'name=' + name, 'source_work=' + w, 'at=0,0,0', 'overwrite=1', 'note=步驟 6（TASK-0023）')
    else:
        rc, out = cli('op=work', 'sub=model', P, 'work=' + host, 'name=' + name, 'source_work=' + w, 'at=0,0,0', 'pivot=0,0,0', 'scale=1', 'rotate=0,0,0',
                      'mirror=none', 'overwrite=1', 'meta={"deco":1}', 'note=步驟 6（TASK-0023）：裝飾，可隱藏（Ship_Fittings §9.9）')
    assert rc == 0, out[-800:]
    print('✓', host, '/', name, '←', w, n, how)

# 船殼換色：只在那幾格還不是新色時落（重跑不會重落）
f = os.path.join(HERE, 'masks', 'step6', 'hull_paint.vox.txt')
want = np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2)
work = wio.export_list(T, None)
cw = dict(zip(wio.key(work).tolist(), work[:, 3].tolist()))
todo = [r for r, k in zip(want.tolist(), wio.key(want).tolist()) if cw.get(k) != r[3]]
if todo:
    assert len(todo) == len(want), ('換色只落了一部分？', len(todo), len(want))
    rc, out = cli('op=stampvox', P, 'work=' + T, 'voxels=' + f, 'at=0,0,0', 'expect_pixels=%d' % len(want), 'overwrite=1', 'draft=0', 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    print('換色 stampvox exit=%d placed=%s／%d' % (rc, m.group(1) if m else None, len(want)))
    assert rc == 0, out[-1500:]
else:
    print('· 換色已經落過（%d 格都是新色）' % len(want))

f = os.path.join(HERE, 'decks_meta.tsv')
rc, out = cli('op=work', 'sub=meta', P, 'work=' + ASM, 'file=' + f)
assert rc == 0, out[-800:]
print('✓ 甲板 meta ←', os.path.basename(f))
