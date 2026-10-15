from dynamic import *
from triangle_distance import seg_tri_distance
D=json.loads((P/'trajectory.json').read_text());ri=next(i for i,r in enumerate(R['ropes']) if r['name']=='mizzen-lateen.sheet-P');yb={x['k']:j for j,x in enumerate(D['yards'])};res=[]
for target in [[185.5,86.5,190.5],[165.5,86.5,190.5],[145.5,86.5,190.5],[125.5,86.5,190.5],[185.5,70.5,190.5],[225.5,70.5,190.5]]:
 hits={};body=[]
 for fi,f in enumerate(D['frames']):
  if fi%5:continue
  a=np.array(f['ropes'][ri][:3]);b=np.array(target);c=candidates(a,b,.2);ds,t=box_distance(a,b,c)
  if np.any(ds<.04-1e-10):body.append({'time':f['time'],'cell':c[ds<.04-1e-10][0].tolist()})
  for mk,m in enumerate(R['models']):
   angle=f['angles'][yb[mk]] if mk in yb else 0;aa,bb=rot(np.array([a,b]),m['points']['pivot'],-angle) if angle else np.array([a,b]);bbox=np.array(m['bbox'])
   if np.any(np.maximum(aa,bb)+.2<bbox[:3]) or np.any(np.minimum(aa,bb)-.2>bbox[3:]):continue
   me=R['meshes'][m['mesh']];v=np.array(me['verts']).reshape(-1,3)+m['origin'];tr=v[np.array(me['tris']).reshape(-1,3)];sel=np.all((tr.max(axis=1)+.2>=np.minimum(aa,bb))&(tr.min(axis=1)-.2<=np.maximum(aa,bb)),axis=1);ds=seg_tri_distance(aa,bb,tr[sel]);ts=seg_tri(aa,bb,tr[sel]);
   if len(ds) and ds.min()<.04-1e-10:
    arc=float(max(ts)*np.linalg.norm(b-a)) if len(ts) else 0;rec={'time':f['time'],'min_distance':float(np.sqrt(ds.min())),'centerline_exit_arc':arc}
    if m['name'] not in hits or hits[m['name']]['centerline_exit_arc']<arc:hits[m['name']]=rec
 res.append({'target':target,'body_hit_frames':len(body),'body_first':body[:1],'models':hits});print(res[-1],flush=True)
(P/'sheet_models.json').write_text(json.dumps(res,indent=2))
