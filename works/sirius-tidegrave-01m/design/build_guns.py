import json,math
import numpy as np
from build_structure import cli,get_actual,listfile,ROOT,WORK,BASE
from build_decks import ensure,stamp,ASSEMBLY
from draft_general import P,width,CY
def read_list(path):return np.array([list(map(int,l.split(','))) for l in path.read_text(encoding='utf-8-sig').splitlines() if l and not l.startswith('#')])
def composed():
    f=ROOT/'guns_baseline.list.txt';cli(op='export',work=ASSEMBLY,format='list',out=f)
    a=read_list(f);return {tuple(q[:3]):int(q[3]) for q in a}
def transformed(vox,pivot,at,scale,theta):
    rad=math.radians(theta);R=np.array([[math.cos(rad),-math.sin(rad),0],[math.sin(rad),math.cos(rad),0],[0,0,1]])
    p=(vox[:,:3]+.5-np.array(pivot))*scale
    return p@R.T+np.array(at)
def conflicts(vox,pivot,at,scale,theta,occ):
    rad=math.radians(theta);R=np.array([[math.cos(rad),-math.sin(rad),0],[math.sin(rad),math.cos(rad),0],[0,0,1]])
    hit=set()
    # Centroids and eight inset corners: contact at boundary alone is not penetration.
    for off in [(0.5,.5,.5)]+[(x,y,z) for x in (.0001,.9999) for y in (.0001,.9999) for z in (.0001,.9999)]:
        pp=((vox[:,:3]+np.array(off)-np.array(pivot))*scale)@R.T+np.array(at)
        for q in np.floor(pp).astype(int):
            t=tuple(q)
            if t in occ:hit.add(t)
    return hit
def anchor(work,k,q):cli(op='work',sub='anchor',work=work,name=k,at=','.join(map(str,q)),overwrite=1)
def main():
    occ=composed();gun=read_list(ROOT/'gun24_reference.list.txt');report=[]
    for di,dz in enumerate(P['guns']['decks']):
        deck=BASE+'-deck-'+('lower' if di==0 else 'upper');deckpath='甲板-'+('lower' if di==0 else 'upper')
        for j,x in enumerate(P['guns']['x'],1):
            for sg,side in [(1,'S'),(-1,'P')]:
                pivot=(7.5,0,0);theta=0 if sg==1 else 180
                start=math.ceil(width(x,dz+12))-28
                found=None
                for inward in range(0,24):
                    by=CY+sg*(start-inward);at=(x+.5,by+.5,dz+1)
                    hits=conflicts(gun,pivot,at,1,theta,occ)
                    muzzle=transformed(np.array([[7,31,11,0]]),pivot,at,1,theta)[0]
                    outside=abs(muzzle[1]-(CY+.5))>width(muzzle[0]-.5,muzzle[2]-.5)
                    if not hits and outside:found=(at,muzzle,inward);break
                if found is None:raise RuntimeError(f'no clear position {di} {j} {side}')
                at,mz,inward=found;name=f'砲-{side}{j:02}'
                cli(op='work',sub='model',work=deck,name=name,source_work='basecamp-frigate-constitution-01m-gun-24',pivot=','.join(map(str,pivot)),at=','.join(map(str,at)),scale=1,rotate=f'0,0,{theta}',meta='{"kind":"gun","gun":"24l"}',overwrite=1,note='Credit basecamp: 憲法號24磅砲；Tidegrave game equipment, not historical Vasa gun')
                report.append({'path':deckpath+'/'+name,'source':'basecamp-frigate-constitution-01m-gun-24','at':at,'pivot':pivot,'scale':1,'theta':theta,'collision_centres_and_corners':0,'muzzle':mz.tolist(),'muzzle_outside':True,'retreat':inward})
    # Purpose-built slender barrels at 0.05m; no fictional rotary mechanism.
    source=BASE+'-chase-tube';ensure(source,'潮墓號｜三聯艏砲單管（0.05m）');cli(op='work',sub='update',work=source,meters_per_voxel=.05)
    a=np.zeros((800,241,200),np.uint8)
    for y in range(2,61):
        radius=5.2 if y<8 else 4.4 if y<22 else 3.7 if y<55 else 4.4
        for x in range(6,19):
            for z in range(6,19):
                r=math.hypot(x-12,z-12)
                if 1.7<r<=radius:a[x,y,z]=36
    stamp(source,a,'chase_tube');vox=np.array([[*q,int(a[tuple(q)])] for q in np.argwhere(a>0)])
    for k,q in {'muzzle':(12,60,12),'breech':(12,3,12),'cascabel':(12,2,12),'eye-aft':(7,10,12),'eye-fwd':(17,10,12),'train':(12,3,7)}.items():anchor(source,k,q)
    # Final fit positions differ from conceptual coarse centres, now use model bounds.
    positions=[(585.5,103.5,119),(585.5,98.5,127),(585.5,108.5,127),
               (585.5,137.5,119),(585.5,132.5,127),(585.5,142.5,127)]
    pivot=(12.5,0,0);carve=set()
    for at in positions:carve.update(conflicts(vox,pivot,at,.5,-90,occ))
    hull=get_actual(BASE);invalid=carve-set(hull)
    if invalid:raise RuntimeError(f'chase intersects {len(invalid)} non-hull cells')
    f=ROOT/'chase_port_cut.vox.txt';f.write_text(''.join(f'{x},{y},{z},{hull[(x,y,z)]}\n' for x,y,z in sorted(carve)),encoding='utf-8')
    if carve:cli(op='carvevox',work=BASE,voxels=f,at='0,0,0',expect_pixels=len(carve))
    occ=composed()
    # Shared cradle rests on weather deck; seat cells stop below barrel surfaces.
    a=np.zeros((800,241,200),np.uint8)
    for i,at in enumerate(positions):
        x=599;y=math.floor(at[1]);seat=122 if i in (0,3) else 130
        for xx in range(x-1,x+2):
            for yy in range(y-1,y+2):
                for z in range(116,seat+1):
                    if (xx,yy,z) not in occ:a[xx,yy,z]=109
    # Beams bring seats outside the narrow prow back to full, solid deck structure.
    for xx in range(582,601):
        for yy in range(96,145):
            if (xx,yy,116) not in occ:a[xx,yy,116]=109
    cradle=BASE+'-chase-cradle';ensure(cradle,'潮墓號｜雙三聯砲支架');now=stamp(cradle,a,'chase_cradle');occ.update(now)
    cli(op='work',sub='link',work=ASSEMBLY,name='艏砲支架',source_work=cradle,at='0,0,0',overwrite=1)
    for i,at in enumerate(positions):
        hits=conflicts(vox,pivot,at,.5,-90,occ)
        if hits:raise RuntimeError(f'cradle collision tube{i} {len(hits)}')
        name='chase-'+str(i+1);cli(op='work',sub='model',work=BASE+'-deck-weather',name=name,source_work=source,pivot='12.5,0,0',at=','.join(map(str,at)),scale=.5,rotate='0,0,-90',meta='{"kind":"gun","gun":"18chase"}',overwrite=1)
        mz=transformed(np.array([[12,60,12,0]]),pivot,at,.5,-90)[0]
        report.append({'path':'甲板-weather/'+name,'source':source,'at':at,'pivot':pivot,'scale':.5,'theta':-90,'collision_centres_and_corners':0,'muzzle':mz.tolist(),'muzzle_outside':True})
    (ROOT/'verify_guns.json').write_text(json.dumps({'guns':report,'count':len(report),'chase_hull_carved':len(carve),'notes':'6 fixed independent barrels in paired triangular groups; normal 18chase mechanic'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cli(op='export',work=ASSEMBLY,format='parts',out=ROOT/'guns_parts.json')
    cli(op='view',work=ASSEMBLY,yaw=-45,pitch=18,sails=0,skybox='none',width=1600,height=1050,out=WORK/'overlays'/'guns_bow.png')
    print('guns',len(report),'chase hull carve',len(carve),flush=True)
if __name__=='__main__':main()
