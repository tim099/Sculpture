import json,math
import numpy as np
from pathlib import Path
from build_structure import cli,get_actual,listfile,ROOT,WORK,BASE
from build_decks import ensure,stamp,draw_plan,ASSEMBLY
from draft_general import P,CY,width
def coord(q):return ','.join(str(x) for x in q)
def linevox(a,p,q,r,color,avoid=None):
    p=np.array(p,float);q=np.array(q,float);n=int(np.linalg.norm(q-p)*2)+1
    for t in np.linspace(0,1,n):
        v=p+(q-p)*t
        for x in range(math.floor(v[0]-r),math.ceil(v[0]+r)+1):
            for y in range(math.floor(v[1]-r),math.ceil(v[1]+r)+1):
                for z in range(math.floor(v[2]-r),math.ceil(v[2]+r)+1):
                    if np.linalg.norm(np.array((x,y,z))-v)<=r and 0<=x<a.shape[0] and 0<=y<a.shape[1] and 0<=z<a.shape[2] and (not avoid or (x,y,z) not in avoid):a[x,y,z]=color
def anchor(work,name,q):cli(op='work',sub='anchor',work=work,name=name,at=coord(q),overwrite=1)
def rope(name,frm,to,group,thick=.5,slack=1,color='#3c453a'):
    cli(op='work',sub='rope',work=ASSEMBLY,name=name,**{'from':frm,'to':to},group=group,thickness=thick,slack=slack,color=color,overwrite=1)
def main():
    path=ROOT/'rig_baseline.list.txt';cli(op='export',work=ASSEMBLY,format='list',out=path)
    occupied={tuple(map(int,l.split(',')[:3])):int(l.split(',')[3]) for l in path.read_text(encoding='utf-8-sig').splitlines() if l and not l.startswith('#')}
    # Rig design frames form the construction plan; all part transforms explicit.
    mastreports=[]
    for M in P['masts']:
        ident=M['id'];x=M['x'];a=np.zeros((800,241,640),np.uint8)
        for z in range(9,M['top_z']+1):
            r=4 if z<M['platform_z'] else 2 if z<M['top_z']-50 else 1
            for xx in range(x-r,x+r+1):
                for yy in range(CY-r,CY+r+1):
                    if (xx-x)**2+(yy-CY)**2<=r*r and (xx,yy,z) not in occupied:a[xx,yy,z]=109
        z=M['platform_z'];a[x-10:x+11,CY-12:CY+13,z:z+2]=145
        for q in list(occupied):
            if q[0]<800 and q[1]<241 and q[2]<640:a[q]=0
        name=BASE+'-mast-'+ident;ensure(name,'潮墓號｜'+ident+'桅')
        now=stamp(name,a,'mast_'+ident);occupied.update(now);draw_plan(a,'mast_'+ident)
        for k,q in {'head':(x,CY,M['platform_z']+20),'truck':(x,CY,M['top_z']),
                    'hounds-P':(x,CY-4,M['platform_z']-5),'hounds-S':(x,CY+4,M['platform_z']-5)}.items():anchor(name,k,q)
        cli(op='work',sub='link',work=ASSEMBLY,name=ident,source_work=name,at='0,0,0',overwrite=1)
        mastreports.append({'mast':ident,'cells':len(now),'x':x,'top':M['top_z']})
    a=np.zeros((800,241,640),np.uint8);linevox(a,(580,CY,145),(748,CY,215),3,109,occupied)
    name=BASE+'-bowsprit';ensure(name,'潮墓號｜艏斜桅');now=stamp(name,a,'bowsprit');occupied.update(now)
    for k,q in {'tip':(748,CY,215),'root':(580,CY,145),'stay':(700,CY,195)}.items():anchor(name,k,q)
    cli(op='work',sub='link',work=ASSEMBLY,name='bowsprit',source_work=name,at='0,0,0',overwrite=1)
    # Individual horizontal yards are full unrotated parts.
    spec=P['rig_layout']['square_yards']
    yards={};rigplan=[]
    for mast,yid,z,length,drop in spec:
        source=BASE+'-yard-'+mast+'-'+yid;a=np.zeros((800,241,200),np.uint8)
        half=length//2
        linevox(a,(4,CY-half,4),(4,CY+half,4),1.6 if yid=='course' else 1.2,109)
        ensure(source,'潮墓號｜'+mast+' '+yid+' 帆桁');stamp(source,a,'yard_'+mast+'_'+yid)
        for k,q in {'pivot':(4,CY,4),'earing-P':(4,CY-half+2,4),'earing-S':(4,CY+half-2,4),'arm-P':(4,CY-half,4),'arm-S':(4,CY+half,4)}.items():anchor(source,k,q)
        mwork=BASE+'-mast-'+mast;x=next(m['x'] for m in P['masts'] if m['id']==mast)
        name='yard-'+mast+'-'+yid;sail=mast+'-'+yid if drop else ''
        mt={'kind':'yard','mast':mast,'yard':yid,'length_ft':round(length*.1/0.3048,2),'diameter_in':round(.3/.0254,2),'pivot_anchor':'pivot','turn_axis':'z','rotate_z_deg':-18}
        if sail:mt['sail']=sail
        cli(op='work',sub='model',work=mwork,name=name,source_work=source,pivot='4.5,120.5,4.5',at=f'{x+.5},{CY+.5},{z+.5}',scale=1,rotate='0,0,-18',meta=json.dumps(mt),overwrite=1)
        yards[(mast,yid)]={'path':mast+'/'+name,'length':length,'z':z,'x':x,'drop':drop,'sail':sail}
        rigplan.append({'mast':mast,'yard':yid,'z':z,'length':length,'drop':drop,'meta':mt})
    # Gaff and boom carry distinct pivots and one shared lateen-style sail.
    for yid,q,z in [('gaff',(70,CY,265),230),('boom',(40,CY,180),205)]:
        source=BASE+'-yard-mizzen-'+yid;a=np.zeros((800,241,300),np.uint8)
        linevox(a,(120,CY,180),q,1.8,109);ensure(source,'潮墓號｜後桅 '+yid);stamp(source,a,'yard_mizzen_'+yid)
        for k,pt in {'pivot':(120,CY,180),'jaws':(120,CY,180),'end':q,'top':q}.items():anchor(source,k,pt)
        cli(op='work',sub='model',work=BASE+'-mast-mizzen',name='yard-mizzen-'+yid,source_work=source,pivot='120.5,120.5,180.5',at=f'205.5,120.5,{z+.5}',scale=1,rotate='0,0,0',meta=json.dumps({'kind':'yard','mast':'mizzen','yard':yid,'turn_axis':'z','pivot_anchor':'pivot','rotate_z_deg':0,'sail':'mizzen-lateen','length_ft':round(np.linalg.norm(np.array(q)-np.array((120,CY,180)))*.1/.3048,2),'diameter_in':14}),overwrite=1)
    # Static rigging, symmetric and anchored on actual outer railing cells.
    for M in P['masts']:
        ident=M['id'];x=M['x'];start=130 if x<240 else 115
        for sg,side in [(-1,'P'),(1,'S')]:
            refs=[]
            for j,dx in enumerate((-20,0,20)):
                xx=x+dx;ww=width(xx,start);yy=CY+sg*math.floor(ww-2)
                pt=(xx,yy,start);anchor(ASSEMBLY,f'{ident}-chain-{side}{j}',pt)
                rn=f'{ident}-shroud-{side}{j}';rope(rn,f'{ident}-chain-{side}{j}',f'{ident}/hounds-{side}','standing/shrouds',.8);refs.append(rn)
            for j in range(1,22):
                t=j/25
                rope(f'{ident}-ratline-{side}-{j}',f'rope:{refs[0]}/{t}',f'rope:{refs[2]}/{t}','standing/ratlines',.25)
        target='bowsprit/stay' if ident=='fore' else 'fore/head' if ident=='main' else 'main/head'
        rope(ident+'-stay',ident+'/head',target,'standing/stays',1.0)
        for side in ('P','S'):rope(ident+'-backstay-'+side,ident+'/truck',ident+'-chain-'+side+'0','standing/backstays',.6)
    # Draws use texture alpha for aged canvas, no destructive tears in the hull.
    from PIL import Image,ImageDraw
    textures=ROOT/'textures';textures.mkdir(exist_ok=True)
    metas=[]
    for mast,yid,z,length,drop in spec:
        if not drop:continue
        v=yards[(mast,yid)];name=v['sail'];path=v['path'];half=length/2-2
        corners=[f'model:{path}/earing-P',f'model:{path}/earing-S',f'{v["x"]+.5},{CY+half*.85+.5},{z-drop+.5}',f'{v["x"]+.5},{CY-half*.85+.5},{z-drop+.5}']
        im=Image.new('RGBA',(64,64),(183,178,142,255));d=ImageDraw.Draw(im)
        # Finite ragged tears with intact top attachments, deterministic per sail.
        for j in range(5):
            u=7+j*11;d.polygon([(u,64),(u+3,43+(j%3)*4),(u+6,64)],fill=(0,0,0,0))
        for j in range(3):d.ellipse((12+j*16,24+j*4,15+j*16,28+j*4),fill=(0,0,0,0))
        tex=textures/(name+'.png');im.save(tex)
        cli(op='work',sub='sail',work=ASSEMBLY,name=name,corners='|'.join(corners),corner_names='head-P|head-S|clew-S|clew-P',bind=0,free='clew-P,clew-S',fullness=1.03,res=16,color='#b7b28e',texture=tex,overwrite=1)
        lowerid={'topsail':'course','topgallant':'topsail'}.get(yid)
        if mast=='mizzen':lowerid='crossjack'
        for side,sg in [('P',-1),('S',1)]:
            target=f'model:{yards[(mast,lowerid)]["path"]}/earing-{side}' if lowerid else f'{mast}-chain-{side}0'
            rope(name+'.sheet-'+side,f'sail:{name}/clew-{side}',target,'running/sheets',.4,1,'#9f9673')
            metas.append(('rope',name+'.sheet-'+side,{'kind':'sheet','sail':name}))
        metas.append(('sail',name,{'kind':'sail','mast':mast,'sail':yid}))
        # Yard braces and lifts are independent of its sail sheets.
        for side in ('P','S'):
            rope(name+'.brace-'+side,f'model:{path}/arm-{side}',f'{mast}-chain-{side}0','running/braces',.4,1.015)
            rope(name+'.lift-'+side,f'model:{path}/arm-{side}',mast+'/truck','running/lifts',.4)
    cli(op='work',sub='sail',work=ASSEMBLY,name='mizzen-lateen',corners='model:mizzen/yard-mizzen-gaff/jaws|model:mizzen/yard-mizzen-gaff/top|model:mizzen/yard-mizzen-boom/end',corner_names='tack|head|clew',bind='0,2',fullness=1.03,res=16,color='#b7b28e',overwrite=1)
    metas.append(('sail','mizzen-lateen',{'kind':'sail','mast':'mizzen','sail':'gaff'}))
    cli(op='work',sub='sail',work=ASSEMBLY,name='jib',corners='bowsprit/tip|fore/head|600.5,145.5,145.5',corner_names='tack|head|clew',bind=0,fullness=1.02,res=14,color='#b7b28e',overwrite=1)
    metas.append(('sail','jib',{'kind':'sail','mast':'fore','sail':'jib'}))
    # Small custom pennant — Sirius's broken ring emblem, texture drawn in code.
    im=Image.new('RGBA',(64,32),(49,66,61,255));d=ImageDraw.Draw(im);d.ellipse((10,6,30,26),outline=(220,216,181,255),width=2);d.rectangle((26,13,32,20),fill=(49,66,61,255));d.line((5,21,41,21),fill=(114,175,168,255),width=2);d.polygon([(64,0),(48,16),(64,31)],fill=(0,0,0,0));im.save(textures/'ensign.png')
    cli(op='work',sub='sail',work=ASSEMBLY,name='ensign',corners='105.5,120.5,205.5|75.5,120.5,205.5|75.5,120.5,189.5|105.5,120.5,189.5',bind=3,res=10,fullness=1.02,color='#31423d',texture=textures/'ensign.png',overwrite=1)
    metas.append(('sail','ensign',{'kind':'flag','flag':'ensign'}))
    f=ROOT/'rig_meta.tsv';f.write_text(''.join(part+'\t'+name+'\t'+json.dumps(mt)+'\n' for part,name,mt in metas),encoding='utf-8')
    cli(op='work',sub='meta',work=ASSEMBLY,file=f)
    cli(op='work',sub='wind',work=ASSEMBLY,wind='4.5,-1.5,0',sail_seconds=3)
    (ROOT/'rig_plan.json').write_text(json.dumps({'masts':mastreports,'yards':rigplan,'appearance':'lateen-inspired mizzen adapted to gaff game class; tears are texture alpha'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cli(op='stats',work=ASSEMBLY,structure=1,mirror='y:120')
    cli(op='work',sub='sails',work=ASSEMBLY);cli(op='work',sub='ropes',work=ASSEMBLY)
    cli(op='view',work=ASSEMBLY,yaw=45,pitch=20,skybox='none',width=1600,height=1100,out=WORK/'overlays'/'rig_yaw45.png')
    print('rig placed',len(metas),flush=True)
if __name__=='__main__':main()
