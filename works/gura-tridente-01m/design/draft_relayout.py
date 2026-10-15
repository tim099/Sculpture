# 三叉戟號 三叉戟砲重配（TASK-0588）—— 從「撤完」的現況算新擺法（tools/apply_relayout.py remove 之後）
#   Tim 2026-10-15：船頭斜放的三叉戟砲跟舷側砲互相佔站位、站不滿 ⇒「船頭抬高砲台 2 門朝前、船尾中砲甲板 2 門取代 18 磅追擊砲、上砲甲板船長室 2 門、封船頭斜砲門」
#   ① 船尾：中砲甲板原本的追擊砲門（第 2、6 扇）、上砲甲板那一列第 2、6 扇窗 ⇒ 刻成寬 w 的砲門（只刻船殼的船尾牆）；
#      砲朝正後方（rotate 90）：從牆外往裡退到零碰撞，砲口伸出牆外 ≥ min_muzzle_out；三根管往後 fire_clear 格內碰到的陽台欄杆 ⇒ 在欄杆上開口（stern-walk 子作品）
#   ② 船頭砲台：上甲板最前段架高一層（底 under、面 top）——範圍 ＝ 舷牆、船頭牆圍住的艙裡（probe_z 那一層量），中線讓艏斜桅穿過；
#      兩門三叉戟砲在艏斜桅兩側朝正前方（rotate −90），往前推到輪子全踩在砲台上、零碰撞；砲台後緣一道矮欄（梯口留開）；底下支柱；兩舷各一座梯子從上甲板爬上來
#   ③ 站位預估：照遊戲 40_crew.js（spots、standNear、blocked）在新的格子上算每門站得到幾個（真正的讀數去遊戲量）
#   輸出：masks/relayout/*.vox.txt、verify_relayout.json。用法：python -I -X utf8 draft_relayout.py <design>
import sys, os, json, math, hashlib, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import deco_base as DB

NX, NY, NZ = 1100, 400, 260
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace(os.sep, '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    v = np.atleast_2d(v)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def write_list(path, head, cells):
    t = head + ''.join('%d,%d,%d,%d\n' % (p + (c,)) for p, c in sorted(cells.items()))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)
    return {'file': os.path.relpath(path, DSN).replace(os.sep, '/'), 'cells': len(cells), 'sha256': hashlib.sha256(t.encode('utf-8')).hexdigest()}


def main():
    global DSN
    sys.stdout.reconfigure(encoding='utf-8')
    D = DSN = os.path.abspath(sys.argv[1])
    WORKS = os.path.dirname(os.path.dirname(D))
    plan = HL.load_plan(D)
    R = plan['relayout']
    SR = R['search']
    YC = plan['space']['yc']
    VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
    keep = [r for r in VG['rows'] if r['type'] != 'trident' and not r['model'].startswith('追擊砲-船尾-')]
    # 重跑也讀「這一階段之前」：組裝件藏本階段的關聯（甲板-battery）；船殼、陽台讀標記 三叉戟船尾砲門:begin 那一刻（還沒標 ⇒ 現在；第一次跑就是現在）
    #   🩸 v1 讀現況 ⇒ 落格之後重跑，船尾那一列第 2、6 扇窗已經不是玻璃（找窗的斷言擋下）
    A = DB.export_list(DB.ASM, 'all', ('hide_links=' + R['battery']['link'],))
    A = A[A[:, 2] < NZ]
    vox = np.zeros((NX, NY, NZ), bool)
    vox[A[:, 0], A[:, 1], A[:, 2]] = True

    def before(work):
        try:
            return DB.export_list(work, None, ('mark=三叉戟船尾砲門:begin',)), True
        except SystemExit:
            return DB.export_list(work, None), False
    H, h_mark = before('gura-tridente-01m')
    hull = np.zeros((NX, NY, NZ), bool)
    hcol = {}
    for x, y, z, c in H[H[:, 2] < NZ].tolist():
        hull[x, y, z] = True
        hcol[(x, y, z)] = c
    vox |= hull                                                          # 船殼 at 0,0,0：刻掉的船尾門補回來
    WK = R['stern']['walk']
    W, w_mark = before(WK['work'])
    wat = np.array(WK['at'])
    walk = {(int(x + wat[0]), int(y + wat[1]), int(z + wat[2])): int(c) for x, y, z, c in W.tolist()}
    for p in walk:
        vox[p] = True
    BS = DB.export_list(DB.ASM, '艏斜桅')
    bsp = np.zeros((NX, NY, NZ), bool)
    BS = BS[BS[:, 2] < NZ]
    bsp[BS[:, 0], BS[:, 1], BS[:, 2]] = True
    occ = vox.copy()
    boxes = []
    for m in parts():
        if (m.get('meta') or {}).get('kind') == 'gun':
            continue
        b = m['box']
        boxes.append(b)
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
    src = {}

    def load_type(t, work, scale):
        if t not in src:
            C = DB.export_list(work, None)
            an = {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, work, 'anchors.json'), encoding='utf-8'))['anchors']}
            bot = C[C[:, 2] == 0]
            ax = an['muzzle'][0] + 0.5
            src[t] = {'C': C, 'samp': (C[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3), 'an': an, 'work': work, 'scale': scale,
                      'bs': np.array([[x + ox, y + oy, 0.5] for x, y, _ in bot[:, :3] for ox in (0.3, 0.7) for oy in (0.3, 0.7)]),
                      'piv': np.array([ax, float(bot[:, 1].max() + 1), 0.0])}
        return src[t]

    def world(tp, Q, at, rot):
        q = (np.atleast_2d(Q) - tp['piv']) * tp['scale']
        return rotz(q, rot) + np.asarray(at, float)

    gunocc = np.zeros_like(occ)
    for r in keep:
        tp = load_type(r['type'], r['work'], r['scale'])
        q = (tp['samp'] - tp['piv']) * tp['scale']
        if r['mirror'] == 'y':
            q[:, 1] = -q[:, 1]
        w = np.floor(rotz(q, r['rotate'][2]) + np.asarray(r['at'], float)).astype(int)
        gunocc[w[:, 0], w[:, 1], w[:, 2]] = True
    TT = R['trident']
    tp = load_type('trident', TT['work'], TT['scale'])

    def free(at, rot, hole=None):
        w = np.floor(world(tp, tp['samp'], at, rot)).astype(int)
        if (w < 0).any() or (w[:, 0] >= NX).any() or (w[:, 1] >= NY).any() or (w[:, 2] >= NZ).any():
            return False
        g = occ[w[:, 0], w[:, 1], w[:, 2]] | gunocc[w[:, 0], w[:, 1], w[:, 2]]
        if hole is not None:
            g &= ~hole[w[:, 0], w[:, 1], w[:, 2]]
        return not g.any()

    def support(at, rot, grid):
        b = np.floor(world(tp, tp['bs'], at, rot)).astype(int)
        return [int(grid[b[:, 0], b[:, 1], b[:, 2] - 1].sum()), len(b)]

    def padding(at, rot):
        b = np.floor(world(tp, tp['bs'], at, rot)).astype(int)
        cells = set()
        for x, y, z in {tuple(v) for v in b.tolist()}:
            k = 0
            while not vox[x, y, z - 1 - k]:
                k += 1
                if k > 2:
                    return None
            for j in range(k):
                cells.add((x, y, z - 1 - j))
        return cells

    def tips(at, rot):
        return {k: world(tp, np.array(tp['an'][k], float) + 0.5, at, rot)[0] for k in ('muzzle', 'muzzle-a', 'muzzle-b', 'muzzle-c', 'breech')}

    def commit(at, rot):
        w = np.floor(world(tp, tp['samp'], at, rot)).astype(int)
        gunocc[w[:, 0], w[:, 1], w[:, 2]] = True

    def gbox(at, rot):
        w = world(tp, tp['samp'], at, rot)
        return [float(w[:, 0].min()), float(w[:, 1].min()), float(w[:, 2].min()), float(w[:, 0].max()), float(w[:, 1].max()), float(w[:, 2].max())]

    rows, problems = [], []
    stern_carve, walk_carve, pads_by = {}, {}, {}

    # ── ① 船尾 ──
    for SRow in R['stern']['rows']:
        deck = SRow['deck']
        floor = int(LY.deck_z(plan, deck, 100)) + 1                       # 甲板面上第一層空氣（船尾 x 80–120 這段甲板一樣高）
        z0, z1 = floor + SRow['sill'], floor + SRow['sill'] + SRow['h'] - 1
        if 'yc' in SRow:
            ycs = list(SRow['yc'])
        else:                                                             # 那一列窗的中心：船殼船尾牆上玻璃 87 的 y 段
            gl = sorted({y for (x, y, z), c in hcol.items() if c == 87 and x < 110 and z0 <= z <= z1})
            runs, cur = [], [gl[0]]
            for y in gl[1:]:
                if y == cur[-1] + 1:
                    cur.append(y)
                else:
                    runs.append(cur)
                    cur = [y]
            runs.append(cur)
            assert len(runs) == 7, ('%s 那一列窗不是 7 扇' % deck, [(r[0], r[-1]) for r in runs])
            ycs = [(runs[i - 1][0] + runs[i - 1][-1]) // 2 for i in SRow['window']]
        hw = SRow['w'] // 2
        for yc in ycs:
            side = 'S' if yc > YC else 'P'
            # 船尾牆：門的兩旁（門外 3 格那一欄）每一層 z 從後面數第一段船殼 ⇒ 外表面 fx、厚 t（牆是斜的，每個 z 各量）
            face = {}
            for z in range(z0, z1 + 1):
                fz = []
                for yy in (yc - hw - 3, yc + hw + 3):
                    xs = np.nonzero(hull[40:200, yy, z])[0]
                    if not len(xs):
                        continue
                    x_ = 40 + int(xs[0])
                    k = x_
                    while hull[k, yy, z]:
                        k += 1
                    fz.append((x_, k - x_))
                face[z] = (min(f[0] for f in fz), max(f[0] + f[1] for f in fz))
            cs, block = [], []
            for z in range(z0, z1 + 1):
                xa_, xb_ = face[z]
                for y in range(yc - hw, yc + hw + 1):
                    for x in range(xa_ - 2, xb_ + 2):
                        if hull[x, y, z]:
                            cs.append((x, y, z))
                        elif vox[x, y, z] and (x, y, z) not in walk:
                            block.append((x, y, z))
            if block:
                problems.append(['%s 船尾門 y %d：刻的範圍裡有船殼以外的格 %d' % (deck, yc, len(block)), block[:5]])
            hole = np.zeros_like(occ)
            for p in cs:
                hole[p] = True
            zm = (z0 + z1) // 2
            fx = face[zm][0]
            rot = 90.0
            c0 = tips([0, 0, 0], rot)
            best = None
            for dl in SR['dl']:
                for zi, dzz in enumerate(SR['dz']):
                    x_start = fx - 4.0 - c0['muzzle'][0]                   # 砲口伸出牆外 4 格那裡開始往裡退
                    for kb in range(int(SR['max_back'] / SR['step']) + 1):
                        at = [x_start + kb * SR['step'], yc + 0.5 + dl, float(floor + dzz)]
                        T_ = tips(at, rot)
                        out = float(fx - T_['muzzle'][0])
                        if out < SR['min_muzzle_out']:
                            break
                        if not free(at, rot, hole):
                            continue
                        pads = padding(at, rot)
                        k_ = (pads is None, abs(dl), zi, kb)
                        if best is None or k_ < best[0]:
                            best = (k_, {'at': [round(v, 3) for v in at], 'dl': dl, 'back': kb * SR['step'], 'muzzle_out': round(out, 3), 'pads': sorted(pads) if pads else [],
                                         'support': support(at, rot, vox)})
                        break
            if best is None or best[0][0]:
                problems.append(['%s 船尾 y %d：砲擺不好' % (deck, yc), best and best[0]])
                continue
            c = best[1]
            at = c['at']
            T_ = tips(at, rot)
            # 陽台欄杆開口：跟砲門同寬同高、從船尾面往後 fire_clear 格內的陽台格（🩸 v1 照砲口十字取 ⇒ 砲口落在整數座標、floor 把兩舷切得不一樣，開口不對稱 44 格）
            for p, cc in walk.items():
                if yc - hw <= p[1] <= yc + hw and z0 <= p[2] <= z1 and fx - SR['fire_clear'] <= p[0] < fx:
                    walk_carve[p] = cc
            # 火線：三根管往後 fire_clear 格（管徑 ±2 的十字），開口之後還碰到的實心 ⇒ 記成擋住
            fire_block = 0
            for k in ('muzzle-a', 'muzzle-b', 'muzzle-c'):
                for s in np.arange(0.5, SR['fire_clear'], 0.5):
                    for oy, oz in ((0, 0), (2, 0), (-2, 0), (0, 2), (0, -2)):
                        p = (int(math.floor(T_[k][0] - s)), int(math.floor(T_[k][1] + oy)), int(math.floor(T_[k][2] + oz)))
                        if vox[p] and not hole[p] and p not in walk_carve:
                            fire_block += 1
            for p in cs:
                stern_carve[p] = hcol[p]
            for p in c['pads']:
                pads_by.setdefault(SRow['host'], {})[tuple(p)] = plan['decks_build']['plank']['gun']
                vox[tuple(p)] = True
            commit(at, rot)
            rows.append({'model': '三叉戟砲-船尾-%s' % side, 'host_link': SRow['host_link'], 'host_work': SRow['host'], 'type': 'trident', 'work': TT['work'], 'scale': TT['scale'],
                         'pivot': tp['piv'].tolist(), 'rotate': [0, 0, rot], 'mirror': 'none', 'at': at, 'yc': yc, 'port_z': [z0, z1], 'port_y': [yc - hw, yc + hw],
                         'face_x': fx, 'muzzle_out': c['muzzle_out'], 'support': c['support'], 'pad_cells': len(c['pads']), 'fire_blocked': fire_block,
                         'muzzle': [round(float(v), 3) for v in T_['muzzle']], 'breech': [round(float(v), 3) for v in T_['breech']], 'box': gbox(at, rot),
                         'meta': {'kind': 'gun', 'gun': TT['code'], 'barrels': 3, 'arc': 'stern', 'side': side, 'deck': deck}})
    # 船尾門刻完的格不算擋（下面的砲台、站位預估讀它）
    for p in stern_carve:
        vox[p] = False
    for p in walk_carve:
        vox[p] = False

    # ── ② 船頭砲台 ──
    B = R['battery']
    xa, zu, zt = B['xa'], B['under'], B['top']
    fl = zt + 1
    pz = B['probe_z']
    inside = np.zeros((NX, NY), bool)
    # 艙裡 ＝ probe_z 那一層：從中線往兩舷第一個不是艏斜桅的實心之間；往前到第一個實心（艏斜桅不算）為止
    solid_p = vox[:, :, pz] & ~bsp[:, :, pz]
    for x in range(xa, NX):
        lo = next((y for y in range(YC, 0, -1) if solid_p[x, y]), None)
        hi = next((y for y in range(YC, NY) if solid_p[x, y]), None)
        if lo is None or hi is None or solid_p[x, YC]:
            continue
        inside[x, lo + 1:hi] = True
    fwd = np.full(NY, NX)
    for y in range(NY):
        xs = np.nonzero(solid_p[xa:, y])[0]
        if len(xs):
            fwd[y] = xa + int(xs[0])
    for y in range(NY):
        inside[fwd[y]:, y] = False
    # 艏斜桅讓開（離 bowsprit_clear 格）
    cl = B['bowsprit_clear']
    near_bs = np.zeros((NX, NY), bool)
    zr = slice(zu - cl, fl + 1 + cl)
    bcol = bsp[:, :, zr].any(axis=2)
    for dx in range(-cl, cl + 1):
        for dy in range(-cl, cl + 1):
            near_bs |= np.roll(np.roll(bcol, dx, 0), dy, 1)
    plat = {}
    for x in range(xa, NX):
        for y in np.nonzero(inside[x])[0].tolist():
            if near_bs[x, y]:
                continue
            if vox[x, y, zu] or vox[x, y, zt] or occ[x, y, zu] or occ[x, y, zt]:
                continue
            plat[(x, y, zt)] = B['plank']
            plat[(x, y, zu)] = B['under_color']
    # 只留跟後緣連在一起的那一片（4 連通，同一層）
    from scipy import ndimage
    m2 = np.zeros((NX, NY), bool)
    for (x, y, z) in plat:
        if z == zt:
            m2[x, y] = True
    lab, nl = ndimage.label(m2)
    keep_l = {int(lab[xa, y]) for y in range(NY) if m2[xa, y]}
    plat = {p: c for p, c in plat.items() if int(lab[p[0], p[1]]) in keep_l}
    floor_m = m2 & np.isin(lab, list(keep_l))
    for (x, y, z), c in plat.items():
        vox[x, y, z] = True
    # 砲：艏斜桅兩側、朝正前方；從船頭往後找第一個「輪子全踩在砲台上、零碰撞」的位置
    rot_b = -90.0
    best_bow = None
    for dy in [B['guns_dy']] + [B['guns_dy'] + k for k in (1, -1, 2, -2, 3, 4)]:
        placed = []
        for sg in (1, -1):
            yc = YC + 0.5 + sg * dy
            got = None
            for xx in np.arange(760.0, xa, -0.5):
                at = [float(xx), yc, float(fl)]
                if not free(at, rot_b):
                    continue
                sp = support(at, rot_b, vox)
                if sp[0] < sp[1]:
                    continue
                got = at
                break
            placed.append(got)
        if all(placed):
            best_bow = (dy, placed)
            break
    bow_rows = []
    if not best_bow:
        problems.append(['船頭砲台：兩門都擺不上', None])
    else:
        dy, placed = best_bow
        for sg, at in zip((1, -1), placed):
            T_ = tips(at, rot_b)
            fire_block = []
            for k in ('muzzle-a', 'muzzle-b', 'muzzle-c'):
                for s in np.arange(0.5, SR['fire_clear'], 0.5):
                    p = tuple(np.floor(T_[k] + np.array([s, 0, 0])).astype(int).tolist())
                    if vox[p] or occ[p]:
                        fire_block.append(p)
            commit(at, rot_b)
            side = 'S' if sg > 0 else 'P'
            bow_rows.append({'model': '三叉戟砲-前砲台-%s' % side, 'host_link': B['host_link'], 'host_work': B['host'], 'type': 'trident', 'work': TT['work'], 'scale': TT['scale'],
                             'pivot': tp['piv'].tolist(), 'rotate': [0, 0, rot_b], 'mirror': 'none', 'at': [round(v, 3) for v in at], 'dy': dy,
                             'support': support(at, rot_b, vox), 'fire_blocked': len(fire_block), 'fire_block_at': fire_block[:6],
                             'muzzle': [round(float(v), 3) for v in T_['muzzle']], 'breech': [round(float(v), 3) for v in T_['breech']], 'box': gbox(at, rot_b),
                             'meta': {'kind': 'gun', 'gun': TT['code'], 'barrels': 3, 'arc': 'bow', 'side': side, 'deck': 'battery'}})
        rows += bow_rows
    # 梯子：兩舷各一座（|dy| ladders.dy），從上甲板往船頭爬、梯頂踩上砲台後緣
    LD = B['ladders']
    lad, lpts = {}, {}
    th = LD['tread_half']
    for sg in (1, -1):
        name = 'battery-%s' % ('S' if sg > 0 else 'P')
        yl = YC + sg * LD['dy']
        xs0 = xa - 1
        zl = int(LY.deck_z(plan, 'spar', xs0))                              # 上甲板甲板板最上面那一格
        n = (zt - zl - 2) // LD['rise']
        xs = xa - LD['run'] * (n + 2)                                        # 頂上那段 stringer（kk ＝ n＋1）的前一欄貼著砲台後緣（🩸 v1 少退一階 ⇒ stringer 插進砲台 16 格）
        for kk in range(0, n + 2):
            xr = (xs + LD['run'] * kk, xs + LD['run'] * kk + LD['run'] - 1)
            zt_ = zl + LD['rise'] * kk
            for xx in range(xr[0], xr[1] + 1):
                if 1 <= kk <= n:
                    for y in range(yl - th, yl + th + 1):
                        lad[(xx, y, zt_)] = LD['color']
                zlo, zhi = (zl + 1, zl + 3) if kk == 0 else (zt_ - 3, min(zt_, zt) if kk <= n else zt)
                if kk == n + 1:
                    zlo, zhi = zl + LD['rise'] * n - 3, zt
                for z in range(zlo, zhi + 1):
                    for yy in (yl - th - 1, yl + th + 1):
                        lad[(xx, yy, z)] = LD['color']
        lpts[name] = {'foot': [xs - 1, yl, zl + 1], 'lo': [xs + LD['run'], yl, zl + LD['rise'] + 1],
                      'hi': [xs + LD['run'] * n, yl, zl + LD['rise'] * n + 1], 'head': [xa + 3, yl, fl], 'steps': n}
    lad_block = [p for p in lad if vox[p] or occ[p] or p in plat]
    if lad_block:
        problems.append(['梯子撞到 %d 格' % len(lad_block), lad_block[:6]])
    for p in lad:
        vox[p] = True
    # 後緣矮欄（梯口留開）＋扶手頂金
    RL = B['rail']
    rail = {}
    open_y = set()
    for sg in (1, -1):
        yl = YC + sg * LD['dy']
        open_y |= set(range(yl - th - 1, yl + th + 2))
    for y in np.nonzero(floor_m[xa])[0].tolist():
        if y in open_y:
            continue
        for z in range(fl, fl + RL['h']):
            p = (xa, y, z)
            if not vox[p]:
                rail[p] = RL['cap'] if z == fl + RL['h'] - 1 else RL['color']
    # 兩舷與船頭的邊：外面那一欄在 fl..fl＋2 沒有牆（舷牆比砲台面低）⇒ 同一道矮欄（🩸 v1 只做後緣，側面看砲台兩舷是空的）；
    #   艏斜桅那一側不加（槽邊的格是砲班內側的站位；艏斜桅本身擋著）
    for (x, y, z) in list(plat):
        if z != zt or x == xa:
            continue
        for dx, dy in ((1, 0), (0, 1), (0, -1)):
            nx_, ny_ = x + dx, y + dy
            if floor_m[nx_, ny_] or near_bs[nx_, ny_]:
                continue
            if vox[nx_, ny_, fl:fl + 3].any():
                continue
            for zz in range(fl, fl + RL['h']):
                p = (x, y, zz)
                if not vox[p]:
                    rail[p] = RL['cap'] if zz == fl + RL['h'] - 1 else RL['color']
            break
    for p in rail:
        vox[p] = True
    # 支柱：後緣往裡 1–2 格、2×2，從上甲板到砲台底；候選 y 由兩舷往中間找，柱子那幾欄要全空、不在模型外框裡、不擋新砲
    posts = {}
    ys_f = np.nonzero(floor_m[xa + 1])[0]
    cand = []
    if len(ys_f):
        for ytry in list(range(int(ys_f.min()) + 1, YC - 20)) + list(range(int(ys_f.max()) - 2, YC + 20, -1)):
            cand.append(ytry)
    got_p = []
    for want in ('P', 'S'):
        for ytry in cand:
            if (want == 'P') != (ytry < YC):
                continue
            cols = [(x, y) for x in (xa + 1, xa + 2) for y in (ytry, ytry + 1)]
            ok = True
            zz = []
            for (x, y) in cols:
                zf = int(LY.deck_z(plan, 'spar', x)) + 1
                rng = range(zf, zu)
                if any(vox[x, y, z] or occ[x, y, z] or gunocc[x, y, z] for z in rng):
                    ok = False
                    break
                zz.append((x, y, zf))
            if ok:
                for (x, y, zf) in zz:
                    for z in range(zf, zu):
                        posts[(x, y, z)] = B['post']
                got_p.append(ytry)
                break
    for p in posts:
        vox[p] = True
    # ── ③ 站位預估（照遊戲 40_crew.js）──
    G = vox

    def standZ(x, y, z0_, z1_, head=14):
        for z in range(z1_, z0_ - 1, -1):
            if not G[x, y, z - 1] or G[x, y, z]:
                continue
            if any(G[x, y, z + h] for h in range(1, head)):
                continue
            return z
        return -1
    blk = [b for b in boxes] + [r['box'] for r in keep_boxes(keep, load_type, rotz)] + [r['box'] for r in rows]

    def blocked(x, y, z):
        for b in blk:
            if math.floor(b[0]) - 1 <= x <= math.ceil(b[3]) + 1 and math.floor(b[1]) - 1 <= y <= math.ceil(b[4]) + 1 and b[2] - 3 <= z <= b[5]:
                return True
        return False
    taken = {}

    def standNear(x, y, z0_, z1_, rmax=4):
        for r_ in range(0, rmax + 1):
            for dy_ in range(-r_, r_ + 1):
                for dx_ in range(-r_, r_ + 1):
                    if max(abs(dx_), abs(dy_)) != r_:
                        continue
                    k = (x + dx_, y + dy_)
                    if k in taken:
                        continue
                    z = standZ(x + dx_, y + dy_, z0_, z1_)
                    if z >= 0 and not blocked(x + dx_, y + dy_, z):
                        taken[k] = 1
                        return (x + dx_, y + dy_, z)
        return None
    crew = {}
    for r in rows:
        b = [math.floor(v) for v in r['box']]
        z0_, z1_ = b[2] - 8, b[2] + 3
        ax = np.array(r['muzzle']) - np.array(r['breech'])
        ex = 1 if ax[0] > 0 else -1
        x0 = b[0] if ex > 0 else b[3]
        cyg = (b[1] + b[4]) // 2
        spots = [[x0 + 10 * ex, b[1] - 3], [x0 + 10 * ex, b[4] + 3], [x0 + 4 * ex, b[1] - 3], [x0 + 4 * ex, b[4] + 3], [x0 - 3 * ex, b[1] - 2], [x0 - 3 * ex, b[4] + 2],
                 [x0 - 6 * ex, cyg], [x0 - 10 * ex, cyg - 5]]
        got = [standNear(int(s[0]), int(s[1]), z0_, z1_) for s in spots[:6]]
        crew[r['model'] + '@' + r['host_link']] = {'found': sum(1 for g in got if g), 'of': 6, 'spots': [g for g in got]}
    # ── 寫檔 ──
    od = os.path.join(D, 'masks', 'relayout')
    os.makedirs(od, exist_ok=True)
    out = {'note': 'draft_relayout.py（TASK-0588）—— 現況 ＝ 撤完的組裝件 links=all（%d 格）＋ 其他模型外框 %d ＋ 留下的砲 %d 門' % (len(A), len(boxes), len(keep)),
           'rows': rows, 'problems': problems, 'crew_estimate': crew, 'ladder_points': lpts, 'posts_y': got_p}
    out['stern_carve'] = write_list(os.path.join(od, 'stern_carve.vox.txt'), '# TASK-0588 船尾三叉戟砲門 刻除清單（船殼，世界座標 x,y,z,color；color ＝ 刻之前那一格的顏色，carvevox 顏色守門）\n', stern_carve)
    out['walk_carve'] = write_list(os.path.join(od, 'walk_carve.vox.txt'), '# TASK-0588 陽台欄杆開口 刻除清單（%s 子作品座標 x,y,z,color；顏色守門）\n' % WK['work'],
                                   {(p[0] - wat[0], p[1] - wat[1], p[2] - wat[2]): c for p, c in walk_carve.items()})
    bat = dict(plat)
    bat.update(rail)
    bat.update(posts)
    out['battery'] = write_list(os.path.join(od, 'battery.vox.txt'), '# TASK-0588 船頭砲台（%s，世界座標 at 0,0,0；x,y,z,color）\n' % B['work'], bat)
    out['ladders'] = write_list(os.path.join(od, 'battery_ladders.vox.txt'), '# TASK-0588 砲台的梯子（%s，世界座標 at 0,0,0）\n' % LD['work'], lad)
    out['pads'] = {w: write_list(os.path.join(od, 'pads_%s.vox.txt' % w.split('-')[-1]), '# TASK-0588 船尾三叉戟砲的墊木（%s，世界座標）\n' % w, cells) for w, cells in pads_by.items()}
    xs_f = sorted({p[0] for p in plat})
    out['battery_meta'] = dict(B['deck_meta'], floor='%d:%d,%d:%d' % (xs_f[0], fl, xs_f[-1], fl))
    out['counts'] = {'guns': len(rows), 'stern_carve': len(stern_carve), 'walk_carve': len(walk_carve), 'platform': len(plat), 'rail': len(rail), 'posts': len(posts), 'ladders': len(lad),
                     'pads': {w: len(c) for w, c in pads_by.items()}, 'problems': len(problems)}
    mirror = {'stern_carve': sum(1 for (x, y, z) in stern_carve if (x, 2 * YC - y, z) not in stern_carve),
              'walk_carve': sum(1 for (x, y, z) in walk_carve if (x, 2 * YC - y, z) not in walk_carve),
              'battery': sum(1 for (x, y, z) in bat if (x, 2 * YC - y, z) not in bat), 'ladders': sum(1 for (x, y, z) in lad if (x, 2 * YC - y, z) not in lad)}
    out['mirror_diff'] = mirror
    with open(os.path.join(D, 'verify_relayout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    for r in rows:
        print(r['host_link'], r['model'], 'at', r['at'], 'out', r.get('muzzle_out'), 'support', r['support'], 'fire', r['fire_blocked'], 'pads', r.get('pad_cells'))
    for k, v in crew.items():
        print('站位', k, v['found'], '/', v['of'])
    print('problems', problems)
    print(out['counts'], 'mirror', mirror, 'meta', out['battery_meta'])


def keep_boxes(keep, load_type, rotz_):
    out = []
    for r in keep:
        tp = load_type(r['type'], r['work'], r['scale'])
        q = (tp['samp'] - tp['piv']) * tp['scale']
        if r['mirror'] == 'y':
            q[:, 1] = -q[:, 1]
        w = rotz_(q, r['rotate'][2]) + np.asarray(r['at'], float)
        out.append({'box': [float(w[:, 0].min()), float(w[:, 1].min()), float(w[:, 2].min()), float(w[:, 0].max()), float(w[:, 1].max()), float(w[:, 2].max())]})
    return out


if __name__ == '__main__':
    main()
