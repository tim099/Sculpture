from audit import *
import base64,collections
src=P.parent/'cloth_verifier/phys_trajectory.jsonl';out=[];st=time.time();S=R['sails'];top=[]
for s in S:
 n=len(s['verts'])//6;tr=np.array(s['tris']).reshape(-1,3);top.append(tr[np.all(tr<n,axis=1)])
for fi,line in enumerate(src.open()):
 f=json.loads(line);contacts=[]
 for sk,fine in enumerate(f['fine']):
  if fine is None:continue
  v=np.array(fine).reshape(-1,3);tr=v[top[sk]];lo=v.min(axis=0);hi=v.max(axis=0);tlo=tr.min(axis=1);thi=tr.max(axis=1)
  for ri,p0 in enumerate(f['ropes']):
   p=np.array(p0).reshape(-1,3)
   if np.any(p.max(axis=0)<lo) or np.any(p.min(axis=0)>hi):continue
   acc=0
   for a,b in zip(p[:-1],p[1:]):
    L=float(np.linalg.norm(b-a));ix=np.flatnonzero(np.all((thi>=np.minimum(a,b))&(tlo<=np.maximum(a,b)),axis=1));tri=tr[ix]
    if not len(ix):acc+=L;continue
    e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];d=b-a;h=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);good=np.abs(det)>1e-10;ff=np.divide(1,det,out=np.zeros_like(det),where=good);ss=a-tri[:,0];u=ff*np.einsum('ij,ij->i',ss,h);q=np.cross(ss,e1);w=ff*(q@d);t=ff*np.einsum('ij,ij->i',e2,q);good&=(u>=0)&(w>=0)&(u+w<=1)&(t>=0)&(t<=1)
    for j in np.flatnonzero(good):
     alpha=255;tx=S[sk].get('texture');uv=None
     if tx and tx.get('rgba'):
      vt=np.array(tx['uv']).reshape(-1,2)[top[sk][ix[j]]];uv=vt[0]*(1-u[j]-w[j])+vt[1]*u[j]+vt[2]*w[j];x=min(tx['w']-1,max(0,int(uv[0]*tx['w'])));y=min(tx['h']-1,max(0,int(uv[1]*tx['h'])));alpha=base64.b64decode(tx['rgba'])[(y*tx['w']+x)*4+3]
      if alpha<tx.get('alpha_min',1):continue
     ar=acc+float(t[j])*L;total=float(np.sum(np.linalg.norm(np.diff(p,axis=0),axis=1)));contacts.append({'rope':R['ropes'][ri]['name'],'sail':S[sk]['name'],'tri':int(ix[j]),'point':(a+t[j]*(b-a)).tolist(),'arc':ar,'end_distance':min(ar,total-ar),'bary':[float(1-u[j]-w[j]),float(u[j]),float(w[j])],'alpha':alpha})
    acc+=L
 if contacts:out.append({'time':f['time'],'contacts':contacts})
 if fi%50==0:print(fi,round(time.time()-st,1),len(out),flush=True)
(P/'rope_cloth.json').write_text(json.dumps({'source':str(src),'source_sha256':sha(src.read_bytes()),'frames':fi+1,'elapsed_s':time.time()-st,'results':out},indent=2));print('DONE',len(out),flush=True)
