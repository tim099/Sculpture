# 新圖紙 10 船殼內部 v1（階段九，TASK-0538）：plan.json interior ＋ readings_LI_decks.json ＋ 階段一～八的清單 ＋ 船殼表（draft_planking.Model）
#   ⇒ masks/interior/{ceiling,bands,cap,fill_cavities}.vox.txt（stampvox at=0,0,0）、recolor.vox.txt（overwrite=1）、
#     decks.json（三層甲板每一個 X 的甲板面）、verify_interior.json、sheet10_interior_v1.png
# 用法：python -I draft_interior.py <design 資料夾> [作品 export list 檔]
#   · 開工前的作品 ＝ 階段一～七的清單 ＋ 階段八的刻與補；給了 export list 就先逐格對一次，對不上不產。
#   · 甲板面 D(X) ＝ 走的那一格（甲板板在 D−1、橫樑在它底下 beam 格、clamp 再底下 clamp 格）：上甲板照讀數三次擬合；下甲板、走道那一層照上甲板平行（plan provenance）。
#   · 艙內空氣 ＝ 船殼 S 裡的空格、跟種子 6 連通的那一塊；肋骨之間 1 格寬的縫（沿 X 兩邊都是實心）當成實心看，
#     再做有深度上限的閉合（離 S 外緣 ≤ 4.5 格、6 鄰居 ≥ 4 格實心 ⇒ 當實心，重複到不變）—— 照憲法號階段九。
#   · 內板 ＝ 艙內空氣裡、6 鄰居碰到船殼實心（中線結構 |dy| ≤ 2 不算）的那一層；砲門開口那幾列（兩舷、所有 dy）不鋪。
#   · bands（clamps／spirketting）＝ 內板再往內一格（沿法向＋同層斜接補一次），Z 範圍照甲板。
#   · 牆裡填實：肋骨那一層裡當成實心看的空格（縫）補 141；最後整個網格的封閉空腔補實（141）。
#   · 中線結構露在艙內那一層換色（keelson 209→136、apron／內艉柱 173→104）。
import sys, os, json, glob, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402
import draft_ports as DPO        # noqa: E402

X0, NDY, NZ, YC = DP.X0G, DP.NDY, DP.NZ, DP.YC
X1 = DP.X1G
Y0 = YC - NDY + 1
SX, SY = X1 - X0, 2 * NDY - 1
PAINT = (36, 100, 255)


def shift(a, ax, k):
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


class Interior:
    def __init__(s, design):
        s.design = design
        po = DPO.Ports(design)                       # 階段一～七（照落子順序）＋木料標籤
        s.plan = po.cx.plan
        s.P = s.plan['interior']
        s.cx = po.cx
        world = dict(po.world)
        for c in DP.read_list(os.path.join(design, 'masks', 'ports', 'carve.vox.txt')):
            del world[c]
        world.update(DP.read_list(os.path.join(design, 'masks', 'ports', 'lining.vox.txt')))
        s.world = world
        G = np.zeros((SX, SY, NZ), np.uint8)
        for (x, y, z), c in world.items():
            G[x - X0, y - Y0, z] = c
        s.G = G
        plank = np.zeros(G.shape, bool)
        for (x, y, z), k in po.lab.items():
            if k in ('plank', 'wale') and (x, y, z) in world:
                plank[x - X0, y - Y0, z] = True
        s.plank = plank
        M = DP.Model(design)
        M.hull()
        s.M = M
        s.S = DP.full(M.S)
        s.zt = M.zt
        s.xs = np.arange(X0, X1)
        iy = np.arange(SY)
        s.dy = np.abs(iy - (YC - Y0))
        s.side = np.sign(iy - (YC - Y0))
        s.vp = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))

    # ───────── 甲板面 ─────────
    def decks(s):
        R = json.load(open(os.path.join(s.design, s.P['source']), encoding='utf-8'))['lines']
        D = s.P['decks']
        up = np.array(R[D['upper']['fit']], float)
        s.fit = np.polyfit(up[:, 0], up[:, 1], D['upper']['poly_deg'])
        s.fit_rms = float(np.sqrt(np.mean((np.polyval(s.fit, up[:, 0]) - up[:, 1]) ** 2)))
        s.fit_range = [float(up[:, 0].min()), float(up[:, 0].max())]
        xb = (s.xs + 0.5 - s.cx.X0) / s.cx.cpm
        zu = np.polyval(s.fit, np.clip(xb, s.fit_range[0], s.fit_range[1]))        # 範圍外照端點（兩頭平）
        s.Dz = {}
        for name, d in D.items():
            z = zu + (d.get('offset_m', 0.0) if d.get('from') else 0.0)
            s.Dz[name] = np.rint(s.cx.Zk + z * s.cx.cpm).astype(int)

    # ───────── 艙內空氣與內板 ─────────
    def ceiling(s):
        G, S = s.G, s.S
        SOL = G > 0
        air = ~SOL & S
        lab, _ = ndimage.label(air)
        sd = s.P['seed']
        k = lab[sd[0] - X0, sd[1] - Y0, sd[2]]
        assert k > 0, '種子不是艙內空氣'
        IA = lab == k
        GAP = IA & shift(SOL, 0, 1) & shift(SOL, 0, -1)
        PORTXZ = np.zeros((SX, NZ), bool)
        for p in s.vp['ports']:
            PORTXZ[p['X'][0] - X0:p['X'][1] - X0 + 1, p['Z'][0]:p['Z'][1] + 1] = True
        s.PORTXZ = PORTXZ
        s.PORT3 = np.broadcast_to(PORTXZ[:, None, :], SOL.shape)
        SOLc = SOL | GAP
        # 肋骨之間的縫（這艘的肋骨 4 格寬、間距 9.08 ⇒ 縫 5 格寬，不是憲法號那種 1 格）：肋骨那一層（離 S 外緣 ≤ moulded(z) 格）的艙內空氣先當成實心 ——
        # 不然內板會鋪進縫裡、貼著外板，艙內看起來一條條 3 格深的溝（v1 第一版量到：X 336 Z 60 內板在 y 224，肋骨上在 221）
        # 距離只量到船殼的牆（兩舷、船底、船頭船尾），⛔ 不量到頂上的開口：S 的頂那一列往上延伸再量
        # （v1 第二版直接量 S ⇒ 頂上 3 格整片當成肋骨那一層，封口變成一整塊蓋子、1,985 個元件）
        S2 = S.copy()
        for ix in range(SX):
            t = int(s.zt[ix])
            if t < NZ - 1:
                S2[ix, :, t + 1:] = S[ix, :, t][:, None]
        edt = ndimage.distance_transform_edt(S2)
        zb = (np.arange(NZ) + 0.5 - s.cx.Zk) / s.cx.cpm
        mc = np.zeros((SX, NZ))
        for ix in range(SX):
            ztop = float(s.cx.ship.top(float((ix + X0 + 0.5 - s.cx.X0) / s.cx.cpm)))
            mc[ix] = [s.cx.mould(float(z), ztop) * s.cx.cpm for z in zb]
        FB = IA & (edt <= mc[:, None, :]) & ~s.PORT3
        s.frame_gap_cells = int((FB & ~SOLc).sum())
        SOLc |= FB
        shallow = edt <= 4.5
        s.closed = 0
        while True:
            n = np.zeros(SOL.shape, np.uint8)
            for ax in range(3):
                for kk in (1, -1):
                    n += shift(SOLc, ax, kk)
            add = IA & ~SOLc & shallow & ~s.PORT3 & (n >= 4)
            if not add.any():
                break
            SOLc |= add
            s.closed += int(add.sum())
        s.IA1 = IA & ~SOLc
        CLS = SOL & (s.dy[None, :, None] <= 2) & ~s.plank & ~np.isin(G, PAINT)
        s.CLS = CLS
        s.HS = SOLc & ~CLS
        s.SOLc = SOLc
        s.SKIN = s.IA1 & nb6(s.HS) & ~s.PORT3
        s.gap_cells = int(GAP.sum())
        # 牆裡填實：當成實心看的那些空格（肋骨之間的縫、1 格縫、閉合補的）真的補 141 —— 內板後面一定是木頭，舷頂也就封住了
        # （v1 第三版只封頂那一列、其他靠「封閉空腔補實」：在舷弧台階處縫跟船外相通、沒被補，內板在船尾艙裡浮了 1,899 格、959 個元件）
        s.CAP = (SOLc & ~SOL) & ~s.PORT3
        s.free = s.IA1 & ~s.SKIN & ~s.PORT3

    # ───────── clamps／spirketting ─────────
    def bands(s):
        D = s.P['decks']
        mask = np.zeros((SX, NZ), bool)
        s.band_rows = []
        ports = [{'xa': p['X'][0], 'xb': p['X'][1], 'sill': p['Z'][0]} for p in s.vp['ports']]
        for name, d in D.items():
            Dz = s.Dz[name]
            for ix in range(SX):
                S_ = int(Dz[ix])
                top = S_ - d['plank'] - d['beam'] - 1
                mask[ix, top - d['clamp'] + 1: top + 1] = True
                s.band_rows.append((name, 'clamp', ix + X0, top - d['clamp'] + 1, top))
                sp = d.get('spirketting')
                if sp == 'sill':
                    x = ix + X0
                    near = [p for p in ports if p['xa'] - 1 <= x <= p['xb'] + 1]
                    # 砲門底下（開口 ±1）到它的下緣 − 1；砲門之間到最近的兩個砲門下緣較低那個 − 1
                    if near:
                        sp_top = min(p['sill'] for p in near) - 1
                    else:
                        left = [p for p in ports if p['xb'] < x]
                        right = [p for p in ports if p['xa'] > x]
                        cand = ([left[-1]['sill']] if left else []) + ([right[0]['sill']] if right else [])
                        sp_top = min(cand) - 1
                    if sp_top >= S_:
                        mask[ix, S_: sp_top + 1] = True
                        s.band_rows.append((name, 'spirketting', x, S_, sp_top))
                elif sp:
                    mask[ix, S_: S_ + sp] = True
                    s.band_rows.append((name, 'spirketting', ix + X0, S_, S_ + sp - 1))
        rows = s.free & mask[:, None, :]
        B = rows & nb6(s.SKIN)
        nbx = shift(B, 0, 1) | shift(B, 0, -1)
        nby = shift(B, 1, 1) | shift(B, 1, -1)
        s.BAND = B | (rows & nbx & nby)

    # ───────── 合起來、換色、補空腔、讀數 ─────────
    def finish(s):
        C = s.P['colors']
        parts = [('ceiling', s.SKIN, C['ceiling']), ('bands', s.BAND, C['bands']), ('wall_fill', s.CAP, C['cap'])]
        tot = np.zeros(s.G.shape, bool)
        for _, m, _c in parts:
            assert not (tot & m).any(), '清單之間有重疊'
            assert not (s.G[m] > 0).any(), '落在實心的格上'
            tot |= m
        new = s.G.copy()
        for _, m, c in parts:
            new[m] = c
        # 封閉空腔（整個網格；引擎 stats structure=1 同一個定義）補實
        pad = np.pad(new > 0, 1)
        lab, _ = ndimage.label(~pad)
        cav = ((lab != lab[0, 0, 0]) & ~pad)[1:-1, 1:-1, 1:-1]
        s.CAV = cav
        new[cav] = C['cavity']
        parts.append(('fill_cavities', cav, C['cavity']))
        # 中線結構露在艙內那一層換色：跟艙內空氣共面、不跟船殼 S 外的空氣共面
        mapping = {v[0]: v[1] for v in s.P['centreline_recolor'].values()}
        air = new == 0
        lab2, _ = ndimage.label(air & s.S)
        sd = s.P['seed']
        ia_new = lab2 == lab2[sd[0] - X0, sd[1] - Y0, sd[2]]
        s.REC = s.CLS & np.isin(s.G, list(mapping)) & nb6(ia_new) & ~nb6(air & ~s.S)
        s.rec_col = np.zeros_like(s.G)
        for a, b in mapping.items():
            s.rec_col[s.REC & (s.G == a)] = b
        new[s.REC] = s.rec_col[s.REC]
        s.recolor_by = {'%d→%d' % (a, b): int((s.REC & (s.G == a)).sum()) for a, b in mapping.items()}
        s.parts = parts
        s.new = new
        # 讀數
        def paint_faces(g):
            a = (g == 0) & s.S
            lb, _ = ndimage.label(a)
            ia = lb == lb[sd[0] - X0, sd[1] - Y0, sd[2]]
            paint = (s.plank & (g > 0)) | np.isin(g, PAINT)
            n = n_port = 0
            for ax in range(3):
                for kk in (1, -1):
                    f = ia & shift(paint, ax, kk)
                    n += int((f & ~s.PORT3).sum())
                    n_port += int((f & s.PORT3).sum())
            return n, n_port
        s.paint_before = paint_faces(s.G)
        s.paint_after = paint_faces(new)
        s.port_hits = int((s.PORT3 & (new > 0) & ~(s.G > 0)).sum())
        _, s.components = ndimage.label(new > 0)
        pad = np.pad(new > 0, 1)
        lab3, _ = ndimage.label(~pad)
        s.cav_after = int(((lab3 != lab3[0, 0, 0]) & ~pad).sum())
        s.mirror = int(sum((m != m[:, ::-1, :]).sum() for _, m, _c in parts) + (s.REC != s.REC[:, ::-1, :]).sum())
        # 每個砲門下緣離上甲板幾格
        s.sill_above_deck = [{'n': p['n'], 'sill': p['Z'][0],
                              'deck': int(s.Dz['upper'][(p['X'][0] + p['X'][1]) // 2 - X0]),
                              'above': p['Z'][0] - int(s.Dz['upper'][(p['X'][0] + p['X'][1]) // 2 - X0])} for p in s.vp['ports']]

    def write(s):
        out = os.path.join(s.design, 'masks', 'interior')
        os.makedirs(out, exist_ok=True)
        for f in glob.glob(os.path.join(out, '*')):
            os.remove(f)
        notes = {'ceiling': '內板（ceiling，1 格）', 'bands': 'clamps（每層橫樑底下）／spirketting（上甲板到砲門下緣）',
                 'wall_fill': '牆裡填實（肋骨之間的縫：肋骨那一層裡當成實心看的空格）', 'fill_cavities': '封閉空腔補實'}
        s.files = {}
        for name, m, c in s.parts:
            idx = np.argwhere(m)
            p = os.path.join(out, name + '.vox.txt')
            body = ''.join('%d,%d,%d,%d\n' % (i + X0, j + Y0, k, c) for i, j, k in idx)
            open(p, 'w', encoding='utf-8', newline='\n').write('# 夜燈號 %s —— %s（新圖紙 10 v1，draft_interior.py 產；%d 格，stampvox at=0,0,0）\n' % (name, notes[name], len(idx)) + body)
            s.files[name] = {'cells': int(len(idx)), 'color': int(c), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        idx = np.argwhere(s.REC)
        p = os.path.join(out, 'recolor.vox.txt')
        body = ''.join('%d,%d,%d,%d\n' % (i + X0, j + Y0, k, s.rec_col[i, j, k]) for i, j, k in idx)
        open(p, 'w', encoding='utf-8', newline='\n').write('# 夜燈號 recolor —— 中線結構露在艙內那一層換色（%s；%d 格，stampvox at=0,0,0 overwrite=1）\n' % ('、'.join('%s %d' % kv for kv in s.recolor_by.items()), len(idx)) + body)
        s.files['recolor'] = {'cells': int(len(idx)), 'overwrite': True, 'by': s.recolor_by, 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        json.dump({'note': '甲板面 ＝ 走的那一格（甲板板在 D−1）；新圖紙 10 v1', 'X0': X0,
                   'decks': {k: [int(v) for v in arr] for k, arr in s.Dz.items()}},
                  open(os.path.join(s.design, 'decks.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False)


def render_sheet(I, path):
    """新圖紙 10：上 ＝ 右舷內側立面（甲板面三條、clamps 深、spirketting 淺、砲門藍）；下 ＝ 船中 X 340 剖面。"""
    sc = 2
    xa, xb, za, zb = 40, 700, 0, 200
    W, H = (xb - xa) * sc, (zb - za) * sc
    top = Image.new('RGB', (W, H + 30), (250, 250, 247))
    d = ImageDraw.Draw(top)

    def P(x, z):
        return ((x - xa) * sc, (zb - z) * sc + 24)
    occ = (I.G[:, YC - Y0:, :] > 0).any(1)
    for ix in range(SX):
        zz = np.where(occ[ix])[0]
        if len(zz):
            d.line([P(ix + X0, zz.min()), P(ix + X0, zz.max())], fill=(225, 220, 210))
    for p in I.vp['ports']:
        d.rectangle([P(p['X'][0], p['Z'][1] + 1), P(p['X'][1] + 1, p['Z'][0])], outline=(30, 80, 220))
    col = {'clamp': (150, 110, 80), 'spirketting': (205, 170, 120)}
    for name, kind, x, z0, z1 in I.band_rows:
        if occ[x - X0].any() and I.SKIN[x - X0].any():
            d.rectangle([P(x, z1 + 1), P(x + 1, z0)], fill=col[kind])
    deckcol = {'lower': (40, 120, 200), 'upper': (200, 60, 50), 'spar': (110, 60, 160)}
    for name, Dz in I.Dz.items():
        d.line([P(ix + X0, int(Dz[ix])) for ix in range(SX)], fill=deckcol[name], width=1)
        d.text(P(330, int(Dz[330 - X0]) + 6), name, fill=deckcol[name])
    d.text((8, 4), 'sheet 10 v1  hull interior (starboard inboard): deck walk levels (lines), clamps (dark) & spirketting (light), gun ports (blue)', fill=(0, 0, 0))
    ix = 340 - X0
    sl = np.zeros((SY, NZ, 3), np.uint8) + 250
    sl[I.G[ix] > 0] = (205, 195, 180)
    for name, m, c in I.parts:
        sl[m[ix]] = DP.rgb332(c)
    for name, Dz in I.Dz.items():
        sl[:, int(Dz[ix]) - 1][~(I.new[ix, :, int(Dz[ix]) - 1] > 0) & I.S[ix, :, int(Dz[ix]) - 1]] = deckcol[name]
    sec = Image.fromarray(np.transpose(sl, (1, 0, 2))[::-1]).resize((SY * 3, NZ * 3), Image.NEAREST)
    canvas = Image.new('RGB', (max(W, SY * 3 + 400), H + 30 + NZ * 3 + 20), (250, 250, 247))
    canvas.paste(top, (0, 0))
    canvas.paste(sec, (0, H + 40))
    ImageDraw.Draw(canvas).text((SY * 3 + 10, H + 50), 'midship section X 340 (looking forward): coloured lines = where each deck plank will go (deck itself is the next stage)', fill=(0, 0, 0))
    canvas.save(path)


def main():
    design = sys.argv[1]
    I = Interior(design)
    v = {'title': I.P['title'], 'world_voxels': len(I.world)}
    if len(sys.argv) > 2:
        work = DP.read_list(sys.argv[2])
        miss = sum(1 for k in I.world if k not in work)
        extra = sum(1 for k in work if k not in I.world)
        cdiff = sum(1 for k, c in I.world.items() if k in work and work[k] != c)
        v['start_ledger'] = {'work_cells': len(work), 'missing': miss, 'extra': extra, 'color_diff': cdiff}
        assert miss == extra == cdiff == 0, ('作品不是階段八結束的樣子 ⇒ 不產', v['start_ledger'])
    I.decks()
    I.ceiling()
    I.bands()
    I.finish()
    I.write()
    new_cells = sum(f['cells'] for k, f in I.files.items() if k != 'recolor')
    mid = 340 - X0
    v.update({'upper_fit': {'coef': [float(c) for c in I.fit], 'rms_m': round(I.fit_rms, 4), 'x_range': I.fit_range},
              'deck_walk_Z_at': {str(X): {k: int(a[X - X0]) for k, a in I.Dz.items()} for X in (100, 150, 200, 260, 340, 420, 500, 560, 620)},
              'gap_cells_x': I.gap_cells, 'frame_gap_cells': I.frame_gap_cells, 'closed_cells_depth_bounded': I.closed, 'files': I.files, 'total_new': new_cells,
              'expect_after': len(I.world) + new_cells, 'recolor': I.recolor_by,
              'visible_paint_faces': {'before': I.paint_before[0], 'after': I.paint_after[0],
                                      'in_port_rows_before': I.paint_before[1], 'in_port_rows_after': I.paint_after[1]},
              'port_cells_hit': I.port_hits, 'components_after': int(I.components), 'cavities_after': I.cav_after,
              'mirror_mismatch': I.mirror, 'sill_above_upper_deck': I.sill_above_deck,
              'midship_X340': {k: int(a[mid]) for k, a in I.Dz.items()}})
    json.dump(v, open(os.path.join(design, 'verify_interior.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(I, os.path.join(design, 'sheet10_interior_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('sill_above_upper_deck',)}, ensure_ascii=False))
    print('sill-deck', [(p['n'], p['above']) for p in I.sill_above_deck])


if __name__ == '__main__':
    main()
