from clearance import *
def ring(center,normal,floor):
 c=np.array(center);nn=np.array(normal);nn/=np.linalg.norm(nn);out=[]
 for x in np.arange(-3,3,.5):
  for y in np.arange(-3,3,.5):
   for z in np.arange(-3,3,.5):
    q=np.array([x+.25,y+.25,z+.25]);ax=q@nn;rad=np.linalg.norm(q-ax*nn)
    if abs(ax)<.4 and 1.5<=rad<=2.5:out.append(c+[x,y,z])
 for x in [-.5,0]:
  for y in [-.5,0]:
   for z in np.arange(floor,c[2]-2,.5):out.append([c[0]+x,c[1]+y,z])
 return np.unique(out,axis=0)
def gunprototype():
 allc=[];C=np.array([0,0,11.5]);anchors={}
 for dx,suffix in [(-1,'aft'),(1,'fwd')]:
  A=C+[dx*2,-3.5,0];B=C+[dx*9,-3.5,0];inc=A-C;out=B-A;na=inc/np.linalg.norm(inc)+out/np.linalg.norm(out);nb=np.array([dx,1,-.1]);
  for code,q,nn in [('a',A,na),('b',B,nb)]:allc.extend(ring(q,nn,0));anchors[code+'-'+suffix]=q.tolist()
 # A common sole plate joins all four posts and rests face-to-face on the deck.
 for x in np.arange(-10,10,.5):
  for y in np.arange(-4.5,-2.5,.5):allc.append([x,y,0])
 return np.unique(allc,axis=0),anchors
def connected(cells):
 ss={tuple(np.rint(x*2).astype(int)) for x in cells};remaining=set(ss);sizes=[]
 while remaining:
  root=remaining.pop();stack=[root];sz=0
  while stack:
   q=stack.pop();sz+=1
   for ax in range(3):
    for d in [-1,1]:
     qq=list(q);qq[ax]+=d;qq=tuple(qq)
     if qq in remaining:remaining.remove(qq);stack.append(qq)
  sizes.append(sz)
 return sorted(sizes,reverse=True)
if __name__=='__main__':
 local,anchors=gunprototype();pieces=connected(local);out=[];alls=[]
 for rr in json.loads((P/'route_clearance.json').read_text(encoding='utf8')):
  m=mods[rr['model']];C=np.array(m['points']['cascabel']);sg=np.sign(m['points']['muzzle'][1]-m['points']['breech'][1]);world=local.copy()
  if sg<0:world[:,:2]=-world[:,:2]-.5
  world+=C-[0,0,11.5];out.append({'name':rr['rope'],'route':rr['route'],'cells':world.tolist()});alls.extend(world)
 cells=np.unique(alls,axis=0);tree2=cKDTree(cells+.25);minimum=1e9;bad=[]
 for rr in out:
  pts=np.array(rr['route'])
  for si,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
   cc=cells[tree2.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+.6831))]
   if not len(cc):continue
   dd,tt=boxdist(a*2,b*2,cc*2);minimum=min(minimum,float(dd.min()**.5/2))
   if dd.min()<.5**2-1e-10:bad.append({'rope':rr['name'],'segment':si,'distance':float(dd.min()**.5/2)})
 offset=np.array([12,6,0]);vox=(local+offset)*2
 (P/'gun_fairlead.vox.txt').write_text(''.join(f'{int(round(x))},{int(round(y))},{int(round(z))},36\n'for x,y,z in vox))
 report={'source_meters_per_voxel':.05,'target_scale':.5,'source_pivot':[24,12,23],'anchors':{k:((np.array(v)+offset)*2).tolist()for k,v in anchors.items()},'placement':'at target cascabel; P mirror geometry Y, source own variant required or rotate180 and swap aft/fwd anchor labels','source_voxels':len(local),'connected_components':pieces,'minimum_rope_surface_distance':minimum,'defects':bad,'local_cells':local.tolist()}
 (P/'gun_prototype.json').write_text(json.dumps(report,indent=2));np.save(P/'support_world.npy',cells);print('sourcevoxels',len(local),'components',pieces,'min rope clearance',minimum,'bad',len(bad))
