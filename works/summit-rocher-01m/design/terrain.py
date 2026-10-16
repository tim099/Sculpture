# 岩堡港 地形與碼頭（TASK-0580 第三階段）：site_height.npy ＋ plan.json ⇒ 兩件子作品的格子清單＋讀數。
# 用法：python -I -X utf8 -B terrain.py <design 資料夾>
#   · 地形（-terrain，關聯 meta render=smooth）：只鋪表層殼 —— 每一欄從地面往下 T 格；跟鄰欄（上下左右）有高低差 ⇒ 往下補到鄰欄那麼低，
#     鄰欄是海、碼頭外、作品邊 ⇒ 補到 z_floor（海面下 2 m）⇒ 殼連成一片、不露縫，底下是空的（不做實心：實心約 5 千萬格）。
#   · 碼頭（-quay，方塊、不平滑）：石砌碼頭（牆面到海面下 2 m；只留 2 格厚的外殼）＋兩座木棧橋（樁、橫梁、面板）。子作品自己的座標，原點 QO。
#   · 高度一律讀 site_height.npy（draft_site.py 產的），⛔ 不再用算式重算第二遍。
#   · 輸出：masks/terrain/{terrain,quay}.vox.txt（x,y,z,color；照座標排序）、verify_terrain.json。重跑逐位元組相同。
import sys, os, json
import numpy as np

D = sys.argv[1]
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
S, PAL = plan['site'], plan['palette']
H = np.load(os.path.join(D, 'site_height.npy')).astype(np.int32)          # 每一欄地面上第一層空氣的 z；海 ＝ −1
NX, NY = H.shape
ZSEA = S['z_sea']
ZF = ZSEA - 20                                                            # 殼往下補到的最低處：海面下 2 m（海是 80% 不透明，看得到一點岸邊往下）
T = 2                                                                     # 殼厚（格）
Q = S['quay']
QM = np.zeros_like(H, bool)
QM[Q['x0']:Q['x1'], Q['y_face']:Q['promenade_y1']] = True                 # 碼頭（含步道）那幾欄歸 -quay
LAND = (H >= 0) & ~QM

# ── 地面的顏色（每一欄頂面那一格）──
def hash2(x, y, s):
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return (h ^ (h >> 16)) / 4294967296.0

def vnoise(sc, seed):
    gx, gy = NX // sc + 2, NY // sc + 2
    g = np.array([[hash2(i, j, seed) for j in range(gy)] for i in range(gx)])
    xi, yi = np.arange(NX) / sc, np.arange(NY) / sc
    x0, y0 = xi.astype(int), yi.astype(int)
    fx, fy = (xi - x0)[:, None], (yi - y0)[None, :]
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = g[x0][:, y0], g[x0 + 1][:, y0]
    c, d = g[x0][:, y0 + 1], g[x0 + 1][:, y0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

N = 0.65 * vnoise(40, 1) + 0.35 * vnoise(13, 2)
top = np.where(N > 0.6, PAL['grass_dark'], PAL['grass']).astype(np.int32)
top[(H >= 0) & (H < ZSEA + 6)] = PAL['sand']
T_ = S['town']
xs, ys = np.arange(NX)[:, None], np.arange(NY)[None, :]
town = (xs >= T_['x0']) & (xs < T_['x1']) & (ys >= S['terraces'][0]['y0']) & (ys < S['terraces'][-1]['y1'])
top[town] = PAL['dirt']
for st in S['streets']:
    if st['kind'] != 'promenade':
        top[st['x0']:st['x1'], st['y0']:st['y1']] = PAL['dirt']
P = S['fort_path']                                                        # 上岩堡的小徑：寬 8 格的泥路
for (ax, ay), (bx, by) in zip(P, P[1:]):
    L = max(abs(bx - ax), abs(by - ay))
    for i in range(L + 1):
        cx, cy = ax + (bx - ax) * i / L, ay + (by - ay) * i / L
        top[int(cx) - 4:int(cx) + 4, int(cy) - 4:int(cy) + 4] = PAL['dirt']
sub = np.where(top == PAL['sand'], PAL['sand'], PAL['dirt'])              # 頂面底下那幾格（只有坎、岸邊露得出來）

# ── 擋土牆（-walls，方塊；第五階段 2026-10-16）：鎮的平台與街是從坡上切下去的 ⇒ 切面外側高出 ≥ WT 格的地方砌石牆 ──
#   牆 ＝ 不是鎮／街的陸地欄、離鎮／街 ≤ WB 格、比窗內最低的鎮／街欄高 ≥ WT 格；從那個低處往下埋 2 格、砌到地面上 2 格（壓頂）。
#   那幾欄地形讓出來（-terrain 不鋪），鄰欄的殼只補到牆頂 ⇒ 兩件不重疊。
WB, WT = 4, 4
LOW = town.copy()
for st in S['streets']:
    if st['kind'] != 'promenade':
        LOW[st['x0']:st['x1'], st['y0']:st['y1']] = True
LOW &= LAND & ~QM
BIG = 10 ** 6
lowv = np.pad(np.where(LOW, H, BIG), WB, constant_values=BIG)
LOWMIN = np.full_like(H, BIG)
for dx in range(2 * WB + 1):
    for dy in range(2 * WB + 1):
        LOWMIN = np.minimum(LOWMIN, lowv[dx:dx + NX, dy:dy + NY])
WALL = LAND & ~LOW & ~QM & (LOWMIN < BIG) & (H - LOWMIN >= WT)

# ── 殼：每一欄 z 從 lo 到 H−1 ──
NB = np.where(LAND, H, ZF)
NB[QM] = Q['z_top']                                                       # 貼著碼頭的那幾欄只補到碼頭面
NB[WALL] = H[WALL] + 2                                                    # 貼著擋土牆的那幾欄只補到牆頂
LAND = LAND & ~WALL                                                       # 牆那幾欄地形讓出來
pad = np.pad(NB, 1, constant_values=ZF)                                   # 作品邊 ⇒ 補到 z_floor（像切開的沙盤）
nmin = np.minimum.reduce([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]])
LO = np.maximum(np.minimum(H - T, nmin), ZF)

out_t = []
for x in range(NX):
    for y in np.nonzero(LAND[x])[0]:
        h, lo, c0, c1 = H[x, y], LO[x, y], top[x, y], sub[x, y]
        for z in range(lo, h):
            out_t.append((x, int(y), z, int(c0 if z == h - 1 else c1)))

# ── 碼頭與棧橋（子作品座標：原點 QO）──
y_lo = min(p['y_end'] for p in S['piers'])
QO = (Q['x0'], y_lo, ZF)
cells = {}
def put(x, y, z, c):
    cells[(x - QO[0], y - QO[1], z - QO[2])] = c
for x in range(Q['x0'], Q['x1']):                                         # 石砌碼頭：頂面淺色（壓頂石 6 格寬、每 12 格一道縫），牆面每 6 層一道灰縫、上下層錯縫
    for y in range(Q['y_face'], Q['promenade_y1']):
        for z in range(ZF, Q['z_top']):
            if not (y < Q['y_face'] + 2 or y >= Q['promenade_y1'] - 2 or x < Q['x0'] + 2 or x >= Q['x1'] - 2 or z >= Q['z_top'] - 2):
                continue                                                  # 只留外殼（牆面、兩端、背面、頂面各 2 格厚；底下開口 ⇒ 不是封閉空腔）
            if z == Q['z_top'] - 1:
                coping = y < Q['y_face'] + 6
                c = PAL['stone'] if coping and (x - Q['x0']) % 12 == 0 else PAL['stone_light']
            else:
                face = y == Q['y_face'] or x in (Q['x0'], Q['x1'] - 1)
                joint = (Q['z_top'] - 1 - z) % 6 == 0 or ((x - Q['x0'] + (0 if ((Q['z_top'] - 1 - z) // 6) % 2 else 9)) % 18 == 0)
                c = PAL['stone_light'] if face and joint else PAL['stone']
            put(x, y, z, c)
for p in S['piers']:                                                      # 木棧橋：兩排樁（3×3、每 30 格）、樁頭橫梁（2 格高）、面板 2 格厚（橫鋪、每 3 格一道暗縫）
    x0, x1, zd = p['x'], p['x'] + p['w'], p['z_deck']
    for y in range(p['y_end'], Q['y_face']):
        for x in range(x0, x1):
            for z in (zd - 2, zd - 1):
                put(x, y, z, PAL['wood_grey'] if (y - p['y_end']) % 3 == 0 and z == zd - 1 else PAL['wood'])
    for yp in range(p['y_end'] + 1, Q['y_face'] - 2, 30):
        for x in range(x0, x1):
            for y in (yp, yp + 1, yp + 2):
                for z in (zd - 4, zd - 3):
                    put(x, y, z, PAL['timber_dark'])
        for xp in (x0, x1 - 3):
            for x in range(xp, xp + 3):
                for y in range(yp, yp + 3):
                    for z in range(ZF, zd - 4):
                        put(x, y, z, PAL['timber_dark'])
out_q = sorted((k[0], k[1], k[2], c) for k, c in cells.items())

# ── 擋土牆＋Rue du Fort 出鎮的石階（-walls，方塊；原點 WO ＝ 外框最小角）──
#   毛石：沿牆每 6 格一塊、每 4 層一皮、上下皮錯 3 格；灰縫淺石；頂上 2 格（地面以上）壓頂淺石。
#   石階：Rue du Fort 在鎮的背面（y 640）一步從 z 96 跳到街面 ⇒ 鎮裡那段最後 40 格（y 600–639）砌 10 級、每級 3 格高 4 格深，頂級接街面。
wcells = {}
RUBBLE = (PAL['stone'], PAL['stone'], PAL['rock'], PAL['stone_light'])
for x, y in zip(*np.nonzero(WALL)):
    h, lo = int(H[x, y]), int(LOWMIN[x, y]) - 3
    for z in range(lo, h + 2):
        u = int(x) + int(y) + (3 if (z // 4) % 2 else 0)
        if z >= h:
            c = PAL['stone_light']
        elif u % 6 == 0 or z % 4 == 0:
            c = PAL['stone_light']
        else:
            c = RUBBLE[int(hash2(u // 6, z // 4, 7) * len(RUBBLE))]
        wcells[(int(x), int(y), z)] = c
RF = next(st for st in S['streets'] if st['name'] == 'Rue du Fort')
Y_TOWN = S['ground']['y_town_top']
z_town = int(H[RF['x0'], Y_TOWN - 1])
for x in range(RF['x0'], RF['x1']):
    z_top = int(H[x, Y_TOWN])
    for k in range(10):
        zk = z_town + round((z_top - z_town) * (k + 1) / 10)
        for y in range(Y_TOWN - 40 + 4 * k, Y_TOWN - 36 + 4 * k):
            for z in range(z_town, zk):
                nose = z == zk - 1 and y == Y_TOWN - 40 + 4 * k
                wcells[(x, y, z)] = PAL['stone_light'] if nose else PAL['stone']
WO = tuple(int(v) for v in np.array(list(wcells)).min(0))
out_w = sorted((k[0] - WO[0], k[1] - WO[1], k[2] - WO[2], c) for k, c in wcells.items())

os.makedirs(os.path.join(D, 'masks', 'terrain'), exist_ok=True)
for nm, arr in (('terrain', out_t), ('quay', out_q), ('walls', out_w)):
    with open(os.path.join(D, 'masks', 'terrain', nm + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 岩堡港 %s（terrain.py 產；x,y,z,color）\n' % nm)
        f.write(''.join('%d,%d,%d,%d\n' % t for t in arr))

def bbox(arr):
    a = np.array([t[:3] for t in arr])
    return [int(v) for v in a.max(0) + 1]
colors = lambda arr: {str(k): int(v) for k, v in zip(*np.unique([t[3] for t in arr], return_counts=True))}
R = {'T': T, 'z_floor': ZF, 'z_sea': ZSEA,
     'terrain': {'voxels': len(out_t), 'bbox': bbox(out_t), 'colors': colors(out_t), 'columns': int(LAND.sum()), 'origin': [0, 0, 0], 'render': 'smooth'},
     'quay': {'voxels': len(out_q), 'bbox': bbox(out_q), 'colors': colors(out_q), 'origin': list(QO)},
     'walls': {'voxels': len(out_w), 'bbox': bbox(out_w), 'colors': colors(out_w), 'origin': list(WO), 'wall_columns': int(WALL.sum()),
               'wall_rule': {'band': WB, 'min_rise': WT}, 'rue_du_fort_steps': 10}}
with open(os.path.join(D, 'verify_terrain.json'), 'w', encoding='utf-8', newline='\n') as fo:
    json.dump(R, fo, ensure_ascii=False, indent=1, sort_keys=True); fo.write('\n')
print(json.dumps(R, ensure_ascii=False))
