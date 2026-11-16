# 塔爾塔納 步驟 6（TASK-1299）：建立 stern-glass 關聯（material=glass）與 3 件可隱藏外部裝飾模型（deco=1）
#   用法：python -I -X utf8 tools/build_deco.py <design>
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'apex-one-tartane-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
spec = json.load(open(os.path.join(design, 'deco_spec.json'), encoding='utf-8'))['parts']


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def make(work, title, size_str, parent=HULL):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=apex-one', 'id=' + work, 'title=' + title, 'parent_work=' + parent, 'size=' + size_str)
    cli('op=work', 'sub=update', 'persona=apex-one', 'work=' + work, 'meters_per_voxel=0.1', 'tags=sub')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=apex-one', 'work=' + work,
              'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        raise SystemExit('✗ placed %s != %d (%s)' % (got, n, work))
    print('  stampvox %s: %d' % (os.path.basename(path), n))


# 1. 船尾窗玻璃（1 格厚、material=glass、不標 deco）
w_glass = HULL + '-stern-glass'
if make(w_glass, '塔爾塔納 船尾窗玻璃', '360,192,320'):
    stamp(w_glass, os.path.join(design, 'masks', 'deco', 'stern_glass.vox.txt'))
cli('op=work', 'sub=link', 'persona=apex-one', 'work=' + ASM, 'name=窗玻璃-船尾',
    'source_work=' + w_glass, 'at=0,0,0', 'meta={"material":"glass"}',
    'note=步驟 6：三扇船尾窗玻璃（Ship_Materials）', ok=(0, 2))

# 2. 三件外部裝飾模型（deco=1）
TITLES = {
    'beak': ('deco-船首像', '塔爾塔納 船首喙與雕首像'),
    'gallery': ('deco-船尾陽台', '塔爾塔納 船尾陽台與假艉廊'),
    'nameplate': ('deco-船名牌', '塔爾塔納 船尾船名牌 LUCIA'),
}
for nm in ('beak', 'gallery', 'nameplate'):
    info = spec[nm]
    mname, title = TITLES[nm]
    w = '%s-deco-%s' % (HULL, nm)
    sz = '%d,%d,%d' % tuple(info['box'])
    if make(w, title, sz):
        stamp(w, os.path.join(design, 'masks', 'deco', nm + '.vox.txt'))
    at_str = '%d,%d,%d' % tuple(info['at'])
    cli('op=work', 'sub=model', 'persona=apex-one', 'work=' + ASM, 'name=' + mname,
        'source_work=' + w, 'pivot=0,0,0', 'at=' + at_str, 'scale=1', 'rotate=0,0,0',
        'meta={"deco":1}', 'note=步驟 6 可隱藏裝飾', ok=(0, 2))

print(cli('op=work', 'sub=models', 'work=' + ASM))
