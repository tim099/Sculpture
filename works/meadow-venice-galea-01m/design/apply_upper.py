"""Apply a verified galley stage through the Sculpture CLI."""
import json
from pathlib import Path
import subprocess
import sys

DESIGN = Path(__file__).resolve().parent
HULL = DESIGN.parent.name
ASM = HULL + "-assembly"


def cli(op, **args):
    command = ["senate", "cmd", "sculpture", "--arg", "op=" + op, "--arg", "persona=meadow"]
    for key, value in args.items():
        if isinstance(value, dict):
            value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        command.extend(("--arg", f"{key}={value}"))
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"{command!r}\n{result.stdout}")
    return result.stdout


def coords(values):
    return ",".join(map(str, values))


def component(suffix, title, path, size):
    work = HULL + "-" + suffix
    where = DESIGN.parent.parent / work
    if not (where / "work.json").exists():
        cli("work", sub="create", id=work, title=title, size=coords(size), parent_work=HULL, tags="sub")
    cli("work", sub="update", work=work, meters_per_voxel=.1, tags="sub")
    count = len(path.read_text().splitlines())
    if not list((where / "events").rglob("*.json")):
        cli("stampvox", work=work, voxels=path, at="0,0,0", expect_pixels=count)
    return work


def link(work, name, part, at="0,0,0", meta=None):
    kw = dict(sub="link", work=work, name=name, source_work=part, at=at)
    if meta:
        kw["meta"] = meta
    cli("work", **kw)


def anchor(work, name, at):
    cli("work", sub="anchor", work=work, name=name, at=coords(at))


def upper():
    masks = DESIGN / "masks" / "upper"
    for part, title in (("deck", "主甲板與中央走道"), ("benches", "划凳"), ("rails", "舷外槳架")):
        work = component(part, "威尼斯 galea " + title, masks / (part + ".txt"), (560, 321, 50))
        meta = dict(kind="deck", deck="main", level=0, floor="57:18,465:18", thick=1,
                    walk="84:21,429:21", walk_y="157:163") if part == "deck" else None
        link(ASM, part, work, meta=meta)
        print(part, "linked", flush=True)
    oar = component("oar", "威尼斯 galea 四人共用長槳", masks / "oar.txt", (9, 118, 33))
    for name, point in (("pivot", (6, 30, 23)), ("blade", (6, 116, 3)), ("seat", (2, 20, 16))):
        anchor(oar, name, point)
    rows = json.loads((DESIGN / "oar_layout.json").read_text())
    for placement in rows:
        right = placement["side"] == 1
        cli("work", sub="model", work=HULL + "-rails", name=placement["name"], source_work=oar,
            at=coords(placement["pivot"]), pivot="6.5,30.5,23.5", scale=1, mirror="none" if right else "y",
            meta=dict(kind="oar", rowers=4, side="S" if right else "P", stroke_deg=10, dip_deg=8))
    print(len(rows), "oar models", flush=True)


if __name__ == "__main__":
    upper()
