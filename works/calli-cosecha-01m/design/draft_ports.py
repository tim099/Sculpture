# 收穫號 階段三（TASK-0592）：砲門、塗裝（黑底＋砲列玫瑰粉帶＋金線、船樓菱格、金舷頂）、船尾窗與追擊砲門
#   輸入：plan.json（ports／paint／stern）＋ 船殼（draft_lines.hull_volume 算的那一份 ⇒ 跟作品逐格相同，階段二結果帳證過）
#   輸出：masks/ports/carve.vox.txt（carvevox，帶刻之前的顏色守門）、masks/ports/paint.vox.txt（stampvox overwrite=1：換色）、
#         verify_ports.json、sheet03_ports_paint_v1.png
#   用法：python -I -X utf8 draft_ports.py <design> [--probe=skip_port=<層>:<序號>]   （probe：少開一個砲門重量，⛔ 不寫檔）
#   · 結構照 gura-tridente-01m/design/draft_ports.py（開口、reveal、船尾面的「從最後面往前那一段牆」、對稱取整的窗）；配色與菱格是本船的。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb


def wale_rows(plan, w, xs):
    """一條 wale 的玫瑰粉那幾列：z 範圍（含端點）＝ 甲板面 ＋ dz .. ＋ h − 1（照甲板舷弧）；陣列吃 x。"""
    lo = np.array([int(LY.deck_z(plan, w['deck'], x + 0.5)) + w['dz'] for x in np.atleast_1d(xs)])
    return lo, lo + w['h'] - 1


def stern_windows(plan, YC):
    out = []
    for row in plan['stern']['rows']:
        n, w, h, half = row['n'], row['w'], row['h'], row['half']
        assert w % 2 == 1, '船尾窗寬要奇數（才能對中線對稱）'
        zc = int(LY.deck_z(plan, row['deck'], 130)) + row['sill']
        cs = np.linspace(-half + w / 2.0, half - w / 2.0, n)
        for j, c in enumerate(cs):
            k = int(math.floor(abs(c) + 0.5)) * (1 if c >= 0 else -1)   # 對稱取整：±c ⇒ ±k
            y0 = YC + k - (w - 1) // 2
            out.append({'deck': row['deck'], 'j': j + 1, 'y0': y0, 'y1': y0 + w - 1, 'z0': zc, 'z1': zc + h - 1, 'kind': row['kind']})
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist)
    PA = plan['paint']
    BAND, GOLD, BLACK, REVEAL, GLASS = PA['band'], PA['gold'], PA['base'], PA['reveal'], PA['glass']
    nx, ny, nz = wall.shape
    dy_of = np.arange(ny) + ylo - YC
    xs_all = np.arange(nx) + x0
    zz = np.arange(nz)[None, :]

    ports = LY.ports(plan)
    skip = None
    if probe:
        k, i = probe[0].split('=')[1].split(':')
        skip = (k, int(i))
    carve = np.zeros(wall.shape, bool)
    ring = np.zeros(wall.shape, bool)
    for p in ports:
        if skip and (p['deck'], p['i']) == skip:
            continue
        for side in (1, -1):
            ysel = (dy_of * side) >= 6
            xs = slice(p['x0'] - x0, p['x1'] - x0 + 1)
            zs = slice(p['z0'], p['z1'] + 1)
            carve[xs, :, zs] |= wall[xs, :, zs] & ysel[None, :, None]
            xr = slice(p['x0'] - 1 - x0, p['x1'] + 2 - x0)
            zr = slice(p['z0'] - 1, p['z1'] + 2)
            ring[xr, :, zr] |= wall[xr, :, zr] & ysel[None, :, None]
    ring &= ~carve

    # ── 塗裝：外板那一層（dist ≤ 1）照高度換色；只換黑 36（水線下灰白不動） ──
    outer = wall & (dist <= 1.0) & (col == BLACK)
    paint = np.zeros(wall.shape, np.uint8)
    for w in PA['wales']['rows']:
        lo, hi = wale_rows(plan, w, xs_all)
        inband = (zz >= lo[:, None]) & (zz <= hi[:, None])
        edge = (zz == lo[:, None] - 1) | (zz == hi[:, None] + 1)
        paint[outer & inband[:, None, :]] = BAND
        paint[outer & edge[:, None, :]] = GOLD
    # 船樓菱格（只照 x、z 算 ⇒ 兩舷對稱）
    LZ = PA['lozenge']
    per, rad = LZ['period'], LZ['radius']
    u = np.abs((xs_all[:, None] % per) - per // 2)
    for r in LZ['rows']:
        a, b = LY.deck_span(plan, L, r['deck'])
        inx = (xs_all >= a) & (xs_all <= b)
        v = np.abs((zz - r['z0']) % per - per // 2)
        dia = (u + v) <= rad
        rows = (zz >= r['z0']) & (zz <= r['z1'])
        m = inx[:, None] & rows
        paint[outer & (m & dia)[:, None, :]] = LZ['color']
        paint[outer & (m & ~dia)[:, None, :]] = BLACK
        edge = inx[:, None] & ((zz == r['z0'] - 1) | (zz == r['z1'] + 1))
        paint[outer & edge[:, None, :]] = GOLD
    # 舷頂最上一格（外板那一層）金
    topz = np.array([int(math.floor(float(L.top_z(x + 0.5)) + 0.5)) for x in xs_all])
    cap = np.zeros(wall.shape, bool)
    for xi in range(nx):
        zt = min(nz - 1, topz[xi])
        cap[xi, :, zt] = outer[xi, :, zt]
    paint[cap] = GOLD
    paint[ring] = REVEAL

    # ── 船尾面：每個 (y, z) 從最後面往前那一段牆 ──
    first = np.full((ny, nz), -1, int)
    for yi in range(ny):
        for z in range(nz):
            c = np.nonzero(wall[:, yi, z])[0]
            if len(c) and c[0] + x0 < 170:
                first[yi, z] = c[0]
    windows = stern_windows(plan, YC)
    glass = np.zeros(wall.shape, bool)
    frame = np.zeros(wall.shape, bool)
    stern_open = np.zeros(wall.shape, bool)
    for wdw in windows:
        for yi in range(wdw['y0'] - ylo, wdw['y1'] - ylo + 1):
            for z in range(wdw['z0'], wdw['z1'] + 1):
                f = first[yi, z]
                if f < 0:
                    continue
                run = [f]
                while run[-1] + 1 < nx and wall[run[-1] + 1, yi, z]:
                    run.append(run[-1] + 1)
                if wdw['kind'] == 'port':
                    for xi in run:
                        stern_open[xi, yi, z] = True
                else:
                    stern_open[f, yi, z] = True
                    if len(run) > 1:
                        glass[run[1], yi, z] = True
        for yi in range(wdw['y0'] - 1 - ylo, wdw['y1'] + 2 - ylo):
            for z in range(wdw['z0'] - 1, wdw['z1'] + 2):
                if wdw['y0'] - ylo <= yi <= wdw['y1'] - ylo and wdw['z0'] <= z <= wdw['z1']:
                    continue
                f = first[yi, z]
                if f >= 0:
                    frame[f, yi, z] = True
    carve |= stern_open
    paint[frame & ~carve] = GOLD
    paint[glass & ~carve] = GLASS
    paint[carve] = 0
    changes = (paint > 0) & wall & (paint != col)

    # ── 讀數 ──
    after = wall & ~carve
    acol = col.copy()
    acol[changes] = paint[changes]
    R = {'carve_cells': int(carve.sum()), 'paint_cells': int(changes.sum()),
         'carve_by_color': {int(c): int(n) for c, n in zip(*np.unique(col[carve], return_counts=True))},
         'paint_to': {int(c): int(n) for c, n in zip(*np.unique(acol[changes], return_counts=True))},
         'after_cells': int(after.sum())}
    see = []
    for p in ports:
        for side in (1, -1):
            ysel = (dy_of * side) >= 6
            blk = after[p['x0'] - x0:p['x1'] - x0 + 1, :, p['z0']:p['z1'] + 1] & ysel[None, :, None]
            if blk.any():
                see.append({'deck': p['deck'], 'i': p['i'], 'side': 'S' if side > 0 else 'P', 'solid': int(blk.sum())})
    R['ports_not_open'] = see
    chasers = [w for w in windows if w['kind'] == 'port']
    st_closed = []
    for w in chasers:
        blk = after[:max(1, 170 - x0), w['y0'] - ylo:w['y1'] - ylo + 1, w['z0']:w['z1'] + 1]
        # 從船尾往前看：每個 (y, z) 第一段牆要整段刻穿 ⇒ 那一欄在牆範圍內沒有實心
        cnt = 0
        for yi in range(w['y0'] - ylo, w['y1'] - ylo + 1):
            for z in range(w['z0'], w['z1'] + 1):
                f = first[yi, z]
                if f >= 0 and after[f, yi, z]:
                    cnt += 1
        if cnt:
            st_closed.append({'y0': w['y0'], 'solid_first': cnt})
    R['stern_ports_not_open'] = st_closed
    # wale 的高度裡、外板那一層還是黑的（船頭朝前的面也算 —— 漏漆會在這裡現形）
    left_black = 0
    for w in PA['wales']['rows']:
        lo, hi = wale_rows(plan, w, xs_all)
        for xi in range(nx):
            m = after[xi, :, lo[xi]:hi[xi] + 1] & (dist[xi, :, lo[xi]:hi[xi] + 1] <= 1.0) & (acol[xi, :, lo[xi]:hi[xi] + 1] == BLACK)
            left_black += int(m.sum())
    R['band_black_left'] = left_black
    R['mirror_diff'] = int((after != after[:, ::-1, :]).sum() + ((acol * after) != (acol * after)[:, ::-1, :]).sum())
    R['windows'] = windows
    R['ports_total'] = len(ports) * 2 + len(chasers)
    if probe:
        print(json.dumps({'probe': probe[0], 'ports_not_open': see}, ensure_ascii=False))
        return
    out = os.path.join(design, 'masks', 'ports')
    os.makedirs(out, exist_ok=True)

    def dump(path, mask, colors, head):
        idx = np.argwhere(mask)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for xi, yi, z in idx:
                f.write('%d,%d,%d,%d\n' % (xi + x0, yi + ylo, z, colors[xi, yi, z]))
        return len(idx), hashlib.sha256(open(path, 'rb').read()).hexdigest()
    n1, h1 = dump(os.path.join(out, 'carve.vox.txt'), carve, col, '# 收穫號 砲門與船尾開口（carvevox；第 4 欄 ＝ 刻之前的顏色，守門）\n')
    n2, h2 = dump(os.path.join(out, 'paint.vox.txt'), changes, acol, '# 收穫號 塗裝（stampvox overwrite=1：換色；不含刻掉的格）\n')
    R['lists'] = {'carve': [n1, h1], 'paint': [n2, h2]}
    # 圖紙：右舷側面＋船尾正面
    sc = 2.0
    Wp = int(nx * sc) + 120 + int(ny * sc) + 80
    Hp = int(nz * sc) + 160
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((40, 16), '收穫號 新圖紙 03：砲門、塗裝、船尾窗　v1　（帶 %d、金 %d、reveal %d、玻璃 %d）' % (BAND, GOLD, REVEAL, GLASS), fill=(0, 0, 0), font=font(20))
    oy = 60
    for xi in range(nx):
        for z in range(nz):
            ys = np.nonzero(after[xi, :, z])[0]
            if len(ys):
                c = palette_rgb(int(acol[xi, ys[-1], z]))
                X, Y = 40 + xi * sc, oy + (nz - 1 - z) * sc
                d.rectangle([X, Y, X + sc, Y + sc], fill=c)
    ox = 40 + int(nx * sc) + 60
    for yi in range(ny):
        for z in range(nz):
            xs = np.nonzero(after[:, yi, z])[0]
            if len(xs):
                c = palette_rgb(int(acol[xs[0], yi, z]))
                X, Y = ox + yi * sc, oy + (nz - 1 - z) * sc
                d.rectangle([X, Y, X + sc, Y + sc], fill=c)
    d.text((40, oy + nz * sc + 10), '右舷側面（船頭在右）　　船尾正面（從船尾看，左手 ＝ −y ＝ 左舷 P）', fill=(40, 40, 40), font=font(14))
    d.text((40, oy + nz * sc + 34), '刻 %d 格、換色 %d 格；砲門 %d（看不穿的 %d）、船尾追擊 %d（沒刻穿的 %d）；帶子裡外板還是黑的 %d 格；鏡像差 %d' % (
        R['carve_cells'], R['paint_cells'], len(ports) * 2, len(see), len(chasers), len(st_closed), left_black, R['mirror_diff']), fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet03_ports_paint_v1.png'))
    with open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'windows'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
