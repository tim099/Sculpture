"""Package the independently written verifiers; select one frozen final input.

No verification algorithm is changed here. The parent executes the independent
implementations after the verifier agents stopped; provenance records this.
"""
from pathlib import Path
import shutil
import json
import hashlib

HERE = Path(__file__).resolve().parent
OUT = HERE / 'dynamic_20261015'
SRC = Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/dynamic_20261015')
DEST = OUT / 'independent_final'
FINAL = OUT / 'final_dynamic.vxk'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare():
    if (DEST / 'rope_verifier/provenance.json').exists():
        raise RuntimeError('Evidence already prepared. Rerun the bundled checks; do not overwrite their final input adapters.')
    for name in ('rope_verifier', 'cloth_verifier', 'yard_verifier'):
        source, dest = SRC / name, DEST / name
        dest.mkdir(parents=True, exist_ok=True)
        for p in source.iterdir():
            if p.is_file() and p.suffix in ('.py', '.cjs', '.js', '.md'):
                shutil.copy2(p, dest / p.name)
        original = dest / 'original_results'
        original.mkdir(exist_ok=True)
        for p in source.glob('*.json'):
            if p.name != 'trajectory.json':
                shutil.copy2(p, original / p.name)
    rope = DEST / 'rope_verifier'
    shutil.copytree(SRC / 'rope_verifier/frozen', rope / 'frozen', dirs_exist_ok=True)
    shutil.copy2(FINAL, rope / 'frozen/final_heads.vxk')
    (rope / 'provenance.json').write_text(json.dumps({
        'input': 'frozen/final_heads.vxk', 'sha256': sha(FINAL),
        'original_name_note': 'Stable historical basename; bytes are final_dynamic.vxk',
        'source': [{ 'file': p.name, 'sha256': sha(p)}
                   for p in sorted((rope / 'frozen').glob('*.js'))],
        'verifier_author': '/root/all_rope_dynamic', 'final_executor': 'Sirius parent',
    }, indent=2) + '\n', 'utf8')
    cloth = DEST / 'cloth_verifier'
    shutil.copytree(SRC / 'cloth_verifier/frozen_source', cloth / 'frozen_source', dirs_exist_ok=True)
    for name in ('09_phx.js', '32_hull.js', '34_shreds.js'):
        shutil.copy2(SRC / 'cloth_verifier/candidate_standing/frozen_source/src/js' / name,
                     cloth / 'frozen_source/src/js' / name)
    yard = DEST / 'yard_verifier'
    shutil.copytree(SRC / 'yard_verifier/input', yard / 'input', dirs_exist_ok=True)
    shutil.copy2(FINAL, yard / 'input/final_heads.vxk')
    for sub in ('candidate', 'candidate_forward', 'candidate_forward065', 'actual_standing'):
        shutil.copytree(SRC / 'yard_verifier' / sub, yard / sub, dirs_exist_ok=True)
    shutil.copy2(FINAL, yard / 'actual_standing/candidate_standing.vxk')
    print('Prepared final independent inputs:', sha(FINAL))


if __name__ == '__main__':
    prepare()
