# 收穫號 階段九（TASK-0598）：彈藥庫（子作品＋火藥桶模型）、小艇架（子作品）、舵輪／羅經櫃／絞盤／小艇（沿用現有元件的外部模型）
#   輸入：plan.json（gear_build）＋ 組裝件現在的格子（CLI 匯出，扣掉本階段自己的兩件子作品 ⇒ 重產時不會把自己上一輪當成船）
#   輸出：masks/gear/magazine.vox.txt、masks/gear/skids.vox.txt（世界座標、at 0,0,0）、gear_placement.json（固定點＋每個模型）、verify_gear.json
#   彈藥庫做法照夜燈號 draft_magazine.py（照抄餘燼號）：兩道橫艙壁之間、每個 x 的橫切面裡中線那一塊空氣 ⇒ 艙壁銅皮（橡木框、門洞）、靠船殼那一側包銅、
#   松木地板（每 6 格橡木壓條）；火藥桶直立、每 4.6 格、中線 ±3 留走道，第二層放在靠船殼的木架上；≤ 50 格封閉空腔填實、新格都要接到原本的實心。
#   用法：python -I -X utf8 draft_gear.py <design> [--probe=nokind=<模型名>]（反向對照：那一個模型當作沒 meta kind，⛔ 不寫檔）
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
from wio import export_list
from gunsim import Grid, Gun

X_LO, X_HI, Z_LO, Z_HI = 60, 620, 0, 200


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    GB = plan['gear_build']
    MG, SK = GB['magazine'], GB['skids']
    YC = plan['space']['yc']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list(GB['assembly'], None, links=None)
    own = set()
    for w in (MG['work'], SK['work']):
        if os.path.exists(os.path.join(WORKS, w, 'work.json')):
            own |= set(map(tuple, export_list(w, None)[:, :3].tolist()))
    A = np.array([r for r in A.tolist() if tuple(r[:3]) not in own], np.int32)
    occ = np.zeros((X_HI - X_LO, 2 * YC + 1, Z_HI - Z_LO), bool)
    sel = (A[:, 0] >= X_LO) & (A[:, 0] < X_HI) & (A[:, 2] >= Z_LO) & (A[:, 2] < Z_HI)        # 只拿彈藥庫與小艇架那一帶（艏斜桅、桅頂不用）
    occ[A[sel, 0] - X_LO, A[sel, 1], A[sel, 2] - Z_LO] = True
    C = MG['colors']
    COPPER, OAK, DARK, PINE = C['copper'], C['oak'], C['dark'], C['pine']
    X0, X1, F, ZTOP = MG['x0'], MG['x1'], MG['floor'], MG['ztop']

    # ── 彈藥庫：每個 x 的橫切面，z F..ZTOP 之間、中線兩側最近的空氣（4 連通）──
    interior, log = {}, []
    for x in range(X0, X1 + 1):
        air = ~occ[x - X_LO]
        band = np.zeros_like(air)
        band[:, F - Z_LO:ZTOP + 1 - Z_LO] = air[:, F - Z_LO:ZTOP + 1 - Z_LO]
        lab, _ = ndimage.label(band)
        I = np.zeros_like(band)
        seeds = []
        for sgn in (-1, 1):
            ys = [y for y in range(YC, YC + sgn * 80, sgn) if 0 <= y < band.shape[0] and band[y, F + 1 - Z_LO]]
            if ys:
                I |= lab == lab[ys[0], F + 1 - Z_LO]
                seeds.append(ys[0])
        interior[x] = I
        ys, zs = np.nonzero(I)
        log.append({'x': x, 'cells': int(I.sum()), 'y': [int(ys.min()), int(ys.max())] if len(ys) else None, 'seeds': seeds})
    mag = {}
    dw, dh = MG['door_w'], MG['door_head']
    door_x = X1 if MG['door'] == 'fore' else X0
    for x, I in interior.items():
        wall = x in (X0, X1)
        for y, zi in zip(*np.nonzero(I)):
            y, z = int(y), int(zi) + Z_LO
            if z == F:
                mag[(x, y, z)] = OAK if (y - YC) % 6 == 0 else PINE                 # 地板：松木、每 6 格橡木壓條
            elif wall:
                if x == door_x and abs(y - YC) <= dw // 2 and z <= ZTOP - dh:
                    continue                                                       # 門洞
                frame = (y - YC) % 8 == 0 or z == F + 1 or z == ZTOP
                if x == door_x and (abs(y - YC) == dw // 2 + 1 and z <= ZTOP - dh + 1 or abs(y - YC) <= dw // 2 and z == ZTOP - dh + 1):
                    frame = True
                mag[(x, y, z)] = OAK if frame else COPPER
            else:
                side = any(not (0 <= y + d < I.shape[0]) or (not I[y + d, zi] and occ[x - X_LO, y + d, zi]) for d in (-1, 1))
                if side and abs(y - YC) > 6:
                    mag[(x, y, z)] = COPPER                                        # 靠船殼那一側包銅
    free = set()
    for x, I in interior.items():
        for y, zi in zip(*np.nonzero(I)):
            k = (x, int(y), int(zi) + Z_LO)
            if F + 1 <= k[2] <= ZTOP and k not in mag:
                free.add(k)
    # 火藥桶（直立；第二層放在靠船殼的階梯木架上；排到 cap 就停）
    B = MG['barrel']
    R = B['d'] * B['mpv'] / 0.1 / 2
    H = B['h'] * B['mpv'] / 0.1
    barrels, rack, capacity = [], {}, []

    def foot(cx, cy):
        return [(x, y) for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R))) for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)))]

    def body_free(cx, cy, z0):
        # 格心離桶軸 ≤ R ＋ 0.75 的格都要空（一格碰得到半徑 R 的圓，格心距離最遠到 R ＋ 0.71；夜燈號的 R ＋ 0.3 ⇒ v2 還有 10 個桶擦到銅皮與木架）
        return all((x, y, z) in free and (x, y, z) not in rack for x in range(int(math.floor(cx - R - 1)), int(math.ceil(cx + R + 1)))
                   for y in range(int(math.floor(cy - R - 1)), int(math.ceil(cy + R + 1))) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= (R + 0.75) ** 2
                   for z in range(int(math.floor(z0)), int(math.ceil(z0 + H))))

    def under_barrel(x, y, z, t_now):
        return any(b['tier'] < t_now and b['at'][2] <= z < b['at'][2] + H and (x + 0.5 - b['at'][0]) ** 2 + (y + 0.5 - b['at'][1]) ** 2 <= R ** 2 for b in barrels)

    def in_barrel(x, y, z):
        """這一格（格心）在不在已經放下的桶身裡 —— 桶是模型、不在格子裡（v1 第二層木架的立柱往下長進了底層的桶身）。"""
        return any(z < b['at'][2] + H and z + 1 > b['at'][2] and (x + 0.5 - b['at'][0]) ** 2 + (y + 0.5 - b['at'][1]) ** 2 <= (R + 0.75) ** 2 for b in barrels)

    for t in range(0, 4):
        n_t = 0
        cx = X0 + 2 + R
        while cx + R <= X1 - 1:
            z0 = F + 1 + t * B['tier']
            cy = YC + 0.5 + (B['aisle'] + 0.5 + R)
            while abs(cy - YC) < 80:                                               # 一次放一對（S 舷 cy、P 舷鏡過去 2·YC ＋ 1 − cy）⇒ 桶與木架兩舷對稱（v1 排到 cap 停在第二層一半 ⇒ 木架只鋪一邊）
                pair = [(cy, 1), (2 * YC + 1 - cy, -1)]
                shelf = {s: [(x, y, int(z0) - 1) for x, y in foot(cx, c)] if t else [] for c, s in pair}
                ok = all(body_free(cx, c, z0) and all(p in free and p not in rack and not under_barrel(*p, t) for p in shelf[s]) for c, s in pair)
                posts = {}
                if ok and t:
                    # 立柱：架板底下的格裡、一路通到地板都沒有桶、沒有別的木架的那幾欄，取兩根（相距最遠）；找不到兩根 ⇒ 這一對不放
                    #   （v3 只試靠走道的兩角、被底層的桶擋住就停 ⇒ 6 塊架板浮空 —— 造船規格 §8：桶是模型，架板以格子來看會浮空）
                    def post_ok(x, y):
                        return all((x, y, z) in free and (x, y, z) not in rack and not in_barrel(x, y, z) for z in range(F + 1, int(z0) - 1))
                    col = sorted((x, y) for x, y, _ in shelf[1] if post_ok(x, y))
                    best = max(((a, b) for a in col for b in col), key=lambda ab: ((ab[0][0] - ab[1][0]) ** 2 + (ab[0][1] - ab[1][1]) ** 2, ab), default=None)
                    if not best or best[0] == best[1]:
                        ok = False
                    else:
                        posts[1] = sorted(set(best))
                        posts[-1] = [(x, 2 * YC - y) for x, y in posts[1]]          # P 舷照 S 舷鏡過去（v4 兩舷各挑最遠的兩格、平手各挑各的 ⇒ 鏡像差 300）
                        ok = all(post_ok(x, y) for x, y in posts[-1])
                if ok:
                    n_t += 2
                    if len(barrels) + 2 <= MG['cap']:
                        for c, s in pair:
                            barrels.append({'at': [round(cx, 3), round(c, 3), round(z0, 3)], 'tier': t})
                            for p in shelf[s]:
                                rack[p] = OAK
                            for px, py in posts.get(s, []):
                                for z in range(F + 1, int(z0) - 1):
                                    rack[(px, py, z)] = DARK
                elif not t:
                    break
                cy += B['pitch']
            cx += B['pitch']
        capacity.append(n_t)
        if not n_t and t:
            break
    assert not set(rack) & set(mag)
    mag.update(rack)
    free -= set(rack)

    # ── 小艇架：兩座橫架（橫樑 2 格寬 2 格高、兩根 2×2 立柱落到甲板）──
    skids = {}
    for xs in SK['xs']:
        for x in (xs, xs + 1):
            for y in range(YC - SK['y_half'], YC + SK['y_half'] + 1):
                for z in (SK['beam_z'], SK['beam_z'] + 1):
                    skids[(x, y, z)] = SK['color']
            for py in (YC - SK['post_dy'], YC - SK['post_dy'] + 1, YC + SK['post_dy'] - 1, YC + SK['post_dy']):
                z = SK['beam_z'] - 1
                while z > 0 and not occ[x - X_LO, py, z - Z_LO]:
                    skids[(x, py, z)] = SK['color']
                    z -= 1

    new = dict(mag)
    clash = [k for k in skids if k in new]
    new.update(skids)
    on_solid = [k for k in new if occ[k[0] - X_LO, k[1], k[2] - Z_LO]]
    # 封閉空腔（≤ 50 格填實）＋ 新格都要接到原本的實心（彈藥庫、小艇架各量一次）
    sealed, floating = [], []
    for nm, part, (xa, xb, za, zb) in (('magazine', mag, (X0 - 2, X1 + 2, F - 2, ZTOP + 3)), ('skids', skids, (min(SK['xs']) - 2, max(SK['xs']) + 3, 80, SK['beam_z'] + 4))):
        sub = occ[xa - X_LO:xb + 1 - X_LO, :, za - Z_LO:zb + 1 - Z_LO].copy()
        nw = np.zeros_like(sub)
        for (x, y, z) in part:
            if xa <= x <= xb and za <= z <= zb:
                nw[x - xa, y, z - za] = True
        solid = sub | nw
        lab, n = ndimage.label(~solid)
        edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
        for L in range(1, n + 1):
            if L in edge:
                continue
            xs_, ys_, zs_ = np.nonzero(lab == L)
            if len(xs_) > 50:
                sealed.append([nm, 'big', int(len(xs_)), int(xs_.min()) + xa, int(ys_.min()), int(zs_.min()) + za])
                continue
            for x, y, z in zip(xs_, ys_, zs_):
                part[(int(x) + xa, int(y), int(z) + za)] = OAK
                nw[x, y, z] = True
            sealed.append([nm, 'filled', int(len(xs_)), int(xs_.min()) + xa, int(ys_.min()), int(zs_.min()) + za])
        solid = sub | nw
        lab, n = ndimage.label(solid)
        anchored = set(np.unique(lab[sub])) - {0}
        fl = [int(L) for L in np.unique(lab[nw]) if L not in anchored]
        floating += [[nm, (np.argwhere(lab == L).min(axis=0) + [xa, 0, za]).tolist()] for L in fl]

    # ── 模型 ──
    cells_all = np.concatenate([A[:, :3], np.array(sorted(mag) + sorted(skids), np.int32).reshape(-1, 3)])
    G = Grid(cells_all)
    deck_top = {}
    rows = []
    cache = {}

    def src(w):
        if w not in cache:
            cache[w] = export_list(w, None)
        return cache[w]

    def model(m, at):
        return Gun(m['name'], {'work': m['work'], 'scale': m['scale'], 'pivot': m['pivot'], 'meta': m['meta']}, src(m['work']), {}, 0.2)

    def footcheck(g, at, rot):
        lo, hi = g.bbox(at, rot, False)
        cx, cy, fz = int(math.floor((lo[0] + hi[0]) / 2)), int(math.floor((lo[1] + hi[1]) / 2)), int(math.floor(lo[2])) - 1
        for d in range(0, GB['foot_reach'] + 1):
            if G.solid(cx, cy, fz - d):
                return d
        return None

    for m in GB['models']:
        g = model(m, None)
        at = list(m['at'])
        if at[2] is None:
            bot = g.world(g.bottom, (at[0], at[1], 0.0), m['rotate'], False)
            if m['host'] not in deck_top:
                tp = {}
                for x, y, z in export_list(m['host'], None)[:, :3].tolist():
                    tp[(x, y)] = max(tp.get((x, y), -1), z)
                deck_top[m['host']] = tp
            tp = deck_top[m['host']]
            under = [tp[c] for c in set(map(tuple, np.floor(bot[:, :2]).astype(int).tolist())) if c in tp]
            z0 = min(under) + 1                                                    # 從所在甲板子作品的頂往上找（⛔ 從低處掃 ⇒ 13 格高的絞盤會先落進底艙）
            z = z0
            for z in range(z0, z0 + 30):
                P = g.world(g.samples, (at[0], at[1], float(z)), m['rotate'], False)
                if G.hit(P).any():
                    continue
                below = bot.copy()
                below[:, 2] = z - 0.5
                if G.hit(below).any():
                    break
            at[2] = float(z)
        rows.append({'name': m['name'], 'host': m['host'], 'work': m['work'], 'at': [float(v) for v in at], 'pivot': m['pivot'], 'scale': m['scale'], 'rotate': m['rotate'], 'meta': m['meta']})
    for i, b in enumerate(barrels):
        rows.append({'name': '桶-%03d' % (i + 1), 'host': MG['work'], 'work': B['work'], 'at': b['at'], 'pivot': B['pivot'], 'scale': B['scale'], 'rotate': 0,
                     'meta': {'kind': 'powder', 'powder_lb': 100}, 'tier': b['tier']})
    if probe:
        nm = probe[0].split('=', 1)[1]
        for r in rows:
            if r['name'] == nm:
                r['meta'] = {k: v for k, v in r['meta'].items() if k != 'kind'}
    # 讀數：每個模型撞實心的樣本、腳下 12 格內有沒有實心、彼此重疊、meta 有沒有 kind
    coll, nofoot, nokind, mm = {}, [], [], {}
    for r in rows:
        g = model(r, None)
        P = g.world(g.samples, r['at'], r['rotate'], False)
        k = int(G.hit(P).sum())
        if k:
            coll[r['name']] = k
        d = footcheck(g, r['at'], r['rotate'])
        if d is None:
            nofoot.append(r['name'])
        r['foot_gap'] = d
        if 'kind' not in r['meta']:
            nokind.append(r['name'])
        r['_g'] = g
        r['_box'] = g.bbox(r['at'], r['rotate'], False)
    # 模型彼此重疊：外框相交的每一對，把 a 的格心換回 b 自己的格子座標、看落不落在 b 的格子裡（v1 用世界格取整 ⇒ 相距 0.2 格的兩個桶全報重疊）
    overlap = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            (alo, ahi), (blo, bhi) = a['_box'], b['_box']
            if np.any(ahi <= blo) or np.any(bhi <= alo):
                continue
            gb = b['_g']
            P = a['_g'].world(a['_g'].centers, a['at'], a['rotate'], False)
            q = P - np.array(b['at'], float)
            c, s = math.cos(math.radians(-b['rotate'])), math.sin(math.radians(-b['rotate']))
            loc = np.stack([q[:, 0] * c - q[:, 1] * s, q[:, 0] * s + q[:, 1] * c, q[:, 2]], -1) / gb.scale + gb.pivot
            cells_b = set(map(tuple, gb.cells.astype(int).tolist()))
            k = sum(1 for t_ in np.floor(loc).astype(int).tolist() if tuple(t_) in cells_b)
            if k:
                overlap.append([a['name'], b['name'], k])
    for r in rows:
        r.pop('_g'); r.pop('_box')
    cen = np.array(sorted(free)).mean(axis=0)
    blast = min(free, key=lambda p: sum((p[i] - cen[i]) ** 2 for i in range(3)))
    door = (door_x, YC, F + 1)
    kinds = {}
    for r in rows:
        kinds[r['meta'].get('kind')] = kinds.get(r['meta'].get('kind'), 0) + 1
    v = {'read': {'assembly_voxels_minus_own': int(len(A))},
         'magazine': {'cells': len(mag), 'colors': {str(c): sum(1 for q in mag.values() if q == c) for c in sorted(set(mag.values()))}, 'air_inside': len(free),
                      'barrels': len(barrels), 'cap': MG['cap'], 'capacity_per_tier': capacity, 'tiers': [sum(1 for b in barrels if b['tier'] == t) for t in range(4)],
                      'rack': len(rack), 'powder_lb': len(barrels) * 100, 'blast': list(blast), 'door': list(door),
                      'x_skipped': [r['x'] for r in log if not r['cells']]},
         'skids': {'cells': len(skids)},
         'new_on_solid': len(on_solid), 'mag_skids_clash': len(clash), 'sealed': sealed, 'floating': floating,
         'models': len(rows), 'kinds': kinds, 'model_collisions': coll, 'no_foot_within_12': nofoot, 'no_kind': nokind, 'model_overlap': overlap[:10], 'model_overlap_pairs': len(overlap),
         'gear_at': {r['name']: [r['at'], r['foot_gap']] for r in rows if r['host'] != MG['work']},
         'mirror_diff': {'magazine': sum(1 for (x, y, z), c in mag.items() if mag.get((x, 2 * YC - y, z)) != c),
                         'skids': sum(1 for (x, y, z), c in skids.items() if skids.get((x, 2 * YC - y, z)) != c)}}
    if probe:
        print(json.dumps({'probe': probe[0], 'no_kind': nokind}, ensure_ascii=False))
        return
    out = os.path.join(design, 'masks', 'gear')
    os.makedirs(out, exist_ok=True)
    lists = {}
    for nm, part, head in (('magazine', mag, '# 收穫號 彈藥庫（世界座標、at 0,0,0）\n'), ('skids', skids, '# 收穫號 小艇架（世界座標、at 0,0,0）\n')):
        p = os.path.join(out, nm + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for (x, y, z), c in sorted(part.items()):
                f.write('%d,%d,%d,%d\n' % (x, y, z, c))
        lists[nm] = [len(part), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    v['lists'] = lists
    place = {'note': 'draft_gear.py 的結果；模型 at ＝ pivot 落點（世界座標；host 子作品都在 0,0,0）',
             'magazine': {'work': MG['work'], 'anchors': {'blast': list(blast), 'door': list(door)}, 'meta': {'kind': 'magazine', 'pos': MG['pos'], 'powder_lb': len(barrels) * 100}},
             'models': rows}
    json.dump(place, open(os.path.join(design, 'gear_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(design, 'verify_gear.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k not in ('gear_at',)}, ensure_ascii=False))
    print(json.dumps(v['gear_at'], ensure_ascii=False))


if __name__ == '__main__':
    main()
