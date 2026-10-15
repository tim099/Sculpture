# 夜燈號 彈藥庫＋水線 meta：照 magazine_placement.json 下 CLI（改自餘燼號 design/tools/magazine_mid_apply.py）
#   -magazine 子作品（0.1 m、parent 船殼、tags sub；已在 ⇒ 不重建不重落）→ 固定點 blast／door
#   → 子作品裡掛火藥桶模型（憲法號 -powder-barrel、scale 0.2、meta kind=powder／powder_lb=100；overwrite=1）
#   → 組裝件：關聯 彈藥庫（meta kind=magazine、pos=aft、powder_lb ＝ 桶數 × 100）
#   → 組裝件：船殼那條關聯 meta kind=ship、waterline_z=75（船中塗裝吃水線；ame 2026-10-15 seq 24672「用船中 75 就好」）
# 用法：python -I magazine_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException「無法移除要被取代的檔案」（TASK-0534）⇒ 只對那一句重試，最多 3 次（中英文訊息都認）
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL = 'basecamp-nightlamp-01m'
ASM = 'basecamp-nightlamp-01m-assembly'
W = 'basecamp-nightlamp-01m-magazine'
WATERLINE_Z = 75
PL = json.load(open(os.path.join(D, 'magazine_placement.json'), encoding='utf-8'))
ok = bad = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args, quiet=False):
    global ok, bad, retried
    for k in range(4):
        r = run(args)
        if r.returncode and any(t in (r.stdout + r.stderr) for t in ('無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 3:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:6]), (r.stdout + r.stderr)[-600:])
        raise SystemExit(1)
    ok += 1
    if not quiet:
        print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
    return r


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


vox = os.path.join(D, 'masks', 'magazine', 'magazine.vox.txt').replace('\\', '/')
if run(['op=work', 'sub=show', 'work=' + W]).returncode == 0:
    print('· %s 已在 ⇒ 不重建' % W)
else:
    cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + W, 'title=' + PL['title'], 'size=' + xyz(PL['size']), 'parent_work=' + HULL, 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + W, 'meters_per_voxel=0.1'])
    cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % PL['cells']])

have = run(['op=work', 'sub=anchors', 'work=' + W]).stdout
for name, p in PL['anchors'].items():
    if '`%s`' % name in have or ' %s ' % name in have:
        print('· 固定點 %s 已在' % name)
        continue
    cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + W, 'name=' + name, 'at=' + xyz(p), 'overwrite=1',
         'note=' + ('爆心：房間內空氣重心最近的一格' if name == 'blast' else '門洞地板中線（船頭那道艙壁，對著後艙口）')])

meta_b = json.dumps({'kind': 'powder', 'powder_lb': 100})
for i, b in enumerate(PL['barrels']):
    s = PL['barrel_scale']
    cli(['op=work', 'sub=model', 'persona=basecamp', 'work=' + W, 'name=' + b['name'], 'source_work=' + PL['barrel_work'], 'at=' + xyz(b['at']),
         'pivot=' + xyz(PL['barrel_pivot']), 'rotate=0,0,0', 'scale=' + xyz([s, s, s]), 'overwrite=1', 'meta=' + meta_b,
         'note=火藥桶 第 %d 層（magazine_placement.json）' % b['tier']], quiet=True)
print('· 桶 %d 個' % len(PL['barrels']))

lb = len(PL['barrels']) * 100
cli(['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=彈藥庫', 'source_work=' + W, 'at=' + xyz(PL['at']), 'overwrite=1',
     'note=船尾貨艙彈藥庫（Tim 2026-10-15）', 'meta=' + json.dumps({'kind': 'magazine', 'pos': 'aft', 'powder_lb': lb})])
cli(['op=work', 'sub=meta', 'persona=basecamp', 'work=' + ASM, 'part=link', 'name=船殼', 'meta=' + json.dumps({'kind': 'ship', 'waterline_z': WATERLINE_Z})])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
