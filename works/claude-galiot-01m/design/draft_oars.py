# 蠍子號 新圖紙 10（TASK-0023 步驟 13）：舷外槳架（apostis）＋槳栓、新做的槳元件（8.2 m、每支 3 人）、每舷 20 支的擺法
#   ⇒ masks/oars/apostis.vox.txt（槳架子作品）、masks/oars/oar.vox.txt（槳元件，0.05 m）、oars_placement.json、verify_oars.json、sheet10_oars_v1.png
#   出處：槳元件的做法照皇家號 apex-one-reale-01m/design/draft_oars.py（沿 +y、畫在「掃到一半」的姿勢、固定點 pivot／blade／seat、通用部件 0.05 m、模型 scale 0.5）；
#         擺法照海鷗號 claude-felucca-01m/design/draft_oars.py（at ＝ pivot、右舷原樣、左舷 mirror=y、rotate 的 x 角補到槳葉中心落在水面、左舷反號；槳栓在槳的船頭側 2 格）。
#         槳架的格子照步驟 3 的 layout.py build_apostis（圖紙 02 驗過；這一步才落格）。
#   改的地方：槳手照遊戲 40_crew.js oarCrew 模擬（seat 起沿槳柄往船裡每 6 格一個、standNear 6 格內、standZ 頭上 14 格）；繩（步驟 8）離槳多遠也量。
#   用法：python -I -X utf8 draft_oars.py [--sink=S05] [--drop=P20]   （反向對照：那一支往下沉 3 格 ⇒ 只有它報碰撞；不擺 ⇒ 那一舷少一支）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import layout as LY
import wio
import draft_guns as DG

sys.stdout.reconfigure(encoding='utf-8')
M5 = 0.05                                                     # 元件一格幾公尺
NP = lambda o: o.item() if hasattr(o, 'item') else str(o)     # numpy 數字 ⇒ JSON


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def rot_x(v, deg):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return np.stack([v[:, 0], v[:, 1] * c - v[:, 2] * s, v[:, 1] * s + v[:, 2] * c], axis=1)


def oar_cells(O):
    """槳元件：x 中心 3.5（寬 7）；y 0 ＝ 槳柄端、往 +y ＝ 槳葉；槳柄照 angle_deg 往外往下。回傳 (格, size, 固定點, 槳葉中心)。"""
    yi = int(round(O['inboard_m'] / M5))
    yo = int(round(O['outboard_m'] / M5))
    L = yi + yo
    tn = math.tan(math.radians(O['angle_deg']))
    bw = O['blade_w_m'] / M5
    zt = int(math.ceil(yo * tn + bw / 2 + 2))
    zc = lambda y: zt - (y - yi) * tn
    size = [7, L + 2, int(math.ceil(zc(0) + 4))]
    d0, d1 = O['loom_d_m']
    yb = L - int(round(O['blade_m'] / M5))
    cells = {}
    for y in range(0, L + 1):
        c = zc(y + 0.5)
        if y < yb:
            r = (d0 + (d1 - d0) * min(1.0, y / max(1, yb))) / M5 / 2
            for x in range(size[0]):
                for z in range(size[2]):
                    if (x + 0.5 - 3.5) ** 2 + (z + 0.5 - c) ** 2 <= max(r, 0.9) ** 2:
                        cells[(x, y, z)] = O['colors']['grip'] if y < O['grip_cells'] or abs(y - yi) <= 2 else O['colors']['loom']
        else:                                                  # 槳葉：一格厚（x 3）、寬 blade_w、往外漸寬一點
            hw = bw / 2 * (0.8 + 0.2 * (y - yb) / max(1, L - yb))
            for z in range(size[2]):
                if abs(z + 0.5 - c) <= hw:
                    cells[(3, y, z)] = O['colors']['blade']
    piv = (3, yi, int(math.floor(zc(yi + 0.5))))
    tip = (3, L, int(math.floor(zc(L + 0.5))))
    bmid = (3.5, L + 0.5 - O['blade_m'] / M5 / 2, zc(L + 0.5 - O['blade_m'] / M5 / 2))
    assert piv in cells and tip in cells, (piv, tip)
    return cells, size, {'pivot': list(piv), 'blade': list(tip)}, np.array(bmid), yi, L


def main():
    sink = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--sink=')), None)
    drop = next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--drop=')), None)
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    O = V(plan['oars_build'])
    surf = plan['waterline']['z'] + 1.0                        # 水面 ＝ DWL 那一格的頂
    K = LY.Ctx(plan)
    pieces, _, clipped = LY.assemble(K)
    ap = pieces['apostis']
    apostis = {(int(x), int(y), int(z)): int(ap[x, y, z]) for x, y, z in zip(*np.nonzero(ap))}
    P = K.P
    ah, rw = int(P['apostis']['half']), int(P['apostis']['rail_w'])
    th_dy = ah - rw + 1 + int(P['tholes'].get('dy_in_rail', 0))
    hull = load('masks/hull/hull_01.vox.txt')
    hole = load('masks/masts/deck_hole.vox.txt')
    deck = {k: c for k, c in load('masks/decks/deck_main.vox.txt').items() if k not in hole}
    ship = set(hull) | set(deck) | set(load('masks/decks/bow.vox.txt')) | set(load('masks/deco/spur.vox.txt')) | set(load('masks/deco/poop.vox.txt')) \
        | set(load('masks/masts/main.vox.txt')) | set(load('masks/guns/posts.vox.txt')) | set(load('masks/magazine/room.vox.txt')) | set(load('masks/helm/strap.vox.txt'))
    R = {'apostis': {'cells': len(apostis), 'overlap_ship': len(set(apostis) & ship), 'clipped_by_layout': clipped.get('apostis'),
                     'mirror_diff': sum(1 for (x, y, z), c in apostis.items() if apostis.get((x, 2 * YC - y, z)) != c)}}
    ship = ship | set(apostis)
    rud = set(load('masks/helm/rudder.vox.txt')) | set(load('masks/helm/tiller.vox.txt'))
    # 其他模型（砲、座、桶、燈、艙蓋、錨）的外框：槳不准穿過（Ship_Oars §9.10.2-5）
    boxes = []
    for f, key in (('guns_placement.json', 'models'), ('magazine_placement.json', 'models'), ('helm_placement.json', 'anchors')):
        for m in json.load(open(os.path.join(HERE, f), encoding='utf-8'))[key]:
            src_m = [tuple(r[:3]) for r in wio.export_list(m['work'], None).tolist()]
            if isinstance(m['scale'], list):
                lo = np.array([min(k[i] for k in src_m) for i in range(3)], float)
                hi = np.array([max(k[i] for k in src_m) + 1 for i in range(3)], float)
                b = list(np.array(m['at']) + lo * np.array(m['scale'])) + list(np.array(m['at']) + hi * np.array(m['scale']))
            else:
                b = DG.model_box(src_m, m['pivot'], m['scale'], m['at'], m['rotate'][2])
            boxes.append((m['name'], b))

    cells, size, anc, bmid, yi, Ltot = oar_cells(O)
    src = np.array(sorted(cells), float)
    PIV = np.array(anc['pivot'], float) + 0.5
    sc = O['scale']
    corners = [np.zeros(3)] + [np.array([dx, dy, dz]) * sc for dx in (-.5, .5) for dy in (-.5, .5) for dz in (-.5, .5)]
    G = np.zeros((K.SX, K.SY, 60), bool)
    for k in ship:
        if k[2] < 60:
            G[k] = True

    def standZ(x, y, z0, z1, head=14):
        for z in range(z1, z0 - 1, -1):
            if 1 <= z < 60 - head and G[x, y, z - 1] and not G[x, y, z:z + head].any():
                return z
        return -1
    taken = {}
    place, OR = [], {}
    occ_o = {}
    rope_ends = json.load(open(os.path.join(HERE, 'verify_rigging.json'), encoding='utf-8'))['rope_ends']
    RS = []
    for nm, e in rope_ends.items():
        a, b = np.array(e['from']), np.array(e['to'])
        RS.append((nm, np.array([a + t * (b - a) for t in np.linspace(0, 1, int(np.linalg.norm(b - a) * 2) + 2)])))
    from scipy.spatial import cKDTree
    bc_rel = (bmid - PIV) * sc
    ang0 = math.degrees(math.atan2(-bc_rel[2], bc_rel[1]))
    y_s = YC + th_dy + 0.5                                          # 槳柄靠在縱樑頂、槳栓那一欄的格心（右舷）；左舷照 y ↔ 2·YC＋1 − y 鏡過去

    def pose(xc, sg, sink_dz=0.0):
        x = xc + O['x_off']
        at = np.array([x + 0.5, y_s if sg > 0 else 2 * YC + 1 - y_s, K.rail_top(x) + 1 + O['loom_r_cells'] * sc - sink_dz])
        want = math.degrees(math.asin(min(1.0, (at[2] - surf) / np.linalg.norm(bc_rel[1:]))))
        return x, at, -(want - ang0)

    def tw(p, at, rx, sg):
        q = rot_x(((np.atleast_2d(p) - PIV) * sc), rx)
        if sg < 0:
            q[:, 1] = -q[:, 1]
        return q + at
    # 槳手（遊戲 40_crew.js oarCrew）：從元件的固定點 seat 起、往船裡（pivot − blade 的平面方向）每 6 格一個，standNear 6 格內、z 在 [min(seat,pivot)−14, max+2]。
    #   seat 是元件的固定點 ⇒ 同一件元件每支槳一樣 ⇒ 分兩件：一般的（seat 在 dy seat_dy、3 人）與船尾窄的那幾張（甲板內緣半寬 < seat_dy ⇒ seat 在 dy seat_dy_aft、站得下幾個給幾個）
    cor = int(P['corsia']['half']) + 1
    groups = {}
    for xc in K.benches:
        aft = K.hw_deck(xc + O['x_off']) < O['seat_dy']
        groups[xc] = 'aft' if aft else 'main'
    comp = {}
    for g, sdy in (('main', O['seat_dy']), ('aft', O['seat_dy_aft'])):
        ref = next((xc for xc in K.benches if groups[xc] == g), None)
        if ref is None:
            continue
        x, at, rx = pose(ref, 1)
        sw = np.array([x + 0.5, YC + 0.5 + sdy, K.deck_top(x, sdy) + 0.5])
        sl = rot_x(((sw - at) / sc)[None, :], -rx)[0] + PIV
        comp[g] = {'work': O['work'] + ('' if g == 'main' else '-aft'), 'seat': [int(math.floor(v)) for v in sl], 'seat_dy': sdy,
                   'rowers': min(O['rowers'], (sdy - cor) // 6 + 1), 'ref_bench': ref}
    for side, sg in (('S', 1), ('P', -1)):
        for i, xc in enumerate(K.benches, 1):
            nm = 'oar-%s%02d' % (side, i)
            if drop == '%s%02d' % (side, i):
                continue
            x, at, rx = pose(xc, sg, 3.0 if sink == '%s%02d' % (side, i) else 0.0)
            xt = xc + int(P['tholes']['dx'][0])
            cg = comp[groups[xc]]
            pts = tw(src + 0.5, at, rx, sg)
            hit_cells = set()
            for off in corners:
                for kk in map(tuple, np.floor(pts + off).astype(int)):
                    if kk in ship or kk in rud:
                        hit_cells.add(kk)
            box_hits = [n for n, b in boxes if ((pts >= np.array(b[:3])) & (pts <= np.array(b[3:]))).all(axis=1).any()]
            bw = tw(bmid, at, rx, sg)[0]
            seat_w = tw(np.array(cg['seat'], float) + 0.5, at, rx, sg)[0]
            tipw = tw(np.array(anc['blade'], float) + 0.5, at, rx, sg)[0]
            d = np.array([at[0] - tipw[0], at[1] - tipw[1]])
            d = d / np.linalg.norm(d)
            z0 = int(math.floor(min(seat_w[2], at[2]))) - 14
            z1 = int(math.floor(max(seat_w[2], at[2]))) + 2
            n_i = cg['rowers']
            rowers = []
            for r_i in range(n_i):
                sx, sy = int(math.floor(seat_w[0] + d[0] * 6 * r_i)), int(math.floor(seat_w[1] + d[1] * 6 * r_i))
                got = None
                for rr in range(0, 7):
                    for ddy in range(-rr, rr + 1):
                        for ddx in range(-rr, rr + 1):
                            if got or max(abs(ddx), abs(ddy)) != rr or taken.get((sx + ddx, sy + ddy)):
                                continue
                            z = standZ(sx + ddx, sy + ddy, z0, z1)
                            if z >= 0 and not any(b[0] - 1 <= sx + ddx <= b[3] + 1 and b[1] - 1 <= sy + ddy <= b[4] + 1 and b[2] - 3 <= z <= b[5] for _, b in boxes):
                                got = (sx + ddx, sy + ddy, z)
                    if got:
                        break
                if got:
                    taken[got[:2]] = 1
                    rowers.append({'at': list(got), 'moved': max(abs(got[0] - sx), abs(got[1] - sy)), 'on': 'deck' if (got[0], got[1], got[2] - 1) in deck else 'other'})
            near = sum(1 for k in ship if abs(k[0] - at[0]) <= 8 and abs(k[1] - at[1]) <= 8 and abs(k[2] - at[2]) <= 8)
            tree = cKDTree(pts)
            rope_d = {rn: round(float(tree.query(rp)[0].min()), 2) for rn, rp in RS}
            for kk in set(map(tuple, np.floor(pts).astype(int))):
                occ_o.setdefault(kk, set()).add(nm)
            OR[nm] = {'bench_x': xc, 'component': cg['work'], 'at': [round(float(v), 3) for v in at], 'rot_x': round(rx, 3), 'hits': len(hit_cells), 'hit_cells': sorted(hit_cells)[:3], 'model_hits': box_hits,
                      'blade_center_above_water_m': round(float(bw[2] - surf) * 0.1, 3), 'thole': [xt, YC + sg * th_dy], 'thole_gap_cells': round(abs((xt + 0.5) - at[0]) - O['loom_r_cells'] * sc - 0.5, 2),
                      'seat_world': [round(float(v), 2) for v in seat_w], 'rowers': rowers, 'rowers_meta': n_i, 'hull_cells_near_pivot': near,
                      'rope_min_cells': min(rope_d.values()), 'rope_min_name': min(rope_d, key=rope_d.get)}
            place.append({'name': nm, 'work': cg['work'], 'at': [round(float(v), 3) for v in at], 'pivot': [round(float(v), 3) for v in PIV], 'scale': sc,
                          'rotate': [round(rx if sg > 0 else -rx, 3), 0, 0], 'mirror': 'y' if sg < 0 else '',
                          'meta': {'kind': 'oar', 'rowers': n_i, 'side': side, 'stroke_deg': O['stroke_deg'], 'dip_deg': O['dip_deg'], 'id': 'oar-%d' % (2 * i - (1 if side == 'S' else 0))}})
    anc['seat'] = comp['main']['seat']
    R['components'] = comp
    R['component'] = {'size': size, 'cells': len(cells), 'anchors': anc, 'length_m': round(Ltot * M5, 2), 'inboard_m': round(yi * M5, 2), 'outboard_m': round((Ltot - yi) * M5, 2)}
    R['per_side'] = {s: sum(1 for k in OR if k[4] == s) for s in 'SP'}
    R['total_hits'] = sum(o['hits'] for o in OR.values())
    R['model_hits'] = sum(len(o['model_hits']) for o in OR.values())
    R['oar_oar_shared_cells'] = sum(1 for v in occ_o.values() if len(v) > 1)
    R['rowers'] = {'want': sum(o['rowers_meta'] for o in OR.values()), 'per_oar': {str(n): sum(1 for o in OR.values() if o['rowers_meta'] == n) for n in range(1, O['rowers'] + 1)}, 'placed': sum(len(o['rowers']) for o in OR.values()), 'on_deck': sum(1 for o in OR.values() for r in o['rowers'] if r['on'] == 'deck'),
                   'moved_max': max((r['moved'] for o in OR.values() for r in o['rowers']), default=None)}
    R['blade_above_water_m_range'] = [min(o['blade_center_above_water_m'] for o in OR.values()), max(o['blade_center_above_water_m'] for o in OR.values())]
    R['rot_x_range'] = [min(o['rot_x'] for o in OR.values()), max(o['rot_x'] for o in OR.values())]
    R['thole_gap_min_cells'] = min(o['thole_gap_cells'] for o in OR.values())
    R['hang_min_cells_near_pivot'] = min(o['hull_cells_near_pivot'] for o in OR.values())
    R['rope_min_cells'] = min(o['rope_min_cells'] for o in OR.values())
    R['problems'] = (R['total_hits'] + R['model_hits'] + R['oar_oar_shared_cells'] + (R['rowers']['placed'] != R['rowers']['want']) + R['apostis']['overlap_ship'] + R['apostis']['mirror_diff']
                     + (R['per_side']['S'] != R['per_side']['P']) + (R['hang_min_cells_near_pivot'] == 0) + (R['rope_min_cells'] < 1.0) + (R['thole_gap_min_cells'] < 0.5)
                     + sum(1 for o in OR.values() if abs(o['blade_center_above_water_m']) > 0.05))
    if sink or drop:
        print(json.dumps({'sink': sink, 'drop': drop, 'per_side': R['per_side'], 'problems': R['problems'], 'hits': {k: v['hits'] for k, v in OR.items() if v['hits']},
                          'total_hits': R['total_hits'], 'rowers': R['rowers']}, ensure_ascii=False, default=NP))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'oars'), exist_ok=True)
    with open(os.path.join(HERE, 'masks', 'oars', 'apostis.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蠍子號 舷外槳架與槳栓（draft_oars.py ← layout.py build_apostis；子作品、船殼的框）x,y,z,color —— at 0,0,0\n')
        f.write(''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(apostis.items())))
    with open(os.path.join(HERE, 'masks', 'oars', 'oar.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蠍子號 槳（通用部件，draft_oars.py）x,y,z,color —— 0.05 m、框 %s、at 0,0,0\n' % size)
        f.write(''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(cells.items())))
    with open(os.path.join(HERE, 'oars_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'components': {c['work']: {'title': '蠍子號 槳（8.2 m；%s、seat 在 dy %d、%d 人；通用部件 0.05 m）' % ('一般' if g == 'main' else '船尾窄的那幾張座', c['seat_dy'], c['rowers']),
                                              'anchors': dict(anc, seat=c['seat'])} for g, c in comp.items()}, 'component_size': size,
                   'host': 'claude-galiot-01m-apostis', 'models': place}, f, ensure_ascii=False, indent=1, default=NP)
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('masks/oars/apostis.vox.txt', 'masks/oars/oar.vox.txt', 'oars_placement.json')}
    with open(os.path.join(HERE, 'verify_oars.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(R, oars=OR), f, ensure_ascii=False, indent=1, default=NP)
    # 圖紙 10：右舷第 10 支槳的橫剖面（x ＝ 那支槳）＋平面（槳、槳栓、槳手）
    s_ = 6
    o = OR['oar-S10']
    sgn = 1
    xo = int(o['at'][0])
    img = Image.new('RGB', (130 * s_ + 80, 70 * s_ + 140), (246, 242, 230))
    dr = ImageDraw.Draw(img)
    f_ = ImageFont.load_default()
    dr.text((20, 8), '%s - new sheet 10: oar (%.1f m, %d rowers), apostis, section at x %d (oar-S10)' % (plan['title_en'], Ltot * M5, O['rowers'], xo), fill=(20, 20, 40), font=f_)
    for (x, y, z) in ship:
        if x == xo and YC - 10 <= y < YC + 120 and z < 70:
            dr.rectangle([40 + (y - YC + 10) * s_, 40 + (69 - z) * s_, 40 + (y - YC + 10) * s_ + s_ - 1, 40 + (69 - z) * s_ + s_ - 1], fill=(120, 120, 120))
    pts = tw(src + 0.5, np.array(o['at']), o['rot_x'], 1)
    for p in pts:
        dr.point((40 + (p[1] - YC + 10) * s_, 40 + (69 - p[2]) * s_), fill=(150, 90, 30))
    for r in o['rowers']:
        dr.rectangle([40 + (r['at'][1] - YC + 10) * s_, 40 + (69 - r['at'][2] - 14) * s_, 40 + (r['at'][1] - YC + 10) * s_ + s_, 40 + (69 - r['at'][2]) * s_], outline=(30, 120, 30), width=2)
    dr.line([40, 40 + (69 - surf) * s_, 40 + 130 * s_, 40 + (69 - surf) * s_], fill=(60, 120, 220), width=1)
    dr.text((40, 70 * s_ + 60), 'oars %s, rowers %s, hits %d, blade above water %s m, rot_x %s' % (R['per_side'], R['rowers'], R['total_hits'], R['blade_above_water_m_range'], R['rot_x_range']), fill=(30, 30, 30), font=f_)
    img.save(os.path.join(HERE, 'sheet10_oars_v1.png'))
    print(json.dumps({k: v for k, v in R.items()}, ensure_ascii=False, default=NP))
    for k, v in OR.items():
        if v['hits'] or v['model_hits'] or len(v['rowers']) != v['rowers_meta']:
            print(k, v)


if __name__ == '__main__':
    main()
