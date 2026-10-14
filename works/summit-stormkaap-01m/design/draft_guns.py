# 階段十二：砲 —— 三種砲各一件子作品（0.05 m／格）＋ 42 門外部模型的擺放（退到零碰撞）
# 設計 plan.json guns（出處在 provenance guns.*）；砲門：verify_decks.json ports（舷側兩排）、verify_stern.json ports（船尾）、verify_head.json chase_ports（船頭大嘴）。
# 從夜隼號 draft_guns.py（階段十三）改：外形照 plan guns.base（夜隼號 4 磅）× 每種的倍數（sl 管長、sr 半徑、sh 砲架高、sw 砲架寬）；三管砲三根倒三角＋鐵箍。
# 子作品座標（同憲法號 -gun-24／long18 的慣例）：x ＝ 砲的寬（軸在 AX 那一格的格心）、y ＝ 砲身方向（砲口 +y）、z 0 ＝ 甲板面上第一層。
# 擺法（Shipbuilding §4.2）：現況 ＝ 引擎匯出的組裝件格子（exports/stage11/ship_list.txt）＋ 模型外框（parts.json）。
#   橫向對準砲門中線（再試 ±0.5…±1.5），沿砲口方向從牆外往裡退（每步 0.5 格），退到模型每一格的格心＋八個角都不在實心裡 ⇒ 推得最出去的位置；
#   排序：四輪著地 ＞ 砲口伸出牆外 ≥ min_muzzle_out ＞ 置中 ＞ 推得出去。S 照原樣（砲口 +y）、P mirror=y；船尾 rotate z 90（砲口 −x）、船頭 rotate z −90（砲口 +x）。
#   pivot ＝ 砲架前緣中間、甲板面那一層；模型 world ＝ at ＋ R(scale × mirror(Q − pivot))。
# 輸出：masks/guns/<型>.vox.txt（stampvox，at 0,0,0）、verify_guns.json。重跑逐位元組相同。
# 用法：python -I -X utf8 -B draft_guns.py <design 資料夾> <匯出資料夾（ship_list.txt、parts.json）>
import sys, os, json, math, hashlib
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); EX = os.path.abspath(sys.argv[2])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
G = plan['guns']; B = G['base']; COL = G['colors']; YC = plan['frame']['YC']


class Part:
    def __init__(s, W, L, H):
        s.cells = {}; s.W, s.L, s.H = W, L, H

    def put(s, x, y, z, c, over=False):
        if not (0 <= x < s.W and 0 <= y < s.L and 0 <= z < s.H):
            raise ValueError(('框外', x, y, z))
        if (x, y, z) in s.cells and not over:
            return
        s.cells[(x, y, z)] = c

    def box(s, x0, x1, y0, y1, z0, z1, c, over=False):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    s.put(x, y, z, c, over)

    def tube(s, cx, cz, y0, prof, c, bore_r=0.0, bore_depth=0.0, over=False):
        """沿 y 的旋轉體：軸在 (cx, cz) 那一格的格心；prof ＝ [(s, r), …] 分段；格心落在半徑內就放；砲口那一段挖空。"""
        smax = prof[-1][0]
        for y in range(s.L):
            t = y + 0.5 - y0
            if not (0 <= t < smax):
                continue
            r = None
            for (a, ra), (b, rb) in zip(prof, prof[1:]):
                if a <= t < b:
                    r = ra + (rb - ra) * (t - a) / (b - a) if b > a else rb
                    break
            if r is None:
                continue
            R = int(math.ceil(r)) + 1
            for dx in range(-R, R + 1):
                for dz in range(-R, R + 1):
                    d = math.hypot(dx, dz)
                    if d <= r + 1e-9:
                        if bore_r > 0 and t > smax - bore_depth and d <= bore_r:
                            s.cells.pop((cx + dx, y, cz + dz), None)
                            continue
                        s.put(cx + dx, y, cz + dz, c, over)

    def wheel(s, cx, cy, cz, r, c):
        for y in range(s.L):
            for z in range(s.H):
                if math.hypot(y + 0.5 - cy, z + 0.5 - cz) <= r:
                    s.put(cx, y, z, c, True)


def build(key):
    T = G['types'][key]; sl, sr, sh, sw = T['sl'], T['sr'], T['sh'], T['sw']; Cb = B['carriage']
    rl = lambda v: int(round(v * sl)); rh = lambda v: int(round(v * sh)); rw = lambda v: int(round(v * sw))
    prof = [(round(a * sl, 3), round(r * sr, 3)) for a, r in B['profile']]
    blen = prof[-1][0]
    barrels = T.get('barrels', [[0, 0]])
    k0, k1 = rw(Cb['cheek_x'][0]), rw(Cb['cheek_x'][1])
    AX = k1 + 2; AZ = T['AZ']
    cl = rl(2) if rl(2) >= 2 else 2
    YB = 2 * cl + 1
    rmax = max(r for _, r in prof)
    ext = max(abs(dz) for _, dz in barrels)
    W, L, H = 2 * AX + 1, YB + int(math.ceil(blen)) + 1, AZ + int(math.ceil(ext + rmax)) + 2
    P = Part(W, L, H)
    for dx, dz in barrels:
        assert abs(dx) + rmax < k0, ('砲管碰到 cheek', key, dx)
        P.tube(AX + dx, AZ + dz, YB, prof, COL['barrel'], T['bore_r'], B['bore_depth'] * sl)
        P.tube(AX + dx, AZ + dz, YB - cl, [(0, 1.0 * sr), (cl, 1.0 * sr)], COL['barrel'])            # cascabel 頸
        P.tube(AX + dx, AZ + dz, YB - 2 * cl, [(0, 1.5 * sr), (cl, 1.5 * sr)], COL['barrel'])        # cascabel 鈕
    if len(barrels) > 1:                                                     # 鐵箍：離任一根砲管軸 ≤ 那裡的半徑＋0.8 的格（挖空的砲口不碰）
        for b in T['bands_at']:
            y = YB + rl(b)
            t = y + 0.5 - YB
            r = [rr for (a, rr), (bb, _) in zip(prof, prof[1:]) if a <= t < bb][0] + 0.8
            for x in range(W):
                for z in range(H):
                    if any(math.hypot(x - AX - dx, z - AZ - dz) <= r for dx, dz in barrels) and not (x, y, z) in P.cells:
                        P.put(x, y, z, COL['iron'])
    TY = YB + rl(B['trunnion_from_base'])
    YF = TY + rl(Cb['front_from_trunnion'])
    YR = YF - rl(Cb['len']) + 1
    assert YR >= 0, (key, YR)
    steps = [(rl(b0), rh(h)) for b0, h in Cb['cheek_steps']]
    a0, a1, abot = rl(Cb['arch'][0]), rl(Cb['arch'][1]), rh(Cb['arch'][2])
    cb = rh(Cb['cheek_bottom'])
    for k in range(k0, k1 + 1):                                              # cheek（兩片）
        for sg in (-1, 1):
            x = AX + sg * k
            for y in range(YR, YF + 1):
                back = YF - y
                top = [h for b0, h in steps if back >= b0][-1]
                bot = abot if a0 <= back <= a1 else cb
                for z in range(bot, top + 1):
                    P.put(x, y, z, COL['carriage'])
            P.put(x, TY, AZ + 1, COL['iron'], True)                          # cap square
    for k in range(-k1, k1 + 1):                                             # 耳軸：沿 x 穿過兩片 cheek
        P.put(AX + k, TY, AZ, COL['barrel'], True)
    yf = YF - rl(Cb['axle_front_back']); yr = YR + rl(Cb['axle_rear_fwd'])
    for ya, r in ((yf, Cb['wheel_front_r'] * sh), (yr, Cb['wheel_rear_r'] * sh)):
        P.box(AX - k1 - 1, AX + k1 + 1, ya, ya, 2, cb - 1, COL['carriage'])   # 軸木
        for sg in (-1, 1):
            P.wheel(AX + sg * (k1 + 1), ya + 0.5, r, r, COL['barrel'])
            P.put(AX + sg * (k1 + 2), ya, 2, COL['iron'], True)              # 輪軸頭
    P.box(AX - k0 + 1, AX + k0 - 1, YR, YR + rl(9), cb, cb, COL['carriage'])                       # 床板
    zq = min(AZ + dz for _, dz in barrels) - int(math.ceil(rmax)) - 1
    P.box(AX - rw(2), AX + rw(2), YR + 1, YR + rl(6), cb + 1, max(cb + 1, zq), COL['quoin'])        # quoin
    P.box(AX - k0 + 1, AX + k0 - 1, YF - 1, YF, cb, cb + 3, COL['carriage'])                         # 前 transom
    top = max(barrels, key=lambda b: b[1])
    pts = {'muzzle': (AX + top[0], YB + int(math.ceil(blen)) - 1, AZ + top[1]), 'breech': (AX + top[0], YB, AZ + top[1]),
           'cascabel': (AX + top[0], YB - 2 * cl, AZ + top[1]), 'train': (AX, YR, cb), 'trunnion': (AX, TY, AZ),
           'eye-aft': (AX - k1 - 1, YF - rl(10), rh(8)), 'eye-fwd': (AX + k1 + 1, YF - rl(10), rh(8))}
    if len(barrels) > 1:
        for i, (dx, dz) in enumerate(barrels):
            pts['muzzle-%s' % 'abc'[i]] = (AX + dx, YB + int(math.ceil(blen)) - 1, AZ + dz)
    for k, v in pts.items():
        if k.startswith('muzzle'):
            assert v not in P.cells, (key, k, '砲口那一格應該是挖空的')
    return P, pts, {'AX': AX, 'AZ': AZ, 'YB': YB, 'YF': YF, 'YR': YR, 'TY': TY, 'size': [W, L, H], 'barrel_len': blen}


def components(cells):
    S = set(cells); seen = set(); n = 0
    for c in S:
        if c in seen:
            continue
        n += 1; st = [c]; seen.add(c)
        while st:
            x, y, z = st.pop()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (x + d[0], y + d[1], z + d[2])
                if q in S and q not in seen:
                    seen.add(q); st.append(q)
    return n


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def main():
    S = G['scale']
    types = {}
    for key, T in G['types'].items():
        P, pts, geo = build(key)
        path = os.path.join(D, 'masks', 'guns', key + '.vox.txt'); os.makedirs(os.path.dirname(path), exist_ok=True)
        text = '# 風暴角號 %s（draft_guns.py，0.05 m）x,y,z,color —— at 0,0,0\n' % T['title'] + ''.join('%d,%d,%d,%d\n' % (x, y, z, c) for (x, y, z), c in sorted(P.cells.items()))
        open(path, 'w', encoding='utf-8', newline='\n').write(text)
        AX = geo['AX']
        cnt = {}
        for c in P.cells.values(): cnt[c] = cnt.get(c, 0) + 1
        asym = sum(1 for (x, y, z), c in P.cells.items() if P.cells.get((2 * AX - x, y, z)) != c)
        types[key] = {'P': P, 'pts': pts, 'geo': geo, 'pivot': [AX + 0.5, geo['YF'] + 1.0, 0.0],
                      'out': {'work': T['work'], 'title': T['title'], 'file': 'masks/guns/%s.vox.txt' % key, 'size': geo['size'], 'mpv': G['mpv'],
                              'cells': len(P.cells), 'colors': {str(k): v for k, v in sorted(cnt.items())}, 'asym_x': asym, 'components': components(P.cells),
                              'anchors': {k: list(v) for k, v in sorted(pts.items())}, 'pivot': [AX + 0.5, geo['YF'] + 1.0, 0.0],
                              'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}}
        print(key, types[key]['out']['size'], len(P.cells), cnt, 'asym', asym, 'components', types[key]['out']['components'])

    # ── 現況：引擎的組裝件格子＋模型外框 ──
    a = np.loadtxt(os.path.join(EX, 'ship_list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
    F = plan['frame']; NX, NY = F['NX'], F['NY']; NZ = 576
    occ = np.zeros((NX, NY, NZ), bool); occ[tuple(a[:, :3].T)] = True
    hull_only = occ.copy()
    PJ = json.load(open(os.path.join(EX, 'parts.json'), encoding='utf-8'))
    for m in PJ['models']:
        b = m['box']; occ[int(math.floor(b[0])):int(math.ceil(b[3])), int(math.floor(b[1])):int(math.ceil(b[4])), int(math.floor(b[2])):int(math.ceil(b[5]))] = True
    offs = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])

    def hit(Wp):
        i = np.floor(Wp).astype(int)
        ok = (i[:, 0] >= 0) & (i[:, 0] < NX) & (i[:, 1] >= 0) & (i[:, 1] < NY) & (i[:, 2] >= 0) & (i[:, 2] < NZ)
        h = np.ones(len(Wp), bool); h[ok] = occ[i[ok, 0], i[ok, 1], i[ok, 2]] | guns_occ[i[ok, 0], i[ok, 1], i[ok, 2]]
        return h

    # ── 砲門清單：(列, 名, 側, 型, 砲口方向, rotate, mirror, 橫向中心, 牆外面（沿砲口方向的座標）, 開口 z, 甲板面候選, host) ──
    VD = json.load(open(os.path.join(D, 'verify_decks.json'), encoding='utf-8'))
    VS = json.load(open(os.path.join(D, 'verify_stern.json'), encoding='utf-8'))
    VH = json.load(open(os.path.join(D, 'verify_head.json'), encoding='utf-8'))
    host = {'lower': ('summit-stormkaap-01m-deck-lower', '甲板-下'), 'upper': ('summit-stormkaap-01m-deck-upper', '甲板-上')}

    def tops_under(xs, ys, zmax, around):
        t = set()
        for x in xs:
            for y in ys:
                c = np.nonzero(hull_only[x, y, :zmax])[0]
                if len(c): t.add(int(c.max()))
        return sorted(v for v in t if around - 2 <= v <= around + 2)

    ports = []
    n_by = {'lower': 0, 'upper': 0}
    for p in VD['ports']:
        n_by[p['row']] += 1; n = n_by[p['row']]
        x0, x1 = p['x']; xc = (x0 + x1 + 1) / 2.0; z0 = p['z'][0]
        for side, nm in ((1, 'S'), (-1, 'P')):
            ys = range(YC + 1, NY) if side > 0 else range(YC - 1, -1, -1)
            row = [y for y in ys if hull_only[int(xc), y, z0 - 1]]
            outer = (max(row) + 1) if side > 0 else min(row)
            inboard = [outer - side * k for k in range(4, 21)]                 # 牆內 4–20 格（船尾那幾個砲門船很窄，⛔ 不用離中線多遠）
            tops = tops_under(range(int(xc) - 6, int(xc) + 7), inboard, z0 - 3, p['deck_plank_z'])
            ports.append({'name': '砲-%s%d' % (nm, n), 'row': p['row'], 'type': G.get('override', {}).get('%s:%d' % (p['row'], n), G['rows'][p['row']]), 'dir': [0, side, 0], 'rot': 0, 'mirror': 'y' if side < 0 else 'none',
                          'lat_axis': 0, 'lat': xc, 'outer': outer, 'open_z': p['z'], 'open_lat': p['x'], 'tops': tops, 'host': host[p['deck']],
                          'meta': {'kind': 'gun', 'side': nm, 'port': n, 'deck': p['deck']}})
    for i, (sp, nm) in enumerate(zip(VS['ports'], ('AP', 'AS'))):
        yc = (sp['y'][0] + sp['y'][1] + 1) / 2.0; z0 = sp['z'][0]
        row = [x for x in range(60, 200) if hull_only[x, int(yc), z0 - 1]]
        run = [row[0]]
        for x in row[1:]:
            if x != run[-1] + 1: break
            run.append(x)
        outer = run[0]
        tops = tops_under(range(run[-1] + 4, run[-1] + 30), range(int(yc) - 5, int(yc) + 6), z0 - 3, z0 - 7)
        ports.append({'name': '砲-%s' % nm, 'row': 'stern', 'type': G['rows']['stern'], 'dir': [-1, 0, 0], 'rot': 90, 'mirror': 'none', 'lat_axis': 1, 'lat': yc,
                      'outer': outer, 'open_z': sp['z'], 'open_lat': sp['y'], 'tops': tops, 'host': host['upper'],
                      'meta': {'kind': 'gun', 'side': nm[1], 'port': i + 1, 'deck': 'upper', 'arc': 'stern'}})
    for i, (cp, nm) in enumerate(zip(VH['chase_ports'], ('FP', 'FS'))):
        yc = (cp['y'][0] + cp['y'][1] + 1) / 2.0; z0 = cp['z'][0]
        row = [x for x in range(VH['bulkhead_x'] + 20, 450, -1) if hull_only[x, int(yc), z0 - 1]]
        run = [row[0]]
        for x in row[1:]:
            if x != run[-1] - 1: break
            run.append(x)
        outer = run[0] + 1
        tops = tops_under(range(run[-1] - 30, run[-1] - 3), range(int(yc) - 5, int(yc) + 6), z0 - 3, z0 - 7)
        ports.append({'name': '砲-%s' % nm, 'row': 'chase', 'type': G['rows']['chase'], 'dir': [1, 0, 0], 'rot': -90, 'mirror': 'none', 'lat_axis': 1, 'lat': yc,
                      'outer': outer, 'open_z': cp['z'], 'open_lat': cp['y'], 'tops': tops, 'host': host['upper'],
                      'meta': {'kind': 'gun', 'side': nm[1], 'port': i + 1, 'deck': 'upper', 'arc': 'bow'}})

    codes = {'12l': '12l', '6l': '6l', 'chase3': '3chase'}
    rows = []
    guns_occ = np.zeros_like(occ)                                           # 已經擺好的砲（格心＋八角落在的格）⇒ 後擺的要躲開（兩舷的砲彼此是模型、不在 occ 裡）
    for po in ports:
        tp = types[po['type']]; P = tp['P']; piv = np.array(tp['pivot'])
        cells = np.array(sorted(P.cells), float)
        samp = (cells[:, None, :] + offs[None]).reshape(-1, 3)
        bot = cells[cells[:, 2] == 0]
        bsamp = np.array([[x + ox, y + oy, 0.0] for x, y, _ in bot for ox in (0.3, 0.7) for oy in (0.3, 0.7)])
        muz = np.array(tp['pts']['muzzle'], float) + 0.5
        dvec = np.array(po['dir'], float); ax = 0 if dvec[0] else 1

        def place(Q, at):
            q = (Q - piv) * S
            if po['mirror'] == 'y': q[:, 1] = -q[:, 1]
            return rotz(q, po['rot']) + np.asarray(at)

        def support(at):
            i = np.floor(place(bsamp, at)).astype(int)
            return [int(occ[i[:, 0], i[:, 1], i[:, 2] - 1].sum()), len(i)]
        best = None
        if not po['tops']:
            raise SystemExit('%s 找不到甲板面' % po['name'])
        for dl in G['search']['dx']:
            for t in po['tops']:
                for kb in range(int(G['search']['max_back'] / G['search']['step']) + 1):
                    back = kb * G['search']['step']
                    at = [0.0, 0.0, float(t + 1)]
                    at[po['lat_axis']] = po['lat'] + dl
                    at[ax] = po['outer'] - dvec[ax] * back
                    if hit(place(samp, at)).any():
                        continue
                    tip = place(muz[None], at)[0]
                    sup = support(at)
                    beyond = float((tip[ax] - po['outer']) * dvec[ax])
                    cand = {'at': [round(v, 3) for v in at], 'dl': dl, 'back_from_outer': back, 'muzzle_beyond_outer': round(beyond, 3),
                            'axis_z': round(float(tip[2]), 3), 'deck_top': t, 'wheel_support': sup}
                    key = (sup[0] < sup[1], beyond < G['search']['min_muzzle_out'], abs(dl), back)
                    if best is None or key < best[0]:
                        best = (key, cand)
                    break
        if best is None:
            raise SystemExit('%s 退到 %g 格還塞不進去' % (po['name'], G['search']['max_back']))
        c = best[1]
        gi = np.floor(place(samp, c['at'])).astype(int); guns_occ[gi[:, 0], gi[:, 1], gi[:, 2]] = True
        meta = dict(po['meta']); meta['gun'] = codes[po['type']]
        if po['type'] == 'chase3': meta['barrels'] = 3
        r = {'model': po['name'], 'host_work': po['host'][0], 'host_link': po['host'][1], 'type': po['type'], 'work': G['types'][po['type']]['work'],
             'row': po['row'], 'rotate': [0, 0, po['rot']], 'mirror': po['mirror'], 'pivot': tp['pivot'], 'meta': meta,
             'opening_z': po['open_z'], 'opening_lat': po['open_lat'], 'outer': po['outer'], 'tops': po['tops']}
        r.update(c)
        rows.append(r)
        print(r['model'], r['row'], json.dumps({k: c[k] for k in ('at', 'dl', 'back_from_outer', 'muzzle_beyond_outer', 'axis_z', 'deck_top', 'wheel_support')}), 'open_z', po['open_z'])

    # ── 墊木：還有輪子懸空的砲，輪底（模型 z 0 那一層）正下方的空格往下補到碰到實心（甲板色），格放在那一層甲板的子作品 ──
    pads = {}
    for r in rows:
        if r['wheel_support'][0] == r['wheel_support'][1]:
            r['pad_cells'] = 0; continue
        tp = types[r['type']]; piv = np.array(tp['pivot'])
        cells = np.array(sorted(tp['P'].cells), float); bot = cells[cells[:, 2] == 0]
        bs = np.array([[x + ox, y + oy, 0.0] for x, y, _ in bot for ox in (0.3, 0.7) for oy in (0.3, 0.7)])
        q = (bs - piv) * S
        if r['mirror'] == 'y': q[:, 1] = -q[:, 1]
        w = rotz(q, r['rotate'][2]) + r['at']
        n0 = 0
        for x, y in sorted({(int(math.floor(p[0])), int(math.floor(p[1]))) for p in w}):
            z = int(round(r['at'][2])) - 1
            k = 0
            while not occ[x, y, z - k]:
                assert k < 3, (r['model'], '墊木要補超過 3 格', x, y)
                k += 1
            for j in range(k):
                c = (x, y, z - j)
                if c not in pads.setdefault(r['host_work'], {}):
                    pads[r['host_work']][c] = plan['decks']['colors']['plank'] if 'plank' in plan['decks']['colors'] else 104; n0 += 1
        r['pad_cells'] = n0
        for c in pads[r['host_work']]: occ[c] = True
        sup = np.floor(w).astype(int)
        r['wheel_support_after_pad'] = [int(occ[sup[:, 0], sup[:, 1], sup[:, 2] - 1].sum()), len(sup)]
    pad_files = {}
    for hw, P_ in sorted(pads.items()):
        NL = chr(10)
        text = '# 風暴角號 砲的墊木（draft_guns.py）x,y,z,color —— %s，at 0,0,0' % hw + NL + ''.join('%d,%d,%d,%d' % (c + (v,)) + NL for c, v in sorted(P_.items()))
        fn = 'masks/guns/pads_%s.vox.txt' % hw.rsplit('-', 1)[1]
        open(os.path.join(D, fn), 'w', encoding='utf-8', newline=NL).write(text)
        pad_files[hw] = {'file': fn, 'voxels': len(P_), 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
    print('pads', {k: v['voxels'] for k, v in pad_files.items()}, {r['model'] + '@' + r['host_link']: r.get('wheel_support_after_pad') for r in rows if r['pad_cells']})
    out = {'note': 'draft_guns.py（階段十二）—— 三種砲的子作品與 42 門模型的擺放；現況 ＝ 引擎匯出 %s（%d 格）＋ 模型外框 %d' % ('exports/stage11', len(a), len(PJ['models'])),
           'scale': S, 'types': {k: v['out'] for k, v in types.items()}, 'rows': rows, 'pads': pad_files}
    with open(os.path.join(D, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
    bad = [r['model'] for r in rows if r['wheel_support'][0] < r['wheel_support'][1] or r['muzzle_beyond_outer'] < G['search']['min_muzzle_out']]
    print('rows', len(rows), '不理想（輪子懸空或砲口沒伸出）:', bad)


if __name__ == '__main__':
    main()
