"""Upper braces lead to supported adjacent-mast blocks, not through lower yards."""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'audits/20261014/yard_sweep'))
from build_structure import cli, BASE
from vxk_decode import unpack

OUT = ROOT / 'continued_20261015'
ASSEMBLY = BASE + '-assembly'


def main():
    _, vox = unpack((OUT / 'after_standing.vxk').read_bytes())
    occupied = {tuple(v[:3]) for v in vox}
    path = ROOT.parent.parent / ASSEMBLY / 'ropes.json'
    before = json.loads(path.read_text('utf8'))
    by = {r['name']: r for r in before['ropes']}
    plan = []
    for mast, yard, target_mast, target_anchor in [
        ('main', 'topsail', 'mizzen', 'truck'),
        ('main', 'topgallant', 'mizzen', 'truck'),
        ('fore', 'topsail', 'main', 'head'),
        ('fore', 'topgallant', 'main', 'truck'),
        ('mizzen', 'topsail', 'main', 'hounds-{}'),
    ]:
        ap = ROOT.parent.parent / (BASE + '-mast-' + target_mast) / 'anchors.json'
        anchors = {a['name']: a['at'] for a in json.loads(ap.read_text('utf8'))['anchors']}
        for side in ('P', 'S'):
            anchor = target_anchor.format(side)
            point = anchors[anchor]
            assert tuple(point) in occupied, ('unsupported target', target_mast, anchor)
            name = f'{mast}-{yard}.brace-{side}'
            r = by[name]
            assert r['from'] == f'model:{mast}/yard-{mast}-{yard}/arm-{side}'
            plan.append({'name': name, 'from': r['from'],
                         'to': f'{target_mast}/{anchor}', 'point': point})
    (OUT / 'brace_plan.json').write_text(json.dumps(plan, indent=2) + '\n', 'utf8')
    print('Supported adjacent-mast targets:', len(plan), flush=True)
    if '--apply' not in sys.argv:
        print('Dry-run only. Actual curve and dynamic sweep still require audit.')
        return
    snapshot = OUT / 'ropes_before_braces.json'
    if not snapshot.exists():
        snapshot.write_text(json.dumps(before, indent=2) + '\n', 'utf8')
    for p in plan:
        r = by[p['name']]
        if r['to'] == p['to'] and r['slack'] == 1:
            continue
        cli(op='work', sub='rope', work=ASSEMBLY, name=p['name'],
            **{'from': p['from'], 'to': p['to']}, slack=1, overwrite=1)
    after = json.loads(path.read_text('utf8'))
    ab = {r['name']: r for r in after['ropes']}
    targets = {p['name']: p for p in plan}
    assert len(by) == len(ab)
    for name, r in by.items():
        expected = dict(r)
        if name in targets:
            expected.update(to=targets[name]['to'], slack=1)
        assert expected == ab[name], ('unexpected rope change', name)
    (OUT / 'ropes_after_braces.json').write_text(json.dumps(after, indent=2) + '\n', 'utf8')
    print('Readback: 10 brace targets/slack; every other rope field preserved.')


if __name__ == '__main__':
    main()
