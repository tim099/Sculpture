# 利劍號 新圖紙 08（TASK-0022 步驟 10）：彈藥庫與甲板物件 ⇒ masks/gear/magazine.vox.txt、gear_placement.json、verify_gear.json、sheet08_gear_v1.png
#   出處：星辰號 claude-baghlah-01m/design/draft_gear.py（彈藥庫：每個 x 的 (y, z) 剖面取中線那一塊空氣、銅皮／松木地板／橡木壓條、門洞、
#         桶一對一對擺（兩舷鏡像）、上層木架；≤ 50 格封閉空腔填實、新格要連到舊實心；模型 at.z 自動量、門先擺；hoist 梯腳 9×9、梯頭站位；門與開口；廚房四面）
#         ＋ 本船 draft_guns.py（Gun 類、砲的格、後座、迴旋砲 arc、遊戲砲手站位、走路格 nav、繩的直線）。
#   改的地方：
#     · 彈藥庫整間在水線下：房間空氣 z floor+1..ztop、z ztop+1 是銅皮頂板（每 8 格一道橡木樑）；佔滿底艙平台的寬 ⇒ 前後牆都開門洞（不然後面那段底艙走不到）。
#     · 實心照前面每一步的設計清單（跟 draft_guns.py 同一份：船殼＋換色、三層甲板、梯子、長喙、船尾平台、窗玻璃、三根桅、砲柱；篷架、帆桁只擋模型、不給人站）⇒ 不開 Server、落格後重跑逐位元組相同。
#     · 砲用砲自己的格當障礙，另外量後座掃過的格、迴旋砲照 arc 轉一圈掃過的格、遊戲砲手站位（guns_placement.json）。
#     · hoist 取用點照遊戲 23_powder.js hoistStation 重寫（梯腳四周 3 格、梯腳往外那一條 8 格不壓；先讓開梯子找、找不到才不管；clear() 照砲與 galley 的外框）。
#     · 走路格照 draft_guns.py 的 nav（每層甲板 meta floor、每 2 格一點、頭上 12 格、高差 ≤ 3、8 鄰）：加了彈藥庫的格、甲板物件外框、hoist 三個桶之後，三層各幾群、砲手站位與梯子點在不在主群。
#     · 槳手會站的地方（plan.gear.rower_zone，步驟 13 之前的假設）不准放東西；帆布與繩（步驟 8 export 的 obj）離甲板物件多遠。
#   用法：python -I -X utf8 draft_gear.py [--probe=shift=<模型>:<dx>] [--probe=nokind=<模型>] [--probe=cap=<n>] [--probe=x0=<x>] [--probe=x1=<x>] [--probe=nochocks=1]
#     反向對照不寫檔：把一個模型沿 x 推（量完 z 才推；要報撞）；拿掉一個模型的 kind；換桶數（看那個桶數的讀數）。
import sys, os, json, math, hashlib
from collections import deque
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_guns as DG
from draft_lines import palette_rgb

V = HL.V
HEAD = 12           # 走路：站的格頭上 1.2 m 空（Ship_Decks）
KEEP_HEAD = 8       # 取用點：9×9 平地、頭上 0.8 m 空（遊戲 23_powder.js clear()）
LAD_KEEP, LAD_LANE = 3, 8   # 遊戲 23_powder.js：桶堆離梯腳四周幾格、梯腳往外那一條多長


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def r3(v):
    return [round(float(c), 3) for c in v]


def corners(cells, inset=0.2):
    a, b = inset, 1.0 - inset
    o = np.array([[0.5, 0.5, 0.5]] + [[(a, b)[k & 1], (a, b)[(k >> 1) & 1], (a, b)[(k >> 2) & 1]] for k in range(8)])
    return (cells[:, None, :] + o[None]).reshape(-1, 3)


class Model:
    """CLI 外部模型：p ＝ at ＋ Rz(rot)·((v − pivot) × scale)（scale 可以分軸；這一步沒有 mirror）。"""

    def __init__(s, cells, pivot, scale, rot):
        s.cells = np.asarray(cells, float)
        s.pivot = np.array(pivot, float)
        s.scale = np.array(scale if isinstance(scale, (list, tuple)) else [scale] * 3, float)
        s.rot = float(rot)
        s.samples = corners(s.cells)
        s.centers = s.cells + 0.5
        zmin = s.cells[:, 2].min()
        s.bottom = corners(s.cells[s.cells[:, 2] == zmin])
        s.bottom = s.bottom[s.bottom[:, 2] < zmin + 0.5]
        s.lo, s.hi = s.cells.min(0), s.cells.max(0) + 1

    def world(s, P, at):
        q = (np.asarray(P, float) - s.pivot) * s.scale
        c, sn = math.cos(math.radians(s.rot)), math.sin(math.radians(s.rot))
        return np.stack([q[..., 0] * c - q[..., 1] * sn + at[0], q[..., 0] * sn + q[..., 1] * c + at[1], q[..., 2] + at[2]], -1)

    def bbox(s, at):
        C = np.array([[(s.lo[0], s.hi[0])[k & 1], (s.lo[1], s.hi[1])[(k >> 1) & 1], (s.lo[2], s.hi[2])[(k >> 2) & 1]] for k in range(8)], float)
        W = s.world(C, at)
        return W.min(0), W.max(0)

    def local(s, P, at):
        q = np.asarray(P, float) - np.array(at, float)
        c, sn = math.cos(math.radians(-s.rot)), math.sin(math.radians(-s.rot))
        return np.stack([q[..., 0] * c - q[..., 1] * sn, q[..., 0] * sn + q[..., 1] * c, q[..., 2]], -1) / s.scale + s.pivot


def grid_of(cells, shape):
    G = np.zeros(shape, bool)
    c = np.array(sorted(cells), int)
    if len(c):
        G[c[:, 0], c[:, 1], c[:, 2]] = True
    return G


def hit(P, grid):
    """取樣點落在哪一格；框外算實心（不准出框）。"""
    i = np.floor(np.asarray(P, float)).astype(int)
    ok = np.all((i >= 0) & (i < np.array(grid.shape)), -1)
    out = np.ones(i.shape[:-1], bool)
    j = i[ok]
    out[ok] = grid[j[:, 0], j[:, 1], j[:, 2]]
    return out


def mark(grid, P):
    i = np.floor(np.asarray(P, float)).astype(int)
    ok = np.all((i >= 0) & (i < np.array(grid.shape)), -1)
    j = i[ok]
    grid[j[:, 0], j[:, 1], j[:, 2]] = True


def box_cells(lo, hi):
    return (int(math.floor(lo[0])), int(math.ceil(hi[0])), int(math.floor(lo[1])), int(math.ceil(hi[1])), int(math.floor(lo[2])), int(math.ceil(hi[2])))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    probe = dict(a[len('--probe='):].split('=', 1) for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    AX, AY, AZ = [int(v) for v in plan['space']['assembly']]
    SH = (AX, AY, AZ)
    GB = plan['gear']
    MG = GB['magazine']
    for k in ('cap', 'x0', 'x1'):                     # 試別的桶數、別的房間前後牆（掃描用，不寫檔）
        if k in probe:
            MG[k] = int(probe[k])
    SRC = os.path.join(HERE, 'masks', 'gear_src')
    WL = int(plan['waterline']['z'])

    # ── 步驟 10 以前的實心（設計清單；跟 draft_guns.py 同一份）──
    hull = load('masks/hull/hull_01.vox.txt')
    hull.update(load('masks/step6/hull_paint.vox.txt'))
    decks = {k: load('masks/decks/%s.vox.txt' % k) for k in ('hold', 'main', 'quarter')}
    stand = set(hull)
    for d in decks.values():
        stand |= set(d)
    for f in ('ladders/main', 'ladders/quarter', 'deco/beak', 'deco/platform', 'deco/glass', 'masts/mizzen', 'masts/main', 'masts/fore',
              'guns/posts_main', 'guns/posts_quarter'):
        stand |= set(load('masks/' + f + '.vox.txt'))
    awning = set(load('masks/deco/awning.vox.txt'))
    yardw = set()
    for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
        off = [int(round(p['at'][i] - p['pivot'][i])) for i in range(3)]
        yardw |= {(x + off[0], y + off[1], z + off[2]) for (x, y, z) in load('masks/yards/lateen-%s.vox.txt' % p['mast'])}
    S0 = grid_of(stand, SH)                         # 船（站人用的格）
    SA = S0 | grid_of(awning | yardw, SH)           # ＋篷架、帆桁（只擋模型）
    deck_top = {k: {} for k in decks}
    for k, d in decks.items():
        for (x, y, z) in d:
            deck_top[k][(x, y)] = max(deck_top[k].get((x, y), -1), z + 1)

    # ── 砲：砲自己的格、外框、後座掃過的格、迴旋砲 arc 掃過的格、砲手站位 ──
    GBG = {k: V(v) for k, v in plan['guns_build'].items() if not k.endswith('src')}
    gun_t = {k: DG.Gun(k, t, GBG['search']['inset']) for k, t in GBG['types'].items()}
    gun_rows = [r for r in json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))['rows'] if r.get('at') is not None]
    gun_cells = np.zeros(SH, bool)
    recoil_cells = np.zeros(SH, bool)
    sweep_cells = np.zeros(SH, bool)
    gun_box, crew_spots = [], []
    RC = GBG['recoil']
    for r in gun_rows:
        g = gun_t[r['type']]
        mir = r['side'] == 'P'
        mark(gun_cells, g.world(g.centers, r['at'], r['phi'], mir))
        gun_box.append((r['name'], np.array(r['bbox'][0], float), np.array(r['bbox'][1], float)))
        dist = max(RC['min'], g.barrel_len * RC['k'])
        ax = g.axis(r['phi'], mir)
        part = g.barrel_samples if r['swivel'] else g.samples
        for t in np.arange(0.5, dist + 1e-9, 0.5):
            mark(recoil_cells, g.world(part, np.array(r['at'], float) - ax * t, r['phi'], mir))
        if r['swivel'] and r.get('arc'):
            a0, a1 = [int(v) for v in r['arc'].split(',')]
            for a in range(a0, a1 + 1, GBG['sweep_step_deg']):
                mark(sweep_cells, g.world(g.samples, r['at'], float(a), mir))
        for a in r['crew']['at']:
            crew_spots.append((r['name'], r['deck'], [float(v) for v in a]))
    recoil_cells &= ~gun_cells
    sweep_cells &= ~gun_cells

    # ── 彈藥庫：每個 x 的 (y, z) 剖面，floor..ztop+1 那一段離中線最近的一塊空氣（4 連通）──
    C = MG['colors']
    COPPER, OAK, DARK, PINE = C['copper'], C['oak'], C['dark'], C['pine']
    X0, X1, F, ZTOP = MG['x0'], MG['x1'], MG['floor'], MG['ztop']
    ZC = ZTOP + 1                                    # 頂板那一層
    interior, mlog = {}, []
    for x in range(X0, X1 + 1):
        band = np.zeros(SH[1:], bool)
        band[:, F:ZC + 1] = ~SA[x, :, F:ZC + 1]
        lab, _ = ndimage.label(band)
        I = np.zeros_like(band)
        if band[YC, F + 1]:
            I = lab == lab[YC, F + 1]
        interior[x] = I
        ys, zs = np.nonzero(I)
        mlog.append({'x': x, 'cells': int(I.sum()), 'y': [int(ys.min()), int(ys.max())] if len(ys) else None})
    mag = {}
    dw, dh = MG['door_w'], MG['door_head']
    door_xs = {'aft': X0, 'fore': X1}
    dxs = [door_xs[k] for k in MG['doors']]
    for x, I in interior.items():
        wall = x in (X0, X1)
        for y, z in zip(*np.nonzero(I)):
            y, z = int(y), int(z)
            if z == F:
                mag[(x, y, z)] = OAK if (y - YC) % 6 == 0 else PINE                  # 地板：松木、每 6 格一條橡木壓條
            elif z == ZC:
                mag[(x, y, z)] = OAK if (x - X0) % 8 == 0 or wall else COPPER         # 頂板：銅皮、每 8 格一道橡木樑
            elif wall:
                if x in dxs and abs(y - YC) <= dw // 2 and z <= ZTOP - dh:
                    continue                                                        # 門洞
                frame = (y - YC) % 8 == 0 or z == F + 1 or z == ZTOP
                if x in dxs and (abs(y - YC) == dw // 2 + 1 and z <= ZTOP - dh + 1 or abs(y - YC) <= dw // 2 and z == ZTOP - dh + 1):
                    frame = True
                mag[(x, y, z)] = OAK if frame else COPPER
            else:
                side = any(not (0 <= y + d < I.shape[0]) or (not I[y + d, z] and SA[x, y + d, z]) for d in (-1, 1))
                if side and abs(y - YC) > 6:
                    mag[(x, y, z)] = COPPER                                         # 船殼那一面貼銅皮
    free = set()
    for x, I in interior.items():
        for y, z in zip(*np.nonzero(I)):
            k = (x, int(y), int(z))
            if F + 1 <= k[2] <= ZTOP and k not in mag:
                free.add(k)
    B = MG['barrel']
    R = B['d'] * B['mpv'] / 0.1 / 2
    H = B['h'] * B['mpv'] / 0.1
    barrels, rack, capacity = [], {}, []

    def foot(cx, cy):
        return [(x, y) for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R))) for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)))]

    def body_free(cx, cy, z0):
        # 軸心 R ＋ 0.75 以內每一格都要空（收穫號 v3：R ＋ 0.3 會讓桶擦到銅皮）
        return all((x, y, z) in free and (x, y, z) not in rack for x in range(int(math.floor(cx - R - 1)), int(math.ceil(cx + R + 1)))
                   for y in range(int(math.floor(cy - R - 1)), int(math.ceil(cy + R + 1))) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= (R + 0.75) ** 2
                   for z in range(int(math.floor(z0)), int(math.ceil(z0 + H))))

    def under_barrel(x, y, z, t_now):
        return any(b['tier'] < t_now and b['at'][2] <= z < b['at'][2] + H and (x + 0.5 - b['at'][0]) ** 2 + (y + 0.5 - b['at'][1]) ** 2 <= R ** 2 for b in barrels)

    def in_barrel(x, y, z):
        return any(z < b['at'][2] + H and z + 1 > b['at'][2] and (x + 0.5 - b['at'][0]) ** 2 + (y + 0.5 - b['at'][1]) ** 2 <= (R + 0.75) ** 2 for b in barrels)

    for t in range(0, 4):
        n_t = 0
        cx = X0 + 2 + R
        while cx + R <= X1 - 1:
            z0 = F + 1 + t * B['tier']
            cy = YC + 0.5 + (B['aisle'] + 0.5 + R)
            jcol = 0
            while abs(cy - YC) < 80 and jcol < MG.get('cols', 99):                 # 一次一對（兩舷鏡像）；cols：每舷最多幾排（都靠走道 ⇒ 每個桶都摸得到）
                pair = [(cy, 1), (2 * YC + 1 - cy, -1)]
                shelf = {s: [(x, y, int(z0) - 1) for x, y in foot(cx, c)] if t else [] for c, s in pair}
                ok = all(body_free(cx, c, z0) and all(p in free and p not in rack and not under_barrel(*p, t) for p in shelf[s]) for c, s in pair)
                posts = {}
                if ok and t:
                    def post_ok(x, y):
                        return all((x, y, z) in free and (x, y, z) not in rack and not in_barrel(x, y, z) for z in range(F + 1, int(z0) - 1))
                    col = sorted((x, y) for x, y, _ in shelf[1] if post_ok(x, y))
                    best = max(((a, b) for a in col for b in col), key=lambda ab: ((ab[0][0] - ab[1][0]) ** 2 + (ab[0][1] - ab[1][1]) ** 2, ab), default=None)
                    if not best or best[0] == best[1]:
                        ok = False
                    else:
                        posts[1] = sorted(set(best))
                        posts[-1] = [(x, 2 * YC - y) for x, y in posts[1]]
                        ok = all(post_ok(x, y) for x, y in posts[-1])
                if ok:
                    n_t += 2
                    if len(barrels) + 2 <= MG['cap']:
                        for c, s in pair:
                            barrels.append({'at': [round(cx, 3), round(c, 3), round(z0, 3)], 'tier': t})
                            for p in shelf[s]:
                                rack[p] = OAK
                            for px, py in posts.get(s, []):
                                for z in range(F + 1, int(z0) - 1):
                                    rack[(px, py, z)] = DARK
                elif not t:
                    break
                cy += B['pitch']
                jcol += 1
            cx += B['pitch']
        capacity.append(n_t)
        if len(barrels) >= MG['cap'] or (not n_t and t):
            break
    assert not set(rack) & set(mag)
    mag.update(rack)
    free -= set(rack)

    # ── 墊木：房間裡從門走不到的地板（最外一排桶跟船殼斜面中間那一條）墊到 floor＋3 ⇒ 站上去高過那一層甲板的走路帶（meta floor ＋3），
    #   不再是走路格上的孤島（v1 沒墊：底艙走路格多出 25／11／3 點的三小群）。照桶的外框外擴 1 格擋（同 nav 的 blocked；這裡照連續座標算重疊 ⇒ 兩舷對稱）。──
    GM = SA.copy()
    for k in mag:
        GM[k] = True
    bbx = [(b['at'][0] - R, b['at'][1] - R, b['at'][2], b['at'][0] + R, b['at'][1] + R, b['at'][2] + H) for b in barrels]

    def st_room(x, y):
        """這一柱在 floor..floor＋3 之間站得住的最高一格（腳下實心、頭上 HEAD 格空、不在桶的外框外擴 1 格裡）；沒有 ⇒ None。"""
        for z in range(F + 3, F - 1, -1):
            if GM[x, y, z - 1] and not GM[x, y, z:z + HEAD].any():
                if any(x + 1 > b[0] - 1 and x < b[3] + 1 and y + 1 > b[1] - 1 and y < b[4] + 1 and b[2] - 3 <= z <= b[5] for b in bbx):
                    return None
                return z
        return None
    cols = {}
    for x in range(X0 - 3, X1 + 4):                                            # 門外 3 格也算（從門外走進來）
        for y in range(YC - 80, YC + 81):
            z = st_room(x, y)
            if z is not None:
                cols[(x, y)] = z
    # 只走「四鄰都站得住」的格（走路格每 2 格一點，一格寬的縫走不過去；遊戲那側的起點奇偶不一定 ⇒ 照兩格寬算），走到的再往外算一圈
    wide = {k for k in cols if all((k[0] + dx, k[1] + dy) in cols for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    seeds = [(X0 - 2, YC), (X1 + 2, YC)]
    seen = set(seeds)
    q = deque(seeds)
    while q:
        a = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            b = (a[0] + dx, a[1] + dy)
            if b in wide and b not in seen and abs(cols[b] - cols[a]) <= 3 and (not (dx and dy) or ((a[0] + dx, a[1]) in wide and (a[0], a[1] + dy) in wide)):
                seen.add(b)
                q.append(b)
    seen |= {(a[0] + dx, a[1] + dy) for a in list(seen) for dx in (-1, 0, 1) for dy in (-1, 0, 1)} & set(cols)
    chocks = {}
    for (x, y), z in sorted(cols.items()):
        if (x, y) in seen or not X0 < x < X1:
            continue
        for zz in range(z, F + 4):
            for yy in (y, 2 * YC - y):                                         # 兩舷一起墊（鏡像）
                if not GM[x, yy, zz]:
                    chocks[(x, yy, zz)] = OAK
    if probe.get('nochocks'):
        chocks = {}                                                             # 反向對照：不墊 ⇒ 底艙走路格要報孤島
    mag.update(chocks)
    free -= set(chocks)

    # ── 封閉空腔（≤ 50 格填實）、新格要連到舊實心 ──
    on_solid = [k for k in mag if SA[k]]
    sealed, floating = [], []
    xa, xb, za, zb = X0 - 2, X1 + 2, F - 2, ZC + 3
    sub = SA[xa:xb + 1, :, za:zb + 1].copy()
    nw = np.zeros_like(sub)
    for (x, y, z) in mag:
        nw[x - xa, y, z - za] = True
    lab, n = ndimage.label(~(sub | nw))
    edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
    for L in range(1, n + 1):
        if L in edge:
            continue
        xs_, ys_, zs_ = np.nonzero(lab == L)
        if len(xs_) > 50:
            sealed.append(['big', int(len(xs_)), int(xs_.min()) + xa, int(ys_.min()), int(zs_.min()) + za])
            continue
        for x, y, z in zip(xs_, ys_, zs_):
            mag[(int(x) + xa, int(y), int(z) + za)] = OAK
            nw[x, y, z] = True
        sealed.append(['filled', int(len(xs_)), int(xs_.min()) + xa, int(ys_.min()), int(zs_.min()) + za])
    lab, n = ndimage.label(sub | nw)
    anchored = set(np.unique(lab[sub])) - {0}
    floating = [(np.argwhere(lab == L).min(axis=0) + [xa, 0, za]).tolist() for L in np.unique(lab[nw]) if L not in anchored]
    MAGG = grid_of(set(mag), SH)
    SS = S0 | MAGG                                    # 站人的格（遊戲 BASE：船的格，外部模型不算）
    SX = SA | MAGG                                    # 模型要避開的實心

    # ── 模型 ──
    src_cache = {}

    def src(w):
        if w not in src_cache:
            src_cache[w] = np.loadtxt(os.path.join(SRC, w + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)[:, :3].astype(float)
        return src_cache[w]

    obst = SX | gun_cells                             # 門先擺，擺好的門再加進來
    rows = []
    order = sorted(GB['models'], key=lambda m: 0 if m.get('door') else 1)
    for m in order:
        sc = list(m['scale']) if isinstance(m['scale'], list) else [m['scale']] * 3
        at = list(m['at'])
        g = Model(src(m['work']), m['pivot'], sc, m['rotate'])
        if at[2] is None:
            bot = g.world(g.bottom, (at[0], at[1], 0.0))
            tp = deck_top[m['host']]
            under = [tp[c] for c in set(map(tuple, np.floor(bot[:, :2]).astype(int).tolist())) if c in tp]
            z0 = min(under) if under else 0
            zf = None
            for z in range(z0, z0 + 40):
                if hit(g.world(g.samples, (at[0], at[1], float(z))), obst).any():
                    continue
                below = g.world(g.bottom, (at[0], at[1], float(z)))
                below[:, 2] -= 0.5
                if hit(below, obst).any():
                    zf = z
                    break
            at[2] = float(zf if zf is not None else z0)
        if probe.get('shift', '').split(':')[0] == m['name']:
            at[0] += float(probe['shift'].split(':')[1])          # 量完 z 才推（星辰號 v1 先推再量 ⇒ 量 z 把它抬開、什麼都報不出來）
        lo, hi = g.bbox(at)
        r = {'name': m['name'], 'host': m['host'], 'work': m['work'], 'at': r3(at), 'pivot': m['pivot'], 'scale': [round(v, 7) for v in sc],
             'rotate': m['rotate'], 'meta': dict(m['meta']), 'bbox': [r3(lo), r3(hi)]}
        for k in ('door', 'opening', 'wall_x'):
            if k in m:
                r[k] = m[k]
        r['_g'] = g
        rows.append(r)
        if m.get('door'):
            mark(obst, g.world(g.centers, at))
    BW = B['work']
    for i, b in enumerate(barrels):
        g = Model(src(BW), B['pivot'], B['scale'], 0)
        lo, hi = g.bbox(b['at'])
        rows.append({'name': '桶-%03d' % (i + 1), 'host': 'magazine', 'work': BW, 'at': r3(b['at']), 'pivot': B['pivot'], 'scale': [B['scale']] * 3, 'rotate': 0,
                     'meta': {'kind': 'powder', 'powder_lb': 100}, 'tier': b['tier'], 'bbox': [r3(lo), r3(hi)], '_g': g})
    if probe.get('nokind'):
        for r in rows:
            if r['name'] == probe['nokind']:
                r['meta'] = {k: v for k, v in r['meta'].items() if k != 'kind'}

    # ── 每個模型：撞（格心＋八角內縮 0.2）、腳、離砲／後座／迴旋砲／砲手／繩 ──
    door_cells = np.zeros(SH, bool)
    for r in rows:
        if r.get('door'):
            mark(door_cells, r['_g'].world(r['_g'].centers, r['at']))
    RE = json.load(open(os.path.join(HERE, 'verify_rigging.json'), encoding='utf-8'))['rope_ends']
    RT = {r_['name']: r_['thickness'] for r_ in json.load(open(os.path.join(HERE, 'rig_plan.json'), encoding='utf-8'))['ropes']}
    ropes = [(nm, np.array(e['from'], float), np.array(e['to'], float), RT.get(nm, 0.5) / 2.0) for nm, e in sorted(RE.items())]
    LP = json.load(open(os.path.join(HERE, 'ladder_points.json'), encoding='utf-8'))
    RZ = GB['rower_zone']
    oars = [p for p in json.load(open(os.path.join(HERE, 'verify_lines.json'), encoding='utf-8'))['ports'] if p['kind'] == 'oar']
    rz_x = (min(p['x'][0] for p in oars) - RZ['pad_x'], max(p['x'][1] for p in oars) + RZ['pad_x'])
    coll = {}
    nofoot, nokind = [], []
    for r in rows:
        g = r['_g']
        P = g.world(g.samples, r['at'])
        lo, hi = np.array(r['bbox'][0]), np.array(r['bbox'][1])
        hits = {'solid': int(hit(P, SX).sum()), 'gun': int(hit(P, gun_cells).sum()), 'recoil': int(hit(P, recoil_cells).sum()),
                'swivel_sweep': int(hit(P, sweep_cells).sum())}
        if not r.get('door'):
            hits['door'] = int(hit(P, door_cells).sum())
        hits = {k: v for k, v in hits.items() if v}
        if hits:
            coll[r['name']] = hits
        cx, cy, fz = int(math.floor((lo[0] + hi[0]) / 2)), int(math.floor((lo[1] + hi[1]) / 2)), int(math.floor(lo[2])) - 1
        d = next((dd for dd in range(0, GB['foot_reach'] + 1) if SX[cx, cy, fz - dd] or (r['host'] == 'magazine' and MAGG[cx, cy, fz - dd])), None)
        r['foot_gap'] = d
        if d is None and not r.get('door'):
            nofoot.append(r['name'])
        bot = g.world(g.bottom, r['at'])
        bot[:, 2] -= 0.5
        r['support'] = round(float(hit(bot, SX).mean()), 3)
        if 'kind' not in r['meta']:
            nokind.append(r['name'])
        C_ = g.world(g.centers, r['at'])
        best = None
        for nm, a, b, rad in ropes:
            dmin = float(DG.seg_points_dist(a, b, C_).min()) - 0.5 - rad
            if best is None or dmin < best[0]:
                best = [round(dmin, 2), nm]
        r['rope_clear'] = best
        r['gun_box_overlap'] = [n for n, a, b in gun_box if not (np.any(hi <= a) or np.any(b <= lo))]
        # 砲手站位：模型外框（xy 外擴 1 格、z 在 [底 −3, 頂]，同遊戲 40_crew.js 的擋法）裡有沒有砲手；最近的水平距離
        inbox, dmin = [], None
        for gn, dk, a in crew_spots:
            if lo[0] - 1 <= a[0] <= hi[0] + 1 and lo[1] - 1 <= a[1] <= hi[1] + 1 and lo[2] - 3 <= a[2] <= hi[2]:
                inbox.append(gn)
            if abs(a[2] - lo[2]) <= 14:
                dd = math.hypot(max(lo[0] - a[0], 0, a[0] - hi[0]), max(lo[1] - a[1], 0, a[1] - hi[1]))
                if dmin is None or dd < dmin[0]:
                    dmin = [round(dd, 2), gn]
        r['crew_in_box'] = inbox
        r['crew_nearest'] = dmin
        r['ladder_pts_in_box'] = [[ln, pk] for ln, v in sorted(LP.items()) for pk, p in sorted(v['points'].items())
                                  if lo[0] <= p[0] + 0.5 <= hi[0] and lo[1] <= p[1] + 0.5 <= hi[1] and p[2] < hi[2] and p[2] + HEAD > lo[2]]
        r['rower_zone'] = bool(r['host'] in ('main',) and hi[0] > rz_x[0] and lo[0] < rz_x[1] and (hi[1] > YC + 0.5 + RZ['dy_min'] or lo[1] < YC + 0.5 - RZ['dy_min']))
        r['dy_max'] = round(float(max(hi[1] - (YC + 0.5), (YC + 0.5) - lo[1])), 2)
    overlap = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            (alo, ahi), (blo, bhi) = (np.array(a['bbox'][0]), np.array(a['bbox'][1])), (np.array(b['bbox'][0]), np.array(b['bbox'][1]))
            if np.any(ahi <= blo) or np.any(bhi <= alo):
                continue
            loc = b['_g'].local(a['_g'].world(a['_g'].centers, a['at']), b['at'])
            cells_b = set(map(tuple, b['_g'].cells.astype(int).tolist()))
            k = sum(1 for t_ in np.floor(loc).astype(int).tolist() if tuple(t_) in cells_b)
            if k:
                overlap.append([a['name'], b['name'], k])

    # ── 帆布與繩（步驟 8 export 的 obj；只讀頂點）──
    cloth = {'files': {}, 'by_model': {}}
    CV, CO = [], []
    for rel in GB.get('cloth_objs', []):
        fn = os.path.normpath(os.path.join(HERE, rel))
        if not os.path.exists(fn):
            cloth['files'][rel] = None
            continue
        cloth['files'][rel] = hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]
        cur = None
        for line in open(fn, encoding='utf-8'):
            if line.startswith('o '):
                cur = ('sail' if line.startswith('o sail_') else 'rope' if line.startswith('o rope_') else None)
                if cur:
                    cur = cur + ':' + (line.split('#', 1)[1].strip() if '#' in line else line[2:].strip())
            elif line.startswith('v ') and cur:
                x, y, z = map(float, line.split()[1:4])
                CV.append((x, z, y))
                CO.append(cur)
    if CV:
        CV = np.array(CV)
        tree = cKDTree(CV)
        for r in rows:
            if r['host'] == 'magazine':
                continue
            d_, i_ = tree.query(r['_g'].world(r['_g'].samples, r['at']))
            k = int(np.argmin(d_))
            cloth['by_model'][r['name']] = [round(float(d_[k]), 2), CO[int(i_[k])]]
        cloth['min'] = min((v for v in cloth['by_model'].values()), key=lambda v: v[0]) if cloth['by_model'] else None

    # ── 走路：站得住的格（腳下實心、頭上 12 格空、不在非門模型與砲的外框裡）──
    box_solid = np.zeros(SH, bool)
    for r in rows:
        if r.get('door'):
            continue
        x0, x1, y0, y1, z0, z1 = box_cells(*r['bbox'])
        box_solid[x0:x1, y0:y1, z0:z1] = True
    for n_, a, b in gun_box:
        x0, x1, y0, y1, z0, z1 = box_cells(a, b)
        box_solid[x0:x1, y0:y1, z0:z1] = True
    WS = SS | box_solid

    def standable(x, y, z, head=HEAD, G=None):
        G = WS if G is None else G
        return 0 <= x < SH[0] and 0 <= y < SH[1] and 1 <= z < SH[2] - head and G[x, y, z - 1] and not G[x, y, z:z + head].any()

    def flood(seed, zlo, zhi, G=None):
        """從 seed 沿站得住的格走（8 鄰、高差 ≤ 3、對角兩邊都要站得住），只走 z 在 [zlo, zhi] 的。"""
        if not standable(*seed, G=G):
            return set()
        seen = {seed}
        q = deque([seed])
        top = {(seed[0], seed[1]): seed[2]}
        while q:
            x, y, z = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx_, ny_ = x + dx, y + dy
                if (nx_, ny_) in top:
                    continue
                for zz in (z, z + 1, z - 1, z + 2, z - 2, z + 3, z - 3):
                    if zlo <= zz <= zhi and standable(nx_, ny_, zz, G=G):
                        if dx and dy and not (any(standable(x + dx, y, z + e, G=G) for e in range(-3, 4)) and any(standable(x, y + dy, z + e, G=G) for e in range(-3, 4))):
                            break
                        top[(nx_, ny_)] = zz
                        seen.add((nx_, ny_, zz))
                        q.append((nx_, ny_, zz))
                        break
        return seen

    hold_walk = flood(tuple(LP['hold-aft']['points']['foot']), F - 3, ZC + 2)
    main_walk = flood(tuple(LP['hold-fore']['points']['head']), 36, 56)

    # 桶摸得到：照墊木那一把的走法（桶外框外擴 1 格擋、兩格寬才走得過）從門外走得到的房間地板格，離桶身水平 ≤ reach_cells
    hw = np.array(sorted((x, y, cols[(x, y)]) for (x, y) in seen if X0 <= x <= X1), float) + [0.5, 0.5, 0]
    reach = {}
    for r in rows:
        if r['host'] != 'magazine':
            continue
        if len(hw):
            d_ = np.hypot(hw[:, 0] - r['at'][0], hw[:, 1] - r['at'][1]) - R
            reach[r['name']] = round(float(d_.min()), 2)
        else:
            reach[r['name']] = None
    unreachable = [k for k, v in reach.items() if v is None or v > MG['reach_cells']]

    # ── 廚房四面（Ship_Fittings §9.13：外框外 2 格的四個面中點，0.6 m 內要有走路格、而且走得到）──
    def near_stand(px, py, pz, rad, walk):
        best = None
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if dx * dx + dy * dy > rad * rad:
                    continue
                for dz in range(-3, 4):
                    c = (px + dx, py + dy, pz + dz)
                    if standable(*c) and (walk is None or c in walk):
                        d = round(math.sqrt(dx * dx + dy * dy), 2)
                        if best is None or d < best[0]:
                            best = (d, list(c))
        return best

    galley = {}
    for r in rows:
        if r['meta'].get('kind') != 'galley':
            continue
        lo, hi = np.array(r['bbox'][0]), np.array(r['bbox'][1])
        cxm, cym, zb = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, int(math.floor(lo[2]))
        faces = {'-x': (lo[0] - 2, cym), '+x': (hi[0] + 2, cym), '-y': (cxm, lo[1] - 2), '+y': (cxm, hi[1] + 2)}
        galley[r['name']] = {f: near_stand(int(math.floor(px)), int(math.floor(py)), zb, 6, main_walk) for f, (px, py) in faces.items()}

    # ── hoist 取用點（遊戲 23_powder.js hoistStation 重寫）──
    def standZ(x, y, z0, z1, head):
        for z in range(z1, z0 - 1, -1):
            if not (0 <= x < SH[0] and 0 <= y < SH[1] and 1 <= z < SH[2] - head):
                continue
            if not SS[x, y, z - 1] or SS[x, y, z]:
                continue
            if SS[x, y, z + 1:z + head].any():
                continue
            return z
        return -1

    clear_boxes = [(a, b) for n_, a, b in gun_box] + [(np.array(r['bbox'][0]), np.array(r['bbox'][1])) for r in rows if r['meta'].get('kind') == 'galley']
    lad_ends = []
    for ln, v in sorted(LP.items()):
        pts = [v['points'][k] for k in ('foot', 'lo', 'hi', 'head')]
        if pts[0][2] > pts[-1][2]:
            pts.reverse()
        lad_ends += [pts[0], pts[-1]]

    def clear(x, y, z, ladk):
        if ladk and any(abs(p[2] - z) <= 6 and x - 1 - LAD_KEEP <= p[0] <= x + 10 + LAD_KEEP and y - 1 - LAD_KEEP <= p[1] <= y + 10 + LAD_KEEP for p in lad_ends):
            return False
        for dy in range(0, 10, 3):
            for dx in range(0, 10, 3):
                if standZ(x + dx, y + dy, z - 1, z + 1, KEEP_HEAD) < 0:
                    return False
        return not any(x + 11 > b[0][0] and x - 2 < b[1][0] and y + 11 > b[0][1] and y - 2 < b[1][1] and z + 8 > b[0][2] and z - 3 < b[1][2] for b in clear_boxes)

    def in_gun(x, y, z):
        return any(x > a[0] - 2 and x < b[0] + 2 and y > a[1] - 2 and y < b[1] + 2 and z + 8 > a[2] and z - 3 < b[2] for n_, a, b in gun_box)

    hoist = {}
    keg_boxes = []
    KB = np.array([2 * R, 2 * R, H])                    # 取用點的桶：照桶的外框（0.44 × 0.44 × 0.54 m）；遊戲照網格頂點，這裡近似
    for path in MG['hoist'].split(','):
        ln = path.rsplit('/', 1)[1]
        v = LP[ln]
        fx, fy, fz = v['points']['foot']
        hx, hy, hz = v['points']['head']
        ex, ey = fx - hx, fy - hy
        lane = None
        if math.hypot(ex, ey) >= 2:
            sd = 1 if (ex if abs(ex) >= abs(ey) else ey) > 0 else -1
            a0, a1 = (0, LAD_LANE) if sd > 0 else (-LAD_LANE, 0)
            lane = [fx + a0, fy - 2, fx + a1, fy + 2] if abs(ex) >= abs(ey) else [fx - 2, fy + a0, fx + 2, fy + a1]

        def hb(x, y, b):
            return x - 1 <= b[2] and x + 10 >= b[0] and y - 1 <= b[3] and y + 10 >= b[1]

        def find(ladk):
            for rr in range(0, 25):
                for dy in range(-rr, rr + 1):
                    for dx in range(-rr, rr + 1):
                        if max(abs(dx), abs(dy)) != rr:
                            continue
                        x, y = fx + dx - 4, fy + dy - 4
                        z = standZ(x + 4, y + 4, fz - 1, fz + 1, KEEP_HEAD)
                        off = not ladk or (not hb(x, y, [fx - LAD_KEEP, fy - LAD_KEEP, fx + LAD_KEEP, fy + LAD_KEEP]) and not (lane and hb(x, y, lane)))
                        if z >= 0 and off and clear(x, y, z, ladk):
                            return [x, y, z]
            return None
        spot = find(True) or find(False)
        at = None
        for rr in range(0, 13):
            for dy in range(-rr, rr + 1):
                for dx in range(-rr, rr + 1):
                    if at or max(abs(dx), abs(dy)) != rr:
                        continue
                    x2, y2 = hx + dx, hy + dy
                    z2 = standZ(x2, y2, hz - 1, hz + 1, KEEP_HEAD)
                    if z2 >= 0 and not in_gun(x2, y2, z2):
                        at = [x2 + 0.5, y2 + 0.5, z2]
        kegs = []
        if spot:
            for o in ((0, 0), (5, 0), (0, 5)):
                org = np.array([spot[0] + o[0], spot[1] + o[1], spot[2]], float)
                kegs.append([r3(org), r3(org + KB)])
                keg_boxes.append((org, org + KB))
        kh = 0
        for lo_, hi_ in [(np.array(k[0]), np.array(k[1])) for k in kegs]:
            x0, x1, y0, y1, z0, z1 = box_cells(lo_, hi_)
            kh += int(SX[x0:x1, y0:y1, z0:z1].sum() + box_solid[x0:x1, y0:y1, z0:z1].sum())
        hoist[path] = {'foot': v['points']['foot'], 'head': v['points']['head'], 'decks': v.get('decks'), 'lane': lane, 'spot_9x9': spot,
                       'spot_dist_to_foot': round(math.hypot(spot[0] + 4.5 - (fx + 0.5), spot[1] + 4.5 - (fy + 0.5)), 2) if spot else None,
                       'head_stand': at, 'kegs_box': kegs, 'kegs_box_hits_solid_or_model': kh}

    # ── 走路格（draft_guns.py 的 nav：每層 meta floor、每 2 格一點、頭上 12 格、高差 ≤ 3、8 鄰）：加了這一步的格與外框前後 ──
    DM = {}
    for line in open(os.path.join(HERE, 'decks_meta.tsv'), encoding='utf-8'):
        f_ = line.rstrip('\n').split('\t')
        if len(f_) >= 3 and f_[0] == 'link':
            m_ = json.loads(f_[2])
            if m_.get('kind') == 'deck':
                DM[m_['deck']] = DG.poly(m_['floor'])
    boxes_before = [(a, b) for n_, a, b in gun_box]
    boxes_after = boxes_before + [(np.array(r['bbox'][0]), np.array(r['bbox'][1])) for r in rows if not r.get('door')] + keg_boxes

    def blocked(x, y, z, boxes):
        for lo_, hi_ in boxes:
            if math.floor(lo_[0]) - 1 <= x <= math.ceil(hi_[0]) + 1 and math.floor(lo_[1]) - 1 <= y <= math.ceil(hi_[1]) + 1 and lo_[2] - 3 <= z <= hi_[2]:
                return True
        return False

    def nav(dk, G, boxes):
        Fp = DM[dk]
        NC = DG.NAV_C
        Z = {}
        for x in range(int(Fp[0][0]) // NC * NC, int(Fp[-1][0]) + NC, NC):
            f = DG.polyZ(Fp, x)
            if f is None:
                continue
            for y in range(0, AY, NC):
                z = -1
                for zz in range(f + 3, f - 3, -1):
                    if G[x, y, zz - 1] and not G[x, y, zz:zz + DG.NAV_HEAD].any():
                        z = zz
                        break
                if z < 0 or blocked(x, y, z, boxes):
                    continue
                Z[(x, y)] = z
        comp, sizes = {}, []
        for k in sorted(Z):
            if k in comp:
                continue
            cid = len(sizes)
            comp[k] = cid
            q, n_ = [k], 0
            while q:
                a = q.pop()
                n_ += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    b = (a[0] + dx * NC, a[1] + dy * NC)
                    if b not in Z or b in comp or abs(Z[b] - Z[a]) > DG.NAV_DZ:
                        continue
                    if dx and dy and ((a[0] + dx * NC, a[1]) not in Z or (a[0], a[1] + dy * NC) not in Z):
                        continue
                    comp[b] = cid
                    q.append(b)
            sizes.append(n_)
        big = int(np.argmax(sizes)) if sizes else -1
        return Z, comp, sizes, big

    navr = {}
    for dk in sorted(DM):
        Z0, c0, s0, b0 = nav(dk, S0, boxes_before)
        Z1, c1, s1, b1 = nav(dk, SS, boxes_after)

        def in_main(p, Z=Z1, c=c1, big=b1):
            NC = DG.NAV_C
            k = (int(round(p[0] / NC)) * NC, int(round(p[1] / NC)) * NC)
            cands = [(k[0] + dx, k[1] + dy) for dx in (0, -NC, NC) for dy in (0, -NC, NC)]
            return any(c.get(q) == big for q in cands if q in Z and abs(Z[q] - p[2]) <= DG.NAV_DZ)
        crew_out = [[gn, a] for gn, d_, a in crew_spots if d_ == dk and not in_main(a)]
        lad_out = []
        for nm, L in sorted(LP.items()):
            for pn in ('foot', 'head'):
                p = L['points'][pn]
                if (L['lo'] if pn == 'foot' else L['up']) == dk and not in_main(p):
                    lad_out.append([nm, pn])
        hoist_out = []
        for path, h in hoist.items():
            ln = path.rsplit('/', 1)[1]
            if h['head_stand'] and LP[ln]['up'] == dk and not in_main(h['head_stand']):
                hoist_out.append([ln, 'head_stand'])
        others = []
        for cid, n_ in enumerate(s1):
            if cid == b1:
                continue
            ks = [k for k, v in c1.items() if v == cid]
            others.append([n_, min(k[0] for k in ks), max(k[0] for k in ks), min(k[1] for k in ks), max(k[1] for k in ks)])
        navr[dk] = {'points_before': len(Z0), 'main_before': s0[b0] if s0 else 0, 'points_after': len(Z1), 'main_after': s1[b1] if s1 else 0,
                    'groups_ge12_before': sum(1 for v in s0 if v >= 12), 'groups_ge12_after': sum(1 for v in s1 if v >= 12),
                    'other_groups_after': sorted(others, reverse=True)[:8],
                    'crew_spots_not_in_main': crew_out, 'ladder_points_not_in_main': lad_out, 'hoist_heads_not_in_main': hoist_out}

    # ── 門（Ship_Fittings §9.7）──
    doors = {}
    for r in rows:
        if not r.get('door'):
            continue
        lo, hi = np.array(r['bbox'][0]), np.array(r['bbox'][1])
        if r['door'] == 'hatch':
            ox0, ox1, oy0, oy1 = r['opening']
            fx0, fx1, fy0, fy1 = int(round(lo[0])), int(round(hi[0])) - 1, int(round(lo[1])), int(round(hi[1])) - 1
            Fp = DM[r['host']]
            under_air = [(x, y) for x in range(fx0, fx1 + 1) for y in range(fy0, fy1 + 1) if not S0[x, y, DG.polyZ(Fp, x) - 1]]
            open_cells = [(x, y) for x in range(ox0, ox1 + 1) for y in range(oy0, oy1 + 1)]
            doors[r['name']] = {'box_cells': [fx0, fx1, fy0, fy1, int(round(lo[2])), int(round(hi[2])) - 1], 'margin': [ox0 - fx0, fx1 - ox1, oy0 - fy0, fy1 - oy1],
                                'air_under_in_deck_layer': len(under_air), 'opening_cells': len(open_cells),
                                'opening_all_air': all(not S0[x, y, DG.polyZ(Fp, x) - 1] for x, y in open_cells),
                                'air_under_outside_opening': len(set(under_air) - set(open_cells)), 'rests_on': r['support']}
        else:
            y0, y1 = int(round(lo[1])), int(round(hi[1])) - 1
            z0, z1 = int(round(lo[2])), int(round(hi[2])) - 1
            wx = r['wall_x']
            frame = all(S0[wx, y, z] for y in (y0, y1) for z in range(z0, z1 + 1))
            hole = [(y, z) for y in range(y0, y1 + 1) for z in range(z0, z1 + 1) if not S0[wx, y, z]]
            doors[r['name']] = {'panel_cells': [int(round(lo[0])), y0, y1, z0, z1], 'height': z1 - z0 + 1, 'frame_cols_wall': frame,
                                'hole_cells': len(hole), 'hole_rows': len({z for _, z in hole}), 'hole_y': [min(y for y, _ in hole), max(y for y, _ in hole)] if hole else None,
                                'floor_under': all(S0[int(round(lo[0])), y, z0 - 1] for y in range(y0, y1 + 1)), 'gap_to_wall': int(round(lo[0])) - wx - 1}

    # ── 火藥與明火的距離 ──
    fire = {}
    for r in rows:
        if r['meta'].get('kind') != 'galley':
            continue
        c = (np.array(r['bbox'][0]) + np.array(r['bbox'][1])) / 2
        bx = [(b['name'], np.array(b['at'])) for b in rows if b['host'] == 'magazine'] + [('hoist-keg', (a + b) / 2) for a, b in keg_boxes]
        nm, p = min(bx, key=lambda t: float(np.linalg.norm(t[1][:2] - c[:2])))
        fire[r['name']] = [round(float(np.linalg.norm(p[:2] - c[:2])) / 10, 2), nm]

    for r in rows:
        r.pop('_g')
    fr = sorted(free)
    cen = np.array(fr).mean(axis=0)
    blast = min(fr, key=lambda p: (sum((p[i] - cen[i]) ** 2 for i in range(3)), p))
    door = (door_xs['fore'] if 'fore' in MG['doors'] else door_xs[MG['doors'][0]], YC, F + 1)
    kinds = {}
    for r in rows:
        k = str(r['meta'].get('kind'))
        kinds[k] = kinds.get(k, 0) + 1
    mz = [z for (_, _, z) in free]
    Vv = {'read': {'solid_stand_cells': int(S0.sum()), 'solid_all_cells': int(SA.sum()), 'gun_cells': int(gun_cells.sum()), 'recoil_cells': int(recoil_cells.sum()),
                   'swivel_sweep_cells': int(sweep_cells.sum()), 'crew_spots': len(crew_spots),
                   'component_sha256': {f: hashlib.sha256(open(os.path.join(SRC, f), 'rb').read()).hexdigest()[:16] for f in sorted(os.listdir(SRC))}},
          'magazine': {'cells': len(mag), 'colors': {str(c): sum(1 for q in mag.values() if q == c) for c in sorted(set(mag.values()))}, 'air_inside': len(free),
                       'x': [X0, X1], 'doors': MG['doors'], 'barrels': len(barrels), 'cap': MG['cap'], 'capacity_per_tier': capacity,
                       'tiers': [sum(1 for b in barrels if b['tier'] == t) for t in range(4)], 'rack': len(rack), 'chocks': len(chocks), 'powder_lb': len(barrels) * 100,
                       'blast': list(blast), 'door': list(door), 'x_skipped': [r_['x'] for r_ in mlog if not r_['cells']],
                       'section_y': {str(r_['x']): r_['y'] for r_ in mlog if r_['x'] in (X0, (X0 + X1) // 2, X1)},
                       'vs_waterline': {'floor': F, 'ztop': ZTOP, 'ceiling_z': ZC, 'waterline_z': WL, 'air_z': [min(mz), max(mz)],
                                        'air_rows_below_wl': sum(1 for z in range(min(mz), max(mz) + 1) if z <= WL), 'air_rows_above_wl': sum(1 for z in range(min(mz), max(mz) + 1) if z > WL)}},
          'new_on_solid': len(on_solid), 'sealed': sealed, 'floating': floating,
          'models': len(rows), 'kinds': kinds, 'model_collisions': coll, 'no_foot_within_12': nofoot, 'no_kind': nokind,
          'model_overlap_pairs': len(overlap), 'model_overlap': overlap[:10],
          'gear': {r['name']: {k: r[k] for k in ('at', 'scale', 'bbox', 'foot_gap', 'support', 'rope_clear', 'gun_box_overlap', 'crew_in_box', 'crew_nearest',
                                                  'ladder_pts_in_box', 'rower_zone', 'dy_max') if k in r} for r in rows if r['host'] != 'magazine'},
          'barrels_reach': {'max_cells': max((v for v in reach.values() if v is not None), default=None), 'limit': MG['reach_cells'], 'unreachable': unreachable,
                            'hold_walk_cells_in_room_band': int(len(hw))},
          'barrels_min_rope_clear': min(r['rope_clear'][0] for r in rows if r['host'] == 'magazine') if barrels else None,
          'rower_zone': {'x': list(rz_x), 'dy_min': RZ['dy_min'], 'models_in_zone': [r['name'] for r in rows if r.get('rower_zone')]},
          'cloth': cloth, 'galley_faces': galley, 'fire_to_powder_m': fire, 'hoist': hoist, 'doors': doors, 'nav': navr,
          'walk_fine': {'hold_cells': len(hold_walk), 'main_cells': len(main_walk)},
          'mirror_diff': {'magazine': sum(1 for (x, y, z), c in mag.items() if mag.get((x, 2 * YC - y, z)) != c),
                          'barrels': sum(1 for b in barrels if not any(abs(c['at'][0] - b['at'][0]) < 1e-6 and abs(2 * YC + 1 - c['at'][1] - b['at'][1]) < 1e-6 for c in barrels))}}
    rope_min = GBG['rope_min_cells']
    Vv['problems'] = (len(coll) + len(nofoot) + len(nokind) + len(overlap) + len(sealed and [s for s in sealed if s[0] == 'big']) + len(floating) + len(on_solid)
                      + len(unreachable) + len(Vv['rower_zone']['models_in_zone'])
                      + sum(1 for r in rows if r['rope_clear'] and r['rope_clear'][0] < rope_min) + sum(1 for r in rows if r['crew_in_box'])
                      + sum(1 for v in (cloth.get('by_model') or {}).values() if v[0] < 1.0)
                      + sum(1 for v in galley.values() if not any(v.values()))
                      + sum(1 for h in hoist.values() if not h['spot_9x9'] or not h['head_stand'] or h['kegs_box_hits_solid_or_model'])
                      + sum(len(v['crew_spots_not_in_main']) + len(v['ladder_points_not_in_main']) + len(v['hoist_heads_not_in_main']) + max(0, v['groups_ge12_after'] - 1) for v in navr.values())
                      + Vv['mirror_diff']['magazine'] + Vv['mirror_diff']['barrels'] + (len(barrels) < MG['cap']))
    if probe:
        out = {'probe': probe, 'problems': Vv['problems'], 'model_collisions': coll, 'no_kind': nokind, 'overlap': overlap[:5],
               'magazine': {k: Vv['magazine'][k] for k in ('barrels', 'tiers', 'capacity_per_tier', 'rack', 'chocks', 'cells')},
               'hoist': {k: [v['spot_9x9'], v['kegs_box_hits_solid_or_model'], v['head_stand']] for k, v in hoist.items()},
               'nav': {k: [v['groups_ge12_after'], v['other_groups_after'][:3], len(v['crew_spots_not_in_main'])] for k, v in navr.items()},
               'barrels_reach': Vv['barrels_reach'],
               'doors': {k: {q: v[q] for q in ('margin', 'air_under_outside_opening', 'frame_cols_wall', 'hole_cells', 'gap_to_wall') if q in v} for k, v in doors.items()}}
        print(json.dumps(out, ensure_ascii=False))
        return
    od = os.path.join(HERE, 'masks', 'gear')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'magazine.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 利劍號 彈藥庫（世界座標、at 0,0,0；draft_gear.py 產生；子作品 %s）\n' % MG['work'])
        for (x, y, z), c in sorted(mag.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    Vv['lists'] = {'magazine': [len(mag), hashlib.sha256(open(p, 'rb').read()).hexdigest()]}
    place = {'note': 'draft_gear.py 的結果；模型 at ＝ pivot 落點（世界座標；host 子作品都在 0,0,0）；桶掛在彈藥庫子作品',
             'magazine': {'work': MG['work'], 'title': MG['title'], 'link': MG['link'], 'anchors': {'blast': list(blast), 'door': list(door)},
                          'meta': {'kind': 'magazine', 'pos': MG['pos'], 'powder_lb': len(barrels) * 100, 'hoist': MG['hoist']}},
             'deck_works': GB['deck_works'],
             'models': [{k: v for k, v in r.items() if k not in ('foot_gap', 'support', 'rope_clear', 'gun_box_overlap', 'crew_in_box', 'crew_nearest',
                                                                 'ladder_pts_in_box', 'rower_zone', 'dy_max')} for r in rows]}
    json.dump(place, open(os.path.join(HERE, 'gear_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(Vv, open(os.path.join(HERE, 'verify_gear.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    sheet(plan, SA, mag, rows, barrels, R, MG, YC, hoist, gun_box, crew_spots, rz_x, RZ)
    print(json.dumps({k: Vv[k] for k in Vv if k not in ('gear', 'read', 'lists', 'cloth')}, ensure_ascii=False))
    print(json.dumps(Vv['gear'], ensure_ascii=False))


def sheet(plan, SA, mag, rows, barrels, R, MG, YC, hoist, gun_box, crew_spots, rz_x, RZ):
    """圖紙 08：(a) 底艙 z floor+3 切面：彈藥庫與桶；(b) 彈藥庫橫剖面（x 中間）；(c) 主甲板與後甲板俯視：模型外框、砲外框、砲手、槳手區、hoist 桶。"""
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    except OSError:
        f = ImageFont.load_default()
    s = 3
    W_, H_ = 40 + 340 * s + 40, 60 + 70 * s + 60 + 30 * s + 60 + 100 * s + 100
    im = Image.new('RGB', (W_, H_), (250, 248, 242))
    d = ImageDraw.Draw(im)
    d.text((20, 12), '%s - new sheet 08: magazine and deck gear (TASK-0022 step 10; draft_gear.py)' % plan['title_en'], fill=(0, 0, 0), font=f)
    X0, X1, F = MG['x0'], MG['x1'], MG['floor']
    # (a) 底艙平台 x 130–200 俯視切面 z F+3
    zs = F + 3
    oy = 50
    xr, yr = (130, 200), (95, 166)
    d.text((40, oy - 18), '(a) hold, slice z %d: magazine x %d-%d (copper/oak/pine), %d barrels (red circles), hoist kegs (blue)' % (zs, X0, X1, len(barrels)), fill=(0, 0, 0), font=f)
    for x in range(*xr):
        for y in range(*yr):
            c = None
            if (x, y, zs) in mag:
                c = palette_rgb(mag[(x, y, zs)])
            elif (x, y, F) in mag:
                c = palette_rgb(mag[(x, y, F)])
            elif SA[x, y, zs]:
                c = (120, 120, 120)
            if c:
                px, py = 40 + (x - xr[0]) * s * 2, oy + (yr[1] - 1 - y) * s
                d.rectangle([px, py, px + 2 * s - 1, py + s - 1], fill=c)
    for b in barrels:
        px, py = 40 + (b['at'][0] - xr[0]) * s * 2, oy + (yr[1] - b['at'][1]) * s
        d.ellipse([px - R * s * 2, py - R * s, px + R * s * 2, py + R * s], outline=(170, 20, 20), width=2)
    for path, h in hoist.items():
        for lo, hi in h['kegs_box']:
            if lo[2] < 30 and xr[0] <= lo[0] < xr[1]:
                d.rectangle([40 + (lo[0] - xr[0]) * s * 2, oy + (yr[1] - hi[1]) * s, 40 + (hi[0] - xr[0]) * s * 2, oy + (yr[1] - lo[1]) * s], outline=(30, 60, 200), width=2)
    # (b) 橫剖面 x 中間
    xm = (X0 + X1) // 2
    oy2 = oy + 70 * s + 40
    d.text((40, oy2 - 18), '(b) section x %d (looking forward): room z %d-%d under waterline z %d, ceiling z %d' % (xm, F + 1, MG['ztop'], plan['waterline']['z'], MG['ztop'] + 1), fill=(0, 0, 0), font=f)
    for y in range(95, 166):
        for z in range(8, 38):
            c = palette_rgb(mag[(xm, y, z)]) if (xm, y, z) in mag else ((120, 120, 120) if SA[xm, y, z] else None)
            if c:
                px, py = 40 + (y - 95) * s, oy2 + (37 - z) * s
                d.rectangle([px, py, px + s - 1, py + s - 1], fill=c)
    wl = plan['waterline']['z']
    d.line([40, oy2 + (37 - wl) * s, 40 + 71 * s, oy2 + (37 - wl) * s], fill=(0, 120, 220), width=1)
    # (c) 主甲板／後甲板俯視
    oy3 = oy2 + 30 * s + 50
    sc = 2
    d.text((40, oy3 - 18), '(c) main and quarter deck from above: gear boxes (orange), guns (grey), gun crew (blue dots), rower zone (green, step-13 assumption)', fill=(0, 0, 0), font=f)
    X = lambda x: 40 + (x - 60) * sc
    Y = lambda y: oy3 + (y - 70) * sc * 1.6
    d.rectangle([X(60), Y(70), X(470), Y(191)], outline=(180, 180, 180))
    for y0, y1 in ((70, YC + 0.5 - RZ['dy_min']), (YC + 0.5 + RZ['dy_min'], 191)):
        d.rectangle([X(rz_x[0]), Y(y0), X(rz_x[1]), Y(y1)], outline=(60, 160, 60), width=1)
    for n_, a, b in gun_box:
        if a[2] < 80:
            d.rectangle([X(a[0]), Y(a[1]), X(b[0]), Y(b[1])], outline=(110, 110, 110), width=1)
    for gn, dk, a in crew_spots:
        d.ellipse([X(a[0]) - 2, Y(a[1]) - 2, X(a[0]) + 2, Y(a[1]) + 2], fill=(40, 60, 200))
    for r in rows:
        if r['host'] == 'magazine':
            continue
        lo, hi = r['bbox']
        d.rectangle([X(lo[0]), Y(lo[1]), X(hi[0]), Y(hi[1])], outline=(220, 110, 0), width=2)
        d.text((X(lo[0]), Y(hi[1]) + 2), r['work'].split('-01m-')[-1], fill=(150, 70, 0), font=f)
    for path, h in hoist.items():
        for lo, hi in h['kegs_box']:
            if lo[2] >= 30:
                d.rectangle([X(lo[0]), Y(lo[1]), X(hi[0]), Y(hi[1])], outline=(30, 60, 200), width=2)
    d.text((40, H_ - 30), 'hoist ladders: ' + ', '.join(p.rsplit('/', 1)[1] for p in MG['hoist'].split(',')) + '   |   magazine %d barrels = %d lb, pos=%s' % (len(barrels), len(barrels) * 100, MG['pos']),
           fill=(0, 0, 0), font=f)
    im.save(os.path.join(HERE, 'sheet08_gear_v1.png'), optimize=False)


if __name__ == '__main__':
    main()
