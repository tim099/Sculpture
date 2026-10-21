import audit as a
import numpy as np, json, math, collections
out={}
# The wheel was split into wheel + stand on Oct16: support must use the stand.
path,m,off=next(x for x in a.raw if x[1].get('meta',{}).get('kind')=='wheel_stand')
sl,sh=a.boxes(m,off); wl,wh=a.transformed['甲板-quarter/舵輪']
contact=0
for l,h in zip(wl,wh):
 contact+=int(np.count_nonzero(np.any(np.isclose(h,sl,atol=1e-8)|np.isclose(l,sh,atol=1e-8),axis=1)&np.all(np.minimum(h,sh)-np.maximum(l,sl)>=-1e-8,axis=1)))
base=np.isclose(sl[:,2],np.min(sl[:,2]));supported=0
for l,h in zip(sl[base],sh[base]):
 supported+=any((x,y,round(l[2])-1) in a.static for x in range(math.floor(l[0]+1e-8),math.ceil(h[0]-1e-8)) for y in range(math.floor(l[1]+1e-8),math.ceil(h[1]-1e-8)))
out['wheel_stand']={'voxels':len(sl),'positive_hull_pairs':len(a.touch(sl,sh,a.static)),'wheel_positive_pairs':sum(int(np.count_nonzero(np.all(np.minimum(h,sh)-np.maximum(l,sl)>1e-8,axis=1))) for l,h in zip(wl,wh)),'wheel_boundary_contacts':contact,'stand_bottom_voxels':int(sum(base)),'stand_supported_bottom':int(supported)}
dirs=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
out['magazines']=[]
for name in ['彈藥庫-後','彈藥庫-前']:
 s=a.linksets[name];other=a.static-s;touch=sum(any(tuple(v[k]+d[k] for k in range(3)) in other for d in dirs) for v in s)
 barrel=[t for t in a.targets if t['path'].startswith(name+'/')]
 out['magazines'].append({'name':name,'solid_voxels':len(s),'face_contacts_to_other_structure':touch,'barrels':len(barrel),'barrel_lb_sum':sum(t['meta']['powder_lb'] for t in barrel)})
out['passages']=[]
design=a.ROOT/'sirius-tidegrave-01m/design'
for p in design.glob('*fairlead_holes.vox.txt'):
 work=p.name.split('_fairlead')[0];cells=[]
 for ln in p.read_text().splitlines():
  try:v=tuple(map(int,ln.replace(',', ' ').split()[:3]))
  except ValueError:continue
  if len(v)==3:cells.append(v)
 own=set(a.replay(work));out['passages'].append({'work':work,'designed_holes':len(cells),'current_occupied':sum(v in own for v in cells)})
out['resolved_anchor_comparison']=[]
export={m['path']:m for m in a.parts['models']}
for g in a.guns:
 pts=export[g['path']]['points'];out['resolved_anchor_comparison'].append({'path':g['path'],'muzzle_delta':float(np.linalg.norm(np.array(pts['muzzle'])-g['points']['muzzle'])),'breech_delta':float(np.linalg.norm(np.array(pts['breech'])-g['points']['breech']))})
(a.OUT/'additional.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
