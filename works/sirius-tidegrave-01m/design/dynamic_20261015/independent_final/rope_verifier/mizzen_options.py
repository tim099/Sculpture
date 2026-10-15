from dynamic import *
from triangle_distance import seg_tri_distance
out=[];ropes=[]
for side,sgn in [('P',-1),('S',1)]:
 parents=[]
 for i,(x,dy) in enumerate(zip([125.5,140.5,155.5],[18,21,24])):
  old=next(r for r in R['ropes'] if r['name']==f'mizzen-shroud-{side}{i}');a=np.array([x,120.5+sgn*dy,185.5]);b=np.array(old['pts'][-3:]);parents.append((a,b));ropes.append((old['name'],a,b,.4))
 for k in range(1,22):
  t=k*.04;a=parents[0][0]*(1-t)+parents[0][1]*t;b=parents[2][0]*(1-t)+parents[2][1]*t;ropes.append((f'mizzen-ratline-{side}-{k}',a,b,.2))
for name,a,b,radius in ropes:
 c=candidates(a,b,radius);ds,t=box_distance(a,b,c);hit=ds<radius*radius-1e-10;body=[{'cell':cc.tolist(),'t':float(tt),'point':(a+tt*(b-a)).tolist()} for cc,tt in zip(c[hit],t[hit])];yards=[]
 for m in R['models']:
  if m.get('meta',{}).get('kind')!='yard':continue
  bb=np.array(m['bbox']);
  if min(a[2],b[2])-radius>bb[5] or max(a[2],b[2])+radius<bb[2]:continue
  me=R['meshes'][m['mesh']];v=np.array(me['verts']).reshape(-1,3)+m['origin'];tr=v[np.array(me['tris']).reshape(-1,3)];r0=m.get('meta',{}).get('rotate_z_deg',0)*np.pi/180
  for angle in np.linspace(-.7-r0,.7-r0,141):
   aa,bb=rot(np.array([a,b]),m['points']['pivot'],-angle);sel=np.all((np.max(tr,axis=1)+radius>=np.minimum(aa,bb))&(np.min(tr,axis=1)-radius<=np.maximum(aa,bb)),axis=1);d=seg_tri_distance(aa,bb,tr[sel]);
   if len(d) and d.min()<radius*radius-1e-10:yards.append({'yard':m['name'],'rot':float(angle),'distance':float(np.sqrt(d.min()))});break
 out.append({'name':name,'a':a.tolist(),'b':b.tolist(),'body':body,'yards':yards})
 if body or yards:print(name,'body',body,'yards',yards,flush=True)
(P/'mizzen_options.json').write_text(json.dumps(out,indent=2));print('DONE',len(out),flush=True)
