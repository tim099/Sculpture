# 新圖紙 03 船頭柱・gripe・船尾柱・內艉柱 v1（階段二，TASK-0538）：plan.json posts ⇒ 四份 3D 格子清單、Pl. LI 對照圖、verify_posts.json。
# 用法：python -I draft_posts.py <design 資料夾>
#   · 清單給 `sculpture op=stampvox at=0,0,0`；四份互不重疊，也不跟階段一（masks/keel）重疊。
#   · 格中心 (X+0.5, Z+0.5) 換回底圖公尺判斷在不在區域裡；y 158..162。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_lines as DL   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


class Posts:
    def __init__(s, plan, R, B, ship):
        s.P, s.ship = plan['posts'], ship
        s.pxm, s.x0p, s.kt = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']
        L = B['stern_post_lines']
        s.c1, s.c3 = L['L1']['off_px_vs_py'], L['L3']['off_px_vs_py']
        sp = plan['hull']['sternpost']
        s.sp_x0, s.sp_tan = sp['x_at_keel_top'], math.tan(math.radians(sp['rake_deg']))
        K = plan['keel']
        s.keel_fore, s.shoe_fore = K['keel']['fore_x'], K['shoe']['fore_x']
        s.kd = ship.keel_depth

    # 船尾的線：原圖 px「離船尾柱後面幾 px」對 py 的直線 ⇒ 底圖公尺
    def _py(s, z):
        return s.kt - z * s.pxm

    def aft_face(s, z):
        return s.sp_x0 - z * s.sp_tan

    def L1(s, z):
        return s.aft_face(z) + np.polyval(s.c1, s._py(z)) / s.pxm

    def L3(s, z):
        return s.aft_face(z) + np.polyval(s.c3, s._py(z)) / s.pxm

    def sternpost_fore(s, z):
        return max(s.L1(z), s.aft_face(z) + s.P['sternpost']['min_siding'])

    def part_of(s, x, z, z_bow_top):
        """格中心（底圖公尺）屬於哪一件；不屬於任何一件 ⇒ None"""
        sh = s.ship
        # 船尾
        if 0.0 <= z <= s.P['sternpost']['z_top']:
            a, f = s.aft_face(z), s.sternpost_fore(z)
            if a <= x < f:
                return 'sternpost'
            if f <= x < s.L3(z) and z <= s.P['inner_post']['z_top']:
                return 'inner_post'
        if x < 20.0:
            return None
        # 船頭
        if 0.0 <= z <= z_bow_top:
            if float(sh.rabbet_x(z)) <= x < float(sh.stem_face_x(z)):
                return 'stem'
        if -s.kd <= z <= s.P['gripe']['z_top']:
            back = float(sh.stem_face_x(z)) if z >= 0 else (s.keel_fore if z >= -0.374 else s.shoe_fore)
            if back <= x < float(sh.stem_outer_x(z)):
                return 'gripe'
        return None


def build(plan, R, B, ship, X0, Zk, cpm):
    po = Posts(plan, R, B, ship)
    y0, y1 = plan['posts']['y']
    x_bow = ship.fwd_end_top_x()
    z_bow_top = float(ship.top(x_bow))
    cells = {k: [] for k in ('sternpost', 'inner_post', 'stem', 'gripe')}
    for Zc in range(0, int(Zk + z_bow_top * cpm) + 2):
        z = (Zc + 0.5 - Zk) / cpm
        for Xc in range(int(X0 - 4 * cpm), int(X0 + 44 * cpm)):
            x = (Xc + 0.5 - X0) / cpm
            part = po.part_of(x, z, z_bow_top)
            if part:
                col = plan['posts'][part]['color']
                for y in range(y0, y1 + 1):
                    cells[part].append((Xc, y, Zc, col))
    return po, cells, z_bow_top


def main():
    design = sys.argv[1]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Sc = plan['scale']
    X0, Zk = Sc['X_of_x0'], Sc['Z_of_keel_top']
    po, cells, z_bow_top = build(plan, R, B, ship, X0, Zk, cpm)

    keel = set()
    for part in ('shoe', 'keel'):
        for ln in open(os.path.join(design, 'masks', 'keel', part + '.vox.txt'), encoding='utf-8'):
            if ln.strip() and not ln.startswith('#'):
                keel.add(tuple(int(v) for v in ln.split(',')[:3]))
    mdir = os.path.join(design, 'masks', 'posts')
    os.makedirs(mdir, exist_ok=True)
    ver = {'k': round(k, 5), 'z_bow_top_plate_m': round(z_bow_top, 3), 'parts': {}}
    seen = set()
    for part in ('sternpost', 'inner_post', 'stem', 'gripe'):
        cl = cells[part]
        xyz = [(a, b, c) for a, b, c, _ in cl]
        st = set(xyz)
        assert len(st) == len(xyz), part + ' 有重複格'
        assert not (st & keel), part + ' 跟龍骨重疊 %d 格' % len(st & keel)
        assert not (st & seen), part + ' 跟前面幾件重疊'
        seen |= st
        with open(os.path.join(mdir, part + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 夜燈號 {part}（新圖紙 03 v1，draft_posts.py 產）—— x,y,z,color；stampvox at=0,0,0\n')
            for c in cl:
                f.write('%d,%d,%d,%d\n' % c)
        a = np.array(xyz)
        rows = {}
        for x, y, z in xyz:
            r = rows.setdefault(z, [x, x])
            r[0], r[1] = min(r[0], x), max(r[1], x)
        ver['parts'][part] = {'file': f'masks/posts/{part}.vox.txt', 'cells': len(cl), 'color': cl[0][3],
                              'x': [int(a[:, 0].min()), int(a[:, 0].max())], 'z': [int(a[:, 2].min()), int(a[:, 2].max())],
                              'rows_x': {str(z): rows[z] for z in sorted(rows)}}
    # 接合：每件跟龍骨＋其他件是不是面相鄰（6 連通），整體 1 塊
    allc = seen | keel
    from collections import deque
    start = next(iter(allc))
    q, vis = deque([start]), {start}
    while q:
        c = q.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
            if n in allc and n not in vis:
                vis.add(n)
                q.append(n)
    ver['connected_with_keel'] = {'cells': len(allc), 'reached_from_one': len(vis)}
    ver['total_new_cells'] = len(seen)

    # 對照圖：作品格（中線 y 160 那一層）換回底圖像素疊在 Pl. LI 上
    base = Image.open(os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768',
                                   'PlLI_Engelsk_Ostindiefarare.tif')).convert('L')
    pxm, x0p, kt = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']
    toP = lambda Xc, Zc: (x0p + (Xc - X0) / cpm * pxm, kt - (Zc - Zk) / cpm * pxm)
    colmap = {177: (220, 0, 0, 70), 173: (0, 90, 230, 80), 104: (230, 120, 0, 90)}
    prof = {}
    for part in ('sternpost', 'inner_post', 'stem', 'gripe'):
        for x, y, z, c in cells[part]:
            prof[(x, z)] = c
    outs = []
    for name, (px0, py0, px1, py1, sc) in {'stern': (1400, 5000, 2200, 6900, 0.6), 'bow': (9000, 4300, 10900, 6900, 0.42)}.items():
        A = base.crop((px0, py0, px1, py1)).resize((int((px1 - px0) * sc), int((py1 - py0) * sc)), Image.LANCZOS).convert('RGBA')
        ov = Image.new('RGBA', A.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for (x, z), c in prof.items():
            a0, a1 = toP(x, z + 1), toP(x + 1, z)
            d.rectangle([(a0[0] - px0) * sc, (a0[1] - py0) * sc, (a1[0] - px0) * sc, (a1[1] - py0) * sc], fill=colmap[c])
        A = Image.alpha_composite(A, ov).convert('RGB')
        p = os.path.join(design, f'compare03_posts_{name}_v1.png')
        A.save(p)
        outs.append(os.path.basename(p))
    ver['outputs'] = outs
    json.dump(ver, open(os.path.join(design, 'verify_posts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({kk: v for kk, v in ver.items() if kk != 'parts'}, ensure_ascii=False))
    for part, v in ver['parts'].items():
        print(part, v['cells'], 'x', v['x'], 'z', v['z'])


if __name__ == '__main__':
    main()
