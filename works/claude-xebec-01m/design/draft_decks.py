# 利劍號 新圖紙 03（TASK-0022 步驟 5）：甲板（底艙平台、主甲板、後甲板）、梯子、梯井、桅孔、後甲板前壁（門）、梯子固定點、甲板 meta
#   出處：claude-baghlah-01m/design/draft_decks.py（星辰號；它出自 calli-cosecha-01m）。改的地方：
#   * 船殼不是 draft_ports.build，是本船的 lines.solid ＋ masks/hull（S ＝ 外形實心、wall ＝ 外形往裡 2 格的殼、keep ＝ 作品上的船殼格）。
#   * 甲板高度不是 layout.deck_z：主甲板 ＝ 主舷牆頂往下 decks_build.main_below_rail（跟舷弧平行）、後甲板 ＝ 主舷牆頂那一層、
#     底艙平台 ＝ 固定高度；每一層的範圍照「那一層船殼裡夠寬」自動找（底艙平台）或照 plan 的 X 範圍（後甲板）。
#   * 沒有星辰號的船首水槽、舵手台、台階、胸牆；有後甲板前壁（break，門）。
#   * 走路格、梯子點、④ 梯頂、⑤ 甲板連通、⑥ 艙底的量法照星辰號（Ship_Decks §9.3）。
#   用法：python -I -X utf8 draft_decks.py [--probe=drop_ladder=<名>[,<名>]]（probe 不寫檔）
#   輸出：masks/decks/<層>.vox.txt、masks/ladders/<上層>.vox.txt（世界座標，at 0,0,0）、ladder_points.json、decks_meta.tsv、
#         verify_decks.json、sheet03_decks_v1.png
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import main_rail, palette_rgb

HEAD = 12      # 走路頭上 1.2 m
STEP_HOLD = 6  # 艙底：0.6 m 一步（Ship_Decks ⑥）
HEAD_PT = 14   # 梯子點頭上 14 格（照收穫號、星辰號）
STEP = 3       # 走路一步 0.3 m
V = HL.V


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    probes = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[1:] if a.startswith('--probe'))
    plan = HL.load_plan(HERE)
    L = HL.Lines(plan)
    SX, SY, SZ = plan['space']['hull']
    YC = L.YC
    S = L.solid(0, SX - 1, SZ - 1, 0.0)
    Sx = np.pad(L.solid(0, SX - 1, SZ - 1, 3.0), 1)
    dist = ndimage.distance_transform_edt(Sx)[1:-1, 1:-1, 1:-1]
    wall = S & (dist <= V(plan['hull_build']['wall']))
    hull = np.loadtxt(os.path.join(HERE, 'masks', 'hull', 'hull_01.vox.txt'), delimiter=',', comments='#', dtype=int)
    keep = np.zeros(S.shape, bool)
    keep[hull[:, 0], hull[:, 1], hull[:, 2]] = True
    final = np.zeros(S.shape, np.uint8)
    final[hull[:, 0], hull[:, 1], hull[:, 2]] = hull[:, 3]
    inside = S & ~wall & ~keep
    nx, ny, nz = S.shape
    X = np.arange(nx)
    Y = np.arange(ny)
    DY = Y - YC
    Xm = L.x_m(X + 0.5)
    B = plan['decks_build']
    G = B['groups']
    rows = [g['key'] for g in G]
    mr = main_rail(L, Xm)
    # 每一層的站立高度（第一層空氣）與範圍
    zstand, inspan = {}, {}
    zmain = np.floor(L.K * 10 * (mr - B['main_below_rail'])).astype(int) + 1
    zstand['main'] = zmain
    zq = np.floor(L.K * 10 * mr).astype(int) + np.where(X <= B['quarter_dz_aft_to_x'], B['quarter_dz_aft'], B['quarter_dz'])
    zstand['quarter'] = zq
    # 底艙平台：船中一段平鋪在 hold_z；往兩頭船底抬起來的地方，板跟著抬到「那一欄船殼裡寬過 ±hold_end_half 的最低一層」，
    #   只要板上到主甲板樑底還有 HEAD 格（v1 只鋪平的一段 ⇒ 兩頭的船底斜面被算成沒梯子的艙底 34／23 m²，⑥ 會報）
    zh = np.full(nx, -1, int)
    for x in range(nx):
        zw = next((z for z in range(nz) if inside[x, YC - B['hold_end_half']:YC + B['hold_end_half'] + 1, z].all()), None)
        if zw is None:
            continue
        z = max(B['hold_z'], zw)
        if z + 1 + HEAD <= zmain[x] - 1 - B['beam_depth']['main']:
            zh[x] = z
    ok = zh >= 0
    lab_, n_ = ndimage.label(ok)
    mid = lab_[int(np.argmax(np.where(ok, zh == B['hold_z'], False)))]
    inspan['hold'] = lab_ == mid
    zstand['hold'] = np.where(inspan['hold'], zh + 1, B['hold_z'] + 1)
    inspan['main'] = np.array([inside[x, YC, max(0, zmain[x] - 1)] for x in range(nx)])
    qa = int(math.floor(L.XAP + V(plan['decks']['quarterdeck'])['X_plate'][1] * L.K * 10))
    inspan['quarter'] = (X <= qa) & np.array([inside[x, YC, zq[x] - 1] for x in range(nx)])

    LD = B['ladders']
    ladders = [dict(l) for l in LD['list']]
    if 'drop_ladder' in probes:
        ladders = [l for l in ladders if l['name'] not in probes['drop_ladder'].split(',')]
    th, rise, run = LD['tread_half'], LD['rise'], LD['run']
    geo = []
    for ld in ladders:
        s, xs = ld['dir'], ld['xs']
        zl = int(zstand[ld['lo']][xs - s])
        n = None
        for _ in range(4):
            xe = xs + s * (run * (n or 4) + run - 1) + s
            zu = int(zstand[ld['up']][xe])
            n2 = (zu - zl - 1) // rise
            if n2 == n:
                break
            n = n2
        top_end = xs + s * (run * n + run - 1)
        zu = int(zstand[ld['up']][top_end + s])
        head_x = top_end + s * LD['head_back']
        beam_bot = zu - 1 - B['beam_depth'][ld['up']]
        k0 = next(k for k in range(0, n + 1) if zl + rise * k + HEAD_PT - 1 >= beam_bot)
        geo.append(dict(ld, zl=zl, zu=zu, n=n, top_end=top_end, head_x=head_x, k0=k0, well_from=xs + s * run * k0))

    hole = {k: np.zeros((nx, ny), bool) for k in rows}
    coam = {k: np.zeros((nx, ny), bool) for k in rows}
    for g in geo:
        if not g.get('well'):
            continue
        s, yc = g['dir'], YC + g['dy']
        xa, xb = sorted((g['well_from'], g['top_end']))
        m = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - yc)[None, :] <= th + 2)
        hole[g['up']] |= m
        side = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - yc)[None, :] == th + 3)
        low_end = (X[:, None] == g['well_from'] - s) & (np.abs(Y - yc)[None, :] <= th + 3)
        coam[g['up']] |= side | low_end
    # 桅孔：照 draft_layout 的桅腳與傾角，在每一層板的高度算桅軸
    lay = json.load(open(os.path.join(HERE, 'verify_layout.json'), encoding='utf-8'))['masts']
    rig = plan['rig']['v']
    masts = {}
    for m, v in lay.items():
        r = V(B['mast_r'])[m]
        (fx, fz), (tx, tz) = v['foot'], v['top']
        masts[m] = {'foot': [fx, fz], 'top': [tx, tz], 'r': r}
        for k in rows:
            # 桅軸在這一層板高度的 x（以中段 x 的板高近似）
            xa_ = fx + (tx - fx) * ((zstand[k][int(round(fx))] - 1) - fz) / (tz - fz)
            xi = int(round(xa_))
            if 0 <= xi < nx and inspan[k][xi] and zstand[k][xi] - 1 > fz:
                disk = (X[:, None] + 0.5 - xa_) ** 2 + (Y[None, :] + 0.5 - (YC + 0.5)) ** 2 <= r ** 2
                hole[k] |= disk
                masts[m].setdefault('holes', {})[k] = round(xa_, 1)
    for k in rows:
        coam[k] &= ~hole[k]

    # 甲板：板（相鄰一欄低 2 格以上補 riser）、樑、艙口圍
    cells = {k: np.zeros(S.shape, np.uint8) for k in rows}
    P = B['plank']
    for k in rows:
        c = cells[k]
        pc = P['weather'] if k in P['weather_rows'] else P['interior']
        bd = B['beam_depth'][k]
        zp = zstand[k] - 1
        for xi in range(nx):
            if not inspan[k][xi]:
                continue
            z = zp[xi]
            zlo = z
            for nb in (xi - 1, xi + 1):
                if 0 <= nb < nx and inspan[k][nb]:
                    zlo = min(zlo, zp[nb] + 1)
            for zz in range(zlo, z + 1):
                r = inside[xi, :, zz] & ~hole[k][xi]
                c[xi, r, zz] = pc
            if bd and (X[xi] % B['beam_every']) < B['beam_w']:
                for dz in range(1, bd + 1):
                    r = inside[xi, :, zlo - dz] & ~hole[k][xi] & (c[xi, :, zlo - dz] == 0)
                    c[xi, r, zlo - dz] = B['beam_color']
            for dz in range(1, B['coaming_h'] + 1):
                r = inside[xi, :, z + dz] & coam[k][xi]
                c[xi, r, z + dz] = B['trim']
    # 後甲板前壁（break）：主甲板到後甲板板之間一道牆，中間開門
    br = B['break']
    xb_ = qa + 1
    door = np.abs(DY) <= br['door_half']
    for z in range(int(zstand['main'][xb_]), int(zstand['quarter'][qa])):
        r = inside[xb_, :, z] & ~door & (cells['quarter'][xb_, :, z] == 0)
        cells['quarter'][xb_, r, z] = B['trim']

    # 後甲板前緣欄杆（verifier45：前緣沒欄杆、整條掉 1.4 m 到主甲板）：x ＝ 後甲板最前一欄，板上 h 格高，
    #   柱每 2 格一根、頂欄 1 格；上後甲板的梯子那兩段（梯頭 ± th+2）留口
    bw = B['breast_rail']
    gap = np.zeros(ny, bool)
    for g in geo:
        if g['up'] == 'quarter':
            gap |= np.abs(Y - (YC + g['dy'])) <= th + 2
    zq0 = int(zstand['quarter'][qa])
    plank_y = cells['quarter'][qa, :, zq0 - 1] > 0              # 欄杆只放在那一欄有板的寬度裡（前緣在船殼頂上面，inside 不能用）
    for z in range(zq0, zq0 + bw['h']):
        top_row = z == zq0 + bw['h'] - 1
        r = plank_y & ~keep[qa, :, z] & ~gap & (top_row | (DY % 2 == 0))
        cells['quarter'][qa, r & (cells['quarter'][qa, :, z] == 0), z] = B['trim']

    # 梯子：每 rise 一階、每階 run 長、兩側斜樑
    LC = LD['color']
    lad, pts = {}, {}
    for g in geo:
        up = g['up']
        cl = lad.setdefault(up, np.zeros(S.shape, np.uint8))
        s, xs, n, zl, zu = g['dir'], g['xs'], g['n'], g['zl'], g['zu']
        yc = YC + g['dy']
        for kk in range(0, n + 2):
            xa = xs + s * run * kk
            xr = sorted((xa, xa + s * (run - 1)))
            zt = zl - 1 + rise * kk
            for xx in range(xr[0], xr[1] + 1):
                if 1 <= kk <= n:
                    cl[xx, yc - th:yc + th + 1, zt] = LC
                if kk == 0:
                    zlo_, zhi_ = zl, zl + 2
                elif kk <= n:
                    zlo_, zhi_ = zt - 3, zt
                else:
                    zlo_, zhi_ = zl - 1 + rise * n - 3, zu - 1
                for z in range(max(zlo_, 0), zhi_ + 1):
                    for yy in (yc - th - 1, yc + th + 1):
                        cl[xx, yy, z] = LC
        pts[g['name']] = {'up': g['up'], 'lo': g['lo'], 'group_up': up, 'steps': n, 'decks': g.get('decks'),
                          'points': {'foot': [xs - s, yc, zl], 'lo': [xs + s * run, yc, zl + rise],
                                     'hi': [xs + s * run * n, yc, zl + rise * n], 'head': [g['head_x'], yc, zu]}}
    anyd = np.zeros(S.shape, bool)
    for c in cells.values():
        anyd |= c > 0
    for k in lad:
        lad[k][anyd | keep | ~inside] = 0

    # 封閉空腔（船殼＋甲板＋梯子）⇒ 填樑色，歸最近的那一層
    uni = keep.copy()
    for c in list(cells.values()) + list(lad.values()):
        uni |= c > 0
    cav = ndimage.binary_fill_holes(uni) & ~uni
    labc, ncav = ndimage.label(cav)
    filled = []
    for i in range(1, ncav + 1):
        idx = np.argwhere(labc == i)
        xm_, zm_ = int(np.median(idx[:, 0])), float(np.median(idx[:, 2]))
        k = min(rows, key=lambda kk: abs(zstand[kk][xm_] - zm_) + (0 if inspan[kk][xm_] else 1000))
        cells[k][labc == i] = B['beam_color']
        filled.append({'group': k, 'cells': int(len(idx)), 'x': [int(idx[:, 0].min()), int(idx[:, 0].max())], 'z': [int(idx[:, 2].min()), int(idx[:, 2].max())]})

    # ── 讀數 ──
    R = {'groups': {}, 'ladders': {}, 'spans': {k: [int(np.where(inspan[k])[0].min()), int(np.where(inspan[k])[0].max())] for k in rows}}
    allc = np.zeros(S.shape, np.int16)
    for k, c in cells.items():
        m = c > 0
        R['groups'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & keep).sum()), 'outside_hull': int((m & ~S).sum()),
                          'colors': {int(a): int(b) for a, b in zip(*np.unique(c[m], return_counts=True))}, 'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    for k, c in lad.items():
        m = c > 0
        R['ladders'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & keep).sum()), 'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    R['overlap_between_parts'] = int((allc > 1).sum())
    R['parts_outside_inside'] = int(((allc > 0) & ~inside).sum())
    occ = keep | (allc > 0)
    ladm = np.zeros(S.shape, bool)
    for c in lad.values():
        ladm |= c > 0
    R['structure_all'] = {'components_6': int(ndimage.label(occ)[1]), 'cavities': int((ndimage.binary_fill_holes(occ) & ~occ).sum()),
                          'mirror_diff': int((occ != occ[:, ::-1, :]).sum())}

    meta = {}
    for g in G:
        k = g['key']
        pts_xz = [(int(x), int(zstand[k][x])) for x in range(nx) if inspan[k][x] and (cells[k][x, :, zstand[k][x] - 1] > 0).any()]
        comp = []
        for i, (x, z) in enumerate(pts_xz):
            prev = pts_xz[i - 1][1] if i else None
            nxt = pts_xz[i + 1][1] if i + 1 < len(pts_xz) else None
            if prev != z or nxt != z:
                comp.append('%d:%d' % (x, z))
        meta[k] = {'kind': 'deck', 'deck': k, 'level': g['level'], 'name': g['name'], 'floor': ','.join(comp), 'thick': g['thick']}
    R['deck_meta'] = meta

    def floor_at(gk, x):
        f = [tuple(map(int, p.split(':'))) for p in meta[gk]['floor'].split(',')]
        if x < f[0][0] or x > f[-1][0]:
            return None
        for (xa, za), (xb, zb) in zip(f, f[1:]):
            if xa <= x <= xb:
                return za if xb == xa else za + (zb - za) * (x - xa) / (xb - xa)
        return f[0][1]

    probs = []
    for nm, v in pts.items():
        for pk, (px, py, pz) in v['points'].items():
            air = not occ[px, py, pz]
            flo = bool(occ[px, py, pz - 1])
            hd = int(occ[px, py, pz:pz + HEAD_PT].sum())
            if not (air and flo) or hd:
                probs.append([nm, pk, [px, py, pz], air, flo, hd])
        hx = v['points']['hi'][0]
        ex, ez = v['points']['head'][0], v['points']['head'][2]
        s = 1 if ex > hx else -1
        run_empty, worst = 0, 0
        for x in range(hx + s, ex + s, s):
            ok = False
            for dy in range(-1, 2):
                yi_ = v['points']['head'][1] + dy
                for z in range(ez - 3, ez + 4):
                    if occ[x, yi_, z - 1] and not occ[x, yi_, z:z + HEAD].any():
                        ok = True
            run_empty = 0 if ok else run_empty + 1
            worst = max(worst, run_empty)
        v['top_gap_cols'] = worst
    R['ladder_point_problems'] = probs

    # 走路格：腳下實心、頭上 HEAD 格空、站的那一格在船殼裡、不踩梯子
    airrun = np.zeros(S.shape, np.int16)
    for z in range(nz - 1, -1, -1):
        airrun[:, :, z] = np.where(occ[:, :, z], 0, (airrun[:, :, z + 1] + 1) if z + 1 < nz else 1)
    st_ok = np.zeros(S.shape, bool)
    st_ok[:, :, 1:] = occ[:, :, :-1] & ~ladm[:, :, :-1] & (airrun[:, :, 1:] >= HEAD) & S[:, :, 1:] & ~keep[:, :, 1:]
    idx = np.argwhere(st_ok)
    nid = -np.ones(S.shape, np.int64)
    nid[tuple(idx.T)] = np.arange(len(idx))
    ea, eb, edz = [], [], []
    for dx, dyy in ((1, 0), (0, 1)):
        for dz in range(-STEP_HOLD, STEP_HOLD + 1):
            a = idx
            b = a + [dx, dyy, dz]
            ok = (b[:, 0] < nx) & (b[:, 1] < ny) & (b[:, 2] >= 0) & (b[:, 2] < nz)
            a, b = a[ok], b[ok]
            j = nid[tuple(b.T)]
            ok = j >= 0
            ea.append(nid[tuple(a[ok].T)])
            eb.append(j[ok])
            edz.append(np.full(int(ok.sum()), abs(dz)))
    ea, eb, edz = np.concatenate(ea), np.concatenate(eb), np.concatenate(edz)
    deck_of = np.full(len(idx), '', object)
    best = np.full(len(idx), 1e9)
    for g in G:
        fl = np.array([floor_at(g['key'], x) if floor_at(g['key'], x) is not None else np.nan for x in range(nx)])
        f = fl[idx[:, 0]]
        d = idx[:, 2] - f
        ok = ~np.isnan(f) & (d >= -3) & (d <= 20) & (np.abs(d) < best)
        deck_of[ok] = g['key']
        best[ok] = np.abs(d[ok])
    lowest = np.array([min([floor_at(g['key'], x) for g in G if floor_at(g['key'], x) is not None] or [1e9]) for x in range(nx)])
    hold = (deck_of == '') & (idx[:, 2] < lowest[idx[:, 0]] - 3)
    deck_of[hold] = 'bilge'

    def comps(extra):
        same = (deck_of[ea] == deck_of[eb]) & ((edz <= STEP) | (deck_of[ea] == 'bilge'))
        e1 = np.concatenate([ea[same]] + [np.array([p for p, q in extra], np.int64)])
        e2 = np.concatenate([eb[same]] + [np.array([q for p, q in extra], np.int64)])
        M = coo_matrix((np.ones(len(e1)), (e1, e2)), shape=(len(idx), len(idx)))
        return connected_components(M, directed=False)[1]

    def nearest(p, want):
        x, y, z = p
        best_, bd_ = None, 1e9
        for dx in range(-10, 11):
            for dyy in range(-10, 11):
                for dz in range(-3, 4):
                    xi_, yi_, zi_ = x + dx, y + dyy, z + dz
                    if 0 <= xi_ < nx and 0 <= yi_ < ny and 0 <= zi_ < nz and nid[xi_, yi_, zi_] >= 0:
                        j = nid[xi_, yi_, zi_]
                        if deck_of[j] != want:
                            continue
                        dd = dx * dx + dyy * dyy + dz * dz
                        if dd < bd_:
                            best_, bd_ = j, dd
        return best_, bd_ ** 0.5 if best_ is not None else None
    links, link_rd = [], {}
    for nm, v in pts.items():
        a, da = nearest(v['points']['foot'], v['lo'])
        b, db = nearest(v['points']['head'], v['group_up'])
        link_rd[nm] = {'foot_to_walk': da, 'head_to_walk': db}
        if a is not None and b is not None:
            links.append((a, b))
    lab = comps(links)
    trunk = int(np.argmax(np.bincount(lab)))
    walk = {}
    for gk in rows + ['bilge']:
        sel = deck_of == gk
        cols = lambda m: len({(int(a), int(b)) for a, b in idx[m][:, :2]})
        tot, got = cols(sel), cols(sel & (lab == trunk))
        chunks = []
        for c_ in np.unique(lab[sel & (lab != trunk)]):
            mm = sel & (lab == c_)
            area = cols(mm)
            if area >= 200:
                chunks.append({'m2': area / 100.0, 'x': [int(idx[mm][:, 0].min()), int(idx[mm][:, 0].max())], 'z': [int(idx[mm][:, 2].min()), int(idx[mm][:, 2].max())]})
        walk[gk] = {'m2': tot / 100.0, 'reached_m2': got / 100.0, 'unreached_chunks_ge_2m2': chunks}
    R['walk'] = walk
    R['ladder_links'] = link_rd

    # 開口前面（往艙裡 8 格）不能有本步驟的格
    blocked = []
    parts = allc > 0
    lv = json.load(open(os.path.join(HERE, 'verify_lines.json'), encoding='utf-8'))
    for p in lv['ports']:
        za, zb = p['z']
        for sg in (1, -1):
            n = 0
            for x in range(p['x'][0], p['x'][1] + 1):
                ys = [y for y in range(ny) if (y - YC) * sg > 0 and wall[x, y, (za + zb) // 2]]
                if not ys:
                    continue
                yin = min(ys, key=lambda y: abs(y - YC))
                rng = range(yin - sg * 8, yin) if sg > 0 else range(yin + 1, yin + 9)
                for yy in rng:
                    n += int(parts[x, yy, za:zb + 1].sum())
            if n:
                blocked.append([p['kind'], p['X_m'], 'S' if sg > 0 else 'P', n])
    R['ports_blocked_inside'] = blocked
    R['holes'] = {k: int(hole[k].sum()) for k in rows}
    R['masts'] = masts
    R['cavities_filled'] = filled
    R['ladders_geo'] = {g['name']: {'n': g['n'], 'zl': g['zl'], 'zu': g['zu'], 'top_end': g['top_end'], 'head_x': g['head_x'],
                                    'well': [g['well_from'], g['top_end']] if g.get('well') else None} for g in geo}
    R['ladder_points'] = pts
    R['zstand_samples'] = {k: {str(x): int(zstand[k][x]) for x in range(0, nx, 40) if inspan[k][x]} for k in rows}
    if probes:
        print(json.dumps({'probe': probes, 'walk': {k: [v['m2'], v['reached_m2']] for k, v in walk.items()},
                          'ladder_point_problems': probs, 'top_gap': {k: v['top_gap_cols'] for k, v in pts.items()}}, ensure_ascii=False))
        return

    def dump(path, c, head):
        ii = np.argwhere(c > 0)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for a, b, z in ii:
                f.write('%d,%d,%d,%d\n' % (a, b, z, c[a, b, z]))
        return [int(len(ii)), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    od, ol = os.path.join(HERE, 'masks', 'decks'), os.path.join(HERE, 'masks', 'ladders')
    for dd in (od, ol):
        os.makedirs(dd, exist_ok=True)
        for f in os.listdir(dd):
            if f.endswith('.vox.txt'):
                os.remove(os.path.join(dd, f))
    R['lists'] = {}
    for k, c in cells.items():
        R['lists']['deck-' + k] = dump(os.path.join(od, k + '.vox.txt'), c, '# 利劍號 甲板 %s（draft_decks.py；世界座標，at 0,0,0）\n' % k)
    for k, c in lad.items():
        R['lists']['ladders-' + k] = dump(os.path.join(ol, k + '.vox.txt'), c, '# 利劍號 梯子（上到 %s；draft_decks.py；世界座標，at 0,0,0）\n' % k)
    with open(os.path.join(HERE, 'ladder_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pts, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'decks_meta.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        for g in G:
            f.write('link\t甲板-%s\t%s\n' % (g['key'], json.dumps(meta[g['key']], ensure_ascii=False, separators=(',', ':'))))
    # 圖：每層由上往下看 ＋ 中線剖面
    fnt = ImageFont.load_default()
    Hp = 80 + len(rows) * (ny + 30) + nz + 60
    im = Image.new('RGB', (nx + 140, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((10, 10), 'al-Sayf sheet 03: decks, break, ladders, mast holes v1', fill=(0, 0, 0), font=fnt)
    d.text((10, 30), 'each deck from above; blue = ladders; bottom = centreline section', fill=(0, 0, 0), font=fnt)
    for i, k in enumerate(rows):
        oy = 60 + i * (ny + 30)
        d.text((10, oy + ny // 2 - 6), k, fill=(0, 0, 0), font=fnt)
        top = cells[k].max(axis=2)
        lt = lad[k].max(axis=2) if k in lad else np.zeros_like(top)
        for a in range(nx):
            for b in range(ny):
                if lt[a, b]:
                    d.point((100 + a, oy + b), fill=(0, 90, 200))
                elif top[a, b]:
                    d.point((100 + a, oy + b), fill=palette_rgb(int(top[a, b])))
    oy = 60 + len(rows) * (ny + 30)
    for a in range(nx):
        for z in range(nz):
            cc = final[a, YC, z]
            for dd in list(cells.values()) + list(lad.values()):
                if dd[a, YC, z]:
                    cc = dd[a, YC, z]
            if cc:
                d.point((100 + a, oy + nz - z), fill=palette_rgb(int(cc)))
    im.save(os.path.join(HERE, 'sheet03_decks_v1.png'))
    with open(os.path.join(HERE, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('ladder_points', 'lists', 'deck_meta')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
