import sys, numpy as np
from PIL import Image
sys.path.insert(0, '.')
import gen_virginia as G
own, col, names, meta = G.build()
def rgb(c):
    c = c.astype(np.int32); return np.stack([((c >> 5) & 7) * 255 // 7, ((c >> 2) & 7) * 255 // 7, (c & 3) * 255 // 3], -1).astype(np.uint8)
def side():   # 從 +y 看（右舷）：每個 (x,z) 取 y 最大的那一格
    m = own > 0; idx = np.where(m.any(1), G.NY - 1 - np.argmax(m[:, ::-1, :], axis=1), -1)
    c = np.take_along_axis(col, np.clip(idx, 0, None)[:, None, :], 1)[:, 0, :]
    img = rgb(c); img[idx < 0] = (200, 220, 240); img[:, G.ZW][idx[:, G.ZW] < 0] = (0, 0, 255)
    return np.transpose(img, (1, 0, 2))[::-1]
def sect(xx):
    img = rgb(col[xx]); img[own[xx] == 0] = (200, 220, 240); return np.transpose(img, (1, 0, 2))[::-1]
def plan(zz):
    img = rgb(col[:, :, zz]); img[own[:, :, zz] == 0] = (200, 220, 240); return np.transpose(img, (1, 0, 2))[::-1]
Image.fromarray(side()).resize((1800, 340), Image.NEAREST).save('pv_side.png')
s = np.concatenate([sect(450), np.full((170, 4, 3), 255, np.uint8), sect(700), np.full((170, 4, 3), 255, np.uint8), sect(100), np.full((170, 4, 3), 255, np.uint8), sect(330)], 1)
Image.fromarray(s).resize((s.shape[1] * 3, s.shape[0] * 3), Image.NEAREST).save('pv_sect.png')
p = np.concatenate([plan(80), np.full((4, 900, 3), 255, np.uint8), plan(68), np.full((4, 900, 3), 255, np.uint8), plan(30)], 0)
Image.fromarray(p).resize((1800, p.shape[0] * 2), Image.NEAREST).save('pv_plan.png')
