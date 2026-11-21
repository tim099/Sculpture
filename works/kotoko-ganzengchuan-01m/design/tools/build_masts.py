# 福建趕繒船 步驟 7 落格與固定點／外部模型掛載（TASK-1314）：
#   1. 建立並落格頭桅、大桅（link 於組裝件，標 meta kind=mast, mast=fore|main）
#   2. 建立並落格 4 根主帆桁＋固定點，掛為各桅子作品之外部模型（scale=1, meta kind=yard, yard=course）
#   3. 建立並落格 2 件共用竹篾＋固定點，依配方在各桅掛滿 7＋9＝16 根竹篾（meta kind=yard, yard=batten, material=bamboo）
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


def set_anchors(work_id, anchors_dict):
    for an, pt in anchors_dict.items():
        cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={work_id}', f'name={an}',
            'at=%d,%d,%d' % tuple(pt), 'overwrite=1', 'note=步驟 7：桅與帆桁固定點')


def main():
    design = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..'))
    works_root = os.path.dirname(os.path.dirname(design))
    P = json.load(open(os.path.join(design, 'masts_placement.json'), encoding='utf-8'))

    # 1. 頭桅 & 大桅（link 進 assembly，標 kind=mast + mast=<mk>）
    for mk, mcfg in P['masts'].items():
        w_m = mcfg['work']
        title_m = '福建趕繒船 頭桅（0.1 m）' if mk == 'fore' else '福建趕繒船 大桅（0.1 m）'
        if ensure_work(works_root, w_m, title_m, '384,192,384'):
            stamp(w_m, os.path.join(design, 'masks', 'masts', f'mast_{mk}.vox.txt'))
        set_anchors(w_m, mcfg['anchors'])
        meta_link = json.dumps({'kind': 'mast', 'mast': mk}, ensure_ascii=False, separators=(',', ':'))
        cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}', f'name=桅-{mk}', f'source_work={w_m}',
            'at=0,0,0', f'meta={meta_link}', f'note=步驟 7：{mk} 下桅（Ship_Masts）')

    # 2. 4 根主帆桁（每根一件子作品 ＋ 掛在對應桅子作品上）
    for sub_name, ycfg in P['yards'].items():
        w_y = ycfg['work']
        if ensure_work(works_root, w_y, f'福建趕繒船 帆桁 {sub_name}（0.1 m）', ycfg['size']):
            stamp(w_y, os.path.join(design, ycfg['vox_file']))
        set_anchors(w_y, ycfg['anchors'])
        meta_y = json.dumps(ycfg['meta'], ensure_ascii=False, separators=(',', ':'))
        cli('op=work', 'sub=model', f'persona={PERSONA}', 'work=' + ycfg['host_mast'],
            'name=' + ycfg['model_name'], 'source_work=' + w_y,
            'at=%g,%g,%g' % tuple(ycfg['at']),
            'pivot=%g,%g,%g' % tuple(ycfg['pivot']),
            'rotate=%g,%g,%g' % tuple(ycfg['rotate']),
            'scale=1', 'overwrite=1',
            f'meta={meta_y}', f'note=步驟 7：中式硬篷帆桁 {sub_name}')

    # 3. 共用竹篾桿元件（每桅 1 件）＋ 16 根竹篾模型掛於對應桅子作品
    for mk, bcfg in P['batten_templates'].items():
        w_b = bcfg['work']
        if ensure_work(works_root, w_b, f'福建趕繒船 共用竹篾桿 {mk}（0.1 m）', bcfg['size']):
            stamp(w_b, os.path.join(design, bcfg['vox_file']))
        set_anchors(w_b, bcfg['anchors'])

    for bm in P['battens']:
        meta_b = json.dumps(bm['meta'], ensure_ascii=False, separators=(',', ':'))
        cli('op=work', 'sub=model', f'persona={PERSONA}', 'work=' + bm['host_mast'],
            'name=' + bm['model_name'], 'source_work=' + bm['source_work'],
            'at=%g,%g,%g' % tuple(bm['at']),
            'pivot=%g,%g,%g' % tuple(bm['pivot']),
            'rotate=%g,%g,%g' % tuple(bm['rotate']),
            'scale=%g,%g,%g' % tuple(bm['scale']),
            'overwrite=1',
            f'meta={meta_b}', f'note=步驟 7：{bm["mast"]} 竹篾第 {bm["batten"]} 根')

    for mk in ('fore', 'main'):
        print(f'=== models on mast-{mk} ===')
        print(cli('op=work', 'sub=models', f'work={HULL}-mast-{mk}'))
    print('=== assembly links ===')
    print(cli('op=work', 'sub=links', f'work={ASM}'))
    print('=== assembly stats (links=all) ===')
    print(cli('op=stats', f'work={ASM}', 'links=all', 'structure=1'))


if __name__ == '__main__':
    main()
