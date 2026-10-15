"""Apply a tested integration proposal ONLY to the isolated preview copy.

The real Blockside tree and configuration remain owned by ame. The patch fixes
fore/aft gun powder crew spawning at the muzzle beyond the bow, instead of aft
of the actual breech. Broadside behavior remains identical.
"""
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/manual-preview')
OUT = ROOT / 'delivery/game_integration'
OUT.mkdir(exist_ok=True)
source = DEST / 'src/js/23_powder.js'
old = source.read_text('utf8')
needle = '    sh.pmWant += sh.cw.monkeys;'
assert old.count(needle) == 1
insert = '''    // Fore/aft guns: the muzzle can be outside the deck. Spawn behind the breech.
    if (Math.abs(gs[0].ax[0]) > Math.abs(gs[0].ax[1]) && gs[0].model.pts.breech)
      x = Math.round(gs[0].model.pts.breech[0] - (gs[0].ax[0] > 0 ? 6 : -6));
'''
new = old.replace(needle, insert + needle)
source.write_text(new, 'utf8')
(OUT / '23_powder.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
    fromfile='a/src/js/23_powder.js', tofile='b/src/js/23_powder.js')), 'utf8')
spec = importlib.util.spec_from_file_location('preview_admin', DEST / 'src/admin.py')
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)
cfg = admin.load()
ship = next(s for s in cfg['ships'] if s['id'] == 'tidegrave')
ship['name'] = '潮墓號'
ship['geo'] = {'spar': [114, 140], 'marines': [100, 80], 'center': 155,
               'aim': 90, 'aimZ': [30, 480], 'deckAim': [74, 106], 'rigAim': [210, 410]}
assert not admin.validate(cfg)
admin.save(cfg)
(OUT / 'suggested_ship.json').write_text(json.dumps(ship, ensure_ascii=False, indent=2), 'utf8')
(OUT / 'BUILD.txt').write_text('\n'.join(admin.act_build() + admin.act_verify()), 'utf8')
manifest_path = DEST / 'MANIFEST.json'
manifest = json.loads(manifest_path.read_text('utf8'))
manifest['sources']['src/js/23_powder.js'] = hashlib.sha256(source.read_bytes()).hexdigest()
manifest['html_sha256'] = hashlib.sha256((DEST / 'index.html').read_bytes()).hexdigest()
manifest['integrationProposal'] = 'Only isolated copy: fore/aft powder spawn behind breech, Tidegrave geo.'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), 'utf8')
print('Isolated integration proposal built. Actual game is unchanged.')
