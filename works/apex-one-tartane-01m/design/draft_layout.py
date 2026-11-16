# 塔爾塔納 新圖紙 02（TASK-1299）：配置 ⇒ sheet02_layout_v1.png（側面：甲板、雙拉丁桅與斜桁、首斜桅與 foc；俯視：甲板範圍與桅位）、verify_layout.json
#   用法：python -I -X utf8 draft_layout.py <design 資料夾> [--probe=mast=fore:rake:+5]
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    if probe:
        _, spec = probe[0].split('=', 1)
        mkey, field, dv = spec.split(':')
        for row in plan['masts']['rows']:
            if row['key'] == mkey:
                if field == 'rake':
                    row['rake_deg'] += float(dv)
                elif field == 'x':
                    row['x_step'] += int(float(dv))
    M = LY.masts(plan, L)
    B = LY.bowsprit(plan, L)
    wl = plan['waterline']['z']

    # 計算雙拉丁帆桁幾何與淨隙驗證
    lateen_checks = {}
    for m in M:
        yl = m['yards']['lateen']
        if m['key'] == 'fore':
            a, fwd_frac, clew_x = math.radians(41), 0.26, m['x'] - 12.0
        else:
            a, fwd_frac, clew_x = math.radians(39), 0.34, 114.0
        hx = LY.mast_axis_x(plan, m['key'], yl['z'], L)
        hz = yl['z']
        fx, fz = hx + fwd_frac * yl['len'] * math.cos(a), hz - fwd_frac * yl['len'] * math.sin(a)
        bx, bz = hx - (1.0 - fwd_frac) * yl['len'] * math.cos(a), hz + (1.0 - fwd_frac) * yl['len'] * math.sin(a)
        clew_z = float(LY.deck_z(plan, 'quarter' if clew_x < 134 else 'main', clew_x) + 12)
        lateen_checks[m['key']] = {
            'mast_top': [round(float(LY.mast_axis_x(plan, m['key'], m['truck'], L)), 1), round(m['truck'], 1)],
            'sling': [round(float(hx), 1), round(hz, 1)],
            'car': [round(float(fx), 1), round(fz, 1)],
            'peak': [round(float(bx), 1), round(bz, 1)],
            'clew': [round(float(clew_x), 1), round(clew_z, 1)],
        }

    R = {
        'ports_total': 0,
        'decks': {r['key']: {'z': r['z'], 'span': LY.deck_span(plan, L, r['key'])} for r in plan['decks']['rows']},
        'masts': [{
            'key': m['key'], 'label': m['label'], 'x': m['x'], 'rake': m['rake'],
            'heel': round(m['heel'], 1), 'calcet': round(m['calcet'], 1), 'truck': round(m['truck'], 1),
            'above_wl_m': round((m['truck'] - wl) * 0.1, 2),
            'yards': {k: {'z': round(v['z'], 1), 'len_m': round(v['len'] * 0.1, 2)} for k, v in m['yards'].items()},
        } for m in M],
        'bowsprit': {k: (round(v, 1) if isinstance(v, (int, float)) else v) for k, v in B.items()},
        'lateen_geometry': lateen_checks,
    }
    if probe:
        print(json.dumps({'probe': probe[0], 'lateen_geometry': lateen_checks}, ensure_ascii=False))
        return

    sc = 3.5
    x_lo, x_hi, z_hi = 45, 345, 240
    nx, nz = x_hi - x_lo, z_hi
    padL, padT = 60, 90
    Wp = int(nx * sc) + padL * 2 + 140
    side_h = int(nz * sc)
    top_h = int(75 * sc)
    Hp = padT + side_h + 70 + top_h + 70 + 320
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    f12, f14, f20 = font(12), font(14), font(22)
    X = lambda x: padL + (x - x_lo) * sc
    Zs = lambda z: padT + (z_hi - z) * sc
    d.text((padL, 20), '塔爾塔納（Tartane de négoce）新圖紙 02：甲板、雙拉丁桅帆、短斜桅　v1', fill=(20, 20, 20), font=f20)
    d.text((padL, 52), '0.1 m／格　側面從右舷看（船頭在右）　Jouve 1679 Pl.19–20 / Zuanne 1686 / Paragan', fill=(60, 60, 60), font=f14)

    zs = np.arange(0, 50) + 0.5
    top = L.top_z(np.arange(x_lo, x_hi) + 0.5)
    for x in range(x_lo, x_hi):
        h = L.hb(np.full(zs.shape, x + 0.5), zs)
        for z in np.nonzero((h >= 0) & (zs <= top[x - x_lo] + 0.5))[0]:
            c = palette_rgb(plan['hull_build']['bottom_color'] if z < wl else plan['hull_build']['side_color'])
            d.rectangle([X(x), Zs(z + 1), X(x + 1), Zs(z)], fill=c)
    d.line([X(x_lo), Zs(wl), X(x_hi), Zs(wl)], fill=(0, 90, 200))
    d.text((X(x_hi) + 4, Zs(wl) - 8), 'WL %d' % wl, fill=(0, 90, 200), font=f12)

    for r in plan['decks']['rows']:
        a, b = LY.deck_span(plan, L, r['key'])
        xs = np.arange(a, b + 1)
        zz = LY.deck_z(plan, r['key'], xs + 0.5)
        d.line(list(zip([X(x) for x in xs], [Zs(z + 1) for z in zz])), fill=(220, 40, 40), width=2)
        d.text((X(b) + 3, Zs(zz[-1] + 1) - 7), r['key'], fill=(190, 0, 0), font=f12)

    sail = (242, 234, 214)
    for m in M:
        ax = lambda z: LY.mast_axis_x(plan, m['key'], z, L)
        d.line([X(ax(m['heel'])), Zs(m['heel']), X(ax(m['truck'])), Zs(m['truck'])], fill=(110, 70, 30), width=4)
        lg = lateen_checks[m['key']]
        d.polygon([(X(lg['car'][0]), Zs(lg['car'][1])), (X(lg['peak'][0]), Zs(lg['peak'][1])), (X(lg['clew'][0]), Zs(lg['clew'][1]))],
                  fill=sail, outline=(150, 140, 120))
        d.line([X(lg['car'][0]), Zs(lg['car'][1]), X(lg['peak'][0]), Zs(lg['peak'][1])], fill=(60, 40, 20), width=3)
        d.text((X(ax(m['truck'])) - 24, Zs(m['truck']) - 18), m['label'], fill=(80, 50, 20), font=f12)

    d.line([X(B['x0']), Zs(B['z0']), X(B['x1']), Zs(B['z1'])], fill=(110, 70, 30), width=3)
    fore_top = lateen_checks['fore']['mast_top']
    d.polygon([(X(fore_top[0] - 1), Zs(fore_top[1] - 4)), (X(B['x1'] - 2), Zs(B['z1'] + 1)), (X(298), Zs(39))],
              fill=sail, outline=(150, 140, 120))

    for x in range(50, x_hi, 25):
        d.line([X(x), Zs(0), X(x), Zs(0) + 6], fill=(0, 0, 0))
        d.text((X(x) - 10, Zs(0) + 8), str(x), fill=(80, 80, 80), font=f12)
    for z in range(0, z_hi, 25):
        d.text((padL - 40, Zs(z) - 7), 'z%d' % z, fill=(120, 120, 120), font=f12)

    oy = padT + side_h + 70
    d.text((padL, oy - 22), '② 俯視（右半）：甲板範圍、雙桅腳位、斜桁水平投影與首斜桅', fill=(0, 0, 0), font=f14)
    cy = oy + top_h - 24
    T = lambda y: cy - y * sc
    d.line([X(x_lo), cy, X(x_hi), cy], fill=(0, 0, 0))
    for x in range(x_lo, x_hi):
        h = float(L.hb(np.array([x + 0.5]), np.array([20.5]))[0])
        if h > 0:
            d.line([X(x), T(0), X(x), T(h)], fill=(225, 222, 210))
    cols = {'hold': (150, 150, 150), 'main': (200, 60, 60), 'cabin': (220, 120, 0), 'quarter': (0, 120, 0)}
    for j, r in enumerate(plan['decks']['rows']):
        a, b = LY.deck_span(plan, L, r['key'])
        d.line([X(a), T(-6 - 4 * j), X(b), T(-6 - 4 * j)], fill=cols[r['key']], width=3)
        d.text((X(b) + 4, T(-6 - 4 * j) - 7), r['name'], fill=cols[r['key']], font=f12)
    for m in M:
        lg = lateen_checks[m['key']]
        d.line([X(lg['peak'][0]), T(3), X(lg['car'][0]), T(3)], fill=(110, 70, 30), width=2)
        d.ellipse([X(m['x']) - 4, T(0) - 4, X(m['x']) + 4, T(0) + 4], fill=(110, 70, 30))
    d.line([X(B['x0']), T(0), X(B['x1']), T(0)], fill=(110, 70, 30), width=2)

    oy3 = oy + top_h + 45
    rows = ['武裝：無艦砲商船（0 門），300 cantars（~15 t 貨載）沿岸貿易型']
    for r in plan['decks']['rows']:
        sp = R['decks'][r['key']]['span']
        rows.append('%s（%s）：z %d、x %d..%d（長 %.1f m）' % (r['key'], r['name'], r['z'], sp[0], sp[1], (sp[1] - sp[0] + 1) * 0.1))
    for m in R['masts']:
        rows.append('%s（%s）：x %d（rake %+g°）、腳 z %.0f、calcet z %.0f、頂 z %.0f（離水線 %.1f m）；斜桁 %s' % (
            m['key'], m['label'], m['x'], m['rake'], m['heel'], m['calcet'], m['truck'], m['above_wl_m'],
            '、'.join('%s %.1f m @z%.0f' % (k, v['len_m'], v['z']) for k, v in m['yards'].items())))
    rows.append('bowsprit（bout-dehors）：腳 (%d, z %.0f)、仰角 %g°、長 %.1f m、頂 (%.0f, z %.0f)、張帆 %s' % (
        B['x0'], B['z0'], B['angle'], B['len'] * 0.1, B['x1'], B['z1'], B['extra_sail']))
    for i, t in enumerate(rows):
        d.text((padL, oy3 + i * 22), t, fill=(20, 20, 20), font=f14)
    im.save(os.path.join(design, 'sheet02_layout_v1.png'), optimize=False)
    with open(os.path.join(design, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
