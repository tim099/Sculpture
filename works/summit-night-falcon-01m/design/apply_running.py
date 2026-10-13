# 階段十：照 verify_running.json 下 CLI —— 新固定點（帆桁、桅）與動索
# 用法：python -I -X utf8 -B apply_running.py <design 資料夾> <步驟> [名字 regex]
#   步驟：anchors｜ropes（overwrite=1 ⇒ 重跑一樣；⛔ 失敗整段印出來）
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
V = json.load(open(os.path.join(D, 'verify_running.json'), encoding='utf-8'))
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


if step == 'anchors':
    for w, L in V['anchors_new'].items():
        n = 0
        for a in L:
            if not flt.search(a['name']): continue
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + w, 'name=' + a['name'], 'at=' + ','.join('%d' % c for c in a['at']), 'overwrite=1',
                 'note=%s（verify_running.json，階段十）' % a['kind']]); n += 1
        print('anchors', w, n)
elif step == 'ropes':
    n = 0
    for r in V['ropes']:
        if not flt.search(r['name']): continue
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=' + r['kind'] + '（階段十）'])
        n += 1
    print('ropes', n)
else:
    raise SystemExit('步驟？ anchors|ropes')
print(step, 'ok', ok, 'bad', bad)
