"""Build an isolated manual preview from the exact audited VXK and current game.

Uses the game's config writer/build/roundtrip verifier. Does not register an
unfinished ship in the normal game's fleet or replace any other user's cache.
"""
import hashlib
import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding='utf8', errors='replace')

SOURCE = Path('D:/Unity/Valhalla/Blockside')
DEST = Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/manual-preview')
SNAPSHOT = Path(sys.argv[1]).resolve()
assert SNAPSHOT.is_file() and SNAPSHOT.suffix == '.vxk'
assert DEST.resolve().parent == Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603').resolve()
DEST.mkdir(exist_ok=True)
for name in ('src', 'VoxelKit'):
    shutil.copytree(SOURCE / name, DEST / name, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.git', '__pycache__', '*.prev', '*.stale', '*.source'))
for name in ('admin.html', 'sandbox.html'):
    if (SOURCE / name).exists():
        shutil.copy2(SOURCE / name, DEST / name)
spec = importlib.util.spec_from_file_location('preview_admin', DEST / 'src/admin.py')
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)


def exact_snapshot(work, dest):
    assert work == 'sirius-tidegrave-01m-assembly'
    shutil.copy2(SNAPSHOT, dest)
    return 'Imported exact frozen candidate: ' + str(SNAPSHOT)


admin.export = exact_snapshot
old_cache = DEST / 'VoxelKit/_cache/tidegrave.vxk'
if old_cache.exists():
    archive = DEST / 'previous'
    archive.mkdir(exist_ok=True)
    old_cache.rename(archive / ('tidegrave-' + uuid.uuid4().hex + '.vxk'))
logs = admin.act_import('sirius-tidegrave-01m-assembly', 'tidegrave', '潮墓號・TASK-0603 候選', build=False)
cfg = admin.load()
cfg['ships'] = [s for s in cfg['ships'] if s['id'] in ('constitution', 'tidegrave')]
assert not admin.validate(cfg)
admin.save(cfg)
logs += admin.act_build()
logs += admin.act_verify()
(DEST / 'BUILD.txt').write_text('\n'.join(logs) + '\n', 'utf8')
print('\n'.join(logs[-4:]), flush=True)
files = list((DEST / 'src/js').glob('*.js')) + [DEST / 'src/template.html', DEST / 'VoxelKit/voxelkit.js']
manifest = {
    'purpose': 'Local manual acceptance candidate; TASK-0603 remains open until Tim accepts.',
    'snapshot': str(SNAPSHOT),
    'vxk_sha256': hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),
    'html_sha256': hashlib.sha256((DEST / 'index.html').read_bytes()).hexdigest(),
    'sources': {str(p.relative_to(DEST)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    'settings': 'Normal defaults preserved: cloth collision defaults off and requires rig High when enabled.',
}
(DEST / 'MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', 'utf8')
print('Manual preview:', DEST / 'index.html')
