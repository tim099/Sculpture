import supplement as a
import numpy as np,json
from scipy.spatial import cKDTree
V=np.array(list(a.solid),float);cent=V+.5;tree=cKDTree(cent)
p=np.array([111.5,120.5,74.5]);dist=np.linalg.norm(np.maximum(np.maximum(V-p,p-(V+1)),0),axis=1);ix=np.argsort(dist)[:8]
result={'stock_top':p.tolist(),'nearest_cube_distance':float(dist[ix[0]]),'nearest_cubes':[{'voxel':V[i].astype(int).tolist(),'distance':float(dist[i])} for i in ix]}
axis=np.array([-.2983,0,.9545]);axis/=np.linalg.norm(axis);hinge=np.array([135,120.5,0]);samples=[]
for z in [6,20,30,40,52,60,70,74.5]:
 p=hinge+axis*(z/axis[2]);d=np.linalg.norm(np.maximum(np.maximum(V-p,p-(V+1)),0),axis=1);i=int(np.argmin(d));samples.append({'z':z,'axis_point':p.tolist(),'nearest_static_cube':V[i].astype(int).tolist(),'distance':float(d[i])})
result['axis_sections']=samples
rud=np.array(list(a.rud),float);d,inds=tree.query(rud+.5,k=8);candidates=V[inds];gaps=np.maximum(abs((rud+.5)[:,None,:]-(candidates+.5))-1,0);ds=np.linalg.norm(gaps,axis=2);i,j=np.unravel_index(np.argmin(ds),ds.shape)
result['global_rudder_static_min_cube_gap']={'distance':float(ds[i,j]),'rudder_voxel':rud[i].astype(int).tolist(),'static_voxel':candidates[i,j].astype(int).tolist(),'method':'k8 nearest-center broad phase on unit axis-aligned grid; global min of resulting exact cube distances'}
(a.O/'rudder_support.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
