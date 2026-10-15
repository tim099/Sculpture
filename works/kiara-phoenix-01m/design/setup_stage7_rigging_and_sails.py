# -*- coding: utf-8 -*-
import sys as _sys; _sys.exit("⛔ 這支直接寫 links／models／ropes／sails.json、繞過引擎檢查；已由 design/v2/ 取代（TASK-0587，2026-10-15）。要改請改 v2 的產生程式。")
"""
炎羽號（kiara-phoenix-01m）階段七：索具（Stays/Sheets）與帆（Sails）布料模擬
依據：Sculpture_Shipbuilding.md §6、§7、§9、§9.1
"""
import os
import json
import datetime

WORK_DIR = "D:/Unity/Valhalla/Sculpture/works"
ASSEMBLY_WORK = "kiara-phoenix-01m-assembly"

# ==========================================
# 1. 帆（Sails）定義與風向配置
# ==========================================
sails_fn = os.path.join(WORK_DIR, ASSEMBLY_WORK, "sails.json")

# 預設風速 4.5, -1.5, 0 (迎風航行)，模擬 3 秒
sails_data = {
    "schema": 3,
    "wind": [4.5, -1.5, 0.0],
    "sail_seconds": 3.0,
    "sails": [
        # --- 前桅 (Fore Mast) ---
        {
            "name": "fore-course",
            "corners": [
                {"name": "head_p", "at": "model:前桅/yard-fore-course/earing-P", "pin": True},
                {"name": "head_s", "at": "model:前桅/yard-fore-course/earing-S", "pin": True},
                {"name": "clew_s", "at": "140,150,70", "pin": False},
                {"name": "clew_p", "at": "140,30,70", "pin": False}
            ],
            "bind": [0],
            "color": "#f2ead8",
            "res": 0,
            "fullness": 1.05,
            "enabled": True,
            "note": "前桅下帆（Fore Course）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sail", "mast": "fore", "sail": "course"}
        },
        {
            "name": "fore-topsail",
            "corners": [
                {"name": "head_p", "at": "model:前桅/yard-fore-topsail/earing-P", "pin": True},
                {"name": "head_s", "at": "model:前桅/yard-fore-topsail/earing-S", "pin": True},
                {"name": "clew_s", "at": "140,155,132", "pin": False},
                {"name": "clew_p", "at": "140,25,132", "pin": False}
            ],
            "bind": [0],
            "color": "#f2ead8",
            "res": 0,
            "fullness": 1.05,
            "enabled": True,
            "note": "前桅上帆（Fore Topsail）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sail", "mast": "fore", "sail": "topsail"}
        },
        {
            "name": "fore-topgallant",
            "corners": [
                {"name": "head_p", "at": "model:前桅/yard-fore-topgallant/earing-P", "pin": True},
                {"name": "head_s", "at": "model:前桅/yard-fore-topgallant/earing-S", "pin": True},
                {"name": "clew_s", "at": "140,135,196", "pin": False},
                {"name": "clew_p", "at": "140,45,196", "pin": False}
            ],
            "bind": [0],
            "color": "#f2ead8",
            "res": 0,
            "fullness": 1.05,
            "enabled": True,
            "note": "前桅頂帆（Fore Topgallant）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sail", "mast": "fore", "sail": "topgallant"}
        },

        # --- 主桅 (Main Mast) ---
        {
            "name": "main-course",
            "corners": [
                {"name": "head_p", "at": "model:主桅/yard-main-course/earing-P", "pin": True},
                {"name": "head_s", "at": "model:主桅/yard-main-course/earing-S", "pin": True},
                {"name": "clew_s", "at": "275,160,70", "pin": False},
                {"name": "clew_p", "at": "275,20,70", "pin": False}
            ],
            "bind": [0],
            "color": "#f2ead8",
            "res": 0,
            "fullness": 1.05,
            "enabled": True,
            "note": "主桅下帆（Main Course）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sail", "mast": "main", "sail": "course"}
        },
        {
            "name": "main-topsail",
            "corners": [
                {"name": "head_p", "at": "model:主桅/yard-main-topsail/earing-P", "pin": True},
                {"name": "head_s", "at": "model:主桅/yard-main-topsail/earing-S", "pin": True},
                {"name": "clew_s", "at": "275,165,142", "pin": False},
                {"name": "clew_p", "at": "275,15,142", "pin": False}
            ],
            "bind": [0],
            "color": "#f2ead8",
            "res": 0,
            "fullness": 1.05,
            "enabled": True,
            "note": "主桅上帆（Main Topsail）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sail", "mast": "main", "sail": "topsail"}
        },
        {
            "name": "main-topgallant",
            "corners": [
                {"name": "head_p", "at": "model:主桅/yard-main-topgallant/earing-P", "pin": True},
                {"name": "head_s", "at": "model:主桅/yard-main-topgallant/earing-S", "pin": True},
                {"name": "clew_s", "at": "275,140,212", "pin": False},
                {"name": "clew_p", "at": "275,40,212", "pin": False}
            ],
            "bind": [0],
            "color": "#f2ead8",
            "res": 0,
            "fullness": 1.05,
            "enabled": True,
            "note": "主桅頂帆（Main Topgallant）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sail", "mast": "main", "sail": "topgallant"}
        },

        # --- 後桅 (Mizzen Mast) ---
        {
            "name": "mizzen-crossjack",
            "corners": [
                {"name": "head_p", "at": "model:後桅/yard-mizzen-crossjack/earing-P", "pin": True},
                {"name": "head_s", "at": "model:後桅/yard-mizzen-crossjack/earing-S", "pin": True},
                {"name": "clew_s", "at": "395,145,78", "pin": False},
                {"name": "clew_p", "at": "395,35,78", "pin": False}
            ],
            "bind": [0],
            "color": "#f2ead8",
            "res": 0,
            "fullness": 1.05,
            "enabled": True,
            "note": "後桅橫帆（Mizzen Crossjack）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sail", "mast": "mizzen", "sail": "course"}
        },
        {
            "name": "mizzen-topsail",
            "corners": [
                {"name": "head_p", "at": "model:後桅/yard-mizzen-topsail/earing-P", "pin": True},
                {"name": "head_s", "at": "model:後桅/yard-mizzen-topsail/earing-S", "pin": True},
                {"name": "clew_s", "at": "395,150,132", "pin": False},
                {"name": "clew_p", "at": "395,30,132", "pin": False}
            ],
            "bind": [0],
            "color": "#f2ead8",
            "res": 0,
            "fullness": 1.05,
            "enabled": True,
            "note": "後桅上帆（Mizzen Topsail）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sail", "mast": "mizzen", "sail": "topsail"}
        },

        # --- 艏斜桅三角帆 (Jib) ---
        {
            "name": "jib",
            "corners": [
                {"name": "tack", "at": "530,90.5,95", "pin": True},
                {"name": "head", "at": "140,90.5,210", "pin": True},
                {"name": "clew", "at": "340,90.5,95", "pin": False}
            ],
            "bind": [0],
            "color": "#f2ead8",
            "res": 0,
            "fullness": 1.06,
            "enabled": True,
            "note": "前三角帆（Jib，luff 沿 stay）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sail", "mast": "bowsprit", "sail": "jib"}
        }
    ]
}

with open(sails_fn, "w", encoding="utf-8") as f:
    json.dump(sails_data, f, indent=2, ensure_ascii=False)
print(f"✓ 帆（Sails）已註冊（9 面帆，帶完整 meta）")


# ==========================================
# 2. 繩索（Ropes）：靜索與牽引繩
# ==========================================
ropes_fn = os.path.join(WORK_DIR, ASSEMBLY_WORK, "ropes.json")

ropes_data = {
    "schema": 3,
    "ropes": [
        # --- 靜索 (Stays) ---
        {
            "name": "fore-stay",
            "from": "480,90.5,80",
            "to": "140,90.5,160",
            "color": "#2b2620",
            "thickness": 1.2,
            "slack": 1.0006,
            "enabled": True,
            "group": "standing/stays",
            "note": "前桅前支索（Fore Stay）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "stay"}
        },
        {
            "name": "main-stay",
            "from": "145,90.5,75",
            "to": "275,90.5,170",
            "color": "#2b2620",
            "thickness": 1.2,
            "slack": 1.0006,
            "enabled": True,
            "group": "standing/stays",
            "note": "主桅前支索（Main Stay）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "stay"}
        },
        {
            "name": "mizzen-stay",
            "from": "280,90.5,75",
            "to": "395,90.5,160",
            "color": "#2b2620",
            "thickness": 1.2,
            "slack": 1.0006,
            "enabled": True,
            "group": "standing/stays",
            "note": "後桅前支索（Mizzen Stay）",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "stay"}
        },

        # --- 帆腳索 (Sheets: 牽引各帆的 free clew 角) ---
        {
            "name": "fore-course-sheet-P",
            "from": "sail:fore-course/clew_p",
            "to": "140,30,70",
            "color": "#a08458",
            "thickness": 0.5,
            "slack": 0.85,
            "enabled": True,
            "group": "running/sheets",
            "note": "fore-course 左舷帆腳索",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sheet", "sail": "fore-course"}
        },
        {
            "name": "fore-course-sheet-S",
            "from": "sail:fore-course/clew_s",
            "to": "140,150,70",
            "color": "#a08458",
            "thickness": 0.5,
            "slack": 0.85,
            "enabled": True,
            "group": "running/sheets",
            "note": "fore-course 右舷帆腳索",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sheet", "sail": "fore-course"}
        },
        {
            "name": "main-course-sheet-P",
            "from": "sail:main-course/clew_p",
            "to": "275,20,70",
            "color": "#a08458",
            "thickness": 0.5,
            "slack": 0.85,
            "enabled": True,
            "group": "running/sheets",
            "note": "main-course 左舷帆腳索",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sheet", "sail": "main-course"}
        },
        {
            "name": "main-course-sheet-S",
            "from": "sail:main-course/clew_s",
            "to": "275,160,70",
            "color": "#a08458",
            "thickness": 0.5,
            "slack": 0.85,
            "enabled": True,
            "group": "running/sheets",
            "note": "main-course 右舷帆腳索",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sheet", "sail": "main-course"}
        },
        {
            "name": "mizzen-crossjack-sheet-P",
            "from": "sail:mizzen-crossjack/clew_p",
            "to": "395,35,78",
            "color": "#a08458",
            "thickness": 0.5,
            "slack": 0.85,
            "enabled": True,
            "group": "running/sheets",
            "note": "mizzen-crossjack 左舷帆腳索",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sheet", "sail": "mizzen-crossjack"}
        },
        {
            "name": "mizzen-crossjack-sheet-S",
            "from": "sail:mizzen-crossjack/clew_s",
            "to": "395,145,78",
            "color": "#a08458",
            "thickness": 0.5,
            "slack": 0.85,
            "enabled": True,
            "group": "running/sheets",
            "note": "mizzen-crossjack 右舷帆腳索",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sheet", "sail": "mizzen-crossjack"}
        },
        {
            "name": "jib-sheet",
            "from": "sail:jib/clew",
            "to": "340,90.5,78",
            "color": "#a08458",
            "thickness": 0.5,
            "slack": 0.85,
            "enabled": True,
            "group": "running/sheets",
            "note": "jib 前三角帆腳索",
            "persona": "kiara",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "meta": {"kind": "sheet", "sail": "jib"}
        }
    ]
}

with open(ropes_fn, "w", encoding="utf-8") as f:
    json.dump(ropes_data, f, indent=2, ensure_ascii=False)
print(f"✓ 繩索（Ropes）已註冊（10 條索具，帶完整 meta）")

print("🎉 階段七：索具與帆布裝配完成！")
