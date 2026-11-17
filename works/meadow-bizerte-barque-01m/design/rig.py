"""Fit the two lateen rigs and the vessel's working helm and anchor."""
import json
from math import hypot

import numpy as np

from apply_parts import ASSEMBLY, HULL, anchor, component, coords, entries, link, model, sculpt
from draft_hull import CENTER, DESIGN, PLAN, SIZE, X_RANGE, shell

WOOD, TRIM, IRON = 104, 141, 131
META_ROWS = []
RIG = {
    "main": dict(x=130, base=3, top=115, peak=(11,128), tack=(179,34),
                 clew=(33,64), set=3, ties=(111,133), on_deck=(153,90)),
    "fore": dict(x=181, base=21, top=81, peak=(82,114), tack=(211,40),
                 clew=(105,76), set=1, ties=(155,168), on_deck=(201,148)),
}


def write(name, cells):
    path = DESIGN / "masks" / f"{name}.txt"
    path.write_bytes("".join(f"{x},{y},{z},{c}\n" for (x, y, z), c in sorted(cells.items())).encode("ascii"))


def read(path):
    return {(x,y,z):c for x,y,z,c in (map(int, row.split(",")) for row in path.read_text().splitlines())}


def add_rope(name, start, end, kind, sail=None):
    if name not in entries(ASSEMBLY, "ropes"):
        sculpt("work", sub="rope", work=ASSEMBLY, name=name, **{"from":start, "to":end},
               slack=1.02, thickness=.24, color="#6f6250", group="standing" if kind == "shroud" else "running")
    data = {"kind":kind}
    if sail:
        data["sail"] = sail
    META_ROWS.append(("rope", name, data))


def ship_rig():
    stem, _ = shell()
    used = read(DESIGN / "hull.vox.txt")
    for name in ("hold","deck","aft-deck","hold-ladder","aft-ladder","ends","coaming"):
        used.update(read(DESIGN / "masks" / f"{name}.txt"))

    channels = {}
    points = {}
    for name, spec in RIG.items():
        for i, x in enumerate(spec["ties"], 1):
            for sign, side in ((-1,"P"),(1,"S")):
                width = int(np.flatnonzero(stem[x-X_RANGE.start,:,19]).max() - CENTER)
                y = CENTER + sign*(width+1)
                label = f"{name}-{side}{i}"
                points[label] = (x,y,19)
                for px in range(x-1,x+2):
                    for py in range(min(y,CENTER+sign*(width-1)), max(y,CENTER+sign*(width-1))+1):
                        if (px,py,18) not in used:
                            channels[px,py,18] = TRIM
                channels[x,y,19] = WOOD
    write("channels", channels)
    channels_work = component("channels", "支索木架")
    link(ASSEMBLY, "channels", channels_work, {})
    for key, at in points.items():
        anchor(channels_work, key, at)

    for name, spec in RIG.items():
        mast_x, base, top = (spec[k] for k in ("x","base","top"))
        mast_cells = {}
        for z in range(base, top+1):
            radius = 1.7 - .8*(z-base)/(top-base)
            for dx in range(-1,2):
                for dy in range(-1,2):
                    p = (mast_x+dx,CENTER+dy,z)
                    if p not in used and hypot(dx,dy) <= radius:
                        mast_cells[p] = TRIM if z in (base+1,top-7,top-6) else WOOD
        write(f"mast-{name}", mast_cells)
        mast = component(f"mast-{name}", f"{name} 桅")
        anchor(mast, "hound", (mast_x,CENTER,top-7))

        ax, az = spec["peak"]
        bx, bz = spec["tack"]
        length = hypot(bx-ax,bz-az)
        origin = (ax-1,CENTER-4,bz-1)
        peak = (1,1,az-bz+1)
        fore = (bx-ax+1,1,1)
        root_z = round(az + (bz-az)*(mast_x-ax)/(bx-ax))
        pivot = (mast_x-origin[0],4,root_z-origin[2])
        yard_cells = {}
        for xx, yy, zz in np.linspace(peak, fore, int(length*4)):
            for offset in (0,1):
                yard_cells[round(xx),round(yy)+offset,round(zz)] = WOOD
        write(f"yard-{name}", yard_cells)
        yard = component(f"yard-{name}", f"{name} 拉丁帆桁",
                         (fore[0]+3,7,peak[2]+3))
        for label, point in (("peak",peak),("fore",fore),("pivot",pivot)):
            anchor(yard, label, point)
        sail = f"{name}-lateen"
        model(mast, "yard", yard, (mast_x+.5,CENTER+.5,root_z+.5),
              tuple(v+.5 for v in pivot), dict(kind="yard", yard="gaff", rig="lateen",
                 mast=name, sail=sail, pivot_anchor="pivot", turn_axis="z", length_m=round(length/10,2)))
        mast_link = f"mast-{name}"
        link(ASSEMBLY, mast_link, mast, dict(kind="mast", mast=name))
        route = f"model:{mast_link}/yard/"
        cx, cz = spec["clew"]
        if sail not in entries(ASSEMBLY, "sails"):
            sculpt("work", sub="sail", work=ASSEMBLY, name=sail,
                   corners=f"{route}peak|{route}fore|{cx},{CENTER-5},{cz}",
                   corner_names="peak|tack|clew", bind=0, free="clew", color="#dfd0ad", fullness=1.045)
        META_ROWS.append(("sail", sail, dict(kind="sail", mast=name, sail="gaff", set=spec["set"])))
        for side in ("P","S"):
            for i in (1,2):
                add_rope(f"{name}-{side}{i}", f"channels/{name}-{side}{i}", f"{mast_link}/hound", "shroud")
            if f"{name}-ratlines-{side}.01" not in entries(ASSEMBLY, "ropes"):
                groups = json.loads((DESIGN.parent.parent / ASSEMBLY / "ropes.json").read_text(encoding="utf-8-sig"))
                if not any(item.get("name") == f"{name}-ratlines-{side}"
                           for item in groups.get("ratlines", [])):
                    sculpt("work", sub="ratlines", work=ASSEMBLY, name=f"{name}-ratlines-{side}",
                           rope_a=f"{name}-{side}1", rope_b=f"{name}-{side}2", step=4,
                           start=6, stop=14, min_span=4, thickness=.2, color="#75634b", group="ratlines")
        t, s = spec["on_deck"]
        add_rope(f"{sail}-tack", route + "fore", f"{t},{CENTER},{26 if name=='fore' else 16}", "tack", sail)
        add_rope(f"{sail}-sheet", f"sail:{sail}/clew", f"{s},{CENTER},16", "sheet", sail)
        add_rope(f"{sail}-halyard", f"{mast_link}/hound", route + "pivot", "halyard", sail)
        print(f"{name}: mast {top-base+1} cells, yard {length:.1f} cells", flush=True)

    if "merchant-pennant" not in entries(ASSEMBLY, "sails"):
        sculpt("work", sub="sail", work=ASSEMBLY, name="merchant-pennant",
               corners="mast-main/hound|112,36,106|130,36,101",
               corner_names="hoist|fly|foot", bind=0, free="fly", color="#8a3740", fullness=1.0)
    META_ROWS.append(("sail", "merchant-pennant", dict(kind="flag", flag="pennant")))
    path = DESIGN / "rig_meta.tsv"
    path.write_bytes("".join(f"{part}\t{name}\t{json.dumps(meta)}\n" for part,name,meta in META_ROWS).encode("utf-8"))
    sculpt("work", sub="meta", work=ASSEMBLY, file=path)
    print(sculpt("work", sub="ropecheck", work=ASSEMBLY), flush=True)


def helm_and_anchor():
    tiller = {}
    for z in range(5,26):
        x = 68 - round((z-5)*.52)
        for dx in range(-5 if z < 19 else -1,2):
            tiller[x+dx,CENTER,z] = WOOD if dx != 1 or z % 6 else IRON
    for x in range(58,78):
        tiller[x,CENTER,25] = TRIM
    write("rudder", tiller)
    part = component("rudder", "舵葉與舵柄")
    anchor(part, "stock-top", (58,CENTER,25))
    model(ASSEMBLY, "rudder", part, (0,0,0), (0,0,0),
          dict(kind="rudder", hinge_x=68.5, hinge_y=CENTER+.5, hinge_z=5.5,
               axis_x=-.467, axis_y=0, axis_z=.884, max_deg=28, turn_axis="hinge",
               spin="rudder", spin_k=28, spin_min=-28, spin_max=28, spin_lag=.3))
    ends = f"{HULL}-ends"
    for side, y in (("P",32),("S",40)):
        anchor(ends, f"hawse-{side}", (190,y,25))
        model(ends, f"anchor-{side}", "kotoko-fusta-01m-anchor-grapnel", (187.5,y+.5,25.5),
              (9.5,9.5,23.5), dict(kind="anchor", anchor="bower", hawse=f"ends/hawse-{side}"), scale=.70)
    sculpt("work", sub="meta", work=ASSEMBLY, part="link", name="hull",
           meta=dict(kind="ship", waterline_z=PLAN["dimensions"]["waterline_z"]["cells"]))
    print("Rudder and two grapnel anchors installed", flush=True)


if __name__ == "__main__":
    ship_rig()
    helm_and_anchor()
