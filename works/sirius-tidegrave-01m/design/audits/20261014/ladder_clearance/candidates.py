import ast,pathlib,json,hashlib,math,sys,collections
import numpy as np
OUT=pathlib.Path(__file__).parent;ROOT=pathlib.Path('D:/Unity/Valhalla');WORKS=ROOT/'Sculpture/works'
sys.path.insert(0,str(ROOT/'ArtGallery/VoxelKit'));from voxel_export import unpack
blob=(OUT/'source_snapshot.vxk').read_bytes();header,vox=unpack(blob)
# Same exact continuous interval ruler; restrict immutable voxel input to a conservative corridor.
cells=vox[:,:3];colors={tuple(q[:3]):int(q[3]) for q in vox};corr=cells[(cells[:,1]==120)&(cells[:,0]>=150)&(cells[:,0]<=580)&(cells[:,2]>=60)&(cells[:,2]<=190)]
code=(OUT/'audit.py').read_text(encoding='utf8');node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='intersections');ns={'np':np,'cells':corr,'colors':colors};exec(compile(ast.Module(body=[node],type_ignores=[]),'audit.intersections','exec'),ns);intersections=ns['intersections']
ladders={}
for p in header['parts']:
 if p.get('meta',{}).get('kind') not in ['ladder','ladders']:continue
 for key,q in p['points'].items():
  name,role=key.rsplit('.',1);ladders.setdefault(name,{})[role]=[q[0],q[1],math.floor(q[2])]
results={};alltargets=set()
for lift in [2,3,4,5]:
 rows=[]
 for name,anchors in sorted(ladders.items()):
  names=['foot','lo','hi','head'];path=np.array([anchors[k] for k in names],float);path[1:3,2]+=lift;legs=[];feet=set();body=set();fullbody=set()
  for i in range(3):
   f=intersections(path[i],path[i+1],0,0,0);b=intersections(path[i],path[i+1],14,0,2);full=intersections(path[i],path[i+1],14,0,.001);fv={tuple(q['voxel']) for q in f};bv={tuple(q['voxel']) for q in b};uv={tuple(q['voxel']) for q in full};feet|=fv;body|=bv;fullbody|=uv
   legs.append({'segment':names[i]+'->'+names[i+1],'foot_inside_count':len(fv),'foot_inside_voxels':sorted(fv),'body_above2_to14_count':len(bv),'body_above2_to14_voxels':sorted(bv),'full14_count':len(uv),'full14_voxels':sorted(uv),'body_examples':b[:5]})
  rows.append({'name':name,'path':path.tolist(),'foot_inside_unique':len(feet),'body_unique':len(body),'full14_unique':len(fullbody),'segments':legs});alltargets|=feet|body|fullbody
 results[str(lift)]=rows
links=json.load(open(WORKS/'sirius-tidegrave-01m-assembly/links.json',encoding='utf8'))['links'];ownership=collections.defaultdict(list);sourcehash={}
for l in links:
 v={}
 for f in sorted((WORKS/l['work']/'events').rglob('*.json')):
  b=f.read_bytes();e=json.loads(b);sourcehash[str(f)]=hashlib.sha256(b).hexdigest()
  for q in e.get('carved_voxels',[]):v.pop(tuple(q[:3]),None)
  for q in e.get('placed_voxels',[]):v[tuple(q[:3])]=e.get('color')
  for q in e.get('placed_colored',[]):v[tuple(q[:3])]=q[3]
 for a in alltargets:
  local=tuple(a[k]-l['at'][k] for k in range(3))
  if local in v:ownership[a].append({'work':l['work'],'local':local,'color':v[local],'snapshot_color_match':v[local]==colors[a],'protected_ladder_source':l['work'].endswith('-ladders')})
for lift,rows in results.items():
 out=OUT/('lift'+lift);out.mkdir(exist_ok=True);aggregate=collections.defaultdict(dict);protected=set();fullaggregate=collections.defaultdict(dict);fullprotected=set()
 for row in rows:
  for segment in row['segments']:
   for q in segment['full14_voxels']:
    a=tuple(q);own=ownership.get(a,[])
    if any(o['protected_ladder_source'] for o in own):fullprotected.add(a);continue
    for o in own:fullaggregate[o['work']][tuple(o['local'])]=o['color']
   owned=[]
   for a in map(tuple,segment['body_above2_to14_voxels']):
    item={'assembly':a,'owners':ownership.get(a,[]),'protected':any(o['protected_ladder_source'] for o in ownership.get(a,[]))};owned.append(item)
    if item['protected']:protected.add(a)
    for owner in item['owners']:
     if not item['protected']:aggregate[owner['work']][tuple(owner['local'])]=owner['color']
   segment['body_voxel_owners']=owned
  row['protected_body_voxel_count']=len({tuple(q) for s in row['segments'] for q in s['body_above2_to14_voxels'] if any(o['protected_ladder_source'] for o in ownership.get(tuple(q),[]))})
 for name,m in aggregate.items():
  (out/(name+'.body_remove.vox.txt')).write_text('\n'.join(' '.join(map(str,q)) for q in sorted(m))+'\n',encoding='utf8')
  (out/(name+'.body_color_guard.vox.txt')).write_text('\n'.join(' '.join(map(str,list(q)+[m[q]])) for q in sorted(m))+'\n',encoding='utf8')
 for name,m in fullaggregate.items():
  (out/(name+'.full14_remove.vox.txt')).write_text('\n'.join(' '.join(map(str,q)) for q in sorted(m))+'\n',encoding='utf8')
  (out/(name+'.full14_color_guard.vox.txt')).write_text('\n'.join(' '.join(map(str,list(q)+[m[q]])) for q in sorted(m))+'\n',encoding='utf8')
 groups={name:{'count':len(m),'colors':dict(collections.Counter(m.values()))} for name,m in aggregate.items()};fullgroups={name:{'count':len(m),'colors':dict(collections.Counter(m.values()))} for name,m in fullaggregate.items()};results[lift]={'ladders':rows,'non_ladder_body_carve_groups':groups,'non_ladder_full14_carve_groups':fullgroups,'protected_ladder_full14_voxels':sorted(fullprotected),'protected_ladder_body_voxels':sorted(protected),'all_foot_inside_unique':len({tuple(v) for r in rows for s in r['segments'] for v in s['foot_inside_voxels']}),'all_body_unique':len({tuple(v) for r in rows for s in r['segments'] for v in s['body_above2_to14_voxels']})}
report={'source_sha256':hashlib.sha256(blob).hexdigest(),'ruler_function_sha256':hashlib.sha256(ast.get_source_segment(code,node).encode()).hexdigest(),'source_event_hashes':sourcehash,'body_rule':'foot+2..foot+14 center column; foot penetration separately; protected ladder source is never included in proposed carve files','voxel_owners':{','.join(map(str,q)):o for q,o in ownership.items()},'owner_mismatch':{str(q):o for q,o in ownership.items() if any(not p['snapshot_color_match'] for p in o)},'unowned':list(alltargets-ownership.keys()),'lifts':results}
(OUT/'candidates.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:{'foot':v['all_foot_inside_unique'],'body':v['all_body_unique'],'protected':len(v['protected_ladder_body_voxels']),'groups':v['non_ladder_body_carve_groups'],'by_ladder':[(r['name'],r['foot_inside_unique'],r['body_unique']) for r in v['ladders']]} for k,v in results.items()},ensure_ascii=False,indent=2))
