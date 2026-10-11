# 新圖紙 15（舵子作品）：plan.json 的 rudder 段 ＋ 組裝件的現況（舵加進來之前）
#   ⇒ masks/rudder/rudder.vox.txt（子作品 at 0,0,0）、verify_rudder.json、sheet15_rudder_v1.png；固定點寫進 verify
# 用法：python -I draft_rudder.py <design 資料夾>
#   · 每一欄 (y, z)：從後緣線到「那一欄最後面的實心（艉柱、wing transom、counter）」前一格 ⇒ 前緣貼著艉柱、頂端順著 counter 收進去
#   · 前半 5 格厚、後半 3 格厚；水線以下銅、以上黑
#   · pintle／gudgeon 帶：舵板兩側凸 1 格；往前接到船殼表面（每一層 z 跟船外相通、貼著實心的空格）
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402

YC = 160
XA, XB, ZB = 90, 220, 100


class Rudder:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['rudder']
        B = s.P['base']
        a = export_list(ASSEMBLY, draft=False, hide_links=','.join(B['hide_links']))
        assert len(a) == B['assembly_voxels'], ('讀到的現況格數對不上', len(a), B['assembly_voxels'])
        m = a[(a[:, 0] >= XA) & (a[:, 0] < XB) & (a[:, 2] < ZB)]
        s.G = np.zeros((XB - XA, 320, ZB), np.uint8)
        s.G[m[:, 0] - XA, m[:, 1], m[:, 2]] = m[:, 3]
        s.cells = {}
        s.kind = {}

    def put(s, k, c, kind):
        if k in s.cells or s.G[k[0] - XA, k[1], k[2]]:
            return
        s.cells[k] = int(c)
        s.kind[k] = kind

    def aft_face(s, y, z):
        col = np.where(s.G[:, y, z] > 0)[0]
        return int(col.min()) + XA if len(col) else None

    def build(s):
        P = s.P
        A = np.array(P['aft_edge'], float)
        aft = lambda z: float(np.interp(z, A[:, 1], A[:, 0]))
        hw = P['half_width']
        col = P['colors']
        s.profile = []
        for z in range(P['bottom_z'], P['top_z'] + 1):
            xa = int(math.ceil(aft(z) - 0.5))
            # 前緣：中線那一欄最後面的實心前一格
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
                    c = col['copper'] if z < P['lwl'] else col['black']
                    s.put((x, y, z), c, 'rudder')
        # pintle／gudgeon 帶
        St = P['straps']
        zs = St['z']
        lens = np.interp(zs, [min(zs), max(zs)], St['hull_len'])
        st2 = ndimage.generate_binary_structure(2, 1)
        R = np.zeros_like(s.G, bool)
        for k in s.cells:
            R[k[0] - XA, k[1], k[2]] = True
        S = (s.G > 0) | R
        s.strap_rows = []
        for z0, L in zip(zs, lens):
            for z in range(z0, z0 + St['rows']):
                if z >= ZB:
                    continue
                sol = S[:, :, z]
                lab, n = ndimage.label(~sol, structure=st2)
                seeds = set(np.unique(np.concatenate([lab[0], lab[:, 0], lab[:, -1]]))) - {0}
                ext = np.isin(lab, list(seeds))
                shell = ndimage.binary_dilation(sol, st2) & ext
                xf0 = s.aft_face(YC, z)
                rz = [k for k in s.cells if k[2] == z]
                xa_r = min(k[0] for k in rz) if rz else None
                cnt = 0
                for i, j in np.argwhere(shell):
                    x, y = i + XA, j
                    # 只貼在艉柱兩側（|dy| ≤ 8）—— v1 放到 40，z 70 那道在寬的 tuck 上橫貫整個船尾
                    if abs(y - YC) > St['hull_half']:
                        continue
                    on_rudder = xa_r is not None and xa_r + St['rudder_aft_gap'] <= x < xf0
                    on_hull = xf0 is not None and xf0 <= x <= xf0 + L
                    if (on_rudder or on_hull) and abs(y - YC) >= 2:
                        s.put((x, y, z), col['strap'], 'strap')
                        cnt += 1
                s.strap_rows.append({'z': z, 'cells': cnt, 'hull_to_x': round(float(xf0 + L), 1) if xf0 else None})
        # 固定點
        za = P['anchors']['pendant_z']
        xa = min(k[0] for k in s.cells if k[2] == za and s.kind[k] == 'rudder')
        s.anchors = [{'name': 'rudder.pendant-P', 'owner': P['subwork']['id'], 'kind': 'eyebolt', 'side': 'P', 'world': [xa, YC - hw['aft'], za]},
                     {'name': 'rudder.pendant-S', 'owner': P['subwork']['id'], 'kind': 'eyebolt', 'side': 'S', 'world': [xa, YC + hw['aft'], za]}]

    def verify(s):
        v = {'cells': len(s.cells), 'by_kind': {}, 'colors': {}}
        for k, c in s.cells.items():
            v['by_kind'][s.kind[k]] = v['by_kind'].get(s.kind[k], 0) + 1
            v['colors'][str(c)] = v['colors'].get(str(c), 0) + 1
        v['overlap'] = sum(1 for k in s.cells if s.G[k[0] - XA, k[1], k[2]])
        v['mirror_mismatch'] = sum(1 for (x, y, z), c in s.cells.items() if s.cells.get((x, 2 * YC - y, z)) != c)
        A = s.G > 0
        N = np.zeros_like(A)
        for k in s.cells:
            A[k[0] - XA, k[1], k[2]] = True
        lab, n = ndimage.label(A)
        base = set(np.unique(lab[s.G > 0])) - {0}
        v['floating'] = sum(1 for k in s.cells if lab[k[0] - XA, k[1], k[2]] not in base)

        def cav(sol):
            l, nn = ndimage.label(~sol)
            e = set(np.unique(np.concatenate([l[0].ravel(), l[-1].ravel(), l[:, 0].ravel(), l[:, -1].ravel(), l[:, :, 0].ravel(), l[:, :, -1].ravel()]))) - {0}
            return int(nn - len(e))
        v['cavities_box'] = {'before': cav(s.G > 0), 'after': cav(A)}
        pr = s.profile
        v['profile'] = {'z': [pr[0][0], pr[-1][0]], 'bottom_x': [pr[0][1], pr[0][2]], 'top_x': [pr[-1][1], pr[-1][2]],
                        'width_bottom': pr[0][2] - pr[0][1] + 1, 'width_top': pr[-1][2] - pr[-1][1] + 1}
        v['straps'] = s.strap_rows
        v['anchors'] = s.anchors
        v['expect_assembly_after'] = s.P['base']['assembly_voxels'] + len(s.cells)
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'rudder')
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, 'rudder.vox.txt')
        rows = sorted((k[0], k[1], k[2], c) for k, c in s.cells.items())
        open(p, 'w', encoding='utf-8', newline='\n').write('# rudder —— 舵＋pintle／gudgeon 帶（作品座標，at=0,0,0）（%d 格）\n' % len(rows)
                                                           + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        s.files = {'rudder': {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}


def render_sheet(R, path):
    f12, f14, f18 = DD._font(13), DD._font(15), DD._font(20)
    sc = 6
    xa, xb, za, zb = 98, 175, 0, 100

    def side(with_new):
        img = np.zeros((zb - za, xb - xa, 3), np.uint8)
        img[:] = DD.PAPER
        for ix, x in enumerate(range(xa, xb)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                for y in range(319, -1, -1):
                    k = (x, y, z)
                    c = R.cells.get(k) if with_new else None
                    if c is None and R.G[x - XA, y, z]:
                        c = int(R.G[x - XA, y, z])
                    if c is not None:
                        img[iz, ix] = DP.rgb332(c)
                        break
        return Image.fromarray(img).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)

    def astern():
        ya, yb = YC - 30, YC + 31
        img = np.zeros((zb - za, yb - ya, 3), np.uint8)
        img[:] = DD.PAPER
        for iy, y in enumerate(range(ya, yb)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                for x in range(XA, XB):
                    k = (x, y, z)
                    c = R.cells.get(k)
                    if c is None and R.G[x - XA, y, z]:
                        c = int(R.G[x - XA, y, z])
                    if c is not None:
                        img[iz, iy] = DP.rgb332(c)
                        break
        return Image.fromarray(img).resize(((yb - ya) * sc, (zb - za) * sc), Image.NEAREST)
    s0, s1, a1 = side(False), side(True), astern()
    PADL = 50
    W = PADL + 2 * (xb - xa) * sc + 60 + 61 * sc + 60
    can = Image.new('RGB', (W, 80 + (zb - za) * sc + 150), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), R.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '正交投影、每格 %d px；側面從 y > 160 那一舷看（x %d–%d、z %d–%d）；右：從正後方看（觀者左手邊 ＝ y < 160）' % (sc, xa, xb - 1, za, zb - 1), font=f12, fill=DD.INK)
    x0 = PADL
    for title, im in (('現在', s0), ('新圖紙 15 v1', s1), ('正後方', a1)):
        dr.text((x0, 62), title, font=f14, fill=DD.INK)
        can.paste(im, (x0, 84))
        x0 += im.size[0] + 60
    for z in range(0, zb, 10):
        dr.text((PADL - 30, 84 + (zb - 1 - z) * sc - 7), str(z), font=f12, fill=(130, 130, 130))
    v = R.v
    y = 84 + (zb - za) * sc + 16
    lines = ['舵 %d 格（%s）；z %s、底寬 %d、頂寬 %d；重疊 %d、浮空 %d、鏡像差 %d、空腔 %s；組裝件預期 %d' % (
        v['cells'], '、'.join('%s %d' % kv for kv in v['by_kind'].items()), v['profile']['z'], v['profile']['width_bottom'], v['profile']['width_top'],
        v['overlap'], v['floating'], v['mirror_mismatch'], v['cavities_box'], v['expect_assembly_after']),
        '出處：11 號（1927）sheer plan 的舵後緣、舵底、舵頭、六道 strap；前緣跟著作品的艉柱；設計決定見 plan.json rudder.decisions']
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, W, y + 16))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    R = Rudder(design)
    R.build()
    v = R.verify()
    R.write()
    v['files'] = R.files
    json.dump(v, open(os.path.join(design, 'verify_rudder.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(R, os.path.join(design, 'sheet15_rudder_v1.png'))
    print(json.dumps({k: v[k] for k in v if k != 'straps'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
