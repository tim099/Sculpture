# 炎羽號（kiara-phoenix-01m）桅桿落格腳本
import os, sys, subprocess

masks_dir = r"D:\Unity\Valhalla\Sculpture\works\kiara-phoenix-01m\masks\masts"

masts = [
    ("kiara-phoenix-01m-mast-fore", os.path.join(masks_dir, "mast_fore.vox.txt"), 9455),
    ("kiara-phoenix-01m-mast-main", os.path.join(masks_dir, "mast_main.vox.txt"), 12931),
    ("kiara-phoenix-01m-mast-mizzen", os.path.join(masks_dir, "mast_mizzen.vox.txt"), 5357),
    ("kiara-phoenix-01m-bowsprit", os.path.join(masks_dir, "bowsprit.vox.txt"), 2871),
]

for work_id, path, count in masts:
    print(f"[+] 正在落格: {work_id} ({count} 格)...")
    cmd = [
        "senate", "cmd", "sculpture",
        "--arg", "op=stampvox",
        f"--arg", f"work={work_id}",
        "--arg", "persona=kiara",
        f"--arg", f"voxels={path.replace('\\', '/')}",
        "--arg", "at=0,0,0",
        f"--arg", f"expect_pixels={count}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=r"D:\Unity\Senate")
    if res.returncode != 0:
        print(f"❌ 錯誤: {work_id} 落格失敗 (exit {res.returncode}):\n{res.stderr or res.stdout}")
        sys.exit(1)
    print(f"  ✓ {work_id} 成功落地 {count} 格")

print("\n🎉 四大主桅桿已全數成功落格！")
