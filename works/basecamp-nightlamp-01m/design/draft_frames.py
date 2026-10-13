# 新圖紙 06 方肋骨 v1（階段五，TASK-0538）：plan.json frames ⇒ 每片肋骨的 3D 格子清單、Pl. LI 對照圖、verify_frames.json。
# 用法：python -I draft_frames.py <design 資料夾>
#   · 清單給 `sculpture op=stampvox at=0,0,0`；片片互不重疊，也不跟階段一～四重疊。
#   · 一格屬於肋骨：同一片肋位（跟底肋同一組 x 欄）、格中心在船殼 molded 裡、離 molded 線 ≤ moulded(z)、高度 ≤ 舷牆頂，
#     而且「高過底肋頭的高度」或「半寬 > narrowing」（船身上段往裡收的地方半寬會小於 narrowing，所以要用高度分上下）。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_lines as DL   # noqa: E402
from draft_floors import HullGrid, interp_tab   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def load_prev(design):
    prev = set()
    groups = (('keel', ('shoe', 'keel')), ('posts', ('sternpost', 'inner_post', 'stem', 'gripe')),
              ('deadwood', ('aft_deadwood', 'fore_deadwood', 'apron')))
    for sub, parts in groups:
        for p in parts:
            for ln in open(os.path.join(design, 'masks', sub, p + '.vox.txt'), encoding='utf-8'):
                if ln.strip() and not ln.startswith('#'):
                    prev.add(tuple(int(v) for v in ln.split(',')[:3]))
    for fn in sorted(os.listdir(os.path.join(design, 'masks', 'floors'))):
        for ln in open(os.path.join(design, 'masks', 'floors', fn), encoding='utf-8'):
            if ln.strip() and not ln.startswith('#'):
                prev.add(tuple(int(v) for v in ln.split(',')[:3]))
    return prev


def main():
    design = sys.argv[1]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Sc, Fl, Fr = plan['scale'], plan['floors'], plan['frames']
    X0, Zk = Sc['X_of_x0'], Sc['Z_of_keel_top']
    N = interp_tab(B, 'narrowing_line', 'x_hb')
    hg = HullGrid(xs, zs, T)
    prev = load_prev(design)
    M = Fr['moulded_cells']

    def mould(z, ztop):                                   # 底圖 m
        if z <= M['taper_from_z']:
            c = M['low']
        else:
            t = min(1.0, (z - M['taper_from_z']) / max(ztop - M['taper_from_z'], 1e-6))
            c = M['low'] + (M['top'] - M['low']) * t
        return c / cpm

    frames, info = {}, {}
    for n in range(Fr['n'][0], Fr['n'][1] + 1):
        xf = Fl['frame_x0'] + n * Fl['frame_spacing']
        Xf = X0 + xf * cpm
        i0 = int(round(Xf - Fr['sided_cells'] / 2.0))
        cells = []
        for Xc in range(i0, i0 + Fr['sided_cells']):
            x = (Xc + 0.5 - X0) / cpm
            col = hg.column(x)
            sec = hg.section(x)
            okz = col >= 0
            z_valid_max = float(zs[okz].max())                     # 這一欄船殼表最後一個有值的高度（再上去是 −1 ＝ 外面）
            nh = N(x)
            ztop = float(ship.top(x))
            above = np.where((col >= nh) & (zs <= 7.0))[0]
            z_head = float(zs[above[0]]) if len(above) else 0.0      # 船殼半寬第一次到 narrowing 的高度 ＝ 底肋頭的高度
            for Zc in range(int(Zk), int(Zk + ztop * cpm) + 2):
                z = (Zc + 0.5 - Zk) / cpm
                if z > ztop or z > z_valid_max:
                    continue
                hb_z = float(np.interp(z, zs[okz], col[okz]))     # 只拿有值的點內插（夾著 −1 會內插出假的小半寬）
                if hb_z < 0:
                    continue
                mm = mould(z, ztop)
                for dy in range(0, int(hb_z * cpm) + 2):
                    h = dy / cpm
                    if h > hb_z:
                        continue
                    if not (z > z_head or h > nh):
                        continue
                    if hb_z - h > mm + 1.0 / cpm:                    # 粗篩（水平距離比 moulded 大很多就不必算）
                        continue
                    d = np.min(np.hypot(sec[:, 0] - h, sec[:, 1] - z))
                    if d > mm:
                        continue
                    for y in {160 + dy, 160 - dy}:
                        if (Xc, y, Zc) not in prev:
                            cells.append((Xc, y, Zc, Fr['color']))
        frames[n] = cells
        info[n] = {'x_frame_plate': round(xf, 4), 'X_cells': [i0, i0 + Fr['sided_cells'] - 1], 'top_plate_m': round(float(ship.top(xf)), 3)}

    mdir = os.path.join(design, 'masks', 'frames')
    os.makedirs(mdir, exist_ok=True)
    ver = {'k': round(k, 5), 'frames': {}}
    seen = set()
    total = 0
    for n, cl in frames.items():
        xyz = {(a, b, c) for a, b, c, _ in cl}
        assert len(xyz) == len(cl), f'r{n:+03d} 有重複格'
        assert not (xyz & seen) and not (xyz & prev), f'r{n:+03d} 重疊'
        seen |= xyz
        name = 'r%+03d' % n
        with open(os.path.join(mdir, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 夜燈號 肋骨 {name}（新圖紙 06 v1，draft_frames.py 產）—— x,y,z,color；stampvox at=0,0,0\n')
            for c in cl:
                f.write('%d,%d,%d,%d\n' % c)
        a = np.array(sorted(xyz))
        mir = sum(1 for (x, y, z) in xyz if (x, 320 - y, z) not in xyz)
        # 每一欄每一舷沿 z 是不是連續（肋骨從底肋頭到舷牆頂不斷）—— 以 y 最外那格的 z 序列看斷點
        gaps = 0
        for Xc in range(info[n]['X_cells'][0], info[n]['X_cells'][1] + 1):
            zz = sorted({z for (x, y, z) in xyz if x == Xc and y < 160})
            gaps += sum(1 for p_, q_ in zip(zz, zz[1:]) if q_ - p_ > 1)
        info[n].update({'file': f'masks/frames/{name}.vox.txt', 'cells': len(cl), 'z': [int(a[:, 2].min()), int(a[:, 2].max())],
                        'mirror_missing': mir, 'z_gaps_P': gaps})
        ver['frames'][name] = info[n]
        total += len(cl)
    ver['total_cells'] = total
    # 連通：跟前面全部一起
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

    # 對照圖：落在船尾站上的四片（Ø、4、8、12）中間那一欄疊橫切面圖左半（含底肋，看整條接得順不順）
    base = Image.open(os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768',
                                   'PlLI_Engelsk_Ostindiefarare.tif')).convert('L')
    pxm = R['px_per_m']
    bpc, bpk = B['body_plan']['centre_px'], B['body_plan']['keel_top_py']
    bx0, by0, bx1, by1, s3 = 7450, 1750, 8720, 4130, 0.45
    Bm = base.crop((bx0, by0, bx1, by1)).resize((int((bx1 - bx0) * s3), int((by1 - by0) * s3)), Image.LANCZOS).convert('RGBA')
    ov = Image.new('RGBA', Bm.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    floors = {}
    for n in (0, -4, -8, -12):
        floors[n] = [tuple(int(v) for v in ln.split(',')[:3]) for ln in open(os.path.join(design, 'masks', 'floors', 'f%+03d.vox.txt' % n), encoding='utf-8') if ln[0] != '#']
    cols = {0: (220, 0, 0, 130), -4: (0, 120, 220, 130), -8: (0, 160, 60, 130), -12: (200, 120, 0, 150)}
    for n, colr in cols.items():
        Xc = info[n]['X_cells'][0] + 1
        pts = [(y, z) for (x, y, z, c) in frames[n] if x == Xc and y <= 160] + [(y, z) for (x, y, z) in floors[n] if x == Xc and y <= 160]
        for (y, z) in pts:
            h0 = (160 - y) / cpm - 0.5 / cpm
            z0 = (z - Zk) / cpm
            d.rectangle([(bpc - (h0 + 1 / cpm) * pxm - bx0) * s3, (bpk - (z0 + 1 / cpm) * pxm - by0) * s3,
                         (bpc - h0 * pxm - bx0) * s3, (bpk - z0 * pxm - by0) * s3], fill=colr)
    Bm = Image.alpha_composite(Bm, ov).convert('RGB')
    Bm.save(os.path.join(design, 'compare06_frames_body_v1.png'))
    ver['outputs'] = ['compare06_frames_body_v1.png']
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1, default=lambda v: v.item())
    open(os.path.join(design, 'verify_frames.json'), 'w', encoding='utf-8').write(dump(ver))
    print(json.dumps({'total_cells': total, 'connected_all': ver['connected_all']}, ensure_ascii=False))
    for name in list(ver['frames'])[::5]:
        print(name, ver['frames'][name])
    print('mirror_missing', sum(v['mirror_missing'] for v in ver['frames'].values()), 'z_gaps_P', sum(v['z_gaps_P'] for v in ver['frames'].values()))


if __name__ == '__main__':
    main()
