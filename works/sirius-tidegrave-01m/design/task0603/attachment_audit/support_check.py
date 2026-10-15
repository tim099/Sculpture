from clearance import *
import os
wheel_mode=os.environ.get('CHECK_WHEEL')=='1'
cells=np.concatenate([np.load(P/'wheel_fairlead_1_world.npy'),np.load(P/'wheel_fairlead_2_world.npy')]) if wheel_mode else np.load(P/'support_world.npy');tree2=cKDTree(cells+.25)
def tribox(tr,lo,size=.5):
 c=lo+size/2;v=tr-c;edges=np.roll(v,-1,axis=1)-v;axes=[np.tile(e,(len(v),1))for e in np.eye(3)];axes.append(np.cross(edges[:,0],edges[:,1]));
 for j in range(3):
  for e in np.eye(3):axes.append(np.cross(edges[:,j],e))
 hit=np.ones(len(v),bool)
 for ax in axes:
  proj=np.einsum('tvi,ti->tv',v,ax);r=size/2*np.sum(abs(ax),axis=1);valid=np.linalg.norm(ax,axis=1)>1e-12;hit&=~valid|((proj.max(axis=1)>-r+1e-9)&(proj.min(axis=1)<r-1e-9))
 return hit
bodyhits=[];modelhits=[]
for ci,lo in enumerate(cells):
 cc=BODY[tree.query_ball_point(lo+.25,1.31)]
 insidebody=cc[np.all((cc+1>lo+1e-9)&(cc<lo+.5-1e-9),axis=1)]
 if len(insidebody):bodyhits.append({'lo':lo.tolist(),'body':insidebody.tolist()})
 for m,tr in M:
  bb=np.array(m['bbox'])
  if np.any(bb[:3]>=lo+.5-1e-9)or np.any(bb[3:]<=lo+1e-9):continue
  cand=tr[np.all((tr.max(axis=1)>lo+1e-9)&(tr.min(axis=1)<lo+.5-1e-9),axis=1)]
  if np.any(tribox(cand,lo))or inside(lo+.25,tr):modelhits.append({'lo':lo.tolist(),'model':m['name']})
ropehits=[]
for r in R['ropes']:
 if 'breech'in r['name']or r['name']=='steer-wheel-S':continue
 pts=np.array(r['pts']).reshape(-1,3)
 for si,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
  cc=cells[tree2.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+.4331+r['radius']))]
  if not len(cc):continue
  dd,tt=boxdist(a*2,b*2,cc*2);mask=dd<(2*r['radius'])**2-1e-9
  if np.any(mask):ropehits.append({'rope':r['name'],'segment':si,'lo':cc[mask].tolist(),'distances':(np.sqrt(dd[mask])/2).tolist()})
# Entire sole-plate bottom must bear on real deck solid immediately below.
sole=[];bodyset={tuple(x.astype(int))for x in BODY}
for m in R['models']:
 if m['meta'].get('gun')!='24l':continue
 C=np.array(m['points']['cascabel']);floor=m['bbox'][2];near=cells[(cells[:,0]>C[0]-11)&(cells[:,0]<C[0]+11)&(abs(cells[:,2]-floor)<1e-8)]
 # Source y side differentiates overlapping gun-deck vertical stacks.
 sg=np.sign(m['points']['muzzle'][1]-m['points']['breech'][1]);near=near[((near[:,1]+.25-C[1])*sg< -2)&((near[:,1]+.25-C[1])*sg> -5)]
 missing=[q.tolist()for q in near if tuple(np.floor(q+[.25,.25,-.001]).astype(int))not in bodyset]
 sole.append({'model':m['name'],'foot_cells':len(near),'unsupported':missing})
if wheel_mode:
 sole=[]
 for i in [1,2]:
  cc=np.load(P/('wheel_fairlead_'+str(i)+'_world.npy'));feet=cc[abs(cc[:,2]-cc[:,2].min())<1e-9];missing=[q.tolist()for q in feet if tuple(np.floor(q+[.25,.25,-.001]).astype(int))not in bodyset];sole.append({'model':'wheel_fairlead_'+str(i),'foot_cells':len(feet),'unsupported':missing})
report={'body_overlaps':bodyhits,'model_overlaps':modelhits,'other_rope_contacts':ropehits,'sole_support':sole}
(P/('wheel_support_check.json' if wheel_mode else 'support_check.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('body',len(bodyhits),'model',len(modelhits),'ropes',len(ropehits),'unsupported',sum(len(x['unsupported'])for x in sole))
