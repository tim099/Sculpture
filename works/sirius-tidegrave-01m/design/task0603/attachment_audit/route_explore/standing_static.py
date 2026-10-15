from static import *
data=(Q/'routes_candidate.vxk').read_bytes();rr=zlib.decompress(data,-15);nn=struct.unpack_from('<I',rr,4)[0];NEW=json.loads(rr[8:8+nn])['rig'];SS=[]
for s in NEW['sails']:
 vs=np.array(s['verts']).reshape(-1,3);tt=np.array(s['tris']).reshape(-1,3);SS.append((s['name'],vs[tt[:len(tt)//2]]))
opts=[('main-stay','truck-to-truck',[[355.5,120.5,510.5],[510.5,120.5,465.5]],.5),('fore-stay','upper-truck-to-original-ring',[[510.5,120.5,465.5],[567.5,120.5,269.5]],.5),('fore-stay','lower-ring-to-bowsprit',[[567.5,120.5,269.5],[700.5,120.5,195.5]],.5),('jib-halyard','upper-truck-running-r025',[[510.5,120.5,465.5],[567.5,120.5,269.5]],.25),('jib-halyard','upper-truck-running-r020',[[510.5,120.5,465.5],[567.5,120.5,269.5]],.2),('fore-stay','lower-ring-to-original-tack',[[567.5,120.5,269.5],[748.5,120.5,215.5]],.5)]
for x in [440,445,450,455,460,465,470]:
 for side,sg in [('P',-1),('S',1)]:
  col=BODY[(BODY[:,0]==x)&(BODY[:,1]>120 if sg>0 else BODY[:,1]<120)&(BODY[:,2]>=115)&(BODY[:,2]<=150)];yy=col[:,1].max()if sg>0 else col[:,1].min();z=col[col[:,1]==yy,2].max();opts.append(('fore-backstay-'+side,f'outer-bulwark-{x}',[[509.5,120.5,465.5],[x+.5,yy+.5,z+.5]],.3))
out=[]
for name,label,p,rad in opts:
 pp=np.array(p);a,b=pp;cl=[];body=[];mods0=[]
 for sn,tr in SS:
  cand=np.all((tr.max(axis=1)>=np.minimum(a,b)-rad)&(tr.min(axis=1)<=np.maximum(a,b)+rad),axis=1);ids=np.flatnonzero(cand);tt=tr[cand]
  if not len(tt):continue
  dd=segtri(a,b,tt);ts,ok=ray(a,b-a,tt);hit=ok&(ts>=0)&(ts<=1)
  if np.any(hit)or np.any(dd<rad*rad-1e-9):cl.append({'sail':sn,'centerline':ids[hit].tolist(),'points':(a+ts[hit,None]*(b-a)).tolist(),'capsule':ids[dd<rad*rad-1e-9].tolist()})
 cc=BODY[tree.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+.8661+rad))];dd,t=boxdist(a,b,cc);hit=dd<rad*rad-1e-9;body.extend({'cell':c.tolist(),'t':float(u),'distance':float(d**.5)}for c,u,d in zip(cc[hit],t[hit],dd[hit]))
 for m,tr in M:
  bb=np.array(m['bbox'])
  if np.any(np.maximum(a,b)+rad<bb[:3])or np.any(np.minimum(a,b)-rad>bb[3:]):continue
  dd=segtri(a,b,tr)
  if dd.min()<rad*rad-1e-9:mods0.append({'model':m['name'],'distance':float(dd.min()**.5),'inside':intervals(pp,tr)})
 out.append({'name':name,'option':label,'points':p,'radius':rad,'cloth':cl,'body':body,'model':mods0});print(name,label,'cloth',[(c['sail'],len(c['centerline']),len(c['capsule']))for c in cl],'body',len(body),'model',len(mods0),flush=True)
(Q/'standing_static.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
