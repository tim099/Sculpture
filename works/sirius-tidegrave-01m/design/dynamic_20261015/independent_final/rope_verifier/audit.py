import pathlib,json,zlib,struct,hashlib,shutil,time,os
import numpy as np
from scipy.spatial import cKDTree
P=pathlib.Path(os.environ.get('ROPE_OUTPUT',pathlib.Path(__file__).parent));P.mkdir(exist_ok=True)
SRC=pathlib.Path('D:/Unity/Valhalla')
def sha(b):return hashlib.sha256(b).hexdigest()
def freeze():
 files=[SRC/'Sculpture/works/sirius-tidegrave-01m/design/continued_20261015/final_heads.vxk']+list((SRC/'Blockside/src/js').glob('*.js'))+[SRC/'Blockside/VoxelKit/voxelkit.js']
 (P/'frozen').mkdir(exist_ok=True); manifest=[]
 for f in files:
  b=f.read_bytes();(P/'frozen'/f.name).write_bytes(b);manifest.append({'source':str(f),'file':f.name,'sha256':sha(b)})
 (P/'provenance.json').write_text(json.dumps(manifest,indent=2))
if not (P/'provenance.json').exists():freeze()
b=(P/'frozen'/os.environ.get('ROPE_VXK','final_heads.vxk')).read_bytes();INPUT_SHA=sha(b);raw=zlib.decompress(b,-15);hn=struct.unpack_from('<I',raw,4)[0];H=json.loads(raw[8:8+hn]);R=H['rig'];off=8+hn;nc=H['nchunks'];keys=np.frombuffer(raw,dtype='<u2',count=nc*3,offset=off).reshape(-1,3);off+=nc*6
cells=[]
for k,key in enumerate(keys):
 a=np.frombuffer(raw,dtype='u1',count=4096,offset=off+k*4096);ii=np.flatnonzero(a);cells.append(np.column_stack((ii%16,ii//16%16,ii//256))+key*16)
BODY=np.concatenate(cells).astype(float)
TREE=cKDTree(BODY+.5)
def candidates(a,b,r=0):
 ix=TREE.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+.866026+r));c=BODY[ix];return c[np.all((c+1+r>=np.minimum(a,b))&(c-r<=np.maximum(a,b)),axis=1)]
def segment_boxes(a,b,lo,hi):
 d=b-a; t0=np.zeros(len(lo));t1=np.ones(len(lo))
 for j in range(3):
  if abs(d[j])<1e-14:
   ok=(a[j]>=lo[:,j])&(a[j]<=hi[:,j]);t1[~ok]=-1
  else:
   u=(lo[:,j]-a[j])/d[j];v=(hi[:,j]-a[j])/d[j];t0=np.maximum(t0,np.minimum(u,v));t1=np.minimum(t1,np.maximum(u,v))
 return t0,t1,t1>=t0
def seg_tri(a,b,tri):
 e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];d=b-a;h=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);good=np.abs(det)>1e-10;f=np.divide(1,det,out=np.zeros_like(det),where=good);s=a-tri[:,0];u=f*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=f*(q@d);t=f*np.einsum('ij,ij->i',e2,q);good&=(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(t>=0)&(t<=1);return t[good]
def static():
 start=time.time();result=[];models=[]
 for m in R['models']:
  mesh=R['meshes'][m['mesh']];v=np.array(mesh['verts']).reshape(-1,3)+m['origin'];models.append(v[np.array(mesh['tris']).reshape(-1,3)])
 for r in R['ropes']:
  pts=np.array(r['pts']).reshape(-1,3);acc=0;body=[];mods=[]
  for a,b in zip(pts[:-1],pts[1:]):
   L=float(np.linalg.norm(b-a));c=candidates(a,b)
   t0,t1,hit=segment_boxes(a,b,c,c+1)
   for cell,u,v in zip(c[hit],t0[hit],t1[hit]):body.append({'cell':cell.tolist(),'arc':[acc+L*u,acc+L*v]})
   for m,tr in zip(R['models'],models):
    bb=np.array(m['bbox']);
    if np.any(np.maximum(a,b)<bb[:3]) or np.any(np.minimum(a,b)>bb[3:]):continue
    t=seg_tri(a,b,tr)
    if len(t):mods.append({'model':m['name'],'arc':sorted(set(np.round(acc+L*t,7).tolist()))})
   acc+=L
  result.append({'name':r['name'],'length':acc,'body_centerline':body,'model_surface_centerline':mods})
  if len(result)%50==0:print('progress',len(result),flush=True)
 (P/'static.json').write_text(json.dumps({'vxk_sha256':INPUT_SHA,'body_cells':len(BODY),'ropes':len(result),'models':len(models),'elapsed_s':time.time()-start,'results':result},indent=2))
 print('STATIC',time.time()-start,[(x['name'],len(x['body_centerline']),len(x['model_surface_centerline'])) for x in result if x['body_centerline'] or x['model_surface_centerline']],flush=True)
if __name__=='__main__':static()
