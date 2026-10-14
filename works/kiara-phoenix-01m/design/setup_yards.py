# 炎羽號（kiara-phoenix-01m）帆桁子作品建立、落格與固定點登記腳本
import os, sys, json, subprocess

design_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(design_dir)
verify_path = os.path.join(design_dir, "verify_masts.json")

with open(verify_path, "r", encoding="utf-8") as f:
    data = json.load(f)

yards = data["yards"]
print(f"總帆桁部件: {len(yards)} 件")

for y in yards:
    name = y["name"]
    work_id = f"kiara-phoenix-01m-yard-{name}"
    vox_path = y["path"].replace("\\", "/")
    count = y["voxels"]
    ylen = y["length"]
    half_l = ylen // 2

    # 1. 建立子作品
    print(f"[+] 正在建立帆桁子作品: {work_id}...")
    cmd_create = [
        "senate", "cmd", "sculpture",
        "--arg", "op=work",
        "--arg", "sub=create",
        "--arg", "persona=kiara",
        f"--arg", f"id={work_id}",
        f"--arg", f"title=炎羽號 帆桁 {name}",
        "--arg", "parent_work=kiara-phoenix-01m",
        f"--arg", f"size={ylen + 20},{ylen + 20},30"
    ]
    subprocess.run(cmd_create, check=True, cwd=r"D:\Unity\Senate")

    # 更新 tags=sub 與比例
    cmd_up = [
        "senate", "cmd", "sculpture",
        "--arg", "op=work",
        "--arg", "sub=update",
        f"--arg", f"work={work_id}",
        "--arg", "persona=kiara",
        "--arg", "meters_per_voxel=0.1",
        "--arg", "tags=sub"
    ]
    subprocess.run(cmd_up, check=True, cwd=r"D:\Unity\Senate")

    # 2. 落格 stampvox (帆桁在子作品內部以 (0,0,0) 為中心放置在 (10, half_l+10, 15))
    # 為了簡便與標準化，在子作品內原點平移 at=10,half_l+10,15
    ox, oy, oz = 10, half_l + 10, 15
    print(f"  · 落格 {count} 格...")
    cmd_stamp = [
        "senate", "cmd", "sculpture",
        "--arg", "op=stampvox",
        f"--arg", f"work={work_id}",
        "--arg", "persona=kiara",
        f"--arg", f"voxels={vox_path}",
        f"--arg", f"at={ox},{oy},{oz}",
        f"--arg", f"expect_pixels={count}"
    ]
    subprocess.run(cmd_stamp, check=True, cwd=r"D:\Unity\Senate")

    # 3. 登記固定點 (Anchors)
    print(f"  · 登記固定點...")
    anchors = [
        ("pivot", f"{ox},{oy},{oz}"),
        ("arm-P", f"{ox},{oy - half_l},{oz}"),
        ("arm-S", f"{ox},{oy + half_l},{oz}"),
        ("earing-P", f"{ox},{oy - half_l + 2},{oz}"),
        ("earing-S", f"{ox},{oy + half_l - 2},{oz}")
    ]
    for aname, a_at in anchors:
        cmd_anc = [
            "senate", "cmd", "sculpture",
            "--arg", "op=work",
            "--arg", "sub=anchor",
            f"--arg", f"work={work_id}",
            "--arg", "persona=kiara",
            f"--arg", f"name={aname}",
            f"--arg", f"at={a_at}"
        ]
        subprocess.run(cmd_anc, check=True, cwd=r"D:\Unity\Senate")

print("\n🎉 全部 8 根標準帆桁子作品與固定點已全數設置完畢！")
