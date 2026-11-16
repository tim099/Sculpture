"""威尼斯 galeazza（TASK-1302）船殼 01：plan.json 的線形 ⇒ 外殼兩格厚、塗裝、圖紙、verify。出處：meadow-venice-galea-01m/design/draft_hull.py（改範圍、顏色、圖紙尺寸）。"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

DESIGN = Path(__file__).resolve().parent
sys.path.insert(0, str(DESIGN))
from lines import Lines, load_plan

X_MIN, X_MAX, Z_MAX, EXTRA = 40, 570, 44, 24
BOTTOM, TOPSIDE, INSIDE = 32, 68, 141


def hull_shell(lines, waterline):
    nominal = lines.solid(X_MIN, X_MAX, Z_MAX)
    extended = np.pad(lines.solid(X_MIN, X_MAX, Z_MAX, EXTRA), 1)
    distance = ndimage.distance_transform_edt(extended)
    distance = distance[1:-1, 1:-1, 1:-1]
    shell = nominal & (distance <= 2.0)
    x = np.arange(X_MIN, X_MAX + 1)[:, None] + 0.5
    z = np.arange(Z_MAX + 1)[None, :] + 0.5
    aft = lines.x_aft(z)
    fore = lines.x_fwd(z)
    post = ((x >= aft) & (x < aft + 3) & (z <= lines.z_sh))
    post |= ((x > fore - 3) & (x <= fore) & (z <= lines.z_st))
    post = post[:, None, :] & (np.abs(np.arange(shell.shape[1]) - lines.YC)[None, :, None] <= 1)
    shell |= post
    outer = shell & ((distance <= 1.0) | post)
    colors = np.zeros(shell.shape, np.uint8)
    colors[shell] = INSIDE
    colors[outer] = TOPSIDE
    colors[outer & (z[:, None, :] <= waterline + 0.5)] = BOTTOM
    return colors


def draw_sheet(colors, ym, waterline, path):
    hull = colors > 0
    sheet = Image.new("RGB", (1220, 580), "#f7f5ec")
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 15), "Venetian galeazza / TASK-1302 / hull lines 01 / 0.1 m per voxel", fill="#162e34")
    draw.text((24, 44), "Profile  |  bow right", fill="#162e34")
    draw.line((24, 150 - 2 * waterline, 1200, 150 - 2 * waterline), fill="#588caa")
    for x, z in np.argwhere(hull.any(axis=1)):
        px, py = 24 + 2 * int(x), 150 - 2 * int(z)
        draw.rectangle((px, py, px + 1, py + 1), fill="#563c28")
    draw.text((24, 190), "Plan  |  29 passi (145 piedi, 50.42 m) between posts / beam 25 piedi", fill="#162e34")
    draw.line((24, 300, 1200, 300), fill="#588caa")
    for x, y in np.argwhere(hull.any(axis=2)):
        draw.point((24 + 2 * int(x), 300 + 2 * (int(y) - ym)), fill="#563c28")
    for i, x in enumerate((90, 150, 300, 470, 530)):
        cx = 110 + i * 230
        draw.line((cx, 440, cx, 545), fill="#588caa")
        draw.line((cx - 95, 540 - 2 * waterline, cx + 95, 540 - 2 * waterline), fill="#9cc3d6")
        draw.text((cx - 19, 552), f"x = {x}", fill="#162e34")
        for y, z in np.argwhere(hull[x - X_MIN]):
            draw.point((cx + 2 * (int(y) - ym), 540 - 2 * int(z)), fill="#563c28")
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-width", type=int, default=0)
    args = parser.parse_args()
    plan = load_plan(DESIGN)
    lines = Lines(plan, {"half_beam": args.probe_width} if args.probe_width else None)
    waterline = plan["waterline"]["z"]
    colors = hull_shell(lines, waterline)
    hull = colors > 0
    positions = np.argwhere(hull)
    mins, maxs = positions.min(axis=0), positions.max(axis=0)
    voids = ndimage.binary_fill_holes(np.pad(hull, 1))[1:-1, 1:-1, 1:-1] & ~hull
    stats = {
        "cells": len(positions),
        "components": ndimage.label(hull)[1],
        "enclosed_air_cells": int(voids.sum()),
        "mirror_differences": int(np.count_nonzero(colors != colors[:, ::-1, :])),
        "bbox_min": [int(mins[0]) + X_MIN, int(mins[1]), int(mins[2])],
        "bbox_max": [int(maxs[0]) + X_MIN, int(maxs[1]), int(maxs[2])],
        "beam_m": round((int(maxs[1]) - int(mins[1]) + 1) * plan["meters_per_cell"], 2),
    }
    assert stats["components"] == 1 and not stats["enclosed_air_cells"] and not stats["mirror_differences"], stats
    assert 0 <= stats["bbox_min"][0] <= stats["bbox_max"][0] < plan["space"]["hull"][0]
    assert 0 <= stats["bbox_min"][1] <= stats["bbox_max"][1] < plan["space"]["hull"][1]
    assert 0 <= stats["bbox_min"][2] <= stats["bbox_max"][2] < plan["space"]["hull"][2]
    if not args.probe_width:
        mask = DESIGN / "masks" / "hull" / "hull_01.vox.txt"
        mask.parent.mkdir(parents=True, exist_ok=True)
        voxel_list = "".join(f"{x + X_MIN},{y},{z},{colors[x, y, z]}\n" for x, y, z in positions).encode("ascii")
        mask.write_bytes(voxel_list)
        stats["sha256"] = hashlib.sha256(voxel_list).hexdigest()
        (DESIGN / "verify_hull.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        draw_sheet(colors, lines.YC, waterline, DESIGN / "sheet01_lines.png")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
