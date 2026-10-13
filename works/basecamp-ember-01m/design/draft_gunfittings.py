# 餘燼號 階段十二 砲具與砲索（plan.json gunfittings_build；新圖紙 12）—— 憲法號 draft_gunfittings.py（新圖紙 19、階段二十二）改寫成兩層
#   下層砲甲板（32 磅長砲 16／舷）、上層砲甲板（24 磅 16／舷）各一件「砲具（一舷）」子作品，另一舷 mirror=y 關聯（45 對砲兩舷逐對對稱 ⇒ 可以）：
#   · 船牆上的環：砲中線往船尾／船頭 offset 格、甲板面 ＋8；一格鐵釘進牆、外面一格當環；繩（砲尾 → 環、eye → 環）不准穿過別的實心（自己這門砲不算），
#     另一舷鏡過去也量；不行就換 offset，都不行就不放（照實記）
#   · 甲板上的環：砲架尾（train）往船裡 back 格
#   · shot garland：相鄰兩門之間靠牆、甲板面 ＋2；rammer／sponge：砲正上方、天花板底下
#   · 繩：breeching ×2、side tackle ×2、train tackle ×1（同憲法號的數值）；端點 model:<甲板>/<砲>/<點> → <甲板>/砲具[-鏡像]/<環>
#   牆從船殼量（環要釘在船殼上）；擋不擋從「組裝件（藏這一階段的關聯）＋ 所有砲模型的格」量（模型不在 voxel 匯出裡）。
#   ⇒ masks/gunfittings/<deck>.vox.txt（一舷、自己的座標）、gunfittings_points.json、gun_ropes.json、verify_gunfittings.json
# 用法：python -I draft_gunfittings.py <design 資料夾>
import sys, os, json, hashlib, collections, math
import numpy as np
from scipy import ndimage

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import draft_profile as DP                               # noqa: E402
from draft_ladders import existing_links, export_hidden  # noqa: E402
import place_guns as PG                                  # noqa: E402

YC = 160
ZMAX = 200


class Fit:
    def __init__(s):
        s.plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['gunfittings_build']
        s.GB = s.plan['guns_build']
        have = set(existing_links(s.P['assembly']))
        s.hidden = [h for h in s.P['hide_links'] if h in have]
        a = export_hidden(s.P['assembly'], s.hidden)
        assert len(a) == s.P['assembly_voxels'], ('組裝件現況對不上', len(a), s.P['assembly_voxels'])
        m = a[a[:, 2] < ZMAX]
        s.W = np.zeros((1100, 320, ZMAX), np.uint8)
        s.W[m[:, 0], m[:, 1], m[:, 2]] = m[:, 3]
        h = DP.export_list(s.GB['hull'], links='none')
        h = h[h[:, 2] < ZMAX]
        s.H = np.zeros((1100, 320, ZMAX), bool)
        s.H[h[:, 0], h[:, 1], h[:, 2]] = True
        s.rows = json.load(open(os.path.join(D, 'guns_placement.json'), encoding='utf-8'))['rows']
        s.guns = {}
        s.gun_cells = {}
        for k, t in s.GB['types'].items():
            src = os.path.join(D, t['cells']) if t['cells'].startswith('masks/') else t['cells']
            s.guns[k] = PG.Gun(k, t['work'], PG.load_cells(src), t['scale'], t['pivot'], t['muzzle'], t['meta'])
        s.anch = {k: s.anchors_of(t['work']) for k, t in s.GB['types'].items()}
        # 所有砲模型的格 ⇒ 擋繩（砲名 → 格集合）
        for r in s.rows:
            g = s.guns[r['type']]
            Wp = g.world(g.samples, r['at'], r['phi'], r['side'] == 'P')
            cells = set(map(tuple, np.floor(Wp).astype(int).tolist()))
            s.gun_cells[r['name']] = cells
            for c in cells:
                if 0 <= c[2] < ZMAX:
                    s.W[c] = max(int(s.W[c]), 1)
        s.cells, s.kind = {}, {}
        s.notes = []

    def anchors_of(s, work):
        p = os.path.join(DP.CON_DESIGN, '..', '..', work, 'anchors.json')
        p = os.path.normpath(p)
        return {a['name']: a['at'] for a in json.load(open(p, encoding='utf-8'))['anchors']}

    def point(s, r, name):
        g = s.guns[r['type']]
        loc = np.array(s.anch[r['type']][name], float) + 0.5
        return g.world(loc[None], r['at'], r['phi'], r['side'] == 'P')[0]

    def solid(s, k):
        return s.W[k] > 0

    def blocked(s, a, b, own, extra=()):
        a, b = np.array(a, float), np.array(b, float)
        n = int(np.linalg.norm(b - a) * 3) + 2
        hit = []
        for t in np.linspace(0, 1, n):
            q = tuple(int(np.floor(v)) for v in a + (b - a) * t)
            if q in own or q in extra or q in s.cells:
                continue
            if s.W[q] > 0:
                hit.append(q)
        return hit

    def put(s, k, c, kind):
        if k in s.cells or s.W[k] > 0:
            return False
        s.cells[k] = int(c)
        s.kind[k] = kind
        return True

    def wall_y(s, x, z):
        """S 舷船殼內面（從中線往外第一格船殼）"""
        col = np.where(s.H[x, YC + 15:320, z])[0]
        return YC + 15 + int(col.min()) if len(col) else None

    def build(s):
        P, col = s.P, s.P['colors']
        m = lambda p: (p[0], 2 * YC - p[1], p[2])
        mc = lambda v: np.array([v[0], 2 * YC + 1 - v[1], v[2]])
        s.by_deck = {}
        s.ropes = []
        for dk in P['decks']:
            deck = dk['deck']
            guns = sorted([r for r in s.rows if r['deck'] == deck and not r['chase'] and r['side'] == 'S'], key=lambda r: r['at'][0])
            out = []
            for r in guns:
                rP = next(q for q in s.rows if q['name'] == r['name'].replace('-S', '-P'))
                own, ownP = s.gun_cells[r['name']], s.gun_cells[rP['name']]
                c = int(math.floor(r['at'][0]))
                zd = int(r['at'][2])
                casc = s.point(r, 'cascabel')
                row = {'name': r['name'], 'port': r['port'], 'c': c, 'deck_z': zd, 'rings': {}, 'deck_ring': None}
                for side, sg, eye in (('aft', -1, 'eye-aft'), ('fwd', 1, 'eye-fwd')):
                    z = zd + P['ring']['z_above_deck']
                    done = None
                    for off in P['ring']['offset']:
                        x = c + sg * off
                        yw = s.wall_y(x, z)
                        if yw is None:
                            continue
                        stem, ring = (x, yw - 1, z), (x, yw - 2, z)
                        if s.solid(stem) or s.solid(ring) or s.solid(m(stem)) or s.solid(m(ring)):
                            continue
                        r_c = np.array(ring) + 0.5
                        h1 = s.blocked(casc, r_c, own, {stem, ring})
                        h2 = s.blocked(s.point(r, eye), r_c, own, {stem, ring})
                        h3 = s.blocked(mc(casc), mc(r_c), ownP, {m(stem), m(ring)})
                        if h1 or h2 or h3:
                            continue
                        done = (off, stem, ring)
                        break
                    if done is None and P['ring'].get('partition'):
                        # 牆上放不了（艙房隔牆擋在砲旁邊）⇒ 釘在那道隔牆朝砲的那一面（同憲法號階段二十二的第 2 門）
                        yw0 = min(w for w in (s.wall_y(c + d, z) for d in range(-10, 11)) if w is not None)   # 砲中線那一欄是砲門開口（沒牆）⇒ 取附近的牆
                        for ddx in range(7, 13):
                            x_wall = c + sg * ddx
                            for y in range(yw0 - 3, yw0 - 15, -1):
                                if s.solid((x_wall, y, z)) and not s.solid((x_wall - sg, y, z)):
                                    ring = (x_wall - sg, y, z)
                                    if ring in own or s.solid(m(ring)):
                                        continue
                                    r_c = np.array(ring) + 0.5
                                    if s.blocked(casc, r_c, own, {ring}) or s.blocked(s.point(r, eye), r_c, own, {ring}) or s.blocked(mc(casc), mc(r_c), ownP, {m(ring)}):
                                        continue
                                    done = ('partition', ring, ring)
                                    break
                            if done:
                                break
                        if done:
                            s.notes.append('%s 的 %s 環釘在艙房隔牆上（%s）' % (r['name'], side, list(done[2])))
                    if done is None:
                        s.notes.append('%s 的 %s 環找不到不穿牆的位置 ⇒ 不放、那一側的 breeching 與 tackle 不掛' % (r['name'], side))
                        continue
                    off, stem, ring = done
                    if stem != ring:
                        s.put(stem, col['iron'], 'ring')
                    s.put(ring, col['iron'], 'ring')
                    row['rings'][side] = {'offset': off, 'cell': list(ring), 'name': 'ring-%02d-%s' % (r['port'], side)}
                tr = s.point(r, 'train')
                for back in [P['deck_ring']['back']] + [b for b in range(6, 15) if b != P['deck_ring']['back']]:
                    k = (int(math.floor(tr[0])), int(math.floor(tr[1] - back)), zd)
                    if s.solid(k) or not s.solid((k[0], k[1], zd - 1)) or s.solid(m(k)):
                        continue
                    if s.blocked(tr, np.array(k) + 0.5, own, {k}):
                        continue
                    s.put(k, col['iron'], 'deck_ring')
                    row['deck_ring'] = {'back': back, 'cell': list(k), 'name': 'deck-%02d' % r['port']}
                    break
                if row['deck_ring'] is None:
                    s.notes.append('%s 的甲板環找不到位置 ⇒ train tackle 不掛' % r['name'])
                out.append(row)
            # garlands
            G = P['garland']
            gl = []
            for a, b in zip(out, out[1:]):
                if b['port'] != a['port'] + 1:
                    continue
                lo, hi = a['c'] + G['clear'], b['c'] - G['clear']
                L = min(G['max_len'], hi - lo + 1)
                if L < 6:
                    continue
                x0 = (lo + hi) // 2 - L // 2
                zd = min(a['deck_z'], b['deck_z'])
                zg = zd + G['z_above_deck']
                cells = []
                ok = True
                for x in range(x0, x0 + L):
                    yw = s.wall_y(x, zg)
                    if yw is None or not s.solid((x, yw - 3, zg - G['z_above_deck'] - 1)):
                        ok = False
                        break
                    cells += [((x, yw - 1, zg), col['garland'], 'garland'), ((x, yw - 2, zg), col['garland'], 'garland')]
                    if (x - x0) % G['shot_step'] == 1:
                        cells.append(((x, yw - 2, zg + 1), col['shot'], 'shot'))
                if not ok or any(s.solid(k) or s.solid(m(k)) or k in s.cells for k, _, _ in cells):
                    s.notes.append('%s 第 %d–%d 門之間的 garland 放不下 ⇒ 不放' % (deck, a['port'], b['port']))
                    continue
                for k, cc, kd in cells:
                    s.put(k, cc, kd)
                gl.append({'between': [a['port'], b['port']], 'x': [x0, x0 + L - 1], 'z': zg})
            # rammer／sponge
            I = P['implements']
            imps = []
            for row in out:
                c, zd = row['c'], row['deck_z']
                used = []
                for kind_, head_c in (('rammer', col['rammer_head']), ('sponge', col['sponge_head'])):
                    cands = []
                    for dx, length in [(d, L_) for L_ in I['lengths'] for d in I['dx_try']]:
                        x = c + dx
                        if any(abs(x - u) < 2 for u in used):
                            continue
                        zt = zd + I['ceiling_from']
                        yw = s.wall_y(x, zt)
                        if yw is None:
                            continue
                        y1 = yw - I['clear_wall']
                        ys = list(range(y1 - length + 1, y1 + 1))
                        zc = set()
                        for y in ys:
                            col_ = np.where(s.W[x, y, zt:zd + 30] > 0)[0]
                            zc.add(zt + int(col_.min()) if len(col_) else None)
                        if len(zc) != 1 or None in zc:
                            continue
                        z = zc.pop() - 1
                        cl = [((x, y, z), head_c if y >= y1 - 1 else (col['iron'] if (y1 - y) in I['bands'] else col['staff']), kind_) for y in ys]
                        cl += [((x, y, z - 1), head_c, kind_) for y in (y1 - 1, y1)]
                        if any(s.solid(k) or s.solid(m(k)) or k in s.cells for k, _, _ in cl):
                            continue
                        cands.append((-length, z, abs(dx), dx, x, ys, z, cl))
                    if cands:
                        _, _, _, dx, x, ys, z, cl = min(cands, key=lambda t: t[:4])
                        for k, cc, kd in cl:
                            s.put(k, cc, kd)
                        imps.append({'gun': row['name'], 'kind': kind_, 'x': x, 'y': [ys[0], ys[-1]], 'z': z})
                        used.append(x)
                    else:
                        s.notes.append('%s 上方放不下 %s ⇒ 不放' % (row['name'], kind_))
            # 繩
            R = P['ropes']
            dl = s.GB['deck_links'][deck]
            for row in out:
                for sd in ('S', 'P'):
                    gname = row['name'] if sd == 'S' else row['name'].replace('-S', '-P')
                    gp = 'model:%s/%s' % (dl, gname)
                    fl = '%s/%s' % (dl, dk['link'] if sd == 'S' else dk['mirror_link'])
                    for side in ('aft', 'fwd'):
                        if side not in row['rings']:
                            continue
                        ring = '%s/%s' % (fl, row['rings'][side]['name'])
                        s.ropes.append(dict(name='%s.breeching-%s' % (gname, side), **{'from': gp + '/cascabel', 'to': ring}, **R['breeching'], group='guns/breeching'))
                        s.ropes.append(dict(name='%s.tackle-%s' % (gname, side), **{'from': '%s/eye-%s' % (gp, side), 'to': ring}, **R['tackle'], group='guns/tackle'))
                    if row['deck_ring']:
                        s.ropes.append(dict(name='%s.train' % gname, **{'from': gp + '/train', 'to': '%s/%s' % (fl, row['deck_ring']['name'])}, **R['train'], group='guns/train'))
            s.by_deck[deck] = {'rows': out, 'garlands': gl, 'implements': imps}

    def verify_write(s):
        m = lambda p: (p[0], 2 * YC - p[1], p[2])
        v = {'read': {'assembly_voxels': s.P['assembly_voxels'], 'hidden': s.hidden}, 'decks': {}, 'notes': s.notes}
        out = os.path.join(D, 'masks', 'gunfittings')
        os.makedirs(out, exist_ok=True)
        pts = []
        total = 0
        for dk in s.P['decks']:
            deck = dk['deck']
            bx = dk['box']
            x0, y0, z0 = bx['at']
            mine = {k: c for k, c in s.cells.items() if all(bx['at'][a] <= k[a] < bx['at'][a] + bx['size'][a] for a in range(3))}
            B = s.by_deck[deck]
            # 每一格屬於哪一層：照 z 在框裡；框彼此不重疊（斷言）
            rows = sorted((x - x0, y - y0, z - z0, c) for (x, y, z), c in mine.items())
            p = os.path.join(out, deck + '.vox.txt')
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s 砲具一舷（y > 160；自己的座標，at=%d,%d,%d；另一舷 mirror=y、at.y ＝ %d）（%d 格）\n' % (
                deck, deck, x0, y0, z0, 321 - y0 - bx['size'][1], len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            total += len(mine)
            for row in B['rows']:
                for side, rg in row['rings'].items():
                    pts.append({'work': dk['id'], 'name': rg['name'], 'world': rg['cell'], 'local': [rg['cell'][0] - x0, rg['cell'][1] - y0, rg['cell'][2] - z0]})
                if row['deck_ring']:
                    c = row['deck_ring']['cell']
                    pts.append({'work': dk['id'], 'name': row['deck_ring']['name'], 'world': c, 'local': [c[0] - x0, c[1] - y0, c[2] - z0]})
            v['decks'][deck] = {'cells': len(mine), 'by_kind': dict(collections.Counter(s.kind[k] for k in mine)),
                                'rings': sum(len(r['rings']) for r in B['rows']), 'deck_rings': sum(1 for r in B['rows'] if r['deck_ring']),
                                'garlands': len(B['garlands']), 'implements': len(B['implements']),
                                'ring_offsets': dict(collections.Counter(rg['offset'] for r in B['rows'] for rg in r['rings'].values())),
                                'file': {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}
        assert total == len(s.cells), ('有格不在任何一層的框裡', len(s.cells) - total)
        mir = {m(k) for k in s.cells}
        v['overlap_world'] = sum(1 for k in s.cells if s.W[k] > 0)
        v['mirror_overlap_world'] = sum(1 for k in mir if s.W[k] > 0)
        v['mirror_overlap_self'] = sum(1 for k in mir if k in s.cells)
        # 浮空：放進組裝件（不含砲模型）看是不是接到既有的格
        A = np.zeros(s.W.shape, bool)
        A[:] = s.H
        base = s.W.copy()
        for name, cs in s.gun_cells.items():
            for c in cs:
                if 0 <= c[2] < ZMAX and base[c] == 1:
                    base[c] = 0
        A = base > 0
        for k in list(s.cells) + list(mir):
            A[k] = True
        lab, n = ndimage.label(A[100:800])
        keep = set(np.unique(lab[(base > 0)[100:800]])) - {0}
        fl = [k for k in list(s.cells) + list(mir) if lab[k[0] - 100, k[1], k[2]] not in keep]
        v['floating'] = {'n': len(fl), 'first': [list(k) for k in fl[:6]]}
        v['ropes'] = dict(collections.Counter(r['group'] for r in s.ropes))
        v['ropes_total'] = len(s.ropes)
        v['expect_assembly_after'] = s.P['assembly_voxels'] + 2 * len(s.cells)
        json.dump({'note': '砲具固定點（S 舷那一件；P 舷走鏡像關聯同名）', 'points': pts}, open(os.path.join(D, 'gunfittings_points.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        json.dump({'note': '下層／上層長砲的 breeching、side tackle、train tackle（掛在組裝件）', 'ropes': s.ropes}, open(os.path.join(D, 'gun_ropes.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        json.dump(v, open(os.path.join(D, 'verify_gunfittings.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        return v


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    F = Fit()
    F.build()
    v = F.verify_write()
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
