# 出處：kaguya-guineaman-01m/design/tools/build_masts.py（改寫供沙船步驟 7 落格與 meta 綁定）
# 建立三桅子作品、6 根帆桁子作品（pivot/aft/fore/sling 固定點）、將帆桁模型掛進對應桅子作品、將桅關聯進組裝件並標 kind=mast
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'kaguya-shachuan-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
YP = json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))

MAST_NAMES = {'fore': '頭桅', 'main': '大桅', 'mizzen': '尾桅'}


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


# 1. 建三根桅（tags=sub, meters_per_voxel=0.1）＋固定點 head/heel
for mk, mv in YP['masts'].items():
    mw = f'{HULL}-mast-{mk}'
    if make(mw, f'沙船 {MAST_NAMES[mk]}（0.1 m）'):
        stamp(mw, os.path.join(design, 'masks', 'masts', f'mast_{mk}.vox.txt'))
        for ak, (ax, ay, az) in mv['anchors'].items():
            cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + mw, 'name=' + ak, 'at=%d,%d,%d' % (ax, ay, az), 'note=步驟 7：桅固定點')

# 2. 建 6 根帆桁子作品 ＋ 固定點 pivot/aft/fore/sling，再掛成對應桅子作品的外部模型
for yk, yv in YP['yards'].items():
    yw = f'{HULL}-yard-{yk.replace("_", "-")}'
    bx, by, bz = yv['box']
    if make(yw, f'沙船 帆桁 {yk}（0.1 m）', f'{bx},{by},{bz}'):
        stamp(yw, os.path.join(design, 'masks', 'masts', f'yard_{yk}.vox.txt'))
        for ak, (ax, ay, az) in yv['anchors'].items():
            cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + yw, 'name=' + ak, 'at=%d,%d,%d' % (ax, ay, az), 'note=步驟 7：帆桁固定點')
    mw = f'{HULL}-mast-{yv["on"]}'
    meta_y = {
        'kind': 'yard',
        'mast': yv['on'],
        'yard': yv['kind'],
        'sail': yv['sail'],
        'length_ft': yv['length_ft'],
        'diameter_in': yv['diameter_in'],
        'pivot_anchor': 'pivot',
        'turn_axis': 'z',
        'rotate_z_deg': 0,
    }
    cli('op=work', 'sub=model', 'persona=kaguya', 'work=' + mw, 'name=yard-' + yk.replace('_', '-'),
        'source_work=' + yw, 'at=%g,%g,%g' % tuple(yv['at']), 'pivot=%g,%g,%g' % tuple(yv['pivot']),
        'rotate=0,0,0', 'scale=1', 'meta=' + json.dumps(meta_y, ensure_ascii=False), 'note=步驟 7：硬篷帆桁', ok=(0, 2))

# 3. 將三根桅關聯進組裝件（turn=0, mirror=none, meta kind=mast + mast=<mk>）
for mk in ('fore', 'main', 'mizzen'):
    mw = f'{HULL}-mast-{mk}'
    meta_m = {'kind': 'mast', 'mast': mk}
    cli('op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=桅-' + mk, 'source_work=' + mw, 'at=0,0,0',
        'meta=' + json.dumps(meta_m, ensure_ascii=False), 'note=步驟 7：下桅綁定', ok=(0, 2))

print(cli('op=work', 'sub=links', 'work=' + ASM))
