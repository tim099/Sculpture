import json,zlib,struct,hashlib,math,time
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,MultiPoint,box
from shapely.ops import unary_union
from shapely.prepared import prep
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'input'
start=time.time(); raw=zlib.decompress((SRC/'final_heads.vxk').read_bytes(),-15); n=struct.unpack_from('<I',raw,4)[0]; h=json.loads(raw[8:8+n]); p=8+n; nc=h['nchunks']; keys=np.frombuffer(raw,dtype='<u2',count=nc*3,offset=p).reshape(-1,3);p+=nc*6
body=[]
for k,dat in zip(keys,np.frombuffer(raw,dtype='u1',offset=p).reshape(nc,4096)):
 ids=np.flatnonzero(dat);body.extend(np.c_[ids%16,ids//16%16,ids//256]+k*16)
body=np.array(body); yards=json.loads((SRC/'independent/frozen_yards.json').read_text())['yards']
models=h['rig']['models']; fixed=[m for m in models if m.get('meta',{}).get('kind')!='yard']
def clipped(poly,level,above):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  aa=a[2]>=level if above else a[2]<=level;bb=b[2]>=level if above else b[2]<=level
  if aa:out.append(a)
  if aa!=bb:out.append(a+(b-a)*((level-a[2])/(b[2]-a[2])))
 return out
mesh=[]
for m in fixed:
 v=np.array(h['rig']['meshes'][m['mesh']]['verts']).reshape(-1,3)+m['origin'];t=v[np.array(h['rig']['meshes'][m['mesh']]['tris']).reshape(-1,3)]
 mesh.append((m['name'],t,t.min(axis=1)[:,2],t.max(axis=1)[:,2]))
def solids(z0,z1):
 objs=[];b=body[(body[:,2]<z1)&(body[:,2]+1>z0)]
 if len(b):
  # Union identical xy voxels across the source box's z slab.
  xy=np.unique(b[:,:2],axis=0); objs.append(('body',unary_union([box(x,y,x+1,y+1) for x,y in xy])))
 for name,t,lo,hi in mesh:
  cand=t[(lo<z1)&(hi>z0)];pol=[]
  for tri in cand:
   a=clipped(list(tri),z0,True)
   if a:a=clipped(a,z1,False)
   if len(a)>=3:
    q=MultiPoint(np.array(a)[:,:2]).convex_hull
    if q.area>1e-12:pol.append(q)
  if pol:objs.append((name,unary_union(pol)))
 return objs
cache={}
def boxes(y):
 c=np.array(y['cubes']); groups={}
 pv=np.array(y['piv'])
 for x,yy,z in c:
  radial=max(math.hypot(xx-pv[0],yyy-pv[1]) for xx in (x,x+1) for yyy in (yy,yy+1))
  groups.setdefault((x,z,radial<=8),[]).append(yy)
 out=[]
 for (x,z,central),ys in groups.items():
  ys=sorted(ys);a=b=ys[0]
  for yy in ys[1:]+[float('inf')]:
   if yy!=b+1:out.append((np.array([x,a,z]),np.array([x+1,b+1,z+1])));a=yy
   b=yy
 return out
def corners(lo,hi,piv):return np.array([[lo[0],lo[1]],[lo[0],hi[1]],[hi[0],hi[1]],[hi[0],lo[1]]])-np.array(piv[:2])
def rotated(c,a,at):
 co=math.cos(a);si=math.sin(a);return c@np.array([[co,si],[-si,co]])+at[:2]
stats={'intervals':0,'proof_leaves':0,'unresolved':0}; results=[]
def check(c,at,geom,a,b,depth=0):
 stats['intervals']+=1;mid=(a+b)/2;r=float(np.linalg.norm(c,axis=1).max());err=r*(b-a)**2/8+1e-9
 hull=MultiPoint(np.concatenate([rotated(c,a,at),rotated(c,mid,at),rotated(c,b,at)])).convex_hull.buffer(err,resolution=8)
 # circumscribe polygonal buffer: Shapely's buffer chords are inscribed.
 hull=MultiPoint(np.concatenate([rotated(c,a,at),rotated(c,mid,at),rotated(c,b,at)])).convex_hull.buffer(err/math.cos(math.pi/32),resolution=8)
 if not geom.intersects(hull):stats['proof_leaves']+=1;return None
 poly=Polygon(rotated(c,mid,at));inter=geom.intersection(poly)
 if inter.area>1e-8:return {'angle':mid,'intersection_area_xy':inter.area,'point':list(inter.representative_point().coords)[0]}
 if depth>=20:stats['unresolved']+=1;return {'unresolved_angle_interval':[a,b],'error_bound':err}
 return check(c,at,geom,a,mid,depth+1) or check(c,at,geom,mid,b,depth+1)
for y in yards:
 at=np.array(y['at']);pv=np.array(y['piv']);limit=1.4 if y['meta']['yard'] in ('gaff','boom') else .7
 out={'name':y['name'],'range':[-limit,limit],'cube_count':len(y['cubes']),'cuboid_count':0,'z_eliminated_models':[],'tested_models':[],'contacts':[],'central_attachments':[]}
 zlo=min(c[2] for c in y['cubes'])-pv[2]+at[2];zhi=max(c[2]+1 for c in y['cubes'])-pv[2]+at[2]
 out['z_span']=[zlo,zhi]
 out['z_eliminated_models']=[m['name'] for m in fixed if m['bbox'][5]<=zlo or m['bbox'][2]>=zhi]
 for lo,hi in boxes(y):
  out['cuboid_count']+=1;c=corners(lo,hi,pv);z0=lo[2]-pv[2]+at[2];z1=hi[2]-pv[2]+at[2]
  if (z0,z1) not in cache:cache[z0,z1]=solids(z0,z1)
  central=np.linalg.norm(c,axis=1).max()<=8
  for name,g in cache[z0,z1]:
   hit=check(c,at,g,-limit,limit)
   if hit:
    item={'static':name,'source_box':[lo.tolist(),hi.tolist()],'pivot_radius_max':float(np.linalg.norm(c,axis=1).max()),**hit}
    (out['central_attachments'] if central and name=='body' else out['contacts']).append(item)
   if name not in out['tested_models']:out['tested_models'].append(name)
 results.append(out);(ROOT/'progress.json').write_text(json.dumps({'results':results,'stats':stats},indent=2));print(y['name'],len(out['contacts']),len(out['central_attachments']),flush=True)
def swept(c,at,a,b):
 mid=(a+b)/2;r=float(np.linalg.norm(c,axis=1).max());err=(r*(b-a)**2/8+1e-9)/math.cos(math.pi/32)
 return MultiPoint(np.concatenate([rotated(c,a,at),rotated(c,mid,at),rotated(c,b,at)])).convex_hull.buffer(err,resolution=8)
pair_stats={'intervals':0,'proof_leaves':0,'unresolved':0}
def dual(ca,aa,cb,ab,la,ha,lb,hb,depth=0):
 pair_stats['intervals']+=1
 if not swept(ca,aa,la,ha).intersects(swept(cb,ab,lb,hb)):pair_stats['proof_leaves']+=1;return None
 ma=(la+ha)/2;mb=(lb+hb)/2;inter=Polygon(rotated(ca,ma,aa)).intersection(Polygon(rotated(cb,mb,ab)))
 if inter.area>1e-8:return {'angles':[ma,mb],'intersection_area_xy':inter.area,'point':list(inter.representative_point().coords)[0]}
 if depth>=26:pair_stats['unresolved']+=1;return {'unresolved_intervals':[[la,ha],[lb,hb]]}
 ra=np.linalg.norm(ca,axis=1).max();rb=np.linalg.norm(cb,axis=1).max()
 if (ha-la)*ra>(hb-lb)*rb:return dual(ca,aa,cb,ab,la,ma,lb,hb,depth+1) or dual(ca,aa,cb,ab,ma,ha,lb,hb,depth+1)
 return dual(ca,aa,cb,ab,la,ha,lb,mb,depth+1) or dual(ca,aa,cb,ab,la,ha,mb,hb,depth+1)
def yardpair(ya,yb):
 hits=[];aa=np.array(ya['at']);ab=np.array(yb['at']);pa=np.array(ya['piv']);pb=np.array(yb['piv']);la=1.4 if ya['meta']['yard'] in ('gaff','boom') else .7;lb=1.4 if yb['meta']['yard'] in ('gaff','boom') else .7
 count=0
 for al,ah in boxes(ya):
  za=[al[2]-pa[2]+aa[2],ah[2]-pa[2]+aa[2]]
  for bl,bh in boxes(yb):
   zb=[bl[2]-pb[2]+ab[2],bh[2]-pb[2]+ab[2]]
   if za[1]<=zb[0] or zb[1]<=za[0]:continue
   count+=1;hit=dual(corners(al,ah,pa),aa,corners(bl,bh,pb),ab,-la,la,-lb,lb)
   if hit:
    hits.append({'source_boxes':[[al.tolist(),ah.tolist()],[bl.tolist(),bh.tolist()]],'z_overlap':[max(za[0],zb[0]),min(za[1],zb[1])],**hit})
    if 'angles' in hit:return {'cuboid_pairs_tested':count,'hits':hits}
 return {'cuboid_pairs_tested':count,'hits':hits}
pair=[]
for i,a in enumerate(results):
 for b in results[i+1:]:
  if a['z_span'][1]<=b['z_span'][0] or b['z_span'][1]<=a['z_span'][0]:pair.append({'a':a['name'],'b':b['name'],'proof':'disjoint invariant z slabs; independent asynchronous angles irrelevant'})
  else:pair.append({'a':a['name'],'b':b['name'],'proof':'independent two-angle recursive conservative envelopes',**yardpair(yards[i],next(y for y in yards if y['name']==b['name']))})
actual_pair_stats=dict(pair_stats)
old=json.loads(json.dumps(yards[0]));old['at'][2]=255.5
negative={'mutation':'crossjack at.z restored from 224.5 to 255.5','against_gaff':yardpair(old,yards[2]),'unchanged_new_crossjack_z':yards[0]['at'][2]}
best={'intersection_area_xy':0}
for al,ah in boxes(old):
 za=[al[2]-old['piv'][2]+old['at'][2],ah[2]-old['piv'][2]+old['at'][2]];ca=corners(al,ah,old['piv'])
 for bl,bh in boxes(yards[2]):
  zb=[bl[2]-yards[2]['piv'][2]+yards[2]['at'][2],bh[2]-yards[2]['piv'][2]+yards[2]['at'][2]]
  if za[1]<=zb[0] or zb[1]<=za[0]:continue
  cb=corners(bl,bh,yards[2]['piv'])
  for ang in np.linspace(-.7,.7,15):
   pa=Polygon(rotated(ca,ang,np.array(old['at'])))
   for bang in np.linspace(-1.4,1.4,29):
    inter=pa.intersection(Polygon(rotated(cb,bang,np.array(yards[2]['at']))))
    if inter.area>best['intersection_area_xy']:best={'angles':[float(ang),float(bang)],'intersection_area_xy':inter.area,'z_overlap':[max(za[0],zb[0]),min(za[1],zb[1])],'point':list(inter.representative_point().coords)[0],'source_boxes':[[al.tolist(),ah.tolist()],[bl.tolist(),bh.tolist()]]}
negative['robust_exact_witness']=best
report={'input_sha256':hashlib.sha256((SRC/'final_heads.vxk').read_bytes()).hexdigest(),'body_cells':len(body),'models':len(models),'fixed_models':len(fixed),'results':results,'yard_pairs':pair,'stats':stats,'seconds':time.time()-start,'method':'Exact source unit cubes merged only as contiguous same-x,z y runs. Rotation is absolute game angle; z invariant. Static triangle surfaces clipped exactly to moving prism z slab then projected to XY. Continuous interval swept OBB contains corner trajectories: convex hull endpoint+midpoint with outward sagitta r*delta^2/8, circumscribed numerical buffer. Recursive disjointness proof; midpoint positive-area intersection witnesses. Body union of occupied unit cubes. Central <=8 voxel-radius source boxes against body are quantified attachments, never removes noncentral or model contacts. Mesh-interior containment without surface crossing is not certified.'}
report['yard_pair_stats']=actual_pair_stats;report['negative_control']=negative
report['negative_control_interval_stats']={k:pair_stats[k]-actual_pair_stats[k] for k in pair_stats}
report['input_frozen_yards_sha256']=hashlib.sha256((SRC/'independent/frozen_yards.json').read_bytes()).hexdigest()
report['frozen_yards_match_snapshot']=json.loads((SRC/'independent/frozen_yards.json').read_text())['snapshot_vxk_sha256']==report['input_sha256']
report['fixed_model_invariant_z_eliminations']=sum(len(r['z_eliminated_models']) for r in results)
report['central_attachment_box_count']=sum(len(r['central_attachments']) for r in results)
report['central_attachment_max_witness_radius']=max(math.hypot(c['point'][0]-y['at'][0],c['point'][1]-y['at'][1]) for y,r in zip(yards,results) for c in r['central_attachments'])
canonical=lambda obj:json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
gh={'body_cell_coordinates_sha256':hashlib.sha256(body.astype('<i8').tobytes()).hexdigest(),'models_meshes_canonical_sha256':hashlib.sha256(canonical({'models':models,'meshes':h['rig']['meshes']})).hexdigest(),'yard_geometry_canonical_sha256':hashlib.sha256(canonical([{k:y[k] for k in ('name','cubes','piv','at','r0')} for y in yards])).hexdigest(),'serialization':'body: VXK chunk traversal, little-endian int64 XYZ rows; models/meshes and yard fields: json sort_keys=True,separators=(comma,colon),ensure_ascii=True, ASCII'}
(ROOT/'geometry_hashes.json').write_text(json.dumps(gh,indent=2));report['geometry_hashes']=gh
(ROOT/'report.json').write_text(json.dumps(report,indent=2));print('DONE',stats,time.time()-start)
