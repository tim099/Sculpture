import pathlib,json,zlib,struct,hashlib
import numpy as np
P=pathlib.Path(__file__).parent
b=(P/'input.vxk').read_bytes();raw=zlib.decompress(b,-15);n=struct.unpack_from('<I',raw,4)[0];H=json.loads(raw[8:8+n]);R=H['rig']
def ray(a,d,tr):
 e1=tr[:,1]-tr[:,0];e2=tr[:,2]-tr[:,0];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);ok=abs(det)>1e-9;f=np.divide(1,det,out=np.zeros_like(det),where=ok);s=a-tr[:,0];u=f*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=f*(q@d);t=f*np.einsum('ij,ij->i',e2,q);ok&=(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9);return t,ok
def inside(q,tr):
 t,ok=ray(q,np.array([1,.013733,.071923]),tr);return len(np.unique(np.round(t[ok&(t>1e-8)],7)))%2==1
def intervals(pts,tr):
 out=[];acc=0
 for si,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
  d=b-a;L=float(np.linalg.norm(d));t,ok=ray(a,d,tr);tt=np.unique(np.r_[0,t[ok&(t>0)&(t<1)],1]);tt.sort()
  for u,v in zip(tt[:-1],tt[1:]):
   q=a+d*((u+v)/2)
   if v-u>1e-7 and inside(q,tr):out.append({'segment':si,'arc':[acc+u*L,acc+v*L],'mid':q.tolist()})
  acc+=L
 return out
mods={m['name']:m for m in R['models']};out=[]
for r in R['ropes']:
 if 'breech' not in r['name'] and not r['name'].startswith('steer'):continue
 pts=np.array(r['pts']).reshape(-1,3);names={e[6:].rsplit('/',1)[0] for e in r['ends'] if e.startswith('model:')}
 for name in names:
  m=mods[name];me=R['meshes'][m['mesh']];vs=np.array(me['verts']).reshape(-1,3)+m['origin'];tr=vs[np.array(me['tris']).reshape(-1,3)];hits=intervals(pts,tr)
  for h in hits:
   h['relative_to_attachment']=(np.array(h['mid'])-(pts[0] if r['ends'][0].startswith('model:') else pts[-1])).tolist()
  out.append({'rope':r['name'],'model':name,'ends':r['ends'],'radius':r['radius'],'intervals':hits})
(P/'intervals.json').write_text(json.dumps({'sha256':hashlib.sha256(b).hexdigest(),'results':out},ensure_ascii=False,indent=2),encoding='utf8')
print('ropes',len(out),'interior intervals',sum(len(x['intervals']) for x in out))
for x in out[:2]+[x for x in out if x['rope'].startswith('steer')]:print(json.dumps(x,ensure_ascii=True))
