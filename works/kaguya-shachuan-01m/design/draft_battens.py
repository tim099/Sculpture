"""Upgrade kaguya-shachuan-01m to fanned canted + curved-roach physical batten sails (TASK-1321)."""
import argparse
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

WORKS = Path(r"D:\Unity\Valhalla\Sculpture\works")
HULL = "kaguya-shachuan-01m"
DESIGN = WORKS / HULL / "design"
ASSEMBLY = f"{HULL}-assembly"
CY = 96.5

SPECS = {
    "fore": {
        "mast_work": f"{HULL}-mast-fore",
        "heel": (222.5, 96.5, 6.5),
        "head": (233.5, 96.5, 128.5),
        "gaff": {"work": f"{HULL}-yard-fore-gaff", "aft_len": 41, "fore_len": 13, "z": 116.5, "angle_deg": -18.0, "dia": 6.0},
        "boom": {"work": f"{HULL}-yard-fore-boom", "aft_len": 42, "fore_len": 14, "z": 46.5, "angle_deg": 0.0, "dia": 6.0},
        "battens": 6,
        "roach": (0.05, 0.16),
        "res": 28,
        "set": 1,
    },
    "main": {
        "mast_work": f"{HULL}-mast-main",
        "heel": (150.5, 96.5, 3.5),
        "head": (150.5, 96.5, 173.5),
        "gaff": {"work": f"{HULL}-yard-main-gaff", "aft_len": 59, "fore_len": 19, "z": 158.5, "angle_deg": -17.0, "dia": 8.0},
        "boom": {"work": f"{HULL}-yard-main-boom", "aft_len": 62, "fore_len": 20, "z": 54.5, "angle_deg": 0.0, "dia": 8.0},
        "battens": 8,
        "roach": (0.05, 0.16),
        "res": 36,
        "set": 2,
    },
    "mizzen": {
        "mast_work": f"{HULL}-mast-mizzen",
        "heel": (56.5, 96.5, 23.5),
        "head": (53.5, 96.5, 111.5),
        "gaff": {"work": f"{HULL}-yard-mizzen-gaff", "aft_len": 30, "fore_len": 10, "z": 100.5, "angle_deg": -16.0, "dia": 6.0},
        "boom": {"work": f"{HULL}-yard-mizzen-boom", "aft_len": 32, "fore_len": 10, "z": 56.5, "angle_deg": 0.0, "dia": 6.0},
        "battens": 4,
        "roach": (0.05, 0.16),
        "res": 20,
        "set": 3,
    },
}


def run_cli(senate_exe, op, **args):
    cmd = [senate_exe, "cmd", "sculpture", "--arg", f"op={op}", "--arg", "persona=kaguya"]
    for k, v in args.items():
        if isinstance(v, dict):
            v = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
        elif isinstance(v, (tuple, list)):
            v = ",".join(str(x) for x in v)
        cmd.extend(("--arg", f"{k}={v}"))
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"Command failed ({r.returncode}): {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def mast_x_at_z(spec, z):
    hx0, _, hz0 = spec["heel"]
    hx1, _, hz1 = spec["head"]
    return hx0 + (z - hz0) / (hz1 - hz0) * (hx1 - hx0)


def sync_voxels(senate_exe, work, desired_cells, work_title, parent_work, size_xyz, draft):
    folder = WORKS / work
    created = False
    if not (folder / "work.json").exists():
        run_cli(senate_exe, "work", sub="create", id=work, title=work_title, size=size_xyz, parent_work=parent_work, tags="sub")
        created = True
    wjson = json.loads((folder / "work.json").read_text(encoding="utf-8-sig"))
    cur_sz = (wjson.get("size_x") or wjson.get("size"), wjson.get("size_y") or wjson.get("size"), wjson.get("size_z") or wjson.get("size"))
    if not created and any(size_xyz[i] > cur_sz[i] for i in range(3)):
        big_sz = tuple(max(size_xyz[i], cur_sz[i]) for i in range(3))
        run_cli(senate_exe, "work", sub="update", work=work, size=big_sz)
    if abs((wjson.get("meters_per_voxel") or 0) - 0.1) > 1e-6:
        run_cli(senate_exe, "work", sub="update", work=work, meters_per_voxel=0.1)

    with tempfile.TemporaryDirectory() as td:
        cur_path = Path(td) / "cur.txt"
        current = {}
        if any((folder / "events").rglob("*.json")):
            run_cli(senate_exe, "export", work=work, format="list", out=str(cur_path).replace("\\", "/"), links="none")
            for line in cur_path.read_text(encoding="utf-8-sig").splitlines():
                if line[:1].isdigit():
                    x, y, z, c = map(int, line.split(","))
                    current[(x, y, z)] = c
        extra = {p: c for p, c in current.items() if p not in desired_cells or desired_cells[p] != c}
        missing = {p: c for p, c in desired_cells.items() if p not in current or current[p] != c}
        for subop, cells, fname in (("carvevox", extra, "rm.txt"), ("stampvox", missing, "add.txt")):
            if cells:
                f = Path(td) / fname
                f.write_text("".join(f"{x},{y},{z},{c}\n" for (x, y, z), c in sorted(cells.items())), encoding="ascii")
                out = run_cli(senate_exe, subop, work=work, voxels=str(f).replace("\\", "/"), at=(0, 0, 0), expect_pixels=len(cells), note=draft, share=0)
                m = re.search(r"placed\s*=\s*(\d+)", out)
                if m is None or int(m.group(1)) != len(cells):
                    raise RuntimeError(f"Voxel sync mismatch on {work} ({subop}): {out}")
    wjson2 = json.loads((folder / "work.json").read_text(encoding="utf-8-sig"))
    cur_sz2 = (wjson2.get("size_x") or wjson2.get("size"), wjson2.get("size_y") or wjson2.get("size"), wjson2.get("size_z") or wjson2.get("size"))
    if cur_sz2 != size_xyz:
        run_cli(senate_exe, "work", sub="update", work=work, size=size_xyz)


def set_anchor(senate_exe, work, name, pt):
    run_cli(senate_exe, "work", sub="anchor", work=work, name=name, at=pt, overwrite=1)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def make_sail_texture(name, battens):
    tex_dir = DESIGN / "textures"
    tex_dir.mkdir(parents=True, exist_ok=True)
    h = (battens + 1) * 12
    im = Image.new("RGB", (128, h), "#dbc498")
    d = ImageDraw.Draw(im)
    # Vertical stitched linen/hemp cloth bands
    for x in range(0, 128, 16):
        d.rectangle((x, 0, min(127, x + 7), h - 1), fill="#e2cca2")
        d.rectangle((min(127, x + 8), 0, min(127, x + 15), h - 1), fill="#d4bc8f")
    for x in range(0, 128, 16):
        d.line((x, 0, x, h - 1), fill="#c2a778", width=1)
    # Soft panel vertical weathering
    for y in range(h):
        in_panel = y % 12
        if in_panel <= 2 or in_panel >= 10:
            d.line((0, y, 127, y), fill="#bfa372")
    # Crisp dark bamboo batten seam bands at exact m * 12 rows
    for m in range(1, battens + 1):
        y = m * 12
        d.line((0, y - 1, 127, y - 1), fill="#735b3b", width=1)
        d.line((0, y, 127, y), fill="#5e492e", width=1)
    d.rectangle((0, 0, 127, h - 1), outline="#644e32", width=2)
    path = tex_dir / f"{name}-battens.png"
    im.save(path)
    return str(path).replace("\\", "/")


def update_plan():
    p_path = DESIGN / "plan.json"
    plan = json.loads(p_path.read_text(encoding="utf-8"))
    m = plan["masts"]
    m["_src"] = (
        "〔設計〕參考《天工開物》與多桅沙船／現代中華傳統紅篷帆船資料，三桅均採中式扇形硬骨竹篾帆："
        "下桁 0°→頂桁上揚 −16°～−18°、外緣帶弓形弧線（roach=0.05,0.16），各列附實體竹篾桿（yard=batten）"
    )
    for mk, sp in SPECS.items():
        g, b = sp["gaff"], sp["boom"]
        g_len = g["aft_len"] + g["fore_len"]
        b_len = b["aft_len"] + b["fore_len"]
        m["yards"][f"{mk}_gaff"] = {
            "len": g_len, "fore_len": g["fore_len"], "aft_len": g["aft_len"],
            "on": mk, "z": g["z"], "angle_deg": g["angle_deg"], "kind": "course",
            "src": f"〔設計〕{mk} 上桁 {g_len/10:.1f} m（前低後昂 {g['angle_deg']}°，yard=course）",
        }
        m["yards"][f"{mk}_boom"] = {
            "len": b_len, "fore_len": b["fore_len"], "aft_len": b["aft_len"],
            "on": mk, "z": b["z"], "angle_deg": 0, "kind": "course",
            "src": f"〔設計〕{mk} 下桁 {b_len/10:.1f} m（yard=course，清甲板與尾樓淨空）",
        }
        m.setdefault("battens_spec", {})[mk] = {
            "count": sp["battens"], "roach": f"{sp['roach'][0]},{sp['roach'][1]}", "res": sp["res"]
        }
    p_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--senate", default="senate")
    ap.add_argument("--meta-senate", default="")
    args = ap.parse_args()
    sen = args.senate
    meta_sen = args.meta_senate or sen

    update_plan()
    placements = []
    meta_rows = []

    for mk, sp in SPECS.items():
        g = sp["gaff"]
        b = sp["boom"]
        mast_work = sp["mast_work"]

        # 1. Straight horizontal upper gaff spar rotated via model rotate_y = -angle_deg (>0 lifts aft)
        g_len = g["aft_len"] + g["fore_len"]
        g_aft = g["aft_len"]
        g_cells = {}
        mid0 = max(2, 2 + g_aft - g_len // 4)
        mid1 = min(2 + g_len, 2 + g_aft + g_len // 5)
        for x in range(2, 2 + g_len + 1):
            g_cells[(x, 1, 2)] = 141
            if mid0 <= x <= mid1:
                g_cells[(x, 2, 2)] = 141
        sync_voxels(sen, g["work"], g_cells, f"沙船 上桁 {mk}_gaff（0.1 m）", HULL, (g_len + 5, 5, 5), f"hard_batten_{mk}_gaff")
        set_anchor(sen, g["work"], "pivot", (2 + g_aft, 2, 2))
        set_anchor(sen, g["work"], "aft", (2, 1, 2))
        set_anchor(sen, g["work"], "fore", (2 + g_len, 1, 2))
        set_anchor(sen, g["work"], "sling", (2 + g_aft, 1, 2))

        gx = round(mast_x_at_z(sp, g["z"]), 3)
        ry_top = round(-g["angle_deg"], 3)
        run_cli(
            sen, "work", sub="model", work=mast_work, name=f"yard-{mk}-gaff",
            source_work=g["work"], at=(gx, CY, g["z"]), pivot=(2 + g_aft + 0.5, 2.5, 2.5),
            rotate=(0, ry_top, 0), scale=(1, 1, 1),
            meta={
                "kind": "yard", "yard": "course", "mast": mk, "sail": f"{mk}-junk",
                "pivot_anchor": "pivot", "rotate_z_deg": 0, "turn_axis": "z",
                "diameter_in": g["dia"], "length_ft": round(g_len * 0.3281, 2),
            },
            overwrite=1,
        )

        # Ensure lower boom yard uses yard=course cleanly
        b_len = b["aft_len"] + b["fore_len"]
        bx = round(mast_x_at_z(sp, b["z"]), 3)
        run_cli(
            sen, "work", sub="model", work=mast_work, name=f"yard-{mk}-boom",
            source_work=b["work"], at=(bx, CY, b["z"]), pivot=(2 + b["aft_len"] + 0.5, 2.5, 2.5),
            rotate=(0, 0, 0), scale=(1, 1, 1),
            meta={
                "kind": "yard", "yard": "course", "mast": mk, "sail": f"{mk}-junk",
                "pivot_anchor": "pivot", "rotate_z_deg": 0, "turn_axis": "z",
                "diameter_in": b["dia"], "length_ft": round(b_len * 0.3281, 2),
            },
            overwrite=1,
        )

        # 2. Exact world coordinates of the 4 sail corners (on port side y = CY - 1 = 95.5)
        rad = math.radians(ry_top)
        ca, sa = math.cos(rad), math.sin(rad)
        # Sculpt Y-rotation: (dx, 0, 0) -> (dx*ca, 0, -dx*sa)
        c0 = (gx + g["fore_len"] * ca, CY - 1.0, g["z"] - g["fore_len"] * sa)   # throat (+X)
        c1 = (gx - g["aft_len"] * ca, CY - 1.0, g["z"] + g["aft_len"] * sa)     # peak   (-X)
        c2 = (bx - b["aft_len"], CY - 1.0, b["z"])                              # clew   (-X)
        c3 = (bx + b["fore_len"], CY - 1.0, b["z"])                             # tack   (+X)

        N = sp["battens"]
        r0, r1 = sp["roach"]
        hx0, _, hz0 = sp["heel"]
        hx1, _, hz1 = sp["head"]
        slope_x = (hx1 - hx0) / (hz1 - hz0)

        for m_idx in range(1, N + 1):
            v = m_idx / (N + 1)
            bulge = math.sin(math.pi * (v ** 0.85))
            uL = -bulge * r0
            uR = 1.0 + bulge * r1

            p_fore = lerp(lerp(c0, c1, uL), lerp(c3, c2, uL), v)
            p_aft = lerp(lerp(c0, c1, uR), lerp(c3, c2, uR), v)

            # Intersection of p_aft + s*(p_fore - p_aft) with mast centerline x = hx0 + slope_x*(z - hz0)
            dx = p_fore[0] - p_aft[0]
            dz = p_fore[2] - p_aft[2]
            s_int = ((hx0 - p_aft[0]) + slope_x * (p_aft[2] - hz0)) / (dx - slope_x * dz)
            piv_x = p_aft[0] + s_int * dx
            piv_z = p_aft[2] + s_int * dz

            d_aft = math.hypot(piv_x - p_aft[0], piv_z - p_aft[2])
            d_fore = math.hypot(p_fore[0] - piv_x, p_fore[2] - piv_z)
            aft_cells = int(math.ceil(d_aft + 2.5))
            fore_cells = int(math.ceil(d_fore + 2.5))
            span = aft_cells + fore_cells
            ry_bat = -math.degrees(math.atan2(dz, dx))

            bat_work = f"{HULL}-batten-{mk}-{m_idx:02d}"
            b_cells = {(x, 1, 2): 177 for x in range(2, 2 + span + 1)}
            sync_voxels(sen, bat_work, b_cells, f"沙船 竹篾 {mk}-{m_idx:02d}（0.1 m）", HULL, (span + 5, 4, 5), f"batten_{mk}_{m_idx:02d}")
            set_anchor(sen, bat_work, "pivot", (2 + aft_cells, 2, 2))
            set_anchor(sen, bat_work, "arm-P", (2, 1, 2))
            set_anchor(sen, bat_work, "arm-S", (2 + span, 1, 2))

            model_name = f"batten-{m_idx:02d}"
            run_cli(
                sen, "work", sub="model", work=mast_work, name=model_name,
                source_work=bat_work,
                at=(round(piv_x, 3), CY, round(piv_z, 3)),
                pivot=(2 + aft_cells + 0.5, 2.5, 2.5),
                rotate=(0, round(ry_bat, 3), 0),
                scale=(1, 1, 1),
                meta={
                    "kind": "yard", "yard": "batten", "mast": mk, "sail": f"{mk}-junk",
                    "batten": m_idx, "pivot_anchor": "pivot", "rotate_z_deg": 0,
                    "turn_axis": "z", "diameter_in": 4.0, "length_ft": round(span * 0.3281, 2),
                    "material": "bamboo",
                },
                overwrite=1,
            )
            placements.append({
                "mast": mk, "batten": m_idx, "work": bat_work,
                "at": [round(piv_x, 3), CY, round(piv_z, 3)],
                "rotate_y": round(ry_bat, 3),
                "aft_cells": aft_cells, "fore_cells": fore_cells,
                "row_fore": [round(q, 3) for q in p_fore],
                "row_aft": [round(q, 3) for q in p_aft],
            })

        # 3. Sail + stripes texture + roach/battens meta
        tex_path = make_sail_texture(mk, N)
        sail_name = f"{mk}-junk"
        run_cli(
            sen, "work", sub="sail", work=ASSEMBLY, name=sail_name,
            corners=f"model:桅-{mk}/yard-{mk}-gaff/fore|model:桅-{mk}/yard-{mk}-gaff/aft|model:桅-{mk}/yard-{mk}-boom/aft|model:桅-{mk}/yard-{mk}-boom/fore",
            corner_names="throat|peak|clew|tack",
            bind="0,2", color="#ffffff", fullness=1.05, res=sp["res"],
            texture=tex_path, note="步驟 8+1321：扇形弓邊硬骨竹篾帆", overwrite=1,
        )
        meta_rows.append(("sail", sail_name, {
            "kind": "sail", "mast": mk, "sail": "gaff", "set": sp["set"],
            "battens": N, "roach": f"{r0},{r1}",
        }))

    # Preserve ensign & pennant meta
    meta_rows.append(("sail", "ensign", {"kind": "flag", "flag": "ensign", "nation": "ming"}))
    meta_rows.append(("sail", "pennant", {"kind": "flag", "flag": "pennant", "mast": "main", "nation": "ming"}))

    tsv = DESIGN / "rigging_meta.tsv"
    tsv.write_text("".join(f"{p}\t{n}\t{json.dumps(m, ensure_ascii=False)}\n" for p, n, m in meta_rows), encoding="utf-8")
    run_cli(meta_sen, "work", sub="meta", work=ASSEMBLY, file=str(tsv).replace("\\", "/"))
    (DESIGN / "battens_placement.json").write_text(json.dumps(placements, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run_cli(meta_sen, "work", sub="wind", work=ASSEMBLY, wind="-4.5,-1.5,0", sail_seconds=3)
    rc = run_cli(meta_sen, "work", sub="ropecheck", work=ASSEMBLY)
    print(rc)
    print(f"Done: {len(placements)} physical battens mounted across 3 masts.")


if __name__ == "__main__":
    main()
