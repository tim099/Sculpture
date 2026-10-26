# 直接出處：gura-pinas-01m/design/draft_guns.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成康塞普西翁號（TASK-0969）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/draft_guns.py（收穫號，照抄後改成康塞普西翁號 —— TASK-0969）
# 康塞普西翁號 階段八（TASK-0597）：砲 —— 全部是外部模型，沿用現有的砲（造船規格 §2.1），掛在所在甲板的子作品上
#   主甲板（deck-main）：舷側 9 門／舷 18 磅（憲法號 -gun-long18）＋ 船尾追擊砲 2 門（同一件、gun=18chase）
#   上甲板（deck-puente）：8 門／舷 12 磅（風暴角號 -gun-12l）；後甲板、船首樓：各 2 門／舷 6 磅（風暴角號 -gun-6l）
#   擺法（造船規格 §4.2；同餘燼號 place_guns.py）：沿砲身方向從船殼外面往裡退（每步 0.5 格），退到模型每一格的格心＋八個角（往裡縮 inset）
#   都不在組裝件的實心格裡 ⇒ 推得最出去的位置；再看砲口有沒有伸出船殼、砲口那一點是不是空的、砲腳下有沒有甲板。
#   S 舷 ＝ +y（砲口 +y、φ 0）；P 舷 mirror=y、各自搜。船尾追擊砲砲口朝 −x（S φ 90、P −90），照角度搜。
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
    OV = GB.get('override', {})                                         # 康塞普西翁號：個別砲門放寬搜尋（plan.guns_build.override，鍵 '<層>:<序號>'：dx、phi 各一串）
    only = os.environ.get('GUNS_ONLY')                                  # 測試用：只算這一個砲門（'<層>:<序號>'），印結果就停
    for p in LY.ports(plan):
        if only and only != '%s:%d' % (p['deck'], p['i']):
            continue
        g = guns[p['gun']]
        xc = (p['x0'] + p['x1'] + 1) / 2.0
        zm = (p['z0'] + p['z1']) // 2
        ov = OV.get('%s:%d' % (p['deck'], p['i']), {})
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            outs = [hull_y(x, zm, side) for x in (p['x0'] - 2, p['x1'] + 2)]
            outer = max(outs) if side > 0 else min(outs)
            yin = [outer - side * d for d in (8, 14, 20, 26)]
            zd = deck_top(p['deck'], [(x, y) for x in (p['x0'], int(xc), p['x1']) for y in yin])
            best = None
            for ph0 in ov.get('phi', [0.0]):
                ph = float(ph0) * side                                  # P 舷照鏡像：角度相反（兩舷對稱檢查要 φ 相反）
                d_out = g.direction(ph, mirror)
                offs = [o * side for o in ov['dx']] if 'dx' in ov else S['dx']   # 側向 d_side 在 P 舷是反的 ⇒ 放寬的 dx 乘 side 才兩舷對稱（v1 P 舷的 −1.5 其實往船頭、推向艙壁）
                b_ = place(g, (xc, outer), d_out, ph, mirror, zd, offs, lambda tip: (tip[1] - outer) * side)
                if b_ and (best is None or (b_[0], abs(ph0)) < (best[0], best[2])):
                    best = (b_[0], b_[1], abs(ph0))
            if only:
                print(nm, json.dumps(best[1] if best else None, ensure_ascii=False))
            r = {'deck': p['deck'], 'port': p['i'], 'side': nm, 'type': p['gun'], 'chase': False, 'outer': outer, 'deck_z': zd,
                 'opening': {'x': [p['x0'], p['x1']], 'z': [p['z0'], p['z1']]}}
            r.update(best[1] if best else {'ok': False, 'at': None})
            rows.append(r)
    if only:
        return
    # ── 船尾追擊砲（主甲板 espejo 的兩個砲門）──
    C = GB['chase']
    g = guns[C['type']]
    W = [w for w in json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))['windows'] if w['kind'] == 'port']
    for w in W:
        side = 1 if w['y0'] > plan['space']['yc'] else -1
        nm = 'S' if side > 0 else 'P'
        mirror = side < 0
        yc = (w['y0'] + w['y1'] + 1) / 2.0
        zm = (w['z0'] + w['z1']) // 2
        xs = [min(x for (x, y, z) in Hs if y == yy and z == zm) for yy in (w['y0'] - 2, w['y1'] + 2)]
        outer = min(xs)
        zd = deck_top(C['deck'], [(outer + d, int(yc) + e) for d in (8, 16, 24) for e in (-4, 0, 4)])
        best = None
        tried = []
        for phi0 in C['phis']:
            ph = phi0 * side
            d_out = g.direction(ph, mirror)
            b = place(g, (outer, yc), d_out, ph, mirror, zd, [0.5 * k for k in range(-2 * C['dl'], 2 * C['dl'] + 1)], lambda tip: outer - tip[0])
            if not b:
                continue
            tried.append([ph, b[1]['back'], b[1]['off'], b[1]['dz'], b[1]['muzzle_beyond'], b[1]['ok']])
            key = (b[0][0], abs(phi0 - 90), b[0][1], b[0][2], b[0][3])
            if best is None or key < best[0]:
                best = (key, b[1])
        r = {'deck': C['deck'], 'port': 'stern', 'side': nm, 'type': C['type'], 'chase': True, 'outer_x': outer, 'deck_z': zd,
             'opening': {'y': [w['y0'], w['y1']], 'z': [w['z0'], w['z1']]}, 'tried': tried}
        r.update(best[1] if best else {'ok': False, 'at': None})
        rows.append(r)
    # ── 命名 ──
    cnt = {}
    for r in rows:
        pre = GB['prefix'][r['deck']]
        if r['chase']:
            r['name'] = '%s-chase-stern-%s' % (pre, r['side'])
        else:
            cnt[(pre, r['side'])] = cnt.get((pre, r['side']), 0) + 1
            r['name'] = '砲%s-%s%02d' % (pre, r['side'], cnt[(pre, r['side'])])
    rows.sort(key=lambda r: (list(GB['prefix']).index(r['deck']), r['chase'], r['side'], str(r['port'])))
    # 康塞普西翁號：退到 back_max 都找不到零碰撞的砲照實列出來、停（v0 直接在下面 KeyError 'phi'）
    fail = [[r['name'], r['deck'], r['type'], r.get('opening'), r.get('deck_z')] for r in rows if r.get('at') is None]
    if fail:
        print(json.dumps({'placed_none': fail}, ensure_ascii=False))
        raise SystemExit('✗ 放不下 %d 門（退到 back_max 都撞）' % len(fail))

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
    v['chase'] = [{k: r[k] for k in ('name', 'phi', 'at', 'back', 'off', 'muzzle_beyond', 'muzzle_free', 'axis_z', 'tried')} for r in rows if r['chase']]
    json.dump({'note': 'draft_guns.py 的結果；at ＝ 模型的 at（pivot 落點）、phi ＝ rotate z、P 舷 mirror=y', 'rows': rows},
              open(os.path.join(design, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(v, open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
