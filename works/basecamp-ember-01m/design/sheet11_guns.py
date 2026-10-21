# 新圖紙 11：砲位表（TASK-0519 驗收第 1 格；2026-10-21 補）—— 只讀 guns_placement.json（place_guns.py 的結果），不重新擺砲
#   ⇒ sheet11_guns_v1.png：上半 側面（右舷，x 對 z）每一門砲的位置、型號色；下半 逐門表（砲門號、型號、at、退、砲口伸出船殼外）
#   P 舷是 S 舷的鏡像（at.y 和 ＝ 321）⇒ 表上一列 ＝ 一對；P 舷的數跟 S 舷不同就在那一列標出來（程式斷言：只有 phi 差正負號）
# 用法：python -I -X utf8 sheet11_guns.py
import os, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))
PAPER, INK, GRID = (250, 248, 240), (20, 20, 20), (200, 196, 186)
TYPE_COL = {'long32': (150, 20, 20), 'gun24': (30, 70, 150), 'carr32': (200, 130, 0), 'long18': (20, 120, 60)}
TYPE_NAME = {'long32': '32 磅長砲（新做 -gun-long32，scale 0.5）', 'gun24': '24 磅長砲（憲法號 -gun-24，scale 1）',
             'carr32': '32 磅 carronade（憲法號，scale 0.5）', 'long18': '18 磅追擊砲（憲法號 -gun-long18，scale 0.5）'}
DECK_NAME = {'lower': '下層砲甲板', 'upper': '上層砲甲板', 'spar': '上甲板'}


def font(n):
    for f in ('msjh.ttc', 'msyh.ttc', 'arial.ttf'):
        try:
            return ImageFont.truetype(f, n)
        except OSError:
            pass
    return ImageFont.load_default()


rows = G['rows']
S = {r['name']: r for r in rows if r['side'] == 'S'}
pairs = []
for r in rows:
    if r['side'] != 'P':
        continue
    s = S[r['name'].replace('P', 'S', 1) if r['name'].startswith('砲') else r['name'][:-1] + 'S']
    assert abs(r['at'][1] + s['at'][1] - 321) < 1e-6, r['name']
    assert r['at'][0] == s['at'][0] and r['at'][2] == s['at'][2] and r['back'] == s['back'] and r['muzzle_beyond_outer'] == s['muzzle_beyond_outer'], r['name']
    assert r['phi'] == -s['phi'], r['name']
    pairs.append(s)
assert len(pairs) * 2 == len(rows) == 90

W, H = 2000, 2350
im = Image.new('RGB', (W, H), PAPER)
d = ImageDraw.Draw(im)
F, Fs, Fb = font(22), font(18), font(34)
d.text((40, 30), '餘燼號 新圖紙 11：砲位表 v1（90 門 ＝ 45 對；P 舷 ＝ S 舷鏡像）', fill=INK, font=Fb)
d.text((40, 80), '來源 design/guns_placement.json（place_guns.py 2026-10-13 的結果）；at ＝ 模型 pivot 落點（組裝件座標、格）；退 ＝ 從舷牆外面往裡退的格數；'
       '伸出 ＝ 砲口超出船殼外表面（負 ＝ 縮在砲門裡）', fill=INK, font=Fs)

# 側面：x 100..720、z 70..150，右舷
X0, X1, Z0, Z1 = 100, 720, 70, 150
L, T, R, B = 80, 140, W - 60, 620
sx = (R - L) / (X1 - X0)
sz = (B - T) / (Z1 - Z0)
px = lambda x: L + (x - X0) * sx
pz = lambda z: B - (z - Z0) * sz
for x in range(X0, X1 + 1, 50):
    d.line([(px(x), T), (px(x), B)], fill=GRID)
    d.text((px(x) - 14, B + 6), str(x), fill=INK, font=Fs)
for z in range(Z0, Z1 + 1, 10):
    d.line([(L, pz(z)), (R, pz(z))], fill=GRID)
    d.text((L - 40, pz(z) - 10), str(z), fill=INK, font=Fs)
d.text((L, B + 30), 'x（船尾 ← → 船頭）', fill=INK, font=Fs)
d.text((L - 60, T - 30), 'z', fill=INK, font=Fs)
for s in pairs:
    x, z = s['at'][0], s['axis_z']
    c = TYPE_COL[s['type']]
    if s['chase']:
        d.polygon([(px(x), pz(z) - 12), (px(x) - 10, pz(z) + 8), (px(x) + 10, pz(z) + 8)], fill=c)
    else:
        d.ellipse([px(x) - 8, pz(z) - 8, px(x) + 8, pz(z) + 8], fill=c)
    if s['muzzle_beyond_outer'] < 0:
        d.ellipse([px(x) - 14, pz(z) - 14, px(x) + 14, pz(z) + 14], outline=(0, 0, 0), width=2)
yy = B + 70
for k, v in TYPE_NAME.items():
    d.ellipse([L, yy + 4, L + 16, yy + 20], fill=TYPE_COL[k])
    d.text((L + 26, yy), v, fill=INK, font=Fs)
    yy += 28
d.text((L + 900, B + 70), '● 舷側砲　▲ 追擊砲（船頭、船尾）　○ 外框 ＝ 砲口縮在砲門裡', fill=INK, font=Fs)
d.text((L + 900, B + 126), '（下層船頭、船尾追擊砲那兩對；carronade 齊平到縮 1 格 —— Tim 2026-10-19 接受）', fill=INK, font=Fs)
d.text((L + 900, B + 154), '高度畫的是砲軸 axis_z；船尾追擊砲的 x 在 transom 那一端', fill=INK, font=Fs)

# 表
cols = [('甲板', 150), ('名（S 舷）', 210), ('型號', 110), ('at x', 90), ('at y（S／P）', 160), ('at z', 70), ('軸 z', 80), ('φ（S）', 80), ('退', 70), ('伸出', 80)]
y0, bx = 830, 40
x = bx
for name, w in cols:
    d.text((x, y0), name, fill=INK, font=F)
    x += w
y = y0 + 40
for s in pairs:
    vals = [DECK_NAME[s['deck']], s['name'], s['type'], '%g' % s['at'][0], '%g／%g' % (s['at'][1], 321 - s['at'][1]), '%g' % s['at'][2],
            '%g' % s['axis_z'], '%g' % s['phi'], '%g' % s['back'], '%+.2f' % s['muzzle_beyond_outer']]
    x = bx
    for (name, w), v in zip(cols, vals):
        col = TYPE_COL[s['type']] if name == '型號' else ((150, 0, 0) if name == '伸出' and s['muzzle_beyond_outer'] < 0 else INK)
        d.text((x, y), v, fill=col, font=Fs)
        x += w
    d.line([(bx, y + 26), (x, y + 26)], fill=GRID)
    y += 30
im = im.crop((0, 0, W, y + 40))
out = os.path.join(HERE, 'sheet11_guns_v1.png')
im.save(out)
cnt = {}
for s in pairs:
    cnt[(s['deck'], s['type'])] = cnt.get((s['deck'], s['type']), 0) + 2
print(out, im.size, '對 %d、門 %d' % (len(pairs), len(pairs) * 2), sorted(cnt.items()))
