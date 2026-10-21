"""Readonly independent proposal verification; no other checker imports."""
import json,math,hashlib,itertools
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
O=Path(__file__).resolve().parent
P=O.parent/'hardware/bearing_proposal'
B=Path('D:/Unity/Valhalla/Sculpture/works')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def read(p):
 a={}
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if l.strip() and not l.startswith('#'):
   v=list(map(int,l.split(',')));a[tuple(v[:3])]=v[3]
 return a
def replay(name):
 a={}
 for p in sorted((B/name/'events').rglob('*.json')):
  e=load(p)
  for r in e.get('carved_voxels',[]):a.pop(tuple(r[:3]),None)
  for r in e.get('placed_colored',[]):a[tuple(r[:3])]=r[3]
  for r in e.get('placed_voxels',[]):a[tuple(r[:3])]=e['color']
  if e['op']=='workedit':
   for r in e['edit']['after']:
    q=(r['x'],r['y'],r['z'])
    if r['color']:a[q]=r['color']
    else:a.pop(q,None)
 return a
def components(c):
 p=np.array(list(c));lo=p.min(0);a=np.zeros(tuple(p.max(0)-lo+1),bool);a[tuple((p-lo).T)]=1
 return int(ndi.label(a)[1])
proposal_bytes=(P/'proposal.json').read_bytes();(O/'proposal_snapshot.json').write_bytes(proposal_bytes)
j=json.loads(proposal_bytes.decode('utf-8-sig'));axis=np.array(j['axis']);axis/=np.linalg.norm(axis);hinge=np.array(j['hinge']);t=j['transform'];angle=np.radians(t['rotate'][1]);c,s=np.cos(angle),np.sin(angle)
R=np.array([[c,0,s],[0,1,0],[-s,0,c]]);scale=np.array(t['scale']);pivot=np.array(t['pivot']);at=np.array(t['at'])
fixed=read(P/'fixed.vox.txt');moving=read(P/'moving.vox.txt');cut=read(P/'carve_exact.vox.txt')
f=np.array(list(fixed));m=np.array(list(moving));fc=((f+.5-pivot)*scale)@R.T+at;mc=((m+.5-pivot)*scale)@R.T+at
corn=np.array(list(itertools.product([-.5,.5],repeat=3)))
fv=(fc[:,None,:]+(corn*scale)@R.T).reshape(-1,3);mv=(mc[:,None,:]+(corn*scale)@R.T).reshape(-1,3)
local_f=(fv-hinge)@R;local_m=(mv-hinge)@R
main=replay('sirius-tidegrave-01m');rudder=replay('sirius-tidegrave-01m-rudder')
body={};links=load(B/'sirius-tidegrave-01m-assembly/links.json')['links']
for l in links:
 if not l.get('enabled',True):continue
 assert l['turn']==0 and not l.get('mirror')
 for q,col in replay(l['work']).items():body[tuple(np.array(q)+l['at'])]=col
guard_bad=[q for q,col in cut.items() if main.get(q)!=col]
post={q:c for q,c in body.items() if q not in cut};bp=np.array(list(post),float);bc=bp+.5
def overlap_pairs(centers,rotation,half,static_centers,expand=0):
 """Vectorized 15-axis SAT over KD-tree candidate pairs."""
 tree=cKDTree(static_centers);rad=float(np.linalg.norm(half)+np.sqrt(3)*(.5+expand));ids=tree.query_ball_point(centers,rad)
 counts=np.array(list(map(len,ids)));ii=np.repeat(np.arange(len(centers)),counts)
 if len(ii)==0:return np.empty((0,2),int)
 jj=np.concatenate([np.array(i,int) for i in ids if i]);d=static_centers[jj]-centers[ii];keep=np.ones(len(ii),bool)
 axes=[*np.eye(3),*rotation.T]+[np.cross(a,b) for a in np.eye(3) for b in rotation.T]
 for n in axes:
  if np.linalg.norm(n)<1e-9:continue
  lim=(.5+expand)*abs(n).sum()+abs(n@rotation)@half
  keep &= np.abs(d@n)<lim-1e-9
 return np.array([ii[keep],jj[keep]]).T
# Narrow region enough for tiny new bearing, while retaining all body cells for cylinder proof.
near=(np.linalg.norm(bc-at,axis=1)<10);nb=bc[near];npbody=bp[near]
fixed_hits=overlap_pairs(fc,R,scale/2,nb)
fixed_embed=sorted({tuple(map(int,npbody[k])) for _,k in fixed_hits})
moving_hits=overlap_pairs(mc,R,scale/2,nb)
rp=np.array(list(rudder),float);rc=rp+.5
root_hits=overlap_pairs(mc,R,scale/2,rc)
rv=(rc[:,None,:]+corn).reshape(-1,3);smax=float(((rv-hinge)@axis).max())
# Exact source grid contracts independently reconstructed from dimensions in proposal.
expf={(x,y,z) for x in range(20) for y in range(20) for z in range(40,56) if not (5<=x<15 and 5<=y<15)}
expm={(x,y,z) for x in range(7,13) for y in range(7,13) for z in range(0,66)}|{(x,y,z) for x in range(1,19) for y in range(1,19) for z in range(56,60)}
# World s offset at source z=40 is 80.4: test from actual transform, not JSON range.
s0=float((at-hinge)@axis);minf,maxf=local_f[:,2].min(),local_f[:,2].max()
shaft_r=math.sqrt(2)*.3;collar_r=math.sqrt(2)*.9
corn_local=corn@R
L=(bc-hinge)@R
ext=np.abs(R).sum(axis=0)*.5
lower=L-ext;upper=L+ext
du=np.maximum(np.maximum(lower[:,0],-upper[:,0]),0);dv=np.maximum(np.maximum(lower[:,1],-upper[:,1]),0)
def cylinder_candidates(smin,smax,r):
 return np.where((upper[:,2]>smin+1e-9)&(lower[:,2]<smax-1e-9)&(du*du+dv*dv<r*r-1e-9))[0]
shaft_candidates=cylinder_candidates(s0-4,s0+2.6,shaft_r)
collar_candidates=cylinder_candidates(s0+1.6,s0+2.0,collar_r)
contact_area=math.pi*(.9**2-(math.sqrt(2)*.5)**2)
# Existing rudder sweep: full interval certificate from sampled poses enlarged by max corner displacement.
sub=bc[(bc[:,0]>80)&(bc[:,0]<180)&(bc[:,1]>70)&(bc[:,1]<171)&(bc[:,2]<100)]
radial=rv-hinge;radial-=np.outer(radial@axis,axis);maxradius=np.linalg.norm(radial,axis=1).max()
step=.25;epsilon=2*maxradius*math.sin(math.radians(step)/4)
K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
sweep_bad=[];refine=[];exact_hits=[];calls=0;sweep_lo=np.ones(3)*np.inf;sweep_hi=np.ones(3)*-np.inf
def certify_segment(left,right,depth=0):
 global calls,sweep_lo,sweep_hi
 calls+=1;deg=(left+right)/2;eps=2*maxradius*math.sin(math.radians(right-left)/4)
 th=np.radians(deg);Q=np.eye(3)+np.sin(th)*K+(1-np.cos(th))*(K@K)
 centers=(rc-hinge)@Q.T+hinge
 extworld=np.abs(Q).sum(axis=1)*.5+eps
 sweep_lo=np.minimum(sweep_lo,centers.min(0)-extworld);sweep_hi=np.maximum(sweep_hi,centers.max(0)+extworld)
 hit=overlap_pairs(centers,Q,np.ones(3)*.5,sub,eps)
 if len(hit):
  exact=overlap_pairs(centers,Q,np.ones(3)*.5,sub,0)
  if len(exact):exact_hits.append({'degrees':deg,'pairs':[[rp[i].tolist(),(sub[k]-.5).tolist()] for i,k in exact]});return
  if depth<10:
   refine.append({'left':left,'right':right,'depth':depth,'candidates':len(hit)})
   certify_segment(left,deg,depth+1);certify_segment(deg,right,depth+1)
  else:sweep_bad.append({'interval':[left,right],'possible_pairs':len(hit)})
for i in range(240):certify_segment(-30+i*.25,-30+(i+1)*.25)
for deg in (-30,30):
 th=np.radians(deg);Q=np.eye(3)+np.sin(th)*K+(1-np.cos(th))*(K@K);cen=(rc-hinge)@Q.T+hinge
 hit=overlap_pairs(cen,Q,np.ones(3)*.5,sub,0)
 if len(hit):exact_hits.append({'degrees':deg,'pairs':[[rp[i].tolist(),(sub[k]-.5).tolist()] for i,k in hit]})
# Negative: restore the proposed holes -> the same conservative moving-cylinder test must flag >0.
cutcent=np.array(list(cut),float)+.5;CL=(cutcent-hinge)@R;cl=CL-ext;cu=CL+ext
ud=np.maximum(np.maximum(cl[:,0],-cu[:,0]),0);vd=np.maximum(np.maximum(cl[:,1],-cu[:,1]),0)
restored=int(np.count_nonzero((cu[:,2]>s0-4)&(cl[:,2]<s0+2.6)&(ud*ud+vd*vd<shaft_r**2)))
result={'proposal_sha256':hashlib.sha256((P/'proposal.json').read_bytes()).hexdigest(),'status':'proposal verified only; no actual work mutated','fixed_source_count':len(fixed),'moving_source_count':len(moving),'source_components':[components(fixed),components(moving)],'fixed_grid_contract_symmetric_diff':len(set(fixed)^expf),'moving_grid_contract_symmetric_diff':len(set(moving)^expm),'transformed_axis_error':float(np.linalg.norm(R[:,2]-axis)),'axis_center_perpendicular_error':float(np.linalg.norm((at-hinge)-axis*s0)),'s_at_source_z40':s0,'fixed_s_range_actual':[float(minf),float(maxf)],'moving_s_range_actual':[float(local_m[:,2].min()),float(local_m[:,2].max())],'fixed_static_embed_voxels':fixed_embed,'fixed_embed_voxel_count':len(fixed_embed),'moving_static_neutral_collision_pairs':len(moving_hits),'moving_original_rudder_overlap_pairs':len(root_hits),'moving_root_original_rudder_cells':sorted({tuple(map(int,rp[k])) for _,k in root_hits}),'original_rudder_count':len(rudder),'original_rudder_max_axial_s':smax,'original_fixed_full360_axial_gap':float(minf-smax),'shaft_full360_radius':shaft_r,'shaft_hole_full360_clearance':.5-shaft_r,'shoulder_bottom_s':s0+1.6,'fixed_upper_surface_s':maxf,'contact_normal_vertical_component':float(axis[2]),'guaranteed_contact_area_voxel2_full360':contact_area,'guaranteed_contact_area_m2_full360':contact_area*.01,'retained_body_vs_full360_shaft_cylinder_candidates':len(shaft_candidates),'retained_body_vs_full360_collar_cylinder_candidates':len(collar_candidates),'carve_count':len(cut),'carve_guard_bad':guard_bad,'carve_min_z':min(q[2] for q in cut),'new_parts_min_world_z':float(min(fv[:,2].min(),mv[:,2].min())),'underwater_changed_cells':sum(q[2]<52 for q in cut),'original_rudder_continuous_sweep':{'poses':241,'domain_degrees':[-30,30],'interval_step_degrees':step,'max_corner_radius':float(maxradius),'corner_motion_half_interval_bound':float(epsilon),'expanded_SAT_possible_collisions':sweep_bad},'negative_restored_cut_shaft_cylinder_candidates':restored,'limits':'Contact is analytic ideal rigid geometry and axial gravity load path, not finite element strength/material stress. Fixed embeds are declared joints. Full360 certificate for NEW moving shaft/shoulder; existing rudder certified ±30 with conservative interval enlargement. No runtime animation behavior certified.'}
result['original_rudder_continuous_sweep'].update(method='240 interval midpoints plus adaptive bisection, exact endpoint SAT; expansion bounded by maximum source-corner displacement to nearest interval midpoint',interval_calls=calls,refinements=refine,exact_collisions=exact_hits,unresolved_intervals=sweep_bad)
result['proposal_sha256']=hashlib.sha256(proposal_bytes).hexdigest()
result['original_rudder_continuous_sweep']['poses']=244+2
result['original_rudder_continuous_sweep']['conservative_swept_bbox']=[sweep_lo.tolist(),sweep_hi.tolist()]
result['original_rudder_continuous_sweep']['static_region_filter_proven_sufficient']=bool(sweep_lo[0]>80.5 and sweep_hi[0]<179.5 and sweep_lo[1]>70.5 and sweep_hi[1]<170.5 and sweep_hi[2]<99.5)
bearing_lo=np.minimum(fv.min(0),mv.min(0));bearing_hi=np.maximum(fv.max(0),mv.max(0))
parts=load(O.parent/'shared/parts.json');other=[]
for model in parts['models']:
 if model.get('meta',{}).get('kind')=='rudder':continue
 box=model.get('box')
 if box and np.all(np.array(box[:3])<bearing_hi) and np.all(np.array(box[3:])>bearing_lo):other.append(model['path'])
result['other_model_parts_bbox_candidates']=other
result['negative_remove_shoulders']={'mutant_source_cells':sum(7<=x<13 and 7<=y<13 for x,y,z in moving),'support_contact_area':0,'reason':'remaining 0.6x0.6 shaft is fully inside 1x1 fixed hole, no shoulder rests on top face'}
result['limits']=result['limits'].replace('existing rudder certified ±30 with conservative interval enlargement','existing rudder status depends on exact_collisions and unresolved_intervals; proof uses conservative interval enlargement')
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
