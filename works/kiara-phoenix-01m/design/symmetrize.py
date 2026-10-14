# 炎羽號（kiara-phoenix-01m）鏡像對齊補齊腳本
import os, sys, subprocess
import numpy as np

work_dir = r"D:\Unity\Valhalla\Sculpture\works\kiara-phoenix-01m"
design_dir = os.path.join(work_dir, "design")

list_txt = os.path.join(design_dir, "current_voxels2.txt")
cmd = [
    "senate", "cmd", "sculpture",
    "--arg", "op=export",
    "--arg", "work=kiara-phoenix-01m",
    "--arg", "format=list",
    f"--arg", f"out={list_txt.replace('\\', '/')}"
]
subprocess.run(cmd, check=True, cwd=r"D:\Unity\Senate")

grid = np.zeros((576, 181, 100), np.uint8)
with open(list_txt, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"): continue
        p = line.split(",")
        grid[int(p[0]), int(p[1]), int(p[2])] = int(p[3])

missing_mirror = []
for x in range(576):
    for y in range(91): # 0..90
        my = 180 - y
        for z in range(100):
            c1 = grid[x, y, z]
            c2 = grid[x, my, z]
            if c1 > 0 and c2 == 0:
                missing_mirror.append((x, my, z, c1))
            elif c1 == 0 and c2 > 0:
                missing_mirror.append((x, y, z, c2))

print(f"缺失鏡像格數: {len(missing_mirror)} 格")
if missing_mirror:
    sym_path = os.path.join(design_dir, "sym_patch.vox.txt")
    with open(sym_path, "w", encoding="utf-8") as f:
        for x, y, z, c in missing_mirror:
            f.write(f"{x},{y},{z},{c}\n")
    cmd_patch = [
        "senate", "cmd", "sculpture",
        "--arg", "op=stampvox",
        "--arg", "work=kiara-phoenix-01m",
        "--arg", "persona=kiara",
        f"--arg", f"voxels={sym_path.replace('\\', '/')}",
        "--arg", "at=0,0,0",
        f"--arg", f"expect_pixels={len(missing_mirror)}"
    ]
    subprocess.run(cmd_patch, check=True, cwd=r"D:\Unity\Senate")
    print("✓ 鏡像補齊完成！")
