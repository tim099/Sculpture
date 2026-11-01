# 出處：erina-tradewind-01m/design/tools/build_deco.py（TASK-1097 信風號；TASK-1151 抄來改成好旅號 caravela redonda）
# 出處：erina-oxford-01m/design/tools/build_deco.py（TASK-0972 牛津號；TASK-1097 抄來改成好旅號 brig）
# 好旅號 步驟 6 落地（TASK-1097）：船首（knee＋渦卷＋head rail）、錨架、船尾窗玻璃（material=glass）子作品＋組裝件關聯＋固定點
#   用法：python -I -X utf8 tools/build_deco.py <design>（先跑 draft_deco.py、draft_ports.py；子作品已存在 ⇒ 不重建、改格子走 delta_apply）
#   結構照 tools/build_masts.py
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'summit-boaviagem-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
PARTS = [
    ('head', HULL + '-head', '好旅號 船首（小 cutwater＋柱頭金色圓頭）', '船首', None, os.path.join('masks', 'deco', 'head.vox.txt')),
    ('catheads', HULL + '-catheads', '好旅號 錨架（cathead，兩舷）', '錨架', None, os.path.join('masks', 'deco', 'catheads.vox.txt')),
    ('glass', HULL + '-stern-glass', '好旅號 船尾窗玻璃（兩排 6 扇）', '船尾窗玻璃', {'material': 'glass'}, os.path.join('masks', 'ports', 'glass.vox.txt')),
]
ANC = json.load(open(os.path.join(design, 'deco_anchors.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


for key, w, title, link, meta, rel in PARTS:
    path = os.path.join(design, rel)
    if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
        cli('op=work', 'sub=create', 'persona=summit', 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=448,192,384', 'tags=sub')
        cli('op=work', 'sub=update', 'persona=summit', 'work=' + w, 'meters_per_voxel=0.1')
        n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
        out = cli('op=stampvox', 'persona=summit', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
        got = int(re.search(r'placed\D{0,12}(\d[\d,]*)', out).group(1).replace(',', ''))
        if got != n:
            raise SystemExit('✗ placed %d ≠ %d（%s）' % (got, n, w))
        print('✓ %s %d 格' % (w, n))
    for nm, at in ANC.get(key, {}).items():
        cli('op=work', 'sub=anchor', 'persona=summit', 'work=' + w, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=draft_deco.py')
    args = ['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=' + link, 'source_work=' + w, 'at=0,0,0', 'note=步驟 6（draft_deco.py）']
    if meta:
        args.append('meta=' + json.dumps(meta, ensure_ascii=False))
    cli(*args, ok=(0, 2))
print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-6:]))
