# 新圖紙 00：總圖（側面、俯視、船中剖面、武器、主要尺寸）—— 從設計資料畫（清單＋模型擺法＋帆的角），不是描引擎的圖。
# 用法：python -I -X utf8 -B draft_sheet.py ⇒ sheet00_general.png
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dro

D = dro.D
P = dro.PLAN
WL = P['waterline_z']
VU = json.load(open(os.path.join(D, 'verify_upper.json'), encoding='utf-8'))
VR = json.load(open(os.path.join(D, 'verify_rig.json'), encoding='utf-8'))
VM = json.load(open(os.path.join(D, 'verify_models.json'), encoding='utf-8'))
VL = json.load(open(os.path.join(D, 'verify_lines.json'), encoding='utf-8'))
F = lambda n: ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', n)
FB = lambda n: ImageFont.truetype('C:/Windows/Fonts/msjhbd.ttc', n)
BG, INK, RED, BLUE, GRID, SAIL = (244, 239, 226), (35, 32, 40), (170, 30, 30), (40, 80, 160), (222, 214, 196), (120, 100, 70)


def rot(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def load(p):
    return np.loadtxt(os.path.join(D, p), delimiter=',', comments='#', ndmin=2)


pts, cols = [], []
files = ['lists/hull.txt', 'lists/deck_main.txt'] + [VU[k]['file'] for k in ('forecastle', 'castles', 'fittings', 'ladders')] + [VR['masts'][k]['file'] for k in VR['masts']]
for f in files:
    a = load(f); pts.append(a[:, :3] + 0.5); cols.append(a[:, 3].astype(int))
for m in VM:
    a = load(m['file'])
    s = float(m['scale'])
    # 縮放的模型照比例加密取樣，畫出來才是實心
    sub = [(0.5, 0.5, 0.5)] if s <= 0.5 else [(i, j, k) for i in (0.25, 0.75) for j in (0.25, 0.75) for k in (0.25, 0.75)]
    for o in sub:
        q = a[:, :3] + np.asarray(o) - np.asarray(m['pivot'])
        if 'y' in m.get('mirror', ''):
            q[:, 1] = -q[:, 1]
        pts.append((rot(*m['rotate']) @ (q * s).T).T + np.asarray(m['at'])); cols.append(a[:, 3].astype(int))
Pp = np.vstack(pts); Cc = np.concatenate(cols)
lut = np.array([dro.rgb332(i) for i in range(256)], float)

PX = 3
X0, X1 = 20, 400
W = (X1 - X0) * PX + 720
Z_TOP = 230
H_SIDE = (Z_TOP + 22) * PX
Y_HALF = 30
H_PLAN = 2 * Y_HALF * PX
H = 130 + H_SIDE + 70 + H_PLAN + 70 + 520
img = Image.new('RGB', (W, H), BG)
g = ImageDraw.Draw(img)
OX = 150
OS = 130                                  # 側面圖頂


def sx(x): return OX + (x - X0) * PX
def sz(z): return OS + (Z_TOP - z) * PX


OP = OS + H_SIDE + 80 + Y_HALF * PX      # 俯視圖中線


def py(y): return OP - (y - dro.YM) * PX


# 標題
g.text((OX, 18), '持火號 PYRPHOROS —— 拜占庭 dromon（10 世紀，100 槳雙層槳帆船）　總圖', font=FB(34), fill=INK)
g.text((OX, 64), '1 格 ＝ 0.1 m　·　x 船頭朝右　·　erina 設計（2026-10-18；TASK-0693）　·　數字出處：plan.json provenance（ref ＝ Pryor & Jeffreys 2006 等；design ＝ 設計決定）', font=F(18), fill=INK)
# 格線（每 1 m）
for x in range(X0, X1 + 1, 10):
    c = GRID if x % 50 else (200, 190, 168)
    g.line([sx(x), OS, sx(x), OS + H_SIDE], fill=c); g.line([sx(x), OP - Y_HALF * PX, sx(x), OP + Y_HALF * PX], fill=c)
for z in range(0, Z_TOP + 1, 10):
    g.line([OX, sz(z), sx(X1), sz(z)], fill=GRID if z % 50 else (200, 190, 168))
for z in range(0, Z_TOP + 1, 50):
    g.text((OX - 70, sz(z) - 10), '%.0f m' % (z * 0.1), font=F(16), fill=INK)

# ── 側面：從左舷看（近的最後畫）──
x, y, z = Pp[:, 0], Pp[:, 1], Pp[:, 2]
order = np.argsort(-y)
U = np.round(OX + (x - X0) * PX).astype(int); V = np.round(OS + (Z_TOP - z) * PX).astype(int)
arr = np.array(img)
sh = 0.62 + 0.38 * np.clip((dro.YM + 25 - y) / 50, 0, 1)
for i in order:
    if 0 <= V[i] < H and 0 <= U[i] < W:
        arr[V[i] - PX + 1:V[i] + 1, U[i]:U[i] + PX] = np.clip(lut[Cc[i]] * sh[i], 0, 255)
# ── 俯視（上面 ＝ 右舷 S；高的最後畫）──
order = np.argsort(z)
Vp = np.round(OP - (y - dro.YM) * PX).astype(int)
for i in order:
    if abs(y[i] - dro.YM) < Y_HALF:
        arr[Vp[i]:Vp[i] + PX, U[i]:U[i] + PX] = np.clip(lut[Cc[i]] * (0.7 + 0.3 * min(1, z[i] / 60)), 0, 255)
img = Image.fromarray(arr); g = ImageDraw.Draw(img)

# 帆（側面的三角形，照帆角；布料鼓起來的樣子在引擎圖）
def yard_pt(n, nm):
    m = [mm for mm in VM if mm['name'] == 'yard-' + n][0]
    p = np.asarray(VR['yards'][n]['anchors'][nm], float) + 0.5
    return rot(*m['rotate']) @ (p - np.asarray(m['pivot'])) + np.asarray(m['at'])
CLEW = {'fore': (247.5, 52.5), 'main': (152.5, 34.5)}
for n in ('fore', 'main'):
    t, pk = yard_pt(n, 'tack'), yard_pt(n, 'peak')
    tri = [(sx(t[0]), sz(t[2])), (sx(pk[0]), sz(pk[2])), (sx(CLEW[n][0]), sz(CLEW[n][1]))]
    g.polygon(tri, outline=SAIL)
    g.line([tri[1], tri[2]], fill=SAIL, width=2); g.line([tri[2], tri[0]], fill=SAIL, width=2)
# 水線
g.line([sx(X0), sz(WL), sx(X1), sz(WL)], fill=BLUE, width=2)
g.text((OX - 52, sz(WL) - 10), 'DWL', font=F(16), fill=BLUE)
g.line([sx(X0), py(dro.YM), sx(X1), py(dro.YM)], fill=RED)


def dim(xa, xb, zz, text, up=True):
    yv = sz(zz)
    g.line([sx(xa), yv, sx(xb), yv], fill=RED, width=1)
    for xx in (xa, xb):
        g.line([sx(xx), yv - 6, sx(xx), yv + 6], fill=RED, width=1)
    g.text(((sx(xa) + sx(xb)) / 2 - 60, yv - 24 if up else yv + 4), text, font=F(17), fill=RED)


def vdim(xx, za, zb, text):
    g.line([sx(xx), sz(za), sx(xx), sz(zb)], fill=RED)
    for zz in (za, zb):
        g.line([sx(xx) - 6, sz(zz), sx(xx) + 6, sz(zz)], fill=RED)
    g.text((sx(xx) + 6, (sz(za) + sz(zb)) / 2 - 10), text, font=F(16), fill=RED)


dim(38, 353, -6, '全長（艉柱頭 → 艏柱頭）31.5 m', up=False)
dim(353, 396, -6, 'spur 4.4 m', up=False)
dim(78, 328, -14, '划槳段 25 個槳位 × 1.0 m', up=False)
vdim(285, WL, 117, '前桅頂 離水線 10.6 m')
vdim(205, WL, 86, '中桅頂 7.5 m')
vdim(222, 21, 39, '木塔 1.8 m')
vdim(225, 0, WL, '吃水 1.1 m')


def label(xx, zz, tx, tz, text):                    # 引線：從 (xx, zz) 拉到文字 (tx, tz)
    g.line([sx(xx), sz(zz), sx(tx) - 4, sz(tz)], fill=INK)
    g.ellipse([sx(xx) - 3, sz(zz) - 3, sx(xx) + 3, sz(zz) + 3], outline=INK)
    g.text((sx(tx), sz(tz) - 11), text, font=F(17), fill=INK)


RX = 404                                              # 右邊那一欄
label(352, 31, RX, 150, '希臘火 siphon（鍍金獅頭兼船首像、噴口開在艏部舷牆）')
label(333, 49, RX, 132, 'pseudopation（艏樓平台；上面一架弩砲）')
label(380, 22, RX, 46, 'spur（peronion：水線以上的衝角樑，吊在艏柱上）')
label(330, 20, RX, 28, '錨 ×2（吊錨架 periboloi 下）')
label(256, 42, RX, 114, '投石機 manganikon（迴旋 0／180°）')
label(226, 47, RX, 96, 'xylokastra：中線兩側各一座木塔、中間木橋；各一架小弩砲')
label(296, 112, RX, 200, '前桅（較大、前傾 13°）＋前三角帆桁 20.1 m')
label(200, 84, RX, 182, '中桅＋中三角帆桁 15.4 m')
label(137, 9, 24, 186, '希臘火藥庫（艙底，6 桶）')
label(70, 41, 24, 204, '舷側舵 ×2（pedalion：舵葉、舵桿、舵柄）')
label(36, 60, 24, 222, '艉旗（帝國紫）')
label(300, 16, RX, 10, '下層槳口記號 25 × 2（槳還沒做）')

# 俯視的標註
g.text((sx(X0), OP - Y_HALF * PX - 26), '俯視（上 ＝ 右舷 S；帆桁照預設角度、帆不畫）', font=F(18), fill=INK)
g.text((sx(X0), OS - 30), '側面（從左舷 P 看；帆畫成帆角連線）', font=F(18), fill=INK)

# ── 下半：船中剖面＋武器＋數字表 ──
oy = OP + Y_HALF * PX + 70
g.text((OX, oy), '船中剖面（x 200；1 格 ＝ 6 px）', font=FB(22), fill=INK)
cx0, cz0, S2 = OX + 180, oy + 300, 6
for side in (-1, 1):
    pl = []
    for z4 in range(0, int((21 + 8) * 4) + 1):
        zz = z4 / 4
        w = dro.hb(200.5, zz)
        if w >= 0:
            pl.append((cx0 + side * w * S2, cz0 - zz * S2))
    g.line(pl, fill=INK, width=3)
g.line([cx0 - 160, cz0 - WL * S2, cx0 + 160, cz0 - WL * S2], fill=BLUE, width=2)
g.line([cx0, cz0 + 10, cx0, cz0 - 40 * S2], fill=RED)
for zz, txt in ((21, '主甲板 z 21（水線上 1.0 m）'), (15, '下層槳口 z 15（水線上 0.4 m）'), (5, '艙底走道 z 5'), (WL, 'DWL z 11')):
    g.line([cx0 + 140, cz0 - zz * S2, cx0 + 175, cz0 - zz * S2], fill=INK)
    g.text((cx0 + 180, cz0 - zz * S2 - 11), txt, font=F(16), fill=INK)
g.text((cx0 - 165, cz0 + 16), '寬 3.80 m（直舷）→ 4.46 m（下層槳口以上外張；Pryor）', font=F(16), fill=INK)

# 武器（引用 sheetW 的渲染）
wimg = Image.open(os.path.join(D, 'sheetW_weapons.png'))
wimg = wimg.crop((0, 40, wimg.width, 470)).resize((int(wimg.width * 0.7), int(430 * 0.7)))
img.paste(wimg, (OX + 760, oy + 30))
g.text((OX + 760, oy), '武器（套大炮規格：kind=gun；weapon／ammo 給之後的彈種）', font=FB(20), fill=INK)
tab = [('希臘火 siphon ×1', 'gun=6l　weapon=siphon　ammo=greekfire'),
       ('弩砲 toxoballistra ×3', 'gun=4l　weapon=toxoballistra　ammo=bolt'),
       ('投石機 manganikon ×1', 'gun=12l　weapon=manganikon　ammo=stone（迴旋）')]
for i, (a, b) in enumerate(tab):
    g.text((OX + 760, oy + 340 + i * 26), a, font=F(17), fill=INK); g.text((OX + 1000, oy + 340 + i * 26), b, font=F(17), fill=INK)
nums = ['水線長 %.1f m　水線寬 %.2f m　吃水 %.1f m　排水量約 %.0f t（Cb %.2f）' % (VL['lwl_m'], VL['bwl_m'], VL['draught_m'], VL['displacement_t'], VL['cb']),
        '前桅 11.3 m（前傾 13°）／帆桁 20.1 m　中桅 8.2 m／帆桁 15.4 m　（Pryor：11.85／20.17、8.3／15.43）',
        '槳：每舷上下各 25 支（這一版只標槳口位置，等槳動力系統的規格再加）']
for i, t in enumerate(nums):
    g.text((OX + 760, oy + 430 + i * 28), t, font=F(17), fill=INK)
img.save(os.path.join(D, 'sheet00_general.png'))
print('sheet00_general.png', img.size)
