# -*- coding: utf-8 -*-
"""
炎羽號（kiara-phoenix-01m）階段六：火砲模型、退避檢測與五金裝配
依據：Sculpture_Shipbuilding.md §4、§8、§9
"""
import os
import json
import datetime

WORK_DIR = "D:/Unity/Valhalla/Sculpture/works"
MAIN_WORK = "kiara-phoenix-01m"
GUN_DECK_WORK = "kiara-phoenix-01m-deck-gun"
UPPER_DECK_WORK = "kiara-phoenix-01m-deck-upper"
ASSEMBLY_WORK = "kiara-phoenix-01m-assembly"

LONG18_SOURCE = "basecamp-frigate-constitution-01m-gun-long18"
CARRONADE32_SOURCE = "basecamp-frigate-constitution-01m-gun-carronade32"
WHEEL_SOURCE = "basecamp-frigate-constitution-01m-wheel"

# ==========================================
# 1. 主砲甲板：24 門 18 磅長砲模型安裝
# ==========================================
gun_deck_models_fn = os.path.join(WORK_DIR, GUN_DECK_WORK, "models.json")
if os.path.exists(gun_deck_models_fn):
    with open(gun_deck_models_fn, "r", encoding="utf-8") as f:
        gun_models_data = json.load(f)
else:
    gun_models_data = {"schema": 2, "models": []}

gun_models_dict = {m["name"]: m for m in gun_models_data.get("models", [])}

# 12 個砲門 station 的外板 S 舷外緣 y 座標
stations = [135, 160, 185, 210, 235, 260, 285, 310, 335, 360, 385, 410]
s_outer_y = {
    135: 123, 160: 128, 185: 132, 210: 135, 235: 136, 260: 137,
    285: 137, 310: 137, 335: 135, 360: 132, 385: 128, 410: 121
}

# long18: size_x=27, size_y=66, size_z=28, scale=0.5
# 縮放後：dx=13.5 (中線 6.75), dy=33, dz=14
# breech y=3.5, muzzle y=30.5
for i, st in enumerate(stations):
    idx = i + 1
    s_y = s_outer_y[st]
    p_y = 180 - s_y
    
    # S 舷砲：砲口朝 +y, muzzle 伸出船外約 5 格 (muzzle_y = s_y + 5)
    # muzzle_y = at_y + 30.5 => at_y = s_y + 5 - 30.5 = s_y - 25.5
    at_s_x = st - 6.75
    at_s_y = s_y - 25.5
    at_s_z = 50.0  # 落在主砲甲板面
    
    # P 舷砲：mirror=y
    # 在 mirror=y 變換下，muzzle_y_local = 33 - 30.5 = 2.5
    # 要求 muzzle_y_world = p_y - 5 (朝 -y 伸出 5 格)
    # muzzle_y_world = at_y + 2.5 => at_y = p_y - 5 - 2.5 = p_y - 7.5
    at_p_x = st - 6.75
    at_p_y = p_y - 7.5
    at_p_z = 50.0
    
    name_s = f"砲-S{idx:02d}"
    name_p = f"砲-P{idx:02d}"
    
    gun_models_dict[name_s] = {
        "name": name_s,
        "source": "work",
        "file": "",
        "bytes": 0,
        "sha256": "",
        "work": LONG18_SOURCE,
        "axes": "sculpt",
        "at": [at_s_x, at_s_y, at_s_z],
        "pivot": [0, 0, 0],
        "rotate": [0, 0, 0],
        "scale": [0.5, 0.5, 0.5],
        "mirror": "",
        "color": "",
        "enabled": True,
        "note": f"炎羽號主砲甲板 18 磅長砲（S 舷第 {idx} 門，Station {st}）",
        "persona": "kiara",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "meta": {"kind": "gun", "gun": "18l"}
    }
    
    gun_models_dict[name_p] = {
        "name": name_p,
        "source": "work",
        "file": "",
        "bytes": 0,
        "sha256": "",
        "work": LONG18_SOURCE,
        "axes": "sculpt",
        "at": [at_p_x, at_p_y, at_p_z],
        "pivot": [0, 0, 0],
        "rotate": [0, 0, 0],
        "scale": [0.5, 0.5, 0.5],
        "mirror": "y",
        "color": "",
        "enabled": True,
        "note": f"炎羽號主砲甲板 18 磅長砲（P 舷第 {idx} 門，Station {st}，mirror=y）",
        "persona": "kiara",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "meta": {"kind": "gun", "gun": "18l"}
    }
    print(f"[+] 主砲甲板火砲: {name_s} @ {at_s_x:.2f},{at_s_y:.2f},{at_s_z} & {name_p} @ {at_p_x:.2f},{at_p_y:.2f},{at_p_z}")

gun_models_data["schema"] = 2
gun_models_data["models"] = list(gun_models_dict.values())
with open(gun_deck_models_fn, "w", encoding="utf-8") as f:
    json.dump(gun_models_data, f, indent=2, ensure_ascii=False)
print(f"✓ 主砲甲板 24 門長砲模型已註冊（總計 {len(gun_models_data['models'])} 門）")


# ==========================================
# 2. 露天甲板：6 門卡隆砲、2 門追擊砲、1 座舵輪
# ==========================================
upper_deck_models_fn = os.path.join(WORK_DIR, UPPER_DECK_WORK, "models.json")
if os.path.exists(upper_deck_models_fn):
    with open(upper_deck_models_fn, "r", encoding="utf-8") as f:
        upper_models_data = json.load(f)
else:
    upper_models_data = {"schema": 2, "models": []}

upper_models_dict = {m["name"]: m for m in upper_models_data.get("models", [])}

# 6 門 32 磅卡隆砲 (carronade32: size_x=15, size_y=52, size_z=20, scale=0.5)
# dx=7.5, dy=26, dz=10. muzzle local y=51*0.5=25.5
carronade_stations = [
    {"st": 205, "z": 78.0, "s_y": 133},
    {"st": 230, "z": 78.0, "s_y": 135},
    {"st": 360, "z": 78.0, "s_y": 131}
]

for i, cs in enumerate(carronade_stations):
    idx = i + 1
    st = cs["st"]
    z = cs["z"]
    s_y = cs["s_y"]
    p_y = 180 - s_y
    
    # S 舷卡隆砲：muzzle y = s_y + 4 => at_y + 25.5 = s_y + 4 => at_y = s_y - 21.5
    at_s_x = st - 3.75
    at_s_y = s_y - 21.5
    
    # P 舷卡隆砲：mirror=y => muzzle y = 26 - 25.5 = 0.5 => at_y + 0.5 = p_y - 4 => at_y = p_y - 4.5
    at_p_x = st - 3.75
    at_p_y = p_y - 4.5
    
    name_s = f"carronade-S{idx:02d}"
    name_p = f"carronade-P{idx:02d}"
    
    upper_models_dict[name_s] = {
        "name": name_s,
        "source": "work",
        "file": "",
        "bytes": 0,
        "sha256": "",
        "work": CARRONADE32_SOURCE,
        "axes": "sculpt",
        "at": [at_s_x, at_s_y, z],
        "pivot": [0, 0, 0],
        "rotate": [0, 0, 0],
        "scale": [0.5, 0.5, 0.5],
        "mirror": "",
        "color": "",
        "enabled": True,
        "note": f"炎羽號露天甲板 32 磅卡隆砲（S 舷第 {idx} 門）",
        "persona": "kiara",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "meta": {"kind": "gun", "gun": "32c"}
    }
    
    upper_models_dict[name_p] = {
        "name": name_p,
        "source": "work",
        "file": "",
        "bytes": 0,
        "sha256": "",
        "work": CARRONADE32_SOURCE,
        "axes": "sculpt",
        "at": [at_p_x, at_p_y, z],
        "pivot": [0, 0, 0],
        "rotate": [0, 0, 0],
        "scale": [0.5, 0.5, 0.5],
        "mirror": "y",
        "color": "",
        "enabled": True,
        "note": f"炎羽號露天甲板 32 磅卡隆砲（P 舷第 {idx} 門，mirror=y）",
        "persona": "kiara",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "meta": {"kind": "gun", "gun": "32c"}
    }
    print(f"[+] 露天甲板卡隆砲: {name_s} & {name_p}")

# 2 門艦首追擊砲 (chase18-S & chase18-P)
# 在艏樓前端 x=415, z=78, 朝向艦首微偏角 -20°
upper_models_dict["chase18-S"] = {
    "name": "chase18-S",
    "source": "work",
    "file": "",
    "bytes": 0,
    "sha256": "",
    "work": LONG18_SOURCE,
    "axes": "sculpt",
    "at": [415.0, 108.0, 78.0],
    "pivot": [13.5, 38.5, 0],
    "rotate": [0, 0, -20],
    "scale": [0.5, 0.5, 0.5],
    "mirror": "",
    "color": "",
    "enabled": True,
    "note": "炎羽號艦首 18 磅追擊砲（S 舷，偏向艦首 20°）",
    "persona": "kiara",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "meta": {"kind": "gun", "gun": "18chase"}
}

upper_models_dict["chase18-P"] = {
    "name": "chase18-P",
    "source": "work",
    "file": "",
    "bytes": 0,
    "sha256": "",
    "work": LONG18_SOURCE,
    "axes": "sculpt",
    "at": [415.0, 72.0, 78.0],
    "pivot": [13.5, 38.5, 0],
    "rotate": [0, 0, -20],
    "scale": [0.5, 0.5, 0.5],
    "mirror": "y",
    "color": "",
    "enabled": True,
    "note": "炎羽號艦首 18 磅追擊砲（P 舷，mirror=y）",
    "persona": "kiara",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "meta": {"kind": "gun", "gun": "18chase"}
}
print("[+] 艦首追擊砲: chase18-S & chase18-P")

# 舵輪 (wheel)
# 後甲板 x=175, y=90.5, z=78
upper_models_dict["wheel"] = {
    "name": "wheel",
    "source": "work",
    "file": "",
    "bytes": 0,
    "sha256": "",
    "work": WHEEL_SOURCE,
    "axes": "sculpt",
    "at": [175.0, 90.5, 78.0],
    "pivot": [50.0, 52.0, 0.0],
    "rotate": [0, 0, 0],
    "scale": [0.2, 0.2, 0.2],
    "mirror": "",
    "color": "",
    "enabled": True,
    "note": "炎羽號後甲板舵輪（0.02m 子作品引用，scale 0.2）",
    "persona": "kiara",
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "meta": {"kind": "wheel"}
}
print("[+] 後甲板舵輪: wheel")

upper_models_data["schema"] = 2
upper_models_data["models"] = list(upper_models_dict.values())
with open(upper_deck_models_fn, "w", encoding="utf-8") as f:
    json.dump(upper_models_data, f, indent=2, ensure_ascii=False)
print(f"✓ 露天甲板模型已註冊（總計 {len(upper_models_data['models'])} 件）")


# ==========================================
# 3. 組裝件：彈藥庫關聯（Fore & Aft Magazines）
# ==========================================
assembly_links_fn = os.path.join(WORK_DIR, ASSEMBLY_WORK, "links.json")
with open(assembly_links_fn, "r", encoding="utf-8") as f:
    assembly_links = json.load(f)

existing_link_dict = {l["name"]: l for l in assembly_links.get("links", [])}

# 彈藥庫關聯
existing_link_dict["彈藥庫-前"] = {
    "name": "彈藥庫-前",
    "work": "basecamp-frigate-constitution-01m-magazine-fore",
    "at": [380, 75, 18],
    "turn": 0,
    "mirror": "",
    "pivot": [53, 101, 15],
    "enabled": True,
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "persona": "kiara",
    "note": "炎羽號前部彈藥庫關聯（水線下前艙底）",
    "meta": {
        "kind": "magazine",
        "pos": "fore",
        "powder_lb": 4000
    }
}

existing_link_dict["彈藥庫-後"] = {
    "name": "彈藥庫-後",
    "work": "basecamp-frigate-constitution-01m-magazine-aft",
    "at": [180, 75, 18],
    "turn": 0,
    "mirror": "",
    "pivot": [72, 62, 18],
    "enabled": True,
    "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "persona": "kiara",
    "note": "炎羽號後部主彈藥庫關聯（水線下後艙底）",
    "meta": {
        "kind": "magazine",
        "pos": "aft",
        "powder_lb": 6000
    }
}

assembly_links["schema"] = 3
assembly_links["links"] = list(existing_link_dict.values())
with open(assembly_links_fn, "w", encoding="utf-8") as f:
    json.dump(assembly_links, f, indent=2, ensure_ascii=False)
print("✓ Assembly 彈藥庫關聯註冊完畢（links schema 3）")

print("🎉 階段六：火砲、舵輪與彈藥庫裝配全部成功完成！")
