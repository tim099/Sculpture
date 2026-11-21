"""Apply Step 11 rudder, helm port carve, tiller, cathead anchor gear, anchors, and hawse anchors."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DESIGN_DIR = os.path.dirname(THIS_DIR)
OUT_DIR = os.path.join(DESIGN_DIR, "out")
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

import wio  # noqa: E402

PERSONA = "kotoko"
SENATE = shutil.which("senate") or "senate"
SHIP_ID = "kotoko-ganzengchuan-01m"
BAL_ID = "kotoko-ganzengchuan-01m-stern-balcony"
POOP_ID = "kotoko-ganzengchuan-01m-deck-poop"
ASM_ID = "kotoko-ganzengchuan-01m-assembly"


def sc(*args: str, allow_fail: bool = False) -> subprocess.CompletedProcess:
    cmd = [SENATE, "cmd", "sculpture", *args]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 and not allow_fail:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
    return res


def ensure_subwork(work_id: str, title: str) -> bool:
    """Create subwork if absent, ensure tags=sub and meters_per_voxel=0.1. Returns True if newly created."""
    chk = sc("--arg", "op=work", "--arg", "sub=show", "--arg", f"id={work_id}", allow_fail=True)
    created = chk.returncode != 0
    if created:
        sc(
            "--arg", "op=work",
            "--arg", "sub=create",
            "--arg", f"id={work_id}",
            "--arg", f"title={title}",
            "--arg", "size=384,192,384",
            "--arg", f"parent_work={SHIP_ID}",
            "--arg", f"persona={PERSONA}",
        )
    sc(
        "--arg", "op=work",
        "--arg", "sub=update",
        "--arg", f"id={work_id}",
        "--arg", "tags=sub",
        "--arg", "meters_per_voxel=0.1",
        "--arg", f"persona={PERSONA}",
    )
    return created


def line_count(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for ln in f if ln.strip() and not ln.strip().startswith("#"))


def guarded_carve(work_id: str, txt_path: str, tag: str) -> int:
    cur = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in wio.export_list(work_id)}
    pending = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            x, y, z, c = (int(v) for v in s.split(","))
            if cur.get((x, y, z)) == c:
                pending.append(f"{x},{y},{z},{c}")
    if not pending:
        print(f"[carve] {work_id} ({tag}): already carved (0 pending)")
        return 0
    tmp = os.path.join(OUT_DIR, f"{tag}_pending.txt")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(pending) + "\n")
    sc(
        "--arg", "op=carvevox",
        "--arg", f"work={work_id}",
        "--arg", f"voxels={tmp}",
        "--arg", "at=0,0,0",
        "--arg", f"expect_pixels={len(pending)}",
        "--arg", f"persona={PERSONA}",
        "--arg", "share=0",
    )
    print(f"[carve] {work_id} ({tag}): carved {len(pending)} voxels")
    return len(pending)


def sync_work_voxels(work_id: str, title: str, txt_path: str, tag: str) -> None:
    ensure_subwork(work_id, title)
    cur = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in wio.export_list(work_id)}
    target = {}
    with open(txt_path, "r", encoding="utf-8") as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            x, y, z, c = (int(v) for v in s.split(","))
            target[(x, y, z)] = c

    to_carve = [f"{x},{y},{z},{c}" for (x, y, z), c in sorted(cur.items()) if target.get((x, y, z)) != c]
    if to_carve:
        ctmp = os.path.join(OUT_DIR, f"{tag}_carve.txt")
        with open(ctmp, "w", encoding="utf-8") as f:
            f.write("\n".join(to_carve) + "\n")
        sc(
            "--arg", "op=carvevox",
            "--arg", f"work={work_id}",
            "--arg", f"voxels={ctmp}",
            "--arg", "at=0,0,0",
            "--arg", f"expect_pixels={len(to_carve)}",
            "--arg", f"persona={PERSONA}",
            "--arg", "share=0",
        )
        print(f"[sync] {work_id}: carved {len(to_carve)} stale voxels")

    to_stamp = [
        f"{x},{y},{z},{c}"
        for (x, y, z), c in sorted(target.items())
        if cur.get((x, y, z)) != c
    ]
    if to_stamp:
        stmp = os.path.join(OUT_DIR, f"{tag}_stamp.txt")
        with open(stmp, "w", encoding="utf-8") as f:
            f.write("\n".join(to_stamp) + "\n")
        sc(
            "--arg", "op=stampvox",
            "--arg", f"work={work_id}",
            "--arg", f"voxels={stmp}",
            "--arg", "at=0,0,0",
            "--arg", f"expect_pixels={len(to_stamp)}",
            "--arg", f"persona={PERSONA}",
            "--arg", "share=0",
        )
        print(f"[sync] {work_id}: stamped {len(to_stamp)} voxels (total={len(target)})")
    elif not to_carve:
        print(f"[sync] {work_id}: already matches {len(target)} voxels")


def upsert_anchor(work_id: str, name: str, at: list[int], note: str) -> None:
    sc(
        "--arg", "op=work",
        "--arg", "sub=unanchor",
        "--arg", f"id={work_id}",
        "--arg", f"name={name}",
        "--arg", f"persona={PERSONA}",
        allow_fail=True,
    )
    sc(
        "--arg", "op=work",
        "--arg", "sub=anchor",
        "--arg", f"id={work_id}",
        "--arg", f"name={name}",
        "--arg", f"at={at[0]},{at[1]},{at[2]}",
        "--arg", f"note={note}",
        "--arg", f"persona={PERSONA}",
    )


def upsert_model(
    work_id: str,
    name: str,
    source_work: str,
    at: str,
    pivot: str,
    meta: dict,
    rotate: str | None = None,
    scale: str | None = None,
    note: str = "",
) -> None:
    sc(
        "--arg", "op=work",
        "--arg", "sub=unmodel",
        "--arg", f"id={work_id}",
        "--arg", f"name={name}",
        "--arg", f"persona={PERSONA}",
        allow_fail=True,
    )
    args = [
        "--arg", "op=work",
        "--arg", "sub=model",
        "--arg", f"id={work_id}",
        "--arg", f"name={name}",
        "--arg", f"source_work={source_work}",
        "--arg", f"at={at}",
        "--arg", f"pivot={pivot}",
        "--arg", f"meta={json.dumps(meta, ensure_ascii=False, separators=(',', ':'))}",
        "--arg", f"persona={PERSONA}",
    ]
    if rotate:
        args.extend(["--arg", f"rotate={rotate}"])
    if scale:
        args.extend(["--arg", f"scale={scale}"])
    if note:
        args.extend(["--arg", f"note={note}"])
    sc(*args)


def main() -> int:
    with open(os.path.join(DESIGN_DIR, "plan.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)["rudder_anchor_build"]

    rcfg = cfg["rudder"]
    tcfg = cfg["tiller"]
    gcfg = cfg["anchor_gear"]
    acfg = cfg["anchors"]

    # 1. Helm-port carves (balcony rail gate + lower stern transom slot)
    guarded_carve(BAL_ID, os.path.join(OUT_DIR, "carve_balcony.txt"), "carve_balcony")
    guarded_carve(SHIP_ID, os.path.join(OUT_DIR, "carve_hull.txt"), "carve_hull")

    # 2. Subworks: rudder, tiller, anchor_gear
    sync_work_voxels(rcfg["work"], rcfg["title"], os.path.join(OUT_DIR, "rudder.txt"), "rudder")
    upsert_anchor(rcfg["work"], "stock-top", rcfg["stock_top"], "舵頭（Ship_Game §9 rudder stock-top）")

    sync_work_voxels(tcfg["work"], tcfg["title"], os.path.join(OUT_DIR, "tiller.txt"), "tiller")
    upsert_anchor(tcfg["work"], "spin-a", tcfg["spin_a"], "舵柄繞舵軸轉（spin-a → spin-b；Ship_Helm §9.8）")
    upsert_anchor(tcfg["work"], "spin-b", tcfg["spin_b"], "舵柄繞舵軸轉（spin-a → spin-b；Ship_Helm §9.8）")

    sync_work_voxels(gcfg["work"], gcfg["title"], os.path.join(OUT_DIR, "anchor_gear.txt"), "anchor_gear")

    # 3. Link 錨架 onto assembly
    sc(
        "--arg", "op=work",
        "--arg", "sub=unlink",
        "--arg", f"id={ASM_ID}",
        "--arg", "name=錨架",
        "--arg", f"persona={PERSONA}",
        allow_fail=True,
    )
    sc(
        "--arg", "op=work",
        "--arg", "sub=link",
        "--arg", f"id={ASM_ID}",
        "--arg", "name=錨架",
        "--arg", f"source_work={gcfg['work']}",
        "--arg", "at=0,0,0",
        "--arg", "note=步驟 11（TASK-1314）：艏錨架與將軍柱",
        "--arg", f"persona={PERSONA}",
    )

    # 4. Hull hawse holes (錨鏈孔)
    upsert_anchor(SHIP_ID, "hawse-S", acfg["hawse_s"], "右舷錨鏈孔（步驟 11 TASK-1314）")
    upsert_anchor(SHIP_ID, "hawse-P", acfg["hawse_p"], "左舷錨鏈孔（步驟 11 TASK-1314）")

    # 5. Mount rudder, tiller, and port/starboard grapnel anchors
    hx = rcfg["x_stock"] + 0.5
    hy = rcfg["y_mid"] + 0.5
    hz = 1.0
    pivot_str = f"{hx},{hy},{hz}"
    upsert_model(
        ASM_ID,
        "舵",
        rcfg["work"],
        at=pivot_str,
        pivot=pivot_str,
        meta={
            "kind": "rudder",
            "turn_axis": "hinge",
            "hinge_x": hx,
            "hinge_y": hy,
            "hinge_z": hz,
            "axis_x": 0.0,
            "axis_y": 0.0,
            "axis_z": 1.0,
            "max_deg": rcfg["max_deg"],
            "spin": rcfg["spin"],
            "spin_k": rcfg["max_deg"],
            "spin_min": -rcfg["max_deg"],
            "spin_max": rcfg["max_deg"],
            "spin_lag": rcfg["spin_lag"],
        },
        note="步驟 11：中式開孔升降舵",
    )
    upsert_model(
        POOP_ID,
        "舵柄",
        tcfg["work"],
        at=pivot_str,
        pivot=pivot_str,
        meta={
            "kind": "tiller",
            "spin": rcfg["spin"],
            "spin_k": rcfg["max_deg"],
            "spin_min": -rcfg["max_deg"],
            "spin_max": rcfg["max_deg"],
            "spin_lag": rcfg["spin_lag"],
        },
        note="步驟 11：舵柄（與舵連動）",
    )

    apiv = f"{acfg['pivot'][0]},{acfg['pivot'][1]},{acfg['pivot'][2]}"
    y_cen = float(acfg.get("y_center", 96.5))
    ay_s = y_cen + acfg["y_off"]
    ay_p = y_cen - acfg["y_off"]
    ameta = {"kind": acfg["kind"], "anchor": acfg["anchor"]}
    upsert_model(
        gcfg["work"],
        "錨-S",
        acfg["source"],
        at=f"{acfg['x']},{ay_s},{acfg['z']}",
        pivot=apiv,
        rotate=f"0,0,{acfg['yaw_s']}",
        scale=str(acfg["scale"]),
        meta=ameta,
        note="步驟 11：右舷四爪鐵錨",
    )
    upsert_model(
        gcfg["work"],
        "錨-P",
        acfg["source"],
        at=f"{acfg['x']},{ay_p},{acfg['z']}",
        pivot=apiv,
        rotate=f"0,0,-{acfg['yaw_s']}",
        scale=str(acfg["scale"]),
        meta=ameta,
        note="步驟 11：左舷四爪鐵錨",
    )

    print("Step 11 build_rudder_anchor DONE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
