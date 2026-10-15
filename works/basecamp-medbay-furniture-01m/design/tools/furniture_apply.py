# 醫療艙家具組（TASK-0569）：照 furniture_placement.json 下 CLI
#   每件：子作品（0.05 m、parent ＝ 本作品、tags sub；已在 ⇒ 不重建不重落）→ 固定點 → 目錄作品裡掛成模型（scale 0.5、meta kind=furniture／item；overwrite=1）
# 用法：python -I furniture_apply.py <design 資料夾>
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
MAIN = 'basecamp-medbay-furniture-01m'
PL = json.load(open(os.path.join(D, 'furniture_placement.json'), encoding='utf-8'))
IOERR = ('無法移除要被取代的檔案', 'Unable to remove the file to be replaced')
NAMES = {'bed': '病床', 'table': '手術台', 'medkit': '藥箱'}


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    for k in range(4):
        r = run(args)
        if r.returncode and any(t in (r.stdout + r.stderr) for t in IOERR) and k < 3:
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        print('✗', ' '.join(args[:6]), (r.stdout + r.stderr)[-600:])
        raise SystemExit(1)
    print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
    return r


xyz = lambda v: ','.join(('%.3f' % c).rstrip('0').rstrip('.') for c in v)
FL = PL.pop('_catalog_floor')
have = run(['op=stats', 'work=' + MAIN]).stdout
if 'total_voxels = 0' in have:
    cli(['op=stampvox', 'persona=basecamp', 'work=' + MAIN, 'voxels=' + os.path.join(D, 'masks', 'catalog_floor.vox.txt').replace('\\', '/'),
         'at=0,0,0', 'expect_pixels=%d' % FL['cells']])
else:
    print('· 目錄地板已在')
for it, p in PL.items():
    W = p['work']
    if run(['op=work', 'sub=show', 'work=' + W]).returncode == 0:
        print('· %s 已在 ⇒ 不重建' % W)
    else:
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + W, 'title=' + p['title'], 'size=' + xyz(p['size']), 'parent_work=' + MAIN, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + W, 'meters_per_voxel=0.05'])
        vox = os.path.join(D, 'masks', it + '.vox.txt').replace('\\', '/')
        cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % p['cells']])
    for name, at in p['anchors'].items():
        cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + W, 'name=' + name, 'at=' + xyz(at), 'overwrite=1',
             'note=TASK-0568 崗位物件的位子（draft_furniture.py）'])
    cli(['op=work', 'sub=model', 'persona=basecamp', 'work=' + MAIN, 'name=' + NAMES[it], 'source_work=' + W, 'at=' + xyz(p['catalog_at']),
         'pivot=0,0,0', 'rotate=0,0,0', 'scale=' + xyz([p['scale']] * 3), 'overwrite=1', 'meta=' + json.dumps(p['meta']),
         'note=目錄：放上船照這個 scale 與 meta（TASK-0569）'])
