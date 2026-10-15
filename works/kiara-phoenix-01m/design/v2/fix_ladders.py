# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）步驟四：重做艙梯（造船規格 §9 kind=ladders、§9.3 通道）。

量到的（2026-10-15）：舊的三座梯子是照另一組甲板高度做的 ——
- aft：踏板 x 171..184、z 51..76，穿過後甲板（那裡沒開艙口，甲板面 74），頂端 head z 79 浮在甲板上 4 格；
- fore：踏板 x 371..384、z 51..76，艏樓甲板面 66（x ≥ 380），頂端比艏樓高 10 格；
- main：通到腰部（中間沒有甲板）的半空中，還有 24 格穿進主桅（x 275..278）；
- 踏板一塊一塊只靠斜角相接（6 連通斷開）⇒ 組裝件 39 個元件的來源。
新的：
- aft：主砲甲板 → 後甲板，11 階（每階往前 1、往上 2，2×6 格），後甲板開艙口；
- fore：主砲甲板 → 艏樓，8 階，艏樓開艙口；
  （主砲甲板在 x 170..185、265..285、370..385 開著通往船艙的艙口 ⇒ 梯腳放在艙口前緣之後）
- main：拿掉（主艙口照舊敞開）；
- 兩側各一條梯幫（y 86、94；踏板 87..93，對中線 y 90 對稱），沿斜面 6 連通，把每一階接起來，上端貼著上層甲板。
固定點（§9）：每座 foot／lo／hi／head，取「腳踩的那一格」。
用法：python -I fix_ladders.py | apply
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TMP, export_list, write_vox, senate

LAD = "kiara-phoenix-01m-ladders"
DECK_UP = "kiara-phoenix-01m-deck-upper"
STEP_C = 136      # 踏板（橡木）
RAIL_C = 132      # 梯幫
Y0, Y1 = 87, 93   # 踏板寬 7 格（對中線 y 90 對稱；梯幫 86／94）

# (名字, 第一階 x, 階數, 甲板面 z) —— 主砲甲板面 z 50
# 主砲甲板在 x 170..185、265..285、370..385 開著通往船艙的艙口 ⇒ 梯腳放在艙口前緣之後，爬進上層甲板底下再開艙口
LADDERS = [("aft", 188, 11, 73), ("fore", 388, 8, 66)]  # x 186／386 是主砲甲板艙口的圍欄（2 格高）


def ladder_cells(xs, n):
    cells = []
    for i in range(n):
        z = 51 + 2 * i
        for x in (xs + i, xs + i + 1):
            for y in range(Y0, Y1 + 1):
                cells.append((x, y, z, STEP_C))
        for y in (Y0 - 1, Y1 + 1):
            cells += [(xs + i, y, z, RAIL_C), (xs + i, y, z + 1, RAIL_C), (xs + i + 1, y, z + 1, RAIL_C)]
    # 去重（梯幫在相鄰兩階交界處會重複）
    seen, out = set(), []
    for c in cells:
        if c[:3] not in seen:
            seen.add(c[:3]); out.append(c)
    return out


def anchors(name, xs, n, deck_top):
    top_step_z = 51 + 2 * (n - 1)
    return {
        f"{name}.foot": (xs - 1, 90, 51),
        f"{name}.lo": (xs, 90, 52),
        f"{name}.hi": (xs + n - 1, 90, top_step_z + 1),
        f"{name}.head": (xs + n + 1, 90, deck_top + 1),
    }


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    old = export_list(LAD, os.path.join(TMP, "ladders_before.txt"))
    up = export_list(DECK_UP, os.path.join(TMP, "upper_before_ladders.txt"))
    new, anc = [], {}
    for name, xs, n, top in LADDERS:
        new += ladder_cells(xs, n)
        anc.update(anchors(name, xs, n, top))
    # 艙口：梯子正上方的露天甲板格（x xs..xs+n、y 87..94、z ≥ 55）
    hatch = []
    for name, xs, n, top in LADDERS:
        hatch += [(x, y, z, c) for x, y, z, c in up if xs <= x <= xs + n and Y0 - 1 <= y <= Y1 + 1 and z >= 55]
    # 檢查：head 那一格是空氣、底下是甲板
    upset = {(x, y, z) for x, y, z, c in up}
    for nm, (x, y, z) in anc.items():
        if nm.endswith(".head"):
            print(f"{nm} {x},{y},{z}：腳下 {'甲板' if (x, y, z - 1) in upset else '⚠ 空'}、本格 {'⚠ 實心' if (x, y, z) in upset else '空氣'}")
    print(f"舊梯 {len(old)} 格 → 新梯 {len(new)} 格；艙口拿掉 {len(hatch)} 格")
    if not apply:
        return
    p_old = write_vox(os.path.join(TMP, "ladders_carve.txt"), old)
    p_new = write_vox(os.path.join(TMP, "ladders_new.txt"), new)
    p_hatch = write_vox(os.path.join(TMP, "hatch_aft_carve.txt"), hatch)
    senate("op=carvevox", f"work={LAD}", "persona=kiara", f"voxels={p_old}", "at=0,0,0", f"expect_pixels={len(old)}", "share=0")
    senate("op=stampvox", f"work={LAD}", "persona=kiara", f"voxels={p_new}", "at=0,0,0", f"expect_pixels={len(new)}", "share=0")
    if hatch:
        senate("op=carvevox", f"work={DECK_UP}", "persona=kiara", f"voxels={p_hatch}", "at=0,0,0", f"expect_pixels={len(hatch)}", "share=0")
    for k in ("main.foot", "main.lo", "main.hi", "main.head"):
        senate("op=work", "sub=unanchor", f"work={LAD}", "persona=kiara", f"name={k}", check=False)
    for nm, (x, y, z) in anc.items():
        senate("op=work", "sub=anchor", f"work={LAD}", "persona=kiara", f"name={nm}", f"at={x},{y},{z}", "overwrite=1",
               "note=TASK-0587 v2 艙梯（design/v2/fix_ladders.py）")
    print("done")


if __name__ == "__main__":
    main()
