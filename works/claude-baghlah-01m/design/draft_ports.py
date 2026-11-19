# 出處：apex-two-galeon-01m/design/draft_ports.py（康塞普西翁號，TASK-0969）的開口／塗裝寫法 —— 改成星辰號（TASK-0019）
# 星辰號 新圖紙 02（TASK-0019 步驟 4）：船殼（draft_lines.hull_volume）＋ 砲門、水槽排水孔、船尾窗洞 ＋ 塗裝 ⇒ 落格用的最終船殼清單
#   輸入：plan.json（lines／hull_build／decks／ports／stern／paint）
#   輸出：masks/step4/hull4_NN.vox.txt（stampvox at 0,0,0；作品還沒有格 ⇒ 開口直接不放、顏色直接是塗好的，不用先貼再刻）、
#         verify_ports.json、sheet02_ports_paint_v1.png
#   用法：python -X utf8 draft_ports.py <design> [--probe=port_dx=+3] [--no-write]
#   · 跟康塞普西翁號不同：它是船殼已經雕好之後再 carvevox 刻砲門、stampvox overwrite 換色；星辰號還沒落格 ⇒ 一張清單一次落完。
#   · 船尾窗洞：每個 (y, z) 從船尾往前第一格起那一段連續的牆整段刻穿（看得進艙裡）；玻璃與窗框留給步驟 6。
#   · --probe：反向對照（砲門在設計裡整排挪 dx 格，量到的砲門位置要報 dx；⛔ 不寫檔）。
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb

SIDE_DY = 6        # 砲門、排水孔只開在 |dy| ≥ 6 的牆（兩舷），不碰中線附近的龍骨與艏柱
FACE_X_MAX = 60    # 船尾面：從船尾往前第一格的 x 要小於這個才算船尾面


def build(plan, port_dx=0):
    L = HL.Lines(plan)
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist)
    nx, ny, nz = wall.shape
    dy_of = np.arange(ny) + ylo - YC
    xs_all = np.arange(nx) + x0
    zz = np.arange(nz)[None, :]
    side = (np.abs(dy_of) >= SIDE_DY)[None, :, None]

    ports = LY.ports(plan)
    for p in ports:
        p['x0'] += port_dx
        p['x1'] += port_dx
    holes = np.zeros(wall.shape, bool)
    ring = np.zeros(wall.shape, bool)
    per_port = []
    for p in ports:
        xs = slice(p['x0'] - x0, p['x1'] - x0 + 1)
        zs = slice(p['z0'], p['z1'] + 1)
        cut = np.zeros(wall.shape, bool)
        cut[xs, :, zs] = wall[xs, :, zs]
        cut &= side
        holes |= cut
        xr = slice(p['x0'] - 1 - x0, p['x1'] + 2 - x0)
        zr = slice(p['z0'] - 1, p['z1'] + 2)
        ring[xr, :, zr] |= wall[xr, :, zr]
        per_port.append({'i': p['i'], 'x': [p['x0'], p['x1']], 'z': [p['z0'], p['z1']],
                         'cut_P': int(cut[:, dy_of < 0, :].sum()), 'cut_S': int(cut[:, dy_of > 0, :].sum())})
    ring &= side & ~holes
    scup = LY.scuppers(plan)
    per_scup = []
    for s in scup:
        cut = np.zeros(wall.shape, bool)
        cut[s['x0'] - x0:s['x1'] - x0 + 1, :, s['z0']:s['z1'] + 1] = wall[s['x0'] - x0:s['x1'] - x0 + 1, :, s['z0']:s['z1'] + 1]
        cut &= side
        holes |= cut
        per_scup.append({'i': s['i'], 'x': [s['x0'], s['x1']], 'z': [s['z0'], s['z1']],
                         'cut_P': int(cut[:, dy_of < 0, :].sum()), 'cut_S': int(cut[:, dy_of > 0, :].sum())})
    ring &= ~holes

    # 船尾窗：每個 (y, z) 從船尾往前那一段連續的牆整段刻穿
    wins = LY.stern_windows(plan, YC)
    per_win = []
    for w in wins:
        n0 = int(holes.sum())
        for y in range(w['y0'], w['y1'] + 1):
            yi = y - ylo
            for z in range(w['z0'], w['z1'] + 1):
                c = np.nonzero(wall[:, yi, z])[0]
                if not len(c) or c[0] + x0 >= FACE_X_MAX:
                    continue
                xi = c[0]
                while xi < nx and wall[xi, yi, z]:
                    holes[xi, yi, z] = True
                    xi += 1
        per_win.append({'j': w['j'], 'y': [w['y0'], w['y1']], 'z': [w['z0'], w['z1']], 'cut': int(holes.sum()) - n0})

    # 塗裝
    PA = plan['paint']
    HB = plan['hull_build']
    outer = wall & (dist <= 1.0)
    teak = outer & (col == HB['side_color'])
    paint = np.zeros(wall.shape, np.uint8)
    W = PA['wale']
    lo = (LY.deck_z(plan, W['deck'], xs_all + 0.5, well=False) + W['dz']).astype(int)
    band = (zz >= lo[:, None]) & (zz <= lo[:, None] + W['h'] - 1)
    paint[teak & band[:, None, :]] = PA['black']
    SF = PA['stern_face']
    xp = np.array([float(L.x_post(z + 0.5)) for z in range(nz)])
    behind = ((xs_all[:, None] + 0.5) < xp[None, :]) & (zz >= SF['z_from'])
    paint[teak & behind[:, None, :]] = SF['color']
    # 舷頂：上面一格不在船裡、而且離那一欄（x）最高的格不到 2 格 ⇒ 船尾樓往裡收的舷側那些台階邊緣不算（v1 塗成一片黑點）
    above = np.zeros(S.shape, bool)
    above[:, :, :-1] = S[:, :, 1:]
    top_x = np.array([np.nonzero(S[xi].any(axis=0))[0][-1] if S[xi].any() else -9 for xi in range(nx)])
    cap = wall & ~above & (zz >= top_x[:, None] - 1)[:, None, :]
    paint[cap] = PA['rail_cap']
    paint[ring] = PA['port_ring']

    keep = wall & ~holes
    final = np.where(paint > 0, paint, col).astype(np.uint8)
    final[~keep] = 0
    return {'L': L, 'x0': x0, 'ylo': ylo, 'S': S, 'wall': wall, 'keep': keep, 'final': final, 'holes': holes, 'ring': ring, 'cap': cap,
            'ports': ports, 'per_port': per_port, 'scuppers': per_scup, 'windows': wins, 'per_win': per_win}


def measure_ports(B, plan):
    """從格子量砲門（不看設計清單）：每門在 z 中心、每一舷最外那一層，往前後找連續的空欄 ⇒ 量到的 x 範圍、跟 plan 的差。"""
    keep, x0, ylo, L = B['keep'], B['x0'], B['ylo'], B['L']
    out = []
    for p in LY.ports(plan):
        zc = (p['z0'] + p['z1']) // 2
        xc = (p['x0'] + p['x1']) // 2
        row = {'i': p['i'], 'plan_x': [p['x0'], p['x1']]}
        for nm, sg in (('P', -1), ('S', 1)):
            ys = np.arange(keep.shape[1]) + ylo - L.YC
            sel = ys * sg >= SIDE_DY

            def open_at(x):
                return not keep[x - x0, sel, zc].any()
            # 從 plan 的中心往兩邊找第一個「空」的欄（反向對照時中心可能已經是牆）
            start = next((x for d in range(0, 12) for x in (xc + d, xc - d) if open_at(x)), None)
            if start is None:
                row[nm] = None
                continue
            a = start
            while open_at(a - 1):
                a -= 1
            b = start
            while open_at(b + 1):
                b += 1
            row[nm] = [a, b, a - p['x0'], b - p['x1']]
        out.append(row)
    return out


def readings(B, plan):
    keep, final, wall, L = B['keep'], B['final'], B['wall'], B['L']
    lab, ncomp = ndimage.label(keep)
    filled = ndimage.binary_fill_holes(keep)
    cav = int((filled & ~keep).sum())
    mir = int((final != final[:, ::-1, :]).sum())
    cols = {int(c): int(n) for c, n in zip(*np.unique(final[keep], return_counts=True))}
    mp = measure_ports(B, plan)
    worst = max(max(abs(r[s][2]), abs(r[s][3])) for r in mp for s in ('P', 'S') if r[s])
    # 開口是不是穿透：砲門中心那一格、整段 |dy| ≥ 6 的牆都要空
    x0, ylo = B['x0'], B['ylo']
    ys = np.arange(keep.shape[1]) + ylo - L.YC
    through = 0
    for p in B['ports']:
        xc, zc = (p['x0'] + p['x1']) // 2, (p['z0'] + p['z1']) // 2
        through += int(not keep[xc - x0, np.abs(ys) >= SIDE_DY, zc].any())
    win_through = 0
    for w in B['windows']:
        yc, zc = (w['y0'] + w['y1']) // 2, (w['z0'] + w['z1']) // 2
        col_ = keep[:, yc - ylo, zc]
        xs_ = np.nonzero(B['wall'][:, yc - ylo, zc])[0]
        first_run = []
        for xi in xs_:
            if first_run and xi != first_run[-1] + 1:
                break
            first_run.append(xi)
        win_through += int(not col_[first_run].any())
    return {
        'wall_cells_step3': int(wall.sum()), 'opened_cells': int(B['holes'].sum()), 'cells': int(keep.sum()),
        'colors': cols, 'components_6': int(ncomp), 'cavity_cells': cav, 'mirror_diff_cells': mir,
        'ports_per_side': len(B['ports']), 'ports_through_both_sides': through,
        'windows': len(B['windows']), 'windows_through': win_through,
        'ring_cells': int((B['ring'] & keep).sum()), 'cap_cells': int((B['cap'] & keep).sum()),
        'ports_measured_worst_dx': worst, 'ports_measured': mp,
        'per_port': B['per_port'], 'scuppers': B['scuppers'], 'per_window': B['per_win'],
        'bbox': {'x': [int(B['x0'] + np.nonzero(keep.any(axis=(1, 2)))[0][[0, -1]][k]) for k in (0, 1)],
                 'y': [int(B['ylo'] + np.nonzero(keep.any(axis=(0, 2)))[0][[0, -1]][k]) for k in (0, 1)],
                 'z': [int(np.nonzero(keep.any(axis=(0, 1)))[0][[0, -1]][k]) for k in (0, 1)]},
    }


def draw(plan, B, R, path):
    keep, final, x0, ylo = B['keep'], B['final'], B['x0'], B['ylo']
    nx, ny, nz = keep.shape
    sc = 3
    padL, padT = 60, 90
    Wp = nx * sc + padL * 2 + 120
    Hp = padT + nz * sc + 80 + nz * sc + 80 + 360
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((padL, 20), plan['title'].split(',')[0] + ', new sheet 02:  ports, scuppers, stern windows, paint  v1', fill=(20, 20, 20), font=font(22))
    d.text((padL, 52), '0.1 m/cell   profile seen from port side (-y), bow to the right; stern elevation seen from aft', fill=(60, 60, 60), font=font(14))
    # 1 側面：每個 (x, z) 從 −y 往裡第一格的顏色；開口處看得到對面那一舷的內板
    oy = padT
    for xi in range(nx):
        for z in range(nz):
            c = np.nonzero(keep[xi, :, z])[0]
            if len(c):
                X, Y = padL + xi * sc, oy + (nz - 1 - z) * sc
                d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=palette_rgb(int(final[xi, c[0], z])))
    for p in B['ports']:
        X = padL + ((p['x0'] + p['x1']) / 2.0 - x0) * sc
        d.text((X - 4, oy + (nz - 1 - p['z1']) * sc - 30), str(p['i']), fill=(150, 0, 0), font=font(12))
    for x in range((x0 // 50 + 1) * 50, x0 + nx, 50):
        X = padL + (x - x0) * sc
        d.line([X, oy + nz * sc, X, oy + nz * sc + 6], fill=(0, 0, 0))
        d.text((X - 10, oy + nz * sc + 8), str(x), fill=(80, 80, 80), font=font(12))
    d.text((padL, oy - 20), '1 Profile: 11 ports a side (4-pdr, 0.5 m square), 2 scuppers a side in the fore well', fill=(0, 0, 0), font=font(14))
    # 2 船尾正面：每個 (y, z) 從船尾往前第一格
    oy2 = oy + nz * sc + 80
    cx = Wp // 2
    sc2 = 6
    for yi in range(ny):
        for z in range(nz):
            c = np.nonzero(keep[:, yi, z])[0]
            if len(c) and c[0] + x0 < FACE_X_MAX + 40:
                X, Y = cx + (yi + ylo - B['L'].YC) * sc2, oy2 + (nz - 1 - z) * sc2 // 2
                d.rectangle([X, Y, X + sc2 - 1, Y + sc2 // 2 - 1], fill=palette_rgb(int(final[c[0], yi, z])))
    d.text((padL, oy2 - 20), '2 Stern elevation (y x6, z x3): 5 windows cut through to the cabin; glass and frames come in step 6', fill=(0, 0, 0), font=font(14))
    # 3 讀數
    oy3 = oy2 + nz * sc2 // 2 + 30
    rows = [
        ('Cells', '%s (step-3 wall %s, opened %s)' % (format(R['cells'], ','), format(R['wall_cells_step3'], ','), format(R['opened_cells'], ','))),
        ('Colours', ', '.join('%d: %s' % (k, format(v, ',')) for k, v in sorted(R['colors'].items()))),
        ('Structure', 'components %d, cavities %d, mirror diff %d' % (R['components_6'], R['cavity_cells'], R['mirror_diff_cells'])),
        ('Ports through both sides', '%d / %d' % (R['ports_through_both_sides'], R['ports_per_side'])),
        ('Stern windows through', '%d / %d' % (R['windows_through'], R['windows'])),
        ('Ports measured from cells vs plan', 'worst |dx| %d' % R['ports_measured_worst_dx']),
        ('Paint', 'teak 136 sides, white 182 bottom + port rings, black 36 rail cap / wale / stern face'),
    ]
    for i, (k, v) in enumerate(rows):
        d.text((padL, oy3 + i * 22), k, fill=(40, 40, 40), font=font(14))
        d.text((padL + 320, oy3 + i * 22), v, fill=(0, 0, 0), font=font(14))
    d.text((padL, oy3 + len(rows) * 22 + 10), 'Provenance: plan.json ports / stern / paint src fields.', fill=(90, 90, 90), font=font(12))
    im.save(path, optimize=False)


def write_lists(out_dir, B, chunk=250000):
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith('.vox.txt'):
            os.remove(os.path.join(out_dir, f))
    keep, final, x0, ylo = B['keep'], B['final'], B['x0'], B['ylo']
    idx = np.argwhere(keep)
    idx = idx[np.lexsort((idx[:, 2], idx[:, 1], idx[:, 0]))]
    files = []
    for k in range(0, len(idx), chunk):
        part = idx[k:k + chunk]
        name = 'hull4_%02d.vox.txt' % (k // chunk + 1)
        p = os.path.join(out_dir, name)
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 星辰號 船殼 步驟 4（draft_ports.py：線形＋砲門＋排水孔＋船尾窗洞＋塗裝）—— x,y,z,color；at 0,0,0\n')
            for (xi, yi, z) in part:
                f.write('%d,%d,%d,%d\n' % (xi + x0, yi + ylo, z, final[xi, yi, z]))
        files.append({'file': name, 'cells': int(len(part)), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()})
    return files


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    dx = 0
    if probe:
        k, v = probe[0].split('=')
        assert k == 'port_dx'
        dx = int(v)
    B = build(plan, port_dx=dx)
    R = readings(B, plan)
    if probe or '--no-write' in sys.argv:
        print(json.dumps({k: v for k, v in R.items() if k not in ('ports_measured', 'per_port', 'scuppers', 'per_window')}, ensure_ascii=False))
        if probe:
            print('measured', json.dumps(R['ports_measured'][:3]))
        return
    files = write_lists(os.path.join(design, 'masks', 'step4'), B)
    R['lists'] = files
    draw(plan, B, R, os.path.join(design, 'sheet02_ports_paint_v1.png'))
    with open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('ports_measured', 'per_port', 'scuppers', 'per_window')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
