#!/usr/bin/env python3
"""
Step 3: Deterministic 0.10 m/voxel In-Town Show Gondola Generator & Kinematics Measurer.
Produces:
  - design/voxels_show.txt                   (for apex-one-venice-gondola-show-1666, 112x48x32 @ 0.10 m/vx)
  - design/metrics_step3.json                (waterline, air draft, oar sweep, height/width envelopes)
  - design/sheets/sheet02_show_measurements.png (orthographic + oar-sweep kinematics + bridge-clearance diagram)
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

SCALE_M = 0.10
SIZE_SHOW = (112, 48, 32)
Y_MIN_C = 24
Y_MAX_C = 23  # symmetric centerline at y_cl = 23.5 (24 - hw .. 23 + hw)

# Verified RGB332 palette indices (consistent with build_gondola.py + Venetian attire accents)
C_PITCH_DARK = 36    # (36, 36, 0)    sumptuary pitched black planks
C_PITCH_ALT  = 72    # (72, 72, 0)    tarred oak seam highlight
C_PITCH_RIB  = 73    # (72, 72, 85)   charcoal inner ribs
C_WALNUT     = 104   # (109, 72, 0)   carved walnut gunwale / forcola
C_OAK        = 177   # (182, 145, 85) oiled oak paioli / poppa deck
C_CUSHION    = 36    # (36, 36, 0)    pitched black leather cushion
C_CUSH_TRIM  = 100   # (109, 36, 0)   oxblood leather trim & Venetian waistcoat
C_BRASS      = 176   # (182, 145, 0)  brass mooring cleat
C_IRON_DARK  = 109   # (109, 109, 85) wrought iron collar
C_IRON_BODY  = 146   # (145, 145, 170) forged iron ferro neck & prongs
C_IRON_EDGE  = 182   # (182, 182, 170) burnished iron halberd crest
C_SKIN       = 209   # (218, 145, 85) warm sunlit skin tone
C_LINEN      = 218   # (218, 218, 170) ivory linen collar / shirt sleeves
C_GOLD_SASH  = 212   # (218, 182, 0)  ochre-gold sash / ribbon
C_DARK_CAPE  = 37    # (36, 36, 85)   midnight Venetian cape/breeches


def put(vox: dict, x: int, y: int, z: int, c: int, size=SIZE_SHOW):
    if 0 <= x < size[0] and 0 <= y < size[1] and 0 <= z < size[2]:
        vox[(x, y, z)] = c


def paint_pair_y(vox: dict, x: int, hw: int, z: int, c: int):
    put(vox, x, Y_MIN_C - hw, z, c)
    put(vox, x, Y_MAX_C + hw, z, c)


def z_keel_10(x: int) -> int:
    """Bottom keel z in 0.10 m units over x=7..102 (9.60 m hull). WL is z_wl=2 (0.20 m)."""
    if 24 <= x <= 86:
        return 0
    if x > 86:
        u = min(1.0, (x - 86) / 16.0)
        return int(round(8.0 * (u ** 2.35)))
    u = min(1.0, (24 - x) / 17.0)
    return int(round(7.0 * (u ** 2.35)))


def z_sheer_10(x: int) -> int:
    """Gunwale top voxel z in 0.10 m units. Midships z=4 (top 0.50 m = +0.30 m freeboard)."""
    dx = abs(x - 54.5)
    if x >= 54.5:
        u = min(1.0, dx / 47.5)
        return 4 + int(round(6.0 * (u ** 2.2)))
    u = min(1.0, dx / 47.5)
    return 4 + int(round(4.0 * (u ** 2.1)))


def beam_frac_10(x: int) -> float:
    dx = abs(x - 54.5)
    t = min(1.0, dx / 47.5)
    return max(0.0, math.cos(t * math.pi * 0.5)) ** 0.72


def hw_bot_10(x: int) -> int:
    return max(1, int(round(5.0 * beam_frac_10(x))))


def hw_top_10(x: int) -> int:
    # Midships beam 14 voxels (2 * 7 = 14 vx = 1.40 m exact: y=17..30)
    return max(1, int(round(7.0 * beam_frac_10(x))))


def build_show_gondola() -> dict:
    vox = {}
    prev_zk = prev_ht = None
    for x in range(7, 103):
        zk = z_keel_10(x)
        zs = z_sheer_10(x)
        hb = hw_bot_10(x)
        ht = hw_top_10(x)

        # Flat fondo bottom
        for y in range(Y_MIN_C - hb, Y_MAX_C + hb + 1):
            put(vox, x, y, zk, C_PITCH_DARK if (x + y) % 4 != 0 else C_PITCH_ALT)

        # Stitch rising keel steps so zero X-Z gaps
        if prev_zk is not None and zk != prev_zk:
            for zz in range(min(zk, prev_zk), max(zk, prev_zk) + 1):
                for y in range(Y_MIN_C - min(hb, ht), Y_MAX_C + min(hb, ht) + 1):
                    put(vox, x, y, zz, C_PITCH_DARK)

        # Solid extreme stems
        if ht <= 1 or x <= 11 or x >= 98:
            for zz in range(zk, zs + 1):
                for y in range(Y_MIN_C - 1, Y_MAX_C + 2):
                    col = C_WALNUT if zz == zs else C_PITCH_DARK
                    put(vox, x, y, zz, col)
        else:
            # Flared sides sponde (step orthogonally in hw/z to guarantee 6-connectivity)
            n_steps = max(24, (zs - zk) * 4 + abs(ht - hb) * 4)
            last_hw, last_z = hb, zk
            for s in range(n_steps + 1):
                f = s / float(n_steps)
                hw_f = int(round(hb + (ht - hb) * (f ** 0.78)))
                zz = int(round(zk + (zs - zk) * f))
                if hw_f != last_hw and zz != last_z:
                    paint_pair_y(vox, x, hw_f, last_z, C_PITCH_DARK)
                col = C_WALNUT if zz == zs else (C_PITCH_ALT if zz == zs - 1 else C_PITCH_DARK)
                paint_pair_y(vox, x, hw_f, zz, col)
                last_hw, last_z = hw_f, zz

            if prev_ht is not None and prev_ht != ht:
                for hh in range(min(ht, prev_ht), max(ht, prev_ht) + 1):
                    paint_pair_y(vox, x, hh, zs, C_WALNUT)

        prev_zk, prev_ht = zk, ht

    # Bilge floor bedding (z=1) & DRY paioli floorboards at z=2 (top 0.30 m = +0.10 m WL)
    # Keep z=1 solid under paioli so zero trapped air pockets between ribs!
    for x in range(35, 69):
        hb = hw_bot_10(x)
        for y in range(Y_MIN_C - hb, Y_MAX_C + hb + 1):
            put(vox, x, y, 1, C_PITCH_RIB if x % 4 == 0 else C_PITCH_DARK)
            put(vox, x, y, 2, C_OAK if y % 2 == 0 else C_WALNUT)
        paint_pair_y(vox, x, hb + 1, 2, C_PITCH_DARK)

    # Solid watertight forepeak hull below foredeck (x=69..98, zk..zd) -> zero enclosed cavities
    for x in range(69, 99):
        zk = z_keel_10(x)
        zs = z_sheer_10(x)
        ht = hw_top_10(x)
        zd = zs - 1
        for zz in range(zk + 1, zd + 1):
            frac = 0.0 if zd <= zk else (zz - zk) / float(max(1, zd - zk))
            hw_z = max(1, int(round(hw_bot_10(x) + (ht - hw_bot_10(x)) * (frac ** 0.78))))
            for y in range(Y_MIN_C - hw_z + 1, Y_MAX_C + hw_z):
                if zz == zd:
                    col = C_WALNUT if (x == 69 or y in (23, 24)) else C_PITCH_DARK
                else:
                    col = C_PITCH_DARK
                put(vox, x, y, zz, col)
        for y in range(Y_MIN_C - ht + 1, Y_MAX_C + ht):
            col = C_WALNUT if (x == 69 or y in (23, 24)) else C_PITCH_DARK
            if 73 <= x <= 93 and abs(y - 23.5) <= max(0.6, ht * 0.4):
                put(vox, x, y, zd + 1, col)
        if x == 69:
            for y in range(Y_MIN_C - ht + 1, Y_MAX_C + ht):
                put(vox, x, y, zd + 1, C_WALNUT)
    put(vox, 96, 23, z_sheer_10(96), C_BRASS)
    put(vox, 96, 24, z_sheer_10(96), C_BRASS)

    # Stern poppa standing deck & watertight aftpeak hull (x=12..34, zk..5 => top +0.40 m WL)
    for x in range(12, 35):
        zk = z_keel_10(x)
        ht = hw_top_10(x)
        top_z = 5 if x >= 15 else max(5, z_sheer_10(x) - 1)
        for zz in range(zk + 1, top_z + 1):
            frac = 0.0 if top_z <= zk else (zz - zk) / float(max(1, top_z - zk))
            hw_z = max(1, int(round(hw_bot_10(x) + (ht - hw_bot_10(x)) * (frac ** 0.78))))
            for y in range(Y_MIN_C - hw_z + 1, Y_MAX_C + hw_z):
                if zz == 5 and x >= 15:
                    col = C_OAK if x % 2 == 0 else C_WALNUT
                elif zz == top_z and x < 15:
                    col = C_PITCH_ALT
                else:
                    col = C_PITCH_DARK
                put(vox, x, y, zz, col)
    # Cockpit-to-poppa bulkhead step at x=34 (connects z=2 paioli up to z=5 poppa)
    for y in range(19, 29):
        for zz in range(2, 5):
            put(vox, 34, y, zz, C_WALNUT if zz == 4 else C_PITCH_DARK)

    # Open-cabin parecio seats: trasto sofa (x=39..45, backrest z=5..8) + side banchette (x=46..63)
    for x in range(39, 46):
        ht_s = hw_top_10(x)
        hb_s = hw_bot_10(x)
        for y in range(Y_MIN_C - hb_s, Y_MAX_C + hb_s + 1):
            put(vox, x, y, 3, C_WALNUT)
            put(vox, x, y, 4, C_CUSH_TRIM if x == 45 else C_CUSHION)
    for x in (38, 39):
        hb_b = hw_bot_10(x)
        for y in range(Y_MIN_C - hb_b, Y_MAX_C + hb_b + 1):
            top_z = 8 if 20 <= y <= 27 else 7
            for zz in range(5, top_z + 1):
                if x == 39 and zz >= 7:
                    continue
                put(vox, x, y, zz, C_WALNUT if zz == top_z else (C_CUSH_TRIM if zz == top_z - 1 else C_CUSHION))
    for x in range(46, 64):
        ht_l = hw_top_10(x)
        hb_l = hw_bot_10(x)
        yp0 = max(Y_MIN_C - ht_l + 1, Y_MIN_C - hb_l)
        ys0 = min(Y_MAX_C + ht_l - 1, Y_MAX_C + hb_l)
        for d in range(2):
            put(vox, x, yp0 + d, 3, C_WALNUT)
            put(vox, x, ys0 - d, 3, C_WALNUT)
            put(vox, x, yp0 + d, 4, C_CUSH_TRIM if d == 1 else C_CUSHION)
            put(vox, x, ys0 - d, 4, C_CUSH_TRIM if d == 1 else C_CUSHION)

    # Starboard Forcola oarlock post (x=24..25, y=28..29, z=5..9; pivot notch around (25.0, 28.0, 8.5))
    for zz in range(4, 9):
        put(vox, 24, 29, zz, C_WALNUT)
        put(vox, 25, 29, zz, C_WALNUT)
    put(vox, 26, 28, 6, C_WALNUT)
    put(vox, 26, 28, 7, C_OAK)
    put(vox, 26, 28, 8, C_OAK)
    put(vox, 26, 28, 9, C_WALNUT)  # forward *corno* horn
    put(vox, 23, 28, 6, C_WALNUT)
    put(vox, 23, 28, 7, C_OAK)     # aft heel *morso*

    # Double-ended wrought iron *ferri* (bow x=101..108 z=7..11 -> top 1.20m = +1.00m WL; stern x=4..7 z=6..9 -> top 1.00m = +0.80m WL)
    bow_iron = [
        (102, 10, C_IRON_DARK), (103, 7, C_IRON_DARK), (103, 8, C_IRON_BODY), (103, 9, C_IRON_BODY),
        (103, 10, C_IRON_BODY), (104, 8, C_IRON_BODY), (104, 9, C_IRON_BODY), (104, 10, C_IRON_BODY),
        (104, 11, C_IRON_EDGE), (105, 9, C_IRON_BODY), (105, 10, C_IRON_EDGE), (105, 11, C_IRON_EDGE),
        (106, 10, C_IRON_EDGE), (106, 11, C_IRON_EDGE), (107, 10, C_IRON_EDGE), (108, 10, C_IRON_EDGE),
        # Blunted prongs
        (105, 8, C_IRON_BODY), (106, 9, C_IRON_BODY),
    ]
    for x, z, col in bow_iron:
        put(vox, x, 23, z, col)
        put(vox, x, 24, z, col)

    stern_iron = [
        (7, 8, C_IRON_DARK), (6, 6, C_IRON_DARK), (6, 7, C_IRON_BODY), (6, 8, C_IRON_BODY),
        (5, 7, C_IRON_BODY), (5, 8, C_IRON_EDGE), (5, 9, C_IRON_EDGE),
        (4, 8, C_IRON_EDGE), (4, 9, C_IRON_EDGE),
    ]
    for x, z, col in stern_iron:
        put(vox, x, 23, z, col)
        put(vox, x, 24, z, col)

    # Standing *gondoliere* on aft *poppa* deck (z=5 top -> feet at z=6, hat crown z=22 => top 2.30 m above keel = +2.10 m above WL!)
    # Strictly 6-connected boots, legs, torso, arms reaching forward/starboard toward *forcola* oar loom!
    for zz in range(6, 11):
        put(vox, 22, 23, zz, C_PITCH_DARK if zz < 10 else C_DARK_CAPE)  # aft brace leg grounded on poppa z=5
        put(vox, 24, 24, zz, C_PITCH_DARK if zz < 10 else C_DARK_CAPE)  # forward leg grounded on poppa z=5
    # Hip block connecting both legs (z=11)
    for x in (22, 23, 24):
        for y in (23, 24):
            put(vox, x, y, 11, C_DARK_CAPE)
    # Waist sash & Venetian doublet torso (z=12..17), slight forward lunge (x=24..25) with overlap at z=15
    for zz in range(12, 18):
        col = C_GOLD_SASH if zz == 12 else (C_LINEN if zz == 17 else C_CUSH_TRIM)
        xs_t = (24,) if zz < 15 else ((24, 25) if zz == 15 else (25,))
        for xx in xs_t:
            for y in (23, 24):
                put(vox, xx, y, zz, col)
    # Orthogonal face-connected left & right arms reaching forward/starboard toward the oar loom!
    for p_arm in [(26, 23, 16), (27, 23, 16), (27, 23, 15)]:
        put(vox, *p_arm, C_SKIN if p_arm[0] == 27 and p_arm[2] == 15 else C_LINEN)
    for p_arm in [(25, 25, 16), (26, 25, 16), (27, 25, 16), (27, 26, 16), (27, 26, 15), (28, 26, 15), (28, 26, 14)]:
        put(vox, *p_arm, C_SKIN if p_arm[0] >= 27 and p_arm[1] == 26 else C_LINEN)
    # Neck & head (z=18..20) + brimmed Venetian boatman hat (z=21 brim, z=22 crown => 2.30m above keel = +2.10m above WL!)
    for zz in (18, 19, 20):
        put(vox, 25, 23, zz, C_SKIN)
        put(vox, 25, 24, zz, C_SKIN)
    for x in (24, 25, 26):
        for y in (22, 23, 24, 25):
            put(vox, x, y, 21, C_PITCH_DARK if (x != 24 or y != 25) else C_GOLD_SASH)
    for y in (23, 24):
        put(vox, 25, y, 22, C_PITCH_DARK)

    # 2 Seated Passengers in the open *parecio* cockpit (max z=12 => +1.10 m above WL, leaving gondoliere clear astern line-of-sight)
    # Passenger 1: Seated on main *trasto* sofa (port side, facing forward, wearing dark cape + ivory linen ruff)
    for x in (41, 42, 43):
        for y in (20, 21):
            put(vox, x, y, 5, C_DARK_CAPE)
    put(vox, 43, 20, 4, C_PITCH_DARK)  # shins onto floorboards
    put(vox, 43, 20, 3, C_PITCH_DARK)
    for zz in range(6, 10):
        for y in (20, 21):
            put(vox, 41, y, zz, C_LINEN if zz == 9 else C_DARK_CAPE)
    for zz in (10, 11):
        put(vox, 41, 20, zz, C_SKIN)
        put(vox, 41, 21, zz, C_SKIN)
    put(vox, 41, 20, 12, C_PITCH_DARK)
    put(vox, 41, 21, 12, C_PITCH_DARK)

    # Passenger 2: Seated on starboard longitudinal *banchetta* (facing inward/port toward cabin center)
    for y in (25, 26):
        put(vox, 52, y, 5, C_CUSH_TRIM)
        put(vox, 53, y, 5, C_CUSH_TRIM)
    put(vox, 52, 25, 4, C_PITCH_DARK)
    put(vox, 52, 25, 3, C_PITCH_DARK)
    for zz in range(6, 10):
        put(vox, 52, 26, zz, C_LINEN if zz == 9 else C_DARK_CAPE)
        put(vox, 53, 26, zz, C_LINEN if zz == 9 else C_DARK_CAPE)
    for zz in (10, 11):
        put(vox, 52, 26, zz, C_SKIN)
        put(vox, 53, 26, zz, C_SKIN)
    put(vox, 52, 26, 12, C_PITCH_ALT)
    put(vox, 53, 26, 12, C_PITCH_ALT)

    return vox


def check_connectivity(vox: dict, name: str):
    pts = set(vox.keys())
    seen = set()
    comps = []
    for p in pts:
        if p in seen:
            continue
        q = deque([p])
        seen.add(p)
        c_pts = []
        while q:
            cx, cy, cz = q.popleft()
            c_pts.append((cx, cy, cz))
            for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                np = (cx+dx, cy+dy, cz+dz)
                if np in pts and np not in seen:
                    seen.add(np)
                    q.append(np)
        comps.append((len(c_pts), c_pts[0]))
    comps.sort(reverse=True)

    xs, ys, zs = [k[0] for k in pts], [k[1] for k in pts], [k[2] for k in pts]
    x0, x1 = min(xs)-1, max(xs)+1
    y0, y1 = min(ys)-1, max(ys)+1
    z0, z1 = min(zs)-1, max(zs)+1
    ext = {(x0, y0, z0)}
    q = deque([(x0, y0, z0)])
    while q:
        cx, cy, cz = q.popleft()
        for dx, dy, dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            nx, ny, nz = cx+dx, cy+dy, cz+dz
            if x0 <= nx <= x1 and y0 <= ny <= y1 and z0 <= nz <= z1:
                np = (nx, ny, nz)
                if np not in pts and np not in ext:
                    ext.add(np)
                    q.append(np)
    total_air = (x1 - x0 + 1) * (y1 - y0 + 1) * (z1 - z0 + 1) - len(pts)
    cavities = total_air - len(ext)
    return len(comps), [c[0] for c in comps], [c[1] for c in comps], cavities


def rot_x(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0], v[1]*c - v[2]*s, v[1]*s + v[2]*c)


def rot_y(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0]*c + v[2]*s, v[1], -v[0]*s + v[2]*c)


def rot_z(v, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (v[0]*c - v[1]*s, v[0]*s + v[1]*c, v[2])


def oar_kinematics():
    """
    Exact kinematics of the 4.20 m standing remo attached at the starboard *forcola*:
    - Canonical oar: grip s=-1.35 m, pivot s=0, blade s=+2.80 m (4.15-4.20 m), blade width +/-0.10 m in local X.
    - Base resting orientation (Step 2 rotate=-36,0,58 deg): Rx(-36) -> Ry(0) -> Rz(+58).
    - Blockside oarAnim (31_drive.js lines 370-371) for starboard side p.sg=+1:
      swM = Rz(th) * Rx(al), where th = -stroke_deg * cos(t), al = dip_deg * max(0, -sin(t)).
    """
    # Centerline-relative pivot in meters on 0.05 m / 0.10 m vessels:
    # 0.05 m: x=48.5 vs mid 107.5 (-2.95 m astern of midship), y=43.5 vs 34.5 (+0.45 m stbd), z=16.5*0.05 = 0.825 m (above keel; +0.625 m WL)
    # 0.10 m show: at=(25.0, 28.0, 8.5) => y=(28.0-23.5)*0.10=+0.45 m stbd, z=0.85 m above keel (+0.65 m WL)
    piv_y = 0.45
    piv_z_wl = 0.65  # height of forcola pivot above WL (0.20 m)
    s_grip = -1.35
    s_tip = +2.80
    stroke_deg = 28.0
    dip_deg = 10.0

    def eval_pose(t_rad, blade_edge=0.10):
        th = -stroke_deg * math.cos(t_rad)
        al = dip_deg * max(0.0, -math.sin(t_rad))
        pts = {}
        for name, s, lx in [("grip", s_grip, 0.0), ("tip_c", s_tip, 0.0), ("tip_p", s_tip, -blade_edge), ("tip_s", s_tip, +blade_edge)]:
            v = (lx, s, 0.0)
            v = rot_z(rot_y(rot_x(v, -36.0), 0.0), 58.0)
            v = rot_z(rot_x(v, al), th)
            pts[name] = (v[0], piv_y + v[1], piv_z_wl + v[2])
        return pts

    # Neutral resting pose (mid-drive: cos=0, -sin <= 0 => th=0, al=0)
    neutral = eval_pose(math.pi * 0.5)
    sweep_samples = []
    max_y_stbd = -99.0
    min_y_feathered = 99.0
    min_z_wl = 99.0
    max_grip_z_wl = -99.0
    for k in range(360):
        tr = 2.0 * math.pi * k / 360.0
        p = eval_pose(tr)
        sweep_samples.append((p["tip_c"][0], p["tip_c"][1], p["tip_c"][2]))
        max_y_stbd = max(max_y_stbd, p["tip_c"][1], p["tip_p"][1], p["tip_s"][1])
        min_y_feathered = min(min_y_feathered, p["tip_c"][1])
        min_z_wl = min(min_z_wl, p["tip_c"][2], p["tip_p"][2], p["tip_s"][2])
        max_grip_z_wl = max(max_grip_z_wl, p["grip"][2])

    return {
        "forcola_y_from_cl_m": piv_y,
        "forcola_z_above_wl_m": piv_z_wl,
        "neutral_stbd_reach_m": round(neutral["tip_s"][1], 3),
        "neutral_swept_beam_m": round(0.70 + max(neutral["tip_c"][1], neutral["tip_s"][1]), 3),
        "neutral_blade_depth_below_wl_m": round(-neutral["tip_c"][2], 3),
        "neutral_grip_above_wl_m": round(neutral["grip"][2], 3),
        "dynamic_max_stbd_reach_m": round(max_y_stbd, 3),
        "dynamic_peak_swept_beam_m": round(0.70 + max_y_stbd, 3),
        "aft_stroke_min_stbd_m": round(min_y_feathered, 3),
        "feathered_pass_beam_m": round(0.70 + max(0.70, min_y_feathered + 0.10), 3),
        "min_blade_z_below_wl_m": round(-min_z_wl, 3),
        "max_grip_z_above_wl_m": round(max_grip_z_wl, 3),
        "sweep_arc_points": sweep_samples,
    }


def make_sheet(vox: dict, kin: dict):
    W, H = 1800, 1220
    img = Image.new("RGB", (W, H), (247, 243, 232))
    d = ImageDraw.Draw(img)
    try:
        f_title = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 25)
        f_h = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 17)
        f_t = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 14)
        f_m = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
    except Exception:
        f_title = f_h = f_t = f_m = ImageFont.load_default()

    # Palette RGB table
    def rgb(idx):
        return (((idx >> 5) & 7) * 255 // 7, ((idx >> 2) & 7) * 255 // 7, (idx & 3) * 85)

    d.rectangle([16, 16, W - 16, H - 16], outline=(55, 65, 78), width=3)
    d.text((34, 28), "Blocksail 1666 Venice Gondola (Show 0.10 m/vx) — Waterline, Oar Sweep & Standing Clearance", fill=(25, 30, 38), font=f_title)
    d.text((34, 62), "Work: apex-one-venice-gondola-show-1666 (112x48x32 @ 0.10 m/vx) | LOA 10.50 m | B 1.40 m | Draft 0.20 m | Standing peak +2.10 m WL", fill=(75, 82, 92), font=f_t)

    # Panel A (Top-left): Starboard Profile showing Waterline + Standing Gondoliere (+2.10m WL) + Passengers + Bridge Envelopes
    px0, py0, px1, py1 = 34, 96, 1140, 560
    d.rectangle([px0, py0, px1, py1], fill=(253, 251, 245), outline=(140, 140, 130), width=2)
    d.text((px0 + 12, py0 + 8), "A. Profile (Starboard Elevation @ 0.10 m/vx) — Waterline z_wl = 0.20 m, Standing Hat Crown = +2.10 m WL", fill=(30, 35, 45), font=f_h)

    sc_p = 9.0  # px per 0.10m voxel
    ox_p = px0 + 48
    oz_p = py1 - 95  # keel baseline y-coord (z=0 bottom)

    # Water surface fill below z_wl=2 (0.20 m)
    y_wl = oz_p - 2 * sc_p
    d.rectangle([px0 + 4, y_wl, px1 - 4, py1 - 4], fill=(214, 234, 248))
    d.line([px0 + 4, y_wl, px1 - 4, y_wl], fill=(20, 95, 165), width=3)
    d.text((px0 + 12, y_wl + 6), "WL z = 0.20 m (z_wl=2 @ 0.10 m)", fill=(15, 78, 140), font=f_m)

    # Height reference lines above WL
    for h_wl, lbl, col in [
        (0.30, "+0.30 m Freeboard", (120, 125, 135)),
        (1.05, "+1.05 m Ferro di Prua Peak", (110, 90, 55)),
        (1.75, "+1.75 m Crouched Clearance", (180, 105, 25)),
        (2.10, "+2.10 m Standing Gondoliere Peak", (175, 35, 35)),
    ]:
        yy = y_wl - h_wl * 10.0 * sc_p
        d.line([px0 + 40, yy, px1 - 12, yy], fill=col, width=2 if h_wl >= 1.75 else 1)
        d.text((px1 - 290, yy - 16), lbl, fill=col, font=f_m)

    # Render voxel silhouette sorted back-to-front by Y
    for x, y, z in sorted(vox.keys(), key=lambda p: p[1]):
        c = vox[(x, y, z)]
        rx0 = ox_p + x * sc_p
        ry0 = oz_p - (z + 1) * sc_p
        d.rectangle([rx0, ry0, rx0 + sc_p, ry0 + sc_p], fill=rgb(c))

    # Draw submerged/neutral oar projection on profile from forcola (x=25, z=8.5)
    piv_px = ox_p + 25.0 * sc_p
    piv_py = oz_p - 8.5 * sc_p
    # Neutral oar tip x = 25 + (-2.758*0.809 ? wait: evaluate direct m -> 0.10m vx)
    v_tip = rot_z(rot_x((0.0, 2.80, 0.0), -36.0), 58.0)
    v_grp = rot_z(rot_x((0.0, -1.35, 0.0), -36.0), 58.0)
    d.line([piv_px + v_grp[0]*10*sc_p, piv_py - v_grp[2]*10*sc_p,
            piv_px + v_tip[0]*10*sc_p, piv_py - v_tip[2]*10*sc_p], fill=(175, 105, 28), width=5)
    d.ellipse([piv_px - 4, piv_py - 4, piv_px + 4, piv_py + 4], fill=(220, 40, 40))

    # Panel B (Bottom-left): Plan View + Oar Sweep Arc & Width Envelopes
    qx0, qy0, qx1, qy1 = 34, 580, 1140, 1188
    d.rectangle([qx0, qy0, qx1, qy1], fill=(253, 251, 245), outline=(140, 140, 130), width=2)
    d.text((qx0 + 12, qy0 + 8), "B. Plan View & Starboard Oar Sweep Arc (stroke_deg = +/-28 deg around Rz = 58 deg, 4.20 m Remo)", fill=(30, 35, 45), font=f_h)

    sc_q = 8.6
    ox_q = qx0 + 62
    oy_q = qy0 + 235  # ship centerline

    # Plot swept zone polygon
    arc_px = []
    for k in range(0, 181, 3):
        t = math.radians(k)
        th = -28.0 * math.cos(t)
        v = rot_z(rot_x((0.0, 2.80, 0.0), -36.0), 58.0 + th)
        px = ox_q + (25.0 + v[0] * 10.0) * sc_q
        py = oy_q + (0.45 + v[1]) * 10.0 * sc_q  # starboard downward on screen (+Y down)
        arc_px.append((px, py))
    piv_qx = ox_q + 25.0 * sc_q
    piv_qy = oy_q + 0.45 * 10.0 * sc_q
    d.polygon([(piv_qx, piv_qy)] + arc_px, fill=(255, 232, 200), outline=(210, 120, 30))

    # Draw boat top-down voxels
    for (x, y, z) in sorted(vox.keys(), key=lambda p: p[2]):
        c = vox[(x, y, z)]
        rx = ox_q + x * sc_q
        ry = oy_q + (y - 23.5) * sc_q
        d.rectangle([rx, ry, rx + sc_q, ry + sc_q], fill=rgb(c))

    # Neutral oar & Catch/Finish rays
    for lbl_th, ang, col, w, dx_t, dy_t in [
        (f"Catch (30 deg): +{kin['dynamic_max_stbd_reach_m']:.2f} m stbd ({kin['dynamic_peak_swept_beam_m']:.2f} m W)", -28.0, (200, 45, 45), 3, -40, 12),
        (f"Neutral Push (58 deg): +{kin['neutral_stbd_reach_m']:.2f} m stbd ({kin['neutral_swept_beam_m']:.2f} m W)", 0.0, (25, 110, 45), 4, 14, 14),
        (f"Aft / Feathered (86 deg): +{kin['aft_stroke_min_stbd_m']:.2f} m stbd ({kin['feathered_pass_beam_m']:.2f} m W)", +28.0, (30, 80, 175), 3, 18, 28),
    ]:
        v = rot_z(rot_x((0.0, 2.80, 0.0), -36.0), 58.0 + ang)
        vg = rot_z(rot_x((0.0, -1.35, 0.0), -36.0), 58.0 + ang)
        x0, y0 = piv_qx + vg[0]*10*sc_q, piv_qy + vg[1]*10*sc_q
        x1, y1 = piv_qx + v[0]*10*sc_q, piv_qy + v[1]*10*sc_q
        d.line([x0, y0, x1, y1], fill=col, width=w)
        d.text((x1 + dx_t, y1 + dy_t), lbl_th, fill=col, font=f_m)

    # Beam caliper bars
    yb_p = oy_q - 0.70 * 10 * sc_q
    yb_s = oy_q + 0.70 * 10 * sc_q
    d.line([ox_q + 54*sc_q, yb_p, ox_q + 54*sc_q, yb_s], fill=(30, 30, 30), width=2)
    d.text((ox_q + 55*sc_q, oy_q - 0.90*10*sc_q - 14), "Hull Beam = 1.40 m (0.70 + 0.70 m)", fill=(30, 30, 30), font=f_m)

    # Panel C (Right): Clearance Envelopes & Quantitative Metrics Table
    cx0, cy0, cx1, cy1 = 1156, 96, W - 34, H - 34
    d.rectangle([cx0, cy0, cx1, cy1], fill=(253, 251, 245), outline=(140, 140, 130), width=2)
    d.text((cx0 + 14, cy0 + 10), "C. Step 3 Show Metrics & Envelopes", fill=(30, 35, 45), font=f_h)

    lines = [
        ("Dimensions (0.10 m/vx show vs 0.05 m):", (25, 30, 40)),
        ("  LOA = 10.50 m (105 vx @ 0.10m; 210 @ 0.05m)", (55, 62, 72)),
        ("  Hull Beam = 1.40 m (14 vx)  |  LWL = 8.25 m", (55, 62, 72)),
        ("  Draft (z_wl) = 0.20 m (z=2 @ 0.1m; z=4 @ 0.05m)", (55, 62, 72)),
        ("  Freeboard mid = +0.30 m  |  Poppa = +0.40 m WL", (55, 62, 72)),
        ("  Bow Ferro = +1.00 m (show) / +1.05 m (0.05m) WL", (55, 62, 72)),
        ("  Stern Ferro = +0.80 m (show) / +0.85 m (0.05m) WL", (55, 62, 72)),
        ("", (0, 0, 0)),
        ("Remo Oar Sweep (4.20 m, pivot y=+0.45m, z=+0.65m):", (25, 30, 40)),
        (f"  Neutral pose (-36,0,58): +{kin['neutral_stbd_reach_m']:.2f} m stbd", (25, 105, 45)),
        (f"    -> Neutral swept width = {kin['neutral_swept_beam_m']:.2f} m", (25, 105, 45)),
        (f"    -> Blade immersion = -{kin['neutral_blade_depth_below_wl_m']:.2f} m WL", (25, 105, 45)),
        (f"    -> Loom grip height = +{kin['neutral_grip_above_wl_m']:.2f} m WL", (25, 105, 45)),
        (f"  Dynamic catch (phi=0): +{kin['dynamic_max_stbd_reach_m']:.2f} m stbd", (190, 45, 45)),
        (f"    -> Peak catch width = {kin['dynamic_peak_swept_beam_m']:.2f} m", (190, 45, 45)),
        (f"  Aft/feathered (phi=0.5): +{kin['aft_stroke_min_stbd_m']:.2f} m stbd", (30, 80, 175)),
        (f"    -> Feathered width = {kin['feathered_pass_beam_m']:.2f} m", (30, 80, 175)),
        (f"  Max blade depth = -{kin['min_blade_z_below_wl_m']:.2f} m WL (total 1.25 m)", (55, 62, 72)),
        ("", (0, 0, 0)),
        ("Air-Draft & Bridge Passage Envelopes (vs WL):", (25, 30, 40)),
        (f"  [E1] Peak oar sweep:   2.10 m H x {kin['dynamic_peak_swept_beam_m']:.2f} m W", (190, 45, 45)),
        (f"  [E2] Standing steady:  2.10 m H x {kin['neutral_swept_beam_m']:.2f} m W", (25, 105, 45)),
        ("  [E3] Standing+feather: 2.10 m H x 1.50 m W", (30, 80, 175)),
        ("  [E4] Crouch+feather:   1.75 m H x 1.50 m W", (180, 105, 25)),
        ("  [E5] Uncrewed moored:  1.05 m H x 1.40 m W", (85, 92, 100)),
        ("", (0, 0, 0)),
        ("Topology & Blockside Show Readiness:", (25, 30, 40)),
        (f"  Show voxel count: {len(vox)} (1 component, 0 cavities)", (25, 105, 45)),
        ("  Oar link: apex-one-venice-gondola-1666-oar @0.5x", (55, 62, 72)),
        ("  Canal min depth required: >= 1.25 m (Grand 4.5m,", (55, 62, 72)),
        ("    Rio 2.2m -> clean oar clearance >= 0.95 m!)", (55, 62, 72)),
    ]
    yy = cy0 + 48
    for txt, col in lines:
        if txt:
            d.text((cx0 + 16, yy), txt, fill=col, font=f_m)
        yy += 22

    # Mini Cross-Section Box Diagram (Port-Starboard view) inside bottom of Panel C
    bx0, by0, bx1, by1 = cx0 + 28, cy0 + 735, cx1 - 28, cy1 - 24
    d.rectangle([bx0, by0, bx1, by1], fill=(246, 249, 252), outline=(170, 180, 195))
    d.text((bx0 + 10, by0 + 8), "Cross-Section Envelope (Arch Fit Reference)", fill=(35, 45, 60), font=f_h)
    xc = (bx0 + bx1) / 2 - 40
    yw_c = by1 - 45
    sc_c = 70.0  # px per meter!
    d.line([bx0 + 10, yw_c, bx1 - 10, yw_c], fill=(20, 95, 165), width=2)
    # Draw E1, E2, E4, E5 boxes
    # E5 Hull: [-0.70, +0.70] x [0, 1.05]
    d.rectangle([xc - 0.70*sc_c, yw_c - 1.05*sc_c, xc + 0.70*sc_c, yw_c], outline=(90, 95, 105), width=2)
    # E4 Crouch+feather: [-0.70, +0.80] x [0, 1.75]
    d.rectangle([xc - 0.70*sc_c, yw_c - 1.75*sc_c, xc + 0.80*sc_c, yw_c], outline=(180, 105, 25), width=2)
    # E2 Standing neutral: [-0.70, +1.74] x [0, 2.10]
    d.rectangle([xc - 0.70*sc_c, yw_c - 2.10*sc_c, xc + 1.74*sc_c, yw_c], outline=(25, 110, 45), width=2)
    # E1 Dynamic peak catch: [-0.70, +2.52] x [0, 2.10]
    d.rectangle([xc - 0.70*sc_c, yw_c - 2.10*sc_c, xc + 2.52*sc_c, yw_c], outline=(190, 45, 45), width=2)
    d.text((xc - 0.65*sc_c, yw_c - 1.00*sc_c + 4), "Hull 1.40x1.05m", fill=(80, 85, 95), font=f_m)
    d.text((xc - 0.65*sc_c, yw_c - 1.75*sc_c + 4), "Crouch 1.50x1.75m", fill=(180, 105, 25), font=f_m)
    d.text((xc - 0.65*sc_c, yw_c - 2.10*sc_c + 4), "Stand 2.44x2.10m", fill=(25, 110, 45), font=f_m)
    d.text((xc + 1.80*sc_c, yw_c - 1.30*sc_c), "Peak 3.22m", fill=(190, 45, 45), font=f_m)

    out_png = os.path.join(SHEETS_DIR, "sheet02_show_measurements.png")
    img.save(out_png)
    return out_png


def main():
    vox = build_show_gondola()
    n_comp, sizes, anchors, cav = check_connectivity(vox, "show")
    print(f"Show gondola: count={len(vox)}, components={n_comp} {sizes}, cavities={cav}")
    if n_comp != 1 or cav != 0:
        raise RuntimeError(f"Expected 1 component and 0 cavities, got comp={n_comp}, cav={cav}, sizes={sizes}, anchors={anchors}")

    # Write deterministic sorted voxels_show.txt
    v_path = os.path.join(DESIGN_DIR, "voxels_show.txt")
    with open(v_path, "w", encoding="utf-8") as f:
        f.write("# 1666 Venice Gondola Show Version (0.10 m/voxel, 112x48x32)\n")
        for (x, y, z) in sorted(vox.keys()):
            f.write(f"{x},{y},{z},{vox[(x, y, z)]}\n")

    xs = [k[0] for k in vox]
    ys = [k[1] for k in vox]
    zs = [k[2] for k in vox]
    kin = oar_kinematics()

    metrics = {
        "scale_m": SCALE_M,
        "voxel_count": len(vox),
        "components": n_comp,
        "cavities": cav,
        "bbox_vx": {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]},
        "loa_m": round((max(xs) - min(xs) + 1) * SCALE_M, 2),
        "hull_beam_m": round((max(ys) - min(ys) + 1) * SCALE_M, 2),
        "waterline_z_idx": 2,
        "draft_m": 0.20,
        "poppa_deck_top_above_wl_m": 0.40,
        "bow_ferro_above_wl_m": round((11 + 1) * SCALE_M - 0.20, 2),
        "stern_ferro_above_wl_m": round((9 + 1) * SCALE_M - 0.20, 2),
        "standing_gondoliere_peak_above_wl_m": round((max(zs) + 1) * SCALE_M - 0.20, 2),
        "crouched_gondoliere_above_wl_m": 1.75,
        "passengers_max_above_wl_m": 1.10,
        "oar_kinematics": {k: v for k, v in kin.items() if k != "sweep_arc_points"},
        "clearance_envelopes": {
            "E1_dynamic_catch": {"height_m": 2.10, "width_m": round(kin["dynamic_peak_swept_beam_m"], 2)},
            "E2_standing_neutral": {"height_m": 2.10, "width_m": round(kin["neutral_swept_beam_m"], 2)},
            "E3_standing_feathered": {"height_m": 2.10, "width_m": 1.50},
            "E4_crouched_feathered": {"height_m": 1.75, "width_m": 1.50},
            "E5_uncrewed_moored": {"height_m": 1.05, "width_m": 1.40},
        },
        "min_canal_depth_m": 1.25,
    }
    m_path = os.path.join(DESIGN_DIR, "metrics_step3.json")
    with open(m_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    s_path = make_sheet(vox, kin)
    print(f"LOA={metrics['loa_m']}m B={metrics['hull_beam_m']}m StandingPeak=+{metrics['standing_gondoliere_peak_above_wl_m']}m WL")
    print(f"Neutral swept width={kin['neutral_swept_beam_m']}m | Dynamic catch width={kin['dynamic_peak_swept_beam_m']}m | Feathered={kin['feathered_pass_beam_m']}m")
    print(f"Saved: {v_path}, {m_path}, {s_path}")


if __name__ == "__main__":
    main()
