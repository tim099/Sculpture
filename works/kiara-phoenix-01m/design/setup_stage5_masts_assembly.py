# -*- coding: utf-8 -*-
"""
炎羽號（kiara-phoenix-01m）：桅桿關聯與帆桁外部模型安裝
依據：Sculpture_Shipbuilding.md §5、§9
"""
import os
import json
import datetime

WORK_DIR = "D:/Unity/Valhalla/Sculpture/works"
MAIN_WORK = "kiara-phoenix-01m"
ASSEMBLY_WORK = "kiara-phoenix-01m-assembly"

# 1. 桅桿關聯加入 assembly links.json
assembly_links_fn = os.path.join(WORK_DIR, ASSEMBLY_WORK, "links.json")
with open(assembly_links_fn, "r", encoding="utf-8") as f:
    assembly_links = json.load(f)

existing_link_names = {l["name"] for l in assembly_links.get("links", [])}

masts_to_link = [
    {"name": "前桅", "work": "kiara-phoenix-01m-mast-fore", "note": "前桅桿子作品關聯"},
    {"name": "主桅", "work": "kiara-phoenix-01m-mast-main", "note": "主桅桿子作品關聯"},
    {"name": "後桅", "work": "kiara-phoenix-01m-mast-mizzen", "note": "後桅桿子作品關聯"},
    {"name": "艏斜桅", "work": "kiara-phoenix-01m-bowsprit", "note": "艏斜桅子作品關聯"}
]

for m in masts_to_link:
    if m["name"] not in existing_link_names:
        assembly_links["links"].append({
            "name": m["name"],
            "work": m["work"],
            "at": [0, 0, 0],
            "turn": 0,
            "mirror": "",
            "pivot": [576, 181, 400],
            "enabled": True,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "persona": "kiara",
            "note": m["note"]
        })
        print(f"[+] 關聯桅桿: {m['name']}")

with open(assembly_links_fn, "w", encoding="utf-8") as f:
    json.dump(assembly_links, f, indent=2, ensure_ascii=False)
print("✓ Assembly 桅桿關聯更新完畢")

# 2. 帆桁模型掛載進各桅桿的 models.json
plan_fn = os.path.join(WORK_DIR, MAIN_WORK, "design", "plan.json")
with open(plan_fn, "r", encoding="utf-8") as f:
    plan = json.load(f)

# 定義 8 根帆桁掛載參數
# pivot 在各自作品的格心，at 是在桅桿/全艦座標系裡的格心
mast_yards_map = {
    "kiara-phoenix-01m-mast-fore": [
        {
            "name": "yard-fore-course",
            "work": "kiara-phoenix-01m-yard-fore-course",
            "at": [140, 90.5, 130.5],
            "pivot": [10.5, 90.5, 20.5],
            "rotate": [0, 0, -18],
            "meta": {
                "kind": "yard", "mast": "fore", "yard": "course", "sail": "fore-course",
                "pivot_anchor": "pivot", "turn_axis": "z", "rotate_z_deg": -18,
                "length_ft": 72.0, "diameter_in": 16.0
            }
        },
        {
            "name": "yard-fore-topsail",
            "work": "kiara-phoenix-01m-yard-fore-topsail",
            "at": [140, 90.5, 195.5],
            "pivot": [10.5, 70.5, 15.5],
            "rotate": [0, 0, -20],
            "meta": {
                "kind": "yard", "mast": "fore", "yard": "topsail", "sail": "fore-topsail",
                "pivot_anchor": "pivot", "turn_axis": "z", "rotate_z_deg": -20,
                "length_ft": 56.0, "diameter_in": 12.0
            }
        },
        {
            "name": "yard-fore-topgallant",
            "work": "kiara-phoenix-01m-yard-fore-topgallant",
            "at": [140, 90.5, 255.5],
            "pivot": [10.5, 45.5, 15.5],
            "rotate": [0, 0, -22],
            "meta": {
                "kind": "yard", "mast": "fore", "yard": "topgallant", "sail": "fore-topgallant",
                "pivot_anchor": "pivot", "turn_axis": "z", "rotate_z_deg": -22,
                "length_ft": 36.0, "diameter_in": 9.0
            }
        }
    ],
    "kiara-phoenix-01m-mast-main": [
        {
            "name": "yard-main-course",
            "work": "kiara-phoenix-01m-yard-main-course",
            "at": [275, 90.5, 140.5],
            "pivot": [10.5, 105.5, 20.5],
            "rotate": [0, 0, -18],
            "meta": {
                "kind": "yard", "mast": "main", "yard": "course", "sail": "main-course",
                "pivot_anchor": "pivot", "turn_axis": "z", "rotate_z_deg": -18,
                "length_ft": 84.0, "diameter_in": 18.0
            }
        },
        {
            "name": "yard-main-topsail",
            "work": "kiara-phoenix-01m-yard-main-topsail",
            "at": [275, 90.5, 210.5],
            "pivot": [10.5, 80.5, 15.5],
            "rotate": [0, 0, -20],
            "meta": {
                "kind": "yard", "mast": "main", "yard": "topsail", "sail": "main-topsail",
                "pivot_anchor": "pivot", "turn_axis": "z", "rotate_z_deg": -20,
                "length_ft": 64.0, "diameter_in": 14.0
            }
        },
        {
            "name": "yard-main-topgallant",
            "work": "kiara-phoenix-01m-yard-main-topgallant",
            "at": [275, 90.5, 275.5],
            "pivot": [10.5, 50.5, 15.5],
            "rotate": [0, 0, -22],
            "meta": {
                "kind": "yard", "mast": "main", "yard": "topgallant", "sail": "main-topgallant",
                "pivot_anchor": "pivot", "turn_axis": "z", "rotate_z_deg": -22,
                "length_ft": 40.0, "diameter_in": 10.0
            }
        }
    ],
    "kiara-phoenix-01m-mast-mizzen": [
        {
            "name": "yard-mizzen-crossjack",
            "work": "kiara-phoenix-01m-yard-mizzen-crossjack",
            "at": [395, 90.5, 130.5],
            "pivot": [10.5, 70.5, 15.5],
            "rotate": [0, 0, -18],
            "meta": {
                "kind": "yard", "mast": "mizzen", "yard": "crossjack", "sail": "mizzen-crossjack",
                "pivot_anchor": "pivot", "turn_axis": "z", "rotate_z_deg": -18,
                "length_ft": 56.0, "diameter_in": 12.0
            }
        },
        {
            "name": "yard-mizzen-topsail",
            "work": "kiara-phoenix-01m-yard-mizzen-topsail",
            "at": [395, 90.5, 190.5],
            "pivot": [10.5, 55.5, 15.5],
            "rotate": [0, 0, -20],
            "meta": {
                "kind": "yard", "mast": "mizzen", "yard": "topsail", "sail": "mizzen-topsail",
                "pivot_anchor": "pivot", "turn_axis": "z", "rotate_z_deg": -20,
                "length_ft": 44.0, "diameter_in": 10.0
            }
        }
    ]
}

for mast_work, yards in mast_yards_map.items():
    models_fn = os.path.join(WORK_DIR, mast_work, "models.json")
    if os.path.exists(models_fn):
        with open(models_fn, "r", encoding="utf-8") as f:
            models_data = json.load(f)
    else:
        models_data = {"schema": 2, "models": []}
    
    models_dict = {m["name"]: m for m in models_data.get("models", [])}
    for yd in yards:
        model_entry = {
            "name": yd["name"],
            "source": "work",
            "file": "",
            "bytes": 0,
            "sha256": "",
            "work": yd["work"],
            "axes": "sculpt",
            "at": yd["at"],
            "pivot": yd["pivot"],
            "rotate": yd["rotate"],
            "scale": [1.0, 1.0, 1.0],
            "mirror": "",
            "color": "",
            "enabled": True,
            "note": f"炎羽號帆桁模型（繞 pivot 轉 {yd['rotate'][2]}°）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": yd["meta"]
        }
        models_dict[yd["name"]] = model_entry
        print(f"[+] 註冊帆桁模型: {mast_work} -> {yd['name']}")
    
    models_data["schema"] = 2
    models_data["models"] = list(models_dict.values())
    with open(models_fn, "w", encoding="utf-8") as f:
        json.dump(models_data, f, indent=2, ensure_ascii=False)

print("🎉 桅桿與帆桁模型註冊全部完成！")
