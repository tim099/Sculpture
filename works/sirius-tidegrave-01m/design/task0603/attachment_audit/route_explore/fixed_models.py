from static import *
data=(Q/'routes_candidate.vxk').read_bytes();rr=zlib.decompress(data,-15);nn=struct.unpack_from('<I',rr,4)[0];NEW=json.loads(rr[8:8+nn])['rig'];names={'mizzen-stay','fore-topsail.brace-P','fore-topsail.brace-S','mizzen-topsail.brace-P','mizzen-topsail.brace-S','jib.sheet-S'};Y={m['name']:m for m in NEW['models']if m['meta'].get('kind')=='yard'};out=[]
for r in NEW['ropes']:
 if r['name']not in names:continue
 p=np.array(r['pts']).reshape(-1,3);lo=p.min(axis=0);hi=p.max(axis=0);end=r['ends'][0];own=Y.get(end[6:].rsplit('/',1)[0])if end.startswith('model:')else None
 if own:
  piv=np.array(own['points']['pivot']);radius=np.linalg.norm((p[0]-piv)[:2]);lo[:2]=np.minimum(lo[:2],piv[:2]-radius);hi[:2]=np.maximum(hi[:2],piv[:2]+radius)
 rows=[]
 for m in NEW['models']:
  if m['meta'].get('kind')=='yard':continue
  bb=np.array(m['bbox']);axisgaps=np.maximum(bb[:3]-hi,lo-bb[3:]);axis=int(axisgaps.argmax());gap=float(axisgaps[axis]);assert gap>r['radius'],(r['name'],m['name'],gap);rows.append({'model':m['name'],'axis':axis,'surface_gap':gap})
 out.append({'rope':r['name'],'full_angle_rope_envelope':np.r_[lo,hi].tolist(),'radius':r['radius'],'fixed_model_count':len(rows),'minimum_separating_axis_gap':min(x['surface_gap']for x in rows),'models':rows})
(Q/'fixed_models.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('fixed model pairs',sum(x['fixed_model_count']for x in out),'all disjoint')
