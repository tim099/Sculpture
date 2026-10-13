# 憲法號 階段三十七 船尾 davits 與 28 ft whale gig（Tim 2026-10-13「繼續GO」；todo 102 的後半）
# 出處：Navy plan No. 24474（1931）—— 船尾欄杆上一根往後伸的 davit、底下吊「28 FT WHALE GIG BOAT」；圖上那艘畫成約 1.9 m × 1.2 m 的橢圓
#   ＝ 艇的橫切面 ⇒ 艇是**橫著**（船頭朝舷側）吊在船尾後面。用 gun deck 砲門距當尺：davit 尖比欄杆頂往後約 12 格、高約 4 格；艇底比欄杆頂低約 20 格。
# 作品現況（量過）：船尾欄杆頂 z 128、X 97（y 115–205）；船尾面往下收（z 120 X 99、z 100 X 106）；這一段沒有繩；
#   spanker boom（模型）從 X 192 伸到 X 24、在中線 z 136–146 ⇒ 艇吊在 boom 下面（艇頂 ≤ 121）。
# 艇：沿用階段三十六的 -whaleboat（同樣 28 ft；Tim：子物件能重複用就重複用），模型 rotate 0,0,90（船頭朝 +y）、scale 0.5；
#   at.y 160.75 ⇒ 兩個環在 y 199.75／121.25，對中線剛好鏡像（davit 一舷做、另一舷鏡像，吊索才都垂直）。
# davit（設計）：2×2 黑 36，貼著船尾最後面那一格（欄杆）立起、頂前四分之一圓彎向船尾，尖在艇中線（X）正上方；尖下一格滑車；固定點 gig-davit.head。
# 用法：python -I draft_stern_gig.py <design 資料夾> <組裝件 list 匯出檔（藏掉 gig-davits／gig-davits-鏡像）> <ropes 列表檔>
import sys, os, json, math, re, hashlib
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
OUT = os.path.join(D, 'masks', 'stern_gig')
os.makedirs(OUT, exist_ok=True)
BLACK = 36
QB = json.load(open(os.path.join(D, 'verify_quarter_boats.json'), encoding='utf-8'))['boat']
boat = {}
for l in open(os.path.join(D, 'masks', 'quarter_boats', 'whaleboat.vox.txt'), encoding='utf-8'):
    x, y, z, c = map(int, l.split(','))
    boat[(x, y, z)] = c
assert len(boat) == QB['cells']
PIVOT = QB['pivot']
SCALE = QB['scale']
RING = QB['anchors']                                        # ring-aft／ring-fwd（艇的子作品座標）

a = np.loadtxt(sys.argv[2], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
S = {(int(x), int(y), int(z)) for x, y, z, c in a}

Y_HEAD = 199                                                # davit 頭那一格（S）；格心 199.5，鏡像 121.5
R = 9
Z_TOP = 138                                                 # 尖的高度（欄杆頂 128 ＋10）；v1 134 ⇒ 柱只到 125、彎出去之前沒碰到欄杆（z 126–128 才是船尾最後面）⇒ 浮空
POST_Z0 = 123


def stern_face(y, z):
    xs = [x for x in range(60, 140) if (x, y, z) in S]
    return min(xs) if xs else None


# 柱：貼在 y_head 那一欄、z POST_Z0..欄杆頂 之間船尾最後面那一格的後面
faces = {z: stern_face(Y_HEAD, z) for z in range(POST_Z0, 132)}
faces = {z: f for z, f in faces.items() if f is not None}
xf = min(faces.values())
X_POST = xf - 2                                             # 柱佔 X_POST..X_POST+1
davit = {}
for xx in (X_POST, X_POST + 1):
    for yy in (Y_HEAD - 1, Y_HEAD):
        for z in range(POST_Z0, Z_TOP - R + 1):
            davit[(xx, yy, z)] = BLACK
cx, cz = X_POST - R + 1, Z_TOP - R                          # 四分之一圓：從柱頂（往上）彎到水平往船尾
for k in range(400):
    t = math.pi / 2 * k / 399
    px = cx + R * math.cos(t) - 0.0
    pz = cz + R * math.sin(t)
    for dx in (0, 1):
        for yy in (Y_HEAD - 1, Y_HEAD):
            for dz in (0, -1):
                davit[(int(math.floor(px)) - 1 + dx, yy, int(math.floor(pz)) + dz)] = BLACK
X_TIP = min(k[0] for k in davit)                            # 尖那一欄
for yy in (Y_HEAD - 1, Y_HEAD):
    davit[(X_TIP, yy, Z_TOP - 2)] = BLACK                   # 滑車
head = (X_TIP, Y_HEAD, Z_TOP - 3)

hit = [k for k in davit if k in S]
assert not hit, ('davit 撞到現況', hit[:5])
mhit = [k for k in davit if (k[0], 320 - k[1], k[2]) in S]
assert not mhit, ('鏡像 davit 撞到現況', mhit[:5])
assert head not in davit
xs = [k[0] for k in davit]
lo = min(xs) - 1
sub = np.zeros((max(xs) - lo + 3, 320, 200), bool)
new = np.zeros_like(sub)
for (x, y, z) in S:
    if lo <= x <= max(xs) + 1 and z < 200:
        sub[x - lo, y, z] = True
for (x, y, z) in davit:
    new[x - lo, y, z] = True
lab, _ = ndimage.label(sub | new)
anch = set(np.unique(lab[sub]))
assert all(L_ in anch for L_ in np.unique(lab[new])), 'davit 浮空'

# ───────── 艇：橫吊（rotate z 90：本地 +x → 世界 +y）、艇心 X ＝ 尖那一欄格心 ─────────
KEEL_Z = 108
at = (X_TIP + 0.5, 160.75, KEEL_Z)


def rot(lx, ly):
    return -ly, lx


def boat_world():
    pts = []
    for (x, y, z) in boat:
        for dx in (0.0, 0.5, 1.0):
            for dy in (0.0, 0.5, 1.0):
                for dz in (0.0, 0.5, 1.0):
                    wx, wy = rot((x + dx - PIVOT[0]) * SCALE, (y + dy - PIVOT[1]) * SCALE)
                    pts.append((at[0] + wx, at[1] + wy, at[2] + (z + dz - PIVOT[2]) * SCALE))
    return np.array(pts)


W = boat_world()
wc = set(map(tuple, np.floor(W).astype(int)))
mirror_davit = {(x, 320 - y, z) for (x, y, z) in davit}
bhit = [p for p in wc if p in S or p in davit or p in mirror_davit]
assert not bhit, ('艇撞到東西', len(bhit), sorted(bhit)[:5])
rings = {}
for k, (x, y, z) in RING.items():
    wx, wy = rot((x + 0.5 - PIVOT[0]) * SCALE, (y + 0.5 - PIVOT[1]) * SCALE)
    rings[k] = (round(at[0] + wx, 3), round(at[1] + wy, 3), round(at[2] + (z + 0.5) * SCALE, 3))
S_ring = max(rings, key=lambda k: rings[k][1])             # y 大的那個環 ＝ S 舷 davit 那條吊索

# ───────── 既有的繩不准穿過 davit（兩舷）與艇 ─────────
R_ = set(davit) | mirror_davit | wc
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
assert not rope_hits, ('既有的繩穿過', rope_hits[:10])

FRAME_AT = (75, 190, 115)
FRAME_SIZE = (35, 20, 30)
fx, fy, fz = FRAME_AT
for (x, y, z) in davit:
    assert 0 <= x - fx < FRAME_SIZE[0] and 0 <= y - fy < FRAME_SIZE[1] and 0 <= z - fz < FRAME_SIZE[2], ('出框', (x, y, z))
txt = ''.join('%d,%d,%d,%d\n' % (x - fx, y - fy, z - fz, c) for (x, y, z), c in sorted(davit.items()))
open(os.path.join(OUT, 'gig_davit_side.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
v = dict(source='Navy plan No. 24474 (1931) 船尾 davit＋28 FT WHALE GIG BOAT（橫吊）', stern_face_x=xf, x_post=X_POST, x_tip=X_TIP, z_top=Z_TOP,
         davit=dict(frame_at=list(FRAME_AT), frame_size=list(FRAME_SIZE), mirror_at=[fx, 321 - fy - FRAME_SIZE[1], fz], cells=len(davit),
                    sha256=hashlib.sha256(txt.encode()).hexdigest(), anchors={'gig-davit.head': [head[0] - fx, head[1] - fy, head[2] - fz]}),
         boat=dict(work='basecamp-frigate-constitution-01m-whaleboat', at=list(at), rotate=[0, 0, 90], scale=SCALE, pivot=PIVOT,
                   box=[[round(float(x), 2) for x in W.min(0)], [round(float(x), 2) for x in W.max(0)]], rings=rings, s_ring=S_ring),
         head_world=list(head), ropes_hit=0, assembly_voxels=len(S))
json.dump(v, open(os.path.join(D, 'verify_stern_gig.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps({k: v[k] for k in ('stern_face_x', 'x_post', 'x_tip', 'z_top', 'head_world')}, ensure_ascii=False))
print('davit', v['davit']['cells'], 'boat box', v['boat']['box'], 'rings', rings, 'S ring', S_ring)
