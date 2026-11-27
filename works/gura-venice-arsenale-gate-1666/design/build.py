# -*- coding: utf-8 -*-
"""Porta Magna dell'Arsenale (Venice 1460 Gambello + 1571/1578 attic, STRICT 1666 edition).
0.1 m/voxel, 140 x 80 x 175 (14 m wide x 8 m deep x 17.5 m tall).
STRICT 1666 RULE: Excludes 1687-92 Greek Piraeus lions and outer balustrade terrace!
y=0 faces WNW (rot=188) along Ponte dell'Arsenale toward Campo dell'Arsenale.
"""
import math
import os
import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))
MASK_DIR = os.path.join(OUT, 'masks')
os.makedirs(MASK_DIR, exist_ok=True)

SX, SY, SZ = 140, 80, 175

MARBLE = 254     # #ffffaa Istrian white stone
STONE = 218      # #dadaaa warm limestone
STONE_S = 182    # #b6b6aa weathered grey limestone
PAVE = 146       # #9191aa trachyte square paving
PORPH = 137      # #914855 Verona/porphyry marble inlay panels
BRICK = 173      # #b66d55 Venetian terracotta brick
BRICK_D = 141    # #916d55 shaded brick / joint
DARK = 36        # #242400 deep shadow / iron
IRON = 73        # #484855 wrought iron lantern bracket
GOLD = 248       # #ffda00 gilded Winged Lion & finials (in metal subwork)
GOLD_S = 212     # #dab600 antique bronze studs / rosettes
BRONZE = 140     # #914800 bronze door fittings
WOOD = 104       # #6d4800 heavy timber Arsenal doors
WOOD_D = 68      # #482400 dark oak framing

g = np.zeros((SX, SY, SZ), np.uint8)
mt = np.zeros((SX, SY, SZ), np.uint8)


def B(x0, x1, y0, y1, z0, z1, c, arr=None):
    a = g if arr is None else arr
    x0, x1 = max(0, int(x0)), min(SX - 1, int(x1))
    y0, y1 = max(0, int(y0)), min(SY - 1, int(y1))
    z0, z1 = max(0, int(z0)), min(SZ - 1, int(z1))
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        a[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = c


def cyl_z(cx, cy, z0, z1, r, c, flute=False, arr=None):
    a = g if arr is None else arr
    ri = int(math.ceil(r)) + 1
    for z in range(max(0, z0), min(SZ, z1 + 1)):
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                d = math.hypot(dx, dy)
                if d <= r + 0.15:
                    ang = math.atan2(dy, dx)
                    col = c
                    if flute and d >= r - 0.8 and int(round(ang * 6 / math.pi)) % 2 == 0:
                        col = STONE
                    x, y = int(round(cx + dx)), int(round(cy + dy))
                    if 0 <= x < SX and 0 <= y < SY:
                        a[x, y, z] = col


# 1. Stepped trachyte & Istrian pavement apron (z=0..1)
B(0, SX - 1, 0, SY - 1, 0, 0, PAVE)
B(26, 113, 3, 76, 1, 1, STONE_S)
# Grand entrance approach path with Istrian white curb strips
B(53, 86, 0, 79, 1, 1, MARBLE)
B(56, 83, 0, 79, 1, 1, PAVE)
# Low stone corner bollards at bridgehead entrance (strictly pre-1687 stone posts, NO lions)
for bx in (48, 91):
    B(bx - 1, bx + 1, 2, 4, 2, 10, STONE)
    B(bx - 1, bx + 1, 2, 4, 11, 12, MARBLE)

# 2. Arsenale Flanking Brick Curtain Walls (x=0..16 & 123..139, y=28..45)
for wx0, wx1 in ((0, 16), (123, 139)):
    for z in range(2, 76):
        c = BRICK_D if (z % 4 == 0) else BRICK
        B(wx0, wx1, 28, 45, z, z, c)
    B(wx0, wx1, 27, 46, 2, 8, STONE_S)         # Stone water-table base
    B(wx0, wx1, 27, 46, 68, 70, MARBLE)        # Wall walk stringcourse
    # Brick crenellations (merlons up to z=88)
    for mx in range(wx0, wx1 - 2, 7):
        B(mx, min(wx1, mx + 4), 28, 34, 76, 86, BRICK)
        B(mx, min(wx1, mx + 4), 28, 34, 87, 88, MARBLE)

# 3. Twin Flanking Square Brick Bell/Watch Turrets (x=15..33 & x=106..124, y=20..44)
for tx0 in (15, 106):
    tx1 = tx0 + 18
    tcx = (tx0 + tx1) // 2
    B(tx0, tx1, 20, 44, 2, 12, STONE_S)
    B(tx0, tx1, 19, 45, 13, 15, MARBLE)
    for z in range(16, 138):
        row_c = BRICK_D if (z % 4 == 0) else BRICK
        B(tx0, tx1, 21, 43, z, z, row_c)
        # Istrian corner quoins every 4 layers
        if (z // 4) % 2 == 0:
            for qx0, qx1 in ((tx0, tx0 + 2), (tx1 - 2, tx1)):
                for qy0, qy1 in ((21, 23), (41, 43)):
                    B(qx0, qx1, qy0, qy1, z, z, MARBLE)
    # Recessed lancet/belfry arched windows on N/S/W/E faces (z=84..122)
    B(tcx - 3, tcx + 3, 21, 25, 86, 118, 0)
    B(tcx - 3, tcx + 3, 26, 26, 86, 118, DARK)
    B(tcx - 4, tcx + 4, 20, 22, 84, 85, MARBLE)
    B(tcx - 4, tcx + 4, 20, 22, 119, 122, MARBLE)
    # Also side outer windows
    out_x = tx0 if tx0 < 70 else tx1
    in_off = 2 if tx0 < 70 else -2
    B(min(out_x, out_x + in_off), max(out_x, out_x + in_off), 29, 35, 86, 116, DARK)
    # Stringcourses & corbelled stone crown cornice (z=64..66 & z=134..141)
    B(tx0 - 1, tx1 + 1, 19, 45, 62, 65, MARBLE)
    B(tx0 - 1, tx1 + 1, 19, 45, 134, 136, STONE)
    for kx in range(tx0, tx1 + 1, 4):
        B(kx, kx + 1, 18, 46, 137, 138, STONE_S)
    B(tx0 - 2, tx1 + 2, 18, 46, 139, 141, MARBLE)
    # Pyramid terracotta roof (z=142..165) + gilded copper ball finial in -metal (z=166..172)
    for dz in range(24):
        m = int(dz * 9 // 24)
        c = BRICK_D if dz % 3 == 0 else BRICK
        B(tx0 + m, tx1 - m, 21 + m, 43 - m, 142 + dz, 142 + dz, c)
    B(tcx - 1, tcx + 1, 31, 33, 166, 169, GOLD, mt)
    B(tcx, tcx, 32, 32, 170, 173, GOLD, mt)

# 4. Central 1460 Triumphal Arch Massing (x=34..105, y=12..46)
B(34, 105, 14, 46, 2, 60, STONE)
B(34, 105, 14, 40, 61, 112, STONE)
# Deep Istrian rusticated facing on front & rear faces
B(35, 104, 13, 14, 2, 58, MARBLE)
B(35, 104, 45, 46, 2, 58, MARBLE)

# Ground Arch Passageway Tunnel (x=54..85, 3.2 m wide, spring z=38, apex z=54)
for dx in range(-16, 17):
    x = 70 + dx
    h_arc = int(round(max(0.0, 16.2 ** 2 - dx * dx) ** 0.5))
    z_top = 38 + h_arc
    B(x, x, 12, 48, 2, z_top, 0)
    # Coffered marble archivolt on front & rear portals
    B(x, x, 11, 13, z_top, min(58, z_top + 3), MARBLE)
    B(x, x, 45, 47, z_top, min(58, z_top + 2), MARBLE)
# Sculpted triple keystone over central arch
B(68, 72, 9, 13, 52, 58, MARBLE)
B(69, 71, 8, 9, 54, 57, GOLD_S, mt)

# Massive Studio Oak & Studded Bronze Double Doors recessed inside arch (y=28..31)
for dx in range(-15, 16):
    x = 70 + dx
    h_arc = int(round(max(0.0, 15.2 ** 2 - dx * dx) ** 0.5))
    z_top = 38 + h_arc
    # Recessed transom grille at top & solid oak leaves up to z=48
    if abs(dx) >= 1:
        B(x, x, 28, 30, 2, min(z_top, 48), WOOD_D if (abs(dx) in (1, 15) or x % 5 == 0) else WOOD)
    else:
        B(x, x, 28, 30, 2, min(z_top, 48), DARK)  # Central door seam
    # Horizontal bronze strap bands & studs at z=12, 26, 40 -> -metal
    for zb in (12, 26, 40):
        if zb < z_top - 1:
            B(x, x, 27, 27, zb, zb + 1, BRONZE, mt)
# Bronze lion-ring door knockers
for kx in (64, 76):
    B(kx - 1, kx + 1, 26, 27, 20, 22, GOLD, mt)

# Four Fluted Classical Triumphal Columns on Tall Pedestals (x=39, 49, 90, 100; y=9)
for col_x in (39, 49, 90, 100):
    B(col_x - 3, col_x + 3, 6, 13, 2, 14, MARBLE)     # Pedestal base & die
    B(col_x - 2, col_x + 2, 7, 13, 5, 11, PORPH)      # Verona red marble inset panel
    B(col_x - 4, col_x + 4, 5, 13, 14, 15, MARBLE)    # Pedestal cap
    cyl_z(col_x, 9, 16, 51, 2.7, MARBLE, flute=True)  # Fluted column shaft
    B(col_x - 3, col_x + 3, 6, 12, 16, 17, MARBLE)    # Attic base
    B(col_x - 3, col_x + 3, 6, 12, 52, 55, STONE)     # Corinthian capital
    B(col_x - 4, col_x + 4, 5, 13, 54, 55, MARBLE)    # Capital abacus
    # Engaged pilaster respond on wall behind each column
    B(col_x - 2, col_x + 2, 12, 14, 16, 55, STONE)

# Verona marble spandrel medallions flanked between inner columns & arch
for mx in (53, 86):
    B(mx - 2, mx + 2, 12, 12, 42, 46, PORPH)

# 5. Main Triumphal Entablature (z=56..69)
B(34, 105, 5, 42, 56, 58, MARBLE)      # Projecting Architrave
B(34, 105, 7, 41, 59, 64, PORPH)       # Rich Porphyry/Verona marble frieze!
# Gold inscription bands across front frieze ("VICTORIAE NAVALI..." 1571 / 1460)
for x in range(40, 100, 3):
    B(x, x + 1, 6, 6, 61, 62, GOLD_S, mt)
B(33, 106, 4, 43, 65, 69, MARBLE)      # Deep overhanging classical cornice
for x in range(34, 105, 3):
    B(x, x, 5, 5, 67, 67, STONE_S)

# 6. Attic Story & Winged Lion of San Marco Tympanum Relief (z=70..112)
# Stepped back slightly (y=15..38)
B(34, 105, 15, 38, 70, 112, STONE)
# 4 upper Corinthian pilasters aligned over ground columns (y=13..15)
for px in (39, 49, 90, 100):
    B(px - 2, px + 2, 12, 14, 70, 104, MARBLE)
    B(px - 3, px + 3, 11, 14, 102, 105, STONE)
# Framed Tympanum Niche (x=53..86, y=13..16, z=72..103) — recess PORPH inside MARBLE frame!
B(53, 86, 13, 14, 72, 103, MARBLE)     # Outer Istrian marble frame border
B(55, 84, 13, 14, 74, 101, 0)          # Hollow frame interior so recessed porphyry shows cleanly!
B(55, 84, 15, 16, 74, 101, PORPH)      # Deep dark Verona/porphyry backing recessed at y=15!
# Sculpted Winged Lion of San Marco (in gilded bronze -metal + white Gospel book in body!)
# Distinct crouching winged Lion facing left->right inside recessed porphyry niche (y=12..14)
B(61, 71, 13, 14, 79, 85, GOLD, mt)    # Lion haunches & body
B(70, 75, 12, 14, 83, 89, GOLD, mt)    # Noble shaggy mane & leonine chest
B(72, 76, 11, 13, 89, 93, GOLD, mt)    # Lion head & muzzle
B(57, 66, 13, 14, 86, 94, GOLD, mt)    # Sweeping main wing base
for i_w, (wx, wz) in enumerate(((56, 95), (58, 97), (61, 98), (64, 96))):
    B(wx, wx + 1, 13, 14, 88, wz, GOLD, mt)  # Feathered wingtips
B(71, 77, 13, 14, 93, 97, MARBLE)      # White/gold stone nimbus arc behind head
B(72, 76, 12, 14, 94, 96, GOLD_S, mt)  # Halo core
B(58, 61, 13, 14, 77, 81, GOLD_S, mt)  # Raised arched tail + hind paw
B(74, 82, 12, 14, 76, 81, MARBLE)      # Open white stone Gospel book ("PAX TIBI MARCE")
B(71, 75, 12, 13, 79, 82, GOLD_S, mt)  # Right forepaw resting on Gospel book!
# Winged relief inscription plaque beneath Lion
B(56, 83, 12, 13, 70, 73, MARBLE)
for x in range(58, 82, 3):
    B(x, x + 1, 11, 11, 71, 71, GOLD_S, mt)

# 7. Crowning Classical Pediment (z=106..132) + Santa Giustina Statue (1578, z=133..150)
B(34, 105, 11, 39, 106, 112, MARBLE)   # Attic cornice
# Sloping pediment gable triangle centered at x=69..70 (x=42..97, width 56 -> height 18!)
for dz in range(20):
    hw = int(28 * (1.0 - dz / 20.0))
    if hw >= 0:
        B(69 - hw, 70 + hw, 12, 34, 113 + dz, 113 + dz, STONE)
        # Sloping raking marble cornice border
        B(69 - hw - 1, 69 - hw + 1, 10, 35, 113 + dz, min(133, 113 + dz + 1), MARBLE)
        B(70 + hw - 1, 70 + hw + 1, 10, 35, 113 + dz, min(133, 113 + dz + 1), MARBLE)
# Gilded sunburst emblem inside pediment triangle
B(67, 72, 11, 11, 117, 122, GOLD, mt)

# Central Statue of Santa Giustina (1578 victory of Lepanto!) on apex acroterion
B(66, 73, 13, 19, 133, 135, MARBLE)    # Pedestal
B(68, 71, 15, 17, 136, 146, MARBLE)    # Standing figure draped robes
B(69, 70, 15, 17, 147, 149, STONE)     # Head & crown
B(67, 67, 14, 15, 141, 148, GOLD, mt)  # Palm branch / sword attribute held high

# Left & Right corner acroteria urns/obelisk finials on attic shoulders (x=43, 96)
for ax in (43, 96):
    B(ax - 2, ax + 2, 13, 17, 113, 118, MARBLE)
    B(ax - 1, ax + 1, 14, 16, 119, 125, STONE)
    B(ax, ax, 15, 15, 126, 128, GOLD, mt)

# 8. Two Wrought-Iron Gate Lantern Brackets mounted between paired columns (x=44, 95, y=4..9, z=32..48)
# Leave hollow center pocket at (44, 5, 42) and (95, 5, 42) for beacon-flame models!
for lx in (44, 95):
    # Iron wall plate & scroll bracket projecting out to y=5
    B(lx, lx, 8, 13, 33, 35, IRON, mt)
    B(lx, lx, 5, 8, 34, 34, IRON, mt)
    # Bottom lantern tray (z=36) & top canopy (z=48..50) leaving z=37..47 open inside for flame
    B(lx - 2, lx + 2, 3, 7, 36, 36, IRON, mt)
    for cx, cy in ((lx - 2, 3), (lx + 2, 3), (lx - 2, 7), (lx + 2, 7)):
        B(cx, cx, cy, cy, 37, 47, IRON, mt)
    B(lx - 2, lx + 2, 3, 7, 48, 48, IRON, mt)
    B(lx - 1, lx + 1, 4, 6, 49, 50, GOLD_S, mt)

# Enforce disjointness
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
print(f'Porta Magna (1460/1666, NO 1687 lions) generated: body={nb}, metal={nm}')
