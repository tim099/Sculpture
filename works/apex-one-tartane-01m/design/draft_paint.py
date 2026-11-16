# 塔爾塔納 步驟 4（TASK-1299）：地中海船殼塗裝（雙道深橡木 wale、暖赭上帶、威尼斯紅尾樓／尾鏡、金赭框）＋ 三扇貫穿船尾窗洞
#   輸出：masks/paint/carve.vox.txt、masks/paint/paint.vox.txt、verify_paint.json、sheet03_paint_v1.png
#   用法：python -I -X utf8 draft_paint.py <design> [--probe=skip_win=1]
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb


def wale_rows(plan, w, xs):
    """護舷帶沿主甲板舷弧（x < 134 接後端主甲板高度延伸成艉部水平帶）。"""
    lo = np.array([int(LY.deck_z(plan, w['deck'], max(134.0, float(x)) + 0.5)) + w['dz'] for x in np.atleast_1d(xs)])
    return lo, lo + w['h'] - 1


def stern_windows(plan, YC):
    out = []
    for row in plan['stern']['rows']:
        n, w, h, half = row['n'], row['w'], row['h'], row['half']
        assert w % 2 == 1, '船尾窗寬要奇數（才能對中線對稱）'
        zc = int(LY.deck_z(plan, row['deck'], 110)) + row['sill']
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
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist)
    PA = plan['paint']
    BASE, WALE, CAP, FRIEZE, RED, GOLD = PA['base'], PA['wale'], PA['cap'], PA['frieze'], PA['red'], PA['gold']
    SX = PA['stern_x_max']
    nx, ny, nz = wall.shape
    xs_all = np.arange(nx) + x0
    zz = np.arange(nz)[None, :]

    # ── 外板塗裝（dist <= 1 且原為 side_color 才換；水線下白膏 218 不動）──
    outer = wall & (dist <= 1.0) & (col == BASE)
    paint = np.zeros(wall.shape, np.uint8)
    wtop = None
    for w in PA['wales']['rows']:
        lo, hi = wale_rows(plan, w, xs_all)
        inband = (zz >= lo[:, None]) & (zz <= hi[:, None])
        paint[outer & inband[:, None, :]] = w['color']
        wtop = hi if wtop is None else np.maximum(wtop, hi)

    topz = np.array([int(math.floor(float(L.top_z(x + 0.5)) + 0.5)) for x in xs_all])
    fr = (zz > wtop[:, None]) & (zz < topz[:, None])
    # 船腰用暖赭（209），艉樓（x <= 134）上舷帶用威尼斯紅（164）並在上下緣鑲細邊
    quarter_x = (xs_all <= 134)[:, None, None]
    paint[outer & fr[:, None, :]] = FRIEZE
    paint[outer & fr[:, None, :] & quarter_x] = RED

    # 最上一格舷頂壓條深橡木 68
    cap = np.zeros(wall.shape, bool)
    for xi in range(nx):
        zs_ = np.nonzero(wall[xi].any(axis=0))[0]
        if len(zs_):
            cap[xi, :, zs_[-1]] = outer[xi, :, zs_[-1]]
    paint[cap] = CAP

    # ── 船尾面（tableau）與三扇貫穿船尾窗洞 ──
    first = np.full((ny, nz), -1, int)
    for yi in range(ny):
        for z in range(nz):
            c = np.nonzero(wall[:, yi, z])[0]
            if len(c) and c[0] + x0 < SX:
                first[yi, z] = c[0]

    windows = stern_windows(plan, YC)
    skip_win = int(probe[0].split('=')[1]) if probe else None
    carve = np.zeros(wall.shape, bool)
    frame = np.zeros(wall.shape, bool)
    for wdw in windows:
        if skip_win and wdw['j'] == skip_win:
            continue
        for yi in range(wdw['y0'] - ylo, wdw['y1'] - ylo + 1):
            for z in range(wdw['z0'], wdw['z1'] + 1):
                f = first[yi, z]
                if f < 0:
                    continue
                run = [f]
                while run[-1] + 1 < nx and wall[run[-1] + 1, yi, z]:
                    run.append(run[-1] + 1)
                for xi in run:
                    carve[xi, yi, z] = True
        for yi in range(wdw['y0'] - 1 - ylo, wdw['y1'] + 2 - ylo):
            for z in range(wdw['z0'] - 1, wdw['z1'] + 2):
                if wdw['y0'] - ylo <= yi <= wdw['y1'] - ylo and wdw['z0'] <= z <= wdw['z1']:
                    continue
                f = first[yi, z]
                if f >= 0:
                    frame[f, yi, z] = True

    zwt = int(plan['lines']['wing_transom_z']['v'])
    for yi in range(ny):
        for z in range(zwt, nz):
            f = first[yi, z]
            if f >= 0 and wall[f, yi, z] and f + x0 <= float(L.x_aft(z + 0.5)) + 2:
                paint[f, yi, z] = GOLD if (z == zwt or z == topz[f] - 1) else RED

    paint[frame & ~carve] = GOLD
    paint[carve] = 0
    changes = (paint > 0) & wall & (paint != col)

    after = wall & ~carve
    acol = col.copy()
    acol[changes] = paint[changes]

    # 驗穿窗洞、結構連通與鏡像
    closed = []
    for wdw in windows:
        if skip_win and wdw['j'] == skip_win:
            continue
        cnt = 0
        for yi in range(wdw['y0'] - ylo, wdw['y1'] - ylo + 1):
            for z in range(wdw['z0'], wdw['z1'] + 1):
                f = first[yi, z]
                if f >= 0 and after[f, yi, z]:
                    cnt += 1
        if cnt:
            closed.append({'j': wdw['j'], 'solid': cnt})

    lab, ncomp = ndimage.label(after)
    filled = ndimage.binary_fill_holes(after)
    cav = int((filled & ~after).sum())
    mir_diff = int((after != after[:, ::-1, :]).sum() + ((acol * after) != (acol * after)[:, ::-1, :]).sum())

    R = {
        'carve_cells': int(carve.sum()),
        'paint_cells': int(changes.sum()),
        'carve_by_color': {int(c): int(n) for c, n in zip(*np.unique(col[carve], return_counts=True))},
        'paint_to': {int(c): int(n) for c, n in zip(*np.unique(acol[changes], return_counts=True))},
        'after_cells': int(after.sum()),
        'stern_windows_not_open': closed,
        'components_6': int(ncomp),
        'cavity_cells': cav,
        'mirror_diff': mir_diff,
        'windows': windows,
    }
    if probe:
        print(json.dumps({'probe': probe[0], 'carve_cells': R['carve_cells'], 'stern_windows_not_open': closed}, ensure_ascii=False))
        return

    out = os.path.join(design, 'masks', 'paint')
    os.makedirs(out, exist_ok=True)

    def dump(path, mask, colors, head):
        idx = np.argwhere(mask)
        order = np.lexsort((idx[:, 2], idx[:, 1], idx[:, 0])) if len(idx) else []
        idx = idx[order] if len(idx) else idx
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(head)
            for xi, yi, z in idx:
                fh.write('%d,%d,%d,%d\n' % (xi + x0, yi + ylo, z, colors[xi, yi, z]))
        return len(idx), hashlib.sha256(open(path, 'rb').read()).hexdigest()

    n1, h1 = dump(os.path.join(out, 'carve.vox.txt'), carve, col, '# 塔爾塔納 船尾窗開口（carvevox；第 4 欄為刻前原色）\n')
    n2, h2 = dump(os.path.join(out, 'paint.vox.txt'), changes, acol, '# 塔爾塔納 塗裝換色（stampvox overwrite=1）\n')
    R['lists'] = {'carve': [n1, h1], 'paint': [n2, h2]}

    sc = 4.0
    Wp = int(nx * sc) + 100 + int(ny * sc) + 80
    Hp = int(nz * sc) + 150
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((40, 16), '塔爾塔納 新圖紙 03：地中海塗裝與三扇船尾窗　v1（frieze %d / red %d / gold %d / wale %d）' % (FRIEZE, RED, GOLD, WALE), fill=(0, 0, 0), font=font(18))
    oy = 56
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
    d.text((40, oy + nz * sc + 12), '右舷側面（船頭在右）　　船尾正面（從船尾看，左手 ＝ −y ＝ 左舷 P）', fill=(40, 40, 40), font=font(14))
    d.text((40, oy + nz * sc + 36), '刻窗 %d 格、換色 %d 格、實心 %d 格；未開窗 %d；6 連通 %d、空腔 %d、鏡像差 %d' % (
        R['carve_cells'], R['paint_cells'], R['after_cells'], len(closed), ncomp, cav, mir_diff), fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet03_paint_v1.png'), optimize=False)
    with open(os.path.join(design, 'verify_paint.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('windows', 'lists')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
