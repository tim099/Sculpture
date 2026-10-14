"""Lift four lowest ratlines above rail timber, preserving the climbing ropes."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_structure import cli, BASE


def main():
    path = ROOT.parent.parent / (BASE + '-assembly') / 'ropes.json'
    before = json.loads(path.read_text('utf8'))
    by = {r['name']: r for r in before['ropes']}
    targets = {}
    for mast in ('main', 'fore'):
        for side in ('P', 'S'):
            name = f'{mast}-ratline-{side}-1'
            r = by[name]
            frm, to = f'rope:{mast}-shroud-{side}0/0.065', f'rope:{mast}-shroud-{side}2/0.065'
            assert r['from'] in (f'rope:{mast}-shroud-{side}0/0.04', frm)
            targets[name] = (frm, to)
    if '--apply' not in sys.argv:
        print(targets)
        return
    snap = ROOT / 'continued_20261015/ropes_before_ratline_feet.json'
    if not snap.exists():
        snap.write_text(json.dumps(before, indent=2) + '\n', 'utf8')
    for name, (frm, to) in targets.items():
        if by[name]['from'] != frm:
            cli(op='work', sub='rope', work=BASE + '-assembly', name=name,
                **{'from': frm, 'to': to}, overwrite=1)
    after = json.loads(path.read_text('utf8'))
    assert len(after['ropes']) == len(by)
    for r in after['ropes']:
        expected = dict(by[r['name']])
        if r['name'] in targets:
            expected['from'], expected['to'] = targets[r['name']]
        assert r == expected
    print('Four lowest ratlines raised from parent ratio .04 to .065; all other fields preserved.')


if __name__ == '__main__':
    main()
