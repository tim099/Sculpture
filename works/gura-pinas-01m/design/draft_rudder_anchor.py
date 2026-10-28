# 出處：calli-cosecha-01m/design/draft_rudder_anchor.py（收穫號，照抄後改成藍鯊號 —— TASK-0967）
# 藍鯊號 階段九半（TASK-0619）：舵（新子作品，外部模型、kind=rudder、stock-top）、錨（共用錨元件 ×2、kind=anchor）＋錨架（billboard 托板，新子作品）、錨鏈孔 hawse-S／P
#   輸入：plan.json（rudder_anchor_build）＋ 組裝件現在的格子（CLI 匯出，扣掉本階段自己的錨架）＋ 船首樓上的砲（模型，取樣成格）
#   輸出：masks/rudder/{rudder,anchor_gear}.vox.txt（世界座標、at 0,0,0）、rudder_anchor_placement.json、verify_rudder_anchor.json
#   用法：python -I -X utf8 draft_rudder_anchor.py <design> [--probe=shift=<錨-S|錨-P>:<dz>]（反向對照：那一隻錨上下挪幾格，印碰撞，⛔ 不寫檔）
import sys, os, json, math, hashlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
from wio import export_list
from gunsim import Grid, Gun


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    RB = plan['rudder_anchor_build']
    RU, AN, HW = RB['rudder'], RB['anchor'], RB['hawse']
    YC = plan['space']['yc']
    WORKS = os.environ.get('SCULPT_WORKS') or os.path.dirname(os.path.dirname(os.path.abspath(design)))   # worktree 只放 design/ ⇒ 作品資料讀共用的那一份
    A = export_list('gura-pinas-01m-assembly', None, links=None)
    own = set()
    if os.path.exists(os.path.join(WORKS, AN['gear_work'], 'work.json')):
        own = set(map(tuple, export_list(AN['gear_work'], None)[:, :3].tolist()))
    A = np.array([r for r in A.tolist() if tuple(r[:3]) not in own], np.int32)
    H = export_list('gura-pinas-01m', None)
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
    Gs = Grid(A)
    r_hits = sum(1 for k in rudder if Gs.solid(*k))

    # ── 錨：共用錨元件，錨臂順著船殼切線、往外推到零碰撞 ──
    cas = []
    gun_models = []                                                    # 船頭附近的砲（收穫號讀船首樓甲板；藍鯊號的船頭砲在上甲板、船艏樓底下 ⇒ plan anchor.gun_decks）
    for w_ in AN['gun_decks']:
        gun_models += json.load(open(os.path.join(WORKS, w_, 'models.json'), encoding='utf-8'))['models']
    for m in gun_models:
        g = Gun(m['name'], {'work': m['work'], 'scale': m['scale'][0], 'pivot': m['pivot'], 'meta': {}}, export_list(m['work'], None), {}, 0.2)
        cas.append(np.floor(g.world(g.samples, m['at'], m['rotate'][2], m['mirror'] == 'y')).astype(int))
    G = Grid(np.concatenate([A[:, :3]] + cas + [np.array(sorted(rudder), np.int32)]), outside=False)     # 舷外的錨與托板：框外當空（框外當實心 ⇒ 托板「往外走會碰到實心」全判成船裡）
    ac = export_list(AN['work'], None)
    anc = Gun('anchor', {'work': AN['work'], 'scale': AN['scale'], 'pivot': AN['pivot'], 'meta': {}}, ac, {}, 0.2)
    Hs = set(map(tuple, H[:, :3].tolist()))

    def ymax(x, z):
        ys = [y for y in range(YC, 2 * YC + 1) if (x, y, z) in Hs]
        return max(ys) if ys else None

    tried, best = [], None
    zr = AN['z_ref']                                                   # 量船殼切線的那一層（收穫號寫死 z 100）
    for xc in AN['x_try']:
        y1, y2 = ymax(xc - 4, zr), ymax(xc + 4, zr)
        t = np.array([8.0, float(y2 - y1)])
        t /= np.linalg.norm(t)
        n = np.array([t[1], -t[0]]) if t[1] < 0 else np.array([-t[1], t[0]])
        if n[1] < 0:
            n = -n
        rz = math.degrees(math.atan2(-t[0], t[1]))
        if rz <= -90:
            rz += 180
        rz = round(rz * 2) / 2
        surf = np.array([xc + 0.5, ymax(xc, zr) + 1.0])
        for zt in AN['z_try']:
            hit = None
            for k in range(int(AN['d_max'] / AN['d_step']) + 1):
                d = k * AN['d_step']
                p = surf + n * d
                at = (round(float(p[0]), 3), round(float(p[1]), 3), zt)
                if not G.hit(anc.world(anc.samples, at, rz, False)).any():
                    hit = (d, at)
                    break
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
        cx, cy, fz = int(math.floor((l_[0] + h_[0]) / 2)), int(math.floor((l_[1] + h_[1]) / 2)), int(math.floor(l_[2])) - 1
        r['foot_gap'] = next((d for d in range(0, 13) if G2.solid(cx, cy, fz - d)), None)
        r['foot_on_gear'] = r['foot_gap'] is not None and (cx, cy, fz - r['foot_gap']) in gear
        ring = anc.world((np.array([23, 16, 56], float) + 0.5)[None], r['at'], r['rz'], False)[0]
        r['ring'] = [round(float(v), 2) for v in ring]
        rep[r['name']] = r['hits']
    if probe:
        print(json.dumps({'probe': probe[0], 'anchor_hits': rep}, ensure_ascii=False))
        return
    helm = []                                                          # 舵輪與座（藍鯊號；Ship_Helm §9.8.1）：撞實心的樣本、腳下 12 格內有沒有實心
    for h in RB['helm']:
        gh = Gun(h['name'], {'work': h['work'], 'scale': h['scale'], 'pivot': h['pivot'], 'meta': {}}, export_list(h['work'], None), {}, 0.2)
        l_, h_ = gh.bbox(h['at'], h['rotate'], False)
        cx, cy, fz = int(math.floor((l_[0] + h_[0]) / 2)), int(math.floor((l_[1] + h_[1]) / 2)), int(math.floor(l_[2])) - 1
        helm.append({'name': h['name'], 'hits': int(Gs.hit(gh.world(gh.samples, h['at'], h['rotate'], False)).sum()),
                     'foot_gap': next((d for d in range(0, 13) if Gs.solid(cx, cy, fz - d)), None), 'bbox': [l_.round(2).tolist(), h_.round(2).tolist()]})
    yh = ymax(HW['x'], HW['z'])
    hawse = {'hawse-S': [HW['x'], yh, HW['z']], 'hawse-P': [HW['x'], 2 * YC - yh, HW['z']]}
    v = {'read': {'assembly_voxels_minus_own': int(len(A))},
         'rudder': {'cells': len(rudder), 'on_solid': r_hits, 'z': [0, RU['z_top']], 'stock_top': stock_top,
                    'stock_top_to_hull': min(abs(stock_top[0] - x) for x in [minx.get((YC, RU['z_top']), 10 ** 9)]),
                    'hinge': hinge, 'axis': axis, 'mirror_diff': sum(1 for (x, y, z), c in rudder.items() if rudder.get((x, 2 * YC - y, z)) != c)},
         'anchor': {'tried': tried, 'chosen': S, 'P': P, 'mirror_diff_cells': anchor_mirror_diff, 'rows': rows},
         'gear': {'cells': len(gear), 'on_solid': gear_on_solid, 'mirror_diff': sum(1 for (x, y, z), c in gear.items() if gear.get((x, 2 * YC - y, z)) != c), 'ztop': ztop},
         'hawse': hawse, 'helm': helm}
    out = os.path.join(design, 'masks', 'rudder')
    os.makedirs(out, exist_ok=True)
    lists = {}
    for nm, part in (('rudder', rudder), ('anchor_gear', gear)):
        pth = os.path.join(out, nm + '.vox.txt')
        with open(pth, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 藍鯊號 %s（世界座標、at 0,0,0；draft_rudder_anchor.py）\n' % nm)
            for (x, y, z), c in sorted(part.items()):
                f.write('%d,%d,%d,%d\n' % (x, y, z, c))
        lists[nm] = [len(part), hashlib.sha256(open(pth, 'rb').read()).hexdigest()]
    v['lists'] = lists
    place = {'note': 'draft_rudder_anchor.py 的結果（世界座標）',
             'rudder': {'work': RU['work'], 'model': RU['model'], 'host': 'gura-pinas-01m-assembly', 'at': hinge, 'pivot': hinge,
                        'anchors': {'stock-top': stock_top},
                        'meta': dict({'kind': 'rudder', 'hinge_x': hinge[0], 'hinge_y': hinge[1], 'hinge_z': hinge[2], 'axis_x': axis[0], 'axis_y': axis[1], 'axis_z': axis[2],
                                      'max_deg': RU['max_deg'], 'turn_axis': 'hinge'}, **RB['spin']['rudder'])},
             'helm': [dict(h, meta=dict(h['meta'], **(RB['spin']['wheel'] if h['meta']['kind'] == 'wheel' else {}))) for h in RB['helm']],
             'anchors': [{'name': r['name'], 'host': AN['gear_work'], 'work': AN['work'], 'at': r['at'], 'pivot': AN['pivot'], 'scale': AN['scale'], 'rotate': r['rz'],
                          'meta': {'kind': 'anchor', 'anchor': 'bower'}} for r in rows],
             'hawse': hawse}
    json.dump(place, open(os.path.join(design, 'rudder_anchor_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(design, 'verify_rudder_anchor.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in ('rudder', 'gear', 'hawse', 'helm', 'lists')}, ensure_ascii=False))
    print(json.dumps({k: v['anchor'][k] for k in ('chosen', 'P', 'mirror_diff_cells', 'rows')}, ensure_ascii=False))
    print(json.dumps(v['anchor']['tried'], ensure_ascii=False))


if __name__ == '__main__':
    main()
