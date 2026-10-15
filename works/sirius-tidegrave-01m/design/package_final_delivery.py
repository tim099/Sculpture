"""Freeze author-side game delivery and independently compare decoded body bytes.

No game configuration writes. All sculpture state reads/exports use CLI. This
checks repeat export and current source preservation, not clean stage rebuilding.
"""
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, 'D:/Unity/Valhalla/Blockside/VoxelKit')
from build_structure import cli, BASE
from voxel_export import unpack

OUT = ROOT / 'delivery'
FINAL = OUT / 'tidegrave_import_20261015.vxk'


def checksum(a):
    value = 0
    for x, y, z, c in a.tolist():
        value = (value + ((x * 73856093 & 0xffffffff) ^
                         (y * 19349663 & 0xffffffff) ^
                         (z * 83492791 & 0xffffffff) ^
                         (c * 2654435761 & 0xffffffff))) & 0xffffffff
    return value


def run():
    OUT.mkdir(exist_ok=True)
    cli(op='export', work=BASE + '-assembly', format='vxk',
        include='rig,models,parts,meta,ends', out=FINAL)
    repeat = OUT / 'repeat_export.vxk'
    cli(op='export', work=BASE + '-assembly', format='vxk',
        include='rig,models,parts,meta,ends', out=repeat)
    header, decoded = unpack(FINAL.read_bytes())
    repeat_header, repeat_decoded = unpack(repeat.read_bytes())
    differing_keys = [k for k in set(header) | set(repeat_header)
                      if header.get(k) != repeat_header.get(k)]
    assert set(differing_keys) <= {'exported_at'}, differing_keys
    assert np.array_equal(decoded, repeat_decoded), 'Repeat body mismatch'
    listed = OUT / 'current_body.list'
    cli(op='export', work=BASE + '-assembly', format='list', out=listed)
    actual = np.loadtxt(listed, delimiter=',', comments='#', dtype=np.int32,
                        ndmin=2, encoding='utf-8-sig')
    order = lambda a: a[np.lexsort((a[:, 2], a[:, 1], a[:, 0]))]
    a, b = order(actual), order(decoded)
    assert a.shape == b.shape and np.array_equal(a, b), 'CLI list / VXK mismatch'
    assert checksum(a) == header['checksum']
    bad = b.copy()
    bad[0, 3] = 1 if bad[0, 3] != 1 else 2
    assert checksum(bad) != header['checksum'], 'Tamper control is blind'
    old_header, old = unpack((ROOT / 'task0603/manual_candidate.vxk').read_bytes())
    assert np.array_equal(order(old), a), 'Anchor installation changed body voxels'
    rig = header['rig']
    assert rig['sails'] == old_header['rig']['sails'], 'Original sails changed'
    old_models = {m['name']: m for m in old_header['rig']['models']}
    for m in rig['models']:
        if m['name'] in old_models:
            previous = old_models[m['name']]
            assert {k: v for k, v in m.items() if k != 'mesh'} == {k: v for k, v in previous.items() if k != 'mesh'}, m['name']
            assert rig['meshes'][m['mesh']] == old_header['rig']['meshes'][previous['mesh']], m['name']
    old_ropes = {r['name']: r for r in old_header['rig']['ropes']}
    for r in rig['ropes']:
        if r['name'] in old_ropes:
            assert r == old_ropes[r['name']], r['name']
    assert len(rig['sails']) == 10
    assert len(rig['models']) == 168
    assert len(rig['ropes']) == 502
    assert sum(p.get('meta', {}).get('kind') == 'deck' for p in header['parts']) == 6
    assert all(r.get('ends') for r in rig['ropes'])
    evidence = ROOT / 'task0603/manual_final_smoke'
    shutil.copytree(Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/dynamic_qa/manual_final_smoke'),
                    evidence, dirs_exist_ok=True)
    manifest = {
        'observedAtUtc': datetime.now(timezone.utc).isoformat(),
        'work': BASE + '-assembly', 'delivery': str(FINAL),
        'sha256': hashlib.sha256(FINAL.read_bytes()).hexdigest(),
        'bytes': FINAL.stat().st_size, 'voxels': len(a),
        'checksum': f"{header['checksum']:08x}",
        'voxelAndColorDifferences': 0, 'bodyUnchangedFromManualCandidate': True,
        'repeatExportByteIdentical': FINAL.read_bytes() == repeat.read_bytes(),
        'repeatExportContentIdentical': True, 'repeatHeaderDifferences': differing_keys,
        'negativeControlChangedVoxels': 1,
        'negativeControlChecksum': f'{checksum(bad):08x}',
        'counts': {k: len(rig[k]) for k in ('ropes', 'sails', 'models', 'meshes')},
        'parts': len(header['parts']),
        'status': 'Author-side import handoff. Tim manual dynamic acceptance pending; known cloth penetration remains TASK-0603. Game integration belongs to ame.',
        'rebuildScope': 'Two equal current-state exports except exported_at timestamp, plus CLI/list cross-check; not a clean procedural reconstruction of all historical stages.',
    }
    (OUT / 'import_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    run()
