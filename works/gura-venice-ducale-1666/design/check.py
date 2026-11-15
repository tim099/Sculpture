# -*- coding: utf-8 -*-
"""總督宮自檢（每層）：
 ① 走得到：從小廣場（框外那一條）出發，人（站的那一格空、腳下實心、頭上 1.8 m 空）一步走四鄰、高低差 ≤ 1 格（0.2 m 一階）；
    每一層樓板上站得住的地方，列出走不到的那幾塊（框、格數）。
 ② 懸空：不碰地（z 0）的實心團（6 連通）。
 ③ 每層俯視圖（out/plan_<層>.png）：走得到 ＝ 淺色、站得住但走不到 ＝ 紅、牆 ＝ 深、樓梯 ＝ 依高度。"""
import os, sys
import numpy as np
from scipy import ndimage
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
d = np.load(os.path.join(HERE, 'out', 'grid.npz'))
g, gl, mt = d['g'], d['gl'], d['mt']
S = (g > 0) | (mt > 0) | gl
SX, SY, SZ = g.shape
HEAD = 9
air = ~S
clear = air.copy()
for k in range(1, HEAD):
    clear[:, :, :-k] &= air[:, :, k:]
    clear[:, :, SZ - k:] = False
stand = clear.copy()
stand[:, :, 0] = False
stand[:, :, 1:] &= S[:, :, :-1]
# 連通：四鄰 × 高低差 −1..1
st = np.zeros((3, 3, 3), bool)
for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
    for dz in (-1, 0, 1):
        if dx == 0 and dy == 0 and dz != 0: continue
        st[1 + dx, 1 + dy, 1 + dz] = True
lab, n = ndimage.label(stand, structure=st)
start = lab[357, 2, 1] or lab[2, 2, 1] or lab[357, 200, 1]
reach = lab == start
print('站得住的格 %d，連通塊 %d；從小廣場走得到 %d' % (stand.sum(), n, reach.sum()))

LEVELS = [('底層', 1, 1), ('敞廊層', 37, 37), ('主樓層', 65, 65), ('東翼二樓', 95, 95), ('屋頂平台', 65, 73)]
bad = 0
for name, z0, z1 in LEVELS:
    sl = stand[:, :, z0:z1 + 1].any(2)
    rs = reach[:, :, z0:z1 + 1].any(2)
    un = sl & ~rs
    l2, m = ndimage.label(un)
    big = []
    for i in range(1, m + 1):
        w = np.nonzero(l2 == i)
        if len(w[0]) >= 12:
            big.append((len(w[0]), w[0].min(), w[0].max(), w[1].min(), w[1].max()))
    big.sort(reverse=True)
    print('%s z%d：站得住 %d、走得到 %d、走不到的塊 %d' % (name, z0, sl.sum(), (sl & rs).sum(), len(big)))
    for b in big[:12]:
        print('   ✗ %d 格  x %d–%d  y %d–%d' % b)
    bad += len(big)
# 樓梯：每座樓梯頂端的落腳平台走得到嗎
for nm, (x, y, z) in {'巨人階梯頂': (18, 275, 37), '審查官 → 敞廊': (261, 110, 37), '審查官 → 大議會廳': (261, 110, 65),
                      '黃金 → 敞廊': (155, 330, 37), '黃金 → 主樓層': (155, 330, 65), '黃金 → 二樓': (155, 330, 95),
                      '西翼 → 敞廊': (39, 45, 37), '西翼 → 投票廳': (39, 45, 65), '大議會廳中央': (290, 150, 65), '投票廳中央': (130, 50, 65),
                      '東翼主樓層北端': (30, 320, 65), '東翼二樓南端': (320, 330, 95), '地牢最裡那一間': (320, 320, 1), '屋頂平台': (15, 50, 65)}.items():
    ok = bool(reach[x, y, z]); bad += (not ok)
    print('   %s %s（%d,%d,%d；站得住 %s）' % ('✓' if ok else '✗', nm, x, y, z, bool(stand[x, y, z])))
# ② 懸空
sl, m = ndimage.label(S)
ground = set(np.unique(sl[:, :, 0])) - {0}
sizes = ndimage.sum(np.ones_like(sl), sl, index=np.arange(1, m + 1))
fl = [(int(sizes[i - 1]), i) for i in range(1, m + 1) if i not in ground]
fl.sort(reverse=True)
print('懸空的團 %d 個（共 %d 格）' % (len(fl), sum(f[0] for f in fl)))
for sz, i in fl[:10]:
    w = np.nonzero(sl == i)
    print('   懸空 %d 格  x %d–%d  y %d–%d  z %d–%d' % (sz, w[0].min(), w[0].max(), w[1].min(), w[1].max(), w[2].min(), w[2].max()))
# ③ 俯視圖
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
for name, z0, z1 in LEVELS[:4]:
    img = np.zeros((SX, SY, 3), np.uint8)
    wall = S[:, :, z0 + 3]
    img[wall] = (70, 60, 55)
    sl_ = stand[:, :, max(1, z0 - 14):z1 + 15]
    any_s = sl_.any(2)
    img[any_s] = (230, 225, 210)
    un = any_s & ~reach[:, :, max(1, z0 - 14):z1 + 15].any(2)
    img[un] = (220, 40, 40)
    st_ = (stand & reach)[:, :, max(1, z0 - 14):z1 + 15]
    stairs = st_.any(2) & ~(stand & reach)[:, :, z0]
    img[stairs & ~un] = (90, 160, 220)
    im = Image.fromarray(img).resize((SY * 2, SX * 2), Image.NEAREST)
    im.save(os.path.join(HERE, 'out', 'plan_z%d.png' % z0))
print('✗ 總數', bad)
