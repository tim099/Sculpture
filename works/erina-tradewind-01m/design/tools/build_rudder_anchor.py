# 出處：erina-oxford-01m/design/tools/build_rudder_anchor.py（TASK-1097 牛津號；TASK-1097 抄來改成信風號 brig）
# 來源：calli-cosecha-01m/design/tools/build_rudder_anchor.py（照抄後改：HULL、persona erina、框；舵的 meta 加 spin（Ship_Helm §9.8.1））
# 階段九半落格：舵子作品（貼＋固定點 stock-top）＋ 組裝件的舵模型（meta kind=rudder、鉸鏈）；錨架子作品（貼＋關聯 錨架）＋ 兩隻錨模型（掛在錨架裡）；船殼固定點 hawse-S／P
#   用法：python -I -X utf8 tools/build_rudder_anchor.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼（改格子走 delta_apply）；關聯同名 ⇒ ok 2；模型與固定點 overwrite=1
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'erina-tradewind-01m'
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
    cli('op=work', 'sub=create', 'persona=erina', 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=448,192,384', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=erina', 'work=' + w, 'meters_per_voxel=0.1')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=erina', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
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
R['meta'].update({'spin': 'rudder', 'spin_k': md, 'spin_min': -md, 'spin_max': md, 'spin_lag': 0.3})     # Ship_Helm §9.8.1：舵跟著舵令轉
subwork(RU['work'], RU['title'], os.path.join(design, 'masks', 'rudder', 'rudder.vox.txt'))
for an, at in R['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=erina', 'work=' + RU['work'], 'name=' + an, 'at=' + xyz(at), 'overwrite=1', 'note=舵頭（遊戲在它旁邊 8 格內找掛住的船尾格；造船規格 §9 rudder）')
cli('op=work', 'sub=model', 'persona=erina', 'work=' + R['host'], 'name=' + R['model'], 'source_work=' + RU['work'], 'at=' + xyz(R['at']), 'pivot=' + xyz(R['pivot']),
    'rotate=0,0,0', 'scale=1,1,1', 'overwrite=1', meta(R['meta']), 'note=步驟 11（TASK-1097）：舵（at ＝ pivot ＝ 鉸鏈下端 ⇒ 子作品的世界座標原樣）')
subwork(AN['gear_work'], AN['gear_title'], os.path.join(design, 'masks', 'rudder', 'anchor_gear.vox.txt'))
cli('op=work', 'sub=link', 'persona=erina', 'work=' + ASM, 'name=' + AN['gear_link'], 'source_work=' + AN['gear_work'], 'at=0,0,0', 'note=步驟 11（TASK-1097）', ok=(0, 2))
for a in PL['anchors']:
    s = float(a['scale'])
    cli('op=work', 'sub=model', 'persona=erina', 'work=' + a['host'], 'name=' + a['name'], 'source_work=' + a['work'], 'at=' + xyz(a['at']), 'pivot=' + xyz(a['pivot']),
        'rotate=0,0,' + num(float(a['rotate'])), 'scale=' + xyz([s, s, s]), 'overwrite=1', meta(a['meta']), 'note=步驟 11（TASK-1097）：共用錨元件、吊在船頭舷外、錨冠落在 billboard 上')
for nm, at in PL['hawse'].items():
    cli('op=work', 'sub=anchor', 'persona=erina', 'work=' + HULL, 'name=' + nm, 'at=' + xyz(at), 'overwrite=1', 'note=錨鏈孔（步驟 11 TASK-1097；只登記固定點、沒有開孔）')
# 舵柄：船尾舷牆的 helm port（船殼那幾格 carvevox 帶顏色守門）⇒ 舵柄子作品（貼＋固定點 spin-a／b）⇒ 後甲板子作品的舵柄模型（kind=tiller）
T = PL['tiller']
hp = os.path.join(design, 'masks', 'rudder', 'helm_port_hull.vox.txt')
marks = json.load(open(os.path.join(WORKS, HULL, 'marks.json'), encoding='utf-8')) if os.path.exists(os.path.join(WORKS, HULL, 'marks.json')) else {}
if 'helm port' not in json.dumps(marks, ensure_ascii=False):
    n = sum(1 for l in open(hp, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=carvevox', 'persona=erina', 'work=' + HULL, 'voxels=' + os.path.abspath(hp).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n)
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        print(out[-1500:])
        raise SystemExit('✗ helm port carved ≠ %d' % n)
    cli('op=work', 'sub=mark', 'persona=erina', 'work=' + HULL, 'name=helm port', 'note=步驟 11（TASK-1097）：舵柄穿過船尾舷牆的小口 %d 格（由舵柄填滿）' % n)
    print('✓ helm port 刻 %d' % n)
subwork(T['work'], '信風號 舵柄（tiller，0.1 m）', os.path.join(design, 'masks', 'rudder', 'tiller.vox.txt'))
for an, at in T['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=erina', 'work=' + T['work'], 'name=' + an, 'at=' + xyz(at), 'overwrite=1', 'note=舵柄繞舵軸轉（spin-a → spin-b；Ship_Helm §9.8）')
cli('op=work', 'sub=model', 'persona=erina', 'work=' + T['host'], 'name=' + T['model'], 'source_work=' + T['work'], 'at=' + xyz(T['at']), 'pivot=' + xyz(T['pivot']),
    'rotate=0,0,0', 'scale=1,1,1', 'overwrite=1', meta(T['meta']), 'note=步驟 11（TASK-1097）：舵柄（at ＝ pivot ⇒ 子作品的世界座標原樣；操舵鏈 kind=tiller）')
print('✓ 舵模型、舵柄、錨 %d、hawse %d' % (len(PL['anchors']), len(PL['hawse'])))
