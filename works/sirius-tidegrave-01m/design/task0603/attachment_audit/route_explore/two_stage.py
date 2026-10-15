from static import *
import os
Q=pathlib.Path(__file__).parent
out=[]
earing=os.environ.get('EARING')=='1'
outboard=os.environ.get('OUTBOARD')=='1'
for side,y in [('P',121.5 if earing else 119.5),('S',119.5 if earing else 121.5)]:
 name='mizzen-topsail.brace-'+side;start=np.round(np.array(next(m for m in A['models']if m['name']=='mizzen/yard-mizzen-topsail')['points']['earing-'+side]),2)if earing else np.array(rop[name]['pts'][:3])
 if outboard:
  md=next(m for m in A['models']if m['name']=='mizzen/yard-mizzen-topsail');pv=np.array(md['points']['pivot']);start=np.round(pv+(np.array(md['points']['arm-'+side])-pv)*46/45,2)
 points=np.array([start,[205.5,y,405.5],[355.5,y,510.5]]);cl=[];body=[];model=[]
 for sn,mode,tr in S:
  for i,(a,b)in enumerate(zip(points[:-1],points[1:])):
   cand=np.all((tr.max(axis=1)>=np.minimum(a,b)-.2)&(tr.min(axis=1)<=np.maximum(a,b)+.2),axis=1);ids=np.flatnonzero(cand);tt=tr[cand]
   if not len(tt):continue
   dd=segtri(a,b,tt);ts,ok=ray(a,b-a,tt);hit=ok&(ts>=0)&(ts<=1)
   if np.any(hit)or np.any(dd<.04-1e-9):cl.append({'sail':sn,'mode':mode,'segment':i,'centerline':ids[hit].tolist(),'capsule':ids[dd<.04-1e-9].tolist()})
 for i,(a,b)in enumerate(zip(points[:-1],points[1:])):
  cc=BODY[tree.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+1.0661))];dd,t=boxdist(a,b,cc);hit=dd<.04-1e-9;body.extend({'segment':i,'cell':c.tolist(),'t':float(u),'distance':float(d**.5)}for c,u,d in zip(cc[hit],t[hit],dd[hit]))
  for m,tr in M:
   bb=np.array(m['bbox'])
   if np.any(np.maximum(a,b)+.2<bb[:3])or np.any(np.minimum(a,b)-.2>bb[3:]):continue
   dd=segtri(a,b,tr)
   if dd.min()<.04-1e-9:model.append({'segment':i,'model':m['name'],'distance':float(dd.min()**.5),'inside':intervals(np.array([a,b]),tr)})
 out.append({'rope':name,'points':points.tolist(),'cloth':cl,'body':body,'model':model})
(Q/('two_stage_outboard.json'if outboard else 'two_stage_earing.json'if earing else'two_stage.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(out,ensure_ascii=True))
