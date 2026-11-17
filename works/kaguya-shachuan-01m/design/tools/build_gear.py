# 出處：kaguya-guineaman-01m/design/tools/build_gear.py
# 沙船 步驟 10 落地（TASK-1313）：彈藥庫子作品＋關聯（kind=magazine）、火藥桶 ×4、
#   主艙口格柵（0.05 m）、舵艙門、爐灶、小艇、絞盤、羅經櫃、尾燈
#   用法：python -I -X utf8 tools/build_gear.py <design>
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'kaguya-shachuan-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
G = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))
HOST = {'magazine': HULL + '-magazine', 'deck-main': HULL + '-deck-main', 'deck-poop': HULL + '-deck-poop'}


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
    cli('op=work', 'sub=create', 'persona=kaguya', 'work=' + w, 'title=沙船 彈藥庫（底艙艉端）', 'parent_work=' + HULL, 'size=288,192,288', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=kaguya', 'work=' + w, 'meters_per_voxel=0.1')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=kaguya', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    got = int(re.search(r'placed\D{0,12}(\d[\d,]*)', out).group(1).replace(',', ''))
    if got != n:
        raise SystemExit('✗ placed %d ≠ %d' % (got, n))
    print('✓ 彈藥庫 %d 格' % n)
for nm, at in G['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + w, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=draft_gear.py')
cli('op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=彈藥庫', 'source_work=' + w, 'at=0,0,0',
    'meta=' + json.dumps(G['magazine_meta'], ensure_ascii=False), 'note=步驟 10：彈藥庫', ok=(0, 2))

for g in G.get('gratings', []):
    w = g['work']
    if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
        cli('op=work', 'sub=create', 'persona=kaguya', 'work=' + w, 'title=' + g['title'], 'parent_work=' + HULL, 'size=%d,%d,%d' % tuple(g['size']), 'tags=sub')
        cli('op=work', 'sub=update', 'persona=kaguya', 'work=' + w, 'meters_per_voxel=0.05')
        path = os.path.join(design, g['file'])
        out = cli('op=stampvox', 'persona=kaguya', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % g['cells'], 'share=0')
        got = int(re.search(r'placed\D{0,12}(\d[\d,]*)', out).group(1).replace(',', ''))
        if got != g['cells']:
            raise SystemExit('✗ %s placed %d ≠ %d' % (g['name'], got, g['cells']))
        print('✓ %s %d 格' % (g['name'], got))
    cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + HOST[g['host']], 'name=' + g['name'], 'source_work=' + w,
        'pivot=0,0,0', 'at=%g,%g,%g' % tuple(g['at']), 'rotate=0,0,0', 'scale=%g,%g,%g' % ((g['scale'],) * 3),
        'meta=' + json.dumps(g['meta'], ensure_ascii=False), 'overwrite=1', 'note=步驟 10（draft_gear.py）')

k = 0
for m in G['models']:
    sc = m['scale'] if isinstance(m['scale'], list) else [m['scale']] * 3
    cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + HOST[m['host']], 'name=' + m['name'], 'source_work=' + m['source_work'],
        'pivot=%g,%g,%g' % tuple(m['pivot']), 'at=%g,%g,%g' % tuple(m['at']), 'rotate=0,0,0', 'scale=%g,%g,%g' % tuple(sc),
        'meta=' + json.dumps(m['meta'], ensure_ascii=False), 'overwrite=1', 'note=步驟 10（draft_gear.py）')
    k += 1
print('✓ 模型 %d' % k)
print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-8:]))
