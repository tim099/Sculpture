# 新圖紙 11 甲板 v1（階段十，TASK-0538）：plan.json deckworks ＋ decks.json（階段九的甲板面）＋ 船殼作品的 export list
#   ⇒ masks/decks/<層>.vox.txt（各自一件子作品、在船殼座標裡雕、關聯 at 0,0,0 ⇒ 座標照抄）、verify_decks.json、sheet11_decks_v1.png
# 用法：python -I draft_decks.py <design 資料夾> <船殼 export list>
#   · 艙內 ＝ 同一列 (X, Z) 兩舷之間的空格（兩邊 y 都還有實心）；甲板板放在走的那一格底下一格（D−1）、艙內而且是空的。
#   · 舷弧的 1 格台階：高的那一欄甲板板底下多補一格（台階的立面），兩欄的板才是面接面。
#   · 橫樑：上甲板砲門中心＋中點，兩頭照平均間距往外延；sided 2；板底下 beam 格；落在艙口（±1）、桅孔（半徑＋1）裡的不放。
#   · 艙口：開口（板、樑都不放）；圍欄（coaming）在開口外一圈、甲板面往上 coaming 格。桅孔、絞盤孔：圓（照桅軸在那一層的 X）。
#   · 走道那一層：X ≤ qd_to_X 與 X ≥ fc_from_X 全寬；中間只放兩舷貼著牆的 gangway_width 格。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402

X0, X1, NDY, NZ, YC = DP.X0G, DP.X1G, DP.NDY, DP.NZ, DP.YC
Y0 = YC - NDY + 1
SX, SY = X1 - X0, 2 * NDY - 1


class Decks:
    def __init__(s, design, hull_list):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['deckworks']
        w = DP.read_list(hull_list)
        assert len(w) == s.P['hull_cells'], ('船殼格數對不上', len(w), s.P['hull_cells'])
        s.hull_sha = hashlib.sha256(open(hull_list, 'rb').read()).hexdigest()
        g = np.zeros((SX, SY, NZ), bool)
        for (x, y, z) in w:
            g[x - X0, y - Y0, z] = True
        s.H = g
        lo = np.maximum.accumulate(g, axis=1)
        hi = np.maximum.accumulate(g[:, ::-1], axis=1)[:, ::-1]
        s.between = ~g & lo & hi
        dk = json.load(open(os.path.join(design, 'decks.json'), encoding='utf-8'))
        assert dk['X0'] == X0
        s.D = {k: np.array(v) for k, v in dk['decks'].items()}
        s.iy = np.arange(SY)
        s.dy = np.abs(s.iy - (YC - Y0))
        s.cx = DP.Model(design).cx
        vp = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))
        s.port_c = [(p['X'][0] + p['X'][1]) / 2 for p in vp['ports']]
        s.port_sill = {int(round((p['X'][0] + p['X'][1]) / 2)): p['Z'][0] for p in vp['ports']}

    def walk(s, name, ix):
        d = s.P['decks'][name]
        if 'walk_Z' in d:
            return d['walk_Z']
        return int(s.D[d['level']][ix])

    def mast_X(s, m, Z):
        M = s.plan['masts']
        cpm, X0s = s.cx.cpm, s.cx.X0
        Xm = X0s + M['x'][m] * cpm
        Zref = int(s.D['upper'][int(round(Xm)) - X0])
        return Xm - (Z - Zref) * np.tan(np.radians(M['rake_deg'][m]))

    def beam_xs(s):
        c = sorted(s.port_c)
        xs = []
        for a, b in zip(c[:-1], c[1:]):
            xs += [a, (a + b) / 2]
        xs.append(c[-1])
        step = float(np.mean(np.diff(xs)))
        x = xs[0] - step
        while x > X0:
            xs.insert(0, x)
            x -= step
        x = xs[-1] + step
        while x < X1:
            xs.append(x)
            x += step
        return [int(round(v)) for v in xs], step

    def holes(s, name, Z):
        """(SX, SY) 的開口：艙口、桅孔、絞盤孔；回傳 (開口, 艙口那幾個的框)。"""
        d = s.P['decks'][name]
        hole = np.zeros((SX, SY), bool)
        frames = []
        for h in d['hatches']:
            H = s.P['hatches'][h]
            hole[H['X'][0] - X0:H['X'][1] - X0 + 1, s.dy <= H['dy']] = True
            frames.append((h, H['X'][0], H['X'][1], H['dy']))
        X = np.arange(X0, X1)[:, None] + 0.5
        Y = (s.iy[None, :] + Y0) + 0.5 - (YC + 0.5)
        s.mast_at = getattr(s, 'mast_at', {})
        for m, mm in s.P['masts'].items():
            xm = s.mast_X(m, Z) + 0.5
            disc = (X - xm) ** 2 + Y ** 2 <= mm['r'] ** 2
            hole |= disc
            s.mast_at[(name, m)] = round(float(xm), 2)
        if d['capstan']:
            C = s.P['capstan']
            hole |= (X - (C['X'] + 0.5)) ** 2 + Y ** 2 <= C['r'] ** 2
        return hole, frames

    def build(s):
        C = s.P['colors']
        bxs, s.beam_step = s.beam_xs()
        s.out = {}
        s.stats = {}
        taken = np.zeros_like(s.H)
        for name, d in s.P['decks'].items():
            cells = {}
            xr = range(d['X'][0], d['X'][1] + 1) if 'X' in d else range(X0, X1)
            region = np.zeros((SX, SY), bool)
            walkZ = np.full(SX, -1)
            for X in xr:
                ix = X - X0
                Z = s.walk(name, ix)
                row = s.between[ix, :, Z - 1]
                if not row.any():
                    continue
                if name == 'spar' and d['qd_to_X'] < X < d['fc_from_X']:
                    ys = np.where(row)[0]
                    inner = s.dy[ys].max()
                    row = row & (s.dy >= inner - d['gangway_width'] + 1)
                region[ix] = row
                walkZ[ix] = Z
            # 開口：用每一欄自己的甲板面算（桅軸是斜的）
            hole = np.zeros((SX, SY), bool)
            frames = []
            for ix in np.where(walkZ >= 0)[0]:
                h, frames = s.holes(name, int(walkZ[ix]))
                hole[ix] = h[ix]
            plank = region & ~hole
            for ix, iy in np.argwhere(plank):
                cells[(ix + X0, iy + Y0, int(walkZ[ix]) - 1)] = C['plank']
            # 舷弧台階的立面：高的那一欄板底下補一格（只補兩欄都有板的地方）
            risers = 0
            for ix in range(SX - 1):
                a, b = walkZ[ix], walkZ[ix + 1]
                if a < 0 or b < 0 or a == b:
                    continue
                hi_ix = ix if a > b else ix + 1
                lo_ix = ix + 1 if a > b else ix
                both = plank[hi_ix] & plank[lo_ix]
                for iy in np.where(both)[0]:
                    c = (hi_ix + X0, iy + Y0, int(walkZ[hi_ix]) - 2)
                    if not s.H[c[0] - X0, iy, c[2]] and c not in cells:
                        cells[c] = C['plank']
                        risers += 1
            # 橫樑
            beams = 0
            for bx in bxs:
                for X in (bx, bx + 1):
                    ix = X - X0
                    if not (0 <= ix < SX) or walkZ[ix] < 0:
                        continue
                    near_hole = hole[max(0, ix - 1):ix + 2].any(0)
                    near_hole = ndimage.binary_dilation(near_hole, iterations=1)
                    for iy in np.where(region[ix] & ~near_hole)[0]:
                        for Z in range(int(walkZ[ix]) - 1 - d['beam'], int(walkZ[ix]) - 1):
                            if s.between[ix, iy, Z] and (X, iy + Y0, Z) not in cells:
                                cells[(X, iy + Y0, Z)] = C['beam']
                                beams += 1
            # 艙口圍欄
            coam = 0
            for h, xa, xb, dyh in frames:
                for X in range(xa - 1, xb + 2):
                    ix = X - X0
                    if walkZ[ix] < 0:
                        continue
                    for iy in range(SY):
                        ring = (X in (xa - 1, xb + 1) and s.dy[iy] <= dyh + 1) or (xa <= X <= xb and s.dy[iy] == dyh + 1)
                        if not ring or not region[ix, iy]:
                            continue
                        for Z in range(int(walkZ[ix]), int(walkZ[ix]) + d['coaming']):
                            if not s.H[ix, iy, Z]:
                                cells[(X, iy + Y0, Z)] = C['coaming']
                                coam += 1
            for c in cells:
                assert not s.H[c[0] - X0, c[1] - Y0, c[2]], ('落在船殼的實心上', name, c)
                assert not taken[c[0] - X0, c[1] - Y0, c[2]], ('跟別層重疊', name, c)
                taken[c[0] - X0, c[1] - Y0, c[2]] = True
            s.out[name] = cells
            s.stats[name] = {'cells': len(cells), 'plank': int(plank.sum()), 'risers': risers, 'beams': beams, 'coaming': coam,
                             'X': [int(np.where(walkZ >= 0)[0].min() + X0), int(np.where(walkZ >= 0)[0].max() + X0)],
                             'walk_Z_midship_X340': int(walkZ[340 - X0]) if walkZ[340 - X0] >= 0 else None,
                             'holes_cells': int((region & hole).sum())}
        s.beam_x = bxs

    def fill_cavities(s):
        """船殼＋四層一起的封閉空腔 ⇒ 補進圍住它的那一層（樑的顏色）。
        v1 第一版量到：下甲板在船尾最窄那一欄（X 92）把板底下 16 格封成口袋。"""
        a = s.H.copy()
        for cells in s.out.values():
            for (x, y, z) in cells:
                a[x - X0, y - Y0, z] = True
        pad = np.pad(a, 1)
        lab, _ = ndimage.label(~pad)
        cav = ((lab != lab[0, 0, 0]) & ~pad)[1:-1, 1:-1, 1:-1]
        s.cav_filled = {}
        for p in np.argwhere(cav):
            c = (int(p[0]) + X0, int(p[1]) + Y0, int(p[2]))
            owner = None
            for name, cells in s.out.items():
                if any((c[0] + dx, c[1] + dy, c[2] + dz) in cells for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
                    owner = name
                    break
            assert owner, ('封閉空腔旁邊沒有甲板', c)
            s.out[owner][c] = s.P['colors']['beam']
            s.cav_filled[owner] = s.cav_filled.get(owner, 0) + 1
        for name, n in s.cav_filled.items():
            s.stats[name]['cavity_fill'] = n
            s.stats[name]['cells'] = len(s.out[name])

    def check(s):
        """每一層：自己 1 塊（6 連通）？跟船殼接在一起？鏡像？甲板面那一格之上 2 格有沒有被船殼擋住（走得過去）？"""
        H = s.H
        s.checks = {}
        for name, cells in s.out.items():
            a = np.zeros_like(H)
            for (x, y, z) in cells:
                a[x - X0, y - Y0, z] = True
            _, n_self = ndimage.label(a)
            _, n_all = ndimage.label(a | H)
            mir = int(sum(1 for (x, y, z) in cells if (x, 2 * YC - y, z) not in cells))
            s.checks[name] = {'components_self': int(n_self), 'components_with_hull': int(n_all), 'mirror_missing': mir}
        # 全部一起
        a = H.copy()
        for cells in s.out.values():
            for (x, y, z) in cells:
                a[x - X0, y - Y0, z] = True
        _, s.n_total = ndimage.label(a)
        pad = np.pad(a, 1)
        lab, _ = ndimage.label(~pad)
        s.cav_total = int(((lab != lab[0, 0, 0]) & ~pad).sum())
        s.ALL = a

    def write(s):
        out = os.path.join(s.design, 'masks', 'decks')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        for name, cells in s.out.items():
            p = os.path.join(out, name + '.vox.txt')
            body = ''.join('%d,%d,%d,%d\n' % (c[0], c[1], c[2], v) for c, v in sorted(cells.items()))
            open(p, 'w', encoding='utf-8', newline='\n').write('# 夜燈號 %s（%s；新圖紙 11 v1，draft_decks.py 產；船殼座標、子作品關聯 at 0,0,0；%d 格，stampvox at=0,0,0）\n'
                                                               % (s.P['decks'][name]['title'], name, len(cells)) + body)
            s.files[name] = {'cells': len(cells), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}


def render_sheet(K, path):
    """新圖紙 11：上 ＝ 四層的平面（右舷 y > 160 往上；顏色照格的顏色、艙口圍欄深）；下 ＝ 右舷內側立面（每層甲板板的高度）。"""
    sc = 2
    panels = []
    for name, cells in K.out.items():
        img = np.full((SY, SX, 3), 250, np.uint8)
        hull = K.H.any(2)
        img[hull.T] = (225, 220, 210)
        for (x, y, z), c in cells.items():
            img[y - Y0, x - X0] = DP.rgb332(c)
        im = Image.fromarray(img[::-1]).resize((SX * sc, SY * sc), Image.NEAREST)
        ImageDraw.Draw(im).text((6, 4), 'sheet 11 v1  %s (plan view, bow right, starboard up)' % name, fill=(0, 0, 0))
        panels.append(im)
    el = np.full((NZ, SX, 3), 250, np.uint8)
    el[(K.H[:, YC - Y0:, :].any(1)).T] = (225, 220, 210)
    for name, cells in K.out.items():
        for (x, y, z), c in cells.items():
            if y >= YC:
                el[z, x - X0] = DP.rgb332(c)
    eim = Image.fromarray(el[::-1]).resize((SX * sc, NZ * sc), Image.NEAREST)
    ImageDraw.Draw(eim).text((6, 4), 'starboard inboard elevation: deck planks, beams, coamings', fill=(0, 0, 0))
    W = SX * sc
    Ht = sum(p.size[1] + 8 for p in panels) + eim.size[1]
    canvas = Image.new('RGB', (W, Ht), (255, 255, 255))
    y = 0
    for p in panels:
        canvas.paste(p, (0, y))
        y += p.size[1] + 8
    canvas.paste(eim, (0, y))
    canvas.save(path)


def main():
    design, hull = sys.argv[1], sys.argv[2]
    K = Decks(design, hull)
    K.build()
    K.fill_cavities()
    K.check()
    K.write()
    v = {'title': K.P['title'], 'hull_cells': K.P['hull_cells'], 'hull_list_sha256': K.hull_sha,
         'beam_x': K.beam_x, 'beam_step': round(K.beam_step, 2), 'mast_hole_X': {'%s/%s' % k: v for k, v in K.mast_at.items()},
         'decks': K.stats, 'checks': K.checks, 'components_hull_plus_decks': int(K.n_total), 'cavities_hull_plus_decks': K.cav_total,
         'files': K.files, 'total_cells': sum(f['cells'] for f in K.files.values())}
    json.dump(v, open(os.path.join(design, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(K, os.path.join(design, 'sheet11_decks_v1.png'))
    print(json.dumps({k: v[k] for k in ('decks', 'checks', 'components_hull_plus_decks', 'cavities_hull_plus_decks', 'total_cells', 'mast_hole_X')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
