import json,hashlib,re
from pathlib import Path
O=Path(__file__).parent;R=Path('D:/Unity/Valhalla/Sculpture/works');B='sirius-tidegrave-01m';out=[]
for w in sorted(R.glob(B+'-deck-*')):
 for f in sorted((w/'events').rglob('*.json'))[1:]:
  e=json.loads(f.read_text(encoding='utf8'));s=e['source'];p=Path(s['file']);blob=p.read_bytes();rows=[list(map(int,re.split('[,\\s]+',line.strip()))) for line in blob.decode('utf8').splitlines() if line.strip()]
  key='carved_voxels' if e['op']=='carve' else 'placed_colored';record={tuple(q[:3]):q[3] if len(q)>3 else None for q in e[key]};planned={tuple(q[:3]):q[3] if len(q)>3 else None for q in rows}
  out.append({'event':str(f),'event_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'source':str(p),'hash_matches_recorded_source':hashlib.sha256(blob).hexdigest()==s['sha256'],'recorded_count':len(record),'source_count':len(planned),'coordinate_symmetric_difference':len(record.keys()^planned.keys()),'color_differences_if_source_has_color':sum(record.get(q)!=c for q,c in planned.items() if c is not None and q in record and record[q] is not None)})
inputs=json.loads((O/'report.json').read_text(encoding='utf8'))['inputs_sha256'];changed=[p for p,h in inputs.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
report={'later_deck_patch_ledger':out,'initial_inputs_changed_during_audit':changed}
(O/'patch_ledger.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
