# 加拉塔塔 1453 的圖紙（TASK-0748）：照 plan.json 的參數畫線（⛔ 不從格子拍），標尺寸。python -I -X utf8 -B draft.py <design 資料夾>
#   ⇒ sheets/blueprint.png：南立面、南北剖面、三層平面、配置圖、圖框（出處、比例尺、圖例）
import sys, os, json, math
from PIL import Image, ImageDraw, ImageFont

D = os.path.abspath(sys.argv[1])
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
T, B = P['tower'], P['barbican']
FONT = None
for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/mingliu.ttc'):
    if os.path.exists(f): FONT = f; break
def font(sz): return ImageFont.truetype(FONT, sz) if FONT else ImageFont.load_default()
F12, F14, F18, F26 = font(12), font(14), font(18), font(26)
# 中文字型（微軟正黑體）沒有土耳其字母 ğ ⇒ 圖上一律寫 Saglam（出處的正確拼法在 plan.json）
INK, RED, BLUE, GREY, PAPER = (34, 46, 74), (176, 40, 40), (40, 80, 160), (150, 150, 150), (244, 240, 228)
W, H = 2600, 1500
im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
_rect = d.rectangle
def _rect_sorted(xy, **k):                                      # 左右、上下照大小排（剖面左右兩半共用一段程式，負向那一半座標是反的）
    x0, y0, x1, y1 = xy
    return _rect(sorted([x0, x1])[:1] + sorted([y0, y1])[:1] + sorted([x0, x1])[1:] + sorted([y0, y1])[1:], **k)
d.rectangle = _rect_sorted
S = 20.0                                                     # 立面、剖面：每公尺幾像素


def dim_v(x, y0m, y1m, base, label, side=1):                 # 垂直尺寸線（y 是公尺高度）
    ya, yb = base - y0m * S, base - y1m * S
    d.line([(x, ya), (x, yb)], fill=RED, width=1)
    for y in (ya, yb): d.line([(x - 4, y), (x + 4, y)], fill=RED, width=1)
    d.text((x + 6 * side if side > 0 else x - 6 - d.textlength(label, font=F12), (ya + yb) / 2 - 7), label, fill=RED, font=F12)


def dim_h(x0, x1, y, label):
    d.line([(x0, y), (x1, y)], fill=RED, width=1)
    for x in (x0, x1): d.line([(x, y - 4), (x, y + 4)], fill=RED, width=1)
    d.text(((x0 + x1) / 2 - d.textlength(label, font=F12) / 2, y + 4), label, fill=RED, font=F12)


def level(x0, x1, base, zm, label):
    y = base - zm * S
    d.line([(x0, y), (x1, y)], fill=GREY, width=1)
    d.text((x1 + 4, y - 7), label, fill=GREY, font=F12)


ro, ri, tal = T['r_out'], T['r_in'], T['talus_dr']
RF, PA, CO, AR, FI = T['roof'], T['parapet'], T['corbel'], T['arcade'], T['finial']
apex = RF['z_eave'] + RF['h']; pole_top = apex + FI['pole_h']

# ═════ 南立面 ═════
cx, base = 300, 1080
d.text((cx - 120, 60), '南立面（城裡這一側）', fill=INK, font=F18)
d.polygon([(cx - (ro + tal) * S, base), (cx - ro * S, base - T['talus_h'] * S), (cx + ro * S, base - T['talus_h'] * S), (cx + (ro + tal) * S, base)], outline=INK, fill=(222, 206, 170))
d.rectangle([cx - ro * S, base - T['masonry_top'] * S, cx + ro * S, base - T['talus_h'] * S], outline=INK, fill=(214, 196, 158))
for zb in T['brick_courses']:
    d.rectangle([cx - ro * S, base - (zb + 0.4) * S, cx + ro * S, base - zb * S], fill=(178, 82, 40))
n = AR['n']; vis = [j for j in range(n) if math.cos(math.radians(-180 + (j + 0.5) * 360 / n - 90)) > 0.15]
for j in vis:                                                 # 看得到的那一半盲拱（照角度投影到立面）
    a = math.radians(-180 + (j + 0.5) * 360 / n); xc = cx - ro * math.cos(a) * S
    hw = AR['w'] / 2 * S * abs(math.sin(a + math.pi / 2)); y0, y1 = base - AR['z0'] * S, base - AR['z1'] * S
    if hw < 3: continue
    d.rectangle([xc - hw, y1 + AR['w'] / 2 * S, xc + hw, y0], fill=(165, 150, 125), outline=INK)
    d.pieslice([xc - hw, y1, xc + hw, y1 + AR['w'] * S], 180, 360, fill=(165, 150, 125), outline=(178, 82, 40), width=2)
d.rectangle([cx - (ro + CO['out']) * S, base - CO['z1'] * S, cx + (ro + CO['out']) * S, base - CO['z0'] * S], outline=INK, fill=(200, 190, 170))
pr = ro + CO['out']
d.rectangle([cx - pr * S, base - (PA['z0'] + PA['h']) * S, cx + pr * S, base - PA['z0'] * S], outline=INK, fill=(214, 196, 158))
for j in range(PA['n'] // 2):
    a = math.pi * (j + 0.8) / (PA['n'] // 2); xa = cx - pr * math.cos(a) * S
    d.rectangle([xa - 0.25 * S, base - (PA['z0'] + PA['h']) * S, xa + 0.25 * S, base - (PA['z0'] + PA['h'] - PA['crenel_h']) * S], fill=PAPER)
d.polygon([(cx - RF['r_eave'] * S, base - RF['z_eave'] * S), (cx + RF['r_eave'] * S, base - RF['z_eave'] * S), (cx, base - apex * S)], outline=INK, fill=(150, 150, 175))
d.line([(cx, base - apex * S), (cx, base - pole_top * S)], fill=INK, width=3)
d.ellipse([cx - FI['orb_r'] * S, base - (pole_top + 2 * FI['orb_r']) * S, cx + FI['orb_r'] * S, base - pole_top * S], fill=(230, 190, 40), outline=INK)
ct = pole_top + 2 * FI['orb_r']
d.line([(cx, base - ct * S), (cx, base - (ct + FI['cross_h']) * S)], fill=(200, 160, 20), width=4)
d.line([(cx - 0.8 * S, base - (ct + FI['cross_h'] * 0.65) * S), (cx + 0.8 * S, base - (ct + FI['cross_h'] * 0.65) * S)], fill=(200, 160, 20), width=4)
fw, fh = FI['flag']
d.rectangle([cx + 2, base - (pole_top - 0.2) * S, cx + 2 + fw * S, base - (pole_top - 0.2 - fh) * S], fill=(250, 250, 250), outline=INK)
d.line([(cx + 2 + fw * S / 2, base - (pole_top - 0.2) * S), (cx + 2 + fw * S / 2, base - (pole_top - 0.2 - fh) * S)], fill=RED, width=5)
d.line([(cx + 2, base - (pole_top - 0.2 - fh / 2) * S), (cx + 2 + fw * S, base - (pole_top - 0.2 - fh / 2) * S)], fill=RED, width=5)
Dr = T['door']; d.rectangle([cx - Dr['w'] / 2 * S, base - (Dr['h'] - Dr['w'] / 2) * S, cx + Dr['w'] / 2 * S, base], fill=(90, 60, 30), outline=INK)
d.pieslice([cx - Dr['w'] / 2 * S, base - Dr['h'] * S, cx + Dr['w'] / 2 * S, base - (Dr['h'] - Dr['w']) * S], 180, 360, fill=(90, 60, 30), outline=INK)
for a in (-130, -40, 20, 160):                                # 示意的窄射口
    xs = cx - ro * math.cos(math.radians(a)) * S
    for zb in (6.4, 10.6, 14.5):
        d.rectangle([xs - 1, base - (zb + 1.5) * S, xs + 1, base - zb * S], fill=(60, 50, 40))
d.line([(cx - 260, base), (cx + 260, base)], fill=INK, width=2)
for zm, lb in ((T['talus_h'], '+3.00 牆腳'), (13.21, '+13.21 磚層（2 層）'), (17.17, '+17.17 磚層（3 層）'), (T['genoese_irregular_top'], '+21.09 熱那亞砌體頂（4 層）※'),
               (AR['z0'], '+25.60 盲拱'), (PA['z0'], '+30.00 石砌頂、雉堞'), (RF['z_eave'], '+32.00 簷'), (apex, '+41.00 錐頂'), (pole_top, '+44.60 旗杆頂')):
    level(cx + 200, cx + 230, base, zm, lb)
dim_h(cx - ro * S, cx + ro * S, base + 18, '外徑 16.45 m')
dim_h(cx - (ro + tal) * S, cx + (ro + tal) * S, base + 46, '牆腳 17.65 m')
dim_h(cx - RF['r_eave'] * S, cx + RF['r_eave'] * S, base - RF['z_eave'] * S - 10, '簷 18.80 m')
dim_v(cx - 200, 0, T['masonry_top'], base, '30.00 m', side=-1)
d.text((cx - 290, base - 15.6 * S), '（史料：至少 30 m）', fill=RED, font=F12)

# ═════ 南北剖面 A–A ═════
cx2, base2 = 960, 1080
d.text((cx2 - 220, 60), '剖面 A–A（南北向，左 ＝ 北・城外）', fill=INK, font=F18)
for sgn in (-1, 1):
    x_in, x_out = cx2 + sgn * ri * S, cx2 + sgn * ro * S
    d.rectangle([min(x_in, x_out), base2 - T['masonry_top'] * S, max(x_in, x_out), base2], fill=(205, 186, 150), outline=INK)
    d.polygon([(x_out, base2), (x_out, base2 - T['talus_h'] * S), (x_out + sgn * tal * S, base2)], fill=(205, 186, 150), outline=INK)
    for zb in T['brick_courses']: d.rectangle([min(x_in, x_out), base2 - (zb + 0.4) * S, max(x_in, x_out), base2 - zb * S], fill=(178, 82, 40))
    d.rectangle([min(x_in, x_out) + (0 if sgn > 0 else 0), base2 - (T['genoese_irregular_top'] - 0.3) * S, min(x_in, x_out) + 1.2 * S, base2 - 2 * S], outline=GREY)
for fz in [0.0] + T['floors']:
    d.rectangle([cx2 - ri * S, base2 - (fz + 0.2) * S, cx2 + ri * S, base2 - fz * S], fill=(120, 80, 40))
d.polygon([(cx2 - RF['r_eave'] * S, base2 - RF['z_eave'] * S), (cx2 + RF['r_eave'] * S, base2 - RF['z_eave'] * S), (cx2, base2 - apex * S)], outline=INK, fill=(150, 150, 175))
for sgn in (-1, 1):
    d.rectangle([cx2 + sgn * (ro - PA['t'] + CO['out']) * S, base2 - (PA['z0'] + PA['h']) * S, cx2 + sgn * (ro + CO['out']) * S, base2 - PA['z0'] * S], fill=(205, 186, 150), outline=INK)
    d.rectangle([cx2 + sgn * (ro - 1.4) * S, base2 - RF['z_eave'] * S, cx2 + sgn * (ro - 0.8) * S, base2 - PA['z0'] * S], fill=(205, 186, 150), outline=INK)
xb = cx2 - B['r'] * S                                         # 外堡（北、城外）
d.rectangle([xb - B['t'] / 2 * S, base2 - B['h'] * S, xb + B['t'] / 2 * S, base2], fill=(205, 186, 150), outline=INK)
d.text((xb - 40, base2 - B['h'] * S - 22), '1452 外堡', fill=INK, font=F12)
d.line([(cx2 - 330, base2), (cx2 + 230, base2)], fill=INK, width=2)
dim_h(cx2 - ro * S, cx2 - ri * S, base2 - 4 * S, '3.75')
dim_h(cx2 - ri * S, cx2 + ri * S, base2 - 7.4 * S, '內徑 8.95 m')
dim_h(xb, cx2, base2 + 20, '外堡中線半徑 14.0 m')
dim_v(xb - 30, 0, B['h'], base2, '5.0 m', side=-1)
d.text((cx2 - 210, base2 + 50), '※ 1～4 層牆裡有磚拱的樓梯廊道（Saglam 2021；沒雕，灰框示意）', fill=GREY, font=F12)

# ═════ 平面（三層）═════
def plan_at(ox, oy, s, title, kind):
    d.text((ox - 90, oy - s * 11.5), title, fill=INK, font=F14)
    d.ellipse([ox - ro * s, oy - ro * s, ox + ro * s, oy + ro * s], fill=(214, 196, 158), outline=INK)
    d.ellipse([ox - ri * s, oy - ri * s, ox + ri * s, oy + ri * s], fill=PAPER if kind != 'top' else (150, 150, 175), outline=INK)
    def ray(a, w, col):
        ar = math.radians(a); ca, sa = math.cos(ar), math.sin(ar)
        p = lambda r, t: (ox + (r * ca - t * sa) * s, oy + (r * sa + t * ca) * s)
        d.polygon([p(ri, -w / 2), p(ro + 0.1, -w / 2), p(ro + 0.1, w / 2), p(ri, w / 2)], fill=col)
    if kind == 'ground':
        ray(T['door']['angle'], T['door']['w'], (90, 60, 30))
        for a in (-140, -35, 25, 150): ray(a, 0.35, PAPER)
        d.text((ox - 12, oy + ro * s + 4), '門', fill=INK, font=F12)
    if kind == 'emb':
        for a in T['embrasures']['angles']: ray(a, T['embrasures']['w'] + 0.6, PAPER)
        d.text((ox - 60, oy + ro * s + 4), '3 個大射口朝城外', fill=INK, font=F12)
    if kind == 'top':
        pr = ro + CO['out']
        d.ellipse([ox - pr * s, oy - pr * s, ox + pr * s, oy + pr * s], outline=INK, width=2)
        for j in range(PA['n']):
            a = math.radians(-180 + (j + 0.8) * 360 / PA['n']); d.line([(ox + (pr - PA['t']) * math.cos(a) * s, oy + (pr - PA['t']) * math.sin(a) * s), (ox + pr * math.cos(a) * s, oy + pr * math.sin(a) * s)], fill=PAPER, width=3)
        d.ellipse([ox - RF['r_eave'] * s, oy - RF['r_eave'] * s, ox + RF['r_eave'] * s, oy + RF['r_eave'] * s], outline=BLUE, width=1)
        d.text((ox - 70, oy + RF['r_eave'] * s + 4), '藍圈 ＝ 屋簷（伸出雉堞外）', fill=BLUE, font=F12)
    d.text((ox - 4, oy - ro * s - 18), 'N', fill=INK, font=F14)
ps = 9.0
plan_at(1450, 300, ps, '平面 ±0（地面層）', 'ground')
plan_at(1720, 300, ps, '平面 +18（3 層，砲眼）', 'emb')
plan_at(1990, 300, ps, '平面 +31（雉堞與屋簷）', 'top')

# ═════ 配置圖 ═════
ox, oy, s = 1700, 820, 9.0
d.text((ox - 260, oy - 250), '配置圖（作品框 ＝ 地塊 32 × 32 m；上 ＝ 北）', fill=INK, font=F14)
d.rectangle([ox - 16 * s, oy - 16 * s, ox + 16 * s, oy + 16 * s], outline=GREY)
d.ellipse([ox - ro * s, oy - ro * s, ox + ro * s, oy + ro * s], fill=(214, 196, 158), outline=INK)
# 外堡：作品座標的角度 a（0 ＝ +x ＝ 東邊在左；配置圖照地圖畫：東在右、北在上）⇒ 地圖角 ＝ 180 − a
pts = []
for k in range(0, 61):
    a = B['a0'] + (B['a1'] - B['a0']) * k / 60
    am = math.radians(180 - a)
    pts.append((ox + B['r'] * math.cos(am) * s, oy + B['r'] * math.sin(am) * s))
d.line(pts, fill=INK, width=int(B['t'] * s))
for a, lb in ((B['a0'], '城牆往西北'), (B['a1'], '城牆往東南')):
    am = math.radians(180 - a)
    d.line([(ox, oy), (ox + 26 * math.cos(am) * s, oy + 26 * math.sin(am) * s)], fill=GREY, width=3)
    d.text((ox + 27 * math.cos(am) * s - 30, oy + 27 * math.sin(am) * s), lb, fill=GREY, font=F12)
d.text((ox - 28, oy - 26), '加拉塔塔', fill=INK, font=F12)
d.text((ox - 30, oy - 15.8 * s), '外堡 1452', fill=INK, font=F12)
d.text((ox - 40, oy + 9 * s), '門（城裡）', fill=INK, font=F12)
d.polygon([(ox + 230, oy - 200), (ox + 222, oy - 175), (ox + 238, oy - 175)], fill=INK); d.text((ox + 225, oy - 222), 'N', fill=INK, font=F14)

# ═════ 圖框 ═════
x0 = 2140
d.rectangle([x0, 40, W - 40, H - 40], outline=INK, width=2)
d.text((x0 + 20, 60), '加拉塔塔 1453', fill=INK, font=F26)
d.text((x0 + 20, 100), '基督塔 Christea Turris（熱那亞，1348）', fill=INK, font=F14)
lines = ['比例 1 : 50（立面、剖面 20 px／m）；平面、配置 9 px／m', '作品 kaguya-galata-tower-1453（0.2 m／格、160×160×250）',
         '繪製：kaguya 2026-10-20（TASK-0748）', '', '依據（plan.json provenance 有逐項出處）：',
         '・外徑 16.45、內徑 8.95、牆厚 3.75 m：en.wikipedia', '・熱那亞時期至少 30 m；砌體到 4 層 +21.09；',
         '  磚層 +13.21／+17.17；射口深窄、4 層以下不規則；', '  3 層三個大射口；頂層盲拱＋雉堞＋圓錐頂', '  （1420 Buondelmonti）；簷伸出雉堞（Düsseldorf', '  抄本 c.1485）；熱那亞旗、帶十字的球；1452 外堡',
         '  —— 都是 Saglam 2021（In-Scription 3）', '', '設計決定（資料沒有的）：', '・30 m 這個高度、盲拱 16 個、雉堞 24 個、簷 32 m、',
         '  錐高 9 m、外堡半徑 14 m 高 5 m、門的位置、', '  射口的位置與數量、石色比例', '', '圖例：', '  紅線 ＝ 尺寸　灰線 ＝ 標高　藍圈 ＝ 屋簷']
for i, t in enumerate(lines): d.text((x0 + 20, 140 + i * 22), t, fill=INK, font=F12)
bx, by = x0 + 20, H - 120                                     # 比例尺 0–10 m
for k in range(5):
    d.rectangle([bx + k * 2 * S, by, bx + (k + 1) * 2 * S, by + 8], fill=INK if k % 2 == 0 else PAPER, outline=INK)
d.text((bx, by + 12), '0', fill=INK, font=F12); d.text((bx + 10 * S - 16, by + 12), '10 m', fill=INK, font=F12)
os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
im.save(os.path.join(D, 'sheets', 'blueprint.png'))
print('ok', os.path.join(D, 'sheets', 'blueprint.png'))
