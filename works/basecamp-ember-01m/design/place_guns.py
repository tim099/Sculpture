"""
餘燼號 階段十 砲（plan.json guns；新圖紙 11）—— 90 門全部是外部模型，掛在所在甲板的子作品上（藏甲板就一起藏）。
  下層砲甲板（甲板-lower）：舷側 16 門／舷 ＝ 新做的 32 磅長砲 -gun-long32（0.05 m、scale 0.5）
  上層砲甲板（甲板-upper）：舷側 16 門／舷 ＝ 憲法號 -gun-24（0.1 m、scale 1）
  上甲板（甲板-spar）：carronade 9 門／舷 ＝ 憲法號 -gun-carronade32（第 4–12 個砲門；1–3 在 poop 底下的船長室）
  追擊砲：兩層各一對船頭（第 17 個砲門、照角度搜）＋一對船尾（transom 的砲門）＝ 憲法號 -gun-long18
擺法（憲法號 place_carronades.py／place_chase.py）：沿砲身方向從舷牆外面往裡退（每步 0.5 格），退到「模型每一格的格心＋八個角往裡縮 0.2
都不落在組裝件的實心格裡」⇒ 推得最出去的位置；再看砲口有沒有伸出船殼外面。
另一舷一律 mirror=y（模型 p ＝ at ＋ R(φ)·M(v − pivot)·scale）⇒ eye-aft／eye-fwd 不會前後對調；P 舷各自搜（船艙左右不對稱）。
砲口方向 ＝ 子作品 +y；S 舷舷側 φ 0、船頭追擊砲 φ < 0（往船頭偏）、船尾 φ ≈ 90（砲口朝 −x）。
⇒ guns_placement.json、verify_guns.json
用法：python -I place_guns.py <design 資料夾>
"""
import sys, os, json, math
import numpy as np
from scipy import ndimage

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import draft_profile as DP                               # noqa: E402
from draft_ladders import export_hidden                  # noqa: E402

YC = 160
X0, X1, Z0, Z1 = 60, 800, 60, 200


def grid(a):
    m = a[(a[:, 0] >= X0) & (a[:, 0] < X1) & (a[:, 2] >= Z0) & (a[:, 2] < Z1)]
    G = np.zeros((X1 - X0, 320, Z1 - Z0), bool)
    G[m[:, 0] - X0, m[:, 1], m[:, 2] - Z0] = True
    return G


def hits(G, P):
    i = np.floor(P).astype(int)
    i[..., 0] -= X0
    i[..., 2] -= Z0
    ok = (i[..., 0] >= 0) & (i[..., 0] < X1 - X0) & (i[..., 1] >= 0) & (i[..., 1] < 320) & (i[..., 2] >= 0) & (i[..., 2] < Z1 - Z0)
    out = np.ones(i.shape[:-1], bool)          # 框外當撞（不該跑出去）
    out[ok] = G[i[ok][:, 0], i[ok][:, 1], i[ok][:, 2]]
    return out


OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])


class Gun:
    def __init__(s, key, work, cells, scale, pivot, muzzle, meta):
        s.key, s.work, s.scale = key, work, scale
        s.pivot, s.muzzle = np.array(pivot, float), np.array(muzzle, float)
        c = np.array(cells, float)
        s.samples = (c[:, None, :] + OFFS[None]).reshape(-1, 3)
        s.n = len(c)
        s.meta = meta

    def world(s, P, at, phi, mirror):
        q = (P - s.pivot) * s.scale
        if mirror:
            q = q * np.array([1.0, -1.0, 1.0])
        c, sn = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        x = q[..., 0] * c - q[..., 1] * sn
        y = q[..., 0] * sn + q[..., 1] * c
        return np.stack([x + at[0], y + at[1], q[..., 2] + at[2]], -1)

    def direction(s, phi, mirror):
        """子作品 +y（砲口方向）在世界 xy 的單位向量"""
        a = s.world(s.pivot[None], (0, 0, 0), phi, mirror)[0]
        b = s.world((s.pivot + [0, 1.0 / s.scale, 0])[None], (0, 0, 0), phi, mirror)[0]
        d = (b - a)[:2]
        return d / np.linalg.norm(d)


def load_cells(path_or_work):
    if path_or_work.endswith('.txt'):
        a = np.loadtxt(path_or_work, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    else:
        a = export_hidden(path_or_work, [])
    return a[:, :3].tolist()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
    GB = plan['guns_build']
    asm = export_hidden(GB['assembly'], [])
    assert len(asm) == GB['assembly_voxels'], ('組裝件現況對不上', len(asm))
    G = grid(asm)
    hull = DP.export_list(GB['hull'], links='none')
    H = grid(hull)
    decks = {k: grid(export_hidden(w, [])) for k, w in GB['deck_works'].items()}
    T = GB['types']
    guns = {}
    for k, t in T.items():
        src = t['cells']                                  # masks/…（本作品）或作品 id（匯出）
        src = os.path.join(D, src) if src.startswith('masks/') else src
        guns[k] = Gun(k, t['work'], load_cells(src), t['scale'], t['pivot'], t['muzzle'], t['meta'])

    def deck_top(dk, xs, ys):
        Dg = decks[dk]
        best = None
        for x in xs:
            for y in ys:
                col = np.where(Dg[int(x) - X0, int(y)])[0]
                if len(col):
                    z = int(col.max()) + Z0 + 1
                    best = z if best is None else max(best, z)
        return best

    # ── 舷側砲門（從船殼量：|dy| ≥ 10 沒有船殼格、上下都有牆）──
    wall = H[:, YC + 10:, :].any(1)
    rows, bad = [], []
    for R in GB['rows']:
        z0, z1 = R['band']
        W = wall[:, z0 - Z0:z1 - Z0]
        op = np.zeros_like(W)
        for x in range(W.shape[0]):
            idx = np.where(W[x])[0]
            if len(idx) >= 2:
                op[x, idx.min():idx.max() + 1] = ~W[x, idx.min():idx.max() + 1]
        lab, n = ndimage.label(op)
        ports = []
        for i in range(1, n + 1):
            xs, zs = np.where(lab == i)
            if len(xs) >= 20:
                ports.append((int(xs.min()) + X0, int(xs.max()) + X0, int(zs.min()) + z0, int(zs.max()) + z0))
        ports.sort()
        assert len(ports) == R['ports_per_side'], (R['deck'], '砲門數對不上', len(ports))
        for pi, (xa, xb, za, zb) in enumerate(ports, 1):
            if pi not in R['use'] and pi != R.get('chase_port'):
                continue
            chase = pi == R.get('chase_port')
            g = guns[R['chase_type'] if chase else R['type']]
            xc = (xa + xb + 1) / 2.0
            zm = (za + zb) // 2
            for side, nm in ((1, 'S'), (-1, 'P')):
                mirror = side < 0
                # 舷牆外面：砲門前後兩欄、開口中段那一層，船殼最外那格
                ys = [np.where(H[x - X0, :, zm - Z0])[0] for x in (xa - 2, xb + 2)]
                outer = (max(int(v.max()) for v in ys) + 1) if side > 0 else min(int(v.min()) for v in ys)
                # 船殼面往裡 d 格那一欄：S ＝ outer − d − 1、P ＝ outer ＋ d（格 y ↔ 320 − y ⇒ 兩舷取到鏡像的同一欄；v1 P 舷多往裡 1 格 ⇒ 甲板高讀低 1）
                inside = lambda d: outer - d - 1 if side > 0 else outer + d
                zd = deck_top(R['deck'], [xa, xc, xb], [inside(R['wall_guess'] + k) for k in (4, 12, 20, 28)])
                best = None
                tried = {}
                phis = R['chase_phis'] if chase else [0.0]
                for phi in phis:
                    ph = phi if side > 0 else -phi
                    d_out = g.direction(ph, mirror)                                # 砲口方向（xy）
                    d_side = np.array([d_out[1], -d_out[0]])
                    for dx, dz in [(d, z) for z in (0, 1) for d in ([0.0, 0.5, -0.5, 1.0, -1.0] if not chase else [0.5 * k for k in range(-8, 9)])]:
                        for back in [0.5 * k for k in range(0, 80)]:
                            base = np.array([xc, outer]) + d_side * dx - d_out * back
                            at = (float(base[0]), float(base[1]), float(zd + dz))
                            if hits(G, g.world(g.samples, at, ph, mirror)).any():
                                continue
                            tip = g.world(g.muzzle[None], at, ph, mirror)[0]
                            beyond = float((tip[1] - outer) * side)
                            tip_free = not hits(G, tip[None])[0]
                            cand = {'deck': R['deck'], 'port': pi, 'side': nm, 'type': g.key, 'chase': chase, 'phi': ph, 'at': [round(v, 3) for v in at],
                                    'back': back, 'dx': dx, 'dz': dz, 'muzzle_beyond_outer': round(beyond, 2), 'muzzle_free': tip_free,
                                    'axis_z': round(float(tip[2]), 2), 'opening': {'x': [xa, xb], 'z': [za, zb]}, 'outer_y': outer}
                            ok = beyond > 0 and tip_free
                            key = (dz, not ok, -beyond if chase else back, abs(dx))   # 先貼著甲板（v1 有 16 門 carronade 為了砲口伸出去浮高 1 格）
                            if best is None or key < best[0]:
                                best = (key, cand)
                            if chase:
                                k0 = tried.get(ph)
                                if k0 is None or key < k0[0]:
                                    tried[ph] = (key, [ph, back, dx, dz, round(beyond, 2), tip_free])
                            break
                if best is None or best[0][1]:
                    bad.append((R['deck'], pi, nm, best[1] if best else None))
                if best:
                    if chase:
                        best[1]['tried'] = [v[1] for k, v in sorted(tried.items())]
                    rows.append(best[1])
    # ── 船尾追擊砲（transom 的開口：船尾面往裡、|dy| 照 plan、z 照 band）──
    for St in GB['stern']:
        g = guns[St['type']]
        z0, z1 = St['band']
        dy0, dy1 = St['dy']
        # 開口：(y, z) 在 x 90..130 都沒有船殼格（看得穿）
        best_port = None
        Hs = H[90 - X0:131 - X0]
        clear = ~Hs.any(0)                          # (y, z)
        cells = [(y, z) for y in range(YC + dy0, YC + dy1 + 1) for z in range(z0, z1) if clear[y, z - Z0]]
        assert cells, ('船尾開口找不到', St)
        ys_, zs_ = zip(*cells)
        yc = (min(ys_) + max(ys_) + 1) / 2.0
        za, zb = min(zs_), max(zs_)
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            yC = yc if side > 0 else 321 - yc
            outer = min(int(np.where(H[:, int(yC) + d, (za + zb) // 2 - Z0])[0].min()) for d in (-6, 6)) + X0   # 船尾面（最後面那格）
            zd = deck_top(St['deck'], [outer + k for k in (6, 14, 22)], [int(yC) + d for d in (-4, 0, 4)])
            best = None
            tried = {}
            for phi in St['phis']:
                ph = phi if side > 0 else -phi
                d_out = g.direction(ph, mirror)
                d_side = np.array([d_out[1], -d_out[0]])
                for dl, dz in [(d, z) for z in (0, 1) for d in [0.5 * k for k in range(-6, 7)]]:
                    for back in [0.5 * k for k in range(0, 80)]:
                        base = np.array([outer, yC]) + d_side * dl - d_out * back
                        at = (float(base[0]), float(base[1]), float(zd + dz))
                        if hits(G, g.world(g.samples, at, ph, mirror)).any():
                            continue
                        tip = g.world(g.muzzle[None], at, ph, mirror)[0]
                        beyond = float(outer - tip[0])
                        tip_free = not hits(G, tip[None])[0]
                        cand = {'deck': St['deck'], 'port': 'stern', 'side': nm, 'type': g.key, 'chase': True, 'phi': ph, 'at': [round(v, 3) for v in at],
                                'back': back, 'dx': dl, 'dz': dz, 'muzzle_beyond_outer': round(beyond, 2), 'muzzle_free': tip_free, 'axis_z': round(float(tip[2]), 2),
                                'opening': {'y': [min(ys_), max(ys_)], 'z': [za, zb]}, 'outer_x': outer}
                        ok = beyond > 0 and tip_free
                        key = (dz, not ok, back, abs(ph - (90 if side > 0 else -90)), abs(dl))
                        if best is None or key < best[0]:
                            best = (key, cand)
                        k0 = tried.get(ph)
                        if k0 is None or key < k0[0]:
                            tried[ph] = (key, [ph, back, dl, dz, round(beyond, 2), tip_free])
                        break
            if best is None or best[0][1]:
                bad.append((St['deck'], 'stern', nm, best[1] if best else None))
            if best:
                best[1]['tried'] = [v[1] for k, v in sorted(tried.items())]
                rows.append(best[1])
    # ── 命名、彼此不撞 ──
    occ = {}
    clash = []
    cnt = {}
    for r in rows:
        g = guns[r['type']]
        pre = {'lower': 'L', 'upper': 'U', 'spar': 'C'}[r['deck']]
        if r['chase']:
            r['name'] = '%s-chase-%s-%s' % (pre, 'bow' if r['port'] != 'stern' else 'stern', r['side'])
        else:
            cnt[(pre, r['side'])] = cnt.get((pre, r['side']), 0) + 1
            r['name'] = '砲%s-%s%02d' % (pre, r['side'], cnt[(pre, r['side'])])
        W = g.world(g.samples, r['at'], r['phi'], r['side'] == 'P')
        cellset = set(map(tuple, np.floor(W).astype(int).tolist()))
        for c in cellset:
            if c in occ and occ[c] != r['name']:
                clash.append((r['name'], occ[c]))
                break
            occ[c] = r['name']
    v = {'read': {'assembly_voxels': int(len(asm))}, 'guns': len(rows),
         'by_deck_type': {}, 'not_ok': [(d, p, s, (c or {}).get('muzzle_beyond_outer')) for d, p, s, c in bad], 'gun_gun_clash': clash}
    for r in rows:
        k = '%s/%s' % (r['deck'], r['type'])
        v['by_deck_type'][k] = v['by_deck_type'].get(k, 0) + 1
    v['muzzle_beyond'] = {k: [min(r['muzzle_beyond_outer'] for r in rows if '%s/%s' % (r['deck'], r['type']) == k),
                              max(r['muzzle_beyond_outer'] for r in rows if '%s/%s' % (r['deck'], r['type']) == k)] for k in v['by_deck_type']}
    v['back'] = {k: [min(r['back'] for r in rows if '%s/%s' % (r['deck'], r['type']) == k), max(r['back'] for r in rows if '%s/%s' % (r['deck'], r['type']) == k)] for k in v['by_deck_type']}
    v['chase'] = [{k: r[k] for k in ('name', 'phi', 'at', 'back', 'muzzle_beyond_outer', 'muzzle_free', 'axis_z', 'tried')} for r in rows if r['chase']]
    json.dump({'note': 'place_guns.py 的結果；at 是模型的 at（pivot 落點）、phi ＝ rotate z、P 舷 mirror=y', 'types': T, 'rows': rows},
              open(os.path.join(D, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(D, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
