# 福建趕繒船 步驟 10 落格與甲板物件掛載（TASK-1314）：
#   1. 彈藥庫（底艙艉端銅襯＋blast/door 固定點＋4 具 100 lb 火藥桶＋hoist 指向三層梯子）
#   2. 主艙口木格柵艙蓋（0.05 m 子作品，scale 0.5, open=up）
#   3. 舵艙門、廚房大灶、艦載舢舨、主絞盤、羅經櫃、雙尾燈（全部複用共用組件）
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

PERSONA = 'kotoko'
HULL = 'kotoko-ganzengchuan-01m'
ASM = HULL + '-assembly'
HOST_WORKS = {
    'magazine': f'{HULL}-magazine',
    'deck-main': f'{HULL}-deck-main',
    'deck-poop': f'{HULL}-deck-poop',
}


def num(v):
    return ('%.4f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


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


def ensure_work(works_root, work_id, title, size, m_per_vox):
    if os.path.exists(os.path.join(works_root, work_id, 'work.json')):
        print('· 已有子作品（跳過建立）：', work_id)
        return False
    cli('op=work', 'sub=create', f'persona={PERSONA}', f'id={work_id}', f'title={title}',
        f'parent_work={HULL}', f'size={size}')
    cli('op=work', 'sub=update', f'persona={PERSONA}', f'work={work_id}', 'tags=sub', f'meters_per_voxel={m_per_vox}')
    print('✓ 建立子作品：', work_id, size, f'm/vox={m_per_vox}')
    return True


def stamp(work_id, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    p_norm = os.path.abspath(path).replace('\\', '/')
    out = cli('op=stampvox', f'persona={PERSONA}', f'work={work_id}', f'voxels={p_norm}', 'at=0,0,0', f'expect_pixels={n}')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        raise SystemExit(f'✗ placed {got} != {n} ({work_id})')
    print(f'  stampvox {os.path.basename(path)} -> {work_id}：{n} 格')


def main():
    design = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..'))
    works_root = os.path.dirname(os.path.dirname(design))
    P = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))

    # 1. 彈藥庫（link 至組裝件）
    w_mag = HOST_WORKS['magazine']
    if ensure_work(works_root, w_mag, '福建趕繒船 彈藥庫（底艙艉端，0.1 m）', '384,192,384', 0.1):
        stamp(w_mag, os.path.join(design, 'masks', 'gear', 'magazine.vox.txt'))
    for an, pt in P['magazine_anchors'].items():
        cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w_mag}', f'name={an}',
            'at=%d,%d,%d' % tuple(pt), 'overwrite=1', 'note=步驟 10：彈藥庫固定點')
    meta_mag = json.dumps(P['magazine_meta'], ensure_ascii=False, separators=(',', ':'))
    cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}', 'name=彈藥庫', f'source_work={w_mag}',
        'at=0,0,0', f'meta={meta_mag}', 'note=步驟 10：底艙艉端銅襯彈藥庫')

    # 2. 主艙口木格柵艙蓋（0.05 m 子作品，scale 0.5 掛於甲板-main）
    ht = P['hatch']
    w_hat = ht['work']
    if ensure_work(works_root, w_hat, ht['title'], '%d,%d,%d' % tuple(ht['size']), 0.05):
        stamp(w_hat, os.path.join(design, ht['vox_file']))
    for an, pt in ht['anchors'].items():
        cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w_hat}', f'name={an}',
            'at=%d,%d,%d' % tuple(pt), 'overwrite=1', 'note=步驟 10：上掀艙蓋鉸鏈')
    cli('op=work', 'sub=model', f'persona={PERSONA}', 'work=' + HOST_WORKS[ht['host']],
        'name=' + ht['name'], f'source_work={w_hat}',
        'at=' + xyz(ht['at']), 'pivot=' + xyz(ht['pivot']), 'rotate=0,0,0',
        f'scale={ht["scale"]},{ht["scale"]},{ht["scale"]}', 'overwrite=1',
        'meta=' + json.dumps(ht['meta'], ensure_ascii=False, separators=(',', ':')),
        'note=步驟 10：主艙口木格柵艙蓋（open=up）')

    # 3. 4 具火藥桶 ＋ 甲板配備模型
    for m in P['models']:
        sc = m['scale'] if isinstance(m['scale'], list) else [m['scale']] * 3
        cli('op=work', 'sub=model', f'persona={PERSONA}', 'work=' + HOST_WORKS[m['host']],
            'name=' + m['name'], 'source_work=' + m['source_work'],
            'at=' + xyz(m['at']), 'pivot=' + xyz(m['pivot']), 'rotate=0,0,0',
            'scale=' + xyz(sc), 'overwrite=1',
            'meta=' + json.dumps(m['meta'], ensure_ascii=False, separators=(',', ':')),
            'note=步驟 10（draft_gear.py）')

    print('=== assembly stats (links=all) ===')
    print(cli('op=stats', f'work={ASM}', 'links=all', 'structure=1'))
    print('=== assembly models ===')
    print(cli('op=work', 'sub=models', f'work={ASM}'))


if __name__ == '__main__':
    main()
