# -*- coding: utf-8 -*-
"""
炎羽號（kiara-phoenix-01m）參考夜隼號（Night Falcon）之遊戲全套細節補完
包括：
1. 專屬可動船舵子作品 (kiara-phoenix-01m-rudder) 與 hinge meta
2. 羅經櫃模型 (binnacle)
3. 主立式絞盤模型 (capstan)
4. 船艏左右雙鐵錨模型 (anchors)
5. 應急交通艇模型 (boat)
6. 船殼全艦 meta (waterline_z, crew, kind=ship)
7. 船尾飄揚的鳳凰海軍旗 (ensign flag)
"""
import os
import sys
import json
import subprocess
import datetime

MAIN_WORK = "kiara-phoenix-01m"
RUDDER_WORK = "kiara-phoenix-01m-rudder"
UPPER_DECK_WORK = "kiara-phoenix-01m-deck-upper"
ASSEMBLY_WORK = "kiara-phoenix-01m-assembly"
WORK_DIR = "D:/Unity/Valhalla/Sculpture/works"

def run_senate(args):
    cmd = ["dotnet", "run", "--project", "D:/Unity/Senate/src/Senate.Cli", "--"] + args
    res = subprocess.run(cmd, cwd="D:/Unity/Senate", capture_output=True, text=True, encoding="utf-8")
    return res.returncode, res.stdout, res.stderr

# ==========================================
# 1. 建造專屬可動船舵子作品 (kiara-phoenix-01m-rudder)
# ==========================================
rudder_path = os.path.join(WORK_DIR, RUDDER_WORK)
if not os.path.exists(rudder_path):
    print(f"[+] 建立船舵子作品: {RUDDER_WORK}...")
    run_senate([
        "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=create",
        "--arg", f"id={RUDDER_WORK}", "--arg", "persona=kiara", "--arg", "account=Myth",
        "--arg", f"parent_work={MAIN_WORK}", "--arg", "title=炎羽號 可動木質平衡舵",
        "--arg", "size=576,181,100", "--arg", "tags=sub"
    ])

run_senate([
    "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=update",
    "--arg", f"work={RUDDER_WORK}", "--arg", "persona=kiara",
    "--arg", "size=576,181,100", "--arg", "meters_per_voxel=0.1", "--arg", "tags=sub"
])

# 雕刻船舵本體
# 艉柱在 x=95, z=2 斜向 x=80, z=55，中線 y=90
# 舵板往 -x 延伸 7~9 格，厚度 3 格 (y: 89..91)
voxels_rudder = {}
for z in range(2, 56):
    # 艉柱前端 x
    x_lead = int(round(95 - (z - 2) * (15.0 / 53.0)))
    # 舵板寬度隨高度變化
    w = 7 if z < 30 else 8
    for dx in range(w):
        x = x_lead - dx
        # 水線下鍍銅 168，水線上深橡木 136
        c = 168 if z <= 38 else 136
        for y in range(89, 92):
            voxels_rudder[(x, y, z)] = c

# 鐵製舵紐 (pintles & gudgeons，黑色 36)
for z_hinge in [8, 20, 32, 45]:
    x_lead = int(round(95 - (z_hinge - 2) * (15.0 / 53.0)))
    for dx in range(4):
        for y in [88, 92]:
            voxels_rudder[(x_lead - dx, y, z_hinge)] = 36

rudder_txt = os.path.join(WORK_DIR, MAIN_WORK, "design", "rudder.vox.txt")
with open(rudder_txt, "w", encoding="utf-8") as f:
    f.write("# x,y,z,color\n")
    for (x, y, z), c in sorted(voxels_rudder.items()):
        f.write(f"{x},{y},{z},{c}\n")

print(f"[+] Stampvox {RUDDER_WORK} ({len(voxels_rudder)} 格)...")
run_senate([
    "cmd", "sculpture", "--arg", "op=stampvox", "--arg", f"work={RUDDER_WORK}",
    "--arg", "persona=kiara", "--arg", f"voxels={rudder_txt}", "--arg", "at=0,0,0",
    "--arg", f"expect_pixels={len(voxels_rudder)}"
])

# ==========================================
# 2. 將船舵模型掛進組裝件，帶 hinge 旋轉 meta
# ==========================================
assembly_models_fn = os.path.join(WORK_DIR, ASSEMBLY_WORK, "models.json")
if os.path.exists(assembly_models_fn):
    with open(assembly_models_fn, "r", encoding="utf-8") as f:
        assembly_models_data = json.load(f)
else:
    assembly_models_data = {"schema": 2, "models": []}

assembly_models_dict = {m["name"]: m for m in assembly_models_data.get("models", [])}

# 艉柱絞鏈軸心向量：dx = -15, dz = 53 => 歸一化
import math
hlen = math.sqrt(15**2 + 53**2)
ax = -15.0 / hlen
az = 53.0 / hlen

assembly_models_dict["船舵"] = {
    "name": "船舵",
    "source": "work",
    "file": "",
    "bytes": 0,
    "sha256": "",
    "work": RUDDER_WORK,
    "axes": "sculpt",
    "at": [0.0, 0.0, 0.0],
    "pivot": [95.0, 90.5, 2.0],
    "rotate": [0, 0, 0],
    "scale": [1.0, 1.0, 1.0],
    "mirror": "",
    "color": "",
    "enabled": True,
    "note": "炎羽號可動船舵（帶 hinge 鉸鏈旋轉 meta）",
    "persona": "kiara",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "meta": {
        "kind": "rudder",
        "turn_axis": "hinge",
        "max_deg": 35,
        "hinge_x": 95.0,
        "hinge_y": 90.5,
        "hinge_z": 2.0,
        "axis_x": round(ax, 4),
        "axis_y": 0.0,
        "axis_z": round(az, 4)
    }
}

# 船首大錨 (左右兩舷)
assembly_models_dict["anchor-S"] = {
    "name": "anchor-S",
    "source": "work",
    "file": "",
    "bytes": 0,
    "sha256": "",
    "work": "basecamp-frigate-constitution-01m-anchor",
    "axes": "sculpt",
    "at": [445.0, 116.0, 62.0],
    "pivot": [23.5, 16.5, 29.0],
    "rotate": [0, 0, 0],
    "scale": [1.0, 1.0, 1.0],
    "mirror": "",
    "color": "",
    "enabled": True,
    "note": "右舷船首鑄鐵大錨",
    "persona": "kiara",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "meta": {"kind": "anchor"}
}

assembly_models_dict["anchor-P"] = {
    "name": "anchor-P",
    "source": "work",
    "file": "",
    "bytes": 0,
    "sha256": "",
    "work": "basecamp-frigate-constitution-01m-anchor",
    "axes": "sculpt",
    "at": [445.0, 65.0, 62.0],
    "pivot": [23.5, 16.5, 29.0],
    "rotate": [0, 0, 0],
    "scale": [1.0, 1.0, 1.0],
    "mirror": "y",
    "color": "",
    "enabled": True,
    "note": "左舷船首鑄鐵大錨（mirror=y）",
    "persona": "kiara",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "meta": {"kind": "anchor"}
}

assembly_models_data["schema"] = 2
assembly_models_data["models"] = list(assembly_models_dict.values())
with open(assembly_models_fn, "w", encoding="utf-8") as f:
    json.dump(assembly_models_data, f, indent=2, ensure_ascii=False)
print("✓ Assembly 船舵與船首雙錨模型掛載完畢")


# ==========================================
# 3. 露天甲板：掛載羅經櫃、絞盤、交通小艇
# ==========================================
upper_deck_models_fn = os.path.join(WORK_DIR, UPPER_DECK_WORK, "models.json")
with open(upper_deck_models_fn, "r", encoding="utf-8") as f:
    upper_deck_models_data = json.load(f)

upper_models_dict = {m["name"]: m for m in upper_deck_models_data.get("models", [])}

# 羅經櫃 (binnacle): 在舵輪 (x=175) 正前方
upper_models_dict["binnacle"] = {
    "name": "binnacle",
    "source": "work",
    "file": "",
    "bytes": 0,
    "sha256": "",
    "work": "summit-night-falcon-01m-binnacle",
    "axes": "sculpt",
    "at": [180.5, 90.5, 78.0],
    "pivot": [9.0, 13.0, 0.0],
    "rotate": [0, 0, 0],
    "scale": [0.2, 0.2, 0.2],
    "mirror": "",
    "color": "",
    "enabled": True,
    "note": "後甲板航海羅經櫃（舵手視線正前方）",
    "persona": "kiara",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "meta": {"kind": "binnacle"}
}

# 立式絞盤 (capstan): 後甲板與主桅間
upper_models_dict["capstan"] = {
    "name": "capstan",
    "source": "work",
    "file": "",
    "bytes": 0,
    "sha256": "",
    "work": "basecamp-ember-01m-capstan",
    "axes": "sculpt",
    "at": [235.0, 90.5, 78.0],
    "pivot": [40.0, 40.0, 0.0],
    "rotate": [0, 0, 0],
    "scale": [0.163, 0.163, 0.163],
    "mirror": "",
    "color": "",
    "enabled": True,
    "note": "甲板主立式起錨絞盤（capstan）",
    "persona": "kiara",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "meta": {"kind": "capstan"}
}

# 交通小艇 (cutter): 腰部走道支架中央
upper_models_dict["boat-cutter"] = {
    "name": "boat-cutter",
    "source": "work",
    "file": "",
    "bytes": 0,
    "sha256": "",
    "work": "basecamp-frigate-constitution-01m-whaleboat",
    "axes": "sculpt",
    "at": [215.0, 90.5, 80.0],
    "pivot": [85.5, 18.5, 0.0],
    "rotate": [0, 0, 0],
    "scale": [0.5, 0.5, 0.5],
    "mirror": "",
    "color": "",
    "enabled": True,
    "note": "腰部甲板 28 ft 交通艇（cutter）",
    "persona": "kiara",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "meta": {"kind": "boat", "boat": "cutter", "length_m": 8.5}
}

upper_deck_models_data["schema"] = 2
upper_deck_models_data["models"] = list(upper_models_dict.values())
with open(upper_deck_models_fn, "w", encoding="utf-8") as f:
    json.dump(upper_deck_models_data, f, indent=2, ensure_ascii=False)
print("✓ 露天甲板 羅經櫃、絞盤、小艇模型掛載完畢")


# ==========================================
# 4. 組裝件 links.json 船體 meta 標註
# ==========================================
assembly_links_fn = os.path.join(WORK_DIR, ASSEMBLY_WORK, "links.json")
with open(assembly_links_fn, "r", encoding="utf-8") as f:
    assembly_links = json.load(f)

for l in assembly_links.get("links", []):
    if l["name"] == "船殼":
        l["meta"] = {
            "kind": "ship",
            "waterline_z": 38,
            "crew": 120
        }
        print("✓ 船殼 link 標註 waterline_z=38, crew=120, kind=ship")
        break

assembly_links["schema"] = 3
with open(assembly_links_fn, "w", encoding="utf-8") as f:
    json.dump(assembly_links, f, indent=2, ensure_ascii=False)


# ==========================================
# 5. 船尾鳳凰海軍旗（Ensign Flag）
# ==========================================
sails_fn = os.path.join(WORK_DIR, ASSEMBLY_WORK, "sails.json")
with open(sails_fn, "r", encoding="utf-8") as f:
    sails_data = json.load(f)

# 檢查是否已有名為 ensign 的旗幟
flag_exists = any(s["name"] == "ensign" for s in sails_data.get("sails", []))
if not flag_exists:
    # 船尾旗：懸掛於後甲板船尾旗桿頂部 (x=80, y=90.5, z=95)
    sails_data["sails"].append({
        "name": "ensign",
        "corners": [
            {"name": "head", "at": "80,90.5,95", "pin": True},
            {"name": "peak", "at": "60,90.5,95", "pin": False},
            {"name": "clew", "at": "60,90.5,85", "pin": False},
            {"name": "tack", "at": "80,90.5,85", "pin": True}
        ],
        "bind": [3],
        "color": "#d9483b",  # 鳳凰赤緋色旗幟
        "res": 0,
        "fullness": 1.08,
        "enabled": True,
        "note": "炎羽號艦尾鳳凰海軍旗（Ensign）",
        "persona": "kiara",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "meta": {
            "kind": "flag",
            "flag": "ensign"
        }
    })
    print("✓ 船尾鳳凰海軍旗（ensign）已配置！")

sails_data["schema"] = 3
with open(sails_fn, "w", encoding="utf-8") as f:
    json.dump(sails_data, f, indent=2, ensure_ascii=False)

print("🎉 夜隼號同款全部遊戲細節部件配置完畢！")
