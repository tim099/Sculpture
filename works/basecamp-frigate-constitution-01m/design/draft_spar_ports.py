"""
階段二十九（TASK-0478）：spar deck 砲門 —— source_ports_spar.json（11 號讀數，read_spar_ports.py）＋ 作品現況
  A. 船殼：開口裡的舷牆格全刻（cap rail 104 不刻）；開口外一圈、舷牆厚度內的空格補 141（port timber，牆不能有洞）。兩舷各自量（船殼兩舷差 1 格）。
     下緣 ＝ max(圖上的下緣, SILL_MIN)：z 109–110 舷外有一條黑木（channels 那件子作品），有幾個砲門連牆厚範圍裡都有 ⇒ 開口從 111 起。
  B. pin rails v2（舷牆那件子作品 -belaying-side，一舷，另一舷是鏡像關聯）：原本照 gun deck 砲門的空檔排、第 2、3、11、13 根壓在 spar deck 砲門上
     ⇒ 改照 spar deck 砲門的空檔（waist 沒有 spar deck 砲門 ⇒ 照舊用 gun deck 第 6–11 個當分隔；船頭用 gun deck 第 15 個收尾）。
     13 根照舊編號：每根搬到離原位最近、還沒用過的空檔（照順序）⇒ 固定點名字不變，綁在上面的繩跟著走。cleats 照原規則重找空檔（cleat-4 改瞄 570）。
輸出：masks/spar_ports/{hull_carve,hull_lining,side_carve,side_add}.vox.txt、spar_ports_anchors.json、verify_spar_ports.json
用法：python -I draft_spar_ports.py <組裝件清單.txt>（現況、沒草稿）<船殼清單.txt> <舷牆那件的清單.txt（自己的座標）>
"""
import hashlib, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draft_belaying as DB        # noqa: E402

YC = 160
SILL_MIN = 111
LINING = 141
WALL_COLORS = {36, 141, 177, 168, 255}


def load(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def rows_of(a, b):
    return list(range(int(np.ceil(a - 0.5)), int(np.floor(b - 0.5)) + 1))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    A, H, S = load(sys.argv[1]), load(sys.argv[2]), load(sys.argv[3])
    hull = {(int(x), int(y), int(z)): int(c) for x, y, z, c in H}
    ports = json.load(open(os.path.join(HERE, 'source_ports_spar.json'), encoding='utf-8'))['ports']

    # ── A. 船殼 ──
    carve, lining, per = {}, {}, []
    for p in ports:
        xs = rows_of(p['X_aft'], p['X_fwd'])
        zs = [z for z in rows_of(p['sill'], p['lintel']) if z >= SILL_MIN]
        row = {'n': p['n'], 'x': [xs[0], xs[-1]], 'z': [zs[0], zs[-1]], 'drawing_z': [round(p['sill'], 2), round(p['lintel'], 2)]}
        for side, nm in ((1, 'S'), (-1, 'P')):
            n0 = len(carve)
            span = {}
            for x in range(xs[0] - 1, xs[-1] + 2):
                for z in range(zs[0] - 1, zs[-1] + 2):
                    ys = [y for y in range(320) if (x, y, z) in hull and (y - YC) * side > 20]
                    if ys:
                        span[(x, z)] = (min(ys), max(ys))
            for x in xs:
                for z in zs:
                    for y in range(*((span[(x, z)][0], span[(x, z)][1] + 1) if (x, z) in span else (0, 0))):
                        c = hull[(x, y, z)] if (x, y, z) in hull else None
                        if c is None:
                            continue
                        if c == 104:
                            raise SystemExit('砲門 %d %s：開口裡有 cap rail（%d,%d,%d）—— 上緣太高' % (p['n'], nm, x, y, z))
                        if c not in WALL_COLORS:
                            raise SystemExit('砲門 %d %s：開口裡有不是舷牆的顏色 %d（%d,%d,%d）' % (p['n'], nm, c, x, y, z))
                        carve[(x, y, z)] = c
            # 開口外一圈：牆的厚度（取相鄰那一欄的範圍）內的空格補 141
            ring = [(x, z) for x in (xs[0] - 1, xs[-1] + 1) for z in zs] + [(x, z) for z in (zs[0] - 1, zs[-1] + 1) for x in xs]
            nl = 0
            for (x, z) in ring:
                if (x, z) not in span:
                    continue
                y0, y1 = span[(x, z)]
                for y in range(y0, y1 + 1):
                    if (x, y, z) not in hull and (x, y, z) not in lining:
                        lining[(x, y, z)] = LINING
                        nl += 1
            row[nm] = {'carve': len(carve) - n0, 'lining': nl,
                       'wall_y_mid': list(span.get(((xs[0] + xs[-1]) // 2, (zs[0] + zs[-1]) // 2), (None, None)))}
        per.append(row)
        print(json.dumps(row, ensure_ascii=False))

    # ── B. pin rails v2 ──
    plan = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
    gun_ports = plan['guns']['ports']
    old_rails = json.load(open(os.path.join(HERE, 'verify_belaying.json'), encoding='utf-8'))['rails']

    class Side(DB.Belaying):
        def __init__(s):
            s.design = HERE
            s.plan = plan
            s.P = plan['belaying']
            # 現況：組裝件 − 舷牆那件兩條關聯（它自己要重排）；船殼照「刻完砲門」那個樣子（量內面用）
            box = s.P['subworks']['side']['box']
            x0, y0, z0 = box['at']
            G = np.zeros((DB.XB - DB.XA, 320, DB.ZB - DB.ZA), np.uint8)
            for x, y, z, c in A:
                if DB.XA <= x < DB.XB and DB.ZA <= z < DB.ZB:
                    G[x - DB.XA, y, z - DB.ZA] = c
            # 拿掉舷牆那件（兩舷）：S 用自己的座標＋at；P 是 mirror=y、at.y 80 ⇒ y_P ＝ 80 + (80 − 1 − y_local)
            for x, y, z, c in S:
                wx, wz = int(x) + x0, int(z) + z0
                if DB.XA <= wx < DB.XB and DB.ZA <= wz < DB.ZB:
                    G[wx - DB.XA, int(y) + y0, wz - DB.ZA] = 0
                    G[wx - DB.XA, 80 + (80 - 1 - int(y)), wz - DB.ZA] = 0
            for (x, y, z) in carve:
                if DB.XA <= x < DB.XB and DB.ZA <= z < DB.ZB:
                    G[x - DB.XA, y, z - DB.ZA] = 0
            for (x, y, z), c in lining.items():
                if DB.XA <= x < DB.XB and DB.ZA <= z < DB.ZB:
                    G[x - DB.XA, y, z - DB.ZA] = c
            s.G = G
            s.fife, s.side, s.kind, s.hit, s.anchors = {}, {}, {}, {}, []

        def gaps(s):
            lo, hi = s.P['pinrails']['x_range']
            obst = [tuple(r['x']) for r in per]
            obst += [tuple(g['x']) for g in gun_ports if g['x'][1] > 361 and g['x'][0] < 521]
            obst += [tuple(g['x']) for g in gun_ports if g['n'] == 15]
            s.portx = {x for a, b in obst for x in range(a, b + 1)}
            s.port_runs = sorted([list(o) for o in obst])
            out, run = [], []
            for x in range(lo, hi + 1):
                if x in s.portx:
                    if run:
                        out.append(run)
                    run = []
                else:
                    run.append(x)
            if run:
                out.append(run)
            gl = [(r[0], r[-1]) for r in out if r[0] - 1 in s.portx and r[-1] + 1 in s.portx]
            R = s.P['pinrails']
            gl = [g for g in gl if min(R['max_len'], g[1] - g[0] + 1 - 2 * R['clear_ends']) >= R['min_len']]
            # 13 根照順序各配一個空檔（不共用），總位移最小（DP）
            cen = [(a + b) / 2 for a, b in gl]
            oc = [(r['x'][0] + r['x'][1]) / 2 for r in old_rails]
            n, m = len(oc), len(cen)
            INF = float('inf')
            D = [[INF] * (m + 1) for _ in range(n + 1)]
            D[0] = [0.0] * (m + 1)
            for i in range(1, n + 1):
                for j in range(1, m + 1):
                    D[i][j] = min(D[i][j - 1], D[i - 1][j - 1] + abs(oc[i - 1] - cen[j - 1]))
            pick, i, j = [], n, m
            while i > 0:
                if D[i][j] == D[i][j - 1]:
                    j -= 1
                else:
                    pick.append(j - 1)
                    i -= 1
                    j -= 1
            pick.reverse()
            s.all_gaps = gl
            return [gl[k] for k in pick]

    C = Side()
    # cleat-4 原本瞄 x 600（現在是第 12 個砲門）⇒ 會被排到砲門前面 x 620–631，那裡船頭的牆往內彎、角撞進內板 7 格 ⇒ 改瞄 570（直的那段；cleat 沒有繩綁）
    C.P = dict(C.P)
    C.P['cleats'] = dict(C.P['cleats'], x_targets=[205, 330, 480, 570])
    C.build_side()
    if C.hit:
        raise SystemExit('舷牆那件想放的格已經是實心：%s' % C.hit)
    box = plan['belaying']['subworks']['side']['box']
    x0, y0, z0 = box['at']
    old = {(int(x), int(y), int(z)): int(c) for x, y, z, c in S}
    new = {(x - x0, y - y0, z - z0): c for (x, y, z), c in C.side.items()}
    side_carve = {k: v for k, v in old.items() if new.get(k) != v}
    side_add = {k: v for k, v in new.items() if old.get(k) != v}

    out = os.path.join(HERE, 'masks', 'spar_ports')
    os.makedirs(out, exist_ok=True)
    files = {}

    def write(name, cells, head):
        p = os.path.join(out, name)
        rows = sorted((x, y, z, c) for (x, y, z), c in cells.items())
        open(p, 'w', encoding='utf-8', newline='\n').write('# ' + head + '（%d 格）\n' % len(rows) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        files[name] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}

    write('hull_carve.vox.txt', carve, 'spar deck 砲門 —— 船殼要刻的格（行尾 ＝ 現在的顏色 ⇒ carvevox 守門；世界座標 at 0,0,0）')
    write('hull_lining.vox.txt', lining, 'spar deck 砲門 —— 開口外一圈補 141（stampvox at 0,0,0）')
    write('side_carve.vox.txt', side_carve, '舷牆 pin rails／cleats v1 要拿掉的格（-belaying-side 自己的座標；行尾 ＝ 現在的顏色）')
    write('side_add.vox.txt', side_add, '舷牆 pin rails／cleats v2 要放的格（-belaying-side 自己的座標）')
    anchors = [{'name': a['name'], 'at': [a['world'][0] - x0, a['world'][1] - y0, a['world'][2] - z0], 'world': a['world']} for a in C.anchors]
    old_names = [f'pinrail-{r["k"]}.pin-{j}' for r in old_rails for j in range(1, r['pins'] + 1)] + ['cleat-%d' % k for k in range(1, 5)]
    gone = sorted(set(old_names) - {a['name'] for a in anchors})
    json.dump({'note': 'v2 的固定點（-belaying-side 自己的座標）；gone ＝ v1 有、v2 沒有（要 unanchor）', 'anchors': anchors, 'gone': gone},
              open(os.path.join(HERE, 'spar_ports_anchors.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    v = {'ports': per, 'sill_min': SILL_MIN, 'hull_carve': len(carve), 'hull_lining': len(lining),
         'rails_v1': [{'k': r['k'], 'x': r['x']} for r in old_rails], 'rails_v2': C.rails, 'cleats_v2': C.cleat_list,
         'gaps': C.all_gaps, 'side_carve': len(side_carve), 'side_add': len(side_add), 'anchors_gone': gone, 'files': files}
    json.dump(v, open(os.path.join(HERE, 'verify_spar_ports.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in ('hull_carve', 'hull_lining', 'side_carve', 'side_add', 'anchors_gone', 'gaps')}, ensure_ascii=False))
    for r in C.rails:
        o = next(x for x in old_rails if x['k'] == r['k'])
        print('rail', r['k'], o['x'], '→', r['x'], 'pins', r['pins'], 'z', r['z'])
    print('cleats', [(c['k'], c['x'], c['z']) for c in C.cleat_list])


if __name__ == '__main__':
    main()
