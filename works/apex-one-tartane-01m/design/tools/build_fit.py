# 塔爾塔納 步驟 10（TASK-1299）落格：照 fit_placement.json 建立艙蓋＋小艇架並掛載所有甲板與貨艙模型
#   用法：python -I -X utf8 tools/build_fit.py <design>
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'apex-one-tartane-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
PL = json.load(open(os.path.join(design, 'fit_placement.json'), encoding='utf-8'))
NOTE = 'note=步驟 10（TASK-1299；draft_fit.py）'


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
    cli('op=work', 'sub=create', 'persona=apex-one', 'id=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=' + ','.join(map(str, size)))
    cli('op=work', 'sub=update', 'persona=apex-one', 'work=' + w, 'meters_per_voxel=0.1', 'tags=sub')
    path = os.path.join(design, mask)
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=apex-one', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        print(out[-1500:])
        raise SystemExit('✗ placed ≠ %d（%s）' % (n, w))
    print('✓ 建立 %s（%d 格）' % (w, n))


def model(host, name, w, at, pivot, scale, rotate, meta):
    cli('op=work', 'sub=model', 'persona=apex-one', 'work=' + host, 'name=' + name, 'source_work=' + w,
        'at=' + xyz(at), 'pivot=' + xyz(pivot), 'rotate=0,0,' + num(float(rotate)),
        'scale=' + xyz([scale] * 3), 'overwrite=1', 'meta=' + js(meta), NOTE)


h = PL['hatch']
subwork(h['work'], h['title'], h['mask'], h['size'])
for an, pt in sorted(h['anchors'].items()):
    cli('op=work', 'sub=anchor', 'persona=apex-one', 'work=' + h['work'], 'name=' + an, 'at=' + xyz(pt), 'overwrite=1', NOTE)
model(h['host'], h['name'], h['work'], h['at'], [0, 0, 0], 1.0, 0, h['meta'])
print('✓ 艙蓋 %s/%s' % (h['host'], h['name']))

s = PL['skids']
subwork(s['work'], s['title'], s['mask'], [360, 192, 320])
cli('op=work', 'sub=link', 'persona=apex-one', 'work=' + ASM, 'name=' + s['link'], 'source_work=' + s['work'], 'at=0,0,0', NOTE, ok=(0, 2))
print('✓ 小艇架 %s' % s['link'])

for m in PL['models']:
    model(m['host'], m['name'], m['work'], m['at'], m['pivot'], float(m['scale']), m['rotate'], m['meta'])
print('✓ 模型 %d 件' % len(PL['models']))
