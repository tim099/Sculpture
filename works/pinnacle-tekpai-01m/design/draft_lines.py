# 台灣帆竹筏 Tek-pái 新圖紙 01＋體素清單產生器（TASK-1312 步驟 3–4）
#   功能：
#     1. 產出決定性圖紙 `sheet01_lines_v1.png`（俯視平鋪竹排圖、側視雙翹線圖、舯/艏/艉橫剖面、圖例與規格表）
#     2. 產出 `masks/hull_voxels.vox.txt`（給 sculpture op=stampvox 落子）
#     3. 執行結構與鏡像及反向對照檢查（probe=rocker_fwd_z=+3），寫出 `verify_lines.json`
#   用法：python -I -X utf8 draft_lines.py
import hashlib
import json
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def rgb(i):
    return ((int(i) >> 5 & 7) * 255 // 7, (int(i) >> 2 & 7) * 255 // 7, (int(i) & 3) * 255 // 3)


def analyze(hull, G):
    occ = G > 0
    xs_occ = np.where(occ.any(axis=(1, 2)))[0]
    ys_occ = np.where(occ.any(axis=(0, 2)))[0]
    zs_occ = np.where(occ.any(axis=(0, 1)))[0]
    _, comp_count = ndimage.label(occ)  # 預設 6-鄰接
    filled = ndimage.binary_fill_holes(occ)
    cavities = int((filled & ~occ).sum())

    # 鏡像差：y <-> (SY - 1 - y)
    mir = G[:, ::-1, :]
    mirror_diff = int((G != mir).sum())

    # 水線處長度與寬度（z = wl - 1）
    wl_layer = occ[:, :, max(hull.wl - 1, 0)]
    xs_wl = np.where(wl_layer.any(axis=1))[0]
    ys_wl = np.where(wl_layer.any(axis=0))[0]

    return {
        'voxels_total': int(occ.sum()),
        'loa_cells': int(xs_occ.max() - xs_occ.min() + 1) if len(xs_occ) else 0,
        'loa_x_range': [int(xs_occ.min()), int(xs_occ.max())],
        'beam_cells': int(ys_occ.max() - ys_occ.min() + 1) if len(ys_occ) else 0,
        'beam_y_range': [int(ys_occ.min()), int(ys_occ.max())],
        'height_cells': int(zs_occ.max() - zs_occ.min() + 1) if len(zs_occ) else 0,
        'z_range': [int(zs_occ.min()), int(zs_occ.max())],
        'lwl_cells': int(xs_wl.max() - xs_wl.min() + 1) if len(xs_wl) else 0,
        'bwl_cells': int(ys_wl.max() - ys_wl.min() + 1) if len(ys_wl) else 0,
        'bow_tip_top_z': int(np.where(occ[int(hull.xf), hull.YC, :])[0].max()),
        'stern_tip_top_z': int(np.where(occ[int(hull.xa), hull.YC, :])[0].max()),
        'components_6conn': int(comp_count),
        'closed_cavities': cavities,
        'mirror_diff_cells': mirror_diff,
        'color_counts': {str(int(c)): int((G == c).sum()) for c in np.unique(G[occ])},
    }


def write_vox_list(G, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    xs, ys, zs = np.nonzero(G)
    lines_out = [
        '# Tek-pái hull voxels (x,y,z,color) — deterministic output from draft_lines.py'
    ]
    for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
        lines_out.append(f'{x},{y},{z},{int(G[x, y, z])}')
    content = '\n'.join(lines_out) + '\n'
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def draw_sheet(plan, hull, G, R, probe_res, out_png):
    W, H = 1600, 980
    img = Image.new('RGB', (W, H), (247, 243, 234))
    d = ImageDraw.Draw(img)
    f_title = font(22)
    f_sub = font(14)
    f_mono = font(12)

    d.text((32, 20), f"台灣帆竹筏 Tek-pái 新圖紙 01：竹排線形與雙翹結構 ({plan['task']})", fill=(35, 30, 26), font=f_title)
    d.text((32, 50), f"比例：0.1 m/格 | LOA={R['loa_cells']*0.1:.1f}m | Beam={R['beam_cells']*0.1:.1f}m | 吃水={hull.wl*0.1:.2f}m | 格數={R['voxels_total']} | 連通元件={R['components_6conn']} | 空腔={R['closed_cavities']} | 鏡像差={R['mirror_diff_cells']}", fill=(70, 62, 52), font=f_sub)

    # 1. 側視剖面與輪廓投影 (Top-left box)
    scale = 9
    px0, py0 = 60, 320  # (x=0, z=0) 底基準點
    d.text((px0, 92), '側視（Profile：最大包絡＋中線 z=yc 切面；紅線＝水線 z=3 / 0.30 m）', fill=(40, 40, 40), font=f_sub)
    # 格線與軸線
    for gx in range(0, 141, 10):
        xx = px0 + gx * scale
        d.line([(xx, py0 - 30 * scale), (xx, py0)], fill=(228, 222, 210), width=1)
        d.text((xx - 8, py0 + 4), str(gx), fill=(110, 100, 90), font=f_mono)
    for gz in range(0, 21, 5):
        yy = py0 - gz * scale
        d.line([(px0, yy), (px0 + 140 * scale, yy)], fill=(228, 222, 210), width=1)
        d.text((px0 - 26, yy - 7), f'z{gz}', fill=(110, 100, 90), font=f_mono)

    # 側視投影（由外而內：先畫外廓最高可見色，中線重繪橫擔與藤索點）
    for x in range(hull.SX):
        for z in range(hull.SZ):
            col_slice = G[x, :, z]
            nz = col_slice[col_slice > 0]
            if len(nz):
                # 取最外側（或中線）著色展示外護舷 + 翹首
                c_val = int(nz[-1])
                rx0 = px0 + x * scale
                ry0 = py0 - (z + 1) * scale
                d.rectangle([rx0, ry0, rx0 + scale - 1, ry0 + scale - 1], fill=rgb(c_val))

    # 畫出規劃木桶艙（虛線外框 x=50..74, z=4..8）與桅位（x=82）作為設計參考
    tub = plan['deck_and_tub']['cargo_tub']
    d.rectangle(
        [px0 + tub['x0'] * scale, py0 - (tub['z_top'] + 1) * scale,
         px0 + (tub['x1'] + 1) * scale, py0 - tub['z_base'] * scale],
        outline=(55, 95, 145), width=2,
    )
    mx = plan['rig_plan']['mast_main']['x']
    d.line([(px0 + (mx + 0.5) * scale, py0 - 20 * scale), (px0 + (mx + 0.5) * scale, py0 - 2 * scale)], fill=(150, 60, 45), width=2)
    # 水線 DWL z=3
    d.line([(px0, py0 - hull.wl * scale), (px0 + 140 * scale, py0 - hull.wl * scale)], fill=(205, 55, 50), width=2)

    # 2. 俯視圖（Plan view: x horizontal, y vertical centered）
    top_x0, top_y0 = 60, 410
    d.text((top_x0, top_y0 - 28), '俯視（Plan View：7 主排刺竹＋護舷竹＋9 硬木橫擔＋黃藤編紮；藍框＝規劃防潮木桶艙）', fill=(40, 40, 40), font=f_sub)
    # 顯示 y = 30..70（共 41 格）以清晰放大竹排細節
    y_min, y_max = 30, 70
    y_scale = 8
    # 背景格網
    for gx in range(0, 141, 10):
        xx = top_x0 + gx * scale
        d.line([(xx, top_y0), (xx, top_y0 + (y_max - y_min + 1) * y_scale)], fill=(228, 222, 210), width=1)
    d.line([(top_x0, top_y0 + (hull.YC - y_min + 0.5) * y_scale),
            (top_x0 + 140 * scale, top_y0 + (hull.YC - y_min + 0.5) * y_scale)], fill=(180, 195, 220), width=1)

    for x in range(hull.SX):
        for y in range(y_min, y_max + 1):
            col_z = G[x, y, :]
            zs = np.where(col_z > 0)[0]
            if len(zs):
                top_c = int(col_z[zs.max()])
                rx0 = top_x0 + x * scale
                ry0 = top_y0 + (y - y_min) * y_scale
                d.rectangle([rx0, ry0, rx0 + scale - 1, ry0 + y_scale - 1], fill=rgb(top_c))

    # 規劃木桶艙俯視外框
    d.rectangle(
        [top_x0 + tub['x0'] * scale, top_y0 + (tub['y0'] - y_min) * y_scale,
         top_x0 + (tub['x1'] + 1) * scale, top_y0 + (tub['y1'] - y_min + 1) * y_scale],
        outline=(55, 95, 145), width=2,
    )

    # 3. 橫剖面（Cross sections at Stern x=22, Midship x=60, Bow x=112）
    sec_y_base = 890
    stations = [(22, '艉翹斷面 x=22', 80), (60, '舯平鋪斷面 x=60（雙護舷＋木桶艙框）', 500), (112, '艏翹斷面 x=112', 940)]
    sec_s = 8
    for sx, label, base_px in stations:
        d.text((base_px, sec_y_base - 155), label, fill=(40, 40, 40), font=f_sub)
        cy_px = base_px + 150
        # 水線
        d.line([(cy_px - 20 * sec_s, sec_y_base - hull.wl * sec_s),
                (cy_px + 20 * sec_s, sec_y_base - hull.wl * sec_s)], fill=(205, 55, 50), width=2)
        for y in range(hull.SY):
            dy = y - hull.YC
            if abs(dy) > 18:
                continue
            for z in range(hull.SZ):
                c = int(G[sx, y, z])
                if c:
                    rx0 = cy_px + dy * sec_s
                    ry0 = sec_y_base - (z + 1) * sec_s
                    d.rectangle([rx0, ry0, rx0 + sec_s - 1, ry0 + sec_s - 1], fill=rgb(c))

    # 4. 色票與驗證讀數（右側欄）
    lx = 1355
    d.text((lx, 410), '材料與色票圖例', fill=(35, 30, 26), font=f_sub)
    legend = [
        ('bamboo_dry', '曝曬主竹排 (177)'),
        ('bamboo_wet', '水下濕竹 (141)'),
        ('crossbar',   '硬木橫擔 (104)'),
        ('lashing',    '黃藤編紮 (136)'),
    ]
    for idx, (k, text_lbl) in enumerate(legend):
        ci = hull.colors[k]
        yy = 440 + idx * 30
        d.rectangle([lx, yy, lx + 20, yy + 20], fill=rgb(ci), outline=(60, 60, 60))
        d.text((lx + 28, yy + 2), text_lbl, fill=(50, 45, 40), font=f_mono)

    d.text((lx, 585), '驗證摘要', fill=(35, 30, 26), font=f_sub)
    notes = [
        f"x_range: {R['loa_x_range']}",
        f"y_range: {R['beam_y_range']}",
        f"z_range: {R['z_range']}",
        f"lwl: {R['lwl_cells']*0.1:.1f} m",
        f"bwl: {R['bwl_cells']*0.1:.1f} m",
        f"6-conn: {R['components_6conn']}",
        f"cavities: {R['closed_cavities']}",
        f"mirror_diff: {R['mirror_diff_cells']}",
        f"neg_ctrl (+3 bow): {probe_res['bow_delta_z']}",
    ]
    for idx, ln in enumerate(notes):
        d.text((lx, 615 + idx * 22), ln, fill=(50, 45, 40), font=f_mono)

    img.save(out_png, optimize=False)


def main():
    plan = HL.load_plan(HERE)
    hull = HL.TekpaiHull(plan)
    G = hull.build_voxels()
    R = analyze(hull, G)

    # 反向對照探針：故意把 rocker_fwd_z 加上 +3 格，驗出艏尖頂部剛好上升 +3 格
    hull_probe = HL.TekpaiHull(plan, probe={'rocker_fwd_z': 3})
    Gp = hull_probe.build_voxels()
    Rp = analyze(hull_probe, Gp)
    probe_res = {
        'probe_param': 'rocker_fwd_z=+3',
        'base_bow_tip_top_z': R['bow_tip_top_z'],
        'probe_bow_tip_top_z': Rp['bow_tip_top_z'],
        'bow_delta_z': Rp['bow_tip_top_z'] - R['bow_tip_top_z'],
    }
    assert probe_res['bow_delta_z'] == 3, f"反向對照失敗：{probe_res}"

    vox_path = os.path.join(HERE, 'masks', 'hull_voxels.vox.txt')
    vox_sha = write_vox_list(G, vox_path)

    sheet_path = os.path.join(HERE, 'sheet01_lines_v1.png')
    draw_sheet(plan, hull, G, R, probe_res, sheet_path)
    with open(sheet_path, 'rb') as f:
        sheet_sha = hashlib.sha256(f.read()).hexdigest()

    verify = {
        'stage': 'step03_04_hull_lines',
        'work': 'pinnacle-tekpai-01m',
        'readings': R,
        'reverse_control': probe_res,
        'artifacts': {
            'hull_voxels_sha256': vox_sha,
            'sheet01_sha256': sheet_sha,
        },
    }
    verify_path = os.path.join(HERE, 'verify_lines.json')
    with open(verify_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(verify, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')

    print(json.dumps(verify, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
