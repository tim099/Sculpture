# 三叉戟號 新圖紙 02（TASK-0554）：甲板、砲門四層、桅與帆桁 ⇒ sheet02_layout_v1.png、verify_layout.json
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
        if min(gaps) < 14:
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


def draw(plan, L, S, wall, col, x0, ylo, P, M, R, path):
    sc = 1.2
    nx, ny, nz = S.shape
    zmax_draw = max(m['truck'] for m in M) + 20
    padL, padT = 60, 90
    side_w = int((nx + 300) * sc)
    Wp = side_w + padL * 2 + 420
    Hp = padT + int(zmax_draw * sc) + 520
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    f12, f14, f20 = font(12), font(14), font(22)
    d.text((padL, 20), '三叉戟號（Tridente）新圖紙 02：甲板、砲門四層、桅與帆桁　v1', fill=(20, 20, 20), font=f20)
    d.text((padL, 52), '0.1 m／格　側面從右舷看（船頭在右）；砲門每舷 %s ＝ 舷側 %d ＋ 追擊 %d ＝ %d 門' % (
        '／'.join(str(t['per_side']) for t in plan['ports']['tiers']), R['guns_broadside'],
        plan['ports']['chase']['bow'] + plan['ports']['chase']['stern'], R['guns_total']), fill=(60, 60, 60), font=f14)
    oy = padT
    def X(x):
        return padL + (x - x0 + 60) * sc
    def Z(z):
        return oy + (zmax_draw - z) * sc
    # 船殼剪影（右舷外板色）
    for xi in range(nx):
        for z in np.nonzero(wall[xi].any(axis=0))[0]:
            ys = np.nonzero(wall[xi, :, z])[0]
            c = palette_rgb(int(col[xi, ys[-1], z]))
            d.rectangle([X(xi + x0), Z(z + 1), X(xi + x0 + 1), Z(z)], fill=c)
    # 砲門
    tint = {'lower': (255, 255, 255), 'middle': (255, 255, 255), 'upper': (255, 255, 255), 'spar': (255, 255, 255)}
    for p in P:
        d.rectangle([X(p['x0']), Z(p['z1'] + 1), X(p['x1'] + 1), Z(p['z0'])], fill=(205, 60, 40), outline=tint[p['deck']])
    # 甲板線
    xs = np.arange(x0 + 8, x0 + nx - 8)
    for r in plan['decks']['rows']:
        zs = LY.deck_z(plan, r['key'], xs)
        if r.get('x_to'):
            m = xs <= r['x_to']
        else:
            m = np.ones_like(xs, bool)
        pts = [(X(x), Z(z + 1)) for x, z, k in zip(xs, zs, m) if k]
        for i in range(0, len(pts) - 1, 6):
            d.line([pts[i], pts[min(i + 3, len(pts) - 1)]], fill=(0, 140, 200), width=1)
        d.text((X(x0 + nx) + 6, Z(r['z'] + 1) - 8), '%s z %d' % (r['name'].split('（')[0], r['z']), fill=(0, 110, 170), font=f12)
    d.line([X(x0), Z(plan['waterline']['z']), X(x0 + nx), Z(plan['waterline']['z'])], fill=(0, 70, 200))
    d.text((X(x0 + nx) + 6, Z(plan['waterline']['z']) - 2), 'WL %d' % plan['waterline']['z'], fill=(0, 70, 200), font=f12)
    # 桅（側面：直線＋平台／crosstrees 橫線；帆桁在側面是點 ⇒ 畫小短線）
    for m in M:
        r = math.tan(math.radians(m['rake']))
        def mx(z):
            return m['x'] - (z - 158) * r
        d.line([X(mx(m['heel'])), Z(m['heel']), X(mx(m['truck'])), Z(m['truck'])], fill=(110, 70, 30), width=3)
        for zz, w in ((m['platform'], 30), (m['crosstrees'], 16)):
            d.line([X(mx(zz) - w), Z(zz), X(mx(zz) + w), Z(zz)], fill=(110, 70, 30), width=3)
        for k, zz in m['yard_z'].items():
            d.line([X(mx(zz) - 4), Z(zz), X(mx(zz) + 4), Z(zz)], fill=(40, 40, 40), width=3)
            d.text((X(mx(zz)) + 8, Z(zz) - 7), k, fill=(60, 60, 60), font=f12)
        d.text((X(mx(m['truck'])) - 14, Z(m['truck']) - 18), m['key'], fill=(110, 70, 30), font=f14)
    bs = plan['masts']['bowsprit']
    a = math.radians(bs['angle_deg'])
    L1 = bs['length'] + bs['jibboom'] * 0.75
    d.line([X(bs['heel_x']), Z(bs['heel_z']), X(bs['heel_x'] + L1 * math.cos(a)), Z(bs['heel_z'] + L1 * math.sin(a))], fill=(110, 70, 30), width=3)
    # 正面（從船頭看）：船中剖面＋主桅帆桁的跨度
    fx0 = padL + side_w + 40
    fcx = fx0 + 180
    fs = 1.0
    xi = 430 - x0
    for z in range(nz):
        ys = np.nonzero(S[xi, :, z])[0]
        if len(ys):
            h = ys[-1] + ylo - L.YC
            d.line([fcx - h * fs, oy + (zmax_draw - z) * sc, fcx + h * fs, oy + (zmax_draw - z) * sc], fill=(40, 40, 40))
    for m in M:
        if m['key'] != 'main':
            continue
        d.line([fcx, oy + (zmax_draw - m['heel']) * sc, fcx, oy + (zmax_draw - m['truck']) * sc], fill=(110, 70, 30), width=3)
        for k, zz in m['yard_z'].items():
            hl = m['yard_len'][k] / 2.0
            d.line([fcx - hl * fs, oy + (zmax_draw - zz) * sc, fcx + hl * fs, oy + (zmax_draw - zz) * sc], fill=(40, 40, 40), width=2)
            d.text((fcx + hl * fs + 4, oy + (zmax_draw - zz) * sc - 7), '%s %.1f m' % (k, m['yard_len'][k] / 10.0), fill=(60, 60, 60), font=f12)
    d.text((fx0, oy - 20), '正面（主桅；空間寬 %d 格）' % plan['space']['y'], fill=(0, 0, 0), font=f14)
    d.rectangle([fcx - L.YC * fs, oy, fcx + (plan['space']['y'] - L.YC) * fs, oy + zmax_draw * sc], outline=(180, 180, 180))
    # 表
    ty = oy + int(zmax_draw * sc) + 20
    d.text((padL, ty), '砲門（每舷）', fill=(0, 0, 0), font=f14)
    for i, t in enumerate(plan['ports']['tiers']):
        rr = R['ports'][t['deck']]
        d.text((padL, ty + 24 + i * 20), '%s：%d 個　%d×%d 格　下緣離甲板 %d　間距 %d–%d　x %d–%d　%s' % (
            t['deck'], t['per_side'], t['w'], t['h'], t['sill'], rr['min_gap'], rr['max_gap'], rr['x_first'], rr['x_last'], t['gun']), fill=(40, 40, 40), font=f12)
    ty2 = ty + 24 + 4 * 20 + 16
    d.text((padL, ty2), '桅（z ＝ 格；桅頂離水線）', fill=(0, 0, 0), font=f14)
    for i, m in enumerate(R['masts']):
        d.text((padL, ty2 + 24 + i * 20), '%s：x %d　桅腳 %d　平台 %d　crosstrees %d　桅頂 %d（%.1f m）　最長帆桁半長 %.1f 格' % (
            m['key'], m['x'], m['heel'], m['platform'], m['crosstrees'], m['truck'], m['truck_above_wl_m'], m['max_yard_half']), fill=(40, 40, 40), font=f12)
    ty3 = ty2 + 24 + 3 * 20 + 16
    d.text((padL, ty3), '檢查：' + ('全部通過' if not R['problems'] else '；'.join(R['problems'])), fill=(0, 120, 0) if not R['problems'] else (190, 0, 0), font=f14)
    d.text((padL, ty3 + 24), '出處：plan.json（decks／ports／masts 的 src）與 references/research_2026-10-14.md', fill=(90, 90, 90), font=f12)
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist, x0, ylo)
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
    if probe:
        print(json.dumps({'probe': probe[0], 'ports': R['ports'], 'problems': R['problems']}, ensure_ascii=False))
        return
    R['port_list'] = P
    draw(plan, L, S, wall, col, x0, ylo, P, M, R, os.path.join(design, 'sheet02_layout_v1.png'))
    with open(os.path.join(design, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'port_list'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
