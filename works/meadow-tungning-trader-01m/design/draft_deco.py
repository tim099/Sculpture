"""The ship's own bow eyes, wave painting, lion and flower-and-bird stern.

Geometry and Sculpture CLI patterns derive from meadow-bizerte-barque-01m/design.
Artwork is designed for this ship. No historical identity is implied.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0,str(Path(__file__).resolve().parent))
from draft_hull import CENTER, DESIGN, PLAN, X_RANGE, shell
from draft_decks import read_cells, write_mask
from sculpt_cli import ASSEMBLY, HULL, anchor, component, entries, link, model, sculpt


def draft():
    solid, original = shell(cutouts=False)
    old = {(int(x)+X_RANGE.start,int(y),int(z)):int(original[x,y,z]) for x,y,z in np.argwhere(original>0)}
    glass = {p:155 for p in old if p[0]<60 and 60<=p[2]<=66 and (62<=p[1]<=72 or 88<=p[1]<=98)}
    write_mask("stern-glass",glass)
    write_mask("window-cut",{p:old[p] for p in glass})
    bow = {}
    for x in range(306,333):
        for z in range(49,65):
            ys = np.flatnonzero(solid[x-X_RANGE.start,:,z])
            if not len(ys):
                continue
            y = int(ys.max())+1
            eye = ((x-320)/6)**2 + ((z-57)/3)**2
            if eye <= 1:
                bow[x,y,z] = 36 if eye<.23 else 255
            elif z == 51+round(1.5*math.sin((x-306)*.6)):
                bow[x,y,z] = 255
            elif z == 63 and 309<=x<=323:
                bow[x,y,z] = 160
    # A small carved lion face above the painted eye.
    for x in range(305,314):
        for z in range(59,66):
            ys = np.flatnonzero(solid[x-X_RANGE.start,:,min(z,62)])
            if len(ys) and ((x-309)/4.5)**2+((z-62)/3.5)**2<=1:
                y=int(ys.max())+2
                bow[x,y,z] = 216
                if (x,z) in ((307,63),(311,63),(309,61)):
                    bow[x,y+1,z] = 36
    write_mask("bow-deco",bow)
    stern={}
    for y in range(57,104):
        for z in range(69,79):
            xs=np.flatnonzero(solid[:,y,min(z,77)])
            if not len(xs):
                continue
            x=int(xs.min())+X_RANGE.start-1
            color=160
            if z in (69,78) or y in (57,103):
                color=216
            # Branch, flowers and two birds form the tailboard relief.
            if z == 72+round(1.5*math.sin((y-57)/7)):
                color=216
            if min((y-65)**2+(z-75)**2,(y-95)**2+(z-75)**2)<=4:
                color=255 if z==75 else 216
            if ((y in (73,74,86,87) and z==75) or (y in (72,75,85,88) and z==76)):
                color=255
            stern[x,y,z]=color
    write_mask("stern-deco",stern)
    plaque=Image.new("1",(33,13))
    draw=ImageDraw.Draw(plaque)
    font=ImageFont.truetype("C:/Windows/Fonts/msjh.ttc",11)
    draw.text((0,-2),"東寧",font=font,fill=1)
    board={}
    for y in range(33):
        for z in range(13):
            board[0,y,z]=216 if plaque.getpixel((y,12-z)) else 36
    write_mask("nameboard",board)
    shrine={}
    for x in range(9):
        for y in range(9):
            for z in range(15):
                frame = z in (0,1,12,13) or (x==0 and z<13) or (y in (0,8) and z<13)
                statue = 3<=x<=5 and 3<=y<=5 and 2<=z<=10
                if frame or statue:
                    shrine[x,y,z]=216 if statue else 160
    write_mask("shrine",shrine)
    print(json.dumps({"glass":len(glass),"bow":len(bow),"stern":len(stern),"nameboard":len(board),"shrine":len(shrine)}),flush=True)


def install():
    expected = read_cells(DESIGN / "masks/window-cut.txt")
    target = DESIGN / "actual/hull-before-windows.txt"
    target.parent.mkdir(exist_ok=True)
    sculpt("export",work=HULL,format="list",out=target)
    actual=read_cells(target)
    remove={p:c for p,c in expected.items() if p in actual}
    if remove:
        path=DESIGN/"masks/window-remove.txt"
        path.write_text("".join(f"{x},{y},{z},{c}\n" for (x,y,z),c in sorted(remove.items())),encoding="ascii")
        sculpt("carvevox",work=HULL,voxels=path,at=(0,0,0),expect_pixels=len(remove))
    glass=component("stern-glass","尾樓窗玻璃")
    link(ASSEMBLY,"stern-glass",glass,{"material":"glass"})
    component("bow-deco","獅面、艏眼與浪花彩繪")
    # The final physical bow is installed by fittings_voxels.py after gear.py.
    stern=component("stern-deco","尾樓花鳥飾板")
    model(ASSEMBLY,"stern-carving",stern,(0,0,0),(0,0,0),{"deco":1})
    board=component("nameboard","東寧名牌",(2,33,13))
    model(ASSEMBLY,"nameboard",board,(26.5,64,67),(0,0,0),{"deco":1})
    shrine=component("shrine","媽祖神龕",(12,12,18))
    model(f"{HULL}-deck-poop","mazu-shrine",shrine,(74,87,72),(0,0,0),{"deco":1})
    print("Own bow and stern artwork, glass windows, name and shrine installed",flush=True)


if __name__=="__main__":
    if "--apply" in sys.argv:
        install()
    else:
        draft()
