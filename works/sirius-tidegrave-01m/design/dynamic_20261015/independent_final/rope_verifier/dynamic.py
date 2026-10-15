from audit import *
import collections
def box_distance(a,b,lo):
 # Exact squared segment-to-cube distance: convex piecewise quadratic in t.
 hi=lo+1;d=b-a;n=len(lo);ts=[np.zeros(n),np.ones(n)]
 for j in range(3):
  if abs(d[j])>1e-15:ts.extend([np.clip((lo[:,j]-a[j])/d[j],0,1),np.clip((hi[:,j]-a[j])/d[j],0,1)])
 ts=np.sort(np.array(ts).T,axis=1);best=np.full(n,np.inf);bt=np.zeros(n)
 for l,u in zip(ts[:,:-1].T,ts[:,1:].T):
  mid=(l+u)/2;p=a+mid[:,None]*d;target=np.where(p<lo,lo,np.where(p>hi,hi,p));active=(p<lo)|(p>hi);den=np.sum(active*d*d,axis=1);num=np.sum(active*d*(a-target),axis=1);t=np.clip(np.divide(-num,den,out=mid.copy(),where=den>0),l,u);q=a+t[:,None]*d;diff=np.maximum(lo-q,np.maximum(q-hi,0));ds=np.sum(diff*diff,axis=1);good=ds<best;best[good]=ds[good];bt[good]=t[good]
 return best,bt
def rot(p,piv,angle):
 c=np.cos(angle);s=np.sin(angle);p=np.array(p)-piv;out=p.copy();out[:,0]=c*p[:,0]-s*p[:,1];out[:,1]=s*p[:,0]+c*p[:,1];return out+piv
def run():
 st=time.time();D=json.loads((P/'trajectory.json').read_text());bindings=json.loads((P/'bindings.json').read_text());ykeys={x['k']:j for j,x in enumerate(D['yards'])};tri=[];mbb=[]
 for m in R['models']:
  me=R['meshes'][m['mesh']];v=np.array(me['verts']).reshape(-1,3)+m['origin'];tri.append(v[np.array(me['tris']).reshape(-1,3)]);mbb.append(m['bbox'])
 mbb=np.array(mbb);seen={};records=[];moving=[j for j,b in enumerate(bindings) if b['ya']>=0 or b['yb']>=0]
 resume=int(os.environ.get('ROPE_RESUME','-1'))
 if resume>=0:
  old=json.loads((P/'dynamic_partial.json').read_text());seen={('retained',i):x for i,x in enumerate(old['contacts'])}
 # Every static rope is included against every moving yard; invariant static/static pairs are in static.json.
 for fi,frame in enumerate(D['frames']):
  if fi%5:continue # .5 sec discovery; not a continuous clearance claim.
  if fi<=resume:continue
  angles=frame['angles'];allp=frame['ropes']
  for ri,r in enumerate(R['ropes']):
   pts=np.array(allp[ri]).reshape(-1,3);acc=0
   for si,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
    L=float(np.linalg.norm(b-a))
    if ri in moving:
     c=candidates(a,b,r['radius']);ds,t=box_distance(a,b,c)
     for cell,dd,tt in zip(c[ds<r['radius']**2-1e-9],ds[ds<r['radius']**2-1e-9],t[ds<r['radius']**2-1e-9]):
      key=(ri,'body',tuple(cell));ar=acc+tt*L;rec={'rope':r['name'],'obstacle':'body','cell':cell.tolist(),'time':frame['time'],'arc':ar,'segment':si,'distance':float(np.sqrt(dd)),'point':(a+tt*(b-a)).tolist(),'near_end':min(ar,sum(np.linalg.norm(np.diff(pts,axis=0),axis=1))-ar)}
      if key not in seen or rec['near_end']>seen[key]['near_end']:seen[key]=rec
    # Existing static ropes need only moving-yard tests. Moving ropes get all models.
    ks=range(len(tri)) if ri in moving else ykeys.keys()
    for mk in ks:
     angle=angles[ykeys[mk]] if mk in ykeys else 0;m=R['models'][mk]
     ab=rot(np.array([a,b]),m['points']['pivot'],-angle) if angle else np.array([a,b]);aa,bb=ab
     if np.any(np.maximum(aa,bb)<mbb[mk,:3]) or np.any(np.minimum(aa,bb)>mbb[mk,3:]):continue
     ts=seg_tri(aa,bb,tri[mk]);
     if len(ts):
      ar=acc+float(ts[len(ts)//2])*L;key=(ri,mk,si);rec={'rope':r['name'],'obstacle':m['name'],'time':frame['time'],'arc':ar,'segment':si,'point':(a+float(ts[len(ts)//2])*(b-a)).tolist(),'intersections':sorted(set(ts.tolist())),'near_end':min(ar,sum(np.linalg.norm(np.diff(pts,axis=0),axis=1))-ar)}
      if key not in seen or rec['near_end']>seen[key]['near_end']:seen[key]=rec
    acc+=L
  if fi%100==0:
   (P/'dynamic_partial.json').write_text(json.dumps({'last_frame':fi,'elapsed_s':time.time()-st,'contacts':list(seen.values())},indent=2));print(fi,round(time.time()-st),len(seen),flush=True)
 (P/'dynamic.json').write_text(json.dumps({'elapsed_s':time.time()-st,'frame_dt':.5,'frames':249,'contacts':list(seen.values())},indent=2));print('done',time.time()-st,flush=True)
if __name__=='__main__':run()
