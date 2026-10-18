# 設計側的快速預覽（不經引擎）：把幾份清單疊起來，斜投影畫一張圖（深度上色）。只給自己看形狀，⛔ 不當讀數。
# 用法：python -I -X utf8 -B preview.py <out.png> <清單[@x,y,z]> ... [--yaw 度] [--pitch 度] [--px N]
import os, sys, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dro

args = sys.argv[1:]
out = args.pop(0)
yaw, pitch, px = 30.0, 25.0, 3
files = []
while args:
    a = args.pop(0)
    if a == '--yaw': yaw = float(args.pop(0))
    elif a == '--pitch': pitch = float(args.pop(0))
    elif a == '--px': px = int(args.pop(0))
    else: files.append(a)
pts, cols = [], []
for f in files:
    off = (0, 0, 0)
    if '@' in f:
        f, o = f.split('@'); off = tuple(float(v) for v in o.split(','))
    a = np.loadtxt(f, delimiter=',', comments='#', ndmin=2)
    pts.append(a[:, :3] + 0.5 + np.asarray(off)); cols.append(a[:, 3].astype(int))
P = np.vstack(pts); Cc = np.concatenate(cols)
cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
# 觀者：從 (−sin yaw, −cos yaw) 方向、往下 pitch 看；螢幕 u 往右、v 往上、d 往裡
x, y, z = P[:, 0], P[:, 1], P[:, 2]
u = x * cy - y * sy
dd = x * sy + y * cy
v = z * cp + dd * sp
d = dd * cp - z * sp
U = np.round((u - u.min()) * px).astype(int); V = np.round((v.max() - v) * px).astype(int)
W, Hh = U.max() + px + 1, V.max() + px + 1
img = np.full((Hh, W, 3), (235, 238, 242), np.uint8)
zb = np.full((Hh, W), 1e9)
order = np.argsort(-d)                                   # 遠的先畫
lut = np.array([dro.rgb332(i) for i in range(256)], float)
for i in order:
    c = lut[Cc[i]]
    sh = 0.72 + 0.28 * (z[i] / max(1, z.max()))
    img[V[i]:V[i] + px, U[i]:U[i] + px] = np.clip(c * sh, 0, 255)
Image.fromarray(img).save(out)
print(out, img.shape)
