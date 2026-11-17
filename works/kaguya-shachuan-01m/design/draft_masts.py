# 沙船 步驟 7（TASK-1313）：三桅（頭桅・大桅・尾桅）與 6 根中式硬篷帆桁（gaff＋boom）
#   出處：kaguya-guineaman-01m/design/draft_masts.py ＋ gura-tridente-01m/design/draft_masts.py
#   用法：python -I -X utf8 draft_masts.py <design 資料夾>
import sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import build as hull_build
from draft_decks import load_carved_hull

sys.stdout.reconfigure(encoding='utf-8')


def main():
    design = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else HERE
    plan = HL.load_plan(design)
    L, _, S, x0, ylo = hull_build(plan, None)
    YC = L.YC
    H_col = load_carved_hull(design, x0, ylo, S.shape)

    # 讀入所有甲板占用格（防重疊）
    occ = H_col > 0
    for dk in plan['decks_build']['spans']:
        p = os.path.join(design, 'masks', 'decks', f'{dk}.vox.txt')
        if os.path.exists(p):
            for x, y, z, _ in np.loadtxt(p, delimiter=',', comments='#', dtype=int, ndmin=2):
                occ[x - x0, y - ylo, z] = True

    os.makedirs(os.path.join(design, 'masks', 'masts'), exist_ok=True)
    ms = plan['masts']
    masts_meta = {}
    SX, SY, SZ = plan['space']['assembly']

    for mk in ('fore', 'main', 'mizzen'):
        m = ms[mk]
        ang = math.radians(m['rake_deg'])
        z_start = int(m['heel_z'])
        z_end = int(round(z_start + m['len'] * math.cos(ang)))
        r0, r1 = m['r']
        pts = []
        ov_skip = 0
        for z in range(z_start, z_end + 1):
            t = (z - z_start) / max(z_end - z_start, 1)
            r = r0 + (r1 - r0) * t
            xc = m['x'] + (z - z_start) * math.tan(ang)
            ix0, ix1 = int(math.floor(xc - r - 1)), int(math.ceil(xc + r + 1))
            iy0, iy1 = int(math.floor(YC - r - 1)), int(math.ceil(YC + r + 1))
            for x in range(ix0, ix1 + 1):
                for y in range(iy0, iy1 + 1):
                    if (x - xc) ** 2 + (y - YC) ** 2 <= r * r:
                        if 0 <= x - x0 < occ.shape[0] and 0 <= y - ylo < occ.shape[1] and 0 <= z < occ.shape[2]:
                            if occ[x - x0, y - ylo, z]:
                                ov_skip += 1
                                continue
                        pts.append((x, y, z, 136 if z > z_end - 8 else 141))
        m_path = os.path.join(design, 'masks', 'masts', f'mast_{mk}.vox.txt')
        with open(m_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 沙船 {mk} 桅（步驟 7）x,y,z,color\n')
            for x, y, z, c in pts:
                f.write(f'{x},{y},{z},{c}\n')

        # 記錄桅頂、桅腳、與各高度軸心供帆桁 pivot 對齊
        top_x = m['x'] + (z_end - z_start) * math.tan(ang)
        masts_meta[mk] = {
            'cells': len(pts),
            'overlap_skipped': ov_skip,
            'x0': m['x'],
            'z_start': z_start,
            'z_end': z_end,
            'rake_deg': m['rake_deg'],
            'anchors': {
                'head': [int(round(top_x)), YC, z_end],
                'heel': [int(round(m['x'])), YC, z_start],
            },
        }

    # ── 帆桁（6 根：fore/main/mizzen 各 1 gaff ＋ 1 boom）──
    # 座標慣例（對齊 gura-tridente-01m-yard-mizzen-gaff/boom）：
    #   在帆桁子作品裡沿 X 軸放、+X 為前端（fore）、-X 為後端（peak/aft）；
    #   pivot 設在離前端 25% 處（中式平衡硬篷約 1/4 前伸、3/4 後伸），y 放在桅中線前／旁（y=1，pivot y=1.5 或 2.5）；
    #   gaff 後高前低（angle_deg < 0 ⇒ x 越往 -X 端 z 越高！）
    yards_meta = {}
    for yk, yv in ms['yards'].items():
        mk = yv['on']
        m = ms[mk]
        ang_m = math.radians(m['rake_deg'])
        mast_x_at_z = m['x'] + (yv['z'] - m['heel_z']) * math.tan(ang_m)

        L_cells = int(yv['len'])
        fwd_len = int(round(L_cells * 0.25))
        aft_len = L_cells - fwd_len
        tilt = math.radians(yv['angle_deg'])  # 負值（如 -14°）：-X 端升高、+X 端微降

        # 局部框：x ∈ [0 .. L_cells + 4]，pivot 在 x_piv = aft_len + 2（這樣 aft 端在 x=2, fore 端在 x=aft_len+2+fwd_len）
        x_piv = aft_len + 2
        y_piv = 2
        # z 基準：令最低點在 z >= 2
        dz_aft = int(round(-aft_len * math.tan(tilt)))   # tilt < 0 ⇒ dz_aft > 0
        dz_fwd = int(round(fwd_len * math.tan(tilt)))    # tilt < 0 ⇒ dz_fwd < 0
        z_piv = max(2, 2 - min(0, dz_fwd))

        vox = []
        for s in range(-aft_len, fwd_len + 1):
            lx = x_piv + s
            lz = int(round(z_piv + s * math.tan(tilt)))
            # 1~2 格粗竹木桁（中段略粗 y=1..2，兩端細 y=1）
            ys_bar = (1, 2) if abs(s) < L_cells * 0.35 else (1,)
            for ly in ys_bar:
                vox.append((lx, ly, lz, 136 if yv['kind'] == 'gaff' else 141))
                if abs(s) < L_cells * 0.25 and yv['kind'] == 'gaff':
                    vox.append((lx, ly, lz + 1, 136))

        z_box = max(z for _, _, z, _ in vox) + 4
        y_box = 5
        x_box = L_cells + 6

        yp_path = os.path.join(design, 'masks', 'masts', f'yard_{yk}.vox.txt')
        with open(yp_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 沙船 帆桁 {yk}（局部座標，pivot=({x_piv},{y_piv},{z_piv})）x,y,z,color\n')
            for lx, ly, lz, c in sorted(set(vox)):
                f.write(f'{lx},{ly},{lz},{c}\n')

        # 局部固定點
        z_aft = int(round(z_piv - aft_len * math.tan(tilt)))
        z_fwd = int(round(z_piv + fwd_len * math.tan(tilt)))
        sail_name = f'{mk}-junk'
        yards_meta[yk] = {
            'on': mk,
            'kind': yv['kind'],
            'sail': sail_name,
            'len_cells': L_cells,
            'length_ft': round(L_cells * 0.1 / 0.3048, 2),
            'diameter_in': 8.0 if mk == 'main' else 6.0,
            'box': [x_box, y_box, z_box],
            'pivot': [float(x_piv) + 0.5, float(y_piv) + 0.5, float(z_piv) + 0.5],
            'at': [round(mast_x_at_z, 2) + 0.5, float(YC) + 0.5, float(yv['z']) + 0.5],
            'anchors': {
                'pivot': [x_piv, y_piv, z_piv],
                'aft': [x_piv - aft_len, 1, z_aft],
                'fore': [x_piv + fwd_len, 1, z_fwd],
                'sling': [x_piv, 1, z_piv],
            },
            'cells': len(set(vox)),
        }

    out = {'masts': masts_meta, 'yards': yards_meta}
    with open(os.path.join(design, 'yards_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps({
        'masts': {k: v['cells'] for k, v in masts_meta.items()},
        'yards': {k: {'cells': v['cells'], 'at': v['at']} for k, v in yards_meta.items()},
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
