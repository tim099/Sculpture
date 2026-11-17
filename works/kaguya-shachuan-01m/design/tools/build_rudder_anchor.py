# 出處：kaguya-guineaman-01m/design/tools/build_rudder_anchor.py
# 沙船 步驟 11（TASK-1313）：中式開孔升降舵＋stock-top、舵柄＋helm port＋spin-a/b、錨架＋四爪鐵錨 ×2＋hawse-S/P
#   用法：python -I -X utf8 tools/build_rudder_anchor.py <design>
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'kaguya-shachuan-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
RB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['rudder_anchor_build']
PL = json.load(open(os.path.join(design, 'rudder_anchor_placement.json'), encoding='utf-8'))


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


def subwork(w, title, path):
    if os.path.exists(os.path.join(WORKS, w, 'work.json')):
        return
    cli('op=work', 'sub=create', 'persona=kaguya', 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=288,192,288', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=kaguya', 'work=' + w, 'meters_per_voxel=0.1')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=kaguya', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        print(out[-1500:])
        raise SystemExit('✗ placed ≠ %d（%s）' % (n, w))
    print('✓ 建立 %s（%d 格）' % (w, n))


def meta(d):
    return 'meta=' + json.dumps(d, ensure_ascii=False, separators=(',', ':'))


RU, AN = RB['rudder'], RB['anchor']
R = PL['rudder']
md = RU['max_deg']
R['meta'].update({'spin': 'rudder', 'spin_k': md, 'spin_min': -md, 'spin_max': md, 'spin_lag': 0.3})
subwork(RU['work'], RU['title'], os.path.join(design, 'masks', 'rudder', 'rudder.vox.txt'))
for an, at in R['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + RU['work'], 'name=' + an, 'at=' + xyz(at), 'overwrite=1', 'note=舵頭（Ship_Game §9 rudder stock-top）')
cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + R['host'], 'name=' + R['model'], 'source_work=' + RU['work'], 'at=' + xyz(R['at']), 'pivot=' + xyz(R['pivot']),
    'rotate=0,0,0', 'scale=1,1,1', 'overwrite=1', meta(R['meta']), 'note=步驟 11（TASK-1313）：中式開孔升降舵')

subwork(AN['gear_work'], AN['gear_title'], os.path.join(design, 'masks', 'rudder', 'anchor_gear.vox.txt'))
cli('op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=' + AN['gear_link'], 'source_work=' + AN['gear_work'], 'at=0,0,0', 'note=步驟 11（TASK-1313）', ok=(0, 2))
for a in PL['anchors']:
    s = float(a['scale'])
    cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + a['host'], 'name=' + a['name'], 'source_work=' + a['work'], 'at=' + xyz(a['at']), 'pivot=' + xyz(a['pivot']),
        'rotate=0,0,' + num(float(a['rotate'])), 'scale=' + xyz([s, s, s]), 'overwrite=1', meta(a['meta']), 'note=步驟 11（TASK-1313）：共用四爪鐵錨元件、吊在方艏舷外')
for nm, at in PL['hawse'].items():
    cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + HULL, 'name=' + nm, 'at=' + xyz(at), 'overwrite=1', 'note=錨鏈孔（步驟 11 TASK-1313）')

T = PL['tiller']
hp = os.path.join(design, 'masks', 'rudder', 'helm_port_hull.vox.txt')
marks = json.load(open(os.path.join(WORKS, HULL, 'marks.json'), encoding='utf-8')) if os.path.exists(os.path.join(WORKS, HULL, 'marks.json')) else {}
if 'helm port' not in json.dumps(marks, ensure_ascii=False):
    n = sum(1 for l in open(hp, encoding='utf-8') if l.strip() and not l.startswith('#'))
    if n > 0:
        out = cli('op=carvevox', 'persona=kaguya', 'work=' + HULL, 'voxels=' + os.path.abspath(hp).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n)
        m = re.search(r'(?:placed|carved|removed)\D{0,12}(\d[\d,]*)', out)
        if not m or int(m.group(1).replace(',', '')) != n:
            print(out[-1500:])
            raise SystemExit('✗ helm port carved ≠ %d' % n)
    cli('op=work', 'sub=mark', 'persona=kaguya', 'work=' + HULL, 'name=helm port', 'note=步驟 11（TASK-1313）：舵柄穿過尾樓尾板小口 %d 格' % n)
    print('✓ helm port 刻 %d' % n)

subwork(T['work'], '沙船 舵柄（tiller，0.1 m）', os.path.join(design, 'masks', 'rudder', 'tiller.vox.txt'))
for an, at in T['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + T['work'], 'name=' + an, 'at=' + xyz(at), 'overwrite=1', 'note=舵柄繞舵軸轉（spin-a → spin-b；Ship_Helm §9.8）')
cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + T['host'], 'name=' + T['model'], 'source_work=' + T['work'], 'at=' + xyz(T['at']), 'pivot=' + xyz(T['pivot']),
    'rotate=0,0,0', 'scale=1,1,1', 'overwrite=1', meta(T['meta']), 'note=步驟 11（TASK-1313）：舵柄（kind=tiller, spin=rudder）')
print('✓ 舵模型、舵柄、錨 %d、hawse %d' % (len(PL['anchors']), len(PL['hawse'])))
