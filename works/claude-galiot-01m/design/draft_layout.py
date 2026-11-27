# 蠍子號 新圖紙 02（TASK-0023 步驟 3）：配置 ⇒ 圖紙 sheet02_layout_v1.png、讀數 verify_layout.json
#   用法：python -I -X utf8 draft_layout.py [--probe=benches.first_x=3] [--probe=drop_bench=5]
#   · 只讀 plan.json 與 masks/hull/hull_01.vox.txt（線形那張清單），不碰作品、不產清單（步驟 5 以後各自的程式照 layout.py 落格）。
#   · 量的是「配置放得進這個船殼嗎、遊戲用得了嗎」：
#     划手座（每舷幾張、間距、第一張離艉柱、最後一張離砲台）、中央走道寬高、舷外槳架寬、槳栓離水多高、
#     槳栓往裡到中央走道邊有多長（遊戲沿槳柄每 0.6 m 排一個槳手）、槳手站的那一格頭上 14 格空不空、
#     砲台底下淨空、梯子四點、spur 伸出多長、全長、各件跟船殼與彼此重疊、鏡像差；桅腳、帆桁的範圍、砲位腳下是什麼；
#     甲板高度表（每一層的 z 與離水線）、桅帆表（三角帆三邊與面積）、帆裝三段各張哪幾面、砲門（Ship_Steps 步驟 3 要的）。
#   · --probe：反向對照用（layout 的某個數字加減，⛔ 不寫檔）。
#   出處：結構照 claude-felucca-01m/design/draft_layout.py（海鷗號：plan.layout ⇒ 讀數、圖紙英文＋Pillow 內建字型），
#         件的幾何在 layout.py（出自皇家號、越嶺號的 draft_upper.py）。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import layout as LY

sys.stdout.reconfigure(encoding='utf-8')
HEAD = 14          # 遊戲：站的那一格往上 14 格要空（40_crew.js standZ；Ship_Oars §9.10.2）
ROWER_M = 0.6      # 遊戲：沿槳柄每 0.6 m 一個槳手（Ship_Oars §9.10）


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def mirror_diff(a):
    return int((a != a[:, ::-1, :]).sum())


def readings(plan, K, pieces, lpts, clipped):
    R = {'pieces': {}}
    allp = np.zeros(K.hull.shape, np.int16)
    for name, a in pieces.items():
        R['pieces'][name] = {'cells': int((a > 0).sum()), 'clipped_by_earlier': clipped[name], 'mirror_diff': mirror_diff(a),
                             'colors': {str(c): int((a == c).sum()) for c in np.unique(a[a > 0])}}
        allp += (a > 0)
    R['overlap_between_pieces'] = int((allp > 1).sum())
    R['overlap_with_hull'] = int(((allp > 0) & (K.hull > 0)).sum())
    union = (K.hull > 0) | (allp > 0)
    from scipy import ndimage
    lab, n = ndimage.label(union)
    R['components_hull_plus_pieces'] = int(n)
    holes = ndimage.binary_fill_holes(union) & ~union
    R['cavity_cells'] = int(holes.sum())
    wl = K.wl
    P = K.P
    # ── 划手座 ──
    be = P['benches']
    b0, b1 = be['dy']
    xsp = int(np.where((K.hull[:, K.YC, :] > 0).any(axis=1))[0].min())        # 船尾最後一格（艉柱外緣）
    rx0 = P['rambade']['x'][0]
    rows = []
    for xc in K.benches:
        st = K.seat_top(xc)
        heads = []
        for dy in range(b0, b1 + 1):
            col = union[xc, K.YC + dy, st + 1:st + 1 + HEAD]
            heads.append(int(col.sum()))
        rows.append({'x': xc, 'seat_top_z': st, 'seat_above_deck_cells': st - K.deck_top(xc, 0),
                     'head_blocked_cells': int(sum(heads)), 'stand_z': st + 1})
    dk = pieces['deck']                                     # 每舷幾張座：照格子數（座面那一格兩舷都是座的顏色）——v2 照設計清單數，拿掉一張照樣報 20（反向對照抓到）
    built = [xc for xc in K.benches if all(dk[xc, K.YC + s * b1, K.seat_top(xc)] == K.C['seat'] for s in (1, -1))]
    R['benches'] = {'per_side': len(built), 'missing_x': [xc for xc in K.benches if xc not in built], 'x': K.benches,
                    'pitch_mean_cells': round(float(np.diff(K.benches).mean()), 3) if len(K.benches) > 1 else None,
                    'first_from_stern_m': round((K.benches[0] - xsp) * 0.1, 2),
                    'last_to_rambade_cells': rx0 - K.benches[-1],
                    'seat_dy': [b0, b1], 'seat_span_m': round((b1 - b0 + 1) * 0.1, 2),
                    'head_blocked_total': int(sum(r['head_blocked_cells'] for r in rows)), 'rows': rows}
    # ── 中央走道 ──
    co = P['corsia']
    R['corsia'] = {'x': [co['x0'], co['x1']], 'width_m': round((2 * co['half'] + 1) * 0.1, 2), 'height_m': round(co['h'] * 0.1, 2),
                   'top_z_mid': int(K.deck_top((co['x0'] + co['x1']) // 2, 0) + co['h'])}
    # ── 舷外槳架與槳栓 ──
    ap = P['apostis']
    a = pieces['apostis']
    ys = np.where(a.any(axis=(0, 2)))[0]
    R['apostis'] = {'width_m': round((ys.max() - ys.min() + 1) * 0.1, 2) if len(ys) else None,
                    'x': ap['x'], 'beam_ratio': round(((ys.max() - ys.min() + 1) * 0.1) / (V(plan['lines']['half_beam']) * 0.2 + 0.1), 2) if len(ys) else None}
    th = P['tholes']
    tl = []
    for xc in K.benches:
        for dx in th['dx']:
            x = xc + dx
            rt = K.rail_top(x)
            dy = int(ap['half']) - int(ap['rail_w']) + 1 + int(th.get('dy_in_rail', 0))
            pivot_z = rt + 1                                  # 槳柄靠在縱樑頂上那一格
            inboard_cells = dy - (co['half'] + 1)             # 槳栓往裡到中央走道邊
            tl.append({'x': x, 'dy': dy, 'rail_top_z': rt, 'pivot_above_wl_m': round((pivot_z - (wl + 1)) * 0.1, 2),
                       'inboard_to_corsia_m': round(inboard_cells * 0.1, 2)})
    R['tholes'] = {'per_side': len(tl), 'rows': tl,
                   'pivot_above_wl_m': [min(t['pivot_above_wl_m'] for t in tl), max(t['pivot_above_wl_m'] for t in tl)],
                   'inboard_to_corsia_m': [min(t['inboard_to_corsia_m'] for t in tl), max(t['inboard_to_corsia_m'] for t in tl)]}
    oa = P['oars']
    n_row = int(oa['rowers'])
    R['oars'] = {'rowers_per_oar': n_row, 'per_bench': len(th['dx']),
                 'rowers_need_m': round(n_row * ROWER_M, 2),
                 'rowers_fit': all(t['inboard_to_corsia_m'] + 0.05 >= n_row * ROWER_M for t in tl),   # 門檻跟 rowers_need_m 同一個（v3 前是 (n−1)×0.6＋0.3，verifier3 指出兩套說法）
                 'outboard_m': oa['outboard_m'], 'inboard_m': oa['inboard_m'],
                 'water_angle_deg': [round(math.degrees(math.asin(min(1.0, t['pivot_above_wl_m'] / oa['outboard_m']))), 1) for t in (tl[0], tl[len(tl) // 2], tl[-1])],
                 'total_oars': 2 * len(tl), 'total_rowers': 2 * len(tl) * n_row}
    # ── 砲台、梯子 ──
    rx0, rx1, zt, d_in, wf = LY.rambade_geo(K)
    R['rambade'] = {'x': [rx0, rx1], 'floor_top_z': zt, 'clear_above_deck_cells': zt - 1 - max(K.deck_top(x, 0) for x in range(rx0, rx1 + 1)) - 1,
                    'dy': [d_in, wf(rx0), wf(rx1)]}
    chk = {}
    for nm, p4 in lpts.items():
        r = {}
        for k, (x, y, z) in p4.items():
            head = HEAD if k in ('foot', 'head') else 7
            r[k] = {'at': [x, y, z], 'empty': not bool(union[x, y, z]), 'solid_below': bool(union[x, y, z - 1]),
                    'blocked_above_within': int(next((h for h in range(1, head + 1) if union[x, y, z + h]), 0))}
        chk[nm] = r
    R['ladders'] = chk
    # ── spur、全長 ──
    sp = pieces['spur']
    sx = np.where(sp.any(axis=(1, 2)))[0]
    hx = np.where((K.hull > 0).any(axis=(1, 2)))[0]
    R['spur'] = {'x': [int(sx.min()), int(sx.max())], 'beyond_hull_m': round((sx.max() - hx.max()) * 0.1, 2)}
    R['length_overall_m'] = round((max(sx.max(), hx.max()) - hx.min() + 1) * 0.1, 2)
    R['hull_x'] = [int(hx.min()), int(hx.max())]
    # ── 艉台與篷 ──
    S = P['stern']
    R['stern'] = {'poop_x': S['poop_x'], 'poop_top_z': int(K.deck_top(S['poop_x'][1], 0) + S['poop_above_deck']),
                  'canopy_x': S['canopy_x'], 'canopy_ridge_z': int(K.deck_top((S['canopy_x'][0] + S['canopy_x'][1]) // 2, 0) + S['canopy_ridge'])}
    la = S.get('lantern')
    if la:                                                  # 燈桿：一格都沒放（那一欄沒有實心）要報得出來
        x = int(la['x'])
        pole = np.where(pieces['poop'][x, K.YC, :] == K.C['iron'])[0]     # 步驟 6 起燈桿在 poop 那一件
        R['lantern'] = {'x': x, 'pole_cells': int(len(pole)), 'pole_z': [int(pole.min()), int(pole.max())] if len(pole) else None,
                        'base_solid': bool(len(pole)) and bool(union[x, K.YC, int(pole.min()) - 1]),
                        'lamp_at': [x, K.YC, int(la['top_z'])], 'air_at_lamp': not bool(union[x, K.YC, int(la['top_z'])])}
    # ── 桅、帆桁（步驟 7 再做；這裡只排位置與範圍）──
    rig = P['rig']
    mm = {}
    for name, mv in rig['masts'].items():
        x = int(mv['x'])
        partner = K.deck_top(x, 0)
        top = partner + mv['above_deck_m'] * 10
        hx_ = (top - partner) * math.tan(math.radians(mv['rake_deg']))
        L_ = mv['yard_m'] * 10
        ang = math.radians(rig['yard_angle_deg'])
        hz = top - rig['sling_below_top']
        hx2 = x + 0.5 + (hz - partner) * math.tan(math.radians(mv['rake_deg']))
        fwd = (hx2 + L_ * mv['pivot_frac'] * math.cos(ang), hz - L_ * mv['pivot_frac'] * math.sin(ang))
        aft = (hx2 - L_ * (1 - mv['pivot_frac']) * math.cos(ang), hz + L_ * (1 - mv['pivot_frac']) * math.sin(ang))
        on_bench = any(abs(x - b) <= be['w'] // 2 for b in K.benches)
        mm[name] = {'x_partner': x, 'partner_z': partner, 'top_z': round(top, 1), 'top_x': round(x + 0.5 + hx_, 1),
                    'rake_deg': mv['rake_deg'], 'frac_from_stern': round((x - hx.min()) / float(hx.max() - hx.min()), 3),
                    'yard_m': mv['yard_m'], 'yard_fwd_end': [round(fwd[0], 1), round(fwd[1], 1)], 'yard_peak': [round(aft[0], 1), round(aft[1], 1)],
                    'through_bench': bool(on_bench)}
    R['masts'] = mm
    asm = plan['space']['assembly']
    R['rig_inside_assembly_frame'] = all(0 <= v['yard_fwd_end'][0] < asm[0] and 0 <= v['yard_peak'][0] < asm[0] and v['yard_peak'][1] < asm[2] and v['yard_fwd_end'][1] > 0
                                         for v in mm.values())
    # ── 桅帆表：三角帆 前緣（沿帆桁）＝ 帆桁長 × luff_frac、後緣／帆腳照前緣的比例；面積用三邊（Heron）──
    sails = {}
    for name, mv in rig['masts'].items():
        sv = mv.get('sail')
        if not sv:
            continue
        a = mv['yard_m'] * sv['luff_frac']
        b, c = a * sv['leech_ratio'], a * sv['foot_ratio']
        s2 = (a + b + c) / 2
        sails[name] = {'luff_m': round(a, 2), 'leech_m': round(b, 2), 'foot_m': round(c, 2),
                       'area_m2': round(math.sqrt(max(0.0, s2 * (s2 - a) * (s2 - b) * (s2 - c))), 1)}
    R['sails'] = sails
    R['sail_states'] = rig.get('states', {})
    R['gunports'] = rig.get('gunports', P.get('gunports'))
    # ── 甲板高度表（z ＝ 那一格的頂；離水線 ＝ (z − DWL 那一格的頂) × 0.1）──
    mid = int(plan['space']['mid_x'])
    wl_top = wl + 1

    def hrow(name, z):
        return {'name': name, 'z_top': int(z), 'above_dwl_m': round((int(z) - wl_top) * 0.1, 2)}

    hx0, hx1 = int(hx.min()), int(hx.max())
    R['heights'] = [
        hrow('keel bottom', 0), hrow('DWL', wl_top),
        hrow('deck at centreline, midship x %d' % mid, K.deck_top(mid, 0) + 1),
        hrow('deck at side, midship', K.deck_top(mid, K.hw_deck(mid)) + 1),
        hrow('rail (sheer), midship', K.sh[mid] + 1),
        hrow('rail (sheer), stern end x %d' % hx0, max(K.sh[x] for x in range(hx0, hx0 + 10)) + 1),
        hrow('rail (sheer), bow x %d' % (hx1 - 10), K.sh[hx1 - 10] + 1),
        hrow('corsia top, midship', R['corsia']['top_z_mid'] + 1),
        hrow('rowing bench top, midship', K.seat_top(mid) + 1),
        hrow('apostis rail top (oar pivot below it), midship', K.rail_top(mid) + 1),
        hrow('rambade floor', R['rambade']['floor_top_z'] + 1),
        hrow('poop floor', R['stern']['poop_top_z'] + 1),
        hrow('awning ridge', R['stern']['canopy_ridge_z'] + 1),
    ] + [hrow('%s mast top' % n, round(m['top_z'])) for n, m in mm.items()]
    # ── 砲位：腳下是什麼 ──
    gl = []
    for g in P['guns']:
        x, dy = int(g['x']), int(g['dy'])
        y = K.YC + dy
        zs = np.where(union[x, y, :])[0]
        stand = None
        if g['on'] == 'deck':
            stand = K.deck_top(x, dy)
        elif g['on'] == 'corsia':
            stand = int(K.deck_top(x, 0) + co['h'])
        elif g['on'] == 'rambade':
            stand = zt
        elif g['on'] == 'rail':
            stand = K.rail_top(x)
        elif g['on'] == 'poop':
            stand = int(K.deck_top(x, 0) + S['poop_above_deck'])
        gl.append({'id': g['id'], 'gun': g['gun'], 'x': x, 'dy': dy, 'on': g['on'], 'stand_z': stand,
                   'solid_at_stand': bool(union[x, y, stand]) if stand is not None else None,
                   'air_above_stand': int(next((h for h in range(1, 15) if union[x, y, stand + h]), 0)) if stand is not None else None})
    R['guns'] = gl
    return R


def sheet(plan, K, pieces, R, path):
    comp = K.hull.copy()
    for name, a in pieces.items():
        comp[a > 0] = a[a > 0]
    s = 3
    X0, X1 = 0, K.SX
    oa = K.P['oars']
    yr = int(K.P['apostis']['half'] + oa['outboard_m'] * 10) + 6                # 俯視圖兩舷畫到槳葉
    yr = min(yr, K.YC)
    W = (X1 - X0) * s + 120
    ZT = int(plan['space']['assembly'][2])
    H = 80 + 2 * yr * s + 60 + ZT * 2 + 80 + 260 + 240
    img = Image.new('RGB', (W, H), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((40, 14), '%s - new sheet 02: layout (deck, corsia, benches, apostis and tholes, rambade, spur, poop and awning, masts, yards, guns)   0.1 m/cell'
           % plan['title_en'], fill=(20, 20, 40), font=f)
    d.text((40, 34), '1. plan view (top colour of every (x, y); bow to the right); red circles = guns, brown dots = masts, blue = oars in the half-stroke pose (horizontal projection)',
           fill=(20, 20, 40), font=f)
    oy = 60
    ox = 60
    solid = comp > 0
    zt = np.where(solid.any(axis=2), K.SZ - 1 - np.argmax(solid[:, :, ::-1], axis=2), -1)
    for x in range(X0, X1):
        for y in range(K.YC - yr, K.YC + yr + 1):
            z = zt[x, y]
            if z >= 0:
                d.rectangle([ox + (x - X0) * s, oy + (y - K.YC + yr) * s, ox + (x - X0) * s + s - 1, oy + (y - K.YC + yr) * s + s - 1], fill=rgb(int(comp[x, y, z])))

    def py(y):
        return oy + (y - K.YC + yr) * s + s // 2

    for t in R['tholes']['rows']:
        out_h = math.sqrt(max(0.0, oa['outboard_m'] ** 2 - t['pivot_above_wl_m'] ** 2)) * 10
        for sg in (1, -1):
            yy = K.YC + sg * t['dy']
            d.line([ox + t['x'] * s, py(yy), ox + t['x'] * s, py(yy + sg * out_h)], fill=(40, 90, 200), width=1)
            d.line([ox + t['x'] * s, py(yy), ox + t['x'] * s, py(yy - sg * oa['inboard_m'] * 10)], fill=(120, 150, 220), width=1)
    for g in R['guns']:
        x, y = g['x'], K.YC + g['dy']
        d.ellipse([ox + x * s - 4, py(y) - 4, ox + x * s + 4, py(y) + 4], outline=(200, 30, 30), width=2)
    for name, m in R['masts'].items():
        d.ellipse([ox + m['x_partner'] * s - 3, py(K.YC) - 3, ox + m['x_partner'] * s + 3, py(K.YC) + 3], fill=(90, 50, 20))
    oy2 = oy + 2 * yr * s + 40
    base = oy2 + ZT * 2
    sz = 2
    d.text((40, oy2 - 20), '2. profile (starboard outside, bow right): hull and pieces; masts (brown), lateen yards at the design angle (orange), DWL (blue)', fill=(20, 20, 40), font=f)
    for x in range(X0, X1):
        zs = np.where(solid[x].any(axis=0))[0]
        for z in zs:
            ysx = np.where(solid[x, :, z])[0]
            d.rectangle([ox + x * s, base - (z + 1) * sz, ox + x * s + s - 1, base - z * sz - 1], fill=rgb(int(comp[x, ysx.max(), z])))
    d.line([ox, base - (K.wl + 1) * sz, ox + X1 * s, base - (K.wl + 1) * sz], fill=(40, 110, 200))
    for name, m in R['masts'].items():
        d.line([ox + m['x_partner'] * s, base - m['partner_z'] * sz, ox + m['top_x'] * s, base - m['top_z'] * sz], fill=(90, 50, 20), width=3)
        d.line([ox + m['yard_fwd_end'][0] * s, base - m['yard_fwd_end'][1] * sz, ox + m['yard_peak'][0] * s, base - m['yard_peak'][1] * sz], fill=(220, 130, 30), width=2)
        d.text((ox + m['x_partner'] * s + 6, base - m['top_z'] * sz - 12), '%s mast top z %.0f, yard %.1f m' % (name, m['top_z'], m['yard_m']), fill=(90, 50, 20), font=f)
    for x in range(0, X1 + 1, 20):
        d.line([ox + x * s, base + 4, ox + x * s, base + 10], fill=(80, 80, 80))
        d.text((ox + x * s - 8, base + 12), str(x), fill=(80, 80, 80), font=f)
    b = R['benches']
    ty = base + 36
    rows = [
        'benches: %d per side, pitch %.2f cells, first %.1f m from the sternpost, last %d cells before the rambade; seat span %.1f m; rowers head clearance blocked cells %d'
        % (b['per_side'], b['pitch_mean_cells'] or 0, b['first_from_stern_m'], b['last_to_rambade_cells'], b['seat_span_m'], b['head_blocked_total']),
        'corsia %.1f m wide x %.1f m high, x %d-%d; apostis %.1f m overall (%.2f x beam)' % (R['corsia']['width_m'], R['corsia']['height_m'], R['corsia']['x'][0], R['corsia']['x'][1], R['apostis']['width_m'], R['apostis']['beam_ratio']),
        'tholes: %d per side, pivot %.2f-%.2f m above DWL, thole to corsia edge %.1f-%.1f m; oars %d (%d rowers each, need %.1f m inboard), outboard %.1f m, water angle %s deg'
        % (R['tholes']['per_side'], R['tholes']['pivot_above_wl_m'][0], R['tholes']['pivot_above_wl_m'][1], R['tholes']['inboard_to_corsia_m'][0], R['tholes']['inboard_to_corsia_m'][1],
           R['oars']['total_oars'], R['oars']['rowers_per_oar'], R['oars']['rowers_need_m'], R['oars']['outboard_m'], R['oars']['water_angle_deg']),
        'rambade x %d-%d floor top z %d (%d cells clear above deck); spur x %d-%d, %.1f m beyond the hull; LOA incl. spur %.1f m'
        % (R['rambade']['x'][0], R['rambade']['x'][1], R['rambade']['floor_top_z'], R['rambade']['clear_above_deck_cells'], R['spur']['x'][0], R['spur']['x'][1], R['spur']['beyond_hull_m'], R['length_overall_m']),
        'guns: ' + ', '.join('%s %s x%d dy%+d on %s' % (g['id'], g['gun'], g['x'], g['dy'], g['on']) for g in R['guns'][:5]),
        '      ' + ', '.join('%s %s x%d dy%+d on %s' % (g['id'], g['gun'], g['x'], g['dy'], g['on']) for g in R['guns'][5:]),
        'overlap between pieces %d, with hull %d; components %d, cavity cells %d' % (R['overlap_between_pieces'], R['overlap_with_hull'], R['components_hull_plus_pieces'], R['cavity_cells']),
        'sources: plan.json layout.*.src (every number: source reading, conversion or design decision)',
    ]
    for i, r in enumerate(rows):
        d.text((40, ty + i * 18), r, fill=(30, 30, 30), font=f)
    # 3. 甲板高度表（左）、4. 桅帆表＋帆裝三段＋砲門（右）
    ty3 = ty + len(rows) * 18 + 24
    d.text((40, ty3), '3. heights (top of the cell; m above DWL)', fill=(20, 20, 40), font=f)
    for i, h in enumerate(R['heights']):
        y = ty3 + 22 + i * 17
        d.text((40, y), h['name'], fill=(30, 30, 30), font=f)
        d.text((360, y), 'z %d' % h['z_top'], fill=(160, 30, 30), font=f)
        d.text((420, y), '%+.1f m' % h['above_dwl_m'], fill=(160, 30, 30), font=f)
    tx4 = 560
    d.text((tx4, ty3), '4. masts and sails (lateen; luff along the yard)', fill=(20, 20, 40), font=f)
    hdr = ['mast', 'x', 'from stern', 'above deck', 'rake', 'yard', 'luff', 'leech', 'foot', 'area']
    cols = [0, 50, 100, 180, 260, 310, 370, 430, 490, 550]
    for c, t in zip(cols, hdr):
        d.text((tx4 + c, ty3 + 22), t, fill=(90, 90, 90), font=f)
    rig = K.P['rig']
    for i, (name, m) in enumerate(R['masts'].items()):
        sl = R['sails'].get(name, {})
        mv = rig['masts'][name]
        vals = [name, str(m['x_partner']), '%.2f L' % m['frac_from_stern'], '%.1f m' % mv['above_deck_m'], '%g deg' % mv['rake_deg'], '%.1f m' % mv['yard_m'],
                '%.1f m' % sl.get('luff_m', 0), '%.1f m' % sl.get('leech_m', 0), '%.1f m' % sl.get('foot_m', 0), '%.0f m2' % sl.get('area_m2', 0)]
        for c, t in zip(cols, vals):
            d.text((tx4 + c, ty3 + 42 + i * 17), t, fill=(160, 30, 30), font=f)
    ys = ty3 + 42 + len(R['masts']) * 17 + 14
    d.text((tx4, ys), 'sail states (game: furled / reduced / battle / full):', fill=(20, 20, 40), font=f)
    for i, (st, setl) in enumerate(R['sail_states'].items()):
        d.text((tx4 + 20, ys + 18 + i * 17), '%s: %s' % (st, ', '.join(setl) if setl else '(none set)'), fill=(30, 30, 30), font=f)
    yg = ys + 18 + len(R['sail_states']) * 17 + 14
    d.text((tx4, yg), 'gun ports: %s' % R['gunports'], fill=(20, 20, 40), font=f)
    img.save(path)


def main():
    plan = HL.load_plan(HERE)
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=')
            probe[k] = float(v)
    K = LY.Ctx(plan, probe or None)
    pieces, lpts, clipped = LY.assemble(K)
    R = readings(plan, K, pieces, lpts, clipped)
    if probe:
        print(json.dumps({'probe': probe, 'benches': {k: v for k, v in R['benches'].items() if k != 'rows'},
                          'tholes': {k: v for k, v in R['tholes'].items() if k != 'rows'}, 'pieces': {k: v['cells'] for k, v in R['pieces'].items()},
                          'rambade': R['rambade'], 'guns': R['guns']}, ensure_ascii=False))
        return
    with open(os.path.join(HERE, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(plan, K, pieces, R, os.path.join(HERE, 'sheet02_layout_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('ladders',)}, ensure_ascii=False)[:6000])
    print(json.dumps(R['ladders'], ensure_ascii=False))


if __name__ == '__main__':
    main()
