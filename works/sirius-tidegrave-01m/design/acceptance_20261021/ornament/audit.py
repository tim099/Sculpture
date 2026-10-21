"""Independent readonly verifier. No author modules imported. Outputs beside this file."""
import json, hashlib, collections
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from PIL import Image
OUT=Path(__file__).resolve().parent
BASE=Path('D:/Unity/Valhalla/Sculpture/works')
MAIN=BASE/'sirius-tidegrave-01m'
DES=MAIN/'design'
ORN=BASE/'sirius-tidegrave-01m-ornament'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def replay(folder):
    cells={};events=[]
    for p in sorted((folder/'events').rglob('*.json')):
        e=load(p)
        for v in e.get('carved_voxels',[]):cells.pop(tuple(v[:3]),None)
        for v in e.get('placed_colored',[]):cells[tuple(v[:3])]=v[3]
        for v in e.get('placed_voxels',[]):cells[tuple(v[:3])]=e['color']
        events.append({'path':str(p),'sha256':sha(p),'op':e['op'],'placed':len(e.get('placed_colored',e.get('placed_voxels',[]))),'carved':len(e.get('carved_voxels',[]))})
    return cells,events
def delta(a,b):
    return {'missing':len(b.keys()-a.keys()),'extra':len(a.keys()-b.keys()),'color_diff':sum(a[q]!=b[q] for q in a.keys()&b.keys())}
def readlist(p):
    a={}
    for l in p.read_text(encoding='utf-8-sig').splitlines():
        if l.strip() and not l.startswith('#'):
            v=list(map(int,l.split(',')));a[tuple(v[:3])]=v[3]
    return a
def grid(cells):
    pts=np.array(list(cells),dtype=int);lo=pts.min(0)-1;hi=pts.max(0)+1
    a=np.zeros(tuple(hi-lo+1),bool);i=pts-lo;a[tuple(i.T)]=True
    return a,lo
def mirror(cells):
    return {'missing':sum((x,240-y,z) not in cells for x,y,z in cells),'color_diff':sum(cells.get((x,240-y,z),c)!=c for (x,y,z),c in cells.items())}
orn,events=replay(ORN)
cache={tuple(map(int,k.split(','))):v for k,v in load(ORN/'sculpt_cache.json')['voxels'].items()}
expected={}
for name in ['ornament.vox.txt','ornament_root_correction.vox.txt','raised_flag_staff.vox.txt']:expected.update(readlist(DES/name))
a,lo=grid(orn);labels,n=ndi.label(a);holes=ndi.binary_fill_holes(a)&~a
links=load(BASE/'sirius-tidegrave-01m-assembly/links.json')['links']
body={};link_stats=[]
for link in links:
    if link.get('enabled') is False or link['work']==ORN.name:continue
    if link.get('turn',0) or link.get('mirror',''):raise RuntimeError('Unsupported transform')
    c,ev=replay(BASE/link['work']);t=link['at']
    for p,col in c.items():body[tuple(p[i]+t[i] for i in range(3))]=col
    link_stats.append({'name':link['name'],'work':link['work'],'replayed_cells':len(c),'events':len(ev)})
neighbors=((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))
attached=set();contacts=[]
for p in orn:
    for d in neighbors:
        q=tuple(p[i]+d[i] for i in range(3))
        if q in body:
            lab=int(labels[tuple(np.array(p)-lo)]);attached.add(lab);contacts.append(p);break
sizes=np.bincount(labels.ravel())[1:]
initial=readlist(DES/'ornament.vox.txt')
img=np.array(Image.open(DES/'ornament_stern_cell_plan.png').convert('RGB'))
H,W=img.shape[:2];bg=(16,38,48)
# Read drawing occupied pixels first. Image x is Y, image y is 239-Z.
draw={(int(y),int(H-1-v)) for v,y in np.argwhere(np.any(img!=bg,axis=2))}
proj={(y,z) for x,y,z in orn};oldproj={(y,z) for x,y,z in initial}
expected_rgb=np.zeros_like(img);expected_rgb[:]=bg
projection={}
for (x,y,z),c in orn.items():projection[y,z]=max(c,projection.get((y,z),0))
for (y,z),c in projection.items():
    if 0<=H-1-z<H and 0<=y<W:expected_rgb[H-1-z,y]=[((c>>5)&7)*255//7,((c>>2)&7)*255//7,(c&3)*255//3]
candidate=sorted(draw,key=lambda q:q[1],reverse=True)
tree=cKDTree(np.array(sorted(proj),float)+.5)
# Apply translation to actual geometry, never datum/image. Select exposed image pixel.
shifted=cKDTree(np.array(sorted(proj),float)+.5+np.array([0,3]))
probe=next(p for p in candidate if abs(shifted.query(np.array(p)+.5)[0]-3)<1e-9)
shift_distance=float(shifted.query(np.array(probe)+.5)[0])
# Real asset mutants, in memory only.
mut=dict(orn);floating=(0,0,0);mut[floating]=218
ma,_=grid(mut);_,mn=ndi.label(ma)
asym=dict(orn);q=next(p for p in orn if p[1]!=120);asym.pop(q)
shell={(x,y,z):218 for x in range(3) for y in range(3) for z in range(3) if (x,y,z)!=(1,1,1)}
sa,_=grid(shell)
ledger_mut=dict(orn);first=next(iter(ledger_mut));ledger_mut[first]=(ledger_mut[first]+1)%256
hole_mut=a.copy();center=np.array([200,120,200])-lo
for dx in (-1,0,1):
    for dy in (-1,0,1):
        for dz in (-1,0,1):
            if (dx,dy,dz)!=(0,0,0):hole_mut[tuple(center+[dx,dy,dz])]=True
actual_hole_mutant=int((ndi.binary_fill_holes(hole_mut)&~hole_mut).sum())
extra=sorted(proj-draw)
extra_details=[]
for y,z in extra:
    extra_details.append({'y':y,'z':z,'image_x':y,'image_y':H-1-z,'current_cells':[[x,yy,zz,c] for (x,yy,zz),c in orn.items() if yy==y and zz==z]})
(OUT/'drawing_extra_pixels.json').write_text(json.dumps(extra_details,indent=2)+'\n',encoding='utf-8')
Image.fromarray(expected_rgb).resize((W*3,H*3),Image.Resampling.NEAREST).save(OUT/'readback_projection_rgb332_x3.png')
diffview=expected_rgb.copy()
for y,z in extra:diffview[H-1-z,y]=[255,64,64]
Image.fromarray(diffview).resize((W*3,H*3),Image.Resampling.NEAREST).save(OUT/'readback_projection_extra44_red_x3.png')
report={'method':'Independent event replay, exact list comparison, scipy 6-neighbor labeling/fill, original PNG pixel inventory. No author checker or design module imported. Assembly here includes linked voxel works only; external models/sails/ropes excluded.',
 'ornament_count':len(orn),'bbox':[np.array(list(orn)).min(0).tolist(),np.array(list(orn)).max(0).tolist()], 'events':events,
 'cache_delta':delta(orn,cache),'design_union_delta':delta(orn,expected),'mirror_y120':mirror(orn),
 'components_6':int(n),'component_sizes':sorted(map(int,sizes),reverse=True),'enclosed_empty_cells':int(holes.sum()),
 'body_links':link_stats,'body_cells':len(body),'body_overlap':len(orn.keys()&body.keys()),'face_contact_cells':len(set(contacts)),'attached_components':len(attached),'unattached_components':[int(i) for i in range(1,n+1) if i not in attached],
 'drawing':{'path':str(DES/'ornament_stern_cell_plan.png'),'sha256':sha(DES/'ornament_stern_cell_plan.png'),'dimensions':[W,H],'occupied_pixels':len(draw),'drawing_pixels_absent_current_projection':len(draw-proj),'current_projection_extra_pixels':len(proj-draw),'initial_projection_missing':len(draw-oldproj),'initial_projection_extra':len(oldproj-draw),'pixels_differ_from_current_correct_rgb332':int(np.any(img!=expected_rgb,axis=2).sum()),'actual_unique_rgb':np.unique(img.reshape(-1,3),axis=0).tolist(),'limitation':'Back projection collapses all X; confirms silhouette occupancy only, not unique source voxel or fine spatial separation.'},
 'negative_controls':{'drawing_pixel_probe_yz':probe,'baseline_distance':float(tree.query(np.array(probe)+.5)[0]),'all_actual_projection_Zplus3_distance':shift_distance,'floating_voxel':floating,'floating_mutant_components':int(mn),'baseline_components':int(n),'remove_one_noncentral_voxel_mirror':mirror(asym),'recolor_one_voxel_ledger':delta(ledger_mut,expected),'synthetic_3x3x3_shell_cavity_cells':int((ndi.binary_fill_holes(sa)&~sa).sum()),'actual_ornament_plus_26_cell_shell_cavity_cells':actual_hole_mutant,'cavity_mutant_center':[200,120,200]},
 'source_hashes':{str(DES/name):sha(DES/name) for name in ['ornament.vox.txt','ornament_root_correction.vox.txt','raised_flag_staff.vox.txt','ornament_plan.json','references/README.md']}}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['events','component_sizes','body_links','source_hashes']},ensure_ascii=False,indent=2))
