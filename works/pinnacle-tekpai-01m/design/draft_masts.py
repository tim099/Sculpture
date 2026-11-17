# 台灣帆竹筏 Tek-pái 步驟 7：單竹主桅與上下竹帆桁產生器（TASK-1312）
#   子作品：
#     1. pinnacle-tekpai-01m-mast-main (140x101x110, 0.1 m)：單竹主桅 x=82, y=50, z=3..74
#     2. pinnacle-tekpai-01m-yard-course (5x45x5, 0.1 m)：上帆桁 y=2..42 (4.1 m)，yard=course
#     3. pinnacle-tekpai-01m-yard-lower  (5x45x5, 0.1 m)：下帆桁 y=1..43 (4.3 m)，yard=lower
#   依 Ship_Masts.md §5：
#     - 關聯 `桅-main` 標 meta kind=mast, mast=main
#     - 上下兩桁均掛載於桅子作品並同標 mast=main, sail=main, pivot=pivot，rotate=0,0,-18
import hashlib
import json
import os
import subprocess
import sys
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')


def load_vox(path, shape):
    arr = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros(shape, dtype=np.uint8)
    if len(arr):
        G[arr[:, 0], arr[:, 1], arr[:, 2]] = arr[:, 3].astype(np.uint8)
    return G


def build_mast(dz_probe=0):
    M = np.zeros((140, 101, 110), dtype=np.uint8)
    mx, my = 82, 50
    c_bam = 177    # 曝曬老竹 (#b69155)
    c_node = 104   # 竹節／桅頭木塊 (#6d4800)
    c_lash = 136   # 黃藤箍與桅頂帽 (#914800)

    z_lo = 3
    z_hi = 78 + dz_probe
    for z in range(z_lo, z_hi + 1):
        if z in (12, 22, 32, 42, 52, 62, 70):
            M[mx, my, z] = c_node
        elif z in (3, 71, 72, 73):
            M[mx, my, z] = c_node
        elif z == z_hi:
            M[mx, my, z] = c_lash
        else:
            M[mx, my, z] = c_bam
    # 桅頭滑輪耳 (x=81 at z=71..73, 避開下方 x=82)
    M[mx - 1, my, 71 + dz_probe : 74 + dz_probe] = c_node

    anchors = [
        ('foot',       f'{mx},{my},3'),
        ('collar',     f'{mx},{my},6'),
        ('mast-lower', f'{mx},{my},24'),
        ('mast-upper', f'{mx},{my},68'),
        ('head',       f'{mx},{my},{74 + dz_probe}'),
        ('peak',       f'{mx},{my},{z_hi}'),
    ]
    return M, anchors


def build_yard(y0, y1):
    # 5 x 45 x 5 along Y (center x=2, y=22, z=2)
    Y = np.zeros((5, 45, 5), dtype=np.uint8)
    c_bam = 177
    c_node = 104
    c_lash = 136
    for y in range(y0, y1 + 1):
        if y in (y0, y1, 18, 22, 26):
            Y[2, y, 2] = c_node
        elif y in (6, 12, 32, 38):
            Y[2, y, 2] = c_lash
        else:
            Y[2, y, 2] = c_bam
    # 中央吊環加厚 (y=20..24, z=3)
    Y[2, 20:25, 3] = c_node

    anchors = [
        ('pivot',    '2,22,2'),
        ('sling',    '2,22,3'),
        ('arm-P',    f'2,{y0},2'),
        ('arm-S',    f'2,{y1},2'),
        ('earing-P', f'2,{y0 + 2},2'),
        ('earing-S', f'2,{y1 - 2},2'),
    ]
    jxs = list(range(y0 + 2, y1 - 1, 8))
    if jxs[-1] != y1 - 2:
        jxs.append(y1 - 2)
    for i, jy in enumerate(jxs):
        anchors.append((f'jackstay-{i:02d}', f'2,{jy},2'))
    return Y, anchors


def write_vox(arr, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    xs, ys, zs = np.nonzero(arr)
    lines = ['# deterministic mast/yard voxels (x,y,z,color)']
    for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
        lines.append(f'{x},{y},{z},{int(arr[x, y, z])}')
    txt = '\n'.join(lines) + '\n'
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    _, comp = ndimage.label(arr > 0)
    return int((arr > 0).sum()), int(comp), hashlib.sha256(txt.encode('utf-8')).hexdigest()


def run_cli(args):
    r = subprocess.run(
        ['senate', 'cmd', 'sculpture'] + args,
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    if r.returncode != 0:
        raise SystemExit(f"CLI error ({args}):\n{r.stdout}\n{r.stderr}")
    return r.stdout


def main():
    H = load_vox(os.path.join(HERE, 'masks', 'hull_voxels.vox.txt'), (140, 101, 40))
    D = load_vox(os.path.join(HERE, 'masks_deck', 'deck_voxels.vox.txt'), (140, 101, 40))
    M, m_anc = build_mast(0)
    Mp, mp_anc = build_mast(3)
    Yc, yc_anc = build_yard(2, 42)
    Yl, yl_anc = build_yard(1, 43)

    ov_h = int(((M[:, :, :40] > 0) & (H > 0)).sum())
    ov_d = int(((M[:, :, :40] > 0) & (D > 0)).sum())
    assert ov_h == 0 and ov_d == 0, f'桅與船殼/甲板重疊 hull={ov_h}, deck={ov_d}'

    m_top = int(np.where(M[82, 50, :] > 0)[0].max())
    mp_top = int(np.where(Mp[82, 50, :] > 0)[0].max())
    assert mp_top - m_top == 3

    out_dir = os.path.join(HERE, 'masks_masts')
    mc, m_comp, m_sha = write_vox(M, os.path.join(out_dir, 'mast_main.vox.txt'))
    cc, c_comp, c_sha = write_vox(Yc, os.path.join(out_dir, 'yard_course.vox.txt'))
    lc, l_comp, l_sha = write_vox(Yl, os.path.join(out_dir, 'yard_lower.vox.txt'))

    tsv_path = os.path.join(HERE, 'masts_meta.tsv')
    mast_link_meta = json.dumps({'kind': 'mast', 'mast': 'main'}, ensure_ascii=False)
    with open(tsv_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f"link\t桅-main\t{mast_link_meta}\n")

    rep = {
        'mast': {'voxels': mc, 'components': m_comp, 'overlap_hull': ov_h, 'overlap_deck': ov_d, 'sha256': m_sha, 'anchors': m_anc},
        'yard_course': {'voxels': cc, 'components': c_comp, 'sha256': c_sha, 'anchors': yc_anc},
        'yard_lower': {'voxels': lc, 'components': l_comp, 'sha256': l_sha, 'anchors': yl_anc},
        'reverse_control_delta': mp_top - m_top,
    }
    with open(os.path.join(HERE, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rep, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(rep, ensure_ascii=False, indent=2))

    if '--apply' in sys.argv:
        # 1. Stamp 3 works
        for wid, vpath, exp in [
            ('pinnacle-tekpai-01m-mast-main', os.path.join(out_dir, 'mast_main.vox.txt'), mc),
            ('pinnacle-tekpai-01m-yard-course', os.path.join(out_dir, 'yard_course.vox.txt'), cc),
            ('pinnacle-tekpai-01m-yard-lower', os.path.join(out_dir, 'yard_lower.vox.txt'), lc),
        ]:
            run_cli(['--arg', 'op=stampvox', '--arg', 'persona=pinnacle', '--arg', f'work={wid}',
                     '--arg', 'at=0,0,0', '--arg', f'voxels={vpath}', '--arg', f'expect_pixels={exp}'])
            print(f'✓ stampvox {wid} ({exp})')

        # 2. Register anchors
        for wid, ancs in [
            ('pinnacle-tekpai-01m-mast-main', m_anc),
            ('pinnacle-tekpai-01m-yard-course', yc_anc),
            ('pinnacle-tekpai-01m-yard-lower', yl_anc),
        ]:
            for anm, aat in ancs:
                run_cli(['--arg', 'op=work', '--arg', 'sub=anchor', '--arg', 'persona=pinnacle',
                         '--arg', f'work={wid}', '--arg', f'name={anm}', '--arg', f'at={aat}'])
            print(f'✓ anchors ({len(ancs)}) on {wid}')

        # 3. Mount yards onto mast-main
        yards_cfg = [
            ('yard-course', 'pinnacle-tekpai-01m-yard-course', '84.0,50.5,68.5', {
                'kind': 'yard', 'mast': 'main', 'yard': 'course', 'sail': 'main',
                'length_ft': 13.5, 'diameter_in': 5, 'pivot_anchor': 'pivot',
                'turn_axis': 'z', 'rotate_z_deg': -18,
            }),
            ('yard-lower', 'pinnacle-tekpai-01m-yard-lower', '84.0,50.5,24.5', {
                'kind': 'yard', 'mast': 'main', 'yard': 'lower', 'sail': 'main',
                'length_ft': 14.1, 'diameter_in': 4, 'pivot_anchor': 'pivot',
                'turn_axis': 'z', 'rotate_z_deg': -18,
            }),
        ]
        for ynm, src_w, at_pos, ymeta in yards_cfg:
            run_cli([
                '--arg', 'op=work', '--arg', 'sub=model', '--arg', 'persona=pinnacle',
                '--arg', 'work=pinnacle-tekpai-01m-mast-main', '--arg', f'name={ynm}',
                '--arg', f'source_work={src_w}', '--arg', 'pivot=2.5,22.5,2.5',
                '--arg', f'at={at_pos}', '--arg', 'rotate=0,0,-18', '--arg', 'scale=1',
                '--arg', f'meta={json.dumps(ymeta, ensure_ascii=False, separators=(",", ":"))}',
            ])
            print(f'✓ model {ynm} -> pinnacle-tekpai-01m-mast-main')

        # 4. Apply mast link meta on assembly
        run_cli(['--arg', 'op=work', '--arg', 'sub=meta', '--arg', 'persona=pinnacle',
                 '--arg', 'work=pinnacle-tekpai-01m-assembly', '--arg', f'file={tsv_path}'])
        print('✓ masts_meta.tsv applied to assembly')


if __name__ == '__main__':
    main()
