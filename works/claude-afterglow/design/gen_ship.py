"""餘暉號（claude-afterglow）—— 宇宙飛船的產生器

原創設計：長程信使艇。只借太空歌劇的「舊未來」質感（灰色船殼、面板深淺、管線、髒污、發光的引擎），
⛔ 不照抄任何電影裡的現有船型。

座標（雕刻作品）：x ＝ 船長方向（船尾在小的那端、機頭朝 +x），y ＝ 寬（中線 71.5，左右對稱），z ＝ 上。
每格 0.1 m ⇒ 船長約 20 m、翼展約 12 m、高約 5 m。

用法：python -I gen_ship.py <輸出資料夾>
輸出：每個階段一份 stampvox 清單（x,y,z,color；at=0,0,0），外加 summary.json（每階段格數、顏色分布）。
階段彼此不重疊（每一格只屬於一個部件），所以照順序 stampvox 不會撞格。
"""
import json
import math
import os
import sys

import numpy as np

NX, NY, NZ = 224, 144, 64
CY = 71.5          # 左右對稱的中線（71 與 72 兩格之間）
ZC = 28            # 船身中心高度

# ── 顏色（RGB332 調色盤 index；註解是解碼後的 RGB）────────────
HULL_A = 182   # (182,182,170) 主船殼：暖灰
HULL_B = 146   # (145,145,170) 冷灰面板
HULL_C = 218   # (218,218,170) 淺色面板
MID = 109      # (109,109,85)  中灰：面板縫、環
DARK = 73      # (72,72,85)    深灰：管線、零件、進氣口
VDARK = 37     # (36,36,85)    更深：通風口、噴嘴內壁、燒痕
RED = 164      # (182,36,0)    紅色識別帶
ORANGE = 240   # (255,145,0)   橘色識別帶
GLASS = 41     # (36,72,85)    座艙玻璃
GLOW_CORE = 191  # (182,255,255) 引擎核心（發光）
GLOW = 83        # (72,145,255)  引擎外圈（發光）
NAV_RED = 224    # (255,0,0)     左翼尖航行燈（發光）
NAV_GREEN = 28   # (0,255,0)     右翼尖航行燈（發光）
LAMP = 254       # (255,255,170) 尾燈（發光）
WINDOW = 248     # (255,218,0)   舷窗（發光）
EMISSIVE = [GLOW_CORE, GLOW, NAV_RED, NAV_GREEN, LAMP, WINDOW]

# 部件 ⇒ 階段（stampvox 的順序）
STAGES = ["hull", "cockpit", "wings", "fin", "nacelles", "engines", "details"]
SID = {n: i + 1 for i, n in enumerate(STAGES)}

col = np.zeros((NX, NY, NZ), np.uint8)   # 0 ＝ 空
comp = np.zeros((NX, NY, NZ), np.uint8)  # 屬於哪個階段

X, Y, Z = np.meshgrid(np.arange(NX), np.arange(NY), np.arange(NZ), indexing="ij")
DY = np.abs(Y - CY)                # 到中線的距離：71 → 0.5、72 → 0.5（y ↔ NY-1-y 對稱）


def put(mask, color, stage, overwrite=False):
    """把 mask 裡的格設成 color、歸到 stage。overwrite=False ⇒ 只填空格。"""
    m = mask if overwrite else (mask & (col == 0))
    col[m] = color
    comp[m] = SID[stage]


def hsh(*a):
    """決定性的雜湊 → [0,1)（numpy 向量化；面板深淺、零件位置用）"""
    h = np.zeros_like(np.asarray(a[0], dtype=np.int64)) + 1469598103
    for v in a:
        h = (h ^ (np.asarray(v, dtype=np.int64) + 0x9E3779B9)) * 16777619 % 4294967296
        h = (h ^ (h >> 13)) * 1274126177 % 4294967296
    return (h % 100000) / 100000.0


# ── 1. 船身 ─────────────────────────────────────────────
XS, XN = 22, 214   # 船尾面、機頭尖


def fus_profile(x):
    """回傳 (半寬, 上高, 下深)：船尾是方正的引擎段，中段微收，前段收成尖鼻。"""
    x = np.asarray(x, dtype=float)
    W = np.full_like(x, np.nan); T = np.full_like(x, np.nan); B = np.full_like(x, np.nan)
    a = (x >= XS) & (x < 70)
    W[a], T[a], B[a] = 19.0, 12.0, 11.0
    b = (x >= 70) & (x < 150)
    t = (x[b] - 70) / 80.0
    W[b], T[b], B[b] = 19 - 4 * t, 12 - 1 * t, 11 - 2 * t
    c = (x >= 150) & (x <= XN)
    t = (x[c] - 150) / (XN - 150.0)
    W[c] = 15 * (1 - t) ** 1.1 + 1.0 * t
    T[c] = 9.5 * (1 - t) ** 1.25 + 1.5
    B[c] = 7.5 * (1 - t) ** 1.15 + 1.5
    return W, T, B


W, T, B = fus_profile(X)
inside_x = ~np.isnan(W)
Wn = np.where(inside_x, W, 1.0); Tn = np.where(inside_x, T, 1.0); Bn = np.where(inside_x, B, 1.0)
dz = Z + 0.5 - ZC
H = np.where(dz >= 0, Tn, Bn)
n_exp = np.where(dz >= 0, 2.6, 4.0)          # 上面圓一點、肚子平一點
fus = inside_x & ((np.abs(DY) / Wn) ** n_exp + (np.abs(dz) / H) ** n_exp <= 1.0)
put(fus, HULL_A, "hull")

# 背脊：船尾到座艙前一段的隆起
top_z = ZC + Tn
spine = inside_x & (X >= 30) & (X <= 140) & (DY <= 3.5) & (Z + 0.5 > top_z - 1) & (Z + 0.5 <= top_z + 3)
put(spine, MID, "hull")

# ── 2. 座艙 ─────────────────────────────────────────────
CK0, CK1 = 136, 176
u = np.clip((X - CK0) / float(CK1 - CK0), 0, 1)
ck_h = 6.5 * np.sin(np.pi * u) ** 0.6
ck_w = 7.5 * np.sin(np.pi * u) ** 0.4
canopy = (X >= CK0) & (X <= CK1) & (DY <= ck_w) & (Z + 0.5 > top_z - 1) & (Z + 0.5 <= top_z + ck_h) \
    & ((DY / np.maximum(ck_w, 0.1)) ** 2 + ((Z + 0.5 - top_z) / np.maximum(ck_h, 0.1)) ** 2 <= 1.0)
put(canopy, HULL_C, "cockpit")

# ── 3. 主翼（後掠）──────────────────────────────────────
s = np.clip((DY - 18) / 40.0, 0, 1)
le = 135 + (78 - 135) * s        # 前緣
te = 70 + (48 - 70) * s          # 後緣
th = 5 - 3 * s                   # 厚度
zw = 23.5 + 0.0 * s
wing = (DY >= 14) & (DY <= 58) & (X >= te) & (X <= le) & (Z + 0.5 >= zw) & (Z + 0.5 <= zw + th)
put(wing, HULL_A, "wings")

# ── 4. 垂直尾翼 ─────────────────────────────────────────
fz0 = ZC + 12.0
FIN_TOP = 56
f = np.clip((Z + 0.5 - fz0) / (FIN_TOP - fz0), 0, 1)
fle = 68 + (46 - 68) * f
fte = 27 - 5 * f
fth = np.where(f < 0.5, 2.0, 1.0)
fin = (Z + 0.5 >= fz0 - 1) & (Z < FIN_TOP) & (X >= fte) & (X <= fle) & (DY <= fth)
put(fin, HULL_A, "fin")

# ── 5. 引擎艙（左右各一，掛在翼上）─────────────────────
NAC_DY, NAC_Z, NAC_R = 44, 25.0, 8.5
NAC_X0, NAC_X1 = 26, 92
ry = DY - NAC_DY
rz = Z + 0.5 - NAC_Z
rr = np.sqrt(ry ** 2 + rz ** 2)
taper = np.where(X > NAC_X1 - 8, NAC_R - (X - (NAC_X1 - 8)) * 0.25, NAC_R)
nac = (X >= NAC_X0) & (X <= NAC_X1) & (rr <= taper)
intake = (X >= NAC_X1 - 3) & (rr <= 5.2)
put(nac & ~intake, HULL_B, "nacelles")
put(nac & intake & (X == NAC_X1 - 3), VDARK, "nacelles")      # 進氣口深處
# 噴嘴：喇叭口，內壁深色，裡面是發光盤
noz = (X >= 16) & (X < NAC_X0) & (rr <= 7.6) & (rr >= 5.6 - (NAC_X0 - X) * 0.05)
put(noz, DARK, "nacelles")
put((X == 19) & (rr < 5.6) & (rr >= 2.8), GLOW, "nacelles")
put((X == 19) & (rr < 2.8), GLOW_CORE, "nacelles")
put((X == 20) & (rr < 5.6), VDARK, "nacelles")                # 發光盤後面封住

# ── 6. 主引擎（船尾三具）───────────────────────────────
for (cy_off, cz, R) in [(0.0, 28.0, 6.5), (11.5, 25.5, 5.0), (-11.5, 25.5, 5.0)]:
    ey = Y - (CY + cy_off)
    ez = Z + 0.5 - cz
    er = np.sqrt(ey ** 2 + ez ** 2)
    bell = (X >= 10) & (X < XS) & (er <= R + (XS - X) * 0.08) & (er >= R - 1.6)
    put(bell, DARK, "engines")
    put((X == 13) & (er < R - 1.6) & (er >= (R - 1.6) * 0.5), GLOW, "engines")
    put((X == 13) & (er < (R - 1.6) * 0.5), GLOW_CORE, "engines")
    put((X >= 14) & (X < XS) & (er < R - 1.6), VDARK, "engines")   # 噴嘴裡面（實心，看起來是深洞）

# ── 7. 細節：管線、零件 ───────────────────────────────
# 船身兩側的管線（引擎段，貼著船殼外面）
# 管線跟著船殼的半寬走（船身往前收窄，管線一起往內收；固定在 DY=20 會在中段浮起來）
PW = np.floor(Wn) + 1.0
pipe = (X >= 28) & (X <= 118) & (np.abs(DY - PW) < 0.6) & (Z == ZC - 3)
pipe |= (X >= 28) & (X <= 96) & (np.abs(DY - PW) < 0.6) & (Z == ZC + 2)
put(pipe, DARK, "details")
clamp_ = (X >= 28) & (X <= 118) & ((X - 28) % 10 == 0) & (np.abs(DY - PW) < 0.6) & (Z >= ZC - 4) & (Z <= ZC + 3)
put(clamp_, MID, "details")

# 機鼻下方的感測莢艙
sx, sz = 186, ZC - 8.0
pod = (np.sqrt((X + 0.5 - sx) ** 2 / 4.0 + DY ** 2 + (Z + 0.5 - sz) ** 2) <= 2.6)
put(pod, DARK, "details")

solid = col > 0

# 零件（greeble）：引擎段頂面、背脊兩側、引擎艙頂面；照雜湊撒，左右對稱
rng_boxes = []
for gx in range(26, 132, 3):
    for gdy in range(4, 18, 3):
        r = hsh(gx, gdy, 7)
        if r > 0.30:
            continue
        sx_ = 1 + int(hsh(gx, gdy, 11) * 3.5)
        sy_ = 1 + int(hsh(gx, gdy, 13) * 2.5)
        sz_ = 1 + int(hsh(gx, gdy, 17) * 1.8)
        cc = [DARK, MID, HULL_B, VDARK, DARK][int(hsh(gx, gdy, 19) * 5)]
        rng_boxes.append((gx, gdy, sx_, sy_, sz_, cc))
for (gx, gdy, sx_, sy_, sz_, cc) in rng_boxes:
    if gx + sx_ > 150:
        continue
    y0 = int(math.floor(CY + gdy))                    # 右半邊（+y）那幾欄；左半邊取鏡像 y ↔ NY-1-y
    right = list(range(y0, y0 + sy_))
    for ys in (right, [NY - 1 - v for v in right]):
        for xx in range(gx, gx + sx_):
            for yy in ys:
                # 找這一欄船殼頂面
                zs = np.nonzero(solid[xx, yy, :])[0]
                if len(zs) == 0:
                    continue
                ztop = zs.max()
                for zz in range(ztop + 1, min(NZ, ztop + 1 + sz_)):
                    if col[xx, yy, zz] == 0:
                        col[xx, yy, zz] = cc
                        comp[xx, yy, zz] = SID["details"]

# 引擎艙頂面的零件
for gx in range(30, 86, 4):
    r = hsh(gx, 3, 23)
    if r > 0.55:
        continue
    L = 1 + int(hsh(gx, 3, 29) * 3)
    cc = [DARK, MID, VDARK][int(hsh(gx, 3, 31) * 3)]
    r0 = int(math.floor(CY + NAC_DY))
    for pair in ((r0, r0 + 1), (NY - 1 - r0, NY - 2 - r0)):
        for xx in range(gx, gx + L):
            for yy in pair:
                zs = np.nonzero(col[xx, yy, :])[0]
                if len(zs) == 0:
                    continue
                zt = zs.max() + 1
                if zt < NZ and col[xx, yy, zt] == 0:
                    col[xx, yy, zt] = cc
                    comp[xx, yy, zt] = SID["details"]

# 航行燈：左翼尖紅、右翼尖綠（+y 是右舷 ⇒ 機頭朝 +x、上是 +z 時，+y 在左手邊）
# 右手座標：x 前、z 上 ⇒ y 指向左舷。左舷紅、右舷綠。
ytip = int(math.floor(CY + 58.6))
for (yy, cc) in [(ytip, NAV_RED), (NY - 1 - ytip, NAV_GREEN)]:
    for xx in range(60, 64):
        for zz in (24, 25):
            if 0 <= yy < NY:
                col[xx, yy, zz] = cc
                comp[xx, yy, zz] = SID["details"]
# 尾燈：垂直尾翼頂端後緣
for xx in range(22, 26):
    for yy in (71, 72):
        col[xx, yy, FIN_TOP - 1] = LAMP
        comp[xx, yy, FIN_TOP - 1] = SID["fin"]

# ── 8. 表面處理：面板深淺、面板縫、識別帶、舷窗、座艙玻璃 ─────
solid = col > 0
pad = np.pad(solid, 1)
surface = solid & ~(pad[2:, 1:-1, 1:-1] & pad[:-2, 1:-1, 1:-1] & pad[1:-1, 2:, 1:-1]
                    & pad[1:-1, :-2, 1:-1] & pad[1:-1, 1:-1, 2:] & pad[1:-1, 1:-1, :-2])

is_hull = (comp == SID["hull"]) & (col == HULL_A)
is_wing = (comp == SID["wings"]) & (col == HULL_A)
is_fin = (comp == SID["fin"]) & (col == HULL_A)
paint = surface & (is_hull | is_wing | is_fin)

# 面板：照 (x/9, |y|/7, z/6) 分塊挑深淺；左右對稱
pr = hsh(X // 9, (np.floor(DY) // 7).astype(np.int64), Z // 6)
tone = np.where(pr < 0.62, HULL_A, np.where(pr < 0.80, HULL_B, np.where(pr < 0.95, HULL_C, MID)))
col[paint] = tone[paint]
# 面板縫（船身每 14 格一圈）
seam = surface & (comp == SID["hull"]) & (X % 14 == 0) & (col != MID)
col[seam] = MID
# 主翼：前緣深色、翼尖段紅帶（只上面）
wing_s = surface & (comp == SID["wings"])
col[wing_s & (X >= le - 2.5)] = DARK
col[wing_s & (s >= 0.72) & (s <= 0.80) & (Z + 0.5 >= zw + th - 1)] = RED
# 尾翼：橘帶
fin_s = surface & (comp == SID["fin"]) & (col != LAMP)
col[fin_s & (f >= 0.55) & (f <= 0.68)] = ORANGE
# 船身側面的紅色細帶（中段，靠近腰線）
belt = surface & (comp == SID["hull"]) & (X >= 96) & (X <= 196) & (np.abs(Z - (ZC + 1)) < 0.6) & (DY > 6)
col[belt] = RED
# 舷窗：中段兩側一排
win = surface & (comp == SID["hull"]) & (X >= 100) & (X <= 136) & ((X - 100) % 5 < 2) & (Z == ZC + 4) & (DY > 8)
col[win] = WINDOW
# 引擎段側面的通風口
vent = surface & (comp == SID["hull"]) & (X >= 30) & (X <= 64) & ((X - 30) % 4 == 0) & (Z >= ZC - 6) & (Z <= ZC - 1) & (DY > 15)
col[vent] = VDARK
# 船尾面：深色板
aft = surface & (comp == SID["hull"]) & (X <= XS + 1)
col[aft] = DARK
# 座艙：前段玻璃、框
ck_s = surface & (comp == SID["cockpit"]) & (Z + 0.5 > top_z)
glass = ck_s & (X >= 152)
frame = glass & (((X - 152) % 6 == 0) | (DY < 1))
col[glass] = GLASS
col[frame] = DARK
# 燒痕：引擎噴嘴附近、船尾上方一些不對稱的髒污
burn = surface & (comp == SID["hull"]) & (X <= 34) & (hsh(X // 2, Y // 2, Z // 2) < 0.18)
col[burn] = VDARK

# ── 輸出 ───────────────────────────────────────────────
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "out")
os.makedirs(out, exist_ok=True)
summary = {"size": [NX, NY, NZ], "meters_per_voxel": 0.1, "stages": {}, "emissive": EMISSIVE}
tot = 0
for name in STAGES:
    m = (comp == SID[name]) & (col > 0)
    xs, ys, zs = np.nonzero(m)
    cs = col[xs, ys, zs]
    path = os.path.join(out, "stage_%d_%s.txt" % (SID[name], name))
    with open(path, "w", encoding="utf-8", newline="\n") as fo:
        fo.write("# 餘暉號 stage %s（at=0,0,0；x,y,z,color）\n" % name)
        for a, b_, c_, d in zip(xs, ys, zs, cs):
            fo.write("%d,%d,%d,%d\n" % (a, b_, c_, d))
    cnt = {int(k): int(v) for k, v in zip(*np.unique(cs, return_counts=True))}
    summary["stages"][name] = {"file": os.path.basename(path), "voxels": int(len(xs)), "colors": cnt}
    tot += len(xs)
assert tot == int((col > 0).sum())
summary["total"] = tot
occ = np.argwhere(col > 0)
summary["bbox"] = [occ.min(0).tolist(), occ.max(0).tolist()]
# 對稱讀數（顏色不算）：形狀左右鏡像差幾格
mir = solid[:, ::-1, :]
summary["mirror_shape_diff"] = int((solid != mir).sum())
with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as fo:
    json.dump(summary, fo, ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False))
