from clearance import *
rrs=json.loads((P/'route_clearance.json').read_text(encoding='utf8'));wheel=json.loads((P/'wheel_route.json').read_text(encoding='utf8'));cells=np.concatenate([np.load(P/'support_world.npy'),np.load(P/'wheel_fairlead_1_world.npy'),np.load(P/'wheel_fairlead_2_world.npy')]);t2=cKDTree(cells+.25);minimum=1e9;hits=[]
for rr in rrs+[{'rope':'steer-wheel-S',**wheel}]:
 pp=np.array(rr['route'])
 for i,(a,b) in enumerate(zip(pp[:-1],pp[1:])):
  cc=cells[t2.query_ball_point((a+b)/2,float(np.linalg.norm(b-a)/2+.684))]
  if not len(cc):continue
  dd,tt=boxdist(2*a,2*b,2*cc);d=float(dd.min()**.5/2);minimum=min(minimum,d)
  if d<.25-1e-8:hits.append({'rope':rr['rope'],'segment':i,'distance':d})
# Negative controls use actual discarded geometry and fill a real fairlead hole.
old=json.loads((P/'intervals.json').read_text(encoding='utf8'))['results'];oldguns=[x for x in old if 'breech'in x['rope']];oldwheel=next(x for x in old if x['rope']=='steer-wheel-S')
a,b=np.array(rrs[0]['route'])[1:3];filled=a-[.25,.25,.25];dd,tt=boxdist(a*2,b*2,np.array([filled])*2)
assert all(any(h['arc'][0]>1 and h['arc'][1]-h['arc'][0]>.01 for h in x['intervals'])for x in oldguns)
assert len(oldwheel['intervals']) and oldwheel['intervals'][0]['arc'][0]>13
assert dd.min()==0
contacts=[]
for rr in rrs[:2]+[{'rope':'steer-wheel-S',**wheel}]:
 r=next(x for x in R['ropes']if x['name']==rr['rope']);name=r['ends'][0][6:].rsplit('/',1)[0];m=mods[name];me=R['meshes'][m['mesh']];tr=(np.array(me['verts']).reshape(-1,3)+m['origin'])[np.array(me['tris']).reshape(-1,3)];pp=np.array(rr['route']);a,b=pp[:2];L=np.linalg.norm(b-a);arcs=[]
 for u in np.linspace(0,1,4001):
  q=a+u*(b-a)
  if inside(q,tr)or pttri(q,tr).min()<.25**2:arcs.append(float(u*L))
 contacts.append({'rope':rr['rope'],'first_segment_model_capsule_contact_arc_bounds_dense_4001':[min(arcs),max(arcs)]if arcs else []})
result={'all_new_routes_vs_all_new_supports_minimum_surface_distance':minimum,'defects':hits,'negative_controls':{'old_96_gun_paths_true_interior':len(oldguns),'old_wheel_S_interior_interval':oldwheel['intervals'],'filled_hole_detected':bool(dd.min()==0)},'attachment_local_extents':contacts}
(P/'controls.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=True))
