from dynamic import *
st=time.time();out=[]
for r in R['ropes']:
 pts=np.array(r['pts']).reshape(-1,3);acc=0;hits=[]
 for si,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
  L=float(np.linalg.norm(b-a));c=candidates(a,b,r['radius']);ds,t=box_distance(a,b,c);mask=ds<r['radius']**2-1e-10
  hits.extend({'cell':cell.tolist(),'arc':acc+float(tt)*L,'distance':float(np.sqrt(dd)),'segment':si} for cell,tt,dd in zip(c[mask],t[mask],ds[mask]));acc+=L
 out.append({'name':r['name'],'length':acc,'radius':r['radius'],'contacts':hits})
# Adversarial control penetrates a known occupied body voxel center; same query and exact metric.
c=BODY[len(BODY)//2];a=c+np.array([.2,.5,.5]);b=c+np.array([.8,.5,.5]);cc=candidates(a,b,.1);dd,tt=box_distance(a,b,cc);negative={'cell':c.tolist(),'detected':bool(np.any(dd<.01)),'min_distance':float(np.sqrt(dd.min()))};assert negative['detected']
(P/'body_radius.json').write_text(json.dumps({'elapsed_s':time.time()-st,'negative':negative,'results':out},indent=2));print('done',time.time()-st,'contacts',sum(len(r['contacts']) for r in out))
