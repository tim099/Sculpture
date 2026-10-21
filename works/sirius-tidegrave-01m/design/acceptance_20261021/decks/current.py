"""Independent VXK format reader and fixed path envelope checker; no project imports."""
import json,struct,zlib,hashlib,math
from pathlib import Path
import numpy as np
from scipy.ndimage import label,binary_fill_holes,generate_binary_structure
O=Path(__file__).parent;S=O.parent/'shared';R=Path('D:/Unity/Valhalla/Sculpture/works');D=R/'sirius-tidegrave-01m/design'
blob=(S/'current.vxk').read_bytes();raw=zlib.decompress(blob,-15);assert raw[:4]==b'VXK1';n=struct.unpack_from('<I',raw,4)[0];h=json.loads(raw[8:8+n]);pos=8+n;N=h['nchunks'];coords=np.frombuffer(raw,dtype='<u2',count=3*N,offset=pos).reshape(N,3);pos+=6*N
cells={}
for i,org in enumerate(coords):
 block=raw[pos+i*4096:pos+(i+1)*4096]
 for j,c in enumerate(block):
  if c:cells[(int(org[0])*16+j%16,int(org[1])*16+j//16%16,int(org[2])*16+j//256)]=c
parts=json.loads((S/'parts.json').read_text(encoding='utf8'));lp=next(p for p in parts['links'] if p['meta'].get('kind')=='ladders');paths={}
for name,q in lp['points'].items():
 stem,role=name.rsplit('.',1);v=[q[0],q[1],math.floor(q[2])];v[2]+=3 if role in ['lo','hi'] else 0;paths.setdefault(stem,{})[role]=v
def collision(a,b,V):
 # Solve the X slab time interval first. Z is affine there, so its extrema
 # lie at the interval endpoints. Y does not move for this specified path.
 hits=[];dx=b[0]-a[0];dz=b[2]-a[2]
 assert a[1]==b[1] and dx!=0
 for x,y,z in V:
  if y+1<=a[1]-3.5 or y>=a[1]+3.5:continue
  ta,tb=sorted(((x-a[0])/dx,(x+1-a[0])/dx));lo=max(0,ta);hi=min(1,tb)
  if hi-lo<=1e-9:continue
  za=a[2]+dz*lo;zb=a[2]+dz*hi
  if max(za,zb)>z-18+1e-9 and min(za,zb)<z+1-.001-1e-9:hits.append((x,y,z))
 return hits
routes=[];landings=[]
for name,p in sorted(paths.items()):
 path=[p[k] for k in ['foot','lo','hi','head']];hits=[collision(path[i],path[i+1],cells) for i in range(3)];routes.append({'name':name,'path':path,'obstacles':[len(a) for a in hits],'examples':[a[:4] for a in hits]})
 for key in ['foot','head']:
  x,y,z=map(math.floor,p[key]);landings.append({'name':name+'.'+key,'floor':(x,y,z-1) in cells,'headroom14':sum((x,y,zz) in cells for zz in range(z,z+14))})
# Replay seven children to assert every retained voxel/color survives assembly export.
children=[]
for p in parts['links']:
 if p['meta'].get('kind') not in ['deck','ladders']:continue
 a={}
 for f in sorted((R/p['work']/'events').rglob('*.json')):
  e=json.loads(f.read_text(encoding='utf8'))
  for q in e.get('carved_voxels',[]):a.pop(tuple(q[:3]),None)
  for q in e.get('placed_colored',[]):a[tuple(q[:3])]=q[3]
 children.append({'work':p['work'],'count':len(a),'missing_in_assembly':sum(q not in cells for q in a),'color_in_assembly':sum(cells.get(q)!=c for q,c in a.items()),'turn':p['turn'],'box':p['box']})
# independently characterize later PNG update as current projection, preserving historical differences.
png=[]
for child in children:
 if '-deck-' not in child['work']:continue
 a={}
 for f in sorted((R/child['work']/'events').rglob('*.json')):
  e=json.loads(f.read_text(encoding='utf8'))
  for q in e.get('carved_voxels',[]):a.pop(tuple(q[:3]),None)
  for q in e.get('placed_colored',[]):a[tuple(q[:3])]=q[3]
 from PIL import Image
 name=child['work'].split('-deck-')[1];im=np.array(Image.open(D/('deck_'+name+'_cell_plan.png')).convert('RGB'));proj={q[:2] for q in a};pix={(x,240-y) for y in range(241) for x in range(800) if tuple(im[y,x])!=(16,38,48)}
 png.append({'deck':name,'png_missing_from_current':len(pix-proj),'current_missing_from_png':len(proj-pix),'examples_missing_png':sorted(proj-pix)[:20]})
v=np.array(list(cells),dtype=int);low=v.min(0)-1;high=v.max(0)+1;arr=np.zeros(tuple(high-low+1),bool);arr[tuple((v-low).T)]=True;_,count=label(arr,structure=generate_binary_structure(3,1));holes=int(np.sum(binary_fill_holes(arr)&~arr))
restored=(176,117,157);negative=collision(paths['quarter-poop']['lo'],paths['quarter-poop']['hi'],[restored])
report={'vxk_sha256':hashlib.sha256(blob).hexdigest(),'parts_sha256':hashlib.sha256((S/'parts.json').read_bytes()).hexdigest(),'current_voxels':len(cells),'header_checksum':h['checksum'],'children':children,'png_current':png,'routes':routes,'landings':landings,'whole_current_structure':{'components6':int(count),'enclosed_empty':holes},'negative_control':{'memory_only_restore':restored,'currently_empty':restored not in cells,'quarter_poop_middle_obstacles':len(negative)},'scope':'Static voxel four-point route; lift3 height18 transverse7; no model/rope/sail/avatar collision or game nav claim','assets_modified':False}
(O/'current.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
