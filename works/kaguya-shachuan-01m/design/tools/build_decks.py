# 出處：kaguya-guineaman-01m/design/tools/build_decks.py（改寫供沙船步驟 5 落格）
# 建甲板／梯子／空艙房子作品、貼清單、梯子點與艙房固定點、關聯與甲板 meta（kind=deck、level、floor、thick）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'kaguya-shachuan-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
KEYS = list(plan['decks_build']['spans'])
TITLE = plan['decks_build']['names']
META = json.load(open(os.path.join(design, 'decks_meta.json'), encoding='utf-8'))
pts = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def make(work, title):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=kaguya', 'work=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=288,192,288', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=kaguya', 'work=' + work, 'meters_per_voxel=0.1')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=kaguya', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  stampvox %s：%d' % (os.path.basename(path), n))


for k in KEYS:
    w = f'{HULL}-deck-{k}'
    if make(w, '沙船 甲板 ' + TITLE[k]):
        stamp(w, os.path.join(design, 'masks', 'decks', k + '.vox.txt'))

ups = sorted({v['up'] for v in pts.values()})
for k in ups:
    w = f'{HULL}-ladders-{k}'
    if make(w, '沙船 梯子（上到%s）' % TITLE[k]):
        stamp(w, os.path.join(design, 'masks', 'ladders', k + '.vox.txt'))
        for nm, v in sorted(pts.items()):
            if v['up'] != k:
                continue
            for pk in ('foot', 'lo', 'hi', 'head'):
                x, y, z = v['points'][pk]
                cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + w, 'name=%s.%s' % (nm, pk), 'at=%d,%d,%d' % (x, y, z),
                    'note=梯子點（draft_decks.py）')

# 貨艙與舵艙（空艙房 sub-works，kind=rooms）
for rk, rv in plan['decks_build']['rooms'].items():
    rw = f"{HULL}-{rv['work_suffix']}"
    if make(rw, f"沙船 空艙房（{rv['name']}）"):
        nm = rv['name']
        cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + rw, 'name=%s.min' % nm, 'at=%d,%d,%d' % (rv['x0'], rv['y0'], rv['z0']), 'note=空艙房下角')
        cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + rw, 'name=%s.max' % nm, 'at=%d,%d,%d' % (rv['x1'], rv['y1'], rv['z1']), 'note=空艙房上角')
        dx, dy, dz = rv['door']
        cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + rw, 'name=%s.door' % nm, 'at=%d,%d,%d' % (dx, dy, dz), 'note=空艙房門口')
    cli('op=work', 'sub=link', 'persona=kaguya', 'work=%s-deck-%s' % (HULL, rv['deck']), 'name=艙房', 'source_work=' + rw, 'at=0,0,0',
        'meta={"kind":"rooms"}', 'note=步驟 5：貨艙與舵艙', ok=(0, 2))

for k in ups:
    cli('op=work', 'sub=link', 'persona=kaguya', 'work=%s-deck-%s' % (HULL, k), 'name=梯子', 'source_work=%s-ladders-%s' % (HULL, k), 'at=0,0,0',
        'meta={"kind":"ladders"}', 'note=步驟 5：梯子', ok=(0, 2))

for k in KEYS:
    cli('op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=甲板-' + k, 'source_work=%s-deck-%s' % (HULL, k), 'at=0,0,0',
        'meta=' + json.dumps(META[k], ensure_ascii=False), 'note=步驟 5', ok=(0, 2))

print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-20:]))
