# 直接出處：apex-two-galeon-01m/design/draft_layout.py（康塞普西翁號，TASK-0969）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是康塞普西翁號那時寫的出處
# 直接出處：gura-pinas-01m/design/draft_layout.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/draft_layout.py（收穫號，照抄後改成聖羅曼號 —— TASK-0970）
# 聖羅曼號 新圖紙 02（TASK-0590）：配置 ⇒ sheet02_layout_v1.png（側面：甲板、砲門、桅、帆桁、帆；俯視：甲板範圍、桅位）、verify_layout.json
#   用法：python -I -X utf8 draft_layout.py <design 資料夾> [--probe=port=main:5:+3]
#   · --probe：反向對照（把某一層第 N 個砲門往船頭推幾格），只印讀數、不寫檔。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb


def port_readings(plan, L, P):
    """每層：砲門數、相鄰間距（邊到邊）最小／最大、砲門頂到上一層甲板面的距離、砲門中心那一格離舷外多深（在不在船殼牆上）。"""
    above = {'main': 'tolda', 'tolda': None, 'castillo': None}      # 聖羅曼號：一層主甲板（船尾那一段上面有 tolda）
    top_poly = lambda x: float(L.top_z(x + 0.5))
    out = {}
    for t in plan['ports']['tiers']:
        k = t['deck']
        ps = [p for p in P if p['deck'] == k]
        gaps = [ps[i + 1]['x0'] - ps[i]['x1'] - 1 for i in range(len(ps) - 1)]
        clear = []
        for p in ps:
            xc = (p['x0'] + p['x1']) / 2.0
            lim = top_poly(xc)
            a = above.get(k)
            if a:
                r = LY.deck_row(plan, a)
                if r.get('x_from', -1e9) <= xc <= r.get('x_to', 1e9):
                    lim = min(lim, float(LY.deck_z(plan, a, xc)) - 3)      # 上一層甲板的橫樑約 3 格深
            clear.append(round(lim - p['z1'], 1))
        inside = [round(float(L.hb(np.array([(p['x0'] + p['x1']) / 2.0 + 0.5]), np.array([(p['z0'] + p['z1']) / 2.0 + 0.5]))[0]), 1) for p in ps]
        out[k] = {'n_per_side': len(ps), 'gap_min': min(gaps) if gaps else None, 'gap_max': max(gaps) if gaps else None,
                  'gaps': gaps, 'clear_above_min': min(clear), 'half_breadth_at_port_min': min(inside),
                  'x0s': [p['x0'] for p in ps]}
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    P = LY.ports(plan)
    if probe:
        _, spec = probe[0].split('=', 1)
        dk, i, dv = spec.split(':')
        for p in P:
            if p['deck'] == dk and p['i'] == int(i):
                p['x0'] += int(dv)
                p['x1'] += int(dv)
    M = LY.masts(plan, L)
    B = LY.bowsprit(plan)
    wl = plan['waterline']['z']
    R = {'ports': port_readings(plan, L, P),
         'ports_total': len(P) * 2 + plan['ports']['stern_chasers']['n'],
         'decks': {r['key']: {'z': r['z'], 'span': LY.deck_span(plan, L, r['key'])} for r in plan['decks']['rows']},
         'masts': [{'key': m['key'], 'x': m['x'], 'heel': round(m['heel'], 1), 'platform': round(m['platform'], 1), 'truck': round(m['truck'], 1),
                    'above_wl_m': round((m['truck'] - wl) * 0.1, 2), 'yards': {k: {'z': round(v['z'], 1), 'len_m': round(v['len'] * 0.1, 2)} for k, v in m['yards'].items()}} for m in M],
         'bowsprit': {k: round(v, 1) for k, v in B.items()}}
    if probe:
        print(json.dumps({'probe': probe[0], 'ports': R['ports']}, ensure_ascii=False))
        return

    # ── 圖 ──
    sc = 3.0      # 聖羅曼號：船小 ⇒ 放大、範圍收到 400×240
    x_lo, x_hi, z_hi = 30, 380, 240
    nx, nz = x_hi - x_lo, z_hi
    padL, padT = 60, 90
    Wp = int(nx * sc) + padL * 2 + 120
    side_h = int(nz * sc)
    top_h = int(70 * sc)
    Hp = padT + side_h + 80 + top_h + 80 + 420
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    f12, f14, f20 = font(12), font(14), font(22)
    X = lambda x: padL + (x - x_lo) * sc
    Zs = lambda z: padT + (z_hi - z) * sc
    d.text((padL, 20), '聖羅曼號（Santo Cristo de San Román，patache）新圖紙 02：甲板、砲門、桅與帆　v1', fill=(20, 20, 20), font=f20)
    d.text((padL, 52), '0.1 m／格　側面從右舷看（船頭在右）　主尺寸照 1618 年條例 10 codos；砲門照 art.42；桅位照 art.66–68、桅長研究〔估〕', fill=(60, 60, 60), font=f14)
    # 船殼側面剪影（外形實心的每個 (x, z)）
    zs = np.arange(0, 80) + 0.5
    top = L.top_z(np.arange(x_lo, x_hi) + 0.5)
    for x in range(x_lo, x_hi):
        h = L.hb(np.full(zs.shape, x + 0.5), zs)
        for z in np.nonzero((h >= 0) & (zs <= top[x - x_lo] + 0.5))[0]:
            c = palette_rgb(plan['hull_build']['bottom_color'] if z < wl else plan['hull_build']['side_color'])
            d.rectangle([X(x), Zs(z + 1), X(x + 1), Zs(z)], fill=c)
    d.line([X(x_lo), Zs(wl), X(x_hi), Zs(wl)], fill=(0, 90, 200))
    d.text((X(x_hi) + 4, Zs(wl) - 8), 'WL %d' % wl, fill=(0, 90, 200), font=f12)
    # 甲板（紅線，照舷弧與範圍）
    for r in plan['decks']['rows']:
        a, b = LY.deck_span(plan, L, r['key'])
        xs = np.arange(a, b + 1)
        zz = LY.deck_z(plan, r['key'], xs + 0.5)
        d.line(list(zip([X(x) for x in xs], [Zs(z + 1) for z in zz])), fill=(220, 40, 40), width=2)
        d.text((X(b) + 3, Zs(zz[-1] + 1) - 7), r['key'], fill=(190, 0, 0), font=f12)
    # 砲門
    gc = {'18l': (255, 210, 60), '12l': (255, 150, 60), '8l': (230, 90, 40), '6l': (255, 110, 160), '4l': (170, 60, 170)}
    for p in P:
        d.rectangle([X(p['x0']), Zs(p['z1'] + 1), X(p['x1'] + 1), Zs(p['z0'])], fill=gc[p['gun']], outline=(120, 0, 0))
    # 桅、帆桁、帆
    sail = (240, 232, 210)
    for m in M:
        ax = lambda z: LY.mast_axis_x(plan, m['key'], z, L)
        d.line([X(ax(m['heel'])), Zs(m['heel']), X(ax(m['truck'])), Zs(m['truck'])], fill=(110, 70, 30), width=3)
        d.line([X(ax(m['platform']) - 12), Zs(m['platform']), X(ax(m['platform']) + 12), Zs(m['platform'])], fill=(80, 50, 20), width=3)
        Y = m['yards']
        if 'course' in Y:
            yc, yt = Y['course'], Y['topsail']
            foot = LY.deck_z(plan, 'main', m['x']) + 20      # 聖羅曼號：帆腳在船腰舷頂上面
            # 側面只看得到帆的厚度 ⇒ 畫成一條帆面（帆桁長的投影用虛線框示意在俯視圖）
            d.polygon([(X(ax(yc['z']) - 3), Zs(yc['z'])), (X(ax(yc['z']) + 3), Zs(yc['z'])), (X(ax(foot) + 6), Zs(foot)), (X(ax(foot) - 6), Zs(foot))], fill=sail, outline=(150, 140, 120))
            d.polygon([(X(ax(yt['z']) - 2), Zs(yt['z'])), (X(ax(yt['z']) + 2), Zs(yt['z'])), (X(ax(yc['z'] + 14) + 4), Zs(yc['z'] + 14)), (X(ax(yc['z'] + 14) - 4), Zs(yc['z'] + 14))], fill=sail, outline=(150, 140, 120))
            if 'topgallant' in Y:
                yg = Y['topgallant']
                d.polygon([(X(ax(yg['z']) - 1), Zs(yg['z'])), (X(ax(yg['z']) + 1), Zs(yg['z'])), (X(ax(yt['z'] + 8) + 3), Zs(yt['z'] + 8)), (X(ax(yt['z'] + 8) - 3), Zs(yt['z'] + 8))], fill=sail, outline=(150, 140, 120))
            for k in [k for k in ('course', 'topsail', 'topgallant') if k in Y]:
                d.line([X(ax(Y[k]['z'])) - 4, Zs(Y[k]['z']), X(ax(Y[k]['z'])) + 4, Zs(Y[k]['z'])], fill=(60, 40, 20), width=4)
        if 'lateen' in Y:
            yl = Y['lateen']
            a = math.radians(35)
            hx, hz = ax(yl['z']), yl['z']
            # 吊點在帆桁的 40%：前端低、後端高
            fx, fz = hx + 0.4 * yl['len'] * math.cos(a), hz - 0.4 * yl['len'] * math.sin(a)
            bx, bz = hx - 0.6 * yl['len'] * math.cos(a), hz + 0.6 * yl['len'] * math.sin(a)
            tack_z = max(fz, LY.deck_z(plan, 'main', m['x']) + 30)      # 聖羅曼號：tolda 上面
            d.polygon([(X(fx), Zs(fz)), (X(bx), Zs(bz)), (X(hx - 4), Zs(tack_z))], fill=sail, outline=(150, 140, 120))
            d.line([X(fx), Zs(fz), X(bx), Zs(bz)], fill=(60, 40, 20), width=3)
        d.text((X(ax(m['truck'])) - 20, Zs(m['truck']) - 18), m['key'], fill=(80, 50, 20), font=f12)
    d.line([X(B['x0']), Zs(B['z0']), X(B['x1']), Zs(B['z1'])], fill=(110, 70, 30), width=3)
    sx = B['x0'] + 0.85 * (B['x1'] - B['x0'])
    sz = B['z0'] + 0.85 * (B['z1'] - B['z0'])
    d.polygon([(X(sx - 3), Zs(sz - 3)), (X(sx + 3), Zs(sz - 3)), (X(sx + 6), Zs(sz - 25)), (X(sx - 6), Zs(sz - 25))], fill=sail, outline=(150, 140, 120))
    esp = plan['espolon']['len_beyond_stem']
    xs_stem = float(L.x_stem(40))
    d.polygon([(X(xs_stem), Zs(42)), (X(xs_stem + esp), Zs(45)), (X(xs_stem), Zs(28))], outline=(120, 0, 0))      # 聖羅曼號：喙在主甲板上面
    d.text((X(xs_stem + esp) - 30, Zs(45) - 18), 'espolón（步驟 6）', fill=(120, 0, 0), font=f12)
    for x in range(100, x_hi, 50):
        d.line([X(x), Zs(0), X(x), Zs(0) + 6], fill=(0, 0, 0))
        d.text((X(x) - 10, Zs(0) + 8), str(x), fill=(80, 80, 80), font=f12)
    for z in range(0, z_hi, 50):
        d.text((padL - 40, Zs(z) - 7), 'z%d' % z, fill=(120, 120, 120), font=f12)
    # 俯視：甲板範圍、桅位、帆桁長
    oy = padT + side_h + 80
    d.text((padL, oy - 22), '② 俯視（右半）：甲板範圍、桅位、帆桁長（方帆桁正橫；lateen 投影）', fill=(0, 0, 0), font=f14)
    cy = oy + top_h - 20
    T = lambda y: cy - y * sc
    d.line([X(x_lo), cy, X(x_hi), cy], fill=(0, 0, 0))
    for x in range(x_lo, x_hi):
        h = float(L.hb(np.array([x + 0.5]), np.array([L.z_mb + 0.5]))[0])      # 聖羅曼號：最寬那一層
        if h > 0:
            d.line([X(x), T(0), X(x), T(h)], fill=(225, 222, 210))
    cols = {'orlop': (150, 150, 150), 'main': (200, 60, 60), 'tolda': (0, 120, 0), 'castillo': (130, 0, 160)}
    for j, r in enumerate(plan['decks']['rows']):
        a, b = LY.deck_span(plan, L, r['key'])
        d.line([X(a), T(-6 - 4 * j), X(b), T(-6 - 4 * j)], fill=cols[r['key']], width=3)
        d.text((X(b) + 4, T(-6 - 4 * j) - 7), r['name'], fill=cols[r['key']], font=f12)
    for m in M:
        for k, v in m['yards'].items():
            half = v['len'] / 2 if k != 'lateen' else v['len'] * 0.5 * math.cos(math.radians(35))
            if k == 'lateen':
                d.line([X(m['x'] - half), T(4), X(m['x'] + half), T(4)], fill=(110, 70, 30), width=2)
            else:
                d.line([X(m['x']), T(0), X(m['x']), T(half)], fill=(110, 70, 30), width=2)
        d.ellipse([X(m['x']) - 4, T(0) - 4, X(m['x']) + 4, T(0) + 4], fill=(110, 70, 30))
    # 表
    oy3 = oy + top_h + 50
    rows = []
    for t in plan['ports']['tiers']:
        pr = R['ports'][t['deck']]
        rows.append('%s：每舷 %d 門 %s；砲門 %d×%d、下緣在甲板上 %d；間距 %s–%s 格；砲門頂到上一層樑／舷頂 ≥ %s 格' % (
            t['deck'], t['per_side'], t['gun'], t['w'], t['h'], t['sill'], pr['gap_min'], pr['gap_max'], pr['clear_above_min']))
    sc_ = plan['ports']['stern_chasers']
    rows.append('船尾鏡板砲門：%s %d 門 %s　合計 %d 門' % (sc_['deck'], sc_['n'], sc_['gun'], R['ports_total']))
    guns = {}
    for p in P:
        guns[p['gun']] = guns.get(p['gun'], 0) + 2
    guns[sc_['gun']] = guns.get(sc_['gun'], 0) + sc_['n']
    rows.append('砲種（兩舷＋船尾）：' + '、'.join('%s ×%d' % (k, v) for k, v in sorted(guns.items())))
    R['guns_by_type'] = guns
    for m in R['masts']:
        rows.append('%s：x %d、腳 z %.0f、平台 z %.0f、頂 z %.0f（離水線 %.1f m）；帆桁 %s' % (
            m['key'], m['x'], m['heel'], m['platform'], m['truck'], m['above_wl_m'], '、'.join('%s %.1f m @z%.0f' % (k, v['len_m'], v['z']) for k, v in m['yards'].items())))
    b = R['bowsprit']
    rows.append('bowsprit：腳 (%d, z %d)、仰角 %d°、長 %.1f m、頂 (%.0f, z %.0f)；spritsail 帆桁 %.1f m' % (b['x0'], b['z0'], b['angle'], b['len'] * 0.1, b['x1'], b['z1'], b['spritsail_len'] * 0.1))
    for i, t in enumerate(rows):
        d.text((padL, oy3 + i * 22), t, fill=(20, 20, 20), font=f14)
    im.save(os.path.join(design, 'sheet02_layout_v1.png'), optimize=False)
    with open(os.path.join(design, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'ports'}, ensure_ascii=False))
    for k, v in R['ports'].items():
        print(k, {kk: vv for kk, vv in v.items() if kk not in ('gaps', 'x0s')})


if __name__ == '__main__':
    main()
