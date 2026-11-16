"""Place the Galea's game-only bow battery and below-deck magazine."""
import json
from pathlib import Path

from apply_rig import entries, ensure_anchor, mask
from apply_upper import ASM, HULL, cli, component, coords, link
from verify_assembly import read

D = Path(__file__).resolve().parent
OUT = D / "masks" / "armament"
FLOOR = 28
CENTER = 160
LIGHT = HULL + "-falcone-6-veneto"
KEG = "basecamp-frigate-constitution-01m-powder-barrel"
SIZE = (560, 321, 55)
GUNS = [
    ("corsiero", "corsiero", 422, 0, "ven50", 6.5, 9, 1),
    ("falcone-P1", LIGHT, 415, -17, "ven6", 6.5, 5, .5),
    ("falcone-S1", LIGHT, 415, 17, "ven6", 6.5, 5, .5),
    ("falcone-P2", LIGHT, 443, -14, "ven6", 6.5, 5, .5),
    ("falcone-S2", LIGHT, 443, 14, "ven6", 6.5, 5, .5),
]


def armament():
    source = [D / "masks/hull/hull_01.vox.txt"]
    source += [D / "masks/upper" / f"{n}.txt" for n in ("deck", "benches", "rails")]
    source += [D / "masks/rig" / f"{n}-mast.txt" for n in ("main", "fore")]
    source += [D / "masks/ends" / f"{n}.txt" for n in ("bow", "stern")]
    solid = {}
    for path in source:
        solid.update(read(path))
    battery = {}
    # Keep a flat platform aft of the bow rails, with a short midline approach.
    for x in range(399, 467):
        half = 17 if x < 405 else 24 - max(0, x - 454)
        for y in range(CENTER - half, CENTER + half + 1):
            battery[x, y, FLOOR - 1] = 141
            old_half = 24 - max(0, x - 435) // 2
            if 405 <= x < 456 and abs(y - CENTER) in (half,old_half):
                for z in range(FLOOR - 5, FLOOR):
                    battery[x, y, z] = 104
    for x in range(401,405):
        for y in range(151,170):
            z = 21 + (x - 400)
            for zz in range(18, z + 1):
                battery[x, y, zz] = 104
    for x in (409, 432, 450, 460):
        for y in range(144,177,4):
            for z in range(18, FLOOR-1):
                if abs(y - CENTER) <= 24-max(0,x-435)//2:
                    battery[x, y, z] = 104
    # The small locker sits under the weather deck. Leave its aft doorway open.
    magazine = {}
    for x in range(414,437):
        for y in range(152,169):
            for z in range(4,17):
                floor = z == 4
                wall = y in (152,168) or x in (414,436)
                doorway = x == 414 and 157 <= y <= 163 and z >= 5
                if floor or (wall and not doorway):
                    magazine[x,y,z] = 141 if floor else 104
    battery = {p:c for p,c in battery.items() if p not in solid}
    magazine = {p:c for p,c in magazine.items() if p not in solid}
    return battery, magazine


def corsiero():
    # Bronze silhouette on a low wheel-less slide. Nominal scale is game art.
    voxels = {}
    for y in range(2,29):
        for x in range(13):
            for z in range(3):
                if x in (1,2,10,11) or y % 6 in (1,2):
                    voxels[x,y,z] = 104
        for x in (3,4,8,9):
            for z in range(3,9):
                if 7 <= y <= 26:
                    voxels[x,y,z] = 141
    for y in range(5,35):
        radius = 3.0 if y < 14 or y in (33,34) else 2.25
        for x in range(13):
            for z in range(6,13):
                dist2 = (x-6)**2 + (z-9)**2
                if dist2 <= radius**2 and (y < 31 or dist2 > 1):
                    voxels[x,y,z] = 168 if y not in (9,14,26,33) else 208
    voxels[6,3,9] = voxels[6,4,9] = 168
    return voxels


def build():
    from apply_anchor_and_guns import prepare_light_gun

    prepare_light_gun()
    battery, magazine = armament()
    for name, title, cells, dim in (
        ("battery", "威尼斯 galea 艏砲台", battery, SIZE),
        ("magazine", "威尼斯 galea 艏部彈藥庫", magazine, SIZE),
        ("corsiero", "威尼斯 50 磅艏中線重砲與滑座", corsiero(), (13,37,15)),
    ):
        path = OUT / f"{name}.txt"
        mask(path, cells)
        component(name, title, path, dim)
    bow = HULL + "-battery"
    locker = HULL + "-magazine"
    cannon = HULL + "-corsiero"
    for name, xyz in (("muzzle",(6,34,9)),("breech",(6,7,9)),("cascabel",(6,3,9))):
        ensure_anchor(cannon, name, xyz)
    cli("work", sub="meta", part="work", work=cannon, meta={"kind":"gun","gun":"ven50"})
    for name, xyz in (("blast",(425,160,8)),("door",(414,160,4))):
        ensure_anchor(locker, name, xyz)
    for i, xyz in enumerate(((420.5,155.5,5),(420.5,164.5,5),(430.5,155.5,5),(430.5,164.5,5)),1):
        name = f"keg-{i}"
        if name not in entries(locker, "models"):
            cli("work", sub="model", work=locker, name=name, source_work=KEG, at=coords(xyz),
                pivot="11,11,0", scale=.2, meta={"kind":"powder","powder_lb":100})
    for name, source, x, dy, code, pivot_x, recoil, scale in GUNS:
        pos = (x,CENTER+.5+dy,FLOOR)
        old = entries(bow, "models").get(name)
        if old is None or tuple(old["at"]) != pos or old["meta"].get("gun") != code:
            meta = dict(old["meta"]) if old else {"kind":"gun","gun":code,"recoil":recoil}
            meta["gun"] = code
            cli("work", sub="model", work=bow, name=name, source_work=cannon if source=="corsiero" else source,
                at=coords(pos), pivot=coords((pivot_x,0,0)), rotate="0,0,-90",
                scale=scale, meta=meta, overwrite=1)
    if "battery" not in entries(ASM, "links"):
        link(ASM, "battery", bow)
    cli("work", sub="meta", work=ASM, part="link", name="battery",
        meta={"kind":None,"deck":None,"level":None,"name":None,"floor":None,"thick":None})
    cli("work", sub="meta", work=ASM, part="link", name="deck",
        meta={"floor":"57:18,397:18,405:28,466:28","walk":"84:21,398:21"})
    if "magazine" not in entries(ASM, "links"):
        link(ASM, "magazine", locker, meta={"kind":"magazine","powder_lb":400})
    details = {"game_models": len(GUNS), "floor": FLOOR, "magazine_kegs":4,
        "cells":{"battery":len(battery),"magazine":len(magazine)},
        "historical_choices":{"centre":"50 Venetian libbre","outer":"four falconi of 6 Venetian libbre"},
        "runtime_guns":{"centre":"ven50","outer":"ven6"},
        "sources":["https://hrcak.srce.hr/en/file/167349",
                   "https://www.locusglobus.it/documenti/lingua/Fabio-Mutinelli-Lessico-Veneto-Andreola-Venezia-1851.pdf",
                   "https://www.storiamediterranea.it/wp-content/uploads/mediterranea/p2477/b1661.pdf"]}
    (D / "armament_design.json").write_text(json.dumps(details,indent=2)+"\n",encoding="utf8")
    print(cli("work", sub="ropecheck", work=ASM))


if __name__ == "__main__":
    build()
