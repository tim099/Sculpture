# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）驗：重新匯出組裝件，讀作品現在的 models.json（不讀 plan），逐個模型量
碰撞（格心＋八角落在實心格的點數）、支撐（最底層的格底下是不是實心）、砲口在不在船殼外。
⚠ 自搭的尺：變換公式照 Sculpture.md §9.4.8 手寫在 common.xf；引擎自己的讀數是 sub=models 的外框，兩者要對得上。
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASM, HULL, TMP, WORKS, export_list, load
import plan_models as P

MUZZLE = {P.LONG18: (13, 61, 21), P.CARR: (7, 51, 19)}


def main():
    w = P.World()
    hull = export_list(HULL, os.path.join(TMP, "hull_verify.txt"))
    hy = {}
    for x, y, z, c in hull:
        lo, hi = hy.get((x, z), (999, -1)); hy[(x, z)] = (min(lo, y), max(hi, y))
    bad = 0
    for wk in (P.DECK_GUN, P.DECK_UP):
        d = json.load(open(f"{WORKS}/{wk}/models.json", encoding="utf-8"))
        for m in d["models"]:
            h = P.hits(m, w)
            s = P.src(m["work"]); zmin = min(v[2] for v in s)
            sup = sum(1 for x, y, z, c in s if z == zmin and (lambda p: (math.floor(p[0]), math.floor(p[1]), math.floor(p[2] - 0.3)) in w.solid)(P.xf(m, (x + .5, y + .5, z))))
            bot = sum(1 for v in s if v[2] == zmin)
            line = f" {wk[-8:]} {m['name']}: hits {len(h)}  支撐 {sup}/{bot}"
            if m["work"] in MUZZLE:
                a = MUZZLE[m["work"]]; q = P.xf(m, (a[0] + .5, a[1] + .5, a[2] + .5))
                lo, hi = hy.get((math.floor(q[0]), math.floor(q[2])), (None, None))
                out = lo is None or q[1] < lo or q[1] >= hi + 1
                line += f"  砲口 {tuple(round(t, 1) for t in q)} 船殼 y {lo}..{hi} {'在外' if out else '⚠ 在裡面'}"
                bad += (not out)
            bad += bool(h) + (sup == 0)
            print(line)
    print(f"⚠ 不合格 {bad} 項" if bad else "✓ 全部零碰撞、有支撐、砲口在船殼外")


if __name__ == "__main__":
    main()
