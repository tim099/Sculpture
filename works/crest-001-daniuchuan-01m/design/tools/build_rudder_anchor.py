"""步驟 11 落格：切舵柄孔、建立升降舵／舵柄／貓頭錨架、掛 2× 四爪錨與錨索"""

from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(DESIGN)))
OUT_DIR = os.path.join(DESIGN, "masks", "rudder_anchor")
sys.path.insert(0, HERE)
sys.path.insert(0, DESIGN)
from wio import cli, export_list, PERSONA, HULL, ASM  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

BAL_ID = f"{HULL}-stern-balcony"
POOP_ID = f"{HULL}-deck-poop"


def ensure_subwork(work_id: str, title: str, size: str = "512,256,512") -> bool:
    created = not os.path.exists(os.path.join(WORKS, work_id, "work.json"))
    if created:
        cli("op=work", "sub=create", f"persona={PERSONA}", f"work={work_id}",
            f"title={title}", f"parent_work={HULL}", f"size={size}", "tags=sub")
    cli("op=work", "sub=update", f"persona={PERSONA}", f"work={work_id}",
        "tags=sub", "meters_per_voxel=0.1")
    return created


def load_vox_map(path: str) -> dict[tuple[int, int, int], int]:
    res = {}
    with open(path, encoding="utf-8") as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            x, y, z, c = (int(v) for v in s.split(","))
            res[(x, y, z)] = c
    return res


def guarded_carve(work_id: str, path: str, tag: str) -> int:
    target = load_vox_map(path)
    cur_arr = export_list(work_id, links="none")
    cur = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in cur_arr} if cur_arr.size else {}
    pending = [f"{x},{y},{z},{c}" for (x, y, z), c in sorted(target.items()) if cur.get((x, y, z)) == c]
    if not pending:
        print(f"[carve] {work_id} ({tag}): 0 pending (already carved)")
        return 0
    tmp = os.path.join(OUT_DIR, f"_{tag}_pending.vox.txt")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(pending) + "\n")
    cli("op=carvevox", f"persona={PERSONA}", f"work={work_id}",
        "voxels=" + os.path.abspath(tmp).replace("\\", "/"),
        "at=0,0,0", f"expect_pixels={len(pending)}", "share=0")
    print(f"  carvevox {work_id} ({tag}): {len(pending)}")
    return len(pending)


def sync_work_voxels(work_id: str, title: str, path: str, tag: str) -> None:
    ensure_subwork(work_id, title)
    target = load_vox_map(path)
    cur_arr = export_list(work_id, links="none")
    cur = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in cur_arr} if cur_arr.size else {}

    stale = [f"{x},{y},{z},{c}" for (x, y, z), c in sorted(cur.items()) if target.get((x, y, z)) != c]
    if stale:
        ctmp = os.path.join(OUT_DIR, f"_{tag}_carve.vox.txt")
        with open(ctmp, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(stale) + "\n")
        cli("op=carvevox", f"persona={PERSONA}", f"work={work_id}",
            "voxels=" + os.path.abspath(ctmp).replace("\\", "/"),
            "at=0,0,0", f"expect_pixels={len(stale)}", "share=0")

    add = [f"{x},{y},{z},{c}" for (x, y, z), c in sorted(target.items()) if cur.get((x, y, z)) != c]
    if add:
        stmp = os.path.join(OUT_DIR, f"_{tag}_stamp.vox.txt")
        with open(stmp, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(add) + "\n")
        out = cli("op=stampvox", f"persona={PERSONA}", f"work={work_id}",
                  "voxels=" + os.path.abspath(stmp).replace("\\", "/"),
                  "at=0,0,0", f"expect_pixels={len(add)}", "draft=0", "share=0")
        m = re.search(r"placed\D{0,12}(\d[\d,]*)", out)
        got = int(m.group(1).replace(",", "")) if m else None
        assert got == len(add), f"stamp {work_id}: got {got} != {len(add)}"
        print(f"  stampvox {work_id}: +{len(add)} (total={len(target)})")
    else:
        print(f"  sync {work_id}: already matches {len(target)} voxels")


def upsert_anchor(work_id: str, name: str, at: list[int], note: str) -> None:
    cli("op=work", "sub=unanchor", f"persona={PERSONA}", f"work={work_id}", f"name={name}", ok=(0, 2))
    cli("op=work", "sub=anchor", f"persona={PERSONA}", f"work={work_id}", f"name={name}",
        f"at={at[0]},{at[1]},{at[2]}", f"note={note}")


def upsert_model(
    work_id: str,
    name: str,
    source_work: str,
    at: str,
    pivot: str,
    meta: dict,
    rotate: str = "0,0,0",
    scale: str = "1",
    note: str = "",
) -> None:
    cli("op=work", "sub=unmodel", f"persona={PERSONA}", f"work={work_id}", f"name={name}", ok=(0, 2))
    cli("op=work", "sub=model", f"persona={PERSONA}", f"work={work_id}",
        f"name={name}", f"source_work={source_work}",
        f"at={at}", f"pivot={pivot}", f"rotate={rotate}", f"scale={scale}",
        "meta=" + json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
        f"note={note}")


def upsert_rope(name: str, ep_from: str, ep_to: str, slack: float, group: str, note: str) -> None:
    cli("op=work", "sub=unrope", f"persona={PERSONA}", f"work={ASM}", f"name={name}", ok=(0, 2))
    cli("op=work", "sub=rope", f"persona={PERSONA}", f"work={ASM}",
        f"name={name}", f"from={ep_from}", f"to={ep_to}",
        f"slack={slack:g}", "thickness=0.85", "color=#3b3228", f"group={group}",
        f"note={note}")
    cli("op=work", "sub=meta", f"persona={PERSONA}", f"work={ASM}",
        "part=rope", f"name={name}", 'meta={"kind":"rigging"}')


def main() -> int:
    cfg = json.load(open(os.path.join(DESIGN, "plan.json"), encoding="utf-8"))["rudder_anchor_build"]
    rcfg, tcfg, gcfg, acfg = cfg["rudder"], cfg["tiller"], cfg["anchor_gear"], cfg["anchors"]

    # 1. Cut tiller helm-port slots on stern balcony & transom hull
    guarded_carve(BAL_ID, os.path.join(OUT_DIR, "carve_balcony.vox.txt"), "carve_balcony")
    guarded_carve(HULL, os.path.join(OUT_DIR, "carve_hull.vox.txt"), "carve_hull")

    # 2. Subworks: rudder, tiller, anchor_gear
    sync_work_voxels(rcfg["work"], rcfg["title"], os.path.join(OUT_DIR, "rudder.vox.txt"), "rudder")
    upsert_anchor(rcfg["work"], "stock-top", rcfg["stock_top"], "步驟 11：舵頭 stock-top（Ship_Helm / Ship_Game §9）")

    sync_work_voxels(tcfg["work"], tcfg["title"], os.path.join(OUT_DIR, "tiller.vox.txt"), "tiller")
    upsert_anchor(tcfg["work"], "spin-a", tcfg["spin_a"], "步驟 11：舵柄轉軸 spin-a → spin-b")
    upsert_anchor(tcfg["work"], "spin-b", tcfg["spin_b"], "步驟 11：舵柄轉軸 spin-a → spin-b")

    sync_work_voxels(gcfg["work"], gcfg["title"], os.path.join(OUT_DIR, "anchor_gear.vox.txt"), "anchor_gear")

    # 3. Link 錨架 into assembly
    cli("op=work", "sub=unlink", f"persona={PERSONA}", f"work={ASM}", "name=錨架", ok=(0, 2))
    cli("op=work", "sub=link", f"persona={PERSONA}", f"work={ASM}",
        "name=錨架", f"source_work={gcfg['work']}", "at=0,0,0",
        "note=步驟 11：雙舷貓頭錨架與將軍柱墊木")

    # 4. Hull hawse hole anchors
    upsert_anchor(HULL, "hawse-S", acfg["hawse_s"], "步驟 11：右舷錨鏈孔 hawse-S")
    upsert_anchor(HULL, "hawse-P", acfg["hawse_p"], "步驟 11：左舷錨鏈孔 hawse-P")

    # 5. Mount 舵, 舵柄 (tiller), and 2× 錨 (anchor + material=iron)
    hx = rcfg["x_stock"] + 0.5
    hy = rcfg["y_mid"] + 0.5
    hz = 1.0
    pivot_str = f"{hx},{hy},{hz}"
    upsert_model(
        ASM, "舵", rcfg["work"], at=pivot_str, pivot=pivot_str,
        meta={
            "kind": "rudder",
            "turn_axis": "hinge",
            "hinge_x": hx, "hinge_y": hy, "hinge_z": hz,
            "axis_x": 0.0, "axis_y": 0.0, "axis_z": 1.0,
            "max_deg": rcfg["max_deg"],
            "spin": rcfg["spin"],
            "spin_k": rcfg["max_deg"],
            "spin_min": -rcfg["max_deg"],
            "spin_max": rcfg["max_deg"],
            "spin_lag": rcfg["spin_lag"],
        },
        note="步驟 11：明鄭大鳥船中式開孔升降舵",
    )
    upsert_model(
        POOP_ID, "舵柄", tcfg["work"], at=pivot_str, pivot=pivot_str,
        meta={
            "kind": "tiller",
            "spin": rcfg["spin"],
            "spin_k": rcfg["max_deg"],
            "spin_min": -rcfg["max_deg"],
            "spin_max": rcfg["max_deg"],
            "spin_lag": rcfg["spin_lag"],
        },
        note="步驟 11：獨立舵柄模型（與舵連動）",
    )

    apiv = f"{acfg['pivot'][0]},{acfg['pivot'][1]},{acfg['pivot'][2]}"
    y_cen = float(acfg["y_center"])
    ay_s = y_cen + acfg["y_off"]
    ay_p = y_cen - acfg["y_off"]
    ameta = {"kind": acfg["kind"], "anchor": acfg["anchor"], "material": "iron"}
    upsert_model(
        gcfg["work"], "錨-S", acfg["source"],
        at=f"{acfg['x']},{ay_s},{acfg['z']}", pivot=apiv,
        rotate=f"0,0,{acfg['yaw_s']}", scale=str(acfg["scale"]),
        meta=ameta, note="步驟 11：右舷四爪鐵錨（iron）",
    )
    upsert_model(
        gcfg["work"], "錨-P", acfg["source"],
        at=f"{acfg['x']},{ay_p},{acfg['z']}", pivot=apiv,
        rotate=f"0,0,-{acfg['yaw_s']}", scale=str(acfg["scale"]),
        meta=ameta, note="步驟 11：左舷四爪鐵錨（iron）",
    )

    # 6. Bower anchor cables (hawse -> anchor ring)
    upsert_rope("anchor-cable-S", "船殼/hawse-S", "model:錨架/錨-S/ring", 1.06, "running/anchor", "步驟 11：右舷錨索")
    upsert_rope("anchor-cable-P", "船殼/hawse-P", "model:錨架/錨-P/ring", 1.06, "running/anchor", "步驟 11：左舷錨索")

    print("✓ Step 11 build_rudder_anchor DONE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
