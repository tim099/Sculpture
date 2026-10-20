# 大競技場 1453 的圖紙（TASK-0748）：照 plan.json 的參數畫線（⛔ 不從格子拍），標尺寸。python -I -X utf8 -B draft.py <design 資料夾>
#   ⇒ sheets/blueprint.png：平面（看台、半圓端柱廊、中線與碑柱、起跑門、皇帝包廂）、看台橫剖面、三座碑的立面、圖框（出處、比例尺）
#   抄聖索菲亞 kaguya-hagia-sophia-1453/design/draft.py 的畫法（字型、尺寸線）；圖面重寫。
import sys, os, json, math, random
from PIL import Image, ImageDraw, ImageFont

D = os.path.abspath(sys.argv[1])
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
FONT = None
for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/mingliu.ttc'):
    if os.path.exists(f): FONT = f; break
def font(sz): return ImageFont.truetype(FONT, sz) if FONT else ImageFont.load_default()
F12, F14, F18, F26 = font(12), font(14), font(18), font(26)
INK, RED, BLUE, GREY, PAPER = (34, 46, 74), (176, 40, 40), (40, 80, 160), (150, 150, 150), (244, 240, 228)
BRICK, SEAT, MARBLE, GRANITE, STONE, BRONZE = (196, 120, 92), (214, 196, 170), (232, 228, 214), (196, 120, 130), (190, 178, 150), (110, 100, 60)
W, H = 3000, 2000
im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
M = P['mpv']
O, T, S, K, Q, SP, SN, MO = P['outer'], P['track'], P['stands'], P['carceres'], P['kathisma'], P['sphendone'], P['spina'], P['monuments']


def dim_h(x0, x1, y, label, col=RED):
    d.line([(x0, y), (x1, y)], fill=col); d.line([(x0, y - 5), (x0, y + 5)], fill=col); d.line([(x1, y - 5), (x1, y + 5)], fill=col)
    d.text(((x0 + x1) / 2 - d.textlength(label, font=F12) / 2, y + 3), label, fill=col, font=F12)


def dim_v(x, y0, y1, label, col=RED):
    d.line([(x, y0), (x, y1)], fill=col); d.line([(x - 5, y0), (x + 5, y0)], fill=col); d.line([(x - 5, y1), (x + 5, y1)], fill=col)
    d.text((x + 6, (y0 + y1) / 2 - 7), label, fill=col, font=F12)


# ── 平面：模型 y（北端起跑門 → 半圓端）往右、x（東南 → 西北）往下；每公尺 5 px ──
s = 5.0; ox, oy = 120, 160
def px(yc): return ox + yc * M * s
def py(xc): return oy + xc * M * s
d.text((60, 70), '平面（左 ＝ 北端起跑門、朝方位 38°；上 ＝ 東南 ＝ 大皇宮那一側）', fill=INK, font=F18)
xc, ys, r = O['half_w'], O['straight_to'], O['r']
tw = T['half_w']
for side in (-1, 1):                                                  # 看台帶（跑道邊 → 外緣）
    a, b = xc + side * tw, xc + side * O['half_w']
    d.rectangle([px(S['y0']), py(min(a, b)), px(ys), py(max(a, b))], fill=SEAT, outline=INK)
    wa = xc + side * (O['half_w'] - S['wall_t'])
    d.rectangle([px(S['y0']), py(min(wa, b)), px(ys), py(max(wa, b))], fill=BRICK)
pts = [(px(ys + r * math.sin(math.pi * i / 72)), py(xc + r * math.cos(math.pi * i / 72))) for i in range(73)]
d.line(pts, fill=INK, width=2)
rnd = random.Random(SP['seed']); gone = set(rnd.sample(range(1, SP['cols'] - 1), SP['cols'] - SP['standing']))
for i in range(SP['cols']):
    t = math.pi * i / (SP['cols'] - 1)
    cx_, cy_ = px(ys + SP['r'] * math.sin(t)), py(xc + SP['r'] * math.cos(t))
    if i in gone: d.ellipse([cx_ - 3, cy_ - 3, cx_ + 3, cy_ + 3], outline=GREY)
    else: d.ellipse([cx_ - 4, cy_ - 4, cx_ + 4, cy_ + 4], fill=MARBLE, outline=INK)
d.rectangle([px(K['y0']), py(xc - tw), px(K['y0'] + K['t']), py(xc + tw)], fill=BRICK, outline=INK)
pitch = 2 * tw / K['gates']
for g in range(K['gates']):
    gx = xc - tw + pitch * (g + 0.5)
    d.rectangle([px(K['y0']), py(gx - K['gate_w'] / 2), px(K['y0'] + K['t']), py(gx + K['gate_w'] / 2)], fill=PAPER)
d.rectangle([px(Q['y0']), py(Q['x0']), px(Q['y1']), py(Q['x1'])], fill=(170, 90, 70), outline=INK)
d.text((px(Q['y0']), py(Q['x0']) - 18), '皇帝包廂（殘）', fill=INK, font=F12)
d.rectangle([px(SN['y0']), py(SN['x'] - SN['w'] / 2), px(SN['y1']), py(SN['x'] + SN['w'] / 2)], fill=STONE, outline=INK)
for nm, key, col in (('狄奧多西方尖碑', 'theodosius', GRANITE), ('蛇柱', 'serpent', BRONZE), ('砌石方尖碑', 'walled', STONE)):
    y_ = MO[key]['y']; d.rectangle([px(y_) - 7, py(xc) - 7, px(y_) + 7, py(xc) + 7], fill=col, outline=INK)
    d.text((px(y_) - d.textlength(nm, font=F12) / 2, py(xc) + 12), nm, fill=INK, font=F12)
for c in MO['columns']:
    d.ellipse([px(c['y']) - 5, py(xc) - 5, px(c['y']) + 5, py(xc) + 5], fill=MARBLE, outline=INK)
yb = py(2 * O['half_w']) + 40
dim_h(px(0), px(ys + r), yb, '450 m（外框）')
dim_h(px(MO['theodosius']['y']), px(MO['serpent']['y']), py(xc) - 30, '%.1f m' % ((MO['serpent']['y'] - MO['theodosius']['y']) * M), BLUE)
dim_h(px(MO['serpent']['y']), px(MO['walled']['y']), py(xc) - 30, '%.1f m' % ((MO['walled']['y'] - MO['serpent']['y']) * M), BLUE)
dim_h(px(SN['y0']), px(SN['y1']), py(xc) + 50, '中線 %.0f m' % ((SN['y1'] - SN['y0']) * M), BLUE)
dim_v(px(0) - 40, py(0), py(2 * O['half_w']), '130 m')
dim_v(px(ys) + 30, py(xc - tw), py(xc + tw), '跑道 %.0f m' % (2 * tw * M), BLUE)
dim_h(px(ys), px(ys + r), py(xc) + 90, 'R %.0f m' % (r * M))
d.text((px(ys + 40), py(xc - 10)), '半圓端柱廊：37 個柱位、留 30 根（○ ＝ 1453 年已倒）', fill=INK, font=F12)

# ── 看台橫剖面（跑道邊 → 外牆）；每公尺 14 px ──
s2 = 14.0; gx0, gz0 = 140, 1180
d.text((60, 860), '看台橫剖面（長邊、完整那幾段；左 ＝ 跑道邊、右 ＝ 外牆外面）', fill=INK, font=F18)
def sx(v): return gx0 + v * M * s2
def sz(v): return gz0 - v * M * s2
prof = [(sx(0), sz(0)), (sx(0), sz(S['podium_h']))]
for i in range(S['tiers']):
    x_ = 2 + i * S['tier_w']
    prof += [(sx(x_), sz(S['podium_h'] + i * S['tier_h'])), (sx(x_), sz(S['podium_h'] + (i + 1) * S['tier_h'])), (sx(x_ + S['tier_w']), sz(S['podium_h'] + (i + 1) * S['tier_h']))]
wl = O['half_w'] - T['half_w']
prof += [(sx(wl - S['wall_t']), sz(S['wall_h'])), (sx(wl), sz(S['wall_h'])), (sx(wl), sz(0))]
d.polygon(prof, fill=SEAT, outline=INK)
d.rectangle([sx(wl - S['wall_t']), sz(S['wall_h']), sx(wl), sz(0)], fill=BRICK, outline=INK)
A = S['arch']; d.rectangle([sx(wl - A['depth']), sz(A['h']), sx(wl), sz(0)], fill=(60, 50, 40))
dim_v(sx(wl) + 30, sz(0), sz(S['wall_h']), '%.1f m' % (S['wall_h'] * M))
dim_h(sx(0), sx(wl), sz(0) + 20, '%.1f m' % (wl * M))
d.text((sx(4), sz(S['podium_h']) - 22), '基座 %.1f m' % (S['podium_h'] * M), fill=BLUE, font=F12)
d.text((sx(20), sz(20) - 40), '%d 階（每階 %.1f m 寬、%.1f m 高）' % (S['tiers'], S['tier_w'] * M, S['tier_h'] * M), fill=BLUE, font=F12)
d.text((sx(wl) - 40, sz(A['h']) - 18), '拱室', fill=(240, 240, 240), font=F12)
d.text((sx(0), sz(0) + 44), '1453 年：每 20 m 一段，55% 完整、30% 上層塌到 60–80%、15% 只剩三成（設計決定）', fill=INK, font=F12)

# ── 三座碑的立面；每公尺 18 px ──
s3 = 18.0; bx0, bz0 = 1500, 1450
d.text((1400, 860), '中線的碑柱立面（同一個比例）', fill=INK, font=F18)
def mz(v): return bz0 - v * M * s3
def stack(cx, layers):
    z = 0
    for w_, h_, col in layers:
        d.rectangle([cx - w_ * M * s3 / 2, mz(z + h_), cx + w_ * M * s3 / 2, mz(z)], fill=col, outline=INK); z += h_
    return z
Tt = MO['theodosius']; c1 = bx0 + 60
z = stack(c1, [(Tt['steps'][0], Tt['steps'][1], MARBLE), (Tt['base1'][0], Tt['base1'][1], MARBLE), (Tt['base2'][0], Tt['base2'][1], MARBLE), (Tt['shaft'][0], Tt['blocks'][1], BRONZE)])
s0, s1, sh = Tt['shaft']
d.polygon([(c1 - s0 * M * s3 / 2, mz(z)), (c1 + s0 * M * s3 / 2, mz(z)), (c1 + s1 * M * s3 / 2, mz(z + sh)), (c1 - s1 * M * s3 / 2, mz(z + sh))], fill=GRANITE, outline=INK)
d.polygon([(c1 - s1 * M * s3 / 2, mz(z + sh)), (c1 + s1 * M * s3 / 2, mz(z + sh)), (c1, mz(z + sh + Tt['pyramid']))], fill=GRANITE, outline=INK)
dim_v(c1 + 60, mz(0), mz(z + sh + Tt['pyramid']), '%.1f m' % ((z + sh + Tt['pyramid']) * M))
d.text((c1 - 50, mz(0) + 10), '狄奧多西方尖碑', fill=INK, font=F14)
Sp = MO['serpent']; c2 = bx0 + 260
stack(c2, [(Sp['base'][0], Sp['base'][1], MARBLE)])
for k in range(3):
    pts = [(c2 + (Sp['coil_r'] * M * s3) * math.cos(2 * math.pi * Sp['turns'] * t / 40 + 2 * math.pi * k / 3), mz(Sp['base'][1] + Sp['h'] * t / 40)) for t in range(41)]
    d.line(pts, fill=BRONZE, width=5)
dim_v(c2 + 40, mz(0), mz(Sp['base'][1] + Sp['h']), '%.1f m' % ((Sp['base'][1] + Sp['h']) * M))
d.text((c2 - 20, mz(0) + 10), '蛇柱', fill=INK, font=F14)
Wd = MO['walled']; c3 = bx0 + 480
z = stack(c3, [(w_, h_, STONE) for w_, h_ in Wd['steps']] + [(Wd['base'][0], Wd['base'][1], STONE)])
s0, s1, sh = Wd['shaft']
d.polygon([(c3 - s0 * M * s3 / 2, mz(z)), (c3 + s0 * M * s3 / 2, mz(z)), (c3 + s1 * M * s3 / 2, mz(z + sh)), (c3 - s1 * M * s3 / 2, mz(z + sh))], fill=STONE, outline=INK)
d.polygon([(c3 - s1 * M * s3 / 2, mz(z + sh)), (c3 + s1 * M * s3 / 2, mz(z + sh)), (c3, mz(z + sh + Wd['pyramid']))], fill=STONE, outline=INK)
dim_v(c3 + 70, mz(0), mz(z + sh + Wd['pyramid']), '%.1f m' % ((z + sh + Wd['pyramid']) * M))
d.text((c3 - 40, mz(0) + 10), '砌石方尖碑', fill=INK, font=F14)
Sc = SP; c4 = bx0 + 720
zb = Sc['base']['h']; zc = zb + Sc['col_h']; zt = zc + Sc['capital']['h']
stack(c4, [(Sc['base']['w'], zb, STONE)])
d.rectangle([c4 - Sc['col_d'] * M * s3 / 2, mz(zc), c4 + Sc['col_d'] * M * s3 / 2, mz(zb)], fill=MARBLE, outline=INK)
d.rectangle([c4 - Sc['capital']['w'] * M * s3 / 2, mz(zt), c4 + Sc['capital']['w'] * M * s3 / 2, mz(zc)], fill=MARBLE, outline=INK)
d.rectangle([c4 - 50, mz(zt + Sc['beam']['h']), c4 + 50, mz(zt)], fill=MARBLE, outline=INK)
d.rectangle([c4 + 44, mz(zt + Sc['beam']['h'] + Sc['parapet']['h']), c4 + 50, mz(zt + Sc['beam']['h'])], fill=MARBLE, outline=INK)
dim_v(c4 + 70, mz(0), mz(zt + Sc['beam']['h']), '%.1f m' % ((zt + Sc['beam']['h']) * M))
d.text((c4 - 60, mz(0) + 10), '半圓端柱廊（一跨）', fill=INK, font=F14)

# ── 圖框 ──
d.rectangle([20, 20, W - 20, H - 20], outline=INK, width=3)
d.text((60, 30), P['title'] + '　圖紙 v1（kaguya，照 plan.json 的參數畫）', fill=INK, font=F26)
ty = 1560
d.text((60, ty), '出處（參考資料）', fill=INK, font=F18)
for i, (k, v) in enumerate(P['provenance']['參考資料'].items()):
    d.text((60, ty + 28 + i * 18), '・%s —— %s' % (k, v), fill=INK, font=F12)
d.text((1500, ty), '設計決定（資料沒有）', fill=INK, font=F18)
for i, (k, v) in enumerate(P['provenance']['設計決定'].items()):
    d.text((1500, ty + 28 + i * 18), '・%s（%s）' % (k, v), fill=INK, font=F12)
d.line([(W - 420, H - 60), (W - 420 + 100 * 5, H - 60)], fill=INK, width=3); d.text((W - 420, H - 54), '平面比例尺 100 m', fill=INK, font=F12)
os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
im.save(os.path.join(D, 'sheets', 'blueprint.png'))
print('blueprint', im.size)
