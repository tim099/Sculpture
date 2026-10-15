"""Keep sail pins fixed and route standing rigging through measured real eyes.

Independent standing_cases/standing_continuous proofs live in the TASK-0603
attachment_audit/route_explore evidence. All sculpture mutations use Senate CLI.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_structure import cli, BASE

WORK = BASE + '-assembly'
WD = ROOT.parent.parent / WORK
OUT = ROOT / 'task0603'


def run():
    sails_before = (WD / 'sails.json').read_bytes()
    before = json.loads((WD / 'ropes.json').read_text('utf8'))
    saved = OUT / 'ropes_before_standing.json'
    if not saved.exists():
        saved.write_text(json.dumps(before, ensure_ascii=False, indent=2), 'utf8')
    original = {r['name']: r for r in json.loads(saved.read_text('utf8'))['ropes']}
    for side, y in [('P', 73), ('S', 167)]:
        cli(op='work', sub='anchor', work=WORK,
            name='fore-backstay-foot-clear-' + side, at=f'450,{y},128',
            overwrite=1, note='Measured real bulwark wood; clear of main course sweep')
        cli(op='work', sub='rope', work=WORK, name='fore-backstay-' + side,
            to='fore-backstay-foot-clear-' + side, overwrite=1)
    cli(op='work', sub='rope', work=WORK, name='main-stay',
        **{'from': 'main/truck'}, to='fore/truck', overwrite=1)
    cli(op='work', sub='rope', work=WORK, name='fore-stay',
        **{'from': 'jib-head-stay-ring'}, to='bowsprit/tip', overwrite=1)
    cli(op='work', sub='rope', work=WORK, name='jib-halyard',
        **{'from': 'fore/truck'}, to='jib-head-stay-ring', thickness=.4,
        slack=1, color=original['fore-stay']['color'], group='running/jib', overwrite=1)
    assert (WD / 'sails.json').read_bytes() == sails_before, 'Sail records changed'
    after = json.loads((WD / 'ropes.json').read_text('utf8'))
    changed = {'main-stay', 'fore-stay', 'fore-backstay-P', 'fore-backstay-S', 'jib-halyard'}
    for r in after['ropes']:
        if r['name'] not in changed:
            assert r == original[r['name']], r['name']
    cli(op='export', work=WORK, format='vxk', include='rig,models,parts,meta,ends',
        out=OUT / 'manual_candidate.vxk')
    print('Exported manual_candidate.vxk; sail records and original sail attachment points retained.')


if __name__ == '__main__':
    run()
