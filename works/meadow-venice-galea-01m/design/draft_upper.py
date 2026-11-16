"""Galea upperworks and full-cycle clearance check (all dimensions in 0.1 m cells)."""
import json
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt

D = Path(__file__).resolve().parent
OUT = D / "masks" / "upper"
YC = 160
STROKE, DIP = 10, 8
PIVOT_Y, PIVOT_Z = 35, 30
INBOARD, OUTBOARD, BLADE_DROP = 30, 86, 20
PITCH = 12
GRIPS = np.array([10, 16, 22, 28])
SHOT = np.empty((560, 321, 55), dtype=bool)


def write(name, cells):
    path = OUT / (name + ".txt")
    path.write_bytes("".join(f"{x},{y},{z},{c}\n" for (x, y, z), c in sorted(cells.items())).encode())


def design():
    hull = {tuple(a): int(c) for *a, c in np.loadtxt(D / "masks/hull/hull_01.vox.txt", delimiter=",", dtype=int)}
    deck, benches, rails = {}, {}, {}
    width = {}
    for x, y, z in hull:
        if z == 17:
            width[x] = max(width.get(x, 0), abs(y - YC))
    for x in range(57, 466):
        for y in range(YC - width.get(x, 0), YC + width.get(x, 0) + 1):
            if width.get(x, 0) >= 2 and (x, y, 17) not in hull:
                deck[x, y, 17] = 141
        if 84 <= x <= 429:
            for y in range(YC - 3, YC + 4):
                for z in range(18, 21):
                    deck[x, y, z] = 104
    oars = []
    for side in (1, -1):
        xs = range(108 + (PITCH if side < 0 else 0), 397, PITCH)
        for i, x in enumerate(xs, 1):
            for dx in range(-7, 3):
                for dy in range(4, PIVOT_Y):
                    y = YC + side * dy
                    for z in (18, 19):
                        if (x + dx, y, z) not in hull:
                            rails[x + dx, y, z] = 104
            for dy in range(5, 30):
                y = YC + side * dy
                for dx in range(-5, -1):
                    for z in (21, 22):
                        benches[x + dx, y, z] = 141
                if dy in (8, 16, 24, 29):
                    for z in (20,):
                        benches[x - 4, y, z] = 104
            oars.append(dict(name=f"oar-{'S' if side > 0 else 'P'}{i:02}", side=side, x=x,
                             pivot=[x + .5, YC + side * PIVOT_Y + .5, PIVOT_Z + .5],
                             blade=[x + .5, YC + side * (PIVOT_Y + OUTBOARD) + .5, PIVOT_Z - BLADE_DROP + .5],
                             seat=[x - 3.5, YC + side * (PIVOT_Y - 10) + .5, 23.5]))
        for x in range(101, 405):
            for dy in (34, 35, 36):
                for z in range(20, 28):
                    rails[x, YC + side * dy, z] = 104
            if x % 12 in (0, 1):
                for dy in range(24, 35):
                    rails[x, YC + side * dy, 18] = 104
    # Join occasional non-tapered strips to the hull without touching another child.
    for p in list(rails):
        if p in hull or p in deck:
            del rails[p]
    for p in list(benches):
        if p in hull or p in deck or p in rails:
            del benches[p]
    if set(deck) & set(hull):
        raise ValueError("upper deck overlaps hull")
    return hull, dict(deck=deck, benches=benches, rails=rails), oars


def phase_points(phase, radial, angle=STROKE):
    yaw = -np.radians(angle) * np.cos(phase)
    lift = np.radians(DIP) * max(0, -np.sin(phase))
    height = -BLADE_DROP / OUTBOARD * radial
    y = np.cos(lift) * radial - np.sin(lift) * height
    z = np.sin(lift) * radial + np.cos(lift) * height
    return np.stack((-np.sin(yaw) * y, np.cos(yaw) * y, z), axis=-1)


def verify(full, oars, blocker=False):
    occupied = np.zeros_like(SHOT)
    positions = np.array(list(full))
    occupied[tuple(positions.T)] = True
    if blocker:
        occupied[108, 204, 29:35] = True
    # Clearance of centers, minus 0.87 cell from a grid-center distance to a solid cell face/corner.
    distance = distance_transform_edt(~occupied)
    support_ok = 0
    crew = []
    for row in oars:
        x, y, z = row["seat"]
        for i in range(4):
            cy = int(y - row["side"] * i * 6)
            if occupied[int(x), cy, 22] and not occupied[int(x), cy, 23:37].any():
                support_ok += 1
            crew.append((x, cy + .5, row["side"], row["pivot"][0]))
    minimum_wood = 1e9
    minimum_people = 1e9
    minimum_shafts = 1e9
    max_reach = 0
    min_bench_gap = 1e9
    travel = np.arange(-INBOARD, OUTBOARD + .25, .25)
    piv = np.array([row["pivot"] for row in oars])
    signs = np.array([row["side"] for row in oars])
    bench_xy = np.array([[c[0], c[1]] for c in crew]).reshape(-1, 4, 2)
    for phase in np.linspace(0, 2 * np.pi, 360, endpoint=False):
        center = phase_points(phase, travel)
        world = center[None, :, :] * np.stack([np.ones_like(signs), signs, np.ones_like(signs)], axis=1)[:, None, :] + piv[:, None, :]
        grid = np.floor(world).astype(int)
        sampled = distance[tuple(grid.reshape(-1, 3).T)].reshape(grid.shape[:2])
        # Shaft has a half-width of 0.6 cell; distal blade has a two-cell height.
        allowance = np.where(travel >= 71, 1.3, .6) + 1.02
        minimum_wood = min(minimum_wood, float((sampled - allowance).min()))
        hand = phase_points(phase, -GRIPS)
        hands = hand[None, :, :] * np.stack([np.ones_like(signs), signs, np.ones_like(signs)], axis=1)[:, None, :] + piv[:, None, :]
        # Torso stays 0.4 m behind its grip and follows hand motion, with a 0.42 m diameter.
        body_xy = hands[:, :, :2].copy()
        body_xy[:, :, 0] -= 4
        max_reach = max(max_reach, float(np.linalg.norm(body_xy - bench_xy, axis=2).max()))
        bodies = body_xy.reshape(-1, 2)
        person_dist = np.linalg.norm(bodies[:, None, :] - bodies[None, :, :], axis=2)
        np.fill_diagonal(person_dist, np.inf)
        minimum_people = min(minimum_people, float(person_dist.min() - 4.2))
        # Infinite shaft lines over-approximate finite shafts: same-side shafts are parallel.
        direction = center[-1, :2] - center[0, :2]
        direction /= np.linalg.norm(direction)
        normal = np.stack((signs * direction[1], np.full(len(signs), -direction[0])), axis=1)
        dist = np.abs(np.einsum("sri,si->sr", bodies[None, :, :] - piv[:, None, :2], normal))
        same_side = signs[:, None] == np.repeat(signs, 4)[None, :]
        minimum_shafts = min(minimum_shafts, float((dist[same_side] - 2.7).min()))
        min_bench_gap = min(min_bench_gap, float(PITCH * abs(direction[1]) - 1.2))
    return dict(oars=len(oars), seats=support_ok, phases=360, stroke_deg=STROKE, dip_deg=DIP,
                min_wood_bound_mm=round(minimum_wood * 100, 1), min_body_gap_mm=round(minimum_people * 100, 1),
                min_shaft_to_body_mm=round(minimum_shafts * 100, 1), min_adjacent_shafts_mm=round(min_bench_gap * 100, 1),
                max_body_shift_mm=round(max_reach * 100, 1))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hull, items, oars = design()
    combined = hull | items["deck"] | items["benches"] | items["rails"]
    stats = verify(combined, oars, "--probe" in sys.argv)
    print(json.dumps(stats))
    if "--probe" in sys.argv:
        assert stats["min_wood_bound_mm"] < 0, stats
        return
    assert stats["seats"] == 196 and min(stats[k] for k in ("min_wood_bound_mm", "min_body_gap_mm", "min_shaft_to_body_mm", "min_adjacent_shafts_mm")) > 0, stats
    assert stats["max_body_shift_mm"] < 590, stats
    oar = {}
    for y in range(INBOARD + OUTBOARD + 1):
        height = round(23 - (y - INBOARD) * BLADE_DROP / OUTBOARD)
        oar[6, y, height] = 141
        if y > INBOARD + 70:
            oar[6, y, height - 1] = 141
    for name, cells in items.items():
        write(name, cells)
    write("oar", oar)
    stats["parts"] = {name: len(cells) for name, cells in items.items()} | {"oar": len(oar)}
    (D / "oar_layout.json").write_text(json.dumps(oars, indent=2) + "\n")
    (D / "verify_upper.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
