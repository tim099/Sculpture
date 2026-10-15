import sys,hashlib
sys.path.insert(0,r'D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/attachment_audit')
from clearance import *
Q=P/'anchors_final';Q.mkdir(exist_ok=True)
src=pathlib.Path('D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m-anchor');cache=(src/'sculpt_cache.json').read_bytes();sc=json.loads(cache);V=np.array([list(map(int,k.split(',')))for k in sc['voxels']],float);pivot=np.array([23.5,16.5,56.5]);rawm=zlib.decompress((P/'route_explore/manual_candidate.vxk').read_bytes(),-15);nn=struct.unpack_from('<I',rawm,4)[0];RIG=json.loads(rawm[8:8+nn])['rig'];RR=RIG['ropes'];bodyset=set(map(tuple,BODY.astype(int)))
def rot(a):
 t=np.radians(a);c=np.cos(t);s=np.sin(t);return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def obbbody(at,T):
 centers=(V+.5-pivot)@T.T+at;axes=[*np.eye(3),*T.T];axes +=[np.cross(a,b) for a in np.eye(3) for b in T.T];axes=[a/np.linalg.norm(a) for a in axes if np.linalg.norm(a)>1e-8];bad=[]
 for i,c in enumerate(centers):
  ids=tree.query_ball_point(c,1.75);d=BODY[ids]+.5-c;ok=np.ones(len(ids),bool)
  for ax in axes:ok &= abs(d@ax)<(.5*np.sum(abs(ax))+.5*np.sum(abs(T.T@ax))-1e-8)
  if np.any(ok):bad.extend((i,ids[k])for k in np.flatnonzero(ok))
 return bad

def ropehits(at,T):
 out=[]
 for r in RR:
  p=(np.array(r['pts']).reshape(-1,3)-at)@T+pivot;rad=r['radius']
  if np.any(p.max(0)+rad<V.min(0))or np.any(p.min(0)-rad>V.max(0)+1):continue
  for a,b in zip(p[:-1],p[1:]):
   ds,t=boxdist(a,b,V)
   if ds.min()<rad*rad-1e-9:out.append((r['name'],float(ds.min()**.5)));break
 return out
def tri_box(tr,lo):
 tr=tr-(lo+.5);axes=[*np.eye(3)];edges=np.roll(tr,-1,axis=1)-tr
 axes.append(np.cross(edges[:,0],edges[:,1]))
 for j in range(3):
  for ax in np.eye(3):axes.append(np.cross(edges[:,j],ax))
 ok=np.ones(len(tr),bool)
 for ax in axes:
  if ax.ndim==1: proj=tr@ax;rad=.5*np.sum(abs(ax))
  else:proj=np.einsum('ijk,ik->ij',tr,ax);rad=.5*np.sum(abs(ax),axis=1)
  ok&=(proj.min(1)<rad-1e-8)&(proj.max(1)>-rad+1e-8)
 return ok

def modelhits(at,T):
 lo=((V-pivot)@T.T+at).min(0)-2;hi=((V+1-pivot)@T.T+at).max(0)+2;out=[]
 for m in RIG['models']:
  bb=np.array(m['bbox'])
  if np.any(bb[3:]<lo)or np.any(bb[:3]>hi):continue
  mesh=RIG['meshes'][m['mesh']];verts=(np.array(mesh['verts']).reshape(-1,3)+m['origin']-at)@T+pivot;tr=verts[np.array(mesh['tris']).reshape(-1,3)];tl=tr.min(1);th=tr.max(1);hits=[]
  for i,v in enumerate(V):
   mask=np.all(th>v+1e-8,axis=1)&np.all(tl<v+1-1e-8,axis=1)
   if np.any(mask)and np.any(tri_box(tr[mask],v)):hits.append(i)
   elif np.all(v+.5>verts.min(0))and np.all(v+.5<verts.max(0))and inside(v+.5,tr):hits.append(i)
  if hits:out.append({'model':m['name'],'source_voxels':V[hits].tolist()})
 return out

def segseg(a,b,c,d):
 u=b-a;v=d-c;w=a-c;A=u@u;B=v@u;C=np.sum(v*v,axis=1);D=w@u;E=np.sum(v*w,axis=1);den=A*C-B*B;s=np.clip(np.divide(B*E-C*D,den,out=np.zeros(len(c)),where=abs(den)>1e-14),0,1);t=np.clip(np.divide(B*s+E,C,out=np.zeros(len(c)),where=C>0),0,1);s=np.clip((B*t-D)/(A or 1),0,1);t=np.clip(np.divide(B*s+E,C,out=np.zeros(len(c)),where=C>0),0,1);return np.linalg.norm(w+s[:,None]*u-t[:,None]*v,axis=1)
results=[]
for side,at,angle,hawse in [('P',[560.5,88.5,155.5],-20,[560,94,150]),('S',[560.5,152.5,155.5],20,[560,146,150])]:
 at=np.array(at);T=rot(angle);foot=np.array(hawse)+.5;rad=.35;bodyhits=obbbody(at,T);modhits=modelhits(at,T);rh=ropehits(at,T);dd,tt=boxdist(at,foot,BODY);bodycontact=BODY[dd<rad*rad-1e-8];cablemods=[]
 for m in RIG['models']:
  bb=np.array(m['bbox'])
  if np.any(bb[3:]<np.minimum(at,foot)-rad)or np.any(bb[:3]>np.maximum(at,foot)+rad):continue
  me=RIG['meshes'][m['mesh']];v=np.array(me['verts']).reshape(-1,3)+m['origin'];tr=v[np.array(me['tris']).reshape(-1,3)];ds=segtri(at,foot,tr)
  if ds.min()<rad*rad:cablemods.append([m['name'],float(ds.min()**.5)])
 cableother=[]
 for r in RR:
  p=np.array(r['pts']).reshape(-1,3);ds=segseg(at,foot,p[:-1],p[1:])
  if ds.min()<rad+r['radius']-1e-8:cableother.append([r['name'],float(ds.min()),rad+r['radius']])
 la=(at-at)@T+pivot;lb=(foot-at)@T+pivot;ds,t=boxdist(la,lb,V);selfhit=V[ds<rad*rad-1e-8]
 results.append({'side':side,'source':src.name,'at':at.tolist(),'pivot':pivot.tolist(),'rotate':[angle,0,0],'scale':1,'hawse_anchor':'hawse-'+side,'hawse_at_cell':hawse,'hawse_world':foot.tolist(),'ring_world':at.tolist(),'short_rope_radius':rad,'short_rope_length':float(np.linalg.norm(at-foot)),'anchor_body_penetrations':len(bodyhits),'anchor_model_contacts':modhits,'anchor_old_rope_contacts':rh,'cable_body_cells':bodycontact.tolist(),'cable_model_contacts':cablemods,'cable_old_rope_contacts':cableother,'cable_own_ring_contact_source_cells':selfhit.tolist(),'nearest_wood_center':float(tree.query(at)[0])})
result={'input_sha256':hashlib.sha256((P/'route_explore/manual_candidate.vxk').read_bytes()).hexdigest(),'source_cache_sha256':hashlib.sha256(cache).hexdigest(),'source_voxels':len(V),'models_checked':len(RIG['models']),'ropes_checked':len(RR),'placements':results,'scope':'Exact source voxel OBB/body SAT; transformed actual model triangle SAT plus solid containment; capsule/cube source-space and segment/segment old rope checks in exported author pose. No full arbitrary moving-yard proof claimed.'};(Q/'DESIGN.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=True))
