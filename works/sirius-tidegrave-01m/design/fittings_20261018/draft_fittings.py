"""Additive model-only refit. Geometry inputs come from CLI list/parts exports.
Never run the historical hull/rig constructors on the completed ship.
"""
from pathlib import Path
import hashlib, itertools, json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
SCRATCH=Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave')
PARTS=HERE/'baseline_parts.json'
BODY=SCRATCH/'fittings_before_voxels.txt'
PREFIX={'boat':'basecamp-frigate-constitution-01m-whaleboat','light':'gura-tridente-01m-lantern','shot':'kotoko-napoleon-01m-shotrack','bitts':'kotoko-napoleon-01m-bitts','galley':'kotoko-napoleon-01m-galley','barrel':'summit-rocher-01m-barrel','crate':'summit-rocher-01m-crate'}
SIZES={'boat':[171,37,21],'light':[17,17,36],'shot':[54,4,9],'bitts':[15,41,24],'galley':[44,32,46],'barrel':[12,12,18],'crate':[12,12,12]}
OFF=np.array([[.5,.5,.5]]+list(itertools.product([.0001,.9999],repeat=3)))

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return np.loadtxt(p,delimiter=',',comments='#',dtype=np.int32,ndmin=2,encoding='utf-8')

def main():
    raw=np.load(HERE/'baseline_body.npz')['cells']; grid=np.zeros((800,241,640),np.uint8)
    grid[tuple(raw[:,:3].T)]=raw[:,3]
    parts=json.loads(PARTS.read_text(encoding='utf-8-sig'))
    old=[(p['path'],np.array(p['box'],float)) for p in parts['models'] if p.get('box')]
    # Full centre passage plus each actual ladder foot/head approach. Not a new
    # game collision policy: these are conservative placement exclusions only.
    reserved=[]
    for xa,xb,z in [(181,549,116),(130,239,139),(550,610,139),(130,179,165)]:
        reserved.append((f'centre-{z}',np.array([xa,111,z,xb,130,z+22],float)))
    for link in parts['links']:
        if link.get('meta',{}).get('kind')=='ladders':
            for name,p in link.get('points',{}).items():
                if any(t in name for t in ('foot','head','lo','hi')):
                    x,y,z=p; reserved.append((name,np.array([x-7,y-6,z-1,x+7,y+6,z+22])))
    # Cleared bow chase approaches from 2026-10-16, and all mast bases.
    reserved.extend([('chase-P',np.array([574,93,116,603,105,136.])),('chase-S',np.array([574,136,116,603,148,136.]))])
    for x,z in [(205,139),(355,116),(510,116)]:
        reserved.append(('mast',np.array([x-14,106,z,x+14,135,z+23.])))
    source={k:load(HERE/'source_exports'/f'source_{v}.txt') for k,v in PREFIX.items()}
    placed=[]; boxes=[]; diagnostics=[]

    def candidate(kind,at,sc):
        vox=source[kind][:,:3].copy(); at=np.array(at,float)
        if kind=='bitts':
            vox[:,:2]=np.column_stack([SIZES[kind][1]-1-vox[:,1],vox[:,0]])
        points=(vox[:,None,:]+OFF[None,:,:])*sc+at
        flat=points.reshape(-1,3); ix=np.floor(flat).astype(int)
        if np.any(ix<0) or np.any(ix>=np.array(grid.shape)): return None,'bounds'
        if np.any(grid[tuple(ix.T)]): return None,'body'
        low=vox.min(axis=0)*sc+at; high=(vox.max(axis=0)+1)*sc+at
        for name,box in old+boxes+reserved:
            if np.any(high<=box[:3]+1e-5) or np.any(low>=box[3:]-1e-5): continue
            if np.any(np.all((flat>box[:3]+1e-5)&(flat<box[3:]-1e-5),axis=1)): return None,name
        bottom=vox[vox[:,2]==vox[:,2].min()]
        feet=(bottom[:,:2]+.5)*sc+at[:2]
        z=at[2]+vox[:,2].min()*sc
        # Every bottom voxel centre has deck directly beneath (no floating).
        f=np.column_stack([feet,np.full(len(feet),z-1e-4)])
        fi=np.floor(f).astype(int)
        if not np.all(grid[tuple(fi.T)]): return None,'unsupported'
        return [*low.tolist(),*high.tolist()],'ok'

    def find(name,kind,target,sc=.5,span=24,step=2,frame='weather',meta=None):
        tx,ty,z=target
        offsets=sorted(itertools.product(range(-span,span+1,step),repeat=2),key=lambda p:(p[0]*p[0]+p[1]*p[1],abs(p[0]),p))
        rejected={}
        for dx,dy in offsets:
            at=[tx+dx,ty+dy,z]
            box,why=candidate(kind,at,sc)
            if box is None: rejected[why]=rejected.get(why,0)+1; continue
            p={'name':name,'source':PREFIX[kind],'at':at,'pivot':[0,SIZES[kind][1],0] if kind=='bitts' else [0,0,0],'rotate':[0,0,90] if kind=='bitts' else [0,0,0],'scale':sc,'frame':frame,'meta':meta or {'deco':1},'box':box,'target':target}
            placed.append(p); boxes.append((name,np.array(box)))
            diagnostics.append({'name':name,'at':at,'rejected':rejected})
            return p
        raise RuntimeError((name,'no safe location',rejected))

    # Original arrangement, shared parts. Small working boat to starboard,
    # kitchen to port, low stores in discrete clusters, centre aisle open.
    find('工作艇','boat',[366,142,116],span=18,meta={'kind':'boat','boat':'whaleboat','length_m':8.53})
    find('爐灶','galley',[478,83,116],span=22)
    for side,y in [('P',86),('S',149)]:
        for i,x in enumerate([265,320,480]):
            find(f'砲彈架-{side}{i+1}','shot',[x,y,116],span=14)
    for side,y in [('P',96),('S',137)]:
        find('繫纜柱-'+side,'bitts',[568,y,139],span=20,frame='forecastle')
    for side,y in [('P',96),('S',141)]:
        for i,x in enumerate([262,274,286]):
            find(f'備用水桶-{side}{i+1}','barrel',[x,y,116],span=12)
    for i,(x,y) in enumerate([(300,96),(310,96),(300,143),(310,143)]):
        find(f'工具箱-{i+1}','crate',[x,y,116],span=12)
    for side,y in [('P',96),('S',132)]:
        find('艉樓燈-'+side,'light',[116,y,165],sc=.75,span=12,frame='poop',meta={'kind':'light'})

    # Negative controls exercise real checker, not a different code path.
    first=placed[0]
    bad_body=candidate('boat',[355,110,110],.5)[1]
    bad_aisle=candidate('crate',[400,118,116],.5)[1]
    assert bad_body!='ok' and bad_aisle.startswith('centre-'),(bad_body,bad_aisle)
    manifest={'date':'2026-10-18','ship':'sirius-tidegrave-01m-assembly','metres_per_voxel':.1,'reference':'Constitution deck equipment and small-boat arrangement; not a historical reconstruction','body_sha256':json.loads((HERE/'input_hashes.json').read_text())['body_sha256'],'parts_sha256':sha(PARTS),'source_sha256':{k:sha(HERE/'source_exports'/f'source_{v}.txt') for k,v in PREFIX.items()},'placements':placed,'reserved':[[n,b.tolist()] for n,b in reserved],'negative_controls':{'body':bad_body,'passage':bad_aisle},'diagnostics':diagnostics,'limits':'Model source cubes at centre and eight inset corners; old model boxes conservatively reserved. Original sails/rig not moved; not a new full dynamic cloth certificate.'}
    (HERE/'placement.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    img=Image.new('RGB',(1450,930),'#16202a'); d=ImageDraw.Draw(img)
    ox,oy,sc=40,30,2.4
    surface=raw[(raw[:,2]==115)|(raw[:,2]==138)|(raw[:,2]==164)]
    for x,y,z,c in surface:
        d.point((int(ox+(x-85)*sc),int(oy+y*sc)),fill='#66716d')
    colours={'boat':'#90a9b4','light':'#ffe194','shot':'#c5a16e','bitts':'#93714e','galley':'#c66b49','barrel':'#bd9763','crate':'#9c875f'}
    for i,p in enumerate(placed):
        b=p['box']; xy=[ox+(b[0]-85)*sc,oy+b[1]*sc,ox+(b[3]-85)*sc,oy+b[4]*sc]
        kind=next(k for k,v in PREFIX.items() if v==p['source'])
        d.rectangle(xy,outline=colours[kind],width=2)
        d.text((xy[0],xy[1]-11),str(i+1),fill='white')
    d.text((40,580),'TIDEGRAVE / DECK FITTINGS / 0.1 m PER CELL / BOW ->',fill='white')
    font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',16)
    for x in range(100,621,50):
        px=ox+(x-85)*sc
        d.line((px,24,px,29),fill='#cad3d8'); d.text((px,9),str(x),fill='white')
    d.text((40,608),'X ticks: cells (0.1 m); +X bow; upper side = port (-Y). Grey = existing deck.',fill='white')
    for i,p in enumerate(placed):
        col=i//11; row=i%11
        at=','.join(str(v) for v in p['at'])
        text=f'{i+1:02} {p["name"]}  ({at})  x{p["scale"]}'
        d.text((40+700*col,640+row*23),text,font=font,fill='white')
    d.text((40,905),'Original layout; existing ghost-ship carvings retained. Lanterns enlarged to 2.7 m as stern beacons.',fill='#e6cf9e')
    img.save(HERE/'deck_plan.png')
    print(json.dumps({'models':len(placed),'deco':sum(p['meta'].get('deco')==1 for p in placed),'negative':manifest['negative_controls'],'placements':[{k:p[k] for k in ('name','at','box')} for p in placed]},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
