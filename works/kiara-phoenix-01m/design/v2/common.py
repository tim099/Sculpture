# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）共用：讀 export list、跑 senate CLI（一律經 CLI 寫入，不直接改 json）。"""
import os, subprocess, sys, json, math

WORKS = "D:/Unity/Valhalla/Sculpture/works"
HULL = "kiara-phoenix-01m"
ASM = "kiara-phoenix-01m-assembly"
V2 = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(V2, "_tmp")          # 中間檔（不入版控）
os.makedirs(TMP, exist_ok=True)


def senate(*args, check=True):
    """跑 senate cmd sculpture；args 是 'k=v' 字串。回傳 (exit, stdout)。"""
    cmd = ["senate", "cmd", "sculpture"]
    for a in args:
        cmd += ["--arg", a]
    r = subprocess.run(cmd, cwd="D:/Unity/Senate", capture_output=True, text=True, encoding="utf-8")
    out = r.stdout + r.stderr
    if check and r.returncode != 0:
        print(out)
        raise SystemExit(f"✗ exit {r.returncode}: {' '.join(args)}")
    return r.returncode, out


def export_list(work, path, extra=()):
    senate("op=export", f"work={work}", "format=list", f"out={path}", *extra)
    return load(path)


def load(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s[0] == "#":
                continue
            x, y, z, c = map(int, s.split(","))
            out.append((x, y, z, c))
    return out


def write_vox(path, cells):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for c in cells:
            f.write(",".join(str(v) for v in c) + "\n")
    return path


def xf(m, p):
    """外部模型的變換：繞 pivot 翻面 → 縮放 → 轉（X→Y→Z）→ 放到 at（同 Sculpture.md §9.4.8）。"""
    pv = m["pivot"]; s = m["scale"]
    v = [p[0] - pv[0], p[1] - pv[1], p[2] - pv[2]]
    for i, a in enumerate("xyz"):
        if a in (m.get("mirror") or ""):
            v[i] = -v[i]
    v = [v[0] * s[0], v[1] * s[1], v[2] * s[2]]
    rx, ry, rz = [math.radians(a) for a in m["rotate"]]
    x, y, z = v
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    a = m["at"]
    return (x + a[0], y + a[1], z + a[2])
