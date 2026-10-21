import pathlib,json,struct,zlib,hashlib,copy
O=pathlib.Path(__file__).parent; R=pathlib.Path('D:/Unity/Valhalla/Sculpture/works')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def vx(p):
 b=zlib.decompress(p.read_bytes(),-15);n=struct.unpack_from('<I',b,4)[0];h=json.loads(b[8:8+n]);pos=8+n;N=h['nchunks'];coords=struct.unpack_from('<'+'H'*3*N,b,pos);pos+=6*N;d={}
 for i in range(N):
  x,y,z=coords[3*i:3*i+3]
  for j,c in enumerate(b[pos+4096*i:pos+4096*(i+1)]):
   if c:d[(x*16+j%16,y*16+j//16%16,z*16+j//256)]=c
 return h,d
def replay(w):
 d={}
 for p in sorted((R/w/'events').glob('*/*.json')):
  a=load(p)
  if a.get('op')=='workedit':
   for v in a['edit']['after']:
    k=(v['x'],v['y'],v['z'])
    if v['color']:d[k]=v['color']
    else:d.pop(k,None)
  elif 'placed_colored' in a:
   for v in a['placed_colored']:d[tuple(v[:3])]=v[3]
  elif 'placed_voxels' in a:
   for v in a['placed_voxels']:d[tuple(v[:3])]=a['color']
  elif 'carved_voxels' in a:
   for v in a['carved_voxels']:d.pop(tuple(v),None)
 return d
before,b=vx(O/'shared/current.vxk');after,a=vx(O/'shared/after_bearing.vxk')
P=O/'hardware/bearing_proposal';cut={tuple(map(int,l.split(',')[:3])):int(l.split(',')[3]) for l in (P/'carve_exact.vox.txt').read_text().splitlines()}
assert {k:b[k] for k in b.keys()-a.keys()}==cut
assert not a.keys()-b.keys() and all(a[k]==b[k] for k in a.keys()&b.keys())
assert all(k[2]>52 for k in cut)
def models(h):
 out={}
 for m in h['rig']['models']:
  q=copy.deepcopy(m);q['mesh']=h['rig']['meshes'][q['mesh']];out[q['name']]=q
 return out
bm,am=models(before),models(after)
assert all(am[k]==v for k,v in bm.items())
assert set(am)-set(bm)=={'rudder-bearing-fixed','rudder-bearing-moving'}
assert before['rig']['ropes']==after['rig']['ropes'] and before['rig']['sails']==after['rig']['sails']
for kind,count in [('fixed',4800),('moving',3528)]:
 w='sirius-tidegrave-01m-rudder-bearing-'+kind
 expected={tuple(map(int,l.split(',')[:3])):int(l.split(',')[3]) for l in (P/(kind+'.vox.txt')).read_text().splitlines()}
 assert replay(w)==expected and len(expected)==count
 assert load(R/w/'work.json')['meters_per_voxel']==.01
raw=load(R/'sirius-tidegrave-01m-assembly/models.json');rows=raw['models'];proposal=load(P/'proposal.json')
for kind in ['fixed','moving']:
 m=next(m for m in rows if m['name']=='rudder-bearing-'+kind)
 for k,v in proposal['transform'].items():assert m[k]==v,(kind,k,m[k],v)
moving=am['rudder-bearing-moving']['meta'];old=am['舵']['meta']
for k in ['spin','spin_k','spin_min','spin_max','spin_lag']:assert moving[k]==old[k]
for k in ['x','y','z']:
 assert moving['spin_axis_'+k]==old['axis_'+k]
 assert moving['spin_pivot_'+k]==old['hinge_'+k]
report={'executor':'parent Sirius; actual installation readback','before_voxels':len(b),'after_voxels':len(a),'exact_guarded_removals':len(cut),'added_or_recolored':0,'waterline_and_below_unchanged':True,'original_models_unchanged':len(bm),'new_models':2,'ropes_unchanged':len(after['rig']['ropes']),'sails_unchanged':len(after['rig']['sails']),'source_exact':[4800,3528],'transform_exact':True,'spin_axis_pivot_and_drive_match_old_rudder':True,'after_sha256':hashlib.sha256((O/'shared/after_bearing.vxk').read_bytes()).hexdigest(),'limitation':'No game runtime or cloth dynamic acceptance performed.'}
(O/'after_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
