# 抄來的（燕子號 TASK-0968）：出處 gura-flyingfish-01m/design/draft_gunfittings.py（飛魚號；作品 id、船名、單號已換）
# 抄來的（飛魚號 TASK-0971）：出處 ame-labelle-01m/design/draft_gunfittings.py（拉貝爾號；作品 id、persona、船名、作品尺寸已換）
# 收穫號 階段十二（TASK-0624）：砲具與砲索 —— 每門砲船牆兩側的環（一格鐵釘進牆＋外面一格當環）、甲板環；breeching ×2、side tackle ×2、train tackle ×1
#   做法照造船規格 §4.4（憲法號／餘燼號 draft_gunfittings.py），改成本船的慣例：一件子作品、世界座標、兩舷都在裡面（S 舷算、P 舷鏡過去照樣量）。
#   · 船牆的環：從砲的 pivot 往砲的兩側偏 offset 格，沿砲口方向往外走到第一格船殼 ⇒ 牆裡面那兩格（stem、ring）；高度 ＝ 那一側 eye 的高度。
#     舷側砲與船尾追擊砲同一個算法（砲口方向 d、側向 t）。繩（cascabel → 環、eye → 環）不准穿過別的實心（自己這門砲不算），另一舷鏡過去也量；
#     不行就換 offset，都不行就不放、那一側的繩不掛（照實記）。
#   · 甲板環：train 往船裡（−d）back 格、站在甲板上（腳下實心）；train → 環不准穿過別的實心。
#   輸入：plan.json（gunfittings_build、guns_build）＋ guns_placement.json ＋ 組裝件現在的格子（扣掉本階段的砲具）＋ 所有砲模型取樣成的格（擋繩）
#   輸出：masks/gunfittings/gunfittings.vox.txt、gunfittings_points.json（固定點）、gun_ropes.json、verify_gunfittings.json
#   用法：python -I -X utf8 draft_gunfittings.py <design>
import sys, os, json, math, hashlib, collections
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
from wio import export_list
from gunsim import load_guns


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    plan = HL.load_plan(design)
    GB, FB = plan['guns_build'], plan['gunfittings_build']
    YC = plan['space']['yc']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list(GB['assembly'], None, links=None)
    own = set()
    if os.path.exists(os.path.join(WORKS, FB['work'], 'work.json')):
        own = set(map(tuple, export_list(FB['work'], None)[:, :3].tolist()))
    occ = set(map(tuple, A[:, :3].tolist())) - own
    Hs = set(map(tuple, export_list(GB['hull'], None)[:, :3].tolist()))
    guns = load_guns(GB, WORKS, export_list)
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

    deck_link = {k: '甲板-' + k for k in GB['deck_works']}
    R = FB['ropes']
    pairs = [(n, n.replace('-S', '-P')) for n in rows if rows[n]['side'] == 'S']
    stat = collections.Counter()
    for nS, nP in sorted(pairs):
        rS, rP = rows[nS], rows[nP]
        g = guns[rS['type']]
        d = g.direction(rS['phi'], False)
        da = (int(round(d[0])), int(round(d[1])))                               # 砲口方向（舷側 ±y、追擊砲 −x）—— 一格一格往裡退用
        t = np.array([-d[1], d[0]])
        c2 = np.array(rS['at'][:2], float)
        z0 = int(rS['at'][2])
        got = {}
        for side in ('aft', 'fwd'):
            eye = pt(rS, 'eye-' + side)
            s = 1.0 if (eye[:2] - c2) @ t >= 0 else -1.0
            zr = int(math.floor(eye[2]))
            done = None
            for off in FB['ring']['offset']:
                p = c2 + t * s * off - d * 25                                   # 從船裡深一點開始往外找（v1 從 pivot 起 ⇒ 船頭收窄、船樓隔艙壁那幾門的起點已經在牆裡，stem 落在船殼上）
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
                notes.append('%s／%s 的 %s 環找不到不穿過實心的位置 ⇒ 不放、那一側的 breeching 與 tackle 不掛' % (nS, nP, side))
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
            got[side] = off
        # 甲板環
        tr = pt(rS, 'train')
        done = None
        for back in FB['deck_ring']['back']:
            q = tr[:2] - d * back
            kx, ky = int(math.floor(q[0])), int(math.floor(q[1]))
            zk = next((z for z in range(z0, z0 - 4, -1) if (kx, ky, z - 1) in occ and (kx, ky, z) not in occ), None)   # 甲板舷弧是台階：砲站在高的那一階、環可能在低的那一階（v1 沿用砲的高度 ⇒ M07、追擊砲的環腳下是空的）
            if zk is None:
                continue
            k = (kx, ky, zk)
            if k in W or k in new or mir(k) in W or mir(k) in new or (k[0], 2 * YC - k[1], zk - 1) not in occ:
                continue
            if blocked(tr, ctr(k), gcells[nS] | {k}) or blocked(pt(rP, 'train'), ctr(mir(k)), gcells[nP] | {mir(k)}):
                continue
            done = (back, k)
            break
        if done is None:
            notes.append('%s／%s 的甲板環找不到位置 ⇒ train tackle 不掛' % (nS, nP))
        else:
            back, k = done
            stat['deck_back_%d' % back] += 1
            for nm, rr, kk in ((nS, rS, k), (nP, rP, mir(k))):
                new[kk], kind[kk] = FB['deck_ring']['color'], 'deck_ring'
                an = 'deck-%s' % nm
                anchors[an] = list(kk)
                ropes.append(dict(name='%s.train' % nm, **{'from': 'model:%s/%s/train' % (deck_link[rr['deck']], nm), 'to': '%s/%s' % (FB['link'], an)}, **R['train']))
    # 浮空：新格都要 6 連通接到原本的實心（只看新格附近）
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
    v = {'read': {'assembly_voxels_minus_own': len(occ)}, 'guns': len(rows), 'pairs': len(pairs),
         'cells': len(new), 'by_kind': dict(collections.Counter(kind.values())), 'anchors': len(anchors),
         'ropes': dict(collections.Counter(r['group'] for r in ropes)), 'ropes_total': len(ropes), 'stat': dict(sorted(stat.items())),
         'on_solid': sum(1 for k in new if k in W), 'mirror_diff': sum(1 for k, c in new.items() if new.get(mir(k)) != c),
         'floating': [list(k) for k in floating[:6]], 'floating_n': len(floating), 'notes': notes}
    out = os.path.join(design, 'masks', 'gunfittings')
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'gunfittings.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 收穫號 砲具（世界座標、at 0,0,0；draft_gunfittings.py）\n')
        for (x, y, z), c in sorted(new.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    v['list'] = [len(new), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    json.dump({'note': '砲具子作品的固定點（世界座標）', 'anchors': dict(sorted(anchors.items()))}, open(os.path.join(design, 'gunfittings_points.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump({'note': '砲索（掛在組裝件）', 'ropes': ropes}, open(os.path.join(design, 'gun_ropes.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(design, 'verify_gunfittings.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False))


if __name__ == '__main__':
    main()
