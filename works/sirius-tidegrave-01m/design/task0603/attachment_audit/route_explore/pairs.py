from static import *
def segseg(a,b,c,d):
 u=b-a;v=d-c;w=a-c;AA=u@u;B=u@v;CC=v@v;D=u@w;E=v@w;den=AA*CC-B*B;s=np.clip((B*E-CC*D)/den if abs(den)>1e-14 else 0,0,1);t=np.clip((B*s+E)/CC if CC else 0,0,1);s=np.clip((B*t-D)/AA if AA else 0,0,1);t=np.clip((B*s+E)/CC if CC else 0,0,1);return float(np.linalg.norm(w+s*u-t*v)),float(s),float(t)
picked=[x for x in json.loads((Q/'static.json').read_text(encoding='utf8'))if x['option']=='main-truck'or x['option']=='truck-to-truck'];picked.append({'name':'jib.sheet-S','points':[rop['jib.sheet-S']['pts'][:3],[595.5,140.5,158.5]],'radius':.2});names={x['name']for x in picked};lines=[{'name':x['name'],'points':np.array(x['pts']).reshape(-1,3),'radius':x['radius']}for x in A['ropes']if x['name']not in names]+[dict(x,points=np.array(x['points']))for x in picked];out=[]
for r in picked:
 a,b=np.array(r['points']);
 for q in lines:
  if q['name']==r['name']:continue
  p=q['points'];rad=r['radius']+q['radius']
  if np.any(p.max(axis=0)+rad<np.minimum(a,b))or np.any(p.min(axis=0)-rad>np.maximum(a,b)):continue
  for si,(c,d)in enumerate(zip(p[:-1],p[1:])):
   dist,u,v=segseg(a,b,c,d)
   if dist<rad-1e-9:out.append({'a':r['name'],'b':q['name'],'distance':dist,'u':u,'v':v,'segment_b':si,'point_a':(a+u*(b-a)).tolist(),'point_b':(c+v*(d-c)).tolist(),'shared_exact_endpoint':bool((u<1e-9 or u>1-1e-9)and(v<1e-9 or v>1-1e-9)and dist<1e-8)})
(Q/'pairs.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('contacts',len(out),'nonshared',json.dumps([x for x in out if not x['shared_exact_endpoint']],ensure_ascii=True))
