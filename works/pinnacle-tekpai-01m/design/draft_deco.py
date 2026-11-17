# 台灣帆竹筏 Tek-pái 步驟 6：裝飾模型（deco=1）產生器（TASK-1312）
#   模型（0.05 m/格，scale=0.5 掛於主筏面與船殼）：
#     1. pinnacle-tekpai-01m-deco-awning (24x26x14)：竹編半圓防潮遮棚（覆於木桶艙後半 x=50..62）
#     2. pinnacle-tekpai-01m-deco-coil   (10x10x4)：盤繞黃藤纜索圈
#     3. pinnacle-tekpai-01m-deco-fender (12x5x5)：舷側編藤竹束護墊
import hashlib
import json
import os
import sys
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')


def write_vox(arr, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    xs, ys, zs = np.nonzero(arr)
    lines = ['# deterministic deco voxels (x,y,z,color)']
    for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
        lines.append(f'{x},{y},{z},{int(arr[x, y, z])}')
    txt = '\n'.join(lines) + '\n'
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    _, comp = ndimage.label(arr > 0)
    return {
        'voxels': int((arr > 0).sum()),
        'components': int(comp),
        'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest(),
    }


def make_awning():
    # 24 x 26 x 14 (0.05 m/voxel): semi-cylindrical woven bamboo canopy arch
    A = np.zeros((24, 26, 14), dtype=np.uint8)
    c_mat = 213   # 暖竹蓆黃 (#dab655，避免偏粉紅)
    c_mat2 = 181  # 日曬竹編紋 (#b6b655)
    c_rib = 104   # 彎竹骨肋條 (#6d4800)
    yc = 12.5
    # 兩側貼邊垂直短腳 z=0..2
    for x in range(24):
        is_rib = (x in (0, 1, 11, 12, 22, 23))
        for y in range(26):
            dy = abs(y - yc) / 12.5  # 0..1
            z_arch = 2.5 + 9.0 * np.sqrt(max(0.0, 1.0 - min(dy, 1.0) ** 2))
            zi = int(round(z_arch))
            # 拱頂竹蓆兩層厚
            for z in range(max(0, zi - 1), min(14, zi + 1)):
                if is_rib:
                    A[x, y, z] = c_rib
                elif (x + y) % 4 == 0:
                    A[x, y, z] = c_mat2
                else:
                    A[x, y, z] = c_mat
            if dy > 0.90:
                for z in range(0, zi):
                    A[x, y, z] = c_rib if is_rib else c_mat2
    return A


def make_coil():
    # 10 x 10 x 4 (0.05 m/voxel): coiled rattan mooring rope
    C = np.zeros((10, 10, 4), dtype=np.uint8)
    c_r1 = 136  # 黃藤棕色 (#914800)
    c_r2 = 140  # 淺藤色 (#916d00)
    cx, cy = 4.5, 4.5
    for x in range(10):
        for y in range(10):
            r = np.hypot(x - cx, y - cy)
            if 1.6 <= r <= 4.7:
                C[x, y, 0] = c_r1 if int(round(r)) % 2 == 0 else c_r2
            if 2.2 <= r <= 4.2:
                C[x, y, 1] = c_r2 if int(round(r)) % 2 == 0 else c_r1
            if 2.8 <= r <= 3.6:
                C[x, y, 2] = c_r1
    return C


def make_fender():
    # 12 x 5 x 5 (0.05 m/voxel): side bamboo-bundle fender bound with rattan hoops
    F = np.zeros((12, 5, 5), dtype=np.uint8)
    c_bam = 177  # 老竹黃 (#b69155)
    c_lash = 136 # 黃藤箍 (#914800)
    for x in range(12):
        is_hoop = (x in (1, 2, 5, 6, 9, 10))
        for y in range(5):
            for z in range(5):
                dy = abs(y - 2.0)
                dz = abs(z - 2.0)
                if dy + dz <= 2.5:
                    F[x, y, z] = c_lash if is_hoop else c_bam
    return F


def apply_models():
    import subprocess
    meta_json = json.dumps({'deco': 1}, separators=(',', ':'))
    calls = [
        ('pinnacle-tekpai-01m-deck-main', 'awning-tub', 'pinnacle-tekpai-01m-deco-awning', '0,13,0', '50,50.5,8'),
        ('pinnacle-tekpai-01m-deck-main', 'coil-fwd', 'pinnacle-tekpai-01m-deco-coil', '5,5,0', '96,60.5,5'),
        ('pinnacle-tekpai-01m-deck-main', 'coil-aft', 'pinnacle-tekpai-01m-deco-coil', '5,5,0', '26,54.5,7'),
        ('pinnacle-tekpai-01m', 'fender-p1', 'pinnacle-tekpai-01m-deco-fender', '6,2.5,2.5', '54,33.8,3.2'),
        ('pinnacle-tekpai-01m', 'fender-p2', 'pinnacle-tekpai-01m-deco-fender', '6,2.5,2.5', '84,33.8,3.2'),
        ('pinnacle-tekpai-01m', 'fender-s1', 'pinnacle-tekpai-01m-deco-fender', '6,2.5,2.5', '54,67.2,3.2'),
        ('pinnacle-tekpai-01m', 'fender-s2', 'pinnacle-tekpai-01m-deco-fender', '6,2.5,2.5', '84,67.2,3.2'),
    ]
    for tgt, nm, src, piv, at in calls:
        r = subprocess.run([
            'senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=model',
            '--arg', 'persona=pinnacle', '--arg', f'work={tgt}', '--arg', f'name={nm}',
            '--arg', f'source_work={src}', '--arg', f'pivot={piv}', '--arg', f'at={at}',
            '--arg', 'scale=0.5', '--arg', f'meta={meta_json}',
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(f'model {nm} 失敗：{r.stdout}\n{r.stderr}')
        print(f'✓ model {nm} -> {tgt}')


def main():
    out_dir = os.path.join(HERE, 'masks_deco')
    rep = {
        'awning': write_vox(make_awning(), os.path.join(out_dir, 'awning.vox.txt')),
        'coil': write_vox(make_coil(), os.path.join(out_dir, 'coil.vox.txt')),
        'fender': write_vox(make_fender(), os.path.join(out_dir, 'fender.vox.txt')),
    }
    with open(os.path.join(HERE, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rep, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    if '--apply' in sys.argv:
        apply_models()


if __name__ == '__main__':
    main()
