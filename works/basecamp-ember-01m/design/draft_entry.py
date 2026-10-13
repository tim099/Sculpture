# 餘燼號 階段十三 entry port 與 side steps（plan.json entry_build；新圖紙 13）—— 憲法號 draft_entry.py（新圖紙 23 v1.1）照換算
#   開口：船殼本來就有（憲法號的 entry port 跟著 z ≥ 109 抬 23：x 374–382、z 130 起）⇒ 不刻。
#   踏階：水線抬到 71 之後，從 z 74 每 4 格一道到 126（上甲板面 129 之下）；一道 1 格高、從那一欄的船殼外面貼上去凸出 depth 格（外面齊平）；
#         最下一道照 v1.1 加寬到開口寬、凸出 4 ⇒ man rope 下端埋在它外側兩角。
#   柱：開口兩側 cap rail 最外那一格的上面，頂 z_top；man rope：柱頂外面那一格 → 最下一道外側兩角（拉直）。
#   ⇒ masks/entry/side.vox.txt（一舷、自己的座標）、entry_anchors.json、entry_ropes.json、verify_entry.json
# 用法：python -I draft_entry.py <design 資料夾>
import sys, os, json, hashlib, collections
import numpy as np

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import draft_profile as DP                               # noqa: E402
from draft_ladders import existing_links, export_hidden  # noqa: E402
import place_guns as PG                                  # noqa: E402

YC = 160


def seg_clearance(p, q, solid, radius, n=800, skip=1.0):
    p, q = np.array(p, float), np.array(q, float)
    best = (1e9, None, None)
    Ln = np.linalg.norm(q - p)
    for t in np.linspace(0, 1, n):
        if t * Ln < skip or (1 - t) * Ln < skip:
            continue
        x = p + (q - p) * t
        b = np.floor(x).astype(int)
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                for dz in (-2, -1, 0, 1, 2):
                    k = (b[0] + dx, b[1] + dy, b[2] + dz)
                    if k in solid:
                        lo = np.array(k, float)
                        d = np.linalg.norm(np.maximum(np.maximum(lo - x, 0), x - (lo + 1)))
                        if d - radius < best[0]:
                            best = (d - radius, [round(float(v), 2) for v in x], [int(v) for v in k])
    return best


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
    P = plan['entry_build']
    h = DP.export_list(P['hull'], links='none')
    H = {(int(x), int(y), int(z)): int(c) for x, y, z, c in h if 355 <= x <= 400}
    have = set(existing_links(P['assembly']))
    hide = [l for l in P['hide_links'] if l in have]
    a = export_hidden(P['assembly'], hide)
    assert len(a) == P['assembly_voxels'], ('組裝件現況對不上', len(a))
    A = {(int(x), int(y), int(z)) for x, y, z, c in a if 340 <= x <= 420}
    # 砲模型的格也算實心（踏階、繩不准碰到砲口）
    GB = plan['guns_build']
    rows = json.load(open(os.path.join(D, 'guns_placement.json'), encoding='utf-8'))['rows']
    for r in rows:
        if not (330 <= r['at'][0] <= 430):
            continue
        t = GB['types'][r['type']]
        src = os.path.join(D, t['cells']) if t['cells'].startswith('masks/') else t['cells']
        g = PG.Gun(r['type'], t['work'], PG.load_cells(src), t['scale'], t['pivot'], t['muzzle'], t['meta'])
        A |= set(map(tuple, np.floor(g.world(g.samples, r['at'], r['phi'], r['side'] == 'P')).astype(int).tolist()))
    # 開口確認：x 範圍、z ≥ z_from 的 S 舷舷牆沒有船殼格
    xa, xb = P['opening']['x']
    left = [k for k in H if xa <= k[0] <= xb and k[2] >= P['opening']['z_from'] and k[1] >= P['opening']['y_min_S']]
    steps, step_rows = {}, []
    sx0, sx1 = P['steps']['x']
    bot = P['steps']['bottom']
    zs = list(range(P['steps']['z0'], P['steps']['z1'] + 1, P['steps']['step']))
    for z in zs:
        x0_, x1_, depth = (bot['x'][0], bot['x'][1], bot['depth']) if z == zs[0] else (sx0, sx1, P['steps']['depth'])
        yout = {x: max(k[1] for k in H if k[0] == x and k[2] == z and k[1] > YC) for x in range(x0_, x1_ + 1)}
        face = max(yout.values()) + depth
        for x in range(x0_, x1_ + 1):
            for y in range(yout[x] + 1, face + 1):
                steps[(x, y, z)] = P['steps']['color']
        step_rows.append({'z': z, 'x': [x0_, x1_], 'hull_y_out': [min(yout.values()), max(yout.values())], 'face_y': face,
                          'hull_colors': dict(collections.Counter(H[(x, yout[x], z)] for x in yout))})
    posts, post_rows = {}, []
    for x in P['posts']['x']:
        ys = [k[1] for k in H if k[0] == x and k[2] >= P['posts']['search_z']]
        y = max(ys)                                            # cap rail 最外那一格
        base = max(k[2] for k in H if k[0] == x and k[1] == y)
        for z in range(base + 1, P['posts']['z_top'] + 1):
            posts[(x, y, z)] = P['posts']['color']
        post_rows.append({'x': x, 'y': y, 'base_z': base, 'base_color': H[(x, y, base)], 'z': [base + 1, P['posts']['z_top']]})
    side = dict(steps)
    side.update(posts)
    hit = sorted(k for k in side if k in A)
    # 固定點
    zb = zs[0]
    rb = step_rows[0]
    pa, pf = P['posts']['x']
    zt = P['posts']['z_top']
    cell = {'post-aft.top': (pa, post_rows[0]['y'] + 1, zt), 'post-fwd.top': (pf, post_rows[1]['y'] + 1, zt),
            'step-1.aft': (rb['x'][0], rb['face_y'], zb), 'step-1.fwd': (rb['x'][1], rb['face_y'], zb)}
    assert all(cell[k] in steps for k in ('step-1.aft', 'step-1.fwd')), '下端固定點沒有落在最下一道踏階上'
    assert not [k for k in ('post-aft.top', 'post-fwd.top') if cell[k] in side], '柱頂固定點落在實心格上'
    xs_, ys_, zs_ = zip(*(list(side) + list(cell.values())))
    at = [min(xs_), min(ys_), min(zs_)]
    size = [max(xs_) - at[0] + 1, max(ys_) - at[1] + 1, max(zs_) - at[2] + 1]
    world = {k: [c[0] + 0.5, c[1] + 0.5, c[2] + 0.5] for k, c in cell.items()}
    local = {k: [c[0] - at[0], c[1] - at[1], c[2] - at[2]] for k, c in cell.items()}
    R = P['manropes']
    ropes, clear = [], []
    solid = A | set(side)
    mir = lambda k: (k[0], 2 * YC - k[1], k[2])
    for sd, link in (('S', P['link']), ('P', P['mirror_link'])):
        for end in ('aft', 'fwd'):
            ropes.append({'name': 'entry-%s.manrope-%s' % (sd, end), 'from': '%s/post-%s.top' % (link, end), 'to': '%s/step-1.%s' % (link, end),
                          'thickness': R['thickness'], 'slack': R['slack'], 'color': R['color'], 'group': R['group']})
    for end in ('aft', 'fwd'):
        d, pt, k = seg_clearance(world['post-%s.top' % end], world['step-1.%s' % end], solid, R['thickness'] / 2)
        clear.append({'end': end, 'min_clear': round(d, 2), 'at': pt, 'cell': k})
    # P 舷：鏡過去也不撞
    hitP = sorted(k for k in side if mir(k) in A)
    out = os.path.join(D, 'masks', 'entry')
    os.makedirs(out, exist_ok=True)
    rows_ = sorted((k[0] - at[0], k[1] - at[1], k[2] - at[2], c) for k, c in side.items())
    p = os.path.join(out, 'side.vox.txt')
    open(p, 'w', encoding='utf-8', newline='\n').write('# side —— entry port 柱與 side steps 一舷（自己的座標，at=%d,%d,%d、size %s；另一舷 mirror=y、at.y ＝ %d）（%d 格）\n' % (
        at[0], at[1], at[2], size, 321 - at[1] - size[1], len(rows_)) + '\n'.join('%d,%d,%d,%d' % r for r in rows_) + '\n')
    json.dump({'at': at, 'size': size, 'mirror_at_y': 321 - at[1] - size[1], 'anchors': [{'name': k, 'at': local[k], 'world_S': world[k]} for k in cell]},
              open(os.path.join(D, 'entry_anchors.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump({'ropes': ropes}, open(os.path.join(D, 'entry_ropes.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    v = {'read': {'assembly_voxels': int(len(a)), 'hidden': hide}, 'opening_hull_left': len(left), 'steps': step_rows, 'posts': post_rows,
         'cells': len(side), 'steps_cells': len(steps), 'posts_cells': len(posts), 'hit_S': len(hit), 'hit_P': len(hitP), 'first_hit': hit[:5],
         'box': {'at': at, 'size': size, 'mirror_at_y': 321 - at[1] - size[1]}, 'manrope_clearance': clear,
         'expect_assembly_after': int(len(a)) + 2 * len(side), 'file': {'cells': len(rows_), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}
    json.dump(v, open(os.path.join(D, 'verify_entry.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k != 'steps'}, ensure_ascii=False))
    for r in step_rows:
        print(r)


if __name__ == '__main__':
    main()
