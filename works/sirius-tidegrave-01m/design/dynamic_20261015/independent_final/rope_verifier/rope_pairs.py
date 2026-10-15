from audit import *
import collections
def closest_segments(a,b,c,d):
 u=b-a;v=d-c;w=a-c;A=u@u;B=v@u;C=np.sum(v*v,axis=1);D=w@u;E=np.sum(v*w,axis=1);den=A*C-B*B;s=np.divide(B*E-C*D,den,out=np.zeros(len(c)),where=np.abs(den)>1e-18);s=np.clip(s,0,1);t=np.clip(np.divide(B*s+E,C,out=np.zeros(len(c)),where=C>0),0,1);s=np.clip((B*t-D)/(A or 1),0,1);t=np.clip(np.divide(B*s+E,C,out=np.zeros(len(c)),where=C>0),0,1);ds=np.sum((w+s[:,None]*u-t[:,None]*v)**2,axis=1);return ds,s,t
def contacts(ropes):
 pts=[np.array(x).reshape(-1,3) for x in ropes];lo=np.array([p.min(axis=0) for p in pts]);hi=np.array([p.max(axis=0) for p in pts]);rads=np.array([r['radius'] for r in R['ropes']]);out=[]
 for i,p in enumerate(pts):
  L=np.linalg.norm(np.diff(p,axis=0),axis=1);acc=np.r_[0,np.cumsum(L)]
  for j in np.where(np.all((hi+rads[:,None]+rads[i]>=lo[i])&(lo-rads[:,None]-rads[i]<=hi[i]),axis=1))[0]:
   if j<=i:continue
   q=pts[j];lens=np.linalg.norm(np.diff(q,axis=0),axis=1);acq=np.r_[0,np.cumsum(lens)];bound=rads[i]+rads[j];best=None
   qlo=np.minimum(q[:-1],q[1:]);qhi=np.maximum(q[:-1],q[1:])
   for k,(a,b) in enumerate(zip(p[:-1],p[1:])):
    ix=np.flatnonzero(np.all((qhi+bound>=np.minimum(a,b))&(qlo-bound<=np.maximum(a,b)),axis=1));
    if not len(ix):continue
    ds,s,t=closest_segments(a,b,q[ix],q[ix+1]);ok=ds<bound*bound-1e-9
    for x,dd,ss,tt in zip(ix[ok],ds[ok],s[ok],t[ok]):
     ar=float(acc[k]+ss*L[k]);br=float(acq[x]+tt*lens[x]);point=(a+ss*(b-a)).tolist();nea=min(ar,acc[-1]-ar);neb=min(br,acq[-1]-br)
     kind='shared_end_or_endpoint_knot' if nea<bound+1e-5 and neb<bound+1e-5 else 'endpoint_to_line_lashing' if min(nea,neb)<bound+1e-5 else 'interior_crossing_requires_context'
     rec={'a':R['ropes'][i]['name'],'b':R['ropes'][j]['name'],'distance':float(np.sqrt(dd)),'arc_a':ar,'arc_b':br,'end_distance_a':float(nea),'end_distance_b':float(neb),'point':point,'class':kind}
     if best is None or dd<best['distance']**2:best=rec
   if best:out.append(best)
 return out
if __name__=='__main__':
 st=time.time();out={'static':contacts([r['pts'] for r in R['ropes']]),'dynamic':[]};D=json.loads((P/'trajectory.json').read_text())
 for ti in [5,10,20,30,40,55,70,85,100,115,124]:
  f=min(D['frames'],key=lambda f:abs(f['time']-ti));out['dynamic'].append({'time':f['time'],'contacts':contacts(f['ropes'])});print(ti,len(out['dynamic'][-1]['contacts']),round(time.time()-st,1),flush=True)
 out['elapsed_s']=time.time()-st;(P/'rope_pairs.json').write_text(json.dumps(out,indent=2))
