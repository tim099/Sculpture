"""Generate the cargo barca from Furttenbach's plate 18."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

DESIGN = Path(__file__).resolve().parent
PLAN = json.loads((DESIGN / "plan.json").read_text(encoding="utf-8"))
SIZE = PLAN["size"]
CENTER = PLAN["center_y"]
X_RANGE = range(47, 197)
Z_RANGE = range(39)


def interpolate(query, table):
    positions, values = np.array(table).T
    return np.interp(query, positions, values)


def envelope(extra=0, beam_probe=0):
    lines = PLAN["lines"]
    x = np.array(X_RANGE)[:, None, None]
    z = np.array(Z_RANGE)[None, None, :]
    y = np.abs(np.arange(SIZE[1]) - CENTER)[None, :, None]
    aft = interpolate(z, lines["stern_rake"])
    fore = interpolate(z, lines["stem_rake"])
    span = (x - aft) / (fore - aft)
    sheer = interpolate(x, lines["sheer"])
    plan = interpolate(span, lines["plan_halfwidth"])
    section = interpolate((z - 1) / 16, lines["section_halfwidth"])
    half_beam = PLAN["dimensions"]["beam"]["metres"] / PLAN["metres_per_voxel"] / 2 + beam_probe
    side = (y <= np.maximum(.5, half_beam * plan * section))
    return side & (span >= 0) & (span <= 1) & (z >= 1) & (z < sheer + extra)


def shell(beam_probe=0):
    solid = envelope(beam_probe=beam_probe)
    distance = ndimage.distance_transform_edt(np.pad(envelope(extra=10, beam_probe=beam_probe), 1))[1:-1, 1:-1, 1:-1]
    skin = solid & (distance <= PLAN["dimensions"]["hull_skin"]["cells"])
    # Keep structural seams tight where the rasterized skin meets the posts.
    z = np.array(Z_RANGE)[None, None, :]
    x = np.array(X_RANGE)[:, None, None]
    cap = solid & ((x <= interpolate(z, PLAN["lines"]["stern_rake"]) + 1) |
                   (x >= interpolate(z, PLAN["lines"]["stem_rake"]) - 1))
    skin |= cap
    skin[71 - X_RANGE.start:155 - X_RANGE.start, CENTER, 0] = True
    waterline = PLAN["dimensions"]["waterline_z"]["cells"]
    sheer = interpolate(x, PLAN["lines"]["sheer"])
    colors = np.where(skin, np.where(z < waterline, 100, 104), 0)
    colors = np.where(skin & ((z == sheer.astype(int) - 2) | (z == 15)), 68, colors)
    colors = np.where(skin & (z == sheer.astype(int) - 1), 141, colors)
    return solid, colors


def draw_sheet(solid, colors, out):
    image = Image.new("RGB", (1050, 700), "#f5efe0")
    paint = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 16)
    large = ImageFont.truetype("arial.ttf", 27)
    brown, ink, blue = "#80543c", "#223e46", "#297b96"
    paint.text((38, 28), "Bizerte cargo barque / Furttenbach, plate 18", fill=ink, font=large)
    paint.text((39, 70), "Representative hull | 0.10 m per voxel | stern to bow, left to right", fill=ink, font=font)
    sx, sy, scale = 43, 304, 5
    paint.text((38, 102), "Profile, keel and sheer", fill=ink, font=font)
    for x, z in np.argwhere(colors.any(axis=1)):
        px, py = sx + scale * int(x), sy - scale * int(z)
        if py > 133:
            paint.rectangle((px, py, px + 4, py + 4), fill=brown)
    for title, level in (("Design waterline", 11), ("Cargo deck", 17)):
        y = sy - level * scale
        paint.line((sx, y, 960, y), fill=blue)
        paint.text((970, y - 8), "WL" if title.startswith("Design") else "DK", fill=ink, font=font)
    for v in range(50, 196, 10):
        px = sx + scale * (v - X_RANGE.start)
        paint.line((px, sy + 8, px, sy + 14), fill=ink)
        paint.text((px - 9, sy + 17), str(v), font=font, fill=ink)
    paint.text((38, 335), "Plan of hull girth, cargo hatch in blue", fill=ink, font=font)
    for x, y in np.argwhere(solid.any(axis=2)):
        px, py = sx + scale * int(x), 435 + 3 * (int(y) - CENTER)
        paint.rectangle((px, py, px + 4, py + 2), fill=brown)
    hatch = PLAN["layout"]
    ax, bx = hatch["open_hatch_x"]
    ay, by = hatch["open_hatch_y"]
    paint.rectangle((sx + scale*(ax-X_RANGE.start), 435 + 3*(ay-CENTER),
                     sx + scale*(bx-X_RANGE.start), 435 + 3*(by-CENTER)), outline=blue, width=2)
    paint.text((38, 515), "Transverse sections", fill=ink, font=font)
    for i, station in enumerate((65, 100, 124, 153, 177)):
        cx = 120 + i*197
        paint.line((cx, 555, cx, 648), fill=blue)
        for y, z in np.argwhere(colors[station - X_RANGE.start]):
            px, py = cx + 3*(int(y)-CENTER), 645 - 3*int(z)
            paint.rectangle((px, py, px + 2, py + 2), fill=brown)
        paint.text((cx - 22, 655), f"x={station}", fill=ink, font=font)
    image.save(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DESIGN)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args()
    solid, colors = shell()
    mask = colors > 0
    ordered = {(int(x) + X_RANGE.start, int(y), int(z)): int(colors[x, y, z])
               for x, y, z in np.argwhere(mask)}
    body = "".join(f"{x},{y},{z},{color}\n" for (x, y, z), color in ordered.items()).encode("ascii")
    check = {
        "voxels": len(ordered),
        "components": ndimage.label(mask)[1],
        "enclosed_air": int((ndimage.binary_fill_holes(mask) & ~mask).sum()),
        "mirror_color_differences": int((colors != colors[:, ::-1, :]).sum()),
        "bbox": [[min(c[i] for c in ordered), max(c[i] for c in ordered)] for i in range(3)],
        "mask_sha256": hashlib.sha256(body).hexdigest(),
        "beam_probe_plus_two_cells": int(np.count_nonzero(shell(2)[1] != colors)),
    }
    assert check["components"] == 1 and not check["enclosed_air"] and not check["mirror_color_differences"], check
    assert check["beam_probe_plus_two_cells"] > 0
    if args.export:
        rows = [line for line in args.export.read_text(encoding="utf-8-sig").splitlines() if line[:1].isdigit()]
        loaded = {(x, y, z): color for x, y, z, color in (map(int, row.split(",")) for row in rows)}
        check["sculpture_export"] = {
            "missing": len(ordered.keys() - loaded.keys()), "extra": len(loaded.keys() - ordered.keys()),
            "different_colors": sum(loaded[point] != ordered[point] for point in ordered.keys() & loaded.keys()),
        }
        assert not any(check["sculpture_export"].values()), check
    args.out.mkdir(exist_ok=True, parents=True)
    (args.out / "hull.vox.txt").write_bytes(body)
    draw_sheet(solid, colors, args.out / "sheet01_lines.png")
    (args.out / "verify_hull.json").write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(check))


if __name__ == "__main__":
    main()
