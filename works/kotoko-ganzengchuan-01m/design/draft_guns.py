# 福建趕繒船 新圖紙 07（TASK-1314 步驟 9）：火砲配置 —— 8 門 4 磅長砲（露天主甲板砲門）＋ 4 門佛郎機迴旋砲（艏／艉舷頂）
#   出處：kaguya-shachuan-01m/design/draft_guns.py ＋ Ship_Guns / Ship_Turrets §4.5
#   特性：先自 Step 4 靜態船殼算出迴旋砲舷頂淺豁口（z_top=60/50 ⇒ 40_crew.js 砲手站高 z0=b[2]-8 必覆蓋甲板且 [-80°,80°] 掃掠 0 碰撞），再依退到零碰撞搜出 12 門砲實位
#   用法：python -I -X utf8 draft_guns.py <design 資料夾> [--probe=push=砲M-S01:2.0|swivel_sweep=迴旋砲F-S01:-10]
import hashlib
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
from wio import export_list
from gunsim import Grid, Gun, load_guns


def r3(v):
    return [round(float(c), 3) for c in v]


def load_vox_map(path):
    arr = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    return {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in arr}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = a

    plan = HL.load_plan(design)
    GB = plan['guns_build']
    S = GB['search']
    YC = int(plan['space']['yc'])
    RED = int(plan['hull_build']['colors']['red']['v'])
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))

    # 自不可變步驟 4 遮罩組出基準船殼，算迴旋砲淺豁口，保證重跑逐位元組不變
    hull_base = load_vox_map(os.path.join(design, 'masks', 'hull', 'hull_01.vox.txt'))
    ports_carve = load_vox_map(os.path.join(design, 'masks', 'ports', 'carve.vox.txt'))
    for k in ports_carve:
        hull_base.pop(k, None)

    swivel_carve = {}
    swivel_paint = {}
    for sw in GB['swivels']:
        x0, x1, zr = int(sw['cut_x0']), int(sw['cut_x1']), int(sw['z_rail'])
        for k, col in list(hull_base.items()):
            x, y, z = k
            if x0 <= x <= x1 and z > zr:
                swivel_carve[k] = col
                hull_base.pop(k)
        # 朱紅押邊（z == zr 與兩端柱 x0-1, x1+1 上半部 z >= zr）
        for x in range(x0 - 1, x1 + 2):
            for y in range(YC - 36, YC + 37):
                for z in range(zr, zr + 6):
                    if (x, y, z) in hull_base and ((z == zr) or (x in (x0 - 1, x1 + 1) and z >= zr)):
                        swivel_paint[(x, y, z)] = RED

    # 建立對齊後的整船實心網格（移除尚未刻掉之 swivel_carve 格，令 build 前後一致）
    A_raw = export_list(GB['assembly'], None, links='all')
    cut_set = set(swivel_carve.keys())
    A_rows = [r for r in A_raw[:, :3].tolist() if tuple(r) not in cut_set]
    A_post = np.array(A_rows, dtype=np.int32)
    G = Grid(A_post, pad=16)

    Hs = set(hull_base.keys())
    decks = {}
    for k, w in GB['deck_works'].items():
        top = {}
        for x, y, z in export_list(w, None, links='none')[:, :3].tolist():
            if z + 1 > top.get((x, y), -1):
                top[(x, y)] = z + 1
        decks[k] = top

    guns = load_guns(GB, WORKS, export_list)

    def hull_y(x, z, side):
        ys = [y for y in range(0, 2 * YC + 1) if (x, y, z) in Hs]
        return (max(ys) + 1) if side > 0 else min(ys)

    def deck_top(dk, pts):
        zs = [decks[dk][p] for p in pts if p in decks[dk]]
        return max(zs) if zs else None

    def place_broadside(g, base_xy, d_out, phi, mirror, zd, offs, beyond_fn):
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
                    cand = {'at': r3(at), 'phi': phi, 'back': back, 'off': off, 'dz': dz,
                            'muzzle_beyond': round(float(beyond), 2), 'muzzle_free': tip_free,
                            'support': round(sup, 3), 'axis_z': round(float(tip[2]), 2), 'ok': ok}
                    key = (not ok, abs(dz), back, abs(off))
                    if best is None or key < best[0]:
                        best = (key, cand)
                    break
        return best

    rows = []
    # ── 1. 露天主甲板 4 對共 8 門 4 磅長砲（gun=4l）──
    gp = plan['ports']['gun']
    z_sill = int(plan['decks']['main']['floor']) + int(gp['sill'])  # 39
    zm = z_sill - 2  # 37（實心砲門下檻壁）
    for i, gx in enumerate(gp['x'], 1):
        x0 = gx - int(gp['w']) // 2
        x1 = gx + int(gp['w']) // 2 - (1 if int(gp['w']) % 2 == 0 else 0)
        g = guns[gp['gun']]
        xc = (x0 + x1 + 1) / 2.0
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            outs = [hull_y(x, zm, side) for x in (x0 - 2, x1 + 2)]
            outer = max(outs) if side > 0 else min(outs)
            yin = [outer - side * d for d in (8, 12, 16)]
            zd = deck_top('main', [(x, y) for x in (x0, int(xc), x1) for y in yin])
            d_out = g.direction(0.0, mirror)
            best = place_broadside(g, (xc, outer), d_out, 0.0, mirror, zd, S['dx'], lambda tip: (tip[1] - outer) * side)
            r = {'deck': 'main', 'port': i, 'side': nm, 'type': gp['gun'], 'chase': False, 'outer': outer, 'deck_z': zd,
                 'opening': {'x': [x0, x1], 'z': [z_sill, 48]}}
            r.update(best[1] if best else {'ok': False, 'at': None})
            rows.append(r)

    # ── 2. 尾樓 (x=86) 與艏樓 (x=294) 4 門佛郎機迴旋砲（pierrier + -mount），驗 [-80°, 80°] 掃掠 0 碰撞 ──
    gs = guns['pierrier']
    mt_cfg = GB['types']['pierrier']
    gm = Gun('pierrier_mount', {'work': mt_cfg['mount_work'], 'scale': mt_cfg['scale'], 'pivot': mt_cfg['pivot'], 'meta': {}},
             export_list(mt_cfg['mount_work'], None, links='none'), {}, S['inset'])

    def sweep_hits(at, mirror):
        hits = 0
        min_beyond = 1e9
        for deg in range(-80, 81, 5):
            hits += int(G.hit(gs.world(gs.samples, at, float(deg), mirror)).sum())
            hits += int(G.hit(gm.world(gm.samples, at, float(deg), mirror)).sum())
            tip = gs.world(gs.anchors['muzzle'][None], at, float(deg), mirror)[0]
            min_beyond = min(min_beyond, float((tip[1] - (outer if False else 0))))
        return hits

    for sw in GB['swivels']:
        x = int(sw['x'])
        floor_z = int(plan['decks'][sw['deck']]['floor'])
        for side, nm in ((1, 'S'), (-1, 'P')):
            mirror = side < 0
            zs = [z for (xx, y, z) in Hs if xx == x]
            ztop = max(zs)
            ys = [y for (xx, y, z) in Hs if xx == x and z == ztop]
            # 坐在淺豁口舷頂中線 (yr) 之上 ztop + dz
            yr = (max(ys) - 1) if side > 0 else (min(ys) + 1)
            outer = (max(ys) + 1) if side > 0 else min(ys)
            best = None
            for dz in range(1, 5):
                at = (x + 0.5, yr + 0.5, float(ztop + dz))
                shits = 0
                for deg in range(-80, 81, 5):
                    shits += int(G.hit(gs.world(gs.samples, at, float(deg), mirror)).sum())
                    shits += int(G.hit(gm.world(gm.samples, at, float(deg), mirror)).sum())
                if shits > 0:
                    continue
                tip = gs.world(gs.anchors['muzzle'][None], at, 0.0, mirror)[0]
                beyond = (tip[1] - outer) * side
                tip_free = not G.hit(tip[None])[0]
                crew_in_band = (float(ztop + dz) - 8) <= floor_z <= (float(ztop + dz) + 3)
                ok = bool(beyond > 0 and tip_free and crew_in_band)
                best = {'at': r3(at), 'phi': 0.0, 'back': 0, 'off': 0, 'dz': dz,
                        'muzzle_beyond': round(float(beyond), 2), 'muzzle_free': tip_free,
                        'support': 1.0, 'axis_z': round(float(tip[2]), 2), 'sweep_hits': shits,
                        'crew_z_ok': crew_in_band, 'ok': ok}
                break
            r = {'deck': sw['deck'], 'port': f'sw{x}', 'side': nm, 'type': 'pierrier', 'chase': False, 'outer': outer, 'deck_z': ztop}
            r.update(best or {'ok': False, 'at': None})
            rows.append(r)

    # ── 3. 命名與物件 ID（固定排序）──
    cnt = {}
    for r in rows:
        pre = GB['prefix'][r['deck']]
        kind = '迴旋砲' if r['type'] == 'pierrier' else '砲'
        cnt[(kind, pre, r['side'])] = cnt.get((kind, pre, r['side']), 0) + 1
        r['name'] = f'{kind}{pre}-{r["side"]}{cnt[(kind, pre, r["side"])]:02d}'
    rows.sort(key=lambda r: (r['type'] == 'pierrier', list(GB['prefix']).index(r['deck']), r['side'], str(r['port'])))
    for i, r in enumerate(rows, 1):
        r['id'] = f'gun-{i}'

    if probe:
        kind_p, rest = probe.split('=', 1)
        nm, val_s = rest.rsplit(':', 1)
        val = float(val_s)
        if kind_p == 'push':
            rep = {}
            for r in rows:
                g = guns[r['type']]
                at = np.array(r['at'], float)
                if r['name'] == nm:
                    d = g.direction(r['phi'], r['side'] == 'P')
                    at[:2] += d * val
                n = int(G.hit(g.world(g.samples, at, r['phi'], r['side'] == 'P')).sum())
                if n:
                    rep[r['name']] = n
            print(json.dumps({'probe': probe, 'hit_samples_by_gun': rep}, ensure_ascii=False))
            return
        elif kind_p == 'swivel_sweep':
            rep = {}
            for r in rows:
                if r['name'] == nm:
                    at = [r['at'][0], r['at'][1], r['at'][2] + val]
                    mirror = (r['side'] == 'P')
                    shits = sum(int(G.hit(gs.world(gs.samples, at, float(deg), mirror)).sum())
                                + int(G.hit(gm.world(gm.samples, at, float(deg), mirror)).sum())
                                for deg in range(-80, 81, 5))
                    rep[nm] = shits
            print(json.dumps({'probe': probe, 'sweep_hits': rep}, ensure_ascii=False))
            return

    # 驗證砲之間 0 碰撞＋對稱
    occ, clash = {}, []
    for r in rows:
        g = guns[r['type']]
        P = g.world(g.centers, r['at'], r['phi'], r['side'] == 'P')
        for c in set(map(tuple, np.floor(P).astype(int).tolist())):
            if c in occ and occ[c] != r['name']:
                clash.append([r['name'], occ[c]])
                break
            occ[c] = r['name']

    asym = []
    by = {(r['deck'], str(r['port']), r['side']): r for r in rows}
    for (dk, pt, sd), r in by.items():
        if sd != 'S':
            continue
        q = by.get((dk, pt, 'P'))
        if q and (abs(r['at'][0] - q['at'][0]) > 1e-6 or abs((2 * YC + 1 - r['at'][1]) - q['at'][1]) > 1e-6 or r['at'][2] != q['at'][2] or r['phi'] != -q['phi']):
            asym.append([r['name'], q['name'], r['at'], q['at']])

    assert all(r['ok'] for r in rows), f'有砲不合格：{[r for r in rows if not r["ok"]]}'
    assert not clash and not asym, f'碰撞或對稱異常：{clash=} {asym=}'

    os.makedirs(os.path.join(design, 'masks', 'guns'), exist_ok=True)
    p_sc = os.path.join(design, 'masks', 'guns', 'swivel_carve.vox.txt')
    p_sp = os.path.join(design, 'masks', 'guns', 'swivel_paint.vox.txt')
    with open(p_sc, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 福建趕繒船 步驟 9：艏／艉迴旋砲舷頂豁口刻除清單（帶守門色）x,y,z,color\n')
        for k in sorted(swivel_carve):
            f.write(f'{k[0]},{k[1]},{k[2]},{swivel_carve[k]}\n')
    with open(p_sp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 福建趕繒船 步驟 9：艏／艉迴旋砲舷頂朱漆護邊清單 x,y,z,color\n')
        for k in sorted(swivel_paint):
            f.write(f'{k[0]},{k[1]},{k[2]},{swivel_paint[k]}\n')

    v = {
        'read': {'assembly_voxels_post_cut': int(len(A_post)), 'swivel_cut_cells': len(swivel_carve), 'swivel_paint_cells': len(swivel_paint)},
        'guns': len(rows),
        'by_deck_type': {},
        'not_ok': [[r['name'], r.get('muzzle_beyond'), r.get('muzzle_free'), r.get('support')] for r in rows if not r['ok']],
        'gun_gun_clash': clash,
        'asymmetric_pairs': asym,
        'sha256': {
            'swivel_carve': sha256_file(p_sc),
            'swivel_paint': sha256_file(p_sp),
        },
    }
    for r in rows:
        k = f"{r['deck']}/{r['type']}"
        v['by_deck_type'][k] = v['by_deck_type'].get(k, 0) + 1
    for f in ('back', 'muzzle_beyond', 'support', 'axis_z', 'dz'):
        v[f] = {k: [min(r[f] for r in rows if f"{r['deck']}/{r['type']}" == k),
                    max(r[f] for r in rows if f"{r['deck']}/{r['type']}" == k)] for k in v['by_deck_type']}
    with open(os.path.join(design, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'note': 'draft_guns.py 的結果；8 門 4l + 4 門 pierrier', 'rows': rows}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
    print(json.dumps(v, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
