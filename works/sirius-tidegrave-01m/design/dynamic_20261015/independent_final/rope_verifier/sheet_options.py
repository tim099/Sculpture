from dynamic import *
D=json.loads((P/'trajectory.json').read_text());ri=next(i for i,r in enumerate(R['ropes']) if r['name']=='mizzen-lateen.sheet-P');res=[]
for target in ([185.5,86.5,z] for z in [190.5,194.5,198.5,202.5,205.5]):
 hits=[]
 for fi,f in enumerate(D['frames']):
  a=np.array(f['ropes'][ri][:3]);b=np.array(target);c=candidates(a,b,.2);ds,t=box_distance(a,b,c);mask=ds<.04-1e-10
  if np.any(mask):hits.append({'time':f['time'],'cell':c[mask][0].tolist(),'point':(a+t[mask][0]*(b-a)).tolist(),'n':int(mask.sum())})
 res.append({'target':target,'hit_frames':len(hits),'first':hits[:2]});print(res[-1],flush=True)
(P/'sheet_options.json').write_text(json.dumps(res,indent=2))
