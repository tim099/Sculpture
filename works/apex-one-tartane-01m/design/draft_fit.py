# 塔爾塔納 步驟 10（TASK-1299）：主貨艙格柵艙蓋（kind=door）、小艇架＋共用小艇、前甲板絞盤、艉樓羅經櫃、雙尾燈、貨艙貨箱與貨桶
#   用法：python -I -X utf8 draft_fit.py <design> [--probe=hatch_dz=+1 | --probe=nokind=小艇]
import sys, os, json, math, hashlib, subprocess, tempfile
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from wio import export_list
from gunsim import Grid, Gun

NX, NY, NZ = 360, 192, 320


def export_parts(work):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + work, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(out):
            raise SystemExit('匯出 parts 失敗：' + (r.stdout + r.stderr)[-800:])
        return json.load(open(out, encoding='utf-8'))


def write_list(path, cells):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 塔爾塔納 步驟 10（draft_fit.py）\n')
        for c in sorted(cells):
            f.write('%d,%d,%d,%d\n' % c)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe='))
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    FB = plan['fit_build']
    HT, SK, MS = FB['hatch'], FB['skids'], FB['models']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    YC = plan['space']['yc']

    A = export_list(FB['assembly'], None, links=None)
    own_v = set()
    if os.path.exists(os.path.join(WORKS, SK['work'], 'work.json')):
        own_v |= set(map(tuple, export_list(SK['work'], None)[:, :3].tolist()))
    A = np.array([r for r in A.tolist() if tuple(r[:3]) not in own_v], np.int32)
    S = np.zeros((NX, NY, NZ), bool)
    S[A[:, 0], A[:, 1], A[:, 2]] = True

    own_names = {HT['name']} | {m['name'] for m in MS}
    ext_boxes = [(m['path'], m['box']) for m in export_parts(FB['assembly'])['models'] if m['path'].split('/')[-1] not in own_names]

    def box_hits(b):
        return [n for n, o in ext_boxes if b[0] < o[3] and o[0] < b[3] and b[1] < o[4] and o[1] < b[4] and b[2] < o[5] and o[2] < b[5]]

    # ── 1. 主貨艙格柵艙蓋（kind=door, open=up, open_deg=35） ──
    dz_h = int(probe.get('hatch_dz', 0))
    hz0 = HT['z'] + dz_h
    X, Y = HT['x1'] - HT['x0'] + 1, HT['y1'] - HT['y0'] + 1
    C = HT['colors']
    hcells = set()
    for x in range(X):
        for y in range(Y):
            edge = x in (0, X - 1) or y in (0, Y - 1)
            mid = x == X // 2
            hcells.add((x, y, 0, C['frame'] if (edge or mid) else (C['batten'] if y % 2 == 1 else C['plank'])))
    for x in (1, X // 2, X - 2):
        for y in range(1, Y - 1):
            hcells.add((x, y, 1, C['frame']))
    hcells.add((5, Y - 2, 1, C['iron']))
    hcells.add((X - 6, Y - 2, 1, C['iron']))

    hatch_solid = sum(1 for (x, y, z, _) in hcells if S[HT['x0'] + x, HT['y0'] + y, hz0 + z])
    zt = hz0 - 1
    opening = [(x, y) for x in range(HT['x0'], HT['x1'] + 1) for y in range(HT['y0'], HT['y1'] + 1) if not S[x, y, zt]]
    through = sum(1 for (x, y) in opening if not S[x, y, zt - 3:zt].any())
    rim_solid = sum(1 for x in range(HT['x0'], HT['x1'] + 1) for y in range(HT['y0'], HT['y1'] + 1) if S[x, y, zt])
    if probe:
        if 'hatch_dz' in probe:
            print(json.dumps({'probe': 'hatch_dz=' + probe['hatch_dz'], 'z0': hz0, 'opening_z': zt, 'opening_empty': len(opening), 'opening_through': through, 'hit_solid': hatch_solid}, ensure_ascii=False))
            return

    # ── 2. 小艇架（船腰兩座橫架＋中線縱向龍骨托樑） ──
    skids = {}
    for x0, x1 in SK['xs']:
        for x in range(x0, x1 + 1):
            for y in SK['post_ys']:
                z_deck = max(z for z in range(18, 30) if S[x, y, z])
                for z in range(z_deck + 1, SK['beam_z0']):
                    skids[(x, y, z)] = SK['color']
            for y in range(SK['y_lo'], SK['y_hi'] + 1):
                for z in (SK['beam_z0'], SK['beam_z1']):
                    skids[(x, y, z)] = SK['color']
    for x in range(SK['xs'][0][1] + 1, SK['xs'][-1][0]):
        for y in SK['cradle_y']:
            skids[(x, y, SK['beam_z1'])] = SK['color']
    skid_hits = sum(1 for k in skids if S[k])
    skid_posts_ok = all(S[x, y, max(z for z in range(18, 30) if S[x, y, z])] for x0, x1 in SK['xs'] for x in range(x0, x1 + 1) for y in SK['post_ys'])
    skid_mirror_diff = sum(1 for (x, y, z), c in skids.items() if skids.get((x, 2 * YC - y, z)) != c)

    # 把小艇架格加入格網給外部模型做腳下與碰撞量測
    S2 = S.copy()
    for x, y, z in skids:
        S2[x, y, z] = True
    G = Grid(np.argwhere(S2), outside=False)

    cache = {}
    def src(w):
        if w not in cache:
            cache[w] = export_list(w, None)
        return cache[w]

    rows = []
    coll, nofoot, nometa, m_box_hits = {}, [], [], []
    for m in MS:
        g = Gun(m['name'], m, src(m['work']), {}, 0.2)
        at = list(m['at'])
        if at[2] is None:
            # 依底部腳印找地面（限定合理層高範圍避免誤踩上層甲板）
            max_search = 18 if 'deck-hold' in m['host'] else (46 if m['name'].startswith('尾燈') else 40)
            bot = g.world(g.bottom, (at[0], at[1], 0.0), m['rotate'], False)
            xys = set(map(tuple, np.floor(bot[:, :2]).astype(int).tolist()))
            zfoot = max(z for (bx, by) in xys for z in range(0, max_search) if S2[bx, by, z])
            at[2] = float(zfoot + 1)
        meta = dict(m['meta'])
        if probe.get('nokind') == m['name']:
            meta = {k: v for k, v in meta.items() if k not in ('kind', 'deco')}
        P = g.world(g.samples, at, m['rotate'], False)
        k = int(G.hit(P).sum())
        if k:
            coll[m['name']] = k
        lo, hi = g.bbox(at, m['rotate'], False)
        cx, cy, fz = int(math.floor((lo[0] + hi[0]) / 2)), int(math.floor((lo[1] + hi[1]) / 2)), int(math.floor(lo[2])) - 1
        d = next((dd for dd in range(0, FB['foot_reach'] + 1) if G.solid(cx, cy, fz - dd)), None)
        if d is None:
            nofoot.append(m['name'])
        if 'kind' not in meta and 'deco' not in meta:
            nometa.append(m['name'])
        bh = box_hits([float(lo[0]), float(lo[1]), float(lo[2]), float(hi[0]), float(hi[1]), float(hi[2])])
        if bh:
            m_box_hits.append([m['name'], bh])
        rows.append({'name': m['name'], 'host': m['host'], 'work': m['work'], 'at': [round(float(v), 3) for v in at],
                     'pivot': m['pivot'], 'scale': m['scale'], 'rotate': m['rotate'], 'meta': meta,
                     'foot_gap': d, 'box': [round(float(v), 2) for v in list(lo) + list(hi)], '_g': g, '_box': (lo, hi)})

    if 'nokind' in probe:
        print(json.dumps({'probe': 'nokind=' + probe['nokind'], 'no_meta': nometa}, ensure_ascii=False))
        return

    overlap = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            (alo, ahi), (blo, bhi) = a['_box'], b['_box']
            if np.any(ahi <= blo) or np.any(bhi <= alo):
                continue
            gb = b['_g']
            P = a['_g'].world(a['_g'].centers, a['at'], a['rotate'], False)
            q = P - np.array(b['at'], float)
            c, sn = math.cos(math.radians(-b['rotate'])), math.sin(math.radians(-b['rotate']))
            loc = np.stack([q[:, 0] * c - q[:, 1] * sn, q[:, 0] * sn + q[:, 1] * c, q[:, 2]], -1) / gb.scale + gb.pivot
            cells_b = set(map(tuple, gb.cells.astype(int).tolist()))
            hitn = sum(1 for t_ in np.floor(loc).astype(int).tolist() if tuple(t_) in cells_b)
            if hitn:
                overlap.append([a['name'], b['name'], hitn])
    for r in rows:
        r.pop('_g'); r.pop('_box')

    # ── 3. 檢查繩梯／樓梯／人行道淨空 ──
    lp = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
    lad_hits = []
    for ln, info in lp.items():
        for pk, pt in info['points'].items():
            px, py, pz = pt
            for r in rows:
                b = r['box']
                if b[0] - 1 <= px + 0.5 <= b[3] + 1 and b[1] - 1 <= py + 0.5 <= b[4] + 1 and b[2] <= pz + 12 and pz <= b[5]:
                    lad_hits.append([ln, pk, r['name']])

    p_hatch = os.path.join(design, 'masks', 'fit', 'hatch-main.vox.txt')
    p_skids = os.path.join(design, 'masks', 'fit', 'skids.vox.txt')
    write_list(p_hatch, hcells)
    write_list(p_skids, [(x, y, z, c) for (x, y, z), c in skids.items()])

    verify = {
        'hatch': {'name': HT['name'], 'cells': len(hcells), 'box': [HT['x0'], HT['y0'], hz0, HT['x1'] + 1, HT['y1'] + 1, hz0 + 2],
                  'hit_solid': hatch_solid, 'hit_models': box_hits([HT['x0'], HT['y0'], hz0, HT['x1'] + 1, HT['y1'] + 1, hz0 + 2]),
                  'opening_z': zt, 'opening_cells': len(opening), 'opening_through': through, 'rim_solid': rim_solid,
                  'open_max_z': round(hz0 + Y * math.sin(math.radians(HT['open_deg'])), 2),
                  'mirror_diff': sum(1 for (x, y, z, c) in hcells if (x, Y - 1 - y, z, c) not in hcells)},
        'skids': {'cells': len(skids), 'hit_solid': skid_hits, 'posts_touch_deck': skid_posts_ok, 'mirror_diff': skid_mirror_diff,
                  'walkway_port_y': '79..88 (1.0 m)', 'walkway_stbd_y': '104..115 (1.2 m)'},
        'models': len(rows), 'model_collisions': coll, 'no_foot_within_12': nofoot, 'no_meta': nometa,
        'model_overlap': overlap, 'existing_model_hits': m_box_hits, 'ladder_clearance_hits': lad_hits,
        'sha256': {'hatch': hashlib.sha256(open(p_hatch, 'rb').read()).hexdigest(),
                   'skids': hashlib.sha256(open(p_skids, 'rb').read()).hexdigest()}
    }
    place = {
        'note': 'draft_fit.py（步驟 10）產生；tools/build_fit.py 照它落格與掛載模型',
        'hatch': {'name': HT['name'], 'work': HT['work'], 'title': HT['title'], 'host': HT['host'],
                  'size': [X, Y, 2], 'at': [HT['x0'], HT['y0'], hz0], 'mask': 'masks/fit/hatch-main.vox.txt',
                  'anchors': {'hinge-a': [0, 0, 0], 'hinge-b': [X - 1, 0, 0]},
                  'meta': {'kind': 'door', 'open': 'up', 'open_deg': HT['open_deg']}},
        'skids': {'work': SK['work'], 'title': SK['title'], 'link': SK['link'], 'mask': 'masks/fit/skids.vox.txt'},
        'models': rows
    }
    json.dump(place, open(os.path.join(design, 'fit_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(verify, open(os.path.join(design, 'verify_fit.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(verify, ensure_ascii=False))


if __name__ == '__main__':
    main()
