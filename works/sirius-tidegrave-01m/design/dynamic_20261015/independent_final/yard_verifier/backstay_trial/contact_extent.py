from pathlib import Path
import numpy as np,json
p=Path(__file__).resolve().parent;d=json.loads((p/'report.json').read_text());maximum=0
for r in d['results']:
 a=np.array(r['a']);b=np.array(r['b']);v=b-a;L=np.linalg.norm(v);rad=r['radius']
 for c in r['body_contacts']:
  lo=np.array(c['cell']);hi=lo+1;t=c['rope_t']
  def inside(x):
   q=a+x*v;return np.linalg.norm(np.maximum(lo-q,0)+np.maximum(q-hi,0))<=rad
  l=0.;rr=t
  if inside(0):left=0.
  else:
   for _ in range(55):
    m=(l+rr)/2
    if inside(m):rr=m
    else:l=m
   left=rr
  l=t;rr=1.
  if inside(1):right=1.
  else:
   for _ in range(55):
    m=(l+rr)/2
    if inside(m):l=m
    else:rr=m
   right=l
  extent=right*L if t<.5 else (1-left)*L;c['contact_t_interval']=[left,right];c['nearest_endpoint_contact_arc_extent']=extent;maximum=max(maximum,extent)
d['maximum_endpoint_contact_arc_extent']=maximum;(p/'report.json').write_text(json.dumps(d,indent=2));print(maximum)
