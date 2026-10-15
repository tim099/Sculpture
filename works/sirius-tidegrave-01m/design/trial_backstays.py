"""Parent design trial, in memory only; reuse frozen independent distance code."""
from pathlib import Path
import shutil
import sys
import json
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dynamic_20261015'
YARD = OUT / 'independent_final/yard_verifier'
D = YARD / ('actual_backstays' if '--actual' in sys.argv else 'backstay_trial')
D.mkdir(exist_ok=True)
s = (YARD / 'actual_standing/check.py').read_text('utf8')
replacement = (
    "ropes=[('mizzen-backstay-P',np.array([204.5,120.5,405.5]),np.array([84.5,70.5,226.5]),.3),"
    "('mizzen-backstay-S',np.array([204.5,120.5,405.5]),np.array([84.5,170.5,226.5]),.3)];"
    "feet=[];print('CROWN CANDIDATE',flush=True)")
if '--actual' in sys.argv:
    replacement = (
        "names=['mizzen-backstay-P','mizzen-backstay-S'];"
        "ropes=[(n,np.array(actualropes[n]['pts'][:3]),np.array(actualropes[n]['pts'][-3:]),actualropes[n]['radius']) for n in names];"
        "feet=[];print('ACTUAL CROWN ATTACHMENTS',flush=True)")
s = s.replace("print('FEET',feet,flush=True)", replacement)
(D / 'check.py').write_text(s, 'utf8')
shutil.copy2(YARD / 'actual_standing/candidate_standing.vxk', D / 'candidate_standing.vxk')
sys.path.insert(0, str(OUT / 'independent_final/rope_verifier'))
import audit
import rope_pairs
r = json.loads(json.dumps(audit.R))
for rope in r['ropes']:
    if rope['name'].startswith('mizzen-backstay-'):
        y = 70.5 if rope['name'].endswith('P') else 170.5
        rope['pts'] = [204.5, 120.5, 405.5, 84.5, y, 226.5]
rope_pairs.R = r
pairs = rope_pairs.contacts([rope['pts'] for rope in r['ropes']])
suspects = [c for c in pairs if 'mizzen-backstay' in c['a'] + c['b']
            and c['class'] == 'interior_crossing_requires_context']
(OUT / 'backstay_trial_pairs.json').write_text(json.dumps(suspects, indent=2) + '\n', 'utf8')
print('New backstay middle rope/rope crossings:', len(suspects), suspects[:5])
