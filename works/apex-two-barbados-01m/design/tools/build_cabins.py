# 出處：本作品 tools/build_gear.py（火藥庫子作品＋關聯那一段）；巴貝多商人號 空艙房落地（TASK-1147；Tim 2026-11-02「Build cabins」）
#   艙房子作品（艙壁、門框、平地板；世界座標 at 0,0,0）＋固定點 <房名>.min／.max／.door ⇒ 上甲板子作品裡的關聯「艙房」（meta kind=rooms）
#   用法：python -I -X utf8 tools/build_cabins.py <design>（先跑 draft_cabins.py；子作品已存在 ⇒ 不重貼，改了清單走 tools/delta_apply.py）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'apex-two-barbados-01m'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
G = json.load(open(os.path.join(design, 'cabins_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


w = G['work']
path = os.path.join(design, G['mask'])
if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
    cli('op=work', 'sub=create', 'persona=apex-two', 'work=' + w, 'title=' + G['title'], 'parent_work=' + HULL, 'size=480,192,384', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=apex-two', 'work=' + w, 'meters_per_voxel=0.1')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=apex-two', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    got = int(re.search(r'placed\D{0,12}(\d[\d,]*)', out).group(1).replace(',', ''))
    if got != n:
        raise SystemExit('✗ placed %d ≠ %d' % (got, n))
    print('✓ 艙房 %d 格' % n)
for nm, at in G['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=apex-two', 'work=' + w, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=draft_cabins.py')
print('✓ 固定點 %d' % len(G['anchors']))
cli('op=work', 'sub=link', 'persona=apex-two', 'work=' + G['host'], 'name=' + G['link'], 'source_work=' + w, 'at=0,0,0',
    'meta=' + json.dumps(G['meta'], ensure_ascii=False), 'note=艙房（draft_cabins.py）', ok=(0, 2))
print('\n'.join(cli('op=work', 'sub=links', 'work=' + G['host']).splitlines()[-6:]))
