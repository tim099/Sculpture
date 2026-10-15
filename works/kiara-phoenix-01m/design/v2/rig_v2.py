# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）步驟六：帆桁、帆、繩、錨、舵（全部經 CLI；取代 10-14 直接寫 json 的
setup_stage5_masts_assembly.py／setup_stage7_rigging_and_sails.py／setup_night_falcon_details.py 的那幾段）。

量到的（2026-10-15，桅的格子）：桅軸 前桅 x 405、主桅 275、後桅 155（y 90）。
  前桅：桅頂平台 z 192..196、桅頂橫桁 282..286、桅頂 361；主桅：207..211、302..306、382；後桅：167..171、桅頂 320。
舊的錯：前桅三根帆桁掛在 x 140（後桅的位置）、後桅兩根掛在 x 395（前桅的位置）；pivot 的 z 跟帆桁的 pivot 固定點差 5 格；
三角帆從 x 530 拉到 x 140；三條 stay 方向反了；course 的 sheet 長 0；topsail 以上沒有 sheet。
規則（造船規格 §5、§6、§7、§9.1）：
- 帆桁：pivot ＝ 帆桁子作品的 `pivot` 固定點的格心；掛在桅的前緣（帆桁後緣貼著桅前緣）；高度在桅頂平台／橫桁下面。
- 方帆：上緣（邊 0）釘在兩個 earing；course 的帆腳用 sheet 往後、tack 往前綁到舷牆上方；topsail 以上的帆腳 sheet 綁下一根帆桁同舷的 earing。
- 靜索：每根桅從桅頂往前下拉；三角帆的 luff 沿 fore-topmast-stay（拉直）。
用法：python -I -X utf8 rig_v2.py | apply
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASM, WORKS, senate, xf

MASTS = {"fore": ("前桅", "kiara-phoenix-01m-mast-fore"), "main": ("主桅", "kiara-phoenix-01m-mast-main"),
         "mizzen": ("後桅", "kiara-phoenix-01m-mast-mizzen")}
# 帆桁：(名字, 桅, 帆桁格的中心 x, z（格）, 轉角)；x ＝ 桅前緣 + 1 + 帆桁半厚
YARDS = [
    ("fore-course", "fore", 410.5, 186, -18), ("fore-topsail", "fore", 408.5, 276, -20), ("fore-topgallant", "fore", 408.5, 352, -22),
    ("main-course", "main", 281.5, 201, -18), ("main-topsail", "main", 279.5, 296, -20), ("main-topgallant", "main", 278.5, 372, -22),
    ("mizzen-crossjack", "mizzen", 159.5, 161, -18), ("mizzen-topsail", "mizzen", 158.5, 290, -20),
]
LOWER = {"fore-topsail": "fore-course", "fore-topgallant": "fore-topsail", "main-topsail": "main-course",
         "main-topgallant": "main-topsail", "mizzen-topsail": "mizzen-crossjack"}
# course 帆腳：舷牆上方的高度（各桅那一段的舷牆頂 + 12）與舷牆外緣
COURSE = {"fore-course": (92, 57, 123), "main-course": (88, 43, 137), "mizzen-crossjack": (99, 50, 130)}
YARD_KIND = {"course": "course", "topsail": "topsail", "topgallant": "topgallant", "crossjack": "crossjack"}
SAIL_KIND = {"course": "course", "crossjack": "course", "topsail": "topsail", "topgallant": "topgallant"}
STAY_C, SHEET_C = "#2b2620", "#a08458"


def yard_anchor(name):
    """讀帆桁子作品的固定點（引擎 sub=anchors 的讀數）。"""
    _, out = senate("op=work", "sub=anchors", f"work=kiara-phoenix-01m-yard-{name}")
    pts = {}
    for line in out.splitlines():
        if line.startswith("- `"):
            nm = line.split("`")[1]
            cell = line.split("@")[1].split(" ")[0]
            pts[nm] = tuple(int(v) for v in cell.split(","))
    return pts


def fmt(v):
    return ",".join(f"{a:g}" for a in v)


_rail = None


def rail(x, side):
    """舷牆頂：那一欄（x）那一舷最高的船殼格，取最外側那一格的正上方 ⇒ 繩端貼著實心（遊戲判浮空看端點 2 格內有沒有實心）。"""
    global _rail
    if _rail is None:
        from common import HULL, TMP, export_list
        _rail = {}
        for hx, hy, hz, c in export_list(HULL, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp", "hull_rail.txt")):
            s = "S" if hy > 90 else ("P" if hy < 90 else None)
            if s is None:
                continue
            k = (hx, s); cur = _rail.get(k)
            if cur is None or hz > cur[1] or (hz == cur[1] and (hy > cur[0] if s == "S" else hy < cur[0])):
                _rail[k] = (hy, hz)
    x = round(x)
    while (x, side) not in _rail:          # 超出船首／船尾 ⇒ 往船中找最近一欄有舷牆的
        x += -1 if x > 288 else 1
    hy, hz = _rail[(x, side)]
    return (x, hy, hz + 1)


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    cmds = []
    world = {}
    # 1. 帆桁
    for name, mast, cx, cz, rot in YARDS:
        a = yard_anchor(name)
        pv = a["pivot"]
        pivot = (pv[0] + 0.5, pv[1] + 0.5, pv[2] + 0.5)
        m = {"at": [cx, 90.5, cz + 0.5], "pivot": list(pivot), "rotate": [0, 0, rot], "scale": [1, 1, 1], "mirror": ""}
        for k in ("earing-P", "earing-S", "arm-P", "arm-S"):
            c = a[k]; world[(name, k)] = xf(m, (c[0] + 0.5, c[1] + 0.5, c[2] + 0.5))
        L = (a["arm-S"][1] - a["arm-P"][1] + 1) * 0.1
        kind = name.split("-")[1]
        meta = {"kind": "yard", "mast": mast, "yard": YARD_KIND[kind], "sail": name, "pivot_anchor": "pivot",
                "turn_axis": "z", "rotate_z_deg": rot, "length_ft": round(L / 0.3048, 1)}
        link, mwork = MASTS[mast]
        cmds.append(["op=work", "sub=model", f"work={mwork}", "persona=kiara", f"name=yard-{name}", f"at={fmt(m['at'])}",
                     f"pivot={fmt(pivot)}", f"rotate=0,0,{rot}", "meta=" + json.dumps(meta, ensure_ascii=False),
                     "note=TASK-0587 v2：掛在桅前緣、pivot ＝ 帆桁 pivot 固定點（design/v2/rig_v2.py）"])
    # 2. 舊繩全拿掉（帆角上的牽繩先拿，帆改角才不會留 broken）
    #    （只拿掉不在新清單裡的 ⇒ 重跑時同名的繩照原樣留著，檔案逐位元組不變）
    old = [r["name"] for r in json.load(open(f"{WORKS}/{ASM}/ropes.json", encoding="utf-8"))["ropes"]]
    unrope_at = len(cmds)
    # 3. 帆
    ropes = []
    for name, mast, cx, cz, rot in YARDS:
        link = MASTS[mast][0]
        hp, hs = f"model:{link}/yard-{name}/earing-P", f"model:{link}/yard-{name}/earing-S"
        eP, eS = world[(name, "earing-P")], world[(name, "earing-S")]
        if name in COURSE:
            z, ylo, yhi = COURSE[name]
            cs = (eS[0], min(eS[1], yhi + 2), z)
            cp = (eP[0], max(eP[1], ylo - 2), z)
            for side, c in (("S", cs), ("P", cp)):
                corner = f"sail:{name}/clew_{side.lower()}"
                ropes.append((f"{name}-sheet-{side}", corner, rail(c[0] - 30, side), 1.0, "sheet", name))
                ropes.append((f"{name}-tack-{side}", corner, rail(c[0] + 30, side), 1.0, "tack", name))
        else:
            lo = LOWER[name]
            lS, lP = world[(lo, "earing-S")], world[(lo, "earing-P")]
            cs = (lS[0], lS[1], lS[2] + 3); cp = (lP[0], lP[1], lP[2] + 3)
            lol = MASTS[[y for y in YARDS if y[0] == lo][0][1]][0]
            ropes.append((f"{name}-sheet-S", f"sail:{name}/clew_s", f"model:{lol}/yard-{lo}/earing-S", 1.0, "sheet", name))
            ropes.append((f"{name}-sheet-P", f"sail:{name}/clew_p", f"model:{lol}/yard-{lo}/earing-P", 1.0, "sheet", name))
        corners = f"{hp}|{hs}|{fmt(cs)}|{fmt(cp)}"
        kind = name.split("-")[1]
        cmds.append(["op=work", "sub=sail", f"work={ASM}", "persona=kiara", f"name={name}", f"corners={corners}",
                     "corner_names=head_p|head_s|clew_s|clew_p", "bind=0", "free=clew_s,clew_p", "fullness=1.05",
                     "color=#f2ead8", "overwrite=1"])
        cmds.append(["op=work", "sub=meta", f"work={ASM}", "persona=kiara", "part=sail", f"name={name}",
                     "meta=" + json.dumps({"kind": "sail", "mast": mast, "sail": SAIL_KIND[kind]})])
    # 4. 靜索（桅頂往前下）與三角帆
    stays = [
        ("fore-stay", (408, 90.5, 190), (500, 90.5, 81)),
        ("fore-topmast-stay", (407, 90.5, 280), (566, 90.5, 112)),
        ("main-stay", (279, 90.5, 205), (401, 90.5, 70)),
        ("main-topmast-stay", (278, 90.5, 300), (395, 90.5, 193)),
        ("mizzen-stay", (158, 90.5, 165), (270, 90.5, 100)),
    ]
    for nm, a, b in stays:
        ropes.append((nm, a, b, 1.0, "stay", None))
    A, B = (566, 90.5, 112), (407, 90.5, 280)          # fore-topmast-stay：艏斜桅端 → 前桅上桅頂
    P = lambda t: tuple(A[i] + t * (B[i] - A[i]) for i in range(3))
    tack, head = P(0.06), P(0.72)
    clew = (head[0] + 0.15 * (tack[0] - head[0]), 90.5, 96)
    cmds.append(["op=work", "sub=sail", f"work={ASM}", "persona=kiara", "name=jib", f"corners={fmt(tack)}|{fmt(head)}|{fmt(clew)}",
                 "corner_names=tack|head|clew", "bind=0", "free=clew", "fullness=1.06", "color=#f2ead8", "overwrite=1"])
    cmds.append(["op=work", "sub=meta", f"work={ASM}", "persona=kiara", "part=sail", "name=jib",
                 "meta=" + json.dumps({"kind": "sail", "mast": "bowsprit", "sail": "jib"})])
    for side in ("S", "P"):
        ropes.append((f"jib-sheet-{side}", "sail:jib/clew", rail(425, side), 1.0, "sheet", "jib"))
    keep = {r[0] for r in ropes}
    cmds[unrope_at:unrope_at] = [["op=work", "sub=unrope", f"work={ASM}", "persona=kiara", f"name={n}"] for n in old if n not in keep]
    # 5. 新繩（已經有、兩端一樣 ⇒ 不給 from／to：引擎看到 from／to 就當成換端點而擋下；兩端不一樣才 overwrite=1）
    have = {r["name"]: (r["from"], r["to"]) for r in json.load(open(f"{WORKS}/{ASM}/ropes.json", encoding="utf-8"))["ropes"]}
    for nm, a, b, slack, kind, sail in ropes:
        ends = [x if isinstance(x, str) else fmt(x) for x in (a, b)]
        group = "standing/stays" if kind == "stay" else "running/sheets"
        color, th = (STAY_C, 1.2) if kind == "stay" else (SHEET_C, 0.5)
        c = ["op=work", "sub=rope", f"work={ASM}", "persona=kiara", f"name={nm}",
             f"slack={slack:g}", f"color={color}", f"thickness={th:g}", f"group={group}"]
        if have.get(nm) != tuple(ends):
            c += [f"from={ends[0]}", f"to={ends[1]}"] + (["overwrite=1"] if nm in have else [])
        cmds.append(c)
        meta = {"kind": kind}
        if sail:
            meta["sail"] = sail
        cmds.append(["op=work", "sub=meta", f"work={ASM}", "persona=kiara", "part=rope", f"name={nm}",
                     "meta=" + json.dumps(meta)])
    # 6. 舵與錨（plan：舵的 pivot 放回鉸鏈；錨往舷外 5 格到零碰撞）
    # 舵：舵的格子前緣跟船尾柱平行、但整片在船尾柱後面 12..14 格 ⇒ 往前 12 格（每一層離船尾柱 0..1 格、零碰撞），鉸鏈 meta 跟著搬
    cmds.append(["op=work", "sub=model", f"work={ASM}", "persona=kiara", "name=船舵", "at=107,90.5,2",
                 "meta=" + json.dumps({"hinge_x": 107.0})])
    cmds.append(["op=work", "sub=model", f"work={ASM}", "persona=kiara", "name=anchor-S", "at=445,121,62"])
    cmds.append(["op=work", "sub=model", f"work={ASM}", "persona=kiara", "name=anchor-P", "at=445,60,62"])

    for (name, k), p in sorted(world.items()):
        if k.startswith("earing"):
            print(f" {name} {k}: {tuple(round(v, 1) for v in p)}")
    print(f"指令 {len(cmds)} 支；繩 {len(ropes)} 條")
    if not apply:
        return
    for c in cmds:
        senate(*c)
    print("done")


if __name__ == "__main__":
    main()
