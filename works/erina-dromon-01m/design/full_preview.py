# 整艘船的設計預覽（不經引擎）：所有清單＋verify_models.json 的模型（照擺法變換，scale < 1 的照比例取樣）。只看形狀。
# 用法：python -I -X utf8 -B full_preview.py <out.png> [--yaw 度] [--pitch 度] [--px N] [--hide 名字,…]
import os, sys, math, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dro

D = dro.D
args = sys.argv[1:]
out = args.pop(0)
yaw, pitch, px, hide = 30.0, 25.0, 3, set()
while args:
    a = args.pop(0)
    if a == '--yaw': yaw = float(args.pop(0))
    elif a == '--pitch': pitch = float(args.pop(0))
    elif a == '--px': px = int(args.pop(0))
    elif a == '--hide': hide = set(args.pop(0).split(','))


def load(p):
    return np.loadtxt(os.path.join(D, p), delimiter=',', comments='#', ndmin=2)


def rot(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


pts, cols = [], []
VU = json.load(open(os.path.join(D, 'verify_upper.json'), encoding='utf-8'))
VR = json.load(open(os.path.join(D, 'verify_rig.json'), encoding='utf-8'))
files = {'hull': 'lists/hull.txt', 'deck_main': 'lists/deck_main.txt', 'deck_hold': 'lists/deck_hold.txt'}
for k in ('forecastle', 'castles', 'fittings', 'magazine', 'ladders'):
    files[k] = VU[k]['file']
for k in VR['masts']:
    files['mast-' + k] = VR['masts'][k]['file']
for k, f in files.items():
    if k in hide:
        continue
    a = load(f); pts.append(a[:, :3] + 0.5); cols.append(a[:, 3].astype(int))
for m in json.load(open(os.path.join(D, 'verify_models.json'), encoding='utf-8')):
    if m['name'] in hide or m['host'] in hide:
        continue
    a = load(m['file'])
    s = float(m['scale']) if not isinstance(m['scale'], list) else float(m['scale'][0])
    # 取樣：每格切成 n³ 個點，讓縮放後的模型也是實心的
    n = max(1, int(math.ceil(s * 1.0)))
    q = a[:, :3] + 0.5 - np.asarray(m['pivot'])
    if 'y' in m.get('mirror', ''):
        q[:, 1] = -q[:, 1]
    w = (rot(*m['rotate']) @ (q * s).T).T + np.asarray(m['at'])
    pts.append(w); cols.append(a[:, 3].astype(int))
OP = os.path.join(D, 'oars_placement.json')                  # 槳（draft_oars.py）：--hide oars 藏掉
if os.path.exists(OP) and 'oars' not in hide:
    VO = json.load(open(os.path.join(D, 'verify_oars.json'), encoding='utf-8'))['components']
    PO = json.load(open(OP, encoding='utf-8'))
    for o in PO['oars']:
        a = load(VO[o['bank']]['file'])
        q = a[:, :3] + 0.5 - np.asarray(PO['pivot'][o['bank']])
        if 'y' in o['mirror']:
            q[:, 1] = -q[:, 1]
        pts.append((rot(*o['rotate']) @ (q * 0.5).T).T + np.asarray(o['at'])); cols.append(a[:, 3].astype(int))
P = np.vstack(pts); Cc = np.concatenate(cols)
cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
x, y, z = P[:, 0], P[:, 1], P[:, 2]
u = x * cy - y * sy
dd = x * sy + y * cy
v = z * cp + dd * sp
d = dd * cp - z * sp
U = np.round((u - u.min()) * px).astype(int); V = np.round((v.max() - v) * px).astype(int)
W, Hh = U.max() + px + 1, V.max() + px + 1
img = np.full((Hh, W, 3), (235, 238, 242), np.uint8)
order = np.argsort(-d)
lut = np.array([dro.rgb332(i) for i in range(256)], float)
sh = 0.72 + 0.28 * (z / max(1, z.max()))
for i in order:
    img[V[i]:V[i] + px, U[i]:U[i] + px] = np.clip(lut[Cc[i]] * sh[i], 0, 255)
Image.fromarray(img).save(out)
print(out, img.shape)
