# 步驟 11 舵與錨（kiara-tunis-sandal-01m-rudder ＋ kotoko-fusta-01m-anchor-grapnel ＋ hull/hawse-S）：
#   - 艉柱舵與整合式舵柄：舵底停於 z=1（不高出也不深過平底船底 z=0，維持 0.4 m 突尼斯湖吃水線！），舵柄於 z=12 越過艉鏡 z=10 向前伸至舵手位
#   - 3D 掃掠檢核：-35°..+35° 每 1° 取樣舵體素與船殼／艉飾／右舷旗桿／左舷艉燈之最小間隙＝0 碰撞
#   - 地中海四爪錨（kotoko-fusta-01m-anchor-grapnel, scale=0.3）懸於右舷船首外側，避開 DWL z<4 且設 hawse-S
#   用法：python -I -X utf8 draft_helm.py [--apply] [--probe=rudder_dx=+2]
import sys, os, json, math, subprocess
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_ASM = 'kiara-tunis-sandal-01m-assembly'
WORK_HULL = 'kiara-tunis-sandal-01m'
WORK_RUD = 'kiara-tunis-sandal-01m-rudder'
SX, SY, SZ = 136, 101, 30
YC = 50


def load_vox(path):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros((SX, SY, SZ), bool)
    if len(a):
        G[a[:, 0], a[:, 1], a[:, 2]] = True
    return G


def build_rudder(probe):
    dx = int(probe.get('rudder_dx', 0))
    G = np.zeros((SX, SY, SZ), np.uint8)
    hx = 16 + dx

    # 主舵軸 (z=1..12)
    G[hx, YC, 1:13] = 136
    # 舵柱上下鐵件／箍帶（木色與深鐵帶）
    for z in (1, 4, 8, 11, 12):
        G[hx, YC, z] = 68

    # 舵葉（z=1..9 向後展開，下寬上收、總深不低於船底 z=0 確保淺水安全）
    for z in range(1, 10):
        x0 = hx - 4 if z <= 7 else hx - 3
        for x in range(x0, hx):
            G[x, YC, z] = 68 if z in (4, 8) else 136

    # 鉸鏈凸耳（僅於 z=4, 8 向前伸 1 格接緊艉柱）
    G[hx + 1, YC, 4] = 68
    G[hx + 1, YC, 8] = 68

    # 前伸舵柄（於 z=12 越過艉鏡 z=10、兩邊留空氣，x 從 hx 到 hx+7 = 23）
    for x in range(hx, hx + 8):
        G[x, YC, 12] = 177 if x >= hx + 5 else 68

    hinge = [float(hx) + 0.5, float(YC) + 0.5, 1.0]
    stock_top = (hx, YC, 10)
    return G, hinge, stock_top


def check_rudder_sweep(G, hinge, occ_obs, continuous_boxes=()):
    pts = np.argwhere(G > 0)
    hx, hy, hz = hinge
    max_hits = 0
    for deg in range(-35, 36):
        th = math.radians(deg)
        ct, st = math.cos(th), math.sin(th)
        hits = 0
        for x, y, z in pts:
            # 取每格內 4 角點測試旋轉掃掠包絡
            for ox in (-0.35, 0.35):
                for oy in (-0.35, 0.35):
                    px = (x + 0.5 + ox) - hx
                    py = (y + 0.5 + oy) - hy
                    wx = hx + px * ct - py * st
                    wy = hy + px * st + py * ct
                    ix, iy, iz = int(math.floor(wx)), int(math.floor(wy)), int(z)
                    if 0 <= ix < SX and 0 <= iy < SY and 0 <= iz < SZ and occ_obs[ix, iy, iz]:
                        hits += 1
                    for bx0, by0, bz0, bx1, by1, bz1 in continuous_boxes:
                        if bx0 <= wx <= bx1 and by0 <= wy <= by1 and bz0 <= (z + 0.5) <= bz1:
                            hits += 1
        max_hits = max(max_hits, hits)
    return max_hits


def check_anchor(probe, occ_obs):
    dy = float(probe.get('anchor_in', 0.0))
    scale = 0.3
    pivot = (9.5, 9.5, 24.0)
    at = (103.5, 58.2 + dy, 12.2)
    hawse = (103, 54, 8)
    # 匯出四爪錨實格檢核碰撞
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, 'anc.txt').replace('\\', '/')
        subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list',
                        '--arg', 'work=kotoko-fusta-01m-anchor-grapnel', '--arg', f'out={out}'],
                       check=True, capture_output=True)
        pts = np.loadtxt(out, delimiter=',', comments='#', dtype=float)[:, :3]
    ca = math.cos(math.radians(45.0))
    sa = math.sin(math.radians(45.0))
    hits = 0
    zmin, zmax = 999.0, -999.0
    ymin, ymax = 999.0, -999.0
    for x, y, z in pts:
        dx = (x + 0.5 - pivot[0]) * scale
        dy_l = (y + 0.5 - pivot[1]) * scale
        dz = (z + 0.5 - pivot[2]) * scale
        wx = at[0] + dx * ca - dy_l * sa
        wy = at[1] + dx * sa + dy_l * ca
        wz = at[2] + dz
        zmin, zmax = min(zmin, wz), max(zmax, wz)
        ymin, ymax = min(ymin, wy), max(ymax, wy)
        ix, iy, iz = int(math.floor(wx)), int(math.floor(wy)), int(math.floor(wz))
        if 0 <= ix < SX and 0 <= iy < SY and 0 <= iz < SZ and occ_obs[ix, iy, iz]:
            hits += 1
    return {
        'anchor_hits': hits,
        'at': list(at), 'pivot': list(pivot), 'rotate': [0, 0, 45], 'scale': scale, 'hawse': hawse,
        'world_y_range': [round(ymin, 2), round(ymax, 2)],
        'world_z_range': [round(zmin, 2), round(zmax, 2)],
        'above_dwl': bool(zmin >= 4.0),
    }


def run_cli(args):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise SystemExit(f'CLI fail {" ".join(args)}:\n{r.stdout}\n{r.stderr}')
    return r.stdout


def main():
    apply_mode = '--apply' in sys.argv[1:]
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)

    H = load_vox(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'))
    D = load_vox(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt'))
    F = load_vox(os.path.join(HERE, 'masks', 'rig', 'flagstaff.vox.txt'))
    # 也納入船尾裝飾 stern-orn 與艉燈實測外框作連續避讓檢核
    O = np.zeros_like(H)
    O[18, 46:49, 6:10] = True
    O[18, 52:55, 6:10] = True
    obs = H | D | F | O
    lantern_box = [(17.61, 44.81, 11.0, 19.99, 47.19, 16.04)]

    G, hinge, stock_top = build_rudder(probe)
    rud_sweep_hits = check_rudder_sweep(G, hinge, obs, lantern_box)
    _, n_rud = ndimage.label(G > 0)
    anc_info = check_anchor(probe, H | D)

    R = {
        'rudder_cells': int((G > 0).sum()),
        'rudder_components': int(n_rud),
        'rudder_hinge': hinge,
        'rudder_stock_top': list(stock_top),
        'rudder_z_min': int(np.argwhere(G > 0)[:, 2].min()),
        'rudder_sweep_35deg_hits': int(rud_sweep_hits),
        'anchor': anc_info,
    }
    if probe:
        print(json.dumps({'probe': probe, 'rudder_sweep_35deg_hits': R['rudder_sweep_35deg_hits'], 'anchor_hits': anc_info['anchor_hits']}, ensure_ascii=False))
        return

    os.makedirs(os.path.join(HERE, 'masks', 'helm'), exist_ok=True)
    rud_vox = os.path.join(HERE, 'masks', 'helm', 'rudder.vox.txt')
    pts = np.argwhere(G > 0)
    with open(rud_vox, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 突尼斯湖轉運艇 Sandal 艉柱舵與舵柄（draft_helm.py）x,y,z,color\n')
        for x, y, z in pts:
            f.write(f'{x},{y},{z},{G[x, y, z]}\n')

    with open(os.path.join(HERE, 'verify_helm.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, indent=1, ensure_ascii=False)
    print('HELM_CHECK:', json.dumps(R, ensure_ascii=False))

    if not apply_mode:
        return

    # 1. 落格舵並登記 stock-top
    chk = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=stats', '--arg', f'work={WORK_RUD}'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    if 'total_voxels = 0' in chk.stdout:
        subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'),
                        WORK_RUD, '0', rud_vox], check=True)
    run_cli(['--arg', 'op=work', '--arg', 'sub=anchor', '--arg', 'persona=kiara',
             '--arg', f'work={WORK_RUD}', '--arg', 'name=stock-top',
             '--arg', f'at={stock_top[0]},{stock_top[1]},{stock_top[2]}',
             '--arg', 'note=步驟 11 舵頭連接點', '--arg', 'overwrite=1'])

    # 2. 掛成外部模型 `舵` (kind=rudder + spin)
    rud_meta = {
        'id': 'rudder-1', 'kind': 'rudder',
        'hinge_x': hinge[0], 'hinge_y': hinge[1], 'hinge_z': hinge[2],
        'axis_x': 0.0, 'axis_y': 0.0, 'axis_z': 1.0,
        'max_deg': 35, 'turn_axis': 'hinge',
        'spin': 'rudder', 'spin_k': 35, 'spin_min': -35, 'spin_max': 35, 'spin_lag': 0.3,
    }
    pv = ','.join(str(v) for v in hinge)
    run_cli(['--arg', 'op=work', '--arg', 'sub=model', '--arg', 'persona=kiara',
             '--arg', f'work={WORK_ASM}', '--arg', 'name=舵', '--arg', f'source_work={WORK_RUD}',
             '--arg', f'at={pv}', '--arg', f'pivot={pv}', '--arg', 'scale=1',
             '--arg', 'meta=' + json.dumps(rud_meta, ensure_ascii=False), '--arg', 'overwrite=1'])

    # 3. 登記船殼錨鏈孔 hawse-S 並掛上共用四爪錨 `錨-S`
    hx, hy, hz = anc_info['hawse']
    run_cli(['--arg', 'op=work', '--arg', 'sub=anchor', '--arg', 'persona=kiara',
             '--arg', f'work={WORK_HULL}', '--arg', 'name=hawse-S',
             '--arg', f'at={hx},{hy},{hz}', '--arg', 'note=步驟 11 右舷錨鏈孔', '--arg', 'overwrite=1'])
    anc_meta = {'id': 'anchor-1', 'kind': 'anchor', 'anchor': 'bower', 'hawse': f'{hx},{hy},{hz}'}
    run_cli(['--arg', 'op=work', '--arg', 'sub=model', '--arg', 'persona=kiara',
             '--arg', f'work={WORK_ASM}', '--arg', 'name=錨-S', '--arg', 'source_work=kotoko-fusta-01m-anchor-grapnel',
             '--arg', 'at=' + ','.join(str(v) for v in anc_info['at']),
             '--arg', 'pivot=' + ','.join(str(v) for v in anc_info['pivot']),
             '--arg', 'rotate=0,0,45', '--arg', f'scale={anc_info["scale"]}',
             '--arg', 'meta=' + json.dumps(anc_meta, ensure_ascii=False)])
    print('Mounted rudder and anchor cleanly!')


if __name__ == '__main__':
    main()
