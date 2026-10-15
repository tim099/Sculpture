"""Separate braces from lifts using measured outboard timber eyes and cap leads."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_structure import cli, BASE

OUT = ROOT / 'task0603'
WORK = BASE + '-assembly'
SOURCE = BASE + '-yard-mizzen-topsail'
MAST = BASE + '-mast-mizzen'
WORKS = ROOT.parent.parent


def run():
    before = json.loads((WORKS / WORK / 'ropes.json').read_text('utf8'))
    snapshot = OUT / 'ropes_before_two_stage.json'
    if not snapshot.exists():
        snapshot.write_text(json.dumps(before, ensure_ascii=False, indent=2), 'utf8')
    old = {r['name']: r for r in json.loads(snapshot.read_text('utf8'))['ropes']}
    model = next(m for m in json.loads((WORKS / MAST / 'models.json').read_text('utf8'))['models']
                 if m['name'] == 'yard-mizzen-topsail')
    assert model['at'] == [205.5, 120.5, 340.5]
    assert model['pivot'] == [4.5, 120.5, 4.5]
    assert model['rotate'] == [0, 0, -18] and model['scale'] == [1, 1, 1]
    for side, local_y, cap_y in [('P', 74, 119), ('S', 166, 121)]:
        cli(op='work', sub='anchor', work=SOURCE, name='brace-out-' + side,
            at=f'4,{local_y},4', overwrite=1,
            note='Actual yard timber, one cell outboard of the lift arm eye')
        cli(op='work', sub='anchor', work=WORK, name='mizzen-brace-guide-' + side,
            at=f'205,{cap_y},405', overwrite=1, note='Actual mizzen cap timber side eye')
        cli(op='work', sub='anchor', work=WORK, name='main-brace-guide-' + side,
            at=f'355,{cap_y},510', overwrite=1, note='Actual main cap timber side eye')
    cli(op='work', sub='model', work=MAST, name=model['name'], source_work=SOURCE,
        at='205.5,120.5,340.5', pivot='4.5,120.5,4.5', rotate='0,0,-18', scale=1,
        meta=json.dumps(model['meta']), overwrite=1)
    after_model = next(m for m in json.loads((WORKS / MAST / 'models.json').read_text('utf8'))['models']
                       if m['name'] == model['name'])
    assert after_model == model, 'Model transform/meta unexpectedly changed'
    for side in ('P', 'S'):
        name = 'mizzen-topsail.brace-' + side
        original = old[name]
        cli(op='work', sub='rope', work=WORK, name=name,
            **{'from': 'model:mizzen/yard-mizzen-topsail/brace-out-' + side},
            to='mizzen-brace-guide-' + side, overwrite=1)
        cli(op='work', sub='rope', work=WORK, name=name + '.upper',
            **{'from': 'mizzen-brace-guide-' + side}, to='main-brace-guide-' + side,
            slack=1, thickness=.4, color=original['color'], group=original['group'], overwrite=1)
        if original.get('meta'):
            cli(op='work', sub='meta', work=WORK, part='rope', name=name + '.upper',
                meta=json.dumps(original['meta']))
    cli(op='export', work=WORK, format='vxk', include='rig,models,parts,meta,ends',
        out=OUT / 'two_stage_candidate.vxk')
    print('Two-stage brace export complete; source timber, original eyes and all sail records retained.')


if __name__ == '__main__':
    run()
