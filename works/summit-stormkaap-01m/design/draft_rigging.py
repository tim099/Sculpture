# 新圖紙 08 靜索（TASK-0547 階段八）：plan.json 的 rigging ⇒ channels v2（含下 deadeye、chain plates）的刻／貼清單、固定點、繩清單、verify_rigging.json。
# 用法：python -I -X utf8 -B draft_rigging.py <design 資料夾>
#   · 從夜隼號 draft_rigging.py（TASK-0529 階段九）改：三根桅、shroud 數照桅分、deadeye 避開砲門、斜桅頂桅。
#   · 現況：船 ＝ sk_state 重播到 stage6a（z < 200）；桅、斜桅 ＝ masks/masts/ 的清單；舊 channels ＝ masks/masts/channels.vox.txt（＋鏡像）；
#     帆桁（階段七，外部模型、預設角）照 verify_yards.json 的清單轉進世界座標 —— 只拿來量繩碰撞。
#     全部放進一張「格 → 哪一件」的標籤表（int8）—— 一件一個 bool 陣列放不下（736×261×576）。
#   · channels v2：每根桅一塊。deadeye 從桅孔前 first_fwd 格起往船尾每 spacing 格一顆；deadeye 的 x±1 撞到上排砲門（±port_margin）、
#     或 chain plate 那一欄撞到下排砲門（±port_margin）⇒ 往船尾挪一格再試。channel 的 x 範圍 ＝ deadeye 範圍 ± end_margin。
#     channel 的高度與做法同 draft_masts.py（floor(sheer) ＋ dz、往外 width、外緣加厚一格、舷弧升階往下補一格）。
#     舊 channel 跟新的比：只刻「舊有、新沒有或顏色不同」的格（carvevox 帶原色守門）、只貼「新有、舊沒有或顏色不同」的格。一舷做、鏡像關聯自動跟著。
#   · 下 deadeye：3×3 去四角（x–z 平面）、thick 格厚（channel 最外兩排 y）、坐在那三欄 channel 最高那一格上面。
#   · chain plate：deadeye 那一欄，從 channel 底面外緣往下 down 格、往內收到船殼表面外一格；往內走就在同一層橫著補 ⇒ 6 連通。
#     ⛔ 不進任何砲門的開口（x、z 範圍，±port_margin）—— assert。
#   · 固定點（全部是世界座標 ＝ 子作品座標：桅、斜桅、船頭、channels 的框都是整艘船、at 0,0,0）：
#     桅 —— hounds／futtock／平台邊緣／topmast head／topgallant head（S、P）、crosstrees 兩端、stays 的出入口；
#     斜桅 —— stays 落點、斜桅頂桅頭、bobstay；船頭 —— bobstay；channels —— deadeye-<桅>-<i>（只 S，P 走 channels-鏡像）。
#     每一個都 assert 在那一件的實心格上。
#   · 繩（組裝件）：lower shrouds、backstays、futtock、topmast／topgallant shrouds、stays、bobstay、上 deadeye（短粗繩）、lanyards、ratlines（子繩）。
#   · 碰撞：每條繩兩端之間每 0.25 格取樣，分「著陸」（從端點連續落在端點那一件）與「中段」；中段按撞到的那一件分。
#     另量 shroud／backstay 在砲門正前方（砲門的 x、z 範圍，船殼外 12 格內）的取樣數。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull
from sk_state import state_after
from draft_yards import rot

NZ = 576
MASTS = ('mizzen', 'main', 'fore')
LINK = {'mizzen': '後桅', 'main': '主桅', 'fore': '前桅'}
KEY_OF_LINK = {'後桅': 'mast_mizzen', '主桅': 'mast_main', '前桅': 'mast_fore', '船首斜桅': 'bowsprit', '船頭': 'head',
               'channels': 'channels_S', 'channels-鏡像': 'channels_P'}
G = lambda v: ','.join('%.4f' % c for c in v)


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def lst(rows):
    return ''.join('%d,%d,%d,%d\n' % tuple(r) for r in rows)


class Rig:
    def __init__(s, d):
        s.d = d
        s.plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
        s.R = s.plan['rigging']; s.Mp = {m['name']: m for m in s.plan['masts']['list']}; s.B = s.plan['masts']['bowsprit']
        s.C = s.plan['masts']['colors']
        F = s.plan['frame']; s.NX, s.NY, s.YC = F['NX'], F['NY'], F['YC']
        s.H = Hull(s.plan)
        VM = json.load(open(os.path.join(d, 'verify_masts.json'), encoding='utf-8'))
        s.info = VM['info']
        W = state_after(d, 'stage6a', nz=200)
        s.names = ['']
        s.lab = np.zeros((s.NX, s.NY, NZ), np.int8)
        def put(name, pts):
            s.names.append(name); code = len(s.names) - 1
            assert not s.lab[tuple(pts.T)].any(), ('重疊', name)
            s.lab[tuple(pts.T)] = code
        for k, v in W.items():
            if k.endswith('_model') or not (v > 0).any(): continue
            put(k, np.argwhere(v > 0))
        s.occ200 = s.lab[:, :, :200] > 0                                 # 船（不含桅、channels）
        s.mast = {}
        for k in ('mizzen', 'main', 'fore', 'bowsprit'):
            a = load(os.path.join(d, VM['stamp_order'][k][0]['file']))
            s.mast[k] = a
            put('mast_' + k if k != 'bowsprit' else 'bowsprit', a[:, :3])
        s.old_ch = load(os.path.join(d, VM['stamp_order']['channels'][0]['file']))
        dk = json.load(open(os.path.join(d, 'verify_decks.json'), encoding='utf-8'))
        s.ports = [p for p in dk['ports']]
        s.anchors = {}; s.ropes = []

    def code(s, name):
        return s.names.index(name)

    # ── channels v2 ──
    def port_hit(s, x0, x1, rows=('upper',), z=None):
        mg = s.R['channels_v2']['port_margin']
        for p in s.ports:
            if p['row'] not in rows: continue
            if x1 >= p['x'][0] - mg and x0 <= p['x'][1] + mg and (z is None or p['z'][0] - mg <= z <= p['z'][1] + mg):
                return True
        return False

    def channels(s):
        CV = s.R['channels_v2']; YC = s.YC; col = s.C['channel']
        side = s.occ200[:, YC:, :]
        zch = lambda x: int(math.floor(s.H.sheer(x + 0.5))) + CV['dz']
        chan = {}                                                       # (x,y,z) → 色（右舷、世界座標）
        s.de = {}
        for m in MASTS:
            n = CV['deadeyes'][m]
            x = int(math.floor(s.Mp[m]['x'])) + CV['first_fwd_of_mast']
            xs, skipped = [], []
            while len(xs) < n:
                if s.port_hit(x - 1, x + 1, ('upper',)) or s.port_hit(x, x, ('lower',)):
                    skipped.append(x); x -= 1; continue
                xs.append(x); x -= CV['spacing']
            xa, xb = min(xs) - CV['end_margin'], max(xs) + CV['end_margin']
            for xx in range(xa, xb + 1):
                z = zch(xx)
                ys = np.nonzero(side[xx, :, z])[0]
                assert len(ys), ('channel 那一層找不到船殼', m, xx, z)
                y0 = YC + int(ys.max())
                zlo = min(z, zch(max(xx - 1, xa)), zch(min(xx + 1, xb)))
                # 下面幾層船殼比較寬（舷側內傾）⇒ 撞到船殼的格跳過 —— 同 draft_masts.py 階段六的規則
                for zz in range(zlo, z + 1):
                    for k in range(1, CV['width'] + 1):
                        if not s.lab[xx, y0 + k, zz]: chan[(xx, y0 + k, zz)] = col
                chan[(xx, y0 + CV['width'], z + 1)] = col
            s.de[m] = {'x': xs, 'range': [xa, xb], 'skipped_for_ports': skipped}
        for c in chan:
            assert not s.lab[c], ('channel 撞到', s.names[s.lab[c]], c)
            for p in s.ports:
                assert not (p['x'][0] <= c[0] <= p['x'][1] and p['z'][0] <= c[2] <= p['z'][1]), ('channel 進了砲門', c, p)
        # 下 deadeye、chain plates
        D, P = s.R['deadeye'], s.R['chain_plate']
        plates = {}
        for m in MASTS:
            s.de[m]['centers'] = []
            for i, x in enumerate(s.de[m]['x']):
                yo = min(max(c[1] for c in chan if c[0] == xx) for xx in (x - 1, x, x + 1))
                ys = range(yo - D['thick'] + 1, yo + 1)
                # 坐在 x±1 三欄最高那一格上；中間那一欄比較低 ⇒ 底下補墊木（channel 色）接回 channel。
                # 🩸 第一版沒有墊木 ⇒ 舷弧往前升的地方 6 顆 deadeye 懸空一格（channels 9 塊）；
                #    改坐自己那一欄 ⇒ 側邊那兩格撞進較高那一欄的外緣加厚。⇒ 坐最高、補墊木。
                zb = 1 + max(c[2] for c in chan if c[0] in (x - 1, x, x + 1) and c[1] in ys)
                for y in ys:
                    ztop = max(c[2] for c in chan if c[0] == x and c[1] == y)
                    for z in range(ztop + 1, zb):
                        q = (x, y, z)
                        assert not s.lab[q], ('墊木撞到', m, i, q)
                        chan[q] = s.C['channel']
                zc = zb + 1
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx and dz: continue
                        for y in ys:
                            q = (x + dx, y, zc + dz)
                            assert q not in chan and not s.lab[q], ('deadeye 撞到', m, i, q)
                            chan[q] = D['color']
                assert any((x, y, zb - 1) in chan for y in ys), ('deadeye 底下沒有 channel', m, i)
                s.de[m]['centers'].append((x + 0.5, yo - D['thick'] / 2 + 1.0, zc + 0.5))
                s.anchors.setdefault('channels', []).append(('deadeye-%s-%d' % (m, i + 1), (x, yo, zc), 'deadeye'))
                # chain plate：那一欄 channel 底面外緣往下
                cz = [c for c in chan if c[0] == x and chan[c] == s.C['channel']]
                zbot = min(c[2] for c in cz)
                y0 = max(c[1] for c in cz if c[2] == zbot)
                hy = lambda z: int(np.nonzero(s.occ200[x, YC:, z])[0].max()) + YC
                ze = zbot - P['down']
                yt = hy(ze) + 1
                prev = y0; cells = []
                for k in range(P['down']):
                    z = zbot - 1 - k
                    yk = int(round(y0 + (yt - y0) * k / (P['down'] - 1)))
                    yk = max(yk, hy(z) + 1)
                    for y in range(min(prev, yk), max(prev, yk) + 1): cells.append((x, y, z))
                    prev = yk
                for q in cells:
                    assert q not in chan and not s.lab[q], ('chain plate 撞到', m, i, q)
                    assert not s.port_hit(x, x, ('upper', 'lower'), q[2]), ('chain plate 進了砲門', m, i, q)
                    chan[q] = P['color']
                plates['%s-%d' % (m, i + 1)] = {'cells': len(cells), 'top': [x, y0, zbot - 1], 'bottom': list(cells[-1]), 'hull_y_at_bottom': hy(cells[-1][2])}
        s.chan = chan
        old = {tuple(r[:3]): int(r[3]) for r in s.old_ch}
        carve = sorted((k + (c,)) for k, c in old.items() if chan.get(k) != c)
        stamp = sorted((k + (c,)) for k, c in chan.items() if old.get(k) != c)
        s.carve, s.stamp = carve, stamp
        b = np.zeros((s.NX, s.NY, NZ), bool)
        for k in chan: b[k] = True
        cnt = {'old': len(old), 'new': len(chan), 'carve': len(carve), 'stamp': len(stamp),
               'by_color_new': {str(k): sum(1 for c in chan.values() if c == k) for k in sorted(set(chan.values()))},
               'components_new': int(ndimage.label(b)[1])}
        # 進標籤表（S＋鏡像 P）
        pts = np.array(sorted(chan)); s.names.append('channels_S'); s.lab[tuple(pts.T)] = len(s.names) - 1
        pp = pts.copy(); pp[:, 1] = s.NY - 1 - pp[:, 1]
        assert not s.lab[tuple(pp.T)].any()
        s.names.append('channels_P'); s.lab[tuple(pp.T)] = len(s.names) - 1
        return cnt, plates

    # ── 桅、斜桅、船頭上的固定點（量實際的格）──
    def points(s):
        P = s.R['points']; YC = s.YC; iron = s.C['iron']
        for m in MASTS:
            a = s.mast[m]; I = s.info[m]; M = s.Mp[m]
            cell = {tuple(r[:3]): int(r[3]) for r in a}
            def layer(z, color=None):
                q = a[a[:, 2] == z]
                return q if color is None else q[q[:, 3] == color]
            def side(z):
                q = layer(z); c = q[q[:, 1] == YC]
                xa = int((c[:, 0].min() + c[:, 0].max()) // 2)
                col = q[q[:, 0] == xa]
                return (xa, int(col[:, 1].max()), z), (xa, int(col[:, 1].min()), z)
            def front(z, color=None):
                q = layer(z, color); q = q[q[:, 1] == YC]; return (int(q[:, 0].max()), YC, z)
            def back(z, color=None):
                q = layer(z, color); q = q[q[:, 1] == YC]; return (int(q[:, 0].min()), YC, z)
            L = []
            def put2(nm, sp, kind): L.append((nm + '-S', sp[0], kind)); L.append((nm + '-P', sp[1], kind))
            zpl = I['hounds_z'] - 1                                      # 平台那一層
            put2('hounds', side(zpl - P['hounds_below_platform']), 'hounds')
            put2('futtock', side(zpl - P['futtock_below_platform']), 'futtock')
            axc = side(zpl - 1)[0][0]
            for tag, x in (('rim-fwd', axc + P['rim_dx']), ('rim-aft', axc - P['rim_dx'])):
                q = layer(zpl); q = q[q[:, 0] == x]
                L.append((tag + '-S', (x, int(q[:, 1].max()), zpl), 'top-rim')); L.append((tag + '-P', (x, int(q[:, 1].min()), zpl), 'top-rim'))
            L.append(('top-fwd', front(zpl), 'stay')); L.append(('top-aft', back(zpl), 'stay'))
            if M.get('L_tg'):
                zc = I['topmast_top_z'] - M['head_top'] - 1             # crosstrees 那一層
                put2('tm-head', side(zc - P['tm_head_below_crosstrees']), 'topmast-head')
                xt = int(math.floor(M['x'] + M['off_top']))
                q = layer(zc); q = q[q[:, 0] == xt]
                L.append(('cross-S', (xt, int(q[:, 1].max()), zc), 'crosstree')); L.append(('cross-P', (xt, int(q[:, 1].min()), zc), 'crosstree'))
                ztg = I['tg_top_z'] - 1 - P['tg_head_below_truck']
                put2('tg-head', side(ztg), 'topgallant-head')
                L.append(('tm-cap-fwd', front(I['topmast_top_z'], iron), 'stay'))
                L.append(('tg-head-fwd', front(ztg), 'stay'))
                L.append(('cap-aft', back(I['lower_top_z'], iron), 'stay'))
                L.append(('tm-cap-aft', back(I['topmast_top_z'], iron), 'stay'))
            else:
                ztm = I['topmast_top_z'] - 1 - P['mizzen_tm_head_below_top']
                put2('tm-head', side(ztm), 'topmast-head')
                L.append(('tm-head-fwd', front(ztm), 'stay'))
            if m in ('main', 'fore'):
                bx = back(zpl - 20)[0]
                deck = int(np.nonzero(s.occ200[bx - 1, YC, :])[0].max())
                zl = deck + 1 + P['low_above_deck']
                L.append(('low-aft', back(zl), 'stay'))
            for nm, c, k in L:
                assert c in cell, (m, nm, c, '固定點不在實心格上')
            s.anchors['mast_' + m] = L
        # 斜桅
        B = s.B; bp = s.mast['bowsprit']; Bp = s.R['bowsprit']
        th = math.radians(B['steeve']); tipx = B['heel'][0] + math.cos(th) * B['L']
        def bx(sf): return int(math.floor(B['heel'][0] + math.cos(th) * sf * B['L']))
        def top(x):
            q = bp[(bp[:, 0] == x) & (bp[:, 1] == YC)]; return (x, YC, int(q[:, 2].max()))
        def bot(x):
            q = bp[(bp[:, 0] == x) & (bp[:, 1] == YC)]; return (x, YC, int(q[:, 2].min()))
        zsh = s.info['bowsprit']['sprit_top_z'] - 1 - Bp['sprit_head_below_top']
        q = bp[(bp[:, 2] == zsh) & (bp[:, 1] == YC)]
        x_bob = bx(Bp['bobstay_s'])
        s.anchors['bowsprit'] = [('stay-fore', top(bx(Bp['fore_stay_s'])), 'stay'), ('stay-tm', top(bx(Bp['tm_stay_s'])), 'stay'),
                                 ('sprit-head', (int(q[:, 0].min()), YC, zsh), 'stay'), ('bobstay', bot(x_bob), 'bobstay')]
        # 🩸 sprit-head 第一版取斜桅頂桅的前緣 ⇒ 從後面來的 fore-tg-stay 要穿過頂桅、擦到掛在它前面的 sprit topsail 帆桁 ⇒ 取後緣
        assert all(a[1][0] < tipx - 3 for a in s.anchors['bowsprit'] if a[0] != 'sprit-head')
        # 船頭：大嘴上顎中脊在 bobstay 那一欄的頂面
        hc = s.code('head')
        zs = np.nonzero(s.lab[x_bob, YC, :] == hc)[0]
        s.anchors['head'] = [('bobstay', (x_bob, YC, int(zs.max())), 'bobstay')]
        bset = {tuple(r[:3]) for r in bp}
        for nm, c, k in s.anchors['bowsprit']: assert c in bset, ('斜桅固定點不在實心格上', nm, c)
        for nm, c, k in s.anchors['head']: assert s.lab[c] == hc, ('船頭固定點不在實心格上', nm, c)

    def a(s, key, name):
        for nm, c, k in s.anchors[key]:
            if nm == name: return [c[0] + 0.5, c[1] + 0.5, c[2] + 0.5]
        raise KeyError((key, name))

    # ── 繩 ──
    def rope(s, name, fr, to, kind, group, thick, color=None, frw=None, tow=None, fkey=None, tkey=None):
        def k(e, dflt):
            if '/' in e and not e.startswith('rope:'): return KEY_OF_LINK.get(e.split('/')[0], dflt)
            return dflt
        s.ropes.append({'name': name, 'from': fr, 'to': to, 'kind': kind, 'group': group, 'thickness': thick,
                        'color': color or s.R['color'], 'slack': s.R['slack'], 'from_world': list(frw), 'to_world': list(tow),
                        'from_key': k(fr, fkey), 'to_key': k(to, tkey)})

    def build_ropes(s):
        T = s.R['thickness']; U = s.R['upper_deadeye']; CV = s.R['channels_v2']
        mir = lambda p: [p[0], float(s.NY) - p[1], p[2]]
        s.shroud_ends = {}
        for m in MASTS:
            lk = LINK[m]; ns = CV['shrouds'][m]; tg = bool(s.Mp[m].get('L_tg'))
            ups = ['hounds'] * ns + ['tm-head'] + (['tg-head'] if tg else [])
            assert len(ups) == len(s.de[m]['centers']), (m, len(ups), len(s.de[m]['centers']))
            for side in ('S', 'P'):
                for i, c in enumerate(s.de[m]['centers']):
                    c = list(c) if side == 'S' else mir(c)
                    up = ups[i]
                    if up == 'hounds': kind, grp, th, nm = 'shroud', 'standing/shrouds', T['shroud'], '%s-shroud-%s%d' % (m, side, i + 1)
                    elif up == 'tm-head': kind, grp, th, nm = 'backstay', 'standing/backstays', T['backstay'], '%s-backstay-topmast-%s' % (m, side)
                    else: kind, grp, th, nm = 'backstay', 'standing/backstays', T['backstay'], '%s-backstay-topgallant-%s' % (m, side)
                    pt = s.a('mast_' + m, '%s-%s' % (up, side))
                    u = np.array(pt) - np.array(c); u /= np.linalg.norm(u)
                    cu = np.array(c) + U['along'] * u
                    n = np.array([0, 1.0 if side == 'S' else -1.0, 0])
                    lo = cu + (U['diameter'] / 2) * u
                    s.rope(nm, G(lo), '%s/%s-%s' % (lk, up, side), kind, grp, th, frw=lo, tow=pt)
                    s.shroud_ends[nm] = (list(lo), pt)
                    de = '%s-deadeye-%s%d' % (m, side, i + 1)
                    p0, p1 = cu - (U['length'] / 2) * n, cu + (U['length'] / 2) * n
                    s.rope(de, G(p0), G(p1), 'deadeye', 'standing/deadeyes/upper', U['diameter'], U['color'], p0, p1)
                    for j, off in enumerate(np.linspace(-U['lanyard_spread'], U['lanyard_spread'], U['lanyards'])):
                        q0 = np.array(c) + np.array([off, 0, 1.5]); q1 = cu - (U['diameter'] / 2) * u + np.array([off, 0, 0])
                        s.rope('%s-lanyard-%s%d%s' % (m, side, i + 1, 'abc'[j]), G(q0), G(q1), 'lanyard', 'standing/deadeyes/lanyards',
                               U['lanyard_thickness'], U['lanyard_color'], q0, q1, fkey='channels_' + side)
                for k, rim in enumerate(('rim-fwd', 'rim-aft')):
                    r = '%s/%s-%s' % (lk, rim, side)
                    s.rope('%s-futtock-%s%d' % (m, side, k + 1), r, '%s/futtock-%s' % (lk, side), 'futtock', 'standing/futtock-shrouds', T['futtock'],
                           frw=s.a('mast_' + m, '%s-%s' % (rim, side)), tow=s.a('mast_' + m, 'futtock-' + side))
                    nm = '%s-tm-shroud-%s%d' % (m, side, k + 1)
                    s.rope(nm, r, '%s/tm-head-%s' % (lk, side), 'tm-shroud', 'standing/topmast-shrouds', T['tm_shroud'],
                           frw=s.a('mast_' + m, '%s-%s' % (rim, side)), tow=s.a('mast_' + m, 'tm-head-' + side))
                    s.shroud_ends[nm] = (s.a('mast_' + m, '%s-%s' % (rim, side)), s.a('mast_' + m, 'tm-head-' + side))
                if tg:
                    s.rope('%s-tg-shroud-%s' % (m, side), '%s/cross-%s' % (lk, side), '%s/tg-head-%s' % (lk, side), 'tg-shroud', 'standing/topgallant-shrouds',
                           T['tg_shroud'], frw=s.a('mast_' + m, 'cross-' + side), tow=s.a('mast_' + m, 'tg-head-' + side))
        st = [('mizzen-stay', ('mast_mizzen', '後桅', 'top-fwd'), ('mast_main', '主桅', 'low-aft'), 'stay'),
              ('mizzen-tm-stay', ('mast_mizzen', '後桅', 'tm-head-fwd'), ('mast_main', '主桅', 'top-aft'), 'tm_stay'),
              ('main-stay', ('mast_main', '主桅', 'top-fwd'), ('mast_fore', '前桅', 'low-aft'), 'stay'),
              ('main-tm-stay', ('mast_main', '主桅', 'tm-cap-fwd'), ('mast_fore', '前桅', 'cap-aft'), 'tm_stay'),
              ('main-tg-stay', ('mast_main', '主桅', 'tg-head-fwd'), ('mast_fore', '前桅', 'tm-cap-aft'), 'tg_stay'),
              ('fore-stay', ('mast_fore', '前桅', 'top-fwd'), ('bowsprit', '船首斜桅', 'stay-fore'), 'stay'),
              ('fore-tm-stay', ('mast_fore', '前桅', 'tm-cap-fwd'), ('bowsprit', '船首斜桅', 'stay-tm'), 'tm_stay'),
              ('fore-tg-stay', ('mast_fore', '前桅', 'tg-head-fwd'), ('bowsprit', '船首斜桅', 'sprit-head'), 'tg_stay'),
              ('bobstay', ('bowsprit', '船首斜桅', 'bobstay'), ('head', '船頭', 'bobstay'), 'bobstay')]
        for nm, f, t, th in st:
            s.rope(nm, '%s/%s' % (f[1], f[2]), '%s/%s' % (t[1], t[2]), 'stay', 'standing/stays', T[th], frw=s.a(f[0], f[2]), tow=s.a(t[0], t[2]))
        # ratlines（子繩）
        Rl = s.R['ratlines']
        def ratio(nm, z):
            a, b = s.shroud_ends[nm]; return (z - a[2]) / (b[2] - a[2])
        def at(nm, t):
            a, b = s.shroud_ends[nm]; return [a[i] + t * (b[i] - a[i]) for i in range(3)]
        def run(f, b, z0, z1, prefix, grp):
            k = 0
            for z in np.arange(z0, z1 + 1e-9, Rl['every']):
                tf, tb = ratio(f, z), ratio(b, z); pf, pb = at(f, tf), at(b, tb)
                if math.dist(pf, pb) < Rl['min_len']: continue
                k += 1
                s.rope('%s-%02d' % (prefix, k), 'rope:%s/%.5f' % (f, tf), 'rope:%s/%.5f' % (b, tb), 'ratline', grp, T['ratline'], frw=pf, tow=pb)
        for m in MASTS:
            ns = CV['shrouds'][m]; zpl = s.info[m]['hounds_z'] - 1
            for side in ('S', 'P'):
                f, b = '%s-shroud-%s1' % (m, side), '%s-shroud-%s%d' % (m, side, ns)
                z0 = max(s.shroud_ends[f][0][2], s.shroud_ends[b][0][2]) + Rl['lower_from_deadeye']
                z1 = s.shroud_ends[f][1][2] - Rl['lower_below_hounds']
                run(f, b, z0, z1, '%s-ratline-%s' % (m, side), 'ratlines/lower')
                f, b = '%s-tm-shroud-%s1' % (m, side), '%s-tm-shroud-%s2' % (m, side)
                run(f, b, zpl + 0.5 + Rl['tm_above_rim'], s.shroud_ends[f][1][2] - Rl['tm_below_head'], '%s-tm-ratline-%s' % (m, side), 'ratlines/topmast')

    # ── 碰撞 ──
    def collide(s):
        yv = json.load(open(os.path.join(s.d, 'verify_yards.json'), encoding='utf-8'))
        s.names.append('yards'); yc = len(s.names) - 1
        for P in yv['placements']:
            a = load(os.path.join(s.d, P['file']))
            for c in a[:, :3] + np.asarray(P['origin']):
                q = rot([c[i] + 0.5 for i in range(3)], P['at'], P['rotate'][1], P['rotate'][2])
                g = tuple(int(math.floor(v)) for v in q)
                if not s.lab[g]: s.lab[g] = yc
        ce = s.R['clear_ends']; mid = {}; land = {}
        hull_y = {}
        for r in s.ropes:
            p0, p1 = np.array(r['from_world']), np.array(r['to_world']); L = float(np.linalg.norm(p1 - p0))
            ts = [t for t in np.arange(0, L, 0.25) if ce <= t <= L - ce]
            hs = []
            for t in ts:
                q = tuple(int(math.floor(v)) for v in p0 + (p1 - p0) * t / L)
                hs.append(s.names[s.lab[q]] if s.lab[q] else None)
            lo, hi = 0, len(ts)
            while lo < hi and r['from_key'] and hs[lo] == r['from_key']: lo += 1
            while hi > lo and r['to_key'] and hs[hi - 1] == r['to_key']: hi -= 1
            if lo or hi < len(ts):
                # 著陸的上限：端點在桅上 ⇒ 固定點是表面那一格的格心（往內半格），繩跟桅軸夾角 α 越小，貼著桅走的段越長 ≈ 1／sin α。
                #   🩸 第一版一律用 landing_max 6 ⇒ topgallant shrouds（α ≈ 3°）報 8 格 —— 那是幾何，不是穿過去。⇒ 上限取兩者大的那一個。
                u = (p1 - p0) / L; sa = max(math.hypot(u[0], u[1]), 1e-6)
                bound = lambda key: max(s.R['landing_max'], 1.0 / sa) if key and key.startswith('mast_') else s.R['landing_max']
                l0, l1 = lo * 0.25, (len(ts) - hi) * 0.25
                land[r['name']] = {'from': l0, 'to': l1, 'bound_from': round(bound(r['from_key']), 2), 'bound_to': round(bound(r['to_key']), 2),
                                   'over': l0 > bound(r['from_key']) or l1 > bound(r['to_key'])}
            m = {}
            for h in hs[lo:hi]:
                if h: m[h] = m.get(h, 0) + 1
            if m: mid[r['name']] = m
            r['length'] = round(L, 3)
        # shroud／backstay 擋砲門：取樣點在某個砲門的 x、z 範圍裡、船殼外 12 格內
        block = {}
        for r in s.ropes:
            if r['kind'] not in ('shroud', 'backstay', 'deadeye', 'lanyard'): continue
            p0, p1 = np.array(r['from_world']), np.array(r['to_world']); L = float(np.linalg.norm(p1 - p0))
            n = 0
            for t in np.arange(0, L, 0.25):
                q = p0 + (p1 - p0) * t / L
                x, y, z = int(math.floor(q[0])), int(math.floor(q[1])), int(math.floor(q[2]))
                for p in s.ports:
                    if p['x'][0] <= x <= p['x'][1] and p['z'][0] <= z <= p['z'][1]:
                        yy = y if y >= s.YC else s.NY - 1 - y
                        key = (x, z)
                        if key not in hull_y:
                            col = np.nonzero(s.occ200[x, s.YC:, min(z, 199)])[0]
                            hull_y[key] = s.YC + int(col.max()) if len(col) else s.YC
                        if yy - hull_y[key] <= 12: n += 1
            if n: block[r['name']] = n
        return mid, land, block

    def write(s, v):
        od = os.path.join(s.d, 'masks', 'rigging'); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od): os.remove(os.path.join(od, f))
        so = []
        for nm, rows, op in (('channels_carve', s.carve, 'carvevox'), ('channels_stamp', s.stamp, 'stampvox')):
            text = lst(rows)
            open(os.path.join(od, nm + '.vox.txt'), 'w', encoding='utf-8', newline='\n').write(text)
            so.append({'name': nm, 'op': op, 'file': 'masks/rigging/%s.vox.txt' % nm, 'at': [0, 0, 0], 'voxels': len(rows),
                       'origin_world': [0, 0, 0], 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})
        v['stamp_order'] = {'channels': so}
        v['anchors'] = {k: [{'name': nm, 'at': list(c), 'world': list(c), 'kind': kd} for nm, c, kd in L] for k, L in s.anchors.items()}
        v['ropes'] = [dict({k: r[k] for k in ('name', 'from', 'to', 'kind', 'group', 'thickness', 'color', 'slack', 'length')},
                           from_world=[round(float(c), 4) for c in r['from_world']], to_world=[round(float(c), 4) for c in r['to_world']]) for r in s.ropes]
        with open(os.path.join(s.d, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as fo:
            json.dump(v, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')


def main():
    d = sys.argv[1]
    r = Rig(d)
    cnt, plates = r.channels()
    r.points(); r.build_ropes()
    hits, land, block = r.collide()
    kinds = {}
    for x in r.ropes: kinds[x['kind']] = kinds.get(x['kind'], 0) + 1
    v = {'channels': cnt, 'deadeyes': {m: {k: r.de[m][k] for k in r.de[m]} for m in r.de}, 'chain_plates': plates, 'rope_counts': kinds,
         'ropes_total': len(r.ropes), 'anchors_total': sum(len(L) for L in r.anchors.values()), 'rope_hits_mid': hits,
         'rope_landing_cells': land, 'landing_max_seen': max(max(x['from'], x['to']) for x in land.values()) if land else 0,
         'landing_over_bound': sorted(k for k, x in land.items() if x['over']), 'rope_samples_in_front_of_ports': block}
    r.write(v)
    print(json.dumps({k: v[k] for k in ('channels', 'rope_counts', 'ropes_total', 'anchors_total', 'rope_hits_mid', 'landing_max_seen', 'landing_over_bound',
                                         'rope_samples_in_front_of_ports')}, ensure_ascii=False, indent=1))
    print(json.dumps({m: {k: r.de[m][k] for k in ('x', 'range', 'skipped_for_ports')} for m in r.de}, ensure_ascii=False))


if __name__ == '__main__':
    main()
