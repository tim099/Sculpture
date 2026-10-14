# 三叉戟號（TASK-0575）砲具與砲索：船牆與甲板上的環首螺栓（每層砲甲板一件子作品，關聯在那一層甲板子作品裡 ⇒ 藏甲板一起藏）＋每門 5 條繩
#   改自風暴角號 draft_gunfittings.py（summit，階段十四）—— 她撞過的坑照帶：繩會下垂（拋物線、sag_k 1.1）、管子量中心＋最低一圈＋左右兩側、
#   牆離外板 ≤ max_wall_depth（不然是別的結構）、環的高度先試低的、甲板環的甲板面照那一柱自己量、每門自己量（兩舷不鏡像）。
#   差別：① 四層砲甲板；② 砲借別人的子作品 ⇒ 格子從引擎匯出（export format=list）；③ 「是不是自己這門砲」用記砲編號的格子陣列（138 門、上百萬格）；
#        ④ obús（carronade）沒有 train 固定點 ⇒ 不掛 train tackle（滑座砲）。
#   現況 ＝ 組裝件 links=all（藏本階段的 砲具 關聯）＋ 不是砲的模型外框 ＋ 砲（verify_guns.json 的擺法，格心＋八角）。
#   輸出：masks/gunfittings/<層>.vox.txt（子作品座標）、verify_gunfittings.json。用法：python -I -X utf8 draft_gunfittings.py <design>
import sys, os, json, math, hashlib, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import deco_base as DB

NX, NY = 1100, 400
Z0, Z1 = 60, 200                                                     # 砲甲板那一段（陣列只開這一段）


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    v = np.atleast_2d(v)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def place(Q, r):
    q = (np.atleast_2d(np.asarray(Q, float)) - np.asarray(r['pivot'], float)) * r['scale']
    if r['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    return rotz(q, r['rotate'][2]) + np.asarray(r['at'], float)


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    works = os.path.dirname(os.path.dirname(D))
    plan = HL.load_plan(D)
    F = plan['gunfittings']
    VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
    hide = ','.join('%s/%s' % (dk, F['link']) for dk in F['works'])
    try:
        A = DB.export_list(DB.ASM, 'all', ('hide_links=' + hide,))
    except SystemExit:
        A = DB.export_list(DB.ASM, 'all')                             # 第一次：砲具關聯還不存在
    A = A[(A[:, 2] >= Z0) & (A[:, 2] < Z1)]
    occ = np.zeros((NX, NY, Z1 - Z0), bool)
    occ[A[:, 0], A[:, 1], A[:, 2] - Z0] = True
    nbox = 0
    for m in parts():
        if (m.get('meta') or {}).get('kind') == 'gun':
            continue
        b = m['box']
        if b[5] <= Z0 or b[2] >= Z1:
            continue
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2])) - Z0):min(Z1 - Z0, int(math.ceil(b[5])) - Z0)] = True
        nbox += 1

    offs = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
    tc, tan = {}, {}
    for t, tp in VG['types'].items():
        c = DB.export_list(tp['work'], None)[:, :3].astype(float)
        tc[t] = (c[:, None, :] + offs[None]).reshape(-1, 3)
        tan[t] = json.load(open(os.path.join(works, tp['work'], 'anchors.json'), encoding='utf-8'))['anchors']
        tan[t] = {a['name']: a['at'] for a in tan[t]}
    gid = np.zeros((NX, NY, Z1 - Z0), np.int16)                       # 0 ＝ 沒有砲；i ＋ 1 ＝ 第 i 門
    guns = []
    for i, r in enumerate(VG['rows']):
        w = np.floor(place(tc[r['type']], r)).astype(int)
        gid[w[:, 0], w[:, 1], w[:, 2] - Z0] = i + 1
        pts = {k: place(np.array(v, float) + 0.5, r)[0] for k, v in tan[r['type']].items()}
        ex = place(np.array([1.0, 0, 0]), r)[0] - place(np.zeros(3), r)[0]
        ey = place(np.array([0, 1.0, 0]), r)[0] - place(np.zeros(3), r)[0]
        guns.append({'row': r, 'id': i + 1, 'pts': pts, 'ex': np.round(ex / np.linalg.norm(ex)).astype(int), 'ey': np.round(ey / np.linalg.norm(ey)).astype(int)})

    def blocked(c, own, allow):
        if c in allow:
            return False
        x, y, z = c
        if not (0 <= x < NX and 0 <= y < NY and Z0 <= z < Z1):
            return True
        g = gid[x, y, z - Z0]
        return bool(occ[x, y, z - Z0]) or (g != 0 and g != own)

    def rope_hits(p, q, rp, own, allow):
        p, q = np.asarray(p, float), np.asarray(q, float)
        L = float(np.linalg.norm(q - p))
        s = F['sag_k'] * L * math.sqrt(3 * max(rp['slack'] - 1, 0) / 8)
        n = int(L * 4) + 2
        d = (q - p) / max(L, 1e-9)
        side = np.cross(d, [0, 0, 1.0])
        side = side / np.linalg.norm(side) if np.linalg.norm(side) > 1e-9 else np.array([1.0, 0, 0])
        rings = [np.zeros(3), np.array([0, 0, -rp['thickness']]), side * rp['thickness'], -side * rp['thickness']]
        hit = set()
        for t in np.linspace(0, 1, n):
            c0 = p + (q - p) * t
            c0[2] -= 4 * s * t * (1 - t)
            for dv in rings:
                c = tuple(int(np.floor(v)) for v in c0 + dv)
                if blocked(c, own, allow):
                    hit.add(c)
        return sorted(hit)

    R, DR, RP = F['ring'], F['deck_ring'], F['ropes']
    cells, anchors, rows, notes = {}, [], [], []
    for g in guns:
        r = g['row']
        ex, ey = g['ex'], g['ey']
        dt = int(round(r['at'][2])) - 1                                # 砲腳下那一格
        ax_lat = int(np.argmax(np.abs(ex)))
        ax_out = int(np.argmax(np.abs(ey)))
        lo, hi = r.get('port_x') or r.get('port_y')
        key = r['host_link'] + '/' + r['model']
        row = {'gun': key, 'rings': {}, 'deck_ring': None}
        for side, sgn in (('aft', -1), ('fwd', 1)):
            if 'eye-' + side not in g['pts']:
                continue
            wd = sgn * int(ex[ax_lat])
            edge = lo - 1 if wd < 0 else hi + 1
            done = None
            for za in R['z_above_deck']:
                z = dt + za
                for off in R['offset']:
                    c = [0, 0, z]
                    c[ax_lat] = edge + wd * off
                    tr = g['pts'].get('train', g['pts']['cascabel'])
                    s = int(np.floor(tr[ax_out])) - int(ey[ax_out]) * R['scan_back']
                    stop = int(round(r['outer'])) + int(ey[ax_out]) * R['scan_beyond_outer']
                    k = None
                    while (s - stop) * int(ey[ax_out]) <= 0:
                        c[ax_out] = s
                        if occ[c[0], c[1], c[2] - Z0]:
                            c[ax_out] = s - int(ey[ax_out])
                            k = tuple(c)
                            break
                        s += int(ey[ax_out])
                    dbg = os.environ.get('GF_DEBUG') == key + ':' + side
                    # 牆深從「船殼最外那一格」量：verify_guns 的 outer 在砲口朝 + 那一舷記的是外側面（最外那格 ＋1）、朝 − 那一舷記的是那一格
                    # 🩸 v1 直接拿 outer 減 ⇒ 兩舷差 1 格，S18／S17 船頭側的環量成 9 格深（上限 8）而 P 舷 8 格過了
                    oc = r['outer'] - (1 if ey[ax_out] > 0 else 0)
                    if k is None or abs(oc - k[ax_out]) > R['max_wall_depth'] or blocked(k, -1, set()) or k in cells:
                        if dbg:
                            print('  ', za, off, 'ring', k, 'wall' if k is None else ('deep' if abs(oc - k[ax_out]) > R['max_wall_depth'] else 'cell-blocked'))
                        continue
                    kc = np.array(k) + 0.5
                    h1 = rope_hits(g['pts']['cascabel'], kc, RP['breeching'], g['id'], {k})
                    h2 = rope_hits(g['pts']['eye-' + side], kc, RP['tackle'], g['id'], {k})
                    if h1 or h2:
                        if dbg:
                            print('  ', za, off, 'ring', k, 'breeching', h1[:3], [int(gid[c[0], c[1], c[2] - Z0]) for c in h1[:3]], 'tackle', h2[:3], [int(gid[c[0], c[1], c[2] - Z0]) for c in h2[:3]])
                        continue
                    done = (off, k, za)
                    break
                if done:
                    break
            if done is None:
                notes.append('%s 的 %s 環：offset／高度都不行 ⇒ 不放，那一側 breeching／tackle 不掛' % (key, side))
                continue
            off, k, za = done
            cells[(r['host_link'], k)] = R['color']
            tag = r['model']
            anchors.append({'deck': r['host_link'], 'name': 'ring-%s-%s' % (tag, side), 'kind': 'ring', 'world': list(k), 'gun': key, 'side': side})
            row['rings'][side] = {'offset': off, 'z_above_deck': za, 'cell': list(k)}
        if 'train' in g['pts']:
            tr = g['pts']['train']
            for back in DR['back']:
                b = np.floor(tr).astype(int) - ey * back
                zs = [zz for zz in range(dt - DR['surface_down'], dt + 1) if occ[b[0], b[1], zz - Z0] and not occ[b[0], b[1], zz + 1 - Z0]]
                if not zs:
                    continue
                k = (int(b[0]), int(b[1]), zs[-1] + 1)
                if blocked(k, -1, set()) or (r['host_link'], k) in cells:
                    continue
                if rope_hits(tr, np.array(k) + 0.5, RP['train'], g['id'], {k}):
                    continue
                cells[(r['host_link'], k)] = DR['color']
                anchors.append({'deck': r['host_link'], 'name': 'deck-%s' % r['model'], 'kind': 'deck_ring', 'world': list(k), 'gun': key})
                row['deck_ring'] = {'back': back, 'cell': list(k)}
                break
            if row['deck_ring'] is None:
                notes.append('%s 的甲板環找不到位置 ⇒ train tackle 不掛' % key)
        else:
            row['deck_ring'] = 'no-train'
        rows.append(row)

    ropes = []
    for row in rows:
        deck, model = row['gun'].split('/')
        fl = deck + '/' + F['link']
        gm = 'model:' + row['gun']
        for side in ('aft', 'fwd'):
            if side not in row['rings']:
                continue
            ring = '%s/ring-%s-%s' % (fl, model, side)
            ropes.append(dict({'name': '%s.%s.breeching-%s' % (deck, model, side), 'from': gm + '/cascabel', 'to': ring}, **RP['breeching'], group='guns/breeching'))
            ropes.append(dict({'name': '%s.%s.tackle-%s' % (deck, model, side), 'from': '%s/eye-%s' % (gm, side), 'to': ring}, **RP['tackle'], group='guns/tackle'))
        if isinstance(row['deck_ring'], dict):
            ropes.append(dict({'name': '%s.%s.train' % (deck, model), 'from': gm + '/train', 'to': '%s/deck-%s' % (fl, model)}, **RP['train'], group='guns/train'))

    out_works = []
    os.makedirs(os.path.join(D, 'masks', 'gunfittings'), exist_ok=True)
    for deck, work in sorted(F['works'].items()):
        ks = sorted(k for (d, k) in cells if d == deck)
        if not ks:
            continue
        Aa = np.array(ks)
        fa = Aa.min(0) - F['margin']
        fs = Aa.max(0) - fa + 1 + F['margin']
        tag = deck.split('-', 1)[1]
        txt = '# 三叉戟號砲具（%s）draft_gunfittings.py —— 子作品座標 x,y,z,color；世界 ＝ ＋frame_at %s\n' % (deck, ','.join(map(str, fa))) + \
              ''.join('%d,%d,%d,%d\n' % (k[0] - fa[0], k[1] - fa[1], k[2] - fa[2], cells[(deck, k)]) for k in ks)
        open(os.path.join(D, 'masks', 'gunfittings', tag + '.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
        for an in anchors:
            if an['deck'] == deck:
                an['at'] = [int(v) for v in np.array(an['world']) - fa]
                an['work'] = work
        out_works.append({'deck': deck, 'work': work, 'title': F['titles'][deck], 'frame_at': [int(v) for v in fa], 'frame_size': [int(v) for v in fs],
                          'host_work': 'gura-tridente-01m-deck-' + tag, 'link': F['link'], 'file': 'masks/gunfittings/%s.vox.txt' % tag, 'voxels': len(ks),
                          'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()})
    out = {'note': 'draft_gunfittings.py —— 現況 ＝ 組裝件 links=all 藏 砲具（z %d..%d：%d 格）＋ 模型外框 %d ＋ verify_guns.json 的 %d 門' % (Z0, Z1, len(A), nbox, len(guns)),
           'works': out_works, 'anchors': anchors, 'ropes': ropes, 'rows': rows, 'notes': notes,
           'counts': {'ring_cells': len(cells), 'anchors': len(anchors), 'ropes': len(ropes), 'guns': len(rows),
                      'no_train_guns': sum(1 for x in rows if x['deck_ring'] == 'no-train')}}
    with open(os.path.join(D, 'verify_gunfittings.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(out['counts'])
    for m in notes:
        print('⚠', m)


if __name__ == '__main__':
    main()
