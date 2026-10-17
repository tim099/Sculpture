# -*- coding: utf-8 -*-
"""炎羽號 v3：舵頭接上船尾、舵索（造船規格 §9 rudder、§9.8.1；憲法號階段十七、二十七）。

量到的（2026-10-17）：舵（模型 at ＝ pivot ＋ 12 格 x）前緣 z 3 → 54 從 x 107 退到 92，船尾柱（|y−90| ≤ 2 最後面那格）z 54 在 x 93
⇒ 舵板貼著船尾柱、空 0..1 格；但舵頭停在 z 55，船尾柱往上一路後傾到 z 93（x 76），舵頭跟船尾之間沒有東西接著。
做法：舵頭往上長一根 3×3 的舵柱（色 136，z 58 一道鐵箍 36）：前緣 ＝ min(舵軸延長, 船尾柱 − 1)，離舵軸超過 1.25 格就停（z 56..60）
⇒ 舵頭頂在船尾的 counter 底下（helm port 的位置）；stock-top 改到舵柱頂。
舵索：共用舵輪元件的 drum-rope-a／b → 正下方甲板面（往下穿進甲板，同憲法號）。
用法：python -I -X utf8 fix_rudder.py | apply
"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "v2"))
from common import ASM, WORKS, senate, export_list, load, write_vox

TMP = os.path.join(HERE, "_tmp")
RUD = "kiara-phoenix-01m-rudder"
DX = 12                     # 模型 at − pivot（世界 ＝ 子作品 ＋ 12）
P = "persona=kiara"
Z0 = 55                     # 原本的舵頂（10-14 雕的舵板最上一層）


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    hull = load(os.path.join(TMP, "hull.txt"))
    occ = set((x, y, z) for x, y, z, c in hull)
    aft = collections.defaultdict(lambda: 999)
    for x, y, z, c in hull:
        if 88 <= y <= 92:
            aft[z] = min(aft[z], x)
    rud = export_list(RUD, os.path.join(TMP, "rudder.txt"))
    have = {(x, y, z): c for x, y, z, c in rud}
    front = {}
    for x, y, z, c in rud:
        if z <= Z0:                                         # 只看原本的舵板（重跑時舵柱已在，不能拿它當起點）
            front[z] = max(front.get(z, -1), x + DX)
    ztop = Z0
    slope = (front[ztop] - front[3]) / (ztop - 3)          # 舵前緣每升一格往後退多少
    add = []
    z = ztop + 1
    top = None
    while True:
        axis_f = front[ztop] + slope * (z - ztop)           # 舵前緣照舵軸的斜率延長
        f = min(int(round(axis_f)), aft[z] - 1)             # 不進船尾柱：貼著它（船尾柱後傾得比舵軸快）
        if axis_f - f > 1.25:                               # 離舵軸太遠 ⇒ 轉舵時會甩出去，停
            break
        for x in (f - 2, f - 1, f):
            for y in (89, 90, 91):
                c = 36 if z == 58 else 136
                assert (x, y, z) not in occ, (x, y, z)
                add.append((x - DX, y, z, c))
        top = (f - 1 - DX, 90, z)
        z += 1
    print(f"舵頭 z {ztop} → {top[2]}；加 {len(add)} 格；斜率 {slope:.3f}；stock-top（子作品座標）{top}")
    for zz in range(ztop - 1, top[2] + 2):
        print(f"  z {zz}: 舵前緣 {max([a[0] + DX for a in add if a[2] == zz] or [front.get(zz, '-')])}  船尾柱 {aft[zz]}")
    extra = [k for k in have if k[2] > Z0 and k not in {a[:3] for a in add}]
    print(f"  舵柱以外、z > {Z0} 的格：{len(extra)}")
    assert not extra and all(have.get(a[:3], a[3]) == a[3] for a in add)
    if not apply:
        return
    new = [a for a in add if a[:3] not in have]
    if new:
        f = write_vox(os.path.join(TMP, "rudder_stock.txt"), new)
        senate("op=stampvox", f"work={RUD}", P, "at=0,0,0", f"voxels={f}", f"expect_pixels={len(new)}", "share=0")
    senate("op=work", "sub=anchor", f"work={RUD}", P, "name=stock-top", f"at={top[0]},{top[1]},{top[2]}", "overwrite=1",
           "note=舵頭（v3：舵柱接到船尾柱下；遊戲在旁邊 8 格內找船尾）")
    # 舵索
    ropes = [("wheel-rope-a", "model:露天甲板/wheel/drum-rope-a", "131.3,89.2,79"),
             ("wheel-rope-b", "model:露天甲板/wheel/drum-rope-b", "136.7,91.8,78")]
    have_r = {r["name"]: (r["from"], r["to"]) for r in json.load(open(os.path.join(WORKS, ASM, "ropes.json"), encoding="utf-8"))["ropes"]}
    for nm, a, b in ropes:
        c = ["op=work", "sub=rope", f"work={ASM}", P, f"name={nm}", "slack=1", "color=#a08458", "thickness=0.35",
             "group=steering", "note=舵索：舵輪鼓 → 甲板面（往下穿進甲板，同憲法號階段二十七）"]
        if have_r.get(nm) != (a, b):
            c += [f"from={a}", f"to={b}"] + (["overwrite=1"] if nm in have_r else [])
        senate(*c)
        senate("op=work", "sub=meta", f"work={ASM}", P, "part=rope", f"name={nm}", "meta=" + json.dumps({"kind": "steering"}))
    print("done")


if __name__ == "__main__":
    main()
