# 三叉戟號 階段八（TASK-0561）砲：一門一個外部模型（借現成的砲子作品，plan.json guns.types），擺在所在甲板的子作品上
#   做法照風暴角號 draft_guns.py（summit，階段十二）與造船規格 §4.2：橫向對準砲門中線（再試 ±0.5…±1.5），沿砲口方向從牆外往裡退（每步 0.5 格），
#   退到「模型每一格的格心＋八個角都不在現況的實心裡」；排序：輪子全著地 ＞ 砲口伸出牆外 ≥ min_muzzle_out ＞ 置中 ＞ 推得出去。
#   船頭追擊砲照角度搜（取推得出去的最大角）；船尾追擊砲 rotate 90（砲口 −x）。
#   模型座標 world ＝ at ＋ Rz(rotate) · mirror_y( scale · (Q − pivot) )；pivot ＝ 砲架底層最前緣那一排、軸線中間、z 0（Q 是格的角落座標，格心 ＋0.5）。
#   現況 ＝ 引擎匯出的組裝件（links=all，含 channels）＋ 模型外框（export format=parts）＋ 先擺好的砲；牆外面 ＝ 只看船殼那一條關聯。
#   輸出：verify_guns.json（每門：host、at、rotate、mirror、scale、pivot、meta、讀數）。重跑逐位元組相同。
#   用法：python -I -X utf8 draft_guns.py <design> [--base=<快取.npz>]
import sys, os, json, math, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import deco_base as DB

NX, NY, NZ = 1100, 400, 260
WORKS = None


def anchors_of(work):
    A = json.load(open(os.path.join(WORKS, work, 'anchors.json'), encoding='utf-8'))['anchors']
    return {a['name']: a['at'] for a in A}


def parts_boxes():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def main():
    global WORKS
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    WORKS = os.path.dirname(os.path.dirname(design))
    cache = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--base=')), None)
    plan = HL.load_plan(design)
    GN = plan['guns']
    SR = GN['search']
    YC = plan['space']['yc']

    # ── 砲的型：格子、pivot、固定點（子作品座標）──
    types = {}
    for key, T in sorted(GN['types'].items()):
        C = DB.export_list(T['work'], None)
        z0 = int(C[:, 2].min())
        assert z0 == 0, (key, '砲的最底層不在 z 0', z0)
        an = anchors_of(T['work'])
        ax = an['muzzle'][0] + 0.5
        assert an['breech'][0] == an['muzzle'][0], (key, '砲軸不平行 y')
        bot = C[C[:, 2] == 0]
        piv = np.array([ax, float(bot[:, 1].max() + 1), 0.0])
        cells = C[:, :3].astype(float)
        offs = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
        samp = (cells[:, None, :] + offs[None]).reshape(-1, 3)
        bs = np.array([[x + ox, y + oy, 0.0] for x, y, _ in bot[:, :3] for ox in (0.3, 0.7) for oy in (0.3, 0.7)])
        cs = {(x, y, z): c for x, y, z, c in C.tolist()}
        asym = sum(1 for (x, y, z), c in cs.items() if cs.get((int(2 * ax - 1 - x), y, z)) != c)
        types[key] = {'T': T, 'samp': samp, 'bs': bs, 'piv': piv, 'an': an, 'cells': len(C), 'asym_x': asym,
                      'size': [int(v) for v in C[:, :3].max(0) + 1]}
        print('型', key, T['work'], '格', len(C), '框', types[key]['size'], 'pivot', piv.tolist(), '左右不對稱', asym)

    # ── 現況 ──
    if cache and os.path.exists(cache):
        z = np.load(cache)
        occ, hull = z['occ'], z['hull']
    else:
        A = DB.export_list(DB.ASM, 'all')
        A = A[A[:, 2] < NZ]
        occ = np.zeros((NX, NY, NZ), bool)
        occ[A[:, 0], A[:, 1], A[:, 2]] = True
        H = DB.export_list(DB.ASM, '船殼')
        H = H[H[:, 2] < NZ]
        hull = np.zeros((NX, NY, NZ), bool)
        hull[H[:, 0], H[:, 1], H[:, 2]] = True
        if cache:
            np.savez_compressed(cache, occ=occ, hull=hull)
    nvox = int(occ.sum())
    boxes = parts_boxes()
    for m in boxes:
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
    guns = np.zeros_like(occ)

    def outer_y(x, z, side):
        """船殼在 (x, z) 那一排、那一舷最外面那格的外側面（S：max＋1；P：min）。"""
        col = np.nonzero(hull[int(x), :, int(z)])[0]
        col = col[col > YC] if side > 0 else col[col < YC]
        if len(col) == 0:
            return None
        return float(col.max() + 1) if side > 0 else float(col.min())

    def stern_x(y, z):
        row = np.nonzero(hull[:, int(y), int(z)])[0]
        return float(row.min())

    def place(tp, at, rot, mir):
        q = (tp['samp'] - tp['piv']) * tp['T']['scale']
        if mir:
            q[:, 1] = -q[:, 1]
        return rotz(q, rot) + np.asarray(at)

    def point(tp, nm, at, rot, mir):
        q = (np.array(tp['an'][nm], float) + 0.5 - tp['piv'])[None] * tp['T']['scale']
        if mir:
            q[:, 1] = -q[:, 1]
        return (rotz(q, rot) + np.asarray(at))[0]

    def hit(W):
        i = np.floor(W).astype(int)
        ok = (i[:, 0] >= 0) & (i[:, 0] < NX) & (i[:, 1] >= 0) & (i[:, 1] < NY) & (i[:, 2] >= 0) & (i[:, 2] < NZ)
        h = np.ones(len(W), bool)
        h[ok] = occ[i[ok, 0], i[ok, 1], i[ok, 2]] | guns[i[ok, 0], i[ok, 1], i[ok, 2]]
        return h

    def support(tp, at, rot, mir):
        q = (tp['bs'] - tp['piv']) * tp['T']['scale']
        if mir:
            q[:, 1] = -q[:, 1]
        i = np.floor(rotz(q, rot) + np.asarray(at)).astype(int)
        return [int(occ[i[:, 0], i[:, 1], i[:, 2] - 1].sum()), len(i)]

    def search(tp, lat_axis, lat, start, dvec, zs, rot, mir, beyond_fn):
        """回 (排序鍵, 候選)；start ＝ pivot 放在牆外面那一點（沿砲口方向的座標）。"""
        best = None
        for dl in SR['dl']:
            if best is not None and abs(dl) > best[0][2] and not best[0][0] and not best[0][1]:
                break                                                   # 排序鍵：理想 ＞ 置中 ⇒ 更偏的那一組不可能贏，不用試
            for zt in zs:
                for kb in range(int(SR['max_back'] / SR['step']) + 1):
                    back = kb * SR['step']
                    at = np.array(start, float)
                    at[lat_axis] += dl
                    at[:2] -= dvec[:2] * back
                    at[2] = zt
                    if hit(place(tp, at, rot, mir)).any():
                        continue
                    tip = point(tp, 'muzzle', at, rot, mir)
                    sup = support(tp, at, rot, mir)
                    out = beyond_fn(tip)
                    cand = {'at': [round(float(v), 3) for v in at], 'dl': dl, 'back': back, 'muzzle_out': round(out, 3), 'support': sup,
                            'muzzle': [round(float(v), 3) for v in tip], 'breech': [round(float(v), 3) for v in point(tp, 'breech', at, rot, mir)]}
                    k = (sup[0] < sup[1], out < SR['min_muzzle_out'], abs(dl), zs.index(zt), back)
                    if best is None or k < best[0]:
                        best = (k, cand)
                    break
        return best

    def commit(tp, c, rot, mir):
        i = np.floor(place(tp, c['at'], rot, mir)).astype(int)
        guns[i[:, 0], i[:, 1], i[:, 2]] = True

    rows, fails = [], []
    ports = LY.ports(plan)
    bow = GN['chase']['bow']
    for p in ports:
        typ = GN['rows'][p['deck']]
        if isinstance(typ, list):
            typ = typ[(p['i'] - 1) % len(typ)]
        chase = p['deck'] == bow['deck'] and p['i'] == bow['port']
        if chase:
            typ = bow['type']
        tp = types[typ]
        xc = (p['x0'] + p['x1'] + 1) / 2.0
        dz = float(LY.deck_z(plan, p['deck'], xc))
        zs = [dz + d for d in SR['dz']]
        for side, nm in ((1, 'S'), (-1, 'P')):
            mir = side < 0
            o = outer_y(xc, p['z0'] - 1, side)

            def beyond(tip, side=side, z=p['z0'] - 1):
                ob = outer_y(min(NX - 1, max(0, math.floor(tip[0]))), z, side)
                return -99.0 if ob is None else float((tip[1] - ob) * side)
            if not chase:
                best = search(tp, 0, xc, [xc, o, 0], np.array([0.0, side, 0.0]), zs, 0, mir, beyond)
                rot = 0
            else:
                best, rot = None, 0
                for a in sorted(bow['angles'], reverse=True):
                    r = -a if side > 0 else a
                    d = rotz(np.array([[0.0, float(side), 0.0]]), r)[0]
                    b = search(tp, 0, xc, [xc, o, 0], d, zs, r, mir, beyond)
                    if b is not None and not b[0][0] and not b[0][1]:
                        best, rot = b, r
                        break
            if best is None:
                fails.append('%s-%s%02d' % (p['deck'], nm, p['i']))
                continue
            c = best[1]
            commit(tp, c, rot, mir)
            meta = {'kind': 'gun', 'gun': tp['T']['code'], 'side': nm, 'port': p['i'], 'deck': p['deck']}
            if chase:
                meta['arc'] = 'bow'
            rows.append(dict({'model': '砲-%s%02d' % (nm, p['i']), 'host_link': '甲板-' + p['deck'], 'host_work': 'gura-tridente-01m-deck-' + p['deck'],
                              'type': typ, 'work': tp['T']['work'], 'rotate': [0, 0, rot], 'mirror': 'y' if mir else 'none', 'scale': tp['T']['scale'],
                              'pivot': tp['piv'].tolist(), 'meta': meta, 'port_x': [p['x0'], p['x1']], 'port_z': [p['z0'], p['z1']], 'outer': o, 'deck_z': dz}, **c))
    # 船尾追擊砲：中砲甲板船尾窗那一列 kind=port
    VP = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))
    st = GN['chase']['stern']
    for k, w in enumerate(w for w in VP['windows'] if w['kind'] == 'port' and w['deck'] == st['deck']):
        tp = types[st['type']]
        yc = (w['y0'] + w['y1'] + 1) / 2.0
        xs = stern_x(yc, w['z0'] - 1)
        dz = float(LY.deck_z(plan, w['deck'], xs + 20))
        zs = [dz + d for d in SR['dz']]
        nm = 'S' if yc > YC else 'P'
        best = search(tp, 1, yc, [xs, yc, 0], np.array([-1.0, 0.0, 0.0]), zs, 90, False,
                      lambda tip, z=w['z0'] - 1: float(stern_x(min(NY - 1, max(0, math.floor(tip[1]))), z) - tip[0]))
        if best is None:
            fails.append('stern-%s' % nm)
            continue
        c = best[1]
        commit(tp, c, 90, False)
        rows.append(dict({'model': '追擊砲-船尾-%s' % nm, 'host_link': '甲板-' + w['deck'], 'host_work': 'gura-tridente-01m-deck-' + w['deck'], 'type': st['type'],
                          'work': tp['T']['work'], 'rotate': [0, 0, 90], 'mirror': 'none', 'scale': tp['T']['scale'], 'pivot': tp['piv'].tolist(),
                          'meta': {'kind': 'gun', 'gun': tp['T']['code'], 'side': nm, 'port': w['j'], 'deck': w['deck'], 'arc': 'stern'},
                          'port_y': [w['y0'], w['y1']], 'port_z': [w['z0'], w['z1']], 'outer': xs, 'deck_z': dz}, **c))

    # ── 墊木（同風暴角號）：甲板舷弧取整是一階一階的，一階落在砲架底下 ⇒ 一側輪子懸空 1 格；
    #    懸空的輪底（模型 z 0 那一層的取樣點）正下方的空格往下補到碰到實心，格放在那一層甲板的子作品、甲板板的顏色 ──
    plank = plan['decks_build']['plank']
    pads = {}
    for r in rows:
        if r['support'][0] == r['support'][1]:
            r['pad_cells'] = 0
            continue
        tp = types[r['type']]
        q = (tp['bs'] - tp['piv']) * tp['T']['scale']
        if r['mirror'] == 'y':
            q[:, 1] = -q[:, 1]
        w = rotz(q, r['rotate'][2]) + np.asarray(r['at'])
        col = plank['weather'] if r['meta']['deck'] in ('spar', 'poop') else plank['gun']
        n0 = 0
        for x, y in sorted({(int(math.floor(p[0])), int(math.floor(p[1]))) for p in w}):
            z = int(round(r['at'][2])) - 1
            k = 0
            while not occ[x, y, z - k]:
                assert k < 2, (r['model'], r['host_link'], '墊木要補超過 2 格', x, y)
                k += 1
            for j in range(k):
                c = (x, y, z - j)
                if c not in pads.setdefault(r['host_work'], {}):
                    pads[r['host_work']][c] = col
                    n0 += 1
        for c in pads[r['host_work']]:
            occ[c] = True
        i = np.floor(w).astype(int)
        r['pad_cells'] = n0
        r['support_after_pad'] = [int(occ[i[:, 0], i[:, 1], i[:, 2] - 1].sum()), len(i)]
    pad_files = {}
    for hw, cells in sorted(pads.items()):
        fn = 'masks/guns/pads_%s.vox.txt' % hw.rsplit('-', 1)[1]
        os.makedirs(os.path.join(design, 'masks', 'guns'), exist_ok=True)
        with open(os.path.join(design, fn), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 三叉戟號 砲的墊木（draft_guns.py）x,y,z,color —— %s，at 0,0,0\n' % hw)
            for c, v in sorted(cells.items()):
                f.write('%d,%d,%d,%d\n' % (c + (v,)))
        pad_files[hw] = {'file': fn, 'voxels': len(cells)}

    bad = [r['model'] + '@' + r['host_link'] for r in rows if r.get('support_after_pad', r['support'])[0] < r['support'][1] or r['muzzle_out'] < SR['min_muzzle_out']]
    by = {}
    for r in rows:
        by[r['meta']['gun']] = by.get(r['meta']['gun'], 0) + 1
    out = {'note': 'draft_guns.py（階段八）—— 現況 ＝ 組裝件 links=all（%d 格，z < %d）＋ 模型外框 %d' % (nvox, NZ, len(boxes)),
           'types': {k: {'work': v['T']['work'], 'code': v['T']['code'], 'scale': v['T']['scale'], 'pivot': v['piv'].tolist(), 'cells': v['cells'],
                         'size': v['size'], 'asym_x': v['asym_x'], 'anchors': v['an']} for k, v in types.items()},
           'rows': rows, 'count': len(rows), 'by_code': dict(sorted(by.items())), 'pads': pad_files, 'not_ideal': bad, 'fails': fails}
    with open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print('砲 %d 門 %s；墊木 %s；不理想（墊完輪子還懸空、或砲口沒伸出）%s；放不進去 %s' % (
        len(rows), out['by_code'], {k: v['voxels'] for k, v in pad_files.items()}, bad, fails))


if __name__ == '__main__':
    main()
