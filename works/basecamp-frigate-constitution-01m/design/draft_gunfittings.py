# 新圖紙 19（gun deck 砲具）：plan.json 的 gunfittings 段 ＋ guns 段 ＋ guns_placement.json ＋ 組裝件的現況（砲具加進來之前）
#   ⇒ masks/gunfittings/side.vox.txt（一舷，自己的座標）、design/rig_points_gunfittings.json、design/gun_ropes.json（每門 5 條繩）、
#      verify_gunfittings.json、sheet19_gunfittings_v1.png
# 用法：python -I draft_gunfittings.py <design 資料夾>
#   · 船牆上的環：砲門中線往船尾／船頭 offset 格、甲板面 ＋8；碰到東西、或繩（砲尾 → 環、cheek → 環）會穿過別的實心 ⇒ 換下一個 offset
#     （穿過自己這門砲的砲架不算：實船的 breeching 本來就穿過 cheek 上的孔）
#   · 甲板上的環：砲架尾往船裡 back 格；train tackle 穿過別的實心 ⇒ 往前後找
#   · shot garland：兩門有砲的砲門之間、靠牆、甲板面 ＋2
import sys, os, json, hashlib, subprocess
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402
from draft_guns import existing_links           # noqa: E402

YC = 160
ZMAX = 200


class Fittings:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['gunfittings']
        s.GP = s.plan['guns']
        B = s.P['base']
        have = set(existing_links(ASSEMBLY))
        s.hidden = [h for h in B['hide_links'] if h in have]
        a = export_list(ASSEMBLY, draft=False, hide_links=','.join(s.hidden) if s.hidden else None)
        assert len(a) == B['assembly_voxels'], ('讀到的現況格數對不上', len(a), B['assembly_voxels'])
        m = a[a[:, 2] < ZMAX]
        s.W = np.zeros((1024, 320, ZMAX), np.uint8)
        s.W[m[:, 0], m[:, 1], m[:, 2]] = m[:, 3]
        s.place = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))
        g = [l.split(',') for l in open(os.path.join(design, 'masks', 'guns', 'gun24.vox.txt'), encoding='utf-8') if not l.startswith('#')]
        s.gun = np.array([[int(v) for v in r[:3]] for r in g], np.int32)
        s.pts = {k: np.array(v) for k, v in s.place['points_local'].items()}
        s.cells, s.kind = {}, {}
        s.anchors, s.ropes, s.notes = [], [], []

    def solid(s, k):
        return s.W[k] > 0

    def gun_cells(s, at, mirror):
        p = s.gun.copy()
        if mirror:
            p[:, 1] = s.GP['gun']['size'][1] - 1 - p[:, 1]
        return {tuple(q) for q in (p + np.array(at))}

    def blocked(s, a, b, own, extra=()):
        """a、b 是連續座標（格心 ＋0.5）；線段經過的格是不是有別的實心（own、extra 不算）。"""
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

    def deck(s, x):
        for a, b, z in s.GP['deck_z']['segments']:
            if (a is None or x >= a) and (b is None or x < b):
                return z
        raise ValueError(x)

    def wall_y(s, x, z):
        col = np.where(s.W[x, 185:320, z] > 0)[0]
        return 185 + int(col.min()) if len(col) else None

    def build(s):
        P, col = s.P, s.P['colors']
        X = s.GP['gun']['axis_x']
        guns = [l for l in s.place['links'] if not l['mirror']]
        s.rows = []
        sg_pairs = []
        for lk in guns:
            n = int(lk['name'][-2:])
            at = np.array(lk['at'])
            c, zd = int(at[0] + X), int(at[2])
            own = s.gun_cells(lk['at'], False)
            casc = s.pts['cascabel'] + at + 0.5
            row = {'n': n, 'c': c, 'deck': zd, 'rings': {}, 'deck_ring': None}
            # ── 船牆上的兩個環 ──
            for side, sg, eye in (('aft', -1, 'eye-aft'), ('fwd', 1, 'eye-fwd')):
                z = zd + P['ring']['z_above_deck']
                done = None
                for off in P['ring']['offset']:
                    x = c + sg * off
                    yw = s.wall_y(x, z)
                    if yw is None:
                        continue
                    stem, ring = (x, yw - 1, z), (x, yw - 2, z)
                    if s.solid(stem) or s.solid(ring) or stem in own or ring in own:
                        continue
                    r_c = np.array(ring) + 0.5
                    h1 = s.blocked(casc, r_c, own, {stem, ring})
                    h2 = s.blocked(s.pts[eye] + at + 0.5, r_c, own, {stem, ring})
                    # 另一舷（mirror）同樣量一次
                    m = lambda p: (p[0], 2 * YC - p[1], p[2])
                    ownP = {m(q) for q in own}
                    mc = lambda v: np.array([v[0], 2 * YC + 1 - v[1], v[2]])     # 連續座標鏡過去（格 y ↔ 320 − y）
                    h3 = s.blocked(mc(casc), mc(r_c), ownP, {m(stem), m(ring)})
                    if s.solid(m(stem)) or s.solid(m(ring)) or h1 or h2 or h3:
                        continue
                    done = (off, stem, ring)
                    break
                if done is None and P['ring'].get('partition'):
                    # 牆上放不了（艙房隔牆擋在砲旁邊）⇒ 找砲旁邊那道隔牆，釘在朝砲的那一面（第 2 門，艦長室側艙）
                    yw0 = s.wall_y(c, z)
                    for ddx in range(7, 12):
                        x_wall = c + sg * ddx
                        for y in range(yw0 - 3, yw0 - 15, -1):
                            if s.solid((x_wall, y, z)) and not s.solid((x_wall - sg, y, z)):
                                ring = (x_wall - sg, y, z)
                                if ring in own:
                                    continue
                                m = lambda p: (p[0], 2 * YC - p[1], p[2])
                                r_c = np.array(ring) + 0.5
                                mc = lambda v: np.array([v[0], 2 * YC + 1 - v[1], v[2]])
                                if s.solid(m(ring)) or s.blocked(casc, r_c, own, {ring}) or s.blocked(s.pts[eye] + at + 0.5, r_c, own, {ring})                                         or s.blocked(mc(casc), mc(r_c), {m(q) for q in own}, {m(ring)}):
                                    continue
                                done = ('partition', ring, ring)
                                break
                        if done:
                            break
                    if done:
                        s.notes.append('砲門 %d 的 %s 環釘在艙房隔牆上（%s）' % (n, side, list(done[2])))
                if done is None:
                    s.notes.append('砲門 %d 的 %s 環找不到不穿牆的位置（offset %s）⇒ 不放、那一側的 breeching 與 tackle 不掛' % (n, side, P['ring']['offset']))
                    continue
                off, stem, ring = done
                s.put(stem, col['iron'], 'ring')
                s.put(ring, col['iron'], 'ring')
                nm = 'ring-%02d-%s' % (n, side)
                s.anchors.append({'name': nm, 'kind': 'ring', 'world': list(ring), 'gun': n, 'side': side})
                row['rings'][side] = {'offset': off, 'cell': list(ring)}
            # ── 甲板上的環（train tackle）──
            tr = s.pts['train'] + at + 0.5
            for back in [P['deck_ring']['back']] + [b for b in range(6, 14) if b != P['deck_ring']['back']]:
                k = (c, int(at[1] + s.pts['train'][1] - back), zd)
                m = (k[0], 2 * YC - k[1], k[2])
                if s.solid(k) or not s.solid((k[0], k[1], zd - 1)) or s.solid(m):
                    continue
                if s.blocked(tr, np.array(k) + 0.5, own, {k}):
                    continue
                s.put(k, col['iron'], 'deck_ring')
                s.anchors.append({'name': 'deck-%02d' % n, 'kind': 'deck_ring', 'world': list(k), 'gun': n})
                row['deck_ring'] = {'back': back, 'cell': list(k)}
                break
            if row['deck_ring'] is None:
                s.notes.append('砲門 %d 的甲板環找不到位置 ⇒ train tackle 不掛' % n)
            s.rows.append(row)
            sg_pairs.append((n, c, zd))
        # ── shot garlands：相鄰兩門有砲的砲門之間 ──
        G = P['garland']
        s.garlands = []
        for (n1, c1, z1), (n2, c2, z2) in zip(sg_pairs, sg_pairs[1:]):
            if n2 != n1 + 1:
                continue
            lo, hi = c1 + G['clear'], c2 - G['clear']
            L = min(G['max_len'], hi - lo + 1)
            if L < 6:
                continue
            x0 = (lo + hi) // 2 - L // 2
            # 跨過甲板高低差（570 那一道）的空檔：只放在中心所在的那一段甲板上（v1 取兩門砲裡低的甲板 ⇒ 在高的那段插進甲板板）
            zd = s.deck((lo + hi) // 2)
            xs = [x for x in range(x0, x0 + L) if s.deck(x) == zd]
            if len(xs) < 6:
                continue
            x0, L = xs[0], len(xs)
            zg = zd + G['z_above_deck']
            plan_cells = []
            ok = True
            for x in xs:
                yw = s.wall_y(x, zg)
                if yw is None:
                    ok = False
                    break
                plan_cells += [((x, yw - 1, zg), col['garland'], 'garland'), ((x, yw - 2, zg), col['garland'], 'garland')]
                if (x - x0) % G['shot_step'] == 1:
                    plan_cells.append(((x, yw - 2, zg + 1), col['shot'], 'shot'))
            m = lambda p: (p[0], 2 * YC - p[1], p[2])
            if not ok or any(s.solid(k) or s.solid(m(k)) or k in s.cells for k, _, _ in plan_cells):
                s.notes.append('砲門 %d–%d 之間的 garland 放不下（撞到現況或牆找不到）⇒ 不放' % (n1, n2))
                continue
            for k, cc, kd in plan_cells:
                s.put(k, cc, kd)
            s.garlands.append({'between': [n1, n2], 'x': [x0, x0 + L - 1], 'z': zg, 'shot': sum(1 for _, _, kd in plan_cells if kd == 'shot')})
        # ── rammer／sponge：每門砲正上方、天花板（上一層甲板板或橫樑）底下各一根，平行砲身 ──
        I = P.get('implements')
        s.implements = []
        if I:
            for row in s.rows:
                n, c, zd = row['n'], row['c'], row['deck']
                used = []
                for kind_, head_c in (('rammer', col['rammer_head']), ('sponge', col['sponge_head'])):
                    placed = None
                    cands = []
                    for dx, length in [(d, L_) for L_ in I['lengths'] for d in I['dx_try']]:
                        x = c + dx
                        if any(abs(x - u) < 2 for u in used):
                            continue
                        zt = zd + I['ceiling_from']                 # 砲門上緣之上（v1 取 ＋12 ＝ 砲門的高度 ⇒ 把砲管當成牆）
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
                        cells = [((x, y, z), head_c if y >= y1 - 1 else (col['iron'] if (y1 - y) in I['bands'] else col['staff']), kind_) for y in ys]
                        cells += [((x, y, z - 1), head_c, kind_) for y in (y1 - 1, y1)]
                        m = lambda p: (p[0], 2 * YC - p[1], p[2])
                        if any(s.solid(k) or s.solid(m(k)) or k in s.cells for k, _, _ in cells):
                            continue
                        cands.append((-length, z, abs(dx), dx, x, ys, z, cells))
                    if cands:
                        # 長的優先、掛在橫樑底下（天花板最低）優先，再來離砲中線近
                        # （v2 優先兩根橫樑之間 ⇒ 貼著甲板板、被 3 格深的橫樑擋住，從艙裡幾乎看不到）
                        _, _, _, dx, x, ys, z, cells = min(cands, key=lambda t: t[:4])
                        for k, cc, kd in cells:
                            s.put(k, cc, kd)
                        placed = {'kind': kind_, 'x': x, 'y': [ys[0], ys[-1]], 'z': z}
                        used.append(x)
                    if placed:
                        s.implements.append(dict(placed, gun=n))
                    else:
                        s.notes.append('砲門 %d 上方放不下 %s（天花板不平或撞到東西）⇒ 不放' % (n, kind_))
        # ── 繩 ──
        R = P['ropes']
        for row in s.rows:
            n = row['n']
            for sd, gl, fl in (('S', '甲板-gun/砲-S%02d' % n, '甲板-gun/' + P['subwork']['link']),
                               ('P', '甲板-gun/砲-P%02d' % n, '甲板-gun/' + P['subwork']['mirror_link'])):
                for side in ('aft', 'fwd'):
                    if side not in row['rings']:
                        continue
                    ring = '%s/ring-%02d-%s' % (fl, n, side)
                    s.ropes.append(dict(name='砲-%s%02d.breeching-%s' % (sd, n, side), **{'from': gl + '/cascabel', 'to': ring}, **R['breeching'], group='breeching'))
                    s.ropes.append(dict(name='砲-%s%02d.tackle-%s' % (sd, n, side), **{'from': '%s/eye-%s' % (gl, side), 'to': ring}, **R['tackle'], group='tackle'))
                if row['deck_ring']:
                    s.ropes.append(dict(name='砲-%s%02d.train' % (sd, n), **{'from': gl + '/train', 'to': '%s/deck-%02d' % (fl, n)}, **R['train'], group='train'))

    def verify(s):
        bx = s.P['subwork']['box']
        v = {'cells': len(s.cells), 'by_kind': {}}
        for k, kd in s.kind.items():
            v['by_kind'][kd] = v['by_kind'].get(kd, 0) + 1
        mir = {(x, 2 * YC - y, z): c for (x, y, z), c in s.cells.items()}
        v['overlap_world'] = sum(1 for k in s.cells if s.W[k] > 0)
        v['mirror_overlap_world'] = sum(1 for k in mir if s.W[k] > 0)
        v['mirror_overlap_self'] = sum(1 for k in mir if k in s.cells)
        out = [k for k in s.cells if not all(bx['at'][a] <= k[a] < bx['at'][a] + bx['size'][a] for a in range(3))]
        assert not out, ('有格在固定的框外', out[:5])
        xa, xb = bx['at'][0] - 2, bx['at'][0] + bx['size'][0] + 2
        A = s.W[xa:xb] > 0
        for k in list(s.cells) + list(mir):
            A[k[0] - xa, k[1], k[2]] = True
        lab, nn = ndimage.label(A)
        base = set(np.unique(lab[s.W[xa:xb] > 0])) - {0}
        fl = [k for k in list(s.cells) + list(mir) if lab[k[0] - xa, k[1], k[2]] not in base]
        v['floating'] = {'n': len(fl), 'first': [list(k) for k in fl[:6]]}
        v['rings'] = sum(len(r['rings']) for r in s.rows)
        v['deck_rings'] = sum(1 for r in s.rows if r['deck_ring'])
        v['garlands'] = s.garlands
        v['implements'] = getattr(s, 'implements', [])
        v['ropes'] = {g: sum(1 for r in s.ropes if r['group'] == g) for g in ('breeching', 'tackle', 'train')}
        v['ropes_total'] = len(s.ropes)
        v['anchors_S'] = len(s.anchors)
        v['guns'] = s.rows
        v['notes'] = s.notes
        v['expect_assembly_after'] = s.P['base']['assembly_voxels'] + 2 * len(s.cells)
        v['hidden_for_base'] = s.hidden
        s.v = v
        return v

    def write(s):
        bx = s.P['subwork']['box']
        x0, y0, z0 = bx['at']
        out = os.path.join(s.design, 'masks', 'gunfittings')
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, 'side.vox.txt')
        rows = sorted((x - x0, y - y0, z - z0, c) for (x, y, z), c in s.cells.items())
        open(p, 'w', encoding='utf-8', newline='\n').write(
            '# side —— gun deck 砲具一舷（y > 160；自己的座標，at=%d,%d,%d；另一舷 mirror=y、at.y ＝ %d）（%d 格）\n' % (x0, y0, z0, 321 - y0 - bx['size'][1], len(rows))
            + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        pts = [dict(a, owner=s.P['subwork']['id'], side='S') for a in s.anchors]
        pts += [dict(a, owner=s.P['subwork']['id'], side='P', world=[a['world'][0], 2 * YC - a['world'][1], a['world'][2]], via=s.P['subwork']['mirror_link']) for a in s.anchors]
        rp = os.path.join(s.design, 'rig_points_gunfittings.json')
        json.dump({'note': 'gun deck 砲具的固定點（船牆上的環 ring-NN-aft／fwd、甲板上的環 deck-NN）；S ＝ y > 160，P 是 via 那條鏡像關聯（同名）；世界座標', 'points': pts},
                  open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        gp = os.path.join(s.design, 'gun_ropes.json')
        json.dump({'note': '每門砲的 breeching、side tackles、train tackle（掛在組裝件；端點是關聯路徑）', 'ropes': s.ropes},
                  open(gp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        s.files = {k: {'sha256': hashlib.sha256(open(f, 'rb').read()).hexdigest()} for k, f in (('side', p), ('rig_points', rp), ('ropes', gp))}
        s.files['side']['cells'] = len(rows)


def render_sheet(F, path):
    f12, f18 = DD._font(13), DD._font(20)
    xa, xb, ya, yb = 172, 640, 176, 232
    sc = 3
    W = F.W
    img = np.zeros((yb - ya, xb - xa, 3), np.uint8)
    img[:] = DD.PAPER
    zc = 100
    for ix, x in enumerate(range(xa, xb)):
        for iy, y in enumerate(range(yb - 1, ya - 1, -1)):
            best = None
            for z in range(zc, 78, -1):
                c = F.cells.get((x, y, z))
                if c is not None:
                    best = (c, True)
                    break
                if W[x, y, z] > 0:
                    best = (int(W[x, y, z]), False)
                    break
            if best:
                rgb = np.array(DP.rgb332(best[0]))
                img[iy, ix] = rgb if best[1] else (rgb * 0.5 + np.array(DD.PAPER) * 0.5).astype(np.uint8)
    top = Image.fromarray(img).resize(((xb - xa) * sc, (yb - ya) * sc), Image.NEAREST)
    dr0 = ImageDraw.Draw(top)
    for r in F.ropes:                                       # 繩：S 舷的投影線
        if '-S' not in r['name']:
            continue
        def wpt(path):
            parts = path.split('/')
            if parts[1].startswith('砲-'):
                lk = next(l for l in F.place['links'] if l['name'] == parts[1])
                return np.array(F.place['points_local'][parts[2]]) + np.array(lk['at']) + 0.5
            a = next(a for a in F.anchors if a['name'] == parts[2])
            return np.array(a['world']) + 0.5
        p, q = wpt(r['from']), wpt(r['to'])
        colr = {'breeching': (200, 160, 90), 'tackle': (120, 90, 50), 'train': (60, 120, 160)}[r['group']]
        dr0.line([((p[0] - xa) * sc, (yb - p[1]) * sc), ((q[0] - xa) * sc, (yb - q[1]) * sc)], fill=colr, width=2)
    PADL = 40
    can = Image.new('RGB', (PADL + top.size[0] + 40, 80 + top.size[1] + 160), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), F.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '俯視 S 舷 gun deck（z %d 以下；現況淡色、砲具原色；x %d–%d、y %d–%d，每格 %d px）；線：breeching 淡黃、side tackle 褐、train tackle 藍' % (zc, xa, xb - 1, ya, yb - 1, sc), font=f12, fill=DD.INK)
    can.paste(top, (PADL, 66))
    v = F.v
    y = 66 + top.size[1] + 14
    lines = ['一舷 %d 格（%s）；船牆環 %d、甲板環 %d、garland %d 條（砲彈 %d 顆）；跟現況重疊 %d、鏡像重疊 %d/%d、浮空 %d；組裝件預期 %d' % (
                 v['cells'], '、'.join('%s %d' % kv for kv in sorted(v['by_kind'].items())), v['rings'], v['deck_rings'], len(v['garlands']), sum(g['shot'] for g in v['garlands']),
                 v['overlap_world'], v['mirror_overlap_world'], v['mirror_overlap_self'], v['floating']['n'], v['expect_assembly_after']),
             '繩（兩舷）%d：breeching %d、tackle %d、train %d' % (v['ropes_total'], v['ropes']['breeching'], v['ropes']['tackle'], v['ropes']['train'])]
    lines += ['注意：' + t.replace('⇒', '→') for t in v['notes']]
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, can.size[0], y + 12))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    F = Fittings(design)
    F.build()
    v = F.verify()
    F.write()
    v['files'] = F.files
    json.dump(v, open(os.path.join(design, 'verify_gunfittings.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(F, os.path.join(design, 'sheet19_gunfittings_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('guns', 'garlands')}, ensure_ascii=False))
    for r in v['guns']:
        print(r['n'], {k: r['rings'][k]['offset'] for k in r['rings']}, r['deck_ring']['back'] if r['deck_ring'] else None)


if __name__ == '__main__':
    main()
