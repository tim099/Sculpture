# 牛津號 階段三（TASK-0972）：炮門、塗裝（黑 wale、藍底金邊的上部飾帶、紅炮門框）、船尾（wing transom、兩排船尾窗）
#   輸入：plan.json（ports／paint／stern）＋ 船殼（draft_lines.hull_volume 算的那一份 ⇒ 跟作品逐格相同，階段二結果帳證過）
#   輸出：masks/ports/carve.vox.txt（carvevox，第 4 欄 ＝ 刻之前的顏色，守門）、masks/ports/paint.vox.txt（stampvox overwrite=1：換色）、
#         verify_ports.json、sheet03_ports_paint_v1.png
#   用法：python -I -X utf8 draft_ports.py <design> [--probe=skip_port=<層>:<序號>]   （probe：少開一個炮門重量，⛔ 不寫檔）
#   來源：calli-cosecha-01m/design/draft_ports.py 的結構（開口、reveal、船尾面「從最後面往前那一段牆」、對稱取整的窗）；配色與帶子是本船的。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb


def stern_windows(plan, L, YC):
    out = []
    xs = plan['stern']['x_max']
    for row in plan['stern']['rows']:
        n, w, h, half = row['n'], row['w'], row['h'], row['half']
        assert w % 2 == 1, '船尾窗寬要奇數（才能對中線對稱）'
        zc = int(math.floor(float(L.deck_z(row['deck'], 46)))) + row['sill']
        cs = np.linspace(-half + w / 2.0, half - w / 2.0, n)
        for j, c in enumerate(cs):
            k = int(math.floor(abs(c) + 0.5)) * (1 if c >= 0 else -1)
            y0 = YC + k - (w - 1) // 2
            out.append({'deck': row['deck'], 'j': j + 1, 'y0': y0, 'y1': y0 + w - 1, 'z0': zc, 'z1': zc + h - 1, 'kind': row['kind']})
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    Y = LY.Layout(plan, L)
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist)
    PA = plan['paint']
    WOOD, BLACK, BLUE, GOLD, REVEAL, GLASS = PA['wood'], PA['black'], PA['blue'], PA['gold'], PA['reveal'], PA['glass']
    nx, ny, nz = wall.shape
    dy_of = np.arange(ny) + ylo - YC
    xs_all = np.arange(nx) + x0
    zz = np.arange(nz)[None, :]
    gz = np.array([int(math.floor(float(L.gun_z(x + 0.5)))) for x in xs_all])     # 炮甲板面（第一層空氣）每一欄

    ports = Y.ports()
    for i, p in enumerate(ports):
        p['i'] = sum(1 for q in ports[:i] if q['deck'] == p['deck']) + 1
        p['x0'], p['x1'] = p['x'] - p['w'] // 2, p['x'] + p['w'] // 2
        p['z0'], p['z1'] = p['sill'], p['sill'] + p['h'] - 1
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
            ysel = (dy_of * side) >= 10
            xs = slice(p['x0'] - x0, p['x1'] - x0 + 1)
            zs = slice(p['z0'], p['z1'] + 1)
            carve[xs, :, zs] |= wall[xs, :, zs] & ysel[None, :, None]
            xr = slice(p['x0'] - 1 - x0, p['x1'] + 2 - x0)
            zr = slice(p['z0'] - 1, p['z1'] + 2)
            ring[xr, :, zr] |= wall[xr, :, zr] & ysel[None, :, None]
    ring &= ~carve

    # ── 塗裝：外板那一層（dist ≤ 1）、原本是木色的格照高度換色（水線下白色不動）──
    outer = wall & (dist <= 1.0) & (col == WOOD)
    paint = np.zeros(wall.shape, np.uint8)
    for w in PA['wales']:
        lo = gz + w['dz']
        inband = (zz >= lo[:, None]) & (zz <= lo[:, None] + w['h'] - 1)
        paint[outer & inband[:, None, :]] = BLACK
    fz = gz + PA['frieze_from_dz']
    topz = np.array([int(math.floor(float(L.top_z(x + 0.5)) + 0.5)) for x in xs_all])
    fr = zz >= fz[:, None]
    paint[outer & fr[:, None, :]] = BLUE
    paint[outer & (zz == fz[:, None])[:, None, :]] = GOLD
    paint[outer & (zz == topz[:, None] - 1)[:, None, :] & fr[:, None, :]] = GOLD
    # 舷頂最上一格（不論內外，舷緣頂面）黑
    cap = np.zeros(wall.shape, bool)
    for xi in range(nx):
        zt = min(nz - 1, topz[xi])
        cap[xi, :, zt] = wall[xi, :, zt]
    paint[cap] = BLACK

    # ── 船尾面：每個 (y, z) 從最後面往前那一段牆（x < x_max）──
    XM = plan['stern']['x_max']
    first = np.full((ny, nz), -1, int)
    for yi in range(ny):
        for z in range(nz):
            c = np.nonzero(wall[:, yi, z])[0]
            # 只算船尾板那一面：最後面那一格離艉柱斜面（x_aft）3 格內 —— 船尾附近的舷側（從後面也看得到）不算
            if len(c) and c[0] + x0 < XM and c[0] + x0 <= float(L.x_aft(z + 0.5)) + 3:
                first[yi, z] = c[0]
    sface = np.zeros(wall.shape, bool)
    for yi in range(ny):
        for z in range(nz):
            if first[yi, z] >= 0:
                sface[first[yi, z], yi, z] = True
    sface &= col == WOOD
    wb0, wb1 = plan['stern']['wing_band']
    zsel = np.zeros(nz, bool)
    zsel[wb0:wb1 + 1] = True
    up = np.zeros(nz, bool)
    up[wb1 + 1:] = True
    # 船尾上部：藍底（舷頂黑、wing transom 黑）
    paint[sface & up[None, None, :] & ~cap] = BLUE
    paint[sface & zsel[None, None, :]] = BLACK
    windows = stern_windows(plan, L, YC)
    glass = np.zeros(wall.shape, bool)
    frame = np.zeros(wall.shape, bool)
    stern_open = np.zeros(wall.shape, bool)
    for wdw in windows:
        for yi in range(wdw['y0'] - ylo, wdw['y1'] - ylo + 1):
            for z in range(wdw['z0'], wdw['z1'] + 1):
                f = first[yi, z]
                if f < 0:
                    continue
                # 窗洞整段牆刻穿（外板、肋骨、內板）；玻璃 1 格放在窗洞第二層、另一件子作品（material=glass；Ship_Materials「窗的玻璃」：後面要是空的）
                run = [f]
                while run[-1] + 1 < nx and wall[run[-1] + 1, yi, z]:
                    run.append(run[-1] + 1)
                for xi in run:
                    stern_open[xi, yi, z] = True
                glass[run[1] if len(run) > 1 else f, yi, z] = True
        for yi in range(wdw['y0'] - 1 - ylo, wdw['y1'] + 2 - ylo):
            for z in range(wdw['z0'] - 1, wdw['z1'] + 2):
                if wdw['y0'] - ylo <= yi <= wdw['y1'] - ylo and wdw['z0'] <= z <= wdw['z1']:
                    continue
                f = first[yi, z]
                if f >= 0:
                    frame[f, yi, z] = True
    carve |= stern_open
    paint[frame & ~carve] = GOLD
    paint[ring] = REVEAL
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
            ysel = (dy_of * side) >= 10
            blk = after[p['x0'] - x0:p['x1'] - x0 + 1, :, p['z0']:p['z1'] + 1] & ysel[None, :, None]
            if blk.any():
                see.append({'deck': p['deck'], 'i': p['i'], 'side': 'S' if side > 0 else 'P', 'solid': int(blk.sum())})
    R['ports_not_open'] = see
    R['ports'] = [{k: p[k] for k in ('deck', 'i', 'x0', 'x1', 'z0', 'z1')} for p in ports]
    # 炮門開口每一個：開出來的格數（兩舷應該一樣）
    R['port_open_cells'] = sorted({int((carve[p['x0'] - x0:p['x1'] - x0 + 1, :, p['z0']:p['z1'] + 1]).sum()) for p in ports})
    # wale 高度裡、外板那一層還是木色的（漏漆）
    left = 0
    for w in PA['wales']:
        lo = gz + w['dz']
        for xi in range(nx):
            m = after[xi, :, lo[xi]:lo[xi] + w['h']] & (dist[xi, :, lo[xi]:lo[xi] + w['h']] <= 1.0) & (acol[xi, :, lo[xi]:lo[xi] + w['h']] == WOOD)
            left += int(m.sum())
    R['wale_wood_left'] = left
    R['mirror_diff'] = int((after != after[:, ::-1, :]).sum() + ((acol * after) != (acol * after)[:, ::-1, :]).sum())
    R['windows'] = windows
    R['ports_total'] = len(ports) * 2
    R['stern_windows'] = len(windows)
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
    n1, h1 = dump(os.path.join(out, 'carve.vox.txt'), carve, col, '# 牛津號 炮門與船尾窗開口（carvevox；第 4 欄 ＝ 刻之前的顏色，守門）\n')
    n2, h2 = dump(os.path.join(out, 'paint.vox.txt'), changes, acol, '# 牛津號 塗裝（stampvox overwrite=1：換色；不含刻掉的格）\n')
    gcol = np.zeros(wall.shape, np.uint8)
    gcol[glass] = GLASS
    n3, h3 = dump(os.path.join(out, 'glass.vox.txt'), glass, gcol, '# 牛津號 船尾窗玻璃（子作品 -stern-glass，關聯 meta material=glass；世界座標，at 0,0,0）\n')
    R['lists'] = {'carve': [n1, h1], 'paint': [n2, h2], 'glass': [n3, h3]}
    # 圖紙：右舷側面＋船尾正面
    sc = 2.0
    Wp = int(nx * sc) + 120 + int(ny * sc) + 80
    Hp = int(nz * sc) + 160
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((40, 16), '牛津號 新圖紙 03：炮門、塗裝、船尾窗　v1　（黑 %d、藍 %d、金 %d、炮門框 %d、玻璃 %d）' % (BLACK, BLUE, GOLD, REVEAL, GLASS), fill=(0, 0, 0), font=font(20))
    oy = 60
    for xi in range(nx):
        for z in range(nz):
            ys = np.nonzero(after[xi, :, z])[0]
            if len(ys):
                c = palette_rgb(int(acol[xi, ys[-1], z]))
                Xp, Yp = 40 + xi * sc, oy + (nz - 1 - z) * sc
                d.rectangle([Xp, Yp, Xp + sc, Yp + sc], fill=c)
    ox = 40 + int(nx * sc) + 60
    for yi in range(ny):
        for z in range(nz):
            xs = np.nonzero(after[:, yi, z])[0]
            if len(xs):
                c = palette_rgb(int(acol[xs[0], yi, z]))
                Xp, Yp = ox + yi * sc, oy + (nz - 1 - z) * sc
                d.rectangle([Xp, Yp, Xp + sc, Yp + sc], fill=c)
    d.text((40, oy + nz * sc + 10), '右舷側面（船頭在右）　　船尾正面（從船尾看，左手 ＝ −y ＝ 左舷 P）', fill=(40, 40, 40), font=font(14))
    d.text((40, oy + nz * sc + 34), '刻 %d 格、換色 %d 格；炮門 %d（看不穿的 %d）、船尾窗 %d；wale 漏漆 %d 格；鏡像差 %d' % (
        R['carve_cells'], R['paint_cells'], len(ports) * 2, len(see), len(windows), left, R['mirror_diff']), fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet03_ports_paint_v1.png'))
    with open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('windows', 'ports')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
