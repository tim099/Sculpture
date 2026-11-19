# Source: pinnacle-patache-01m/design/tools/build_guns.py (San Roman, TASK-0970) -- rewritten for the Star (TASK-0019 step 9).
# Step 9 stamping: one external model per gun from guns_placement.json, hung on the deck sub-work it stands on (Ship_Guns 4.2).
#   P side mirror=y; meta = the type's meta + deck, side, port (+ arc of that station for swivels).
#   Swivels: the pierrier was split into barrel + fork (-mount) on 2026-10-28 ⇒ a new ship adds the twin `<name>座` itself
#   (Ship_Guns 4.2.1): same placement, source = the -mount work, meta kind=gunmount. mount_of needs the gun's object id,
#   which only Blockside admin.py ids hands out (step 14) ⇒ written then.
#   Usage: python -X utf8 tools/build_guns.py <design>   (SENATE = wrapper path; reruns use overwrite=1)
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
SENATE = os.environ.get('SENATE', 'senate')
PERSONA = 'Claude-Ojousama'
GB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['guns_build']
PL = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']
NAMES = {'4l': '4 磅砲（聖羅曼號做的通用部件 -gun-4l，縮 0.443）', 'pierrier': '迴旋砲 pierrier（皇家號的通用部件，縮 0.39，同拉貝爾號、聖羅曼號）'}


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


def cli(args):
    p = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return p.returncode, (p.stdout + p.stderr)


ONLY = os.environ.get('GUNS_ONLY')                  # try one gun first (name), then the whole list
ok = bad = 0
for r in PL:
    if ONLY and r['name'] != ONLY:
        continue
    t = GB['types'][r['type']]
    s = float(t['scale'])
    meta = dict(t['meta'])
    meta.update({'deck': r['deck'], 'side': r['side'], 'port': r['port'] if isinstance(r['port'], int) else 'swivel'})
    if r['swivel']:
        meta['arc'] = r['arc']
    where = ('%s 第 %d 個砲門' % (r['deck'], r['port'])) if isinstance(r['port'], int) else ('%s 舷牆頂 x %d' % (r['deck'], int(r['at'][0])))
    note = '%s（步驟 9 TASK-0019；%s 舷、%s；draft_guns.py back %s、砲口伸出 %s）' % (NAMES[r['type']], r['side'], where, num(float(r['back'])), num(float(r['muzzle_beyond'])))
    base = ['op=work', 'sub=model', 'persona=' + PERSONA, 'work=' + GB['deck_works'][r['deck']], 'at=' + xyz(r['at']), 'pivot=' + xyz(t['pivot']),
            'rotate=0,0,' + num(float(r['phi'])), 'scale=' + xyz([s, s, s]), 'overwrite=1'] + (['mirror=y'] if r['side'] == 'P' else [])
    todo = [(r['name'], t['work'], meta, note)]
    if t.get('mount_work'):
        todo.append((r['name'] + '座', t['mount_work'], {'kind': 'gunmount'},
                     '%s的叉架（拆件雙生，Ship_Guns §4.2.1；mount_of 等步驟 14 發 id 後補）' % r['name']))
    for nm, src, mt, nt in todo:
        code, out = cli(base + ['name=' + nm, 'source_work=' + src, 'meta=' + json.dumps(mt, ensure_ascii=False, separators=(',', ':')), 'note=' + nt])
        if code:
            bad += 1
            print('✗', nm, out[-600:])
        else:
            ok += 1
print('models ok %d / bad %d (design %d)' % (ok, bad, sum(2 if GB['types'][r['type']].get('mount_work') else 1 for r in PL)))
sys.exit(1 if bad else 0)
