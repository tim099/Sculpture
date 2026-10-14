# 階段九 b：動索 —— 新固定點（帆桁子作品、桅子作品）、繩（組裝件）。
# 用法：python -I -X utf8 -B apply_running.py <design 資料夾> <步驟> [名字 regex]
#   步驟：anchors（overwrite=1）｜ropes（overwrite=1；照清單順序）
#   · ⛔ 失敗那一行整段印出來（不要在呼叫端再 grep 掉）
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
V = json.load(open(os.path.join(D, 'verify_running.json'), encoding='utf-8'))
ASM = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['work'] + '-assembly'
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1; print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


xyz = lambda v: ','.join('%d' % c for c in v)
if step == 'anchors':
    for work, L in V['anchors_new'].items():
        n = 0
        for a in L:
            if not flt.search(a['name']): continue
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + work, 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
                 'note=%s（階段九 verify_running.json）' % a['kind']]); n += 1
        print('anchors', work, n)
elif step == 'ropes':
    n = 0
    for r in V['ropes']:
        if not flt.search(r['name']): continue
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=' + r['kind'] + '（階段九）'])
        n += 1
    print('ropes', n)
else:
    raise SystemExit('步驟？ anchors|ropes')
print(step, 'ok', ok, 'bad', bad)
