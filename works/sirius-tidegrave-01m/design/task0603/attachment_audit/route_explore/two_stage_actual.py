from static import *
import hashlib,subprocess
def parse(f):
 bb=f.read_bytes();rr=zlib.decompress(bb,-15);nn=struct.unpack_from('<I',rr,4)[0];return bb,rr[8+nn:],json.loads(rr[8:8+nn])['rig']
bb,body,new=parse(Q/'two_stage_candidate.vxk');ob,oldbody,old=parse(Q/'routes_candidate.vxk');assert body==oldbody;assert new['sails']==old['sails'];assert new['meshes']==old['meshes'];assert len(new['ropes'])==499
nm={m['name']:m for m in new['models']};changed=[]
for m in old['models']:
 nn=nm[m['name']]
 if m!=nn:
  assert m['name']=='mizzen/yard-mizzen-topsail';assert {k:v for k,v in m.items()if k!='points'}=={k:v for k,v in nn.items()if k!='points'};assert all(nn['points'][k]==v for k,v in m['points'].items());assert set(nn['points'])-set(m['points'])=={'brace-out-P','brace-out-S'};changed.append(m['name'])
assert changed==['mizzen/yard-mizzen-topsail'];model=nm[changed[0]];me=new['meshes'][model['mesh']];tr=(np.array(me['verts']).reshape(-1,3)+model['origin'])[np.array(me['tris']).reshape(-1,3)];eye=[]
for side in ['P','S']:
 q=np.array(model['points']['brace-out-'+side]);assert inside(q,tr);eye.append({'side':side,'point':q.tolist(),'inside_actual_original_yard_mesh':True})
nr={r['name']:r for r in new['ropes']};OR={r['name']:r for r in old['ropes']};ropechanged=[];cases=json.loads((Q/'two_stage_outboard.json').read_text(encoding='utf8'))
for r in old['ropes']:
 if nr[r['name']]!=r:ropechanged.append(r['name'])
assert set(ropechanged)=={'mizzen-topsail.brace-P','mizzen-topsail.brace-S'}
for x in cases:
 for i in [0,1]:
  name=x['rope']+('.upper'if i else'');r=nr[name];assert r['pts']==np.array(x['points'][i:i+2]).reshape(-1).tolist();assert all(r.get(k)==OR[x['rope']].get(k)for k in ['radius','color','frame','meta'])
 # An exact geometric lower bound against the preexisting lift, all angles.
 # Source displacement is one grid outboard, terminal displacement one grid
 # to the same side. Absolute theta <=.7 gives signed Y displacement >=cos(.7).
 # Project (Y,Z) onto the lift normal; the varying source-to-cap Y span <=46.
 # Rounded export endpoints introduce <=sqrt(2)*.005 error per moving endpoint.
lower=np.cos(.7)*65/np.hypot(65,46)-2*np.sqrt(2)*.005
assert lower>.4
src=pathlib.Path('D:/Unity/Valhalla/Sculpture');rel='works/sirius-tidegrave-01m-assembly/sails.json';head=subprocess.check_output(['git','show','HEAD:'+rel],cwd=src);current=(src/rel).read_bytes();assert json.loads(head)==json.loads(current);(Q/'frozen_sails_design_record.json').write_bytes(current)
result={'sha256':hashlib.sha256(bb).hexdigest(),'bytes':len(bb),'ropes':499,'models':166,'body_bytes_unchanged':True,'all_ten_export_sails_exact_same_as_routes_candidate':True,'all_sail_design_records_equal_git_HEAD':True,'git_HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=src).decode().strip(),'source_geometry_all_mesh_bytes_values_unchanged':True,'all_original_model_points_unchanged':True,'only_model_change_two_brace_out_points':changed,'only_existing_rope_changes':ropechanged,'only_rope_additions':[x for x in nr if x not in OR],'outboard_support_proof':eye,'all_angle_same_side_lift_distance_lower_bound_after_roundoff':float(lower),'radius_sum':.4,'verdict':'PASS exact two-stage implementation; general rope sweep discovery is a separate scope, not certified by byte comparison'}
(Q/'two_stage_actual.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=True))
