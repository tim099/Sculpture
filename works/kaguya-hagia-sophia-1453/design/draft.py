# 聖索菲亞 1453 的圖紙（TASK-0748）：照 plan.json 的參數畫線（⛔ 不從格子拍），標尺寸。python -I -X utf8 -B draft.py <design 資料夾>
#   ⇒ sheets/blueprint.png：平面（地面層＋屋頂輪廓）、縱剖面（西 → 東，沿軸）、橫剖面（北 → 南，過穹頂中心）、圖框（出處、比例尺、圖例）
import sys, os, json, math
from PIL import Image, ImageDraw, ImageFont

D = os.path.abspath(sys.argv[1])
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
FONT = None
for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/mingliu.ttc'):
    if os.path.exists(f): FONT = f; break
def font(sz): return ImageFont.truetype(FONT, sz) if FONT else ImageFont.load_default()
F12, F14, F18, F26 = font(12), font(14), font(18), font(26)
INK, RED, BLUE, GREY, PAPER = (34, 46, 74), (176, 40, 40), (40, 80, 160), (150, 150, 150), (244, 240, 228)
BRICK, LEAD, MARBLE, ANNEX = (196, 120, 92), (150, 156, 176), (232, 228, 214), (214, 190, 160)
W, H = 3000, 1900
im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
S = 7.0                                                      # 每公尺幾像素（三張同一個比例）


def R(x0, x1, y0, y1, **k): d.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], **k)


def dim_h(x0, x1, y, label, col=RED):
    d.line([(x0, y), (x1, y)], fill=col, width=1)
    for x in (x0, x1): d.line([(x, y - 4), (x, y + 4)], fill=col, width=1)
    d.text(((x0 + x1) / 2 - d.textlength(label, font=F12) / 2, y + 3), label, fill=col, font=F12)


def dim_v(x, y0, y1, label, col=RED):
    d.line([(x, y0), (x, y1)], fill=col, width=1)
    for y in (y0, y1): d.line([(x - 4, y), (x + 4, y)], fill=col, width=1)
    d.text((x + 6, (y0 + y1) / 2 - 7), label, fill=col, font=F12)


def arc_pts(cx, cy, r, a0, a1, n=48, sx=1.0):
    return [(cx + sx * r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy - r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


M, Db, Dm, Sd, Ex, Bm, Ap, Wv = P['main'], P['dome_base'], P['dome'], P['semidomes'], P['exedrae'], P['bema'], P['apse'], P['west_vault']
N, O, Bf, F, A, Pi = P['inner_narthex'], P['outer_narthex'], P['belfry'], P['flyers'], P['atrium'], P['piers']

# ═════ 平面（上 ＝ 北，往右 ＝ 東 ＝ +X）═════
ox, oy = 60 + 100 * S, 120 + 63 * S                          # 研究座標 (0, 0) 在圖上哪裡
def px(x): return ox + x * S
def py(y): return oy - y * S
d.text((60, 70), '平面（地面層輪廓＋屋頂；上 ＝ 北、右 ＝ 東 ＝ 後殿，軸向方位 123°）', fill=INK, font=F18)
R(px(A['x'][0]), px(A['x'][1]), py(A['y'][0]), py(A['y'][1]), outline=INK, fill=(236, 230, 214))
for (x0, x1, y0, y1) in ((A['x'][0], A['x'][0] + A['walk_d'], A['y'][0], A['y'][1]), (A['x'][0], A['x'][1], A['y'][1] - A['walk_d'], A['y'][1]), (A['x'][0], A['x'][1], A['y'][0], A['y'][0] + A['walk_d'])):
    R(px(x0), px(x1), py(y0), py(y1), outline=INK, fill=ANNEX)
fc = ((A['x'][0] + A['x'][1]) / 2, (A['y'][0] + A['y'][1]) / 2)
d.regular_polygon((px(fc[0]), py(fc[1]), A['fountain_r'] * S), 8, outline=INK, fill=MARBLE)
for b in P['buttresses']: R(px(b['x'][0]), px(b['x'][1]), py(b['y'][0]), py(b['y'][1]), outline=INK, fill=BRICK)
Q = P['patriarchate']; R(px(Q['x'][0]), px(Q['x'][1]), py(Q['y'][0]), py(Q['y'][1]), outline=INK, fill=ANNEX)
R(px(M['x'][0]), px(M['x'][1]), py(M['y'][0]), py(M['y'][1]), outline=INK, fill=LEAD)
for sx in (-1, 1):
    for sy in (-1, 1): R(px(sx * Pi['x'][0]), px(sx * Pi['x'][1]), py(sy * Pi['y'][0]), py(sy * Pi['y'][1]), outline=INK, fill=BRICK)
R(px(N['x'][0]), px(N['x'][1]), py(N['y'][0]), py(N['y'][1]), outline=INK, fill=LEAD)
R(px(O['x'][0]), px(O['x'][1]), py(O['y'][0]), py(O['y'][1]), outline=INK, fill=LEAD)
for yc in F['y']: R(px(F['pier_x'][0]), px(F['end_x']), py(yc - F['w'] / 2), py(yc + F['w'] / 2), outline=INK, fill=BRICK)
R(px(Bf['x'][0]), px(Bf['x'][1]), py(Bf['y'][0]), py(Bf['y'][1]), outline=INK, fill=BRICK)
R(px(Db['x'][0]), px(Db['x'][1]), py(Db['y'][0]), py(Db['y'][1]), outline=INK, fill=BRICK)
for s in (-1, 1):
    d.chord([px(s * Sd['cx']) - Sd['r_out'] * S, py(0) - Sd['r_out'] * S, px(s * Sd['cx']) + Sd['r_out'] * S, py(0) + Sd['r_out'] * S], -90 if s > 0 else 90, 90 if s > 0 else 270, outline=INK, fill=LEAD)
    for sy in (-1, 1):
        cx, cy = s * Ex['cx'], sy * Ex['cy']; a = math.degrees(math.atan2(sy, s))
        d.pieslice([px(cx) - Ex['r_out'] * S, py(cy) - Ex['r_out'] * S, px(cx) + Ex['r_out'] * S, py(cy) + Ex['r_out'] * S], -a - 90, -a + 90, outline=INK, fill=LEAD)
R(px(Bm['x'][0]), px(Bm['x'][1]), py(-Bm['half_w']), py(Bm['half_w']), outline=INK, fill=LEAD)
d.polygon([(px(Ap['x0']), py(Ap['half_w0'])), (px(Ap['x0'] + 1), py(Ap['half_w0'])), (px(Ap['x1']), py(Ap['half_w1'])), (px(Ap['x1']), py(-Ap['half_w1'])), (px(Ap['x0'] + 1), py(-Ap['half_w0'])), (px(Ap['x0']), py(-Ap['half_w0']))], outline=INK, fill=BRICK)
r = Dm['r_out'] - 0.2
d.ellipse([px(-r * Dm['x_scale']), py(r), px(r * Dm['x_scale']), py(-r)], outline=INK, fill=LEAD)
for k in range(Dm['n_win']):
    a = math.radians(k * 360 / Dm['n_win']); d.line([(px(r * Dm['x_scale'] * math.cos(a)), py(r * math.sin(a))), (px((r + 2.3) * Dm['x_scale'] * math.cos(a)), py((r + 2.3) * math.sin(a)))], fill=BRICK, width=3)
K, Bp = P['skeuophylakion'], P['baptistery']
d.ellipse([px(K['c'][0] - K['r']), py(K['c'][1] + K['r']), px(K['c'][0] + K['r']), py(K['c'][1] - K['r'])], outline=INK, fill=ANNEX)
d.regular_polygon((px(Bp['c'][0]), py(Bp['c'][1]), Bp['r'] * S), 8, rotation=22.5, outline=INK, fill=ANNEX)
for t, x, y in (('中庭', fc[0] - 3, fc[1] + 8), ('外前廊', -56.5, 37.5), ('內前廊', -48.5, 39), ('鐘樓', -60, 8.5), ('聖器室', 26, 59), ('洗禮堂', -32, -63), ('宗主教府', -50, -49), ('後殿', 40, 9), ('扶壁墩', 10.5, 41)):
    d.text((px(x), py(y)), t, fill=INK, font=F12)
dim_h(px(M['x'][0]), px(M['x'][1]), py(M['y'][0]) + 40, '主體 %.0f m（外）' % (M['x'][1] - M['x'][0]))
dim_h(px(A['x'][0]), px(Ap['x1']), py(-63) + 20, '總長 %.1f m（中庭西牆 → 後殿）' % (Ap['x1'] - A['x'][0]))
dim_v(px(M['x'][1]) + 70, py(M['y'][1]), py(M['y'][0]), '%.0f m' % (M['y'][1] - M['y'][0]))
dim_h(px(-Dm['r_out'] + 0.75), px(Dm['r_out'] - 0.75), py(0) + 4, '穹頂淨徑約 31.9 × 30.9 m', col=BLUE)
d.line([(px(-108 + 8), py(66)), (px(-108 + 8), py(56))], fill=INK, width=2); d.polygon([(px(-100), py(67.5)), (px(-101.2), py(64.5)), (px(-98.8), py(64.5))], fill=INK)
d.text((px(-100) - 6, py(70)), '北', fill=INK, font=F14)

# ═════ 縱剖面（沿軸，西 → 東；看向北邊那一半）═════
gx, gz = 60 + 100 * S, 1820
def sx_(x): return gx + x * S
def sz_(z): return gz - z * S
d.text((60, 1390), '縱剖面（沿軸、西 → 東）', fill=INK, font=F18)
d.line([(sx_(-102), sz_(0)), (sx_(47), sz_(0))], fill=INK, width=2)
R(sx_(A['x'][0]), sx_(A['x'][0] + A['wall_t']), sz_(0), sz_(A['z']), fill=ANNEX, outline=INK)
d.polygon([(sx_(A['x'][0]), sz_(A['z'])), (sx_(A['x'][0] + A['walk_d']), sz_(A['walk_z_in'])), (sx_(A['x'][0] + A['walk_d']), sz_(A['walk_z_in'] - 0.8)), (sx_(A['x'][0]), sz_(A['z'] - 0.8))], fill=LEAD, outline=INK)
R(sx_(Bf['x'][0]), sx_(Bf['x'][1]), sz_(0), sz_(Bf['z']), fill=BRICK, outline=INK)
d.polygon([(sx_(Bf['x'][0]), sz_(Bf['z'])), (sx_((Bf['x'][0] + Bf['x'][1]) / 2), sz_(Bf['z'] + Bf['roof_h'])), (sx_(Bf['x'][1]), sz_(Bf['z']))], fill=LEAD, outline=INK)
R(sx_(N['x'][0]), sx_(N['x'][1]), sz_(0), sz_(N['z']), fill=BRICK, outline=INK)
R(sx_(M['x'][0]), sx_(M['x'][1]), sz_(0), sz_(M['z']), fill=BRICK, outline=INK)
R(sx_(Db['x'][0]), sx_(Db['x'][1]), sz_(M['z']), sz_(Db['z']), fill=BRICK, outline=INK)
for s in (-1, 1):
    pts = arc_pts(sx_(s * Sd['cx']), sz_(Sd['zc']), Sd['r_out'] * S, 0 if s > 0 else 180, 90, sx=1)
    d.polygon([(sx_(s * Sd['cx']), sz_(Sd['zc']))] + pts, fill=LEAD, outline=INK)
d.polygon([(sx_(Wv['x'][0]), sz_(Wv['zc'])), (sx_(Wv['x'][1]), sz_(Wv['zc'])), (sx_(Wv['x'][1]), sz_(Wv['zc'] + Wv['r_out'])), (sx_(Wv['x'][0]), sz_(Wv['zc'] + Wv['r_out']))], fill=LEAD, outline=INK)
R(sx_(Bm['x'][0]), sx_(Bm['x'][1]), sz_(Bm['zc']), sz_(Bm['zc'] + Bm['r_out']), fill=LEAD, outline=INK)
R(sx_(Ap['x0']), sx_(Ap['x1']), sz_(0), sz_(Ap['z']), fill=BRICK, outline=INK)
d.polygon([(sx_(Ap['x0']), sz_(Ap['z']))] + arc_pts(sx_(Ap['x0']), sz_(Ap['z']), Ap['conch_r'] * S, 0, 90), fill=LEAD, outline=INK)
zc, Ro, xs = Dm['zc'], Dm['r_out'], Dm['x_scale']
a0 = math.degrees(math.asin((Dm['z0'] - zc) / Ro))
pts = [(sx_(Ro * xs * math.cos(math.radians(a))), sz_(zc + Ro * math.sin(math.radians(a)))) for a in [a0 + (180 - 2 * a0) * i / 64 for i in range(65)]]
d.polygon(pts, fill=LEAD, outline=INK)
ri = 16.65; pts_i = [(sx_(ri * xs * math.cos(math.radians(a))), sz_(zc + ri * math.sin(math.radians(a)))) for a in [8 + 164 * i / 64 for i in range(65)]]
d.line(pts_i, fill=BLUE, width=1)
for z, t in ((Db['z'], '簷口 41.5'), (zc + Ro, '穹頂頂 56.8（史料 56.0）'), (M['z'], '外牆 22'), (13.4, '樓廊 13.4')):
    d.line([(sx_(46), sz_(z)), (sx_(52), sz_(z))], fill=GREY); d.text((sx_(53), sz_(z) - 7), t, fill=GREY, font=F12)
d.text((sx_(-12), sz_(zc) - 6), 'R 16.65（肋內緣）', fill=BLUE, font=F12)
dim_v(sx_(-104), sz_(0), sz_(zc + Ro), '%.1f m' % (zc + Ro))

# ═════ 橫剖面（過穹頂中心，北 → 南）═════
tx, tz = 1650 + 64 * S, 1820
def ty_(y): return tx - y * S
def tz_(z): return tz - z * S
d.text((1650, 1390), '橫剖面（過穹頂中心，左 ＝ 北）', fill=INK, font=F18)
d.line([(ty_(64), tz_(0)), (ty_(-64), tz_(0))], fill=INK, width=2)
for b in P['buttresses']:
    if b['id'] in ('mid-north', 'mid-south'):
        R(ty_(b['y'][0]), ty_(b['y'][1]), tz_(0), tz_(b['z_out']), fill=BRICK, outline=INK)
        d.polygon([(ty_(b['y'][0] if b['y'][0] > 0 else b['y'][1]), tz_(b['z_in'])), (ty_(b['y'][1] if b['y'][0] > 0 else b['y'][0]), tz_(b['z_out'])), (ty_(b['y'][0] if b['y'][0] > 0 else b['y'][1]), tz_(b['z_out']))], fill=BRICK, outline=INK)
R(ty_(M['y'][0]), ty_(M['y'][1]), tz_(0), tz_(M['z']), fill=BRICK, outline=INK)
for sy in (-1, 1): R(ty_(sy * Pi['y'][0]), ty_(sy * Pi['y'][1]), tz_(0), tz_(Pi['z']), fill=BRICK, outline=INK)
R(ty_(Db['y'][0]), ty_(Db['y'][1]), tz_(M['z']), tz_(Db['z']), fill=BRICK, outline=INK)
Ar = Db['arch']
d.polygon([(ty_(-Ar['r_in']), tz_(Ar['zc']))] + arc_pts(ty_(0), tz_(Ar['zc']), Ar['r_in'] * S, 180, 0) + [(ty_(Ar['r_in']), tz_(Ar['zc']))], outline=BLUE)
for row in Db['tymp_rows']:
    for i in range(row['n']):
        yc = (i - (row['n'] - 1) / 2) * row['step']; R(ty_(yc - 0.8), ty_(yc + 0.8), tz_(row['z'][0]), tz_(row['z'][1]), fill=(60, 60, 60))
pts = [(ty_(Ro * math.cos(math.radians(a))), tz_(zc + Ro * math.sin(math.radians(a)))) for a in [a0 + (180 - 2 * a0) * i / 64 for i in range(65)]]
d.polygon(pts, fill=LEAD, outline=INK)
dim_h(ty_(Pi['y'][1]), ty_(-Pi['y'][1]), tz_(0) + 12, '扶壁墩外緣 %.0f m' % (2 * Pi['y'][1]))
dim_h(ty_(Ar['r_in']), ty_(-Ar['r_in']), tz_(Ar['zc']) - 4, '大拱淨跨 %.0f m' % (2 * Ar['r_in']), col=BLUE)
dim_v(ty_(-Pi['y'][1]) + 20, tz_(0), tz_(Pi['z']), '扶壁墩 %.0f m' % Pi['z'])
d.text((ty_(14), tz_(31)), '南北山牆：7 ＋ 5 窗（推定）', fill=INK, font=F12)

# ═════ 圖框 ═════
fx0 = 1650
R(fx0, W - 40, 60, 1330, outline=INK)
d.text((fx0 + 20, 80), '聖索菲亞大教堂 1453（Hagia Sophia，圍城之前）', fill=INK, font=F26)
d.text((fx0 + 20, 125), 'kaguya 繪製，2026-10-20；比例 1 m ＝ %.0f px；雕刻 0.4 m／格（框 122 × 145 × 60.8 m）' % S, fill=INK, font=F14)
src = ['參考資料（每一項的出處在 plan.json provenance）：',
       '・Lethaby & Swainson, The Church of Sancta Sophia, 1894（照 Salzenberg 1854 的尺寸，普魯士尺）',
       '・Duppel 2010（KIT；引 Mainstone 1988、Emerson／Van Nice、Sato／Hidaka）：穹頂 31.90 × 30.87 m、頂 56.0 m、40 肋 40 窗',
       '・Mark 等 1993；Kırlangıç 2008（有限元素模型的幾何）；Diker 等 2023',
       '・Dark & Kostenec, Hagia Sophia in Context 2019（經 ByzRev 書評）；The Byzantine Legacy；istanbultarihi.ist',
       '・OpenStreetMap 3D 建物（位置、量體的對照；群眾外包、只拿來對照）',
       '',
       '1453 年的樣子：',
       '・沒有宣禮塔（征服之後才加）；鐘樓在西立面正中（Grelot 1680 畫的方塔、金字塔頂）',
       '・中庭只剩西、北、南三面迴廊（Broquière 1432）；東面那一廊成了外前廊',
       '・扶壁：查士丁尼的四座扶壁墩、中段南北扶壁、西側飛扶壁、1317 年的東扶壁',
       '・外牆是紅磚夾粉紅色厚灰縫、西立面牆腳有大理石貼面；屋頂鉛皮',
       '',
       '設計決定（資料沒有）：',
       '・鐘樓高 26 m ＋ 5 m 尖頂；附屬建築與扶壁的高度；窗的位置與數量（穹頂 40 窗除外）',
       '・中庭寬約 64 m（＝ 外前廊長）；頂上的十字',
       '・1346～54 年撐穹頂基座的四道飛拱：位置沒查到、沒做',
       '',
       '圖例：']
y = 160
for t in src:
    d.text((fx0 + 20, y), t, fill=INK, font=F14); y += 24
for c, t in ((BRICK, '磚'), (LEAD, '鉛皮屋頂'), (MARBLE, '大理石'), (ANNEX, '附屬建築、中庭'), (BLUE, '內緣、淨跨（藍線）')):
    R(fx0 + 30, fx0 + 60, y + 2, y + 18, fill=c, outline=INK); d.text((fx0 + 70, y), t, fill=INK, font=F14); y += 26
d.line([(fx0 + 30, 1290), (fx0 + 30 + 20 * S, 1290)], fill=INK, width=3); d.text((fx0 + 30, 1296), '0　　　　　20 m', fill=INK, font=F12)
im.save(os.path.join(D, 'sheets', 'blueprint.png'))
print('blueprint', W, H)
