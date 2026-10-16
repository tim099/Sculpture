# 哨兵號（莫尼特號的火力加強改裝船；TASK-0658）產生程式 —— 改裝船只存「差」：原船整艘是一條關聯（原船 → meadow-monitor-01m-assembly），
# 這裡只算新加的部件與挖格子的遮罩（造船規格 §11）。座標照原船：0.1 m／格、X 船長（船頭 +X）、Y 船寬（中線 y=65）、Z 高度（z=0 ＝ 龍骨底）；
# 主甲板最上一層 z 34（走路格 z 35）。每個部件的框 ＝ 改裝船的框（544×131×128），關聯 at 0,0,0；遮罩的框 ＝ 原船的框（544×131×80）。
# 用法：python -I -X utf8 -B gen_sentinel.py <輸出資料夾>
import sys, os, json, math
import numpy as np

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
NX, NY, NZ = 544, 131, 128
YC = 65
ZD = 34                       # 主甲板最上一層（鐵板）
ZFL = ZD + 1                  # 走路格
IRON_BLACK, IRON, LEAD, BRASS, OAK_D = 36, 73, 146, 180, 104

ORIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'meadow-monitor-01m-assembly')
x = np.arange(NX)[:, None, None]; y = np.arange(NY)[None, :, None]; z = np.arange(NZ)[None, None, :]
X3, Y3, Z3 = np.broadcast_arrays(x, y, z)

# ── 速射砲（gura 三叉戟號的三管速射砲 gura-tridente-01m-gun-trident，0.05 m ⇒ scale 0.5）──
# 砲的作品座標：砲管沿 +y（砲口 y 71、耳軸 y 30、砲尾 y 8），z 0 ＝ 底。放法：模型的 pivot (16.5, 34, 0) 落在 at；rotate 照砲口朝外。
# 砲井：主甲板挖半徑 GW、深 2 格（z 33–34：鐵板＋一層木）⇒ 砲座低 0.2 m、砲班站在井裡（走路格 z 33，在甲板 meta 的 −2..+3 裡）。
# 圍欄：半徑 RW0..RW1、高 2 格的矮鐵圍欄（砲尾離 pivot 17 格 ⇒ 圍欄 18 格起，轉一整圈不碰），朝船內留 GAP 格寬的出入口。
GW, RW0, RW1, RH, GAP = 9, 18, 19, 2, 5
#        名字      x    y    朝向（砲口）rotate z   射界（相對砲口朝外的那一邊，度；左正）
GUNS = [('速射砲-艏', 503, 65, 'fwd', -90, '-150,150', '-140,140'),
        ('速射砲-中S', 228, 31, 'S', 180, '-110,110', '-100,100'),
        ('速射砲-中P', 228, 99, 'P', 0, '-110,110', '-100,100'),
        ('速射砲-艉S', 150, 33, 'S', 180, '-110,110', '-100,100'),
        ('速射砲-艉P', 150, 97, 'P', 0, '-110,110', '-100,100')]

parts = {}


def put(part, mask, color):
    """部件 part 在 mask 的格放 color（同一部件後放的蓋過先放的；不同部件不准重疊，最後檢查）。"""
    a = parts.setdefault(part, np.zeros((NX, NY, NZ), np.uint8))
    a[mask] = color


# ── 遮罩：砲井 ──
pit = np.zeros((NX, NY, NZ), bool)
for nm, gx, gy, face, rot, arc, fire in GUNS:
    r = np.hypot(X3 - gx, Y3 - gy)
    pit |= (r <= GW) & (Z3 >= ZD - 1) & (Z3 <= ZD)
mask = np.zeros((NX, NY, 80), np.uint8)
mask[pit[:, :, :80]] = 1

# ── 砲座圍欄 ──
for nm, gx, gy, face, rot, arc, fire in GUNS:
    r = np.hypot(X3 - gx, Y3 - gy)
    ring = (r >= RW0) & (r < RW1 + 1) & (Z3 >= ZFL) & (Z3 < ZFL + RH)
    if face == 'fwd':
        door = (X3 < gx) & (np.abs(Y3 - gy) <= GAP // 2)              # 往船尾那一邊（司令塔那頭）開口
    else:
        door = (np.abs(X3 - gx) <= GAP // 2) & ((Y3 > gy) if face == 'S' else (Y3 < gy))   # 朝船內那一邊開口
    put('mounts', ring & ~door, IRON_BLACK)
    put('mounts', ring & ~door & (Z3 == ZFL + RH - 1) & (r >= RW1), LEAD)   # 頂緣一圈鉛灰（看得出圍欄的輪廓）

# ── 司令塔（取代方形駕駛塔；Passaic 級以後的做法是圓的、加高）──
TX, TY, TR, TT, TZ1 = 469, 65, 11, 2, ZFL + 18          # 外半徑 11（2.2 m）、牆 2 格、塔頂 z 52
r = np.hypot(X3 - TX + 0.5, Y3 - TY + 0.5)
wall = (r <= TR) & (r > TR - TT) & (Z3 >= ZFL) & (Z3 < TZ1 - 2)
slit = (Z3 >= TZ1 - 5) & (Z3 <= TZ1 - 4)                 # 觀察縫：塔頂下面一圈 0.2 m
ang = np.degrees(np.arctan2(Y3 - TY + 0.5, X3 - TX + 0.5)) % 360
posts = (np.abs(((ang + 30) % 60) - 30) < 7)             # 六根柱子
put('conning', wall & ~(slit & ~posts), IRON_BLACK)
roof = (r <= TR + 0.6) & (Z3 >= TZ1 - 2) & (Z3 < TZ1)
put('conning', roof, IRON_BLACK)
dome = (r <= 4) & (Z3 == TZ1)                             # 頂上一個小觀察圓頂
put('conning', dome, IRON)
door_c = (X3 < TX - TR + TT + 1) & (np.abs(Y3 - TY) <= 2) & (Z3 >= ZFL) & (Z3 < ZFL + 15)   # 往船尾的門（1.5 m 高、0.5 m 寬；人從主甲板進出）
parts['conning'][door_c & (r > TR - TT - 1)] = 0

# ── 訊號桅 ──
MX, MY, MZ1 = 445, 65, 112
rm = np.hypot(X3 - MX, Y3 - MY)
put('mast', (rm <= 1.2) & (Z3 >= ZFL) & (Z3 < MZ1), IRON)
put('mast', (rm <= 2.2) & (Z3 >= ZFL) & (Z3 < ZFL + 3), IRON_BLACK)                          # 桅座
put('mast', (rm <= 4.2) & (rm > 1.2) & (Z3 == 88), OAK_D)                                   # 瞭望台
put('mast', (rm <= 4.6) & (rm > 3.6) & (Z3 >= 89) & (Z3 <= 90), IRON_BLACK)                 # 瞭望台欄杆
put('mast', (np.abs(X3 - MX) <= 0) & (np.abs(Y3 - MY) <= 14) & (Z3 == 100), OAK_D)           # 訊號桁
put('mast', (rm <= 1.5) & (Z3 >= MZ1) & (Z3 < MZ1 + 2), BRASS)                              # 桅頂的球

# ── 檢查：部件之間不重疊、新部件不碰原船（原船的格 ＝ 莫尼特號組裝件匯出的清單，挖掉砲井之後）──
names = sorted(parts)
occ = np.zeros((NX, NY, NZ), np.uint8)
for nm in names:
    m = parts[nm] > 0
    if (occ[m] > 0).any(): raise SystemExit('部件 %s 跟前面的部件重疊 %d 格' % (nm, int((occ[m] > 0).sum())))
    occ[m] = 1
orig = None
src = os.environ.get('SENTINEL_ORIG_LIST')
if src and os.path.exists(src):
    rows = [l.split(',') for l in open(src, encoding='utf-8') if l[:1].isdigit()]
    a = np.array(rows, dtype=np.int32)
    orig = np.zeros((NX, NY, NZ), bool); orig[a[:, 0], a[:, 1], a[:, 2]] = True
    orig[:, :, :80] &= ~(mask > 0)
hits = {}
if orig is not None:
    for nm in names:
        hits[nm] = int((orig & (parts[nm] > 0)).sum())

# ── 寫出 ──
def write_list(fn, arr, off=(0, 0, 0)):
    xs, ys, zs = np.nonzero(arr)
    with open(os.path.join(OUT, fn), 'w') as f:
        for a_, b_, c_ in zip(xs.tolist(), ys.tolist(), zs.tolist()):
            f.write('%d,%d,%d,%d\n' % (a_, b_, c_, int(arr[a_, b_, c_])))
    return len(xs)

counts = {nm: write_list('part_%s.txt' % nm, parts[nm]) for nm in names}
counts['carve'] = write_list('part_carve.txt', mask)
models = []
for nm, gx, gy, face, rot, arc, fire in GUNS:
    models.append({'name': nm, 'work': 'gura-tridente-01m-gun-trident', 'at': [gx + 0.5, gy + 0.5, ZD - 1], 'pivot': [16.5, 34, 0], 'rotate': [0, 0, rot], 'scale': [0.5, 0.5, 0.5],
                   'meta': {'kind': 'gun', 'gun': 'trident', 'barrels': 3, 'deck': 'main', 'side': {'fwd': 'C', 'S': 'S', 'P': 'P'}[face], 'mount': 'turret', 'arc': arc, 'fire': fire, 'rate': 40, 'pivot': 11}})
wheel = [{'name': '舵輪', 'work': 'basecamp-frigate-constitution-01m-wheel', 'at': [TX + 0.5, TY + 0.5, ZFL], 'pivot': [50, 52, 0], 'scale': [0.07, 0.07, 0.07],
          'meta': {'kind': 'wheel', 'spin': 'rudder', 'spin_k': 540, 'spin_lag': 0.6}},
         {'name': '舵輪座', 'work': 'basecamp-frigate-constitution-01m-wheel-stand', 'at': [TX + 0.5, TY + 0.5, ZFL], 'pivot': [50, 52, 0], 'scale': [0.07, 0.07, 0.07], 'meta': {'kind': 'wheel_stand'}}]
# ── 備便彈藥櫃（ready-use locker）：速射砲的火藥 —— 原船唯一的彈藥庫從砲塔底下的艙口吊上去（hoist），取用點在砲塔那一圈裡，
#    甲板上的砲走不進去（TASK-0655）⇒ 甲板上放兩座裝甲彈藥櫃，各 4 桶（kind=magazine，沒有 hoist ⇒ 遊戲在旁邊找取用點）。
#    一件小作品（框 14×14×9、櫃底 z 0），關聯兩次（at 照原船座標）。打中會殉爆 —— 露天的備便彈藥本來就是這個代價。
LX, LY, LZ = 14, 14, 9
lk = np.zeros((LX, LY, LZ), np.uint8)
lx, ly, lz = np.meshgrid(np.arange(LX), np.arange(LY), np.arange(LZ), indexing='ij')
shell = (lx == 0) | (lx == LX - 1) | (ly == 0) | (ly == LY - 1) | (lz == 0)
lk[shell & (lz < LZ - 1)] = IRON_BLACK
lk[lz == LZ - 1] = LEAD                                                       # 蓋子
lk[(lz == LZ - 1) & (np.abs(lx - LX / 2 + 0.5) <= 1) & ((ly == 2) | (ly == LY - 3))] = BRASS   # 兩個提把
counts['locker'] = write_list('part_locker.txt', lk)
LOCKERS = [('彈藥櫃-前', 388, 58, 'fore'), ('彈藥櫃-後', 113, 58, 'aft')]
kegs = [{'name': '桶-%d' % (i + 1), 'work': 'basecamp-frigate-constitution-01m-powder-barrel', 'at': [kx, ky, 1], 'pivot': [11, 11, 0], 'scale': [0.2, 0.2, 0.2],
         'meta': {'kind': 'powder', 'powder_lb': 100}} for i, (kx, ky) in enumerate([(4.5, 4.5), (9.5, 4.5), (4.5, 9.5), (9.5, 9.5)])]
lockers = [{'name': nm, 'at': [lx_, ly_, ZFL], 'meta': {'kind': 'magazine', 'pos': pos, 'material': 'iron'}} for nm, lx_, ly_, pos in LOCKERS]
if orig is not None:
    for nm, lx_, ly_, pos in LOCKERS:
        hits[nm] = int(orig[lx_:lx_ + LX, ly_:ly_ + LY, ZFL:ZFL + LZ].sum()) + sum(int((parts[p][lx_:lx_ + LX, ly_:ly_ + LY, ZFL:ZFL + LZ] > 0).sum()) for p in names)

json.dump({'counts': counts, 'hits_orig': hits, 'guns': models, 'wheel': wheel, 'kegs': kegs, 'lockers': lockers}, open(os.path.join(OUT, 'sentinel_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({'counts': counts, 'hits_orig': hits}, ensure_ascii=False))
