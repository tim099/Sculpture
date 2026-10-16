# 新圖紙 20（舵子作品，§9.8.1）：plan.json 的 rudder 段 ＋ 組裝件的現況（舵加進來之前）
#   ⇒ masks/rudder/rudder.vox.txt（子作品 at 0,0,0、跟組裝件同框）、verify_rudder.json、sheet20_rudder_v1.png
# 用法：python -I draft_rudder.py <design 資料夾> <組裝件 export format=list 的檔>
#   · 做法照憲法號 draft_rudder.py：每一欄 (y, z) 從後緣線長到「那一欄最後面的實心（船尾柱、counter）」前一格
#     ⇒ 前緣貼著船尾柱、頂端順著 counter 收進去
#   · 前半 5 格厚、後半 3 格厚；吃水線以下 100、以上 36（換色的高度從船尾柱後面那一欄的實際塗色量）
#   · pintle 帶只貼在舵板上（舵會轉 ⇒ 不往前貼到船殼）
#   · 鉸鏈、stock-top 照造船規格 §9.8.1 step 2–3 量（前緣直線擬合），寫進 verify
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_lines as DL           # noqa: E402
from draft_planking import rgb332  # noqa: E402

YC = 160
XA, XB, ZB = 50, 130, 130
PAPER, INK = (250, 248, 240), (20, 20, 20)


def font(n):
    for f in ('msjh.ttc', 'msyh.ttc', 'arial.ttf'):
        try:
            return ImageFont.truetype(f, n)
        except OSError:
            pass
    return ImageFont.load_default()


def read_list(path):
    rows = []
    for line in open(path, encoding='utf-8'):
        if line.startswith('#'):
            continue
        p = line.strip().split(',')
        if len(p) >= 4:
            try:
                rows.append([int(v) for v in p[:4]])
            except ValueError:
                pass
    return np.array(rows, np.int64)


class Rudder:
    def __init__(s, design, base_list):
        s.design = design
        s.plan, R, B, ship = DL.load(design)
        xs, zs, T, hb_max, _ = DL.hull_table(ship)
        s.k, s.cpm, X, Z, Yh = DL.scale_of(s.plan, ship, hb_max)
        Sc = s.plan['scale']
        s.X = lambda x: Sc['X_of_x0'] + x * s.cpm
        s.Z = lambda z: Sc['Z_of_keel_top'] + z * s.cpm
        s.P = s.plan['rudder']
        a = read_list(base_list)
        assert len(a) == s.P['base']['assembly_voxels'], ('讀到的現況格數對不上', len(a), s.P['base']['assembly_voxels'])
        m = a[(a[:, 0] >= XA) & (a[:, 0] < XB) & (a[:, 2] < ZB)]
        s.G = np.zeros((XB - XA, 320, ZB), np.uint8)
        s.G[m[:, 0] - XA, m[:, 1], m[:, 2]] = m[:, 3]
        s.cells, s.kind = {}, {}

    def put(s, k, c, kind):
        if k in s.cells or s.G[k[0] - XA, k[1], k[2]]:
            return False
        s.cells[k] = int(c)
        s.kind[k] = kind
        return True

    def aft_face(s, y, z):
        col = np.where(s.G[:, y, z] > 0)[0]
        return int(col.min()) + XA if len(col) else None

    def lwl_z(s):
        # 船尾柱後面那一欄（中線 ±2）最後面的格：從下往上第一層出現黑色 36 的高度
        for z in range(ZB):
            for dy in range(-2, 3):
                xf = s.aft_face(YC + dy, z)
                if xf is not None and s.G[xf - XA, YC + dy, z] == s.P['colors']['black'] and z > 20:
                    return z
        raise RuntimeError('量不到吃水線換色的高度')

    def build(s):
        P = s.P
        A = np.array([(s.X(x), s.Z(z)) for x, z in P['aft_edge_m']], float)
        aft = lambda z: float(np.interp(z, A[:, 1], A[:, 0]))
        top = int(math.floor(s.Z(P['top_z_m'])))
        hw, col = P['half_width'], P['colors']
        s.lwl = s.lwl_z()
        s.profile = []
        for z in range(0, top + 1):
            xa = int(math.ceil(aft(z) - 0.5))
            xf0 = s.aft_face(YC, z)
            if xf0 is None or xf0 - 1 < xa:
                continue
            width = xf0 - xa
            s.profile.append((z, xa, xf0 - 1))
            for dy in range(-hw['fore'], hw['fore'] + 1):
                y = YC + dy
                xf = s.aft_face(y, z)
                if xf is None:
                    continue
                for x in range(xa, xf):
                    if abs(dy) > hw['aft'] and (xf0 - x) > 0.5 * width + 0.5:
                        continue
                    s.put((x, y, z), col['bottom'] if z < s.lwl else col['black'], 'rudder')
        # pintle 帶：舵板兩側凸 1 格（|dy| ＝ 舵板那一層的厚度 + 1），從前緣到離後緣 rudder_aft_gap 格
        St = P['straps']
        z0, z1 = s.profile[0][0], s.profile[-1][0]
        zs = [int(round(z0 + (z1 - z0) * (i + 0.5) / St['count'])) for i in range(St['count'])]
        s.strap_rows = []
        for zb in zs:
            for z in range(zb, zb + St['rows']):
                rz = [k for k in s.cells if k[2] == z and s.kind[k] == 'rudder']
                if not rz:
                    continue
                xa_r = min(k[0] for k in rz)
                cnt = 0
                for (x, y, zz) in rz:
                    if x < xa_r + St['rudder_aft_gap']:
                        continue
                    for side in (-1, 1):
                        yy = y + side
                        if (x, yy, z) not in s.cells and abs(yy - YC) > abs(y - YC) and s.put((x, yy, z), col['strap'], 'strap'):
                            cnt += 1
                s.strap_rows.append({'z': z, 'cells': cnt})

    def hinge(s):
        # §9.8.1 step 2：每一層取舵葉朝船頭最遠那一格 ⇒ 前緣面 x ＝ 格 + 1；擬合 x ＝ a + b·z，丟掉離線 > 1.5 格的層
        front = {}
        for (x, y, z), kd in s.kind.items():
            if kd == 'rudder':
                front[z] = max(front.get(z, -1), x + 1)
        pts = sorted(front.items())

        def fit(p):
            z = np.array([q[0] for q in p], float); x = np.array([q[1] for q in p], float)
            b, a = np.polyfit(z, x, 1)
            return float(a), float(b)
        a, b = fit(pts)
        for _ in range(5):
            kept = [q for q in pts if abs(q[1] - (a + b * q[0])) <= 1.5]
            if len(kept) == len(pts):
                break
            a, b = fit(kept)
        kept = [q for q in pts if abs(q[1] - (a + b * q[0])) <= 1.5]
        env = max(q[1] - (a + b * q[0]) for q in kept)
        zlo = pts[0][0]
        n = math.hypot(b, 1.0)
        ys = [k[1] for k in s.cells]
        s.hinge_v = {'fit_a': round(a, 3), 'fit_b': round(b, 5), 'envelope': round(env, 3), 'layers': len(pts), 'kept': len(kept),
                     'axis': [round(b / n, 4), 0, round(1 / n, 4)],
                     'hinge': [round(a + env + b * zlo, 2), (min(ys) + max(ys) + 1) / 2, zlo],
                     'rake_deg_measured': round(math.degrees(math.atan(-b)), 2)}
        ztop = max(k[2] for k in s.cells if s.kind[k] == 'rudder')
        top = sorted(k[0] for k in s.cells if k[2] == ztop and k[1] == YC)
        s.stock_top = [top[len(top) // 2], YC, ztop]

    def verify(s):
        v = {'cells': len(s.cells), 'by_kind': {}, 'colors': {}, 'lwl_z': s.lwl, 'cells_per_base_m': round(s.cpm, 4)}
        for k, c in s.cells.items():
            v['by_kind'][s.kind[k]] = v['by_kind'].get(s.kind[k], 0) + 1
            v['colors'][str(c)] = v['colors'].get(str(c), 0) + 1
        v['overlap'] = sum(1 for k in s.cells if s.G[k[0] - XA, k[1], k[2]])
        v['mirror_mismatch'] = sum(1 for (x, y, z), c in s.cells.items() if s.cells.get((x, 2 * YC - y, z)) != c)
        R = np.zeros_like(s.G, bool)
        for k in s.cells:
            R[k[0] - XA, k[1], k[2]] = True
        lab, n = ndimage.label(R)
        v['rudder_components'] = int(n)
        # 舵碰得到船殼嗎（前緣那一面跟船尾柱相鄰的格數）
        touch = ndimage.binary_dilation(R, ndimage.generate_binary_structure(3, 1)) & (s.G > 0)
        v['touching_hull_cells'] = int(touch.sum())
        pr = s.profile
        v['profile'] = {'z': [pr[0][0], pr[-1][0]], 'bottom_x': [pr[0][1], pr[0][2]], 'top_x': [pr[-1][1], pr[-1][2]],
                        'width_bottom': pr[0][2] - pr[0][1] + 1, 'width_top': pr[-1][2] - pr[-1][1] + 1}
        v['straps'] = s.strap_rows
        v['hinge'] = s.hinge_v
        v['stock_top'] = s.stock_top
        v['expect_assembly_after_cells'] = s.P['base']['assembly_voxels']
        v['note'] = '舵是外部模型 ⇒ 組裝件格數不變；舵的格數在子作品'
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'rudder')
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, 'rudder.vox.txt')
        rows = sorted((k[0], k[1], k[2], c) for k, c in s.cells.items())
        open(p, 'w', encoding='utf-8', newline='\n').write('# rudder —— 舵＋pintle 帶（組裝件座標，at=0,0,0）（%d 格）\n' % len(rows)
                                                           + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        s.files = {'rudder': {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}


def render_sheet(R, path):
    f12, f14, f18 = font(13), font(15), font(20)
    sc = 6
    xa, xb, za, zb = 55, 125, 0, 125

    def side(with_new):
        img = np.zeros((zb - za, xb - xa, 3), np.uint8)
        img[:] = PAPER
        for ix, x in enumerate(range(xa, xb)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                for y in range(319, -1, -1):
                    c = R.cells.get((x, y, z)) if with_new else None
                    if c is None and R.G[x - XA, y, z]:
                        c = int(R.G[x - XA, y, z])
                    if c is not None:
                        img[iz, ix] = rgb332(c)
                        break
        return Image.fromarray(img).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)

    def astern():
        ya, yb = YC - 30, YC + 31
        img = np.zeros((zb - za, yb - ya, 3), np.uint8)
        img[:] = PAPER
        for iy, y in enumerate(range(ya, yb)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                for x in range(XA, XB):
                    c = R.cells.get((x, y, z))
                    if c is None and R.G[x - XA, y, z]:
                        c = int(R.G[x - XA, y, z])
                    if c is not None:
                        img[iz, iy] = rgb332(c)
                        break
        return Image.fromarray(img).resize(((yb - ya) * sc, (zb - za) * sc), Image.NEAREST)
    s0, s1, a1 = side(False), side(True), astern()
    PADL = 50
    W = PADL + 2 * (xb - xa) * sc + 60 + 61 * sc + 60
    can = Image.new('RGB', (W, 80 + (zb - za) * sc + 150), PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), R.P['title'], font=f18, fill=INK)
    dr.text((PADL, 40), '正交投影、每格 %d px；側面從 y > 160 那一舷看（x %d–%d、z %d–%d）；右：從正後方看' % (sc, xa, xb - 1, za, zb - 1), font=f12, fill=INK)
    x0 = PADL
    for title, im in (('現在（沒有舵）', s0), ('新圖紙 20 v1', s1), ('正後方', a1)):
        dr.text((x0, 62), title, font=f14, fill=INK)
        can.paste(im, (x0, 84))
        x0 += im.size[0] + 60
    # 鉸鏈線畫在 v1 那一格上
    h = R.v['hinge']
    ox = PADL + (xb - xa) * sc + 60
    p0 = (ox + (h['hinge'][0] - xa) * sc, 84 + (zb - h['hinge'][2]) * sc)
    zt = R.stock_top[2]
    xt = h['hinge'][0] + h['fit_b'] * (zt - h['hinge'][2])
    p1 = (ox + (xt - xa) * sc, 84 + (zb - zt) * sc)
    dr.line([p0, p1], fill=(220, 30, 30), width=2)
    for z in range(0, zb, 10):
        dr.text((PADL - 30, 84 + (zb - 1 - z) * sc - 7), str(z), font=f12, fill=(130, 130, 130))
    v = R.v
    y = 84 + (zb - za) * sc + 16
    lines = ['舵 %d 格（%s）；z %s、底寬 %d、頂寬 %d；重疊 %d、鏡像差 %d、舵自己 %d 塊、貼著船殼 %d 格；吃水線換色 z %d' % (
        v['cells'], '、'.join('%s %d' % kv for kv in v['by_kind'].items()), v['profile']['z'], v['profile']['width_bottom'], v['profile']['width_top'],
        v['overlap'], v['mirror_mismatch'], v['rudder_components'], v['touching_hull_cells'], v['lwl_z']),
        '紅線 ＝ 量出來的鉸鏈（§9.8.1）：hinge %s、軸 %s、斜 %.2f°（船尾柱 8.24°）；stock-top %s' % (h['hinge'], h['axis'], h['rake_deg_measured'], R.stock_top),
        '出處：Pl. LI 目測的舵後緣與舵頂（plan.json silhouette）；前緣跟著作品的船尾柱；其餘設計（plan.json rudder.provenance）']
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=INK)
        y += 20
    can = can.crop((0, 0, W, y + 16))
    can.save(path)


def main():
    design, base = sys.argv[1], sys.argv[2]
    sys.stdout.reconfigure(encoding='utf-8')
    R = Rudder(design, base)
    R.build()
    R.hinge()
    v = R.verify()
    R.write()
    v['files'] = R.files
    json.dump(v, open(os.path.join(design, 'verify_rudder.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(R, os.path.join(design, 'sheet20_rudder_v1.png'))
    print(json.dumps({k: v[k] for k in v if k != 'straps'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
