"""Fan-shaped hard sails for Tungning; apply after draft_battens.py.

The roach equation and pitched upper yard follow the shachuan rig (TASK-1321).
The photo supplies the silhouette. Dimensions and clearances are design choices
for the existing Tungning mast positions. All sculpture edits go through CLI.
"""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sculpt_cli as sc
from draft_hull import DESIGN, PLAN


# Lower-yard length relative to the original; upper length relative to lower.
# The sail order is aft to fore across a row, so roach[0] is the leech.
SHAPES = {
    "fore": (0.72, 0.78, 17, (0.16, 0.04645)),
    "main": (0.84, 0.78, 16, (0.16, 0.03765)),
    "mizzen": (0.85, 0.76, 15, (0.16, 0.06316)),
}
TIP_MARGIN = 1.5


def read_points(work, names):
    anchors = sc.entries(work, "anchors")
    return {name: tuple(value + .5 if isinstance(value, int) else value
                        for value in anchors[name]["at"]) for name in names}


def lerp(a, b, v):
    return tuple(x + (y - x) * v for x, y in zip(a, b))


def row(corners, roach, v):
    a = lerp(corners[0], corners[3], v)
    b = lerp(corners[1], corners[2], v)
    bulge = 0 if v in (0, 1) else math.sin(math.pi * v ** .85)
    return lerp(a, b, -bulge * roach[0]), lerp(a, b, 1 + bulge * roach[1])


def sail_plan(name):
    spec = PLAN["rig"][name]
    lower_scale, upper_ratio, pitch, roach = SHAPES[name]
    work = f"{sc.HULL}-mast-{name}"
    models = sc.entries(work, "models")
    # Both frames use the lower yard's mesh and earings with different scaling.
    # This keeps the same fore/aft proportion about the mast as the sail narrows.
    source = f"{sc.HULL}-yard-{name}-lower"
    p = read_points(source, ("pivot", "earing-aft", "earing-fore"))
    mast_x, mast_y, _ = models["yard-lower"]["at"]
    frames = {}
    for pos, scale, angle in (("upper", lower_scale * upper_ratio, pitch),
                              ("lower", lower_scale, 0)):
        origin = (mast_x, mast_y, spec[f"{pos}_z"] + .5)
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        ends = []
        for key in ("earing-aft", "earing-fore"):
            assert p[key][1:] == p["pivot"][1:]
            dx = (p[key][0] - p["pivot"][0]) * scale
            ends.append((origin[0] + dx * c, origin[1], origin[2] - dx * s))
        frames[pos] = dict(at=origin, ends=ends, pitch=angle, scale=scale)
    corners = (*frames["upper"]["ends"], *reversed(frames["lower"]["ends"]))
    rods = []
    rod = f"{sc.HULL}-batten-{name}"
    a = read_points(rod, ("pivot", "arm-P", "arm-S"))
    left_span = a["pivot"][0] - a["arm-P"][0]
    right_span = a["arm-S"][0] - a["pivot"][0]
    for m in range(1, spec["battens"] + 1):
        v = m / (spec["battens"] + 1)
        left, right = row(corners, roach, v)
        u = (mast_x - left[0]) / (right[0] - left[0])
        at = lerp(left, right, u)
        angle = -math.degrees(math.atan2(right[2] - left[2], right[0] - left[0]))
        open_left, open_right = math.dist(at, left), math.dist(at, right)
        # A furled row approaches the lower yard's width. Size the same rod
        # for both limits so no sail edge extends past its support in motion.
        lower_width = math.dist(*frames["lower"]["ends"])
        scale = max((max(open_left, u * lower_width) + TIP_MARGIN) / left_span,
                    (max(open_right, (1-u) * lower_width) + TIP_MARGIN) / right_span)
        overhang = (left_span * scale - open_left, right_span * scale - open_right)
        assert min(overhang) >= TIP_MARGIN - 1e-8
        rods.append(dict(name=f"batten-{m:02d}", at=at, pitch=angle, scale=scale,
                         overhang=overhang, span=(left_span * scale, right_span * scale)))
    return dict(mast=name, corners=corners, roach=roach, frames=frames, rods=rods)


def install(plan):
    name = plan["mast"]
    host = f"{sc.HULL}-mast-{name}"
    sail = f"{name}-junk"
    old = sc.entries(host, "models")
    frame_source = f"{sc.HULL}-yard-{name}-lower"
    rod_source = f"{sc.HULL}-batten-{name}"
    frame_pivot = read_points(frame_source, ("pivot",))["pivot"]
    for pos, frame in plan["frames"].items():
        label = f"yard-{pos}"
        span = math.dist(*frame["ends"])
        meta = {**old[label]["meta"], "yard": "course", "length_ft": round(span * .1 / .3048, 2)}
        sc.model(host, label, frame_source, frame["at"], frame_pivot, meta,
                 scale=(frame["scale"], 1, 1), rotate=(0, frame["pitch"], 0))
    rod_pivot = read_points(rod_source, ("pivot",))["pivot"]
    for rod in plan["rods"]:
        label = rod["name"]
        meta = {**old[label]["meta"], "length_ft": round(sum(rod["span"]) * .1 / .3048, 2)}
        sc.model(host, label, rod_source, rod["at"], rod_pivot, meta,
                 scale=(rod["scale"], 1, 1), rotate=(0, rod["pitch"], 0))
    sc.sculpt("work", sub="meta", work=sc.ASSEMBLY, part="sail", name=sail,
              meta={"roach": ",".join(map(str, plan["roach"]))})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--works", type=Path, help="Sculpture metadata root when running from a worktree")
    args = parser.parse_args()
    if args.works:
        sc.WORKS = args.works
    plans = [sail_plan(name) for name in SHAPES]
    envelopes = []
    for plan in plans:
        xs = [point[0] for i in range(101) for point in row(plan["corners"], plan["roach"], i / 100)]
        for rod in plan["rods"]:
            x = rod["at"][0]
            c = math.cos(math.radians(rod["pitch"]))
            xs.extend((x - rod["span"][0] * c, x + rod["span"][1] * c))
        envelopes.append((min(xs), max(xs)))
    gaps = [before[0] - later[1] for before, later in zip(envelopes, envelopes[1:])]
    assert min(gaps) >= 4, gaps
    for plan in plans:
        if args.apply:
            install(plan)
        print(plan["mast"], "roach", plan["roach"], "battens", len(plan["rods"]),
              "max exposed tip (cells)", round(max(max(r["overhang"]) for r in plan["rods"]), 2), flush=True)
    (DESIGN / "curved_sails_placement.json").write_text(json.dumps(
        {"plans": plans, "span_clearance_cells": gaps}, indent=2) + "\n", encoding="utf8")
    print("Longitudinal clearance (cells):", gaps, flush=True)


if __name__ == "__main__":
    main()
