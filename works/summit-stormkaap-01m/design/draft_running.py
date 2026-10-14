# 新圖紙 09b 動索（TASK-0547 階段九）：plan.json 的 running ⇒ 新固定點（帆桁底下、桅上）、動索清單、碰撞、verify_running.json。
# 用法：python -I -X utf8 -B draft_running.py <design 資料夾>
#   · 從夜隼號 draft_running.py（TASK-0529 階段十）改：三根桅、9 根方帆桁＋lateen；走法照 plan provenance running（⛔ 沒有查證）。
#   · 現況：sk_world.World（船＋桅＋channels v2＋帆桁轉好）＋ fife rails（verify_belaying.json 的清單）。
#   · 帆桁上的端點一律寫 model:<桅關聯>/yard-<帆桁>/<點> —— 帆桁一轉，繩跟著走。
#   · 新固定點：方帆桁 foot-in-S／P（中心外 inner_dy 格那一欄的底面）、foot-out-S／P（yardarm 內一格的底面）；
#     桅 cap-S／P（下桅 cap 的鐵、兩側）、主／前桅 tm-cap-S／P（上桅 cap 兩側）；主桅 brace-S／P（前 course 那一高度的桅側）。
#   · pin：每條 fall 指定一根桅的 fife、一舷，取那一舷還沒用過、x 離繩上端最近的 pin。
#   · 碰撞：同階段八（中段要 0；著陸上限：端點在桅上 ＝ max(landing_max, 1／sin α)，其他 ＝ landing_max）；
#     slack > 1 的繩照拋物線下垂取樣（垂度 ≈ L·√(3(slack−1)/8)）。
#   · 重跑逐位元組相同。
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_world import World, rot, load

PRE = 'summit-stormkaap-01m'
G = lambda v: ','.join('%.4f' % c for c in v)
LINKKEY = {'後桅': 'mast_mizzen', '主桅': 'mast_main', '前桅': 'mast_fore', '船首斜桅': 'bowsprit', 'fife-rails': 'fife', '船殼': 'hull'}
MLINK = {'mizzen': '後桅', 'main': '主桅', 'fore': '前桅'}


class Run:
    def __init__(s, d):
        s.d = d
        BL = json.load(open(os.path.join(d, 'verify_belaying.json'), encoding='utf-8'))
        fife = load(os.path.join(d, BL['stamp_order']['fiferails'][0]['file']))
        s.w = World(d, with_yards=True, extra=[('fife', fife[:, :3])])
        s.plan = s.w.plan; s.R = s.plan['running']; s.YC = s.w.YC
        YV = json.load(open(os.path.join(d, 'verify_yards.json'), encoding='utf-8'))
        s.Y = {p['member']: p for p in YV['placements']}; s.YE = YV['anchors_expect']
        s.RG = json.load(open(os.path.join(d, 'verify_rigging.json'), encoding='utf-8'))['anchors']
        s.info = json.load(open(os.path.join(d, 'verify_masts.json'), encoding='utf-8'))['info']
        s.BL = BL
        s.new = {}; s.pt = {}; s.ropes = []; s.used = set()
        s.ycells = {nm: load(os.path.join(d, P['file'])) for nm, P in s.Y.items()}
        for m, L in s.RG.items():
            if m.startswith('mast_'):
                for a in L: s.pt['%s/%s' % (MLINK[m[5:]], a['name'])] = [a['world'][i] + 0.5 for i in range(3)]
        for a in s.RG['bowsprit']: s.pt['船首斜桅/' + a['name']] = [a['world'][i] + 0.5 for i in range(3)]
        s.pin = {}
        for a in BL['anchors']['fife']: s.pin['fife-rails/' + a['name']] = [a['world'][i] + 0.5 for i in range(3)]
        for a in BL['anchors']['hull']: s.pt['船殼/' + a['name']] = [a['world'][i] + 0.5 for i in range(3)]
        s.pt.update(s.pin)

    # ── 帆桁 ──
    def ymodel(s, nm, anchor, loc=None):
        P = s.Y[nm]; key = 'model:%s/%s/%s' % (P['link'], P['model'], anchor)
        if loc is not None:
            c = [loc[i] + P['origin'][i] + 0.5 for i in range(3)]
            s.pt[key] = rot(c, P['at'], P['rotate'][1], P['rotate'][2])
        elif key not in s.pt:
            s.pt[key] = s.YE[nm][anchor]
        return key

    def yard_anchors(s):
        F = s.R['footrope']
        for nm, P in s.Y.items():
            if P['meta']['yard'] == 'lateen': continue
            a = s.ycells[nm]; L = []
            piv = [p for p in P['anchors'] if p['name'] == 'pivot'][0]['at']
            h = (a[:, 1].max() - a[:, 1].min()) // 2
            for sd, sg in (('S', 1), ('P', -1)):
                # 🩸 第一版 footrope 兩端綁在底面那一格 ⇒ 帆桁中間粗、兩頭細，兩端之間的直線從帆桁底部穿過去（4–8 個取樣）⇒ 綁在底面下一格（吊 footrope 的那一點；框有 1 格餘裕）
                for tag, dy in (('foot-in', F['inner_dy']), ('foot-out', h - 1)):
                    y = piv[1] + sg * dy
                    col = a[(a[:, 0] == piv[0]) & (a[:, 1] == y)]
                    L.append(('%s-%s' % (tag, sd), (int(piv[0]), int(y), int(col[:, 2].min()) - 1), 'footrope'))
                # 🩸 第一版 lift 從 arm（yardarm 的軸心）出發 ⇒ 斜著往上、出去之後又碰到往中間變粗的桁身；
                #    第二版從 yardarm 那一欄頂面那一格出發 ⇒ topsail 的 lift 每格只升 0.34、往內 4 格桁身變粗頂面升一格，又擦到 ⇒ 頂面上一格
                y = piv[1] + sg * h
                col = a[(a[:, 0] == piv[0]) & (a[:, 1] == y)]
                L.append(('lift-%s' % sd, (int(piv[0]), int(y), int(col[:, 2].max()) + 1), 'lift'))
            s.new[P['work']] = L
            for n2, c, k in L: s.ymodel(nm, n2, c)

    # ── 桅 ──
    def mast_anchors(s):
        iron = s.plan['masts']['colors']['iron']
        for m in ('mizzen', 'main', 'fore'):
            a = s.w.mast[m]; I = s.info[m]; L = []
            def sides(z, color=None):
                q = a[a[:, 2] == z]
                if color is not None: q = q[q[:, 3] == color]
                c = q[q[:, 1] == s.YC]; xa = int((c[:, 0].min() + c[:, 0].max()) // 2)
                col = q[q[:, 0] == xa]
                return (xa, int(col[:, 1].max()), z), (xa, int(col[:, 1].min()), z)
            pairs = [('cap', I['lower_top_z'], iron)]
            if m != 'mizzen': pairs.append(('tm-cap', I['topmast_top_z'], iron))
            if m == 'main':
                zb = s.Y['fore-course']['at'][2] - 0.5
                pairs.append(('brace', int(zb), None))
            for tag, z, col in pairs:
                p, q = sides(z, col); L += [(tag + '-S', p, 'running'), (tag + '-P', q, 'running')]
            cells = {tuple(r[:3]) for r in a}
            for n2, c, k in L: assert c in cells, (m, n2, c)
            s.new['%s-mast-%s' % (PRE, m)] = L
            for n2, c, k in L: s.pt['%s/%s' % (MLINK[m], n2)] = [c[i] + 0.5 for i in range(3)]

    def pick(s, m, side, near_x):
        pre = 'fife-rails/fife-%s-%s' % (m, side)
        c = [k for k in s.pin if k.startswith(pre) and k not in s.used]
        assert c, ('沒有空的 pin', m, side)
        k = min(c, key=lambda k: (abs(s.pin[k][0] - near_x), k)); s.used.add(k); return k

    # ── 繩 ──
    def rope(s, name, fr, to, kind, group, slack=None):
        assert fr in s.pt and to in s.pt, (name, fr, to)
        s.ropes.append({'name': name, 'from': fr, 'to': to, 'kind': kind, 'group': group, 'color': s.R['color'],
                        'thickness': s.R['thickness'][kind], 'slack': slack or s.R['slack']})

    def build(s):
        T = 'running/'
        lift = {'main-course': '主桅/cap-%s', 'fore-course': '前桅/cap-%s', 'main-topsail': '主桅/tm-cap-%s', 'fore-topsail': '前桅/tm-cap-%s',
                'main-topgallant': '主桅/tg-head-%s', 'fore-topgallant': '前桅/tg-head-%s', 'mizzen-topsail': '後桅/tm-head-%s',
                'spritsail': '船首斜桅/stay-tm', 'sprit-topsail': '船首斜桅/sprit-head'}
        brace = {'fore-course': ('主桅/brace-%s', 'main'), 'main-course': ('船殼/kevel-kamp-%s', None),
                 'fore-topsail': ('主桅/rim-fwd-%s', None), 'fore-topgallant': ('主桅/cross-%s', None),
                 'main-topsail': ('後桅/tm-head-%s', None), 'main-topgallant': ('後桅/tm-head-%s', None),
                 'mizzen-topsail': ('主桅/rim-aft-%s', None), 'spritsail': ('船殼/kevel-bak-%s', None), 'sprit-topsail': ('前桅/rim-fwd-%s', None)}
        halyard = {'main-topsail': ('主桅/cross-S', '主桅/cross-S', '主桅/rim-aft-S'), 'fore-topsail': ('前桅/cross-S', '前桅/cross-S', '前桅/rim-aft-S'),
                   'main-topgallant': ('主桅/tg-head-fwd', '主桅/tg-head-P', '主桅/cross-P'), 'fore-topgallant': ('前桅/tg-head-fwd', '前桅/tg-head-P', '前桅/cross-P'),
                   'mizzen-topsail': ('後桅/tm-head-fwd', '後桅/tm-head-S', '後桅/rim-aft-S')}
        for nm in lift:
            for sd in ('S', 'P'):
                arm = s.ymodel(nm, 'arm-' + sd)
                tgt = lift[nm] % sd if '%s' in lift[nm] else lift[nm]
                s.rope('%s-lift-%s' % (nm, sd), s.ymodel(nm, 'lift-' + sd), tgt, 'lift', T + 'lifts')
                s.rope('%s-footrope-%s' % (nm, sd), s.ymodel(nm, 'foot-out-' + sd), s.ymodel(nm, 'foot-in-' + sd), 'footrope', T + 'footropes',
                       s.R['footrope']['slack'])
                b, fall_m = brace[nm]; b = b % sd
                s.rope('%s-brace-%s' % (nm, sd), arm, b, 'brace', T + 'braces')
                if fall_m:
                    s.rope('%s-brace-fall-%s' % (nm, sd), b, s.pick(fall_m, sd, s.pt[b][0]), 'fall', T + 'braces')
            if nm in halyard:
                tie, top, end = halyard[nm]
                s.rope('%s-halyard' % nm, s.ymodel(nm, 'sling'), tie, 'halyard', T + 'halyards')
                s.rope('%s-halyard-fall' % nm, top, end, 'fall', T + 'halyards')
        L = 'mizzen-lateen'
        s.rope('mizzen-lateen-halyard', s.ymodel(L, 'sling'), '後桅/hounds-P', 'halyard', T + 'lateen')
        s.rope('mizzen-lateen-halyard-fall', '後桅/hounds-P', s.pick('mizzen', 'P', s.pt['後桅/hounds-P'][0]), 'fall', T + 'lateen')
        for sd in ('S', 'P'):
            s.rope('mizzen-lateen-vang-%s' % sd, s.ymodel(L, 'arm-A'), '船殼/kevel-kamp-%s' % sd, 'vang', T + 'lateen')

    def key_of(s, e):
        if e.startswith('model:'): return 'yard:' + e.split('/')[1][len('yard-'):]
        return LINKKEY.get(e.split('/')[0])

    def collide(s):
        lab, names = s.w.lab, s.w.names
        ce = s.plan['rigging']['clear_ends']; lm = s.plan['rigging']['landing_max']; mid = {}; land = {}
        for r in s.ropes:
            p0, p1 = np.array(s.pt[r['from']], float), np.array(s.pt[r['to']], float); L = float(np.linalg.norm(p1 - p0))
            sag = L * math.sqrt(3 * (r['slack'] - 1) / 8) if r['slack'] > 1 else 0.0
            ts = [t for t in np.arange(0, L, 0.25) if ce <= t <= L - ce]
            hs = []
            for t in ts:
                u = t / L; q = p0 + (p1 - p0) * u - np.array([0, 0, 4 * sag * u * (1 - u)])
                v = lab[tuple(int(math.floor(c)) for c in q)]; hs.append(names[v] if v else None)
            kf, kt = s.key_of(r['from']), s.key_of(r['to'])
            lo, hi = 0, len(hs)
            while lo < hi and kf and hs[lo] == kf: lo += 1
            while hi > lo and kt and hs[hi - 1] == kt: hi -= 1
            if lo or hi < len(hs):
                u = (p1 - p0) / L; sa = max(math.hypot(u[0], u[1]), 1e-6)
                bd = lambda k: max(lm, 1.0 / sa) if k and k.startswith('mast_') else lm
                l0, l1 = lo * 0.25, (len(hs) - hi) * 0.25
                land[r['name']] = {'from': l0, 'to': l1, 'over': l0 > bd(kf) or l1 > bd(kt)}
            m = {}
            for h in hs[lo:hi]:
                if h: m[h] = m.get(h, 0) + 1
            if m: mid[r['name']] = m
            r['length'] = round(L, 3); r['sag_est'] = round(sag, 3)
            r['from_world'] = [round(float(c), 4) for c in p0]; r['to_world'] = [round(float(c), 4) for c in p1]
        return mid, land


def main():
    d = sys.argv[1]
    r = Run(d); r.yard_anchors(); r.mast_anchors(); r.build()
    mid, land = r.collide()
    kinds = {}
    for x in r.ropes: kinds[x['kind']] = kinds.get(x['kind'], 0) + 1
    V = {'anchors_new': {w: [{'name': n, 'at': list(c), 'kind': k} for n, c, k in L] for w, L in r.new.items()},
         'anchors_expect': {k: [round(float(c), 4) for c in v] for k, v in sorted(r.pt.items()) if k.startswith('model:')},
         'ropes': r.ropes, 'rope_counts': kinds, 'ropes_total': len(r.ropes), 'pins_used': sorted(r.used),
         'rope_hits_mid': mid, 'rope_landing_cells': land, 'landing_over_bound': sorted(k for k, x in land.items() if x['over'])}
    with open(os.path.join(d, 'verify_running.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(V, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: V[k] for k in ('rope_counts', 'ropes_total', 'pins_used', 'rope_hits_mid', 'landing_over_bound')}, ensure_ascii=False, indent=1))
    print({w: len(L) for w, L in V['anchors_new'].items()})


if __name__ == '__main__':
    main()
