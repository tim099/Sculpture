# 新圖紙 09 gun deck 砲門 v1（階段八，TASK-0538）：plan.json gunports ＋ readings_LI_ports.json（Pl. LI 側面圖 11 個方砲門）＋ 階段一～七的清單
#   ⇒ 刻穿外板與肋骨的清單（masks/ports/carve.vox.txt，`sculpture op=carvevox at=0,0,0`，帶顏色守門）、
#     砲門框清單（masks/ports/lining.vox.txt，stampvox）、新圖紙 09、verify_ports.json。
# 用法：python -I draft_ports.py <design 資料夾> [作品 export list 檔]
#   · 開工前的作品 ＝ 階段一～七的清單（照落子順序蓋上去）；給了 export list 就先逐格對一次，對不上不產。
#   · 開口：格中心落在讀數框（線心）裡的 (X, Z)；兩舷鏡像。框的四邊是直的（原圖的上下緣順著舷弧微斜 —— 斜多少沒量，讀數取那條線在中段的線心）。
#   · 刻：開口裡、舷牆那一層（離那一欄最外面的實心 ≤ wall_depth 格）屬於外板／wale／肋骨的格全刻 —— 從外面看得到船艙；
#     別的木料（stern timbers、wing transom、柱、deadwood…）在那一層裡 ⇒ 不刻、記下來。
#   · 框：開口外一圈、肋骨那一層（外板往裡 moulded(z) 格）的空格補 141（port sill／lintel／port timber —— 肋骨之間的縫從砲門看不進去）；
#     再補「牆不能有洞」：相鄰開口那一欄刻到多深，牆那一欄從那個深度到外緣都要實心（憲法號 v1.2 的規則）。
import sys, os, json, hashlib, glob
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402

YC, NDY, X0G = DP.YC, DP.NDY, DP.X0G
PLANK_ORDER = ['paint_struct', 'fill_cavities', 'plank_x040_149', 'plank_x150_249', 'plank_x250_349',
               'plank_x350_449', 'plank_x450_549', 'plank_x550_699', 'wales']


def cell_rows(a, b):
    """格中心在 [a, b] 的整數格"""
    return list(range(int(np.ceil(a - 0.5)), int(np.floor(b - 0.5)) + 1))


class Ports:
    def __init__(s, design):
        s.design = design
        s.m = DP.Model(design)                      # 階段一～六
        s.cx = s.m.cx
        s.P = s.cx.plan['gunports']
        lab = {}
        for sub in ('keel', 'posts', 'deadwood', 'floors', 'frames', 'ends'):
            for f in glob.glob(os.path.join(design, 'masks', sub, '*.vox.txt')):
                name = os.path.basename(f)[:-8]
                kind = 'frame' if (sub in ('frames', 'floors') or (sub == 'ends' and name.startswith('r'))) else sub + ':' + name
                for c in DP.read_list(f):
                    lab[c] = kind
        world = dict(s.m.world)
        for name in PLANK_ORDER:                    # 階段七照落子順序
            w = DP.read_list(os.path.join(design, 'masks', 'planking', name + '.vox.txt'))
            if name == 'paint_struct':
                assert w.keys() <= world.keys()
            else:
                assert not (w.keys() & world.keys()), name
                k = 'wale' if name == 'wales' else ('plank' if name.startswith('plank') else 'cavity_fill')
                for c in w:
                    lab[c] = k
            world.update(w)
        s.world, s.lab = world, lab

    def X(s, x):
        return s.cx.X0 + x * s.cx.cpm

    def Z(s, z):
        return s.cx.Zk + z * s.cx.cpm

    def openings(s):
        src = json.load(open(os.path.join(s.design, s.P['source']), encoding='utf-8'))
        s.ports = []
        for p in src['ports']:
            Xa, Xf, Zs, Zl = s.X(p['x_aft']), s.X(p['x_fwd']), s.Z(p['z_sill']), s.Z(p['z_lintel'])
            s.ports.append({'n': p['n'], 'read_cells': [round(v, 2) for v in (Xa, Xf, Zs, Zl)],
                            'xs': cell_rows(Xa, Xf), 'zs': cell_rows(Zs, Zl)})

    def outer(s, x, z, side):
        """那一欄 (x, z) 這一舷最外面的實心 d（沒有 ⇒ None）"""
        for d in range(NDY - 1, -1, -1):
            if (x, YC + side * d, z) in s.world:
                return d
        return None

    def plan_cuts(s):
        allowed = set(s.P['carve_members'])
        depth = s.P['wall_depth']
        s.carve, s.blocked = {}, []
        for p in s.ports:
            p['carve'] = {1: set(), -1: set()}
            for side in (1, -1):
                bad = {}
                for z in p['zs']:
                    for x in p['xs']:
                        o = s.outer(x, z, side)
                        assert o is not None, ('開口那一欄沒有船殼', p['n'], x, z)
                        for d in range(max(0, o - depth), o + 1):
                            c = (x, YC + side * d, z)
                            if c not in s.world:
                                continue
                            k = s.lab.get(c, 'other')
                            if k in allowed:
                                p['carve'][side].add(c)
                            else:
                                bad[k] = bad.get(k, 0) + 1
                if bad:
                    s.blocked.append({'port': p['n'], 'side': side, 'kinds': bad})
                for c in p['carve'][side]:
                    s.carve[c] = s.world[c]

    def lining(s):
        """開口外一圈 × 肋骨那一層的空格 ⇒ 141；再補牆洞"""
        col = s.P['lining_color']
        s.fill = {}
        for p in s.ports:
            xs, zs = p['xs'], p['zs']
            ring = {}                                             # 牆那一欄 (x, z) → 相鄰開口那一欄
            for z in zs:
                ring[(xs[0] - 1, z)] = (xs[0], z)
                ring[(xs[-1] + 1, z)] = (xs[-1], z)
            for z, zz in ((zs[0] - 1, zs[0]), (zs[-1] + 1, zs[-1])):
                for x in range(xs[0] - 1, xs[-1] + 2):
                    ring[(x, z)] = (min(max(x, xs[0]), xs[-1]), zz)
            p['ring'] = ring
            n_frame = 0
            for (x, z) in ring:
                ztop = float(s.cx.ship.top(float(s.m.xb(x))))
                mc = s.cx.mould(float(s.m.zb(z)), ztop) * s.cx.cpm   # 肋骨那一層幾格
                for side in (1, -1):
                    o = s.outer(x, z, side)                          # 外板
                    if o is None:
                        continue
                    for d in range(o - int(round(mc)), o):
                        c = (x, YC + side * d, z)
                        if c not in s.world and c not in s.carve:
                            s.fill[c] = col
                            n_frame += 1
            p['lining_frame_layer'] = n_frame

        def occ(c):
            return (c in s.world and c not in s.carve) or c in s.fill
        s.holes = {}
        for p in s.ports:
            n = 0
            for (x, z), (ax, az) in p['ring'].items():
                for side in (1, -1):
                    dug = [abs(c[1] - YC) for c in p['carve'][side] if c[0] == ax and c[2] == az]
                    wall = [d for d in range(NDY) if occ((x, YC + side * d, z))]
                    if not dug or not wall:
                        continue
                    for d in range(max(min(wall), min(dug)), max(wall) + 1):
                        c = (x, YC + side * d, z)
                        if not occ(c):
                            s.holes[c] = col
                            n += 1
            p['wall_holes'] = n
        s.fill.update(s.holes)

    def cavities(s):
        """刻完＋補框之後的封閉空腔（整個網格；跟引擎 stats structure=1 同一個定義）與元件數"""
        from scipy import ndimage
        after = {c: v for c, v in s.world.items() if c not in s.carve}
        after.update(s.fill)
        a = np.array(list(after.keys()))
        lo = a.min(0) - 1
        hi = a.max(0) + 2
        g = np.zeros(hi - lo, bool)
        g[tuple((a - lo).T)] = True
        lab, _ = ndimage.label(~g)
        cav = (~g) & (lab != lab[0, 0, 0])
        s.after = after
        s.cav = [tuple(int(v) for v in (c + lo)) for c in np.argwhere(cav)]
        _, n2 = ndimage.label(g)
        s.n_comp = int(n2)

    def write(s):
        out = os.path.join(s.design, 'masks', 'ports')
        os.makedirs(out, exist_ok=True)
        for f in glob.glob(os.path.join(out, '*.vox.txt')):
            os.remove(f)
        s.lists = []
        for name, cells, note in (('carve', s.carve, '刻穿外板・wale・肋骨（帶顏色守門：那一格現在要是這個顏色才刻）；carvevox at=0,0,0'),
                                  ('lining', s.fill, '砲門框（port sill／lintel／port timber）＋牆洞；stampvox at=0,0,0')):
            p = os.path.join(out, name + '.vox.txt')
            body = ''.join('%d,%d,%d,%d\n' % (c[0], c[1], c[2], v) for c, v in sorted(cells.items()))
            open(p, 'w', encoding='utf-8', newline='\n').write('# 夜燈號 %s（新圖紙 09 v1，draft_ports.py 產）—— %s；%d 格\n' % (name, note, len(cells)) + body)
            s.lists.append({'name': name, 'file': 'masks/ports/%s.vox.txt' % name, 'cells': len(cells),
                            'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()})


def render_sheet(P, path):
    """新圖紙 09：右舷側面（每一欄最外面那一格）；刻掉的格紅、框 tan、讀數框藍；下面：從船裡看右舷外牆、砲門 6 的剖面"""
    X0s, X1s, Z0s, Z1s, sc = 80, 590, 80, 150, 3
    W, H = X1s - X0s, Z1s - Z0s
    img = np.full((H, W, 3), 250, np.uint8)
    for x in range(X0s, X1s):
        for z in range(Z0s, Z1s):
            for d in range(NDY - 1, -1, -1):
                c = (x, YC + d, z)
                if c in P.carve:
                    img[Z1s - 1 - z, x - X0s] = (230, 60, 50)
                    break
                if c in P.fill:
                    img[Z1s - 1 - z, x - X0s] = (200, 160, 110)
                    break
                if c in P.world:
                    img[Z1s - 1 - z, x - X0s] = DP.rgb332(P.world[c]) if P.lab.get(c) in ('plank', 'wale') else (200, 185, 160)
                    break
    im = Image.fromarray(img).resize((W * sc, H * sc), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for p in P.ports:
        Xa, Xf, Zs, Zl = p['read_cells']
        d.rectangle([((Xa - X0s) * sc, (Z1s - Zl) * sc), ((Xf - X0s) * sc, (Z1s - Zs) * sc)], outline=(30, 80, 220), width=1)
        d.text(((Xa - X0s) * sc, (Z1s - Zl) * sc - 12), str(p['n']), fill=(30, 80, 220))
    d.text((6, 6), 'sheet 09 v1  gun deck ports (starboard, bow right)  red: carved   tan: port lining   blue: Pl. LI port outlines (line centres)', fill=(0, 0, 0))
    X0b, X1b, Z0b, Z1b, s2 = 300, 380, 95, 130, 8
    inside = np.full((Z1b - Z0b, X1b - X0b, 3), 250, np.uint8)
    for x in range(X0b, X1b):
        for z in range(Z0b, Z1b):
            for dd in range(1, NDY):
                c = (x, YC + dd, z)
                if c in P.after:
                    inside[Z1b - 1 - z, x - X0b] = (200, 160, 110) if c in P.fill else DP.rgb332(P.after[c])
                    break
    ins = Image.fromarray(inside).resize(((X1b - X0b) * s2, (Z1b - Z0b) * s2), Image.NEAREST)
    ImageDraw.Draw(ins).text((4, 4), 'from inside, starboard wall after carving (X 300-379)', fill=(200, 0, 0))
    p6 = [p for p in P.ports if p['n'] == 6][0]
    xm = p6['xs'][len(p6['xs']) // 2]
    sec = np.full((Z1b - Z0b, NDY, 3), 250, np.uint8)
    for dd in range(NDY):
        for z in range(Z0b, Z1b):
            c = (xm, YC + dd, z)
            if c in P.carve:
                sec[Z1b - 1 - z, dd] = (230, 60, 50)
            elif c in P.fill:
                sec[Z1b - 1 - z, dd] = (200, 160, 110)
            elif c in P.world:
                sec[Z1b - 1 - z, dd] = DP.rgb332(P.world[c]) if P.lab.get(c) in ('plank', 'wale') else (200, 185, 160)
    se = Image.fromarray(sec[:, 30:]).resize(((NDY - 30) * s2, (Z1b - Z0b) * s2), Image.NEAREST)
    ImageDraw.Draw(se).text((4, 4), 'section X %d (port 6)' % xm, fill=(200, 0, 0))
    canvas = Image.new('RGB', (max(im.size[0], ins.size[0] + se.size[0] + 30), im.size[1] + ins.size[1] + 20), (255, 255, 255))
    canvas.paste(im, (0, 0))
    canvas.paste(ins, (0, im.size[1] + 10))
    canvas.paste(se, (ins.size[0] + 20, im.size[1] + 10))
    canvas.save(path)


def main():
    design = sys.argv[1]
    P = Ports(design)
    ver = {'title': P.P['title'], 'world_cells': len(P.world)}
    if len(sys.argv) > 2:
        work = DP.read_list(sys.argv[2])
        miss = sum(1 for k in P.world if k not in work)
        extra = sum(1 for k in work if k not in P.world)
        cdiff = sum(1 for k, c in P.world.items() if k in work and work[k] != c)
        ver['start_ledger'] = {'work_cells': len(work), 'missing': miss, 'extra': extra, 'color_diff': cdiff}
        assert miss == extra == cdiff == 0, ('作品不是階段七結束的樣子 ⇒ 不產', ver['start_ledger'])
    P.openings()
    P.plan_cuts()
    P.lining()
    P.cavities()
    P.write()
    kinds = {}
    for c in P.carve:
        k = P.lab.get(c, 'other')
        kinds[k] = kinds.get(k, 0) + 1
    mir = sum(1 for (x, y, z) in P.carve if (x, 2 * YC - y, z) not in P.carve) + \
        sum(1 for (x, y, z) in P.fill if (x, 2 * YC - y, z) not in P.fill)
    ver.update({
        'ports': [{'n': p['n'], 'read_cells': p['read_cells'], 'X': [p['xs'][0], p['xs'][-1]], 'Z': [p['zs'][0], p['zs'][-1]],
                   'carve': [len(p['carve'][1]), len(p['carve'][-1])], 'lining_frame_layer': p['lining_frame_layer'],
                   'wall_holes': p['wall_holes']} for p in P.ports],
        'carve_cells': len(P.carve), 'carve_by_kind': kinds, 'blocked_in_openings': P.blocked,
        'lining_cells': len(P.fill), 'wall_hole_cells': len(P.holes),
        'mirror_diff': mir, 'cavities_after': len(P.cav), 'cavity_where': P.cav[:20], 'components_after': P.n_comp,
        'expect_after': len(P.world) - len(P.carve) + len(P.fill), 'lists': P.lists})
    json.dump(ver, open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(P, os.path.join(design, P.P['sheet']))
    print(json.dumps({k: v for k, v in ver.items() if k != 'ports'}, ensure_ascii=False))
    for p in ver['ports']:
        print(p)


if __name__ == '__main__':
    main()
