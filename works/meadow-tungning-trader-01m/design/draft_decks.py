"""Decks, watertight-style bulkheads and three working access stairs.

Derived from meadow-bizerte-barque-01m/design/apply_parts.py and its hull envelope.
All exact positions are design decisions recorded here and in plan.json.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from draft_hull import CENTER, DESIGN, PLAN, SIZE, X_RANGE, shell
from sculpt_cli import ASSEMBLY, HULL, WORKS, anchor, component, link, sculpt

WOOD, TRIM = 177, 104
TITLES = {"hold": "底艙貨艙甲板", "main": "主甲板", "poop": "尾樓甲板", "fore": "艏平台"}
STAIRS = {
    "hold": {"decks": "hold,main", "foot": (160, 90, 8), "head": (160, 60, 48),
             "direction": (0, -1), "steps": 14, "run": 2, "rise": 3, "half": 3},
    "poop": {"decks": "main,poop", "foot": (113, 98, 48), "head": (86, 98, 72),
             "direction": (-1, 0), "steps": 8, "run": 3, "rise": 3, "half": 3},
    "poop-P": {"decks": "main,poop", "foot": (113, 62, 48), "head": (86, 62, 72),
               "direction": (-1, 0), "steps": 8, "run": 3, "rise": 3, "half": 3},
    "fore": {"decks": "main,fore", "foot": (289, 80, 48), "head": (300, 80, 56),
             "direction": (1, 0), "steps": 3, "run": 3, "rise": 3, "half": 3}
}


def read_cells(path):
    return {(x,y,z): c for x,y,z,c in (map(int, r.split(",")) for r in Path(path).read_text().splitlines() if r and r[0].isdigit())}


def write_mask(name, cells):
    path = DESIGN / "masks" / f"{name}.txt"
    path.write_text("".join(f"{x},{y},{z},{c}\n" for (x,y,z),c in sorted(cells.items())), encoding="ascii", newline="\n")


def draft():
    solid, _ = shell()
    occupied = read_cells(DESIGN / "hull.vox.txt")
    masks = {}

    def inside(p):
        x,y,z = p
        return (x in X_RANGE and 0 <= y < SIZE[1] and 0 <= z < solid.shape[2] and solid[x-X_RANGE.start,y,z])

    def add(cells, p, color=WOOD):
        if p not in occupied and inside(p):
            cells[p] = color

    for name, spec in PLAN["decks"].items():
        cells = {}
        floor = spec["floor"]
        for x in range(spec["span"][0],spec["span"][1]+1):
            for y in range(SIZE[1]):
                for z in range(floor-spec["thick"],floor):
                    # Precise upper half of the hold stair well, matched to treads.
                    if name == "main" and 157 <= x <= 163 and 62 <= y <= 73:
                        continue
                    if name == "main" and 178 <= x <= 198 and 86 <= y <= 100:
                        continue
                    add(cells, (x,y,z))
        masks[f"deck-{name}"] = cells
        occupied.update(cells)

    walls = {}
    for x in PLAN["bulkheads"]:
        for y in range(SIZE[1]):
            for z in range(8,45):
                if abs(y-CENTER) <= 4 and z < 29:
                    continue
                add(walls, (x,y,z), TRIM)
    # Front wall and windowed transom of the stern accommodation.
    for x in (53,91):
        for y in range(CENTER-25,CENTER+26):
            for z in range(48,69):
                door = x == 91 and (abs(y-CENTER)<=4 or 95<=y<=101 or 59<=y<=65) and z < 69
                window = x == 53 and (CENTER-18<=y<=CENTER-10 or CENTER+10<=y<=CENTER+18) and 56<=z<=64
                if not door and not window:
                    add(walls, (x,y,z), TRIM)
    # Side partitions leave a central cabin aisle around the mizzen heel.
    for y in (CENTER-6,CENTER+6):
        for x in range(54,88):
            for z in range(48,69):
                if not (76<=x<=84 and z<68):
                    add(walls,(x,y,z),TRIM)
    masks["bulkheads"] = walls
    occupied.update(walls)

    stairs_meta = {}
    for name, spec in STAIRS.items():
        cells = {}
        fx,fy,fz = spec["foot"]
        dx,dy = spec["direction"]
        top = spec["head"][2]
        step_points = []
        for i in range(spec["steps"]):
            z = min(top-1,fz+(i+1)*spec["rise"]-1)
            for run in range(spec["run"]):
                x = fx + dx*(2+i*spec["run"]+run)
                y = fy + dy*(2+i*spec["run"]+run)
                for w in range(-spec["half"],spec["half"]+1):
                    p = (x-dy*w,y+dx*w,z)
                    if p not in occupied:
                        cells[p] = TRIM
                # Continuous side stringers join every tread and support the rails.
                for w in (-4,4):
                    for rz in range(fz-1,z+2):
                        p=(x-dy*w,y+dx*w,rz)
                        if p not in occupied:
                            cells[p]=TRIM
                step_points.append((x,y,z+1))
        # Guard rails are outside the standing width.
        for i,p in enumerate(step_points):
            x,y,z = p
            for w in (-5,5):
                for rz in range(z,z+8):
                    if i%spec["run"]==0 or rz>=z+6:
                        p = (x-dy*w,y+dx*w,rz)
                        if p not in occupied:
                            cells[p] = TRIM
        masks[f"ladder-{name}"] = cells
        occupied.update(cells)
        stairs_meta[name] = dict(foot=spec["foot"],lo=step_points[0],hi=step_points[-1],head=spec["head"],decks=spec["decks"])

    # A coaming for the cargo loading opening. It has an individual opening cover.
    coaming = {}
    for x in range(177,200):
        for y in range(85,102):
            if x in (177,199) or y in (85,101):
                for z in (48,49):
                    add(coaming,(x,y,z),TRIM)
    masks["coaming"] = coaming
    for name, cells in masks.items():
        write_mask(name,cells)
    (DESIGN / "ladder_points.json").write_text(json.dumps(stairs_meta,indent=2)+"\n",encoding="utf-8")
    report = {name: len(cells) for name,cells in masks.items()}
    report["overlapping_cells"] = sum(map(len,masks.values())) - len(set().union(*(set(v) for v in masks.values())))
    assert report["overlapping_cells"] == 0
    (DESIGN / "verify_decks.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report),flush=True)


def install():
    for name,spec in PLAN["decks"].items():
        work = component(f"deck-{name}",TITLES[name])
        a,b = spec["span"]
        floor = spec["floor"]
        link(ASSEMBLY,f"deck-{name}",work,dict(kind="deck",deck=name,name=TITLES[name],level=spec["level"],floor=f"{a}:{floor},{b}:{floor}",thick=spec["thick"]))
    walls = component("bulkheads","橫隔艙壁與船員艙")
    link(f"{HULL}-deck-hold","bulkheads",walls,{})
    sculpt("work",sub="meta",work=f"{HULL}-deck-hold",part="link",name="bulkheads",meta={"kind":None})
    for name,deck,low,high,door in (
        ("cargo","hold",(177,72,8),(190,86,42),(174,80,8)),
        ("crew","main",(72,88,48),(85,98,68),(80,86,48))
    ):
        room = f"{HULL}-room-{name}"
        if not (WORKS/room/"work.json").exists():
            sculpt("work",sub="create",id=room,title=f"東寧三桅洋船 {name} 房間標記",parent_work=HULL,size=SIZE,tags="sub")
            sculpt("work",sub="update",work=room,meters_per_voxel=.1)
        for suffix,point in (("min",low),("max",high),("door",door)):
            anchor(room,f"{name}.{suffix}",point)
        link(f"{HULL}-deck-{deck}",f"room-{name}",room,{"kind":"rooms"})
    stairs = json.loads((DESIGN/"ladder_points.json").read_text())
    for name,spec in stairs.items():
        work = component(f"ladder-{name}",f"{name} 交通梯")
        for suffix in ("foot","lo","hi","head"):
            anchor(work,f"access.{suffix}",spec[suffix])
        link(ASSEMBLY,f"ladder-{name}",work,{"kind":"ladders","access.decks":spec["decks"]})
    link(ASSEMBLY,"coaming",component("coaming","貨艙口圍板"),{})
    print("Four decks, eight bulkheads, crew cabins and four stairs installed",flush=True)


if __name__ == "__main__":
    import sys
    if "--apply" in sys.argv:
        install()
    else:
        draft()
