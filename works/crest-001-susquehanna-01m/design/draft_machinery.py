# 蘇士奎哈納號（crest-001，TASK-0697）階段九：機艙 —— 兩具斜置直動式主機（右舷一具、左舷鏡像）、四座銅鍋爐（前後兩組、背靠背）、明輪軸（右舷一段、左舷鏡像）、
#   機艙鐵地板（甲板 level −1）＋一座梯子上住艙甲板、砲甲板上的軸罩（明輪軸從砲甲板板底下過 ⇒ 板開一條縫、上面蓋木罩）。crest-001 自己寫的（做法照拿破崙號 draft_engine.py 的思路）。
#   史料：STUART／BARTOL —— 兩具 inclined direct-acting 主機、汽缸 70 in × 10 ft、佔船長 49 ft；四座銅鍋爐 15¾ × 15 × 12¾ ft、back to back；煙囪接在鍋爐上。其他尺寸都是設計決定。
#   輸出（世界座標；子作品框收緊到部件、關聯 at ＝ 框原點，鏡像的另一舷 at.y ＝ 401 − at.y − 高）：
#     masks/machinery/{engine_S,boilers_aft,boilers_fore,shaft_S,floor,ladder,casing}.vox.txt、masks/machinery/deck_gun_carve.vox.txt（砲甲板開軸縫，carvevox 守門）、
#     machinery_placement.json（固定點、meta）、verify_machinery.json、sheet07_machinery_v1.png
#   用法：python -I -X utf8 draft_machinery.py <design>
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import mio
from draft_lines import font, palette_rgb

YC = 200


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    plan = HL.load_plan(design)
    MC = plan['machinery']
    C = MC['colors']
    G, H = mio.stage_base(design, ('decks', 'ladders', 'deco', 'masts', 'paddles'), nz=260)
    S = G > 0
    hullset = np.zeros_like(S)
    hullset[H[:, 0], H[:, 1], H[:, 2]] = True
    L = HL.Lines(plan)
    x0h, ylo, SOL, dist = __import__('draft_lines').hull_volume(L, plan)

    def inside(x, y, z):
        """在船殼裡面（外形實心、不是牆）。"""
        i, j = x - x0h, y - ylo
        if i < 0 or j < 0 or i >= SOL.shape[0] or j >= SOL.shape[1] or z >= SOL.shape[2] or z < 0:
            return False
        return bool(SOL[i, j, z]) and dist[i, j, z] > plan['hull_build']['wall'] + 1e-6
    parts = {k: {} for k in ('engine_S', 'boilers_aft', 'boilers_fore', 'shaft_S', 'floor', 'ladder', 'casing')}
    clash = {k: 0 for k in parts}

    def put(k, x, y, z, c, need_inside=True):
        q = (int(x), int(y), int(z))
        if S[q] or (need_inside and not inside(*q)):
            clash[k] += 1
            return
        parts[k][q] = c
    sx, sz = MC['shaft']['x'], MC['shaft']['z']
    # ── 機艙地板（鐵板，z floor；x 範圍；每 every 格開排水孔）──
    FL = MC['floor']
    zf = FL['z']
    for x in range(FL['x'][0], FL['x'][1] + 1):
        for y in range(YC - 70, YC + 71):
            if not inside(x, y, zf):
                continue
            hole = (x - FL['x'][0]) % FL['drain_every'] < 2 and abs(y - YC) <= 1
            if hole:
                continue
            put('floor', x, y, zf, C['plate'])
    zb = zf + 1                                                                  # 機器坐在地板上
    # ── 主機（右舷那一具；平面 y ＝ YC ＋ dy）──
    E = MC['engine']
    dy_e = E['dy']
    cyl = np.array(E['cyl_c'], float)                                            # 汽缸中心 (x, z)
    crank = np.array([sx, sz], float)
    axv = (crank - cyl) / np.linalg.norm(crank - cyl)                            # 汽缸軸（往曲軸）
    nrm = np.array([-axv[1], axv[0]])
    ang = math.degrees(math.atan2(axv[1], axv[0]))

    def seg(k, p, q, r, col, ys, need_inside=True):
        p, q = np.array(p, float), np.array(q, float)
        n = max(2, int(np.linalg.norm(q - p) * 3))
        R = int(math.ceil(r)) + 1
        for t in np.linspace(0, 1, n):
            c = p + (q - p) * t
            for x in range(int(c[0]) - R, int(c[0]) + R + 1):
                for z in range(int(c[1]) - R, int(c[1]) + R + 1):
                    if (x + 0.5 - c[0]) ** 2 + (z + 0.5 - c[1]) ** 2 <= r * r:
                        for y in ys:
                            if (x, y, z) not in parts[k]:
                                put(k, x, y, z, col, need_inside)
    yE = YC + dy_e
    # 汽缸：軸 ± half_len、半徑 r 的圓柱（y 方向是圓的寬度 ⇒ 用 3D：離汽缸軸的距離 ≤ r）
    hl, rc = E['cyl_len'] / 2.0, E['cyl_r']
    for x in range(int(cyl[0]) - 30, int(cyl[0]) + 31):
        for z in range(max(zb, int(cyl[1]) - 30), int(cyl[1]) + 31):
            for y in range(yE - int(rc) - 1, yE + int(rc) + 2):
                v = np.array([x + 0.5 - cyl[0], z + 0.5 - cyl[1]])
                t = float(v @ axv)
                d2 = float(v @ nrm) ** 2 + (y + 0.5 - (yE + 0.5)) ** 2
                if abs(t) <= hl and d2 <= rc * rc:
                    band = abs(abs(t) - hl) < 1.2 or abs(t) < 0.6
                    put('engine_S', x, y, z, C['brass'] if band else C['iron'])
    top = cyl + axv * hl
    # 汽缸座：從汽缸底下撐到地板（兩塊板）
    for x in range(int(cyl[0]) - 12, int(cyl[0]) + 13, 1):
        for y in (yE - 6, yE - 5, yE + 5, yE + 6):
            for z in range(zb, int(cyl[1])):
                v = np.array([x + 0.5 - cyl[0], z + 0.5 - cyl[1]])
                if float(v @ nrm) < -rc + 1 and abs(float(v @ axv)) <= 10:
                    put('engine_S', x, y, z, C['iron'])
    # 底座（bedplate）：從汽缸後端到曲軸座
    for x in range(E['bed_x'][0], E['bed_x'][1] + 1):
        for y in range(yE - E['bed_half'], yE + E['bed_half'] + 1):
            for z in range(zb, zb + E['bed_h']):
                put('engine_S', x, y, z, C['iron'])
    # 導桿（兩根，汽缸頂往曲軸方向 guide_len）、活塞桿、十字頭、連桿、曲柄
    gl = E['guide_len']
    for s_ in (-3, 3):
        seg('engine_S', top + nrm * 2.5, top + axv * gl + nrm * 2.5, 0.9, C['steel'], [yE + s_])
        seg('engine_S', top - nrm * 2.5, top + axv * gl - nrm * 2.5, 0.9, C['steel'], [yE + s_])
    xh = top + axv * (gl * 0.75)
    seg('engine_S', top, xh, 1.2, C['steel'], [yE])
    for y in range(yE - 4, yE + 5):
        seg('engine_S', xh - axv * 2, xh + axv * 2, 2.2, C['steel'], [y])
    pin = crank + np.array(E['pin_off'], float)
    seg('engine_S', xh, pin, 1.4, C['steel'], [yE - 1, yE, yE + 1])
    for y in (yE - 3, yE - 2, yE + 2, yE + 3):
        seg('engine_S', crank, pin, 2.5, C['iron'], [y])                         # 曲柄（兩片）
    # 曲軸座（A 字架）：兩條腿從底座撐到曲軸下面的軸承
    brg = crank + np.array([0, -E['bearing_drop']], float)
    for s_ in (-1, 1):
        foot = np.array([sx + s_ * E['leg_spread'], zb + E['bed_h']], float)
        seg('engine_S', foot, brg, 1.6, C['iron'], [yE - 6, yE - 5, yE + 5, yE + 6])
    for x in range(sx - 5, sx + 6):
        for z in range(int(brg[1]) - 2, int(brg[1]) + 2):
            for y in list(range(yE - 7, yE - 3)) + list(range(yE + 4, yE + 8)):
                put('engine_S', x, y, z, C['iron'])
    # 冷凝器／氣泵（底座旁一個箱子）
    CD = E['condenser']
    for x in range(CD['x'][0], CD['x'][1] + 1):
        for y in range(YC + CD['dy'][0], YC + CD['dy'][1] + 1):
            for z in range(zb, zb + CD['h']):
                put('engine_S', x, y, z, C['iron'])
    # ── 鍋爐（每組兩座：兩舷各一座；箱形、頂收圓 crown；爐門那一面三個黑色爐口）──
    B = MC['boilers']
    for key in ('aft', 'fore'):
        R = B[key]
        k = 'boilers_' + key
        for sgn in (1, -1):
            for x in range(R['x'][0], R['x'][1] + 1):
                for dy in range(B['dy'][0], B['dy'][1] + 1):
                    y = YC + sgn * dy
                    for z in range(zb, zb + B['h']):
                        # 頂收圓：離兩側邊 crown 格以內、頂上 crown 格以內 ⇒ 圓角
                        u = min(dy - B['dy'][0], B['dy'][1] - dy)
                        w = zb + B['h'] - 1 - z
                        if u < B['crown'] and w < B['crown'] and (B['crown'] - u) ** 2 + (B['crown'] - w) ** 2 > B['crown'] ** 2:
                            continue
                        face = x == (R['x'][0] if R['doors'] == 'aft' else R['x'][1])
                        door = face and any(abs(dy - dd) <= 3 for dd in B['door_dy']) and zb + 4 <= z <= zb + 10
                        c = C['fire'] if door else C['copper']
                        put(k, x, y, z, c)
    # 煙箱與煙道（兩組鍋爐頂 ⇒ 煙囪底 z_from 那一圈）：從兩組的外框頂收成煙囪的圓（鐵殼 1 格）
    fz = plan['deco']['funnel']['z_from']
    f = plan['funnels']['rows'][0]
    zt = zb + B['h']
    for z in range(zt, fz):
        t = (z - zt) / float(max(1, fz - 1 - zt))
        hx = (1 - t) * (B['fore']['x'][1] - B['aft']['x'][0]) / 2.0 + t * f['r']
        hy = (1 - t) * B['dy'][1] + t * f['r']
        xc = (1 - t) * (B['aft']['x'][0] + B['fore']['x'][1]) / 2.0 + t * f['x']
        for x in range(int(xc - hx) - 1, int(xc + hx) + 2):
            for y in range(YC - int(hy) - 1, YC + int(hy) + 2):
                e = max(abs(x + 0.5 - xc) / max(1, hx), abs(y - YC) / max(1, hy))
                if 0.6 <= e <= 1.0:                                                 # v2：0.86 太薄、上下層不連通（z 50 那一圈 939 格浮空）
                    put('boilers_aft' if x < (B['aft']['x'][1] + B['fore']['x'][0]) / 2.0 else 'boilers_fore', x, y, z, C['iron'])
    # ── 明輪軸（右舷段：從主機曲柄往外到船殼內面；穿船殼那一段借船殼的格 —— 造船規格 §9.6）──
    SH = MC['shaft']
    for y in range(YC + SH['y_in'], YC + SH['y_out'] + 1):
        for x in range(sx - 5, sx + 6):
            for z in range(sz - 5, sz + 6):
                if (x - sx) ** 2 + (z - sz) ** 2 <= SH['r'] ** 2 and not hullset[x, y, z]:
                    q = (x, y, z)
                    if q in parts['engine_S']:
                        continue
                    if S[q]:
                        clash['shaft_S'] += 1
                        continue
                    parts['shaft_S'][q] = C['steel']
    # ── 砲甲板的軸縫與軸罩：軸（z sz ± r）碰到的砲甲板板 ⇒ 刻掉；上面蓋一條木罩（跨過兩舷舷牆之間）──
    CS = MC['casing']
    deck_gun = mio._folder(design, 'decks')
    dgk = {(x, y, z): c for x, y, z, c in deck_gun.tolist()}
    deck_carve = {}
    for (x, y, z), c in dgk.items():
        if abs(x - sx) <= SH['r'] + 1 and z <= sz + SH['r'] + 1 and z >= sz - SH['r'] - 1 and abs(y - YC) <= SH['y_out']:
            if (x - sx) ** 2 + (z - sz) ** 2 <= (SH['r'] + 0.6) ** 2:
                deck_carve[(x, y, z)] = c
    zd = int(LY.deck_z(plan, 'gun', sx))
    for x in range(sx - CS['half'], sx + CS['half'] + 1):
        for y in range(YC - CS['y'], YC + CS['y'] + 1):
            for z in range(zd + 1, zd + 1 + CS['h']):
                edge = abs(x - sx) == CS['half'] or z == zd + CS['h']
                if not S[x, y, z] or (x, y, z) in deck_carve:
                    if abs(y - YC) <= 13 and abs(x - sx) <= 13:                   # 煙囪、主桅不在這裡；中線留給軸罩
                        pass
                    parts['casing'][(x, y, z)] = CS['edge'] if edge else CS['color']
    # 軸罩不蓋在梯子口、艙口上（現況有的格不放）
    parts['casing'] = {q: c for q, c in parts['casing'].items() if not S[q]}
    # ── 梯子：機艙地板 → 住艙甲板（陡梯：每階 rise 格、往前 run 格；住艙甲板開口照梯子長）──
    LD = MC['ladder']
    xs, yc_l = LD['x'], YC
    zl = zf
    zu = int(LY.deck_z(plan, 'berth', xs + LD['run'] * 20))
    n = (zu - zl) // LD['rise']
    th = LD['half']
    for kk in range(1, n + 1):
        x = xs + LD['run'] * kk
        z = zl + LD['rise'] * kk
        for xx in range(x, x + LD['run']):
            for y in range(yc_l - th, yc_l + th + 1):
                put('ladder', xx, y, z, C['wood'])
        for zz in range(z - LD['rise'], z + 1):
            for xx in range(x, x + LD['run']):
                for y in (yc_l - th - 1, yc_l + th + 1):
                    put('ladder', xx, y, zz, C['wood'])
    hx0, hx1 = xs + LD['run'] * (n - 4), xs + LD['run'] * (n + 1)
    berth_hole = {}
    for (x, y, z), c in dgk.items():                                              # 住艙甲板要開的口：梯子上半段穿過的那幾格
        if hx0 <= x <= hx1 and abs(y - yc_l) <= th + 1 and abs(z - zu) <= 3:
            berth_hole[(x, y, z)] = c
    lad_pts = {'engine-berth': {'foot': [xs - 1, yc_l, zl + 1], 'lo': [xs + LD['run'], yc_l, zl + LD['rise'] + 1],
                                'hi': [xs + LD['run'] * n, yc_l, zl + LD['rise'] * n + 1], 'head': [xs + LD['run'] * n + 3, yc_l, zu + 1]}}
    # 部件之間：地板 ＞ 梯子；明輪軸（兩舷）＞ 軸罩
    parts['ladder'] = {q: c for q, c in parts['ladder'].items() if q not in parts['floor']}
    shaft_both = set(parts['shaft_S']) | {(x, 2 * YC - y, z) for (x, y, z) in parts['shaft_S']}
    parts['casing'] = {q: c for q, c in parts['casing'].items() if q not in shaft_both}
    # ── 讀數 ──
    R = {'cells': {k: len(v) for k, v in parts.items()}, 'clash_skipped': clash, 'deck_gun_carve': len(deck_carve), 'berth_hole': len(berth_hole),
         'engine_axis_deg': round(ang, 2), 'cyl_top': [round(float(v), 2) for v in top], 'crank': crank.tolist()}
    allp = {}
    for k, v in parts.items():
        for q in v:
            allp.setdefault(q, []).append(k)
    R['overlap_between'] = sum(1 for v in allp.values() if len(v) > 1)
    R['mirror_note'] = 'engine_S、shaft_S 的左舷用鏡像關聯（y ↔ 400 − y）；鍋爐、地板、梯子、軸罩自己兩舷對稱'
    asym = {k: sum(1 for (x, y, z), c in parts[k].items() if parts[k].get((x, 2 * YC - y, z)) != c) for k in ('boilers_aft', 'boilers_fore', 'floor', 'casing')}
    R['asym'] = asym
    # 固定點（世界座標）
    zb_ = zb
    an = {
        'engine_S': {'core': [int(cyl[0]), yE, int(cyl[1])], 'tend-1': [int(cyl[0]) - 6, YC + E['tend_dy'], zb_]},
        'boilers_aft': {'boiler-1': [(B['aft']['x'][0] + B['aft']['x'][1]) // 2, YC + (B['dy'][0] + B['dy'][1]) // 2, zb_ + B['h'] // 2],
                        'boiler-2': [(B['aft']['x'][0] + B['aft']['x'][1]) // 2, YC - (B['dy'][0] + B['dy'][1]) // 2, zb_ + B['h'] // 2],
                        'uptake': [f['x'], YC, fz - 1], 'stoke-1': [B['aft']['x'][0] - 3, YC + B['door_dy'][0], zb_], 'stoke-2': [B['aft']['x'][0] - 3, YC - B['door_dy'][0], zb_]},
        'boilers_fore': {'boiler-1': [(B['fore']['x'][0] + B['fore']['x'][1]) // 2, YC + (B['dy'][0] + B['dy'][1]) // 2, zb_ + B['h'] // 2],
                         'boiler-2': [(B['fore']['x'][0] + B['fore']['x'][1]) // 2, YC - (B['dy'][0] + B['dy'][1]) // 2, zb_ + B['h'] // 2],
                         'uptake': [f['x'], YC, fz - 1], 'stoke-1': [B['fore']['x'][1] + 3, YC + B['door_dy'][0], zb_], 'stoke-2': [B['fore']['x'][1] + 3, YC - B['door_dy'][0], zb_]},
        'shaft_S': {'fwd': [sx, YC + SH['y_in'], sz], 'aft': [sx, YC + SH['aft_dy'], sz]},
        'ladder': {('engine-berth.' + p): v for p, v in lad_pts['engine-berth'].items()},
    }
    # 固定點檢查：core／boiler-n 旁 8 格有自己的格；stoke／tend 站得住（腳下實心、頭上 12 格空）
    allc = S.copy()
    for v in parts.values():
        for q in v:
            allc[q] = True
    for q in deck_carve:
        allc[q] = False
    chk = {}
    for k, A_ in an.items():
        for nm, p in A_.items():
            x, y, z = p
            if nm.startswith(('core', 'boiler-')):
                near = sum(1 for q in parts[k] if abs(q[0] - x) <= 8 and abs(q[1] - y) <= 8 and abs(q[2] - z) <= 8)
                chk['%s/%s' % (k, nm)] = {'near_cells': near}
            elif nm.startswith(('stoke', 'tend')) or nm.endswith(('.foot', '.head')):
                chk['%s/%s' % (k, nm)] = {'air': not allc[x, y, z], 'floor': bool(allc[x, y, z - 1]), 'head_clear': int(allc[x, y, z:z + 12].sum())}
    R['anchor_check'] = chk
    # 空腔（機艙一帶）
    box = (slice(360, 680), slice(110, 291), slice(0, 120))
    U = allc[box]
    R['cavity_cells'] = int((ndimage.binary_fill_holes(U) & ~U).sum())
    # ── 寫檔 ──
    od = os.path.join(design, 'masks', 'machinery')
    os.makedirs(od, exist_ok=True)
    R['lists'] = {}
    place = {'parts': {}}
    for k, v in parts.items():
        bb = dict(v)
        for p_ in an.get(k, {}).values():                                        # 固定點要在作品框裡（站位 stoke／tend 在部件外面）⇒ 框包住固定點
            bb.setdefault(tuple(p_), 0)
        org, size = mio.bbox(bb)
        R['lists'][k] = mio.write_local(os.path.join(od, k + '.vox.txt'), v, org, '# 蘇士奎哈納號 機艙 %s（draft_machinery.py；子作品座標，關聯 at ＝ %s）\n' % (k, org))
        place['parts'][k] = {'at': org, 'size': size, 'anchors_local': {nm: [p[0] - org[0], p[1] - org[1], p[2] - org[2]] for nm, p in an.get(k, {}).items()},
                             'at_mirror': [org[0], mio.mirror_at_y(org[1], size[1]), org[2]]}
    for nm, cells in (('deck_gun_carve', deck_carve), ('deck_berth_hole', berth_hole)):
        with open(os.path.join(od, nm + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('# 蘇士奎哈納號 %s（carvevox，第 4 欄 ＝ 現在的色、守門；世界座標）\n' % nm)
            for q in sorted(cells):
                fh.write('%d,%d,%d,%d\n' % (q + (cells[q],)))
    place['meta'] = MC['meta']
    with open(os.path.join(design, 'machinery_placement.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(place, fh, ensure_ascii=False, indent=1)
    # 圖：中線往右舷 30 格那一片（主機平面）的側視＋俯視
    sc = 3
    X0, X1, Z1 = 360, 680, 120
    im = Image.new('RGB', ((X1 - X0) * sc + 40, Z1 * sc + 200 * sc // 2 + 120), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '蘇士奎哈納號 新圖紙 07：機艙（側視 y ＝ %d 主機那一片；下：俯視 z ＝ %d）　v1' % (yE, zb + 20), fill=(0, 0, 0), font=font(18))
    oy = 40
    for x in range(X0, X1):
        for z in range(0, Z1):
            c = None
            for k, v in parts.items():
                if (x, yE, z) in v:
                    c = palette_rgb(v[(x, yE, z)])
            if c is None and S[x, yE, z]:
                c = (200, 200, 200)
            if c:
                d.rectangle([20 + (x - X0) * sc, oy + (Z1 - 1 - z) * sc, 20 + (x - X0 + 1) * sc - 1, oy + (Z1 - z) * sc - 1], fill=c)
    oy2 = oy + Z1 * sc + 20
    zz = zb + 20
    for x in range(X0, X1):
        for y in range(100, 300):
            c = None
            for k, v in parts.items():
                for z in range(zz, zb - 1, -1):
                    if (x, y, z) in v:
                        c = palette_rgb(v[(x, y, z)])
                        break
                if c:
                    break
            if c is None and S[x, y, zz]:
                c = (200, 200, 200)
            if c:
                d.rectangle([20 + (x - X0) * sc, oy2 + (y - 100) * sc // 2, 20 + (x - X0 + 1) * sc - 1, oy2 + (y - 99) * sc // 2], fill=c)
    im.save(os.path.join(design, 'sheet07_machinery_v1.png'))
    with open(os.path.join(design, 'verify_machinery.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'lists'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
