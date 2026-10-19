# 三叉戟號 砲門蓋板（造船規格 §9.12；basecamp-frigate-constitution-01m/design/tools/portlids.py 複製、改開頭的表＋三處，其他照原樣）
#   Tim 2026-10-19：「另外參考光榮號 把妳的船都加上炮門吧 GO」—— gura 的船只有三叉戟號（gura-trident-shark 是雕像）
#   哪幾層（設計決定）：下、中、上三層砲甲板（甲板-lower／middle／upper）—— 有天花板、砲門刻穿船殼。
#   · ⛔ 甲板-spar（艏樓＋後甲板那一層，露天、砲從舷牆的砲門伸出去）不做：§9.12「上層、艏樓的砲門通常沒有蓋板」；船頭砲台、船尾窗的三叉戟砲、追擊砲不做（開口量法找不到側牆上封閉的開口 ⇒ 自己會跳過）。
#   · 一層一件蓋板子作品（各層的開口一樣大、層與層不一樣 ⇒ 見 LIDS 上面的讀數）；一件掛 N 次（§2.2）。
#   · 顏色（三叉戟號的塗裝，design/plan.json）：關上朝外那一層 ＝ 紅帶 192（砲門那一排就是紅帶，關上之後帶子接起來）＋兩條鉸鏈板 73；貼船殼那一層也是 192（當時砲甲板裡面漆紅）。
#   跟 basecamp 原版不同的三處：① 匯出的快取照組裝件命名（三層共用一份組裝件）② placement／verify 一層一份（portlids_placement_<層>.json）③ 蓋板檔一種一份（masks/portlids/<種>.txt）。
#   用法同原版（在 Sculpture/works 底下任何地方都可以）：
#     python -I -X utf8 portlids.py draft  <cache 資料夾>
#     python -I -X utf8 portlids.py check  <cache 資料夾>
#     python -I -X utf8 portlids.py apply  <cache 資料夾> [層] [sub|models|all]
import hashlib, json, math, os, re, subprocess, sys, time
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
T = 'gura-tridente-01m'
PERSONA = 'gura'
# 一層一件（draft 量到：下層開口 12 × 9、中層 11 × 9、上層 10 × 8 —— 照砲的大小一層一種、層裡全一樣；三層共用的話 14 × 11，上層每邊多 2 格）
LIDS = {
    'lower': {'work': T + '-portlid-lower', 'parent': T, 'design': T, 'title': '三叉戟號 砲門蓋板・下層砲甲板（上緣鉸鏈，通用部件，0.1 m）'},
    'middle': {'work': T + '-portlid-middle', 'parent': T, 'design': T, 'title': '三叉戟號 砲門蓋板・中層砲甲板（上緣鉸鏈，通用部件，0.1 m）'},
    'upper': {'work': T + '-portlid-upper', 'parent': T, 'design': T, 'title': '三叉戟號 砲門蓋板・上層砲甲板（上緣鉸鏈，通用部件，0.1 m）'},
}
SHIPS = {
    'lower': {'asm': T + '-assembly', 'design': T, 'decks': ['甲板-lower'], 'lid': 'lower', 'name': '三叉戟號 下層砲甲板'},
    'middle': {'asm': T + '-assembly', 'design': T, 'decks': ['甲板-middle'], 'lid': 'middle', 'name': '三叉戟號 中層砲甲板'},
    'upper': {'asm': T + '-assembly', 'design': T, 'decks': ['甲板-upper'], 'lid': 'upper', 'name': '三叉戟號 上層砲甲板'},
}
COL = {'outer': 192, 'inner': 192, 'strap': 73}
RZ_FLAT = 2.0
HOUSE_MIN = 4
OUTLIER = 3                  # 蓋板範圍裡外表面離中位數超過 3 格的欄 ＝ 有東西貼著船殼凸出來（餘燼號上層 13 號砲門後緣的鐵件凸 12 格）⇒ 這一片不做
CLOSE_BIAS = -2.0            # close_deg 少 2°：船殼是凸的，照平面擬合的角度關上會切進鼓出來那一塊（遊戲匯入檢查 v1：憲法號 7、9 號 6–7% 落進船殼）；少 2° 底緣只離開約 0.4 格
SLAB = 16
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])


def sculpt(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def cached(cache, name, args):
    p = os.path.join(cache, name)
    if not os.path.exists(p):
        r = sculpt(args + ['out=' + p.replace('\\', '/')])
        if r.returncode:
            raise SystemExit('✗ 匯出 %s：%s' % (name, r.stdout[-600:]))
    return p


def load_list(p):
    A = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    return A.reshape(-1, 4) if A.size else np.zeros((0, 4), np.int32)


def ship_data(cache, s):
    S = SHIPS[s]
    L = load_list(cached(cache, S['asm'] + '.txt', ['op=export', 'persona=' + PERSONA, 'format=list', 'work=' + S['asm']]))
    P = json.load(open(cached(cache, S['asm'] + '.parts.json', ['op=export', 'persona=' + PERSONA, 'format=parts', 'work=' + S['asm']]), encoding='utf-8'))
    sx, sy, sz = P['size']
    occ = np.zeros((sx, sy, sz), bool)
    occ[L[:, 0], L[:, 1], L[:, 2]] = True
    return occ, P


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def r1(v, k=1):
    v = round(float(v), k)
    return int(v) if v == int(v) else v


def opening(occ, mz, yc):
    side = 1 if mz[1] > yc else -1
    xm, zm = int(math.floor(mz[0])), int(math.floor(mz[2]))
    win = occ[xm - 14:xm + 15, :, zm - 14:zm + 15]
    ys = np.nonzero(win.any(axis=(0, 2)))[0]
    ys = ys[ys > yc] if side > 0 else ys[ys < yc]
    yo = int(ys.max()) if side > 0 else int(ys.min())
    y0, y1 = (yo - SLAB, yo) if side > 0 else (yo, yo + SLAB)
    slab = occ[:, y0:y1 + 1, :].any(axis=1)
    if slab[xm, zm]:
        return None
    seen, st = {(xm, zm)}, [(xm, zm)]
    while st:
        x, z = st.pop()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, z + dz)
            if q in seen or slab[q]:
                continue
            if abs(q[0] - xm) > 25 or abs(q[1] - zm) > 25:
                return None
            seen.add(q)
            st.append(q)
    xs, zs = [c[0] for c in seen], [c[1] for c in seen]
    return {'side': side, 'x0': min(xs), 'x1': max(xs), 'z0': min(zs), 'z1': max(zs), 'cells': len(seen), 'yo': yo, 'slab': [y0, y1]}


def face(occ, x, z, side, slab):
    """(x, z) 那一欄、牆那一段裡最外面的格外面第一格空氣（S ＋1、P −1）；那一欄沒有格 ⇒ None。"""
    c = np.nonzero(occ[x, slab[0]:slab[1] + 1, z])[0]
    if not len(c):
        return None
    return int(slab[0] + c.max() + 1) if side > 0 else int(slab[0] + c.min() - 1)


def lid_cells(W, H):
    sx = (2, W - 3)
    c = {}
    for x in range(W):
        for y in range(H):
            c[(x, y, 0)] = COL['inner']
            c[(x, y, 1)] = COL['strap'] if (x in sx and y < H - 2) else COL['outer']
    return c


def host_models(host_work):
    return json.load(open(os.path.join(WORKS, host_work, 'models.json'), encoding='utf-8'))['models']


def draft(cache):
    found = {}
    for s, S in SHIPS.items():
        occ, P = ship_data(cache, s)
        yc = P['size'][1] / 2
        links = {l['path']: l for l in P['links']}
        guns = [m for m in P['models'] if (m.get('meta') or {}).get('kind') == 'gun' and m['path'].rsplit('/', 1)[0] in S['decks']]
        found[s] = (occ, P, yc, links, guns, [(g, opening(occ, np.array(g['points']['muzzle'], float), yc)) for g in guns])
    # 蓋板尺寸 ＝ 共用那件的幾艘裡最大的開口每邊 ＋1
    size = {}
    for s, f in found.items():
        ops_s = [o for g, o in f[5] if o]
        print('%s 開口 %d 個：寬 %s、高 %s' % (SHIPS[s]['name'], len(ops_s), sorted({o['x1'] - o['x0'] + 1 for o in ops_s}), sorted({o['z1'] - o['z0'] + 1 for o in ops_s})))
    for k in LIDS:
        ops = [o for s, f in found.items() if SHIPS[s]['lid'] == k for g, o in f[5] if o]
        size[k] = (max(o['x1'] - o['x0'] + 1 for o in ops) + 2, max(o['z1'] - o['z0'] + 1 for o in ops) + 2, 2)
    for k, Lw in LIDS.items():
        W, H, TH = size[k]
        cells = lid_cells(W, H)
        od = os.path.join(WORKS, Lw['design'], 'design', 'masks', 'portlids')
        os.makedirs(od, exist_ok=True)
        with open(os.path.join(od, k + '.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# %s（portlids.py draft；造船規格 §9.12）x,y,z,color —— 子作品 %s 自己的座標（畫開著：水平往外伸；y 0 ＝ 鉸鏈那一邊、z 0 ＝ 關上貼船殼那一層），stampvox at 0,0,0\n' % (Lw['title'], Lw['work']))
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
    lid_samp = {}
    for k, Lw in LIDS.items():
        Lc = load_list(os.path.join(WORKS, Lw['design'], 'design', 'masks', 'portlids', k + '.txt'))
        lid_samp[k] = (Lc[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
    ha_ = np.array([[0.5, 0.5, 0.5]])
    for s, (occ, P, yc, links, guns, ops) in found.items():
        S = SHIPS[s]
        W, H, TH = size[S['lid']]
        hb_ = np.array([[W - 0.5, 0.5, 0.5]])
        Lw = LIDS[S['lid']]
        rows, skipped = [], []
        for g, o in ops:
            host, gname = g['path'].rsplit('/', 1)
            if o is None:
                skipped.append({'gun': g['path'], 'id': g['meta']['id'], 'why': '砲口那一欄找不到封閉的開口（斜放／船尾板的追擊砲）'})
                continue
            L = links[host]
            assert L['box'][:3] == [0, 0, 0] and L.get('turn', 0) == 0 and not L.get('mirror'), (s, host, '甲板關聯不是 at 0、不轉、不鏡像')
            side = o['side']
            ow, oh = o['x1'] - o['x0'] + 1, o['z1'] - o['z0'] + 1
            xc = (o['x0'] + o['x1'] + 1) / 2
            lx0, lx1 = int(math.floor(xc - W / 2)), int(math.ceil(xc + W / 2)) - 1    # 蓋板關上蓋住的 x（含端點）
            hm_g = {m['name']: m for m in host_models(L['work'])}[gname]
            gw = place(gun_samples(cache, hm_g['work']), hm_g)
            # 鉸鏈貼開口上緣上面那一排；開著的蓋板壓到推出去的砲（夜燈號 5 號：砲頂 115.7、開口上緣 114）⇒ 整片往上抬一格再量，最多 3 格
            for raised in range(4):
                ztop = o['z1'] + 1 + raised
                lz0 = ztop - H + 1
                fc = {}
                for x in range(lx0, lx1 + 1):
                    for z in range(lz0, ztop + 1):
                        if o['x0'] <= x <= o['x1'] and o['z0'] <= z <= o['z1']:
                            continue
                        v = face(occ, x, z, side, o['slab'])
                        if v is not None:
                            fc[(x, z)] = v if side > 0 else 2 * yc - (v + 1)    # 外表面的角落座標，換成 S 舷的寫法（往外 ＝ ＋y）：S ＝ 第一格空氣的格號、P ＝ 它 ＋1，再對中線翻過來
                med = float(np.median(list(fc.values())))
                odd = sorted({x for (x, z), v in fc.items() if abs(v - med) > OUTLIER})
                if odd:
                    break
                top = [fc[(x, ztop)] for x in range(lx0, lx1 + 1) if (x, ztop) in fc]
                assert len(top) >= W - 2, (s, gname, '蓋板上緣那一排外表面量不到', len(top))
                pts = np.array([[x, z, y] for (x, z), y in sorted(fc.items())], float)
                xcm, zcm = pts[:, 0].mean(), pts[:, 1].mean()
                Am = np.c_[np.ones(len(pts)), pts[:, 0] - xcm, pts[:, 1] - zcm]
                coef, *_ = np.linalg.lstsq(Am, pts[:, 2], rcond=None)
                rz_fit, rx = math.degrees(math.atan(coef[1])), math.degrees(math.atan(coef[2]))
                rz = 0 if abs(rz_fit) <= RZ_FLAT else r1(rz_fit)
                close = r1(90 + rx + CLOSE_BIAS)
                surf = max(top)                                                        # 鉸鏈那一排的外表面（S 寫法）
                hy = int(round(surf if side > 0 else 2 * yc - surf))                   # 實際座標：S ＝ 第一格空氣的格號、P ＝ 第一格空氣的格號 ＋1 —— 兩舷都是 at.y（§9.12：P at.y ＝ 鉸鏈格 ＋1）
                at = [r1(xc, 2), hy, ztop]
                rot = rz if side > 0 else r1(180 - rz)
                pose = {'at': at, 'pivot': [r1(W / 2, 2), 0, 0], 'rotate': [0, 0, rot], 'scale': 1, 'mirror': 'none'}
                if sum(cross_hits(place(lid_samp[S['lid']], pose), gw)) == 0:
                    break
            else:
                raise SystemExit('✗ %s %s：鉸鏈抬 3 格開著的蓋板還是壓到砲' % (s, gname))
            if odd:
                skipped.append({'gun': g['path'], 'id': g['meta']['id'], 'why': '蓋板範圍裡有東西貼著船殼凸出 > %d 格（x %s；外表面中位數 %.1f）⇒ 開關都會撞' % (OUTLIER, odd, med)})
                continue
            # 收砲：砲口退到外表面往裡 1 格
            mz, br = np.array(g['points']['muzzle'], float), np.array(g['points']['breech'], float)
            ax = (mz - br) / np.linalg.norm(mz - br)
            ring = sorted(fc.values())
            outer = ring[len(ring) // 2]                                           # 這一圈外表面的中位數（S 寫法的角落座標）
            mys = mz[1] if side > 0 else 2 * yc - mz[1]
            need = max(0.0, round((mys - (outer - 1)) / abs(ax[1]), 2))
            # house：關上的蓋板（照遊戲的寫法繞鉸鏈反轉 close_deg）跟砲不碰，最少要沿砲軸縮幾格（0.5 一步）—— ⛔ 只照外表面估會少算蓋板的厚度與斜度（v1 量到少 2 格）
            cl = turn(place(lid_samp[S['lid']], pose), place(ha_, pose)[0], place(hb_, pose)[0] - place(ha_, pose)[0], -close)
            min_pull = next(k2 * 0.5 for k2 in range(0, 61) if sum(cross_hits(cl, gw - ax[None] * (k2 * 0.5))) == 0)
            house = max(HOUSE_MIN, int(math.ceil(min_pull + 0.5)))          # 至少留半格：遊戲照網格表面取樣（62_ports.js portHits），跟這裡的格心＋角落不一樣（v1 剛好等於 ⇒ 匯入檢查 ✗ 1–16 點）
            meta = {'kind': 'portlid', 'lid_of': g['meta']['id'], 'close_deg': close, 'house': house}
            rows.append({'model': '砲門蓋-' + re.sub(r'^砲-?', '', gname), 'gun_model': gname, 'gun_path': g['path'], 'host': host, 'host_work': L['work'],
                         'source_work': Lw['work'], 'side': 'S' if side > 0 else 'P', 'at': at, 'pivot': [r1(W / 2, 2), 0, 0], 'rotate': [0, 0, rot],
                         'scale': 1, 'mirror': 'none', 'meta': meta,
                         'open_x': [o['x0'], o['x1']], 'open_z': [o['z0'], o['z1']], 'open_size': [ow, oh], 'lid_x': [lx0, lx1], 'lid_z': [lz0, ztop], 'raised': raised,
                         'face': {'rz_fit': round(rz_fit, 2), 'rx': round(rx, 2), 'resid': round(float(np.abs(Am @ coef - pts[:, 2]).max()), 2), 'n': len(pts),
                                  'hinge_surf_s': r1(surf, 2)},
                         'gun': {'muzzle': [round(float(v), 2) for v in mz], 'axis': [round(float(v), 3) for v in ax], 'outer_s': outer, 'need_pull': need, 'min_pull': min_pull}})
        rows.sort(key=lambda r: (r['host'], r['open_x'][0], r['side']))
        out = {'note': 'portlids.py draft（造船規格 §9.12）—— %s：%d 片（%s），蓋板 %s %s；砲照組裝件 export parts、開口照組裝件 export list 量（見程式開頭）' % (
                   S['name'], len(rows), '、'.join(S['decks']), Lw['work'], list(size[S['lid']])),
               'lid': dict(Lw, size=list(size[S['lid']]), file=os.path.join(Lw['design'], 'design', 'masks', 'portlids', S['lid'] + '.txt').replace('\\', '/'),
                           cells=W * H * 2, sha256=hashlib.sha256(open(os.path.join(WORKS, Lw['design'], 'design', 'masks', 'portlids', S['lid'] + '.txt'), 'rb').read()).hexdigest(),
                           anchors={'hinge-a': [0, 0, 0], 'hinge-b': [W - 1, 0, 0]}, pivot=[r1(W / 2, 2), 0, 0], meters_per_voxel=0.1),
               'rows': rows, 'count': len(rows), 'skipped': skipped,
               'rules': {'rz_flat_deg': RZ_FLAT, 'house_min': HOUSE_MIN, 'house_margin': 0.5, 'slab': SLAB, 'outlier': OUTLIER, 'close_bias_deg': CLOSE_BIAS}}
        with open(os.path.join(WORKS, S['design'], 'design', 'portlids_placement_%s.json' % s), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write('\n')
        hs = sorted({r['meta']['house'] for r in rows})
        print('%s：%d 片、跳過 %d（%s）；蓋板 %s；rz %s；close %s–%s；house %s（至少縮 %s–%s）' % (
            S['name'], len(rows), len(skipped), [k['gun'] for k in skipped], list(size[S['lid']]), sorted({r['rotate'][2] for r in rows}),
            min(r['meta']['close_deg'] for r in rows), max(r['meta']['close_deg'] for r in rows), hs,
            min(r['gun']['min_pull'] for r in rows), max(r['gun']['min_pull'] for r in rows)))


_GUNS = {}


def gun_samples(cache, w):
    if w not in _GUNS:
        G = load_list(cached(cache, 'gun_' + w + '.txt', ['op=export', 'persona=' + PERSONA, 'format=list', 'work=' + w]))
        _GUNS[w] = (G[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
    return _GUNS[w]


def model_cells(cache, m):
    """一個外部模型實際佔的格（來源子作品的格心照擺法放）；繞 x、y 轉的、不是作品來源的 ⇒ None（退回外框）。"""
    if m.get('source', 'work') != 'work' or not m.get('work') or m['rotate'][0] or m['rotate'][1]:
        return None
    G = load_list(cached(cache, 'model_' + m['work'] + '.txt', ['op=export', 'persona=' + PERSONA, 'format=list', 'work=' + m['work']]))
    return np.floor(place(G[:, :3].astype(float) + 0.5, m)).astype(int)


# ───────────────────────── check ─────────────────────────
def place(Q, m):
    assert m['rotate'][0] == 0 and m['rotate'][1] == 0, m
    sc = m['scale'] if isinstance(m['scale'], list) else [m['scale']] * 3
    q = (np.asarray(Q, float) - np.array(m['pivot'], float)) * np.array(sc, float)
    if m['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    return rotz(q, m['rotate'][2]) + np.array(m['at'], float)


def turn(P, c, k, deg):
    k = k / np.linalg.norm(k)
    t = math.radians(deg)
    v = P - c
    return c + v * math.cos(t) + np.cross(k, v) * math.sin(t) + np.outer(v @ k, k) * (1 - math.cos(t))


def key(i):
    return (i[:, 0].astype(np.int64) * 1000 + i[:, 1]) * 1000 + i[:, 2]


def cells_of(P):
    return np.unique(key(np.floor(P).astype(np.int64)))


def cross_hits(A, B):
    return int(np.isin(key(np.floor(A).astype(np.int64)), cells_of(B)).sum()), int(np.isin(key(np.floor(B).astype(np.int64)), cells_of(A)).sum())


def check(cache):
    for s, S in SHIPS.items():
        PL = json.load(open(os.path.join(WORKS, S['design'], 'design', 'portlids_placement_%s.json' % s), encoding='utf-8'))
        LID = PL['lid']
        occ, P = ship_data(cache, s)
        sx, sy, sz = P['size']
        nvox = int(occ.sum())
        boxes = [m for m in P['models'] if (m.get('meta') or {}).get('kind') not in ('gun', 'portlid')]
        nbox = 0
        hm_all = {}
        for m in boxes:
            host, nm = m['path'].rsplit('/', 1) if '/' in m['path'] else ('', m['path'])
            hw = {l['path']: l for l in P['links']}.get(host, {}).get('work', S['asm'])
            if hw not in hm_all:
                try:
                    hm_all[hw] = {x['name']: x for x in host_models(hw)}
                except Exception:
                    hm_all[hw] = {}
            L0 = {l['path']: l for l in P['links']}.get(host)
            mm = hm_all[hw].get(nm)
            cells = model_cells(cache, mm) if (mm and (L0 is None or (L0['box'][:3] == [0, 0, 0] and not L0.get('turn') and not L0.get('mirror')))) else None
            if cells is not None:
                ok_ = (cells[:, 0] >= 0) & (cells[:, 0] < sx) & (cells[:, 1] >= 0) & (cells[:, 1] < sy) & (cells[:, 2] >= 0) & (cells[:, 2] < sz)
                cells = cells[ok_]
                occ[cells[:, 0], cells[:, 1], cells[:, 2]] = True
                continue
            nbox += 1
            b = m['box']
            occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])), max(0, int(math.floor(b[2]))):int(math.ceil(b[5]))] = True

        def in_ship(Pt):
            i = np.floor(Pt).astype(int)
            ok = (i[:, 0] >= 0) & (i[:, 0] < sx) & (i[:, 1] >= 0) & (i[:, 1] < sy) & (i[:, 2] >= 0) & (i[:, 2] < sz)
            i = i[ok]
            return int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())
        Lc = load_list(os.path.join(WORKS, LID['file']))
        lid_samp = (Lc[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
        ha = np.array([LID['anchors']['hinge-a']], float) + 0.5
        hb = np.array([LID['anchors']['hinge-b']], float) + 0.5
        corners = np.array([[x, y, z] for x in (0, LID['size'][0]) for y in (0, LID['size'][1]) for z in (0, LID['size'][2])], float)
        hm = {}
        for r in PL['rows']:
            if r['host_work'] not in hm:
                hm[r['host_work']] = {m['name']: m for m in host_models(r['host_work'])}

        def closed(m, cd):
            a, b = place(ha, m)[0], place(hb, m)[0]
            return turn(place(lid_samp, m), a, b - a, -cd), a, b
        pm = {m['path']: m for m in P['models']}
        rows = []
        for r in PL['rows']:
            side = 1 if r['side'] == 'S' else -1
            cd, house = r['meta']['close_deg'], r['meta']['house']
            g = hm[r['host_work']][r['gun_model']]
            gp = pm[r['gun_path']]
            assert (g.get('meta') or {}).get('id') == r['meta']['lid_of'], (r['model'], g.get('meta'))
            gw = place(gun_samples(cache, g['work']), g)
            ax = np.array(r['gun']['axis'], float)
            assert abs(ax[2]) < 1e-6, (r['gun_model'], '砲軸不水平')
            gin = gw - ax[None] * house
            op = place(lid_samp, r)
            cl, a, b = closed(r, cd)
            cc, hc = cl.mean(0), (a + b) / 2
            min_pull = None
            for k2 in range(0, 41):
                if sum(cross_hits(cl, gw - ax[None] * (k2 * 0.5))) == 0:
                    min_pull = k2 * 0.5
                    break
            oh, ch, c0 = cross_hits(op, gw), cross_hits(cl, gin), cross_hits(cl, gw)
            # 開著：蓋板底比砲高幾格
            foot = set(map(tuple, np.floor(op[:, :2]).astype(int).tolist()))
            under = np.array([tuple(v) in foot for v in np.floor(gw[:, :2]).astype(int).tolist()])
            clear = round(float(op[:, 2].min() - gw[under, 2].max()), 2) if under.any() else None
            # 開口蓋住沒：開口每一格的格心（外表面那一層）關上後在不在蓋板的佔用格 —— 照開口那一欄外表面往裡 0.5 格
            # 沿 y 看：開口每一欄 (x, z) 有沒有被關上的蓋板擋住（蓋板照 tumblehome 斜著貼，⛔ 不能拿一個 y 平面量）
            lidxz = set(map(tuple, np.floor(cl[:, [0, 2]]).astype(int).tolist()))
            hole = [(x, z) for x in range(r['open_x'][0], r['open_x'][1] + 1) for z in range(r['open_z'][0], r['open_z'][1] + 1)]
            covered = sum(1 for q in hole if q in lidxz)
            rec = {'model': r['model'], 'lid_of': r['meta']['lid_of'], 'side': r['side'], 'close_deg': cd, 'house': house,
                   'open': {'hits_ship': in_ship(op), 'hits_gun': oh[0] + oh[1], 'clear_above_gun': clear,
                            'box': [round(float(v), 3) for v in np.r_[place(corners, r).min(0), place(corners, r).max(0)]]},
                   'closed': {'hits_ship': in_ship(cl), 'ship_pct': round(100.0 * in_ship(cl) / len(cl), 2), 'hits_gun_housed': ch[0] + ch[1],
                              'center_below_hinge': round(float(hc[2] - cc[2]), 2), 'center_out_of_hinge': round(float((cc[1] - hc[1]) * side), 2),
                              'hole_covered': '%d/%d' % (covered, len(hole))},
                   'gun': {'housed_hits_ship': in_ship(gin), 'min_pull_clear_lid': min_pull, 'need_pull': r['gun']['need_pull']},
                   'hinge_a': [round(float(v), 3) for v in a], 'hinge_b': [round(float(v), 3) for v in b],
                   'reverse': {'house0_closed_hits_gun': c0[0] + c0[1]}}
            if r['side'] == 'P':
                mm = dict(r, rotate=[0, 0, round(r['rotate'][2] - 180, 3)], mirror='y')
                clm, am, bm = closed(mm, cd)
                rec['reverse']['mirror_y_center_below_hinge'] = round(float((am[2] + bm[2]) / 2 - clm.mean(0)[2]), 2)
            rows.append(rec)
        applied = None
        if sculpt(['op=work', 'sub=show', 'work=' + LID['work']]).returncode == 0:
            Wl = load_list(cached(cache, 'lid_' + LID['work'] + '.txt', ['op=export', 'persona=' + PERSONA, 'format=list', 'work=' + LID['work']]))
            want = {(x, y, z): c for x, y, z, c in Lc.tolist()}
            have = {(x, y, z): c for x, y, z, c in Wl.tolist()}
            anc = {x['name']: x['at'] for x in json.load(open(os.path.join(WORKS, LID['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
            bad, pts_d = [], 0.0
            for r, rec in zip(PL['rows'], rows):
                m = {mm['name']: mm for mm in host_models(r['host_work'])}.get(r['model'])
                if m is None:
                    bad.append(r['model'] + '：沒有')
                    continue
                mt = {k: v for k, v in (m.get('meta') or {}).items() if k != 'id'}
                if not (m['work'] == r['source_work'] and m['at'] == r['at'] and m['pivot'] == r['pivot'] and m['rotate'] == r['rotate'] and m['scale'] == [1, 1, 1] and m['mirror'] in ('', 'none') and mt == r['meta']):
                    bad.append(r['model'] + '：擺法或 meta 跟 placement 不一樣')
                p = pm.get(r['host'] + '/' + r['model'])
                if p:
                    pts_d = max(pts_d, float(np.abs(np.array(p['points']['hinge-a']) - np.array(rec['hinge_a'])).max()))
            applied = {'cells': len(have), 'missing': sum(1 for k in want if k not in have), 'extra': sum(1 for k in have if k not in want),
                       'color_diff': sum(1 for k, v in want.items() if k in have and have[k] != v), 'anchors_ok': all(anc.get(k) == v for k, v in LID['anchors'].items()),
                       'models_bad': bad, 'parts_hinge_max_diff': round(pts_d, 4)}
        tot = lambda f: sum(f(x) for x in rows)
        summary = {'lids': len(rows), 'open_hits_ship': tot(lambda x: x['open']['hits_ship']), 'open_hits_gun': tot(lambda x: x['open']['hits_gun']),
                   'closed_hits_gun_housed': tot(lambda x: x['closed']['hits_gun_housed']), 'gun_housed_hits_ship': tot(lambda x: x['gun']['housed_hits_ship']),
                   'closed_ship_pct_max': max(x['closed']['ship_pct'] for x in rows),
                   'closed_ship_pct_over5': [x['model'] for x in rows if x['closed']['ship_pct'] > 5],
                   'hole_not_covered': [x['model'] + ' ' + x['closed']['hole_covered'] for x in rows if x['closed']['hole_covered'].split('/')[0] != x['closed']['hole_covered'].split('/')[1]],
                   'center_below_hinge': [min(x['closed']['center_below_hinge'] for x in rows), max(x['closed']['center_below_hinge'] for x in rows)],
                   'center_out_of_hinge': [min(x['closed']['center_out_of_hinge'] for x in rows), max(x['closed']['center_out_of_hinge'] for x in rows)],
                   'house': sorted({x['house'] for x in rows}),
                   'house_slack': [min(x['house'] - x['gun']['min_pull_clear_lid'] for x in rows), max(x['house'] - x['gun']['min_pull_clear_lid'] for x in rows)],
                   'reverse_house0_lids_hit': sum(1 for x in rows if x['reverse']['house0_closed_hits_gun'] > 0),
                   'reverse_mirror_y_up': sum(1 for x in rows if x['side'] == 'P' and x['reverse']['mirror_y_center_below_hinge'] < 0),
                   'P': sum(1 for x in rows if x['side'] == 'P')}
        out = {'note': 'portlids.py check —— %s：現況 ＝ 組裝件 export list（%d 格）＋ 其他模型 %d 個（gun、portlid 以外；實際的格，%d 個退回外框：繞 x／y 轉或不在 at 0 的關聯裡）；蓋板每格 9 個取樣點' % (S['name'], nvox, len(boxes), nbox),
               'rows': rows, 'summary': summary, 'applied': applied}
        with open(os.path.join(WORKS, S['design'], 'design', 'verify_portlids_%s.json' % s), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write('\n')
        print(S['name'], json.dumps(summary, ensure_ascii=False, sort_keys=True))
        if applied:
            print('  掛上去：', json.dumps(applied, ensure_ascii=False, sort_keys=True))


# ───────────────────────── apply ─────────────────────────
def apply(cache, only=None, step='all'):
    ok = [0, 0]

    def cli(args):
        for k in range(5):
            r = sculpt(args)
            out = r.stdout + r.stderr
            if r.returncode and (r.returncode == 4 or 'IOException' in out) and k < 4:
                ok[1] += 1
                time.sleep(0.5)
                continue
            break
        if r.returncode:
            print('✗ rc=%d' % r.returncode, ' '.join(args[:6]))
            print(out[-1200:])
            raise SystemExit(1)
        ok[0] += 1
        return r.stdout

    def num(v):
        return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v

    def xyz(v):
        return ','.join(num(c) for c in v)
    done_lid = set()
    for s, S in SHIPS.items():
        if only and s != only:
            continue
        PL = json.load(open(os.path.join(WORKS, S['design'], 'design', 'portlids_placement_%s.json' % s), encoding='utf-8'))
        LID = PL['lid']
        if step in ('sub', 'all') and LID['work'] not in done_lid:
            done_lid.add(LID['work'])
            Wk = LID['work']
            if sculpt(['op=work', 'sub=show', 'work=' + Wk]).returncode != 0:
                cli(['op=work', 'sub=create', 'persona=' + PERSONA, 'id=' + Wk, 'title=' + LID['title'], 'size=' + xyz(LID['size']), 'parent_work=' + LID['parent'], 'tags=sub'])
                cli(['op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + Wk, 'meters_per_voxel=0.1'])
            have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + Wk])).group(1))
            if have == 0:
                o = cli(['op=stampvox', 'persona=' + PERSONA, 'work=' + Wk, 'voxels=' + os.path.join(WORKS, LID['file']).replace('\\', '/'), 'at=0,0,0',
                         'expect_pixels=%d' % LID['cells'], 'draft=0', 'share=0'])
                n = int(re.search(r'🔢 placed = (\d+)', o).group(1))
                if n != LID['cells']:
                    raise SystemExit('✗ %s placed %d ≠ %d' % (Wk, n, LID['cells']))
            elif have != LID['cells']:
                raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (Wk, have, LID['cells']))
            for nm, at in sorted(LID['anchors'].items()):
                cli(['op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + Wk, 'name=' + nm, 'at=' + xyz(at), 'overwrite=1',
                     'note=砲門蓋板的鉸鏈軸（上緣、貼船殼那一邊；造船規格 §9.12：從 hinge-a 看向 hinge-b 照右手定則正轉 ＝ 往上掀、反轉 close_deg ＝ 關上）'])
            print('✓ 子作品', Wk, LID['cells'], '格', LID['size'])
        if step in ('models', 'all'):
            want = {(r['host_work'], r['model']) for r in PL['rows']}
            hosts = sorted({r['host_work'] for r in PL['rows']})
            have = {}
            for hw in hosts:
                for m in host_models(hw):
                    if (m.get('meta') or {}).get('kind') == 'portlid':
                        have[(hw, m['name'])] = m
            for (hw, nm) in sorted(set(have) - want):                      # 這一版不做的（draft 跳過的）⇒ 拿掉
                cli(['op=work', 'sub=unmodel', 'persona=' + PERSONA, 'work=' + hw, 'name=' + nm])
                print('  拿掉', hw, nm)
            for r in PL['rows']:
                meta = dict(r['meta'])
                old = (have.get((r['host_work'], r['model'])) or {}).get('meta') or {}
                if 'id' in old:
                    meta['id'] = old['id']                                     # 已經發過的物件 id 照留（Blockside admin.py ids 發的；§12.2 改名挪位置都不變）
                cli(['op=work', 'sub=model', 'persona=' + PERSONA, 'work=' + r['host_work'], 'name=' + r['model'], 'source_work=' + r['source_work'],
                     'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=' + xyz(r['rotate']), 'scale=1', 'mirror=none', 'overwrite=1',
                     'meta=' + json.dumps(meta, ensure_ascii=False, sort_keys=True),
                     'note=%s 砲門蓋板 %s ↔ %s（portlids.py：畫開著、上緣鉸鏈；%s；kind=portlid 本身是裝飾）' % (
                         S['name'], r['model'], r['gun_model'], 'S 舷 rotate rz' if r['side'] == 'S' else 'P 舷 rotate 180 − rz（⛔ mirror=y）')])
            print('✓', S['name'], '模型', len(PL['rows']))
    print('ok', ok[0], 'IOException 重試', ok[1])


if __name__ == '__main__':
    cmd, cache = sys.argv[1], os.path.abspath(sys.argv[2])
    os.makedirs(cache, exist_ok=True)
    if cmd == 'draft':
        draft(cache)
    elif cmd == 'check':
        check(cache)
    elif cmd == 'apply':
        apply(cache, sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] in SHIPS else None, sys.argv[4] if len(sys.argv) > 4 else 'all')
    else:
        raise SystemExit('draft|check|apply')
