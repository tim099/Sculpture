# 福建趕繒船 新圖紙 06（TASK-1314 步驟 7）：雙桅（頭桅・大桅）、4 根主帆桁與 16 根扇形竹篾（yard=batten）
#   出處：kaguya-shachuan-01m/design/draft_masts.py ＋ draft_battens.py（依福建趕繒船雙桅硬篷規格與 Ship_Masts / Ship_Battens 寫）
#   用法：python -I -X utf8 draft_masts.py <design 資料夾> [--probe=shift_mast_fore=-3|batten_short=-6]
import hashlib
import json
import math
import os
import sys
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import build as hull_build

sys.stdout.reconfigure(encoding='utf-8')


def load_vox_map(path):
    arr = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    return {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in arr}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def check_struct_stats(vox_set, yc=None):
    if not vox_set:
        return {'count': 0, 'components_6': 0, 'cavities': 0, 'mirror_diff': 0}
    xs = [p[0] for p in vox_set]
    ys = [p[1] for p in vox_set]
    zs = [p[2] for p in vox_set]
    x0, y0, z0 = min(xs) - 1, min(ys) - 1, min(zs) - 1
    arr = np.zeros((max(xs) - x0 + 2, max(ys) - y0 + 2, max(zs) - z0 + 2), dtype=bool)
    for x, y, z in vox_set:
        arr[x - x0, y - y0, z - z0] = True
    _, nc = ndimage.label(arr)
    bg = ndimage.label(~arr)[0]
    cav = int(np.sum((~arr) & (bg != int(bg[0, 0, 0]))))
    mdiff = sum(1 for (x, y, z) in vox_set if (x, 2 * yc - y, z) not in vox_set) if yc is not None else 0
    return {'count': len(vox_set), 'components_6': int(nc), 'cavities': cav, 'mirror_diff': int(mdiff)}


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def mast_x(spec, z):
    return spec['x'] + (z - spec['heel_z']) * math.tan(math.radians(spec['rake_deg']))


def main():
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = a

    plan = HL.load_plan(design)
    L, _, _, _, _ = hull_build(plan, None)
    YC = L.YC
    C = plan['hull_build']['colors']
    WOOD = int(C['hull']['v'])   # 177 福杉／竹身
    FIR = int(C['inner']['v'])   # 141 桅身杉木
    TRIM = int(C['trim']['v'])   # 104 深硬木束箍／竹節
    GOLD = int(C['gold']['v'])   # 212 桅頂金帽

    # 讀入步驟 4 + 5 + 6 全部結構占格，防 1 格穿模重疊
    hull_map = load_vox_map(os.path.join(design, 'masks', 'hull', 'hull_01.vox.txt'))
    carve_map = load_vox_map(os.path.join(design, 'masks', 'ports', 'carve.vox.txt'))
    for k in carve_map:
        hull_map.pop(k, None)
    occ = set(hull_map.keys())
    for sub in ('decks', 'ladders'):
        fd = os.path.join(design, 'masks', sub)
        for fn in sorted(os.listdir(fd)):
            if fn.endswith('.vox.txt'):
                occ.update(load_vox_map(os.path.join(fd, fn)).keys())
    for fn in ('stern_glass.vox.txt', 'stern_balcony.vox.txt'):
        p = os.path.join(design, 'masks', 'deco', fn)
        if os.path.exists(p):
            occ.update(load_vox_map(p).keys())

    ms = plan['masts']
    out_dir = os.path.join(design, 'masks', 'masts')
    os.makedirs(out_dir, exist_ok=True)
    masts_meta = {}
    probe_result = {}

    # ── 1. 兩根下桅（fore & main）：直接踩實 z=8 底艙地板 (heel_z=9)，帶木箍、桅夾斗盤 (trestletrees) 與金帽 ──
    for mk in ('fore', 'main'):
        sp = dict(ms[mk])
        if mk == 'fore' and probe == 'shift_mast_fore=-3':
            sp['x'] = sp['x'] - 3
        ang = math.radians(sp['rake_deg'])
        z0 = int(sp['heel_z'])
        z1 = int(round(z0 + sp['len'] * math.cos(ang)))
        r0, r1 = sp['r']

        vox = {}
        ov_hits = 0
        for z in range(z0, z1 + 1):
            t = (z - z0) / max(z1 - z0, 1)
            r = r0 + (r1 - r0) * t
            xc = mast_x(sp, z)
            ix0, ix1 = int(math.floor(xc - r - 1)), int(math.ceil(xc + r + 1))
            iy0, iy1 = int(math.floor(YC - r - 1)), int(math.ceil(YC + r + 1))
            is_woold = ((z - z0) % 22 == 0 and z < z1 - 12)
            for x in range(ix0, ix1 + 1):
                for y in range(iy0, iy1 + 1):
                    if (x - xc) ** 2 + (y - YC) ** 2 <= r * r:
                        if (x, y, z) in occ:
                            ov_hits += 1
                            continue
                        col = GOLD if z >= z1 - 2 else (TRIM if is_woold else FIR)
                        vox[(x, y, z)] = col
        # 桅夾與斗盤木樑（trestletrees + hounds 處，緊貼桅軸 0 懸空；高度 z1-12..z1-10）
        for z in range(z1 - 12, z1 - 9):
            xc = int(round(mast_x(sp, z)))
            hw = 4 if mk == 'main' else 3
            hl = 2 if mk == 'main' else 1
            for x in range(xc - hl, xc + hl + 1):
                for y in range(YC - hw, YC + hw + 1):
                    if (abs(y - YC) == hw or z == z1 - 12 or abs(x - xc) == hl) and (x, y, z) not in occ:
                        vox[(x, y, z)] = TRIM

        if probe == 'shift_mast_fore=-3' and mk == 'fore':
            probe_result = {'probe': probe, 'fore_deck_hull_hits': ov_hits}
        if not probe:
            assert ov_hits == 0, f'{mk} 桅與船殼或甲板穿模 {ov_hits} 格（應為 0）！'
            # 驗證每層 z 均有實體（穿過甲板桅孔不中斷）且緊接底艙地板 z=8
            for z in range(z0, z1 + 1):
                assert any(p[2] == z for p in vox), f'{mk} 桅在 z={z} 斷裂！'
            assert any((x, y, z0 - 1) in occ for (x, y, z) in vox if z == z0), f'{mk} 桅腳未接觸底艙地板！'
            st = check_struct_stats(set(vox), YC)
            assert st['components_6'] == 1 and st['cavities'] == 0 and st['mirror_diff'] == 0, f'{mk} stats={st}'
            p_m = os.path.join(out_dir, f'mast_{mk}.vox.txt')
            with open(p_m, 'w', encoding='utf-8', newline='\n') as f:
                f.write(f'# 福建趕繒船 步驟 7：{mk} 下桅（0 重疊、0 空腔、含桅夾與金帽）x,y,z,color\n')
                for k in sorted(vox):
                    f.write(f'{k[0]},{k[1]},{k[2]},{vox[k]}\n')
            masts_meta[mk] = {
                'work': f'kotoko-ganzengchuan-01m-mast-{mk}',
                'cells': len(vox),
                'z_heel': z0,
                'z_top': z1,
                'top_x': round(mast_x(sp, z1), 3),
                'anchors': {
                    'heel': [int(round(sp['x'])), YC, z0],
                    'hounds': [int(round(mast_x(sp, z1 - 11))), YC, z1 - 11],
                    'cap': [int(round(mast_x(sp, z1 - 2))), YC, z1 - 2],
                    'top': [int(round(mast_x(sp, z1))), YC, z1],
                    'head': [int(round(mast_x(sp, z1))), YC, z1],
                },
                'stats': st,
                'sha256': sha256_file(p_m),
            }

    if probe == 'shift_mast_fore=-3':
        print(json.dumps(probe_result, ensure_ascii=False))
        return

    # ── 2. 4 根主帆桁（上桁與下桁，依 kaguya-shachuan-01m / Ship_Masts：沿 +X 建件，pivot 在桅軸 y=2, z=2）──
    #   注意：+X 為前端（fore/throat/tack），-X 為後端（aft/peak/clew），pivot=(2+aft_len+0.5, 2.5, 2.5)，
    #   rotate=(0, -angle_deg, 0)（上桁 -15°/-16° -> rotate_y=+15°/+16° 將 -X 尾峰抬高）；meta yard=course, rotate_z_deg=0
    yards_out = {}
    yard_frames = {}
    for yk, yv in ms['yards'].items():
        mk = yv['on']
        sp = ms[mk]
        L_cells = int(yv['len'])
        aft_len = int(yv['aft_len'])
        fore_len = int(yv['fore_len'])
        assert aft_len + fore_len == L_cells
        xpiv = 2 + aft_len
        yc_loc, zc_loc = 2, 2
        yvox = {}
        # 桁身核心 (y=2, z=2) 貫穿 2..2+L_cells（嚴守 Ship_Battens 桿心在格心）；中段 1/2 加粗呈圓潤十字截面，兩端收尖
        mid0 = 2 + aft_len - L_cells // 3
        mid1 = 2 + aft_len + L_cells // 4
        for x in range(2, 2 + L_cells + 1):
            col = TRIM if x in (2, xpiv, 2 + L_cells) else FIR
            yvox[(x, yc_loc, zc_loc)] = col
            if mid0 <= x <= mid1:
                for dy, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yvox[(x, yc_loc + dy, zc_loc + dz)] = TRIM if x == xpiv else FIR
        st = check_struct_stats(set(yvox), yc=yc_loc)
        assert st['components_6'] == 1 and st['cavities'] == 0 and st['mirror_diff'] == 0
        sub_name = yk.replace('gaff', 'upper').replace('boom', 'lower').replace('_', '-')
        p_y = os.path.join(out_dir, f'yard_{sub_name}.vox.txt')
        with open(p_y, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 福建趕繒船 步驟 7：{yk} 帆桁（沿 +X，中心 y=2, z=2，0 轉角基準件）x,y,z,color\n')
            for k in sorted(yvox):
                f.write(f'{k[0]},{k[1]},{k[2]},{yvox[k]}\n')

        mx = round(mast_x(sp, float(yv['z'])), 3)
        ry = round(-float(yv['angle_deg']), 3)
        anchors = {
            'pivot': [xpiv, yc_loc, zc_loc],
            'sling': [xpiv, yc_loc, zc_loc],
            'aft': [2, yc_loc, zc_loc],
            'fore': [2 + L_cells, yc_loc, zc_loc],
            'arm-P': [2, yc_loc, zc_loc],
            'arm-S': [2 + L_cells, yc_loc, zc_loc],
            'earing-P': [2, yc_loc, zc_loc],
            'earing-S': [2 + L_cells, yc_loc, zc_loc],
        }
        j_idx = 1
        for jx in range(6, 2 + L_cells - 3, 8):
            anchors[f'jackstay-{j_idx}'] = [jx, yc_loc, zc_loc + (1 if mid0 <= jx <= mid1 else 0)]
            j_idx += 1

        meta = {
            'kind': 'yard',
            'yard': 'course',  # Ship_Masts & Ship_Battens：硬骨帆上下桁皆標 course（禁標 boom）
            'mast': mk,
            'sail': f'{mk}-junk',
            'pivot_anchor': 'pivot',
            'turn_axis': 'z',
            'rotate_z_deg': 0,
            'diameter_in': 8 if mk == 'main' else 6,
            'length_ft': round(L_cells * 0.3281, 2),
        }
        yards_out[sub_name] = {
            'work': f'kotoko-ganzengchuan-01m-yard-{sub_name}',
            'host_mast': f'kotoko-ganzengchuan-01m-mast-{mk}',
            'model_name': f'yard-{sub_name}',
            'size': f'{L_cells + 5},5,5',
            'vox_file': f'masks/masts/yard_{sub_name}.vox.txt',
            'cells': len(yvox),
            'at': [mx, YC + 0.5, float(yv['z'])],
            'pivot': [xpiv + 0.5, yc_loc + 0.5, zc_loc + 0.5],
            'rotate': [0, ry, 0],
            'scale': [1, 1, 1],
            'anchors': anchors,
            'meta': meta,
            'sha256': sha256_file(p_y),
        }
        # 記錄旋轉後的耳點世界座標（與 sail 角點對齊計算竹篾列位置；y 中心 96.5）
        rad = math.radians(ry)
        ca, sa = math.cos(rad), math.sin(rad)
        yard_frames[yk] = {
            'fore': (mx + fore_len * ca, YC + 0.5, float(yv['z']) - fore_len * sa),
            'aft': (mx - aft_len * ca, YC + 0.5, float(yv['z']) + aft_len * sa),
        }

    # ── 3. 每桅 1 件共用竹篾元件 ＋ 16 根實體竹篾模型（Ship_Battens §3 + roach 弧線）──
    batten_templates = {}
    batten_models = []
    roach_str = '0.05,0.16'
    r0, r1 = 0.05, 0.16
    for mk in ('fore', 'main'):
        sp = ms[mk]
        slope_x = math.tan(math.radians(sp['rake_deg']))
        N = int(ms['battens'][mk])
        c0 = yard_frames[f'{mk}_gaff']['fore']   # throat (+X)
        c1 = yard_frames[f'{mk}_gaff']['aft']    # peak   (-X)
        c2 = yard_frames[f'{mk}_boom']['aft']    # clew   (-X)
        c3 = yard_frames[f'{mk}_boom']['fore']   # tack   (+X)

        rows = []
        for m_idx in range(1, N + 1):
            v = m_idx / (N + 1)
            bulge = math.sin(math.pi * (v ** 0.85))
            uL, uR = -bulge * r0, 1.0 + bulge * r1
            p_fore = lerp(lerp(c0, c1, uL), lerp(c3, c2, uL), v)
            p_aft = lerp(lerp(c0, c1, uR), lerp(c3, c2, uR), v)
            dx, dz = p_fore[0] - p_aft[0], p_fore[2] - p_aft[2]
            s_int = ((sp['x'] - p_aft[0]) + slope_x * (p_aft[2] - sp['heel_z'])) / (dx - slope_x * dz)
            piv_x = p_aft[0] + s_int * dx
            piv_z = p_aft[2] + s_int * dz
            d_aft = math.hypot(piv_x - p_aft[0], piv_z - p_aft[2])
            d_fore = math.hypot(p_fore[0] - piv_x, p_fore[2] - piv_z)
            ry_bat = -math.degrees(math.atan2(dz, dx))
            rows.append((m_idx, piv_x, piv_z, ry_bat, d_aft, d_fore, p_fore, p_aft))

        aft_base = int(math.ceil(max(r[4] for r in rows) + 2.5))
        fore_base = int(math.ceil(max(r[5] for r in rows) + 2.5))
        if probe == 'batten_short=-6' and mk == 'fore':
            aft_base -= 6
            fore_base -= 6
        span_base = aft_base + fore_base
        bvox = {(x, 2, 2): (TRIM if (x - 2) % 12 == 0 or x in (2, 2 + span_base) else WOOD)
                for x in range(2, 2 + span_base + 1)}
        b_path = os.path.join(out_dir, f'batten_{mk}.vox.txt')
        if not probe:
            with open(b_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(f'# 福建趕繒船 步驟 7：{mk} 共用竹篾桿（中心 y=2, z=2，pivot x={2+aft_base}）x,y,z,color\n')
                for k in sorted(bvox):
                    f.write(f'{k[0]},{k[1]},{k[2]},{bvox[k]}\n')
            batten_templates[mk] = {
                'work': f'kotoko-ganzengchuan-01m-batten-{mk}',
                'size': f'{span_base + 5},5,5',
                'vox_file': f'masks/masts/batten_{mk}.vox.txt',
                'cells': len(bvox),
                'aft_base': aft_base,
                'fore_base': fore_base,
                'pivot': [2 + aft_base + 0.5, 2.5, 2.5],
                'anchors': {'pivot': [2 + aft_base, 2, 2], 'arm-P': [2, 2, 2], 'arm-S': [2 + span_base, 2, 2]},
                'sha256': sha256_file(b_path),
            }

        for m_idx, piv_x, piv_z, ry_bat, da, df, pf, pa in rows:
            s_need = max((da + 2.0) / aft_base, (df + 2.0) / fore_base) if not probe else 1.0
            sx = round(s_need, 4)
            ov_a = round(aft_base * sx - da, 3)
            ov_f = round(fore_base * sx - df, 3)
            if not probe:
                assert ov_a >= 1.5 and ov_f >= 1.5, f'{mk} batten {m_idx} 伸出不足：{ov_a}, {ov_f}'
            batten_models.append({
                'mast': mk,
                'batten': m_idx,
                'host_mast': f'kotoko-ganzengchuan-01m-mast-{mk}',
                'source_work': f'kotoko-ganzengchuan-01m-batten-{mk}',
                'model_name': f'batten-{m_idx:02d}',
                'at': [round(piv_x, 3), YC + 0.5, round(piv_z, 3)],
                'pivot': [2 + aft_base + 0.5, 2.5, 2.5],
                'rotate': [0, round(ry_bat, 3), 0],
                'scale': [sx, 1, 1],
                'overhang': [ov_a, ov_f],
                'row_fore': [round(q, 3) for q in pf],
                'row_aft': [round(q, 3) for q in pa],
                'meta': {
                    'kind': 'yard',
                    'yard': 'batten',
                    'batten': m_idx,
                    'sail': f'{mk}-junk',
                    'mast': mk,
                    'pivot_anchor': 'pivot',
                    'turn_axis': 'z',
                    'rotate_z_deg': 0,
                    'diameter_in': 4.0,
                    'length_ft': round(span_base * sx * 0.3281, 2),
                    'material': 'bamboo',
                },
            })

    if probe == 'batten_short=-6':
        min_ov = min(min(b['overhang']) for b in batten_models if b['mast'] == 'fore')
        print(json.dumps({'probe': probe, 'fore_min_overhang': min_ov, 'passes_1_5': min_ov >= 1.5}, ensure_ascii=False))
        return

    verify = {
        'masts': masts_meta,
        'yards': yards_out,
        'batten_templates': batten_templates,
        'batten_count': len(batten_models),
        'min_overhang_cells': min(min(b['overhang']) for b in batten_models),
        'roach': roach_str,
    }
    with open(os.path.join(design, 'masts_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'masts': masts_meta, 'yards': yards_out, 'batten_templates': batten_templates, 'battens': batten_models}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(verify, f, ensure_ascii=False, indent=2)

    print(json.dumps(verify, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
