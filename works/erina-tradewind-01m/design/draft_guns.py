# 出處：erina-oxford-01m/design/draft_guns.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 步驟 9（TASK-1097）：砲 —— 全部是外部模型，掛在所在甲板的子作品上
#   主甲板（deck-gun）：每舷 2 門 4 磅砲（pinnacle 的 4 磅專用元件 ×0.5）從舷牆砲門打；
#   迴旋砲 pierrier 6 門：後甲板舷頂每舷 2、艏樓舷頂每舷 1（座的插銷底落在舷頂上一格，撞到就往上墊；砲口要伸出船殼外）
#   擺法（造船規格 §4.2）：沿砲身方向從船殼外面往裡退（每步 0.5 格），退到模型每一格的格心＋八個角（往裡縮 inset）都不在組裝件的實心格裡；
#   再看砲口有沒有伸出船殼、砲口那一點是不是空的、砲腳下有沒有甲板。S 舷 ＝ +y；P 舷 mirror=y、各自搜。
#   來源：calli-cosecha-01m/design/draft_guns.py（照抄後改：本船的炮門清單、沒有船尾追擊砲）
#   用法：python -I -X utf8 draft_guns.py <design> [--probe=push=<砲名>:<格>]（反向對照：那一門往外推幾格，印每門的碰撞樣本數，⛔ 不寫檔）
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list
from gunsim import Grid, load_guns


def r3(v):
    return [round(float(c), 3) for c in v]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    GB = plan['guns_build']
    S = GB['search']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list(GB['assembly'], None, links=None)
    G = Grid(A, pad=16)                     # 🩸 pad 4：砲口伸出舷外 ~7 格、超出網格框 ⇒ 框外當實心 ⇒ 船腰 8 門「砲口不空」的假警報
    H = export_list(GB['hull'], None)
    Hs = set(map(tuple, H[:, :3].tolist()))
    decks = {}
    for k, w in GB['deck_works'].items():
        top = {}
        for x, y, z in export_list(w, None)[:, :3].tolist():
            if z + 1 > top.get((x, y), -1):
                top[(x, y)] = z + 1
        decks[k] = top
    guns = load_guns(GB, WORKS, export_list)

    def hull_y(x, z, side):
        ys = [y for y in range(0, 2 * plan['space']['yc'] + 1) if (x, y, z) in Hs]
        return (max(ys) + 1) if side > 0 else min(ys)

    def deck_top(dk, pts):
        zs = [decks[dk][p] for p in pts if p in decks[dk]]
        return max(zs) if zs else None

    def place(g, base_xy, d_out, phi, mirror, zd, offs, beyond_fn):
        """沿 −d_out 往裡退到零碰撞；回傳 (key, cand) 的最佳者。"""
        best = None
        d_side = np.array([d_out[1], -d_out[0]])
        for dz in S['dz']:
            for off in offs:
                for k in range(int(S['back_max'] / S['step']) + 1):
                    back = k * S['step']
                    b = np.array(base_xy, float) + d_side * off - d_out * back
                    at = (float(b[0]), float(b[1]), float(zd + dz))
                    if G.hit(g.world(g.samples, at, phi, mirror)).any():
                        continue
                    tip = g.world(g.anchors['muzzle'][None], at, phi, mirror)[0]
                    beyond = beyond_fn(tip)
                    tip_free = not G.hit(tip[None])[0]
                    bot = g.world(g.bottom, at, phi, mirror)
                    below = bot.copy()
                    below[:, 2] -= 1.0
                    sup = float(G.hit(below).mean())
                    ok = bool(beyond > 0 and tip_free and sup >= GB['support_min'])
                    cand = {'at': r3(at), 'phi': phi, 'back': back, 'off': off, 'dz': dz, 'muzzle_beyond': round(float(beyond), 2),
                            'muzzle_free': tip_free, 'support': round(sup, 3), 'axis_z': round(float(tip[2]), 2), 'ok': ok}
                    key = (not ok, dz, back, abs(off))
                    if best is None or key < best[0]:
                        best = (key, cand)
                    break
        return best

    rows = []
    # ── 舷側 ──
    L = HL.Lines(plan)
    Y = LY.Layout(plan, L)
    for i, p in enumerate(Y.ports()):
        p['i'] = sum(1 for q in Y.ports()[:i] if q['deck'] == p['deck']) + 1
        p['x0'], p['x1'] = p['x'] - p['w'] // 2, p['x'] + p['w'] // 2
        p['z0'], p['z1'] = p['sill'], p['sill'] + p['h'] - 1
        g = guns[p['gun']]
        xc = (p['x0'] + p['x1'] + 1) / 2.0
        zm = (p['z0'] + p['z1']) // 2
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            outs = [hull_y(x, zm, side) for x in (p['x0'] - 2, p['x1'] + 2)]
            outer = max(outs) if side > 0 else min(outs)
            yin = [outer - side * d for d in (8, 14, 20)]   # 🩸 26 格會碰到主艙口的圍欄（P 舷多 1 格）⇒ 砲墊高 1–2 格、兩舷不對稱
            zd = deck_top(p['deck'], [(x, y) for x in (p['x0'], int(xc), p['x1']) for y in yin])
            d_out = g.direction(0.0, mirror)
            best = place(g, (xc, outer), d_out, 0.0, mirror, zd, S['dx'], lambda tip: (tip[1] - outer) * side)
            r = {'deck': p['deck'], 'port': p['i'], 'side': nm, 'type': p['gun'], 'chase': False, 'outer': outer, 'deck_z': zd,
                 'opening': {'x': [p['x0'], p['x1']], 'z': [p['z0'], p['z1']]}}
            r.update(best[1] if best else {'ok': False, 'at': None})
            rows.append(r)
    # ── 迴旋砲：舷頂上（Ship_Guns §4.2.1；擺法照飛魚號：S 舷照原樣、P 舷 mirror=y）──
    gs = guns['pierrier']
    for sw in GB['swivels']:
        x = sw['x']
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            zs = [z for (xx, y, z) in Hs if xx == x]
            ztop = max(zs)
            ys = [y for (xx, y, z) in Hs if xx == x and z == ztop]
            yr = (max(ys) - 1) if side > 0 else (min(ys) + 1)                  # 舷頂那一列的中間（外板往裡一格）
            outer = (max(ys) + 1) if side > 0 else min(ys)
            best = None
            for dz in range(1, 5):
                at = (x + 0.5, yr + 0.5, float(ztop + dz))
                if G.hit(gs.world(gs.samples, at, 0.0, mirror)).any():
                    continue
                tip = gs.world(gs.anchors['muzzle'][None], at, 0.0, mirror)[0]
                beyond = (tip[1] - outer) * side
                tip_free = not G.hit(tip[None])[0]
                best = {'at': r3(at), 'phi': 0.0, 'back': 0, 'off': 0, 'dz': dz, 'muzzle_beyond': round(float(beyond), 2), 'muzzle_free': tip_free,
                        'support': 1.0, 'axis_z': round(float(tip[2]), 2), 'ok': bool(beyond > 0 and tip_free)}
                break
            r = {'deck': sw['deck'], 'port': 'sw%d' % x, 'side': nm, 'type': 'pierrier', 'chase': False, 'outer': outer, 'deck_z': ztop}
            r.update(best or {'ok': False, 'at': None})
            rows.append(r)
    # ── 命名 ──
    cnt = {}
    for r in rows:
        pre = GB['prefix'][r['deck']]
        if r['chase']:
            r['name'] = '%s-chase-stern-%s' % (pre, r['side'])
        else:
            kind = '迴旋砲' if r['type'] == 'pierrier' else '砲'
            cnt[(kind, pre, r['side'])] = cnt.get((kind, pre, r['side']), 0) + 1
            r['name'] = '%s%s-%s%02d' % (kind, pre, r['side'], cnt[(kind, pre, r['side'])])
    rows.sort(key=lambda r: (r['type'] == 'pierrier', list(GB['prefix']).index(r['deck']), r['side'], str(r['port'])))
    for i, r in enumerate(rows, 1):
        r['id'] = 'gun-%d' % i                                # 物件 id 自己先發（迴旋砲的座 mount_of 要指它；Ship_Guns §4.2.1）

    def cells_of(r, dpush=0.0):
        g = guns[r['type']]
        at = np.array(r['at'], float)
        if dpush:
            d = g.direction(r['phi'], r['side'] == 'P')
            at[:2] += d * dpush
        return g.world(g.samples, at, r['phi'], r['side'] == 'P')

    if probe:
        nm, d = probe[0].split('=', 1)[1].rsplit(':', 1)
        rep = {}
        for r in rows:
            n = int(G.hit(cells_of(r, float(d) if r['name'] == nm else 0.0)).sum())
            if n:
                rep[r['name']] = n
        print(json.dumps({'probe': probe[0], 'hit_samples_by_gun': rep}, ensure_ascii=False))
        return
    # ── 砲跟砲不撞（格心落在同一格）──
    occ, clash = {}, []
    for r in rows:
        g = guns[r['type']]
        P = g.world(g.centers, r['at'], r['phi'], r['side'] == 'P')
        for c in set(map(tuple, np.floor(P).astype(int).tolist())):
            if c in occ and occ[c] != r['name']:
                clash.append([r['name'], occ[c]])
                break
            occ[c] = r['name']
    # ── 兩舷對稱（格 y ↔ 2·YC − y ⇒ 連續座標 y ↔ 2·YC ＋ 1 − y：P 的 at.y 應 ＝ 321 − S 的 at.y；φ 相反）──
    YC = plan['space']['yc']
    asym = []
    by = {(r['deck'], str(r['port']), r['side']): r for r in rows}
    for (dk, pt, sd), r in by.items():
        if sd != 'S':
            continue
        q = by.get((dk, pt, 'P'))
        if q and (abs(r['at'][0] - q['at'][0]) > 1e-6 or abs((2 * YC + 1 - r['at'][1]) - q['at'][1]) > 1e-6 or r['at'][2] != q['at'][2] or r['phi'] != -q['phi']):
            asym.append([r['name'], q['name'], r['at'], q['at']])
    v = {'read': {'assembly_voxels': int(len(A)), 'hull_voxels': int(len(H))}, 'guns': len(rows),
         'by_deck_type': {}, 'not_ok': [[r['name'], r.get('muzzle_beyond'), r.get('muzzle_free'), r.get('support')] for r in rows if not r['ok']],
         'gun_gun_clash': clash, 'asymmetric_pairs': asym}
    for r in rows:
        k = '%s/%s' % (r['deck'], r['type'])
        v['by_deck_type'][k] = v['by_deck_type'].get(k, 0) + 1
    for f in ('back', 'muzzle_beyond', 'support', 'axis_z', 'dz'):
        v[f] = {k: [min(r[f] for r in rows if '%s/%s' % (r['deck'], r['type']) == k), max(r[f] for r in rows if '%s/%s' % (r['deck'], r['type']) == k)] for k in v['by_deck_type']}
    v['chase'] = [{k: r[k] for k in ('name', 'phi', 'at', 'back', 'off', 'muzzle_beyond', 'muzzle_free', 'axis_z', 'tried')} for r in rows if r['chase']]
    json.dump({'note': 'draft_guns.py 的結果；at ＝ 模型的 at（pivot 落點）、phi ＝ rotate z、P 舷 mirror=y', 'rows': rows},
              open(os.path.join(design, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
