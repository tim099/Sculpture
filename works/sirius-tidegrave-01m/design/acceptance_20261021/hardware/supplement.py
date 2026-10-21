import json,pathlib,hashlib,itertools,math
R=pathlib.Path('D:/Unity/Valhalla/Sculpture/works');O=pathlib.Path(__file__).parent
def replay(w):
 d={}
 for p in sorted((R/w/'events').glob('*/*.json')):
  a=json.loads(p.read_text(encoding='utf-8-sig'))
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
   for v in a['carved_voxels']:d.pop(tuple(v),None)
 return d
a=json.loads((O/'additional.json').read_text(encoding='utf-8'));a['passages']=[]
for p in (R/'sirius-tidegrave-01m/design').glob('*fairlead_holes.vox.txt'):
 w=p.name.split('_fairlead')[0];s=replay(w);cells=[tuple(map(int,l.split(',')[:3])) for l in p.read_text().splitlines() if l.strip()];assert cells
 a['passages'].append({'work':w,'designed_holes':len(cells),'current_occupied':sum(v in s for v in cells),'coordinates_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
w=set(replay('basecamp-frigate-constitution-01m-wheel'));s=set(replay('basecamp-frigate-constitution-01m-wheel-stand'));ds=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
a['wheel_stand']['wheel_source_face_contacts']=sum(tuple(v[k]+d[k] for k in range(3)) in s for v in w for d in ds)
parts=json.loads((O.parent/'shared/parts.json').read_text(encoding='utf-8-sig'));solid=set()
raw=json.loads((R/'sirius-tidegrave-01m-assembly/links.json').read_text(encoding='utf-8-sig'))['links']
for l in raw:solid.update(tuple(v[k]+l['at'][k] for k in range(3)) for v in replay(l['work']))
rud=set(replay('sirius-tidegrave-01m-rudder'));a['rudder']={'voxels':len(rud),'static_collision':len(rud&solid),'face_contacts':sum(tuple(v[k]+d[k] for k in range(3)) in solid for v in rud for d in ds)}
(O/'additional.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in a.items() if k!='resolved_anchor_comparison'},ensure_ascii=False))
