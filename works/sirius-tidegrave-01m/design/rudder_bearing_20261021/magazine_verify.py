"""Narrow TASK-0549 magazine verification. No project/checker imports or asset writes."""
from pathlib import Path
from collections import deque,defaultdict
import json,hashlib,math,struct,zlib
import numpy as np
O=Path(__file__).parent;R=Path('D:/Unity/Valhalla/Sculpture/works');B='sirius-tidegrave-01m';S=O.parent/'shared';hashes={}
def load(p):
 b=p.read_bytes();hashes[str(p)]=hashlib.sha256(b).hexdigest();return json.loads(b)
def replay(w):
 a={}
 for f in sorted((R/w/'events').rglob('*.json')):
  e=load(f)
  for q in e.get('carved_voxels',[]):a.pop(tuple(q[:3]),None)
  for q in e.get('placed_colored',[]):a[tuple(q[:3])]=q[3]
  for q in e.get('placed_voxels',[]):a[tuple(q[:3])]=e['color']
 return a
shell=replay(B);parts=load(S/'parts.json');plan=load(R/B/'design/plan.json')
blob=(S/'current.vxk').read_bytes();hashes[str(S/'current.vxk')]=hashlib.sha256(blob).hexdigest();raw=zlib.decompress(blob,-15);assert raw[:4]==b'VXK1';n=struct.unpack_from('<I',raw,4)[0];h=json.loads(raw[8:8+n]);p=8+n;N=h['nchunks'];org=np.frombuffer(raw,'<u2',N*3,p).reshape(N,3);p+=6*N;world={}
for i,c in enumerate(org):
 for j,color in enumerate(raw[p+i*4096:p+(i+1)*4096]):
  if color:world[(int(c[0])*16+j%16,int(c[1])*16+j//16%16,int(c[2])*16+j//256)]=color
# Conservative side span bounds from actual shell events at each X/Z, no width formula.
ys=defaultdict(list)
for x,y,z in shell:ys[(x,z)].append(y)
reports=[]
for pos,x0 in [('aft',240),('fore',440)]:
 work=B+'-magazine-'+pos;a=replay(work);link=next(q for q in parts['links'] if q['work']==work);anchors=load(R/work/'anchors.json');models=load(R/work/'models.json')['models']
 expected={}
 for x in range(45):
  for y in range(41):
   for z in range(24):
    color=145 if z<2 or z==23 else 0
    if x<2 or x>=43 or y<2 or y>=39:color=168
    if x>=43 and 17<=y<=23 and 2<=z<=22:color=0
    if color:expected[(x,y,z)]=color
 allvolume=[(x+x0,y+100,z+30) for x in range(45) for y in range(41) for z in range(24)]
 outside=[];clearance=[]
 for x,y,z in allvolume:
  row=ys[(x,z)]
  if not row or not min(row)<y<max(row):outside.append((x,y,z))
  elif (x,y,z) in shell:outside.append((x,y,z))
  else:clearance.append(min(y-min(row),max(row)-y))
 # Exact bounds containment proves every barrel point is inside the inner room.
 bars=[m for m in parts['models'] if m.get('frame')==link['path'] and m.get('meta',{}).get('kind')=='powder'];bar_report=[]
 for m in bars:
  lo=m['box'][:3];hi=m['box'][3:];innerlo=[x0+2,102,32];innerhi=[x0+43,139,53]
  bar_report.append({'name':m['name'],'box':m['box'],'powder_lb':m['meta'].get('powder_lb'),'inside_room_inner_volume':all(lo[i]>=innerlo[i] and hi[i]<=innerhi[i] for i in range(3)),'state':m['state']})
 opening=[(x,y,z) for x in [43,44] for y in range(17,24) for z in range(2,23)]
 blocked=[q for q in opening if q in a];assemblyblocked=[q for q in opening if (q[0]+x0,q[1]+100,q[2]+30) in world]
 frame=[(x,y,z) for x in [43,44] for y in [16,24] for z in range(2,23)]+[(x,y,z) for x in [43,44] for y in range(17,24) for z in [1,23]]
 # Flood local void from door, retaining roof/walls/floor. This is not hull water testing.
 seed=(44,20,10);seen={seed};todo=deque([seed])
 while todo:
  q=todo.popleft()
  for axis in range(3):
   for d in [-1,1]:
    r=list(q);r[axis]+=d;r=tuple(r)
    if 0<=r[0]<45 and 0<=r[1]<41 and 0<=r[2]<24 and r not in a and r not in seen:seen.add(r);todo.append(r)
 negative=a.copy();negative[(44,20,22)]=168
 rows={'pos':pos,'work':work,'result_ledger':{'expected':len(expected),'actual':len(a),'missing':len(expected.keys()-a.keys()),'extra':len(a.keys()-expected.keys()),'color':sum(a[q]!=expected[q] for q in a.keys()&expected.keys())},'room_outer_box_continuous':[x0,100,30,x0+45,141,54],'tested_room_volume_voxels':len(allvolume),'room_volume_outside_or_intersecting_shell':len(outside),'minimum_side_shell_bound_clearance_cells':min(clearance),'assembly_missing':sum((x+x0,y+100,z+30) not in world for x,y,z in a),'assembly_color_diff':sum(world.get((x+x0,y+100,z+30))!=c for (x,y,z),c in a.items()),'door':{'width':7,'height':21,'wall_thickness':2,'world_x':[x0+43,x0+44],'world_y':[117,123],'world_z':[32,52],'tested_opening_voxels':len(opening),'source_blockers':len(blocked),'assembly_blockers':len(assemblyblocked),'frame_voxels':len(frame),'frame_missing':sum(q not in a for q in frame),'interior_probe_reachable_from_door':(22,20,10) in seen,'void_reachable_cells':len(seen)},'parts_meta':link['meta'],'parts_points':link['points'],'source_anchors':anchors['anchors'],'barrels':bar_report,'powder_total_lb':sum(m['meta'].get('powder_lb',0) for m in bars),'negative_control':{'memory_only_fill_one_top_door_voxel':[44,20,22],'same_opening_test_blockers':sum(q in negative for q in opening)}}
 reports.append(rows)
out={'scope':'TASK-0549 first criterion: independent room enclosure, door height/frame, barrel inner-room containment and metadata. No whole-hull water or game test.','input_sha256':hashes,'magazines':reports,'assets_modified':False}
(O/'magazine_report.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps([{k:v for k,v in r.items() if k not in ['barrels','source_anchors']} for r in reports],ensure_ascii=False,indent=2))
