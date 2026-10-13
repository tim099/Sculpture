# 餘燼號 階段二十一 中央彈藥庫：照 magazine_mid_placement.json／verify_magazine_mid.json 下 CLI
#   -magazine-mid 子作品（0.1 m、parent 船殼、tags sub；已在 ⇒ 不重建不重落）→ 固定點 blast／door
#   → 子作品裡掛火藥桶模型（憲法號 -powder-barrel、scale 0.2、meta kind=powder／powder_lb=100；overwrite=1）
#   → 組裝件：關聯 彈藥庫-中（meta kind=magazine、powder_lb ＝ 桶數 × 100）、拿掉 彈藥庫-前／後（憲法號那兩件子作品不動）
# 用法：python -I magazine_mid_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException「無法移除要被取代的檔案」（TASK-0534）⇒ 只對那一句重試，最多 3 次
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL = 'basecamp-ember-01m'
ASM = 'basecamp-ember-01m-assembly'
W = 'basecamp-ember-01m-magazine-mid'
V = json.load(open(os.path.join(D, 'verify_magazine_mid.json'), encoding='utf-8'))
PL = json.load(open(os.path.join(D, 'magazine_mid_placement.json'), encoding='utf-8'))
ok = bad = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args, quiet=False):
    global ok, bad, retried
    for k in range(4):
        r = run(args)
        if r.returncode and any(t in (r.stdout + r.stderr) for t in ('無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 3:   # 中文／英文系統訊息都要認（v1 只認中文 ⇒ BTC 這台第一次就停）
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


vox = os.path.join(D, 'masks', 'magazine_mid', 'magazine.vox.txt').replace('\\', '/')
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
         'note=' + ('爆心：房間內空氣重心最近的一格' if name == 'blast' else '門洞地板中線（船尾那道艙壁）')])

meta_b = json.dumps({'kind': 'powder', 'powder_lb': 100})
for i, b in enumerate(PL['barrels']):
    s = PL['barrel_scale']
    cli(['op=work', 'sub=model', 'persona=basecamp', 'work=' + W, 'name=' + b['name'], 'source_work=' + PL['barrel_work'], 'at=' + xyz(b['at']),
         'pivot=' + xyz(PL['barrel_pivot']), 'rotate=0,0,0', 'scale=' + xyz([s, s, s]), 'overwrite=1', 'meta=' + meta_b,
         'note=火藥桶 第 %d 層（magazine_mid_placement.json）' % b['tier']], quiet=True)
    if (i + 1) % 50 == 0:
        print('· 桶 %d / %d' % (i + 1, len(PL['barrels'])))

lb = len(PL['barrels']) * 100
cli(['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=彈藥庫-中', 'source_work=' + W, 'at=' + xyz(PL['at']), 'overwrite=1',
     'note=中央彈藥庫（階段二十一；Tim：另做自己的、試試放中央）', 'meta=' + json.dumps({'kind': 'magazine', 'powder_lb': lb})])
links = run(['op=work', 'sub=links', 'work=' + ASM]).stdout
for old in ('彈藥庫-前', '彈藥庫-後'):
    if old in links:
        cli(['op=work', 'sub=unlink', 'persona=basecamp', 'work=' + ASM, 'name=' + old])
    else:
        print('· %s 已不在' % old)
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
