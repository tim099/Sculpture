"""Six independently measured rigging corrections; all work writes use CLI."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_structure import cli, BASE

OUT = ROOT / 'task0603'
WORK = BASE + '-assembly'
WORKDIR = ROOT.parent.parent / WORK


def run():
    before = json.loads((WORKDIR / 'ropes.json').read_text('utf8'))
    snapshot = OUT / 'ropes_before_clear_routes.json'
    if not snapshot.exists():
        snapshot.write_text(json.dumps(before, ensure_ascii=False, indent=2), 'utf8')
    expected = json.loads(snapshot.read_text('utf8'))
    changes = {
        'fore-topsail.brace-P': {'to': 'main/truck'},
        'fore-topsail.brace-S': {'to': 'main/truck'},
        'mizzen-topsail.brace-P': {'to': 'main/truck'},
        'mizzen-topsail.brace-S': {'to': 'main/truck'},
        'mizzen-stay': {'from': 'mizzen/truck', 'to': 'main/truck'},
        'jib.sheet-S': {'to': 'fairlead-jib-sheet-forward-S'},
    }
    original = {r['name']: r for r in expected['ropes']}
    for rope in before['ropes']:
        old = original[rope['name']]
        target = dict(old, **changes.get(rope['name'], {}))
        assert rope == old or rope == target, ('Unexpected concurrent rope change', rope['name'])
    cli(op='work', sub='anchor', work=WORK, name='fairlead-jib-sheet-forward-S',
        at='595,140,158', overwrite=1,
        note='Real forecastle bulwark timber; forward of fore-course swept area')
    for name, values in changes.items():
        cli(op='work', sub='rope', work=WORK, name=name, overwrite=1, **values)
    for rope in expected['ropes']:
        rope.update(changes.get(rope['name'], {}))
    after = json.loads((WORKDIR / 'ropes.json').read_text('utf8'))
    assert after == expected, 'Unrelated rope fields changed'
    cli(op='export', work=WORK, format='vxk', include='rig,models,parts,meta,ends',
        out=OUT / 'routes_candidate.vxk')
    print('Readback: only six routes changed; existing pin/sail/yard geometry untouched.')


if __name__ == '__main__':
    run()
