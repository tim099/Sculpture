# 拿破崙號 階段三（TASK-0608）：砲門三層、塗裝（黑底＋兩層砲列各一條白帶、黑砲門蓋、舷頂一條金）、圓船尾的窗
#   抄自三叉戟號 gura-tridente-01m/design/draft_ports.py（gura，TASK-0556）；改：帶子只畫有 band 的層、砲門框跟帶同色、舷頂金線、船尾窗的範圍
#   輸入：plan.json（ports／paint／stern）＋ 船殼（draft_lines.hull_volume 算的那一份 ⇒ 跟作品逐格相同，階段二結果帳證過；這裡另外拿作品匯出再比一次）
#   輸出：masks/ports/carve.vox.txt（carvevox，帶顏色守門）、masks/ports/paint.vox.txt（stampvox overwrite=1：換色）、verify_ports.json、sheet03_ports_paint_v1.png
#   用法：python -I -X utf8 draft_ports.py <design> [--probe skip_port=<層>:<序號>]   （probe：少開一個砲門重量，⛔ 不寫檔）
import sys, os, json, math, hashlib, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb


def export_work(mark):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=kotoko-napoleon-01m',
                            '--arg', 'out=' + out, '--arg', 'links=none', '--arg', 'mark=' + mark], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-600:])
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def band_rows(plan, tier, x):
    """那一層砲門的白帶：z 範圍（含端點）＝ 砲門下緣 − 2 .. 上緣 ＋ 2（照甲板舷弧）。"""
    zc = int(LY.deck_z(plan, tier['deck'], x))
    lo = zc + tier['sill'] - 2
    return lo, lo + tier['h'] + 3


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist, x0, ylo)
    PA = plan['paint']
    RED, BLACK, GOLD, GLASS = PA['band'], PA['base'], PA['gold'], PA['glass']   # RED ＝ 帶子的顏色（拿破崙號是白）
    nx, ny, nz = wall.shape
    dy_of = np.arange(ny) + ylo - YC

    ports = LY.ports(plan)
    skip = None
    if probe:
        k, i = probe[0].split('=')[1].split(':')
        skip = (k, int(i))
    carve = np.zeros(wall.shape, bool)
    ring = np.zeros(wall.shape, bool)
    banded = set(PA['banded'])
    for p in ports:
        if skip and (p['deck'], p['i']) == skip:
            continue
        for side in (1, -1):
            ysel = (dy_of * side) >= 6
            xs = slice(p['x0'] - x0, p['x1'] - x0 + 1)
            zs = slice(p['z0'], p['z1'] + 1)
            carve[xs, :, zs] |= wall[xs, :, zs] & ysel[None, :, None]
            if p['deck'] in banded:
                xr = slice(p['x0'] - 1 - x0, p['x1'] + 2 - x0)
                zr = slice(p['z0'] - 1, p['z1'] + 2)
                ring[xr, :, zr] |= wall[xr, :, zr] & ysel[None, :, None]
    ring &= ~carve

    # ── 塗裝：外板那一層（dist ≤ 1）照高度換色；只換黑 36（銅底不動） ──
    outer = wall & (dist <= 1.0) & (col == BLACK)
    # 拿破崙號改：帶子只漆「朝舷外」的外板（往外那一格是空的）—— 圓船尾的轉角那一段外板幾乎是水平的，
    #   v1 照高度漆 ⇒ 從船尾斜上方看，白帶底下一片白斑（stage3 sternq 第一版）
    Sp = np.pad(S, ((0, 0), (1, 1), (0, 0)))                 # Sp[:, yi + 1] ＝ S[:, yi]
    side_face = ((dy_of > 0)[None, :, None] & ~Sp[:, 2:, :]) | ((dy_of < 0)[None, :, None] & ~Sp[:, :-2, :])
    band_outer = outer & side_face
    paint = np.zeros(wall.shape, np.uint8)
    xs_all = np.arange(nx) + x0
    for t in plan['ports']['tiers']:
        if t['deck'] not in banded:
            continue
        ps = [p for p in ports if p['deck'] == t['deck']]
        lo = np.array([band_rows(plan, t, x)[0] for x in xs_all])
        hi = lo + t['h'] + 3
        zz = np.arange(nz)[None, :]
        inx = (xs_all >= ps[0]['x0'] - PA['band_overrun']) & (xs_all <= ps[-1]['x1'] + PA['band_overrun'])
        inband = (zz >= lo[:, None]) & (zz <= hi[:, None]) & inx[:, None]
        paint[band_outer & inband[:, None, :]] = RED
    paint[ring] = RED
    # 舷頂一條金（LEBRETON：欄杆 ochre）：每一站（x）牆最高那一層（整個牆厚）＋外板再往下一格
    #   （v1 用「每一欄 (x, y) 最上面那一格」⇒ tumblehome 的外板每一欄都有自己的頂，側面畫出一圈圈金色等高線）
    zz3 = np.broadcast_to(np.arange(nz)[None, None, :], wall.shape)
    anyz = wall.any(axis=1)
    topx = np.where(anyz.any(axis=1), nz - 1 - np.argmax(anyz[:, ::-1], axis=1), -1)
    cap = wall & (zz3 == topx[:, None, None])
    cap |= wall & (dist <= 1.0) & (zz3 == topx[:, None, None] - 1)
    paint[cap] = GOLD

    # ── 船尾窗：船尾面（每個 (y, z) 從最後面往前那一段牆）——
    ST = plan['stern']
    glass = np.zeros(wall.shape, bool)
    frame = np.zeros(wall.shape, bool)
    stern_open = np.zeros(wall.shape, bool)
    first = np.full((ny, nz), -1, int)
    for yi in range(ny):
        for z in range(nz):
            c = np.nonzero(wall[:, yi, z])[0]
            if len(c) and c[0] + x0 < ST['x_max']:
                first[yi, z] = c[0]
    windows = []
    for row in ST['rows']:
        zc = int(LY.deck_z(plan, row['deck'], ST['x_ref'])) + row['sill']
        n, w, h, half = row['n'], row['w'], row['h'], row['half']
        assert w % 2 == 1, '船尾窗寬要奇數（才能對中線對稱）'
        cs = np.linspace(-half + w / 2.0, half - w / 2.0, n)
        for j, c in enumerate(cs):
            k = int(math.floor(abs(c) + 0.5)) * (1 if c >= 0 else -1)   # 對稱取整（±c 取到 ±k）；寬一律奇數 ⇒ 中間那個窗以第 YC 格為中心
            y0 = YC + k - (w - 1) // 2
            kind = 'port' if j + 1 in row.get('ports', []) else 'window'
            windows.append({'deck': row['deck'], 'j': j + 1, 'y0': y0, 'y1': y0 + w - 1, 'z0': zc, 'z1': zc + h - 1, 'kind': kind})
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
    # 換色只留「真的會變」的格
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
    # 船頭朝前的面：帶子高度裡、外板那一層還是黑的（ember 補漆那一課）
    left_black = 0
    for t in plan['ports']['tiers']:
        if t['deck'] not in banded:
            continue
        ps = [p for p in ports if p['deck'] == t['deck']]
        for xi in range(nx):
            if not (ps[0]['x0'] - PA['band_overrun'] <= xi + x0 <= ps[-1]['x1'] + PA['band_overrun']):
                continue
            lo, hi = band_rows(plan, t, xi + x0)
            m = after[xi, :, lo:hi + 1] & side_face[xi, :, lo:hi + 1] & (dist[xi, :, lo:hi + 1] <= 1.0) & (acol[xi, :, lo:hi + 1] == BLACK)
            left_black += int(m.sum())
    R['band_black_left'] = left_black
    R['mirror_diff'] = int((after != after[:, ::-1, :]).sum() + ((acol * after) != (acol * after)[:, ::-1, :]).sum())
    R['windows'] = windows
    R['ports'] = len(ports) * 2
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
    n1, h1 = dump(os.path.join(out, 'carve.vox.txt'), carve, col, '# 拿破崙號 砲門與船尾開口（carvevox；第 4 欄 ＝ 刻之前的顏色，守門）\n')
    n2, h2 = dump(os.path.join(out, 'paint.vox.txt'), changes, acol, '# 拿破崙號 塗裝（stampvox overwrite=1：換色；不含刻掉的格）\n')
    R['lists'] = {'carve': [n1, h1], 'paint': [n2, h2]}
    # 圖紙：右舷側面＋船尾正面
    sc = 1.4
    Wp = int(nx * sc) + 120 + int(ny * sc) + 80
    Hp = int(nz * sc) + 220
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((40, 16), '拿破崙號 新圖紙 03：砲門三層、塗裝、圓船尾的窗　v1　（帶 %d、黑 %d、金 %d、玻璃 %d）' % (RED, BLACK, GOLD, GLASS), fill=(0, 0, 0), font=font(20))
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
    d.text((40, oy + nz * sc + 10), '右舷側面（船頭在右）　　船尾正面（從船尾看，左手 ＝ −y ＝ 左舷 P）　出處：plan.json paint／stern 的 src', fill=(40, 40, 40), font=font(14))
    d.text((40, oy + nz * sc + 34), '刻 %d 格、換色 %d 格；開口看不穿的 %d 個；帶子高度裡外板還是黑的 %d 格；鏡像差 %d' % (
        R['carve_cells'], R['paint_cells'], len(see), left_black, R['mirror_diff']), fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet03_ports_paint_v1.png'))
    with open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'windows'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
