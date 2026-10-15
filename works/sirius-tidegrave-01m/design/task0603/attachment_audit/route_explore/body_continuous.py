from static import *
import os
Q=pathlib.Path(__file__).parent
def rotA(p,piv,t):
 q=p-piv;c=np.cos(t);s=np.sin(t);return piv+np.array([q[0]*c-q[1]*s,q[0]*s+q[1]*c,q[2]])
records=json.loads((Q/'static.json').read_text(encoding='utf8'));picked=[x for x in records if x['option']=='main-truck'or x['option']=='truck-to-truck'];picked.append({'name':'jib.sheet-S','option':'bulwark-visible-595','points':[rop['jib.sheet-S']['pts'][:3],[595.5,140.5,158.5]],'radius':.2});Y=[m for m in A['models']if m['meta'].get('kind')=='yard'];out=[]
two_stage=os.environ.get('TWO_STAGE')=='1'
if two_stage:
 picked=[x for x in picked if not x['name'].startswith('mizzen-topsail.brace-')]
 for x in json.loads((Q/os.environ.get('STAGE_FILE','two_stage.json')).read_text(encoding='utf8')):
  for i in [0,1]:picked.append({'name':x['rope']+('.upper'if i else''),'option':'two-stage','points':x['points'][i:i+2],'radius':.2})
for rr in picked:
 pp=np.array(rr['points']);rad=rr['radius'];own=None if rr['name'].endswith('.upper')else next((m for m in Y if rr['name'].startswith(m['meta'].get('sail','?')+'.brace-')),None);piv=np.array(own['points']['pivot'])if own else np.zeros(3);Ra=np.linalg.norm((pp[0]-piv)[:2])if own else 0
 cap=BODY[(BODY[:,0]>=354)&(BODY[:,0]<=356)&(BODY[:,1]>=119)&(BODY[:,1]<=121)&(BODY[:,2]>=508)&(BODY[:,2]<=510)]
 if rr['name']=='mizzen-stay':cap=np.r_[cap,BODY[(BODY[:,0]>=204)&(BODY[:,0]<=206)&(BODY[:,1]>=119)&(BODY[:,1]<=121)&(BODY[:,2]==405)]]
 if rr['name']=='jib.sheet-S':cap=np.array([[595.,140.,158.]])
 if rr['option']=='two-stage':
  mc=BODY[(BODY[:,0]>=204)&(BODY[:,0]<=206)&(BODY[:,1]>=119)&(BODY[:,1]<=121)&(BODY[:,2]>=403)&(BODY[:,2]<=405)]
  cap=np.r_[cap,mc]if rr['name'].endswith('.upper')else mc
 capset={tuple(c)for c in cap};stack=[(-.7,.7,0)]if own else[(0,0,0)];calls=0;bad=[];certmin=1e9;leaves=0
 while stack:
  lo,hi,depth=stack.pop();theta=(lo+hi)/2;a=rotA(pp[0],piv,theta-own['meta']['rotate_z_deg']*np.pi/180)if own else pp[0];b=pp[1];bound=Ra*(hi-lo)/2;L=np.linalg.norm(b-a);cc=BODY[tree.query_ball_point((a+b)/2,float(L/2+.8661+rad+bound+1e-6))];cc=np.array([c for c in cc if tuple(c)not in capset]);calls+=1
  if not len(cc):leaves+=1;continue
  dd,tt=boxdist(a,b,cc);d=float(dd.min()**.5)
  if d-bound>=rad-1e-9:leaves+=1;certmin=min(certmin,d-bound);continue
  if d<rad-1e-9 or depth>=30:bad.append({'angle':theta,'cell':cc[int(dd.argmin())].tolist(),'distance':d,'interval':[lo,hi],'bound':bound});break
  mid=(lo+hi)/2;stack.extend([(lo,mid,depth+1),(mid,hi,depth+1)])
 out.append({'rope':rr['name'],'named_attachment_real_cells':cap.tolist(),'cap_bbox':np.r_[cap.min(axis=0),cap.max(axis=0)+1].tolist(),'interval_calls':calls,'separated_leaves':leaves,'minimum_certified_non_attachment_distance':certmin,'fail_or_unresolved':bad});print(rr['name'],'calls',calls,'bad',bad,flush=True)
(Q/((pathlib.Path(os.environ.get('STAGE_FILE','two_stage.json')).stem+'_body_continuous.json')if two_stage else'body_continuous.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
