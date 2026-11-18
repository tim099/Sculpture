"""Fit twelve 6-pound guns and four swivel guns with geometric clearance.

Uses gunsim.py from kaguya-shachuan-01m/design/gunsim.py. The same source
6-pound gun is reused at its recorded physical scale, with no calibre substitution.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from draft_hull import CENTER, DESIGN, PLAN, X_RANGE, shell
from draft_decks import read_cells
from gunsim import Grid, Gun
from rig import standing_cells
from sculpt_cli import ASSEMBLY, HULL, WORKS, anchor, entries, model, sculpt


def source(name,work,pivot,meta,extra=None):
    cells=read_cells(DESIGN/"references"/f"{name}.txt")
    if extra:
        cells.update(read_cells(DESIGN/"references"/extra))
    points={a["name"]:a["at"] for a in json.loads((WORKS/work/"anchors.json").read_text(encoding="utf-8-sig"))["anchors"]}
    return Gun(name,{"work":work,"pivot":pivot,"scale":.5,"meta":meta},list(cells),points,.15)


def draft():
    used=standing_cells()
    hull=read_cells(DESIGN/"hull.vox.txt")
    for mast in PLAN["rig"]:
        used.update(read_cells(DESIGN/"masks"/f"mast-{mast}.txt"))
    grid=Grid(list(used),outside=False)
    solid,_=shell()
    long=source("gun6l","summit-stormkaap-01m-gun-6l",(8.5,13,0),{"kind":"gun","gun":"6l"})
    swivel=source("pierrier","apex-one-reale-01m-gun-pierrier",(5.5,18.5,0),
                  {"kind":"gun","gun":"pierrier","mount":"turret","arc":"-80,80","rate":45},"pierrier-mount.txt")
    placements=[]
    for number,x in enumerate(PLAN["guns"]["long6_x"],1):
        for sign,side in ((-1,"P"),(1,"S")):
            found=None
            for d in np.arange(42,0,-.25):
                at=(x+.5,CENTER+.5+sign*d,48)
                if grid.hit(long.world(long.samples,at,0,side=="P")).any():
                    continue
                muzzle=long.world(long.anchors["muzzle"][None],at,0,side=="P")[0]
                ys=np.flatnonzero(solid[int(muzzle[0])-X_RANGE.start,:,int(muzzle[2])])
                if len(ys) and abs(muzzle[1]-CENTER-.5)<max(abs(ys-CENTER))+1:
                    continue
                bottom=long.world(long.bottom,at,0,side=="P")
                bottom[:,2]-=.6
                support=float(grid.hit(bottom).mean())
                if support<.65:
                    continue
                ray=muzzle+np.array([0,sign,0])*np.linspace(.1,12,30)[:,None]
                if grid.hit(ray).any():
                    continue
                found=dict(name=f"long6-{side}{number:02d}",deck="main",work=long.work,at=at,pivot=long.pivot.tolist(),scale=.5,
                           mirror="y" if side=="P" else "",meta=long.meta,collisions=0,support=round(support,3),muzzle=muzzle.tolist())
                break
            if not found:
                raise ValueError((x,side,"6-pound gun cannot fit"))
            placements.append(found)
    for x in PLAN["guns"]["swivel_x"]:
        deck="poop" if x<100 else "fore"
        top=max(z for px,y,z in hull if px==x and y>CENTER+5)
        ys=[y for px,y,z in hull if px==x and z==top and y>CENTER]
        y=max(ys)
        for side,sign in (("P",-1),("S",1)):
            at=(x+.5,CENTER+.5+sign*(y-CENTER-.5),top+1)
            angles=list(range(-80,81,5))
            collisions=sum(int(grid.hit(swivel.world(swivel.samples,at,angle,side=="P")).sum()) for angle in angles)
            if collisions:
                raise ValueError((x,side,collisions,"swivel sweep hits hull"))
            placements.append(dict(name=f"swivel-{x}-{side}",deck=deck,work=swivel.work,at=at,pivot=swivel.pivot.tolist(),scale=.5,
                                   mirror="y" if side=="P" else "",meta=swivel.meta,collisions=0,sweep_angles=angles))
    (DESIGN/"guns_placement.json").write_text(json.dumps(placements,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"guns":len(placements),"collisions":sum(p["collisions"] for p in placements),"minimum_long_gun_support":min(p["support"] for p in placements if "support" in p)}),flush=True)


def install():
    placements=json.loads((DESIGN/"guns_placement.json").read_text())
    for p in placements:
        host=f"{HULL}-deck-{p['deck']}"
        model(host,p["name"],p["work"],p["at"],p["pivot"],p["meta"],scale=p["scale"],mirror=p["mirror"])
        if p["meta"]["gun"]=="pierrier":
            model(host,p["name"]+"-mount",p["work"]+"-mount",p["at"],p["pivot"],
                  {"kind":"gunmount","mount_of":f"deck-{p['deck']}/{p['name']}"},scale=p["scale"],mirror=p["mirror"])
    print("12 six-pound long guns and 4 paired swivels installed",flush=True)


if __name__=="__main__":
    if "--apply" in sys.argv:
        install()
    else:
        draft()
