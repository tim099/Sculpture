from static import *
import hashlib
Q=pathlib.Path(__file__).parent
data=(Q/'routes_candidate.vxk').read_bytes();rr=zlib.decompress(data,-15);nn=struct.unpack_from('<I',rr,4)[0];NEW=json.loads(rr[8:8+nn])['rig'];NROP={r['name']:r for r in NEW['ropes']};changed=[];cloth=[]
for old in A['ropes']:
 new=NROP[old['name']]
 if old!=new:
  changed.append(old['name'])
  for key in ['radius','color','frame','meta']:assert old.get(key)==new.get(key)
assert set(changed)=={'mizzen-stay','fore-topsail.brace-P','fore-topsail.brace-S','mizzen-topsail.brace-P','mizzen-topsail.brace-S','jib.sheet-S'}
assert NEW['models']==A['models']and NEW['meshes']==A['meshes']
oldbytes=(P/'actual_final/input.vxk').read_bytes();oldraw=zlib.decompress(oldbytes,-15);oldn=struct.unpack_from('<I',oldraw,4)[0];assert rr[8+nn:]==oldraw[8+oldn:]
saildelta=[]
for old,new in zip(A['sails'],NEW['sails']):
 if old!=new:
  assert old['name']=='jib';assert all(old[k]==new[k]for k in old if k!='verts');v0=np.array(old['verts']).reshape(-1,3);v1=np.array(new['verts']).reshape(-1,3);saildelta.append({'name':'jib','changed_vertices':int(np.any(v0!=v1,axis=1).sum()),'max_coordinate_delta':float(abs(v0-v1).max()),'unchanged_vertices':np.flatnonzero(np.all(v0==v1,axis=1)).tolist()})
for name in changed:
 p=np.array(NROP[name]['pts']).reshape(-1,3);rad=NROP[name]['radius'];a,b=p
 for s in NEW['sails']:
  vs=np.array(s['verts']).reshape(-1,3);tr=vs[np.array(s['tris']).reshape(-1,3)];tr=tr[:len(tr)//2];cand=np.all((tr.max(axis=1)>=np.minimum(a,b)-rad)&(tr.min(axis=1)<=np.maximum(a,b)+rad),axis=1);ids=np.flatnonzero(cand);tr=tr[cand]
  if not len(tr):continue
  dd=segtri(a,b,tr);tt,ok=ray(a,b-a,tr);hits=ok&(tt>=0)&(tt<=1)
  if np.any(hits)or np.any(dd<rad*rad-1e-9):cloth.append({'rope':name,'sail':s['name'],'capsule_tris':ids[dd<rad*rad-1e-9].tolist(),'centerline_tris':ids[hits].tolist(),'points':(a+tt[hits,None]*(b-a)).tolist()})
 # All actual new endpoints must reside in the named real body attachment solids.
 if name=='jib.sheet-S':
  assert p[-1].tolist()==[595.5,140.5,158.5]
  cc=BODY[tree.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+1.0661))];dd,t=boxdist(a,b,cc);contacts=cc[dd<rad*rad-1e-9];assert contacts.tolist()==[[595.,140.,158.]]
result={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'ropes':len(NEW['ropes']),'models':len(NEW['models']),'changed_ropes':changed,'unchanged_other_491_ropes':True,'radius_color_frame_meta_preserved':True,'body_chunk_bytes_unchanged':True,'all_models_meshes_unchanged':True,'sail_export_delta':saildelta,'new_6_rope_vs_actual_export_cloth':cloth,'jib_terminal_only_actual_cell':[595,140,158],'note':'jib export free-cloth geometry recomputed after sheet endpoint change; original sail record and fixed attachment declarations not edited. This is a delta disclosure, not an all-ten-sails-unchanged claim.'}
(Q/'actual_readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=True))
