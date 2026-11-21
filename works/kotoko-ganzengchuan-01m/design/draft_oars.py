"""Deterministic Step 13 generator and verifier: Fujian Ganzengchuan auxiliary long oars (輔佐長櫓)."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import deque
from typing import Dict, Iterable, List, Set, Tuple

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(THIS_DIR, "tools")
OUT_DIR = os.path.join(THIS_DIR, "out")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import wio  # noqa: E402

MIRROR_SUM = 192
COL_TEAK = 141
COL_PINE = 177
COL_IRON = 104
COL_RED = 192


def components_6(pts: Iterable[Tuple[int, int, int]]) -> int:
    s = set(pts)
    if not s:
        return 0
    seen: Set[Tuple[int, int, int]] = set()
    n = 0
    for seed in s:
        if seed in seen:
            continue
        n += 1
        q = deque([seed])
        seen.add(seed)
        while q:
            x, y, z = q.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nb = (x + dx, y + dy, z + dz)
                if nb in s and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
    return n


def closed_cavities(pts: Iterable[Tuple[int, int, int]]) -> int:
    s = set(pts)
    if not s:
        return 0
    xs, ys, zs = [p[0] for p in s], [p[1] for p in s], [p[2] for p in s]
    x0, x1 = min(xs) - 1, max(xs) + 1
    y0, y1 = min(ys) - 1, max(ys) + 1
    z0, z1 = min(zs) - 1, max(zs) + 1
    ext: Set[Tuple[int, int, int]] = {(x0, y0, z0)}
    q = deque([(x0, y0, z0)])
    while q:
        x, y, z = q.popleft()
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            nx, ny, nz = x + dx, y + dy, z + dz
            if x0 <= nx <= x1 and y0 <= ny <= y1 and z0 <= nz <= z1:
                nb = (nx, ny, nz)
                if nb not in s and nb not in ext:
                    ext.add(nb)
                    q.append(nb)
    return (x1 - x0 + 1) * (y1 - y0 + 1) * (z1 - z0 + 1) - len(s) - len(ext)


def gen_chinese_oar(cfg: dict) -> Dict[Tuple[int, int, int], int]:
    """Build 5.7m traditional Fujian auxiliary yuloh/sweep oar @ 0.05m (size 11x120x60)."""
    px, py, pz = cfg["pivot"]
    bx, by, bz = cfg["blade"]
    v: Dict[Tuple[int, int, int], int] = {}

    # 1. Cross-handle T-grip inside (y = 2..4) at z = 44..45 (waist height)
    for x in range(1, 10):
        for y in (2, 3, 4):
            for z in (44, 45):
                if y in (2, 4) and x in (1, 9):
                    continue
                v[(x, y, z)] = COL_IRON if x in (1, 9) else (COL_RED if x in (2, 8) else COL_PINE)

    # 2. Curved inboard loom rising gently from y=4 (z=44..45) up to pivot plateau y=27..33 (z=49..50)
    prev_z = 44
    for y in range(4, by + 1):
        if y <= py - 3:
            t = (y - 4) / max(1, py - 7)
            zc = 44.0 + (pz - 44.0) * (t ** 0.75)
        elif y <= py + 3:
            # Flat saddle pass across gunwale walls so shaft never dips below z_rail during stroke
            zc = float(pz)
        else:
            u = (y - (py + 3)) / max(1, by - (py + 3))
            zc = pz + (bz - pz) * u

        zi = int(round(zc))
        # Ensure 6-connected z transitions across y columns (always bridge prev_z..zi)
        z_lo = min(zi, prev_z)
        z_hi = max(zi, prev_z) + (0 if y >= 106 else 1)
        prev_z = zi

        is_blade = y >= 92
        if is_blade:
            xs = range(px - 2, px + 3) if (96 <= y <= 114) else range(px - 1, px + 2)
        elif y <= py - 3:
            xs = (px - 1, px, px + 1) if y >= py - 5 else (px,)
        elif y <= py + 3:
            xs = (px - 1, px, px + 1)
        else:
            xs = (px - 1, px, px + 1) if (y - py) < 28 else (px,)

        for x in xs:
            for z in range(z_lo, z_hi + 1):
                if is_blade:
                    col = COL_RED if (y == by and abs(x - px) <= 1) else COL_PINE
                elif py - 2 <= y <= py + 2:
                    col = COL_IRON
                elif y in (12, 20, 48, 66, 84, 91):
                    col = COL_IRON
                else:
                    col = COL_TEAK
                v[(x, y, z)] = col

    return v


def gen_oar_locks(
    cfg: dict,
    hull_map: Dict[Tuple[int, int, int], int],
    stations: List[dict],
) -> Tuple[Dict[Tuple[int, int, int], int], Dict[Tuple[int, int, int], int]]:
    """Build tholepin stops (櫓座) & collect 2-cell waist saddle carve cells on forward station."""
    x0, x1 = cfg["carve_saddle_x"]
    z0, z1 = cfg["carve_saddle_z"]
    carve: Dict[Tuple[int, int, int], int] = {}
    for (x, y, z), c in hull_map.items():
        if x0 <= x <= x1 and z0 <= z <= z1 and (y >= 124 or y <= 68):
            carve[(x, y, z)] = c

    locks: Dict[Tuple[int, int, int], int] = {}
    for st in stations:
        lx = st["lock_x"]
        lz0 = st["lock_z_top"]
        for y in st["lock_y_s"]:
            for my in (y, MIRROR_SUM - y):
                for z in (lz0, lz0 + 1):
                    locks[(lx, my, z)] = COL_IRON if z == lz0 + 1 else COL_TEAK
    return locks, carve


def parse_existing_model_boxes() -> List[Tuple[str, Tuple[float, float, float], Tuple[float, float, float]]]:
    SENATE = shutil.which("senate") or "senate"
    r = subprocess.run(
        [SENATE, "cmd", "sculpture", "--arg", "op=work", "--arg", "sub=models", "--arg", "id=kotoko-ganzengchuan-01m-assembly"],
        capture_output=True, text=True, check=True,
    )
    boxes = []
    pat = re.compile(r"- ✓ `([^`]+)`.*外框 \(([^)]+)\)–\(([^)]+)\)")
    for ln in r.stdout.splitlines():
        m = pat.search(ln)
        if not m:
            continue
        name = m.group(1)
        if name.startswith(("桅-", "砲M-", "甲板-main/", "護舷-")):
            p0 = tuple(float(v) for v in m.group(2).split(","))
            p1 = tuple(float(v) for v in m.group(3).split(","))
            boxes.append((name, p0, p1))
    return boxes


def oar_world_samples(
    oar_vox: Dict[Tuple[int, int, int], int],
    pivot_local: Tuple[float, float, float],
    pivot_world: Tuple[float, float, float],
    side: str,
    stroke_deg: float = 0.0,
) -> List[Tuple[float, float, float]]:
    """Transform 0.05m oar voxels into 0.1m world coordinates (with optional stroke yaw)."""
    px, py, pz = pivot_local
    wx0, wy0, wz0 = pivot_world
    mirror_y = -1.0 if side == "P" else 1.0
    rad = math.radians(stroke_deg)
    ca, sa = math.cos(rad), math.sin(rad)
    pts: List[Tuple[float, float, float]] = []
    for vx, vy, vz in oar_vox:
        for ox, oy, oz in ((0.5, 0.5, 0.5), (0.2, 0.2, 0.2), (0.8, 0.8, 0.8)):
            lx = (vx + ox - px) * 0.5
            ly = (vy + oy - py) * 0.5 * mirror_y
            lz = (vz + oz - pz) * 0.5
            rx = wx0 + lx * ca - ly * sa
            ry = wy0 + lx * sa + ly * ca
            rz = wz0 + lz
            pts.append((rx, ry, rz))
    return pts


def run(probe: str | None = None) -> dict:
    with open(os.path.join(THIS_DIR, "plan.json"), "r", encoding="utf-8") as f:
        plan = json.load(f)
    cfg = plan["oars_build"]
    ocfg = cfg["oar"]
    lcfg = cfg["locks"]
    mcfg = cfg["meta"]

    hull_arr = wio.export_list("kotoko-ganzengchuan-01m")
    deck_arr = wio.export_list("kotoko-ganzengchuan-01m-deck-main")
    hull_map = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in hull_arr}
    deck_set = {(int(r[0]), int(r[1]), int(r[2])) for r in deck_arr}

    oar_vox = gen_chinese_oar(ocfg)
    locks_vox, carve_hull = gen_oar_locks(lcfg, hull_map, cfg["stations"])
    carved_hull_map = {k: v for k, v in hull_map.items() if k not in carve_hull}
    solid_world = set(carved_hull_map) | set(locks_vox) | deck_set

    model_boxes = parse_existing_model_boxes()
    px, py, pz = ocfg["pivot"]
    bx, by, bz = ocfg["blade"]
    sx, sy, sz = ocfg["seat"]
    piv_loc = (px + 0.5, py + 0.5, pz + 0.5)

    drop_target = None
    drop_dz = 0.0
    if probe and probe.startswith("drop="):
        spec = probe.split("=", 1)[1]
        drop_target, dzs = spec.split(":")
        drop_dz = float(dzs)

    oars_report = []
    total_static_hits = 0
    total_sweep_hits = 0

    for idx, st in enumerate(cfg["stations"], start=1):
        for side in ("S", "P"):
            name = f"oar-{side}0{idx}"
            wy = float(st["y_s"] if side == "S" else st["y_p"])
            wz = float(st["z"]) + (drop_dz if name == drop_target else 0.0)
            pw = (float(st["x"]), wy, wz)

            # Static collision against hull + locks + deck + model boxes
            pts0 = oar_world_samples(oar_vox, piv_loc, pw, side, 0.0)
            vox_hits = {(int(math.floor(x)), int(math.floor(y)), int(math.floor(z))) for x, y, z in pts0 if (int(math.floor(x)), int(math.floor(y)), int(math.floor(z))) in solid_world}
            box_hits = []
            for mname, b0, b1 in model_boxes:
                if any(b0[0] <= x <= b1[0] and b0[1] <= y <= b1[1] and b0[2] <= z <= b1[2] for x, y, z in pts0):
                    box_hits.append(mname)

            # Stroke sweep check +/- stroke_deg
            sweep_hits = 0
            for ang in (-mcfg["stroke_deg"], -mcfg["stroke_deg"] // 2, mcfg["stroke_deg"] // 2, mcfg["stroke_deg"]):
                pts_a = oar_world_samples(oar_vox, piv_loc, pw, side, ang)
                for x, y, z in pts_a:
                    cell = (int(math.floor(x)), int(math.floor(y)), int(math.floor(z)))
                    if cell in solid_world:
                        sweep_hits += 1
                    for mname, b0, b1 in model_boxes:
                        if mname.startswith("砲M-") and b0[0] <= x <= b1[0] and b0[1] <= y <= b1[1] and b0[2] <= z <= b1[2]:
                            sweep_hits += 1

            # Check blade & rower standing positions (rowers = 2 along inboard axis, 0.6 m spacing)
            mir = -1.0 if side == "P" else 1.0
            blade_z = wz + ((bz + 0.5) - (pz + 0.5)) * 0.5
            seat0_y = wy + ((sy + 0.5) - (py + 0.5)) * 0.5 * mir
            seat0_z = wz + ((sz + 0.5) - (pz + 0.5)) * 0.5
            # Also check Ship_Oars rower#0 (at pivot -> inboard 0.6m? Actually Ship_Oars uses seat & +0.6m inboard)
            rower_ok = True
            rower_cells = []
            for r_i in range(mcfg["rowers"]):
                ry = int(math.floor(seat0_y - 6.0 * r_i * mir))
                rx = int(math.floor(pw[0]))
                rz = int(math.floor(seat0_z))
                floor_ok = (rx, ry, rz - 1) in deck_set
                head_ok = all((rx, ry, zz) not in solid_world for zz in range(rz, rz + 14))
                # Ensure rower column doesn't intersect nearby main deck models (boat/hatch/galley/capstan/guns)
                mod_ok = not any(b0[0] - 1 <= rx <= b1[0] + 1 and b0[1] - 1 <= ry <= b1[1] + 1 and b0[2] <= rz + 13 and b1[2] >= rz for mname, b0, b1 in model_boxes if mname.startswith("甲板-main/"))
                if not (floor_ok and head_ok and mod_ok):
                    rower_ok = False
                rower_cells.append({"rx": rx, "ry": ry, "rz": rz, "floor_ok": floor_ok, "head_ok": head_ok, "mod_ok": mod_ok})

            total_static_hits += len(vox_hits) + len(box_hits)
            total_sweep_hits += sweep_hits
            oars_report.append({
                "name": name,
                "side": side,
                "at": list(pw),
                "vox_hits": len(vox_hits),
                "box_hits": box_hits,
                "sweep_hits": sweep_hits,
                "blade_z": round(blade_z, 3),
                "blade_vs_wl24": round(blade_z - 24.0, 3),
                "seat0_z": round(seat0_z, 3),
                "rowers_ok": rower_ok,
                "rower_cells": rower_cells,
            })

    # Verify oar X-mirror symmetry (x <-> size_x - 1 - x => x <-> 10 - x)
    oar_mirror_diff = sum(1 for (x, y, z), c in oar_vox.items() if oar_vox.get((ocfg["size"][0] - 1 - x, y, z)) != c)
    locks_mirror_diff = sum(1 for (x, y, z), c in locks_vox.items() if locks_vox.get((x, MIRROR_SUM - y, z)) != c)

    report = {
        "oar_voxels": len(oar_vox),
        "oar_components_6": components_6(oar_vox),
        "oar_cavities": closed_cavities(oar_vox),
        "oar_mirror_x_diff": oar_mirror_diff,
        "locks_voxels": len(locks_vox),
        "locks_components_6": components_6(locks_vox),
        "locks_cavities": closed_cavities(locks_vox),
        "locks_mirror_y_diff": locks_mirror_diff,
        "carve_saddle_count": len(carve_hull),
        "carved_hull_components_6": components_6(carved_hull_map),
        "carved_hull_cavities": closed_cavities(carved_hull_map),
        "locks_overlap": len(set(locks_vox) & (set(carved_hull_map) | deck_set)),
        "total_static_hits": total_static_hits,
        "total_sweep_hits": total_sweep_hits,
        "oars": oars_report,
    }

    if probe is None:
        os.makedirs(OUT_DIR, exist_ok=True)
        for fname, vmap, desc in (
            ("oar.txt", oar_vox, "Ganzengchuan auxiliary long oar 0.05m"),
            ("oar_locks.txt", locks_vox, "Ganzengchuan oar locks 0.1m"),
            ("carve_oar_saddles.txt", carve_hull, "Hull waist oar saddle carve"),
        ):
            with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
                f.write(f"# {desc}\n")
                for (x, y, z), c in sorted(vmap.items()):
                    f.write(f"{x},{y},{z},{c}\n")
        with open(os.path.join(OUT_DIR, "oars_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", default=None)
    args = ap.parse_args()
    print(json.dumps(run(probe=args.probe), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
