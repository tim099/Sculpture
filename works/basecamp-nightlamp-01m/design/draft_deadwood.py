# 新圖紙 04 deadwood・apron v1（階段三，TASK-0538）：plan.json deadwood ⇒ 三份 3D 格子清單、Pl. LI 對照圖、verify_deadwood.json。
# 用法：python -I draft_deadwood.py <design 資料夾>
#   · 清單給 `sculpture op=stampvox at=0,0,0`；三份互不重疊，也不跟階段一、二（masks/keel、masks/posts）重疊。
#   · 格中心 (X+0.5, Z+0.5) 換回底圖公尺判斷；y 158..162。A ＝ cutting-down line、B ＝ keelson 頂（readings_LI_bodyplan）。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_lines as DL   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


class Deadwood:
    def __init__(s, plan, B, ship):
        s.P, s.ship = plan['deadwood'], ship
        a = np.array(B['line_A_cutting_down']['x_z'], float)
        b = np.array(B['line_B_keelson_top']['x_z'], float)
        s.A = lambda x: float(np.interp(x, a[:, 0], a[:, 1]))
        s.B = lambda x: float(np.interp(x, b[:, 0], b[:, 1]))
        st = plan['hull']['stations_x']
        s.x_aft_end = st[s.P['aft']['x_to_station']]
        s.x_fore_start = st[s.P['fore']['x_from_station']]
        s.b_end = b[-1]                                    # B 碰到船頭 rabbet 的那一點
        s.band = s.P['apron']['band']

    def part_of(s, x, z):
        sh = s.ship
        if z < 0:
            return None
        # 船尾：rabbet（L3）往前到 16 號站、龍骨頂到 B
        if x <= s.x_aft_end and x >= float(sh.rabbet_aft_x(z)) and z <= s.B(x) and z <= sh.tuck_z:
            return 'aft_deadwood'
        # 船頭：M 站往前到船頭 rabbet
        if x >= s.x_fore_start and x < float(sh.rabbet_x(z)):
            if z <= s.A(x):
                return 'fore_deadwood'
            if z <= s.B(x):
                return 'apron'
            if s.b_end[1] <= z <= s.band['z_top'] and x >= float(sh.rabbet_x(z)) - s.band['thickness']:
                return 'apron'
        return None


def main():
    design = sys.argv[1]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Sc = plan['scale']
    X0, Zk = Sc['X_of_x0'], Sc['Z_of_keel_top']
    dw = Deadwood(plan, B, ship)
    y0, y1 = plan['deadwood']['y']
    names = ('aft_deadwood', 'fore_deadwood', 'apron')
    color = {'aft_deadwood': plan['deadwood']['aft']['color'], 'fore_deadwood': plan['deadwood']['fore']['color'],
             'apron': plan['deadwood']['apron']['color']}
    cells = {n: [] for n in names}
    for Zc in range(int(Zk), int(Zk + 9.5 * cpm)):
        z = (Zc + 0.5 - Zk) / cpm
        for Xc in range(int(X0 - 2 * cpm), int(X0 + 41 * cpm)):
            x = (Xc + 0.5 - X0) / cpm
            n = dw.part_of(x, z)
            if n:
                for y in range(y0, y1 + 1):
                    cells[n].append((Xc, y, Zc, color[n]))

    prev = set()
    for sub, parts in (('keel', ('shoe', 'keel')), ('posts', ('sternpost', 'inner_post', 'stem', 'gripe'))):
        for p in parts:
            for ln in open(os.path.join(design, 'masks', sub, p + '.vox.txt'), encoding='utf-8'):
                if ln.strip() and not ln.startswith('#'):
                    prev.add(tuple(int(v) for v in ln.split(',')[:3]))
    mdir = os.path.join(design, 'masks', 'deadwood')
    os.makedirs(mdir, exist_ok=True)
    ver = {'k': round(k, 5), 'x_aft_end_plate_m': dw.x_aft_end, 'x_fore_start_plate_m': dw.x_fore_start,
           'B_meets_rabbet_plate_m': [round(float(v), 3) for v in dw.b_end], 'parts': {}}
    seen = set()
    for n in names:
        cl = cells[n]
        xyz = [(a, b, c) for a, b, c, _ in cl]
        st = set(xyz)
        assert len(st) == len(xyz), n + ' 有重複格'
        assert not (st & prev), n + ' 跟階段一、二重疊 %d 格' % len(st & prev)
        assert not (st & seen), n + ' 跟前面幾件重疊'
        seen |= st
        with open(os.path.join(mdir, n + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 夜燈號 {n}（新圖紙 04 v1，draft_deadwood.py 產）—— x,y,z,color；stampvox at=0,0,0\n')
            for c in cl:
                f.write('%d,%d,%d,%d\n' % c)
        a = np.array(xyz)
        ver['parts'][n] = {'file': f'masks/deadwood/{n}.vox.txt', 'cells': len(cl), 'color': color[n],
                           'x': [int(a[:, 0].min()), int(a[:, 0].max())], 'z': [int(a[:, 2].min()), int(a[:, 2].max())]}
    # 接合：跟階段一、二一起 6 連通 1 塊
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
    ver['total_new_cells'] = len(seen)

    # 對照圖
    base = Image.open(os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768',
                                   'PlLI_Engelsk_Ostindiefarare.tif')).convert('L')
    pxm, x0p, kt = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']
    toP = lambda Xc, Zc: (x0p + (Xc - X0) / cpm * pxm, kt - (Zc - Zk) / cpm * pxm)
    colmap = {209: (0, 150, 60, 80), 173: (0, 90, 230, 80)}
    prof = {}
    for n in names:
        for x, y, z, c in cells[n]:
            prof[(x, z)] = c
    outs = []
    for name, (px0, py0, px1, py1, sc) in {'stern': (1400, 5000, 3800, 6900, 0.45), 'bow': (8600, 5300, 10600, 6900, 0.5)}.items():
        Aim = base.crop((px0, py0, px1, py1)).resize((int((px1 - px0) * sc), int((py1 - py0) * sc)), Image.LANCZOS).convert('RGBA')
        ov = Image.new('RGBA', Aim.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for (x, z), c in prof.items():
            a0, a1 = toP(x, z + 1), toP(x + 1, z)
            d.rectangle([(a0[0] - px0) * sc, (a0[1] - py0) * sc, (a1[0] - px0) * sc, (a1[1] - py0) * sc], fill=colmap[c])
        Aim = Image.alpha_composite(Aim, ov).convert('RGB')
        p = os.path.join(design, f'compare04_deadwood_{name}_v1.png')
        Aim.save(p)
        outs.append(os.path.basename(p))
    ver['outputs'] = outs
    json.dump(ver, open(os.path.join(design, 'verify_deadwood.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({kk: v for kk, v in ver.items() if kk != 'parts'}, ensure_ascii=False))
    for n, v in ver['parts'].items():
        print(n, v['cells'], 'x', v['x'], 'z', v['z'])


if __name__ == '__main__':
    main()
