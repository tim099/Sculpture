# 越嶺號 階段五（TASK-0762）：舵、艙底、彈藥庫、艙口梯、四爪錨、甲板 meta ⇒
#   masks/hold/{rudder,hold,magazine,ladder}.vox.txt、masks/hold/anchor.vox.txt（新通用部件）、hold_placement.json、decks_meta.tsv、verify_hold.json
#   用法：python -I -X utf8 draft_hold.py [--probe=floor=3]   （probe ⇒ 地板抬幾格，只印彈藥庫與梯腳的淨空；⛔ 不寫檔）
#   · 讀船殼、階段二～四（清單 ＝ 作品已證；武器、帆桁照模型擺法取樣）。做法照皇家號 draft_hold.py（舵＝模型、艙底填壓艙、彈藥庫 hoist）。
import sys, os, json, math, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL
import draft_guns as DG

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 360, 161, 230
C_BAL, C_FLOOR, C_COPPER, C_WOOD, C_DARK, C_BLACK, C_TOP, C_IRON = 146, 177, 168, 141, 68, 36, 173, 73


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def grapnel(len_m, span_m):
    """四爪錨（0.05 m；錨幹沿 +z、ring 在上 —— 照憲法號錨的慣例）。"""
    H = int(round(len_m / 0.05))
    R = span_m / 0.05 / 2
    W = int(math.ceil(R)) * 2 + 3
    c = W // 2
    cells = {}
    for z in range(3, H - 2):                                    # 錨幹 2×2
        for x in (c, c + 1):
            for y in (c, c + 1):
                cells[(x, y, z)] = C_IRON
    for z in range(H - 3, H):                                    # 錨環（xz 平面一個小方環）
        for x in range(c - 1, c + 3):
            if z in (H - 3, H - 1) or x in (c - 1, c + 2):
                cells[(x, c, z)] = C_IRON
    for ang in (0, 90, 180, 270):                                # 四爪：從錨冠往外再往上彎
        ca, sa = round(math.cos(math.radians(ang))), round(math.sin(math.radians(ang)))
        for k in range(0, int(R) + 1):
            zc = 2 + int(round((k / R) ** 2 * 6))
            for zz in range(2, zc + 2) if k == int(R) else (zc, zc + 1):
                x, y = c + int(round(ca * k)) + (1 if ca >= 0 and ang in (0,) else 0), c + int(round(sa * k)) + (1 if sa > 0 else 0)
                for dx in (0, 1) if ca == 0 else (0,):
                    for dy in (0, 1) if sa == 0 else (0,):
                        cells[(x + dx, y + dy, zz)] = C_IRON
    for x in range(c - 1, c + 3):                                # 錨冠
        for y in range(c - 1, c + 3):
            for z in range(0, 4):
                cells[(x, y, z)] = C_IRON
    tipA = max((k for k in cells if k[1] in (c, c + 1)), key=lambda k: (k[0], k[2]))
    tipB = min((k for k in cells if k[1] in (c, c + 1)), key=lambda k: (k[0], -k[2]))
    anchors = {'ring': (c, c, H - 1), 'crown': (c, c, 0), 'fluke-a': tipA, 'fluke-b': tipB}
    return cells, anchors, (W + 1, W + 1, H)


def main():
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=', 1)
            probe[k] = float(v)
    plan, L, occ = DG.world()
    YC = L.YC
    hp = {k: V(v) for k, v in plan['hold'].items() if k != 'src'}
    tz = np.floor(L.sheer(np.arange(SX) + 0.5)).astype(int)
    hull = np.zeros((SX, SY, 80), bool)
    hc = DL.hull_cells(L, plan)
    hull[DL.X0:DL.X0 + hc.shape[0], :, :hc.shape[2]] = hc > 0
    sol = np.zeros((SX, SY, 80), bool)
    s0 = L.solid(DL.X0, DL.X1, DL.ZMAX, 0)
    sol[DL.X0:DL.X0 + s0.shape[0], :, :s0.shape[2]] = s0
    interior = sol & ~hull
    # 武器模型也算障礙（錨要避開）
    gp = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))
    gocc = np.zeros((SX, SY, SZ), bool)
    bomb = DG.load_list(os.path.join(HERE, 'masks', 'guns', 'bombardella.vox.txt'))
    srcs = {'kotoko-fusta-01m-gun-bombardella': bomb}
    for r in gp['rows']:
        Q = srcs.get(r['source_work'])
        if Q is None:
            Q = srcs[r['source_work']] = DG.export(r['source_work'])
        Pw = DG.place((Q[:, :3].astype(float)[:, None, :] + DG.OFFS[None]).reshape(-1, 3), r)
        i = np.floor(Pw).astype(int)
        gocc[i[:, 0], i[:, 1], i[:, 2]] = True
    allocc = occ | gocc
    parts = {k: {} for k in ('rudder', 'hold', 'magazine', 'ladder')}

    # ── 舵：鉸鏈 ＝ 艉柱後緣在 z_fit 兩點的連線，往後退到每一層都不碰艉柱（再留 gap）；舵葉往後（−x）w 格寬、3 格厚 ──
    ru = hp['rudder']
    za, zb = ru['z_fit']
    xa, xb = float(L.x_aft(za + 0.5)), float(L.x_aft(zb + 0.5))
    b = (xb - xa) / (zb - za)
    a0 = xa - b * (za + 0.5)
    viol = max(a0 + b * (z + 0.5) - min((x for x in range(SX) if hull[x, YC, z]), default=999) for z in range(0, ru['stock_top'] + 1) if hull[:, YC, z].any())
    a0 -= max(0.0, viol) + ru['gap']
    hx = lambda z: a0 + b * (z + 0.5)                            # 鉸鏈（舵葉前緣）在 z 那一層的 x
    for z in range(0, ru['stock_top'] + 1):
        if z <= ru['blade_top']:
            w = ru['w_bottom'] + (ru['w_top'] - ru['w_bottom']) * z / ru['blade_top']
        else:
            w = 2
        for x in range(int(math.floor(hx(z) - w)), int(math.floor(hx(z)))):
            if x + 0.5 > hx(z) - w:
                for dy in (-1, 0, 1):
                    c = C_BLACK if z <= plan['waterline']['z'] else (C_TOP if z <= ru['blade_top'] else C_WOOD)
                    parts['rudder'][(x, YC + dy, z)] = c
    sx_ = int(math.floor(hx(ru['tiller_z']))) - 1                # 舵柄：從舵頭往前（+x）到船尾篷下
    for x in range(sx_, ru['tiller_x1'] + 1):
        parts['rudder'][(x, YC, ru['tiller_z'])] = C_DARK
    stock_top = (sx_, YC, ru['stock_top'])
    parts['rudder'][stock_top] = C_WOOD
    for z in range(ru['tiller_z'], ru['stock_top'] + 1):
        parts['rudder'][(sx_, YC, z)] = C_WOOD
    hinge = (round(hx(0), 3), YC + 0.5, 0.0)
    ax = np.array([b, 0.0, 1.0])
    ax = ax / np.linalg.norm(ax)
    rud_hits = sum(1 for k in parts['rudder'] if allocc[k])

    # ── 艙底：x0–x1 一層地板（z），地板下填壓艙碎石（只填船殼裡面）──
    fl = hp['floor']
    zf = fl['z'] + int(probe.get('floor', 0))
    for x in range(fl['x0'], fl['x1'] + 1):
        for y in range(SY):
            for z in range(0, zf + 1):
                if interior[x, y, z] and not occ[x, y, z]:
                    parts['hold'][(x, y, z)] = C_FLOOR if z == zf else C_BAL
    # ── 彈藥庫：x0–x1、|dy| ≤ half，地板上到甲板底的銅皮牆；船尾那面開門 ──
    mg = hp['magazine']
    for x in range(mg['x0'], mg['x1'] + 1):
        for dy in range(-mg['half'], mg['half'] + 1):
            wall = x in (mg['x0'], mg['x1']) or abs(dy) == mg['half']
            if not wall or (x == mg['x0'] and abs(dy) <= mg['door_half']):          # 門開在船尾那面（朝梯腳）
                continue
            for z in range(zf + 1, SZ):
                if occ[x, YC + dy, z] or not interior[x, YC + dy, z]:
                    break
                parts['magazine'][(x, YC + dy, z)] = C_COPPER
    head_in = []
    for x in range(mg['x0'] + 1, mg['x1']):
        z = zf + 1
        while z < 80 and interior[x, YC, z] and not occ[x, YC, z]:
            z += 1
        head_in.append(z - (zf + 1))
    # 火藥桶 4、箭箱 2（模型；掛在彈藥庫子作品）
    stores = []
    k = 0
    for i, (dx, dy) in enumerate(((3.5, -3.0), (3.5, 3.0))[:mg['barrels']]):
        stores.append({'name': 'barrel-%d' % (i + 1), 'work': 'basecamp-frigate-constitution-01m-powder-barrel', 'at': [mg['x0'] + dx, YC + 0.5 + dy, zf + 1],
                       'pivot': [11, 11, 0], 'scale': 0.2, 'rotate': [0, 0, 0], 'meta': {'kind': 'powder', 'powder_lb': 100}})
    for i, dy in enumerate((-3.0, 3.0)[:mg['boltboxes']]):
        stores.append({'name': 'arrows-%d' % (i + 1), 'work': 'erina-dromon-01m-store-boltbox', 'at': [mg['x0'] + 10.5, YC + 0.5 + dy, zf + 1],
                       'pivot': [5.5, 3.5, 0], 'scale': 0.5, 'rotate': [0, 0, 0], 'meta': {'kind': 'powder', 'powder_lb': 100, 'store': 'bolt'}})
    store_hits = []
    for s in stores:
        Q = DG.export(s['work'])
        Pw = DG.place((Q[:, :3].astype(float)[:, None, :] + DG.OFFS[None]).reshape(-1, 3), dict(s, mirror=''))
        i = np.floor(Pw).astype(int)
        hc_ = [t for t in map(tuple, i) if occ[t] or t in parts['magazine'] or t in parts['hold']]
        store_hits.append(len(hc_))
        if hc_:
            print('  ', s['name'], 'hits', sorted(set(hc_))[:6], file=sys.stderr)
    # ── 艙口梯：艙口 x 82–87；兩根梯樑 dy ±2、踏板 dy −1..1、每 step 格一階，從艙底往船尾上到甲板 ──
    ld = hp['ladder']
    x_lo, x_hi = ld['x_hatch'][1] + 1, ld['x_hatch'][0]
    z_lo, z_hi = zf + 1, int(tz[ld['x_hatch'][0]])
    steps = []
    nst = (z_hi - z_lo) // ld['step']
    for i in range(1, nst + 1):
        z = z_lo + i * ld['step'] - 1
        x = int(round(x_lo - (x_lo - x_hi) * i / (nst + 1)))
        steps.append((x, z))
        for dy in (-1, 0, 1):
            parts['ladder'][(x, YC + dy, z)] = C_WOOD
    for i in range(len(steps)):
        x, z = steps[i]
        zprev = steps[i - 1][1] if i else z_lo - 1
        for zz in range(zprev + 1, z + 1):
            for dy in (-2, 2):
                if not occ[x, YC + dy, zz]:                     # 梯樑腳碰到船殼的那一格不放（坐在船殼上）
                    parts['ladder'][(x, YC + dy, zz)] = C_DARK
        if i:
            for xx in range(x, steps[i - 1][0] + 1):
                for dy in (-2, 2):
                    parts['ladder'][(xx, YC + dy, steps[i - 1][1])] = C_DARK
    lad_hit_cells = [k for k in parts['ladder'] if occ[k] or k in parts['hold']]
    lad_hits = len(lad_hit_cells)
    foot = (steps[0][0] + 2, YC, z_lo)
    head = (x_hi - 2, YC, int(tz[x_hi - 2]) + 1)
    lo = (steps[0][0], YC, steps[0][1] + 1)
    hi = (steps[-1][0], YC, steps[-1][1] + 1)
    for nm, p in (('foot', foot), ('lo', lo), ('hi', hi), ('head', head)):
        assert not (occ[p] or p in parts['ladder'] or p in parts['hold']), ('梯子點不是空格', nm, p)
    for nm, p in (('foot', foot), ('head', head)):
        q = (p[0], p[1], p[2] - 1)
        assert occ[q] or q in parts['hold'], ('梯子點腳下不是實心', nm, p)
    # 中央走道前端 → 船首平台：一階踏板（走道頂 ＋1），梯子 bow（匯入檢查 v1：船首平台沒有梯子通到）
    co = V(plan['layout']['corsia'])
    bpl = V(plan['layout']['bow_platform'])
    zc = int(tz[co['x1']]) + co['h']
    xs_ = co['x1'] + 1
    for dy in range(-2, 3):
        parts['ladder'][(xs_, YC + dy, zc + 1)] = C_WOOD
    bow_pts = {'foot': (co['x1'] - 2, YC, zc + 1), 'lo': (xs_, YC, zc + 2), 'hi': (xs_, YC, zc + 2), 'head': (bpl['x0'] + 1, YC, bpl['top'] + 1)}
    for nm, p in bow_pts.items():
        assert not (occ[p] or p in parts['ladder']), ('船首梯子點不是空格', nm, p)
        q = (p[0], p[1], p[2] - 1)
        assert occ[q] or q in parts['ladder'], ('船首梯子點腳下不是實心', nm, p)
    lad_hits += sum(1 for dy in range(-2, 3) if occ[xs_, YC + dy, zc + 1])
    # ── 四爪錨：新通用部件；掛在船首平台前緣兩角外側（ring 在胸牆頂），往外 45°；搜 dy 讓它不碰 ──
    an = hp['anchor']
    acells, aanc, asize = grapnel(an['len_m'], an['span_m'])
    bp = V(plan['layout']['bow_platform'])
    Q = np.array(list(acells.keys()), float)
    S = (Q[:, None, :] + DG.OFFS[None]).reshape(-1, 3)
    anchors_m = []
    for side, sg in (('S', 1), ('P', -1)):
        best = None
        for x in (314.5, 312.5, 310.5, 316.5):
            for out_ in range(2, 9):
                ys = np.where(occ[int(x), :, bp['top'] + bp['wall_h']])[0]
                hw = int(np.abs(ys - YC).max())
                m = {'at': [x, YC + 0.5 + sg * (hw + out_), bp['top'] + bp['wall_h'] + 1], 'pivot': list(np.array(aanc['ring']) + [0.5, 0.5, 1.0]),
                     'rotate': [0, 0, 45 * sg], 'scale': 0.5, 'mirror': ''}
                h = DG.hits(allocc, DG.place(S, m))
                crown = DG.place(np.array([aanc['crown']], float) + 0.5, m)[0]
                if h == 0 and crown[2] > plan['waterline']['z'] + 1:
                    best = (m, out_, crown)
                    break
            if best:
                break
        assert best, ('錨放不下', side)
        m, out_, crown = best
        hz = (int(best[0]['at'][0]), YC + sg * (int(np.abs(np.where(hull[int(best[0]['at'][0]), :, 18])[0] - YC).max()) if hull[int(best[0]['at'][0]), :, 18].any() else 4), 18)
        anchors_m.append({'name': 'anchor-' + side, 'work': 'kotoko-fusta-01m-anchor-grapnel', 'at': m['at'], 'pivot': m['pivot'], 'rotate': m['rotate'], 'scale': 0.5,
                          'meta': {'kind': 'anchor', 'anchor': 'bower', 'hawse': '%d,%d,%d' % hz}, 'crown_z': round(float(crown[2]), 2), 'out': out_})
    # ── 甲板 meta ──
    deck_main_floor = ','.join('%d:%d' % (x, tz[x] + 1) for x in range(44, 317, 12))
    co = V(plan['layout']['corsia'])
    walk = ['%d:%d' % (x, tz[x] + 1) for x in (60, 75, co['x0'] - 3)] + ['%d:%d' % (co['x0'] - 2, tz[co['x0'] - 2] + 2), '%d:%d' % (co['x0'] - 1, tz[co['x0'] - 1] + 3)]
    walk += ['%d:%d' % (x, tz[x] + co['h'] + 1) for x in range(co['x0'], co['x1'] + 1, 12)] + ['%d:%d' % (co['x1'], tz[co['x1']] + co['h'] + 1)]
    walk += ['%d:%d' % (bp['x0'], bp['top'] + 1), '%d:%d' % (bp['x1'] - 1, bp['top'] + 1)]
    decks = [('link', '甲板-hold', {'kind': 'deck', 'deck': 'hold', 'level': 0, 'name': '艙底（藥庫）', 'floor': '%d:%d,%d:%d' % (fl['x0'], zf + 1, fl['x1'], zf + 1), 'thick': 2}),
             ('link', '甲板-main', {'kind': 'deck', 'deck': 'main', 'level': 1, 'name': '甲板（中央走道與划手座）', 'floor': deck_main_floor, 'walk': ','.join(walk), 'thick': 2}),
             ('link', '甲板-bow', {'kind': 'deck', 'deck': 'bow', 'level': 2, 'name': '船首平台', 'floor': '%d:%d,%d:%d' % (bp['x0'], bp['top'] + 1, bp['x1'], bp['top'] + 1), 'thick': 1})]
    R = {'cells': {k: len(v) for k, v in parts.items()}, 'rudder_hits': rud_hits, 'hinge': hinge, 'axis': [round(float(v), 5) for v in ax],
         'stock_top': stock_top, 'store_hits': store_hits, 'magazine_headroom_cells': [min(head_in), max(head_in)], 'ladder_hits': lad_hits, 'ladder_hit_cells': lad_hit_cells,
         'ladder_points': {'foot': foot, 'lo': lo, 'hi': hi, 'head': head}, 'anchors': [{k: a[k] for k in ('name', 'at', 'crown_z', 'out')} for a in anchors_m],
         'anchor_cells': len(acells)}
    if probe:
        print(json.dumps({'probe': probe, 'magazine_headroom_cells': R['magazine_headroom_cells'], 'magazine_headroom_m': round(min(head_in) * 0.1, 2)}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'hold'), exist_ok=True)
    sha = {}
    for k, cells in list(parts.items()) + [('anchor', acells)]:
        fn = os.path.join(HERE, 'masks', 'hold', k + '.vox.txt')
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 越嶺號 %s（draft_hold.py）x,y,z,color —— %s\n' % (k, '元件自己的座標（0.05 m；錨幹 +z、ring 在上）' if k == 'anchor' else 'at 0,0,0'))
            f.write(''.join('%d,%d,%d,%d\n' % (p[0], p[1], p[2], c) for p, c in sorted(cells.items())))
        sha[k] = hashlib.sha256(open(fn, 'rb').read()).hexdigest()
    R['sha256'] = sha
    rud_meta = {'kind': 'rudder', 'hinge_x': hinge[0], 'hinge_y': hinge[1], 'hinge_z': hinge[2], 'axis_x': R['axis'][0], 'axis_y': 0, 'axis_z': R['axis'][2],
                'max_deg': ru['max_deg'], 'turn_axis': 'hinge', 'spin': 'rudder', 'spin_k': ru['max_deg'], 'spin_min': -ru['max_deg'], 'spin_max': ru['max_deg'], 'spin_lag': 0.3}
    out = {'rudder': {'at': list(hinge), 'pivot': list(hinge), 'meta': rud_meta, 'stock_top': stock_top},
           'stores': stores, 'anchors': anchors_m,
           'anchor_component': {'work': 'kotoko-fusta-01m-anchor-grapnel', 'size': list(asize), 'anchors': {k: list(v) for k, v in aanc.items()}, 'cells': len(acells)},
           'ladders': [{'name': 'hold', 'points': {k: list(v) for k, v in R['ladder_points'].items()}}, {'name': 'bow', 'points': {k: list(v) for k, v in bow_pts.items()}}],
           'magazine_meta': {'kind': 'magazine', 'pos': 'aft', 'powder_lb': 100 * len(stores), 'hoist': '甲板-main/梯子/hold'},
           'decks': [[a, b, c] for a, b, c in decks]}
    with open(os.path.join(HERE, 'hold_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_hold.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
