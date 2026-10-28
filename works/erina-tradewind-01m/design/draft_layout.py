# 出處：erina-oxford-01m/design/draft_layout.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 新圖紙 02（TASK-1097）：總佈置 —— 側面帆圖（甲板、炮門、桅、帆桁、帆）＋俯視（主甲板、炮門、桅、帆桁）＋主尺寸表
#   用法：python -I -X utf8 draft_layout.py <design 資料夾> [--probe=port=gun:1:+3]
#   ⇒ sheet02_layout_v1.png、verify_layout.json。只讀 plan.json、不碰作品。
#   跟牛津號不同：兩根桅；主帆 gaff＋boom；艏斜桅＋三角帆桿；沒有艉樓、沒有後甲板砲。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import font, hull_volume


def readings(plan, L, Y, S, x0, ylo):
    wl = float(plan['waterline']['z'])
    m = plan['meters_per_cell']
    R = {'waterline_z': wl}
    ports, bad = [], []
    D = plan['decks']
    for p in Y.ports():
        top = p['sill'] + p['h']
        rail = float(L.top_z(p['x']))
        over = None
        for up in ('qd', 'fc'):
            if p['deck'] == 'gun' and D[up]['x0'] <= p['x'] <= D[up]['x1']:
                over = float(L.deck_z(up, p['x'])) - 3                     # 上面那一層的甲板板＋樑 3 格
        ceil = min(rail, over) if over is not None else rail
        row = {'deck': p['deck'], 'x': p['x'], 'sill_z': p['sill'], 'sill_above_wl_m': round((p['sill'] - wl) * m, 2), 'top_z': top, 'ceiling_z': round(ceil, 1), 'margin': round(ceil - top, 1),
               'half_beam_at_sill': round(float(L.hb(np.array([p['x'] + 0.5]), np.array([p['sill'] + 0.5]))[0]), 1)}
        ports.append(row)
        if row['margin'] < 2:
            bad.append('炮門 %s x %d 頂 %d 離上面（舷頂／甲板底）只 %.1f 格' % (p['deck'], p['x'], top, row['margin']))
    for deck in plan['ports']:
        xs = plan['ports'][deck]['x']
        R['port_gaps_' + deck] = [b - a - plan['ports'][deck]['w'] for a, b in zip(xs, xs[1:])]
    R['ports'] = ports
    masts = {}
    for k, mm in Y.masts.items():
        top = mm['stages'][-1][2]
        zd = float(L.gun_z(mm['x0']))
        masts[k] = {'heel_z': mm['z0'], 'top_z': top, 'truck_above_wl_m': round((top - wl) * m, 2), 'truck_above_deck_m': round((top - zd) * m, 2),
                    'x_at_deck': round(float(Y.mast_x(k, zd)), 1), 'stages': [(s[0], s[1], s[2]) for s in mm['stages']]}
    R['masts'] = masts
    bx, bz = Y.bow_point(1.0)
    jx, jz = Y.jib_point(1.0)
    R['bowsprit_tip'] = [round(bx, 1), round(bz, 1)]
    R['jibboom_tip'] = [round(jx, 1), round(jz, 1)]
    xs_head = float(L.x_stem(L.st_b))
    R['bowsprit_z_over_stem_head'] = round(float(Y.bow['p0'][1] + (xs_head - Y.bow['p0'][0]) * math.tan(math.radians(plan['masts']['bowsprit']['steeve_deg']))), 1)
    R['stem_head'] = [round(xs_head, 1), L.st_b]
    Yd = Y.yards()
    R['yards'] = {k: {kk: (round(v, 1) if isinstance(v, float) else v) for kk, v in y.items()} for k, y in Yd.items()}
    R['sail_area_m2'] = round(Y.sail_area_m2(), 1)
    SS = Y.sails()
    R['sails'] = {k: (round(s['z_head'] - s['z_foot'], 1) if s['kind'] == 'square' else [tuple(round(c, 1) for c in p) for p in s['pts']]) for k, s in SS.items()}
    R['fore_course_foot_above_rail'] = round(SS['fore-course']['z_foot'] - float(L.top_z(SS['fore-course']['x'])), 1)
    # 帆杆：每一欄離舷頂（後甲板 taffrail）多高、尖伸出船尾板多少
    b = Yd['main_boom']
    xs = np.linspace(b['end'][0], b['x'], 40)
    zb = b['z'] + (b['x'] - xs) * math.tan(math.radians(b['angle_deg']))
    clear = zb - L.top_z(xs)
    R['boom_min_clear_over_rail'] = round(float(clear.min()), 1)
    R['boom_over_qd_deck_min'] = round(float((zb - L.deck_z('qd', xs))[(xs >= plan['decks']['qd']['x0']) & (xs <= plan['decks']['qd']['x1'])].min()), 1)
    R['boom_end_past_stern'] = round(float(L.x_aft(L.top_z(b['end'][0]))) - b['end'][0], 1)
    if R['boom_min_clear_over_rail'] < 4:
        bad.append('主帆杆離舷頂最少 %.1f 格' % R['boom_min_clear_over_rail'])
    # 框：x 範圍、方帆桁半長 vs 中線到框邊
    W = plan['space']
    R['x_extent'] = [round(min(b['end'][0], float(L.x_aft(60))), 1), round(jx, 1)]
    if R['x_extent'][0] < 1 or R['x_extent'][1] > W['x'] - 2:
        bad.append('x 範圍 %s 超出框 0..%d' % (R['x_extent'], W['x']))
    longest = max(y['len'] for y in Yd.values() if y['kind'] == 'square')
    R['longest_square_yard'] = longest
    if longest / 2 > W['yc'] - 2:
        bad.append('最長的方帆桁 %d 格、半長超過中線到框邊 %d' % (longest, W['yc']))
    R['problems'] = bad
    return R


def draw(plan, L, Y, S, x0, ylo, R, path):
    sc = 2.0
    nx, ny, nz = S.shape
    ZMAX = 320
    XMIN, XMAX = 20, 430
    padL, padT = 50, 80
    W = int((XMAX - XMIN) * sc) + padL * 2 + 120
    side_h = int(ZMAX * sc)
    top_h = int(200 * sc)
    H = padT + side_h + 60 + top_h + 330
    im = Image.new('RGB', (W, H), (250, 248, 240))
    d = ImageDraw.Draw(im)
    f12, f14, f20 = font(12), font(14), font(22)
    d.text((padL, 18), plan['title'].replace('新圖紙', '新圖紙 02 總佈置') + '　v1', fill=(20, 20, 20), font=f20)
    d.text((padL, 48), '0.1 m／格；帆圖照慣例把方帆攤平畫（帆桁正橫時從側面看不到帆面）；出處見 plan.json 的 src', fill=(60, 60, 60), font=f14)
    X = lambda x: padL + (x - XMIN) * sc
    Zs = lambda z: padT + (ZMAX - z) * sc
    SS = Y.sails()
    for n, s in SS.items():
        if s['kind'] == 'square':
            x, zh, zf, wh, wf = s['x'], s['z_head'], s['z_foot'], s['w_head'], s['w_foot']
            poly = [(X(x - wh / 2), Zs(zh)), (X(x + wh / 2), Zs(zh)), (X(x + wf / 2), Zs(zf)), (X(x - wf / 2), Zs(zf))]
        else:
            poly = [(X(p[0]), Zs(p[1])) for p in s['pts']]
        d.polygon(poly, fill=(236, 230, 210), outline=(170, 160, 130))
    for xi in range(nx):
        zz = np.nonzero(S[xi].any(axis=0))[0]
        if len(zz):
            d.line([X(xi + x0), Zs(zz[0]), X(xi + x0), Zs(zz[-1])], fill=(176, 142, 92), width=int(sc))
    wl = plan['waterline']['z']
    d.line([X(XMIN), Zs(wl), X(XMAX), Zs(wl)], fill=(0, 90, 200))
    d.text((X(XMAX) + 4, Zs(wl) - 8), 'WL %d' % wl, fill=(0, 90, 200), font=f12)
    cols = {'gun': (180, 0, 0), 'qd': (200, 90, 0), 'fc': (0, 120, 0)}
    D = plan['decks']
    for k in ('gun', 'qd', 'fc'):
        xa, xb = (48, 290) if k == 'gun' else (D[k]['x0'], D[k]['x1'])
        pts = [(X(x), Zs(float(L.deck_z(k, x)))) for x in range(int(xa), int(xb) + 1, 2)]
        d.line(pts, fill=cols[k], width=2)
    for p in Y.ports():
        d.rectangle([X(p['x'] - p['w'] / 2), Zs(p['sill'] + p['h']), X(p['x'] + p['w'] / 2), Zs(p['sill'])], fill=(150, 20, 20))
    for k, m in Y.masts.items():
        for nm, z0, z1, r in m['stages']:
            d.line([X(float(Y.mast_x(k, z0))), Zs(z0), X(float(Y.mast_x(k, z1))), Zs(z1)], fill=(110, 70, 30), width=max(2, int(r[0] * sc * 0.8)))
        for zt in (m['z_top'], m['z_tt']):
            xt = float(Y.mast_x(k, zt))
            d.line([X(xt - 8), Zs(zt), X(xt + 8), Zs(zt)], fill=(60, 40, 20), width=3)
    p0 = Y.bow['p0']
    p1 = Y.bow_point(1.0)
    d.line([X(p0[0]), Zs(p0[1]), X(p1[0]), Zs(p1[1])], fill=(110, 70, 30), width=5)
    j0, j1 = Y.jib_point(0.0), Y.jib_point(1.0)
    d.line([X(j0[0]), Zs(j0[1]) - 2, X(j1[0]), Zs(j1[1]) - 2], fill=(110, 70, 30), width=3)
    for k, y in Y.yards().items():
        if y['kind'] == 'square':
            d.line([X(y['x'] - 3), Zs(y['z']), X(y['x'] + 3), Zs(y['z'])], fill=(40, 20, 0), width=3)
        else:
            d.line([X(y['x']), Zs(y['z']), X(y['end'][0]), Zs(y['end'][1])], fill=(40, 20, 0), width=3)
    for x in range(50, XMAX + 1, 50):
        d.line([X(x), Zs(0), X(x), Zs(0) + 6], fill=(0, 0, 0))
        d.text((X(x) - 10, Zs(0) + 8), str(x), fill=(80, 80, 80), font=f12)
    for z in range(0, ZMAX + 1, 50):
        d.text((padL - 40, Zs(z) - 8), 'z%d' % z, fill=(120, 120, 120), font=f12)
    lg = ['紅 主甲板', '橙 後甲板', '綠 艏樓', '深紅方塊 炮門', '淡黃 帆（方帆攤平）']
    for i, t in enumerate(lg):
        d.text((X(XMAX) - 120, padT + 10 + 16 * i), t, fill=(60, 60, 60), font=f12)
    # ② 俯視
    oy = padT + side_h + 60
    d.text((padL, oy - 22), '② 俯視：主甲板那一層的外緣（z %d）、後甲板與艏樓的範圍、炮門、桅、帆桁長（正橫）' % plan['readings_at']['deck_z'], fill=(0, 0, 0), font=f14)
    cy = oy + top_h // 2
    Yv = lambda dy: cy - dy * sc
    zd = int(plan['readings_at']['deck_z']) + 4
    pts_p, pts_s = [], []
    for xi in range(nx):
        ys = np.nonzero(S[xi, :, zd])[0]
        if len(ys):
            pts_s.append((X(xi + x0), Yv(ys[-1] + ylo - L.YC)))
            pts_p.append((X(xi + x0), Yv(ys[0] + ylo - L.YC)))
    d.line(pts_s, fill=(0, 0, 0), width=2)
    d.line(pts_p, fill=(0, 0, 0), width=2)
    for k in ('qd', 'fc'):
        d.rectangle([X(D[k]['x0']), Yv(30), X(D[k]['x1']), Yv(-30)], outline=cols[k])
    for p in Y.ports():
        hb = float(L.hb(np.array([p['x'] + 0.5]), np.array([p['sill'] + 0.5]))[0])
        for sgn in (-1, 1):
            d.rectangle([X(p['x'] - p['w'] / 2), Yv(sgn * hb) - 3, X(p['x'] + p['w'] / 2), Yv(sgn * hb) + 3], fill=(150, 20, 20))
    for k, m in Y.masts.items():
        x = float(Y.mast_x(k, zd))
        r = m['stages'][0][3][0]
        d.ellipse([X(x - r), Yv(r), X(x + r), Yv(-r)], fill=(110, 70, 30))
        d.text((X(x) - 14, Yv(-62)), k, fill=(110, 70, 30), font=f12)
    for k, y in Y.yards().items():
        if y['kind'] == 'square':
            h = y['len'] / 2
            d.line([X(y['x']), Yv(h), X(y['x']), Yv(-h)], fill=(160, 140, 110), width=1)
        else:
            d.line([X(y['x']), cy, X(y['end'][0]), cy], fill=(160, 140, 110), width=2)
    d.line([X(p0[0]), cy, X(j1[0]), cy], fill=(110, 70, 30), width=4)
    d.line([X(XMIN), Yv(plan['space']['yc']), X(XMAX), Yv(plan['space']['yc'])], fill=(200, 200, 200))
    d.line([X(XMIN), Yv(-plan['space']['yc']), X(XMAX), Yv(-plan['space']['yc'])], fill=(200, 200, 200))
    # ③ 表
    oy3 = oy + top_h + 20
    m = plan['meters_per_cell']
    rows = [
        ('炮門下緣離水線', '、'.join('x %d %.2f m' % (r['x'], r['sill_above_wl_m']) for r in R['ports'])),
        ('炮門頂離舷頂', '、'.join('x %d %.1f 格' % (r['x'], r['margin']) for r in R['ports'])),
        ('桅頂離水線／甲板', '、'.join('%s %.1f／%.1f m' % (k, v['truck_above_wl_m'], v['truck_above_deck_m']) for k, v in R['masts'].items())),
        ('艏斜桅、三角帆桿', '跟艏柱頭 x %.0f 交會那裡 z %.1f（艏柱頭 z %d）；艏斜桅尖 (%.0f, %.0f)、三角帆桿尖 (%.0f, %.0f)' % (R['stem_head'][0], R['bowsprit_z_over_stem_head'], R['stem_head'][1], R['bowsprit_tip'][0], R['bowsprit_tip'][1], R['jibboom_tip'][0], R['jibboom_tip'][1])),
        ('主帆杆', '離舷頂最少 %.1f 格、離後甲板面最少 %.1f 格；尖伸出船尾 %.1f 格' % (R['boom_min_clear_over_rail'], R['boom_over_qd_deck_min'], R['boom_end_past_stern'])),
        ('帆面積（攤平）', '%.0f m²（%d 面）' % (R['sail_area_m2'], len(R['sails']))),
        ('前帆桁', '%.1f m（%.2f × 寬）；最長方帆桁 %d 格（框半寬 %d）' % (plan['masts']['yards']['fore_course']['len'] * m, plan['masts']['yards']['fore_course']['len'] / 69.0, R['longest_square_yard'], plan['space']['yc'])),
        ('問題', '；'.join(R['problems']) or '0'),
    ]
    for i, (k, v) in enumerate(rows):
        d.text((padL, oy3 + i * 24), k, fill=(40, 40, 40), font=f14)
        d.text((padL + 200, oy3 + i * 24), v, fill=(0, 0, 0), font=f14)
    im.save(path, optimize=False)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    if probe:
        deck, i, dv = probe[0].split('=', 1)[1].split(':')
        plan['ports'][deck]['x'][int(i)] += int(dv)
    L = HL.Lines(plan)
    Y = LY.Layout(plan, L)
    x0, ylo, S, dist = hull_volume(L, plan)
    R = readings(plan, L, Y, S, x0, ylo)
    if probe:
        print(json.dumps({'probe': probe[0], 'port_gaps_gun': R['port_gaps_gun']}, ensure_ascii=False))
        return
    draw(plan, L, Y, S, x0, ylo, R, os.path.join(design, 'sheet02_layout_v1.png'))
    with open(os.path.join(design, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('ports', 'yards', 'sails')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
