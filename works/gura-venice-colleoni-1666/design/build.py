# -*- coding: utf-8 -*-
"""Monumento a Bartolomeo Colleoni (Venice 1488, Verrocchio & Alessandro Leopardi).
0.1 m/voxel, 60 x 60 x 125 (6 m x 6 m x 12.5 m).
Campo Santi Giovanni e Paolo (rot=210 facing WSW).
Pedestal in Istrian white marble & porphyry panels; equestrian statue & Corinthian frieze in smooth bronze.
"""
import math
import os
import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))
MASK_DIR = os.path.join(OUT, 'masks')
os.makedirs(MASK_DIR, exist_ok=True)

SX, SY, SZ = 60, 60, 125

MARBLE = 254     # #ffffaa Istrian white stone
STONE = 218      # #dadaaa warm limestone / marmorino
STONE_S = 182    # #b6b6aa weathered limestone
PAVE = 146       # #9191aa trachyte square paving
PORPH = 137      # #914855 porphyry / Verona inset panel
DARK = 36        # #242400 deep shadow
BRONZE = 140     # #914800 Verrocchio bronze (in metal subwork)
BRONZE_D = 104   # #6d4800 shaded bronze patina
GOLD_S = 212     # #dab600 gilt bronze collar / frieze / armor highlights
GOLD = 248       # #ffda00 gilt visor / saddle emblem

g = np.zeros((SX, SY, SZ), np.uint8)
mt = np.zeros((SX, SY, SZ), np.uint8)


def B(x0, x1, y0, y1, z0, z1, c, arr=None):
    a = g if arr is None else arr
    x0, x1 = max(0, int(x0)), min(SX - 1, int(x1))
    y0, y1 = max(0, int(y0)), min(SY - 1, int(y1))
    z0, z1 = max(0, int(z0)), min(SZ - 1, int(z1))
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        a[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = c


def add_ellipsoid(cx, cy, cz, rx, ry, rz, c, arr):
    for x in range(max(0, int(cx - rx - 1)), min(SX, int(cx + rx + 2))):
        for y in range(max(0, int(cy - ry - 1)), min(SY, int(cy + ry + 2))):
            for z in range(max(0, int(cz - rz - 1)), min(SZ, int(cz + rz + 2))):
                v = ((x - cx) / max(rx, 0.1)) ** 2 + ((y - cy) / max(ry, 0.1)) ** 2 + ((z - cz) / max(rz, 0.1)) ** 2
                if v <= 1.0:
                    arr[x, y, z] = c


def add_limb(p0, p1, r0, r1, c, arr):
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    steps = max(int(math.dist(p0, p1) * 3), 4)
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        z = z0 + (z1 - z0) * t
        r = r0 + (r1 - r0) * t
        add_ellipsoid(x, y, z, r, r, r, c, arr)


# 1. Piazza Base Pad & Two Stepped Marble Tiers (z=0..11)
B(0, 59, 0, 59, 0, 0, PAVE)
B(2, 57, 2, 57, 0, 0, STONE_S)
# 4 Corner Venetian Stone & Bronze Bollards on piazza corners
for bx in (5, 54):
    for by in (5, 54):
        B(bx - 1, bx + 1, by - 1, by + 1, 1, 7, STONE)
        B(bx, bx, by, by, 8, 9, BRONZE, mt)

# Lower step (4.4 x 4.6 m, z=1..4) & Upper step (3.4 x 3.8 m, z=5..9)
B(8, 51, 7, 52, 1, 3, STONE_S)
B(8, 51, 7, 52, 4, 4, MARBLE)
B(13, 46, 11, 48, 5, 8, STONE)
B(13, 46, 11, 48, 9, 9, MARBLE)

# 2. Leopardi Stepped Plinth & Corinthian Pedestal (z=10..70)
# Base plinth block (x=17..42, y=14..45, z=10..20)
B(17, 42, 14, 45, 10, 17, MARBLE)
B(18, 41, 15, 44, 18, 20, STONE)
# Tall shaft core (x=20..39, y=17..42, z=21..56) with porphyry inscription tablets front & sides
B(20, 39, 17, 42, 21, 56, MARBLE)
B(25, 34, 16, 17, 26, 49, PORPH)      # Front recessed inscription tablet (facing y=0)
B(25, 34, 42, 43, 26, 49, PORPH)      # Rear tablet
B(19, 20, 24, 35, 26, 49, PORPH)      # Left tablet
B(39, 40, 24, 35, 26, 49, PORPH)      # Right tablet
# Gilt inscription border studs on front tablet
B(26, 33, 15, 15, 45, 46, GOLD_S, mt)

# 6 Engaged Corinthian Marble Columns around pedestal shaft (sides & flanks)
for cx, cy in ((20, 17), (39, 17), (20, 29), (39, 29), (20, 42), (39, 42)):
    for z in range(21, 53):
        B(cx - 1, cx + 1, cy - 1, cy + 1, z, z, STONE if (z % 2 == 0) else MARBLE)
    B(cx - 2, cx + 2, cy - 2, cy + 2, 53, 56, STONE)
    B(cx - 2, cx + 2, cy - 2, cy + 2, 55, 55, GOLD_S, mt)

# Ornate Bronze Frieze Band (z=57..62) — trophies, sea horses & gilt frieze!
B(18, 41, 15, 44, 57, 62, BRONZE, mt)
B(19, 40, 16, 43, 57, 62, STONE)      # Solid marble structural core inside bronze frieze!
B(18, 41, 15, 44, 59, 60, GOLD_S, mt)

# Overhanging Classical Marble Cornice & Upper Plinth Slab (z=63..71)
B(17, 42, 14, 45, 63, 64, MARBLE)
B(16, 43, 13, 46, 65, 67, MARBLE)
B(18, 41, 15, 44, 68, 70, STONE)      # Cushion pad under bronze baseplate
B(19, 40, 16, 43, 71, 72, BRONZE_D, mt)  # Bronze mounting baseplate for hooves!

# 3. Verrocchio Bronze Equestrian Group (all in mt -> smooth bronze!)
# Facing toward -y (y=17 is horse chest/head, y=42 is hindquarters), centered around x=29.5
CX = 29.5

# Hind legs anchored onto bronze plate at z=72..73
# Left hind (stepped back at y=40): hock (26, 41, 81) -> hip (26, 38, 92)
add_limb((26.0, 40.5, 72.5), (26.0, 41.5, 81.0), 1.4, 1.8, BRONZE, mt)
add_limb((26.0, 41.5, 81.0), (26.2, 37.5, 92.5), 1.8, 3.0, BRONZE, mt)
# Right hind (stepping forward at y=36): hock (33, 37.5, 81) -> hip (33, 36.5, 92)
add_limb((33.0, 36.0, 72.5), (33.0, 38.0, 81.0), 1.4, 1.8, BRONZE, mt)
add_limb((33.0, 38.0, 81.0), (32.8, 36.5, 92.5), 1.8, 3.0, BRONZE, mt)

# Forelegs: RIGHT foreleg planted firmly forward (33, 21, 72.5 -> shoulder 32.5, 22, 91)
add_limb((33.0, 21.0, 72.5), (33.0, 21.5, 81.5), 1.3, 1.6, BRONZE, mt)
add_limb((33.0, 21.5, 81.5), (32.2, 22.2, 91.5), 1.7, 2.7, BRONZE, mt)
# LEFT foreleg classically RAISED & BENT at knee! (shoulder 26.5,22,91 -> bent knee 26,18.5,83 -> raised hoof 26,20.5,77!)
add_limb((26.8, 22.0, 91.5), (26.0, 18.2, 83.5), 2.5, 1.6, BRONZE, mt)
add_limb((26.0, 18.2, 83.5), (26.0, 21.0, 77.5), 1.5, 1.3, BRONZE, mt)

# Muscular Horse Barrel, Chest & Hindquarters (y=21..39, z=87..98)
add_ellipsoid(CX, 23.0, 92.5, 4.5, 4.2, 4.6, BRONZE, mt)    # Deep chest & shoulder blades
add_ellipsoid(CX, 29.5, 91.5, 4.4, 5.8, 4.3, BRONZE, mt)    # Ribcage & barrel
add_ellipsoid(CX, 36.5, 93.0, 4.6, 4.5, 4.5, BRONZE, mt)    # Powerful croup / haunches
# Horse gilded breastplate & saddle trim
add_limb((25.5, 22.5, 91.5), (29.5, 19.2, 92.5), 0.9, 0.9, GOLD_S, mt)
add_limb((33.5, 22.5, 91.5), (29.5, 19.2, 92.5), 0.9, 0.9, GOLD_S, mt)
# Sculpted arched tail sweeping down behind haunches
add_limb((CX, 40.5, 94.5), (CX, 43.2, 89.0), 1.5, 1.2, BRONZE_D, mt)
add_limb((CX, 43.2, 89.0), (CX, 42.5, 80.5), 1.2, 0.8, BRONZE_D, mt)

# Arched Horse Neck, Flowing Mane & Noble Head (head turned slightly right, facing forward-west)
add_limb((CX, 21.5, 95.0), (CX, 16.5, 105.5), 3.3, 2.4, BRONZE, mt)
add_ellipsoid(CX + 0.5, 14.5, 106.5, 2.0, 2.8, 2.2, BRONZE, mt)  # Poll & cranium
add_limb((CX + 0.5, 14.5, 106.5), (CX + 1.0, 11.2, 100.5), 1.9, 1.2, BRONZE, mt)  # Tapered muzzle
# Ears & arched mane crest
add_limb((CX - 0.8, 16.0, 108.0), (CX - 1.0, 15.5, 110.5), 0.6, 0.4, BRONZE, mt)
add_limb((CX + 1.8, 16.0, 108.0), (CX + 2.0, 15.5, 110.5), 0.6, 0.4, BRONZE, mt)
add_limb((CX, 21.0, 97.5), (CX, 16.0, 107.0), 1.1, 0.9, BRONZE_D, mt)

# War Saddle & Stirrups
add_ellipsoid(CX, 29.0, 96.5, 3.3, 3.0, 1.4, GOLD_S, mt)

# Armored Condottiere Bartolomeo Colleoni standing upright in the stirrups!
# Rider thighs gripping saddle, boots in stirrups (z=84..99)
add_limb((25.0, 28.5, 96.5), (24.2, 26.8, 86.0), 1.6, 1.2, BRONZE, mt)
add_limb((34.0, 28.5, 96.5), (34.8, 26.8, 86.0), 1.6, 1.2, BRONZE, mt)
# Armored cuirass torso (z=98..111, shoulders twisted defiantly!)
add_ellipsoid(CX, 29.0, 101.5, 3.2, 2.3, 4.2, BRONZE, mt)
add_ellipsoid(CX, 28.5, 107.5, 4.2, 2.5, 3.2, BRONZE, mt)
# Gilded pauldrons & chest sash
add_ellipsoid(CX - 3.5, 28.5, 109.0, 1.6, 1.6, 1.4, GOLD_S, mt)
add_ellipsoid(CX + 3.5, 28.5, 109.0, 1.6, 1.6, 1.4, GOLD_S, mt)
# Head & flared Italian sallet helmet (z=111..117) + neck overlap
add_ellipsoid(CX, 28.4, 111.0, 1.9, 1.9, 1.8, BRONZE, mt)
add_ellipsoid(CX, 28.2, 113.5, 2.0, 2.1, 2.3, BRONZE, mt)
add_ellipsoid(CX, 29.0, 115.2, 2.2, 2.6, 1.2, GOLD_S, mt)
# Left hand holding leather bronze reins forward toward neck
add_limb((CX - 3.5, 28.5, 108.0), (CX - 2.2, 22.0, 101.0), 1.3, 1.0, BRONZE, mt)
add_limb((CX - 2.2, 22.0, 101.0), (CX, 16.5, 101.5), 0.9, 0.9, GOLD_S, mt)
# Right arm & raised Commander's Baton (held resolutely at right hip/side!)
add_limb((CX + 3.8, 28.5, 108.0), (CX + 4.8, 27.0, 101.5), 1.3, 1.1, BRONZE, mt)
add_limb((CX + 4.8, 27.0, 101.5), (CX + 5.2, 22.5, 105.0), 0.95, 0.85, GOLD, mt)

# Enforce strict disjointness (body vs metal)
g[mt > 0] = 0


def dump(arr, path):
    xs, ys, zs = np.nonzero(arr)
    cs = arr[xs, ys, zs]
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for x, y, z, c in zip(xs.tolist(), ys.tolist(), zs.tolist(), cs.tolist()):
            f.write(f'{x},{y},{z},{c}\n')
    return len(xs)


nb = dump(g, os.path.join(MASK_DIR, 'body.txt'))
nm = dump(mt, os.path.join(MASK_DIR, 'metal.txt'))
print(f'Colleoni Monument generated: body={nb}, metal={nm}')
