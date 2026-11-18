"""Sculpture CLI helpers, derived from meadow-bizerte-barque-01m/design/apply_parts.py."""
import json
import subprocess

from draft_hull import DESIGN, SIZE

HULL = DESIGN.parent.name
ASSEMBLY = f"{HULL}-assembly"
WORKS = DESIGN.parent.parent


def coords(values):
    return ",".join(str(v) for v in values)


def sculpt(op, **args):
    command = ["senate", "cmd", "sculpture", "--arg", f"op={op}", "--arg", "persona=meadow"]
    for key, value in args.items():
        if isinstance(value, dict):
            value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        if isinstance(value, (tuple, list)):
            value = coords(value)
        command.extend(("--arg", f"{key}={value}"))
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"{command!r}\n{result.stdout}")
    return result.stdout


def entries(work, kind):
    path = WORKS / work / f"{kind}.json"
    return {e["name"]: e for e in json.loads(path.read_text(encoding="utf-8-sig"))[kind]} if path.exists() else {}


def component(name, title, size=SIZE):
    work = f"{HULL}-{name}"
    folder = WORKS / work
    if not (folder / "work.json").exists():
        sculpt("work", sub="create", id=work, title=f"東寧三桅洋船 {title}", size=size, parent_work=HULL, tags="sub")
    if json.loads((folder / "work.json").read_text(encoding="utf-8-sig")).get("meters_per_voxel") != .1:
        sculpt("work", sub="update", work=work, meters_per_voxel=.1)
    mask = DESIGN / "masks" / f"{name}.txt"
    sync_mask(work,mask)
    return work


def sync_mask(work, mask):
    name=work.removeprefix(HULL).lstrip("-") or "hull"
    folder=WORKS/work
    expected = read_cells(mask)
    current = {}
    if any((folder / "events").rglob("*.json")):
        target = DESIGN / "actual" / f"{name}.txt"
        target.parent.mkdir(exist_ok=True)
        sculpt("export", work=work, format="list", out=target, links="none")
        current = read_cells(target)
    extra = {p:c for p,c in current.items() if p not in expected or expected[p] != c}
    missing = {p:c for p,c in expected.items() if p not in current or current[p] != c}
    for op,cells,suffix in (("carvevox",extra,"remove"),("stampvox",missing,"add")):
        if cells:
            delta = DESIGN / "masks" / f"{name}-{suffix}.txt"
            delta.write_text("".join(f"{x},{y},{z},{c}\n" for (x,y,z),c in sorted(cells.items())),encoding="ascii")
            result = sculpt(op, work=work, voxels=delta, at=(0,0,0), expect_pixels=len(cells))
            import re
            placed = re.search(r"placed\s*=\s*(\d+)", result)
            if placed is None or int(placed.group(1)) != len(cells):
                raise RuntimeError(result)


def read_cells(path):
    return {(x,y,z):c for x,y,z,c in (map(int,line.split(",")) for line in path.read_text(encoding="utf-8-sig").splitlines() if line[:1].isdigit())}


def link(work, name, source, meta):
    if name not in entries(work, "links"):
        sculpt("work", sub="link", work=work, name=name, source_work=source, at=(0,0,0), meta=meta)


def model(work, name, source, at, pivot, meta, scale=1, rotate=(0,0,0), mirror=""):
    found=entries(work,"models").get(name)
    if found:
        meta={**found.get("meta",{}),**meta}
    sculpt("work", sub="model", work=work, name=name, source_work=source, at=at, pivot=pivot, scale=scale,
           rotate=rotate, mirror=mirror or "none",meta=meta,overwrite=1)


def anchor(work, name, point):
    found = entries(work, "anchors").get(name)
    if found is None:
        sculpt("work", sub="anchor", work=work, name=name, at=point, overwrite=1)
    elif tuple(found["at"]) != tuple(point):
        sculpt("work", sub="anchor", work=work, name=name, at=point, overwrite=1)

