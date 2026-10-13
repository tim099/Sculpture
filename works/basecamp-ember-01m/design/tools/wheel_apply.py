# 餘燼號 階段十七 舵輪：照 wheel_placement.json 下 CLI —— 甲板-spar 掛外部模型「舵輪」（憲法號 -wheel）、組裝件加舵索 2 條
# 用法：python -I wheel_apply.py <design 資料夾>（重跑：overwrite=1）
# ⚠ 寫入偶爾 IOException「無法移除要被取代的檔案」（TASK-0534）⇒ 只對那一句重試，最多 3 次
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['wheel_build']
W = json.load(open(os.path.join(D, 'wheel_placement.json'), encoding='utf-8'))
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
        print('✗', ' '.join(args[:6]), (r.stdout + r.stderr)[-400:])
    else:
        ok += 1
        print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓')))


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


s = W['scale']
cli(['op=work', 'sub=model', 'persona=basecamp', 'work=' + W['work'], 'name=' + W['name'], 'source_work=' + W['source_work'], 'at=' + xyz(W['at']),
     'pivot=' + xyz(W['pivot']), 'rotate=0,0,0', 'scale=' + xyz([s, s, s]), 'overwrite=1',
     'note=雙舵輪（階段十七；憲法號 -wheel 重複用；draft_wheel.py 從 x 246 起搜、0 碰撞）'])
for r in W['ropes']:
    cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + P['assembly'], 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
         'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'],
         'note=舵索（階段十七；鼓輪 → 甲板面，往下穿進甲板；同憲法號）'])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
