"""Shift main standing feet forward 1m, away from raised quarter rail/posts."""
import sys, json, math
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'audits/20261014/yard_sweep'))
from build_structure import cli, BASE
from vxk_decode import unpack


def main():
    OUT = ROOT / 'continued_20261015'
    _, vox = unpack((OUT / 'after_robbands.vxk').read_bytes())
    path = ROOT.parent.parent / (BASE + '-assembly') / 'anchors.json'
    before = json.loads(path.read_text('utf8'))
    ab = {a['name']: a for a in before['anchors']}
    plan = []
    for j, x in enumerate([245, 265, 285]):
        cells = vox[(vox[:, 0] == x) & (vox[:, 2] == 128)]
        assert len(cells)
        for side in ('P', 'S'):
            y = int(cells[:, 1].min() if side == 'P' else cells[:, 1].max())
            name = f'main-standing-chain-{side}{j}'
            assert ab[name]['at'][0] in (x - 10, x)
            point = [x, y, 128]
            gaps = []
            for z in [247.3, 252.7]:
                t = (z - 128.5) / (295.5 - 128.5)
                q = np.array(point) + .5 + (np.array([355.5, 116.5 if side == 'P' else 124.5, 295.5]) - np.array(point) - .5) * t
                gap = abs(q[0]-355.5)*math.cos(.7)-abs(q[1]-120.5)*math.sin(.7)-2.5-.4
                assert gap > .5, (name, z, gap)
                gaps.append(gap)
            plan.append({'name': name, 'at': point, 'own_course_strip_gap': min(gaps)})
    (OUT / 'main_feet_plan.json').write_text(json.dumps(plan, indent=2)+'\n', 'utf8')
    print(json.dumps(plan, indent=2), flush=True)
    if '--apply' not in sys.argv:
        return
    snap = OUT / 'anchors_before_main_feet.json'
    if not snap.exists():
        snap.write_text(json.dumps(before, indent=2)+'\n', 'utf8')
    for p in plan:
        if ab[p['name']]['at'] != p['at']:
            cli(op='work', sub='anchor', work=BASE+'-assembly', name=p['name'],
                at=','.join(map(str,p['at'])), overwrite=1,
                note='20261015 forward 1m to clear raised quarter rail; existing rail timber')
    after = {a['name']: a for a in json.loads(path.read_text('utf8'))['anchors']}
    for p in plan:
        assert after[p['name']]['at'] == p['at']
    print('Six main feet moved; all rope objects and parent references preserved.')


if __name__ == '__main__':
    main()
