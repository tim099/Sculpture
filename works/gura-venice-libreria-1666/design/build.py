# -*- coding: utf-8 -*-
"""Libreria Nazionale Marciana (Venice 1666, Sansovino 1537-53 + Scamozzi 1588).
0.2 m/voxel, 200 x 70 x 105 (40 m along Piazzetta x 14 m deep x 21 m high).
y=0 faces EAST toward Piazzetta San Marco & Palazzo Ducale (rot=0).
"""
import os
import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))
MASK_DIR = os.path.join(OUT, 'masks')
os.makedirs(MASK_DIR, exist_ok=True)

SX, SY, SZ = 200, 70, 105

MARBLE = 254     # #ffffaa Istrian white limestone
STONE = 218      # #dadaaa warm limestone / marmorino
STONE_S = 182    # #b6b6aa shaded limestone / lead roof
PAVE = 146       # #9191aa trachyte paving / lead seam
DARK = 36        # #242400 deep shadow / doorway recess
GOLD_S = 212     # #dab600 muted antique gold relief
GOLD = 248       # #ffda00 bright gilded sphere finials
WOOD = 104       # #6d4800 panelled oak doors
WOOD_D = 68      # #482400 dark timber
GLASS = 46       # #246daa leaded window glass

g = np.zeros((SX, SY, SZ), np.uint8)
gl = np.zeros((SX, SY, SZ), bool)
mt = np.zeros((SX, SY, SZ), np.uint8)


def B(x0, x1, y0, y1, z0, z1, c, arr=None):
    a = g if arr is None else arr
    x0, x1 = max(0, int(x0)), min(SX - 1, int(x1))
    y0, y1 = max(0, int(y0)), min(SY - 1, int(y1))
    z0, z1 = max(0, int(z0)), min(SZ - 1, int(z1))
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        a[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = c


def cut(x0, x1, y0, y1, z0, z1):
    B(x0, x1, y0, y1, z0, z1, 0, g)
    B(x0, x1, y0, y1, z0, z1, False, gl)


def carve_arch_x(x_c, half_w, y0, y1, z_bot, z_spring, glass_y=None):
    """Carve a flat-topped-to-semicircular arch opening along y-axis centered at x_c."""
    for dx in range(-half_w, half_w + 1):
        x = x_c + dx
        h_arc = int(round((max(0.0, (half_w + 0.3) ** 2 - dx * dx)) ** 0.5))
        z_top = z_spring + h_arc
        cut(x, x, y0, y1, z_bot, z_top)
        if glass_y is not None:
            B(x, x, glass_y, glass_y, z_bot + 1, z_top - 1, True, gl)


def carve_arch_y(y_c, half_w, x0, x1, z_bot, z_spring, glass_x=None):
    for dy in range(-half_w, half_w + 1):
        y = y_c + dy
        h_arc = int(round((max(0.0, (half_w + 0.3) ** 2 - dy * dy)) ** 0.5))
        z_top = z_spring + h_arc
        cut(x0, x1, y, y, z_bot, z_top)
        if glass_x is not None:
            B(glass_x, glass_x, y, y, z_bot + 1, z_top - 1, True, gl)


# 1. Stepped Istrian marble stylobate & portico deck (z=0..3)
B(0, SX - 1, 0, SY - 1, 0, 0, PAVE)
B(0, SX - 1, 1, SY - 1, 1, 1, STONE_S)
B(0, SX - 1, 2, SY - 1, 2, 2, MARBLE)
B(0, SX - 1, 3, SY - 1, 3, 3, STONE)
# Alternating piazza border pavers on steps & porch
for x in range(0, SX, 5):
    B(x, x, 3, 21, 3, 3, MARBLE)

# 2. Core building volume (z=4..93)
# Front wall of closed ground archive rooms at y=22..66; open portico at y=3..21!
B(0, SX - 1, 22, 66, 4, 45, STONE)
# Main Piano Nobile & frieze core (y=7..66)
B(0, SX - 1, 7, 66, 46, 93, STONE)

# Interior rooms (ground archive bays + grand Piano Nobile Salone)
cut(8, SX - 9, 27, 61, 4, 41)
B(0, SX - 1, 22, 66, 42, 46, STONE)      # Piano Nobile floor slab
cut(8, SX - 9, 13, 61, 47, 81)          # Salone grand hall
B(0, SX - 1, 7, 66, 82, 84, WOOD)       # Coffered wooden hall ceiling under entablature
# Interior gilt ribs & bookcases in Salone
for x in range(15, SX - 10, 15):
    B(x, x + 1, 13, 61, 81, 82, GOLD_S)
B(8, SX - 9, 58, 60, 47, 68, WOOD_D)    # Renaissance wall bookcases
for x in range(12, SX - 10, 6):
    B(x, x, 57, 57, 48, 67, GOLD_S)

# Ground portico inner rear wall recessed doors (every 2nd bay + central grand portal)
for i in range(13):
    xc = 15 * i + 9
    if i % 2 == 0 or i == 6:
        B(xc - 2, xc + 2, 22, 25, 4, 24, WOOD_D)
        B(xc - 3, xc + 3, 21, 21, 4, 26, MARBLE)
        if i == 6:  # Central portal archway into Libreria staircase
            B(xc - 3, xc + 3, 21, 22, 27, 30, MARBLE)
            B(xc - 1, xc + 1, 21, 21, 27, 29, GOLD_S)
    # Blind arcade niches in other ground bays
    else:
        cut(xc - 2, xc + 2, 22, 23, 8, 25)
        B(xc - 2, xc + 2, 24, 24, 8, 25, DARK)

# 3. Piazzetta East Front (y=4..10) + Side Gables: 13 Classical Doric + Ionic Bays
# 14 piers at [15*i .. 15*i+4] (center cx = 15*i+2)
# 13 bays  at [15*i+5 .. 15*i+14] (center bx = 15*i+9..10)
for i in range(14):
    px = 15 * i
    # Ground Doric Pier & Engaged Half-Column (z=4..37)
    B(px, px + 4, 5, 21, 4, 37, STONE)          # Pier into portico
    B(px, px + 4, 4, 4, 4, 9, MARBLE)           # Column plinth
    B(px + 1, px + 3, 3, 4, 10, 32, MARBLE)     # Engaged Doric shaft protruding to y=3
    B(px, px + 4, 3, 4, 33, 35, MARBLE)         # Doric capital & necking
    # Portico transverse stone vault springers inside loggia (y=6..21)
    B(px + 1, px + 3, 6, 21, 32, 37, STONE)

    # Upper Ionic Pier & Engaged Fluted Half-Column (z=46..82)
    B(px, px + 4, 5, 7, 46, 50, MARBLE)         # Pedestal under Ionic order
    B(px + 1, px + 3, 4, 6, 51, 75, MARBLE)     # Ionic column shaft (y=4 protrude)
    B(px, px + 4, 4, 6, 76, 78, MARBLE)         # Ionic volute capital
    B(px, px + 4, 5, 6, 77, 77, GOLD_S)         # Volute eye highlight

for i in range(13):
    bx0, bx1 = 15 * i + 5, 15 * i + 14
    bc = 15 * i + 9
    # Ground Doric Arch opening (portico open y=4..12!)
    B(bx0, bx1, 5, 11, 4, 37, STONE)
    carve_arch_x(bc, 4, 4, 13, z_bot=4, z_spring=26)
    # Archivolts & sculpted keystone
    for dx in range(-5, 6):
        z_a = 27 + int(round(max(0.0, 26.0 - dx * dx) ** 0.5))
        if 27 <= z_a <= 36:
            B(bc + dx, bc + dx, 4, 5, z_a, min(36, z_a + 1), MARBLE)
    B(bc, bc + 1, 3, 5, 31, 34, MARBLE)  # Projecting keystone

    # Piano Nobile Balustrade sill (z=46..51)
    B(bx0, bx1, 5, 6, 46, 47, MARBLE)
    for x in range(bx0 + 1, bx1, 2):
        B(x, x, 5, 5, 48, 49, STONE)
    B(bx0, bx1, 4, 6, 50, 50, MARBLE)

    # Palladian/Serlian window with twin minor Ionic colonnettes + glass!
    # Outer wall frame at y=6..10, recessed window opening y=6..13
    B(bx0, bx1, 6, 12, 51, 82, STONE)
    # Paired minor frame mullions at edges of bay
    B(bx0, bx0 + 1, 5, 7, 51, 70, MARBLE)
    B(bx1 - 1, bx1, 5, 7, 51, 70, MARBLE)
    # Main tall arched window cut + glass pane at y=9
    carve_arch_x(bc, 3, 5, 13, z_bot=51, z_spring=67, glass_y=9)
    # Center transom mullion bar inside window (without blocking light continuity badly)
    B(bc, bc, 8, 8, 51, 67, STONE_S)
    # Arched limestone surround & gilded spandrel rosettes
    B(bc, bc + 1, 5, 6, 71, 73, MARBLE)
    B(bx0 + 1, bx0 + 1, 5, 5, 73, 74, GOLD_S)
    B(bx1 - 1, bx1 - 1, 5, 5, 73, 74, GOLD_S)

# 4. Doric Entablature (z=38..45) — Triglyphs & Metopes along y=3..7
B(0, SX - 1, 4, 7, 38, 39, MARBLE)      # Architrave
B(0, SX - 1, 4, 7, 40, 42, STONE)       # Frieze backing
for x in range(2, SX - 1, 7):
    B(x - 1, x + 1, 3, 4, 40, 42, STONE_S)  # Triglyphs
    if x + 4 < SX - 2:
        B(x + 3, x + 4, 3, 3, 41, 41, GOLD_S)  # Carved metope patera boss
B(0, SX - 1, 2, 7, 43, 45, MARBLE)      # Deep projecting Doric cornice

# 5. Upper Ionic Entablature + Iconic Putti/Festoon Frieze + Oval Windows (z=79..93)
B(0, SX - 1, 4, 67, 79, 80, MARBLE)     # Architrave all around
B(0, SX - 1, 4, 67, 81, 87, STONE)      # Tall sculpted frieze
# Carved festoon swags & tiny oval attic windows centered on each bay!
for i in range(13):
    bc = 15 * i + 9
    cut(bc - 1, bc + 1, 4, 10, 83, 84)
    B(bc - 1, bc + 1, 6, 6, 83, 84, True, gl)  # Oval oculus glass!
    # Garlands hanging left and right of oval window
    for dx in range(-5, 6):
        zz = 82 if abs(dx) >= 4 else 81
        B(bc + dx, bc + dx, 3, 3, zz, zz + 1, GOLD_S if abs(dx) in (3, 4) else MARBLE)
# Grand overhanging crowning cornice (z=88..93)
B(0, SX - 1, 3, 68, 88, 89, MARBLE)
B(0, SX - 1, 2, 68, 90, 91, STONE)
B(0, SX - 1, 1, 69, 92, 93, MARBLE)
for x in range(1, SX - 1, 3):
    B(x, x, 2, 2, 91, 91, MARBLE)       # Modillions/dentils under crown cornice

# 6. Rear West Facade (y=65..67) & Side Facades facing Campanile (x=196..199) & Molo (x=0..4)
# Molo South end (x=0..4, 3 classical arched bays across y=10..62) & North end (x=195..199)
for side_x, wall_x, in_x, gx in [(0, 4, 12, 7), (SX - 1, SX - 5, SX - 13, SX - 8)]:
    # 3 bays across depth y = 16, 33, 50
    for yc in (18, 35, 52):
        # Ground closed blind arch / window
        carve_arch_y(yc, 3, min(side_x, wall_x), max(side_x, wall_x), z_bot=10, z_spring=26, glass_x=min(side_x, wall_x) + (2 if side_x == 0 else -2))
        # Upper Piano Nobile Ionic arched window
        x_lo = 0 if side_x == 0 else SX - 13
        x_hi = 12 if side_x == 0 else SX - 1
        carve_arch_y(yc, 3, x_lo, x_hi, z_bot=51, z_spring=67, glass_x=gx)

# Rear West Facade (y=64..66 facing Zecca courtyard / calle): ordered Venetian windows
for i in range(13):
    bc = 15 * i + 9
    carve_arch_x(bc, 2, 60, 67, z_bot=52, z_spring=66, glass_y=64)
    if i % 3 == 1:
        carve_arch_x(bc, 2, 60, 67, z_bot=10, z_spring=24, glass_y=64)

# Ensure bottom wall & Doric entablature corner return around Molo/North sides (y=7..21, z=38..45)
B(0, 4, 3, 66, 4, 10, STONE)
B(SX - 5, SX - 1, 3, 66, 4, 10, STONE)
B(0, 4, 4, 22, 38, 45, MARBLE)
B(SX - 5, SX - 1, 4, 22, 38, 45, MARBLE)
# Continue Doric cornice band (z=43..45) cleanly along Molo/North and Rear walls
B(0, 3, 4, 67, 43, 45, MARBLE)
B(SX - 4, SX - 1, 4, 67, 43, 45, MARBLE)
B(0, SX - 1, 66, 68, 43, 45, MARBLE)

# 7. Rooftop Balustrade, Classical Statues, Corner Obelisks & Lead Roof (z=94..104)
B(3, SX - 4, 6, 65, 94, 94, STONE_S)    # Roof deck seal
# Low hipped Venetian lead roof (z=94..99)
for dz in range(6):
    margin = 10 + dz * 4
    if margin < 32:
        B(margin, SX - 1 - margin, margin, SY - 1 - margin, 94 + dz, 94 + dz, PAVE if dz % 2 else STONE_S)

# Perimeter Istrian stone balustrade (z=94..97)
# Front (y=4..5), Back (y=65..66), Left (x=2..3), Right (x=196..197)
for x in range(2, SX - 2):
    if x % 3 != 1:
        B(x, x, 4, 4, 94, 96, STONE)
        B(x, x, 66, 66, 94, 96, STONE)
    B(x, x, 3, 5, 97, 97, MARBLE)
    B(x, x, 65, 67, 97, 97, MARBLE)
for y in range(4, 67):
    if y % 3 != 1:
        B(2, 2, y, y, 94, 96, STONE)
        B(SX - 3, SX - 3, y, y, 94, 96, STONE)
    B(2, 3, y, y, 97, 97, MARBLE)
    B(SX - 4, SX - 3, y, y, 97, 97, MARBLE)

# Statues above the 14 front piers (z=98..103) + Molo/North piers (y=26,44)
def add_statue(cx, cy, z0=98):
    B(cx - 1, cx + 1, cy - 1, cy + 1, z0, z0, MARBLE)      # Plinth
    B(cx, cx + 1, cy, cy, z0 + 1, z0 + 4, MARBLE)          # Draped body (leaning lightly)
    B(cx, cx, cy, cy, z0 + 5, z0 + 5, STONE)               # Head
    B(cx + 1, cx + 1, cy - 1, cy, z0 + 3, z0 + 4, MARBLE)  # Extended sculptural arm

for i in range(1, 13):
    add_statue(15 * i + 2, 4, 98)
    if i % 2 == 0:
        add_statue(15 * i + 2, 66, 98)
for yc in (26, 44):
    add_statue(2, yc, 98)
    add_statue(SX - 3, yc, 98)

# 4 Taller Corner Obelisks on balustrade pedestals (bronze gilded sphere on top -> mt!)
for cx, cy in ((2, 4), (SX - 3, 4), (2, 66), (SX - 3, 66)):
    B(cx - 1, cx + 1, cy - 1, cy + 1, 98, 99, MARBLE)
    B(cx, cx, cy, cy, 100, 102, STONE)
    B(cx, cx, cy, cy, 103, 104, GOLD, mt)

# Final disjointness enforcement (body vs glass vs metal)
g[gl] = 0
g[mt > 0] = 0
gl[g > 0] = False
gl[mt > 0] = False


def dump(arr, path, col=None):
    xs, ys, zs = np.nonzero(arr)
    cs = arr[xs, ys, zs] if col is None else np.full(len(xs), col, dtype=np.uint8)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for x, y, z, c in zip(xs.tolist(), ys.tolist(), zs.tolist(), cs.tolist()):
            f.write(f'{x},{y},{z},{c}\n')
    return len(xs)


nb = dump(g, os.path.join(MASK_DIR, 'body.txt'))
ng = dump(gl, os.path.join(MASK_DIR, 'glass.txt'), GLASS)
nm = dump(mt, os.path.join(MASK_DIR, 'metal.txt'))
print(f'Libreria Marciana generated: body={nb}, glass={ng}, metal={nm}')
