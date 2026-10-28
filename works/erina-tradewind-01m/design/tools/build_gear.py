# 出處：erina-oxford-01m/design/tools/build_gear.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 步驟 10 落地：火藥庫子作品（牆＋固定點 blast／door）＋關聯（kind=magazine）、火藥桶（掛在火藥庫裡）、艙蓋／爐灶／絞盤（掛在炮甲板）
#   用法：python -I -X utf8 tools/build_gear.py <design>（先跑 draft_gear.py；模型 overwrite=1、子作品已存在不重貼）
#   結構照 tools/build_masts.py
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'erina-tradewind-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
G = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))
HOST = {'magazine': HULL + '-magazine', 'deck-gun': HULL + '-deck-gun'}


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


w = HOST['magazine']
path = os.path.join(design, 'masks', 'gear', 'magazine.vox.txt')
if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
    cli('op=work', 'sub=create', 'persona=erina', 'work=' + w, 'title=信風號 火藥庫（底艙平台後段）', 'parent_work=' + HULL, 'size=448,192,384', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=erina', 'work=' + w, 'meters_per_voxel=0.1')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=erina', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    got = int(re.search(r'placed\D{0,12}(\d[\d,]*)', out).group(1).replace(',', ''))
    if got != n:
        raise SystemExit('✗ placed %d ≠ %d' % (got, n))
    print('✓ 火藥庫 %d 格' % n)
for nm, at in G['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=erina', 'work=' + w, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=draft_gear.py')
cli('op=work', 'sub=link', 'persona=erina', 'work=' + ASM, 'name=彈藥庫', 'source_work=' + w, 'at=0,0,0',
    'meta=' + json.dumps(G['magazine_meta'], ensure_ascii=False), 'note=步驟 10：火藥庫', ok=(0, 2))
k = 0
for m in G['models']:
    sc = m['scale'] if isinstance(m['scale'], list) else [m['scale']] * 3
    cli('op=work', 'sub=model', 'persona=erina', 'work=' + HOST[m['host']], 'name=' + m['name'], 'source_work=' + m['source_work'],
        'pivot=%g,%g,%g' % tuple(m['pivot']), 'at=%g,%g,%g' % tuple(m['at']), 'rotate=0,0,0', 'scale=%g,%g,%g' % tuple(sc),
        'meta=' + json.dumps(m['meta'], ensure_ascii=False), 'overwrite=1', 'note=步驟 10（draft_gear.py）')
    k += 1
print('✓ 模型 %d' % k)
print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-8:]))
