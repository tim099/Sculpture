#!/usr/bin/env python3
"""
Build the 4 historical European port lighthouses (0.1 m/voxel) under calli-lighthouses-01m:
1. livorno-fanale: Fanale di Livorno (Fanale dei Pisani, 1303-1305), 120x120x420
   - 13-sided polygonal stepped stone base (Pietra della Verruca), two concentric cylindrical drums
     with projecting machicolated & crenellated galleries (ballatoi su archetti pensili), glazed lantern drum + dome.
2. larochelle-lanterne: Tour de la Lanterne (La Rochelle, 1445-1468), 160x160x480
   - Cylindrical Charente limestone base with stair turret & machicolated parapet walkway,
     octagonal Flamboyant Gothic stone spire with 8 crocketed ribs, 4 Gothic dormers,
     and the signature projecting octagonal glazed stone lantern turret on the seaward (-y) side of the spire base.
3. marseille-fanal: Tour du Fanal (Marseille Saint-Jean, 1644-1646), 120x120x320
   - Square battered Provençal limestone plinth, stout cylindrical watch/beacon tower with mid-tower
     projecting corbelled gallery on false machicolations (faux-mâchicoulis), upper parapet terrace, domed stone lantern.
4. cadiz-san-sebastian: Torre-Atalaya de San Sebastián (Cádiz, 1613-1617), 160x160x260
   - Truncated-conical (troncocónico) fortified watchtower of warm golden-brown piedra ostionera,
     exterior masonry stair-bridge to raised portal, cordón magistral, parapet terrace, and domed lantern turret.
"""

import json
import math
import os
import subprocess
import sys
from collections import deque
import numpy as np

WORKS_DIR = "D:/Unity/Valhalla/Sculpture/works"
PARENT_WORK = "calli-lighthouses-01m"

# RGB332 palette constants (matching calli-genoa-lanterna-01m & European port stone palettes)
STONE_LIGHT = 182       # warm light limestone / sunlit ashlar
STONE_MID = 146         # standard warm ashlar
STONE_DARK = 109        # weathered ashlar / mortar / quoins
STONE_DEEP = 73         # deep shadow stone / plinth base / embrasures
OSTIONERA_LIGHT = 214   # warm golden-ochre shell limestone (Cádiz)
OSTIONERA_MID = 178     # golden-brown piedra ostionera
OSTIONERA_DARK = 141    # dark weathered ostionera / reef rock
WOOD_DARK = 68          # heavy oak door / timber beams
IRON_DARK = 36          # wrought iron / cannon / hardware
COPPER_DOME = 77        # weathered copper/lead dome highlight
COPPER_DARK = 41        # dark patinated copper/lead roof
BRASS_FRAME = 200       # brass / bronze lantern frame
GLASS_PANE = 187        # glazed lantern window pane
FIRE_CORE = 253         # bright yellow-white beacon flame
FIRE_GLOW = 244         # orange-gold fire glow
RED_CREST = 196         # heraldic red (Medici / Pisa / royal arms)
WHITE_MARBLE = 219      # white Carrara marble / limestone trim


def run_senate(args_dict):
    cmd = ["senate", "cmd", "sculpture"]
    for k, v in args_dict.items():
        cmd.extend(["--arg", f"{k}={v}"])
    res = subprocess.run(cmd, cwd="D:/Unity/Senate", capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print("ERROR running:", " ".join(cmd))
        print(res.stdout)
        print(res.stderr)
        sys.exit(1)
    return res.stdout


def ensure_subwork(sub_id, size_str, title, style, tags):
    work_dir = os.path.join(WORKS_DIR, sub_id)
    if not os.path.exists(work_dir):
        print(f"Creating subwork {sub_id} ({size_str})...")
        run_senate({
            "op": "work",
            "sub": "create",
            "persona": "calli",
            "work": sub_id,
            "parent_work": PARENT_WORK,
            "size": size_str,
            "title": title,
        })
    run_senate({
        "op": "work",
        "sub": "update",
        "persona": "calli",
        "work": sub_id,
        "meters_per_voxel": "0.1",
        "tags": tags,
        "notes": style,
    })


def stone_tex(x, y, z, c_light=STONE_LIGHT, c_mid=STONE_MID, c_dark=STONE_DARK):
    """Ashlar stone course texture with subtle block variation."""
    course = z // 6
    block = (x + (course % 2) * 7 + y * 3) // 12
    h = (course * 37 + block * 101 + (x // 4) * 17 + (y // 4) * 29) & 15
    if z % 6 == 0 and h < 6:
        return c_dark
    if h < 3:
        return c_dark
    if h < 11:
        return c_mid
    return c_light


def clean_floating(grid):
    """Keep only voxels 6-connected to z=0 ground layer."""
    nx, ny, nz = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    q = deque()
    xs, ys = np.where(grid[:, :, 0] > 0)
    for x, y in zip(xs, ys):
        visited[x, y, 0] = True
        q.append((x, y, 0))
    dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    while q:
        x, y, z = q.popleft()
        for dx, dy, dz in dirs:
            nx_, ny_, nz_ = x + dx, y + dy, z + dz
            if 0 <= nx_ < nx and 0 <= ny_ < ny and 0 <= nz_ < nz:
                if grid[nx_, ny_, nz_] > 0 and not visited[nx_, ny_, nz_]:
                    visited[nx_, ny_, nz_] = True
                    q.append((nx_, ny_, nz_))
    removed = int(np.sum((grid > 0) & (~visited)))
    if removed > 0:
        grid[~visited] = 0
    return removed


def save_and_stamp(sub_id, grid, anchors):
    # Hollow deep interior (keep 6-voxel outer shell + z=0..3 base) so .vxk size matches genoa-lanterna (~350k voxels)
    solid = grid > 0
    eroded = solid.copy()
    for _ in range(5):
        eroded = (
            eroded
            & np.pad(eroded[1:, :, :], ((0, 1), (0, 0), (0, 0)), constant_values=False)
            & np.pad(eroded[:-1, :, :], ((1, 0), (0, 0), (0, 0)), constant_values=False)
            & np.pad(eroded[:, 1:, :], ((0, 0), (0, 1), (0, 0)), constant_values=False)
            & np.pad(eroded[:, :-1, :], ((0, 0), (1, 0), (0, 0)), constant_values=False)
            & np.pad(eroded[:, :, 1:], ((0, 0), (0, 0), (0, 1)), constant_values=False)
            & np.pad(eroded[:, :, :-1], ((0, 0), (0, 0), (1, 0)), constant_values=False)
        )
    eroded[:, :, :4] = False
    grid[eroded] = 0

    removed = clean_floating(grid)
    xs, ys, zs = np.where(grid > 0)
    cs = grid[xs, ys, zs]
    total = len(xs)
    print(f"[{sub_id}] total voxels = {total:,} (removed {removed} floating)")
    work_dir = os.path.join(WORKS_DIR, sub_id)
    design_dir = os.path.join(work_dir, "design")
    os.makedirs(design_dir, exist_ok=True)
    vox_path = os.path.join(design_dir, "voxels.txt")
    with open(vox_path, "w", encoding="utf-8") as f:
        lines = [f"{x},{y},{z},{c}\n" for x, y, z, c in zip(xs, ys, zs, cs)]
        f.writelines(lines)

    run_senate({
        "op": "stampvox",
        "persona": "calli",
        "work": sub_id,
        "voxels": vox_path.replace("\\", "/"),
        "at": "0,0,0",
        "expect_pixels": str(total),
        "overwrite": "1",
        "share": "0",
    })

    for name, pt in anchors.items():
        run_senate({
            "op": "work",
            "sub": "anchor",
            "persona": "calli",
            "work": sub_id,
            "name": name,
            "at": f"{pt[0]},{pt[1]},{pt[2]}",
        })

    meta_path = os.path.join(work_dir, "work_meta.json")
    meta = {
        "schema": 1,
        "meta": {
            "kind": "searchlight",
            "light_angle": 3.5,
            "light_period": 14,
            "light_range": 650,
            "light_sweep": 24,
        },
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"[{sub_id}] stamped, anchored, and wrote work_meta.json.")


def build_livorno_fanale():
    """
    1. Fanale di Livorno (1303-1305) — 120 x 120 x 420 (12m x 12m x 42m)
    - z=0..16: 13-sided polygonal rocky/stepped base (R_poly ~ 54 -> 48)
    - z=16..52: 13-sided polygonal battered base drum (R ~ 46 -> 42) with entrance door at -y (y ~ 16..24, z=16..38)
    - z=52..200: Lower cylindrical shaft (R = 38), with vertical arrow slits & Medici/Pisa marble plaques
    - z=200..222: Lower projecting machicolated gallery (ballatoio su archetti pensili, R = 38 -> 44) with Ghibelline/square battlements
    - z=216..348: Upper narrower cylindrical shaft (R = 29), with arched windows
    - z=348..368: Upper projecting machicolated gallery (R = 29 -> 35) with crenellations
    - z=362..396: Glazed cylindrical lantern drum (R = 20) with brass ribs & glowing beacon fire at z=372..386
    - z=396..418: Domed cupola & finial
    """
    nx, ny, nz = 120, 120, 420
    grid = np.zeros((nx, ny, nz), dtype=np.uint8)
    cx, cy = 59.5, 59.5

    # Precompute 13-gon signed distance / radius factor
    n_sides = 13
    angles_13 = [2.0 * math.pi * k / n_sides - math.pi / 2.0 for k in range(n_sides)]
    normals_13 = [(math.cos(a), math.sin(a)) for a in angles_13]

    for x in range(nx):
        dx = x - cx
        for y in range(ny):
            dy = y - cy
            r = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)  # -pi/2 is -y (front/seaward)
            poly13 = max(dx * nx_ + dy * ny_ for nx_, ny_ in normals_13)

            # 1) z=0..16: 13-sided stepped foundation & sea-polished stone apron
            for z in range(0, 17):
                lim = 52.0 - (z // 5) * 2.0
                if poly13 <= lim:
                    if z < 4 or poly13 > lim - 2.5:
                        grid[x, y, z] = STONE_DEEP if (x + y + z) % 3 == 0 else STONE_DARK
                    else:
                        grid[x, y, z] = stone_tex(x, y, z)

            # 2) z=16..52: 13-sided polygonal battered base (Barbican / basamento poligonale)
            for z in range(16, 53):
                t = (z - 16) / 36.0
                lim = 46.0 - 4.0 * t
                if poly13 <= lim:
                    if z in (50, 51, 52) and poly13 <= lim + 1.0:
                        grid[x, y, z] = WHITE_MARBLE  # stone torus molding (toro marcapiano)
                    elif poly13 >= lim - 1.8:
                        grid[x, y, z] = stone_tex(x, y, z)
                    else:
                        grid[x, y, z] = STONE_MID

            # Front steps leading up to door at -y (x=51..68, y=6..18, z=0..16)
            if 51 <= x <= 68 and 7 <= y <= 18:
                step_h = max(0, min(16, (y - 7) * 2))
                for z in range(0, step_h + 1):
                    grid[x, y, z] = STONE_DARK if z % 2 == 0 else STONE_LIGHT

            # 3) z=52..200: Lower cylindrical shaft (R = 38)
            if r <= 45.0:
                for z in range(52, 201):
                    if r <= 38.0:
                        c = stone_tex(x, y, z)
                        # Subtle vertical pilaster / ashlar bands and horizontal stringcourse at z=126
                        if z in (125, 126, 127) and r >= 36.0:
                            c = WHITE_MARBLE
                        elif r >= 36.2 and int(round((ang + math.pi) / (2 * math.pi) * 13)) % 2 == 0 and (z % 18 == 0):
                            c = STONE_DARK
                        grid[x, y, z] = c

                # 4) z=196..222: Lower machicolated gallery (ballatoio inferiore, R=38 -> 44)
                # 24 corbelled brackets (beccatelli) & blind arches
                sector24 = ((ang + math.pi) / (2.0 * math.pi) * 24.0) % 1.0
                is_bracket = (sector24 < 0.35 or sector24 > 0.65)
                for z in range(196, 223):
                    if z < 206:
                        reach = 38.0 + (z - 196) * 0.6
                        if r <= 38.0:
                            grid[x, y, z] = stone_tex(x, y, z)
                        elif r <= reach and (is_bracket or z >= 203):
                            grid[x, y, z] = STONE_DARK if z < 203 else WHITE_MARBLE
                    elif z <= 214:
                        # Parapet floor & solid wall
                        if r <= 44.0:
                            if z <= 209 or r >= 40.5 or r <= 31.0:
                                grid[x, y, z] = STONE_LIGHT if r >= 42.5 else stone_tex(x, y, z)
                    else:
                        # Merlons (z=215..222) + inner shaft continuation
                        if r <= 30.0:
                            grid[x, y, z] = stone_tex(x, y, z)
                        elif 40.5 <= r <= 44.0 and is_bracket:
                            grid[x, y, z] = STONE_LIGHT if z < 221 else WHITE_MARBLE

                # 5) z=216..348: Upper cylindrical shaft (R = 29)
                for z in range(216, 349):
                    if r <= 29.0:
                        c = stone_tex(x, y, z)
                        if z in (282, 283) and r >= 27.0:
                            c = WHITE_MARBLE
                        grid[x, y, z] = c

                # 6) z=344..368: Upper machicolated gallery (ballatoio superiore, R=29 -> 35.5)
                sector20 = ((ang + math.pi) / (2.0 * math.pi) * 20.0) % 1.0
                is_b20 = (sector20 < 0.36 or sector20 > 0.64)
                for z in range(344, 369):
                    if z < 353:
                        reach = 29.0 + (z - 344) * 0.72
                        if r <= 29.0:
                            grid[x, y, z] = stone_tex(x, y, z)
                        elif r <= reach and (is_b20 or z >= 350):
                            grid[x, y, z] = STONE_DARK if z < 350 else WHITE_MARBLE
                    elif z <= 361:
                        if r <= 35.5:
                            if z <= 356 or r >= 32.0 or r <= 21.0:
                                grid[x, y, z] = STONE_LIGHT if r >= 34.0 else stone_tex(x, y, z)
                    else:
                        # Merlons (z=362..368) + lantern base inside
                        if r <= 21.0:
                            grid[x, y, z] = stone_tex(x, y, z)
                        elif 32.0 <= r <= 35.5 and is_b20:
                            grid[x, y, z] = STONE_LIGHT if z < 367 else WHITE_MARBLE

                # 7) z=362..396: Glazed lantern drum (R = 20)
                sector8 = ((ang + math.pi) / (2.0 * math.pi) * 8.0) % 1.0
                is_rib = (sector8 < 0.22 or sector8 > 0.78)
                for z in range(362, 397):
                    if z <= 368:
                        if r <= 20.5:
                            grid[x, y, z] = WHITE_MARBLE if r >= 18.5 else STONE_MID
                    elif z <= 391:
                        if r <= 9.0:
                            # Glowing beacon fire & brazier column in the center
                            if z < 372:
                                grid[x, y, z] = IRON_DARK
                            elif z <= 387 and r <= 7.0 - abs(z - 379) * 0.4:
                                grid[x, y, z] = FIRE_CORE if r <= 3.8 else FIRE_GLOW
                        elif 16.5 <= r <= 20.0:
                            if is_rib or z in (369, 370, 380, 390, 391):
                                grid[x, y, z] = BRASS_FRAME if r >= 18.0 else STONE_DARK
                            else:
                                grid[x, y, z] = GLASS_PANE
                    else:
                        # Lantern cornice (z=392..396)
                        if r <= 21.5:
                            grid[x, y, z] = WHITE_MARBLE if z in (392, 393) else COPPER_DARK

                # 8) z=397..419: Ribbed dome cupola & cross finial
                for z in range(397, 420):
                    if z <= 411:
                        t = (z - 397) / 14.0
                        dome_r = 20.0 * math.sqrt(max(0.0, 1.0 - t * t))
                        if r <= dome_r:
                            grid[x, y, z] = COPPER_DOME if is_rib else COPPER_DARK
                    elif z <= 415:
                        if r <= 3.2:
                            grid[x, y, z] = BRASS_FRAME
                    else:
                        if r <= 1.5 or (z == 417 and abs(dx) <= 4.0 and abs(dy) <= 1.2):
                            grid[x, y, z] = BRASS_FRAME

    # Carve & frame arched entrance door on -y face (x=54..65, y=12..25, z=16..38)
    for x in range(52, 68):
        for y in range(12, 26):
            for z in range(16, 41):
                dx_d = abs(x - 59.5)
                arch_z = 32.0 + math.sqrt(max(0.0, 36.0 - dx_d * dx_d))
                if z <= arch_z:
                    if dx_d <= 4.5 and z <= arch_z - 1.5:
                        if y >= 17:
                            grid[x, y, z] = WOOD_DARK if (z % 5 != 0 and x != 59) else IRON_DARK
                        else:
                            grid[x, y, z] = 0
                    elif dx_d <= 6.5 and y <= 20:
                        grid[x, y, z] = WHITE_MARBLE

    # Medici / Pisa heraldic shield above door (x=55..64, y=15..19, z=41..50)
    for x in range(55, 65):
        for z in range(41, 50):
            for y in range(15, 20):
                if grid[x, y, z] > 0:
                    if x in (55, 64) or z in (41, 49):
                        grid[x, y, z] = WHITE_MARBLE
                    elif x in (59, 60) or z == 45:
                        grid[x, y, z] = WHITE_MARBLE
                    else:
                        grid[x, y, z] = RED_CREST

    # Narrow arched windows on the two shafts (4 cardinal directions)
    for z_base, r_out in [(85, 38), (145, 38), (245, 29), (305, 29)]:
        for w in range(56, 64):
            for depth in range(int(r_out) - 5, int(r_out) + 2):
                for dz in range(0, 18):
                    z = z_base + dz
                    dw = abs(w - 59.5)
                    if dz <= 12 + math.sqrt(max(0.0, 12.25 - dw * dw)):
                        val = IRON_DARK if dw <= 1.5 else WHITE_MARBLE
                        grid[w, int(59.5 - depth), z] = val
                        grid[w, int(59.5 + depth), z] = val
                        grid[int(59.5 - depth), w, z] = val
                        grid[int(59.5 + depth), w, z] = val

    anchors = {
        "lot-0": [0, 0, 0],
        "door": [59, 15, 16],
        "work-a1": [59, 22, 355],
        "wick": [59, 59, 378],
        "beam-to": [59, 5, 375],
    }
    return grid, anchors


def build_larochelle_lanterne():
    """
    2. Tour de la Lanterne (La Rochelle, 1445-1468) — 160 x 160 x 480 (16m x 16m x 48m)
    - z=0..36: Battered cylindrical Charente limestone base talus (R = 64 -> 55) + stair turret bulge on +x/+y
    - z=36..220: Massive cylindrical fortress cylinder (R = 54) with stair turret (tourelle d'escalier) on NE (+x,+y)
      and narrow medieval arrow loops / mullioned windows
    - z=220..250: Projecting machicolated & crenellated parapet walkway (chemin de ronde sur mâchicoulis, R = 60)
    - z=248..468: Tall octagonal Flamboyant Gothic stone spire (flèche octogonale, R_oct = 40 -> 3)
      with 8 projecting stone ribs adorned with Gothic crockets (crochets gothiques) and 4 gabled Gothic dormers (lucarnes)
    - z=248..338: Signature projecting octagonal glazed stone lantern turret (tourelle de la lanterne)
      engaged on the seaward (-y) side of the spire base (center x=79.5, y=38.0, R_turret = 14),
      housing the glowing beacon flame at z=294..314 (wick=[79,38,304], beam-to=[79,4,301])!
    """
    nx, ny, nz = 160, 160, 480
    grid = np.zeros((nx, ny, nz), dtype=np.uint8)
    cx, cy = 79.5, 79.5

    c45 = math.sqrt(0.5)

    for x in range(nx):
        dx = x - cx
        for y in range(ny):
            dy = y - cy
            r = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            # Octagonal norm (inscribed circle radius)
            oct_r = max(abs(dx), abs(dy), (abs(dx) + abs(dy)) * c45)
            # Engaged stair turret on NE (+x, +y) side: center (cx+38, cy+30), R=20
            r_stair = math.hypot(dx - 38.0, dy - 30.0)

            # 1) z=0..36: Battered limestone talus base (R = 64 -> 54)
            for z in range(0, 37):
                t = z / 36.0
                r_lim = 64.0 - 10.0 * t
                st_lim = 24.0 - 4.0 * t
                if r <= r_lim or r_stair <= st_lim:
                    if z < 4:
                        grid[x, y, z] = STONE_DEEP if (x + y) % 2 == 0 else STONE_DARK
                    elif abs(r - r_lim) <= 1.8 or abs(r_stair - st_lim) <= 1.8:
                        grid[x, y, z] = stone_tex(x, y, z, WHITE_MARBLE, STONE_LIGHT, STONE_MID)
                    else:
                        grid[x, y, z] = STONE_MID

            # Front steps at -y (x=71..88, y=10..22, z=0..16)
            if 71 <= x <= 88 and 10 <= y <= 22:
                sh = max(0, min(16, (y - 10) * 2))
                for z in range(0, sh + 1):
                    grid[x, y, z] = STONE_DARK if z % 2 == 0 else STONE_LIGHT

            # 2) z=36..220: Cylindrical fortress tower (R = 54) + NE stair turret (R = 20)
            if r <= 62.0 or r_stair <= 24.0:
                for z in range(36, 221):
                    in_main = (r <= 54.0)
                    in_stair = (r_stair <= 20.0)
                    if in_main or in_stair:
                        c = stone_tex(x, y, z, WHITE_MARBLE, STONE_LIGHT, STONE_MID)
                        if z in (36, 37, 110, 111, 175, 176) and (r >= 52.0 or r_stair >= 18.0):
                            c = WHITE_MARBLE
                        grid[x, y, z] = c

                # 3) z=216..250: Machicolated & crenellated parapet walkway (R = 54 -> 60.5)
                sector32 = ((ang + math.pi) / (2.0 * math.pi) * 32.0) % 1.0
                is_corbel = (sector32 < 0.38 or sector32 > 0.62)
                for z in range(216, 251):
                    if z < 228:
                        reach = 54.0 + (z - 216) * 0.55
                        st_reach = 20.0 + (z - 216) * 0.35
                        if r <= 54.0 or r_stair <= 20.0:
                            grid[x, y, z] = stone_tex(x, y, z, WHITE_MARBLE, STONE_LIGHT, STONE_MID)
                        elif (r <= reach or r_stair <= st_reach) and (is_corbel or z >= 225):
                            grid[x, y, z] = STONE_DARK if z < 225 else WHITE_MARBLE
                    elif z <= 238:
                        if r <= 60.5 or r_stair <= 24.0:
                            if z <= 232 or r >= 56.5 or r_stair >= 20.5 or oct_r <= 42.0:
                                grid[x, y, z] = WHITE_MARBLE if (r >= 59.0 or z == 238) else STONE_LIGHT
                    else:
                        # Crenellations + flamboyant openwork parapet & spire base inside
                        if oct_r <= 41.0 or r_stair <= 18.0:
                            grid[x, y, z] = stone_tex(x, y, z, WHITE_MARBLE, STONE_LIGHT, STONE_MID)
                        elif (56.5 <= r <= 60.5 or 20.5 <= r_stair <= 24.0) and is_corbel:
                            grid[x, y, z] = WHITE_MARBLE if z >= 248 else STONE_LIGHT

                # Small conical stone roof over the NE stair turret (z=250..286)
                if r_stair <= 19.0:
                    for z in range(250, 287):
                        cone_r = 18.0 * (1.0 - (z - 250) / 36.0)
                        if r_stair <= cone_r:
                            grid[x, y, z] = STONE_DARK if (z // 4) % 2 == 0 else STONE_LIGHT

            # 4) z=248..476: Octagonal Flamboyant Gothic stone spire (oct_r: 40 -> 2.5)
            if oct_r <= 46.0:
                # Distance to the 8 octagon vertices (ribs at angles k * pi/4 + pi/8)
                rib_min = 999.0
                for k in range(8):
                    ra = k * (math.pi / 4.0) + (math.pi / 8.0)
                    proj = dx * math.cos(ra) + dy * math.sin(ra)
                    perp = abs(-dx * math.sin(ra) + dy * math.cos(ra))
                    if proj > 0:
                        rib_min = min(rib_min, perp)

                for z in range(248, 477):
                    if z <= 462:
                        t = (z - 248) / 214.0
                        spire_r = 40.0 * (1.0 - t) + 2.5 * t
                        # Crockets (crochets gothiques) projecting along the 8 ribs every 14 voxels
                        crocket = 2.8 if (rib_min <= 2.2 and (z % 14) in (0, 1, 2, 3)) else (1.4 if rib_min <= 2.0 else 0.0)
                        if oct_r <= spire_r + crocket:
                            if oct_r > spire_r:
                                grid[x, y, z] = WHITE_MARBLE
                            elif oct_r >= spire_r - 2.0:
                                grid[x, y, z] = WHITE_MARBLE if (z % 12 == 0 or rib_min <= 2.2) else STONE_LIGHT
                            else:
                                grid[x, y, z] = STONE_MID
                    else:
                        # Gothic finial cross at top (z=463..476)
                        if r <= 2.2 or (z in (469, 470) and abs(dx) <= 6.0 and abs(dy) <= 1.8):
                            grid[x, y, z] = BRASS_FRAME

            # 5) Signature projecting octagonal glazed stone LANTERN TURRET on seaward (-y) side!
            # Center at (tx=79.5, ty=38.0), z=242..342
            tdx = x - 79.5
            tdy = y - 38.0
            t_oct = max(abs(tdx), abs(tdy), (abs(tdx) + abs(tdy)) * c45)
            t_ang = math.atan2(tdy, tdx)
            t_sec8 = ((t_ang + math.pi) / (2.0 * math.pi) * 8.0) % 1.0
            t_is_rib = (t_sec8 < 0.24 or t_sec8 > 0.76)

            if t_oct <= 17.0:
                for z in range(242, 344):
                    if z < 252:
                        # Corbelled stone base supporting turret
                        reach = 10.0 + (z - 242) * 0.6
                        if t_oct <= reach:
                            grid[x, y, z] = WHITE_MARBLE if z >= 249 else STONE_LIGHT
                    elif z <= 286:
                        # Stone turret body with Gothic blind tracery panels
                        if t_oct <= 15.0:
                            grid[x, y, z] = WHITE_MARBLE if (t_is_rib or z in (252, 285, 286)) else STONE_LIGHT
                    elif z <= 318:
                        # Glazed lantern chamber (z=287..318) with glowing beacon flame inside!
                        if t_oct <= 7.5:
                            if z < 292:
                                grid[x, y, z] = IRON_DARK
                            elif z <= 313 and t_oct <= 6.2 - abs(z - 303) * 0.3:
                                grid[x, y, z] = FIRE_CORE if t_oct <= 3.2 else FIRE_GLOW
                        elif 11.5 <= t_oct <= 15.0:
                            if t_is_rib or z in (287, 288, 302, 317, 318):
                                grid[x, y, z] = BRASS_FRAME if t_oct >= 13.0 else WHITE_MARBLE
                            else:
                                grid[x, y, z] = GLASS_PANE
                        elif t_oct < 11.5:
                            grid[x, y, z] = 0  # hollow inside lantern around fire
                    else:
                        # Pointed octagonal stone/copper spirelet over the lantern turret (z=319..343)
                        t_sp = 15.5 * (1.0 - (z - 319) / 24.0)
                        if t_oct <= max(1.2, t_sp):
                            grid[x, y, z] = WHITE_MARBLE if t_is_rib else COPPER_DARK

    # 4 Gothic gabled dormers (lucarnes) on E, W, S faces of spire (z=256..292)
    for sx, sy in [(1, 0), (-1, 0), (0, 1)]:
        for z in range(256, 292):
            gable_w = max(0, int(9 - (z - 256) * 0.25))
            for w in range(-gable_w, gable_w + 1):
                for d in range(30, 44):
                    px = int(79.5 + sx * d + sy * w)
                    py = int(79.5 + sy * d + sx * w)
                    if 0 <= px < nx and 0 <= py < ny:
                        if abs(w) >= gable_w - 1 or z >= 286:
                            grid[px, py, z] = WHITE_MARBLE
                        elif abs(w) <= 2 and z <= 280 and d >= 41:
                            grid[px, py, z] = IRON_DARK
                        else:
                            grid[px, py, z] = STONE_LIGHT

    # Entrance portal at -y (x=73..86, y=15..29, z=16..42)
    for x in range(72, 88):
        for y in range(15, 30):
            for z in range(16, 44):
                dx_d = abs(x - 79.5)
                arch_z = 34.0 + math.sqrt(max(0.0, 49.0 - dx_d * dx_d))
                if z <= arch_z:
                    if dx_d <= 4.5 and z <= arch_z - 2.0:
                        if y >= 22:
                            grid[x, y, z] = WOOD_DARK if (z % 5 != 0 and x != 79) else IRON_DARK
                        else:
                            grid[x, y, z] = 0
                    elif dx_d <= 7.0 and y <= 24:
                        grid[x, y, z] = WHITE_MARBLE

    # Vertical arrow slits / Gothic lancet windows on main cylinder
    for z_base in (75, 130, 180):
        for w in range(76, 84):
            for d in range(49, 55):
                for dz in range(0, 20):
                    z = z_base + dz
                    dw = abs(w - 79.5)
                    if dz <= 15 + (3 - dw):
                        val = IRON_DARK if dw <= 1.2 else WHITE_MARBLE
                        grid[w, int(79.5 - d), z] = val
                        grid[w, int(79.5 + d), z] = val
                        grid[int(79.5 - d), w, z] = val
                        grid[int(79.5 + d), w, z] = val

    anchors = {
        "lot-0": [0, 0, 0],
        "door": [79, 19, 16],
        "work-a1": [79, 24, 240],
        "wick": [79, 38, 304],
        "beam-to": [79, 4, 301],
    }
    return grid, anchors


def build_marseille_fanal():
    """
    3. Tour du Fanal (Marseille Saint-Jean, 1644-1646) — 120 x 120 x 320 (12m x 12m x 32m)
    - z=0..38: Square battered Provençal limestone plinth / rocky headland base (x,y within 48 -> 43 from center)
    - z=38..252: Stout concentric cylindrical limestone tower (R = 40 -> 38)
    - z=150..172: Signature mid-tower projecting corbelled gallery on false machicolations (faux-mâchicoulis, R = 45)
    - z=242..264: Upper corbelled parapet terrace with stone balustrade & embrasures (R = 44)
    - z=260..316: Cylindrical stone lantern turret (R = 19) on the terrace with glazed windows,
      glowing beacon fire at z=276..292, and Provençal hemispherical stone dome cupola + finial.
    """
    nx, ny, nz = 120, 120, 320
    grid = np.zeros((nx, ny, nz), dtype=np.uint8)
    cx, cy = 59.5, 59.5

    for x in range(nx):
        dx = x - cx
        for y in range(ny):
            dy = y - cy
            r = math.hypot(dx, dy)
            sq = max(abs(dx), abs(dy))
            ang = math.atan2(dy, dx)

            # 1) z=0..38: Battered square Provençal limestone plinth (sq: 49 -> 42)
            for z in range(0, 39):
                t = z / 38.0
                lim = 49.0 - 7.0 * t
                # Chamfer corners slightly
                if sq <= lim and (abs(dx) + abs(dy)) <= lim * 1.75:
                    if z < 4:
                        grid[x, y, z] = STONE_DEEP if (x + y) % 2 == 0 else STONE_DARK
                    elif z in (36, 37, 38):
                        grid[x, y, z] = WHITE_MARBLE
                    elif sq >= lim - 2.0 or abs(abs(dx) - abs(dy)) <= 2.0:
                        grid[x, y, z] = WHITE_MARBLE if (z // 4) % 2 == 0 else STONE_LIGHT
                    else:
                        grid[x, y, z] = stone_tex(x, y, z, WHITE_MARBLE, STONE_LIGHT, STONE_MID)

            # Front steps at -y (x=51..68, y=4..14, z=0..16)
            if 51 <= x <= 68 and 4 <= y <= 14:
                sh = max(0, min(16, (y - 4) * 2))
                for z in range(0, sh + 1):
                    grid[x, y, z] = STONE_DARK if z % 2 == 0 else STONE_LIGHT

            # 2) z=38..252: Stout cylindrical shaft (R = 40 -> 38.5)
            if r <= 47.0:
                sector24 = ((ang + math.pi) / (2.0 * math.pi) * 24.0) % 1.0
                is_corbel = (sector24 < 0.36 or sector24 > 0.64)

                for z in range(38, 265):
                    t = (z - 38) / 214.0
                    r_shaft = 40.0 - 1.5 * t

                    # Main cylindrical shaft up to z=252
                    if z <= 252 and r <= r_shaft:
                        grid[x, y, z] = stone_tex(x, y, z, WHITE_MARBLE, STONE_LIGHT, STONE_MID)

                    # 3) Signature mid-tower projecting corbelled cordon/gallery (faux-mâchicoulis, z=150..172)
                    if 150 <= z <= 172:
                        if z < 160:
                            reach = r_shaft + (z - 150) * 0.55
                            if r_shaft < r <= reach and (is_corbel or z >= 157):
                                grid[x, y, z] = STONE_DARK if z < 157 else WHITE_MARBLE
                        elif z <= 168:
                            if r_shaft < r <= r_shaft + 5.5:
                                grid[x, y, z] = WHITE_MARBLE if z in (160, 168) else STONE_LIGHT
                        else:
                            if r_shaft < r <= r_shaft + 4.5 and is_corbel:
                                grid[x, y, z] = WHITE_MARBLE

                    # 4) Upper corbelled parapet terrace (z=240..264, R -> 44)
                    if 240 <= z <= 264:
                        if z < 249:
                            reach = r_shaft + (z - 240) * 0.6
                            if r_shaft < r <= reach and (is_corbel or z >= 246):
                                grid[x, y, z] = STONE_DARK if z < 246 else WHITE_MARBLE
                        elif z <= 256:
                            if r <= 44.0:
                                grid[x, y, z] = WHITE_MARBLE if r >= 42.0 else STONE_LIGHT
                        else:
                            # Parapet wall with embrasures + lantern base inside
                            if r <= 20.5:
                                grid[x, y, z] = stone_tex(x, y, z, WHITE_MARBLE, STONE_LIGHT, STONE_MID)
                            elif 39.5 <= r <= 44.0 and is_corbel:
                                grid[x, y, z] = WHITE_MARBLE if z >= 263 else STONE_LIGHT

                # 5) z=260..318: Domed stone lantern turret (R = 19)
                sector8 = ((ang + math.pi) / (2.0 * math.pi) * 8.0) % 1.0
                is_rib = (sector8 < 0.24 or sector8 > 0.76)
                for z in range(260, 319):
                    if z <= 270:
                        if r <= 19.5:
                            grid[x, y, z] = WHITE_MARBLE if z in (269, 270) else STONE_LIGHT
                    elif z <= 294:
                        if r <= 8.5:
                            if z < 274:
                                grid[x, y, z] = IRON_DARK
                            elif z <= 290 and r <= 6.8 - abs(z - 282) * 0.35:
                                grid[x, y, z] = FIRE_CORE if r <= 3.5 else FIRE_GLOW
                        elif 15.5 <= r <= 19.0:
                            if is_rib or z in (271, 272, 282, 293, 294):
                                grid[x, y, z] = WHITE_MARBLE if r < 17.5 else BRASS_FRAME
                            else:
                                grid[x, y, z] = GLASS_PANE
                    elif z <= 311:
                        # Hemispherical stone/copper dome (z=295..311)
                        t_d = (z - 295) / 16.0
                        dome_r = 19.5 * math.sqrt(max(0.0, 1.0 - t_d * t_d))
                        if r <= dome_r:
                            grid[x, y, z] = WHITE_MARBLE if is_rib else COPPER_DOME
                    else:
                        if r <= 2.2 or (z == 315 and abs(dx) <= 4.0 and abs(dy) <= 1.2):
                            grid[x, y, z] = BRASS_FRAME

    # Entrance door at -y (x=53..66, y=10..22, z=16..38)
    for x in range(52, 68):
        for y in range(10, 23):
            for z in range(16, 40):
                dx_d = abs(x - 59.5)
                arch_z = 31.0 + math.sqrt(max(0.0, 36.0 - dx_d * dx_d))
                if z <= arch_z:
                    if dx_d <= 4.5 and z <= arch_z - 1.5:
                        if y >= 15:
                            grid[x, y, z] = WOOD_DARK if (z % 5 != 0 and x != 59) else IRON_DARK
                        else:
                            grid[x, y, z] = 0
                    elif dx_d <= 6.5 and y <= 17:
                        grid[x, y, z] = WHITE_MARBLE

    # Royal French / Marseille coat-of-arms plaque above door (z=42..52)
    for x in range(55, 65):
        for z in range(42, 52):
            for y in range(18, 23):
                if grid[x, y, z] > 0:
                    if x in (55, 64) or z in (42, 51) or x in (59, 60) or z == 46:
                        grid[x, y, z] = WHITE_MARBLE
                    else:
                        grid[x, y, z] = GLASS_PANE  # azure & white cross of Marseille

    # Arched windows at z=85 and z=190
    for z_base in (85, 190):
        for w in range(56, 64):
            for d in range(34, 41):
                for dz in range(0, 18):
                    z = z_base + dz
                    dw = abs(w - 59.5)
                    if dz <= 12 + math.sqrt(max(0.0, 12.25 - dw * dw)):
                        val = IRON_DARK if dw <= 1.5 else WHITE_MARBLE
                        grid[w, int(59.5 - d), z] = val
                        grid[w, int(59.5 + d), z] = val
                        grid[int(59.5 - d), w, z] = val
                        grid[int(59.5 + d), w, z] = val

    anchors = {
        "lot-0": [0, 0, 0],
        "door": [59, 13, 16],
        "work-a1": [59, 22, 257],
        "wick": [59, 59, 282],
        "beam-to": [59, 5, 279],
    }
    return grid, anchors


def build_cadiz_san_sebastian():
    """
    4. Torre-Atalaya de San Sebastián (Cádiz, 1613-1617) — 160 x 160 x 260 (16m x 16m x 26m)
    - Built by Juan de la Fuente Hurtado in 1613 on the rocky Atlantic reef of La Caleta.
    - z=0..16: Atlantic reef plinth & stepped circular masonry apron (R = 68 -> 62)
    - z=16..168: Truncated-conical (troncocónico) fortified watchtower of warm golden-brown
      piedra ostionera (R = 61 at z=16 tapering to R = 49 at z=168)
    - Exterior arched stone stair-ramp on the -y face leading up to the raised entrance portal at z=24
    - z=156..164: Heavy stone torus molding (cordón magistral)
    - z=164..184: Circular gun & watch parapet terrace (R = 51) with 8 cannon embrasures & iron barrels
    - z=174..252: Octagonal/cylindrical glazed lantern tower in the center of the terrace (R = 21)
      with glowing beacon fire at z=202..222 (wick=[79,79,212], beam-to=[79,5,209]),
      topped by a golden-ochre & glazed-tile Spanish hemispherical cupola + cross finial.
    """
    nx, ny, nz = 160, 160, 260
    grid = np.zeros((nx, ny, nz), dtype=np.uint8)
    cx, cy = 79.5, 79.5

    for x in range(nx):
        dx = x - cx
        for y in range(ny):
            dy = y - cy
            r = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)

            # 1) z=0..16: Stepped piedra ostionera reef plinth (R = 68 -> 62)
            for z in range(0, 17):
                lim = 67.0 - (z // 4) * 1.5
                if r <= lim:
                    if z < 4 or r >= lim - 2.0:
                        grid[x, y, z] = OSTIONERA_DARK if (x + y + z) % 2 == 0 else STONE_DEEP
                    else:
                        grid[x, y, z] = stone_tex(x, y, z, OSTIONERA_LIGHT, OSTIONERA_MID, OSTIONERA_DARK)

            # Exterior masonry stair-bridge at -y (x=70..89, y=4..22, z=0..24) with arch underneath
            if 70 <= x <= 89 and 4 <= y <= 22:
                sh = max(0, min(24, int((y - 4) * 1.4)))
                for z in range(0, sh + 1):
                    # Small relieving arch under the stair bridge at y=12..18, z=4..12
                    if 12 <= y <= 18 and 73 <= x <= 86 and z <= 10 - abs(y - 15) * 1.5:
                        continue
                    if x in (70, 71, 88, 89) and z >= sh - 3:
                        grid[x, y, z] = OSTIONERA_LIGHT  # stair parapet
                    else:
                        grid[x, y, z] = OSTIONERA_DARK if z % 2 == 0 else OSTIONERA_MID

            # 2) z=16..168: Truncated-conical shaft (R = 61 -> 49) of golden-brown piedra ostionera
            if r <= 62.0:
                for z in range(16, 169):
                    t = (z - 16) / 152.0
                    r_cone = 61.0 - 12.0 * t
                    # Cordón magistral (projecting half-round stone torus) at z=156..162
                    if 156 <= z <= 162:
                        r_cone += 2.2 - abs(z - 159) * 0.5
                    if r <= r_cone:
                        if 156 <= z <= 162 and r >= r_cone - 2.5:
                            grid[x, y, z] = OSTIONERA_LIGHT
                        else:
                            grid[x, y, z] = stone_tex(x, y, z, OSTIONERA_LIGHT, OSTIONERA_MID, OSTIONERA_DARK)

                # 3) z=168..184: Fortified parapet terrace (R = 50.5) with 8 cannon embrasures
                sector8 = ((ang + math.pi) / (2.0 * math.pi) * 8.0) % 1.0
                is_merlon = (sector8 < 0.36 or sector8 > 0.64)
                for z in range(168, 185):
                    if z <= 173:
                        if r <= 50.5:
                            grid[x, y, z] = OSTIONERA_LIGHT if r >= 48.5 else OSTIONERA_MID
                    else:
                        if r <= 23.0:
                            grid[x, y, z] = stone_tex(x, y, z, OSTIONERA_LIGHT, OSTIONERA_MID, OSTIONERA_DARK)
                        elif 45.0 <= r <= 50.5:
                            if is_merlon or z <= 176:
                                grid[x, y, z] = OSTIONERA_LIGHT if z >= 183 else OSTIONERA_MID

                # 4) z=174..254: Domed lantern turret in center of terrace (R = 22)
                is_rib = (sector8 < 0.24 or sector8 > 0.76)
                for z in range(174, 255):
                    if z <= 194:
                        # Octagonal/cylindrical stone drum base of lantern
                        if r <= 22.0:
                            grid[x, y, z] = OSTIONERA_LIGHT if (is_rib or z in (193, 194)) else OSTIONERA_MID
                    elif z <= 224:
                        # Glazed lantern chamber (z=195..224) with glowing beacon fire at z=202..220
                        if r <= 9.5:
                            if z < 200:
                                grid[x, y, z] = IRON_DARK
                            elif z <= 220 and r <= 7.5 - abs(z - 210) * 0.35:
                                grid[x, y, z] = FIRE_CORE if r <= 4.0 else FIRE_GLOW
                        elif 17.5 <= r <= 21.5:
                            if is_rib or z in (195, 196, 210, 223, 224):
                                grid[x, y, z] = BRASS_FRAME if r >= 19.5 else OSTIONERA_LIGHT
                            else:
                                grid[x, y, z] = GLASS_PANE
                    elif z <= 245:
                        # Spanish hemispherical cupola (z=225..245) with golden-ochre & red ribs
                        t_d = (z - 225) / 20.0
                        dome_r = 21.5 * math.sqrt(max(0.0, 1.0 - t_d * t_d))
                        if r <= dome_r:
                            grid[x, y, z] = RED_CREST if is_rib else OSTIONERA_LIGHT
                    else:
                        if r <= 2.4 or (z == 251 and abs(dx) <= 4.5 and abs(dy) <= 1.5):
                            grid[x, y, z] = BRASS_FRAME

    # Raised arched entrance portal at -y (x=73..86, y=17..28, z=24..46)
    for x in range(72, 88):
        for y in range(17, 29):
            for z in range(24, 48):
                dx_d = abs(x - 79.5)
                arch_z = 39.0 + math.sqrt(max(0.0, 36.0 - dx_d * dx_d))
                if z <= arch_z:
                    if dx_d <= 4.5 and z <= arch_z - 1.5:
                        if y >= 22:
                            grid[x, y, z] = WOOD_DARK if (z % 5 != 0 and x != 79) else IRON_DARK
                        else:
                            grid[x, y, z] = 0
                    elif dx_d <= 6.5 and y <= 24:
                        grid[x, y, z] = WHITE_MARBLE

    # Spanish Habsburg royal coat-of-arms plaque above portal (z=49..59)
    for x in range(74, 86):
        for z in range(49, 60):
            for y in range(19, 25):
                if grid[x, y, z] > 0:
                    if x in (74, 85) or z in (49, 59):
                        grid[x, y, z] = WHITE_MARBLE
                    elif (x + z) % 3 == 0:
                        grid[x, y, z] = RED_CREST
                    else:
                        grid[x, y, z] = OSTIONERA_LIGHT

    # 4 cardinal watch slits on the conical tower (z=85..105, z=125..142)
    for z_base, r_mid in [(85, 55), (125, 52)]:
        for w in range(77, 83):
            for d in range(r_mid - 4, r_mid + 4):
                for dz in range(0, 16):
                    z = z_base + dz
                    dw = abs(w - 79.5)
                    if dz <= 13:
                        val = IRON_DARK if dw <= 1.0 else OSTIONERA_LIGHT
                        grid[w, int(79.5 - d), z] = val
                        grid[w, int(79.5 + d), z] = val
                        grid[int(79.5 - d), w, z] = val
                        grid[int(79.5 + d), w, z] = val

    anchors = {
        "lot-0": [0, 0, 0],
        "door": [79, 20, 24],
        "work-a1": [79, 32, 174],
        "wick": [79, 79, 212],
        "beam-to": [79, 5, 209],
    }
    return grid, anchors


def main():
    specs = [
        (
            "calli-lighthouses-01m-livorno-fanale",
            "120,120,420",
            "利佛諾燈塔（Fanale di Livorno，1303）",
            "14th-century Pisan/Medici 13-sided polygonal stepped stone base and twin machicolated cylindrical lighthouse drums (0.1m/vox)",
            "building,livorno",
            build_livorno_fanale,
        ),
        (
            "calli-lighthouses-01m-larochelle-lanterne",
            "160,160,480",
            "拉羅歇爾燈塔塔（Tour de la Lanterne，1468）",
            "15th-century Flamboyant Gothic cylindrical limestone fortress-lighthouse with crocketed octagonal stone spire and engaged seaward lantern turret (0.1m/vox)",
            "building,larochelle",
            build_larochelle_lanterne,
        ),
        (
            "calli-lighthouses-01m-marseille-fanal",
            "120,120,320",
            "馬賽聖約翰燈塔塔（Tour du Fanal，1644）",
            "1644 Provençal square-plinth cylindrical harbour beacon tower with mid-shaft faux-mâchicoulis cordon and domed stone lantern (0.1m/vox)",
            "building,marseille",
            build_marseille_fanal,
        ),
        (
            "calli-lighthouses-01m-cadiz-san-sebastian",
            "160,160,260",
            "加的斯聖塞巴斯蒂安燈塔塔（Torre de San Sebastián，1613）",
            "1613 Spanish Atlantic truncated-conical piedra ostionera watchtower and harbour lighthouse with cordón magistral and domed lantern (0.1m/vox)",
            "building,cadiz",
            build_cadiz_san_sebastian,
        ),
    ]

    for sub_id, size_str, title, style, tags, builder in specs:
        ensure_subwork(sub_id, size_str, title, style, tags)
        grid, anchors = builder()
        save_and_stamp(sub_id, grid, anchors)

    print("All 4 lighthouses built and stamped successfully!")


if __name__ == "__main__":
    main()
