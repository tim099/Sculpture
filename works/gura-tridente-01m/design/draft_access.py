# 三叉戟號 TASK-1257（Tim 2026-11-07）：
#   「參考憲法號 把三叉戟號的玻璃替換成透明材質吧」「同時加上通往貨艙的梯子吧」「貨艙 火藥庫目前都走不到」
#   「參考收穫號 加上通往船頭的門(以及把其他門洞加上門)」「船尾的欄杆區域 也可以加門出去」
# 讀組裝件現況（落格之前），一次算出：
#   ① 玻璃：船殼船尾窗的玻璃 87（漆在牆裡、後面實心）與 quarter gallery 的窗 ⇒ 從原作品拿出來、另做一件子作品（關聯 meta material=glass），
#      後面刻穿到艙裡；船尾面是斜的（一扇窗跨兩個 x）⇒ 相鄰兩柱玻璃深度不同的地方，淺的那一柱往後補到深的那一格（整片 6 連通，Ship_Materials「窗的玻璃」）。
#      gallery 原本是實心 ⇒ 每一層掏成一間小艙（外殼留 3 格、z ＝ 那一層甲板站高起 17 格），往裡打通船殼舷側接到船艙；船殼那一舷的刻法鏡到另一舷。
#   ② 船尾三層陽台（中、上砲甲板、上甲板）正中那扇窗改成門洞（寬 7 ＝ 窗寬、高 17）＋金框往下接到地板。
#   ③ 船頭：圓船頭兩舷 y 190／210 各開一個門洞（寬 5、z 149–162，門檻 ＝ 格柵平台面），門裡墊兩階接上砲甲板（站 142 → 145 → 147 → 149）。
#   ④ 貨艙：兩間彈藥庫之間（x 297–561）鋪一層平台（地板 z 30 ＝ 彈藥庫地板、橫樑每 16 格）＝ 新的一層甲板「貨艙」（level −1）；
#      梯子：orlop → 平台兩座（主艙口 rise 3／run 2、後艙口陡梯 run 1；圍欄在梯頭那一段開口）、平台 → 艙底一座（平台開梯口、梯腳墊一塊平地）。
#   ⑤ 門（kind=door，門板引用藍鯊號 gura-pinas-01m-door，照收穫號）：船頭 2、船尾陽台 3、poop 前艙壁 2、彈藥庫 2、orlop 艙房 11（鏡像那一舷跟著翻）。
# 用法：python -I -X utf8 draft_access.py <design>
#   ⇒ masks/access/*.vox.txt、access_placement.json、verify_access.json
import sys, os, json, subprocess, tempfile, hashlib
from collections import Counter, defaultdict
import numpy as np
from scipy import ndimage

D = os.path.abspath(sys.argv[1])
OUT = os.path.join(D, 'masks', 'access')
YC = 200
NX, NY, NZ = 1100, 400, 260
MIR = lambda y: 2 * YC - y
GAL, GAL_AT, GAL_SIZE = 'gura-tridente-01m-quarter-gallery', (62, 241, 99), (62, 34, 102)
GAL_P_AT = (62, 126, 99)
GLASS, GOLD, PLANK, BEAM = 87, 248, 177, 136
DOOR_WORK, DOOR_SIZE, DOOR_PIVOT = 'gura-pinas-01m-door', (2, 14, 32), (1, 7, 0)
ROWS = {'middle': (117, (121, 129)), 'upper': (140, (144, 152)), 'spar': (163, (167, 175)), 'poop': (186, (189, 196))}   # 站高、那一列窗的 z
DOOR_ROWS = ('middle', 'upper', 'spar')            # 有陽台的三層
STERN_IN = {'middle': 91, 'upper': 87, 'spar': 83}  # 那一列船尾窗玻璃的 x（87／83／79）＋ 4 ＝ 船尾牆內面以前
ROOM_H = 17
DOOR_TOP = 14                                       # 陽台門洞 z 站高 … 站高＋14（再高撞到上一層陽台底下的托架）


INPUTS = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--inputs=')), None)


def export(work, links=True):
    """作品現況；--inputs=<資料夾> ⇒ 讀那裡的 <作品ID>.txt（落格之前的匯出快照：重算時用，sha256 記在 verify 的 inputs）。"""
    if INPUTS:
        f = os.path.join(INPUTS, work + '.txt')
        return np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8'), hashlib.sha256(open(f, 'rb').read()).hexdigest()
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        a = ['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out]
        if not links:
            a += ['--arg', 'links=none']
        r = subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode or not os.path.exists(out):
            raise SystemExit('匯出失敗 %s：%s' % (work, (r.stdout + r.stderr)[-600:]))
        sha = hashlib.sha256(open(out, 'rb').read()).hexdigest()
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8'), sha


def grid(a, val=None):
    a = a[(a[:, 2] < NZ)]
    m = np.zeros((NX, NY, NZ), np.uint8)
    m[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3] if val is None else val
    return m


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    R = {'task': 'TASK-1257', 'inputs': {}, 'problems': []}
    P = R['problems']
    A, R['inputs']['assembly'] = export('gura-tridente-01m-assembly')
    H, R['inputs']['hull'] = export('gura-tridente-01m', False)
    G, R['inputs']['gallery'] = export(GAL, False)
    occ = grid(A)                               # 組裝件：顏色（0 ＝ 空）
    hull = grid(H)
    galw = np.zeros((NX, NY, NZ), np.uint8)     # gallery 的格（世界座標，兩舷）
    for g in G:
        x, y, z = g[0] + GAL_AT[0], g[1] + GAL_AT[1], g[2] + GAL_AT[2]
        galw[x, y, z] = g[3]
        galw[x, MIR(y), z] = g[3]               # P 舷 at 62,126 mirror=y：126 + (33 − ly) ＝ 400 − (241 + ly)
    deck_cells = {}
    for k in ('orlop', 'upper', 'poop'):
        a, R['inputs']['deck-' + k] = export('gura-tridente-01m-deck-' + k, False)
        deck_cells[k] = a
    air = occ == 0
    carve_h, carve_g = {}, {}                   # 刻：船殼（世界）、gallery（S 舷世界座標 ⇒ 輸出時轉成 gallery 自己的座標）
    paint_h = {}
    glass = {}
    pieces = []                                 # 每一片窗：(玻璃格, 往裡的軸, 往裡的正負) —— 封水檢查用

    def cut(x, y, z, why, mirror_hull=False):
        if hull[x, y, z]:
            carve_h[(x, y, z)] = int(hull[x, y, z])
            if mirror_hull:
                ym = MIR(y)
                if hull[x, ym, z] != hull[x, y, z]:
                    P.append('%s：船殼鏡像那格不同 (%d,%d,%d)' % (why, x, ym, z))
                carve_h[(x, ym, z)] = int(hull[x, ym, z])
                air[x, ym, z] = True
        elif galw[x, y, z]:
            if y > YC:
                carve_g[(x, y, z)] = int(galw[x, y, z])
        else:
            P.append('%s：(%d,%d,%d) 不是船殼也不是 gallery（色 %d）' % (why, x, y, z, occ[x, y, z]))
            return False
        air[x, y, z] = True
        return True

    # ── ① gallery 每一層掏成小艙（S 舷算、船殼那幾格鏡到 P 舷）──
    room_n = {}
    for row in DOOR_ROWS:
        st = ROWS[row][0]
        n0 = len(carve_h) + len(carve_g)
        for z in range(st, st + ROOM_H):
            x0, x1, y0, y1 = 60, 125, 230, 279
            sol = ~air[x0:x1, y0:y1, z]
            # 船外 ＝ 這一層平面上「船艙以外」的空氣（船艙 ＝ 從 (100, 235) 灌得到的那一塊）
            #   🩸 v1 從框的兩個邊灌 ⇒ 陽台欄杆把陽台圍起來、陽台的空氣不算船外 ⇒ gallery 靠陽台那一面被當成內部掏掉（中層小艙開口到陽台）
            #   🩸 v2 船艙不限範圍 ⇒ 中、上兩層的船尾砲門（三叉戟砲）把船艙接到陽台，整個平面都算船艙、船外是空的 ⇒ 那兩層一格都沒掏
            #   ⇒ 船艙只在船尾牆內面以前（x ≥ STERN_IN）灌
            seed = np.zeros_like(sol)
            seed[100 - x0, 235 - y0] = True
            fwd = (np.arange(x0, x1) >= STERN_IN[row])[:, None]
            cabin = ndimage.binary_propagation(seed, mask=~sol & fwd)
            outside = ~sol & ~cabin
            dist = ndimage.distance_transform_cdt(~outside, metric='taxicab')
            for xi, yi in np.argwhere(sol & (dist >= 4)):
                x, y = xi + x0, yi + y0
                if x < 68 or x > 121 or occ[x, y, z] == GLASS:
                    continue
                if not (galw[x, y, z] or (hull[x, y, z] and x >= STERN_IN[row])):
                    continue                    # 船殼只掏船尾牆內側以前的舷側（船尾牆、轉角留著）
                cut(x, y, z, 'gallery 小艙', mirror_hull=True)
        room_n[row] = len(carve_h) + len(carve_g) - n0
    for (x, y, z) in list(carve_g):
        air[x, MIR(y), z] = True                # gallery 是同一件作品鏡像：S 舷刻一次，P 舷也空了
    R['gallery_room_cells'] = room_n

    # ── ② 船尾窗、gallery 窗：玻璃整片 6 連通、後面刻穿 ──
    def sheet(cells, why):
        """cells：一扇窗的玻璃格（世界）。回傳 (玻璃格, 往裡的軸, 往裡的正負)。"""
        votes = Counter()
        for (x, y, z) in cells:
            for ax in range(3):
                for sg in (-1, 1):
                    q = [x, y, z]
                    q[ax] += sg
                    if air[tuple(q)] and tuple(q) not in cells:
                        votes[(ax, -sg)] += 1
        (ax, sg), _ = votes.most_common(1)[0]
        others = [i for i in range(3) if i != ax]
        col = {}
        for c in cells:
            k = (c[others[0]], c[others[1]])
            col[k] = min(col.get(k, 10 ** 9), c[ax] * sg)
        out = set(cells)
        for k, t in col.items():
            for d0, d1 in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (k[0] + d0, k[1] + d1)
                if nb in col and col[nb] > t:
                    for tt in range(t + 1, col[nb] + 1):
                        q = [0, 0, 0]
                        q[ax], q[others[0]], q[others[1]] = tt * sg, k[0], k[1]
                        out.add(tuple(q))
        return out, ax, sg, col

    def behind(gl, ax, sg, why, mirror_hull=False):
        col = defaultdict(int)
        others = [i for i in range(3) if i != ax]
        for c in gl:
            k = (c[others[0]], c[others[1]])
            col[k] = max(col.get(k, -10 ** 9), c[ax] * sg)
        depth = []
        for k, t in col.items():
            n = 0
            for tt in range(t + 1, t + 16):
                q = [0, 0, 0]
                q[ax], q[others[0]], q[others[1]] = tt * sg, k[0], k[1]
                q = tuple(q)
                if air[q] and q not in gl:
                    break
                if q in gl:
                    continue
                if not cut(*q, why=why, mirror_hull=mirror_hull):
                    break
                if mirror_hull and galw[q]:
                    air[q[0], MIR(q[1]), q[2]] = True
                n += 1
            else:
                P.append('%s：(%s) 刻 15 格還沒到空氣' % (why, k))
            depth.append(n)
        return depth

    wins = []
    lab, n = ndimage.label(hull == GLASS, structure=np.ones((3, 3, 3)))
    sill = []
    for i in range(1, n + 1):
        cells = set(map(tuple, np.argwhere(lab == i).tolist()))
        zs = [c[2] for c in cells]
        ys = [c[1] for c in cells]
        row = next((r for r, (st, (z0, z1)) in ROWS.items() if z0 <= min(zs) and max(zs) <= z1), None)
        if len(cells) < 20:
            sill.append(cells)
            continue
        if row in DOOR_ROWS and min(ys) <= YC <= max(ys):
            wins.append({'kind': 'door', 'row': row, 'cells': cells, 'y': (min(ys), max(ys))})
            continue
        wins.append({'kind': 'window', 'row': row, 'cells': cells, 'y': (min(ys), max(ys))})
    # 三叉戟砲船尾砲門下緣剩的一排玻璃（階段十五刻砲門時留下）⇒ 照旁邊船殼的顏色補
    for cells in sill:
        for (x, y, z) in cells:
            nb = Counter(int(hull[x + dx, y + dy, z + dz]) for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, -1), (0, 1, 0), (0, -1, 0))
                         if hull[x + dx, y + dy, z + dz] not in (0, GLASS))
            paint_h[(x, y, z)] = nb.most_common(1)[0][0]
    R['sill_repaint'] = {'cells': len(paint_h), 'colors': dict(Counter(paint_h.values()))}

    win_rows = []
    for w in wins:
        if w['kind'] != 'window':
            continue
        gl, ax, sg, col = sheet(w['cells'], 'hull')
        if ax != 0 or sg != 1:
            P.append('船尾窗 %s y %s 往裡的方向 %s%s' % (w['row'], w['y'], '+-'[sg < 0], 'xyz'[ax]))
        for q in gl:
            if not hull[q]:
                P.append('船尾窗補的玻璃不在船殼裡 %s' % (q,))
            cut(*q, why='船尾窗玻璃')
            glass[q] = GLASS
            air[q] = False
        pieces.append((gl, ax, sg))
        dep = behind(gl, ax, sg, '船尾窗 %s y %d–%d 後面' % (w['row'], w['y'][0], w['y'][1]))
        win_rows.append({'row': w['row'], 'y': list(w['y']), 'glass': len(gl), 'added': len(gl) - len(w['cells']), 'behind_depth': [min(dep), max(dep)],
                         'xs': sorted(set(c[0] for c in gl))})
    R['stern_windows'] = win_rows

    gl_lab, gn = ndimage.label(galw == GLASS, structure=np.ones((3, 3, 3)))
    gal_rows = []
    for i in range(1, gn + 1):
        cells = set(map(tuple, np.argwhere(gl_lab == i).tolist()))
        if min(c[1] for c in cells) < YC:
            continue                                    # P 舷照鏡像
        gl, ax, sg, col = sheet(cells, 'gallery')
        for q in gl:
            if not galw[q]:
                P.append('gallery 窗補的玻璃不在 gallery 裡 %s' % (q,))
            cut(*q, why='gallery 窗玻璃')
            glass[q] = GLASS
            air[q] = False
            qm = (q[0], MIR(q[1]), q[2])
            air[qm] = False
            glass[qm] = GLASS
        pieces.append((gl, ax, sg))
        pieces.append(({(q[0], MIR(q[1]), q[2]) for q in gl}, ax, -sg if ax == 1 else sg))
        dep = behind(gl, ax, sg, 'gallery 窗 %d' % i, mirror_hull=True)
        gal_rows.append({'n': len(gl), 'added': len(gl) - len(cells), 'in': '%s%s' % ('+-'[sg < 0], 'xyz'[ax]), 'z': [min(c[2] for c in gl), max(c[2] for c in gl)],
                         'behind_depth': [min(dep), max(dep)]})
    R['gallery_windows'] = gal_rows

    # ── ③ 船尾陽台門洞 ──
    doors = []
    for w in wins:
        if w['kind'] != 'door':
            continue
        row, st = w['row'], ROWS[w['row']][0]
        y0, y1 = w['y']
        top = st + DOOR_TOP
        xo = {}
        for y in range(y0, y1 + 1):
            for z in range(st, top + 1):
                x = 60
                while x < 140 and not hull[x, y, z]:
                    x += 1                      # 陽台欄杆、地板不算（門板擺好之後另外量撞不撞）
                xo[(y, z)] = x
                while hull[x, y, z]:
                    cut(x, y, z, '陽台門洞 %s' % row)
                    x += 1
                if not air[x, y, z]:
                    P.append('陽台門洞 %s (%d,%d) 刻穿之後不是空氣 x %d' % (row, y, z, x))
        for y in range(y0 - 1, y1 + 2):                 # 門板比門洞高一格：上面那一排的牆面也算（船尾面往上往後倒）
            x = 60
            while x < 140 and not hull[x, y, top + 1]:
                x += 1
            xo[(y, top + 1)] = x
        xd = min(xo.values()) - 1
        for y in range(y0 - 1, y1 + 2):
            for z in range(st - 1, top + 2):
                if (y in (y0 - 1, y1 + 1) or z == top + 1) and z >= st:
                    x = 60
                    while x < 140 and not hull[x, y, z]:
                        x += 1
                    if x < 140 and not air[x, y, z] and hull[x, y, z] != GOLD:
                        paint_h[(x, y, z)] = GOLD
        doors.append({'name': '門-stern-%s' % row, 'host': 'gura-tridente-01m-deck-%s' % row, 'world_plane_x': xd, 'yc': YC, 'z0': st, 'h': top - st + 2,
                      'w': y1 - y0 + 3, 'rotate': 180, 'opening': [y1 - y0 + 1, top - st + 1], 'why': '船尾 %s 那一層的陽台' % row})

    # ── ④ 船頭門洞＋門裡兩階 ──
    up_cells = defaultdict(int)
    bow = []
    for yc in (190, 210):
        xin = {}
        xout = 0
        for y in range(yc - 2, yc + 3):
            for z in range(149, 163):
                x = 706                         # 上甲板橫樑在 x 704–705（每 16 格）⇒ 從它後面起掃
                while not hull[x, y, z]:
                    if occ[x, y, z]:
                        P.append('船頭門洞 y %d：牆裡面擋著 (%d,%d,%d) 色 %d' % (yc, x, y, z, occ[x, y, z]))
                        break
                    x += 1
                xin[(y, z)] = x
                while hull[x, y, z]:
                    cut(x, y, z, '船頭門洞')
                    x += 1
                if occ[x, y, z]:
                    P.append('船頭門洞 y %d (%d,%d) 外面擋著 x %d 色 %d' % (yc, y, z, x, occ[x, y, z]))
                xout = max(xout, x)
        for y in range(yc - 2, yc + 3):
            wi = xin[(y, 149)]
            for xs, ztop in (((wi - 2, wi - 1), 146), ((wi - 4, wi - 3), 144)):
                for x in xs:
                    z = 142
                    while occ[x, y, z - 1] == 0:
                        z -= 1
                    for zz in range(z, ztop + 1):
                        if air[x, y, zz]:
                            up_cells[(x, y, zz)] = PLANK
                            air[x, y, zz] = False
        for y in range(yc - 3, yc + 4):
            for z in range(149, 165):
                if (y in (yc - 3, yc + 3) or z >= 163) and z <= 163:
                    x = 712
                    while x < 730 and not hull[x, y, z]:
                        x += 1
                    if x < 730 and not air[x, y, z]:
                        x2 = x
                        while hull[x2 + 1, y, z]:
                            x2 += 1
                        if hull[x2, y, z] != GOLD:
                            paint_h[(x2, y, z)] = GOLD
        doors.append({'name': '門-bow-%s' % ('S' if yc > YC else 'P'), 'host': 'gura-tridente-01m-deck-upper', 'world_plane_x': xout, 'yc': yc, 'z0': 149, 'h': 15,
                      'w': 7, 'rotate': 0, 'opening': [5, 14], 'why': '圓船頭往格柵平台'})
        bow.append({'yc': yc, 'wall_in_x': [min(xin.values()), max(xin.values())], 'door_x': xout})
    R['bow'] = bow
    R['bow_steps'] = len(up_cells)

    # ── ⑤ poop 前艙壁的門、彈藥庫的門、orlop 艙房的門 ──
    for yc in (184, 216):
        doors.append({'name': '門-poop-%s' % ('S' if yc > YC else 'P'), 'host': 'gura-tridente-01m-deck-poop', 'world_plane_x': 229, 'yc': yc, 'z0': 160, 'h': 17,
                      'w': 7, 'rotate': 0, 'opening': [5, 16], 'why': 'poop 前緣艙壁'})
    for nm, xd, rot in (('門-magazine-aft', 297, 0), ('門-magazine-fore', 561, 180)):
        doors.append({'name': nm, 'host': 'gura-tridente-01m-deck-hold', 'world_plane_x': xd, 'yc': YC, 'z0': 31, 'h': 16, 'w': 7, 'rotate': rot,
                      'opening': [5, 15], 'why': '彈藥庫門（朝貨艙平台）'})
    ra = json.load(open(os.path.join(D, '..', '..', 'gura-tridente-01m-rooms-orlop', 'anchors.json'), encoding='utf-8'))['anchors']
    for a in ra:
        if not a['name'].endswith('.door'):
            continue
        lx, ly, lz = a['at']
        doors.append({'name': '門-艙房-%s' % a['name'][:-5], 'host': 'gura-tridente-01m-rooms-orlop', 'local': True, 'world_plane_x': None,
                      'at_local': [lx + 0.5, -0.5, lz], 'yc': None, 'z0': lz, 'h': 19, 'w': 9, 'rotate': 270, 'opening': [7, 18], 'why': 'orlop 艙房門洞（朝中線走道）',
                      'world_check': [228 + lx, 220, 67 + lz]})

    # ── ⑥ 貨艙平台、梯子 ──
    hold = {}
    HX0, HX1, ZP = 297, 561, 30
    hole = lambda x, y: 385 <= x <= 398 and abs(y - YC) <= 4     # 梯口從第一階（x 385）開；🩸 v1 從 383 開 ⇒ 樓梯自檢報梯頂那一角 14 格洞（梯腳那兩柱沒踏板）

    def inner(x, z):
        ys = np.nonzero(hull[x, :, z])[0]
        lo = max(ys[ys < YC]) + 1
        hi = min(ys[ys > YC]) - 1
        return lo, hi
    for x in range(HX0, HX1 + 1):
        lo, hi = inner(x, ZP)
        for y in range(lo, hi + 1):
            if occ[x, y, ZP] == 0 and not hole(x, y):
                hold[(x, y, ZP)] = PLANK
        if x % 16 < 2:
            for z in range(ZP - 3, ZP):
                lo, hi = inner(x, z)
                for y in range(lo, hi + 1):
                    if occ[x, y, z] == 0 and not hole(x, y):
                        hold[(x, y, z)] = BEAM
    for x in range(384, 399):                           # 梯口圍欄（梯頭那一頭 x 399 不圍）
        for y in range(YC - 5, YC + 6):
            if (x == 384 or abs(y - YC) == 5) and not hole(x, y):
                for z in (ZP + 1, ZP + 2):
                    hold[(x, y, z)] = BEAM
    for x in range(379, 385):                           # 艙底梯腳墊平（limber 溝與 V 底 ⇒ 平到 z 8）
        for y in range(YC - 4, YC + 5):
            for z in range(5, 9):
                if occ[x, y, z] == 0:
                    hold[(x, y, z)] = PLANK
    for k in hold:
        air[k] = False

    def build_ladder(name, xs, s, run, n, zl, zu, head_x, yc=YC, th=3):
        cells = {}
        for kk in range(0, n + 2):
            xa = xs + s * run * kk
            xr = sorted((xa, xa + s * (run - 1)))
            zt = zl + 3 * kk
            for xx in range(xr[0], xr[1] + 1):
                if 1 <= kk <= n:
                    for yy in range(yc - th, yc + th + 1):
                        cells[(xx, yy, zt)] = BEAM
                zlo, zhi = (zl + 1, zl + 3) if kk == 0 else (zt - 3, min(zt, zu))
                if kk == n + 1:
                    zlo, zhi = zl + 3 * n - 3, zu
                for z in range(zlo, zhi + 1):
                    for yy in (yc - th - 1, yc + th + 1):
                        cells[(xx, yy, z)] = BEAM
        kept = {k: v for k, v in cells.items() if air[k]}
        pts = {'foot': [xs - s, yc, zl + 1], 'lo': [xs + s * run, yc, zl + 4], 'hi': [xs + s * run * n, yc, zl + 3 * n + 1], 'head': [head_x, yc, zu + 1]}
        for nm, p in pts.items():
            if not air[tuple(p)] or air[p[0], p[1], p[2] - 1]:
                if not (nm in ('lo', 'hi')):
                    P.append('梯子 %s 的 %s %s：那格不空或腳下沒東西' % (name, nm, p))
        for k in kept:
            air[k] = False
        return kept, {'cells': len(kept), 'dropped': len(cells) - len(kept), 'steps': n, 'run': run, 'points': pts}

    orlop_cut = {}
    od = deck_cells['orlop']
    oset = set(map(tuple, od[np.isin(od[:, 0], (299, 501)), :3].tolist()))
    for x in (299, 501):
        for y in range(YC - 4, YC + 5):
            for z in range(64, 72):
                if occ[x, y, z] == BEAM and (x, y, z) in oset:
                    orlop_cut[(x, y, z)] = BEAM
                    air[x, y, z] = True
    lad_o, lad_h, L = {}, {}, {}
    c1, L['hold-main'] = build_ladder('hold-main', 477, 1, 2, 11, ZP, 66, 502)
    c2, L['hold-aft'] = build_ladder('hold-aft', 312, -1, 1, 12, ZP, 67, 298)
    c3, L['bilge'] = build_ladder('bilge', 383, 1, 2, 7, 8, ZP, 400)
    lad_o.update(c1)
    lad_o.update(c2)
    lad_h.update(c3)
    R['ladders'] = L
    R['hold_deck_cells'] = len(hold)
    R['orlop_coaming_cut'] = len(orlop_cut)

    # ── 門的擺法（門板 0.05 m：厚 2、寬 14、高 32；scale 0.5 ⇒ 1 × 7 × 16 格；寬 9 的 ⇒ y 方向 0.5 × 9／7）──
    drows = []
    for d in doors:
        sy = 0.5 * d['w'] / 7.0
        sz = d['h'] / 32.0
        if d.get('local'):
            at = d['at_local']
            wx, wy, wz = d['world_check']
            cells = [(wx + dx, wy, wz + dz) for dx in range(-4, 5) for dz in range(d['h'])]
            foot = [(wx + dx, wy, wz - 1) for dx in range(-4, 5)]
        else:
            xd, yc, z0 = d['world_plane_x'], d['yc'], d['z0']
            at = [xd + 0.5, yc + 0.5, z0]
            hw = d['w'] // 2
            cells = [(xd, y, z) for y in range(yc - hw, yc + hw + 1) for z in range(z0, z0 + d['h'])]
            foot = [(xd, y, z0 - 1) for y in range(yc - hw, yc + hw + 1)]
        hits = [c for c in cells if not air[c]]
        nofoot = [c for c in foot if air[c]]
        if hits:
            P.append('%s 門板撞 %d 格：%s' % (d['name'], len(hits), hits[:4]))
        drows.append({'name': d['name'], 'host': d['host'], 'at': at, 'rotate': d['rotate'], 'scale': [0.5, round(sy, 6), round(sz, 6)], 'opening': d['opening'],
                      'why': d['why'], 'hits_solid': len(hits), 'foot_air': len(nofoot), 'meta': {'kind': 'door', 'open': 'side'}})

    # ── 讀數：玻璃一片一片 6 連通、封不封得住（26 連通灌，比遊戲嚴）；新格跟現況重疊 ──
    drop = next((int(a.split('=')[1]) for a in sys.argv[2:] if a.startswith('--drop=')), None)
    if drop is not None:                       # 反向對照：拿掉第 drop 片正中間那一格玻璃 ⇒ 那一片要報漏（⛔ 不寫檔）
        gl0 = sorted(pieces[drop][0])
        mid = gl0[len(gl0) // 2]
        pieces[drop] = (set(gl0) - {mid}, pieces[drop][1], pieces[drop][2])
        del glass[mid]
        air[mid] = True
    gm = np.zeros((NX, NY, NZ), bool)
    for q in glass:
        gm[q] = True
    gl6, n6 = ndimage.label(gm, structure=ndimage.generate_binary_structure(3, 1))
    gl26, n26 = ndimage.label(gm, structure=np.ones((3, 3, 3)))
    R['glass'] = {'cells': len(glass), 'pieces_26': int(n26), 'pieces_6': int(n6)}
    # 每一片：只看玻璃周圍一格的薄殼（26 連通外擴 1 格）裡的空氣 —— 從玻璃往外一步的空氣灌（26 連通：斜角也算通 ⇒ 比遊戲的 6 連通嚴），
    #   灌得到玻璃往裡一步的空氣 ⇒ 漏（真的縫一定貼著玻璃；盒子框大了會量到繞過 gallery 外面的空氣）
    leaks, no_back = [], []
    for pi, (gl, ax, sg) in enumerate(pieces):
        idx = np.array(sorted(gl))
        lo = idx.min(0) - 2
        hi = idx.max(0) + 3
        sl = tuple(slice(a, b) for a, b in zip(lo, hi))
        sheet_m = np.zeros(tuple(hi - lo), bool)
        sheet_m[tuple((idx - lo).T)] = True
        shell = ndimage.binary_dilation(sheet_m, structure=np.ones((3, 3, 3))) & air[sl]
        step = np.zeros(3, int)
        step[ax] = sg
        front = np.zeros_like(shell)
        back = np.zeros_like(shell)
        for c in idx - lo:
            f, b = tuple(c - step), tuple(c + step)
            if shell[f]:
                front[f] = True
            if shell[b]:
                back[b] = True
        wet = ndimage.binary_propagation(front, structure=np.ones((3, 3, 3)), mask=shell)
        if (wet & back).any():
            leaks.append({'piece': pi, 'at': (np.argwhere(wet & back)[0] + lo).tolist(), 'in': '%s%s' % ('+-'[sg < 0], 'xyz'[ax]), 'cells': len(gl)})
        if not back.any():
            no_back.append(pi)
    R['glass']['pieces'] = len(pieces)
    R['glass']['leaks_26'] = leaks
    if no_back:
        P.append('玻璃 %s 後面一格都不是空氣（看不穿）' % no_back)
    newc = {}
    for dct in (glass, hold, lad_o, lad_h, up_cells):
        for k in dct:
            newc[k] = newc.get(k, 0) + 1
    R['new_overlap_each_other'] = sum(1 for v in newc.values() if v > 1)
    R['new_on_old_solid'] = sum(1 for k in newc if occ[k] and k not in carve_h and k not in carve_g and (k[0], MIR(k[1]), k[2]) not in carve_g)
    hm = sum(1 for (x, y, z) in carve_h if (x, MIR(y), z) not in carve_h)
    R['hull_carve'] = {'cells': len(carve_h), 'mirror_missing': hm, 'colors': dict(Counter(carve_h.values()).most_common(8))}
    R['gallery_carve'] = {'cells_S_side': len(carve_g), 'colors': dict(Counter(carve_g.values()).most_common(8))}
    R['hull_paint'] = {'cells': len(paint_h), 'colors': dict(Counter(paint_h.values()))}
    R['doors'] = drows

    if drop is not None:
        print(json.dumps({'probe_drop': drop, 'leaks': R['glass']['leaks_26']}, ensure_ascii=False))
        return
    # ── 輸出 ──
    os.makedirs(OUT, exist_ok=True)
    files = {}

    def dump(name, dct, head, off=(0, 0, 0)):
        p = os.path.join(OUT, name)
        rows = sorted((k[0] - off[0], k[1] - off[1], k[2] - off[2], v) for k, v in dct.items())
        body = ''.join('%d,%d,%d,%d\n' % r for r in rows)
        open(p, 'w', encoding='utf-8', newline='\n').write('# %s（%d 格；TASK-1257 draft_access.py）\n' % (head, len(rows)) + body)
        files[name] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
    dump('hull_carve.vox.txt', carve_h, '船殼要刻的格（世界座標；第 4 欄 ＝ 刻之前的顏色，carvevox 守門）')
    dump('hull_paint.vox.txt', paint_h, '船殼換色（門框金 248、砲門下緣剩的玻璃換回旁邊的色；stampvox overwrite=1）')
    dump('gallery_carve.vox.txt', carve_g, 'quarter gallery 要刻的格（gallery 自己的座標；第 4 欄 ＝ 刻之前的顏色）', GAL_AT)
    dump('glass.vox.txt', glass, '船尾窗玻璃（世界座標，at 0,0,0；子作品 -stern-glass，關聯 meta material=glass）')
    dump('deck_hold.vox.txt', hold, '貨艙平台（世界座標；地板 z 30、橫樑、梯口圍欄、艙底梯腳墊平）')
    dump('ladders_orlop.vox.txt', lad_o, '梯子 貨艙平台 → orlop（世界座標）')
    dump('ladders_hold.vox.txt', lad_h, '梯子 艙底 → 貨艙平台（世界座標）')
    dump('orlop_carve.vox.txt', orlop_cut, 'orlop 艙口圍欄在梯頭那一段開口（世界座標；第 4 欄 ＝ 刻之前的顏色）')
    dump('upper_steps.vox.txt', up_cells, '船頭門裡的兩階（世界座標；掛在上砲甲板子作品）')
    R['files'] = files
    deck_meta = {'kind': 'deck', 'deck': 'hold', 'level': -1, 'name': '貨艙', 'floor': '236:31,632:31', 'thick': 4}
    json.dump({'doors': {'work': DOOR_WORK, 'size': list(DOOR_SIZE), 'pivot': list(DOOR_PIVOT), 'rows': drows},
               'ladders': {'gura-tridente-01m-ladders-orlop': {k: L[k] for k in ('hold-main', 'hold-aft')}, 'gura-tridente-01m-ladders-hold': {'bilge': L['bilge']}},
               'deck_meta': deck_meta},
              open(os.path.join(D, 'access_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(R, open(os.path.join(D, 'verify_access.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: R[k] for k in R if k not in ('stern_windows', 'gallery_windows', 'doors', 'ladders', 'files', 'inputs')}, ensure_ascii=False))
    print('problems', len(P))
    for p in P[:40]:
        print(' ✗', p)
    for d in drows:
        print(' 門', d['name'], d['at'], 'rot', d['rotate'], 'scale', d['scale'], '撞', d['hits_solid'], '腳下空', d['foot_air'])
    for k, v in L.items():
        print(' 梯', k, v)


if __name__ == '__main__':
    main()
