# 出處：kaguya-guineaman-01m/design/draft_rudder_anchor.py
# 沙船 步驟 11（TASK-1313）：
#   1) 中式開孔升降舵（kaguya-shachuan-01m-rudder，kind=rudder + stock-top + spin）
#   2) 尾樓舵柄（kaguya-shachuan-01m-tiller，kind=tiller + spin-a/b + helm_port）
#   3) 四爪鐵錨 ×2（共用件 kotoko-fusta-01m-anchor-grapnel ×0.4，kind=anchor, anchor=bower）＋ 錨架 ＋ hawse-S/P
#   用法：python -I -X utf8 draft_rudder_anchor.py <design> [--probe=shift=<錨-S|錨-P>:<dz>]
import sys, os, json, math, hashlib, subprocess, tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
from wio import export_list
from gunsim import Grid, Gun


def gun_boxes(asm, own_prefix):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + asm, '--arg', 'out=' + out],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
        P = json.load(open(out, encoding='utf-8'))
    return {m['path']: m['box'] for m in P['models'] if (m.get('meta') or {}).get('kind') in ('gun', 'gunmount') and not m['path'].startswith(own_prefix)}


def box_hits(lo, hi, boxes):
    return [p for p, b in boxes.items() if not (hi[0] <= b[0] or lo[0] >= b[3] or hi[1] <= b[1] or lo[1] >= b[4] or hi[2] <= b[2] or lo[2] >= b[5])]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    RB = plan['rudder_anchor_build']
    RU, AN, HW = RB['rudder'], RB['anchor'], RB['hawse']
    YC = plan['space']['yc']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    ASM = 'kaguya-shachuan-01m-assembly'
    HULL = 'kaguya-shachuan-01m'

    A = export_list(ASM, None, links=None)
    own = set()
    for w_ in (AN['gear_work'], RU['tiller_work']):
        if os.path.exists(os.path.join(WORKS, w_, 'work.json')):
            own |= set(map(tuple, export_list(w_, None)[:, :3].tolist()))
    A = np.array([r for r in A.tolist() if tuple(r[:3]) not in own], np.int32)

    # 讀步驟 11 刻 helm port 之前的船殼狀態（用「船尾窗」或補回已刻出的 port）
    H = export_list(HULL, '炮門塗裝:end')
    As = set(map(tuple, A[:, :3].tolist()))
    add = [r for r in H.tolist() if tuple(r[:3]) not in As]
    if add:
        A = np.concatenate([A, np.array(add, np.int32).reshape(-1, 4)])
    Hc0 = {tuple(r[:3]): int(r[3]) for r in H.tolist()}
    Hs0 = set(Hc0)
    minx = {}
    for x, y, z in H[:, :3].tolist():
        if x < minx.get((y, z), 10 ** 9):
            minx[(y, z)] = x

    # ── 1. 中式開孔升降舵（垂直舵柱 x=34, z=1..46；水下開菱形／方孔減轉矩）──
    xs_r = RU['x_stock']
    rudder = {}
    # 舵柱 x=33..35（z 1..46，兩側略收）、舵葉 x=18..34（z 1..22）漸收至上段 z 23..46
    for z in range(RU['z_bot'], RU['z_top'] + 1):
        c = RU['below'] if z <= RU['waterline_z'] else RU['above']
        if z % RU['strap_every'] == RU['strap_every'] // 2:
            c = RU['iron']
        # 舵葉後緣與下段寬度（中式梯形闊葉升降舵，水線以下闊 x=18..34，水上漸收窄為舵柱 x=32..35）
        if z <= 20:
            x_back = 18 + max(0, (z - 14) // 2)
        elif z <= 32:
            x_back = 21 + (z - 20)
        else:
            x_back = 33
        x_fwd = min(35, minx.get((YC, z), 10 ** 9) - 2)
        # 在舵葉前緣允許伸進斜艉虛梢下方（z<=11 時 minx>=51，可在 35..39 加前平衡葉）
        if z <= 10:
            x_fwd = min(39, minx.get((YC, z), 10 ** 9) - 3)
        for y in range(YC - RU['half_t'], YC + RU['half_t'] + 1):
            # 外側面收窄後緣 1 格，前緣留 1 格削斜
            if y != YC and z > 32:
                continue  # 上部舵柱與舷齊平處取 1 格寬圓潤桿
            xb = x_back + (1 if y != YC else 0)
            xf = x_fwd - (1 if y != YC else 0)
            for x in range(xb, xf + 1):
                rudder[(x, y, z)] = c

    # 中式開孔（菱形減力孔：z=5..17 區間於舵葉上開 4 個對穿孔，保持周圍實心連續）
    holes = [
        (24, 9), (29, 9),
        (24, 15), (29, 15),
    ]
    for hx, hz in holes:
        for dx, dz in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            for y in range(YC - RU['half_t'], YC + RU['half_t'] + 1):
                rudder.pop((hx + dx, y, hz + dz), None)

    stock_top = [xs_r, YC, RU['z_top']]
    hinge = [float(RU['hinge_x']), YC + 0.5, float(RU['z_bot'])]
    axis = [0.0, 0.0, 1.0]
    Gs = Grid(A, pad=24, outside=False)
    r_hits = sum(1 for k in rudder if Gs.solid(*k))

    # ── 2. 舵柄（x=35..49, z=43..44 穿過尾板小口 helm port 伸上尾樓甲板）──
    TI = RU['tiller']
    tiller, port = {}, {}
    for z in range(TI['z'], TI['z'] + TI['h']):
        for x in range(xs_r + 1, TI['x_end'] + 1):
            for y in range(YC - TI['port_half'], YC + TI['port_half'] + 1):
                if (x, y, z) in Hs0 and abs(y - YC) <= TI['port_half']:
                    port[(x, y, z)] = Hc0[(x, y, z)]
            for y in range(YC - TI['half'], YC + TI['half'] + 1):
                if (x, y, z) in rudder:
                    continue
                if Gs.solid(x, y, z) and (x, y, z) not in port:
                    continue
                tiller[(x, y, z)] = TI['color'] if x < TI['x_end'] - 1 else TI['end_color']
    t_hits = sum(1 for k in tiller if Gs.solid(*k) and k not in port)
    spin_a = [xs_r, YC, TI['z']]
    spin_b = [xs_r, YC, TI['z'] + TI['h'] - 1]

    # ── 3. 四爪鐵錨（共用元件 ×0.4，吊在方艏兩舷外，避開前舷頂迴旋砲）──
    GB = gun_boxes(ASM, AN['gear_link'] + '/')
    G = Grid(np.concatenate([A[:, :3], np.array(sorted(rudder), np.int32)]), outside=False)
    ac = export_list(AN['work'], None)
    anc = Gun('anchor', {'work': AN['work'], 'scale': AN['scale'], 'pivot': AN['pivot'], 'meta': {}}, ac, {}, 0.2)

    def ymax(x, z):
        ys = [y for y in range(YC, 2 * YC + 1) if (x, y, z) in Hs0]
        return max(ys) if ys else None

    tried, best = [], None
    for xc in AN['x_try']:
        y1, y2 = ymax(xc - 3, AN['z_side']), ymax(xc + 3, AN['z_side'])
        if y1 is None or y2 is None:
            continue
        t = np.array([6.0, float(y2 - y1)])
        t /= np.linalg.norm(t)
        n = np.array([t[1], -t[0]]) if t[1] < 0 else np.array([-t[1], t[0]])
        if n[1] < 0:
            n = -n
        rz = math.degrees(math.atan2(-t[0], t[1]))
        if rz <= -90:
            rz += 180
        rz = round(rz * 2) / 2
        ym = ymax(xc, AN['z_side'])
        if ym is None:
            continue
        surf = np.array([xc + 0.5, ym + 1.0])
        for zt in AN['z_try']:
            hit = None
            for k in range(int(AN['d_max'] / AN['d_step']) + 1):
                d = k * AN['d_step']
                p = surf + n * d
                at = (round(float(p[0]), 3), round(float(p[1]), 3), zt)
                if not G.hit(anc.world(anc.samples, at, rz, False)).any():
                    hit = (d, at)
                    break
            if hit and box_hits(*anc.bbox(hit[1], rz, False), GB):
                tried.append([xc, zt, rz, 'gun'])
                continue
            tried.append([xc, zt, rz, hit[0] if hit else None])
            if hit and (best is None or (hit[0], zt) < (best['d'], best['at'][2])):
                best = {'x': xc, 'rz': rz, 'd': hit[0], 'at': list(hit[1]), 't': t.tolist(), 'n': n.tolist()}

    S = best
    P = {'at': [S['at'][0], round(2 * YC + 1 - S['at'][1], 3), S['at'][2]], 'rz': -S['rz']}
    ws_ = set(map(tuple, np.floor(anc.world(anc.samples, S['at'], S['rz'], False)).astype(int).tolist()))
    wp_ = set(map(tuple, np.floor(anc.world(anc.samples, P['at'], P['rz'], False)).astype(int).tolist()))
    anchor_mirror_diff = len({(x, 2 * YC - y, z) for x, y, z in ws_} ^ wp_)

    # 錨架（錨冠底下托板）
    lo, hi = anc.bbox(S['at'], S['rz'], False)
    ztop = int(math.floor(lo[2])) - 1
    t, n = np.array(S['t']), np.array(S['n'])
    p = np.array(S['at'][:2])
    gear = {}
    for z in range(ztop - AN['ledge_t'] + 1, ztop + 1):
        for x in range(int(p[0]) - 15, int(p[0]) + 16):
            for y in range(int(p[1]) - 15, int(p[1]) + 16):
                cc = np.array([x + 0.5, y + 0.5])
                s_, u_ = float((cc - p) @ t), float((cc - p) @ n)
                if abs(s_) > AN['ledge_half'] or u_ > AN['ledge_out'] or G.solid(x, y, z):
                    continue
                if any(G.solid(int(math.floor(cc[0] + n[0] * k)), int(math.floor(cc[1] + n[1] * k)), z) for k in np.arange(0.5, 30, 0.5)):
                    continue
                if not any(G.solid(int(math.floor(cc[0] - n[0] * k)), int(math.floor(cc[1] - n[1] * k)), z) for k in np.arange(0.5, 20, 0.5)):
                    continue
                gear[(x, y, z)] = AN['color']
    for (x, y, z), c in list(gear.items()):
        gear[(x, 2 * YC - y, z)] = c
    gear_on_solid = sum(1 for k in gear if G.solid(*k))

    G2 = Grid(np.concatenate([G.lo + np.argwhere(G.G), np.array(sorted(gear), np.int32)]), outside=False)
    rows = [{'name': '錨-S', 'at': S['at'], 'rz': S['rz']}, {'name': '錨-P', 'at': P['at'], 'rz': P['rz']}]
    if probe:
        nm, dz = probe[0].split('=', 1)[1].rsplit(':', 1)
        for r in rows:
            if r['name'] == nm:
                r['at'] = [r['at'][0], r['at'][1], r['at'][2] + float(dz)]
    rep = {}
    for r in rows:
        r['hits'] = int(G2.hit(anc.world(anc.samples, r['at'], r['rz'], False)).sum())
        l_, h_ = anc.bbox(r['at'], r['rz'], False)
        r['gun_box_overlap'] = box_hits(l_, h_, GB)
        cx, cy, fz = int(math.floor((l_[0] + h_[0]) / 2)), int(math.floor((l_[1] + h_[1]) / 2)), int(math.floor(l_[2])) - 1
        r['foot_gap'] = next((d for d in range(0, 10) if G2.solid(cx, cy, fz - d)), None)
        r['foot_on_gear'] = r['foot_gap'] is not None and (cx, cy, fz - r['foot_gap']) in gear
        ring = anc.world((np.array([9, 9, 23], float) + 0.5)[None], r['at'], r['rz'], False)[0]
        r['ring'] = [round(float(v), 2) for v in ring]
        rep[r['name']] = r['hits']
    if probe:
        print(json.dumps({'probe': probe[0], 'anchor_hits': rep, 'gun_box_overlap': {r['name']: r['gun_box_overlap'] for r in rows}}, ensure_ascii=False))
        return

    yh = ymax(HW['x'], HW['z'])
    hawse = {'hawse-S': [HW['x'], yh, HW['z']], 'hawse-P': [HW['x'], 2 * YC - yh, HW['z']]}
    v = {'read': {'assembly_voxels_minus_own': int(len(A))},
         'tiller': {'cells': len(tiller), 'on_solid_not_port': t_hits, 'helm_port_cells': len(port), 'spin_a': spin_a, 'spin_b': spin_b,
                    'mirror_diff': sum(1 for (x, y, z), c in tiller.items() if tiller.get((x, 2 * YC - y, z)) != c)},
         'rudder': {'cells': len(rudder), 'on_solid': r_hits, 'z': [RU['z_bot'], RU['z_top']], 'stock_top': stock_top,
                    'stock_top_to_hull': min(abs(stock_top[0] - x) for x in [minx.get((YC, RU['z_top']), 10 ** 9)]),
                    'hinge': hinge, 'axis': axis, 'mirror_diff': sum(1 for (x, y, z), c in rudder.items() if rudder.get((x, 2 * YC - y, z)) != c)},
         'anchor': {'tried': tried, 'chosen': S, 'P': P, 'mirror_diff_cells': anchor_mirror_diff, 'rows': rows},
         'gear': {'cells': len(gear), 'on_solid': gear_on_solid, 'mirror_diff': sum(1 for (x, y, z), c in gear.items() if gear.get((x, 2 * YC - y, z)) != c), 'ztop': ztop},
         'hawse': hawse}

    out = os.path.join(design, 'masks', 'rudder')
    os.makedirs(out, exist_ok=True)
    lists = {}
    for nm, part in (('rudder', rudder), ('anchor_gear', gear), ('tiller', tiller), ('helm_port_hull', port)):
        pth = os.path.join(out, nm + '.vox.txt')
        with open(pth, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 沙船 %s（世界座標、at 0,0,0；draft_rudder_anchor.py）\n' % nm)
            for (x, y, z), c in sorted(part.items()):
                f.write('%d,%d,%d,%d\n' % (x, y, z, c))
        lists[nm] = [len(part), hashlib.sha256(open(pth, 'rb').read()).hexdigest()]
    v['lists'] = lists

    place = {'note': 'draft_rudder_anchor.py 的結果（世界座標）',
             'rudder': {'work': RU['work'], 'model': RU['model'], 'host': ASM, 'at': hinge, 'pivot': hinge,
                        'anchors': {'stock-top': stock_top},
                        'meta': {'kind': 'rudder', 'hinge_x': hinge[0], 'hinge_y': hinge[1], 'hinge_z': hinge[2], 'axis_x': axis[0], 'axis_y': axis[1], 'axis_z': axis[2],
                                 'max_deg': RU['max_deg'], 'turn_axis': 'hinge'}},
             'anchors': [{'name': r['name'], 'host': AN['gear_work'], 'work': AN['work'], 'at': r['at'], 'pivot': AN['pivot'], 'scale': AN['scale'], 'rotate': r['rz'],
                          'meta': {'kind': 'anchor', 'anchor': 'bower'}} for r in rows],
             'tiller': {'work': RU['tiller_work'], 'model': '舵柄', 'host': RU['tiller_host'], 'at': hinge, 'pivot': hinge, 'anchors': {'spin-a': spin_a, 'spin-b': spin_b},
                        'meta': {'kind': 'tiller', 'spin': 'rudder', 'spin_k': RU['max_deg'], 'spin_min': -RU['max_deg'], 'spin_max': RU['max_deg'], 'spin_lag': 0.3}},
             'hawse': hawse}
    json.dump(place, open(os.path.join(design, 'rudder_anchor_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(design, 'verify_rudder_anchor.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in ('rudder', 'tiller', 'gear', 'hawse', 'lists')}, ensure_ascii=False))
    print(json.dumps({k: v['anchor'][k] for k in ('chosen', 'P', 'mirror_diff_cells', 'rows')}, ensure_ascii=False))
    print(json.dumps(v['anchor']['tried'], ensure_ascii=False))


if __name__ == '__main__':
    main()
