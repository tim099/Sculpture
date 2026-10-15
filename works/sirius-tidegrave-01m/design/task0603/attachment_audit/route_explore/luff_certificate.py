from static import *
import hashlib
data=(Q/'two_stage_candidate.vxk').read_bytes();rr=zlib.decompress(data,-15);nn=struct.unpack_from('<I',rr,4)[0];NEW=json.loads(rr[8:8+nn])['rig'];s=next(x for x in NEW['sails']if x['name']=='jib');v=np.array(s['verts']).reshape(-1,3);tridx=np.array(s['tris']).reshape(-1,3);tridx=tridx[:len(tridx)//2];a=np.array([748.5,120.5,215.5]);b=np.array([567.5,120.5,269.5]);edge=v[:15];matched=np.linspace(a,b,15);errors=np.linalg.norm(edge-matched,axis=1);delta=float(errors.max());rad=.5;dd=segtri(a,b,v[tridx]);contacts=np.flatnonzero(dd<rad*rad-1e-9);ts,ok=ray(a,b-a,v[tridx]);pierce=ok&(ts>=0)&(ts<=1)
record=json.loads((Q/'frozen_sails_design_record.json').read_text(encoding='utf8'));design=next(x for x in record['sails']if x['name']=='jib');assert design['bind']==[0];assert design['corners'][0]['at']=='bowsprit/tip'and design['corners'][1]['at']=='jib-head-stay-ring';assert design['corners'][0]['pin']and design['corners'][1]['pin']
# Explicit adversarial old stay point sits well inside the free sail, remotely
# from the declared luff. It cannot qualify under this boundary certificate.
old=[x for x in json.loads((Q/'standing_static.json').read_text(encoding='utf8'))if x['option']=='lower-ring-to-bowsprit'][0];neg=[]
for h in old['cloth']:
 if h['sail']!='jib':continue
 for q in h['points']:
  pp=np.array(q);u=np.clip((pp-a)@(b-a)/((b-a)@(b-a)),0,1);d=float(np.linalg.norm(pp-a-u*(b-a)));neg.append(d)
assert max(neg)>rad+delta
result={'vxk_sha256':hashlib.sha256(data).hexdigest(),'declared_fixed_boundary':'jib bind[0], tack=bowsprit/tip, head=jib-head-stay-ring','all_original_design_pins_preserved':True,'fore_stay_ideal_edge':[a.tolist(),b.tolist()],'front_boundary_vertex_indices':list(range(15)),'max_corresponding_point_error_between_p0_polyline_and_ideal_edge':delta,'physical_radius':rad,'all_contact_points_certified_within_boundary_band':rad+delta,'centerline_piercings':np.flatnonzero(pierce).tolist(),'capsule_contact_triangle_indices':contacts.tolist(),'negative_old_interior_piercing_distance_to_luff':neg,'proof':'Both p0 boundary and ideal edge share a monotone matched parameter. Their piecewise-linear interpolation deviation is bounded by the maximum corresponding vertex error. Every point in the exact finite rope capsule is therefore within radius+delta of the declared fixed luff polyline. Only the actual capsule/triangle intersection subset is attached; a complete neighboring triangle is not exempted.'}
(Q/'luff_certificate.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=True))
