# 越嶺號 階段二落格（TASK-0759）：每件一件子作品（整船的框 360×161×80、0.1 m、parent 船殼、tags sub）⇒ stamp_lists ⇒ 組裝件關聯 at 0,0,0
#   用法：python -I -X utf8 tools/build_upper.py
#   已經建過、已經有格的件不重落（讀回格數 ＝ 清單才算數，不等就停）。
import os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = 'kotoko-fusta-01m'
PARTS = [  # 清單, 子作品 id 尾巴, 名稱, 關聯名
    ('deck', 'deck-main', '越嶺號 甲板（中央走道、划手座、腳踏）', '甲板-main'),
    ('apostis', 'apostis', '越嶺號 舷外槳架（縱樑、橫樑、托樑、槳栓）', '舷外槳架'),
    ('bow', 'bow', '越嶺號 船首平台（胸牆、盾）', '甲板-bow'),
    ('spur', 'spur', '越嶺號 衝角 sperone', '衝角'),
    ('stern', 'stern', '越嶺號 船尾篷（木拱、紅布）與盾', '船尾篷'),
]


def cli(args):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


for key, tail, title, link in PARTS:
    w = T + '-' + tail
    f = os.path.join(HERE, 'masks', 'upper', key + '.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    rc, out = cli(['op=work', 'sub=show', 'work=' + w])
    if rc != 0:
        rc, out = cli(['op=work', 'sub=create', 'persona=kotoko', 'id=' + w, 'title=' + title, 'size=360,161,80', 'parent_work=' + T, 'tags=sub'])
        assert rc == 0, out[-800:]
        rc, out = cli(['op=work', 'sub=update', 'persona=kotoko', 'work=' + w, 'meters_per_voxel=0.1'])
        assert rc == 0, out[-800:]
    rc, out = cli(['op=stats', 'work=' + w])
    have = int(re.search(r'total_voxels = (\d+)', out).group(1))
    if have == 0:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), w, '0', f], capture_output=True, text=True, encoding='utf-8')
        print(r.stdout.strip())
        if r.returncode:
            sys.exit(1)
    elif have != n:
        sys.exit('✗ %s 已有 %d 格 ≠ 清單 %d' % (w, have, n))
    rc, out = cli(['op=work', 'sub=link', 'persona=kotoko', 'work=' + T + '-assembly', 'name=' + link, 'source_work=' + w, 'at=0,0,0', 'overwrite=1'])
    assert rc == 0, out[-800:]
    print('✓', link, w, n)
