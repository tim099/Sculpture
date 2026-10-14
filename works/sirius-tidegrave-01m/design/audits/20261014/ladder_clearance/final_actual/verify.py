"""Actual post-CLI verification from immutable VXK snapshots. No asset writes."""
import pathlib,json,hashlib,math,sys,ast
import numpy as np
from scipy.ndimage import label,binary_fill_holes,binary_propagation,generate_binary_structure
OUT=pathlib.Path(__file__).parent;P=OUT.parent;ROOT=pathlib.Path('D:/Unity/Valhalla')
sys.path.insert(0,str(ROOT/'ArtGallery/VoxelKit'));from voxel_export import unpack
source=ROOT/'Sculpture/works/sirius-tidegrave-01m-assembly/exports/tidegrave_preview.vxk';oldblob=(P/'source_snapshot.vxk').read_bytes()
expected='a5994eeeacbb1155776145e3ebc2e69bd743815b7574df45ca6eb58653bdaf73'
snap=OUT/'actual_snapshot.vxk'
if not snap.exists():
 b=source.read_bytes()
 if hashlib.sha256(b).hexdigest()!=expected:raise RuntimeError('Unexpected new preview SHA; do not certify a different source')
 snap.write_bytes(b)
newblob=snap.read_bytes();oldh,oldv=unpack(oldblob);h,vox=unpack(newblob);old={tuple(q[:3]):int(q[3]) for q in oldv};base={tuple(q[:3]):int(q[3]) for q in vox};cells=vox[:,:3]
removed=old.keys()-base.keys();added=base.keys()-old.keys();changed={q for q in old.keys()&base.keys() if old[q]!=base[q]};guard={};guardfiles={}
for f in sorted((P/'design18').glob('*.color_guard.vox.txt')):
 b=f.read_bytes();guardfiles[str(f)]={'sha256':hashlib.sha256(b).hexdigest(),'count':0}
 for line in b.decode().splitlines():
  if not line.strip():continue
  x,y,z,c=map(int,line.split());guard[(x,y,z)]=c;guardfiles[str(f)]['count']+=1
# Compile only the exact design corridor ruler, no full author/verifier execution.
code=(P/'design21.py').read_text(encoding='utf8');node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='sweep');ns={'np':np,'cells':cells,'HEIGHT':18};exec(compile(ast.Module(body=[node],type_ignores=[]),'design.sweep','exec'),ns);sweep=ns['sweep']
parts=[q for q in h['parts'] if q.get('meta',{}).get('kind') in ['ladder','ladders']];routes=[];endpoints=[]
for p in parts:
 by={}
 for key,q in p['points'].items():
  name,role=key.rsplit('.',1);by.setdefault(name,{})[role]=[q[0],q[1],math.floor(q[2])]
 for name,b in sorted(by.items()):
  path=np.array([b[k] for k in ['foot','lo','hi','head']],float);path[1:3,2]+=3;hits=[]
  for i in range(3):
   hit=sweep(path[i],path[i+1]);hits.append({'segment':['foot->lo','lo->hi','hi->head'][i],'obstacle_count':len(hit),'examples':[[int(v) for v in q] for q in hit[:5]]})
  routes.append({'name':name,'path':path.tolist(),'segments':hits,'total_obstacle_segments':sum(q['obstacle_count'] for q in hits)})
  for role,pnt in [('foot',path[0]),('head',path[-1])]:
   x,y,z=map(int,np.floor(pnt));endpoints.append({'name':name+'.'+role,'at':pnt.tolist(),'floor_present':(x,y,z-1) in base,'headroom14_blockers':[(x,y,zz) for zz in range(z,z+14) if (x,y,zz) in base]})
floorcoords={tuple(map(int,[q['at'][0],q['at'][1],q['at'][2]-1])) for q in endpoints}
# Exact foot point sweep from same audit function; not the tall corridor extrusion.
acode=(P/'audit.py').read_text(encoding='utf8');anode=next(n for n in ast.parse(acode).body if isinstance(n,ast.FunctionDef) and n.name=='intersections');ans={'np':np,'cells':cells,'colors':base};exec(compile(ast.Module(body=[anode],type_ignores=[]),'audit.intersections','exec'),ans)
for route in routes:
 path=np.array(route['path']);route['foot_inside_counts']=[len(ans['intersections'](path[i],path[i+1],0,0,0)) for i in range(3)]
arr=cells.astype(np.int16);lo=arr.min(axis=0)-1;hi=arr.max(axis=0)+1;a=np.zeros(tuple(map(int,hi-lo+1)),bool);a[tuple((arr-lo).T)]=True;lab,n=label(a,structure=generate_binary_structure(3,1));counts=np.bincount(lab.ravel());del lab;filled=binary_fill_holes(a);holes=int(np.sum(filled&~a));del a,filled
water={}
for name,V in [('old_snapshot',oldv),('actual_snapshot',vox)]:
 air=np.ones((800,241,52),bool);q=V[V[:,2]<52,:3];air[tuple(q.T)]=False;seeds=np.zeros_like(air);seeds[0]=air[0];seeds[-1]=air[-1];seeds[:,0]=air[:,0];seeds[:,-1]=air[:,-1];seeds[:,:,0]=air[:,:,0];flood=binary_propagation(seeds,mask=air)
 water[name]={'enclosed_air_voxels':int(np.sum(air&~flood)),'probe350_120_40_water':bool(flood[350,120,40]),'probe170_120_40_water':bool(flood[170,120,40])}
restored=sorted(removed)[0];ns['cells']=np.array([restored]);reverse=[]
for route in routes:
 path=np.array(route['path'])
 for i in range(3):
  hit=sweep(path[i],path[i+1])
  if hit:reverse.append({'ladder':route['name'],'segment':['foot->lo','lo->hi','hi->head'][i],'restored_voxel':[int(q) for q in restored],'color':old[restored],'collision_count':len(hit)})
original_events=json.load(open(P/'candidates.json',encoding='utf8'))['source_event_hashes'];ladder_event_guards={name:hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()==sha for name,sha in original_events.items() if '/sirius-tidegrave-01m-ladders/' in name.replace('\\','/')}
report={'old_sha256':hashlib.sha256(oldblob).hexdigest(),'actual_sha256':hashlib.sha256(newblob).hexdigest(),'expected_actual_sha256':expected,'actual_hash_match':hashlib.sha256(newblob).hexdigest()==expected,'guard_files':guardfiles,'delta':{'old_voxels':len(oldv),'actual_voxels':len(vox),'removed':len(removed),'added':len(added),'color_changed':len(changed),'removed_minZ':int(min(q[2] for q in removed)),'removed_maxZ':int(max(q[2] for q in removed)),'exact_guard_match':removed==guard.keys(),'removed_color_guard_match':all(old.get(q)==c for q,c in guard.items()),'below_waterline_removed':sum(q[2]<52 for q in removed)},'design_scope':{'lift':3,'height':18,'y_range':[117,123],'width':7,'source_rule':'Continuous linear swept strip, longitudinal radius0. Does not assert current game CLIMB_LIFT is already3.'},'routes':routes,'endpoints':endpoints,'ladder_source_events_unchanged':ladder_event_guards,'all_ladder_source_events_unchanged':bool(ladder_event_guards) and all(ladder_event_guards.values()),'protected_landing_floor_removed':[[int(v) for v in q] for q in removed&floorcoords],'structure':{'voxels':len(vox),'components6':int(n),'component_sizes':sorted(counts[1:].tolist(),reverse=True),'enclosed_empty_voxels':holes,'mirror_y120_missing':sum((x,240-y,z) not in base for x,y,z in base),'mirror_y120_color_diff':sum(base.get((x,240-y,z))!=c for (x,y,z),c in base.items() if (x,240-y,z) in base)},'water':water,'reverse_control':{'restored_voxel':[int(v) for v in restored],'hits':reverse,'passed':bool(reverse),'memory_only':True},'limitations':['Only fixed four-anchor strip and VXK static voxel layer.','navSnap approach/departure legs, model/rig geometry, pose/sprite alpha excluded.','Exact path geometry is for proposed lift3; current game constant remains independently reported.'],'assets_modified':False}
report['passed']=report['actual_hash_match'] and report['delta']['exact_guard_match'] and not added and not changed and report['delta']['removed_color_guard_match'] and all(not q['total_obstacle_segments'] and not any(q['foot_inside_counts']) for q in routes) and all(q['floor_present'] and not q['headroom14_blockers'] for q in endpoints) and report['all_ladder_source_events_unchanged'] and not report['protected_landing_floor_removed'] and n==1 and holes==0 and report['structure']['mirror_y120_missing']==0 and report['structure']['mirror_y120_color_diff']==0 and water['old_snapshot']==water['actual_snapshot'] and bool(reverse)
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda o:o.item()),encoding='utf8')
print(json.dumps({k:report[k] for k in ['actual_sha256','delta','structure','water','reverse_control','passed']},ensure_ascii=False,indent=2,default=lambda o:o.item()))
