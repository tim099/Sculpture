# 階段十四：砲具與砲索 —— 船牆與甲板上的環首螺栓（每層甲板一件子作品，兩舷各自量、不鏡像）＋每門 5 條繩
# 設計 plan.json gunfittings（出處 provenance gunfittings）；砲 verify_guns.json（階段十二）；現況 ＝ 引擎匯出的組裝件格子（<exports>/ship_list.txt）。
# 從夜隼號 draft_gunfittings.py（階段十四）改：
#   · 兩舷不鏡像（下排 P1 的墊木 ⇒ 組裝件左右差 4、P1 的 at 跟 S1 不對稱）⇒ 每門自己量；
#   · 環的兩側照砲自己的 local x（eye-aft ＝ local x 小的那一側）換算成世界方向 ⇒ 船尾（rotate 90）、船頭（rotate −90）也走同一段；
#   · 牆面：從砲的 train 往砲口方向掃，在 outer ＋ scan_beyond_outer 以內第一格實心 ⇒ 環 ＝ 它前一格（牆內面第一格空氣）。
#   要求：環那一格空、不在任何一門砲（模型取樣點）裡；cascabel → 環、eye → 環、train → 甲板環 不穿過別的實心、不穿過別門砲（自己這門不算擋）。
# 輸出：masks/gunfittings/<lower|upper>.vox.txt（子作品座標）、verify_gunfittings.json（子作品框、anchors、ropes、讀數）
# 用法：python -I -X utf8 -B draft_gunfittings.py <design 資料夾> <exports 資料夾（有 ship_list.txt）>
import sys, os, json, math, hashlib
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); EX = os.path.abspath(sys.argv[2])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
F = plan['gunfittings']
NX, NY, NZ = plan['frame']['NX'], plan['frame']['NY'], plan['frame']['NZ_work']
VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
S = VG['scale']

a = np.loadtxt(os.path.join(EX, 'ship_list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
occ = np.zeros((NX, NY, NZ), bool); occ[a[:, 0], a[:, 1], a[:, 2]] = True


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    v = np.atleast_2d(v)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def place(Q, r):
    """子作品座標（連續）⇒ 世界：at ＋ R(scale × mirror(Q − pivot))（同 draft_guns.py place）。"""
    q = (np.atleast_2d(np.asarray(Q, float)) - np.asarray(r['pivot'], float)) * S
    if r['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    return rotz(q, r['rotate'][2]) + np.asarray(r['at'], float)


offs = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
tcells = {}
for t, tp in VG['types'].items():
    c = np.loadtxt(os.path.join(D, tp['file']), delimiter=',', dtype=int, comments='#', ndmin=2)[:, :3].astype(float)
    tcells[t] = (c[:, None, :] + offs[None]).reshape(-1, 3)
guns = {}
for r in VG['rows']:
    tp = VG['types'][r['type']]
    w = np.floor(place(tcells[r['type']], r)).astype(int)
    pts = {k: place(np.array(v, float) + 0.5, r)[0] for k, v in tp['anchors'].items()}
    o = place(np.zeros(3), r)[0]
    ex = place(np.array([1.0, 0, 0]), r)[0] - place(np.zeros(3), r)[0]; ex /= np.linalg.norm(ex)   # local +x 的世界方向
    ey = place(np.array([0, 1.0, 0]), r)[0] - place(np.zeros(3), r)[0]; ey /= np.linalg.norm(ey)   # local +y ＝ 砲口方向
    key = r['host_link'] + '/' + r['model']
    guns[key] = {'row': r, 'cells': set(map(tuple, w)), 'pts': pts, 'ex': np.round(ex).astype(int), 'ey': np.round(ey).astype(int)}
allgun = set().union(*(g['cells'] for g in guns.values()))


def line_hits(p, q, own, allow):
    p, q = np.asarray(p, float), np.asarray(q, float)
    n = int(np.linalg.norm(q - p) * 4) + 2
    hit = set()
    for t in np.linspace(0, 1, n):
        c = tuple(int(np.floor(v)) for v in p + (q - p) * t)
        if c in allow:
            continue
        if occ[c] or (c in allgun and c not in own):
            hit.add(c)
    return sorted(hit)


def rope_hits(p, q, rp, own, allow):
    """繩會下垂：拋物線 z −= 4·s·t(1−t)，s ＝ sag_k × L × √(3(slack − 1)／8)；管子半徑 ＝ 粗細 ⇒ 中心線與最低那一圈都量。
    🩸 第一版只量直線：船尾兩門的 breeching 垂了約 5 格，掉進牆內側的窗台（引擎 obj 抓到 192 個頂點）。
    sag_k：拋物線估算 vs 引擎 sub=ropes 的「最大下垂」（4 條：18.64→4.15、5.49→0.87、22.92→5.08、13.34→1.43）估算小了 5–15% ⇒ 乘 1.1。"""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = float(np.linalg.norm(q - p))
    s = F['sag_k'] * L * math.sqrt(3 * max(rp['slack'] - 1, 0) / 8)
    n = int(L * 4) + 2
    hit = set()
    d = (q - p) / max(L, 1e-9)
    side = np.cross(d, [0, 0, 1.0]); side = side / np.linalg.norm(side) if np.linalg.norm(side) > 1e-9 else np.array([1.0, 0, 0])
    # 管子：中心線、最低那一圈、左右兩側（🩸 第二版只量中心與最低：下排 S2／P2 的 breeching 側面擦到牆內側的窗台，obj 抓到 3＋3 個頂點）
    rings = [np.zeros(3), np.array([0, 0, -rp['thickness']]), side * rp['thickness'], -side * rp['thickness']]
    for t in np.linspace(0, 1, n):
        c0 = p + (q - p) * t
        c0[2] -= 4 * s * t * (1 - t)
        for dv in rings:
            c = tuple(int(np.floor(v)) for v in c0 + dv)
            if c in allow:
                continue
            if occ[c] or (c in allgun and c not in own):
                hit.add(c)
    return sorted(hit)


def build():
    R, DR, RP = F['ring'], F['deck_ring'], F['ropes']
    cells, anchors, ropes, notes, rows = {}, [], [], [], []
    for key, g in guns.items():
        r = g['row']; ex, ey = g['ex'], g['ey']
        dt = r['deck_top']
        ax_lat = int(np.argmax(np.abs(ex)))               # 環沿著牆排的那一軸
        ax_out = int(np.argmax(np.abs(ey)))               # 砲口那一軸
        lo, hi = r['opening_lat']
        row = {'gun': key, 'rings': {}, 'deck_ring': None}
        for side, sgn in (('aft', -1), ('fwd', 1)):        # local −x ＝ aft、local +x ＝ fwd
            wd = sgn * int(ex[ax_lat])                     # 這一側在世界那一軸上往哪邊
            edge = lo - 1 if wd < 0 else hi + 1
            done = None
            # 先試最低那一層的每個 offset，都不行才往上一層（舷側 ＋5 就過；船尾兩門 ＋5 的環正好在牆內側窗台上一格，breeching 一垂就掉進去）
            for za in R['z_above_deck']:
                z = dt + za
                for off in R['offset']:
                    lat = edge + wd * off
                    tr = g['pts']['train']
                    c = [0, 0, z]
                    c[ax_lat] = lat
                    start = int(np.floor(tr[ax_out])) - int(ey[ax_out]) * R['scan_back']
                    stop = r['outer'] + int(ey[ax_out]) * R['scan_beyond_outer']
                    k = None
                    s = start
                    while (s - stop) * int(ey[ax_out]) <= 0:
                        c[ax_out] = s
                        if occ[tuple(c)]:
                            c[ax_out] = s - int(ey[ax_out]); k = tuple(c); break
                        s += int(ey[ax_out])
                    # 牆離外板太深 ⇒ 那不是船牆（第一版船尾 AP 的環落到 x 121：外板 104 往裡 17 格的別的結構上）
                    if k is None or abs(r['outer'] - k[ax_out]) > R['max_wall_depth'] or occ[k] or k in allgun or k in cells:
                        continue
                    kc = np.array(k) + 0.5
                    h = rope_hits(g['pts']['cascabel'], kc, RP['breeching'], g['cells'], {k}) + rope_hits(g['pts']['eye-' + side], kc, RP['tackle'], g['cells'], {k})
                    if h:
                        continue
                    done = (off, k, za)
                    break
                if done:
                    break
            if done is None:
                notes.append(f'{key} 的 {side} 環：offset {R["offset"]} 都不行 ⇒ 不放，那一側 breeching／tackle 不掛')
                continue
            off, k, za = done
            cells[(r['host_link'], k)] = R['color']
            nm = f'ring-{r["model"][2:]}-{side}'
            anchors.append({'deck': r['host_link'], 'name': nm, 'kind': 'ring', 'world': list(k), 'gun': key, 'side': side})
            row['rings'][side] = {'offset': off, 'z_above_deck': za, 'cell': list(k)}
        tr = g['pts']['train']
        for back in DR['back']:
            b = np.floor(tr).astype(int) - ey * back
            # 甲板面照那一柱自己量：deck_top 是砲腳下那一格（墊木、舷邊高一格），往船裡退幾格甲板面會低 1–3 格（量過：下排 P1、上排 S1／S3／S8、船尾、船頭）
            zs = [zz for zz in range(dt - DR['surface_down'], dt + 1) if occ[(int(b[0]), int(b[1]), zz)] and not occ[(int(b[0]), int(b[1]), zz + 1)]]
            if not zs:
                continue
            k = (int(b[0]), int(b[1]), zs[-1] + 1)
            if occ[k] or k in allgun or (r['host_link'], k) in cells:
                continue
            if rope_hits(tr, np.array(k) + 0.5, RP['train'], g['cells'], {k}):
                continue
            cells[(r['host_link'], k)] = DR['color']
            anchors.append({'deck': r['host_link'], 'name': f'deck-{r["model"][2:]}', 'kind': 'deck_ring', 'world': list(k), 'gun': key})
            row['deck_ring'] = {'back': back, 'cell': list(k)}
            break
        if row['deck_ring'] is None:
            notes.append(f'{key} 的甲板環找不到位置 ⇒ train tackle 不掛')
        rows.append(row)
    RP = F['ropes']
    for row in rows:
        key = row['gun']; deck, model = key.split('/'); fl = deck + '/' + F['link']; tag = model[2:]
        gm = 'model:' + key
        for side in ('aft', 'fwd'):
            if side not in row['rings']:
                continue
            ring = f'{fl}/ring-{tag}-{side}'
            ropes.append(dict(name=f'{deck}.{model}.breeching-{side}', **{'from': gm + '/cascabel', 'to': ring}, **RP['breeching'], group='guns/breeching'))
            ropes.append(dict(name=f'{deck}.{model}.tackle-{side}', **{'from': f'{gm}/eye-{side}', 'to': ring}, **RP['tackle'], group='guns/tackle'))
        if row['deck_ring']:
            ropes.append(dict(name=f'{deck}.{model}.train', **{'from': gm + '/train', 'to': f'{fl}/deck-{tag}'}, **RP['train'], group='guns/train'))
    return cells, anchors, ropes, notes, rows


def main():
    cells, anchors, ropes, notes, rows = build()
    out_works, stamps = [], []
    for deck, work in F['works'].items():
        ks = [k for (d, k) in cells if d == deck]
        if not ks:
            continue
        A = np.array(ks)
        if deck in F.get('frames', {}):                    # 子作品已經建好 ⇒ 框照建好的（框是決定，不從這一次的環推；第二版的環要落在裡面）
            fa = np.array(F['frames'][deck]['at']); fs = np.array(F['frames'][deck]['size'])
            assert (A >= fa).all() and (A < fa + fs).all(), (deck, '環落在子作品框外')
        else:
            fa = A.min(0) - F['margin']; fs = A.max(0) - fa + 1 + F['margin']
        txt = '# 風暴角號砲具（%s）draft_gunfittings.py —— 子作品座標 x,y,z,color；世界 ＝ ＋frame_at %s\n' % (deck, ','.join(map(str, fa))) + \
              ''.join(f'{k[0] - fa[0]},{k[1] - fa[1]},{k[2] - fa[2]},{cells[(deck, k)]}\n' for k in sorted(ks))
        tag = 'lower' if deck == '甲板-下' else 'upper'
        path = os.path.join(D, 'masks', 'gunfittings', tag + '.vox.txt')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w', encoding='utf-8', newline='\n').write(txt)
        for an in anchors:
            if an['deck'] == deck:
                an['at'] = [int(v) for v in np.array(an['world']) - fa]
                an['work'] = work
        out_works.append({'deck': deck, 'work': work, 'title': F['titles'][deck], 'frame_at': [int(v) for v in fa], 'frame_size': [int(v) for v in fs],
                          'link_in': [r['host_work'] for r in VG['rows'] if r['host_link'] == deck][0], 'link': F['link']})
        stamps.append({'work': work, 'op': 'stampvox', 'file': 'masks/gunfittings/%s.vox.txt' % tag, 'at': [0, 0, 0], 'voxels': len(ks),
                       'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()})
    out = {'note': 'draft_gunfittings.py（階段十四）—— 現況 ＝ 引擎匯出 %s（%d 格）＋ verify_guns.json' % (os.path.relpath(EX, os.path.dirname(D)).replace('\\', '/'), len(a)),
           'works': out_works, 'stamp_order': stamps, 'anchors': anchors, 'ropes': ropes, 'rows': rows, 'notes': notes,
           'counts': {'ring_cells': len(cells), 'anchors': len(anchors), 'ropes': len(ropes), 'guns': len(rows)}}
    with open(os.path.join(D, 'verify_gunfittings.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for row in rows:
        print(row['gun'], {s: (v['offset'], v['cell']) for s, v in row['rings'].items()}, 'deck', row['deck_ring'] and (row['deck_ring']['back'], row['deck_ring']['cell']))
    print(out['counts'])
    for m in notes:
        print('⚠', m)


if __name__ == '__main__':
    main()
