from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parent
hashes = json.loads((ROOT / 'trajectory_hashes.json').read_text('utf8'))
for row in hashes:
    raw = ROOT / row['path']
    packed = raw.with_name(raw.name + '.gz')
    if not raw.exists():
        data = gzip.decompress(packed.read_bytes())
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        raw.write_bytes(data)
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == row['sha256']
    print(row['path'])
