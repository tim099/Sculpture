# 岩堡港 岩堡（TASK-0580 第五階段，2026-10-16）：site_height.npy ＋ plan.json ⇒ 兩件子作品的格子清單＋砲的擺放＋讀數。
# 用法：python -I -X utf8 -B fort.py <design 資料夾>
#   · -rock（方塊）：9 m 的岩（實心算形狀、只留 3 格殼；底下開口坐在平台上）＋鑿在南面的石階（20 級、每級 3 格，到 z 260 的平台）
#     ＋從平台架到岩頂的木梯（史實：石階接一道從上面放下來的梯子）＋岩頂的「鴿舍」（圓塔、兩層、垛口、門朝梯子）＋旗杆與白旗。
#   · -battery（方塊）：平台邊的胸牆（3 格厚、1.2 m 高，壓頂淺石）、砲眼、小徑進來的門（門柱＋過梁）。
#   · 砲：外部模型借風暴角號的 12 磅長砲（summit-stormkaap-01m-gun-12l，0.05 m ⇒ 自動 scale 0.5），擺在 -battery 裡、砲口朝外穿過砲眼。
#   · 高度一律讀 site_height.npy，⛔ 不用算式重算地面。輸出 masks/fort/{rock,battery}.vox.txt、guns.json、verify_fort.json。重跑逐位元組相同。
import sys, os, json, math
import numpy as np

D = sys.argv[1]
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
S, PAL = plan['site'], plan['palette']
H = np.load(os.path.join(D, 'site_height.npy')).astype(np.int32)
NX, NY = H.shape
R, F = S['rock'], S['fort_hill']
ZP = F['plateau_z']                                                       # 平台第一層空氣
CX, CY, RX, RY, RH = R['cx'], R['cy'], R['rx'], R['ry'], R['h']
ZT = ZP + RH                                                              # 岩頂 z 290


def hash2(x, y, s):
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return (h ^ (h >> 16)) / 4294967296.0


def anoise(theta, z, seed, nseg=12, zstep=30.0):                          # 繞岩一圈連續的雜訊（角度 nseg 段、高度每 zstep 格一段，平滑內插）
    a = (theta / (2 * math.pi)) % 1.0 * nseg
    i0, fa = int(a), a - int(a)
    zz = z / zstep
    j0, fz = int(math.floor(zz)), zz - math.floor(zz)
    fa, fz = fa * fa * (3 - 2 * fa), fz * fz * (3 - 2 * fz)
    g = lambda i, j: hash2(i % nseg, j, seed) * 2 - 1
    return (g(i0, j0) * (1 - fa) + g(i0 + 1, j0) * fa) * (1 - fz) + (g(i0, j0 + 1) * (1 - fa) + g(i0 + 1, j0 + 1) * fa) * fz


def srad(th, z):                                                          # 岩在 θ、z 的外緣（底面橢圓的倍數）：往上收 12%、大小兩層雜訊、腳下外擴（碎石坡）
    t = (z - ZP) / RH
    s = (1 - 0.12 * t) * (1 + 0.07 * anoise(th, z, 5, 16, 25.0) + 0.03 * anoise(th, z, 6, 40, 8.0))
    if t < 0.15:
        s *= 1 + 0.06 * (1 - t / 0.15) ** 2
    return s


# ═════════ -rock ═════════
X0, X1, Y0, Y1 = CX - int(RX * 1.25), CX + int(RX * 1.25), CY - int(RY * 1.25), CY + int(RY * 1.25)
ZTOP = ZT + 100
solid = np.zeros((X1 - X0, Y1 - Y0, ZTOP - ZP), bool)                    # 岩的實心（局部座標 z 從 ZP 起）
for x in range(X0, X1):
    for y in range(Y0, Y1):
        u, v = (x + 0.5 - CX) / RX, (y + 0.5 - CY) / RY
        rho, th = math.hypot(u, v), math.atan2(v, u)
        if rho > 1.25:
            continue
        top = ZT - int(8 * rho ** 3) - (int(5 * max(0.0, anoise(th, 0, 7, 24, 1e9))) if rho > 0.55 else 0) - (1 if hash2(x // 5, y // 5, 3) > 0.7 else 0)
        for z in range(int(H[x, y]), top):
            if rho <= srad(th, z):
                solid[x - X0, y - Y0, z - ZP] = True

# 鑿岩石階：南面，西南（θ0）往東南（θ1）爬；從那一級高度的岩面往裡 DEPTH（以底面橢圓的倍數量），第 k 段以上全部鑿掉 ⇒ 露天的石階（崖上鑿出來的路）
TH0, TH1, NST, RISE, DEPTH = math.radians(-165), math.radians(-70), 20, 3, 0.13
TH_LAND = math.radians(-55)                                               # 平台（landing）到這裡為止
treads = {}
for x in range(X0, X1):
    for y in range(Y0, Y1):
        u, v = (x + 0.5 - CX) / RX, (y + 0.5 - CY) / RY
        rho, th = math.hypot(u, v), math.atan2(v, u)
        if not (TH0 <= th <= TH_LAND):
            continue
        k = min(int((th - TH0) / (TH1 - TH0) * NST), NST)
        zt = ZP + RISE * k                                                # 這一級踏面上第一層空氣
        if rho < srad(th, zt) - DEPTH:
            continue
        solid[x - X0, y - Y0, zt - ZP:] = False
        treads[(x, y)] = zt

# 只留最大的一塊（岩頂雜訊會在邊上留下懸空的單格）
from scipy import ndimage
lab, nlab = ndimage.label(solid)
if nlab > 1:
    solid = lab == (1 + int(np.argmax(ndimage.sum(solid, lab, range(1, nlab + 1)))))
SOLID_PIECES = int(nlab)

# 殼：實心裡離空氣 ≤ 3 格的留下（底面 z < ZP 當成實的 ⇒ 底下開口、不封口）
air = ~solid
near = np.zeros_like(solid)
pad = np.pad(air, 3, constant_values=True)
pad[:, :, :3] = False                                                     # 底下是平台
for dx in range(-3, 4):
    for dy in range(-3, 4):
        for dz in range(-3, 4):
            if abs(dx) + abs(dy) + abs(dz) > 3:
                continue
            near |= pad[3 + dx:3 + dx + air.shape[0], 3 + dy:3 + dy + air.shape[1], 3 + dz:3 + dz + air.shape[2]]
shell = solid & near

rcells = {}
for i, j, k in zip(*np.nonzero(shell)):
    x, y, z = int(i) + X0, int(j) + Y0, int(k) + ZP
    up_air = k + 1 >= solid.shape[2] or not solid[i, j, k + 1]
    th = math.atan2(y - CY, x - CX)
    c = PAL['rock'] if anoise(th, z, 9, 48, 6.0) > 0.45 else PAL['stone']   # 灰岩為底（146），一塊一塊橄欖色的苔（145）
    if hash2(int((th + math.pi) * 60), z // 25, 19) > 0.96:
        c = PAL['dirt']                                                   # 直的裂縫
    hh = hash2(x, y * 7 + z, 11)
    if hh > 0.95:
        c = PAL['stone_light']
    elif hh < 0.04:
        c = PAL['dirt']
    if up_air:
        if (x, y) in treads and treads[(x, y)] == z + 1:
            c = PAL['stone_light']                                        # 踏面（磨亮）
        elif z >= ZT - 10:
            c = PAL['grass_dark'] if hash2(x // 4, y // 4, 13) > 0.6 else PAL['grass']   # 岩頂的草
    rcells[(x, y, z)] = c

# 木梯：在平台那一段的中間，靠著鑿面內牆（ρ ＝ RHO_IN）立直，從平台踏面到岩頂上 4 格
THL = (TH1 + TH_LAND) / 2
z_land = ZP + RISE * NST
RHO_IN = srad(THL, z_land) - DEPTH                                        # 平台那裡鑿面內牆的位置
rho_l = RHO_IN + 1.6 / RY
px, py = CX + RX * rho_l * math.cos(THL), CY + RY * rho_l * math.sin(THL)
tx, ty = -RX * math.sin(THL), RY * math.cos(THL)
tn = math.hypot(tx, ty); tx, ty = tx / tn, ty / tn
ix, iy = int(round(px)), int(round(py))
ax_x = abs(tx) >= abs(ty)                                                 # 梯子順著切線的主軸擺（斜擺的話橫檔跟梯腳只碰到角、不相連）
rung_cells = [(ix + s, iy) if ax_x else (ix, iy + s) for s in range(-3, 4)]
rails = [rung_cells[0], rung_cells[-1]]
z_rock_edge = max(z for (x, y, z) in rcells if abs(x - (CX + RX * (RHO_IN - 0.02) * math.cos(THL))) < 1.5 and abs(y - (CY + RY * (RHO_IN - 0.02) * math.sin(THL))) < 1.5)
z_ladder_top = z_rock_edge + 5
for (rx_, ry_) in rails:
    for z in range(z_land, z_ladder_top + 1):
        rcells[(rx_, ry_, z)] = PAL['timber_dark']
for z in range(z_land + 3, z_ladder_top - 1, 3):                          # 橫檔每 3 格（0.3 m）
    for (gx_, gy_) in rung_cells[1:-1]:
        rcells[(gx_, gy_, z)] = PAL['wood']

# 鴿舍：圓塔，外徑 TR、牆 3 格；z ZT−4 起（埋進岩頂）到牆頂 TZ；兩層樓板、屋頂平台；頂上垛口；門朝梯子
TC = (CX + 5, CY + 10)
TR, TW, TZ = 20, 3, ZT + 54
door_dir = math.atan2(py - TC[1], px - TC[0])
z_floor1, z_floor2, z_roof = ZT - 2, ZT + 26, TZ - 6                      # 樓板（各 2 格厚，z 是下面那一格）
loops = [door_dir + math.radians(a) for a in (60, 120, 180, 240, 300)]


def angdiff(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


for x in range(TC[0] - TR - 1, TC[0] + TR + 2):
    for y in range(TC[1] - TR - 1, TC[1] + TR + 2):
        r = math.hypot(x + 0.5 - TC[0], y + 0.5 - TC[1])
        if r > TR:
            continue
        a = math.atan2(y + 0.5 - TC[1], x + 0.5 - TC[0])
        arc = int((a + math.pi) * TR / 4.5)                               # 垛口：沿圓周每 4.5 格換一次
        wall = r > TR - TW
        for z in range(ZT - 4, TZ + 5):
            if wall:
                if z >= TZ and arc % 2 == 1:
                    continue                                              # 垛口的缺
                if angdiff(a, door_dir) < 6.0 / TR and ZT <= z < ZT + 20:
                    continue                                              # 門（寬約 6、高 2 m）
                if any(angdiff(a, la) < 0.8 / TR for la in loops) and (ZT + 6 <= z < ZT + 12 or ZT + 34 <= z < ZT + 40):
                    continue                                              # 射口（1 格寬、0.6 m 高）
                u = int(a * TR) + (2 if (z // 4) % 2 else 0)
                if z >= TZ or z == ZT + 26:
                    c = PAL['stone_light']                                # 垛口頂、腰線
                elif u % 5 == 0 or z % 4 == 0:
                    c = PAL['stone_light']
                else:
                    c = PAL['stone'] if hash2(u // 5, z // 4, 17) < 0.7 else PAL['rock']
                rcells[(x, y, z)] = c
            else:
                hatch = abs(x + 0.5 - (TC[0] - 10)) < 3 and abs(y + 0.5 - TC[1]) < 3
                if z in (z_floor1, z_floor1 + 1):
                    rcells[(x, y, z)] = PAL['stone']
                elif z in (z_floor2, z_floor2 + 1, z_roof, z_roof + 1) and not hatch:
                    rcells[(x, y, z)] = PAL['wood'] if z < z_roof else PAL['stone']
# 旗杆＋白旗（1640 年法國王旗是白的；設計決定：旗朝東飄）
for x in (TC[0], TC[0] + 1):
    for y in (TC[1], TC[1] + 1):
        for z in range(z_roof + 2, TZ + 40):
            rcells[(x, y, z)] = PAL['wood']
for x in range(TC[0] + 2, TC[0] + 18):
    for z in range(TZ + 28, TZ + 38):
        rcells[(x, TC[1], z)] = PAL['plaster_white']

# ═════════ -battery ═════════
P = H >= ZP
padp = np.pad(P, 1, constant_values=False)
edge = P & ~(padp[:-2, 1:-1] & padp[2:, 1:-1] & padp[1:-1, :-2] & padp[1:-1, 2:])
ys_ = np.arange(NY)[None, :]
edge &= ys_ < NY - 4                                                      # 北邊是作品邊（切開的沙盤），不砌
ex, ey = np.nonzero(edge)
band = np.zeros_like(P)
for dx in range(-2, 3):
    for dy in range(-2, 3):
        band[np.clip(ex + dx, 0, NX - 1), np.clip(ey + dy, 0, NY - 1)] = True
band &= P & (ys_ < NY - 4)
HC = (F['cx'], F['cy'])


def edge_at(phi_deg):                                                     # 從山包中心看 φ 角的那個邊格
    ang = np.degrees(np.arctan2(ey - HC[1], ex - HC[0]))
    i = int(np.argmin(np.abs(ang - phi_deg)))
    return int(ex[i]), int(ey[i])


GUN_PHI = [-180, -170, -160, -14, -4, 6]
GATE = edge_at(-120)
guns = []
for phi in GUN_PHI:
    bx, by = edge_at(phi)
    nx_, ny_ = bx + 0.5 - HC[0], by + 0.5 - HC[1]
    n = math.hypot(nx_, ny_); nx_, ny_ = nx_ / n, ny_ / n
    guns.append({'phi': phi, 'edge': [bx, by], 'n': [round(nx_, 4), round(ny_, 4)]})

BZ = ZP + 12                                                              # 胸牆頂（1.2 m）
bcells = {}
for x, y in zip(*np.nonzero(band)):
    x, y = int(x), int(y)
    gx, gy = x + 0.5 - (GATE[0] + 0.5), y + 0.5 - (GATE[1] + 0.5)
    in_gate = math.hypot(gx, gy) < 7
    post = 7 <= math.hypot(gx, gy) < 11
    ztop = ZP + 25 if (post or in_gate) else BZ
    for z in range(ZP, ztop):
        if in_gate and z < ZP + 22:
            continue
        cut = False
        for g in guns:
            vx, vy = x + 0.5 - (g['edge'][0] + 0.5), y + 0.5 - (g['edge'][1] + 0.5)
            along, across = vx * g['n'][0] + vy * g['n'][1], -vx * g['n'][1] + vy * g['n'][0]
            if abs(across) <= 4.5 and -6 <= along <= 3 and ZP + 6 <= z:
                cut = True
        if cut and not post:
            continue
        u = x + y + (3 if (z // 4) % 2 else 0)
        if z == ztop - 1 or (in_gate and z >= ZP + 22 and z == ZP + 22):
            c = PAL['stone_light']
        elif u % 6 == 0 or z % 4 == 0:
            c = PAL['stone_light']
        else:
            c = PAL['stone'] if hash2(u // 6, z // 4, 21) < 0.7 else PAL['rock']
        bcells[(x, y, z)] = c

# 砲：模型 at（-battery 子作品座標換算前的世界座標）＝ 砲尾底面中心；砲口朝外 n、伸到胸牆內面再進 1 格
GUN_LEN = 62 * 0.5
for g in guns:
    bx, by = g['edge']; nx_, ny_ = g['n']
    inner = 3.0
    g['at_world'] = [round(bx + 0.5 - nx_ * (inner + GUN_LEN - 1), 2), round(by + 0.5 - ny_ * (inner + GUN_LEN - 1), 2), ZP]
    g['rotate_z'] = round(math.degrees(math.atan2(-nx_, ny_)), 2)

# ═════════ 輸出 ═════════
def norm(cells):
    o = tuple(int(v) for v in np.array(list(cells)).min(0))
    return o, sorted((k[0] - o[0], k[1] - o[1], k[2] - o[2], c) for k, c in cells.items())


RO, out_r = norm(rcells)
BO, out_b = norm(bcells)
for g in guns:
    g['at'] = [round(g['at_world'][0] - BO[0], 2), round(g['at_world'][1] - BO[1], 2), g['at_world'][2] - BO[2]]
os.makedirs(os.path.join(D, 'masks', 'fort'), exist_ok=True)
for nm, arr in (('rock', out_r), ('battery', out_b)):
    with open(os.path.join(D, 'masks', 'fort', nm + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 岩堡港 %s（fort.py 產；x,y,z,color）\n' % nm)
        f.write(''.join('%d,%d,%d,%d\n' % t for t in arr))


def bbox(arr):
    a = np.array([t[:3] for t in arr])
    return [int(v) for v in a.max(0) + 1]


colors = lambda arr: {str(k): int(v) for k, v in zip(*np.unique([t[3] for t in arr], return_counts=True))}
# 砲跟岩的最近距離（底面那幾層）—— 砲身在 at 往 n 方向 31 格的線上
rock_base = np.array([(x, y) for (x, y, z) in rcells if z < ZP + 20])
for g in guns:
    pts = np.array([[g['at_world'][0] + g['n'][0] * s, g['at_world'][1] + g['n'][1] * s] for s in np.linspace(0, GUN_LEN, 16)])
    g['min_dist_to_rock'] = round(float(np.min(np.hypot(*(rock_base[:, None, :] - pts[None, :, :]).transpose(2, 0, 1)))), 1)
V = {'rock': {'voxels': len(out_r), 'bbox': bbox(out_r), 'colors': colors(out_r), 'origin': list(RO),
              'z_top': ZT, 'solid_pieces_before_keep_largest': SOLID_PIECES, 'stairs': {'steps': NST, 'rise': RISE, 'theta_deg': [-165, -70], 'landing_z': z_land},
              'ladder': {'rails': rails, 'z': [z_land, z_ladder_top], 'rock_edge_z': z_rock_edge},
              'dovecote': {'center': list(TC), 'r': TR, 'z': [ZT - 4, TZ + 4], 'door_deg': round(math.degrees(door_dir), 1)}},
     'battery': {'voxels': len(out_b), 'bbox': bbox(out_b), 'colors': colors(out_b), 'origin': list(BO), 'top_z': BZ, 'gate': list(GATE)},
     'guns': guns, 'gun_source': 'summit-stormkaap-01m-gun-12l', 'gun_pivot': [9.5, 0, 0]}
with open(os.path.join(D, 'verify_fort.json'), 'w', encoding='utf-8', newline='\n') as fo:
    json.dump(V, fo, ensure_ascii=False, indent=1, sort_keys=True); fo.write('\n')
print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != 'colors'} if isinstance(v, dict) else v) for k, v in V.items()}, ensure_ascii=False))
