from audit import *
from scipy.spatial import cKDTree
# Exact segment/cube distance (independent rope verifier's 20261015 piecewise quadratic method).
def boxdist(a,b,lo):
 hi=lo+1;d=b-a;n=len(lo);ts=[np.zeros(n),np.ones(n)]
 for j in range(3):
  if abs(d[j])>1e-15:ts.extend([np.clip((lo[:,j]-a[j])/d[j],0,1),np.clip((hi[:,j]-a[j])/d[j],0,1)])
 ts=np.sort(np.array(ts).T,axis=1);best=np.full(n,np.inf);bt=np.zeros(n)
 for l,u in zip(ts[:,:-1].T,ts[:,1:].T):
  mid=(l+u)/2;p=a+mid[:,None]*d;target=np.where(p<lo,lo,np.where(p>hi,hi,p));active=(p<lo)|(p>hi);den=np.sum(active*d*d,axis=1);num=np.sum(active*d*(a-target),axis=1);t=np.clip(np.divide(-num,den,out=mid.copy(),where=den>0),l,u);q=a+t[:,None]*d;ds=np.sum(np.maximum(lo-q,np.maximum(q-hi,0))**2,axis=1);good=ds<best;best[good]=ds[good];bt[good]=t[good]
 return best,bt
def pttri(p,tr):
 a=tr[:,0];ab=tr[:,1]-a;ac=tr[:,2]-a;nn=np.cross(ab,ac);den=np.sum(nn*nn,axis=1);s=np.divide(np.sum((p-a)*nn,axis=1),den,out=np.zeros(len(tr)),where=den>0);q=p-s[:,None]*nn;v=q-a;d00=np.sum(ab*ab,axis=1);d01=np.sum(ab*ac,axis=1);d11=np.sum(ac*ac,axis=1);d20=np.sum(v*ab,axis=1);d21=np.sum(v*ac,axis=1);dd=d00*d11-d01*d01;u=np.divide(d11*d20-d01*d21,dd,out=np.zeros(len(tr)),where=dd>0);w=np.divide(d00*d21-d01*d20,dd,out=np.zeros(len(tr)),where=dd>0);best=np.where((u>=0)&(w>=0)&(u+w<=1)&(dd>0),s*s*den,np.inf)
 for j in range(3):
  x=tr[:,j];d=tr[:,(j+1)%3]-x;t=np.clip(np.divide(np.sum((p-x)*d,axis=1),np.sum(d*d,axis=1),out=np.zeros(len(tr)),where=np.sum(d*d,axis=1)>0),0,1);best=np.minimum(best,np.sum((p-x-t[:,None]*d)**2,axis=1))
 return best
def segtri(a,b,tr):
 best=np.minimum(pttri(a,tr),pttri(b,tr));u=b-a;A=u@u
 for j in range(3):
  c=tr[:,j];v=tr[:,(j+1)%3]-c;w=a-c;B=v@u;C=np.sum(v*v,axis=1);D=w@u;E=np.sum(v*w,axis=1);den=A*C-B*B;s=np.clip(np.divide(B*E-C*D,den,out=np.zeros(len(tr)),where=np.abs(den)>1e-18),0,1);t=np.clip(np.divide(B*s+E,C,out=np.zeros(len(tr)),where=C>0),0,1);s=np.clip((B*t-D)/(A or 1),0,1);t=np.clip(np.divide(B*s+E,C,out=np.zeros(len(tr)),where=C>0),0,1);best=np.minimum(best,np.sum((w+s[:,None]*u-t[:,None]*v)**2,axis=1))
 t,ok=ray(a,b-a,tr)
 if np.any(ok&(t>=0)&(t<=1)):best[0]=0
 return best
off=8+n;nc=H['nchunks'];keys=np.frombuffer(raw,dtype='<u2',count=nc*3,offset=off).reshape(-1,3);off+=nc*6;BODY=[]
for k,key in enumerate(keys):
 a=np.frombuffer(raw,dtype='u1',count=4096,offset=off+k*4096);ii=np.flatnonzero(a);BODY.append(np.column_stack((ii%16,ii//16%16,ii//256))+key*16)
BODY=np.concatenate(BODY).astype(float);tree=cKDTree(BODY+.5)
M=[]
for m in R['models']:
 me=R['meshes'][m['mesh']];v=np.array(me['verts']).reshape(-1,3)+m['origin'];M.append((m,v[np.array(me['tris']).reshape(-1,3)]))
def checkroute(points,own):
 out=[]
 for si,(a,b) in enumerate(zip(points[:-1],points[1:])):
  cc=BODY[tree.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+1.2))];dd,tt=boxdist(a,b,cc)
  if np.any(dd<.25**2-1e-9):out.extend({'kind':'body','segment':si,'cell':c.tolist(),'distance':float(d**.5),'t':float(t)}for c,d,t in zip(cc[dd<.25**2-1e-9],dd[dd<.25**2-1e-9],tt[dd<.25**2-1e-9]))
  for m,tr in M:
   bb=np.array(m['bbox']);
   if np.any(np.maximum(a,b)+.25<bb[:3])or np.any(np.minimum(a,b)-.25>bb[3:]):continue
   ds=segtri(a,b,tr)
   if ds.min()<.25**2-1e-9:out.append({'kind':'model','name':m['name'],'segment':si,'own':m['name']==own,'distance':float(ds.min()**.5),'inside':intervals(np.array([a,b]),tr)})
 return out
if __name__=='__main__':
 out=[]
 for r in R['ropes']:
  if 'breech'not in r['name']:continue
  p=np.array(r['pts']).reshape(-1,3);name=r['ends'][0][6:].rsplit('/',1)[0];m=mods[name];sg=np.sign(m['points']['muzzle'][1]-m['points']['breech'][1]);dx=np.sign(p[-1,0]-p[0,0]);points=np.array([p[0],p[0]+[dx*2,-sg*3.5,0],p[0]+[dx*9,-sg*3.5,0],p[-1]])
  out.append({'rope':r['name'],'model':name,'route':points.tolist(),'contacts':checkroute(points,name)})
 (P/'route_clearance.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('routes',len(out),'non-own-model',sum(sum(c['kind']=='model'and not c['own'] for c in x['contacts'])for x in out),'body',sum(sum(c['kind']=='body' for c in x['contacts'])for x in out),'own non initial',sum(sum(c['kind']=='model'and c['own']and c['segment']>0 for c in x['contacts'])for x in out))
