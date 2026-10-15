from static import *
from scipy.optimize import minimize_scalar
Q=pathlib.Path(__file__).parent
records=json.loads((Q/'static.json').read_text(encoding='utf8'));picked=[x for x in records if x['option']=='main-truck'or x['option']=='truck-to-truck'];picked.append({'name':'jib.sheet-S','option':'bulwark-visible-595','points':[rop['jib.sheet-S']['pts'][:3],[595.5,140.5,158.5]],'radius':.2})
Y=[m for m in A['models']if m['meta'].get('kind')=='yard'];N=[]
for m in A['models']:
 me=A['meshes'][m['mesh']];vs=np.array(me['verts']).reshape(-1,3)+m['origin'];N.append((m,vs[np.array(me['tris']).reshape(-1,3)]))
def rot(pp,piv,t):
 pp=np.array(pp)-piv;c=np.cos(t);s=np.sin(t);q=pp.copy();q[...,0]=pp[...,0]*c-pp[...,1]*s;q[...,1]=pp[...,0]*s+pp[...,1]*c;return q+piv
out=[]
for rr in picked:
 pp=np.array(rr['points']);rad=rr['radius'];own=next((m for m in Y if rr['name'].startswith(m['meta'].get('sail','?')+'.brace-')),None);pivot=np.array(own['points']['pivot'])if own else None
 # Positions are transformed through full square-yard absolute-angle [-.7,.7],
 # subtracting source authored rotation -18 degrees.
 angles=np.linspace(-.7,.7,57)if own else [None];hits=[];pairmins=[]
 for theta in angles:
  pts=pp.copy()
  if own:pts[0]=rot(pp[:1],pivot,theta-(-18*np.pi/180))[0]
  a,b=pts;L=np.linalg.norm(b-a)
  cc=BODY[tree.query_ball_point((a+b)/2,float(L/2+.8661+rad))];ds,t=boxdist(a,b,cc);mask=(ds<rad*rad-1e-9)&(t>.03)&(t<.97)
  if np.any(mask):hits.append({'type':'body-mid','angle':theta,'cells':cc[mask].tolist()})
  for m,tr in N:
   if m['meta'].get('kind')=='yard':continue
   bb=np.array(m['bbox'])
   if np.any(np.maximum(a,b)+rad<bb[:3])or np.any(np.minimum(a,b)-rad>bb[3:]):continue
   ds=segtri(a,b,tr)
   if ds.min()<rad*rad-1e-9:hits.append({'type':'fixed-model','model':m['name'],'angle':theta,'distance':float(ds.min()**.5)})
  for y in Y:
   if own and y['name']==own['name']:continue
   me=A['meshes'][y['mesh']];vs=np.array(me['verts']).reshape(-1,3)+y['origin'];tr0=vs[np.array(me['tris']).reshape(-1,3)];piv=np.array(y['points']['pivot']);limit=1.4 if y['meta'].get('yard')in ['gaff','boom']else .7
   if np.max([a[2],b[2]])+rad<y['bbox'][2]or np.min([a[2],b[2]])-rad>y['bbox'][5]:continue
   # Every source angle independently sampled; no synchronous-yard assumption.
   for otherangle in np.linspace(-limit,limit,29):
    offset=otherangle-(0 if limit==1.4 else -18*np.pi/180);ab=rot(np.array([a,b]),piv,-offset);ds=segtri(ab[0],ab[1],tr0)
    if ds.min()<rad*rad-1e-9:hits.append({'type':'yard','model':y['name'],'own_angle':theta,'other_angle':otherangle,'distance':float(ds.min()**.5)})
 out.append({'name':rr['name'],'option':rr['option'],'points':rr['points'],'radius':rad,'own_yard':own['name']if own else None,'sampled_failures':hits})
 print(rr['name'],'failures',len(hits),json.dumps(hits[:2],ensure_ascii=True),flush=True)
(Q/'sweep.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
