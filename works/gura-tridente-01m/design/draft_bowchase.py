# 三叉戟號 船頭追擊砲門＋三叉戟砲（TASK-0578）—— 只動船頭這一塊，已驗收的其他部分不碰
#   ① 上砲甲板第 18 個舷側砲門還回 12 磅（v1 借它放船頭追擊砲、只偏得了 5°）：只重算這兩門；現況 ＝ 整艘船扣掉這兩門自己（模型與它們的砲具）
#   ② 每層（plan bowchase.decks）每舷一個船頭砲門：照角度 θ（砲軸從 +x 往外偏的角）試，在那一層砲門中段高度的船頭輪廓上找「表面朝向」最接近 θ 的那一點 Q，
#      沿砲軸把船殼刻穿（寬 w、高 h、sill 照那一層）；刻的範圍裡只准有船殼的格（別的關聯擋著 ⇒ 換角度）
#   ③ 三叉戟砲（gura-tridente-01m-gun-trident，scale 0.5）：從 Q 沿砲軸往裡退（每 0.5 格、橫移 ±1.5、高度兩檔），格心＋八角不落在實心／其他模型外框／別門砲；
#      要求輪子全著地、中管砲口伸出 Q ≥ 0.5、三根管的砲口往前 fire_clear 格內沒有實心（不然船頭欄杆擋砲火）⇒ 取第一個角度全過的
#   S 舷算、P 舷鏡像（船頭兩舷對稱：格 y ↔ 400 − y、連續座標 y ↔ 401 − y；模型 mirror=y、rotate 取負）。
#   輸出：masks/bowchase/hull_carve.vox.txt（帶色，carvevox 顏色守門）、verify_bowchase.json。用法：python -I -X utf8 draft_bowchase.py <design>
import sys, os, json, math, hashlib, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import deco_base as DB

NX, NY, NZ = 1100, 400, 260
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace(os.sep, '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    v = np.atleast_2d(v)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    WORKS = os.path.dirname(os.path.dirname(D))
    plan = HL.load_plan(D)
    BC = plan['bowchase']
    VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
    VF = json.load(open(os.path.join(D, 'verify_gunfittings.json'), encoding='utf-8'))
    VI = json.load(open(os.path.join(D, 'verify_implements.json'), encoding='utf-8'))
    hide = BC.get('hide_links', '')
    A = DB.export_list(DB.ASM, 'all', (('hide_links=' + hide),) if hide else ())
    A = A[A[:, 2] < NZ]
    vox = np.zeros((NX, NY, NZ), bool)
    vox[A[:, 0], A[:, 1], A[:, 2]] = True
    H = DB.export_list(DB.ASM, '船殼')
    hcol = {}
    hull = np.zeros((NX, NY, NZ), bool)
    for x, y, z, c in H[H[:, 2] < NZ].tolist():
        hull[x, y, z] = True
        hcol[(x, y, z)] = c
    # 換掉的那兩門：它們自己的砲具（環、rammer／sponge）不算擋（之後跟著新砲重量）
    redo = {('甲板-%s' % d, m) for d, m in (r.split('/') for r in BC['redo_broadside'])}
    own = set()
    for an in VF['anchors']:
        if (an['deck'], an['gun'].split('/')[1]) in redo:
            own.add(tuple(an['world']))
    for row in VI['rows']:
        d, m = row['gun'].split('/')
        if (d, m) in redo:
            for k in ('rammer', 'sponge'):
                v = row.get(k)
                if v:
                    for y in range(v['y'][0], v['y'][1] + 1):
                        own.add((v['x'], y, v['z']))
                    for y in (v['y'][0], v['y'][1]):
                        own.add((v['x'], y, v['z'] - 1))
    for p in own:
        vox[p] = False                                                   # rammer 頭底下那一層多扣了也無妨（只在那兩門頭上）
    occ = vox.copy()
    nbox = 0
    for m in parts():
        if (m.get('meta') or {}).get('kind') == 'gun':
            continue
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
        nbox += 1
    src = {}

    def load_type(t, work, scale):
        if t not in src:
            C = DB.export_list(work, None)
            an = {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, work, 'anchors.json'), encoding='utf-8'))['anchors']}
            bot = C[C[:, 2] == 0]
            ax = an['muzzle'][0] + 0.5
            src[t] = {'samp': (C[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3), 'an': an, 'work': work, 'scale': scale,
                      'bs': np.array([[x + ox, y + oy, 0.5] for x, y, _ in bot[:, :3] for ox in (0.3, 0.7) for oy in (0.3, 0.7)]),
                      'piv': np.array([ax, float(bot[:, 1].max() + 1), 0.0])}
        return src[t]

    def world(tp, Q, at, rot, mir):
        q = (np.atleast_2d(Q) - tp['piv']) * tp['scale']
        if mir:
            q[:, 1] = -q[:, 1]
        return rotz(q, rot) + np.asarray(at, float)

    gunocc = np.zeros_like(occ)
    for r in VG['rows']:
        if (r['host_link'], r['model']) in redo:
            continue
        tp = load_type(r['type'], r['work'], r['scale'])
        w = np.floor(world(tp, tp['samp'], r['at'], r['rotate'][2], r['mirror'] == 'y')).astype(int)
        gunocc[w[:, 0], w[:, 1], w[:, 2]] = True

    def free(tp, at, rot, mir, extra=None):
        w = np.floor(world(tp, tp['samp'], at, rot, mir)).astype(int)
        ok = (w[:, 0] >= 0) & (w[:, 0] < NX) & (w[:, 1] >= 0) & (w[:, 1] < NY) & (w[:, 2] >= 0) & (w[:, 2] < NZ)
        if not ok.all():
            return False
        g = occ[w[:, 0], w[:, 1], w[:, 2]] | gunocc[w[:, 0], w[:, 1], w[:, 2]]
        if extra is not None:
            g &= ~extra[w[:, 0], w[:, 1], w[:, 2]]
        return not g.any()

    def support(tp, at, rot, mir):
        b = np.floor(world(tp, tp['bs'], at, rot, mir)).astype(int)
        return [int(vox[b[:, 0], b[:, 1], b[:, 2] - 1].sum()), len(b)]

    def padding(tp, at, rot, mir):
        """輪底懸空的取樣 ⇒ 往下補到碰到實心（≤ 2 格）的格；墊不起來 ⇒ None（同第八階段的墊木：甲板舷弧在船頭往上翹）。"""
        b = np.floor(world(tp, tp['bs'], at, rot, mir)).astype(int)
        cells = set()
        for x, y, z in {tuple(v) for v in b.tolist()}:
            k = 0
            while not vox[x, y, z - 1 - k]:
                k += 1
                if k > 2:
                    return None
            for j in range(k):
                cells.add((x, y, z - 1 - j))
        return cells

    def commit(tp, at, rot, mir):
        w = np.floor(world(tp, tp['samp'], at, rot, mir)).astype(int)
        gunocc[w[:, 0], w[:, 1], w[:, 2]] = True

    # ① 上砲甲板第 18 門還回 12 磅（同 draft_guns 的搜法，只做這兩門）
    SR = plan['guns']['search']
    rows_redo = []
    for r in VG['rows']:
        if (r['host_link'], r['model']) not in redo:
            continue
        deck = r['host_link'].split('-')[1]
        typ = plan['guns']['rows'][deck]
        T = plan['guns']['types'][typ]
        tp = load_type(typ, T['work'], T['scale'])
        side = 1 if r['meta']['side'] == 'S' else -1
        xc = (r['port_x'][0] + r['port_x'][1] + 1) / 2.0
        dz = float(LY.deck_z(plan, deck, xc))
        o = r['outer']
        best = None
        for dl in SR['dl']:
            for zi, dzz in enumerate(SR['dz']):
                for kb in range(int(SR['max_back'] / SR['step']) + 1):
                    back = kb * SR['step']
                    at = [xc + dl, o - side * back, dz + dzz]
                    if not free(tp, at, 0, side < 0):
                        continue
                    tip = world(tp, np.array(tp['an']['muzzle'], float) + 0.5, at, 0, side < 0)[0]
                    sup = support(tp, at, 0, side < 0)
                    out = float((tip[1] - o) * side)
                    k = (sup[0] < sup[1], out < SR['min_muzzle_out'], abs(dl), zi, back)
                    if best is None or k < best[0]:
                        best = (k, {'at': [round(v, 3) for v in at], 'dl': dl, 'back': back, 'support': sup, 'muzzle_out': round(out, 3),
                                    'muzzle': [round(float(v), 3) for v in tip],
                                    'breech': [round(float(v), 3) for v in world(tp, np.array(tp['an']['breech'], float) + 0.5, at, 0, side < 0)[0]]})
                    break
        assert best and not best[0][0] and not best[0][1], ('第 18 門還回 12 磅擺不好', r['model'], best and best[0])
        c = best[1]
        commit(tp, c['at'], 0, side < 0)
        meta = {'kind': 'gun', 'gun': T['code'], 'side': r['meta']['side'], 'port': r['meta']['port'], 'deck': deck}
        nr = dict(r)
        nr.update({'type': typ, 'work': T['work'], 'scale': T['scale'], 'pivot': tp['piv'].tolist(), 'rotate': [0, 0, 0], 'meta': meta, **c})
        rows_redo.append(nr)

    # 船頭裝飾（一舷子作品 ＋ 鏡像關聯）：刻門的範圍裡碰到它的格 ⇒ 一起刻（只刻 S 舷那一件 ⇒ 鏡像那一舷跟著）
    HSL = BC['head_side']
    HS = DB.export_list(HSL['work'], None)
    hs_at = np.array(HSL['at'])
    head = {(int(x + hs_at[0]), int(y + hs_at[1]), int(z + hs_at[2])): int(c) for x, y, z, c in HS.tolist()}
    carve_head = {}
    # knee（含 beakhead 格柵平台；一整件、沒有鏡像）：平台高度剛好是上砲甲板砲門下緣、邊緣貼著船殼 ⇒ 門口碰到的那幾格一起刻、兩舷各刻
    KN = BC['knee']
    KK = DB.export_list(KN['work'], None)
    kn_at = np.array(KN['at'])
    knee = {(int(x + kn_at[0]), int(y + kn_at[1]), int(z + kn_at[2])): int(c) for x, y, z, c in KK.tolist()}
    carve_knee = {}
    pads_by = {}
    # ② ③ 船頭砲門＋三叉戟砲
    TT = BC['trident']
    tp = load_type('trident', TT['work'], TT['scale'])
    YC = plan['space']['yc']
    carve = {}
    rows_tri, log = [], []
    for D_ in BC['decks']:
        deck = D_['deck']
        got = None
        tries = []
        for th in BC['angles']:
            xq = D_['x_hint']
            floor = int(LY.deck_z(plan, deck, xq)) + 1                    # 甲板面上第一層空氣
            z0, z1 = floor + D_['sill'], floor + D_['sill'] + D_['h'] - 1
            zm = (z0 + z1) // 2
            ys = list(range(YC + 2, YC + 90))
            f = {}
            for y in ys:
                xs = np.nonzero(hull[:, y, zm])[0]
                xs = xs[xs > 500]
                if len(xs):
                    f[y] = int(xs.max())
            phi = {}
            for y in f:
                if y - 2 in f and y + 2 in f:
                    dfdy = (f[y + 2] - f[y - 2]) / 4.0
                    phi[y] = math.degrees(math.atan2(-dfdy, 1.0))
            if not phi:
                tries.append([th, '量不到輪廓'])
                continue
            ys_ = sorted([y for y in phi if y >= YC + D_['dy_min']], key=lambda y: (abs(phi[y] - th), y))
            if not ys_:
                tries.append([th, '離中線 %d 以外量不到輪廓' % D_['dy_min']])
                continue
            y0 = ys_[0]
            d = np.array([math.cos(math.radians(th)), math.sin(math.radians(th)), 0.0])
            n = np.array([-d[1], d[0], 0.0])
            Q = np.array([f[y0] + 1.0, y0 + 0.5, zm + 0.5])
            # 刻的範圍：沿砲軸 −depth..＋2、橫向 |l| ≤ w/2、z0..z1
            cs, block, ch, ck = [], [], [], []
            for x in range(int(Q[0]) - 20, int(Q[0]) + 6):
                for y in range(int(Q[1]) - 20, int(Q[1]) + 20):
                    for z in range(z0, z1 + 1):
                        v = np.array([x + 0.5, y + 0.5, z + 0.5]) - Q
                        u, l = float(v @ d), float(v @ n)
                        # 只刻到船殼外表面（u ≤ 0.5）：🩸 v1 刻到外面 ＋2 ⇒ 上砲甲板那一層貼在船頭外面的 cheek、head rails、beakhead 平台都算進「刻的範圍」⇒ 每個角度都被擋
                        if abs(l) <= D_['w'] / 2.0 and -BC['carve_depth'] <= u <= 0.5:
                            if hull[x, y, z]:
                                cs.append((x, y, z))
                            elif (x, y, z) in head:
                                ch.append((x, y, z))
                            elif (x, y, z) in knee:
                                ck.append((x, y, z))
                            elif vox[x, y, z]:
                                block.append((x, y, z))
            if block:
                tries.append([th, '刻的範圍裡有別的關聯 %d 格' % len(block)])
                continue
            hole = np.zeros_like(occ)
            for p in cs + ch + ck:
                hole[p] = True
                hole[(p[0], 2 * YC - p[1], p[2])] = True
            rot = th - 90.0
            if os.environ.get('BC_DEBUG') == deck:
                for back in range(0, 41, 5):
                    at = Q - d * back
                    at = [float(at[0]), float(at[1]), float(floor)]
                    w = np.floor(world(tp, tp['samp'], at, rot, False)).astype(int)
                    vv = vox[w[:, 0], w[:, 1], w[:, 2]] & ~hole[w[:, 0], w[:, 1], w[:, 2]]
                    bb = occ[w[:, 0], w[:, 1], w[:, 2]] & ~vox[w[:, 0], w[:, 1], w[:, 2]]
                    gg = gunocc[w[:, 0], w[:, 1], w[:, 2]]
                    print('  dbg', deck, th, 'Q', [round(float(v), 1) for v in Q], 'back', back, 'vox', int(vv.sum()), 'model-box', int(bb.sum()), 'guns', int(gg.sum()),
                          'hit z', (int(w[vv][:, 2].min()), int(w[vv][:, 2].max())) if vv.any() else None, 'hit x', (int(w[vv][:, 0].min()), int(w[vv][:, 0].max())) if vv.any() else None)
            best = None
            for dl in BC['dl']:
                for zi, dzz in enumerate((0, 1)):
                    for kb in range(int(BC['max_back'] / 0.5) + 1):
                        back = kb * 0.5
                        at = Q + n * dl - d * back
                        # 高度照砲所在那裡的甲板面（🩸 v1 用 x_hint 那裡的 ⇒ 砲退到 x 676 時甲板因舷弧低 1–2 格，輪子懸空 75／80）
                        at = [float(at[0]), float(at[1]), float(int(LY.deck_z(plan, deck, float(at[0]))) + 1 + dzz)]
                        if not free(tp, at, rot, False, hole):
                            continue
                        sup = support(tp, at, rot, False)
                        tips = {k: world(tp, np.array(tp['an'][k], float) + 0.5, at, rot, False)[0] for k in ('muzzle', 'muzzle-a', 'muzzle-b', 'muzzle-c')}
                        out = float((tips['muzzle'] - Q) @ d)
                        fire = 0
                        for k in ('muzzle-a', 'muzzle-b', 'muzzle-c'):
                            for s in np.arange(1.0, BC['fire_clear'], 0.5):
                                p = np.floor(tips[k] + d * s).astype(int)
                                if (occ[tuple(p)] or gunocc[tuple(p)]) and not hole[tuple(p)]:
                                    fire += 1
                        pads = padding(tp, at, rot, False)                 # None ＝ 墊不起來（懸空的輪底往下 2 格內沒有實心）
                        k_ = (pads is None, out < 0.5, fire > 0, sup[0] < sup[1], abs(dl), zi, back)
                        if best is None or k_ < best[0]:
                            best = (k_, {'at': [round(v, 3) for v in at], 'dl': dl, 'back': back, 'support': sup, 'muzzle_out': round(out, 3), 'fire_blocked': fire,
                                         'pads': sorted(pads) if pads else [],
                                         'muzzle': [round(float(v), 3) for v in tips['muzzle']],
                                         'breech': [round(float(v), 3) for v in world(tp, np.array(tp['an']['breech'], float) + 0.5, at, rot, False)[0]]})
                        break
            if best is None or best[0][0] or best[0][1] or best[0][2]:
                tries.append([th, '砲擺不好 %s' % (best and best[0][:3],)])
                continue
            got = (th, Q, cs, best[1], rot, z0, z1, y0, ch, ck)
            tries.append([th, 'ok'])
            break
        log.append({'deck': deck, 'tries': tries})
        if not got:
            continue
        th, Q, cs, c, rot, z0, z1, y0, ch, ck = got
        for p in ch:
            carve_head[p] = head[p]
        for p in ck:
            pm = (p[0], 2 * YC - p[1], p[2])
            assert pm in knee, ('knee 兩舷不對稱', p)
            carve_knee[p] = knee[p]
            carve_knee[pm] = knee[pm]
        for p in cs:
            carve[p] = hcol[p]
            pm = (p[0], 2 * YC - p[1], p[2])
            assert hull[pm], ('船頭兩舷不對稱', p)
            carve[pm] = hcol[pm]
        commit(tp, c['at'], rot, False)
        atP = [c['at'][0], round(2 * YC + 1 - c['at'][1], 3), c['at'][2]]
        hole = np.zeros_like(occ)
        for p in list(carve) + list(carve_knee) + list(carve_head) + [(q[0], 2 * YC - q[1], q[2]) for q in carve_head]:
            hole[p] = True
        p_free = free(tp, atP, -rot, True, hole)                          # 鏡像那一舷也真的量一次（船頭兩舷對稱是假設，不是讀數）
        p_sup = support(tp, atP, -rot, True)
        p_pads = padding(tp, atP, -rot, True)
        assert p_pads is not None, ('P 舷墊不起來', deck)
        col = plan['decks_build']['plank']['weather' if deck in ('spar', 'poop') else 'gun']
        for p in list(c['pads']) + sorted(p_pads):
            pads_by.setdefault(deck, {})[tuple(p)] = col
            vox[tuple(p)] = True
        commit(tp, atP, -rot, True)
        for sd, at, rr, mir in (('S', c['at'], rot, False), ('P', atP, -rot, True)):
            mu = world(tp, np.array(tp['an']['muzzle'], float) + 0.5, at, rr, mir)[0]
            br = world(tp, np.array(tp['an']['breech'], float) + 0.5, at, rr, mir)[0]
            rows_tri.append({'model': '三叉戟砲-%s' % sd, 'host_link': '甲板-' + deck, 'host_work': 'gura-tridente-01m-deck-' + deck, 'type': 'trident',
                             'work': TT['work'], 'scale': TT['scale'], 'pivot': tp['piv'].tolist(), 'rotate': [0, 0, round(rr, 3)], 'mirror': 'y' if mir else 'none',
                             'at': at, 'angle_deg': th, 'Q': [round(float(v), 3) for v in (Q if sd == 'S' else [Q[0], 2 * YC + 1 - Q[1], Q[2]])],
                             'port_z': [z0, z1], 'support': c['support'] if sd == 'S' else p_sup, 'free': True if sd == 'S' else p_free,
                             'pad_cells': len(c['pads']) if sd == 'S' else len(p_pads),
                             'muzzle_out': c['muzzle_out'], 'fire_blocked': c['fire_blocked'],
                             'muzzle': [round(float(v), 3) for v in mu], 'breech': [round(float(v), 3) for v in br],
                             'meta': {'kind': 'gun', 'gun': TT['code'], 'barrels': 3, 'arc': 'bow', 'side': sd, 'deck': deck}})
    os.makedirs(os.path.join(D, 'masks', 'bowchase'), exist_ok=True)
    pad_files = {}
    for deck, cells in sorted(pads_by.items()):
        fn = 'masks/bowchase/pads_%s.vox.txt' % deck
        t_ = '# 三叉戟號 三叉戟砲的墊木（draft_bowchase.py）x,y,z,color —— gura-tridente-01m-deck-%s，at 0,0,0\n' % deck + \
             ''.join('%d,%d,%d,%d\n' % (p + (c,)) for p, c in sorted(cells.items()))
        open(os.path.join(D, fn), 'w', encoding='utf-8', newline='\n').write(t_)
        pad_files['gura-tridente-01m-deck-' + deck] = {'file': fn, 'voxels': len(cells), 'sha256': hashlib.sha256(t_.encode('utf-8')).hexdigest()}
    txt = '# 三叉戟號 船頭追擊砲門 刻除清單（draft_bowchase.py）x,y,z,color（color ＝ 刻之前那一格的顏色，carvevox 顏色守門）\n' + \
          ''.join('%d,%d,%d,%d\n' % (p + (c,)) for p, c in sorted(carve.items()))
    open(os.path.join(D, 'masks', 'bowchase', 'hull_carve.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
    txt_h = '# 三叉戟號 船頭追擊砲門 船頭裝飾刻除清單（draft_bowchase.py）—— %s 子作品座標 x,y,z,color（顏色守門；鏡像關聯那一舷跟著）\n' % HSL['work'] + \
            ''.join('%d,%d,%d,%d\n' % (p[0] - hs_at[0], p[1] - hs_at[1], p[2] - hs_at[2], c) for p, c in sorted(carve_head.items()))
    open(os.path.join(D, 'masks', 'bowchase', 'head_side_carve.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt_h)
    txt_k = '# 三叉戟號 船頭追擊砲門 knee（beakhead 平台）刻除清單（draft_bowchase.py）—— %s 子作品座標 x,y,z,color（顏色守門；兩舷都列）\n' % KN['work'] + \
            ''.join('%d,%d,%d,%d\n' % (p[0] - kn_at[0], p[1] - kn_at[1], p[2] - kn_at[2], c) for p, c in sorted(carve_knee.items()))
    open(os.path.join(D, 'masks', 'bowchase', 'knee_carve.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt_k)
    out = {'note': 'draft_bowchase.py —— 現況 ＝ 組裝件 links=all（%d 格）扣掉換掉那兩門的砲具 %d 格 ＋ 其他模型外框 %d ＋ 不換的砲 %d 門' % (len(A), len(own), nbox, len(VG['rows']) - len(redo)),
           'redo_broadside': rows_redo, 'trident': rows_tri, 'carve': {'file': 'masks/bowchase/hull_carve.vox.txt', 'cells': len(carve), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()},
           'carve_head_side': {'file': 'masks/bowchase/head_side_carve.vox.txt', 'work': HSL['work'], 'cells': len(carve_head), 'sha256': hashlib.sha256(txt_h.encode('utf-8')).hexdigest()},
           'pads': pad_files,
           'carve_knee': {'file': 'masks/bowchase/knee_carve.vox.txt', 'work': KN['work'], 'cells': len(carve_knee), 'sha256': hashlib.sha256(txt_k.encode('utf-8')).hexdigest()},
           'log': log, 'counts': {'trident': len(rows_tri), 'carve': len(carve), 'carve_head_side': len(carve_head), 'carve_knee': len(carve_knee), 'redo': len(rows_redo)}}
    with open(os.path.join(D, 'verify_bowchase.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    for r in rows_redo:
        print('還回', r['host_link'], r['model'], r['type'], r['at'], 'support', r['support'], 'out', r['muzzle_out'])
    for L in log:
        print(L['deck'], L['tries'])
    for r in rows_tri:
        print(r['host_link'], r['model'], 'θ', r['angle_deg'], 'at', r['at'], 'rot', r['rotate'][2], 'free', r['free'], 'support', r['support'], 'out', r['muzzle_out'], 'fire', r['fire_blocked'])
    print(out['counts'])


if __name__ == '__main__':
    main()
