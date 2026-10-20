# 階段四落格（TASK-0754）：30 支槳（外部模型，掛在船殼作品裡；來源 erina-dromon-01m-oar-upper，scale 0.5；左舷 mirror=y）
#   用法：python -I -X utf8 tools/build_oars.py
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
HULL = 'apex-one-punt-01m'
SRC = 'erina-dromon-01m-oar-upper'
PL = json.load(open(os.path.join(HERE, 'oars_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:150]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


for o in PL:
    args = ['op=work', 'sub=model', 'persona=apex-one', 'work=' + HULL, 'name=' + o['name'], 'source_work=' + SRC,
            'at=%g,%g,%g' % tuple(o['at']), 'pivot=%g,%g,%g' % tuple(o['pivot']), 'scale=%g' % o['scale'], 'rotate=%g,%g,%g' % tuple(o['rotate']),
            'meta=' + json.dumps(o['meta'], ensure_ascii=False), 'note=階段四 槳（引用持火號上層槳；照舷弧補傾角）']
    if o['mirror']:
        args.append('mirror=' + o['mirror'])
    cli(*args)
