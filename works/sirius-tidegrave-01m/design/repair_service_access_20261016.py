"""Open mirrored 0.8m-wide, 1.8m-high bow service passages using guarded CLI cuts.

The gun platform exists outside the narrowing hull. Its side workstations were
isolated by the hull wall. Preserve the forecastle above and every model/pin.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, 'D:/Unity/Valhalla/Blockside/VoxelKit')
from build_structure import cli, BASE, get_actual
from voxel_export import unpack

OUT = ROOT / 'service_access_20261016'
OUT.mkdir(exist_ok=True)
INPUT = ROOT / 'delivery/tidegrave_import_20261015.vxk'


def run():
    h, vox = unpack(INPUT.read_bytes())
    body = {tuple(map(int, v[:3])): int(v[3]) for v in vox}
    hull = get_actual(BASE)
    record = OUT / 'plan.json'
    if record.exists():
        plan = json.loads(record.read_text('utf8'))
    else:
        cut = [[x,y,z,c] for (x,y,z),c in hull.items()
               if 574 <= x <= 581 and (94 <= y <= 103 or 137 <= y <= 146)
               and 117 <= z <= 134]
        assert cut and all(z > 52 for x,y,z,c in cut)
        post = dict(body)
        for x,y,z,c in cut:
            assert post[(x,y,z)] == c
            del post[(x,y,z)]
        add = []
        for x in range(574,585):
            for y in list(range(94,104)) + list(range(137,147)):
                # Only place a walking surface with the full requested headroom.
                if any((x,y,z) in post for z in range(117,135)):continue
                for z in (115,116):
                    if (x,y,z) not in post:add.append([x,y,z,109])
        plan = {'baseline': str(INPUT), 'cuts': sorted(cut), 'additions': sorted(add),
                'clearance': 'X574..581, Y94..103 /137..146, Z117..134; floor Z115..116',
                'scope': 'Original hull only, no cuts to models, mast, ladders, forecastle or sail pins.'}
        record.write_text(json.dumps(plan, indent=2), 'utf8')
    cuts = [v for v in plan['cuts'] if tuple(v[:3]) in hull]
    assert all(hull[tuple(v[:3])] == v[3] for v in cuts)
    for name, values in [('cut',cuts)]:
        if not values:continue
        f = OUT / (name + '.vox.txt')
        f.write_text(''.join(','.join(map(str,v))+'\n' for v in values), 'utf8')
        cli(op='carvevox', work=BASE, voxels=f, at='0,0,0', expect_pixels=len(values), share=0)
    cradle = get_actual(BASE + '-chase-cradle')
    additions = [v for v in plan['additions'] if tuple(v[:3]) not in cradle]
    if additions:
        f = OUT / 'add.vox.txt'
        f.write_text(''.join(','.join(map(str,v))+'\n' for v in additions), 'utf8')
        cli(op='stampvox', work=BASE + '-chase-cradle', voxels=f, at='0,0,0',
            expect_pixels=len(additions), share=0)
    cli(op='export',work=BASE+'-assembly',format='vxk',include='rig,models,parts,meta,ends',
        out=ROOT/'delivery/tidegrave_import_20261016.vxk')
    print('Guarded service passages:',len(cuts),'hull cells cut;',len(additions),'floor cells added.')


if __name__ == '__main__':
    run()
