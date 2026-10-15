from clearance import *
routes=json.loads((P/'route_clearance.json').read_text(encoding='utf8'));wheel=json.loads((P/'wheel_route.json').read_text(encoding='utf8'))
spec=[]
for rr in routes:
 pp=np.array(rr['route']);m=mods[rr['model']];floor=m['bbox'][2]
 for i in [1,2]:spec.append({'rope':rr['rope'],'corner':i,'center':pp[i].tolist(),'incoming':(pp[i]-pp[i-1]).tolist(),'outgoing':(pp[i+1]-pp[i]).tolist(),'floor_z':floor})
pp=np.array(wheel['route'])
for i,floor in [(1,151),(2,139)]:spec.append({'rope':'steer-wheel-S','corner':i,'center':pp[i].tolist(),'incoming':(pp[i]-pp[i-1]).tolist(),'outgoing':(pp[i+1]-pp[i]).tolist(),'floor_z':floor})
allcells=[];minclear=1e9;defects=[]
for s in spec:
 c=np.array(s['center']);inc=np.array(s['incoming']);out=np.array(s['outgoing']);nn=inc/np.linalg.norm(inc)+out/np.linalg.norm(out);nn/=np.linalg.norm(nn);loc=[]
 # 0.05m source cells = half a ship grid unit. Shell chosen by voxel centers,
 # every resulting solid cube then checked against adjacent rope capsules.
 for x in np.arange(-2.5,2.5,.5):
  for y in np.arange(-2.5,2.5,.5):
   for z in np.arange(-2.5,2.5,.5):
    q=np.array([x+.25,y+.25,z+.25]);ax=q@nn;rad=np.linalg.norm(q-ax*nn)
    if abs(ax)<.4 and 1.7<=rad<=2.25:loc.append(c+[x,y,z])
 for x in [-.5,0]:
  for y in [-.5,0]:
   for z in np.arange(s['floor_z'],c[2]-2,.5):loc.append(np.array([c[0]+x,c[1]+y,z]))
 cells=np.unique(loc,axis=0);s['normal']=nn.tolist();s['cells_lo']=cells.tolist();allcells.extend(cells)
 # boxdist uses unit cubes, scale coordinates by 2 for half-grid cubes.
 rr=next((r for r in routes if r['rope']==s['rope']),wheel);pp=np.array(rr['route']);near=[]
 for i,(a,b) in enumerate(zip(pp[:-1],pp[1:])):
  dd,tt=boxdist(a*2,b*2,cells*2);d=float(dd.min()**.5/2);minclear=min(minclear,d)
  if d<.25-1e-8:near.append({'segment':i,'distance':d,'cell':cells[int(dd.argmin())].tolist()})
 if near:defects.append({'rope':s['rope'],'corner':s['corner'],'hits':near})
(P/'fairlead_spec.json').write_text(json.dumps({'scale_ship_grid':.5,'minimum_rope_clearance':minclear,'defects':defects,'supports':spec},ensure_ascii=False,indent=2),encoding='utf8')
print('supports',len(spec),'cells',len(allcells),'min rope clearance',minclear,'defects',len(defects));print(json.dumps(defects[:3],ensure_ascii=True))
