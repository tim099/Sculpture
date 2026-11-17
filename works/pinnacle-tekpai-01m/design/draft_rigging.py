# 台灣帆竹筏 Tek-pái 步驟 8：索具、竹骨草蓆帆與桅頂長旗（TASK-1312）
#   規範：Ship_Rigging.md §6, §7, §9.1
#   - 靜索 (standing/stays, standing/shrouds) ＋ 動索 (running/halyards, running/lifts, running/braces, running/sheets)
#   - 主帆 `main` (bind=0,2 綁於上桁 yard-course 與下桁 yard-lower；meta kind=sail, mast=main, sail=course, set=1)
#   - 桅頂長旗 `pennant` (kind=flag, mast=main, flag=pennant, nation=none，附 PNG 貼圖)
#   - 帆裝三段張帆表：0=全收 / 1=收帆[main] / 2=戰鬥帆[main] / 3=滿帆[main]
import hashlib
import json
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_ASM = 'pinnacle-tekpai-01m-assembly'
WORK_HULL = 'pinnacle-tekpai-01m'
sys.stdout.reconfigure(encoding='utf-8')


def make_sail_mat_png(out_png):
    """64x64 像素畫：傳統台灣草蓆編紋＋水平竹骨壓條＋邊繩加固。"""
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    img = Image.new('RGBA', (64, 64), (214, 184, 126, 255))
    px = img.load()
    for y in range(64):
        for x in range(64):
            # 水平竹片壓骨（每 11 px 一道，頂/底各一道）
            if y in (0, 1, 12, 24, 36, 48, 62, 63):
                px[x, y] = (118, 78, 36, 255)
            # 垂直拼蓆縫線（三幅併縫）
            elif x in (0, 1, 21, 42, 62, 63):
                px[x, y] = (158, 120, 68, 255)
            # 交錯編織細紋
            elif ((x // 2 + y // 2) % 2) == 0:
                px[x, y] = (206, 174, 114, 255)
            else:
                px[x, y] = (222, 192, 134, 255)
    img.save(out_png, optimize=False)
    with open(out_png, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def make_pennant_png(out_png):
    """32x16 傳統金邊朱紅三角小旗貼圖（alpha 裁出燕尾尖端）。"""
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    img = Image.new('RGBA', (32, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 紅底長三角（角 0=(0,0) 在 peak, 角 0->1 往右飛尖, 角 0->2 沿桅往下）
    for x in range(32):
        # 上下收窄成三角尖
        y0 = int(round((x / 31.0) * 5.0))
        y1 = 15 - int(round((x / 31.0) * 5.0))
        for y in range(y0, y1 + 1):
            is_border = (x < 3 or y == y0 or y == y1 or x > 28)
            img.putpixel((x, y), (218, 178, 72, 255) if is_border else (178, 44, 36, 255))
    img.save(out_png, optimize=False)
    with open(out_png, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def run_cli(args):
    r = subprocess.run(
        ['senate', 'cmd', 'sculpture'] + args,
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    if r.returncode != 0:
        raise SystemExit(f"CLI error ({args}):\n{r.stdout}\n{r.stderr}")
    return r.stdout


def main():
    sail_png = os.path.join(HERE, 'textures', 'sail_mat.png')
    pen_png = os.path.join(HERE, 'textures', 'pennant.png')
    s_sha = make_sail_mat_png(sail_png)
    p_sha = make_pennant_png(pen_png)

    # 計算草蓆帆面積（4.1m/4.3m 平均寬 4.2m × 高 4.4m = 18.48 m²？實際 earing-P..S = 3.7m/3.9m -> 3.8m * 4.4m = 16.72 m²）
    area_m2 = round(((3.6 + 3.8) * 0.5) * (68.5 - 24.5) * 0.1, 2)

    hull_anchors = [
        ('stay-bow',      '118,50,9', '步驟 8 前支索固定點（翹首橫擔中線，避開帆腹）'),
        ('shroud-base-P', '73,35,4',  '步驟 8 左舷側支索固定點（護舷竹上緣）'),
        ('shroud-base-S', '73,65,4',  '步驟 8 右舷側支索固定點（護舷竹上緣）'),
        ('backstay-P',    '60,35,4',  '步驟 8 左舷後支索固定點'),
        ('backstay-S',    '60,65,4',  '步驟 8 右舷後支索固定點'),
        ('sheet-base-P',  '48,35,4',  '步驟 8 左舷帆腳索固定點'),
        ('sheet-base-S',  '48,65,4',  '步驟 8 右舷帆腳索固定點'),
    ]

    rope_groups = ['standing', 'standing/stays', 'standing/shrouds', 'running', 'running/halyards', 'running/lifts', 'running/braces', 'running/sheets']

    ropes = [
        ('stay-main',   '桅-main/head',                        'hull/stay-bow',      '1.0006', '#2b2620', '0.5',  'standing/stays',   {'kind': 'stay'}),
        ('shroud-P',    '桅-main/head',                        'hull/shroud-base-P', '1.0',    '#2b2620', '0.45', 'standing/shrouds', {'kind': 'shroud'}),
        ('shroud-S',    '桅-main/head',                        'hull/shroud-base-S', '1.0',    '#2b2620', '0.45', 'standing/shrouds', {'kind': 'shroud'}),
        ('backstay-P',  '桅-main/peak',                        'hull/backstay-P',    '1.0',    '#2b2620', '0.4',  'standing/shrouds', {'kind': 'backstay'}),
        ('backstay-S',  '桅-main/peak',                        'hull/backstay-S',    '1.0',    '#2b2620', '0.4',  'standing/shrouds', {'kind': 'backstay'}),
        ('halyard',     '桅-main/peak',                        'model:桅-main/yard-course/sling', '1.0', '#a08458', '0.4', 'running/halyards', {'kind': 'halyard'}),
        ('lift-P',      '桅-main/peak',                        'model:桅-main/yard-course/arm-P', '1.0', '#a08458', '0.35', 'running/lifts',   {'kind': 'lift'}),
        ('lift-S',      '桅-main/peak',                        'model:桅-main/yard-course/arm-S', '1.0', '#a08458', '0.35', 'running/lifts',   {'kind': 'lift'}),
        ('brace-P',     'model:桅-main/yard-course/arm-P',     'hull/sheet-base-P',  '1.03',   '#a08458', '0.35', 'running/braces',   {'kind': 'brace'}),
        ('brace-S',     'model:桅-main/yard-course/arm-S',     'hull/sheet-base-S',  '1.03',   '#a08458', '0.35', 'running/braces',   {'kind': 'brace'}),
        ('main-sheet-P','model:桅-main/yard-lower/earing-P',   'hull/sheet-base-P',  '1.03',   '#a08458', '0.4',  'running/sheets',   {'kind': 'sheet', 'sail': 'main'}),
        ('main-sheet-S','model:桅-main/yard-lower/earing-S',   'hull/sheet-base-S',  '1.03',   '#a08458', '0.4',  'running/sheets',   {'kind': 'sheet', 'sail': 'main'}),
    ]

    stages = {
        '0_全收': [],
        '1_收帆': ['main'],
        '2_戰鬥帆': ['main'],
        '3_滿帆': ['main'],
        '旗幟': ['pennant (flag=pennant, nation=none)'],
    }

    rep = {
        'sail_area_m2': area_m2,
        'hull_anchors_count': len(hull_anchors),
        'ropes_count': len(ropes),
        'stages': stages,
        'textures': {'sail_mat_sha256': s_sha, 'pennant_sha256': p_sha},
    }
    with open(os.path.join(HERE, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rep, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(rep, ensure_ascii=False, indent=2))

    if '--apply' in sys.argv:
        # 1. Hull anchors (idempotent with overwrite=1)
        for nm, at, nt in hull_anchors:
            run_cli(['--arg', 'op=work', '--arg', 'sub=anchor', '--arg', 'persona=pinnacle',
                     '--arg', f'work={WORK_HULL}', '--arg', f'name={nm}', '--arg', f'at={at}',
                     '--arg', f'note={nt}', '--arg', 'overwrite=1'])
        print(f'✓ hull anchors ({len(hull_anchors)})')

        # 2. Default wind (4.5,-1.5,0) on assembly
        run_cli(['--arg', 'op=work', '--arg', 'sub=wind', '--arg', 'persona=pinnacle',
                 '--arg', f'work={WORK_ASM}', '--arg', 'wind=4.5,-1.5,0'])

        # 3. Ropes (group= creates rope groups on demand)
        for rname, rfrom, rto, rslack, rcol, rthk, rgrp, rmeta in ropes:
            run_cli([
                '--arg', 'op=work', '--arg', 'sub=rope', '--arg', 'persona=pinnacle',
                '--arg', f'work={WORK_ASM}', '--arg', f'name={rname}',
                '--arg', f'from={rfrom}', '--arg', f'to={rto}',
                '--arg', f'slack={rslack}', '--arg', f'color={rcol}',
                '--arg', f'thickness={rthk}', '--arg', f'group={rgrp}', '--arg', 'overwrite=1',
            ])
        print(f'✓ ropes ({len(ropes)})')

        # 4. Sail `main` & Pennant `pennant`
        run_cli([
            '--arg', 'op=work', '--arg', 'sub=sail', '--arg', 'persona=pinnacle',
            '--arg', f'work={WORK_ASM}', '--arg', 'name=main',
            '--arg', 'corners=model:桅-main/yard-course/earing-P|model:桅-main/yard-course/earing-S|model:桅-main/yard-lower/earing-S|model:桅-main/yard-lower/earing-P',
            '--arg', 'corner_names=head-P|head-S|foot-S|foot-P',
            '--arg', 'bind=0,2', '--arg', 'fullness=1.05', '--arg', 'color=#d6b87e',
            '--arg', f'texture={sail_png}', '--arg', 'overwrite=1',
        ])
        run_cli([
            '--arg', 'op=work', '--arg', 'sub=sail', '--arg', 'persona=pinnacle',
            '--arg', f'work={WORK_ASM}', '--arg', 'name=pennant',
            '--arg', 'corners=桅-main/peak|73,50,76|桅-main/head',
            '--arg', 'corner_names=hoist-top|fly|hoist-bot',
            '--arg', 'free=1', '--arg', 'bind=2', '--arg', 'fullness=1.03', '--arg', 'color=#b22c24',
            '--arg', f'texture={pen_png}', '--arg', 'overwrite=1',
        ])
        print('✓ sails (main, pennant)')

        # 5. Apply sail & rope meta TSV
        meta_lines = []
        meta_lines.append('sail\tmain\t' + json.dumps({'kind': 'sail', 'mast': 'main', 'sail': 'course', 'set': 1}, ensure_ascii=False))
        meta_lines.append('sail\tpennant\t' + json.dumps({'kind': 'flag', 'mast': 'main', 'flag': 'pennant', 'nation': 'none'}, ensure_ascii=False))
        for rname, *_rest, rmeta in ropes:
            meta_lines.append('rope\t' + rname + '\t' + json.dumps(rmeta, ensure_ascii=False))
        tsv = os.path.join(HERE, 'rig_meta.tsv')
        with open(tsv, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(meta_lines) + '\n')
        run_cli(['--arg', 'op=work', '--arg', 'sub=meta', '--arg', 'persona=pinnacle',
                 '--arg', f'work={WORK_ASM}', '--arg', f'file={tsv}'])
        print('✓ rig_meta.tsv applied')


if __name__ == '__main__':
    main()
