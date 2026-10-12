"""
階段三十 新圖紙 23：entry port 與 side steps v1（從小艇上船的那一處）。設計在 plan.json `entry`。
讀圖：11 號（1927 MIT PLAN VIII）sheer plan —— 主桅 channel 前、gun deck 第 6／7 個砲門之間一排橫條（side steps）、
上面舷牆一個開口、兩側各一根柱子。逐列數亮像素（> 背景＋40）⇒ 橫條；逐欄數 ⇒ 柱子。換算同 read_spar_ports.py ⇒ source_entry.json。
產生（只讀「這一階段之前」：船殼、-belaying-side 讀標記 舷梯:begin；組裝件藏 舷梯、舷梯-鏡像 —— 套用之後重跑逐位元組一樣）：
  ① 船殼 carvevox（兩舷，帶顏色守門）：開口 x 範圍、z ≥ z_from、舷牆那幾格
  ② -entry-side（一舷，自己的座標）：踏階（每一欄從那一欄的船殼外面貼上去、外面齊平）＋兩根柱（立在 cap rail 外緣）
  ③ -belaying-side carvevox：pinrail-6 那一塊（6 連通元件，帶顏色守門）
  ④ 固定點 rig_points_entry.json（子作品自己的座標）、繩 entry_ropes.json（組裝件，S／P 各兩條）
驗：跟現況重疊、踏階每一欄貼著船殼、柱腳有東西、P 舷鏡過去也一樣、開口裡剩什麼、繩離實心多遠（直線取樣）。
用法：python -I draft_entry.py
"""
import hashlib, json, os, sys
from collections import Counter, deque
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402
from read_spar_ports import X_of, Z_of, IMG    # noqa: E402

HULL = 'basecamp-frigate-constitution-01m'
BELAY = 'basecamp-frigate-constitution-01m-belaying-side'
MARK = '舷梯:begin'
YC = 160


def read_drawing():
    """11 號：橫條（side steps）與兩根柱。回傳讀數（世界座標）。"""
    Image.MAX_IMAGE_PIXELS = None
    im = np.asarray(Image.open(IMG).convert('L'), dtype=float)
    bg = float(np.median(im[1680:1960, 2000:2400]))
    # 橫條：x 2140–2250、y 1690–1950（上面那條甲板線、下面水線不算）
    x0, x1, y0, y1 = 2140, 2250, 1690, 1950
    br = im[y0:y1, x0:x1] > bg + 40
    rows = br.sum(1)
    steps = []
    r = 0
    while r < len(rows):
        if rows[r] >= 15:
            s = r
            while r < len(rows) and rows[r] >= 15:
                r += 1
            colany = br[s:r].any(0)
            # 最長的連續一段（排水孔的圓點會黏在旁邊）
            best, c = (0, 0, 0), 0
            while c < len(colany):
                if colany[c]:
                    a = c
                    while c < len(colany) and colany[c]:
                        c += 1
                    if c - a > best[0]:
                        best = (c - a, a, c - 1)
                c += 1
            yc = y0 + (s + r - 1) / 2.0
            L, R = x0 + best[1], x0 + best[2]
            steps.append({'px': {'y': yc, 'L': L, 'R': R, 'h': r - s},
                          'X_aft': round(X_of(L, yc), 2), 'X_fwd': round(X_of(R + 1, yc), 2), 'Z': round(Z_of((L + R) / 2, yc), 2)})
        r += 1
    # 柱：x 2150–2260、y 1520–1690 逐欄數
    bx0, bx1, by0, by1 = 2150, 2260, 1520, 1690
    b2 = im[by0:by1, bx0:bx1] > bg + 40
    cc = b2.sum(0)
    posts = []
    c = 0
    while c < len(cc):
        if cc[c] > 60:
            a = c
            while c < len(cc) and cc[c] > 60:
                c += 1
            L, R = bx0 + a, bx0 + c - 1
            xm = int(round((L + R) / 2))
            col = im[:, xm - 1:xm + 2].max(1)
            t = by0 + int(np.argmax(b2[:, xm - bx0]))
            while col[t - 1] > bg + 40:
                t -= 1
            bt = by1 - 1
            while col[bt] <= bg + 40:
                bt -= 1
            ym = (t + bt) / 2
            posts.append({'px': {'L': L, 'R': R, 'T': t, 'B': bt}, 'X_aft': round(X_of(L, ym), 2), 'X_fwd': round(X_of(R + 1, ym), 2),
                          'X_center': round(X_of((L + R + 1) / 2, ym), 2), 'Z_top': round(Z_of(xm, t), 2), 'Z_bottom': round(Z_of(xm, bt), 2)})
        c += 1
    zs = [s_['Z'] for s_ in steps]
    return {'note': '11 號 sheer plan 上的 side steps 與 entry port 柱（draft_entry.py 讀；換算同 read_spar_ports.py）',
            'source_image': 'references/uss-constitution-1927/RG19_ALPHA_Constitution_1797_11.JPG',
            'background': bg, 'steps': steps, 'posts': posts,
            'step_count': len(steps), 'step_spacing_mean': round((zs[0] - zs[-1]) / (len(zs) - 1), 3) if len(zs) > 1 else None,
            'opening_between_posts': [posts[0]['X_fwd'], posts[1]['X_aft']] if len(posts) == 2 else None}


def as_dict(a):
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def comp_containing(cells, seed_pts):
    """cells: dict；回傳含 seed（任一點 ≤ 1 格）的 6 連通元件。"""
    seeds = [k for k in cells if any(max(abs(k[i] - p[i]) for i in range(3)) <= 1 for p in seed_pts)]
    seen, q = set(seeds), deque(seeds)
    while q:
        p = q.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
            if n in cells and n not in seen:
                seen.add(n)
                q.append(n)
    return seen


def seg_clearance(p, q, solid, radius, n=600, skip=1.0):
    """直線 p→q 取樣，每點到最近實心格（方塊）的距離 − 半徑；回傳最小值與那一點、那一格。
    兩端 skip 格以內不算（繩端本來就綁在柱頂／踏階上）。"""
    p, q = np.array(p, float), np.array(q, float)
    best = (1e9, None, None)
    Ln = np.linalg.norm(q - p)
    for t in np.linspace(0, 1, n):
        if t * Ln < skip or (1 - t) * Ln < skip:
            continue
        x = p + (q - p) * t
        b = np.floor(x).astype(int)
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                for dz in (-2, -1, 0, 1, 2):
                    k = (b[0] + dx, b[1] + dy, b[2] + dz)
                    if k in solid:
                        lo = np.array(k, float)
                        d = np.linalg.norm(np.maximum(np.maximum(lo - x, 0), x - (lo + 1)))
                        if d - radius < best[0]:
                            best = (d - radius, [round(float(v), 2) for v in x], [int(v) for v in k])
    return best


class Entry:
    def __init__(s):
        s.plan = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['entry']
        s.hull = export_list(HULL, draft=False, mark=MARK)
        s.belay = export_list(BELAY, draft=False, mark=MARK)
        s.asm = export_list(ASSEMBLY, draft=False, hide_links='舷梯,舷梯-鏡像')
        s.files = {}

    def region(s, a, x0, x1, z0=0, z1=999):
        m = a[(a[:, 0] >= x0) & (a[:, 0] <= x1) & (a[:, 2] >= z0) & (a[:, 2] <= z1)]
        return as_dict(m)

    def build(s):
        P = s.P
        xa, xb = P['opening']['x']
        sx0, sx1 = P['steps']['x']
        H = s.region(s.hull, xa - 12, xb + 12)
        s.H = H
        # ① 開口：兩舷，z ≥ z_from、舷牆那幾格（S：y ≥ y_min_S；P：y ≤ 320 − y_min_S）
        ymin = P['opening']['y_min_S']
        s.carve_S = sorted((k, c) for k, c in H.items() if xa <= k[0] <= xb and k[2] >= P['opening']['z_from'] and k[1] >= ymin)
        s.carve_P = sorted((k, c) for k, c in H.items() if xa <= k[0] <= xb and k[2] >= P['opening']['z_from'] and k[1] <= 320 - ymin)
        # ② 踏階（世界座標，S 舷）
        s.steps = {}
        s.step_rows = []
        for z in P['steps']['z']:
            yout = {}
            for x in range(sx0, sx1 + 1):
                ys = [k[1] for k in H if k[0] == x and k[2] == z and k[1] > YC]
                yout[x] = max(ys)
            face = max(yout.values()) + P['steps']['depth']
            for x in range(sx0, sx1 + 1):
                for y in range(yout[x] + 1, face + 1):
                    s.steps[(x, y, z)] = P['steps']['color']
            s.step_rows.append({'z': z, 'hull_y_out': [min(yout.values()), max(yout.values())], 'face_y': face,
                                'hull_colors': dict(Counter(H[(x, yout[x], z)] for x in yout))})
        # 柱：立在 cap rail 外緣（y）那一格最上面的實心上
        s.posts = {}
        s.post_rows = []
        y = P['posts']['y']
        for x in P['posts']['x']:
            zs = [k[2] for k in H if k[0] == x and k[1] == y]
            base = max(zs)
            for z in range(base + 1, P['posts']['z_top'] + 1):
                s.posts[(x, y, z)] = P['posts']['color']
            s.post_rows.append({'x': x, 'y': y, 'base_z': base, 'base_color': H[(x, y, base)], 'z': [base + 1, P['posts']['z_top']]})
        s.side_world = dict(s.steps)
        s.side_world.update(s.posts)
        # ③ pinrail-6（-belaying-side 自己的座標）—— 種子讀設計檔 spar_ports_anchors.json（階段二十九登記的那份），
        #    ⛔ 不讀作品現在的 anchors.json：套用時那 5 個已經 unanchor，重跑會找不到（2026-10-12 量到）
        sa = json.load(open(os.path.join(HERE, 'spar_ports_anchors.json'), encoding='utf-8'))['anchors']
        mine = [a for a in sa if a['name'].startswith(P['remove']['pinrail'] + '.')]
        s.pr_anchors = sorted(a['name'] for a in mine)
        seeds = [tuple(a['at']) for a in mine]
        assert seeds, '設計檔裡沒有 %s 的固定點' % P['remove']['pinrail']
        B = as_dict(s.belay)
        comp = comp_containing(B, seeds)
        s.pr_cells = sorted((k, B[k]) for k in comp)
        # belaying-side 的 at（從固定點 world − at 反推；spar_ports_anchors.json 兩欄都有）
        offs = {tuple(np.array(a['world']) - np.array(a['at'])) for a in sa if a['name'].startswith('pinrail-')}
        assert len(offs) == 1, offs
        s.belay_at = list(map(int, offs.pop()))
        # ④ 固定點：引擎只收整數格（點取格心）且要在子作品框裡 ⇒ 先定格、點 ＝ 格＋0.5
        #    柱頂：柱外面那一格（繩端離柱面 0.5）；下端：踏階兩端外側那一欄、格心離踏階外面 bottom_off
        at = P['subwork']['at']
        zb = P['steps']['z'][0]
        face_b = [r for r in s.step_rows if r['z'] == zb][0]['face_y']
        pa, pf = P['posts']['x']
        zt = P['posts']['z_top']
        yb = int(round(face_b + 1 + P['manropes']['bottom_off'] - 0.5))
        s.anchor_cell = {
            'post-aft.top': (pa, y + 1, zt),
            'post-fwd.top': (pf, y + 1, zt),
            'step-1.aft': (sx0 - 1, yb, zb),
            'step-1.fwd': (sx1 + 1, yb, zb),
        }
        s.anchor_world = {k: [c[0] + 0.5, c[1] + 0.5, c[2] + 0.5] for k, c in s.anchor_cell.items()}
        s.anchor_local = {k: [c[0] - at[0], c[1] - at[1], c[2] - at[2]] for k, c in s.anchor_cell.items()}
        s.local = {(k[0] - at[0], k[1] - at[1], k[2] - at[2]): c for k, c in s.side_world.items()}
        W, L, Hh = P['subwork']['size']
        bad = [k for k in list(s.local) + [tuple(v) for v in s.anchor_local.values()] if not (0 <= k[0] < W and 0 <= k[1] < L and 0 <= k[2] < Hh)]
        assert not bad, ('出框', bad[:5])
        assert not [c for c in s.anchor_cell.values() if c in s.side_world], '固定點落在實心格上'
        R = P['manropes']
        s.ropes = []
        for side, link in (('S', '舷梯'), ('P', '舷梯-鏡像')):
            for end in ('aft', 'fwd'):
                s.ropes.append({'name': 'entry-%s.manrope-%s' % (side, end), 'from': '%s/post-%s.top' % (link, end), 'to': '%s/step-1.%s' % (link, end),
                                'thickness': R['thickness'], 'slack': R['slack'], 'color': R['color'], 'group': R['group']})

    def mirror_y(s, k):
        return (k[0], 320 - k[1], k[2])

    def verify(s):
        A = as_dict(s.asm)
        Aset = set(A)
        carve = {k for k, _ in s.carve_S} | {k for k, _ in s.carve_P}
        pr_world = {(k[0] + s.belay_at[0], k[1] + s.belay_at[1], k[2] + s.belay_at[2]) for k, _ in s.pr_cells}
        pr_world_P = {s.mirror_y(k) for k in pr_world}
        side_S = set(s.side_world)
        side_P = {s.mirror_y(k) for k in side_S}
        after = (Aset - carve - pr_world - pr_world_P) | side_S | side_P
        v = {'title': s.P['title'], 'base_assembly_voxels': len(Aset)}
        v['hull_carve'] = {'S': len(s.carve_S), 'P': len(s.carve_P), 'by_color_S': dict(Counter(c for _, c in s.carve_S)),
                           'P_equals_mirror_S': sorted((s.mirror_y(k), c) for k, c in s.carve_S) == sorted(s.carve_P),
                           'not_in_assembly': len(carve - Aset)}
        v['pinrail'] = {'name': s.P['remove']['pinrail'], 'cells': len(s.pr_cells), 'by_color': dict(Counter(c for _, c in s.pr_cells)),
                        'world_box': [list(map(int, np.min(list(pr_world), 0))), list(map(int, np.max(list(pr_world), 0)))],
                        'belay_at': s.belay_at, 'anchors_to_unanchor': s.pr_anchors,
                        'in_assembly_S': len(pr_world & Aset), 'in_assembly_P': len(pr_world_P & Aset)}
        # 誰綁在 pinrail-6 上（組裝件的繩與帆）＋正向對照
        asm_dir = os.path.join(HERE, '..', '..', ASSEMBLY)
        txt = open(os.path.join(asm_dir, 'ropes.json'), encoding='utf-8').read() + open(os.path.join(asm_dir, 'sails.json'), encoding='utf-8').read()
        v['pinrail']['users'] = txt.count(s.P['remove']['pinrail'] + '.')
        v['pinrail']['control_pinrail_refs'] = txt.count('pinrail-')
        v['side'] = {'cells_one_side': len(side_S), 'steps': len(s.steps), 'posts': len(s.posts),
                     'overlap_S': len(side_S & (Aset - carve)), 'overlap_P': len(side_P & (Aset - carve)),
                     'step_rows': s.step_rows, 'post_rows': s.post_rows}
        # 踏階每一欄貼著船殼（S：y − 1 是船殼；P 鏡過去：y + 1 是船殼）
        loose_S = loose_P = 0
        for (x, y, z) in s.steps:
            if (x, y - 1, z) not in s.steps and (x, y - 1, z) not in A:
                loose_S += 1
            xp, yp, zp = s.mirror_y((x, y, z))
            if (xp, yp + 1, zp) not in side_P and (xp, yp + 1, zp) not in A:
                loose_P += 1
        v['side']['steps_not_touching_S'] = loose_S
        v['side']['steps_not_touching_P'] = loose_P
        v['side']['post_base_P'] = [A.get(s.mirror_y((r['x'], r['y'], r['base_z']))) for r in s.post_rows]
        # 開口裡剩什麼（兩舷）：x 範圍 × z_from..舷頂 × 舷牆內面往裡 4 格 → 外面 1 格
        xa, xb = s.P['opening']['x']
        rem = {}
        for nm, side_ in (('S', 1), ('P', -1)):
            ys = [k[1] for k, _ in (s.carve_S if side_ == 1 else s.carve_P)]
            lo, hi = (min(ys) - 4, max(ys) + 1) if side_ == 1 else (min(ys) - 1, max(ys) + 4)
            ztop = max(k[2] for k, _ in s.carve_S)
            left = Counter()
            for x in range(xa, xb + 1):
                for y in range(lo, hi + 1):
                    for z in range(s.P['opening']['z_from'], ztop + 1):
                        if (x, y, z) in after:
                            left[(z, A.get((x, y, z), -1))] += 1
            rem[nm] = {'%d:%d' % k: n for k, n in sorted(left.items())}
        v['opening_left'] = rem
        # 繩：直線取樣離實心多遠（after，含 P）
        solid = after
        cl = []
        for r in s.ropes:
            link, a_ = r['from'].split('/')
            _, b_ = r['to'].split('/')
            pa_, pb_ = s.anchor_world[a_], s.anchor_world[b_]
            if link.endswith('鏡像'):
                pa_ = [pa_[0], 321 - pa_[1], pa_[2]]
                pb_ = [pb_[0], 321 - pb_[1], pb_[2]]
            m, pt, cell = seg_clearance(pa_, pb_, solid, r['thickness'] / 2)
            cl.append({'name': r['name'], 'from': pa_, 'to': pb_, 'length': round(float(np.linalg.norm(np.subtract(pb_, pa_))), 2),
                       'min_clear': round(float(m), 3), 'at': pt, 'nearest_cell': cell, 'nearest_color': A.get(tuple(cell)) if cell else None})
        v['ropes'] = cl
        v['anchors_world'] = s.anchor_world
        v['anchors_local'] = s.anchor_local
        v['expect_assembly_after'] = len(Aset) - len(carve & Aset) - len((pr_world | pr_world_P) & Aset) + len(side_S - Aset) + len(side_P - Aset)
        s.after = after
        s.v = v
        return v

    def write(s):
        d = os.path.join(HERE, 'masks', 'entry')
        os.makedirs(d, exist_ok=True)

        def put(fn, rows, head):
            p = os.path.join(d, fn)
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write('# ' + head + '\n')
                for (x, y, z), c in rows:
                    f.write('%d,%d,%d,%d\n' % (x, y, z, c))
            s.files[fn] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        put('hull_carve.vox.txt', s.carve_S + s.carve_P, '船殼 carvevox（世界座標，帶顏色守門）：entry port 開口兩舷')
        put('side.vox.txt', sorted(s.local.items()), '-entry-side stampvox（子作品自己的座標）：side steps＋entering stanchions（一舷）')
        put('pinrail6_carve.vox.txt', s.pr_cells, '-belaying-side carvevox（子作品自己的座標，帶顏色守門）：pinrail-6 整根')
        json.dump({'note': '-entry-side 的固定點（子作品自己的座標；組裝件裡 舷梯/…、舷梯-鏡像/… 用）', 'anchors': [{'name': k, 'at': v_, 'world_S': s.anchor_world[k]} for k, v_ in s.anchor_local.items()]},
                  open(os.path.join(HERE, 'rig_points_entry.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        json.dump({'note': 'entry port 的 man ropes（組裝件；tools/ropes_apply.py 下 CLI）', 'ropes': s.ropes},
                  open(os.path.join(HERE, 'entry_ropes.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


def render_sheet(E, src, path):
    f12, f18 = DD._font(13), DD._font(20)
    xa, xb, za, zb = 340, 420, 56, 134
    sc = 7
    after = E.after
    A = as_dict(E.asm)
    new = set(E.side_world)
    col = {}
    col.update({k: c for k, c in A.items()})
    col.update(E.side_world)
    # 從右舷看（x–z）：每一格取最外面（y 最大、y > 160）的
    img = np.zeros((zb - za, xb - xa, 3), np.uint8)
    img[:] = DD.PAPER
    best = {}
    for k in after:
        x, y, z = k
        if xa <= x < xb and za <= z < zb and y > YC:
            if (x, z) not in best or y > best[(x, z)][0]:
                best[(x, z)] = (y, col[k])
    for (x, z), (y, c) in best.items():
        rgb = np.array(DP.rgb332(c), float)
        img[zb - 1 - z, x - xa] = rgb.astype(np.uint8)
    side = Image.fromarray(img).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)
    dr_s = ImageDraw.Draw(side)
    # 繩（S 舷，投影到 x–z）
    for r in E.v['ropes'][:2]:
        p, q = r['from'], r['to']
        dr_s.line([((p[0] - xa) * sc, (zb - p[2]) * sc), ((q[0] - xa) * sc, (zb - q[2]) * sc)], fill=(205, 184, 142), width=3)
    # 剖面（y–z，x 378，從船尾往船頭看）：改之前淡色、之後原色
    ya, yb = 196, 232
    xs = 378
    sec = np.zeros((zb - za, yb - ya, 3), np.uint8)
    sec[:] = DD.PAPER
    for z in range(za, zb):
        for y in range(ya, yb):
            k = (xs, y, z)
            if k in after:
                sec[zb - 1 - z, y - ya] = DP.rgb332(col[k])
            elif k in A:
                sec[zb - 1 - z, y - ya] = (np.array(DP.rgb332(A[k])) * 0.35 + np.array(DD.PAPER) * 0.65).astype(np.uint8)
    secim = Image.fromarray(sec).resize(((yb - ya) * sc, (zb - za) * sc), Image.NEAREST)
    # 原圖那一塊
    Image.MAX_IMAGE_PIXELS = None
    crop = Image.open(IMG).crop((1990, 1480, 2440, 1990)).convert('RGB')
    crop = crop.resize((int(crop.size[0] * (zb - za) * sc / crop.size[1]), (zb - za) * sc))
    PADL = 30
    can = Image.new('RGB', (PADL + side.size[0] + secim.size[0] + crop.size[0] + 100, 80 + side.size[1] + 150), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), E.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 42), '左：從右舷看 x %d–%d、z %d–%d（每格 %d px；繩只畫投影）　中：x %d 的剖面（從船尾往船頭看；淡色 ＝ 改之前、會被刻掉的）　右：11 號原圖同一段' % (xa, xb, za, zb, sc, xs), font=f12, fill=DD.INK)
    x = PADL
    for im_ in (side, secim, crop):
        can.paste(im_, (x, 66))
        x += im_.size[0] + 30
    y = 66 + side.size[1] + 14
    v = E.v
    lines = [
        '開口：船殼刻 S %d／P %d 格（P ＝ S 鏡過去：%s）；%s 拿掉 %d 格（world %s–%s；綁在上面的繩／帆 %d、正向對照 pinrail- 參照 %d）' % (
            v['hull_carve']['S'], v['hull_carve']['P'], v['hull_carve']['P_equals_mirror_S'], v['pinrail']['name'], v['pinrail']['cells'],
            v['pinrail']['world_box'][0], v['pinrail']['world_box'][1], v['pinrail']['users'], v['pinrail']['control_pinrail_refs']),
        '-entry-side 一舷 %d 格（踏階 %d、柱 %d）；跟現況重疊 S %d／P %d；踏階沒貼著船殼 S %d／P %d；組裝件預期 %d' % (
            v['side']['cells_one_side'], v['side']['steps'], v['side']['posts'], v['side']['overlap_S'], v['side']['overlap_P'],
            v['side']['steps_not_touching_S'], v['side']['steps_not_touching_P'], v['expect_assembly_after']),
        '繩（直線，半徑 0.175）離實心最近：' + '、'.join('%s %.2f' % (r['name'], r['min_clear']) for r in v['ropes']),
        '讀圖：橫條 %d 道、間距 %.2f；柱之間 X %s' % (src['step_count'], src['step_spacing_mean'], src['opening_between_posts']),
    ]
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, can.size[0], y + 12))
    can.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    src = read_drawing()
    json.dump(src, open(os.path.join(HERE, 'source_entry.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    E = Entry()
    E.build()
    v = E.verify()
    E.write()
    v['files'] = E.files
    v['source'] = {'step_count': src['step_count'], 'step_spacing_mean': src['step_spacing_mean'], 'posts': src['posts'],
                   'steps_Z': [s_['Z'] for s_ in src['steps']]}
    json.dump(v, open(os.path.join(HERE, 'verify_entry.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(E, src, os.path.join(HERE, 'sheet23_entry_v1.png'))
    out = {k: v[k] for k in ('hull_carve', 'pinrail', 'expect_assembly_after', 'opening_left', 'files')}
    out['side'] = {k: v['side'][k] for k in v['side'] if k not in ('step_rows',)}
    out['ropes'] = [(r['name'], r['min_clear'], r['at'], r['nearest_cell'], r['nearest_color']) for r in v['ropes']]
    print(json.dumps(out, ensure_ascii=False))
    print(json.dumps(v['source'], ensure_ascii=False))


if __name__ == '__main__':
    main()
