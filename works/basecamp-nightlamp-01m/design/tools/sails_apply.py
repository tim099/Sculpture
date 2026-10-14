# 階段十六：照 design/sails_plan.json 下 CLI —— 固定點、帆、帆自己的繩、meta、預設風
# 用法：python -I sails_apply.py <design 資料夾> <步驟> [名字 regex]
#   步驟：anchors｜sails｜ropes｜meta（帆＋繩一份批次檔）｜wind｜readback
import sys, os, json, re, subprocess, tempfile
sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
WORKS = os.path.dirname(os.path.dirname(D))
ASM = 'basecamp-nightlamp-01m-assembly'
SP = json.load(open(os.path.join(D, 'sails_plan.json'), encoding='utf-8'))
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['sails']
ok = bad = 0


def cli(args, show=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:5]), (r.stdout + r.stderr)[-600:])
    else:
        ok += 1
        if show:
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓'))[-600:])
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%g' % c for c in v)


if step == 'anchors':
    for a in SP['points']:
        if flt.search(a['name']):
            cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + a['owner'], 'name=' + a['name'], 'at=' + xyz(a['local']), 'overwrite=1',
                 'note=%s（階段十六 sails_plan.json）' % a['kind']])

elif step == 'sails':
    for s in SP['sails']:
        if not flt.search(s['name']):
            continue
        args = ['op=work', 'sub=sail', 'persona=basecamp', 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(s['corners']),
                'bind=' + ','.join(str(b) for b in s['bind']), 'fullness=%g' % s['fullness'], 'color=' + s['color'], 'overwrite=1',
                'note=階段十六（sails_plan.json）']
        if s['corner_names']:
            args.append('corner_names=' + '|'.join(s['corner_names']))
        if s['free']:
            args.append('free=' + ','.join(str(f) for f in s['free']))
        if s.get('texture'):
            args.append('texture=' + os.path.join(D, s['texture']).replace('\\', '/'))
        cli(args, show=True)

elif step == 'ropes':
    for r in SP['ropes']:
        if flt.search(r['name']):
            cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'],
                 'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'overwrite=1',
                 'note=階段十六 帆自己的繩（sails_plan.json）'])

elif step == 'meta':
    lines = ['sail\t%s\t%s' % (s['name'], json.dumps(s['meta'], ensure_ascii=False)) for s in SP['sails']]
    lines += ['rope\t%s\t%s' % (r['name'], json.dumps(r['meta'], ensure_ascii=False)) for r in SP['ropes']]
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, 'meta.tsv')
        open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
        cli(['op=work', 'sub=meta', 'persona=basecamp', 'work=' + ASM, 'file=' + p.replace('\\', '/')], show=True)

elif step == 'wind':
    cli(['op=work', 'sub=wind', 'persona=basecamp', 'work=' + ASM, 'wind=' + xyz(plan['wind']), 'sail_seconds=%g' % plan['sail_seconds']], show=True)

elif step == 'readback':
    miss = diff = 0
    for a in SP['points']:
        A = {x['name']: x for x in json.load(open(os.path.join(WORKS, a['owner'], 'anchors.json'), encoding='utf-8'))['anchors']}
        g = A.get(a['name'])
        if g is None:
            miss += 1
        elif [round(c) for c in g['at']] != a['local']:
            diff += 1
    print('anchors', len(SP['points']), 'missing', miss, 'diff', diff)
    got = {s['name']: s for s in json.load(open(os.path.join(WORKS, ASM, 'sails.json'), encoding='utf-8'))['sails']}
    sm = [s['name'] for s in SP['sails'] if s['name'] not in got]
    sd = []
    for s in SP['sails']:
        g = got.get(s['name'])
        if g and ([c['at'] for c in g['corners']] != s['corners'] or g['bind'] != s['bind'] or (g.get('meta') or {}) != s['meta']
                  or sorted(c['name'] if s['corner_names'] else str(i) for i, c in enumerate(g['corners']) if not c['pin']) != sorted(str(f) for f in s['free'])):
            sd.append(s['name'])
    print('sails', len(SP['sails']), 'missing', len(sm), 'diff', len(sd), sd)
    gr = {r['name']: r for r in json.load(open(os.path.join(WORKS, ASM, 'ropes.json'), encoding='utf-8'))['ropes']}
    rm = [r['name'] for r in SP['ropes'] if r['name'] not in gr]
    rd = [r['name'] for r in SP['ropes'] if r['name'] in gr and (gr[r['name']]['from'] != r['from'] or gr[r['name']]['to'] != r['to'] or (gr[r['name']].get('meta') or {}) != r['meta'])]
    print('ropes', len(SP['ropes']), 'missing', len(rm), 'diff', len(rd), rd)
else:
    raise SystemExit('步驟？ anchors|sails|ropes|meta|wind|readback')
print(step, 'ok', ok, 'bad', bad)
