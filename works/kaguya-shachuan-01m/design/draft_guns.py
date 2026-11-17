# 出處：kaguya-guineaman-01m/design/draft_guns.py
# 沙船 步驟 9（TASK-1313）：砲 —— 全部是外部模型，掛在所在甲板的子作品上
#   主甲板（deck-main）：x=180 兩舷各 1 門 4 磅砲（pinnacle 4l ×0.5）從低舷牆砲門打；
#   佛郎機迴旋砲 pierrier（4 門）：尾樓舷頂 x=64、前舷頂 x=228（皇家號共用件 ×0.5 ＋ 座雙生）
#   用法：python -I -X utf8 draft_guns.py <design> [--probe=push=<砲名>:<格>]
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
from wio import export_list
from gunsim import Grid, load_guns


def r3(v):
    return [round(float(c), 3) for c in v]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    GB = plan['guns_build']
    S = GB['search']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list(GB['assembly'], None, links=None)
    G = Grid(A, pad=16)
    H = export_list(GB['hull'], None)
    Hs = set(map(tuple, H[:, :3].tolist()))
    decks = {}
    for k, w in GB['deck_works'].items():
        top = {}
        for x, y, z in export_list(w, None)[:, :3].tolist():
            if z + 1 > top.get((x, y), -1):
                top[(x, y)] = z + 1
        decks[k] = top
    guns = load_guns(GB, WORKS, export_list)

    def hull_y(x, z, side):
        ys = [y for y in range(0, 2 * plan['space']['yc'] + 1) if (x, y, z) in Hs]
        return (max(ys) + 1) if side > 0 else min(ys)

    def deck_top(dk, pts):
        zs = [decks[dk][p] for p in pts if p in decks[dk]]
        return max(zs) if zs else None

    def place(g, base_xy, d_out, phi, mirror, zd, offs, beyond_fn):
        best = None
        d_side = np.array([d_out[1], -d_out[0]])
        for dz in S['dz']:
            for off in offs:
                for k in range(int(S['back_max'] / S['step']) + 1):
                    back = k * S['step']
                    b = np.array(base_xy, float) + d_side * off - d_out * back
                    at = (float(b[0]), float(b[1]), float(zd + dz))
                    if G.hit(g.world(g.samples, at, phi, mirror)).any():
                        continue
                    tip = g.world(g.anchors['muzzle'][None], at, phi, mirror)[0]
                    beyond = beyond_fn(tip)
                    tip_free = not G.hit(tip[None])[0]
                    bot = g.world(g.bottom, at, phi, mirror)
                    below = bot.copy()
                    below[:, 2] -= 1.0
                    sup = float(G.hit(below).mean())
                    ok = bool(beyond > 0 and tip_free and sup >= GB['support_min'])
                    cand = {'at': r3(at), 'phi': phi, 'back': back, 'off': off, 'dz': dz, 'muzzle_beyond': round(float(beyond), 2),
                            'muzzle_free': tip_free, 'support': round(sup, 3), 'axis_z': round(float(tip[2]), 2), 'ok': ok}
                    key = (not ok, dz, back, abs(off))
                    if best is None or key < best[0]:
                        best = (key, cand)
                    break
        return best

    rows = []
    # ── 前腰露天 4 磅砲（plan['ports']['gun']，與 draft_ports.py 同源）──
    gp = plan['ports']['gun']
    for i, gx in enumerate(gp['x'], 1):
        x0, x1 = gx - gp['w'] // 2, gx + gp['w'] // 2 - (1 if gp['w'] % 2 == 0 else 0)
        z0, z1 = 27, 31
        g = guns[gp['gun']]
        xc = (x0 + x1 + 1) / 2.0
        zm = (z0 + z1) // 2 - 1  # z=28 實心門柱層
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            outs = [hull_y(x, zm, side) for x in (x0 - 2, x1 + 2)]
            outer = max(outs) if side > 0 else min(outs)
            yin = [outer - side * d for d in (8, 12, 16)]
            zd = deck_top('main', [(x, y) for x in (x0, int(xc), x1) for y in yin])
            d_out = g.direction(0.0, mirror)
            best = place(g, (xc, outer), d_out, 0.0, mirror, zd, S['dx'], lambda tip: (tip[1] - outer) * side)
            r = {'deck': 'main', 'port': i, 'side': nm, 'type': gp['gun'], 'chase': False, 'outer': outer, 'deck_z': zd,
                 'opening': {'x': [x0, x1], 'z': [z0, z1]}}
            r.update(best[1] if best else {'ok': False, 'at': None})
            rows.append(r)

    # ── 佛郎機迴旋砲（舷頂）──
    gs = guns['pierrier']
    from gunsim import Gun
    mt_cfg = GB['types']['pierrier']
    gm = Gun('pierrier_mount', {'work': mt_cfg['mount_work'], 'scale': mt_cfg['scale'], 'pivot': mt_cfg['pivot'], 'meta': {}},
             export_list(mt_cfg['mount_work'], None), {}, S['inset'])
    for sw in GB['swivels']:
        x = sw['x']
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            zs = [z for (xx, y, z) in Hs if xx == x]
            ztop = max(zs)
            ys = [y for (xx, y, z) in Hs if xx == x and z == ztop]
            yr = (max(ys) - 1) if side > 0 else (min(ys) + 1)
            outer = (max(ys) + 1) if side > 0 else min(ys)
            best = None
            for dz in range(1, 5):
                at = (x + 0.5, yr + 0.5, float(ztop + dz))
                if G.hit(gs.world(gs.samples, at, 0.0, mirror)).any():
                    continue
                if G.hit(gm.world(gm.samples, at, 0.0, mirror)).any():
                    continue
                tip = gs.world(gs.anchors['muzzle'][None], at, 0.0, mirror)[0]
                beyond = (tip[1] - outer) * side
                tip_free = not G.hit(tip[None])[0]
                best = {'at': r3(at), 'phi': 0.0, 'back': 0, 'off': 0, 'dz': dz, 'muzzle_beyond': round(float(beyond), 2), 'muzzle_free': tip_free,
                        'support': 1.0, 'axis_z': round(float(tip[2]), 2), 'ok': bool(beyond > 0 and tip_free)}
                break
            r = {'deck': sw['deck'], 'port': 'sw%d' % x, 'side': nm, 'type': 'pierrier', 'chase': False, 'outer': outer, 'deck_z': ztop}
            r.update(best or {'ok': False, 'at': None})
            rows.append(r)

    # ── 命名與 ID ──
    cnt = {}
    for r in rows:
        pre = GB['prefix'][r['deck']]
        kind = '迴旋砲' if r['type'] == 'pierrier' else '砲'
        cnt[(kind, pre, r['side'])] = cnt.get((kind, pre, r['side']), 0) + 1
        r['name'] = '%s%s-%s%02d' % (kind, pre, r['side'], cnt[(kind, pre, r['side'])])
    rows.sort(key=lambda r: (r['type'] == 'pierrier', list(GB['prefix']).index(r['deck']), r['side'], str(r['port'])))
    for i, r in enumerate(rows, 1):
        r['id'] = 'gun-%d' % i

    def cells_of(r, dpush=0.0):
        g = guns[r['type']]
        at = np.array(r['at'], float)
        if dpush:
            d = g.direction(r['phi'], r['side'] == 'P')
            at[:2] += d * dpush
        return g.world(g.samples, at, r['phi'], r['side'] == 'P')

    if probe:
        nm, d = probe[0].split('=', 1)[1].rsplit(':', 1)
        rep = {}
        for r in rows:
            n = int(G.hit(cells_of(r, float(d) if r['name'] == nm else 0.0)).sum())
            if n:
                rep[r['name']] = n
        print(json.dumps({'probe': probe[0], 'hit_samples_by_gun': rep}, ensure_ascii=False))
        return

    occ, clash = {}, []
    for r in rows:
        g = guns[r['type']]
        P = g.world(g.centers, r['at'], r['phi'], r['side'] == 'P')
        for c in set(map(tuple, np.floor(P).astype(int).tolist())):
            if c in occ and occ[c] != r['name']:
                clash.append([r['name'], occ[c]])
                break
            occ[c] = r['name']

    YC = plan['space']['yc']
    asym = []
    by = {(r['deck'], str(r['port']), r['side']): r for r in rows}
    for (dk, pt, sd), r in by.items():
        if sd != 'S':
            continue
        q = by.get((dk, pt, 'P'))
        if q and (abs(r['at'][0] - q['at'][0]) > 1e-6 or abs((2 * YC + 1 - r['at'][1]) - q['at'][1]) > 1e-6 or r['at'][2] != q['at'][2] or r['phi'] != -q['phi']):
            asym.append([r['name'], q['name'], r['at'], q['at']])

    v = {'read': {'assembly_voxels': int(len(A)), 'hull_voxels': int(len(H))}, 'guns': len(rows),
         'by_deck_type': {}, 'not_ok': [[r['name'], r.get('muzzle_beyond'), r.get('muzzle_free'), r.get('support')] for r in rows if not r['ok']],
         'gun_gun_clash': clash, 'asymmetric_pairs': asym}
    for r in rows:
        k = '%s/%s' % (r['deck'], r['type'])
        v['by_deck_type'][k] = v['by_deck_type'].get(k, 0) + 1
    for f in ('back', 'muzzle_beyond', 'support', 'axis_z', 'dz'):
        v[f] = {k: [min(r[f] for r in rows if '%s/%s' % (r['deck'], r['type']) == k), max(r[f] for r in rows if '%s/%s' % (r['deck'], r['type']) == k)] for k in v['by_deck_type']}
    json.dump({'note': 'draft_guns.py 的結果；at ＝ 模型的 at（pivot 落點）、phi ＝ rotate z、P 舷 mirror=y', 'rows': rows},
              open(os.path.join(design, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
