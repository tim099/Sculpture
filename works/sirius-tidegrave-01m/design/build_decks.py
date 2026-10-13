import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from draft_general import P,width,CY
from build_structure import cli,get_actual,listfile,ROOT,WORK,BASE
ASSEMBLY=BASE+'-assembly'
def ensure(name,title,parent=BASE,tags='sub'):
    path=WORK.parent/name/'work.json'
    if not path.exists():cli(op='work',sub='create',id=name,title=title,parent_work=parent,size='800,241,640',tags=tags)
    cli(op='work',sub='update',work=name,meters_per_voxel=.1)
def stamp(work,a,label):
    old=get_actual(work);planned={tuple(map(int,q)):int(a[tuple(q)]) for q in np.argwhere(a>0)}
    extra=set(old)-set(planned)
    if extra:
        if not work.endswith('-ladders'):raise RuntimeError(f'{work} contains {len(extra)} unexpected cells')
        path=ROOT/'ladders_revision_remove.vox.txt'
        path.write_text(''.join(f'{x},{y},{z},{old[(x,y,z)]}\n' for x,y,z in sorted(extra)),encoding='utf-8')
        cli(op='carvevox',work=work,voxels=path,at='0,0,0',expect_pixels=len(extra));old=get_actual(work)
    missing=np.zeros_like(a)
    for q,c in planned.items():
        if q in old and old[q]!=c:raise RuntimeError(f'color changed {q}')
        if q not in old:missing[q]=c
    path,n=listfile(missing,label)
    if n:
        v=cli(op='stampvox',work=work,voxels=path,at='0,0,0',expect_pixels=n)
        if int(v.get('placed',-1))!=n:raise RuntimeError(v)
    now=get_actual(work)
    if now!=planned:raise RuntimeError(f'{work} does not match design')
    return now
def draw_plan(a,label):
    # Independent drawable cell plan at z-axis; file contains exact top-projection pixels.
    c=a.max(axis=2).T[::-1];rgb=np.zeros((241,800,3),np.uint8);rgb[:]=(16,38,48);m=c>0;v=c[m]
    rgb[m]=np.stack([((v>>5)&7)*255/7,((v>>2)&7)*255/7,(v&3)*255/3],axis=1).astype(np.uint8)
    Image.fromarray(rgb).save(ROOT/(label+'_cell_plan.png'))
def main():
    ensure(ASSEMBLY,'潮墓號｜完整組裝件',tags='ship')
    cli(op='work',sub='link',work=ASSEMBLY,name='船殼',source_work=BASE,at='0,0,0',overwrite=1,meta=json.dumps({'kind':'ship','waterline_z':52,'crew':300}))
    occupied=get_actual(BASE);reports=[]
    for D in P['decks']:
        ident=D['id'];dz=D['z'];name=BASE+'-deck-'+ident;a=np.zeros((800,241,200),np.uint8)
        for x in range(*[D['x'][0],D['x'][1]+1]):
            for z in range(dz-1,dz+1):
                w=width(x,z)
                if w>0:
                    for y in range(max(0,int(CY-w)),min(241,int(CY+w)+1)):
                        if abs(y-CY)<=w and (x,y,z) not in occupied:a[x,y,z]=136
        # Stacked open central companionways; mast holes reserved all the way down.
        if ident in ('lower','upper','weather'):
            for hx in (290,425):a[hx-18:hx+20,CY-9:CY+10,:]=0
        for m in P['masts']:
            x=m['x'];a[x-5:x+6,CY-5:CY+6,:]=0
        # Upper-level companions align against the step bulkhead and leave landing.
        if ident=='quarter':a[219:240,CY-9:CY+10,:]=0
        if ident=='poop':a[159:180,CY-9:CY+10,:]=0
        if ident=='forecastle':a[550:574,CY-9:CY+10,:]=0
        ensure(name,'潮墓號｜'+ident+'甲板');now=stamp(name,a,'deck_'+ident)
        occupied.update(now);draw_plan(a,'deck_'+ident)
        cli(op='work',sub='link',work=ASSEMBLY,name='甲板-'+ident,source_work=name,at='0,0,0',overwrite=1)
        reports.append({'deck':ident,'surface_z':dz,'cells':len(now),'prior_overlap':0,'result_missing_extra_color':0,'hatches':'open; centre passages and mast holes reserved'})
    # One child for game-visible, connected stairways; rail is timber, ropes added later.
    a=np.zeros((800,241,200),np.uint8);stairs=[]
    # lower->upper & upper->weather via two hatches, plus outside stern/bow stairs.
    specs=[('lower-upper-a',65,90,272,1),('lower-upper-b',65,90,407,1),
           ('upper-weather-a',90,115,272,1),('upper-weather-b',90,115,407,1),
           ('weather-quarter',115,138,219,1),('quarter-poop',138,164,159,1),
           ('weather-forecastle',115,138,573,-1)]
    anchors={}
    for label,low,high,land,sg in specs:
        rise=high-low;steps=8;run=32
        # land is high end of hatch; low end extends away from upper platform.
        for i in range(steps):
            x=land+sg*(run-4*i);z=low+round(rise*(i+1)/steps)
            for xx in range(min(x,x+sg*3),max(x,x+sg*3)+1):
                for y in range(CY-9,CY+10):
                    for zz in range(z-1,z+1):
                        if (xx,y,zz) not in occupied:a[xx,y,zz]=109
                for y in (CY-10,CY+10):
                    for zz in range(low+1,z+2):
                        if (xx,y,zz) not in occupied:a[xx,y,zz]=109
        # top bridge meets the upper deck edge; foot stands on lower deck surface.
        xhi=land+sg*4
        for xx in range(min(land,xhi),max(land,xhi)+1):
            for y in range(CY-7,CY+8):
                for z in range(high-1,high+1):
                    if (xx,y,z) not in occupied:a[xx,y,z]=109
        # Lowest tread meets solid lower deck, no unwalkable hatch gap.
        lowend=land+sg*35;footend=land+sg*38
        for xx in range(min(lowend,footend),max(lowend,footend)+1):
            for yy in range(CY-9,CY+10):
                for zz in (low-1,low):
                    if (xx,yy,zz) not in occupied:a[xx,yy,zz]=109
        pts={'foot':(land+sg*39,CY,low+1),'lo':(land+sg*33,CY,low+round(rise/steps)+1),
             'hi':(land+sg*5,CY,high+1),'head':(land-sg*2,CY,high+1)}
        for k,q in pts.items():anchors[label+'.'+k]=q
        stairs.append({'name':label,'from_z':low,'to_z':high,'points':pts})
    name=BASE+'-ladders';ensure(name,'潮墓號｜七座梯子與通道');now=stamp(name,a,'ladders');draw_plan(a,'ladders')
    for k,q in anchors.items():cli(op='work',sub='anchor',work=name,name=k,at=','.join(map(str,q)),overwrite=1)
    cli(op='work',sub='link',work=ASSEMBLY,name='梯子',source_work=name,at='0,0,0',overwrite=1,meta='{"kind":"ladders"}')
    (ROOT/'verify_decks.json').write_text(json.dumps({'decks':reports,'stairs':stairs,'ladder_cells':len(now),'status':'geometry placed; tread/head/foot independently checked before final acceptance'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cli(op='stats',work=ASSEMBLY,structure=1,mirror='y:120')
    cli(op='view',work=ASSEMBLY,yaw=45,pitch=35,skybox='none',width=1500,height=1000,out=WORK/'overlays'/'decks_yaw45.png')
    cli(op='view',work=ASSEMBLY,yaw=150,pitch=65,skybox='none',width=1500,height=1000,hide_links='甲板-weather,甲板-quarter,甲板-poop,甲板-forecastle',out=WORK/'overlays'/'decks_inside.png')
    print(json.dumps({'decks':reports,'ladder_cells':len(now)},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
