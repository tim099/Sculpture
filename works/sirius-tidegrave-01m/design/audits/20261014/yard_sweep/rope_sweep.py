import sys,json,ast,itertools,math
from pathlib import Path
import numpy as np
OUT=Path(__file__).parent;I=json.loads((OUT/'input.json').read_text('utf8'));G=json.loads((OUT/'game_bindings.json').read_text('utf8'));states=json.loads((OUT/'states.json').read_text('utf8'));yards=I['yards'];ropes=I['header']['rig']['ropes'];bindings={r['name']:r for r in G['bindings']};model_to_yard={y['model_index']:i for i,y in enumerate(yards)}
tree=ast.parse((OUT/'geometry.py').read_text('utf8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='distance');exec(compile(ast.Module(body=[fn],type_ignores=[]),'own_distance','exec'))
OFF=np.array(list(itertools.product((-1,0,1),repeat=3)))
def rot(points,a):
    c,s=math.cos(a),math.sin(a);p=np.array(points,float);o=p.copy();o[...,0]=p[...,0]*c-p[...,1]*s;o[...,1]=p[...,0]*s+p[...,1]*c;return o
for y in yards:
    y['pivot']=np.array(y['world_pivot']);y['srcpivot']=np.array(y['source_pivot']);cells=np.array(y['cells']);y['lo']=cells.min(0);y['hi']=cells.max(0)+1;y['grid']=np.zeros(y['hi']-y['lo'],bool);y['grid'][tuple((cells-y['lo']).T)]=1;y['zmin']=cells[:,2].min()-y['srcpivot'][2]+y['pivot'][2];y['zmax']=cells[:,2].max()+1-y['srcpivot'][2]+y['pivot'][2]
for r in ropes:
    r['p0']=np.array(r['pts']).reshape(-1,3);r['acc']=np.r_[0,np.cumsum(np.linalg.norm(np.diff(r['p0'],axis=0),axis=1))].astype(np.float32);r['weights']=(r['acc']/r['acc'][-1] if r['acc'][-1]>0 else r['acc'])[:,None];bi=bindings[r['name']];r['ya']=model_to_yard.get(bi['ya'],-1);r['yb']=model_to_yard.get(bi['yb'],-1)
def warp(r,angles):
    a,b=r['ya'],r['yb'];p=r['p0'];w=r['weights']
    pa=rot(p-yards[a]['pivot'],angles[a]-yards[a]['r0'])+yards[a]['pivot'] if a>=0 else p
    pb=rot(p-yards[b]['pivot'],angles[b]-yards[b]['r0'])+yards[b]['pivot'] if b>=0 else p
    return (pa*(1-w)+pb*w).astype(np.float32).astype(float)
def clipped(a,b,lo,hi):
    d=b-a;l=0.;u=1.
    for j in range(3):
        if abs(d[j])<1e-10:
            if a[j]<lo[j] or a[j]>hi[j]:return None
        else:
            A=(lo[j]-a[j])/d[j];B=(hi[j]-a[j])/d[j];l=max(l,min(A,B));u=min(u,max(A,B))
    return (l,u) if l<=u else None
def candidates(a,b,y,r):
    clip=clipped(a,b,y['lo']-r,y['hi']+r)
    if clip is None:return []
    l,u=clip;aa=a+(b-a)*l;bb=a+(b-a)*u;n=max(2,math.ceil(np.linalg.norm(bb-aa)/.5)+1);q=np.floor(np.linspace(aa,bb,n)).astype(int)[:,None,:]+OFF;q=np.unique(q.reshape(-1,3),axis=0);ix=q-y['lo'];good=((ix>=0)&(ix<y['grid'].shape)).all(1);q=q[good];ix=ix[good]
    return q[y['grid'][tuple(ix.T)]] if len(q) else []
summary={};tested=0
for state_index,st in enumerate(states):
    angles=st['absolute_angles'];warped=[warp(r,angles) for r in ropes]
    for yi,y in enumerate(yards):
        a=angles[yi]
        for r,world in zip(ropes,warped):
            rad=r['radius']
            if world[:,2].min()-rad>=y['zmax'] or world[:,2].max()+rad<=y['zmin']:continue
            local=rot(world-y['pivot'],-a)+y['srcpivot'];ll=np.linalg.norm(np.diff(local,axis=0),axis=1);L=ll.sum();walk=0.;events=[]
            for p,q,l in zip(local[:-1],local[1:],ll):
                for cell in candidates(p,q,y,rad):
                    tested+=1;dd,t=distance(p,q,cell)
                    if dd>=rad-1e-6:continue
                    along=walk+t*l;bound=((r['ya']==yi and along<3) or (r['yb']==yi and L-along<3));bug='ratline' in r['name'] and bound
                    kind='game_misbound_ratline_endpoint' if bug else 'bound_rope_endpoint' if bound else 'interior_penetration'
                    where=rot(np.array(cell)+.5-y['srcpivot'],a)+y['pivot'];event={'kind':kind,'penetration':float(rad-dd),'radius':rad,'distance':float(dd),'along':float(along),'length':float(L),'source_yard_cell':cell.tolist(),'world_yard_cell_center':where.tolist(),'state_index':state_index,'wind_deg':st['wind_deg'],'state_kind':st['kind'],'yard_absolute_deg':math.degrees(a),'all_absolute_angles_deg':[math.degrees(x) for x in angles]};events.append(event)
                walk+=l
            if not events:continue
            key=(y['name'],r['name']);rec=summary.setdefault(key,{'yard':y['name'],'rope':r['name'],'binding':{'ya':r['ya'],'yb':r['yb']},'state_indices':set(),'kinds':{},'examples':{}});rec['state_indices'].add(state_index)
            for ev in events:
                kind=ev['kind'];rec['kinds'][kind]=rec['kinds'].get(kind,0)+1
                if kind not in rec['examples'] or ev['penetration']>rec['examples'][kind]['penetration']:rec['examples'][kind]=ev
    if state_index%100==0:print('states',state_index,'pairs',len(summary),'exact tests',tested,flush=True)
out=[]
for rec in summary.values():rec['states_with_contact']=len(rec['state_indices']);rec['state_indices']=sorted(rec['state_indices']);out.append(rec)
(OUT/'rope_sweep.json').write_text(json.dumps({'source_sha256':I['source_sha256'],'states':len(states),'exact_cube_capsule_tests':tested,'method':'Actual game yardNear bindings and yardRopes arc-length endpoint displacement blend. Complete warped rope polylines transformed into source yard unit-cube frame; exact capsule/AABB distance. Only semantically attached first/last 3 arc-length units classified endpoint. Ratline false binding retained separately. Sampled states, not continuous cloth/rope physics certificate.','contacts':out},ensure_ascii=False,indent=2),'utf8');print('DONE',len(out),tested)
