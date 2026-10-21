import json, pathlib, hashlib, math, itertools, collections
import numpy as np
ROOT=pathlib.Path('D:/Unity/Valhalla/Sculpture/works')
OUT=pathlib.Path(__file__).parent
IN=OUT.parent/'shared/parts.json'
inputs={}; replay_cache={}; replay_reports=[]
def read(p):
 b=p.read_bytes(); inputs[str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}; return json.loads(b.decode('utf-8-sig'))
def replay(w):
 if w in replay_cache:return replay_cache[w]
 d={}; fs=sorted((ROOT/w/'events').glob('*/*.json')); unknown=[]
 for p in fs:
  a=read(p)
  if a.get('op')=='workedit':
   for v in a['edit']['after']:
    k=(v['x'],v['y'],v['z'])
    if v['color']:d[k]=v['color']
    else:d.pop(k,None)
  elif 'placed_colored' in a:
   for v in a['placed_colored']:d[tuple(v[:3])]=v[3]
  elif 'placed_voxels' in a:
   for v in a['placed_voxels']:d[tuple(v[:3])]=a['color']
  elif 'carved_voxels' in a:
   for v in a['carved_voxels']:d.pop(tuple(v[:3]),None)
  else:unknown.append((p.name,a.get('op')))
 cache=read(ROOT/w/'sculpt_cache.json'); cv={tuple(map(int,k.split(','))):v for k,v in cache.get('voxels',{}).items()}
 replay_reports.append({'work':w,'events':len(fs),'voxels':len(d),'cache_missing':len(d.keys()-cv.keys()),'cache_extra':len(cv.keys()-d.keys()),'cache_color':sum(v!=cv[k] for k,v in d.items() if k in cv),'unknown':unknown})
 replay_cache[w]=d; return d
parts=read(IN); assembly=ROOT/'sirius-tidegrave-01m-assembly'
links=read(assembly/'links.json')['links']; raw=[]; static=set(); linksets={}
for l in links:
 assert l['turn']==0 and not l.get('mirror')
 off=np.array(l['at']); s={tuple(np.array(v)+off) for v in replay(l['work'])}; static.update(s);linksets[l['name']]=s
 p=ROOT/l['work']/'models.json'
 if p.exists():
  for m in read(p)['models']:
   if m.get('enabled',True):raw.append((l['name']+'/'+m['name'],m,off))
for m in read(assembly/'models.json')['models']:
 if m.get('enabled',True):raw.append((m['name'],m,np.zeros(3)))
def matrix(m):
 x,y,z=np.radians(m['rotate']); cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
 rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
 return rz@ry@rx@np.diag(m['scale'])
def boxes(m,off):
 assert not m.get('mirror')
 M=matrix(m);assert np.allclose(np.count_nonzero(abs(M)>1e-8,axis=0),1)
 a=np.array(list(replay(m['work'])),float)
 if len(a)==0:raise RuntimeError('empty source '+m['work']+' '+str(replay_reports[-1]))
 c=(a+.5-np.array(m['pivot']))@M.T+np.array(m['at'])+off
 h=np.sum(abs(M),axis=1)/2
 return c-h,c+h
def touch(lo,hi,occ):
 hits=[]
 for i,(a,b) in enumerate(zip(lo,hi)):
  for v in itertools.product(*(range(math.floor(x+1e-8),math.ceil(y-1e-8)) for x,y in zip(a,b))):
   if v in occ:hits.append((i,v))
 return hits
targets=[]; guns=[]; transformed={}
for path,m,off in raw:
 kind=m.get('meta',{}).get('kind')
 if kind not in ['gun','powder','wheel','binnacle','capstan']:continue
 lo,hi=boxes(m,off); transformed[path]=(lo,hi)
 h=touch(lo,hi,static)
 base=abs(lo[:,2]-np.min(lo[:,2]))<1e-8
 feet=0
 for a,b in zip(lo[base],hi[base]):
  z=round(a[2])-1
  if abs(a[2]-round(a[2]))<1e-8 and any((x,y,z) in static for x in range(math.floor(a[0]+1e-8),math.ceil(b[0]-1e-8)) for y in range(math.floor(a[1]+1e-8),math.ceil(b[1]-1e-8))):feet+=1
 row={'path':path,'kind':kind,'source':m['work'],'source_voxels':len(lo),'positive_pairs':len(h),'collision_samples':h[:5],'bottom_voxels':int(sum(base)),'direct_supported_bottom_voxels':feet,'scale':m['scale'],'meta':m.get('meta',{}),'note':m.get('note','')}
 if kind=='gun':
  an=read(ROOT/m['work']/'anchors.json')['anchors']; pts={x['name']:(np.array(x['at'])+.5-np.array(m['pivot']))@matrix(m).T+np.array(m['at'])+off for x in an};row['points']={k:v.tolist() for k,v in pts.items()};guns.append(row)
 targets.append(row)
# Exact positive-volume model/model tests; broad-phase then vectorized AABB.
pair=[]
for (pa,(al,ah)),(pb,(bl,bh)) in itertools.combinations(transformed.items(),2):
 if np.any(np.max(ah,axis=0)<=np.min(bl,axis=0)+1e-8) or np.any(np.max(bh,axis=0)<=np.min(al,axis=0)+1e-8):continue
 n=0
 for a,b in zip(al,ah):n+=int(np.count_nonzero(np.all(np.minimum(b,bh)-np.maximum(a,bl)>1e-8,axis=1)))
 if n:pair.append({'a':pa,'b':pb,'positive_pairs':n})
# Amanatides/Woo traversal from anchor centers, 200 voxels = 20 m.
def ray(p,d):
 v=np.floor(p).astype(int);step=np.sign(d).astype(int); tmax=np.full(3,np.inf);td=np.full(3,np.inf)
 for k in range(3):
  if d[k]:td[k]=abs(1/d[k]);tmax[k]=((v[k]+(d[k]>0))-p[k])/d[k]
 hits=[];t=0
 while t<=200:
  if tuple(v) in static:hits.append(tuple(map(int,v)))
  k=int(np.argmin(tmax));t=tmax[k];v[k]+=step[k];tmax[k]+=td[k]
 return hits
for g in guns:
 p=np.array(g['points']['muzzle']);d=p-np.array(g['points']['breech']);d/=np.linalg.norm(d);g['ray_20m_hits']=ray(p,d)[:10]
g=next(g for g in guns if g['path']=='甲板-lower/砲-S01');lo,hi=transformed[g['path']]
negative={'path':g['path'],'original_pairs':len(touch(lo,hi,static)),'Y_plus_3_pairs':len(touch(lo+np.array([0,3,0]),hi+np.array([0,3,0]),static)),'Y_plus_3_samples':touch(lo+np.array([0,3,0]),hi+np.array([0,3,0]),static)[:10]}
allropes=[]
for l in [{'name':'','work':assembly.name}]+links:
 p=ROOT/l['work']/'ropes.json'
 if p.exists():
  for r in read(p)['ropes']:
   if r.get('enabled',True):allropes.append(dict(r,frame=l['name']))
rope_groups=collections.Counter(r.get('group','') for r in allropes)
res={'method':'Own independent event replay; exact transformed voxel AABBs for orthogonal target models, positive volume only; own DDA 20m static linked solids rays. No author checker or design modules imported. Current resolved export used only inventory and metadata comparison.','inputs':inputs,'replay':replay_reports,'static_voxels':len(static),'model_count':len(parts['models']),'kinds':dict(collections.Counter(x.get('meta',{}).get('kind','unset') for x in parts['models'])),'targets':targets,'target_model_collisions':pair,'guns':guns,'negative':negative,'rope_count':len(allropes),'rope_groups':dict(rope_groups),'hardware_ropes':[r for r in allropes if 'steer' in r.get('group','') or 'gun' in r.get('group','')],'magazine_links':[x for x in parts['links'] if x.get('meta',{}).get('kind')=='magazine']}
OUT.mkdir(exist_ok=True,parents=True);(OUT/'readback.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'static':len(static),'targets':len(targets),'target_hull_collisions':sum(t['positive_pairs'] for t in targets),'target_pair_collisions':pair,'rays_blocked':[g['path'] for g in guns if g['ray_20m_hits']],'negative':negative,'rope_groups':dict(rope_groups),'cache_differences':[x for x in replay_reports if x['cache_missing'] or x['cache_extra'] or x['cache_color'] or x['unknown']]},ensure_ascii=False))
