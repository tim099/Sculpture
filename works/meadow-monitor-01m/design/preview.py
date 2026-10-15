# 預覽圖（側視、剖面、平面）：python -X utf8 -B preview.py [輸出資料夾]
import sys, os, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_monitor as G
out = sys.argv[1] if len(sys.argv) > 1 else '.'
own, col, names, anc, _ = G.build()
def rgb(c):
    c = c.astype(np.int32); return np.stack([((c >> 5) & 7) * 255 // 7, ((c >> 2) & 7) * 255 // 7, (c & 3) * 255 // 3], -1).astype(np.uint8)
SKY = (200, 220, 240)
def side(): # 從 +y 看
    m = own > 0; idx = np.where(m.any(1), G.NY - 1 - np.argmax(m[:, ::-1, :], axis=1), -1)
    c = np.take_along_axis(col, np.clip(idx, 0, None)[:, None, :], 1)[:, 0, :]
    img = rgb(c); img[idx < 0] = SKY; img[:, G.ZW][idx[:, G.ZW] < 0] = (0, 0, 255)
    return np.transpose(img, (1, 0, 2))[::-1]
def sect(xx):
    img = rgb(col[xx]); img[own[xx] == 0] = SKY; return np.transpose(img, (1, 0, 2))[::-1]
def plan(zz):
    img = rgb(col[:, :, zz]); img[own[:, :, zz] == 0] = SKY; return np.transpose(img, (1, 0, 2))[::-1]
def cut_y(yy):  # 中線縱剖
    img = rgb(col[:, yy, :]); img[own[:, yy, :] == 0] = SKY; return np.transpose(img, (1, 0, 2))[::-1]
W = G.NX
s1 = np.concatenate([side(), np.full((4, W, 3), 255, np.uint8), cut_y(G.YC)], 0)
Image.fromarray(s1).resize((W * 3, s1.shape[0] * 3), Image.NEAREST).save(os.path.join(out, 'pv_side.png'))
xs = G.P['sections']
sp = np.full((G.NZ, 4, 3), 255, np.uint8)
s = np.concatenate(sum([[sect(xx), sp] for xx in xs], [])[:-1], 1)
Image.fromarray(s).resize((s.shape[1] * 3, s.shape[0] * 3), Image.NEAREST).save(os.path.join(out, 'pv_sect.png'))
p = np.concatenate([plan(G.ZFL + 2), np.full((4, W, 3), 255, np.uint8), plan(G.ZD), np.full((4, W, 3), 255, np.uint8), plan(G.P['z_berth_top'] + 4), np.full((4, W, 3), 255, np.uint8), plan(8)], 0)
Image.fromarray(p).resize((W * 2, p.shape[0] * 2), Image.NEAREST).save(os.path.join(out, 'pv_plan.png'))
print('ok')
