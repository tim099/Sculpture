# -*- coding: utf-8 -*-
"""炎羽號 v3（2026-10-17，Tim「請參考憲法號的規格 優化一下妳的船吧(包含桅杆的繩梯 船舵等)」）：
靜索整套 —— channels（一舷＋鏡像）、下 deadeye、chain plate、桅的固定點、lower shrouds、backstays、
上 deadeye＋lanyards、futtock shrouds、topmast／topgallant shrouds、ratlines 橫繩組（lower 標繩梯 climb=1）。
照造船規格 §5、§6、§9（ladders／ratline）、§10；做法抄憲法號階段十八、十九、二十五、四十七。全部經 CLI 寫入。

量到的（2026-10-17，桅與船殼的格子；design/v3/_tmp/*.txt）：
  前桅 x 405：下桅 r3 到 z 191、桅頂平台 z 192..196（平台 z 195..196、y 77..103）、topmast r1 z 262..、橫桁 z 282..286（頂層 285..286 y 81..99）、桅頂 361
  主桅 x 275：到 z 206、平台 207..211（210..211 y 75..105）、topmast r2 212..306、橫桁 302..306（305..306 y 80..100）、桅頂 382
  後桅 x 155：到 z 166、平台 167..171（170..171 y 79..101）、topmast r2 172..185、r1 186..、沒有橫桁、桅頂 322
  船殼：下層砲門開口 z 59..64；露天甲板 carronade 砲門 x 157..161／182..186／206..210（z 82..87）、追擊砲門 x 420..423
用法：python -I -X utf8 rig_standing.py | apply
"""
import sys, os, json, math, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "v2"))
from common import ASM, HULL, WORKS, senate, export_list, load, write_vox

TMP = os.path.join(HERE, "_tmp")
os.makedirs(TMP, exist_ok=True)
P = "persona=kiara"
CH = "kiara-phoenix-01m-channels"
# channels 子作品的框（S 舷；P 舷 mirror=y、at.y ＝ 181 − at.y − sy）
CH_AT = (120, 120, 64)
CH_SIZE = (300, 30, 14)
CH_AT_P = (CH_AT[0], 181 - CH_AT[1] - CH_SIZE[1], CH_AT[2])
CH_Z = (70, 71)            # channel 板（下層砲門頂 64 之上、舷牆頂 76 之下）
CH_W = 8                   # 往船殼外 8 格（憲法號 12；炎羽號船寬 9.6 m）
DE_Z = (72, 73, 74)        # 下 deadeye 3×3 去四角、2 格厚，坐在外緣上
PLATE_Z = 65               # chain plate 下端（砲門頂 64 之上）
C_CH, C_DE, C_PLATE = 36, 104, 36

MASTS = {
    # 桅：(關聯名, 子作品, 桅軸 x, hounds z, 下桅在 hounds 的半徑, 平台頂 z, 平台半寬, topmast 頭 z, topmast 半徑, 橫桁頂 z 或 None, 橫桁半寬, topgallant 頭 z 或 None)
    "fore": ("前桅", "kiara-phoenix-01m-mast-fore", 405, 191, 2, 196, 13, 281, 1, 286, 9, 356),
    "main": ("主桅", "kiara-phoenix-01m-mast-main", 275, 206, 2, 211, 15, 301, 2, 306, 10, 376),
    "mizzen": ("後桅", "kiara-phoenix-01m-mast-mizzen", 155, 166, 2, 171, 11, 298, 1, None, 0, None),
}
# 每根桅一舷的 deadeye x（前 → 後）：lower shrouds ＋ backstays；間距 6、第一個在桅前 4
# 後桅避開 carronade 砲門 x 157..161（shroud 從 deadeye 幾乎直上，砲門前面不能有繩；憲法號 channels v2 的教訓）
DEADEYES = {
    "fore": ([409, 403, 397, 391, 385, 379], [373, 367]),
    "main": ([279, 273, 267, 261, 255, 249, 243], [237, 231]),
    "mizzen": ([165, 152, 146, 140, 134], [128]),
}
TM_RIM_DX = {"fore": [4, 0, -4], "main": [5, 0, -5], "mizzen": [3, -3]}   # topmast shrouds 在平台邊緣的 x（相對桅軸）
TAR = "#2b2620"; LANY = "#a08458"; DEAD = "#6d4900"


def fmt(v):
    return ",".join(f"{round(a, 2):g}" for a in v)


def norm(v):
    L = math.sqrt(sum(a * a for a in v))
    return tuple(a / L for a in v)


def add(a, b, k=1.0):
    return tuple(a[i] + k * b[i] for i in range(3))


def mirror_pt(p):
    return (p[0], 181 - p[1], p[2])


# ---------------------------------------------------------------- 量
def hull_profile():
    path = os.path.join(TMP, "hull.txt")
    cells = load(path) if os.path.exists(path) else export_list(HULL, path)
    mx = collections.defaultdict(lambda: -1)
    for x, y, z, c in cells:
        if y >= 90 and y > mx[(x, z)]:
            mx[(x, z)] = y
    return mx


def channel_cells(mx):
    """S 舷的 channels（組裝件座標）：板＋下 deadeye＋chain plate；回傳 {cell: color}、deadeye 中心。"""
    cells = {}
    centers = {}
    for mast, (shr, bks) in DEADEYES.items():
        xs = shr + bks
        x0, x1 = min(xs) - 4, max(xs) + 4
        span = x1 - x0 + 1
        edge = {}
        for x in range(x0, x1 + 1):
            d = min(x - x0, x1 - x)
            r = 4.0
            cut = 0 if d >= r else int(round(r - math.sqrt(max(0.0, r * r - (r - d - 0.5) ** 2))))
            base = max(mx[(x, z)] for z in CH_Z)
            e = base + CH_W - cut
            edge[x] = e
            for z in CH_Z:
                for y in range(mx[(x, z)] + 1, e + 1):
                    cells[(x, y, z)] = C_CH
        for i, dx in enumerate(xs):
            e = edge[dx]
            for x in (dx - 1, dx, dx + 1):
                for z in DE_Z:
                    if x != dx and z in (DE_Z[0], DE_Z[-1]):
                        continue
                    for y in (e - 1, e):
                        cells[(x, y, z)] = C_DE
            centers[(mast, i)] = (dx + 0.5, e, DE_Z[1] + 0.5)          # 2 格厚的中間（格界）
            # chain plate：板底（z 69）外緣 → 船殼表面（z 65），6 連通地往內往下
            y, z = e - 1, CH_Z[0] - 1
            yb = mx[(dx, PLATE_Z)] + 1
            n = (y - yb) + (z - PLATE_Z)
            pts = []
            for k in range(n + 1):
                t = k / n if n else 0
                pts.append((y - (y - yb) * t, z - (z - PLATE_Z) * t))
            prev = None
            for py, pz in pts:
                c = (dx, int(round(py)), int(round(pz)))
                if prev and abs(c[1] - prev[1]) + abs(c[2] - prev[2]) > 1:
                    cells[(dx, c[1], prev[2])] = C_PLATE
                cells[c] = C_PLATE
                prev = c
    return cells, centers


def mast_anchors():
    """桅的固定點（桅子作品與組裝件同框 ⇒ 組裝件座標）。"""
    out = {}
    for mast, (link, work, mx_, hz, hr, tz, tw, tmz, tmr, xz, xw, tgz) in MASTS.items():
        a = {}
        for s, sg in (("S", 1), ("P", -1)):
            a[f"shrouds-{s}"] = (mx_, 90 + sg * hr, hz)                 # hounds：平台下一格的桅側
            a[f"futtock-{s}"] = (mx_, 90 + sg * (hr + 1), hz - 10)       # futtock band：hounds 下 10 格、下桅表面
            a[f"tm-{s}"] = (mx_, 90 + sg * tmr, tmz)                    # topmast head：橫桁（或 topsail 上方）下一格
            for i, dxr in enumerate(TM_RIM_DX[mast], 1):
                a[f"rim-{s}{i}"] = (mx_ + dxr, 90 + sg * tw, tz)          # 平台頂層邊緣（topmast shrouds 下端）
                a[f"rimlow-{s}{i}"] = (mx_ + dxr, 90 + sg * tw, tz - 1)   # 平台底層邊緣（futtock shrouds 上端）
            if xz:
                for i, dxr in enumerate((3, -3), 1):
                    a[f"xtree-{s}{i}"] = (mx_ + dxr, 90 + sg * xw, xz - 1)
        if tgz:
            a["tg-head"] = (mx_, 90, tgz)
        out[mast] = (link, work, a)
    return out


def cont(c):
    return (c[0] + 0.5, c[1] + 0.5, c[2] + 0.5)


def plan():
    mx = hull_profile()
    ch, centers = channel_cells(mx)
    ma = mast_anchors()
    ropes = []      # (name, from, to, thickness, color, slack, group, kind)
    de_anchor = {}  # S 舷 channels 子作品的固定點（子作品座標）
    ratl = []
    for mast, (shr, bks) in DEADEYES.items():
        link, work, A = ma[mast]
        n_sh = len(shr)
        for s in ("S", "P"):
            for i, dx in enumerate(shr + bks):
                L = centers[(mast, i)]
                if s == "P":
                    L = mirror_pt(L)
                if s == "S":
                    de_anchor[f"{mast}.deadeye-{i + 1}"] = (dx - CH_AT[0], int(L[1]) - CH_AT[1], DE_Z[1] - CH_AT[2])
                is_sh = i < n_sh
                top = A[f"shrouds-{s}"] if is_sh else A[f"tm-{s}"]
                H = cont(top)
                u = norm(tuple(H[k] - L[k] for k in range(3)))
                U = add(L, u, 8.0)                                     # 上 deadeye 中心：下 deadeye → 桅上那端的線上 8 格
                out_y = 1 if s == "S" else -1
                nm = f"{mast}-shroud-{s}{i + 1}" if is_sh else f"{mast}-backstay-{s}{i - n_sh + 1}"
                th = {"fore": 0.8, "main": 0.9, "mizzen": 0.7}[mast] if is_sh else 0.75
                ropes.append((nm, fmt(add(U, u, 1.5)), f"{link}/{'shrouds' if is_sh else 'tm'}-{s}", th, TAR, 1,
                              "standing/shrouds" if is_sh else "standing/backstays", "shroud" if is_sh else "backstay"))
                ropes.append((f"{nm}.deadeye", fmt((U[0], U[1] - out_y, U[2])), fmt((U[0], U[1] + out_y, U[2])), 3, DEAD, 1,
                              "standing/deadeyes/upper", None))
                for k, ox in zip("abc", (-0.9, 0, 0.9)):
                    a = add(add(L, u, 1.3), (ox, 0, 0))
                    b = add(add(U, u, -1.3), (ox, 0, 0))
                    ropes.append((f"{nm}.lanyard-{k}", fmt(a), fmt(b), 0.25, LANY, 1, "standing/deadeyes/lanyards", None))
            # futtock、topmast、topgallant shrouds
            for i in range(1, len(TM_RIM_DX[mast]) + 1):
                ropes.append((f"{mast}-futtock-{s}{i}", f"{link}/rimlow-{s}{i}", f"{link}/futtock-{s}", 0.5, TAR, 1,
                              "standing/futtock-shrouds", "shroud"))
                ropes.append((f"{mast}-tmshroud-{s}{i}", f"{link}/rim-{s}{i}", f"{link}/tm-{s}", 0.55, TAR, 1,
                              "standing/topmast-shrouds", "shroud"))
            if "tg-head" in A:
                for i in (1, 2):
                    ropes.append((f"{mast}-tgshroud-{s}{i}", f"{link}/xtree-{s}{i}", f"{link}/tg-head", 0.4, TAR, 1,
                                  "standing/topgallant-shrouds", "shroud"))
            # ratlines 橫繩組：rope_a ＝ 最前那根、rope_b ＝ 最後那根
            ratl.append(dict(name=f"{mast}-lower-{s}", a=f"{mast}-shroud-{s}1", b=f"{mast}-shroud-{s}{n_sh}",
                             start=7, stop=16, th=0.3, group="ratlines/lower", climb=True, mast=mast, side=s))
            ntm = len(TM_RIM_DX[mast])
            ratl.append(dict(name=f"{mast}-topmast-{s}", a=f"{mast}-tmshroud-{s}1", b=f"{mast}-tmshroud-{s}{ntm}",
                             start=4, stop=10, th=0.25, group="ratlines/topmast", climb=False, mast=mast, side=s))
    return ch, de_anchor, ma, ropes, ratl


# ---------------------------------------------------------------- 繩梯落腳點（照遊戲的 standZ：腳下實心、上面 7 格空）
def deck_floor(x):
    """露天甲板關聯 meta 的 floor（地板上第一層空氣），線性內插。"""
    links = json.load(open(os.path.join(WORKS, ASM, "links.json"), encoding="utf-8"))["links"]
    fl = [l for l in links if (l.get("meta") or {}).get("deck") == "spar"][0]["meta"]["floor"]
    pts = [tuple(int(v) for v in p.split(":")) for p in fl.split(",")]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return int(round(z0 + (z1 - z0) * (x - x0) / (x1 - x0)))
    raise SystemExit(f"x {x} 不在露天甲板 floor 的範圍")



def stand_points(ratl, ropes, ma):
    path = os.path.join(TMP, "asm.txt")
    cells = export_list(ASM, path)
    occ = set((x, y, z) for x, y, z, c in cells)
    ok = lambda x, y, z: (x, y, z - 1) in occ and all((x, y, z + k) not in occ for k in range(7))
    rope = {r[0]: r for r in ropes}
    res = {}
    for r in ratl:
        if not r["climb"]:
            continue
        mast, s = r["mast"], r["side"]
        link, work, A = ma[mast]
        sg = 1 if s == "S" else -1
        # 最低一道的中點 x ≈ 兩根母繩下端 x 的平均
        xa = float(rope[r["a"]][1].split(",")[0]); xb = float(rope[r["b"]][1].split(",")[0])
        xm = int(round((xa + xb) / 2 - 0.5))
        foot = None
        for xx in [xm + d for d in (0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6)]:
            # 從中線往這一舷走：露天甲板（甲板 meta floor ±2）站得住的最後一格 ＝ 舷牆內側；再往內 2 格
            fz = deck_floor(xx)
            last = None
            for k in range(0, 60):
                y = 90 + sg * k
                zs = [z for z in range(fz - 2, fz + 3) if ok(xx, y, z)]
                if zs:
                    last = (y, zs[0])
                elif last is not None and any((xx, y, z) in occ for z in range(fz, fz + 6)):
                    break                                              # 撞到舷牆
            if last:
                y2 = last[0] - sg * 2
                z2 = [z for z in range(fz - 2, fz + 3) if ok(xx, y2, z)]
                if z2:
                    foot = (xx, y2, z2[0])
            if foot:
                break
        # head：桅頂平台靠這一舷的邊往內 2 格、桅軸那一欄
        mx_ = MASTS[mast][2]; tz = MASTS[mast][5]; tw = MASTS[mast][6]
        head = None
        for yy in [90 + sg * (tw - 2 - d) for d in range(6)]:
            for xx in (mx_, mx_ - 1, mx_ + 1, mx_ - 2, mx_ + 2):
                if ok(xx, yy, tz + 1):
                    head = (xx, yy, tz + 1); break
            if head:
                break
        res[r["name"]] = (foot, head)
    return res


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    ch, de_anchor, ma, ropes, ratl = plan()
    print(f"channels 一舷 {len(ch)} 格；deadeye 固定點 {len(de_anchor)}；繩 {len(ropes)}；橫繩組 {len(ratl)}")
    # 跟組裝件現有的格子撞不撞（channels 是新部件，不准蓋到任何東西）
    asm_path = os.path.join(TMP, "asm.txt")
    asm = load(asm_path) if os.path.exists(asm_path) else export_list(ASM, asm_path)
    occ = set((x, y, z) for x, y, z, c in asm)
    chw = os.path.join(WORKS, CH)
    # 已經套用過 ⇒ 組裝件裡就有 channels 自己的格，拿掉再比
    have = set()
    if os.path.exists(chw):
        for x, y, z, c in export_list(CH, os.path.join(TMP, "ch_now.txt")):
            w = (x + CH_AT[0], y + CH_AT[1], z + CH_AT[2])
            have.add(w); have.add((w[0], 180 - w[1], w[2]))
    clash = [c for c in ch if c in occ and c not in have]
    clash_p = [c for c in ch if (c[0], 180 - c[1], c[2]) in occ and (c[0], 180 - c[1], c[2]) not in have]
    print(f"碰撞：S {len(clash)}、P（鏡像）{len(clash_p)}", clash[:5], clash_p[:5])
    xs = [c[0] for c in ch]; ys = [c[1] for c in ch]; zs = [c[2] for c in ch]
    print("channels 外框", (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs)), "框", CH_AT, CH_SIZE)
    assert min(xs) >= CH_AT[0] and max(xs) < CH_AT[0] + CH_SIZE[0]
    assert min(ys) >= CH_AT[1] and max(ys) < CH_AT[1] + CH_SIZE[1]
    assert min(zs) >= CH_AT[2] and max(zs) < CH_AT[2] + CH_SIZE[2]
    sp = stand_points(ratl, ropes, ma)
    for k, v in sp.items():
        print(" 繩梯", k, "foot", v[0], "head", v[1])
    if not apply:
        for r in ropes[:6]:
            print(" ", r)
        return
    if clash or clash_p or any(v[0] is None or v[1] is None for v in sp.values()):
        raise SystemExit("✗ 有碰撞或落腳點量不到 ⇒ 不套用")

    # 1. channels 子作品
    if not os.path.exists(chw):
        senate("op=work", "sub=create", f"id={CH}", P, "account=Myth", f"parent_work={HULL}",
               "title=炎羽號 channels（一舷）", f"size={fmt(CH_SIZE)}", "tags=sub")
    senate("op=work", "sub=update", f"work={CH}", P, f"size={fmt(CH_SIZE)}", "meters_per_voxel=0.1", "tags=sub")
    want = {(x - CH_AT[0], y - CH_AT[1], z - CH_AT[2]): c for (x, y, z), c in ch.items()}
    now = {(x, y, z): c for x, y, z, c in export_list(CH, os.path.join(TMP, "ch_now.txt"))}
    if now != want:
        if now:
            write_vox(os.path.join(TMP, "ch_carve.txt"), [(*k, v) for k, v in sorted(now.items())])
            senate("op=carvevox", f"work={CH}", P, "at=0,0,0", f"voxels={os.path.join(TMP, 'ch_carve.txt')}",
                   f"expect_pixels={len(now)}", "share=0")
        write_vox(os.path.join(TMP, "ch_stamp.txt"), [(*k, v) for k, v in sorted(want.items())])
        senate("op=stampvox", f"work={CH}", P, "at=0,0,0", f"voxels={os.path.join(TMP, 'ch_stamp.txt')}",
               f"expect_pixels={len(want)}", "share=0")
    links = {l["name"]: l for l in json.load(open(os.path.join(WORKS, ASM, "links.json"), encoding="utf-8"))["links"]}
    if "channels" not in links:
        senate("op=work", "sub=link", f"work={ASM}", P, "name=channels", f"source_work={CH}", f"at={fmt(CH_AT)}",
               "note=v3：channels（S 舷）")
    if "channels-鏡像" not in links:
        senate("op=work", "sub=link", f"work={ASM}", P, "name=channels-鏡像", f"source_work={CH}", f"at={fmt(CH_AT_P)}",
               "mirror=y", "note=v3：channels（P 舷，mirror=y）")
    # 2. 固定點
    for nm, at in de_anchor.items():
        senate("op=work", "sub=anchor", f"work={CH}", P, f"name={nm}", f"at={fmt(at)}", "overwrite=1",
               "note=下 deadeye 中心（S 舷；P 舷走 channels-鏡像/…）")
    for mast, (link, work, A) in ma.items():
        for nm, at in A.items():
            senate("op=work", "sub=anchor", f"work={work}", P, f"name={nm}", f"at={fmt(at)}", "overwrite=1",
                   "note=v3 靜索固定點（design/v3/rig_standing.py）")
    # 3. 繩（同名、兩端一樣 ⇒ 不給 from／to）
    have_r = {r["name"]: (r["from"], r["to"]) for r in json.load(open(os.path.join(WORKS, ASM, "ropes.json"), encoding="utf-8"))["ropes"]}
    meta_lines = []
    for nm, a, b, th, color, slack, group, kind in ropes:
        c = ["op=work", "sub=rope", f"work={ASM}", P, f"name={nm}", f"slack={slack:g}", f"color={color}",
             f"thickness={th:g}", f"group={group}"]
        if have_r.get(nm) != (a, b):
            c += [f"from={a}", f"to={b}"] + (["overwrite=1"] if nm in have_r else [])
        senate(*c)
        if kind:
            meta_lines.append(f"rope\t{nm}\t" + json.dumps({"kind": kind}))
    mf = os.path.join(TMP, "rope_meta.tsv")
    with open(mf, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(meta_lines) + "\n")
    senate("op=work", "sub=meta", f"work={ASM}", P, f"file={mf}")
    # 4. ratlines 橫繩組（同名、參數一樣 ⇒ 不重下；不一樣 ⇒ overwrite=1）
    have_rl = {r["name"]: r for r in json.load(open(os.path.join(WORKS, ASM, "ropes.json"), encoding="utf-8")).get("ratlines", [])}
    for r in ratl:
        foot, head = sp.get(r["name"], (None, None))
        h = have_rl.get(r["name"])
        if h and (h["a"], h["b"], h["start"], h["stop"], h["climb"], h.get("foot", ""), h.get("head", ""), h["thickness"]) == \
                (r["a"], r["b"], r["start"], r["stop"], r["climb"], fmt(foot) if foot else "", fmt(head) if head else "", r["th"]):
            continue
        c = ["op=work", "sub=ratlines", f"work={ASM}", P, f"name={r['name']}", f"rope_a={r['a']}", f"rope_b={r['b']}",
             "step=4", f"start={r['start']}", f"stop={r['stop']}", "min_span=5", f"thickness={r['th']:g}",
             f"color={TAR}", f"group={r['group']}"] + (["overwrite=1"] if h else [])
        if r["climb"]:
            foot, head = sp[r["name"]]
            c += ["climb=1", f"foot={fmt(foot)}", f"head={fmt(head)}"]
        senate(*c)
    print("done")


if __name__ == "__main__":
    main()
