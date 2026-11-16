"""Install Venetian-calibre game components and put the four-fluke anchors aboard."""
import json
from pathlib import Path

from apply_armament import GUNS, FLOOR, CENTER, OUT, LIGHT
from apply_rig import entries, ensure_anchor, mask
from apply_upper import ASM, HULL, cli, component, coords, link
from verify_assembly import read

D = Path(__file__).resolve().parent
ANCHOR = "kotoko-fusta-01m-anchor-grapnel"


def light_gun():
    # Voxel silhouette and visual game carriage in the same placement envelope.
    cells = {}
    for y in range(1, 36):
        for x in (1,2,3,9,10,11):
            for z in range(0, 11):
                if z < 3 or (8 <= y <= 26 and z <= 8 + (x in (3,9))):
                    cells[x,y,z] = 104 if z < 8 else 141
    for y in range(3, 45):
        rad = 2.6 if y in (*range(3,12), 13, 25, 42, 43, 44) else 1.8
        for x in range(13):
            for z in range(11,18):
                r = (x-6)**2 + (z-14)**2
                if r <= rad**2 and not (y>=41 and r<1):
                    cells[x,y,z] = 208 if y in (7,13,25,43) else 168
    return cells


def anchor_fittings():
    occupied = set()
    masks = [D / "masks/hull/hull_01.vox.txt"]
    masks += [D / "masks/ends" / f"{name}.txt" for name in ("bow","stern")]
    masks += [OUT / f"{name}.txt" for name in ("battery","magazine")]
    for p in masks:
        occupied.update(read(p))
    cells = {}
    for sign in (-1,1):
        for x in range(457,461):
            for y in range(18,26):
                for z in range(26 + max(0,y-19)//2, 34):
                    p = (x,CENTER+sign*y,z)
                    if p not in occupied:
                        cells[p] = 104 if z < 33 else 141
    return cells


def prepare_light_gun():
    falcon_name = LIGHT
    path = OUT / "falcone-6-veneto.txt"
    mask(path, light_gun())
    component("falcone-6-veneto", "威尼斯 6 磅 falcone（0.05 m 遊戲元件）", path, (13,46,20))
    cli("work",sub="update", work=falcon_name, meters_per_voxel=.05)
    for name, point in (("muzzle",(6,44,14)),("breech",(6,5,14)),("cascabel",(6,3,14))):
        ensure_anchor(falcon_name,name,point)
    cli("work",sub="meta",part="work",work=falcon_name,meta={"kind":"gun","gun":"ven6"})


def apply():
    prepare_light_gun()
    cli("work",sub="meta",part="work",work=HULL+"-corsiero",meta={"kind":"gun","gun":"ven50"})
    host = HULL + "-battery"
    for name, source, x, dy, code, pivot, _, scale in GUNS:
        old = entries(host, "models")[name]
        if old["meta"]["gun"] == code:
            continue
        meta = old["meta"] | {"gun":code}
        if name == "corsiero":
            cli("work",sub="meta",part="model",work=host,name=name,meta={"gun":code})
        else:
            cli("work",sub="model",work=host,name=name,source_work=source,
                at=coords((x,CENTER+.5+dy,FLOOR)),pivot=coords((pivot,0,0)),
                rotate="0,0,-90",scale=scale,meta=meta,overwrite=1)

    path = OUT / "anchor-fittings.txt"
    mask(path, anchor_fittings())
    mount = component("anchor-fittings","威尼斯 galea 艏部吊錨木",path,(560,321,55))
    if "anchor-fittings" not in entries(ASM,"links"):
        link(ASM,"anchor-fittings",mount)
    for side, sign in (("P",-1),("S",1)):
        name = f"anchor-{side}"
        hole = (460,CENTER+sign*12,23)
        ensure_anchor(mount,f"hawse-{side}",hole)
        if name not in entries(mount,"models"):
            cli("work",sub="model",work=mount,name=name,source_work=ANCHOR,
                at=coords((458.5,160.5+sign*25,33.5)),pivot="9.5,9.5,23.5",
                rotate=coords((0,0,sign*45)),scale=.65,
                meta={"kind":"anchor","anchor":"bower","hawse":coords(hole)})
    spec = {
        "unit": "Venetian libbra sottile",
        "kg_per_libbra": 0.30122,
        "guns": {
            "veniceCorsiero50": {"code":"ven50","name":"50 威尼斯磅艏主砲（corsiero）","short":"50 威尼斯磅砲",
                                "shot":15.061,"V":178,"reload":1.5,"big":True,"hole":1.22,"crew":7,"min":3,"mass":3.2},
            "veniceFalcone6": {"code":"ven6","name":"6 威尼斯磅輕砲（falcone）","short":"6 威尼斯磅砲",
                              "shot":1.80732,"V":165,"reload":.6,"big":False,"hole":.6,"crew":2,"min":1,"mass":.5},
        },
        "anchor_work":ANCHOR,
        "source": "Walter Panciera, Il governo delle artiglierie, ch. 10; the other numbers are engine tuning.",
    }
    (D / "galea_venetian_guns.json").write_text(json.dumps(spec,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    design_file = D / "armament_design.json"
    design = json.loads(design_file.read_text(encoding="utf-8-sig"))
    design.pop("runtime_proxies", None)
    design["runtime_guns"] = {"centre":"ven50","outer":"ven6"}
    design_file.write_text(json.dumps(design,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(cli("work",sub="ropecheck",work=ASM),flush=True)


if __name__ == "__main__":
    apply()
