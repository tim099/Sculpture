# 蠍子號 新圖紙 09（TASK-0023 步驟 11）：舵（艉柱舵）、舵柄、兩隻四爪錨 ⇒ masks/helm/{rudder,tiller}.vox.txt、helm_placement.json、verify_helm.json、sheet09_helm_v1.png
#   出處：海鷗號 claude-felucca-01m/design/draft_helm.py（舵、舵柄各一件整船框的子作品、模型 at ＝ pivot ＝ 鉸鏈點、舵 meta kind=rudder＋hinge／axis＋spin、
#         舵柄 kind=tiller＋spin_pivot／spin_axis 跟舵同一條軸；鉸鏈取「每一層都在艉柱後面 gap 格以上」的支撐直線）；錨的擺法照越嶺號 kotoko-fusta-01m-bow
#         （共用件 kotoko-fusta-01m-anchor-grapnel 掛在船首平台兩舷、pivot ＝ 錨環頂 (9.5,9.5,24)、rotate ±45）。
#   改的地方：舵柄長度照「舵柄掃 ±35° 不碰艉燈桿、不碰船尾篷」量出來（艉台只有 0.9 m 寬、艉燈桿立在艉柱頭前面 ⇒ 舵柄只能從艉柱頭上方伸到燈桿後面）；
#            錨兩隻（FUR p.80：galeotta 只有 2 個錨），錨環頂掛在船首平台胸牆頂外緣、往外推到零碰撞；船殼登記 hawse-S／P。
#   用法：python -I -X utf8 draft_helm.py [--probe=gap=-1] [--probe=tiller_x=2]
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio
import draft_guns as DG

sys.stdout.reconfigure(encoding='utf-8')
CORNERS = [(a, b, c) for a in (-0.5, 0.5) for b in (-0.5, 0.5) for c in (-0.5, 0.5)] + [(0, 0, 0)]


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def rot_about(p, o, u, ang):
    """點 p 繞過 o、方向 u（單位）的軸轉 ang 度（Rodrigues）。"""
    p, o, u = np.array(p, float), np.array(o, float), np.array(u, float)
    v = p - o
    t = math.radians(ang)
    return o + v * math.cos(t) + np.cross(u, v) * math.sin(t) + u * np.dot(u, v) * (1 - math.cos(t))


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    wl = int(plan['waterline']['z'])
    HP = V(plan['helm'])
    hull = load('masks/hull/hull_01.vox.txt')
    hole = load('masks/masts/deck_hole.vox.txt')
    deck = {k for k in load('masks/decks/deck_main.vox.txt') if k not in hole}
    bow = set(load('masks/decks/bow.vox.txt'))
    ship = set(hull) | deck | bow | set(load('masks/deco/spur.vox.txt')) | set(load('masks/deco/poop.vox.txt')) \
        | set(load('masks/masts/main.vox.txt')) | set(load('masks/guns/posts.vox.txt')) | set(load('masks/magazine/room.vox.txt'))
    awning = set(load('masks/deco/awning.vox.txt'))
    solid = ship | awning                                        # 篷是外部模型（deco），舵柄掃到它一樣算碰
    gap = HP['gap'] + int(probe.get('gap', 0))
    # ── 鉸鏈線：艉柱中線（y YC）每一層最後面那一格 ⇒ 每一層都在它後面 gap 格以上的支撐直線、總縫最小 ──
    aft = {}
    for (x, y, z) in hull:
        if y == YC:
            aft[z] = min(aft.get(z, 999), x)
    z0, z1 = HP['z'][0], HP['z'][1]
    zf = HP.get('fit_z0', z0) + int(probe.get('fit_z0', 0))        # 鉸鏈線只照 z ≥ fit_z0 的艉柱擬合（上段貼著艉柱、舵頭才掛得到船尾：遊戲 anchorNear 8 格）
    best = None
    for k in range(0, 2001):
        bb = -2.0 + k * 0.001
        a0 = min(aft[z] - gap - bb * (z + 0.5) for z in range(z0, z1 + 1))
        tot = sum(aft[z] - gap - (a0 + bb * (z + 0.5)) for z in range(zf, z1 + 1))
        if best is None or tot < best[0] - 1e-9:
            best = (tot, bb, a0)
    _, b, a0 = best

    def L(z):
        return a0 + b * (z + 0.5)
    axis = np.array([b, 0.0, 1.0])
    axis = axis / np.linalg.norm(axis)
    hinge = np.array([L(z0 - 1) + b * 0.5, YC + 0.5, float(z0)])   # 最低那層底面的鉸鏈點
    # ── 舵葉＋舵桿（色：水線下牛脂白 218、上面木色 173、舵桿 177）──
    C = HP['colors']
    rud = {}
    for z in range(z0, HP['stock_top'] + 1):
        lz = L(z)
        if z <= z1:
            ch = HP['chord'] if z <= wl else max(HP['chord_top'], int(round(HP['chord'] - (z - wl) * (HP['chord'] - HP['chord_top']) / max(1, z1 - wl))))
            for x in range(int(math.floor(lz - ch)), int(math.floor(lz))):
                if x + 0.5 < lz:
                    rud[(x, YC, z)] = C['below'] if z <= wl else C['above']
        if z >= z1 - 3:                                        # 舵頭：鉸鏈正後方 2 格 × 3 格寬
            for x in (int(math.floor(lz)) - 2, int(math.floor(lz)) - 1):
                for dy in (-1, 0, 1):
                    rud[(x, YC + dy, z)] = C['stock']
    stock_top = max((k for k in rud if k[1] == YC), key=lambda k: (k[2], k[0]))
    # ── 舵柄：舵頭頂那一層、往船頭伸到 tiller_x（從舵頭後面往前；靠舵頭 3 格兩格高）──
    zt = stock_top[2]
    tx = HP['tiller_x'] + int(probe.get('tiller_x', 0))
    til = {}
    for x in range(stock_top[0] + 1, tx + 1):
        til[(x, YC, zt)] = C['stock']
        if x <= stock_top[0] + 3:
            til[(x, YC, zt - 1)] = C['stock']
    til = {k: c for k, c in til.items() if k not in rud}
    tiller_end = (tx, YC, zt)
    # ── 舵頭的鐵箍（gudgeon 臂）：舵頭在艉柱頭後面 0.8 m，遊戲照 stock-top 旁 8 格內的船尾格當「腳」（10_ship.js anchorNear）⇒ 從艉柱頭往後伸一條 3 格寬、2 格高的鐵臂，
    #    末端停在鉸鏈前 strap_clear 格（舵頭都在鉸鏈後面 ⇒ 轉 ±35° 掃不到）；落在艉台子作品（船的一部分，舵被打掉它還在）──
    SP = HP['strap']
    strap = {}
    xs0 = int(math.floor(L(SP['z'][1]) + SP['clear']))
    for z in range(SP['z'][0], SP['z'][1] + 1):
        for x in range(xs0, aft[z] if z in aft else aft[max(aft)]):
            for dy in (-1, 0, 1):
                if (x, YC + dy, z) not in ship:
                    strap[(x, YC + dy, z)] = SP['color']
    ship = ship | set(strap)
    solid = solid | set(strap)

    lantern = json.load(open(os.path.join(HERE, 'magazine_placement.json'), encoding='utf-8'))['models']
    lan = next(m for m in lantern if m['meta'].get('kind') == 'light')
    lsrc = [tuple(r[:3]) for r in wio.export_list(lan['work'], None).tolist()]
    lbox = DG.model_box(lsrc, lan['pivot'], lan['scale'], lan['at'], 0)
    GP = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))['models']

    def sweep(cells, against):
        out = []
        for ang in range(-35, 36, 5):
            hit = inbox = 0
            first = []
            for (x, y, z) in cells:
                for (a, bb, c) in CORNERS:
                    p = rot_about((x + 0.5 + a, y + 0.5 + bb, z + 0.5 + c), hinge, axis, ang)
                    q = tuple(int(math.floor(v)) for v in p)
                    if q in against:
                        hit += 1
                        if len(first) < 4:
                            first.append([[x, y, z], list(q), 'awning' if q in awning else 'ship'])
                        break
                p = rot_about((x + 0.5, y + 0.5, z + 0.5), hinge, axis, ang)
                if lbox[0] <= p[0] <= lbox[3] and lbox[1] <= p[1] <= lbox[4] and lbox[2] <= p[2] <= lbox[5]:
                    inbox += 1
            out.append({'deg': ang, 'cells_hit': hit, 'cells_in_lantern_box': inbox, 'first_hits': first})
        return out
    gaps = {z: round(aft[z] - L(z), 2) for z in range(z0, z1 + 1)}
    R = {'probe': probe or None, 'hinge': [round(float(v), 3) for v in hinge], 'axis': [round(float(v), 4) for v in axis], 'rake_deg': round(math.degrees(math.atan2(-b, 1)), 1),
         'post_aft_x_by_z': {str(z): aft[z] for z in range(z0, z1 + 1, 4)},
         'gap_post_to_hinge_cells': {'min': min(gaps.values()), 'max': max(gaps.values()), 'by_z': {str(z): gaps[z] for z in range(z0, z1 + 1, 4)}}}
    R['rudder'] = {'cells': len(rud), 'sweep': sweep(rud, solid), 'stock_top': list(stock_top), 'below_wl_cells': sum(1 for k in rud if k[2] <= wl),
                   'length_along_axis_m': round((stock_top[2] - z0) / float(axis[2]) * 0.1, 1),
                   'chord_below_wl_m': HP['chord'] * 0.1}
    st = stock_top
    near = [k for k in ship if abs(k[0] - st[0]) <= 8 and abs(k[1] - st[1]) <= 8 and abs(k[2] - st[2]) <= 8]
    R['stock_top_foot'] = {'game_anchorNear_r8_found': bool(near), 'nearest': list(min(near, key=lambda k: (k[0] - st[0]) ** 2 + (k[1] - st[1]) ** 2 + (k[2] - st[2]) ** 2)) if near else None,
                           'strap_cells': len(strap), 'strap_x': [min(k[0] for k in strap), max(k[0] for k in strap)] if strap else None}
    R['tiller'] = {'cells': len(til), 'sweep': sweep(til, solid), 'end': list(tiller_end),
                   'length_from_axis_m': round((tx + 0.5 - (L(zt) )) * 0.1, 2), 'end_above_poop_stand_m': round((zt - 29) * 0.1, 2)}
    ends = [rot_about((tiller_end[0] + 0.5, tiller_end[1] + 0.5, tiller_end[2] + 0.5), hinge, axis, a) for a in (-35, 0, 35)]
    R['tiller']['end_at_-35_0_35'] = [[round(float(v), 2) for v in e] for e in ends]
    R['lantern_box'] = [round(v, 2) for v in lbox]

    # ── 錨：兩隻四爪錨，錨環頂掛在船首平台胸牆頂外緣、往舷外推到零碰撞（越嶺號的擺法：rotate ±45、pivot 錨環頂）──
    AN = HP['anchor']
    gsrc = [tuple(r[:3]) for r in wio.export_list(AN['work'], None).tolist()]
    sc = AN['scale']
    anchors_out, hawse = [], {}
    R['anchors'] = []
    for side, sd, rot in ((1, 'S', 45), (-1, 'P', -45)):
        x = AN['x']
        col = [k for k in ship if k[0] == x and (k[1] - YC) * side > 0]
        top = max(k[2] for k in col)
        rail = max((k for k in col if k[2] == top), key=lambda k: abs(k[1] - YC))
        found = None
        for off in np.arange(1.0, 20.0, 0.5):
            at = (x + 0.5, rail[1] + 0.5 + side * off, float(top + 1 + AN['ring_above']))
            hit = 0
            pts = []
            for (i, j, k) in gsrc:
                for (a, bb, c) in CORNERS:
                    p = DG.world((i + 0.5 + a, j + 0.5 + bb, k + 0.5 + c), AN['pivot'], sc, at, rot)
                    if (int(math.floor(p[0])), int(math.floor(p[1])), int(math.floor(p[2]))) in ship:
                        hit += 1
                        break
            if hit == 0:
                found = (at, off)
                break
        at, off = found
        P = np.array([DG.world((i + 0.5, j + 0.5, k + 0.5), AN['pivot'], sc, at, rot) for (i, j, k) in gsrc])
        # 錨鏈孔 hawse：錨環頂往船裡那一欄、胸牆頂那一格（鐵鏈從這裡出去）
        hz = (rail[0], rail[1], rail[2])
        hawse['hawse-' + sd] = list(hz)
        nm = '錨-' + sd
        anchors_out.append({'name': nm, 'host': 'bow', 'work': AN['work'], 'at': [round(float(v), 3) for v in at], 'pivot': AN['pivot'], 'scale': sc, 'rotate': [0, 0, rot],
                            'meta': {'kind': 'anchor', 'anchor': 'bower', 'id': 'anchor-%d' % (1 if sd == 'S' else 2)}})
        R['anchors'].append({'name': nm, 'at': [round(float(v), 3) for v in at], 'off_rail_cells': float(off), 'rail_cell': list(rail), 'crown_z': round(float(P[:, 2].min()), 2),
                             'crown_above_wl_m': round((float(P[:, 2].min()) - (wl + 1)) * 0.1, 2), 'height_m': round(float(P[:, 2].max() - P[:, 2].min()) * 0.1, 2),
                             'nearest_ship_cells': None})
    # 吊錨木（verifier11：錨環在胸牆外 3.5 格、沒有東西掛著 ⇒ 看起來懸空）：從胸牆頂外緣往舷外伸一根 1 格見方的木頭到錨環正上方，錨環貼在它底下；落在船首平台子作品
    cat = {}
    for a in R['anchors']:
        sg_ = 1 if a['at'][1] > YC else -1
        y0_, y1_ = a['rail_cell'][1] + sg_, int(math.floor(a['at'][1]))
        zc_ = int(round(a['at'][2]))                                  # 吊錨木躺在胸牆頂上（胸牆頂＋1），錨環頂貼在它底面下 0.02 格
        for y in range(min(y0_, y1_), max(y0_, y1_) + 1):
            cat[(a['rail_cell'][0], y, zc_)] = AN['cathead_color']
        cat[(a['rail_cell'][0], a['rail_cell'][1], zc_)] = AN['cathead_color'] if (a['rail_cell'][0], a['rail_cell'][1], zc_) not in ship else None
    cat = {k: c for k, c in cat.items() if c is not None and k not in ship}
    R['cathead'] = {'cells': len(cat), 'touches_rail': all(any((k[0], k[1] + d, k[2] + e) in ship for d in (-1, 0, 1) for e in (-1, 0)) for k in cat if abs(k[1] - YC) == min(abs(q[1] - YC) for q in cat)),
                    'anchor_hits': 0}
    for a, m in zip(R['anchors'], anchors_out):
        for (i, j, k) in gsrc:
            for (aa, bb, cc) in CORNERS:
                p = DG.world((i + 0.5 + aa, j + 0.5 + bb, k + 0.5 + cc), m['pivot'], sc, m['at'], m['rotate'][2])
                if (int(math.floor(p[0])), int(math.floor(p[1])), int(math.floor(p[2]))) in cat:
                    R['cathead']['anchor_hits'] += 1
                    break
    from scipy.spatial import cKDTree
    tree = cKDTree(np.array(sorted(ship), float) + 0.5)
    for a, m in zip(R['anchors'], anchors_out):
        P = np.array([DG.world((i + 0.5, j + 0.5, k + 0.5), m['pivot'], sc, m['at'], m['rotate'][2]) for (i, j, k) in gsrc])
        a['nearest_ship_cells'] = round(float(tree.query(P)[0].min()), 2)
    R['problems'] = (sum(s['cells_hit'] + s['cells_in_lantern_box'] for s in R['rudder']['sweep']) + sum(s['cells_hit'] + s['cells_in_lantern_box'] for s in R['tiller']['sweep'])
                     + sum(1 for a in R['anchors'] if a['crown_above_wl_m'] < 0) + (R['gap_post_to_hinge_cells']['min'] < gap - 1e-6)
                     + (not R['stock_top_foot']['game_anchorNear_r8_found']) + R['cathead']['anchor_hits'] + (not R['cathead']['touches_rail']))
    if probe:
        print(json.dumps({'probe': probe, 'problems': R['problems'], 'gap': R['gap_post_to_hinge_cells'], 'rudder_hits': [(s['deg'], s['cells_hit'], s['first_hits']) for s in R['rudder']['sweep'] if s['cells_hit']][:2],
                          'tiller_hits': [(s['deg'], s['cells_hit'], s['cells_in_lantern_box']) for s in R['tiller']['sweep'] if s['cells_hit'] or s['cells_in_lantern_box']],
                          'tiller': {k: R['tiller'][k] for k in ('end', 'length_from_axis_m')}, 'foot': R['stock_top_foot'], 'cathead': R.get('cathead'), 'anchors': R['anchors']}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'helm'), exist_ok=True)
    for nm, cl in (('rudder', rud), ('tiller', til), ('strap', strap), ('cathead', cat)):
        with open(os.path.join(HERE, 'masks', 'helm', nm + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 蠍子號 %s（draft_helm.py；船殼的框）x,y,z,color —— at 0,0,0\n' % nm)
            f.write(''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(cl.items())))
    hz = {'hinge_x': round(float(hinge[0]), 3), 'hinge_y': round(float(hinge[1]), 3), 'hinge_z': round(float(hinge[2]), 3),
          'axis_x': round(float(axis[0]), 4), 'axis_y': 0.0, 'axis_z': round(float(axis[2]), 4)}
    spin = {'spin': 'rudder', 'spin_k': 35, 'spin_min': -35, 'spin_max': 35, 'spin_lag': 0.3}
    P = [round(float(v), 3) for v in hinge]
    out = {'rudder': {'work': 'claude-galiot-01m-rudder', 'title': '蠍子號 舵（艉柱舵：舵葉＋舵頭）', 'model': '舵', 'at': P, 'pivot': P,
                      'anchors': {'stock-top': list(stock_top)}, 'meta': dict({'kind': 'rudder', 'max_deg': 35, 'turn_axis': 'hinge', 'id': 'rudder-1'}, **hz, **spin)},
           'tiller': {'work': 'claude-galiot-01m-tiller', 'title': '蠍子號 舵柄', 'model': '舵柄', 'at': P, 'pivot': P,
                      'anchors': {'tiller-end': list(tiller_end)},
                      'meta': dict({'kind': 'tiller', 'id': 'tiller-1', 'spin_pivot_x': hz['hinge_x'], 'spin_pivot_y': hz['hinge_y'], 'spin_pivot_z': hz['hinge_z'],
                                    'spin_axis_x': hz['axis_x'], 'spin_axis_y': 0.0, 'spin_axis_z': hz['axis_z']}, **spin)},
           'anchors': anchors_out, 'hosts': {'bow': 'claude-galiot-01m-bow', 'poop': 'claude-galiot-01m-poop'}, 'hull_anchors': hawse,
           'strap': {'host': 'poop', 'cells': len(strap)}, 'cathead': {'host': 'bow', 'cells': len(cat)}}
    with open(os.path.join(HERE, 'helm_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('masks/helm/rudder.vox.txt', 'masks/helm/tiller.vox.txt', 'masks/helm/strap.vox.txt', 'masks/helm/cathead.vox.txt', 'helm_placement.json')}
    with open(os.path.join(HERE, 'verify_helm.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    # 圖紙 09：船尾中線剖面（舵、舵柄、艉柱、艉台、燈桿、篷、鉸鏈線）＋船首平面（兩隻錨）
    s_ = 8
    img = Image.new('RGB', (64 * s_ + 80, 70 * s_ + 120), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((20, 8), '%s - new sheet 09: rudder (rake %.1f deg), tiller, stern centreline (y %d)' % (plan['title_en'], R['rake_deg'], YC), fill=(20, 20, 40), font=f)
    for z in range(0, 66):
        for x in range(0, 64):
            k = (x, YC, z)
            c = (30, 30, 30) if k in strap else (90, 90, 90) if k in ship else (200, 60, 60) if k in awning else (40, 120, 200) if k in rud else (200, 140, 30) if k in til else None
            if c:
                d.rectangle([40 + x * s_, 40 + (66 - z) * s_, 40 + x * s_ + s_ - 1, 40 + (66 - z) * s_ + s_ - 1], fill=c)
    d.line([40 + L(z0) * s_, 40 + (66 - z0) * s_, 40 + L(zt) * s_, 40 + (66 - zt) * s_], fill=(0, 0, 0), width=1)
    d.line([40, 40 + (66 - wl - 1) * s_, 40 + 64 * s_, 40 + (66 - wl - 1) * s_], fill=(60, 120, 220), width=1)
    d.rectangle([40 + lbox[0] * s_, 40 + (66 - lbox[5]) * s_, 40 + lbox[3] * s_, 40 + (66 - lbox[2]) * s_], outline=(220, 160, 0), width=1)
    d.text((40, 66 * s_ + 60), 'hinge %s axis %s; tiller end %s (%.2f m from the axis); anchors %s' % (R['hinge'], R['axis'], tiller_end, R['tiller']['length_from_axis_m'],
                                                                                                    [(a['name'], a['at'], a['crown_z']) for a in R['anchors']]), fill=(30, 30, 30), font=f)
    img.save(os.path.join(HERE, 'sheet09_helm_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('rudder', 'tiller')} | {
        'rudder_hits': [(s['deg'], s['cells_hit'], s['cells_in_lantern_box']) for s in R['rudder']['sweep'] if s['cells_hit'] or s['cells_in_lantern_box']],
        'tiller_hits': [(s['deg'], s['cells_hit'], s['cells_in_lantern_box']) for s in R['tiller']['sweep'] if s['cells_hit'] or s['cells_in_lantern_box']],
        'rudder': {k: v for k, v in R['rudder'].items() if k != 'sweep'}, 'tiller': {k: v for k, v in R['tiller'].items() if k != 'sweep'}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
