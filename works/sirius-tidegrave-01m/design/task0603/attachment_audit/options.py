from audit import *
out=[]
for r in R['ropes']:
 if 'breech' not in r['name']:continue
 name=r['ends'][0][6:].rsplit('/',1)[0];m=mods[name];me=R['meshes'][m['mesh']];tr=(np.array(me['verts']).reshape(-1,3)+m['origin'])[np.array(me['tris']).reshape(-1,3)]
 p=np.array(r['pts']).reshape(-1,3);suffix=r['name'].split('-')[-1];eye=np.array(m['points']['eye-'+suffix]);straight=intervals(p[[0,-1]],tr);tackle=intervals(np.array([eye,p[-1]]),tr)
 out.append({'name':r['name'],'straight':straight,'eye_tackle':tackle,'eye':eye.tolist(),'to':p[-1].tolist()})
(P/'options.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print('straight lengths range',min(sum(h['arc'][1]-h['arc'][0] for h in x['straight'])for x in out),max(sum(h['arc'][1]-h['arc'][0] for h in x['straight'])for x in out));print('eye lengths range',min(sum(h['arc'][1]-h['arc'][0] for h in x['eye_tackle'])for x in out),max(sum(h['arc'][1]-h['arc'][0] for h in x['eye_tackle'])for x in out))
