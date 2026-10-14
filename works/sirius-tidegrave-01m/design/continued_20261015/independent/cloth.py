import pathlib,sys,json,numpy as np
sys.argv=[sys.argv[0],'after_robbands.vxk']
p=pathlib.Path(__file__).parent/'check.py'
exec(p.read_text(encoding='utf8').split('sel=[r')[0])
def clip(poly,axis,value,sgn):
    if not len(poly):return poly
    out=[]
    for j,P in enumerate(poly):
        Q=poly[(j+1)%len(poly)]; d=(P[axis]-value)*sgn; e=(Q[axis]-value)*sgn
        if d>=0:out.append(P)
        if (d>=0)!=(e>=0):out.append(P+(Q-P)*(d/(d-e)))
    return np.array(out)
def polyarea(poly):
    if len(poly)<3:return 0.
    return float(np.linalg.norm(np.sum([np.cross(poly[i]-poly[0],poly[i+1]-poly[0]) for i in range(1,len(poly)-1)],axis=0))*.5)
def checktris(v,tris,cubes):
    cubes=cubes[np.all(cubes+1>v.min(0),axis=1)&np.all(cubes<v.max(0),axis=1)]
    out=[]
    for i,tri in enumerate(tris):
        P=v[tri]; lo=P.min(0);hi=P.max(0); cand=cubes[np.all(cubes+1>lo,axis=1)&np.all(cubes<hi,axis=1)]
        for c in cand:
            poly=P.copy()
            for k in range(3):
                poly=clip(poly,k,c[k]+1e-8,1);poly=clip(poly,k,c[k]+1-1e-8,-1)
            area=polyarea(poly)
            if area>1e-9:out.append({'triangle':i,'cube':c.astype(int).tolist(),'area':area})
    return out
s=next(s for s in rig['sails'] if s['name']=='mizzen-topsail'); v=np.array(s['verts']).reshape(-1,3);t=np.array(s['tris']).reshape(-1,3)
res={'sha256':hashlib.sha256(blob).hexdigest(),'ratlines':[],'sail_body':checktris(v,t,body),'sail_yards':{},'sheets':[],'robbands':[]}
for y in yards:
    local=rot(v,y['at'],-y['r0'])+y['piv']-y['at'];hits=checktris(local,t,y['cubes']);res['sail_yards'][y['name']]=hits
for r in rig['ropes']:
    if (r['name'] in ['main-ratline-P-1','main-ratline-S-1','fore-ratline-P-1','fore-ratline-S-1'] or r['name'].startswith('mizzen-topsail.sheet') or 'robband' in r['name']):
        P=np.array(r['pts']).reshape(-1,3);rec={'name':r['name'],'body':[],'yards':{}}
        for i in range(len(P)-1):
            h=probe(P[i],P[i+1],body,r['radius'])
            if h:rec['body'].append(h)
        for y in yards:
            local=rot(P,y['at'],-y['r0'])+y['piv']-y['at'];hits=[]
            for i in range(len(P)-1):
                h=probe(local[i],local[i+1],y['cubes'],r['radius'])
                if h:hits.append(h)
            if hits:rec['yards'][y['name']]=hits
        key='ratlines' if 'ratline' in r['name'] else 'sheets' if '.sheet' in r['name'] else 'robbands';res[key].append(rec)
(OUT/'cloth.json').write_text(json.dumps(res,ensure_ascii=False),encoding='utf8')
print('source',res['sha256']); print('body',res['sail_body']);print('yards',[(k,len(v),sum(q['area'] for q in v)) for k,v in res['sail_yards'].items()]);print('ropes',[(r['name'],len(r['body']),list(r['yards'])) for k in ['ratlines','sheets','robbands'] for r in res[k]])
