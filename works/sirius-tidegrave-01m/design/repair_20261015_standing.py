"""Move main/fore shroud feet aft onto existing rail timber, through CLI.

Each rope remains a single line, so all ratlines keep their parent references.
Old chain anchors remain for braces/sheets. No voxels are changed.
"""
import sys, json, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'audits/20261014/yard_sweep'))
from build_structure import cli, BASE
from vxk_decode import unpack

ASSEMBLY = BASE + '-assembly'
OUT = ROOT / 'continued_20261015'


def main():
    h, vox = unpack((OUT / 'after_lifts.vxk').read_bytes())
    rope_path = ROOT.parent.parent / ASSEMBLY / 'ropes.json'
    original = json.loads(rope_path.read_text('utf8'))
    by = {r['name']: r for r in original['ropes']}
    anchors_path = ROOT.parent.parent / ASSEMBLY / 'anchors.json'
    existing = {a['name']: a['at'] for a in json.loads(anchors_path.read_text('utf8'))['anchors']}
    # Conservative continuous +/-0.70 rad strip bound, including voxel width,
    # rope radius and 0.5 cell extra margin. Candidate selection is not an audit.
    specs = [('main', 355, 295, 510, [250, 375, 460]),
             ('fore', 510, 275, 465, [235, 340, 420])]
    plan = []
    for mast, mx, top, truck, levels in specs:
        for j, aft in enumerate([120, 100, 80]):
            x = mx - aft
            at_z = vox[(vox[:, 0] == x) & (vox[:, 2] == 128)]
            assert len(at_z), ('No rail timber', mast, x)
            for side, sign in [('P', -1), ('S', 1)]:
                y = int(at_z[:, 1].min() if sign < 0 else at_z[:, 1].max())
                p = [x, y, 128]
                anchor = f'{mast}-standing-chain-{side}{j}'
                assert anchor not in existing or existing[anchor] == p
                ropes = [(f'{mast}-shroud-{side}{j}', top, f'{mast}/hounds-{side}')]
                if j == 0:
                    ropes.append((f'{mast}-backstay-{side}', truck, f'{mast}/truck'))
                for name, zhi, endpoint in ropes:
                    r = by[name]
                    lower = np.array(p, float) + .5
                    upper = np.array([mx + .5, 120.5 + (sign * 4 if 'shroud' in name else 0), zhi + .5])
                    bounds = []
                    for level in levels:
                        for z in [level - 2.7, level + 2.7]:
                            if lower[2] <= z <= upper[2]:
                                t = (z - lower[2]) / (upper[2] - lower[2])
                                q = lower + (upper - lower) * t
                                dx, dy = abs(q[0] - mx - .5), abs(q[1] - 120.5)
                                gap = dx * math.cos(.70) - dy * math.sin(.70) - 2.5 - .4
                                assert gap > .5, ('fails continuous strip bound', name, z, gap)
                                bounds.append({'z': z, 'conservative_gap': gap})
                    if 'shroud' in name:
                        frm, to = anchor, endpoint
                    else:
                        frm, to = endpoint, anchor
                    assert r['from'] in (frm, f'{mast}-chain-{side}{j}') if 'shroud' in name else r['from'] == frm
                    plan.append({'name': name, 'anchor': anchor, 'point': p,
                                 'from': frm, 'to': to, 'bounds': bounds})
    (OUT / 'standing_plan.json').write_text(json.dumps(plan, indent=2) + '\n', 'utf8')
    print('Candidate routes:', len(plan), 'minimum own-mast strip gap:',
          min(b['conservative_gap'] for p in plan for b in p['bounds']), flush=True)
    if '--apply' not in sys.argv:
        print('Dry-run only; existing rail roots and conservative own-mast envelope checked.')
        return
    before = OUT / 'ropes_before_standing.json'
    if not before.exists():
        before.write_text(json.dumps(original, indent=2) + '\n', 'utf8')
    written = set()
    for p in plan:
        if p['anchor'] not in written:
            cli(op='work', sub='anchor', work=ASSEMBLY, name=p['anchor'],
                at=','.join(map(str, p['point'])), overwrite=1,
                note='20261015 aft standing-rig foot; existing rail cell, no brace anchor moved')
            written.add(p['anchor'])
        r = by[p['name']]
        if (r['from'], r['to']) != (p['from'], p['to']):
            cli(op='work', sub='rope', work=ASSEMBLY, name=p['name'],
                **{'from': p['from'], 'to': p['to']}, overwrite=1)
    after = json.loads(rope_path.read_text('utf8'))
    after_by = {r['name']: r for r in after['ropes']}
    targets = {p['name']: p for p in plan}
    assert len(by) == len(after_by)
    for name, r in by.items():
        expected = dict(r)
        if name in targets:
            expected.update({k: targets[name][k] for k in ('from', 'to')})
        assert expected == after_by[name], ('unexpected field change', name)
    (OUT / 'ropes_after_standing.json').write_text(json.dumps(after, indent=2) + '\n', 'utf8')
    print('Readback: all 16 standing lines rerouted; other rope fields and all ratline references preserved.')


if __name__ == '__main__':
    main()
