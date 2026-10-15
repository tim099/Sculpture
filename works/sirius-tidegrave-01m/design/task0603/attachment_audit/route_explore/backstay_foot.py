from static import *
top=np.array([509.5,120.5,465.5]);ss={tuple(c)for c in BODY};candidates=BODY[(BODY[:,0]>=440)&(BODY[:,0]<=465)&(BODY[:,1]>=68)&(BODY[:,1]<=95)&(BODY[:,2]>=115)&(BODY[:,2]<=150)];candidates=np.array([c for c in candidates if tuple(c+[0,0,1])not in ss]);out=[]
for c in candidates:
 end=c+.5;a=top;b=end;cc=BODY[tree.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+1.1661))];dd,t=boxdist(a,b,cc);hit=dd<.09-1e-9;contacts=cc[hit];other=contacts[contacts[:,2]<450]
 if len(other)!=1:continue
 out.append({'point':end.tolist(),'cell':c.tolist(),'head_contacts':contacts[contacts[:,2]>=450].tolist(),'foot_contacts':other.tolist(),'distance_to_x450':abs(c[0]-450)})
out.sort(key=lambda x:(x['distance_to_x450'],x['point'][1]));(Q/'backstay_foot.json').write_text(json.dumps(out,indent=2));print('single visible feet',len(out),json.dumps(out[:12]))
