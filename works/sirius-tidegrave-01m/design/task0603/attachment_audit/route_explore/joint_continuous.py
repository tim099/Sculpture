from static import *
Q=pathlib.Path(__file__).parent
def rotp(p,piv,t):
 q=p-piv;c=np.cos(t);s=np.sin(t);return piv+np.array([q[0]*c-q[1]*s,q[0]*s+q[1]*c,q[2]])
cap=BODY[(BODY[:,0]>=354)&(BODY[:,0]<=356)&(BODY[:,1]>=119)&(BODY[:,1]<=121)&(BODY[:,2]>=507)&(BODY[:,2]<=510)]
def dcap(p):return float(np.linalg.norm(np.maximum(cap-p,np.maximum(p-(cap+1),0)),axis=1).min())
def dline(p,pp):
 a=pp[:-1];d=pp[1:]-a;t=np.clip(np.sum((p-a)*d,axis=1)/np.sum(d*d,axis=1),0,1);return float(np.linalg.norm(p-a-t[:,None]*d,axis=1).min())
records=json.loads((Q/'static.json').read_text(encoding='utf8'));picked=[x for x in records if x['option']=='main-truck'or x['option']=='truck-to-truck'];Y=[m for m in A['models']if m['meta'].get('kind')=='yard'];out=[]
for rr in picked:
 pp=np.array(rr['points']);own=next((m for m in Y if rr['name'].startswith(m['meta'].get('sail','?')+'.brace-')),None);pivot=np.array(own['points']['pivot'])if own else np.zeros(3);Ra=np.linalg.norm((pp[0]-pivot)[:2])if own else 0;Lmax=np.linalg.norm(pp[1]-pivot)+Ra if own else np.linalg.norm(pp[1]-pp[0])
 for qname in ['main-backstay-P','main-backstay-S']:
  qr=rop[qname];q=np.array(qr['pts']).reshape(-1,3);rsum=rr['radius']+qr['radius'];joint_radius=1.;stack=[(-.7,.7,0.,1.,0)]if own else[(0.,0.,0.,1.,0)];calls=0;good=0;joint=0;bad=[]
  while stack:
   al,ah,ul,uh,depth=stack.pop();aa=(al+ah)/2;uu=(ul+uh)/2;a=rotp(pp[0],pivot,aa-own['meta']['rotate_z_deg']*np.pi/180)if own else pp[0];p=a*(1-uu)+pp[1]*uu;ba=Ra*(1-ul)*(ah-al)/2;bu=Lmax*(uh-ul)/2;bound=ba+bu;calls+=1
   if dcap(p)+bound<=joint_radius+1e-10:joint+=1;continue
   dl=dline(p,q)
   if dl-bound>=rsum-1e-10:good+=1;continue
   if (dl<rsum-1e-9 and dcap(p)>joint_radius+1e-9)or depth>=45:bad.append({'angle':aa,'u':uu,'point':p.tolist(),'line_distance':dl,'real_cap_surface_distance':dcap(p),'depth':depth});break
   if ba>=bu:mid=(al+ah)/2;stack.extend([(al,mid,ul,uh,depth+1),(mid,ah,ul,uh,depth+1)])
   else:mid=(ul+uh)/2;stack.extend([(al,ah,ul,mid,depth+1),(al,ah,mid,uh,depth+1)])
  out.append({'rope':rr['name'],'other':qname,'cap_cells':cap.tolist(),'certified_contact_neighborhood_of_actual_cells':joint_radius,'neighborhood_definition':'reported all-angle spatial bound: one ship grid unit (0.1m) from 20 explicit real mastcap cells; contacts remain real contacts, not a generic endpoint exemption or contact-free assertion','interval_calls':calls,'free_leaves':good,'actual_cap_joint_leaves':joint,'fail_or_unresolved':bad});print(rr['name'],qname,'calls',calls,'bad',bad,flush=True)
(Q/'joint_continuous.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
