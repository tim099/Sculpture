# 新圖紙 21（錨）：plan.json 的 anchors 段 ＋ 組裝件的現況（錨加進來之前）
#   ⇒ masks/anchors/bower.vox.txt（一隻錨，自己的座標）、design/anchors_placement.json（兩條關聯的 at／mirror）、
#      verify_anchors.json、sheet21_anchors_v1.png
# 用法：python -I draft_anchors.py <design 資料夾>
#   · 一隻錨做一次（子作品 -anchor），用關聯掛到兩舷的 cathead：S 舷照原樣、P 舷 mirror=y
#   · 自己的座標：x ＝ 沿船長、y ＝ 橫向、z ＝ 高；shank 直立在 (cx, cy)，ring 在最上面、crown 在最下面
#   · 掛法（catted）：ring 頂那一格貼在 cathead 某一格的正下方；從 cathead 端面往船裡一格一格試，
#     兩舷都跟現況不重疊的第一格就是它（stock 方向兩種都試，plan 指定優先順序）
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402

YC = 160


class Anchor:
    """一隻 Admiralty 式（old pattern）bower anchor；stock 沿 y、arms 在 x-z 平面（orient='y'）。"""

    def __init__(s, A):
        s.A = A
        s.cells, s.kind = {}, {}

    def put(s, k, c, kind, over=False):
        if k in s.cells and not over:
            return
        s.cells[k] = int(c)
        s.kind[k] = kind

    def build(s):
        A, col = s.A, s.A['colors']
        W, L, H = A['size']
        cx, cy = A['cx'], A['cy']
        sh = A['shank']
        # shank：3×3 直立，crown 底 z0 到頂 z1
        for z in range(sh['z0'], sh['z1'] + 1):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    s.put((cx + dx, cy + dy, z), col['iron'], 'shank')
        # ring：在 x-z 平面（arms 同一面），圓心 (cx, ring_zc)，半徑 r，粗 1 格；下緣穿過 shank 頂
        R = A['ring']
        for x in range(cx - 6, cx + 7):
            for z in range(R['zc'] - 6, R['zc'] + 7):
                d = math.hypot(x - cx, z - R['zc'])
                if abs(d - R['r']) <= R['w']:
                    s.put((x, cy, z), col['iron'], 'ring')
        # stock：沿 y，木頭；中間粗（x 4、z 3）往兩端收（x 2、z 2）；兩道一組鐵箍
        st = A['stock']
        half = st['length'] // 2
        for dy in range(-half, half + 1):
            t = abs(dy) / half
            hx = st['half_x_mid'] + (st['half_x_end'] - st['half_x_mid']) * t
            hz = st['half_z_mid'] + (st['half_z_end'] - st['half_z_mid']) * t
            band = abs(dy) in st['bands']
            for x in range(cx - 3, cx + 4):
                for z in range(st['zc'] - 3, st['zc'] + 4):
                    if abs(x - cx) <= hx and abs(z - st['zc']) <= hz:
                        s.put((x, cy + dy, z), col['iron'] if band else col['wood'], 'band' if band else 'stock', over=True)
        # arms：x-z 平面上的圓弧，圓心 (cx, z0 + R)，從 θ0 到 θ1（兩邊對稱），截面 3 格寬（y）、在面內粗 arm_r
        ar = A['arms']
        zc = sh['z0'] + ar['R']
        steps = 400
        for i in range(steps + 1):
            th = math.radians(ar['th1'] * i / steps)
            rr = ar['r0'] + (ar['r1'] - ar['r0']) * i / steps
            for sgn in (-1, 1):
                px, pz = cx + sgn * ar['R'] * math.sin(th), zc - ar['R'] * math.cos(th)
                for x in range(int(px) - 3, int(px) + 4):
                    for z in range(int(pz) - 3, int(pz) + 4):
                        if math.hypot(x - px, z - pz) <= rr:
                            for dy in (-1, 0, 1):
                                s.put((x, cy + dy, z), col['iron'], 'arm')
        # palms（flukes）：貼在 arm 內側（朝圓心那一面）的平板，寬在 y 方向；中段最寬
        pa = A['palm']
        for i in range(steps + 1):
            thd = pa['th0'] + (pa['th1'] - pa['th0']) * i / steps
            th = math.radians(thd)
            u = (thd - pa['th0']) / (pa['th1'] - pa['th0'])
            w = pa['w_mid'] * math.sin(math.pi * min(1.0, 0.15 + u * 0.95))       # 中段最寬、兩頭收
            for sgn in (-1, 1):
                for off in pa['offsets']:
                    rr = ar['R'] - off
                    px, pz = cx + sgn * rr * math.sin(th), zc - rr * math.cos(th)
                    x, z = int(round(px)), int(round(pz))
                    for dy in range(-int(round(w)), int(round(w)) + 1):
                        s.put((x, cy + dy, z), col['iron'], 'palm')
        # bill：arm 尖端
        for sgn in (-1, 1):
            th = math.radians(ar['th1'])
            px, pz = cx + sgn * ar['R'] * math.sin(th), zc - ar['R'] * math.cos(th)
            s.put((int(round(px)), cy, int(round(pz)) + 1), col['iron'], 'bill')
        for k in list(s.cells):
            assert 0 <= k[0] < W and 0 <= k[1] < L and 0 <= k[2] < H, k
        s.ring_top = max(z for (x, y, z), kd in s.kind.items() if kd == 'ring')
        return s

    def rotated(s):
        """stock 改沿 x（x、y 對調）。"""
        o = Anchor(s.A)
        for (x, y, z), c in s.cells.items():
            o.cells[(y, x, z)] = c
            o.kind[(y, x, z)] = s.kind[(x, y, z)]
        o.ring_top = s.ring_top
        return o


class Rig:
    def __init__(s, design):
        s.design = design
        s.P = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['anchors']
        a = export_list(ASSEMBLY, draft=False)
        s.base_count = len(a)
        assert s.base_count == s.P['base']['assembly_voxels'], ('組裝件現況跟 plan 記的不一樣', s.base_count)
        s.W = np.zeros((1024, 320, 800), np.uint8)
        s.W[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
        s.anchor = Anchor(s.P['anchor']).build()

    def cathead_cells(s):
        C = s.P['cathead_box']
        x0, x1, y0, y1, z0, z1 = C['x'] + C['y'] + C['z']
        sub = s.W[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1]
        idx = np.argwhere(sub == C['color'])
        cells = [(x0 + i, y0 + j, z0 + k) for i, j, k in idx]
        # 每一欄最低那一格（下面要掛東西）
        low = {}
        for x, y, z in cells:
            if (x, y) not in low or z < low[(x, y)]:
                low[(x, y)] = z
        # 從端面往船裡：y 由大到小、同 y 時 x 由大到小
        return sorted(((x, y, z) for (x, y), z in low.items()), key=lambda q: (-q[1], -q[0]))

    def place_cells(s, an, at, mirror):
        W, L, H = s.P['anchor']['size'] if an.orient == 'y' else (s.P['anchor']['size'][1], s.P['anchor']['size'][0], s.P['anchor']['size'][2])
        p = np.array(list(an.cells), np.int32)
        if mirror:
            p[:, 1] = L - 1 - p[:, 1]
        return p + np.array(at), (W, L, H)

    def place(s):
        s.tries = []
        a_y = s.anchor
        a_y.orient = 'y'
        a_x = s.anchor.rotated()
        a_x.orient = 'x'
        cands = {'y': a_y, 'x': a_x}
        hang = s.cathead_cells()
        s.hang_cells = len(hang)
        for orient in s.P['orient_order']:
            an = cands[orient]
            cxl = s.P['anchor']['cx'] if orient == 'y' else s.P['anchor']['cy']
            cyl = s.P['anchor']['cy'] if orient == 'y' else s.P['anchor']['cx']
            size = s.P['anchor']['size'] if orient == 'y' else [s.P['anchor']['size'][1], s.P['anchor']['size'][0], s.P['anchor']['size'][2]]
            for hx, hy, hz in hang:
                at = [hx - cxl, hy - cyl, hz - 1 - an.ring_top]
                atP = [at[0], 321 - size[1] - at[1], at[2]]
                pS, _ = s.place_cells(an, at, False)
                pP, _ = s.place_cells(an, atP, True)
                if pS.min() < 0 or pP.min() < 0 or (pS[:, 2] >= 800).any():
                    continue
                hS = int((s.W[pS[:, 0], pS[:, 1], pS[:, 2]] > 0).sum())
                hP = int((s.W[pP[:, 0], pP[:, 1], pP[:, 2]] > 0).sum())
                s.tries.append({'orient': orient, 'hang': [int(hx), int(hy), int(hz)], 'hits_S': hS, 'hits_P': hP})
                if hS == 0 and hP == 0:
                    s.chosen = {'orient': orient, 'hang': [int(hx), int(hy), int(hz)], 'size': size}
                    s.an = an
                    s.links = [{'name': s.P['subwork']['link_prefix'] + 'S', 'at': [int(v) for v in at], 'mirror': ''},
                               {'name': s.P['subwork']['link_prefix'] + 'P', 'at': [int(v) for v in atP], 'mirror': 'y'}]
                    s.pS, s.pP = pS, pP
                    return
        raise SystemExit('兩舷都放得下的 cathead 掛點找不到：' + json.dumps(s.tries[:12], ensure_ascii=False))

    def verify(s):
        an = s.an
        v = {'anchor_cells': len(an.cells), 'orient': s.chosen['orient'], 'size': s.chosen['size'], 'hang_cathead_cell': s.chosen['hang'],
             'by_kind': {}, 'colors': {}}
        for k, kd in an.kind.items():
            v['by_kind'][kd] = v['by_kind'].get(kd, 0) + 1
            c = str(an.cells[k])
            v['colors'][c] = v['colors'].get(c, 0) + 1
        X = s.P['anchor']['cx'] if an.orient == 'y' else s.P['anchor']['cy']
        Y = s.P['anchor']['cy'] if an.orient == 'y' else s.P['anchor']['cx']
        v['asym_x'] = sum(1 for (x, y, z), c in an.cells.items() if an.cells.get((2 * X - x, y, z)) != c)
        v['asym_y'] = sum(1 for (x, y, z), c in an.cells.items() if an.cells.get((x, 2 * Y - y, z)) != c)
        A = np.zeros(tuple(s.chosen['size']), bool)
        for k in an.cells:
            A[k] = True
        v['anchor_components'] = int(ndimage.label(A)[1])
        allp = np.concatenate([s.pS, s.pP])
        v['overlap_world'] = int((s.W[allp[:, 0], allp[:, 1], allp[:, 2]] > 0).sum())
        v['overlap_each_other'] = len(allp) - len({tuple(q) for q in allp})
        # 掛住：每一隻跟現況 6 連通相接的格數（ring 頂貼 cathead）
        nb = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
        for nm, p in (('S', s.pS), ('P', s.pP)):
            touch = 0
            for q in map(tuple, p):
                for d in nb:
                    r = (q[0] + d[0], q[1] + d[1], q[2] + d[2])
                    if s.W[r] > 0:
                        touch += 1
                        break
            v['touch_world_' + nm] = touch
        # 錨離水線多高（crown 最低那一格）
        v['lowest_z'] = int(s.pS[:, 2].min())
        v['lwl_z'] = s.P['lwl_z']
        v['clear_of_hull_min'] = s.clearance()
        v['tries_before'] = len(s.tries) - 1
        v['links'] = s.links
        v['expect_assembly_after'] = s.base_count + 2 * len(an.cells)
        s.v = v
        return v

    def clearance(s):
        """S 那一隻每一格到現況最近實心格的距離（格），取最小（不含 ring 頂貼 cathead 那幾格的鄰居）。"""
        x0, y0, z0 = s.pS.min(0) - 6
        x1, y1, z1 = s.pS.max(0) + 7
        sub = s.W[x0:x1, y0:y1, z0:z1] > 0
        dist = ndimage.distance_transform_edt(~sub)
        q = s.pS - np.array([x0, y0, z0])
        ring_top = s.pS[:, 2] >= s.pS[:, 2].max() - 1
        d = dist[q[:, 0], q[:, 1], q[:, 2]][~ring_top]
        return round(float(d.min()), 2)

    def write(s):
        out = os.path.join(s.design, 'masks', 'anchors')
        os.makedirs(out, exist_ok=True)
        rows = sorted((x, y, z, c) for (x, y, z), c in s.an.cells.items())
        p = os.path.join(out, 'bower.vox.txt')
        open(p, 'w', encoding='utf-8', newline='\n').write(
            '# bower anchor —— 一隻（自己的座標，stock 沿 %s、shank 直立、ring 在上）（%d 格）\n' % (s.chosen['orient'], len(rows))
            + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        pl = os.path.join(s.design, 'anchors_placement.json')
        json.dump({'note': '兩舷 cathead 各掛一隻（關聯進組裝件；S 舷照原樣、P 舷 mirror=y）；at ＝ 子作品原點在世界的位置', 'subwork': s.P['subwork']['id'],
                   'size': s.chosen['size'], 'links': s.links},
                  open(pl, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        s.files = {'bower': {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()},
                   'placement': {'links': len(s.links), 'sha256': hashlib.sha256(open(pl, 'rb').read()).hexdigest()}}


def render_sheet(R, path):
    f12, f18 = DD._font(13), DD._font(20)
    an = R.an
    W, L, H = R.chosen['size']
    sc = 10

    def view(cells, dims, axes, flip_h=False):
        a, b, depth = axes
        img = np.zeros((dims[b], dims[a], 3), np.uint8)
        img[:] = DD.PAPER
        idx = {'x': 0, 'y': 1, 'z': 2}
        best = {}
        for k, c in cells.items():
            u, v_, d = k[idx[a]], k[idx[b]], k[idx[depth]]
            if (u, v_) not in best or d > best[(u, v_)][0]:
                best[(u, v_)] = (d, c)
        for (u, v_), (d, c) in best.items():
            img[dims[b] - 1 - v_, (dims[a] - 1 - u) if flip_h else u] = DP.rgb332(c)
        return img
    dims = {'x': W, 'y': L, 'z': H}
    side = Image.fromarray(view(an.cells, dims, ('x', 'z', 'y'))).resize((W * sc, H * sc), Image.NEAREST)
    front = Image.fromarray(view(an.cells, dims, ('y', 'z', 'x'))).resize((L * sc, H * sc), Image.NEAREST)
    top = Image.fromarray(view(an.cells, dims, ('x', 'y', 'z'))).resize((W * sc, L * sc), Image.NEAREST)
    # 擺放：從船頭正前方看（y–z）與從右舷看（x–z）；現況淡色、錨原色
    xa, xb, za, zb = 590, 720, 60, 150
    ya, yb = 90, 231
    occ_s, occ_f = {}, {}
    for p in (R.pS, R.pP):
        for q in map(tuple, p):
            # 2026-10-12 修：原本 P 舷寫死 36 ⇒ sheet21 v1 的正前方圖把左舷那隻畫成黑的（作品兩隻都是 146）
            c = R.an.cells.get(tuple(np.array(q) - np.array(R.links[0]['at']))) if p is R.pS else R.P['anchor']['colors']['iron']
            if xa <= q[0] < xb and za <= q[2] < zb:
                if (q[0], q[2]) not in occ_s or q[1] > occ_s[(q[0], q[2])][0]:
                    occ_s[(q[0], q[2])] = (q[1], c or 36)
            if ya <= q[1] < yb and za <= q[2] < zb:
                if (q[1], q[2]) not in occ_f or q[0] > occ_f[(q[1], q[2])][0]:
                    occ_f[(q[1], q[2])] = (q[0], c or 36)

    def place_view(occ, ua, ub, axis_world):
        img = np.zeros((zb - za, ub - ua, 3), np.uint8)
        img[:] = DD.PAPER
        for iu, u in enumerate(range(ua, ub)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                if (u, z) in occ:
                    img[iz, iu] = DP.rgb332(occ[(u, z)][1])
                    continue
                col_ = R.W[u, :, z] if axis_world == 'side' else R.W[:, u, z]
                nz = np.nonzero(col_)[0]
                if len(nz):
                    c = int(col_[nz[-1]]) if axis_world == 'side' else int(col_[nz[-1]])
                    img[iz, iu] = (np.array(DP.rgb332(c)) * 0.5 + np.array(DD.PAPER) * 0.5).astype(np.uint8)
        return Image.fromarray(img).resize(((ub - ua) * 3, (zb - za) * 3), Image.NEAREST)
    ps = place_view(occ_s, xa, xb, 'side')
    pf = place_view(occ_f, ya, yb, 'front')
    PADL = 40
    can = Image.new('RGB', (max(PADL + side.size[0] + front.size[0] + top.size[0] + 120, PADL + ps.size[0] + pf.size[0] + 80), 90 + H * sc + ps.size[1] + 200), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), R.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '一隻錨（自己的座標，每格 %d px）：左 沿 y 看（x–z 面）、中 沿 x 看（y–z 面）、右 從上面看；stock 沿 %s ⇒ %s；下：擺放（左 從右舷看、右 從船頭正前方看；現況淡色）' % (sc, R.chosen['orient'], '左圖看到 stock、中圖看到 arms' if R.chosen['orient'] == 'x' else '左圖看到 arms、中圖看到 stock'), font=f12, fill=DD.INK)
    x = PADL
    for im in (side, front, top):
        can.paste(im, (x, 66))
        x += im.size[0] + 40
    y = 66 + H * sc + 30
    can.paste(ps, (PADL, y))
    can.paste(pf, (PADL + ps.size[0] + 40, y))
    y += ps.size[1] + 16
    v = R.v
    lines = ['一隻 %d 格（%s）；x 不對稱 %d、y 不對稱 %d、元件 %d；stock 沿 %s' % (v['anchor_cells'], '、'.join('%s %d' % kv for kv in sorted(v['by_kind'].items())), v['asym_x'], v['asym_y'], v['anchor_components'], v['orient']),
             '掛在 cathead 格 %s 正下方（之前試了 %d 個掛點）；跟現況重疊 %d、兩隻彼此重疊 %d；貼著現況的格 S %d／P %d；離現況最近 %.2f 格；最低 z %d（水線 %s）；組裝件預期 %d' % (
                 v['hang_cathead_cell'], v['tries_before'], v['overlap_world'], v['overlap_each_other'], v['touch_world_S'], v['touch_world_P'], v['clear_of_hull_min'], v['lowest_z'], v['lwl_z'], v['expect_assembly_after'])]
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, can.size[0], y + 16))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    R = Rig(design)
    R.place()
    v = R.verify()
    R.write()
    v['files'] = R.files
    json.dump(v, open(os.path.join(design, 'verify_anchors.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(R, os.path.join(design, 'sheet21_anchors_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('links',)}, ensure_ascii=False))
    print(json.dumps(R.tries[:6], ensure_ascii=False))


if __name__ == '__main__':
    main()
