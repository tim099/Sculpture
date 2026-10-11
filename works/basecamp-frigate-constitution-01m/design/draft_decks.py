# 新圖紙 08（甲板子作品）：plan.json 的 deckworks 段（高度照 interior.decks）＋ 作品（deckworks.world_mark ＝ 階段九做完）
#   ⇒ masks/decks/<層>.vox.txt（四件子作品各一份，stampvox at=0,0,0）、verify_decks.json、sheet08_decks_v1.png
# 用法：python -I draft_decks.py <design 資料夾>
#   · 只放在艙內空氣裡（跟船中 (440,160,60) 6 連通的空格）—— 船殼一格都不動；四層一起算、彼此不重疊
#   · 每層甲板是一件完整的子作品，兩舷一起產生（Tim：鏡像只用在甲板上面的物件）
#   · 甲板面 D(x) 照 interior.decks 的分段：甲板板在 D−1、橫樑在板下 moulded 格（橫樑底 ＝ clamp 頂 ＋ 1）
#   · 量牆（肘、waterway、hooks）時把階段九的斜肋／hooks 當成空氣 ⇒ 肘貼的是內板，不是斜肋；碰到斜肋的另外數
import sys, os, json, glob, hashlib, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import draft_planking as DP        # noqa: E402
from replay import replay          # noqa: E402
from draft_interior import seg_z   # noqa: E402

X0, X1, NDY, NZ = DP.X0, DP.X1, DP.NDY, DP.NZ
YC = DP.YC
Y0 = YC - NDY + 1
SX, SY = X1 - X0, 2 * NDY - 1
SEED = (440, 160, 60)
DECKS = ('orlop', 'berth', 'gun', 'spar')
BELOW = {'spar': 'gun', 'gun': 'berth', 'berth': 'orlop', 'orlop': None}
CODES = ['plank', 'beam', 'carling', 'partner', 'hook', 'lodging', 'knee', 'waterway', 'coaming', 'sill', 'coat', 'pillar']
CODE = {k: i + 1 for i, k in enumerate(CODES)}
UNDER = ('beam', 'carling', 'partner', 'hook', 'lodging', 'knee')        # 板下的骨架（平面圖畫成半透明）
ABOVE = ('waterway', 'coaming', 'sill', 'coat')                          # 甲板面上的


def color_key(m):
    return {'lodging': 'knee', 'coat': 'partner'}.get(m, m)


class Decks:
    def __init__(s, design):
        s.design = design
        s.W = os.path.dirname(os.path.abspath(design))
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['deckworks']
        s.I = s.plan['interior']
        s.world = {k: v[0] for k, v in replay(s.W, mark=s.P['world_mark']).items()}
        assert len(s.world) == s.P['world_voxels'], ('讀到的作品格數對不上 world_voxels', len(s.world), s.P['world_voxels'])
        G = np.zeros((SX, SY, NZ), np.uint8)
        for (x, y, z), c in s.world.items():
            G[x - X0, y - Y0, z] = c
        s.G = G
        M = DP.Model(design)
        M.lines()
        M.hull()
        S = DP.full(M.S)
        lab, _ = ndimage.label((G == 0) & S)
        k = lab[SEED[0] - X0, SEED[1] - Y0, SEED[2]]
        assert k > 0, '種子不是空氣'
        s.A = lab == k                                            # 艙內空氣
        R = np.zeros(G.shape, bool)
        for f in ('riders', 'riders_t', 'hooks'):
            a = np.loadtxt(os.path.join(design, 'masks', 'interior', f + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
            R[a[:, 0] - X0, a[:, 1] - Y0, a[:, 2]] = True
        s.R = R & (G > 0)
        s.Awall = s.A | s.R                                       # 量牆用：斜肋當成空氣
        vp = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))
        s.ports = []
        for p in vp['ports']:
            zs = sorted(int(z) for z in p['x_rows'])
            xr = [p['x_rows'][str(z)] for z in zs]
            s.ports.append({'n': p['n'], 'xa': min(a for a, b in xr), 'xb': max(b for a, b in xr), 'sill': zs[0], 'lintel': zs[-1]})
        iy = np.arange(SY)
        s.dy = np.abs(iy - (YC - Y0))
        s.L = {d: np.zeros((SX, SY, NZ), np.uint8) for d in DECKS}
        s.OCC = np.zeros((SX, SY, NZ), bool)                      # 四層合起來佔掉的格
        s.log = {d: {'beams': [], 'knees': {'placed': 0, 'skip_port': 0, 'skip_rider': 0, 'skip_wall': 0}, 'pillars': [], 'pillars_skipped': []} for d in DECKS}
        s._wall = {}
        s._edt = {}

    # ───────── 基本量 ─────────
    def D(s, deck, x):
        return seg_z(s.I['decks'][deck]['segments'], x)

    def dims(s, deck):
        d = s.I['decks'][deck]
        return d['plank'], d['beam']

    def wall(s, x, z, sgn):
        """(x,z) 那一列、sgn 舷：從中線往外連續的 Awall 最外一格的 y 索引（中線不是空氣 ⇒ None）。"""
        key = (x, z, sgn)
        if key in s._wall:
            return s._wall[key]
        ix, c = x - X0, YC - Y0
        out = None
        if 0 <= ix < SX and s.Awall[ix, c, z]:
            row = s.Awall[ix, :, z]
            j = c
            while 0 <= j + sgn < SY and row[j + sgn]:
                j += sgn
            out = j
        s._wall[key] = out
        return out

    def edt(s, x):
        """切片 x（y,z）上每一格到最近的非 Awall 格的距離（貼牆那一格 ＝ 1）。"""
        if x not in s._edt:
            s._edt[x] = ndimage.distance_transform_edt(s.Awall[x - X0])
        return s._edt[x]

    def ends(s, z):
        """z 那一層有艙內空氣的 x 範圍（最船尾、最船頭）。"""
        xs = np.where(s.A[:, :, z].any(1))[0]
        return int(xs.min()) + X0, int(xs.max()) + X0

    def hatches(s, deck):
        return [h for h in s.P['hatches']['list'] if deck in h['decks']]

    def opening(s, deck, x, y):
        dy = abs(y - YC)
        return any(h['x'][0] <= x <= h['x'][1] and dy <= h['hw'] for h in s.hatches(deck))

    def mast_c(s, m, z):
        mm = s.P['masts'][m]
        return mm['x_gun'] - (z - s.P['masts']['z_ref']) * math.tan(math.radians(mm['rake_deg'])), mm['r']

    def masts_at(s, deck):
        out = []
        for m in ('mizzen', 'main', 'fore'):
            x = s.P['masts'][m]['x_gun']
            if s.D(deck, x) is not None:
                out.append(m)
        return out

    def hole2d(s, deck, z):
        """z 那一層的桅孔（SX × SY bool）。"""
        H = np.zeros((SX, SY), bool)
        xs = np.arange(X0, X1)[:, None]
        dy = s.dy[None, :]
        for m in s.masts_at(deck):
            cx, r = s.mast_c(m, z)
            H |= (xs - cx) ** 2 + dy ** 2 <= (r + 0.25) ** 2
        return H

    def put(s, deck, mask, member, only_free=True):
        """mask（全網格 bool）裡、艙內空氣且還沒被佔的格 ⇒ member。回傳放了幾格。"""
        m = mask & s.A & ~s.OCC
        s.L[deck][m] = CODE[member]
        s.OCC |= m
        return int(m.sum())

    # ───────── 橫樑格點 ─────────
    def grid(s):
        xc = sorted((p['xa'] + p['xb']) / 2 for p in s.ports)
        g = list(xc) + [(a + b) / 2 for a, b in zip(xc, xc[1:])]
        pe = s.P['beams']['pitch_ends']
        lo, hi = 95, 685
        c = xc[0] - pe
        while c > lo:
            g.append(c)
            c -= pe
        c = xc[-1] + pe
        while c < hi:
            g.append(c)
            c += pe
        return sorted(g)

    def beam_list(s, deck):
        """回傳 [(x0, x1 不含, kind)]；kind ＝ grid／seam／end。"""
        sided = s.P['beams']['sided'][deck]
        segs = s.I['decks'][deck]['segments']
        pl, bm = s.dims(deck)
        fixed = []
        if deck == 'orlop':
            for a, b, z in segs:
                fixed.append((a, a + sided, 'end'))
                fixed.append((b - sided, b, 'end'))
        else:
            for (a1, b1, z1), (a2, b2, z2) in zip(segs, segs[1:]):
                sx = b1
                fixed.append((sx, sx + sided, 'seam') if z2 > z1 else (sx - sided, sx, 'seam'))
        out = list(fixed)
        zt = (s.D(deck, 440) or 42) - pl - 1
        xs_aft, xs_fore = s.ends(zt)
        s.log[deck]['ends_at_beam'] = [xs_aft, xs_fore]
        arm = s.P['hooks']['bow_arm']
        for c in s.grid():
            x0 = int(math.floor(c - sided / 2 + 0.5))
            x1 = x0 + sided
            if s.D(deck, x0) is None or s.D(deck, x1 - 1) is None:
                continue
            if any(x0 < f1 + 6 and f0 - 6 < x1 for f0, f1, _ in fixed):
                continue
            if deck != 'orlop':
                if x0 < xs_aft + sided + 6 or x1 > xs_fore - arm:
                    continue
            out.append((x0, x1, 'grid'))
        return sorted(out)

    # ───────── 每一層 ─────────
    def build(s, deck):
        P, I = s.P, s.I
        pl, bm = s.dims(deck)
        Lg = s.log[deck]
        xs = np.arange(X0, X1)
        Dx = np.array([s.D(deck, x) if s.D(deck, x) is not None else -1 for x in xs])
        has = Dx > 0
        Z = np.arange(NZ)[None, None, :]
        Dg = Dx[:, None, None]
        ally = np.ones((1, SY, 1), bool)
        # 開口（艙口）—— 只在甲板板那一層與橫樑切口用
        OPEN = np.zeros((SX, SY), bool)
        for h in s.hatches(deck):
            OPEN[h['x'][0] - X0:h['x'][1] - X0 + 1, s.dy <= h['hw']] = True
        HOLE = {z: s.hole2d(deck, z) for z in range(max(1, int(Dx[has].min()) - 8), int(Dx[has].max()) + 3)}

        def holes3(zmask):
            H = np.zeros((SX, SY, NZ), bool)
            for z, h in HOLE.items():
                H[:, :, z] = h
            return H & zmask
        # ① 甲板板
        plank = has[:, None, None] & (Z == Dg - 1) & ~OPEN[:, :, None]
        plank &= ~holes3(plank)
        n_plank = s.put(deck, plank, 'plank')
        # ② 橫樑（艙口裡的切掉，keep_beams 的照樣跨過；桅孔四周 partners 方框以內切掉）
        beams = s.beam_list(deck)
        BZ = has[:, None, None] & (Z >= Dg - pl - bm) & (Z <= Dg - pl - 1)
        cut = np.zeros((SX, SY), bool)
        for h in s.hatches(deck):
            if not h.get('keep_beams'):
                cut[h['x'][0] - X0:h['x'][1] - X0 + 1, s.dy <= h['hw']] = True
        PART = np.zeros((SX, SY, NZ), bool)
        PIN = np.zeros((SX, SY, NZ), bool)
        for m in s.masts_at(deck):
            for z in range(NZ):
                if not BZ[:, :, z].any():
                    continue
                cx, r = s.mast_c(m, z)
                cheb = np.maximum(np.abs(xs[:, None] - cx), s.dy[None, :])
                PART[:, :, z] |= (cheb > r + 0.5) & (cheb <= r + 2.5)
                PIN[:, :, z] |= cheb <= r + 2.5
        PART &= BZ
        PIN &= BZ
        BM = np.zeros((SX, SY, NZ), bool)
        for x0, x1, kind in beams:
            BM[x0 - X0:x1 - X0] = True
            Lg['beams'].append([x0, x1, kind])
        BM &= BZ & ~cut[:, :, None] & ~PIN
        BM &= ~holes3(BM)
        n_beam = s.put(deck, BM, 'beam')
        n_part = s.put(deck, PART & ~holes3(PART), 'partner')
        # ③ carlings：|dy| 20–21 沿船長（艙口兩邊另外一排 hw+1..hw+2），板下 2 格
        cd = P['carlings']
        CZ = has[:, None, None] & (Z >= Dg - pl - cd['depth']) & (Z <= Dg - pl - 1)
        CL = np.zeros((SX, SY), bool)
        zmid = Dx - pl - 1
        for ix in np.where(has)[0]:
            w = s.wall(ix + X0, int(zmid[ix]), 1)
            if w is not None and w - (YC - Y0) >= cd['dy'][1] + 5:
                CL[ix, (s.dy >= cd['dy'][0]) & (s.dy <= cd['dy'][1])] = True
        for h in s.hatches(deck):
            if h['hw'] + 2 < cd['dy'][0]:
                CL[h['x'][0] - X0:h['x'][1] - X0 + 1, (s.dy >= h['hw'] + 1) & (s.dy <= h['hw'] + 2)] = True
        CA = CZ & CL[:, :, None] & ~OPEN[:, :, None]
        n_carl = s.put(deck, CA & ~holes3(CA), 'carling')
        # ④ deck hooks（船頭）、transom 橫樑與 knees（船尾）
        hk = P['hooks']
        HK = np.zeros((SX, SY, NZ), bool)
        LK = np.zeros((SX, SY, NZ), bool)
        if deck == 'orlop':
            fore_end = s.I['decks']['orlop']['segments'][-1][1] - 1
        for z in range(NZ):
            if not BZ[:, :, z].any():
                continue
            xa, xf = s.ends(z)
            if deck == 'orlop':
                xf = fore_end
            for x in range(xf - hk['bow_arm'], xf + 1):
                ix = x - X0
                if not BZ[ix, :, z].any():
                    continue
                if x >= xf - hk['bow_tip']:
                    HK[ix, :, z] = True
                    continue
                for sgn in (1, -1):
                    w = s.wall(x, z, sgn)
                    if w is None:
                        continue
                    for t in range(hk['thick']):
                        j = w - sgn * t
                        if 0 <= j < SY:
                            HK[ix, j, z] = True
            if deck != 'orlop':
                sided = P['beams']['sided'][deck]
                BMs = np.zeros((SX, SY), bool)
                BMs[xa - X0:xa - X0 + sided] = True
                BM2 = BMs[:, :, None] & (Z == z) & BZ
                s.put(deck, BM2, 'beam')
                for x in range(xa + sided, xa + sided + hk['stern_arm']):
                    for sgn in (1, -1):
                        w = s.wall(x, z, sgn)
                        if w is None:
                            continue
                        for t in range(hk['thick']):
                            j = w - sgn * t
                            if 0 <= j < SY:
                                LK[x - X0, j, z] = True
        n_hook = s.put(deck, HK & BZ, 'hook')
        n_tk = s.put(deck, LK & BZ, 'hook')
        # ⑤ lodging knees：橫樑那一層、每根橫樑前面貼著船殼
        lk = P['knees']['lodging']
        LG = np.zeros((SX, SY, NZ), bool)
        for x0, x1, kind in beams:
            for dxx in range(lk['along']):
                x = x1 + dxx
                ix = x - X0
                if not (0 <= ix < SX) or not has[ix]:
                    continue
                for z in np.where(BZ[ix].any(0))[0]:
                    for sgn in (1, -1):
                        w = s.wall(x, int(z), sgn)
                        if w is None:
                            continue
                        for t in range(lk['thick'] + lk['throat']):
                            if t < lk['thick'] or t + dxx < lk['thick'] + lk['throat']:
                                j = w - sgn * t
                                if 0 <= j < SY:
                                    LG[ix, j, z] = True
        n_lodg = s.put(deck, LG & BZ, 'lodging')
        # ⑥ hanging knees：橫樑兩端底下，貼著船殼往下
        n_knee = 0
        hkn = P['knees']['hanging']
        if deck in hkn['decks']:
            sided = P['beams']['sided'][deck]
            for x0, x1, kind in beams:
                if kind == 'end':
                    continue
                kx = list(range(x0 + (sided - 2) // 2, x0 + (sided - 2) // 2 + 2))
                zb = int(Dx[x0 - X0]) - pl - bm                     # 橫樑最底那一格
                zr = list(range(zb - hkn['down'], zb))
                if any(p['xa'] - 2 <= kx[-1] and kx[0] <= p['xb'] + 2 and p['sill'] - 1 <= zr[-1] and zr[0] <= p['lintel'] + 1 for p in s.ports):
                    Lg['knees']['skip_port'] += 2
                    continue
                for sgn in (1, -1):
                    cells = []
                    ok = True
                    for x in kx:
                        ws = [s.wall(x, z, sgn) for z in zr]
                        # 牆要接近直立（船兩頭 V 形的底艙不放：直臂會斷成台階）
                        if any(w is None for w in ws) or max(ws) - min(ws) > hkn.get('max_slope', 4):
                            ok = False
                            break
                        # 到牆的距離用切片上的真實距離（EDT，斜肋當成空氣）⇒ 臂厚照牆的法向量、不會斷開
                        dist = s.edt(x)
                        for z, w in zip(zr, ws):
                            dd = zb - 1 - z
                            for di in range(hkn['along']):
                                j = w - sgn * di
                                if not (0 <= j < SY):
                                    continue
                                t = dist[j, z] - 1.0
                                if t < hkn['thick'] or dd < hkn['thick'] or t + dd < hkn['thick'] + hkn['throat']:
                                    cells.append((x - X0, j, z))
                    if not ok or not cells:
                        Lg['knees']['skip_wall'] += 1
                        continue
                    c = np.array(cells)
                    free = s.A[c[:, 0], c[:, 1], c[:, 2]] & ~s.OCC[c[:, 0], c[:, 1], c[:, 2]]
                    if free.mean() < 0.9:
                        Lg['knees']['skip_rider'] += 1
                        continue
                    c = c[free]
                    s.L[deck][c[:, 0], c[:, 1], c[:, 2]] = CODE['knee']
                    s.OCC[c[:, 0], c[:, 1], c[:, 2]] = True
                    n_knee += len(c)
                    Lg['knees']['placed'] += 1
        # ⑦ 甲板面上：艙口圍板、seam 504 的橫檻、桅座、waterway
        ch = P['hatches']['coaming']
        CO = np.zeros((SX, SY, NZ), bool)
        for h in s.hatches(deck):
            ring = np.zeros((SX, SY), bool)
            ring[h['x'][0] - X0 - ch['thick']:h['x'][1] - X0 + 1 + ch['thick'], s.dy <= h['hw'] + ch['thick']] = True
            ring &= ~OPEN
            CO |= ring[:, :, None] & (Z >= Dg) & (Z < Dg + ch['height'][deck]) & has[:, None, None]
        n_coam = s.put(deck, CO, 'coaming')
        n_sill = 0
        if deck in P['sill_504']['decks']:
            a, b = P['sill_504']['x']
            zt = max(s.D(deck, a - 1), s.D(deck, a))
            SI = np.zeros((SX, SY, NZ), bool)
            SI[a - X0:b - X0 + 1, :, :] = True
            SI &= (Z >= Dg) & (Z <= zt)
            n_sill = s.put(deck, SI, 'sill')
        COAT = np.zeros((SX, SY, NZ), bool)
        for m in s.masts_at(deck):
            for x in range(X0, X1):
                if not has[x - X0]:
                    continue
                z = int(Dx[x - X0])
                cx, r = s.mast_c(m, z)
                d2 = (x - cx) ** 2 + s.dy ** 2
                COAT[x - X0, (d2 > (r + 0.25) ** 2) & (d2 <= (r + 1.25) ** 2), z] = True
        n_coat = s.put(deck, COAT, 'coat')
        ww = P['waterway']
        WW = np.zeros((SX, SY, NZ), bool)
        for ix in np.where(has)[0]:
            x = ix + X0
            for hgt in range(ww['height']):
                z = int(Dx[ix]) + hgt
                for sgn in (1, -1):
                    w = s.wall(x, z, sgn)
                    if w is None:
                        continue
                    for t in range(ww['width']):
                        j = w - sgn * t
                        if 0 <= j < SY:
                            WW[ix, j, z] = True
        n_ww = s.put(deck, WW, 'waterway')
        Lg['cells'] = {'plank': n_plank, 'beam': n_beam, 'partner': n_part, 'carling': n_carl, 'hook': n_hook + n_tk, 'lodging': n_lodg,
                       'knee': n_knee, 'coaming': n_coam, 'sill': n_sill, 'coat': n_coat, 'waterway': n_ww}

    # ───────── 柱子（屬於它撐住的那一層）─────────
    def pillar_cells(s, deck, x0, cdy, turned):
        """橫樑 x0 底下、離中線 cdy 的一根柱子 ⇒ (cells, None) 或 (None, 原因)。"""
        pl, bm = s.dims(deck)
        low = BELOW[deck]
        sided = s.P['beams']['sided'][deck]
        Dt = s.D(deck, x0)
        ztop = Dt - pl - bm - 1
        px = x0 + (sided - 3) // 2
        yc = YC - Y0 + cdy
        if not (1 <= yc < SY - 1):
            return None, 'out'
        foot = [(px + a - X0, yc + b) for a in range(3) for b in (-1, 0, 1)]
        # 底：下一層的甲板板；沒有下一層（或 orlop 平台以外）⇒ 底艙中線最高的實心格（只放中線）
        if low is not None and all(s.D(low, px + a) is not None for a in range(3)):
            Dl = s.D(low, px)
            if not all(s.L[low][i, j, Dl - 1] == CODE['plank'] for i, j in foot):
                return None, 'opening_below'
            zb = Dl
        else:
            if cdy != 0:
                return None, 'hold_offcentre'
            zz = np.where(s.G[px - X0 + 1, YC - Y0, :ztop] > 0)[0]
            if not len(zz):
                return None, 'no_base'
            zb = int(zz.max()) + 1
            if not all(s.G[i, j, zb - 1] > 0 for i, j in foot):
                return None, 'base_not_solid'
        if ztop - zb < 4:
            return None, 'too_short'
        # 頂：橫樑底下那一格要是這一層的橫樑（被艙口／桅孔切掉的地方不放）
        if not all(s.L[deck][i, j, ztop + 1] in (CODE['beam'], CODE['partner']) for i, j in foot):
            return None, 'no_beam_above'
        cells = []
        h = ztop - zb + 1
        rings = {zb, zb + 1, ztop, ztop - 1, zb + h // 3}
        for z in range(zb, ztop + 1):
            for i, j in foot:
                corner = (i - (px - X0)) != 1 and (j - yc) != 0
                if turned and corner and z not in rings:
                    continue
                cells.append((i, j, z))
        c = np.array(cells)
        if not (s.A[c[:, 0], c[:, 1], c[:, 2]] & ~s.OCC[c[:, 0], c[:, 1], c[:, 2]]).all():
            return None, 'blocked'
        return (c, (px, zb, ztop)), None

    def pillars(s):
        kmax = s.P['pillars'].get('pair_max_dy', 26)
        for deck in DECKS:
            turned = deck in ('gun', 'spar')                         # 站在 berth／gun deck 上的那幾根是車削的
            n = 0
            for x0, x1, kind in s.log[deck]['beams']:
                if s.D(deck, x0) is None:
                    continue
                # 中線一根；放不下（底下是艙口／桅孔／圍板，或橫樑在中線被切掉）⇒ 往外找第一個兩舷都放得下的位置，放一對
                got, why = s.pillar_cells(deck, x0, 0, turned)
                picks = [(0, got)] if got else []
                if not got:
                    for k in range(3, kmax + 1):
                        a, _ = s.pillar_cells(deck, x0, k, turned)
                        b, _ = s.pillar_cells(deck, x0, -k, turned)
                        if a and b and not set(map(tuple, a[0])) & set(map(tuple, b[0])):
                            picks = [(k, a), (-k, b)]
                            break
                if not picks:
                    s.log[deck]['pillars_skipped'].append([x0, why])
                    continue
                for cdy, (c, (px, zb, ztop)) in picks:
                    s.L[deck][c[:, 0], c[:, 1], c[:, 2]] = CODE['pillar']
                    s.OCC[c[:, 0], c[:, 1], c[:, 2]] = True
                    s.log[deck]['pillars'].append([px, cdy, zb, ztop, 'turned' if turned else 'square'])
                    n += len(c)
            s.log[deck]['cells']['pillar'] = n

    # ───────── 收尾：碎塊、封閉空腔 ─────────
    def tidy(s):
        """① 每一層自己的元件裡，小於 16 格、只有 waterway／肘的碎塊拿掉（落在斜肋、wing transom、船頭尖端上的）；
        ② 船殼＋四層合起來的封閉空腔 ⇒ 補進蓋住它的那一層、用鄰居構件（Tim：用鄰近 voxel 顏色填滿）。"""
        decor = {CODE[k] for k in ('waterway', 'knee', 'lodging', 'hook')}
        for d in DECKS:
            lab, n = ndimage.label(s.L[d] > 0)
            sz = np.bincount(lab.ravel())
            drop = 0
            for k in range(1, n + 1):
                if sz[k] < 16:
                    m = lab == k
                    if set(np.unique(s.L[d][m]).tolist()) <= decor:
                        s.L[d][m] = 0
                        s.OCC[m] = False
                        drop += int(sz[k])
            s.log[d]['dropped_fragments'] = drop
        SOL = (s.G > 0) | s.OCC
        lab, n = ndimage.label(~SOL)
        edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
        filled = {d: 0 for d in DECKS}
        for k in range(1, n + 1):
            if k in edge:
                continue
            idx = np.argwhere(lab == k)
            if len(idx) > 64:
                raise SystemExit('封閉空腔太大（%d 格 @ %s）—— 先看是哪裡封住的' % (len(idx), idx[0]))
            for i, j, z in idx:
                votes = {}
                for di, dj, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    for d in DECKS:
                        c = s.L[d][i + di, j + dj, z + dz]
                        if c:
                            votes[(d, c)] = votes.get((d, c), 0) + 1
                if not votes:
                    continue
                (d, c), _ = max(votes.items(), key=lambda kv: (kv[1], -DECKS.index(kv[0][0])))
                s.L[d][i, j, z] = c
                s.OCC[i, j, z] = True
                filled[d] += 1
            # 第二輪：只鄰著船殼、沒鄰著甲板的那幾格（多格的空腔）—— 跟著同一個空腔裡已經補的那一層
            for i, j, z in idx:
                if s.OCC[i, j, z]:
                    continue
                for d in DECKS:
                    near = [s.L[d][a, b, cc] for a, b, cc in idx if s.L[d][a, b, cc]]
                    if near:
                        s.L[d][i, j, z] = near[0]
                        s.OCC[i, j, z] = True
                        filled[d] += 1
                        break
        s.cavity_filled = filled

    # ───────── 驗收（從產物量）─────────
    def verify(s):
        v = {}
        tot = 0
        for d in DECKS:
            Ld = s.L[d]
            m = Ld > 0
            tot += int(m.sum())
            mir = int((Ld != Ld[:, ::-1, :]).sum())
            v[d] = {'cells': int(m.sum()), 'by_member': {k: int((Ld == CODE[k]).sum()) for k in CODES}, 'mirror_mismatch': mir,
                    'outside_inner_air': int((m & ~s.A).sum()),
                    'plank_components': int(ndimage.label(Ld == CODE['plank'])[1]),
                    'components': int(ndimage.label(m)[1])}
        both = sum((s.L[d] > 0).astype(np.uint8) for d in DECKS)
        v['overlap_between_decks'] = int((both > 1).sum())
        v['total_new'] = tot
        SOL = (s.G > 0) | (both > 0)
        v['composed_voxels'] = int(SOL.sum())
        v['composed_components'] = int(ndimage.label(SOL)[1])
        lab, n = ndimage.label(~SOL)
        sizes = np.bincount(lab.ravel())
        border = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
        cav = [i for i in range(1, n + 1) if i not in border]
        v['cavities_composed'] = {'n': len(cav), 'cells': int(sum(sizes[i] for i in cav))}
        s.cav_mask = np.isin(lab, cav) if cav else np.zeros(SOL.shape, bool)
        # 甲板面離上一層橫樑底的淨高（中線）
        clr = {}
        for d, up in (('orlop', 'berth'), ('berth', 'gun'), ('gun', 'spar')):
            vals = []
            for x in range(110, 670, 10):
                a, b = s.D(d, x), s.D(up, x)
                if a and b:
                    vals.append(b - s.dims(up)[0] - s.dims(up)[1] - a)
            clr[d + '→' + up] = [min(vals), max(vals)] if vals else None
        v['headroom_to_beams_above'] = clr
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'decks')
        os.makedirs(out, exist_ok=True)
        for f in glob.glob(os.path.join(out, '*')):
            os.remove(f)
        cols = s.P['colors']
        s.files = {}
        for d in DECKS:
            idx = np.argwhere(s.L[d] > 0)
            codes = s.L[d][s.L[d] > 0]
            p = os.path.join(out, d + '.vox.txt')
            body = '\n'.join('%d,%d,%d,%d' % (i + X0, j + Y0, k, cols[color_key(CODES[c - 1])]) for (i, j, k), c in zip(idx, codes))
            sw = s.P['subworks'][d]
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（子作品 %s；%d 格，at=0,0,0）\n' % (d, sw['title'], sw['id'], len(idx)) + body + '\n')
            s.files[d] = {'cells': len(idx), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}


# ───────── 圖紙 08 ─────────
def _font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


PAPER = (250, 249, 244)
HULLC = (214, 208, 196)
INK = (40, 40, 40)
DECKC = {'orlop': (70, 140, 70), 'berth': (60, 90, 190), 'gun': (190, 60, 50), 'spar': (120, 60, 160)}


def pal(c):
    return tuple(int(v) for v in DP.rgb332(c))


def render_sheet(K, path):
    cols = K.P['colors']
    mc = {m: pal(cols[color_key(m)]) for m in CODES}
    f12, f14, f18 = _font(13), _font(15), _font(20)
    xa, xb = 95, 682
    # ── 上：中線縱剖面（右舷看過去）
    sc = 2.5
    za, zb = 0, 132
    W = int((xb - xa) * sc)
    Hs = int((zb - za) * sc)
    ys = YC - Y0
    img = np.zeros((zb - za, xb - xa, 3), np.uint8)
    img[:] = (226, 231, 238)                          # 淡藍灰底：奶油色的甲板板才看得出來
    hullsec = K.G[xa - X0:xb - X0, ys, za:zb] > 0
    img[np.transpose(hullsec)[::-1]] = HULLC
    for d in DECKS:
        Ld = np.transpose(K.L[d][xa - X0:xb - X0, ys, za:zb])[::-1]
        for k in CODES:
            img[Ld == CODE[k]] = mc[k]
    sec = Image.fromarray(img).resize((W, Hs), Image.NEAREST)
    # ── 中：四層平面圖（從上往下看）
    pv = 2
    Hp = SY * pv
    plans = []
    for d in reversed(DECKS):
        Ld = K.L[d][xa - X0:xb - X0]
        rgb = np.zeros((xb - xa, SY, 3), np.float32)
        rgb[:] = PAPER
        # 船殼在甲板板那一層的斷面
        for ix in range(xb - xa):
            Dz = K.D(d, ix + xa)
            zz = (Dz - 1) if Dz else 41
            rgb[ix][K.G[ix + xa - X0, :, zz] > 0] = HULLC
        top = np.zeros((xb - xa, SY), np.uint8)
        for z in range(NZ - 1, -1, -1):                   # 這一層從上往下第一個看到的構件
            c = Ld[:, :, z]
            top = np.where((top == 0) & (c > 0), c, top)
        under = np.zeros((xb - xa, SY), np.uint8)
        for k in UNDER:
            under |= ((Ld == CODE[k]).any(2) * CODE[k]).astype(np.uint8) * (under == 0)
        for k in CODES:
            rgb[top == CODE[k]] = mc[k]
        # 板下的骨架：疊一層半透明
        for k in UNDER:
            m = (under == CODE[k]) & (top == CODE['plank'])
            rgb[m] = rgb[m] * 0.55 + np.array(mc[k]) * 0.45
        # 開口：甲板板那一層是艙內空氣、卻沒有任何構件 ⇒ 看下去是深灰
        inside = np.zeros((xb - xa, SY), bool)
        for ix in range(xb - xa):
            Dz = K.D(d, ix + xa)
            if Dz:
                inside[ix] = K.A[ix + xa - X0, :, Dz - 1]
        rgb[(top == 0) & inside] = (90, 92, 98)
        # 站在這一層上的柱子（上一層的）：黑點
        for up in DECKS:
            if BELOW[up] == d:
                for px, cdy, zb_, zt_, kind in K.log[up]['pillars']:
                    rgb[px - xa:px - xa + 3, YC - Y0 + cdy - 1:YC - Y0 + cdy + 2] = (20, 20, 20)
        im = Image.fromarray(np.transpose(rgb.clip(0, 255).astype(np.uint8), (1, 0, 2))[::-1]).resize((int((xb - xa) * pv), Hp), Image.NEAREST)
        plans.append((d, im))
    # ── 下：兩個剖面（x=437 兩個砲門之間；x=421 砲門那一根），從船尾往船頭看
    secs = []
    for xsec, cap in ((437, 'x = 437（兩個砲門之間的那一根：spar deck 有 hanging knee）'), (421, 'x = 421（第 8 個砲門那一根：spar deck 只有 lodging knee）')):
        ix = xsec - X0
        a = np.zeros((SY, NZ, 3), np.uint8)
        a[:] = PAPER
        a[K.G[ix] > 0] = HULLC
        for d in DECKS:
            for k in CODES:
                a[K.L[d][ix] == CODE[k]] = mc[k]
        im = Image.fromarray(np.transpose(a, (1, 0, 2))[::-1][NZ - 132:]).resize((SY * 4, 132 * 4), Image.NEAREST)
        secs.append((cap, im))
    # ── 排版
    PADL = 70
    Wc = max(W, int((xb - xa) * pv), 2 * (SY * 4 + 40) + 300) + PADL + 30
    y = 0
    Htot = 70 + Hs + 50 + len(plans) * (Hp + 46) + 40 + 132 * 4 + 60 + 260
    can = Image.new('RGB', (Wc, Htot), PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), K.P['title'], font=f18, fill=INK)
    dr.text((PADL, 40), '上：中線縱剖面　中：四層平面（從上往下看，圖上方 ＝ y > 160 那一舷；板下的骨架半透明、開口深灰、黑點 ＝ 站在這層上的柱子）　下：船中剖面（往船頭看）　1 格 ＝ 0.1 m', font=f12, fill=INK)
    y = 70
    can.paste(sec, (PADL, y))

    def SX_(x):
        return PADL + (x - xa) * sc
    for xs_ in K.I['decks']['seams']:
        xx = SX_(int(xs_))
        dr.line([(xx, y), (xx, y + Hs)], fill=(170, 170, 170))
        dr.text((xx + 2, y + 2), xs_, font=f12, fill=(120, 120, 120))
    for m in ('mizzen', 'main', 'fore'):
        mm = K.P['masts'][m]
        t = math.tan(math.radians(mm['rake_deg']))
        p0 = (SX_(mm['x_gun'] - (20 - 80) * t), y + (zb - 20) * sc)
        p1 = (SX_(mm['x_gun'] - (128 - 80) * t), y + (zb - 128) * sc)
        dr.line([p0, p1], fill=(200, 120, 40), width=1)
        dr.text((p1[0] - 14, p1[1] - 16), m, font=f12, fill=(200, 120, 40))
    for d in DECKS:
        for a, b, zz in K.I['decks'][d]['segments']:
            a = xa if a is None else a
            dr.text((SX_(a) + 3, y + (zb - zz) * sc - 15), '%s %d' % (d, zz), font=f12, fill=DECKC[d])
    for x in range(xa, xb, 50):
        dr.text((SX_(x) - 8, y + Hs + 4), str(x), font=f12, fill=(120, 120, 120))
    y += Hs + 50
    for d, im in plans:
        dr.text((PADL, y - 2), '%s deck（甲板面 %s）' % (d, ' | '.join(('%s–%s: %d' % ('…' if a is None else a, '…' if b is None else b, z)) for a, b, z in K.I['decks'][d]['segments'])),
                font=f14, fill=DECKC[d])
        y += 22
        can.paste(im, (PADL, y))
        for h in K.hatches(d):
            xx = PADL + (h['x'][0] - xa) * pv
            dr.text((xx, y + Hp + 1), h['name'], font=f12, fill=(110, 110, 110))
        for x in range(xa, xb, 50):
            dr.line([(PADL + (x - xa) * pv, y + Hp - 4), (PADL + (x - xa) * pv, y + Hp)], fill=(150, 150, 150))
        y += Hp + 24
    y += 16
    x = PADL
    for cap, im in secs:
        dr.text((x, y), cap, font=f14, fill=INK)
        can.paste(im, (x, y + 24))
        x += SY * 4 + 40
    # 圖例
    lx, ly = x + 10, y + 24
    dr.text((lx, ly), '圖例（作品裡的顏色）', font=f14, fill=INK)
    ly += 26
    names = {'plank': '甲板板 250', 'beam': '橫樑 136', 'carling': 'carlings 136', 'partner': '桅 partners 104', 'hook': 'deck hooks／transom knees 104',
             'lodging': 'lodging knees 104', 'knee': 'hanging knees 104', 'waterway': 'waterway 136', 'coaming': '艙口圍板 104', 'sill': '504 橫檻 104',
             'coat': '桅座（mast coat）104', 'pillar': '柱子 136'}
    for k in CODES:
        dr.rectangle([lx, ly, lx + 22, ly + 16], fill=mc[k], outline=(90, 90, 90))
        dr.text((lx + 30, ly), names[k], font=f12, fill=INK)
        ly += 22
    dr.rectangle([lx, ly, lx + 22, ly + 16], fill=HULLC, outline=(90, 90, 90))
    dr.text((lx + 30, ly), '船殼（階段九做完的）', font=f12, fill=INK)
    ly += 34
    for d in reversed(DECKS):
        c = K.v[d]
        dr.text((lx, ly), '%s：%d 格' % (d, c['cells']), font=f12, fill=DECKC[d])
        dr.text((lx + 14, ly + 17), '橫樑 %d 根、柱子 %d、hanging knee %d' % (len(K.log[d]['beams']), len(K.log[d]['pillars']), K.log[d]['knees']['placed']), font=f12, fill=DECKC[d])
        ly += 38
    y += 24 + 132 * 4 + 20
    can = can.crop((0, 0, Wc, min(Htot, max(y, ly) + 20)))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    K = Decks(design)
    for d in DECKS:
        K.build(d)
    K.pillars()
    K.tidy()
    v = K.verify()
    K.write()
    v['files'] = K.files
    v['log'] = K.log
    v['world_voxels'] = len(K.world)
    v['expect_after_composed'] = len(K.world) + v['total_new']
    v['cavity_filled'] = K.cavity_filled
    json.dump(v, open(os.path.join(design, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(K, os.path.join(design, 'sheet08_decks_v1.png'))
    short = {k: v[k] for k in ('total_new', 'overlap_between_decks', 'composed_voxels', 'composed_components', 'cavities_composed', 'headroom_to_beams_above')}
    for d in DECKS:
        short[d] = {k: v[d][k] for k in ('cells', 'by_member', 'mirror_mismatch', 'outside_inner_air', 'plank_components', 'components')}
        short[d]['beams'] = len(K.log[d]['beams'])
        short[d]['knees'] = K.log[d]['knees']
        short[d]['pillars'] = len(K.log[d]['pillars'])
        short[d]['pillars_skipped'] = K.log[d]['pillars_skipped']
    print(json.dumps(short, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
