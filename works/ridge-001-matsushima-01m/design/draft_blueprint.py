# 松島號 新圖紙（藍圖風格）—— 從產生程式的輸出（gen_matsushima 的 own.npy＋gen_parts 的零件＋place_guns 的擺法＋check_arcs 的射界）畫：
#   一、外形側視（右舷）　二、中線縱剖　三、上層平面與主砲射界　四、中甲板平面（12 cm 砲列）　五、橫剖面　六、主砲詳圖　＋尺寸線、圖說。
# 用法：python -I -X utf8 -B draft_blueprint.py <gen 輸出> <parts 輸出> <out.png>
# 寫法照定遠號的 draft_blueprint.py（trailhead）。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

out, pout, png = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P, PP = PLAN['params'], PLAN['parts']
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
M = json.load(open(os.path.join(out, 'matsushima_meta.json'), encoding='utf-8'))
ARC = json.load(open(os.path.join(out, 'arcs.json'), encoding='utf-8'))['turret-main']
GUNS = json.load(open(os.path.join(out, 'guns.json'), encoding='utf-8'))
PM = json.load(open(os.path.join(pout, 'parts_meta.json'), encoding='utf-8'))
NX, NY, NZ = own.shape; YC = (NY - 1) // 2; ZW = P['z_waterline']
BG = (20, 50, 102); LINE = (236, 243, 255); FAINT = (120, 152, 205); ACC = (255, 214, 120); RED = (255, 128, 118); WATER = (110, 190, 255); GREEN = (140, 230, 160)
FONT_CJK = 'C:/Windows/Fonts/kaiu.ttf'


def font(sz):
    try: return ImageFont.truetype(FONT_CJK, sz)
    except Exception: return ImageFont.load_default()


lab = own.astype(np.int16)
for nm in ('boilers', 'engine', 'shaft'):                                   # 鏡像部件的左舷那一份也畫
    i = names.index(nm) + 1
    m = (own == i)[:, ::-1, :] & (lab == 0)
    lab[m] = i
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


TM = P['turret_main']; CX = PM['turret-main-shell']['geom']['CX']; bx = P['barbette']['x']
shell = load_list(os.path.join(pout, 'turret-main-shell.txt'))
stamp(shell, [bx + 0.5, YC + 0.5, TM['z_table']], [CX + 0.5, CX + 0.5, 0], 90, 1, 'turret')
g320 = load_list(os.path.join(pout, 'gun320.txt')); tr = PM['gun320']['anchors']['trunnion']
stamp(g320, [bx + 0.5 - TM['gun_u'], YC + 0.5, TM['z_table'] + 1], [tr[0] + 0.5, tr[1] + 0.5, 0], 90, 0.5, 'gun')
SRC = {'gun120': ('gun120.txt', 0.5, 'gun'), 'gun57': ('gun57.txt', 0.2, 'gun'), 'gun47': ('gun47.txt', 0.2, 'gun'), 'h37': ('gun37.txt', 0.2, 'gun'),
       'basecamp-ember-01m-boat': ('basecamp-ember-01m-boat.txt', 0.5, 'boat'), 'basecamp-frigate-constitution-01m-whaleboat': ('basecamp-frigate-constitution-01m-whaleboat.txt', 0.5, 'boat'),
       'basecamp-frigate-constitution-01m-anchor': ('basecamp-frigate-constitution-01m-anchor.txt', 0.6, 'boat')}
CL = {}
for nm, g in GUNS.items():
    if not g.get('at'): continue
    fn, sc, kind = SRC[g['src']]
    if fn not in CL: CL[fn] = load_list(os.path.join(pout, fn))
    if 'pivot' in g: pv = g['pivot']
    elif g['src'] == 'h37': pv = [18.5, 40.5, 0]
    else:
        a = PM[g['src']]['anchors']['pivot']; pv = [a[0] + 0.5, a[1] + 0.5, 0]
    stamp(CL[fn], g['at'], pv, g['rz'], sc, kind)
KIND = {}
for i, nm in enumerate(names):
    k = i + 1
    if nm in ('barbette', 'conning', 'deck-lower'): KIND[k] = 'armor'
    elif nm.startswith(('boilers', 'engine', 'shaft', 'screw', 'funnel', 'floor')): KIND[k] = 'mach'
    elif nm.startswith('mag-'): KIND[k] = 'mag'
    elif nm.startswith('deck'): KIND[k] = 'deck'
    else: KIND[k] = 'other'
for j, nm in enumerate(extra): KIND[len(names) + 1 + j] = {'turret': 'armor', 'gun': 'gun', 'boat': 'other'}[nm]
FILL = {'armor': (150, 70, 80), 'mach': (70, 100, 140), 'mag': (150, 120, 40), 'deck': (40, 78, 140), 'gun': (200, 200, 220), 'other': None}
K = 2
img = Image.new('RGB', (NX * K + 480, 5600), BG); dr = ImageDraw.Draw(img)


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


def zline(oy, z, color, txt, w, nz=NZ):
    yy = oy + (nz - 1 - z) * K + K // 2
    dr.line([ox - 20, yy, ox + w + 20, yy], fill=color, width=1)
    dr.text((ox + w + 26, yy - 12), txt, fill=color, font=font(18))


ox = 90
# ── 一、外形側視 ──
y0 = 120
title(ox, 20, '一、外形側視（右舷）', 'Outboard profile — starboard；z 0 ＝ 龍骨底；比例 0.1 m／格（1 格 ＝ 2 px）；砲、小艇、錨照擺法畫進來')
w, h = blit(first_hit(1, True), ox, y0)
zline(y0, ZW, WATER, 'DWL 6.1 m', w)
xs_all = np.nonzero((own > 0).any((1, 2)))[0]
dim(ox + xs_all.min() * K, y0 + h + 22, ox + (xs_all.max() + 1) * K, y0 + h + 22, '全長 %.1f m（衝角尖到船尾）' % ((xs_all.max() - xs_all.min() + 1) * 0.1), off=64)
wl = np.nonzero(own[:, :, ZW].any(1))[0]
dim(ox + wl.min() * K, y0 + h + 70, ox + (wl.max() + 1) * K, y0 + h + 70, '水線長 %.1f m' % ((wl.max() - wl.min() + 1) * 0.1), off=64)
dim(ox + w + 150, y0 + (NZ - ZW) * K, ox + w + 150, y0 + NZ * K, '吃水 %.1f m' % (ZW * 0.1))
for nm_, z_, c_ in (('船首樓 %.1f m' % ((P['z_fc_deck'] + 1 - ZW) * 0.1), P['z_fc_deck'] + 1, FAINT), ('後甲板 %.1f m' % ((P['z_upper_deck'] + 1 - ZW) * 0.1), P['z_upper_deck'] + 1, FAINT),
                    ('煙囪頂 %.1f m' % ((P['funnel']['top'] - ZW) * 0.1), P['funnel']['top'], FAINT), ('下桅樓 %.1f m' % ((P['mast']['top1'] - ZW) * 0.1), P['mast']['top1'], FAINT),
                    ('桅頂 %.1f m' % ((P['mast']['pole_top'] - ZW) * 0.1), P['mast']['pole_top'], FAINT)):
    zline(y0, z_, c_, nm_, w)
# ── 二、中線縱剖 ──
y1 = y0 + h + 170
title(ox, y1 - 60, '二、中線縱剖', 'Inboard profile on centreline —— 防護甲板、中甲板、上甲板、船首樓甲板、機艙、鍋爐、彈藥庫、露砲台、梯子')
sec = lab[:, YC, :].copy()
mir = np.zeros_like(sec)
for nm in ('boilers', 'engine'):                                           # 中線剖不到右舷的機器 ⇒ 疊上右舷那一份（看得出位置）
    i = names.index(nm) + 1
    hit = (own == i).any(1)
    mir[hit & (sec == 0)] = i
sec = np.where(sec > 0, sec, mir)
w, h = blit(sec, ox, y1)
zline(y1, ZW, WATER, 'DWL', w)
for nm, xx, zz in [('機艙', 490, 40), ('鍋爐 ×6', 610, 40), ('前彈藥庫', 790, 28), ('後彈藥庫', 290, 28), ('防護甲板', 150, 62), ('中甲板', 150, 88), ('後甲板', 150, 112), ('船首樓', 800, 140), ('露砲台', 285, 128)]:
    dr.text((ox + xx * K, y1 + (NZ - 1 - zz) * K - 22), nm, fill=ACC, font=font(18))
# ── 三、上層平面與主砲射界 ──
y2 = y1 + h + 140
title(ox, y2 - 60, '三、上層平面與主砲射界', 'Plan from above —— 船頭朝右、右舷在下；扇形 ＝ 開火範圍（綠）、轉動範圍（虛線）；check_arcs.py 量的')
top = first_hit(2, True)
w, h = blit(top[:, ::-1], ox, y2)


def to_plan(x, y): return ox + (x + 0.5) * K, y2 + (y + 0.5) * K


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


wedge(bx, YC, 180, ARC['arc'][0], ARC['arc'][1], 130, FAINT, dash=True)
wedge(bx, YC, 180, ARC['fire'][0], ARC['fire'][1], 170, GREEN)
tx, ty_ = to_plan(bx, YC)
dr.text((tx - 380, ty_ + 70), '32 cm Canet　轉動 %d～%d°　開火 %d～%d°（史料 ±140°）' % (ARC['arc'][0], ARC['arc'][1], ARC['fire'][0], ARC['fire'][1]), fill=ACC, font=font(18))
dim(ox + w + 40, y2 + (YC - 78) * K, ox + w + 40, y2 + (YC + 79) * K, '寬 15.6 m')
# ── 四、中甲板平面 ──
y3 = y2 + h + 170
title(ox, y3 - 60, '四、中甲板平面（z ＝ 中甲板走路格往上 10 格的切面）', 'Middle deck plan —— 12 cm 砲列每舷 5 門（前半段）、煙囪、桅、露砲台圈、梯子')
zc = P['z_middle_deck'] + 11
w, h = blit(lab[:, ::-1, zc], ox, y3)
for L in M['anchors']['ladders']:
    x_, y_ = L['head'][0], L['head'][1]
    dr.ellipse([ox + x_ * K - 5, y3 + (NY - 1 - y_) * K - 5, ox + x_ * K + 5, y3 + (NY - 1 - y_) * K + 5], outline=ACC, width=2)
dr.text((ox, y3 + h + 8), '○ ＝ 梯頭（kind=ladders，foot／lo／hi／head 四點；這張平面只畫位置，不分層）', fill=FAINT, font=font(18))
# ── 五、橫剖面 ──
y4 = y3 + h + 120
title(ox, y4 - 60, '五、橫剖面（從船尾往船頭看；左 ＝ 左舷）', 'Sections —— 露砲台、機艙、鍋爐、砲列、艏追擊砲')
k2 = 2
xx0 = ox
for xs in (bx, 504, 638, 735, 880):
    L2 = lab[xs, :, :260]
    w2, h2 = blit(L2, xx0, y4, k=k2)
    yy = y4 + (260 - 1 - ZW) * k2
    dr.line([xx0 - 6, yy, xx0 + w2 + 6, yy], fill=WATER, width=1)
    dr.text((xx0, y4 + h2 + 6), 'x %d（離艦首 %.1f m）' % (xs, (P['x_stem'] - xs) * 0.1), fill=FAINT, font=font(18))
    xx0 += w2 + 26
# ── 六、主砲詳圖 ──
y5 = y4 + 260 * k2 + 110
title(ox, y5 - 60, '六、主砲詳圖（露砲台 300 mm＋轉盤與砲罩 100 mm＋32 cm Canet）', 'Main gun —— 平面（砲軸高度）／側剖（中線）；殼 0.1 m／格、砲 0.05 m／格（scale 0.5）')
R = 110
k3 = 3
sub = lab[bx - R:bx + 30, YC - 50:YC + 51, :]
wa, ha = blit(sub[:, ::-1, int(ARC['gun_axis_z'])], ox, y5, k=k3)
wb, hb = blit(lab[bx - R:bx + 30, YC, 50:170], ox + wa + 60, y5, k=k3)
dr.text((ox, y5 + max(ha, hb) + 10), '露砲台外徑 %.1f m、砲軸水線上 %.1f m、砲管全長 12.8 m、砲口離轉軸 %.1f m；砲罩掃過半徑 %.1f m，掃過的圓裡別的格 %d' %
        (2 * P['barbette']['r'][1] * 0.1, (ARC['gun_axis_z'] - ZW) * 0.1, 9.75, ARC['hood_r'] * 0.1, ARC['hood_cells']), fill=ACC, font=font(20))
# ── 圖說 ──
yb = y5 + max(ha, hb) + 70
notes = [
    '主尺寸：全長 %.1f m、水線長 %.1f m、寬 15.6 m、吃水 6.1 m；排水量（設計水線以下外形）%.0f t —— 史料 4,217 長噸（Conway\'s）／4,278 長噸（1894 年 6 月）。' % ((xs_all.max() - xs_all.min() + 1) * 0.1, (wl.max() - wl.min() + 1) * 0.1, M['disp_t']),
    '船形：內傾船殼、水線衝角、懸出的圓 counter；長船首樓（艦首到離艦首 60 m），後甲板低一層、只放主砲露砲台（三景艦裡只有松島是這樣）。',
    '主砲：1 × 32 cm／38 Canet，在艦尾、朝後；露砲台 300 mm、砲罩 100 mm；左右各 140°（史料）—— 量出來轉 ±%d°、開火 ±%d°。' % (ARC['arc'][1], ARC['fire'][1]),
    '副砲：12 × 12 cm Armstrong 速射砲 —— 中甲板每舷 5 門（前半段的窄高砲門）＋艦首上甲板每舷 1 門（往前偏 %d°）。' % GUNS['艏砲-S']['phi'],
    '輕砲：6 × 57 mm 哈乞開斯（船首樓側面突出砲台 4、船首樓後端 2）、6 × 47 mm（兩層桅樓各 2、後甲板船尾 2）、2 × 37 mm 轉膛砲（艦橋兩翼）—— 位置是設計決定。',
    '機器：6 座圓筒鍋爐（兩舷各三、爐門朝中線）、一支煙囪；兩具臥式三缸三段膨脹主機、雙軸內旋、兩個 3.2 m 四葉螺旋槳；5,400 ihp、設計 16.5 kn。',
    '塗裝：白殼、白上層、黑煙囪、白桅、水線一條黑、水線下紅丹（1893 嚴島照片、1895–96 松島照片、1895 黃海海戰畫；1894 年 9 月的顏色沒有文字史料 —— 設計決定）。旗：旭日旗。',
    '史料：泉江三《日本の戦艦》（經 ja Wikipedia）、EN／ja Wikipedia、navypedia、Jane\'s 1906、Brassey 1900（姊妹艦）、照片 1895／1896（三笠保存會）；每個數字的出處在 plan.json provenance。',
]
dr.rectangle([ox - 12, yb - 12, ox + NX * K + 330, yb + 54 + 30 * len(notes)], outline=LINE, width=2)
dr.text((ox, yb), '松島 MATSUSHIMA（1892，聯合艦隊旗艦，1894 黃海海戰）—— 遊戲用造船圖紙　繪：ridge-001　比例 0.1 m／格（砲 0.05 m、哈乞開斯 0.02 m）', fill=LINE, font=font(26))
for i, s in enumerate(notes): dr.text((ox, yb + 44 + 30 * i), s, fill=FAINT, font=font(20))
img = img.crop((0, 0, img.width, yb + 70 + 30 * len(notes)))
img.save(png)
print('ok', img.size)
