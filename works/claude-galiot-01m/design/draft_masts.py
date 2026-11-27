# 蠍子號 新圖紙 05（TASK-0023 步驟 7）：桅、桅孔、三角帆桁
#   出處：海鷗號 claude-felucca-01m/design/draft_masts.py（它出自星辰號 → 收穫號：三角帆桁在自己的框裡就做成斜的、模型 rotate 0、固定點 pivot／sling／fore／peak／jackstay）；
#         桅孔照皇家號 apex-one-reale-01m／越嶺號 kotoko-fusta-01m（桅穿過甲板-main 的格刻掉、由桅填滿）；
#         走路格照 Blockside 42_hands.js navBuild／navZ／navStep、35_decks.js deckWalk／polyZ、40_crew.js standZ（verifier456 v4_nav.py 的寫法）。
#   改的地方：只有一根桅、沒有船頭桿；桅直立（rake 0）、截面 3 × 3；桅頂 calcet 5 × 3；走路格照遊戲每 2 格取樣（NAV_C 2）量中央走道過不過得了桅。
#   輸入：plan.json（layout.rig、rig_build、space）、前面每一步的設計清單（船殼 hull_01＋步驟 6 換色、甲板-main、船首平台、spur、艉台、篷）與 decks_meta.tsv
#         ——不讀作品 ⇒ 落格之後重跑一樣。
#   輸出：masks/masts/main.vox.txt（桅子作品，at 0,0,0、組裝件的框）、masks/masts/deck_hole.vox.txt（甲板-main 要刻的格，帶現在的顏色守門）、
#         masks/yards/lateen-main.vox.txt（帆桁子作品，自己的框）、yards_lateen.json、yards_placement.json、verify_masts.json、sheet05_masts_v1.png
#   用法：python -I -X utf8 draft_masts.py [--probe=r=2.1] [--probe=pivot=-40] [--probe=hole=0]
#     反向對照（不寫檔）：桅粗到 5 格 ⇒ 中央走道要斷；帆桁吊點上下挪 ⇒「匯入檢查那一段」的桅格數、跟船的距離要變；不刻桅孔 ⇒ 桅要斷成兩段。
import sys, os, json, math, hashlib
from collections import deque
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
CELL = 0.1
NAV_C, NAV_HEAD, NAV_DZ, NAV_MINREG = 2, 12, 3, 12     # 遊戲 42_hands.js


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


# ───────── 遊戲的走路格（每 NAV_C 格一點；8 鄰、斜走兩個側點都要站得住）─────────
def poly(s):
    return sorted((tuple(float(v) for v in p.split(':')) for p in s.split(',')), key=lambda a: a[0])


def polyZ(F, x):
    for i in range(1, len(F)):
        if x <= F[i][0]:
            a, b = F[i - 1], F[i]
            t = 0 if b[0] == a[0] else (x - a[0]) / (b[0] - a[0])
            return int(math.floor(a[1] + (b[1] - a[1]) * t + 0.5))
    return int(F[-1][1])


def deck_meta():
    for line in open(os.path.join(HERE, 'decks_meta.tsv'), encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if len(f) >= 3 and f[1] == '甲板-main':
            m = json.loads(f[2])
            return {'floor': poly(m['floor']), 'walk': poly(m['walk']), 'wy': [float(v) for v in m['walk_y'].split(':')]}
    raise SystemExit('✗ decks_meta.tsv 沒有甲板-main')


def deck_walk(d, x, y):
    W, Y, F = d['walk'], d['wy'], d['floor']
    if W[0][0] - 0.5 <= x <= W[-1][0] + 0.5 and Y[0] - 0.5 <= y <= Y[1] + 0.5:
        return polyZ(W, x)
    if x < F[0][0] - 0.5 or x > F[-1][0] + 0.5:
        return None
    return polyZ(F, x)


def stand_z(G, x, y, z0, z1):
    for z in range(z1, z0 - 1, -1):
        if z < 1 or z + NAV_HEAD > G.shape[2]:
            continue
        if G[x, y, z - 1] and not G[x, y, z:z + NAV_HEAD].any():
            return z
    return -1


def nav(G, d, hx0, hx1, only_y=None):
    """only_y=(y0, y1)：只留 y 在這段的取樣點再切連通（量「只走中央走道過不過得了桅」）。"""
    SX, SY = G.shape[:2]
    x0 = max(0, hx0 - 4)
    nx = int(math.ceil((min(SX, hx1 + 5) - x0) / NAV_C)) + 1
    ny = int(math.ceil(SY / NAV_C))
    Z = np.full((nx, ny), -1, np.int32)
    for i in range(1, nx - 1):
        gx = x0 + i * NAV_C
        if gx >= SX:
            continue
        for j in range(1, ny - 1):
            gy = j * NAV_C
            f = deck_walk(d, gx, gy)
            if f is not None and (only_y is None or only_y[0] <= gy <= only_y[1]):
                Z[i, j] = stand_z(G, gx, gy, f - 2, f + 3)
    DX, DY = [1, -1, 0, 0, 1, 1, -1, -1], [0, 0, 1, -1, 1, -1, 1, -1]
    comp = np.full((nx, ny), -1, np.int32)
    sizes = []
    for i in range(nx):
        for j in range(ny):
            if Z[i, j] < 0 or comp[i, j] >= 0:
                continue
            cid = len(sizes)
            comp[i, j] = cid
            q, n = deque([(i, j)]), 0
            while q:
                a, b = q.popleft()
                n += 1
                for k in range(8):
                    u, v = a + DX[k], b + DY[k]
                    if not (0 <= u < nx and 0 <= v < ny) or Z[u, v] < 0 or abs(Z[u, v] - Z[a, b]) > NAV_DZ:
                        continue
                    if k >= 4 and (Z[a + DX[k], b] < 0 or Z[a, b + DY[k]] < 0):
                        continue
                    if comp[u, v] < 0:
                        comp[u, v] = cid
                        q.append((u, v))
            sizes.append(n)
    big = int(np.argmax(sizes)) if sizes else -1

    def at(x, y):
        i, j = int(math.floor((x - x0) / NAV_C + 0.5)), int(math.floor(y / NAV_C + 0.5))
        return {'sample': [x0 + i * NAV_C, j * NAV_C], 'z': int(Z[i, j]), 'in_main_group': bool(comp[i, j] == big and big >= 0)}

    return {'x0': x0, 'points': int((Z >= 0).sum()), 'groups': len(sizes), 'main_points': sizes[big] if sizes else 0,
            'groups_ge_minreg': sum(1 for s in sizes if s >= NAV_MINREG), 'others_ge_minreg': sorted((s for i, s in enumerate(sizes) if i != big and s >= NAV_MINREG), reverse=True)[:8]}, at


def main():
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    AX, AY, AZ = [int(v) for v in plan['space']['assembly']]
    RB = {k: V(v) for k, v in plan['rig_build'].items() if k != 'src'}
    C = RB['colors']
    MH = RB['masthead']
    Y = RB['yard']
    RIG = V(plan['layout']['rig'])
    LR = json.load(open(os.path.join(HERE, 'verify_layout.json'), encoding='utf-8'))['masts']['main']   # 步驟 3 圖紙 02 的桅位與頂
    xm, top_z = int(RIG['masts']['main']['x']), int(round(LR['top_z']))
    r = float(probe.get('r', RB['mast']['r']))

    hull = load('masks/hull/hull_01.vox.txt')
    hull.update(load('masks/step6/hull_paint.vox.txt'))
    deck = load('masks/decks/deck_main.vox.txt')
    others = {}
    for fn in ('masks/decks/bow.vox.txt', 'masks/deco/spur.vox.txt', 'masks/deco/poop.vox.txt'):
        others.update(load(fn))
    awning = load('masks/deco/awning.vox.txt')            # 外部模型 deco=1：帆桁不能撞它，走路格不算它

    # ── 桅：截面（格心離軸 ≤ r）從船殼最上一格往上到 calcet 底；calcet 5 × 3、滑輪槽、金帽 ──
    mast = {}
    cols = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4) if dx * dx + dy * dy <= r * r + 1e-9]
    for dx, dy in cols:
        x, y = xm + dx, YC + dy
        zh = max((z for (a, b, z) in hull if a == x and b == y), default=-1) + 1
        for z in range(zh, top_z - MH['h']):
            mast[(x, y, z)] = C['mast']
    for z in range(top_z - MH['h'], top_z):
        for dx in range(-MH['half_x'], MH['half_x'] + 1):
            for dy in range(-MH['half_y'], MH['half_y'] + 1):
                c = C['mast']
                if dy == 0 and top_z - 1 - z in MH['sheave'] and abs(dx) == MH['half_x']:
                    c = C['sheave']
                if z >= top_z - MH['cap_h']:
                    c = C['cap']
                mast[(xm + dx, YC + dy, z)] = c
    on_hull = [k for k in mast if k in hull]
    hole = {k: deck[k] for k in mast if k in deck}
    if probe.get('hole') == '0':                          # 反向對照：不刻桅孔 ⇒ 桅在甲板那一段不放
        for k in list(hole):
            del mast[k]
        hole = {}
    deck_after = {k: c for k, c in deck.items() if k not in hole}

    # ── 三角帆桁（自己的框）：一根斜桿，前端低（x 大）、後端高 ──
    Lc = Y['len_m'] / CELL
    th = math.radians(Y['tilt_deg'])
    pad = 3
    W_ = int(math.ceil(Lc * math.cos(th))) + 2 * pad
    H_ = int(math.ceil(Lc * math.sin(th))) + 2 * pad
    yc = 3
    F = (W_ - pad, pad)
    A = (F[0] - Lc * math.cos(th), F[1] + Lc * math.sin(th))
    hs = Y['hoist_frac'] * Lc
    vx, vz = A[0] - F[0], A[1] - F[1]
    ln = math.hypot(vx, vz)

    def radius(s):
        return Y['r_end'] + (Y['r_max'] - Y['r_end']) * max(0.0, 1 - abs(s - hs) / max(hs, Lc - hs))

    ycells = {}
    for x in range(0, W_):
        for z in range(0, H_):
            px, pz = x + 0.5 - F[0], z + 0.5 - F[1]
            t = (px * vx + pz * vz) / ln
            if t < -0.5 or t > ln + 0.5:
                continue
            tc = min(max(t, 0.0), ln)
            d2 = (px - tc * vx / ln) ** 2 + (pz - tc * vz / ln) ** 2
            rr = radius(tc)
            lash = abs(tc - hs) <= Y['lash_half'] and abs(tc - hs) > 1.5 and int(round(tc - hs)) % Y['lash_every'] == 0
            for dy in range(-3, 4):
                if d2 + dy * dy <= rr * rr:
                    ycells[(x, yc + dy, z)] = C['lashing'] if lash else C['yard']

    def near(s, top=False):
        px_, pz_ = F[0] + vx / ln * s, F[1] + vz / ln * s
        best = min((k for k in ycells if k[1] == yc), key=lambda k: ((k[0] + 0.5 - px_) ** 2 + (k[2] + 0.5 - pz_) ** 2, k))
        if top:
            z = best[2]
            while (best[0], yc, z + 1) in ycells:
                z += 1
            best = (best[0], yc, z)
        return list(best)

    anchors = {'pivot': near(hs), 'sling': near(hs, True), 'fore': near(1.0), 'peak': near(Lc - 1.0)}
    for k_, s in enumerate(np.arange(8.0, Lc - 4, 8.0)):
        anchors['jackstay-%02d' % (k_ + 1)] = near(float(s), True)
    pv = anchors['pivot']
    zp = top_z - Y['below_top'] + int(probe.get('pivot', 0))
    yw = YC + Y['y_off']
    off = (xm - pv[0], yw - pv[1], zp - pv[2])
    place = [{'name': 'yard-main-lateen', 'mast': 'main', 'host': 'mast-main', 'work': 'claude-galiot-01m-yard-main',
              'at': [xm + 0.5, yw + 0.5, zp + 0.5], 'pivot': [pv[0] + 0.5, pv[1] + 0.5, pv[2] + 0.5], 'rotate': [0, 0, 0], 'scale': [1, 1, 1],
              'meta': {'kind': 'yard', 'mast': 'main', 'yard': 'gaff', 'rig': 'lateen', 'sail': Y['sail'], 'length_m': Y['len_m'],
                       'length_ft': round(Y['len_m'] / 0.3048, 1), 'diameter_in': round((2 * int(Y['r_max']) + 1) * CELL / 0.0254, 1),
                       'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}}]

    # ── 讀數 ──
    R = {'probe': probe or None, 'mast_axis': [xm + 0.5, YC + 0.5], 'r': r, 'top_z': top_z}
    G = np.zeros((AX, AY, AZ), bool)
    for k in mast:
        G[k] = True
    _, n6 = ndimage.label(G)
    zs = sorted({k[2] for k in mast})
    R['mast'] = {'cells': len(mast), 'components_6': int(n6), 'z': [zs[0], zs[-1]] if zs else None,
                 'length_m': round((zs[-1] + 1 - zs[0]) * CELL, 2) if zs else None,
                 'heel_z_by_column': {'%d,%d' % (dx, dy): min(z for (x, y, z) in mast if x == xm + dx and y == YC + dy) for dx, dy in cols} if mast else None,
                 'section_cells': len(cols), 'section_y': [YC - max(abs(dy) for _, dy in cols), YC + max(abs(dy) for _, dy in cols)],
                 'mirror_diff': sum(1 for (x, y, z), c in mast.items() if mast.get((x, 2 * YC - y, z)) != c),
                 'colours': {str(c): sum(1 for v in mast.values() if v == c) for c in sorted(set(mast.values()))},
                 'overlap_hull': len(on_hull)}
    R['deck_hole'] = {'cells': len(hole), 'colours': {str(c): sum(1 for v in hole.values() if v == c) for c in sorted(set(hole.values()))},
                      'z': [min(k[2] for k in hole), max(k[2] for k in hole)] if hole else None,
                      'filled_by_mast': sum(1 for k in hole if k in mast)}
    ship = dict(hull)
    ship.update(deck_after)
    ship.update(others)
    R['overlap'] = {'mast_ship': sum(1 for k in mast if k in ship), 'mast_awning': sum(1 for k in mast if k in awning)}
    U = np.zeros((AX, AY, AZ), bool)
    for k in ship:
        U[k] = True
    for k in mast:
        U[k] = True
    _, ncomp = ndimage.label(U)
    R['ship_with_mast'] = {'cells': int(U.sum()), 'components_6': int(ncomp), 'cavities': int((ndimage.binary_fill_holes(U) & ~U).sum())}
    # 帆桁
    wc = {(x + off[0], y + off[1], z + off[2]) for (x, y, z) in ycells}
    an_w = {n: [a[0] + off[0], a[1] + off[1], a[2] + off[2]] for n, a in anchors.items()}
    G2 = np.zeros((W_, 7, H_), bool)
    for k in ycells:
        G2[k] = True
    _, ny6 = ndimage.label(G2)
    world = set(ship) | set(mast) | set(awning)
    tree = cKDTree(np.array(sorted(world), float))
    dmin, _ = tree.query(np.array(sorted(wc), float))
    piv, fore = an_w['pivot'], an_w['fore']
    xh = fore[0] - piv[0]
    band = [k for k in mast if piv[2] - 40 <= k[2] <= piv[2] - 10 and abs(k[1] - YC) <= 4]
    R['yard'] = {'size': [W_, 7, H_], 'cells': len(ycells), 'components_6': int(ny6), 'anchors': len(anchors),
                 'colours': {str(c): sum(1 for v in ycells.values() if v == c) for c in sorted(set(ycells.values()))},
                 'overlap_world': sum(1 for k in wc if k in world), 'min_gap_cells': round(float(dmin.min()) - 1, 2),
                 'world_x': [min(k[0] for k in wc), max(k[0] for k in wc)], 'world_y': [min(k[1] for k in wc), max(k[1] for k in wc)],
                 'world_z': [min(k[2] for k in wc), max(k[2] for k in wc)],
                 'pivot_world': piv, 'fore_world': fore, 'peak_world': an_w['peak'], 'sling_world': an_w['sling'],
                 'mast_cells_in_shipcheck_band': len(band), 'band_z': [piv[2] - 40, piv[2] - 10],
                 'empty_cells_between_yard_and_mast_y': min(k[1] for k in mast) - max(k[1] for k in wc) - 1 if mast else None,
                 'lateen_swing_deg': round(math.degrees(math.asin(min(1.0, 25.0 / xh))), 1) if xh > 0 else None,
                 'inside_assembly_box': all(0 <= k[0] < AX and 0 <= k[1] < AY and 0 <= k[2] < AZ for k in wc),
                 'pivot_inside_mast_frame': 0 <= piv[0] < AX and 0 <= piv[1] < AY and 0 <= piv[2] < AZ}
    # 走路格：桅之前（步驟 6 的船）vs 桅之後，照遊戲每 2 格取樣
    dm = deck_meta()
    Gb = np.zeros((AX, AY, AZ), bool)
    for k in set(hull) | set(deck) | set(others):
        Gb[k] = True
    xs = np.nonzero(Gb.any(axis=(1, 2)))[0]
    hx0, hx1 = int(xs.min()), int(xs.max())
    Nb, at_b = nav(Gb, dm, hx0, hx1)
    Na, at_a = nav(U, dm, hx0, hx1)
    wy = (int(dm['wy'][0]), int(dm['wy'][1]))
    Nc, at_c = nav(U, dm, hx0, hx1, wy)                   # 只走中央走道（walk_y 那幾欄）
    co = V(plan['layout']['corsia'])
    pr = {'corsia_aft_of_mast': (xm - 6, YC), 'corsia_fwd_of_mast': (xm + 6, YC), 'corsia_beside_mast_P': (xm, YC - 2), 'corsia_beside_mast_S': (xm, YC + 2),
          'corsia_aft_end': (co['x0'] + 1, YC), 'corsia_fwd_end': (co['x1'] - 1, YC), 'bow_platform': (339, YC), 'poop': (40, YC)}
    R['nav'] = {'game_sampling': 'NAV_C %d, x0 %d (hx0 %d - 4), y even; 8-neighbour, step <= %d, head %d' % (NAV_C, Nb['x0'], hx0, NAV_DZ, NAV_HEAD),
                'before_mast': Nb, 'after_mast': Na, 'points_lost': Nb['points'] - Na['points'],
                'probes_after': {k: at_a(*v) for k, v in pr.items()}, 'probes_before': {k: at_b(*v)['in_main_group'] for k, v in pr.items()},
                'corsia_only': {'y': list(wy), 'points': Nc['points'], 'groups_ge_minreg': Nc['groups_ge_minreg'], 'main_points': Nc['main_points'],
                                'aft_end_and_fwd_end_connected': at_c(co['x0'] + 1, YC)['in_main_group'] and at_c(co['x1'] - 1, YC)['in_main_group'],
                                'fore_and_aft_of_mast_connected': at_c(xm - 6, YC)['in_main_group'] and at_c(xm + 6, YC)['in_main_group']}}
    R['problems'] = (R['overlap']['mast_ship'] + R['overlap']['mast_awning'] + R['mast']['mirror_diff'] + (R['mast']['components_6'] != 1)
                     + (len(hole) - R['deck_hole']['filled_by_mast']) + (R['ship_with_mast']['components_6'] != 1) + R['ship_with_mast']['cavities']
                     + (R['yard']['components_6'] != 1) + R['yard']['overlap_world'] + (R['yard']['mast_cells_in_shipcheck_band'] == 0)
                     + (not R['yard']['inside_assembly_box']) + (Na['groups_ge_minreg'] != Nb['groups_ge_minreg'])
                     + sum(1 for v in R['nav']['probes_after'].values() if not v['in_main_group'])
                     + (not R['nav']['corsia_only']['fore_and_aft_of_mast_connected']) + (not R['nav']['corsia_only']['aft_end_and_fwd_end_connected']))
    if probe:
        print(json.dumps({'probe': probe, 'problems': R['problems'], 'mast': {k: R['mast'][k] for k in ('cells', 'components_6', 'section_y')},
                          'deck_hole': R['deck_hole']['cells'], 'ship_with_mast': R['ship_with_mast'],
                          'nav_groups_ge_minreg': [Nb['groups_ge_minreg'], Na['groups_ge_minreg']], 'nav_others_after': Na['others_ge_minreg'],
                          'probes_off_main': [k for k, v in R['nav']['probes_after'].items() if not v['in_main_group']], 'corsia_only': R['nav']['corsia_only'],
                          'yard': {k: R['yard'][k] for k in ('pivot_world', 'band_z', 'mast_cells_in_shipcheck_band', 'min_gap_cells', 'overlap_world')}}, ensure_ascii=False))
        return

    def dump(path, cl, head, color=True):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(head)
            for (x, y, z), c in sorted(cl.items()):
                fh.write('%d,%d,%d,%d\n' % (x, y, z, c))
        return hashlib.sha256(open(path, 'rb').read()).hexdigest()

    sha = {
        'masts/main': dump(os.path.join(HERE, 'masks', 'masts', 'main.vox.txt'), mast, '# 蠍子號 步驟 7：主桅（at 0,0,0、組裝件的框 %d×%d×%d）\n' % (AX, AY, AZ)),
        'masts/deck_hole': dump(os.path.join(HERE, 'masks', 'masts', 'deck_hole.vox.txt'), hole, '# 蠍子號 步驟 7：甲板-main 的桅孔（carvevox；第四欄 ＝ 刻之前的顏色，守門）\n'),
        'yards/lateen-main': dump(os.path.join(HERE, 'masks', 'yards', 'lateen-main.vox.txt'), ycells, '# 蠍子號 步驟 7：三角帆桁（自己的框 %d×7×%d）\n' % (W_, H_)),
    }
    R['sha256'] = sha
    with open(os.path.join(HERE, 'yards_lateen.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({'main': {'size': [W_, 7, H_], 'anchors': anchors, 'len_m': Y['len_m'], 'tilt_deg': Y['tilt_deg'], 'hoist_frac': Y['hoist_frac'], 'sail': Y['sail']}},
                  fh, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'yards_placement.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(place, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)

    # ── 圖紙 05：1. 側面（右舷外、船頭朝右）全船＋桅＋帆桁；2. 桅孔特寫（x 226–238 的平面、走路取樣點）──
    s = 3
    img = Image.new('RGB', (AX * s + 80, AZ * s + 330), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((30, 10), '%s - new sheet 05: main mast x %d (upright, %.1f m long, 3x3 cells, calcet 5x3), lateen yard %.1f m at %d deg, hoist %.0f%% from fwd end   0.1 m/cell'
           % (plan['title_en'], xm, R['mast']['length_m'], Y['len_m'], Y['tilt_deg'], Y['hoist_frac'] * 100), fill=(20, 20, 40), font=f)
    oy = 40 + AZ * s
    side = {}
    for src in (hull, deck_after, others, awning):
        for k, c in src.items():
            if k[1] >= YC and ((k[0], k[2]) not in side or k[1] > side[(k[0], k[2])][0]):
                side[(k[0], k[2])] = (k[1], c)
    for k, c in mast.items():                              # 桅畫在船殼外板前面（剖開看到腳），但照 y 排：從右舷看，左舷的帆桁在桅後面（verifier7：v1 帆桁畫在桅前面）
        if (k[0], k[2]) not in side or side[(k[0], k[2])][0] < 999 or k[1] > side[(k[0], k[2])][0] - 1000:
            side[(k[0], k[2])] = (1000 + k[1], c)
    for (x, y, z), c in ycells.items():
        p = (x + off[0], z + off[2])
        if p not in side or side[p][0] < 1000 + y + off[1]:
            side[p] = (1000 + y + off[1], c)
    for (x, z), (_, c) in side.items():
        d.rectangle([40 + x * s, oy - (z + 1) * s, 40 + x * s + s - 1, oy - z * s - 1], fill=rgb(c))
    wl = plan['waterline']['z']
    d.line([40, oy - (wl + 1) * s, 40 + AX * s, oy - (wl + 1) * s], fill=(40, 110, 200))
    for x in range(0, AX + 1, 20):
        d.text((40 + x * s - 6, oy + 6), str(x), fill=(80, 80, 80), font=f)
    for z in range(0, AZ + 1, 20):
        d.text((8, oy - z * s - 5), str(z), fill=(80, 80, 80), font=f)
    for nm, col in (('pivot', (200, 30, 30)), ('fore', (30, 120, 30)), ('peak', (30, 30, 200))):
        p = an_w[nm]
        d.ellipse([40 + p[0] * s - 4, oy - p[2] * s - 4, 40 + p[0] * s + 4, oy - p[2] * s + 4], outline=col, width=2)
        d.text((40 + p[0] * s + 8, oy - p[2] * s - 6), '%s (%d,%d,%d)' % (nm, p[0], p[1], p[2]), fill=col, font=f)
    b = R['yard']['band_z']
    d.rectangle([40 + (xm - 3) * s, oy - b[1] * s, 40 + (xm + 4) * s, oy - b[0] * s], outline=(200, 30, 200))
    d.text((40 + (xm + 6) * s, oy - b[1] * s), 'shipcheck band z %d-%d: %d mast cells' % (b[0], b[1], R['yard']['mast_cells_in_shipcheck_band']), fill=(200, 30, 200), font=f)
    # 2. 平面特寫：corsia 頂那一層（z 25）與上面一層（z 26），黑點 ＝ 走路取樣點（站得住）
    k = 14
    ox2, oy2 = 60, oy + 50
    d.text((40, oy + 30), '2. plan close-up x %d-%d, y %d-%d at corsia top z 25 (colour; red frame = mast); dots = game walk samples after the mast (black = main group, red = other group, none = cannot stand)' % (xm - 8, xm + 8, YC - 5, YC + 5), fill=(20, 20, 40), font=f)
    d.text((40, oy + 16), '1. profile from starboard (mast drawn over the hull side down to its heel on the keel, z %d)' % R['mast']['z'][0], fill=(20, 20, 40), font=f)
    Na_at = at_a
    for x in range(xm - 8, xm + 9):
        for y in range(YC - 5, YC + 6):
            c = mast.get((x, y, 25)) or deck_after.get((x, y, 25))
            X0, Y0 = ox2 + (x - xm + 8) * k, oy2 + (YC + 5 - y) * k
            if c:
                d.rectangle([X0, Y0, X0 + k - 2, Y0 + k - 2], fill=rgb(c), outline=(200, 30, 30) if (x, y, 25) in mast else None, width=2)
            if (x - Nb['x0']) % NAV_C == 0 and y % NAV_C == 0:
                q = Na_at(x, y)
                if q['z'] >= 0:
                    d.ellipse([X0 + 4, Y0 + 4, X0 + 9, Y0 + 9], fill=(0, 0, 0) if q['in_main_group'] else (220, 30, 30))
    rows = ['mast %d cells (z %d-%d, %.1f m), heel on hull, mirror diff %d; deck hole %d cells %s filled %d' % (R['mast']['cells'], R['mast']['z'][0], R['mast']['z'][1], R['mast']['length_m'], R['mast']['mirror_diff'], R['deck_hole']['cells'], R['deck_hole']['colours'], R['deck_hole']['filled_by_mast']),
            'ship + mast: %s; overlaps %s' % (R['ship_with_mast'], R['overlap']),
            'yard %d cells, %d anchors, overlap %d, min gap %.1f cells, world x %s z %s, lateen swing %s deg' % (R['yard']['cells'], R['yard']['anchors'], R['yard']['overlap_world'], R['yard']['min_gap_cells'], R['yard']['world_x'], R['yard']['world_z'], R['yard']['lateen_swing_deg']),
            'walk grid (game NAV_C 2): groups >= 12 points before %d / after %d; main group %d -> %d points; corsia fore/aft of mast in main group: %s / %s'
            % (Nb['groups_ge_minreg'], Na['groups_ge_minreg'], Nb['main_points'], Na['main_points'], R['nav']['probes_after']['corsia_aft_of_mast']['in_main_group'], R['nav']['probes_after']['corsia_fwd_of_mast']['in_main_group']),
            'corsia only (y %d-%d): fore and aft of the mast connected %s, aft end to fwd end connected %s' % (wy[0], wy[1], R['nav']['corsia_only']['fore_and_aft_of_mast_connected'], R['nav']['corsia_only']['aft_end_and_fwd_end_connected']),
            'problems %d' % R['problems']]
    for i, t in enumerate(rows):
        d.text((ox2 + 18 * k, oy2 + i * 18), t, fill=(30, 30, 30), font=f)
    img.save(os.path.join(HERE, 'sheet05_masts_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k != 'nav'} | {'nav': {k: R['nav'][k] for k in ('points_lost', 'probes_before', 'corsia_only')} | {
        'before': {k: Nb[k] for k in ('points', 'groups_ge_minreg', 'main_points', 'others_ge_minreg')},
        'after': {k: Na[k] for k in ('points', 'groups_ge_minreg', 'main_points', 'others_ge_minreg')},
        'probes_after': R['nav']['probes_after']}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
