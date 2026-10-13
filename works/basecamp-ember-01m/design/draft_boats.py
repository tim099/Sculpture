# 餘燼號 階段二十 小艇與艇架（plan.json boats_build；外觀，自由設計）
#   船腰開口（上甲板 x ≈ 372..583、y 125..195，兩側是走道甲板）：
#   · 艇架：skid beams 橫跨開口、擱在開口兩邊欄杆的扶手（z 135）上（甲板-spar 子作品的格，世界座標）。
#     v1 擱在走道甲板（z 128..130）⇒ 撞到欄杆柱 18 格 ⇒ 抬到扶手上。
#   · 小艇：一艘 9 m × 2.6 m 的 cutter（0.05 m／格子作品 -boat，縮 0.5 當外部模型），兩舷各一艘（P 舷 mirror=y），擱在艇架上。
#     艇：外殼黑（舷頂一條暗紅帶＋金線）、艇內木色、龍骨、舷緣、坐板 5 條、收著 4 支槳；船頭尖、船尾方（transom）。尺寸照一般比例，未查證。
#   每一格／模型格心＋八角：不落在「組裝件＋spar carronade＋已擺的模型」實心裡；艇架在扶手那兩格正下方要是扶手。
#   ⇒ masks/boats/{boat,skids}.vox.txt、boats_placement.json、verify_boats.json
# 用法：python -I draft_boats.py <design 資料夾>
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import export_hidden  # noqa: E402
import place_guns as PG                   # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
P = plan['boats_build']
B = P['boat']
L, BW, DEP = B['length'], B['beam'], B['depth']
K = P['colors']
OUT = os.path.join(D, 'masks', 'boats')
os.makedirs(OUT, exist_ok=True)


# ───────── 艇（子作品座標：x 沿艇長、船頭 +x；y 橫向；z 上，z 0 ＝ 龍骨底）─────────
def half_breadth(u):
    """u 0（船尾 transom）→ 1（船頭）的半寬比例"""
    if u <= 0.55:
        return B['transom'] + (1 - B['transom']) * math.sin(u / 0.55 * math.pi / 2)
    return math.cos((u - 0.55) / 0.45 * math.pi / 2) ** 0.75


def hull_in(x, y, z, shrink=0.0):
    """格心 (x,y,z) 在不在艇殼外形裡（shrink ＝ 往內縮幾格 ⇒ 內面）"""
    u = (x + 0.5) / L
    if u < 0 or u > 1:
        return False
    zk = z + 0.5 - B['keel']                    # 龍骨以上
    if zk < shrink or zk > DEP:
        return False
    sheer = DEP + B['sheer'] * (2 * u - 1) ** 2  # 舷弧：兩頭翹
    if zk > sheer:
        return False
    hb = BW / 2.0 * half_breadth(u) * (zk / DEP) ** 0.35 - shrink
    if u * L < shrink or (1 - u) * L < shrink * 2:
        return False
    return abs(y + 0.5 - BW / 2.0) <= hb


def boat_cell(x, y, z):
    cy = BW / 2.0
    dy = abs(y + 0.5 - cy)
    u = (x + 0.5) / L
    # 龍骨
    if z < B['keel'] and dy <= 1.0 and 0.03 <= u <= 0.97:
        return K['black']
    if not hull_in(x, y, z):
        return 0
    zk = z + 0.5 - B['keel']
    sheer = DEP + B['sheer'] * (2 * u - 1) ** 2
    inside = hull_in(x, y, z, shrink=B['shell'])
    if not inside:                              # 殼
        if zk > sheer - 1.0:
            return K['gunwale']                 # 舷緣
        if zk > sheer - 1.0 - B['strake']:
            return K['gold'] if zk <= sheer - B['strake'] else K['red']
        return K['black']
    # 艇內：底板、坐板、槳；其他是空的
    if zk < B['shell'] + 1.0:
        return K['wood']                        # 底板
    for t in B['thwarts_u']:
        if abs(u - t) * L <= 2.0 and abs(zk - B['thwart_z']) <= 1.0:
            return K['thwart']
    for oy in B['oars_y']:                      # 槳：擱在坐板上、沿艇長
        if abs(y + 0.5 - (cy + oy)) <= 1.0 and B['oar_u'][0] <= u <= B['oar_u'][1] and abs(zk - (B['thwart_z'] + 2.0)) <= 1.0:
            return K['oar']
    return 0


size = (L, BW, B['keel'] + DEP + B['sheer'] + 2)
boat = [(x, y, z, c) for x in range(size[0]) for y in range(size[1]) for z in range(size[2]) for c in [boat_cell(x, y, z)] if c]
bs = {(x, y, z): c for x, y, z, c in boat}
asym = sum(1 for (x, y, z), c in bs.items() if bs.get((x, size[1] - 1 - y, z)) != c)
G = np.zeros(size, bool)
for x, y, z, c in boat:
    G[x, y, z] = True
_, ncomp = ndimage.label(G)
assert asym == 0 and ncomp == 1, ('艇不對稱或散開', asym, ncomp)

# ───────── 現況 ─────────
a = export_hidden(P['assembly'], [])
skid_cells_planned = []
for sx in P['skids']['x']:
    for x in range(sx - 1, sx + 2):
        for y in range(P['skids']['y'][0], P['skids']['y'][1] + 1):
            for z in range(P['skids']['z'][0], P['skids']['z'][1] + 1):
                skid_cells_planned.append((x, y, z))
S = {(int(x), int(y), int(z)) for x, y, z, c in a}
if len(S) == P['assembly_voxels'] + len(skid_cells_planned) and set(skid_cells_planned) <= S:
    S -= set(skid_cells_planned)                 # 重跑：艇架已經落了 ⇒ 扣掉本階段自己的格
assert len(S) == P['assembly_voxels'], ('組裝件（這一階段之前）對不上', len(S), len(a))
Gw = np.zeros((PG.X1 - PG.X0, 320, PG.Z1 - PG.Z0), bool)
for x, y, z in S:
    if PG.X0 <= x < PG.X1 and PG.Z0 <= z < PG.Z1:
        Gw[x - PG.X0, y, z - PG.Z0] = True
GB = plan['guns_build']
for r in json.load(open(os.path.join(D, 'guns_placement.json'), encoding='utf-8'))['rows']:
    if r['deck'] != 'spar':
        continue
    t = GB['types'][r['type']]
    src = os.path.join(D, t['cells']) if t['cells'].startswith('masks/') else t['cells']
    g = PG.Gun(r['type'], t['work'], PG.load_cells(src), t['scale'], t['pivot'], t['muzzle'], t['meta'])
    w = np.floor(g.world(g.samples, r['at'], r['phi'], r['side'] == 'P')).astype(int)
    Gw[w[:, 0] - PG.X0, w[:, 1], w[:, 2] - PG.Z0] = True

# 艇架：每格要是空氣（含砲模型）；兩端（開口外）正下方要是甲板
skid_hit = [c for c in skid_cells_planned if Gw[c[0] - PG.X0, c[1], c[2] - PG.Z0]]
assert not skid_hit, ('艇架撞到東西', len(skid_hit), skid_hit[:5])
z0 = P['skids']['z'][0]                      # 艇架擱在船腰兩邊欄杆的扶手上：每根梁、每個 x、兩邊 rest_y 那一格正下方要是實心
ends = [(x, y) for sx in P['skids']['x'] for x in range(sx - 1, sx + 2) for y in P['skids']['rest_y']]
unsupported = [(x, y) for x, y in ends if (x, y, z0 - 1) not in S]
assert not unsupported, ('艇架底下不是扶手', unsupported[:5])
for c in skid_cells_planned:
    Gw[c[0] - PG.X0, c[1], c[2] - PG.Z0] = True

# 小艇：擱在艇架頂上（龍骨底 ＝ 艇架頂 ＋ 1）；格心＋八角不落在實心
bg = PG.Gun('boat', P['work'], [list(c[:3]) for c in boat], B['scale'], B['pivot'], B['pivot'], {})
rows = []
for side, yc in (('S', P['y_s']), ('P', 321 - P['y_s'])):
    at = (P['x'], yc, P['skids']['z'][1] + 1)
    W = bg.world(bg.samples, at, 0, side == 'P')
    n = int(PG.hits(Gw, W).sum())
    assert n == 0, ('小艇撞到東西', side, n)
    w = np.floor(W).astype(int)
    Gw[w[:, 0] - PG.X0, w[:, 1], w[:, 2] - PG.Z0] = True
    rows.append({'name': '小艇-' + side, 'side': side, 'at': [float(v) for v in at], 'mirror': 'y' if side == 'P' else '',
                 'box': [[round(float(v), 2) for v in W.min(0)], [round(float(v), 2) for v in W.max(0)]]})

files = {}
for name, cells in (('boat', boat), ('skids', [(x, y, z, P['skids']['color']) for x, y, z in skid_cells_planned])):
    txt = ''.join('%d,%d,%d,%d\n' % c for c in cells)
    open(os.path.join(OUT, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
    files[name] = {'file': 'masks/boats/%s.vox.txt' % name, 'cells': len(cells), 'sha256': hashlib.sha256(txt.encode()).hexdigest()}
cnt = {}
for *_, c in boat:
    cnt[c] = cnt.get(c, 0) + 1
json.dump({'boat_work': P['work'], 'deck_work': P['deck_work'], 'scale': B['scale'], 'pivot': B['pivot'], 'boats': rows},
          open(os.path.join(D, 'boats_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
json.dump({'boat': {'size': list(size), 'voxels': len(boat), 'colors': cnt, 'asym_y': asym, 'components': ncomp},
           'skids': {'cells': len(skid_cells_planned), 'ends_supported': len(ends)}, 'files': files,
           'assembly_voxels_after': P['assembly_voxels'] + len(skid_cells_planned)},
          open(os.path.join(D, 'verify_boats.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('艇', size, len(boat), cnt, '艇架', len(skid_cells_planned))
for r in rows:
    print(r)
