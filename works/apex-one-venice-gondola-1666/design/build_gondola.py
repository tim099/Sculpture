#!/usr/bin/env python3
"""
Deterministic 1666 Venetian Open-Cabin Gondola Generator (0.05 m/voxel).
Produces:
  - design/voxels_hull.txt   (for apex-one-venice-gondola-1666-hull)
  - design/voxels_ferro.txt  (for apex-one-venice-gondola-1666-ferro, material=iron)
  - design/voxels_oar.txt    (for apex-one-venice-gondola-1666-oar, 4.20 m standing remo)
  - design/sheets/sheet01_gondola_1666.png (annotated 2D blueprint)
  - design/metrics_step2.json
"""
import json
import math
import os
from collections import deque
from PIL import Image, ImageDraw, ImageFont

WORK_DIR = r"D:\Unity\Valhalla\Sculpture\works\apex-one-venice-gondola-1666"
DESIGN_DIR = os.path.join(WORK_DIR, "design")
SHEETS_DIR = os.path.join(DESIGN_DIR, "sheets")
os.makedirs(SHEETS_DIR, exist_ok=True)

SCALE_M = 0.05  # 0.05 m / voxel

# RGB332 palette indices (verified against SCP_CanvasPalette.cs)
C_PITCH_DARK = 36    # (36, 36, 0)    sumptuary pitched black hull planks
C_PITCH_ALT  = 72    # (72, 72, 0)    deep tarred oak seam highlight
C_PITCH_RIB  = 73    # (72, 72, 85)   charcoal inner frame / trim
C_WALNUT     = 104   # (109, 72, 0)   carved walnut gunwale / forcola / armrest
C_OAK        = 177   # (182, 145, 85) warm oiled honey oak paioli & poppa deck planks
C_ASH        = 177   # (182, 145, 85) natural beech/ash remo oar
C_CUSHION    = 36    # (36, 36, 0)    sumptuary pitched-black Venetian leather cushion
C_CUSH_TRIM  = 100   # (109, 36, 0)   dark oxblood-brown leather bolster trim
C_BRASS      = 176   # (182, 145, 0)  brass ring / fore cleat pin
C_IRON_DARK  = 109   # (109, 109, 85) wrought iron stem collar
C_IRON_BODY  = 146   # (145, 145, 170) forged iron ferro neck & prongs
C_IRON_EDGE  = 182   # (182, 182, 170) burnished iron halberd blade edge

SIZE_HULL = (220, 70, 50)
SIZE_OAR  = (12, 88, 12)

Y_MIN_CENT = 35
Y_MAX_CENT = 34  # symmetric pair around y_cl = 34.5: [35-hw, 34+hw]


def z_keel(x: int) -> int:
    """Bottom keel z (voxel index) along X=[12..203]. Waterline is z=4 (0.20 m)."""
    if 46 <= x <= 170:
        return 0
    if x > 170:
        u = min(1.0, (x - 170) / 33.0)
        return int(round(16.0 * (u ** 2.35)))
    u = min(1.0, (46 - x) / 34.0)
    return int(round(14.0 * (u ** 2.35)))


def z_sheer(x: int) -> int:
    """Gunwale top z (voxel index). Midships z=9 (top 0.50m = +0.30m freeboard)."""
    dx = abs(x - 108)
    if x >= 108:
        u = min(1.0, dx / 95.0)
        return 9 + int(round(11.0 * (u ** 2.2)))
    u = min(1.0, dx / 96.0)
    return 9 + int(round(8.0 * (u ** 2.1)))


def beam_frac(x: int) -> float:
    if x >= 108:
        t = min(1.0, (x - 108) / 95.0)
    else:
        t = min(1.0, (108 - x) / 96.0)
    return max(0.0, math.cos(t * math.pi * 0.5)) ** 0.72


def hw_bot(x: int) -> int:
    return max(1, int(round(9.0 * beam_frac(x))))


def hw_top(x: int) -> int:
    return max(1, int(round(14.0 * beam_frac(x))))


def put(vox: dict, x: int, y: int, z: int, c: int, size: tuple):
    if 0 <= x < size[0] and 0 <= y < size[1] and 0 <= z < size[2]:
        vox[(x, y, z)] = c


def paint_pair_y(vox: dict, x: int, hw: int, z: int, c: int, size=SIZE_HULL):
    put(vox, x, Y_MIN_CENT - hw, z, c, size)
    put(vox, x, Y_MAX_CENT + hw, z, c, size)


def build_hull() -> dict:
    vox = {}
    # 1. Outer watertight-feeling shell with guaranteed 6-connectivity
    prev_zk, prev_zs, prev_hb, prev_ht = None, None, None, None
    for x in range(12, 204):
        zk = z_keel(x)
        zs = z_sheer(x)
        hb = hw_bot(x)
        ht = hw_top(x)

        # Flat bottom *fondo*
        y0, y1 = Y_MIN_CENT - hb, Y_MAX_CENT + hb
        for y in range(y0, y1 + 1):
            col = C_PITCH_DARK if (x + y) % 5 != 0 else C_PITCH_ALT
            put(vox, x, y, zk, col, SIZE_HULL)

        # Connect keel steps between adjacent x slices so no diagonal X-Z disconnect
        if prev_zk is not None and zk != prev_zk:
            z_lo, z_hi = min(zk, prev_zk), max(zk, prev_zk)
            hb_c = min(hb, prev_hb)
            for zz in range(z_lo, z_hi + 1):
                for y in range(Y_MIN_CENT - hb_c, Y_MAX_CENT + hb_c + 1):
                    put(vox, x, y, zz, C_PITCH_DARK, SIZE_HULL)

        # Solidify extreme narrow stem/stern *asta* fins so they hold heavy ferro cleanly
        if ht <= 2 or x <= 20 or x >= 195:
            for zz in range(zk, zs + 1):
                frac_z = 0.0 if zs == zk else (zz - zk) / float(zs - zk)
                hw_here = max(1, int(round(hb + (ht - hb) * frac_z)))
                for y in range(Y_MIN_CENT - hw_here, Y_MAX_CENT + hw_here + 1):
                    col = C_WALNUT if zz == zs else (C_PITCH_ALT if zz == zs - 1 else C_PITCH_DARK)
                    put(vox, x, y, zz, col, SIZE_HULL)
        else:
            # Flared hull sides (*sponde*) from (hb, zk) to (ht, zs)
            n_steps = max(40, (zs - zk) * 6 + abs(ht - hb) * 6)
            last_hw, last_z = hb, zk
            for s in range(n_steps + 1):
                f = s / float(n_steps)
                # Slight flare curve
                f_y = f ** 0.78
                hw_f = int(round(hb + (ht - hb) * f_y))
                zz = int(round(zk + (zs - zk) * f))
                # Step orthogonally if both changed
                if hw_f != last_hw and zz != last_z:
                    paint_pair_y(vox, x, hw_f, last_z, C_PITCH_DARK)
                col = C_WALNUT if zz == zs else (C_PITCH_ALT if zz == zs - 1 else C_PITCH_DARK)
                paint_pair_y(vox, x, hw_f, zz, col)
                last_hw, last_z = hw_f, zz

            # Ensure 6-connected join to previous x slice on side walls
            if prev_ht is not None and abs(ht - prev_ht) > 0:
                for hh in range(min(ht, prev_ht), max(ht, prev_ht) + 1):
                    paint_pair_y(vox, x, hh, zs, C_WALNUT)

        prev_zk, prev_zs, prev_hb, prev_ht = zk, zs, hb, ht

    # 2. Inner ribs (*corbe*) every 8 voxels (0.40 m) in open passenger cockpit (z=1..3)
    for x in range(74, 138, 8):
        hb = hw_bot(x)
        for zz in (1, 2, 3):
            for y in range(Y_MIN_CENT - hb + 1, Y_MAX_CENT + hb):
                put(vox, x, y, zz, C_PITCH_RIB, SIZE_HULL)

    # 3. Dry Slatted Floorboards (*paioli*) inside cockpit & footwell (x = 70..136, z = 4 => top 0.25 m DRY above WL z=4!)
    # Connected cleanly onto transverse ribs z=1..3 while leaving bilge end passages open so zero enclosed air cavities!
    for x in range(70, 137):
        hb_in = max(2, hw_bot(x) - 1)
        for y in range(Y_MIN_CENT - hb_in, Y_MAX_CENT + hb_in + 1):
            col = C_OAK if y % 3 != 0 else C_WALNUT
            put(vox, x, y, 4, col, SIZE_HULL)
        # Ensure continuous connection from flared chine bottom up to z=4 around cockpit perimeter
        hb_wall = hw_bot(x) + 1
        paint_pair_y(vox, x, hb_wall, 3, C_PITCH_DARK)

    # 4. Foredeck (*coperta di prua*, x = 138..194)
    # Tightly seals to flared hull wall along z_deck & z_deck-1 while leaving central limber gap open below at x=138..141!
    for x in range(138, 195):
        zs = z_sheer(x)
        ht = hw_top(x)
        z_deck = zs - 1
        crown = 1 if 144 <= x <= 184 else 0
        for y in range(Y_MIN_CENT - ht + 1, Y_MAX_CENT + ht):
            dy = abs(y - 34.5)
            if x == 138 or y in (34, 35):
                col_base = C_WALNUT
            elif int(round(dy)) in (3, 6, 9):
                col_base = C_PITCH_ALT
            else:
                col_base = C_PITCH_DARK
            put(vox, x, y, z_deck, col_base, SIZE_HULL)
            put(vox, x, y, z_deck - 1, C_PITCH_DARK, SIZE_HULL)
            if crown and dy <= max(1.0, ht * 0.45):
                put(vox, x, y, z_deck + 1, col_base, SIZE_HULL)
        # Decorative carved *fiubone* coaming arch at cockpit forward border x=138
        if x == 138:
            for y in range(Y_MIN_CENT - ht + 1, Y_MAX_CENT + ht):
                put(vox, x, y, z_deck + 1, C_WALNUT, SIZE_HULL)
    # Forward brass mooring cleat sitting directly atop foredeck (z_sheer(191) = z_deck + 1)
    put(vox, 191, 34, z_sheer(191), C_BRASS, SIZE_HULL)
    put(vox, 191, 35, z_sheer(191), C_BRASS, SIZE_HULL)

    # 5. Stern *poppa* standing deck (*coperta di poppa*, x = 30..69)
    # Standing surface at z_top = 11*0.05 = 0.55 m (+0.35 m above WL) -> top voxel z=10!
    for x in range(30, 70):
        ht = hw_top(x)
        z_pop = 10
        for y in range(Y_MIN_CENT - ht + 1, Y_MAX_CENT + ht):
            if 32 <= x <= 66:
                col = C_OAK if x % 2 == 0 else C_WALNUT
            else:
                col = C_PITCH_DARK
            put(vox, x, y, z_pop, col, SIZE_HULL)
            put(vox, x, y, z_pop - 1, C_PITCH_DARK, SIZE_HULL)
        # Forward step bulkhead edge at x=69 down to z=4 (leave central passage y=32..37 open => zero enclosed cavities!)
        if x == 69:
            hb_69 = hw_bot(x)
            for y in range(Y_MIN_CENT - hb_69 + 1, Y_MAX_CENT + hb_69):
                if not (32 <= y <= 37):
                    for zz in range(5, z_pop):
                        put(vox, x, y, zz, C_PITCH_DARK, SIZE_HULL)
                else:
                    put(vox, x, y, z_pop - 1, C_WALNUT, SIZE_HULL)

    # 6. Open-cabin passenger seating (*parecio*, x = 76..129)
    # 6a. Main transverse *trasto* sofa (x = 78..90, seat z = 8 => top 0.45m = +0.25m WL; backrest x=76..79 z = 9..16 => top 0.85m = +0.65m WL)
    for x in range(77, 91):
        ht_s = hw_top(x)
        hb_s = hw_bot(x)
        for y in range(Y_MIN_CENT - ht_s + 2, Y_MAX_CENT + ht_s - 1):
            y_in_p, y_in_s = Y_MIN_CENT - hb_s + 1, Y_MAX_CENT + hb_s - 1
            if x in (77, 90) and y in (y_in_p, y_in_s):
                for zz in range(5, 7):
                    put(vox, x, y, zz, C_WALNUT, SIZE_HULL)
            put(vox, x, y, 7, C_WALNUT, SIZE_HULL)
            col_c = C_CUSH_TRIM if (x == 90 or abs(y - 34.5) > ht_s - 3) else C_CUSHION
            put(vox, x, y, 8, col_c, SIZE_HULL)

    # *Trasto* upholstered backrest (x = 76..79, rising to z = 16 -> top +0.65 m above WL)
    for x in range(76, 80):
        ht_b = hw_top(x)
        for y in range(Y_MIN_CENT - ht_b + 2, Y_MAX_CENT + ht_b - 1):
            top_z = 16 if (Y_MIN_CENT - ht_b + 4 <= y <= Y_MAX_CENT + ht_b - 3) else 15
            for zz in range(9, top_z + 1):
                if x >= 78 and zz >= 14:
                    continue
                if zz == top_z or x == 76:
                    col = C_WALNUT
                elif zz == 15:
                    col = C_CUSH_TRIM
                else:
                    col = C_CUSHION
                put(vox, x, y, zz, col, SIZE_HULL)

    # Carved armrests (*braccioli*) along cockpit gunwale beside *trasto*
    for x in range(78, 92):
        ht_a = hw_top(x)
        for zz in range(9, 13):
            if zz == 12 and x in (78, 91):
                continue
            put(vox, x, Y_MIN_CENT - ht_a + 1, zz, C_WALNUT, SIZE_HULL)
            put(vox, x, Y_MAX_CENT + ht_a - 1, zz, C_WALNUT, SIZE_HULL)

    # 6b. Side benches (*banchette*, x = 91..126 along port & starboard inside coaming)
    for x in range(91, 127):
        ht_l = hw_top(x)
        hb_l = hw_bot(x)
        y_pl_out = Y_MIN_CENT - ht_l + 1
        y_sb_out = Y_MAX_CENT + ht_l - 1
        for d in range(4):
            yp = y_pl_out + d
            ys = y_sb_out - d
            put(vox, x, yp, 7, C_WALNUT, SIZE_HULL)
            put(vox, x, ys, 7, C_WALNUT, SIZE_HULL)
            col = C_CUSH_TRIM if d == 3 else C_CUSHION
            put(vox, x, yp, 8, col, SIZE_HULL)
            put(vox, x, ys, 8, col, SIZE_HULL)
        if x in (106, 124):
            for zz in range(5, 7):
                put(vox, x, Y_MIN_CENT - hb_l + 2, zz, C_WALNUT, SIZE_HULL)
                put(vox, x, Y_MAX_CENT + hb_l - 2, zz, C_WALNUT, SIZE_HULL)

    # 7. Carved Starboard *Forcola* Oarlock Post (x = 46..50, y = 43..44, z = 11..18)
    # Pivot crotch notch centered at (48.5, 43.5, 16.5) -> clear jaw opening along angled oar shaft
    for x in range(46, 51):
        zs_f = z_sheer(x)
        ys_f = Y_MAX_CENT + hw_top(x)
        for zz in range(zs_f, 14):
            put(vox, x, ys_f, zz, C_WALNUT, SIZE_HULL)
            put(vox, x, ys_f + 1, zz, C_WALNUT, SIZE_HULL)
    # Forward rising walnut horn (*corno*) kept cleanly forward of the swinging oar at x=50, y=42..43
    for zz in range(14, 19):
        put(vox, 50, 42, zz, C_WALNUT, SIZE_HULL)
        put(vox, 50, 43, zz, C_OAK, SIZE_HULL)
    # Aft lower heel spur (*morso*) at x=46, y=43..44
    for zz in range(14, 17):
        put(vox, 46, 43, zz, C_WALNUT, SIZE_HULL)
        put(vox, 46, 44, zz, C_OAK, SIZE_HULL)
    # Base cradle across x=47..49 at z=14..15 (leaving open saddle above z=15 for pivot 16.5!)
    for x in (47, 48, 49):
        put(vox, x, 43, 14, C_WALNUT, SIZE_HULL)
        put(vox, x, 44, 14, C_WALNUT, SIZE_HULL)
    put(vox, 48, 43, 15, C_OAK, SIZE_HULL)

    return vox


def build_ferro(hull_vox: dict) -> dict:
    """
    17th-c. double-ended wrought-iron *ferri* (Küsel/Baur 1670 + May 2 1624 Proclama):
    - Bow ferro: x=201..214, z=15..24 (crest top 1.25 m above keel = +1.05 m above WL)
      Halberd-blade top + 4 forward blunted *brocche* prongs (2 vx = 10 cm).
    - Stern ferro: x=5..16, z=12..20 (crest top 1.05 m above keel = +0.85 m above WL)
      Backward halberd blade + 3 aft blunted *brocche* prongs (2 vx = 10 cm).
    Strictly avoids overlapping hull_vox while touching face-to-face!
    """
    vox = {}

    def put_iron(x, y, z, col):
        if (x, y, z) not in hull_vox:
            put(vox, x, y, z, col, SIZE_HULL)

    # Bow stem wooden tip reaches x=203, z=20 (y=34..35)
    # Iron collar wraps just ahead/above stem face at x=204 (and base shoe x=201..203 at z=21)
    # Rising S-curve neck (sleek 1670 Küsel/Baur silhouette + 1624 blunted prongs):
    bow_spine = [
        (202, 21, C_IRON_DARK), (203, 21, C_IRON_DARK), (204, 15, C_IRON_DARK),
        (204, 16, C_IRON_BODY), (204, 17, C_IRON_BODY), (204, 18, C_IRON_BODY),
        (204, 19, C_IRON_BODY), (204, 20, C_IRON_BODY), (204, 21, C_IRON_BODY),
        (205, 19, C_IRON_BODY), (205, 20, C_IRON_BODY), (205, 21, C_IRON_BODY), (205, 22, C_IRON_EDGE),
        (206, 21, C_IRON_BODY), (206, 22, C_IRON_EDGE), (206, 23, C_IRON_EDGE), (206, 24, C_IRON_EDGE),
        (207, 22, C_IRON_EDGE), (207, 23, C_IRON_EDGE), (207, 24, C_IRON_EDGE),
        (208, 22, C_IRON_EDGE), (208, 23, C_IRON_EDGE), (208, 24, C_IRON_EDGE),
        (209, 22, C_IRON_EDGE), (209, 23, C_IRON_EDGE), (209, 24, C_IRON_EDGE),
        (210, 21, C_IRON_EDGE), (210, 22, C_IRON_EDGE), (210, 23, C_IRON_EDGE),
        (211, 21, C_IRON_EDGE), (211, 22, C_IRON_EDGE),
        (212, 22, C_IRON_EDGE), (213, 22, C_IRON_EDGE), (213, 23, C_IRON_EDGE), (214, 22, C_IRON_EDGE),
    ]
    for x, z, col in bow_spine:
        for y in (34, 35):
            put_iron(x, y, z, col)

    # 4 crisp horizontal *brocche* prongs (2 voxels = 10 cm ahead of neck at z=16, 18, 20, 22; 1624 Proclama ~9 cm)
    for x, z in [
        (205, 16), (206, 16),
        (205, 18), (206, 18),
        (206, 20), (207, 20),
        (204, 22),  # back spur
    ]:
        for y in (34, 35):
            put_iron(x, y, z, C_IRON_EDGE if z >= 20 else C_IRON_BODY)

    # Stern stem wooden tip reaches x=12, z=17 (y=34..35)
    # Stern *ferro di poppa*: x=5..14, z=13..20 (top voxel z=20 -> top 1.05 m = +0.85 m above WL)
    stern_spine = [
        (13, 18, C_IRON_DARK), (12, 18, C_IRON_DARK),
        (11, 13, C_IRON_DARK), (11, 14, C_IRON_BODY), (11, 15, C_IRON_BODY), (11, 16, C_IRON_BODY),
        (11, 17, C_IRON_BODY), (11, 18, C_IRON_BODY),
        (10, 15, C_IRON_BODY), (10, 16, C_IRON_BODY), (10, 17, C_IRON_BODY), (10, 18, C_IRON_BODY), (10, 19, C_IRON_EDGE),
        (9, 17, C_IRON_BODY), (9, 18, C_IRON_EDGE), (9, 19, C_IRON_EDGE), (9, 20, C_IRON_EDGE),
        (8, 18, C_IRON_EDGE), (8, 19, C_IRON_EDGE), (8, 20, C_IRON_EDGE),
        (7, 18, C_IRON_EDGE), (7, 19, C_IRON_EDGE), (7, 20, C_IRON_EDGE),
        (6, 18, C_IRON_EDGE), (6, 19, C_IRON_EDGE),
        (5, 18, C_IRON_EDGE), (5, 19, C_IRON_EDGE),
    ]
    for x, z, col in stern_spine:
        for y in (34, 35):
            put_iron(x, y, z, col)

    # 3 aft blunt *brocche* prongs (5-10 cm outward astern at z=14, 16, 18)
    for x, z in [(10, 14), (9, 14), (9, 16), (8, 16), (12, 19)]:
        for y in (34, 35):
            put_iron(x, y, z, C_IRON_BODY)

    return vox


def build_oar() -> dict:
    """
    4.20 m canonical Venetian *remo* oar in `12 x 88 x 12` at 0.05 m/voxel.
    Runs along +Y from y=2 (grip top) to y=85 (blade tip) -> 84 voxels = 4.20 m.
    - Pivot at (5.5, 29.0, 5.5): 27 vx (1.35 m) inboard loom + 57 vx (2.85 m) outboard shaft & blade.
    - Blade (*pala*) spans y=69..85 (0.85 m), tapered 2->4 voxels wide in X (0.10 -> 0.20 m), 2 vx thick in Z.
    """
    vox = {}
    for y in range(2, 86):
        if y <= 7:
            # Upper grip handle *impugnatura*
            for x in (5, 6):
                put(vox, x, y, 5, C_WALNUT if y <= 3 else C_ASH, SIZE_OAR)
        elif y <= 67:
            # Main cylindrical shaft (*fusto*), thicker around fulcrum wear collar (y=26..33)
            if 26 <= y <= 33:
                col = C_WALNUT
                xs, zs = (5, 6), (5, 6)
            else:
                col = C_ASH
                xs, zs = (5, 6), (5, 6) if y <= 45 else (5,)
            for x in xs:
                for z in zs:
                    put(vox, x, y, z, col, SIZE_OAR)
        else:
            # Tapered Venetian oar blade *pala* (y=68..85)
            # Flat face vertical or horizontal? Around X (vertical paddle face in X-Y plane, rotated when dipping)
            # In canonical +Y space, make blade wider along X (x=4..7 = 4 vx = 0.20 m) and thin in Z (1-2 vx)
            xs = (4, 5, 6, 7) if 73 <= y <= 83 else (5, 6)
            zs = (5, 6) if y <= 74 else (5,)
            col = C_OAK if y >= 83 else C_ASH
            for x in xs:
                for z in zs:
                    put(vox, x, y, z, col, SIZE_OAR)
    return vox


def check_connectivity(vox: dict, name: str):
    if not vox:
        raise RuntimeError(f"{name}: EMPTY")
    pts = set(vox.keys())
    seen = set()
    comps = []
    for p in pts:
        if p in seen:
            continue
        q = deque([p])
        seen.add(p)
        cnt = 0
        while q:
            cx, cy, cz = q.popleft()
            cnt += 1
            for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                np = (cx+dx, cy+dy, cz+dz)
                if np in pts and np not in seen:
                    seen.add(np)
                    q.append(np)
        comps.append(cnt)
    comps.sort(reverse=True)

    # Check enclosed cavities inside bounding box padded by 1
    xs, ys, zs = [k[0] for k in pts], [k[1] for k in pts], [k[2] for k in pts]
    x0, x1 = min(xs)-1, max(xs)+1
    y0, y1 = min(ys)-1, max(ys)+1
    z0, z1 = min(zs)-1, max(zs)+1
    air = set()
    q = deque([(x0, y0, z0)])
    air.add((x0, y0, z0))
    while q:
        cx, cy, cz = q.popleft()
        for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            nx, ny, nz = cx+dx, cy+dy, cz+dz
            if x0 <= nx <= x1 and y0 <= ny <= y1 and z0 <= nz <= z1:
                np = (nx, ny, nz)
                if np not in pts and np not in air:
                    air.add(np)
                    q.append(np)
    cavities = 0
    for xx in range(x0, x1+1):
        for yy in range(y0, y1+1):
            for zz in range(z0, z1+1):
                if (xx, yy, zz) not in pts and (xx, yy, zz) not in air:
                    cavities += 1
    print(f"[{name}] voxels={len(pts)}, components={len(comps)} ({comps}), enclosed_air_cells={cavities}")
    return comps, cavities


def write_vox_list(vox: dict, path: str, header: str):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {header}\n")
        for (x, y, z) in sorted(vox.keys()):
            f.write(f"{x},{y},{z},{vox[(x,y,z)]}\n")


def rgb332_to_rgb(c: int):
    return (((c >> 5) & 7) * 255 // 7, ((c >> 2) & 7) * 255 // 7, (c & 3) * 255 // 3)


def draw_blueprint(hull: dict, ferro: dict, oar: dict, out_path: str):
    W, H = 1800, 1220
    img = Image.new("RGB", (W, H), (246, 241, 229))
    d = ImageDraw.Draw(img)
    combined = dict(hull)
    combined.update(ferro)

    # Header band
    d.rectangle([0, 0, W, 70], fill=(32, 38, 46))
    d.text((30, 18), "VENICE GONDOLA (c. 1666) OPEN-CABIN PASSENGER CRAFT — BLUEPRINT 0.05 m/voxel (TASK-1298)", fill=(245, 236, 210))
    d.text((30, 42), "LOA 10.50 m | LWL ~8.25 m | B 1.40 m | Draft 0.20 m | Bow Ferro +1.05 m WL | Stern Ferro +0.85 m WL | 4.20 m Remo Oar", fill=(180, 200, 215))

    # Helper to plot ortho projections cleanly
    def plot_ortho(vox_map, ox, oy, px_per_vx, axes_fn, title, wl_z=None, extra_fn=None):
        d.text((ox, oy - 24), title, fill=(32, 38, 46))
        items = []
        for (x, y, z), c in vox_map.items():
            u, v, depth = axes_fn(x, y, z)
            items.append((depth, u, v, c))
        items.sort()
        for _, u, v, c in items:
            rgb = rgb332_to_rgb(c)
            rx = ox + u * px_per_vx
            ry = oy + v * px_per_vx
            d.rectangle([rx, ry, rx + px_per_vx - 1, ry + px_per_vx - 1], fill=rgb)
        if wl_z is not None:
            wy = oy + wl_z * px_per_vx
            d.line([(ox - 10, wy), (ox + 225 * px_per_vx, wy)], fill=(35, 115, 175), width=2)
            d.text((ox + 205 * px_per_vx, wy - 16), "WL z=4 (0.20m)", fill=(35, 115, 175))
        if extra_fn:
            extra_fn(d, ox, oy, px_per_vx)

    # 1. Profile View (+X right = Bow, +Z up)
    plot_ortho(
        combined, 50, 140, 7,
        lambda x, y, z: (x, 30 - z, y),
        "1. PROFILE (Starboard Elevation, +X Bow Right, Grid = 0.05m)",
        wl_z=30 - 4,
        extra_fn=lambda dr, ox, oy, s: (
            dr.text((ox + 205*s - 60, oy + (30-24)*s - 18), "Bow Ferro +1.05m WL", fill=(140,40,30)),
            dr.text((ox + 6*s, oy + (30-20)*s - 18), "Stern Ferro +0.85m", fill=(140,40,30)),
            dr.text((ox + 78*s, oy + (30-16)*s - 18), "Trasto +0.65m", fill=(70,50,30)),
            dr.ellipse([ox + 48.5*s - 5, oy + (30-16.5)*s - 5, ox + 48.5*s + 5, oy + (30-16.5)*s + 5], outline=(210,45,30), width=2),
            dr.text((ox + 42*s, oy + (30-16.5)*s - 22), "Forcola Pivot (48.5, 43.5, 16.5)", fill=(180,35,20)),
        )
    )

    # 2. Plan View (+X right = Bow, +Y down/starboard)
    plot_ortho(
        combined, 50, 440, 7,
        lambda x, y, z: (x, y - 10, z),
        "2. PLAN VIEW (+X Bow Right, +Y Starboard Down; Midships B = 1.40 m, Parecio Open Cabin)",
        extra_fn=lambda dr, ox, oy, s: (
            dr.line([(ox + 12*s, oy + (34.5-10)*s), (ox + 205*s, oy + (34.5-10)*s)], fill=(170,70,70), width=1),
            dr.line([
                (ox + (48.5 + 27*0.809*0.848)*s, oy + (43.5 - 10 - 27*0.809*0.530)*s),
                (ox + (48.5 - 57*0.809*0.848)*s, oy + (43.5 - 10 + 57*0.809*0.530)*s),
            ], fill=(200, 120, 20), width=4),
            dr.text((ox + 18*s, oy + 58*s), "Oar Reach: +1.67 m from CL (Active Swept Beam ~2.37 m)", fill=(165, 85, 10)),
        )
    )

    # 3. Midships Section (x = 84..116 slice looking forward)
    mid_slice = {k: v for k, v in hull.items() if 84 <= k[0] <= 116}
    plot_ortho(
        mid_slice, 50, 920, 10,
        lambda x, y, z: (y - 18, 22 - z, x),
        "3. MIDSHIPS OPEN-CABIN SECTION (Trasto + Banchette, WL at z=4)",
        wl_z=22 - 4,
    )

    # 4. Zoomed Bow Ferro Detail (1624 Proclama)
    bow_ferro = {k: v for k, v in combined.items() if 195 <= k[0] <= 216}
    plot_ortho(
        bow_ferro, 560, 900, 16,
        lambda x, y, z: (x - 195, 26 - z, y),
        "4. BOW FERRO DETAIL (x=195..216, 2-vx=10cm Brocche)",
        wl_z=None,
    )

    # 5. Canonical Standing Oar (4.20 m)
    plot_ortho(
        oar, 1040, 920, 8,
        lambda x, y, z: (y, x, z),
        "5. CANONICAL 4.20 m REMO OAR (1.35 m Inboard | Pivot y=29 | 2.85 m Outboard)",
        extra_fn=lambda dr, ox, oy, s: (
            dr.line([(ox + 29*s, oy - 8), (ox + 29*s, oy + 14*s)], fill=(200, 40, 40), width=2),
            dr.text((ox + 29*s - 20, oy + 16*s), "Pivot (5.5, 29.0, 5.5)", fill=(200, 40, 40)),
        )
    )

    img.save(out_path)
    print(f"[Blueprint] saved {out_path} ({W}x{H})")


def main():
    hull = build_hull()
    ferro = build_ferro(hull)
    oar = build_oar()

    # Check overlap
    overlap = set(hull.keys()) & set(ferro.keys())
    if overlap:
        raise RuntimeError(f"Hull/Ferro overlap: {len(overlap)} voxels")

    check_connectivity(hull, "hull")
    check_connectivity(ferro, "ferro_alone")
    combined = dict(hull)
    combined.update(ferro)
    comp_all, cav_all = check_connectivity(combined, "hull+ferro_combined")
    comp_oar, cav_oar = check_connectivity(oar, "oar")

    if len(comp_all) != 1 or cav_all != 0 or len(comp_oar) != 1 or cav_oar != 0:
        raise RuntimeError("Topology check failed!")

    write_vox_list(hull, os.path.join(DESIGN_DIR, "voxels_hull.txt"), "1666 Venice Gondola Hull (0.05 m/voxel)")
    write_vox_list(ferro, os.path.join(DESIGN_DIR, "voxels_ferro.txt"), "1666 Venice Gondola Bow+Stern Ferro (0.05 m/voxel, material=iron)")
    write_vox_list(oar, os.path.join(DESIGN_DIR, "voxels_oar.txt"), "1666 Venice Gondola Standing Remo Oar (4.20 m, 0.05 m/voxel)")

    draw_blueprint(hull, ferro, oar, os.path.join(SHEETS_DIR, "sheet01_gondola_1666.png"))

    # Exact metrics
    xs_all = [k[0] for k in combined]
    ys_all = [k[1] for k in combined]
    zs_all = [k[2] for k in combined]
    wl_xs = [x for (x, y, z) in hull if z == 4]
    bow_ferro_z = max(z for (x, y, z) in ferro if x > 100)
    stern_ferro_z = max(z for (x, y, z) in ferro if x < 100)

    metrics = {
        "scale_m": SCALE_M,
        "hull_voxels": len(hull),
        "ferro_voxels": len(ferro),
        "combined_voxels": len(combined),
        "oar_voxels": len(oar),
        "loa_voxels": max(xs_all) - min(xs_all) + 1,
        "loa_m": round((max(xs_all) - min(xs_all) + 1) * SCALE_M, 3),
        "lwl_m": round((max(wl_xs) - min(wl_xs) + 1) * SCALE_M, 3),
        "beam_voxels": max(ys_all) - min(ys_all) + 1,
        "beam_m": round((max(ys_all) - min(ys_all) + 1) * SCALE_M, 3),
        "draft_m": 4 * SCALE_M,
        "bow_ferro_peak_z_idx": bow_ferro_z,
        "bow_ferro_height_above_keel_m": round((bow_ferro_z + 1) * SCALE_M, 3),
        "bow_ferro_above_wl_m": round((bow_ferro_z + 1 - 4) * SCALE_M, 3),
        "stern_ferro_peak_z_idx": stern_ferro_z,
        "stern_ferro_height_above_keel_m": round((stern_ferro_z + 1) * SCALE_M, 3),
        "stern_ferro_above_wl_m": round((stern_ferro_z + 1 - 4) * SCALE_M, 3),
        "forcola_pivot": [48.5, 43.5, 16.5],
        "poppa_deck_surface_m_above_wl": round((11 - 4) * SCALE_M, 3),
        "combined_components": len(comp_all),
        "combined_cavities": cav_all,
    }
    with open(os.path.join(DESIGN_DIR, "metrics_step2.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
