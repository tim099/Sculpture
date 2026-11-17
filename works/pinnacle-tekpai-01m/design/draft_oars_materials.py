# 台灣帆竹筏 Tek-pái 步驟 13：雙槳推進（Ship_Oars §9.10）與竹木空腔材質浮力評估（Ship_Materials §9.5）
#   - 複用共用元件 basecamp-piragua-01m-oar (0.05 m/格, scale=0.5, 已具 pivot/blade/seat 固定點)
#   - 兩對 4 支單人划槳（oar-S1/P1 @ x=40.5, oar-S2/P2 @ x=77.5），pivot=(1.5,16.5,16.5) 設於 y=65.5/35.5, z=9.0
#     ⇒ seat 精準落於左右側走道 y=59 / y=42, z=5.0（頭頂 14 格淨空）；blade 精準落於水線 z=3.0
#   - 材質：刺竹具天然中空管腔，hull 與 甲板-main 評估並採用混合材質 `oak*0.55`（等效密度 0.385 t/m³），使 3–5 t 級竹筏穩立於 DWL z=3（0.30 m）
#   用法：python -I -X utf8 draft_oars_materials.py [--apply] [--probe=oar_drop=5]
import json
import math
import os
import subprocess
import sys
import tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_ASM = 'pinnacle-tekpai-01m-assembly'
WORK_HULL = 'pinnacle-tekpai-01m'
OAR_WORK = 'basecamp-piragua-01m-oar'
SX, SY, SZ = 140, 101, 110
sys.stdout.reconfigure(encoding='utf-8')


def load_vox(path):
    arr = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros((SX, SY, SZ), dtype=bool)
    if len(arr):
        G[arr[:, 0], arr[:, 1], arr[:, 2]] = True
    return G


def load_oar_pts():
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, 'oar.txt').replace('\\', '/')
        subprocess.run(
            ['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list',
             '--arg', f'work={OAR_WORK}', '--arg', f'out={out}'],
            check=True, capture_output=True,
        )
        return np.loadtxt(out, delimiter=',', comments='#', dtype=float)[:, :3]


def build_oars(drop=0.0):
    stations = [
        (1, 40.5, 65.5, 35.5, 9.0 - drop, 0.0),
        (2, 77.5, 65.5, 35.5, 9.0 - drop, 0.0),
    ]
    oars = []
    oid = 1
    for idx, x, ys, yp, pz, rot_s in stations:
        oars.append({
            'name': f'oar-S{idx}', 'side': 'S', 'station': idx,
            'at': [x, ys, pz], 'pivot': [1.5, 16.5, 16.5],
            'rotate': [rot_s, 0.0, 0.0], 'mirror': '', 'scale': 0.5,
            'meta': {'id': f'oar-{oid}', 'kind': 'oar', 'rowers': 1, 'side': 'S', 'stroke_deg': 30, 'dip_deg': 12},
        })
        oid += 1
        oars.append({
            'name': f'oar-P{idx}', 'side': 'P', 'station': idx,
            'at': [x, yp, pz], 'pivot': [1.5, 16.5, 16.5],
            'rotate': [-rot_s, 0.0, 0.0], 'mirror': 'y', 'scale': 0.5,
            'meta': {'id': f'oar-{oid}', 'kind': 'oar', 'rowers': 1, 'side': 'P', 'stroke_deg': 30, 'dip_deg': 12},
        })
        oid += 1
    return oars


def transform_pt(pt_local, o, stroke_deg=0.0, dip_deg=0.0):
    sc = o['scale']
    px, py, pz = o['pivot']
    dx = (pt_local[0] + 0.5 - px) * sc
    dy = (pt_local[1] + 0.5 - py) * sc
    dz = (pt_local[2] + 0.5 - pz) * sc
    if o['mirror'] == 'y':
        dy = -dy
    rx = math.radians(o['rotate'][0])
    dy1 = dy * math.cos(rx) - dz * math.sin(rx)
    dz1 = dy * math.sin(rx) + dz * math.cos(rx)
    rd = math.radians(dip_deg if o['side'] == 'S' else -dip_deg)
    dy2 = dy1 * math.cos(rd) - dz1 * math.sin(rd)
    dz2 = dy1 * math.sin(rd) + dz1 * math.cos(rd)
    rs = math.radians(stroke_deg if o['side'] == 'S' else -stroke_deg)
    wx = o['at'][0] + dx * math.cos(rs) - dy2 * math.sin(rs)
    wy = o['at'][1] + dx * math.sin(rs) + dy2 * math.cos(rs)
    wz = o['at'][2] + dz2
    return wx, wy, wz


def eval_oars(oars, occ, oar_pts):
    hits = 0
    bad_rowers = 0
    blade_zs = []
    for o in oars:
        # 1. 檢查站姿席位 seat 與 14 格淨空 (1.4 m)
        sx, sy, sz = transform_pt((1.0, 3.0, 8.0), o)
        ix, iy, iz = int(math.floor(sx)), int(math.floor(sy)), int(math.floor(sz))
        stand_ok = (0 <= ix < SX and 0 <= iy < SY and iz >= 1 and occ[ix, iy, iz - 1] and not occ[ix, iy, iz : min(iz + 14, SZ)].any())
        if not stand_ok:
            bad_rowers += 1
        # 2. 記錄靜態槳葉末端高度
        _, _, bz = transform_pt((1.0, 66.0, 4.0), o)
        blade_zs.append(round(bz, 2))
        # 3. 掃掠碰撞檢查 (stroke -30..+30 step 5 × dip 0..12 step 4)
        for st in range(-30, 31, 5):
            for dp in (0, 4, 8, 12):
                for p in oar_pts:
                    wx, wy, wz = transform_pt(p, o, stroke_deg=st, dip_deg=dp)
                    gx, gy, gz = int(math.floor(wx)), int(math.floor(wy)), int(math.floor(wz))
                    if 0 <= gx < SX and 0 <= gy < SY and 0 <= gz < SZ and occ[gx, gy, gz]:
                        hits += 1
                        break
                else:
                    continue
                break
    return hits, bad_rowers, blade_zs


def eval_materials():
    # 體積 = 格數 * 0.001 m³
    H = load_vox(os.path.join(HERE, 'masks', 'hull_voxels.vox.txt'))
    D = load_vox(os.path.join(HERE, 'masks_deck', 'deck_voxels.vox.txt'))
    M = load_vox(os.path.join(HERE, 'masks_masts', 'mast_main.vox.txt'))
    hull_vox = int(H.sum())
    deck_vox = int(D.sum())
    mast_vox = int(M.sum())
    total_vox = hull_vox + deck_vox + mast_vox
    submerged_vox = int(H[:, :, :3].sum())  # z=0,1,2 below DWL=3
    disp_dwl3_t = round(submerged_vox * 0.001 * 1.025, 3)  # 海水比重 ~1.025
    mass_oak_t = round(total_vox * 0.001 * 0.70, 3)
    mass_bamboo_mix_t = round(total_vox * 0.001 * 0.385, 3)  # oak*0.55 (0.7*0.55=0.385)
    return {
        'voxels': {'hull': hull_vox, 'deck': deck_vox, 'mast': mast_vox, 'total': total_vox},
        'submerged_voxels_z_lt_3': submerged_vox,
        'dwl3_displacement_t': disp_dwl3_t,
        'mass_if_solid_oak_t': mass_oak_t,
        'recommended_material': 'oak*0.55',
        'recommended_effective_density_t_m3': 0.385,
        'mass_with_oak_055_t': mass_bamboo_mix_t,
        'reserve_buoyancy_payload_t': round(disp_dwl3_t - mass_bamboo_mix_t, 3),
    }


def run_cli(args):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise SystemExit(f"CLI error ({args}):\n{r.stdout}\n{r.stderr}")
    return r.stdout


def main():
    H = load_vox(os.path.join(HERE, 'masks', 'hull_voxels.vox.txt'))
    D = load_vox(os.path.join(HERE, 'masks_deck', 'deck_voxels.vox.txt'))
    M = load_vox(os.path.join(HERE, 'masks_masts', 'mast_main.vox.txt'))
    occ = H | D | M
    oar_pts = load_oar_pts()

    oars = build_oars(0.0)
    hits, bad_rowers, blade_zs = eval_oars(oars, occ, oar_pts)
    # 反向對照：把 pivot 降 5 格 (z=4.0)，槳柄必撞上護舷竹
    oars_probe = build_oars(5.0)
    hits_p, _, blade_zs_p = eval_oars(oars_probe, occ, oar_pts)
    assert hits == 0 and bad_rowers == 0, f'槳碰撞或站不下 hits={hits}, bad_rowers={bad_rowers}'
    assert hits_p > 0 and round(blade_zs[0] - blade_zs_p[0], 2) == 5.0

    mat_eval = eval_materials()
    rep = {
        'oars_count': len(oars),
        'sweep_collision_hits': hits,
        'bad_rowers': bad_rowers,
        'blade_z_at_rest': blade_zs,
        'reverse_control': {'probe_drop': 5.0, 'collision_hits': hits_p, 'blade_z_delta': round(blade_zs_p[0] - blade_zs[0], 2)},
        'materials_buoyancy': mat_eval,
    }
    with open(os.path.join(HERE, 'verify_oars_materials.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rep, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(rep, ensure_ascii=False, indent=2))

    if '--apply' in sys.argv:
        # 1. Mount 4 oars onto hull
        for o in oars:
            args = [
                '--arg', 'op=work', '--arg', 'sub=model', '--arg', 'persona=pinnacle',
                '--arg', f'work={WORK_HULL}', '--arg', f'name={o["name"]}',
                '--arg', f'source_work={OAR_WORK}',
                '--arg', f'pivot={o["pivot"][0]},{o["pivot"][1]},{o["pivot"][2]}',
                '--arg', f'at={o["at"][0]},{o["at"][1]},{o["at"][2]}',
                '--arg', f'scale={o["scale"]}',
                '--arg', f'rotate={o["rotate"][0]},{o["rotate"][1]},{o["rotate"][2]}',
                '--arg', f'meta={json.dumps(o["meta"], ensure_ascii=False, separators=(",", ":"))}',
            ]
            if o['mirror']:
                args += ['--arg', f'mirror={o["mirror"]}']
            run_cli(args)
            print(f'✓ model {o["name"]} -> {WORK_HULL}')

        # 2. Apply material oak*0.55 on structural links in assembly (hull, 甲板-main, 桅-main)
        mat_tsv = os.path.join(HERE, 'materials_meta.tsv')
        mat_json = json.dumps({'material': 'oak*0.55'}, ensure_ascii=False)
        with open(mat_tsv, 'w', encoding='utf-8', newline='\n') as f:
            for lname in ('hull', '甲板-main', '桅-main'):
                f.write(f'link\t{lname}\t{mat_json}\n')
        run_cli(['--arg', 'op=work', '--arg', 'sub=meta', '--arg', 'persona=pinnacle',
                 '--arg', f'work={WORK_ASM}', '--arg', f'file={mat_tsv}'])
        print('✓ materials_meta.tsv (oak*0.55) applied to structural links')


if __name__ == '__main__':
    main()
