# 階段十七：照 design/guns_placement.json 在上甲板子作品放砲（外部模型 ← 憲法號 -gun-24）
# 用法：python -I guns_apply.py <design 資料夾> <models|readback> [名字 regex]
import sys, os, json, re, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
WORKS = os.path.dirname(os.path.dirname(D))
G = json.load(open(os.path.join(D, 'guns_placement.json'), encoding='utf-8'))
PL = [p for p in G['placements'] if flt.search(p['name'])]
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:5]), (r.stdout + r.stderr)[-500:])
    else:
        ok += 1
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%g' % c for c in v)


if step == 'models':
    for p in PL:
        args = ['op=work', 'sub=model', 'persona=basecamp', 'work=' + G['host'], 'name=' + p['name'], 'source_work=' + G['source_work'],
                'at=' + xyz(p['at']), 'pivot=' + xyz(p['pivot']), 'rotate=' + xyz(p['rotate']), 'scale=' + xyz(p['scale']), 'overwrite=1',
                'meta=' + json.dumps(p['meta'], ensure_ascii=False),
                'note=24 磅長砲（階段十七 place_guns.py；第 %d 個砲門 %s 舷）' % (p['port'], p['side'])]
        args.append('mirror=' + (p['mirror'] or 'none'))
        cli(args)
elif step == 'readback':
    M = {m['name']: m for m in json.load(open(os.path.join(WORKS, G['host'], 'models.json'), encoding='utf-8'))['models']}
    diff = [p['name'] for p in PL if p['name'] not in M or M[p['name']]['at'] != p['at'] or M[p['name']].get('meta') != p['meta']
            or (M[p['name']].get('mirror') or '') != p['mirror'] or M[p['name']]['work'] != G['source_work'] or M[p['name']]['scale'] != p['scale']]
    print('guns', len(PL), 'missing/diff', len(diff), diff)
else:
    raise SystemExit('步驟？ models|readback')
print(step, 'ok', ok, 'bad', bad)
