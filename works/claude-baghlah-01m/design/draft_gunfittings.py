# Source: gura-pinas-01m/design/draft_gunfittings.py (Blue Shark, TASK-0967; itself from calli-cosecha-01m, TASK-0624) --
#   rewritten for the Star (TASK-0019 step 9).
# Star (al-Najm) gun fittings (Ship_Guns 4.4): for every 4l carriage gun two rings in the bulwark beside the port, one ring
#   in the deck behind the train; breeching x2, side tackle x2, train tackle x1. Swivels have no carriage ⇒ nothing.
#   · wall rings: from the gun's pivot go `offset` cells to either side, walk outward along the muzzle direction to the first
#     hull cell ⇒ the two air cells inside it (stem = iron through the wall, ring); height = that side's eye. The rope lines
#     (cascabel -> ring, eye -> ring) must not pass any other solid (the gun itself excluded), measured on both sides
#     (P = the S design mirrored); else the next offset; none ⇒ no ring, that side's ropes not hung (written down).
#   · deck ring: from the train go `back` cells inboard (and `lat` sideways, same for both sides), standing on the deck.
#   Differences from Blue Shark: solids are the design lists (draft_masts.ship_cells + masts + yards + rigging parts) plus
#     the gun models from guns_placement.json (no CLI export ⇒ reruns are byte-identical); guns from draft_guns.Gun.
#   Outputs: masks/gunfittings/gunfittings.vox.txt, gunfittings_points.json, gun_ropes.json, verify_gunfittings.json
#   Usage: python -X utf8 draft_gunfittings.py <design> [--probe=offset=<n>] (force one wall offset, print, write nothing)
import sys, os, json, math, hashlib, collections
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_guns as DG
from draft_masts import ship_cells, load


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe'))
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    GB, FB = plan['guns_build'], plan['gunfittings_build']
    if probe.get('offset'):
        FB['ring']['offset'] = [int(probe['offset'])]
    YC = plan['space']['yc']
    M = os.path.join(design, 'masks')
    occ = set(ship_cells(design, plan))
    hull = load(os.path.join(M, 'step4', 'hull4_01.vox.txt'))
    hull.update(load(os.path.join(M, 'step6', 'hull_recolor.vox.txt')))
    hull.update(load(os.path.join(M, 'step6', 'hull_add.vox.txt')))
    Hs = set(hull)
    for f in ('main', 'mizzen', 'jibboom', 'cable_beam'):
        occ |= set(load(os.path.join(M, 'masts', f + '.vox.txt')))
    for f in ('rings', 'stern_spars', 'halyard_bitt'):
        occ |= set(load(os.path.join(M, 'rigging', f + '.vox.txt')))
    guns = {k: DG.Gun(k, t, design, GB['search']['inset']) for k, t in GB['types'].items()}
    rows = {r['name']: r for r in json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))['rows']}
    gcells = {}
    for n, r in rows.items():
        g = guns[r['type']]
        gcells[n] = set(map(tuple, np.floor(g.world(g.samples, r['at'], r['phi'], r['side'] == 'P')).astype(int).tolist()))
    W = set(occ)
    for c in gcells.values():
        W |= c
    new, kind, anchors, ropes, notes = {}, {}, {}, [], []
    mir = lambda k: (k[0], 2 * YC - k[1], k[2])

    def pt(r, name):
        g = guns[r['type']]
        return g.world(g.anchors[name][None], r['at'], r['phi'], r['side'] == 'P')[0]

    def blocked(a, b, ignore):
        a, b = np.asarray(a, float), np.asarray(b, float)
        hit = []
        for t in np.linspace(0, 1, int(np.linalg.norm(b - a) * 3) + 2):
            q = tuple(int(math.floor(v)) for v in a + (b - a) * t)
            if q in ignore or q in new:
                continue
            if q in W:
                hit.append(q)
        return hit

    def ctr(k):
        return np.array(k, float) + 0.5

    deck_link = GB['deck_links']
    R = FB['ropes']
    pairs = [(n, n.replace('-S', '-P')) for n in rows if rows[n]['side'] == 'S' and not rows[n]['swivel']]
    stat = collections.Counter()
    for nS, nP in sorted(pairs):
        rS, rP = rows[nS], rows[nP]
        g = guns[rS['type']]
        d = g.direction(rS['phi'], False)
        da = (int(round(d[0])), int(round(d[1])))
        t = np.array([-d[1], d[0]])
        c2 = np.array(rS['at'][:2], float)
        z0 = int(rS['at'][2])
        for side in ('aft', 'fwd'):
            eye = pt(rS, 'eye-' + side)
            s = 1.0 if (eye[:2] - c2) @ t >= 0 else -1.0
            zr = int(math.floor(eye[2]))
            done = None
            for off in FB['ring']['offset']:
                p = c2 + t * s * off - d * 25
                face = None
                for k in np.arange(0, 80, 0.5):
                    q = p + d * k
                    cell = (int(math.floor(q[0])), int(math.floor(q[1])), zr)
                    if cell in Hs:
                        face = cell
                        break
                if face is None:
                    continue
                stem = (face[0] - da[0], face[1] - da[1], zr)
                ring = (stem[0] - da[0], stem[1] - da[1], zr)
                if any(c in W or c in new or mir(c) in W or mir(c) in new for c in (stem, ring)):
                    continue
                rc = ctr(ring)
                ign = gcells[nS] | {stem, ring}
                ignP = gcells[nP] | {mir(stem), mir(ring)}
                if blocked(pt(rS, 'cascabel'), rc, ign) or blocked(eye, rc, ign) or \
                        blocked(pt(rP, 'cascabel'), ctr(mir(ring)), ignP) or blocked(pt(rP, 'eye-' + side), ctr(mir(ring)), ignP):
                    continue
                done = (off, stem, ring)
                break
            if done is None:
                notes.append('%s / %s: no %s wall ring clear of solids ⇒ not placed, that side not hung' % (nS, nP, side))
                continue
            off, stem, ring = done
            stat['ring_offset_%d' % off] += 1
            for nm, rr, st, rg in ((nS, rS, stem, ring), (nP, rP, mir(stem), mir(ring))):
                new[st], kind[st] = FB['ring']['color'], 'ring'
                new[rg], kind[rg] = FB['ring']['color'], 'ring'
                an = 'ring-%s-%s' % (nm, side)
                anchors[an] = list(rg)
                gp = 'model:%s/%s' % (deck_link[rr['deck']], nm)
                ropes.append(dict(name='%s.breeching-%s' % (nm, side), **{'from': gp + '/cascabel', 'to': '%s/%s' % (FB['link'], an)}, **R['breeching']))
                ropes.append(dict(name='%s.tackle-%s' % (nm, side), **{'from': '%s/eye-%s' % (gp, side), 'to': '%s/%s' % (FB['link'], an)}, **R['tackle']))
        # deck ring
        tr = pt(rS, 'train')
        done = None
        for back, lat in [(b, l) for l in FB['deck_ring']['lat'] for b in FB['deck_ring']['back']]:
            q = tr[:2] - d * back + t * lat
            kx, ky = int(math.floor(q[0])), int(math.floor(q[1]))
            zk = next((z for z in range(z0, z0 - 4, -1) if (kx, ky, z - 1) in occ and (kx, ky, z) not in occ), None)
            if zk is None:
                continue
            k = (kx, ky, zk)
            if k in W or k in new or mir(k) in W or mir(k) in new or (k[0], 2 * YC - k[1], zk - 1) not in occ:
                continue
            if blocked(tr, ctr(k), gcells[nS] | {k}) or blocked(pt(rP, 'train'), ctr(mir(k)), gcells[nP] | {mir(k)}):
                continue
            done = (back, k, lat)
            break
        if done is None:
            notes.append('%s / %s: no deck ring ⇒ train tackle not hung' % (nS, nP))
        else:
            back, k, lat = done
            stat['deck_back_%d' % back + ('_lat%+d' % lat if lat else '')] += 1
            for nm, rr, kk in ((nS, rS, k), (nP, rP, mir(k))):
                new[kk], kind[kk] = FB['deck_ring']['color'], 'deck_ring'
                an = 'deck-%s' % nm
                anchors[an] = list(kk)
                ropes.append(dict(name='%s.train' % nm, **{'from': 'model:%s/%s/train' % (deck_link[rr['deck']], nm), 'to': '%s/%s' % (FB['link'], an)}, **R['train']))
    # floating: every new cell 6-connected to an old solid (window around the new cells)
    xs = [k[0] for k in new]
    zs = [k[2] for k in new]
    x0, x1, z0_, z1 = min(xs) - 2, max(xs) + 3, min(zs) - 2, max(zs) + 3
    sub = np.zeros((x1 - x0, 2 * YC + 2, z1 - z0_), bool)
    nw = np.zeros_like(sub)
    for (x, y, z) in occ:
        if x0 <= x < x1 and z0_ <= z < z1:
            sub[x - x0, y, z - z0_] = True
    for (x, y, z) in new:
        nw[x - x0, y, z - z0_] = True
    lab, _ = ndimage.label(sub | nw)
    anch = set(np.unique(lab[sub])) - {0}
    floating = sorted(k for k in new if lab[k[0] - x0, k[1], k[2] - z0_] not in anch)
    # rope lines vs gun models of OTHER guns and every solid (both ends' own cells excepted) -- the same test, recounted
    cross = 0
    for rp in ropes:
        nm = rp['from'].split('/')[1]
        a = pt(rows[nm], rp['from'].rsplit('/', 1)[1])
        b = ctr(tuple(anchors[rp['to'].split('/', 1)[1]]))
        if blocked(a, b, gcells[nm] | {tuple(anchors[rp['to'].split('/', 1)[1]])} | {k for k in new}):
            cross += 1
    v = {'read': {'solid_cells': len(occ)}, 'guns': sum(1 for r in rows.values() if not r['swivel']), 'pairs': len(pairs),
         'cells': len(new), 'by_kind': dict(collections.Counter(kind.values())), 'anchors': len(anchors),
         'ropes': dict(collections.Counter(r['group'] for r in ropes)), 'ropes_total': len(ropes), 'ropes_through_solid': cross,
         'stat': dict(sorted(stat.items())),
         'on_solid': sum(1 for k in new if k in W), 'mirror_diff': sum(1 for k, c in new.items() if new.get(mir(k)) != c),
         'floating': [list(k) for k in floating[:6]], 'floating_n': len(floating), 'notes': notes}
    if probe:
        print(json.dumps({'probe': probe, 'readings': v}, ensure_ascii=False))
        return
    out = os.path.join(M, 'gunfittings')
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'gunfittings.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# Star (al-Najm) gun fittings (world coords, at 0,0,0; draft_gunfittings.py)\n')
        for (x, y, z), c in sorted(new.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    v['list'] = [len(new), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    json.dump({'note': 'gun-fittings sub-work anchors (world coords)', 'anchors': dict(sorted(anchors.items()))},
              open(os.path.join(design, 'gunfittings_points.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump({'note': 'gun tackle (hung on the assembly)', 'ropes': ropes}, open(os.path.join(design, 'gun_ropes.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(design, 'verify_gunfittings.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False))


if __name__ == '__main__':
    main()
