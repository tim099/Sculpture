# 新圖紙 05（TASK-0489）：外板與塗裝 —— plan.json 的 planking 段 ＋ 整艘的船殼表（draft_frames_ends.HullTable）＋ 作品現況（events 重播）
#   ⇒ 外板的 3D 格子清單（給 `sculpture op=stampvox`）、dubbing 清單（overwrite=1）、新圖紙 05、verify_planking.json。
# 用法：python -I draft_planking.py <design 資料夾>
#   · 船殼 S ＝ 格中心在 molded 線以內（|dy| < hb）、z 在 z_min..肋骨頂之間。肋骨頂每一欄 ＝ floor(top(X) − 0.5)，跟肋骨同一條線。
#   · 外板第一層 ＝ 不在 S、跟 S 共用一個面、而且現在是空的（或是要蓋掉的凸出肋骨格）——6 連通下把船內與船外隔開的最薄一層。
#   · wales 第二層 ＝ 往外再一格，只在舷側（往中線那一格是第一層）、wales 帶的高度內。
#   · 顏色：水線以下銅、砲門帶白、其餘黑（plan.json planking.paint）。
#   · 兩舷照中線鏡像（y ↔ 320 − y）；清單用絕對座標（at=0,0,0），中線那一格只寫一次。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import draft_frames_ends as DFE   # noqa: E402

YC = DFE.YC
IN = 0.254                     # 1 吋 ＝ 0.254 格（0.1 m／格）
X0, X1, NDY, NZ = 90, 690, 72, 145


def rgb332(i):
    return (round(((i >> 5) & 7) * 255 / 7), round(((i >> 2) & 7) * 255 / 7), round((i & 3) * 255 / 3))


def full(a):
    """只存 dy ≥ 0 的半舷陣列 → 整舷（第 1 軸 j ＝ dy + NDY − 1）。"""
    return np.concatenate([a[:, :0:-1, :], a], axis=1)


class Model:
    def __init__(s, design):
        s.design = design
        s.cx = DFE.Ctx(design)
        s.P = s.cx.plan['planking']
        # 外板是從「階段七第一刀之前」的作品算出來的 —— 讀現況的話，雕完再重跑會把剛鋪的外板當成船殼、再往外長一層
        #（2026-10-11 雕完重跑真的發生過，清單被覆寫成錯的；靠事件記的 sha256 才對回來）
        from replay import replay
        upto = s.P.get('world_upto')
        if upto:
            s.cx.world = {k: v[0] for k, v in replay(os.path.dirname(os.path.abspath(design)), upto=upto).items()}
        s.ports = json.load(open(os.path.join(design, s.P['port_lines']['source']), encoding='utf-8'))['ports_gun_deck']
        s.xs = np.arange(X0, X1)
        s.zs = np.arange(NZ)
        s.dys = np.arange(NDY)
        for (x, y, z) in s.cx.world:
            assert X0 <= x < X1 and abs(y - YC) < NDY and z < NZ, ('作品超出網格', x, y, z)

    # ───────── 線 ─────────
    def lines(s):
        Xc = np.array([(p['X_aft'] + p['X_fwd']) / 2 for p in s.ports])
        deg = s.P['port_lines']['fit_deg']
        s.c_sill = np.polyfit(Xc, [p['sill'] for p in s.ports], deg)
        s.c_lint = np.polyfit(Xc, [p['lintel'] for p in s.ports], deg)
        s.res_sill = [p['sill'] - np.polyval(s.c_sill, x) for p, x in zip(s.ports, Xc)]
        s.res_lint = [p['lintel'] - np.polyval(s.c_lint, x) for p, x in zip(s.ports, Xc)]
        X = s.xs + 0.5
        s.sill = np.polyval(s.c_sill, X)
        s.lintel = np.polyval(s.c_lint, X)
        W, B = s.P['wales'], s.P['black_strakes']
        s.bs_h = B['strakes'] * B['width_in'] * IN
        s.wale_h = W['strakes'] * W['width_in'] * IN
        s.wale_top = s.sill - s.bs_h
        s.wale_bot = s.wale_top - s.wale_h
        s.zt = np.floor(s.cx.top(X) - 0.5).astype(int)          # 肋骨頂（每一欄最上面那一格的 z）

    # ───────── 船殼 ─────────
    def hull(s):
        XX, ZZ = np.meshgrid(s.xs + 0.5, s.zs + 0.5, indexing='ij')
        H = s.cx.T.hb(XX, ZZ)
        H = np.where(ZZ <= s.cx.T.zg[-1], H, np.nan)
        s.xin = ~np.isnan(H).all(1)
        # 肋骨頂以下、表的 z 格點剛好是 nan 的（船殼上緣附近）⇒ 沿用正下方的值（船殼在頂上幾乎是直的）
        s.n_hold = 0
        for i in np.where(s.xin)[0]:
            last = np.nan
            for z in range(NZ):
                if np.isnan(H[i, z]):
                    if not np.isnan(last) and z <= s.zt[i] + 1:
                        H[i, z] = last
                        s.n_hold += 1
                else:
                    last = H[i, z]
        s.H = H
        zmin = s.P['z_min']
        band = (s.zs[None, :] >= zmin) & ((s.zs[None, :] <= s.zt[:, None]) | ~s.xin[:, None])
        s.S = (s.dys[None, :, None] < np.nan_to_num(H, nan=-1.0)[:, None, :]) & band[:, None, :]
        s.allowed = band

    def world(s):
        occ = np.zeros((len(s.xs), NDY, NZ), bool)
        col = np.zeros(occ.shape, np.int16)
        for (x, y, z), c in s.cx.world.items():
            d = y - YC
            if d >= 0:
                occ[x - X0, d, z] = True
                col[x - X0, d, z] = c
        s.occ, s.col = occ, col

    # ───────── 外板 ─────────
    def shell(s):
        S = s.S
        nan = np.isnan(s.H)[:, None, :]
        s.D = s.occ & (s.col == 141) & ~S & s.allowed[:, None, :] & ~nan          # 凸出 molded 線的肋骨格
        keep = s.occ & ~s.D
        Sf, Kf = full(S), full(keep)
        adj = np.zeros_like(Sf)
        adj[1:, :, :] |= Sf[:-1, :, :]
        adj[:-1, :, :] |= Sf[1:, :, :]
        adj[:, 1:, :] |= Sf[:, :-1, :]
        adj[:, :-1, :] |= Sf[:, 1:, :]
        adj[:, :, 1:] |= Sf[:, :, :-1]
        adj[:, :, :-1] |= Sf[:, :, 1:]
        A = np.broadcast_to(s.allowed[:, None, :], Sf.shape)
        L1 = adj & ~Sf & ~Kf & A
        # 舷側：往中線那一格在 S 裡（j 往中線 ＝ dy 絕對值減 1）
        jc = NDY - 1
        lat = np.zeros_like(L1)
        lat[:, jc + 1:, :] = L1[:, jc + 1:, :] & Sf[:, jc:-1, :]       # 右舷：j − 1 在 S
        lat[:, :jc, :] = L1[:, :jc, :] & Sf[:, 1:jc + 1, :]            # 左舷：j + 1 在 S
        # wales 第二層：舷側第一層的外面一格、wales 帶內
        zc = (s.zs + 0.5)[None, :]
        wband = (zc >= s.wale_bot[:, None]) & (zc <= s.wale_top[:, None])
        W = np.broadcast_to(wband[:, None, :], Sf.shape)
        L2 = np.zeros_like(L1)
        L2[:, jc + 2:, :] = lat[:, jc + 1:-1, :]
        L2[:, :jc - 1, :] |= lat[:, 1:jc, :]
        L2 &= W & ~Sf & ~Kf & ~L1 & A
        # 只靠邊（不共用面）接上的外板碎塊：⛔ 不能拿掉 —— 它們是擋水的那一格（第一版拿掉船頭舷頂 x 651 兩舷各 2 格，整個船艙就漏了）。
        # ⇒ 補一格「橋」：空的、在船殼外、同時跟碎塊和主體共用面的格，加進外板第一層。
        from scipy import ndimage
        s.bridges = []
        for _ in range(4):
            lab, n = ndimage.label(Kf | L1 | L2)
            main = np.bincount(lab[Kf]).argmax()
            frag = (L1 | L2) & (lab != main) & (lab > 0)
            if not frag.any():
                break
            mainm = lab == main
            nf = np.zeros_like(frag)
            nm = np.zeros_like(frag)
            for a, b in ((slice(1, None), slice(None, -1)), (slice(None, -1), slice(1, None))):
                for ax in range(3):
                    ia = [slice(None)] * 3
                    ib = [slice(None)] * 3
                    ia[ax], ib[ax] = a, b
                    nf[tuple(ia)] |= frag[tuple(ib)]
                    nm[tuple(ia)] |= mainm[tuple(ib)]
            br = nf & nm & ~Sf & ~Kf & ~L1 & ~L2 & A
            s.bridges += [tuple(int(v) for v in c) for c in np.argwhere(br)]
            L1 |= br
        lab, n = ndimage.label(Kf | L1 | L2)
        assert n == 1, ('外板補橋之後仍不是一塊', n)
        s.Sf, s.Kf, s.L1, s.L2, s.lat = Sf, Kf, L1, L2, lat

    def paint(s):
        Pn = s.P['paint']
        C = Pn['colors']
        zc = np.broadcast_to((s.zs + 0.5)[None, None, :], s.L1.shape)
        sill = s.sill[:, None, None]
        lint = s.lintel[:, None, None]
        col = np.zeros(s.L1.shape, np.int16)
        on = s.L1 | s.L2
        col[on] = C['black']
        xx = np.broadcast_to((s.xs + 0.5)[:, None, None], s.L1.shape)
        white = on & (xx >= Pn['stripe_x_aft']) & (zc >= sill - Pn['stripe_below_sill']) & (zc <= lint + Pn['stripe_above_lintel'])
        col[white] = C['white']
        col[on & (zc <= Pn['copper_top_z'])] = C['copper']
        s.C = col

    # ───────── 檢查（設計層面；雕完之後用 tools/struct_check_planking.py 從 events 重播再量一次） ─────────
    def outside_air(s, solid):
        """船外的空氣：肋骨頂以上當牆（只問「從舷側／船底通不通」，不問從甲板上方繞過去）。"""
        from scipy import ndimage
        zz = s.zs[None, None, :]
        top = np.where(s.xin, s.zt, NZ)[:, None, None]
        dom = np.broadcast_to(zz <= top, solid.shape)
        air = ~solid & dom
        airp = np.pad(air, 1, constant_values=True)
        lab, _ = ndimage.label(airp)
        lab = lab[1:-1, 1:-1, 1:-1]
        return air, lab == lab[0, 0, 0] if air[0, 0, 0] else np.zeros_like(air)

    def leak(s, remove=None):
        solid = s.Kf | s.L1 | s.L2
        if remove is not None:
            solid = solid & ~remove
        air, out = s.outside_air(solid)
        inner = air & s.Sf
        return int(inner.sum()), np.argwhere(inner & out)

    def struct_paint(s):
        """龍骨、護龍骨、gripe、艏柱、艉柱、deadwood 露在船外的那一層也上塗裝（實船水線以下連龍骨一起包銅）。"""
        Pn = s.P['paint']
        C = Pn['colors']
        colf = full(s.col)
        st = np.isin(colf, Pn['structure_colors']) & s.Kf
        _, out = s.outside_air(s.Kf | s.L1 | s.L2)
        nb = np.zeros_like(out)
        nb[1:] |= out[:-1]
        nb[:-1] |= out[1:]
        nb[:, 1:] |= out[:, :-1]
        nb[:, :-1] |= out[:, 1:]
        nb[:, :, 1:] |= out[:, :, :-1]
        nb[:, :, :-1] |= out[:, :, 1:]
        s.SP = st & nb
        zc = np.broadcast_to((s.zs + 0.5)[None, None, :], s.SP.shape)
        s.C[s.SP] = C['black']
        s.C[s.SP & (zc <= Pn['copper_top_z'])] = C['copper']
        s.SP_from = {int(k): int(v) for k, v in zip(*np.unique(colf[s.SP], return_counts=True))}

    # ───────── 清單 ─────────
    def cells(s, mask):
        w = np.argwhere(mask)
        x = w[:, 0] + X0
        y = w[:, 1] - (NDY - 1) + YC
        z = w[:, 2]
        c = s.C[w[:, 0], w[:, 1], w[:, 2]]
        return np.c_[x, y, z, c]

    def write_lists(s):
        out = os.path.join(s.design, 'masks', 'planking')
        os.makedirs(out, exist_ok=True)
        for f in os.listdir(out):
            if f.endswith('.vox.txt'):
                os.remove(os.path.join(out, f))
        Df = full(s.D)
        lists = []

        def write(name, arr, note, overwrite):
            p = os.path.join(out, name + '.vox.txt')
            body = '\n'.join('%d,%d,%d,%d' % tuple(r) for r in arr)
            head = '# %s —— %s（%d 格，at=0,0,0%s）\n' % (name, note, len(arr), '，overwrite=1' if overwrite else '')
            open(p, 'w', encoding='utf-8', newline='\n').write(head + body + '\n')
            raw = open(p, 'rb').read()
            lists.append({'name': name, 'file': 'masks/planking/' + name + '.vox.txt', 'cells': int(len(arr)),
                          'overwrite': overwrite, 'sha256': hashlib.sha256(raw).hexdigest(),
                          'colors': {int(k): int(v) for k, v in zip(*np.unique(arr[:, 3], return_counts=True))}})

        write('dub', s.cells(Df & (s.L1 | s.L2)), 'dubbing：凸出 molded 線的肋骨格換成外板', True)
        write('paint_struct', s.cells(s.SP), '龍骨／艏艉柱／deadwood／gripe 露在船外那一層上塗裝', True)
        rest = (s.L1 | s.L2) & ~Df
        seg = s.P['segments_x']
        for a, b in zip(seg[:-1], seg[1:]):
            m = rest.copy()
            m[:max(0, a - X0)] = False
            m[b - X0:] = False
            write('plank_x%03d_%03d' % (a, b - 1), s.cells(m), '外板 X %d..%d' % (a, b - 1), False)
        s.lists = lists
        return lists


def render_sheet(m, path):
    """新圖紙 05：側面（從右舷看，船頭朝右）每一欄最外面那一格的顏色 ＋ 砲門框（原圖讀數）＋ 線；下方船中剖面。"""
    sc = 3
    on = m.L1 | m.L2
    jc = NDY - 1
    nx = len(m.xs)
    side = np.full((NZ, nx, 3), 250, np.uint8)
    # 右舷（dy > 0）由外往內找第一格
    for i in range(nx):
        for z in range(NZ):
            js = np.where((on | m.SP)[i, jc:, z])[0]
            if len(js):
                side[NZ - 1 - z, i] = rgb332(int(m.C[i, jc + js.max(), z]))
            elif m.Kf[i, jc:, z].any():
                side[NZ - 1 - z, i] = (200, 185, 160)
    im = Image.fromarray(side).resize((nx * sc, NZ * sc), Image.NEAREST)
    d = ImageDraw.Draw(im)

    def P(X, Z):
        return ((X - X0) * sc, (NZ - Z) * sc)
    for p in m.ports:
        d.rectangle([P(p['X_aft'], p['lintel']), P(p['X_fwd'], p['sill'])], outline=(220, 30, 30), width=2)
    for arr, c in ((m.sill, (220, 30, 30)), (m.lintel, (220, 30, 30)), (m.wale_top, (30, 160, 60)), (m.wale_bot, (30, 160, 60))):
        pts = [P(x + 0.5, v) for x, v in zip(m.xs, arr) if m.xin[x - X0]]
        d.line(pts, fill=c, width=1)
    d.line([P(X0, 62.86), P(X1, 62.86)], fill=(40, 90, 220), width=1)
    d.text((8, 8), 'sheet 05 v1  planking & paint  (red: gun deck ports from drawing 11 / sill & lintel fits;  green: main wales band;  blue: LWL Z 62.86)', fill=(0, 0, 0))
    # 船中剖面（X 449）放大
    i = 449 - X0
    sec = np.full((NZ, 2 * NDY - 1, 3), 250, np.uint8)
    for j in range(2 * NDY - 1):
        for z in range(NZ):
            if on[i, j, z] or m.SP[i, j, z]:
                sec[NZ - 1 - z, j] = rgb332(int(m.C[i, j, z]))
            elif m.Kf[i, j, z]:
                sec[NZ - 1 - z, j] = (200, 185, 160)
    s2 = 4
    secim = Image.fromarray(sec).resize(((2 * NDY - 1) * s2, NZ * s2), Image.NEAREST)
    dd = ImageDraw.Draw(secim)
    dd.text((6, 6), 'midship X 449', fill=(0, 0, 0))
    canvas = Image.new('RGB', (im.size[0], im.size[1] + secim.size[1] + 10), (255, 255, 255))
    canvas.paste(im, (0, 0))
    canvas.paste(secim, (20, im.size[1] + 10))
    canvas.save(path)


def main():
    design = sys.argv[1]
    m = Model(design)
    m.lines()
    m.hull()
    m.world()
    m.shell()
    m.paint()
    n_inner, leaks = m.leak()
    assert len(leaks) == 0, ('外板漏水 ⇒ 不產清單（船外空氣的判斷也會錯，結構塗裝會塗到船艙裡）', len(leaks))
    m.struct_paint()
    lists = m.write_lists()
    on = m.L1 | m.L2
    vals, cnts = np.unique(m.C[on], return_counts=True)
    v = {
        'title': m.P['title'], 'task': m.P['task'],
        'hull_hold_cells': m.n_hold,
        'dubbing_cells_half': int(m.D.sum()),
        'dubbing_max_beyond_hb': float(np.nanmax((m.dys[None, :, None] - m.H[:, None, :])[m.D])),
        'bridges': [[c[0] + X0, c[1] - (NDY - 1) + YC, c[2]] for c in m.bridges],
        'shell_cells': int(m.L1.sum()), 'wale_outer_cells': int(m.L2.sum()), 'total_cells': int(on.sum()),
        'struct_paint_cells': int(m.SP.sum()), 'struct_paint_from_colors': m.SP_from,
        'colors': {int(a): int(b) for a, b in zip(vals, cnts)},
        'port_fit': {'sill_coef': m.c_sill.tolist(), 'lintel_coef': m.c_lint.tolist(),
                     'sill_res_max': float(np.max(np.abs(m.res_sill))), 'lintel_res_max': float(np.max(np.abs(m.res_lint)))},
        'bands_at': {str(X): {'wale_bot': round(float(m.wale_bot[X - X0]), 2), 'wale_top': round(float(m.wale_top[X - X0]), 2),
                              'sill': round(float(m.sill[X - X0]), 2), 'lintel': round(float(m.lintel[X - X0]), 2), 'top': int(m.zt[X - X0])}
                     for X in (130, 190, 300, 449, 560, 620, 660)},
        'leak_design': {'interior_air_cells': n_inner, 'leaking': int(len(leaks)),
                        'where': leaks[:20].tolist()},
        'lists': lists,
    }
    json.dump(v, open(os.path.join(design, 'verify_planking.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    render_sheet(m, os.path.join(design, 'sheet05_planking_v1.png'))
    print(json.dumps({k: v[k] for k in ('dubbing_cells_half', 'dubbing_max_beyond_hb', 'shell_cells', 'wale_outer_cells', 'total_cells', 'colors', 'leak_design')}, ensure_ascii=False))
    for L in lists:
        print(L['name'], L['cells'], L['colors'])


if __name__ == '__main__':
    main()
