# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）步驟七：關聯重疊歸零（§10「link_overlap 0」）、拿掉碎片。

組裝件的關聯照清單順序先到的贏（船殼 → 主砲甲板 → 露天甲板 → 三根桅 → 艏斜桅 → 彈藥庫 → 梯子）。
處置：
- 桅穿過甲板：在**甲板**上開桅孔（拿掉甲板那幾格）—— 桅是完整的一根，甲板讓路；
- 其他（甲板伸進船殼、艏斜桅插進船首、桅腳踩進龍骨…）：拿掉**後到的那件**的格 —— 組起來的樣子不變（那幾格本來就被蓋掉）。
- 碎片：組裝件 6 連通、最大那塊以外的小塊（開砲門時留下的舷牆碎格）—— 拿掉它所屬那件的格。
用法：python -I -X utf8 fix_overlap.py | apply
"""
import sys, os, json
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASM, HULL, TMP, WORKS, export_list, write_vox, senate

ORDER = [("船殼", HULL), ("主砲甲板", "kiara-phoenix-01m-deck-gun"), ("露天甲板", "kiara-phoenix-01m-deck-upper"),
         ("前桅", "kiara-phoenix-01m-mast-fore"), ("主桅", "kiara-phoenix-01m-mast-main"), ("後桅", "kiara-phoenix-01m-mast-mizzen"),
         ("艏斜桅", "kiara-phoenix-01m-bowsprit"), ("彈藥庫-前", "kiara-phoenix-01m-magazine-fore"),
         ("彈藥庫-後", "kiara-phoenix-01m-magazine-aft"), ("梯子", "kiara-phoenix-01m-ladders")]
MASTS = {"前桅", "主桅", "後桅"}
DECKS = {"主砲甲板", "露天甲板"}


def link_offsets():
    d = json.load(open(f"{WORKS}/{ASM}/links.json", encoding="utf-8"))
    return {l["name"]: tuple(l["at"]) for l in d["links"]}


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    off = link_offsets()
    parts = {}
    for name, work in ORDER:
        ox, oy, oz = off[name]
        cells = export_list(work, os.path.join(TMP, f"ov_{work}.txt"))
        parts[name] = (work, (ox, oy, oz), {(x + ox, y + oy, z + oz): c for x, y, z, c in cells})
    owner = {}
    carve = {}
    pairs = {}
    for name, _ in ORDER:
        work, o, cells = parts[name]
        for k in cells:
            if k in owner:
                first = owner[k]
                pairs[(first, name)] = pairs.get((first, name), 0) + 1
                loser = first if (first in DECKS and name in MASTS) else name
                carve.setdefault(loser, set()).add(k)
                if loser == first:
                    owner[k] = name
            else:
                owner[k] = name
    for (a, b), n in sorted(pairs.items(), key=lambda t: -t[1]):
        print(f"重疊 {a} × {b}：{n} 格 ⇒ 拿掉 {a if (a in DECKS and b in MASTS) else b} 的")
    # 碎片（以處置後的組裝為準）
    solid = {k for k, v in owner.items()}
    seen, comps = set(), []
    for s in solid:
        if s in seen:
            continue
        q = deque([s]); seen.add(s); comp = [s]
        while q:
            x, y, z = q.popleft()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                n = (x + d[0], y + d[1], z + d[2])
                if n in solid and n not in seen:
                    seen.add(n); q.append(n); comp.append(n)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    print(f"元件 {len(comps)}：最大 {len(comps[0])}，其餘 {[len(c) for c in comps[1:]]}")
    for comp in comps[1:]:
        names = {owner[k] for k in comp}
        print(f"  碎片 {len(comp)} 格 @{min(comp)} 屬於 {names}")
        if len(comp) <= 50 and names == {"船殼"}:          # 只拿開砲門留下的舷牆碎格；甲板與桅的浮塊交給 fix_connect.py 接回去
            for k in comp:
                carve.setdefault(owner[k], set()).add(k)
    out = {}
    for name, ks in carve.items():
        work, (ox, oy, oz), cells = parts[name]
        lst = [(x - ox, y - oy, z - oz, cells[(x, y, z)]) for x, y, z in sorted(ks) if (x, y, z) in cells]
        out[work] = lst
        print(f"{name}（{work}）：拿掉 {len(lst)} 格")
    if not apply:
        return
    for work, lst in out.items():
        if not lst:
            continue
        p = write_vox(os.path.join(TMP, f"overlap_carve_{work}.txt"), lst)
        senate("op=carvevox", f"work={work}", "persona=kiara", f"voxels={p}", "at=0,0,0", f"expect_pixels={len(lst)}", "share=0")
    print("done")


if __name__ == "__main__":
    main()
