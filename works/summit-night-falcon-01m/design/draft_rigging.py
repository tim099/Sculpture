# 新圖紙 09 靜索（TASK-0529 階段九）：plan.json 的 rigging ⇒ channels v2（含下 deadeye、chain plates）的刻／貼清單、固定點、繩清單、verify_rigging.json。
# 用法：python -I -X utf8 -B draft_rigging.py <design 資料夾>
#   · 現況照 nf_state.state_after('stage7') 重建；帆桁（階段八，外部模型、預設角）照 verify_yards.json 的清單擺進世界座標（gaff／boom 照 rot 轉）—— 只拿來量繩碰撞。
#   · channels v2：同 draft_masts.py 的算法（舷牆頂最低處往下 below_top 起 thick 格厚、往外 out、兩頭圓角），x 範圍改成 5 顆 deadeye 的範圍。
#     舊 channel 跟新的比：只刻「舊有、新沒有或顏色不同」的格（carvevox 帶原色守門）、只貼「新有、舊沒有」的格。一舷做、鏡像關聯自動跟著。
#   · 下 deadeye：3×3 去四角（x–z 平面）、2 格厚（channel 最外兩排 y）、坐在 channel 頂面上。
#   · chain plate：deadeye 底下，從 channel 底面外緣往下 down 格、往內收到船殼表面外一格；往內走就在同一層橫著補 ⇒ 6 連通。
#   · 固定點（世界座標；channels 寫子作品座標）：桅 —— hounds／futtock／top 邊緣／topmast head／topgallant head（S、P）、crosstrees 兩端、stays 的出入口；
#     艏斜桅 —— stays 落點、bobstay；船頭作品 —— bobstay；channels —— deadeye-<桅>-<i>（只 S，P 走 channels-鏡像）。
#   · 繩（組裝件）：lower shrouds、backstays、futtock、topmast／topgallant shrouds、stays、bobstay、上 deadeye（短粗繩）、lanyards、ratlines（子繩）。
#     座標端點一律寫 4 位小數（CLI：整數 ＝ 格心）。
#   · 碰撞：每條繩兩端之間每 0.25 格取樣（跳過兩端 clear_ends），落在實心格的點數 —— 按撞到的作品分。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC
from nf_state import state_after, NX, NY, NZ
from draft_yards import rot

LINK = {'fore': '前桅', 'main': '主桅'}
G = lambda v: ','.join('%.4f' % c for c in v)


def lst(rows):
    return ''.join('%d,%d,%d,%d\n' % tuple(r) for r in rows)


class Rig:
    def __init__(s, d):
        s.d = d
        s.plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
        s.R = s.plan['rigging']; s.M = s.plan['masts']; s.H = Hull(s.plan)
        s.W = state_after(d, 'stage7')
        s.anchors = {}            # 作品鍵 → [(名字, 世界格, 種類)]
        s.ropes = []

    # ── channels v2 ──
    def channels(s):
        CH = s.M['channels']; R = s.R['channels_v2']; W = s.W
        old = W['channels_S'] > 0
        occ_wo = np.zeros((NX, NY, NZ), bool)
        for k, v in W.items():
            if not k.startswith('channels'): occ_wo |= v > 0
        chan = np.zeros((NX, NY, NZ), np.int16)
        s.de = {}
        for m in ('fore', 'main'):
            xd = [s.M[m]['x'] + R['first_fwd_of_mast'] - R['spacing'] * i for i in range(R['deadeyes'])]
            xa, xb = xd[-1] - R['end_margin'], xd[0] + R['end_margin']
            ztop = int(math.floor(min(float(s.H.top(x + 0.5)) for x in range(xa, xb + 1))))
            zs = list(range(ztop - CH['below_top'] - CH['thick'] + 1, ztop - CH['below_top'] + 1))
            for xx in range(xa, xb + 1):
                e = min(xx - xa, xb - xx)
                o = CH['out'] if e >= 2 else CH['out'] - (2 - e)
                for zz in zs:
                    ys = np.nonzero(W['hull'][xx, YC:, zz])[0]
                    if len(ys) == 0: continue
                    yo = YC + ys.max()
                    chan[xx, yo + 1:yo + 1 + o, zz] = CH_COLOR
            s.de[m] = {'x': xd, 'z': zs, 'range': [xa, xb], 'ztop': ztop}
        dropped = int(((chan > 0) & occ_wo).sum()); chan[occ_wo] = 0
        # 下 deadeye、chain plates
        D, P = s.R['deadeye'], s.R['chain_plate']
        hull = W['hull'] > 0
        plates = {}
        for m in ('fore', 'main'):
            zt, zb = max(s.de[m]['z']), min(s.de[m]['z'])
            s.de[m]['centers'] = []
            for i, x in enumerate(s.de[m]['x']):
                yo = min(int(np.nonzero(chan[xx, :, zt])[0].max()) for xx in (x - 1, x, x + 1))
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx and dz: continue
                        for y in range(yo - D['thick'] + 1, yo + 1):
                            assert not occ_wo[x + dx, y, zt + 2 + dz] and chan[x + dx, y, zt + 2 + dz] == 0
                            chan[x + dx, y, zt + 2 + dz] = D['color']
                c = (x + 0.5, yo - D['thick'] / 2 + 1.0, zt + 2.5)
                s.de[m]['centers'].append(c)
                s.anchors.setdefault('channels', []).append(('deadeye-%s-%d' % (m, i + 1), (x, yo, zt + 2), 'deadeye'))
                # chain plate
                y0 = int(np.nonzero(chan[x, :, zb])[0].max())
                ze = zb - P['down']
                hy = lambda z: int(np.nonzero(hull[x, YC:, z])[0].max()) + YC
                yt = hy(ze) + 1
                prev = y0; cells = []
                for k in range(P['down']):
                    z = zb - 1 - k
                    yk = int(round(y0 + (yt - y0) * k / (P['down'] - 1)))
                    yk = max(yk, hy(z) + 1)
                    for y in range(min(prev, yk), max(prev, yk) + 1):
                        cells.append((x, y, z))
                    prev = yk
                for c3 in cells:
                    assert not occ_wo[c3] and chan[c3] == 0, ('plate 撞到', m, i, c3)
                    chan[c3] = P['color']
                plates['%s-%d' % (m, i + 1)] = {'cells': len(cells), 'top': [x, y0, zb - 1], 'bottom': list(cells[-1]), 'hull_y_at_bottom': hy(cells[-1][2])}
        s.chan = chan
        # 刻／貼（一舷，世界座標 → 子作品座標）
        fa = np.asarray(CH['frame_at']); fs = np.asarray(CH['frame_size'])
        oldv = W['channels_S']
        carve = np.argwhere((oldv > 0) & (chan != oldv))
        stamp = np.argwhere((chan > 0) & (chan != oldv))
        loc = np.argwhere(chan > 0) - fa
        assert (loc >= 0).all() and (loc < fs).all(), ('channels v2 出框', loc.min(0), loc.max(0))
        s.carve = np.column_stack([carve - fa, oldv[tuple(carve.T)]])
        s.stamp = np.column_stack([stamp - fa, chan[tuple(stamp.T)]])
        cnt = {'old': int(old.sum()), 'new': int((chan > 0).sum()), 'carve': len(carve), 'stamp': len(stamp), 'dropped_by_occupancy': dropped,
               'by_color_new': {str(int(k)): int(v) for k, v in zip(*np.unique(chan[chan > 0], return_counts=True))},
               'components_new': int(ndimage.label(chan > 0)[1])}
        return cnt, plates

    # ── 桅、艏斜桅、船頭上的固定點（量實際的格）──
    def points(s):
        P = s.R['points']
        for m in ('fore', 'main'):
            S = s.M[m]; A = s.W['mast_' + m]; L = []
            def side(z, col=None):
                xs = np.nonzero(A[:, YC, z])[0]; xa = int((xs.min() + xs.max()) // 2)
                ys = np.nonzero(A[xa, :, z] > 0)[0]
                return (xa, int(ys.max()), z), (xa, int(ys.min()), z)
            def put(nm, sp, kind):
                L.append((nm + '-S', sp[0], kind)); L.append((nm + '-P', sp[1], kind))
            zc = S['topmast_head_z'] - S['tm_doubling']
            put('hounds', side(S['top_z'] - P['hounds_below_top']), 'hounds')
            put('futtock', side(S['top_z'] - P['futtock_below_top']), 'futtock')
            put('tm-head', side(zc - P['tm_head_below_crosstrees']), 'topmast-head')
            put('tg-head', side(S['truck_z'] - P['tg_head_below_truck']), 'topgallant-head')
            # top 邊緣（平台色）：桅軸前後 rim_dx
            zt = S['top_z']; plat = A[:, :, zt] == s.M['colors']['top']
            xs = np.nonzero(A[:, YC, zt])[0]
            axc = side(zt - 1)[0][0]
            for tag, x in (('rim-fwd', axc + P['rim_dx']), ('rim-aft', axc - P['rim_dx'])):
                ys = np.nonzero(plat[x, :])[0]
                L.append((tag + '-S', (x, int(ys.max()), zt), 'top-rim')); L.append((tag + '-P', (x, int(ys.min()), zt), 'top-rim'))
            # 中桅 crosstrees 兩端（z ＝ zc＋1 那一層的鐵）
            cr = np.argwhere(A[:, :, zc + 1] == s.M['colors']['iron'])
            cx = int(round(np.median(cr[:, 0])))
            row = cr[cr[:, 0] == cx]
            L.append(('cross-S', (cx, int(row[:, 1].max()), zc + 1), 'crosstree')); L.append(('cross-P', (cx, int(row[:, 1].min()), zc + 1), 'crosstree'))
            # stays 的出入口（中線）
            front = lambda z, col: (int(np.nonzero((A[:, YC, z] == col) if col else (A[:, YC, z] > 0))[0].max()), YC, z)
            back = lambda z, col: (int(np.nonzero((A[:, YC, z] == col) if col else (A[:, YC, z] > 0))[0].min()), YC, z)
            L.append(('top-fwd', front(zt, s.M['colors']['top']), 'stay'))
            L.append(('tm-cap-fwd', front(S['topmast_head_z'], s.M['colors']['iron']), 'stay'))
            L.append(('tg-head-fwd', front(S['truck_z'] - P['tg_head_below_truck'], None), 'stay'))
            if m == 'fore':
                zd = json.load(open(os.path.join(s.d, 'verify_masts.json'), encoding='utf-8'))['rig_points']['fore']['zdeck']
                L.append(('aft-low', back(zd + P['fore_low_above_deck'], None), 'stay'))
                L.append(('cap-aft', back(S['lower_head_z'], s.M['colors']['iron']), 'stay'))
                L.append(('tm-cap-aft', back(S['topmast_head_z'], s.M['colors']['iron']), 'stay'))
            for nm, c, k in L:
                assert A[c] > 0, (m, nm, c, '固定點不在實心格上')
            s.anchors['mast_' + m] = L
        B = s.W['bowsprit']; Bp = s.R['bowsprit']; spar = s.M['colors']['spar']
        top = lambda x: (x, YC, int(np.nonzero(B[x, YC, :] == spar)[0].max()))
        bot = lambda x: (x, YC, int(np.nonzero(B[x, YC, :] == spar)[0].min()))
        xj = int(np.nonzero((B[:, YC, :] == spar).any(1))[0].max()) - 1
        s.anchors['bowsprit'] = [('stay-fore', top(Bp['fore_stay_x']), 'stay'), ('stay-tm', top(Bp['tm_stay_x']), 'stay'),
                                 ('stay-tg', top(xj), 'stay'), ('bobstay', bot(Bp['bobstay_x']), 'bobstay')]
        Hd = s.W['head']
        xs = np.nonzero(Hd[:, YC, Bp['stem_z']] > 0)[0]
        s.anchors['head'] = [('bobstay', (int(xs.max()), YC, Bp['stem_z']), 'bobstay')]
        for k in ('bowsprit', 'head'):
            for nm, c, kd in s.anchors[k]:
                assert s.W[k][c] > 0, (k, nm, c)

    def a(s, key, name):
        for nm, c, k in s.anchors[key]:
            if nm == name: return [c[0] + 0.5, c[1] + 0.5, c[2] + 0.5]
        raise KeyError(name)

    # ── 繩 ──
    KEY = {'前桅': 'mast_fore', '主桅': 'mast_main', '艏斜桅': 'bowsprit', '船頭': 'head', 'channels': 'channels_S', 'channels-鏡像': 'channels_P'}

    def rope(s, name, fr, to, kind, group, thick, color=None, frw=None, tow=None, fkey=None, tkey=None):
        k = lambda e, dflt: s.KEY.get(e.split('/')[0], dflt) if '/' in e and not e.startswith('rope:') else dflt
        s.ropes.append({'name': name, 'from': fr, 'to': to, 'kind': kind, 'group': group, 'thickness': thick,
                        'color': color or s.R['color'], 'slack': s.R['slack'], 'from_world': frw, 'to_world': tow,
                        'from_key': k(fr, fkey), 'to_key': k(to, tkey)})

    def build_ropes(s):
        T = s.R['thickness']; U = s.R['upper_deadeye']
        mir = lambda p: [p[0], 161.0 - p[1], p[2]]
        s.shroud_ends = {}
        for m in ('fore', 'main'):
            lk = LINK[m]
            for side in ('S', 'P'):
                for i, c in enumerate(s.de[m]['centers']):
                    c = list(c) if side == 'S' else mir(c)
                    if i < 3: up, kind, grp, th, nm = 'hounds', 'shroud', 'standing/shrouds', T['shroud'], '%s-shroud-%s%d' % (m, side, i + 1)
                    elif i == 3: up, kind, grp, th, nm = 'tm-head', 'backstay', 'standing/backstays', T['backstay'], '%s-backstay-topmast-%s' % (m, side)
                    else: up, kind, grp, th, nm = 'tg-head', 'backstay', 'standing/backstays', T['backstay'], '%s-backstay-topgallant-%s' % (m, side)
                    pt = s.a('mast_' + m, '%s-%s' % (up, side))
                    u = np.array(pt) - np.array(c); u /= np.linalg.norm(u)
                    cu = np.array(c) + U['along'] * u
                    n = np.array([0, 1.0 if side == 'S' else -1.0, 0])
                    lo = cu + (U['diameter'] / 2) * u
                    s.rope(nm, G(lo), '%s/%s-%s' % (lk, up, side), kind, grp, th, frw=list(lo), tow=pt)
                    s.shroud_ends[nm] = (list(lo), pt)
                    de = '%s-deadeye-%s%d' % (m, side, i + 1)
                    p0, p1 = cu - (U['length'] / 2) * n, cu + (U['length'] / 2) * n
                    s.rope(de, G(p0), G(p1), 'deadeye', 'standing/deadeyes/upper', U['diameter'], U['color'], list(p0), list(p1))
                    for j, off in enumerate(np.linspace(-U['lanyard_spread'], U['lanyard_spread'], U['lanyards'])):
                        q0 = np.array(c) + np.array([off, 0, 1.5]); q1 = cu - (U['diameter'] / 2) * u + np.array([off, 0, 0])
                        s.rope('%s-lanyard-%s%d%s' % (m, side, i + 1, 'abc'[j]), G(q0), G(q1), 'lanyard', 'standing/deadeyes/lanyards',
                               U['lanyard_thickness'], U['lanyard_color'], list(q0), list(q1), fkey='channels_' + side)
                for k, rim in enumerate(('rim-fwd', 'rim-aft')):
                    r = '%s/%s-%s' % (lk, rim, side)
                    s.rope('%s-futtock-%s%d' % (m, side, k + 1), r, '%s/futtock-%s' % (lk, side), 'futtock', 'standing/futtock-shrouds', T['futtock'],
                           frw=s.a('mast_' + m, '%s-%s' % (rim, side)), tow=s.a('mast_' + m, 'futtock-' + side))
                    nm = '%s-tm-shroud-%s%d' % (m, side, k + 1)
                    s.rope(nm, r, '%s/tm-head-%s' % (lk, side), 'tm-shroud', 'standing/topmast-shrouds', T['tm_shroud'],
                           frw=s.a('mast_' + m, '%s-%s' % (rim, side)), tow=s.a('mast_' + m, 'tm-head-' + side))
                    s.shroud_ends[nm] = (s.a('mast_' + m, '%s-%s' % (rim, side)), s.a('mast_' + m, 'tm-head-' + side))
                s.rope('%s-tg-shroud-%s' % (m, side), '%s/cross-%s' % (lk, side), '%s/tg-head-%s' % (lk, side), 'tg-shroud', 'standing/topgallant-shrouds',
                       T['tg_shroud'], frw=s.a('mast_' + m, 'cross-' + side), tow=s.a('mast_' + m, 'tg-head-' + side))
        st = [('fore-stay', '前桅/top-fwd', '艏斜桅/stay-fore', 'stay', ('mast_fore', 'top-fwd'), ('bowsprit', 'stay-fore')),
              ('fore-tm-stay', '前桅/tm-cap-fwd', '艏斜桅/stay-tm', 'tm_stay', ('mast_fore', 'tm-cap-fwd'), ('bowsprit', 'stay-tm')),
              ('fore-tg-stay', '前桅/tg-head-fwd', '艏斜桅/stay-tg', 'tg_stay', ('mast_fore', 'tg-head-fwd'), ('bowsprit', 'stay-tg')),
              ('main-stay', '主桅/top-fwd', '前桅/aft-low', 'stay', ('mast_main', 'top-fwd'), ('mast_fore', 'aft-low')),
              ('main-tm-stay', '主桅/tm-cap-fwd', '前桅/cap-aft', 'tm_stay', ('mast_main', 'tm-cap-fwd'), ('mast_fore', 'cap-aft')),
              ('main-tg-stay', '主桅/tg-head-fwd', '前桅/tm-cap-aft', 'tg_stay', ('mast_main', 'tg-head-fwd'), ('mast_fore', 'tm-cap-aft')),
              ('bobstay', '艏斜桅/bobstay', '船頭/bobstay', 'bobstay', ('bowsprit', 'bobstay'), ('head', 'bobstay'))]
        for nm, f, t, th, fa, ta in st:
            s.rope(nm, f, t, 'stay', 'standing/stays', T[th], frw=s.a(*fa), tow=s.a(*ta))
        # ratlines（子繩）
        Rl = s.R['ratlines']
        def ratio(nm, z):
            a, b = s.shroud_ends[nm]; return (z - a[2]) / (b[2] - a[2])
        def at(nm, t):
            a, b = s.shroud_ends[nm]; return [a[i] + t * (b[i] - a[i]) for i in range(3)]
        for m in ('fore', 'main'):
            S = s.M[m]; zc = S['topmast_head_z'] - S['tm_doubling']
            for side in ('S', 'P'):
                f, b = '%s-shroud-%s1' % (m, side), '%s-shroud-%s3' % (m, side)
                z0 = max(s.shroud_ends[f][0][2], s.shroud_ends[b][0][2]) + Rl['lower_from_deadeye']
                z1 = s.shroud_ends[f][1][2] - Rl['lower_below_hounds']
                k = 0
                for z in np.arange(z0, z1 + 1e-9, Rl['every']):
                    tf, tb = ratio(f, z), ratio(b, z); pf, pb = at(f, tf), at(b, tb)
                    if math.dist(pf, pb) < Rl['min_len']: continue
                    k += 1
                    s.rope('%s-ratline-%s-%02d' % (m, side, k), 'rope:%s/%.5f' % (f, tf), 'rope:%s/%.5f' % (b, tb), 'ratline', 'ratlines/lower',
                           s.R['thickness']['ratline'], frw=pf, tow=pb)
                f, b = '%s-tm-shroud-%s1' % (m, side), '%s-tm-shroud-%s2' % (m, side)
                z0 = S['top_z'] + 0.5 + Rl['tm_above_rim']; z1 = s.shroud_ends[f][1][2] - Rl['tm_below_head']
                k = 0
                for z in np.arange(z0, z1 + 1e-9, Rl['every']):
                    tf, tb = ratio(f, z), ratio(b, z); pf, pb = at(f, tf), at(b, tb)
                    if math.dist(pf, pb) < Rl['min_len']: continue
                    k += 1
                    s.rope('%s-tm-ratline-%s-%02d' % (m, side, k), 'rope:%s/%.5f' % (f, tf), 'rope:%s/%.5f' % (b, tb), 'ratline', 'ratlines/topmast',
                           s.R['thickness']['ratline'], frw=pf, tow=pb)

    # ── 碰撞 ──
    def collide(s):
        world = {k: v > 0 for k, v in s.W.items() if not k.startswith('channels')}
        world['channels_S'] = s.chan > 0; world['channels_P'] = (s.chan > 0)[:, ::-1, :]
        yv = json.load(open(os.path.join(s.d, 'verify_yards.json'), encoding='utf-8'))
        yd = np.zeros((NX, NY, NZ), bool)
        for P in yv['placements']:
            a = np.loadtxt(os.path.join(s.d, P['file']), delimiter=',', dtype=int, ndmin=2)
            for c in a[:, :3] + np.asarray(P['origin']):
                q = rot([c[i] + 0.5 for i in range(3)], P['at'], P['rotate'][1], P['rotate'][2])
                yd[tuple(int(math.floor(v)) for v in q)] = True
        world['yards'] = yd
        ce = s.R['clear_ends']; mid = {}; land = {}
        for r in s.ropes:
            p0, p1 = np.array(r['from_world']), np.array(r['to_world']); L = float(np.linalg.norm(p1 - p0))
            ts = [t for t in np.arange(0, L, 0.25) if ce <= t <= L - ce]
            hs = []
            for t in ts:
                q = tuple(int(math.floor(v)) for v in p0 + (p1 - p0) * t / L)
                hs.append({k for k, v in world.items() if v[q]})
            lo, hi = 0, len(ts)
            while lo < hi and r['from_key'] and r['from_key'] in hs[lo]: lo += 1      # 從起點連續落在起點那件作品裡 ＝ 著陸
            while hi > lo and r['to_key'] and r['to_key'] in hs[hi - 1]: hi -= 1
            if lo or hi < len(ts): land[r['name']] = round(max(lo, len(ts) - hi) * 0.25, 2)
            m = {}
            for h in hs[lo:hi]:
                for k in h: m[k] = m.get(k, 0) + 1
            if m: mid[r['name']] = m
            r['length'] = round(L, 3)
        return mid, land

    def write(s, v):
        od = os.path.join(s.d, 'masks', 'rigging'); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od): os.remove(os.path.join(od, f))
        so = []
        for nm, rows, op in (('channels_carve', s.carve, 'carvevox'), ('channels_stamp', s.stamp, 'stampvox')):
            text = lst(sorted(map(tuple, rows.tolist())))
            open(os.path.join(od, nm + '.vox.txt'), 'w', encoding='utf-8', newline='\n').write(text)
            so.append({'name': nm, 'op': op, 'file': 'masks/rigging/%s.vox.txt' % nm, 'at': [0, 0, 0], 'voxels': len(rows),
                       'origin_world': s.M['channels']['frame_at'], 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})
        fa = s.M['channels']['frame_at']
        anc = {}
        for k, L in s.anchors.items():
            anc[k] = [{'name': nm, 'at': [c[i] - (fa[i] if k == 'channels' else 0) for i in range(3)], 'world': list(c), 'kind': kd} for nm, c, kd in L]
        v['stamp_order'] = {'channels': so}
        v['anchors'] = anc
        v['ropes'] = [dict({k: r[k] for k in ('name', 'from', 'to', 'kind', 'group', 'thickness', 'color', 'slack', 'length')},
                           from_world=[round(float(c), 4) for c in r['from_world']], to_world=[round(float(c), 4) for c in r['to_world']]) for r in s.ropes]
        with open(os.path.join(s.d, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as fo:
            json.dump(v, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')


CH_COLOR = None


def main():
    global CH_COLOR
    d = sys.argv[1]
    r = Rig(d); CH_COLOR = r.M['colors']['channel']
    cnt, plates = r.channels()
    r.points(); r.build_ropes()
    hits, land = r.collide()
    kinds = {}
    for x in r.ropes: kinds[x['kind']] = kinds.get(x['kind'], 0) + 1
    v = {'channels': cnt, 'deadeyes': {m: r.de[m] for m in r.de}, 'chain_plates': plates, 'rope_counts': kinds, 'ropes_total': len(r.ropes),
         'anchors_total': sum(len(L) for L in r.anchors.values()), 'rope_hits_mid': hits,
         'rope_landing_cells': land, 'landing_max_seen': max(land.values()) if land else 0}
    r.write(v)
    print(json.dumps({k: v[k] for k in ('channels', 'rope_counts', 'ropes_total', 'anchors_total', 'rope_hits_mid', 'landing_max_seen')}, ensure_ascii=False, indent=1))
    print(json.dumps(plates, ensure_ascii=False))


if __name__ == '__main__':
    main()
