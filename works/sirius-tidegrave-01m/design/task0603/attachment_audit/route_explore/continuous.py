from static import *
import os
Q=pathlib.Path(__file__).parent
records=json.loads((Q/'static.json').read_text(encoding='utf8'));picked=[x for x in records if x['option']=='main-truck'or x['option']=='truck-to-truck'];picked.append({'name':'jib.sheet-S','option':'bulwark-visible-595','points':[rop['jib.sheet-S']['pts'][:3],[595.5,140.5,158.5]],'radius':.2})
two_stage=os.environ.get('TWO_STAGE')=='1'
standing=os.environ.get('STANDING')=='1'
if two_stage:
 picked=[x for x in picked if not x['name'].startswith('mizzen-topsail.brace-')]
 for x in json.loads((Q/os.environ.get('STAGE_FILE','two_stage.json')).read_text(encoding='utf8')):
  for i in [0,1]:picked.append({'name':x['rope']+('.upper'if i else''),'option':'two-stage','points':x['points'][i:i+2],'radius':.2})
if standing:picked=json.loads((Q/'standing_cases.json').read_text(encoding='utf8'))
Y=[m for m in A['models']if m['meta'].get('kind')=='yard']
def rot(pp,piv,t):
 pp=np.array(pp)-piv;c=np.cos(t);s=np.sin(t);q=pp.copy();q[...,0]=pp[...,0]*c-pp[...,1]*s;q[...,1]=pp[...,0]*s+pp[...,1]*c;return q+piv
out=[]
for rr in picked:
 pp=np.array(rr['points']);rad=rr['radius'];own=None if rr['name'].endswith('.upper')else next((m for m in Y if rr['name'].startswith(m['meta'].get('sail','?')+'.brace-')),None);piv=np.array(own['points']['pivot'])if own else np.zeros(3);Ra=np.linalg.norm((pp[0]-piv)[:2])if own else 0;rows=[]
 for y in Y:
  if own and y['name']==own['name']:
   # Rope Z rises strictly from the named arm. Once above source max Z plus
   # radius, contact is impossible for all rotations (Z is invariant).
   u=max(0,(y['bbox'][5]+rad-pp[0,2])/(pp[1,2]-pp[0,2]));Lmax=np.linalg.norm(pp[1]-piv)+Ra;rows.append({'yard':y['name'],'attached_own_arm':True,'all_contacts_within_arc_bound':float(u*Lmax),'fraction':float(u)});continue
  zgap=max(y['bbox'][2]-max(pp[:,2]),min(pp[:,2])-y['bbox'][5])
  if zgap>rad:rows.append({'yard':y['name'],'Z_separation':float(zgap)});continue
  me=A['meshes'][y['mesh']];vs=np.array(me['verts']).reshape(-1,3)+y['origin'];tr=vs[np.array(me['tris']).reshape(-1,3)];yp=np.array(y['points']['pivot']);Ry=np.linalg.norm((vs-yp)[:,:2],axis=1).max();lim=1.4 if y['meta']['yard']in ['gaff','boom']else .7;r0=y['meta'].get('rotate_z_deg',0)*np.pi/180;stack=[(-.7,.7,-lim,lim,0)]if own else[(0,0,-lim,lim,0)];leaves=0;calls=0;lower=1e9;bad=[]
  while stack:
   al,ah,bl,bh,depth=stack.pop();aa=(al+ah)/2;bb=(bl+bh)/2;pts=pp.copy()
   if own:pts[0]=rot(pp[:1],piv,aa-own['meta']['rotate_z_deg']*np.pi/180)[0]
   ab=rot(pts,yp,-(bb-r0));d=float(segtri(ab[0],ab[1],tr).min()**.5);bound=Ra*(ah-al)/2+Ry*(bh-bl)/2;calls+=1
   if d-bound>rad+1e-9:leaves+=1;lower=min(lower,d-bound);continue
   if d<rad-1e-9 or depth>=30:bad.append({'angles':[aa,bb],'distance':d,'bound':bound,'depth':depth});break
   if Ra*(ah-al)>=Ry*(bh-bl):mid=(al+ah)/2;stack.extend([(al,mid,bl,bh,depth+1),(mid,ah,bl,bh,depth+1)])
   else:mid=(bl+bh)/2;stack.extend([(al,ah,bl,mid,depth+1),(al,ah,mid,bh,depth+1)])
  rows.append({'yard':y['name'],'interval_calls':calls,'separated_leaves':leaves,'minimum_certified_lower_distance':lower,'fail_or_unresolved':bad})
 out.append({'rope':rr['name'],'points':rr['points'],'radius':rad,'yards':rows});print(rr['name'],'calls',sum(x.get('interval_calls',0)for x in rows),'bad',[x for x in rows if x.get('fail_or_unresolved')],flush=True)
(Q/('standing_continuous.json'if standing else(pathlib.Path(os.environ.get('STAGE_FILE','two_stage.json')).stem+'_continuous.json')if two_stage else'continuous.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
