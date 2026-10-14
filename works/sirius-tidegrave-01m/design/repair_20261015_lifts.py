"""Reroute only lower lifts; source mast cells and all ropes are preserved.

Dry-run first. Every write uses Senate; never call initial construction main().
"""
import sys, json, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_structure import cli, BASE

ASSEMBLY = BASE + '-assembly'
OUT = ROOT / 'continued_20261015'


def get_actual(work):
    path = OUT / (work + '.list.txt')
    cli(op='export', work=work, format='list', links='none', out=path)
    return {tuple(map(int, line.split(',')[:3])): int(line.split(',')[3])
            for line in path.read_text('utf-8-sig').splitlines()
            if line and not line.startswith('#')}


def main():
    OUT.mkdir(exist_ok=True)
    rope_path = ROOT.parent.parent / ASSEMBLY / 'ropes.json'
    original = json.loads(rope_path.read_text('utf8'))
    by = {r['name']: r for r in original['ropes']}
    plan = []
    for mast, x, z in [('main', 355, 420), ('fore', 510, 380)]:
        actual = get_actual(BASE + '-mast-' + mast)
        anchors = json.loads((ROOT.parent.parent / (BASE + '-mast-' + mast) / 'anchors.json').read_text('utf8'))
        anchors = {a['name']: a['at'] for a in anchors['anchors']}
        for side, sign in [('P', -1), ('S', 1)]:
            for yard in ['course', 'topsail']:
                name = f'{mast}-{yard}.lift-{side}'
                anchor = f'hounds-{side}' if yard == 'course' else f'topsail-lift-{side}'
                point = anchors[anchor] if yard == 'course' else [x, 120 + sign * 2, z]
                assert tuple(point) in actual, ('unsupported anchor', mast, anchor, point)
                r = by[name]
                target = f'{mast}/{anchor}'
                assert r['from'] == f'model:{mast}/yard-{mast}-{yard}/arm-{side}'
                assert r['to'] in (f'{mast}/truck', target), (name, r['to'])
                plan.append({'name': name, 'work': BASE + '-mast-' + mast,
                             'anchor': anchor, 'point': point, 'to': target,
                             'from': r['from'], 'already': r['to'] == target})
    (OUT / 'lift_plan.json').write_text(json.dumps(plan, indent=2) + '\n', 'utf8')
    print(json.dumps(plan, indent=2), flush=True)
    if '--apply' not in sys.argv:
        print('Dry-run: supported mast cells verified; add --apply to write through Senate.')
        return
    before = OUT / 'ropes_before_lifts.json'
    if not before.exists():
        before.write_text(json.dumps(original, indent=2) + '\n', 'utf8')
    for p in plan:
        if p['already']:
            continue
        if p['anchor'].startswith('topsail-'):
            cli(op='work', sub='anchor', work=p['work'], name=p['anchor'],
                at=','.join(map(str, p['point'])), overwrite=1,
                note='20261015: supported mast-side lift attachment below next yard')
        cli(op='work', sub='rope', work=ASSEMBLY, name=p['name'],
            **{'from': p['from'], 'to': p['to']}, overwrite=1)
    after = json.loads(rope_path.read_text('utf8'))
    after_by = {r['name']: r for r in after['ropes']}
    assert len(after_by) == len(by)
    targets = {p['name']: p['to'] for p in plan}
    for name, r in by.items():
        expected = dict(r)
        if name in targets:
            expected['to'] = targets[name]
        assert expected == after_by[name], ('Unexpected rope field change', name)
    (OUT / 'ropes_after_lifts.json').write_text(json.dumps(after, indent=2) + '\n', 'utf8')
    print('Readback: 8 target lift endpoints; all other rope fields unchanged.')


if __name__ == '__main__':
    main()
