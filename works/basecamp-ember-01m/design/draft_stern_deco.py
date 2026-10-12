# 餘燼號 階段四b：船尾裝飾 —— quarter gallery（一舷＋鏡像）、stern walk、船尾名牌與火焰、船尾燈籠（0.02 m 子作品當模型）
#   輸入：plan.json stern_deco ＋ 餘燼號船殼（標記 船尾:end）
#   ⇒ masks/deco/{quarter_gallery,stern_walk,stern_deco,lantern}.vox.txt（各自子作品的座標）、deco_placement.json、verify_stern_deco.json、sheet05_stern_deco_v1.png
# 用法：python -I draft_stern_deco.py <design 資料夾>
#   · 世界座標先算、再減各自子作品的 origin（外框最小角 −1）；quarter gallery 只做右舷（y > 160），左舷 ＝ mirror=y 關聯
#   · 量：跟船殼重疊 0、每件 6 連通接到船殼、左舷鏡過去也不撞船殼
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402
from draft_ports import export_mark   # noqa: E402

W = 'basecamp-ember-01m'
YC = 160
BLACK, RED, GOLD, GLASS, IRON, WOOD, ORANGE, YELLOW = 36, 128, 248, 245, 146, 104, 240, 252


class Deco:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.D = s.plan['stern_deco']
        a = export_mark(W, s.D['world_mark'])
        assert len(a) == s.D['world_voxels'], ('船殼現況跟 plan 記的不一樣', len(a))
        s.H = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
        s.read = {'world': len(s.H)}
        s.parts = {}

    def yout(s, x, z):
        ys = [y for y in range(YC + 1, 320) if (x, y, z) in s.H]
        return max(ys) if ys else None

    def face(s, z, y=YC):
        xs = [x for x in range(80, 140) if (x, y, z) in s.H]
        return min(xs) if xs else None

    # ── quarter gallery（右舷）──
    def gallery(s):
        G = s.D['gallery']
        cx = G['x_center']
        cells = {}

        def span(z):
            if z < G['drop'][1] + 1:                      # 垂飾：往下收
                t = (z - G['drop'][0]) / (G['drop'][1] - G['drop'][0])
                hl, d = 2 + round(9 * t), 1 + round(5 * t)
                return cx - hl, cx + hl, d
            if z >= G['crown'][0]:                       # 冠：往上收
                t = (z - G['crown'][0]) / (G['crown'][1] - G['crown'][0])
                hl, d = 11 - round(7 * t), 6 - round(4 * t)
                return cx - hl, cx + hl, d
            if G['belt'][0] <= z <= G['belt'][1]:
                return G['x'][0] - 1, G['x'][1] + 1, 7
            return G['x'][0], G['x'][1], 6
        zs = range(G['drop'][0], G['crown'][1] + 1)
        face_y = {}
        for z in zs:
            xa, xb, d = span(z)
            yo = [s.yout(x, z) for x in range(xa, xb + 1)]
            yo = [y for y in yo if y is not None]
            if not yo:
                continue
            Yo = max(yo) + d
            face_y[z] = Yo
            for x in range(xa, xb + 1):
                y0 = s.yout(x, z)
                if y0 is None:
                    continue
                for y in range(y0 + 1, Yo + 1):
                    cells[(x, y, z)] = BLACK
        # 顏色
        wins = G['windows_x']
        for (x, y, z) in list(cells):
            outer = y == face_y[z]
            xa, xb, d = span(z)
            if z < G['drop'][1] + 1:
                cells[(x, y, z)] = GOLD if (z - G['drop'][0]) % 3 == 1 or z == G['drop'][0] else BLACK
                continue
            if z >= G['crown'][0]:
                top = (x, y, z + 1) not in cells and span(z + 1)[0] > x or x in (xa, xb) or z == G['crown'][0]
                cells[(x, y, z)] = GOLD if top else RED
                continue
            if G['belt'][0] <= z <= G['belt'][1]:
                cells[(x, y, z)] = GOLD
                continue
            if not outer:
                if x in (xa, xb):
                    cells[(x, y, z)] = GOLD if x == xa or x == xb else BLACK
                continue
            tier = None
            for t in G['tiers']:
                if t['z'][0] <= z <= t['z'][1]:
                    tier = t
            if tier is None:
                continue
            c = BLACK
            if z in (tier['z'][0], tier['z'][1]) or x in (xa, xb):
                c = GOLD
            if 'panel_z' in tier and tier['panel_z'][0] <= z <= tier['panel_z'][1] and xa < x < xb:
                c = RED
            wz = tier['win_z']
            for w0, w1 in wins:
                if w0 <= x <= w1 and wz[0] <= z <= wz[1]:
                    c = GLASS
                elif w0 - 1 <= x <= w1 + 1 and wz[0] - 1 <= z <= wz[1] + 1:
                    c = GOLD
            cells[(x, y, z)] = c
        # 尖頂
        ft = G['finial']
        top_z = G['crown'][1]
        yo = face_y[top_z]
        for z in range(top_z + 1, top_z + ft['h'] + 1):
            cells[(cx, yo, z)] = GOLD
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                cells[(cx + dx, yo, top_z + ft['ball'] + dz)] = GOLD
        s.parts['quarter_gallery'] = cells

    # ── stern walk ──
    def walk(s):
        Wk = s.D['walk']
        z0 = Wk['z']
        fx = s.face(z0)
        dmax = Wk['dy']
        cells = {}
        xo = fx - Wk['depth']
        for y in range(YC - dmax, YC + dmax + 1):
            for x in range(xo, fx):
                cells[(x, y, z0)] = WOOD
                cells[(x, y, z0 - 1)] = GOLD if x == xo else BLACK
            for z in range(z0 + 1, z0 + Wk['rail_h']):
                if (y - YC) % 3 == 0:
                    cells[(xo, y, z)] = GOLD
            cells[(xo, y, z0 + Wk['rail_h'])] = GOLD
        for sg in (1, -1):
            y = YC + sg * dmax
            for x in range(xo, fx):
                cells[(x, y, z0 + Wk['rail_h'])] = GOLD
                if (x - xo) % 3 == 0:
                    for z in range(z0 + 1, z0 + Wk['rail_h']):
                        cells[(x, y, z)] = GOLD
        for dy in Wk['brackets_dy']:
            y = YC + dy
            for z in range(Wk['bracket_z'][0], z0 - 1):
                frac = (z - Wk['bracket_z'][0] + 1) / (z0 - 1 - Wk['bracket_z'][0])
                for x in range(fx - 1 - round((Wk['depth'] - 1) * frac), fx):
                    if (x, y, z) not in s.H:
                        cells[(x, y, z)] = GOLD if x == fx - 1 - round((Wk['depth'] - 1) * frac) else BLACK
        s.read['walk_skipped_hull'] = sum(1 for k in cells if k in s.H)
        s.parts['stern_walk'] = {k: c for k, c in cells.items() if k not in s.H}     # 船尾角往前彎 ⇒ 平台邊緣碰到船殼的格不放
        s.read['walk_face_x'] = fx

    # ── 船尾名牌與火焰 ──
    def deco(s):
        Dd = s.D['name']
        cells = {}
        font = Dd['font']
        word = Dd['text']
        w = len(word) * 5 + (len(word) - 1) * 2
        y_left = YC - w // 2          # 從船尾看，觀者左手邊 ＝ −y ⇒ 字從 −y 往 +y 寫
        for i, ch in enumerate(word):
            rows = font[ch]
            for r, row in enumerate(rows):
                z = Dd['z_top'] - r
                for c, b in enumerate(row):
                    if b == '#':
                        y = y_left + i * 7 + c
                        fx = s.face(z, y)
                        cells[(fx - 1, y, z)] = GOLD
        fl = s.D['flame']
        cmap = {'O': ORANGE, 'G': GOLD, 'Y': YELLOW, 'R': RED}
        for sg in (1, -1):
            yc = YC + sg * fl['dy']
            for r, row in enumerate(fl['glyph']):
                z = fl['z_top'] - r
                for c, b in enumerate(row):
                    if b in cmap:
                        dc = c - len(row) // 2
                        y = yc + (dc if sg > 0 else -dc)
                        fx = s.face(z, y)
                        cells[(fx - 1, y, z)] = cmap[b]
        s.parts['stern_deco'] = cells

    # ── 燈籠（0.02 m，自己的座標：底面中心 (c, c, 0)）──
    def lantern(s):
        L = s.D['lantern']
        c = L['half']
        cells = {}

        def octo(dx, dy):
            return max(abs(dx), abs(dy), (abs(dx) + abs(dy)) / 1.4142)
        for z in range(L['height']):
            for x in range(2 * c + 1):
                for y in range(2 * c + 1):
                    dx, dy = x - c, y - c
                    r = octo(dx, dy)
                    col = None
                    if z < L['post']:
                        if dx * dx + dy * dy <= L['post_r'] ** 2:
                            col = IRON
                    elif z < L['bowl'][1]:
                        t = (z - L['bowl'][0]) / (L['bowl'][1] - L['bowl'][0])
                        if r <= 6 + (L['r'] - 6) * t:
                            col = GOLD
                    elif z < L['body'][1]:
                        if r <= L['r']:
                            band = z in L['bands']
                            rib = r > L['r'] - 2.5 and (abs(abs(dx) - abs(dy)) <= 1 or abs(dx) <= 1 or abs(dy) <= 1)
                            col = GOLD if band or rib else GLASS
                    elif z < L['dome'][1]:
                        t = (z - L['dome'][0]) / (L['dome'][1] - L['dome'][0])
                        rr = (L['r'] + 1) * math.sqrt(max(0.0, 1 - t * t))
                        if r <= rr:
                            col = GOLD if z < L['dome'][0] + 2 else RED
                    else:
                        zz = z - L['dome'][1]
                        if dx * dx + dy * dy <= (9 if abs(zz - 4) <= 1 else 2):
                            col = GOLD
                    if col is not None:
                        cells[(x, y, z)] = col
        s.lantern_cells = cells

    def place(s):
        s.place = {}
        for nm, cells in s.parts.items():
            ks = np.array(sorted(cells))
            lo = ks.min(0) - 1
            hi = ks.max(0) + 1
            s.place[nm] = {'origin': [int(v) for v in lo], 'size': [int(v) for v in hi - lo + 1], 'cells': len(cells)}
        # quarter gallery 左舷：mirror=y 的關聯 at.y ＝ 321 − at.y − 高
        q = s.place['quarter_gallery']
        q['mirror_at'] = [q['origin'][0], 321 - q['origin'][1] - q['size'][1], q['origin'][2]]
        L = s.D['lantern']
        ks = np.array(sorted(s.lantern_cells))
        s.place['lantern'] = {'size': [int(v) for v in ks.max(0) + 1], 'cells': len(s.lantern_cells), 'pivot': [L['half'] + 0.5, L['half'] + 0.5, 0],
                              'scale': L['scale'], 'at': []}
        for nm, dy in L['spots']:
            y = YC + dy
            zc = max(z for (x, yy, z) in s.H if yy == y and x < 130)
            xc = min(x for (x, yy, z) in s.H if yy == y and z == zc)
            s.place['lantern']['at'].append({'name': nm, 'at': [xc + 0.5 + L['dx'], y + 0.5, zc + 1], 'cap_cell': [xc, y, zc]})

    def verify(s):
        v = {}
        allc = {}
        mir = {(x, 320 - y, z): c for (x, y, z), c in s.parts['quarter_gallery'].items()}
        sets = dict(s.parts)
        sets['quarter_gallery_P'] = mir
        for nm, cells in sets.items():
            ov = sum(1 for k in cells if k in s.H)
            pts = set(cells) | set(s.H)
            arr = np.array(sorted(pts))
            lo = arr.min(0)
            A = np.zeros(tuple(arr.max(0) - lo + 1), bool)
            A[tuple((arr - lo).T)] = True
            lab, n = ndimage.label(A)
            hl = lab[tuple((np.array(sorted(s.H)[:1]) - lo).T)][0]
            fl = sum(1 for k in cells if lab[tuple(np.array(k) - lo)] != hl)
            cross = sum(1 for k in cells if k in allc)
            v[nm] = {'cells': len(cells), 'overlap_hull': ov, 'not_connected_to_hull': fl, 'overlap_other_parts': cross}
            allc.update(cells)
        v['lantern_cells'] = len(s.lantern_cells)
        v['lantern_symmetry_diff'] = sum(1 for (x, y, z), c in s.lantern_cells.items() if s.lantern_cells.get((2 * s.D['lantern']['half'] - x, y, z)) != c)
        R = dict(s.H)
        R.update(allc)
        v['assembly_voxels_expect'] = len(R)
        v['structure_expect'] = DP.Ember.structure(None, R)
        s.R = R
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'deco')
        os.makedirs(out, exist_ok=True)
        files = {}
        for nm, cells in list(s.parts.items()) + [('lantern', s.lantern_cells)]:
            o = s.place[nm].get('origin', [0, 0, 0])
            rows = sorted((k[0] - o[0], k[1] - o[1], k[2] - o[2], c) for k, c in cells.items())
            p = os.path.join(out, nm + '.vox.txt')
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s（子作品座標；組裝件座標 ＝ 這裡 ＋ %s）（%d 格）\n' % (nm, ','.join(map(str, o)), len(rows))
                                                               + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files[nm] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        json.dump(s.place, open(os.path.join(s.design, 'deco_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        return files

    def sheet(s, path):
        R = s.R
        sc = 4
        ys, zs = (100, 221), (88, 170)
        aft = {}
        for (x, y, z), c in R.items():
            if x < 140:
                k = (y, z)
                if k not in aft or x < aft[k][0]:
                    aft[k] = (x, c)
        Wd, Hd = (ys[1] - ys[0]) * sc, (zs[1] - zs[0]) * sc
        side = {}
        for (x, y, z), c in R.items():
            if x < 220 and y >= YC:
                k = (x, z)
                if k not in side or y > side[k][0]:
                    side[k] = (y, c)
        sx = (90, 220)
        Ws = (sx[1] - sx[0]) * sc
        im = Image.new('RGB', (Wd + Ws + 80, Hd + 110), (250, 249, 244))
        px = im.load()
        for (y, z), (x, c) in aft.items():
            if ys[0] <= y < ys[1] and zs[0] <= z < zs[1]:
                X0, Y0 = 20 + (y - ys[0]) * sc, 80 + (zs[1] - 1 - z) * sc
                for i in range(sc):
                    for j in range(sc):
                        px[X0 + i, Y0 + j] = DP.rgb(c)
        for (x, z), (y, c) in side.items():
            if sx[0] <= x < sx[1] and zs[0] <= z < zs[1]:
                X0, Y0 = 60 + Wd + (x - sx[0]) * sc, 80 + (zs[1] - 1 - z) * sc
                for i in range(sc):
                    for j in range(sc):
                        px[X0 + i, Y0 + j] = DP.rgb(c)
        d = ImageDraw.Draw(im)
        d.text((20, 12), '餘燼號 新圖紙 05 v1：船尾裝飾（左：從正後方看，觀者左手邊 = -y；右：右舷側面船尾段）—— 燈籠是模型、這張沒畫', font=DP.font(18), fill=(30, 30, 30))
        d.text((20, 44), 'quarter gallery %d 格（一舷）、stern walk %d、名牌＋火焰 %d、燈籠 %d（0.02 m）' % (
            len(s.parts['quarter_gallery']), len(s.parts['stern_walk']), len(s.parts['stern_deco']), len(s.lantern_cells)), font=DP.font(14), fill=(80, 80, 80))
        im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    D = Deco(design)
    D.gallery()
    D.walk()
    D.deco()
    D.lantern()
    D.place()
    v = {'read': D.read, 'parts': D.verify()}
    v['files'] = D.write()
    v['placement'] = D.place
    D.sheet(os.path.join(design, 'sheet05_stern_deco_v1.png'))
    json.dump(v, open(os.path.join(design, 'verify_stern_deco.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in ('read', 'parts', 'placement')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
