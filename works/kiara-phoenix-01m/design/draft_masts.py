# 炎羽號（kiara-phoenix-01m）新圖紙 05：三桅全帆裝、艏斜桅與帆桁（Phase 5: Masts & Yards）
# 用法：python -I -X utf8 -B draft_masts.py <design 資料夾>

import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC

def generate_cylinder(x0, y0, z0, z1, r_bot, r_top, color=177):
    voxels = []
    dz_tot = max(1, z1 - z0)
    for z in range(z0, z1 + 1):
        u = (z - z0) / dz_tot
        r = r_bot + (r_top - r_bot) * u
        r_ceil = int(math.ceil(r))
        for dx in range(-r_ceil, r_ceil + 1):
            for dy in range(-r_ceil, r_ceil + 1):
                if dx * dx + dy * dy <= r * r:
                    voxels.append((x0 + dx, y0 + dy, z, color))
    return voxels

def generate_top_platform(x0, y0, z_plat, lx=20, ly=26, color=104):
    voxels = []
    # 平台地板 (2 格厚)
    for dx in range(-lx//2, lx//2 + 1):
        for dy in range(-ly//2, ly//2 + 1):
            # 避開桅桿孔 (半徑 4)
            if dx*dx + dy*dy > 16:
                # 橢圓切邊
                if (dx / (lx/2))**2 + (dy / (ly/2))**2 <= 1.0:
                    voxels.append((x0 + dx, y0 + dy, z_plat, color))
                    voxels.append((x0 + dx, y0 + dy, z_plat + 1, color))
    # 支撐托架 (Trestletrees)
    for dy in (-ly//4, ly//4):
        for dx in range(-lx//2 - 2, lx//2 + 3):
            for dz in range(-3, 0):
                voxels.append((x0 + dx, y0 + dy, z_plat + dz, 136))
    return voxels

def build_fore_mast(masts_plan):
    m = masts_plan['fore']
    mx, my = m['x'], YC
    voxels = []
    # 1. 下桅 (Lower mast): z 4..210, 半徑 3.6..2.8
    voxels.extend(generate_cylinder(mx, my, 4, 210, 3.6, 2.8, 177))
    # 桅頂平台 (Top): z = 195
    voxels.extend(generate_top_platform(mx, my, 195, lx=22, ly=26, color=104))
    # 2. 中桅 (Topmast): z 195..295, 半徑 2.4..1.8
    voxels.extend(generate_cylinder(mx, my, 195, 295, 2.4, 1.8, 177))
    # 中桅平台 (Crosstrees): z = 285
    voxels.extend(generate_top_platform(mx, my, 285, lx=14, ly=18, color=104))
    # 3. 頂桅 (Topgallant & Royal): z 285..360, 半徑 1.5..1.0
    voxels.extend(generate_cylinder(mx, my, 285, 360, 1.5, 1.0, 177))
    # 桅頂帽 (Truck): z = 360..362
    voxels.extend(generate_cylinder(mx, my, 360, 362, 2.0, 1.5, 208))
    return sorted(list(set(voxels)))

def build_main_mast(masts_plan):
    m = masts_plan['main']
    mx, my = m['x'], YC
    voxels = []
    # 1. 下桅: z 4..225, 半徑 4.0..3.2
    voxels.extend(generate_cylinder(mx, my, 4, 225, 4.0, 3.2, 177))
    # 桅頂平台: z = 210
    voxels.extend(generate_top_platform(mx, my, 210, lx=24, ly=30, color=104))
    # 2. 中桅: z 210..315, 半徑 2.8..2.0
    voxels.extend(generate_cylinder(mx, my, 210, 315, 2.8, 2.0, 177))
    # 中桅平台: z = 305
    voxels.extend(generate_top_platform(mx, my, 305, lx=16, ly=20, color=104))
    # 3. 頂桅: z 305..380, 半徑 1.8..1.1
    voxels.extend(generate_cylinder(mx, my, 305, 380, 1.8, 1.1, 177))
    # 桅頂帽: z = 380..382
    voxels.extend(generate_cylinder(mx, my, 380, 382, 2.4, 1.8, 208))
    return sorted(list(set(voxels)))

def build_mizzen_mast(masts_plan):
    m = masts_plan['mizzen']
    mx, my = m['x'], YC
    voxels = []
    # 1. 下桅: z 4..185, 半徑 2.8..2.2
    voxels.extend(generate_cylinder(mx, my, 4, 185, 2.8, 2.2, 177))
    # 桅頂平台: z = 170
    voxels.extend(generate_top_platform(mx, my, 170, lx=18, ly=22, color=104))
    # 2. 中桅: z 170..265, 半徑 2.0..1.5
    voxels.extend(generate_cylinder(mx, my, 170, 265, 2.0, 1.5, 177))
    # 3. 頂桅: z 255..320, 半徑 1.4..0.9
    voxels.extend(generate_cylinder(mx, my, 255, 320, 1.4, 0.9, 177))
    # 桅頂帽: z = 320..322
    voxels.extend(generate_cylinder(mx, my, 320, 322, 1.8, 1.2, 208))
    return sorted(list(set(voxels)))

def build_bowsprit(masts_plan):
    b = masts_plan['bowsprit']
    x0, y0, z0 = b['heel_x'], YC, 54
    length = b['length'] # 135
    angle_rad = math.radians(b['angle_deg']) # 24 deg
    dx = math.cos(angle_rad)
    dz = math.sin(angle_rad)
    voxels = []
    for step in range(length):
        cur_x = int(round(x0 + step * dx))
        cur_z = int(round(z0 + step * dz))
        u = step / length
        r = b['r'][0] + (b['r'][1] - b['r'][0]) * u
        r_ceil = int(math.ceil(r))
        for cy in range(-r_ceil, r_ceil + 1):
            for cz in range(-r_ceil, r_ceil + 1):
                if cy*cy + cz*cz <= r*r:
                    voxels.append((cur_x, y0 + cy, cur_z + cz, 177))
    # 艏斜桅帽 (Bowsprit Cap)
    cap_x = int(round(x0 + length * 0.7 * dx))
    cap_z = int(round(z0 + length * 0.7 * dz))
    for cx in range(-2, 3):
        for cy in range(-5, 6):
            for cz in range(-3, 6):
                voxels.append((cap_x + cx, y0 + cy, cap_z + cz, 104))
    return sorted(list(set(voxels)))

def build_yard(length_y, diameter_vox, color=177):
    """橫向帆桁 (沿 Y 軸放置，長度 length_y，中心在 0,0,0)"""
    voxels = []
    half_l = length_y // 2
    r_max = diameter_vox / 2.0
    for dy in range(-half_l, half_l + 1):
        u = abs(dy) / half_l
        r = r_max * (1.0 - 0.35 * (u ** 1.5))
        r_ceil = int(math.ceil(r))
        for dx in range(-r_ceil, r_ceil + 1):
            for dz in range(-r_ceil, r_ceil + 1):
                if dx*dx + dz*dz <= r*r:
                    voxels.append((dx, dy, dz, color))
    return sorted(list(set(voxels)))

def main():
    design_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    plan_path = os.path.join(design_dir, "plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    work_dir = os.path.dirname(os.path.abspath(plan_path))
    parent_dir = os.path.dirname(work_dir)
    masks_dir = os.path.join(parent_dir, "masks", "masts")
    os.makedirs(masks_dir, exist_ok=True)

    def dedup(vox_list):
        d = {}
        for x, y, z, c in vox_list:
            d[(x, y, z)] = c
        return sorted([(x, y, z, d[(x, y, z)]) for x, y, z in d.keys()])

    m_fore = dedup(build_fore_mast(plan['masts']))
    m_main = dedup(build_main_mast(plan['masts']))
    m_mizzen = dedup(build_mizzen_mast(plan['masts']))
    m_bow = dedup(build_bowsprit(plan['masts']))

    masts_files = [
        ("fore", m_fore, "mast_fore.vox.txt"),
        ("main", m_main, "mast_main.vox.txt"),
        ("mizzen", m_mizzen, "mast_mizzen.vox.txt"),
        ("bowsprit", m_bow, "bowsprit.vox.txt")
    ]

    for name, vox, fn in masts_files:
        path = os.path.join(masks_dir, fn)
        with open(path, "w", encoding="utf-8") as f:
            for x, y, z, c in vox:
                f.write(f"{x},{y},{z},{c}\n")
        print(f"✓ 桅桿生成: {name} ({len(vox)} 格) → {path}")

    # 2. 產生標準帆桁 (沿 Y 軸，中心在 0,0,0)
    # 前桅帆桁: course 160 格 (16m), topsail 120 格 (12m), topgallant 80 格 (8m)
    # 主桅帆桁: course 180 格 (18m), topsail 135 格 (13.5m), topgallant 90 格 (9m)
    # 後桅帆桁: crossjack 120 格, topsail 90 格
    yards_data = [
        ("fore-course", 160, 4.0),
        ("fore-topsail", 120, 3.2),
        ("fore-topgallant", 80, 2.4),
        ("main-course", 180, 4.4),
        ("main-topsail", 135, 3.4),
        ("main-topgallant", 90, 2.6),
        ("mizzen-crossjack", 120, 3.2),
        ("mizzen-topsail", 90, 2.4),
    ]

    yards_manifest = []
    for yname, ylen, ydia in yards_data:
        yvox = build_yard(ylen, ydia, 177)
        yfn = os.path.join(masks_dir, f"yard_{yname}.vox.txt")
        with open(yfn, "w", encoding="utf-8") as f:
            for x, y, z, c in yvox:
                f.write(f"{x},{y},{z},{c}\n")
        yards_manifest.append({"name": yname, "length": ylen, "diameter": ydia, "voxels": len(yvox), "path": yfn})
        print(f"✓ 帆桁生成: {yname} (長 {ylen} 格, {len(yvox)} 格) → {yfn}")

    verify_path = os.path.join(work_dir, "verify_masts.json")
    with open(verify_path, "w", encoding="utf-8") as f:
        json.dump({
            "masts": {
                "fore": len(m_fore),
                "main": len(m_main),
                "mizzen": len(m_mizzen),
                "bowsprit": len(m_bow)
            },
            "yards": yards_manifest
        }, f, indent=2, ensure_ascii=False)
    print(f"✓ 桅檣與帆桁驗證檔已保存: {verify_path}")

if __name__ == "__main__":
    main()
