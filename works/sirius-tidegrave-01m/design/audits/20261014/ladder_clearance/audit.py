"""Read-only VXK ladder trajectory audit; exact linear swept-column tests plus foot samples."""
import sys,pathlib,json,hashlib,math
import numpy as np
ROOT=pathlib.Path('D:/Unity/Valhalla');OUT=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT/'ArtGallery/VoxelKit'))
from voxel_export import unpack
src=ROOT/'Sculpture/works/sirius-tidegrave-01m/design/delivery/tidegrave_candidate_20261014.vxk'
snapshot=OUT/'source_snapshot.vxk'
if not snapshot.exists():snapshot.write_bytes(src.read_bytes())
blob=snapshot.read_bytes();header,vox=unpack(blob);cells=vox[:,:3];solid=set(map(tuple,cells));colors={tuple(q[:3]):int(q[3]) for q in vox}
jsroot=ROOT/'ArtGallery/HtmlGames/_build/ame_constitution_broadside/js'
sources={str(snapshot):hashlib.sha256(blob).hexdigest()}
for name in ['40_crew.js','41_crew_art.js','42_hands.js']:
 p=jsroot/name;sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
result={'source_sha256':sources[str(snapshot)],'source_header_checksum':header['checksum'],'voxel_count':len(vox),'meters_per_voxel':header['meters_per_voxel'],'source_hashes':sources,'method':'Analytic continuous interval clipping of a linear foot segment extruded vertically (strict positive body/voxel overlap). No frame-step tunnelling. Foot-contact diagnostics sample at <=0.1 voxel arc length. Only fixed four-anchor trajectory, not navSnap approach/departure legs. Official VoxelKit unpack is a binary decoder, not an author checker.','actual_game_rules':{'NAV_HEAD_voxels':12,'spawn_head_voxels':14,'CLIMB_LIFT_voxels':2,'render_height_m':2.1,'render_billboard_width_m':1.05,'volumetric_body_collider':False,'climb_collision_blocking':False,'render_box_note':'21 voxel height and 10.5 voxel width include transparent padding and pose deformation; width is camera-facing, not a physical capsule.','render_pose_note':'Nominal upright dimensions only; animation lean, bob, sy and transparent alpha are not modelled.'},'ladders':[],'limits':['No gameplay physical blockage assertion: climb movement currently does not perform body collision checks.','No claim of opaque sprite pixel contact from full billboard envelope overlap.','Ropes, sails and model import volumes excluded; fixed VXK voxel layer only.','Full navSnap->foot and head->navSnap approach paths not included.']}
parts=[p for p in header['parts'] if p.get('meta',{}).get('kind') in ['ladder','ladders']]
def intersections(a,b,H,r,bottom):
 low=np.minimum(a,b)+[-r,-r,bottom];high=np.maximum(a,b)+[r,r,H]
 q=cells[np.all(cells+1>low+1e-10,axis=1)&np.all(cells<high-1e-10,axis=1)]
 # H=0 is a mathematical foot point, so the previous bbox z filter still has nonzero path extent.
 if not len(q):return []
 L=q-np.array([r,r,H]);U=q+1+np.array([r,r,-bottom]);d=b-a;t0=np.zeros(len(q));t1=np.ones(len(q));ok=np.ones(len(q),bool)
 for k in range(3):
  if abs(d[k])<1e-12:ok&=(a[k]>L[:,k]+1e-10)&(a[k]<U[:,k]-1e-10)
  else:
   p=(L[:,k]-a[k])/d[k];s=(U[:,k]-a[k])/d[k];t0=np.maximum(t0,np.minimum(p,s));t1=np.minimum(t1,np.maximum(p,s))
 ok&=(t1-t0)>1e-9
 hits=[]
 for k in np.flatnonzero(ok):
  t=float((t0[k]+t1[k])/2);p=a+t*d
  hits.append({'voxel':q[k].tolist(),'color':colors[tuple(q[k])],'t_enter':float(t0[k]),'t_exit':float(t1[k]),'evidence_t':t,'foot_at_evidence':p.tolist(),'obstacle_bottom_relative_to_foot':float(q[k,2]-p[2]),'obstacle_top_relative_to_foot':float(q[k,2]+1-p[2])})
 return sorted(hits,key=lambda h:h['t_enter'])
for part in parts:
 by={}
 for key,p in part['points'].items():
  name,role=key.rsplit('.',1);by.setdefault(name,{})[role]=[p[0],p[1],math.floor(p[2])]
 for name,anchors in sorted(by.items()):
  names=['foot','lo','hi','head'];original=np.array([anchors[k] for k in names],float);path=original.copy();path[1:3,2]+=2
  modes=[('foot_inside_solid',0,0,0),('nav12_center_column',12,0,.001),('nav12_body_above2',12,0,2),('spawn14_center_column',14,0,.001),('spawn14_body_above2',14,0,2),('nominal21_center_column',21,0,.001),('nominal21_visual_bbox',21,5.25,.001)]
  one={'name':name,'anchor_points':original.tolist(),'game_foot_path':path.tolist(),'continuous_tests':{},'endpoints':[]}
  for p in [path[0],path[-1]]:
   x,y,z=map(int,np.floor(p));one['endpoints'].append({'at':p.tolist(),'floor_present':(x,y,z-1) in solid,'headroom14_blockers':[(x,y,h) for h in range(z,z+14) if (x,y,h) in solid]})
  for label,H,r,bottom in modes:
   segments=[];allcells=set()
   for i in range(3):
    hits=intersections(path[i],path[i+1],H,r,bottom);allcells.update(tuple(h['voxel']) for h in hits)
    segments.append({'segment':names[i]+'->'+names[i+1],'blocking_voxels':len(hits),'examples':hits[:8]})
   one['continuous_tests'][label]={'unique_obstacle_voxels':len(allcells),'segments':segments,'all_obstacle_voxels':sorted(allcells)}
  samples=[];penetrations=[];gaps=[]
  for i in range(3):
   a,b=path[i],path[i+1];n=max(1,math.ceil(float(np.linalg.norm(b-a))/.1))
   for t in np.linspace(0,1,n+1):
    p=a+t*(b-a);x,y,z=map(int,np.floor(p));inside=bool((x,y,z) in solid and p[2]-z>1e-8)
    floor=None
    for zz in range(math.floor(p[2])-1,math.floor(p[2])-21,-1):
     if (x,y,zz) in solid and zz+1<=p[2]+1e-8:floor=zz+1;break
    gap=None if floor is None else float(p[2]-floor)
    row={'segment':names[i]+'->'+names[i+1],'t':float(t),'foot':p.tolist(),'inside_solid':inside,'support_surface_z':floor,'vertical_gap_voxels':gap}
    samples.append(row)
    if inside:penetrations.append(row)
    if gap is not None:gaps.append(gap)
  one['sampled_foot_contact']={'sample_step_max_voxels':.1,'sample_count':len(samples),'inside_solid_count':len(penetrations),'inside_examples':penetrations[:8],'vertical_gap_min_voxels':min(gaps) if gaps else None,'vertical_gap_max_voxels':max(gaps) if gaps else None,'no_support_within20_voxels':sum(q['vertical_gap_voxels'] is None for q in samples),'interpretation':'Ladder lift intentionally floats the mathematical foot above treads. Nonzero gap alone is not gameplay failure; positive inside-solid is direct geometric penetration.'}
  (OUT/(name+'.samples.json')).write_text(json.dumps(samples,ensure_ascii=False,indent=2),encoding='utf8')
  result['ladders'].append(one)
result['summary']=[{'name':q['name'],'endpoint14_pass':all(e['floor_present'] and not e['headroom14_blockers'] for e in q['endpoints']),**{k:v['unique_obstacle_voxels'] for k,v in q['continuous_tests'].items()},'foot_inside_sample_count':q['sampled_foot_contact']['inside_solid_count'],'max_foot_gap_voxels':q['sampled_foot_contact']['vertical_gap_max_voxels']} for q in result['ladders']]
(OUT/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'source_sha256':result['source_sha256'],'summary':result['summary']},ensure_ascii=False,indent=2))
