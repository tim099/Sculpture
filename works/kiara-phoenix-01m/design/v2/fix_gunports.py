# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）步驟一：主砲甲板 24 個砲門往上移 5 格。

量到的（2026-10-15）：砲門開口 z 54..59（sill z53、lintel z60），每舷 12 個，x 132+25k 起 6 格寬；
甲板面 z 50 ⇒ 砲（long18、scale 0.5）放在 z 51，砲管 z 60..63 ⇒ 舊開口只到 59，砲管穿牆。
做法：每個砲門的那 6 欄
  - z 53..57 照左邊 6 格那一欄（沒有砲門的船牆）補回去（照外板位置對齊 y）；
  - 舊 sill（z53 那一排）搬到 z58、舊 lintel（z60）搬到 z65；z59..64 是新開口。
兩舷各做一次（P 舷用 y ↔ 180−y 對同一套算法）。
用法：python -I fix_gunports.py          只算、寫清單、印格數
      python -I fix_gunports.py apply    carvevox（帶色守門）＋ stampvox（expect_pixels）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HULL, TMP, export_list, write_vox, senate

PORTS = [132 + 25 * k for k in range(12)]
W = 6
SHIFT = 5
WIN = 7          # 外板往內看幾格當「船牆」


def side_cells(hull, side):
    """把該舷的格換成「S 舷座標」：P 舷 y → 180−y。回傳 {(x,y,z): color}。"""
    out = {}
    for x, y, z, c in hull:
        if side == "S" and y > 90:
            out[(x, y, z)] = c
        elif side == "P" and y < 90:
            out[(x, 180 - y, z)] = c
    return out


def plan(cells):
    outer = {}
    for (x, y, z) in cells:
        if y > outer.get((x, z), -1):
            outer[(x, z)] = y

    def oi(x, z):
        if 53 <= z <= 60:
            a, b = outer[(x, 52)], outer[(x, 61)]
            return a + (b - a) * (z - 52) / 9.0
        return outer[(x, z)]

    byx = {}
    for (cx, cy, cz), c in cells.items():
        byx.setdefault(cx, []).append((cx, cy, cz, c))

    carve, stamp = [], []
    for x0 in PORTS:
        for x in range(x0, x0 + W):
            # 1. 舊的：z 53..65 船牆窗內的格全部拿掉
            for (cx, cy, cz, c) in byx[x]:
                if 53 <= cz <= 65 and cy >= round(oi(x, cz)) - WIN:
                    carve.append((cx, cy, cz, c))
            # 2. z 53..57：照左邊 6 格那一欄補
            xr = x - 6
            for (cx, cy, cz, c) in byx[xr]:
                if 53 <= cz <= 57 and cy >= outer[(xr, cz)] - WIN:
                    d = round(oi(x, cz) - outer[(xr, cz)])
                    stamp.append((x, cy + d, cz, c))
            # 3. sill 搬上去、lintel 搬上去
            for (cx, cy, cz, c) in byx[x]:
                if cz == 53 and cy >= round(oi(x, 53)) - WIN:
                    d = round(oi(x, 53 + SHIFT) - oi(x, 53))
                    stamp.append((x, cy + d, 53 + SHIFT, c))
                if cx == x and cz == 60 and cy >= round(oi(x, 60)) - WIN:
                    d = round(oi(x, 60 + SHIFT) - oi(x, 60))
                    stamp.append((x, cy + d, 60 + SHIFT, c))
    return carve, stamp


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    hull = export_list(HULL, os.path.join(TMP, "hull_before_ports.txt"))
    all_carve, all_stamp = [], []
    for side in ("S", "P"):
        cells = side_cells(hull, side)
        carve, stamp = plan(cells)
        if side == "P":
            carve = [(x, 180 - y, z, c) for x, y, z, c in carve]
            stamp = [(x, 180 - y, z, c) for x, y, z, c in stamp]
        print(f"{side}: 拿掉 {len(carve)} 格、放 {len(stamp)} 格")
        all_carve += carve
        all_stamp += stamp
    # 同一格不能放兩次
    keys = [(x, y, z) for x, y, z, c in all_stamp]
    assert len(keys) == len(set(keys)), "stamp 有重複格"
    cpath = write_vox(os.path.join(TMP, "ports_carve.txt"), all_carve)
    spath = write_vox(os.path.join(TMP, "ports_stamp.txt"), all_stamp)
    print(f"清單：{cpath}（{len(all_carve)}）／{spath}（{len(all_stamp)}）")
    if not apply:
        return
    senate("op=carvevox", f"work={HULL}", "persona=kiara", f"voxels={cpath}", "at=0,0,0",
           f"expect_pixels={len(all_carve)}", "share=0")
    senate("op=stampvox", f"work={HULL}", "persona=kiara", f"voxels={spath}", "at=0,0,0",
           f"expect_pixels={len(all_stamp)}", "share=0")
    print("✓ 砲門已上移")


if __name__ == "__main__":
    main()
