import pathlib,sys,json,numpy as np,math
p=pathlib.Path(__file__).parent/'check.py'; sys.argv=[sys.argv[0],'final_rig.vxk'];exec(p.read_text(encoding='utf8').split('sel=[r')[0])
prev=json.loads((OUT/'after_robbands_header.json').read_text(encoding='utf8')); delta={}
for kind in ['ropes','sails','models','meshes']:
    A=prev['rig'][kind]; B=H['rig'][kind]
    if kind in ['meshes']:delta[kind]=A==B;continue
    a={q['name']:q for q in A};b={q['name']:q for q in B};delta[kind]={'count':[len(a),len(b)],'added':list(b.keys()-a.keys()),'removed':list(a.keys()-b.keys()),'changed':{k:[key for key in a[k].keys()|b[k].keys() if a[k].get(key)!=b[k].get(key)] for k in a.keys()&b.keys() if a[k]!=b[k]}}
stand=[];strip=[]
for r in rig['ropes']:
    if not r['name'].startswith(('main-shroud','fore-shroud','main-backstay','fore-backstay')):continue
    P=np.array(r['pts']).reshape(-1,3);A,B=P;L=np.linalg.norm(B-A);h=probe(A,B,body,r['radius']);cells=np.array(h['cells']) if h else np.empty((0,3)); records=[]
    for c in cells:
        q=probe(A,B,c[None,:],r['radius']);records.append({'cell':c.tolist(),'arc':q['arc'],'end_distance_min':min(q['arc'][0],L-q['arc'][1]),'end_distance_max':min(q['arc'][1],L-q['arc'][0])})
    stand.append({'name':r['name'],'length':float(L),'contacts':records})
    for y in yards:
        if y['meta']['mast']!=r['name'].split('-')[0] or y['meta']['yard'] in ('gaff','boom'):continue
        zlo=y['cubes'][:,2].min()-y['piv'][2]+y['at'][2]-r['radius'];zhi=y['cubes'][:,2].max()+1-y['piv'][2]+y['at'][2]+r['radius']; aa=(zlo-A[2])/(B[2]-A[2]);bb=(zhi-A[2])/(B[2]-A[2]); tl=max(0,min(aa,bb));th=min(1,max(aa,bb))
        if tl>th:continue
        q=A+np.array([tl,th])[:,None]*(B-A)-y['at']; halfwidth=float(np.max(np.abs(np.r_[y['cubes'][:,0]-y['piv'][0],y['cubes'][:,0]+1-y['piv'][0]])))
        bound=min(abs(v[0])*math.cos(.7)-abs(v[1])*math.sin(.7) for v in q)-halfwidth-r['radius'];strip.append({'rope':r['name'],'yard':y['name'],'source_halfwidth':halfwidth,'clearance_lower_bound':float(bound)})
neg={}; oldpath=OUT/'snapshots/old_source_after.vxk' if os.environ.get('VERIFY_FROZEN')=='1' else ROOT/'sirius-tidegrave-01m/design/audits/20261014/yard_sweep/source_after.vxk';rr=zlib.decompress(oldpath.read_bytes(),-15);nn=struct.unpack_from('<I',rr,4)[0];old=json.loads(rr[8:8+nn])
for rn,yn in [('main-course.lift-P','main/yard-main-topsail'),('main-topsail.lift-P','main/yard-main-topgallant'),('main-shroud-P0','main/yard-main-course')]:
    r=next(q for q in old['rig']['ropes'] if q['name']==rn); y=next(q for q in yards if q['name']==yn); P=np.array(r['pts']).reshape(-1,3); P=rot(P,y['at'],-y['r0'])+y['piv']-y['at'];neg[rn+' -> '+yn]=[probe(P[i],P[i+1],y['cubes'],r['radius']) for i in range(len(P)-1)]
out={'source':str(SRC),'sha256':hashlib.sha256(blob).hexdigest(),'delta_from_robbands':delta,'standing':stand,'standing_continuous_strip':strip,'negative_old_rig':neg}
(OUT/'final_audit.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf8')
print('delta', {k:(v if k=='meshes' else len(v['changed'])) for k,v in delta.items()});print('strip minimum',min(x['clearance_lower_bound'] for x in strip)); print('standing max terminal distance',[(s['name'],max(c['end_distance_max'] for c in s['contacts'])) for s in stand]);print('negative',[(k,any(v)) for k,v in neg.items()])
