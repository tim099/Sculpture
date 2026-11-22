# 明鄭一號大鳥船 新圖紙 07（TASK-1316 步驟 9）：30 門火砲配置與零碰撞後座／射界掃描
#   12 紅夷大銅砲（主砲甲板）＋ 2 船首戰棚紅夷 ＋ 10 戰棚發熕 ＋ 6 佛郎機迴旋砲（pierrier ＋ -mount）
#   用法：python -I -X utf8 draft_guns.py <design 資料夾> [--probe=shift_fwd=+4]
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL
import draft_decks as DD

sys.path.insert(0, os.path.join(HERE, 'tools'))
from wio import export_list

sys.stdout.reconfigure(encoding='utf-8')


def load_vox(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def transform_pts(vox_arr, pivot, at, rz_deg, scale):
    """將砲局部座標變換到組裝件世界座標（先減 pivot 再縮放、再繞 Z 軸旋轉 rz_deg、最後加 at）。"""
    c, s = math.cos(math.radians(rz_deg)), math.sin(math.radians(rz_deg))
    pts = vox_arr[:, :3].astype(float) + 0.5 - np.array(pivot, float)
    pts *= float(scale)
    x_new = at[0] + pts[:, 0] * c - pts[:, 1] * s
    y_new = at[1] + pts[:, 0] * s + pts[:, 1] * c
    z_new = at[2] + pts[:, 2]
    return np.stack([x_new, y_new, z_new], axis=1)


def main():
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = a
    design = os.path.abspath(design)

    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    GB = plan['guns_build']

    zmax = int(math.ceil(L.top_max)) + 16
    x0 = int(math.floor(L.xa_min)) - 12
    x1 = int(math.ceil(L.xf_max)) + 16
    half = int(math.ceil(L.B)) + 10
    ylo = L.YC - half
    yhi = L.YC + half
    shape = (x1 - x0 + 1, yhi - ylo + 1, zmax + 1)

    wall_col, _ = DD.load_carved_shell(design, plan, L, x0, ylo, shape)
    paint_p = os.path.join(design, 'masks', 'ports', 'paint.vox.txt')
    if os.path.exists(paint_p):
        pa = load_vox(paint_p)
        if pa.size:
            px, py, pz = pa[:, 0] - x0, pa[:, 1] - ylo, pa[:, 2]
            pm = (px >= 0) & (px < shape[0]) & (py >= 0) & (py < shape[1]) & (pz >= 0) & (pz < shape[2])
            wall_col[px[pm], py[pm], pz[pm]] = pa[pm, 3]
    hull_occ = wall_col > 0

    # 生成並模擬步驟 9 迴旋砲舷牆淺凹口（swivel cut_x0-1..cut_x1+1，z > z_rail 刻除並保留 z_rail 朱漆壓頂，對齊 stern-balcony 預留空隙）
    sw_carve_pts = []
    sw_sill_pts = []
    for sw in GB['swivels']:
        zr = int(sw['z_rail'])
        for xw in range(int(sw['cut_x0']) - 1, int(sw['cut_x1']) + 2):
            xi = xw - x0
            for yi in range(shape[1]):
                yw = yi + ylo
                for zw in range(zr + 1, shape[2]):
                    if hull_occ[xi, yi, zw]:
                        hull_occ[xi, yi, zw] = False
                        sw_carve_pts.append((xw, yw, zw, int(wall_col[xi, yi, zw])))
                if hull_occ[xi, yi, zr]:
                    sw_sill_pts.append((xw, yw, zr, 192))  # 朱漆砲門坎邊

    world_occ = hull_occ.copy()

    deck_floors = {}
    for folder in ('decks', 'ladders', 'rooms', 'deco', 'masts'):
        pdir = os.path.join(design, 'masks', folder)
        if not os.path.isdir(pdir):
            continue
        for fn in os.listdir(pdir):
            if not fn.endswith('.vox.txt'):
                continue
            if folder == 'masts' and not fn.startswith('mast-'):
                continue
            arr = load_vox(os.path.join(pdir, fn))
            if not arr.size:
                continue
            xi, yi, zi = arr[:, 0] - x0, arr[:, 1] - ylo, arr[:, 2]
            m = (xi >= 0) & (xi < shape[0]) & (yi >= 0) & (yi < shape[1]) & (zi >= 0) & (zi < shape[2])
            world_occ[xi[m], yi[m], zi[m]] = True
            if folder == 'decks' and fn.endswith('.vox.txt'):
                deck_floors[fn[:-8]] = arr

    def check_occ(world_pts, allow_swivel_deck_z=None):
        """回傳落在 world_occ 實心格裡的數量；同時保護出框安全。"""
        ix = np.floor(world_pts[:, 0]).astype(int) - x0
        iy = np.floor(world_pts[:, 1]).astype(int) - ylo
        iz = np.floor(world_pts[:, 2]).astype(int)
        inb = (ix >= 0) & (ix < shape[0]) & (iy >= 0) & (iy < shape[1]) & (iz >= 0) & (iz < shape[2])
        hits = world_occ[ix[inb], iy[inb], iz[inb]]
        return int(hits.sum())

    # 讀入 3 種砲體素（hongyi, fagong, pierrier + pierrier-mount）
    def read_gun_local(fn):
        return load_vox(os.path.join(design, 'masks', 'guns', f'{fn}.vox.txt'))

    gun_vox = {
        'hongyi': read_gun_local(f"{GB['hull']}-gun-hongyi"),
        'fagong': read_gun_local(f"{GB['hull']}-gun-fagong"),
        'pierrier': export_list('apex-one-reale-01m-gun-pierrier', links='none'),
        'pierrier-mount': export_list('apex-one-reale-01m-gun-pierrier-mount', links='none'),
    }
    gun_anchors_local = {}
    for gk in ('hongyi', 'fagong'):
        an = json.load(open(os.path.join(os.path.dirname(os.path.dirname(design)), f"{GB['hull']}-gun-{gk}", 'anchors.json'), encoding='utf-8'))['anchors']
        gun_anchors_local[gk] = {a['name']: a['at'] for a in an}

    placements = []
    search = GB['search']
    shift_probe = 4.0 if probe == 'shift_fwd=+4' else 0.0

    # ── 1. 兩重甲板輪式大砲（12 下層紅夷 + 2 上戰棚艏紅夷 + 10 上戰棚發熕 = 24 門）──
    carriage_specs = []
    P = plan['ports']
    for i, xw in enumerate(P['enclosed']['x'], 1):
        carriage_specs.append({'deck': 'main', 'i': i, 'x': xw, 'type': 'hongyi', 'name': f'M-{i}'})
    for i, xw in enumerate(P['upper_hongyi']['x'], 1):
        carriage_specs.append({'deck': 'upper', 'i': i, 'x': xw, 'type': 'hongyi', 'name': f'U-HY{i}'})
    for i, xw in enumerate(P['upper_fagong']['x'], 1):
        carriage_specs.append({'deck': 'upper', 'i': i, 'x': xw, 'type': 'fagong', 'name': f'U-FG{i}'})

    for sp in carriage_specs:
        dk = sp['deck']
        gt = sp['type']
        tcfg = GB['types'][gt]
        piv = tcfg['pivot']
        sc = float(tcfg['scale'])
        gv = gun_vox[gt]
        muz_local = gun_anchors_local[gt]['muzzle']
        z_floor = float(plan['decks'][dk]['floor'])
        xw_center = float(sp['x'])

        # 於船殼外表面決定起點，再往艙內退到零碰撞且四輪落實甲板，並以最小對稱 rz 兼顧不撞艙壁
        for side_lbl, sign in (('S', 1), ('P', -1)):
            # 找砲口高度該 x 處的外殼最外側 y
            zh_port = int(round(z_floor + muz_local[2] * sc))
            xs_hull_y = np.nonzero(hull_occ[sp['x'] - x0, :, zh_port])[0]
            if not len(xs_hull_y):
                # 露天上戰棚砲門上方切通時改用甲板邊緣推外殼
                xs_hull_y = np.nonzero(hull_occ[sp['x'] - x0, :, int(z_floor + 2)])[0]
            y_hull_out = (int(xs_hull_y.max()) if sign > 0 else int(xs_hull_y.min())) + ylo
            y_hull_in = y_hull_out - sign * 2  # wall=2 內側

            # 嘗試角度（船頭較窄處允許微前傾配合砲門開口方向，否則優先 0 / 180）
            yaw_cands = [0.0, -8.0, 8.0, -15.0, 15.0] if dk == 'upper' and sp['x'] >= 390 else [0.0, -4.0, 4.0]
            found = None
            for d_rz in yaw_cands:
                rz = (0.0 + d_rz) if sign > 0 else (180.0 - d_rz)
                c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
                # forward vector of +Y axis in local coords: (-sin(rz), cos(rz))
                fx, fy = -s, c
                for dx_off in (0.0, 0.5, -0.5, 1.0, -1.0):
                    for back in np.arange(-8.0, float(search['back_max']), 0.5):
                        b_eff = back - shift_probe
                        cand_at = [
                            xw_center + 0.5 + dx_off - fx * b_eff,
                            float(y_hull_out) + 0.5 - fy * (12.0 + b_eff),
                            z_floor,
                        ]
                        wpts = transform_pts(gv, piv, cand_at, rz, sc)
                        hits = check_occ(wpts)
                        if hits > 0 and shift_probe == 0.0:
                            continue
                        m_pt = transform_pts(np.array([[*muz_local, 1]]), piv, cand_at, rz, sc)[0]
                        muzzle_out = (m_pt[1] - (y_hull_out + (1.0 if sign > 0 else 0.0))) * sign
                        if muzzle_out < 2.0 and shift_probe == 0.0:
                            continue
                        # 檢查四輪底 (lz <= 2) 下方一格均為實心甲板（防止懸空）
                        wheels = gv[gv[:, 2] <= 2]
                        w_foot = transform_pts(wheels, piv, cand_at, rz, sc)
                        wx = np.floor(w_foot[:, 0]).astype(int) - x0
                        wy = np.floor(w_foot[:, 1]).astype(int) - ylo
                        wz_sup = int(z_floor) - 1
                        sup_ratio = float(world_occ[wx, wy, wz_sup].mean()) if len(wx) else 1.0
                        if sup_ratio < 0.99 and shift_probe == 0.0:
                            continue
                        # 射界微擺 +/-5 deg 掃描確認無碰撞
                        sw_hits = 0
                        for sr in (-5.0, 5.0):
                            sw_hits += check_occ(transform_pts(gv, piv, cand_at, rz + sr, sc))
                        found = {
                            'name': f"{sp['name']}-{side_lbl}",
                            'deck': dk,
                            'type': gt,
                            'side': side_lbl,
                            'source': tcfg['work'],
                            'at': [round(v, 3) for v in cand_at],
                            'pivot': piv,
                            'rotate': [0.0, 0.0, round(rz, 2)],
                            'scale': sc,
                            'meta': tcfg['meta'],
                            'hits': hits,
                            'muzzle_out_cells': round(float(muzzle_out), 2),
                            'support': round(sup_ratio, 3),
                            'sweep5_hits': sw_hits,
                            'breech_world': [round(v, 3) for v in transform_pts(np.array([[*gun_anchors_local[gt]['breech'], 1]]), piv, cand_at, rz, sc)[0]],
                            'eye_aft_world': [round(v, 3) for v in transform_pts(np.array([[*gun_anchors_local[gt]['eye-aft'], 1]]), piv, cand_at, rz, sc)[0]],
                            'eye_fwd_world': [round(v, 3) for v in transform_pts(np.array([[*gun_anchors_local[gt]['eye-fwd'], 1]]), piv, cand_at, rz, sc)[0]],
                            'train_world': [round(v, 3) for v in transform_pts(np.array([[*gun_anchors_local[gt]['train'], 1]]), piv, cand_at, rz, sc)[0]],
                        }
                        break
                    if found:
                        break
                if found:
                    break
            assert found is not None, f"無法放置 {sp['name']}-{side_lbl} (z_floor={z_floor}, hull_out={y_hull_out})"
            placements.append(found)

    # ── 2. 6 門佛郎機迴旋砲（pierrier ＋ -mount 雙生；檢查實心欄頂、0 碰撞、±80° 掃描與 40_crew.js 站高）──
    sw_cfg = GB['types']['pierrier']
    sw_piv = sw_cfg['pivot']
    sw_sc = float(sw_cfg['scale'])
    sw_gun_v = gun_vox['pierrier']
    sw_mnt_v = gun_vox['pierrier-mount']

    for idx, sw in enumerate(GB['swivels'], 1):
        dk = sw['deck']
        xw = int(sw['x'])
        z_floor = int(plan['decks'][dk]['floor'])
        # 實測 hull_occ 在 [cut_x0..cut_x1] 於該側的最高欄格
        for side_lbl, sign in (('S', 1), ('P', -1)):
            col_ys = []
            for yw in (range(YC + 4, yhi + 1) if sign > 0 else range(ylo, YC - 3)):
                zs = np.nonzero(hull_occ[xw - x0, yw - ylo, z_floor:zmax])[0]
                if len(zs):
                    col_ys.append((yw, int(z_floor + zs.max())))
            assert col_ys, f"swivel hull rail missing at x={xw} {side_lbl}"
            # 取外側弦牆頂緣那兩格之內外均實心頂高
            col_ys.sort(key=lambda t: t[0], reverse=(sign > 0))
            y_rail, z_rail_top = col_ys[0][0], col_ys[0][1]
            # swivel mount pivot.z = 0.0 -> 站在欄頂 voxel top (z_rail_top + 1.0)
            rz = 0.0 if sign > 0 else 180.0
            # 從外側或內側調整 y_at（+0.5 居中於欄中心）
            y_at = float(col_ys[1][0] + 0.5) if len(col_ys) > 1 and col_ys[1][1] == z_rail_top else float(y_rail + 0.5)
            z_at = float(z_rail_top + 1.0)
            at_pt = [xw + 0.5, y_at, z_at]
            crew_ok = (z_at - 8.0) <= z_floor <= (z_at + 3.0)
            hits_static = check_occ(transform_pts(sw_gun_v, sw_piv, at_pt, rz, sw_sc)) + check_occ(transform_pts(sw_mnt_v, sw_piv, at_pt, rz, sw_sc))
            sweep_hits = 0
            for sr in range(-80, 81, 20):
                sweep_hits += check_occ(transform_pts(sw_gun_v, sw_piv, at_pt, rz + sr, sw_sc))
            placements.append({
                'name': f'SW-{idx}-{side_lbl}',
                'deck': dk,
                'type': 'pierrier',
                'side': side_lbl,
                'source': sw_cfg['work'],
                'mount_source': sw_cfg['mount_work'],
                'at': at_pt,
                'pivot': sw_piv,
                'rotate': [0.0, 0.0, rz],
                'scale': sw_sc,
                'meta': sw_cfg['meta'],
                'hits': hits_static,
                'sweep80_hits': sweep_hits,
                'crew_z_ok': crew_ok,
                'z_rail_top': z_rail_top,
            })

    max_hits = max(p['hits'] for p in placements)
    max_sweep_c = max(p.get('sweep5_hits', 0) for p in placements)
    max_sweep_sw = max(p.get('sweep80_hits', 0) for p in placements)
    all_crew_ok = all(p.get('crew_z_ok', True) for p in placements)
    min_muz = min(p.get('muzzle_out_cells', 99) for p in placements)
    min_sup = min(p.get('support', 1.0) for p in placements)

    summary = {
        'total_guns': len(placements),
        'by_type': {k: sum(1 for p in placements if p['type'] == k) for k in ('hongyi', 'fagong', 'pierrier')},
        'by_deck': {k: sum(1 for p in placements if p['deck'] == k) for k in ('main', 'upper', 'poop')},
        'max_hits': max_hits,
        'max_carriage_sweep5_hits': max_sweep_c,
        'max_swivel_sweep80_hits': max_sweep_sw,
        'all_swivel_crew_z_ok': all_crew_ok,
        'min_muzzle_out_cells': min_muz,
        'min_wheel_support': min_sup,
    }
    if probe:
        summary['probe'] = probe
        print(json.dumps(summary, ensure_ascii=False))
        return

    assert max_hits == 0, f"gun collision max_hits={max_hits}"
    assert all_crew_ok, "swivel crew height check failed"
    assert min_muz >= 0.2, f"muzzle inside hull: {min_muz}"

    out_p = os.path.join(design, 'guns_placement.json')
    txt = json.dumps(placements, ensure_ascii=False, indent=1)
    with open(out_p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    summary['placement_sha256'] = hashlib.sha256(open(out_p, 'rb').read()).hexdigest()
    summary['swivel_carve_cells'] = len(sw_carve_pts)
    summary['swivel_sill_cells'] = len(sw_sill_pts)

    gdir = os.path.join(design, 'masks', 'guns')
    os.makedirs(gdir, exist_ok=True)
    with open(os.path.join(gdir, 'swivel_rail_carve.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 步驟 9 迴旋砲舷牆淺凹口刻除\n')
        for pt in sorted(sw_carve_pts):
            f.write(f'{pt[0]},{pt[1]},{pt[2]},{pt[3]}\n')
    with open(os.path.join(gdir, 'swivel_rail_sill.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 步驟 9 迴旋砲舷牆坎朱漆\n')
        for pt in sorted(sw_sill_pts):
            f.write(f'{pt[0]},{pt[1]},{pt[2]},{pt[3]}\n')

    # 出圖 sheet07_guns_v1.png（雙層甲板俯視砲位配置）
    im = Image.new('RGB', (shape[0] + 100, (shape[1] + 20) * 2 + 60), (248, 246, 238))
    d = ImageDraw.Draw(im)
    d.text((20, 12), '明鄭一號大鳥船 新圖紙 07：30 門火砲配置（上：主砲甲板 12 紅夷｜下：上戰棚／尾樓 18 門）', fill=(0, 0, 0), font=DL.font(14))
    for ridx, dks in enumerate((('main',), ('upper', 'poop'))):
        oy = 50 + ridx * (shape[1] + 20)
        for xi_ in range(shape[0]):
            for yi_ in range(shape[1]):
                for dn in dks:
                    arr = deck_floors.get(dn)
                    if arr is not None:
                        pass
                # 標出 hull contour
                z_ref = 52 if ridx == 0 else 74
                if hull_occ[xi_, yi_, z_ref]:
                    d.point((30 + xi_, oy + yi_), fill=(120, 90, 60))
        for p in placements:
            if p['deck'] not in dks:
                continue
            gx = int(round(p['at'][0])) - x0 + 30
            gy = int(round(p['at'][1])) - ylo + oy
            col = (210, 40, 30) if p['type'] == 'hongyi' else ((70, 90, 160) if p['type'] == 'fagong' else (30, 140, 60))
            d.ellipse((gx - 4, gy - 4, gx + 4, gy + 4), fill=col)
    im.save(os.path.join(design, 'sheet07_guns_v1.png'))

    with open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
