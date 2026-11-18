"""Magazine, deck equipment, opening doors, steering and anchors.

CLI patterns and shared equipment derive from meadow-bizerte-barque-01m/design/rig.py.
The perforated Chinese rudder and its tiller are designed for this ship.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from draft_hull import CENTER, DESIGN, PLAN, X_RANGE, shell
from draft_decks import read_cells, write_mask
from rig import standing_cells
from sculpt_cli import ASSEMBLY, HULL, anchor, component, entries, link, model, sculpt


def equipment():
    used=standing_cells()
    solid,_=shell()
    magazine={}
    for x in range(119,146):
        for y in range(69,92):
            for z in range(8,33):
                if y in (69,91) or z==32:
                    if z==32 and 131<=x<=133 and 79<=y<=81:
                        continue
                    p=(x,y,z)
                    if p not in used and solid[x-X_RANGE.start,y,z]:
                        magazine[p]=104
    write_mask("magazine",magazine)
    mag=component("magazine","底艙後彈藥庫")
    anchor(mag,"blast",(132,80,20))
    anchor(mag,"door",(146,80,8))
    link(f"{HULL}-deck-hold","magazine",mag,{"kind":"magazine","pos":"aft","powder_lb":800,
         "hoist":"ladder-hold#access"})
    ladders=entries(ASSEMBLY,"links")
    hoists=",".join(ladders[k].get("meta",{}).get("id",k)+"#access" for k in ("ladder-hold","ladder-poop","ladder-poop-P","ladder-fore"))
    sculpt("work",sub="meta",work=f"{HULL}-deck-hold",part="link",name="magazine",meta={"hoist":hoists})
    for i,(x,y) in enumerate(( (x,y) for x in (123,129,135,141) for y in (74,86) ),1):
        model(mag,f"powder-{i:02d}","basecamp-frigate-constitution-01m-powder-barrel",(x+.5,y+.5,8),(11,11,0),
              {"kind":"powder","powder_lb":100},scale=.2)

    # One reusable door slab, referenced at all eight bulkheads and the cabin entrance.
    door_cells={(0,y,z):104 if z not in (4,16) else 36 for y in range(11) for z in range(22)}
    write_mask("bulkhead-door",door_cells)
    door=component("bulkhead-door","通用隔艙門（0.1 m）",(3,11,22))
    anchor(door,"hinge-a",(0,0,0))
    anchor(door,"hinge-b",(0,0,21))
    sculpt("work",sub="meta",work=door,part="work",meta={"kind":"door","open":"side"})
    for x in PLAN["bulkheads"]:
        model(f"{HULL}-deck-hold",f"bulkhead-door-{x}",door,(x+1,75,8),(0,0,0),{"kind":"door","open":"side","open_deg":100})
    model(f"{HULL}-deck-main","cabin-door",door,(92,75,48),(0,0,0),{"kind":"door","open":"side","open_deg":100})

    for name,size,at in (("cargo-hatch",(23,17,2),(177,85,50)),("stair-hatch",(9,14,2),(156,61,48))):
        w,h,t=size
        cells={(x,y,z):104 if y%5==0 else 177 for x in range(w) for y in range(h) for z in range(t)}
        write_mask(name,cells)
        cover=component(name,"貨艙蓋" if name=="cargo-hatch" else "底艙梯口艙蓋",size)
        anchor(cover,"hinge-a",(0,0,0))
        anchor(cover,"hinge-b",(w-1,0,0))
        model(f"{HULL}-deck-main",name,cover,at,(0,0,0),{"kind":"door","open":"up","open_deg":100})

    for deck,name,source,at,pivot,scale,meta in (
        ("main","boat","basecamp-ember-01m-boat",(250.5,80.5,48),(90,26,0),.22,{"kind":"boat","boat":"cutter","length_m":4}),
        ("main","capstan","basecamp-ember-01m-capstan",(110.5,80.5,48),(40,40,0),.12,{"kind":"capstan"}),
        ("poop","binnacle","summit-night-falcon-01m-binnacle",(78.5,80.5,72),(9,13,0),.2,{"kind":"binnacle"}),
        ("main","galley","kaguya-gloire-01m-galley",(177.5,61.5,48),(22,16,0),.3,{"kind":"galley"}),
        ("poop","stern-lantern","gura-tridente-01m-lantern",(49.5,95.5,72),(8,8,0),.35,{"kind":"light","light_color":"#ffae52"}),
    ):
        model(f"{HULL}-deck-{deck}",name,source,at,pivot,meta,scale=scale)
    # A restrained cargo display and sleeping berths are optional decorations.
    furniture={}
    for x0,y0,w,d,h in ((75,89,16,6,5),(98,72,10,9,8),(206,72,12,7,6)):
        z0=48 if x0==75 else 8
        for x in range(x0,x0+w):
            for y in range(y0,y0+d):
                for z in range(z0,z0+h):
                    furniture[x,y,z]=104 if z in (z0,z0+h-1) else 136
    write_mask("furniture",furniture)
    work=component("furniture","船員鋪位與貨箱")
    model(ASSEMBLY,"furniture",work,(0,0,0),(0,0,0),{"deco":1})
    print("Magazine with eight barrels, doors, hatches, boat and working deck equipment installed",flush=True)


def helm():
    rudder={}
    for z in range(3,77):
        for y in range(79,82):
            for x in range(32,35):
                rudder[x,y,z]=104
        if z<=38:
            aft=19+max(0,12-z)//3
            for x in range(aft,33):
                # Four small diamond perforations leave continuous webs.
                hole=min(abs(x-hx)+abs(z-hz) for hx,hz in ((24,12),(29,20),(24,28),(29,34)))<=2
                if not hole:
                    for y in range(79,82):
                        rudder[x,y,z]=104 if z%9 else 36
    write_mask("rudder",rudder)
    work=component("rudder","通用中式開孔舵（0.1 m）")
    anchor(work,"stock-top",(33,80,75))
    meta=dict(kind="rudder",hinge_x=33.5,hinge_y=80.5,hinge_z=3.5,axis_x=0,axis_y=0,axis_z=1,max_deg=35,turn_axis="hinge",
              spin="rudder",spin_k=35,spin_min=-35,spin_max=35,spin_lag=.3)
    sculpt("work",sub="meta",work=work,part="work",meta=meta)
    model(ASSEMBLY,"rudder",work,(0,0,0),(0,0,0),meta)
    tiller={}
    for x in range(33,62):
        for y in range(79,82):
            for z in (75,76):
                tiller[x,y,z]=104 if x<57 else 36
    write_mask("tiller",tiller)
    work=component("tiller","絞舵舵柄")
    anchor(work,"spin-a",(33,80,75))
    anchor(work,"spin-b",(33,80,76))
    rudder_id=entries(ASSEMBLY,"models")["rudder"].get("meta",{}).get("id","rudder")
    model(f"{HULL}-deck-poop","tiller",work,(0,0,0),(0,0,0),
          dict(kind="tiller",rudder=rudder_id,spin="rudder",spin_k=35,spin_min=-35,spin_max=35,spin_lag=.3))

    used=standing_cells()
    gear={}
    hull=read_cells(DESIGN/"hull.vox.txt")
    for side,sign in (("P",-1),("S",1)):
        for x in range(319,326):
            for y in range(80,113):
                for z in (62,63):
                    p=(x,80+sign*(y-80),z)
                    if p not in used:
                        gear[p]=104
        candidates=[p for p in hull if p[0]==325 and p[2]==60 and sign*(p[1]-80)>0]
        point=max(candidates,key=lambda p:sign*(p[1]-80))
        anchor(HULL,f"hawse-{side}",point)
    write_mask("anchor-gear",gear)
    work=component("anchor-gear","艏部吊錨架")
    link(ASSEMBLY,"anchor-gear",work,{})
    for side,sign in (("P",-1),("S",1)):
        model(work,f"anchor-{side}","basecamp-frigate-constitution-01m-anchor",(322.5,80.5+sign*31,64),
              (23.5,16.5,57.5),{"kind":"anchor","anchor":"bower","material":"iron"},scale=.5)
    sculpt("work",sub="meta",work=ASSEMBLY,part="link",name="hull",meta={"kind":"ship","waterline_z":PLAN["dimensions"]["waterline_z"]})
    print("Perforated rudder, tiller and two bower anchors installed",flush=True)


if __name__=="__main__":
    if "--helm" in sys.argv:
        helm()
    else:
        equipment()
