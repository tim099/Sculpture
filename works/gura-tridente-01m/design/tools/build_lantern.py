# 階段五落格：船尾燈子作品（0.05 m）、固定點、組裝件上兩盞模型（meta kind=light）—— 照 lantern_placement.json
#   用法：python -I -X utf8 tools/build_lantern.py <design>
#   · 子作品已存在而且格數 ＝ 清單 ⇒ 不重貼；模型已存在 ⇒ 先 unmodel 再放（at／pivot／scale 以 placement 為準）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'gura-tridente-01m'
ASM = HULL + '-assembly'
WORK = HULL + '-lantern'


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return r.returncode, out


pl = json.load(open(os.path.join(design, 'lantern_placement.json'), encoding='utf-8'))
L = pl['lantern']
path = os.path.join(design, 'masks', 'lantern', 'lantern.vox.txt')
n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(design))), WORK, 'work.json')):
    cli('op=work', 'sub=create', 'persona=gura', 'id=' + WORK, 'title=三叉戟號 船尾燈（0.05 m／格）', 'parent_work=' + HULL,
        'size=' + ','.join(str(v) for v in L['size']), 'tags=sub')
    cli('op=work', 'sub=update', 'persona=gura', 'work=' + WORK, 'meters_per_voxel=%g' % L['meters_per_voxel'])
    print('✓ 建立', WORK)
_, out = cli('op=stats', 'work=' + WORK, 'links=none')
have = int(re.search(r'🔢 total_voxels = (\d+)', out).group(1))
if have == 0:
    _, out = cli('op=stampvox', 'persona=gura', 'work=' + WORK, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    print('  stampvox %d' % n)
elif have != n:
    raise SystemExit('✗ %s 已有 %d 格 ≠ 清單 %d' % (WORK, have, n))
NOTE = {'base': '腳底（站在 taffrail 上的那一點）', 'wick': '火焰中心：遊戲在這裡放點光源', 'bail': '頂（提環）'}
for nm, xyz in L['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + WORK, 'name=' + nm, 'at=%d,%d,%d' % tuple(xyz), 'note=' + NOTE[nm])
print('  固定點', ', '.join(L['anchors']))
for nm, m in sorted(pl['models'].items()):
    cli('op=work', 'sub=unmodel', 'persona=gura', 'work=' + ASM, 'name=' + nm, ok=(0, 2))
    cli('op=work', 'sub=model', 'persona=gura', 'work=' + ASM, 'name=' + nm, 'source_work=' + WORK,
        'at=%g,%g,%g' % tuple(m['at']), 'pivot=%g,%g,%g' % tuple(m['pivot']), 'scale=%g' % m['scale'],
        'meta=' + json.dumps(m['meta'], ensure_ascii=False), 'note=階段五（TASK-0558）船尾燈')
    print('  模型 %s at %s' % (nm, m['at']))
