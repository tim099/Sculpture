# 塔爾塔納 步驟 11（TASK-1299）落格：舵、舵柄、錨架＋錨、錨鏈孔 hawse-P/S
#   用法：python -I -X utf8 tools/build_rudder_anchor.py <design>
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'apex-one-tartane-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
RB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['rudder_anchor_build']
PL = json.load(open(os.path.join(design, 'rudder_anchor_placement.json'), encoding='utf-8'))
NOTE = 'note=步驟 11（TASK-1299；draft_rudder_anchor.py）'


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-1500:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args[:5])))
    return out


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


def js(o):
    return 'meta=' + json.dumps(o, ensure_ascii=False, separators=(',', ':'))


def subwork(w, title, path):
    if os.path.exists(os.path.join(WORKS, w, 'work.json')):
        return
    cli('op=work', 'sub=create', 'persona=apex-one', 'id=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=360,192,320')
    cli('op=work', 'sub=update', 'persona=apex-one', 'work=' + w, 'meters_per_voxel=0.1', 'tags=sub')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=apex-one', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        print(out[-1500:])
        raise SystemExit('✗ placed ≠ %d（%s）' % (n, w))
    print('✓ 建立 %s（%d 格）' % (w, n))


RU, AN, TI = RB['rudder'], RB['anchor'], RB['tiller']
R = PL['rudder']
subwork(RU['work'], RU['title'], os.path.join(design, 'masks', 'rudder', 'rudder.vox.txt'))
for an, at in R['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=apex-one', 'work=' + RU['work'], 'name=' + an, 'at=' + xyz(at), 'overwrite=1', NOTE)
cli('op=work', 'sub=model', 'persona=apex-one', 'work=' + R['host'], 'name=' + R['model'], 'source_work=' + RU['work'],
    'at=' + xyz(R['at']), 'pivot=' + xyz(R['pivot']), 'rotate=0,0,0', 'scale=1,1,1', 'overwrite=1',
    js(dict(R['meta'], spin='rudder', spin_k=RU['max_deg'], spin_min=-RU['max_deg'], spin_max=RU['max_deg'], spin_lag=0.3)), NOTE)

T = PL['tiller']
subwork(TI['work'], TI['title'], os.path.join(design, 'masks', 'rudder', 'tiller.vox.txt'))
for an, at in T['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=apex-one', 'work=' + TI['work'], 'name=' + an, 'at=' + xyz(at), 'overwrite=1', NOTE)
cli('op=work', 'sub=model', 'persona=apex-one', 'work=' + T['host'], 'name=' + T['model'], 'source_work=' + TI['work'],
    'at=' + xyz(T['at']), 'pivot=' + xyz(T['pivot']), 'rotate=0,0,0', 'scale=1,1,1', 'overwrite=1', js(T['meta']), NOTE)

subwork(AN['gear_work'], AN['gear_title'], os.path.join(design, 'masks', 'rudder', 'anchor_gear.vox.txt'))
cli('op=work', 'sub=link', 'persona=apex-one', 'work=' + ASM, 'name=' + AN['gear_link'], 'source_work=' + AN['gear_work'], 'at=0,0,0', NOTE, ok=(0, 2))
for a in PL['anchors']:
    s = float(a['scale'])
    cli('op=work', 'sub=model', 'persona=apex-one', 'work=' + a['host'], 'name=' + a['name'], 'source_work=' + a['work'],
        'at=' + xyz(a['at']), 'pivot=' + xyz(a['pivot']), 'rotate=0,0,' + num(float(a['rotate'])), 'scale=' + xyz([s, s, s]),
        'overwrite=1', js(a['meta']), NOTE)
for nm, at in PL['hawse'].items():
    cli('op=work', 'sub=anchor', 'persona=apex-one', 'work=' + HULL, 'name=' + nm, 'at=' + xyz(at), 'overwrite=1', NOTE)
print('✓ 舵、舵柄、錨 %d、hawse %d' % (len(PL['anchors']), len(PL['hawse'])))
