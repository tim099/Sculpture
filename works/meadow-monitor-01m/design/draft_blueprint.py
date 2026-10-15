# 莫尼特號 新圖紙（藍圖風格）—— 從 plan.json 的設計（同一支 gen_monitor／gen_turret）畫：外形側視、中線縱剖、主甲板與住艙甲板平面、橫剖面、砲塔詳圖、尺寸與圖說。
# 用法：python -X utf8 -B draft_blueprint.py <輸出 png>
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gen_monitor as G
import gen_turret as GT

BG = (22, 52, 104); LINE = (235, 242, 255); FAINT = (120, 150, 200); ACC = (255, 214, 120); RED = (255, 130, 120); WATER = (110, 190, 255)
FONT_CJK = 'C:/Windows/Fonts/kaiu.ttf'; FONT_NUM = 'C:/Windows/Fonts/georgia.ttf'
def font(sz, cjk=True):
    try: return ImageFont.truetype(FONT_CJK if cjk else FONT_NUM, sz)
    except Exception: return ImageFont.load_default()

own, col, names, anc, extra = G.build()
town, tcol, tnames, tanc, tinfo = GT.build()
_g = np.isin(town, [tnames.index('gun'), tnames.index('carriage')])
town = town.copy(); town[_g[::-1] & (town == 0)] = tnames.index('gun')   # 第二門（鏡像）
P = G.P; NX, NY, NZ, YC = G.NX, G.NY, G.NZ, G.YC
K = 3                                        # 一格幾 px（0.1 m 格 ⇒ 1 m ＝ 30 px）
img = Image.new('RGB', (NX * K + 420, 3400), BG); dr = ImageDraw.Draw(img)


def edges(lab):
    """2D 標籤圖 → 邊線（跟相鄰格的標籤不同的格）。"""
    e = np.zeros(lab.shape, bool)
    e[1:, :] |= lab[1:, :] != lab[:-1, :]; e[:-1, :] |= lab[:-1, :] != lab[1:, :]
    e[:, 1:] |= lab[:, 1:] != lab[:, :-1]; e[:, :-1] |= lab[:, :-1] != lab[:, 1:]
    e[0, :] = e[-1, :] = e[:, 0] = e[:, -1] = True
    return e & (lab > 0)


def blit(lab, ox, oy, flipv=True, color=LINE, k=K, fill=None):
    """lab：[u, v] 的標籤（u ＝ 水平、v ＝ 垂直，v 0 在下）；畫在 (ox, oy) 為左上角。"""
    L = lab.T[::-1] if flipv else lab.T
    if fill is not None:
        a = np.zeros(L.shape + (3,), np.uint8); a[:] = BG
        for i, c in fill.items(): a[L == i] = c
        im = Image.fromarray(a).resize((L.shape[1] * k, L.shape[0] * k), Image.NEAREST)
        img.paste(im, (ox, oy))
    e = edges(L)
    ys, xs = np.nonzero(e)
    for yy, xx in zip(ys.tolist(), xs.tolist()):
        dr.rectangle([ox + xx * k, oy + yy * k, ox + xx * k + k - 1, oy + yy * k + k - 1], fill=color)
    return L.shape[1] * k, L.shape[0] * k


def dim(x0, y0, x1, y1, text, off=0, color=ACC, f=None):
    f = f or font(22)
    dr.line([x0, y0, x1, y1], fill=color, width=2)
    for (a, b) in ((x0, y0), (x1, y1)):
        if y0 == y1: dr.line([a, b - 8, a, b + 8], fill=color, width=2)
        else: dr.line([a - 8, b, a + 8, b], fill=color, width=2)
    tw = dr.textlength(text, font=f)
    if y0 == y1: dr.text(((x0 + x1) / 2 - tw / 2, y0 - 30 + off), text, fill=color, font=f)
    else: dr.text((x0 + 12, (y0 + y1) / 2 - 12), text, fill=color, font=f)


def title(x, y, t, sub=None):
    dr.text((x, y), t, fill=LINE, font=font(30))
    if sub: dr.text((x, y + 36), sub, fill=FAINT, font=font(20))


ox = 80
# ── 1. 外形側視（從右舷 +y 看）──
y0 = 110
title(ox, 20, '一、外形側視（右舷）', 'Outboard profile — starboard side; z 0 ＝ 龍骨底，比例 0.1 m／格')
m = own > 0
idx = np.where(m.any(1), NY - 1 - np.argmax(m[:, ::-1, :], axis=1), -1)
lab = np.take_along_axis(own, np.clip(idx, 0, None)[:, None, :], 1)[:, 0, :].astype(int); lab[idx < 0] = 0
w, h = blit(lab, ox, y0)
zw_y = y0 + (NZ - 1 - G.ZW) * K + K // 2
dr.line([ox - 30, zw_y, ox + w + 30, zw_y], fill=WATER, width=2); dr.text((ox + w + 4, zw_y - 26), 'DWL', fill=WATER, font=font(18, False))
dim(ox + G.XS * K, y0 + h + 20, ox + (G.XB + 1) * K, y0 + h + 20, '全長 %.1f m（%.0f ft）' % ((G.XB - G.XS + 1) * 0.1, (G.XB - G.XS + 1) * 0.1 / 0.3048), off=60)
dim(ox + w + 60, y0 + (NZ - 1 - G.ZW) * K, ox + w + 60, y0 + NZ * K, '吃水 %.1f m' % (G.ZW * 0.1))
# ── 2. 中線縱剖（y ＝ YC）──
y1 = y0 + h + 110
title(ox, y1 - 50, '二、中線縱剖', 'Inboard profile on centreline — 甲板、住艙甲板、機艙、鍋爐、彈藥庫、梯子')
lab = own[:, YC, :].astype(int)
w, h = blit(lab, ox, y1)
# 砲塔（模型）的位置畫虛線外框
t = P['turret_x']; tr = P['turret_r_out']; th = GT.T['height'] / 2
for yy in (y0, y1):
    bx0 = ox + (t - tr) * K; bx1 = ox + (t + tr + 1) * K; bz1 = yy + (NZ - 1 - G.ZFL + 1) * K; bz0 = bz1 - int(th * K)
    for xx in range(int(bx0), int(bx1), 12): dr.line([xx, bz0, min(xx + 6, bx1), bz0], fill=ACC, width=2)
    dr.line([bx0, bz0, bx0, bz1], fill=ACC, width=2); dr.line([bx1, bz0, bx1, bz1], fill=ACC, width=2)
dr.text((ox + (t - tr) * K, y0 - 6), '砲塔（外部模型、會轉）', fill=ACC, font=font(20))
# 部件標籤
def tag(nm, xx, zz, yy0):
    dr.text((ox + xx * K, yy0 + (NZ - 1 - zz) * K), nm, fill=ACC, font=font(18))
for nm, xx, zz in P.get('labels_profile', []): tag(nm, xx, zz, y1)
# ── 3. 主甲板平面（z ＝ ZFL 以上看下來）、住艙甲板平面 ──
y2 = y1 + h + 100
title(ox, y2 - 50, '三、主甲板平面', 'Deck plan — 船頭朝右；虛線圓 ＝ 砲塔外緣、十字 ＝ 轉的中心')
m = own > 0
idx = np.where(m.any(2), NZ - 1 - np.argmax(m[:, :, ::-1], axis=2), -1)
lab = np.take_along_axis(own, np.clip(idx, 0, None)[:, :, None], 2)[:, :, 0].astype(int); lab[idx < 0] = 0
w, h = blit(lab, ox, y2)
cxp, cyp = ox + (t + 0.5) * K, y2 + (NY - 1 - YC + 0.5) * K
for a in range(0, 360, 6):
    a0, a1 = math.radians(a), math.radians(a + 3)
    dr.line([cxp + tr * K * math.cos(a0), cyp + tr * K * math.sin(a0), cxp + tr * K * math.cos(a1), cyp + tr * K * math.sin(a1)], fill=ACC, width=2)
dr.line([cxp - 12, cyp, cxp + 12, cyp], fill=ACC, width=2); dr.line([cxp, cyp - 12, cxp, cyp + 12], fill=ACC, width=2)
dim(ox + w + 40, y2 + (NY - 1 - (YC + P['half_beam'])) * K, ox + w + 40, y2 + (NY - YC + P['half_beam']) * K, '寬 %.1f m' % ((2 * P['half_beam'] + 1) * 0.1))
y3 = y2 + h + 100
title(ox, y3 - 50, '四、住艙甲板平面', 'Berth deck plan（z ＝ 住艙甲板上一格）—— 艙房、彈藥庫、機艙、鍋爐')
zz = P['z_berth_top'] + 3
lab = own[:, :, zz].astype(int)
w, h = blit(lab, ox, y3)
for nm, xx, yy in P.get('labels_berth', []): dr.text((ox + xx * K, y3 + (NY - 1 - yy) * K), nm, fill=ACC, font=font(18))
# ── 5. 橫剖面（幾站）──
y4 = y3 + h + 110
title(ox, y4 - 50, '五、橫剖面', 'Sections（從船尾往船頭看）')
xx0 = ox
for xs in P.get('sections', [150, 240, 290, 420, 480]):
    lab = own[xs].astype(int)
    w, h = blit(lab, xx0, y4, k=2)
    dr.text((xx0, y4 + h + 6), 'x %d（%.1f m）' % (xs, xs * 0.1), fill=FAINT, font=font(18))
    xx0 += w + 30
# ── 6. 砲塔詳圖（0.05 m／格）──
y5 = y4 + NZ * 2 + 90
title(ox, y5 - 50, '六、砲塔詳圖（元件 0.05 m／格）', '平面（砲軸高度）／正視（砲門）／側剖（砲 a）—— 兩門 11 吋 Dahlgren')
k2 = 3
lab = town[:, :, GT.T['gun_z']].astype(int)
w1, h1 = blit(lab, ox, y5, k=k2)
m = town > 0
idx = np.where(m.any(1), GT.N - 1 - np.argmax(m[:, ::-1, :], axis=1), -1)
lab = np.take_along_axis(town, np.clip(idx, 0, None)[:, None, :], 1)[:, 0, :].astype(int); lab[idx < 0] = 0
w2, h2 = blit(lab, ox + w1 + 40, y5, k=k2)
lab = town[tinfo['gx']].astype(int)
w3, h3 = blit(lab, ox + w1 + w2 + 80, y5, k=k2)
R = GT.T
dr.text((ox, y5 + h1 + 8), '內徑 %.2f m、外徑 %.2f m、高 %.2f m、牆厚 %.2f m' % (2 * R['r_in'] * 0.05, 2 * R['r_out'] * 0.05, R['height'] * 0.05, (R['r_out'] - R['r_in']) * 0.05), fill=ACC, font=font(20))
# ── 圖說 ──
yb = y5 + max(h1, h2, h3) + 60
notes = P.get('legend', [])
dr.rectangle([ox - 10, yb - 10, ox + NX * K, yb + 30 + 28 * len(notes)], outline=LINE, width=2)
dr.text((ox, yb), 'USS MONITOR（1862）莫尼特號 —— 遊戲用造船圖紙　繪：meadow 🌿　比例 0.1 m／格（砲塔 0.05 m／格）', fill=LINE, font=font(24))
for i, s in enumerate(notes): dr.text((ox, yb + 34 + 28 * i), s, fill=FAINT, font=font(20))
img = img.crop((0, 0, img.width, yb + 40 + 28 * len(notes) + 20))
img.save(sys.argv[1])
print('ok', img.size)
