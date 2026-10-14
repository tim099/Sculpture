"""Original hull structure design; generated lists applied ONLY via senate CLI.
Arrays carry design colors. Engine lists used for current state; events witness
is independent and never used as the design state.
"""
import json, subprocess, sys, hashlib, math, uuid
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFont
from draft_general import P,H,CY,width,top
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent
EXE='D:/Unity/Senate/publish/senate.exe';BASE=P['id']
def cli(**args):
    command=[EXE,'cmd','sculpture','--arg','persona=Sirius']
    for k,v in args.items():command+=['--arg',str(k)+'='+str(v)]
    r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8')
    log=ROOT/'cli_log';log.mkdir(exist_ok=True)
    n=len(list(log.glob('*.txt')));(log/f'{n:04}_{args.get("op")}_{args.get("sub","")}_{uuid.uuid4().hex[:8]}.txt').write_text(r.stdout,encoding='utf-8')
    if r.returncode:raise RuntimeError(f'{command}\n{r.returncode}\n{r.stdout}')
    vals={}
    for l in r.stdout.splitlines():
        if l.startswith('🔢 ') and ' = ' in l:
            k,v=l[2:].strip().split(' = ',1);vals[k]=v
    return vals
def get_actual(work):
    out=ROOT/'current.list.txt';cli(op='export',work=work,format='list',links='none',out=out)
    d={}
    for l in out.read_text(encoding='utf-8-sig').splitlines():
        if l and not l.startswith('#'):
            x,y,z,c=map(int,l.split(','));d[(x,y,z)]=c
    return d
def listfile(a,name):
    coords=np.argwhere(a>0);out=ROOT/(name+'.vox.txt')
    with out.open('w',encoding='utf-8',newline='\n') as f:
        for x,y,z in coords:f.write(f'{x},{y},{z},{a[x,y,z]}\n')
    return out,len(coords)
def generate():
    shape=(800,241,200);outer=np.zeros(shape,bool)
    yy=np.arange(241)-CY
    for x in range(100,621):
        for z in range(0,top(x)+1):
            w=width(x,z)
            if w>0:outer[x,:,z]=np.abs(yy)<=w
    # Solid keel follows independently measured first occupied cell of each column.
    keel=np.zeros(shape,np.uint8)
    for x in range(105,618):
        zz=np.flatnonzero(outer[x,CY,:])
        if len(zz):keel[x,CY-2:CY+3,:int(zz[0])+4]=109
    # Side shell ring with no artificial horizontal roof across the open hull.
    ring=np.zeros(shape,bool)
    for x in range(100,621):
        for z in range(0,top(x)+1):
            w=width(x,z)
            if w>0:ring[x,:,z]=outer[x,:,z] & (np.abs(yy)>max(0,w-4))
        for y in range(241):
            zz=np.flatnonzero(outer[x,y,:])
            if len(zz):ring[x,y,zz[:4]]=True
    # Raked transom and narrow stem follow outside air along X, not a box.
    boundary_x=outer & ~(np.roll(outer,4,axis=0)&np.roll(outer,-4,axis=0))
    shell=ring|boundary_x
    skeleton=np.zeros(shape,np.uint8);skeleton[keel>0]=keel[keel>0]
    for x in range(143,591,32):
        cross=outer[x,:,:116]
        rib=cross & ~ndimage.binary_erosion(cross,iterations=3)
        for xx in range(x-1,x+2):skeleton[xx,:,:116][rib]=109
    # End posts stay at the centreline; angled cant framing is a later detail.
    skeleton[:,CY-3:CY+4,:116][boundary_x[:,CY-3:CY+4,:116]]=109
    # longitudinal keelson directly above all central keel cells, face-connected.
    for x in range(105,618):
        zz=np.flatnonzero(keel[x,CY,:])
        if len(zz):skeleton[x,CY-3:CY+4,int(zz[-1]):int(zz[-1])+5]=109
    # Frames that do not meet keel removed by main connected component now,
    # reported rather than silently hidden; small join corrections will be visible.
    labels,n=ndimage.label(skeleton>0)
    print('prejoin components',n,flush=True)
    sizes=np.bincount(labels.ravel());sizes[0]=0;main=int(sizes.argmax())
    disconnected=int(np.count_nonzero((labels!=main)&(labels!=0)))
    if disconnected:raise RuntimeError(f'preflight has {n} components / {disconnected} detached cells; redesign joints')
    labels,n=ndimage.label(skeleton>0)
    print('postjoin components',n,flush=True)
    if n!=1:raise RuntimeError(f'skeleton {n} components')
    # A keel/frames stage is open; no hidden cavity should exist.
    holes=ndimage.binary_fill_holes(skeleton>0)&(skeleton==0)
    if holes.any():skeleton[holes]=109
    shell_a=np.zeros(shape,np.uint8)
    shell_a[shell]=73 # muted green-grey RGB332 (72,73,85)
    # Two solid rubbing wales around gun-deck boundaries.
    for z in (62,88,113):
        band=shell[:,:,z:z+3];c=shell_a[:,:,z:z+3];c[band]=109
    # ports are actual hull holes, measured above the design waterline.
    for dz in P['guns']['decks']:
        for x in P['guns']['x']:
            for z in range(dz+5,dz+20):
                for xx in range(x-8,x+9):
                    w=width(xx,z)
                    for sg in (-1,1):
                        yc=CY+sg*w
                        shell_a[xx,max(0,int(yc)-6):min(241,int(yc)+7),z]=0
    # Keep existing framing distinct; shell cannot overwrite the skeleton.
    shell_a[skeleton>0]=0
    combined=(skeleton>0)|(shell_a>0)
    holes=ndimage.binary_fill_holes(combined)&~combined
    shell_a[holes]=73
    (ROOT/'structure_report.json').write_text(json.dumps({'prejoin_disconnected_cells':disconnected,'skeleton_components':n,'skeleton_cells':int(np.count_nonzero(skeleton)),'shell_cells':int(np.count_nonzero(shell_a)),'combined_closed_air_filled':int(holes.sum())},indent=2)+'\n',encoding='utf-8')
    return skeleton,shell_a
def sheet(a,name):
    # Exact cell raster is a separate design artefact, not decorated drafting lines.
    proj=np.max(a,axis=1).T[::-1];im=Image.new('RGB',(800,200),(16,38,48))
    rgb=np.zeros((200,800,3),np.uint8);rgb[:]=(16,38,48)
    m=proj>0;c=proj[m].astype(np.int32);rgb[m]=np.stack([((c>>5)&7)*255/7,((c>>2)&7)*255/7,(c&3)*255/3],axis=1).astype(np.uint8)
    im=Image.fromarray(rgb);im.save(ROOT/(name+'_cell_plan.png'))
    # draw annotated larger sheet without changing the exact raster.
    out=Image.new('RGB',(1800,760),'#102630');out.paste(im.resize((1600,400),Image.Resampling.NEAREST),(100,160))
    d=ImageDraw.Draw(out);font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',25)
    d.text((100,65),f'潮墓號 / {name} / SIDE CELL PLAN / 0.1m per cell',font=font,fill='#d9e2d0')
    d.text((100,600),'原色像素每格對應一格；裝飾線另外存。+X 船頭 / Z0 龍骨底。',font=font,fill='#72b2ae')
    out.save(ROOT/(name+'_construction.png'))
def apply(stage):
    sk,sh=generate();a=sk if stage=='skeleton' else sh
    sheet(a,stage);out,count=listfile(a,stage)
    if stage=='skeleton':
        work=BASE
    else:work=BASE
    actual=get_actual(work)
    coords=np.argwhere(a>0);planned={tuple(map(int,v)):int(a[tuple(v)]) for v in coords}
    conflict=sum(1 for q,c in planned.items() if q in actual and actual[q]!=c)
    if conflict:raise RuntimeError(f'{conflict} occupied colors differ')
    if stage=='skeleton':
        # An explicit revision removes only coordinates absent from revised design.
        removal={q:c for q,c in actual.items() if q not in planned}
        if removal:
            path=ROOT/'skeleton_v1_remove.vox.txt'
            path.write_text(''.join(f'{x},{y},{z},{c}\n' for (x,y,z),c in sorted(removal.items())),encoding='utf-8')
            print('explicit v1 correction carve',len(removal),flush=True)
            cli(op='carvevox',work=work,voxels=path,at='0,0,0',expect_pixels=len(removal))
            actual=get_actual(work)
    missing={q:c for q,c in planned.items() if q not in actual}
    if not missing:print(f'{stage}: already complete, no duplicate stamp',flush=True)
    missing_a=np.zeros_like(a)
    for q,c in missing.items():missing_a[q]=c
    out,count=listfile(missing_a,stage+'_missing')
    if count>1_000_000:raise RuntimeError('split list required')
    # First narrow rib then remaining list, validating each actual placed count.
    if stage=='skeleton' and not actual:
        xs=[q[0] for q in missing];firstx=min(xs)
        first=np.zeros_like(a);first[firstx,:,:]=missing_a[firstx,:,:]
        f,n=listfile(first,'skeleton_first');v=cli(op='stampvox',work=work,voxels=f,at='0,0,0',expect_pixels=n)
        if int(v.get('placed',-1))!=n:raise RuntimeError(f'first expected {n}, {v}')
        missing_a[firstx,:,:]=0;out,count=listfile(missing_a,stage+'_remaining')
        cli(op='section',work=work,axis='y+',out=WORK/'overlays'/f'{stage}_first.png')
    if count:
        v=cli(op='stampvox',work=work,voxels=out,at='0,0,0',expect_pixels=count)
        if int(v.get('placed',-1))!=count:raise RuntimeError(f'expected {count}, {v}')
    now=get_actual(work);missing_count=sum(now.get(q)!=c for q,c in planned.items())
    changed=sum(now.get(q)!=c for q,c in actual.items());extra=len(set(now)-set(actual)-set(planned))
    # independent image -> actual coordinate check from exact cell-plan pixels.
    img=np.array(Image.open(ROOT/(stage+'_cell_plan.png')));mask=np.any(img!=(16,38,48),axis=2)
    zs,xs=np.where(mask); projected={(x,z) for x,y,z in now}
    absent=sum((int(x),199-int(z)) not in projected for z,x in zip(zs,xs))
    # real geometry perturbation: translate actual asset by 3 X cells; nearest
    # exposed stern point selected from drawing, independent of list coordinates.
    row=100;rowxs=np.flatnonzero(mask[199-row]);q=int(rowxs[0])
    stage_projected={(x,z) for x,y,z in now if (x,y,z) in planned}
    shifted={x+3 for x,z in stage_projected if z==row}
    rev=min(abs(x-q) for x in shifted)
    report={'stage':stage,'expected_cells':len(planned),'result_missing_or_color':missing_count,'result_extra':extra,'previous_changed':changed,'drawing_pixels_absent':absent,'negative_control_geometry_shift_x':3,'negative_control_measured_cells':rev,'actual_cells':len(now)}
    (ROOT/f'verify_{stage}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if any((missing_count,changed,extra,absent)) or rev!=3:raise RuntimeError(report)
    cli(op='stats',work=work,structure=1,mirror='y:120')
    cli(op='section',work=work,axis='y+',out=WORK/'overlays'/f'{stage}_side.png')
    cli(op='view',work=work,yaw=45,pitch=25,skybox='none',width=1400,height=900,out=WORK/'overlays'/f'{stage}_yaw45.png')
    print(json.dumps(report))
if __name__=='__main__':apply(sys.argv[1])
