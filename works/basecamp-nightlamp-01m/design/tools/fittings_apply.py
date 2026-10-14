# 階段十八：照 design/fittings_placement.json 放配件模型（舵輪、羅經櫃、主絞盤）
# 用法：python -I fittings_apply.py <design 資料夾> <models|readback>
import sys, os, json, subprocess
sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
WORKS = os.path.dirname(os.path.dirname(D))
PL = json.load(open(os.path.join(D, 'fittings_placement.json'), encoding='utf-8'))['placements']
ok = bad = 0


def xyz(v):
    return ','.join('%g' % c for c in v)


if step == 'models':
    for p in PL:
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in [
            'op=work', 'sub=model', 'persona=basecamp', 'work=' + p['host'], 'name=' + p['name'], 'source_work=' + p['source_work'],
            'at=' + xyz(p['at']), 'pivot=' + xyz(p['pivot']), 'rotate=' + xyz(p['rotate']), 'scale=' + xyz(p['scale']), 'overwrite=1',
            'meta=' + json.dumps(p['meta'], ensure_ascii=False), 'note=階段十八 甲板配件（place_fittings.py）']], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode:
            bad += 1
            print('✗', p['name'], (r.stdout + r.stderr)[-400:])
        else:
            ok += 1
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓')))
elif step == 'readback':
    for p in PL:
        M = {m['name']: m for m in json.load(open(os.path.join(WORKS, p['host'], 'models.json'), encoding='utf-8'))['models']}
        m = M.get(p['name'])
        good = m is not None and m['at'] == p['at'] and m['scale'] == p['scale'] and m.get('meta') == p['meta'] and m['work'] == p['source_work'] and m['pivot'] == p['pivot']
        print(p['name'], 'ok' if good else '✗')
print(step, 'ok', ok, 'bad', bad)
