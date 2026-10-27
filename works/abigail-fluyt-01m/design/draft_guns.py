# 澤漢號 步驟 9（TASK-0966）：出處 ame-labelle-01m/design/draft_guns.py（拉貝爾號）；本船每舷 4 門 4 磅、迴旋砲每舷 3。原檔頭：砲 —— 全部是外部模型，沿用現有的砲（Ship_Setup §2.1），掛在所在甲板的子作品上
#   出處：calli-cosecha-01m/design/draft_guns.py（收穫號 階段八）；船尾追擊砲那段換成迴旋砲（插在舷牆頂，plan.guns_build.swivels）
#   主甲板（deck-main）：舷側 3 門／舷 4 磅（風暴角號 -gun-6l 縮 0.375）；迴旋砲 8 門（皇家號 -gun-pierrier 縮 0.39）：後甲板 2、船腰 1、船首樓 1（每舷）
#   擺法（Ship_Guns §4.2）：沿砲身方向從船殼外面往裡退（每步 0.5 格），退到模型每一格的格心＋八個角（往裡縮 inset）都不在組裝件的實心格裡 ⇒
#   推得最出去的位置；再看砲口有沒有伸出船殼、砲口那一點是不是空的、砲腳下有沒有甲板。迴旋砲：pivot 站在舷牆頂那一欄最高那一層、牆厚中間，量零碰撞與砲口伸出。
#   S 舷 ＝ +y（砲口 +y、φ 0）；P 舷 mirror=y。
#   輸入：plan.json（ports、guns_build）＋ 組裝件現在的格子（CLI 匯出；模型不在匯出裡 ⇒ 重產時不會撞到自己上一輪的砲）
#   輸出：guns_placement.json、verify_guns.json
#   用法：python -I -X utf8 draft_guns.py <design> [--probe=push=<砲名>:<格>]（反向對照：那一門往外推幾格，印每門的碰撞樣本數，⛔ 不寫檔）
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
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
    G = Grid(A)
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
        """沿 −d_out 往裡退到零碰撞；回傳 (key, cand) 的最佳者。"""
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
    # ── 舷側 ──
    for p in LY.ports(plan):
        g = guns[p['gun']]
        xc = (p['x0'] + p['x1'] + 1) / 2.0
        zm = (p['z0'] + p['z1']) // 2
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            outs = [hull_y(x, zm, side) for x in (p['x0'] - 2, p['x1'] + 2)]
            outer = max(outs) if side > 0 else min(outs)
            yin = [plan['space']['yc'] + side * d for d in (6, 8, 10, 12)]     # 本船：從中線對稱取樣（收穫號從外緣往裡數，兩舷外緣差一格 ⇒ v1 S03 踩到前艙口圍欄浮一格）
            zd = deck_top(p['deck'], [(x, y) for x in (p['x0'], int(xc), p['x1']) for y in yin])
            d_out = g.direction(0.0, mirror)
            best = place(g, (xc, outer), d_out, 0.0, mirror, zd, S['dx'], lambda tip: (tip[1] - outer) * side)
            r = {'deck': p['deck'], 'port': p['i'], 'side': nm, 'type': p['gun'], 'chase': False, 'outer': outer, 'deck_z': zd,
                 'opening': {'x': [p['x0'], p['x1']], 'z': [p['z0'], p['z1']]}}
            r.update(best[1] if best else {'ok': False, 'at': None})
            rows.append(r)
    # ── 迴旋砲：插在舷牆頂（那一欄船殼最高那一層、牆厚中間）——
    SW = GB['swivels']
    g = guns[SW['type']]
    YC = plan['space']['yc']
    for row in SW['rows']:
        x = row['x']
        zt = max(z for (xx, y, z) in Hs if xx == x and y > YC)
        ys = sorted(y for (xx, y, z) in Hs if xx == x and z == zt and y > YC)
        ym = (ys[0] + ys[-1]) // 2
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            y_at = (ym + 0.5) if side > 0 else (2 * YC + 1 - (ym + 0.5))
            at = (x + 0.5, y_at, float(zt + 1))
            hit = int(G.hit(g.world(g.samples, at, 0.0, mirror)).sum())
            tip = g.world(g.anchors['muzzle'][None], at, 0.0, mirror)[0]
            outer = (ys[-1] + 1) if side > 0 else (2 * YC - ys[-1])
            beyond = (tip[1] - outer) * side
            tip_free = not G.hit(tip[None])[0]
            r = {'deck': row['deck'], 'port': 'sw%d' % x, 'side': nm, 'type': SW['type'], 'chase': False, 'swivel': True, 'deck_z': zt + 1,
                 'at': r3(at), 'phi': 0.0, 'back': 0.0, 'off': 0.0, 'dz': 0, 'muzzle_beyond': round(float(beyond), 2), 'muzzle_free': tip_free,
                 'support': 1.0, 'axis_z': round(float(tip[2]), 2), 'hit_samples': hit, 'ok': bool(hit == 0 and beyond > 0 and tip_free)}
            rows.append(r)
    # ── 命名 ──
    cnt = {}
    for r in rows:
        pre = GB['prefix'][r['deck']]
        if r.get('swivel'):
            cnt[('sw', r['side'])] = cnt.get(('sw', r['side']), 0) + 1
            r['name'] = '迴旋砲-%s%02d' % (r['side'], cnt[('sw', r['side'])])
        elif r['chase']:
            r['name'] = '%s-chase-stern-%s' % (pre, r['side'])
        else:
            cnt[(pre, r['side'])] = cnt.get((pre, r['side']), 0) + 1
            r['name'] = '砲%s-%s%02d' % (pre, r['side'], cnt[(pre, r['side'])])
    rows.sort(key=lambda r: (bool(r.get('swivel')), list(GB['prefix']).index(r['deck']), r['side'], str(r['port'])))

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
    # ── 砲跟砲不撞（格心落在同一格）──
    occ, clash = {}, []
    for r in rows:
        g = guns[r['type']]
        P = g.world(g.centers, r['at'], r['phi'], r['side'] == 'P')
        for c in set(map(tuple, np.floor(P).astype(int).tolist())):
            if c in occ and occ[c] != r['name']:
                clash.append([r['name'], occ[c]])
                break
            occ[c] = r['name']
    # ── 兩舷對稱（格 y ↔ 2·YC − y ⇒ 連續座標 y ↔ 2·YC ＋ 1 − y：P 的 at.y 應 ＝ 321 − S 的 at.y；φ 相反）──
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
    v['swivels'] = [{k: r[k] for k in ('name', 'deck', 'at', 'muzzle_beyond', 'muzzle_free', 'hit_samples', 'ok')} for r in rows if r.get('swivel')]
    json.dump({'note': 'draft_guns.py 的結果；at ＝ 模型的 at（pivot 落點）、phi ＝ rotate z、P 舷 mirror=y', 'rows': rows},
              open(os.path.join(design, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
