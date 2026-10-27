# 拉貝爾號 步驟 4（TASK-0965）：砲門、塗裝（原木底＋兩道黑 wale、上部藍 frieze、黑舷頂、紅砲門框）、tableau（藍底金框）、船尾小艙窗
#   出處：calli-cosecha-01m/design/draft_ports.py（收穫號 階段三）；菱格與粉帶拿掉、換成本船的塗裝；船尾面的範圍讀 plan.paint.stern_x_max。
#   輸入：plan.json（ports／paint／stern）＋ 船殼（draft_lines.hull_volume 算的那一份 ⇒ 跟作品逐格相同，階段二結果帳證過）
#   輸出：masks/ports/carve.vox.txt（carvevox，帶刻之前的顏色守門）、masks/ports/paint.vox.txt（stampvox overwrite=1：換色）、
#         verify_ports.json、sheet03_ports_paint_v1.png
#   用法：python -I -X utf8 draft_ports.py <design> [--probe=skip_port=<層>:<序號>]   （probe：少開一個砲門重量，⛔ 不寫檔）
#   · 結構照 gura-tridente-01m/design/draft_ports.py（開口、reveal、船尾面的「從最後面往前那一段牆」、對稱取整的窗）；配色與菱格是本船的。
#   · TASK-1045：plan 有 paint.beakhead ⇒ beakhead 艙壁那一面（漆、門洞、圓窗）與平台頂面；門洞寫進 verify_ports.json 的 doors（draft_doors.py 讀）。
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
        if 'ref_x' in row:     # 從一段甲板的最高處量（追擊砲站的那一段；階段八：船尾最後那一階比 x 130 高 1 格，砲管頂到門楣）
            zc = max(int(LY.deck_z(plan, row['deck'], x + 0.5)) for x in range(row['ref_x'][0], row['ref_x'][1] + 1)) + row['sill']
        else:
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
    GOLD, BASE, BLACK, FRIEZE, REVEAL, GLASS = PA['gold'], PA['base'], PA['black'], PA['frieze'], PA['reveal'], PA['glass']
    SX = PA['stern_x_max']
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

    # ── 塗裝：外板那一層（dist ≤ 1）照高度換色；只換原木底（水線下灰白不動） ──
    outer = wall & (dist <= 1.0) & (col == BASE)
    paint = np.zeros(wall.shape, np.uint8)
    wtop = None
    for w in PA['wales']['rows']:
        lo, hi = wale_rows(plan, w, xs_all)
        inband = (zz >= lo[:, None]) & (zz <= hi[:, None])
        paint[outer & inband[:, None, :]] = w['color']
        wtop = hi if wtop is None else np.maximum(wtop, hi)
    # 上部 frieze：upper wale 頂上一格起、到舷頂下一格（藍）；舷頂最上一格黑（只照 x、z 算 ⇒ 兩舷對稱）
    topz = np.array([int(math.floor(float(L.top_z(x + 0.5)) + 0.5)) for x in xs_all])
    fr = (zz > wtop[:, None]) & (zz < topz[:, None])
    paint[outer & fr[:, None, :]] = FRIEZE
    # 舷頂：每個 x 船殼最高那一層的外板（v1 照折線四捨五入取 z，舷弧那幾段差一格 ⇒ 黑線斷斷續續；
    #   v2 取每個 (x, y) 的最上一格 ⇒ 內收的舷側每一階都算舷頂、滿身黑點）
    cap = np.zeros(wall.shape, bool)
    for xi in range(nx):
        zs_ = np.nonzero(wall[xi].any(axis=0))[0]
        if len(zs_):
            cap[xi, :, zs_[-1]] = outer[xi, :, zs_[-1]]
    paint[cap] = BLACK
    paint[ring] = REVEAL

    # ── 船尾面：每個 (y, z) 從最後面往前那一段牆 ──
    first = np.full((ny, nz), -1, int)
    for yi in range(ny):
        for z in range(nz):
            c = np.nonzero(wall[:, yi, z])[0]
            if len(c) and c[0] + x0 < SX:
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
    # tableau：wing transom 以上、船尾面那一層藍底；wing transom 那一列與舷頂下一列金
    zwt = int(plan['lines']['wing_transom_z']['v'])
    for yi in range(ny):
        for z in range(zwt, nz):
            f = first[yi, z]
            # 只塗船尾面那一層（f 在 x_aft 往前 2 格以內）—— v1 沒限制 ⇒ 船尾肩膀上的舷側格被塗成金點
            if f >= 0 and wall[f, yi, z] and f + x0 <= float(L.x_aft(z + 0.5)) + 2:
                paint[f, yi, z] = GOLD if (z == zwt or z == topz[f] - 1) else FRIEZE
    # ── TASK-1045 beakhead 艙壁那一面（Ship_Ends §3；plan 有 paint.beakhead 才做）：門洞整段牆刻穿；最前面那一層藍底、
    #    四周與舷頂下一列金、船首樓甲板那一列金、門框金、中間圓窗；平台頂面（切口下一格）甲板色、最外緣照舊黑 ──
    BK = PA.get('beakhead')
    doors = []
    if BK:
        bx, bz = int(plan['lines']['beakhead']['x']), int(plan['lines']['beakhead']['z'])
        T = int(plan['hull_build']['wall'])
        fi = bx - 1 - x0
        holes = []
        for d in BK['doors']:
            for sgn in (1, -1):
                ya, yb = sorted((YC + sgn * d['dy0'], YC + sgn * d['dy1']))
                z0d, z1d = d['z0'], d['z0'] + d['h'] - 1
                sl = (slice(bx - T - x0, bx - x0), slice(ya - ylo, yb - ylo + 1), slice(z0d, z1d + 1))
                carve[sl] |= wall[sl]
                holes.append((ya, yb, z0d, z1d))
                doors.append({'deck': d['deck'], 'face': 'fwd', 'y0': ya, 'y1': yb, 'z0': z0d, 'z1': z1d, 'door_x': bx,
                              'model_h': d['model_h'], 'model_z0': z0d})
        zf = np.nonzero(wall[fi].any(axis=0))[0]
        ztop = int(zf[-1])
        pw = BK['port']
        for z in range(bz, ztop):
            ys = np.nonzero(wall[fi, :, z])[0]
            if not len(ys):
                continue
            for yi in ys:
                y = yi + ylo
                c = BK['face_color']
                if yi in (ys[0], ys[-1]) or z in (ztop - 1, BK['line_z']):
                    c = GOLD
                for ya, yb, z0d, z1d in holes:
                    if ya - 1 <= y <= yb + 1 and z0d <= z <= z1d + 1:
                        c = GOLD
                rr = math.hypot(y - YC, z + 0.5 - pw['z'])
                if rr <= pw['r']:
                    c = pw['color']
                elif rr <= pw['r'] + 1:
                    c = GOLD
                paint[fi, yi, z] = c
        for xi in range(bx - x0, nx):
            ys = np.nonzero(wall[xi, :, bz - 1])[0]
            if len(ys) > 2:
                paint[xi, ys[1]:ys[-1], bz - 1] = BK['deck_color']
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
        blk = after[:max(1, SX - x0), w['y0'] - ylo:w['y1'] - ylo + 1, w['z0']:w['z1'] + 1]
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
    # wale 的高度裡、外板那一層還是原木色的（船頭朝前的面也算 —— 漏漆會在這裡現形）
    left_black = 0
    for w in PA['wales']['rows']:
        lo, hi = wale_rows(plan, w, xs_all)
        for xi in range(nx):
            m = after[xi, :, lo[xi]:hi[xi] + 1] & (dist[xi, :, lo[xi]:hi[xi] + 1] <= 1.0) & (acol[xi, :, lo[xi]:hi[xi] + 1] == BASE)
            left_black += int(m.sum())
    R['band_black_left'] = left_black
    R['mirror_diff'] = int((after != after[:, ::-1, :]).sum() + ((acol * after) != (acol * after)[:, ::-1, :]).sum())
    R['windows'] = windows
    R['ports_total'] = len(ports) * 2 + len(chasers)
    if BK:
        R['doors'] = doors
        R['door_holes_solid'] = int(sum(after[bx - T - x0:bx - x0, d['y0'] - ylo:d['y1'] - ylo + 1, d['z0']:d['z1'] + 1].sum() for d in doors))
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
    n1, h1 = dump(os.path.join(out, 'carve.vox.txt'), carve, col, '# 拉貝爾號 砲門與船尾開口（carvevox；第 4 欄 ＝ 刻之前的顏色，守門）\n')
    n2, h2 = dump(os.path.join(out, 'paint.vox.txt'), changes, acol, '# 拉貝爾號 塗裝（stampvox overwrite=1：換色；不含刻掉的格）\n')
    R['lists'] = {'carve': [n1, h1], 'paint': [n2, h2]}
    # 圖紙：右舷側面＋船尾正面
    sc = 4.0
    Wp = int(nx * sc) + 120 + int(ny * sc) + 80
    Hp = int(nz * sc) + 160
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((40, 16), '拉貝爾號 新圖紙 03：砲門、塗裝、船尾窗　v1　（frieze %d、金 %d、reveal %d、玻璃 %d）' % (FRIEZE, GOLD, REVEAL, GLASS), fill=(0, 0, 0), font=font(20))
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
