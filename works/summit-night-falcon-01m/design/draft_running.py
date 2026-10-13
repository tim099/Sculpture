# 新圖紙 10 動索（TASK-0529 階段十）：plan.json 的 running ⇒ 新固定點（帆桁底下、桅上）、動索清單、碰撞、verify_running.json。
# 用法：python -I -X utf8 -B draft_running.py <design 資料夾>
#   · 現況照 nf_state.state_after('stage10')；帆桁照 verify_yards.json 擺（預設角；gaff／boom 照 rot 轉）。
#   · 帆桁上的端點一律寫 model:<桅關聯>/yard-<帆桁>/<點> —— 帆桁一轉，繩跟著走。
#   · 新固定點：方帆桁 foot-in-S／P（中心外 inner_dy 格的底面）、foot-out-S／P（yardarm 內一格的底面）；boom sheet（top72 那一欄的底面）；
#     桅 cap-S／P（下桅 cap 的鐵、兩側）、tm-cap-S／P（中桅 cap 兩側）；主桅 brace-S／P（top 下 brace_block_below_top 格的桅側）、
#     top-aft（同高度的桅後面，topping lift）、tm-head-aft（中桅 crosstrees 下 1 格的桅後面，peak halyard）。
#   · pin 分配：每條 fall 指定一根 rail（或 fife 的一邊），取那根 rail 上還沒用過、x 離繩上端最近的 pin；P 舷走 繫繩欄-鏡像（y → 161 − y）。
#   · 碰撞：同階段九（中段要 0、著陸分開報）；slack > 1 的繩照拋物線下垂取樣（垂度 ≈ L·√(3(slack−1)/8)）。
#   · 重跑逐位元組相同。
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC
from nf_state import state_after, NX, NY, NZ
from draft_yards import rot

PRE = 'summit-night-falcon-01m'
G = lambda v: ','.join('%.4f' % c for c in v)
LINKW = {'前桅': 'mast_fore', '主桅': 'mast_main', 'fife-rails': 'fife', '繫繩欄': 'side_S', '繫繩欄-鏡像': 'side_P'}


class Run:
    def __init__(s, d):
        s.d = d
        s.plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
        s.R = s.plan['running']; s.M = s.plan['masts']
        s.W = state_after(d, 'stage10')
        s.Y = {p['member']: p for p in json.load(open(os.path.join(d, 'verify_yards.json'), encoding='utf-8'))['placements']}
        s.YE = json.load(open(os.path.join(d, 'verify_yards.json'), encoding='utf-8'))['anchors_expect']
        s.RG = json.load(open(os.path.join(d, 'verify_rigging.json'), encoding='utf-8'))['anchors']
        s.BL = json.load(open(os.path.join(d, 'verify_belaying.json'), encoding='utf-8'))
        s.new = {}          # 作品 id → [(名字, 子作品座標格, 種類)]
        s.pt = {}           # 端點字串 → 世界座標（格心）
        s.ropes = []; s.used = set()
        s.yard_cells = {}
        for nm, P in s.Y.items():
            a = np.loadtxt(os.path.join(d, P['file']), delimiter=',', dtype=int, ndmin=2)
            s.yard_cells[nm] = a

    # ── 帆桁上的點（子作品座標 → 世界）──
    def ywork(s, nm):
        return s.Y[nm]['work']

    def yworld(s, nm, loc):
        P = s.Y[nm]; c = [loc[i] + P['origin'][i] + 0.5 for i in range(3)]
        return rot(c, P['at'], P['rotate'][1], P['rotate'][2])

    def ymodel(s, nm, anchor, loc=None):
        P = s.Y[nm]
        key = 'model:%s/%s/%s' % (P['link'], P['model'], anchor)
        if loc is not None: s.pt[key] = s.yworld(nm, loc)
        elif key not in s.pt: s.pt[key] = s.YE[nm][anchor]
        return key

    def yard_anchors(s):
        F = s.R['footrope']
        for nm, P in s.Y.items():
            a = s.yard_cells[nm]; L = []
            if P['meta']['yard'] in ('course', 'topsail', 'topgallant'):
                piv = [p for p in P['anchors'] if p['name'] == 'pivot'][0]['at']
                h = (a[:, 1].max() - a[:, 1].min()) // 2
                for sd, sg in (('S', 1), ('P', -1)):
                    for tag, dy in (('foot-in', F['inner_dy']), ('foot-out', h - 1)):
                        y = piv[1] + sg * dy
                        col = a[(a[:, 0] == piv[0]) & (a[:, 1] == y)]
                        L.append(('%s-%s' % (tag, sd), (int(piv[0]), int(y), int(col[:, 2].min())), 'footrope'))
            if nm == 'main-gaff':
                # 帆頭沿 gaff 的底面（階段十一）—— 🩸 主帆第一版綁 gaff 的 top 點（頂面），模擬後布從 gaff 身體裡穿過去 12 點
                for du in (8, 64):
                    t = [p for p in P['anchors'] if p['name'] == 'top%d' % du][0]['at']
                    col = a[(a[:, 0] == t[0]) & (a[:, 1] == t[1])]
                    L.append(('bot%d' % du, (int(t[0]), int(t[1]), int(col[:, 2].min())), 'sail-head'))
            if nm == 'main-boom':
                t = [p for p in P['anchors'] if p['name'] == 'top72'][0]['at']
                col = a[(a[:, 0] == t[0]) & (a[:, 1] == t[1])]
                L.append(('sheet', (int(t[0]), int(t[1]), int(col[:, 2].min())), 'sheet'))
            if L: s.new[P['work']] = L
            for n2, c, k in L: s.ymodel(nm, n2, c)

    # ── 桅上的點（世界座標 ＝ 子作品座標）──
    def mast_anchors(s):
        for m in ('fore', 'main'):
            A = s.W['mast_' + m]; S = s.M[m]; L = []; iron = s.M['colors']['iron']
            def side_of(z, col=None):
                sel = (A[:, :, z] == col) if col else (A[:, :, z] > 0)
                xs = np.nonzero(sel[:, YC])[0]; xa = int((xs.min() + xs.max()) // 2)
                ys = np.nonzero(sel[xa, :])[0]
                return (xa, int(ys.max()), z), (xa, int(ys.min()), z)
            for tag, z in (('cap', S['lower_head_z']), ('tm-cap', S['topmast_head_z'])):
                a, b = side_of(z, iron); L += [(tag + '-S', a, 'lift'), (tag + '-P', b, 'lift')]
            if m == 'main':
                zb = S['top_z'] - s.R['points']['brace_block_below_top']
                xs = np.nonzero(A[:, YC, zb])[0]; L.append(('top-aft', (int(xs.min()), YC, zb), 'topping-lift'))
                zc = S['topmast_head_z'] - S['tm_doubling'] - 1
                xs = np.nonzero(A[:, YC, zc])[0]; L.append(('tm-head-aft', (int(xs.min()), YC, zc), 'peak-halyard'))
            for n2, c, k in L: assert A[c] > 0, (m, n2, c)
            s.new[PRE + '-mast-' + m] = L
            lk = {'fore': '前桅', 'main': '主桅'}[m]
            for n2, c, k in L: s.pt['%s/%s' % (lk, n2)] = [c[i] + 0.5 for i in range(3)]
            for a in s.RG['mast_' + m]: s.pt['%s/%s' % (lk, a['name'])] = [a['world'][i] + 0.5 for i in range(3)]

    # ── pins ──
    def pins(s):
        s.pin = {}
        for a in s.BL['anchors']['fife']:
            s.pin['fife-rails/' + a['name']] = [a['world'][i] + 0.5 for i in range(3)]
        for a in s.BL['anchors']['side']:
            w = [a['world'][i] + 0.5 for i in range(3)]
            s.pin['繫繩欄/' + a['name']] = w
            s.pin['繫繩欄-鏡像/' + a['name']] = [w[0], 161.0 - w[1], w[2]]
        s.pt.update(s.pin)

    def pick(s, prefix, near_x):
        c = [k for k in s.pin if k.startswith(prefix) and k not in s.used]
        assert c, ('沒有空的 pin', prefix)
        k = min(c, key=lambda k: (abs(s.pin[k][0] - near_x), k)); s.used.add(k); return k

    def lead(s, pin):
        # 導點：pin 那一欄船殼最高那一層（頂蓋）最靠裡那一格的內緣往裡 0.3、頂面上 0.3
        p = s.pt[pin]; x = int(math.floor(p[0])); sg = 1 if p[1] > YC + 0.5 else -1
        side = s.W['hull'][x, YC + 10:, :] if sg > 0 else s.W['hull'][x, :YC - 9, :][::-1]
        zt = int(np.nonzero(side.any(0))[0].max())
        dyi = int(np.nonzero(side[:, zt])[0].min()) + 10
        y = YC + dyi - 0.3 if sg > 0 else 161.0 - (YC + dyi - 0.3)
        return [p[0], y, zt + 1.3]

    def rail(s, n, side):
        return ('繫繩欄/pinrail-%d.' if side == 'S' else '繫繩欄-鏡像/pinrail-%d.') % n

    # ── 繩 ──
    def rope(s, name, fr, to, kind, group, slack=None):
        s.ropes.append({'name': name, 'from': fr, 'to': to, 'kind': kind, 'group': group, 'color': s.R['color'],
                        'thickness': s.R['thickness'][kind], 'slack': slack or s.R['slack']})

    def build(s):
        T = 'running/'
        sq = {'fore-course': ('前桅', 'cap'), 'fore-topsail': ('前桅', 'tm-cap'), 'fore-topgallant': ('前桅', 'tg-head'), 'main-topsail': ('主桅', 'tm-cap'),
              'main-course': ('主桅', 'cap')}
        # 🩸 v1：course 的 fall 落主桅 fife（貼著主桅跑 8 格）、topgallant brace 到主桅 tm-head（落點前先穿過 crosstrees）⇒ 都改
        # 階段十一：主桅加了下桁（z 130，在主桅前面）—— 原本 fore course brace 的滑車就在主桅那一高度的側面 ⇒ 改直接落船腰 rail 6（一段）
        brace = {'fore-course': (None, ('rail', 6)), 'main-course': (None, ('rail', 4)),
                 'fore-topsail': ('主桅/cross-%s', ('rail', 5)), 'fore-topgallant': ('主桅/cross-%s', ('rail', 5)),   # 🩸 v2 落 rail 7（往前下）⇒ 擦主桅 topsail yard 的背面 ⇒ 往後落後甲板
                 'main-topsail': (None, ('rail', 3))}
        # 🩸 v1：topsail 的 tye 從 sling 直上 cap 前面 —— 頂桅的跟就站在 topsail yard 正上方（doubling）⇒ 穿過 24–25 格；fall 從 cap 側面下 ⇒ 擦 crosstrees／穿過下面那根帆桁
        #     ⇒ tye 拉到 crosstrees 那一舷的端點、fall 從同一個端點下
        halyard = {'fore-topsail': ('前桅/cross-S', '前桅/cross-S', ('rail', 9, 'S')), 'fore-topgallant': ('前桅/tg-head-fwd', '前桅/cross-P', ('rail', 9, 'P')),
                   'main-topsail': ('主桅/cross-S', '主桅/cross-S', ('rail', 5, 'S'))}
        for nm, (lk, lift) in sq.items():
            for sd in ('S', 'P'):
                arm = s.ymodel(nm, 'arm-' + sd)
                self_lift = '%s/%s-%s' % (lk, lift, sd)
                s.rope('%s-lift-%s' % (nm, sd), arm, self_lift, 'lift', T + 'lifts')
                fo, fi = s.ymodel(nm, 'foot-out-' + sd), s.ymodel(nm, 'foot-in-' + sd)
                s.rope('%s-footrope-%s' % (nm, sd), fo, fi, 'footrope', T + 'footropes', s.R['footrope']['slack'])
                blk, fall = brace[nm]
                if blk:
                    b = blk % sd
                    s.rope('%s-brace-%s' % (nm, sd), arm, b, 'brace', T + 'braces')
                    pin = s.pick(s.rail(fall[1], sd), s.pt[b][0])
                    s.rope('%s-brace-fall-%s' % (nm, sd), b, pin, 'fall', T + 'braces')
                else:
                    # 從舷外（yardarm）直接落舷牆裡的 pin，一定會在最後 1.5 格擦過頂蓋的內角（量到 104）⇒ 在頂蓋內緣上方放一個導點（真船：rail 上的 sheave／fairlead）
                    pin = s.pick(s.rail(fall[1], sd), s.pt[arm][0])
                    lead = s.lead(pin)
                    s.rope('%s-brace-%s' % (nm, sd), arm, G(lead), 'brace', T + 'braces')
                    s.pt[G(lead)] = lead
                    s.rope('%s-brace-lead-%s' % (nm, sd), G(lead), pin, 'fall', T + 'braces')
            if nm in halyard:
                tie, top, (_, rn, sd) = halyard[nm]
                s.rope('%s-halyard' % nm, s.ymodel(nm, 'sling'), tie, 'halyard', T + 'halyards')
                s.rope('%s-halyard-fall' % nm, top, s.pick(s.rail(rn, sd), s.pt[top][0]), 'fall', T + 'halyards')
        g = 'main-gaff'
        for t in ('top24', 'top48'):
            s.rope('main-gaff-peak-halyard-%s' % t, s.ymodel(g, t), '主桅/tm-head-aft', 'halyard', T + 'gaff')
        s.rope('main-gaff-peak-halyard-fall', '主桅/tm-head-S', s.pick(s.rail(5, 'S'), s.pt['主桅/tm-head-S'][0]), 'fall', T + 'gaff')
        for sd in ('S', 'P'):
            pk = s.ymodel(g, 'peak')
            s.rope('main-gaff-vang-%s' % sd, pk, s.pick(s.rail(2, sd), s.pt[pk][0]), 'vang', T + 'gaff')
        # 🩸 v1 一條在中線、到主桅 top 下的後面 —— 中線上從 boom 尾往上到桅的線一定會跟往後上翹的 gaff 交叉（量到穿過 gaff 7 格）⇒ 兩舷各一條、到下桅 cap 兩側
        for sd in ('S', 'P'):
            s.rope('main-boom-topping-lift-%s' % sd, s.ymodel('main-boom', 'end'), '主桅/cap-%s' % sd, 'topping_lift', T + 'boom')
        s.pt['fife-rails/horse'] = s.pin['fife-rails/horse']
        s.rope('main-sheet', s.ymodel('main-boom', 'sheet'), 'fife-rails/horse', 'sheet', T + 'boom')

    def key_of(s, e):
        if e.startswith('model:'):
            nm = e.split('/')[1][len('yard-'):]; return 'yard:' + nm
        return LINKW.get(e.split('/')[0])

    def collide(s):
        world = {k: v > 0 for k, v in s.W.items()}
        for nm, P in s.Y.items():
            g = np.zeros((NX, NY, NZ), bool)
            for c in s.yard_cells[nm][:, :3] + np.asarray(P['origin']):
                q = rot([c[i] + 0.5 for i in range(3)], P['at'], P['rotate'][1], P['rotate'][2])
                g[tuple(int(math.floor(v)) for v in q)] = True
            world['yard:' + nm] = g
        ce = s.plan['rigging']['clear_ends']; mid = {}; land = {}
        for r in s.ropes:
            p0, p1 = np.array(s.pt[r['from']], float), np.array(s.pt[r['to']], float); L = float(np.linalg.norm(p1 - p0))
            sag = L * math.sqrt(3 * (r['slack'] - 1) / 8) if r['slack'] > 1 else 0.0
            ts = [t for t in np.arange(0, L, 0.25) if ce <= t <= L - ce]
            hs = []
            for t in ts:
                u = t / L; q = p0 + (p1 - p0) * u - np.array([0, 0, 4 * sag * u * (1 - u)])
                hs.append({k for k, v in world.items() if v[tuple(int(math.floor(c)) for c in q)]})
            kf, kt = s.key_of(r['from']), s.key_of(r['to'])
            lo, hi = 0, len(hs)
            while lo < hi and kf and kf in hs[lo]: lo += 1
            while hi > lo and kt and kt in hs[hi - 1]: hi -= 1
            if lo or hi < len(hs): land[r['name']] = round(max(lo, len(hs) - hi) * 0.25, 2)
            m = {}
            for h in hs[lo:hi]:
                for k in h: m[k] = m.get(k, 0) + 1
            if m: mid[r['name']] = m
            r['length'] = round(L, 3); r['sag_est'] = round(sag, 3)
            r['from_world'] = [round(float(c), 4) for c in p0]; r['to_world'] = [round(float(c), 4) for c in p1]
        return mid, land


def main():
    d = sys.argv[1]
    r = Run(d); r.yard_anchors(); r.mast_anchors(); r.pins(); r.build()
    mid, land = r.collide()
    kinds = {}
    for x in r.ropes: kinds[x['kind']] = kinds.get(x['kind'], 0) + 1
    V = {'anchors_new': {w: [{'name': n, 'at': list(c), 'kind': k} for n, c, k in L] for w, L in r.new.items()},
         'ropes': r.ropes, 'rope_counts': kinds, 'ropes_total': len(r.ropes), 'pins_used': sorted(r.used),
         'rope_hits_mid': mid, 'rope_landing_cells': land, 'landing_max_seen': max(land.values()) if land else 0}
    with open(os.path.join(d, 'verify_running.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(V, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: V[k] for k in ('rope_counts', 'ropes_total', 'pins_used', 'rope_hits_mid', 'rope_landing_cells', 'landing_max_seen')}, ensure_ascii=False, indent=1))
    print({w: len(L) for w, L in V['anchors_new'].items()})


if __name__ == '__main__':
    main()
