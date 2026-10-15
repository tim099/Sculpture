"""Package finished evidence, never alter a live work or engine file."""
from pathlib import Path
import json
import gzip
import hashlib
import shutil

ROOT = Path(__file__).resolve().parent / 'dynamic_20261015'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    final = ROOT / 'independent_final'
    rope = json.loads((final / 'rope_verifier/dynamic.json').read_text('utf8'))
    cloth = json.loads((final / 'cloth_verifier/matrix.json').read_text('utf8'))
    assert rope['frames'] == 249 and len(cloth['reports']) == 20
    assert cloth['file'].endswith('final_dynamic.vxk')
    old = ROOT / 'independent'
    if old.exists():
        shutil.copy2(old / 'rope_verifier/rope_pairs.json', ROOT / 'rejected_rail_feet_pairs.json')
        shutil.copy2(old / 'rope_verifier/frozen/final_heads.vxk', ROOT / 'rejected_rail_feet.vxk')
    hashes = []
    for folder in (final / 'rope_verifier', final / 'cloth_verifier'):
        for path in sorted(folder.iterdir()):
            if (path.name.startswith('trajectory') and path.suffix == '.json') or path.suffix == '.jsonl':
                data = path.read_bytes()
                hashes.append({'path': path.relative_to(ROOT).as_posix(),
                               'bytes': len(data), 'sha256': sha(data)})
                packed = gzip.compress(data, compresslevel=9, mtime=0)
                target = path.with_name(path.name + '.gz')
                target.write_bytes(packed)
                assert gzip.decompress(target.read_bytes()) == data
                path.unlink()
    (ROOT / 'trajectory_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n', 'utf8')
    for p in sorted(ROOT.rglob('__pycache__'), reverse=True):
        # Owned generated cache only. The parent path is explicitly constrained.
        assert p.resolve().is_relative_to(ROOT.resolve())
        shutil.rmtree(p)
    for p in (final / 'yard_verifier/MANIFEST.json',):
        if p.exists():
            p.unlink()  # Superseded by the complete final package manifest below.
    records = []
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or p == ROOT / 'MANIFEST.json' or old in p.parents:
            continue
        data = p.read_bytes()
        records.append({'path': p.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
    (ROOT / 'MANIFEST.json').write_text(json.dumps(records, indent=2) + '\n', 'utf8')
    print('Files', len(records), 'bytes', sum(r['bytes'] for r in records), 'gzip trajectories', len(hashes))


if __name__ == '__main__':
    main()
