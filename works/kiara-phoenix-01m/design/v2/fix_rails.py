# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）步驟三：舷牆頂蓋收窄。

量到的（2026-10-15）：
- 船殼最上一層的頂蓋（色 104）每一個 x 都從 y 110（P 舷 70）鋪到外板，最寬 25 格（2.5 m）——
  一片架在甲板邊上的屋簷：卡隆砲放不進後甲板、腰部的走道被它蓋住。⇒ 只留靠外板的 4 格。
（舷側走道的橫樑頂到長砲那幾格不在這裡處理：走道順著舷弧往船頭爬高，整條搬會撞到自己 ——
 改在 plan_models.py 照每門砲實際碰到的格挖缺口。）
用法：python -I fix_rails.py          只算、印格數
      python -I fix_rails.py apply    carvevox（帶色守門）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HULL, TMP, export_list, write_vox, senate

CAP = 104
KEEP = 4


def cap_trim(hull):
    top = {}
    for x, y, z, c in hull:
        k = (x, y > 90)
        if y != 90 and z > top.get(k, -1):
            top[k] = z
    carve = []
    for side in (True, False):
        rows = {}
        for x, y, z, c in hull:
            if y != 90 and (y > 90) == side and z == top.get((x, side)) and c == CAP:
                rows.setdefault(x, []).append((x, y, z, c))
        for x, cells in rows.items():
            if side:
                outer = max(c[1] for c in cells)
                carve += [c for c in cells if c[1] <= outer - KEEP]
            else:
                outer = min(c[1] for c in cells)
                carve += [c for c in cells if c[1] >= outer + KEEP]
    return carve


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    hull = export_list(HULL, os.path.join(TMP, "hull_before_rails.txt"))
    carve = cap_trim(hull)
    s = sum(1 for c in carve if c[1] > 90); p = len(carve) - s
    print(f"頂蓋收窄：S {s}、P {p} 格")
    path = write_vox(os.path.join(TMP, "cap_carve.txt"), carve)
    if not apply:
        return
    senate("op=carvevox", f"work={HULL}", "persona=kiara", f"voxels={path}", "at=0,0,0",
           f"expect_pixels={len(carve)}", "share=0")
    print("done")


if __name__ == "__main__":
    main()
