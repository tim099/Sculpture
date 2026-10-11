# 新圖紙 17（甲板繫繩點）：plan.json 的 belaying 段 ＋ 組裝件的現況（這兩件加進來之前）
#   ⇒ masks/belaying/{fife,side}.vox.txt、design/rig_points_belaying.json、verify_belaying.json、sheet17_belaying_v1.png
# 用法：python -I draft_belaying.py <design 資料夾>
#   · fife：中線整件（世界座標、at 0,0,0），關聯進 spar deck 子作品
#   · side：舷牆 pin rails ＋ cleats，只做 y > 160 那一舷（自己的座標，at ＝ box.at；另一舷 mirror=y）
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402

YC = 160
XA, XB, ZA, ZB = 100, 700, 90, 140
PLUS = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
SQ3 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)]


class Belaying:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['belaying']
        B = s.P['base']
        a = export_list(ASSEMBLY, draft=False, hide_links=','.join(B['hide_links']))
        assert len(a) == B['assembly_voxels'], ('讀到的現況格數對不上', len(a), B['assembly_voxels'])
        m = a[(a[:, 0] >= XA) & (a[:, 0] < XB) & (a[:, 2] >= ZA) & (a[:, 2] < ZB)]
        s.G = np.zeros((XB - XA, 320, ZB - ZA), np.uint8)
        s.G[m[:, 0] - XA, m[:, 1], m[:, 2] - ZA] = m[:, 3]
        s.fife, s.side = {}, {}
        s.kind = {}
        s.hit = {}            # 想放但那一格已經是實心（現況）⇒ 設計錯，應該 0
        s.anchors = []

    def solid(s, x, y, z):
        return s.G[x - XA, y, z - ZA] > 0

    def deck(s, x):
        for a, b, z in s.P['deck_z']['segments']:
            if (a is None or x >= a) and (b is None or x < b):
                return z
        raise ValueError(x)

    def put(s, store, k, c, kind):
        if k in store:
            return False
        if s.solid(*k):
            s.hit[kind] = s.hit.get(kind, 0) + 1
            return False
        store[k] = int(c)
        s.kind[k] = kind
        return True

    def anchor(s, name, k, kind, side, owner):
        s.anchors.append({'name': name, 'owner': owner, 'kind': kind, 'side': side, 'world': list(k)})

    # ── fife rails ＋ bitts ──
    def build_fife(s):
        F, col = s.P['fife'], s.P['colors']
        own = s.P['subworks']['fife']['id']
        st = s.fife
        for M in F['masts']:
            m = M['mast']
            zd = s.deck(int(M['xm']))
            zr = zd + F['rail_h']
            x0, w = M['rail_x0'], F['rail_w']
            xr = x0 + w // 2                                   # athwartship rail 的中線
            n = M['athwart']
            assert n % 2 == 1, ('athwartship rail 要奇數格才對中線對稱', m, n)
            ys = range(YC - n // 2, YC + n // 2 + 1)
            xb = x0 + M['side_len']                            # bitt 中心 x
            bh = M['bitt_h']
            # bitts（先放 ⇒ side rail 接進去的那幾格算 bitt）
            for sd, sg in (('P', -1), ('S', 1)):
                c = YC + sg * M['side_dy']
                for dx, dy in SQ3:
                    for z in range(zd, zd + bh):
                        s.put(st, (xb + dx, c + dy, z), col['bitt'], 'bitt')
                for z in (zd + bh - 7, zd + bh - 6):           # 外側面的 sheave 槽
                    k = (xb, c + sg, z)
                    st[k] = col['sheave']
                for x in range(xb - 4, xb + 5):                # 鐵 cross pin（前後穿過）
                    s.put(st, (x, c, zd + bh - 3), col['cross_pin'], 'cross_pin')
                for dx, hh in ((2, 3), (3, 2), (4, 1)):        # 前面的黑 knee
                    for z in range(zd, zd + hh):
                        s.put(st, (xb + dx, c, z), col['knee'], 'knee')
                s.anchor('%s-bitt-%s' % (m, sd), (xb, c, zd + bh - 1), 'bitt', sd, own)
            # athwartship rail
            for x in range(x0, x0 + w):
                for y in ys:
                    s.put(st, (x, y, zr), col['rail'], 'rail')
            # side rails（從 athwartship rail 往前接到 bitt）
            for sg in (-1, 1):
                c = YC + sg * M['side_dy']
                for x in range(x0, xb - 1):
                    for dy in (-1, 0, 1):
                        s.put(st, (x, c + dy, zr), col['rail'], 'rail')
            # baluster（athwartship rail 底下）
            for dy0 in M['posts']:
                yc = YC + dy0
                for i, z in enumerate(range(zd, zr)):
                    shape = SQ3 if i in (0, F['rail_h'] - 1) else PLUS   # 座與頂 3×3、中間十字（v1 的腰一圈渲出來一節一節像串珠 ⇒ 拿掉）
                    for dx, dy in shape:
                        s.put(st, (xr + dx, yc + dy, z), col['post'], 'post')
            # belaying pins
            posts = [YC + d for d in M['posts']]
            k = 0
            J = (n // 2 - 1) // F['pin_step']
            for y in [YC + F['pin_step'] * j for j in range(-J, J + 1)]:   # 從中線往兩邊每 pin_step 一根 ⇒ 左右對稱
                if any(abs(y - p) <= 1 for p in posts):
                    continue
                k += 1
                s.pin(st, (xr, y, zr), F, col['pin'])
                s.anchor('%s-fife.rail-%d' % (m, k), (xr, y, zr + F['pin_up']), 'pin', 'P' if y < YC else ('S' if y > YC else 'CL'), own)
            for sd, sg in (('P', -1), ('S', 1)):
                c = YC + sg * M['side_dy']
                for j, x in enumerate(range(x0 + w + 1, xb - 2, F['pin_step'])):
                    s.pin(st, (x, c, zr), F, col['pin'])
                    s.anchor('%s-fife.side-%s%d' % (m, sd, j + 1), (x, c, zr + F['pin_up']), 'pin', sd, own)

    def pin(s, st, k, F, c):
        x, y, z = k
        for dz in list(range(1, F['pin_up'] + 1)) + [-d for d in range(1, F['pin_down'] + 1)]:
            s.put(st, (x, y, z + dz), c, 'pin')

    # ── 舷牆 pin rails ＋ cleats（S 那一舷）──
    def outer_dy(s, x, z):
        col = np.where(s.G[x - XA, YC:, z - ZA] > 0)[0]
        return int(col.max()) if len(col) else -1

    def inner_y(s, x, z):
        col = np.where(s.G[x - XA, 185:, z - ZA] > 0)[0]
        assert len(col), ('舷牆內側找不到', x, z)
        return 185 + int(col.min())

    def gaps(s):
        lo, hi = s.P['pinrails']['x_range']
        portx = set()
        for x in range(lo - 30, hi + 30):
            # 跟 channels 那支同一把尺，但上面那層取 z 106：現況已經有 channels（z 109–110 往外 12 格），z 110 會把它當成「外板被鋸開」
            a, b = s.outer_dy(x, 95), s.outer_dy(x, 106)
            if b >= 0 and (a < 0 or a < b - 4):
                portx.add(x)
        # chain plates 在 z 106 還伸在船殼外面 ⇒ 也會被量成「縮進去」，但只有 1–2 格寬；砲門 ≈ 10 格 ⇒ 連續 6 格以上才算
        runs = []
        for x in sorted(portx):
            if runs and x == runs[-1][-1] + 1:
                runs[-1].append(x)
            else:
                runs.append([x])
        portx = {x for r in runs if len(r) >= 6 for x in r}
        s.port_runs = [[r[0], r[-1]] for r in runs if len(r) >= 6]
        s.portx = portx
        out, run = [], []
        for x in range(lo, hi + 1):
            if x in portx:
                if run:
                    out.append(run)
                run = []
            else:
                run.append(x)
        if run:
            out.append(run)
        # 只要兩頭都是砲門的空檔（第一段與最後一段不完整，不算）
        return [(r[0], r[-1]) for r in out if r[0] - 1 in portx and r[-1] + 1 in portx]

    def build_side(s):
        R, Cl, col = s.P['pinrails'], s.P['cleats'], s.P['colors']
        own = s.P['subworks']['side']['id']
        st = s.side
        s.gap_list = s.gaps()
        s.rails = []
        for g0, g1 in s.gap_list:
            L = min(R['max_len'], g1 - g0 + 1 - 2 * R['clear_ends'])
            if L < R['min_len']:
                continue
            xc = (g0 + g1) / 2
            xs = list(range(int(round(xc - (L - 1) / 2)), int(round(xc - (L - 1) / 2)) + L))
            zd = min(s.deck(x) for x in xs)                    # 跨過甲板高低差（570）的那根取低的那段 ⇒ pins 不會頂到舷牆上緣
            zr = zd + R['rail_h']
            k = len(s.rails) + 1
            for x in xs:
                yi = s.inner_y(x, zr)
                for d in range(1, R['depth'] + 1):
                    s.put(st, (x, yi - d, zr), col['rail'], 'pinrail')
            for x in (xs[0], xs[-1]):
                yi = s.inner_y(x, zr)
                for dz in (1, 2):
                    s.put(st, (x, yi - 1, zr - dz), col['rail'], 'bracket')
            pins = list(range(xs[0] + 1, xs[-1], R['pin_step']))
            for j, x in enumerate(pins):
                yp = s.inner_y(x, zr) - R['depth']
                s.pin(st, (x, yp, zr), R, col['pin'])
                s.anchor('pinrail-%d.pin-%d' % (k, j + 1), (x, yp, zr + R['pin_up']), 'pin', 'S', own)
            s.rails.append({'k': k, 'x': [xs[0], xs[-1]], 'z': zr, 'pins': len(pins), 'gap': [g0, g1]})
        # cleats：每個 x_target 取最近的砲門空檔中心
        s.cleat_list = []
        for i, t in enumerate(Cl['x_targets']):
            g0, g1 = min(s.gap_list, key=lambda g: abs((g[0] + g[1]) / 2 - t))
            xc = (g0 + g1) // 2
            zc = s.deck(xc) + Cl['z_above_deck']
            half = Cl['len'] // 2
            yb = s.inner_y(xc, zc) - 2
            for x in range(xc - Cl['foot'] // 2 + 1, xc + Cl['foot'] // 2 + 1):
                for z in range(zc, zc + Cl['h']):
                    s.put(st, (x, s.inner_y(x, z) - 1, z), col['cleat'], 'cleat')
            for x in range(xc - half + 1, xc + half + 1):
                end = x in (xc - half + 1, xc + half)
                for z in range(zc, zc + Cl['h']):
                    if end and z == zc:
                        continue                               # 兩頭只留上面那格 ⇒ 角
                    s.put(st, (x, yb, z), col['cleat'], 'cleat')
            s.anchor('cleat-%d' % (i + 1), (xc, yb, zc + Cl['h'] - 1), 'cleat', 'S', own)
            s.cleat_list.append({'k': i + 1, 'x': xc, 'z': zc, 'gap': [g0, g1]})

    def verify(s):
        v = {'fife': len(s.fife), 'side': len(s.side), 'by_kind': {}, 'colors': {}}
        for k in list(s.fife) + list(s.side):
            v['by_kind'][s.kind[k]] = v['by_kind'].get(s.kind[k], 0) + 1
        for st in (s.fife, s.side):
            for c in st.values():
                v['colors'][str(c)] = v['colors'].get(str(c), 0) + 1
        v['hit_existing'] = s.hit
        mir = {(x, 2 * YC - y, z): c for (x, y, z), c in s.side.items()}
        v['mirror_overlap_self'] = sum(1 for k in mir if k in s.side)
        v['mirror_overlap_world'] = sum(1 for k in mir if s.solid(*k))
        v['mirror_overlap_fife'] = sum(1 for k in mir if k in s.fife)
        v['fife_side_overlap'] = sum(1 for k in s.side if k in s.fife)
        # 左右對稱（fife 本身、side 對鏡像後的現況）
        v['fife_asym'] = sum(1 for (x, y, z), c in s.fife.items() if s.fife.get((x, 2 * YC - y, z)) != c)
        A = s.G > 0
        new = list(s.fife) + list(s.side) + list(mir)
        for k in new:
            A[k[0] - XA, k[1], k[2] - ZA] = True
        lab, n = ndimage.label(A)
        base = set(np.unique(lab[s.G > 0])) - {0}
        fl = [k for k in new if lab[k[0] - XA, k[1], k[2] - ZA] not in base]
        v['floating'] = {'n': len(fl), 'first': [list(k) for k in fl[:6]]}

        def cav(sol):
            l, nn = ndimage.label(~sol)
            e = set(np.unique(np.concatenate([l[0].ravel(), l[-1].ravel(), l[:, 0].ravel(), l[:, -1].ravel(), l[:, :, 0].ravel(), l[:, :, -1].ravel()]))) - {0}
            return int(nn - len(e))
        v['cavities_box'] = {'before': cav(s.G > 0), 'after': cav(A)}
        bx = s.P['subworks']['side']['box']
        out_box = [k for k in s.side if not all(bx['at'][a] <= k[a] < bx['at'][a] + bx['size'][a] for a in range(3))]
        assert not out_box, ('有格在固定的框外', out_box[:5])
        v['side_used'] = [[min(k[a] for k in s.side), max(k[a] for k in s.side)] for a in range(3)]
        v['port_columns'] = len(s.portx)
        v['port_runs'] = s.port_runs
        v['gaps'] = len(s.gap_list)
        v['rails'] = s.rails
        v['cleats'] = s.cleat_list
        v['anchors'] = {'S_side': len([a for a in s.anchors if a['owner'] == s.P['subworks']['side']['id']]),
                        'fife': len([a for a in s.anchors if a['owner'] == s.P['subworks']['fife']['id']])}
        v['expect_assembly_after'] = s.P['base']['assembly_voxels'] + len(s.fife) + 2 * len(s.side)
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'belaying')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        p = os.path.join(out, 'fife.vox.txt')
        rows = sorted((x, y, z, c) for (x, y, z), c in s.fife.items())
        open(p, 'w', encoding='utf-8', newline='\n').write(
            '# fife —— 三根桅的 fife rails＋bitts（世界座標、at 0,0,0）（%d 格）\n' % len(rows) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        s.files['fife'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        bx = s.P['subworks']['side']['box']
        x0, y0, z0 = bx['at']
        p = os.path.join(out, 'side.vox.txt')
        rows = sorted((x - x0, y - y0, z - z0, c) for (x, y, z), c in s.side.items())
        open(p, 'w', encoding='utf-8', newline='\n').write(
            '# side —— 舷牆 pin rails＋cleats 一舷（y > 160；自己的座標，at=%d,%d,%d；另一舷 mirror=y、at.y ＝ %d）（%d 格）\n' % (x0, y0, z0, 321 - y0 - bx['size'][1], len(rows))
            + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        s.files['side'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        pts = []
        for a in s.anchors:
            pts.append(a)
            if a['side'] == 'S' and a['owner'] == s.P['subworks']['side']['id']:
                b = dict(a)
                b['name'] = a['name']
                b['side'] = 'P'
                b['world'] = [a['world'][0], 2 * YC - a['world'][1], a['world'][2]]
                b['via'] = s.P['subworks']['side']['mirror_link']
                pts.append(b)
        rp = os.path.join(s.design, 'rig_points_belaying.json')
        json.dump({'note': '甲板繫繩點（給之後的動索）：belaying pin 頂、bitt 頂、cleat 角的中間；P ＝ y < 160、S ＝ y > 160；世界座標。舷牆那件只做 S，P 是 via 那條鏡像關聯（同名）', 'points': pts},
                  open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        s.files['rig_points'] = {'points': len(pts), 'sha256': hashlib.sha256(open(rp, 'rb').read()).hexdigest()}


def render_sheet(C, path):
    f12, f18 = DD._font(13), DD._font(20)
    D = dict(C.fife)
    D.update(C.side)
    D.update({(x, 2 * YC - y, z): c for (x, y, z), c in C.side.items()})

    def color_at(x, y, z):
        c = D.get((x, y, z))
        if c is None and XA <= x < XB and ZA <= z < ZB and C.solid(x, y, z):
            c = int(C.G[x - XA, y, z - ZA])
        return c

    def top(xa, xb, ya, yb, zt, sc):
        img = np.zeros((yb - ya, xb - xa, 3), np.uint8)
        img[:] = DD.PAPER
        for ix, x in enumerate(range(xa, xb)):
            for iy, y in enumerate(range(yb - 1, ya - 1, -1)):
                for z in range(zt, ZA - 1, -1):
                    c = color_at(x, y, z)
                    if c is not None:
                        img[iy, ix] = DP.rgb332(c)
                        break
        return Image.fromarray(img).resize(((xb - xa) * sc, (yb - ya) * sc), Image.NEAREST)

    def from_aft(x0, x1, ya, yb, za, zb, sc):
        img = np.zeros((zb - za, yb - ya, 3), np.uint8)
        img[:] = DD.PAPER
        for iy, y in enumerate(range(ya, yb)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                for x in range(x0, x1):
                    c = color_at(x, y, z)
                    if c is not None:
                        img[iz, iy] = DP.rgb332(c)
                        break
        return Image.fromarray(img).resize(((yb - ya) * sc, (zb - za) * sc), Image.NEAREST)

    def bulwark(xa, xb, za, zb, sc):
        img = np.zeros((zb - za, xb - xa, 3), np.uint8)
        img[:] = DD.PAPER
        for ix, x in enumerate(range(xa, xb)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                for y in range(186, 320):
                    c = color_at(x, y, z)
                    if c is not None:
                        img[iz, ix] = DP.rgb332(c)
                        break
        return Image.fromarray(img).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)

    tiles = []
    for M in C.P['fife']['masts']:
        xm = int(M['xm'])
        zd = C.deck(xm)
        t = top(xm - 14, xm + 22, 128, 193, zd + 16, 5)
        e = from_aft(M['rail_x0'] - 3, M['rail_x0'] + 40, 128, 193, zd - 1, zd + 18, 5)
        tiles.append((M['mast'], t, e))
    PADL = 40
    colw = max(t.size[0] for _, t, _ in tiles) + 30
    W = max(PADL + colw * 3, PADL + (640 - 140) * 3 + 40)
    b = bulwark(140, 640, 100, 132, 3)
    H = 80 + max(t.size[1] + e.size[1] for _, t, e in tiles) + 60 + b.size[1] + 200
    can = Image.new('RGB', (W, H), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), C.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '正交投影；上排：俯視（每格 5 px，x 往右 ＝ 往船頭）；中排：從船尾往前看（每格 5 px）；下排：從中線看 S 舷舷牆內側（x 140–639、z 100–131，每格 3 px）', font=f12, fill=DD.INK)
    y0 = 66
    for i, (m, t, e) in enumerate(tiles):
        x = PADL + i * colw
        dr.text((x, y0), m, font=f12, fill=DD.INK)
        can.paste(t, (x, y0 + 18))
        can.paste(e, (x, y0 + 18 + t.size[1] + 10))
    y = y0 + 18 + max(t.size[1] + e.size[1] for _, t, e in tiles) + 30
    can.paste(b, (PADL, y))
    for xx in range(150, 640, 50):
        dr.text((PADL + (xx - 140) * 3 - 8, y + b.size[1] + 2), str(xx), font=f12, fill=(130, 130, 130))
    v = C.v
    y += b.size[1] + 24
    lines = ['fife 件 %d 格；舷牆一舷 %d 格（兩舷 %d）；%s' % (v['fife'], v['side'], 2 * v['side'], '、'.join('%s %d' % kv for kv in v['by_kind'].items())),
             '撞到現況 %s、鏡像重疊 %d/%d/%d、fife 左右不對稱 %d、浮空 %d、空腔 %s；組裝件預期 %d' % (
                 v['hit_existing'] or 0, v['mirror_overlap_self'], v['mirror_overlap_world'], v['mirror_overlap_fife'], v['fife_asym'], v['floating']['n'], v['cavities_box'], v['expect_assembly_after']),
             'pin rails %d 根（gun deck 砲門空檔 %d 個）：%s' % (len(v['rails']), v['gaps'], ' '.join('%d–%d' % tuple(r['x']) for r in v['rails'])),
             'cleats：%s；固定點 fife %d、舷牆一舷 %d' % (' '.join('x%d z%d' % (c['x'], c['z']) for c in v['cleats']), v['anchors']['fife'], v['anchors']['S_side'])]
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, W, y + 16))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    C = Belaying(design)
    C.build_fife()
    C.build_side()
    v = C.verify()
    C.write()
    v['files'] = C.files
    json.dump(v, open(os.path.join(design, 'verify_belaying.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(C, os.path.join(design, 'sheet17_belaying_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('rails', 'cleats')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
