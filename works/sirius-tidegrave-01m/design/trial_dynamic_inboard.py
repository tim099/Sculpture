"""Parent candidate selection using the independently authored distance metric."""
from pathlib import Path
import sys
import json
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / 'dynamic_20261015'
sys.path.insert(0, str(OUT / 'independent_final/rope_verifier'))
sys.path.insert(0, str(HERE / 'audits/20261014/yard_sweep'))
import audit
import rope_pairs
from vxk_decode import unpack

header, _ = unpack((OUT / 'candidate_standing.vxk').read_bytes())
audit.R = rope_pairs.R = header['rig']
contacts = rope_pairs.contacts([r['pts'] for r in header['rig']['ropes']])
crossings = [c for c in contacts if c['class'] == 'interior_crossing_requires_context']
unexpected = [c for c in crossings if not (
    ('ratline-' in c['a'] or 'ratline-' in c['b'])
    and c['a'].split('-')[0] == c['b'].split('-')[0])]
(OUT / 'inboard_rope_pairs.json').write_text(json.dumps({
    'parent_candidate_selection': True, 'contacts': len(contacts),
    'interior_crossings': len(crossings), 'unexpected': unexpected,
    'remaining': crossings,
}, indent=2) + '\n', 'utf8')
print('Contacts:', len(contacts), 'middle crossings:', len(crossings),
      'not same-mast ratline lashing:', len(unexpected))
for c in unexpected[:20]:
    print(c['a'], c['b'], c['distance'], c['point'])
