"""Reviewed dynamic-audit corrections; all sculpture writes use Senate CLI.

The jib head ring sits on the existing forestay, not on imaginary timber.
Keep the original snapshot and corner freedom; do not rebuild other rigging.
"""
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'audits/20261014/yard_sweep'))
from build_structure import cli, BASE, get_actual
from vxk_decode import unpack

OUT = ROOT / 'dynamic_20261015'
WORK = ROOT.parent.parent / (BASE + '-assembly')


def jib():
    header, _ = unpack((ROOT / 'continued_20261015/final_heads.vxk').read_bytes())
    stay = next(r for r in header['rig']['ropes'] if r['name'] == 'fore-stay')
    pts = np.array(stay['pts']).reshape(-1, 3)
    lengths = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    arc = np.r_[0, np.cumsum(lengths)]
    head = [float(np.interp(.3 * arc[-1], arc, pts[:, a])) for a in range(3)]
    corners = ['bowsprit/tip', 'jib-head-stay-ring', '600.5,145.5,190.5']
    before = json.loads((WORK / 'sails.json').read_text('utf8'))
    sail = next(s for s in before['sails'] if s['name'] == 'jib')
    assert [c['at'] for c in sail['corners']] in [
        ['bowsprit/tip', 'fore/head', '600.5,145.5,145.5'], corners]
    OUT.mkdir(exist_ok=True)
    (OUT / 'jib_plan.json').write_text(json.dumps({
        'stay_head_ratio': .3, 'head_ring': head, 'corners': corners,
        'reason': 'Clear original bowsprit and fore-topsail intersections',
    }, indent=2) + '\n', 'utf8')
    print('Jib plan:', head, corners, flush=True)
    if '--apply' not in sys.argv:
        return
    snap = OUT / 'sails_before_dynamic.json'
    if not snap.exists():
        snap.write_text(json.dumps(before, indent=2) + '\n', 'utf8')
    cli(op='work', sub='anchor', work=BASE + '-assembly',
        name='jib-head-stay-ring', at=','.join(str(int(np.floor(a))) for a in head),
        overwrite=1, note='Jib head ring on actual fore-stay at 30 percent arc length')
    cli(op='work', sub='sail', work=BASE + '-assembly', name='jib',
        corners='|'.join(corners), free='clew', overwrite=1)
    after = json.loads((WORK / 'sails.json').read_text('utf8'))
    expected = json.loads(json.dumps(before))
    for s in expected['sails']:
        if s['name'] == 'jib':
            for c, at in zip(s['corners'], corners):
                c['at'] = at
    assert after == expected, 'Unrelated sail field or pin changed'
    cli(op='export', work=BASE + '-assembly', format='vxk',
        include='rig,models,parts,meta,ends', out=OUT / 'candidate_jib.vxk')
    print('Readback: only jib corner references changed; clew remains free.')


def standing():
    _, vox = unpack((ROOT / 'continued_20261015/final_heads.vxk').read_bytes())
    path = WORK / 'ropes.json'
    before = json.loads(path.read_text('utf8'))
    by = {r['name']: r for r in before['ropes']}
    plan = []
    targets = {}
    for j, x in enumerate((290, 310, 330)):
        for side in ('P', 'S'):
            # Inboard deck tie points separate the crossing fore-led mizzen
            # shrouds from the aft-led main shrouds. The first rail candidate
            # cleared wood but introduced six rope/rope crossings and is rejected.
            y = 86 if side == 'P' else 154
            assert np.any(np.all(vox[:, :3] == [x, y, 115], axis=1))
            anchor = f'mizzen-standing-chain-{side}{j}'
            name = f'mizzen-shroud-{side}{j}'
            assert by[name]['from'] in (f'mizzen-chain-{side}{j}', anchor)
            plan.append({'name': anchor, 'at': [x, y, 115]})
            targets[name] = {'from': anchor}
    for side in ('P', 'S'):
        targets[f'mizzen-ratline-{side}-1'] = {
            'from': f'rope:mizzen-shroud-{side}0/0.065',
            'to': f'rope:mizzen-shroud-{side}2/0.065'}
    OUT.mkdir(exist_ok=True)
    (OUT / 'mizzen_standing_plan.json').write_text(json.dumps({
        'anchors': plan, 'rope_fields': targets,
        'independent_candidate': 'yard_verifier/candidate_forward065/report.json',
        'rejected': 'aft feet cross boom/gaff; forward rail feet cross main shrouds; original first ratio .04 crosses rail',
    }, indent=2) + '\n', 'utf8')
    print('Standing plan:', plan, flush=True)
    if '--apply' not in sys.argv:
        return
    snap = OUT / 'ropes_before_dynamic.json'
    if not snap.exists():
        snap.write_text(json.dumps(before, indent=2) + '\n', 'utf8')
    for p in plan:
        cli(op='work', sub='anchor', work=BASE + '-assembly', name=p['name'],
            at=','.join(map(str, p['at'])), overwrite=1,
            note='Forward inboard mizzen tie on real weather deck, separated from main shrouds')
    for name, fields in targets.items():
        cli(op='work', sub='rope', work=BASE + '-assembly', name=name,
            overwrite=1, **fields)
    after = json.loads(path.read_text('utf8'))
    expected = json.loads(json.dumps(before))
    for r in expected['ropes']:
        r.update(targets.get(r['name'], {}))
    assert after == expected, 'Unrelated rope field changed'
    cli(op='export', work=BASE + '-assembly', format='vxk',
        include='rig,models,parts,meta,ends', out=OUT / 'candidate_standing.vxk')
    print('Readback: only six shroud feet and two first-ratline ratios changed.')


def fairlead():
    before = get_actual(BASE)
    intended = {}
    # Supported outboard brackets: a two-cell-deep beam rooted in the existing
    # stern rail, plus its four-cell upright. Mirror the unused bracket as timber.
    for side in ('P', 'S'):
        rail = [y for x, y, z in before if x == 145 and z == 185]
        assert rail, 'No real stern rail at bracket root'
        root = min(rail) if side == 'P' else max(rail)
        tip = 86 if side == 'P' else 154
        for y in range(min(root, tip), max(root, tip) + 1):
            for z in (185, 186):
                intended[(145, y, z)] = 109
        for z in range(187, 191):
            intended[(145, tip, z)] = 109
    missing = {q: c for q, c in intended.items() if q not in before}
    OUT.mkdir(exist_ok=True)
    voxfile = OUT / 'lateen_brackets.vox.txt'
    voxfile.write_text(''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c
                               in sorted(missing.items())), 'utf8')
    print('Fairlead: mirrored rooted brackets, new cells', len(missing), flush=True)
    if '--apply' not in sys.argv:
        return
    if missing:
        result = cli(op='stampvox', work=BASE, voxels=voxfile, at='0,0,0',
                     expect_pixels=len(missing), share=0)
        assert int(result.get('placed', -1)) == len(missing)
    cli(op='work', sub='anchor', work=BASE + '-assembly',
        name='fairlead-mizzen-lateen-sheet-P', at='145,86,190', overwrite=1,
        note='Supported outboard bracket on existing stern rail; sheet exits boom end')
    actual = get_actual(BASE)
    assert all(actual.get(q) == c for q, c in before.items())
    assert all(actual.get(q) == c for q, c in missing.items())
    assert len(actual) == len(before) + len(missing)
    delta = OUT / 'bracket_delta.json'
    result = {
        'added_cells': len(missing), 'existing_cells_unchanged': len(before),
        'only_added': [list(q) + [c] for q, c in sorted(missing.items())],
        'sheet_endpoint': [145.5, 86.5, 190.5], 'beam_z': [185, 186],
        'upright_z': [187, 190],
    }
    if missing or not delta.exists():
        delta.write_text(json.dumps(result, indent=2) + '\n', 'utf8')
    cli(op='export', work=BASE + '-assembly', format='vxk',
        include='rig,models,parts,meta,ends', out=OUT / 'final_dynamic.vxk')
    print('Readback: exact bracket addition; existing body unchanged.')


def backstays():
    _, vox = unpack((OUT / 'final_dynamic.vxk').read_bytes())
    points = {'mizzen-backstay-aft-head': [204, 120, 405],
              'mizzen-crown-backstay-P': [84, 70, 226],
              'mizzen-crown-backstay-S': [84, 170, 226]}
    for q in points.values():
        assert np.any(np.all(vox[:, :3] == q, axis=1)), ('No physical root', q)
    path = WORK / 'ropes.json'
    before = json.loads(path.read_text('utf8'))
    if '--apply' not in sys.argv:
        print('Crown-supported aft backstays:', points)
        return
    snap = OUT / 'ropes_before_backstays.json'
    if not snap.exists():
        snap.write_text(json.dumps(before, indent=2) + '\n', 'utf8')
    for name, at in points.items():
        cli(op='work', sub='anchor', work=BASE + '-assembly', name=name,
            at=','.join(map(str, at)), overwrite=1,
            note='Existing solid mast tip / rooted coral-crown horn used as backstay attachment')
    for side in ('P', 'S'):
        cli(op='work', sub='rope', work=BASE + '-assembly',
            name='mizzen-backstay-' + side,
            **{'from': 'mizzen-backstay-aft-head', 'to': 'mizzen-crown-backstay-' + side},
            overwrite=1)
    expected = json.loads(json.dumps(before))
    for r in expected['ropes']:
        if r['name'] in ('mizzen-backstay-P', 'mizzen-backstay-S'):
            r['from'] = 'mizzen-backstay-aft-head'
            r['to'] = 'mizzen-crown-backstay-' + r['name'][-1]
    assert json.loads(path.read_text('utf8')) == expected
    cli(op='export', work=BASE + '-assembly', format='vxk',
        include='rig,models,parts,meta,ends', out=OUT / 'final_dynamic.vxk')
    print('Readback: only two aft backstay attachments changed; all actual roots retained.')


if __name__ == '__main__':
    if '--standing' in sys.argv:
        standing()
    elif '--fairlead' in sys.argv:
        fairlead()
    elif '--backstays' in sys.argv:
        backstays()
    else:
        jib()
