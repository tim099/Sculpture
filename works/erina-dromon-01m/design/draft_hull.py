# 新圖紙 02：船殼格子（plan.json ⇒ 清單）。部件各一份清單，彼此不重疊：
#   hull      船殼：龍骨、艏艉柱、外板（厚 shell_t）、舷牆、肋骨（每站一片）、外板塗裝帶、槳口記號、衝角樑（spur）
#   deck_main 主甲板：甲板板（舷弧下一層）＋橫樑；艙口留洞
#   deck_hold 艙底走道（下層槳手的地板）：一層板
# 用法：python -I -X utf8 -B draft_hull.py ⇒ lists/hull.txt、lists/deck_main.txt、lists/deck_hold.txt、verify_hull.json
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
import dro

D = dro.D
P = dro.PLAN
Hp = P['hull']
C = dro.C
NX, NY, NZ = dro.NX, dro.NY, dro.NZ
WL = P['waterline_z']
T = Hp['shell_t']

xs = np.arange(NX) + 0.5
zs = np.arange(NZ) + 0.5
yc = np.arange(NY) + 0.5 - dro.YM                         # 格心離中線

# 每一欄 (x, z) 的半寬、每一欄 x 的舷弧（甲板面上第一層空氣的那一格）
W2 = np.full((NX, NZ), -1.0)
for i, x in enumerate(xs):
    for k, z in enumerate(zs):
        if z > 80:
            break
        W2[i, k] = dro.hb(x, z)
ZAIR = np.array([int(round(dro.sheer(x))) for x in xs])    # 甲板面上第一層空氣
HBW = Hp['bulwark']['h']

Y = np.abs(yc)[None, :, None]
inform = (Y <= W2[:, None, :]) & (W2[:, None, :] >= 0)     # 外形（不管高度上限）
zz = np.arange(NZ)[None, None, :]
S = inform & (zz < ZAIR[:, None, None])                     # 船殼外形：甲板面以下
# 龍骨：龍骨範圍內、龍骨頂以下、中線 3 格
kx0, kx1 = Hp['stern']['x_foot'], Hp['stem']['x_foot']
keel = np.zeros_like(S)
for i in range(int(kx0), int(kx1) + 1):
    kt = dro.keel_top(i + 0.5)
    keel[i, dro.YC - 1:dro.YC + 2, max(0, int(math.ceil(kt)) - 2):int(math.ceil(kt))] = True   # 龍骨 2 格高、跟著船底往上翹（rocker）
S |= keel

# 殼：往裡侵蝕 T 格（甲板面以上當成「裡面」，殼才不會在甲板面封頂）
ext = S | (inform & (zz >= ZAIR[:, None, None]))
I = ndimage.binary_erosion(ext, structure=ndimage.generate_binary_structure(3, 1), iterations=T, border_value=0)
shell = S & ~I
shell |= keel
# 舷牆：甲板面以上 HBW 格、外形最外 2 格
bw = np.zeros_like(S)
if HBW > 0:
    for i in range(NX):
        za = ZAIR[i]
        for k in range(za, min(NZ, za + HBW)):
            w = W2[i, k]
            if w < 0:
                continue
            m = (np.abs(yc) <= w) & (np.abs(yc) > w - 2)
            bw[i, m, k] = True
    bw &= ~S
# 艏柱、艉柱：照 end_fwd／end_aft 的弧，從柱腳一路到柱頭（舷弧以上那段是露在外面的柱頭：新月形的兩端）
po = Hp['posts']
posts = np.zeros_like(S)
for nm, fn in (('stem', dro.end_fwd), ('stern', dro.end_aft)):
    e = Hp[nm]
    for z4 in range(int(e['z_foot'] * 4), int(e['z_head'] * 4) + 1):
        z = z4 / 4
        xe = fn(z)
        rng = range(int(math.floor(xe - po['depth'])), int(math.floor(xe)) + 1) if nm == 'stem' else range(int(math.floor(xe)), int(math.floor(xe + po['depth'])) + 1)
        for x in rng:
            posts[x, dro.YC - 1:dro.YC + 2, int(z)] = True
posts &= ~S
shell |= posts
interior = S & ~shell                                        # 船殼裡的空間（之後放甲板、肋骨）
# 內龍骨（keelson）：中線 3 格、龍骨頂到艙底走道下一格（Yenikapı 有 keelson；也把走道底下中線那條溝填掉，不留封閉空腔）
keelson = interior.copy()
keelson[:, :dro.YC - 1, :] = False; keelson[:, dro.YC + 2:, :] = False; keelson[:, :, P['deck_hold']['z']:] = False
shell |= keelson
interior &= ~keelson

# 肋骨：每站（frame_dx 格一站）一片 1 格厚，貼著殼往裡 1 格，從龍骨到甲板下 3 格
ribs = np.zeros_like(S)
st = P['hull'].get('frames', {'dx': 10, 'x0': 50, 'x1': 340})
near = ndimage.binary_dilation(shell, structure=ndimage.generate_binary_structure(3, 1), iterations=1) & interior
for xf in range(st['x0'], st['x1'] + 1, st['dx']):
    col = near[xf].copy()
    col[:, ZAIR[xf] - 3:] = False
    ribs[xf] = col

# 主甲板：甲板面下一層（板）＋站上的橫樑（再下一層、x 2 格寬）
deck = np.zeros_like(S)
hatches = P['deck_main'].get('hatches', [])
for i in range(NX):
    za = ZAIR[i]
    if za - 1 < 0:
        continue
    deck[i, :, za - 1] = interior[i, :, za - 1]
for xf in range(st['x0'], st['x1'] + 1, st['dx']):
    for i in (xf, xf + 1):
        za = ZAIR[i]
        deck[i, :, za - 2] |= interior[i, :, za - 2] & ~ribs[i, :, za - 2]
for h in hatches:                                            # 艙口：甲板開洞（含底下的橫樑）
    deck[h['x0']:h['x1'] + 1, dro.YC - h['hw']:dro.YC + h['hw'] + 1, :] = False
ribs &= ~deck

# 艙底走道：z ＝ hold_z 一層，x 範圍內
hold = np.zeros_like(S)
hz, hx0, hx1 = P['deck_hold']['z'], P['deck_hold']['x0'], P['deck_hold']['x1']
near2 = ndimage.binary_dilation(shell, structure=np.array([[[0], [1], [0]]] * 1, bool).reshape(1, 3, 1), iterations=2)   # 只往 y 方向膨脹   # 兩舷各留 1 格排水縫（板底下不封成空腔）
stations = np.zeros(NX, bool); stations[st['x0']:st['x1'] + 1:st['dx']] = True     # 肋骨那一站的板伸到肋骨（撐住、連通），站與站之間留縫
hold[hx0:hx1 + 1, :, hz] = interior[hx0:hx1 + 1, :, hz] & ~ribs[hx0:hx1 + 1, :, hz] & (~near2[hx0:hx1 + 1, :, hz] | stations[hx0:hx1 + 1, None])

# ── 顏色 ──
hull = shell | bw | ribs
col = np.zeros(S.shape, np.int16)
col[hull] = C['topside']
col[ribs] = C['beam']
# 水線下（含水線往上 1 格）＝ 瀝青黑
col[shell & (zz <= WL)] = C['bottom']
col[keel] = C['keel']
# 外板帶：wale（兩條）、紅帶（舷牆頂下）
for b in P['paint']['wales']:
    sel = shell & (zz >= b[0]) & (zz <= b[1])
    col[sel] = C['wale']
for i in range(NX):
    za = ZAIR[i]
    z0, z1 = za + P['paint']['stripe'][0], za + P['paint']['stripe'][1]
    col[i, :, z0:z1 + 1][hull[i, :, z0:z1 + 1]] = C['stripe']
# 槳口（造船規格 §9.10.2）：下層開在外板（z_lower 起 h 格、x 起 w 格，殼打穿）、上層開在舷牆（甲板面上 upper_dz 格起、upper_h 格高、錯半個位）；
#   plan oars.skip 裡的位子（上層 U18：投石機的底座）不放槳、也不開洞；
#   洞的一圈外板塗深色（皮套 askoma 的樣子）。槳的模型穿過洞（draft_oars.py 量碰撞）。
oar = P['oars']
marks, ports = [], []


def cut_port(x0, z0, side, h):
    ys = range(dro.YC + 1, NY) if side > 0 else range(0, dro.YC)
    for z in range(z0, z0 + h):
        for x in range(x0, x0 + oar['w']):
            for y in ys:                                          # 外面 4 格內的殼／舷牆（外張那段兩層殼斜著疊）
                if hull[x, y, z] and abs(y + 0.5 - dro.YM) > W2[x, z] - 4:
                    hull[x, y, z] = False; ports.append((x, y, z))
    for z in range(z0 - 1, z0 + h + 1):                           # 洞的一圈：最外那一格塗深色
        for x in range(x0 - 1, x0 + oar['w'] + 1):
            yy = [y for y in ys if hull[x, y, z]]
            if yy:
                yo = max(yy) if side > 0 else min(yy)
                col[x, yo, z] = C['oarport']; marks.append((x, yo, z))


for j in range(oar['per_side']):
    xl = oar['x_first'] + j * oar['dx']
    xu = xl + oar['upper_offset']
    skipU = 'U%02d' % (j + 1) in oar.get('skip', [])
    for side in (-1, 1):
        cut_port(xl, oar['z_lower'], side, oar['h'])
        if not skipU:
            cut_port(xu, int(ZAIR[xu]) + oar['upper_dz'], side, oar.get('upper_h', oar['h']))

# 衝角樑（spur）：從艏柱往前、往上一點，方截面漸細，尖端包銅
sp = Hp['spur']
spur = {}
for x in range(sp['x0'], sp['x1'] + 1):
    t = (x - sp['x0']) / (sp['x1'] - sp['x0'])
    zc = sp['z0'] + (sp['z1'] - sp['z0']) * t
    hw = sp['hw0'] + (sp['hw1'] - sp['hw0']) * t
    hh = sp['hh0'] + (sp['hh1'] - sp['hh0']) * t
    for y in range(NY):
        for z in range(int(zc - hh - 1), int(zc + hh + 2)):
            if abs(y + 0.5 - dro.YM) <= hw and abs(z + 0.5 - zc) <= hh and not hull[x, y, z]:
                spur[(x, y, z)] = C['bronze'] if t > sp['tip_from'] else C['wale']

sp_ = Hp['siphon_port']                                      # 艏部噴口：siphon 的獅頭從這裡伸出去
hull[sp_['x0']:sp_['x1'] + 1, sp_['y0']:sp_['y1'] + 1, sp_['z0']:sp_['z1'] + 1] = False
cells_hull = {tuple(map(int, p)): int(col[tuple(p)]) for p in np.argwhere(hull)}
for k, v in spur.items():
    cells_hull[k] = v
cells_deck = {tuple(map(int, p)): C['deck'] if True else 0 for p in np.argwhere(deck)}
for p in np.argwhere(deck):
    if p[2] == ZAIR[p[0]] - 2:
        cells_deck[tuple(map(int, p))] = C['beam']
cells_hold = {tuple(map(int, p)): C['deck'] for p in np.argwhere(hold)}

# 讀數：重疊、元件、空腔、鏡像
allc = set(cells_hull) | set(cells_deck) | set(cells_hold)
ov = len(cells_hull) + len(cells_deck) + len(cells_hold) - len(allc)
A = np.zeros(S.shape, bool)
for p in allc:
    A[p] = True
lab, ncomp = ndimage.label(A, structure=ndimage.generate_binary_structure(3, 1))
holes = ndimage.binary_fill_holes(A) & ~A
hl, nh = ndimage.label(holes)
cav = [(int(c[0].start), int(c[1].start), int(c[2].start), int(c[0].stop), int(c[1].stop), int(c[2].stop)) for c in ndimage.find_objects(hl)]
mir = sum(1 for (x, y, z) in allc if (x, dro.mirror_y(y), z) not in allc)
n1 = dro.write_list(os.path.join(D, 'lists', 'hull.txt'), cells_hull, '持火號 船殼（draft_hull.py）')
n2 = dro.write_list(os.path.join(D, 'lists', 'deck_main.txt'), cells_deck, '持火號 主甲板（draft_hull.py）')
n3 = dro.write_list(os.path.join(D, 'lists', 'deck_hold.txt'), cells_hold, '持火號 艙底走道（draft_hull.py）')
R = {'hull': n1, 'deck_main': n2, 'deck_hold': n3, 'overlap': ov, 'components': int(ncomp), 'cavities': int(nh), 'cavity_cells': int(holes.sum()), 'cavity_boxes': cav,
     'mirror_diff': mir, 'oar_marks': len(marks), 'oar_port_cells': len(ports), 'zair_mid': int(ZAIR[P['hull']['x_mid']]),
     'x_range': [int(np.argwhere(A.any((1, 2)))[0][0]), int(np.argwhere(A.any((1, 2)))[-1][0])],
     'z_top': int(np.argwhere(A.any((0, 1)))[-1][0]), 'y_range': [int(np.argwhere(A.any((0, 2)))[0][0]), int(np.argwhere(A.any((0, 2)))[-1][0])]}
json.dump({'readings': R, 'zair': ZAIR.tolist(), 'stamp_order': [{'work': 'hull', 'file': 'lists/hull.txt', 'cells': n1},
           {'work': 'deck_main', 'file': 'lists/deck_main.txt', 'cells': n2}, {'work': 'deck_hold', 'file': 'lists/deck_hold.txt', 'cells': n3}]},
          open(os.path.join(D, 'verify_hull.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
print(json.dumps(R, ensure_ascii=False))
