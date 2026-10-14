# -*- coding: utf-8 -*-
"""
炎羽號（kiara-phoenix-01m）專屬甲板舷梯子作品生成
依據：Sculpture_Shipbuilding.md §9
"""
import os
import sys
import json
import subprocess
import datetime

MAIN_WORK = "kiara-phoenix-01m"
LADDERS_WORK = "kiara-phoenix-01m-ladders"
WORK_DIR = "D:/Unity/Valhalla/Sculpture/works"

def run_senate(args):
    cmd = ["dotnet", "run", "--project", "D:/Unity/Senate/src/Senate.Cli", "--"] + args
    res = subprocess.run(cmd, cwd="D:/Unity/Senate", capture_output=True, text=True, encoding="utf-8")
    return res.returncode, res.stdout, res.stderr

# 1. 建立子作品
lad_path = os.path.join(WORK_DIR, LADDERS_WORK)
if not os.path.exists(lad_path):
    print(f"[+] 建立任務子作品: {LADDERS_WORK}...")
    run_senate([
        "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=create",
        "--arg", f"id={LADDERS_WORK}", "--arg", "persona=kiara", "--arg", "account=Myth",
        "--arg", f"parent_work={MAIN_WORK}", "--arg", "title=炎羽號 甲板舷梯（上下通行路網）",
        "--arg", "size=576,181,100", "--arg", "tags=sub"
    ])

run_senate([
    "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=update",
    "--arg", f"work={LADDERS_WORK}", "--arg", "persona=kiara",
    "--arg", "size=576,181,100", "--arg", "meters_per_voxel=0.1", "--arg", "tags=sub"
])

# 2. 生成階梯木料 (橡木色 136)
# 階梯寬度 6 格 (y: 87..93)
voxels = {}

# (A) 主艙口階梯: x 266..284, z 51..70 (走道高 70, 下層 50)
steps_main = 10
dx_m = (284 - 266) / steps_main
dz_m = (70 - 51) / steps_main
for s in range(steps_main):
    x = int(round(266 + s * dx_m))
    z = int(round(51 + s * dz_m))
    for y in range(88, 94):
        voxels[(x, y, z)] = 136
        voxels[(x + 1, y, z)] = 136

# (B) 前艙口階梯: x 371..384, z 51..78 (艏樓高 78)
steps_fore = 14
dx_f = (384 - 371) / steps_fore
dz_f = (78 - 51) / steps_fore
for s in range(steps_fore):
    x = int(round(371 + s * dx_f))
    z = int(round(51 + s * dz_f))
    for y in range(88, 94):
        voxels[(x, y, z)] = 136
        voxels[(x + 1, y, z)] = 136

# (C) 後艙口階梯: x 171..184, z 51..78 (後甲板高 78)
steps_aft = 14
dx_a = (184 - 171) / steps_aft
dz_a = (78 - 51) / steps_aft
for s in range(steps_aft):
    x = int(round(171 + s * dx_a))
    z = int(round(51 + s * dz_a))
    for y in range(88, 94):
        voxels[(x, y, z)] = 136
        voxels[(x + 1, y, z)] = 136

txt_fn = os.path.join(WORK_DIR, MAIN_WORK, "design", "ladders.vox.txt")
with open(txt_fn, "w", encoding="utf-8") as f:
    f.write("# x,y,z,color\n")
    for (x, y, z), c in sorted(voxels.items()):
        f.write(f"{x},{y},{z},{c}\n")

print(f"[+] Stampvox {LADDERS_WORK} ({len(voxels)} 格)...")
run_senate([
    "cmd", "sculpture", "--arg", "op=stampvox", "--arg", f"work={LADDERS_WORK}",
    "--arg", "persona=kiara", "--arg", f"voxels={txt_fn}", "--arg", "at=0,0,0",
    "--arg", f"expect_pixels={len(voxels)}"
])

# 3. 註冊關鍵導航固定點 (foot, lo, hi, head)
anchors_to_set = [
    # 主艙口梯
    ("main.foot", "264,90,51"),
    ("main.lo", "266,90,52"),
    ("main.hi", "283,90,69"),
    ("main.head", "286,90,71"),
    # 前艙口梯
    ("fore.foot", "369,90,51"),
    ("fore.lo", "371,90,52"),
    ("fore.hi", "383,90,77"),
    ("fore.head", "386,90,79"),
    # 後艙口梯
    ("aft.foot", "169,90,51"),
    ("aft.lo", "171,90,52"),
    ("aft.hi", "183,90,77"),
    ("aft.head", "186,90,79"),
]

for name, at_str in anchors_to_set:
    run_senate([
        "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=anchor",
        "--arg", f"work={LADDERS_WORK}", "--arg", "persona=kiara",
        "--arg", f"name={name}", "--arg", f"at={at_str}", "--arg", "overwrite=1"
    ])
print(f"✓ 註冊了 {len(anchors_to_set)} 個梯子寻路固定點！")

# 4. 加入 assembly links.json，帶 meta kind=ladders
assembly_links_fn = os.path.join(WORK_DIR, "kiara-phoenix-01m-assembly", "links.json")
with open(assembly_links_fn, "r", encoding="utf-8") as f:
    assembly_links = json.load(f)

links_dict = {l["name"]: l for l in assembly_links.get("links", [])}
links_dict["梯子"] = {
    "name": "梯子",
    "work": LADDERS_WORK,
    "at": [0, 0, 0],
    "turn": 0,
    "mirror": "",
    "pivot": [576, 181, 100],
    "enabled": True,
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "persona": "kiara",
    "note": "炎羽號三座甲板通聯舷梯（含 12 個寻路導航固定點）",
    "meta": {
        "kind": "ladders"
    }
}

assembly_links["schema"] = 3
assembly_links["links"] = list(links_dict.values())
with open(assembly_links_fn, "w", encoding="utf-8") as f:
    json.dump(assembly_links, f, indent=2, ensure_ascii=False)

print("🎉 甲板舷梯與遊戲寻路導航點全部安裝完畢！")
