"""Read-only negative control using the exact touched-cell function of this verifier."""
import ast,hashlib,json,pathlib,copy
import numpy as np
OUT=pathlib.Path(__file__).parent
ROOT=pathlib.Path('D:/Unity/Valhalla/Sculpture/works')
ruler=OUT.parent/'verify.py';code=ruler.read_text(encoding='utf8');tree=ast.parse(code)
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='touched')
# Compile ONLY the original ruler function; do not execute the full verifier.
ns={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),str(ruler),'exec'),ns);touched=ns['touched']
base=set(map(tuple,np.load(OUT/'base_cells.npy')))
ledger=ROOT/'sirius-tidegrave-01m-deck-lower/models.json'
m=copy.deepcopy(next(m for m in json.loads(ledger.read_text(encoding='utf8'))['models'] if m.get('meta',{}).get('kind')=='gun'))
v={}
for f in sorted((ROOT/m['work']/'events').rglob('*.json')):
 e=json.loads(f.read_text(encoding='utf8'))
 for q in e.get('carved_voxels',[]):v.pop(tuple(q[:3]),None)
 for q in e.get('placed_voxels',[]):v[tuple(q[:3])]=e.get('color')
 for q in e.get('placed_colored',[]):v[tuple(q[:3])]=q[3]
 for q in e.get('edit',{}).get('after',[]):
  qk=(q['x'],q['y'],q['z'])
  if q['color']:v[qk]=q['color']
  else:v.pop(qk,None)
corners=np.array([[x,y,z] for x in [0,1] for y in [0,1] for z in [0,1]])
ax,ay,az=np.radians(m['rotate']);cx,sx=np.cos(ax),np.sin(ax);cy,sy=np.cos(ay),np.sin(ay);cz,sz=np.cos(az),np.sin(az)
R=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
scale=np.array(m['scale'])*[-1 if a in m.get('mirror','') else 1 for a in 'xyz']
points=((np.array(list(v))[:,None,:]+corners[None,:,:]-m['pivot'])*scale)@R.T+m['at']
lo=points.min(axis=1);hi=points.max(axis=1)
def measure(delta):
 hits=set();examples=[];pairs=0
 for k,(a,b) in enumerate(zip(lo+delta,hi+delta)):
  for q in touched(a,b):
   if q in base:
    pairs+=1;hits.add(q)
    if len(examples)<8:examples.append({'base_voxel':list(map(int,q)),'source_box_index':k,'model_box_lo':a.tolist(),'model_box_hi':b.tolist(),'positive_volume_voxel3':float(np.prod(np.minimum(b,np.array(q)+1)-np.maximum(a,q)))})
 return {'actual_delta':delta,'model_at_after':(np.array(m['at'])+delta).tolist(),'positive_volume_pairs':pairs,'unique_base_collision_voxels':len(hits),'examples':examples}
baseline=measure([0,0,0]);trials=[]
for delta in [[0,0,3],[0,3,0],[0,0,-3],[0,10,0]]:
 result=measure(delta);trials.append(result)
 if result['positive_volume_pairs']>0:break
report={'method':'Exact original verify.py touched() compiled alone via AST; transformed source voxel AABBs and strict floor/ceil interior cell enumeration, same ruler as 105-model verification. Modifications exist only in in-memory test coordinates.','ruler_sha256':hashlib.sha256(ruler.read_bytes()).hexdigest(),'ruler_function_sha256':hashlib.sha256(ast.get_source_segment(code,node).encode()).hexdigest(),'base_snapshot_sha256':hashlib.sha256((OUT/'base_cells.npy').read_bytes()).hexdigest(),'model_ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),'gun_name':m['name'],'gun_source_work':m['work'],'original_at':m['at'],'source_voxel_count':len(v),'base_voxel_count':len(base),'baseline':baseline,'trials':trials,'control_passed':baseline['positive_volume_pairs']==0 and any(t['positive_volume_pairs']>0 for t in trials),'files_modified_in_works':False}
(OUT/'gun_negative_control.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'gun':m['name'],'baseline':baseline['positive_volume_pairs'],'trials':[(t['actual_delta'],t['positive_volume_pairs'],t['unique_base_collision_voxels']) for t in trials],'control_passed':report['control_passed']},ensure_ascii=False))
