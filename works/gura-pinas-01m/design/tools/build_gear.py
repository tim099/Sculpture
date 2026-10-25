# 出處：calli-cosecha-01m/design/tools/build_gear.py（收穫號，照抄後改成藍鯊號 —— TASK-0967）
# 階段九落格：彈藥庫子作品（貼＋固定點 blast／door、組裝件關聯 彈藥庫 meta kind=magazine）、小艇架子作品（貼＋關聯 小艇架）、
#   模型（火藥桶掛在彈藥庫子作品裡；舵輪／羅經櫃掛 deck-alcazar、絞盤／小艇掛 deck-puente）
#   用法：python -I -X utf8 tools/build_gear.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼（之後改格子走 delta_apply）；關聯同名 ⇒ 交給 CLI（ok 2）；模型 overwrite=1
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'gura-pinas-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
GB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['gear_build']
PL = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))


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


def subwork(spec, path, anchors=None, meta=None):
    w = spec['work']
    if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
        cli('op=work', 'sub=create', 'persona=gura', 'work=' + w, 'title=' + spec['title'], 'parent_work=' + HULL, 'size=800,320,640', 'tags=sub')
        cli('op=work', 'sub=update', 'persona=gura', 'work=' + w, 'meters_per_voxel=0.1')
        n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
        out = cli('op=stampvox', 'persona=gura', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
        m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
        if not m or int(m.group(1).replace(',', '')) != n:
            print(out[-1500:])
            raise SystemExit('✗ placed ≠ %d（%s）' % (n, w))
        print('✓ 建立 %s（%d 格）' % (w, n))
    for an, at in sorted((anchors or {}).items()):
        cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + w, 'name=' + an, 'at=' + xyz(at), 'overwrite=1', 'note=draft_gear.py（階段九）')
    args = ['op=work', 'sub=link', 'persona=gura', 'work=' + ASM, 'name=' + spec['link'], 'source_work=' + w, 'at=0,0,0', 'note=階段九（TASK-0598）']
    if meta:
        args.append('meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
    cli(*args, ok=(0, 2))
    if meta:      # 關聯已在（上面 ok 2）也要把 meta 合併上去 ⇒ sub=meta part=link（⛔ 不吞錯）
        cli('op=work', 'sub=meta', 'persona=gura', 'work=' + ASM, 'part=link', 'name=' + spec['link'], 'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')))


subwork(GB['magazine'], os.path.join(design, 'masks', 'gear', 'magazine.vox.txt'), PL['magazine']['anchors'], PL['magazine']['meta'])
subwork(GB['skids'], os.path.join(design, 'masks', 'gear', 'skids.vox.txt'))
ok = bad = 0
for r in PL['models']:
    s = float(r['scale'])
    note = '階段九（TASK-0598；draft_gear.py）' + ('；火藥桶 第 %d 層' % r['tier'] if 'tier' in r else '')
    p = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in ['op=work', 'sub=model', 'persona=gura', 'work=' + r['host'], 'name=' + r['name'], 'source_work=' + r['work'],
                        'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=0,0,' + num(float(r['rotate'])), 'scale=' + xyz([s, s, s]), 'overwrite=1',
                        'meta=' + json.dumps(r['meta'], ensure_ascii=False, separators=(',', ':')), 'note=' + note] for a in ('--arg', kv)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        bad += 1
        print('✗', r['name'], (p.stdout + p.stderr)[-400:])
    else:
        ok += 1
print('模型 ok %d／bad %d（設計 %d）' % (ok, bad, len(PL['models'])))
print('\n'.join(l for l in cli('op=work', 'sub=links', 'work=' + ASM).splitlines() if '彈藥庫' in l or '小艇架' in l))
