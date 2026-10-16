"""Read-only verification of the frozen stage 1/2 events; never stamp a work."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

D = Path(__file__).resolve().parents[1]
WORK = D.parent
OUT = Path(__file__).parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cells(path):
    result = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line and not line.startswith("#"):
            x, y, z, color = map(int, line.split(","))
            assert (x, y, z) not in result, (path.name, "duplicate", x, y, z)
            result[x, y, z] = color
    return result


def structure(actual):
    bounds = np.array(list(actual))
    low = bounds.min(axis=0) - 1
    high = bounds.max(axis=0) + 2
    solid = np.zeros(tuple(high - low), dtype=bool)
    points = bounds - low
    solid[tuple(points.T)] = True
    result = {
        "face_components": int(ndimage.label(solid)[1]),
        "closed_air_cells": int((ndimage.binary_fill_holes(solid) & ~solid).sum()),
        "mirror_differences": sum(actual.get((x, 240-y, z)) != c for (x,y,z),c in actual.items()),
    }
    assert result == {"face_components": 1, "closed_air_cells": 0, "mirror_differences": 0}, result
    return result


state = {}
snapshots = {}
event_sources = []
for path in sorted((WORK / "events").rglob("*.json")):
    event = json.loads(path.read_text(encoding="utf-8"))
    if path.parent.name != "2026-10-13":
        continue
    event_sources.append({"path": str(path.relative_to(WORK)), "sha256": digest(path)})
    if "placed_colored" in event:
        for x,y,z,c in event["placed_colored"]:
            assert (x,y,z) not in state
            state[x,y,z] = c
    elif "placed_voxels" in event:
        for x,y,z in event["placed_voxels"]:
            assert (x,y,z) not in state
            state[x,y,z] = event["color"]
    for point in event.get("carved_voxels", []):
        assert tuple(point) in state
        del state[tuple(point)]
    for prefix, name in [("230136", "skeleton"), ("230252", "shell"), ("231407", "ports")]:
        if path.name.startswith(prefix):
            snapshots[name] = state.copy()
    if "ports" in snapshots:
        break
assert set(snapshots) == {"skeleton", "shell", "ports"}
sk = cells(D / "skeleton.vox.txt")
sh = cells(D / "shell.vox.txt")
cuts = cells(D / "ports_frame_correction.vox.txt")
assert not (sk.keys() & sh.keys())
assert snapshots["skeleton"] == sk
assert snapshots["shell"] == sk | sh
assert all(snapshots["shell"][p] == c for p,c in sk.items())
assert snapshots["ports"] == {p:c for p,c in (sk | sh).items() if p not in cuts}
assert all(p[2] >= 52 for p in cuts)

report = {"scope": "Frozen construction stages 1/2, not the final assembled ship or rig dynamics", "events": event_sources, "stages": {}}
for name, own, probe in [("skeleton", sk, (105,100)), ("shell", sh, (100,150))]:
    actual = snapshots[name]
    im = np.asarray(Image.open(D / f"{name}_cell_plan.png").convert("RGB"))
    rows, cols = np.where(np.any(im != (16,38,48), axis=2))
    drawing = {(int(x),199-int(row)) for row,x in zip(rows,cols)}
    projection = {(x,z) for x,y,z in own}
    assert drawing == projection
    color_projection = {}
    for (x,y,z),c in own.items():
        color_projection[x,z] = max(c, color_projection.get((x,z),0))
    mismatches = 0
    for (x,z),c in color_projection.items():
        rgb = (int(((c>>5)&7)*255/7), int(((c>>2)&7)*255/7), int((c&3)*255/3))
        mismatches += tuple(im[199-z,x]) != rgb
    assert mismatches == 0
    assert probe in drawing
    px,pz = probe
    xs = {x for x,y,z in actual if z == pz}
    baseline = min(abs(x-px) for x in xs)
    shifted = min(abs(x+3-px) for x in xs)
    assert (baseline,shifted) == (0,3)
    report["stages"][name] = {
        "cells": len(actual), "new_cells": len(own), "result_ledger_differences": 0,
        "previous_changed": 0, "drawing_projection_differences": 0, "drawing_color_differences": mismatches,
        "png_sha256": digest(D / f"{name}_cell_plan.png"),
        "list_sha256": digest(D / f"{name}.vox.txt"),
        "probe_from_png": probe, "baseline_distance": baseline, "full_asset_x_plus_3_distance": shifted,
        **structure(actual),
    }

report["stages"]["ports"] = {"cells": len(snapshots["ports"]), "removed": len(cuts), "removed_below_waterline": 0, **structure(snapshots["ports"])}
# Water occupies z=0..51; seed the sides and bottom, never the open waterline top.
solid = np.zeros((800,241,52), dtype=bool)
for x,y,z in snapshots["ports"]:
    if z < 52:
        solid[x,y,z] = True
seed = np.zeros_like(solid)
seed[0,:,:] = seed[-1,:,:] = True
seed[:,0,:] = seed[:,-1,:] = True
seed[:,:,0] = True
water = ndimage.binary_propagation(seed & ~solid, mask=~solid)
assert not solid[350,120,40] and not water[350,120,40]
report["stages"]["ports"]["interior_probe_reached_by_exterior_water"] = False
report["all_assertions_passed"] = True
(OUT / "early_stage_readback.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"passed": True, "stages": report["stages"]}, ensure_ascii=False))
