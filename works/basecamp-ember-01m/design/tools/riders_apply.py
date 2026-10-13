# 餘燼號 船艙底斜肋重畫：照 verify_riders.json／masks/riders/ 下 CLI（船殼 basecamp-ember-01m）
#   標記 斜肋:begin → carvevox 碎段（顏色守門 104）→ stampvox 新的斜肋（空氣）→ stampvox overwrite limber→斜肋 → stampvox overwrite 斜肋→limber → 斜肋:end
# 用法：python -I riders_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException「無法移除要被取代的檔案」（TASK-0534）⇒ 只對那一句重試，最多 3 次
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['riders_fix']
V = json.load(open(os.path.join(D, 'verify_riders.json'), encoding='utf-8'))
W = P['hull']
ok = bad = retried = 0


def cli(args):
    global ok, bad, retried
    for k in range(4):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode and '無法移除要被取代的檔案' in (r.stdout + r.stderr) and k < 3:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:4]), (r.stdout + r.stderr)[-500:])
        raise SystemExit(1)
    ok += 1
    print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l or 'carved =' in l))


def path(k):
    return os.path.join(D, V['files'][k]['file']).replace('\\', '/')


cli(['op=work', 'sub=mark', 'persona=basecamp', 'work=' + W, 'name=斜肋', 'phase=begin', 'note=船艙底斜肋重畫（拉長時斷成鋸齒的 6 根改成整根 +66）'])
cli(['op=carvevox', 'persona=basecamp', 'work=' + W, 'voxels=' + path('carve'), 'at=0,0,0', 'expect_pixels=%d' % V['files']['carve']['cells']])
cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + path('stamp'), 'at=0,0,0', 'expect_pixels=%d' % V['files']['stamp']['cells']])
cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + path('over_rider'), 'at=0,0,0', 'overwrite=1', 'expect_pixels=%d' % V['files']['over_rider']['cells']])
cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + path('refill_limber'), 'at=0,0,0', 'overwrite=1', 'expect_pixels=%d' % V['files']['refill_limber']['cells']])
cli(['op=work', 'sub=mark', 'persona=basecamp', 'work=' + W, 'name=斜肋', 'phase=end'])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
