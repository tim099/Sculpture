import json,math,itertools,hashlib,argparse
from pathlib import Path
import numpy as np
OUT=Path(__file__).parent;ROOT=Path('D:/Unity/Valhalla/Sculpture/works');I=json.loads((OUT/'input.json').read_text('utf8'));G=json.loads((OUT/'game_bindings.json').read_text('utf8'));yards=I['yards'];vox=np.load(OUT/'body.npy');body=np.zeros(vox[:,:3].max(0)+3,bool);body[tuple(vox[:,:3].T)]=1
OFF=np.array(list(itertools.product((-1,0,1),(-1,0,1),(0,))))
def rot(points,a):
    c,s=math.cos(a),math.sin(a);p=np.array(points,float);o=p.copy();o[...,0]=p[...,0]*c-p[...,1]*s;o[...,1]=p[...,0]*s+p[...,1]*c;return o
for y in yards:
    y['rel']=np.array(y['relative_centers']);y['pivot']=np.array(y['world_pivot']);y['srcpivot']=np.array(y['source_pivot']);cells=np.array(y['cells']);y['lo']=cells.min(0)-2;y['grid']=np.zeros(cells.max(0)-y['lo']+3,bool);y['grid'][tuple((cells-y['lo']).T)]=1
def query(moving_centers,relative_angle,grid,lo=None,margin=0):
    # Exact OBB versus axis-aligned unit cube SAT, with Z fixed. A conservative
    # margin covers all points between neighboring sampled angles when requested.
    base=np.floor(moving_centers).astype(int);q=base[:,None,:]+OFF;d=q+.5-moving_centers[:,None,:];c,s=math.cos(relative_angle),math.sin(relative_angle);lim=.5*(1+abs(c)+abs(s))+margin
    ok=(np.abs(d[...,0])<lim-1e-9)&(np.abs(d[...,1])<lim-1e-9)&(np.abs(c*d[...,0]+s*d[...,1])<lim-1e-9)&(np.abs(-s*d[...,0]+c*d[...,1])<lim-1e-9)
    q=q[ok];p=q if lo is None else q-lo;good=((p>=0)&(p<grid.shape)).all(1);q=q[good];p=p[good]
    return q[grid[tuple(p.T)]] if len(p) else np.empty((0,3),int)
def state_key(angles):return tuple(round(a,7) for a in angles)
states=[];seen=set()
initial={'wind_deg':None,'absolute_angles':[y['r0'] for y in yards],'kind':'physics_off_initial'}
for state in [initial]+[{**s,'kind':'steady_actual_function'} for s in G['samples']]+[{**s,'kind':'transient_actual_function'} for s in G['trajectories']]:
    key=state_key(state['absolute_angles'])
    if key not in seen:seen.add(key);states.append(state)
(OUT/'states.json').write_text(json.dumps(states),'utf8')
report={'source_sha256':I['source_sha256'],'codeHashes':G['codeHashes'],'actual_constants':G['constants'],'body':[],'model_pairs':[],'state_count':len(states),'angle_step_deg':.25,'method':'Original source event unit cubes rotated at actual model pivot. Source mesh bounds independently match export within .005 voxel. OBB/unit-AABB separating axes test; quarter-degree interval envelope bound retained as conservative candidates.'}
all_hits=set()
for y in yards:
    maxa=1.4 if I['header']['rig']['models'][y['model_index']]['meta']['yard'] in ('gaff','boom') else .7
    steps=math.ceil(2*maxa/math.radians(.25));angles=np.linspace(-maxa,maxa,steps+1);radius=np.linalg.norm(y['rel'][:,:2],axis=1).max()+math.sqrt(.5);margin=2*radius*math.sin((angles[1]-angles[0])/4)
    entries=[];conservative=set()
    for a in sorted(set([*angles,y['r0']])):
        centers=rot(y['rel'],a)+y['pivot'];hits=np.unique(query(centers,a,body),axis=0);guard=np.unique(query(centers,a,body,margin=margin),axis=0);conservative.update(map(tuple,guard))
        all_hits.update(map(tuple,guard))
        if len(hits):
            entries.append({'angle_deg':math.degrees(a),'cells':hits.tolist()});all_hits.update(map(tuple,hits))
    item={'name':y['name'],'source_work':y['source_work'],'source_mesh_bounds_error':y['source_mesh_bounds_error'],'absolute_angle_range_deg':[-math.degrees(maxa),math.degrees(maxa)],'relative_angle_range_deg':[-math.degrees(maxa+y['r0']),math.degrees(maxa-y['r0'])],'interval_envelope_margin':margin,'samples':len(angles),'hits':entries,'guard_cells':sorted(conservative)};report['body'].append(item)
    print('body',y['name'],'angles with hits',len(entries),'guard cells',len(conservative),flush=True)
owners={p:[] for p in all_hits}
if (OUT/'guard_owners.json').exists():
    for c in json.loads((OUT/'guard_owners.json').read_text('utf8')):
        p=tuple(c['cell'])
        if p in owners:owners[p]=c['owners']
else:
    for part in I['header']['parts']:
        st={}
        for f in sorted((ROOT/part['src']/'events').rglob('*.json')):
            e=json.loads(f.read_text('utf8'))
            for p in e.get('carved_voxels',[]):st.pop(tuple(p),None)
            for p in e.get('placed_colored',[]):
                if tuple(p[:3]) in owners:st[tuple(p[:3])]=1
            for p in e.get('placed_voxels',[]):
                if tuple(p) in owners:st[tuple(p)]=1
        for p in st:owners[p].append(part['path'])
for y,item in zip(yards,report['body']):
    own=I['header']['rig']['models'][y['model_index']]['meta']['mast'];unique=set(tuple(p) for p in item['guard_cells']);exact=set(tuple(p) for hit in item['hits'] for p in hit['cells']);item['classified_cells']=[]
    for p in sorted(unique):
        root=np.linalg.norm((np.array(p)+.5-y['pivot'])[:2])<=8 and abs(p[2]+.5-y['pivot'][2])<=12
        item['classified_cells'].append({'cell':p,'owners':owners[p],'observed_exact':p in exact,'class':'mast_sling_attachment_candidate' if owners[p]==[own] and root else 'outside_attachment_zone'})
    print('BODY_CLASS',item['name'],[(c['owners'],c['cell']) for c in item['classified_cells'] if c['class']=='outside_attachment_zone'][:12],flush=True)
# Exact source-cube overlap for yard pairs at simultaneously reachable steady and
# explicit rate-limited transition states. No Cartesian-product false witnesses.
for ai,A in enumerate(yards):
    za=np.array(A['cells'])[:,2]+.5-A['srcpivot'][2]+A['pivot'][2]
    for bi in range(ai+1,len(yards)):
        B=yards[bi];zb=np.array(B['cells'])[:,2]+.5-B['srcpivot'][2]+B['pivot'][2]
        if za.max()+.5<=zb.min()-.5 or zb.max()+.5<=za.min()-.5:continue
        if np.linalg.norm(A['pivot'][:2]-B['pivot'][:2])>np.linalg.norm(A['rel'][:,:2],axis=1).max()+np.linalg.norm(B['rel'][:,:2],axis=1).max()+3:continue
        collisions=[]
        for st in states:
            aa,ba=st['absolute_angles'][ai],st['absolute_angles'][bi];world=rot(B['rel'],ba)+B['pivot'];local=rot(world-A['pivot'],-aa)+A['srcpivot'];hit=np.unique(query(local,ba-aa,A['grid'],A['lo']),axis=0)
            if len(hit):
                w=rot(hit+.5-A['srcpivot'],aa)+A['pivot'];collisions.append({'wind_deg':st['wind_deg'],'kind':st['kind'],'angle_a_deg':math.degrees(aa),'angle_b_deg':math.degrees(ba),'source_a_cells':hit.tolist(),'world_centers':w.tolist()})
        report['model_pairs'].append({'a':A['name'],'b':B['name'],'states_with_overlap':len(collisions),'collisions':collisions});print('PAIR',A['name'],B['name'],len(collisions),flush=True)
(OUT/'sweep.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:int(x)),'utf8')
