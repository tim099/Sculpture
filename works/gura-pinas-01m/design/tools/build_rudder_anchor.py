# 出處：calli-cosecha-01m/design/tools/build_rudder_anchor.py（收穫號，照抄後改成藍鯊號 —— TASK-0967）
# 步驟 11 落格：舵子作品（貼＋固定點 stock-top）＋ 組裝件的舵模型（meta kind=rudder、鉸鏈）；錨架子作品（貼＋關聯 錨架）＋ 兩隻錨模型（掛在錨架裡）；船殼固定點 hawse-S／P
#   用法：python -I -X utf8 tools/build_rudder_anchor.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼（改格子走 delta_apply）；關聯同名 ⇒ ok 2；模型與固定點 overwrite=1
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'gura-pinas-01m'
ASM = HULL + '-assembly'
WORKS = os.environ.get('SCULPT_WORKS') or os.path.dirname(os.path.dirname(os.path.abspath(design)))   # worktree 只放 design/ ⇒ 作品資料讀共用的那一份
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
    cli('op=work', 'sub=create', 'persona=gura', 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=800,320,640', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=gura', 'work=' + w, 'meters_per_voxel=0.1')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=gura', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        print(out[-1500:])
        raise SystemExit('✗ placed ≠ %d（%s）' % (n, w))
    print('✓ 建立 %s（%d 格）' % (w, n))


def meta(d):
    return 'meta=' + json.dumps(d, ensure_ascii=False, separators=(',', ':'))


RU, AN = RB['rudder'], RB['anchor']
R = PL['rudder']
subwork(RU['work'], RU['title'], os.path.join(design, 'masks', 'rudder', 'rudder.vox.txt'))
for an, at in R['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + RU['work'], 'name=' + an, 'at=' + xyz(at), 'overwrite=1', 'note=舵頭（遊戲在它旁邊 8 格內找掛住的船尾格；造船規格 §9 rudder）')
cli('op=work', 'sub=model', 'persona=gura', 'work=' + R['host'], 'name=' + R['model'], 'source_work=' + RU['work'], 'at=' + xyz(R['at']), 'pivot=' + xyz(R['pivot']),
    'rotate=0,0,0', 'scale=1,1,1', 'overwrite=1', meta(R['meta']), 'note=步驟 11（TASK-0967）：舵（at ＝ pivot ＝ 鉸鏈下端 ⇒ 子作品的世界座標原樣）')
subwork(AN['gear_work'], AN['gear_title'], os.path.join(design, 'masks', 'rudder', 'anchor_gear.vox.txt'))
cli('op=work', 'sub=link', 'persona=gura', 'work=' + ASM, 'name=' + AN['gear_link'], 'source_work=' + AN['gear_work'], 'at=0,0,0', 'note=步驟 11（TASK-0967）', ok=(0, 2))
for a in PL['anchors']:
    s = float(a['scale'])
    cli('op=work', 'sub=model', 'persona=gura', 'work=' + a['host'], 'name=' + a['name'], 'source_work=' + a['work'], 'at=' + xyz(a['at']), 'pivot=' + xyz(a['pivot']),
        'rotate=0,0,' + num(float(a['rotate'])), 'scale=' + xyz([s, s, s]), 'overwrite=1', meta(a['meta']), 'note=步驟 11（TASK-0967）：共用錨元件、吊在船頭舷外、錨冠落在 billboard 上')
for nm, at in PL['hawse'].items():
    cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + HULL, 'name=' + nm, 'at=' + xyz(at), 'overwrite=1', 'note=錨鏈孔（步驟 11 TASK-0967；只登記固定點、沒有開孔）')
for h in PL.get('helm', []):                 # 藍鯊號：舵輪＋座（Ship_Helm §9.8.1：掛輪要同時掛座、擺法照抄；輪的 meta 帶 spin）
    s = float(h['scale'])
    cli('op=work', 'sub=model', 'persona=gura', 'work=' + h['host'], 'name=' + h['name'], 'source_work=' + h['work'], 'at=' + xyz(h['at']), 'pivot=' + xyz(h['pivot']),
        'rotate=0,0,' + num(float(h['rotate'])), 'scale=' + xyz([s, s, s]), 'overwrite=1', meta(h['meta']), 'note=步驟 11（TASK-0967）：沿用憲法號雙舵輪與座')
print('✓ 舵模型、錨 %d、hawse %d、舵輪與座 %d' % (len(PL['anchors']), len(PL['hawse']), len(PL.get('helm', []))))
