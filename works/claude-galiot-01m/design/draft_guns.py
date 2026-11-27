# 蠍子號 新圖紙 07（TASK-0023 步驟 9）：船首三門砲（FUR p.80：中線一門最大的、兩旁各一門後膛小砲）⇒ guns_placement.json、verify_guns.json、sheet07_guns_v1.png
#   出處：海鷗號 claude-felucca-01m/design/draft_guns.py（共用件 apex-one-reale-01m-gun-pierrier＋拆好的 -mount、scale 0.5、pivot 在叉架插銷底 (5.5,18.5,0)、
#         meta kind=gun gun=pierrier mount=turret arc rate、座 kind=gunmount mount_of；碰撞照 Ship_Guns §4.2：格心＋八個角，每 10° 一個角度＋砲口往外的射線）；
#         8l 的擺法照皇家號（ridge-two-centurion-01m-gun-8l，scale 0.5、pivot 砲架尾底 (7.5,0,0)、rotate −90 ⇒ 砲口朝船頭）。
#   改的地方：8l 固定（沒有 mount），沿中線從前往後退到「零碰撞」再要求砲口出了船首胸牆；多量後座退到底那一刻撞不撞（Ship_Guns §4.2「後座」：砲管長 × 0.3）；
#            兩門 pierrier 插在船首平台兩舷的胸牆頂（叉架插進胸牆），arc 照每 10° 的碰撞與射線量出來的連續範圍定。
#   用法：python -I -X utf8 draft_guns.py [--probe=gun8_x=-6] [--probe=pier_dy=-7]
#   · 讀前面每一步的設計清單與帆桁的世界格；共用砲件的格子用 CLI export 讀（唯讀、別人的作品）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio
import draft_masts as DM                                  # 遊戲走路格（deck meta、standZ、8 鄰）照步驟 7 那一支

sys.stdout.reconfigure(encoding='utf-8')
CORNERS = [(a, b, c) for a in (-0.5, 0.5) for b in (-0.5, 0.5) for c in (-0.5, 0.5)] + [(0, 0, 0)]


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def world(p, piv, scale, at, rot):
    """模型座標 p（0.05 m 格）⇒ 世界（0.1 m 格）：先減 pivot、縮 scale、繞 z 轉 rot、加 at。"""
    dx, dy, dz = (p[0] - piv[0]) * scale, (p[1] - piv[1]) * scale, (p[2] - piv[2]) * scale
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return (at[0] + c * dx - s * dy, at[1] + s * dx + c * dy, at[2] + dz)


def cells_hit(src, piv, scale, at, rot, solid):
    hit = 0
    for (i, j, k) in src:
        for (a, b, c) in CORNERS:
            w = world((i + 0.5 + a, j + 0.5 + b, k + 0.5 + c), piv, scale, at, rot)
            if (int(math.floor(w[0])), int(math.floor(w[1])), int(math.floor(w[2]))) in solid:
                hit += 1
                break
    return hit


def footprint(src, piv, scale, at, rot):
    out = set()
    for (i, j, k) in src:
        w = world((i + 0.5, j + 0.5, k + 0.5), piv, scale, at, rot)
        out.add((int(math.floor(w[0])), int(math.floor(w[1])), int(math.floor(w[2]))))
    return out


def ray(mz, br, solid, far=60.0):
    u = np.array(mz) - np.array(br)
    u = u / np.linalg.norm(u)
    for t in np.arange(0.5, far, 0.5):
        q = np.array(mz) + t * u
        if (int(math.floor(q[0])), int(math.floor(q[1])), int(math.floor(q[2]))) in solid:
            return round(float(t), 1)
    return None


def model_box(src, piv, scale, at, rot):
    """模型的世界外框 [x0, y0, z0, x1, y1, z1]（格心＋八角都算）。"""
    P = np.array([world((i + 0.5 + a, j + 0.5 + b, k + 0.5 + c), piv, scale, at, rot) for (i, j, k) in src for (a, b, c) in CORNERS[:8]])
    return [float(v) for v in P.min(axis=0)] + [float(v) for v in P.max(axis=0)]


def nav_with_models(G, dm, hx0, hx1, boxes):
    """遊戲 navBuild：站在砲、舵輪、家具裡的點不能走 —— 40_crew.js blocked()：外框 x、y 各外擴 1 格、z 在 [底 −3, 頂]（模型高 ≤ 20 格 ⇒ 整個外框）。"""
    SX, SY = G.shape[:2]
    x0 = max(0, hx0 - 4)
    nx = int(math.ceil((min(SX, hx1 + 5) - x0) / DM.NAV_C)) + 1
    ny = int(math.ceil(SY / DM.NAV_C))
    Z = np.full((nx, ny), -1, np.int32)
    blk = 0
    for i in range(1, nx - 1):
        gx = x0 + i * DM.NAV_C
        for j in range(1, ny - 1):
            gy = j * DM.NAV_C
            f = DM.deck_walk(dm, gx, gy)
            if f is None:
                continue
            z = DM.stand_z(G, gx, gy, f - 2, f + 3)
            if z >= 0 and any(math.floor(b[0]) - 1 <= gx <= math.ceil(b[3]) + 1 and math.floor(b[1]) - 1 <= gy <= math.ceil(b[4]) + 1 and b[2] - 3 <= z <= b[5] for b in boxes):
                blk += 1
                continue
            Z[i, j] = z
    DX, DY = [1, -1, 0, 0, 1, 1, -1, -1], [0, 0, 1, -1, 1, -1, 1, -1]
    comp = np.full((nx, ny), -1, np.int32)
    sizes = []
    for i in range(nx):
        for j in range(ny):
            if Z[i, j] < 0 or comp[i, j] >= 0:
                continue
            cid = len(sizes)
            comp[i, j] = cid
            q, n = [(i, j)], 0
            while q:
                a, b = q.pop()
                n += 1
                for k in range(8):
                    u, v = a + DX[k], b + DY[k]
                    if not (0 <= u < nx and 0 <= v < ny) or Z[u, v] < 0 or abs(Z[u, v] - Z[a, b]) > DM.NAV_DZ:
                        continue
                    if k >= 4 and (Z[a + DX[k], b] < 0 or Z[a, b + DY[k]] < 0):
                        continue
                    if comp[u, v] < 0:
                        comp[u, v] = cid
                        q.append((u, v))
            sizes.append(n)
    big = int(np.argmax(sizes))

    def at(x, y):
        i, j = int(math.floor((x - x0) / DM.NAV_C + 0.5)), int(math.floor(y / DM.NAV_C + 0.5))
        return {'sample': [x0 + i * DM.NAV_C, j * DM.NAV_C], 'z': int(Z[i, j]), 'in_main_group': bool(comp[i, j] == big)}

    return {'points': int((Z >= 0).sum()), 'blocked_by_models': blk, 'main_points': sizes[big], 'groups_ge_minreg': sum(1 for s in sizes if s >= DM.NAV_MINREG)}, at


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    GB = {k: V(v) for k, v in plan['guns_build'].items() if k != 'src'}
    RA = V(plan['layout']['rambade'])
    hull = load('masks/hull/hull_01.vox.txt')
    hole = load('masks/masts/deck_hole.vox.txt')
    deck = {k for k in load('masks/decks/deck_main.vox.txt') if k not in hole}
    bow = load('masks/decks/bow.vox.txt')
    ship = set(hull) | deck | set(bow) | set(load('masks/deco/spur.vox.txt')) | set(load('masks/deco/poop.vox.txt')) | set(load('masks/masts/main.vox.txt'))
    PL = json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8'))[0]
    for (x, y, z) in load('masks/yards/lateen-main.vox.txt'):
        ship.add((int(round(x + 0.5 - PL['pivot'][0] + PL['at'][0] - 0.5)), int(round(y + 0.5 - PL['pivot'][1] + PL['at'][1] - 0.5)),
                  int(round(z + 0.5 - PL['pivot'][2] + PL['at'][2] - 0.5))))
    T = {}
    for key, t in GB['types'].items():
        src = [tuple(r[:3]) for r in wio.export_list(t['work'], None).tolist()]
        if t.get('mount_work'):
            src += [tuple(r[:3]) for r in wio.export_list(t['mount_work'], None).tolist()]
        T[key] = dict(t, src=src)
    zt = max(k[2] for k in bow if k[1] == YC and k[2] < 28) + 1   # 平台站面：中線那一欄的板最上一格 ＋1（v1 拿全部 z ≤ 26 ⇒ 撿到胸牆的柱 z 26、站面算成 27）
    R = {'probe': probe or None, 'stand_z': zt, 'guns': []}
    models = []

    # ── 8l：中線、砲口朝船頭（rotate −90）；從「砲口剛好在胸牆外」往後退到零碰撞 ──
    G8 = GB['gun8']
    t8 = T['8l']
    # 從「中央走道末端 ＋ gap」往船頭找：第一個零碰撞、底下的輪子都踩在實心上、砲口出了胸牆 muzzle_out 格的位置
    #   （v1 從胸牆往後退：x_rear 326 就零碰撞，但砲架尾貼著中央走道末端 x 325 ⇒ 遊戲把砲的外框外擴 1 格當障礙，走道上不了平台）
    co = V(plan['layout']['corsia'])
    zb = min(k[2] for k in t8['src'])
    bottom = [k for k in t8['src'] if k[2] == zb]

    def unsupported(at):
        n = 0
        for (i, j, k) in bottom:
            w = world((i + 0.5, j + 0.5, k + 0.5), t8['pivot'], t8['scale'], at, -90)
            if (int(math.floor(w[0])), int(math.floor(w[1])), int(math.floor(w[2])) - 1) not in ship:
                n += 1
        return n
    tries = []
    x_rear = None
    for k in range(0, 40):
        xr = co['x1'] + G8['gap'] + k + int(probe.get('gun8_x', 0))
        if 'gun8_fixed' in probe:                             # 反向對照：不搜，直接放在 x_rear ＝ 這個值，報撞幾格、懸空幾格
            xr = float(probe['gun8_fixed'])
        at = [xr, YC + 0.5, float(zt)]
        h = cells_hit(t8['src'], t8['pivot'], t8['scale'], at, -90, ship)
        u = unsupported(at)
        mx = world([v + 0.5 for v in t8['muzzle']], t8['pivot'], t8['scale'], at, -90)[0]
        tries.append((xr, h, u, round(mx - (RA['x'][1] + 1), 2)))
        if (h == 0 and u == 0 and mx - (RA['x'][1] + 1) >= G8['muzzle_out']) or 'gun8_fixed' in probe:
            x_rear = xr
            break
    assert x_rear is not None, tries
    R['gun8_cells_hit_at_x_rear'] = tries[-1][1]
    R['gun8_bottom_cells_unsupported'] = tries[-1][2]
    at8 = [x_rear, YC + 0.5, float(zt)]
    mz = world([v + 0.5 for v in t8['muzzle']], t8['pivot'], t8['scale'], at8, -90)
    br = world([v + 0.5 for v in t8['breech']], t8['pivot'], t8['scale'], at8, -90)
    recoil = 0.3 * math.dist(mz, br)
    at8r = [x_rear - recoil, at8[1], at8[2]]
    fp8 = footprint(t8['src'], t8['pivot'], t8['scale'], at8, -90)
    R['guns'].append({'id': 'gun-1', 'gun': '8l', 'at': at8, 'rot': -90, 'tries': tries, 'muzzle': [round(v, 2) for v in mz], 'breech': [round(v, 2) for v in br],
                      'muzzle_past_parapet_cells': round(mz[0] - (RA['x'][1] + 1), 2), 'bore_above_stand_m': round((mz[2] - zt) * 0.1, 2),
                      'ray_blocked_at_cells': ray(mz, br, ship), 'recoil_cells': round(recoil, 2),
                      'recoil_cells_hit': cells_hit(t8['src'], t8['pivot'], t8['scale'], at8r, -90, ship),
                      'footprint_y': [min(k[1] for k in fp8), max(k[1] for k in fp8)], 'footprint_x': [min(k[0] for k in fp8), max(k[0] for k in fp8)]})
    models.append({'host': 'bow', 'name': '8磅砲-F01', 'work': t8['work'], 'at': at8, 'pivot': t8['pivot'], 'scale': t8['scale'], 'rotate': [0, 0, -90],
                   'meta': {'kind': 'gun', 'gun': '8l', 'deck': 'main', 'id': 'gun-1', 'port': 'bow'}})

    # ── pierrier ×2：插在船首平台兩舷胸牆頂（叉架插銷底 ＝ 胸牆頂面）；右舷 rotate 0（砲口朝 +y）、左舷 180 ──
    GP = GB['pierrier']
    tp = T['pierrier']
    # v2：插在平台上的砲柱頂（x、dy ±dy，柱高 post_h）——v1 插在胸牆頂，遊戲照砲的外框排砲手站位（40_crew.js makeCrew）⇒ 砲手站在 1 格寬的胸牆頂，
    #   迴旋砲轉的時候砲手跟著繞轉軸（21_gunnery.js mountStep）、腳下 3×3 都空就掉（32_hull.js svRest）⇒ 轉過 ±17° 就掉、朝船頭 68° 以上落海（verifier9）。
    #   柱頂夠高 ⇒ 砲尾掃過 8l 上方不撞；砲手站在平台板上、繞轉軸的圈整個在平台上。
    post = {}
    PH = GP['post_h'] + int(probe.get('post_h', 0))
    for side in (1, -1):
        y = YC + side * (GP['dy'] + int(probe.get('pier_dy', 0)))
        for z in range(zt, zt + PH):
            post[(GP['x'], y, z)] = GP['post_color']
    solid_p = ship | fp8 | set(post)
    D2 = math.pi / 180

    def game_gunner(at, rot):
        """遊戲 makeCrew 的砲手站位（只算第一個：pierrier 砲班 1 人）：外框 ＝ 砲＋座（gmtPair）取 floor；砲軸偏正橫 ⇒ [b0−3, y0＋10·sg]，
           y0 ＝ S 舷 b1／P 舷 b4；高度 b2−8 … b2＋3、頭上 14 格、不在任何模型外框（外擴 1 格）裡；standNear 從那一點往外一圈一圈找（≤ 4）。"""
        bx = model_box(tp['src'], tp['pivot'], tp['scale'], at, rot)
        b = [math.floor(v) for v in bx]
        sg = 1 if at[1] > YC else -1
        y0 = b[1] if sg > 0 else b[4]
        sx, sy = b[0] - 3, y0 + 10 * sg
        z0, z1 = b[2] - 8, b[2] + 3
        for r in range(0, 5):
            for ddy in range(-r, r + 1):
                for ddx in range(-r, r + 1):
                    if max(abs(ddx), abs(ddy)) != r:
                        continue
                    x, y = sx + ddx, sy + ddy
                    for z in range(z1, z0 - 1, -1):
                        if (x, y, z - 1) in solid_p and not any((x, y, z + h) in solid_p for h in range(0, 14)):
                            if not any(math.floor(q[0]) - 1 <= x <= math.ceil(q[3]) + 1 and math.floor(q[1]) - 1 <= y <= math.ceil(q[4]) + 1 and q[2] - 3 <= z <= q[5] for q in boxes_now):
                                return [x + 0.5, y + 0.5, z]
                            break
        return None
    boxes_now = [model_box(t8['src'], t8['pivot'], t8['scale'], at8, -90)]
    for i, (side, sd) in enumerate(((1, 'S'), (-1, 'P')), 2):
        x = GP['x']
        y = YC + side * (GP['dy'] + int(probe.get('pier_dy', 0)))
        at = [x + 0.5, y + 0.5, float(zt + PH)]
        rot = 0 if side > 0 else 180
        boxes_now.append(model_box(tp['src'], tp['pivot'], tp['scale'], at, rot))
    for i, (side, sd) in enumerate(((1, 'S'), (-1, 'P')), 2):
        x = GP['x']
        y = YC + side * (GP['dy'] + int(probe.get('pier_dy', 0)))
        at = [x + 0.5, y + 0.5, float(zt + PH)]
        rot = 0 if side > 0 else 180
        gunner = game_gunner(at, rot)
        rows = []
        for ang in range(-180, 180, 10):
            r_ = rot + ang
            h = cells_hit(tp['src'], tp['pivot'], tp['scale'], at, r_, solid_p - {(x, y, z) for z in range(zt, zt + PH)})
            m_ = world([v + 0.5 for v in tp['muzzle']], tp['pivot'], tp['scale'], at, r_)
            b_ = world([v + 0.5 for v in tp['breech']], tp['pivot'], tp['scale'], at, r_)
            fwd = math.degrees(math.atan2(m_[1] - b_[1], m_[0] - b_[0]))       # 砲口方向（0 ＝ 船頭、+90 ＝ +y 那一舷）
            foot = None
            if gunner:                                                          # 砲手跟著繞轉軸轉 ang 度，腳下 3×3 有沒有實心
                c_, s_ = math.cos(ang * D2), math.sin(ang * D2)
                px = at[0] + c_ * (gunner[0] - at[0]) - s_ * (gunner[1] - at[1])
                py = at[1] + s_ * (gunner[0] - at[0]) + c_ * (gunner[1] - at[1])
                fx, fy = int(math.floor(px)), int(math.floor(py))
                foot = sum(1 for a in (-1, 0, 1) for b in (-1, 0, 1) if (fx + a, fy + b, gunner[2] - 1) in solid_p)
            rows.append({'deg': ang, 'cells_hit': h, 'ray_blocked_at_cells': ray(m_, b_, solid_p, 40.0), 'muzzle': [round(v, 2) for v in m_],
                         'heading_deg': round(fwd, 1), 'gunner_foot_cells': foot})
        ok = {r['deg'] for r in rows if r['cells_hit'] == 0 and r['ray_blocked_at_cells'] is None and r['gunner_foot_cells']}
        lim = (-GP['arc_fwd'], GP['arc_aft']) if side > 0 else (-GP['arc_aft'], GP['arc_fwd'])   # 右舷 rotate 0：−90 ＝ 船頭；左舷 rotate 180：+90 ＝ 船頭
        lo = hi = 0
        if 0 in ok:
            while lo - 10 in ok and lo - 10 >= lim[0]:
                lo -= 10
            while hi + 10 in ok and hi + 10 <= lim[1]:
                hi += 10
        arc = (lo, hi) if 0 in ok else (0, 0)
        name = '迴旋砲-F%02d' % i
        g = {'id': 'gun-%d' % i, 'gun': 'pierrier', 'side': sd, 'at': at, 'rot': rot, 'arc': list(arc), 'angles': rows, 'gunner_at_rest': gunner,
             'gunner_min_foot_in_arc': min((r['gunner_foot_cells'] or 0) for r in rows if arc[0] <= r['deg'] <= arc[1]),
             'bore_above_stand_m': round((world([v + 0.5 for v in tp['muzzle']], tp['pivot'], tp['scale'], at, rot)[2] - zt) * 0.1, 2)}
        R['guns'].append(g)
        base = {'host': 'bow', 'at': at, 'pivot': tp['pivot'], 'scale': tp['scale'], 'rotate': [0, 0, rot]}
        models.append(dict(base, name=name, work=tp['work'], meta={'kind': 'gun', 'gun': 'pierrier', 'deck': 'main', 'id': g['id'], 'mount': 'turret',
                                                                   'arc': '%d,%d' % arc, 'rate': GP['rate'], 'port': 'bow'}))
        models.append(dict(base, name=name + '座', work=tp['mount_work'], meta={'kind': 'gunmount', 'id': 'gunmount-%d' % i, 'mount_of': g['id']}))
    R['post'] = {'cells': len(post), 'overlap_ship': len(set(post) & ship), 'on_board': all((x, y, zt - 1) in ship for (x, y, z) in post if z == zt)}
    # 兩門 pierrier 在 arc 兩端與中間的格，跟 8l、彼此重疊
    # 走路格（遊戲 navBuild＋砲的外框當障礙）：中央走道走得上平台、三門砲旁邊站得到人
    dm = DM.deck_meta()
    AX, AY, AZ = [int(v) for v in plan['space']['assembly']]
    Gm = np.zeros((AX, AY, AZ), bool)
    for k in ship | set(post):
        if 0 <= k[2] < AZ:
            Gm[k] = True
    xs = np.nonzero(Gm.any(axis=(1, 2)))[0]
    boxes = []
    for mdl in models:
        if mdl['meta']['kind'] == 'gun':
            t = T[mdl['meta']['gun']]
            boxes.append(model_box(t['src'], t['pivot'], t['scale'], mdl['at'], mdl['rotate'][2]))
    N0, at0 = nav_with_models(Gm, dm, int(xs.min()), int(xs.max()), [])
    N1, at1 = nav_with_models(Gm, dm, int(xs.min()), int(xs.max()), boxes)
    pr = {'corsia_mid': (195, YC), 'corsia_fwd_end': (co['x1'] - 1, YC), 'platform_aft_centre': (co['x1'] + 1, YC),
          'beside_8l_P': (340, YC - 8), 'beside_8l_S': (340, YC + 8), 'by_pierrier_P': (338, YC - 12), 'by_pierrier_S': (338, YC + 12)}
    R['nav'] = {'before_guns': N0, 'after_guns': N1, 'gun_boxes': [[round(v, 2) for v in b] for b in boxes], 'probes': {k: at1(*v) for k, v in pr.items()}}
    # 繩（步驟 8 的直線，verify_rigging.json）離砲多遠：8l 固定、pierrier 照 arc 每 10° 掃一圈；< 1 格 ⇒ 繩會穿過砲或被砲掃到
    from scipy.spatial import cKDTree
    RE = json.load(open(os.path.join(HERE, 'verify_rigging.json'), encoding='utf-8'))['rope_ends']
    gun_pts = [np.array(sorted(fp8), float) + 0.5]
    for g in R['guns'][1:]:
        for a in range(g['arc'][0], g['arc'][1] + 1, 10):
            gun_pts.append(np.array(sorted(footprint(tp['src'], tp['pivot'], tp['scale'], g['at'], g['rot'] + a)), float) + 0.5)
    tree = cKDTree(np.concatenate(gun_pts))
    R['rope_to_guns_cells'] = {}
    for nm, e in RE.items():
        a, b = np.array(e['from']), np.array(e['to'])
        pts = np.array([a + t * (b - a) for t in np.linspace(0, 1, int(np.linalg.norm(b - a) * 2) + 2)])
        R['rope_to_guns_cells'][nm] = round(float(tree.query(pts)[0].min()), 2)
    R['problems'] = (R['gun8_cells_hit_at_x_rear'] + sum(1 for v in R['rope_to_guns_cells'].values() if v < 1.5) + R['post']['overlap_ship'] + (not R['post']['on_board'])
                     + sum(1 for g in R['guns'][1:] if not g['gunner_at_rest'] or not g['gunner_min_foot_in_arc']) + R['gun8_bottom_cells_unsupported'] + sum(1 for v in R['nav']['probes'].values() if not v['in_main_group']) + sum(1 for g in R['guns'] if g['gun'] == '8l' and (g['ray_blocked_at_cells'] is not None or g['muzzle_past_parapet_cells'] <= 0 or g['recoil_cells_hit']))
                     + sum(1 for g in R['guns'] if g['gun'] == 'pierrier' and g['arc'][1] - g['arc'][0] < 90))
    if probe:
        print(json.dumps({'probe': probe, 'problems': R['problems'], 'gun8': {k: R['guns'][0][k] for k in ('at', 'muzzle', 'muzzle_past_parapet_cells', 'ray_blocked_at_cells', 'recoil_cells_hit', 'footprint_y')},
                          'gun8_cells_hit': R['gun8_cells_hit_at_x_rear'], 'gun8_unsupported': R['gun8_bottom_cells_unsupported'],
                          'nav_off_main': [k for k, v in R['nav']['probes'].items() if not v['in_main_group']], 'nav_main': [R['nav']['before_guns']['main_points'], R['nav']['after_guns']['main_points']],
                          'rope_to_guns_cells': R['rope_to_guns_cells'],
                          'pierrier': [(g['side'], g['at'], g['arc'], g['gunner_at_rest'], g['gunner_min_foot_in_arc'], [(r['deg'], r['cells_hit'], r['gunner_foot_cells']) for r in g['angles'] if r['deg'] in (-90, -45, 0, 45, 90)]) for g in R['guns'][1:]], 'post': R['post']}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'guns'), exist_ok=True)
    with open(os.path.join(HERE, 'masks', 'guns', 'posts.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蠍子號 船首平台的兩根迴旋砲柱（draft_guns.py；落在船首平台子作品）x,y,z,color —— at 0,0,0\n')
        f.write(''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(post.items())))
    with open(os.path.join(HERE, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'hosts': {'bow': 'claude-galiot-01m-bow'}, 'models': models}, f, ensure_ascii=False, indent=1)
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('guns_placement.json', 'masks/guns/posts.vox.txt')}
    with open(os.path.join(HERE, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    # 圖紙 07：船首平台平面（上看）＋三門砲的腳印、pierrier 的 arc
    s_ = 10
    x0, x1, y0, y1 = 316, 372, YC - 26, YC + 26
    img = Image.new('RGB', ((x1 - x0) * s_ + 80, (y1 - y0) * s_ + 120), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((30, 10), '%s - new sheet 07: bow guns (FUR p.80): 8l on the centreline (fixed, muzzle through the bow parapet port), 2 pierriers on the side parapets (mount=turret)' % plan['title_en'], fill=(20, 20, 40), font=f)
    top = {}
    for (x, y, z) in ship:
        if x0 <= x < x1 and y0 <= y < y1 and z < 60 and z >= top.get((x, y), -1):
            top[(x, y)] = z
    for (x, y), z in top.items():
        g_ = 230 - min(150, max(0, (z - 10) * 5))
        d.rectangle([40 + (x - x0) * s_, 40 + (y1 - 1 - y) * s_, 40 + (x - x0) * s_ + s_ - 1, 40 + (y1 - 1 - y) * s_ + s_ - 1], fill=(g_, g_ - 10, g_ - 30))
    for g in R['guns']:
        t = T[g['gun']]
        for (x, y, z) in footprint(t['src'], t['pivot'], t['scale'], g['at'], g['rot']):
            if x0 <= x < x1 and y0 <= y < y1:
                d.rectangle([40 + (x - x0) * s_ + 2, 40 + (y1 - 1 - y) * s_ + 2, 40 + (x - x0) * s_ + s_ - 3, 40 + (y1 - 1 - y) * s_ + s_ - 3], fill=(40, 40, 40))
        if g['gun'] == 'pierrier':
            cx, cy = 40 + (g['at'][0] - x0) * s_, 40 + (y1 - g['at'][1]) * s_
            for a in (g['arc'][0], g['arc'][1]):
                hd = math.radians(g['rot'] + 90 + a)
                d.line([cx, cy, cx + 120 * math.cos(hd), cy - 120 * math.sin(hd)], fill=(200, 30, 30), width=2)
            d.text((cx + 6, cy + 6), '%s arc %s' % (g['id'], g['arc']), fill=(200, 30, 30), font=f)
    g0 = R['guns'][0]
    d.text((40, (y1 - y0) * s_ + 60), 'gun-1 8l at %s muzzle %s (%.1f cells past the parapet), bore %.2f m above the platform, ray clear: %s, recoil %.1f cells -> cells hit %d'
           % (g0['at'], g0['muzzle'], g0['muzzle_past_parapet_cells'], g0['bore_above_stand_m'], g0['ray_blocked_at_cells'] is None, g0['recoil_cells'], g0['recoil_cells_hit']), fill=(30, 30, 30), font=f)
    img.save(os.path.join(HERE, 'sheet07_guns_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k != 'guns'} | {'guns': [{k: v for k, v in g.items() if k not in ('angles', 'tries')} for g in R['guns']]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
