import sys,pathlib,zlib,struct,json
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent.parent))
from clearance import *
Q=pathlib.Path(__file__).parent
b=(P/'actual_final/input.vxk').read_bytes();r=zlib.decompress(b,-15);n=struct.unpack_from('<I',r,4)[0];A=json.loads(r[8:8+n])['rig'];rop={x['name']:x for x in A['ropes']}
W=json.loads((Q/'render_state0.json').read_text(encoding='utf8'));WT={x['name']:x for x in W['sails']}
S=[]
for s in A['sails']:
 vs=np.array(s['verts']).reshape(-1,3);ts=np.array(s['tris']).reshape(-1,3);ts=ts[:len(ts)//2];S.append((s['name'],'export',vs[ts]))
 w=WT[s['name']]
 if w['p']is not None:S.append((s['name'],'live_t0',np.array(w['p']).reshape(-1,3)[np.array(w['tri']).reshape(-1,3)]))
opts=[]
for name in ['fore-topsail.brace-P','fore-topsail.brace-S','mizzen-topsail.brace-P','mizzen-topsail.brace-S']:
 pp=np.array(rop[name]['pts']).reshape(-1,3);opts.append((name,'main-truck',np.array([pp[0],[355.5,120.5,510.5]])))
opts.extend([('mizzen-stay','head-to-maintruck',np.array([[205.5,120.5,285.5],[355.5,120.5,510.5]])),('mizzen-stay','truck-to-truck',np.array([[205.5,120.5,405.5],[355.5,120.5,510.5]]))])
for x in [565,570,575,580,585,590]:
 col=BODY[(BODY[:,0]==x)&(BODY[:,1]>120)&(BODY[:,2]>=138)];maxy=col[:,1].max();z=col[col[:,1]==maxy,2].max();end=np.array([x+.5,maxy+.5,z+.5]);opts.append(('jib.sheet-S',f'bulwark-{x}',np.array([np.array(rop['jib.sheet-S']['pts'][:3]),end])))
out=[]
for name,label,pp in opts:
 rad=rop[name]['radius'];cl=[]
 for sn,mode,tr in S:
  for si,(a,b)in enumerate(zip(pp[:-1],pp[1:])):
   bblo=tr.min(axis=1);bbhi=tr.max(axis=1);cand=np.all((bbhi>=np.minimum(a,b)-rad)&(bblo<=np.maximum(a,b)+rad),axis=1);inds=np.flatnonzero(cand);trr=tr[cand]
   if not len(trr):continue
   ds=segtri(a,b,trr);tt,ok=ray(a,b-a,trr);hit=(ok&(tt>=0)&(tt<=1));caps=ds<rad*rad-1e-9
   if np.any(hit)|np.any(caps):cl.append({'sail':sn,'mode':mode,'surface_triangles':inds[caps].tolist(),'centerline_triangles':inds[hit].tolist(),'centerline_points':(a+tt[hit,None]*(b-a)).tolist(),'min_distance':float(ds.min()**.5)})
 # Body exact capsule and full model triangles, raw contacts retained.
 body=[];models=[]
 for si,(a,b)in enumerate(zip(pp[:-1],pp[1:])):
  cc=BODY[tree.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+.8661+rad))];ds,t=boxdist(a,b,cc);hit=ds<rad*rad-1e-9;body.extend({'cell':c.tolist(),'t':float(u),'distance':float(d**.5)}for c,u,d in zip(cc[hit],t[hit],ds[hit]))
  for m,tr in M:
   bb=np.array(m['bbox'])
   if np.any(np.maximum(a,b)+rad<bb[:3])or np.any(np.minimum(a,b)-rad>bb[3:]):continue
   ds=segtri(a,b,tr)
   if ds.min()<rad*rad-1e-9:models.append({'model':m['name'],'distance':float(ds.min()**.5),'inside':intervals(pp,tr)})
 out.append({'name':name,'option':label,'points':pp.tolist(),'radius':rad,'cloth':cl,'body':body,'models':models})
(Q/'static.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
for x in out:print(x['name'],x['option'],'cloth',[(c['sail'],c['mode'],len(c['centerline_triangles']),len(c['surface_triangles']))for c in x['cloth']],'body',len(x['body']),'model',[(c['model'].encode('unicode_escape'),len(c['inside']))for c in x['models']])
