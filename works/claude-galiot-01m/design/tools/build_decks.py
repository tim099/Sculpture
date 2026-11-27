# 蠍子號 步驟 5 落格（TASK-0023）：每件一件子作品（船殼的框 420×241×90、0.1 m、parent 船殼、tags sub）⇒ stamp_lists ⇒ 關聯 at 0,0,0 ⇒ 甲板 meta
#   出處：kotoko-fusta-01m/design/tools/build_upper.py（越嶺號）。改：persona Claude-Ojousama、senate 用離線包裝、框照 plan.json、
#        船首低平台掛在甲板-main 底下（同一層，不另開甲板）、最後照 decks_meta.tsv 標組裝件的甲板 meta。
#   用法：python -I -X utf8 tools/build_decks.py
#   已經建過、已經有格的件不重落（讀回格數 ＝ 清單才算數，不等就停）。
import os, re, subprocess, sys, json

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENATE = os.environ.get('SENATE', '/paperclip/instances/default/projects/482d2c24-3be9-40fc-8ec9-1a7a02dd4f3f/1ea1d409-d2dd-45dc-b44e-35e83e49b833/_default/.work/senate/bin/senate')
P = 'persona=Claude-Ojousama'
T = 'claude-galiot-01m'
ASM = T + '-assembly'
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
SIZE = ','.join(str(v) for v in PLAN['space']['hull'])
PARTS = [  # 清單, 子作品 id 尾巴, 名稱, 掛在哪件作品, 關聯名
    ('deck_main', 'deck-main', '蠍子號 甲板（中央走道、划手座、腳踏、艙口格柵）', ASM, '甲板-main'),
    ('bow', 'bow', '蠍子號 船首低平台', T + '-deck-main', '船首平台'),
]


def cli(*args):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


for key, tail, title, host, link in PARTS:
    w = T + '-' + tail
    f = os.path.join(HERE, 'masks', 'decks', key + '.vox.txt')
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
    rc, out = cli('op=work', 'sub=link', P, 'work=' + host, 'name=' + link, 'source_work=' + w, 'at=0,0,0', 'overwrite=1', 'note=步驟 5（TASK-0023）')
    assert rc == 0, out[-800:]
    print('✓', host, '/', link, '←', w, n)

f = os.path.join(HERE, 'decks_meta.tsv')
rc, out = cli('op=work', 'sub=meta', P, 'work=' + ASM, 'file=' + f)
assert rc == 0, out[-800:]
print('✓ 甲板 meta ←', os.path.basename(f))
