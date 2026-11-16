"""Build two lateen rigs on the measured galley upperworks."""
import json
from pathlib import Path
import sys

import numpy as np

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from apply_upper import ASM, HULL, anchor, cli, component, coords, link

RIG = {
    "main": {"x": 248, "mast_top": 184, "peak": [88, 244], "fore": [329, 84], "clew": [109, 98],
             "shrouds": [234, 258], "tack": [347, 160, 21], "sheet": [86, 160, 21]},
    "fore": {"x": 393, "mast_top": 157, "peak": [339, 190], "fore": [477, 73], "clew": [355, 69],
             "shrouds": [378, 402], "tack": [452, 160, 17], "sheet": [324, 160, 21]},
}
SIZE = (560, 321, 280)


def mask(path, cells):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes("".join(f"{x},{y},{z},{c}\n" for (x,y,z), c in sorted(cells.items())).encode())


def geometry():
    result = {}
    for name, spec in RIG.items():
        x, top = spec["x"], spec["mast_top"]
        mast = {}
        for z in range(21, top + 1):
            radius = 2.4 - .95 * (z - 21) / (top - 21)
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx * dx + dy * dy <= radius * radius:
                        mast[x + dx, 160 + dy, z] = 104
        # Yard is baked in its raked rest pose and pivots on the mast, 0.35 m to port.
        ax, az = spec["peak"]
        bx, bz = spec["fore"]
        length = int(np.ceil(np.hypot(ax - bx, az - bz)))
        origin = [ax - 2, 155, bz - 2]
        peak = [2, 2, az - origin[2]]
        fore = [bx - origin[0], 2, 2]
        local_x = x - origin[0]
        local_z = round(az + (bz - az) * (x - ax) / (bx - ax)) - origin[2]
        pivot = [local_x + .5, 5.5, local_z + .5]
        yard = {}
        for point in np.linspace(peak, fore, length * 4):
            xx, yy, zz = (int(round(n)) for n in point)
            for dy in (0, 1):
                yard[xx, yy + dy, zz] = 104
        paths = [D / "masks" / "rig" / f"{name}-{part}.txt" for part in ("mast", "yard")]
        for path, cells in zip(paths, (mast, yard)):
            mask(path, cells)
        result[name] = dict(paths=paths, origin=origin, peak=peak, fore=fore, pivot=pivot,
                            at=[pivot[i] + origin[i] for i in range(3)],
                            yard_size=(fore[0] + 3, 7, peak[2] + 3), length_m=round(length / 10, 2))
    return result


def rope(name, start, end, group):
    cli("work", sub="rope", work=ASM, name=name, **{"from": start, "to": end},
        slack=1.03, thickness=.4, color="#8b7657", group=group, overwrite=1)


def entries(work, kind):
    path = D.parent.parent / work / (kind + ".json")
    return {entry["name"]: entry for entry in json.loads(path.read_text(encoding="utf-8"))[kind]} if path.exists() else {}


def ensure_anchor(work, name, point):
    actual = entries(work, "anchors").get(name)
    if actual is None:
        anchor(work, name, point)
    elif tuple(actual["at"]) != tuple(point):
        raise ValueError((work, name, actual["at"], point))


def apply():
    (D / "rig_dimensions.json").write_text(json.dumps(
        {"source": "N65 and IUAV Figs 7–10 support two lateen rigs. Heights, rake and attachment coordinates are reconstruction values.",
         "provenance": ["https://www.veniceboats.com/it-progetti-piani-navi-sottili-2.htm",
                        "https://air.iuav.it/bitstream/11578/295653/1/isprs-archives-XLIII-B2-2020-1371-2020.pdf"],
         "masts": RIG}, indent=2) + "\n")
    meta_rows = []
    for name, part in geometry().items():
        spec = RIG[name]
        mast = component("mast-" + name, "威尼斯 galea 桅 " + name, part["paths"][0], SIZE)
        yard = component("yard-" + name, "威尼斯 galea 拉丁帆桁 " + name, part["paths"][1], part["yard_size"])
        ensure_anchor(yard, "pivot", tuple(int(v) for v in part["pivot"]))
        for point in ("peak", "fore"):
            ensure_anchor(yard, point, part[point])
        ensure_anchor(mast, "hound", (spec["x"], 160, spec["mast_top"] - 8))
        mast_link = "mast-" + name
        model = "yard-" + name
        if model not in entries(mast, "models"):
            cli("work", sub="model", work=mast, name=model, source_work=yard,
            at=coords(part["at"]), pivot=coords(part["pivot"]), scale=1,
            meta=dict(kind="yard", mast=name, yard="gaff", rig="lateen", length_m=part["length_m"]))
        if mast_link not in entries(ASM, "links"):
            link(ASM, mast_link, mast, meta=dict(kind="mast", mast=name))
        m = "model:" + mast_link + "/" + model + "/"
        sail = name + "-lateen"
        clew = coords([spec["clew"][0], 158, spec["clew"][1]])
        if sail not in entries(ASM, "sails"):
            cli("work", sub="sail", work=ASM, name=sail, corners=m + "peak|" + m + "fore|" + clew,
            corner_names="peak|tack|clew", bind="0", free="clew", color="#e7d9b8", fullness=1.07)
        meta_rows.append(("sail", sail, dict(kind="sail", mast=name, sail="gaff")))
        for i, x in enumerate(spec["shrouds"]):
            for side, y in (("P", 125.5), ("S", 195.5)):
                name_rope = f"{name}-shroud-{side}{i+1}"
                rope(name_rope, mast_link + "/hound", coords([x + .5, y, 28]), "standing")
                meta_rows.append(("rope", name_rope, dict(kind="shroud")))
        tack, sheet, halyard = sail + ".tack", sail + ".sheet", sail + ".halyard"
        rope(tack, m + "fore", coords(spec["tack"]), "running")
        rope(sheet, "sail:" + sail + "/clew", coords(spec["sheet"]), "running")
        rope(halyard, mast_link + "/hound", coords(part["at"]), "running")
        for line, kind in ((tack, "tack"), (sheet, "sheet"), (halyard, "halyard")):
            meta_rows.append(("rope", line, dict(kind=kind, sail=sail)))
        print(name, "lateen rig installed", flush=True)
    meta_file = D / "galea_rig.tsv"
    meta_file.write_text("".join(f"{part}\t{name}\t{json.dumps(meta)}\n" for part, name, meta in meta_rows))
    cli("work", sub="meta", work=ASM, file=meta_file)
    print(cli("work", sub="ropecheck", work=ASM), flush=True)


if __name__ == "__main__":
    apply()
