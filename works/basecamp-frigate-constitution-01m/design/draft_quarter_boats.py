# 憲法號 階段三十六 quarter davits 與 28 ft whaleboat（Tim 2026-10-13「繼續GO」⇒ todo 102「davits 與小艇」）
# 出處：Navy plan No. 24474（1931，Outboard Profile Fittings）—— quarterdeck 舷外兩根直立 davit、頂上一根橫桁、中間吊「28 FT WHALEBOAT」（虛線）；
#   davit 頂比舷頂高約 32 格、艇底比舷頂高約 6 格（用 gun deck 砲門距當尺：500 px ≈ 31 格）。另有船尾 davit 吊「28 FT WHALE GIG BOAT」⇒ 下一階段。
# 位置：圖上兩根 davit 換到作品 X 173／251（gun deck 第 1、2 號砲門當尺）；⚠ X 173 正壓在作品 mizzen backstay 的 deadeye／lanyard（X 168–178、y 214–218）
#   ⇒ 兩根一起往船尾挪 10 格 ＝ X 163／241（間距照圖 78）。量過：這一段的繩全部 y ≤ 218、船殼與 channels 最外 y 219 ⇒ 艇放在 y ≥ 222 外面。
# 艇（設計；尺寸照一般 whaleboat 比例，未查證）：28 ft ＝ 8.53 m ⇒ 0.05 m／格 171 長、寬 37（1.85 m）、深 15；兩頭尖（double-ended）、
#   外殼白 255、舷頂一條黑 36、舷緣 136、艇內 141、坐板 5 條 104、收著 5 支槳 177；固定點 ring-aft／ring-fwd（吊索）。當外部模型縮 0.5 掛組裝件，P 舷 mirror=y。
# davit（設計）：2×2 黑 36 直柱，貼船殼最寬那一格往上，到頂之前彎向船外（四分之一圓），水平伸到艇的中線上方，頭下面一格是滑車；兩根頭用一根 1 格橫桁連起來。
#   一舷子作品（S）＋鏡像關聯。吊索：davit 頭 → 艇環，垂直、拉直。
# 用法：python -I draft_quarter_boats.py <design 資料夾> <組裝件 list 匯出檔（藏掉 davits／davits-鏡像）> <ropes 列表檔（sub=ropes 的輸出）>
import sys, os, json, math, re, hashlib
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
OUT = os.path.join(D, 'masks', 'quarter_boats')
os.makedirs(OUT, exist_ok=True)
WHITE, BLACK, GUNWALE, WOOD, THWART, OAR = 255, 36, 136, 141, 104, 177

# ───────── 艇（子作品座標：x 沿艇長、船頭 +x；y 橫向；z 0 ＝ 龍骨底；0.05 m／格）─────────
L, BW, DEP, KEEL, SHEER, SHELL, STRAKE = 171, 37, 15, 1, 3.0, 2.0, 1.5   # SHELL v1 1.0 ⇒ 斜的殼一層錯一格、只靠斜角相接 ⇒ 散成 30 塊
THWARTS_U = [0.2, 0.35, 0.5, 0.65, 0.8]
THWART_Z = 9.0
OARS_Y = [-8, -4, 0, 4, 8]
OAR_U = (0.12, 0.88)


def half_breadth(u):
    return max(0.0, math.sin(math.pi * u)) ** 0.6          # 兩頭尖


def hull_in(x, y, z, shrink=0.0):
    u = (x + 0.5) / L
    if u < 0 or u > 1:
        return False
    zk = z + 0.5 - KEEL
    if zk < shrink:
        return False
    sheer = DEP + SHEER * (2 * u - 1) ** 2
    if zk > sheer:
        return False
    hb = BW / 2.0 * half_breadth(u) * (min(zk, DEP) / DEP) ** 0.35 - shrink
    return abs(y + 0.5 - BW / 2.0) <= hb


def boat_cell(x, y, z):
    cy = BW / 2.0
    dy = abs(y + 0.5 - cy)
    u = (x + 0.5) / L
    if z < KEEL and dy <= 1.0 and 0.02 <= u <= 0.98:
        return BLACK
    if not hull_in(x, y, z):
        return 0
    zk = z + 0.5 - KEEL
    sheer = DEP + SHEER * (2 * u - 1) ** 2
    if not hull_in(x, y, z, shrink=SHELL):
        if zk > sheer - 1.0:
            return GUNWALE
        if zk > sheer - 1.0 - STRAKE:
            return BLACK
        return WHITE
    if zk < SHELL + 1.0:
        return WOOD
    for t in THWARTS_U:
        if abs(u - t) * L <= 2.0 and abs(zk - THWART_Z) <= 1.0:
            return THWART
    for oy in OARS_Y:
        if abs(y + 0.5 - (cy + oy)) <= 0.6 and OAR_U[0] <= u <= OAR_U[1] and abs(zk - (THWART_Z + 2.0)) <= 1.0:
            return OAR
    return 0


bsize = (L, BW, KEEL + DEP + int(SHEER) + 2)
boat = {(x, y, z): c for x in range(bsize[0]) for y in range(bsize[1]) for z in range(bsize[2]) for c in [boat_cell(x, y, z)] if c}
asym = sum(1 for (x, y, z), c in boat.items() if boat.get((x, bsize[1] - 1 - y, z)) != c)
G = np.zeros(bsize, bool)
for k in boat:
    G[k] = True
_, ncomp = ndimage.label(G)
assert asym == 0 and ncomp == 1, ('艇不對稱或散開', asym, ncomp)

# ───────── 現況 ─────────
a = np.loadtxt(sys.argv[2], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
S = {(int(x), int(y), int(z)) for x, y, z, c in a}
YC = 160


def outer_y(x, z):
    ys = [y for y in range(YC, 260) if (x, y, z) in S]
    return max(ys) if ys else None


CAP = {}
for X in (163, 241):
    zs = [z for z in range(100, 160) if outer_y(X, z) is not None]
    CAP[X] = max(zs)                                        # 那一欄舷側最高的格（舷頂）
DAVIT_X = [163, 241]
Y_BOAT = 233                                                # 艇中線（格）；艇半寬 BW·0.5/2 ＝ 9.25 ⇒ y 223.75..242.25
Z_TOP = max(CAP.values()) + 32                              # davit 頭（圖：舷頂 ＋32）
KEEL_Z = max(CAP.values()) + 6                              # 艇底（圖：舷頂 ＋6）

davit = {}
anchors = {}
for i, X in enumerate(DAVIT_X):
    # 柱：貼在 z 100..舷頂 之間船殼最寬那一格外面
    zr = [z for z in range(100, CAP[X] + 1) if outer_y(X, z) is not None]
    zw = max(zr, key=lambda z: (outer_y(X, z), -z))
    y0 = max(outer_y(X, z) for z in zr) + 1
    for xx in (X, X + 1):
        for yy in (y0, y0 + 1):
            for z in range(zw, Z_TOP - (Y_BOAT - y0) + 1):
                davit[(xx, yy, z)] = BLACK
    # 彎：四分之一圓，圓心 (y0 + R, Z_TOP - R)，從柱頂彎到水平
    R = Y_BOAT - y0
    cy, cz = y0 + R, Z_TOP - R
    for k in range(0, 400):
        t = math.pi / 2 * k / 399                           # 0 ＝ 柱頂（往上）→ π/2 ＝ 水平往外
        py = cy - R * math.cos(t)
        pz = cz + R * math.sin(t)
        for xx in (X, X + 1):
            for dy in (0, 1):
                for dz in (0, -1):
                    davit[(xx, int(math.floor(py)) + dy, int(math.floor(pz)) + dz)] = BLACK
    # 頭：中線上方往下一格滑車
    for xx in (X, X + 1):
        davit[(xx, Y_BOAT, Z_TOP - 2)] = BLACK
    anchors['davit-%s.head' % ('aft' if i == 0 else 'fwd')] = (X, Y_BOAT, Z_TOP - 3)
# 橫桁：兩根 davit 頭之間，y ＝ Y_BOAT、z ＝ Z_TOP
for X in range(DAVIT_X[0], DAVIT_X[1] + 2):
    davit[(X, Y_BOAT, Z_TOP)] = BLACK

hit = [k for k in davit if k in S]
assert not hit, ('davit 撞到現況', hit[:5])
mhit = [k for k in davit if (k[0], 320 - k[1], k[2]) in S]
assert not mhit, ('鏡像 davit 撞到現況', mhit[:5])
for k, p in anchors.items():
    assert p not in davit, ('固定點不在空氣裡', k)

# 浮空：davit 每一塊都要連到現況
xs = [k[0] for k in davit]
lo = min(xs) - 1
sub = np.zeros((max(xs) - lo + 2, 320, 200), bool)
new = np.zeros_like(sub)
for (x, y, z) in S:
    if lo <= x <= max(xs) + 1 and z < 200:
        sub[x - lo, y, z] = True
for (x, y, z) in davit:
    new[x - lo, y, z] = True
lab, _ = ndimage.label(sub | new)
anch = set(np.unique(lab[sub]))
assert all(L_ in anch for L_ in np.unique(lab[new])), 'davit 浮空'

# ───────── 艇放哪：兩根 davit 中間、艇環在 davit 正下方 ─────────
SCALE = 0.5
xc = (DAVIT_X[0] + DAVIT_X[1] + 2) / 2.0                  # 兩根 2 格寬柱的中點（連續座標）
ring_dx = (DAVIT_X[1] + 1 - DAVIT_X[0]) / 2.0 / SCALE      # 環離艇中心幾格（0.05 m）
ring_aft_lx = int(round(L / 2.0 - ring_dx))
ring_fwd_lx = int(round(L / 2.0 + ring_dx)) - 1
assert 0 < ring_aft_lx < ring_fwd_lx < L
PIVOT = (L / 2.0, BW / 2.0, 0)
at_s = (xc, Y_BOAT + 0.5, KEEL_Z)


def boat_world(at, mirror):
    pts = []
    for (x, y, z) in boat:
        for dx in (0.0, 0.5, 1.0):
            for dy in (0.0, 0.5, 1.0):
                for dz in (0.0, 0.5, 1.0):
                    lx, ly, lz = x + dx - PIVOT[0], y + dy - PIVOT[1], z + dz - PIVOT[2]
                    if mirror:
                        ly = -ly
                    pts.append((at[0] + lx * SCALE, at[1] + ly * SCALE, at[2] + lz * SCALE))
    return np.array(pts)


W = boat_world(at_s, False)
wc = np.floor(W).astype(int)
bhit = sum(1 for p in map(tuple, wc) if p in S or p in davit)
assert bhit == 0, ('艇撞到東西', bhit)
boat_cells_world = set(map(tuple, wc))

# 艇環（艇的子作品座標）：艏艉在中線、舷緣下面一格 ⇒ 那一格要是艇內的空氣或坐板以上
def ring_z(lx):
    u = (lx + 0.5) / L
    return int(KEEL + DEP + SHEER * (2 * u - 1) ** 2) - 2


boat_anchors = {'ring-aft': (ring_aft_lx, BW // 2, ring_z(ring_aft_lx)), 'ring-fwd': (ring_fwd_lx, BW // 2, ring_z(ring_fwd_lx))}

# ───────── 繩：既有的繩不准穿過 davit（兩舷）與艇（兩舷）─────────
R_ = set(davit) | {(x, 320 - y, z) for (x, y, z) in davit} | boat_cells_world | {(x, 320 - y, z) for (x, y, z) in boat_cells_world}
rope_hits = []
for line in open(sys.argv[3], encoding='utf-8'):
    if not line.startswith('- '):
        continue
    name = re.search(r'`([^`]+)`', line).group(1)
    pts = re.findall(r'\(([-\d.]+),([-\d.]+),([-\d.]+)\)', line)
    if len(pts) < 2:
        continue
    sag = float(re.search(r'最大下垂 ([\d.]+)', line).group(1)) if '最大下垂' in line else 0.0
    A = tuple(map(float, pts[0])); B = tuple(map(float, pts[1]))
    k = max(2, int(math.dist(A, B) * 4)); c = 0
    for i in range(k + 1):
        p = [A[j] + (B[j] - A[j]) * i / k for j in range(3)]
        s = sag * 4 * (i / k) * (1 - i / k)
        if any((math.floor(p[0]), math.floor(p[1]), math.floor(p[2] - dz)) in R_ for dz in range(0, int(math.ceil(s)) + 1)):
            c += 1
    if c:
        rope_hits.append((name, c))
assert not rope_hits, ('既有的繩穿過 davit 或艇', rope_hits[:10])

# ───────── 輸出 ─────────
FRAME_AT = (150, 200, 100)
FRAME_SIZE = (110, 50, 80)
fx, fy, fz = FRAME_AT
for (x, y, z) in davit:
    assert 0 <= x - fx < FRAME_SIZE[0] and 0 <= y - fy < FRAME_SIZE[1] and 0 <= z - fz < FRAME_SIZE[2], ('出框', (x, y, z))
dtxt = ''.join('%d,%d,%d,%d\n' % (x - fx, y - fy, z - fz, c) for (x, y, z), c in sorted(davit.items()))
btxt = ''.join('%d,%d,%d,%d\n' % (x, y, z, c) for (x, y, z), c in sorted(boat.items()))
open(os.path.join(OUT, 'davits_side.vox.txt'), 'w', encoding='utf-8', newline='\n').write(dtxt)
open(os.path.join(OUT, 'whaleboat.vox.txt'), 'w', encoding='utf-8', newline='\n').write(btxt)
cnt = {}
for c in boat.values():
    cnt[c] = cnt.get(c, 0) + 1
v = dict(source='Navy plan No. 24474 (1931) quarter davits + 28 FT WHALEBOAT; X 挪 −10（避 mizzen backstay）',
         cap=CAP, z_top=Z_TOP, keel_z=KEEL_Z, y_boat=Y_BOAT,
         davits=dict(frame_at=list(FRAME_AT), frame_size=list(FRAME_SIZE), mirror_at=[fx, 321 - fy - FRAME_SIZE[1], fz], cells=len(davit),
                     sha256=hashlib.sha256(dtxt.encode()).hexdigest(),
                     anchors={k: [p[0] - fx, p[1] - fy, p[2] - fz] for k, p in anchors.items()}),
         boat=dict(size=list(bsize), cells=len(boat), colors=cnt, asym_y=asym, components=ncomp, sha256=hashlib.sha256(btxt.encode()).hexdigest(),
                   anchors={k: list(p) for k, p in boat_anchors.items()}, scale=SCALE, pivot=list(PIVOT),
                   at_s=list(at_s), at_p=[at_s[0], 321 - at_s[1], at_s[2]],
                   box_s=[[round(float(x), 2) for x in W.min(0)], [round(float(x), 2) for x in W.max(0)]]),
         ropes_hit=0, assembly_voxels=len(S))
json.dump(v, open(os.path.join(D, 'verify_quarter_boats.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps({k: v[k] for k in ('cap', 'z_top', 'keel_z', 'y_boat')}, ensure_ascii=False))
print('davits', v['davits']['cells'], v['davits']['anchors'], 'mirror_at', v['davits']['mirror_at'])
print('boat', v['boat']['size'], v['boat']['cells'], v['boat']['colors'], v['boat']['anchors'], 'box', v['boat']['box_s'])
