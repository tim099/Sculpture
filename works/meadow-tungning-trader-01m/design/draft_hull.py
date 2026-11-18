"""Generate the Tungning trader's designed lines.

Derived from meadow-bizerte-barque-01m/design/draft_hull.py.
The parameters are design decisions, with museum references in sources.md.
"""
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
X_RANGE = range(27, 345)
Z_RANGE = range(84)


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
    section = interpolate((z - 1) / lines["section_height_cells"], lines["section_halfwidth"])
    half_beam = lines["half_beam_cells"] + beam_probe
    side = (y <= np.maximum(.5, half_beam * plan * section))
    return side & (span >= 0) & (span <= 1) & (z >= 1) & (z < sheer + extra)


def shell(beam_probe=0, cutouts=True):
    solid = envelope(beam_probe=beam_probe)
    distance = ndimage.distance_transform_edt(np.pad(envelope(extra=10, beam_probe=beam_probe), 1))[1:-1, 1:-1, 1:-1]
    skin = solid & (distance <= PLAN["dimensions"]["skin_cells"])
    # Keep structural seams tight where the rasterized skin meets the posts.
    z = np.array(Z_RANGE)[None, None, :]
    x = np.array(X_RANGE)[:, None, None]
    cap = solid & ((x <= interpolate(z, PLAN["lines"]["stern_rake"]) + 1) |
                   (x >= interpolate(z, PLAN["lines"]["stem_rake"]) - 1))
    skin |= cap
    skin[66 - X_RANGE.start:307 - X_RANGE.start, CENTER, 0] = True
    waterline = PLAN["dimensions"]["loaded_waterline_z"]
    sheer = interpolate(x, PLAN["lines"]["sheer"])
    colors = np.where(skin, np.where(z < waterline, 219, 104), 0)
    colors = np.where(skin & ((z == sheer.astype(int) - 2) | (z == 37)), 36, colors)
    colors = np.where(skin & (z == sheer.astype(int) - 1), 160, colors)
    # Stern windows are cut through the complete planking. Glass is a separate part.
    if not cutouts:
        return solid, colors
    for y0,y1 in ((62,72),(88,98)):
        colors[:60-X_RANGE.start,y0:y1+1,60:67] = 0
    # Open-topped bulwark notches, above the weather-deck sill.
    for station in PLAN["guns"]["long6_x"]:
        for y in range(SIZE[1]):
            if abs(y-CENTER)>=10:
                colors[station-5-X_RANGE.start:station+6-X_RANGE.start,y,52:] = 0
    # Open the stern-accommodation door and the top of its exterior stair.
    colors[88-X_RANGE.start:92-X_RANGE.start,76:85,48:69] = 0
    colors[88-X_RANGE.start:92-X_RANGE.start,95:102,72:80] = 0
    colors[88-X_RANGE.start:92-X_RANGE.start,59:66,72:80] = 0
    return solid, colors


def draw_sheet(solid, colors, out):
    image = Image.new("RGB", (1550, 1020), "#f5efe0")
    paint = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 16)
    large = ImageFont.truetype("arial.ttf", 27)
    brown, ink, blue = "#80543c", "#223e46", "#297b96"
    paint.text((38, 28), "Tungning three-masted trader / designed Fuchuan lines", fill=ink, font=large)
    paint.text((39, 70), "31.2 x 8.1 m | design loaded draft 3.8 m | 0.10 m per voxel | stern left, bow right", fill=ink, font=font)
    sx, sy, scale = 43, 490, 4
    paint.text((38, 102), "Profile, keel and sheer", fill=ink, font=font)
    for x, z in np.argwhere(colors.any(axis=1)):
        px, py = sx + scale * int(x), sy - scale * int(z)
        paint.rectangle((px, py, px + 3, py + 3), fill=brown)
    for title, level in (("Light reference", 20), ("Loaded waterline", 38), ("Main deck", 48), ("Poop", 72)):
        y = sy - level * scale
        paint.line((sx, y, 1380, y), fill=blue)
        paint.text((1390, y - 8), title, fill=ink, font=font)
    for v in range(40, 345, 20):
        px = sx + scale * (v - X_RANGE.start)
        paint.line((px, sy + 8, px, sy + 14), fill=ink)
        paint.text((px - 9, sy + 17), str(v), font=font, fill=ink)
    paint.text((38, 535), "Hull girth plan", fill=ink, font=font)
    for x, y in np.argwhere(solid.any(axis=2)):
        px, py = sx + scale * int(x), 650 + 2 * (int(y) - CENTER)
        paint.rectangle((px, py, px + 3, py + 1), fill=brown)
    paint.text((38, 765), "Transverse sections", fill=ink, font=font)
    for i, station in enumerate(PLAN["lines"]["stations"]):
        cx = 120 + i*205
        paint.line((cx, 790, cx, 980), fill=blue)
        for y, z in np.argwhere(colors[station - X_RANGE.start]):
            px, py = cx + 2*(int(y)-CENTER), 980 - 2*int(z)
            paint.rectangle((px, py, px + 1, py + 1), fill=brown)
        paint.text((cx - 22, 990), f"x={station}", fill=ink, font=font)
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
        "displacement_t_light_reference": round(float(solid[:, :, :PLAN["dimensions"]["light_reference_z"]].sum()) * .001 * 1.025, 3),
        "displacement_t_loaded": round(float(solid[:, :, :PLAN["dimensions"]["loaded_waterline_z"]].sum()) * .001 * 1.025, 3),
        "loa_m": round(float(np.ptp(np.argwhere(mask)[:, 0]) + 1) * .1, 2),
        "beam_m": round(float(np.ptp(np.argwhere(mask)[:, 1]) + 1) * .1, 2),
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
