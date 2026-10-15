"""Install existing shared bower anchors at independently checked author poses."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_structure import cli, BASE


def run():
    evidence = Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/attachment_audit/anchors_final/DESIGN.json')
    plan = json.loads(evidence.read_text('utf8'))
    work = BASE + '-assembly'
    wd = ROOT.parent.parent / work
    original_sails = (wd / 'sails.json').read_bytes()
    for p in plan['placements']:
        assert p['anchor_body_penetrations'] == 0
        assert not p['anchor_model_contacts'] and not p['anchor_old_rope_contacts']
        assert not p['cable_model_contacts'] and not p['cable_old_rope_contacts']
        assert p['nearest_wood_center'] < 8
        side = p['side']
        # Part-level points are consumed by the game's anchor setup; root assembly
        # points alone are not exported as header.parts points.
        cli(op='work', sub='anchor', work=BASE, name='hawse-' + side,
            at=','.join(map(str, p['hawse_at_cell'])), overwrite=1,
            note='Measured solid bow fastening for the bower anchor cable')
        cli(op='work', sub='model', work=work, name='anchor-' + side,
            source_work=p['source'], at=','.join(map(str, p['at'])),
            pivot=','.join(map(str, p['pivot'])), rotate=','.join(map(str, p['rotate'])),
            scale=1, overwrite=1, meta=json.dumps({'kind': 'anchor', 'anchor': 'bower'}))
        cli(op='work', sub='rope', work=work, name='anchor-cable-' + side,
            **{'from': 'model:anchor-' + side + '/ring'}, to='船殼/hawse-' + side,
            thickness=.7, slack=1, color='#51493c', group='anchors/bower', overwrite=1)
    assert (wd / 'sails.json').read_bytes() == original_sails
    out = ROOT / 'delivery/anchor_placement.json'
    out.write_bytes(evidence.read_bytes())
    print('Two shared bower anchors installed; all original sail records preserved.')


if __name__ == '__main__':
    run()
