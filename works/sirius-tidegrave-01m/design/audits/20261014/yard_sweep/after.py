import json,sys,ast,math,itertools,hashlib,collections
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent));import vxk_decode as V
OUT=Path(__file__).parent;ROOT=Path('D:/Unity/Valhalla/Sculpture/works');I=json.loads((OUT/'input.json').read_text('utf8'));before=I['header'];src=OUT/'source_after.vxk';blob=src.read_bytes();h,vox=V.unpack(blob);sha=hashlib.sha256(blob).hexdigest();assert sha=='a5994eeeacbb1155776145e3ebc2e69bd743815b7574df45ca6eb58653bdaf73',sha;(OUT/'source_after.vxk').write_bytes(blob);(OUT/'after_input.json').write_text(json.dumps({'source_sha256':sha,'header':h},ensure_ascii=False),'utf8');occ={tuple(p[:3]) for p in vox};occupied=occ
tree=ast.parse((OUT/'geometry.py').read_text('utf8'));exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]),'own_capsule','exec'))
tree=ast.parse((OUT/'geometry.py').read_text('utf8'));fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='triangle_hits');exec(compile(ast.Module(body=[fn],type_ignores=[]),'own_sat','exec'))
out={'before_sha256':I['source_sha256'],'after_sha256':sha,'voxels':len(vox),'checksum':hex(V.checksum(vox)),'source':str(src),'changed_ropes':[],'changed_models':[],'changed_cloth':[]}
def packed(a):return (((a[:,0].astype(np.uint64)*256+a[:,1])*1024+a[:,2])*256+a[:,3])
oldvox=np.load(OUT/'body.npy');oldkeys=packed(oldvox);newkeys=packed(vox);added=np.setdiff1d(newkeys,oldkeys);removed=np.setdiff1d(oldkeys,newkeys);out['body_delta']={'new_or_recolored_voxels':len(added),'removed_voxels':len(removed),'new_body_is_exact_color_preserving_subset':len(added)==0}
oldrope={r['name']:r for r in before['rig']['ropes']}
for r in h['rig']['ropes']:
    b=oldrope[r['name']]
    if r!=b:out['changed_ropes'].append({'name':r['name'],'changed_fields':[k for k in set(r)|set(b) if r.get(k)!=b.get(k)]})
oldmodels={m['name']:m for m in before['rig']['models']}
for m in h['rig']['models']:
    b=oldmodels[m['name']]
    if m!=b:out['changed_models'].append({'name':m['name'],'changed_fields':[k for k in set(m)|set(b) if m.get(k)!=b.get(k)]})
oldsails={s['name']:s for s in before['rig']['sails']}
for s in h['rig']['sails']:
    b=oldsails[s['name']]
    if s!=b:out['changed_cloth'].append({'name':s['name'],'changed_fields':[k for k in set(s)|set(b) if s.get(k)!=b.get(k)]})
out['rig_meshes_unchanged']=h['rig']['meshes']==before['rig']['meshes'];cj=next(m for m in h['rig']['models'] if m['name'].endswith('mizzen-crossjack'));gaff=next(m for m in h['rig']['models'] if m['name'].endswith('mizzen-gaff'));boom=next(m for m in h['rig']['models'] if m['name'].endswith('mizzen-boom'));out['continuous_Z_separation']={'crossjack_z':[cj['bbox'][2],cj['bbox'][5]],'gaff_z':[gaff['bbox'][2],gaff['bbox'][5]],'boom_z':[boom['bbox'][2],boom['bbox'][5]],'gaff_gap':gaff['bbox'][2]-cj['bbox'][5],'boom_gap':cj['bbox'][2]-boom['bbox'][5],'all_absolute_angles_including_independent_transients':cj['bbox'][5]<gaff['bbox'][2] and cj['bbox'][2]>boom['bbox'][5]}
out['sheet_capsules']=[]
for r in h['rig']['ropes']:
    if not r['name'].startswith('mizzen-topsail.sheet'):continue
    pts=np.array(r['pts']).reshape(-1,3);ls=np.linalg.norm(np.diff(pts,axis=0),axis=1);L=ls.sum();walk=0;found={}
    for a,b,l in zip(pts[:-1],pts[1:],ls):
        for cell,dd,t in hits(a,b,r['radius']):
            s=walk+t*l;found[cell]={'cell':cell,'distance':dd,'kind':'endpoint_zone' if s<3 or L-s<3 else 'interior'}
        walk+=l
    out['sheet_capsules'].append({'name':r['name'],'radius':r['radius'],'pts':r['pts'],'voxel_collisions':list(found.values()),'interior_count':sum(c['kind']=='interior' for c in found.values())})
s=next(s for s in h['rig']['sails'] if s['name']=='mizzen-topsail');vs=np.array(s['verts']).reshape(-1,3);ts=np.array(s['tris']).reshape(-1,3);half=len(vs)//2;front=ts[(ts<half).all(1)];edges=collections.Counter(tuple(sorted(e)) for t in front for e in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])));boundary=set(itertools.chain.from_iterable(e for e,n in edges.items() if n==1));allhit=set();inner=set()
for t in front:
    found=triangle_hits(vs[t]);allhit.update(found)
    if not any(v in boundary for v in t):inner.update(found)
out['mizzen_topsail_static']={'bbox':[vs.min(0).tolist(),vs.max(0).tolist()],'all_voxel_collision_cells':sorted(allhit),'strict_interior_triangle_collision_cells':sorted(inner),'scope':'Exact triangle/unit-box SAT versus body voxels; source-yard models tested separately below.'}
# Exact cloth triangle / gaff-or-crossjack cube SAT: transform cloth into each
# yard's source cell frame, retaining source geometry (no voxelizing rotated mesh).
out['cloth_to_yard_models']=[]
for source in I['yards']:
    model=next(m for m in h['rig']['models'] if m['name']==source['name']);pivot=np.array(model['points']['pivot']);a=source['r0'];co,si=math.cos(-a),math.sin(-a);local=vs-pivot;ll=local.copy();ll[:,0]=co*local[:,0]-si*local[:,1];ll[:,1]=si*local[:,0]+co*local[:,1];ll+=np.array(source['source_pivot']);occupied={tuple(p) for p in source['cells']};full=set();inside=set()
    for t in front:
        found=triangle_hits(ll[t]);full.update(found)
        if not any(v in boundary for v in t):inside.update(found)
    out['cloth_to_yard_models'].append({'yard':source['name'],'all_source_cells':sorted(full),'strict_interior_source_cells':sorted(inside)})
(OUT/'after.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=lambda x:int(x)),'utf8');print('DELTA',out['body_delta'],out['changed_models'],out['changed_ropes'],out['changed_cloth']);print('Z',out['continuous_Z_separation']);print('SHEETS',[(r['name'],r['interior_count']) for r in out['sheet_capsules']]);print('CLOTH',len(allhit),len(inner),[(r['yard'],len(r['strict_interior_source_cells'])) for r in out['cloth_to_yard_models']])
