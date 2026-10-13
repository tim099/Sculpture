import json,math
from pathlib import Path
import numpy as np
from build_structure import cli,get_actual,ROOT,WORK,BASE
from build_decks import ensure,stamp,ASSEMBLY
from build_guns import composed
from build_rig import linevox,anchor,rope
def main():
    occ=composed();reports=[];support=np.zeros((800,241,200),np.uint8)
    for pos,x0 in [('aft',240),('fore',440)]:
        name=BASE+'-magazine-'+pos;path=WORK.parent/name/'work.json'
        if not path.exists():cli(op='work',sub='create',id=name,title='潮墓號｜'+pos+'彈藥庫',parent_work=BASE,size='45,41,24',tags='sub')
        cli(op='work',sub='update',work=name,meters_per_voxel=.1)
        a=np.zeros((45,41,24),np.uint8);a[:,:,0:2]=145;a[:,:,23]=145
        a[0:2,:,:]=168;a[43:45,:,:]=168;a[:,0:2,:]=168;a[:,39:41,:]=168
        a[43:45,17:24,2:18]=0 # open doorway, no sealed air behind a room
        now=stamp(name,a,'magazine_'+pos)
        for q,c in now.items():
            world=(q[0]+x0,q[1]+100,q[2]+30)
            if world in occ:raise RuntimeError('magazine overlaps existing shell/deck')
        for k,q in {'blast':(22,20,10),'door':(44,20,2)}.items():anchor(name,k,q)
        n=0
        for xx in (6,12,18,24,30,36):
            for yy in (8,14,26,32):
                n+=1;cli(op='work',sub='model',work=name,name=f'powder-{n:02}',source_work='basecamp-frigate-constitution-01m-powder-barrel',pivot='11,11,0',at=f'{xx+.5},{yy+.5},2',scale=.2,meta='{"kind":"powder","powder_lb":100}',overwrite=1,note='Credit basecamp powder barrel; 100 lb is game inventory')
        # Four load-bearing supports reach the actual hull inside the bowl.
        for xx in (x0+3,x0+41):
            for yy in (103,137):
                for x in range(xx-1,xx+2):
                    for y in range(yy-1,yy+2):
                        below=[z for z in range(30) if (x,y,z) in occ]
                        if not below:raise RuntimeError('no hull beneath magazine support')
                        for z in range(max(below)+1,30):support[x,y,z]=109
        cli(op='work',sub='link',work=ASSEMBLY,name='彈藥庫-'+('後' if pos=='aft' else '前'),source_work=name,at=f'{x0},100,30',meta=json.dumps({'kind':'magazine','powder_lb':2400,'pos':pos}),overwrite=1)
        reports.append({'magazine':pos,'at':[x0,100,30],'size':[45,41,24],'powder_barrels':24,'powder_lb':2400,'door_open':True})
    name=BASE+'-magazine-supports';ensure(name,'潮墓號｜彈藥庫下承柱');stamp(name,support,'magazine_supports')
    cli(op='work',sub='link',work=ASSEMBLY,name='彈藥庫承柱',source_work=name,at='0,0,0',overwrite=1)
    # Original sloped rudder, aft of the raked stern. Continuous stock & tiller.
    a=np.zeros((800,241,200),np.uint8)
    for z in range(6,76):
        stock=135-.3125*z
        for x in range(math.floor(stock)-2,math.floor(stock)+2):
            for y in range(118,123):a[x,y,z]=109
        if 10<=z<=58:
            for x in range(math.floor(stock)-25,math.floor(stock)-1):
                for y in range(118,123):a[x,y,z]=109
    linevox(a,(111,120,74),(155,120,74),1.8,109)
    name=BASE+'-rudder';ensure(name,'潮墓號｜斜舵柱、舵葉與舵柄');stamp(name,a,'rudder')
    anchor(name,'stock-top',(111,120,74));anchor(name,'tiller-end',(155,120,74))
    # Tiller penetrates only the stern transom; exact source color guards the hole.
    hull=get_actual(BASE);cut={q:c for q,c in hull.items() if a[q]>0}
    f=ROOT/'tiller_port.vox.txt';f.write_text(''.join(f'{x},{y},{z},{c}\n' for (x,y,z),c in sorted(cut.items())),encoding='utf-8')
    if cut:cli(op='carvevox',work=BASE,voxels=f,at='0,0,0',expect_pixels=len(cut))
    cli(op='work',sub='model',work=ASSEMBLY,name='舵',source_work=name,pivot='0,0,0',at='0,0,0',scale=1,meta=json.dumps({'kind':'rudder','turn_axis':'hinge','hinge_x':135,'hinge_y':120.5,'hinge_z':0,'axis_x':-.2983,'axis_y':0,'axis_z':.9545,'max_deg':30}),overwrite=1)
    # Readymade equipment retains authorship/source references.
    for work,model,source,pivot,at,scale,kind in [
      (BASE+'-deck-quarter','舵輪','basecamp-frigate-constitution-01m-wheel','50,52,0','180.5,120.5,139',.2,'wheel'),
      (BASE+'-deck-quarter','羅經櫃','summit-night-falcon-01m-binnacle','9,13,0','196.5,120.5,139',.2,'binnacle'),
      (BASE+'-deck-weather','絞盤','basecamp-ember-01m-capstan','40,40,0','465.5,120.5,116',.2,'capstan')]:
        cli(op='work',sub='model',work=work,name=model,source_work=source,pivot=pivot,at=at,scale=scale,meta=json.dumps({'kind':kind}),overwrite=1,note='Credit source author; original asset retained')
    # Steering blocks & guarded lead-throughs: no claim of new engine mechanics.
    for k,q in {'steer-P':(155,106,85),'steer-S':(155,134,85),'lead-P':(175,106,135),'lead-S':(175,134,135)}.items():anchor(ASSEMBLY,k,q)
    for side,drum in [('P','a'),('S','b')]:
        rope('steer-wheel-'+side,'model:甲板-quarter/舵輪/drum-rope-'+drum,'lead-'+side,'steering',.5)
        rope('steer-lead-'+side,'lead-'+side,'steer-'+side,'steering',.5)
        rope('steer-tiller-'+side,'steer-'+side,'model:舵/tiller-end','steering',.5)
    # Cannon breech ropes tie to individually measured side rings.
    fittings=np.zeros((800,241,200),np.uint8);guns=json.loads((ROOT/'verify_guns.json').read_text(encoding='utf-8'))['guns']
    for G in guns[:48]:
        path=G['path'];at=G['at'];side='P' if G['theta']==180 else 'S';sg=-1 if side=='P' else 1
        x=round(at[0]-.5);dz=round(at[2]-1);basey=round(at[1]-.5)
        # Rings sit in the shell, behind the gun doorway edge, and connect to side.
        for suffix,dx in [('aft',-11),('fwd',11)]:
            xx=x+dx;from draft_general import width
            yy=120+sg*math.floor(width(xx,dz+8)-3)
            pt=(xx,yy,dz+8);anchor(ASSEMBLY,path.replace('/','-')+'-'+suffix,pt)
            rope(path.replace('/','-')+'.breech-'+suffix,'model:'+path+'/cascabel',path.replace('/','-')+'-'+suffix,'guns/breeching',.5,1.08,'#a99e79')
    (ROOT/'equipment_plan.json').write_text(json.dumps({'magazines':reports,'tiller_hull_cut':len(cut),'rudder':'original; stepped raked stock, blade, tiller; degrees are design allowance, sweep checked later','borrowed_equipment':['basecamp wheel','summit binnacle','basecamp capstan']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cli(op='stats',work=ASSEMBLY,structure=1,mirror='y:120')
    cli(op='export',work=ASSEMBLY,format='parts',out=ROOT/'equipment_parts.json')
    print('equipment and two 24-barrel magazines ready',flush=True)
if __name__=='__main__':main()
