# 新圖紙 16（channels 子作品，一舷＋鏡像）：plan.json 的 channels 段 ＋ 組裝件的現況（channels 與舵加進來之前）
#   ⇒ masks/channels/side.vox.txt（自己的座標，at ＝ box.at；另一舷 mirror=y）、design/rig_points_channels.json、
#      verify_channels.json、sheet16_channels_v1.png
# 用法：python -I draft_channels.py <design 資料夾>
#   · channel：每個 x，從船殼表面（那一層 y > 160 最外面的實心）往外 width 格；兩頭收圓角
#   · deadeye：外緣上、坐在 channel 頂上，3×3 去四角、2 格厚
#   · chain plate：deadeye 底下 → 斜向內往下 → z plate_to_z 的船殼表面（前後照 hounds → deadeye 那條線往下延長）
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402

YC = 160
XA, XB, ZA, ZB = 140, 620, 60, 130


class Channels:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['channels']
        B = s.P['base']
        a = export_list(ASSEMBLY, draft=False, hide_links=','.join(B['hide_links']))
        assert len(a) == B['assembly_voxels'], ('讀到的現況格數對不上', len(a), B['assembly_voxels'])
        m = a[(a[:, 0] >= XA) & (a[:, 0] < XB) & (a[:, 2] >= ZA) & (a[:, 2] < ZB)]
        s.G = np.zeros((XB - XA, 320, ZB - ZA), np.uint8)
        s.G[m[:, 0] - XA, m[:, 1], m[:, 2] - ZA] = m[:, 3]
        s.cells = {}
        s.kind = {}
        s.anchors = []
        s.groups = []

    def solid(self, x, y, z):
        return self.G[x - XA, y, z - ZA] > 0

    def outer_dy(s, x, z):
        col = np.where(s.G[x - XA, YC:, z - ZA] > 0)[0]
        return int(col.max()) if len(col) else -1

    def put(s, k, c, kind):
        if k in s.cells or s.solid(*k):
            return False
        s.cells[k] = int(c)
        s.kind[k] = kind
        return True

    def line(s, p0, p1, c, kind):
        p0, p1 = np.array(p0, float), np.array(p1, float)
        n = int(np.linalg.norm(p1 - p0) * 4) + 2
        prev = None
        for t in np.linspace(0, 1, n):
            q = tuple(int(round(v)) for v in p0 + (p1 - p0) * t)
            if prev is not None and sum(abs(a - b) for a, b in zip(q, prev)) > 1:
                for ax in range(3):                       # 斜著走補中間的格 ⇒ 面相連
                    if q[ax] != prev[ax]:
                        mid = list(prev)
                        mid[ax] = q[ax]
                        s.put(tuple(mid), c, kind)
                        prev = tuple(mid)
            s.put(q, c, kind)
            prev = q

    def port_columns(s):
        """gun deck 砲門開口的 x：z 95 那層，最外面的實心比 z 110 那層縮進去 4 格以上（外板被鋸開了）。"""
        s.portx = set()
        for x in range(XA, XB):
            a, b = s.outer_dy(x, 95), s.outer_dy(x, 110)
            if b >= 0 and (a < 0 or a < b - 4):
                s.portx.add(x)

    def plate_clear(s, x_top, x_bot, z_top, z_bot, zr=(86, 104)):
        for z in range(zr[0], zr[1] + 1):
            x = x_top + (x_bot - x_top) * (z - z_top) / (z_bot - z_top)
            if any(int(round(x)) + d in s.portx for d in (-1, 0, 1)):
                return False
        return True

    def build(s):
        P = s.P
        col = P['colors']
        s.port_columns()
        s.plate_moves = []
        z0, z1 = P['z']
        W, R = P['width'], P['corner']
        for M in P['masts']:
            n = M['shrouds'] + M['backstays']
            xs = [M['x_mast'] + M['fwd'] - i * M['spacing'] for i in range(n)]
            xa, xb = int(math.floor(xs[-1] - 4)), int(math.ceil(xs[0] + 4))
            L = xb - xa
            g = {'mast': M['mast'], 'x': [xa, xb], 'deadeyes': [round(x, 1) for x in xs], 'hull_dy': []}
            # channel
            for x in range(xa, xb + 1):
                e = min(x - xa, xb - x)
                inset = R - math.sqrt(max(0.0, R * R - (R - e) ** 2)) if e < R else 0.0
                w = int(round(W - inset))
                for z in range(z0, z1 + 1):
                    hd = s.outer_dy(x, z)
                    for d in range(1, w + 1):
                        s.put((x, YC + hd + d, z), col['channel'], 'channel')
                g['hull_dy'].append(s.outer_dy(x, z1))
            # deadeyes ＋ chain plates
            hx, hz = M['hounds']
            for i, xd in enumerate(xs):
                xi = int(round(xd))
                yo = YC + s.outer_dy(xi, z1) + W            # 外緣那一格
                for dx in (-1, 0, 1):
                    for dz in (0, 1, 2):
                        if abs(dx) == 1 and dz in (0, 2):
                            continue
                        for t in range(P['deadeye']['thick']):
                            s.put((xi + dx, yo - t, z1 + 1 + dz), col['deadeye'], 'deadeye')
                nm = '%s-channel.deadeye-S%d' % (M['mast'], i + 1)
                s.anchors.append({'name': nm, 'owner': P['subwork']['id'], 'kind': 'deadeye', 'side': 'S', 'world': [xi, yo, z1 + 3],
                                  'for': 'shroud %d' % (i + 1) if i < M['shrouds'] else 'backstay %d' % (i + 1 - M['shrouds'])})
                nm = '%s-channel.deadeye-P%d' % (M['mast'], i + 1)
                s.anchors.append({'name': nm, 'owner': P['subwork']['id'], 'kind': 'deadeye', 'side': 'P', 'world': [xi, 2 * YC - yo, z1 + 3],
                                  'for': 'shroud %d' % (i + 1) if i < M['shrouds'] else 'backstay %d' % (i + 1 - M['shrouds'])})
                # chain plate：deadeye 底下（channel 外緣、z0 − 1）→ z plate_to_z 的船殼表面
                k = (xd - hx) / (z1 - hz)                   # 每降 1 格 z，x 走多少（往船尾為負）
                zb = P['plate_to_z']
                xb2 = xd + (zb - z1) * k
                xb2i = int(round(xb2))
                # 不要擋在 gun deck 砲門前面（v1 主桅那組有好幾根斜過砲門，像一把梳子）：下端往前／後挪最少的格數；
                # 10 格內都找不到空檔 ⇒ 在白帶上方（z 105）收住
                mv = None
                for dlt in sorted(range(-10, 11), key=abs):
                    if s.plate_clear(xi, xb2i + dlt, z0 - 1, zb):
                        mv = dlt
                        break
                if mv is None:
                    zb2 = 105
                    xe = int(round(xi + (xb2i - xi) * (zb2 - (z0 - 1)) / (zb - (z0 - 1))))
                    s.line((xi, yo, z0 - 1), (xe, YC + s.outer_dy(xe, zb2) + 1, zb2), col['plate'], 'plate')
                    s.plate_moves.append({'mast': M['mast'], 'i': i + 1, 'move': None, 'ends_z': zb2})
                else:
                    xb = xb2i + mv
                    s.line((xi, yo, z0 - 1), (xb, YC + s.outer_dy(xb, zb) + 1, zb), col['plate'], 'plate')
                    if mv:
                        s.plate_moves.append({'mast': M['mast'], 'i': i + 1, 'move': mv})
            s.groups.append(g)

    def verify(s):
        v = {'cells': len(s.cells), 'by_kind': {}, 'colors': {}}
        for k, c in s.cells.items():
            v['by_kind'][s.kind[k]] = v['by_kind'].get(s.kind[k], 0) + 1
            v['colors'][str(c)] = v['colors'].get(str(c), 0) + 1
        mir = {(x, 2 * YC - y, z): c for (x, y, z), c in s.cells.items()}
        v['overlap'] = sum(1 for k in list(s.cells) + list(mir) if s.solid(*k))
        v['mirror_overlap'] = sum(1 for k in mir if k in s.cells)
        A = s.G > 0
        for k in list(s.cells) + list(mir):
            A[k[0] - XA, k[1], k[2] - ZA] = True
        lab, n = ndimage.label(A)
        base = set(np.unique(lab[s.G > 0])) - {0}
        fl = [k for k in s.cells if lab[k[0] - XA, k[1], k[2] - ZA] not in base]
        v['floating'] = {'n': len(fl), 'first': [list(k) + [s.kind[k]] for k in fl[:6]]}

        def cav(sol):
            l, nn = ndimage.label(~sol)
            e = set(np.unique(np.concatenate([l[0].ravel(), l[-1].ravel(), l[:, 0].ravel(), l[:, -1].ravel(), l[:, :, 0].ravel(), l[:, :, -1].ravel()]))) - {0}
            return int(nn - len(e))
        v['cavities_box'] = {'before': cav(s.G > 0), 'after': cav(A)}
        bx = s.P['subwork']['box']
        out_box = [k for k in s.cells if not all(bx['at'][a] <= k[a] < bx['at'][a] + bx['size'][a] for a in range(3))]
        assert not out_box, ('有格在固定的框外', out_box[:5])
        v['used'] = [[min(k[a] for k in s.cells), max(k[a] for k in s.cells)] for a in range(3)]
        v['groups'] = s.groups
        v['port_columns'] = len(s.portx)
        v['plate_moves'] = s.plate_moves
        v['anchors'] = len(s.anchors)
        v['expect_assembly_after'] = s.P['base']['assembly_voxels'] + 2 * len(s.cells)
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'channels')
        os.makedirs(out, exist_ok=True)
        bx = s.P['subwork']['box']
        x0, y0, z0 = bx['at']
        p = os.path.join(out, 'side.vox.txt')
        rows = sorted((k[0] - x0, k[1] - y0, k[2] - z0, c) for k, c in s.cells.items())
        open(p, 'w', encoding='utf-8', newline='\n').write(
            '# side —— channels 一舷（y > 160；自己的座標，at=%d,%d,%d；另一舷 mirror=y、at.y ＝ %d）（%d 格）\n' % (x0, y0, z0, 321 - y0 - bx['size'][1], len(rows))
            + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        rp = os.path.join(s.design, 'rig_points_channels.json')
        json.dump({'note': '下 deadeye 頂（給 TASK-0502 shrouds／backstays 的下端）；P ＝ y < 160、S ＝ y > 160；世界座標', 'points': s.anchors},
                  open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        s.files = {'side': {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()},
                   'rig_points': {'points': len(s.anchors), 'sha256': hashlib.sha256(open(rp, 'rb').read()).hexdigest()}}


def render_sheet(C, path):
    f12, f14, f18 = DD._font(13), DD._font(15), DD._font(20)
    sc = 2
    xa, xb, za, zb = 150, 610, 70, 125
    D = dict(C.cells)

    def side():
        img = np.zeros((zb - za, xb - xa, 3), np.uint8)
        img[:] = DD.PAPER
        for ix, x in enumerate(range(xa, xb)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                for y in range(319, YC - 1, -1):
                    c = D.get((x, y, z))
                    if c is None and C.solid(x, y, z):
                        c = int(C.G[x - XA, y, z - ZA])
                    if c is not None:
                        img[iz, ix] = DP.rgb332(c)
                        break
        return Image.fromarray(img).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)

    def top():
        ya, yb = YC, YC + 80
        img = np.zeros((yb - ya, xb - xa, 3), np.uint8)
        img[:] = DD.PAPER
        for ix, x in enumerate(range(xa, xb)):
            for iy, y in enumerate(range(yb - 1, ya - 1, -1)):
                for z in range(zb - 1, za - 1, -1):
                    c = D.get((x, y, z))
                    if c is None and C.solid(x, y, z):
                        c = int(C.G[x - XA, y, z - ZA])
                    if c is not None:
                        img[iy, ix] = DP.rgb332(c)
                        break
        return Image.fromarray(img).resize(((xb - xa) * sc, (yb - ya) * sc), Image.NEAREST)
    s1, t1 = side(), top()
    PADL = 50
    W = PADL + (xb - xa) * sc + 50
    can = Image.new('RGB', (W, 80 + s1.size[1] + t1.size[1] + 160), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), C.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '正交投影、每格 %d px；上：從 y > 160 那一舷看（x %d–%d、z %d–%d）；下：俯視（y 160–239）' % (sc, xa, xb - 1, za, zb - 1), font=f12, fill=DD.INK)
    can.paste(s1, (PADL, 66))
    can.paste(t1, (PADL, 66 + s1.size[1] + 20))
    for x in range(200, xb, 50):
        dr.text((PADL + (x - xa) * sc - 8, 66 + s1.size[1] + 2), str(x), font=f12, fill=(130, 130, 130))
    v = C.v
    y = 66 + s1.size[1] + 20 + t1.size[1] + 16
    lines = ['一舷 %d 格（%s）—— 兩舷 %d；deadeye 固定點 %d 個；重疊 %d、浮空 %d、空腔 %s；組裝件預期 %d' % (
        v['cells'], '、'.join('%s %d' % kv for kv in v['by_kind'].items()), 2 * v['cells'], v['anchors'], v['overlap'], v['floating']['n'], v['cavities_box'], v['expect_assembly_after'])]
    for g in v['groups']:
        lines.append('%s：x %d–%d、deadeyes %s' % (g['mast'], g['x'][0], g['x'][1], g['deadeyes']))
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, W, y + 16))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    C = Channels(design)
    C.build()
    v = C.verify()
    C.write()
    v['files'] = C.files
    json.dump(v, open(os.path.join(design, 'verify_channels.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(C, os.path.join(design, 'sheet16_channels_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('groups',)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
