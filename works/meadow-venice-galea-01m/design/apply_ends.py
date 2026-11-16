"""Fit out the galley's bow, stern and flag on the 0.1 m assembly grid."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

from apply_rig import entries, ensure_anchor, mask, rope
from apply_upper import ASM, HULL, cli, component, link
from verify_assembly import read

D = Path(__file__).resolve().parent
WOOD, TRIM, RED, GOLD = 104, 141, 128, 208
CENTER = 160
SIZE = (560, 321, 90)


def make_geometry():
    hull = read(D / "masks/hull/hull_01.vox.txt")
    occupied = hull | read(D / "masks/upper/deck.txt")
    bow, stern = {}, {}
    outlines = {}
    for x, y, z in hull:
        if y != CENTER:
            outlines[x] = max(outlines.get(x, 0), abs(y - CENTER))
    # Low forecastle and narrowing timber spur, with access from the center gangway.
    for x in range(433, 474):
        w = max(1, outlines[x] - 1)
        floor = max(20, 23 - (465 - x) // 7)
        for dy in range(-w, w + 1):
            bow[x, CENTER + dy, floor] = TRIM
            if abs(dy) == w:
                for z in range(floor + 1, floor + 5):
                    bow[x, CENTER + dy, z] = RED if z < floor + 4 else GOLD
    for x in range(467, 514):
        w = max(1, 4 - (x - 467) // 13)
        bottom = 22 + max(0, (x - 483) // 15)
        top = 27 + max(0, (x - 467) // 10)
        for dy in range(-w, w + 1):
            for z in range(bottom, top + 1):
                bow[x, CENTER + dy, z] = GOLD if z == top else WOOD if z < top - 2 else RED
    # A stepped aft platform, open-sided canopy and a centered flagstaff socket.
    for x in range(39, 94):
        w = max(1, outlines[x] - 1)
        floor = 29 - min(8, (x - 39) // 6)
        for dy in range(-w, w + 1):
            stern[x, CENTER + dy, floor] = TRIM
            if abs(dy) == w or x == 39:
                for z in range(floor + 1, floor + 6):
                    stern[x, CENTER + dy, z] = RED if z < floor + 5 else GOLD
    for x in range(50, 84):
        for dy in range(-11, 12):
            z = 49 - abs(dy) // 3 - max(0, abs(x - 66) - 12) // 3
            edge = abs(dy) == 11 or x in (50, 83)
            stern[x, CENTER + dy, z - 1] = WOOD
            stern[x, CENTER + dy, z] = GOLD if edge else RED
    for x in (52, 65, 81):
        for dy in (-10, 10):
            for z in range(29 - (x - 39) // 6, 46):
                stern[x, CENTER + dy, z] = WOOD
    for z in range(29, 72):
        x = 43 - (z - 29) // 12
        stern[x, CENTER, z] = GOLD if z == 71 else WOOD
    for x, z in ((42, 40), (41, 52), (40, 64)):
        stern[x, CENTER, z] = WOOD
    for z in range(29, 35):
        stern[39, CENTER, z] = WOOD
    out = {"bow": {p: c for p, c in bow.items() if p not in occupied},
           "stern": {p: c for p, c in stern.items() if p not in occupied}}
    return out


def ensign_texture(path):
    """Paint a simplified red and gold St Mark ensign at game texture size."""
    image = Image.new("RGBA", (112, 44))
    draw = ImageDraw.Draw(image)
    red, gold, pale = "#992522", "#dda54f", "#efc669"
    draw.rectangle((0, 0, 73, 43), fill=red)
    for y in range(0, 42, 7):
        draw.polygon([(70, y), (111, y), (108, y + 4), (70, y + 4)], fill=red)
        draw.line((73, y + 2, 107, y + 2), fill=gold)
    draw.rectangle((2, 2, 71, 41), outline=gold)
    draw.rectangle((7, 6, 66, 37), outline=gold)
    draw.line([(20, 32), (28, 32), (30, 26), (53, 26), (57, 29), (53, 32), (46, 33)], fill=gold, width=3)
    draw.ellipse((29, 21, 53, 29), fill=gold)
    draw.polygon([(33, 24), (32, 19), (45, 10), (56, 8), (53, 14),
                  (46, 16), (50, 16), (42, 21), (47, 20), (39, 26)], fill=pale)
    draw.ellipse((23, 18, 34, 26), fill=gold)
    draw.polygon([(19, 23), (27, 21), (29, 26), (22, 27)], fill=gold)
    draw.arc((18, 13, 34, 22), 180, 357, fill=pale, width=2)
    draw.arc((49, 15, 59, 26), 230, 115, fill=gold, width=2)
    draw.rectangle((16, 31, 23, 35), fill=pale)
    draw.line((19, 31, 19, 35), fill=red)
    draw.point((24, 22), fill=red)
    image.save(path)


def apply():
    geometry = make_geometry()
    for name, cells in geometry.items():
        path = D / "masks" / "ends" / f"{name}.txt"
        mask(path, cells)
        title = "艏平台與艏喙" if name == "bow" else "艉平台、艉篷與旗桿"
        work = component(name, "威尼斯 galea " + title, path, SIZE)
        if name not in entries(ASM, "links"):
            link(ASM, name, work)
    stern = HULL + "-stern"
    for name, point in {"ensign-head": (40, 160, 70), "ensign-foot": (40, 160, 53),
                        "ensign-cleat": (43, 160, 31)}.items():
        ensure_anchor(stern, name, point)
    texture = D / "masks" / "ends" / "venice-ensign.png"
    ensign_texture(texture)
    if "ensign" not in entries(ASM, "sails"):
        cli("work", sub="sail", work=ASM, name="ensign",
            corners="stern/ensign-head|1,160,69|1,160,52|stern/ensign-foot",
            corner_names="head|fly-top|fly-foot|foot", bind="3", free="fly-top,fly-foot",
            color="#ffffff", texture=texture, fullness=1.04)
    rope("ensign-halyard", "stern/ensign-cleat", "stern/ensign-head", "standing")
    rope("ensign-downhaul", "stern/ensign-cleat", "stern/ensign-foot", "standing")
    cli("work", sub="meta", work=ASM, part="sail", name="ensign",
        meta=dict(kind="flag", flag="ensign", nation="venice"))
    plan = json.loads((D / "plan.json").read_text(encoding="utf-8"))
    waterline = plan["waterline"]["blocksail_full_load_z"]
    cli("work", sub="meta", work=ASM, part="link", name="船殼", meta=dict(kind="ship", waterline_z=waterline))
    for mast in ("fore", "main"):
        cli("work", sub="meta", work=HULL + "-mast-" + mast, part="model", name="yard-" + mast,
            meta=dict(sail=mast + "-lateen"))
    cli("work", sub="meta", work=ASM, part="sail", name="fore-lateen", meta=dict(set=1))
    if "stern-lantern" not in entries(ASM, "models"):
        cli("work", sub="model", work=ASM, name="stern-lantern", source_work="gura-tridente-01m-lantern",
            at="39.5,160.5,35", pivot="8.5,8.5,0", scale=.5, meta=dict(kind="light"))
    if "rudder" not in entries(ASM, "models"):
        # The stock runs just aft of the rising sternpost. Blade stays aft of the hinge.
        cells = {}
        for z in range(2, 35):
            stock = 26 + z // 3
            width = 7 if z < 16 else max(1, (30 - z) // 3)
            for x in range(stock - width, stock + 1):
                for y in (159, 160, 161):
                    cells[x, y, z] = WOOD
        for x in range(37, 57):
            cells[x, 160, 34] = TRIM
        path = D / "masks/ends/rudder.txt"
        mask(path, cells)
        rudder = component("rudder", "威尼斯 galea 舵與舵柄", path, SIZE)
        ensure_anchor(rudder, "stock-top", (37, 160, 34))
        cli("work", sub="model", work=ASM, name="rudder", source_work=rudder,
            at="26.5,160.5,0.5", pivot="26.5,160.5,0.5", scale=1,
            meta=dict(kind="rudder", hinge_x=26.5, hinge_y=160.5, hinge_z=.5,
                axis_x=.316, axis_y=0, axis_z=.949, max_deg=30, turn_axis="hinge",
                spin="rudder", spin_k=30, spin_min=-30, spin_max=30, spin_lag=.3))
    print(json.dumps({key: len(cells) for key, cells in geometry.items()}), flush=True)
    print(cli("work", sub="ropecheck", work=ASM), flush=True)


if __name__ == "__main__":
    apply()
