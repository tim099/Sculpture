# 照 design/<清單>.json 的 ropes 一條一條下 CLI（掛在組裝件；overwrite=1 ⇒ 重跑一樣）
# 用法：python -I ropes_apply.py <design 資料夾> <清單檔名> [繩名篩選 regex]
import sys, os, json, re, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D, fn = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
ASM = 'basecamp-frigate-constitution-01m-assembly'
ok = bad = 0
for r in json.load(open(os.path.join(D, fn), encoding='utf-8'))['ropes']:
    if not flt.search(r['name']):
        continue
    args = ['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=rope', '--arg', 'persona=basecamp', '--arg', 'work=' + ASM,
            '--arg', 'name=' + r['name'], '--arg', 'from=' + r['from'], '--arg', 'to=' + r['to'], '--arg', 'overwrite=1',
            '--arg', 'slack=%g' % r['slack'], '--arg', 'color=' + r['color'], '--arg', 'thickness=%g' % r['thickness'], '--arg', 'note=' + r.get('group', '')]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        bad += 1
        print('✗', r['name'], (p.stdout + p.stderr)[-400:])
    else:
        ok += 1
print('ropes ok', ok, 'bad', bad)
