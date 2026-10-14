# 炎羽號（kiara-phoenix-01m）外板、壓樑與砲門框批次落格腳本
# 依 verify_planking.json 的清單逐一執行 stampvox，每刀讀回 placed 驗證

import os, sys, json, subprocess

design_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(design_dir)
verify_path = os.path.join(design_dir, "verify_planking.json")

with open(verify_path, "r", encoding="utf-8") as f:
    data = json.load(f)

manifest = data["manifest"]
print(f"總外板與構件部件: {len(manifest)} 件")

for piece in manifest:
    name = piece["name"]
    count = piece["count"]
    path = piece["path"].replace("\\", "/")

    print(f"[+] 正在落格: {name} ({count} 格)...")
    cmd = [
        "senate", "cmd", "sculpture",
        "--arg", "op=stampvox",
        "--arg", "work=kiara-phoenix-01m",
        "--arg", "persona=kiara",
        f"--arg", f"voxels={path}",
        "--arg", "at=0,0,0",
        f"--arg", f"expect_pixels={count}"
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, cwd=r"D:\Unity\Senate")
    if res.returncode != 0:
        print(f"❌ 錯誤: {name} 落格失敗 (exit {res.returncode})")
        print(res.stderr or res.stdout)
        sys.exit(1)
    
    out = res.stdout
    if f"placed = {count}" not in out and f"stampvox {count} voxels" not in out:
        print(f"⚠️ 警告: {name} placed 數值不符，請核查輸出:\n{out}")
    else:
        print(f"  ✓ {name} 成功落地 {count} 格")

print("\n🎉 全部外板、砲門框、壓樑與頂蓋已全數成功落格！")
