# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/split_funnels.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 階段九（TASK-0614）煙囪拆成兩件：遊戲（Blockside 78_funnel.js）照「關聯 meta kind=funnel ＋ 固定點 smoke」一條關聯冒一股煙
#   ⇒ 階段五的 -funnels（兩根同一件）拆成 -funnel-aft／-funnel-fore（x < 510 ／ ≥ 510；清單從 masks/deco/funnels.vox.txt 切，世界座標、at 0,0,0），
#   各登記 smoke（煙囪口中心：頂那一層的中線那一格 —— 煙囪是空心的，那一格是空氣）；關聯 煙囪-後／煙囪-前 meta kind=funnel、material=iron、render=smooth
#   （照維吉尼亞號 ame-virginia-01m-funnel，ame）；最後拿掉舊的關聯 `煙囪`（-funnels 那件留著、改名註明不再使用）。
#   讀數：組裝件拆之前／之後逐格相同（缺 0、多 0、色差 0）。
#   用法：python -I -X utf8 tools/split_funnels.py <design> [plan|apply]
import json, os, re, subprocess, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
step = sys.argv[2] if len(sys.argv) > 2 else 'plan'
sys.path.insert(0, D)
import mio  # noqa: E402

HULL, ASM = 'crest-001-susquehanna-01m', 'crest-001-susquehanna-01m-assembly'
SPLIT_X = 510
PARTS = [('aft', '煙囪-後', '蘇士奎哈納號 後煙囪（主桅後，x 406）'), ('fore', '煙囪-前', '蘇士奎哈納號 前煙囪（主桅與前桅之間，x 615）')]
META = {'kind': 'funnel', 'material': 'iron', 'render': 'smooth'}


def cli(*a):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print((r.stdout + r.stderr)[-1200:])
        raise SystemExit('✗ ' + ' '.join(a[:4]))
    return r.stdout


def key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


A = np.loadtxt(os.path.join(D, 'masks', 'deco', 'funnels.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
plan = {}
for k, link, title in PARTS:
    B = A[(A[:, 0] < SPLIT_X) if k == 'aft' else (A[:, 0] >= SPLIT_X)]
    zt = int(B[:, 2].max())
    T = B[B[:, 2] == zt]
    cx, cy = int(round(T[:, 0].mean())), int(round(T[:, 1].mean()))
    assert not ((B[:, 0] == cx) & (B[:, 1] == cy) & (B[:, 2] == zt)).any(), '煙囪口中心那一格不是空氣'
    fn = os.path.join(D, 'masks', 'deco', 'funnel_%s.vox.txt' % k)
    cells = {(int(x), int(y), int(z)): int(c) for x, y, z, c in B.tolist()}
    n, h = mio.write_local(fn, cells, (0, 0, 0), '# 蘇士奎哈納號 %s（split_funnels.py 從 funnels.vox.txt 切；世界座標，at 0,0,0）\n' % title)
    plan[k] = {'work': 'crest-001-susquehanna-01m-funnel-' + k, 'link': link, 'title': title, 'file': fn.replace(os.sep, '/'), 'cells': n, 'sha256': h,
               'smoke': [cx, cy, zt], 'x': [int(B[:, 0].min()), int(B[:, 0].max())]}
assert sum(p['cells'] for p in plan.values()) == len(A)
print(json.dumps(plan, ensure_ascii=False, indent=1))
if step != 'apply':
    raise SystemExit(0)

before = mio.export_list(ASM, 'all')
for k, p in plan.items():
    if subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=show', '--arg', 'work=' + p['work']], capture_output=True).returncode != 0:
        cli('op=work', 'sub=create', 'persona=crest-001', 'id=' + p['work'], 'title=' + p['title'], 'size=1200,400,800', 'parent_work=' + HULL, 'tags=sub')
        cli('op=work', 'sub=update', 'persona=crest-001', 'work=' + p['work'], 'meters_per_voxel=0.1')
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli('op=stats', 'work=' + p['work'])).group(1))
    if have == 0:
        out = cli('op=stampvox', 'persona=crest-001', 'work=' + p['work'], 'voxels=' + p['file'], 'at=0,0,0', 'expect_pixels=%d' % p['cells'], 'share=0')
        assert int(re.search(r'🔢 placed = (\d+)', out).group(1)) == p['cells']
    elif have != p['cells']:
        raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (p['work'], have, p['cells']))
    cli('op=work', 'sub=anchor', 'persona=crest-001', 'work=' + p['work'], 'name=smoke', 'at=' + ','.join(map(str, p['smoke'])), 'overwrite=1',
        'note=排煙點：煙囪口的中心（Blockside 78_funnel.js）')
    cli('op=work', 'sub=link', 'persona=crest-001', 'work=' + ASM, 'name=' + p['link'], 'source_work=' + p['work'], 'at=0,0,0', 'overwrite=1',
        'note=階段九（TASK-0614）煙囪拆成兩件（遊戲一條 kind=funnel 關聯冒一股煙）', 'meta=' + json.dumps(META))
    print('✓', p['link'], p['work'], p['cells'], 'smoke', p['smoke'])
cli('op=work', 'sub=unlink', 'persona=crest-001', 'work=' + ASM, 'name=煙囪')
cli('op=work', 'sub=update', 'persona=crest-001', 'work=crest-001-susquehanna-01m-funnels', 'title=蘇士奎哈納號 煙囪（階段五；階段九拆成 -funnel-aft／-funnel-fore，這件不再關聯）')
after = mio.export_list(ASM, 'all')
db = dict(zip(key(before).tolist(), before[:, 3].tolist()))
da = dict(zip(key(after).tolist(), after[:, 3].tolist()))
print('組裝件 拆之前 %d ↔ 之後 %d：缺 %d、多 %d、色差 %d' % (len(before), len(after), len(set(db) - set(da)), len(set(da) - set(db)),
                                                    sum(1 for k in set(db) & set(da) if db[k] != da[k])))
