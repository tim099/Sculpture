"""Three balanced junk sails and working yard bindings.

Derived from meadow-bizerte-barque-01m/design/rig.py and
kaguya-shachuan-01m/design/draft_masts.py. Batten lines are painted into the
sail texture so they fold with the cloth in every sail setting.
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parent))
from draft_hull import CENTER, DESIGN, PLAN
from draft_decks import read_cells, write_mask
from sculpt_cli import ASSEMBLY, HULL, anchor, component, coords, entries, link, model, sculpt

ROWS=[]


def rope(name,start,end,kind,sail=None,slack=1):
    if name not in entries(ASSEMBLY,"ropes"):
        sculpt("work",sub="rope",work=ASSEMBLY,name=name,**{"from":start,"to":end},
               thickness=.35,color="#493e2e" if kind=="shroud" else "#a28c63",slack=slack,
               group="standing" if kind in ("shroud","stay") else "running")
    meta={"kind":kind}
    if sail:
        meta["sail"]=sail
    ROWS.append(("rope",name,meta))


def standing_cells():
    cells=read_cells(DESIGN/"hull.vox.txt")
    for name in ("deck-hold","deck-main","deck-poop","deck-fore","bulkheads","ladder-hold","ladder-poop","ladder-poop-P","ladder-fore","coaming","stern-glass"):
        cells.update(read_cells(DESIGN/"masks"/f"{name}.txt"))
    return cells


def build_masts():
    used=standing_cells()
    placements={}
    for name,spec in PLAN["rig"].items():
        x,heel,top = (spec[k] for k in ("x","heel","top"))
        cells={}
        for z in range(heel,top+1):
            radius=spec["radius"]*(1-.62*(z-heel)/(top-heel))
            for dx in range(-4,5):
                for dy in range(-4,5):
                    p=(x+dx,CENTER+dy,z)
                    if dx*dx+dy*dy<=radius*radius and p not in used:
                        cells[p]=104
        for dx in range(-12,13):
            for dy in range(-12,13):
                if dx*dx+dy*dy<=144:
                    for z in (top-12,top-11):
                        p=(x+dx,CENTER+dy,z)
                        if p not in used:
                            cells[p]=104
        write_mask(f"mast-{name}",cells)
        mast=component(f"mast-{name}",f"{name} 桅與工作平台")
        anchor(mast,"hound",(x,CENTER,top-7))
        anchor(mast,"head-P",(x,CENTER-5,top-10))
        anchor(mast,"head-S",(x,CENTER+5,top-10))
        for position,kind in (("upper","gaff"),("lower","boom")):
            lower=spec["aft"]+(12 if position=="upper" else 0)
            upper=spec["fore"]-(8 if position=="upper" else 0)
            length=upper-lower
            peak=12 if position=="upper" else 2
            front=2
            pivot_x=2-lower
            pivot_z=round(peak+(front-peak)*(-lower)/length)
            yard_cells={}
            for lx in range(2,length+3):
                z=round(peak+(front-peak)*(lx-2)/length)
                for y in (1,2):
                    for dz in (0,1):
                        yard_cells[lx,y,z+dz]=136
            label=f"yard-{name}-{position}"
            write_mask(label,yard_cells)
            source=component(label,f"{name} 硬篷{position}桁",(length+5,7,peak+5))
            points={"pivot":(pivot_x,3,pivot_z),"earing-aft":(2,1,peak),"earing-fore":(length+2,1,front),"sling":(pivot_x,1,pivot_z)}
            for key,point in points.items():
                anchor(source,key,point)
            z=spec["upper_z"]-round(10*(-lower)/length) if position=="upper" else spec["lower_z"]
            meta=dict(kind="yard",mast=name,yard=kind,sail=f"{name}-junk",pivot_anchor="pivot",turn_axis="z",rotate_z_deg=0,
                      length_ft=round(length*.1/.3048,2),diameter_in=7 if name=="main" else 5)
            model(mast,f"yard-{position}",source,(x+.5,CENTER+.5,z+.5),tuple(v+.5 for v in points["pivot"]),meta)
            placements[f"{name}-{position}"]={"at":[x+.5,CENTER+.5,z+.5],"pivot":points["pivot"],"span_cells":length}
        link(ASSEMBLY,f"mast-{name}",mast,{"kind":"mast","mast":name})
        print(f"Mast and two yards installed: {name}",flush=True)
    (DESIGN/"yards_placement.json").write_text(json.dumps(placements,indent=2)+"\n",encoding="utf-8")


def sail_texture(name,count):
    folder=DESIGN/"textures"
    folder.mkdir(exist_ok=True)
    image=Image.new("RGB",(128,128),"#c9b18b")
    d=ImageDraw.Draw(image)
    for y in range(1,128,4):
        d.line((0,y,127,y),fill="#c5aa80")
    for x in range(3,128,8):
        d.line((x,0,x,127),fill="#c3a77c")
    for i in range(count+1):
        y=round(i*127/count)
        d.line((0,y,127,y),fill="#735e3c",width=2)
    d.rectangle((0,0,127,127),outline="#6a553a",width=2)
    path=folder/f"{name}-battens.png"
    image.save(path)
    return path


def build_sails():
    hull=read_cells(DESIGN/"hull.vox.txt")
    used=standing_cells()
    channel_cells={}
    support_points={}
    for name,spec in PLAN["rig"].items():
        x=spec["x"]
        z=77 if name=="mizzen" else 54
        for i,dx in enumerate((-8,8),1):
            for sign,side in ((-1,"P"),(1,"S")):
                px=x+dx
                ys=[p[1] for p in hull if p[0]==px and p[2]==z]
                if not ys:
                    raise ValueError((name,px,z,"missing hull support"))
                y=max(ys) if sign>0 else min(ys)
                for ox in (-1,0,1):
                    for oy in range(1,4):
                        p=(px+ox,y+sign*oy,z)
                        if p not in used:
                            channel_cells[p]=104
                support_points[f"{name}-{side}{i}"]=(px,y+sign*2,z)
    write_mask("channels",channel_cells)
    channels=component("channels","桅索舷側繫索木架")
    link(ASSEMBLY,"channels",channels,{})
    for key,point in support_points.items():
        anchor(channels,key,point)

    for name,spec in PLAN["rig"].items():
        mast=f"mast-{name}"
        sail=f"{name}-junk"
        upper=f"model:{mast}/yard-upper/"
        lower=f"model:{mast}/yard-lower/"
        if sail not in entries(ASSEMBLY,"sails"):
            sculpt("work",sub="sail",work=ASSEMBLY,name=sail,
                   corners=f"{upper}earing-aft|{upper}earing-fore|{lower}earing-fore|{lower}earing-aft",
                   corner_names="peak|throat|tack|clew",bind="0,1,2,3",color="#ffffff",fullness=1.025,res=24,
                   texture=sail_texture(name,spec["battens"]))
        ROWS.append(("sail",sail,{"kind":"sail","mast":name,"sail":"gaff","set":spec["set"]}))
        for side in ("P","S"):
            for i in (1,2):
                rope(f"{name}-{side}{i}",f"channels/{name}-{side}{i}",f"{mast}/hound","shroud")
            ratname=f"{name}-ratlines-{side}"
            data=json.loads((DESIGN.parent.parent/ASSEMBLY/"ropes.json").read_text(encoding="utf-8-sig"))
            level=72 if name=="mizzen" else 48
            sign=-1 if side=="P" else 1
            foot=(spec["x"]+8,CENTER+sign*(15 if name=="mizzen" else 22 if name=="fore" else 26),level)
            old=next((e for e in data.get("ratlines",[]) if e.get("name")==ratname),None)
            if old is None or old.get("foot")!=coords(foot):
                sculpt("work",sub="ratlines",work=ASSEMBLY,name=ratname,rope_a=f"{name}-{side}1",rope_b=f"{name}-{side}2",
                       step=4,start=5,stop=12,min_span=4,thickness=.25,color="#493e2e",group="ratlines",climb=1,
                       foot=coords(foot),head=f"{mast}/head-{side}",overwrite=1)
        # Halyards and sheet have explicit moving model endpoints and sail ownership.
        rope(f"{sail}-halyard",f"{mast}/hound",upper+"sling","halyard",sail)
        tie=f"{name}-sheet"
        level=72 if name=="mizzen" else 48
        deck=f"{HULL}-deck-{'poop' if name=='mizzen' else 'main'}"
        anchor(deck,tie,(spec["x"]-12,CENTER-18,level-1))
        rope(f"{sail}-sheet",lower+"earing-aft",f"deck-{'poop' if name=='mizzen' else 'main'}/{tie}","sheet",sail,1.02)
        print(f"Sail, batten texture and shrouds installed: {name}",flush=True)

    # The red ensign is a designed ship flag, with UVs for nation replacement.
    mast=f"{HULL}-mast-main"
    anchor(mast,"flag-upper",(194,CENTER,294))
    anchor(mast,"flag-lower",(194,CENTER,286))
    flag=Image.new("RGB",(64,32),"#a82522")
    paint=ImageDraw.Draw(flag)
    paint.rectangle((0,0,63,31),outline="#d5ba67",width=2)
    path=DESIGN/"textures/ensign.png"
    flag.save(path)
    sculpt("work",sub="sail",work=ASSEMBLY,name="tungning-ensign",
           corners="mast-main/flag-upper|174,80,294|174,80,286|mast-main/flag-lower",
           corner_names="hoist|fly-top|fly-bottom|foot",bind=3,free="fly-top,fly-bottom",texture=path,color="#ffffff",fullness=1.03,res=10,overwrite=1)
    ROWS.append(("sail","tungning-ensign",{"kind":"flag","flag":"ensign","nation":"tungning"}))
    path=DESIGN/"rig_meta.tsv"
    path.write_text("".join(f"{part}\t{name}\t{json.dumps(meta)}\n" for part,name,meta in ROWS),encoding="utf-8")
    sculpt("work",sub="meta",work=ASSEMBLY,file=path)
    sculpt("work",sub="wind",work=ASSEMBLY,wind="4.5,-1.5,0",sail_seconds=3)
    print(sculpt("work",sub="ropecheck",work=ASSEMBLY),flush=True)


if __name__=="__main__":
    if "--sails" in sys.argv:
        build_sails()
    else:
        build_masts()
