"""Turn this ship's own bow artwork into supported, destructible hull voxels.

Derived from draft_deco.py's original painted-eye/lion masks and sculpt_cli.py.
Only Sculpture CLI writes the works. Run after gear.py and draft_deco.draft().
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import label, binary_fill_holes

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sculpt_cli as sc
from draft_hull import DESIGN, SIZE
from draft_decks import write_mask


def geometry():
    before = DESIGN / 'actual/fittings-before.txt'
    before.parent.mkdir(exist_ok=True)
    args = {'work': sc.ASSEMBLY, 'format': 'list', 'out': before}
    if 'bow-voxel' in sc.entries(sc.ASSEMBLY, 'links'):
        args['hide_links'] = 'bow-voxel'
    sc.sculpt('export', **args)
    body = sc.read_cells(before)
    source = sc.read_cells(DESIGN / 'masks/bow-deco.txt')
    artwork = dict(source)
    artwork.update({(x, 160-y, z): c for (x,y,z), c in source.items()})
    paint = {p:c for p,c in artwork.items() if p in body}
    assert len(paint) == 10, 'Changed interface: review the anchor-gear paint'
    physical = {p:c for p,c in artwork.items() if p not in body}
    columns = {}
    for x,y,z in body:
        columns.setdefault((x,z),[]).append(y)
    # Behind every visible relief cell, continue to the actual hull surface.
    # These short wood pads remove four disconnected patches from the old art.
    for (x,y,z), color in artwork.items():
        support_z = next((zz for zz in range(z,max(-1,z-8),-1) if (x,zz) in columns),None)
        if support_z is None:
            raise RuntimeError(f'No nearby hull behind bow artwork {(x,y,z)}')
        column = columns[(x,support_z)]
        for zz in range(support_z,z):
            p=(x,y,zz)
            if p not in body and p not in artwork: physical[p]=104
        surface = max(column) if y > 80 else min(column)
        for yy in range(min(y,surface)+1, max(y,surface)):
            p = (x,yy,support_z)
            if p not in body and p not in artwork:
                physical[p] = 104
    assert not set(physical).intersection(body)
    expected = {**body, **paint, **physical}
    grid = np.zeros(SIZE, dtype=bool)
    for p in expected: grid[p] = True
    count = int(label(grid)[1])
    enclosed = int(np.count_nonzero(binary_fill_holes(grid) & ~grid))
    assert count == 1 and enclosed == 0, (count, enclosed)
    assert all(expected.get((x,160-y,z)) == c for (x,y,z),c in physical.items())
    write_mask('bow-voxel', physical)
    write_mask('bow-paint', paint)
    return body, physical, paint, {
        'before': len(body), 'artwork': len(artwork), 'physical_added': len(physical),
        'backing': len(set(physical)-set(artwork)), 'repainted': len(paint),
        'after': len(expected), 'components': count, 'enclosed_air': enclosed,
        'nameboard_at': [26.5,64,67], 'original_nameboard_at': [28,64,67],
        'stern_carving_min_x': 28, 'nameboard_back_x': 27.5,
        'nameboard_min_clearance_m': .05,
    }


def install_bow():
    body, physical, paint, report = geometry()
    support = sc.HULL + '-anchor-gear'
    current_path = DESIGN / 'actual/fittings-anchor-gear.txt'
    sc.sculpt('export', work=support, format='list', links='none', out=current_path)
    current = sc.read_cells(current_path)
    assert all(p in current and current[p] in (104,c) for p,c in paint.items())
    delta = {p:c for p,c in paint.items() if current[p] != c}
    if delta:
        write_mask('bow-paint-delta', delta)
        sc.sculpt('stampvox', work=support, voxels=DESIGN/'masks/bow-paint-delta.txt',
                  at=(0,0,0), overwrite=1, expect_pixels=len(delta))
    work = sc.component('bow-voxel', '可破壞艏眼、浪花與獅面')
    sc.link(sc.ASSEMBLY, 'bow-voxel', work, {})
    for name in ('bow-P','bow-S'):
        if name in sc.entries(sc.ASSEMBLY,'models'):
            sc.sculpt('work', sub='unmodel', work=sc.ASSEMBLY, name=name)
    return report


def install():
    report = install_bow()
    board = sc.entries(sc.ASSEMBLY, 'models')['nameboard']
    sc.model(sc.ASSEMBLY, 'nameboard', board['work'], (26.5,64,67),
             board['pivot'], board.get('meta',{}))
    (DESIGN/'fittings-placement.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--works', type=Path, help='CLI work metadata root when running from a code worktree')
    args = parser.parse_args()
    if args.works: sc.WORKS = args.works
    if args.apply: install()
    else:
        _,_,_,report = geometry()
        print(json.dumps(report),flush=True)
