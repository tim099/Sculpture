# 新圖紙 16 channels 與靜索 v1（階段十五，TASK-0538）：plan.json standing ＋ 現況 export list
#   ⇒ masks/channels/channels.vox.txt（索具台子作品：只框右舷 y 161–319，關聯 at 0,161,0；左舷 mirror=y at 0,1,0）、
#     rig_points_standing.json（要登記的固定點：桅、艏斜桅、船殼、前甲板、索具台）、standing_ropes.json（繩）、verify_standing.json、sheet16_standing_v1.png
# 用法：python -I draft_standing.py <design> <組裝件 list> <船殼 list> <後甲板・走道・前甲板 list> <後桅 list> <主桅 list> <前桅 list> <艏斜桅 list>
#   · 繩端：固定點一律寫 `關聯/固定點`；deadeye 與 lanyard 的端點是算出來的座標（一律帶小數 ⇒ 照原值，造船規格 §1）。
#   · 左舷 ＝ 右舷鏡過去：索具台走 `索具台-鏡像/…`、桅的 `-S` 換 `-P`、座標 y → 321 − y（格 y ↔ 320 − y 的連續版）。
#   · 每條繩（不算子繩）拿兩端的直線每 0.5 格取樣，離兩端 1.5 格以外的點不准落在組裝件實心裡。
import sys, os, json, hashlib, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402

YC = 160
MASTS = ('mizzen', 'main', 'fore')


def fx(v):
    """座標字串：一律帶小數（整數會被當格心 ⇒ 錯半格）。"""
    s = '%.3f' % v
    if s.endswith('.000'):
        s = '%.3f' % (v + 0.001)
    return s


def pt(p):
    return ','.join(fx(c) for c in p)


def unit(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


class Standing:
    def __init__(s, design, lists):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.S = s.plan['standing']
        s.Y = s.plan['yards']
        s.sha = {k: hashlib.sha256(open(p, 'rb').read()).hexdigest() for k, p in lists.items()}
        s.occ = DP.read_list(lists['assembly'])
        assert len(s.occ) == s.S['assembly_cells'], ('組裝件格數對不上', len(s.occ))
        s.hull = DP.read_list(lists['hull'])
        s.spar = DP.read_list(lists['spar'])
        s.mast = {m: DP.read_list(lists[m]) for m in MASTS}
        s.bow = DP.read_list(lists['bowsprit'])
        s.works = dict(s.Y['works'])
        s.works['bowsprit'] = 'basecamp-nightlamp-01m-bowsprit'
        s.links = dict(s.Y['links'])
        s.links['bowsprit'] = '艏斜桅'
        s.points = []          # {owner, link, name, world}
        s.ropes = []
        s.read = {}
        # 船殼外緣（右舷）：每個 (x, z) 最大的 y
        s.hy = {}
        for (x, y, z) in s.hull:
            if y > YC and y > s.hy.get((x, z), -1):
                s.hy[(x, z)] = y

    def add_point(s, owner_key, name, cell, kind):
        work = {'hull': 'basecamp-nightlamp-01m', 'spar': 'basecamp-nightlamp-01m-deck-spar', 'channels': s.S['channels']['work']}.get(owner_key, s.works.get(owner_key))
        link = {'hull': '船殼', 'spar': '後甲板・走道・前甲板', 'channels': s.S['channels']['link']}.get(owner_key, s.links.get(owner_key))
        o = s.S['channels']['origin'] if owner_key == 'channels' else [0, 0, 0]
        s.points.append({'owner': work, 'link': link, 'name': name, 'kind': kind, 'world': [int(c) for c in cell], 'local': [int(cell[i]) - o[i] for i in range(3)]})
        return link + '/' + name

    @staticmethod
    def c(cell):
        return np.array(cell, float) + 0.5

    # ── 桅上的固定點 ──
    def mast_points(s):
        s.mp = {}
        for m in MASTS:
            M = s.mast[m]
            H = s.Y['heights'][m]
            P = {}

            def layer(z, r):
                return [(x, y) for (x, y, zz) in M if zz == z and abs(y - YC) <= r]

            def sides(z, r, key):
                L = layer(z, r)
                xs = [x for x, y in L if y == YC]
                xc = int(round(sum(xs) / len(xs)))
                ys = [y for x, y in L if x == xc]
                P[key + '-S'] = (xc, max(ys), z)
                P[key + '-P'] = (xc, min(ys), z)
                return xs
            zt = H['top']
            xs = sides(zt - 4, 6, 'shrouds')
            P['stay-out'] = (max(xs), YC, zt - 4)
            zc = H['crosstrees']
            xs = sides(zc - 3, 4, 'tm')
            P['tmstay-out'] = (max(xs), YC, zc - 3)
            zg = H['truck'] - 6
            xs = [x for x, y in layer(zg, 3) if y == YC]
            P['tg-head'] = (int(round(sum(xs) / len(xs))), YC, zg)
            P['tgstay-out'] = (max(xs), YC, zg)
            # top 的邊（z top+1 的黑邊）：前、後、右舷三點（往船尾排）
            rim = [(x, y) for (x, y, z), col in M.items() if z == zt + 1]
            P['top-front'] = (max(x for x, y in rim if y == YC), YC, zt + 1)
            P['top-aft'] = (min(x for x, y in rim if y == YC), YC, zt + 1)
            xa = s.axis_x(m, zt - 4)
            n = s.S['topmast_shrouds'][m]
            for k in range(n):
                xt = int(round(xa)) + 2 - 6 * k
                cand = [(x, y) for x, y in rim if y > YC]
                x0 = min(cand, key=lambda q: (abs(q[0] - xt), -q[1]))[0]
                ymax = max(y for x, y in cand if x == x0)
                P['toprim-S%d' % (k + 1)] = (x0, ymax, zt + 1)
                P['toprim-P%d' % (k + 1)] = (x0, 2 * YC - ymax, zt + 1)
            # crosstrees 兩端（z crosstrees−1 的黑）
            ct = [(x, y) for (x, y, z), col in M.items() if z == zc - 1 and col == 36]
            ymax = max(y for x, y in ct)
            ends = sorted({x for x, y in ct if y == ymax}, reverse=True)
            for k, x0 in enumerate(ends[:2]):
                P['ct-S%d' % (k + 1)] = (x0, ymax, zc - 1)
                P['ct-P%d' % (k + 1)] = (x0, 2 * YC - ymax, zc - 1)
            P['ct-aft'] = (min(x for (x, y, z) in M if z == zc - 1 and y == YC), YC, zc - 1)
            if m == 'main':
                xs = [x for x, y in layer(150, 5) if y == YC]
                P['stay-in-low'] = (min(xs), YC, 150)
            for k, v in P.items():
                assert v in M, (m, k, v, '固定點不在桅的格上')
            s.mp[m] = P
            for k, v in sorted(P.items()):
                s.add_point(m, k, v, 'mast')

    def axis_x(s, m, z):
        xs = [x for (x, y, zz) in s.mast[m] if zz == z and y == YC]
        return (min(xs) + max(xs)) / 2

    # ── 艏斜桅、船頭柱、前甲板 ──
    def bow_points(s):
        B = s.bow
        cap = [(x, z) for (x, y, z), c in B.items() if c == 36 and y == YC]
        cx = int(round(sum(x for x, z in cap) / len(cap)))
        s.bp = {'cap': (cx, YC, max(z for x, z in cap if x == cx)), 'bobstay': (cx, YC, min(z for x, z in cap if x == cx))}
        xm = max(x for (x, y, z) in B if y == YC)
        zs = sorted(z for (x, y, z) in B if x == xm and y == YC)
        s.bp['jibboom-end'] = (xm, YC, zs[len(zs) // 2])
        s.bp['forestay'] = (612, YC, max(z for (x, y, z) in B if x == 612 and y == YC))
        s.bp['fore-tmstay'] = (cx + 8, YC, max(z for (x, y, z) in B if x == cx + 8 and y == YC))
        for k, v in s.bp.items():
            assert v in B, (k, v)
            s.add_point('bowsprit', k, v, 'bowsprit')
        a = s.c(s.bp['bobstay'])
        s.bob_try = []
        for z in range(72, 30, -2):
            xs = max(x for (x, y, zz) in s.hull if y == YC and zz == z)
            h = s.line_hits(a, s.c((xs, YC, z)), s.S['clearance_end_skip'])
            s.bob_try.append([z, xs, h])
            if h == 0:
                break
        assert h == 0, ('bobstay 找不到不穿過的高度', s.bob_try)
        s.stem = (xs, YC, z)
        assert s.stem in s.hull
        s.add_point('hull', 'stem-bobstay', s.stem, 'hull')
        # main-stay 下端：前甲板、前桅右舷旁 —— 前甲板的板（走的那一格底下一格）
        x, y = int(round(s.axis_x('fore', 140))) + 6, YC + 8
        z = max(zz for (xx, yy, zz) in s.spar if xx == x and yy == y)
        s.mainstay = (x, y, z)
        s.add_point('spar', 'mainstay', s.mainstay, 'deck')

    def line_hits(s, a, b, skip):
        L = float(np.linalg.norm(b - a))
        n = 0
        for t in np.arange(skip, L - skip, 0.5):
            q = a + (b - a) * t / L
            if tuple(int(math.floor(v)) for v in q) in s.occ:
                n += 1
        return n

    # ── 索具台（右舷）──
    def channels(s):
        C = s.S['channels']
        s.ch_cells = {}
        s.deadeyes = {}
        s.ch_log = {}
        for m in MASTS:
            G = C['masts'][m]
            xm = int(round(s.axis_x(m, 130)))
            n = G['shrouds'] + G['backstays']
            xk = [xm + G['fwd'] - G['spacing'] * k for k in range(n)]
            z0, z1 = G.get('z', C['z'])
            cells = {}
            for x in range(xk[-1] - 3, xk[0] + 4):
                ho = s.hy[(x, z1)]
                for z in range(z0, z1 + 1):
                    for y in range(s.hy[(x, z)] + 1, ho + G['width'] + 1):
                        cells[(x, y, z)] = C['color']
            dz0, dz1 = G.get('deadeye_z', C['deadeye_z'])
            des = []
            for k, x in enumerate(xk):
                yo = s.hy[(x, z1)] + G['width'] - 1
                for xx in (x - 1, x, x + 1):
                    for yy in (yo - 1, yo):
                        for z in range(dz0, dz1 + 1):
                            cells[(xx, yy, z)] = C['deadeye_color']
                des.append((x, yo, dz1))
            hit = sum(1 for k in cells if k in s.occ)
            s.ch_cells.update(cells)
            s.deadeyes[m] = des
            s.ch_log[m] = {'mast_x_at_130': xm, 'deadeye_x': xk, 'cells': len(cells), 'overlap_existing': hit}
            for k, d in enumerate(des):
                s.add_point('channels', 'dl-%s-%d' % (m, k + 1), d, 'deadeye')
        # 每一欄都貼著船殼（往 −y 一格是船殼）
        bad = [k for k in s.ch_cells if s.ch_cells[k] == C['color'] and (k[0], k[1] - 1, k[2]) not in s.hull and (k[0], k[1] - 1, k[2]) not in s.ch_cells]
        s.read['channel_cells_not_attached'] = len(bad)
        # 擋到砲門：右舷每個砲門開口的 (x, z) 欄、船殼外面那一側有沒有索具台的格
        s.read['channels_overlap_existing'] = sum(1 for k in s.ch_cells if k in s.occ)

    # ── 繩 ──
    def rope(s, name, a, b, slack, color, t, group, meta=None):
        s.ropes.append({'name': name, 'from': a, 'to': b, 'slack': slack, 'color': color, 'thickness': t, 'group': group, 'meta': meta or {}})

    def mirror_end(s, e):
        if isinstance(e, str):
            if e.startswith(s.S['channels']['link'] + '/'):
                return s.S['channels']['link_mirror'] + e[len(s.S['channels']['link']):]
            if e.endswith('-S') or '-S' in e.split('/')[-1]:
                head, tail = e.rsplit('/', 1)
                return head + '/' + tail.replace('-S', '-P')
            return e
        return [e[0], 321 - e[1], e[2]]

    def end_str(s, e):
        return e if isinstance(e, str) else pt(e)

    def world_of(s, e):
        """端點 → 組裝件連續座標（只用來量、畫圖）。"""
        if not isinstance(e, str):
            return np.array(e, float)
        if '/' not in e:
            return np.array([float(v) for v in e.split(',')])
        mir = e.startswith(s.S['channels']['link_mirror'] + '/')
        link, name = e.split('/', 1)
        for p in s.points:
            if p['name'] == name and (p['link'] == link or (mir and p['link'] == s.S['channels']['link'])):
                w = np.array(p['world'], float) + 0.5
                if mir:
                    w[1] = 321 - w[1]
                return w
        raise KeyError(e)

    def deadeye_set(s, base, low_cell, top_end, t, group):
        """下 deadeye（格）→ 上 deadeye（圓盤）→ 繩往上到 top_end。回傳主繩的下端座標。"""
        D = s.S['deadeye']
        L = s.c(low_cell)
        T = s.world_of(top_end)
        u = unit(T - L)
        U = L + D['rise'] * u
        top = U + 1.0 * u
        side = np.array([0.0, 1.0, 0.0])
        s.rope(base + '.deadeye', list(U - side * D['disc_len'] / 2), list(U + side * D['disc_len'] / 2), 1, D['disc_color'], D['disc_d'], 'standing/deadeyes/upper')
        low = U - 1.0 * u
        for tag, dx in (('a', -D['lanyard_spread']), ('b', 0.0), ('c', D['lanyard_spread'])):
            off = np.array([dx, 0, 0])
            s.rope(base + '.lanyard-' + tag, list(L + off + np.array([0, 0, 0.5])), list(low + off), 1, D['lanyard_color'], D['lanyard_t'], 'standing/deadeyes/lanyards')
        return list(top)

    def build_ropes(s):
        S, th, tar = s.S, s.S['thick'], s.S['tar']
        CL = S['channels']['link']
        s.shroud_names = {}
        for m in MASTS:
            G = S['channels']['masts'][m]
            ml = s.links[m]
            des = s.deadeyes[m]
            names = []
            for k in range(G['shrouds']):
                nm = '%s-shroud-S%d' % (m, k + 1)
                low = s.deadeye_set(nm, des[k], ml + '/shrouds-S', th['shroud'][m], 'standing/shrouds')
                s.rope(nm, low, ml + '/shrouds-S', 1, tar, th['shroud'][m], 'standing/shrouds', {'kind': 'shroud'})
                names.append(nm)
            s.shroud_names[m] = names
            for j in range(G['backstays']):
                nm = '%s-backstay-S%d' % (m, j + 1)
                top = ml + ('/tm-S' if j < 2 else '/tg-head')
                low = s.deadeye_set(nm, des[G['shrouds'] + j], top, th['backstay'][m], 'standing/backstays')
                s.rope(nm, low, top, 1, tar, th['backstay'][m], 'standing/backstays', {'kind': 'backstay'})
            for k in range(S['topmast_shrouds'][m]):
                s.rope('%s-tm-shroud-S%d' % (m, k + 1), ml + '/toprim-S%d' % (k + 1), ml + '/tm-S', 1, tar, th['tm_shroud'], 'standing/topmast-shrouds', {'kind': 'shroud'})
            for k in range(S['topgallant_shrouds'][m]):
                s.rope('%s-tg-shroud-S%d' % (m, k + 1), ml + '/ct-S%d' % (k + 1), ml + '/tg-head', 1, tar, th['tg_shroud'], 'standing/topgallant-shrouds', {'kind': 'shroud'})
        # 左舷：右舷那一批鏡過去
        right = list(s.ropes)
        for r in right:
            nm = r['name']
            if '-S' not in nm:
                continue
            q = dict(r)
            q['name'] = nm.replace('-S', '-P', 1)
            q['from'] = s.mirror_end(r['from'])
            q['to'] = s.mirror_end(r['to'])
            s.ropes.append(q)
        # stays（中線，各一條）
        st, sl = th['stay'], S['stay_slack']
        straight = set(S['straight_stays'])
        L = s.links
        for nm, a, b in (('mizzen-stay', L['mizzen'] + '/stay-out', L['main'] + '/stay-in-low'),
                         ('mizzen-topmast-stay', L['mizzen'] + '/tmstay-out', L['main'] + '/top-aft'),
                         ('main-stay', L['main'] + '/stay-out', '後甲板・走道・前甲板/mainstay'),
                         ('main-topmast-stay', L['main'] + '/tmstay-out', L['fore'] + '/top-aft'),
                         ('main-topgallant-stay', L['main'] + '/tgstay-out', L['fore'] + '/ct-aft'),
                         ('fore-stay', L['fore'] + '/stay-out', '艏斜桅/forestay'),
                         ('fore-topmast-stay', L['fore'] + '/tmstay-out', '艏斜桅/fore-tmstay'),
                         ('jib-stay', L['fore'] + '/tgstay-out', '艏斜桅/jibboom-end'),
                         ('bobstay', '艏斜桅/bobstay', '船殼/stem-bobstay')):
            s.rope(nm, a, b, 1 if (nm in straight or nm == 'bobstay') else sl, tar, st[nm], 'standing/stays', {'kind': 'stay'})

    def ratlines(s):
        R = s.S['ratlines']
        n = 0
        s.rat_log = {}
        for m in MASTS:
            zt = s.Y['heights'][m]['top']
            for side in ('S', 'P'):
                names = [nm.replace('-S', '-' + side, 1) for nm in s.shroud_names[m]]
                rs = [next(r for r in s.ropes if r['name'] == nm) for nm in names]
                ends = [(s.world_of(r['from']), s.world_of(r['to'])) for r in rs]
                zlo = max(e[0][2] for e in ends) + R['from_above_deadeye']
                zhi = zt - R['below_top']
                k = 0
                z = zlo
                while z <= zhi:
                    ta = (z - ends[0][0][2]) / (ends[0][1][2] - ends[0][0][2])
                    tb = (z - ends[-1][0][2]) / (ends[-1][1][2] - ends[-1][0][2])
                    k += 1
                    s.rope('%s-ratline-%s%d' % (m, side, k), 'rope:%s/%.4f' % (names[0], ta), 'rope:%s/%.4f' % (names[-1], tb), 1, s.S['tar'], s.S['thick']['ratline'], 'ratlines/lower', {'kind': 'ratline'})
                    z += R['every']
                # topmast shrouds
                tn = ['%s-tm-shroud-%s%d' % (m, side, j + 1) for j in range(s.S['topmast_shrouds'][m])]
                if len(tn) >= 2:
                    rs = [next(r for r in s.ropes if r['name'] == nm) for nm in tn]
                    ends = [(s.world_of(r['from']), s.world_of(r['to'])) for r in rs]
                    z = max(e[0][2] for e in ends) + 3
                    zhi2 = s.Y['heights'][m]['crosstrees'] - 8
                    j = 0
                    while z <= zhi2:
                        ta = (z - ends[0][0][2]) / (ends[0][1][2] - ends[0][0][2])
                        tb = (z - ends[-1][0][2]) / (ends[-1][1][2] - ends[-1][0][2])
                        j += 1
                        s.rope('%s-tm-ratline-%s%d' % (m, side, j), 'rope:%s/%.4f' % (tn[0], ta), 'rope:%s/%.4f' % (tn[-1], tb), 1, s.S['tar'], s.S['thick']['ratline_tm'], 'ratlines/topmast', {'kind': 'ratline'})
                        z += s.S['ratlines']['every']
                s.rat_log['%s-%s' % (m, side)] = {'lower': k, 'topmast': j if len(tn) >= 2 else 0}
                n += k
        return n

    def clearance(s):
        bad = {}
        for r in s.ropes:
            if isinstance(r['from'], str) and r['from'].startswith('rope:'):
                continue
            hits = s.line_hits(s.world_of(r['from']), s.world_of(r['to']), s.S['clearance_end_skip'])
            if hits:
                bad[r['name']] = hits
        return bad


def render_sheet(S, path):
    X0, X1, Z1 = 40, 1000, 560
    img = np.full((Z1, X1 - X0, 3), 250, np.uint8)
    for (x, y, z) in S.occ:
        if X0 <= x < X1 and z < Z1:
            img[Z1 - 1 - z, x - X0] = (215, 208, 196)
    for (x, y, z), c in S.ch_cells.items():
        img[Z1 - 1 - z, x - X0] = DP.rgb332(c)
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    for r in S.ropes:
        if isinstance(r['from'], str) and r['from'].startswith('rope:'):
            continue
        if r['name'].endswith('-P') or '-P' in r['name'] and 'stay' not in r['name']:
            continue
        a, b = S.world_of(r['from']), S.world_of(r['to'])
        col = (60, 50, 40) if 'lanyard' not in r['name'] else (160, 130, 90)
        dr.line([(a[0] - X0, Z1 - 1 - a[2]), (b[0] - X0, Z1 - 1 - b[2])], fill=col, width=1)
    dr.text((6, 4), 'sheet 16 v1  channels & standing rigging (starboard profile; ratlines not drawn)', fill=(0, 0, 0))
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    keys = ('assembly', 'hull', 'spar', 'mizzen', 'main', 'fore', 'bowsprit')
    S = Standing(design, dict(zip(keys, sys.argv[2:9])))
    S.mast_points()
    S.bow_points()
    S.channels()
    S.build_ropes()
    nr = S.ratlines()
    v = {'base': S.sha, 'read': S.read, 'channels': S.ch_log, 'ratlines': S.rat_log, 'bobstay_tried': S.bob_try}
    v['rope_clearance_hits'] = S.clearance()
    v['ropes'] = len(S.ropes)
    v['ropes_by_group'] = {}
    for r in S.ropes:
        v['ropes_by_group'][r['group']] = v['ropes_by_group'].get(r['group'], 0) + 1
    v['points'] = len(S.points)
    v['channel_cells'] = len(S.ch_cells)
    # 鏡像：索具台的格鏡過去落在現況實心裡的數（左舷那件 ＝ 鏡像關聯）
    v['mirror_side_overlap'] = sum(1 for (x, y, z) in S.ch_cells if (x, 320 - y, z) in S.occ)
    v['mirror_side_not_attached'] = sum(1 for (x, y, z), c in S.ch_cells.items() if c == S.S['channels']['color']
                                        and (x, 320 - y + 1, z) not in S.hull and (x, y - 1, z) not in S.ch_cells)
    out = os.path.join(design, 'masks', 'channels')
    os.makedirs(out, exist_ok=True)
    o = S.S['channels']['origin']
    rows = sorted((k[0] - o[0], k[1] - o[1], k[2] - o[2], c) for k, c in S.ch_cells.items())
    p = os.path.join(out, 'channels.vox.txt')
    open(p, 'w', encoding='utf-8', newline='\n').write('# 索具台（右舷）—— 子作品自己的座標（框 %s）；組裝件座標 ＝ 這裡 ＋ %s；左舷 mirror=y（%d 格）\n' % (
        ','.join(map(str, S.S['channels']['size'])), ','.join(map(str, o)), len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
    files = {'channels': {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}
    rp = os.path.join(design, 'rig_points_standing.json')
    json.dump({'note': '階段十五要登記的固定點：owner 作品、link 關聯名、world ＝ 組裝件座標、local ＝ 子作品座標（索具台 ＝ world − 0,161,0；其他幾件關聯 at 0,0,0 ⇒ ＝ world）', 'points': S.points},
              open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    files['points'] = {'n': len(S.points), 'sha256': hashlib.sha256(open(rp, 'rb').read()).hexdigest()}
    for r in S.ropes:
        r['from'] = S.end_str(r['from'])
        r['to'] = S.end_str(r['to'])
    sp = os.path.join(design, 'standing_ropes.json')
    json.dump({'ropes': S.ropes}, open(sp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    files['ropes'] = {'n': len(S.ropes), 'sha256': hashlib.sha256(open(sp, 'rb').read()).hexdigest()}
    v['files'] = files
    json.dump(v, open(os.path.join(design, 'verify_standing.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(S, os.path.join(design, 'sheet16_standing_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('files', 'base')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
