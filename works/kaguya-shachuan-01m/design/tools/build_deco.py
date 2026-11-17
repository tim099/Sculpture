# 出處：kaguya-guineaman-01m/design/tools/build_deco.py（改寫供沙船步驟 6 裝飾與玻璃落格）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'kaguya-shachuan-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
P = json.load(open(os.path.join(design, 'deco_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def make(work, title, size='288,192,288'):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=kaguya', 'work=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=' + size, 'tags=sub')
    cli('op=work', 'sub=update', 'persona=kaguya', 'work=' + work, 'meters_per_voxel=0.1')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=kaguya', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        raise SystemExit(f'✗ placed {got} != {n} ({work})')
    print(f'  stampvox {os.path.basename(path)}：{n}')


# 1. 船尾窗玻璃（關聯，material=glass，不寫 render）
wg = f'{HULL}-stern-glass'
if make(wg, '沙船 船尾窗玻璃（0.1 m）'):
    stamp(wg, os.path.join(design, 'masks', 'deco', 'stern_glass.vox.txt'))
cli('op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=船尾窗玻璃', 'source_work=' + wg, 'at=0,0,0',
    'meta={"material":"glass"}', 'note=步驟 6：船尾窗玻璃（Ship_Materials）', ok=(0, 2))

# 2. 披水板（外部模型，deco=1）
wl = f'{HULL}-leeboard'
if make(wl, '沙船 披水板（0.1 m）', '24,4,24'):
    stamp(wl, os.path.join(design, 'masks', 'deco', 'leeboard.vox.txt'))
for side in ('S', 'P'):
    cfg = P['leeboards'][side]
    cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + ASM, 'name=披水板-' + side, 'source_work=' + wl,
        'at=%g,%g,%g' % tuple(cfg['at']), 'pivot=%g,%g,%g' % tuple(cfg['pivot']), 'scale=1',
        'meta={"deco":1}', 'note=步驟 6：兩舷披水板', ok=(0, 2))

# 3. 方艏彩繪牌額（外部模型，deco=1）
wb = f'{HULL}-deco-bow'
if make(wb, '沙船 方艏彩繪牌額（0.1 m）', '4,18,12'):
    stamp(wb, os.path.join(design, 'masks', 'deco', 'deco_bow.vox.txt'))
db = P['deco_bow']
cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + ASM, 'name=方艏牌額', 'source_work=' + wb,
    'at=%g,%g,%g' % tuple(db['at']), 'pivot=%g,%g,%g' % tuple(db['pivot']), 'scale=1',
    'meta={"deco":1}', 'note=步驟 6：方艏彩繪牌額', ok=(0, 2))

# 4. 船尾牌飾（外部模型，deco=1）
ws = f'{HULL}-deco-stern'
if make(ws, '沙船 船尾牌飾（0.1 m）', '4,18,8'):
    stamp(ws, os.path.join(design, 'masks', 'deco', 'deco_stern.vox.txt'))
ds = P['deco_stern']
cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + ASM, 'name=船尾牌飾', 'source_work=' + ws,
    'at=%g,%g,%g' % tuple(ds['at']), 'pivot=%g,%g,%g' % tuple(ds['pivot']), 'scale=1',
    'meta={"deco":1}', 'note=步驟 6：船尾牌飾', ok=(0, 2))

# 5. 護舷（複用 kiara-tunis-sandal-01m-fender，0.1 m，deco=1）
for fd in P['fenders']:
    cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + ASM, 'name=' + fd['name'],
        'source_work=kiara-tunis-sandal-01m-fender',
        'at=%g,%g,%g' % tuple(fd['at']), 'pivot=2,1.5,2', 'rotate=%g,%g,%g' % tuple(fd['rotate']), 'scale=1',
        'meta={"deco":1}', 'note=步驟 6：複用 Sandal 護舷靠墊', ok=(0, 2))

print(cli('op=work', 'sub=models', 'work=' + ASM))
