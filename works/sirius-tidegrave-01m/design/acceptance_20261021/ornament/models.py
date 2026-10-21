"""Independent transformed source voxel OBB vs ornament unit AABB, strict volume SAT."""
import json,math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
OUT=Path(__file__).resolve().parent
B=Path('D:/Unity/Valhalla/Sculpture/works')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def replay(w):
 a={}
 for p in sorted((B/w/'events').rglob('*.json')):
  e=load(p)
  if e['op']=='workedit':
   for v in e['edit'].get('after',[]):
    q=(v['x'],v['y'],v['z'])
    if v['color']:a[q]=v['color']
    else:a.pop(q,None)
  for v in e.get('carved_voxels',[]):a.pop(tuple(v[:3]),None)
  for v in e.get('placed_colored',[]):a[tuple(v[:3])]=v[3]
  for v in e.get('placed_voxels',[]):a[tuple(v[:3])]=e['color']
 return np.array(list(a),float)
orn=replay('sirius-tidegrave-01m-ornament')+.5;tree=cKDTree(orn)
assembly='sirius-tidegrave-01m-assembly';links=load(B/assembly/'links.json')['links']
instances=[(assembly,np.zeros(3),'')]+[(l['work'],np.array(l['at']),l['name']+'/') for l in links if l.get('enabled',True)]
cache={};reports=[];allcoll=[];source_checks={}
def rot(v):
 x,y,z=np.radians(v);cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z)
 return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def overlaps(delta,R,h):
 axes=[*np.eye(3),*R.T]+[np.cross(x,y) for x in np.eye(3) for y in R.T]
 for axis in axes:
  if np.linalg.norm(axis)<1e-8:continue
  limit=.5*np.abs(axis).sum()+np.abs(axis@R)@h
  if abs(delta@axis)>=limit-1e-8:return False
 return True
tested_pairs=0;actual_model_negative=None
for w,t,prefix in instances:
 p=B/w/'models.json'
 if not p.exists():continue
 for m in load(p)['models']:
  if not m.get('enabled',True):continue
  name=prefix+m['name'];r={'name':name,'source_work':m.get('work'),'rotate':m['rotate'],'status':'unverified'}
  if m['source']!='work':r['reason']='file mesh source';reports.append(r);continue
  sw=m['work']
  if sw not in cache:
   cache[sw]=replay(sw)
   cp=B/sw/'sculpt_cache.json'
   cc=load(cp).get('voxels',{}) if cp.exists() else {}
   ck={tuple(map(int,k.split(','))) for k,v in cc.items() if v}
   rp={tuple(map(int,q)) for q in cache[sw]}
   nested=B/sw/'links.json';nested_models=B/sw/'models.json'
   source_checks[sw]={'events_cells':len(rp),'cache_cells':len(ck),'missing':len(ck-rp),'extra':len(rp-ck),'nested_links':len(load(nested).get('links',[])) if nested.exists() else 0,'nested_models':len(load(nested_models).get('models',[])) if nested_models.exists() else 0}
  src=cache[sw]
  if len(src)==0:r['reason']='empty source event replay';reports.append(r);continue
  R=rot(m['rotate']);scale=np.array(m['scale'],float);sign=np.array([-1 if a in m.get('mirror','') else 1 for a in 'xyz'])
  centers=((src+.5-np.array(m['pivot']))*scale*sign)@R.T+np.array(m['at'])+t
  h=scale/2;ext=np.abs(R)@h
  if actual_model_negative is None:
   moved=centers+(orn[0]-centers[0]);hits=0
   for c,ids in zip(moved,tree.query_ball_point(moved,float(np.linalg.norm(h)+np.sqrt(.75)))):
    for i in ids:
     d=orn[i]-c
     if np.all(np.abs(d)<ext+.5-1e-8) and overlaps(d,R,h):hits+=1
   actual_model_negative={'model':name,'source_cells_translated':len(src),'translate':(orn[0]-centers[0]).tolist(),'collision_pairs':hits,'baseline_model_not_mutated':True}
  # Per-cell source geometry: only cells near actual ornament are potential pairs.
  near=tree.query_ball_point(centers,float(np.linalg.norm(h)+np.sqrt(.75)))
  collisions=[];candidates=sum(map(len,near));tested_pairs+=candidates
  for c,ids in zip(centers,near):
   for i in ids:
    d=orn[i]-c
    if np.any(np.abs(d)>=ext+.5-1e-8):continue
    if overlaps(d,R,h):collisions.append([orn[i].tolist(),c.tolist()])
  r.update(status='pass' if not collisions else 'collision',source_cells=len(src),candidate_pairs=candidates,collision_pairs=len(collisions),examples=collisions[:8])
  if collisions:allcoll.append(r)
  reports.append(r)
# Same exact classifier, actual model cube moved onto actual ornament voxel.
negative=overlaps(np.zeros(3),np.eye(3),np.ones(3)*.5)
result={'method':'Actual per-source voxel event replay; unit cubes transformed with at + Rz Ry Rx (scale * mirror (p-pivot)); linked work translation; exact OBB/unit-AABB separating axis test, touching excluded 1e-8. No author modules imported. Current neutral static model transforms only.', 'models':len(reports),'source_meshes':len(cache),'source_checks':source_checks,'tested_pairs':tested_pairs,'unverified':[r for r in reports if r['status']=='unverified'],'collision_models':len(allcoll),'collision_pairs':sum(r['collision_pairs'] for r in allcoll),'negative_exact_cube_overlap':negative,'negative_touch_only':overlaps(np.array([1.,0,0]),np.eye(3),np.ones(3)*.5),'reports':reports}
(OUT/'models_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result['actual_whole_model_translation_negative']=actual_model_negative
(OUT/'models_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print({k:v for k,v in result.items() if k not in ['reports','unverified','source_checks']});print('unverified count',len(result['unverified']));print('source issues',[s for s,c in source_checks.items() if c['missing'] or c['extra'] or c['nested_links'] or c['nested_models']])
