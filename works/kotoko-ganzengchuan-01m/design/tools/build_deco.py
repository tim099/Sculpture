# 福建趕繒船 步驟 6 落格與外部裝飾安裝（TASK-1314）：
#   1. 船尾窗玻璃（stern-glass，關聯 meta={"material":"glass"}）
#   2. 高尾陽台欄杆（stern-balcony，關聯結構）
#   3. 船首龍獅彩雕（deco-bow，外部模型 deco=1）
#   4. 高尾翔龍牌飾（deco-stern，外部模型 deco=1）
#   5. 四具護舷（複用 kiara-tunis-sandal-01m-fender，外部模型 deco=1）
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

PERSONA = 'kotoko'
HULL = 'kotoko-ganzengchuan-01m'
ASM = HULL + '-assembly'


def cli(*args, ok=(0,)):
    cmd = ['senate', 'cmd', 'sculpture']
    for kv in args:
        cmd += ['--arg', kv]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit(f'✗ exit {r.returncode}：{" ".join(args)}')
    return out


def ensure_work(works_root, work_id, title, size):
    if os.path.exists(os.path.join(works_root, work_id, 'work.json')):
        print('· 已有子作品（跳過建立）：', work_id)
        return False
    cli('op=work', 'sub=create', f'persona={PERSONA}', f'id={work_id}', f'title={title}', f'parent_work={HULL}', f'size={size}')
    cli('op=work', 'sub=update', f'persona={PERSONA}', f'work={work_id}', 'tags=sub', 'meters_per_voxel=0.1')
    print('✓ 建立子作品：', work_id, size)
    return True


def stamp(work_id, vox_path):
    n = sum(1 for l in open(vox_path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    p_norm = os.path.abspath(vox_path).replace('\\', '/')
    out = cli('op=stampvox', f'persona={PERSONA}', f'work={work_id}', f'voxels={p_norm}', 'at=0,0,0', f'expect_pixels={n}')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        raise SystemExit(f'✗ placed {got} != {n} ({work_id})')
    print(f'  stampvox {os.path.basename(vox_path)} -> {work_id}：{n} 格')


def main():
    design = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..'))
    works_root = os.path.dirname(os.path.dirname(design))
    P = json.load(open(os.path.join(design, 'deco_placement.json'), encoding='utf-8'))

    # 1. 船尾窗玻璃（link, material=glass，不寫 render）
    w_glass = f'{HULL}-stern-glass'
    if ensure_work(works_root, w_glass, '福建趕繒船 船尾窗玻璃（0.1 m）', '384,192,384'):
        stamp(w_glass, os.path.join(design, 'masks', 'deco', 'stern_glass.vox.txt'))
    cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}', 'name=船尾窗玻璃', f'source_work={w_glass}',
        'at=0,0,0', 'meta={"material":"glass"}', 'note=步驟 6：兩扇花格艉窗玻璃（Ship_Materials）')

    # 2. 高尾懸挑陽台與望樓欄杆（link，結構件）
    w_bal = f'{HULL}-stern-balcony'
    if ensure_work(works_root, w_bal, '福建趕繒船 尾樓陽台欄杆（0.1 m）', '384,192,384'):
        stamp(w_bal, os.path.join(design, 'masks', 'deco', 'stern_balcony.vox.txt'))
    cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}', 'name=尾樓陽台欄杆', f'source_work={w_bal}',
        'at=0,0,0', 'note=步驟 6：高尾懸挑陽台與上層望樓欄杆')

    # 3. 船首龍獅彩雕（外部模型，deco=1）
    db = P['deco_bow']
    w_bow = f'{HULL}-deco-bow'
    if ensure_work(works_root, w_bow, '福建趕繒船 船首龍獅彩雕（0.1 m）', db['size']):
        stamp(w_bow, os.path.join(design, 'masks', 'deco', 'deco_bow.vox.txt'))
    cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={ASM}', 'name=船首龍獅彩雕', f'source_work={w_bow}',
        'at=%g,%g,%g' % tuple(db['at']), 'pivot=%g,%g,%g' % tuple(db['pivot']), 'scale=1',
        'meta={"deco":1}', 'note=步驟 6：船首龍獅浪紋彩雕（deco=1）')

    # 4. 高尾翔龍牌飾（外部模型，deco=1）
    ds = P['deco_stern']
    w_stern = f'{HULL}-deco-stern'
    if ensure_work(works_root, w_stern, '福建趕繒船 高尾翔龍牌飾（0.1 m）', ds['size']):
        stamp(w_stern, os.path.join(design, 'masks', 'deco', 'deco_stern.vox.txt'))
    cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={ASM}', 'name=高尾翔龍牌飾', f'source_work={w_stern}',
        'at=%g,%g,%g' % tuple(ds['at']), 'pivot=%g,%g,%g' % tuple(ds['pivot']), 'scale=1',
        'meta={"deco":1}', 'note=步驟 6：高尾翔龍花飾匾（deco=1）')

    # 5. 兩舷護舷（複用 kiara-tunis-sandal-01m-fender，0.1 m，deco=1）
    for fd in P['fenders']:
        cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={ASM}', 'name=' + fd['name'],
            'source_work=kiara-tunis-sandal-01m-fender',
            'at=%g,%g,%g' % tuple(fd['at']), 'pivot=%g,%g,%g' % tuple(fd['pivot']),
            'rotate=%g,%g,%g' % tuple(fd['rotate']), 'scale=1',
            'meta={"deco":1}', 'note=步驟 6：複用 Sandal 護舷（deco=1）')

    print('=== models ===')
    print(cli('op=work', 'sub=models', f'work={ASM}'))
    print('=== stats (hull + balcony) ===')
    print(cli('op=stats', f'work={ASM}', 'links=船殼,尾樓陽台欄杆', 'structure=1', 'mirror=y:96'))
    print('=== stats (all links) ===')
    print(cli('op=stats', f'work={ASM}', 'links=all', 'structure=1', 'mirror=y:96'))


if __name__ == '__main__':
    main()
