# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）：三根桅的桅頂縱桁（trestletrees）一邊在 y 83、一邊在 96 —— 對 y 90.5 對稱、不是對中線那一格（y 90）。
補成兩舷對稱：每一格沒有鏡像（y ↔ 180−y）的，在鏡像位置補一格同色（只補、不拿）。
用法：python -I -X utf8 mirror_masts.py | apply
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import TMP, export_list, write_vox, senate

MASTS = ["kiara-phoenix-01m-mast-fore", "kiara-phoenix-01m-mast-main", "kiara-phoenix-01m-mast-mizzen"]


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    for w in MASTS:
        cells = {(x, y, z): c for x, y, z, c in export_list(w, os.path.join(TMP, f"mm_{w}.txt"))}
        add = [(x, 180 - y, z, c) for (x, y, z), c in cells.items() if (x, 180 - y, z) not in cells]
        print(f"{w}：補 {len(add)} 格")
        if apply and add:
            p = write_vox(os.path.join(TMP, f"mirror_{w}.txt"), add)
            senate("op=stampvox", f"work={w}", "persona=kiara", f"voxels={p}", "at=0,0,0", f"expect_pixels={len(add)}", "share=0")


if __name__ == "__main__":
    main()
