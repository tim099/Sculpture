# 炎羽號（kiara-phoenix-01m）新圖紙 01 線形圖（Phase 1: Line Plan & Hydrostatics）
# plan.json 的 lines 段 ⇒ 船殼曲面、線形圖、殼預覽格子、verify_lines.json
# 用法：python -I -X utf8 draft_lines.py <design 資料夾>

import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

YC = 90
FONT = r"C:\Windows\Fonts\msjh.ttc"


class Hull:
    def __init__(s, plan):
        L = plan['lines']
        s.L = L
        k, sp, st, sh, ms, tr = L['keel'], L['sternpost'], L['stem'], L['sheer'], L['midship'], L['transom']
        s.half = k['half']; s.rab = k['rabbet_z']; s.kx0 = k['x_aft']; s.kx1 = k['x_fwd']
        s.sp_x0, s.sp_rake, s.sp_h, s.sp_sid = sp['x_at_keel'], sp['rake'], sp['rake_height'], sp['siding']
        s.st_x0, s.st_rx, s.st_rz, s.st_sid = st['x_at_keel'], st['rx'], st['rz'], st['siding']
        s.sh = sh
        s.dwl = L['dwl']
        s.xm = ms['x']; s.B = ms['half_beam']; s.zmb = ms['z_max_beam']
        s.t = math.tan(math.radians(ms['deadrise_deg'])); s.R = ms['bilge_radius']
        s.th, s.thh = ms['tumblehome'], ms['tumblehome_height']
        s.yc = s.B - s.R
        s.zc = s.rab + (s.yc - s.half) * s.t + s.R * math.sqrt(1 + s.t * s.t)
        s.z_floor_tan = s.zc - s.R / math.sqrt(1 + s.t * s.t)
        s.trz, s.trk, s.trV = tr['z'], tr['rake'], tr['virtual_extension']
        s.fu = L['fullness']
        s.up = L.get('upper')

    def hb_mid(s, z):
        z = np.asarray(z, float)
        out = np.full(z.shape, np.nan)
        out = np.where(z < s.rab, s.half, out)
        m = (z >= s.rab) & (z <= s.z_floor_tan)
        out = np.where(m, s.half + (z - s.rab) / s.t, out)
        m = (z > s.z_floor_tan) & (z <= s.zc)
        out = np.where(m, s.yc + np.sqrt(np.clip(s.R * s.R - (s.zc - z) ** 2, 0, None)), out)
        m = (z > s.zc) & (z <= s.zmb)
        out = np.where(m, s.B, out)
        m = z > s.zmb
        out = np.where(m, s.B - s.th * ((z - s.zmb) / s.thh) ** 2, out)
        return out

    def sheer(s, x):
        x = np.asarray(x, float); h = s.sh
        aft = h['z_low'] + (h['z_aft'] - h['z_low']) * ((h['x_low'] - x) / (h['x_low'] - h['x_aft'])) ** 2
        fwd = h['z_low'] + (h['z_fwd'] - h['z_low']) * ((x - h['x_low']) / (h['x_fwd'] - h['x_low'])) ** 2
        return np.where(x <= h['x_low'], aft, fwd)

    def deck_side(s, x):
        x = np.asarray(x, float); z = s.sheer(x)
        if not s.up: return z
        q = s.up['quarterdeck']
        return np.where(x <= q['x_break'], z + q['rise'], z)

    def top(s, x):
        x = np.asarray(x, float)
        if not s.up: return s.sheer(x)
        q = s.up['quarterdeck']
        hi = q['rise'] + q['bulwark'] - s.up['bulwark']
        tt = np.clip((x - q['x_break']) / q['drift'], 0, 1)
        return s.sheer(x) + s.up['bulwark'] + hi * (1 - tt * tt * (3 - 2 * tt))

    def stern_top(s):
        x = float(s.transom_face(s.sh['z_aft']))
        if not s.up: return x, float(s.sh['z_aft'])
        for _ in range(60): x = float(s.transom_face(float(s.top(x))))
        return x, float(s.top(x))

    def stem_face(s, z):
        z = np.asarray(z, float)
        q = np.clip((s.st_rz - z) / s.st_rz, 0, 1)
        return s.st_x0 + s.st_rx * np.sqrt(1 - q * q)

    def post_face(s, z):
        return s.sp_x0 - s.sp_rake * np.asarray(z, float) / s.sp_h

    def transom_face(s, z):
        return s.post_face(s.trz) - (np.asarray(z, float) - s.trz) * s.trk

    def aft_limit(s, z):
        z = np.asarray(z, float)
        return np.where(z >= s.trz, s.transom_face(z), s.post_face(z))

    def hb(s, x, z):
        x = np.asarray(x, float); z = np.asarray(z, float)
        x_bc, z_bc = np.broadcast_arrays(x, z)
        out = np.full(x_bc.shape, np.nan)
        hbm = s.hb_mid(z_bc)
        top_z = s.top(x_bc)
        valid = (z_bc >= 0) & (z_bc <= top_z)
        if not np.any(valid): return out

        # 前部
        fore = valid & (x_bc >= s.xm)
        if np.any(fore):
            zf = z_bc[fore]
            xf = x_bc[fore]
            x_fwd_end = s.stem_face(zf)
            L_fwd = np.maximum(x_fwd_end - s.xm, 1e-4)
            xi = np.clip((xf - s.xm) / L_fwd, 0.0, 1.0)
            u = np.clip(zf / s.sh['z_fwd'], 0.0, 1.0)
            fu = s.fu['fore']
            a = fu['a_bottom'] + (fu['a_top'] - fu['a_bottom']) * u
            b = fu['b_bottom'] + (fu['b_top'] - fu['b_bottom']) * u
            f = np.clip(1.0 - xi ** a, 0.0, 1.0) ** b
            hb_val = hbm[fore] * f
            hb_val = np.maximum(hb_val, s.half)
            hb_val = np.where(xf > x_fwd_end, np.nan, hb_val)
            out[fore] = hb_val

        # 後部
        aft = valid & (x_bc < s.xm)
        if np.any(aft):
            za = z_bc[aft]
            xa = x_bc[aft]
            x_aft_end = s.aft_limit(za)
            x_v_end = x_aft_end - s.trV * np.clip((za - s.trz) / (s.sh['z_aft'] - s.trz), 0, 1)
            L_aft = np.maximum(s.xm - x_v_end, 1e-4)
            xi = np.clip((s.xm - xa) / L_aft, 0.0, 1.0)
            u = np.clip(za / s.sh['z_aft'], 0.0, 1.0)
            fu = s.fu['aft']
            a = fu['a_bottom'] + (fu['a_top'] - fu['a_bottom']) * u
            b = fu['b_bottom'] + (fu['b_top'] - fu['b_bottom']) * u
            f = np.clip(1.0 - xi ** a, 0.0, 1.0) ** b
            hb_val = hbm[aft] * f
            hb_val = np.maximum(hb_val, s.half)
            hb_val = np.where(xa < x_aft_end, np.nan, hb_val)
            out[aft] = hb_val

        return out

    def contains(s, x, y, z):
        """測試點 (x, y, z) 是否在船殼內"""
        dy = np.abs(y - YC)
        h = s.hb(x, z)
        return (~np.isnan(h)) & (dy <= h)


def calculate_hydrostatics(hull):
    """計算水線長、型寬、排水量、方塊係數 Cb、稜形係數 Cp、中剖面係數 Cm、水線面係數 Cwp 與浮心"""
    dwl = hull.dwl
    xs = np.linspace(hull.sp_x0 - 5, hull.st_x0 + hull.st_rx + 5, 2000)
    hb_dwl = hull.hb(xs, dwl)
    valid_x = xs[~np.isnan(hb_dwl) & (hb_dwl > hull.half)]

    lwl = float(valid_x.max() - valid_x.min()) if len(valid_x) > 0 else 0.0
    bwl = float(np.nanmax(hb_dwl) * 2.0)
    draft = float(dwl)

    # 體積積分 (以 0.5 格步長採樣)
    x_steps = np.arange(hull.sp_x0 - 15, hull.st_x0 + hull.st_rx + 10, 0.5)
    z_steps = np.arange(0.25, dwl, 0.5)
    X, Z = np.meshgrid(x_steps, z_steps)
    HB = hull.hb(X, Z)
    HB_clean = np.where(np.isnan(HB), 0.0, np.maximum(HB - hull.half, 0.0))
    water_area_per_x = np.sum(HB_clean * 2.0 * 0.5, axis=0) # 沿 z 積分

    disp_voxels = float(np.sum(water_area_per_x) * 0.5)
    # 比例 0.1 m / voxel ⇒ 1 voxel = 0.001 m³
    volume_m3 = disp_voxels * (0.1 ** 3)
    disp_tonnes_sw = volume_m3 * 1.025 # 海水排水量

    # 浮心 LCB (從船尾量起)
    x_moment = np.sum(water_area_per_x * x_steps * 0.5)
    lcb_x = float(x_moment / np.sum(water_area_per_x * 0.5)) if np.sum(water_area_per_x) > 0 else hull.xm
    lcb_percent_fwd = float((lcb_x - valid_x.min()) / lwl * 100.0) if lwl > 0 else 50.0

    # 係數
    am = float(np.sum(np.nan_to_num(hull.hb_mid(z_steps)) * 2.0 * 0.5))
    awp = float(np.sum(np.nan_to_num(hb_dwl) * 2.0 * (xs[1] - xs[0])))
    cb = float(disp_voxels / (lwl * bwl * draft)) if (lwl * bwl * draft) > 0 else 0.0
    cm = float(am / (bwl * draft)) if (bwl * draft) > 0 else 0.0
    cp = float(disp_voxels / (am * lwl)) if (am * lwl) > 0 else 0.0
    cwp = float(awp / (lwl * bwl)) if (lwl * bwl) > 0 else 0.0

    return {
        "lwl_vox": round(lwl, 2), "lwl_m": round(lwl * 0.1, 2),
        "bwl_vox": round(bwl, 2), "bwl_m": round(bwl * 0.1, 2),
        "draft_vox": round(draft, 2), "draft_m": round(draft * 0.1, 2),
        "disp_volume_m3": round(volume_m3, 2),
        "displacement_tonnes_seawater": round(disp_tonnes_sw, 1),
        "Cb": round(cb, 3), "Cm": round(cm, 3), "Cp": round(cp, 3), "Cwp": round(cwp, 3),
        "L_over_B": round(lwl / bwl, 2), "B_over_T": round(bwl / draft, 2),
        "lcb_x": round(lcb_x, 2), "lcb_percent": round(lcb_percent_fwd, 1)
    }


def generate_lines_blueprint(hull, out_png):
    """生成正式線形圖紙 PNG（含側視輪廓、俯視水線、正視站號肋骨圖與型值讀數標註）"""
    w, h = 2400, 1500
    im = Image.new("RGB", (w, h), "#0d1117")
    draw = ImageDraw.Draw(im)

    try:
        font_title = ImageFont.truetype(FONT, 36)
        font_sub = ImageFont.truetype(FONT, 20)
        font_body = ImageFont.truetype(FONT, 16)
    except:
        font_title = font_sub = font_body = ImageFont.load_default()

    # 圖框與標題
    draw.rectangle([30, 30, w - 30, h - 30], outline="#30363d", width=2)
    draw.rectangle([36, 36, w - 36, h - 36], outline="#238636", width=1)
    draw.text((60, 50), "炎羽號（L'Oiseau de Feu / Ignis Phoenix）—— 32 門砲鳳凰級巡防艦 線形圖", fill="#f0883e", font=font_title)
    draw.text((60, 95), "比例 0.1 m / voxel | 參考 Sané 1782 Hébé 級 & HMS Phoenix 1783 幾何線形 | 設計者: kiara (wake #58)", fill="#8b949e", font=font_sub)

    # 1. 側視圖 (Profile, y = 90)
    ox, oz = 100, 520
    scale = 3.2  # 1 voxel = 3.2 像素
    draw.text((ox, oz - 220), "【側視輪廓圖 (Sheer & Inboard Profile)】", fill="#58a6ff", font=font_sub)

    # 畫水線基準
    dwl_y = oz - hull.dwl * scale
    draw.line([(ox, dwl_y), (ox + 500 * scale, dwl_y)], fill="#1f6feb", width=1)
    draw.text((ox + 505 * scale, dwl_y - 8), "DWL (z=38)", fill="#1f6feb", font=font_body)

    # 龍骨、艏柱、艉柱、舷弧輪廓
    profile_pts = []
    # 龍骨底
    draw.line([(ox + hull.sp_x0 * scale, oz), (ox + hull.st_x0 * scale, oz)], fill="#f0883e", width=3)
    # 艉柱
    draw.line([(ox + hull.sp_x0 * scale, oz), (ox + (hull.sp_x0 - hull.sp_rake) * scale, oz - hull.sp_h * scale)], fill="#f0883e", width=2)
    # 艏柱
    zs = np.linspace(0, hull.st_rz, 80)
    st_xs = hull.stem_face(zs)
    st_pts = [(ox + x * scale, oz - z * scale) for x, z in zip(st_xs, zs)]
    for i in range(len(st_pts) - 1):
        draw.line([st_pts[i], st_pts[i+1]], fill="#f0883e", width=2)

    # 舷牆頂與舷弧線
    xs_curve = np.linspace(hull.sp_x0 - hull.sp_rake - 10, hull.st_x0 + hull.st_rx, 200)
    sheer_zs = hull.sheer(xs_curve)
    top_zs = hull.top(xs_curve)
    sheer_pts = [(ox + x * scale, oz - z * scale) for x, z in zip(xs_curve, sheer_zs)]
    top_pts = [(ox + x * scale, oz - z * scale) for x, z in zip(xs_curve, top_zs)]
    for i in range(len(sheer_pts) - 1):
        draw.line([sheer_pts[i], sheer_pts[i+1]], fill="#8b949e", width=1)
        draw.line([top_pts[i], top_pts[i+1]], fill="#e6edf3", width=2)

    # 2. 俯視半寬水線圖 (Waterlines, Plan View)
    py0 = 850
    draw.text((ox, py0 - 150), "【半寬水線面圖 (Half-Breadth Plan / Waterlines)】", fill="#58a6ff", font=font_sub)
    # 中線
    draw.line([(ox, py0), (ox + 500 * scale, py0)], fill="#8b949e", width=2)
    draw.text((ox + 505 * scale, py0 - 8), "Centerline (y=90)", fill="#8b949e", font=font_body)

    wl_colors = ["#388bfd", "#58a6ff", "#79c0ff", "#a5d6ff", "#f0883e", "#ffa657", "#ff7b72", "#d2a8ff"]
    for idx, wl in enumerate(hull.L['waterlines']):
        c = wl_colors[idx % len(wl_colors)]
        xs_wl = np.linspace(hull.sp_x0 - 20, hull.st_x0 + hull.st_rx + 10, 300)
        hbs = hull.hb(xs_wl, wl)
        valid = ~np.isnan(hbs) & (hbs > hull.half)
        if np.any(valid):
            pts = [(ox + x * scale, py0 - hb * scale) for x, hb in zip(xs_wl[valid], hbs[valid])]
            for i in range(len(pts) - 1):
                draw.line([pts[i], pts[i+1]], fill=c, width=1)
            draw.text((pts[0][0] - 40, pts[0][1] - 8), f"WL{wl}", fill=c, font=font_body)

    # 3. 站號剖面圖 (Body Plan / Stations)
    bx0 = 1950
    by0 = 550
    b_scale = 4.2
    draw.text((bx0 - 120, by0 - 250), "【型線橫剖面圖 (Body Plan)】", fill="#58a6ff", font=font_sub)
    # 中線
    draw.line([(bx0, by0 - 90 * b_scale), (bx0, by0 + 10)], fill="#8b949e", width=2)
    # 水線基準
    draw.line([(bx0 - 60 * b_scale, by0 - hull.dwl * b_scale), (bx0 + 60 * b_scale, by0 - hull.dwl * b_scale)], fill="#1f6feb", width=1)
    draw.text((bx0 + 62 * b_scale, by0 - hull.dwl * b_scale - 8), "DWL", fill="#1f6feb", font=font_body)

    stations = np.linspace(hull.kx0 + 10, hull.kx1 - 10, hull.L['stations'])
    for st_x in stations:
        zs_st = np.linspace(hull.rab, hull.top(st_x), 150)
        hbs_st = hull.hb(st_x, zs_st)
        valid = ~np.isnan(hbs_st)
        if np.any(valid):
            # 前半身畫右側，後半身畫左側
            side = 1 if st_x >= hull.xm else -1
            col = "#ffa657" if st_x >= hull.xm else "#79c0ff"
            pts = [(bx0 + side * hb * b_scale, by0 - z * b_scale) for hb, z in zip(hbs_st[valid], zs_st[valid])]
            for i in range(len(pts) - 1):
                draw.line([pts[i], pts[i+1]], fill=col, width=1)

    # 4. 水力與型值表面板
    stats = calculate_hydrostatics(hull)
    info_x = 1750
    info_y = 750
    draw.rectangle([info_x - 20, info_y - 20, w - 60, h - 60], fill="#161b22", outline="#30363d", width=1)
    draw.text((info_x, info_y), "【水動力與型值統計 (Hydrostatics)】", fill="#f0883e", font=font_sub)
    lines_text = [
        f"設計水線長 (LWL): {stats['lwl_m']} m ({stats['lwl_vox']} 格)",
        f"型寬水線處 (BWL): {stats['bwl_m']} m ({stats['bwl_vox']} 格)",
        f"設計吃水 (Draft): {stats['draft_m']} m ({stats['draft_vox']} 格)",
        f"排水體積: {stats['disp_volume_m3']} m³",
        f"海水排水量: {stats['displacement_tonnes_seawater']} 公噸 (海水比重 1.025)",
        f"方塊係數 (Cb): {stats['Cb']}",
        f"中剖面係數 (Cm): {stats['Cm']}",
        f"稜形係數 (Cp): {stats['Cp']}",
        f"水線面係數 (Cwp): {stats['Cwp']}",
        f"長寬比 (L/B): {stats['L_over_B']} (巡防艦頂級高速比)",
        f"寬吃比 (B/T): {stats['B_over_T']}",
        f"浮心縱向位置 (LCB): x={stats['lcb_x']} (水線長 {stats['lcb_percent']}%)",
        "",
        "【艦體特徵】",
        "• 14° 斜升角尖底＋R18 圓滑舭部，降低阻力並確保橫向穩定",
        "• 水線以上向內微縮 2.5 格 (Tumblehome)，集中側舷重砲重心",
        "• 24 門 18 磅長砲主甲板乾舷達 1.6m，高海況下依然能全開火"
    ]
    cur_y = info_y + 35
    for line in lines_text:
        draw.text((info_x, cur_y), line, fill="#e6edf3", font=font_body)
        cur_y += 24

    im.save(out_png)
    print(f"✓ 已生成線形圖紙: {out_png}")
    return stats


def generate_shell_preview_voxels(hull, out_vox_txt, thickness=4):
    """生成空心船殼預覽 voxel 清單（供驗證與草稿檢視）"""
    print("正在計算船殼預覽 voxel 空間...")
    x0 = int(hull.sp_x0 - hull.sp_rake - 5)
    x1 = int(hull.st_x0 + hull.st_rx + 5)
    z0 = 0
    z1 = int(max(hull.sh['z_aft'], hull.sh['z_fwd']) + 15)

    voxels = []
    # 遍歷網格格心
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            hb_val = hull.hb(x + 0.5, z + 0.5)
            if np.isnan(hb_val) or hb_val < hull.half:
                continue
            max_dy = int(math.floor(hb_val))
            min_dy = max(0, max_dy - thickness + 1)
            for dy in range(min_dy, max_dy + 1):
                y_p = YC - dy
                y_s = YC + dy
                # 判定外板顏色：水線下鍍銅色 168，水線上深黑 36
                color = 168 if (z + 0.5) <= hull.dwl else 36
                voxels.append((x, y_p, z, color))
                if dy > 0:
                    voxels.append((x, y_s, z, color))

    # 去重並排序
    voxels = sorted(list(set(voxels)))
    os.makedirs(os.path.dirname(out_vox_txt), exist_ok=True)
    with open(out_vox_txt, "w", encoding="utf-8") as f:
        f.write(f"# kiara-phoenix-01m 船殼預覽 (thickness={thickness})\n")
        for vx in voxels:
            f.write(f"{vx[0]},{vx[1]},{vx[2]},{vx[3]}\n")

    print(f"✓ 已生成預覽格子檔: {out_vox_txt} (共 {len(voxels)} 格)")
    return len(voxels)


def main():
    design_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    plan_path = os.path.join(design_dir, "plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    hull = Hull(plan)
    work_dir = os.path.dirname(os.path.abspath(plan_path))
    parent_dir = os.path.dirname(work_dir)

    out_png = os.path.join(parent_dir, "overlays", "sheet01_lines_v1.png")
    out_vox = os.path.join(parent_dir, "masks", "hull", "shell_preview.vox.txt")
    verify_json = os.path.join(work_dir, "verify_lines.json")

    stats = generate_lines_blueprint(hull, out_png)
    voxel_count = generate_shell_preview_voxels(hull, out_vox, thickness=plan['lines'].get('shell_preview_thickness', 4))

    stats['shell_preview_voxels'] = voxel_count
    with open(verify_json, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"✓ 已生成驗證檔案: {verify_json}")


if __name__ == "__main__":
    main()
