# 拉貝爾號 步驟 16 補做（TASK-0965）落格：照 fit_placement.json（draft_fit.py 產生）
#   · 艙蓋：每片一件小子作品（貼＋固定點 hinge-a／hinge-b）⇒ 主甲板子作品裡的模型（meta kind=door）
#   · 廚房：主甲板子作品裡的模型「爐灶」換位置、meta kind=galley（deco 刪掉）
#   · 絞盤：子作品（貼）⇒ 組裝件關聯「絞盤」
#   · 艙房：子作品（艙壁，貼＋固定點 <房名>.min／max／door）⇒ 貨艙地板子作品裡的關聯「艙房」（meta kind=rooms）
#   · 下桅繩梯：橫繩組照 rigging_plan.json 原樣重下＋climb=1 foot= head=
#   用法：python -I -X utf8 tools/build_fit.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼（之後改格子走 delta_apply）；關聯同名 ⇒ 交給 CLI（ok 2）＋ sub=meta 合併；模型 overwrite=1
#   出處：tools/build_gear.py（本船步驟 10，cli／subwork 的寫法）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'ame-labelle-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
PL = json.load(open(os.path.join(design, 'fit_placement.json'), encoding='utf-8'))
RIG = {r['name']: r for r in json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))['ratline_sets']}
NOTE = 'note=步驟 16 補做（TASK-0965；draft_fit.py）'


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
    return json.dumps(o, ensure_ascii=False, separators=(',', ':'))


def subwork(w, title, mask, size):
    if os.path.exists(os.path.join(WORKS, w, 'work.json')):
        return
    cli('op=work', 'sub=create', 'persona=ame', 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=' + ','.join(map(str, size)), 'tags=sub')
    cli('op=work', 'sub=update', 'persona=ame', 'work=' + w, 'meters_per_voxel=0.1')
    path = os.path.join(design, mask)
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=ame', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        print(out[-1500:])
        raise SystemExit('✗ placed ≠ %d（%s）' % (n, w))
    print('✓ 建立 %s（%d 格）' % (w, n))


def anchors(w, pts):
    for an, at in sorted(pts.items()):
        cli('op=work', 'sub=anchor', 'persona=ame', 'work=' + w, 'name=' + an, 'at=' + xyz(at), 'overwrite=1', NOTE)


def link(host, name, w, meta=None, at=(0, 0, 0)):
    args = ['op=work', 'sub=link', 'persona=ame', 'work=' + host, 'name=' + name, 'source_work=' + w, 'at=' + xyz(at), NOTE]
    if meta:
        args.append('meta=' + js(meta))
    cli(*args, ok=(0, 2))
    if meta:
        cli('op=work', 'sub=meta', 'persona=ame', 'work=' + host, 'part=link', 'name=' + name, 'meta=' + js(meta))


def model(host, name, w, at, pivot, scale, rotate, meta):
    cli('op=work', 'sub=model', 'persona=ame', 'work=' + host, 'name=' + name, 'source_work=' + w, 'at=' + xyz(at), 'pivot=' + xyz(pivot),
        'rotate=0,0,' + num(float(rotate)), 'scale=' + xyz([scale] * 3), 'overwrite=1', 'meta=' + js(meta), NOTE)
    print('✓ 模型 %s/%s' % (host, name))


for h in PL['hatches']:
    subwork(h['work'], h['title'], h['mask'], h['size'])
    if h.get('link'):                                      # 封死、走得過去的蓋子：關聯（格子）；v1 當門的那一版要先 unmodel、子作品 delta_apply（notes 步驟 16）
        link(h['host'], h['name'], h['work'], at=h['at'])
        continue
    anchors(h['work'], h['anchors'])
    model(h['host'], h['name'], h['work'], h['at'], [0, 0, 0], 1.0, 0, h['meta'])
g = PL['galley']
model(g['host'], g['name'], g['work'], g['at'], g['pivot'], float(g['scale']), g['rotate'], g['meta'])
w = PL['windlass']
subwork(w['work'], w['title'], w['mask'], [352, 160, 256])
link(ASM, w['link'], w['work'])
r = PL['room']
subwork(r['work'], r['title'], r['mask'], [352, 160, 256])
anchors(r['work'], r['anchors'])
link(r['host'], r['link'], r['work'], r['meta'])
for c in PL['ratlines']:
    R = RIG[c['name']]
    cli('op=work', 'sub=ratlines', 'persona=ame', 'work=' + ASM, 'name=' + R['name'], 'rope_a=' + R['rope_a'], 'rope_b=' + R['rope_b'],
        'step=%g' % R['step'], 'start=%g' % R['start'], 'stop=%g' % R['stop'], 'min_span=%g' % R['min_span'], 'thickness=%g' % R['thickness'],
        'color=#2b2620', 'group=' + R['group'], 'climb=1', 'foot=' + xyz(c['foot']), 'head=' + xyz(c['head']), 'overwrite=1')
    print('✓ 繩梯 %s' % c['name'])
