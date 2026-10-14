# 新圖紙 18 砲 v1（階段十七，TASK-0538）：上甲板 11 個砲門 × 兩舷，各放一門 24 磅長砲（外部模型 ← 憲法號 -gun-24，0.1 m）
#   輸入：plan.json guns、verify_ports.json（砲門 X／Z）、decks.json（上甲板走的那一格）、組裝件 export list、船殼 export list、-gun-24 export list
#   ⇒ guns_placement.json（模型名、at、mirror、meta）、verify_guns.json、sheet18_guns_v1.png
# 用法：python -I place_guns.py <design> <組裝件 list> <船殼 list> <gun list>
#   · 照造船規格 §4.2：每個砲門從舷牆外面往裡退，直到模型每一格的格心＋八個角（往裡縮 0.05 格）都不在組裝件的實心裡，再要求砲口在船殼外。
#     起點 ＝ 砲尾在船殼外緣往裡 start_inside 格（砲架跨在舷牆上、一定碰）—— v1 從船外起算，整門砲在船外本來就零碰撞，第一步就停。
#   · 右舷照原樣（砲口 +y、pivot 0,0,0、scale 1）；左舷 mirror=y、at.y ＝ 321 − 右舷的 at.y（照憲法號的砲；格 y ↔ 320 − y）。
#   · z：上甲板在砲門中心那一欄走的那一格（gun z 0 ＝ 甲板面上第一層）；碰到就試 +1。
import sys, os, json, hashlib, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402

YC = 160


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    G = plan['guns']
    asm_p, hull_p, gun_p = sys.argv[2], sys.argv[3], sys.argv[4]
    occ = DP.read_list(asm_p)
    assert len(occ) == G['assembly_cells'], ('組裝件格數對不上', len(occ))
    hull = DP.read_list(hull_p)
    gun = DP.read_list(gun_p)
    assert len(gun) == G['gun_cells'], ('砲的格數對不上', len(gun))
    ports = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))['ports']
    dk = json.load(open(os.path.join(design, 'decks.json'), encoding='utf-8'))
    X0d, up = dk['X0'], dk['decks']['upper']
    A = G['anchors']
    e = G['inset']
    offs = [(dx, dy, dz) for dx in (-0.5 + e, 0.5 - e) for dy in (-0.5 + e, 0.5 - e) for dz in (-0.5 + e, 0.5 - e)] + [(0, 0, 0)]
    gcells = np.array(sorted(gun), float) + 0.5
    pts = (gcells[:, None, :] + np.array(offs)[None, :, :]).reshape(-1, 3)

    def hits(at, mir):
        q = pts.copy()
        if mir:
            q[:, 1] = -q[:, 1]
        q = q + np.array(at)
        c = np.floor(q).astype(int)
        return sum(1 for k in set(map(tuple, c)) if k in occ)

    hy = {}
    for (x, y, z) in hull:
        if y > YC and y > hy.get((x, z), -1):
            hy[(x, z)] = y
    place, log = [], {}
    for P in ports:
        n = P['n']
        xc = (P['X'][0] + P['X'][1] + 1) / 2
        ax = xc - (A['muzzle'][0] + 0.5)
        zw = int(up[int(round(xc)) - X0d])
        best = None
        tried = []
        hx0 = int(math.floor(xc))
        y_start = hy[(hx0, P['Z'][0] - 1)] - G['start_inside']
        assert hits((ax, y_start, zw), False) > 0, ('砲門', n, '起點沒有跨在舷牆上')
        for z0 in (zw, zw + 1):
            for y0 in range(y_start, y_start - 80, -1):
                h = hits((ax, y0, z0), False)
                if h == 0:
                    break
            tried.append([z0, y0, h])
            if h == 0:
                best = (z0, y0)
                break
        assert best, ('砲門', n, '退不出零碰撞', tried)
        z0, y0 = best
        mz = (ax + A['muzzle'][0] + 0.5, y0 + A['muzzle'][1] + 0.5, z0 + A['muzzle'][2] + 0.5)
        # 砲口在船殼外：砲口那一欄、砲門下檻底下一格那一層的船殼外緣
        hx = int(math.floor(mz[0]))
        h_out = hy[(hx, P['Z'][0] - 1)]
        out_by = round(mz[1] - (h_out + 1), 2)
        # 兩舷同一個砲門的兩門砲不准重疊（窄的船尾）
        sS = {tuple(c) for c in np.floor(gcells + np.array([ax, y0, z0])).astype(int)}
        mP = gcells.copy()
        mP[:, 1] = -mP[:, 1]
        sP = {tuple(c) for c in np.floor(mP + np.array([ax, 321 - y0, z0])).astype(int)}
        both = len(sS & sP)
        hP = hits((ax, 321 - y0, z0), True)
        log[n] = {'X': P['X'], 'Z': P['Z'], 'deck_walk_z': zw, 'z0': z0, 'y_rear_S': y0, 'tried': tried, 'muzzle_S': [round(v, 2) for v in mz],
                  'hull_outer_y_below_sill': h_out, 'muzzle_out_of_hull_by': out_by, 'S_P_overlap': both, 'P_hits': hP,
                  'muzzle_rel_sill': round(mz[2] - P['Z'][0], 2), 'muzzle_rel_top': round(P['Z'][1] + 1 - mz[2], 2)}
        for side, at, mir in (('S', [ax, y0, z0], ''), ('P', [ax, 321 - y0, z0], 'y')):
            place.append({'name': '砲-%s%02d' % (side, n), 'port': n, 'side': side, 'at': [round(v, 3) for v in at], 'pivot': [0, 0, 0], 'rotate': [0, 0, 0],
                          'scale': [1, 1, 1], 'mirror': mir, 'meta': dict(G['meta'])})
    v = {'base': {'assembly': hashlib.sha256(open(asm_p, 'rb').read()).hexdigest(), 'hull': hashlib.sha256(open(hull_p, 'rb').read()).hexdigest(),
                  'gun': hashlib.sha256(open(gun_p, 'rb').read()).hexdigest()},
         'guns': len(place), 'ports': log,
         'all_zero_collision': all(L['P_hits'] == 0 and L['tried'][-1][2] == 0 for L in log.values()),
         'all_muzzles_out': all(L['muzzle_out_of_hull_by'] > 0 for L in log.values()),
         'S_P_overlap_total': sum(L['S_P_overlap'] for L in log.values())}
    pp = os.path.join(design, 'guns_placement.json')
    json.dump({'source_work': G['source_work'], 'host': G['host'], 'link': G['link'], 'placements': place}, open(pp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    v['placement_sha256'] = hashlib.sha256(open(pp, 'rb').read()).hexdigest()
    json.dump(v, open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    # 圖：上甲板平面（從上往下看、右舷在上），砲的格投影
    X0, X1 = 60, 660
    img = np.full((320, X1 - X0, 3), 250, np.uint8)
    for (x, y, z) in occ:
        if X0 <= x < X1 and 95 <= z <= 125:
            img[319 - y, x - X0] = (215, 208, 196)
    for p in place:
        q = gcells.copy()
        if p['mirror']:
            q[:, 1] = -q[:, 1]
        q = np.floor(q + np.array(p['at'])).astype(int)
        for x, y, z in q:
            if X0 <= x < X1:
                img[319 - y, x - X0] = (30, 30, 30)
    im = Image.fromarray(img)
    ImageDraw.Draw(im).text((4, 4), 'sheet 18 v1  24-pdr long guns on the upper deck (plan, starboard up; deck band z 95-125)', fill=(0, 0, 0))
    im.save(os.path.join(design, 'sheet18_guns_v1.png'))
    print(json.dumps({k: v[k] for k in ('guns', 'all_zero_collision', 'all_muzzles_out', 'S_P_overlap_total')}, ensure_ascii=False))
    for n, L in log.items():
        print(n, 'X', L['X'], 'z0', L['z0'], 'walk', L['deck_walk_z'], 'yS', L['y_rear_S'], 'muzzle out by', L['muzzle_out_of_hull_by'], 'sill+', L['muzzle_rel_sill'], 'top-', L['muzzle_rel_top'], 'P hits', L['P_hits'], 'tried', L['tried'])


if __name__ == '__main__':
    main()
