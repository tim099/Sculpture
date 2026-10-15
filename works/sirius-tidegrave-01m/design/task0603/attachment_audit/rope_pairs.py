from clearance import *
def segseg(a,b,c,d):
 u=b-a;v=d-c;w=a-c;A=u@u;B=u@v;C=v@v;D=u@w;E=v@w;den=A*C-B*B;s=np.clip((B*E-C*D)/den if abs(den)>1e-14 else 0,0,1);t=np.clip((B*s+E)/C if C else 0,0,1);s=np.clip((B*t-D)/A if A else 0,0,1);t=np.clip((B*s+E)/C if C else 0,0,1);return float(np.linalg.norm(w+s*u-t*v)),float(s),float(t)
new=json.loads((P/'route_clearance.json').read_text(encoding='utf8'));ww=json.loads((P/'wheel_route.json').read_text(encoding='utf8'));new.append({'rope':'steer-wheel-S','route':ww['route']});newnames={x['rope']for x in new};lines=[]
for r in R['ropes']:
 if r['name']in newnames:continue
 lines.append({'name':r['name'],'points':np.array(r['pts']).reshape(-1,3),'radius':r['radius'],'new':False})
for r in new:lines.append({'name':r['rope'],'points':np.array(r['route']),'radius':.25,'new':True})
contacts=[]
for i,r in enumerate(lines):
 for q in lines[i+1:]:
  if not r['new']and not q['new']:continue
  p=r['points'];v=q['points'];rad=r['radius']+q['radius']
  if np.any(p.max(axis=0)+rad<v.min(axis=0))or np.any(v.max(axis=0)+rad<p.min(axis=0)):continue
  for si,(a,b)in enumerate(zip(p[:-1],p[1:])):
   for sj,(c,d)in enumerate(zip(v[:-1],v[1:])):
    if np.any(np.maximum(a,b)+rad<np.minimum(c,d))or np.any(np.maximum(c,d)+rad<np.minimum(a,b)):continue
    dist,s,t=segseg(a,b,c,d)
    if dist<rad-1e-8:contacts.append({'a':r['name'],'b':q['name'],'segment_a':si,'segment_b':sj,'distance':dist,'point_a':(a+s*(b-a)).tolist(),'point_b':(c+t*(d-c)).tolist(),'same_gun_cascabel':'.breech-'in r['name']and'.breech-'in q['name']and r['name'].split('.breech-')[0]==q['name'].split('.breech-')[0]})
for x in contacts:
 x['same_named_steering_lead_joint']=bool(set([x['a'],x['b']])==set(['steer-lead-S','steer-wheel-S'])and np.linalg.norm(np.array(x['point_a'])-[175.5,134.5,135.5])<1e-10 and np.linalg.norm(np.array(x['point_b'])-[175.5,134.5,135.5])<1e-10)
bad=[x for x in contacts if not x['same_gun_cascabel'] and not x['same_named_steering_lead_joint']];(P/'route_pairs.json').write_text(json.dumps({'contacts':contacts,'defects':bad},ensure_ascii=False,indent=2),encoding='utf8');print('contacts',len(contacts),'same gun',sum(x['same_gun_cascabel']for x in contacts),'same named steering joint',sum(x['same_named_steering_lead_joint']for x in contacts),'defects',len(bad));print(json.dumps(bad[:5],ensure_ascii=True))
