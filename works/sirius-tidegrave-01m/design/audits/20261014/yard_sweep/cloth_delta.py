import json,ast,itertools
from pathlib import Path
import numpy as np
OUT=Path(__file__).parent;before=json.loads((OUT/'input.json').read_text('utf8'))['header'];after=json.loads((OUT/'after_input.json').read_text('utf8'))['header'];occupied={(207,120,336)}
tree=ast.parse((OUT/'geometry.py').read_text('utf8'));fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='triangle_hits');exec(compile(ast.Module(body=[fn],type_ignores=[]),'own_sat','exec'))
def clip(tri,cell):
    poly=[p.copy() for p in tri]
    for axis in range(3):
        for plane,side in [(cell[axis],1),(cell[axis]+1,-1)]:
            old=poly;poly=[]
            if not old:continue
            for p,q in zip(old,old[1:]+old[:1]):
                pin=side*(p[axis]-plane)>=0;qin=side*(q[axis]-plane)>=0
                if pin:poly.append(p)
                if pin!=qin:poly.append(p+(q-p)*((plane-p[axis])/(q[axis]-p[axis])))
    if len(poly)<3:return [],0.
    area=np.linalg.norm(sum((np.cross(poly[i]-poly[0],poly[i+1]-poly[0]) for i in range(1,len(poly)-1)),np.zeros(3)))*.5
    return [p.tolist() for p in poly],float(area)
result={'target_cell':[207,120,336],'snapshots':[]}
for label,h in [('before_5e92885e',before),('after_a5994eee',after)]:
    s=next(s for s in h['rig']['sails'] if s['name']=='mizzen-topsail');vs=np.array(s['verts']).reshape(-1,3);ts=np.array(s['tris']).reshape(-1,3);front=ts[(ts<len(vs)//2).all(1)];edges={}
    for t in front:
        for e in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):key=tuple(sorted(e));edges[key]=edges.get(key,0)+1
    boundary=set(itertools.chain.from_iterable(e for e,n in edges.items() if n==1));hits=[]
    for ti,t in enumerate(front):
        if any(v in boundary for v in t):continue
        if triangle_hits(vs[t]):
            poly,area=clip(vs[t],result['target_cell']);hits.append({'triangle_index_front':ti,'indices':t.tolist(),'vertices':vs[t].tolist(),'clipped_polygon':poly,'area_voxel_squared':area})
    result['snapshots'].append({'name':label,'strict_inner_target_hits':hits})
result['conclusion']='new_after_crossjack_lowering' if not result['snapshots'][0]['strict_inner_target_hits'] and result['snapshots'][1]['strict_inner_target_hits'] else 'pre_existing' if result['snapshots'][0]['strict_inner_target_hits'] else 'no_confirmed_inner_collision'
(OUT/'cloth_delta.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');print(result)
