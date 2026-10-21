# 定遠號 新圖紙（藍圖風格）—— 從產生程式的輸出（gen_dingyuan 的 own.npy＋gen_parts 的零件＋check_arcs 的射界）畫：
#   一、外形側視（右舷）　二、中線縱剖　三、上層平面（砲塔、射界）　四、主甲板平面　五、橫剖面　六、主砲塔詳圖　＋尺寸線、圖說。
# 用法：python -I -X utf8 -B draft_blueprint.py <gen 輸出> <parts 輸出> <out.png>
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

out, pout, png = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P, PP = PLAN['params'], PLAN['parts']
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
M = json.load(open(os.path.join(out, 'dingyuan_meta.json'), encoding='utf-8'))
ARC = json.load(open(os.path.join(out, 'arcs.json'), encoding='utf-8'))
NX, NY, NZ = own.shape; YC = (NY - 1) // 2; ZW = P['z_waterline']
BG = (20, 50, 102); LINE = (236, 243, 255); FAINT = (120, 152, 205); ACC = (255, 214, 120); RED = (255, 128, 118); WATER = (110, 190, 255); GREEN = (140, 230, 160)
FONT_CJK = 'C:/Windows/Fonts/kaiu.ttf'; FONT_NUM = 'C:/Windows/Fonts/georgia.ttf'


def font(sz, cjk=True):
    try: return ImageFont.truetype(FONT_CJK if cjk else FONT_NUM, sz)
    except Exception: return ImageFont.load_default()


# ── 模型也畫進來（砲塔殼、砲、小艇、魚雷艇、舵、螺旋槳）：照擺法把來源格子的格心換算進船的格 ──
lab = own.astype(np.int16)
extra = []


def load_list(fn):
    a = np.array([[int(v) for v in l.split(',')] for l in open(fn, encoding='utf-8') if l[:1].isdigit()])
    return a[:, :3]


def stamp(cells, at, pivot, rot_deg, sc, name):
    """格心 → 船的格；只畫空格（跟模型一樣疊在上面）。"""
    if name not in extra: extra.append(name)
    k = len(names) + 1 + extra.index(name)
    p = (cells + 0.5 - np.array(pivot)) * sc
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    q = np.stack([p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c, p[:, 2]], 1) + np.array(at)
    q = np.floor(q).astype(int)
    ok = (q[:, 0] >= 0) & (q[:, 0] < NX) & (q[:, 1] >= 0) & (q[:, 1] < NY) & (q[:, 2] >= 0) & (q[:, 2] < NZ)
    q = q[ok]
    m = lab[q[:, 0], q[:, 1], q[:, 2]] == 0
    lab[q[m, 0], q[m, 1], q[m, 2]] = k


PM = json.load(open(os.path.join(pout, 'parts_meta.json'), encoding='utf-8'))
TM, T15 = P['turret_main'], P['turret_15']
shell = load_list(os.path.join(pout, 'turret-main-shell.txt')); CXM = PM['turret-main-shell']['geom']['CX']
g305 = load_list(os.path.join(pout, 'gun305.txt')); tr305 = PM['gun305']['anchors']['trunnion']
for b in P['barbettes']:
    sg = 1 if b['dy'] > 0 else -1; o = np.array([b['x'] - CXM, YC + b['dy'] - CXM, TM['z_table']])
    stamp(shell, o + [CXM + 0.5, CXM + 0.5, 0], [CXM + 0.5, CXM + 0.5, 0], 0 if sg > 0 else 180, 1, 'turret')
    for lat in (-TM['gun_dx'], TM['gun_dx']):
        at = o + [CXM + 0.5 + sg * lat, CXM + 0.5 + sg * TM['gun_fwd'], 1]
        stamp(g305, at, [tr305[0] + 0.5, tr305[1] + 0.5, 0], 0 if sg > 0 else 180, 0.5, 'gun')
sh15 = load_list(os.path.join(pout, 'turret15-shell.txt')); CX15 = PM['turret15-shell']['geom']['CX']
g150 = load_list(os.path.join(pout, 'gun150.txt')); tr150 = PM['gun150']['anchors']['trunnion']
for t in P['turrets_15']:
    f = t['front']; o = np.array([t['x'] - CX15, YC - CX15, T15['z0']])
    stamp(sh15, o + [CX15 + 0.5, CX15 + 0.5, 0], [CX15 + 0.5, CX15 + 0.5, 0], -90 if f > 0 else 90, 1, 'turret')
    stamp(g150, o + [CX15 + 0.5 + f * T15['gun_fwd'], CX15 + 0.5, 0], [tr150[0] + 0.5, tr150[1] + 0.5, 0], -90 if f > 0 else 90, 0.5, 'gun')
tb = load_list(os.path.join(pout, 'torpedo-boat.txt')); tl = PP['torpedo_boat']['len']
for sg in (1, -1):
    stamp(tb, [P['torpedo_boats']['x'] + tl / 2 + 0.5, YC + sg * P['torpedo_boats']['dy'] + 0.5, P['torpedo_boats']['z']], [tl / 2 + 1.0, PP['torpedo_boat']['half'] + 1.5, 0], 0, 1, 'boat')
KIND = {}                                                                 # 部件 → 類別（上色）
for i, nm in enumerate(names):
    k = i + 1
    if nm in ('belt', 'barbettes', 'conning', 'armour-deck'): KIND[k] = 'armor'
    elif nm.startswith(('boilers', 'engine', 'shaft', 'screw', 'funnel', 'floor')): KIND[k] = 'mach'
    elif nm.startswith('mag-'): KIND[k] = 'mag'
    elif nm.startswith('deck') : KIND[k] = 'deck'
    else: KIND[k] = 'other'
for j, nm in enumerate(extra): KIND[len(names) + 1 + j] = {'turret': 'armor', 'gun': 'gun', 'boat': 'other'}[nm]
FILL = {'armor': (150, 70, 80), 'mach': (70, 100, 140), 'mag': (150, 120, 40), 'deck': (40, 78, 140), 'gun': (200, 200, 220), 'other': None}
K = 2
W_IMG = NX * K + 460
img = Image.new('RGB', (W_IMG, 5200), BG); dr = ImageDraw.Draw(img)


def edges(L):
    e = np.zeros(L.shape, bool)
    e[1:, :] |= L[1:, :] != L[:-1, :]; e[:-1, :] |= L[:-1, :] != L[1:, :]
    e[:, 1:] |= L[:, 1:] != L[:, :-1]; e[:, :-1] |= L[:, :-1] != L[:, 1:]
    return e & (L > 0)


def blit(L2, ox, oy, k=K, fill=True):
    """L2[u, v]（u 水平、v 垂直、v 0 在下）畫在 (ox, oy) 左上角。"""
    L = L2.T[::-1]
    if fill:
        a = np.zeros(L.shape + (3,), np.uint8); a[:] = BG
        for kk, kind in KIND.items():
            c = FILL[kind]
            if c: a[L == kk] = c
        img.paste(Image.fromarray(a).resize((L.shape[1] * k, L.shape[0] * k), Image.NEAREST), (ox, oy))
    e = edges(L)
    ys, xs = np.nonzero(e)
    for yy, xx in zip(ys.tolist(), xs.tolist()):
        dr.rectangle([ox + xx * k, oy + yy * k, ox + xx * k + k - 1, oy + yy * k + k - 1], fill=LINE)
    return L.shape[1] * k, L.shape[0] * k


def first_hit(axis, rev):
    b = np.flip(lab, axis) if rev else lab
    m = b > 0
    idx = np.argmax(m, axis=axis)
    v = np.take_along_axis(b, np.expand_dims(idx, axis), axis).squeeze(axis)
    v[~m.any(axis)] = 0
    return v


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
    dr.text((x, y), t, fill=LINE, font=font(32))
    if sub: dr.text((x, y + 40), sub, fill=FAINT, font=font(20))


def zline(oy, z, color, txt, w):
    yy = oy + (NZ - 1 - z) * K + K // 2
    dr.line([ox - 20, yy, ox + w + 20, yy], fill=color, width=1)
    dr.text((ox + w + 26, yy - 12), txt, fill=color, font=font(18))


ox = 90
# ── 一、外形側視 ──
y0 = 120
title(ox, 20, '一、外形側視（右舷）', 'Outboard profile — starboard；z 0 ＝ 龍骨底；比例 0.1 m／格（1 格 ＝ 2 px）')
w, h = blit(first_hit(1, True)[:, :], ox, y0)
zline(y0, ZW, WATER, 'DWL 6.0 m', w)
xs_all = np.nonzero((own > 0).any((1, 2)))[0]
dim(ox + xs_all.min() * K, y0 + h + 22, ox + (xs_all.max() + 1) * K, y0 + h + 22, '全長 %.1f m（含衝角）' % ((xs_all.max() - xs_all.min() + 1) * 0.1), off=64)
wl = np.nonzero(own[:, :, ZW].any(1))[0]
dim(ox + wl.min() * K, y0 + h + 70, ox + (wl.max() + 1) * K, y0 + h + 70, '水線長 %.1f m' % ((wl.max() - wl.min() + 1) * 0.1), off=64)
dim(ox + w + 150, y0 + (NZ - ZW) * K, ox + w + 150, y0 + NZ * K, '吃水 %.1f m' % (ZW * 0.1))
for nm_, z_, c_ in (('艉樓／艏樓 5.2 m', P['z_upper_deck'] + 1, FAINT), ('飛橋 8.1 m', P['z_hurricane'] + 1, FAINT), ('煙囪頂 13.3 m', P['funnel_top'], FAINT)):
    zline(y0, z_, c_, nm_, w)
# ── 二、中線縱剖 ──
y1 = y0 + h + 170
title(ox, y1 - 60, '二、中線縱剖', 'Inboard profile on centreline —— 下甲板、主甲板、艉樓／艏樓、機艙、鍋爐（右舷那一座）、彈藥庫、梯子')
sec = lab[:, YC, :].copy()
mir = np.zeros_like(sec)
for nm in ('boilers-aft', 'boilers-fwd', 'engine'):                        # 中線剖不到右舷的機器 ⇒ 疊上右舷那一份（看得出位置）
    i = names.index(nm) + 1
    hit = (own == i).any(1)
    mir[hit & (sec == 0)] = i
sec = np.where(sec > 0, sec, mir)
w, h = blit(sec, ox, y1)
zline(y1, ZW, WATER, 'DWL', w)
for nm, xx, zz in [('機艙', 300, 40), ('鍋爐 1–4', 430, 40), ('前彈藥庫', 600, 30), ('後彈藥庫', 170, 30), ('下甲板', 120, 63), ('主甲板', 330, 88), ('艉樓', 60, 115), ('艏樓', 760, 115)]:
    dr.text((ox + xx * K, y1 + (NZ - 1 - zz) * K - 22), nm, fill=ACC, font=font(18))
# ── 三、上層平面（砲塔、射界）──
y2 = y1 + h + 140
title(ox, y2 - 60, '三、上層平面與射界', 'Plan from above —— 船頭朝右、右舷在下；扇形 ＝ 開火範圍（綠）、轉動範圍（虛線）；check_arcs.py 量的')
top = first_hit(2, True)
w, h = blit(top[:, ::-1], ox, y2)


def to_plan(x, y): return ox + (x + 0.5) * K, y2 + (y + 0.5) * K       # 平面：y 往下（右舷在下）


def wedge(cx, cy, front, a0, a1, r, color, dash=False):
    pts = [to_plan(cx, cy)]
    for a in np.linspace(a0, a1, max(6, int(abs(a1 - a0) / 3))):
        ang = math.radians(front + a)
        pts.append(to_plan(cx + r * math.cos(ang), cy + r * math.sin(ang)))
    pts.append(to_plan(cx, cy))
    if dash:
        for i in range(1, len(pts) - 2, 2): dr.line([pts[i], pts[i + 1]], fill=color, width=2)
    else:
        dr.line(pts, fill=color, width=3)


TUR = [('turret-' + b['name'], b['x'], YC + b['dy'], 90 if b['dy'] > 0 else -90, 105) for b in P['barbettes']]
TUR += [('turret15-' + t['name'], t['x'], YC, 0 if t['front'] > 0 else 180, 70) for t in P['turrets_15']]
for nm, cx, cy, front, r in TUR:
    a = ARC[nm]
    wedge(cx, cy, front, a['arc'][0], a['arc'][1], r * 0.8, FAINT, dash=True)
    wedge(cx, cy, front, a['fire'][0], a['fire'][1], r, GREEN)
    tx, ty = to_plan(cx, cy)
    dr.text((tx + 8, ty + 6), '%s　開火 %d～%d°' % ({'turret-S': '右主砲', 'turret-P': '左主砲', 'turret15-aft': '艉 15 cm', 'turret15-fwd': '艏 15 cm'}[nm], a['fire'][0], a['fire'][1]), fill=ACC, font=font(18))
dim(ox + w + 40, y2 + (YC - 91) * K, ox + w + 40, y2 + (YC + 92) * K, '寬 18.3 m')
# ── 四、主甲板平面 ──
y3 = y2 + h + 170
title(ox, y3 - 60, '四、主甲板平面（z ＝ 主甲板走路格往上 3 格的切面）', 'Main deck plan —— 露砲台、梯子、艉樓與艏樓裡、煙囪、通風筒')
zc = P['z_main_deck'] + 4
w, h = blit(lab[:, ::-1, zc], ox, y3)
for L in M['anchors']['ladders']:
    x_, y_ = L['head'][0], L['head'][1]
    if L['head'][2] in (P['z_main_deck'] + 1, P['z_upper_deck'] + 1, P['z_hurricane'] + 1, P['turret_main']['z_table']):
        dr.ellipse([ox + x_ * K - 5, y3 + y_ * K - 5, ox + x_ * K + 5, y3 + y_ * K + 5], outline=ACC, width=2)
dr.text((ox, y3 + h + 8), '○ ＝ 梯頭（梯子 kind=ladders，foot／lo／hi／head 四點）', fill=FAINT, font=font(18))
# ── 五、橫剖面 ──
y4 = y3 + h + 120
title(ox, y4 - 60, '五、橫剖面（從船尾往船頭看；左 ＝ 左舷）', 'Sections —— 機艙、鍋爐、左露砲台、右露砲台、艏樓')
k2 = 2
xx0 = ox
for xs in (300, 446, P['barbettes'][0]['x'], P['barbettes'][1]['x'], 800):
    L2 = lab[xs, :, :260]
    w2, h2 = blit(L2, xx0, y4, k=k2)
    yy = y4 + (260 - 1 - ZW) * k2
    dr.line([xx0 - 6, yy, xx0 + w2 + 6, yy], fill=WATER, width=1)
    dr.text((xx0, y4 + h2 + 6), 'x %d（離船尾 %.1f m）' % (xs, (xs - P['x_stern_deck']) * 0.1), fill=FAINT, font=font(18))
    xx0 += w2 + 26
# ── 六、主砲塔詳圖 ──
y5 = y4 + 260 * k2 + 110
title(ox, y5 - 60, '六、主砲塔詳圖（砲塔層：轉盤＋砲罩＋兩門 30.5 cm 克虜伯 L/25）', 'Main turret —— 平面（砲軸高度）／側剖（砲 a）；殼 0.1 m／格、砲 0.05 m／格（scale 0.5）')
b = P['barbettes'][1]; cx, cy = b['x'], YC + b['dy']
R = 60
sub = lab[cx - R:cx + R + 1, cy - R:cy + R + 1, :]
k3 = 4
wa, ha = blit(sub[:, ::-1, TM['gun_axis']], ox, y5, k=k3)
gx = cy + TM['gun_dx']
wb, hb = blit(lab[cx - R:cx + R + 1, gx, 80:135].transpose(0, 1)[:, :], ox + wa + 60, y5, k=k3)
wc, hc = blit(lab[cx, cy - R:cy + R + 1, 80:135], ox + wa + wb + 120, y5, k=k3)
dr.text((ox, y5 + ha + 10), '露砲台 12 in：外徑 %.1f m；轉盤半徑 %.1f m；砲罩外徑 %.1f m；砲軸水線上 %.1f m；兩門砲軸距 %.1f m' %
        (2 * P['barbette_r'][1] * 0.1 + 0.1, TM['r_table'] * 0.1, 2 * TM['r_hood'][1] * 0.1 + 0.1, (TM['gun_axis'] - ZW) * 0.1, 2 * TM['gun_dx'] * 0.1), fill=ACC, font=font(20))
# ── 圖說 ──
yb = y5 + max(ha, hb, hc) + 70
notes = [
    '主尺寸：全長 94.5 m（含衝角）、水線長 %.1f m、寬 18.3 m、吃水 6.0 m；排水量（設計水線以下外形）%.0f t —— 史料 7,220–7,670 t。' % ((wl.max() - wl.min() + 1) * 0.1, M['disp_t']),
    '裝甲：城堡 14 in 複合裝甲（x 248–676、水線下 1.8 m 到水線上 1.6 m）、露砲台 12 in、司令塔 8 in、城堡上的裝甲甲板 3 in；全部是獨立的關聯、material=iron。',
    '主砲：4 × 30.5 cm 克虜伯 L/25，兩座梯次配置的露砲台（右舷那座在前，Feng 2018；1883 年設計圖 Fig.9）；砲罩照 1885–1894 年帶罩的樣子（1894 年拆掉）。',
    '副砲：艏、艉各一門 15 cm 克虜伯 L/35（輕砲塔）；機關砲：6 × 37 mm 哈乞開斯五管轉膛砲（兩個桅樓各兩門、飛橋甲板前角兩門）。',
    '機器：8 座圓筒鍋爐分 4 間（兩舷各一、爐門朝中線）、兩根煙囪；兩具臥式三缸主機、兩支軸、兩個 3 m 四葉螺旋槳；設計 6,000 ihp、14.5 kn（鎮遠試航 15.4 kn）。',
    '塗裝：1888–1894 年 —— 黑殼、白上層、黃（buff）煙囪與桅；水線下紅（沒查到，設計決定）。旗：1889 年起的長方形黃龍旗（2:3、藍龍、左上紅珠）。',
    '史料：1883《Die Kriegsschiffbauten 1881–1882》設計圖 Fig.8–14（Wikimedia Commons，公有領域）、照片 NH 1926、EN／zh／ja Wikipedia、navypedia；每個數字的出處在 plan.json provenance。',
]
dr.rectangle([ox - 12, yb - 12, ox + NX * K + 300, yb + 54 + 30 * len(notes)], outline=LINE, width=2)
dr.text((ox, yb), '定遠 TING-YUEN（1884，北洋艦隊旗艦）—— 遊戲用造船圖紙　繪：trailhead　比例 0.1 m／格（砲 0.05 m、37 mm 砲 0.02 m）', fill=LINE, font=font(26))
for i, s in enumerate(notes): dr.text((ox, yb + 44 + 30 * i), s, fill=FAINT, font=font(20))
img = img.crop((0, 0, img.width, yb + 70 + 30 * len(notes)))
img.save(png)
print('ok', img.size)
