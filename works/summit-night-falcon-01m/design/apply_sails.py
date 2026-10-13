# 階段十一：照 verify_sails.json 下 CLI —— 預設風、帆、帆腳索
# 用法：python -I -X utf8 -B apply_sails.py <design 資料夾> <步驟> [名字 regex]
#   步驟：wind｜sails｜ropes（overwrite=1 ⇒ 重跑一樣；⛔ 失敗整段印出來）
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
V = json.load(open(os.path.join(D, 'verify_sails.json'), encoding='utf-8'))
ASM = 'summit-night-falcon-01m-assembly'
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.stdout


if step == 'wind':
    cli(['op=work', 'sub=wind', 'persona=summit', 'work=' + ASM, 'wind=' + ','.join('%g' % c for c in V['wind']), 'sail_seconds=%g' % V['seconds']])
elif step == 'sails':
    for s in V['sails']:
        if not flt.search(s['name']): continue
        args = ['op=work', 'sub=sail', 'persona=summit', 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(s['corners']),
                'corner_names=' + '|'.join(s['corner_names']), 'bind=' + s['bind'], 'fullness=%g' % s['fullness'], 'color=' + s['color'],
                'overwrite=1', 'note=' + s['note'] + '（階段十一）']
        if s['free']: args.append('free=' + s['free'])
        cli(args); print('sail', s['name'])
elif step == 'ropes':
    for r in V['ropes']:
        if not flt.search(r['name']): continue
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=' + r['kind'] + '（階段十一）'])
    print('ropes', sum(1 for r in V['ropes'] if flt.search(r['name'])))
else:
    raise SystemExit('步驟？ wind|sails|ropes')
print(step, 'ok', ok, 'bad', bad)
