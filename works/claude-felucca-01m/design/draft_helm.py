# 海鷗號 新圖紙 09（TASK-0024 步驟 11）：舵（艉柱舵）、舵柄、四爪錨 ⇒ masks/helm/{rudder,tiller}.vox.txt、helm_placement.json、verify_helm.json
#   出處：做法照星辰號 claude-baghlah-01m/design/draft_helm.py（舵、舵柄各一件整船框的子作品、模型 at ＝ pivot ＝ 鉸鏈點、舵 meta kind=rudder＋hinge／axis＋spin、
#         舵柄 kind=tiller＋spin_pivot／spin_axis 跟舵同一條軸）與杉心號的錨（共用件 kotoko-fusta-01m-anchor-grapnel、pivot ＝ 錨環頂、船殼登記 hawse）；量法自己寫。
#   用法：python -I -X utf8 draft_helm.py [--probe=gap=-1]
#   · 鉸鏈：船殼中線（y 80）每一層最後面那一格 ⇒ 底（z 1）與頂（艉柱頂）兩點連直線、往後挪 gap 格 ⇒ 舵的前緣與舵桿照這條線；艉柱是彎的（中段比直線前面）⇒ 中段會留一點縫。
#   · 量：舵與舵柄每 5° 一個角度（−35～35°）繞鉸鏈轉，每一格的格心＋八角不准落在船的實心格裡；舵柄外框跟砲的外框不准重疊；錨同樣量。
import sys, os, json, math, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
YC = 80
GRAPNEL = 'kotoko-fusta-01m-anchor-grapnel'          # 20×20×24、0.05 m；ring (9,9,23)、crown (9,9,0)、fluke-a／b


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)) for x, y, z, c in a}


def rot_about(p, o, u, ang):
    """點 p 繞過 o、方向 u（單位）的軸轉 ang 度（Rodrigues）。"""
    p, o, u = np.array(p, float), np.array(o, float), np.array(u, float)
    v = p - o
    t = math.radians(ang)
    return o + v * math.cos(t) + np.cross(u, v) * math.sin(t) + u * np.dot(u, v) * (1 - math.cos(t))


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    wl = plan['waterline']['z']
    hull = load('masks/hull/hull_01.vox.txt')
    ship = hull | load('masks/decks/deck_main.vox.txt') | load('masks/guns/post.vox.txt') | load('masks/magazine/chest.vox.txt') | \
        load('masks/masts/main.vox.txt') | load('masks/masts/fore.vox.txt') | load('masks/masts/tack_spar.vox.txt') | load('masks/deco/stem_head.vox.txt')
    gap = 1 + int(probe.get('gap', 0))
    # ── 鉸鏈線 ──
    aft = {z: min(x for (x, y, zz) in hull if y == YC and zz == z) for z in range(0, 22)}
    z0, z1 = 1, max(z for z in aft if z <= 21)
    # 艉柱往後凸（中段比兩頭的連線還後面）⇒ 鉸鏈取「每一層都在艉柱後面 gap 格以上」的支撐直線：斜率格點掃，截距取最緊的那一層，挑總縫最小的
    #   （v1 用兩頭連線，中段穿進艉柱 7 格）
    best = None
    for k in range(0, 1001):
        bb = -1.0 + k * 0.001
        a0 = min(aft[z] - gap - bb * (z + 0.5) for z in range(z0, z1 + 1))
        tot = sum(aft[z] - gap - (a0 + bb * (z + 0.5)) for z in range(z0, z1 + 1))
        if best is None or tot < best[0] - 1e-9:
            best = (tot, bb, a0)
    _, b, a0 = best

    def L(z):                                                  # 鉸鏈在高度 z（格心 z+0.5）的 x（連續座標：前緣格角）
        return a0 + b * (z + 0.5)
    axis = np.array([b, 0.0, 1.0])
    axis = axis / np.linalg.norm(axis)
    hinge = np.array([L(0) , YC + 0.5, 0.5])                  # 最低那層的鉸鏈點
    # ── 舵葉＋舵桿（色：水線下牛脂白 218、上面木色 173、舵桿 177）──
    rud = {}
    for z in range(z0, 25):
        lz = L(z)
        if z <= z1:
            chord = 7 if z <= wl else max(3, int(round(7 - (z - wl) * 4 / (z1 - wl))))
            for x in range(int(math.floor(lz - chord)), int(math.floor(lz))):
                if x + 0.5 < lz:
                    rud[(x, YC, z)] = 218 if z <= wl else 173
        if z >= z1 - 2:                                        # 舵桿：鉸鏈正後方 2 格 × 3 格寬
            for x in (int(math.floor(lz)) - 2, int(math.floor(lz)) - 1):
                for dy in (-1, 0, 1):
                    rud[(x, YC + dy, z)] = 177
    stock_top = max((k for k in rud if k[1] == YC), key=lambda k: (k[2], k[0]))
    # ── 舵柄：舵桿頂下一格、往船頭伸到 x 26，粗 1 格（靠舵桿那 4 格 2 格高）──
    zt = stock_top[2] - 1
    til = {}
    for x in range(stock_top[0] + 1, 27):
        til[(x, YC, zt)] = 177
        if x <= stock_top[0] + 4:
            til[(x, YC, zt + 1)] = 177
    tiller_end = (26, YC, zt)
    # ── 量：每 5° 一個角度 ──
    corners = [(a, bb, c) for a in (-0.5, 0.5) for bb in (-0.5, 0.5) for c in (-0.5, 0.5)] + [(0, 0, 0)]
    guns = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))['models']
    import draft_magazine as DM
    gboxes = [DM.box_of(g['at'], g['pivot'], g['work'], g['scale'], g['rotate'][2]) for g in guns]

    def sweep(cells):
        out = []
        for ang in range(-35, 36, 5):
            hit = 0
            hitbox = 0
            for (x, y, z) in cells:
                for (a, bb, c) in corners:
                    p = rot_about((x + 0.5 + a, y + 0.5 + bb, z + 0.5 + c), hinge, axis, ang)
                    k = tuple(int(math.floor(v)) for v in p)
                    if k in ship:
                        hit += 1
                        break
                p = rot_about((x + 0.5, y + 0.5, z + 0.5), hinge, axis, ang)
                if any(bx[0][0] <= p[0] <= bx[1][0] and bx[0][1] <= p[1] <= bx[1][1] and bx[0][2] <= p[2] <= bx[1][2] for bx in gboxes):
                    hitbox += 1
            out.append({'deg': ang, 'cells_hit_ship': hit, 'cells_in_gun_boxes': hitbox})
        return out
    gaps = {z: round(aft[z] - L(z), 2) for z in range(z0, z1 + 1)}
    R = {'probe': probe or None, 'hinge': [round(v, 3) for v in hinge], 'axis': [round(v, 4) for v in axis], 'slope_dx_per_dz': round(b, 3),
         'post_aft_x_by_z': {str(z): aft[z] for z in range(0, 22, 3)}, 'gap_post_to_hinge_cells': {'min': min(gaps.values()), 'max': max(gaps.values()), 'by_z': {str(z): gaps[z] for z in range(z0, z1 + 1, 4)}}}
    R['rudder'] = {'cells': len(rud), 'sweep': sweep(rud), 'stock_top': list(stock_top), 'below_wl_cells': sum(1 for k in rud if k[2] <= wl)}
    R['tiller'] = {'cells': len(til), 'sweep': sweep(til), 'end': list(tiller_end), 'end_above_stern_platform_m': round((zt - 10) * 0.1, 2)}
    # 舵柄端掃過的範圍（±35°）
    ends = [rot_about((tiller_end[0] + 0.5, tiller_end[1] + 0.5, tiller_end[2] + 0.5), hinge, axis, a) for a in (-35, 0, 35)]
    R['tiller']['end_at_-35_0_35'] = [[round(v, 2) for v in e] for e in ends]
    # ── 錨：左舷 x 108（SCH）、錨環頂在舷頂外、往外推到零碰撞 ──
    import wio
    gsrc = [tuple(r[:3]) for r in wio.export_list(GRAPNEL, None).tolist()]
    sc = 0.4
    rail = max((k for k in hull if k[0] == 108 and k[1] < YC - 2), key=lambda k: (k[2], -k[1]))
    out_y = min(k[1] for k in hull if k[0] == 108 and k[1] < YC)
    anc = None
    for off in np.arange(0.0, 12.0, 0.5):
        at = (108.5, out_y - off, float(rail[2] + 3))          # 錨環頂比舷頂高 0.2 m（綁在舷頂上掛下來）⇒ 錨冠在水線上；v1 環頂貼舷頂 ⇒ 錨冠 z 5.4 泡在水裡（SCH 的錨在水面上）
        hit = 0
        for (i, j, k) in gsrc:
            for (a, bb, c) in corners:
                p = (at[0] + (i + 0.5 + a - 9.5) * sc, at[1] + (j + 0.5 + bb - 9.5) * sc, at[2] + (k + 0.5 + c - 24) * sc)
                if tuple(int(math.floor(v)) for v in p) in ship:
                    hit += 1
                    break
        if hit == 0:
            anc = (at, off)
            break
    at, off = anc
    hawse = (rail[0], rail[1], rail[2])
    R['anchor'] = {'at': list(at), 'pivot': [9.5, 9.5, 24.0], 'scale': sc, 'out_of_hull_cells': off, 'crown_z': round(at[2] - 24 * sc, 2), 'hawse-P': list(hawse),
                   'height_m': round(24 * sc * 0.1, 2)}
    if probe:
        print(json.dumps({k: R[k] for k in ('probe', 'gap_post_to_hinge_cells')} | {'rudder_hits': [s['cells_hit_ship'] for s in R['rudder']['sweep']], 'tiller_hits': [s['cells_hit_ship'] for s in R['tiller']['sweep']]}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'helm'), exist_ok=True)
    for nm, cl in (('rudder', rud), ('tiller', til)):
        with open(os.path.join(HERE, 'masks', 'helm', nm + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 海鷗號 %s（draft_helm.py；整船的框）x,y,z,color —— at 0,0,0\n' % nm)
            f.write(''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(cl.items())))
    hz = {'hinge_x': round(float(hinge[0]), 3), 'hinge_y': round(float(hinge[1]), 3), 'hinge_z': round(float(hinge[2]), 3),
          'axis_x': round(float(axis[0]), 4), 'axis_y': 0.0, 'axis_z': round(float(axis[2]), 4)}
    spin = {'spin': 'rudder', 'spin_k': 35, 'spin_min': -35, 'spin_max': 35, 'spin_lag': 0.3}
    P = [round(float(v), 3) for v in hinge]
    out = {'rudder': {'work': 'claude-felucca-01m-rudder', 'title': '海鷗號 舵（艉柱舵：舵葉＋舵桿）', 'model': '舵', 'at': P, 'pivot': P,
                      'anchors': {'stock-top': list(stock_top)}, 'meta': dict({'kind': 'rudder', 'max_deg': 35, 'turn_axis': 'hinge', 'id': 'rudder-1'}, **hz, **spin)},
           'tiller': {'work': 'claude-felucca-01m-tiller', 'title': '海鷗號 舵柄', 'model': '舵柄', 'at': P, 'pivot': P,
                      'anchors': {'tiller-end': list(tiller_end)},
                      'meta': dict({'kind': 'tiller', 'spin_pivot_x': hz['hinge_x'], 'spin_pivot_y': hz['hinge_y'], 'spin_pivot_z': hz['hinge_z'],
                                    'spin_axis_x': hz['axis_x'], 'spin_axis_y': 0.0, 'spin_axis_z': hz['axis_z']}, **spin)},
           'anchor': {'name': '錨-P', 'host': 'claude-felucca-01m-deck-main', 'work': GRAPNEL, 'at': list(at), 'pivot': [9.5, 9.5, 24.0], 'scale': sc, 'rotate': [0, 0, 0],
                      'meta': {'kind': 'anchor', 'anchor': 'bower', 'id': 'anchor-1'}},
           'hull_anchors': {'hawse-P': list(hawse)}}
    with open(os.path.join(HERE, 'helm_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('masks/helm/rudder.vox.txt', 'masks/helm/tiller.vox.txt', 'helm_placement.json')}
    with open(os.path.join(HERE, 'verify_helm.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('rudder', 'tiller')} | {'rudder_hits': [(s['deg'], s['cells_hit_ship'], s['cells_in_gun_boxes']) for s in R['rudder']['sweep'] if s['cells_hit_ship'] or s['cells_in_gun_boxes']],
                                                                                  'tiller_hits': [(s['deg'], s['cells_hit_ship'], s['cells_in_gun_boxes']) for s in R['tiller']['sweep'] if s['cells_hit_ship'] or s['cells_in_gun_boxes']],
                                                                                  'rudder_cells': len(rud), 'tiller_cells': len(til), 'stock_top': stock_top, 'tiller_end_sweep': R['tiller']['end_at_-35_0_35']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
