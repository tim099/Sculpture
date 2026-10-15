"""Author readback of exact CLI delta, independent of collision implementations."""
from pathlib import Path
import sys
import json
import hashlib
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / 'dynamic_20261015'
sys.path.insert(0, str(HERE / 'audits/20261014/yard_sweep'))
from vxk_decode import unpack

old, ov = unpack((HERE / 'continued_20261015/final_heads.vxk').read_bytes())
new, nv = unpack((OUT / 'final_dynamic.vxk').read_bytes())
a = {tuple(map(int, v[:3])): int(v[3]) for v in ov}
b = {tuple(map(int, v[:3])): int(v[3]) for v in nv}
delta = json.loads((OUT / 'bracket_delta.json').read_text('utf8'))
added = {tuple(v[:3]): v[3] for v in delta['only_added']}
assert len(added) == 56
assert len(b) == len(a) + 56 and all(b.get(q) == c for q, c in a.items())
assert {q: c for q, c in b.items() if q not in a} == added
assert old['rig']['models'] == new['rig']['models']
assert old['rig']['meshes'] == new['rig']['meshes']
ro, rn = ({r['name']: r for r in h['rig']['ropes']} for h in (old, new))
changed_ropes = [n for n in ro if ro[n] != rn[n]]
sa, sb = ({s['name']: s for s in h['rig']['sails']} for h in (old, new))
changed_sails = [n for n in sa if sa[n] != sb[n]]
assert len(ro) == len(rn) == 302 and len(sa) == len(sb) == 10
expected = {f'mizzen-shroud-{side}{j}' for side in ('P', 'S') for j in range(3)}
expected |= {f'mizzen-ratline-{side}-{j}' for side in ('P', 'S') for j in range(1, 22)}
expected |= {'jib.sheet-S', 'mizzen-lateen.sheet-P'}
expected |= {'mizzen-backstay-P', 'mizzen-backstay-S'}
assert set(changed_ropes) <= expected
assert set(changed_sails) == {'jib'}
bindings = json.loads((OUT / 'independent_final/rope_verifier/bindings.json').read_text('utf8'))
assert all(r['ya'] == r['yb'] == -1 for r in bindings if '-ratline-' in r['name'])
result = {
    'sha256': hashlib.sha256((OUT / 'final_dynamic.vxk').read_bytes()).hexdigest(),
    'voxels': len(b), 'checksum': format(new['checksum'], '08x'),
    'body_delta_only_added': len(added), 'existing_voxels_and_colors_unchanged': len(a),
    'all_models_and_meshes_unchanged': True, 'changed_ropes': changed_ropes,
    'changed_sails': changed_sails, 'ropes': len(rn), 'sails': len(sb),
    'models': len(new['rig']['models']),
    'game_moving_ropes': sum(r['ya'] >= 0 or r['yb'] >= 0 for r in bindings),
    'ratline_yard_bindings': 0,
}
(OUT / 'delta_readback.json').write_text(json.dumps(result, indent=2) + '\n', 'utf8')
print(json.dumps(result, indent=2))
