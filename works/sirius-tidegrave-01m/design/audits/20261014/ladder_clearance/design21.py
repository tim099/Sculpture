"""Hypothetical construction package only: lift3, upright21, transverse7. Never modifies works."""
import pathlib,json,hashlib,math,sys,collections
import numpy as np
from scipy.ndimage import label,binary_fill_holes,generate_binary_structure
HEIGHT=int(sys.argv[1]) if len(sys.argv)>1 else 21
OUT=pathlib.Path(__file__).parent/('design'+str(HEIGHT));OUT.mkdir(exist_ok=True)
ROOT=pathlib.Path('D:/Unity/Valhalla');WORKS=ROOT/'Sculpture/works'
sys.path.insert(0,str(ROOT/'ArtGallery/VoxelKit'));from voxel_export import unpack
blob=(OUT.parent/'source_snapshot.vxk').read_bytes();h,vox=unpack(blob);cells=vox[:,:3];base={tuple(q[:3]):int(q[3]) for q in vox};rows=json.load(open(OUT.parent/'candidates.json',encoding='utf8'))['lifts']['3']['ladders']
protected_floors={tuple(map(int,[p[0],p[1],p[2]-1])) for row in rows for p in [row['path'][0],row['path'][-1]]}
def sweep(a,b):
 low=np.minimum(a,b)+[0,-3.5,.001];high=np.maximum(a,b)+[0,3.5,HEIGHT]
 q=cells[np.all(cells+1>low+1e-10,axis=1)&np.all(cells<high-1e-10,axis=1)]
 if not len(q):return []
 L=q-np.array([0,3.5,HEIGHT]);U=q+1+np.array([0,3.5,-.001]);d=b-a;t0=np.zeros(len(q));t1=np.ones(len(q));ok=np.ones(len(q),bool)
 for k in range(3):
  if abs(d[k])<1e-12:ok&=(a[k]>L[:,k]+1e-10)&(a[k]<U[:,k]-1e-10)
  else:
   p=(L[:,k]-a[k])/d[k];s=(U[:,k]-a[k])/d[k];t0=np.maximum(t0,np.minimum(p,s));t1=np.minimum(t1,np.maximum(p,s))
 ok&=t1-t0>1e-9
 return [tuple(q[i]) for i in np.flatnonzero(ok)]
allhits=set();per=[];names=['foot','lo','hi','head']
for row in rows:
 path=np.array(row['path']);segments=[]
 for i in range(3):
  hit=sweep(path[i],path[i+1]);allhits.update(hit);segments.append({'segment':names[i]+'->'+names[i+1],'count':len(hit),'voxels':[[int(q) for q in p] for p in sorted(hit)]})
 per.append({'name':row['name'],'path':row['path'],'segments':segments})
links=json.load(open(WORKS/'sirius-tidegrave-01m-assembly/links.json',encoding='utf8'))['links'];owners=collections.defaultdict(list);sources={}
for l in links:
 v={}
 for f in sorted((WORKS/l['work']/'events').rglob('*.json')):
  e=json.load(open(f))
  for q in e.get('carved_voxels',[]):v.pop(tuple(q[:3]),None)
  for q in e.get('placed_voxels',[]):v[tuple(q[:3])]=e.get('color')
  for q in e.get('placed_colored',[]):v[tuple(q[:3])]=q[3]
 sources[l['work']]=v
 for a in allhits:
  local=tuple(int(a[k]-l['at'][k]) for k in range(3))
  if local in v:owners[a].append({'work':l['work'],'local':local,'color':v[local],'protected_ladder':l['work'].endswith('-ladders')})
blocked={a for a in allhits if a in protected_floors or any(o['protected_ladder'] for o in owners[a])};remove=allhits-blocked;groups=collections.defaultdict(dict)
for a in remove:
 for o in owners[a]:groups[o['work']][tuple(o['local'])]=o['color']
for name,m in groups.items():
 (OUT/(name+'.remove.vox.txt')).write_text('\n'.join(' '.join(map(str,q)) for q in sorted(m))+'\n',encoding='utf8')
 (OUT/(name+'.color_guard.vox.txt')).write_text('\n'.join(' '.join(map(str,list(q)+[m[q]])) for q in sorted(m))+'\n',encoding='utf8')
after={q:c for q,c in base.items() if q not in remove};arr=np.array(list(after),np.int16);lo=arr.min(axis=0)-1;hi=arr.max(axis=0)+1;grid=np.zeros(tuple(map(int,hi-lo+1)),bool);grid[tuple((arr-lo).T)]=1;lab,n=label(grid,structure=generate_binary_structure(3,1));counts=np.bincount(lab.ravel());del lab;filled=binary_fill_holes(grid);holes=int(np.sum(filled&~grid));del filled,grid
mirrormiss=sum((x,240-y,z) not in after for x,y,z in after);mirrordiff=sum(after.get((x,240-y,z))!=c for (x,y,z),c in after.items() if (x,240-y,z) in after)
bodyowners={','.join(map(str,a)):owners[a] for a in sorted(allhits)}
report={'source_sha256':hashlib.sha256(blob).hexdigest(),'design':{'lift':3,'upright_height':HEIGHT,'transverse_y_voxels':[117,123],'transverse_width':7,'foot_y':120.5,'longitudinal_radius':0,'bottom_epsilon':.001,'note':'Explicit ship design corridor, not a claimed game collider. Exact continuous linear-segment extrusion; endpoint-only and frame sampling are not used for obstacle mask.'},'all_swept_obstacle_count':len(allhits),'proposed_remove_count':len(remove),'protected_conflict_count':len(blocked),'protected_conflicts':[[int(q) for q in p] for p in sorted(blocked)],'protected_floor_cells':[list(q) for q in sorted(protected_floors)],'source_groups':{name:{'count':len(m),'colors':dict(collections.Counter(m.values()))} for name,m in groups.items()},'unowned':[[int(q) for q in p] for p in allhits-owners.keys()],'color_mismatches':[[int(q) for q in p] for p,o in owners.items() if any(x['color']!=base[p] for x in o)],'per_ladder':per,'voxel_owners':bodyowners,'hypothetical_structure':{'voxel_count':len(after),'components6':int(n),'component_sizes':sorted(counts[1:].tolist(),reverse=True),'enclosed_empty_voxels':holes,'mirror_y120_missing':mirrormiss,'mirror_y120_color_diff':mirrordiff,'all14_landing_floor_present':all(q in after for q in protected_floors)},'can_claim_design_corridor_clear':not blocked,'limits':['Does not certify a full human capsule, opaque sprite or pose envelope.','Approach/departure navSnap paths excluded.','Ropes/sails/import model geometry excluded.','Only hypothetical assembly connectivity, cavity, mirror and landing-floor support checks; not structural load certification.']}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:report[k] for k in ['all_swept_obstacle_count','proposed_remove_count','protected_conflict_count','source_groups','hypothetical_structure','can_claim_design_corridor_clear']},ensure_ascii=False,indent=2))
