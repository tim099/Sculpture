# 餘燼號 階段二十 小艇與艇架：照 verify_boats.json／boats_placement.json 下 CLI
#   -boat 子作品（0.05 m、parent 船殼、tags sub；已在 ⇒ 不重建不重落）→ 甲板-spar：標記 艇架:begin → stampvox 艇架 → 艇架:end（艇架已在 ⇒ 跳過）
#   → 甲板-spar 掛外部模型 小艇-S／小艇-P（P 舷 mirror=y；overwrite=1）
# 用法：python -I boats_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException「無法移除要被取代的檔案」（TASK-0534）⇒ 只對那一句重試，最多 3 次
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL = 'basecamp-ember-01m'
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['boats_build']
V = json.load(open(os.path.join(D, 'verify_boats.json'), encoding='utf-8'))
PL = json.load(open(os.path.join(D, 'boats_placement.json'), encoding='utf-8'))
ok = bad = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, bad, retried
    for k in range(4):
        r = run(args)
        if r.returncode and '無法移除要被取代的檔案' in (r.stdout + r.stderr) and k < 3:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:5]), (r.stdout + r.stderr)[-500:])
        raise SystemExit(1)
    ok += 1
    print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))


def path(rel):
    return os.path.join(D, rel).replace('\\', '/')


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


W = P['work']
if run(['op=work', 'sub=show', 'work=' + W]).returncode == 0:
    print('· %s 已在 ⇒ 不重建' % W)
else:
    cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + W, 'title=餘燼號 小艇 cutter 9 m（0.05 m／格）', 'size=' + xyz(V['boat']['size']), 'parent_work=' + HULL, 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + W, 'meters_per_voxel=0.05'])
    cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + path(V['files']['boat']['file']), 'at=0,0,0', 'expect_pixels=%d' % V['files']['boat']['cells']])

DW = P['deck_work']
sx = P['skids']['x'][0]
probe = run(['op=stats', 'work=' + DW, 'region=%d..%d,160..160,%d..%d' % (sx, sx, P['skids']['z'][0], P['skids']['z'][0])])
if '🔢 scoped_voxels = 1' in probe.stdout:
    print('· 艇架已在 ⇒ 不重落')
else:
    cli(['op=work', 'sub=mark', 'persona=basecamp', 'work=' + DW, 'name=艇架', 'phase=begin', 'note=船腰 skid beams 三根（階段二十）'])
    cli(['op=stampvox', 'persona=basecamp', 'work=' + DW, 'voxels=' + path(V['files']['skids']['file']), 'at=0,0,0', 'expect_pixels=%d' % V['files']['skids']['cells']])
    cli(['op=work', 'sub=mark', 'persona=basecamp', 'work=' + DW, 'name=艇架', 'phase=end'])

s = PL['scale']
for b in PL['boats']:
    args = ['op=work', 'sub=model', 'persona=basecamp', 'work=' + PL['deck_work'], 'name=' + b['name'], 'source_work=' + PL['boat_work'], 'at=' + xyz(b['at']),
            'pivot=' + xyz(PL['pivot']), 'rotate=0,0,0', 'scale=' + xyz([s, s, s]), 'overwrite=1', 'note=小艇 cutter 9 m（階段二十；%s 舷，擱在艇架上）' % b['side']]
    if b['mirror']:
        args.append('mirror=' + b['mirror'])
    cli(args)
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
