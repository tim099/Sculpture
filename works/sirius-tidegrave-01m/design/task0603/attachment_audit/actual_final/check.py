import sys,pathlib,json,zlib,struct,hashlib
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent.parent))
from clearance import *
from prototype import gunprototype
Q=pathlib.Path(__file__).parent
bb=(Q/'input.vxk').read_bytes();ar=zlib.decompress(bb,-15);an=struct.unpack_from('<I',ar,4)[0];AH=json.loads(ar[8:8+an]);A=AH['rig'];am={m['name']:m for m in A['models']};ars={r['name']:r for r in A['ropes']}
assert len(A['ropes'])==497 and len(A['models'])==166 and len(A['sails'])==10
assert ar[8+an:]==raw[8+n:], 'body byte delta'
assert A['sails']==R['sails']
for m in R['models']:
 a=am[m['name']];assert {k:v for k,v in a.items()if k!='mesh'}=={k:v for k,v in m.items()if k!='mesh'};assert A['meshes'][a['mesh']]==R['meshes'][m['mesh']]
plans=json.loads((P/'route_clearance.json').read_text(encoding='utf8'));wheel=json.loads((P/'wheel_route.json').read_text(encoding='utf8'));changed={x['rope']for x in plans}|{'steer-wheel-S'}
for r in R['ropes']:
 if r['name']not in changed:assert ars[r['name']]==r
for rr in plans+[{'rope':'steer-wheel-S',**wheel}]:
 names=[rr['rope'],rr['rope']+'.guide',rr['rope']+'.wall'] if rr['rope']!='steer-wheel-S'else[rr['rope']]+[rr['rope']+'.guide'+str(i)for i in [1,2,3]]
 for i,name in enumerate(names):
  r=ars[name];assert r['pts']==np.array(rr['route'][i:i+2]).reshape(-1).tolist(),name;assert r['radius']==.25
  original=next(x for x in R['ropes']if x['name']==rr['rope'])
  for key in ['color','frame','meta']:
   assert r.get(key)==original.get(key),(name,key)
  if i==0:assert r['ends'][0]==original['ends'][0]
  if i==len(names)-1:assert r['ends'][1]==original['ends'][1]
def voxelize(mesh):
 vs=np.array(mesh['verts']).reshape(-1,3);tr=vs[np.array(mesh['tris']).reshape(-1,3)];lo=vs.min(axis=0);hi=vs.max(axis=0);cells=[]
 for y in np.arange(lo[1],hi[1],.5):
  for z in np.arange(lo[2],hi[2],.5):
   origin=np.array([lo[0]-1,y+.25,z+.25]);tt,ok=ray(origin,np.array([1.,0,0]),tr);ts=np.unique(np.round(tt[ok&(tt>0)],8));assert len(ts)%2==0
   for x in np.arange(lo[0],hi[0],.5):
    if np.count_nonzero(ts>x+.25-origin[0])%2:cells.append([x,y,z])
 return np.array(cells)
guides=[m for m in A['models']if m['meta'].get('kind')=='fairlead'];assert len(guides)==50
assert len({m['meta']['gun_mount']for m in guides if 'gun_mount'in m['meta']})==48
types={m['mesh']:voxelize(A['meshes'][m['mesh']])for m in guides};local,_=gunprototype();worlds=[];geom=[]
def tuples(a):return {tuple(x)for x in np.rint(a*1000000).astype(int)}
for m in guides:
 actual=types[m['mesh']]+m['origin'];worlds.extend(actual)
 if 'gun_mount'in m['meta']:
  gun=am[m['meta']['gun_mount']];C=np.array(gun['points']['cascabel']);sg=np.sign(gun['points']['muzzle'][1]-gun['points']['breech'][1]);expected=local.copy()
  if sg<0:expected[:,:2]=-expected[:,:2]-.5
  expected+=C-[0,0,11.5]
 else:expected=np.load(P/(m['name'].replace('-','_')+'_world.npy'))
 assert tuples(actual)==tuples(expected),m['name'];geom.append({'name':m['name'],'cubes':len(actual),'expected_equal':True})
cells=np.array(worlds);ct=cKDTree(cells+.25);contacts=[]
for r in A['ropes']:
 pp=np.array(r['pts']).reshape(-1,3)
 for i,(a,b) in enumerate(zip(pp[:-1],pp[1:])):
  cc=cells[ct.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+.434+r['radius']))]
  if not len(cc):continue
  dd,tt=boxdist(2*a,2*b,2*cc)
  if dd.min()<(2*r['radius'])**2-1e-9:contacts.append({'rope':r['name'],'segment':i,'distance':float(dd.min()**.5/2)})
assert not contacts
# Actual exported guide cells are exactly equal to the independent proposal.
# Prior SAT/body/foot checks therefore apply to these current exact bytes after
# the above bitwise body and geometric equality assertions, without guessing
# mesh triangulation or trusting author placement metadata.
result={'sha256':hashlib.sha256(bb).hexdigest(),'bytes':len(bb),'ropes':len(A['ropes']),'models':len(A['models']),'guide_models':len(guides),'guide_cubes':len(cells),'guide_mesh_types':{str(k):len(v)for k,v in types.items()},'body_bytes_identical':True,'original_116_model_geometry_and_meta_identical':True,'ten_sails_identical':True,'unchanged_205_ropes_identical':True,'changed_routes_and_radius_exact':True,'all_guide_meshes_equal_independent_solid_design':True,'all_497_rope_capsules_vs_actual_guide_solids_contacts':contacts,'geometry':geom,'verdict':'PASS attachment repair exact export'}
yards=[m for m in A['models']if m['meta'].get('kind')=='yard'];separation=[]
for g in guides:
 for y in yards:
  gap=max(y['bbox'][2]-g['bbox'][5],g['bbox'][2]-y['bbox'][5]);assert gap>0,(g['name'],y['name']);separation.append(gap)
result['rope_color_frame_meta_and_original_terminal_refs_preserved']=True
result['guide_vs_yard_all_angle_Z_separation']={'yard_count':len(yards),'pairs':len(separation),'minimum_gap':min(separation)}
for gi,g in enumerate(guides):
 for h in guides[gi+1:]:
  overlap=np.minimum(g['bbox'][3:],h['bbox'][3:])-np.maximum(g['bbox'][:3],h['bbox'][:3]);assert np.any(overlap<=0),(g['name'],h['name'])
result['all_1225_guide_pairs_AABB_disjoint']=True
(Q/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k!='geometry'},ensure_ascii=True))
