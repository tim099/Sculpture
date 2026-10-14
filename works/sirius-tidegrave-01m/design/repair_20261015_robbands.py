"""Two short robbands hold mizzen topsail head 0.4m forward of its yard.

No mast cells are removed. Named model-frame head anchors follow yard rotation.
"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_structure import cli, BASE


def main():
    assembly = BASE + '-assembly'
    source = BASE + '-yard-mizzen-topsail'
    work = ROOT.parent.parent / assembly
    original = ROOT / 'continued_20261015/before_robbands_sails.json'
    sails_before = json.loads((original if original.exists() else work / 'sails.json').read_text('utf8'))
    sail = next(s for s in sails_before['sails'] if s['name'] == 'mizzen-topsail')
    frame = 'model:mizzen/yard-mizzen-topsail/'
    corners = [c['at'] for c in sail['corners']]
    for j, side in enumerate(('P', 'S')):
        assert corners[j] in (frame + 'earing-' + side, frame + 'sail-head-' + side)
        corners[j] = frame + 'sail-head-' + side
    if '--apply' not in sys.argv:
        print('Two 4-cell robbands; mizzen-topsail upper corners:', corners[:2])
        return
    out = ROOT / 'continued_20261015'
    for filename in ('sails.json', 'ropes.json'):
        snap = out / ('before_robbands_' + filename)
        if not snap.exists():
            snap.write_bytes((work / filename).read_bytes())
    for side, y in [('P', 77), ('S', 163)]:
        cli(op='work', sub='anchor', work=source, name='sail-head-' + side,
            at=f'8,{y},4', overwrite=1,
            note='Sail head held by 0.4m robband tied to earing, not a timber attachment')
        cli(op='work', sub='rope', work=assembly, name='mizzen-topsail.robband-' + side,
            **{'from': frame + 'earing-' + side, 'to': frame + 'sail-head-' + side},
            slack=1, thickness=.25, color='#9f9673', group='running/robbands', overwrite=1)
    cli(op='work', sub='sail', work=assembly, name='mizzen-topsail',
        corners='|'.join(corners), free='clew-P,clew-S', overwrite=1)
    after = json.loads((work / 'sails.json').read_text('utf8'))
    expected = json.loads(json.dumps(sails_before))
    target = next(s for s in expected['sails'] if s['name'] == 'mizzen-topsail')
    for c, at in zip(target['corners'], corners):
        c['at'] = at
    assert after == expected, 'Unrelated sail field changed'
    print('Readback: only two sail-head references changed; other sail fields preserved.')


if __name__ == '__main__':
    main()
