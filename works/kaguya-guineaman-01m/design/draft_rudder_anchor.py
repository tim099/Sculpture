# 出處：summit-boaviagem-01m/design/draft_rudder_anchor.py（2026-11-01 複製；作品 id、persona、船名、單號已換）
#   它的出處鏈：erina-oxford-01m（TASK-0972 牛津號）⇒ erina-tradewind-01m（TASK-1097 信風號，加舵柄）⇒ summit-boaviagem-01m（TASK-1151 好旅號）
#   （本船原本那一份是牛津號的、沒有舵柄 ⇒ 換成好旅號這一版，同步驟 9 的砲）
# 幾內亞船 步驟 11（TASK-1149）：舵（新子作品，外部模型、kind=rudder、stock-top、spin）、舵柄（新子作品，kind=tiller、spin-a／b）＋船尾板的 helm port、
#   錨（共用錨元件 ×2、kind=anchor）＋錨架托板、錨鏈孔 hawse-S／P
#   舵柄：舵頭從船尾板外面升到後甲板的高度，舵柄穿過船尾板一個小口伸進艉樓底下（steerage）
#   跟好旅號不同：艏樓上有迴旋砲 ⇒ 錨的候選位置外框碰到砲模型的外框就不選（`gun_box_overlap`）
#   來源：calli-cosecha-01m/design/draft_rudder_anchor.py（照抄後改：作品 id、船殼的 z 參考寫進 plan）
#   用法：python -I -X utf8 draft_rudder_anchor.py <design> [--probe=shift=<錨-S|錨-P>:<dz>]（反向對照：那一隻錨上下挪幾格，印碰撞，⛔ 不寫檔）
import sys, os, json, math, hashlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
from wio import export_list
from gunsim import Grid, Gun


def gun_boxes(asm, own_prefix):
    """組裝件裡別人的模型外框（砲、座…）；本步驟自己的錨不算。照 draft_gear.py 的 parts_boxes。"""
    import subprocess, tempfile
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
    L = HL.Lines(plan)
    RB = plan['rudder_anchor_build']
    RU, AN, HW = RB['rudder'], RB['anchor'], RB['hawse']
    YC = plan['space']['yc']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list('kaguya-guineaman-01m-assembly', None, links=None)
    own = set()
    for w_ in (AN['gear_work'], RU['tiller_work']):
        if os.path.exists(os.path.join(WORKS, w_, 'work.json')):
            own |= set(map(tuple, export_list(w_, None)[:, :3].tolist()))
    A = np.array([r for r in A.tolist() if tuple(r[:3]) not in own], np.int32)
    # 船殼讀本步驟開始時的樣子（Ship_Game §10「產生程式重跑逐位元組相同」）：helm port 是本步驟刻的 ⇒ 讀上一個標記「艏斜桅孔」（point，刻 helm port 之前）；
    #   🩸 步驟 15 照現況重跑 ⇒ helm port 0 格、stock_top_to_hull 找不到船殼（10 ** 9）。組裝件裡的船殼 at 0,0,0 ⇒ 刻掉的那幾格補回 A
    H = export_list('kaguya-guineaman-01m', '艏斜桅孔')
    As = set(map(tuple, A[:, :3].tolist()))
    A = np.concatenate([A, np.array([r for r in H.tolist() if tuple(r[:3]) not in As], np.int32).reshape(-1, 4)])
    Hc0 = {tuple(r[:3]): r[3] for r in H.tolist()}
    Hs0 = set(Hc0)
    minx = {}
    for x, y, z in H[:, :3].tolist():
        if x < minx.get((y, z), 10 ** 9):
            minx[(y, z)] = x

    # ── 舵：沿艉柱後緣（x_post），3 格厚，寬照 width 表內插 ──
    rake = L.sp_rake
    zs_w, ws = zip(*RU['width'])
    rudder = {}
    for z in range(0, RU['z_top'] + 1):
        xh = float(L.x_post(z + 0.5))
        W = float(np.interp(z, zs_w, ws))
        c = RU['below'] if z <= RU['waterline_z'] else RU['above']
        if z % RU['strap_every'] == RU['strap_every'] // 2:
            c = RU['iron']
        for y in range(YC - RU['half_t'], YC + RU['half_t'] + 1):
            x_hi = min(int(math.floor(xh)) - 1, minx.get((y, z), 10 ** 9) - 1) - (RU['bevel'] if y != YC else 0)     # 兩側前緣削斜（bearding）⇒ 轉舵不掃進艉柱
            for x in range(int(math.floor(xh - W)), x_hi + 1):
                rudder[(x, y, z)] = c
    top = sorted(x for (x, y, z) in rudder if z == RU['z_top'] and y == YC)
    stock_top = [top[len(top) // 2], YC, RU['z_top']]
    hinge = [round(float(L.x_post(0.0)), 3), YC + 0.5, 0.0]
    axis = [round(-math.sin(rake), 4), 0.0, round(math.cos(rake), 4)]
    Gs = Grid(A, pad=16)                     # 🩸 pad 4：舵後緣伸出組裝件外框 ⇒ 框外當實心 ⇒ 舵 198 格「落在實心」假警報
    r_hits = sum(1 for k in rudder if Gs.solid(*k))
    # ── 舵柄：舵頭上面那兩層、從舵的軸往前穿過船尾舷牆（helm port：那幾格船殼刻掉）伸進後甲板 ──
    TI = RU['tiller']
    xa = int(math.floor(float(L.x_post(TI['z'] + 0.5)))) - 1                        # 舵軸在舵柄高度的 x（舵的前緣後一格）
    tiller, port = {}, {}
    for z in range(TI['z'], TI['z'] + TI['h']):
        for y in range(YC - TI['half'], YC + TI['half'] + 1):
            for x in range(xa, TI['x_end'] + 1):
                if (x, y, z) in rudder:
                    continue
                if (x, y, z) in Hs0:
                    port[(x, y, z)] = Hc0[(x, y, z)]                                  # 船殼那幾格：刻掉（帶顏色守門），舵柄填進去
                elif Gs.solid(x, y, z):
                    continue
                tiller[(x, y, z)] = TI['color'] if x < TI['x_end'] - 1 else TI['end_color']
    t_hits = sum(1 for k in tiller if Gs.solid(*k) and k not in port)
    spin_a, spin_b = [xa, YC, TI['z']], [xa, YC, TI['z'] + TI['h'] - 1]

    # ── 錨：共用錨元件，錨臂順著船殼切線、往外推到零碰撞 ──
    cas = []                                                                       # 砲是模型、不在格子裡 ⇒ 改用砲模型的外框（gun_box_overlap）
    GB = gun_boxes('kaguya-guineaman-01m-assembly', AN['gear_link'] + '/')
    G = Grid(np.concatenate([A[:, :3]] + cas + [np.array(sorted(rudder), np.int32)]), outside=False)     # 舷外的錨與托板：框外當空（框外當實心 ⇒ 托板「往外走會碰到實心」全判成船裡）
    ac = export_list(AN['work'], None)
    anc = Gun('anchor', {'work': AN['work'], 'scale': AN['scale'], 'pivot': AN['pivot'], 'meta': {}}, ac, {}, 0.2)
    Hs = set(map(tuple, H[:, :3].tolist()))

    def ymax(x, z):
        ys = [y for y in range(YC, 2 * YC + 1) if (x, y, z) in Hs]
        return max(ys) if ys else None

    tried, best = [], None
    for xc in AN['x_try']:
        y1, y2 = ymax(xc - 4, AN['z_side']), ymax(xc + 4, AN['z_side'])
        t = np.array([8.0, float(y2 - y1)])
        t /= np.linalg.norm(t)
        n = np.array([t[1], -t[0]]) if t[1] < 0 else np.array([-t[1], t[0]])
        if n[1] < 0:
            n = -n
        rz = math.degrees(math.atan2(-t[0], t[1]))
        if rz <= -90:
            rz += 180
        rz = round(rz * 2) / 2
        surf = np.array([xc + 0.5, ymax(xc, AN['z_side']) + 1.0])
        for zt in AN['z_try']:
            hit = None
            for k in range(int(AN['d_max'] / AN['d_step']) + 1):
                d = k * AN['d_step']
                p = surf + n * d
                at = (round(float(p[0]), 3), round(float(p[1]), 3), zt)
                if not G.hit(anc.world(anc.samples, at, rz, False)).any():
                    hit = (d, at)
                    break
            if hit and box_hits(*anc.bbox(hit[1], rz, False), GB):                    # 錨的外框碰到迴旋砲（或座）的外框 ⇒ 這個位置不選
                tried.append([xc, zt, rz, 'gun'])
                continue
            tried.append([xc, zt, rz, hit[0] if hit else None])
            if hit and (best is None or (hit[0], zt) < (best['d'], best['at'][2])):      # 每個高度都試完、取最貼船的（v1 一找到可行高度就停 ⇒ 橫桿擦欄杆、整隻錨被推出去 18 格）
                best = {'x': xc, 'rz': rz, 'd': hit[0], 'at': list(hit[1]), 't': t.tolist(), 'n': n.tolist()}
    S = best
    P = {'at': [S['at'][0], round(2 * YC + 1 - S['at'][1], 3), S['at'][2]], 'rz': -S['rz']}
    # 兩舷對稱（P 不鏡像、只 rotate −rz ⇒ 同一份網格）：取樣點的格，P ＝ S 鏡過去？
    ws_ = set(map(tuple, np.floor(anc.world(anc.samples, S['at'], S['rz'], False)).astype(int).tolist()))
    wp_ = set(map(tuple, np.floor(anc.world(anc.samples, P['at'], P['rz'], False)).astype(int).tolist()))
    anchor_mirror_diff = len({(x, 2 * YC - y, z) for x, y, z in ws_} ^ wp_)

    # ── 錨架：錨冠底下的 billboard 托板（S 舷算、P 舷鏡過去）──
    lo, hi = anc.bbox(S['at'], S['rz'], False)
    ztop = int(math.floor(lo[2])) - 1
    t, n = np.array(S['t']), np.array(S['n'])
    p = np.array(S['at'][:2])
    gear = {}
    for z in range(ztop - AN['ledge_t'] + 1, ztop + 1):
        for x in range(int(p[0]) - 20, int(p[0]) + 21):
            for y in range(int(p[1]) - 20, int(p[1]) + 21):
                cc = np.array([x + 0.5, y + 0.5])
                s_, u_ = float((cc - p) @ t), float((cc - p) @ n)
                if abs(s_) > AN['ledge_half'] or u_ > AN['ledge_out'] or G.solid(x, y, z):
                    continue
                if any(G.solid(int(math.floor(cc[0] + n[0] * k)), int(math.floor(cc[1] + n[1] * k)), z) for k in np.arange(0.5, 40, 0.5)):
                    continue                                                       # 往外走會碰到實心 ⇒ 在船裡面（不是舷外）
                if not any(G.solid(int(math.floor(cc[0] - n[0] * k)), int(math.floor(cc[1] - n[1] * k)), z) for k in np.arange(0.5, 30, 0.5)):
                    continue                                                       # 往裡走碰不到船殼 ⇒ 不靠船
                gear[(x, y, z)] = AN['color']
    for (x, y, z), c in list(gear.items()):
        gear[(x, 2 * YC - y, z)] = c
    gear_on_solid = sum(1 for k in gear if G.solid(*k))
    # 錨架裝上去之後，錨照樣零碰撞？錨的腳（外框中心往下）是錨架？
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
        r['foot_gap'] = next((d for d in range(0, 13) if G2.solid(cx, cy, fz - d)), None)
        r['foot_on_gear'] = r['foot_gap'] is not None and (cx, cy, fz - r['foot_gap']) in gear
        ring = anc.world((np.array([23, 16, 56], float) + 0.5)[None], r['at'], r['rz'], False)[0]
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
         'rudder': {'cells': len(rudder), 'on_solid': r_hits, 'z': [0, RU['z_top']], 'stock_top': stock_top,
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
            f.write('# 幾內亞船 %s（世界座標、at 0,0,0；draft_rudder_anchor.py）\n' % nm)
            for (x, y, z), c in sorted(part.items()):
                f.write('%d,%d,%d,%d\n' % (x, y, z, c))
        lists[nm] = [len(part), hashlib.sha256(open(pth, 'rb').read()).hexdigest()]
    v['lists'] = lists
    place = {'note': 'draft_rudder_anchor.py 的結果（世界座標）',
             'rudder': {'work': RU['work'], 'model': RU['model'], 'host': 'kaguya-guineaman-01m-assembly', 'at': hinge, 'pivot': hinge,
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
