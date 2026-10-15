from pathlib import Path
import numpy as np,json,zlib,struct,math,time
ROOT=Path(__file__).resolve().parent;src=ROOT.parent/'input';raw=zlib.decompress((src/'final_heads.vxk').read_bytes(),-15);n=struct.unpack_from('<I',raw,4)[0];h=json.loads(raw[8:8+n]);p=8+n;nc=h['nchunks'];keys=np.frombuffer(raw,dtype='<u2',count=nc*3,offset=p).reshape(-1,3);p+=nc*6
body=[]
for k,dat in zip(keys,np.frombuffer(raw,dtype='u1',offset=p).reshape(nc,4096)):
 ids=np.flatnonzero(dat);body.extend(np.c_[ids%16,ids//16%16,ids//256]+k*16)
body=np.array(body);bs=set(map(tuple,body));yards=json.loads((src/'independent/frozen_yards.json').read_text())['yards']
def dist(a,b,lo,hi):
 # Exact segment/AABB minimizer. Breakpoints where each segment coordinate crosses each box plane; stationary root on each resulting quadratic interval.
 d=b-a;ts=[0.,1.]
 for ax in range(3):
  if abs(d[ax])>1e-15:ts.extend([float(np.clip((lo[ax]-a[ax])/d[ax],0,1)),float(np.clip((hi[ax]-a[ax])/d[ax],0,1))])
 ts=sorted(set(ts));best=(float('inf'),0.)
 for l,r in zip(ts,ts[1:]):
  m=(l+r)/2;q=a+m*d;target=np.where(q<lo,lo,np.where(q>hi,hi,q));active=(q<lo)|(q>hi);den=float(np.dot(d[active],d[active]));t=float(np.clip(-np.dot((a-target)[active],d[active])/den,l,r)) if den else m
  v=a+t*d;delta=np.maximum(lo-v,0)+np.maximum(v-hi,0);ds=float(np.linalg.norm(delta))
  if ds<best[0]:best=(ds,t)
 return best
def boxes(y):
 c=np.array(y['cubes']);groups={}
 for x,yy,z in c:groups.setdefault((x,z),[]).append(yy)
 out=[]
 for (x,z),ys in groups.items():
  ys=sorted(ys);a=b=ys[0]
  for yy in ys[1:]+[float('inf')]:
   if yy!=b+1:out.append((np.array([x,a,z]),np.array([x+1,b+1,z+1])));a=yy
   b=yy
 return out
ropes=[];feet=[]
for side,hy in [('P',116.5),('S',124.5)]:
 fs=[]
 for x in [290,310,330]:
  ys=body[(body[:,0]==x)&(body[:,2]==128),1]; yy=ys.min() if side=='P' else ys.max();fs.append(np.array([x+.5,yy+.5,128.5]))
 head=np.array([205.5,hy,260.5])
 for i,f in enumerate(fs):
  feet.append({'side':side,'index':i,'point':f.tolist(),'solid':tuple(np.floor(f).astype(int)) in bs});ropes.append((f'mizzen-shroud-{side}{i}',f,head,.4))
 for j in range(1,22):ropes.append((f'mizzen-ratline-{side}-{j}',fs[0]+j/25*(head-fs[0]),fs[2]+j/25*(head-fs[2]),.125))
print('FEET',feet,flush=True)
results=[];stats={'intervals':0,'clear_leaves':0,'unresolved':0}
def yrcheck(a,b,rad,y,lo,hi,l,r,depth=0):
 stats['intervals']+=1;pv=np.array(y['piv']);at=np.array(y['at']);ang=(l+r)/2;co=math.cos(ang);si=math.sin(ang);mat=np.array([[co,-si,0],[si,co,0],[0,0,1]])
 aa=(a-at)@mat+pv;bb=(b-at)@mat+pv;dd,t=dist(aa,bb,lo,hi);rr=max(math.hypot(x-pv[0],yy-pv[1]) for x in (lo[0],hi[0]) for yy in (lo[1],hi[1]));err=rr*(r-l)/2
 if dd>rad+err+1e-9:stats['clear_leaves']+=1;return None
 if dd<rad-1e-8:return {'angle':ang,'distance':dd,'rope_t':t,'rope_point':(a+t*(b-a)).tolist(),'source_box':[lo.tolist(),hi.tolist()]}
 if depth>=22:stats['unresolved']+=1;return {'unresolved':[l,r],'distance':dd,'error':err}
 return yrcheck(a,b,rad,y,lo,hi,l,ang,depth+1) or yrcheck(a,b,rad,y,lo,hi,ang,r,depth+1)
for name,a,b,rad in ropes:
 out={'name':name,'a':a.tolist(),'b':b.tolist(),'radius':rad,'body_contacts':[],'yard_contacts':[]};mn=np.minimum(a,b)-rad;mx=np.maximum(a,b)+rad
 cand=body[np.all(body+1>=mn,axis=1)&np.all(body<=mx,axis=1)]
 for v in cand:
  dd,t=dist(a,b,v,v+1)
  if dd<rad-1e-8:
   enddist=min(t,1-t)*np.linalg.norm(b-a);out['body_contacts'].append({'cell':v.tolist(),'distance':dd,'rope_t':t,'point':(a+t*(b-a)).tolist(),'endpoint_arclength':enddist,'attachment_candidate':name.startswith('mizzen-shroud-') and bool(enddist<=1.0)})
 for y in yards:
  lim=1.4 if y['meta']['yard'] in ('boom','gaff') else .7;pv=np.array(y['piv']);at=np.array(y['at'])
  for lo,hi in boxes(y):
   z0=lo[2]-pv[2]+at[2];z1=hi[2]-pv[2]+at[2]
   if z0>mx[2] or z1<mn[2]:continue
   hit=yrcheck(a,b,rad,y,lo,hi,-lim,lim)
   if hit:out['yard_contacts'].append({'yard':y['name'],**hit});break
 results.append(out);(ROOT/'progress.json').write_text(json.dumps({'feet':feet,'results':results,'stats':stats},indent=2));print(name,'body',len(out['body_contacts']),'yard',len(out['yard_contacts']),flush=True)
(ROOT/'report.json').write_text(json.dumps({'feet':feet,'results':results,'stats':stats},indent=2));print('DONE',stats,flush=True)

