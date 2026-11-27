# 利劍號 新圖紙 02（TASK-0022 步驟 3）：配置 ⇒ sheet02_layout_v1.png、verify_layout.json
#   側視：船殼外形（masks/hull）、主甲板線、三根桅與三角帆桁（plan.rig）、砲門與槳門（plan.ports）、長喙（plan.beak）、
#   船尾平台與遮陽桿（plan.stern_platform）、砲的擺法（plan.guns_plan，只畫位置）。讀數：每一件的格座標、框夠不夠放。
#   只讀 plan.json 與 masks/hull，不碰作品。用法：python -I -X utf8 draft_layout.py
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

V = HL.V
PLAN = HL.load_plan(HERE)
L = HL.Lines(PLAN)
K, XAP = L.K, L.XAP
AX, AY, AZ = PLAN['space']['assembly']


def cx(Xp):
    return XAP + Xp * K * 10


def cz(Zp):
    return Zp * K * 10


def main():
    cells = np.loadtxt(os.path.join(HERE, 'masks', 'hull', 'hull_01.vox.txt'), delimiter=',', comments='#', dtype=int)
    prof = {}
    for x, y, z, c in cells:
        lo, hi = prof.get(x, (999, -1))
        prof[x] = (min(lo, z), max(hi, z))
    R = {'masts': {}, 'beak': {}, 'stern_platform': {}, 'fits': {}}
    rig = PLAN['rig']['v']; ang = PLAN['rig']['yard_angle_deg']['v']
    keelson = 0.5                                                # 桅腳高度（公尺，設計決定：龍骨頂上 0.2 m 的 keelson）
    segs = []
    for m, v in rig.items():
        r = math.radians(v['rake_deg'])
        Xr, Zr = v['X_at_Z']                                     # 原圖上量到的一點（桅身中心）⇒ 照傾角推回桅腳 Z keelson
        x0 = cx(Xr - (Zr - keelson) * math.tan(r)); z0 = keelson * 10
        Lm = v['mast_len_m'] * 10
        x1 = x0 + Lm * math.sin(r); z1 = z0 + Lm * math.cos(r)
        # 帆桁：吊點在桅頂往下 1.5 m，前段 0.4、後段 0.6（設計決定，步驟 7 定）；前端低、後端高
        Ly = v['yard_len_m'] * 10; a = math.radians(ang[m])
        hx, hz = x0 + (Lm - 15) * math.sin(r), z0 + (Lm - 15) * math.cos(r)
        fx, fz = hx + 0.4 * Ly * math.cos(a), hz - 0.4 * Ly * math.sin(a)
        bx, bz = hx - 0.6 * Ly * math.cos(a), hz + 0.6 * Ly * math.sin(a)
        R['masts'][m] = {'foot': [round(x0, 1), round(z0, 1)], 'top': [round(x1, 1), round(z1, 1)],
                         'yard_fwd_end': [round(fx, 1), round(fz, 1)], 'yard_aft_end': [round(bx, 1), round(bz, 1)]}
        segs.append(((x0, z0), (x1, z1), (120, 70, 30), 3)); segs.append(((fx, fz), (bx, bz), (150, 90, 40), 2))
    bk = PLAN['beak']['v']
    up = [(cx(X), cz(Z)) for X, Z in bk['upper']]; lo = [(cx(X), cz(Z)) for X, Z in bk['lower']]
    R['beak'] = {'tip': [round(cx(bk['tip_X_plate']), 1), round(cz(bk['tip_Z_plate']), 1)], 'base_x': round(cx(bk['base_X_plate']), 1)}
    sp = PLAN['stern_platform']['v']
    spr = [(cx(X), cz(Z)) for X, Z in sp['rail_top']]; spu = [(cx(X), cz(Z)) for X, Z in sp['underside']]
    aw = [(cx(X), cz(Z)) for X, Z in sp['awning_spar']]
    R['stern_platform'] = {'rail_aft_end': [round(spr[0][0], 1), round(spr[0][1], 1)], 'awning_aft_end': [round(aw[0][0], 1), round(aw[0][1], 1)]}
    allx = [p[0] for s in segs for p in s[:2]] + [p[0] for p in up + lo + spr + aw]
    allz = [p[1] for s in segs for p in s[:2]] + [p[1] for p in up + lo + spr + aw]
    R['fits'] = {'x_min': round(min(allx), 1), 'x_max': round(max(allx), 1), 'z_max': round(max(allz), 1),
                 'assembly': [AX, AY, AZ], 'fits_x': bool(min(allx) >= 0 and max(allx) < AX), 'fits_z': bool(max(allz) < AZ)}
    # 圖
    s = 2
    W, H = AX * s + 120, AZ * s + 140
    img = Image.new('RGB', (W, H), (246, 242, 230)); d = ImageDraw.Draw(img); f = ImageFont.load_default()
    P = lambda x, z: (60 + x * s, H - 60 - z * s)
    d.text((40, 14), '%s - new sheet 02: layout (profile)   0.1 m/cell   assembly %dx%dx%d' % (PLAN['title_en'], AX, AY, AZ), fill=(20, 20, 40), font=f)
    d.rectangle([P(0, AZ), P(AX, 0)], outline=(180, 180, 180))
    for x, (a, b) in prof.items():
        d.line([P(x, a), P(x, b + 1)], fill=(90, 70, 50))
    wl = PLAN['waterline']['z']
    d.line([P(0, wl + 1), P(AX, wl + 1)], fill=(40, 110, 200))
    for a, b, c, w in segs:
        d.line([P(*a), P(*b)], fill=c, width=w)
    d.line([P(*p) for p in up], fill=(200, 30, 30), width=2); d.line([P(*p) for p in lo], fill=(200, 30, 30), width=2)
    d.line([P(*p) for p in spr], fill=(30, 120, 30), width=2); d.line([P(*p) for p in spu], fill=(30, 120, 30), width=1)
    d.line([P(*p) for p in aw], fill=(30, 120, 30), width=1)
    for m, v in R['masts'].items():
        d.text(P(v['top'][0] + 4, v['top'][1]), m, fill=(20, 20, 40), font=f)
    for x in range(0, AX + 1, 50):
        d.text((P(x, 0)[0] - 8, H - 50), str(x), fill=(80, 80, 80), font=f)
    d.text((40, H - 30), 'masts & yards: NAV 1749 / OR 2452 ratios x Chapman Lpp; yard angles and slings are design decisions (step 7). red = beak, green = stern platform & awning spar.', fill=(60, 60, 60), font=f)
    img.save(os.path.join(HERE, 'sheet02_layout_v1.png'))
    with open(os.path.join(HERE, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
