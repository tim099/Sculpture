import json,zlib,struct,base64,math,pathlib,collections
p=pathlib.Path(__file__).parent
b=zlib.decompress(pathlib.Path('D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m/design/continued_20261015/final_heads.vxk').read_bytes(),-15)
h=json.loads(b[8:8+struct.unpack('<I',b[4:8])[0]])
ss={s['name']:s for s in h['rig']['sails']}
r=json.loads((p/'body_dynamics.json').read_text())
for sc in r['results']:
 for x in sc['uniqueHits']:
  s=ss[x['sail']]; tx=s.get('texture'); x['alpha']=255
  if tx:
   vs=s['tris'][3*x['tri']:3*x['tri']+3]
   uv=[sum(tx['uv'][v*2+a] for v in vs)/3 for a in (0,1)]
   uv=[max(0,min(n-1,math.floor(v*n))) for v,n in zip(uv,[tx['w'],tx['h']])]
   x['alpha']=base64.b64decode(tx['rgba'])[(uv[1]*tx['w']+uv[0])*4+3]
  if x['alpha']<128: x['kind']='transparent-hole'
  elif all(x['pinnedFine']): x['kind']='attachment'
  elif not any(x['pinnedFine']): x['kind']='opaque-interior'
  else: x['kind']='attachment-neighborhood'
  x['cellInteriorMargin']=min(min(v-math.floor(v),math.ceil(v)-v) for v in x['xyz'])
 sc['classification']=dict(collections.Counter(x['kind'] for x in sc['uniqueHits']))
(p/'body_classified.json').write_text(json.dumps(r,indent=2))
for sc in r['results']:
 print(sc['scenario'],sc['classification'])
 for sail in ss:
  xs=[x for x in sc['uniqueHits'] if x['sail']==sail and x['kind']=='opaque-interior' and x['cellInteriorMargin']>.1]
  if xs: print(sail,xs[0])
