"""Check actual assembled timber and oar transforms after rig installation."""
import json
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import binary_fill_holes, distance_transform_edt, label

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))

from draft_upper import verify

WORKS = D.parent.parent
NAME = D.parent.name


def read(path):
    a = np.loadtxt(path, delimiter=",", dtype=int, ndmin=2)
    return {tuple(p): int(c) for *p, c in a}


def rotate(points, phase, sign, stroke, dip):
    yaw = -sign * np.deg2rad(stroke) * np.cos(phase)
    lift = sign * np.deg2rad(dip) * max(0, -np.sin(phase))
    x, y, z = points.T
    y, z = np.cos(lift) * y - np.sin(lift) * z, np.sin(lift) * y + np.cos(lift) * z
    return np.stack([np.cos(yaw)*x - np.sin(yaw)*y, np.sin(yaw)*x+np.cos(yaw)*y, z], axis=-1)


def main():
    assembled = read(Path(sys.argv[1]))
    sources = [D / "masks" / "hull" / "hull_01.vox.txt"]
    sources += [D / "masks" / "upper" / (part + ".txt") for part in ("deck", "rails", "benches")]
    sources += [D / "masks" / "rig" / (name + "-mast.txt") for name in ("main", "fore")]
    interior = "--interior" in sys.argv
    if "--ends" in sys.argv or "--armament" in sys.argv or interior:
        sources += [D / "masks" / "ends" / (name + ".txt") for name in ("bow", "stern")]
    if "--armament" in sys.argv or interior:
        sources += [D / "masks" / "armament" / (name + ".txt") for name in ("battery", "magazine")]
    fittings = D / "masks" / "interior"
    if interior:
        sources += [D / "masks" / "armament" / "anchor-fittings.txt"]
        sources += [fittings / f"{name}.txt" for name in ("hold-floor", "hold-stores", "hold-ladder")]
    cut = (read(fittings / "access-opening.txt") | read(fittings / "hold-headroom.txt")) if interior else {}
    expected = {}
    for src in sources:
        data = read(src)
        if interior and src == D / "masks" / "upper" / "deck.txt":
            assert all(data.pop(p) == c for p,c in cut.items())
        assert not (expected.keys() & data.keys()), src
        expected.update(data)
    assert assembled == expected
    rows = json.loads((D / "oar_layout.json").read_text())
    models = json.loads((WORKS / (NAME + "-rails") / "models.json").read_text())["models"]
    assert len(models) == 49
    actual_oar = read(Path(sys.argv[2]))
    assert actual_oar == read(D / "masks" / "upper" / "oar.txt")
    points = np.array(list(actual_oar), float) + .5
    info = {r["name"]: r for r in rows}
    occupied = np.zeros((560, 321, 55), dtype=bool)
    occupied[tuple(np.array([p for p in assembled if p[2] < 55]).T)] = True
    if interior:
        gear = read(fittings / "stores-and-aft-fittings.txt")
        gear.update({(x+210,y+155,z+21):c for (x,y,z),c in read(fittings / "hold-hatch.txt").items()})
        occupied[tuple(np.array(list(gear)).T)] = True
    distance = distance_transform_edt(~occupied)
    worst = 1e9
    for m in models:
        r = info[m["name"]]
        assert m["at"] == r["pivot"] and m["scale"] == [1, 1, 1] and m["rotate"] == [0, 0, 0]
        assert m["enabled"] and m["meta"]["rowers"] == 4
        sign = r["side"]
        assert m["mirror"] == ("" if sign == 1 else "y")
        local = (points - np.array(m["pivot"])) * [1, sign, 1]
        for phase in np.linspace(0, 2*np.pi, 360, endpoint=False):
            world = rotate(local, phase, sign, m["meta"]["stroke_deg"], m["meta"]["dip_deg"]) + m["at"]
            cells = np.floor(world).astype(int)
            # Query shift to nearest center, oar cube radius and unsampled angular motion.
            bound = float(distance[tuple(cells.T)].min()) - 2 * np.sqrt(3) / 2 - .20
            worst = min(worst, bound)
    assert worst > 0, worst
    stats = verify({p: c for p, c in assembled.items() if p[2] < 55}, rows)
    assert stats["seats"] == 196 and stats["min_body_gap_mm"] > 0
    stats["assembled_timber_voxels"] = len(assembled)
    stats["each_oar_model_voxels"] = len(actual_oar)
    stats["min_actual_oar_to_timber_bound_mm"] = round(worst * 100, 1)
    if interior:
        shape = np.array(list(assembled))
        lo, hi = shape.min(axis=0), shape.max(axis=0)
        timber = np.zeros(tuple(hi-lo+3),dtype=bool)
        timber[tuple((shape-lo+1).T)] = True
        stats["timber_components"] = int(label(timber)[1])
        stats["enclosed_air_cells"] = int(binary_fill_holes(timber).sum()-timber.sum())
    (D / ("verify_handover.json" if interior else "verify_armament_clearance.json" if "--armament" in sys.argv else "verify_ends.json" if "--ends" in sys.argv else "verify_assembly.json")).write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
