# 皇家號 新圖紙 07（TASK-0694 傘；Tim 2026-10-18「可以試著加一些艙室嗎」「送藥手&其他問題發現的話一起修復」）：
#   艙底分間（地板、隔艙壁）、每間從中央走道開艙口放梯子、空艙房的框（§9.2）、甲板 meta（甲板-hold 的 floor 延伸、甲板-main 的 walk ＝ 中央走道）
#   ⇒ masks/cabins/{cabins,ladders}.vox.txt、masks/cabins/deck_carve.vox.txt（從甲板-main 刻掉的艙口）、cabins_placement.json、verify_cabins.json
#   用法：python -I -X utf8 draft_cabins.py <reale.vxk> [--probe=floor=+3]
#   · 佔用照遊戲匯入的那一份 .vxk（＝ 組裝件的格；不含外部模型）。只讀，不碰作品。
#   · --probe：反向對照（只印讀數）。floor=+3 ⇒ 地板抬 3 格（艙房的頭頂淨空要報不夠）。
import sys, os, json, struct, zlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')
YC = 160
SX, SY, SZ = 720, 321, 140
HEAD = 14                       # 艙房與站位：頭上 1.4 m（遊戲 40_crew.js、rooms.py）
NAV_C, NAV_DZ, NAV_HEAD = 2, 3, 12   # 遊戲 42_hands.js 走路格


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load_vxk(path):
    b = zlib.decompress(open(path, 'rb').read(), -15)
    n = struct.unpack('<I', b[4:8])[0]
    h = json.loads(b[8:8 + n].decode('utf-8'))
    o = 8 + n
    nc = (len(b) - o) // (6 + 4096)
    co = struct.unpack('<%dH' % (nc * 3), b[o:o + nc * 6])
    o += nc * 6
    G = np.zeros(((SX + 15) // 16 * 16, (SY + 15) // 16 * 16, (SZ + 15) // 16 * 16), np.uint8)
    for i in range(nc):
        cx, cy, cz = co[3 * i:3 * i + 3]
        blk = np.frombuffer(b[o + i * 4096:o + (i + 1) * 4096], np.uint8).reshape(16, 16, 16)   # [z][y][x]
        if cz * 16 >= G.shape[2] or cx * 16 >= G.shape[0] or cy * 16 >= G.shape[1]:
            continue
        G[cx * 16:cx * 16 + 16, cy * 16:cy * 16 + 16, cz * 16:cz * 16 + 16] = blk.transpose(2, 1, 0)
    return h, G[:SX, :SY, :SZ].copy()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
    K = V(plan['cabins'])
    C = {k: V(v) for k, v in plan['layout']['colors'].items()}
    h, G = load_vxk(args[0])
    occ = G > 0
    fz = int(K['floor_top_z'] + probe.get('floor', 0))
    cab, lad, carve = {}, {}, set()
    R = {'rooms': {}, 'ladders': {}}

    def inside(x, z):                       # 那一高度艙裡的半寬（中線往外第一格實心之前）；中線本身是實心 ⇒ -1
        if occ[x, YC, z]:
            return -1
        d = 0
        while YC + d + 1 < SY and not occ[x, YC + d + 1, z]:
            d += 1
        return d

    def put(D, x, dy, z, c):
        for y in (YC + dy, YC - dy):
            if not occ[x, y, z]:
                D[(x, y, z)] = c

    # ───── 地板（每間整段，|dy| ≤ floor_half）─────
    for r in K['rooms']:
        for x in range(r['x'][0], r['x'][1] + 1):
            for dy in range(K['floor_half'] + 1):
                put(cab, x, dy, fz, C['deck'])
    # ───── 隔艙壁（從底艙到甲板底；最前面那道開門）─────
    for x0, x1, door in K['bulkheads']:
        for x in range(x0, x1 + 1):
            for z in range(1, 40):
                hw = inside(x, z)
                if hw < 0:
                    if z > 10:
                        break                   # 碰到甲板（中線實心）⇒ 到頂了
                    continue
                for dy in range(hw + 1):
                    if door and dy <= K['door_half'] and fz < z <= K['door_top_z']:
                        continue
                    put(cab, x, dy, z, C['wood'])
    occ2 = occ.copy()
    for (x, y, z) in cab:
        occ2[x, y, z] = True

    # ───── 中央走道頂（walk 用、梯頭）：dy +3 那一欄，甲板上 8 格以上最高的實心 ─────
    def top_at(x, dy=3):
        zs = [z for z in range(20, 60) if occ[x, YC + dy, z]]
        return max(zs) if zs else None

    # ───── 每間的艙口與梯子 ─────
    L = K['ladder']
    pts, boxes = {}, {}
    for r in K['rooms']:
        nm, (rx0, rx1) = r['name'], r['x']
        x_top = rx0 + L['x_off']
        ztop = top_at(x_top - L['head_back'])           # 梯頭那一點的走道頂
        zs = [fz + L['pitch'] * k for k in range(1, 40) if fz + L['pitch'] * k < ztop - 1]
        rungs = [(x_top + (len(zs) - 1 - i), z) for i, z in enumerate(zs)]
        xs0, xs1 = x_top - 1, rungs[0][0] + 1           # 艙口（刻掉的範圍）：x
        ys = range(YC + L['dyc'] - L['half'], YC + L['dyc'] + L['half'] + 1)
        for x in range(xs0, xs1 + 1):
            for y in ys:
                for z in range(fz + 1, ztop + 1):
                    if occ[x, y, z]:
                        carve.add((x, y, z))
        for (x, z) in rungs:
            for y in ys:
                lad[(x, y, z)] = C['dark']
        for k_, (x, z) in enumerate(rungs):             # 扶手：靠中線那一邊
            z_from = fz + 1 if k_ == 0 else rungs[k_ - 1][1]
            for zz in range(z_from, z + 3):
                lad[(x, YC + L['rail_dy'], zz)] = C['dark']
        xlo = rungs[0][0]
        yc = YC + L['dyc']
        p4 = {'foot': [xlo + 2, yc, fz + 1], 'lo': [rungs[0][0], yc, rungs[0][1] + 1], 'hi': [rungs[-1][0], yc, rungs[-1][1] + 1],
              'head': [x_top - L['head_back'], yc, ztop + 1]}
        pts[nm] = p4
        bx0 = xs1 + 3                                   # 艙房的框：梯子那一段之後（框只框空氣、門口那一格在框外）
        bx1 = bx0
        while bx1 < rx1 and not occ2[bx1 + 1, YC - K['box_half']:YC + K['box_half'] + 1, fz + 1:K['box_top_z'] + 1].any():
            bx1 += 1                                    # 框從梯子那頭往前長，碰到東西就停（taverne：主桅腳）
        box = {'min': [bx0, YC - K['box_half'], fz + 1], 'max': [bx1, YC + K['box_half'], K['box_top_z']], 'door': [bx0 - 1, YC, fz + 1]}
        boxes[nm] = box
        R['ladders'][nm] = {'rungs': len(rungs), 'hatch_x': [xs0, xs1], 'coursier_top': ztop}
    for p in list(lad):
        if p in carve:
            continue
        if occ2[p]:
            del lad[p]
    occ3 = occ2.copy()
    for p in carve:
        occ3[p] = False
    for p in lad:
        occ3[p] = True
    # 讀數：梯子點（那一格空、腳下實心、頭上幾格空）、艙房（框裡不是空氣的格、腳下不是實心的格、淨空）
    for nm, p4 in pts.items():
        R['ladders'][nm]['points'] = {k: {'at': v, 'empty': not occ3[tuple(v)], 'solid_below': bool(occ3[v[0], v[1], v[2] - 1]),
                                          'clear_up': next((hh for hh in range(1, 13) if occ3[v[0], v[1], v[2] + hh]), 12)} for k, v in p4.items()}
    for nm, b in boxes.items():
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        sub = occ3[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1]
        under = occ3[x0:x1 + 1, y0:y1 + 1, z0 - 1]
        above = occ3[x0:x1 + 1, y0:y1 + 1, z1 + 1]
        R['rooms'][nm] = {'box': [b['min'], b['max']], 'size_m': [round((x1 - x0 + 1) / 10, 1), round((y1 - y0 + 1) / 10, 1), round((z1 - z0 + 1) / 10, 1)],
                          'not_air': int(sub.sum()), 'head_ok': z1 - z0 + 1 >= HEAD, 'floor_holes': int((~under).sum()), 'ceiling_cells': int(above.sum()), 'type': next(q['type'] for q in K['rooms'] if q['name'] == nm)}

    # ───── 甲板 meta ─────
    xs = sorted(x for r in K['rooms'] for x in r['x'])
    hold_floor = '132:15,182:15,%d:%d,%d:%d' % (xs[0], fz + 1, xs[-1], fz + 1)
    # walk（甲板-main）：中央走道頂 ＋ 1，兩頭連台階；照 dy +3 那一欄逐格量，連續同高的只留頭尾
    wx0, wx1 = 142, 557
    col = []
    for x in range(wx0, wx1 + 1):
        t = None
        for z in range(60, 15, -1):                         # 那一欄站得住的最高點（腳下實心、頭上 12 格空）
            if occ3[x, YC + 3, z - 1] and not occ3[x, YC + 3, z:z + NAV_HEAD].any():
                t = z
                break
        col.append((x, t))
    W = []
    for i, (x, z) in enumerate(col):
        if z is None:
            continue
        pz = col[i - 1][1] if i else None
        nz = col[i + 1][1] if i + 1 < len(col) else None
        if pz != z or nz != z:
            W.append('%d:%d' % (x, z))
    walk = ','.join(W)

    # ───── 走路格（照遊戲 navZ／navStep 算，主甲板那一層）：取用點（艙口梯頭）連得到哪裡 ─────
    deck_floor = [tuple(map(int, q.split(':'))) for q in next(p for p in h['parts'] if p.get('path') == '甲板-main')['meta']['floor'].split(',')]

    def poly(F, x):
        if x < F[0][0] - 0.5 or x > F[-1][0] + 0.5:
            return None
        for i in range(1, len(F)):
            if x <= F[i][0]:
                a, b = F[i - 1], F[i]
                t = 0 if b[0] == a[0] else (x - a[0]) / (b[0] - a[0])
                return int(np.floor(a[1] + (b[1] - a[1]) * t + 0.5))   # 同 JS Math.round
        return F[-1][1]
    WF = [tuple(map(int, q.split(':'))) for q in walk.split(',')]

    def navz(x, y, use_walk):
        f = poly(WF, x) if use_walk and WF[0][0] - 0.5 <= x <= WF[-1][0] + 0.5 else poly(deck_floor, x)
        if f is None:
            return -1
        for z in range(f + 3, f - 3, -1):
            if occ3[x, y, z - 1] and not occ3[x, y, z] and not occ3[x, y, z + 1:z + NAV_HEAD].any():
                return z
        return -1

    def regions(use_walk):
        x0 = 69
        nx, ny = (690 - x0) // NAV_C + 1, SY // NAV_C
        Z = np.full((nx, ny), -1, np.int32)
        for i in range(1, nx - 1):
            for j in range(1, ny - 1):
                Z[i, j] = navz(x0 + i * NAV_C, j * NAV_C, use_walk)
        lab = np.full((nx, ny), -1, np.int32)
        n = 0
        DX = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for i in range(nx):
            for j in range(ny):
                if Z[i, j] < 0 or lab[i, j] >= 0:
                    continue
                st = [(i, j)]
                lab[i, j] = n
                while st:
                    a, b = st.pop()
                    for d, (dx, dy) in enumerate(DX):
                        c, e = a + dx, b + dy
                        if Z[c, e] < 0 or lab[c, e] >= 0 or abs(Z[c, e] - Z[a, b]) > NAV_DZ:
                            continue
                        if d >= 4 and (Z[a + dx, b] < 0 or Z[a, b + dy] < 0):
                            continue
                        lab[c, e] = n
                        st.append((c, e))
                n += 1
        return x0, Z, lab

    def at(x0, Z, lab, p):
        i, j = int(round((p[0] - x0) / NAV_C)), int(round(p[1] / NAV_C))
        best = None
        for di in range(-3, 4):
            for dj in range(-3, 4):
                if Z[i + di, j + dj] >= 0 and abs(Z[i + di, j + dj] - p[2]) <= 3:
                    d = di * di + dj * dj
                    if best is None or d < best[0]:
                        best = (d, lab[i + di, j + dj])
        return None if best is None else int(best[1])
    station = [133, 160, 32]                            # 取用點旁：艙口梯頭（甲板-main/梯子 hold.head）
    probes = {'砲台下 船頭 x 575': [575, 160, 28], '砲台下 x 590 S': [590, 172, 29], '中央走道 x 300': [300, 163, 37], '中央走道 x 500': [500, 163, 37]}
    for nm, p4 in pts.items():
        probes['梯頭 ' + nm] = p4['head']
    NR = {}
    for use in (False, True):
        x0, Z, lab = regions(use)
        s = at(x0, Z, lab, station)
        NR['walk' if use else 'floor'] = {k: (at(x0, Z, lab, v) == s and s is not None) for k, v in probes.items()}
    R['nav_same_region_as_station'] = NR
    R['meta'] = {'hold_floor': hold_floor, 'walk': walk, 'walk_points': len(W)}
    R['cells'] = {'cabins': len(cab), 'ladders': len(lad), 'carve': len(carve)}

    if probe:
        print(json.dumps({'probe': probe, 'rooms': R['rooms']}, ensure_ascii=False, indent=1))
        return
    od = os.path.join(HERE, 'masks', 'cabins')
    os.makedirs(od, exist_ok=True)
    for fn, D, title in (('cabins', cab, '艙底分間：地板、隔艙壁'), ('ladders', lad, '艙口梯（中央走道 → 艙底各間）')):
        with open(os.path.join(od, fn + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 皇家號 %s（draft_cabins.py）x,y,z,color —— at 0,0,0\n' % title)
            f.writelines('%d,%d,%d,%d\n' % (x, y, z, c) for (x, y, z), c in sorted(D.items()))
    with open(os.path.join(od, 'deck_carve.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 皇家號 從甲板-main 刻掉的艙口（draft_cabins.py）x,y,z\n')
        f.writelines('%d,%d,%d\n' % p for p in sorted(carve))
    json.dump({'ladder_points': pts, 'rooms': boxes, 'room_types': {r['name']: r['type'] for r in K['rooms']}, 'hold_floor': hold_floor, 'walk': walk},
              open(os.path.join(HERE, 'cabins_placement.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(R, open(os.path.join(HERE, 'verify_cabins.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
