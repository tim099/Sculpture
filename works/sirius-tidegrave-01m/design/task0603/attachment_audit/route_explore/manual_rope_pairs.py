from static import *
data=(Q/'manual_candidate.vxk').read_bytes();rr=zlib.decompress(data,-15);nn=struct.unpack_from('<I',rr,4)[0];NEW=json.loads(rr[8:8+nn])['rig'];lines=[]
for r in NEW['ropes']:
 p=np.array(r['pts']).reshape(-1,3);lines.append((r,p,p.min(axis=0)-r['radius'],p.max(axis=0)+r['radius']))
def segd(a,b,c,d):
 u=b-a;v=d-c;w=a-c;AA=u@u;B=v@u;CC=np.sum(v*v,axis=1);D=w@u;E=np.sum(v*w,axis=1);den=AA*CC-B*B;s=np.clip(np.divide(B*E-CC*D,den,out=np.zeros(len(c)),where=abs(den)>1e-14),0,1);t=np.clip(np.divide(B*s+E,CC,out=np.zeros(len(c)),where=CC>0),0,1);s=np.clip((B*t-D)/(AA or 1),0,1);t=np.clip(np.divide(B*s+E,CC,out=np.zeros(len(c)),where=CC>0),0,1);return np.linalg.norm(w+s[:,None]*u-t[:,None]*v,axis=1),s,t
changed={'main-stay','fore-stay','fore-backstay-P','fore-backstay-S','jib-halyard','mizzen-topsail.brace-P','mizzen-topsail.brace-S','mizzen-topsail.brace-P.upper','mizzen-topsail.brace-S.upper'};out=[]
for i,(r,p,lo,hi)in enumerate(lines):
 for q,v,qlo,qhi in lines[i+1:]:
  if np.any(hi<qlo)or np.any(qhi<lo):continue
  rad=r['radius']+q['radius']
  for j,(a,b)in enumerate(zip(p[:-1],p[1:])):
   ds,s,t=segd(a,b,v[:-1],v[1:]);mask=ds<rad-1e-8
   for k in np.flatnonzero(mask):
    pa=a+s[k]*(b-a);pb=v[k]+t[k]*(v[k+1]-v[k]);out.append({'a':r['name'],'b':q['name'],'segment_a':j,'segment_b':int(k),'distance':float(ds[k]),'radius_sum':rad,'point_a':pa.tolist(),'point_b':pb.tolist(),'new_route_pair':r['name']in changed or q['name']in changed})
(Q/'manual_rope_pairs.json').write_text(json.dumps({'scope':'All 500 static author-pose rope capsule pairs. Closest witnesses retained; contacts are not automatically labeled legal or exempted by endpoint distance. This is not a full independent-angle proof.','contacts':out},ensure_ascii=False,indent=2),encoding='utf8');print('contacts',len(out),'new route pairs',len([x for x in out if x['new_route_pair']]));print(json.dumps([x for x in out if x['new_route_pair']],ensure_ascii=True))
