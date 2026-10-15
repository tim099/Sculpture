# 夜燈號 船頭（鬼盜船化，2026-10-15；Tim：「船頭 船尾的建築&弧線可以參考鬼盜船」「船頭加上朝正前的炮」
#   「做船頭（追擊砲、head rails、前牆、錨）」；劇照（前甲板前面一片淺色格子鑲板）與模型照（head rails 的弧線、船頭掛錨）只看不收）
#   船殼、前甲板、欄杆、上甲板各自的 list 匯出 ＋ 組裝件 list ＋ 共用錨 list ⇒
#   masks/bow/<作品>.add.vox.txt、<作品>.carve.vox.txt（各作品自己的座標 ＝ 船殼座標，關聯都在 0,0,0）、bow_placement.json（砲、錨、固定點）、verify_bow.json
# 用法：python -I draft_bow.py <design 資料夾> <scratch 資料夾（hull2／deck-spar／rails／deck-upper／asm2／anchor .list.txt）>
# 內容：
#   · beakhead：X ≥ 577、Z ≥ 120 的圓船頭截掉（船殼、前甲板、欄杆三件；中線 ±3 的船頭柱留著），在 X 574–576 立一道平的前牆（Z 120–144），
#     前牆下半兩片格子鑲板（劇照讀圖；顏色淺）、頂上一道窗框色的壓條；牆前 Z 119 鋪一片格柵當 head 平台。
#   · head rails：每舷上下兩道，沿 head 平台外緣（船殼輪廓外一格）彎到船頭柱、再往前彎到船首像 knee 兩側（弧線：中段往下沉、到 knee 再抬）；
#     兩道之間三根 head timber。（模型照讀圖；形狀是設計）
#   · 追擊砲：上甲板兩門 18 磅長砲（共用元件 -gun-long18、scale 0.5、meta gun=18chase），朝正前，從 head 平台底下船頭兩個砲門伸出去。
#     ⚠ 前甲板的舷牆只到 Z 137–141，砲放前甲板砲口會高過前牆 ⇒ 放上甲板（跟憲法號的船頭砲門同一種）。
#   · cathead＋錨：兩舷各一根 cathead（往外往前），共用錨（basecamp-frigate-constitution-01m-anchor、kind=anchor、anchor=bower）縮 0.85 掛在端下；
#     船殼登記 hawse-S／P（錨鏈孔，鐵鍊從船殼出來的地方）。錨不碰船殼的最短 cathead 用搜的。
import sys, os, json, math
import numpy as np

BLACK, TRIM, OAK, DARK, LIGHT = 36, 73, 136, 104, 182      # #242400、#494955、#929255? 見 notes；LIGHT #B6B6AA（格子鑲板）
YC = 160                                                   # 鏡像 y' ＝ 320 − y
CUT_X0, CUT_Z0 = 577, 120
STEM_KEEP = 3                                              # 中線 ±3 的船殼（船頭柱）不截
BULK_X = (574, 577)                                        # v1 只到 576 ⇒ 遇到別件作品的格就跳過，截口露出內襯（淺色直條）與前甲板切邊（橫木色線）
                                                           # ⇒ v2 多貼一層 X 577（已截空），寬照 X 576 那一欄，整面蓋住
BULK_Z = (120, 144)
PLAT_Z = 119
PANELS = [((141, 153), (122, 131))]                        # 左舷那片（右舷鏡像）
PORT_Y = (140, 148)                                        # 追擊砲門（左舷；右舷鏡像）
PORT_Z = (110, 118)
GUN = dict(work='basecamp-frigate-constitution-01m-gun-long18', scale=0.5, pivot=[13.5, 33.0, 0.0],
           muzzle_y=61.5, breech_y=7.5, axis_z=21.5, half_len=33.0, half_w=13.5, meta={'kind': 'gun', 'gun': '18chase'})
ANCHOR = dict(work='basecamp-frigate-constitution-01m-anchor', scale=0.85, ring=[23.5, 16.5, 56.5],
              meta={'kind': 'anchor', 'anchor': 'bower'})
CAT = dict(x=566, z=(135, 137), fwd_per_out=0.35)          # cathead 根部 X、高度（X 566 船殼頂 Z 137）、每往外 1 格往前幾格
KNEE_Y = (157, 163)                                        # 船首像 knee 的寬（世界 y）


def load(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def as_set(a):
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def main(design, scratch):
    L = lambda n: as_set(load(os.path.join(scratch, n + '.list.txt')))
    hull, spar, rails, upper, asm = L('hull2'), L('deck-spar'), L('rails'), L('deck-upper'), L('asm2')
    anchor = load(os.path.join(scratch, 'anchor.list.txt'))
    occ = set(asm)
    adds = {'hull': {}, 'deck-spar': {}, 'rails': {}}
    carves = {'hull': {}, 'deck-spar': {}, 'rails': {}}
    st = {}

    def mirror(p):
        return (p[0], 2 * YC - p[1], p[2])

    # ── 截掉圓船頭 ──
    for name, cells in (('hull', hull), ('deck-spar', spar), ('rails', rails)):
        for p, c in cells.items():
            if p[0] >= CUT_X0 and p[2] >= CUT_Z0 and not (name == 'hull' and abs(p[1] - YC) <= STEM_KEEP):
                carves[name][p] = c
    gone = set().union(*[set(v) for v in carves.values()])
    free = lambda p: p not in occ or p in gone
    st['cut'] = {k: len(v) for k, v in carves.items()}

    def side_y(x, z, cells=hull):
        ys = [p[1] for p in cells if p[0] == x and p[2] == z]
        return (min(ys), max(ys)) if ys else None

    hull_xz = {}
    for (x, y, z) in hull:
        k = (x, z)
        lo, hi = hull_xz.get(k, (999, -1))
        hull_xz[k] = (min(lo, y), max(hi, y))

    # ── 前牆 ──
    H = adds['hull']
    for z in range(BULK_Z[0], BULK_Z[1] + 1):
        for x in range(BULK_X[0], BULK_X[1] + 1):
            sy = hull_xz.get((min(x, CUT_X0 - 1), min(z, 139)))
            assert sy, ('前牆那一格沒有船殼', x, z)
            for y in range(sy[0], sy[1] + 1):
                p = (x, y, z)
                if free(p) or p in hull:
                    if p in hull and p not in gone:
                        continue
                    H[p] = TRIM if z == BULK_Z[1] else BLACK
    st['bulkhead'] = len(H)
    # 格子鑲板：牆外表面（X 576）刻成格子 ⇒ 格線淺色、格眼刻空露出 X 575 那層黑
    panel = 0
    for (ya, yb), (za, zb) in PANELS:
        for y0 in range(ya, yb + 1):
            for z in range(za, zb + 1):
                for y in (y0, 2 * YC - y0):
                    p = (BULK_X[1], y, z)
                    edge = y0 in (ya, yb) or z in (za, zb)
                    line = (y0 - ya) % 3 == 0 or (z - za) % 3 == 0
                    if edge:
                        H[(BULK_X[1] + 1, y, z)] = TRIM                  # 外框凸一格
                        H[p] = TRIM
                    elif line:
                        H[p] = LIGHT
                    else:
                        H.pop(p, None)                                   # 格眼：空
                    panel += 1
    st['panel_cells'] = panel
    # ── head 平台（格柵）──
    plat = 0
    for x in range(BULK_X[1] + 1, 600):
        sy = hull_xz.get((x, PLAT_Z))
        if not sy:
            continue
        for y in range(sy[0], sy[1] + 1):
            p = (x, y, PLAT_Z)
            if p in hull:
                continue
            if not free(p):
                continue
            if x % 3 == 0 or (y - YC) % 3 == 0:
                H[p] = OAK
                plat += 1
    st['platform'] = plat
    # ── 追擊砲門：船頭（Z 110–118）刻穿到裡面的空氣 ──
    port_carve = 0
    for y0 in range(PORT_Y[0], PORT_Y[1] + 1):
        for z in range(PORT_Z[0], PORT_Z[1] + 1):
            for y in (y0, 2 * YC - y0):
                xs = [x for x in range(560, 600) if (x, y, z) in hull]
                if not xs:
                    continue
                x = max(xs)                                              # 外表面
                while (x, y, z) in hull and x > 560:
                    carves['hull'][(x, y, z)] = hull[(x, y, z)]
                    port_carve += 1
                    x -= 1
    st['port_carve'] = port_carve
    gone = set().union(*[set(v) for v in carves.values()])
    # 砲門外框（窗框色，外表面往外一格）
    for y0 in range(PORT_Y[0] - 1, PORT_Y[1] + 2):
        for z in range(PORT_Z[0] - 1, PORT_Z[1] + 2):
            if PORT_Y[0] <= y0 <= PORT_Y[1] and PORT_Z[0] <= z <= PORT_Z[1]:
                continue
            for y in (y0, 2 * YC - y0):
                xs = [x for x in range(560, 600) if (x, y, z) in hull and (x, y, z) not in gone]
                if xs:
                    H[(max(xs) + 1, y, z)] = TRIM
    # ── 砲（模型，上甲板）──
    guns = []
    for sgn, name in ((-1, '追擊砲-P'), (1, '追擊砲-S')):
        yc = (PORT_Y[0] + PORT_Y[1]) / 2 + 0.5
        if sgn > 0:
            yc = 2 * YC - (PORT_Y[0] + PORT_Y[1]) / 2 + 0.5
        yi = int(yc)
        floor = max(z for (x, y, z) in upper if x == 571 and y == yi) + 1
        zc_port = (PORT_Z[0] + PORT_Z[1]) / 2 + 0.5
        floor_needed = zc_port - GUN['axis_z'] * GUN['scale']
        zf = max(floor, floor_needed)                                     # 砲軸對準砲門中線；比甲板高 ⇒ 墊木（下面加格）
        outer = max(x for x in range(560, 600) if (x, yi, int(zc_port)) in hull)
        at_x = outer + 1.5 - (GUN['muzzle_y'] - GUN['pivot'][1]) * GUN['scale']
        guns.append(dict(name=name, at=[round(at_x, 3), yc, round(zf, 3)], floor=floor, outer=outer))
    st['guns'] = guns
    # 墊木：砲架底下到甲板之間（上甲板作品裡；寬 = 砲寬、長 = 砲長）
    adds['deck-upper'] = {}
    for g in guns:
        if g['at'][2] > g['floor']:
            hx = GUN['half_len'] * GUN['scale']
            hw = GUN['half_w'] * GUN['scale'] / 2
            for x in range(int(g['at'][0] - hx * 0.6), int(g['at'][0] + hx * 0.6) + 1):
                for y in range(int(g['at'][1] - hw), int(g['at'][1] + hw) + 1):
                    for z in range(g['floor'], int(math.floor(g['at'][2]))):
                        if (x, y, z) not in occ:
                            adds['deck-upper'][(x, y, z)] = OAK
    # 砲的外框有沒有撞到東西（刻掉的除外）
    hit = 0
    for g in guns:
        hx, hw = GUN['half_len'] * GUN['scale'], GUN['half_w'] * GUN['scale'] / 2
        for x in range(int(g['at'][0] - hx + 1), int(g['at'][0] + hx)):
            for y in range(int(g['at'][1] - hw + 1), int(g['at'][1] + hw)):
                for z in range(int(g['at'][2]) + 1, int(g['at'][2] + 13)):
                    p = (x, y, z)
                    if p in occ and p not in gone:
                        hit += 1
    st['gun_bbox_hits_rough'] = hit          # 粗估的長方外框（比砲大很多）—— 真的砲格轉到世界座標逐格對是 0（notes 階段十九 船頭）
    # ── head rails ──
    rails_cells = head_rails(hull_xz, occ, gone, H)
    st['head_rails'] = rails_cells
    # ── cathead＋錨 ──
    cat, anchors_pl = catheads(hull_xz, occ, gone, H, anchor)
    st['cathead'] = cat
    st['anchors'] = anchors_pl
    # hawse：船殼外表面、追擊砲門外側下方
    hawse = {}
    for sgn, nm in ((-1, 'hawse-P'), (1, 'hawse-S')):
        z = 108
        y = int(YC + sgn * 17)
        xs = [x for x in range(560, 600) if (x, y, z) in hull]
        hawse[nm] = [max(xs), y, z]
    st['hawse'] = hawse
    # 對稱
    for k in ('hull',):
        st['asym_' + k] = sum(1 for p, c in adds[k].items() if adds[k].get(mirror(p)) != c)
        st['asym_carve_' + k] = sum(1 for p in carves[k] if mirror(p) not in carves[k])
    # 新格不能落在別件作品現有的格上（自己作品裡被刻掉的除外）
    for k, a in adds.items():
        bad = [p for p in a if p in occ and p not in gone]
        st['overlap_' + k] = len(bad)
        assert not bad, ('落在現有的格上', k, bad[:5])
    write(design, adds, carves, guns, anchors_pl, hawse, st)


def bez(p0, p1, p2, p3, n=200):
    out = []
    for i in range(n + 1):
        t = i / n
        a = [(1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3]
        out.append(tuple(sum(a[k] * P[j] for k, P in enumerate((p0, p1, p2, p3))) for j in range(3)))
    return out


def head_rails(hull_xz, occ, gone, H):
    """右舷算、鏡像到左舷。每道欄 2×2，頂那一排窗框色。"""
    n = 0
    specs = {'upper': dict(z0=138, zmid=125, z1=123, xk=631), 'lower': dict(z0=127, zmid=111, z1=109, xk=627)}
    paths = {}
    for nm, s in specs.items():
        sy0 = hull_xz[(CUT_X0 - 1, min(s['z0'], 139))][1] + 1
        p0 = (BULK_X[1] + 1, sy0, s['z0'])
        p3 = (s['xk'], KNEE_Y[1] + 1.5, s['z1'])
        p1 = (BULK_X[1] + 15, sy0 - 4, s['zmid'] + 4)
        p2 = (s['xk'] - 18, KNEE_Y[1] + 8, s['zmid'] - 2)
        pts = []
        for (x, y, z) in bez(p0, p1, p2, p3):
            xi, zi = int(round(x)), int(round(z))
            # 船殼還在的那幾格（Z < 120 的船頭）⇒ 往外推到船殼外一格
            sy = hull_xz.get((xi, zi))
            if sy and zi < CUT_Z0:
                y = max(y, sy[1] + 1.5)
            pts.append((x, y, z))
        paths[nm] = pts
        for (x, y, z) in pts:
            for dy in (0, 1):
                for dz in (0, 1):
                    p = (int(round(x)), int(math.floor(y)) + dy, int(round(z)) + dz)
                    if p in occ and p not in gone:
                        continue
                    c = TRIM if dz == 1 else BLACK
                    if H.get(p) != c:
                        H[p] = c
                        H[(p[0], 2 * YC - p[1], p[2])] = c
                        n += 1
    # head timbers：上下兩道之間，三根
    for xt in (588, 602, 616):
        u = min(paths['upper'], key=lambda q: abs(q[0] - xt))
        l = min(paths['lower'], key=lambda q: abs(q[0] - xt))
        for z in range(int(round(l[2])) + 2, int(round(u[2]))):
            y = (u[1] + l[1]) / 2
            for p in ((int(round(xt)), int(math.floor(y)), z), (int(round(xt)), int(math.floor(y)) + 1, z)):
                if p in occ and p not in gone:
                    continue
                H[p] = BLACK
                H[(p[0], 2 * YC - p[1], p[2])] = BLACK
                n += 1
    return n


def catheads(hull_xz, occ, gone, H, anchor):
    """右舷算、鏡像。cathead 從舷外一格往外（＋往前），3×3；錨 ring 點掛在端下；找錨不碰任何格（離 ≥ 1）的最短長度。"""
    s = ANCHOR['scale']
    ring = np.array(ANCHOR['ring'])
    cells = anchor[:, :3].astype(float) + 0.5
    x0 = CAT['x']
    zlo, zhi = CAT['z']
    side = hull_xz[(x0, zhi)][1] + 1
    solid = {p for p in occ if p not in gone}
    for length in range(8, 40):
        xe = x0 + length * CAT['fwd_per_out']
        ye = side + length
        at = np.array([xe, ye + 0.5, zlo - 0.5])                      # ring 點在 cathead 端的正下方
        w = (cells - ring) * s + at
        pts = {tuple(np.floor(q).astype(int)) for q in w}
        near = any((p[0] + dx, p[1] + dy, p[2] + dz) in solid for p in pts for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1))
        if not near:
            break
    else:
        raise SystemExit('cathead 40 格內找不到錨不碰的位置')
    n = 0
    for k in range(0, length + 1):
        xc, yc = x0 + k * CAT['fwd_per_out'], side + k
        for dx in (-1, 0, 1):
            for z in range(zlo, zhi + 1):
                p = (int(round(xc)) + dx, int(yc), z)
                if p in solid:
                    continue
                c = TRIM if k == length else BLACK
                H[p] = c
                H[(p[0], 2 * YC - p[1], p[2])] = c
                n += 1
    zmin = float(w[:, 2].min())
    pl = [dict(name='錨-S', at=[round(float(at[0]), 3), round(float(at[1]), 3), round(float(at[2]), 3)], mirror=False),
          dict(name='錨-P', at=[round(float(at[0]), 3), round(2 * YC + 1 - float(at[1]), 3), round(float(at[2]), 3)], mirror=False)]   # 錨本身左右對稱（verify_anchors asym 0）⇒ 不鏡像，只移到對面
    return dict(cells=n, length=length, side=side, anchor_bottom_z=round(zmin, 2)), pl


def write(design, adds, carves, guns, anchors_pl, hawse, st):
    out = os.path.join(design, 'masks', 'bow')
    os.makedirs(out, exist_ok=True)
    for k in set(adds) | set(carves):
        a, c = adds.get(k, {}), carves.get(k, {})
        if a:
            with open(os.path.join(out, k + '.add.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
                f.write('# 夜燈號 船頭 %s 要加的格：%d 格（船殼座標）\n' % (k, len(a)))
                for (x, y, z), v in sorted(a.items()):
                    f.write('%d,%d,%d,%d\n' % (x, y, z, v))
        if c:
            with open(os.path.join(out, k + '.carve.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
                f.write('# 夜燈號 船頭 %s 要刻掉的格：%d 格（船殼座標，帶現在的顏色）\n' % (k, len(c)))
                for (x, y, z), v in sorted(c.items()):
                    f.write('%d,%d,%d,%d\n' % (x, y, z, v))
        st.setdefault('files', {})[k] = dict(add=len(a), carve=len(c))
    json.dump(dict(gun=GUN, guns=guns, anchor=ANCHOR, anchors=anchors_pl, hawse=hawse), open(os.path.join(design, 'bow_placement.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    json.dump(st, open(os.path.join(design, 'verify_bow.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(st, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1], sys.argv[2])
