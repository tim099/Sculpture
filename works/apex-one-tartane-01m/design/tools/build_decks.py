# 塔爾塔納 步驟 5（TASK-1299）：建立甲板／梯子／空艙房子作品、落格、固定點、關聯與 meta
#   用法：python -I -X utf8 tools/build_decks.py <design>
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'apex-one-tartane-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
ROWS = plan['decks']['rows']
TITLE = {r['key']: r['name'].split('（')[0] for r in ROWS}


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def make(work, title, parent=HULL):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=apex-one', 'id=' + work, 'title=' + title, 'parent_work=' + parent, 'size=360,192,320')
    cli('op=work', 'sub=update', 'persona=apex-one', 'work=' + work, 'meters_per_voxel=0.1', 'tags=sub')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    if n == 0:
        return
    out = cli('op=stampvox', 'persona=apex-one', 'work=' + work,
              'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s != %d (%s)' % (got, n, work))
    print('  stampvox %s: %d' % (os.path.basename(path), n))


pts = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
rooms = json.load(open(os.path.join(design, 'rooms_spec.json'), encoding='utf-8'))
ups = sorted({v['up'] for v in pts.values()})

for r in ROWS:
    k = r['key']
    w = '%s-deck-%s' % (HULL, k)
    if make(w, '塔爾塔納 甲板 ' + TITLE[k]):
        stamp(w, os.path.join(design, 'masks', 'decks', k + '.vox.txt'))

for k in ups:
    w = '%s-ladders-%s' % (HULL, k)
    if make(w, '塔爾塔納 梯子（上到%s）' % TITLE[k]):
        stamp(w, os.path.join(design, 'masks', 'ladders', k + '.vox.txt'))
        for nm, v in sorted(pts.items()):
            if v['up'] != k:
                continue
            for pk in ('foot', 'lo', 'hi', 'head'):
                x, y, z = v['points'][pk]
                cli('op=work', 'sub=anchor', 'persona=apex-one', 'work=' + w, 'name=%s.%s' % (nm, pk),
                    'at=%d,%d,%d' % (x, y, z), 'note=步驟 5 梯子點（站腳那一格）')

w_rooms = '%s-rooms-cabin' % HULL
if make(w_rooms, '塔爾塔納 尾艙空艙房', parent='%s-deck-cabin' % HULL):
    for rname, rbox in sorted(rooms.items()):
        for pk in ('min', 'max', 'door'):
            x, y, z = rbox[pk]
            cli('op=work', 'sub=anchor', 'persona=apex-one', 'work=' + w_rooms, 'name=%s.%s' % (rname, pk),
                'at=%d,%d,%d' % (x, y, z), 'note=步驟 5 空艙房框點（純空氣）')

for k in ups:
    cli('op=work', 'sub=link', 'persona=apex-one', 'work=%s-deck-%s' % (HULL, k),
        'name=梯子', 'source_work=%s-ladders-%s' % (HULL, k), 'at=0,0,0',
        'meta={"kind":"ladders"}', 'note=步驟 5：從下一層上來的梯子', ok=(0, 2))

cli('op=work', 'sub=link', 'persona=apex-one', 'work=%s-deck-cabin' % HULL,
    'name=艙房', 'source_work=' + w_rooms, 'at=0,0,0',
    'meta={"kind":"rooms"}', 'note=步驟 5：尾艙空艙房（stern_cabin）', ok=(0, 2))

for r in ROWS:
    k = r['key']
    cli('op=work', 'sub=link', 'persona=apex-one', 'work=' + ASM,
        'name=甲板-' + k, 'source_work=%s-deck-%s' % (HULL, k), 'at=0,0,0',
        'note=步驟 5 甲板子作品', ok=(0, 2))

cli('op=work', 'sub=meta', 'persona=apex-one', 'work=' + ASM, 'part=link',
    'file=' + os.path.abspath(os.path.join(design, 'decks_meta.tsv')).replace('\\', '/'))

print(cli('op=work', 'sub=links', 'work=' + ASM))
