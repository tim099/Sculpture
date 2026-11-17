"""Install the barca's generated assemblies through the Sculpture CLI."""
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
        sculpt("work", sub="create", id=work, title=f"比塞大 barque {title}", size=size, parent_work=HULL, tags="sub")
    if json.loads((folder / "work.json").read_text(encoding="utf-8-sig")).get("meters_per_voxel") != .1:
        sculpt("work", sub="update", work=work, meters_per_voxel=.1)
    if not any((folder / "events").rglob("*.json")):
        mask = DESIGN / "masks" / f"{name}.txt"
        sculpt("stampvox", work=work, voxels=mask, at=(0,0,0), expect_pixels=mask.read_bytes().count(b"\n"))
    return work


def link(work, name, source, meta):
    if name not in entries(work, "links"):
        sculpt("work", sub="link", work=work, name=name, source_work=source, at=(0,0,0), meta=meta)


def model(work, name, source, at, pivot, meta, scale=1):
    if name not in entries(work, "models"):
        sculpt("work", sub="model", work=work, name=name, source_work=source, at=at, pivot=pivot, scale=scale, meta=meta)


def anchor(work, name, point):
    found = entries(work, "anchors").get(name)
    if found is None:
        sculpt("work", sub="anchor", work=work, name=name, at=point)
    elif tuple(found["at"]) != tuple(point):
        raise ValueError((work, name, found["at"], point))


def build_decks():
    for name, title, deck, level, floor in (
        ("hold", "底艙地板", "hold", 0, "72:3,155:3"),
        ("deck", "裝卸主甲板", "main", 1, "62:17,180:17"),
        ("aft-deck", "旅客艉平台", "aft", 2, "56:23,85:23"),
    ):
        part = component(name, title)
        link(ASSEMBLY, name, part, dict(kind="deck", name=title, deck=deck, level=level, floor=floor, thick=1))
    for name, title, ends, points in (
        ("hold-ladder", "貨艙梯", "hold,main", ((102,36,3),(104,36,4),(121,36,16),(123,36,17))),
        ("aft-ladder", "艉平台梯", "main,aft", ((96,36,17),(94,36,18),(85,36,23),(83,36,23))),
    ):
        part = component(name, title)
        for suffix, p in zip(("foot","lo","hi","head"), points):
            anchor(part, f"access.{suffix}", p)
        link(ASSEMBLY, name, part, {"kind":"ladders", "access.decks":ends})
    link(ASSEMBLY, "coaming", component("coaming", "貨艙口圍板"), {})
    print("Three decks and two ladders linked", flush=True)


def build_ends():
    link(ASSEMBLY, "ends", component("ends", "艏喙與艉欄"), {})
    hatch = component("hatch", "貨艙艙蓋", (17,15,3))
    anchor(hatch, "hinge-a", (0,0,0))
    anchor(hatch, "hinge-b", (16,0,0))
    model(f"{HULL}-deck", "cargo-hatch", hatch, (105,29,16), (0,0,0), dict(kind="door", open="up", open_deg=105))
    model(ASSEMBLY, "passenger-shelter", component("shelter", "旅客遮篷與座椅"), (0,0,0), (0,0,0), dict(deco=1))
    model(ASSEMBLY, "cargo-boxes", component("cargo", "艙內箱具"), (0,0,0), (0,0,0), dict(deco=1))
    print("Open cargo hatch, passenger shelter and cargo installed", flush=True)


if __name__ == "__main__":
    build_decks()
    build_ends()
