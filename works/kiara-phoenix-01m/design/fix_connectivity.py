# 炎羽號（kiara-phoenix-01m）連通性檢查與微調修補腳本
# 檢查非主連通元件的小碎片，將其 6 連通至主體，或剔除純漂浮碎屑

import os, sys, json, subprocess
import numpy as np
from scipy import ndimage

work_dir = r"D:\Unity\Valhalla\Sculpture\works\kiara-phoenix-01m"
design_dir = os.path.join(work_dir, "design")

# 1. 匯出目前清單
list_txt = os.path.join(design_dir, "current_voxels.txt")
print("正在匯出作品當前 voxel 清單...")
cmd = [
    "senate", "cmd", "sculpture",
    "--arg", "op=export",
    "--arg", "work=kiara-phoenix-01m",
    "--arg", "format=list",
    f"--arg", f"out={list_txt.replace('\\', '/')}"
]
subprocess.run(cmd, check=True, cwd=r"D:\Unity\Senate")

# 2. 讀取並構建 3D 空間 (576, 181, 100)
grid = np.zeros((576, 181, 100), np.uint8)
with open(list_txt, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = line.split(",")
        grid[int(parts[0]), int(parts[1]), int(parts[2])] = int(parts[3])

binary = grid > 0
total_before = int(binary.sum())
lab, n = ndimage.label(binary) # 6 連通
sizes = ndimage.sum(binary, lab, range(1, n + 1))
main_label = int(np.argmax(sizes)) + 1
main_mask = (lab == main_label)
stray_mask = binary & ~main_mask

num_stray = int(stray_mask.sum())
print(f"總 voxel 數: {total_before}，連通元件數: {n}，非主體碎屑: {num_stray} 格")

if num_stray == 0:
    print("✓ 作品已經是 100% 單一 6 連通元件，無需修復！")
    sys.exit(0)

# 3. 處理碎屑：檢查是否能補 1 格橋接格連到主體
bridge_voxels = []
carve_voxels = []

stray_coords = np.argwhere(stray_mask)
for x, y, z in stray_coords:
    c = grid[x, y, z]
    # 檢查 26 鄰域是否有主體格
    x0, x1 = max(0, x - 1), min(575, x + 1)
    y0, y1 = max(0, y - 1), min(180, y + 1)
    z0, z1 = max(0, z - 1), min(99, z + 1)
    sub_main = main_mask[x0:x1+1, y0:y1+1, z0:z1+1]
    
    if np.any(sub_main):
        # 尋找一個空白格，使其同時與 (x,y,z) 6 相鄰且與 sub_main 6 相鄰
        found_bridge = False
        for dx, dy, dz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
            bx, by, bz = x + dx, y + dy, z + dz
            if 0 <= bx < 576 and 0 <= by < 181 and 0 <= bz < 100:
                if grid[bx, by, bz] == 0: # 空白格
                    # 檢查 (bx, by, bz) 的 6 鄰居是否有 main_mask
                    has_main_neighbor = False
                    for ddx, ddy, ddz in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                        mx, my, mz = bx + ddx, by + ddy, bz + ddz
                        if 0 <= mx < 576 and 0 <= my < 181 and 0 <= mz < 100:
                            if main_mask[mx, my, mz]:
                                has_main_neighbor = True
                                break
                    if has_main_neighbor:
                        bridge_voxels.append((bx, by, bz, c))
                        found_bridge = True
                        break
        if not found_bridge:
            carve_voxels.append((x, y, z))
    else:
        carve_voxels.append((x, y, z))

# 去重
bridge_voxels = list(set(bridge_voxels))
print(f"計畫橋接補格: {len(bridge_voxels)} 格，直接剔除散屑: {len(carve_voxels)} 格")

# 寫入檔案
if carve_voxels:
    carve_path = os.path.join(design_dir, "fix_carve.txt")
    with open(carve_path, "w", encoding="utf-8") as f:
        for x, y, z in carve_voxels:
            f.write(f"{x},{y},{z}\n")
    print(f"正在刻除純散屑 ({len(carve_voxels)} 格)...")
    cmd_carve = [
        "senate", "cmd", "sculpture",
        "--arg", "op=carvevox",
        "--arg", "work=kiara-phoenix-01m",
        "--arg", "persona=kiara",
        f"--arg", f"voxels={carve_path.replace('\\', '/')}",
        "--arg", "at=0,0,0",
        f"--arg", f"expect_pixels={len(carve_voxels)}"
    ]
    subprocess.run(cmd_carve, check=True, cwd=r"D:\Unity\Senate")

if bridge_voxels:
    bridge_path = os.path.join(design_dir, "fix_bridge.vox.txt")
    with open(bridge_path, "w", encoding="utf-8") as f:
        for x, y, z, c in bridge_voxels:
            f.write(f"{x},{y},{z},{c}\n")
    print(f"正在貼入橋接格 ({len(bridge_voxels)} 格)...")
    cmd_bridge = [
        "senate", "cmd", "sculpture",
        "--arg", "op=stampvox",
        "--arg", "work=kiara-phoenix-01m",
        "--arg", "persona=kiara",
        f"--arg", f"voxels={bridge_path.replace('\\', '/')}",
        "--arg", "at=0,0,0",
        f"--arg", f"expect_pixels={len(bridge_voxels)}"
    ]
    subprocess.run(cmd_bridge, check=True, cwd=r"D:\Unity\Senate")

print("✓ 連通性修復完成！")
