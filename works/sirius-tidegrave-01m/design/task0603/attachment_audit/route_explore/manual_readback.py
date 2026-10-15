from static import *
import hashlib
def parse(f):
 bb=f.read_bytes();rr=zlib.decompress(bb,-15);n=struct.unpack_from('<I',rr,4)[0];return bb,rr[8+n:],json.loads(rr[8:8+n])['rig']
bb,body,new=parse(Q/'manual_candidate.vxk');ob,body0,old=parse(Q/'two_stage_candidate.vxk');assert body==body0;assert new['models']==old['models']and new['meshes']==old['meshes']and new['sails']==old['sails'];assert len(new['ropes'])==500
oldr={r['name']:r for r in old['ropes']};nr={r['name']:r for r in new['ropes']};changed=[]
for r in old['ropes']:
 if r!=nr[r['name']]:
  changed.append(r['name']);assert all(r.get(k)==nr[r['name']].get(k)for k in ['radius','color','frame','meta'])
assert set(changed)=={'main-stay','fore-stay','fore-backstay-P','fore-backstay-S'};assert set(nr)-set(oldr)=={'jib-halyard'}
for case in json.loads((Q/'standing_cases.json').read_text(encoding='utf8')):
 r=nr[case['name']];assert r['pts']==np.array(case['points']).reshape(-1).tolist();assert r['radius']==case['radius'];assert r['ends']==[case['from'],case['to']]
design=(Q/'frozen_sails_design_record.json').read_bytes();actual=pathlib.Path('D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m-assembly/sails.json').read_bytes();assert design==actual
caps=[]
for name in ['main-stay','fore-stay','fore-backstay-P','fore-backstay-S','jib-halyard']:
 r=nr[name];a,b=np.array(r['pts']).reshape(-1,3);rad=r['radius'];L=np.linalg.norm(b-a);samples=max(1,int(np.ceil(L/8)));samplepts=np.linspace(a,b,samples+1);ix=set()
 for row in tree.query_ball_point(samplepts,L/samples/2+.8661+rad):ix.update(row)
 cc=BODY[list(ix)];dd,t=boxdist(a,b,cc);hit=dd<rad*rad-1e-9;caps.append({'rope':name,'body_contacts':[{'cell':c.tolist(),'arc':float(u*L),'distance':float(d**.5)}for c,u,d in zip(cc[hit],t[hit],dd[hit])]})
result={'sha256':hashlib.sha256(bb).hexdigest(),'bytes':len(bb),'ropes':500,'models':166,'body_bytes_identical_to_two_stage':True,'all_models_meshes_and_ten_sails_identical_to_two_stage':True,'original_fixed_sail_design_record_byte_exact':True,'changed_original_ropes':changed,'unchanged_existing_495_ropes':True,'new_rope':'jib-halyard','all_standing_coords_refs_radii_exact':True,'body_terminal_contacts':caps,'fore_stay_head_junction_is_exact_shared_endpoint':nr['fore-stay']['pts'][:3]==nr['jib-halyard']['pts'][-3:],'scope':'Exact data and terminal readback, all-angle yard/body certificates are separate files; no claim of all500 independent-angle rope pairs or all cloth wind states.'}
(Q/'manual_readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k!='body_terminal_contacts'},ensure_ascii=True))
