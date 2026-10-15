from static import *
import os
Q=pathlib.Path(__file__).parent
data=(Q/'routes_candidate.vxk').read_bytes();rr=zlib.decompress(data,-15);nn=struct.unpack_from('<I',rr,4)[0];NEW=json.loads(rr[8:8+nn])['rig'];RNEW={r['name']:r for r in NEW['ropes']};Y={m['name']:m for m in NEW['models']if m['meta'].get('kind')=='yard'}
two_stage=os.environ.get('TWO_STAGE')=='1'
if two_stage:
 for case in json.loads((Q/os.environ.get('STAGE_FILE','two_stage.json')).read_text(encoding='utf8')):
  r=RNEW[case['rope']];r['pts']=np.array(case['points'][:2]).reshape(-1).tolist();r['ends'][1]=','.join(map(str,case['points'][1]));upper=dict(r,name=case['rope']+'.upper',pts=np.array(case['points'][1:]).reshape(-1).tolist(),ends=[','.join(map(str,case['points'][1])),','.join(map(str,case['points'][2]))]);NEW['ropes'].append(upper);RNEW[upper['name']]=upper
def rotp(p,piv,t):
 q=p-piv;c=np.cos(t);s=np.sin(t);o=q.copy();o[...,0]=q[...,0]*c-q[...,1]*s;o[...,1]=q[...,0]*s+q[...,1]*c;return o+piv
def segd(a,b,c,d):
 u=b-a;v=d-c;w=a-c;AA=u@u;B=v@u;CC=np.sum(v*v,axis=1);D=w@u;E=np.sum(v*w,axis=1);den=AA*CC-B*B;s=np.clip(np.divide(B*E-CC*D,den,out=np.zeros(len(c)),where=abs(den)>1e-14),0,1);t=np.clip(np.divide(B*s+E,CC,out=np.zeros(len(c)),where=CC>0),0,1);s=np.clip((B*t-D)/(AA or 1),0,1);t=np.clip(np.divide(B*s+E,CC,out=np.zeros(len(c)),where=CC>0),0,1);dist=np.linalg.norm(w+s[:,None]*u-t[:,None]*v,axis=1);return dist,s,t
def binding(r):return [e[6:].rsplit('/',1)[0]if e.startswith('model:')and e[6:].rsplit('/',1)[0]in Y else None for e in r['ends']]
out=[]
for name in ['fore-topsail.brace-P','fore-topsail.brace-S','mizzen-topsail.brace-P','mizzen-topsail.brace-S']:
 r=RNEW[name];own=Y[binding(r)[0]];piv=np.array(own['points']['pivot']);p=np.array(r['pts']).reshape(-1,3);found={}
 for angle in np.linspace(-.7,.7,57):
  off=angle-own['meta']['rotate_z_deg']*np.pi/180;a=rotp(p[:1],piv,off)[0];b=p[-1]
  for q in NEW['ropes']:
   if q['name']==name:continue
   pp=np.array(q['pts']).reshape(-1,3);bind=binding(q);cum=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pp,axis=0),axis=1))];u=cum/cum[-1]
   if own['name']in bind:
    moved=rotp(pp,piv,off);w=np.ones(len(pp))if bind[0]==bind[1]else(1-u if bind[0]==own['name']else u);pp+=w[:,None]*(moved-pp)
   rad=r['radius']+q['radius']
   if np.any(pp.max(axis=0)+rad<np.minimum(a,b))or np.any(pp.min(axis=0)-rad>np.maximum(a,b)):continue
   dd,s,t=segd(a,b,pp[:-1],pp[1:]);hits=dd<rad-1e-8
   for j in np.flatnonzero(hits):
    pa=a+s[j]*(b-a);pb=pp[j]+t[j]*(pp[j+1]-pp[j]);cap=BODY[(BODY[:,0]>=354)&(BODY[:,0]<=356)&(BODY[:,1]>=119)&(BODY[:,1]<=121)&(BODY[:,2]>=507)&(BODY[:,2]<=510)]
    if two_stage:cap=np.r_[cap,BODY[(BODY[:,0]>=204)&(BODY[:,0]<=206)&(BODY[:,1]>=119)&(BODY[:,1]<=121)&(BODY[:,2]>=402)&(BODY[:,2]<=405)]]
    dc=np.linalg.norm(np.maximum(cap-pa,np.maximum(pa-cap-1,0)),axis=1).min();same_arm=own['name']in bind and np.linalg.norm(pa-a)<3 and np.linalg.norm(pb-a)<3
    if dc<=1+1e-8 or same_arm:continue
    key=q['name'];found[key]={'other':key,'angle':float(angle),'distance':float(dd[j]),'point_a':pa.tolist(),'point_b':pb.tolist(),'candidate_fraction':float(s[j]),'other_segment':int(j),'source_endpoint_binding':bind}
 out.append({'rope':name,'discovery_nonlocal_contacts':list(found.values())});print(name,json.dumps(list(found.values())[:12],ensure_ascii=True),flush=True)
(Q/((pathlib.Path(os.environ.get('STAGE_FILE','two_stage.json')).stem+'_rope_sweep_discovery.json')if two_stage else'rope_sweep_discovery.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
