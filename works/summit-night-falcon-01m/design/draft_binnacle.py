# 階段二十：羅經櫃（binnacle）—— 0.02 m 子作品當外部模型（scale 0.2）掛甲板-後，meta kind=binnacle（造船規格 §9）
# 設計 plan.json binnacle（出處 provenance binnacle、binnacle.place）；現況 nf_state stage19（格）＋組裝件 obj 的繩／帆／模型（軟障礙）。
# 子作品座標：x 沿船長（船頭 +x）、y 橫向、z 上，z 0 ＝ 甲板面上第一層；朝船尾那一面（x 0）是舵手看的那一面。
#   底座（plinth）滿框 → 櫃身內縮 inset、四角 corner×corner 深色柱 → 簷（cornice）滿框 → 銅罩（半球，罩在羅經上）＋兩根燈煙囪
#   朝船尾：羅經窗（金框、玻璃往裡一格）、兩側燈窗（琥珀，往裡一格）
# 擺法：見 provenance binnacle.place。
# 輸出：masks/binnacle/binnacle.vox.txt、verify_binnacle.json、sheet20_binnacle_v1.png
# 用法：python -I -X utf8 -B draft_binnacle.py <design 資料夾> <組裝件 obj（階段十九之後的現況）>
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, occupancy, NX, NY, NZ

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
B = plan['binnacle']
SX, SY, SZ = B['size']
C = B['colors']
cells = {}


def put(x, y, z, c, over=False):
    assert 0 <= x < SX and 0 <= y < SY and 0 <= z < SZ, ('框外', x, y, z)
    if over or (x, y, z) not in cells:
        cells[(x, y, z)] = c


# 底座
for x in range(SX):
    for y in range(SY):
        for z in range(B['plinth']['z'][0], B['plinth']['z'][1] + 1):
            put(x, y, z, C['plinth'])
# 櫃身＋四角柱
I, K = B['body']['inset'], B['body']['corner']
for x in range(I, SX - I):
    for y in range(I, SY - I):
        corner = (x < I + K or x >= SX - I - K) and (y < I + K or y >= SY - I - K)
        for z in range(B['body']['z'][0], B['body']['z'][1] + 1):
            put(x, y, z, C['corner'] if corner else C['body'])
# 簷
for x in range(SX):
    for y in range(SY):
        for z in range(B['cornice']['z'][0], B['cornice']['z'][1] + 1):
            put(x, y, z, C['corner'])
# 朝船尾的窗：外面那一層（x ＝ I）挖掉、往裡一格（x ＝ I＋1）換成玻璃色；羅經窗外圈一格金框（貼在 x ＝ I）
cw = B['compass_window']
y0, y1 = cw['y']; z0, z1 = cw['z']
for y in range(y0 - 1, y1 + 2):
    for z in range(z0 - 1, z1 + 2):
        if y0 <= y <= y1 and z0 <= z <= z1:
            del cells[(I, y, z)]
            put(I + 1, y, z, C['glass'], over=True)
        else:
            put(I, y, z, C['frame'], over=True)
lw = B['lamp_windows']
for ya, yb in lw['y']:
    for y in range(ya, yb + 1):
        for z in range(lw['z'][0], lw['z'][1] + 1):
            del cells[(I, y, z)]
            put(I + 1, y, z, C['lamp'], over=True)
# 銅罩：半球（中心在簷頂上一層的格面）
H = B['hood']
zc = H['z0']
for x in range(SX):
    for y in range(SY):
        for z in range(zc, SZ):
            if math.hypot(x + 0.5 - H['cx'], y + 0.5 - H['cy'], z + 0.5 - zc) <= H['r']:
                put(x, y, z, C['hood'])
# 燈煙囪
ch = B['chimneys']
for ya, yb in ch['y']:
    for y in range(ya, yb + 1):
        for x in range(ch['x'][0], ch['x'][1] + 1):
            for z in range(ch['z'][0], ch['z'][1] + 1):
                put(x, y, z, C['iron'])
    for y in range(ya - 1, yb + 2):
        for x in range(ch['x'][0] - 1, ch['x'][1] + 2):
            put(x, y, ch['cap'], C['iron'])

M = np.zeros((SX, SY, SZ), bool)
for k in cells:
    M[k] = True
comp = ndimage.label(M, ndimage.generate_binary_structure(3, 1))[1]
pad = np.pad(~M, 1, constant_values=True)
cav = ndimage.label(pad, ndimage.generate_binary_structure(3, 1))[1] - 1
asym = sum(1 for (x, y, z), c in cells.items() if cells.get((x, SY - 1 - y, z)) != c)
top = max(z for _, _, z in cells)
print('羅經櫃 %d 格、元件 %d、空腔 %d、左右差 %d、最高 z %d（%.2f m）' % (len(cells), comp, cav, asym, top, (top + 1) * B['mpv']))

# ───── 擺放 ─────
W = state_after(D, 'stage19')
occ = occupancy(W)
assert int(occ.sum()) == 97160, ('設計那一側的現況格數對不上組裝件', int(occ.sum()))
XR, ZR = (85, 115), (38, 70)
soft = np.zeros((NX, NY, NZ), bool)
vs, faces, cur = [], [], None
for line in open(sys.argv[2], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        cur = line.split()[1]
    elif line.startswith('f ') and cur and cur.split('_')[0] in ('rope', 'sail', 'model'):
        faces.append([int(t.split('/')[0]) - 1 for t in line.split()[1:4]])
vs = np.array(vs)[:, [0, 2, 1]]                         # obj 是 y 朝上 ⇒ 換回作品座標
T = vs[np.array(faces)]
keep = (T[:, :, 0].max(1) >= XR[0]) & (T[:, :, 0].min(1) <= XR[1]) & (T[:, :, 2].max(1) >= ZR[0]) & (T[:, :, 2].min(1) <= ZR[1])
for t in T[keep]:
    a, b, c = t
    n = int(np.ceil(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / 0.25)) + 1
    i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
    m = (i + j) <= n
    p = np.floor(a + np.outer(i[m] / n, b - a) + np.outer(j[m] / n, c - a)).astype(int)
    soft[p[:, 0], p[:, 1], p[:, 2]] = True
soft &= ~occ
S = B['scale']
pivot = np.array([SX / 2.0, SY / 2.0, 0.0])
offs = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
samp = (np.array(sorted(cells), float)[:, None, :] + offs[None]).reshape(-1, 3)
bot = np.array([[x + ox, y + oy, 0.0] for (x, y, z) in cells if z == 0 for ox in (0.25, 0.75) for oy in (0.25, 0.75)])
pl = B['place']
Q = W['quarter']
cands, why = [], []
x = pl['x_search'][0]
while x <= pl['x_search'][1] + 1e-9:
    xs = range(int(math.floor(x - SX / 2 * S)), int(math.ceil(x + SX / 2 * S)) + 1)
    tops = sorted({int(np.nonzero(Q[xx, yy, :])[0].max()) for xx in xs for yy in range(77, 85) if Q[xx, yy, :].any()})
    for t in tops:
        at = np.array([x, pl['y'], t + 1.0])
        P = (samp - pivot) * S + at
        i = np.floor(P).astype(int)
        h_occ, h_soft = int(occ[i[:, 0], i[:, 1], i[:, 2]].sum()), int(soft[i[:, 0], i[:, 1], i[:, 2]].sum())
        lo, hi = P.min(0), P.max(0)
        kx, ky = pl['keep']['x'], pl['keep']['y']
        in_keep = hi[0] > kx[0] and lo[0] < kx[1] + 1 and hi[1] > ky[0] and lo[1] < ky[1] + 1
        b = np.floor((bot - pivot) * S + at).astype(int)
        sup = int(occ[b[:, 0], b[:, 1], b[:, 2] - 1].sum())
        why.append({'x': x, 'deck_top': t, 'hit_cells': h_occ, 'hit_soft': h_soft, 'in_keep': bool(in_keep), 'support': '%d/%d' % (sup, len(b))})
        if not h_occ and not h_soft and not in_keep and sup == len(b):
            cands.append((abs(x - pl['x_target']), x, at.tolist(), t, lo.tolist(), hi.tolist()))
    x += pl['step']
assert cands, ('後甲板上找不到位置', why)
_, xb, at, t, lo, hi = min(cands)
print('羅經櫃 at', at, 'deck_top', t, '外框', [round(v, 2) for v in lo], [round(v, 2) for v in hi], '候選', len(cands), '／', len(why))

# 跟舵輪的距離（舵輪＋座的外框，從 verify_helm 換算）
VH = json.load(open(os.path.join(D, 'verify_helm.json'), encoding='utf-8'))
wheel_front = VH['at'][0] + (VH['size'][0] - VH['pivot'][0]) * VH['scale']

out = os.path.join(D, 'masks', 'binnacle')
os.makedirs(out, exist_ok=True)
p = os.path.join(out, 'binnacle.vox.txt')
rws = sorted((k[0], k[1], k[2], c) for k, c in cells.items())
open(p, 'w', encoding='utf-8', newline='\n').write('# 夜隼號 羅經櫃（draft_binnacle.py，0.02 m）x,y,z,color —— at 0,0,0（%d 格）\n' % len(rws)
                                                + '\n'.join('%d,%d,%d,%d' % r for r in rws) + '\n')
cnt = {}
for c in cells.values():
    cnt[str(c)] = cnt.get(str(c), 0) + 1
v = {'note': 'draft_binnacle.py（階段二十）—— 現況 nf_state stage19 ＋ 組裝件 obj 的繩／帆／模型',
     'work': B['work'], 'title': B['title'], 'size': B['size'], 'mpv': B['mpv'], 'scale': S, 'pivot': pivot.tolist(),
     'file': {'path': 'masks/binnacle/binnacle.vox.txt', 'cells': len(rws), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()},
     'colors': cnt, 'components': int(comp), 'cavities': int(cav), 'asym_y': asym, 'top_m': round((top + 1) * B['mpv'], 3),
     'host': 'summit-night-falcon-01m-deck-quarter', 'model': {'name': '羅經櫃', 'meta': {'kind': 'binnacle'}},
     'at': at, 'deck_top': t, 'box_world': [lo, hi], 'gap_to_wheel_box': round(lo[0] - wheel_front, 3),
     'soft_cells_in_window': int(soft.sum()), 'candidates': len(cands), 'tried': why}
json.dump(v, open(os.path.join(D, 'verify_binnacle.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)

# 圖紙：朝船尾那一面（從 −x 看）＋側面（從 +y 看），每格 10 px
sc = 10
im = Image.new('RGB', ((SY + SX) * sc + 90, SZ * sc + 80), (250, 249, 244))
dr = ImageDraw.Draw(im)
dr.text((20, 12), '新圖紙 20 v1 羅經櫃（左：朝船尾；右：側面）%d 格' % len(cells), fill=(30, 30, 30), font=ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 15))
pal = {104: (92, 58, 30), 136: (150, 105, 60), 208: (212, 175, 55), 37: (120, 160, 175), 253: (240, 170, 60), 168: (190, 120, 60), 36: (55, 55, 60)}
for (x, y, z), c in cells.items():
    if all(not ((xx, y, z) in cells) for xx in range(0, x)):
        X0 = 20 + (SY - 1 - y) * sc; Y0 = 50 + (SZ - 1 - z) * sc
        dr.rectangle([X0, Y0, X0 + sc - 1, Y0 + sc - 1], fill=pal[c])
    if all(not ((x, yy, z) in cells) for yy in range(y + 1, SY)):
        X0 = 60 + SY * sc + x * sc; Y0 = 50 + (SZ - 1 - z) * sc
        dr.rectangle([X0, Y0, X0 + sc - 1, Y0 + sc - 1], fill=pal[c])
im.save(os.path.join(D, 'sheet20_binnacle_v1.png'))
print(json.dumps({k: v[k] for k in v if k not in ('tried',)}, ensure_ascii=False))
