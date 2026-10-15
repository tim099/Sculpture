from static import *
start=np.array(rop['jib.sheet-S']['pts'][:3]);candidates=BODY[(BODY[:,0]>=570)&(BODY[:,0]<=595)&(BODY[:,1]>=135)&(BODY[:,1]<=148)&(BODY[:,2]>=150)];ss={tuple(x)for x in BODY};candidates=np.array([x for x in candidates if tuple(x+[0,0,1])not in ss]);out=[]
for cell in candidates:
 end=cell+.5;a=start;b=end;cc=BODY[tree.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+1.0661))];ds,t=boxdist(a,b,cc);hit=ds<.04-1e-9
 if np.count_nonzero(hit)>1:continue
 out.append({'cell':cell.tolist(),'point':end.tolist(),'body_contacts':cc[hit].tolist(),'min_t':float(t[hit].min())})
out.sort(key=lambda x:np.linalg.norm(np.array(x['point'])-start));(Q/'jib_endpoints.json').write_text(json.dumps(out,indent=2));print('single-cell',len(out),json.dumps(out[:12]))
