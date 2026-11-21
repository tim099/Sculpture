"""Apply Step 13: carve waist oar saddles, create generic oar component (render=pole), locks, and mount 4 oars."""

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
ASM_ID = "kotoko-ganzengchuan-01m-assembly"


def sc(*args: str, allow_fail: bool = False) -> subprocess.CompletedProcess:
    cmd = [SENATE, "cmd", "sculpture", *args]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 and not allow_fail:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
    return res


def ensure_subwork(work_id: str, title: str, size: str, mpv: str) -> None:
    chk = sc("--arg", "op=work", "--arg", "sub=show", "--arg", f"id={work_id}", allow_fail=True)
    if chk.returncode != 0:
        sc(
            "--arg", "op=work",
            "--arg", "sub=create",
            "--arg", f"id={work_id}",
            "--arg", f"title={title}",
            "--arg", f"size={size}",
            "--arg", f"parent_work={SHIP_ID}",
            "--arg", f"persona={PERSONA}",
        )
    sc(
        "--arg", "op=work",
        "--arg", "sub=update",
        "--arg", f"id={work_id}",
        "--arg", f"size={size}",
        "--arg", "tags=sub",
        "--arg", f"meters_per_voxel={mpv}",
        "--arg", f"persona={PERSONA}",
    )


def sync_voxels(work_id: str, txt_path: str, tag: str) -> None:
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
    to_stamp = [f"{x},{y},{z},{c}" for (x, y, z), c in sorted(target.items()) if cur.get((x, y, z)) != c]
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
    print(f"[sync] {work_id}: target={len(target)} carved={len(to_carve)} stamped={len(to_stamp)}")


def guarded_carve(work_id: str, txt_path: str, tag: str) -> None:
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
        print(f"[carve] {work_id} ({tag}): 0 pending")
        return
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
    print(f"[carve] {work_id} ({tag}): carved {len(pending)}")


def upsert_anchor(work_id: str, name: str, at: list[int], note: str) -> None:
    sc("--arg", "op=work", "--arg", "sub=unanchor", "--arg", f"id={work_id}", "--arg", f"name={name}", "--arg", f"persona={PERSONA}", allow_fail=True)
    sc("--arg", "op=work", "--arg", "sub=anchor", "--arg", f"id={work_id}", "--arg", f"name={name}", "--arg", f"at={at[0]},{at[1]},{at[2]}", "--arg", f"note={note}", "--arg", f"persona={PERSONA}")


def main() -> int:
    with open(os.path.join(DESIGN_DIR, "plan.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)["oars_build"]

    ocfg = cfg["oar"]
    lcfg = cfg["locks"]
    mcfg = cfg["meta"]

    # 1. Carve forward waist oar saddles (2 cells down on gunwale at x=244..247)
    guarded_carve(SHIP_ID, os.path.join(OUT_DIR, "carve_oar_saddles.txt"), "carve_oar_saddles")

    # 2. Generic oar subwork (0.05m, render=pole)
    sz = ocfg["size"]
    ensure_subwork(ocfg["work"], ocfg["title"], f"{sz[0]},{sz[1]},{sz[2]}", "0.05")
    sync_voxels(ocfg["work"], os.path.join(OUT_DIR, "oar.txt"), "oar")
    upsert_anchor(ocfg["work"], "pivot", ocfg["pivot"], "櫓樞：靠在舷緣櫓座旁（轉動與推力中心）")
    upsert_anchor(ocfg["work"], "blade", ocfg["blade"], "櫓葉末端（貼齊水線）")
    upsert_anchor(ocfg["work"], "seat", ocfg["seat"], "首位操櫓手站位（主甲板上 z=35）")
    sc("--arg", "op=work", "--arg", "sub=meta", "--arg", f"id={ocfg['work']}", "--arg", "part=work", "--arg", f"meta={json.dumps({'render': ocfg['render']})}", "--arg", f"persona={PERSONA}")

    # 3. Oar locks & link onto assembly
    ensure_subwork(lcfg["work"], lcfg["title"], "384,192,384", "0.1")
    sync_voxels(lcfg["work"], os.path.join(OUT_DIR, "oar_locks.txt"), "oar_locks")
    sc("--arg", "op=work", "--arg", "sub=unlink", "--arg", f"id={ASM_ID}", "--arg", "name=櫓座", "--arg", f"persona={PERSONA}", allow_fail=True)
    sc("--arg", "op=work", "--arg", "sub=link", "--arg", f"id={ASM_ID}", "--arg", "name=櫓座", "--arg", f"source_work={lcfg['work']}", "--arg", "at=0,0,0", "--arg", "note=步驟 13（TASK-1314）：兩舷輔佐長櫓櫓座", "--arg", f"persona={PERSONA}")

    # 4. Mount 4 long oars on 櫓座
    px, py, pz = ocfg["pivot"]
    piv_str = f"{px + 0.5},{py + 0.5},{pz + 0.5}"
    for idx, st in enumerate(cfg["stations"], start=1):
        for side in ("S", "P"):
            name = f"oar-{side}0{idx}"
            wy = st["y_s"] if side == "S" else st["y_p"]
            sc("--arg", "op=work", "--arg", "sub=unmodel", "--arg", f"id={lcfg['work']}", "--arg", f"name={name}", "--arg", f"persona={PERSONA}", allow_fail=True)
            meta = dict(mcfg, side=side)
            args = [
                "--arg", "op=work",
                "--arg", "sub=model",
                "--arg", f"id={lcfg['work']}",
                "--arg", f"name={name}",
                "--arg", f"source_work={ocfg['work']}",
                "--arg", f"at={st['x']},{wy},{st['z']}",
                "--arg", f"pivot={piv_str}",
                "--arg", "scale=0.5",
                "--arg", f"meta={json.dumps(meta, ensure_ascii=False, separators=(',', ':'))}",
                "--arg", f"note=步驟 13：輔佐長櫓（{st['name']}-{side}）",
                "--arg", f"persona={PERSONA}",
            ]
            if side == "P":
                args.extend(["--arg", "mirror=y"])
            sc(*args)

    print("Step 13 build_oars DONE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
