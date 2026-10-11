# 新圖紙 07（TASK-0496）：船殼內部 —— plan.json 的 interior 段 ＋ 作品（interior.world_upto；空 ＝ 現況）＋ 船殼表（draft_planking.Model）
#   ⇒ masks/interior/{ceiling,limber,bands,riders,hooks}.vox.txt（stampvox，at=0,0,0）、verify_interior.json、sheet07_interior_v1.png
# 用法：python -I draft_interior.py <design 資料夾>
#   · 艙內空氣 ＝ 船殼 S（格中心在 molded 線以內、z_min..肋骨頂）裡的空格、跟船中 (440,160,60) 6 連通的那一塊
#   · 肋骨之間 1 格寬的縫（沿 x 兩邊都是實心）先當成實心看 ⇒ 內板 ＝ 艙內空氣裡、6 鄰居碰到船殼實心（不算 |dy| ≤ 2 的中線結構）的那一層；
#     砲門開口那幾列（兩舷、所有 dy）不鋪 ⇒ 開口的隧道往內多一格
#   · bands（clamps／stringer／spirketting）＝ 舷側內板再往內一格，z 範圍照甲板分段（艙壁處一起升降）；limber ＝ 底肋頂上那層內板再往上一格
#   · 斜肋：每個 x 切片沿內板量弧長（從 keelson 旁起），在（x, 弧長）展開面上畫一條 angle 度的帶子（寬 sided），再往艙內長 moulded 格
#   · hooks：船頭／船尾那幾層 z，離船殼內面 moulded 格以內、兩臂 arm 格長
#   · 兩舷照中線鏡像（同一支程式兩邊各算一次，產完逐格驗鏡像）
import sys, os, json, glob, hashlib, heapq
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import draft_planking as DP        # noqa: E402
from replay import replay          # noqa: E402

X0, X1, NDY, NZ = DP.X0, DP.X1, DP.NDY, DP.NZ
YC = DP.YC
Y0 = YC - NDY + 1
SX, SY = X1 - X0, 2 * NDY - 1
SEED = (440, 160, 60)
PAINT = (36, 168, 255)


def shift(a, ax, k):
    """out[i] = a[i − k]（沿 ax，補 0）。"""
    out = np.zeros_like(a)
    src = [slice(None)] * a.ndim
    dst = [slice(None)] * a.ndim
    if k > 0:
        src[ax], dst[ax] = slice(0, -k), slice(k, None)
    else:
        src[ax], dst[ax] = slice(-k, None), slice(0, k)
    out[tuple(dst)] = a[tuple(src)]
    return out


def nb6(a):
    o = np.zeros_like(a)
    for ax in range(a.ndim):
        for k in (1, -1):
            o |= shift(a, ax, k)
    return o


def seg_z(segs, x):
    for a, b, z in segs:
        if (a is None or x >= a) and (b is None or x < b):
            return z
    return None


def seg_bounds(segs, x):
    for a, b, z in segs:
        if (a is None or x >= a) and (b is None or x < b):
            return a, b
    return None, None


class Interior:
    def __init__(s, design):
        s.design = design
        s.W = os.path.dirname(os.path.abspath(design))
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['interior']
        # 讀「階段九第一刀之前」的作品（標記 船殼內部:begin）—— 讀現況的話，apply 之後重跑會把內板當成船殼再往內鋪一層
        if s.P.get('world_mark'):
            s.world = {k: v[0] for k, v in replay(s.W, mark=s.P['world_mark']).items()}
        else:
            s.world = {k: v[0] for k, v in replay(s.W, upto=s.P.get('world_upto') or None).items()}
        if s.P.get('world_voxels'):
            assert len(s.world) == s.P['world_voxels'], ('讀到的作品格數對不上 world_voxels', len(s.world), s.P['world_voxels'])
        G = np.zeros((SX, SY, NZ), np.uint8)
        for (x, y, z), c in s.world.items():
            assert X0 <= x < X1 and Y0 <= y < Y0 + SY and z < NZ, ('作品超出網格', x, y, z)
            G[x - X0, y - Y0, z] = c
        s.G = G
        M = DP.Model(design)
        M.lines()
        M.hull()
        s.S = DP.full(M.S)
        s.zt = M.zt
        s.vp = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))
        plank = np.zeros(G.shape, bool)
        for f in glob.glob(os.path.join(design, 'masks', 'planking', 'plank_*.vox.txt')) + [os.path.join(design, 'masks', 'planking', 'dub.vox.txt')]:
            a = np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
            ok = (a[:, 0] >= X0) & (a[:, 0] < X1) & (a[:, 1] >= Y0) & (a[:, 1] < Y0 + SY)
            plank[a[ok, 0] - X0, a[ok, 1] - Y0, a[ok, 2]] = True
        s.plank = plank
        iy = np.arange(SY)
        s.dy = np.abs(iy - (YC - Y0))
        s.side = np.sign(iy - (YC - Y0))
        s.xs = np.arange(X0, X1)

    # ───────── 艙內空氣與內板 ─────────
    def ceiling(s):
        G, S = s.G, s.S
        SOL = G > 0
        air = ~SOL & S
        lab, _ = ndimage.label(air)
        k = lab[SEED[0] - X0, SEED[1] - Y0, SEED[2]]
        assert k > 0, '種子不是空氣'
        IA = lab == k
        GAP = IA & shift(SOL, 0, 1) & shift(SOL, 0, -1)          # 兩邊（x−1、x+1）都是實心的 1 格縫
        PORTXZ = np.zeros((SX, NZ), bool)
        for p in s.vp['ports']:
            for zz, (xa, xb) in p['x_rows'].items():
                PORTXZ[xa - X0:xb - X0 + 1, int(zz)] = True
        s.PORT3 = np.broadcast_to(PORTXZ[:, None, :], SOL.shape)
        SOLc = SOL | GAP
        # 有深度上限的閉合（評審 A2）：船殼那一層（離 S 外緣 ≤ 4.5 格）裡、6 鄰居有 ≥ 4 格實心的空格當成實心，重複到不再變 ——
        # cant 之間斜著的縫、坑先補平，內板才不會照著鋸齒走；不設深度上限會一路灌進船尾的 V 形艙底（verifier 試過）
        shallow = ndimage.distance_transform_edt(S) <= 4.5
        s.closed = 0
        while True:
            n = np.zeros(SOL.shape, np.uint8)
            for ax in range(3):
                for k in (1, -1):
                    n += shift(SOLc, ax, k)
            add = IA & ~SOLc & shallow & ~s.PORT3 & (n >= 4)
            if not add.any():
                break
            SOLc |= add
            s.closed += int(add.sum())
        s.IA1 = IA & ~SOLc
        # 中線結構（keelson、deadwood、apron、艏柱、艉柱）—— 只算木料、只算艉柱以前（x ≥ centreline_x_min）；
        # 中線那幾格的外板（船尾面、艏柱頭）與船尾的橫材照樣要蓋（評審 F5）
        xmin = s.P['members'].get('centreline_x_min', X0)
        CLS = SOL & (s.dy[None, :, None] <= 2) & ~(s.plank & SOL) & ~np.isin(G, PAINT) & (s.xs >= xmin)[:, None, None]
        s.CLS = CLS
        s.HS = SOLc & ~CLS
        s.SOLc = SOLc
        s.SKIN = s.IA1 & nb6(s.HS) & ~s.PORT3
        s.gap_cells = int(GAP.sum())
        # 舷頂封口：肋骨之間的縫（當成實心、實際還空著的格）在舷頂那一列（z ＝ 肋骨頂）補 141 ——
        # 不封的話縫從船底通到舷頂開口，從上面看是一條條深縫、匯出多一堆內面；封了之後整條縫變封閉空腔，收尾時 fill_cavities 補實
        top = np.arange(NZ)[None, None, :] == np.asarray(s.zt)[:, None, None]
        s.CAP = (SOLc & ~SOL) & top & ~s.PORT3
        s.free = s.IA1 & ~s.SKIN & ~s.PORT3                      # 內板之內、還可以放構件的空氣

    # ───────── clamps／stringer／spirketting、limber ─────────
    def ports_info(s):
        out = []
        for p in s.vp['ports']:
            zs = sorted(int(z) for z in p['x_rows'])
            xr = [p['x_rows'][str(z)] for z in zs]
            xa, xb = min(a for a, b in xr), max(b for a, b in xr)
            out.append({'n': p['n'], 'xa': xa, 'xb': xb, 'xc': (xa + xb) / 2, 'sill': zs[0], 'lintel': zs[-1]})
        return out

    def bands(s):
        D = s.P['decks']
        mask = np.zeros((SX, NZ), bool)
        s.band_rows = []                                         # 給圖紙畫
        xr = {'orlop': tuple(D['orlop'].get('stringer_x', (167, 633))), 'berth': (150, 645), 'gun': (135, 655), 'spar': (112, 660)}
        ports = s.ports_info()
        for name in ('orlop', 'berth', 'gun', 'spar'):
            d = D[name]
            lo_x, hi_x = xr[name]
            for x in range(lo_x, hi_x + 1):
                if name == 'orlop':
                    S_ = d['segments'][0][2]                       # stringer 連續（中間的開放貨艙也有）
                else:
                    S_ = seg_z(d['segments'], x)
                if S_ is None:
                    continue
                top = S_ - d['plank'] - d['beam'] - 1
                n = d.get('clamp', d.get('stringer'))
                mask[x - X0, top - n + 1: top + 1] = True
                s.band_rows.append((name, 'clamp', x, top - n + 1, top))
                sp = d.get('spirketting')
                if sp == 'sill':
                    # 到這一段最低的砲門下緣 − 1；下緣較高的砲門底下（開口 ±1）再補到它自己的下緣 − 1
                    a, b = seg_bounds(d['segments'], x)
                    seg = [p for p in ports if (a is None or p['xc'] >= a) and (b is None or p['xc'] < b)]
                    sp_top = (min(p['sill'] for p in seg) - 1) if seg else S_ + 4
                    under = [p for p in ports if p['xa'] - 1 <= x <= p['xb'] + 1]
                    if under:
                        sp_top = max(sp_top, max(p['sill'] for p in under) - 1)
                    mask[x - X0, S_: sp_top + 1] = True
                    s.band_rows.append((name, 'spirketting', x, S_, sp_top))
                elif sp:
                    mask[x - X0, S_: S_ + sp] = True
                    s.band_rows.append((name, 'spirketting', x, S_, S_ + sp - 1))
        rows = s.free & mask[:, None, :]
        # 往內一格沿船殼表面的法向（6 鄰居碰到內板），再在同一層 z 補一次斜接（x、y 兩個方向都有帶子鄰居的格）—— 只補一次、不跨 z（評審 A1）
        B = rows & nb6(s.SKIN)
        nbx = shift(B, 0, 1) | shift(B, 0, -1)
        nby = shift(B, 1, 1) | shift(B, 1, -1)
        s.BAND = B | (rows & nbx & nby)
        L = s.P['members']['limber']
        xm = np.zeros(SX, bool)
        xm[L['x'][0] - X0: L['x'][1] - X0 + 1] = True
        dm = (s.dy >= L['dy'][0]) & (s.dy <= L['dy'][1])
        s.LIMB = s.free & shift(s.SKIN, 2, 1) & xm[:, None, None] & dm[None, :, None] & ~s.BAND

    # ───────── 斜肋 ─────────
    def girth(s, ix, sgn):
        """切片 x 的內板（sgn 那一舷）沿船殼的弧長：從 keelson 旁（鄰著中線結構）起，8 鄰居 Dijkstra（斜 √2）。回傳 {(iy, z): s}。"""
        sk = s.SKIN[ix] & (s.side[:, None] == sgn)
        cells = set(map(tuple, np.argwhere(sk)))
        if not cells:
            return {}
        sol = s.G[ix] > 0
        starts = [c for c in cells if s.dy[c[0]] <= 4 and any(0 <= c[0] + d < SY and sol[c[0] + d, c[1]] and s.dy[c[0] + d] <= 2 for d in (-1, 1))]
        if not starts:
            m = min(s.dy[c[0]] for c in cells)
            starts = [c for c in cells if s.dy[c[0]] == m]
        dist = {c: 0.0 for c in starts}
        h = [(0.0, c) for c in starts]
        while h:
            d0, c = heapq.heappop(h)
            if d0 > dist[c]:
                continue
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    if a == 0 and b == 0:
                        continue
                    n = (c[0] + a, c[1] + b)
                    if n in cells:
                        nd = d0 + (1.4142 if a and b else 1.0)
                        if nd < dist.get(n, 1e9):
                            dist[n] = nd
                            heapq.heappush(h, (nd, n))
        return dist

    def riders(s):
        R = s.P['members']['riders']
        st = s.P['stations']
        tan = np.tan(np.radians(R['angle_deg']))
        D = s.P['decks']['berth']
        RID = np.zeros_like(s.SKIN)
        s.rider_lines = []
        for end, heads in (('forward', R['heads_st']['forward']), ('aft', R['heads_st']['aft'])):
            for st_h in heads:
                xh = int(round(st['x0'] + st['per_ft'] * st_h))
                S_b = seg_z(D['segments'], xh)
                zh = S_b - D['plank'] - D['beam'] - 1 - D['clamp']          # berth clamp 底下那一格
                for sgn in (1, -1):
                    g = s.girth(xh - X0, sgn)
                    side = [(c, v) for c, v in g.items() if c[1] == zh]
                    assert side, ('斜肋頭那一層沒有內板', xh, zh)
                    st_t = max(side, key=lambda cv: s.dy[cv[0][0]])[1]
                    run = st_t / tan
                    xheel = xh - run if end == 'forward' else xh + run
                    ws = R['sided'] / 2 * np.sqrt(1 + tan ** 2)
                    if sgn == 1:
                        s.rider_lines.append((end, st_h, xh, zh, round(xheel, 1), round(st_t, 1)))
                    for x in range(int(np.floor(min(xh, xheel))) - 1, int(np.ceil(max(xh, xheel))) + 2):
                        ix = x - X0
                        t = (x - xheel) / (xh - xheel)
                        sl = st_t * t
                        if sl < -ws or sl > st_t + ws:
                            continue
                        gx = s.girth(ix, sgn) if x != xh else g
                        fp = np.zeros((SY, NZ), bool)
                        for (a, b), v in gx.items():
                            if abs(v - sl) <= ws and 0 <= v <= st_t:
                                fp[a, b] = True
                        if not fp.any():
                            continue
                        other = s.SKIN[ix] & (s.side[:, None] == sgn) & ~fp
                        d_fp = ndimage.distance_transform_edt(~fp)
                        d_ot = ndimage.distance_transform_edt(~other) if other.any() else np.full(fp.shape, 1e9)
                        body = s.free[ix] & (d_fp <= R['moulded'] + 0.5) & (d_fp <= d_ot) & (s.side[:, None] == sgn) & (s.dy[:, None] >= 3)
                        S_x = seg_z(D['segments'], x)                        # 頭停在 berth clamp 底下（評審 R8／F2）—— 每個 x 用自己那一段的甲板高
                        zh_x = S_x - D['plank'] - D['beam'] - 1 - D['clamp'] if S_x is not None else zh
                        body &= np.arange(NZ)[None, :] <= min(zh, zh_x)
                        RID[ix] |= body
        s.RID = RID

    # ───────── breast hooks／crutches ─────────
    def hooks(s):
        H = s.P['members']['hooks']
        HK = np.zeros_like(s.SKIN)
        s.hook_rows = []
        for end, zs in (('bow', H['bow_z']), ('stern', H['stern_z'])):
            for z0 in zs:
                for z in range(z0, z0 + H['rows']):
                    ia = s.IA1[:, :, z]
                    xi = np.where(ia.any(1))[0]
                    if not len(xi):
                        continue
                    if end == 'bow':
                        xm = np.arange(SX) >= xi.max() - H['arm']
                    else:
                        xm = np.arange(SX) <= xi.min() + H['arm']
                    d = ndimage.distance_transform_edt(~s.SOLc[:, :, z])
                    cell = s.free[:, :, z] & (d <= H['moulded'] + 1.5) & xm[:, None]
                    HK[:, :, z] |= cell
                    s.hook_rows.append((end, z, int(cell.sum())))
        s.HK = HK & ~s.RID
        s.BAND &= ~s.RID & ~s.HK
        s.LIMB &= ~s.RID & ~s.HK

    # ───────── 橫向 rider（v1.1）─────────
    def transverse(s):
        """對齊肋骨站位、疊在內板上的橫向 rider：每個切片離實心（含這一階段已經算好的內板、limber、斜肋…）≤ moulded＋0.5 的艙內空氣，
        dy ≥ 3、z ≤ z_max、寬 sided（x0 置中）。"""
        T = s.P['members'].get('transverse_riders')
        s.RT = np.zeros_like(s.SKIN)
        s.rt_x = []
        if not T:
            return
        fr = s.plan['lines']['frames']
        occ = (s.G > 0) | s.SKIN | s.LIMB | s.BAND | s.RID | s.HK | s.CAP
        zm = np.arange(NZ)[None, :] <= T['z_max']
        for k in T['frames']:
            xc = int(round(fr['x0'] + k * fr['spacing']))
            s.rt_x.append(xc)
            for x in range(xc - T['sided'] // 2, xc + T['sided'] // 2 + 1):
                ix = x - X0
                d = ndimage.distance_transform_edt(~occ[ix])
                body = s.free[ix] & ~occ[ix] & (d <= T['moulded'] + 0.5) & zm & (s.dy[:, None] >= 3)
                s.RT[ix] |= body
        dil = ndimage.binary_dilation(s.RID | s.HK, iterations=1)
        s.rt_touch_diagonal = int((s.RT & dil).sum())

    # ───────── 驗算 ─────────
    def verify(s):
        M = s.P['members']
        parts = [('ceiling', s.SKIN, M['ceiling']['color']), ('limber', s.LIMB, M['limber']['color']),
                 ('bands', s.BAND, M['bands']['color']), ('riders', s.RID, M['riders']['color']), ('hooks', s.HK, M['hooks']['color']),
                 ('cap', s.CAP, M.get('cap', {}).get('color', 141))]
        if M.get('transverse_riders'):
            parts.append(('riders_t', s.RT, M['transverse_riders']['color']))
        tot = np.zeros_like(s.SKIN, np.uint8)
        for _, m, _c in parts:
            assert not (tot.astype(bool) & m).any(), '清單之間有重疊'
            tot[m] = 1
        new = s.G.copy()
        for name, m, c in parts:
            assert not (s.G[m] > 0).any(), '落在實心的格上'
            if name != 'riders_t':                 # 換色照 v1（橫向 rider 之前）的艙內空氣算 —— v1 已套進作品，重產要逐格一樣
                new[m] = c
        s.parts = parts
        # 中線結構露在艙內的那一層換色（評審 A3）：跟艙內空氣共面、不跟船殼 S 外的空氣共面
        rc = M.get('centreline_recolor', {})
        mapping = {v[0]: v[1] for v in rc.values() if isinstance(v, list)}
        air = new == 0
        lab, _ = ndimage.label(air & s.S)
        ia_new = lab == lab[SEED[0] - X0, SEED[1] - Y0, SEED[2]]
        s.REC = s.CLS & np.isin(s.G, list(mapping)) & nb6(ia_new) & ~nb6(air & ~s.S)
        s.rec_col = np.zeros_like(s.G)
        for a, b in mapping.items():
            s.rec_col[s.REC & (s.G == a)] = b
        new[s.REC] = s.rec_col[s.REC]
        for name, m, c in parts:
            if name == 'riders_t':
                new[m] = c
        s.recolor_by = {'%d→%d' % (a, b): int((s.REC & (s.G == a)).sum()) for a, b in mapping.items()}
        # 帶子在船頭船尾還碎不碎（右舷，6 連通的塊數）、斜肋有沒有穿進 berth clamp、斜肋穿過 orlop 平台那一層的 x 範圍
        stb = (s.side > 0)[None, :, None]
        xs = s.xs[:, None, None]
        s.band_pieces = {}
        for nm, sel in (('stern_x<190', xs < 190), ('bow_x>=610', xs >= 610), ('mid_250-560', (xs >= 250) & (xs < 560))):
            _, k = ndimage.label(s.BAND & stb & sel)
            s.band_pieces[nm] = int(k)
        D = s.P['decks']['berth']
        clamp_rows = np.zeros((SX, NZ), bool)
        for ix in range(SX):
            S_ = seg_z(D['segments'], ix + X0)
            if S_ is not None:
                top = S_ - D['plank'] - D['beam'] - 1
                clamp_rows[ix, top - D['clamp'] + 1: S_] = True       # clamp 到甲板面（含橫樑、甲板板）
        s.rider_in_clamp = int((s.RID & clamp_rows[:, None, :]).sum())
        cross = {}
        zz = (np.arange(NZ) >= 38) & (np.arange(NZ) <= 41)
        xs_hit = np.where((s.RID & stb & zz[None, None, :]).any((1, 2)))[0] + X0
        runs = []
        for x in xs_hit:
            if runs and x == runs[-1][1] + 1:
                runs[-1][1] = int(x)
            else:
                runs.append([int(x), int(x)])
        cross['starboard_x_runs_z38_41'] = runs
        cross['mirrored'] = True
        s.riders_cross_orlop = cross
        # 看得到的外板漆（艙內空氣 ＝ 船殼 S 裡、跟種子連通的空格；面的另一邊是外板格或塗裝色）
        # 砲門開口那幾列裡的空氣不算：從艙內看穿砲門，看到開口邊緣的外板是應該的
        plank = s.plank

        def paint_faces(g):
            air = (g == 0) & s.S
            lab, _ = ndimage.label(air)
            ia = (lab == lab[SEED[0] - X0, SEED[1] - Y0, SEED[2]])
            paint = ((plank & (g > 0)) | np.isin(g, PAINT))
            n = n_port = 0
            for ax in range(3):
                for k in (1, -1):
                    f = ia & shift(paint, ax, k)
                    n += int((f & ~s.PORT3).sum())
                    n_port += int((f & s.PORT3).sum())
            return n, n_port
        (s.paint_before, s.paint_before_port) = paint_faces(s.G)
        (s.paint_after, s.paint_after_port) = paint_faces(new)
        # 砲門還透光：開口那幾列（兩舷、所有 dy）一格都沒放
        s.port_hits = int((s.PORT3 & (new > 0) & ~(s.G > 0)).sum())
        # 結構：元件數、封閉空腔
        lab, ncomp = ndimage.label(new > 0)
        s.components = ncomp
        pad = np.pad(new > 0, 1)
        lab2, _ = ndimage.label(~pad)
        inner = (lab2 != lab2[0, 0, 0]) & ~pad
        s.cav_cells = int(inner.sum())
        s.cav_n = int(len(np.unique(lab2[inner]))) if s.cav_cells else 0
        # 鏡像
        mir = 0
        for _, m, _c in parts + [('recolor', s.REC, 0)]:
            mir += int((m != m[:, ::-1, :]).sum())
        s.mirror = mir

    # ───────── 輸出 ─────────
    def write(s):
        out = os.path.join(s.design, 'masks', 'interior')
        os.makedirs(out, exist_ok=True)
        for f in glob.glob(os.path.join(out, '*')):
            os.remove(f)
        notes = {'ceiling': '內板（running ceiling，1 格）', 'limber': 'limber 厚板（底肋頂上多一層）',
                 'bands': 'clamps／orlop stringer／spirketting（舷側多一層）', 'riders': '斜肋（diagonal riders，live oak）',
                 'hooks': 'breast hooks（船頭）／crutches（船尾）', 'cap': '舷頂封口（肋骨之間的縫在肋骨頂那一列補實）',
                 'riders_t': '橫向 rider（v1.1，對齊肋骨站位、疊在內板上）'}
        s.files = {}
        for name, m, c in s.parts:
            idx = np.argwhere(m)
            p = os.path.join(out, name + '.vox.txt')
            body = '\n'.join('%d,%d,%d,%d' % (i + X0, j + Y0, k, c) for i, j, k in idx)
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（%d 格，at=0,0,0）\n' % (name, notes[name], len(idx)) + body + '\n')
            s.files[name] = {'cells': len(idx), 'color': c, 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        idx = np.argwhere(s.REC)
        p = os.path.join(out, 'recolor.vox.txt')
        body = '\n'.join('%d,%d,%d,%d' % (i + X0, j + Y0, k, s.rec_col[i, j, k]) for i, j, k in idx)
        open(p, 'w', encoding='utf-8', newline='\n').write(
            '# recolor —— 中線結構露在艙內那一層換色（stampvox overwrite=1；%s；%d 格，at=0,0,0）\n' % ('、'.join('%s %d' % kv for kv in s.recolor_by.items()), len(idx)) + body + '\n')
        s.files['recolor'] = {'cells': len(idx), 'overwrite': True, 'by': s.recolor_by, 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}


def render_sheet(I, path):
    """新圖紙 07：上 ＝ 右舷內側立面（從中線往外看：甲板分段、clamps／spirketting、砲門、斜肋、hooks、艙壁）；下 ＝ 船中 x=440 剖面。"""
    sc = 3
    xa, xb, za, zb = 95, 690, 0, 140
    W, H = (xb - xa) * sc, (zb - za) * sc
    top = Image.new('RGB', (W, H + 40), (250, 250, 247))
    d = ImageDraw.Draw(top)

    def P(x, z):
        return ((x - xa) * sc, (zb - z) * sc + 30)
    # 船殼輪廓（每一欄最上、最下的實心格，右舷）
    occ = (I.G[:, YC - Y0:, :] > 0).any(1)
    for ix in range(SX):
        x = ix + X0
        if not (xa <= x < xb):
            continue
        zz = np.where(occ[ix])[0]
        if len(zz):
            d.line([P(x, zz.min()), P(x, zz.max())], fill=(225, 220, 210))
    for p in I.vp['ports']:
        zs = sorted(int(z) for z in p['x_rows'])
        x0, x1 = p['x_rows'][str(zs[0])]
        d.rectangle([P(x0, zs[-1] + 1), P(x1 + 1, zs[0])], outline=(30, 80, 220))
    col = {'clamp': (150, 110, 80), 'spirketting': (190, 150, 110)}
    for name, kind, x, z0, z1 in I.band_rows:
        d.rectangle([P(x, z1 + 1), P(x + 1, z0)], fill=col[kind])
    deckcol = {'orlop': (120, 160, 120), 'berth': (90, 120, 200), 'gun': (200, 80, 60), 'spar': (120, 60, 160)}
    for name, dd in I.P['decks'].items():
        if not isinstance(dd, dict) or 'segments' not in dd:
            continue
        for a, b, zz in dd['segments']:
            a = xa if a is None else a
            b = xb if b is None else b
            d.line([P(a, zz), P(b, zz)], fill=deckcol[name], width=2)
            d.text(P(a + 2, zz + 3), '%s %d' % (name, zz), fill=deckcol[name])
    for xs in I.P['decks']['seams']:
        d.line([P(int(xs), 20), P(int(xs), 125)], fill=(160, 160, 160))
        d.text(P(int(xs) + 1, 128), xs, fill=(100, 100, 100))
    for end, st_h, xh, zh, xheel, st_t in I.rider_lines:
        d.line([P(xh, zh), P(xheel, 16)], fill=(90, 50, 60), width=3)
    for end, z, n in I.hook_rows:
        if n:
            x = 640 if end == 'bow' else 150
            d.line([P(x - 6, z), P(x + 6, z)], fill=(90, 50, 60), width=2)
    d.text((8, 6), 'sheet 07 v1  hull interior (starboard, inboard elevation): deck surfaces (lines), clamps/stringer (dark) & spirketting (light), gun ports (blue), diagonal riders & hooks (maroon), seams (grey)', fill=(0, 0, 0))
    # 船中剖面
    ix = 440 - X0
    sl = np.zeros((SY, NZ, 3), np.uint8) + 250
    sl[I.G[ix] > 0] = (205, 195, 180)
    for name, m, c in I.parts:
        sl[m[ix]] = DP.rgb332(c)
    sec = Image.fromarray(np.transpose(sl, (1, 0, 2))[::-1]).resize((SY * 4, NZ * 4), Image.NEAREST)
    canvas = Image.new('RGB', (max(W, SY * 4), H + 40 + NZ * 4 + 30), (250, 250, 247))
    canvas.paste(top, (0, 0))
    canvas.paste(sec, (0, H + 60))
    ImageDraw.Draw(canvas).text((SY * 4 + 10, H + 70), 'midship section x=440 (looking forward): frames/plank grey, ceiling / limber / bands / riders / hooks in their colours', fill=(0, 0, 0))
    canvas.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    I = Interior(design)
    I.ceiling()
    I.bands()
    I.riders()
    I.hooks()
    I.transverse()
    I.verify()
    I.write()
    new_cells = sum(f['cells'] for k, f in I.files.items() if k != 'recolor')
    v = {'title': I.P['title'], 'task': I.P['task'], 'world_mark': I.P.get('world_mark', ''), 'world_voxels': len(I.world),
         'gap_cells_x': I.gap_cells, 'closed_cells_depth_bounded': I.closed, 'files': I.files, 'total_new': new_cells,
         'expect_after': len(I.world) + new_cells, 'recolor': I.recolor_by,
         'band_pieces_starboard': I.band_pieces, 'rider_cells_in_berth_clamp_or_beam': I.rider_in_clamp,
         'riders_cross_orlop': I.riders_cross_orlop,
         'visible_paint_faces': {'before': I.paint_before, 'after': I.paint_after,
                                 'in_port_openings_before': I.paint_before_port, 'in_port_openings_after': I.paint_after_port},
         'port_cells_hit': I.port_hits, 'components_after': I.components,
         'cavities_after': {'n': I.cav_n, 'cells': I.cav_cells}, 'mirror_mismatch': I.mirror,
         'riders': [{'end': e, 'head_st': a, 'head_x': b, 'head_z': c, 'heel_x': h, 'girth': g} for e, a, b, c, h, g in I.rider_lines],
         'hooks': [{'end': e, 'z': z, 'cells': n} for e, z, n in I.hook_rows]}
    json.dump(v, open(os.path.join(design, 'verify_interior.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(I, os.path.join(design, 'sheet07_interior_v1.png'))
    print(json.dumps({k: v[k] for k in ('world_voxels', 'gap_cells_x', 'closed_cells_depth_bounded', 'files', 'total_new', 'expect_after', 'recolor',
                                        'visible_paint_faces', 'port_cells_hit', 'components_after', 'cavities_after', 'mirror_mismatch',
                                        'band_pieces_starboard', 'rider_cells_in_berth_clamp_or_beam', 'riders_cross_orlop', 'riders', 'hooks')},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
