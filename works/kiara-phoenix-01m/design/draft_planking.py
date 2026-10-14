# 炎羽號（kiara-phoenix-01m）新圖紙 03：外板、砲門與甲板壓樑（Phase 3: Planking, Gunports & Clamps）
# 用法：python -I -X utf8 -B draft_planking.py <design 資料夾>

import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC, FONT
from draft_hull import build as build_framing

NX, NY, NZ = 576, 181, 100


def build_planking(plan):
    H, solid, d, own_frames, frame_names, frame_layer, aft, dropped = build_framing(plan)
    P = plan['planking']
    D = plan['decks']
    F = plan['framing']

    # 1. 判定砲門開口空間 (24 門 18 磅長砲，每舷 12 門)
    port_stations = D['ports']['stations']
    pw = D['ports']['width']  # 6
    ph = D['ports']['height'] # 6
    pz_low = D['gun_deck_z'] + D['ports']['sill_above_deck'] # 50 + 4 = 54
    pz_high = pz_low + ph - 1 # 59

    is_port_opening = np.zeros((NX, NY, NZ), bool)
    for st_x in port_stations:
        x_min = st_x - pw // 2
        x_max = x_min + pw - 1
        is_port_opening[x_min:x_max + 1, :, pz_low:pz_high + 1] = True

    # 2. 需要從既有肋骨中刻除的砲門格子 (Carve ports out of frames)
    # 只要在砲門 x, z 範圍內且屬於肋骨層 (d <= 1 + F['moulded'] + 1.5) 的格
    ports_carve_mask = (own_frames > 0) & is_port_opening & (d <= 1.0 + F['moulded'] + 2.0)
    carve_coords = np.argwhere(ports_carve_mask)

    # 3. 砲門襯框 (Sills, Lintels & Linings, 141 號木色)
    # 在砲門四周一圈 (下緣 z_low-1, 上緣 z_high+1, 側舷 x_min-1, x_max+1) 的肋骨深度層
    port_frame_mask = np.zeros((NX, NY, NZ), bool)
    for st_x in port_stations:
        x_min = st_x - pw // 2
        x_max = x_min + pw - 1
        # 四周輪廓
        rim_x = (np.arange(NX) >= x_min - 1) & (np.arange(NX) <= x_max + 1)
        rim_z = (np.arange(NZ) >= pz_low - 1) & (np.arange(NZ) <= pz_high + 1)
        inner_x = (np.arange(NX) >= x_min) & (np.arange(NX) <= x_max)
        inner_z = (np.arange(NZ) >= pz_low) & (np.arange(NZ) <= pz_high)
        rim = rim_x[:, None, None] & rim_z[None, None, :] & ~(inner_x[:, None, None] & inner_z[None, None, :])
        # 深度在肋骨層
        m = rim & solid & (d > 1.0) & (d <= 1.0 + F['moulded']) & (own_frames == 0) & ~ports_carve_mask
        port_frame_mask |= m

    # 4. 外板層 (Planking): 深度 0.0 < d <= 1.41421356
    # 排除砲門開口、排除骨架、排除被刻除區
    plank_mask = solid & (d > 0.0) & (d <= 1.41421356) & (own_frames == 0) & ~is_port_opening & ~port_frame_mask

    # 塗裝上色:
    # z <= 38 (水線下): 168 (鍍銅色)
    # 38 < z < 51: 36 (深黑)
    # 51 <= z <= 63: 砲門帶 (208 象牙白，並在砲門上下緣點綴 132 鳳凰赤緋)
    # z > 63: 36 (深黑舷牆)
    Z_grid = np.arange(NZ)[None, None, :]
    plank_colors = np.full((NX, NY, NZ), 36, np.uint8)
    plank_colors = np.where(Z_grid <= P['paint_waterline_z'], P['colors']['copper_bottom'], plank_colors)
    gun_band = (Z_grid >= 51) & (Z_grid <= 63)
    plank_colors = np.where(gun_band, P['colors']['gun_band_white'], plank_colors)
    # 砲門帶上下緣飾線 (z=51, z=63) 塗鳳凰赤緋 132
    accent_lines = (Z_grid == 51) | (Z_grid == 63)
    plank_colors = np.where(gun_band & accent_lines, P['colors']['phoenix_crimson'], plank_colors)

    # 5. 舷牆頂蓋 (Capping Rail, 104 號橡木色)
    # 尋找每欄最高實心格上方第一格 (且在舷牆頂部附近 z > 60)
    cap_mask = np.zeros((NX, NY, NZ), bool)
    for xi in range(NX):
        for yi in range(NY):
            z_indices = np.where(solid[xi, yi, :])[0]
            if len(z_indices) > 0:
                top_z = z_indices.max()
                if top_z >= 60 and top_z + 1 < NZ:
                    cap_mask[xi, yi, top_z + 1] = True
    # 舷牆頂蓋只保留在外板與肋骨欄位 (DY >= half_beam - 8)
    cap_mask &= (np.abs(np.arange(NY)[None, :, None] - YC) >= 20)

    # 6. 甲板壓樑 (Clamps, 136 號深橡木色)
    # 肋骨內側面 (1+moulded < d <= 2.5+moulded)，在主砲甲板橫樑下方 (z=47, 48)
    clamp_mask = solid & (d > 1.0 + F['moulded']) & (d <= 2.8 + F['moulded']) & ((Z_grid == 47) | (Z_grid == 48)) & ~is_port_opening

    return {
        "H": H,
        "ports_carve_coords": carve_coords,
        "port_frame_mask": port_frame_mask,
        "plank_mask": plank_mask,
        "plank_colors": plank_colors,
        "cap_mask": cap_mask,
        "clamp_mask": clamp_mask,
        "port_stations": port_stations
    }


def main():
    design_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    plan_path = os.path.join(design_dir, "plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    data = build_planking(plan)

    work_dir = os.path.dirname(os.path.abspath(plan_path))
    parent_dir = os.path.dirname(work_dir)
    masks_dir = os.path.join(parent_dir, "masks", "planking")
    os.makedirs(masks_dir, exist_ok=True)

    manifest = []

    # 1. 砲門刻除檔
    carve_coords = data["ports_carve_coords"]
    carve_fn = os.path.join(masks_dir, "gunports_carve.txt")
    with open(carve_fn, "w", encoding="utf-8") as f:
        for pt in carve_coords:
            f.write(f"{pt[0]},{pt[1]},{pt[2]}\n")
    print(f"✓ 已生成砲門刻除遮罩: {carve_fn} (共 {len(carve_coords)} 格)")

    # 2. 砲門襯框 (141 木色)
    pf_coords = np.argwhere(data["port_frame_mask"])
    pf_fn = os.path.join(masks_dir, "gunports_lining.vox.txt")
    with open(pf_fn, "w", encoding="utf-8") as f:
        for pt in pf_coords:
            f.write(f"{pt[0]},{pt[1]},{pt[2]},141\n")
    manifest.append({"name": "gunports_lining", "count": len(pf_coords), "path": pf_fn})

    # 3. 外板分段 (按 X 每 60 格一段，方便 stampvox)
    plank_mask = data["plank_mask"]
    plank_colors = data["plank_colors"]
    chunk_size = 60
    total_plank = 0
    for chunk_idx, x_start in enumerate(range(70, 520, chunk_size)):
        x_end = min(x_start + chunk_size, 520)
        sub_mask = plank_mask.copy()
        sub_mask[:x_start, :, :] = False
        sub_mask[x_end:, :, :] = False
        coords = np.argwhere(sub_mask)
        if len(coords) == 0: continue
        fn = os.path.join(masks_dir, f"plank_chunk_{chunk_idx:02d}.vox.txt")
        with open(fn, "w", encoding="utf-8") as f:
            for pt in coords:
                c = plank_colors[pt[0], pt[1], pt[2]]
                f.write(f"{pt[0]},{pt[1]},{pt[2]},{c}\n")
        manifest.append({"name": f"plank_chunk_{chunk_idx:02d}", "count": len(coords), "path": fn})
        total_plank += len(coords)

    # 4. 舷牆頂蓋 (104 木色)
    cap_coords = np.argwhere(data["cap_mask"])
    cap_fn = os.path.join(masks_dir, "capping_rail.vox.txt")
    with open(cap_fn, "w", encoding="utf-8") as f:
        for pt in cap_coords:
            f.write(f"{pt[0]},{pt[1]},{pt[2]},104\n")
    manifest.append({"name": "capping_rail", "count": len(cap_coords), "path": cap_fn})

    # 5. 甲板壓樑 Clamps (136 橡木色)
    clamp_coords = np.argwhere(data["clamp_mask"])
    clamp_fn = os.path.join(masks_dir, "clamps.vox.txt")
    with open(clamp_fn, "w", encoding="utf-8") as f:
        for pt in clamp_coords:
            f.write(f"{pt[0]},{pt[1]},{pt[2]},136\n")
    manifest.append({"name": "clamps", "count": len(clamp_coords), "path": clamp_fn})

    # 驗證檔
    verify_path = os.path.join(work_dir, "verify_planking.json")
    with open(verify_path, "w", encoding="utf-8") as f:
        json.dump({
            "carve_ports_voxels": len(carve_coords),
            "port_lining_voxels": len(pf_coords),
            "planking_total_voxels": total_plank,
            "capping_rail_voxels": len(cap_coords),
            "clamps_voxels": len(clamp_coords),
            "gunports_count": len(data["port_stations"]) * 2,
            "manifest": manifest
        }, f, indent=2, ensure_ascii=False)

    print(f"✓ 外板與砲門遮罩生成完畢: 外板共 {total_plank} 格，壓樑 {len(clamp_coords)} 格，頂蓋 {len(cap_coords)} 格")
    print(f"✓ 驗證檔已保存: {verify_path}")


if __name__ == "__main__":
    main()
