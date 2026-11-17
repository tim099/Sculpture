# 台灣帆竹筏 Tek-pái 步驟 10（甲板物件）＋ 步驟 11（尾舵槳與石錨）產生與驗證器（TASK-1312）
#   規範：Ship_Fittings §9.7/§9.9/§9.13/§9.14、Ship_Helm §9.8/§9.8.1、Ship_Game §9 anchor
import hashlib
import json
import math
import os
import subprocess
import sys
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_HULL = 'pinnacle-tekpai-01m'
WORK_DECK = 'pinnacle-tekpai-01m-deck-main'
WORK_ASM = 'pinnacle-tekpai-01m-assembly'
sys.stdout.reconfigure(encoding='utf-8')


def load_vox(path, shape=(140, 101, 40)):
    arr = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros(shape, dtype=bool)
    if len(arr):
        G[arr[:, 0], arr[:, 1], arr[:, 2]] = True
    return G


def build_pole():
    # 44 x 3 x 3 (0.1 m/voxel)：4.4 m 撐灘竹篙，帶深色竹節與金屬篙頭點綴
    P = np.zeros((44, 3, 3), dtype=np.uint8)
    for x in range(44):
        if x in (0, 43):
            P[x, 1, 0] = 104
        elif x % 8 == 0:
            P[x, 1, 0] = 136
        else:
            P[x, 1, 0] = 181
    return P


def build_bitt():
    # 4 x 4 x 6 (0.05 m/voxel, scale=0.5)：木製繫纜樁
    B = np.zeros((4, 4, 6), dtype=np.uint8)
    B[1:3, 1:3, 0:5] = 104
    B[0:4, 1:3, 4:6] = 136  # 十字橫栓
    return B


def build_rudder(dx_probe=0):
    # 26 x 5 x 14 (0.1 m/voxel)：傳統長尾舵槳（整合式舵柄 + 舵軸插銷），hinge=(16.5, 50.5, 1.0) at=(16.5, 50.5, 1.0) pivot=(15.5, 2.5, 1.0)
    R = np.zeros((26, 5, 14), dtype=np.uint8)
    c_shaft = 104   # 深色硬木舵軸/箍 (#6d4800)
    c_blade = 136   # 濕潤紅棕舵葉 (#914800)
    c_tiller = 177  # 竹木舵柄 (#b69155)

    px = 15 + dx_probe
    # 舵軸 (rx=px, ry=2, rz=1..11)
    R[px, 2, 1:12] = c_shaft
    # 水下寬大尾舵葉（不低於 z=1，保持 0.3 m 淺灘安全；向後伸展至 rx=2）
    for rz in range(1, 7):
        x0 = 3 if rz <= 5 else 6
        R[x0:px, 2, rz] = c_shaft if rz in (3, 6) else c_blade
    # 斜向上延伸至舵軸的槳頸 (rz=7..8)
    R[px - 3:px, 2, 7] = c_blade
    R[px - 1:px, 2, 8] = c_blade
    # 舵枕轉軸箍耳 (rx=px+1, rz=8 -> 組裝件 x=17, z=8，緊貼艉尖 x=18)
    R[px + 1, 2, 8] = c_shaft
    # 前伸整合式舵柄 (rz=11, rx=px..px+7 -> 組裝件 x=16..23, z=11，高出艉尖與甲板)
    R[px:px + 8, 2, 11] = c_tiller
    R[px + 7, 2, 11] = c_shaft  # 把手端頭

    stock_top = (px + 1, 2, 8)
    return R, stock_top


def write_vox(arr, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    xs, ys, zs = np.nonzero(arr)
    lines = ['# deterministic fittings/helm voxels']
    for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
        lines.append(f'{x},{y},{z},{int(arr[x, y, z])}')
    txt = '\n'.join(lines) + '\n'
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    _, comp = ndimage.label(arr > 0)
    return int((arr > 0).sum()), int(comp), hashlib.sha256(txt.encode('utf-8')).hexdigest()


def check_rudder_sweep(R, pivot, at, occ):
    pts = np.argwhere(R > 0)
    px, py, pz = pivot
    ax, ay, az = at
    max_hits = 0
    for deg in range(-35, 36):
        rad = math.radians(deg)
        c, s = math.cos(rad), math.sin(rad)
        for rx, ry, rz in pts:
            vx = (rx + 0.5) - px
            vy = (ry + 0.5) - py
            vz = (rz + 0.5) - pz
            wx = ax + vx * c - vy * s
            wy = ay + vx * s + vy * c
            wz = az + vz
            ix, iy, iz = int(math.floor(wx)), int(math.floor(wy)), int(math.floor(wz))
            if 0 <= ix < 140 and 0 <= iy < 101 and 0 <= iz < 40 and occ[ix, iy, iz]:
                max_hits += 1
                break
    return max_hits


def run_cli(args):
    r = subprocess.run(
        ['senate', 'cmd', 'sculpture'] + args,
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    if r.returncode != 0:
        raise SystemExit(f"CLI error ({args}):\n{r.stdout}\n{r.stderr}")
    return r.stdout


def main():
    H = load_vox(os.path.join(HERE, 'masks', 'hull_voxels.vox.txt'))
    D = load_vox(os.path.join(HERE, 'masks_deck', 'deck_voxels.vox.txt'))
    occ = H | D

    P = build_pole()
    B = build_bitt()
    R, stock_top = build_rudder(0)
    Rp, _ = build_rudder(2)

    pivot = (15.5, 2.5, 1.0)
    at = (16.5, 50.5, 1.0)
    sweep_hits = check_rudder_sweep(R, pivot, at, occ)
    # 反向對照：舵前移 +2 格必撞船尾
    probe_hits = check_rudder_sweep(Rp, (17.5, 2.5, 1.0), (18.5, 50.5, 1.0), occ)
    assert sweep_hits == 0, f"舵掃掠碰撞：{sweep_hits}"
    assert probe_hits > 0, "反向對照未撞到船尾"

    out_dir = os.path.join(HERE, 'masks_fittings')
    pc, p_comp, p_sha = write_vox(P, os.path.join(out_dir, 'pole.vox.txt'))
    bc, b_comp, b_sha = write_vox(B, os.path.join(out_dir, 'bitt.vox.txt'))
    rc, r_comp, r_sha = write_vox(R, os.path.join(out_dir, 'rudder.vox.txt'))

    rep = {
        'pole': {'voxels': pc, 'components': p_comp, 'sha256': p_sha},
        'bitt': {'voxels': bc, 'components': b_comp, 'sha256': b_sha},
        'rudder': {'voxels': rc, 'components': r_comp, 'stock_top': stock_top, 'sweep_hits_deg_pm35': sweep_hits, 'reverse_probe_dx2_hits': probe_hits, 'sha256': r_sha},
    }
    with open(os.path.join(HERE, 'verify_fittings_helm.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rep, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(rep, ensure_ascii=False, indent=2))

    if '--apply' in sys.argv:
        # 1. Create works (if missing) & update tags/meters_per_voxel & stamp
        specs = [
            ('pinnacle-tekpai-01m-pole', '台灣帆竹筏 撐灘竹篙', '44,3,3', 0.1, os.path.join(out_dir, 'pole.vox.txt'), pc),
            ('pinnacle-tekpai-01m-bitt', '台灣帆竹筏 繫纜木樁', '4,4,6', 0.05, os.path.join(out_dir, 'bitt.vox.txt'), bc),
            ('pinnacle-tekpai-01m-rudder', '台灣帆竹筏 尾舵槳', '26,5,14', 0.1, os.path.join(out_dir, 'rudder.vox.txt'), rc),
        ]
        for wid, title, sz, mpv, vpath, exp in specs:
            if not os.path.isdir(f'D:/Unity/Valhalla/Sculpture/works/{wid}'):
                run_cli(['--arg', 'op=work', '--arg', 'sub=create', '--arg', 'persona=pinnacle',
                         '--arg', f'id={wid}', '--arg', f'title={title}',
                         '--arg', f'parent_work={WORK_HULL}', '--arg', f'size={sz}'])
                run_cli(['--arg', 'op=work', '--arg', 'sub=update', '--arg', 'persona=pinnacle',
                         '--arg', f'work={wid}', '--arg', 'tags=sub', '--arg', f'meters_per_voxel={mpv}'])
                run_cli(['--arg', 'op=stampvox', '--arg', 'persona=pinnacle', '--arg', f'work={wid}',
                         '--arg', 'at=0,0,0', '--arg', f'voxels={vpath}', '--arg', f'expect_pixels={exp}'])
                print(f'✓ created & stamped {wid} ({exp})')

        # 2. Rudder anchor stock-top
        run_cli(['--arg', 'op=work', '--arg', 'sub=anchor', '--arg', 'persona=pinnacle',
                 '--arg', 'work=pinnacle-tekpai-01m-rudder', '--arg', 'name=stock-top',
                 '--arg', f'at={stock_top[0]},{stock_top[1]},{stock_top[2]}', '--arg', 'overwrite=1'])

        # 3. Step 10 Models (deck-main & hull)
        models = [
            (WORK_DECK, 'cargo-barrel-1', 'summit-rocher-01m-barrel', '6,6,0', '66.0,48.0,6.0', '0.35', {'deco': 1}),
            (WORK_DECK, 'cargo-crate-1', 'summit-rocher-01m-crate', '6,6,0', '69.0,53.0,6.0', '0.4', {'deco': 1}),
            (WORK_DECK, 'cargo-crate-2', 'summit-rocher-01m-crate', '6,6,0', '57.0,50.5,6.0', '0.4', {'deco': 1}),
            (WORK_DECK, 'lantern-tub', 'basecamp-nightlamp-01m-lantern-01m', '4.5,4.5,0', '74.5,56.5,8.0', '0.35', {'kind': 'light'}),
            (WORK_HULL, 'pole-spare', 'pinnacle-tekpai-01m-pole', '0,1.5,0', '44.0,63.5,4.0', '1', {'deco': 1}),
            (WORK_HULL, 'bitt-aft-P', 'pinnacle-tekpai-01m-bitt', '2,2,0', '35.5,37.5,4.0', '0.5', {'deco': 1}),
            (WORK_HULL, 'bitt-aft-S', 'pinnacle-tekpai-01m-bitt', '2,2,0', '35.5,63.5,4.0', '0.5', {'deco': 1}),
            (WORK_HULL, 'bitt-fwd-P', 'pinnacle-tekpai-01m-bitt', '2,2,0', '96.5,37.5,4.0', '0.5', {'deco': 1}),
            (WORK_HULL, 'bitt-fwd-S', 'pinnacle-tekpai-01m-bitt', '2,2,0', '96.5,63.5,4.0', '0.5', {'deco': 1}),
            # Step 11 Rudder & Stone Anchor (命名 rudder-main 避免 Blockside metaRebase 誤把 spin:"rudder" 當模型路徑改寫)
            (WORK_HULL, 'rudder-main', 'pinnacle-tekpai-01m-rudder', '15.5,2.5,1.0', '16.5,50.5,1.0', '1', {
                'kind': 'rudder', 'hinge_x': 16.5, 'hinge_y': 50.5, 'hinge_z': 1.0,
                'axis_x': 0, 'axis_y': 0, 'axis_z': 1, 'max_deg': 35, 'turn_axis': 'hinge',
                'spin': 'rudder', 'spin_k': 35, 'spin_min': -35, 'spin_max': 35, 'spin_lag': 0.3,
            }),
            (WORK_HULL, 'anchor-S', 'apex-one-punt-01m-anchor-stone', '5.5,1.5,12.5', '99.5,67.2,9.5', '0.5', {
                'kind': 'anchor', 'anchor': 'bower', 'hawse': '99.5,65.5,5.5',
            }),
        ]
        for tgt, nm, src, piv, at_pos, sc, mobj in models:
            run_cli([
                '--arg', 'op=work', '--arg', 'sub=model', '--arg', 'persona=pinnacle',
                '--arg', f'work={tgt}', '--arg', f'name={nm}', '--arg', f'source_work={src}',
                '--arg', f'pivot={piv}', '--arg', f'at={at_pos}', '--arg', f'scale={sc}',
                '--arg', f'meta={json.dumps(mobj, ensure_ascii=False, separators=(",", ":"))}',
                '--arg', 'overwrite=1',
            ])
            print(f'✓ model {nm} -> {tgt}')

        # 4. Anchor hawse-S + Anchor cable
        run_cli(['--arg', 'op=work', '--arg', 'sub=anchor', '--arg', 'persona=pinnacle',
                 '--arg', f'work={WORK_HULL}', '--arg', 'name=hawse-S', '--arg', 'at=99,65,5', '--arg', 'overwrite=1'])
        run_cli(['--arg', 'op=work', '--arg', 'sub=rope', '--arg', 'persona=pinnacle',
                 '--arg', f'work={WORK_ASM}', '--arg', 'name=anchor-cable-S',
                 '--arg', 'from=hull/hawse-S', '--arg', 'to=model:hull/anchor-S/ring',
                 '--arg', 'slack=1.02', '--arg', 'color=#a08458', '--arg', 'thickness=0.4',
                 '--arg', 'group=standing/anchor', '--arg', 'overwrite=1'])
        print('✓ hawse-S & anchor-cable-S attached')


if __name__ == '__main__':
    main()
