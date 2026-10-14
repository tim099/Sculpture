# 新圖紙 08 外板・wale・塗裝・吃水刻度 v1（階段七，TASK-0538）：plan.json planking ＋ 船殼表（HullGrid，跟肋骨同一套）＋ 階段一～六的清單
#   ⇒ 外板的 3D 格子清單（給 `sculpture op=stampvox at=0,0,0`）、dubbing／結構塗裝清單（overwrite=1）、新圖紙 08、verify_planking.json。
# 用法：python -I draft_planking.py <design 資料夾> [作品 export list 檔]
#   · 開工前的作品 ＝ 階段一～六的清單（masks/）；給了 export list 就先逐格對一次，對不上不產（雕完重跑讀現況會把外板當船殼、再長一層）。
#   · 船殼 S ＝ 格中心在 molded 裡（dy/cpm ≤ hb）、z ≥ 龍骨頂、≤ 舷牆頂 —— 跟 draft_frames.frame_cells 同一套條件。
#   · 外板 L1 ＝ 不在 S、跟 S 共用一個面、現在是空的；高度 ≤ 那一欄 S 的頂（不往舷牆頂上長、也不在舷弧的台階處長出橫牆）。
#   · wale L2 ＝ 舷側那一格外板（往中線那一格在 S 裡）的外面一格、wale 帶內。
#   · 顏色：黑；吃水線以下深鏽褐；吃水刻度白（從外面看左到右讀得正：右舷 y > 160 船頭在右手邊）。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_frames import Ctx   # noqa: E402

YC = 160
X0G, X1G, NDY, NZ = 40, 700, 76, 216          # 網格：X 範圍、半舷 dy 0..NDY−1、Z 0..NZ−1

GLYPH = {
    '0': ('111', '101', '101', '101', '111'), '1': ('010', '110', '010', '010', '111'),
    '2': ('111', '001', '111', '100', '111'), '3': ('111', '001', '111', '001', '111'),
    '4': ('101', '101', '111', '001', '001'), '5': ('111', '100', '111', '001', '111'),
    '6': ('111', '100', '111', '101', '111'), '7': ('111', '001', '001', '001', '001'),
    '8': ('111', '101', '111', '101', '111'), '9': ('111', '101', '111', '001', '111'),
}


def rgb332(i):
    return (round(((i >> 5) & 7) * 255 / 7), round(((i >> 2) & 7) * 255 / 7), round((i & 3) * 255 / 3))


def full(a):
    """只存 dy ≥ 0 的半舷陣列 → 整舷（第 1 軸 j ＝ dy + NDY − 1）。"""
    return np.concatenate([a[:, :0:-1, :], a], axis=1)


def shift_or(m):
    """6 鄰居裡有沒有 m"""
    o = np.zeros_like(m)
    o[1:] |= m[:-1]
    o[:-1] |= m[1:]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    o[:, :, 1:] |= m[:, :, :-1]
    o[:, :, :-1] |= m[:, :, 1:]
    return o


def read_list(p):
    out = {}
    for ln in open(p, encoding='utf-8'):
        ln = ln.strip()
        if ln and ln[0] != '#':
            x, y, z, c = (int(v) for v in ln.split(',')[:4])
            out[(x, y, z)] = c
    return out


class Model:
    def __init__(s, design):
        s.design = design
        s.cx = Ctx(design)
        s.P = s.cx.plan['planking']
        s.xs = np.arange(X0G, X1G)
        s.zs = np.arange(NZ)
        s.dys = np.arange(NDY)
        s.world = {}
        for sub in ('keel', 'posts', 'deadwood', 'floors', 'frames', 'ends'):
            d = os.path.join(design, 'masks', sub)
            for fn in sorted(os.listdir(d)):
                if fn.endswith('.vox.txt'):
                    w = read_list(os.path.join(d, fn))
                    assert not (w.keys() & s.world.keys()), ('清單重疊', sub, fn)
                    s.world.update(w)
        for (x, y, z) in s.world:
            assert X0G <= x < X1G and abs(y - YC) < NDY and z < NZ, ('作品超出網格', x, y, z)

    def xb(s, X):                                             # 格 X → 底圖 x（格中心）
        return (np.asarray(X, float) + 0.5 - s.cx.X0) / s.cx.cpm

    def zb(s, Z):
        return (np.asarray(Z, float) + 0.5 - s.cx.Zk) / s.cx.cpm

    # ───────── 船殼 S（半舷） ─────────
    def hull(s):
        cx = s.cx
        S = np.zeros((len(s.xs), NDY, NZ), bool)
        for i, X in enumerate(s.xs):
            x = float(s.xb(X))
            col = cx.hg.column(x)
            okz = col >= 0
            if not okz.any():
                continue
            zmax, zmin = float(cx.zs[okz].max()), float(cx.zs[okz].min())
            ztop = float(cx.ship.top(x))
            for Z in range(int(cx.Zk), int(cx.Zk + ztop * cx.cpm) + 2):
                z = float(s.zb(Z))
                if z > ztop or z > zmax or z < zmin:
                    continue
                hb = float(np.interp(z, cx.zs[okz], col[okz]))
                if hb < 0:
                    continue
                S[i, :, Z] = s.dys / cx.cpm <= hb
        s.S = S
        has = S.any(axis=(1, 2))
        s.zt = np.where(has, np.array([np.where(S[i].any(0))[0].max() if has[i] else -1 for i in range(len(s.xs))]), NZ)
        s.has = has
        # 高度上限：有 S 的欄 ＝ 那一欄 S 的頂；沒有 S 的欄（船尾板後面、船頭柱前面）不限
        s.allowed = s.zs[None, :] <= s.zt[:, None]

    def world_arrays(s):
        occ = np.zeros((len(s.xs), 2 * NDY - 1, NZ), bool)
        col = np.zeros(occ.shape, np.int16)
        for (x, y, z), c in s.world.items():
            j = y - YC + NDY - 1
            occ[x - X0G, j, z] = True
            col[x - X0G, j, z] = c
        s.Kf, s.colf = occ, col

    # ───────── 外板 ─────────
    def shell(s):
        from scipy import ndimage
        Sf = full(s.S)
        A = np.broadcast_to(full(np.broadcast_to(s.allowed[:, None, :], s.S.shape)), Sf.shape)
        # dubbing：凸出 molded 線的肋骨格（141／173 在 S 外）
        frame_cols = np.isin(s.colf, s.P['frame_colors'])
        s.D = s.Kf & frame_cols & ~Sf & A
        keep = s.Kf & ~s.D
        L1 = shift_or(Sf) & ~Sf & ~keep & A
        # 只從下面接到 S 的格（S 往上長的那種）：數出來看是不是都是內傾的台階
        lat_or_down = np.zeros_like(Sf)
        lat_or_down[1:] |= Sf[:-1]
        lat_or_down[:-1] |= Sf[1:]
        lat_or_down[:, 1:] |= Sf[:, :-1]
        lat_or_down[:, :-1] |= Sf[:, 1:]
        lat_or_down[:, :, :-1] |= Sf[:, :, 1:]                  # 上面那一格在 S（這一格在 S 底下）
        s.up_only = L1 & ~lat_or_down
        jc = NDY - 1
        lat = np.zeros_like(L1)
        lat[:, jc + 1:, :] = L1[:, jc + 1:, :] & Sf[:, jc:-1, :]       # 右舷：往中線那一格在 S
        lat[:, :jc, :] = L1[:, :jc, :] & Sf[:, 1:jc + 1, :]            # 左舷
        # wale：舷側外板外面一格、wale 帶內（底圖 m）
        Xb = s.xb(s.xs)
        wale = s.cx.ship.wale(np.clip(Xb, -1.0, 41.0))
        wb = s.P['wale_band']
        zc = s.zb(s.zs)[None, :]
        s.wale_bot, s.wale_top = wale + wb[0], wale + wb[1]
        wband = (zc >= s.wale_bot[:, None]) & (zc <= s.wale_top[:, None]) & s.has[:, None]
        W = np.broadcast_to(wband[:, None, :], Sf.shape)
        L2 = np.zeros_like(L1)
        L2[:, jc + 2:, :] = lat[:, jc + 1:-1, :]
        L2[:, :jc - 1, :] |= lat[:, 1:jc, :]
        L2 &= W & ~Sf & ~keep & ~L1 & A
        # 只靠邊接上的碎塊：補一格「橋」（照憲法號；拿掉碎塊會漏水）
        s.bridges = []
        for _ in range(4):
            lab, n = ndimage.label(keep | L1 | L2)
            main = np.bincount(lab[keep]).argmax()
            frag = (L1 | L2) & (lab != main) & (lab > 0)
            if not frag.any():
                break
            br = shift_or(frag) & shift_or(lab == main) & ~Sf & ~keep & ~L1 & ~L2 & A
            s.bridges += [tuple(int(v) for v in c) for c in np.argwhere(br)]
            L1 |= br
        lab, n = ndimage.label(keep | L1 | L2)
        s.n_components = int(n)
        s.Sf, s.keep, s.L1, s.L2, s.lat = Sf, keep, L1, L2, lat

    # ───────── 船外的空氣（有 S 的欄：S 的頂以上當牆 —— 只問從舷側／船底通不通） ─────────
    def outside(s, solid):
        from scipy import ndimage
        A = np.broadcast_to(full(np.broadcast_to(s.allowed[:, None, :], s.S.shape)), solid.shape)
        air = ~solid & A
        airp = np.pad(air, 1, constant_values=True)
        lab, _ = ndimage.label(airp)
        lab = lab[1:-1, 1:-1, 1:-1]
        return air, (lab == lab[0, 0, 0]) & air

    def cavities(s):
        """封閉空腔：整個網格（不設高度上限）跟外面不通的空格 —— 外板把 stern timber 之間最外那一格夾成小口袋（引擎 stats structure=1 同一個定義）"""
        from scipy import ndimage
        solid = s.keep | s.L1 | s.L2
        airp = np.pad(~solid, 1, constant_values=True)
        lab, _ = ndimage.label(airp)
        lab = lab[1:-1, 1:-1, 1:-1]
        s.CAV = ~solid & (lab != lab[0, 0, 0])

    def leak(s):
        solid = s.keep | s.L1 | s.L2
        air, out = s.outside(solid)
        inner = air & s.Sf
        return int(inner.sum()), np.argwhere(inner & out)

    # ───────── 塗裝 ─────────
    def paint(s):
        C = s.P['colors']
        on = s.L1 | s.L2
        s.on = on
        col = np.zeros(on.shape, np.int16)
        lwl = s.cx.ship.lwl(s.xb(s.xs))
        below = s.zb(s.zs)[None, :] <= lwl[:, None]               # (X, Z)
        Bw = np.broadcast_to(below[:, None, :], on.shape)
        col[on] = C['black']
        col[on & Bw] = C['bottom']
        # 結構塗裝：龍骨／柱／gripe／deadwood 露在船外的那一層
        _, out = s.outside(s.keep | on)
        st = s.keep & np.isin(s.colf, s.P['structure_colors'])
        s.SP = st & shift_or(out)
        col[s.SP] = C['black']
        col[s.SP & Bw] = C['bottom']
        s.SP_from = {int(k): int(v) for k, v in zip(*np.unique(s.colf[s.SP], return_counts=True))}
        s.C = col
        s.lwl = lwl

    def marks(s):
        """吃水刻度：船頭、船尾兩舷；數字 n 的底邊 ＝ 龍骨底起 n 公尺（真實 1 m ＝ 10 格 ⇒ Z 10n），3×5 白字。
        貼在那一格 (X, Z) 從外面看最外面那一格外板上；擺在 rabbet 線外 gap 格。"""
        M = s.P['draft_marks']
        C = s.P['colors']
        ship, cx = s.cx.ship, s.cx
        jc = NDY - 1
        s.mark_cells = []
        s.mark_place = []
        vis = s.on | s.SP                                          # 從外面看得到的那一層（船頭最低處是 deadwood／gripe，不是外板）
        for where in M['where']:
            for n in M['meters']:
                txt = str(n)
                w = 4 * len(txt) - 1
                Zb = 10 * n
                zmid = float(s.zb(Zb + 2))
                if where == 'stern':
                    Xa = int(np.ceil(cx.X0 + float(ship.rabbet_aft_x(zmid)) * cx.cpm)) + M['gap_cells']
                else:
                    Xa = int(np.floor(cx.X0 + float(ship.rabbet_x(zmid)) * cx.cpm)) - M['gap_cells'] - w + 1
                for side in M['sides']:
                    for k, ch in enumerate(txt):
                        g = GLYPH[ch]
                        for r in range(5):
                            for c in range(3):
                                if g[r][c] != '1':
                                    continue
                                cc = 4 * k + c                       # 從左讀起第幾欄
                                X = Xa + cc if side == 'S' else Xa + (w - 1 - cc)
                                Z = Zb + 4 - r
                                i = X - X0G
                                if side == 'S':
                                    js = np.where(vis[i, jc + 1:, Z])[0]
                                    assert len(js), ('刻度落空', where, n, side, X, Z)
                                    j = jc + 1 + js.max()
                                else:
                                    js = np.where(vis[i, :jc, Z])[0]
                                    assert len(js), ('刻度落空', where, n, side, X, Z)
                                    j = js.min()
                                s.C[i, j, Z] = C['marks']
                                s.mark_cells.append((X, j - jc + YC, Z))
                    s.mark_place.append({'where': where, 'n': n, 'side': side, 'X': [Xa, Xa + w - 1], 'Z': [Zb, Zb + 4]})

    # ───────── 清單 ─────────
    def cells(s, mask):
        w = np.argwhere(mask)
        return np.c_[w[:, 0] + X0G, w[:, 1] - (NDY - 1) + YC, w[:, 2], s.C[w[:, 0], w[:, 1], w[:, 2]]]

    def write_lists(s):
        out = os.path.join(s.design, 'masks', 'planking')
        os.makedirs(out, exist_ok=True)
        for f in os.listdir(out):
            if f.endswith('.vox.txt'):
                os.remove(os.path.join(out, f))
        lists = []

        def write(name, arr, note, overwrite):
            p = os.path.join(out, name + '.vox.txt')
            body = ''.join('%d,%d,%d,%d\n' % tuple(r) for r in arr)
            head = '# 夜燈號 %s（新圖紙 08 v1，draft_planking.py 產）—— %s；%d 格，stampvox at=0,0,0%s\n' % (
                name, note, len(arr), '，overwrite=1' if overwrite else '')
            open(p, 'w', encoding='utf-8', newline='\n').write(head + body)
            raw = open(p, 'rb').read()
            lists.append({'name': name, 'file': 'masks/planking/' + name + '.vox.txt', 'cells': int(len(arr)),
                          'overwrite': overwrite, 'sha256': hashlib.sha256(raw).hexdigest(),
                          'colors': {int(k): int(v) for k, v in zip(*np.unique(arr[:, 3], return_counts=True))} if len(arr) else {}})

        if s.D.any():
            write('dub', s.cells(s.D & (s.L1 | s.L2)), 'dubbing：凸出 molded 線的肋骨格換成外板', True)
        write('paint_struct', s.cells(s.SP), '龍骨／柱／gripe／deadwood 露在船外那一層上塗裝', True)
        if s.CAV.any():
            w = np.argwhere(s.CAV)
            write('fill_cavities', np.c_[w[:, 0] + X0G, w[:, 1] - (NDY - 1) + YC, w[:, 2], np.full(len(w), s.P['cavity_color'])],
                  '外板夾出來的封閉空腔填實', False)
        L1 = s.L1 & ~s.D
        seg = s.P['segments_x']
        for a, b in zip(seg[:-1], seg[1:]):
            m = L1.copy()
            m[:max(0, a - X0G)] = False
            m[b - X0G:] = False
            write('plank_x%03d_%03d' % (a, b - 1), s.cells(m), '外板 X %d..%d' % (a, b - 1), False)
        write('wales', s.cells(s.L2 & ~s.D), 'wale 帶外面那一格', False)
        n_all = sum(L['cells'] for L in lists if L['name'] not in ('paint_struct', 'fill_cavities')) - (int((s.D & (s.L1 | s.L2)).sum()) if s.D.any() else 0)
        assert n_all == int((s.L1 | s.L2).sum() - (s.D & (s.L1 | s.L2)).sum()), '分段漏了格'
        s.lists = lists
        return lists


def render_sheet(m, path):
    """新圖紙 08：右舷側面（船頭朝右，每一欄最外面那一格的顏色）＋ 吃水線／wale 帶 ＋ 船頭船尾刻度放大 ＋ 船中剖面。"""
    sc = 2
    jc = NDY - 1
    nx = len(m.xs)
    vis = m.on | m.SP
    side = np.full((NZ, nx, 3), 250, np.uint8)
    for i in range(nx):
        for z in range(NZ):
            js = np.where(vis[i, jc:, z])[0]
            if len(js):
                side[NZ - 1 - z, i] = rgb332(int(m.C[i, jc + js.max(), z]))
            elif m.keep[i, jc:, z].any():
                side[NZ - 1 - z, i] = (200, 185, 160)
    im = Image.fromarray(side).resize((nx * sc, NZ * sc), Image.NEAREST)
    d = ImageDraw.Draw(im)

    def P(X, Z):
        return ((X - X0G) * sc, (NZ - Z) * sc)
    Zk, cpm = m.cx.Zk, m.cx.cpm
    for arr, c in ((m.wale_bot, (30, 160, 60)), (m.wale_top, (30, 160, 60)), (m.lwl, (40, 90, 220))):
        pts = [P(X + 0.5, Zk + v * cpm) for X, v, h in zip(m.xs, arr, m.has) if h]
        d.line(pts, fill=c, width=1)
    d.text((8, 8), 'sheet 08 v1  planking / wale / paint / draft marks  (starboard, bow right;  green: wale band;  blue: LWL)', fill=(0, 0, 0))
    # 刻度放大（船尾、船頭；右舷）
    crops = []
    for where in ('stern', 'bow'):
        ps = [p for p in m.mark_place if p['where'] == where and p['side'] == 'S']
        xa = min(p['X'][0] for p in ps) - 12
        xb_ = max(p['X'][1] for p in ps) + 12
        za, zb_ = 0, max(p['Z'][1] for p in ps) + 8
        sub = side[NZ - 1 - zb_:NZ - za, xa - X0G:xb_ - X0G + 1]
        k = 6
        ci = Image.fromarray(sub).resize((sub.shape[1] * k, sub.shape[0] * k), Image.NEAREST)
        ImageDraw.Draw(ci).text((4, 4), where + ' marks (starboard)', fill=(200, 0, 0))
        crops.append(ci)
    # 船中剖面（船中站 x 18.919）
    Xm = int(round(m.cx.X0 + 18.919 * cpm))
    i = Xm - X0G
    sec = np.full((NZ, 2 * NDY - 1, 3), 250, np.uint8)
    for j in range(2 * NDY - 1):
        for z in range(NZ):
            if vis[i, j, z]:
                sec[NZ - 1 - z, j] = rgb332(int(m.C[i, j, z]))
            elif m.keep[i, j, z]:
                sec[NZ - 1 - z, j] = (200, 185, 160)
            elif m.Sf[i, j, z]:
                sec[NZ - 1 - z, j] = (235, 235, 245)
    s2 = 3
    secim = Image.fromarray(sec).resize(((2 * NDY - 1) * s2, NZ * s2), Image.NEAREST)
    ImageDraw.Draw(secim).text((6, 6), 'midship X %d' % Xm, fill=(0, 0, 0))
    h2 = max(secim.size[1], max(c.size[1] for c in crops))
    canvas = Image.new('RGB', (max(im.size[0], secim.size[0] + sum(c.size[0] + 20 for c in crops) + 20), im.size[1] + h2 + 20), (255, 255, 255))
    canvas.paste(im, (0, 0))
    canvas.paste(secim, (10, im.size[1] + 10))
    ox = secim.size[0] + 30
    for c in crops:
        canvas.paste(c, (ox, im.size[1] + 10))
        ox += c.size[0] + 20
    canvas.save(path)


def main():
    design = sys.argv[1]
    m = Model(design)
    ver = {'title': m.P['title'], 'world_cells': len(m.world)}
    if len(sys.argv) > 2:                                       # 開工前的作品 ＝ 清單？
        work = read_list(sys.argv[2])
        miss = sum(1 for k in m.world if k not in work)
        extra = sum(1 for k in work if k not in m.world)
        cdiff = sum(1 for k, c in m.world.items() if k in work and work[k] != c)
        ver['start_ledger'] = {'work_cells': len(work), 'missing': miss, 'extra': extra, 'color_diff': cdiff}
        assert miss == extra == cdiff == 0, ('作品不是階段六結束的樣子 ⇒ 不產', ver['start_ledger'])
    m.hull()
    m.world_arrays()
    m.shell()
    n_inner, leaks = m.leak()
    assert len(leaks) == 0, ('外板漏水 ⇒ 不產清單', len(leaks), leaks[:10].tolist())
    assert m.n_components == 1, ('外板補橋之後仍不是一塊', m.n_components)
    m.cavities()
    m.paint()
    m.marks()
    lists = m.write_lists()
    on = m.on
    jc = NDY - 1
    # 鏡像差：外板格的位置應該全對稱；顏色只有刻度不對稱
    onx = np.argwhere(on)
    pos_mis = int((on != on[:, ::-1, :]).sum())
    col_mis = int(((m.C != m.C[:, ::-1, :]) & (on | m.SP)).sum())
    mk = {(x, y, z) for (x, y, z) in m.mark_cells}
    mk_mir = {(x, 2 * YC - y, z) for (x, y, z) in mk}
    expect_col_mis = len(mk ^ mk_mir)
    # 船中最外一格外板（＋wale）的外緣 vs 半寬圖（另一張圖）的線
    Xm = int(round(m.cx.X0 + 18.919 * m.cx.cpm))
    i = Xm - X0G
    dyo = np.where(on[i, jc:, :].any(1))[0].max()
    dys = np.where(m.Sf[i, jc:, :].any(1))[0].max()
    dyl1 = np.where(m.L1[i, jc:, :].any(1))[0].max()
    hb_lines = m.cx.B['half_breadth_plan']['lines_at_midship_px5560']
    vals, cnts = np.unique(m.C[on], return_counts=True)
    ver.update({
        'S_cells_half': int(m.S.sum()),
        'dubbing_cells': int(m.D.sum()),
        'up_only_cells': int(m.up_only.sum()), 'up_only_where': [[int(a + X0G), int(b - jc + YC), int(c)] for a, b, c in np.argwhere(m.up_only)[:20]],
        'up_only_note': '只從下面接到 S 的外板格（S 往上長的）—— 內傾台階才會有；舷牆頂以上被高度上限擋掉',
        'bridges': [[c[0] + X0G, c[1] - jc + YC, c[2]] for c in m.bridges],
        'shell_cells': int(m.L1.sum()), 'wale_outer_cells': int(m.L2.sum()), 'total_cells': int(on.sum()),
        'cavity_cells': int(m.CAV.sum()), 'cavity_where': [[int(a + X0G), int(b - jc + YC), int(c)] for a, b, c in np.argwhere(m.CAV)[:20]],
        'struct_paint_cells': int(m.SP.sum()), 'struct_paint_from_colors': m.SP_from,
        'colors': {int(a): int(b) for a, b in zip(vals, cnts)},
        'marks': {'cells': len(m.mark_cells), 'placed': m.mark_place},
        'mirror': {'position_diff': pos_mis, 'color_diff': col_mis, 'color_diff_expected_from_marks': expect_col_mis},
        'components_with_existing': m.n_components,
        'leak_design': {'interior_air_cells': n_inner, 'leaking': int(len(leaks))},
        'midship_vs_half_breadth_plan': {
            'X': Xm, 'S_outer_face_m': round((dys + 0.5) / m.cx.cpm, 3), 'plank_outer_face_m': round((dyl1 + 0.5) / m.cx.cpm, 3),
            'wale_outer_face_m': round((dyo + 0.5) / m.cx.cpm, 3), 'half_breadth_plan_lines_m': hb_lines,
            'note': '底圖公尺；半寬圖是另一張圖（橫切面圖做的船殼拿它對，是獨立的一次）'},
        'bands_at': {str(X): {'wale_bot': round(float(m.wale_bot[X - X0G]), 2), 'wale_top': round(float(m.wale_top[X - X0G]), 2),
                              'lwl': round(float(m.lwl[X - X0G]), 2), 'top_Z': int(m.zt[X - X0G])}
                     for X in (120, 200, 333, 450, 560)},
        'lists': lists,
    })
    json.dump(ver, open(os.path.join(design, 'verify_planking.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1,
              default=lambda v: v.item())
    render_sheet(m, os.path.join(design, 'sheet08_planking_v1.png'))
    print(json.dumps({k: ver[k] for k in ('world_cells', 'start_ledger', 'dubbing_cells', 'up_only_cells', 'shell_cells', 'wale_outer_cells',
                                         'total_cells', 'cavity_cells', 'struct_paint_cells', 'colors', 'mirror', 'leak_design', 'midship_vs_half_breadth_plan') if k in ver},
                     ensure_ascii=False, default=lambda v: v.item()))
    print('bridges', len(m.bridges))
    for L in lists:
        print(L['name'], L['cells'], L['colors'])


if __name__ == '__main__':
    main()
