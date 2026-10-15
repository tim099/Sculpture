from pathlib import Path
import json
import hashlib
from collections import Counter

ROOT = Path(__file__).resolve().parent / 'dynamic_20261015'
for row in json.loads((ROOT / 'MANIFEST.json').read_text('utf8')):
    data = (ROOT / row['path']).read_bytes()
    assert len(data) == row['bytes']
    assert hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
P = ROOT / 'independent_final'
final_sha = hashlib.sha256((ROOT / 'final_dynamic.vxk').read_bytes()).hexdigest()
assert json.loads((P / 'rope_verifier/provenance.json').read_text('utf8'))['sha256'] == final_sha
assert json.loads((P / 'cloth_verifier/pins.json').read_text('utf8'))['vxkSHA'] == final_sha
assert json.loads((P / 'yard_verifier/report.json').read_text('utf8'))['input_sha256'] == final_sha
d = json.loads((P / 'rope_verifier/dynamic.json').read_text('utf8'))
assert d['frames'] == 249
assert not [c for c in d['contacts'] if c['near_end'] > 5]
assert not [c for c in d['contacts'] if 'ratline' in c['rope']]
f = json.loads((P / 'cloth_verifier/matrix.json').read_text('utf8'))
extra = json.loads((P / 'cloth_verifier/extra_matrix.json').read_text('utf8'))
assert len(f['reports']) == 20 and len(extra['reports']) == 3
assert any(h['type'] == 'body' and h.get('pins') == [0, 0, 0]
           and h['alpha'] == 255 for r in f['reports'] for h in r['hits'])
assert all(h['type'] == 'attachment' for r in extra['reports'][:2] for h in r['hits'])
pairs = json.loads((P / 'rope_verifier/rope_pairs.json').read_text('utf8'))
middle = [c for c in pairs['static'] if c['class'] == 'interior_crossing_requires_context']
assert len(middle) == 126
assert all(('ratline-' in c['a'] + c['b']) and c['a'].split('-')[0] == c['b'].split('-')[0] for c in middle)
summary = {'input_sha256': final_sha, 'manifest_verified': True,
    'dynamic_sampled_poses': 249, 'dynamic_contact_records_retained': len(d['contacts']),
    'dynamic_records_beyond_5_cells_discovery_only': 0,
    'middle_rope_crossings': len(middle), 'same_mast_ratline_lashings': True,
    'cloth_cases': len(f['reports']) + len(extra['reports']),
    'sampled_cloth_snapshots': sum(r['frames'] for r in f['reports'] + extra['reports']),
    'overall': 'FAIL: intact opaque free cloth penetrates body/models/ropes',
    'important': 'The 5-cell filter above is only a discovery check, not an attachment acceptance exemption.'}
print(json.dumps(summary, indent=2))
