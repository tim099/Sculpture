# 利劍號 新圖紙 07（TASK-0022 步驟 9）：砲 ⇒ guns_placement.json、verify_guns.json、sheet07_guns_v1.png、masks/guns/posts.vox.txt
#   出處：星辰號 claude-baghlah-01m/design/draft_guns.py（Gun 類、從船殼外沿砲軸往裡退到零碰撞、後座、射線、離繩）＋
#         蠍子號 claude-galiot-01m/design/draft_guns.py（迴旋砲插在甲板上的砲柱頂、遊戲砲手站位、走路格）。
#   改的地方：
#     · 舷側 6l 照星辰號；船首 12l、後甲板 3l 沒有砲門 ⇒「從舷牆頂上打」：每個種子 x 照角度（往船頭偏幾度）從船殼外往裡退，
#       要求砲口那一柱從甲板到砲口都沒有實心＋射線不碰船；v3 再加：砲口在那一欄船殼最外一面的外面（muzzle_beyond_hull_min）、
#       砲架最底那一層每一格離站人的格子最多 gap_max_cells 格（verifier9 F1／F2）。
#     · 砲手站位照 Blockside origin/dev efdcdc3 的 40_crew.js makeCrew 重寫（全部的砲，不只迴旋砲）：外框取 floor、照砲軸偏正橫或偏前後挑 8 個點、
#       z 在 [底 −8, 底 ＋3]、頭上 14 格、不在任何砲的外框（外擴 1 格、z 在 [底 −3, 頂]）裡、往外一圈一圈找 ≤ 4、站不到開得動的人數再放寬到 30。
#     · 走路格（遊戲 navBuild 的簡化：每層甲板 meta 的 floor、每 2 格一點、頭上 12 格、相鄰高差 ≤ 3、8 鄰）：砲擺上去前後、砲手站位在不在主群。
#   用法：python -I -X utf8 draft_guns.py [--probe=push=<砲名>:<格>] [--probe=scale=<種>:<scale>] [--probe=bow_x=<x,x>] [--probe=bow_angles=<θ,…>] [--probe=quarter_x=<x,…>] [--probe=swivel_rows=<deck:x:inset:post_h;…>]
#     反向對照不寫檔：把一門砲往外推（要撞）；換 scale；換種子 x（印完整讀數）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
V = HL.V
NAV_C, NAV_HEAD, NAV_DZ = 2, 12, 3         # 遊戲 42_hands.js 走路格
CREW_HEAD = 14                            # 40_crew.js standNear(…, 14, …)


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def r3(v):
    return [round(float(c), 3) for c in v]


def inset_offsets(inset):
    a, b = inset, 1.0 - inset
    return np.array([[0.5, 0.5, 0.5]] + [[(a, b)[k & 1], (a, b)[(k >> 1) & 1], (a, b)[(k >> 2) & 1]] for k in range(8)])


class Gun:
    """模型擺法（CLI 外部模型）：p ＝ at ＋ Rz(phi)·M·(v − pivot)·scale，M ＝ mirror y（P 舷）。"""

    def __init__(s, key, t, inset):
        s.key, s.t = key, t
        s.scale = float(t['scale'])
        s.pivot = np.array(t['pivot'], float)
        G = os.path.join(HERE, 'masks', 'guns_src')
        ld = lambda w: np.loadtxt(os.path.join(G, w + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)[:, :3].astype(float)
        s.barrel = ld(t['work'])
        s.mount = ld(t['mount_work']) if t.get('mount_work') else np.zeros((0, 3))
        s.cells = np.concatenate([s.barrel, s.mount])
        A = json.load(open(os.path.join(HERE, '..', '..', t['work'], 'anchors.json'), encoding='utf-8'))
        A = A.get('anchors', A)
        s.anchors = {a['name']: np.array(a['at'], float) + 0.5 for a in A}
        off = inset_offsets(inset)
        s.samples = (s.cells[:, None, :] + off[None]).reshape(-1, 3)
        s.barrel_samples = (s.barrel[:, None, :] + off[None]).reshape(-1, 3)
        s.centers = s.cells + 0.5
        s.bottom = s.cells[s.cells[:, 2] == s.cells[:, 2].min()] + 0.5
        s.corners = (s.cells[:, None, :] + np.array([[a, b, c] for a in (0, 1) for b in (0, 1) for c in (0, 1)], float)[None]).reshape(-1, 3)
        s.barrel_len = float(np.linalg.norm(s.anchors['muzzle'] - s.anchors['breech']) * s.scale)

    def world(s, P, at, phi, mirror):
        q = (np.asarray(P, float) - s.pivot) * s.scale
        if mirror:
            q = q * np.array([1.0, -1.0, 1.0])
        c, sn = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        x = q[..., 0] * c - q[..., 1] * sn
        y = q[..., 0] * sn + q[..., 1] * c
        return np.stack([x + at[0], y + at[1], q[..., 2] + at[2]], -1)

    def axis(s, phi, mirror):
        a = s.world(s.anchors['breech'][None], (0, 0, 0), phi, mirror)[0]
        b = s.world(s.anchors['muzzle'][None], (0, 0, 0), phi, mirror)[0]
        return (b - a) / np.linalg.norm(b - a)

    def direction(s, phi, mirror):
        d = s.axis(phi, mirror)[:2]
        return d / np.linalg.norm(d)

    def bbox(s, at, phi, mirror):
        W = s.world(s.corners, at, phi, mirror)
        return W.min(0), W.max(0)


class Grid:
    def __init__(s, cells, shape):
        s.G = np.zeros(shape, bool)
        c = np.array(list(cells), int)
        s.G[c[:, 0], c[:, 1], c[:, 2]] = True

    def hit(s, P):
        i = np.floor(np.asarray(P, float)).astype(int)
        ok = np.all((i >= 0) & (i < np.array(s.G.shape)), -1)
        out = np.ones(i.shape[:-1], bool)                  # 框外算實心（不准出框）
        j = i[ok]
        out[ok] = s.G[j[:, 0], j[:, 1], j[:, 2]]
        return out

    def get(s, x, y, z):
        return 0 <= x < s.G.shape[0] and 0 <= y < s.G.shape[1] and 0 <= z < s.G.shape[2] and bool(s.G[x, y, z])


def seg_points_dist(a, b, P):
    d = b - a
    t = np.clip(((P - a) @ d) / max(d @ d, 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * d), axis=1)


def poly(s):
    return sorted((tuple(float(v) for v in p.split(':')) for p in s.split(',')), key=lambda a: a[0])


def polyZ(F, x):
    if x < F[0][0] - 0.5 or x > F[-1][0] + 0.5:
        return None
    for i in range(1, len(F)):
        if x <= F[i][0]:
            a, b = F[i - 1], F[i]
            t = 0 if b[0] == a[0] else (x - a[0]) / (b[0] - a[0])
            return int(math.floor(a[1] + (b[1] - a[1]) * t + 0.5))
    return int(F[-1][1])


def main():
    probe = dict(a[len('--probe='):].split('=', 1) for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    AX, AY, AZ = [int(v) for v in plan['space']['assembly']]
    GB = {k: V(v) for k, v in plan['guns_build'].items() if not k.endswith('src')}
    S = GB['search']
    if 'scale' in probe:
        k, v = probe['scale'].split(':')
        GB['types'][k]['scale'] = float(v)
    for key, pk in (('bow', 'bow_x'), ('quarter', 'quarter_x')):
        if pk in probe:
            GB['chase'][key]['x'] = [int(v) for v in probe[pk].split(',')]
        if pk.replace('_x', '_angles') in probe:
            GB['chase'][key]['angles'] = [int(v) for v in probe[pk.replace('_x', '_angles')].split(',')]

    # ── 步驟 9 以前的實心（設計清單）：船（遊戲站人用的格子）＋篷架、帆桁（只擋砲，不給人站）──
    hull = load('masks/hull/hull_01.vox.txt')
    hull.update(load('masks/step6/hull_paint.vox.txt'))
    decks = {k: load('masks/decks/%s.vox.txt' % k) for k in ('hold', 'main', 'quarter')}
    ship = set(hull)
    for d in decks.values():
        ship |= set(d)
    for f in ('ladders/main', 'ladders/quarter', 'deco/beak', 'deco/platform', 'deco/glass', 'masts/mizzen', 'masts/main', 'masts/fore'):
        ship |= set(load('masks/' + f + '.vox.txt'))
    awning = set(load('masks/deco/awning.vox.txt'))
    yardw = set()
    for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
        off = [int(round(p['at'][i] - p['pivot'][i])) for i in range(3)]
        yardw |= {(x + off[0], y + off[1], z + off[2]) for (x, y, z) in load('masks/yards/lateen-%s.vox.txt' % p['mast'])}
    # 迴旋砲的砲柱（插在甲板上；落在那一層甲板的子作品）
    SW = GB['swivels']
    if 'swivel_rows' in probe:                                          # 反向對照／試位置：deck:x:inset:post_h（post_h 寫 a ＝ 自動），分號隔
        SW['rows'] = [dict(zip(('deck', 'x', 'inset', 'post_h'), r.split(':')), arc_lim=SW.get('arc_lim', '-90,45')) for r in probe['swivel_rows'].split(';')]
    # 每一排：右舷舷牆內面（甲板面以上到舷牆頂、船殼最內那一格；砲門、圓孔那幾層沒有牆）往裡 inset 格；柱高讓砲軸（柱頂 ＋ 4.5 格）比舷牆頂高 2 格、最多 8 格（遊戲砲手站的高度 ≥ 柱頂 − 8）
    hull0 = load('masks/hull/hull_01.vox.txt')
    hull0.update(load('masks/step6/hull_paint.vox.txt'))
    for row in SW['rows']:
        x = int(row['x'])
        dtop0 = {}
        for (xx, y, z) in load('masks/decks/%s.vox.txt' % row['deck']):
            if xx == x:
                dtop0[y] = max(dtop0.get(y, -1), z + 1)
        zf = max(v for y, v in dtop0.items() if y > YC + 2)
        rail = max(z for (xx, y, z) in hull0 if xx == x and y > YC)
        ins = [y for (xx, y, z) in hull0 if xx == x and zf < z <= rail and y > YC]
        if not ins:
            raise SystemExit('✗ 迴旋砲 x %d：甲板面以上沒有右舷舷牆' % x)
        inner = min(ins)
        row['dy'] = inner - int(row['inset']) - YC
        row['z'] = dtop0.get(YC + row['dy'], zf)
        row['rail_z'] = rail
        if str(row['post_h']) == 'a':
            row['post_h'] = min(8, max(1, int(math.ceil(rail + 2 - 4.5 - row['z']))))
        row['x'] = x
    posts, posts_by_deck = {}, {}
    for row in SW['rows']:
        for side in (1, -1):
            y = YC + side * int(row['dy'])
            for z in range(int(row['z']), int(row['z']) + int(row['post_h'])):
                posts[(int(row['x']), y, z)] = SW['post_color']
                posts_by_deck.setdefault(row['deck'], {})[(int(row['x']), y, z)] = SW['post_color']
    solid_stand = ship | set(posts)                                     # 遊戲 navBase：船的格子（外部模型不算）
    solid_all = solid_stand | awning | yardw
    G = Grid(solid_all, (AX, AY, AZ))
    Gs = Grid(solid_stand, (AX, AY, AZ))
    guns = {k: Gun(k, t, S['inset']) for k, t in GB['types'].items()}
    deck_top = {k: {} for k in decks}
    for k, d in decks.items():
        for (x, y, z) in d:
            if z + 1 > deck_top[k].get((x, y), -1):
                deck_top[k][(x, y)] = z + 1

    hull_by_xz = {}
    for (x, y, z) in hull:
        lo, hi = hull_by_xz.get((x, z), (999, -1))
        hull_by_xz[(x, z)] = (min(lo, y), max(hi, y))

    def outer_y(x, z, side):
        lo, hi = hull_by_xz[(x, z)]
        return (hi + 1) if side > 0 else lo

    def dtop(dk, pts):
        zs = [deck_top[dk][p] for p in pts if p in deck_top[dk]]
        return max(zs) if zs else None

    def muzzle_column_clear(tip, zd):
        """砲口出了舷牆：砲口那一柱從甲板面到砲口上一格都沒有船的實心。"""
        x, y = int(math.floor(tip[0])), int(math.floor(tip[1]))
        return not any(G.get(x, y, z) for z in range(int(zd), int(math.floor(tip[2])) + 2))

    def ray(g, at, phi, mir, far=None, grid=None):
        mz = g.world(g.anchors['muzzle'][None], at, phi, mir)[0]
        d = g.axis(phi, mir)
        t = np.arange(0.5, (far or GB['ray_len']) + 1e-9, 0.25)
        Q = mz[None] + t[:, None] * d[None]
        inside = np.all((Q >= 0) & (Q < np.array((grid or G).G.shape)), -1)
        hit = (grid or G).hit(Q) & inside
        return round(float(t[hit.argmax()]), 2) if hit.any() else None

    def evaluate(g, at, phi, mir, zd):
        tip = g.world(g.anchors['muzzle'][None], at, phi, mir)[0]
        bot = g.world(g.bottom, at, phi, mir)
        below = bot.copy()
        below[:, 2] -= 1.0
        return tip, (not G.hit(tip[None])[0]), float(Gs.hit(below).mean()), muzzle_column_clear(tip, zd), ray(g, at, phi, mir)

    def gap_max(g, at, phi, mir):
        """v3（verifier9 F1）：砲架最底那一層每一格往下幾格才碰到船（站人的格子）；support 只看「有沒有一半貼地」，看不到一側懸空。"""
        gs = []
        for p in g.world(g.bottom, at, phi, mir):
            x, y, z = int(math.floor(p[0])), int(math.floor(p[1])), int(math.floor(p[2])) - 1
            k = 0
            while k < 8 and not Gs.get(x, y, z - k):
                k += 1
            gs.append(k)
        return max(gs)

    def beyond_hull(tip, zd, side):
        """v3（verifier9 F2）：砲口超出船殼外面幾格（Ship_Guns §4.2「砲口在船殼外」）：砲口那一欄 x、甲板面到砲口上一格之間船殼最外那一面；< 0 ＝ 砲口還在舷牆裡。"""
        x = int(math.floor(tip[0]))
        ys = [hull_by_xz[(x, z)] for z in range(int(zd), int(math.floor(tip[2])) + 2) if (x, z) in hull_by_xz]
        if not ys:
            return None
        return round(float(tip[1] - (max(h for _, h in ys) + 1)) if side > 0 else float(min(l for l, _ in ys) - tip[1]), 2)

    def place(g, base_xy, phi, mir, zd, chase=False):
        """從 base（舷外）沿砲軸往裡每 step 格退：每個 (dz, 側移) 取第一個零碰撞的位置，再看合不合格；取 (不合格, dz, 退多少, |側移|) 最小的。"""
        best = None
        d_out = g.direction(phi, mir)
        d_side = np.array([d_out[1], -d_out[0]])
        for dz in S['dz']:
            for off in S['dx']:
                for k in range(int(S['back_max'] / S['step']) + 1):
                    back = k * S['step']
                    b = np.array(base_xy, float) + d_side * off - d_out * back
                    at = (float(b[0]), float(b[1]), float(zd + dz))
                    if G.hit(g.world(g.samples, at, phi, mir)).any():
                        continue
                    tip, free, sup, out, rb = evaluate(g, at, phi, mir, zd)
                    gm = gap_max(g, at, phi, mir)
                    bh = beyond_hull(tip, zd, 1 if not mir else -1)
                    ok = bool(free and out and rb is None and sup >= GB['support_min'] and gm <= GB['gap_max_cells']
                              and (not chase or (bh is not None and bh >= GB['muzzle_beyond_hull_min'])))
                    cand = {'at': r3(at), 'phi': phi, 'back': back, 'off': off, 'dz': dz, 'muzzle': r3(tip), 'muzzle_free': free, 'muzzle_out': out,
                            'ray_blocked_at': rb, 'support': round(sup, 3), 'gap_max': gm, 'muzzle_beyond_hull': bh, 'ok': ok}
                    key = (not ok, dz, back, abs(off))
                    if best is None or key < best[0]:
                        best = (key, cand)
                    break
        return best[1] if best else None

    rows = []

    def commit(r):
        """擺好的砲當實心（後面的砲要避開它）。"""
        g = guns[r['type']]
        P = g.world(g.centers, r['at'], r['phi'], r['side'] == 'P')
        for c in set(map(tuple, np.floor(P).astype(int).tolist())):
            if all(0 <= c[i] < G.G.shape[i] for i in range(3)):
                G.G[c] = True

    # ── 舷側 6l（主甲板砲門）──
    BS = GB['broadside']
    VL = json.load(open(os.path.join(HERE, 'verify_lines.json'), encoding='utf-8'))
    gp = [p for p in VL['ports'] if p['kind'] == 'gun']
    for i, p in enumerate(gp, 1):
        g = guns[BS['type']]
        x0, x1 = p['x']
        z0, z1 = p['z']
        xc = (x0 + x1 + 1) / 2.0
        zm = (z0 + z1) // 2
        for side, nm in ((1, 'S'), (-1, 'P')):
            mir = side < 0
            outs = [outer_y(x, zm, side) for x in (x0 - 2, x1 + 2)]
            outer = max(outs) if side > 0 else min(outs)
            zd = dtop(BS['deck'], [(x, outer - side * d) for x in (x0, int(xc), x1) for d in (8, 14, 20, 26)])
            c = place(g, (xc, outer), 0.0, mir, zd)
            r = {'group': 'broadside', 'deck': BS['deck'], 'port': i, 'side': nm, 'type': BS['type'], 'swivel': False, 'deck_z': zd, 'outer': outer,
                 'opening': {'x': [x0, x1], 'z': [z0, z1]}, 'name': '砲%s-%s%02d' % (BS['prefix'], nm, i)}
            r.update(c or {'ok': False, 'at': None})
            if c:
                r['muzzle_beyond_outer'] = round((c['muzzle'][1] - outer) * side, 2)
            rows.append(r)
            if c:
                commit(r)
    # ── 船首 12l、後甲板 3l：從舷牆頂上打；角度從最偏船頭往回試 ──
    for key, CH in GB['chase'].items():
        g = guns[CH['type']]
        for i, x in enumerate(CH['x'], 1):
            for side, nm in ((1, 'S'), (-1, 'P')):
                mir = side < 0
                zs = sorted(z for (xx, z) in hull_by_xz if xx == x)
                zr = max(z for z in zs if (side > 0 and hull_by_xz[(x, z)][1] > YC) or (side < 0 and hull_by_xz[(x, z)][0] < YC))
                outer = outer_y(x, zr, side)
                zd = dtop(CH['deck'], [(x + dx, outer - side * d) for dx in (-3, 0, 3) for d in (6, 10, 14, 20)])
                tried, pick = [], None
                for th in CH['angles']:
                    phi = -side * th                        # S：rotate −θ ⇒ 砲口往 +x 偏；P（mirror y）：+θ
                    c = place(g, (x + 0.5, outer), float(phi), mir, zd, chase=True)
                    tried.append([th] + ([c['ok'], c['back'], c['muzzle_out'], c['ray_blocked_at'], c['support'], c['gap_max'], c['muzzle_beyond_hull']] if c else [None]))
                    if c and c['ok']:
                        pick = dict(c, angle_fwd=th)
                        break
                r = {'group': key, 'deck': CH['deck'], 'port': 'x%d' % x, 'side': nm, 'type': CH['type'], 'swivel': False, 'deck_z': zd, 'rail_z': zr,
                     'outer': outer, 'angles_tried': tried, 'name': '砲%s-%s%02d' % (CH['prefix'], nm, i)}
                r.update(pick or {'ok': False, 'at': None})
                rows.append(r)
                if pick:
                    commit(r)
    # ── 迴旋砲：砲柱頂（叉架插銷底 ＝ 柱頂面）；S rotate 0（砲口 +y）、P mirror y ──
    gsw = guns[SW['type']] if SW['rows'] else None
    for i, row in enumerate(SW['rows'], 1):
        for side, nm in ((1, 'S'), (-1, 'P')):
            mir = side < 0
            at = (row['x'] + 0.5, YC + side * int(row['dy']) + 0.5, float(int(row['z']) + int(row['post_h'])))
            hit = int(G.hit(gsw.world(gsw.samples, at, 0.0, mir)).sum())
            tip, free, sup, out, rb = evaluate(gsw, at, 0.0, mir, int(row['z']))
            rows.append({'group': 'swivel', 'deck': row['deck'], 'port': 'sw%d' % row['x'], 'side': nm, 'type': SW['type'], 'swivel': True, 'deck_z': int(row['z']),
                         'post_h': int(row['post_h']), 'arc_lim': row['arc_lim'], 'at': r3(at), 'phi': 0.0, 'back': 0, 'off': 0, 'dz': 0, 'muzzle': r3(tip),
                         'muzzle_free': free, 'muzzle_out': out, 'ray_blocked_at': rb, 'support': round(sup, 3), 'hit_samples': hit, 'ok': bool(hit == 0 and free and out),
                         'name': '迴旋砲-%s%02d' % (nm, i)})
    fail = [[r['name'], r.get('angles_tried')] for r in rows if r.get('at') is None]
    R = {'probe': probe or None, 'guns': len(rows), 'by_type': {}, 'placed_none': fail,
         'read': {'solid_stand_cells': len(solid_stand), 'awning_cells': len(awning), 'yard_cells': len(yardw), 'post_cells': len(posts),
                  'component_sha256': {f: hashlib.sha256(open(os.path.join(HERE, 'masks', 'guns_src', f), 'rb').read()).hexdigest()[:16]
                                       for f in sorted(os.listdir(os.path.join(HERE, 'masks', 'guns_src')))}}}
    for r in rows:
        R['by_type'][r['type']] = R['by_type'].get(r['type'], 0) + 1
    placed = [r for r in rows if r.get('at') is not None]
    R['not_ok'] = [[r['name'], r.get('muzzle_free'), r.get('muzzle_out'), r.get('ray_blocked_at'), r.get('support')] for r in placed if not r['ok']]

    def world_of(r, which='samples', phi=None, push=0.0, recoil=0.0):
        g = guns[r['type']]
        mir = r['side'] == 'P'
        ph = r['phi'] if phi is None else phi
        at = np.array(r['at'], float)
        if push:
            at[:2] += g.direction(ph, mir) * push
        if recoil:
            at -= g.axis(ph, mir) * recoil
        return g.world(getattr(g, which), at, ph, mir)

    G0 = Grid(solid_all, (AX, AY, AZ))                                  # 不含砲的實心（量撞擊用；砲對砲另外量）
    if probe.get('push'):
        nm, d = probe['push'].rsplit(':', 1)
        rep = {r['name']: int(G0.hit(world_of(r, push=float(d) if r['name'] == nm else 0.0)).sum()) for r in placed}
        print(json.dumps({'probe': probe, 'hit_samples_by_gun': {k: v for k, v in rep.items() if v}}, ensure_ascii=False))
        return
    R['hit_samples'] = {r['name']: int(G0.hit(world_of(r)).sum()) for r in placed if int(G0.hit(world_of(r)).sum())}
    # 砲對砲（格心落在同一格）
    occg, clash = {}, []
    for r in placed:
        for c in set(map(tuple, np.floor(world_of(r, 'centers')).astype(int).tolist())):
            if c in occg and occg[c] != r['name']:
                clash.append([r['name'], occg[c]])
                break
            occg[c] = r['name']
    R['gun_gun_clash'] = clash
    # 兩舷對稱：P 的 at.y ＝ 2·YC ＋ 1 − S 的 at.y、x／z 一樣、phi 相反
    by = {(r['group'], str(r['port']), r['side']): r for r in placed}
    R['asymmetric_pairs'] = [r['name'] for (gk, pt, sd), r in by.items() if sd == 'S' and (
        (gk, pt, 'P') not in by or abs(r['at'][0] - by[(gk, pt, 'P')]['at'][0]) > 1e-6 or abs(2 * YC + 1 - r['at'][1] - by[(gk, pt, 'P')]['at'][1]) > 1e-6
        or r['at'][2] != by[(gk, pt, 'P')]['at'][2] or r['phi'] != -by[(gk, pt, 'P')]['phi'])]
    # 舷側砲穿過砲門那一段：離窗台、上楣幾格
    gap = {}
    for r in placed:
        if r['group'] != 'broadside':
            continue
        P = world_of(r, 'barrel_samples')
        o, side = r['opening'], (1 if r['side'] == 'S' else -1)
        u = (P[:, 1] - r['outer']) * side
        inwall = P[(P[:, 0] >= o['x'][0]) & (P[:, 0] <= o['x'][1] + 1) & (u >= -4) & (u <= 0)]
        gap[r['name']] = [round(float(inwall[:, 2].min() - o['z'][0]), 2), round(float(o['z'][1] + 1 - inwall[:, 2].max()), 2)] if len(inwall) else None
    R['broadside_barrel_sill_lintel_gap_min'] = [min(v[0] for v in gap.values() if v), min(v[1] for v in gap.values() if v)] if any(gap.values()) else None
    R['broadside_barrel_not_in_port'] = [k for k, v in gap.items() if not v]
    # 後座（Ship_Guns §4.2 預設：砲管長 × 0.3、至少 4 格；整門退，迴旋砲只退砲身）
    RC = GB['recoil']
    rec = {}
    for r in placed:
        g = guns[r['type']]
        dist = max(RC['min'], g.barrel_len * RC['k'])
        r['recoil_cells'] = round(dist, 2)
        n = int(G0.hit(world_of(r, 'barrel_samples' if r['swivel'] else 'samples', recoil=dist)).sum())
        if n:
            rec[r['name']] = n
    R['recoil_hit_samples'] = rec
    # 迴旋砲：每 sweep 度轉一圈（-180..180），撞、射線、砲手腳下 ⇒ 取 0 往兩邊連續、在 arc_lim 裡的範圍
    # ── 遊戲砲手站位（40_crew.js makeCrew）──
    boxes = {}
    for r in placed:
        g = guns[r['type']]
        lo, hi = g.bbox(r['at'], r['phi'], r['side'] == 'P')
        boxes[r['name']] = (lo, hi)
        r['bbox'] = [r3(lo), r3(hi)]

    def blocked(x, y, z, skip=None):
        for nm, (lo, hi) in boxes.items():
            if math.floor(lo[0]) - 1 <= x <= math.ceil(hi[0]) + 1 and math.floor(lo[1]) - 1 <= y <= math.ceil(hi[1]) + 1 and lo[2] - 3 <= z <= hi[2]:
                return True
        return False

    def stand_z(x, y, z0, z1, head):
        for z in range(z1, z0 - 1, -1):
            if not Gs.get(x, y, z - 1) or Gs.get(x, y, z):
                continue
            if any(Gs.get(x, y, z + h) for h in range(1, head)):
                continue
            return z
        return -1

    def stand_near(x, y, z0, z1, taken, rmax=4):
        for rr in range(0, rmax + 1):
            for dy in range(-rr, rr + 1):
                for dx in range(-rr, rr + 1):
                    if max(abs(dx), abs(dy)) != rr or (x + dx, y + dy) in taken:
                        continue
                    z = stand_z(x + dx, y + dy, z0, z1, CREW_HEAD)
                    if z >= 0 and not blocked(x + dx, y + dy, z):
                        taken.add((x + dx, y + dy))
                        return [x + dx + 0.5, y + dy + 0.5, z]
        return None

    taken = set()
    crew = {}
    for r in placed:
        g = guns[r['type']]
        lo, hi = boxes[r['name']]
        b = [math.floor(v) for v in list(lo) + list(hi)]
        n, nmin = GB['types'][r['type']]['crew']
        z0, z1 = b[2] - 8, b[2] + 3
        ax = g.axis(r['phi'], r['side'] == 'P')
        cx = (b[0] + b[3]) // 2
        sg = -1 if r['side'] == 'P' else 1
        y0 = b[1] if sg > 0 else b[4]
        if abs(ax[0]) <= abs(ax[1]):
            spots = [[b[0] - 3, y0 + 10 * sg], [b[3] + 3, y0 + 10 * sg], [b[0] - 3, y0 + 4 * sg], [b[3] + 3, y0 + 4 * sg], [b[0] - 2, y0 - 3 * sg], [b[3] + 2, y0 - 3 * sg],
                     [cx, y0 - 6 * sg], [cx - 5, y0 - 10 * sg]]
        else:
            ex = 1 if ax[0] > 0 else -1
            x0 = b[0] if ex > 0 else b[3]
            cyg = (b[1] + b[4]) // 2
            spots = [[x0 + 10 * ex, b[1] - 3], [x0 + 10 * ex, b[4] + 3], [x0 + 4 * ex, b[1] - 3], [x0 + 4 * ex, b[4] + 3], [x0 - 3 * ex, b[1] - 2], [x0 - 3 * ex, b[4] + 2],
                     [x0 - 6 * ex, cyg], [x0 - 10 * ex, cyg - 5]]
        got = []
        for i in range(n):
            a = stand_near(spots[i][0], spots[i][1], z0, z1, taken)
            if a:
                got.append(a)
        wide = 0
        while len(got) < min(n, nmin):
            a = stand_near(cx, (b[1] + b[4]) // 2, z0, z1, taken, 30)
            if not a:
                break
            got.append(a)
            wide += 1
        crew[r['name']] = got
        r['crew'] = {'want': n, 'min': nmin, 'got': len(got), 'from_wide_search': wide, 'at': got}
    R['crew_short'] = {r['name']: [r['crew']['got'], r['crew']['want']] for r in placed if r['crew']['got'] < r['crew']['want']}
    R['crew_below_min'] = [r['name'] for r in placed if r['crew']['got'] < r['crew']['min']]
    R['crew_total'] = [sum(r['crew']['got'] for r in placed), sum(r['crew']['want'] for r in placed)]
    # 繩（步驟 8 的直線）
    RE = json.load(open(os.path.join(HERE, 'verify_rigging.json'), encoding='utf-8'))['rope_ends']
    RT = {r_['name']: r_['thickness'] for r_ in json.load(open(os.path.join(HERE, 'rig_plan.json'), encoding='utf-8'))['ropes']}
    ropes = [(nm, np.array(e['from'], float), np.array(e['to'], float), RT.get(nm, 0.5) / 2.0) for nm, e in RE.items()]

    def rope_clear(P):
        lo, hi = P.min(0) - 3, P.max(0) + 3
        best = None
        for nm, a_, b_, rad in ropes:
            if np.any(np.maximum(a_, b_) < lo) or np.any(np.minimum(a_, b_) > hi):
                continue
            dmin = float(seg_points_dist(a_, b_, P).min()) - 0.5 - rad
            if best is None or dmin < best[0]:
                best = [round(dmin, 2), nm]
        return best

    # 迴旋砲 arc：撞（不含自己的砲柱）、射線、砲手跟著繞轉軸轉、腳下 3×3、離繩 ≥ rope_min_cells（帆的靜索也會擋住迴旋砲）
    arcs = {}
    for r in placed:
        if not r['swivel']:
            continue
        g = guns[r['type']]
        mir = r['side'] == 'P'
        gun0 = crew[r['name']][0] if crew[r['name']] else None
        own_post = {(int(r['at'][0] - 0.5), int(r['at'][1] - 0.5), z) for z in range(r['deck_z'], r['deck_z'] + r['post_h'])}
        Gx = Grid((solid_all - own_post) | {c for k, v in occg.items() if v != r['name'] for c in [k]}, (AX, AY, AZ))
        ang = {}
        for a in range(-180, 180, GB['sweep_step_deg']):
            h = int(Gx.hit(g.world(g.samples, r['at'], float(a), mir)).sum())
            rb = ray(g, r['at'], float(a), mir, 40.0, grid=Gx)        # v3（verifier9 minor 1）：射線也要擋別的砲（含別的迴旋砲靜止的樣子）
            foot = None
            if gun0:
                c_, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
                px = r['at'][0] + c_ * (gun0[0] - r['at'][0]) - s_ * (gun0[1] - r['at'][1])
                py = r['at'][1] + s_ * (gun0[0] - r['at'][0]) + c_ * (gun0[1] - r['at'][1])
                fx, fy = int(math.floor(px)), int(math.floor(py))
                foot = sum(1 for u in (-1, 0, 1) for v in (-1, 0, 1) if Gs.get(fx + u, fy + v, gun0[2] - 1))
            rcl = rope_clear(g.world(g.centers, r['at'], float(a), mir))
            ang[a] = (h == 0 and rb is None and bool(foot) and (rcl is None or rcl[0] >= GB['rope_min_cells']), h, rb, foot, rcl)
        lo_, hi_ = [int(v) for v in r['arc_lim'].split(',')]
        if mir:
            lo_, hi_ = -hi_, -lo_
        lo = hi = 0
        if ang[0][0]:
            while lo - GB['sweep_step_deg'] >= lo_ and ang[lo - GB['sweep_step_deg']][0]:
                lo -= GB['sweep_step_deg']
            while hi + GB['sweep_step_deg'] <= hi_ and ang[hi + GB['sweep_step_deg']][0]:
                hi += GB['sweep_step_deg']
        r['arc'] = '%d,%d' % (lo, hi) if ang[0][0] else None
        arcs[r['name']] = {'arc': r['arc'], 'min_foot_in_arc': min((ang[a][3] or 0) for a in range(lo, hi + 1, GB['sweep_step_deg'])) if ang[0][0] else 0,
                           'first_bad': {str(a): list(ang[a][1:]) for a in (lo - GB['sweep_step_deg'], hi + GB['sweep_step_deg']) if a in ang}}
    R['swivel_arcs'] = arcs
    # 射線（迴旋砲照 arc 掃）、繩離砲
    rc = {}
    for r in placed:
        if r['swivel'] and r.get('arc'):
            a0, a1 = [int(v) for v in r['arc'].split(',')]
            angs = list(range(a0, a1 + 1, GB['sweep_step_deg']))
        else:
            angs = [r['phi']]
        best = None
        for a in angs:
            c_ = rope_clear(world_of(r, 'centers', phi=float(a)))
            if c_ and (best is None or c_[0] < best[0]):
                best = c_ + [a]
        rc[r['name']] = best
    R['rope_clearance_min'] = min((v for v in rc.values() if v), key=lambda v: v[0]) if any(rc.values()) else None
    R['rope_clearance_below_min'] = {k: v for k, v in rc.items() if v and v[0] < GB['rope_min_cells']}
    # ── 走路格（每層甲板 meta floor；砲擺上去前後）──
    DM = {}
    for line in open(os.path.join(HERE, 'decks_meta.tsv'), encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if len(f) >= 3 and f[0] == 'link':
            m = json.loads(f[2])
            if m.get('kind') == 'deck':
                DM[m['deck']] = poly(m['floor'])

    def nav(dk, use_boxes):
        F = DM[dk]
        xs = range(int(F[0][0]) // NAV_C * NAV_C, int(F[-1][0]) + NAV_C, NAV_C)
        ys = range(0, AY, NAV_C)
        Z = {}
        for x in xs:
            f = polyZ(F, x)
            if f is None:
                continue
            for y in ys:
                z = -1
                for zz in range(f + 3, f - 3, -1):
                    if Gs.get(x, y, zz - 1) and not any(Gs.get(x, y, zz + h) for h in range(0, NAV_HEAD)):
                        z = zz
                        break
                if z < 0 or (use_boxes and blocked(x, y, z)):
                    continue
                Z[(x, y)] = z
        comp, sizes = {}, []
        for k in Z:
            if k in comp:
                continue
            cid = len(sizes)
            comp[k] = cid
            q, n = [k], 0
            while q:
                a = q.pop()
                n += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    b = (a[0] + dx * NAV_C, a[1] + dy * NAV_C)
                    if b not in Z or b in comp or abs(Z[b] - Z[a]) > NAV_DZ:
                        continue
                    if dx and dy and ((a[0] + dx * NAV_C, a[1]) not in Z or (a[0], a[1] + dy * NAV_C) not in Z):
                        continue
                    comp[b] = cid
                    q.append(b)
            sizes.append(n)
        big = int(np.argmax(sizes)) if sizes else -1
        return Z, comp, sizes, big

    R['nav'] = {}
    LP = json.load(open(os.path.join(HERE, 'ladder_points.json'), encoding='utf-8'))
    for dk in DM:
        Z0, c0, s0, b0 = nav(dk, False)
        Z1, c1, s1, b1 = nav(dk, True)

        def in_main(p, Z=Z1, c=c1, big=b1):
            k = (int(round(p[0] / NAV_C)) * NAV_C, int(round(p[1] / NAV_C)) * NAV_C)
            cands = [(k[0] + dx, k[1] + dy) for dx in (0, -NAV_C, NAV_C) for dy in (0, -NAV_C, NAV_C)]
            return any(c.get(q) == big for q in cands if q in Z and abs(Z[q] - p[2]) <= NAV_DZ)
        crew_out = [[r['name'], a] for r in placed if r['deck'] == dk for a in r['crew']['at'] if not in_main(a)]
        lad_out = []
        for nm, L in LP.items():
            for pn in ('foot', 'head'):
                p = L['points'][pn]
                dk_p = L['lo'] if pn == 'foot' else L['up']
                if dk_p == dk and not in_main(p):
                    lad_out.append([nm, pn])
        R['nav'][dk] = {'points_before': len(Z0), 'main_before': s0[b0] if s0 else 0, 'points_after': len(Z1), 'main_after': s1[b1] if s1 else 0,
                        'groups_ge12_before': sum(1 for v in s0 if v >= 12), 'groups_ge12_after': sum(1 for v in s1 if v >= 12),
                        'crew_spots_not_in_main': crew_out, 'ladder_points_not_in_main': lad_out}
    for r in placed:
        r['muzzle_ray_blocked_at'] = r.get('ray_blocked_at')
    R['problems'] = (len(fail) + len(R['not_ok']) + len(R['hit_samples']) + len(clash) + len(R['asymmetric_pairs']) + len(R['broadside_barrel_not_in_port'])
                     + len(rec) + len(R['crew_below_min']) + len(R['rope_clearance_below_min'])
                     + sum(len(v['crew_spots_not_in_main']) + len(v['ladder_points_not_in_main']) for v in R['nav'].values())
                     + sum(1 for v in arcs.values() if not v['arc'] or not v['min_foot_in_arc']))
    if probe:
        print(json.dumps({'probe': probe, 'problems': R['problems'], 'readings': {k: v for k, v in R.items() if k not in ('read',)},
                          'rows': [{k: r.get(k) for k in ('name', 'at', 'phi', 'angle_fwd', 'back', 'dz', 'ok', 'muzzle_out', 'ray_blocked_at', 'support', 'gap_max', 'muzzle_beyond_hull', 'muzzle_beyond_outer', 'angles_tried')} for r in rows]},
                         ensure_ascii=False))
        return
    for r in placed:
        r.pop('ray_blocked_at', None)
    json.dump({'note': 'draft_guns.py：at ＝ 模型 at（pivot 落在這裡）、phi ＝ rotate z、P 舷 mirror y', 'rows': rows},
              open(os.path.join(HERE, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(HERE, 'masks', 'guns'), exist_ok=True)
    outs = ['guns_placement.json', 'sheet07_guns_v1.png']
    for dk, pc in sorted(posts_by_deck.items()):
        fn = os.path.join('masks', 'guns', 'posts_%s.vox.txt' % dk)
        with open(os.path.join(HERE, fn), 'w', encoding='utf-8', newline='\n') as fo:
            fo.write('# 利劍號 迴旋砲砲柱（draft_guns.py 產生；落在 %s 甲板的子作品 %s）\n' % (dk, GB['deck_works'][dk]))
            fo.write(''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(pc.items())))
        outs.append(fn)
    R['post_cells_by_deck'] = {dk: len(pc) for dk, pc in sorted(posts_by_deck.items())}
    R['outputs'] = outs
    json.dump(R, open(os.path.join(HERE, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)

    # ── 新圖紙 07：平面（砲、迴旋砲 arc、砲手）＋左舷側面 ──
    sc = 2
    W_, H_ = 40 + 600 * sc + 40, 70 + 261 * sc + 40 + 140 * sc + 40
    img = Image.new('RGB', (W_, H_), (250, 248, 242))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    except OSError:
        f = ImageFont.load_default()
    d.text((40, 15), '%s - new sheet 07: guns (%s); black = guns, red = swivels and their arcs, blue = game gun-crew spots'
           % (plan['title_en'], ', '.join('%d x %s' % (v, k) for k, v in sorted(R['by_type'].items()))), fill=(20, 20, 20), font=f)
    oy = 50
    Xs = lambda x: 40 + x * sc
    top = {}
    for (x, y, z) in solid_stand:
        if z > top.get((x, y), -1):
            top[(x, y)] = z
    for (x, y), z in top.items():
        v = int(120 + min(100, z))
        d.rectangle([Xs(x), oy + y * sc, Xs(x + 1) - 1, oy + (y + 1) * sc - 1], fill=(v, v - 10, v - 30))
    for r in placed:
        col = (30, 30, 30) if not r['swivel'] else (170, 30, 40)
        for p in world_of(r, 'centers'):
            d.point((Xs(p[0]), oy + p[1] * sc), fill=col)
        for a in r['crew']['at']:
            d.ellipse([Xs(a[0]) - 2, oy + a[1] * sc - 2, Xs(a[0]) + 2, oy + a[1] * sc + 2], fill=(40, 60, 200))
        if r['swivel'] and r.get('arc'):
            g = guns[r['type']]
            a0, a1 = [int(v) for v in r['arc'].split(',')]
            for a in range(a0, a1 + 1, GB['sweep_step_deg']):
                mz = g.world(g.anchors['muzzle'][None], r['at'], float(a), r['side'] == 'P')[0]
                d.point((Xs(mz[0]), oy + mz[1] * sc), fill=(220, 120, 0))
    oz = oy + 261 * sc + 40 + 140 * sc
    Zs = lambda z: oz - z * sc
    side_ = {}
    for (x, y, z) in solid_stand:
        if y <= YC:
            side_[(x, z)] = 1
    for (x, z) in side_:
        d.rectangle([Xs(x), Zs(z + 1), Xs(x + 1) - 1, Zs(z) - 1], fill=(190, 175, 150))
    for r in placed:
        if r['side'] != 'P':
            continue
        for p in world_of(r, 'centers'):
            d.point((Xs(p[0]), Zs(p[2])), fill=(30, 30, 30) if not r['swivel'] else (170, 30, 40))
    d.text((40, oz - 140 * sc - 25), 'port side (z 0 .. 140)', fill=(20, 20, 20), font=f)
    img.save(os.path.join(HERE, 'sheet07_guns_v1.png'), optimize=False)
    print(json.dumps({k: v for k, v in R.items() if k not in ('read',)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
