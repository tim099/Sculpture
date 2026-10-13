# 新圖紙 05 底肋・keelson v1（階段四，TASK-0538）：plan.json floors ⇒ 每片底肋與 keelson 的 3D 格子清單、Pl. LI 對照圖、verify_floors.json。
# 用法：python -I draft_floors.py <design 資料夾>
#   · 清單給 `sculpture op=stampvox at=0,0,0`；底肋片片互不重疊，也不跟 keelson、階段一～三重疊。
#   · 一格屬於底肋：格中心在船殼 molded 裡、半寬 ≤ narrowing（底肋頭），而且「在 A 以下」或「離 molded 線 ≤ moulded」；
#     中線 5 格（|y−160| ≤ 2）A 以上一律歸 keelson。A、B、narrowing 都是每一欄（x 格）自己的值。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_lines as DL   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def interp_tab(B, key, col):
    a = np.array(B[key][col], float)
    return lambda x: float(np.interp(x, a[:, 0], a[:, 1]))


class HullGrid:
    """船殼半寬表的雙線性內插（nan ＝ 船殼外）＋ 某個 x 的 molded 剖面折線"""
    def __init__(s, xs, zs, T):
        s.xs, s.zs, s.T = xs, zs, np.nan_to_num(T, nan=-1.0)

    def column(s, x):
        i = np.clip(np.searchsorted(s.xs, x) - 1, 0, len(s.xs) - 2)
        t = (x - s.xs[i]) / (s.xs[i + 1] - s.xs[i])
        a, b = s.T[:, i], s.T[:, i + 1]
        out = a * (1 - t) + b * t                                # 每個 zs 的 hb（< 0 ＝ 外面）
        out[(a < 0) | (b < 0)] = -1.0                            # 兩欄有一欄在外面就算外面（夾著 −1 會內插出假的小半寬）
        return out

    def section(s, x):
        c = s.column(x)
        ok = c >= 0
        return np.c_[c[ok], s.zs[ok]]


def build(plan, R, B, ship, X0, Zk, cpm, xs, zs, T, occupied):
    F = plan['floors']
    A = interp_tab(B, 'line_A_cutting_down', 'x_z')
    Bk = interp_tab(B, 'line_B_keelson_top', 'x_z')
    N = interp_tab(B, 'narrowing_line', 'x_hb')
    st = plan['hull']['stations_x']
    xk0, xk1 = st[F['keelson']['x'][0].split()[1]], st[F['keelson']['x'][1].split()[1]]
    hg = HullGrid(xs, zs, T)
    mould = F['moulded_cells'] / cpm
    floors = {}
    for n in range(F['n'][0], F['n'][1] + 1):
        xf = F['frame_x0'] + n * F['frame_spacing']
        Xf = X0 + xf * cpm
        i0 = int(round(Xf - F['sided_cells'] / 2.0))
        cells = []
        for Xc in range(i0, i0 + F['sided_cells']):
            x = (Xc + 0.5 - X0) / cpm
            col = hg.column(x)
            sec = hg.section(x)
            a, nh = A(x), N(x)
            for Zc in range(int(Zk), int(Zk + 4.0 * cpm)):
                z = (Zc + 0.5 - Zk) / cpm
                hb_z = float(np.interp(z, zs, col))
                if hb_z < 0:
                    continue
                for dy in range(0, int(hb_z * cpm) + 2):
                    h = dy / cpm
                    if h > hb_z or h > nh:
                        continue
                    if dy <= 2 and z > a:
                        continue                                 # keelson 的
                    if z > a:
                        d = np.min(np.hypot(sec[:, 0] - h, sec[:, 1] - z))
                        if d > mould:
                            continue
                    for y in ({160 + dy, 160 - dy}):
                        if (Xc, y, Zc) not in occupied:
                            cells.append((Xc, y, Zc, F['color']))
        floors[n] = {'x_frame': round(xf, 4), 'X_frame': round(Xf, 3), 'X_cells': [i0, i0 + F['sided_cells'] - 1], 'cells': cells}
    # keelson：16 號站到 M 站、A 到 B、中線 5 格
    K = F['keelson']
    kc = []
    for Xc in range(int(X0 + xk0 * cpm) - 1, int(X0 + xk1 * cpm) + 2):
        x = (Xc + 0.5 - X0) / cpm
        if not (xk0 < x < xk1):
            continue
        a, b = A(x), Bk(x)
        for Zc in range(int(Zk), int(Zk + 3.0 * cpm)):
            z = (Zc + 0.5 - Zk) / cpm
            if a < z <= b:
                for y in range(K['y'][0], K['y'][1] + 1):
                    kc.append((Xc, y, Zc, K['color']))
    return floors, kc, (A, Bk, N, hg, xk0, xk1)


def main():
    design = sys.argv[1]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Sc = plan['scale']
    X0, Zk = Sc['X_of_x0'], Sc['Z_of_keel_top']
    prev = set()
    for sub, parts in (('keel', ('shoe', 'keel')), ('posts', ('sternpost', 'inner_post', 'stem', 'gripe')),
                       ('deadwood', ('aft_deadwood', 'fore_deadwood', 'apron'))):
        for p in parts:
            for ln in open(os.path.join(design, 'masks', sub, p + '.vox.txt'), encoding='utf-8'):
                if ln.strip() and not ln.startswith('#'):
                    prev.add(tuple(int(v) for v in ln.split(',')[:3]))
    floors, kc, (A, Bk, N, hg, xk0, xk1) = build(plan, R, B, ship, X0, Zk, cpm, xs, zs, T, prev)

    mdir = os.path.join(design, 'masks', 'floors')
    os.makedirs(mdir, exist_ok=True)
    ver = {'k': round(k, 5), 'floors': {}, 'keelson': {}}
    seen = set()

    def write(name, cl):
        with open(os.path.join(mdir, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 夜燈號 {name}（新圖紙 05 v1，draft_floors.py 產）—— x,y,z,color；stampvox at=0,0,0\n')
            for c in cl:
                f.write('%d,%d,%d,%d\n' % c)

    kxyz = {(a, b, c) for a, b, c, _ in kc}
    assert len(kxyz) == len(kc) and not (kxyz & prev), 'keelson 重複或跟前面重疊'
    seen |= kxyz
    write('keelson', kc)
    ka = np.array(sorted(kxyz))
    ver['keelson'] = {'file': 'masks/floors/keelson.vox.txt', 'cells': len(kc), 'x': [int(ka[:, 0].min()), int(ka[:, 0].max())],
                      'z': [int(ka[:, 2].min()), int(ka[:, 2].max())], 'x_plate': [xk0, xk1]}
    total = 0
    for n, f in floors.items():
        cl = f['cells']
        xyz = {(a, b, c) for a, b, c, _ in cl}
        assert len(xyz) == len(cl), f'f{n:+03d} 有重複格'
        assert not (xyz & seen), f'f{n:+03d} 跟 keelson／別片重疊'
        seen |= xyz
        name = 'f%+03d' % n
        write(name, cl)
        a = np.array(sorted(xyz))
        dy = np.abs(a[:, 1] - 160)
        mir = sum(1 for (x, y, z) in xyz if (x, 320 - y, z) not in xyz)
        ver['floors'][name] = {'file': f'masks/floors/{name}.vox.txt', 'cells': len(cl), 'x_frame_plate': f['x_frame'], 'X_frame': f['X_frame'],
                               'X_cells': f['X_cells'], 'z': [int(a[:, 2].min()), int(a[:, 2].max())],
                               'head_dy_max': int(dy.max()), 'head_plate_m': round(N(f['x_frame']), 3), 'mirror_missing': mir}
        total += len(cl)
    ver['floor_cells_total'] = total
    ver['n_floors'] = len(floors)
    # 接合：跟階段一～三一起 6 連通
    allc = seen | prev
    from collections import deque
    s0 = next(iter(allc))
    q, vis = deque([s0]), {s0}
    while q:
        c = q.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            nb = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
            if nb in allc and nb not in vis:
                vis.add(nb)
                q.append(nb)
    ver['connected_all'] = {'cells': len(allc), 'reached_from_one': len(vis)}
    # keelson 坐在底肋上：每片底肋那幾欄，keelson 底下那一格是不是底肋
    seat = {'checked': 0, 'gaps': []}
    fl = {}
    for n, f in floors.items():
        for (x, y, z, c) in f['cells']:
            fl[(x, y, z)] = n
    for n, f in floors.items():
        for Xc in range(f['X_cells'][0], f['X_cells'][1] + 1):
            zk = min(z for (x, y, z) in kxyz if x == Xc and y == 160)
            seat['checked'] += 1
            if (Xc, 160, zk - 1) not in fl:
                seat['gaps'].append([Xc, zk])
    ver['keelson_seat'] = seat

    # ── 對照圖一：側面（中線 y 160）疊 Pl. LI
    base = Image.open(os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768',
                                   'PlLI_Engelsk_Ostindiefarare.tif')).convert('L')
    pxm, x0p, kt = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']
    toP = lambda Xc, Zc: (x0p + (Xc - X0) / cpm * pxm, kt - (Zc - Zk) / cpm * pxm)
    prof = {}
    for (x, y, z) in seen:
        if y == 160:
            prof[(x, z)] = 209 if (x, y, z) in kxyz else 141
    px0, py0, px1, py1, sc = 3000, 6300, 9600, 6800, 0.3
    Aim = base.crop((px0, py0, px1, py1)).resize((int((px1 - px0) * sc), int((py1 - py0) * sc)), Image.LANCZOS).convert('RGBA')
    ov = Image.new('RGBA', Aim.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for (x, z), c in prof.items():
        a0, a1 = toP(x, z + 1), toP(x + 1, z)
        d.rectangle([(a0[0] - px0) * sc, (a0[1] - py0) * sc, (a1[0] - px0) * sc, (a1[1] - py0) * sc],
                    fill=(0, 150, 60, 90) if c == 209 else (200, 0, 160, 110))
    Aim = Image.alpha_composite(Aim, ov).convert('RGB')
    Aim.save(os.path.join(design, 'compare05_floors_profile_v1.png'))
    # ── 對照圖二：落在船尾站上的幾片（Ø、4、8、12、16 號站 ＝ 肋位 0、−4、−8、−12、−16 —— −16 不在範圍）疊橫切面圖左半
    bpc, bpk = B['body_plan']['centre_px'], B['body_plan']['keel_top_py']
    bx0, by0, bx1, by1, s3 = 7450, 3300, 8720, 4130, 0.8
    Bm = base.crop((bx0, by0, bx1, by1)).resize((int((bx1 - bx0) * s3), int((by1 - by0) * s3)), Image.LANCZOS).convert('RGBA')
    ov = Image.new('RGBA', Bm.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cols = {0: (220, 0, 0, 120), -4: (0, 120, 220, 120), -8: (0, 160, 60, 120), -12: (200, 120, 0, 140)}
    for n, colr in cols.items():
        f = floors[n]
        Xc = f['X_cells'][0] + 1                                  # 這一片中間那一欄
        for (x, y, z, c) in f['cells']:
            if x != Xc or y > 160:
                continue
            h0 = (160 - y) / cpm - 0.5 / cpm
            h1 = h0 + 1 / cpm
            z0 = (z - Zk) / cpm
            z1 = z0 + 1 / cpm
            d.rectangle([(bpc - h1 * pxm - bx0) * s3, (bpk - z1 * pxm - by0) * s3, (bpc - h0 * pxm - bx0) * s3, (bpk - z0 * pxm - by0) * s3], fill=colr)
    Bm = Image.alpha_composite(Bm, ov).convert('RGB')
    Bm.save(os.path.join(design, 'compare05_floors_body_v1.png'))
    ver['outputs'] = ['compare05_floors_profile_v1.png', 'compare05_floors_body_v1.png']
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1, default=lambda v: v.item())
    open(os.path.join(design, 'verify_floors.json'), 'w', encoding='utf-8').write(dump(ver))
    print(dump({kk: v for kk, v in ver.items() if kk != 'floors'}))
    for name in list(ver['floors'])[::5]:
        print(name, ver['floors'][name])


if __name__ == '__main__':
    main()
