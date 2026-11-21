"""Deterministic Step 11 generator and verifier: rudder, helm port, tiller, catheads, and anchors."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import deque
from typing import Dict, Iterable, List, Set, Tuple

import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(THIS_DIR, "tools")
WORK_DIR = os.path.dirname(THIS_DIR)
OUT_DIR = os.path.join(THIS_DIR, "out")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import wio  # noqa: E402

YC = 96
MIRROR_SUM = 192
COL_TEAK = 141
COL_PINE = 177
COL_IRON = 104
COL_RED = 192
COL_GOLD = 212


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
    xs = [p[0] for p in s]
    ys = [p[1] for p in s]
    zs = [p[2] for p in s]
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
    total = (x1 - x0 + 1) * (y1 - y0 + 1) * (z1 - z0 + 1)
    return total - len(s) - len(ext)


def mirror_diff(vmap: Dict[Tuple[int, int, int], int]) -> int:
    return sum(1 for (x, y, z), c in vmap.items() if vmap.get((x, MIRROR_SUM - y, z)) != c)


def gen_rudder(cfg: dict) -> Dict[Tuple[int, int, int], int]:
    """Generate pierced Chinese lifting rudder (開孔升降舵) symmetric about y=96."""
    xs = cfg["x_stock"]
    y0 = cfg["y_mid"]
    z0 = cfg["z_bot"]
    z1 = cfg["z_top"]
    x_aft_bot = cfg["x_aft_bot"]
    x_aft_top = cfg["x_aft_top"]
    x_fwd_bot = cfg["x_fwd_bot"]
    z_chin = cfg["z_chin"]
    z_sh = cfg["z_shoulder"]

    v: Dict[Tuple[int, int, int], int] = {}

    # Vertical 3x3 rudder stock (with slight bevel above z_sh)
    for z in range(z0, z1 + 1):
        for x in range(xs - 1, xs + 2):
            for y in range(y0 - 1, y0 + 2):
                # Iron straps & gilded cap accents
                if z >= z1 - 1:
                    col = COL_GOLD if (x == xs and y == y0) else COL_RED
                elif z in (12, 24, 36, 46, 53):
                    col = COL_IRON
                else:
                    col = COL_TEAK
                v[(x, y, z)] = col

    # Swept Chinese blade body across z = z0 .. z_sh
    for z in range(z0, z_sh + 1):
        t_aft = (z - z0) / max(1, (z_sh - z0))
        x_aft = int(round(x_aft_bot + (x_aft_top - x_aft_bot) * (t_aft ** 1.35)))
        if z <= z_chin:
            t_fwd = z / max(1, z_chin)
            if z <= 14:
                x_fwd = x_fwd_bot
            else:
                u = (z - 14) / max(1, (z_chin - 14))
                x_fwd = int(round(x_fwd_bot + (xs + 1 - x_fwd_bot) * (u ** 0.9)))
        else:
            x_fwd = xs + 1

        # Top shoulder bevel aft
        if z > z_sh - 5:
            u = (z - (z_sh - 5)) / 5.0
            x_aft = max(x_aft, int(round(x_aft + (xs - 3 - x_aft) * u)))

        for x in range(x_aft, x_fwd + 1):
            # Taper single cell thickness on trailing-most column for hydrodynamic edge
            ys = (y0,) if x == x_aft else (y0 - 1, y0, y0 + 1)
            for y in ys:
                if (x, y, z) in v:
                    continue
                if z in (12, 24, 36) or z == z0:
                    col = COL_IRON
                elif z >= z_sh - 1 and x >= xs - 2:
                    col = COL_RED
                else:
                    col = COL_TEAK
                v[(x, y, z)] = col

    # Traditional 5 diamond water-release perforations (開孔減壓, 6-connected margins preserved)
    holes = [
        (43, 12, 2),
        (51, 16, 2),
        (44, 24, 2),
        (51, 28, 2),
        (46, 33, 1),
    ]
    for cx, cz, rad in holes:
        for z in range(cz - rad, cz + rad + 1):
            for x in range(cx - rad, cx + rad + 1):
                if abs(x - cx) + abs(z - cz) <= rad - 1 or (rad == 1 and x == cx and z == cz):
                    for y in (y0 - 1, y0, y0 + 1):
                        v.pop((x, y, z), None)
        # Re-check iron border on hole rims if desired? Leave clean dark teak wall

    return v


def gen_tiller(cfg: dict, x_stock: int, y_mid: int) -> Dict[Tuple[int, int, int], int]:
    """Generate curved traditional tiller bar passing cleanly onto poop deck."""
    xs = cfg["x_start"]
    xb = cfg["x_bend"]
    xe = cfg["x_end"]
    zp = cfg["z_pass"]
    zg = cfg["z_grip"]
    v: Dict[Tuple[int, int, int], int] = {}

    for x in range(xs, xe + 1):
        if x < xb:
            zs = (zp, zp + 1)
        elif x == xb:
            zs = (zp, zp + 1, zg + 1)
        else:
            zs = (zg, zg + 1)
        for z in zs:
            if x <= xs + 2:
                col = COL_IRON
            elif x >= xe - 1:
                col = COL_GOLD if z == zg + 1 else COL_RED
            else:
                col = COL_TEAK
            v[(x, y_mid, z)] = col
    return v


def gen_anchor_gear(cfg: dict) -> Dict[Tuple[int, int, int], int]:
    """Generate symmetric outboard gunwale cathead knees (錨架 P/S), leaving foredeck center clear."""
    x0 = cfg["x_cat"]
    x1 = x0 + cfg["x_len"] - 1
    y_in = cfg["y_in"]
    y_out = cfg["y_out"]
    z_in_bot = cfg["z_in_bot"]
    zb = cfg["z_beam"]
    z_drop = cfg["z_tip_drop"]
    v: Dict[Tuple[int, int, int], int] = {}

    for side_s in (True, False):
        ys_in = (y_in, y_in + 1)
        ys_out = range(y_in, y_out + 1)
        ys_drop = (y_out - 1, y_out)
        if not side_s:
            ys_in = tuple(MIRROR_SUM - y for y in ys_in)
            ys_out = [MIRROR_SUM - y for y in ys_out]
            ys_drop = tuple(MIRROR_SUM - y for y in ys_drop)

        for x in range(x0, x1 + 1):
            # Inboard backing stanchions down inside bulwark
            for y in ys_in:
                for z in range(z_in_bot, zb):
                    v[(x, y, z)] = COL_IRON if z in (z_in_bot, zb - 1) else COL_TEAK
            # Horizontal cathead horn over gunwale (z=51..52, strictly above z<=50 rail)
            for y in ys_out:
                for z in (zb, zb + 1):
                    edge = (y == (y_out if side_s else MIRROR_SUM - y_out))
                    col = COL_RED if edge else (COL_IRON if (abs(y - YC) >= y_out - YC - 1 and z == zb + 1) else COL_TEAK)
                    v[(x, y, z)] = col
            # Outboard drop hook holding grapnel ring cleanly at z_tip_drop=49..50
            for y in ys_drop:
                for z in range(z_drop, zb):
                    v[(x, y, z)] = COL_IRON if z == z_drop else COL_TEAK

    return v


def rotate_xy_box_hits(
    pts: Iterable[Tuple[int, int, int]],
    hx: float,
    hy: float,
    deg: float,
    obstacles: Set[Tuple[int, int, int]],
) -> List[Tuple[int, int, int]]:
    rad = math.radians(deg)
    ca, sa = math.cos(rad), math.sin(rad)
    hits: List[Tuple[int, int, int]] = []
    # Sample corners + center of each moving voxel across continuous rotation
    offs = ((0.15, 0.15), (0.85, 0.15), (0.15, 0.85), (0.85, 0.85), (0.5, 0.5))
    for vx, vy, vz in pts:
        for ox, oy in offs:
            dx = (vx + ox) - hx
            dy = (vy + oy) - hy
            rx = hx + dx * ca - dy * sa
            ry = hy + dx * sa + dy * ca
            cell = (int(math.floor(rx)), int(math.floor(ry)), vz)
            if cell in obstacles:
                hits.append(cell)
    return hits


def check_grapnel_hits(
    grap_vox: np.ndarray,
    at: Tuple[float, float, float],
    pivot: Tuple[float, float, float],
    scale: float,
    yaw_deg: float,
    obstacles: Set[Tuple[int, int, int]],
) -> Set[Tuple[int, int, int]]:
    """Compute exact world cells touched by scaled/rotated grapnel model."""
    rad = math.radians(yaw_deg)
    ca, sa = math.cos(rad), math.sin(rad)
    hits: Set[Tuple[int, int, int]] = set()
    # Sample sub-points of each grapnel voxel transformed to world
    for gx, gy, gz, _ in grap_vox:
        for ox, oy, oz in ((0.2, 0.2, 0.2), (0.8, 0.8, 0.8), (0.5, 0.5, 0.5)):
            lx = (gx + ox - pivot[0]) * scale
            ly = (gy + oy - pivot[1]) * scale
            lz = (gz + oz - pivot[2]) * scale
            wx = at[0] + lx * ca - ly * sa
            wy = at[1] + lx * sa + ly * ca
            wz = at[2] + lz
            c = (int(math.floor(wx)), int(math.floor(wy)), int(math.floor(wz)))
            if c in obstacles:
                hits.add(c)
    return hits


def write_list(path: str, vmap: Dict[Tuple[int, int, int], int], comment: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {comment}\n")
        for (x, y, z), c in sorted(vmap.items()):
            f.write(f"{x},{y},{z},{c}\n")


def run(probe: str | None = None) -> dict:
    with open(os.path.join(THIS_DIR, "plan.json"), "r", encoding="utf-8") as f:
        plan = json.load(f)
    cfg = plan["rudder_anchor_build"]

    # Load live baseline works
    hull_arr = wio.export_list("kotoko-ganzengchuan-01m")
    bal_arr = wio.export_list("kotoko-ganzengchuan-01m-stern-balcony")
    poop_arr = wio.export_list("kotoko-ganzengchuan-01m-deck-poop")
    fore_arr = wio.export_list("kotoko-ganzengchuan-01m-deck-fore")
    dbow_arr = wio.export_list("kotoko-ganzengchuan-01m-deco-bow")
    grap_arr = wio.export_list(cfg["anchors"]["source"])

    hull_map = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in hull_arr}
    bal_map = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in bal_arr}
    poop_set = {(int(r[0]), int(r[1]), int(r[2])) for r in poop_arr}
    fore_set = {(int(r[0]), int(r[1]), int(r[2])) for r in fore_arr}
    dbow_set = {(int(r[0]), int(r[1]), int(r[2])) for r in dbow_arr}

    tcfg = cfg["tiller"]
    # Exact carve sets on balcony & hull for tiller helm port
    carve_bal: Dict[Tuple[int, int, int], int] = {}
    bx0, bx1 = tcfg["carve_balcony_x"]
    by0, by1 = tcfg["carve_balcony_y"]
    bz0, bz1 = tcfg["carve_balcony_z"]
    for (x, y, z), c in bal_map.items():
        if bx0 <= x <= bx1 and by0 <= y <= by1 and bz0 <= z <= bz1:
            carve_bal[(x, y, z)] = c

    carve_hull: Dict[Tuple[int, int, int], int] = {}
    hx0, hx1 = tcfg["carve_hull_x"]
    hy0, hy1 = tcfg["carve_hull_y"]
    hz0, hz1 = tcfg["carve_hull_z"]
    for (x, y, z), c in hull_map.items():
        if hx0 <= x <= hx1 and hy0 <= y <= hy1 and hz0 <= z <= hz1:
            carve_hull[(x, y, z)] = c

    carved_hull_map = {k: v for k, v in hull_map.items() if k not in carve_hull}
    carved_bal_map = {k: v for k, v in bal_map.items() if k not in carve_bal}

    rudder_map = gen_rudder(cfg["rudder"])
    tiller_map = gen_tiller(tcfg, cfg["rudder"]["x_stock"], cfg["rudder"]["y_mid"])
    gear_map = gen_anchor_gear(cfg["anchor_gear"])

    # Static overlap checks against vessel body
    hull_bal_poop_fore = set(carved_hull_map) | set(carved_bal_map) | poop_set | fore_set | dbow_set
    rudder_overlap = sorted(set(rudder_map) & (hull_bal_poop_fore | set(tiller_map)))
    tiller_overlap = sorted(set(tiller_map) & (hull_bal_poop_fore | set(rudder_map)))
    gear_overlap = sorted(set(gear_map) & (hull_bal_poop_fore | set(rudder_map) | set(tiller_map)))

    # Dynamic +/- 35 deg sweep collision checks for rudder & tiller
    hx = cfg["rudder"]["x_stock"] + 0.5
    hy = cfg["rudder"]["y_mid"] + 0.5
    sweep_obstacles = set(carved_hull_map) | set(carved_bal_map) | poop_set
    rudder_sweep_hits = 0
    tiller_sweep_hits = 0
    for deg in range(-35, 36, 5):
        rudder_sweep_hits += len(rotate_xy_box_hits(rudder_map.keys(), hx, hy, deg, sweep_obstacles))
        tiller_sweep_hits += len(rotate_xy_box_hits(tiller_map.keys(), hx, hy, deg, sweep_obstacles))

    # Anchors placement + counterfactual shift probe
    acfg = cfg["anchors"]
    ax = float(acfg["x"])
    y_cen = float(acfg.get("y_center", YC + 0.5))
    ay_s = float(y_cen + acfg["y_off"])
    ay_p = float(y_cen - acfg["y_off"])
    az = float(acfg["z"])
    if probe and probe.startswith("shift="):
        spec = probe.split("=", 1)[1]
        name, delta_s = spec.split(":")
        delta = float(delta_s)
        if name == "錨-S":
            ay_s += delta
        elif name == "錨-P":
            ay_p += delta

    anchor_obs = set(carved_hull_map) | set(gear_map) | dbow_set
    pivot = tuple(float(v) for v in acfg["pivot"])
    hits_s = check_grapnel_hits(grap_arr, (ax, ay_s, az), pivot, float(acfg["scale"]), float(acfg["yaw_s"]), anchor_obs)
    hits_p = check_grapnel_hits(grap_arr, (ax, ay_p, az), pivot, float(acfg["scale"]), -float(acfg["yaw_s"]), anchor_obs)

    # Check hawse points lie cleanly in hull plating
    hawse_s = tuple(acfg["hawse_s"])
    hawse_p = tuple(acfg["hawse_p"])
    hawse_s_solid = hawse_s in carved_hull_map
    hawse_p_solid = hawse_p in carved_hull_map

    # Verify structural invariants (6-conn, 0 cavities, y-mirror)
    checks = {
        "rudder_voxels": len(rudder_map),
        "rudder_components_6": components_6(rudder_map),
        "rudder_cavities": closed_cavities(rudder_map),
        "rudder_mirror_diff": mirror_diff(rudder_map),
        "tiller_voxels": len(tiller_map),
        "tiller_components_6": components_6(tiller_map),
        "tiller_cavities": closed_cavities(tiller_map),
        "tiller_mirror_diff": mirror_diff(tiller_map),
        "gear_voxels": len(gear_map),
        "gear_components_6": components_6(gear_map),
        "gear_cavities": closed_cavities(gear_map),
        "gear_mirror_diff": mirror_diff(gear_map),
        "carved_bal_components_6": components_6(carved_bal_map),
        "carved_bal_cavities": closed_cavities(carved_bal_map),
        "carved_bal_mirror_diff": mirror_diff(carved_bal_map),
        "carved_hull_components_6": components_6(carved_hull_map),
        "carved_hull_cavities": closed_cavities(carved_hull_map),
        "carved_hull_mirror_diff": mirror_diff(carved_hull_map),
        "carve_bal_count": len(carve_bal),
        "carve_hull_count": len(carve_hull),
        "rudder_overlap": len(rudder_overlap),
        "tiller_overlap": len(tiller_overlap),
        "gear_overlap": len(gear_overlap),
        "rudder_sweep_hits": rudder_sweep_hits,
        "tiller_sweep_hits": tiller_sweep_hits,
        "anchor_s_hits": len(hits_s),
        "anchor_p_hits": len(hits_p),
        "anchor_s_at": [ax, ay_s, az],
        "anchor_p_at": [ax, ay_p, az],
        "hawse_s_solid": hawse_s_solid,
        "hawse_p_solid": hawse_p_solid,
    }

    if probe is None:
        write_list(os.path.join(OUT_DIR, "rudder.txt"), rudder_map, "Ganzengchuan pierced rudder")
        write_list(os.path.join(OUT_DIR, "tiller.txt"), tiller_map, "Ganzengchuan tiller")
        write_list(os.path.join(OUT_DIR, "anchor_gear.txt"), gear_map, "Ganzengchuan catheads and bitts")
        write_list(os.path.join(OUT_DIR, "carve_hull.txt"), carve_hull, "Hull stern helm-port carve")
        write_list(os.path.join(OUT_DIR, "carve_balcony.txt"), carve_bal, "Stern balcony helm-port carve")
        with open(os.path.join(OUT_DIR, "rudder_anchor_report.json"), "w", encoding="utf-8") as f:
            json.dump(checks, f, ensure_ascii=False, indent=2)

    return checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", default=None)
    args = ap.parse_args()
    res = run(probe=args.probe)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
