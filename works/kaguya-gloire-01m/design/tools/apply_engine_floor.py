# 光榮號 機艙鐵地板落格：子作品 -deck-engine（整船的框、世界座標、0.1 m、parent 船殼、sub）← masks/engine_floor/floor.vox.txt；
#   組裝件關聯 甲板-engine（at 0,0,0）meta kind=deck、deck=engine、level −1、name 機艙、floor、thick 1（照拿破崙號階段十四）。
#   floor 折線從 x 404 起：主機底座（x 404–462）頂面也是 z 12 ⇒ 機匠站位（tend-*）照這一層。
#   用法：python -I -X utf8 tools/apply_engine_floor.py <design>
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL, ASM = 'kaguya-gloire-01m', 'kaguya-gloire-01m-assembly'
PL = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['engine']['floor']
V = json.load(open(os.path.join(D, 'verify_engine_floor.json'), encoding='utf-8'))
W = PL['work']
meta = dict(V['deck_meta'], floor='404:%d,%d:%d' % (PL['z'] + 1, V['x'][1], PL['z'] + 1))


def cli(*a):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print((r.stdout + r.stderr)[-1200:])
        raise SystemExit(1)
    return r.stdout


if subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=show', '--arg', 'work=' + W], capture_output=True).returncode != 0:
    cli('op=work', 'sub=create', 'persona=kaguya', 'id=' + W, 'title=光榮號 機艙鐵地板（level −1；0.1 m）', 'size=1200,400,800', 'parent_work=' + HULL, 'tags=sub')
    cli('op=work', 'sub=update', 'persona=kaguya', 'work=' + W, 'meters_per_voxel=0.1')
have = int(re.search(r'🔢 total_voxels = (\d+)', cli('op=stats', 'work=' + W)).group(1))
if have == 0:
    out = cli('op=stampvox', 'persona=kaguya', 'work=' + W, 'voxels=' + os.path.join(D, 'masks', 'engine_floor', 'floor.vox.txt').replace(os.sep, '/'),
              'at=0,0,0', 'expect_pixels=%d' % V['cells'], 'share=0')
    n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
    assert n == V['cells'], (n, V['cells'])
elif have != V['cells']:
    raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (W, have, V['cells']))
cli('op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=' + PL['link'], 'source_work=' + W, 'at=0,0,0', 'overwrite=1',
    'note=機艙鐵地板（level −1）', 'meta=' + json.dumps(meta, ensure_ascii=False, sort_keys=True))
print('✓', W, V['cells'], '格；關聯', PL['link'], meta)
