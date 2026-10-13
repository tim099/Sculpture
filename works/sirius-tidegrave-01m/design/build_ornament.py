"""Original ghost-ship ornament: branching stern crown, arch & aged growth.
Movie model observations inform motifs; coordinates and emblem are new design.
"""
import math,json
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFont
from build_structure import cli,get_actual,ROOT,WORK,BASE
from build_decks import ensure,stamp,ASSEMBLY
from build_guns import composed
from build_rig import linevox
from draft_general import CY,width,top
def main():
    occ=composed();a=np.zeros((800,241,240),np.uint8);bone=218;sea=77
    # Curving cantilever galleries, three tiers; railing spindles on each semicircle.
    galleries=[]
    for z,rx,ry in [(105,24,38),(138,28,39),(164,27,34)]:
        cx=112
        for x in range(cx-rx,cx+1):
            for y in range(CY-ry,CY+ry+1):
                if ((x-cx)/rx)**2+((y-CY)/ry)**2<=1:a[x,y,z:z+2]=145
        pts=[(cx-rx*math.cos(t),CY+ry*math.sin(t),z+12) for t in np.linspace(-math.pi/2,math.pi/2,101)]
        for p,q in zip(pts,pts[1:]):linevox(a,p,q,1.5,bone)
        for t in np.linspace(-math.pi/2,math.pi/2,21):
            x=cx-rx*math.cos(t);y=CY+ry*math.sin(t);linevox(a,(x,y,z+2),(x,y,z+12),1.3,bone)
        galleries.append({'z':z,'center_x':cx,'rx':rx,'ry':ry})
    # Gothic frame behind the narrow high stern; keeps open negative space.
    for side in (-1,1):
        linevox(a,(94,CY+side*17,139),(94,CY+side*17,183),2.0,bone)
        linevox(a,(94,CY+side*17,183),(94,CY+side*8,202),2.0,bone)
        linevox(a,(94,CY+side*8,202),(94,CY,213),2.0,bone)
    # Broken astrolabe ring, no pre-existing movie crest copied.
    angles=np.linspace(0,2*math.pi,181)
    for t,u in zip(angles,angles[1:]):
        if 4.15<(t+u)/2<5.275:continue
        linevox(a,(92,CY+14*math.cos(t),188+14*math.sin(t)),(92,CY+14*math.cos(u),188+14*math.sin(u)),1.3,bone)
    linevox(a,(92,CY-17,181),(92,CY+17,181),1.0,sea)
    for t in np.linspace(0,2*math.pi,9)[:-1]:
        if 4.15<t<5.275:continue
        linevox(a,(92,CY,188),(92,CY+10*math.cos(t),188+10*math.sin(t)),.8,145)
    # Coral crown: three forked limbs per side, visually open rather than solid box.
    for sg in (-1,1):
        p=(94,CY+sg*26,164);mid=(90,CY+sg*32,190);end=(88,CY+sg*42,224)
        linevox(a,p,mid,2.2,bone);linevox(a,mid,end,1.6,bone)
        for z,dy in [(184,34),(198,37),(211,40)]:
            root=(90,CY+sg*(26+(z-164)*.27),z)
            linevox(a,root,(84,CY+sg*(dy+10),z+15),1.2,bone)
            linevox(a,root,(91,CY+sg*(dy-8),z+13),1.1,bone)
        # Under-crown support root lands on the gallery floor.
        linevox(a,(94,CY+sg*26,139),(94,CY+sg*26,165),1.6,bone)
    # Finial row climbs above the stern silhouette.
    for i in range(9):
        y=CY-24+i*6;z=196+round(12*(1-abs(y-CY)/24))
        linevox(a,(101,y,183),(101,y,z),1.3,bone)
    # Flag staff with real deck footing, not a free-floating cloth attachment.
    linevox(a,(105,CY,165),(105,CY,207),1.1,109)
    # Raised beakhead swept rails with hooked, toothlike terminal spikes.
    for sg in (-1,1):
        pts=[(570,CY+sg*round(width(570,150)-1),150),(602,CY+sg*20,158),(637,CY+sg*15,170),(680,CY+sg*5,180)]
        for p,q in zip(pts,pts[1:]):linevox(a,p,q,2.1,bone)
        for i,x in enumerate((602,620,637,653)):
            y=CY+sg*(20-i*4);z=158+i*5
            linevox(a,(x,y,z),(x+8,y+sg*3,z+15),1.5,bone)
            linevox(a,(x,y,z),(x+9,y,z-17),1.5,bone)
        linevox(a,(620,CY+sg*3,134),(656,CY+sg*3,134),1.7,109)
    linevox(a,(645,CY,134),(645,CY,158),2.1,109)
    # Original tide-watcher rostrum: a narrow open jaw, with two sockets.
    linevox(a,(643,CY,155),(663,CY,163),3.5,bone)
    for sg in (-1,1):
        linevox(a,(650,CY+sg*4,160),(670,CY+sg*3,170),1.7,bone)
        linevox(a,(650,CY+sg*4,156),(670,CY+sg*2,157),1.7,bone)
        a[651:656,CY+sg*3:CY+sg*3+1,160:163]=36
    # Surface growth: low-profile ribs/lumps attached to the original hull skin.
    for x in range(152,565,19):
        for z in (35,43,56,94):
            w=width(x,z)
            if w<8:continue
            for sg in (-1,1):
                y=CY+sg*math.floor(w)
                for xx in range(x-1,x+2):
                    for yy in range(min(y,y+sg*2),max(y,y+sg*2)+1):
                        for zz in range(z-1,z+2):a[xx,yy,zz]=sea
    # Rail fins: visible pointed gothic rhythm along the open waist.
    for x in range(260,536,20):
        z=top(x)
        for sg in (-1,1):
            y=CY+sg*math.floor(width(x,z)-1)
            linevox(a,(x,y,z),(x,y,z+7),1.2,bone)
    # Drill stern windows only into the hull; ornate frame remains outside.
    hull=get_actual(BASE);cut={}
    for q,c in hull.items():
        x,y,z=q;dy=abs(y-CY)
        arch=146<=z<=178 and dy<=12 if z<168 else 168<=z<=182 and dy<=max(0,12-(z-168)*.7)
        small=110<=z<=123 and any(abs(y-(CY+v))<=3 for v in (-13,0,13))
        xlim=106 if z>=128 else 100+40*(1-z/128)+6
        if x<=xlim and (arch or small):cut[q]=c
    f=ROOT/'stern_windows_cut.vox.txt';f.write_text(''.join(f'{x},{y},{z},{c}\n' for (x,y,z),c in sorted(cut.items())),encoding='utf-8')
    if cut:cli(op='carvevox',work=BASE,voxels=f,at='0,0,0',expect_pixels=len(cut))
    occ=composed()
    for q in occ:
        if q[2]<240:a[q]=0
    # Small closed ornament voids are solidified, then exclude the original ship again.
    closed=ndimage.binary_fill_holes(a>0)&(a==0)
    for q in np.argwhere(closed):
        if tuple(q) not in occ:a[tuple(q)]=bone
    name=BASE+'-ornament';ensure(name,'潮墓號｜艉廊、破星盤與珊瑚冠');now=stamp(name,a,'ornament')
    cli(op='work',sub='link',work=ASSEMBLY,name='海蝕裝飾',source_work=name,at='0,0,0',overwrite=1)
    # Exact construction projections plus annotated views of new ornament.
    from build_structure import sheet
    # only low 200 rows for generic sheet; tall ornament has own full image below
    proj=a.max(axis=0).T[::-1];rgb=np.zeros((*proj.shape,3),np.uint8);rgb[:]=(16,38,48);m=proj>0;v=proj[m]
    rgb[m]=np.stack([((v>>5)&7)*255/7,((v>>2)&7)*255/7,(v&3)*255/3],axis=1).astype(np.uint8)
    Image.fromarray(rgb).save(ROOT/'ornament_stern_cell_plan.png')
    (ROOT/'ornament_plan.json').write_text(json.dumps({'galleries':galleries,'window_hull_carved':len(cut),'new_voxels':len(now),'motif_sources':'D23 model bow and stern personally viewed; broken astrolabe designed by Sirius','palette':{'bone':218,'growth':77}},indent=2)+'\n',encoding='utf-8')
    cli(op='stats',work=ASSEMBLY,structure=1,mirror='y:120')
    for label,yaw,pitch in [('stern',150,18),('bow',-30,15),('whole',45,18)]:
        cli(op='view',work=ASSEMBLY,yaw=yaw,pitch=pitch,skybox='none',width=1600,height=1100,out=WORK/'overlays'/f'ornament_{label}.png')
    print('ornament',len(now),'windows carve',len(cut),flush=True)
if __name__=='__main__':main()
