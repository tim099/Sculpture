# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/draft_layout.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 新圖紙 02（TASK-0606）：甲板、砲門三層、桅與帆桁、煙囪、螺旋槳 ⇒ sheet02_layout_v1.png、verify_layout.json
#   抄自三叉戟號 gura-tridente-01m/design/draft_layout.py（gura，TASK-0554）；改：煙囪／螺旋槳的檢查與畫法、白帶、帆的外框、俯視圖。
#   用法：python -I -X utf8 draft_layout.py <design 資料夾> [--probe port=<層>:<序號>:<dx>]
#   · 只讀 plan.json、不碰作品。船殼照 draft_lines.hull_volume 算（同一支）⇒ 砲門「在不在船側」拿真的牆來量。
#   · --probe：反向對照（把某一個砲門往 x 推 dx 格重量，⛔ 不寫圖與讀數檔）。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb


def check(plan, L, S, wall, x0, ylo, P, M):
    YC = L.YC
    R = {'ports': {}, 'problems': []}
    tiers = [t['deck'] for t in plan['ports']['tiers']]
    by = {k: [p for p in P if p['deck'] == k] for k in tiers}
    for k in tiers:
        ps = by[k]
        gaps = [ps[i + 1]['x0'] - ps[i]['x1'] - 1 for i in range(len(ps) - 1)]
        bulge = []
        for p in ps:
            hbs = []
            for x in (p['x0'], p['x1']):
                for z in (p['z0'], p['z1']):
                    col = S[x - x0, :, z]
                    ys = np.nonzero(col)[0]
                    hbs.append(int(ys[-1] + ylo - YC) if len(ys) else -1)
            bulge.append(max(hbs) - min(hbs))
            if min(hbs) < 0:
                R['problems'].append('%s 第 %d 個：有一角不在船上' % (k, p['i']))
            # 牆在不在：右舷外緣往裡 wall 格都是牆
        R['ports'][k] = {'per_side': len(ps), 'min_gap': int(min(gaps)) if gaps else None, 'max_gap': int(max(gaps)) if gaps else None,
                         'max_surface_step': int(max(bulge)), 'x_first': ps[0]['x0'], 'x_last': ps[-1]['x1'],
                         'z_sill_range': [min(p['z0'] for p in ps), max(p['z0'] for p in ps)]}
        if gaps and min(gaps) < 14:
            R['problems'].append('%s：砲門間距 %d < 14（砲架擺不下）' % (k, min(gaps)))
    # 層與層之間：上一層的下緣離下一層的上緣（同 x 重疊的那幾對）
    vg = []
    for a, b in zip(tiers, tiers[1:]):
        m = 999
        for p in by[a]:
            for q in by[b]:
                if q['x0'] <= p['x1'] and p['x0'] <= q['x1']:
                    m = min(m, q['z0'] - p['z1'] - 1)
        vg.append({'between': [a, b], 'min_clear': int(m)})
        if m < 5:
            R['problems'].append('%s→%s 砲門上下只隔 %d 格' % (a, b, m))
    R['vertical_clear'] = vg
    # 砲門上緣要在上一層甲板下面
    for t in plan['ports']['tiers']:
        rows = [r['key'] for r in plan['decks']['rows']]
        i = rows.index(t['deck'])
        if i + 1 < len(rows) and plan['decks']['rows'][i + 1]['key'] != 'poop':
            nk = rows[i + 1]
            worst = min(int(LY.deck_z(plan, nk, (p['x0'] + p['x1']) / 2)) - p['z1'] for p in by[t['deck']])
            R['ports'][t['deck']]['below_next_deck_min'] = worst
            if worst < 3:
                R['problems'].append('%s 的砲門上緣離上一層甲板只剩 %d' % (t['deck'], worst))
    # 甲板：在船裡（那一層的內寬）
    dk = {}
    for r in plan['decks']['rows']:
        xs = np.arange(x0 + 5, x0 + S.shape[0] - 5)
        zs = LY.deck_z(plan, r['key'], xs).astype(int)
        inner = []
        for x, z in zip(xs, zs):
            if z >= S.shape[2]:
                continue
            col = S[x - x0, :, z]
            ys = np.nonzero(col)[0]
            if len(ys):
                inner.append((int(x), int(ys[-1] + ylo - YC) - int(plan['hull_build']['wall'])))
        span = [x for x, w in inner if w > 6]
        dk[r['key']] = {'z_mid': r['z'], 'z_ends': [int(zs[0]), int(zs[-1])], 'inside_x': [min(span), max(span)] if span else None}
    R['decks'] = dk
    # 桅：在船裡、頂在空間裡、帆桁半長在 y 框裡
    mm = []
    for m in M:
        zs = m['heel']
        top_ok = m['truck'] < plan['space']['z']
        half = max(v for v in m['yard_len'].values()) / 2.0
        mm.append({'key': m['key'], 'x': m['x'], 'heel': m['heel'], 'platform': m['platform'], 'crosstrees': m['crosstrees'], 'truck': m['truck'],
                   'truck_above_wl_m': round((m['truck'] - plan['waterline']['z']) * 0.1, 2), 'max_yard_half': half,
                   'yard_in_frame': bool(YC + half < plan['space']['y'] and YC - half > 0)})
        if not top_ok:
            R['problems'].append('%s 桅頂 z %d 超出空間' % (m['key'], m['truck']))
    R['masts'] = mm
    R['guns_broadside'] = sum(t['per_side'] * 2 for t in plan['ports']['tiers'])
    R['guns_total'] = R['guns_broadside'] + plan['ports']['chase']['bow'] + plan['ports']['chase']['stern']
    return R


def check_steam(plan, L, S, x0, ylo, M, R):
    """煙囪與螺旋槳：煙囪在船裡（上甲板那一層的內寬夠）、離桅夠遠、頂低於最低的方帆桁；螺旋槳整個在 aperture 裡。"""
    YC = L.YC
    zs = next(r['z'] for r in plan['decks']['rows'] if r['key'] == 'spar')
    out = []
    low_yard = min(min(v for k, v in m['yard_z'].items() if k in ('course', 'crossjack')) for m in M)
    for f in plan['funnels']['rows']:
        col = S[f['x'] - x0, :, zs]
        ys = np.nonzero(col)[0]
        inner = int(ys[-1] + ylo - YC) - int(plan['hull_build']['wall']) if len(ys) else -1
        near = min(abs(f['x'] - LY.mast_axis_x(plan, m['key'], zs)) for m in M)
        row = {'key': f['key'], 'x': f['x'], 'r': f['r'], 'deck_inner_half': inner, 'nearest_mast_dx': round(float(near), 1),
               'top_z': f['top_z'], 'top_above_wl_m': round((f['top_z'] - plan['waterline']['z']) * 0.1, 2), 'clear_to_lowest_course_yard': int(low_yard - f['top_z'])}
        out.append(row)
        if inner < f['r'] + 4:
            R['problems'].append('煙囪 %s 在上甲板放不下' % f['key'])
        if near < f['r'] + 8:
            R['problems'].append('煙囪 %s 離桅太近（%.1f）' % (f['key'], near))
        if low_yard - f['top_z'] < 20:
            R['problems'].append('煙囪 %s 頂離最低的方帆桁不到 20 格' % f['key'])
    R['funnels'] = out
    pr = plan['propeller']
    ap = plan['aperture']
    z0, z1 = pr['hub_z'] - pr['diameter'] / 2.0, pr['hub_z'] + pr['diameter'] / 2.0
    xa_lo = float(L.x_post(z1)) + ap['x_aft_off']
    xa_hi = float(L.x_post(z0)) + ap['x_aft_off'] + ap['len']
    R['propeller'] = {'x': pr['x'], 'hub_z': pr['hub_z'], 'diameter': pr['diameter'], 'blades': pr['blades'],
                      'aperture_z': [ap['z0'], ap['z1']], 'aperture_x_at_hub': [round(float(L.x_post(pr['hub_z'])) + ap['x_aft_off'], 1), round(float(L.x_post(pr['hub_z'])) + ap['x_aft_off'] + ap['len'], 1)],
                      'margin_z': [round(z0 - ap['z0'], 1), round(ap['z1'] - z1, 1)], 'margin_x': [round(pr['x'] - 3 - xa_lo, 1), round(xa_hi - pr['x'] - 3, 1)]}
    if z0 < ap['z0'] or z1 > ap['z1'] or pr['x'] - 3 < xa_lo or pr['x'] + 3 > xa_hi:
        R['problems'].append('螺旋槳超出 aperture')
    if z0 < 3:
        R['problems'].append('螺旋槳低於龍骨')


def draw(plan, L, S, wall, col, x0, ylo, P, M, R, path):
    sc = 1.2
    nx, ny, nz = S.shape
    zmax_draw = max(m['truck'] for m in M) + 20
    zs_spar = next(r['z'] for r in plan['decks']['rows'] if r['key'] == 'spar')
    padL, padT = 60, 90
    side_w = int((nx + 360) * sc)
    Wp = side_w + padL * 2 + 470
    plan_h = int(ny * sc * 0.5) + 40
    Hp = padT + int(zmax_draw * sc) + 60 + plan_h + 470
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    f12, f14, f20 = font(12), font(14), font(22)
    pp = plan['paint']
    d.text((padL, 20), '蘇士奎哈納號（Gloire，1859）新圖紙 02：側面、甲板、砲門、桅帆、煙囪與螺旋槳　v1', fill=(20, 20, 20), font=f20)
    d.text((padL, 52), '0.1 m／格　側面從右舷看（船頭在右）；砲門每舷 %s ＝ %d 門　參考：NARA 1862 造船圖（78116333）、1863／1869 照片、Musée 模型 —— 重畫，不描圖' % (
        '／'.join(str(t['per_side']) for t in plan['ports']['tiers']), R['guns_total']), fill=(60, 60, 60), font=f14)
    oy = padT

    def X(x):
        return padL + (x - x0 + 80) * sc

    def Z(z):
        return oy + (zmax_draw - z) * sc

    def mx(m, z):
        return m['x'] - (z - zs_spar) * math.tan(math.radians(m['rake']))
    # 帆的外框（淡，畫在最底下）：方帆 ＝ 這一根帆桁到下一根（或甲板上方）之間的梯形
    for m in M:
        ks = [k for k in ('course', 'crossjack', 'topsail', 'topgallant', 'royal') if k in m['yard_z']]
        for i, k in enumerate(ks):
            if k == 'crossjack':
                continue
            zt = m['yard_z'][k]
            zb = m['yard_z'][ks[i - 1]] if i > 0 else zs_spar + 30
            wt, wb = m['yard_len'][k] / 2.0 * 0.22, (m['yard_len'][ks[i - 1]] if i > 0 else m['yard_len'][k] * 1.05) / 2.0 * 0.22
            d.polygon([(X(mx(m, zt) - wt), Z(zt)), (X(mx(m, zt) + wt), Z(zt)), (X(mx(m, zb) + wb), Z(zb)), (X(mx(m, zb) - wb), Z(zb))], fill=(236, 230, 214), outline=(200, 190, 170))
        if 'gaff' in m['yard_z']:
            zg, zb = m['yard_z']['gaff'], m['yard_z']['boom']
            xg = mx(m, zg)
            d.polygon([(X(xg), Z(zg)), (X(xg - m['yard_len']['gaff'] * 0.85), Z(zg + 40)), (X(mx(m, zb) - m['yard_len']['boom']), Z(zb)), (X(mx(m, zb)), Z(zb))], fill=(236, 230, 214), outline=(200, 190, 170))
    # 船殼剪影（右舷外板色）＋ 白帶
    for xi in range(nx):
        for z in np.nonzero(wall[xi].any(axis=0))[0]:
            ys = np.nonzero(wall[xi, :, z])[0]
            c = palette_rgb(int(col[xi, ys[-1], z]))
            d.rectangle([X(xi + x0), Z(z + 1), X(xi + x0 + 1), Z(z)], fill=c)
    for t in plan['ports']['tiers']:
        if t['deck'] not in pp.get('banded', []):        # 蘇士奎哈納號改：只畫有帶的層（蘇士奎哈納號沒有白帶）
            continue
        ps = [p for p in P if p['deck'] == t['deck']]
        xs = np.arange(ps[0]['x0'] - 14, ps[-1]['x1'] + 15)
        for x in xs:
            zc = float(LY.deck_z(plan, t['deck'], x))
            zb0, zb1 = int(zc) + t['sill'] - 2, int(zc) + t['sill'] + t['h'] + 1
            d.rectangle([X(x), Z(zb1 + 1), X(x + 1), Z(zb0)], fill=palette_rgb(pp['band']))
    for p in P:
        d.rectangle([X(p['x0']), Z(p['z1'] + 1), X(p['x1'] + 1), Z(p['z0'])], fill=(30, 30, 30), outline=(120, 120, 120))
    # 甲板線
    xs = np.arange(x0 + 8, x0 + nx - 8)
    for r in plan['decks']['rows']:
        zs = LY.deck_z(plan, r['key'], xs)
        m_ = (xs >= r.get('x_from', -1e9)) & (xs <= r.get('x_to', 1e9))
        for a, b in r.get('skip', []):
            m_ &= ~((xs >= a) & (xs <= b))
        pts = [(X(x), Z(z + 1)) for x, z, k in zip(xs, zs, m_) if k]
        for i in range(0, len(pts) - 1, 6):
            if abs(pts[min(i + 3, len(pts) - 1)][0] - pts[i][0]) < 6 * sc:
                d.line([pts[i], pts[min(i + 3, len(pts) - 1)]], fill=(0, 140, 200), width=1)
        d.text((X(x0 + nx) + 6, Z(r['z'] + 1) - 8), '%s z %d' % (r['name'].split('（')[0], r['z']), fill=(0, 110, 170), font=f12)
    d.line([X(x0 - 40), Z(plan['waterline']['z']), X(x0 + nx), Z(plan['waterline']['z'])], fill=(0, 70, 200))
    d.text((X(x0 + nx) + 6, Z(plan['waterline']['z']) - 2), 'WL %d' % plan['waterline']['z'], fill=(0, 70, 200), font=f12)
    # 螺旋槳（側面看是一根細長的葉片）＋ 舵（艉柱後面、到舷頂下）
    pr = plan['propeller']
    d.rectangle([X(pr['x'] - 3), Z(pr['hub_z'] + pr['diameter'] / 2.0), X(pr['x'] + 3), Z(pr['hub_z'] - pr['diameter'] / 2.0)], fill=(176, 141, 60), outline=(90, 70, 20))
    d.ellipse([X(pr['x'] - 4), Z(pr['hub_z'] + 4), X(pr['x'] + 4), Z(pr['hub_z'] - 4)], fill=(90, 70, 20))
    zr = np.arange(3, 112)
    xr = L.x_post(zr)
    d.polygon([(X(xr[0] - 0), Z(3)), (X(xr[-1]), Z(112)), (X(xr[-1] - 12), Z(112)), (X(xr[0] - 14), Z(3))], fill=(70, 50, 30), outline=(30, 20, 10))
    # 煙囪
    for f in plan['funnels']['rows']:
        d.rectangle([X(f['x'] - f['r']), Z(f['top_z']), X(f['x'] + f['r'] + 1), Z(zs_spar)], fill=palette_rgb(plan['funnels']['color']), outline=(80, 80, 80))
        d.text((X(f['x'] - f['r']), Z(f['top_z']) - 18), '煙囪 %s' % f['key'], fill=(40, 40, 40), font=f12)
    # 桅（側面：直線＋平台／crosstrees 橫線；帆桁在側面是點 ⇒ 畫小短線）
    for m in M:
        d.line([X(mx(m, m['heel'])), Z(m['heel']), X(mx(m, m['truck'])), Z(m['truck'])], fill=(110, 70, 30), width=3)
        for zz, w in ((m['platform'], 30), (m['crosstrees'], 16)):
            d.line([X(mx(m, zz) - w), Z(zz), X(mx(m, zz) + w), Z(zz)], fill=(110, 70, 30), width=3)
        for k, zz in m['yard_z'].items():
            if k in ('gaff', 'boom'):
                L1 = m['yard_len'][k]
                d.line([X(mx(m, zz)), Z(zz), X(mx(m, zz) - L1), Z(zz + (40 if k == 'gaff' else 0))], fill=(40, 40, 40), width=3)
            else:
                d.line([X(mx(m, zz) - 4), Z(zz), X(mx(m, zz) + 4), Z(zz)], fill=(40, 40, 40), width=3)
            d.text((X(mx(m, zz)) + 8, Z(zz) - 7), k, fill=(60, 60, 60), font=f12)
        d.text((X(mx(m, m['truck'])) - 14, Z(m['truck']) - 18), m['key'], fill=(110, 70, 30), font=f14)
    bs = plan['masts']['bowsprit']
    a = math.radians(bs['angle_deg'])
    L1 = bs['length'] + bs['jibboom'] * 0.75
    d.line([X(bs['heel_x']), Z(bs['heel_z']), X(bs['heel_x'] + L1 * math.cos(a)), Z(bs['heel_z'] + L1 * math.sin(a))], fill=(110, 70, 30), width=3)
    for x in range((x0 // 50 + 1) * 50, x0 + nx + 300, 50):
        d.line([X(x), Z(0) + 4, X(x), Z(0) + 10], fill=(0, 0, 0))
        d.text((X(x) - 10, Z(0) + 12), str(x), fill=(80, 80, 80), font=f12)
    # 正面（從船頭看）：船中剖面＋主桅帆桁的跨度＋煙囪
    fx0 = padL + side_w + 40
    fcx = fx0 + 210
    fs = 1.0
    xi = 470 - x0
    for z in range(nz):
        ys = np.nonzero(S[xi, :, z])[0]
        if len(ys):
            h = ys[-1] + ylo - L.YC
            d.line([fcx - h * fs, Z(z), fcx + h * fs, Z(z)], fill=(40, 40, 40))
    for f in plan['funnels']['rows'][:1]:
        d.rectangle([fcx - f['r'] * fs, Z(f['top_z']), fcx + f['r'] * fs, Z(zs_spar)], fill=(60, 60, 60))
    for m in M:
        if m['key'] != 'main':
            continue
        d.line([fcx, Z(m['heel']), fcx, Z(m['truck'])], fill=(110, 70, 30), width=3)
        for k, zz in m['yard_z'].items():
            hl = m['yard_len'][k] / 2.0
            d.line([fcx - hl * fs, Z(zz), fcx + hl * fs, Z(zz)], fill=(40, 40, 40), width=2)
            d.text((fcx + hl * fs + 4, Z(zz) - 7), '%s %.1f m' % (k, m['yard_len'][k] / 10.0), fill=(60, 60, 60), font=f12)
    d.text((fx0, oy - 20), '正面（主桅；空間寬 %d 格）' % plan['space']['y'], fill=(0, 0, 0), font=f14)
    d.rectangle([fcx - L.YC * fs, oy, fcx + (plan['space']['y'] - L.YC) * fs, oy + zmax_draw * sc], outline=(180, 180, 180))
    # 俯視：上甲板那一層的外緣、桅、煙囪、艏斜桅
    oyp = oy + int(zmax_draw * sc) + 60
    d.text((padL, oyp - 20), '俯視（上甲板 z %d 的外緣；桅 ●、煙囪 ◯）' % zs_spar, fill=(0, 0, 0), font=f14)
    cyp = oyp + plan_h / 2.0

    def Yp(dy):
        return cyp + dy * sc * 0.5 * 1.6
    pts_u, pts_d = [], []
    for xi in range(nx):
        ys = np.nonzero(S[xi, :, min(zs_spar, nz - 1)])[0]
        if len(ys):
            h = ys[-1] + ylo - L.YC
            pts_u.append((X(xi + x0), Yp(-h)))
            pts_d.append((X(xi + x0), Yp(h)))
    if pts_u:
        d.polygon(pts_u + pts_d[::-1], fill=(222, 205, 160), outline=(40, 40, 40))
    for m in M:
        xm_ = mx(m, zs_spar)
        d.ellipse([X(xm_ - 5), Yp(-5), X(xm_ + 5), Yp(5)], fill=(110, 70, 30))
    for f in plan['funnels']['rows']:
        d.ellipse([X(f['x'] - f['r']), Yp(-f['r']), X(f['x'] + f['r']), Yp(f['r'])], fill=(40, 40, 40))
    d.line([X(bs['heel_x']), Yp(0), X(bs['heel_x'] + L1 * math.cos(a)), Yp(0)], fill=(110, 70, 30), width=3)
    # 表
    ty = oyp + plan_h + 20
    d.text((padL, ty), '砲門（每舷）', fill=(0, 0, 0), font=f14)
    for i, t in enumerate(plan['ports']['tiers']):
        rr = R['ports'][t['deck']]
        d.text((padL, ty + 24 + i * 20), '%s：%d 個　%d×%d 格　下緣離甲板 %d　間距 %s–%s　x %d–%d　%s' % (
            t['deck'], t['per_side'], t['w'], t['h'], t['sill'], rr['min_gap'], rr['max_gap'], rr['x_first'], rr['x_last'], t['gun']), fill=(40, 40, 40), font=f12)
    ty2 = ty + 24 + len(plan['ports']['tiers']) * 20 + 16
    d.text((padL, ty2), '桅（z ＝ 格；桅頂離水線）', fill=(0, 0, 0), font=f14)
    for i, m in enumerate(R['masts']):
        d.text((padL, ty2 + 24 + i * 20), '%s：x %d　桅腳 %d　平台 %d　crosstrees %d　桅頂 %d（%.1f m）　最長帆桁半長 %.1f 格' % (
            m['key'], m['x'], m['heel'], m['platform'], m['crosstrees'], m['truck'], m['truck_above_wl_m'], m['max_yard_half']), fill=(40, 40, 40), font=f12)
    ty3 = ty2 + 24 + 3 * 20 + 16
    d.text((padL, ty3), '蒸汽機外觀', fill=(0, 0, 0), font=f14)
    for i, f in enumerate(R['funnels']):
        d.text((padL, ty3 + 24 + i * 20), '煙囪 %s：x %d　半徑 %d　頂 z %d（離水線 %.1f m）　離最近的桅 %.1f 格　離最低的方帆桁 %d 格' % (
            f['key'], f['x'], f['r'], f['top_z'], f['top_above_wl_m'], f['nearest_mast_dx'], f['clear_to_lowest_course_yard']), fill=(40, 40, 40), font=f12)
    pr_ = R['propeller']
    d.text((padL, ty3 + 24 + 2 * 20), '螺旋槳：%d 葉、直徑 %d 格、軸心 (x %d, z %d)；aperture z %d–%d，上下餘裕 %s、前後餘裕 %s' % (
        pr_['blades'], pr_['diameter'], pr_['x'], pr_['hub_z'], pr_['aperture_z'][0], pr_['aperture_z'][1], pr_['margin_z'], pr_['margin_x']), fill=(40, 40, 40), font=f12)
    ty4 = ty3 + 24 + 3 * 20 + 16
    d.text((padL, ty4), '檢查：' + ('全部通過' if not R['problems'] else '；'.join(R['problems'])), fill=(0, 120, 0) if not R['problems'] else (190, 0, 0), font=f14)
    d.text((padL, ty4 + 24), '出處：plan.json（decks／ports／masts／funnels／propeller 的 src）與 references/research_*.md', fill=(90, 90, 90), font=f12)
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col, _armor = shell_colors(plan, S, dist, x0, ylo)
    P = LY.ports(plan)
    if probe:
        _, spec = probe[0].split('=')
        k, i, dx = spec.split(':')
        for p in P:
            if p['deck'] == k and p['i'] == int(i):
                p['x0'] += int(dx)
                p['x1'] += int(dx)
    M = LY.mast_spars(plan)
    R = check(plan, L, S, wall, x0, ylo, P, M)
    check_steam(plan, L, S, x0, ylo, M, R)
    if probe:
        print(json.dumps({'probe': probe[0], 'ports': R['ports'], 'funnels': R['funnels'], 'problems': R['problems']}, ensure_ascii=False))
        return
    R['port_list'] = P
    draw(plan, L, S, wall, col, x0, ylo, P, M, R, os.path.join(design, 'sheet02_layout_v1.png'))
    with open(os.path.join(design, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'port_list'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
