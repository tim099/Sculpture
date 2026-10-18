# 新圖紙 01：線形（側面輪廓、半寬水線、橫剖面）＋ 讀數（水線長寬、排水量、Cb）。
# 用法：python -I -X utf8 -B draft_lines.py  ⇒ sheet01_lines.png、verify_lines.json（重跑逐位元組相同）
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dro

D = dro.D
P = dro.PLAN
WL = P['waterline_z']
S = 3                                   # 每格幾 px
FONT = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 22)
FS = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 16)

X0, X1 = 0, dro.NX
ZT = 80                                  # 側面圖畫到 z 80
W = (X1 - X0) * S + 160
Hh = ZT * S + 60 + 130 * S // 2 * 2 + 80 + 260
img = Image.new('RGB', (W, Hh), (250, 247, 238))
g = ImageDraw.Draw(img)
INK, RED, BLUE, GRY = (30, 30, 40), (180, 30, 30), (40, 80, 170), (170, 170, 170)


def pside(x, z):                         # 側面：左邊船尾、右邊船頭
    return 80 + (x - X0) * S, 40 + (ZT - z) * S


oy_plan = 40 + ZT * S + 40 + 22 * S


def pplan(x, y):
    return 80 + (x - X0) * S, oy_plan + (y - dro.YM) * S


g.text((80, 6), '持火號（拜占庭 dromon）新圖紙 01：線形　1 格 = 0.1 m　erina 設計', font=FONT, fill=INK)
# 格線（每 1 m）
for x in range(0, X1 + 1, 10):
    a, _ = pside(x, 0)
    g.line([a, 40, a, 40 + ZT * S], fill=(232, 228, 215) if x % 50 else (205, 200, 185))
for z in range(0, ZT + 1, 10):
    _, b = pside(0, z)
    g.line([80, b, 80 + X1 * S, b], fill=(232, 228, 215) if z % 50 else (205, 200, 185))

# 側面輪廓：每一欄最低（龍骨底）與舷弧
prof_top, prof_bot = [], []
for x10 in range(int(dro.end_aft(60) * 10), int(dro.end_fwd(60) * 10) + 1):
    x = x10 / 10
    top = dro.sheer(x)
    # 這一欄船殼最低點：龍骨底 0（龍骨範圍）或船殼底
    zs = [z / 4 for z in range(0, int(top * 4) + 1) if dro.hb(x, z / 4) >= 0]
    if not zs:
        continue
    bot = 0 if (P['hull']['stern']['x_foot'] <= x <= P['hull']['stem']['x_foot']) else min(zs)
    prof_top.append(pside(x, top)); prof_bot.append(pside(x, bot))
g.line(prof_top, fill=INK, width=2); g.line(prof_bot, fill=INK, width=2)
# 艏柱、艉柱
g.line([pside(dro.end_fwd(z / 4), z / 4) for z in range(int(P['hull']['stem']['z_foot'] * 4), int(P['hull']['stem']['z_head'] * 4) + 1)], fill=INK, width=2)
g.line([pside(dro.end_aft(z / 4), z / 4) for z in range(int(P['hull']['stern']['z_foot'] * 4), int(P['hull']['stern']['z_head'] * 4) + 1)], fill=INK, width=2)
# 水線
g.line([pside(X0, WL), pside(X1, WL)], fill=BLUE, width=1)
g.text(pside(X0 + 2, WL + 4), 'DWL z %d' % WL, font=FS, fill=BLUE)

# 半寬水線（俯視上半＝P 舷）
for z, col in ((WL, BLUE), (4, GRY), (7, GRY), (14, GRY), (18, GRY)):
    pts = []
    for x10 in range(0, X1 * 10):
        x = x10 / 10
        w = dro.hb(x, z)
        if w >= 0:
            pts.append(pplan(x, dro.YM - w))
    if len(pts) > 1:
        g.line(pts, fill=col, width=2 if col == BLUE else 1)
# 舷弧的半寬（甲板邊）
pts = [pplan(x10 / 10, dro.YM - dro.hb(x10 / 10, dro.sheer(x10 / 10))) for x10 in range(0, X1 * 10) if dro.hb(x10 / 10, dro.sheer(x10 / 10)) >= 0]
g.line(pts, fill=INK, width=2)
g.line([pplan(X0, dro.YM), pplan(X1, dro.YM)], fill=RED, width=1)

# 橫剖面（body plan）：船尾半邊在左、船頭半邊在右
stations = [40, 60, 90, 130, 190, 250, 290, 320, 340, 350]
ox, oz = 80 + 60 * S, Hh - 30
g.text((80, oz - 50 * S - 30), '橫剖面（左：船中以後；右：船中以前）', font=FS, fill=INK)
for x in stations:
    side = -1 if x <= P['hull']['x_mid'] else 1
    pts = []
    for z4 in range(0, int(dro.sheer(x) * 4) + 1):
        z = z4 / 4
        w = dro.hb(x, z)
        if w >= 0:
            pts.append((ox + side * w * S * 2, oz - z * S * 2))
    if len(pts) > 1:
        g.line(pts, fill=INK if x != P['hull']['x_mid'] else RED, width=1)
g.line([ox - 30 * S * 2, oz - WL * S * 2, ox + 30 * S * 2, oz - WL * S * 2], fill=BLUE)
g.line([ox, oz, ox, oz - 50 * S * 2], fill=RED)

# 讀數
cells_wl = 0; vol = 0.0; lwl = []; bwl = 0.0
for x in range(X1):
    for z in range(0, WL):
        w = dro.hb(x + 0.5, z + 0.5)
        if w >= 0:
            vol += 2 * w
    w = dro.hb(x + 0.5, WL - 0.01)
    if w >= 0:
        lwl.append(x); bwl = max(bwl, 2 * w)
L = (lwl[-1] - lwl[0] + 1) if lwl else 0
mpv = P['frame']['mpv']
disp_t = vol * mpv ** 3 * 1.025
cb = vol / (L * bwl * WL) if L and bwl else 0
R = {'lwl_m': round(L * mpv, 2), 'bwl_m': round(bwl * mpv, 2), 'draught_m': WL * mpv, 'displacement_t': round(disp_t, 1), 'cb': round(cb, 3),
     'loa_hull_m': round((dro.end_fwd(dro.sheer(dro.NX)) - dro.end_aft(40)) * mpv, 2),
     'sheer_mid_m': round(P['hull']['sheer']['z_mid'] * mpv, 2), 'freeboard_mid_m': round((P['hull']['sheer']['z_mid'] - WL) * mpv, 2)}
y = 40 + ZT * S + 10
g.text((80 + X1 * S - 900, Hh - 200), '  '.join('%s %s' % kv for kv in R.items()), font=FS, fill=INK)
img.save(os.path.join(D, 'sheet01_lines.png'), optimize=False)
json.dump(R, open(os.path.join(D, 'verify_lines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print(json.dumps(R, ensure_ascii=False))
