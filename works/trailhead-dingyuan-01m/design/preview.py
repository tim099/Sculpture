# 快速預覽（不經引擎）：讀 gen_dingyuan.py 輸出的 own.npy＋部件清單的顏色 ⇒ 側視（右舷）、俯視、幾個橫剖面，RGB332 調色盤上色。
# 用法：python -I -X utf8 -B preview.py <gen 輸出資料夾> <out.png> [x 剖面,…]
import sys, os, json
import numpy as np
from PIL import Image

out = sys.argv[1]; png = sys.argv[2]
secs = [int(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 else [100, 300, 450, 554, 640, 820]
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
NX, NY, NZ = own.shape
col = np.zeros(own.shape, np.uint8)
for i, nm in enumerate(names):
    for l in open(os.path.join(out, 'part_%s.txt' % nm), encoding='utf-8'):
        if l[:1].isdigit():
            a = l.split(','); col[int(a[0]), int(a[1]), int(a[2])] = int(a[3])
MIRR = ('boilers-aft', 'boilers-fwd', 'engine', 'shaft')
for nm in MIRR:
    if nm in names:
        i = names.index(nm) + 1
        m = (own == i)[:, ::-1, :]
        col[m & (col == 0)] = col[:, ::-1, :][m & (col == 0)]


def rgb(c):
    c = c.astype(np.int32)
    return np.stack([((c >> 5) & 7) * 255 // 7, ((c >> 2) & 7) * 255 // 7, (c & 3) * 255 // 3], -1).astype(np.uint8)


def proj(a, axis, rev=False):
    """沿 axis 看過去第一個非空格的顏色（rev ＝ 從大的那一頭看）。"""
    b = np.flip(a, axis) if rev else a
    m = b > 0
    idx = np.argmax(m, axis=axis)
    v = np.take_along_axis(b, np.expand_dims(idx, axis), axis).squeeze(axis)
    v[~m.any(axis)] = 0
    return v


def shade(v, bg=(225, 232, 240)):
    im = rgb(v); im[v == 0] = bg
    return im


side = shade(proj(col, 1, rev=True))[:, ::-1].transpose(1, 0, 2)       # 從 +y（右舷）看：x 往右、z 往上
top = shade(proj(col, 2, rev=True))[:, ::-1].transpose(1, 0, 2)        # 從上看：x 往右、y 往上（右舷在下）
top = top[::-1]
sec = [shade(col[x])[:, ::-1].transpose(1, 0, 2) for x in secs]       # 從船尾往前看：y 往右、z 往上
K = 1
W = NX
H = NZ + NY + NZ + 40
img = Image.new('RGB', (W, H), (255, 255, 255))
img.paste(Image.fromarray(side), (0, 0))
img.paste(Image.fromarray(top), (0, NZ + 10))
x0 = 0
for s in sec:
    img.paste(Image.fromarray(s), (x0, NZ + NY + 30)); x0 += NY + 8
# 水線
from PIL import ImageDraw
d = ImageDraw.Draw(img)
d.line([0, NZ - 1 - 60, NX, NZ - 1 - 60], fill=(40, 120, 220))
img = img.resize((W * 2, H * 2), Image.NEAREST)
img.save(png)
print('ok', img.size)
