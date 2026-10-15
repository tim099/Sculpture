from audit import *
out=[]
for r in R['ropes']:
 if 'breech' not in r['name']:continue
 name=r['ends'][0][6:].rsplit('/',1)[0];m=mods[name];me=R['meshes'][m['mesh']];tr=(np.array(me['verts']).reshape(-1,3)+m['origin'])[np.array(me['tris']).reshape(-1,3)]
 p=np.array(r['pts']).reshape(-1,3);sg=np.sign(m['points']['muzzle'][1]-m['points']['breech'][1]);dx=np.sign(p[-1,0]-p[0,0]);a=p[0]+[0,-sg*2,0];b=p[0]+[dx*9,-sg*2,0];points=np.array([p[0],a,b,p[-1]]);hh=intervals(points,tr)
 out.append({'rope':r['name'],'route':points.tolist(),'inside':hh,'required_physical_fairleads':[a.tolist(),b.tolist()]})
(P/'routes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print('bad outside initial knob',[(x['rope'].encode('unicode_escape'),x['inside']) for x in out if any(h['segment']!=0 for h in x['inside'])]);print('initial ranges', min(sum(h['arc'][1]-h['arc'][0] for h in x['inside']) for x in out), max(sum(h['arc'][1]-h['arc'][0] for h in x['inside']) for x in out))
