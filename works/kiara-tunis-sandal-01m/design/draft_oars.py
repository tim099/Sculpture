# 步驟 13 動力槳與五金材質（Ship_Oars §9.10 ＋ Ship_Materials §9.5）：
#   - 複用共用元件 basecamp-piragua-01m-oar（0.05 m/格, scale=0.5, 已具 pivot/blade/seat 固定點），掛於船殼 kiara-tunis-sandal-01m 形成 船殼/oar-{S,P}{1..3}
#   - 3 對 6 支單人坐姿槳分別對位 thwart-1(x=35), thwart-2(x=43), thwart-3(x=81)，以極小傾角對齊 DWL z=4.0（槳葉浸水 -0.02 m）
#   - 完整划槳掃掠檢查（stroke ±30° × dip 0..+12°）＋ 槳手站/坐淨高（14 格）＋ 靠泊寬度對帳 ＋ 金屬配件（錨=iron, 艉燈=brass）
#   用法：python -I -X utf8 draft_oars.py [--apply] [--probe=oar_drop=3]
import sys, os, json, math, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_ASM = 'kiara-tunis-sandal-01m-assembly'
WORK_HULL = 'kiara-tunis-sandal-01m'
OAR_WORK = 'basecamp-piragua-01m-oar'
SX, SY, SZ = 136, 101, 110


def load_vox(path):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros((SX, SY, SZ), bool)
    if len(a):
        G[a[:, 0], a[:, 1], a[:, 2]] = True
    return G


def build_oars(probe):
    drop = float(probe.get('oar_drop', 0.0))
    # 各坐板站位：x、右舷舷緣 y_S、左舷舷緣 y_P (=101-y_S)、pivot z、補償 x 傾角 (使 blade 中心齊於 DWL z≈3.8)
    stations = [
        (1, 35.5, 59.5, 41.5, 10.65 - drop, -1.8),
        (2, 43.5, 60.5, 40.5,  9.65 - drop,  0.0),
        (3, 81.5, 60.5, 40.5,  9.65 - drop,  0.0),
    ]
    oars = []
    oid = 1
    for idx, x, ys, yp, pz, rot_s in stations:
        # 右舷 S（rotate rot_s,0,0）
        oars.append({
            'name': f'oar-S{idx}', 'side': 'S', 'station': idx,
            'at': [x, ys, pz], 'pivot': [1.5, 16.5, 16.5],
            'rotate': [rot_s, 0.0, 0.0], 'mirror': '', 'scale': 0.5,
            'meta': {'id': f'oar-{oid}', 'kind': 'oar', 'rowers': 1, 'side': 'S', 'stroke_deg': 30, 'dip_deg': 12},
        })
        oid += 1
        # 左舷 P（mirror y, rotate -rot_s,0,0）
        oars.append({
            'name': f'oar-P{idx}', 'side': 'P', 'station': idx,
            'at': [x, yp, pz], 'pivot': [1.5, 16.5, 16.5],
            'rotate': [-rot_s, 0.0, 0.0], 'mirror': 'y', 'scale': 0.5,
            'meta': {'id': f'oar-{oid}', 'kind': 'oar', 'rowers': 1, 'side': 'P', 'stroke_deg': 30, 'dip_deg': 12},
        })
        oid += 1
    return oars


def load_oar_pts():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, 'oar.txt').replace('\\', '/')
        subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list',
                        '--arg', f'work={OAR_WORK}', '--arg', f'out={out}'],
                       check=True, capture_output=True)
        return np.loadtxt(out, delimiter=',', comments='#', dtype=float)[:, :3]


def transform_pt(pt_local, o, stroke_deg=0.0, dip_deg=0.0):
    scale = o['scale']
    px, py, pz = o['pivot']
    dx = (pt_local[0] + 0.5 - px) * scale
    dy = (pt_local[1] + 0.5 - py) * scale
    dz = (pt_local[2] + 0.5 - pz) * scale
    if o['mirror'] == 'y':
        dy = -dy
    # 靜態 X 軸微調傾角
    rx = math.radians(o['rotate'][0])
    dy1 = dy * math.cos(rx) - dz * math.sin(rx)
    dz1 = dy * math.sin(rx) + dz * math.cos(rx)
    # 划槳動畫：回槳抬升 dip (繞 X) ＋ 前後掃掠 stroke (繞 Z)
    rd = math.radians(dip_deg if o['side'] == 'S' else -dip_deg)
    dy2 = dy1 * math.cos(rd) - dz1 * math.sin(rd)
    dz2 = dy1 * math.sin(rd) + dz1 * math.cos(rd)
    rs = math.radians(stroke_deg if o['side'] == 'S' else -stroke_deg)
    wx = o['at'][0] + dx * math.cos(rs) - dy2 * math.sin(rs)
    wy = o['at'][1] + dx * math.sin(rs) + dy2 * math.cos(rs)
    wz = o['at'][2] + dz2
    return wx, wy, wz


def main():
    apply_mode = '--apply' in sys.argv[1:]
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)

    H = load_vox(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'))
    D = load_vox(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt'))
    M = load_vox(os.path.join(HERE, 'masks', 'masts', 'mast.vox.txt'))
    F = load_vox(os.path.join(HERE, 'masks', 'rig', 'flagstaff.vox.txt'))
    # 也納入兩側護舷外包絡（x=51..54 y=37/63, x=67..70 y=36/64）確認掃掠不碰護舷
    FD = np.zeros_like(H)
    FD[51:55, 37:39, 5:10] = True
    FD[51:55, 63:65, 5:10] = True
    FD[67:71, 36:38, 5:10] = True
    FD[67:71, 64:66, 5:10] = True
    occ = H | D | M | F | FD

    oar_pts = load_oar_pts()
    oars = build_oars(probe)

    static_hits = 0
    sweep_hits = 0
    seat_ok = True
    gunwale_near_ok = True
    per_oar = []
    min_y_tip, max_y_tip = 999.0, -999.0

    for o in oars:
        # 1. 靜態與全週期掃掠（-30..+30 × 0..12°）
        sh = 0
        wh = 0
        for sd in (-30, -15, 0, 15, 30):
            for dd in (0, 12):
                if sd == 0 and dd == 0:
                    for p in oar_pts:
                        wx, wy, wz = transform_pt(p, o, 0, 0)
                        ix, iy, iz = int(math.floor(wx)), int(math.floor(wy)), int(math.floor(wz))
                        if 0 <= ix < SX and 0 <= iy < SY and 0 <= iz < SZ and occ[ix, iy, iz]:
                            sh += 1
                else:
                    for p in oar_pts:
                        wx, wy, wz = transform_pt(p, o, sd, dd)
                        ix, iy, iz = int(math.floor(wx)), int(math.floor(wy)), int(math.floor(wz))
                        if 0 <= ix < SX and 0 <= iy < SY and 0 <= iz < SZ and occ[ix, iy, iz]:
                            wh += 1
        static_hits += sh
        sweep_hits += wh

        # 2. 檢查 blade 浸水深度 (DWL z=4.0)、seat 坐板支撐與 14 格淨高、pivot 旁 8 格內有舷緣
        bx, by, bz = transform_pt((1.0, 66.0, 4.0), o, 0, 0)
        sx, sy, sz = transform_pt((1.0, 3.0, 8.0), o, 0, 0)
        min_y_tip, max_y_tip = min(min_y_tip, by), max(max_y_tip, by)

        is_x, is_y = int(math.floor(sx)), int(math.floor(sy))
        thwart_solid = bool(D[is_x, is_y, 4])
        headroom_clear = bool(not occ[is_x, is_y, 5:19].any())
        if not (thwart_solid and headroom_clear):
            seat_ok = False

        px0, py0, pz0 = int(math.floor(o['at'][0])), int(math.floor(o['at'][1])), int(math.floor(o['at'][2]))
        has_gunwale = bool(H[max(0, px0 - 2):px0 + 3, max(0, py0 - 3):py0 + 4, max(0, pz0 - 3):pz0 + 2].any())
        if not has_gunwale:
            gunwale_near_ok = False

        per_oar.append({
            'name': o['name'], 'blade_z': round(bz, 2), 'blade_vs_dwl_m': round((bz - 4.0) * 0.1, 3),
            'seat_xy': [round(sx, 1), round(sy, 1)], 'thwart_solid': thwart_solid, 'headroom_clear': headroom_clear,
            'static_hits': sh, 'sweep_hits': wh,
        })

    R = {
        'oar_count': len(oars),
        'port_oars': sum(1 for o in oars if o['side'] == 'P'),
        'stbd_oars': sum(1 for o in oars if o['side'] == 'S'),
        'rowers_total': len(oars),
        'static_hits': static_hits,
        'sweep_hits': sweep_hits,
        'all_seats_ok': seat_ok,
        'all_gunwales_near': gunwale_near_ok,
        'rowing_span_m': round((max_y_tip - min_y_tip) * 0.1, 2),
        'berth_hull_beam_m': 2.7,
        'oars': per_oar,
    }
    if probe:
        print(json.dumps({'probe': probe, 'static_hits': R['static_hits'], 'sweep_hits': R['sweep_hits'],
                          'blade_z_0': R['oars'][0]['blade_z']}, ensure_ascii=False))
        return

    with open(os.path.join(HERE, 'verify_oars.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, indent=1, ensure_ascii=False)
    print('OARS_CHECK:', json.dumps({k: v for k, v in R.items() if k != 'oars'}, ensure_ascii=False))

    if not apply_mode:
        return

    for o in oars:
        cmd = [
            'senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=model', '--arg', 'persona=kiara',
            '--arg', f'work={WORK_HULL}', '--arg', f'name={o["name"]}', '--arg', f'source_work={OAR_WORK}',
            '--arg', 'at=' + ','.join(str(v) for v in o['at']),
            '--arg', 'pivot=' + ','.join(str(v) for v in o['pivot']),
            '--arg', 'rotate=' + ','.join(str(v) for v in o['rotate']),
            '--arg', f'scale={o["scale"]}', '--arg', 'meta=' + json.dumps(o['meta'], ensure_ascii=False),
            '--arg', 'overwrite=1',
        ]
        if o['mirror']:
            cmd += ['--arg', f'mirror={o["mirror"]}']
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(f'oar mount fail {o["name"]}:\n{r.stdout}\n{r.stderr}')

    # 步驟 13 材質：金屬五金標示（鐵錨 material=iron、黃銅艉燈 material=brass；均保持尖銳方格 render=voxel）
    for mname, mmeta in [
        ('錨-S', {'material': 'iron', 'render': 'voxel'}),
        ('艉燈', {'material': 'brass', 'render': 'voxel'}),
    ]:
        r = subprocess.run([
            'senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=meta', '--arg', 'persona=kiara',
            '--arg', f'work={WORK_ASM}', '--arg', 'part=model', '--arg', f'name={mname}',
            '--arg', 'meta=' + json.dumps(mmeta, ensure_ascii=False),
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(f'material meta fail {mname}:\n{r.stdout}\n{r.stderr}')
    print('Mounted 6 oars + hardware material meta cleanly!')


if __name__ == '__main__':
    main()
