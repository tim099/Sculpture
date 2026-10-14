# -*- coding: utf-8 -*-
"""
炎羽號（kiara-phoenix-01m）專屬前後彈藥庫子作品生成
依據：Sculpture_Shipbuilding.md §8、§9
"""
import os
import sys
import json
import subprocess
import datetime

MAIN_WORK = "kiara-phoenix-01m"
FORE_MAG_WORK = "kiara-phoenix-01m-magazine-fore"
AFT_MAG_WORK = "kiara-phoenix-01m-magazine-aft"
BARREL_SOURCE = "basecamp-frigate-constitution-01m-powder-barrel"
WORK_DIR = "D:/Unity/Valhalla/Sculpture/works"

def run_senate(args):
    cmd = ["dotnet", "run", "--project", "D:/Unity/Senate/src/Senate.Cli", "--"] + args
    res = subprocess.run(cmd, cwd="D:/Unity/Senate", capture_output=True, text=True, encoding="utf-8")
    return res.returncode, res.stdout, res.stderr

# 1. 建立兩個子作品（若尚未建立）
for mag_name, title in [(FORE_MAG_WORK, "炎羽號 前部彈藥庫"), (AFT_MAG_WORK, "炎羽號 後部主彈藥庫")]:
    mag_path = os.path.join(WORK_DIR, mag_name)
    if not os.path.exists(mag_path):
        print(f"[+] 建立任務子作品: {mag_name}...")
        code, out, err = run_senate([
            "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=create",
            "--arg", f"id={mag_name}", "--arg", "persona=kiara", "--arg", "account=Myth",
            "--arg", f"parent_work={MAIN_WORK}", "--arg", f"title={title}",
            "--arg", "size=44", "--arg", "tags=sub"
        ])
        print(out.strip()[-300:] if out else err)

    # 設置尺寸為 40, 40, 16
    run_senate([
        "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=update",
        "--arg", f"work={mag_name}", "--arg", "persona=kiara",
        "--arg", "size=40,40,16", "--arg", "meters_per_voxel=0.1", "--arg", "tags=sub"
    ])

# 2. 生成彈藥庫內部體積格子
# 銅皮鋪底 (168)、橡木牆 (136)、門洞 (5 格寬)
# 40 x 40 x 16 的本地空間：
# 地板 z=0 (168)
# 外牆 x=0, x=39, y=0, y=39 (136)，留門洞在 x=39, y=17..22
def build_mag_voxels(fn):
    voxels = {}
    # 地板
    for x in range(40):
        for y in range(40):
            voxels[(x, y, 0)] = 168
            voxels[(x, y, 15)] = 136  # 天花板
    # 牆壁
    for z in range(1, 15):
        for x in range(40):
            voxels[(x, 0, z)] = 136
            voxels[(x, 39, z)] = 136
        for y in range(40):
            voxels[(0, y, z)] = 136
            # 門洞在 x=39, y=18..22
            if not (18 <= y <= 22 and z <= 10):
                voxels[(39, y, z)] = 136
    
    with open(fn, "w", encoding="utf-8") as f:
        f.write("# x,y,z,color\n")
        for (x, y, z), c in sorted(voxels.items()):
            f.write(f"{x},{y},{z},{c}\n")
    return len(voxels)

for mag_name in [FORE_MAG_WORK, AFT_MAG_WORK]:
    txt_fn = os.path.join(WORK_DIR, MAIN_WORK, "design", f"{mag_name}.vox.txt")
    cnt = build_mag_voxels(txt_fn)
    print(f"[+] Stampvox {mag_name} ({cnt} 格)...")
    run_senate([
        "cmd", "sculpture", "--arg", "op=stampvox", "--arg", f"work={mag_name}",
        "--arg", "persona=kiara", "--arg", f"voxels={txt_fn}", "--arg", "at=0,0,0",
        "--arg", f"expect_pixels={cnt}"
    ])
    
    # 登記 anchors (blast, door)
    run_senate([
        "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=anchor",
        "--arg", f"work={mag_name}", "--arg", "persona=kiara",
        "--arg", "name=blast", "--arg", "at=20,20,5", "--arg", "overwrite=1"
    ])
    run_senate([
        "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=anchor",
        "--arg", f"work={mag_name}", "--arg", "persona=kiara",
        "--arg", "name=door", "--arg", "at=39,20,1", "--arg", "overwrite=1"
    ])

    # 放入火藥桶模型 (整齊排列在彈藥庫架上)
    models_fn = os.path.join(WORK_DIR, mag_name, "models.json")
    m_list = []
    barrel_idx = 1
    for bx in range(6, 34, 7):
        for by in range(6, 34, 7):
            m_list.append({
                "name": f"barrel-{barrel_idx:03d}",
                "source": "work",
                "file": "",
                "bytes": 0,
                "sha256": "",
                "work": BARREL_SOURCE,
                "axes": "sculpt",
                "at": [bx + 0.5, by + 0.5, 1.0],
                "pivot": [11, 11, 0],
                "rotate": [0, 0, 0],
                "scale": [0.2, 0.2, 0.2],
                "mirror": "",
                "color": "",
                "enabled": True,
                "note": f"100 lb 火藥桶 #{barrel_idx}",
                "persona": "kiara",
                "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "meta": {"kind": "powder", "powder_lb": 100}
            })
            barrel_idx += 1
    with open(models_fn, "w", encoding="utf-8") as f:
        json.dump({"schema": 2, "models": m_list}, f, indent=2, ensure_ascii=False)
    print(f"✓ {mag_name} 放置了 {len(m_list)} 桶火藥！")

# 3. 更新組裝件 links.json，將彈藥庫位置精確放在炎羽號艙底內部
assembly_links_fn = os.path.join(WORK_DIR, "kiara-phoenix-01m-assembly", "links.json")
with open(assembly_links_fn, "r", encoding="utf-8") as f:
    assembly_links = json.load(f)

links_dict = {l["name"]: l for l in assembly_links.get("links", [])}

# 炎羽號中線 y=90.5，彈藥庫寬度 40 => y 範圍 70..110，剛好置中！
# 前彈藥庫：x=350, y=71, z=18
links_dict["彈藥庫-前"] = {
    "name": "彈藥庫-前",
    "work": FORE_MAG_WORK,
    "at": [350, 71, 18],
    "turn": 0,
    "mirror": "",
    "pivot": [40, 40, 16],
    "enabled": True,
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "persona": "kiara",
    "note": "炎羽號專屬前部彈藥庫（完全收納於水線下尖底艙底）",
    "meta": {
        "kind": "magazine",
        "pos": "fore",
        "powder_lb": 1600
    }
}

# 後彈藥庫：x=180, y=71, z=18
links_dict["彈藥庫-後"] = {
    "name": "彈藥庫-後",
    "work": AFT_MAG_WORK,
    "at": [180, 71, 18],
    "turn": 0,
    "mirror": "",
    "pivot": [40, 40, 16],
    "enabled": True,
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "persona": "kiara",
    "note": "炎羽號專屬後部主彈藥庫（完全收納於水線下尖底艙底）",
    "meta": {
        "kind": "magazine",
        "pos": "aft",
        "powder_lb": 1600
    }
}

assembly_links["schema"] = 3
assembly_links["links"] = list(links_dict.values())
with open(assembly_links_fn, "w", encoding="utf-8") as f:
    json.dump(assembly_links, f, indent=2, ensure_ascii=False)

print("🎉 炎羽號專屬艙內彈藥庫已全部配置並嚴格收納在船底內壁！")
