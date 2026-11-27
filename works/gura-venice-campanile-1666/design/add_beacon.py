# -*- coding: utf-8 -*-
"""Upgrade Venetia Campanile di San Marco (1666) with historical belfry signal braziers/lanterns (fanali) + seaward beacon."""
import json
import math
import os
import re
import subprocess
import numpy as np

WORKS = 'D:/Unity/Valhalla/Sculpture/works'
PARENT = 'gura-venice-campanile-1666'
STONE_W = PARENT + '-beacon-stone'
IRON_W = PARENT + '-beacon-iron'
FLAME_W = 'gura-venice-beacon-flame'

BRAIN_SCRATCH = 'C:/Users/Tim/.gemini/antigravity/brain/8f07d383-ea4b-41cc-bda0-39dc527b9a91/scratch'
EXISTING_LIST = os.path.join(BRAIN_SCRATCH, 'camp_belfry_voxels.txt')
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'beacon_out')
os.makedirs(OUT_DIR, exist_ok=True)

# RGB332 palette matching gura-venice-ducale-1666 / campanile
MARBLE = 254     # #ffffaa Istrian white stone
STONE = 218      # #dadaaa warm limestone
STONE_S = 182    # #b6b6aa weathered grey stone
IRON = 73        # #484855 dark wrought iron
IRON_D = 36      # #242400 blackened cast iron / charcoal bed
IRON_H = 109     # #6d6d55 gunmetal iron highlight
GOLD = 248       # #ffda00 gilded finial accent
FLAME_C = 254    # #ffffaa white-yellow flame heart
FLAME_Y = 248    # #ffda00 bright yellow flame
FLAME_O = 244    # #ffb600 warm amber flame
FLAME_R = 236    # #ff9100 deep ember orange

# Load existing occupied voxels in z=495..620 to guarantee zero collisions
occ = set()
for line in open(EXISTING_LIST, encoding='utf-8'):
    if not line or line.startswith('#'):
        continue
    x, y, z, _ = line.strip().split(',')
    occ.add((int(x), int(y), int(z)))


def safe_set(cells, x, y, z, c, allow_z_min=506, allow_z_max=562):
    if not (0 <= x < 160 and 0 <= y < 160 and allow_z_min <= z <= allow_z_max):
        return
    if (x, y, z) in occ:
        return
    cells[(x, y, z)] = c


def add_oct_disk(cells, cx, cy, z0, z1, r, c, r_inner=0.0):
    ri = int(math.ceil(r)) + 1
    for z in range(z0, z1 + 1):
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                oct_d = max(abs(dx), abs(dy), (abs(dx) + abs(dy)) * 0.7071)
                if r_inner <= oct_d <= r + 0.15:
                    safe_set(cells, int(round(cx + dx)), int(round(cy + dy)), z, c)


def add_box(cells, x0, x1, y0, y1, z0, z1, c):
    for z in range(z0, z1 + 1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                safe_set(cells, x, y, z, c)


def add_line(cells, p0, p1, c, rad=1):
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    steps = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1) * 2
    for i in range(steps + 1):
        t = i / steps
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        z = int(round(z0 + (z1 - z0) * t))
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                for dz in range(-rad, rad + 1):
                    if dx * dx + dy * dy + dz * dz <= rad * rad + 0.5:
                        safe_set(cells, x + dx, y + dy, z + dz, c)


def build_cresset(stone, iron, cx, cy, base_z=506, bowl_z=536, is_central=False):
    """Build Istrian stone pedestal + wrought-iron openwork brazier/lantern."""
    # Stepped Istrian pedestal resting firmly on z=505 belfry floor
    if is_central:
        add_oct_disk(stone, cx, cy, base_z, base_z + 2, 13.5, STONE_S)
        add_oct_disk(stone, cx, cy, base_z + 3, base_z + 5, 11.0, MARBLE)
        add_oct_disk(stone, cx, cy, base_z + 6, base_z + 11, 8.5, STONE)
        add_oct_disk(stone, cx, cy, base_z + 12, base_z + 13, 9.8, MARBLE)
        top_stone = base_z + 13
        br_r = 7.5
        hood_z0 = bowl_z + 16
        hood_r = 9.0
    else:
        add_oct_disk(stone, cx, cy, base_z, base_z + 1, 6.2, STONE_S)
        add_oct_disk(stone, cx, cy, base_z + 2, base_z + 4, 4.8, MARBLE)
        add_oct_disk(stone, cx, cy, base_z + 5, base_z + 10, 3.6, STONE)
        add_oct_disk(stone, cx, cy, base_z + 11, base_z + 12, 4.5, MARBLE)
        top_stone = base_z + 12
        br_r = 5.2
        hood_z0 = bowl_z + 14
        hood_r = 6.2

    # Iron base ring & central stanchion + 4 scrolled buttresses up to brazier bowl
    add_oct_disk(iron, cx, cy, top_stone + 1, top_stone + 2, br_r * 0.55, IRON_D)
    add_oct_disk(iron, cx, cy, top_stone + 3, bowl_z - 1, 1.8 if is_central else 1.3, IRON)
    for ang in (0, 90, 180, 270) if not is_central else (45, 135, 225, 315):
        rad = math.radians(ang)
        p0 = (cx + math.cos(rad) * (br_r * 0.55), cy + math.sin(rad) * (br_r * 0.55), top_stone + 2)
        p1 = (cx + math.cos(rad) * (br_r * 0.85), cy + math.sin(rad) * (br_r * 0.85), bowl_z)
        add_line(iron, p0, p1, IRON, rad=0 if not is_central else 1)

    # Flared openwork wrought-iron fire basket (bowl_z .. bowl_z+9)
    # Keep inner core empty (r < br_r-1.8) for flame model!
    add_oct_disk(iron, cx, cy, bowl_z, bowl_z + 1, br_r * 0.72, IRON_D)
    add_oct_disk(iron, cx, cy, bowl_z + 2, bowl_z + 2, br_r * 0.85, IRON_D, r_inner=br_r * 0.48)
    # Lower rim & upper basket hoop
    add_oct_disk(iron, cx, cy, bowl_z + 3, bowl_z + 3, br_r, IRON, r_inner=br_r - 1.2)
    add_oct_disk(iron, cx, cy, bowl_z + 6, bowl_z + 7, br_r + 0.5, IRON_H, r_inner=br_r - 1.0)
    # 8 openwork ribs from bowl_z+2 to hood_z0
    for k in range(4 if not is_central else 8):
        ang = math.radians(k * (90 if not is_central else 45) + 22.5)
        for z in range(bowl_z + 2, hood_z0 + 1):
            rx = int(round(cx + math.cos(ang) * (br_r - 0.1)))
            ry = int(round(cy + math.sin(ang) * (br_r - 0.1)))
            safe_set(iron, rx, ry, z, IRON if (z % 2 == 0) else IRON_D)

    # Vented octagonal conical rain hood + gilded finial (capped <= 562, below bells 565!)
    for dz in range(6):
        z = hood_z0 + dz
        if z > 562:
            break
        rr = hood_r * (1.0 - dz / 6.2)
        c = GOLD if dz == 5 else (IRON_H if dz % 2 == 0 else IRON)
        add_oct_disk(iron, cx, cy, z, z, max(1.0, rr), c)


stone_cells = {}
iron_cells = {}

# 1. Central Sanctuary Cauldron at (71.5, 79.5) — well below bells (z=565)
build_cresset(stone_cells, iron_cells, 71, 79, base_z=506, bowl_z=536, is_central=True)

# 2. East, West, North cardinal arch cressets standing on floor right inside arches
build_cresset(stone_cells, iron_cells, 71, 32, base_z=506, bowl_z=536, is_central=False)
build_cresset(stone_cells, iron_cells, 71, 126, base_z=506, bowl_z=536, is_central=False)
build_cresset(stone_cells, iron_cells, 118, 79, base_z=506, bowl_z=536, is_central=False)

# 3. South Seaward Signal Lantern ("Braccio del Fanale") projecting to x=16, y=79!
# Anchored on heavy Istrian base inside balustrade (x=24..34, y=74..84, z=506..518)
add_oct_disk(stone_cells, 29, 79, 506, 508, 6.2, STONE_S)
add_oct_disk(stone_cells, 29, 79, 509, 515, 4.5, MARBLE)
add_oct_disk(stone_cells, 29, 79, 516, 518, 5.2, STONE)
# Wrought-iron mast & arched cantilever crane extending outward over South arch sill to x=16
add_box(iron_cells, 27, 30, 77, 81, 519, 548, IRON)
add_oct_disk(iron_cells, 29, 79, 549, 551, 2.2, IRON_H)
add_line(iron_cells, (28, 79, 524), (17, 79, 536), IRON, rad=1)
add_line(iron_cells, (28, 79, 546), (16, 79, 557), IRON, rad=1)
# Diagonal brace & scroll
add_line(iron_cells, (28, 79, 548), (19, 79, 555), IRON_H, rad=0)
# South Seaward Fanale Lantern hung at (16, 79), flame center at (16, 79, 544)
add_oct_disk(iron_cells, 16, 79, 535, 537, 4.8, IRON_D)
add_oct_disk(iron_cells, 16, 79, 538, 539, 5.4, IRON, r_inner=3.4)
add_oct_disk(iron_cells, 16, 79, 548, 549, 5.5, IRON_H, r_inner=4.0)
for ang in (45, 135, 225, 315):
    r = math.radians(ang)
    rx = int(round(16 + math.cos(r) * 4.8))
    ry = int(round(79 + math.sin(r) * 4.8))
    add_box(iron_cells, rx, rx, ry, ry, 538, 550, IRON)
for dz in range(6):
    add_oct_disk(iron_cells, 16, 79, 550 + dz, 550 + dz, max(1.0, 5.8 - dz * 0.9), GOLD if dz >= 4 else IRON)

# Disjoint check between stone, iron, and existing Campanile
overlap_si = set(stone_cells) & set(iron_cells)
overlap_occ = (set(stone_cells) | set(iron_cells)) & occ
assert not overlap_si, f'stone/iron overlap: {len(overlap_si)}'
assert not overlap_occ, f'existing overlap: {len(overlap_occ)}'

# 4. Separate Flame micro-work (7x7x12, wick at [3, 3, 5])
flame_cells = {}
for z in range(2, 10):
    rad_z = 2.6 if z <= 5 else (2.6 - (z - 5) * 0.55)
    for x in range(7):
        for y in range(7):
            d = math.hypot(x - 3.0, y - 3.0)
            if d <= rad_z:
                if d <= 0.9 and 3 <= z <= 6:
                    c = FLAME_C
                elif d <= 1.6 and z <= 7:
                    c = FLAME_Y
                elif z <= 8:
                    c = FLAME_O
                else:
                    c = FLAME_R
                flame_cells[(x, y, z)] = c

# Dump lists
def dump(cells, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for (x, y, z), c in sorted(cells.items()):
            f.write(f'{x},{y},{z},{c}\n')
    print(f'Wrote {len(cells)} voxels -> {path}')

p_stone = os.path.join(OUT_DIR, 'beacon_stone.txt').replace('\\', '/')
p_iron = os.path.join(OUT_DIR, 'beacon_iron.txt').replace('\\', '/')
p_flame = os.path.join(OUT_DIR, 'beacon_flame.txt').replace('\\', '/')
dump(stone_cells, p_stone)
dump(iron_cells, p_iron)
dump(flame_cells, p_flame)

if '--apply' not in sys.argv if 'sys' in dir() else False:
    pass

import sys
if '--apply' in sys.argv:
    def cli(args, quiet=False):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []),
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 and not quiet:
            print('ERR:', ' '.join(args[:8]), '\n', (r.stdout + r.stderr)[-1000:])
        return r.returncode, r.stdout

    def ensure_work(wid, title, size, tags='sub'):
        rc, _ = cli(['op=work', 'sub=show', f'work={wid}'], quiet=True)
        if rc != 0:
            rc, out = cli(['op=work', 'sub=create', 'persona=gura', f'id={wid}', f'title={title}',
                           f'size={size}', f'parent_work={PARENT}', 'meters_per_voxel=0.1', f'tags={tags}'])
            assert rc == 0, out
        else:
            cli(['op=work', 'sub=update', 'persona=gura', f'work={wid}', 'meters_per_voxel=0.1', f'tags={tags}', f'title={title}'])

    def sync_stamp(wid, want, vox_path):
        exp_p = os.path.join(OUT_DIR, f'{wid}.cur.txt').replace('\\', '/')
        rc, out = cli(['op=export', 'format=list', f'work={wid}', f'out={exp_p}'])
        assert rc == 0, out
        cur = {}
        for l in open(exp_p, encoding='utf-8'):
            if l.strip() and not l.startswith('#'):
                a = l.split(',')
                cur[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
        carve = {k: c for k, c in cur.items() if k not in want}
        add = {k: c for k, c in want.items() if cur.get(k) != c}
        if carve:
            cp = os.path.join(OUT_DIR, f'{wid}.carve.txt').replace('\\', '/')
            dump(carve, cp)
            rc, out = cli(['op=carvevox', 'persona=gura', f'work={wid}', f'voxels={cp}', 'at=0,0,0',
                           f'expect_pixels={len(carve)}', 'draft=0', 'share=0'])
            assert rc == 0, out
        if add:
            ap = os.path.join(OUT_DIR, f'{wid}.add.txt').replace('\\', '/')
            dump(add, ap)
            rc, out = cli(['op=stampvox', 'persona=gura', f'work={wid}', f'voxels={ap}', 'at=0,0,0',
                           'overwrite=1', f'expect_pixels={len(add)}', 'draft=0', 'share=0'])
            assert rc == 0, out
        print(f'Synced {wid}: want={len(want)} carve={len(carve)} add={len(add)}')

    ensure_work(STONE_W, '聖馬可鐘樓信號燈台基座', '160,160,1000', tags='sub')
    ensure_work(IRON_W, '聖馬可鐘樓信號燈架鐵件', '160,160,1000', tags='sub')
    ensure_work(FLAME_W, '威尼斯港口信號燈火芯', '7,7,12', tags='sub')

    sync_stamp(STONE_W, stone_cells, p_stone)
    sync_stamp(IRON_W, iron_cells, p_iron)
    sync_stamp(FLAME_W, flame_cells, p_flame)

    # Flame wick anchor
    cli(['op=work', 'sub=unanchor', 'persona=gura', f'work={FLAME_W}', 'name=wick'], quiet=True)
    rc, out = cli(['op=work', 'sub=anchor', 'persona=gura', f'work={FLAME_W}', 'name=wick', 'at=3,3,5'])
    assert rc == 0, out

    # Link stone & iron into campanile
    for nm, src, meta in [
        ('beacon-stone', STONE_W, ''),
        ('beacon-iron', IRON_W, json.dumps({'material': 'iron'}, sort_keys=True)),
    ]:
        args = ['op=work', 'sub=link', 'persona=gura', f'work={PARENT}', f'name={nm}', f'source_work={src}',
                'at=0,0,0', 'turn=0', 'overwrite=1']
        if meta:
            args.append(f'meta={meta}')
        rc, out = cli(args)
        assert rc == 0, out

    # Attach 5 flame models (kind=light -> points.wick)
    FLAMES = [
        ('beacon-c', [68, 76, 538]),
        ('beacon-s', [13, 76, 539]),
        ('beacon-e', [68, 29, 538]),
        ('beacon-w', [68, 123, 538]),
        ('beacon-n', [115, 76, 538]),
    ]
    for nm, at in FLAMES:
        rc, out = cli(['op=work', 'sub=model', 'persona=gura', f'work={PARENT}', f'name={nm}', f'source_work={FLAME_W}',
                       f'at={at[0]},{at[1]},{at[2]}', 'pivot=0,0,0', 'rotate=0,0,0',
                       f'meta={json.dumps({"kind": "light"})}', 'overwrite=1'])
        assert rc == 0, out

    # Parent seaward searchlight anchors (wick at seaward south fanale [120,79,544], beam SSE toward Bacino/Lido [+z/+x in game])
    for anm in ('wick', 'beam-to'):
        cli(['op=work', 'sub=unanchor', 'persona=gura', f'work={PARENT}', f'name={anm}'], quiet=True)
    rc, out = cli(['op=work', 'sub=anchor', 'persona=gura', f'work={PARENT}', 'name=wick', 'at=120,79,544',
                   'note=南面海側信號提燈火芯'])
    assert rc == 0, out
    rc, out = cli(['op=work', 'sub=anchor', 'persona=gura', f'work={PARENT}', 'name=beam-to', 'at=140,72,541',
                   'note=朝外海南南東（聖馬可灣與利多水道出口）'])
    assert rc == 0, out

    # Write work_meta.json for seaward searchlight
    wm = {
        'schema': 1,
        'meta': {
            'kind': 'searchlight',
            'light_angle': 4.5,
            'light_period': 16,
            'light_range': 700,
            'light_sweep': 35,
        }
    }
    open(os.path.join(WORKS, PARENT, 'work_meta.json'), 'w', encoding='utf-8').write(json.dumps(wm, indent=2))
    print('Updated work_meta.json on', PARENT)
