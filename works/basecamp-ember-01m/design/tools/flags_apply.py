# 餘燼號 階段十九 旗：照 plan.json flags_build／verify_flags.json 下 CLI
#   每根旗桿（後桅、主桅子作品）：冠那一格已有 ⇒ 跳過；否則 標記 旗桿:begin → stampvox → 旗桿:end；組裝件：sub=sail 船尾旗、長旗（貼圖；重跑 overwrite=1）
# 用法：python -I flags_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException「無法移除要被取代的檔案」（TASK-0534）⇒ 只對那一句重試，最多 3 次
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['flags_build']
V = json.load(open(os.path.join(D, 'verify_flags.json'), encoding='utf-8'))
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
        print('✗', ' '.join(args[:5]), (r.stdout + r.stderr)[-500:])
        raise SystemExit(1)
    ok += 1
    print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))


def path(rel):
    return os.path.join(D, rel).replace('\\', '/')


for pole in P['poles']:
    W = pole['work']
    F = V['pole_' + W.rsplit('-', 1)[1]]
    cap = (pole['x'], pole['y'], pole['z'][1] + 1)
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=stats', '--arg', 'work=' + W, '--arg', 'region=%d..%d,%d..%d,%d..%d' % (cap[0], cap[0], cap[1], cap[1], cap[2], cap[2])],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if '🔢 scoped_voxels = 1' in r.stdout:
        print('· %s 旗桿已在（冠那一格有東西）⇒ 不重落' % pole['label'])
        continue
    cli(['op=work', 'sub=mark', 'persona=basecamp', 'work=' + W, 'name=旗桿', 'phase=begin', 'note=%s桅冠上加旗桿（階段十九）' % pole['label']])
    cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + path(F['file']), 'at=0,0,0', 'expect_pixels=%d' % F['cells']])
    cli(['op=work', 'sub=mark', 'persona=basecamp', 'work=' + W, 'name=旗桿', 'phase=end'])
for key, label in (('ensign', '船尾旗（餘燼號旗：暗紅底金邊、正中一團火）'), ('pennant', '長旗（靠桅金、暗紅、燕尾）')):
    F = P[key]
    cli(['op=work', 'sub=sail', 'persona=basecamp', 'work=' + P['assembly'], 'name=' + F['name'], 'corners=' + '|'.join(F['corners']),
         'bind=' + F['bind'], 'free=' + F['free'], 'color=' + F['color'], 'texture=' + path(V[key]['file']), 'overwrite=1',
         'note=%s（階段十九）' % label])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
